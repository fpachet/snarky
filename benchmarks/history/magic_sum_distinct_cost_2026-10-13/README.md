# Optimisation du coût de SUM + ALLDIFF

Expérience du **13 octobre 2026**, à la suite du
[premier couplage sélectif](../magic_sum_distinct_2026-10-13/README.md).

**Deux optimisations sont conservées dans le prototype : déclenchement arrêté
plus tôt et traitement spécialisé à trois variables.** Les réductions, les
contradictions et les recherches restent identiques. Le temps interne du filtrage
baisse, mais le gain sur le temps total reste faible et non uniforme. Le solveur
de production n'est pas modifié.

## Changements

### Déclenchement

Le prototype cesse de construire la liste des variables actives dès que les
seuils excluent le filtrage : quatrième variable pour `tiny`, troisième pour
`fast_pair`, ou dépassement des 24 candidats après l'apparition d'une troisième
variable. Il évite aussi une seconde liste contenant les tailles de domaines.

La priorité historique de la règle à deux variables est conservée : elle reste
applicable quelle que soit la taille des deux domaines, même si une limite plus
stricte a été fournie. Tous les supports SUM sont appliqués avant ce contrôle ;
l'arrêt anticipé ne saute donc aucune réduction native.

### Trois variables

Des bitsets temporaires représentent les valeurs de chaque domaine actif.
Les unions se calculent par OR, sans Counter ni tri de l'union complète. Trois
extrêmes inférieurs et supérieurs suffisent : après exclusion du candidat testé,
il faut seulement deux valeurs distinctes pour borner les deux autres variables.

Les index sont normalisés par une borne d'alphabet immuable, obtenue directement
des colonnes numériques déjà compilées. Une étendue supérieure à **4 096** utilise
l'ancien algorithme général. Cela évite les bitsets gigantesques pour des valeurs
très éloignées, tout en acceptant les translations de `10**40` lorsque l'étendue
reste petite.

Tout est recalculé depuis les masques courants. Aucun cache de témoins, de
supports, ni état logique supplémentaire à restaurer n'est ajouté. La règle
arithmétique à deux variables conserve son implémentation précédente.

Un premier essai avec de petites listes d'extrêmes conservait aussi le
comportement, mais n'apportait pas de gain convaincant sur 9×9. Il est archivé
séparément dans [pilot_lists](pilot_lists/runs.jsonl). La comparaison principale
ci-dessous utilise les bitsets.

## Comparaison principale : même recherche, coût différent

**Avant désigne le prototype avec couplage**, et non le solveur natif sans
couplage. Le code exact précédent est chargé depuis l'archive. Les paramètres
de recherche, les limites de filtrage et l'ordre des réductions sont conservés.

Les 144 exécutions comparent les deux réglages (`fast_pair` et `tiny`), avant et
après optimisation, sur 12 tailles et trois répétitions. Elles sont séquentielles
et mélangées de façon déterministe. Le temps comprend modèle, état, index et
recherche ; imports et validation indépendante sont exclus.

Temps médians de `tiny`, en secondes :

| Carré | Avant optimisation du coût | Après | Variation |
|---|---:|---:|---:|
| 6×6 | 0,058485 | 0,058179 | −0,5 % |
| 8×8 | 0,123707 | 0,136815 | +10,6 % |
| 9×9 | 2,139267 | 2,126691 | −0,6 % |
| 10×10 | 0,257753 | 0,251489 | −2,4 % |
| 11×11 | 0,496773 | 0,466504 | −6,1 % |
| 12×12 | 0,552707 | 0,546836 | −1,1 % |
| 13×13 | 0,943188 | 0,922533 | −2,2 % |
| 14×14 | 1,136882 | 1,182045 | +4,0 % |
| 16×16 | 6,433212 | 6,393306 | −0,6 % |

Ces petits effets globaux ne constituent pas une accélération uniforme. Les
résultats 8×8 et 14×14 ont motivé une vérification supplémentaire.

Pour `fast_pair`, qui bénéficie seulement du nouveau déclenchement, les effets
globaux sont également petits et mixtes. Par exemple, 16×16 passe de 6,810691 s
à 6,787643 s ; 9×9 passe de 2,238883 s à 2,264445 s. Les valeurs complètes sont
dans le [résumé principal](comparison/summary.json).

## Vérification supplémentaire : sept répétitions

Les trois tailles ci-dessous sont remesurées dans une nouvelle série de
42 exécutions, avec les mêmes sources et réglages. Les ralentissements marqués
de la première série ne se reproduisent pas avec la même amplitude.

| Carré | Avant, médiane | Après, médiane | Variation |
|---|---:|---:|---:|
| 8×8 | 0,131271 s | 0,132714 s | +1,1 % |
| 9×9 | 2,296216 s | 2,279554 s | −0,7 % |
| 14×14 | 1,237192 s | 1,214387 s | −1,8 % |

La variabilité est du même ordre que beaucoup des gains globaux recherchés.
Il serait prématuré de présenter cette modification comme une accélération
générale de quelques pour cent.

## Coût interne du filtrage

Le compteur interne chronomètre le filtrage, la préparation de ses paramètres,
ses compteurs et l'application de ses réductions. Il **exclut les contrôles de
déclenchement** ; le coût de ces derniers n'est donc pas isolé ici. Les temps
totaux précédents incluent, eux, tout le coût du prototype.

Médianes du compteur `seconds` dans la comparaison principale `tiny` :

| Carré | Avant | Après | Baisse |
|---|---:|---:|---:|
| 8×8 | 8,035 ms | 7,403 ms | 7,9 % |
| 9×9 | 168,992 ms | 151,027 ms | 10,6 % |
| 13×13 | 10,096 ms | 9,106 ms | 9,8 % |
| 16×16 | 162,822 ms | 150,649 ms | 7,5 % |

Dans la série de sept répétitions, 9×9 passe de 184,056 ms à 162,206 ms de
filtrage, soit une baisse d'environ 11,9 %. Cette baisse reste diluée dans le
temps total, dominé par les autres travaux du solveur.

## Recherches bornées

15×15 est limité aux 80 premiers nœuds ; 18×18 et 20×20 aux 30 premiers.
Ces lignes ne sont **pas des temps de résolution**, et aucun carré n'est retourné.
Les compteurs et réductions restent identiques avant/après.

| Carré | Nœuds | `tiny` avant | `tiny` après |
|---|---:|---:|---:|
| 15×15 | 80 | 0,568360 s | 0,573425 s |
| 18×18 | 30 | 0,631665 s | 0,642009 s |
| 20×20 | 30 | 1,000796 s | 0,999467 s |

## Validation et décision

**44 tests passent**, dont les 22 tests précédents du couplage et 22 nouveaux :

- 5 000 cas comparent exactement les masques retournés et tous les compteurs
  avec l'algorithme archivé, y compris lors des contradictions ;
- trois cas couvrent l'étendue limite 4 096, 4 097 et `10**40`, ainsi que le
  repli sur l'algorithme général ;
- 48 modèles, neuf configurations et deux heuristiques produisent 864
  comparaisons de traces complètes : décisions, réductions et restaurations des
  domaines, solutions, nœuds, échecs, révisions et compteurs hors chronométrage.

Les 144 exécutions principales, 42 confirmations et huit essais avec listes
forment **194 exécutions**, avec **158 carrés indépendamment validés**. Aucun
dépassement de temps ne se produit. Les comparaisons avant/après conservent
nœuds, échecs, révisions, terminaison, carrés retournés et tous les compteurs de
filtrage hors temps. La série principale vérifie 24 couples taille/réglage.

Ruff et les liens Markdown passent. Aucun fichier sous `src/snarky` ni aucun
paramètre sauvegardé de recherche n'a changé. Le runtime reste `edfe3c9` ; la
suite complète du cœur n'a pas été relancée pour ces fichiers expérimentaux.

**Décision : conserver les changements dans le prototype opt-in.** Le coût
interne baisse avec un comportement identique, mais les mesures ne justifient
pas une promesse de gain global uniforme ni une intégration immédiate dans le
solveur. L'ancienne version reste utilisable avec `--before`.

La fusion de la règle à deux variables dans le noyau SUM et une gestion
incrémentale réversible des variables actives n'ont pas été implémentées ici.
L'expérience mesure ensemble le déclenchement anticipé et la spécialisation à
trois variables ; elle ne sépare pas leurs contributions individuelles.

## Données et reproduction

- [Résumé](summary.json) et [validation](validation.json)
- [144 exécutions principales](comparison/runs.jsonl),
  [médianes](comparison/summary.json),
  [équivalence des recherches et du filtrage](comparison/equivalence.json),
  [sources et paramètres](comparison/frozen.json)
- [42 confirmations](confirmation/runs.jsonl) et
  [résumé](confirmation/summary.json)
- [Prototype optimisé figé](sum_distinct.py.txt),
  [collecteur](magic_sum_distinct_benchmark.py.txt),
  [tests d'équivalence](test_sum_distinct_optimization.py.txt)
- [Ancien prototype exact](comparison/before_snapshot.py.txt)
- [Code actuel](../../../experiments/neural_attention/sum_distinct.py)
  et [tests actuels](../../../experiments/neural_attention/test_sum_distinct_optimization.py)

Chaque répertoire contient les sources exactes utilisées. Les empreintes
SHA-256 et les paramètres sont enregistrés avant l'exécution.

Depuis la racine du dépôt, avec un nouveau répertoire de sortie :

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_sum_distinct_benchmark \
  --before benchmarks/history/magic_sum_distinct_cost_2026-10-13/comparison/before_snapshot.py.txt \
  --presets benchmarks/history/magic_sum_distinct_cost_2026-10-13/presets.json \
  --sizes 6 8 9 10 11 12 13 14 15 16 18 20 \
  --variants before_fast_pair fast_pair before_tiny tiny \
  --repeats 3 --limit 30 \
  --output generated/neural_attention/sum_distinct_cost_NEW

PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_sum_distinct_benchmark \
  --before benchmarks/history/magic_sum_distinct_cost_2026-10-13/comparison/before_snapshot.py.txt \
  --sizes 8 9 14 --variants before_tiny tiny --repeats 7 --limit 30 \
  --output generated/neural_attention/sum_distinct_cost_confirmation_NEW

.venv/bin/pytest experiments/neural_attention/test_sum_distinct.py \
  experiments/neural_attention/test_sum_distinct_optimization.py
```
