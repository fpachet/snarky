# V6 — contrôlabilité des résidus par les 30 facteurs gelés

Cette analyse utilise uniquement des chorals du train. Pour une métrique
`g` et un facteur `f`, la sensibilité locale est estimée par :

```text
∂ E[g] / ∂ poids(f) = Cov(g, nombre_d_activations(f))
```

Aucun facteur ni poids n'est modifié par cette expérience. Le test
réservé n'est pas chargé.

## Échantillonnage

- Pièces : `64`.
- Chaînes par pièce : `2`.
- États conservés par chaîne : `6`.
- Rang de la matrice de sensibilité : `2/2`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Répétitions de basse | 4.450 | 5.220 | -0.770 pp | `-1.534` à `+0.049` |
| Dissonances par bloc fort | 0.404 | 0.583 | -0.180 | `-0.222` à `-0.135` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000013`.
- Plus grand déplacement proposé : `0.205955`.
- Structure localement contrôlable : `true`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-019` | `attacked_repeat_from_previous(v3)` | +0.045447 | `+0.040529` à `+0.050537` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.031934 | `-0.049006` à `-0.014476` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.023567 | `-0.038811` à `-0.008137` |
| `F-K3-V6-025` | `any_voice_three_block_sign_shape(all_voices)=-1,-1` | -0.023152 | `-0.031473` à `-0.014721` |
| `F-K3-V6-006` | `any_voice_adjacent_abs_class(all_voices)=2` | -0.019344 | `-0.034815` à `-0.004220` |
| `F-K3-V6-017` | `central_distinct_pc_count_metric(all_voices)=3,0` | +0.010600 | `+0.004785` à `+0.017278` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | +0.008332 | `-0.000216` à `+0.017568` |
| `F-K3-V6-004` | `central_bass_pcset(all_voices)=265` | -0.007359 | `-0.013455` à `-0.001679` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `F-K3-V6-011` | `any_pair_central_abs_class(all_voices)=10` | +0.289877 | `+0.238048` à `+0.349406` |
| `F-K3-V6-020` | `any_pair_central_abs_class(all_voices)=2` | +0.260177 | `+0.192774` à `+0.327785` |
| `F-K3-V6-005` | `any_voice_adjacent_abs_class(all_voices)=1` | +0.214799 | `+0.125200` à `+0.303012` |
| `F-K3-V6-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.106500 | `-0.222237` à `+0.013197` |
| `F-K3-V6-002` | `central_bass_pcset(all_voices)=145` | -0.089819 | `-0.134422` à `-0.046523` |
| `F-K3-V6-003` | `central_bass_pcset(all_voices)=137` | -0.080423 | `-0.123792` à `-0.039345` |
| `F-K3-V6-007` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | +0.072922 | `-0.002134` à `+0.142613` |
| `F-K3-V6-004` | `central_bass_pcset(all_voices)=265` | -0.059077 | `-0.093994` à `-0.024007` |
