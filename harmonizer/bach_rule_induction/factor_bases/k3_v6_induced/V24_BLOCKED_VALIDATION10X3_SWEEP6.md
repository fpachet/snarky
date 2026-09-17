# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

`1` passe(s) conjointe(s) aux temps forts pour : `V24-blocked`.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V24 | V24-blocked |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 27.51 % | 28.03 % |
| Répétitions à la basse | 3.71 % | 4.16 % | 4.16 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 27.26 % | 27.19 % |
| Basse hors gamme naturelle globale | 7.14 % | 11.53 % | 11.19 % |
| Blocs triadiques (6 renversements) | 50.87 % | 51.27 % | 50.09 % |
| Blocs forts non triadiques | 26.91 % | 31.04 % | 33.01 % |
| Dissonances par bloc faible | 1.032 | 1.085 | 1.101 |
| Dissonances par bloc fort | 0.357 | 0.515 | 0.556 |
| {0,3,6,8} sur bloc fort | 1.40 % | 1.58 % | 1.74 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 3.97 % | 4.01 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V24

- Demi-tons à la basse : `+2.506 pp` (IC95 `-0.780` à `+5.792`).
- Répétitions à la basse : `+0.441 pp` (IC95 `-2.025` à `+2.906`).
- Sauts de basse > 4 demi-tons : `-0.613 pp` (IC95 `-3.942` à `+2.716`).
- Basse hors gamme naturelle globale : `+4.390 pp` (IC95 `+1.048` à `+7.733`).
- Blocs triadiques (6 renversements) : `+0.396 pp` (IC95 `-4.889` à `+5.682`).
- Blocs forts non triadiques : `+4.125 pp` (IC95 `-6.634` à `+14.885`).
- Dissonances par bloc faible : `+0.053` (IC95 `-0.061` à `+0.167`).
- Dissonances par bloc fort : `+0.159` (IC95 `-0.040` à `+0.357`).
- {0,3,6,8} sur bloc fort : `+0.173 pp` (IC95 `-1.664` à `+2.009`).
- {0,3,6,8} sur bloc faible : `+0.900 pp` (IC95 `-1.307` à `+3.106`).

### V24-blocked

- Demi-tons à la basse : `+3.031 pp` (IC95 `-0.525` à `+6.587`).
- Répétitions à la basse : `+0.446 pp` (IC95 `-2.385` à `+3.276`).
- Sauts de basse > 4 demi-tons : `-0.683 pp` (IC95 `-3.620` à `+2.255`).
- Basse hors gamme naturelle globale : `+4.046 pp` (IC95 `+0.967` à `+7.124`).
- Blocs triadiques (6 renversements) : `-0.785 pp` (IC95 `-6.437` à `+4.867`).
- Blocs forts non triadiques : `+6.100 pp` (IC95 `-4.610` à `+16.810`).
- Dissonances par bloc faible : `+0.068` (IC95 `-0.045` à `+0.181`).
- Dissonances par bloc fort : `+0.200` (IC95 `+0.002` à `+0.397`).
- {0,3,6,8} sur bloc fort : `+0.336 pp` (IC95 `-1.157` à `+1.830`).
- {0,3,6,8} sur bloc faible : `+0.938 pp` (IC95 `-1.164` à `+3.040`).
