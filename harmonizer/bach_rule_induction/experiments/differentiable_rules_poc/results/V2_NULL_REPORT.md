# POC V2.1 — génération de colonnes résiduelle

## Protocole

- Corpus : 352 chorals, 20350 décisions disponibles.
- Train : 246 pièces / 14436 décisions.
- Validation : 53 pièces / 3029 décisions.
- Le jeu de test reste scellé et n'est pas chargé par ce programme.
- Contrôle nul : choix mélangés à l'intérieur des pièces.
- Direction des colonnes résiduelles : `both`.
- `LEARNED_PREDICATE_001` est réutilisé comme résultat du V1.

## Modèle parcimonieux

- NLL validation du socle : `2.651940`.
- Meilleur préfixe de colonnes : `2.643994`.
- NLL finale après élagage : `2.643938`.
- Clauses actives : 30, dont 11 interactions résiduelles et 0 raffinements de famille.

## Colonnes proposées

| Tour | z résiduel | Score pénalisé | Poids ajusté | NLL validation | Clause |
|---:|---:|---:|---:|---:|---|
| 1 | 10.116 | 0.003378 | 1.230 | 2.652297 | `abs(candidate_s-current_b)%12 == 6 AND sign(candidate_s-prev_s) == zero` |
| 2 | 7.612 | 0.001853 | 0.448 | 2.648706 | `abs(prev_s-prev_b)%12 == 8 AND sign(candidate_s-prev_s) == negative` |
| 3 | 7.165 | 0.001616 | 0.969 | 2.647312 | `abs(candidate_s-current_b)%12 == 1 AND sign(candidate_s-prev_s) == zero` |
| 4 | 6.185 | 0.001166 | 0.647 | 2.646715 | `abs(candidate_s-current_b)%12 == 4 AND sign(candidate_s-prev_s) == zero` |
| 5 | 5.914 | 0.000995 | 0.353 | 2.646327 | `abs(prev_s-prev_b)%12 == 0 AND sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 4` |
| 6 | 5.461 | 0.000815 | 0.852 | 2.646595 | `abs(prev_s-prev_b)%12 == 9 AND abs(candidate_s-current_b)%12 == 1 AND abs(candidate_s-prev_s) > 2` |
| 7 | 5.611 | 0.000884 | 1.305 | 2.646918 | `abs(prev_s-prev_b)%12 == 8 AND abs(candidate_s-current_b)%12 == 1 AND sign(current_b-prev_b) == zero` |
| 8 | -5.249 | 0.000806 | -0.546 | 2.645782 | `abs(candidate_s-current_b)%12 == 0 AND sign(candidate_s-prev_s) == zero` |
| 9 | -5.392 | 0.000795 | -0.416 | 2.645292 | `abs(prev_s-prev_b)%12 == 3 AND sign(candidate_s-prev_s) == positive AND sign(current_b-prev_b) == positive` |
| 10 | -5.179 | 0.000710 | -0.285 | 2.644343 | `abs(prev_s-prev_b)%12 == 4 AND sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 1` |
| 11 | 5.216 | 0.000735 | 0.952 | 2.643994 | `abs(prev_s-prev_b)%12 == 4 AND abs(candidate_s-current_b)%12 == 11 AND sign(current_b-prev_b) == zero` |
| 12 | 4.870 | 0.000605 | 0.805 | 2.644165 | `abs(prev_s-prev_b)%12 == 4 AND abs(candidate_s-current_b)%12 == 1 AND LEARNED_PREDICATE_001 == true` |

## Scan uniforme des arrivées après saut en même direction

Les classes `0..11` sont testées symétriquement. Le premier z est le
marginal uniforme ; le second précède le raffinement de famille et
le troisième suit son éventuelle acceptation.

| Classe | z train uniforme | z validation uniforme | z train avant | z validation avant | z train après | z validation après |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | -1.963 | -0.684 | -1.871 | -0.840 | -1.871 | -0.840 |
| 1 | -14.918 | -6.727 | 1.051 | 0.711 | 1.051 | 0.711 |
| 2 | -5.727 | -1.969 | -1.251 | 0.209 | -1.251 | 0.209 |
| 3 | -7.971 | -5.122 | -1.486 | -2.286 | -1.486 | -2.286 |
| 4 | -9.661 | -3.842 | -2.645 | -0.189 | -2.645 | -0.189 |
| 5 | 1.580 | -0.875 | 2.539 | -0.315 | 2.539 | -0.315 |
| 6 | -13.646 | -7.140 | 0.088 | -1.444 | 0.088 | -1.444 |
| 7 | 4.447 | 0.733 | 2.434 | -0.157 | 2.434 | -0.157 |
| 8 | -11.147 | -5.087 | -3.289 | -1.265 | -3.289 | -1.265 |
| 9 | -5.036 | -2.591 | -0.124 | -0.245 | -0.124 | -0.245 |
| 10 | -6.236 | -4.756 | -0.111 | -2.490 | -0.111 | -2.490 |
| 11 | -12.100 | -4.498 | 0.629 | 1.823 | 0.629 | 1.823 |

## Raffinement uniforme de la famille

- Seuils : z train ≤ `-3.0` et z validation ≤ `-2.0`.
- Classes proposées : `[]`.
- Raffinement accepté : `False`.
- NLL validation avant : `2.643938`.
- NLL validation après : `nan`.

## Comparaison sémantique postérieure

| Classe | États valides testés | Positifs appris | Désaccords | Classification |
|---:|---:|---:|---:|---|

## Règles actives

| Type | Poids | Clause |
|---|---:|---|
| baseline_main_effect | -1.601 | `abs(candidate_s-prev_s) > 12` |
| residual_interaction | 1.291 | `abs(prev_s-prev_b)%12 == 8 AND abs(candidate_s-current_b)%12 == 1 AND sign(current_b-prev_b) == zero` |
| residual_interaction | 1.266 | `abs(candidate_s-current_b)%12 == 6 AND sign(candidate_s-prev_s) == zero` |
| baseline_main_effect | -1.244 | `abs(candidate_s-prev_s) > 7` |
| residual_interaction | 0.969 | `abs(candidate_s-current_b)%12 == 1 AND sign(candidate_s-prev_s) == zero` |
| residual_interaction | 0.943 | `abs(prev_s-prev_b)%12 == 4 AND abs(candidate_s-current_b)%12 == 11 AND sign(current_b-prev_b) == zero` |
| residual_interaction | 0.874 | `abs(prev_s-prev_b)%12 == 9 AND abs(candidate_s-current_b)%12 == 1 AND abs(candidate_s-prev_s) > 2` |
| baseline_main_effect | -0.851 | `abs(candidate_s-current_b)%12 == 1` |
| baseline_main_effect | 0.695 | `abs(candidate_s-current_b)%12 == 0` |
| baseline_main_effect | 0.650 | `abs(candidate_s-current_b)%12 == 7` |
| baseline_main_effect | 0.649 | `abs(candidate_s-prev_s) > 1` |
| baseline_main_effect | -0.597 | `abs(candidate_s-current_b)%12 == 6` |
| baseline_main_effect | -0.569 | `sign(candidate_s-prev_s) == negative` |
| residual_interaction | 0.554 | `abs(candidate_s-current_b)%12 == 4 AND sign(candidate_s-prev_s) == zero` |
| residual_interaction | -0.552 | `abs(candidate_s-current_b)%12 == 0 AND sign(candidate_s-prev_s) == zero` |
| baseline_main_effect | 0.542 | `abs(candidate_s-current_b)%12 == 5` |
| baseline_main_effect | 0.535 | `sign(candidate_s-prev_s) == zero` |
| baseline_main_effect | -0.501 | `abs(candidate_s-prev_s) > 2` |
| residual_interaction | 0.492 | `abs(prev_s-prev_b)%12 == 8 AND sign(candidate_s-prev_s) == negative` |
| baseline_main_effect | -0.479 | `sign(candidate_s-prev_s) == positive` |
| residual_interaction | -0.469 | `abs(prev_s-prev_b)%12 == 3 AND sign(candidate_s-prev_s) == positive AND sign(current_b-prev_b) == positive` |
| baseline_main_effect | 0.420 | `abs(candidate_s-current_b)%12 == 2` |
| baseline_main_effect | -0.407 | `abs(candidate_s-prev_s) > 4` |
| baseline_main_effect | 0.360 | `abs(candidate_s-current_b)%12 == 9` |
| baseline_main_effect | 0.309 | `abs(candidate_s-current_b)%12 == 10` |
| residual_interaction | -0.290 | `abs(prev_s-prev_b)%12 == 4 AND sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 1` |
| baseline_main_effect | -0.284 | `abs(candidate_s-current_b)%12 == 11` |
| residual_interaction | 0.270 | `abs(prev_s-prev_b)%12 == 0 AND sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 4` |
| baseline_main_effect | 0.229 | `abs(candidate_s-current_b)%12 == 3` |
| baseline_main_effect | 0.117 | `abs(candidate_s-current_b)%12 == 4` |
