# V10 — réinduction exacte avec licences locales d’intervalle

La structure est sélectionnée par les gradients résiduels des véritables
conditionnelles Gibbs. Registre, profil tonal et poids factoriels sont
réappris conjointement. Aucun facteur V6/V8 n'est imposé.

## Résultat

- Catalogue exact : `1050` facteurs.
- Facteurs sélectionnés : `30`.
- NLL validation structure : `0.761534`.
- NLL validation complète : `0.757960`.
- Test réservé chargé : `False`.

| # | Famille | Facteur | Poids | z de sélection |
|---:|---|---|---:|---:|
| 1 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=2` | -1.181618 | -92.97 |
| 2 | `observed_vertical_set` | `central_bass_pcset(all_voices)=145` | +2.280005 | +63.53 |
| 3 | `observed_vertical_set` | `central_bass_pcset(all_voices)=137` | +1.509835 | +40.16 |
| 4 | `ordered_voice_gap` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.573328 | -30.54 |
| 5 | `observed_vertical_set` | `central_bass_pcset(all_voices)=265` | +1.156210 | +28.98 |
| 6 | `universal_vertical_interval_target_context` | `any_pair_central_abs_class_target_passing(all_voices)=9` | +0.699597 | +27.50 |
| 7 | `observed_vertical_set` | `central_bass_pcset(all_voices)=329` | +1.795292 | +24.63 |
| 8 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.766700 | -19.51 |
| 9 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=7` | -1.981515 | -20.46 |
| 10 | `attacked_repetition` | `attacked_repeat_from_previous(v3)` | -1.885802 | -19.95 |
| 11 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=0` | -1.952537 | -18.55 |
| 12 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=11` | -1.094572 | -17.00 |
| 13 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=1` | -1.001580 | -17.99 |
| 14 | `universal_pair_motion` | `any_pair_arrival_abs_class_same_sign(all_voices)=2` | -0.963997 | -13.59 |
| 15 | `universal_melodic_interval_class` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.570554 | +12.84 |
| 16 | `universal_pair_motion` | `any_pair_arrival_abs_class_same_sign(all_voices)=10` | -0.446032 | -12.64 |
| 17 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.295370 | +13.80 |
| 18 | `universal_vertical_interval_target_context` | `any_pair_central_abs_class_target_passing(all_voices)=10` | +1.284584 | +13.40 |
| 19 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v3,v1)=6` | -1.050273 | -10.74 |
| 20 | `ordered_voice_gap` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | -0.523276 | -10.54 |
| 21 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=10` | -0.687538 | -11.12 |
| 22 | `universal_vertical_interval_metric_context` | `any_pair_central_abs_class_metric(all_voices)=7,1` | +0.344444 | +10.78 |
| 23 | `voice_melodic_distance_threshold` | `abs_step_to_next_gt(v2)=1` | +0.653432 | +9.33 |
| 24 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v2,v3)=5` | -0.826717 | -8.91 |
| 25 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v3,v2)=6` | -1.052127 | -9.20 |
| 26 | `observed_vertical_set` | `central_bass_pcset(all_voices)=161` | +1.320909 | +11.07 |
| 27 | `observed_vertical_set` | `central_bass_pcset(all_voices)=1169` | +1.233326 | +10.30 |
| 28 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=12` | -1.359710 | -8.27 |
| 29 | `three_block_direction_shape` | `three_block_sign_shape(v1)=0,-1` | +0.985849 | +8.88 |
| 30 | `voice_melodic_distance_threshold` | `abs_step_to_next_gt(v1)=1` | +0.621068 | +8.61 |

La calibration nulle familiale doit encore être répétée avec les
mondes exacts avant toute prétention de règle scientifique finale.
