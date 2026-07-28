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
- Chaînes par pièce : `2`.
- États conservés par chaîne (min/moy/max) : `8/8.0/8`.
- Arrêt adaptatif : `false` ; chaînes convergées : `0/64`.
- Mode d'exécution : `trajectory`.
- Chaînes restaurées : `0/64`.
- Cache issu des mêmes poids : `None`.
- Temps d'échantillonnage : `155.791` secondes.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 24.983 | 26.390 | -1.407 pp | `-3.974` à `+1.078` |
| Répétitions de basse | 4.938 | 4.490 | +0.448 pp | `-0.772` à `+1.817` |
| Sauts de basse > 4 demi-tons | 26.917 | 27.769 | -0.852 pp | `-2.890` à `+1.040` |
| Basse hors gamme naturelle globale | 9.094 | 10.256 | -1.162 pp | `-2.981` à `+0.898` |
| Blocs triadiques | 53.875 | 52.942 | +0.933 pp | `-1.551` à `+3.085` |
| Blocs forts non triadiques | 29.598 | 29.053 | +0.545 pp | `-3.272` à `+4.418` |
| Dissonances par bloc faible | 0.892 | 0.907 | -0.015 | `-0.070` à `+0.040` |
| Dissonances par bloc fort | 0.406 | 0.413 | -0.007 | `-0.066` à `+0.058` |
| {0,3,6,8} sur bloc fort | 1.762 | 2.408 | -0.646 pp | `-1.845` à `+0.708` |
| {0,3,6,8} sur bloc faible | 4.225 | 4.170 | +0.055 pp | `-1.064` à `+1.199` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000226`.
- Plus grand déplacement proposé : `0.250125`.
- Structure localement contrôlable : `true`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.201412 | `+0.153730` à `+0.246201` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.125391 | `-0.180809` à `-0.067398` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.043395 | `-0.083404` à `+0.001104` |
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.027917 | `+0.020041` à `+0.035628` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.023448 | `-0.040244` à `-0.007121` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | -0.022138 | `-0.034732` à `-0.009275` |
| `F-K3-V6-014` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.020166 | `-0.034577` à `-0.004756` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.018585 | `-0.011427` à `+0.051304` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-019` | `attacked_repeat_from_previous(v3)` | +0.045715 | `+0.039454` à `+0.052723` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.033027 | `-0.054061` à `-0.013783` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | -0.019767 | `-0.030976` à `-0.009127` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.013992 | `-0.030502` à `+0.003414` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | +0.009108 | `+0.002062` à `+0.015974` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.008457 | `-0.026473` à `+0.011138` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.007327 | `-0.019749` à `+0.005893` |
| `F-K3-V6-014` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.007239 | `-0.014669` à `-0.000022` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.186734 | `+0.140956` à `+0.234258` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.105455 | `-0.150114` à `-0.056896` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.077733 | `-0.129833` à `-0.034638` |
| `F-K3-V6-014` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.064412 | `+0.044505` à `+0.084063` |
| `F-K3-V6-019` | `attacked_repeat_from_previous(v3)` | -0.025723 | `-0.036020` à `-0.015326` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.025692 | `+0.001932` à `+0.052507` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | -0.024672 | `-0.048000` à `-0.003630` |
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | -0.021026 | `-0.032640` à `-0.010127` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.073678 | `+0.046482` à `+0.100282` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.042961 | `-0.071176` à `-0.012529` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.023460 | `-0.052041` à `+0.004280` |
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.017505 | `+0.012825` à `+0.022560` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.016560 | `+0.005677` à `+0.028199` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.010852 | `-0.020462` à `-0.001485` |
| `F-K3-V6-019` | `attacked_repeat_from_previous(v3)` | -0.007458 | `-0.012527` à `-0.001662` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | -0.007438 | `-0.015746` à `+0.001656` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | -0.094921 | `-0.122246` à `-0.070095` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.068373 | `-0.094525` à `-0.041513` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | +0.063607 | `+0.050477` à `+0.081526` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | +0.057501 | `+0.044586` à `+0.072353` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | -0.055706 | `-0.076496` à `-0.035632` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.050497 | `+0.017564` à `+0.083851` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | +0.046058 | `+0.031240` à `+0.062170` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.042976 | `-0.067261` à `-0.018471` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.106108 | `+0.066249` à `+0.157593` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.084833 | `+0.025610` à `+0.144096` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.078364 | `+0.033746` à `+0.130537` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.059502 | `-0.082602` à `-0.035481` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.043244 | `-0.071824` à `-0.016504` |
| `F-K3-V6-004` | `central_bass_pcset(all_voices)=265` | -0.034882 | `-0.054703` à `-0.014615` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | +0.034059 | `+0.011389` à `+0.061558` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.030522 | `+0.001523` à `+0.060620` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.242739 | `+0.186573` à `+0.301325` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.199410 | `-0.291752` à `-0.106738` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.177219 | `+0.132320` à `+0.225694` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.141186 | `+0.046402` à `+0.243347` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | +0.130511 | `+0.007783` à `+0.263021` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | -0.128338 | `-0.163742` à `-0.097378` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.110047 | `-0.153145` à `-0.070323` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.066691 | `-0.106812` à `-0.028026` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.205753 | `+0.139671` à `+0.295921` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.161693 | `+0.071039` à `+0.256107` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.100816 | `+0.004715` à `+0.202178` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.100420 | `+0.047200` à `+0.156419` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.091143 | `-0.131220` à `-0.051733` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.048069 | `-0.100640` à `+0.003043` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | +0.047263 | `+0.007388` à `+0.092192` |
| `F-K3-V6-004` | `central_bass_pcset(all_voices)=265` | -0.040452 | `-0.069209` à `-0.011712` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.027316 | `+0.020579` à `+0.034399` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.022660 | `+0.006855` à `+0.038671` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | +0.011155 | `-0.002791` à `+0.025284` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.010870 | `-0.004923` à `+0.026341` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.009825 | `+0.002739` à `+0.016268` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.007341 | `-0.023806` à `+0.009451` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | -0.007125 | `-0.014825` à `+0.001670` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.005559 | `-0.012311` à `+0.024088` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.046872 | `+0.037779` à `+0.057995` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.026948 | `-0.050679` à `-0.002828` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.023519 | `+0.009394` à `+0.037177` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | +0.017476 | `-0.022351` à `+0.053974` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.015441 | `-0.008626` à `+0.040605` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.012246 | `-0.020369` à `-0.004810` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | -0.011563 | `-0.017911` à `-0.005121` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.011066 | `-0.004525` à `+0.025616` |
