# Audit génératif explicite de la basse et des sonorités

`20` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V10 | V12Hybrid1 | V12Hybrid2 |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 25.37 % | 28.29 % | 27.08 % | 25.58 % |
| Répétitions à la basse | 3.41 % | 3.75 % | 4.11 % | 3.81 % |
| Sauts de basse > 4 demi-tons | 27.95 % | 31.39 % | 32.55 % | 33.03 % |
| Basse hors gamme naturelle globale | 8.61 % | 12.40 % | 11.86 % | 11.36 % |
| Blocs triadiques (6 renversements) | 52.37 % | 52.10 % | 52.40 % | 52.59 % |
| Blocs forts non triadiques | 27.56 % | 39.04 % | 36.60 % | 36.75 % |
| Dissonances par bloc faible | 0.962 | 0.866 | 0.848 | 0.855 |
| Dissonances par bloc fort | 0.381 | 0.587 | 0.526 | 0.536 |
| {0,3,6,8} sur bloc fort | 1.60 % | 1.79 % | 2.57 % | 2.04 % |
| {0,3,6,8} sur bloc faible | 3.14 % | 3.43 % | 3.59 % | 3.15 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

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

### V12Hybrid1

- Demi-tons à la basse : `+1.715 pp` (IC95 `-1.003` à `+4.432`).
- Répétitions à la basse : `+0.697 pp` (IC95 `-0.940` à `+2.333`).
- Sauts de basse > 4 demi-tons : `+4.596 pp` (IC95 `+2.023` à `+7.169`).
- Basse hors gamme naturelle globale : `+3.247 pp` (IC95 `+0.984` à `+5.511`).
- Blocs triadiques (6 renversements) : `+0.029 pp` (IC95 `-3.202` à `+3.261`).
- Blocs forts non triadiques : `+9.043 pp` (IC95 `+3.067` à `+15.019`).
- Dissonances par bloc faible : `-0.115` (IC95 `-0.189` à `-0.041`).
- Dissonances par bloc fort : `+0.145` (IC95 `+0.039` à `+0.250`).
- {0,3,6,8} sur bloc fort : `+0.968 pp` (IC95 `-0.508` à `+2.444`).
- {0,3,6,8} sur bloc faible : `+0.454 pp` (IC95 `-1.036` à `+1.943`).

### V12Hybrid2

- Demi-tons à la basse : `+0.209 pp` (IC95 `-2.208` à `+2.626`).
- Répétitions à la basse : `+0.393 pp` (IC95 `-1.288` à `+2.073`).
- Sauts de basse > 4 demi-tons : `+5.080 pp` (IC95 `+2.544` à `+7.616`).
- Basse hors gamme naturelle globale : `+2.745 pp` (IC95 `+0.163` à `+5.326`).
- Blocs triadiques (6 renversements) : `+0.225 pp` (IC95 `-2.947` à `+3.397`).
- Blocs forts non triadiques : `+9.189 pp` (IC95 `+1.760` à `+16.619`).
- Dissonances par bloc faible : `-0.107` (IC95 `-0.183` à `-0.031`).
- Dissonances par bloc fort : `+0.155` (IC95 `+0.020` à `+0.290`).
- {0,3,6,8} sur bloc fort : `+0.443 pp` (IC95 `-0.950` à `+1.835`).
- {0,3,6,8} sur bloc faible : `+0.018 pp` (IC95 `-1.308` à `+1.344`).
