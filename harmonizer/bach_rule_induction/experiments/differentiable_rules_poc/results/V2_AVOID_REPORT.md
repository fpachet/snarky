# POC V2.1 — génération de colonnes résiduelle

## Protocole

- Corpus : 352 chorals, 20350 décisions disponibles.
- Train : 246 pièces / 14436 décisions.
- Validation : 53 pièces / 3029 décisions.
- Le jeu de test reste scellé et n'est pas chargé par ce programme.
- Données authentiques.
- Direction des colonnes résiduelles : `avoid`.
- `LEARNED_PREDICATE_001` est réutilisé comme résultat du V1.

## Modèle parcimonieux

- NLL validation du socle : `1.736939`.
- Meilleur préfixe de colonnes : `1.620815`.
- NLL finale après élagage : `1.620815`.
- Clauses actives : 33, dont 12 interactions résiduelles et 0 raffinements de famille.

## Colonnes proposées

| Tour | z résiduel | Score pénalisé | Poids ajusté | NLL validation | Clause |
|---:|---:|---:|---:|---:|---|
| 1 | -15.429 | 0.008035 | -0.965 | 1.726504 | `abs(prev_s-prev_b)%12 == 3 AND sign(candidate_s-prev_s) == negative AND abs(candidate_s-prev_s) > 1` |
| 2 | -14.856 | 0.007429 | -1.370 | 1.710994 | `sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 3 | -14.153 | 0.006735 | -2.758 | 1.696877 | `abs(prev_s-prev_b)%12 == 0 AND abs(candidate_s-current_b)%12 == 0 AND LEARNED_PREDICATE_001 == true` |
| 4 | -14.295 | 0.006877 | -2.707 | 1.686320 | `abs(prev_s-prev_b)%12 == 7 AND abs(candidate_s-current_b)%12 == 7 AND LEARNED_PREDICATE_001 == true` |
| 5 | -13.576 | 0.006185 | -3.028 | 1.677318 | `abs(prev_s-prev_b)%12 == 4 AND abs(candidate_s-current_b)%12 == 3 AND sign(current_b-prev_b) == zero` |
| 6 | -12.804 | 0.005493 | -1.249 | 1.664708 | `abs(candidate_s-current_b)%12 == 8 AND sign(candidate_s-prev_s) == negative` |
| 7 | -12.460 | 0.005243 | -2.127 | 1.659168 | `abs(prev_s-prev_b)%12 == 6 AND LEARNED_PREDICATE_001 == true` |
| 8 | -12.173 | 0.004931 | -2.129 | 1.652942 | `abs(prev_s-prev_b)%12 == 3 AND abs(candidate_s-current_b)%12 == 0 AND sign(candidate_s-prev_s) == positive` |
| 9 | -11.583 | 0.004489 | -1.030 | 1.650194 | `sign(current_b-prev_b) == zero AND abs(candidate_s-prev_s) > 2` |
| 10 | -15.802 | 0.008492 | -1.377 | 1.637755 | `sign(candidate_s-prev_s) == zero AND sign(current_b-prev_b) == zero` |
| 11 | -13.343 | 0.005967 | -3.118 | 1.625944 | `abs(prev_s-prev_b)%12 == 3 AND abs(candidate_s-current_b)%12 == 4 AND sign(current_b-prev_b) == zero` |
| 12 | -10.740 | 0.003774 | -0.903 | 1.620815 | `abs(candidate_s-current_b)%12 == 4 AND sign(candidate_s-prev_s) == positive AND sign(current_b-prev_b) == negative` |

## Scan uniforme des arrivées après saut en même direction

Les classes `0..11` sont testées symétriquement. Le premier z est le
marginal uniforme ; le second précède le raffinement de famille et
le troisième suit son éventuelle acceptation.

| Classe | z train uniforme | z validation uniforme | z train avant | z validation avant | z train après | z validation après |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | -18.335 | -8.715 | -1.380 | -1.715 | -1.380 | -1.715 |
| 1 | -20.206 | -9.319 | -1.428 | -0.875 | -1.428 | -0.875 |
| 2 | -19.818 | -9.226 | 0.858 | 0.329 | 0.858 | 0.329 |
| 3 | -9.335 | -5.010 | 5.031 | 1.412 | 5.031 | 1.412 |
| 4 | -11.190 | -6.202 | -1.204 | -1.812 | -1.204 | -1.812 |
| 5 | -20.366 | -9.333 | -3.883 | -1.564 | -3.883 | -1.564 |
| 6 | -19.281 | -8.854 | -2.625 | -1.084 | -2.625 | -1.084 |
| 7 | -14.804 | -7.444 | -1.747 | -1.756 | -1.747 | -1.756 |
| 8 | -15.171 | -5.662 | 0.356 | 3.387 | 0.356 | 3.387 |
| 9 | -17.280 | -8.186 | -0.144 | -0.677 | -0.144 | -0.677 |
| 10 | -20.695 | -9.396 | -3.080 | -0.705 | -3.080 | -0.705 |
| 11 | -20.717 | -9.555 | -2.437 | -1.130 | -2.437 | -1.130 |

## Raffinement uniforme de la famille

- Seuils : z train ≤ `-3.0` et z validation ≤ `-2.0`.
- Classes proposées : `[]`.
- Raffinement accepté : `False`.
- NLL validation avant : `1.620815`.
- NLL validation après : `nan`.

## Comparaison sémantique postérieure

| Classe | États valides testés | Positifs appris | Désaccords | Classification |
|---:|---:|---:|---:|---|

## Règles actives

| Type | Poids | Clause |
|---|---:|---|
| residual_interaction | -3.298 | `abs(prev_s-prev_b)%12 == 4 AND abs(candidate_s-current_b)%12 == 3 AND sign(current_b-prev_b) == zero` |
| residual_interaction | -3.245 | `abs(prev_s-prev_b)%12 == 3 AND abs(candidate_s-current_b)%12 == 4 AND sign(current_b-prev_b) == zero` |
| residual_interaction | -2.917 | `abs(prev_s-prev_b)%12 == 0 AND abs(candidate_s-current_b)%12 == 0 AND LEARNED_PREDICATE_001 == true` |
| residual_interaction | -2.754 | `abs(prev_s-prev_b)%12 == 7 AND abs(candidate_s-current_b)%12 == 7 AND LEARNED_PREDICATE_001 == true` |
| residual_interaction | -2.183 | `abs(prev_s-prev_b)%12 == 3 AND abs(candidate_s-current_b)%12 == 0 AND sign(candidate_s-prev_s) == positive` |
| residual_interaction | -2.105 | `abs(prev_s-prev_b)%12 == 6 AND LEARNED_PREDICATE_001 == true` |
| baseline_main_effect | -2.102 | `abs(candidate_s-current_b)%12 == 1` |
| baseline_main_effect | -1.782 | `abs(candidate_s-prev_s) > 2` |
| baseline_main_effect | -1.780 | `abs(candidate_s-current_b)%12 == 11` |
| baseline_main_effect | 1.562 | `abs(candidate_s-current_b)%12 == 4` |
| residual_interaction | -1.539 | `sign(candidate_s-prev_s) == zero AND sign(current_b-prev_b) == zero` |
| baseline_main_effect | 1.482 | `abs(candidate_s-current_b)%12 == 7` |
| residual_interaction | -1.463 | `sign(current_b-prev_b) == zero AND abs(candidate_s-prev_s) > 2` |
| residual_interaction | -1.449 | `sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| baseline_main_effect | -1.422 | `abs(candidate_s-prev_s) > 7` |
| baseline_main_effect | 1.388 | `abs(candidate_s-current_b)%12 == 3` |
| baseline_main_effect | -1.268 | `abs(candidate_s-current_b)%12 == 10` |
| baseline_main_effect | 1.246 | `abs(candidate_s-current_b)%12 == 8` |
| baseline_main_effect | -1.213 | `abs(candidate_s-prev_s) > 12` |
| residual_interaction | -1.174 | `abs(candidate_s-current_b)%12 == 8 AND sign(candidate_s-prev_s) == negative` |
| baseline_main_effect | -1.172 | `abs(candidate_s-prev_s) > 4` |
| baseline_main_effect | 1.156 | `abs(candidate_s-current_b)%12 == 0` |
| baseline_main_effect | -1.013 | `abs(candidate_s-current_b)%12 == 2` |
| residual_interaction | -0.997 | `abs(prev_s-prev_b)%12 == 3 AND sign(candidate_s-prev_s) == negative AND abs(candidate_s-prev_s) > 1` |
| residual_interaction | -0.903 | `abs(candidate_s-current_b)%12 == 4 AND sign(candidate_s-prev_s) == positive AND sign(current_b-prev_b) == negative` |
| baseline_main_effect | -0.709 | `abs(candidate_s-current_b)%12 == 5` |
| baseline_main_effect | 0.643 | `abs(candidate_s-prev_s) > 1` |
| baseline_main_effect | -0.472 | `abs(candidate_s-current_b)%12 == 6` |
| baseline_main_effect | 0.459 | `abs(candidate_s-current_b)%12 == 9` |
| baseline_main_effect | 0.261 | `sign(candidate_s-prev_s) == negative` |
| baseline_main_effect | -0.238 | `sign(candidate_s-prev_s) == positive` |
| baseline_main_effect | 0.160 | `sign(candidate_s-prev_s) == zero` |
| baseline_main_effect | -0.079 | `LEARNED_PREDICATE_001 == true` |
