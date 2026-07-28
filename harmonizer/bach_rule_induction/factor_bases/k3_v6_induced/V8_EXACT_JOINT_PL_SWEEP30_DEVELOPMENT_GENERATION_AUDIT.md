# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `30` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Iteration2 | V8Central | V8Exact |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 26.27 % | 42.62 % | 29.57 % |
| Répétitions à la basse | 3.71 % | 4.41 % | 4.01 % | 6.75 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 28.29 % | 7.04 % | 18.98 % |
| Basse hors gamme naturelle globale | 7.14 % | 7.26 % | 15.40 % | 7.48 % |
| Blocs triadiques (6 renversements) | 50.87 % | 54.76 % | 51.82 % | 58.09 % |
| Blocs forts non triadiques | 26.91 % | 24.79 % | 23.89 % | 24.09 % |
| Dissonances par bloc faible | 1.032 | 0.908 | 1.041 | 0.882 |
| Dissonances par bloc fort | 0.357 | 0.346 | 0.359 | 0.341 |
| {0,3,6,8} sur bloc fort | 1.40 % | 0.91 % | 2.72 % | 3.13 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 3.80 % | 6.61 % | 5.33 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### Iteration2

- Demi-tons à la basse : `+1.266 pp` (IC95 `-2.575` à `+5.106`).
- Répétitions à la basse : `+0.697 pp` (IC95 `-0.948` à `+2.342`).
- Sauts de basse > 4 demi-tons : `+0.423 pp` (IC95 `-4.591` à `+5.438`).
- Basse hors gamme naturelle globale : `+0.115 pp` (IC95 `-2.437` à `+2.667`).
- Blocs triadiques (6 renversements) : `+3.894 pp` (IC95 `-1.883` à `+9.671`).
- Blocs forts non triadiques : `-2.119 pp` (IC95 `-12.643` à `+8.405`).
- Dissonances par bloc faible : `-0.124` (IC95 `-0.283` à `+0.035`).
- Dissonances par bloc fort : `-0.010` (IC95 `-0.204` à `+0.183`).
- {0,3,6,8} sur bloc fort : `-0.495 pp` (IC95 `-2.202` à `+1.212`).
- {0,3,6,8} sur bloc faible : `+0.729 pp` (IC95 `-1.982` à `+3.440`).

### V8Central

- Demi-tons à la basse : `+17.617 pp` (IC95 `+14.319` à `+20.915`).
- Répétitions à la basse : `+0.291 pp` (IC95 `-2.113` à `+2.694`).
- Sauts de basse > 4 demi-tons : `-20.826 pp` (IC95 `-22.871` à `-18.781`).
- Basse hors gamme naturelle globale : `+8.257 pp` (IC95 `+5.573` à `+10.941`).
- Blocs triadiques (6 renversements) : `+0.951 pp` (IC95 `-5.086` à `+6.989`).
- Blocs forts non triadiques : `-3.020 pp` (IC95 `-14.827` à `+8.788`).
- Dissonances par bloc faible : `+0.009` (IC95 `-0.124` à `+0.142`).
- Dissonances par bloc fort : `+0.003` (IC95 `-0.193` à `+0.198`).
- {0,3,6,8} sur bloc fort : `+1.315 pp` (IC95 `-0.157` à `+2.788`).
- {0,3,6,8} sur bloc faible : `+3.532 pp` (IC95 `+1.423` à `+5.641`).

### V8Exact

- Demi-tons à la basse : `+4.562 pp` (IC95 `+0.628` à `+8.497`).
- Répétitions à la basse : `+3.036 pp` (IC95 `+0.146` à `+5.926`).
- Sauts de basse > 4 demi-tons : `-8.886 pp` (IC95 `-12.885` à `-4.887`).
- Basse hors gamme naturelle globale : `+0.334 pp` (IC95 `-2.787` à `+3.454`).
- Blocs triadiques (6 renversements) : `+7.218 pp` (IC95 `+2.314` à `+12.122`).
- Blocs forts non triadiques : `-2.820 pp` (IC95 `-14.329` à `+8.690`).
- Dissonances par bloc faible : `-0.150` (IC95 `-0.283` à `-0.017`).
- Dissonances par bloc fort : `-0.016` (IC95 `-0.236` à `+0.204`).
- {0,3,6,8} sur bloc fort : `+1.723 pp` (IC95 `-0.606` à `+4.052`).
- {0,3,6,8} sur bloc faible : `+2.261 pp` (IC95 `-0.344` à `+4.867`).
