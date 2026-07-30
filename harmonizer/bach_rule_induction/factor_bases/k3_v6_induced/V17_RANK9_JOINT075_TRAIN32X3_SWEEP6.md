# Audit génératif explicite de la basse et des sonorités

`32` chorals de train, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V13 | V17-joint075 |
|---|---:|---:|---:|
| Demi-tons à la basse | 24.98 % | 26.05 % | 27.12 % |
| Répétitions à la basse | 4.94 % | 4.22 % | 4.74 % |
| Sauts de basse > 4 demi-tons | 26.92 % | 32.04 % | 30.45 % |
| Basse hors gamme naturelle globale | 9.09 % | 13.33 % | 13.64 % |
| Blocs triadiques (6 renversements) | 53.88 % | 51.20 % | 50.24 % |
| Blocs forts non triadiques | 29.60 % | 41.95 % | 41.81 % |
| Dissonances par bloc faible | 0.892 | 0.892 | 0.912 |
| Dissonances par bloc fort | 0.406 | 0.642 | 0.643 |
| {0,3,6,8} sur bloc fort | 1.76 % | 2.76 % | 3.04 % |
| {0,3,6,8} sur bloc faible | 4.23 % | 2.89 % | 3.27 % |

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

### V17-joint075

- Demi-tons à la basse : `+2.137 pp` (IC95 `-0.613` à `+4.888`).
- Répétitions à la basse : `-0.195 pp` (IC95 `-1.765` à `+1.376`).
- Sauts de basse > 4 demi-tons : `+3.537 pp` (IC95 `+1.447` à `+5.627`).
- Basse hors gamme naturelle globale : `+4.544 pp` (IC95 `+2.842` à `+6.247`).
- Blocs triadiques (6 renversements) : `-3.634 pp` (IC95 `-6.084` à `-1.183`).
- Blocs forts non triadiques : `+12.210 pp` (IC95 `+7.611` à `+16.808`).
- Dissonances par bloc faible : `+0.020` (IC95 `-0.033` à `+0.073`).
- Dissonances par bloc fort : `+0.237` (IC95 `+0.159` à `+0.315`).
- {0,3,6,8} sur bloc fort : `+1.278 pp` (IC95 `-0.068` à `+2.623`).
- {0,3,6,8} sur bloc faible : `-0.950 pp` (IC95 `-2.267` à `+0.367`).
