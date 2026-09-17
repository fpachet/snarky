# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `30` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Iteration2 | V10 | V12Hybrid1 |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 26.27 % | 33.07 % | 31.15 % |
| Répétitions à la basse | 3.71 % | 4.41 % | 4.41 % | 4.72 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 28.29 % | 23.81 % | 25.65 % |
| Basse hors gamme naturelle globale | 7.14 % | 7.26 % | 13.62 % | 13.06 % |
| Blocs triadiques (6 renversements) | 50.87 % | 54.76 % | 51.59 % | 54.27 % |
| Blocs forts non triadiques | 26.91 % | 24.79 % | 36.62 % | 35.11 % |
| Dissonances par bloc faible | 1.032 | 0.908 | 0.931 | 0.864 |
| Dissonances par bloc fort | 0.357 | 0.346 | 0.539 | 0.517 |
| {0,3,6,8} sur bloc fort | 1.40 % | 0.91 % | 2.05 % | 2.36 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 3.80 % | 3.78 % | 4.68 % |

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

### V10

- Demi-tons à la basse : `+8.071 pp` (IC95 `+5.113` à `+11.030`).
- Répétitions à la basse : `+0.693 pp` (IC95 `-2.012` à `+3.398`).
- Sauts de basse > 4 demi-tons : `-4.060 pp` (IC95 `-7.611` à `-0.509`).
- Basse hors gamme naturelle globale : `+6.483 pp` (IC95 `+3.689` à `+9.276`).
- Blocs triadiques (6 renversements) : `+0.724 pp` (IC95 `-5.660` à `+7.109`).
- Blocs forts non triadiques : `+9.706 pp` (IC95 `-0.102` à `+19.514`).
- Dissonances par bloc faible : `-0.101` (IC95 `-0.239` à `+0.037`).
- Dissonances par bloc fort : `+0.182` (IC95 `+0.003` à `+0.361`).
- {0,3,6,8} sur bloc fort : `+0.645 pp` (IC95 `-1.267` à `+2.556`).
- {0,3,6,8} sur bloc faible : `+0.708 pp` (IC95 `-1.342` à `+2.757`).

### V12Hybrid1

- Demi-tons à la basse : `+6.150 pp` (IC95 `+2.054` à `+10.247`).
- Répétitions à la basse : `+1.001 pp` (IC95 `-1.143` à `+3.145`).
- Sauts de basse > 4 demi-tons : `-2.219 pp` (IC95 `-6.763` à `+2.325`).
- Basse hors gamme naturelle globale : `+5.917 pp` (IC95 `+2.319` à `+9.515`).
- Blocs triadiques (6 renversements) : `+3.397 pp` (IC95 `-3.069` à `+9.863`).
- Blocs forts non triadiques : `+8.197 pp` (IC95 `-4.466` à `+20.861`).
- Dissonances par bloc faible : `-0.168` (IC95 `-0.309` à `-0.027`).
- Dissonances par bloc fort : `+0.160` (IC95 `-0.049` à `+0.370`).
- {0,3,6,8} sur bloc fort : `+0.952 pp` (IC95 `-1.251` à `+3.156`).
- {0,3,6,8} sur bloc faible : `+1.605 pp` (IC95 `-0.437` à `+3.647`).
