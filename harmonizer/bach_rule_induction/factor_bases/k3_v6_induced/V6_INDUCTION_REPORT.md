# V6 — induction d'une base factorielle depuis zéro

## Garanties

- Grammaire gelée avant cette exécution.
- Aucune règle historique, CHORAL ou contrainte experte chargée.
- Structure et poids appris sur `train`.
- Validation utilisée uniquement pour le réajustement et l'arrêt.
- Chaque sélection dépasse le maximum absolu de sa famille sous
  permutation des choix à l'intérieur de chaque pièce et voix.
- Test de 51 chorals non chargé.

## Résultat

- Catalogue engendré : `954` facteurs candidats.
- Facteurs retenus : `30`.
- NLL validation baseline : `2.422315`.
- NLL validation finale : `1.048935`.
- Gain : `1.373380`.

| # | Famille | Prédicat numérique | Poids | z | max |z| nul |
|---:|---|---|---:|---:|---:|
| 1 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=2` | -1.262611 | -282.435 | 39.584 |
| 2 | `observed_vertical_set` | `central_bass_pcset(all_voices)=145` | +1.670369 | +195.567 | 7.455 |
| 3 | `observed_vertical_set` | `central_bass_pcset(all_voices)=137` | +1.314629 | +111.001 | 7.247 |
| 4 | `observed_vertical_set` | `central_bass_pcset(all_voices)=265` | +0.999026 | +108.762 | 7.256 |
| 5 | `universal_melodic_interval_class` | `any_voice_adjacent_abs_class(all_voices)=1` | +1.347572 | +104.096 | 15.099 |
| 6 | `universal_melodic_interval_class` | `any_voice_adjacent_abs_class(all_voices)=2` | +0.826808 | +79.485 | 15.702 |
| 7 | `ordered_voice_gap` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -1.011708 | -68.736 | 18.903 |
| 8 | `observed_vertical_set` | `central_bass_pcset(all_voices)=329` | +1.854828 | +60.887 | 7.135 |
| 9 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=11` | -1.615866 | -56.367 | 9.775 |
| 10 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=7` | -1.953714 | -54.828 | 5.611 |
| 11 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=10` | -1.353030 | -52.664 | 9.244 |
| 12 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=0` | -2.027701 | -55.750 | 4.848 |
| 13 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=1` | -1.442818 | -49.020 | 8.146 |
| 14 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=7` | -1.170406 | -47.803 | 24.051 |
| 15 | `universal_pair_motion` | `any_pair_arrival_abs_class_same_sign(all_voices)=2` | -1.197657 | -46.670 | 3.822 |
| 16 | `vertical_cardinality` | `central_distinct_pc_count(all_voices)=2` | -1.425733 | -45.237 | 2.460 |
| 17 | `vertical_cardinality_metric_conjunction` | `central_distinct_pc_count_metric(all_voices)=3,0` | -1.164938 | -43.996 | 0.907 |
| 18 | `ordered_voice_gap` | `previous_ordered_gap_le(v0,v1)=2` | +1.272421 | +41.714 | 8.881 |
| 19 | `attacked_repetition` | `attacked_repeat_from_previous(v3)` | -1.542158 | -41.235 | 5.363 |
| 20 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=2` | -0.921881 | -37.714 | 7.368 |
| 21 | `observed_vertical_set` | `central_bass_pcset(all_voices)=141` | +2.221952 | +42.927 | 7.550 |
| 22 | `observed_vertical_set` | `central_bass_pcset(all_voices)=161` | +1.297473 | +39.206 | 7.532 |
| 23 | `three_block_direction_shape` | `three_block_sign_shape(v1)=0,-1` | +1.695959 | +32.358 | 8.030 |
| 24 | `observed_vertical_set` | `central_bass_pcset(all_voices)=649` | +1.652610 | +30.958 | 7.544 |
| 25 | `three_block_direction_shape` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | +0.992565 | +30.128 | 7.980 |
| 26 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.856041 | +30.524 | 3.698 |
| 27 | `observed_vertical_set` | `central_bass_pcset(all_voices)=1041` | +1.931191 | +27.604 | 7.551 |
| 28 | `observed_vertical_set` | `central_bass_pcset(all_voices)=1169` | +1.446748 | +29.458 | 7.551 |
| 29 | `observed_vertical_set` | `central_tonic_pcset(all_voices)=2180` | +1.273322 | +28.876 | 7.553 |
| 30 | `observed_vertical_set` | `central_bass_pcset(all_voices)=545` | -1.485772 | -30.217 | 7.622 |

Les noms musicologiques et la comparaison aux traités sont différés
jusqu'après gel de cette liste.
