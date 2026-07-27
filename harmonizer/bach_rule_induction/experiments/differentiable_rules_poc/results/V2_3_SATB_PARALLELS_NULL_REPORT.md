# POC V2.3 — parallèles dans les six paires de voix

## Protocole

- Train groupé : 251 chorals / 68491 décisions SATB.
- Validation groupée : 50 chorals / 13249 décisions SATB.
- Test réservé : 51 chorals, non ouvert.
- Contrôle nul : choix mélangés par choral et par voix.
- Les douze classes numériques sont testées avec le même prédicat.

## Scan résiduel

| Classe | z train | z validation | Contraste local train/val. | Bootstrap val. médian [2,5 % ; 97,5 %] | P(z val. < 0) |
|---:|---:|---:|---:|---:|---:|
| 0 | -0.668 | -0.836 | 0.393 / 8.549 | -0.848 [-2.420 ; 0.629] | 0.865 |
| 1 | -0.358 | -1.991 | -0.116 / -17.105 | -1.966 [-2.392 ; -1.586] | 1.000 |
| 2 | 1.134 | -1.213 | 0.093 / 8.390 | -1.194 [-2.637 ; 0.213] | 0.951 |
| 3 | 2.249 | 0.685 | 0.112 / 0.277 | 0.697 [-1.319 ; 2.790] | 0.253 |
| 4 | -6.001 | -3.565 | -0.217 / -0.342 | -3.582 [-5.244 ; -1.884] | 1.000 |
| 5 | -0.479 | 1.652 | 0.069 / 0.260 | 1.662 [-0.334 ; 3.807] | 0.051 |
| 6 | 0.494 | -0.313 | 0.037 / -0.084 | -0.372 [-2.487 ; 2.098] | 0.627 |
| 7 | 0.365 | -0.624 | 0.120 / 0.061 | -0.606 [-2.241 ; 1.015] | 0.756 |
| 8 | -5.823 | -1.395 | -0.268 / -0.075 | -1.385 [-3.149 ; 0.495] | 0.934 |
| 9 | 0.435 | -1.305 | 0.233 / -0.066 | -1.289 [-2.648 ; 0.137] | 0.963 |
| 10 | -2.809 | 0.710 | 0.176 / 0.113 | 0.697 [-1.205 ; 2.649] | 0.235 |
| 11 | -2.780 | 0.109 | -0.632 / 0.020 | 0.052 [-2.001 ; 2.471] | 0.481 |

## Sélection automatique

- Classes retenues : `[]`.

## Comparaison sémantique postérieure

| Classe | Référence | États testés | Désaccords | Classification |
|---:|---|---:|---:|---|
