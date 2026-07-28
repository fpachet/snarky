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
- Temps d'échantillonnage : `141.736` secondes.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 24.983 | 26.118 | -1.136 pp | `-3.729` à `+1.452` |
| Répétitions de basse | 4.938 | 4.757 | +0.181 pp | `-1.091` à `+1.655` |
| Sauts de basse > 4 demi-tons | 26.917 | 27.119 | -0.202 pp | `-2.234` à `+1.721` |
| Basse hors gamme naturelle globale | 9.094 | 10.404 | -1.310 pp | `-3.460` à `+0.941` |
| Blocs triadiques | 53.875 | 52.433 | +1.442 pp | `-0.976` à `+3.705` |
| Blocs forts non triadiques | 29.598 | 30.143 | -0.544 pp | `-4.693` à `+3.187` |
| Dissonances par bloc faible | 0.892 | 0.920 | -0.028 | `-0.081` à `+0.036` |
| Dissonances par bloc fort | 0.406 | 0.435 | -0.028 | `-0.091` à `+0.032` |
| {0,3,6,8} sur bloc fort | 1.762 | 2.226 | -0.464 pp | `-1.660` à `+0.867` |
| {0,3,6,8} sur bloc faible | 4.225 | 4.633 | -0.408 pp | `-1.673` à `+0.859` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000137`.
- Plus grand déplacement proposé : `0.183508`.
- Structure localement contrôlable : `true`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.211442 | `+0.170026` à `+0.256691` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.116509 | `-0.161021` à `-0.078634` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.061083 | `-0.099779` à `-0.020148` |
| `F-K3-V6-014` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.033591 | `-0.048136` à `-0.019419` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.025025 | `-0.043077` à `-0.005856` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | +0.021635 | `+0.009039` à `+0.034882` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.020028 | `-0.000598` à `+0.042612` |
| `F-K3-V6-019` | `attacked_repeat_from_previous(v3)` | -0.016152 | `-0.023856` à `-0.008105` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-019` | `attacked_repeat_from_previous(v3)` | +0.041600 | `+0.035908` à `+0.047585` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.024927 | `-0.039561` à `-0.010214` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.018244 | `-0.033818` à `-0.001902` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | -0.015272 | `-0.024172` à `-0.006526` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.007493 | `-0.001243` à `+0.015522` |
| `F-K3-V6-029` | `central_tonic_pcset(all_voices)=2180` | +0.006694 | `+0.001754` à `+0.012503` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | +0.005751 | `-0.003577` à `+0.014527` |
| `F-K3-V6-018` | `previous_ordered_gap_le(v0,v1)=2` | +0.005678 | `-0.001403` à `+0.012273` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.161706 | `+0.119731` à `+0.205018` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.131464 | `-0.178045` à `-0.089101` |
| `F-K3-V6-014` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.086796 | `+0.071305` à `+0.104265` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.077265 | `-0.120311` à `-0.034121` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.025141 | `-0.048809` à `-0.005625` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | +0.023477 | `-0.000252` à `+0.045752` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | -0.019414 | `-0.041312` à `-0.000284` |
| `F-K3-V6-019` | `attacked_repeat_from_previous(v3)` | -0.016902 | `-0.025962` à `-0.008171` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.063643 | `+0.041797` à `+0.086528` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.020849 | `+0.007876` à `+0.032089` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.017959 | `-0.045483` à `+0.006252` |
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.012640 | `+0.007416` à `+0.017530` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | +0.010415 | `+0.003549` à `+0.017907` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | +0.010388 | `-0.000076` à `+0.021966` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.010073 | `-0.002133` à `+0.022321` |
| `F-K3-V6-014` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.007927 | `-0.015078` à `+0.000830` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | -0.122496 | `-0.148237` à `-0.095876` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.081438 | `-0.119426` à `-0.043723` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | +0.080277 | `+0.066733` à `+0.094132` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | -0.078046 | `-0.093249` à `-0.063813` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | +0.065538 | `+0.053897` à `+0.077087` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.059623 | `+0.025510` à `+0.094164` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | +0.053142 | `+0.038851` à `+0.066876` |
| `F-K3-V6-004` | `central_bass_pcset(all_voices)=265` | +0.038731 | `+0.024045` à `+0.054670` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.137205 | `+0.095543` à `+0.182745` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.073668 | `+0.015485` à `+0.127633` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.070644 | `+0.044463` à `+0.097968` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.066798 | `-0.096600` à `-0.038336` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.066681 | `-0.089020` à `-0.045489` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.054433 | `-0.103222` à `-0.005075` |
| `F-K3-V6-004` | `central_bass_pcset(all_voices)=265` | -0.032559 | `-0.057165` à `-0.008589` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | +0.027014 | `+0.006782` à `+0.050656` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.304245 | `+0.216844` à `+0.387973` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.276308 | `+0.162584` à `+0.395537` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.255509 | `-0.361245` à `-0.164899` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.181657 | `+0.137344` à `+0.225334` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | -0.164011 | `-0.200792` à `-0.128643` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.156686 | `-0.201193` à `-0.114469` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | +0.106609 | `-0.023248` à `+0.224892` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | +0.097168 | `+0.066931` à `+0.130097` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.287898 | `+0.208957` à `+0.375369` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.208280 | `+0.105001` à `+0.310897` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.126420 | `+0.077013` à `+0.178517` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.114153 | `-0.213561` à `-0.010174` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.110482 | `-0.174179` à `-0.051277` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.094903 | `-0.139628` à `-0.050111` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | +0.070005 | `+0.028294` à `+0.114328` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.069541 | `-0.188834` à `+0.056589` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.028401 | `+0.015259` à `+0.044862` |
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.021918 | `+0.017323` à `+0.027022` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.014578 | `-0.034469` à `+0.004860` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.008674 | `-0.012534` à `+0.032150` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.007115 | `-0.016424` à `+0.001374` |
| `F-K3-V6-004` | `central_bass_pcset(all_voices)=265` | -0.006884 | `-0.013849` à `-0.000205` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | -0.006709 | `-0.014068` à `-0.000163` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | -0.006204 | `-0.015559` à `+0.003965` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.038691 | `+0.031550` à `+0.046137` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.019244 | `+0.006376` à `+0.032090` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.013768 | `+0.002460` à `+0.025469` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | +0.012565 | `-0.012565` à `+0.040686` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | -0.012115 | `-0.018411` à `-0.006038` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.009737 | `-0.007121` à `+0.025494` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.009249 | `-0.017934` à `-0.001428` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.007299 | `-0.005801` à `+0.021430` |
