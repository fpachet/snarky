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
- Cache issu des mêmes poids : `True`.
- Temps d'échantillonnage : `45.434` secondes.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 24.983 | 31.734 | -6.751 pp | `-9.116` à `-4.207` |
| Répétitions de basse | 4.938 | 4.318 | +0.621 pp | `-0.523` à `+1.949` |
| Sauts de basse > 4 demi-tons | 26.917 | 24.092 | +2.824 pp | `+0.911` à `+4.785` |
| Basse hors gamme naturelle globale | 9.094 | 13.462 | -4.368 pp | `-6.054` à `-2.493` |
| Blocs triadiques | 53.875 | 51.049 | +2.826 pp | `+0.450` à `+5.510` |
| Blocs forts non triadiques | 29.598 | 41.360 | -11.762 pp | `-16.528` à `-6.888` |
| Dissonances par bloc faible | 0.892 | 0.905 | -0.013 | `-0.062` à `+0.036` |
| Dissonances par bloc fort | 0.406 | 0.639 | -0.233 | `-0.310` à `-0.155` |
| {0,3,6,8} sur bloc fort | 1.762 | 2.347 | -0.585 pp | `-1.565` à `+0.447` |
| {0,3,6,8} sur bloc faible | 4.225 | 3.632 | +0.593 pp | `-0.687` à `+1.982` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000138`.
- Plus grand déplacement proposé : `1.032229`.
- Structure localement contrôlable : `false`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.276914 | `+0.179140` à `+0.384821` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.102707 | `-0.160388` à `-0.044902` |
| `LEARNED-005` | `any_pair_central_abs_class_target_passing_metric(all_voices)=9,0` | +0.033829 | `+0.001879` à `+0.072144` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.029191 | `-0.007459` à `+0.071456` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.015144 | `-0.039508` à `+0.007329` |
| `LEARNED-011` | `attacked_repeat_from_previous(v3)` | -0.014107 | `-0.028794` à `-0.000615` |
| `LEARNED-023` | `central_pair_abs_class(v3,v2)=6` | +0.012786 | `+0.003473` à `+0.021009` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | +0.011581 | `-0.005902` à `+0.029956` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-011` | `attacked_repeat_from_previous(v3)` | +0.036135 | `+0.028060` à `+0.045020` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.013173 | `-0.044305` à `+0.019253` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | -0.012913 | `-0.030135` à `+0.003604` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.009555 | `-0.031003` à `+0.009520` |
| `LEARNED-014` | `any_pair_central_abs_class(all_voices)=1` | +0.009159 | `-0.001111` à `+0.018873` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | -0.007145 | `-0.015675` à `+0.001356` |
| `LEARNED-005` | `any_pair_central_abs_class_target_passing_metric(all_voices)=9,0` | -0.007103 | `-0.017212` à `+0.002747` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.006829 | `-0.018191` à `+0.004501` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.161254 | `+0.106519` à `+0.215211` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.155132 | `-0.233135` à `-0.085037` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.076677 | `+0.035857` à `+0.119709` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | -0.056202 | `-0.102822` à `-0.015682` |
| `LEARNED-005` | `any_pair_central_abs_class_target_passing_metric(all_voices)=9,0` | -0.045580 | `-0.070623` à `-0.021387` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.037733 | `-0.128316` à `+0.041893` |
| `LEARNED-014` | `any_pair_central_abs_class(all_voices)=1` | -0.030370 | `-0.055366` à `-0.002674` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.028786 | `-0.021161` à `+0.074973` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.095773 | `+0.043514` à `+0.146271` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.035001 | `-0.005730` à `+0.073598` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.023121 | `-0.063024` à `+0.018041` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.019820 | `-0.001182` à `+0.042042` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.017799 | `-0.054933` à `+0.020350` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | +0.015308 | `+0.001811` à `+0.028904` |
| `LEARNED-025` | `abs_step_to_next_gt(v2)=1` | +0.012980 | `-0.002669` à `+0.029986` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | +0.012167 | `+0.000149` à `+0.023710` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | -0.074147 | `-0.119013` à `-0.035520` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.073143 | `+0.051496` à `+0.096780` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.064057 | `-0.111897` à `-0.017938` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.041902 | `-0.084821` à `+0.000018` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | +0.032133 | `+0.013111` à `+0.048121` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | -0.026066 | `-0.042478` à `-0.010141` |
| `LEARNED-025` | `abs_step_to_next_gt(v2)=1` | -0.020469 | `-0.040822` à `+0.000848` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | +0.020223 | `+0.001048` à `+0.044411` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.088562 | `+0.016141` à `+0.171655` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.060922 | `-0.106859` à `-0.013407` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.049128 | `-0.080105` à `-0.020530` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | +0.030896 | `-0.007065` à `+0.069452` |
| `LEARNED-029` | `abs_step_to_next_gt(v1)=1` | -0.027408 | `-0.070635` à `+0.010494` |
| `LEARNED-014` | `any_pair_central_abs_class(all_voices)=1` | +0.026915 | `-0.018119` à `+0.076323` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.026752 | `-0.047609` à `+0.104648` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.024665 | `-0.055143` à `+0.007243` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.168973 | `+0.073106` à `+0.281906` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.168637 | `-0.248591` à `-0.095083` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.124077 | `+0.004002` à `+0.245263` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.108847 | `-0.179924` à `-0.038575` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.093837 | `-0.003259` à `+0.188284` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.091053 | `-0.232442` à `+0.074943` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | +0.062638 | `+0.021416` à `+0.110558` |
| `LEARNED-014` | `any_pair_central_abs_class(all_voices)=1` | +0.060447 | `+0.011164` à `+0.114251` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.192342 | `+0.060138` à `+0.346954` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.112415 | `-0.242048` à `+0.008235` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.093926 | `-0.044978` à `+0.256364` |
| `LEARNED-014` | `any_pair_central_abs_class(all_voices)=1` | +0.091339 | `-0.002388` à `+0.191975` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.085242 | `-0.147666` à `-0.024220` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | +0.082877 | `+0.010897` à `+0.151499` |
| `LEARNED-017` | `any_pair_arrival_abs_class_same_sign(all_voices)=2` | +0.082160 | `+0.030668` à `+0.145168` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.072129 | `-0.154020` à `+0.000531` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.019980 | `+0.013836` à `+0.026379` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.014817 | `-0.017829` à `+0.047382` |
| `LEARNED-023` | `central_pair_abs_class(v3,v2)=6` | +0.012773 | `+0.006384` à `+0.020335` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.011227 | `-0.034919` à `+0.011529` |
| `LEARNED-014` | `any_pair_central_abs_class(all_voices)=1` | -0.010922 | `-0.025902` à `+0.002037` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | +0.008903 | `-0.001126` à `+0.022460` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.006394 | `-0.012950` à `+0.028217` |
| `LEARNED-022` | `central_pair_abs_class(v2,v3)=5` | -0.006283 | `-0.013874` à `+0.001401` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.023061 | `+0.017563` à `+0.029496` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.022178 | `-0.007432` à `+0.050022` |
| `LEARNED-029` | `abs_step_to_next_gt(v1)=1` | -0.011827 | `-0.021483` à `-0.001840` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | -0.007415 | `-0.017092` à `+0.002124` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.007269 | `-0.029112` à `+0.013822` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.005731 | `-0.011954` à `+0.021321` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.005611 | `-0.017522` à `+0.006163` |
| `LEARNED-025` | `abs_step_to_next_gt(v2)=1` | -0.005535 | `-0.016953` à `+0.005228` |
