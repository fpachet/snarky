# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `5` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V24 | V25 |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 26.57 % | 26.11 % |
| Répétitions à la basse | 3.71 % | 3.19 % | 3.07 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 27.06 % | 27.65 % |
| Basse hors gamme naturelle globale | 7.14 % | 12.25 % | 11.69 % |
| Blocs triadiques (6 renversements) | 50.87 % | 50.39 % | 50.39 % |
| Blocs forts non triadiques | 26.91 % | 30.49 % | 31.91 % |
| Dissonances par bloc faible | 1.032 | 1.080 | 1.051 |
| Dissonances par bloc fort | 0.357 | 0.510 | 0.552 |
| {0,3,6,8} sur bloc fort | 1.40 % | 1.92 % | 2.96 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 4.23 % | 4.59 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V24

- Demi-tons à la basse : `+1.565 pp` (IC95 `-1.651` à `+4.782`).
- Répétitions à la basse : `-0.524 pp` (IC95 `-3.027` à `+1.980`).
- Sauts de basse > 4 demi-tons : `-0.806 pp` (IC95 `-4.066` à `+2.453`).
- Basse hors gamme naturelle globale : `+5.108 pp` (IC95 `+2.439` à `+7.778`).
- Blocs triadiques (6 renversements) : `-0.483 pp` (IC95 `-5.744` à `+4.777`).
- Blocs forts non triadiques : `+3.579 pp` (IC95 `-6.645` à `+13.804`).
- Dissonances par bloc faible : `+0.048` (IC95 `-0.051` à `+0.147`).
- Dissonances par bloc fort : `+0.154` (IC95 `-0.012` à `+0.319`).
- {0,3,6,8} sur bloc fort : `+0.513 pp` (IC95 `-1.588` à `+2.615`).
- {0,3,6,8} sur bloc faible : `+1.158 pp` (IC95 `-1.006` à `+3.322`).

### V25

- Demi-tons à la basse : `+1.108 pp` (IC95 `-1.800` à `+4.017`).
- Répétitions à la basse : `-0.647 pp` (IC95 `-3.486` à `+2.192`).
- Sauts de basse > 4 demi-tons : `-0.218 pp` (IC95 `-3.226` à `+2.790`).
- Basse hors gamme naturelle globale : `+4.547 pp` (IC95 `+1.519` à `+7.575`).
- Blocs triadiques (6 renversements) : `-0.484 pp` (IC95 `-5.716` à `+4.748`).
- Blocs forts non triadiques : `+5.004 pp` (IC95 `-5.465` à `+15.472`).
- Dissonances par bloc faible : `+0.018` (IC95 `-0.109` à `+0.146`).
- Dissonances par bloc fort : `+0.195` (IC95 `+0.010` à `+0.381`).
- {0,3,6,8} sur bloc fort : `+1.556 pp` (IC95 `-0.679` à `+3.791`).
- {0,3,6,8} sur bloc faible : `+1.519 pp` (IC95 `-0.941` à `+3.978`).
