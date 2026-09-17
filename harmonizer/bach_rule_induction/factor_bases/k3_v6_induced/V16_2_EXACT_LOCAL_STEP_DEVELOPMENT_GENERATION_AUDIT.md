# Audit génératif explicite de la basse et des sonorités

`20` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V13 | V16.2-local |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.37 % | 26.51 % | 26.50 % |
| Répétitions à la basse | 3.41 % | 3.74 % | 4.37 % |
| Sauts de basse > 4 demi-tons | 27.95 % | 29.63 % | 30.96 % |
| Basse hors gamme naturelle globale | 8.61 % | 12.91 % | 12.42 % |
| Blocs triadiques (6 renversements) | 52.37 % | 50.96 % | 51.03 % |
| Blocs forts non triadiques | 27.56 % | 40.16 % | 41.43 % |
| Dissonances par bloc faible | 0.962 | 0.906 | 0.880 |
| Dissonances par bloc fort | 0.381 | 0.600 | 0.641 |
| {0,3,6,8} sur bloc fort | 1.60 % | 3.26 % | 3.47 % |
| {0,3,6,8} sur bloc faible | 3.14 % | 3.40 % | 2.82 % |

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

### V16.2-local

- Demi-tons à la basse : `+1.136 pp` (IC95 `-1.549` à `+3.821`).
- Répétitions à la basse : `+0.960 pp` (IC95 `-0.897` à `+2.817`).
- Sauts de basse > 4 demi-tons : `+3.005 pp` (IC95 `+0.343` à `+5.666`).
- Basse hors gamme naturelle globale : `+3.809 pp` (IC95 `+1.478` à `+6.139`).
- Blocs triadiques (6 renversements) : `-1.333 pp` (IC95 `-4.455` à `+1.790`).
- Blocs forts non triadiques : `+13.868 pp` (IC95 `+7.054` à `+20.683`).
- Dissonances par bloc faible : `-0.082` (IC95 `-0.151` à `-0.013`).
- Dissonances par bloc fort : `+0.259` (IC95 `+0.141` à `+0.378`).
- {0,3,6,8} sur bloc fort : `+1.870 pp` (IC95 `+0.341` à `+3.398`).
- {0,3,6,8} sur bloc faible : `-0.319 pp` (IC95 `-1.240` à `+0.603`).
