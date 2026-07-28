# Audit génératif explicite de la basse et des sonorités

`50` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Iteration2 | Iteration3 |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.67 % | 26.13 % | 25.15 % |
| Répétitions à la basse | 3.37 % | 4.42 % | 4.81 % |
| Sauts de basse > 4 demi-tons | 26.76 % | 27.25 % | 27.80 % |
| Basse hors gamme naturelle globale | 8.15 % | 9.68 % | 9.45 % |
| Blocs triadiques (6 renversements) | 52.74 % | 52.23 % | 53.01 % |
| Blocs forts non triadiques | 28.72 % | 31.30 % | 29.65 % |
| Dissonances par bloc faible | 0.987 | 0.893 | 0.907 |
| Dissonances par bloc fort | 0.410 | 0.449 | 0.405 |
| {0,3,6,8} sur bloc fort | 2.17 % | 1.92 % | 1.80 % |
| {0,3,6,8} sur bloc faible | 2.93 % | 4.24 % | 4.20 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### Iteration2

- Demi-tons à la basse : `+0.461 pp` (IC95 `-1.255` à `+2.177`).
- Répétitions à la basse : `+1.051 pp` (IC95 `+0.144` à `+1.957`).
- Sauts de basse > 4 demi-tons : `+0.498 pp` (IC95 `-1.358` à `+2.354`).
- Basse hors gamme naturelle globale : `+1.522 pp` (IC95 `-0.062` à `+3.106`).
- Blocs triadiques (6 renversements) : `-0.514 pp` (IC95 `-2.404` à `+1.376`).
- Blocs forts non triadiques : `+2.575 pp` (IC95 `-0.838` à `+5.987`).
- Dissonances par bloc faible : `-0.094` (IC95 `-0.191` à `+0.003`).
- Dissonances par bloc fort : `+0.040` (IC95 `-0.021` à `+0.100`).
- {0,3,6,8} sur bloc fort : `-0.250 pp` (IC95 `-1.268` à `+0.769`).
- {0,3,6,8} sur bloc faible : `+1.312 pp` (IC95 `+0.485` à `+2.139`).

### Iteration3

- Demi-tons à la basse : `-0.521 pp` (IC95 `-2.348` à `+1.306`).
- Répétitions à la basse : `+1.436 pp` (IC95 `+0.513` à `+2.359`).
- Sauts de basse > 4 demi-tons : `+1.042 pp` (IC95 `-0.753` à `+2.837`).
- Basse hors gamme naturelle globale : `+1.296 pp` (IC95 `-0.357` à `+2.948`).
- Blocs triadiques (6 renversements) : `+0.270 pp` (IC95 `-1.625` à `+2.165`).
- Blocs forts non triadiques : `+0.921 pp` (IC95 `-2.431` à `+4.273`).
- Dissonances par bloc faible : `-0.080` (IC95 `-0.142` à `-0.017`).
- Dissonances par bloc fort : `-0.004` (IC95 `-0.058` à `+0.049`).
- {0,3,6,8} sur bloc fort : `-0.371 pp` (IC95 `-1.398` à `+0.656`).
- {0,3,6,8} sur bloc faible : `+1.278 pp` (IC95 `+0.338` à `+2.218`).
