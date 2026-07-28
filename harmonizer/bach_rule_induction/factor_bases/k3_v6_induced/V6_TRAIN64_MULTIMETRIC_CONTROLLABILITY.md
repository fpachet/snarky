# V6 — contrôlabilité des résidus par les 30 facteurs gelés

Cette analyse utilise uniquement des chorals du train. Pour une métrique
`g` et un facteur `f`, la sensibilité locale est estimée par :

```text
∂ E[g] / ∂ poids(f) = Cov(g, nombre_d_activations(f))
```

Aucun facteur ni poids n'est modifié par cette expérience. Le test
réservé n'est pas chargé.

## Échantillonnage

- Pièces : `64`.
- Chaînes par pièce : `2`.
- États conservés par chaîne : `6`.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 25.777 | 28.216 | -2.440 pp | `-4.190` à `-0.644` |
| Répétitions de basse | 4.450 | 5.220 | -0.770 pp | `-1.534` à `+0.049` |
| Sauts de basse > 4 demi-tons | 26.725 | 22.621 | +4.104 pp | `+2.459` à `+5.852` |
| Basse hors gamme naturelle globale | 8.429 | 11.088 | -2.659 pp | `-4.151` à `-1.209` |
| Blocs triadiques | 53.925 | 51.789 | +2.136 pp | `+0.794` à `+3.536` |
| Blocs forts non triadiques | 29.307 | 37.330 | -8.023 pp | `-10.792` à `-5.207` |
| Dissonances par bloc faible | 0.958 | 0.910 | +0.048 | `-0.011` à `+0.113` |
| Dissonances par bloc fort | 0.404 | 0.583 | -0.180 | `-0.222` à `-0.135` |
| {0,3,6,8} sur bloc fort | 2.649 | 2.693 | -0.044 pp | `-1.061` à `+0.994` |
| {0,3,6,8} sur bloc faible | 3.737 | 3.411 | +0.325 pp | `-0.353` à `+0.951` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000352`.
- Plus grand déplacement proposé : `0.727985`.
- Structure localement contrôlable : `true`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.255694 | `+0.222372` à `+0.293586` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.139463 | `-0.176909` à `-0.104854` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.087839 | `-0.127634` à `-0.052142` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.029714 | `-0.040446` à `-0.018247` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.027648 | `+0.000292` à `+0.057721` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | -0.023860 | `-0.034611` à `-0.013299` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.019958 | `-0.038090` à `-0.002241` |
| `F-K3-V6-014` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.018688 | `-0.031328` à `-0.007073` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-019` | `attacked_repeat_from_previous(v3)` | +0.045447 | `+0.040529` à `+0.050537` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.031934 | `-0.049006` à `-0.014476` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.023567 | `-0.038811` à `-0.008137` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | -0.023152 | `-0.031473` à `-0.014721` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.019344 | `-0.034815` à `-0.004220` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | +0.010600 | `+0.004785` à `+0.017278` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | +0.008332 | `-0.000216` à `+0.017568` |
| `F-K3-V6-004` | `central_bass_pcset(all_voices)=265` | -0.007359 | `-0.013455` à `-0.001679` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.200938 | `+0.157642` à `+0.244814` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.120551 | `-0.157470` à `-0.086025` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.077457 | `-0.113459` à `-0.039663` |
| `F-K3-V6-014` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.070745 | `+0.058876` à `+0.083134` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | +0.024310 | `+0.010139` à `+0.038960` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | +0.021109 | `+0.001659` à `+0.038503` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | -0.019856 | `-0.044911` à `+0.004888` |
| `F-K3-V6-019` | `attacked_repeat_from_previous(v3)` | -0.017312 | `-0.025045` à `-0.010089` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.091513 | `+0.072660` à `+0.112152` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.052739 | `-0.076499` à `-0.030995` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.039891 | `+0.021591` à `+0.058931` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | -0.011367 | `-0.016533` à `-0.006371` |
| `F-K3-V6-019` | `attacked_repeat_from_previous(v3)` | -0.011179 | `-0.015540` à `-0.007177` |
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.010740 | `+0.005598` à `+0.015806` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.010150 | `-0.019818` à `-0.000332` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.007773 | `-0.031836` à `+0.015865` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | -0.109994 | `-0.131605` à `-0.088690` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | -0.107987 | `-0.127174` à `-0.089010` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.089397 | `-0.124723` à `-0.055499` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | +0.088106 | `+0.073543` à `+0.105518` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.071384 | `+0.036059` à `+0.103596` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | +0.049429 | `+0.038437` à `+0.060540` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | +0.035352 | `+0.024444` à `+0.047073` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.033960 | `-0.058339` à `-0.011598` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.131007 | `+0.102858` à `+0.161344` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.125715 | `+0.091083` à `+0.163251` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.107900 | `+0.065239` à `+0.154439` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.064596 | `-0.088644` à `-0.042048` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.061091 | `-0.116733` à `-0.001824` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.047358 | `-0.068203` à `-0.027698` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.041923 | `+0.006913` à `+0.080949` |
| `F-K3-V6-004` | `central_bass_pcset(all_voices)=265` | -0.037786 | `-0.054703` à `-0.020656` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.244382 | `+0.183557` à `+0.304530` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.239612 | `+0.153212` à `+0.329003` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.221065 | `+0.143948` à `+0.287175` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.216138 | `-0.267512` à `-0.166147` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.143459 | `-0.228136` à `-0.063121` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | -0.141504 | `-0.176373` à `-0.108745` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.081569 | `+0.025492` à `+0.140888` |
| `F-K3-V6-029` | `central_tonic_pcset(all_voices)=2180` | -0.074006 | `-0.104935` à `-0.045283` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.289877 | `+0.238048` à `+0.349406` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.260177 | `+0.192774` à `+0.327785` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.214799 | `+0.125200` à `+0.303012` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.106500 | `-0.222237` à `+0.013197` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.089819 | `-0.134422` à `-0.046523` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.080423 | `-0.123792` à `-0.039345` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.072922 | `-0.002134` à `+0.142613` |
| `F-K3-V6-004` | `central_bass_pcset(all_voices)=265` | -0.059077 | `-0.093994` à `-0.024007` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.026553 | `+0.020331` à `+0.033336` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.021519 | `+0.008856` à `+0.035457` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.018419 | `-0.040258` à `+0.002161` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.016495 | `-0.000123` à `+0.034785` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.012557 | `-0.032422` à `+0.008457` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.012137 | `+0.000317` à `+0.025179` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | -0.010754 | `-0.022500` à `+0.000723` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.010214 | `-0.003692` à `+0.024581` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.033165 | `+0.026114` à `+0.040719` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.020019 | `+0.007205` à `+0.035727` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.015967 | `+0.005630` à `+0.027009` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.010223 | `-0.006018` à `+0.028412` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | -0.010139 | `-0.014779` à `-0.005462` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.009820 | `-0.025022` à `+0.005950` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.009351 | `-0.026856` à `+0.007920` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | -0.007565 | `-0.012522` à `-0.003145` |
