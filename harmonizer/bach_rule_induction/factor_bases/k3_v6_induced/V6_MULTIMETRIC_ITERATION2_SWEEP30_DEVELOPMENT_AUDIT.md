# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `30` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V6-iteration2 |
|---|---:|---:|
| Demi-tons à la basse | 25.73 % | 24.52 % |
| Répétitions à la basse | 3.11 % | 4.31 % |
| Sauts de basse > 4 demi-tons | 28.03 % | 28.67 % |
| Basse hors gamme naturelle globale | 10.08 % | 8.33 % |
| Blocs triadiques (6 renversements) | 53.86 % | 54.56 % |
| Blocs forts non triadiques | 28.20 % | 27.61 % |
| Dissonances par bloc faible | 0.893 | 0.838 |
| Dissonances par bloc fort | 0.406 | 0.406 |
| {0,3,6,8} sur bloc fort | 1.79 % | 2.20 % |
| {0,3,6,8} sur bloc faible | 3.20 % | 4.48 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V6-iteration2

- Demi-tons à la basse : `-1.208 pp` (IC95 `-5.385` à `+2.969`).
- Répétitions à la basse : `+1.193 pp` (IC95 `-1.020` à `+3.407`).
- Sauts de basse > 4 demi-tons : `+0.639 pp` (IC95 `-2.454` à `+3.731`).
- Basse hors gamme naturelle globale : `-1.744 pp` (IC95 `-5.752` à `+2.264`).
- Blocs triadiques (6 renversements) : `+0.699 pp` (IC95 `-2.038` à `+3.436`).
- Blocs forts non triadiques : `-0.596 pp` (IC95 `-7.775` à `+6.583`).
- Dissonances par bloc faible : `-0.054` (IC95 `-0.140` à `+0.032`).
- Dissonances par bloc fort : `+0.000` (IC95 `-0.121` à `+0.121`).
- {0,3,6,8} sur bloc fort : `+0.403 pp` (IC95 `-1.834` à `+2.641`).
- {0,3,6,8} sur bloc faible : `+1.285 pp` (IC95 `-0.263` à `+2.833`).
