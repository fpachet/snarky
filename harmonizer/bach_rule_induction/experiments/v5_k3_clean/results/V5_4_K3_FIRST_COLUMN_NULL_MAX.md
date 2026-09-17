# V5.4 — calibration du maximum familial K3

## Protocole

- `49` permutations des choix au sein de chaque pièce et voix.
- `791` prédicats scannés, dont `777` testables après filtrage.
- Maximum absolu calculé sur tous les prédicats testables.
- Distribution de registre réestimée sur le train authentique.
- Cette calibration porte sur la première étape de génération de colonne.
- Le test de 51 chorals reste fermé.

## Maximum nul

- médiane : `56.450` ;
- percentile 90 : `57.804` ;
- percentile 95 : `58.091` ;
- maximum observé : `58.465`.

## Première règle authentique

- clause : `any_voice_adjacent_step_gt(all_voices)=2` ;
- z authentique : `-284.796` ;
- p familial empirique : `0.020` ;
- dépasse les 49 maxima nuls : `true`.
- `0,020 = 1/50` est la résolution minimale avec 49 permutations : aucun maximum nul n'atteint le signal authentique.

## Principaux signaux authentiques avant réajustement

| Rang | Prédicat | z | p familial |
|---:|---|---:|---:|
| 1 | `any_voice_adjacent_step_gt(all_voices)=2` | -284.796 | 0.020 |
| 2 | `any_voice_adjacent_abs_class(all_voices)=2` | +183.002 | 0.020 |
| 3 | `any_voice_adjacent_step_gt(all_voices)=4` | -166.620 | 0.020 |
| 4 | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -156.916 | 0.020 |
| 5 | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | +136.199 | 0.020 |
| 6 | `any_adjacent_central_ordered_gap_le(all_voices)=1` | -131.246 | 0.020 |
| 7 | `any_voice_adjacent_abs_class(all_voices)=1` | +123.086 | 0.020 |
| 8 | `any_pair_central_abs_class(all_voices)=1` | -122.828 | 0.020 |
| 9 | `abs_step_from_previous_gt(v0)=2` | -120.225 | 0.020 |
| 10 | `abs_step_from_previous_gt(v1)=2` | -115.229 | 0.020 |
| 11 | `abs_step_from_previous_gt(v2)=2` | -113.762 | 0.020 |
| 12 | `any_voice_adjacent_step_gt(all_voices)=1` | -111.492 | 0.020 |

## Portée

Le p familial protège la sélection de la première colonne contre les
791 essais numériques du catalogue, dont
777 sont testables. Il ne valide pas
automatiquement les onze colonnes suivantes, qui sont recherchées sur
des résidus successivement réajustés. Leur calibration complète exigera
de répéter toute la génération de colonnes sous chaque permutation.
