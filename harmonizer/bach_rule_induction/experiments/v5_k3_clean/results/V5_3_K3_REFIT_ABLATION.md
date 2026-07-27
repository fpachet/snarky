# V5.3 — ablation réajustée des règles K3

## Protocole

- Les douze règles V5.1 sont réajustées conjointement depuis zéro.
- Chaque règle est d'abord neutralisée à poids fixe.
- Elle est ensuite retirée et les onze autres poids sont réappris.
- Une pénalité NLL positive indique une contribution utile.
- Le test de 51 chorals reste fermé.

## Modèle complet réajusté

- NLL train : `1.454559`.
- NLL validation : `1.449123`.

## Résultats

| # | Règle numérique | Poids | Neutralisation validation | Retrait + réajustement validation |
|---:|---|---:|---:|---:|
| 1 | `any_voice_adjacent_step_gt(all_voices)=2` | -1.654188 | +0.306096 | +0.269848 |
| 2 | `any_pair_central_abs_class(all_voices)=1` | -1.699181 | +0.135089 | +0.123638 |
| 3 | `any_pair_central_abs_class(all_voices)=11` | -1.864991 | +0.160034 | +0.153510 |
| 4 | `any_pair_central_abs_class(all_voices)=2` | -1.427930 | +0.103623 | +0.100364 |
| 5 | `any_pair_central_abs_class(all_voices)=10` | -1.276725 | +0.072766 | +0.075309 |
| 6 | `any_adjacent_central_ordered_gap_le(all_voices)=1` | -1.426639 | +0.069122 | +0.050200 |
| 7 | `any_voice_adjacent_step_gt(all_voices)=7` | -1.301362 | +0.036436 | +0.029167 |
| 8 | `any_pair_central_abs_class(all_voices)=7` | +0.725760 | +0.046675 | +0.042563 |
| 9 | `any_pair_abs_class_preserved_same_sign(all_voices)=0` | -2.091950 | +0.030281 | +0.031190 |
| 10 | `any_pair_abs_class_preserved_same_sign(all_voices)=7` | -2.069681 | +0.035134 | +0.034538 |
| 11 | `previous_ordered_gap_le(v0,v1)=2` | +1.285055 | +0.011101 | +0.012102 |
| 12 | `any_voice_adjacent_abs_class(all_voices)=1` | +0.565046 | +0.025514 | +0.017702 |

## Lecture

`12` règles sur `12` conservent une pénalité positive après réajustement.

Cette expérience mesure la redondance interne du catalogue fixé. Elle
ne remplace pas la calibration du processus de recherche sur plusieurs
permutations.
