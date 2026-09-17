# Audit génératif explicite de la basse et des sonorités

`50` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | Iteration2 | V7Sonority |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.67 % | 26.13 % | 25.69 % |
| Répétitions à la basse | 3.37 % | 4.42 % | 4.75 % |
| Sauts de basse > 4 demi-tons | 26.76 % | 27.25 % | 28.54 % |
| Basse hors gamme naturelle globale | 8.15 % | 9.68 % | 9.48 % |
| Blocs triadiques (6 renversements) | 52.74 % | 52.23 % | 52.37 % |
| Blocs forts non triadiques | 28.72 % | 31.30 % | 28.62 % |
| Dissonances par bloc faible | 0.987 | 0.893 | 0.925 |
| Dissonances par bloc fort | 0.410 | 0.449 | 0.409 |
| {0,3,6,8} sur bloc fort | 2.17 % | 1.92 % | 1.36 % |
| {0,3,6,8} sur bloc faible | 2.93 % | 4.24 % | 3.85 % |

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

### V7Sonority

- Demi-tons à la basse : `+0.023 pp` (IC95 `-1.827` à `+1.872`).
- Répétitions à la basse : `+1.382 pp` (IC95 `+0.512` à `+2.252`).
- Sauts de basse > 4 demi-tons : `+1.781 pp` (IC95 `-0.100` à `+3.661`).
- Basse hors gamme naturelle globale : `+1.327 pp` (IC95 `-0.241` à `+2.895`).
- Blocs triadiques (6 renversements) : `-0.374 pp` (IC95 `-2.479` à `+1.730`).
- Blocs forts non triadiques : `-0.108 pp` (IC95 `-3.311` à `+3.096`).
- Dissonances par bloc faible : `-0.062` (IC95 `-0.141` à `+0.017`).
- Dissonances par bloc fort : `-0.000` (IC95 `-0.054` à `+0.053`).
- {0,3,6,8} sur bloc fort : `-0.806 pp` (IC95 `-1.770` à `+0.157`).
- {0,3,6,8} sur bloc faible : `+0.925 pp` (IC95 `+0.099` à `+1.750`).
