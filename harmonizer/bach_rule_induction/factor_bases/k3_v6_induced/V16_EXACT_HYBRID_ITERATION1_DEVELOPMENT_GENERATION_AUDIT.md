# Audit génératif explicite de la basse et des sonorités

`20` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V13 | V16.1 |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.37 % | 26.51 % | 25.88 % |
| Répétitions à la basse | 3.41 % | 3.74 % | 4.64 % |
| Sauts de basse > 4 demi-tons | 27.95 % | 29.63 % | 32.45 % |
| Basse hors gamme naturelle globale | 8.61 % | 12.91 % | 12.82 % |
| Blocs triadiques (6 renversements) | 52.37 % | 50.96 % | 51.30 % |
| Blocs forts non triadiques | 27.56 % | 40.16 % | 39.93 % |
| Dissonances par bloc faible | 0.962 | 0.906 | 0.898 |
| Dissonances par bloc fort | 0.381 | 0.600 | 0.611 |
| {0,3,6,8} sur bloc fort | 1.60 % | 3.26 % | 2.92 % |
| {0,3,6,8} sur bloc faible | 3.14 % | 3.40 % | 3.30 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V13

- Demi-tons à la basse : `+1.140 pp` (IC95 `-0.971` à `+3.251`).
- Répétitions à la basse : `+0.330 pp` (IC95 `-1.144` à `+1.804`).
- Sauts de basse > 4 demi-tons : `+1.680 pp` (IC95 `-0.951` à `+4.311`).
- Basse hors gamme naturelle globale : `+4.302 pp` (IC95 `+2.006` à `+6.598`).
- Blocs triadiques (6 renversements) : `-1.402 pp` (IC95 `-4.350` à `+1.546`).
- Blocs forts non triadiques : `+12.607 pp` (IC95 `+5.736` à `+19.477`).
- Dissonances par bloc faible : `-0.056` (IC95 `-0.127` à `+0.015`).
- Dissonances par bloc fort : `+0.219` (IC95 `+0.103` à `+0.335`).
- {0,3,6,8} sur bloc fort : `+1.659 pp` (IC95 `+0.137` à `+3.182`).
- {0,3,6,8} sur bloc faible : `+0.262 pp` (IC95 `-1.048` à `+1.572`).

### V16.1

- Demi-tons à la basse : `+0.513 pp` (IC95 `-2.114` à `+3.140`).
- Répétitions à la basse : `+1.227 pp` (IC95 `-0.405` à `+2.859`).
- Sauts de basse > 4 demi-tons : `+4.496 pp` (IC95 `+1.984` à `+7.007`).
- Basse hors gamme naturelle globale : `+4.208 pp` (IC95 `+2.085` à `+6.332`).
- Blocs triadiques (6 renversements) : `-1.071 pp` (IC95 `-4.278` à `+2.136`).
- Blocs forts non triadiques : `+12.372 pp` (IC95 `+4.829` à `+19.915`).
- Dissonances par bloc faible : `-0.065` (IC95 `-0.149` à `+0.019`).
- Dissonances par bloc fort : `+0.230` (IC95 `+0.105` à `+0.356`).
- {0,3,6,8} sur bloc fort : `+1.317 pp` (IC95 `-0.054` à `+2.688`).
- {0,3,6,8} sur bloc faible : `+0.163 pp` (IC95 `-0.975` à `+1.301`).
