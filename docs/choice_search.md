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
Seule une solution conservée est recopiée. Un matcher semi-naïf vierge est
installé après chaque rollback afin qu'aucun cache de la branche abandonnée
ne survive.

Les parcours largeur et meilleur poids gardent des forks : plusieurs états
de la frontière doivent y rester vivants simultanément. Ils bénéficient
néanmoins d'une copie spécialisée de la provenance qui partage les faits et
termes immuables au lieu de les recopier profondément.

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

## Applications de validation

[`csp_solver`](../csp_solver/README.md) exprime un CSP binaire par des faits et
des règles, sans appeler le solveur Python historique.
[`harmonizer`](../harmonizer/README.md) utilise le même protocole avec des
voicings SATB, des contraintes musicales dures et des poids dérivés de
marginales.
