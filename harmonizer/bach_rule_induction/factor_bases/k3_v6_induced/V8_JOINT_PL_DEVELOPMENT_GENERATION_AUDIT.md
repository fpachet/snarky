# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Iteration2 | V8JointPL |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 25.03 % | 39.58 % |
| Répétitions à la basse | 3.71 % | 4.09 % | 4.82 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 28.67 % | 10.03 % |
| Basse hors gamme naturelle globale | 7.14 % | 8.06 % | 16.06 % |
| Blocs triadiques (6 renversements) | 50.87 % | 52.30 % | 49.54 % |
| Blocs forts non triadiques | 26.91 % | 29.26 % | 28.38 % |
| Dissonances par bloc faible | 1.032 | 0.926 | 1.072 |
| Dissonances par bloc fort | 0.357 | 0.411 | 0.412 |
| {0,3,6,8} sur bloc fort | 1.40 % | 1.13 % | 1.68 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 3.06 % | 3.74 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### Iteration2

- Demi-tons à la basse : `+0.031 pp` (IC95 `-2.973` à `+3.036`).
- Répétitions à la basse : `+0.376 pp` (IC95 `-2.016` à `+2.768`).
- Sauts de basse > 4 demi-tons : `+0.801 pp` (IC95 `-2.900` à `+4.503`).
- Basse hors gamme naturelle globale : `+0.921 pp` (IC95 `-1.706` à `+3.548`).
- Blocs triadiques (6 renversements) : `+1.427 pp` (IC95 `-3.380` à `+6.234`).
- Blocs forts non triadiques : `+2.348 pp` (IC95 `-8.636` à `+13.332`).
- Dissonances par bloc faible : `-0.106` (IC95 `-0.245` à `+0.033`).
- Dissonances par bloc fort : `+0.054` (IC95 `-0.144` à `+0.252`).
- {0,3,6,8} sur bloc fort : `-0.278 pp` (IC95 `-2.312` à `+1.756`).
- {0,3,6,8} sur bloc faible : `-0.013 pp` (IC95 `-2.538` à `+2.511`).

### V8JointPL

- Demi-tons à la basse : `+14.574 pp` (IC95 `+11.187` à `+17.962`).
- Répétitions à la basse : `+1.101 pp` (IC95 `-1.771` à `+3.973`).
- Sauts de basse > 4 demi-tons : `-17.838 pp` (IC95 `-20.266` à `-15.410`).
- Basse hors gamme naturelle globale : `+8.917 pp` (IC95 `+5.719` à `+12.115`).
- Blocs triadiques (6 renversements) : `-1.334 pp` (IC95 `-7.731` à `+5.063`).
- Blocs forts non triadiques : `+1.464 pp` (IC95 `-8.977` à `+11.906`).
- Dissonances par bloc faible : `+0.040` (IC95 `-0.111` à `+0.191`).
- Dissonances par bloc fort : `+0.055` (IC95 `-0.135` à `+0.246`).
- {0,3,6,8} sur bloc fort : `+0.280 pp` (IC95 `-1.863` à `+2.423`).
- {0,3,6,8} sur bloc faible : `+0.670 pp` (IC95 `-1.768` à `+3.108`).
