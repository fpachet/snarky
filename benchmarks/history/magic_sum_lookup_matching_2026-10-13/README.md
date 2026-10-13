# Réutilisation des index numériques, budget de paires et matching ALLDIFF

Expérience du **13 octobre 2026**, après le
[premier filtrage exact à trois variables](../magic_sum_distinct_exact_2026-10-13/README.md).

**Les trois modifications sont implémentées et testées.** Le chemin rapide du
matching évite du travail et conserve exactement les recherches. Les gains
supplémentaires sur le temps total sont petits et mixtes ; les index et le
plafond élargi restent des options expérimentales.

## Trois modifications séparées

### Supports exacts avec index compilés

Le filtre exact utilise désormais les dictionnaires immuables `positions`
présents dans les colonnes numériques de SUM. Il exclut les valeurs fixées par
appartenance à un ensemble dans les deux petits domaines et par consultation
de l’index du troisième terme, choisit les deux plus petits domaines courants, puis
énumère leurs paires. La valeur requise du troisième terme est recherchée dans
son index et testée dans son **masque courant**. Le troisième domaine n'est ni
parcouru ni converti en dictionnaire temporaire.

Les masques de supports et les compteurs de déductions restent identiques au
premier filtre exact, y compris dans les révisions qui échouent. Le nombre réel
de paires vérifiées peut changer : exclure les valeurs fixées peut changer
l’ordre des tailles, alors que le nouveau filtre choisit les deux domaines
avant cette exclusion pour éviter de parcourir le troisième. Les index décrivent
seulement les alphabets immuables : aucun cache de témoins ou état logique
supplémentaire n'est ajouté. Les masques courants sont relus après chaque
restauration.

### Sélection par coût réel des paires

L'option `pairs` remplace le plafond de 24 candidats au total par un plafond de
**64 paires**, calculé comme le produit des tailles des deux plus petits domaines
actifs après la propagation native de SUM. Les exclusions ultérieures des
valeurs fixées ne peuvent qu'abaisser ce nombre.

Le plafond peut donc accepter des domaines déséquilibrés qui étaient exclus par
la somme de leurs tailles. Les alphabets plus larges du troisième terme ne
nécessitent aucun parcours supplémentaire dans le filtre. Le réglage `exact`
conserve l'ancien plafond total, pour isoler le seul changement de coût. La
règle rapide à deux variables conserve sa priorité.

Le filtrage reste limité à trois termes actifs, dans une égalité SUM ou
LINEAR_SUM à coefficients +1 couverte entièrement par un ALLDIFF inconditionnel.
L'exactitude concerne cette somme et la distinction de ses propres termes ;
elle ne garantit pas un support dans le modèle complet.

### Matching ALLDIFF déjà complet

Après validation de **chaque arête** de son matching existant, ALLDIFF retourne
immédiatement de la fonction de réparation si toutes les variables restent
appariées. Cela évite de reconstruire l'ensemble des valeurs occupées et de
trier toutes les variables lorsque ces opérations ne servent à rien.

Cette sortie ne quitte **que la réparation du matching**. La construction du
graphe et le filtrage par composantes continuent lorsque les domaines changent,
même si le matching reste valide. Si une arête disparaît, le chemin existant de
réparation est conservé. Les restaurations entre branches restent validées.

Cette petite modification est active dans le solveur natif. Les deux variantes
du filtre SUM + ALLDIFF restent optionnelles dans le prototype expérimental ;
aucun paramètre sauvegardé de recherche n'est changé.

## Protocole des comparaisons

Les séries sont séquentielles et mélangées de façon déterministe. Le temps
comprend modèle, état, détection et recherche ; imports et validation sont exclus.
Les comparaisons du filtre utilisent toutes le nouveau matching natif, afin
d'isoler le changement de filtre. La comparaison du matching utilise le modèle
natif sans couplage et échange uniquement `AllDifferentPlan._match`.

`before_exact` charge le premier filtre exact depuis son archive ; `exact`
utilise le nouvel index avec le même plafond total de 24 candidats. Ces deux
réglages doivent conserver exactement recherche, carrés et compteurs de déductions hors temps. Le compteur de travail
`pair_checks` est comparé séparément ; il peut différer sans changer les supports.
`pairs` utilise les nouveaux index et le plafond de 64 paires ; il peut changer
la recherche. Les révisions natives ne comptent pas les opérations internes du
prototype. Le temps interne de filtrage exclut le déclenchement par plafond de
paires ; les temps totaux l'incluent.

Les tailles 15×15, 18×18 et 20×20 utilisent respectivement des limites de 80,
30 et 30 nœuds. Ce sont des préfixes, pas des temps de résolution complète.

## Matching natif : même recherche, trois répétitions

| Carré | Avant, s | Après, s | Variation | Portée |
|---|---:|---:|---:|---|
| 6×6 | 0.056502 | 0.056363 | -0.2 % | Solution |
| 8×8 | 0.127436 | 0.124474 | -2.3 % | Solution |
| 9×9 | 2.289458 | 2.251713 | -1.6 % | Solution |
| 10×10 | 0.281745 | 0.274602 | -2.5 % | Solution |
| 11×11 | 0.469550 | 0.475217 | +1.2 % | Solution |
| 12×12 | 0.567969 | 0.573526 | +1.0 % | Solution |
| 13×13 | 2.379707 | 2.339786 | -1.7 % | Solution |
| 14×14 | 1.220798 | 1.214539 | -0.5 % | Solution |
| 15×15 | 0.589667 | 0.575724 | -2.4 % | Préfixe |
| 16×16 | 7.003672 | 6.957483 | -0.7 % | Solution |
| 18×18 | 0.640183 | 0.637489 | -0.4 % | Préfixe |
| 20×20 | 0.988239 | 0.987269 | -0.1 % | Préfixe |

Les 72 exécutions conservent exactement les nœuds, échecs, révisions,
terminaisons et carrés. Les effets globaux restent petits et mixtes : les
gains souvent proches de 1–2 % ne prouvent pas une accélération uniforme avec
seulement trois répétitions. 11×11 et 12×12 ont de petites régressions mesurées.

## Index et plafond de paires : trois répétitions

Toutes ces variantes utilisent le matching natif optimisé. « Ancien exact »
désigne le premier filtre à trois variables, **pas le solveur natif sans
couplage**. « Index » garde ses limites de sélection ; « Paires » élargit
la sélection à 64 paires.

| Carré | Ancien exact, s | Index, s | Paires, s | Nœuds index → paires |
|---|---:|---:|---:|---:|
| 6×6 | 0.049324 | 0.050126 | 0.048542 | 68 → 68 |
| 8×8 | 0.121472 | 0.120882 | 0.126085 | 115 → 115 |
| 9×9 | 1.918703 | 1.936118 | 1.936340 | 2268 → 2243 |
| 10×10 | 0.242902 | 0.244213 | 0.249562 | 193 → 193 |
| 11×11 | 0.453708 | 0.454954 | 0.450302 | 206 → 197 |
| 12×12 | 0.529626 | 0.523931 | 0.525545 | 149 → 149 |
| 13×13 | 0.813713 | 0.813868 | 0.813409 | 228 → 228 |
| 14×14 | 1.192274 | 1.178920 | 1.171750 | 207 → 207 |
| 16×16 | 5.483894 | 5.489416 | 5.473298 | 1688 → 1658 |

Les index conservent exactement la recherche de l’ancien filtre. Leur effet
sur le temps total est essentiellement neutre. Le plafond de paires réduit
les nœuds de 9×9 (2 268 → 2 243), 11×11 (206 → 197) et 16×16
(1 688 → 1 658), mais ne donne pas un gain de temps cohérent. Sur 8×8,
les deux variantes explorent 115 nœuds et le plafond élargi est plus lent.

### Coût interne et premier essai

Le premier essai excluait les valeurs fixées par index dans **les trois**
domaines actifs, puis choisissait les deux plus petits domaines filtrés. Il
conservait aussi exactement le nombre de paires de l’ancien filtre, mais
ajoutait trop de travail sur les petits domaines. Ses 12 essais préliminaires
et 108 comparaisons sont conservés séparément.

La version finale filtre directement les deux petits domaines et consulte
l’index du troisième. Elle réduit ce surcoût, sans produire de gain interne
uniforme par rapport à l’ancien filtre. Médianes internes, en millisecondes,
dans la comparaison finale :

| Carré | Ancien exact | Index | Paires |
|---|---:|---:|---:|
| 9×9 | 120.466 | 123.650 | 140.677 |
| 13×13 | 5.663 | 5.989 | 6.313 |
| 16×16 | 92.796 | 99.271 | 100.678 |

Le coût de consultation du masque courant et du filtrage supplémentaire peut
compenser l’économie de préparation. Le compteur interne exclut le contrôle
du plafond de paires ; les temps globaux l’incluent. La version par index reste
un mécanisme expérimental, sans affirmation de gain de vitesse général.

### Préfixes de la comparaison finale

| Carré | Nœuds | Ancien exact, s | Index, s | Paires, s |
|---|---:|---:|---:|---:|
| 15×15 | 80 | 0.573114 | 0.582876 | 0.574449 |
| 18×18 | 30 | 0.637089 | 0.656462 | 0.665476 |
| 20×20 | 30 | 1.004696 | 1.003963 | 0.999542 |

Aucune solution n’est retournée dans ces préfixes. Les petites variations de
temps ne permettent pas de conclure sur la résolution complète.

## Deux graines supplémentaires

Les graines 2 et 3 changent les ordres aléatoires des réglages 11×11, 12×12,
13×13 et 16×16. Chaque couple est répété trois fois avec un plafond commun
de 1 000 nœuds et 30 secondes.

| Graine | Carré | Index, s | Paires, s | Nœuds | Résultat |
|---:|---|---:|---:|---:|---|
| 2 | 11×11 | 0.368452 | 0.358864 | 140 | Solution |
| 2 | 12×12 | 2.222555 | 2.226275 | 1000 | Préfixe |
| 2 | 13×13 | 0.745868 | 0.743180 | 170 | Solution |
| 2 | 16×16 | 4.409578 | 4.381735 | 1000 | Préfixe |
| 3 | 11×11 | 1.548597 | 1.518438 | 1000 | Préfixe |
| 3 | 12×12 | 0.625778 | 0.629232 | 238 | Solution |
| 3 | 13×13 | 2.604661 | 2.575699 | 1000 | Préfixe |
| 3 | 16×16 | 4.653723 | 4.545518 | 1000 | Préfixe |

Les nœuds ne diminuent dans aucun de ces huit couples. Trois couples sont
résolus par les deux variantes ; les cinq autres restent limités aux préfixes.
Cette série ne justifie donc pas une adoption automatique du plafond élargi.

## Maintenance du matching seule : sept répétitions

Un microbenchmark séparé appelle uniquement `AllDifferentPlan._match` avec un
matching complet et valide. Deux masques alternent en supprimant des arêtes
non appariées ; toutes les arêtes appariées survivent. Chaque essai effectue
1 000 appels, sur sept répétitions mélangées. Médianes par appel :

| Variables | Avant, µs | Après, µs | Accélération du composant |
|---:|---:|---:|---:|
| 64 | 11.554 | 4.256 | 2.71× |
| 256 | 46.690 | 17.193 | 2.72× |
| 400 | 80.150 | 28.471 | 2.82× |

Ces 42 essais mesurent seulement le cas où le matching reste complet. Ils
n’incluent ni construction du graphe, ni composantes, ni domaines, ni recherche.
L’accélération de ce composant ne doit pas être présentée comme une accélération
d’ALLDIFF complet ou du solveur. Une première série équivalente de 42 essais
est également archivée.

## Validation et décision

- Le cœur passe **1 221 tests non lents**, avec 4 skips et 58 tests désélectionnés.
  La série lente passe **56 tests**, avec 3 skips et 1 224 tests désélectionnés.
  Les logs sont conservés ; certains skips de collecte peuvent apparaître dans
  les deux commandes.
- **111 tests des expériences SUM passent**, dont 74 tests du couplage. Les
  13 nouveaux tests vérifient notamment 5 000 masques et compteurs de déductions
  contre le filtre exact précédent et une énumération exhaustive indépendante.
- 96 comparaisons de traces complètes vérifient décisions, réductions,
  restaurations, solutions et compteurs de déductions pour le nouvel index.
  Le compteur de travail `pair_checks` peut différer et son plafond est vérifié
  séparément. Les tests précédents des modes sans filtrage exact continuent
  d’exiger tous leurs compteurs entiers identiques.
- 150 petits modèles sont entièrement énumérés sous MRV et `dom_wdeg` avec
  le plafond élargi. Les solutions sont vérifiées indépendamment, y compris
  avec des sommes chevauchantes. Les limites, grands entiers, exclusions de
  valeurs fixées, restauration et huit carrés magiques 3×3 sont également testés.
- Deux nouveaux tests du cœur vérifient un Hall set malgré un matching retenu
  complet, et la réparation après une branche en échec et un élargissement.

Les séries de résolution totalisent **348 exécutions**, avec **246 carrés
indépendamment validés**, 102 préfixes et aucun dépassement de temps. Elles
incluent le premier essai de coût abandonné. Les 84 essais de maintenance
du matching sont comptés séparément. Les signatures, médianes, déductions,
limites et empreintes des sources ont été vérifiées. Ruff, mypy et les liens
Markdown passent.

**Décision : conserver le petit chemin rapide natif et laisser les deux
raffinements SUM + ALLDIFF optionnels.** Le chemin natif évite du travail en
conservant exactement les recherches. Les nouveaux index et le plafond élargi
ne montrent pas de gain global régulier par rapport au premier filtre exact.
Ils ne justifient pas une activation automatique dans le solveur. Les gains
mesurés dans l’expérience précédente du filtrage exact restent une comparaison
distincte de ces derniers raffinements.

## Données et reproduction

- [Résumé complet](summary.json), [validation](validation.json),
  [paramètres](presets.json)
- [Comparaison finale : 108 exécutions](comparison/runs.jsonl),
  [médianes](comparison/summary.json), [sources](comparison/frozen.json),
  [équivalence des recherches et déductions](comparison/equivalence.json)
- [Matching natif : 72 exécutions](matching/runs.jsonl),
  [médianes](matching/summary.json), [sources](matching/frozen.json)
- [Graine 2](seed2/runs.jsonl), [médianes](seed2/summary.json),
  [graine 3](seed3/runs.jsonl), [médianes](seed3/summary.json)
- [Premier essai : 12 exécutions](pilot_all_positions/runs.jsonl),
  [108 comparaisons initiales](initial_all_positions/runs.jsonl),
  [source initiale](initial_all_positions/sum_distinct.py.txt)
- [Microbenchmark du matching](matching_micro.json),
  [collecteur](matching_micro.py.txt), [première série](matching_micro_first.json),
  [collecteur initial](matching_micro_first.py.txt)
- [Cœur avant](alldifferent_before.py.txt), [cœur après](alldifferent.py.txt),
  [prototype figé](sum_distinct.py.txt), [nouveaux tests](test_sum_distinct_lookup.py.txt)
- [Logs du cœur non lent](core_non_slow.log.txt), [logs des tests lents](core_slow.log.txt)
- [Code actuel du prototype](../../../experiments/neural_attention/sum_distinct.py),
  [code actuel d’ALLDIFF](../../../src/snarky/finite/alldifferent.py)

Depuis la racine du dépôt, avec des répertoires de sortie neufs :

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_sum_distinct_benchmark \
  --before benchmarks/history/magic_sum_lookup_matching_2026-10-13/comparison/before_snapshot.py.txt \
  --presets benchmarks/history/magic_sum_lookup_matching_2026-10-13/presets.json \
  --sizes 6 8 9 10 11 12 13 14 15 16 18 20 \
  --variants before_exact exact pairs --repeats 3 --limit 30 \
  --output generated/neural_attention/sum_lookup_NEW

PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_alldifferent_benchmark \
  --before benchmarks/history/magic_sum_lookup_matching_2026-10-13/alldifferent_before.py.txt \
  --presets benchmarks/history/magic_sum_lookup_matching_2026-10-13/presets.json \
  --kernel matching --sizes 6 8 9 10 11 12 13 14 15 16 18 20 --repeats 3 \
  --output generated/neural_attention/matching_NEW

# Répéter avec --seed 3 pour la seconde graine supplémentaire.
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_sum_distinct_benchmark \
  --presets benchmarks/history/magic_sum_lookup_matching_2026-10-13/presets.json \
  --sizes 11 12 13 16 --variants exact pairs --seed 2 \
  --max-nodes 1000 --repeats 3 --limit 30 \
  --output generated/neural_attention/sum_lookup_seed2_NEW

PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  benchmarks/history/magic_sum_lookup_matching_2026-10-13/matching_micro.py.txt \
  --output generated/neural_attention/matching_micro_NEW.json

.venv/bin/python scripts/check_redesign.py -m "not slow"
.venv/bin/python scripts/check_redesign.py -m slow
.venv/bin/pytest experiments/neural_attention/test_sum_distinct.py \
  experiments/neural_attention/test_sum_distinct_optimization.py \
  experiments/neural_attention/test_sum_distinct_exact.py \
  experiments/neural_attention/test_sum_distinct_lookup.py
```
