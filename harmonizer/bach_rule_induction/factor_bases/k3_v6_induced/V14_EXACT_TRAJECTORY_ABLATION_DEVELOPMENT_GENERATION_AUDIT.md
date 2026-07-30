# Audit génératif explicite de la basse et des sonorités

`20` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V13 | V14 | V14Ablated |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 25.37 % | 26.51 % | 28.89 % | 27.45 % |
| Répétitions à la basse | 3.41 % | 3.74 % | 4.14 % | 4.17 % |
| Sauts de basse > 4 demi-tons | 27.95 % | 29.63 % | 31.27 % | 32.31 % |
| Basse hors gamme naturelle globale | 8.61 % | 12.91 % | 13.09 % | 12.87 % |
| Blocs triadiques (6 renversements) | 52.37 % | 50.96 % | 49.73 % | 50.33 % |
| Blocs forts non triadiques | 27.56 % | 40.16 % | 44.66 % | 41.05 % |
| Dissonances par bloc faible | 0.962 | 0.906 | 0.899 | 0.898 |
| Dissonances par bloc fort | 0.381 | 0.600 | 0.697 | 0.598 |
| {0,3,6,8} sur bloc fort | 1.60 % | 3.26 % | 3.27 % | 2.74 % |
| {0,3,6,8} sur bloc faible | 3.14 % | 3.40 % | 3.46 % | 3.13 % |

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

### V14

- Demi-tons à la basse : `+3.524 pp` (IC95 `+1.018` à `+6.031`).
- Répétitions à la basse : `+0.722 pp` (IC95 `-0.971` à `+2.414`).
- Sauts de basse > 4 demi-tons : `+3.319 pp` (IC95 `+0.765` à `+5.873`).
- Basse hors gamme naturelle globale : `+4.484 pp` (IC95 `+1.944` à `+7.025`).
- Blocs triadiques (6 renversements) : `-2.632 pp` (IC95 `-6.495` à `+1.231`).
- Blocs forts non triadiques : `+17.103 pp` (IC95 `+10.027` à `+24.178`).
- Dissonances par bloc faible : `-0.063` (IC95 `-0.146` à `+0.020`).
- Dissonances par bloc fort : `+0.315` (IC95 `+0.195` à `+0.436`).
- {0,3,6,8} sur bloc fort : `+1.675 pp` (IC95 `-0.007` à `+3.357`).
- {0,3,6,8} sur bloc faible : `+0.323 pp` (IC95 `-0.930` à `+1.577`).

### V14Ablated

- Demi-tons à la basse : `+2.078 pp` (IC95 `-0.316` à `+4.472`).
- Répétitions à la basse : `+0.751 pp` (IC95 `-0.951` à `+2.453`).
- Sauts de basse > 4 demi-tons : `+4.355 pp` (IC95 `+2.281` à `+6.429`).
- Basse hors gamme naturelle globale : `+4.257 pp` (IC95 `+1.810` à `+6.703`).
- Blocs triadiques (6 renversements) : `-2.038 pp` (IC95 `-5.595` à `+1.518`).
- Blocs forts non triadiques : `+13.489 pp` (IC95 `+6.208` à `+20.769`).
- Dissonances par bloc faible : `-0.064` (IC95 `-0.145` à `+0.016`).
- Dissonances par bloc fort : `+0.216` (IC95 `+0.085` à `+0.348`).
- {0,3,6,8} sur bloc fort : `+1.139 pp` (IC95 `-0.330` à `+2.609`).
- {0,3,6,8} sur bloc faible : `-0.005 pp` (IC95 `-1.347` à `+1.338`).
