# Choix pondérés et backtracking

Le chaînage avant de Snarky reste déterministe et ne crée aucune recherche
implicite. La recherche est une couche publique distincte qui pilote des
sessions, des groupes de règles et des faits d'hypothèse.

## Instruction `CHOICE`

`CHOICE` instancie un fait ou un objet ; il ne choisit pas une instanciation
de règle :

```text
RULE assign_queen
WHEN
    (n_queens variable $queen)
    NOT EXISTS ($queen value $known)
THEN
    CHOICE ($queen decision $row) WEIGHT $weight
    FROM
        ($queen candidate $row)
        ($queen choice_weight SEQ[$row $weight])
    END_CHOICE
END
```

Le `WHEN` lie ici `$queen`. La sous-requête corrélée `FROM` lie `$row` et
`$weight`. Chaque solution distincte de cette sous-requête fournit une
alternative qui affirme exactement un fait cible dans sa branche.

`WEIGHT` est optionnel et vaut `1` par défaut. Il doit être ground et
numérique après la sous-requête. Les variables locales deviennent disponibles
pour les `CHOICE` suivants de la règle.

Plusieurs choix sont séquentiels :

```text
CHOICE ($object first $x)
FROM
    ($source first_candidate $x)
END_CHOICE

CHOICE ($object second $y)
FROM
    ($source second_candidate $y)
    $y != $x
END_CHOICE

ADD ($object state complete)
```

Après le choix de `$x`, son fait cible est présent dans la branche. Le second
choix retrouve cette liaison, énumère les `$y` compatibles, puis les actions
terminales s'exécutent après le dernier choix.

`RuleChoiceProvider` sépare automatiquement les règles de choix des groupes
de propagation ordinaires et les expose à `SessionChoiceSearch`. Un groupe
appelé directement par le chaînage avant ne lance donc jamais une recherche
implicite. `CHOICE` dans `FOR EACH` et une action déterministe placée avant ou
entre deux choix restent volontairement refusés dans ce premier incrément.

## Objets publics

`ChoicePoint` nomme une variable de décision et contient des
`ChoiceAlternative`. Chaque alternative :

- affirme un ou plusieurs faits dans sa branche ;
- possède une valeur optionnelle pour les traces ;
- porte un poids fini et positif ou nul ;
- peut conserver des métadonnées métier.

`SessionChoiceSearch` reçoit :

1. les groupes à saturer après chaque décision ;
2. un producteur de points, normalement `RuleChoiceProvider` ;
3. un prédicat de but ;
4. un prédicat optionnel de contradiction ;
5. une politique, un ordre de parcours et des limites.

La politique MRV choisit le plus petit domaine et ordonne par poids
décroissant. `WeightedRandomChoicePolicy` échantillonne sans remise,
proportionnellement aux poids, avec une graine reproductible. Un poids nul
reste faisable mais vient après les poids positifs.

`DomWdegChoicePolicy` divise la taille du domaine par la somme des poids des
contraintes incidentes encore actives, puis augmente le poids des contraintes
qui expliquent un échec. `PropagationGuidedChoicePolicy` est un décorateur
optionnel : pour un petit domaine, il propage chaque valeur sur une session
isolée et laisse un score métier ordonner les branches non contradictoires.

`LearnedImpactChoicePolicy` apprend au contraire pendant les branches réelles.
Il compare le produit logarithmique des tailles de domaines avant et après le
point fixe, puis essaie d'abord les valeurs ayant laissé le plus de choix.
Une contradiction a un impact maximal et une solution un impact nul. Cette
politique enveloppe dom/wdeg par défaut pour les CSP persistants.

Les parcours disponibles sont profondeur, largeur et meilleur poids d'abord.
Le score d'un chemin est la somme des logarithmes des poids. Il s'agit d'un
score de priorité : les contraintes et les règles déterminent seules la
faisabilité.

## Cycle d'une branche

```text
checkpoint de la session (DFS)
      ↓
assertion des faits de décision
      ↓
saturation des groupes jusqu'au point fixe
      ↓
contradiction ? abandon et backtrack
but atteint ? solution
sinon ? nouveau ChoicePoint
      ↓
rollback avant le choix frère
```

La session fournie au solveur n'est jamais modifiée. Une branche hérite de la
réfraction, des faits, de la provenance et de l'historique. En profondeur,
une copie racine l'isole d'abord de l'appelant, puis les branches sœurs
réutilisent cette session avec `checkpoint()`, `rollback()` et `release()`.
Seule une solution conservée est recopiée. Après rollback, la branche repart
d'un clone présemé de l'index exact du parent. Les mémoires de jointure,
watchers et témoins restent neuves afin qu'aucun cache de la branche
abandonnée ne survive.

Les parcours largeur et meilleur poids gardent plusieurs états logiques dans
leur frontière, mais ne créent plus immédiatement leur session. Un
descripteur contient le parent et l'alternative ; le fork rapide et
l'assertion ne sont exécutés qu'au retrait. BFS utilise une `deque` et
best-first un tas stable, avec le rang d'insertion pour départager les scores
égaux. Le mode avide reste disponible pour les tests différentiels avec
`lazy_frontier=False`.

`RuleChoiceProvider` interroge une vue du matcher courant qui partage son
`FactIndex`, tout en conservant des mémoires de requête indépendantes. Le
producteur de choix ne reconstruit donc plus l'index complet de la session.

La trace distingue `choice`, `decision`, `contradiction`, `backtrack`,
`solution`, `dead_end` et `limit`. Les limites techniques ne sont pas
confondues avec une contradiction logique.

## Trail de session

`InferenceSession` expose maintenant un checkpoint réversible complet. Le
trail restaure :

- l'ordre et la présence des faits par une liste doublement chaînée ;
- les profondeurs et dérivations de provenance ;
- les tags temporels, faits supposés et compteurs `FRESH` ;
- la réfraction positive et négative ;
- les journaux, groupes, mémoires d'agenda et compteurs de cycles.

Les ensembles de réfraction sont photographiés au checkpoint ; les parties
volumineuses et fréquemment mutées — mémoire de travail, provenance et tags —
sont annulées par opérations inverses. Les checkpoints sont imbriqués,
réutilisables entre plusieurs alternatives, et doivent être libérés en ordre
LIFO. Un test différentiel exécute les quatre reines avec forks puis avec
trail et compare états solutions, décisions, compteurs et événements.

`reversible_depth_first=False` conserve le DFS à forks paresseux comme oracle
et outil de mesure. La valeur par défaut est `True`.

Le trail local de `PropagationState` reste utile à l'intérieur d'un
propagateur. Une intégration future pourra éviter aussi la reconstruction du
matcher après rollback ; elle n'est plus nécessaire pour supprimer les copies
de sessions entre branches sœurs.

## Parallélisme différé

Plusieurs alternatives ne peuvent pas partager simultanément la session
mutable du DFS. Une exécution parallèle future utiliserait un fork isolé par
travailleur, puis le trail local pour explorer chaque sous-arbre. L'ordre des
solutions resterait déterminé par le coordinateur, indépendamment de l'ordre
d'arrivée des processus.

Cette piste, ses contraintes de déterminisme, de granularité, de transfert de
mémoire et son plan de benchmark sont documentés dans
[`parallel_choice_search.md`](parallel_choice_search.md). Elle n'est pas
implémentée.

Les optimisations séquentielles réalisées auparavant sont ordonnées et
mesurées dans
[`choice_search_optimization_plan.md`](choice_search_optimization_plan.md).

## Applications de validation

[`csp_solver`](../csp_solver/README.md) exprime un CSP binaire par des faits et
des règles, sans appeler le solveur Python historique.
[`harmonizer`](../harmonizer/README.md) utilise le même protocole avec des
voicings SATB, des contraintes musicales dures et des poids dérivés de
marginales.
