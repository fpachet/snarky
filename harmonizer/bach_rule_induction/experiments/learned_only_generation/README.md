# Génération par règles apprises seulement

Ce dossier contient la première boucle fermée de V4 :

```text
base apprise → génération → diagnostic → induction → contrôle nul
```

## V4.1 — génération diagnostique

`run_diagnostic.py` charge le manifeste `S-LEARNED`, fixe quatre attaques de
soprano provenant de cinq chorals du `train`, puis génère les trois voix
inférieures pour deux graines. Aucune règle historique ni aucun vocabulaire
d'accords n'est chargé.

Les sorties reproductibles sont conservées dans :

- `results/v4_1_learned_only_diagnostic.json` ;
- `results/V4_1_LEARNED_ONLY_DIAGNOSTIC_REPORT.md` ;
- `results/generated/*.musicxml`.

Cette étape teste l'autonomie, la traçabilité et la génération. Elle ne teste
pas encore une qualité comparable à Bach ou DeepBach.

## V4.2 — première réinduction

`run_vertical_order_induction.py` ouvre la première famille de défauts
préenregistrée : ordre simultané, croisements, tessitures et espacements. Il
scanne cinq seuils numériques sans exposer le nom de la règle historique,
ajuste un poids MaxEnt conditionnel, mesure le gain sur `validation`, puis
répète la procédure sur une réponse mélangée au sein des pièces.

Le seuil `-1` — la voix inférieure dépasse strictement la voix supérieure —
est fortement pénalisé dans les données authentiques. Comme un unique contrôle
mélangé sélectionne le même seuil, avec un effet beaucoup plus faible, la carte
`R-LEARNED-ORDER-001` reste `CANDIDATE` et n'est pas chargée par `S-LEARNED`.

## Reproduction

Les scripts supposent l'environnement scientifique du projet et un
`PYTHONPATH` contenant la racine du dépôt :

```bash
python -m harmonizer.bach_rule_induction.experiments.learned_only_generation.run_diagnostic
python -m harmonizer.bach_rule_induction.experiments.learned_only_generation.run_vertical_order_induction
```

Les tests unitaires vérifient les six patrons de niveau A, la résolution
tonale, l'isolation des profils, la reproductibilité de la génération et la
construction de la feature d'ordre vertical.
