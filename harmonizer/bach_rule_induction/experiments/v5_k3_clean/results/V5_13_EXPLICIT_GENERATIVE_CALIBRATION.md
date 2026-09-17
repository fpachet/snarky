# V5.13 — calibration K3 explicite de la basse et des sonorités

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
| basse : saut entrant supérieur à 4 demi-tons | `bass_motion` | 28.25 % | 17.84 % | +10.41 pp | +0.2790 |
| basse : saut entrant supérieur à 1 demi-tons | `bass_motion` | 72.03 % | 62.14 % | +9.89 pp | +0.2782 |
| basse : classe d'intervalle entrant 1 | `bass_motion` | 22.59 % | 31.31 % | -8.72 pp | -0.2771 |
| sonorité {0, 3, 6, 8} relative à la basse, bloc fort | `vertical_context` | 0.45 % | 7.64 % | -7.19 pp | -0.2761 |
| intervalle vertical 8 présent sur bloc métrique faible | `vertical_context` | 12.73 % | 16.60 % | -3.87 pp | -0.2733 |
| basse : classe d'intervalle entrant 3 | `bass_motion` | 3.56 % | 6.29 % | -2.73 pp | -0.2743 |
| sonorité {0, 4, 9} relative à la basse, bloc faible | `vertical_context` | 4.13 % | 0.64 % | +3.49 pp | +0.2779 |
| transition {0, 4, 7} → {0, 3, 6, 8} | `sonority_transition` | 0.20 % | 3.40 % | -3.20 pp | -0.2754 |
| transition {0, 3, 6, 8} → {0, 4, 7} | `sonority_transition` | 0.88 % | 4.45 % | -3.57 pp | -0.2715 |
| transition {0, 4, 7} → {0, 4, 7, 10} | `sonority_transition` | 3.91 % | 0.43 % | +3.48 pp | +0.2768 |
| sonorité {0, 4, 7, 10} relative à la basse, bloc faible | `vertical_context` | 1.99 % | 0.21 % | +1.78 pp | +0.2747 |
| transition {0, 5, 7} → {0, 4, 7} | `sonority_transition` | 2.34 % | 0.02 % | +2.32 pp | +0.2780 |

## Critères internes

- candidats explicites : `172` ;
- règles ajoutées : `12` ;
- erreur absolue moyenne des moments sélectionnés : `0.050539` → `0.042038` ;
- NLL validation avant : `1.130530` ;
- NLL validation après : `1.130398`.

Ces nombres ne suffisent pas à promouvoir le modèle. La décision
dépend de générations contrôlées multi-chorals et d'un retour
spécifique sur BWV 108.6.
