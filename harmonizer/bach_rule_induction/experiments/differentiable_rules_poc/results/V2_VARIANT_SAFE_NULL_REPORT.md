# POC V2.1 — génération de colonnes résiduelle

## Protocole

- Corpus : 352 chorals, 20350 décisions disponibles.
- Train : 251 pièces / 14744 décisions.
- Validation : 50 pièces / 2807 décisions.
- Partage : `exact_soprano_contour_and_rhythm_conservative_grouping`.
- Le jeu de test reste scellé et n'est pas chargé par ce programme.
- Contrôle nul : choix mélangés à l'intérieur des pièces.
- Direction des colonnes résiduelles : `both`.
- `LEARNED_PREDICATE_001` est réutilisé comme résultat du V1.

## Modèle parcimonieux

- NLL validation du socle : `2.655890`.
- Meilleur préfixe de colonnes : `2.648323`.
- NLL finale après élagage : `2.648323`.
- Clauses actives : 33, dont 12 interactions résiduelles et 0 raffinements de famille.

## Colonnes proposées

| Tour | z résiduel | Score pénalisé | Poids ajusté | NLL validation | Clause |
|---:|---:|---:|---:|---:|---|
| 1 | 8.727 | 0.002424 | 1.121 | 2.655833 | `abs(candidate_s-current_b)%12 == 6 AND sign(candidate_s-prev_s) == zero` |
| 2 | 7.439 | 0.001719 | 0.966 | 2.653317 | `abs(candidate_s-current_b)%12 == 1 AND sign(candidate_s-prev_s) == zero` |
| 3 | 7.198 | 0.001606 | 0.425 | 2.651627 | `abs(prev_s-prev_b)%12 == 8 AND sign(candidate_s-prev_s) == negative` |
| 4 | -6.609 | 0.001266 | -0.348 | 2.651043 | `abs(prev_s-prev_b)%12 == 4 AND sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 1` |
| 5 | 5.784 | 0.000932 | 1.227 | 2.650433 | `abs(prev_s-prev_b)%12 == 8 AND abs(candidate_s-current_b)%12 == 1 AND sign(current_b-prev_b) == zero` |
| 6 | 5.722 | 0.000950 | 0.595 | 2.649731 | `abs(candidate_s-current_b)%12 == 8 AND sign(candidate_s-prev_s) == zero` |
| 7 | 5.938 | 0.000944 | 0.699 | 2.649139 | `abs(candidate_s-current_b)%12 == 1 AND sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 2` |
| 8 | 5.499 | 0.000822 | 1.042 | 2.648854 | `abs(prev_s-prev_b)%12 == 7 AND abs(candidate_s-current_b)%12 == 11 AND sign(candidate_s-prev_s) == zero` |
| 9 | 5.199 | 0.000695 | 0.775 | 2.648674 | `abs(prev_s-prev_b)%12 == 9 AND abs(candidate_s-current_b)%12 == 1 AND abs(candidate_s-prev_s) > 2` |
| 10 | 4.963 | 0.000670 | 0.365 | 2.648821 | `abs(prev_s-prev_b)%12 == 0 AND abs(candidate_s-prev_s) > 7` |
| 11 | -4.823 | 0.000601 | -0.419 | 2.650052 | `abs(candidate_s-current_b)%12 == 10 AND sign(candidate_s-prev_s) == negative` |
| 12 | 4.578 | 0.000551 | 0.238 | 2.648323 | `abs(prev_s-prev_b)%12 == 3 AND sign(candidate_s-prev_s) == negative` |

## Scan uniforme des arrivées après saut en même direction

Les classes `0..11` sont testées symétriquement. Le premier z est le
marginal uniforme ; le second précède le raffinement de famille et
le troisième suit son éventuelle acceptation.

| Classe | z train uniforme | z validation uniforme | z train avant | z validation avant | z train après | z validation après |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | -0.368 | -0.629 | 0.754 | -0.383 | 0.754 | -0.383 |
| 1 | -14.708 | -6.098 | -0.730 | 0.305 | -0.730 | 0.305 |
| 2 | -6.435 | -1.955 | -1.188 | 0.540 | -1.188 | 0.540 |
| 3 | -9.168 | -4.004 | -2.081 | -0.662 | -2.081 | -0.662 |
| 4 | -9.345 | -4.999 | -2.595 | -1.984 | -2.595 | -1.984 |
| 5 | 0.611 | 0.231 | 1.536 | 0.982 | 1.536 | 0.982 |
| 6 | -13.722 | -5.908 | 0.913 | 0.726 | 0.913 | 0.726 |
| 7 | 5.399 | 1.605 | 1.424 | -0.032 | 1.424 | -0.032 |
| 8 | -11.708 | -4.279 | -3.111 | 0.016 | -3.111 | 0.016 |
| 9 | -6.597 | -2.410 | -0.708 | 0.370 | -0.708 | 0.370 |
| 10 | -6.810 | -2.610 | -0.930 | -0.092 | -0.930 | -0.092 |
| 11 | -11.843 | -5.485 | 0.847 | -0.181 | 0.847 | -0.181 |

## Bootstrap groupé par choral avant raffinement

Chaque réplication rééchantillonne des pièces entières avec remise.

| Classe | Train z médian [2,5 % ; 97,5 %] | Validation z médian [2,5 % ; 97,5 %] | P(z val. < 0) |
|---:|---:|---:|---:|
| 0 | 0.768 [-1.287 ; 2.794] | -0.365 [-2.107 ; 1.523] | 0.642 |
| 1 | -0.753 [-2.658 ; 1.454] | 0.238 [-1.655 ; 2.442] | 0.410 |
| 2 | -1.168 [-3.284 ; 0.927] | 0.582 [-1.208 ; 2.370] | 0.272 |
| 3 | -2.055 [-3.972 ; -0.330] | -0.692 [-2.662 ; 1.433] | 0.740 |
| 4 | -2.598 [-4.494 ; -0.525] | -2.033 [-3.700 ; -0.012] | 0.975 |
| 5 | 1.476 [-0.572 ; 3.532] | 0.987 [-0.853 ; 2.914] | 0.140 |
| 6 | 0.889 [-1.353 ; 3.128] | 0.721 [-1.477 ; 3.259] | 0.270 |
| 7 | 1.342 [-0.504 ; 3.504] | -0.034 [-1.837 ; 1.839] | 0.507 |
| 8 | -3.079 [-4.839 ; -1.062] | -0.003 [-1.918 ; 1.922] | 0.502 |
| 9 | -0.822 [-2.618 ; 1.424] | 0.328 [-1.633 ; 2.477] | 0.370 |
| 10 | -0.978 [-2.931 ; 1.026] | -0.105 [-1.954 ; 1.779] | 0.540 |
| 11 | 0.885 [-1.020 ; 2.751] | -0.147 [-1.782 ; 1.603] | 0.570 |

## Raffinement uniforme de la famille

- Seuils : z train ≤ `-3.0` et z validation ≤ `-2.0`.
- Classes proposées : `[]`.
- Raffinement accepté : `False`.
- NLL validation avant : `2.648323`.
- NLL validation après : `nan`.

## Comparaison sémantique postérieure

| Classe | États valides testés | Positifs appris | Désaccords | Classification |
|---:|---:|---:|---:|---|

## Règles actives

| Type | Poids | Clause |
|---|---:|---|
| residual_interaction | 1.650 | `abs(prev_s-prev_b)%12 == 8 AND abs(candidate_s-current_b)%12 == 1 AND sign(current_b-prev_b) == zero` |
| baseline_main_effect | -1.567 | `abs(candidate_s-prev_s) > 12` |
| residual_interaction | 1.465 | `abs(candidate_s-current_b)%12 == 1 AND sign(candidate_s-prev_s) == zero` |
| baseline_main_effect | -1.296 | `abs(candidate_s-prev_s) > 7` |
| residual_interaction | 1.264 | `abs(candidate_s-current_b)%12 == 6 AND sign(candidate_s-prev_s) == zero` |
| residual_interaction | 1.038 | `abs(prev_s-prev_b)%12 == 7 AND abs(candidate_s-current_b)%12 == 11 AND sign(candidate_s-prev_s) == zero` |
| baseline_main_effect | -1.037 | `abs(candidate_s-current_b)%12 == 1` |
| residual_interaction | 0.804 | `abs(prev_s-prev_b)%12 == 9 AND abs(candidate_s-current_b)%12 == 1 AND abs(candidate_s-prev_s) > 2` |
| baseline_main_effect | -0.697 | `abs(candidate_s-current_b)%12 == 6` |
| residual_interaction | 0.693 | `abs(candidate_s-current_b)%12 == 8 AND sign(candidate_s-prev_s) == zero` |
| baseline_main_effect | 0.691 | `abs(candidate_s-current_b)%12 == 7` |
| residual_interaction | 0.686 | `abs(candidate_s-current_b)%12 == 1 AND sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 2` |
| baseline_main_effect | 0.644 | `abs(candidate_s-prev_s) > 1` |
| baseline_main_effect | 0.617 | `abs(candidate_s-current_b)%12 == 0` |
| residual_interaction | 0.517 | `abs(prev_s-prev_b)%12 == 8 AND sign(candidate_s-prev_s) == negative` |
| baseline_main_effect | 0.510 | `abs(candidate_s-current_b)%12 == 5` |
| baseline_main_effect | -0.502 | `abs(candidate_s-prev_s) > 2` |
| baseline_main_effect | -0.480 | `sign(candidate_s-prev_s) == negative` |
| baseline_main_effect | 0.459 | `abs(candidate_s-current_b)%12 == 10` |
| baseline_main_effect | 0.437 | `sign(candidate_s-prev_s) == zero` |
| residual_interaction | -0.423 | `abs(candidate_s-current_b)%12 == 10 AND sign(candidate_s-prev_s) == negative` |
| baseline_main_effect | -0.397 | `sign(candidate_s-prev_s) == positive` |
| baseline_main_effect | -0.392 | `abs(candidate_s-prev_s) > 4` |
| residual_interaction | -0.378 | `abs(prev_s-prev_b)%12 == 4 AND sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 1` |
| residual_interaction | 0.361 | `abs(prev_s-prev_b)%12 == 0 AND abs(candidate_s-prev_s) > 7` |
| baseline_main_effect | 0.353 | `abs(candidate_s-current_b)%12 == 2` |
| baseline_main_effect | -0.292 | `abs(candidate_s-current_b)%12 == 11` |
| baseline_main_effect | 0.242 | `abs(candidate_s-current_b)%12 == 9` |
| residual_interaction | 0.238 | `abs(prev_s-prev_b)%12 == 3 AND sign(candidate_s-prev_s) == negative` |
| baseline_main_effect | 0.169 | `abs(candidate_s-current_b)%12 == 3` |
| baseline_main_effect | 0.128 | `abs(candidate_s-current_b)%12 == 4` |
| baseline_main_effect | -0.110 | `abs(candidate_s-current_b)%12 == 8` |
| baseline_main_effect | -0.074 | `LEARNED_PREDICATE_001 == true` |
