# POC V2.1 — génération de colonnes résiduelle

## Protocole

- Corpus : 352 chorals, 20350 décisions disponibles.
- Train : 251 pièces / 14744 décisions.
- Validation : 50 pièces / 2807 décisions.
- Partage : `exact_soprano_contour_and_rhythm_conservative_grouping`.
- Le jeu de test reste scellé et n'est pas chargé par ce programme.
- Données authentiques.
- Direction des colonnes résiduelles : `both`.
- `LEARNED_PREDICATE_001` est réutilisé comme résultat du V1.

## Modèle parcimonieux

- NLL validation du socle : `1.731060`.
- Meilleur préfixe de colonnes : `1.626783`.
- NLL finale après élagage : `1.624531`.
- Clauses actives : 34, dont 12 interactions résiduelles et 2 raffinements de famille.

## Colonnes proposées

| Tour | z résiduel | Score pénalisé | Poids ajusté | NLL validation | Clause |
|---:|---:|---:|---:|---:|---|
| 1 | 23.720 | 0.018847 | 1.462 | 1.724328 | `abs(prev_s-prev_b)%12 == 0 AND sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 4` |
| 2 | 22.923 | 0.017599 | 2.008 | 1.703798 | `abs(prev_s-prev_b)%12 == 7 AND abs(candidate_s-current_b)%12 == 0 AND LEARNED_PREDICATE_001 == true` |
| 3 | 19.579 | 0.012733 | 2.100 | 1.691478 | `abs(candidate_s-current_b)%12 == 2 AND sign(candidate_s-prev_s) == negative AND sign(current_b-prev_b) == zero` |
| 4 | 19.586 | 0.012802 | 2.007 | 1.681672 | `abs(prev_s-prev_b)%12 == 9 AND abs(candidate_s-current_b)%12 == 0 AND LEARNED_PREDICATE_001 == true` |
| 5 | 18.141 | 0.010917 | 1.286 | 1.665593 | `abs(candidate_s-current_b)%12 == 8 AND sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 1` |
| 6 | 18.946 | 0.011924 | 2.043 | 1.658947 | `abs(candidate_s-current_b)%12 == 5 AND sign(candidate_s-prev_s) == positive AND sign(current_b-prev_b) == zero` |
| 7 | 17.103 | 0.009664 | 1.904 | 1.654483 | `abs(candidate_s-current_b)%12 == 6 AND sign(current_b-prev_b) == zero AND abs(candidate_s-prev_s) > 1` |
| 8 | 20.908 | 0.014611 | 2.771 | 1.646402 | `abs(candidate_s-current_b)%12 == 6 AND sign(candidate_s-prev_s) == zero AND sign(current_b-prev_b) == negative` |
| 9 | -14.214 | 0.006671 | -1.100 | 1.635745 | `sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 2` |
| 10 | 17.023 | 0.009548 | 0.534 | 1.631118 | `sign(candidate_s-prev_s) == positive AND sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 4` |
| 11 | -13.599 | 0.006116 | -1.172 | 1.628739 | `sign(current_b-prev_b) == zero AND abs(candidate_s-prev_s) > 2` |
| 12 | 15.745 | 0.008203 | 2.685 | 1.626783 | `abs(prev_s-prev_b)%12 == 4 AND abs(candidate_s-current_b)%12 == 9 AND sign(current_b-prev_b) == zero` |

## Scan uniforme des arrivées après saut en même direction

Les classes `0..11` sont testées symétriquement. Le premier z est le
marginal uniforme ; le second précède le raffinement de famille et
le troisième suit son éventuelle acceptation.

| Classe | z train uniforme | z validation uniforme | z train avant | z validation avant | z train après | z validation après |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | -18.512 | -8.368 | -6.291 | -3.741 | 0.792 | -1.034 |
| 1 | -20.407 | -9.012 | -1.278 | -0.786 | -1.429 | -0.838 |
| 2 | -20.032 | -8.895 | 1.667 | 0.830 | 1.226 | 0.628 |
| 3 | -9.324 | -5.044 | 3.227 | 0.431 | 1.930 | -0.104 |
| 4 | -11.379 | -5.695 | -1.870 | -1.334 | -2.963 | -1.796 |
| 5 | -20.591 | -8.997 | -3.745 | -1.368 | -3.980 | -1.482 |
| 6 | -19.505 | -8.514 | -0.909 | -0.082 | -1.241 | -0.243 |
| 7 | -15.037 | -7.134 | -3.319 | -2.345 | 1.336 | -0.515 |
| 8 | -15.271 | -5.471 | -6.126 | -0.410 | -6.587 | -0.652 |
| 9 | -17.502 | -7.844 | 0.367 | -0.224 | -0.446 | -0.551 |
| 10 | -20.886 | -9.105 | -2.873 | -0.473 | -3.063 | -0.607 |
| 11 | -20.925 | -9.238 | -2.125 | -0.944 | -2.261 | -1.006 |

## Bootstrap groupé par choral avant raffinement

Chaque réplication rééchantillonne des pièces entières avec remise.

| Classe | Train z médian [2,5 % ; 97,5 %] | Validation z médian [2,5 % ; 97,5 %] | P(z val. < 0) |
|---:|---:|---:|---:|
| 0 | -6.273 [-7.977 ; -4.264] | -3.792 [-4.743 ; -2.572] | 1.000 |
| 1 | -1.293 [-1.872 ; -0.130] | -0.786 [-0.822 ; -0.747] | 1.000 |
| 2 | 1.609 [-1.179 ; 5.296] | 0.779 [-1.405 ; 4.726] | 0.280 |
| 3 | 3.181 [0.649 ; 5.849] | 0.393 [-1.899 ; 3.434] | 0.387 |
| 4 | -1.891 [-4.055 ; 0.453] | -1.351 [-3.349 ; 0.626] | 0.905 |
| 5 | -3.833 [-4.533 ; -2.511] | -1.396 [-1.964 ; -0.216] | 0.983 |
| 6 | -0.912 [-2.556 ; 0.990] | -0.136 [-1.790 ; 2.024] | 0.616 |
| 7 | -3.438 [-5.525 ; -0.920] | -2.373 [-3.775 ; -0.703] | 0.996 |
| 8 | -6.142 [-7.742 ; -4.312] | -0.451 [-2.877 ; 2.765] | 0.619 |
| 9 | 0.335 [-2.023 ; 3.201] | -0.302 [-2.034 ; 1.937] | 0.625 |
| 10 | -2.870 [-2.995 ; -2.774] | -0.484 [-1.317 ; 1.211] | 0.723 |
| 11 | -2.121 [-2.210 ; -2.053] | -0.944 [-0.994 ; -0.894] | 1.000 |

## Raffinement uniforme de la famille

- Seuils : z train ≤ `-3.0` et z validation ≤ `-2.0`.
- Classes proposées : `[0, 7]`.
- Raffinement accepté : `True`.
- NLL validation avant : `1.627234`.
- NLL validation après : `1.624531`.

## Comparaison sémantique postérieure

| Classe | États valides testés | Positifs appris | Désaccords | Classification |
|---:|---:|---:|---:|---|
| 0 | 301401 | 9972 | 0 | `RECOVERED_EQUIVALENT` |
| 7 | 301401 | 9324 | 0 | `RECOVERED_EQUIVALENT` |

## Règles actives

| Type | Poids | Clause |
|---|---:|---|
| residual_interaction | 2.851 | `abs(candidate_s-current_b)%12 == 6 AND sign(candidate_s-prev_s) == zero AND sign(current_b-prev_b) == negative` |
| residual_interaction | 2.605 | `abs(prev_s-prev_b)%12 == 4 AND abs(candidate_s-current_b)%12 == 9 AND sign(current_b-prev_b) == zero` |
| residual_interaction | 2.526 | `abs(candidate_s-current_b)%12 == 2 AND sign(candidate_s-prev_s) == negative AND sign(current_b-prev_b) == zero` |
| residual_interaction | 2.295 | `abs(prev_s-prev_b)%12 == 7 AND abs(candidate_s-current_b)%12 == 0 AND LEARNED_PREDICATE_001 == true` |
| residual_interaction | 2.253 | `abs(candidate_s-current_b)%12 == 5 AND sign(candidate_s-prev_s) == positive AND sign(current_b-prev_b) == zero` |
| residual_interaction | 2.239 | `abs(prev_s-prev_b)%12 == 9 AND abs(candidate_s-current_b)%12 == 0 AND LEARNED_PREDICATE_001 == true` |
| residual_interaction | 2.107 | `abs(candidate_s-current_b)%12 == 6 AND sign(current_b-prev_b) == zero AND abs(candidate_s-prev_s) > 1` |
| baseline_main_effect | -2.005 | `abs(candidate_s-current_b)%12 == 1` |
| baseline_main_effect | -1.751 | `abs(candidate_s-current_b)%12 == 11` |
| baseline_main_effect | -1.683 | `abs(candidate_s-prev_s) > 2` |
| baseline_main_effect | 1.634 | `abs(candidate_s-current_b)%12 == 4` |
| baseline_main_effect | 1.590 | `abs(candidate_s-current_b)%12 == 3` |
| residual_interaction | 1.524 | `abs(candidate_s-current_b)%12 == 8 AND sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 1` |
| baseline_main_effect | 1.436 | `abs(candidate_s-current_b)%12 == 7` |
| baseline_main_effect | -1.418 | `abs(candidate_s-prev_s) > 7` |
| direct_family_refinement | -1.345 | `abs(candidate_s-current_b)%12 == 0 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| residual_interaction | -1.235 | `sign(current_b-prev_b) == zero AND abs(candidate_s-prev_s) > 2` |
| baseline_main_effect | -1.220 | `abs(candidate_s-prev_s) > 12` |
| residual_interaction | 1.201 | `abs(prev_s-prev_b)%12 == 0 AND sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 4` |
| residual_interaction | -1.125 | `sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 2` |
| baseline_main_effect | -1.116 | `abs(candidate_s-prev_s) > 4` |
| baseline_main_effect | -1.101 | `abs(candidate_s-current_b)%12 == 10` |
| baseline_main_effect | -1.037 | `abs(candidate_s-current_b)%12 == 2` |
| baseline_main_effect | -0.879 | `abs(candidate_s-current_b)%12 == 6` |
| baseline_main_effect | 0.798 | `abs(candidate_s-current_b)%12 == 0` |
| baseline_main_effect | -0.745 | `abs(candidate_s-current_b)%12 == 5` |
| direct_family_refinement | -0.590 | `abs(candidate_s-current_b)%12 == 7 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| baseline_main_effect | 0.565 | `abs(candidate_s-current_b)%12 == 9` |
| baseline_main_effect | 0.533 | `abs(candidate_s-current_b)%12 == 8` |
| baseline_main_effect | -0.527 | `LEARNED_PREDICATE_001 == true` |
| baseline_main_effect | 0.376 | `abs(candidate_s-prev_s) > 1` |
| residual_interaction | 0.360 | `sign(candidate_s-prev_s) == positive AND sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 4` |
| baseline_main_effect | 0.245 | `sign(candidate_s-prev_s) == negative` |
| baseline_main_effect | -0.032 | `sign(candidate_s-prev_s) == positive` |
