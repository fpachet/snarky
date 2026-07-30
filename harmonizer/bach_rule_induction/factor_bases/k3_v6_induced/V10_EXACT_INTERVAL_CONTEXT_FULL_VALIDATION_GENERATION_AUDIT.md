# Audit génératif explicite de la basse et des sonorités

`50` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Iteration2 | V9Reinduced | V10IntervalContext |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 25.67 % | 26.11 % | 28.58 % | 28.39 % |
| Répétitions à la basse | 3.37 % | 4.68 % | 4.39 % | 4.26 % |
| Sauts de basse > 4 demi-tons | 26.76 % | 27.79 % | 30.36 % | 31.43 % |
| Basse hors gamme naturelle globale | 8.15 % | 9.73 % | 13.37 % | 13.03 % |
| Blocs triadiques (6 renversements) | 52.74 % | 52.65 % | 48.96 % | 52.29 % |
| Blocs forts non triadiques | 28.72 % | 30.30 % | 45.74 % | 39.85 % |
| Dissonances par bloc faible | 0.987 | 0.891 | 0.943 | 0.878 |
| Dissonances par bloc fort | 0.410 | 0.422 | 0.743 | 0.607 |
| {0,3,6,8} sur bloc fort | 2.17 % | 2.10 % | 2.53 % | 1.91 % |
| {0,3,6,8} sur bloc faible | 2.93 % | 4.17 % | 2.89 % | 3.31 % |

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

### V9Reinduced

- Demi-tons à la basse : `+2.909 pp` (IC95 `+1.127` à `+4.691`).
- Répétitions à la basse : `+1.015 pp` (IC95 `+0.104` à `+1.926`).
- Sauts de basse > 4 demi-tons : `+3.609 pp` (IC95 `+1.729` à `+5.488`).
- Basse hors gamme naturelle globale : `+5.215 pp` (IC95 `+3.852` à `+6.577`).
- Blocs triadiques (6 renversements) : `-3.783 pp` (IC95 `-5.981` à `-1.584`).
- Blocs forts non triadiques : `+17.016 pp` (IC95 `+13.647` à `+20.385`).
- Dissonances par bloc faible : `-0.044` (IC95 `-0.100` à `+0.012`).
- Dissonances par bloc fort : `+0.333` (IC95 `+0.275` à `+0.391`).
- {0,3,6,8} sur bloc fort : `+0.358 pp` (IC95 `-0.673` à `+1.390`).
- {0,3,6,8} sur bloc faible : `-0.040 pp` (IC95 `-0.787` à `+0.707`).

### V10IntervalContext

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
