# Base de règles Sudoku

Ce répertoire est réservé à la base de règles native du projet Sudoku.

Le fichier [`catalog.yaml`](catalog.yaml) constitue son inventaire normatif :
il définit l’ordre des groupes, les noms de règles prévus, le niveau CLIPS
visé et les capacités génériques requises.

## Fichiers exécutables

```text
topology.rules
singles.rules
locked_candidates.rules
pairs.rules
validation.rules
```

Chaque fichier contient des blocs `GROUP ... END_GROUP` lus par
`parse_rule_groups`.

## Conventions

- une case est un atome stable tel que `r4c7` ;
- ses coordonnées et sa boîte sont des faits séparés ;
- `(r4c7 candidate 3)` signifie que 3 est encore possible ;
- une suppression de candidat doit produire un événement explicatif ;
- une règle de technique ne doit ni imprimer ni piloter le groupe suivant ;
- les variantes ligne, colonne et boîte restent des règles distinctes ;
- les règles sont ordonnées de manière déterministe dans chaque groupe.

La salience CLIPS n’est pas traduite. Sa fonction est remplacée par l’ordre
explicite des groupes dans l’orchestrateur et par les modes d’exécution de
`InferenceSession`.
