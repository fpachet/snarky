# Audit génératif explicite de la basse et des sonorités

`50` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Iteration2 | V10 | V12Hybrid1 |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 25.67 % | 26.11 % | 28.39 % | 27.84 % |
| Répétitions à la basse | 3.37 % | 4.68 % | 4.26 % | 4.34 % |
| Sauts de basse > 4 demi-tons | 26.76 % | 27.79 % | 31.43 % | 32.13 % |
| Basse hors gamme naturelle globale | 8.15 % | 9.73 % | 13.03 % | 12.56 % |
| Blocs triadiques (6 renversements) | 52.74 % | 52.65 % | 52.29 % | 51.85 % |
| Blocs forts non triadiques | 28.72 % | 30.30 % | 39.85 % | 38.48 % |
| Dissonances par bloc faible | 0.987 | 0.891 | 0.878 | 0.860 |
| Dissonances par bloc fort | 0.410 | 0.422 | 0.607 | 0.555 |
| {0,3,6,8} sur bloc fort | 2.17 % | 2.10 % | 1.91 % | 2.11 % |
| {0,3,6,8} sur bloc faible | 2.93 % | 4.17 % | 3.31 % | 3.01 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### Iteration2

- Demi-tons à la basse : `+0.442 pp` (IC95 `-1.311` à `+2.195`).
- Répétitions à la basse : `+1.304 pp` (IC95 `+0.443` à `+2.165`).
- Sauts de basse > 4 demi-tons : `+1.033 pp` (IC95 `-0.808` à `+2.875`).
- Basse hors gamme naturelle globale : `+1.576 pp` (IC95 `-0.122` à `+3.274`).
- Blocs triadiques (6 renversements) : `-0.087 pp` (IC95 `-2.136` à `+1.962`).
- Blocs forts non triadiques : `+1.576 pp` (IC95 `-1.792` à `+4.945`).
- Dissonances par bloc faible : `-0.096` (IC95 `-0.191` à `-0.000`).
- Dissonances par bloc fort : `+0.012` (IC95 `-0.043` à `+0.067`).
- {0,3,6,8} sur bloc fort : `-0.069 pp` (IC95 `-1.151` à `+1.014`).
- {0,3,6,8} sur bloc faible : `+1.248 pp` (IC95 `+0.460` à `+2.036`).

### V10

- Demi-tons à la basse : `+2.718 pp` (IC95 `+1.083` à `+4.352`).
- Répétitions à la basse : `+0.886 pp` (IC95 `+0.077` à `+1.695`).
- Sauts de basse > 4 demi-tons : `+4.674 pp` (IC95 `+2.790` à `+6.558`).
- Basse hors gamme naturelle globale : `+4.877 pp` (IC95 `+3.528` à `+6.226`).
- Blocs triadiques (6 renversements) : `-0.451 pp` (IC95 `-2.624` à `+1.722`).
- Blocs forts non triadiques : `+11.126 pp` (IC95 `+7.406` à `+14.846`).
- Dissonances par bloc faible : `-0.109` (IC95 `-0.160` à `-0.058`).
- Dissonances par bloc fort : `+0.197` (IC95 `+0.132` à `+0.262`).
- {0,3,6,8} sur bloc fort : `-0.255 pp` (IC95 `-1.217` à `+0.708`).
- {0,3,6,8} sur bloc faible : `+0.386 pp` (IC95 `-0.286` à `+1.057`).

### V12Hybrid1

- Demi-tons à la basse : `+2.175 pp` (IC95 `+0.356` à `+3.994`).
- Répétitions à la basse : `+0.971 pp` (IC95 `+0.093` à `+1.849`).
- Sauts de basse > 4 demi-tons : `+5.371 pp` (IC95 `+3.394` à `+7.348`).
- Basse hors gamme naturelle globale : `+4.403 pp` (IC95 `+3.129` à `+5.678`).
- Blocs triadiques (6 renversements) : `-0.892 pp` (IC95 `-3.061` à `+1.276`).
- Blocs forts non triadiques : `+9.754 pp` (IC95 `+6.282` à `+13.226`).
- Dissonances par bloc faible : `-0.127` (IC95 `-0.195` à `-0.059`).
- Dissonances par bloc fort : `+0.145` (IC95 `+0.085` à `+0.205`).
- {0,3,6,8} sur bloc fort : `-0.055 pp` (IC95 `-1.089` à `+0.978`).
- {0,3,6,8} sur bloc faible : `+0.089 pp` (IC95 `-0.669` à `+0.847`).
