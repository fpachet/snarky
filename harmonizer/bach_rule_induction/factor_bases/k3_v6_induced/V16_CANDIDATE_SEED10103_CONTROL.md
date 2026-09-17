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
- Temps d'échantillonnage : `683.517` secondes.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 24.983 | 28.740 | -3.757 pp | `-6.438` à `-1.264` |
| Répétitions de basse | 4.938 | 4.246 | +0.692 pp | `-0.496` à `+1.995` |
| Sauts de basse > 4 demi-tons | 26.917 | 27.915 | -0.999 pp | `-3.080` à `+1.036` |
| Basse hors gamme naturelle globale | 9.094 | 13.611 | -4.517 pp | `-6.260` à `-2.734` |
| Blocs triadiques | 53.875 | 51.813 | +2.062 pp | `-0.023` à `+4.270` |
| Blocs forts non triadiques | 29.598 | 39.970 | -10.372 pp | `-14.536` à `-6.402` |
| Dissonances par bloc faible | 0.892 | 0.914 | -0.022 | `-0.077` à `+0.025` |
| Dissonances par bloc fort | 0.406 | 0.594 | -0.188 | `-0.250` à `-0.129` |
| {0,3,6,8} sur bloc fort | 1.762 | 2.846 | -1.083 pp | `-2.317` à `+0.179` |
| {0,3,6,8} sur bloc faible | 4.225 | 3.505 | +0.720 pp | `-0.338` à `+1.823` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000465`.
- Plus grand déplacement proposé : `0.850232`.
- Structure localement contrôlable : `false`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.238574 | `+0.198916` à `+0.280574` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.129872 | `-0.191006` à `-0.066656` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.045995 | `+0.014823` à `+0.077203` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | -0.043090 | `-0.138424` à `+0.029296` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.040157 | `-0.129965` à `+0.042857` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.027995 | `-0.067976` à `+0.011394` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | +0.021938 | `-0.012386` à `+0.057130` |
| `V16-CANDIDATE-008` | `abs_class_from_previous(v3)=0` | -0.021180 | `-0.031857` à `-0.011469` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-011` | `attacked_repeat_from_previous(v3)` | +0.032148 | `+0.027640` à `+0.037161` |
| `V16-CANDIDATE-008` | `abs_class_from_previous(v3)=0` | +0.031807 | `+0.026825` à `+0.037421` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.022663 | `-0.043131` à `-0.002947` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | -0.017536 | `-0.044238` à `+0.006552` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | -0.013900 | `-0.032085` à `+0.003406` |
| `V16-CANDIDATE-005` | `any_voice_three_block_sign_shape(all_voices)=0,-1` | +0.013695 | `+0.007906` à `+0.020116` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.013233 | `-0.017195` à `+0.041611` |
| `LEARNED-028` | `central_pair_abs_class(v1,v0)=5` | +0.008185 | `-0.000506` à `+0.017860` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.274191 | `+0.188803` à `+0.350119` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.160242 | `+0.053471` à `+0.257842` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.122694 | `+0.076165` à `+0.166041` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.119886 | `+0.032092` à `+0.216905` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.113226 | `-0.165333` à `-0.059681` |
| `V16-CANDIDATE-012` | `any_voice_adjacent_abs_class(all_voices)=6` | +0.034451 | `+0.012313` à `+0.055898` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | -0.031043 | `-0.056736` à `-0.006195` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.031037 | `-0.065522` à `+0.003808` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.076279 | `+0.047788` à `+0.103637` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.053777 | `+0.031895` à `+0.079973` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.026587 | `-0.025308` à `+0.080557` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.022937 | `-0.027113` à `+0.067352` |
| `V16-CANDIDATE-008` | `abs_class_from_previous(v3)=0` | -0.015919 | `-0.025070` à `-0.007554` |
| `LEARNED-025` | `abs_step_to_next_gt(v2)=1` | +0.014589 | `-0.000773` à `+0.029201` |
| `V16-CANDIDATE-005` | `any_voice_three_block_sign_shape(all_voices)=0,-1` | -0.014535 | `-0.024952` à `-0.004842` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.013248 | `+0.006893` à `+0.019896` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | -0.142725 | `-0.177810` à `-0.109880` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.122930 | `+0.096814` à `+0.153981` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.104821 | `-0.203116` à `-0.009510` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | -0.055903 | `-0.151637` à `+0.048519` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | +0.054394 | `+0.034260` à `+0.075990` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.052397 | `-0.023766` à `+0.134743` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | +0.045411 | `+0.030114` à `+0.059935` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.045093 | `-0.110004` à `+0.013870` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | +0.144287 | `+0.102781` à `+0.192857` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.097569 | `-0.145176` à `-0.054108` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.084869 | `-0.073427` à `+0.251166` |
| `LEARNED-028` | `central_pair_abs_class(v1,v0)=5` | -0.063249 | `-0.120814` à `-0.008700` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.055978 | `-0.081355` à `-0.032016` |
| `V16-CANDIDATE-009` | `any_pair_arrival_abs_class_same_sign(all_voices)=10` | +0.054493 | `+0.024045` à `+0.088184` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.048802 | `-0.082219` à `-0.018245` |
| `LEARNED-027` | `central_pair_abs_class(v0,v1)=5` | -0.045850 | `-0.090136` à `-0.007265` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | +0.317648 | `+0.246994` à `+0.393400` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.296024 | `+0.072358` à `+0.517610` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.253144 | `-0.325353` à `-0.184065` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.233518 | `+0.054544` à `+0.427254` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.196865 | `-0.001101` à `+0.412479` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.172618 | `-0.380888` à `+0.004739` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.113423 | `-0.172928` à `-0.060479` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | +0.107269 | `+0.074580` à `+0.140596` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | +0.268941 | `+0.176602` à `+0.373291` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.175753 | `-0.169197` à `+0.511618` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.165344 | `-0.263729` à `-0.070312` |
| `LEARNED-028` | `central_pair_abs_class(v1,v0)=5` | -0.125614 | `-0.237503` à `-0.024516` |
| `LEARNED-021` | `central_pair_abs_class(v0,v1)=2` | +0.120282 | `+0.082420` à `+0.164468` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.117605 | `-0.170148` à `-0.066922` |
| `LEARNED-027` | `central_pair_abs_class(v0,v1)=5` | -0.100737 | `-0.169201` à `-0.027369` |
| `V16-CANDIDATE-009` | `any_pair_arrival_abs_class_same_sign(all_voices)=10` | +0.094443 | `+0.032814` à `+0.165334` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | -0.039186 | `-0.094133` à `+0.003202` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.033137 | `+0.014631` à `+0.050939` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.030807 | `-0.060889` à `+0.000254` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.026838 | `+0.018913` à `+0.035490` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.025169 | `-0.075011` à `+0.017113` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.021730 | `-0.005831` à `+0.050239` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=10` | +0.020610 | `+0.005935` à `+0.035467` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.019812 | `-0.037107` à `-0.002350` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.034811 | `+0.028723` à `+0.042226` |
| `LEARNED-017` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.022337 | `-0.000436` à `+0.045296` |
| `LEARNED-020` | `any_adjacent_central_ordered_gap_le(all_voices)=-1` | +0.019661 | `-0.015630` à `+0.052143` |
| `LEARNED-018` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.016225 | `+0.000405` à `+0.031329` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.011111 | `-0.015288` à `+0.044338` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.010211 | `-0.022785` à `+0.000198` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.008964 | `-0.018915` à `+0.001384` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.008739 | `-0.005620` à `+0.024646` |
