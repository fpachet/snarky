# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `1` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V23 | V24C |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 28.84 % | 29.40 % |
| Répétitions à la basse | 3.71 % | 4.50 % | 5.05 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 25.68 % | 25.73 % |
| Basse hors gamme naturelle globale | 7.14 % | 11.88 % | 11.99 % |
| Blocs triadiques (6 renversements) | 50.87 % | 49.58 % | 52.34 % |
| Blocs forts non triadiques | 26.91 % | 34.93 % | 30.99 % |
| Dissonances par bloc faible | 1.032 | 1.079 | 1.053 |
| Dissonances par bloc fort | 0.357 | 0.563 | 0.501 |
| {0,3,6,8} sur bloc fort | 1.40 % | 0.61 % | 1.44 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 4.48 % | 4.86 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V23

- Demi-tons à la basse : `+3.837 pp` (IC95 `-0.796` à `+8.469`).
- Répétitions à la basse : `+0.790 pp` (IC95 `-1.790` à `+3.370`).
- Sauts de basse > 4 demi-tons : `-2.187 pp` (IC95 `-8.021` à `+3.646`).
- Basse hors gamme naturelle globale : `+4.734 pp` (IC95 `-0.484` à `+9.952`).
- Blocs triadiques (6 renversements) : `-1.292 pp` (IC95 `-8.770` à `+6.185`).
- Blocs forts non triadiques : `+8.019 pp` (IC95 `-6.286` à `+22.324`).
- Dissonances par bloc faible : `+0.047` (IC95 `-0.114` à `+0.207`).
- Dissonances par bloc fort : `+0.206` (IC95 `-0.070` à `+0.482`).
- {0,3,6,8} sur bloc fort : `-0.791 pp` (IC95 `-2.484` à `+0.903`).
- {0,3,6,8} sur bloc faible : `+1.402 pp` (IC95 `-0.954` à `+3.757`).

### V24C

- Demi-tons à la basse : `+4.393 pp` (IC95 `-2.799` à `+11.586`).
- Répétitions à la basse : `+1.339 pp` (IC95 `-1.610` à `+4.288`).
- Sauts de basse > 4 demi-tons : `-2.146 pp` (IC95 `-7.833` à `+3.542`).
- Basse hors gamme naturelle globale : `+4.845 pp` (IC95 `+0.767` à `+8.924`).
- Blocs triadiques (6 renversements) : `+1.468 pp` (IC95 `-4.880` à `+7.815`).
- Blocs forts non triadiques : `+4.076 pp` (IC95 `-8.114` à `+16.267`).
- Dissonances par bloc faible : `+0.021` (IC95 `-0.156` à `+0.198`).
- Dissonances par bloc fort : `+0.145` (IC95 `-0.081` à `+0.370`).
- {0,3,6,8} sur bloc fort : `+0.039 pp` (IC95 `-2.095` à `+2.174`).
- {0,3,6,8} sur bloc faible : `+1.782 pp` (IC95 `-1.858` à `+5.422`).
