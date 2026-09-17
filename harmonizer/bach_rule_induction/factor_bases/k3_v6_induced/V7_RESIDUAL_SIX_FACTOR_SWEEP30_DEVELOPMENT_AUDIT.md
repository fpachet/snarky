# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `30` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Iteration2 | V7 |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 25.53 % | 24.74 % |
| Répétitions à la basse | 3.71 % | 3.94 % | 3.57 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 28.42 % | 22.90 % |
| Basse hors gamme naturelle globale | 7.14 % | 7.15 % | 7.25 % |
| Blocs triadiques (6 renversements) | 50.87 % | 54.77 % | 53.19 % |
| Blocs forts non triadiques | 26.91 % | 24.78 % | 25.38 % |
| Dissonances par bloc faible | 1.032 | 0.921 | 0.942 |
| Dissonances par bloc fort | 0.357 | 0.349 | 0.341 |
| {0,3,6,8} sur bloc fort | 1.40 % | 1.57 % | 0.93 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 4.09 % | 3.52 % |

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

### V7

- Demi-tons à la basse : `-0.263 pp` (IC95 `-3.876` à `+3.349`).
- Répétitions à la basse : `-0.143 pp` (IC95 `-3.228` à `+2.941`).
- Sauts de basse > 4 demi-tons : `-4.972 pp` (IC95 `-10.050` à `+0.106`).
- Basse hors gamme naturelle globale : `+0.112 pp` (IC95 `-2.553` à `+2.777`).
- Blocs triadiques (6 renversements) : `+2.320 pp` (IC95 `-3.158` à `+7.799`).
- Blocs forts non triadiques : `-1.528 pp` (IC95 `-11.522` à `+8.466`).
- Dissonances par bloc faible : `-0.090` (IC95 `-0.227` à `+0.046`).
- Dissonances par bloc fort : `-0.015` (IC95 `-0.202` à `+0.172`).
- {0,3,6,8} sur bloc fort : `-0.476 pp` (IC95 `-2.563` à `+1.610`).
- {0,3,6,8} sur bloc faible : `+0.442 pp` (IC95 `-1.797` à `+2.681`).
