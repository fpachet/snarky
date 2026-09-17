# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `1` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V22 | V22+C | V23 | V23+C |
|---|---:|---:|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 25.58 % | 25.43 % | 23.58 % | 23.85 % |
| Répétitions à la basse | 3.71 % | 2.90 % | 3.84 % | 2.13 % | 3.12 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 27.75 % | 28.72 % | 29.02 % | 28.81 % |
| Basse hors gamme naturelle globale | 7.14 % | 11.59 % | 10.58 % | 11.15 % | 12.17 % |
| Blocs triadiques (6 renversements) | 50.87 % | 47.07 % | 49.23 % | 47.87 % | 45.38 % |
| Blocs forts non triadiques | 26.91 % | 37.55 % | 37.64 % | 33.36 % | 37.62 % |
| Dissonances par bloc faible | 1.032 | 1.172 | 1.055 | 1.127 | 1.175 |
| Dissonances par bloc fort | 0.357 | 0.688 | 0.654 | 0.552 | 0.649 |
| {0,3,6,8} sur bloc fort | 1.40 % | 4.38 % | 2.61 % | 2.07 % | 2.33 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 4.37 % | 5.13 % | 3.93 % | 3.15 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

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

### V23

- Demi-tons à la basse : `-1.419 pp` (IC95 `-5.356` à `+2.519`).
- Répétitions à la basse : `-1.580 pp` (IC95 `-4.057` à `+0.897`).
- Sauts de basse > 4 demi-tons : `+1.154 pp` (IC95 `-2.304` à `+4.613`).
- Basse hors gamme naturelle globale : `+4.008 pp` (IC95 `-1.420` à `+9.437`).
- Blocs triadiques (6 renversements) : `-3.004 pp` (IC95 `-8.480` à `+2.472`).
- Blocs forts non triadiques : `+6.449 pp` (IC95 `-2.290` à `+15.188`).
- Dissonances par bloc faible : `+0.095` (IC95 `-0.033` à `+0.223`).
- Dissonances par bloc fort : `+0.195` (IC95 `+0.014` à `+0.375`).
- {0,3,6,8} sur bloc fort : `+0.668 pp` (IC95 `-1.699` à `+3.034`).
- {0,3,6,8} sur bloc faible : `+0.859 pp` (IC95 `-1.316` à `+3.035`).

### V23+C

- Demi-tons à la basse : `-1.151 pp` (IC95 `-4.412` à `+2.110`).
- Répétitions à la basse : `-0.592 pp` (IC95 `-3.527` à `+2.343`).
- Sauts de basse > 4 demi-tons : `+0.943 pp` (IC95 `-3.503` à `+5.390`).
- Basse hors gamme naturelle globale : `+5.029 pp` (IC95 `+1.190` à `+8.868`).
- Blocs triadiques (6 renversements) : `-5.491 pp` (IC95 `-9.620` à `-1.362`).
- Blocs forts non triadiques : `+10.708 pp` (IC95 `+1.430` à `+19.987`).
- Dissonances par bloc faible : `+0.143` (IC95 `+0.055` à `+0.230`).
- Dissonances par bloc fort : `+0.292` (IC95 `+0.128` à `+0.457`).
- {0,3,6,8} sur bloc fort : `+0.925 pp` (IC95 `-1.079` à `+2.929`).
- {0,3,6,8} sur bloc faible : `+0.078 pp` (IC95 `-1.769` à `+1.925`).
