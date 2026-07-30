# Audit génératif explicite de la basse et des sonorités

`20` chorals de validation, `3` graine(s), `30` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V13 | V16-rank5-local | V16-rank5-refit |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 25.37 % | 29.29 % | 29.40 % | 30.01 % |
| Répétitions à la basse | 3.41 % | 4.40 % | 3.94 % | 5.00 % |
| Sauts de basse > 4 demi-tons | 27.95 % | 26.03 % | 25.94 % | 25.38 % |
| Basse hors gamme naturelle globale | 8.61 % | 12.31 % | 12.97 % | 13.52 % |
| Blocs triadiques (6 renversements) | 52.37 % | 53.88 % | 52.23 % | 53.10 % |
| Blocs forts non triadiques | 27.56 % | 36.60 % | 36.34 % | 37.56 % |
| Dissonances par bloc faible | 0.962 | 0.864 | 0.912 | 0.878 |
| Dissonances par bloc fort | 0.381 | 0.576 | 0.561 | 0.595 |
| {0,3,6,8} sur bloc fort | 1.60 % | 2.48 % | 2.39 % | 3.25 % |
| {0,3,6,8} sur bloc faible | 3.14 % | 3.47 % | 3.14 % | 3.72 % |

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

### V16-rank5-local

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

### V16-rank5-refit

- Demi-tons à la basse : `+4.643 pp` (IC95 `+2.635` à `+6.650`).
- Répétitions à la basse : `+1.590 pp` (IC95 `-0.033` à `+3.214`).
- Sauts de basse > 4 demi-tons : `-2.571 pp` (IC95 `-4.879` à `-0.263`).
- Basse hors gamme naturelle globale : `+4.913 pp` (IC95 `+2.435` à `+7.392`).
- Blocs triadiques (6 renversements) : `+0.735 pp` (IC95 `-2.778` à `+4.248`).
- Blocs forts non triadiques : `+10.001 pp` (IC95 `+3.681` à `+16.321`).
- Dissonances par bloc faible : `-0.085` (IC95 `-0.164` à `-0.005`).
- Dissonances par bloc fort : `+0.214` (IC95 `+0.102` à `+0.326`).
- {0,3,6,8} sur bloc fort : `+1.647 pp` (IC95 `+0.241` à `+3.053`).
- {0,3,6,8} sur bloc faible : `+0.588 pp` (IC95 `-0.625` à `+1.801`).
