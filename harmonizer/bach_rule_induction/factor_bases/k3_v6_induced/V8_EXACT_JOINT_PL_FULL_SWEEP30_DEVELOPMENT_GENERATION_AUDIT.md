# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `30` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Iteration2 | V8ExactFull |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 26.27 % | 27.64 % |
| Répétitions à la basse | 3.71 % | 4.41 % | 5.43 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 28.29 % | 21.46 % |
| Basse hors gamme naturelle globale | 7.14 % | 7.26 % | 7.43 % |
| Blocs triadiques (6 renversements) | 50.87 % | 54.76 % | 57.10 % |
| Blocs forts non triadiques | 26.91 % | 24.79 % | 23.73 % |
| Dissonances par bloc faible | 1.032 | 0.908 | 0.895 |
| Dissonances par bloc fort | 0.357 | 0.346 | 0.332 |
| {0,3,6,8} sur bloc fort | 1.40 % | 0.91 % | 1.61 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 3.80 % | 4.04 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### Iteration2

- Demi-tons à la basse : `+1.266 pp` (IC95 `-2.575` à `+5.106`).
- Répétitions à la basse : `+0.697 pp` (IC95 `-0.948` à `+2.342`).
- Sauts de basse > 4 demi-tons : `+0.423 pp` (IC95 `-4.591` à `+5.438`).
- Basse hors gamme naturelle globale : `+0.115 pp` (IC95 `-2.437` à `+2.667`).
- Blocs triadiques (6 renversements) : `+3.894 pp` (IC95 `-1.883` à `+9.671`).
- Blocs forts non triadiques : `-2.119 pp` (IC95 `-12.643` à `+8.405`).
- Dissonances par bloc faible : `-0.124` (IC95 `-0.283` à `+0.035`).
- Dissonances par bloc fort : `-0.010` (IC95 `-0.204` à `+0.183`).
- {0,3,6,8} sur bloc fort : `-0.495 pp` (IC95 `-2.202` à `+1.212`).
- {0,3,6,8} sur bloc faible : `+0.729 pp` (IC95 `-1.982` à `+3.440`).

### V8ExactFull

- Demi-tons à la basse : `+2.641 pp` (IC95 `-1.962` à `+7.245`).
- Répétitions à la basse : `+1.720 pp` (IC95 `-0.782` à `+4.223`).
- Sauts de basse > 4 demi-tons : `-6.415 pp` (IC95 `-10.694` à `-2.137`).
- Basse hors gamme naturelle globale : `+0.286 pp` (IC95 `-2.649` à `+3.222`).
- Blocs triadiques (6 renversements) : `+6.225 pp` (IC95 `+0.913` à `+11.537`).
- Blocs forts non triadiques : `-3.176 pp` (IC95 `-13.330` à `+6.979`).
- Dissonances par bloc faible : `-0.137` (IC95 `-0.270` à `-0.005`).
- Dissonances par bloc fort : `-0.024` (IC95 `-0.211` à `+0.162`).
- {0,3,6,8} sur bloc fort : `+0.202 pp` (IC95 `-2.340` à `+2.743`).
- {0,3,6,8} sur bloc faible : `+0.967 pp` (IC95 `-1.859` à `+3.793`).
