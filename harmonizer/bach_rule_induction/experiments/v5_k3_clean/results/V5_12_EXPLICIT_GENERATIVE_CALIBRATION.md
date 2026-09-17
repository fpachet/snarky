# V5.12 — calibration K3 explicite de la basse et des sonorités

V5.11 n'est pas utilisée. Toutes les variables sont directement
observables dans trois blocs : mouvement de basse, niveau métrique,
intervalles verticaux et empreintes de sonorité relatives à la basse.

Le gradient reste :

`g_r = E_Bach[f_r] - E_Gibbs[f_r]`.

Calibration sur `16` chorals
du train. Validation utilisée seulement pour la NLL finale ; test fermé.

## Règles retenues

| Règle observable | Famille | Bach | Gibbs initial | Gradient | Poids |
|---|---|---:|---:|---:|---:|
| basse : saut entrant supérieur à 4 demi-tons | `bass_motion` | 28.25 % | 15.13 % | +13.12 pp | +0.4906 |
| basse : saut entrant supérieur à 1 demi-tons | `bass_motion` | 72.03 % | 57.94 % | +14.10 pp | +0.4756 |
| basse : saut entrant supérieur à 2 demi-tons | `bass_motion` | 35.94 % | 25.57 % | +10.36 pp | +0.4833 |
| basse : classe d'intervalle entrant 1 | `bass_motion` | 22.59 % | 33.78 % | -11.19 pp | -0.4760 |
| sonorité {0, 3, 6, 8} relative à la basse, bloc fort | `vertical_context` | 0.45 % | 6.22 % | -5.77 pp | -0.4825 |
| intervalle vertical 8 présent sur bloc métrique fort | `vertical_context` | 11.03 % | 15.67 % | -4.64 pp | -0.4763 |
| sonorité {0, 3, 6, 8} relative à la basse, bloc faible | `vertical_context` | 2.30 % | 8.81 % | -6.51 pp | -0.4589 |
| intervalle vertical 8 présent sur bloc métrique faible | `vertical_context` | 12.73 % | 17.35 % | -4.62 pp | -0.4726 |
| transition {0, 3, 6, 8} → {0, 3, 6, 8} | `sonority_transition` | 0.00 % | 3.20 % | -3.20 pp | -0.4382 |
| transition {0, 4, 7} → {0, 4, 7, 10} | `sonority_transition` | 3.91 % | 0.60 % | +3.31 pp | +0.4702 |
| transition {0, 3, 6, 8} → {0, 4, 7} | `sonority_transition` | 0.88 % | 3.81 % | -2.93 pp | -0.4340 |
| transition {0, 4, 7} → {0, 3, 6, 8} | `sonority_transition` | 0.20 % | 2.67 % | -2.47 pp | -0.4569 |

## Critères internes

- candidats explicites : `175` ;
- règles ajoutées : `12` ;
- erreur absolue moyenne des moments sélectionnés : `0.068524` → `0.024533` ;
- NLL validation avant : `1.130530` ;
- NLL validation après : `1.181668`.

Ces nombres ne suffisent pas à promouvoir le modèle. La décision
dépend de générations contrôlées multi-chorals et d'un retour
spécifique sur BWV 108.6.
