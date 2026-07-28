# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `1` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test fermé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V5.13 |
|---|---:|---:|
| Demi-tons à la basse | 25.00 % | 27.35 % |
| Répétitions à la basse | 3.71 % | 9.16 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 21.20 % |
| Basse hors gamme naturelle globale | 7.14 % | 11.52 % |
| Blocs triadiques (6 renversements) | 50.87 % | 61.89 % |
| Blocs forts non triadiques | 26.91 % | 15.37 % |
| Dissonances par bloc faible | 1.032 | 0.839 |
| Dissonances par bloc fort | 0.357 | 0.278 |
| {0,3,6,8} sur bloc fort | 1.40 % | 8.23 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 7.90 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V5.13

- Demi-tons à la basse : `+2.345 pp` (IC95 `-1.905` à `+6.595`).
- Répétitions à la basse : `+5.447 pp` (IC95 `+2.214` à `+8.681`).
- Sauts de basse > 4 demi-tons : `-6.671 pp` (IC95 `-13.005` à `-0.337`).
- Basse hors gamme naturelle globale : `+4.382 pp` (IC95 `+0.484` à `+8.279`).
- Blocs triadiques (6 renversements) : `+11.019 pp` (IC95 `+5.412` à `+16.626`).
- Blocs forts non triadiques : `-11.541 pp` (IC95 `-22.820` à `-0.262`).
- Dissonances par bloc faible : `-0.194` (IC95 `-0.353` à `-0.034`).
- Dissonances par bloc fort : `-0.078` (IC95 `-0.300` à `+0.143`).
- {0,3,6,8} sur bloc fort : `+6.829 pp` (IC95 `+3.885` à `+9.773`).
- {0,3,6,8} sur bloc faible : `+4.825 pp` (IC95 `+1.950` à `+7.701`).
