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
- Chaînes restaurées : `0/32`.
- Cache issu des mêmes poids : `None`.
- Temps d'échantillonnage : `75.861` secondes.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 24.983 | 31.460 | -6.477 pp | `-8.888` à `-3.974` |
| Répétitions de basse | 4.938 | 4.520 | +0.418 pp | `-0.710` à `+1.598` |
| Sauts de basse > 4 demi-tons | 26.917 | 25.595 | +1.322 pp | `-0.789` à `+3.472` |
| Basse hors gamme naturelle globale | 9.094 | 14.032 | -4.939 pp | `-6.899` à `-2.993` |
| Blocs triadiques | 53.875 | 52.482 | +1.394 pp | `-0.720` à `+3.739` |
| Blocs forts non triadiques | 29.598 | 37.883 | -8.285 pp | `-12.641` à `-4.085` |
| Dissonances par bloc faible | 0.892 | 0.909 | -0.017 | `-0.073` à `+0.041` |
| Dissonances par bloc fort | 0.406 | 0.572 | -0.166 | `-0.231` à `-0.101` |
| {0,3,6,8} sur bloc fort | 1.762 | 2.604 | -0.841 pp | `-1.854` à `+0.430` |
| {0,3,6,8} sur bloc faible | 4.225 | 3.247 | +0.978 pp | `-0.097` à `+2.079` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000392`.
- Plus grand déplacement proposé : `0.688701`.
- Structure localement contrôlable : `true`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.334246 | `+0.216699` à `+0.456633` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.248915 | `-0.383579` à `-0.136437` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.101990 | `-0.186881` à `-0.022212` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.064884 | `-0.135718` à `-0.006015` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | +0.054300 | `+0.024003` à `+0.083479` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | -0.054015 | `-0.136714` à `+0.020738` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.053329 | `+0.004706` à `+0.104923` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.039281 | `-0.084165` à `+0.008614` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.046074 | `-0.091938` à `+0.001374` |
| `LEARNED-010` | `attacked_repeat_from_previous(v3)` | +0.041800 | `+0.033531` à `+0.049295` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.025559 | `-0.029409` à `+0.081917` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | -0.024840 | `-0.043106` à `-0.004883` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | -0.024265 | `-0.052692` à `+0.002276` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | -0.023275 | `-0.039444` à `-0.008364` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.023240 | `-0.051838` à `-0.001756` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.018058 | `-0.024988` à `+0.065814` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.232691 | `+0.126780` à `+0.367524` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.197610 | `-0.335910` à `-0.083232` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.158267 | `+0.100015` à `+0.219067` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.112252 | `+0.029651` à `+0.209893` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.102604 | `+0.023981` à `+0.190545` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | -0.037546 | `-0.074886` à `-0.002971` |
| `LEARNED-028` | `any_voice_adjacent_step_gt(all_voices)=12` | +0.035074 | `+0.018029` à `+0.055821` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | -0.027562 | `-0.065033` à `+0.003302` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.164847 | `+0.103148` à `+0.228105` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.068432 | `-0.135637` à `-0.002715` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.037555 | `+0.006489` à `+0.072598` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | +0.024949 | `+0.003943` à `+0.047979` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.023298 | `+0.013759` à `+0.033791` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.019158 | `-0.043268` à `+0.002809` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | +0.017639 | `-0.002727` à `+0.038153` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.016369 | `-0.043747` à `+0.070955` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.095062 | `+0.065352` à `+0.127831` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | -0.087125 | `-0.134059` à `-0.048796` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.083529 | `-0.159372` à `-0.011039` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.061897 | `-0.006472` à `+0.132306` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | -0.037890 | `-0.061091` à `-0.018558` |
| `LEARNED-012` | `any_pair_central_abs_class(all_voices)=11` | -0.027128 | `-0.041478` à `-0.014211` |
| `LEARNED-005` | `central_bass_pcset(all_voices)=265` | +0.025411 | `+0.007790` à `+0.043346` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | -0.024128 | `-0.051154` à `+0.007269` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.107719 | `-0.146532` à `-0.064898` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.096247 | `+0.038973` à `+0.151830` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.069655 | `-0.056275` à `+0.177979` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.052778 | `-0.183297` à `+0.085287` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.048522 | `-0.116894` à `+0.013913` |
| `LEARNED-012` | `any_pair_central_abs_class(all_voices)=11` | +0.047053 | `+0.016246` à `+0.078290` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.038732 | `-0.068912` à `+0.149353` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | +0.029176 | `-0.013818` à `+0.066949` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.310093 | `+0.188694` à `+0.447441` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.273107 | `+0.065367` à `+0.485239` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.182651 | `-0.405933` à `+0.075328` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.152143 | `-0.228288` à `-0.077933` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | +0.144124 | `+0.066089` à `+0.225711` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.141283 | `-0.380168` à `+0.091755` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.138026 | `-0.253119` à `-0.009485` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | -0.098561 | `-0.302844` à `+0.077709` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.196303 | `+0.102478` à `+0.298203` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.107392 | `-0.091527` à `+0.298894` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.105372 | `-0.189851` à `-0.030452` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.104951 | `-0.255802` à `+0.016700` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.083509 | `-0.162939` à `+0.306062` |
| `LEARNED-030` | `abs_step_to_next_gt(v1)=1` | +0.073267 | `-0.003884` à `+0.162384` |
| `LEARNED-012` | `any_pair_central_abs_class(all_voices)=11` | +0.071088 | `+0.019273` à `+0.124292` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | +0.070187 | `-0.022185` à `+0.169796` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.026466 | `+0.018348` à `+0.036988` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.020827 | `-0.075588` à `+0.029192` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.019394 | `-0.021055` à `+0.063966` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.017265 | `-0.069191` à `+0.018430` |
| `LEARNED-005` | `central_bass_pcset(all_voices)=265` | -0.014924 | `-0.024686` à `-0.005368` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.014168 | `-0.030559` à `+0.055391` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | +0.009069 | `-0.010712` à `+0.031805` |
| `LEARNED-012` | `any_pair_central_abs_class(all_voices)=11` | +0.009009 | `-0.002825` à `+0.021930` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.034684 | `+0.005957` à `+0.065381` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.030828 | `+0.022192` à `+0.041165` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.020159 | `-0.032690` à `-0.009265` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.016436 | `-0.046453` à `+0.012559` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.015848 | `-0.003118` à `+0.035371` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | +0.013150 | `+0.001494` à `+0.024356` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | +0.010266 | `-0.009190` à `+0.029967` |
| `LEARNED-010` | `attacked_repeat_from_previous(v3)` | -0.008014 | `-0.013563` à `-0.003269` |
