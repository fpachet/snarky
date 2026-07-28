# Audit génératif explicite de la basse et des sonorités

`50` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V6-train64 | V6-train248 |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.67 % | 27.87 % | 27.65 % |
| Répétitions à la basse | 3.37 % | 5.61 % | 4.90 % |
| Sauts de basse > 4 demi-tons | 26.76 % | 22.33 % | 22.70 % |
| Basse hors gamme naturelle globale | 8.15 % | 10.49 % | 10.55 % |
| Blocs triadiques (6 renversements) | 52.74 % | 51.46 % | 50.35 % |
| Blocs forts non triadiques | 28.72 % | 36.10 % | 37.45 % |
| Dissonances par bloc faible | 0.987 | 0.925 | 0.949 |
| Dissonances par bloc fort | 0.410 | 0.564 | 0.584 |
| {0,3,6,8} sur bloc fort | 2.17 % | 2.31 % | 2.64 % |
| {0,3,6,8} sur bloc faible | 2.93 % | 3.53 % | 3.50 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V6-train64

- Demi-tons à la basse : `+2.197 pp` (IC95 `+0.402` à `+3.993`).
- Répétitions à la basse : `+2.239 pp` (IC95 `+1.277` à `+3.201`).
- Sauts de basse > 4 demi-tons : `-4.422 pp` (IC95 `-6.495` à `-2.349`).
- Basse hors gamme naturelle globale : `+2.334 pp` (IC95 `+0.648` à `+4.020`).
- Blocs triadiques (6 renversements) : `-1.281 pp` (IC95 `-3.488` à `+0.926`).
- Blocs forts non triadiques : `+7.377 pp` (IC95 `+3.739` à `+11.014`).
- Dissonances par bloc faible : `-0.062` (IC95 `-0.150` à `+0.027`).
- Dissonances par bloc fort : `+0.154` (IC95 `+0.092` à `+0.216`).
- {0,3,6,8} sur bloc fort : `+0.138 pp` (IC95 `-0.859` à `+1.135`).
- {0,3,6,8} sur bloc faible : `+0.608 pp` (IC95 `-0.203` à `+1.419`).

### V6-train248

- Demi-tons à la basse : `+1.981 pp` (IC95 `+0.046` à `+3.916`).
- Répétitions à la basse : `+1.529 pp` (IC95 `+0.590` à `+2.468`).
- Sauts de basse > 4 demi-tons : `-4.052 pp` (IC95 `-6.139` à `-1.966`).
- Basse hors gamme naturelle globale : `+2.392 pp` (IC95 `+0.682` à `+4.102`).
- Blocs triadiques (6 renversements) : `-2.396 pp` (IC95 `-4.606` à `-0.187`).
- Blocs forts non triadiques : `+8.726 pp` (IC95 `+5.216` à `+12.236`).
- Dissonances par bloc faible : `-0.038` (IC95 `-0.116` à `+0.040`).
- Dissonances par bloc fort : `+0.174` (IC95 `+0.114` à `+0.235`).
- {0,3,6,8} sur bloc fort : `+0.470 pp` (IC95 `-0.596` à `+1.536`).
- {0,3,6,8} sur bloc faible : `+0.574 pp` (IC95 `-0.252` à `+1.400`).
