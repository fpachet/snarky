# Catalogue des bases de règles

Ce répertoire rassemble les bases de règles fournies avec Snarky. Il sépare
les exemples pédagogiques courts, les reformulations historiques et les deux
grands projets du dépôt.

```text
rulebases/
├── small/                  exemples minimaux et pédagogiques
├── constraints/            propagation CSP écrite en règles Snarky
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

Une base peut aussi fournir un compagnon Python lorsqu'elle illustre une
interface qui ne peut pas être déclarée dans le DSL, comme le registre de
prédicats calculés de la géométrie. La connaissance métier reste néanmoins
dans les règles dès que le langage le permet. Les quatre reines engendrent
leurs combinaisons par saturation et Hanoï dérécursive entièrement ses appels
au moyen de faits de sous-problèmes.

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

[`constraints`](constraints/README.md) réifie variables, domaines,
contraintes et tables de compatibilité sous forme de faits. Son premier noyau
implémente l'arc-consistance binaire uniquement avec `NOT EXISTS`, `REMOVE`
et la saturation de groupes. Une seconde base exerce les prémisses globales
`NVALUE` et `ALL_DIFFERENT`, les bornes de cardinalité distincte et les
ensembles de Hall.

Sudoku et Spinoza restent à la racine du dépôt parce qu'ils possèdent leur
propre corpus, leurs outils et leurs tests. [`projects`](projects/README.md)
les référence sans dupliquer leurs données.
