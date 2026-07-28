# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `1` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test fermé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V5.14 |
|---|---:|---:|
| Demi-tons à la basse | 25.00 % | 29.97 % |
| Répétitions à la basse | 3.71 % | 6.92 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 15.52 % |
| Basse hors gamme naturelle globale | 7.14 % | 9.51 % |
| Blocs triadiques (6 renversements) | 50.87 % | 54.12 % |
| Blocs forts non triadiques | 26.91 % | 24.53 % |
| Dissonances par bloc faible | 1.032 | 0.975 |
| Dissonances par bloc fort | 0.357 | 0.357 |
| {0,3,6,8} sur bloc fort | 1.40 % | 3.02 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 3.26 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V5.14

- Demi-tons à la basse : `+4.966 pp` (IC95 `+0.183` à `+9.750`).
- Répétitions à la basse : `+3.209 pp` (IC95 `-0.413` à `+6.830`).
- Sauts de basse > 4 demi-tons : `-12.355 pp` (IC95 `-16.907` à `-7.804`).
- Basse hors gamme naturelle globale : `+2.372 pp` (IC95 `-1.571` à `+6.314`).
- Blocs triadiques (6 renversements) : `+3.245 pp` (IC95 `-2.558` à `+9.049`).
- Blocs forts non triadiques : `-2.385 pp` (IC95 `-12.734` à `+7.965`).
- Dissonances par bloc faible : `-0.057` (IC95 `-0.203` à `+0.089`).
- Dissonances par bloc fort : `+0.001` (IC95 `-0.174` à `+0.175`).
- {0,3,6,8} sur bloc fort : `+1.617 pp` (IC95 `-0.730` à `+3.964`).
- {0,3,6,8} sur bloc faible : `+0.185 pp` (IC95 `-2.756` à `+3.126`).
