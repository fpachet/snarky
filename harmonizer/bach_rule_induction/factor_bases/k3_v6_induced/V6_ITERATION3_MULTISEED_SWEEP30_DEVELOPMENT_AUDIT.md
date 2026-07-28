# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `30` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Iteration2 | Iteration3 |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 25.53 % | 26.16 % |
| Répétitions à la basse | 3.71 % | 3.94 % | 3.92 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 28.42 % | 28.06 % |
| Basse hors gamme naturelle globale | 7.14 % | 7.15 % | 7.09 % |
| Blocs triadiques (6 renversements) | 50.87 % | 54.77 % | 56.49 % |
| Blocs forts non triadiques | 26.91 % | 24.78 % | 23.24 % |
| Dissonances par bloc faible | 1.032 | 0.921 | 0.884 |
| Dissonances par bloc fort | 0.357 | 0.349 | 0.347 |
| {0,3,6,8} sur bloc fort | 1.40 % | 1.57 % | 1.71 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 4.09 % | 4.06 % |

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

### Iteration3

- Demi-tons à la basse : `+1.155 pp` (IC95 `-2.327` à `+4.636`).
- Répétitions à la basse : `+0.201 pp` (IC95 `-2.184` à `+2.585`).
- Sauts de basse > 4 demi-tons : `+0.194 pp` (IC95 `-4.132` à `+4.521`).
- Basse hors gamme naturelle globale : `-0.049 pp` (IC95 `-2.843` à `+2.745`).
- Blocs triadiques (6 renversements) : `+5.618 pp` (IC95 `+0.446` à `+10.790`).
- Blocs forts non triadiques : `-3.667 pp` (IC95 `-14.358` à `+7.023`).
- Dissonances par bloc faible : `-0.148` (IC95 `-0.282` à `-0.014`).
- Dissonances par bloc fort : `-0.010` (IC95 `-0.210` à `+0.190`).
- {0,3,6,8} sur bloc fort : `+0.302 pp` (IC95 `-1.817` à `+2.421`).
- {0,3,6,8} sur bloc faible : `+0.990 pp` (IC95 `-1.405` à `+3.384`).
