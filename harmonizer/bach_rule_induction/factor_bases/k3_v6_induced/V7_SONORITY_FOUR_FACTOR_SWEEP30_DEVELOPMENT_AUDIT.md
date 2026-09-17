# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `30` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Iteration2 | V7Sonority |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 25.53 % | 24.71 % |
| Répétitions à la basse | 3.71 % | 3.94 % | 4.29 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 28.42 % | 28.21 % |
| Basse hors gamme naturelle globale | 7.14 % | 7.15 % | 6.74 % |
| Blocs triadiques (6 renversements) | 50.87 % | 54.77 % | 57.16 % |
| Blocs forts non triadiques | 26.91 % | 24.78 % | 21.94 % |
| Dissonances par bloc faible | 1.032 | 0.921 | 0.867 |
| Dissonances par bloc fort | 0.357 | 0.349 | 0.282 |
| {0,3,6,8} sur bloc fort | 1.40 % | 1.57 % | 1.00 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 4.09 % | 3.80 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### Iteration2

- Demi-tons à la basse : `+0.525 pp` (IC95 `-3.330` à `+4.379`).
- Répétitions à la basse : `+0.228 pp` (IC95 `-2.020` à `+2.477`).
- Sauts de basse > 4 demi-tons : `+0.553 pp` (IC95 `-3.433` à `+4.539`).
- Basse hors gamme naturelle globale : `+0.010 pp` (IC95 `-2.753` à `+2.772`).
- Blocs triadiques (6 renversements) : `+3.902 pp` (IC95 `-1.019` à `+8.823`).
- Blocs forts non triadiques : `-2.127 pp` (IC95 `-13.330` à `+9.075`).
- Dissonances par bloc faible : `-0.111` (IC95 `-0.260` à `+0.037`).
- Dissonances par bloc fort : `-0.008` (IC95 `-0.216` à `+0.201`).
- {0,3,6,8} sur bloc fort : `+0.163 pp` (IC95 `-1.855` à `+2.180`).
- {0,3,6,8} sur bloc faible : `+1.013 pp` (IC95 `-1.036` à `+3.063`).

### V7Sonority

- Demi-tons à la basse : `-0.296 pp` (IC95 `-4.516` à `+3.923`).
- Répétitions à la basse : `+0.571 pp` (IC95 `-2.062` à `+3.205`).
- Sauts de basse > 4 demi-tons : `+0.344 pp` (IC95 `-2.818` à `+3.505`).
- Basse hors gamme naturelle globale : `-0.398 pp` (IC95 `-3.650` à `+2.854`).
- Blocs triadiques (6 renversements) : `+6.286 pp` (IC95 `+0.681` à `+11.892`).
- Blocs forts non triadiques : `-4.967 pp` (IC95 `-14.610` à `+4.677`).
- Dissonances par bloc faible : `-0.165` (IC95 `-0.301` à `-0.029`).
- Dissonances par bloc fort : `-0.074` (IC95 `-0.236` à `+0.087`).
- {0,3,6,8} sur bloc fort : `-0.405 pp` (IC95 `-2.399` à `+1.589`).
- {0,3,6,8} sur bloc faible : `+0.730 pp` (IC95 `-1.407` à `+2.867`).
