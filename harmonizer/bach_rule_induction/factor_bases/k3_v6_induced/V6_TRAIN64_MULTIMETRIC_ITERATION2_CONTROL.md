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
- Chaînes par pièce : `1`.
- États conservés par chaîne : `6`.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 25.777 | 27.490 | -1.713 pp | `-3.655` à `+0.121` |
| Répétitions de basse | 4.450 | 4.006 | +0.444 pp | `-0.369` à `+1.342` |
| Sauts de basse > 4 demi-tons | 26.725 | 25.789 | +0.936 pp | `-0.888` à `+2.697` |
| Basse hors gamme naturelle globale | 8.429 | 10.561 | -2.132 pp | `-3.697` à `-0.573` |
| Blocs triadiques | 53.925 | 52.020 | +1.905 pp | `+0.245` à `+3.649` |
| Blocs forts non triadiques | 29.307 | 31.531 | -2.224 pp | `-4.928` à `+0.744` |
| Dissonances par bloc faible | 0.958 | 0.925 | +0.034 | `-0.033` à `+0.100` |
| Dissonances par bloc fort | 0.404 | 0.449 | -0.045 | `-0.090` à `+0.004` |
| {0,3,6,8} sur bloc fort | 2.649 | 2.414 | +0.234 pp | `-0.858` à `+1.382` |
| {0,3,6,8} sur bloc faible | 3.737 | 4.580 | -0.843 pp | `-1.784` à `+0.100` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000261`.
- Plus grand déplacement proposé : `0.558983`.
- Structure localement contrôlable : `true`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.219168 | `+0.162338` à `+0.281392` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.107868 | `-0.151739` à `-0.067549` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.060635 | `-0.104265` à `-0.014213` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.038922 | `+0.010383` à `+0.071619` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | -0.027210 | `-0.054002` à `+0.001543` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.026066 | `-0.044288` à `-0.010411` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | +0.019723 | `-0.006404` à `+0.045977` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.017117 | `+0.000424` à `+0.035299` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-019` | `attacked_repeat_from_previous(v3)` | +0.039828 | `+0.033901` à `+0.046352` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.024248 | `-0.045702` à `-0.003674` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.018557 | `-0.043619` à `+0.007021` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.012404 | `-0.000083` à `+0.024920` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | -0.011356 | `-0.022106` à `-0.001696` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.010675 | `-0.026665` à `+0.004323` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.007584 | `-0.003931` à `+0.020485` |
| `F-K3-V6-018` | `previous_ordered_gap_le(v0,v1)=2` | -0.005874 | `-0.011547` à `-0.000431` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.135509 | `+0.087037` à `+0.189534` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.094069 | `-0.142520` à `-0.044707` |
| `F-K3-V6-014` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.078133 | `+0.059001` à `+0.099455` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.068401 | `-0.113457` à `-0.023552` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | +0.027235 | `+0.006632` à `+0.050622` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.020985 | `-0.039147` à `-0.002740` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.018322 | `-0.017903` à `+0.054578` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.017376 | `-0.043345` à `+0.006602` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.059501 | `+0.034176` à `+0.086270` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.039990 | `-0.065915` à `-0.014442` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.015669 | `-0.006297` à `+0.037386` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.012911 | `-0.023426` à `-0.003789` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | +0.012382 | `+0.000712` à `+0.024375` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.009340 | `-0.001106` à `+0.019178` |
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.009292 | `+0.004276` à `+0.013837` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | +0.007930 | `-0.006895` à `+0.022808` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | -0.092689 | `-0.117002` à `-0.071265` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.072905 | `-0.115719` à `-0.032819` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | +0.064606 | `+0.048839` à `+0.081046` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | -0.061637 | `-0.080393` à `-0.044263` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | +0.058509 | `+0.046126` à `+0.073166` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | +0.047731 | `+0.034765` à `+0.063784` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.037124 | `-0.002533` à `+0.077106` |
| `F-K3-V6-004` | `central_bass_pcset(all_voices)=265` | +0.033885 | `+0.020870` à `+0.046527` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.102825 | `+0.068837` à `+0.142955` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.053357 | `-0.077085` à `-0.030913` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.052983 | `-0.110324` à `+0.003090` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.042677 | `-0.066976` à `-0.020811` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.037450 | `+0.003443` à `+0.069059` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.036122 | `-0.026378` à `+0.095432` |
| `F-K3-V6-004` | `central_bass_pcset(all_voices)=265` | -0.027862 | `-0.047662` à `-0.006968` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | -0.024039 | `-0.055432` à `+0.008505` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.317890 | `+0.173792` à `+0.488813` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.203696 | `+0.101647` à `+0.295381` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.202517 | `+0.148085` à `+0.256045` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | -0.128887 | `-0.168031` à `-0.095944` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.115742 | `-0.159621` à `-0.075193` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.107924 | `-0.151936` à `-0.070503` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.089968 | `-0.288577` à `+0.077059` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | +0.071164 | `-0.002776` à `+0.158475` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.213022 | `+0.145870` à `+0.299842` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.097817 | `-0.193765` à `-0.000491` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.072842 | `-0.112978` à `-0.030343` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.059704 | `-0.102051` à `-0.021397` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.057598 | `+0.003592` à `+0.110957` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.048591 | `-0.068047` à `+0.162916` |
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.043409 | `+0.020228` à `+0.068199` |
| `F-K3-V6-004` | `central_bass_pcset(all_voices)=265` | -0.041973 | `-0.082279` à `-0.002524` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.024492 | `+0.018589` à `+0.031013` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.021928 | `+0.008299` à `+0.036512` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.020269 | `-0.038047` à `-0.000939` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | -0.011190 | `-0.019973` à `-0.001843` |
| `F-K3-V6-014` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.009753 | `-0.017376` à `-0.002103` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.008979 | `-0.002355` à `+0.020399` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | -0.008923 | `-0.021481` à `+0.003721` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.008264 | `-0.001797` à `+0.019580` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.041406 | `+0.032253` à `+0.051235` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.031474 | `+0.014929` à `+0.047525` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.020905 | `-0.042384` à `-0.000155` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | -0.014946 | `-0.024613` à `-0.006251` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.014009 | `-0.004360` à `+0.031636` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | -0.008402 | `-0.015881` à `-0.001489` |
| `F-K3-V6-004` | `central_bass_pcset(all_voices)=265` | -0.008222 | `-0.015370` à `-0.001241` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.007036 | `-0.003617` à `+0.018204` |
