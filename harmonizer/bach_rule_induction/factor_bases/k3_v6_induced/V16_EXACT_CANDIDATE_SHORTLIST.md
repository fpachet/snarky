# V16 — présélection conditionnelle des candidats hybrides

Cette étape ne sélectionne encore aucune nouvelle règle. Elle calcule le
gradient conditionnel exact sous le modèle V13, exclut les facteurs déjà
présents et produit le top-K qui devra ensuite passer le garde-fou
génératif multigraine.

- Catalogue : `3676` clauses.
- Facteurs déjà présents : `30`.
- Candidats conditionnellement admissibles : `69`.
- Candidats conservés : `12`.
- Test réservé chargé : `false`.

| Rang | Famille | Candidat | Score | Gradient | z | Occasions | Pièces |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `directed_pair_interval_metric_trajectory` | `central_pair_abs_class_metric_target_rearticulated(v1,v2)=7,1` | +0.002964 | +0.011969 | +10.69 | 756 | 32 |
| 2 | `three_block_direction_shape` | `three_block_sign_shape(v1)=0,-1` | +0.002876 | +0.012906 | +8.80 | 1400 | 32 |
| 3 | `voice_melodic_distance_threshold` | `abs_step_to_next_gt(v1)=1` | +0.002864 | +0.020356 | +7.71 | 2125 | 32 |
| 4 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v1,v3)=5` | +0.002569 | -0.011736 | -7.43 | 4401 | 32 |
| 5 | `three_block_direction_shape` | `any_voice_three_block_sign_shape(all_voices)=0,-1` | +0.002507 | +0.019138 | +8.49 | 4242 | 32 |
| 6 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v0,v3)=3` | +0.002167 | +0.008849 | +7.02 | 1813 | 32 |
| 7 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v2,v1)=7` | +0.001857 | +0.013563 | +6.69 | 4478 | 32 |
| 8 | `voice_melodic_interval_class` | `abs_class_from_previous(v3)=0` | +0.001795 | +0.010962 | +6.63 | 2411 | 32 |
| 9 | `universal_pair_motion` | `any_pair_arrival_abs_class_same_sign(all_voices)=10` | +0.001769 | -0.018041 | -7.83 | 6295 | 32 |
| 10 | `voice_pair_vertical_interval_class` | `central_pair_abs_class(v3,v0)=3` | +0.001690 | +0.009068 | +6.51 | 2411 | 32 |
| 11 | `directed_pair_interval_metric_trajectory` | `central_pair_abs_class_metric_target_rearticulated(v1,v0)=1,1` | +0.001630 | +0.002208 | +9.74 | 123 | 28 |
| 12 | `universal_melodic_interval_class` | `any_voice_adjacent_abs_class(all_voices)=6` | +0.001574 | -0.014444 | -6.38 | 7273 | 32 |

Aucun candidat de cette table n'est admis par ce seul classement.
V16 doit maintenant mesurer, pour chacun, la covariance entre son
activation et les dix diagnostics dans les mêmes chaînes persistantes.
