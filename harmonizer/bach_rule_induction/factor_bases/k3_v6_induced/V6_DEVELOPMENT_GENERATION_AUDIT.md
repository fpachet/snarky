# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `6` balayages. Même soprano,
rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V5.16 | V6 |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.73 % | 25.86 % | 39.41 % |
| Répétitions à la basse | 3.11 % | 5.06 % | 4.67 % |
| Sauts de basse > 4 demi-tons | 28.03 % | 24.94 % | 11.03 % |
| Basse hors gamme naturelle globale | 10.08 % | 8.32 % | 17.67 % |
| Blocs triadiques (6 renversements) | 53.86 % | 56.42 % | 46.41 % |
| Blocs forts non triadiques | 28.20 % | 23.71 % | 41.08 % |
| Dissonances par bloc faible | 0.893 | 0.879 | 1.017 |
| Dissonances par bloc fort | 0.406 | 0.345 | 0.663 |
| {0,3,6,8} sur bloc fort | 1.79 % | 1.86 % | 4.38 % |
| {0,3,6,8} sur bloc faible | 3.20 % | 4.24 % | 5.12 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V5.16

- Demi-tons à la basse : `+0.124 pp` (IC95 `-3.762` à `+4.010`).
- Répétitions à la basse : `+1.942 pp` (IC95 `-0.917` à `+4.801`).
- Sauts de basse > 4 demi-tons : `-3.093 pp` (IC95 `-7.255` à `+1.069`).
- Basse hors gamme naturelle globale : `-1.754 pp` (IC95 `-5.880` à `+2.371`).
- Blocs triadiques (6 renversements) : `+2.559 pp` (IC95 `-0.406` à `+5.523`).
- Blocs forts non triadiques : `-4.499 pp` (IC95 `-11.847` à `+2.848`).
- Dissonances par bloc faible : `-0.014` (IC95 `-0.112` à `+0.084`).
- Dissonances par bloc fort : `-0.061` (IC95 `-0.189` à `+0.067`).
- {0,3,6,8} sur bloc fort : `+0.068 pp` (IC95 `-2.625` à `+2.760`).
- {0,3,6,8} sur bloc faible : `+1.041 pp` (IC95 `-0.220` à `+2.301`).

### V6

- Demi-tons à la basse : `+13.682 pp` (IC95 `+10.086` à `+17.278`).
- Répétitions à la basse : `+1.556 pp` (IC95 `-0.991` à `+4.103`).
- Sauts de basse > 4 demi-tons : `-17.005 pp` (IC95 `-20.652` à `-13.359`).
- Basse hors gamme naturelle globale : `+7.594 pp` (IC95 `+2.996` à `+12.192`).
- Blocs triadiques (6 renversements) : `-7.451 pp` (IC95 `-10.959` à `-3.943`).
- Blocs forts non triadiques : `+12.877 pp` (IC95 `+4.244` à `+21.511`).
- Dissonances par bloc faible : `+0.124` (IC95 `+0.047` à `+0.202`).
- Dissonances par bloc fort : `+0.257` (IC95 `+0.118` à `+0.396`).
- {0,3,6,8} sur bloc fort : `+2.587 pp` (IC95 `-0.280` à `+5.454`).
- {0,3,6,8} sur bloc faible : `+1.928 pp` (IC95 `+0.210` à `+3.646`).
