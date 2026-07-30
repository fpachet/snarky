# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `3` graine(s), `30` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test réservé non chargé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V18 | V19 |
|---|---:|---:|---:|
| Demi-tons à la basse | 25.00 % | 29.28 % | 28.36 % |
| Répétitions à la basse | 3.71 % | 5.32 % | 4.27 % |
| Sauts de basse > 4 demi-tons | 27.87 % | 24.93 % | 25.26 % |
| Basse hors gamme naturelle globale | 7.14 % | 12.95 % | 13.36 % |
| Blocs triadiques (6 renversements) | 50.87 % | 38.68 % | 52.58 % |
| Blocs forts non triadiques | 26.91 % | 53.90 % | 32.44 % |
| Dissonances par bloc faible | 1.032 | 1.104 | 0.936 |
| Dissonances par bloc fort | 0.357 | 0.765 | 0.533 |
| {0,3,6,8} sur bloc fort | 1.40 % | 0.65 % | 0.22 % |
| {0,3,6,8} sur bloc faible | 3.07 % | 0.81 % | 0.91 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

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

### V19

- Demi-tons à la basse : `+3.361 pp` (IC95 `+0.181` à `+6.541`).
- Répétitions à la basse : `+0.554 pp` (IC95 `-2.186` à `+3.294`).
- Sauts de basse > 4 demi-tons : `-2.607 pp` (IC95 `-5.954` à `+0.739`).
- Basse hors gamme naturelle globale : `+6.215 pp` (IC95 `+3.147` à `+9.283`).
- Blocs triadiques (6 renversements) : `+1.711 pp` (IC95 `-4.691` à `+8.113`).
- Blocs forts non triadiques : `+5.526 pp` (IC95 `-6.152` à `+17.203`).
- Dissonances par bloc faible : `-0.096` (IC95 `-0.222` à `+0.029`).
- Dissonances par bloc fort : `+0.176` (IC95 `-0.016` à `+0.368`).
- {0,3,6,8} sur bloc fort : `-1.181 pp` (IC95 `-2.888` à `+0.526`).
- {0,3,6,8} sur bloc faible : `-2.168 pp` (IC95 `-3.901` à `-0.434`).
