# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `1` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test fermé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V5.15 |
|---|---:|---:|
| Demi-tons à la basse | 25.00 % | 18.38 % |
| Répétitions à la basse | 3.71 % | 5.25 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 35.60 % |
| Basse hors gamme naturelle globale | 7.14 % | 5.56 % |
| Blocs triadiques (6 renversements) | 50.87 % | 54.96 % |
| Blocs forts non triadiques | 26.91 % | 22.20 % |
| Dissonances par bloc faible | 1.032 | 0.964 |
| Dissonances par bloc fort | 0.357 | 0.335 |
| {0,3,6,8} sur bloc fort | 1.40 % | 1.21 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 3.06 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V5.15

- Demi-tons à la basse : `-6.623 pp` (IC95 `-10.573` à `-2.673`).
- Répétitions à la basse : `+1.536 pp` (IC95 `-1.486` à `+4.559`).
- Sauts de basse > 4 demi-tons : `+7.726 pp` (IC95 `+4.665` à `+10.787`).
- Basse hors gamme naturelle globale : `-1.585 pp` (IC95 `-5.521` à `+2.351`).
- Blocs triadiques (6 renversements) : `+4.094 pp` (IC95 `-2.344` à `+10.533`).
- Blocs forts non triadiques : `-4.714 pp` (IC95 `-17.066` à `+7.638`).
- Dissonances par bloc faible : `-0.069` (IC95 `-0.231` à `+0.093`).
- Dissonances par bloc fort : `-0.021` (IC95 `-0.238` à `+0.195`).
- {0,3,6,8} sur bloc fort : `-0.192 pp` (IC95 `-2.577` à `+2.194`).
- {0,3,6,8} sur bloc faible : `-0.013 pp` (IC95 `-2.324` à `+2.298`).
