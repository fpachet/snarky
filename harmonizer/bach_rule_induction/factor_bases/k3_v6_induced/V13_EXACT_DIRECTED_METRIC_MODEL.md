# V13 — réinduction exacte avec contextes dirigés et métriques

La structure est sélectionnée par les gradients résiduels des véritables
conditionnelles Gibbs. Registre, profil tonal et poids factoriels sont
réappris conjointement. Aucun facteur V6/V8 n'est imposé.

## Résultat

- Catalogue exact : `1660` facteurs.
- Facteurs sélectionnés : `30`.
- NLL validation structure : `0.749027`.
- NLL validation complète : `0.759483`.
- Test réservé chargé : `False`.

| # | Famille | Facteur | Poids | z de sélection |
|---:|---|---|---:|---:|
| 1 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=2` | -1.185153 | -92.97 |
| 2 | `observed_vertical_set` | `central_bass_pcset(all_voices)=145` | +2.390690 | +63.53 |
| 3 | `observed_vertical_set` | `central_bass_pcset(all_voices)=137` | +1.594743 | +40.16 |
| 4 | `ordered_voice_gap` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.597722 | -30.54 |
| 5 | `universal_passing_interval_metric` | `any_pair_central_abs_class_target_passing_metric(all_voices)=9,0` | +0.929315 | +30.03 |
| 6 | `observed_vertical_set` | `central_bass_pcset(all_voices)=265` | +1.126569 | +28.35 |
| 7 | `observed_vertical_set` | `central_bass_pcset(all_voices)=329` | +1.747776 | +24.51 |
| 8 | `universal_passing_interval_metric` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | +1.466944 | +22.79 |
| 9 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.771371 | -19.59 |
| 10 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=7` | -1.918127 | -19.58 |
| 11 | `attacked_repetition` | `attacked_repeat_from_previous(v3)` | -1.883110 | -18.98 |
| 12 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=0` | -1.970795 | -17.94 |
| 13 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=1` | -0.993932 | -16.47 |
| 14 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=11` | -1.099166 | -17.32 |
| 15 | `universal_vertical_interval_class` | `any_pair_central_abs_class(all_voices)=10` | -0.753290 | -15.36 |
| 16 | `universal_pair_motion` | `any_pair_arrival_abs_class_same_sign(all_voices)=2` | -1.006687 | -13.69 |
| 17 | `universal_melodic_interval_class` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.453888 | +11.45 |
| 18 | `universal_pair_motion` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.310755 | +13.10 |
| 19 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v3,v1)=6` | -1.044430 | -10.98 |
| 20 | `ordered_voice_gap` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | -0.496770 | -10.38 |
| 21 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v0,v1)=2` | +1.055683 | +9.95 |
| 22 | `directed_voice_pair_interval_metric` | `central_pair_abs_class_metric(v0,v1)=1,1` | +1.458502 | +11.57 |
| 23 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v3,v2)=6` | -1.080832 | -9.22 |
| 24 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v2,v3)=5` | -0.826484 | -9.49 |
| 25 | `voice_melodic_distance_threshold` | `abs_step_to_next_gt(v2)=1` | +0.537004 | +8.75 |
| 26 | `observed_vertical_set` | `central_bass_pcset(all_voices)=161` | +1.290600 | +10.81 |
| 27 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v0,v1)=5` | +0.356043 | +8.83 |
| 28 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v1,v0)=5` | +0.275731 | +8.31 |
| 29 | `universal_melodic_distance_threshold` | `any_voice_adjacent_step_gt(all_voices)=12` | -1.343292 | -8.23 |
| 30 | `observed_vertical_set` | `central_bass_pcset(all_voices)=1169` | +1.251813 | +10.19 |

La calibration nulle familiale doit encore être répétée avec les
mondes exacts avant toute prétention de règle scientifique finale.

L'audit génératif de développement améliore la basse et les dissonances
faibles, mais aggrave les blocs non triadiques et dissonances sur temps fort.
Le candidat n'est pas promu ; voir `V13_DIRECTED_METRIC_DECISION.md`.
