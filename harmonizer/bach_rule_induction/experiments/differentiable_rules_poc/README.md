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

Le partage historique du V1, réalisé avant tout événement, est :

- 246 chorals d'apprentissage ;
- 53 chorals de validation ;
- 53 chorals de test scellé.

Le POC ne lit aucune métrique du test sans l'option explicite `--open-test`.

Un audit ultérieur a trouvé six groupes de mélodies identiques traversant ce
partage. Le V2 canonique utilise donc
[`results/splits.variant-safe.json`](results/splits.variant-safe.json) :

- 251 chorals d'apprentissage ;
- 50 chorals de validation ;
- 51 chorals de test scellé.

Le nouveau test est un sous-ensemble du test historique : aucune pièce déjà
exposée en train ou validation n'y a été ajoutée.

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
audit_variants.py

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
  --output-stem v2_variant_safe_null

../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/\
run_column_generation.py \
  --column-direction avoid \
  --output-stem v2_avoid
```

Par défaut, le V2 charge le partage groupé et produit `v2_variant_safe`. Il
effectue aussi 1 000 réplications bootstrap par classe en rééchantillonnant des
chorals entiers. Il ne contient aucune option d'ouverture du test scellé. Son
[`V2_ANALYSIS.md`](V2_ANALYSIS.md) montre que les classes `0` et `7` sont les
seules retenues dans la famille des arrivées après saut en même direction. Les
formules obtenues sont équivalentes aux règles Snarky de mouvement direct sur
301 401 états locaux valides par classe, sans désaccord.

Sorties principales :

- [`results/VARIANT_AUDIT.md`](results/VARIANT_AUDIT.md) ;
- [`results/V2_VARIANT_SAFE_REPORT.md`](results/V2_VARIANT_SAFE_REPORT.md) ;
- [`results/V2_VARIANT_SAFE_NULL_REPORT.md`](results/V2_VARIANT_SAFE_NULL_REPORT.md) ;
- [`results/V2_AVOID_REPORT.md`](results/V2_AVOID_REPORT.md) ;
- les fichiers JSON correspondants.

Les anciens rapports `V2_RESULT` et `V2_NULL` sont conservés pour provenance,
mais leur partage contient les fuites par variantes documentées par l'audit.
Les clauses canoniques retenues sont publiées dans
[`rules/R-LEARNED-DIRECT-001.yaml`](../../rules/R-LEARNED-DIRECT-001.yaml) et
[`rules/R-LEARNED-DIRECT-002.yaml`](../../rules/R-LEARNED-DIRECT-002.yaml).

## POC V2.2 — contraintes locales dans les quatre voix

Le troisième incrément construit des décisions pour soprano, alto, ténor et
basse, puis scanne uniformément les douze classes mélodiques et neuf seuils
d'espacement entre voix adjacentes :

```sh
../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/\
run_satb_level_a.py

../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/\
run_satb_level_a.py \
  --null-shuffle \
  --output-stem v2_2_satb_level_a_null
```

Le gradient résiduel filtre les candidates. Un budget d'une règle par famille
et une encoche locale relativement aux valeurs numériques voisines empêchent
de transformer toute rareté en interdiction. Le corpus authentique retient la
classe mélodique `6` et la frontière d'overlap `0`; le contrôle permuté ne
retient rien. Les deux formules sont équivalentes aux règles cachées
`R-MELODY-002` et `R-OVERLAP-001` sur les domaines finis testés.

Voir [`V2_2_ANALYSIS.md`](V2_2_ANALYSIS.md), les rapports
[`V2_2_SATB_LEVEL_A_REPORT.md`](results/V2_2_SATB_LEVEL_A_REPORT.md) et
[`V2_2_SATB_LEVEL_A_NULL_REPORT.md`](results/V2_2_SATB_LEVEL_A_NULL_REPORT.md).

## POC V2.3 — parallèles dans les six paires de voix

Le V2.3 recherche le même patron de répétition d'intervalle dans les six
paires SATB, avec un budget de deux règles :

```sh
../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/\
run_satb_parallels.py

../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/\
run_satb_parallels.py \
  --null-shuffle \
  --output-stem v2_3_satb_parallels_null
```

Les classes `0` et `7` sont seules retenues ; le contrôle nul ne retient
aucune classe. Les deux formules sont équivalentes à `R-PARALLEL-001/002` sur
1 130 364 états locaux valides par classe.

Voir [`V2_3_ANALYSIS.md`](V2_3_ANALYSIS.md) et le
[`rapport canonique`](results/V2_3_SATB_PARALLELS_REPORT.md).

## POC V2.4 — ablation conjointe

Les sept règles de niveau A sont ensuite ajustées dans un même catalogue :

```sh
../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/\
run_satb_ablation.py
```

Elles réduisent ensemble la NLL de validation de `1,355250` à `1,287062`.
Neutraliser n'importe laquelle des sept colonnes augmente la perte ; les
octaves et quintes parallèles ont les contributions propres les plus fortes.
Le contrôle permuté ne gagne que `0,006307`, contre `0,068188` sur les chorals.

Voir [`V2_4_ANALYSIS.md`](V2_4_ANALYSIS.md) et le
[`rapport d'ablation`](results/V2_4_SATB_ABLATION_REPORT.md).

## POC V2.5 — ablation réajustée par groupe

Le V2.5 retire chaque famille puis réestime depuis zéro tous les poids
restants :

```sh
../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/\
run_satb_group_refit.py
```

Après compensation, les pénalités de validation restent positives :
`+0,051384` pour les parallèles, `+0,008753` pour la mélodie, `+0,005419`
pour l'overlap et `+0,000997` pour les mouvements directs. Dans le contrôle,
la pénalité des parallèles est pratiquement nulle.

Voir [`V2_5_ANALYSIS.md`](V2_5_ANALYSIS.md) et le
[`rapport canonique`](results/V2_5_SATB_GROUP_REFIT_REPORT.md).

## POC V3.1 — première obligation tonale

Le V3.1 scanne les douze classes sources relatives à la tonique globale pour
la conclusion positive `candidate == previous + 1` :

```sh
../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/\
run_tonal_tendency.py
```

La classe `11` est la seule retenue ; elle est interprétée après sélection
comme la sensible globale. Un pic local contre les classes voisines élimine le
faux signal observé dans le premier contrôle nul. Voir
[`V3_1_ANALYSIS.md`](V3_1_ANALYSIS.md).

## POC V3.2–V3.3 — raffinements et ajout du mode

Le V3.2 énumère 432 contextes `voix × basse source × basse cible`. Le V3.3
ajoute le mode comme statut explicite et en teste 864 :

```sh
../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/\
run_leading_tone_refinement.py

../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/\
run_leading_tone_refinement.py \
  --stratify-mode \
  --min-train-support 20 \
  --candidate-budget 8 \
  --output-stem v3_3_mode_stratified_leading_tone
```

Sept clauses passent train et validation dans le V3.3, contre aucune après
permutation. L'audit des états leur associe postérieurement des proxys de
progressions harmoniques usuelles. Voir
[`V3_2_ANALYSIS.md`](V3_2_ANALYSIS.md) et
[`V3_3_ANALYSIS.md`](V3_3_ANALYSIS.md).

## POC V3.4 — calibration de la famille complète

Le V3.4 répète 49 fois le pipeline nul, baseline et scan des 864 clauses
compris :

```sh
../deepbach-reference/.venv/bin/python \
  harmonizer/bach_rule_induction/experiments/differentiable_rules_poc/\
run_tonal_family_calibration.py
```

Pour chaque permutation, il conserve le maximum de
`min(z_train, z_validation)` parmi toutes les clauses suffisamment supportées.
Le quantile nul à 95 % vaut `4,817` et le maximum `6,205`. Une seule clause
authentique survit : `majeur + alto + basse 2→4`, avec `p FWER = 0,02`.

Voir [`V3_4_ANALYSIS.md`](V3_4_ANALYSIS.md) et le
[`rapport canonique`](results/V3_4_TONAL_FAMILY_CALIBRATION_REPORT.md).

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
