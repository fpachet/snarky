# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `1` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test fermé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V5.9 | V5.12 |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 34.92 % | 18.38 % |
| Répétitions à la basse | 3.71 % | 6.53 % | 5.71 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 18.04 % | 30.08 % |
| Basse hors gamme naturelle globale | 7.14 % | 13.74 % | 6.91 % |
| Blocs triadiques (6 renversements) | 50.87 % | 59.18 % | 66.63 % |
| Blocs forts non triadiques | 26.91 % | 20.81 % | 9.02 % |
| Dissonances par bloc faible | 1.032 | 0.876 | 0.821 |
| Dissonances par bloc fort | 0.357 | 0.382 | 0.183 |
| {0,3,6,8} sur bloc fort | 1.40 % | 14.21 % | 4.10 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 10.43 % | 2.27 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V5.9

- Demi-tons à la basse : `+9.920 pp` (IC95 `+4.442` à `+15.399`).
- Répétitions à la basse : `+2.817 pp` (IC95 `-0.893` à `+6.526`).
- Sauts de basse > 4 demi-tons : `-9.832 pp` (IC95 `-14.644` à `-5.020`).
- Basse hors gamme naturelle globale : `+6.601 pp` (IC95 `+2.833` à `+10.370`).
- Blocs triadiques (6 renversements) : `+8.308 pp` (IC95 `+1.714` à `+14.902`).
- Blocs forts non triadiques : `-6.100 pp` (IC95 `-18.286` à `+6.087`).
- Dissonances par bloc faible : `-0.156` (IC95 `-0.321` à `+0.009`).
- Dissonances par bloc fort : `+0.025` (IC95 `-0.183` à `+0.234`).
- {0,3,6,8} sur bloc fort : `+12.802 pp` (IC95 `+8.787` à `+16.817`).
- {0,3,6,8} sur bloc faible : `+7.360 pp` (IC95 `+3.881` à `+10.838`).

### V5.12

- Demi-tons à la basse : `-6.619 pp` (IC95 `-10.850` à `-2.388`).
- Répétitions à la basse : `+1.993 pp` (IC95 `-0.581` à `+4.568`).
- Sauts de basse > 4 demi-tons : `+2.213 pp` (IC95 `-2.989` à `+7.415`).
- Basse hors gamme naturelle globale : `-0.233 pp` (IC95 `-3.808` à `+3.341`).
- Blocs triadiques (6 renversements) : `+15.758 pp` (IC95 `+9.878` à `+21.638`).
- Blocs forts non triadiques : `-17.886 pp` (IC95 `-28.841` à `-6.931`).
- Dissonances par bloc faible : `-0.211` (IC95 `-0.364` à `-0.058`).
- Dissonances par bloc fort : `-0.173` (IC95 `-0.355` à `+0.008`).
- {0,3,6,8} sur bloc fort : `+2.699 pp` (IC95 `-0.053` à `+5.451`).
- {0,3,6,8} sur bloc faible : `-0.808 pp` (IC95 `-2.744` à `+1.129`).
