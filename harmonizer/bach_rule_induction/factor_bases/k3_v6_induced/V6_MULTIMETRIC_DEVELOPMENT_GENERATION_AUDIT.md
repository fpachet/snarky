# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V6-train64 | V6-multimetric |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.73 % | 27.11 % | 26.06 % |
| Répétitions à la basse | 3.11 % | 5.10 % | 3.89 % |
| Sauts de basse > 4 demi-tons | 28.03 % | 24.33 % | 26.83 % |
| Basse hors gamme naturelle globale | 10.08 % | 10.35 % | 7.84 % |
| Blocs triadiques (6 renversements) | 53.86 % | 52.52 % | 51.12 % |
| Blocs forts non triadiques | 28.20 % | 33.49 % | 30.67 % |
| Dissonances par bloc faible | 0.893 | 0.926 | 0.910 |
| Dissonances par bloc fort | 0.406 | 0.537 | 0.447 |
| {0,3,6,8} sur bloc fort | 1.79 % | 2.47 % | 2.52 % |
| {0,3,6,8} sur bloc faible | 3.20 % | 3.86 % | 4.63 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V6-train64

- Demi-tons à la basse : `+1.376 pp` (IC95 `-2.088` à `+4.841`).
- Répétitions à la basse : `+1.989 pp` (IC95 `-0.167` à `+4.145`).
- Sauts de basse > 4 demi-tons : `-3.703 pp` (IC95 `-7.635` à `+0.228`).
- Basse hors gamme naturelle globale : `+0.269 pp` (IC95 `-4.193` à `+4.730`).
- Blocs triadiques (6 renversements) : `-1.345 pp` (IC95 `-5.102` à `+2.412`).
- Blocs forts non triadiques : `+5.290 pp` (IC95 `-3.160` à `+13.739`).
- Dissonances par bloc faible : `+0.034` (IC95 `-0.034` à `+0.102`).
- Dissonances par bloc fort : `+0.131` (IC95 `+0.001` à `+0.262`).
- {0,3,6,8} sur bloc fort : `+0.677 pp` (IC95 `-1.660` à `+3.014`).
- {0,3,6,8} sur bloc faible : `+0.667 pp` (IC95 `-0.411` à `+1.744`).

### V6-multimetric

- Demi-tons à la basse : `+0.332 pp` (IC95 `-3.948` à `+4.612`).
- Répétitions à la basse : `+0.773 pp` (IC95 `-1.823` à `+3.370`).
- Sauts de basse > 4 demi-tons : `-1.200 pp` (IC95 `-3.541` à `+1.140`).
- Basse hors gamme naturelle globale : `-2.235 pp` (IC95 `-6.557` à `+2.087`).
- Blocs triadiques (6 renversements) : `-2.744 pp` (IC95 `-5.794` à `+0.306`).
- Blocs forts non triadiques : `+2.467 pp` (IC95 `-5.376` à `+10.310`).
- Dissonances par bloc faible : `+0.018` (IC95 `-0.062` à `+0.097`).
- Dissonances par bloc fort : `+0.041` (IC95 `-0.084` à `+0.166`).
- {0,3,6,8} sur bloc fort : `+0.728 pp` (IC95 `-2.062` à `+3.519`).
- {0,3,6,8} sur bloc faible : `+1.436 pp` (IC95 `-0.770` à `+3.642`).
