# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Iteration2 | V7Refit |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 25.68 % | 24.05 % |
| Répétitions à la basse | 3.71 % | 4.82 % | 4.50 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 27.09 % | 31.15 % |
| Basse hors gamme naturelle globale | 7.14 % | 8.37 % | 8.60 % |
| Blocs triadiques (6 renversements) | 50.87 % | 51.41 % | 52.50 % |
| Blocs forts non triadiques | 26.91 % | 32.52 % | 26.96 % |
| Dissonances par bloc faible | 1.032 | 0.906 | 0.942 |
| Dissonances par bloc fort | 0.357 | 0.474 | 0.397 |
| {0,3,6,8} sur bloc fort | 1.40 % | 1.56 % | 1.89 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 3.38 % | 3.27 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### Iteration2

- Demi-tons à la basse : `+0.674 pp` (IC95 `-2.140` à `+3.488`).
- Répétitions à la basse : `+1.103 pp` (IC95 `-1.317` à `+3.523`).
- Sauts de basse > 4 demi-tons : `-0.782 pp` (IC95 `-4.571` à `+3.007`).
- Basse hors gamme naturelle globale : `+1.228 pp` (IC95 `-1.621` à `+4.077`).
- Blocs triadiques (6 renversements) : `+0.536 pp` (IC95 `-4.528` à `+5.599`).
- Blocs forts non triadiques : `+5.612 pp` (IC95 `-4.978` à `+16.201`).
- Dissonances par bloc faible : `-0.127` (IC95 `-0.271` à `+0.018`).
- Dissonances par bloc fort : `+0.117` (IC95 `-0.077` à `+0.310`).
- {0,3,6,8} sur bloc fort : `+0.156 pp` (IC95 `-1.859` à `+2.172`).
- {0,3,6,8} sur bloc faible : `+0.306 pp` (IC95 `-2.192` à `+2.803`).

### V7Refit

- Demi-tons à la basse : `-0.957 pp` (IC95 `-4.156` à `+2.243`).
- Répétitions à la basse : `+0.790 pp` (IC95 `-1.694` à `+3.274`).
- Sauts de basse > 4 demi-tons : `+3.276 pp` (IC95 `-0.453` à `+7.006`).
- Basse hors gamme naturelle globale : `+1.463 pp` (IC95 `-1.664` à `+4.589`).
- Blocs triadiques (6 renversements) : `+1.629 pp` (IC95 `-4.036` à `+7.294`).
- Blocs forts non triadiques : `+0.048 pp` (IC95 `-10.110` à `+10.206`).
- Dissonances par bloc faible : `-0.090` (IC95 `-0.196` à `+0.016`).
- Dissonances par bloc fort : `+0.041` (IC95 `-0.135` à `+0.217`).
- {0,3,6,8} sur bloc fort : `+0.482 pp` (IC95 `-1.229` à `+2.193`).
- {0,3,6,8} sur bloc faible : `+0.199 pp` (IC95 `-2.182` à `+2.579`).
