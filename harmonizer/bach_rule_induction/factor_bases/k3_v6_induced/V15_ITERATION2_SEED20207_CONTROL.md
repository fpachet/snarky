# V6 — contrôlabilité des résidus par les 30 facteurs gelés

Cette analyse utilise uniquement des chorals du train. Pour une métrique
`g` et un facteur `f`, la sensibilité locale est estimée par :

```text
∂ E[g] / ∂ poids(f) = Cov(g, nombre_d_activations(f))
```

Aucun facteur ni poids n'est modifié par cette expérience. Le test
réservé n'est pas chargé.

## Échantillonnage

- Pièces : `32`.
- Chaînes par pièce : `1`.
- États conservés par chaîne (min/moy/max) : `6/6.0/6`.
- Arrêt adaptatif : `false` ; chaînes convergées : `0/32`.
- Mode d'exécution : `trajectory`.
- Chaînes restaurées : `32/32`.
- Cache issu des mêmes poids : `False`.
- Temps d'échantillonnage : `98.752` secondes.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 24.983 | 32.472 | -7.489 pp | `-10.122` à `-4.714` |
| Répétitions de basse | 4.938 | 4.216 | +0.722 pp | `-0.518` à `+2.041` |
| Sauts de basse > 4 demi-tons | 26.917 | 23.008 | +3.908 pp | `+1.688` à `+5.961` |
| Basse hors gamme naturelle globale | 9.094 | 13.629 | -4.536 pp | `-6.205` à `-2.756` |
| Blocs triadiques | 53.875 | 53.855 | +0.020 pp | `-2.416` à `+2.520` |
| Blocs forts non triadiques | 29.598 | 37.352 | -7.753 pp | `-12.795` à `-2.607` |
| Dissonances par bloc faible | 0.892 | 0.868 | +0.024 | `-0.026` à `+0.074` |
| Dissonances par bloc fort | 0.406 | 0.548 | -0.142 | `-0.222` à `-0.066` |
| {0,3,6,8} sur bloc fort | 1.762 | 2.665 | -0.903 pp | `-1.963` à `+0.207` |
| {0,3,6,8} sur bloc faible | 4.225 | 3.811 | +0.414 pp | `-0.764` à `+1.603` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000183`.
- Plus grand déplacement proposé : `1.095194`.
- Structure localement contrôlable : `false`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.159233 | `+0.101045` à `+0.219721` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.060378 | `-0.120767` à `-0.006791` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.026547 | `-0.059630` à `+0.003252` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | +0.026205 | `+0.008598` à `+0.044190` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.023707 | `-0.014131` à `+0.059404` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | +0.019229 | `+0.000247` à `+0.037915` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.016273 | `-0.037215` à `+0.003789` |
| `LEARNED-005` | `any_pair_central_abs_class_target_passing_metric(all_voices)=9,0` | +0.013196 | `-0.010465` à `+0.036091` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-011` | `attacked_repeat_from_previous(v3)` | +0.034413 | `+0.027775` à `+0.041982` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.027638 | `-0.051605` à `-0.007706` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.011039 | `-0.000820` à `+0.021890` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.008282 | `-0.026654` à `+0.012432` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.007463 | `-0.031977` à `+0.017501` |
| `LEARNED-025` | `abs_step_to_next_gt(v2)=1` | -0.007184 | `-0.017678` à `+0.004313` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | -0.006289 | `-0.015185` à `+0.001892` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.004903 | `-0.023750` à `+0.015223` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.127939 | `+0.084083` à `+0.176385` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.038901 | `+0.009288` à `+0.072483` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.033455 | `+0.007434` à `+0.058465` |
| `LEARNED-029` | `abs_step_to_next_gt(v1)=1` | -0.031140 | `-0.050242` à `-0.011032` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | -0.030354 | `-0.072157` à `+0.007785` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.027813 | `-0.093774` à `+0.030328` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.027441 | `-0.089236` à `+0.028796` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | -0.023689 | `-0.049913` à `-0.003579` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.045655 | `+0.004521` à `+0.087709` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.026150 | `-0.002121` à `+0.053826` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.025213 | `-0.008305` à `+0.061965` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.016621 | `+0.006794` à `+0.027783` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.015273 | `-0.054791` à `+0.021988` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.012285 | `-0.026972` à `+0.004950` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | +0.009354 | `-0.002980` à `+0.021811` |
| `LEARNED-025` | `abs_step_to_next_gt(v2)=1` | +0.009250 | `-0.008423` à `+0.027828` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | -0.091714 | `-0.142728` à `-0.046932` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.081939 | `+0.059309` à `+0.104802` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.060146 | `-0.001816` à `+0.123864` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | +0.037776 | `+0.017896` à `+0.057031` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | +0.037320 | `+0.013362` à `+0.063272` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | -0.036947 | `-0.066431` à `-0.014317` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | -0.036458 | `-0.055712` à `-0.018029` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.031236 | `-0.074272` à `+0.011688` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.082121 | `+0.020004` à `+0.142153` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.062044 | `-0.098583` à `-0.027132` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.059830 | `-0.011609` à `+0.132257` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.055808 | `-0.090912` à `-0.019400` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.052132 | `-0.146637` à `+0.047842` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.041541 | `-0.072511` à `-0.010408` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.034743 | `-0.132136` à `+0.055698` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | +0.034030 | `+0.000823` à `+0.066792` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.304948 | `+0.201748` à `+0.421466` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | +0.159650 | `+0.099580` à `+0.229388` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.142993 | `-0.200524` à `-0.087031` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.116155 | `-0.229394` à `-0.004624` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.099930 | `-0.146650` à `-0.058319` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | +0.092818 | `+0.051054` à `+0.137750` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.063621 | `-0.104377` à `+0.228741` |
| `LEARNED-014` | `any_pair_central_abs_class(all_voices)=1` | +0.055547 | `+0.016905` à `+0.092939` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.193661 | `+0.092215` à `+0.293017` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.150769 | `+0.020456` à `+0.265636` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | +0.099328 | `+0.042068` à `+0.157888` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.069744 | `-0.145353` à `+0.004419` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.068131 | `-0.128934` à `-0.010237` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.065527 | `-0.126977` à `-0.002966` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.060169 | `-0.098820` à `+0.217545` |
| `LEARNED-014` | `any_pair_central_abs_class(all_voices)=1` | +0.044627 | `-0.009168` à `+0.106075` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.026925 | `-0.054729` à `-0.000395` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.020908 | `-0.040384` à `-0.003389` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | -0.019433 | `-0.038322` à `-0.001018` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.019065 | `+0.013672` à `+0.025896` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | -0.012643 | `-0.023194` à `-0.001765` |
| `LEARNED-023` | `central_pair_abs_class(v3,v2)=6` | +0.012622 | `+0.006425` à `+0.021261` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | -0.009149 | `-0.020424` à `+0.003658` |
| `LEARNED-025` | `abs_step_to_next_gt(v2)=1` | +0.008161 | `-0.004797` à `+0.020697` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.035784 | `+0.027083` à `+0.046713` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.020250 | `+0.001144` à `+0.041492` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.013398 | `-0.005586` à `+0.031579` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.013084 | `+0.000501` à `+0.025805` |
| `LEARNED-023` | `central_pair_abs_class(v3,v2)=6` | +0.010598 | `+0.004930` à `+0.015892` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.006632 | `-0.015212` à `+0.000978` |
| `LEARNED-005` | `any_pair_central_abs_class_target_passing_metric(all_voices)=9,0` | -0.006305 | `-0.020046` à `+0.006598` |
| `LEARNED-029` | `abs_step_to_next_gt(v1)=1` | +0.005606 | `-0.006565` à `+0.020244` |
