# POC V2.3 — parallèles dans les six paires de voix

## Protocole

- Train groupé : 251 chorals / 68491 décisions SATB.
- Validation groupée : 50 chorals / 13249 décisions SATB.
- Test réservé : 51 chorals, non ouvert.
- Données authentiques.
- Les douze classes numériques sont testées avec le même prédicat.

## Scan résiduel

| Classe | z train | z validation | Contraste local train/val. | Bootstrap val. médian [2,5 % ; 97,5 %] | P(z val. < 0) |
|---:|---:|---:|---:|---:|---:|
| 0 | -48.430 | -21.588 | 13.731 / 13.835 | -21.560 [-23.154 ; -19.864] | 1.000 |
| 1 | -3.295 | -1.566 | -15.146 / -15.317 | -1.555 [-2.017 ; -1.086] | 1.000 |
| 2 | -0.241 | -0.353 | 8.190 / 8.219 | -0.356 [-2.273 ; 1.632] | 0.648 |
| 3 | 16.215 | 6.102 | 0.227 / 0.217 | 6.139 [2.433 ; 10.065] | 0.000 |
| 4 | -7.512 | -2.963 | -0.160 / -0.146 | -3.068 [-6.314 ; 0.415] | 0.962 |
| 5 | -5.233 | -1.723 | 0.605 / 0.733 | -1.847 [-4.275 ; 0.836] | 0.901 |
| 6 | -11.894 | -5.609 | -0.217 / -0.358 | -5.657 [-6.771 ; -4.312] | 1.000 |
| 7 | -45.585 | -20.314 | -1.239 / -1.277 | -20.364 [-22.027 ; -18.610] | 1.000 |
| 8 | -10.113 | -5.286 | 0.697 / 0.754 | -5.356 [-8.196 ; -2.060] | 1.000 |
| 9 | 5.223 | -0.147 | 0.835 / 0.645 | -0.243 [-3.213 ; 3.018] | 0.566 |
| 10 | -8.759 | -3.386 | 6.985 / 7.218 | -3.452 [-4.597 ; -2.106] | 1.000 |
| 11 | -3.388 | -1.335 | -14.506 / -14.523 | -1.330 [-1.594 ; -1.080] | 1.000 |

## Sélection automatique

- Classes retenues : `[0, 7]`.

## Comparaison sémantique postérieure

| Classe | Référence | États testés | Désaccords | Classification |
|---:|---|---:|---:|---|
| 0 | `R-PARALLEL-001` | 1130364 | 0 | `RECOVERED_EQUIVALENT` |
| 7 | `R-PARALLEL-002` | 1130364 | 0 | `RECOVERED_EQUIVALENT` |
