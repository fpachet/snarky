# Audit génératif explicite de la basse et des sonorités

`50` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V6-multimetric |
|---|---:|---:|
| Demi-tons à la basse | 25.67 % | 27.32 % |
| Répétitions à la basse | 3.37 % | 4.35 % |
| Sauts de basse > 4 demi-tons | 26.76 % | 25.87 % |
| Basse hors gamme naturelle globale | 8.15 % | 9.91 % |
| Blocs triadiques (6 renversements) | 52.74 % | 50.71 % |
| Blocs forts non triadiques | 28.72 % | 32.77 % |
| Dissonances par bloc faible | 0.987 | 0.934 |
| Dissonances par bloc fort | 0.410 | 0.479 |
| {0,3,6,8} sur bloc fort | 2.17 % | 1.87 % |
| {0,3,6,8} sur bloc faible | 2.93 % | 4.60 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V6-multimetric

- Demi-tons à la basse : `+1.654 pp` (IC95 `-0.223` à `+3.531`).
- Répétitions à la basse : `+0.977 pp` (IC95 `+0.073` à `+1.881`).
- Sauts de basse > 4 demi-tons : `-0.885 pp` (IC95 `-2.511` à `+0.742`).
- Basse hors gamme naturelle globale : `+1.760 pp` (IC95 `+0.034` à `+3.486`).
- Blocs triadiques (6 renversements) : `-2.036 pp` (IC95 `-4.291` à `+0.220`).
- Blocs forts non triadiques : `+4.043 pp` (IC95 `+0.299` à `+7.788`).
- Dissonances par bloc faible : `-0.053` (IC95 `-0.124` à `+0.018`).
- Dissonances par bloc fort : `+0.069` (IC95 `+0.008` à `+0.130`).
- {0,3,6,8} sur bloc fort : `-0.298 pp` (IC95 `-1.347` à `+0.750`).
- {0,3,6,8} sur bloc faible : `+1.678 pp` (IC95 `+0.707` à `+2.649`).
