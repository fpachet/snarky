# POC V2.1 — génération de colonnes résiduelle

## Protocole

- Corpus : 352 chorals, 20350 décisions disponibles.
- Train : 246 pièces / 14436 décisions.
- Validation : 53 pièces / 3029 décisions.
- Le jeu de test reste scellé et n'est pas chargé par ce programme.
- Données authentiques.
- Direction des colonnes résiduelles : `both`.
- `LEARNED_PREDICATE_001` est réutilisé comme résultat du V1.

## Modèle parcimonieux

- NLL validation du socle : `1.736939`.
- Meilleur préfixe de colonnes : `1.628203`.
- NLL finale après élagage : `1.625642`.
- Clauses actives : 34, dont 12 interactions résiduelles et 2 raffinements de famille.

## Colonnes proposées

| Tour | z résiduel | Score pénalisé | Poids ajusté | NLL validation | Clause |
|---:|---:|---:|---:|---:|---|
| 1 | 23.367 | 0.018674 | 1.453 | 1.728273 | `abs(prev_s-prev_b)%12 == 0 AND sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 4` |
| 2 | 22.607 | 0.017476 | 2.001 | 1.707343 | `abs(prev_s-prev_b)%12 == 7 AND abs(candidate_s-current_b)%12 == 0 AND LEARNED_PREDICATE_001 == true` |
| 3 | 19.225 | 0.012529 | 2.087 | 1.694668 | `abs(candidate_s-current_b)%12 == 2 AND sign(candidate_s-prev_s) == negative AND sign(current_b-prev_b) == zero` |
| 4 | 19.396 | 0.012819 | 2.006 | 1.685104 | `abs(prev_s-prev_b)%12 == 9 AND abs(candidate_s-current_b)%12 == 0 AND LEARNED_PREDICATE_001 == true` |
| 5 | 17.757 | 0.010673 | 1.272 | 1.668110 | `abs(candidate_s-current_b)%12 == 8 AND sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 1` |
| 6 | 18.881 | 0.012094 | 2.053 | 1.662172 | `abs(candidate_s-current_b)%12 == 5 AND sign(candidate_s-prev_s) == positive AND sign(current_b-prev_b) == zero` |
| 7 | 16.786 | 0.009499 | 1.893 | 1.656423 | `abs(candidate_s-current_b)%12 == 6 AND sign(current_b-prev_b) == zero AND abs(candidate_s-prev_s) > 1` |
| 8 | 20.987 | 0.015038 | 2.788 | 1.649100 | `abs(candidate_s-current_b)%12 == 6 AND sign(candidate_s-prev_s) == zero AND sign(current_b-prev_b) == negative` |
| 9 | -14.072 | 0.006674 | -1.100 | 1.638425 | `sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 2` |
| 10 | 16.339 | 0.008963 | 0.495 | 1.632936 | `sign(candidate_s-prev_s) == positive AND sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 4` |
| 11 | -13.414 | 0.006074 | -1.169 | 1.630025 | `sign(current_b-prev_b) == zero AND abs(candidate_s-prev_s) > 2` |
| 12 | 15.735 | 0.008368 | 2.696 | 1.628203 | `abs(prev_s-prev_b)%12 == 4 AND abs(candidate_s-current_b)%12 == 9 AND sign(current_b-prev_b) == zero` |

## Scan uniforme des arrivées après saut en même direction

Les classes `0..11` sont testées symétriquement. Le premier z est le
marginal uniforme ; le second précède le raffinement de famille et
le troisième suit son éventuelle acceptation.

| Classe | z train uniforme | z validation uniforme | z train avant | z validation avant | z train après | z validation après |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | -18.335 | -8.715 | -6.239 | -3.889 | 0.765 | -1.142 |
| 1 | -20.206 | -9.319 | -1.253 | -0.820 | -1.402 | -0.874 |
| 2 | -19.818 | -9.226 | 1.733 | 0.687 | 1.294 | 0.488 |
| 3 | -9.335 | -5.010 | 3.171 | 0.680 | 1.903 | 0.123 |
| 4 | -11.190 | -6.202 | -1.635 | -1.918 | -2.711 | -2.370 |
| 5 | -20.366 | -9.333 | -3.662 | -1.476 | -3.891 | -1.590 |
| 6 | -19.281 | -8.854 | -0.846 | -0.255 | -1.172 | -0.412 |
| 7 | -14.804 | -7.444 | -3.161 | -2.491 | 1.277 | -0.674 |
| 8 | -15.171 | -5.662 | -6.224 | -0.453 | -6.671 | -0.699 |
| 9 | -17.280 | -8.186 | 0.424 | -0.428 | -0.377 | -0.751 |
| 10 | -20.695 | -9.396 | -2.854 | -0.529 | -3.040 | -0.662 |
| 11 | -20.717 | -9.555 | -2.111 | -0.975 | -2.245 | -1.038 |

## Raffinement uniforme de la famille

- Seuils : z train ≤ `-3.0` et z validation ≤ `-2.0`.
- Classes proposées : `[0, 7]`.
- Raffinement accepté : `True`.
- NLL validation avant : `1.628718`.
- NLL validation après : `1.625642`.

## Comparaison sémantique postérieure

| Classe | États valides testés | Positifs appris | Désaccords | Classification |
|---:|---:|---:|---:|---|
| 0 | 301401 | 9972 | 0 | `RECOVERED_EQUIVALENT` |
| 7 | 301401 | 9324 | 0 | `RECOVERED_EQUIVALENT` |

## Règles actives

| Type | Poids | Clause |
|---|---:|---|
| residual_interaction | 2.869 | `abs(candidate_s-current_b)%12 == 6 AND sign(candidate_s-prev_s) == zero AND sign(current_b-prev_b) == negative` |
| residual_interaction | 2.615 | `abs(prev_s-prev_b)%12 == 4 AND abs(candidate_s-current_b)%12 == 9 AND sign(current_b-prev_b) == zero` |
| residual_interaction | 2.513 | `abs(candidate_s-current_b)%12 == 2 AND sign(candidate_s-prev_s) == negative AND sign(current_b-prev_b) == zero` |
| residual_interaction | 2.290 | `abs(prev_s-prev_b)%12 == 7 AND abs(candidate_s-current_b)%12 == 0 AND LEARNED_PREDICATE_001 == true` |
| residual_interaction | 2.258 | `abs(candidate_s-current_b)%12 == 5 AND sign(candidate_s-prev_s) == positive AND sign(current_b-prev_b) == zero` |
| residual_interaction | 2.239 | `abs(prev_s-prev_b)%12 == 9 AND abs(candidate_s-current_b)%12 == 0 AND LEARNED_PREDICATE_001 == true` |
| residual_interaction | 2.095 | `abs(candidate_s-current_b)%12 == 6 AND sign(current_b-prev_b) == zero AND abs(candidate_s-prev_s) > 1` |
| baseline_main_effect | -2.001 | `abs(candidate_s-current_b)%12 == 1` |
| baseline_main_effect | -1.747 | `abs(candidate_s-current_b)%12 == 11` |
| baseline_main_effect | -1.678 | `abs(candidate_s-prev_s) > 2` |
| baseline_main_effect | 1.631 | `abs(candidate_s-current_b)%12 == 4` |
| baseline_main_effect | 1.587 | `abs(candidate_s-current_b)%12 == 3` |
| residual_interaction | 1.516 | `abs(candidate_s-current_b)%12 == 8 AND sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 1` |
| baseline_main_effect | 1.434 | `abs(candidate_s-current_b)%12 == 7` |
| baseline_main_effect | -1.420 | `abs(candidate_s-prev_s) > 7` |
| direct_family_refinement | -1.345 | `abs(candidate_s-current_b)%12 == 0 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| residual_interaction | -1.232 | `sign(current_b-prev_b) == zero AND abs(candidate_s-prev_s) > 2` |
| baseline_main_effect | -1.216 | `abs(candidate_s-prev_s) > 12` |
| residual_interaction | 1.198 | `abs(prev_s-prev_b)%12 == 0 AND sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 4` |
| baseline_main_effect | -1.124 | `abs(candidate_s-prev_s) > 4` |
| residual_interaction | -1.120 | `sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 2` |
| baseline_main_effect | -1.100 | `abs(candidate_s-current_b)%12 == 10` |
| baseline_main_effect | -1.030 | `abs(candidate_s-current_b)%12 == 2` |
| baseline_main_effect | -0.873 | `abs(candidate_s-current_b)%12 == 6` |
| baseline_main_effect | 0.799 | `abs(candidate_s-current_b)%12 == 0` |
| baseline_main_effect | -0.753 | `abs(candidate_s-current_b)%12 == 5` |
| baseline_main_effect | 0.573 | `abs(candidate_s-current_b)%12 == 9` |
| direct_family_refinement | -0.568 | `abs(candidate_s-current_b)%12 == 7 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| baseline_main_effect | 0.545 | `abs(candidate_s-current_b)%12 == 8` |
| baseline_main_effect | -0.531 | `LEARNED_PREDICATE_001 == true` |
| baseline_main_effect | 0.375 | `abs(candidate_s-prev_s) > 1` |
| residual_interaction | 0.325 | `sign(candidate_s-prev_s) == positive AND sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 4` |
| baseline_main_effect | 0.243 | `sign(candidate_s-prev_s) == negative` |
| baseline_main_effect | -0.033 | `sign(candidate_s-prev_s) == positive` |
