# V5.15 — calibration K3 explicite de la basse et des sonorités

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
| basse : saut entrant supérieur à 4 demi-tons | `bass_motion` | 28.25 % | 16.79 % | +11.46 pp | +0.4658 |
| basse : saut entrant supérieur à 2 demi-tons | `bass_motion` | 35.94 % | 24.66 % | +11.27 pp | +0.4614 |
| basse : classe d'intervalle entrant 1 | `bass_motion` | 22.59 % | 30.69 % | -8.10 pp | -0.4534 |
| basse : directions K3 (-1, +0) | `bass_motion` | 13.68 % | 16.83 % | -3.15 pp | -0.4754 |

## Critères internes

- candidats explicites : `184` ;
- règles ajoutées : `4` ;
- erreur absolue moyenne des moments sélectionnés : `0.084963` → `0.014642` ;
- NLL validation avant : `1.133933` ;
- NLL validation après : `1.184205`.

Ces nombres ne suffisent pas à promouvoir le modèle. La décision
dépend de générations contrôlées multi-chorals et d'un retour
spécifique sur BWV 108.6.
