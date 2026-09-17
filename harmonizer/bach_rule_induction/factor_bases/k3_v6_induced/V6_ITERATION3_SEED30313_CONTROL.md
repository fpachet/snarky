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
- Temps d'échantillonnage : `138.917` secondes.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 24.983 | 26.309 | -1.327 pp | `-4.193` à `+1.451` |
| Répétitions de basse | 4.938 | 4.331 | +0.608 pp | `-0.647` à `+1.979` |
| Sauts de basse > 4 demi-tons | 26.917 | 27.548 | -0.631 pp | `-2.453` à `+1.267` |
| Basse hors gamme naturelle globale | 9.094 | 10.186 | -1.093 pp | `-3.119` à `+1.029` |
| Blocs triadiques | 53.875 | 52.297 | +1.578 pp | `-0.954` à `+3.847` |
| Blocs forts non triadiques | 29.598 | 29.344 | +0.254 pp | `-3.997` à `+4.146` |
| Dissonances par bloc faible | 0.892 | 0.928 | -0.036 | `-0.092` à `+0.024` |
| Dissonances par bloc fort | 0.406 | 0.425 | -0.019 | `-0.086` à `+0.044` |
| {0,3,6,8} sur bloc fort | 1.762 | 2.601 | -0.839 pp | `-2.210` à `+0.617` |
| {0,3,6,8} sur bloc faible | 4.225 | 4.680 | -0.455 pp | `-1.689` à `+0.816` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000319`.
- Plus grand déplacement proposé : `0.343638`.
- Structure localement contrôlable : `true`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.238913 | `+0.184921` à `+0.306350` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.164507 | `-0.227051` à `-0.098720` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.065883 | `-0.107293` à `-0.025700` |
| `F-K3-V6-014` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.039548 | `-0.058536` à `-0.020815` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.028262 | `-0.046021` à `-0.010600` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.021958 | `-0.053426` à `+0.007187` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.021731 | `+0.000688` à `+0.045948` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.021156 | `-0.002797` à `+0.045436` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-019` | `attacked_repeat_from_previous(v3)` | +0.035423 | `+0.030637` à `+0.040680` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.023302 | `-0.039604` à `-0.006516` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.022927 | `-0.039859` à `-0.004423` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | -0.013653 | `-0.023921` à `-0.003495` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.008574 | `-0.024463` à `+0.009785` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | -0.007265 | `-0.014306` à `-0.000023` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.006945 | `-0.013191` à `-0.000082` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.006488 | `-0.017257` à `+0.006188` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.237554 | `+0.186602` à `+0.294508` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.118878 | `-0.170926` à `-0.069699` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.102880 | `-0.168607` à `-0.040588` |
| `F-K3-V6-014` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.088202 | `+0.067375` à `+0.108826` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.060415 | `+0.030238` à `+0.092127` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | -0.029591 | `-0.059522` à `-0.000519` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | -0.026475 | `-0.056743` à `-0.000964` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | -0.023767 | `-0.043166` à `-0.002867` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.056703 | `+0.026479` à `+0.085317` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.044734 | `-0.074865` à `-0.016394` |
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.017446 | `+0.011755` à `+0.023167` |
| `F-K3-V6-026` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.010786 | `+0.001481` à `+0.020618` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.010566 | `-0.018706` à `-0.002790` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.010051 | `-0.026668` à `+0.003594` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | +0.009511 | `+0.000125` à `+0.019372` |
| `F-K3-V6-019` | `attacked_repeat_from_previous(v3)` | -0.009139 | `-0.012775` à `-0.005796` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | -0.106065 | `-0.129935` à `-0.084568` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | +0.071499 | `+0.054696` à `+0.089308` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | -0.070021 | `-0.087796` à `-0.052695` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | +0.057917 | `+0.047014` à `+0.070667` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | +0.053973 | `+0.040416` à `+0.066673` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.052801 | `-0.096219` à `-0.016115` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.036221 | `-0.065429` à `-0.008544` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.032396 | `-0.053154` à `-0.014804` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.100425 | `+0.059707` à `+0.141504` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.083695 | `-0.150372` à `-0.011967` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.075377 | `+0.011882` à `+0.136922` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.068010 | `+0.031496` à `+0.109395` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | +0.046784 | `+0.025476` à `+0.065920` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | +0.046230 | `-0.034846` à `+0.124109` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.045476 | `-0.063129` à `-0.028378` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.043737 | `-0.076661` à `-0.013130` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.265624 | `+0.200226` à `+0.336159` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.207089 | `+0.168509` à `+0.249846` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.157897 | `-0.200736` à `-0.114638` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | -0.149936 | `-0.187336` à `-0.116856` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.148866 | `+0.020741` à `+0.303039` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.103741 | `-0.141986` à `-0.063949` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | +0.074367 | `+0.019132` à `+0.130940` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.068167 | `+0.014831` à `+0.116069` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.221380 | `+0.124408` à `+0.332013` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.180157 | `+0.111707` à `+0.250489` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.172731 | `-0.315797` à `-0.037618` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.155902 | `+0.095117` à `+0.227445` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.081653 | `-0.133828` à `-0.032319` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.076128 | `-0.110544` à `-0.047110` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | +0.066854 | `+0.024974` à `+0.110174` |
| `F-K3-V6-016` | `central_distinct_pc_count(all_voices)=2` | -0.035988 | `-0.060796` à `-0.011549` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.032549 | `-0.054948` à `-0.008819` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.031161 | `+0.015762` à `+0.048112` |
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.030836 | `+0.021016` à `+0.040787` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.020838 | `-0.005145` à `+0.046103` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | +0.008573 | `-0.008952` à `+0.027842` |
| `F-K3-V6-004` | `central_bass_pcset(all_voices)=265` | -0.007322 | `-0.014070` à `-0.001118` |
| `F-K3-V6-028` | `central_bass_pcset(all_voices)=1169` | -0.005515 | `-0.011384` à `+0.000480` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.005423 | `-0.016339` à `+0.004838` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-008` | `central_bass_pcset(all_voices)=329` | +0.051839 | `+0.043133` à `+0.061547` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.030943 | `-0.058384` à `-0.002688` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.028044 | `+0.012138` à `+0.042608` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.014025 | `-0.027852` à `-0.001244` |
| `F-K3-V6-013` | `any_pair_central_abs_class(all_voices)=1` | -0.010911 | `-0.019302` à `-0.002813` |
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.010488 | `+0.000631` à `+0.020940` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.008794 | `-0.017257` à `-0.000645` |
| `F-K3-V6-009` | `any_pair_central_abs_class(all_voices)=11` | -0.006566 | `-0.011241` à `-0.001919` |
