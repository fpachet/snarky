# Snarky

Snarky est un projet de moteur d’inférence symbolique en Python inspiré de
SNARK, de Jean-Louis Laurière, et surtout de BOOJUM, développé par Jean-Luc
Dormoy.

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

Le dépôt est dans sa phase initiale de reconstruction et de préparation des
tests. Le moteur Python n’est pas encore implémenté.

Le contenu actuel comprend :

- [`docs/prompt_codex_moteur_boojum.md`](docs/prompt_codex_moteur_boojum.md),
  la spécification détaillée du moteur ;
- [`docs/prompt_codex_spinoza_ethique_III.md`](docs/prompt_codex_spinoza_ethique_III.md),
  la spécification du cas d’étude Spinoza ;
- [`docs/Gondran.ppt`](docs/Gondran.ppt), la présentation historique de Michel
  Gondran sur la modélisation de l’*Éthique* en SNARK/BOOJUM ;
- [`third_party/test_rulebases`](third_party/test_rulebases/README.md), une
  sélection de corpus de règles externes ;
- [`tests/rulebases/debug`](tests/rulebases/debug/README.md), une petite base
  native destinée au debug du futur moteur.

## Base de debug initiale

La base `mini_boojum` constitue le premier objectif d’intégration. Elle tient
en quatre règles et neuf faits initiaux, tout en testant :

1. une jointure sur deux prémisses ;
2. une relation variable ;
3. une clôture transitive récursive ;
4. des propositions imbriquées ;
5. une variable représentant une proposition complète ;
6. un statut explicite `FAUX`.

Le point fixe attendu contient six faits dérivés, dont un à profondeur de
preuve deux. Voir :

- [`mini_boojum.rules`](tests/rulebases/debug/mini_boojum.rules) ;
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
2. Définir la sémantique opérationnelle minimale.
3. Implémenter les termes immuables, substitutions et matching récursif.
4. Faire passer la base `mini_boojum` avec un moteur naïf de référence.
5. Ajouter provenance, indexation et stratégies d’instanciation optimisées.
6. Reproduire les démonstrations Spinoza P19, P21, P22 et P33.
7. Exécuter les benchmarks externes adaptés.

La cible prévue est Python 3.12 ou ultérieur, avec `pytest`, `ruff`, un
vérificateur de types et des tests différentiels fondés sur Hypothesis.
