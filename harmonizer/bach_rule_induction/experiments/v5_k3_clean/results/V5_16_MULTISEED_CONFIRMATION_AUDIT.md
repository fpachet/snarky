# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test fermé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V5.16 |
|---|---:|---:|
| Demi-tons à la basse | 25.73 % | 25.86 % |
| Répétitions à la basse | 3.11 % | 5.06 % |
| Sauts de basse > 4 demi-tons | 28.03 % | 24.94 % |
| Basse hors gamme naturelle globale | 10.08 % | 8.32 % |
| Blocs triadiques (6 renversements) | 53.86 % | 56.42 % |
| Blocs forts non triadiques | 28.20 % | 23.71 % |
| Dissonances par bloc faible | 0.893 | 0.879 |
| Dissonances par bloc fort | 0.406 | 0.345 |
| {0,3,6,8} sur bloc fort | 1.79 % | 1.86 % |
| {0,3,6,8} sur bloc faible | 3.20 % | 4.24 % |

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
