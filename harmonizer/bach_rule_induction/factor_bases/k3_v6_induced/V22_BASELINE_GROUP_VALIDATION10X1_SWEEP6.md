# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `1` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Baseline | V22 |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 26.77 % | 24.91 % |
| Répétitions à la basse | 3.71 % | 3.83 % | 3.18 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 30.69 % | 32.14 % |
| Basse hors gamme naturelle globale | 7.14 % | 12.57 % | 12.93 % |
| Blocs triadiques (6 renversements) | 50.87 % | 44.92 % | 45.90 % |
| Blocs forts non triadiques | 26.91 % | 44.27 % | 42.51 % |
| Dissonances par bloc faible | 1.032 | 1.124 | 1.150 |
| Dissonances par bloc fort | 0.357 | 0.740 | 0.685 |
| {0,3,6,8} sur bloc fort | 1.40 % | 2.95 % | 3.69 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 4.57 % | 4.35 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### Baseline

- Demi-tons à la basse : `+1.770 pp` (IC95 `-3.288` à `+6.829`).
- Répétitions à la basse : `+0.118 pp` (IC95 `-2.742` à `+2.977`).
- Sauts de basse > 4 demi-tons : `+2.821 pp` (IC95 `-1.274` à `+6.915`).
- Basse hors gamme naturelle globale : `+5.431 pp` (IC95 `+0.819` à `+10.043`).
- Blocs triadiques (6 renversements) : `-5.946 pp` (IC95 `-12.387` à `+0.495`).
- Blocs forts non triadiques : `+17.356 pp` (IC95 `+8.397` à `+26.314`).
- Dissonances par bloc faible : `+0.092` (IC95 `-0.061` à `+0.245`).
- Dissonances par bloc fort : `+0.383` (IC95 `+0.217` à `+0.550`).
- {0,3,6,8} sur bloc fort : `+1.543 pp` (IC95 `-1.833` à `+4.919`).
- {0,3,6,8} sur bloc faible : `+1.498 pp` (IC95 `-0.682` à `+3.678`).

### V22

- Demi-tons à la basse : `-0.092 pp` (IC95 `-3.602` à `+3.419`).
- Répétitions à la basse : `-0.530 pp` (IC95 `-2.691` à `+1.631`).
- Sauts de basse > 4 demi-tons : `+4.272 pp` (IC95 `-2.042` à `+10.587`).
- Basse hors gamme naturelle globale : `+5.786 pp` (IC95 `+2.475` à `+9.096`).
- Blocs triadiques (6 renversements) : `-4.967 pp` (IC95 `-11.766` à `+1.832`).
- Blocs forts non triadiques : `+15.595 pp` (IC95 `+3.971` à `+27.219`).
- Dissonances par bloc faible : `+0.117` (IC95 `+0.003` à `+0.231`).
- Dissonances par bloc fort : `+0.328` (IC95 `+0.107` à `+0.550`).
- {0,3,6,8} sur bloc fort : `+2.290 pp` (IC95 `-0.672` à `+5.251`).
- {0,3,6,8} sur bloc faible : `+1.278 pp` (IC95 `-1.754` à `+4.309`).
