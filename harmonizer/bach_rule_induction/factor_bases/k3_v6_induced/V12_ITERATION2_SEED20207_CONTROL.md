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
- Temps d'échantillonnage : `115.910` secondes.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 24.983 | 32.569 | -7.586 pp | `-10.453` à `-4.736` |
| Répétitions de basse | 4.938 | 4.155 | +0.783 pp | `-0.487` à `+2.137` |
| Sauts de basse > 4 demi-tons | 26.917 | 24.805 | +2.112 pp | `-0.433` à `+4.552` |
| Basse hors gamme naturelle globale | 9.094 | 13.716 | -4.622 pp | `-6.248` à `-3.074` |
| Blocs triadiques | 53.875 | 52.804 | +1.071 pp | `-1.163` à `+3.132` |
| Blocs forts non triadiques | 29.598 | 36.076 | -6.478 pp | `-10.735` à `-2.303` |
| Dissonances par bloc faible | 0.892 | 0.900 | -0.008 | `-0.065` à `+0.047` |
| Dissonances par bloc fort | 0.406 | 0.536 | -0.130 | `-0.195` à `-0.060` |
| {0,3,6,8} sur bloc fort | 1.762 | 2.778 | -1.016 pp | `-2.132` à `+0.209` |
| {0,3,6,8} sur bloc faible | 4.225 | 3.641 | +0.584 pp | `-0.573` à `+1.844` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000124`.
- Plus grand déplacement proposé : `0.499236`.
- Structure localement contrôlable : `true`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.269853 | `+0.190455` à `+0.354296` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.100614 | `-0.188289` à `-0.010109` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | +0.077548 | `+0.037992` à `+0.118118` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.060961 | `-0.096637` à `-0.020181` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.050514 | `-0.079405` à `-0.025346` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.048543 | `-0.002412` à `+0.103960` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.036032 | `-0.076460` à `+0.010902` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.026264 | `-0.022280` à `+0.072560` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.044559 | `-0.075841` à `-0.011662` |
| `LEARNED-010` | `attacked_repeat_from_previous(v3)` | +0.035561 | `+0.028070` à `+0.043393` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | -0.013985 | `-0.026153` à `-0.001876` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.013484 | `-0.033417` à `+0.005776` |
| `LEARNED-005` | `central_bass_pcset(all_voices)=265` | +0.012434 | `+0.001995` à `+0.023578` |
| `LEARNED-023` | `abs_step_to_next_gt(v2)=1` | +0.011477 | `-0.000492` à `+0.022098` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.009399 | `+0.000185` à `+0.018629` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.009288 | `-0.026342` à `+0.007277` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.219583 | `+0.126430` à `+0.334264` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.139382 | `+0.089528` à `+0.198676` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.133150 | `-0.235879` à `-0.059760` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | -0.059291 | `-0.095435` à `-0.026769` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | -0.042663 | `-0.092423` à `+0.011501` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | -0.039910 | `-0.069644` à `-0.013569` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.035785 | `-0.104006` à `+0.024493` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.030451 | `+0.003783` à `+0.062377` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.133731 | `+0.083738` à `+0.190451` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | +0.028309 | `+0.002316` à `+0.054644` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.027595 | `-0.050132` à `-0.007451` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.027438 | `-0.009847` à `+0.069502` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.021212 | `-0.047758` à `+0.007533` |
| `LEARNED-013` | `any_pair_central_abs_class(all_voices)=1` | +0.019131 | `+0.003974` à `+0.034892` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.017480 | `-0.047950` à `+0.013069` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.014665 | `-0.012878` à `+0.044278` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.110184 | `-0.168828` à `-0.055281` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | -0.102150 | `-0.138338` à `-0.066778` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.091364 | `+0.058352` à `+0.123042` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.066010 | `+0.017859` à `+0.121963` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | +0.053557 | `+0.024343` à `+0.083495` |
| `LEARNED-005` | `central_bass_pcset(all_voices)=265` | +0.043020 | `+0.026709` à `+0.059485` |
| `LEARNED-013` | `any_pair_central_abs_class(all_voices)=1` | -0.041308 | `-0.062778` à `-0.019792` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | -0.038020 | `-0.059237` à `-0.018895` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.139283 | `+0.074207` à `+0.216358` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.121055 | `+0.009998` à `+0.235846` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.111456 | `-0.171500` à `-0.057846` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.097133 | `-0.149822` à `-0.050860` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.091116 | `+0.040414` à `+0.142725` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.068899 | `-0.154870` à `+0.026972` |
| `LEARNED-013` | `any_pair_central_abs_class(all_voices)=1` | +0.057633 | `+0.018109` à `+0.101752` |
| `LEARNED-005` | `central_bass_pcset(all_voices)=265` | -0.045409 | `-0.070328` à `-0.020902` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.205557 | `+0.070205` à `+0.351019` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.194156 | `+0.104098` à `+0.295851` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.164817 | `-0.238028` à `-0.089311` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.155988 | `-0.314793` à `-0.004358` |
| `LEARNED-013` | `any_pair_central_abs_class(all_voices)=1` | +0.105137 | `+0.059812` à `+0.154860` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | +0.094360 | `+0.021516` à `+0.169284` |
| `LEARNED-005` | `central_bass_pcset(all_voices)=265` | -0.076082 | `-0.115653` à `-0.037771` |
| `LEARNED-023` | `abs_step_to_next_gt(v2)=1` | +0.073567 | `+0.012123` à `+0.135847` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.255310 | `+0.153835` à `+0.388766` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.225372 | `-0.313035` à `-0.136967` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.192058 | `-0.362415` à `-0.018335` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.163275 | `-0.265826` à `-0.073194` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.152759 | `+0.047702` à `+0.257807` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.140046 | `-0.048171` à `+0.319367` |
| `LEARNED-013` | `any_pair_central_abs_class(all_voices)=1` | +0.109269 | `+0.051261` à `+0.173078` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | +0.092401 | `+0.030217` à `+0.156373` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.022533 | `+0.015306` à `+0.030350` |
| `LEARNED-030` | `abs_step_to_next_gt(v1)=1` | +0.020536 | `+0.005291` à `+0.034112` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.019568 | `-0.000782` à `+0.039798` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.014695 | `-0.034256` à `+0.003851` |
| `LEARNED-023` | `abs_step_to_next_gt(v2)=1` | +0.012324 | `-0.001483` à `+0.026116` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.011915 | `-0.004041` à `+0.033816` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.011230 | `-0.039744` à `+0.018753` |
| `LEARNED-025` | `central_pair_abs_class(v3,v2)=6` | +0.010130 | `+0.003353` à `+0.016904` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.031076 | `+0.022569` à `+0.042344` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.018277 | `-0.009482` à `+0.047629` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | +0.013410 | `-0.004739` à `+0.032993` |
| `LEARNED-005` | `central_bass_pcset(all_voices)=265` | -0.011258 | `-0.022300` à `-0.000497` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.010284 | `-0.025243` à `+0.004572` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.010033 | `-0.007636` à `+0.027220` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | -0.008238 | `-0.025663` à `+0.009590` |
| `LEARNED-012` | `any_pair_central_abs_class(all_voices)=11` | -0.008186 | `-0.017691` à `+0.000628` |
