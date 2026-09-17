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
- États conservés par chaîne (min/moy/max) : `6/6.0/6`.
- Arrêt adaptatif : `false` ; chaînes convergées : `0/64`.
- Mode d'exécution : `trajectory`.
- Chaînes restaurées : `0/64`.
- Cache issu des mêmes poids : `None`.
- Temps d'échantillonnage : `682.221` secondes.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 24.983 | 28.619 | -3.637 pp | `-6.299` à `-1.128` |
| Répétitions de basse | 4.938 | 4.359 | +0.579 pp | `-0.630` à `+2.001` |
| Sauts de basse > 4 demi-tons | 26.917 | 28.294 | -1.377 pp | `-3.419` à `+0.524` |
| Basse hors gamme naturelle globale | 9.094 | 13.751 | -4.657 pp | `-6.273` à `-3.030` |
| Blocs triadiques | 53.875 | 51.972 | +1.903 pp | `-0.327` à `+4.220` |
| Blocs forts non triadiques | 29.598 | 40.283 | -10.685 pp | `-15.234` à `-6.579` |
| Dissonances par bloc faible | 0.892 | 0.900 | -0.008 | `-0.049` à `+0.032` |
| Dissonances par bloc fort | 0.406 | 0.611 | -0.205 | `-0.270` à `-0.141` |
| {0,3,6,8} sur bloc fort | 1.762 | 3.231 | -1.469 pp | `-2.597` à `-0.151` |
| {0,3,6,8} sur bloc faible | 4.225 | 3.582 | +0.643 pp | `-0.444` à `+1.819` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000428`.
- Plus grand déplacement proposé : `0.540945`.
- Structure localement contrôlable : `true`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.307442 | `+0.243668` à `+0.367646` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.230397 | `-0.311997` à `-0.156445` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.072929 | `-0.116505` à `-0.032770` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.051876 | `-0.148922` à `+0.038893` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | -0.050588 | `-0.142130` à `+0.036354` |
| `LEARNED-005` | `any_pair_central_abs_class_target_passing_metric(all_voices)=9,0` | +0.035451 | `+0.011594` à `+0.062928` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.029108 | `-0.005026` à `+0.063800` |
| `V16-CANDIDATE-008` | `abs_class_from_previous(v3)=0` | -0.028228 | `-0.043971` à `-0.011679` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-011` | `attacked_repeat_from_previous(v3)` | +0.040635 | `+0.034619` à `+0.046821` |
| `V16-CANDIDATE-008` | `abs_class_from_previous(v3)=0` | +0.038887 | `+0.032235` à `+0.045391` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.032863 | `-0.059285` à `-0.008048` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | -0.020658 | `-0.035237` à `-0.007141` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.017851 | `-0.011145` à `+0.043158` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.016916 | `-0.033602` à `-0.001312` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.014180 | `-0.016318` à `+0.043822` |
| `V16-CANDIDATE-005` | `any_voice_three_block_sign_shape(all_voices)=0,-1` | +0.013667 | `+0.006688` à `+0.021321` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.324516 | `+0.244443` à `+0.403603` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.186492 | `+0.084538` à `+0.294438` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.185090 | `-0.257304` à `-0.101846` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.180268 | `+0.129511` à `+0.235259` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.142608 | `+0.045650` à `+0.242166` |
| `LEARNED-005` | `any_pair_central_abs_class_target_passing_metric(all_voices)=9,0` | -0.049582 | `-0.076180` à `-0.027241` |
| `LEARNED-029` | `any_voice_adjacent_step_gt(all_voices)=12` | +0.045519 | `+0.024112` à `+0.067019` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.042113 | `-0.081206` à `-0.000641` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.091210 | `+0.050283` à `+0.130286` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.054153 | `-0.095908` à `-0.010275` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.034510 | `-0.059165` à `-0.011351` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.033834 | `-0.070568` à `+0.004347` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | -0.026981 | `-0.064770` à `+0.012224` |
| `LEARNED-029` | `any_voice_adjacent_step_gt(all_voices)=12` | -0.020422 | `-0.028934` à `-0.010418` |
| `V16-CANDIDATE-008` | `abs_class_from_previous(v3)=0` | -0.018910 | `-0.027079` à `-0.011091` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.018151 | `-0.000523` à `+0.038926` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | -0.128010 | `-0.161961` à `-0.098665` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.094614 | `-0.185196` à `-0.010631` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.087664 | `+0.065401` à `+0.110748` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.086824 | `-0.150691` à `-0.023201` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | +0.069005 | `+0.043911` à `+0.096998` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | +0.055260 | `+0.042469` à `+0.069508` |
| `LEARNED-028` | `central_pair_abs_class(v1,v0)=5` | +0.050642 | `+0.018359` à `+0.090894` |
| `LEARNED-027` | `central_pair_abs_class(v0,v1)=5` | +0.039993 | `+0.015072` à `+0.069879` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | +0.130949 | `+0.081579` à `+0.184716` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.118031 | `+0.006819` à `+0.244505` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.085793 | `-0.136151` à `-0.040496` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.076313 | `-0.108999` à `-0.039039` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.062152 | `-0.089036` à `-0.033591` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.060083 | `-0.083849` à `-0.036044` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.058324 | `-0.044040` à `+0.159306` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.056187 | `-0.036971` à `+0.159647` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | +0.296476 | `+0.217193` à `+0.384866` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.266266 | `+0.117471` à `+0.426256` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.190054 | `-0.256017` à `-0.121871` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.139718 | `-0.319530` à `+0.033442` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.129734 | `-0.088378` à `+0.355916` |
| `LEARNED-028` | `central_pair_abs_class(v1,v0)=5` | -0.113645 | `-0.223466` à `-0.021328` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | +0.109336 | `+0.062537` à `+0.164625` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.104535 | `-0.171962` à `-0.042751` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | +0.260810 | `+0.171075` à `+0.351187` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.163068 | `-0.067175` à `+0.410990` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.134396 | `-0.237273` à `-0.031271` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.128865 | `-0.181879` à `-0.080389` |
| `LEARNED-021` | `central_pair_abs_class(v0,v1)=2` | +0.106702 | `+0.074296` à `+0.141107` |
| `LEARNED-028` | `central_pair_abs_class(v1,v0)=5` | -0.105215 | `-0.176120` à `-0.032723` |
| `V16-CANDIDATE-009` | `any_pair_arrival_abs_class_same_sign(all_voices)=10` | +0.102814 | `+0.053038` à `+0.159288` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.102666 | `-0.085917` à `+0.288750` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.036993 | `-0.084182` à `+0.003357` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.029797 | `+0.021342` à `+0.041465` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.016933 | `-0.016155` à `+0.051238` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.016303 | `-0.036166` à `+0.003545` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.013392 | `-0.010194` à `+0.035443` |
| `LEARNED-028` | `central_pair_abs_class(v1,v0)=5` | +0.013165 | `-0.000181` à `+0.029172` |
| `V16-CANDIDATE-006` | `central_pair_abs_class(v0,v3)=3` | -0.011808 | `-0.022092` à `-0.002153` |
| `V16-CANDIDATE-010` | `central_pair_abs_class(v3,v0)=3` | -0.011545 | `-0.024390` à `-0.001304` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.040291 | `+0.027437` à `+0.057626` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.034092 | `-0.062576` à `-0.007577` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | -0.021510 | `-0.061830` à `+0.020751` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.018519 | `-0.003886` à `+0.042230` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.014097 | `-0.051326` à `+0.025297` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.014006 | `-0.031479` à `-0.001468` |
| `LEARNED-028` | `central_pair_abs_class(v1,v0)=5` | -0.013174 | `-0.038466` à `+0.005825` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | +0.012816 | `-0.002505` à `+0.025872` |
