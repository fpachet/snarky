# Audit génératif explicite de la basse et des sonorités

`20` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V13 | V15Hybrid1 | V15Hybrid2 |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 25.37 % | 26.51 % | 28.12 % | 26.79 % |
| Répétitions à la basse | 3.41 % | 3.74 % | 3.91 % | 4.85 % |
| Sauts de basse > 4 demi-tons | 27.95 % | 29.63 % | 29.88 % | 31.60 % |
| Basse hors gamme naturelle globale | 8.61 % | 12.91 % | 12.72 % | 12.22 % |
| Blocs triadiques (6 renversements) | 52.37 % | 50.96 % | 50.89 % | 51.56 % |
| Blocs forts non triadiques | 27.56 % | 40.16 % | 40.88 % | 41.21 % |
| Dissonances par bloc faible | 0.962 | 0.906 | 0.872 | 0.865 |
| Dissonances par bloc fort | 0.381 | 0.600 | 0.599 | 0.622 |
| {0,3,6,8} sur bloc fort | 1.60 % | 3.26 % | 2.59 % | 2.75 % |
| {0,3,6,8} sur bloc faible | 3.14 % | 3.40 % | 2.90 % | 3.17 % |

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

### V15Hybrid1

- Demi-tons à la basse : `+2.753 pp` (IC95 `+0.135` à `+5.370`).
- Répétitions à la basse : `+0.500 pp` (IC95 `-1.322` à `+2.322`).
- Sauts de basse > 4 demi-tons : `+1.924 pp` (IC95 `-0.062` à `+3.910`).
- Basse hors gamme naturelle globale : `+4.108 pp` (IC95 `+1.940` à `+6.277`).
- Blocs triadiques (6 renversements) : `-1.476 pp` (IC95 `-4.879` à `+1.927`).
- Blocs forts non triadiques : `+13.326 pp` (IC95 `+6.711` à `+19.941`).
- Dissonances par bloc faible : `-0.090` (IC95 `-0.169` à `-0.012`).
- Dissonances par bloc fort : `+0.218` (IC95 `+0.100` à `+0.336`).
- {0,3,6,8} sur bloc fort : `+0.991 pp` (IC95 `-0.317` à `+2.300`).
- {0,3,6,8} sur bloc faible : `-0.235 pp` (IC95 `-1.477` à `+1.007`).

### V15Hybrid2

- Demi-tons à la basse : `+1.424 pp` (IC95 `-0.647` à `+3.496`).
- Répétitions à la basse : `+1.436 pp` (IC95 `-0.275` à `+3.148`).
- Sauts de basse > 4 demi-tons : `+3.649 pp` (IC95 `+1.238` à `+6.060`).
- Basse hors gamme naturelle globale : `+3.606 pp` (IC95 `+1.488` à `+5.724`).
- Blocs triadiques (6 renversements) : `-0.803 pp` (IC95 `-4.266` à `+2.659`).
- Blocs forts non triadiques : `+13.655 pp` (IC95 `+6.229` à `+21.082`).
- Dissonances par bloc faible : `-0.097` (IC95 `-0.185` à `-0.010`).
- Dissonances par bloc fort : `+0.241` (IC95 `+0.114` à `+0.368`).
- {0,3,6,8} sur bloc fort : `+1.153 pp` (IC95 `-0.176` à `+2.482`).
- {0,3,6,8} sur bloc faible : `+0.039 pp` (IC95 `-1.121` à `+1.199`).
