# V5.14 — calibration K3 explicite de la basse et des sonorités

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
| basse : saut entrant supérieur à 4 demi-tons | `bass_motion` | 28.25 % | 8.93 % | +19.32 pp | +0.2786 |
| basse : saut entrant supérieur à 2 demi-tons | `bass_motion` | 35.94 % | 15.25 % | +20.69 pp | +0.2781 |
| basse : classe d'intervalle entrant 1 | `bass_motion` | 22.59 % | 38.57 % | -15.98 pp | -0.2795 |
| intervalle vertical 7 présent sur bloc métrique fort | `vertical_context` | 20.06 % | 11.69 % | +8.36 pp | +0.2746 |
| sonorité {0, 4, 7} relative à la basse, bloc fort | `vertical_context` | 14.31 % | 5.78 % | +8.52 pp | +0.2774 |
| intervalle vertical 6 présent sur bloc métrique fort | `vertical_context` | 2.38 % | 6.78 % | -4.40 pp | -0.2637 |
| intervalle vertical 5 présent sur bloc métrique faible | `vertical_context` | 15.39 % | 19.67 % | -4.29 pp | -0.2567 |
| transition {0, 4, 7} → {0, 4, 7, 10} | `sonority_transition` | 3.91 % | 0.14 % | +3.77 pp | +0.2781 |
| basse : classe d'intervalle entrant 2 | `bass_motion` | 36.23 % | 40.21 % | -3.98 pp | -0.2680 |
| transition {0, 4, 7} → {0, 4, 7} | `sonority_transition` | 9.06 % | 4.24 % | +4.82 pp | +0.2715 |
| transition {0, 3, 8} → {0, 3, 8} | `sonority_transition` | 0.67 % | 2.72 % | -2.05 pp | -0.2642 |
| transition {0, 5, 8} → {0, 3, 8} | `sonority_transition` | 0.09 % | 0.88 % | -0.79 pp | -0.2412 |

## Critères internes

- candidats explicites : `196` ;
- règles ajoutées : `12` ;
- erreur absolue moyenne des moments sélectionnés : `0.080810` → `0.064365` ;
- NLL validation avant : `1.130530` ;
- NLL validation après : `1.133933`.

Ces nombres ne suffisent pas à promouvoir le modèle. La décision
dépend de générations contrôlées multi-chorals et d'un retour
spécifique sur BWV 108.6.
