# Audit génératif explicite de la basse et des sonorités

`10` chorals de validation, `1` graine(s), `6` balayages. Même soprano, rythme et blocs de bord pour Bach et chaque modèle. Test fermé.

Chaque valeur est d'abord calculée par pièce, puis moyennée pour ne pas
donner davantage de poids aux chorals longs.

| Mesure | Bach | V5.16 |
|---|---:|---:|
| Demi-tons à la basse | 25.73 % | 26.32 % |
| Répétitions à la basse | 3.11 % | 4.61 % |
| Sauts de basse > 4 demi-tons | 28.03 % | 24.35 % |
| Basse hors gamme naturelle globale | 10.08 % | 8.80 % |
| Blocs triadiques (6 renversements) | 53.86 % | 56.08 % |
| Blocs forts non triadiques | 28.20 % | 27.52 % |
| Dissonances par bloc faible | 0.893 | 0.839 |
| Dissonances par bloc fort | 0.406 | 0.362 |
| {0,3,6,8} sur bloc fort | 1.79 % | 2.35 % |
| {0,3,6,8} sur bloc faible | 3.20 % | 5.77 % |

## Écarts appariés à Bach

Les intervalles ci-dessous portent sur `modèle − Bach`, pièce par
pièce. Un intervalle recouvrant zéro ne démontre pas une différence
stable dans ce petit audit.

### V5.16

- Demi-tons à la basse : `+0.591 pp` (IC95 `-3.747` à `+4.929`).
- Répétitions à la basse : `+1.493 pp` (IC95 `-1.602` à `+4.587`).
- Sauts de basse > 4 demi-tons : `-3.685 pp` (IC95 `-9.370` à `+2.000`).
- Basse hors gamme naturelle globale : `-1.281 pp` (IC95 `-5.316` à `+2.755`).
- Blocs triadiques (6 renversements) : `+2.219 pp` (IC95 `-2.566` à `+7.003`).
- Blocs forts non triadiques : `-0.680 pp` (IC95 `-8.711` à `+7.351`).
- Dissonances par bloc faible : `-0.054` (IC95 `-0.184` à `+0.077`).
- Dissonances par bloc fort : `-0.044` (IC95 `-0.175` à `+0.086`).
- {0,3,6,8} sur bloc fort : `+0.555 pp` (IC95 `-3.235` à `+4.344`).
- {0,3,6,8} sur bloc faible : `+2.573 pp` (IC95 `+1.149` à `+3.996`).
