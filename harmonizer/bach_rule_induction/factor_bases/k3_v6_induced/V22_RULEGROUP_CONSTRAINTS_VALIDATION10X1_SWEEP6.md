# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `1` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Baseline | V22 | V22+C |
|---|---:|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 24.43 % | 25.58 % | 25.43 % |
| Répétitions à la basse | 3.71 % | 3.92 % | 2.90 % | 3.84 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 27.92 % | 27.75 % | 28.72 % |
| Basse hors gamme naturelle globale | 7.14 % | 10.59 % | 11.59 % | 10.58 % |
| Blocs triadiques (6 renversements) | 50.87 % | 49.33 % | 47.07 % | 49.23 % |
| Blocs forts non triadiques | 26.91 % | 35.91 % | 37.55 % | 37.64 % |
| Dissonances par bloc faible | 1.032 | 1.101 | 1.172 | 1.055 |
| Dissonances par bloc fort | 0.357 | 0.611 | 0.688 | 0.654 |
| {0,3,6,8} sur bloc fort | 1.40 % | 3.37 % | 4.38 % | 2.61 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 3.21 % | 4.37 % | 5.13 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### Baseline

- Demi-tons à la basse : `-0.568 pp` (IC95 `-4.507` à `+3.371`).
- Répétitions à la basse : `+0.203 pp` (IC95 `-2.610` à `+3.016`).
- Sauts de basse > 4 demi-tons : `+0.045 pp` (IC95 `-3.170` à `+3.261`).
- Basse hors gamme naturelle globale : `+3.450 pp` (IC95 `-0.024` à `+6.925`).
- Blocs triadiques (6 renversements) : `-1.536 pp` (IC95 `-8.057` à `+4.986`).
- Blocs forts non triadiques : `+9.000 pp` (IC95 `-2.440` à `+20.440`).
- Dissonances par bloc faible : `+0.069` (IC95 `-0.116` à `+0.253`).
- Dissonances par bloc fort : `+0.255` (IC95 `+0.024` à `+0.485`).
- {0,3,6,8} sur bloc fort : `+1.966 pp` (IC95 `-1.411` à `+5.342`).
- {0,3,6,8} sur bloc faible : `+0.140 pp` (IC95 `-1.755` à `+2.035`).

### V22

- Demi-tons à la basse : `+0.577 pp` (IC95 `-3.980` à `+5.133`).
- Répétitions à la basse : `-0.812 pp` (IC95 `-4.506` à `+2.883`).
- Sauts de basse > 4 demi-tons : `-0.122 pp` (IC95 `-3.393` à `+3.148`).
- Basse hors gamme naturelle globale : `+4.447 pp` (IC95 `+0.959` à `+7.936`).
- Blocs triadiques (6 renversements) : `-3.801 pp` (IC95 `-11.194` à `+3.591`).
- Blocs forts non triadiques : `+10.638 pp` (IC95 `+2.857` à `+18.419`).
- Dissonances par bloc faible : `+0.140` (IC95 `-0.061` à `+0.341`).
- Dissonances par bloc fort : `+0.332` (IC95 `+0.187` à `+0.476`).
- {0,3,6,8} sur bloc fort : `+2.973 pp` (IC95 `+0.935` à `+5.011`).
- {0,3,6,8} sur bloc faible : `+1.300 pp` (IC95 `-1.462` à `+4.063`).

### V22+C

- Demi-tons à la basse : `+0.431 pp` (IC95 `-3.676` à `+4.538`).
- Répétitions à la basse : `+0.124 pp` (IC95 `-2.342` à `+2.590`).
- Sauts de basse > 4 demi-tons : `+0.847 pp` (IC95 `-3.209` à `+4.903`).
- Basse hors gamme naturelle globale : `+3.441 pp` (IC95 `-1.837` à `+8.719`).
- Blocs triadiques (6 renversements) : `-1.641 pp` (IC95 `-8.023` à `+4.741`).
- Blocs forts non triadiques : `+10.727 pp` (IC95 `+0.390` à `+21.064`).
- Dissonances par bloc faible : `+0.023` (IC95 `-0.092` à `+0.138`).
- Dissonances par bloc fort : `+0.297` (IC95 `+0.129` à `+0.466`).
- {0,3,6,8} sur bloc fort : `+1.203 pp` (IC95 `-1.082` à `+3.488`).
- {0,3,6,8} sur bloc faible : `+2.061 pp` (IC95 `-0.551` à `+4.673`).
