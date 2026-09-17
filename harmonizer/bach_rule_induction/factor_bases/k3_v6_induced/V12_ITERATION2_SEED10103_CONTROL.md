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
- Temps d'échantillonnage : `116.315` secondes.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 24.983 | 31.109 | -6.126 pp | `-9.118` à `-3.243` |
| Répétitions de basse | 4.938 | 4.063 | +0.875 pp | `-0.346` à `+2.218` |
| Sauts de basse > 4 demi-tons | 26.917 | 26.015 | +0.902 pp | `-1.310` à `+2.805` |
| Basse hors gamme naturelle globale | 9.094 | 13.766 | -4.672 pp | `-6.183` à `-3.068` |
| Blocs triadiques | 53.875 | 53.064 | +0.811 pp | `-1.550` à `+3.314` |
| Blocs forts non triadiques | 29.598 | 36.764 | -7.166 pp | `-12.115` à `-2.505` |
| Dissonances par bloc faible | 0.892 | 0.876 | +0.016 | `-0.029` à `+0.060` |
| Dissonances par bloc fort | 0.406 | 0.545 | -0.139 | `-0.212` à `-0.075` |
| {0,3,6,8} sur bloc fort | 1.762 | 2.528 | -0.766 pp | `-1.789` à `+0.446` |
| {0,3,6,8} sur bloc faible | 4.225 | 3.244 | +0.981 pp | `-0.118` à `+2.174` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000128`.
- Plus grand déplacement proposé : `0.623544`.
- Structure localement contrôlable : `true`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.214614 | `+0.157359` à `+0.268837` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.183907 | `-0.269067` à `-0.107977` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.065583 | `+0.018593` à `+0.113429` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.037337 | `-0.066287` à `-0.006660` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.028200 | `-0.074783` à `+0.017950` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.027323 | `-0.053622` à `-0.000347` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.023643 | `-0.023187` à `+0.071855` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | +0.022357 | `-0.010398` à `+0.052460` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-010` | `attacked_repeat_from_previous(v3)` | +0.038471 | `+0.030017` à `+0.048296` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.011080 | `-0.032228` à `+0.010193` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.007703 | `-0.009336` à `+0.027370` |
| `LEARNED-023` | `abs_step_to_next_gt(v2)=1` | -0.007264 | `-0.019956` à `+0.005531` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | +0.006596 | `-0.010671` à `+0.025744` |
| `LEARNED-030` | `abs_step_to_next_gt(v1)=1` | +0.006460 | `-0.003469` à `+0.016392` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.004782 | `-0.038361` à `+0.030753` |
| `LEARNED-019` | `central_pair_abs_class(v3,v1)=6` | -0.004510 | `-0.009953` à `+0.000045` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.210303 | `+0.123451` à `+0.309866` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.186975 | `-0.269135` à `-0.112075` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.080489 | `+0.042030` à `+0.125004` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.057361 | `-0.116096` à `-0.002127` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | -0.045248 | `-0.070860` à `-0.019654` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.028134 | `-0.008678` à `+0.071427` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | +0.026119 | `+0.003480` à `+0.048603` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | -0.018577 | `-0.062866` à `+0.022787` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.062087 | `+0.026801` à `+0.098885` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.018448 | `-0.014899` à `+0.053420` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.015099 | `-0.030480` à `+0.000083` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.014912 | `-0.032489` à `+0.001312` |
| `LEARNED-005` | `central_bass_pcset(all_voices)=265` | +0.010643 | `-0.001170` à `+0.022717` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.009269 | `-0.049217` à `+0.028013` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | -0.008179 | `-0.025992` à `+0.009512` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.007403 | `-0.012117` à `+0.028123` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.088465 | `+0.054501` à `+0.124595` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | -0.073498 | `-0.119866` à `-0.031528` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.048864 | `-0.020168` à `+0.120612` |
| `LEARNED-005` | `central_bass_pcset(all_voices)=265` | +0.046733 | `+0.031537` à `+0.061631` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | +0.041754 | `+0.021436` à `+0.065213` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.033003 | `-0.004887` à `+0.068988` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.030323 | `-0.073372` à `+0.011351` |
| `LEARNED-030` | `abs_step_to_next_gt(v1)=1` | -0.028215 | `-0.049248` à `-0.007444` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.069393 | `+0.012291` à `+0.125720` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.060801 | `-0.092451` à `-0.026535` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.052945 | `-0.023093` à `+0.129543` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.050056 | `-0.141242` à `+0.025319` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.047954 | `-0.085880` à `-0.007648` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.045929 | `-0.175468` à `+0.067097` |
| `LEARNED-005` | `central_bass_pcset(all_voices)=265` | -0.038038 | `-0.065484` à `-0.014003` |
| `LEARNED-026` | `central_bass_pcset(all_voices)=161` | +0.035616 | `+0.012126` à `+0.062070` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.172968 | `+0.060659` à `+0.290340` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.161255 | `-0.241020` à `-0.081202` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.136095 | `-0.290784` à `+0.033019` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.090501 | `-0.048478` à `+0.228667` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | +0.072669 | `+0.027007` à `+0.120399` |
| `LEARNED-013` | `any_pair_central_abs_class(all_voices)=1` | +0.071920 | `+0.010533` à `+0.131243` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.071889 | `-0.121844` à `-0.023056` |
| `LEARNED-030` | `abs_step_to_next_gt(v1)=1` | +0.069486 | `+0.015468` à `+0.123468` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.231960 | `-0.383263` à `-0.092585` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.214175 | `+0.118336` à `+0.329099` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.191087 | `+0.049933` à `+0.354272` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.177231 | `-0.382824` à `+0.015668` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.088397 | `-0.176451` à `+0.017640` |
| `LEARNED-018` | `any_pair_central_abs_class_target_passing(all_voices)=10` | +0.085209 | `+0.029227` à `+0.143003` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.062870 | `-0.135871` à `+0.008045` |
| `LEARNED-030` | `abs_step_to_next_gt(v1)=1` | -0.062681 | `-0.120366` à `-0.007547` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.043736 | `-0.075018` à `-0.012238` |
| `LEARNED-021` | `any_pair_central_abs_class(all_voices)=10` | +0.024012 | `+0.000133` à `+0.049776` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.021694 | `+0.015209` à `+0.029061` |
| `LEARNED-022` | `any_pair_central_abs_class_metric(all_voices)=7,1` | -0.020047 | `-0.053608` à `+0.005392` |
| `LEARNED-008` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.011660 | `-0.031505` à `+0.006590` |
| `LEARNED-014` | `any_pair_arrival_abs_class_same_sign(all_voices)=2` | +0.010071 | `+0.003032` à `+0.017884` |
| `LEARNED-025` | `central_pair_abs_class(v3,v2)=6` | +0.009880 | `+0.004110` à `+0.016331` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.008818 | `-0.038590` à `+0.021011` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.021957 | `+0.016483` à `+0.027841` |
| `LEARNED-017` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.017649 | `-0.002075` à `+0.035619` |
| `LEARNED-015` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.010934 | `-0.036349` à `+0.013620` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.010593 | `-0.019091` à `+0.042118` |
| `LEARNED-030` | `abs_step_to_next_gt(v1)=1` | +0.009812 | `+0.001866` à `+0.018030` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.007580 | `-0.006969` à `+0.024379` |
| `LEARNED-006` | `any_pair_central_abs_class_target_passing(all_voices)=9` | -0.007497 | `-0.019394` à `+0.004727` |
| `LEARNED-024` | `central_pair_abs_class(v2,v3)=5` | -0.006398 | `-0.011364` à `-0.001158` |
