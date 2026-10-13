# Filtrage exact de SUM + ALLDIFF à trois variables

Expérience du **13 octobre 2026**, après le
[filtrage par bornes distinctes](../magic_sum_distinct_2026-10-13/README.md) et
[l'optimisation de son coût](../magic_sum_distinct_cost_2026-10-13/README.md).

## Algorithme et périmètre

Le réglage optionnel `exact` conserve la règle rapide à deux variables et remplace
les bornes distinctes par des supports exacts lorsque **trois variables restent
actives et que la somme des tailles de leurs domaines ne dépasse pas 24**.

Les termes fixés sont soustraits de la cible ; leurs valeurs sont exclues des
termes actifs. Les valeurs fixées dupliquées rendent la contrainte impossible.
L'algorithme parcourt les deux plus petits domaines, calcule `z = résidu - x - y`,
puis consulte le troisième domaine. Il conserve les supports des seuls triplets
qui vérifient la somme et trois valeurs distinctes. Il effectue au maximum
**64 vérifications de paires** par appel. Les valeurs peuvent être négatives,
très grandes ou très espacées ; aucun bitset indexé par l'étendue n'est nécessaire.

L'exactitude porte sur cette somme et la distinction de ses propres termes.
Elle ne signifie pas que chaque valeur restante possède un support dans le
modèle complet, ni dans l'ALLDIFF global avec toutes ses autres variables.
Les autres contraintes continuent leur propagation native.

Le déclenchement exige toujours une somme à coefficients +1, une égalité et un
ALLDIFF inconditionnel qui couvre toute la somme. Les sommes pondérées, signées,
les inégalités et les couvertures partielles ou conditionnelles ne qualifient
pas. Au-delà de la limite de 24 candidats, l'option `exact_three=True` utilise
les bornes existantes si les autres seuils l'autorisent ; le réglage `exact` du
benchmark saute ces révisions comme `tiny`.

Les supports sont recalculés à partir des masques courants. Les réductions
utilisent la pile de restauration et la file natives. Il n'y a aucun cache de
témoins ni d'état logique supplémentaire à restaurer. Les échecs conjoints ne
sont pas attribués arbitrairement à une contrainte originale pour `dom_wdeg`.

## Protocole

La comparaison principale oppose le solveur natif (`baseline`), le prototype
avec bornes (`tiny`) et le nouveau filtrage (`exact`). Les paramètres de recherche
sauvegardés restent identiques. Les exécutions sont séquentielles, mélangées
avec une graine fixe, et répétées trois fois. Le temps inclut modèle, état,
détection et recherche ; imports et validation indépendante sont exclus.

Les tailles 6, 8, 9, 10, 11, 12, 13, 14 et 16 recherchent une première solution.
15×15 est limité à 80 nœuds ; 18×18 et 20×20 à 30 nœuds. Ces préfixes ne sont
pas des temps de résolution. Une série séparée utilise d'autres graines avec
une limite de nœuds commune, afin d'examiner la sensibilité à l'ordre de recherche.

Les révisions natives ne comptent pas les opérations expérimentales. Le compteur
`pair_checks` compte les paires visitées par le nouveau filtre. `exact_removals`
compte les candidats rejetés par celui-ci, y compris lors d'un appel qui échoue ;
`removed_values` compte seulement les réductions effectivement appliquées.
Ces nombres comptent des occurrences dans les branches, et non des valeurs
uniques du problème. Le temps interne `seconds` exclut les contrôles de
sélection du filtre mais inclut préparation, filtrage, compteurs et réductions.

## Résultats principaux : trois répétitions

Temps médians en secondes. La variation compare `exact` à `tiny`, le prototype
avec bornes ; `baseline` désigne le solveur natif sans couplage expérimental.

| Carré | Natif | Bornes `tiny` | Exact | Variation | Nœuds bornes → exact |
|---|---:|---:|---:|---:|---:|
| 6×6 | 0.056966 | 0.056301 | 0.049533 | -12.0 % | 80 → 68 |
| 8×8 | 0.130339 | 0.125531 | 0.125612 | +0.1 % | 130 → 115 |
| 9×9 | 2.250574 | 2.156573 | 2.035361 | -5.6 % | 2535 → 2268 |
| 10×10 | 0.274972 | 0.256615 | 0.248194 | -3.3 % | 213 → 193 |
| 11×11 | 0.471834 | 0.488860 | 0.454708 | -7.0 % | 232 → 206 |
| 12×12 | 0.605765 | 0.574196 | 0.525955 | -8.4 % | 176 → 149 |
| 13×13 | 2.346606 | 0.922902 | 0.824180 | -10.7 % | 343 → 228 |
| 14×14 | 1.235398 | 1.193303 | 1.173979 | -1.6 % | 209 → 207 |
| 16×16 | 6.872600 | 6.559401 | 5.447669 | -16.9 % | 2204 → 1688 |

Tous ces essais retournent un carré valide. Les recherches se répètent exactement
pour chaque réglage, mais le filtre exact change la recherche par rapport aux
bornes. Cette comparaison ne mesure donc pas seulement le coût du propagateur.

Sur ces réglages, le gain est le plus net sur 16×16 (−16,9 % de temps, −23,4 %
de nœuds). 13×13 gagne 10,7 % de temps et 33,5 % de nœuds par rapport au couplage
par bornes. En revanche, les 15 nœuds évités sur 8×8 ne produisent aucun gain
de temps mesurable dans cette série. Les effets de quelques pour cent doivent
être interprétés avec prudence : trois répétitions ne caractérisent pas toute
la variabilité de la machine.

### Préfixes bornés

| Carré | Limite de nœuds | Bornes | Exact |
|---|---:|---:|---:|
| 15×15 | 80 | 0.574299 | 0.571911 |
| 18×18 | 30 | 0.656047 | 0.671918 |
| 20×20 | 30 | 1.001319 | 0.995254 |

Aucune solution n’est retournée pour ces préfixes. Le filtre ne réduit pas
le nombre de nœuds explorés avant la limite ; ces temps ne permettent pas
de conclure sur la résolution complète.

## Sensibilité à deux autres graines

Les graines 2 et 3 changent les ordres aléatoires des réglages 11×11, 12×12,
13×13 et 16×16. Chaque couple est répété trois fois, avec un plafond de
1 000 nœuds et 30 secondes. « Préfixe » signifie que les deux variantes
atteignent le plafond sans solution ; aucune comparaison de temps de résolution
complète ne peut alors être faite.

| Graine | Carré | Bornes, s | Exact, s | Nœuds bornes → exact | Résultat |
|---:|---|---:|---:|---:|---|
| 2 | 11×11 | 0.379713 | 0.357613 | 156 → 140 | Solution |
| 2 | 12×12 | 2.155502 | 2.218131 | 1000 → 1000 | Préfixe |
| 2 | 13×13 | 0.794649 | 0.727428 | 226 → 170 | Solution |
| 2 | 16×16 | 4.234828 | 4.351623 | 1000 → 1000 | Préfixe |
| 3 | 11×11 | 1.400703 | 1.499090 | 1000 → 1000 | Préfixe |
| 3 | 12×12 | 0.642513 | 0.623189 | 253 → 238 | Solution |
| 3 | 13×13 | 2.600697 | 2.578293 | 1000 → 1000 | Préfixe |
| 3 | 16×16 | 4.599399 | 4.605448 | 1000 → 1000 | Préfixe |

Les trois couples qui terminent dans cette série ont moins de nœuds et des
temps plus courts avec le filtre exact. Les cinq autres restent non résolus
au plafond ; plusieurs préfixes ralentissent, notamment 11×11 avec la graine 3
(+7,0 %). Le gain de 16×16 avec le réglage sauvegardé ne doit donc pas être
extrapolé à tous les ordres de recherche.

## Validation et décision

**61 tests du couplage passent**, dont 17 nouveaux tests pour le filtre exact.
La suite combinée des expériences SUM contient **98 tests réussis**.

- 5 000 cas comparent les masques exacts à une énumération indépendante, avec
  termes fixés, valeurs exclues, alphabets permutés, nombres négatifs, translations
  et grandes étendues de `10**40`.
- 150 modèles sont entièrement énumérés sous MRV et `dom_wdeg` : l’ensemble
  des solutions est comparé à une énumération exhaustive indépendante. Les
  modèles comprennent des sommes locales sous ALLDIFF global, des égalités
  linéaires unitaires et, dans la moitié des cas, une seconde somme chevauchante.
- Les tests couvrent la limite de 64 paires, le repli au-delà de 24 candidats,
  la restauration entre branches, les exclusions de portée et de type de somme,
  les délais et les huit carrés magiques normaux 3×3.
- Les tests existants vérifient que les réglages sans `exact_three=True`
  conservent les réductions, restaurations et recherches du prototype archivé.

Les 18 essais préliminaires, 108 comparaisons principales et 48 essais à graines
supplémentaires forment **174 exécutions** : **117 carrés validés indépendamment**,
57 préfixes et aucun dépassement de temps. Les signatures des recherches, les
compteurs hors temps, les médianes et les empreintes des sources ont été vérifiés.
L’essai préliminaire vérifie aussi l’équivalence de `tiny` avec son code archivé
avant l’ajout de l’option exacte. Ruff et les liens Markdown passent.

**Décision : conserver ce filtre comme option expérimentale.** Le gain est plus
convaincant que les dernières seules optimisations du coût : les recherches
complètes mesurées utilisent moins de nœuds, et plusieurs temps baissent
nettement. Les préfixes difficiles n’établissent aucun gain de résolution
complète. Aucun fichier sous `src/snarky` et aucun paramètre de recherche
sauvegardé n’est modifié. Les autres pistes — fusion de la règle à deux variables
dans SUM, optimisation d’ALLDIFF — ne sont pas incluses dans cette expérience.

## Données et reproduction

- [Résumé complet](summary.json), [validation](validation.json),
  [paramètres sauvegardés](presets.json)
- [Comparaison principale : 108 exécutions](comparison/runs.jsonl),
  [médianes](comparison/summary.json), [sources et ordre](comparison/frozen.json)
- [Graine 2](seed2/runs.jsonl), [médianes](seed2/summary.json),
  [graine 3](seed3/runs.jsonl), [médianes](seed3/summary.json)
- [18 essais préliminaires](pilot/runs.jsonl),
  [contrôle du prototype précédent](pilot/equivalence.json)
- [Source figée](sum_distinct.py.txt),
  [collecteur figé](magic_sum_distinct_benchmark.py.txt),
  [nouveaux tests figés](test_sum_distinct_exact.py.txt)
- [Code actuel](../../../experiments/neural_attention/sum_distinct.py),
  [tests actuels](../../../experiments/neural_attention/test_sum_distinct_exact.py)

Les sous-répertoires conservent les sources exactes utilisées et les paramètres
figés avant chaque série. Depuis la racine du dépôt, choisir de nouveaux
répertoires de sortie :

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_sum_distinct_benchmark \
  --presets benchmarks/history/magic_sum_distinct_exact_2026-10-13/presets.json \
  --sizes 6 8 9 10 11 12 13 14 15 16 18 20 \
  --variants baseline tiny exact --repeats 3 --limit 30 \
  --output generated/neural_attention/sum_distinct_exact_NEW

# Répéter avec --seed 3 pour la deuxième graine supplémentaire.
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_sum_distinct_benchmark \
  --presets benchmarks/history/magic_sum_distinct_exact_2026-10-13/presets.json \
  --sizes 11 12 13 16 --variants tiny exact --seed 2 \
  --max-nodes 1000 --repeats 3 --limit 30 \
  --output generated/neural_attention/sum_distinct_exact_seed2_NEW

.venv/bin/pytest experiments/neural_attention/test_sum_distinct.py \
  experiments/neural_attention/test_sum_distinct_optimization.py \
  experiments/neural_attention/test_sum_distinct_exact.py
```

La [suite sur les index compilés, le plafond de paires et le matching](../magic_sum_lookup_matching_2026-10-13/README.md)
mesure trois raffinements supplémentaires. Elle ajoute une petite optimisation
native d'ALLDIFF ; le filtrage conjoint SUM + ALLDIFF reste optionnel.
