# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `5` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V23 | V24C |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 26.91 % | 27.28 % |
| Répétitions à la basse | 3.71 % | 3.73 % | 3.88 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 27.76 % | 27.97 % |
| Basse hors gamme naturelle globale | 7.14 % | 11.69 % | 12.11 % |
| Blocs triadiques (6 renversements) | 50.87 % | 49.42 % | 50.17 % |
| Blocs forts non triadiques | 26.91 % | 35.17 % | 32.02 % |
| Dissonances par bloc faible | 1.032 | 1.081 | 1.085 |
| Dissonances par bloc fort | 0.357 | 0.596 | 0.530 |
| {0,3,6,8} sur bloc fort | 1.40 % | 1.57 % | 1.59 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 3.86 % | 4.16 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V23

- Demi-tons à la basse : `+1.907 pp` (IC95 `-0.105` à `+3.918`).
- Répétitions à la basse : `+0.014 pp` (IC95 `-2.222` à `+2.250`).
- Sauts de basse > 4 demi-tons : `-0.116 pp` (IC95 `-2.962` à `+2.731`).
- Basse hors gamme naturelle globale : `+4.548 pp` (IC95 `+1.128` à `+7.968`).
- Blocs triadiques (6 renversements) : `-1.453 pp` (IC95 `-6.382` à `+3.477`).
- Blocs forts non triadiques : `+8.259 pp` (IC95 `-2.397` à `+18.915`).
- Dissonances par bloc faible : `+0.049` (IC95 `-0.054` à `+0.152`).
- Dissonances par bloc fort : `+0.240` (IC95 `+0.051` à `+0.428`).
- {0,3,6,8} sur bloc fort : `+0.170 pp` (IC95 `-1.663` à `+2.004`).
- {0,3,6,8} sur bloc faible : `+0.787 pp` (IC95 `-1.179` à `+2.754`).

### V24C

- Demi-tons à la basse : `+2.276 pp` (IC95 `-0.446` à `+4.997`).
- Répétitions à la basse : `+0.169 pp` (IC95 `-1.978` à `+2.317`).
- Sauts de basse > 4 demi-tons : `+0.098 pp` (IC95 `-1.884` à `+2.080`).
- Basse hors gamme naturelle globale : `+4.970 pp` (IC95 `+1.951` à `+7.989`).
- Blocs triadiques (6 renversements) : `-0.704 pp` (IC95 `-5.925` à `+4.516`).
- Blocs forts non triadiques : `+5.105 pp` (IC95 `-5.654` à `+15.863`).
- Dissonances par bloc faible : `+0.053` (IC95 `-0.059` à `+0.165`).
- Dissonances par bloc fort : `+0.173` (IC95 `-0.017` à `+0.364`).
- {0,3,6,8} sur bloc fort : `+0.185 pp` (IC95 `-1.658` à `+2.028`).
- {0,3,6,8} sur bloc faible : `+1.086 pp` (IC95 `-0.840` à `+3.012`).
