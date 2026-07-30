# V14 — réinduction exacte avec trajectoires dirigées et métriques

La structure est sélectionnée par les gradients résiduels des véritables
conditionnelles Gibbs. Registre, profil tonal et poids factoriels sont
réappris conjointement. Aucun facteur V6/V8 n'est imposé.

## Résultat

- Catalogue exact : `3676` facteurs.
- Facteurs sélectionnés : `30`.
- NLL validation structure : `0.750334`.
- NLL validation complète : `0.749295`.
- Test réservé chargé : `False`.

| # | Famille | Facteur | Poids | z de sélection |
|---:|---|---|---:|---:|
| 1 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=2` | -1.217715 | -92.97 |
| 2 | `observed_vertical_set` | `central_bass_pcset(all_voices)=145` | +2.369551 | +63.53 |
| 3 | `observed_vertical_set` | `central_bass_pcset(all_voices)=137` | +1.556723 | +40.16 |
| 4 | `ordered_voice_gap` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.680572 | -30.54 |
| 5 | `universal_passing_interval_metric` | `any_pair_central_abs_class_target_passing_metric(all_voices)=9,0` | +0.947408 | +30.03 |
| 6 | `observed_vertical_set` | `central_bass_pcset(all_voices)=265` | +1.083219 | +28.35 |
| 7 | `observed_vertical_set` | `central_bass_pcset(all_voices)=329` | +1.732826 | +24.51 |
| 8 | `universal_passing_interval_metric` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | +1.521188 | +22.79 |
| 9 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.801908 | -19.59 |
| 10 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=7` | -1.921276 | -19.58 |
| 11 | `attacked_repetition` | `attacked_repeat_from_previous(v3)` | -1.875119 | -18.98 |
| 12 | `directed_pair_interval_metric_trajectory` | `central_pair_abs_class_metric_target_rearticulated(v1,v0)=2,1` | +2.065987 | +18.32 |
| 13 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=0` | -1.991472 | -17.95 |
| 14 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=1` | -1.042197 | -16.20 |
| 15 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=11` | -1.145699 | -17.25 |
| 16 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=10` | -0.677123 | -15.23 |
| 17 | `universal_pair_motion` | `any_pair_arrival_abs_class_same_sign(all_voices)=2` | -0.937171 | -12.89 |
| 18 | `universal_melodic_interval_class` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.560566 | +11.29 |
| 19 | `directed_voice_pair_interval_metric` | `central_pair_abs_class_metric(v0,v1)=1,1` | +1.459760 | +13.14 |
| 20 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.293023 | +13.16 |
| 21 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v3,v1)=6` | -1.160563 | -10.48 |
| 22 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v2,v3)=5` | -0.958822 | -9.75 |
| 23 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v3,v2)=6` | -1.157000 | -9.59 |
| 24 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=12` | -1.457649 | -9.44 |
| 25 | `voice_melodic_distance_threshold` | `abs_step_to_next_gt(v2)=1` | +0.631311 | +8.51 |
| 26 | `observed_vertical_set` | `central_bass_pcset(all_voices)=161` | +1.491162 | +10.39 |
| 27 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v0,v1)=5` | +0.502332 | +8.50 |
| 28 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v1,v3)=5` | -0.744530 | -8.57 |
| 29 | `voice_melodic_distance_threshold` | `abs_step_to_next_gt(v1)=1` | +0.623177 | +8.09 |
| 30 | `three_block_direction_shape` | `three_block_sign_shape(v1)=0,-1` | +0.855274 | +9.04 |

La calibration nulle familiale doit encore être répétée avec les
mondes exacts avant toute prétention de règle scientifique finale.
