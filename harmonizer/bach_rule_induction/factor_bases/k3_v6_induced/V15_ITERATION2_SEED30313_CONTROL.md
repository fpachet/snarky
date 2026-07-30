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
- Temps d'échantillonnage : `98.223` secondes.
- Rang de la matrice de sensibilité : `10/10`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 24.983 | 32.940 | -7.957 pp | `-10.638` à `-5.642` |
| Répétitions de basse | 4.938 | 4.259 | +0.679 pp | `-0.483` à `+1.985` |
| Sauts de basse > 4 demi-tons | 26.917 | 23.057 | +3.860 pp | `+2.039` à `+5.710` |
| Basse hors gamme naturelle globale | 9.094 | 14.479 | -5.386 pp | `-7.222` à `-3.662` |
| Blocs triadiques | 53.875 | 52.572 | +1.303 pp | `-0.689` à `+3.548` |
| Blocs forts non triadiques | 29.598 | 38.061 | -8.463 pp | `-13.511` à `-4.154` |
| Dissonances par bloc faible | 0.892 | 0.880 | +0.012 | `-0.035` à `+0.055` |
| Dissonances par bloc fort | 0.406 | 0.587 | -0.181 | `-0.258` à `-0.111` |
| {0,3,6,8} sur bloc fort | 1.762 | 3.760 | -1.998 pp | `-3.063` à `-0.789` |
| {0,3,6,8} sur bloc faible | 4.225 | 4.067 | +0.158 pp | `-1.211` à `+1.603` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000166`.
- Plus grand déplacement proposé : `1.285317`.
- Structure localement contrôlable : `false`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Demi-tons à la basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.284671 | `+0.187960` à `+0.380974` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.176039 | `-0.280317` à `-0.088447` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.083998 | `+0.038256` à `+0.133118` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.032406 | `-0.075782` à `+0.008933` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.028278 | `-0.009084` à `+0.069090` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.022949 | `+0.009810` à `+0.037614` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | +0.020152 | `+0.003988` à `+0.035718` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.015409 | `-0.042904` à `+0.010088` |

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-011` | `attacked_repeat_from_previous(v3)` | +0.039955 | `+0.032224` à `+0.048125` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.035651 | `-0.058262` à `-0.012863` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.016304 | `+0.002107` à `+0.031201` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.013754 | `-0.031463` à `+0.004588` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.010516 | `-0.023251` à `+0.002953` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.008456 | `-0.042611` à `+0.029516` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.007122 | `-0.011408` à `+0.028105` |
| `LEARNED-029` | `abs_step_to_next_gt(v1)=1` | -0.006387 | `-0.020580` à `+0.007970` |

### Sauts de basse > 4 demi-tons

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.222681 | `+0.142383` à `+0.309926` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.109196 | `-0.196768` à `-0.014248` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.107965 | `+0.070827` à `+0.144389` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.061686 | `+0.017805` à `+0.109260` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | -0.056732 | `-0.093419` à `-0.020687` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.033399 | `-0.079578` à `+0.009860` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.030698 | `+0.004704` à `+0.057267` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | -0.023394 | `-0.038752` à `-0.009550` |

### Basse hors gamme naturelle globale

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.109837 | `+0.067919` à `+0.153320` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.032430 | `+0.000209` à `+0.065541` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.028253 | `-0.078782` à `+0.019282` |
| `LEARNED-014` | `any_pair_central_abs_class(all_voices)=1` | +0.022306 | `+0.006539` à `+0.041100` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | +0.011151 | `-0.013694` à `+0.040874` |
| `LEARNED-027` | `central_pair_abs_class(v0,v1)=5` | -0.008069 | `-0.021611` à `+0.004295` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | +0.007962 | `-0.002398` à `+0.019023` |
| `LEARNED-029` | `abs_step_to_next_gt(v1)=1` | -0.007601 | `-0.028159` à `+0.018017` |

### Blocs triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.074340 | `-0.126923` à `-0.022808` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.057488 | `+0.039143` à `+0.078193` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | -0.054905 | `-0.082669` à `-0.025432` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.043450 | `+0.002240` à `+0.086861` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | +0.036047 | `+0.018593` à `+0.055330` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.035062 | `-0.073624` à `+0.005897` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | +0.025549 | `+0.010964` à `+0.041120` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | -0.022529 | `-0.037349` à `-0.009543` |

### Blocs forts non triadiques

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.062168 | `-0.132927` à `+0.004721` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.045352 | `-0.073846` à `-0.014114` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.044819 | `-0.084341` à `-0.005943` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.044489 | `+0.002055` à `+0.086403` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.042862 | `-0.019378` à `+0.101274` |
| `LEARNED-027` | `central_pair_abs_class(v0,v1)=5` | -0.030970 | `-0.054038` à `-0.008899` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.027452 | `-0.065396` à `+0.009507` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | +0.027197 | `+0.002270` à `+0.051749` |

### Dissonances par bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.343356 | `+0.166501` à `+0.531352` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.209710 | `+0.130302` à `+0.288557` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.185592 | `-0.331764` à `-0.043219` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | +0.096017 | `+0.051241` à `+0.144800` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.094570 | `-0.164147` à `-0.025680` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.083637 | `-0.139970` à `-0.031682` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.078298 | `-0.014911` à `+0.176732` |
| `LEARNED-025` | `abs_step_to_next_gt(v2)=1` | -0.065899 | `-0.126219` à `-0.002934` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.080233 | `-0.007527` à `+0.165919` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.078481 | `-0.053375` à `+0.201390` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.070598 | `-0.119356` à `-0.022063` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.067321 | `-0.143292` à `+0.276642` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.065119 | `-0.254736` à `+0.119642` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | +0.059917 | `+0.010367` à `+0.111852` |
| `LEARNED-027` | `central_pair_abs_class(v0,v1)=5` | -0.045728 | `-0.097538` à `+0.003793` |
| `LEARNED-025` | `abs_step_to_next_gt(v2)=1` | -0.038679 | `-0.107903` à `+0.033761` |

### {0,3,6,8} sur bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.033221 | `-0.008049` à `+0.077279` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.032065 | `+0.023877` à `+0.041755` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.027044 | `-0.002233` à `+0.060392` |
| `LEARNED-023` | `central_pair_abs_class(v3,v2)=6` | +0.015264 | `+0.007616` à `+0.024122` |
| `LEARNED-014` | `any_pair_central_abs_class(all_voices)=1` | -0.012972 | `-0.024854` à `-0.002624` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.012382 | `-0.012950` à `+0.039790` |
| `LEARNED-005` | `any_pair_central_abs_class_target_passing_metric(all_voices)=9,0` | -0.012082 | `-0.028124` à `+0.001796` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | -0.008457 | `-0.037558` à `+0.018372` |

### {0,3,6,8} sur bloc faible

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.035458 | `-0.083746` à `-0.001535` |
| `LEARNED-007` | `central_bass_pcset(all_voices)=329` | +0.028801 | `+0.021844` à `+0.036463` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.016150 | `-0.001986` à `+0.034925` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.014340 | `-0.024825` à `-0.004368` |
| `LEARNED-008` | `any_pair_central_abs_class_target_passing_metric(all_voices)=10,0` | +0.011012 | `+0.002921` à `+0.018892` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.009368 | `-0.003595` à `+0.022108` |
| `LEARNED-009` | `any_voice_adjacent_step_gt(all_voices)=7` | -0.009305 | `-0.025421` à `+0.005895` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | +0.009275 | `-0.008533` à `+0.028875` |
