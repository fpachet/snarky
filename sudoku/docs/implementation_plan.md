# Plan d’implémentation du Sudoku « humain »

## État d’avancement

Les phases 0 à 7 sont réalisées pour le périmètre p1–p6 :

- fixtures natives vérifiées contre les sources CLIPS ;
- mémoire mutable, journal, réfraction et index après retrait ;
- `EXISTS`/`NOT EXISTS` corrélés ;
- singles, candidats verrouillés et paires ;
- orchestrateur générique et explications rejouables ;
- solutions et familles de techniques identiques aux oracles.

La phase 8 reste ouverte pour les tests génératifs 4×4 et les optimisations
supplémentaires. Les niveaux p7 à p18 restent le palier avancé.

## Objectif

Le but n’est pas d’ajouter un solveur Sudoku spécialisé à côté de Snarky, mais
d’utiliser le Sudoku comme banc d’essai pour des capacités générales de
résolution de problèmes :

- modifier une mémoire de travail ;
- raisonner sur l’absence d’une configuration ;
- organiser des familles de règles par difficulté ;
- expliquer chaque transformation ;
- détecter qu’un problème est résolu ou bloqué.

Le corpus de référence est l’exemple officiel CLIPS 6.4.2 présent dans
[`third_party/test_rulebases/clips-6.4.2/clips_examples_642/sudoku`](../../third_party/test_rulebases/clips-6.4.2/clips_examples_642/sudoku).
Il contient dix-huit niveaux progressifs.

Le premier objectif fonctionnel couvre les grilles 9×9 `grid3x3-p1.clp` à
`grid3x3-p6.clp` :

| Niveau | Techniques supplémentaires attendues |
|---|---|
| p1 | Naked Single |
| p2 | Hidden Single |
| p3 | Locked Candidate Single Line |
| p4 | Locked Candidate Multiple Lines |
| p5 | Naked Pairs |
| p6 | Hidden Pairs |

Cette cible constitue déjà une résolution logique progressive et explicable.
Les niveaux p7 à p18, qui introduisent notamment X-Wing, triples, coloriage,
chaînes forcées et rectangle unique, sont hors du premier périmètre.

## Ce que Snarky sait déjà faire

La représentation des données n’est pas bloquante. Une case peut être décrite
par des faits ordinaires :

```text
(r1c1 row 1)
(r1c1 column 1)
(r1c1 box 1)
(r1c1 candidate 5)
```

Les triplets récursifs, les jointures, les variables, les comparaisons,
l’arithmétique locale et la provenance existantes suffisent pour représenter
la grille et les relations entre cases.

`RuleGroup` et `InferenceSession` apportent déjà le contrôle nécessaire pour
séparer les techniques :

```text
GROUP naked_singles
    ...
END_GROUP

GROUP hidden_singles
    ...
END_GROUP
```

Un orchestrateur peut appeler les groupes du plus simple au plus complexe,
recommencer au premier après chaque progrès et s’arrêter quand la grille est
résolue ou qu’aucune technique ne s’applique.

## Écarts fonctionnels

| Capacité | État | Nécessité pour p1–p6 |
|---|---|---|
| Faits structurés et jointures | Disponible | Suffisant |
| Comparaisons `==`, `!=`, `<`, etc. | Disponible | Suffisant |
| Groupes et sessions persistantes | Disponible | Suffisant |
| Modes saturation/pas-à-pas/jusqu’à un but | Disponible | Suffisant |
| Suppression d’un fait | Disponible | Critique |
| Prémisse existentielle négative corrélée | Disponible | Critique |
| Réfaction et index compatibles avec les suppressions | Disponibles | Critique |
| Trace des suppressions et décisions | Disponible | Critique pour expliquer |
| Ordonnancement des techniques | Disponible via `TechniquePlan` | Requis |
| Agrégats ou cardinalités | Absents | Utiles, mais non indispensables à p1–p6 |
| Salience CLIPS | Absente | Non nécessaire avec les groupes |
| `deftemplate` CLIPS | Absent | Non nécessaire |
| Retour arrière ou hypothèses | Absent | Hors périmètre p1–p6 |

Les deux extensions sémantiques centrales sont donc la mutation contrôlée de
la mémoire de travail et `NOT EXISTS`. Elles ne sont pas spécifiques au
Sudoku : elles servent aussi à la planification, au diagnostic, aux workflows
et à de nombreuses bases de règles de production.

## Sémantique cible

### Candidats

Une case donnée ne possède qu’un fait `candidate` correspondant à sa valeur.
Une case vide commence avec les neuf candidats. Résoudre consiste
principalement à retirer des faits `candidate`.

Cette représentation suit la logique du programme CLIPS et rend les règles
lisibles :

- un singleton nu est une case sans autre candidat ;
- un singleton caché est une valeur sans autre case candidate dans une unité ;
- une paire est caractérisée par deux candidats et l’absence d’un troisième.

### Négation

La négation doit être une prémisse existentielle corrélée, et non un statut
`INEXISTANT`. Exemple conceptuel :

```text
CANDIDATE($cell, $value)
NOT EXISTS {
    CANDIDATE($cell, $other)
    $other != $value
}
```

Les variables venant du contexte extérieur sont visibles dans le bloc négatif.
Les variables introduites dans ce bloc restent locales et ne peuvent pas être
utilisées ensuite. Cette règle de sûreté doit être vérifiée lors de la
construction ou du parsing de la règle.

### Mutation

Une activation peut ajouter et retirer des faits. Ses actions forment une
transaction logique : les tests d’arrêt et les activations suivantes ne voient
le nouvel état qu’après l’exécution complète de l’activation.

Retirer un fait absent est un non-changement déterministe, pas une erreur.
Chaque retrait effectif produit cependant un événement explicable contenant
la règle, le groupe, la substitution, les prémisses et le cycle.

### Progression des techniques

Les groupes sont ordonnés par difficulté. Après toute modification de la
grille, le contrôle repart de la technique la plus simple :

```text
naked_singles
hidden_singles
locked_candidates_single_line
locked_candidates_multiple_lines
naked_pairs
hidden_pairs
```

Si un tour complet ne change aucun candidat, la résolution renvoie `STUCK`
avec les candidats restants. Si chaque case possède exactement un candidat et
que toutes les unités sont valides, elle renvoie `SOLVED`.

## Plan incrémental

### Phase 0 — Figer les oracles et le modèle natif

1. Créer le sous-projet autonome `sudoku/`, avec ses fixtures et ses tests.
2. Transcrire les indices et solutions attendues de p1 à p6 dans un format
   natif compact, avec un lien explicite vers chaque fichier CLIPS source.
3. Écrire un chargeur qui produit les faits `row`, `column`, `box` et
   `candidate`.
4. Écrire un validateur Python indépendant du moteur :
   - 81 cases ;
   - une seule valeur finale par case ;
   - valeurs 1 à 9 uniques dans chaque ligne, colonne et boîte ;
   - respect des indices initiaux.
5. Ajouter un rendu textuel déterministe de la grille et des candidats pour
   faciliter le diagnostic des tests.

Critère de sortie : les six fixtures sont chargées, leurs solutions de
référence passent le validateur et une solution volontairement corrompue est
rejetée.

### Phase 1 — Mémoire de travail mutable

1. Ajouter `NaiveFactStore.remove(fact) -> bool`.
2. Ajouter une action publique `RemoveFact` et la syntaxe DSL
   `REMOVE <fact>`.
3. Étendre le résultat d’un appel de groupe avec :
   - `removed_facts` ;
   - `changed` ;
   - un nombre total de mutations.
4. Faire dépendre `FIRST_CHANGE` de toute mutation effective, pas seulement
   d’un ajout.
5. Exécuter les actions d’une activation comme une unité logique.
6. Introduire un journal chronologique `InferenceEvent` pour les ajouts et
   retraits, sans effacer l’histoire lorsqu’un fait quitte la mémoire.
7. Définir précisément le comportement d’un fait retiré puis réintroduit.

Critère de sortie : tests unitaires des ajouts/retraits mixtes, de l’atomicité,
des non-opérations, de la provenance et des modes de `RuleGroup`.

### Phase 2 — Réfaction et instanciation après mutation

Les index actuels ne savent que s’étendre. La première version mutable doit
privilégier la correction :

1. invalider et reconstruire l’index d’une règle après un retrait pertinent ;
2. recalculer exhaustivement les activations dans l’oracle naïf ;
3. conserver dans la réfraction les activations encore continûment actives ;
4. oublier une activation lorsqu’elle cesse de satisfaire son côté gauche,
   afin qu’elle puisse redevenir éligible plus tard ;
5. couvrir les sessions qui alternent plusieurs groupes ;
6. ajouter des tests différentiels entre stratégies naïve et indexée.

Une optimisation incrémentale des suppressions viendra seulement après les
mesures Sudoku. Pour p1–p6, reconstruire un index sur quelques centaines de
faits reste acceptable.

Critère de sortie : les stratégies produisent exactement les mêmes mutations
et le même journal sur des séquences contenant ajouts, retraits et
réintroductions.

### Phase 3 — Prémisses `EXISTS` et `NOT EXISTS`

1. Ajouter des prémisses `ExistsPremise` et `NotExistsPremise` portant sur une
   conjonction de prémisses.
2. Implémenter d’abord leur sémantique dans la stratégie naïve.
3. Vérifier statiquement la portée des variables :
   - les variables extérieures peuvent être lues ;
   - les variables locales ne s’échappent pas ;
   - une comparaison ne s’exécute que lorsque ses opérandes sont liés.
4. Ajouter une syntaxe DSL explicite, par exemple :

   ```text
   NOT EXISTS
       ($cell candidate $other)
       $other != $value
   END_EXISTS
   ```

5. Étendre la stratégie indexée en réutilisant les index de faits dans les
   sous-jointures existentielles.
6. Définir l’invalidation : un ajout peut rendre faux un `NOT EXISTS`, un
   retrait peut le rendre vrai.

Critère de sortie : tests corrélés et non corrélés, variables locales,
comparaisons, changements de vérité après mutation et équivalence des
stratégies.

### Phase 4 — Singles et première grille complète

Créer les groupes natifs :

1. `derive_solved_cells` : une case n’ayant qu’un candidat produit un fait
   explicatif `solved`;
2. `naked_singles` : élimination de la valeur résolue dans les cases qui
   partagent sa ligne, sa colonne ou sa boîte ;
3. `hidden_singles` : lorsqu’une valeur n’est candidate que dans une case
   d’une unité, élimination des autres candidats de cette case ;
4. `validate_state` : détection d’une case sans candidat ou de deux valeurs
   résolues identiques dans une unité.

Chaque élimination doit enregistrer :

- la technique ;
- la case et la valeur éliminée ;
- l’unité concernée ;
- les faits qui justifient l’élimination.

Critères de sortie :

- p1 est résolue avec le seul groupe `naked_singles`;
- p2 nécessite effectivement `hidden_singles`;
- aucune grille invalide n’est déclarée résolue ;
- la trace permet d’expliquer chaque valeur finale.

### Phase 5 — Orchestrateur générique de techniques

Implémenter un petit composant Python, sans logique Sudoku codée dans le
moteur :

```python
plan = TechniquePlan(
    naked_singles,
    hidden_singles,
    locked_candidates_single_line,
    locked_candidates_multiple_lines,
    naked_pairs,
    hidden_pairs,
)
result = plan.solve(session, solved=..., inconsistent=...)
```

Le composant :

1. appelle les groupes dans l’ordre ;
2. repart du premier après un changement ;
3. distingue `SOLVED`, `STUCK`, `INCONSISTENT` et `LIMIT_REACHED`;
4. conserve la séquence des groupes essayés et efficaces ;
5. accepte les conditions d’arrêt déclaratives de la session ;
6. ne connaît ni les lignes, ni les colonnes, ni les candidats.

Ce composant est une première forme légère de plan SHAL. Il doit rester
générique afin de servir ultérieurement au diagnostic ou à d’autres problèmes.

Critère de sortie : les tests démontrent la priorité des groupes, le retour à
la technique la plus simple et un arrêt `STUCK` reproductible.

### Phase 6 — Candidats verrouillés et paires

Ajouter successivement :

1. `locked_candidates_single_line` pour p3 ;
2. `locked_candidates_multiple_lines` pour p4 ;
3. `naked_pairs` pour p5 ;
4. `hidden_pairs` pour p6.

Chaque technique doit exister sous forme de règles déclaratives séparées pour
les lignes, colonnes et boîtes. Les alternatives simples peuvent être
exprimées par plusieurs règles plutôt que par un opérateur `OR` prématuré.

Après les paires, mesurer la verbosité et le coût. Un agrégat général
`COUNT`/`COLLECT` ne sera ajouté que si les règles ou les performances montrent
un besoin réel. Cela évite une fonctionnalité conçue uniquement autour du
Sudoku tout en laissant une voie claire vers les triples et les motifs
avancés.

Critère de sortie : p1 à p6 sont toutes résolues, et désactiver le dernier
groupe requis laisse chaque grille correspondante dans l’état `STUCK`.

### Phase 7 — Explications de niveau humain

1. Transformer le journal bas niveau en étapes :
   `technique`, `supports`, `eliminations`, `nouvelle valeur`.
2. Regrouper les retraits produits par une même activation.
3. Préserver l’ordre chronologique, indépendamment de la provenance minimale.
4. Produire un rendu stable, par exemple :

   ```text
   Hidden Single: la valeur 7 n’apparaît qu’en r4c2 dans la colonne 2;
   retrait de {1, 3, 8} en r4c2.
   ```

5. Vérifier chaque étape en rejouant la trace depuis les indices initiaux.

Critère de sortie : une trace de p1 et une trace de p6 sont rejouables et
chaque retrait est justifié par des faits présents juste avant l’étape.

### Phase 8 — Robustesse et performances

1. Ajouter des tests génératifs sur de petits Sudoku 4×4.
2. Comparer naïf et indexé sur les mêmes grilles et journaux.
3. Mesurer activations, tentatives de matching, reconstructions d’index et
   mémoire maximale.
4. Ajouter un index de règles candidates réveillées par un ajout ou retrait.
5. Fixer des baselines reproductibles pour p1 à p6.

Critère de sortie : aucun écart sémantique entre stratégies et absence de
régression mesurable non expliquée.

## Après le périmètre essentiel

Les niveaux p7 à p18 doivent être abordés comme de nouveaux paliers :

- X-Wing, triples et Swordfish peuvent motiver `COUNT`, `COLLECT`, ensembles
  ordonnés ou combinaisons finies ;
- coloriage et chaînes demandent des identités temporaires, des graphes de
  dépendance et éventuellement des symboles frais ;
- chaînes forcées et hypothèses demandent des contextes isolés, du retour
  arrière ou une vérité conditionnelle ;
- rectangle unique exige une sémantique explicite de l’unicité de solution.

Ces fonctionnalités ne doivent pas être introduites pour faire artificiellement
passer tout le corpus. Chaque palier devra d’abord être formulé comme capacité
générale du moteur, avec son propre oracle sémantique.

## Ordre recommandé

Le chemin critique est :

```text
RuleGroup
  → REMOVE et journal de mutations
  → réfraction/index compatibles avec les retraits
  → NOT EXISTS corrélé
  → Naked/Hidden Singles
  → orchestrateur de techniques
  → Locked Candidates
  → Naked/Hidden Pairs
  → explications et optimisation
```

Le premier jalon visible est p1, après les phases 0 à 4. Le jalon « Sudoku
essentiel » est atteint à la fin de la phase 7 avec p1 à p6 résolues et
expliquées sans recherche exhaustive ni solveur externe.
