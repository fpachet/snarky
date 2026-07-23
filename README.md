# Snarky

Snarky est un moteur d’inférence symbolique en Python inspiré de SNARK, de
Jean-Louis Laurière, et de BOOJUM, développé par Jean-Luc Dormoy. Il ne cherche
pas à reproduire exactement BOOJUM : Snarky possède sa propre sémantique et
sera notamment enrichi par du raisonnement sous contraintes.

## Pourquoi « Snarky » ?

Le nom rend d’abord hommage au langage historique SNARK, l’une des principales
sources d’inspiration du projet. Il constitue aussi un clin d’œil à Snarky
Puppy, groupe emblématique de la fusion musicale.

Cette idée de fusion décrit l’ambition de Snarky : faire coopérer dans un même
moteur des langages de règles symboliques, des solveurs de contraintes tels
qu’OR-Tools et, à terme, d’autres algorithmes d’inférence. Snarky ne désigne donc
pas une réimplémentation de SNARK ou de BOOJUM, mais un moteur hybride qui en
prolonge certains principes.

L’objectif est de construire un moteur expressif, déterministe et testable,
capable de manipuler :

- des règles d’ordre 0, 1 et 2 ;
- des variables dans les trois positions d’un triplet, y compris en position
  relation ;
- des triplets récursifs et des propositions utilisées comme objets ;
- des statuts explicites tels que `VRAI`, `FAUX` et `INEXISTANT` ;
- le chaînage avant récursif, la réfraction et la provenance des faits ;
- plusieurs stratégies d’instanciation, d’un matcher naïf de référence à des
  stratégies centrées sur les variables et la propagation de contraintes.

Le projet ne prétend pas reproduire à l’identique le logiciel historique
BOOJUM. Chaque fonctionnalité devra être qualifiée comme `HISTORICAL`,
`INFERRED` ou `MODERN_EXTENSION`.

## État actuel

Le dépôt contient un moteur Python semi-naïf par défaut, une stratégie naïve
servant de référence sémantique et une stratégie indexée exhaustive pour les
comparaisons de performance. Le cœur prend en charge
les termes et triplets récursifs immuables, les variables dans toutes les
positions, le matching orienté, l’unification bidirectionnelle séparée, les
statuts explicites, le chaînage avant jusqu’au point fixe, la réfraction et la
provenance avec profondeur de preuve. Des groupes de règles nommés peuvent
désormais être appelés successivement dans une même session persistante, en
saturation, pour un cycle, jusqu’au premier changement ou jusqu’à un motif de
fait.

Le DSL sait également exécuter des actions arithmétiques séquentielles `LET`
dans la conclusion des règles. Cette fonctionnalité est une
`MODERN_EXTENSION` : elle évalue de manière sûre des expressions numériques
avec `+`, `-`, `*`, `/`, précédence et parenthèses, puis transmet la liaison
calculée aux actions suivantes. Il ne s’agit pas encore d’un solveur de
contraintes arithmétiques.

La mémoire de travail accepte maintenant `REMOVE`, avec un journal
chronologique des ajouts et retraits. Les prémisses corrélées `EXISTS` et
`NOT EXISTS` permettent de raisonner sur la présence ou l’absence d’une
configuration sans confondre cette absence avec le statut explicite
`INEXISTANT`.

`TechniquePlan` fournit une orchestration générique de groupes ordonnés :
après chaque changement, il repart du groupe le plus simple et distingue les
terminaisons `SOLVED`, `STUCK`, `INCONSISTENT` et `LIMIT_REACHED`. Le projet
Sudoku valide conjointement ces capacités sur six niveaux progressifs.

Le contenu actuel comprend :

- [l’atlas web de l’Éthique III](https://fpachet.github.io/snarky/), une
  exploration statique des textes, affects, 27 explications, règles, chaînes
  de preuve et dépendances producteur–consommateur entre règles, publiée
  automatiquement par GitHub Pages ;

- [`docs/prompt_codex_moteur_snarky.md`](docs/prompt_codex_moteur_snarky.md),
  la spécification détaillée du moteur ;
- [`docs/prompt_codex_spinoza_ethique_III.md`](docs/prompt_codex_spinoza_ethique_III.md),
  la spécification du cas d’étude Spinoza ;
- [`docs/Gondran.ppt`](docs/Gondran.ppt), la présentation historique de Michel
  Gondran sur la modélisation de l’*Éthique* en SNARK/BOOJUM ;
- [`docs/Cavarretta-X1988-SpinozaExpertSystem.pdf`](docs/Cavarretta-X1988-SpinozaExpertSystem.pdf),
  le rapport complet de Fabrice Cavarretta sur SpinoLog ; ses apports possibles
  au projet sont analysés dans
  [`spinoza/reports/spinolog_1988_enrichment.md`](spinoza/reports/spinolog_1988_enrichment.md) ;
- [`spinoza`](spinoza/README.md), le cas d'étude complet de l'*Éthique III* :
  corpus structuré des 59 propositions, reproduction historique des quatre
  preuves de Gondran et reconstruction systématique exécutable de E3P01 à
  E3P59 ainsi que des 48 définitions finales et de la définition générale des
  affects, avec faits, règles, provenance et contre-cas explicites ;
- [`third_party/test_rulebases`](third_party/test_rulebases/README.md), une
  sélection de corpus de règles externes ;
- [`tests/rulebases/debug`](tests/rulebases/debug/README.md), une petite base
  native destinée au debug du moteur ;
- [`tests/rulebases/fibonacci_explicit`](tests/rulebases/fibonacci_explicit/README.md),
  une base récursive de trois règles qui construit explicitement l'arbre de
  calcul de Fibonacci ;
- [`docs/semantics.md`](docs/semantics.md), les décisions sémantiques du moteur
  de référence ;
- [`docs/arithmetic_actions.md`](docs/arithmetic_actions.md), la syntaxe et la
  sémantique des liaisons arithmétiques séquentielles `LET` ;
- [`docs/rule_groups.md`](docs/rule_groups.md), les sessions persistantes, la
  syntaxe des groupes de règles et leurs différents modes d’appel ;
- [`docs/mutations_and_negation.md`](docs/mutations_and_negation.md), la
  suppression de faits, le journal de mutations et les blocs corrélés
  `EXISTS`/`NOT EXISTS` ;
- [`sudoku`](sudoku/README.md), le sous-projet autonome qui organise la base
  de règles, les fixtures natives, le solveur orchestré et le plan incrémental
  pour résoudre et expliquer les niveaux essentiels de l’exemple Sudoku
  CLIPS ;
- [`docs/optimization_plan.md`](docs/optimization_plan.md), le plan mesurable
  pour faire évoluer le moteur naïf vers des stratégies indexées, semi-naïves
  et centrées sur les contraintes ;
- [`benchmarks`](benchmarks/README.md), les scénarios reproductibles, leurs
  compteurs algorithmiques et les baselines de performance ;
- [`src/snarky`](src/snarky), le package Python et son API publique.

La base Fibonacci explicite utilise `LET $somme := $gauche + $droite` et ne
reçoit qu’un fait racine : les sommes et les rangs des fils ne sont plus
préchargés sous forme de tables.

Les modifications partielles de faits, la création de symboles frais et le
raisonnement par contraintes restent à implémenter. L’évaluation semi-naïve
est le mode par défaut de `ForwardEngine`.

## Démarrage rapide

Le projet cible Python 3.12 ou ultérieur. Depuis la racine du dépôt :

```sh
python -m pip install -e '.[dev]'
pytest
```

Pour une boucle locale rapide, les grands balayages d’intégration peuvent être
écartés avec `pytest -m "not slow"`. Si `pytest-xdist` est installé
séparément, la suite complète peut exploiter plusieurs cœurs avec
`pytest -n auto`.

Le plan et les baselines de performance, notamment pour Fibonacci et Sudoku,
sont consignés dans [`docs/optimization_plan.md`](docs/optimization_plan.md).

Exemple minimal avec l’API Python :

```python
from snarky import Atom, Fact, ForwardEngine, Rule, Triple, Variable, add, when

x = Variable("x")
y = Variable("y")
z = Variable("z")

rule = Rule(
    name="grand_parent",
    premises=(
        when(Triple(x, Atom("parent_de"), y)),
        when(Triple(y, Atom("parent_de"), z)),
    ),
    actions=(add(Triple(x, Atom("grand_parent_de"), z)),),
)

facts = (
    Fact(Triple(Atom("alice"), Atom("parent_de"), Atom("bob"))),
    Fact(Triple(Atom("bob"), Atom("parent_de"), Atom("clara"))),
)
result = ForwardEngine((rule,)).run(facts)
```

Le moteur utilise par défaut la stratégie semi-naïve. Elle maintient des index
persistants et ne recalcule que les jointures contenant un fait nouveau, sans
modifier l'ordre observable des activations. L'appel sans paramètre `strategy`
dans l'exemple ci-dessus utilise donc directement cette implémentation.

La stratégie naïve reste disponible comme oracle sémantique et comme option de
diagnostic explicite :

```python
from snarky import NaiveInstantiationStrategy

result = ForwardEngine(
    (rule,),
    strategy=NaiveInstantiationStrategy(),
).run(facts)
```

`IndexedInstantiationStrategy` reste disponible pour mesurer séparément le
bénéfice de l'indexation exhaustive.

Pour les sessions persistantes, les mutations, la négation et les plans de
groupes, voir respectivement
[`docs/rule_groups.md`](docs/rule_groups.md),
[`docs/mutations_and_negation.md`](docs/mutations_and_negation.md) et la
[spécification détaillée](docs/prompt_codex_moteur_snarky.md).

Le benchmark Fibonacci explicite mesure un passage de 7,142 s à 0,053 s pour
`F(10)` et de 27,914 s à 3,338 s pour `F(17)` sur la machine de développement.
Le benchmark Sudoku mesure désormais p1 à 0,523 s, p5 à 1,504 s et p6 à
1,462 s en médiane ; les index composés et les bloqueurs négatifs ciblés
réduisent de 71 à 75 % les matchings de la baseline précédente. Les commandes
reproductibles et les compteurs sont décrits dans
[`benchmarks/README.md`](benchmarks/README.md).

La suite complète compte 273 tests et s’exécute en 29,51 s sur cette même
machine, contre 46,88 s avant cette passe d’optimisation.

## Base de debug initiale

La base `mini_snarky` constitue le premier test d’intégration. Elle tient
en quatre règles et neuf faits initiaux, tout en testant :

1. une jointure sur deux prémisses ;
2. une relation variable ;
3. une clôture transitive récursive ;
4. des propositions imbriquées ;
5. une variable représentant une proposition complète ;
6. un statut explicite `FAUX`.

Le moteur semi-naïf par défaut et l'oracle naïf reproduisent le même point fixe
attendu : six faits dérivés, dont un à profondeur de preuve deux. Voir :

- [`mini_snarky.rules`](tests/rulebases/debug/mini_snarky.rules) ;
- [`initial_facts.yaml`](tests/rulebases/debug/initial_facts.yaml) ;
- [`expected.yaml`](tests/rulebases/debug/expected.yaml).

## Corpus externes

Le dépôt contient des sélections provenant de W3C N3, W3C RIF, CLIPS,
ChaseBench, rbench/OpenRuleBench, Soufflé et EYE. Les versions, chemins
sélectionnés, licences trouvées et sommes SHA-256 sont consignés dans
[`third_party/test_rulebases/manifest.yaml`](third_party/test_rulebases/manifest.yaml).

Ces corpus restent dans leur langage source. Ils devront être traduits par des
adaptateurs explicites ; les comparaisons ne seront valides que pour
l’intersection des sémantiques.

Les snapshots ChaseBench et rbench ne contiennent pas de licence explicite.
Leur redistribution doit donc être réévaluée avant de rendre ce dépôt public.

Pour reconstruire la sélection dans un dépôt propre :

```sh
./scripts/fetch_test_rulebases.sh
```

Le script vérifie les révisions et les sommes SHA-256, et refuse d’écraser un
répertoire existant.

## Projet Sudoku

Le répertoire [`sudoku`](sudoku/README.md) isole le cas d’étude Sudoku du cœur
du moteur et du corpus CLIPS original. Il contient :

- le [catalogue de la base de règles](sudoku/rules/catalog.yaml) p1 à p6 ;
- les règles natives et leur chargeur ;
- les fixtures natives vérifiées contre les sources CLIPS ;
- l’orchestrateur et le rendu des explications ;
- le [plan d’implémentation](sudoku/docs/implementation_plan.md), avec un
  critère d’acceptation pour chaque étape.

La base native est exécutable : les six grilles p1 à p6 sont résolues avec les
familles de techniques annoncées par le corpus CLIPS, sans recherche
exhaustive ni solveur externe. Chaque retrait de candidat est conservé dans
une trace rejouable.

## Plan de développement

1. Produire la reconstruction historique et documenter les questions
   ouvertes.
2. ~~Définir la sémantique opérationnelle minimale.~~
3. ~~Implémenter les termes immuables, substitutions et matching récursif.~~
4. ~~Faire passer la base `mini_snarky` avec un moteur naïf de référence.~~
5. ~~Ajouter la réfraction et la provenance avec profondeur de preuve.~~
6. ~~Introduire l’action arithmétique séquentielle `LET`, documenter sa
   sémantique et reformuler Fibonacci sans tables de prédécesseurs ni de
   sommes.~~
7. ~~Ajouter une première stratégie d’instanciation indexée, des compteurs et
   une baseline Fibonacci reproductible jusqu’à `F(17)`.~~
8. ~~Ajouter des index persistants par règle et une évaluation semi-naïve
   pilotée par les faits nouveaux, avec ordre et provenance identiques au
   moteur naïf.~~
9. ~~Ajouter des groupes de règles nommés, une mémoire de travail persistante
   entre leurs appels et plusieurs modes de contrôle du chaînage avant.~~
10. ~~Ajouter les suppressions, un journal de mutations et les prémisses
    corrélées `EXISTS`/`NOT EXISTS`, puis résoudre les niveaux Sudoku p1 à
    p6 par techniques progressives.~~
11. Renforcer le moteur mutable par des tests génératifs 4×4, des tests
    différentiels sur les retraits et des mesures de reconstruction d’index.
12. ~~Reproduire les démonstrations Spinoza P19, P21, P22 et P33, importer la
    structure textuelle complète de l'Éthique III, puis rendre exécutables les
    59 propositions, les 48 définitions finales et la définition générale dans
    le modèle systématique.~~
13. Ajouter une couche optionnelle de raisonnement par contraintes pour
   exprimer et résoudre des problèmes de satisfaction (CSP, SAT et variantes),
   notamment au moyen d’un adaptateur vers OR-Tools. Le moteur d’inférence
   devra pouvoir produire des contraintes, appeler le solveur, puis réinjecter
   les solutions et contradictions obtenues comme faits assortis de leur
   provenance.
14. Exécuter les benchmarks externes adaptés, puis ajouter des cas de test
    dédiés au couplage entre règles et contraintes.
15. Aborder le Sudoku avancé à partir de p7, en n’ajoutant `COUNT`, `COLLECT`,
    ensembles finis, symboles frais ou hypothèses que lorsque plusieurs cas
    d’usage en justifient la généralité.
16. ~~Optimiser, à partir du profil Sudoku, les index composés, le matching
    ground, les substitutions, les caches existentiels et l’invalidation
    directe des bloqueurs négatifs simples.~~ Poursuivre avec les activations
    paresseuses, la planification générale des jointures et la sélection des
    règles positives candidates.

La cible est Python 3.12 ou ultérieur, avec `pytest`, `ruff`, `mypy` et des
tests différentiels. L’ajout de tests génératifs fondés sur Hypothesis reste
prévu.
Les solveurs externes, dont OR-Tools, resteront des dépendances optionnelles
derrière une interface générique afin de préserver un cœur symbolique léger et
de permettre l’utilisation future d’autres backends.
