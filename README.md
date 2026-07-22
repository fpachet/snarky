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

Le dépôt contient désormais un premier moteur Python naïf servant de référence
sémantique. Il prend en charge les termes et triplets récursifs immuables, les
variables dans toutes les positions, le matching orienté, l’unification
bidirectionnelle séparée, les statuts explicites, le chaînage avant jusqu’au
point fixe, la réfraction et la provenance avec profondeur de preuve.

Le contenu actuel comprend :

- [`docs/prompt_codex_moteur_snarky.md`](docs/prompt_codex_moteur_snarky.md),
  la spécification détaillée du moteur ;
- [`docs/prompt_codex_spinoza_ethique_III.md`](docs/prompt_codex_spinoza_ethique_III.md),
  la spécification du cas d’étude Spinoza ;
- [`docs/Gondran.ppt`](docs/Gondran.ppt), la présentation historique de Michel
  Gondran sur la modélisation de l’*Éthique* en SNARK/BOOJUM ;
- [`third_party/test_rulebases`](third_party/test_rulebases/README.md), une
  sélection de corpus de règles externes ;
- [`tests/rulebases/debug`](tests/rulebases/debug/README.md), une petite base
  native destinée au debug du moteur ;
- [`tests/rulebases/fibonacci_explicit`](tests/rulebases/fibonacci_explicit/README.md),
  une base récursive de trois règles qui construit explicitement l'arbre de
  calcul de Fibonacci ;
- [`docs/semantics.md`](docs/semantics.md), les décisions sémantiques du moteur
  de référence ;
- [`docs/optimization_plan.md`](docs/optimization_plan.md), le plan mesurable
  pour faire évoluer le moteur naïf vers des stratégies indexées, semi-naïves
  et centrées sur les contraintes ;
- [`src/snarky`](src/snarky), le package Python et son API publique.

## Démarrage rapide

Le projet cible Python 3.12 ou ultérieur. Depuis la racine du dépôt :

```sh
python -m pip install -e '.[dev]'
pytest
```

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

Le moteur naïf reste le comportement par défaut et sert d'oracle sémantique.
Pour les bases plus importantes, la stratégie indexée réduit les candidats
avant le matching sans modifier l'ordre des activations :

```python
from snarky import IndexedInstantiationStrategy

result = ForwardEngine(
    (rule,),
    strategy=IndexedInstantiationStrategy(),
).run(facts)
```

Le benchmark Fibonacci explicite mesure un passage de 8,800 s à 0,267 s pour
`F(10)` sur la machine de développement. La commande reproductible et les
compteurs sont décrits dans [`benchmarks/README.md`](benchmarks/README.md).

## Base de debug initiale

La base `mini_snarky` constitue le premier test d’intégration. Elle tient
en quatre règles et neuf faits initiaux, tout en testant :

1. une jointure sur deux prémisses ;
2. une relation variable ;
3. une clôture transitive récursive ;
4. des propositions imbriquées ;
5. une variable représentant une proposition complète ;
6. un statut explicite `FAUX`.

Le moteur naïf reproduit son point fixe attendu : six faits dérivés, dont un à
profondeur de preuve deux. Voir :

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

## Plan de développement

1. Produire la reconstruction historique et documenter les questions
   ouvertes.
2. ~~Définir la sémantique opérationnelle minimale.~~
3. ~~Implémenter les termes immuables, substitutions et matching récursif.~~
4. ~~Faire passer la base `mini_snarky` avec un moteur naïf de référence.~~
5. Ajouter provenance, indexation et stratégies d’instanciation optimisées.
6. Reproduire les démonstrations Spinoza P19, P21, P22 et P33.
7. Ajouter une couche optionnelle de raisonnement par contraintes pour
   exprimer et résoudre des problèmes de satisfaction (CSP, SAT et variantes),
   notamment au moyen d’un adaptateur vers OR-Tools. Le moteur d’inférence
   devra pouvoir produire des contraintes, appeler le solveur, puis réinjecter
   les solutions et contradictions obtenues comme faits assortis de leur
   provenance.
8. Exécuter les benchmarks externes adaptés, puis ajouter des cas de test
   dédiés au couplage entre règles et contraintes.

La cible prévue est Python 3.12 ou ultérieur, avec `pytest`, `ruff`, un
vérificateur de types et des tests différentiels fondés sur Hypothesis.
Les solveurs externes, dont OR-Tools, resteront des dépendances optionnelles
derrière une interface générique afin de préserver un cœur symbolique léger et
de permettre l’utilisation future d’autres backends.
