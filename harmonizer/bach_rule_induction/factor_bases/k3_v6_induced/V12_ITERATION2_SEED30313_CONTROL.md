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
- Temps d'échantillonnage : `115.701` secondes.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 24.983 | 32.526 | -7.543 pp | `-10.408` à `-4.777` |
| Répétitions de basse | 4.938 | 4.164 | +0.775 pp | `-0.480` à `+2.239` |
| Sauts de basse > 4 demi-tons | 26.917 | 24.496 | +2.421 pp | `+0.269` à `+4.611` |
| Basse hors gamme naturelle globale | 9.094 | 13.693 | -4.599 pp | `-6.561` à `-2.722` |
| Blocs triadiques | 53.875 | 53.426 | +0.450 pp | `-1.757` à `+2.736` |
| Blocs forts non triadiques | 29.598 | 35.619 | -6.021 pp | `-10.875` à `-1.724` |
| Dissonances par bloc faible | 0.892 | 0.881 | +0.011 | `-0.038` à `+0.060` |
| Dissonances par bloc fort | 0.406 | 0.529 | -0.122 | `-0.198` à `-0.056` |
| {0,3,6,8} sur bloc fort | 1.762 | 2.936 | -1.174 pp | `-2.204` à `+0.037` |
| {0,3,6,8} sur bloc faible | 4.225 | 3.952 | +0.273 pp | `-0.982` à `+1.506` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000154`.
- Plus grand déplacement proposé : `0.524022`.
- Structure localement contrôlable : `true`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.249864 | `+0.175306` à `+0.327331` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.187271 | `-0.273863` à `-0.109865` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.065842 | `-0.111798` à `-0.016582` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.054748 | `+0.003861` à `+0.114904` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.038736 | `-0.062740` à `-0.015227` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.032082 | `-0.006210` à `+0.076668` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.021721 | `+0.004886` à `+0.041269` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | +0.020629 | `-0.002018` à `+0.044408` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-010` | `attacked_repeat_from_previous(v3)` | +0.029559 | `+0.024421` à `+0.035224` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.023923 | `-0.060840` à `+0.010835` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.012276 | `-0.028481` à `+0.002987` |
| `LEARNED-023` | `abs_step_to_next_gt(v2)=1` | +0.010009 | `+0.000218` à `+0.019917` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.009010 | `-0.023350` à `+0.005810` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.006889 | `-0.023439` à `+0.009789` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.006841 | `-0.003803` à `+0.018056` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.005963 | `-0.009805` à `+0.021854` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.263391 | `+0.155616` à `+0.389272` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.130860 | `-0.216377` à `-0.056348` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.122961 | `+0.086834` à `+0.163324` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.100019 | `-0.172042` à `-0.042340` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.028047 | `-0.001119` à `+0.059673` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | -0.025765 | `-0.057060` à `+0.002064` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | -0.024873 | `-0.049654` à `+0.000289` |
| `LEARNED-013` | `any_pair_central_abs_class(all_voices)=1` | -0.018440 | `-0.043710` à `+0.007109` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.112988 | `+0.072684` à `+0.155049` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.025401 | `+0.001134` à `+0.048875` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.021745 | `-0.062576` à `+0.022441` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.020498 | `-0.050580` à `+0.006918` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.018549 | `-0.041995` à `+0.008222` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | +0.013982 | `-0.007899` à `+0.039055` |
| `LEARNED-030` | `abs_step_to_next_gt(v1)=1` | +0.011219 | `-0.002230` à `+0.025513` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.010678 | `-0.020920` à `+0.040707` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | -0.105810 | `-0.143595` à `-0.065783` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.081470 | `+0.052731` à `+0.110106` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | +0.062646 | `+0.039227` à `+0.087787` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | -0.044655 | `-0.066585` à `-0.024023` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.033789 | `-0.042544` à `+0.106587` |
| `LEARNED-005` | `central_bass_pcset(all_voices)=265` | +0.028452 | `+0.010212` à `+0.049020` |
| `LEARNED-013` | `any_pair_central_abs_class(all_voices)=1` | -0.025965 | `-0.052490` à `-0.002048` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.023845 | `-0.094481` à `+0.049266` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.129487 | `+0.070419` à `+0.192902` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.078986 | `-0.133507` à `-0.030035` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.074674 | `-0.111943` à `-0.040426` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.060391 | `-0.136402` à `+0.022850` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.053969 | `-0.186714` à `+0.067108` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | +0.045367 | `+0.012171` à `+0.075316` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | +0.038362 | `-0.008472` à `+0.086741` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.037138 | `-0.029434` à `+0.103331` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.171199 | `+0.071138` à `+0.288143` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.160064 | `+0.018467` à `+0.302762` |
| `LEARNED-012` | `any_pair_central_abs_class(all_voices)=11` | +0.103127 | `+0.059915` à `+0.152507` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.095357 | `-0.285482` à `+0.086123` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.094635 | `-0.150248` à `-0.042989` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.091257 | `-0.154982` à `-0.032243` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.080513 | `-0.160606` à `+0.004729` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | +0.078030 | `+0.040649` à `+0.120774` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.196765 | `+0.093825` à `+0.313255` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.125393 | `-0.305671` à `+0.071421` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.119471 | `-0.225805` à `-0.021632` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.100061 | `-0.222091` à `+0.013087` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.076520 | `-0.129532` à `-0.025092` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | +0.069618 | `+0.013226` à `+0.124924` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | +0.065389 | `-0.003974` à `+0.143492` |
| `LEARNED-023` | `abs_step_to_next_gt(v2)=1` | +0.060949 | `+0.003451` à `+0.122400` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.039883 | `+0.001376` à `+0.085325` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.028861 | `-0.072986` à `+0.005957` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.028488 | `-0.050496` à `-0.008331` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.023210 | `+0.014510` à `+0.032731` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.022954 | `-0.005402` à `+0.054188` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | +0.016683 | `-0.001727` à `+0.036762` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.015599 | `-0.001391` à `+0.037850` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.012943 | `-0.009294` à `+0.035809` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.035808 | `+0.027804` à `+0.045376` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.034850 | `+0.004772` à `+0.063869` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.030603 | `+0.016449` à `+0.046798` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.024265 | `-0.058339` à `+0.012441` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | +0.016377 | `-0.001599` à `+0.032117` |
| `LEARNED-023` | `abs_step_to_next_gt(v2)=1` | -0.011816 | `-0.026413` à `+0.001047` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | -0.009490 | `-0.018987` à `+0.000140` |
| `LEARNED-013` | `any_pair_central_abs_class(all_voices)=1` | -0.008313 | `-0.017678` à `+0.001103` |
