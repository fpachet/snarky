# Audit génératif explicite de la basse et des sonorités

`50` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Iteration2 | V8Exact | V9Reinduced |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 25.67 % | 26.11 % | 27.62 % | 28.58 % |
| Répétitions à la basse | 3.37 % | 4.68 % | 6.24 % | 4.39 % |
| Sauts de basse > 4 demi-tons | 26.76 % | 27.79 % | 20.91 % | 30.36 % |
| Basse hors gamme naturelle globale | 8.15 % | 9.73 % | 10.07 % | 13.37 % |
| Blocs triadiques (6 renversements) | 52.74 % | 52.65 % | 54.33 % | 48.96 % |
| Blocs forts non triadiques | 28.72 % | 30.30 % | 29.56 % | 45.74 % |
| Dissonances par bloc faible | 0.987 | 0.891 | 0.943 | 0.943 |
| Dissonances par bloc fort | 0.410 | 0.422 | 0.419 | 0.743 |
| {0,3,6,8} sur bloc fort | 2.17 % | 2.10 % | 2.09 % | 2.53 % |
| {0,3,6,8} sur bloc faible | 2.93 % | 4.17 % | 4.27 % | 2.89 % |

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

### V8Exact

- Demi-tons à la basse : `+1.947 pp` (IC95 `+0.097` à `+3.796`).
- Répétitions à la basse : `+2.866 pp` (IC95 `+2.010` à `+3.722`).
- Sauts de basse > 4 demi-tons : `-5.843 pp` (IC95 `-7.948` à `-3.738`).
- Basse hors gamme naturelle globale : `+1.919 pp` (IC95 `+0.401` à `+3.436`).
- Blocs triadiques (6 renversements) : `+1.587 pp` (IC95 `-0.427` à `+3.601`).
- Blocs forts non triadiques : `+0.831 pp` (IC95 `-2.663` à `+4.324`).
- Dissonances par bloc faible : `-0.044` (IC95 `-0.111` à `+0.022`).
- Dissonances par bloc fort : `+0.010` (IC95 `-0.046` à `+0.065`).
- {0,3,6,8} sur bloc fort : `-0.078 pp` (IC95 `-1.055` à `+0.900`).
- {0,3,6,8} sur bloc faible : `+1.345 pp` (IC95 `+0.459` à `+2.231`).

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
