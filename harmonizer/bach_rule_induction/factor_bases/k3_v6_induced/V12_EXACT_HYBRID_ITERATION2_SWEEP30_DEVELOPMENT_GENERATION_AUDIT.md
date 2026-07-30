# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `30` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V12Hybrid1 | V12Hybrid2 |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 31.15 % | 28.91 % |
| Répétitions à la basse | 3.71 % | 4.72 % | 4.27 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 25.65 % | 26.01 % |
| Basse hors gamme naturelle globale | 7.14 % | 13.06 % | 11.79 % |
| Blocs triadiques (6 renversements) | 50.87 % | 54.27 % | 52.98 % |
| Blocs forts non triadiques | 26.91 % | 35.11 % | 33.31 % |
| Dissonances par bloc faible | 1.032 | 0.864 | 0.872 |
| Dissonances par bloc fort | 0.357 | 0.517 | 0.487 |
| {0,3,6,8} sur bloc fort | 1.40 % | 2.36 % | 2.02 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 4.68 % | 3.01 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

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

### V12Hybrid2

- Demi-tons à la basse : `+3.904 pp` (IC95 `+1.493` à `+6.316`).
- Répétitions à la basse : `+0.553 pp` (IC95 `-1.940` à `+3.047`).
- Sauts de basse > 4 demi-tons : `-1.861 pp` (IC95 `-4.371` à `+0.649`).
- Basse hors gamme naturelle globale : `+4.652 pp` (IC95 `+1.450` à `+7.855`).
- Blocs triadiques (6 renversements) : `+2.111 pp` (IC95 `-4.446` à `+8.669`).
- Blocs forts non triadiques : `+6.403 pp` (IC95 `-5.149` à `+17.954`).
- Dissonances par bloc faible : `-0.160` (IC95 `-0.297` à `-0.024`).
- Dissonances par bloc fort : `+0.130` (IC95 `-0.068` à `+0.328`).
- {0,3,6,8} sur bloc fort : `+0.613 pp` (IC95 `-1.536` à `+2.762`).
- {0,3,6,8} sur bloc faible : `-0.068 pp` (IC95 `-2.201` à `+2.064`).
