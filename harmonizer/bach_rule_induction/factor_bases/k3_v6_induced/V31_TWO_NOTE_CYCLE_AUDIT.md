# V31 — audit des cycles de deux notes

Les calculs portent uniquement sur les notes attaquées. Une tenue ne
compte pas comme répétition. `ABA` est un retour à retard 2 ; `ABAB`
et au-delà sont des continuations du même cycle.

## BWV 108.6 apparié

| Voix | Mesure | Bach | V28 | V29 |
|---|---|---:|---:|---:|
| Soprano | Retours ABA | 27.869 % | 27.869 % | 27.869 % |
| Soprano | Continuations ABAB | 6.667 % | 6.667 % | 6.667 % |
| Soprano | Runs ≥ 4 | 4.000 | 4.000 | 4.000 |
| Soprano | Longueur maximale | 4.000 | 4.000 | 4.000 |
| Alto | Retours ABA | 9.524 % | 17.460 % | 25.397 % |
| Alto | Continuations ABAB | 3.226 % | 8.065 % | 16.129 % |
| Alto | Runs ≥ 4 | 1.000 | 3.000 | 4.000 |
| Alto | Longueur maximale | 5.000 | 5.000 | 8.000 |
| Tenor | Retours ABA | 4.348 % | 18.841 % | 28.986 % |
| Tenor | Continuations ABAB | 0.000 % | 8.824 % | 13.235 % |
| Tenor | Runs ≥ 4 | 0.000 | 3.000 | 5.000 |
| Tenor | Longueur maximale | 3.000 | 5.000 | 6.000 |
| Bass | Retours ABA | 2.198 % | 48.352 % | 37.363 % |
| Bass | Continuations ABAB | 0.000 % | 23.333 % | 13.333 % |
| Bass | Runs ≥ 4 | 0.000 | 9.000 | 7.000 |
| Bass | Longueur maximale | 3.000 | 8.000 | 5.000 |

## Corpus Bach réservé

| Split | Voix | Retours ABA | Continuations ABAB | Runs ≥ 4 | Max |
|---|---|---:|---:|---:|---:|
| train32 | Soprano | 16.205 % | 2.294 % | 37 | 6 |
| train32 | Alto | 14.600 % | 2.060 % | 41 | 6 |
| train32 | Tenor | 13.831 % | 2.108 % | 39 | 5 |
| train32 | Bass | 10.908 % | 0.967 % | 23 | 4 |
| validation50 | Soprano | 16.547 % | 2.120 % | 55 | 5 |
| validation50 | Alto | 16.065 % | 2.510 % | 67 | 8 |
| validation50 | Tenor | 15.149 % | 2.577 % | 67 | 6 |
| validation50 | Bass | 11.515 % | 1.085 % | 36 | 5 |

Cet audit est descriptif : aucun poids ni seuil n'est ajusté.
