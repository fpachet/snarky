# V20C — couverture train des transitions de fondamentales nommées

Cet audit est effectué avant toute extension de la grammaire. Il ne
sélectionne aucune règle et n'apprend aucun poids.

## Test de nouveauté

- Chorals de train : `251`.
- Arêtes entre blocs voisins : `24201`.
- Deux analyses nommées uniques : `58.33 %`.
- Changement de fondamentale parmi ces arêtes : `76.86 %`.
- Transition de fondamentales différente de la transition de basses : `67.58 %`.
- Cellules observées : `209`.
- Cellules avec ≥100 occurrences et ≥10 chorals : `42`.

Le dernier pourcentage mesure directement ce que cette représentation
ajoute à l'expérience V13 : dans un renversement, la fondamentale
analysée n'est pas la note de basse.

## Changements de fondamentale les plus enrichis

| Mode | Degré précédent → courant | Blocs | Chorals | P(courant|précédent) | lift log2 |
|---|---:|---:|---:|---:|---:|
| minor | 10 → 3 | 348 | 113 | 36.67 % | +1.54 |
| major | 4 → 9 | 184 | 88 | 33.45 % | +1.45 |
| major | 2 → 11 | 128 | 71 | 13.81 % | +1.32 |
| minor | 3 → 8 | 164 | 76 | 18.16 % | +1.32 |
| minor | 2 → 7 | 212 | 75 | 40.08 % | +1.29 |
| major | 9 → 2 | 242 | 95 | 29.95 % | +1.11 |
| major | 4 → 5 | 112 | 66 | 20.36 % | +1.03 |
| major | 11 → 0 | 190 | 91 | 50.94 % | +1.02 |
| minor | 7 → 0 | 563 | 121 | 43.75 % | +0.99 |
| major | 0 → 5 | 292 | 100 | 18.42 % | +0.88 |
| minor | 2 → 3 | 123 | 65 | 23.25 % | +0.88 |
| minor | 0 → 2 | 226 | 95 | 13.79 % | +0.85 |
| minor | 5 → 10 | 264 | 107 | 21.66 % | +0.85 |
| major | 2 → 7 | 361 | 111 | 38.94 % | +0.83 |
| major | 7 → 0 | 695 | 121 | 43.93 % | +0.81 |
| minor | 0 → 5 | 437 | 115 | 26.66 % | +0.70 |
| major | 2 → 4 | 109 | 62 | 11.76 % | +0.49 |
| minor | 7 → 8 | 129 | 69 | 10.02 % | +0.46 |
| major | 5 → 7 | 176 | 88 | 27.33 % | +0.32 |
| minor | 3 → 5 | 185 | 85 | 20.49 % | +0.31 |
| major | 0 → 2 | 272 | 103 | 17.16 % | +0.30 |
| minor | 5 → 2 | 112 | 56 | 9.19 % | +0.27 |
| minor | 5 → 7 | 226 | 101 | 18.54 % | +0.18 |
| major | 7 → 4 | 127 | 70 | 8.03 % | -0.06 |

Ces enrichissements ne sont pas encore des règles : ils servent
uniquement à décider si la famille est couverte, distincte de V13
et assez parcimonieuse pour être soumise à l'induction exacte.
