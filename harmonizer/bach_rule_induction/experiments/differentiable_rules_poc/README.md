# POC différentiable d'induction de règles

Ce POC teste une question volontairement étroite :

> Des clauses locales courtes, apprises par gradient à partir de hauteurs
> numériques, font-elles émerger des régularités reconnaissables de conduite
> des voix sans recevoir leurs noms musicologiques ?

La première expérience masque chaque attaque de soprano. Elle classe toutes les
hauteurs de l'ambitus historique de la soprano (`60..81`) en connaissant :

- la soprano précédente ;
- la basse entendue au même instant précédent ;
- la basse entendue à l'instant courant ;
- l'identité de la pièce et les deux positions temporelles, uniquement pour le
  partage et la traçabilité.

Le rythme, la basse et les autres décisions de Bach ne sont pas générés.

## Ce qui n'est pas fourni

Le mineur ne reçoit aucun prédicat nommé :

- `perfect_fifth` ou `perfect_octave` ;
- `similar_motion`, `parallel_motion` ou `direct_motion` ;
- `parallel_fifth` ou `direct_octave`.

Il reçoit des tests numériques génériques :

```text
intervalle_source modulo 12 == k
intervalle_candidat modulo 12 == k
delta_soprano > 0, == 0 ou < 0
delta_basse > 0, == 0 ou < 0
abs(delta_soprano) > k
```

Les constantes `k` sont énumérées sans étiquette musicale. Les clauses sont des
conjonctions d'au plus quatre familles de tests.

## Où intervient le gradient

Pour une opportunité `i`, une candidate `c` et une clause booléenne `r` :

```text
score(i, c) = somme_r poids_r * clause_r(i, c)
P(c | i) = softmax_c(score(i, c))
```

Le gradient de la log-vraisemblance conditionnelle à poids nul mesure quelles
clauses séparent le choix de Bach des candidates disponibles. Il guide le beam
search. Les colonnes retenues sont ensuite ajustées conjointement par Adam avec
une pénalité L1, toujours à partir de la même loss conditionnelle.

Les candidates non choisies ne sont jamais étiquetées comme des erreurs.

## Invention symbolique minimale

Après apprentissage, une passe de compression recherche les clauses symétriques :

```text
delta_soprano > 0 AND delta_basse > 0 AND X
delta_soprano < 0 AND delta_basse < 0 AND X
```

Si les deux queues statistiques vont dans le même sens, le rapport propose le
prédicat dérivé anonyme :

```text
PREDICATE_same_nonzero_sign :=
    (delta_soprano > 0 AND delta_basse > 0)
 OR (delta_soprano < 0 AND delta_basse < 0)
```

Le rapprochement avec un concept musicologique est effectué seulement dans
l'analyse postérieure, jamais pendant l'apprentissage.

## Corpus et partage

La source est l'archive officielle `music21-3.1.0.tar.gz` conservée dans le
projet frère `deepbach-reference`. Seules les 352 pièces incluses dans le
manifeste historique sont analysées.

Le partage déterministe, réalisé avant tout événement, est :

- 246 chorals d'apprentissage ;
- 53 chorals de validation ;
- 53 chorals de test scellé.

Le POC ne lit aucune métrique du test sans l'option explicite `--open-test`.

## Exécution

Depuis la racine de Boojum, l'environnement de référence DeepBach fournit
actuellement NumPy et Music21 :

```sh
../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/run_poc.py
```

Pour un smoke test :

```sh
../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/run_poc.py \
  --max-pieces 12 \
  --max-steps 30 \
  --beam-size 64
```

Les partitions extraites et les matrices de travail sont placées dans `work/`,
ignoré par Git. Les résultats compacts et le rapport sont écrits dans
`results/`.

Les observations et limites du premier lancement complet sont synthétisées
dans [`ANALYSIS.md`](ANALYSIS.md). Les sorties principales sont :

- [`results/REPORT.md`](results/REPORT.md) pour le modèle authentique compact ;
- [`results/NULL_REPORT.md`](results/NULL_REPORT.md) pour le contrôle mélangé ;
- les fichiers JSON homonymes pour les statistiques complètes.

## POC V2.1 — génération de colonnes

Le second incrément ajuste d'abord des effets numériques génériques, puis
recherche une clause à la fois sur le résidu conditionnel du catalogue courant :

```sh
../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/\
run_column_generation.py
```

Le contrôle nul et la branche limitée aux évitements sont :

```sh
../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/\
run_column_generation.py \
  --null-shuffle \
  --output-stem v2_null

../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/\
run_column_generation.py \
  --column-direction avoid \
  --output-stem v2_avoid
```

Le V2 ne contient aucune option d'ouverture du test scellé. Son
[`V2_ANALYSIS.md`](V2_ANALYSIS.md) montre que les classes `0` et `7` sont les
seules retenues dans la famille des arrivées après saut en même direction. Les
formules obtenues sont équivalentes aux règles Snarky de mouvement direct sur
301 401 états locaux valides par classe, sans désaccord.

Sorties principales :

- [`results/V2_RESULT_REPORT.md`](results/V2_RESULT_REPORT.md) ;
- [`results/V2_NULL_REPORT.md`](results/V2_NULL_REPORT.md) ;
- [`results/V2_AVOID_REPORT.md`](results/V2_AVOID_REPORT.md) ;
- les trois fichiers JSON correspondants.

## Interprétation prudente

Une valeur conditionnelle extrême est une hypothèse de règle, pas une preuve
normative. Le rapport distingue :

- la disponibilité moyenne de la propriété parmi les candidates ;
- sa fréquence parmi les choix de Bach ;
- le score normalisé de l'écart ;
- le poids conjoint après prise en compte des autres clauses ;
- le support en opportunités et en pièces ;
- la stabilité entre train et validation.

Le test final reste fermé tant que le vocabulaire, les pénalités et les
critères de sélection ne sont pas gelés.
