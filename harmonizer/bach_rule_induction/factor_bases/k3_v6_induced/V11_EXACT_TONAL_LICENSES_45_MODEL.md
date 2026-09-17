# V11 — contrôle de budget à 45 facteurs

La structure est sélectionnée par les gradients résiduels des véritables
conditionnelles Gibbs. Registre, profil tonal et poids factoriels sont
réappris conjointement. Aucun facteur V6/V8 n'est imposé.

## Résultat

- Catalogue exact : `1122` facteurs.
- Facteurs sélectionnés : `45`.
- NLL validation structure : `0.704638`.
- NLL validation complète : `0.711052`.
- Test réservé chargé : `False`.

| # | Famille | Facteur | Poids | z de sélection |
|---:|---|---|---:|---:|
| 1 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=2` | -1.069074 | -92.97 |
| 2 | `observed_vertical_set` | `central_bass_pcset(all_voices)=145` | +2.217657 | +63.53 |
| 3 | `observed_vertical_set` | `central_bass_pcset(all_voices)=137` | +1.373114 | +40.16 |
| 4 | `ordered_voice_gap` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.676735 | -30.54 |
| 5 | `observed_vertical_set` | `central_bass_pcset(all_voices)=265` | +1.029223 | +28.98 |
| 6 | `universal_vertical_interval_target_context` | `any_pair_central_abs_class_target_passing(all_voices)=9` | +0.743908 | +27.50 |
| 7 | `observed_vertical_set` | `central_bass_pcset(all_voices)=329` | +1.788523 | +24.63 |
| 8 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.580598 | -19.51 |
| 9 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=7` | -1.832113 | -20.46 |
| 10 | `attacked_repetition` | `attacked_repeat_from_previous(v3)` | -1.691214 | -19.95 |
| 11 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=0` | -2.008930 | -18.55 |
| 12 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=11` | -1.098830 | -17.00 |
| 13 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=1` | -0.994927 | -17.99 |
| 14 | `universal_pair_motion` | `any_pair_arrival_abs_class_same_sign(all_voices)=2` | -0.988037 | -13.59 |
| 15 | `universal_melodic_interval_class` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.646009 | +12.84 |
| 16 | `universal_pair_motion` | `any_pair_arrival_abs_class_same_sign(all_voices)=10` | -0.378553 | -12.64 |
| 17 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.262744 | +13.80 |
| 18 | `universal_vertical_interval_target_context` | `any_pair_central_abs_class_target_passing(all_voices)=10` | +1.219524 | +13.40 |
| 19 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v3,v1)=6` | -0.874832 | -10.74 |
| 20 | `ordered_voice_gap` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | -0.481918 | -10.54 |
| 21 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=10` | -0.768211 | -11.12 |
| 22 | `universal_vertical_interval_metric_context` | `any_pair_central_abs_class_metric(all_voices)=7,1` | +0.397459 | +10.78 |
| 23 | `voice_melodic_distance_threshold` | `abs_step_to_next_gt(v2)=1` | +0.741838 | +9.33 |
| 24 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v2,v3)=5` | -0.825277 | -8.91 |
| 25 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v3,v2)=6` | -1.062665 | -9.20 |
| 26 | `observed_vertical_set` | `central_bass_pcset(all_voices)=161` | +1.416596 | +11.07 |
| 27 | `observed_vertical_set` | `central_bass_pcset(all_voices)=1169` | +1.354137 | +10.30 |
| 28 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=12` | -1.483444 | -8.27 |
| 29 | `three_block_direction_shape` | `three_block_sign_shape(v1)=0,-1` | +0.958102 | +8.88 |
| 30 | `voice_melodic_distance_threshold` | `abs_step_to_next_gt(v1)=1` | +0.690537 | +8.61 |
| 31 | `universal_pair_motion` | `any_pair_arrival_abs_class_same_sign(all_voices)=7` | -0.261162 | -9.30 |
| 32 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v1,v3)=5` | -0.665825 | -7.72 |
| 33 | `voice_melodic_interval_class` | `abs_class_from_previous(v3)=2` | +0.517849 | +7.73 |
| 34 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v0,v1)=1` | +1.404320 | +7.48 |
| 35 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v3,v2)=0` | +0.507054 | +7.38 |
| 36 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v1,v0)=5` | +0.505971 | +7.13 |
| 37 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v0,v1)=2` | +0.985945 | +7.16 |
| 38 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v3,v2)=9` | -0.409028 | -6.32 |
| 39 | `universal_melodic_interval_class` | `any_voice_adjacent_abs_class(all_voices)=6` | -0.486647 | -5.94 |
| 40 | `voice_melodic_interval_class` | `abs_class_to_next(v3)=5` | +0.311703 | +5.95 |
| 41 | `universal_melodic_interval_class` | `any_voice_adjacent_abs_class(all_voices)=11` | -0.914551 | -5.62 |
| 42 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v3,v0)=3` | +0.108459 | +5.51 |
| 43 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v0,v3)=3` | +0.561762 | +5.50 |
| 44 | `observed_vertical_set` | `central_bass_pcset(all_voices)=1041` | +1.240943 | +8.24 |
| 45 | `universal_melodic_interval_class` | `any_voice_adjacent_abs_class(all_voices)=10` | -0.955999 | -5.55 |

La calibration nulle familiale doit encore être répétée avec les
mondes exacts avant toute prétention de règle scientifique finale.
