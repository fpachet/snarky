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
- Temps d'échantillonnage : `686.938` secondes.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 24.983 | 28.906 | -3.924 pp | `-6.168` à `-1.792` |
| Répétitions de basse | 4.938 | 4.435 | +0.503 pp | `-0.783` à `+1.918` |
| Sauts de basse > 4 demi-tons | 26.917 | 27.525 | -0.608 pp | `-2.719` à `+1.543` |
| Basse hors gamme naturelle globale | 9.094 | 13.611 | -4.517 pp | `-6.124` à `-2.948` |
| Blocs triadiques | 53.875 | 51.802 | +2.073 pp | `+0.086` à `+4.061` |
| Blocs forts non triadiques | 29.598 | 39.654 | -10.056 pp | `-14.351` à `-6.303` |
| Dissonances par bloc faible | 0.892 | 0.913 | -0.021 | `-0.067` à `+0.026` |
| Dissonances par bloc fort | 0.406 | 0.601 | -0.195 | `-0.259` à `-0.134` |
| {0,3,6,8} sur bloc fort | 1.762 | 2.780 | -1.017 pp | `-2.011` à `+0.103` |
| {0,3,6,8} sur bloc faible | 4.225 | 3.592 | +0.633 pp | `-0.448` à `+1.843` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000383`.
- Plus grand déplacement proposé : `0.679000`.
- Structure localement contrôlable : `true`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.287437 | `+0.224263` à `+0.344566` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.204657 | `-0.296635` à `-0.107801` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.087294 | `-0.180949` à `-0.011543` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | -0.080836 | `-0.176994` à `-0.003012` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.073912 | `-0.117703` à `-0.031433` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.040276 | `-0.061724` à `-0.017038` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.031489 | `-0.006088` à `+0.066744` |
| `LEARNED-005` | `any_pair_central_abs_class_target_passing_metric(all_voices)=9,0` | +0.029187 | `+0.004840` à `+0.053971` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-011` | `attacked_repeat_from_previous(v3)` | +0.045794 | `+0.038684` à `+0.053277` |
| `V16-CANDIDATE-008` | `abs_class_from_previous(v3)=0` | +0.043871 | `+0.035869` à `+0.052299` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.012544 | `-0.040171` à `+0.017287` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.010564 | `+0.002097` à `+0.018833` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.009844 | `-0.035627` à `+0.016138` |
| `V16-CANDIDATE-005` | `any_voice_three_block_sign_shape(all_voices)=0,-1` | +0.009024 | `+0.001207` à `+0.017115` |
| `V16-CANDIDATE-012` | `any_voice_adjacent_abs_class(all_voices)=6` | -0.008246 | `-0.019166` à `+0.001957` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.007164 | `-0.024302` à `+0.009547` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.383982 | `+0.275942` à `+0.509619` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.232569 | `+0.113395` à `+0.385149` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.223672 | `-0.312079` à `-0.140797` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.220291 | `+0.120100` à `+0.360967` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.191366 | `+0.128908` à `+0.262292` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.056282 | `-0.100142` à `-0.015119` |
| `LEARNED-029` | `any_voice_adjacent_step_gt(all_voices)=12` | +0.047658 | `+0.027754` à `+0.070087` |
| `LEARNED-005` | `any_pair_central_abs_class_target_passing_metric(all_voices)=9,0` | -0.047242 | `-0.072115` à `-0.025225` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.127115 | `+0.091953` à `+0.160792` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.053262 | `-0.092080` à `-0.014702` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.028298 | `+0.007327` à `+0.047450` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | +0.020829 | `+0.000014` à `+0.041264` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.019655 | `-0.036852` à `+0.000601` |
| `LEARNED-013` | `any_pair_central_abs_class(all_voices)=1` | +0.017182 | `+0.005170` à `+0.028032` |
| `V16-CANDIDATE-012` | `any_voice_adjacent_abs_class(all_voices)=6` | +0.014919 | `+0.003080` à `+0.026765` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.014492 | `+0.006990` à `+0.021578` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.119620 | `+0.089777` à `+0.153322` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | -0.114155 | `-0.144130` à `-0.084943` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.076498 | `-0.133871` à `-0.025041` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | +0.059296 | `+0.043762` à `+0.075783` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.053863 | `-0.127789` à `+0.021323` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | +0.045370 | `+0.030220` à `+0.061758` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.044289 | `-0.028709` à `+0.124423` |
| `V16-CANDIDATE-009` | `any_pair_arrival_abs_class_same_sign(all_voices)=10` | -0.042016 | `-0.057099` à `-0.026455` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.103502 | `-0.145001` à `-0.066486` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | +0.084601 | `+0.033689` à `+0.134547` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.073891 | `-0.069353` à `+0.216232` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.059999 | `-0.083557` à `-0.036568` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.058408 | `-0.081394` à `+0.197640` |
| `LEARNED-013` | `any_pair_central_abs_class(all_voices)=1` | +0.056467 | `+0.019488` à `+0.091282` |
| `LEARNED-014` | `any_pair_central_abs_class(all_voices)=11` | +0.039696 | `+0.018620` à `+0.061752` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.038331 | `-0.176226` à `+0.103388` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | +0.289330 | `+0.219977` à `+0.363796` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.258355 | `+0.131183` à `+0.380301` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.205561 | `-0.285484` à `-0.133681` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.169883 | `-0.024172` à `+0.375160` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.116210 | `-0.153979` à `-0.080509` |
| `V16-CANDIDATE-009` | `any_pair_arrival_abs_class_same_sign(all_voices)=10` | +0.104147 | `+0.061439` à `+0.151934` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | +0.103925 | `+0.068597` à `+0.139874` |
| `LEARNED-013` | `any_pair_central_abs_class(all_voices)=1` | +0.092563 | `+0.041153` à `+0.153993` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.168691 | `-0.442311` à `+0.108135` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | +0.162173 | `+0.062004` à `+0.266461` |
| `LEARNED-013` | `any_pair_central_abs_class(all_voices)=1` | +0.150221 | `+0.079915` à `+0.217307` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.142415 | `-0.027819` à `+0.286683` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.129859 | `-0.214548` à `-0.053526` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.114303 | `-0.153174` à `-0.072312` |
| `LEARNED-016` | `any_pair_arrival_abs_class_same_sign(all_voices)=2` | +0.078649 | `+0.039915` à `+0.117347` |
| `LEARNED-014` | `any_pair_central_abs_class(all_voices)=11` | +0.073167 | `+0.027576` à `+0.128632` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.063308 | `-0.137305` à `-0.007038` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | -0.060931 | `-0.146936` à `+0.003992` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.043072 | `-0.127549` à `+0.029077` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.035719 | `+0.015034` à `+0.057704` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.031721 | `+0.023156` à `+0.041605` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.025016 | `-0.004657` à `+0.058893` |
| `LEARNED-023` | `central_pair_abs_class(v3,v2)=6` | +0.014817 | `+0.009621` à `+0.020798` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | -0.013230 | `-0.033023` à `+0.003694` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.040270 | `+0.033052` à `+0.049236` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.026269 | `-0.001650` à `+0.056829` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.025422 | `-0.003808` à `+0.054577` |
| `LEARNED-028` | `central_pair_abs_class(v1,v0)=5` | -0.010174 | `-0.019435` à `-0.001409` |
| `LEARNED-023` | `central_pair_abs_class(v3,v2)=6` | +0.008465 | `+0.004335` à `+0.012659` |
| `V16-CANDIDATE-012` | `any_voice_adjacent_abs_class(all_voices)=6` | +0.008226 | `+0.000596` à `+0.016020` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.007583 | `-0.018659` à `+0.002791` |
| `LEARNED-025` | `abs_step_to_next_gt(v2)=1` | -0.007011 | `-0.019572` à `+0.005280` |
