# Audit génératif explicite de la basse et des sonorités

`20` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V13 | V16-050 | V16-025 | V16-0125 |
|---|---:|---:|---:|---:|---:|
| Demi-tons à la basse | 25.37 % | 26.51 % | 26.63 % | 26.70 % | 26.64 % |
| Répétitions à la basse | 3.41 % | 3.74 % | 4.78 % | 4.34 % | 3.87 % |
| Sauts de basse > 4 demi-tons | 27.95 % | 29.63 % | 30.86 % | 30.90 % | 30.84 % |
| Basse hors gamme naturelle globale | 8.61 % | 12.91 % | 12.51 % | 12.46 % | 12.54 % |
| Blocs triadiques (6 renversements) | 52.37 % | 50.96 % | 51.89 % | 51.80 % | 51.84 % |
| Blocs forts non triadiques | 27.56 % | 40.16 % | 41.11 % | 39.98 % | 39.52 % |
| Dissonances par bloc faible | 0.962 | 0.906 | 0.876 | 0.878 | 0.884 |
| Dissonances par bloc fort | 0.381 | 0.600 | 0.640 | 0.618 | 0.598 |
| {0,3,6,8} sur bloc fort | 1.60 % | 3.26 % | 2.81 % | 3.17 % | 3.16 % |
| {0,3,6,8} sur bloc faible | 3.14 % | 3.40 % | 3.33 % | 3.02 % | 3.19 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V13

- Demi-tons à la basse : `+1.140 pp` (IC95 `-0.971` à `+3.251`).
- Répétitions à la basse : `+0.330 pp` (IC95 `-1.144` à `+1.804`).
- Sauts de basse > 4 demi-tons : `+1.680 pp` (IC95 `-0.951` à `+4.311`).
- Basse hors gamme naturelle globale : `+4.302 pp` (IC95 `+2.006` à `+6.598`).
- Blocs triadiques (6 renversements) : `-1.402 pp` (IC95 `-4.350` à `+1.546`).
- Blocs forts non triadiques : `+12.607 pp` (IC95 `+5.736` à `+19.477`).
- Dissonances par bloc faible : `-0.056` (IC95 `-0.127` à `+0.015`).
- Dissonances par bloc fort : `+0.219` (IC95 `+0.103` à `+0.335`).
- {0,3,6,8} sur bloc fort : `+1.659 pp` (IC95 `+0.137` à `+3.182`).
- {0,3,6,8} sur bloc faible : `+0.262 pp` (IC95 `-1.048` à `+1.572`).

### V16-050

- Demi-tons à la basse : `+1.258 pp` (IC95 `-0.950` à `+3.465`).
- Répétitions à la basse : `+1.362 pp` (IC95 `-0.134` à `+2.858`).
- Sauts de basse > 4 demi-tons : `+2.910 pp` (IC95 `-0.264` à `+6.084`).
- Basse hors gamme naturelle globale : `+3.901 pp` (IC95 `+1.342` à `+6.460`).
- Blocs triadiques (6 renversements) : `-0.473 pp` (IC95 `-3.565` à `+2.619`).
- Blocs forts non triadiques : `+13.550 pp` (IC95 `+7.335` à `+19.766`).
- Dissonances par bloc faible : `-0.086` (IC95 `-0.166` à `-0.006`).
- Dissonances par bloc fort : `+0.258` (IC95 `+0.152` à `+0.364`).
- {0,3,6,8} sur bloc fort : `+1.217 pp` (IC95 `-0.106` à `+2.540`).
- {0,3,6,8} sur bloc faible : `+0.197 pp` (IC95 `-1.029` à `+1.424`).

### V16-025

- Demi-tons à la basse : `+1.336 pp` (IC95 `-1.186` à `+3.857`).
- Répétitions à la basse : `+0.921 pp` (IC95 `-0.627` à `+2.470`).
- Sauts de basse > 4 demi-tons : `+2.946 pp` (IC95 `+0.054` à `+5.838`).
- Basse hors gamme naturelle globale : `+3.853 pp` (IC95 `+1.646` à `+6.059`).
- Blocs triadiques (6 renversements) : `-0.570 pp` (IC95 `-3.558` à `+2.418`).
- Blocs forts non triadiques : `+12.423 pp` (IC95 `+6.180` à `+18.666`).
- Dissonances par bloc faible : `-0.084` (IC95 `-0.157` à `-0.012`).
- Dissonances par bloc fort : `+0.236` (IC95 `+0.126` à `+0.346`).
- {0,3,6,8} sur bloc fort : `+1.571 pp` (IC95 `+0.006` à `+3.136`).
- {0,3,6,8} sur bloc faible : `-0.114 pp` (IC95 `-1.449` à `+1.222`).

### V16-0125

- Demi-tons à la basse : `+1.277 pp` (IC95 `-1.145` à `+3.699`).
- Répétitions à la basse : `+0.459 pp` (IC95 `-1.017` à `+1.934`).
- Sauts de basse > 4 demi-tons : `+2.892 pp` (IC95 `-0.293` à `+6.077`).
- Basse hors gamme naturelle globale : `+3.934 pp` (IC95 `+1.628` à `+6.240`).
- Blocs triadiques (6 renversements) : `-0.524 pp` (IC95 `-3.458` à `+2.411`).
- Blocs forts non triadiques : `+11.967 pp` (IC95 `+5.332` à `+18.602`).
- Dissonances par bloc faible : `-0.079` (IC95 `-0.149` à `-0.008`).
- Dissonances par bloc fort : `+0.217` (IC95 `+0.102` à `+0.332`).
- {0,3,6,8} sur bloc fort : `+1.564 pp` (IC95 `-0.043` à `+3.171`).
- {0,3,6,8} sur bloc faible : `+0.059 pp` (IC95 `-1.293` à `+1.411`).
