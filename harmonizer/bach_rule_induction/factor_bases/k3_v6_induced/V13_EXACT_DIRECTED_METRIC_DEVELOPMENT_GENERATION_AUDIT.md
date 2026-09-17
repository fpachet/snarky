# Audit génératif explicite de la basse et des sonorités

`20` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Iteration2 | V10 | V13 |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 25.37 % | 25.23 % | 28.29 % | 26.51 % |
| Répétitions à la basse | 3.41 % | 4.33 % | 3.75 % | 3.74 % |
| Sauts de basse > 4 demi-tons | 27.95 % | 28.69 % | 31.39 % | 29.63 % |
| Basse hors gamme naturelle globale | 8.61 % | 8.13 % | 12.40 % | 12.91 % |
| Blocs triadiques (6 renversements) | 52.37 % | 52.94 % | 52.10 % | 50.96 % |
| Blocs forts non triadiques | 27.56 % | 28.55 % | 39.04 % | 40.16 % |
| Dissonances par bloc faible | 0.962 | 0.904 | 0.866 | 0.906 |
| Dissonances par bloc fort | 0.381 | 0.393 | 0.587 | 0.600 |
| {0,3,6,8} sur bloc fort | 1.60 % | 1.55 % | 1.79 % | 3.26 % |
| {0,3,6,8} sur bloc faible | 3.14 % | 3.96 % | 3.43 % | 3.40 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### Iteration2

- Demi-tons à la basse : `-0.134 pp` (IC95 `-2.786` à `+2.518`).
- Répétitions à la basse : `+0.916 pp` (IC95 `-0.763` à `+2.596`).
- Sauts de basse > 4 demi-tons : `+0.741 pp` (IC95 `-1.574` à `+3.056`).
- Basse hors gamme naturelle globale : `-0.477 pp` (IC95 `-3.082` à `+2.129`).
- Blocs triadiques (6 renversements) : `+0.572 pp` (IC95 `-2.455` à `+3.599`).
- Blocs forts non triadiques : `+0.991 pp` (IC95 `-5.337` à `+7.320`).
- Dissonances par bloc faible : `-0.059` (IC95 `-0.135` à `+0.017`).
- Dissonances par bloc fort : `+0.012` (IC95 `-0.099` à `+0.123`).
- {0,3,6,8} sur bloc fort : `-0.044 pp` (IC95 `-1.683` à `+1.595`).
- {0,3,6,8} sur bloc faible : `+0.825 pp` (IC95 `-0.563` à `+2.213`).

### V10

- Demi-tons à la basse : `+2.922 pp` (IC95 `+0.636` à `+5.207`).
- Répétitions à la basse : `+0.333 pp` (IC95 `-1.122` à `+1.787`).
- Sauts de basse > 4 demi-tons : `+3.442 pp` (IC95 `+0.571` à `+6.312`).
- Basse hors gamme naturelle globale : `+3.788 pp` (IC95 `+1.504` à `+6.072`).
- Blocs triadiques (6 renversements) : `-0.269 pp` (IC95 `-3.691` à `+3.152`).
- Blocs forts non triadiques : `+11.478 pp` (IC95 `+4.537` à `+18.419`).
- Dissonances par bloc faible : `-0.097` (IC95 `-0.173` à `-0.020`).
- Dissonances par bloc fort : `+0.205` (IC95 `+0.077` à `+0.334`).
- {0,3,6,8} sur bloc fort : `+0.192 pp` (IC95 `-1.043` à `+1.427`).
- {0,3,6,8} sur bloc faible : `+0.296 pp` (IC95 `-0.722` à `+1.314`).

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
