# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V6-train64 | V6-controlled |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.73 % | 27.11 % | 21.24 % |
| Répétitions à la basse | 3.11 % | 5.10 % | 4.52 % |
| Sauts de basse > 4 demi-tons | 28.03 % | 24.33 % | 28.64 % |
| Basse hors gamme naturelle globale | 10.08 % | 10.35 % | 7.40 % |
| Blocs triadiques (6 renversements) | 53.86 % | 52.52 % | 57.65 % |
| Blocs forts non triadiques | 28.20 % | 33.49 % | 30.00 % |
| Dissonances par bloc faible | 0.893 | 0.926 | 0.766 |
| Dissonances par bloc fort | 0.406 | 0.537 | 0.444 |
| {0,3,6,8} sur bloc fort | 1.79 % | 2.47 % | 2.09 % |
| {0,3,6,8} sur bloc faible | 3.20 % | 3.86 % | 3.29 % |

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

### V6-controlled

- Demi-tons à la basse : `-4.491 pp` (IC95 `-8.385` à `-0.596`).
- Répétitions à la basse : `+1.402 pp` (IC95 `-0.502` à `+3.306`).
- Sauts de basse > 4 demi-tons : `+0.611 pp` (IC95 `-3.014` à `+4.236`).
- Basse hors gamme naturelle globale : `-2.675 pp` (IC95 `-7.131` à `+1.781`).
- Blocs triadiques (6 renversements) : `+3.786 pp` (IC95 `+1.207` à `+6.366`).
- Blocs forts non triadiques : `+1.791 pp` (IC95 `-5.849` à `+9.430`).
- Dissonances par bloc faible : `-0.127` (IC95 `-0.215` à `-0.039`).
- Dissonances par bloc fort : `+0.038` (IC95 `-0.096` à `+0.171`).
- {0,3,6,8} sur bloc fort : `+0.296 pp` (IC95 `-2.042` à `+2.635`).
- {0,3,6,8} sur bloc faible : `+0.092 pp` (IC95 `-1.577` à `+1.761`).
