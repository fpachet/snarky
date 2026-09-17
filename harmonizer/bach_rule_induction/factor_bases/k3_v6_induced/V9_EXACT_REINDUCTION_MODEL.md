# V9 — réinduction exacte depuis zéro

La structure est sélectionnée par les gradients résiduels des véritables
conditionnelles Gibbs. Registre, profil tonal et poids factoriels sont
réappris conjointement. Aucun facteur V6/V8 n'est imposé.

## Résultat

- Catalogue exact : `954` facteurs.
- Facteurs sélectionnés : `30`.
- NLL validation structure : `0.774130`.
- NLL validation complète : `0.779783`.
- Test réservé chargé : `False`.

| # | Famille | Facteur | Poids | z de sélection |
|---:|---|---|---:|---:|
| 1 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=2` | -1.330036 | -92.97 |
| 2 | `observed_vertical_set` | `central_bass_pcset(all_voices)=145` | +2.408396 | +63.53 |
| 3 | `observed_vertical_set` | `central_bass_pcset(all_voices)=137` | +1.648617 | +40.16 |
| 4 | `ordered_voice_gap` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.638392 | -30.54 |
| 5 | `observed_vertical_set` | `central_bass_pcset(all_voices)=265` | +1.052941 | +28.98 |
| 6 | `observed_vertical_set` | `central_bass_pcset(all_voices)=329` | +1.614206 | +23.85 |
| 7 | `three_block_direction_shape` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | +0.462028 | +21.66 |
| 8 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=7` | -1.979848 | -20.93 |
| 9 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.743307 | -19.10 |
| 10 | `attacked_repetition` | `attacked_repeat_from_previous(v3)` | -1.911294 | -18.58 |
| 11 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=0` | -2.012708 | -19.20 |
| 12 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=1` | -1.095832 | -17.76 |
| 13 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=11` | -1.203248 | -19.03 |
| 14 | `universal_pair_motion` | `any_pair_arrival_abs_class_same_sign(all_voices)=2` | -1.020789 | -13.98 |
| 15 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=10` | -0.534537 | -13.43 |
| 16 | `observed_vertical_set` | `central_bass_pcset(all_voices)=1169` | +1.420885 | +14.24 |
| 17 | `universal_melodic_interval_class` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.573616 | +11.75 |
| 18 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.281682 | +13.32 |
| 19 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v3,v1)=6` | -1.172898 | -11.16 |
| 20 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v0,v1)=2` | +0.991090 | +10.69 |
| 21 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v2,v3)=5` | -0.944596 | -10.35 |
| 22 | `observed_vertical_set` | `central_bass_pcset(all_voices)=161` | +1.581815 | +12.03 |
| 23 | `ordered_voice_gap` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | -0.489012 | -9.82 |
| 24 | `voice_melodic_distance_threshold` | `abs_step_to_next_gt(v2)=1` | +0.670119 | +9.91 |
| 25 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v3,v2)=6` | -1.110839 | -9.48 |
| 26 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v1,v3)=5` | -0.783050 | -8.68 |
| 27 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v0,v1)=1` | +1.442347 | +8.65 |
| 28 | `three_block_direction_shape` | `three_block_sign_shape(v1)=0,-1` | +1.007989 | +9.57 |
| 29 | `voice_melodic_distance_threshold` | `abs_step_to_next_gt(v1)=1` | +0.652113 | +8.39 |
| 30 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=12` | -1.367333 | -8.30 |

La calibration nulle familiale doit encore être répétée avec les
mondes exacts avant toute prétention de règle scientifique finale.
