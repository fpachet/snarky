# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V6-refit16 | V6-train64 |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.73 % | 27.03 % | 27.11 % |
| Répétitions à la basse | 3.11 % | 6.95 % | 5.10 % |
| Sauts de basse > 4 demi-tons | 28.03 % | 23.97 % | 24.33 % |
| Basse hors gamme naturelle globale | 10.08 % | 9.26 % | 10.35 % |
| Blocs triadiques (6 renversements) | 53.86 % | 51.82 % | 52.52 % |
| Blocs forts non triadiques | 28.20 % | 35.71 % | 33.49 % |
| Dissonances par bloc faible | 0.893 | 0.921 | 0.926 |
| Dissonances par bloc fort | 0.406 | 0.564 | 0.537 |
| {0,3,6,8} sur bloc fort | 1.79 % | 2.72 % | 2.47 % |
| {0,3,6,8} sur bloc faible | 3.20 % | 4.21 % | 3.86 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V6-refit16

- Demi-tons à la basse : `+1.295 pp` (IC95 `-3.139` à `+5.729`).
- Répétitions à la basse : `+3.835 pp` (IC95 `+1.283` à `+6.386`).
- Sauts de basse > 4 demi-tons : `-4.064 pp` (IC95 `-6.942` à `-1.185`).
- Basse hors gamme naturelle globale : `-0.821 pp` (IC95 `-5.315` à `+3.673`).
- Blocs triadiques (6 renversements) : `-2.047 pp` (IC95 `-5.313` à `+1.218`).
- Blocs forts non triadiques : `+7.508 pp` (IC95 `+0.947` à `+14.070`).
- Dissonances par bloc faible : `+0.028` (IC95 `-0.075` à `+0.132`).
- Dissonances par bloc fort : `+0.158` (IC95 `+0.041` à `+0.275`).
- {0,3,6,8} sur bloc fort : `+0.926 pp` (IC95 `-2.033` à `+3.886`).
- {0,3,6,8} sur bloc faible : `+1.017 pp` (IC95 `-0.599` à `+2.634`).

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
