# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `30` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Iteration2 | V9Reinduced |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 26.27 % | 33.43 % |
| Répétitions à la basse | 3.71 % | 4.41 % | 3.97 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 28.29 % | 25.54 % |
| Basse hors gamme naturelle globale | 7.14 % | 7.26 % | 13.85 % |
| Blocs triadiques (6 renversements) | 50.87 % | 54.76 % | 52.77 % |
| Blocs forts non triadiques | 26.91 % | 24.79 % | 39.93 % |
| Dissonances par bloc faible | 1.032 | 0.908 | 0.860 |
| Dissonances par bloc fort | 0.357 | 0.346 | 0.606 |
| {0,3,6,8} sur bloc fort | 1.40 % | 0.91 % | 3.81 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 3.80 % | 4.30 % |

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

### V9Reinduced

- Demi-tons à la basse : `+8.423 pp` (IC95 `+5.306` à `+11.540`).
- Répétitions à la basse : `+0.256 pp` (IC95 `-2.441` à `+2.953`).
- Sauts de basse > 4 demi-tons : `-2.330 pp` (IC95 `-6.935` à `+2.276`).
- Basse hors gamme naturelle globale : `+6.707 pp` (IC95 `+2.905` à `+10.508`).
- Blocs triadiques (6 renversements) : `+1.902 pp` (IC95 `-4.982` à `+8.787`).
- Blocs forts non triadiques : `+13.022 pp` (IC95 `+0.479` à `+25.564`).
- Dissonances par bloc faible : `-0.172` (IC95 `-0.313` à `-0.032`).
- Dissonances par bloc fort : `+0.250` (IC95 `+0.046` à `+0.453`).
- {0,3,6,8} sur bloc fort : `+2.404 pp` (IC95 `+0.648` à `+4.160`).
- {0,3,6,8} sur bloc faible : `+1.226 pp` (IC95 `-0.911` à `+3.364`).
