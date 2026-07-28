# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `6` balayages. Même soprano,
rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V6-refit |
|---|---:|---:|
| Demi-tons à la basse | 25.73 % | 25.29 % |
| Répétitions à la basse | 3.11 % | 6.87 % |
| Sauts de basse > 4 demi-tons | 28.03 % | 24.43 % |
| Basse hors gamme naturelle globale | 10.08 % | 9.31 % |
| Blocs triadiques (6 renversements) | 53.86 % | 53.66 % |
| Blocs forts non triadiques | 28.20 % | 34.79 % |
| Dissonances par bloc faible | 0.893 | 0.873 |
| Dissonances par bloc fort | 0.406 | 0.530 |
| {0,3,6,8} sur bloc fort | 1.79 % | 2.38 % |
| {0,3,6,8} sur bloc faible | 3.20 % | 3.50 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V6-refit

- Demi-tons à la basse : `-0.440 pp` (IC95 `-4.291` à `+3.411`).
- Répétitions à la basse : `+3.760 pp` (IC95 `+1.156` à `+6.364`).
- Sauts de basse > 4 demi-tons : `-3.600 pp` (IC95 `-7.179` à `-0.020`).
- Basse hors gamme naturelle globale : `-0.765 pp` (IC95 `-4.761` à `+3.231`).
- Blocs triadiques (6 renversements) : `-0.205 pp` (IC95 `-3.805` à `+3.394`).
- Blocs forts non triadiques : `+6.585 pp` (IC95 `-0.896` à `+14.067`).
- Dissonances par bloc faible : `-0.020` (IC95 `-0.097` à `+0.058`).
- Dissonances par bloc fort : `+0.124` (IC95 `+0.001` à `+0.247`).
- {0,3,6,8} sur bloc fort : `+0.593 pp` (IC95 `-1.771` à `+2.956`).
- {0,3,6,8} sur bloc faible : `+0.305 pp` (IC95 `-1.440` à `+2.049`).
