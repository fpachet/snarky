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
- Temps d'échantillonnage : `63.285` secondes.
- Rang de la matrice de sensibilité : `2/2`.
- Métriques standardisées : `true`.

## Résidus train

| Mesure | Bach | Gibbs | Cible Bach−Gibbs | IC95 bootstrap |
|---|---:|---:|---:|---:|
| Répétitions de basse | 4.938 | 4.101 | +0.837 pp | `-0.440` à `+2.167` |
| Dissonances par bloc fort | 0.406 | 0.652 | -0.245 | `-0.314` à `-0.179` |

## Correction linéaire minimale

- Erreur relative projetée : `0.000006`.
- Plus grand déplacement proposé : `0.303861`.
- Structure localement contrôlable : `true`.

Cette projection est un diagnostic local, pas encore un nouveau
jeu de poids. Elle doit être confirmée par génération.

## Facteurs les plus sensibles

### Répétitions de basse

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-011` | `attacked_repeat_from_previous(v3)` | +0.033451 | `+0.027265` à `+0.039819` |
| `LEARNED-018` | `any_voice_adjacent_abs_class(all_voices)=1` | -0.033451 | `-0.068901` à `-0.000580` |
| `LEARNED-029` | `abs_step_to_next_gt(v1)=1` | +0.011759 | `-0.003165` à `+0.027250` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | +0.011579 | `-0.019146` à `+0.046215` |
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | -0.009097 | `-0.024569` à `+0.007126` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | -0.008863 | `-0.017481` à `-0.000852` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | +0.008131 | `-0.006304` à `+0.022926` |
| `LEARNED-005` | `any_pair_central_abs_class_target_passing_metric(all_voices)=9,0` | -0.007945 | `-0.016930` à `+0.000366` |

### Dissonances par bloc fort

| Facteur | Prédicat | Sensibilité | IC95 |
|---|---|---:|---:|
| `LEARNED-016` | `any_pair_central_abs_class(all_voices)=10` | +0.275257 | `+0.155896` à `+0.418931` |
| `LEARNED-001` | `any_voice_adjacent_step_gt(all_voices)=2` | -0.243093 | `-0.535604` à `+0.033876` |
| `LEARNED-020` | `any_pair_abs_class_preserved_same_sign(all_voices)=3` | -0.136368 | `-0.273348` à `-0.007324` |
| `LEARNED-015` | `any_pair_central_abs_class(all_voices)=11` | +0.125932 | `+0.066006` à `+0.193160` |
| `LEARNED-006` | `central_bass_pcset(all_voices)=265` | -0.092771 | `-0.143592` à `-0.047484` |
| `LEARNED-002` | `central_bass_pcset(all_voices)=145` | -0.088304 | `-0.185439` à `+0.011748` |
| `LEARNED-004` | `any_adjacent_central_ordered_gap_le(all_voices)=2` | -0.084007 | `-0.377667` à `+0.215221` |
| `LEARNED-003` | `central_bass_pcset(all_voices)=137` | -0.082252 | `-0.150868` à `-0.016010` |
