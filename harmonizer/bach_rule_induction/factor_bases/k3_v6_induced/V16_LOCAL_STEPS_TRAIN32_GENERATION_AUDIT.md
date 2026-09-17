# Audit génératif explicite de la basse et des sonorités

`32` chorals de train, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V13 | V16-rank5 | V16-rank9 |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 24.98 % | 26.05 % | 26.77 % | 26.65 % |
| Répétitions à la basse | 4.94 % | 4.22 % | 4.13 % | 4.27 % |
| Sauts de basse > 4 demi-tons | 26.92 % | 32.04 % | 31.89 % | 31.45 % |
| Basse hors gamme naturelle globale | 9.09 % | 13.33 % | 13.53 % | 13.90 % |
| Blocs triadiques (6 renversements) | 53.88 % | 51.20 % | 50.96 % | 50.27 % |
| Blocs forts non triadiques | 29.60 % | 41.95 % | 41.90 % | 41.66 % |
| Dissonances par bloc faible | 0.892 | 0.892 | 0.900 | 0.917 |
| Dissonances par bloc fort | 0.406 | 0.642 | 0.633 | 0.648 |
| {0,3,6,8} sur bloc fort | 1.76 % | 2.76 % | 2.63 % | 2.88 % |
| {0,3,6,8} sur bloc faible | 4.23 % | 2.89 % | 3.19 % | 3.12 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V13

- Demi-tons à la basse : `+1.071 pp` (IC95 `-1.510` à `+3.651`).
- Répétitions à la basse : `-0.720 pp` (IC95 `-1.940` à `+0.501`).
- Sauts de basse > 4 demi-tons : `+5.127 pp` (IC95 `+2.772` à `+7.483`).
- Basse hors gamme naturelle globale : `+4.231 pp` (IC95 `+2.389` à `+6.074`).
- Blocs triadiques (6 renversements) : `-2.672 pp` (IC95 `-5.032` à `-0.313`).
- Blocs forts non triadiques : `+12.350 pp` (IC95 `+8.399` à `+16.300`).
- Dissonances par bloc faible : `-0.000` (IC95 `-0.063` à `+0.063`).
- Dissonances par bloc fort : `+0.236` (IC95 `+0.181` à `+0.291`).
- {0,3,6,8} sur bloc fort : `+0.995 pp` (IC95 `-0.345` à `+2.334`).
- {0,3,6,8} sur bloc faible : `-1.335 pp` (IC95 `-2.738` à `+0.069`).

### V16-rank5

- Demi-tons à la basse : `+1.782 pp` (IC95 `-0.743` à `+4.308`).
- Répétitions à la basse : `-0.811 pp` (IC95 `-2.252` à `+0.630`).
- Sauts de basse > 4 demi-tons : `+4.977 pp` (IC95 `+2.756` à `+7.197`).
- Basse hors gamme naturelle globale : `+4.436 pp` (IC95 `+2.588` à `+6.285`).
- Blocs triadiques (6 renversements) : `-2.919 pp` (IC95 `-4.915` à `-0.924`).
- Blocs forts non triadiques : `+12.306 pp` (IC95 `+8.128` à `+16.484`).
- Dissonances par bloc faible : `+0.008` (IC95 `-0.047` à `+0.063`).
- Dissonances par bloc fort : `+0.226` (IC95 `+0.166` à `+0.287`).
- {0,3,6,8} sur bloc fort : `+0.866 pp` (IC95 `-0.517` à `+2.250`).
- {0,3,6,8} sur bloc faible : `-1.036 pp` (IC95 `-2.315` à `+0.244`).

### V16-rank9

- Demi-tons à la basse : `+1.671 pp` (IC95 `-0.738` à `+4.080`).
- Répétitions à la basse : `-0.672 pp` (IC95 `-2.007` à `+0.663`).
- Sauts de basse > 4 demi-tons : `+4.536 pp` (IC95 `+2.488` à `+6.584`).
- Basse hors gamme naturelle globale : `+4.806 pp` (IC95 `+3.235` à `+6.377`).
- Blocs triadiques (6 renversements) : `-3.609 pp` (IC95 `-6.134` à `-1.085`).
- Blocs forts non triadiques : `+12.063 pp` (IC95 `+8.360` à `+15.765`).
- Dissonances par bloc faible : `+0.025` (IC95 `-0.035` à `+0.085`).
- Dissonances par bloc fort : `+0.242` (IC95 `+0.179` à `+0.305`).
- {0,3,6,8} sur bloc fort : `+1.121 pp` (IC95 `-0.315` à `+2.556`).
- {0,3,6,8} sur bloc faible : `-1.104 pp` (IC95 `-2.455` à `+0.248`).
