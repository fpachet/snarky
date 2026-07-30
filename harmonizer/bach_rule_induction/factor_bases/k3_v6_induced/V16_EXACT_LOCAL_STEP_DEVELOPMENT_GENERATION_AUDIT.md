# Audit génératif explicite de la basse et des sonorités

`20` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V13 | V16-local |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.37 % | 26.51 % | 25.37 % |
| Répétitions à la basse | 3.41 % | 3.74 % | 4.70 % |
| Sauts de basse > 4 demi-tons | 27.95 % | 29.63 % | 31.60 % |
| Basse hors gamme naturelle globale | 8.61 % | 12.91 % | 11.86 % |
| Blocs triadiques (6 renversements) | 52.37 % | 50.96 % | 51.83 % |
| Blocs forts non triadiques | 27.56 % | 40.16 % | 40.63 % |
| Dissonances par bloc faible | 0.962 | 0.906 | 0.878 |
| Dissonances par bloc fort | 0.381 | 0.600 | 0.626 |
| {0,3,6,8} sur bloc fort | 1.60 % | 3.26 % | 2.92 % |
| {0,3,6,8} sur bloc faible | 3.14 % | 3.40 % | 2.86 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V13

- Demi-tons à la basse : `+1.140 pp` (IC95 `-0.971` à `+3.251`).
- Répétitions à la basse : `+0.330 pp` (IC95 `-1.144` à `+1.804`).
- Sauts de basse > 4 demi-tons : `+1.680 pp` (IC95 `-0.951` à `+4.311`).
- Basse hors gamme naturelle globale : `+4.302 pp` (IC95 `+2.006` à `+6.598`).
- Blocs triadiques (6 renversements) : `-1.402 pp` (IC95 `-4.350` à `+1.546`).
- Blocs forts non triadiques : `+12.607 pp` (IC95 `+5.736` à `+19.477`).
- Dissonances par bloc faible : `-0.056` (IC95 `-0.127` à `+0.015`).
- Dissonances par bloc fort : `+0.219` (IC95 `+0.103` à `+0.335`).
- {0,3,6,8} sur bloc fort : `+1.659 pp` (IC95 `+0.137` à `+3.182`).
- {0,3,6,8} sur bloc faible : `+0.262 pp` (IC95 `-1.048` à `+1.572`).

### V16-local

- Demi-tons à la basse : `+0.000 pp` (IC95 `-2.413` à `+2.413`).
- Répétitions à la basse : `+1.283 pp` (IC95 `-0.444` à `+3.010`).
- Sauts de basse > 4 demi-tons : `+3.646 pp` (IC95 `+0.984` à `+6.307`).
- Basse hors gamme naturelle globale : `+3.247 pp` (IC95 `+0.836` à `+5.658`).
- Blocs triadiques (6 renversements) : `-0.541 pp` (IC95 `-3.868` à `+2.786`).
- Blocs forts non triadiques : `+13.069 pp` (IC95 `+5.845` à `+20.293`).
- Dissonances par bloc faible : `-0.084` (IC95 `-0.161` à `-0.007`).
- Dissonances par bloc fort : `+0.244` (IC95 `+0.123` à `+0.365`).
- {0,3,6,8} sur bloc fort : `+1.320 pp` (IC95 `-0.037` à `+2.677`).
- {0,3,6,8} sur bloc faible : `-0.271 pp` (IC95 `-1.572` à `+1.029`).
