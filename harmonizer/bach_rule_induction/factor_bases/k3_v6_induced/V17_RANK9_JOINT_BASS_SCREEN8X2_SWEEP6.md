# Audit génératif explicite de la basse et des sonorités

`8` chorals de train, `2` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V13 | Joint025 | Joint050 | Joint075 |
|---|---:|---:|---:|---:|---:|
| Demi-tons à la basse | 21.45 % | 27.15 % | 26.66 % | 28.46 % | 27.81 % |
| Répétitions à la basse | 6.68 % | 4.54 % | 3.97 % | 3.94 % | 2.66 % |
| Sauts de basse > 4 demi-tons | 30.27 % | 33.64 % | 33.39 % | 32.96 % | 32.66 % |
| Basse hors gamme naturelle globale | 7.93 % | 12.28 % | 13.73 % | 13.24 % | 14.96 % |
| Blocs triadiques (6 renversements) | 53.94 % | 54.09 % | 53.63 % | 54.10 % | 54.12 % |
| Blocs forts non triadiques | 35.91 % | 39.21 % | 35.73 % | 36.65 % | 35.89 % |
| Dissonances par bloc faible | 0.828 | 0.823 | 0.870 | 0.840 | 0.831 |
| Dissonances par bloc fort | 0.523 | 0.618 | 0.502 | 0.561 | 0.540 |
| {0,3,6,8} sur bloc fort | 0.75 % | 3.01 % | 3.73 % | 3.16 % | 3.16 % |
| {0,3,6,8} sur bloc faible | 4.49 % | 3.84 % | 3.56 % | 3.46 % | 5.06 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V13

- Demi-tons à la basse : `+5.698 pp` (IC95 `+2.347` à `+9.048`).
- Répétitions à la basse : `-2.141 pp` (IC95 `-4.781` à `+0.499`).
- Sauts de basse > 4 demi-tons : `+3.368 pp` (IC95 `+0.020` à `+6.716`).
- Basse hors gamme naturelle globale : `+4.346 pp` (IC95 `+0.479` à `+8.213`).
- Blocs triadiques (6 renversements) : `+0.157 pp` (IC95 `-3.551` à `+3.864`).
- Blocs forts non triadiques : `+3.297 pp` (IC95 `-1.229` à `+7.824`).
- Dissonances par bloc faible : `-0.005` (IC95 `-0.100` à `+0.090`).
- Dissonances par bloc fort : `+0.095` (IC95 `-0.009` à `+0.199`).
- {0,3,6,8} sur bloc fort : `+2.257 pp` (IC95 `+0.323` à `+4.190`).
- {0,3,6,8} sur bloc faible : `-0.655 pp` (IC95 `-4.571` à `+3.260`).

### Joint025

- Demi-tons à la basse : `+5.209 pp` (IC95 `+0.603` à `+9.815`).
- Répétitions à la basse : `-2.712 pp` (IC95 `-5.845` à `+0.422`).
- Sauts de basse > 4 demi-tons : `+3.119 pp` (IC95 `-1.242` à `+7.479`).
- Basse hors gamme naturelle globale : `+5.801 pp` (IC95 `+1.899` à `+9.703`).
- Blocs triadiques (6 renversements) : `-0.306 pp` (IC95 `-3.104` à `+2.493`).
- Blocs forts non triadiques : `-0.179 pp` (IC95 `-4.358` à `+4.001`).
- Dissonances par bloc faible : `+0.042` (IC95 `-0.050` à `+0.134`).
- Dissonances par bloc fort : `-0.022` (IC95 `-0.139` à `+0.096`).
- {0,3,6,8} sur bloc fort : `+2.981 pp` (IC95 `-0.549` à `+6.511`).
- {0,3,6,8} sur bloc faible : `-0.933 pp` (IC95 `-3.714` à `+1.847`).

### Joint050

- Demi-tons à la basse : `+7.007 pp` (IC95 `+2.699` à `+11.314`).
- Répétitions à la basse : `-2.737 pp` (IC95 `-5.700` à `+0.227`).
- Sauts de basse > 4 demi-tons : `+2.690 pp` (IC95 `-2.403` à `+7.782`).
- Basse hors gamme naturelle globale : `+5.309 pp` (IC95 `+0.596` à `+10.022`).
- Blocs triadiques (6 renversements) : `+0.162 pp` (IC95 `-4.245` à `+4.569`).
- Blocs forts non triadiques : `+0.738 pp` (IC95 `-5.681` à `+7.157`).
- Dissonances par bloc faible : `+0.012` (IC95 `-0.093` à `+0.117`).
- Dissonances par bloc fort : `+0.038` (IC95 `-0.096` à `+0.171`).
- {0,3,6,8} sur bloc fort : `+2.409 pp` (IC95 `-0.362` à `+5.179`).
- {0,3,6,8} sur bloc faible : `-1.038 pp` (IC95 `-3.458` à `+1.383`).

### Joint075

- Demi-tons à la basse : `+6.364 pp` (IC95 `+1.393` à `+11.334`).
- Répétitions à la basse : `-4.020 pp` (IC95 `-7.844` à `-0.195`).
- Sauts de basse > 4 demi-tons : `+2.393 pp` (IC95 `-2.690` à `+7.476`).
- Basse hors gamme naturelle globale : `+7.029 pp` (IC95 `+2.631` à `+11.427`).
- Blocs triadiques (6 renversements) : `+0.182 pp` (IC95 `-5.006` à `+5.370`).
- Blocs forts non triadiques : `-0.025 pp` (IC95 `-7.778` à `+7.727`).
- Dissonances par bloc faible : `+0.003` (IC95 `-0.115` à `+0.120`).
- Dissonances par bloc fort : `+0.017` (IC95 `-0.119` à `+0.154`).
- {0,3,6,8} sur bloc fort : `+2.414 pp` (IC95 `+0.090` à `+4.738`).
- {0,3,6,8} sur bloc faible : `+0.564 pp` (IC95 `-3.037` à `+4.165`).
