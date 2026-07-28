# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `30` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V6-multimetric |
|---|---:|---:|
| Demi-tons à la basse | 25.73 % | 28.07 % |
| Répétitions à la basse | 3.11 % | 4.32 % |
| Sauts de basse > 4 demi-tons | 28.03 % | 25.27 % |
| Basse hors gamme naturelle globale | 10.08 % | 9.18 % |
| Blocs triadiques (6 renversements) | 53.86 % | 53.51 % |
| Blocs forts non triadiques | 28.20 % | 27.87 % |
| Dissonances par bloc faible | 0.893 | 0.866 |
| Dissonances par bloc fort | 0.406 | 0.370 |
| {0,3,6,8} sur bloc fort | 1.79 % | 2.51 % |
| {0,3,6,8} sur bloc faible | 3.20 % | 5.07 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V6-multimetric

- Demi-tons à la basse : `+2.337 pp` (IC95 `-2.377` à `+7.051`).
- Répétitions à la basse : `+1.207 pp` (IC95 `-0.942` à `+3.357`).
- Sauts de basse > 4 demi-tons : `-2.761 pp` (IC95 `-7.230` à `+1.708`).
- Basse hors gamme naturelle globale : `-0.894 pp` (IC95 `-5.118` à `+3.329`).
- Blocs triadiques (6 renversements) : `-0.355 pp` (IC95 `-3.623` à `+2.912`).
- Blocs forts non triadiques : `-0.331 pp` (IC95 `-8.010` à `+7.347`).
- Dissonances par bloc faible : `-0.027` (IC95 `-0.094` à `+0.039`).
- Dissonances par bloc fort : `-0.036` (IC95 `-0.155` à `+0.083`).
- {0,3,6,8} sur bloc fort : `+0.715 pp` (IC95 `-1.997` à `+3.426`).
- {0,3,6,8} sur bloc faible : `+1.871 pp` (IC95 `+0.038` à `+3.703`).
