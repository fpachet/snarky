# Audit génératif explicite de la basse et des sonorités

`20` chorals de validation, `3` graine(s), `30` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V13 | V16-rank5 | V16-rank9 |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 25.37 % | 29.29 % | 29.40 % | 29.45 % |
| Répétitions à la basse | 3.41 % | 4.40 % | 3.94 % | 4.80 % |
| Sauts de basse > 4 demi-tons | 27.95 % | 26.03 % | 25.94 % | 25.59 % |
| Basse hors gamme naturelle globale | 8.61 % | 12.31 % | 12.97 % | 12.71 % |
| Blocs triadiques (6 renversements) | 52.37 % | 53.88 % | 52.23 % | 53.84 % |
| Blocs forts non triadiques | 27.56 % | 36.60 % | 36.34 % | 36.93 % |
| Dissonances par bloc faible | 0.962 | 0.864 | 0.912 | 0.868 |
| Dissonances par bloc fort | 0.381 | 0.576 | 0.561 | 0.558 |
| {0,3,6,8} sur bloc fort | 1.60 % | 2.48 % | 2.39 % | 3.19 % |
| {0,3,6,8} sur bloc faible | 3.14 % | 3.47 % | 3.14 % | 3.63 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V13

- Demi-tons à la basse : `+3.926 pp` (IC95 `+1.523` à `+6.328`).
- Répétitions à la basse : `+0.985 pp` (IC95 `-0.992` à `+2.962`).
- Sauts de basse > 4 demi-tons : `-1.925 pp` (IC95 `-5.148` à `+1.298`).
- Basse hors gamme naturelle globale : `+3.704 pp` (IC95 `+1.163` à `+6.244`).
- Blocs triadiques (6 renversements) : `+1.516 pp` (IC95 `-1.853` à `+4.884`).
- Blocs forts non triadiques : `+9.046 pp` (IC95 `+1.555` à `+16.538`).
- Dissonances par bloc faible : `-0.098` (IC95 `-0.165` à `-0.031`).
- Dissonances par bloc fort : `+0.195` (IC95 `+0.076` à `+0.315`).
- {0,3,6,8} sur bloc fort : `+0.883 pp` (IC95 `-0.345` à `+2.111`).
- {0,3,6,8} sur bloc faible : `+0.339 pp` (IC95 `-1.051` à `+1.729`).

### V16-rank5

- Demi-tons à la basse : `+4.028 pp` (IC95 `+1.350` à `+6.705`).
- Répétitions à la basse : `+0.526 pp` (IC95 `-1.437` à `+2.489`).
- Sauts de basse > 4 demi-tons : `-2.009 pp` (IC95 `-4.976` à `+0.957`).
- Basse hors gamme naturelle globale : `+4.355 pp` (IC95 `+2.085` à `+6.624`).
- Blocs triadiques (6 renversements) : `-0.134 pp` (IC95 `-3.700` à `+3.431`).
- Blocs forts non triadiques : `+8.778 pp` (IC95 `+1.328` à `+16.228`).
- Dissonances par bloc faible : `-0.051` (IC95 `-0.133` à `+0.031`).
- Dissonances par bloc fort : `+0.180` (IC95 `+0.055` à `+0.305`).
- {0,3,6,8} sur bloc fort : `+0.789 pp` (IC95 `-0.595` à `+2.174`).
- {0,3,6,8} sur bloc faible : `+0.005 pp` (IC95 `-1.175` à `+1.184`).

### V16-rank9

- Demi-tons à la basse : `+4.086 pp` (IC95 `+1.603` à `+6.568`).
- Répétitions à la basse : `+1.388 pp` (IC95 `-0.108` à `+2.884`).
- Sauts de basse > 4 demi-tons : `-2.363 pp` (IC95 `-4.801` à `+0.075`).
- Basse hors gamme naturelle globale : `+4.101 pp` (IC95 `+1.507` à `+6.696`).
- Blocs triadiques (6 renversements) : `+1.478 pp` (IC95 `-1.668` à `+4.623`).
- Blocs forts non triadiques : `+9.372 pp` (IC95 `+3.335` à `+15.408`).
- Dissonances par bloc faible : `-0.094` (IC95 `-0.182` à `-0.007`).
- Dissonances par bloc fort : `+0.177` (IC95 `+0.063` à `+0.291`).
- {0,3,6,8} sur bloc fort : `+1.588 pp` (IC95 `-0.298` à `+3.473`).
- {0,3,6,8} sur bloc faible : `+0.491 pp` (IC95 `-0.592` à `+1.574`).
