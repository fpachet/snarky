# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `30` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V13 | V18 |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 30.35 % | 29.28 % |
| Répétitions à la basse | 3.71 % | 3.77 % | 5.32 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 25.43 % | 24.93 % |
| Basse hors gamme naturelle globale | 7.14 % | 12.94 % | 12.95 % |
| Blocs triadiques (6 renversements) | 50.87 % | 53.03 % | 38.68 % |
| Blocs forts non triadiques | 26.91 % | 36.34 % | 53.90 % |
| Dissonances par bloc faible | 1.032 | 0.906 | 1.104 |
| Dissonances par bloc fort | 0.357 | 0.558 | 0.765 |
| {0,3,6,8} sur bloc fort | 1.40 % | 2.27 % | 0.65 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 3.12 % | 0.81 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V13

- Demi-tons à la basse : `+5.343 pp` (IC95 `+2.536` à `+8.151`).
- Répétitions à la basse : `+0.057 pp` (IC95 `-2.894` à `+3.007`).
- Sauts de basse > 4 demi-tons : `-2.439 pp` (IC95 `-7.049` à `+2.171`).
- Basse hors gamme naturelle globale : `+5.797 pp` (IC95 `+2.795` à `+8.800`).
- Blocs triadiques (6 renversements) : `+2.160 pp` (IC95 `-3.896` à `+8.215`).
- Blocs forts non triadiques : `+9.434 pp` (IC95 `-3.034` à `+21.902`).
- Dissonances par bloc faible : `-0.126` (IC95 `-0.219` à `-0.033`).
- Dissonances par bloc fort : `+0.202` (IC95 `-0.002` à `+0.405`).
- {0,3,6,8} sur bloc fort : `+0.868 pp` (IC95 `-0.571` à `+2.307`).
- {0,3,6,8} sur bloc faible : `+0.048 pp` (IC95 `-2.208` à `+2.305`).

### V18

- Demi-tons à la basse : `+4.278 pp` (IC95 `+0.278` à `+8.278`).
- Répétitions à la basse : `+1.603 pp` (IC95 `-0.293` à `+3.500`).
- Sauts de basse > 4 demi-tons : `-2.946 pp` (IC95 `-6.415` à `+0.523`).
- Basse hors gamme naturelle globale : `+5.807 pp` (IC95 `+3.020` à `+8.595`).
- Blocs triadiques (6 renversements) : `-12.187 pp` (IC95 `-18.817` à `-5.556`).
- Blocs forts non triadiques : `+26.986 pp` (IC95 `+15.269` à `+38.704`).
- Dissonances par bloc faible : `+0.072` (IC95 `-0.080` à `+0.223`).
- Dissonances par bloc fort : `+0.408` (IC95 `+0.190` à `+0.626`).
- {0,3,6,8} sur bloc fort : `-0.755 pp` (IC95 `-2.183` à `+0.672`).
- {0,3,6,8} sur bloc faible : `-2.266 pp` (IC95 `-4.153` à `-0.379`).
