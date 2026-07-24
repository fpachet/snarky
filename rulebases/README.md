# Catalogue des bases de règles

Ce répertoire rassemble les bases de règles fournies avec Snarky. Il sépare
les exemples pédagogiques courts, les reformulations historiques et les deux
grands projets du dépôt.

```text
rulebases/
├── small/                  exemples minimaux et pédagogiques
├── thesis/                 reformulations de la thèse NéOpus
├── projects/               index vers Sudoku et Spinoza
├── catalog.yaml            inventaire, maturité et besoins du moteur
└── runner.py               exécuteur commun des scénarios
```

Une base exécutable contient normalement :

- `README.md`, qui explique le problème et l'intérêt du cas ;
- `rules.rules`, dans le DSL natif de Snarky ;
- `initial_facts.yaml`, les données de départ ;
- `expected_facts.yaml`, un oracle minimal ;
- `scenario.yaml`, l'ordre d'appel des groupes.

Un scénario peut aussi déclarer `conflict_strategy: mea`. L’option `--trace`
affiche alors chaque sélection de l’agenda, sa fraîcheur et ses mutations :

```sh
uv run python -m rulebases.runner \
  thesis/monkey_bananas/neopus_mea --trace
```

La commande suivante exécute un scénario et vérifie son oracle :

```sh
uv run python -m rulebases.runner thesis/tomorrow_date
```

## Catégories

Les exemples de [`small`](small/README.md) isolent une propriété du moteur et
servent de tutoriels ou de micro-benchmarks. Les exemples de
[`thesis`](thesis/README.md) reconstruisent des bases décrites dans la thèse
NéOpus de François Pachet. Certaines sont des noyaux exécutables délibérément
bornés : leur README distingue toujours ce qui est effectivement reproduit de
ce qui demanderait une extension générale du moteur.

Sudoku et Spinoza restent à la racine du dépôt parce qu'ils possèdent leur
propre corpus, leurs outils et leurs tests. [`projects`](projects/README.md)
les référence sans dupliquer leurs données.
