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
- Temps d'échantillonnage : `98.032` secondes.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 24.983 | 32.766 | -7.783 pp | `-10.387` à `-5.163` |
| Répétitions de basse | 4.938 | 4.784 | +0.155 pp | `-1.011` à `+1.427` |
| Sauts de basse > 4 demi-tons | 26.917 | 23.889 | +3.027 pp | `+0.793` à `+5.021` |
| Basse hors gamme naturelle globale | 9.094 | 14.174 | -5.081 pp | `-6.687` à `-3.324` |
| Blocs triadiques | 53.875 | 53.712 | +0.163 pp | `-1.748` à `+2.224` |
| Blocs forts non triadiques | 29.598 | 38.266 | -8.667 pp | `-13.948` à `-3.743` |
| Dissonances par bloc faible | 0.892 | 0.852 | +0.040 | `-0.011` à `+0.087` |
| Dissonances par bloc fort | 0.406 | 0.570 | -0.164 | `-0.251` à `-0.082` |
| {0,3,6,8} sur bloc fort | 1.762 | 2.996 | -1.234 pp | `-2.258` à `-0.117` |
| {0,3,6,8} sur bloc faible | 4.225 | 3.836 | +0.389 pp | `-0.800` à `+1.682` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000161`.
- Plus grand déplacement proposé : `1.016339`.
- Structure localement contrôlable : `false`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.217417 | `+0.150646` à `+0.289340` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.106672 | `-0.159456` à `-0.054160` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.060639 | `-0.099211` à `-0.026898` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.036066 | `-0.060922` à `-0.013808` |
| `LEARNED-011` | `attacked_repeat_from_previous(v3)` | -0.024357 | `-0.037852` à `-0.012233` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | +0.020142 | `-0.001740` à `+0.043119` |
| `LEARNED-023` | `central_pair_abs_class(v3,v2)=6` | +0.018821 | `+0.006091` à `+0.030664` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.016388 | `+0.007348` à `+0.027630` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-011` | `attacked_repeat_from_previous(v3)` | +0.048833 | `+0.040090` à `+0.058087` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.036193 | `-0.065595` à `-0.007144` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.025895 | `-0.057967` à `+0.004003` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.020679 | `-0.007781` à `+0.048014` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | -0.012302 | `-0.021786` à `-0.002755` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | +0.010511 | `-0.001721` à `+0.023438` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.010108 | `-0.034783` à `+0.010915` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.009462 | `-0.012546` à `+0.034888` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.203986 | `+0.144756` à `+0.281977` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.101377 | `-0.180942` à `-0.029478` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.091776 | `+0.059760` à `+0.137805` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.038129 | `-0.012568` à `+0.095891` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.035981 | `+0.002817` à `+0.067048` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.022143 | `-0.045408` à `+0.001391` |
| `LEARNED-027` | `central_pair_abs_class(v0,v1)=5` | -0.019260 | `-0.042898` à `+0.005397` |
| `LEARNED-029` | `abs_step_to_next_gt(v1)=1` | +0.017420 | `-0.002004` à `+0.036845` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.061834 | `+0.030122` à `+0.093537` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.027531 | `-0.054957` à `-0.003645` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.026261 | `-0.045202` à `-0.008317` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.014289 | `-0.030216` à `+0.001974` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | +0.014121 | `-0.000561` à `+0.027872` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | +0.012562 | `-0.001813` à `+0.026817` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.012481 | `-0.018940` à `+0.045465` |
| `LEARNED-011` | `attacked_repeat_from_previous(v3)` | -0.012277 | `-0.021273` à `-0.004524` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.066833 | `+0.041517` à `+0.092967` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | -0.065676 | `-0.100321` à `-0.034160` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.059558 | `-0.121476` à `-0.002042` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | +0.048755 | `+0.028914` à `+0.070641` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.040462 | `-0.084689` à `+0.001115` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.039118 | `-0.002525` à `+0.078166` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | +0.038021 | `+0.023333` à `+0.052957` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | -0.026354 | `-0.041087` à `-0.012664` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.073042 | `-0.107148` à `-0.042803` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.063688 | `-0.003037` à `+0.132773` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.047725 | `-0.016024` à `+0.112958` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.047408 | `-0.139925` à `+0.037110` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.044957 | `-0.081136` à `-0.012219` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.044271 | `-0.121472` à `+0.037173` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.035506 | `-0.073989` à `+0.006468` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | +0.033408 | `+0.008854` à `+0.060932` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.238560 | `+0.074506` à `+0.414485` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.160295 | `-0.245591` à `-0.079468` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.157748 | `+0.075492` à `+0.242371` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | +0.096647 | `+0.045892` à `+0.167714` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.092868 | `-0.226599` à `+0.042551` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.085372 | `-0.127617` à `-0.048980` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.078728 | `-0.052305` à `+0.193282` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.069352 | `-0.135407` à `-0.003857` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.191020 | `-0.406561` à `-0.004208` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.131184 | `+0.004550` à `+0.271050` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.088384 | `-0.056125` à `+0.240121` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.082745 | `-0.165839` à `+0.010351` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | +0.078950 | `+0.026625` à `+0.138369` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.076442 | `-0.136030` à `-0.021581` |
| `LEARNED-014` | `any_pair_central_abs_class(all_voices)=1` | +0.045559 | `-0.005909` à `+0.105426` |
| `LEARNED-017` | `any_pair_arrival_abs_class_same_sign(all_voices)=2` | +0.044629 | `-0.003803` à `+0.090150` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.045529 | `+0.009436` à `+0.086876` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.040122 | `-0.071045` à `-0.011262` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.017736 | `+0.011197` à `+0.024894` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.012895 | `-0.026512` à `-0.001543` |
| `LEARNED-029` | `abs_step_to_next_gt(v1)=1` | -0.012847 | `-0.027161` à `-0.000445` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.010399 | `-0.012024` à `+0.033755` |
| `LEARNED-023` | `central_pair_abs_class(v3,v2)=6` | +0.009015 | `+0.003119` à `+0.014763` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.009011 | `-0.033064` à `+0.013022` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.020760 | `+0.014904` à `+0.026252` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.016663 | `-0.044204` à `+0.008830` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.014527 | `-0.008186` à `+0.040705` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.014386 | `-0.026950` à `-0.000572` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.012153 | `-0.007375` à `+0.030993` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.008511 | `-0.006831` à `+0.022874` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.006619 | `-0.015402` à `+0.002045` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | +0.006601 | `-0.001107` à `+0.013953` |
