# V4.2 — Induction de l'ordre simultané des voix

Cette expérience exploratoire est déclenchée par les croisements et
unissons des générations V4.1. Elle recherche uniformément cinq seuils
numériques autour de la frontière zéro, sans consulter la règle
historique correspondante.

## Scan authentique

| Seuil | z train | z validation | contraste local validation |
|---:|---:|---:|---:|
| -2 | -34.802 | -16.634 | — |
| -1 | -38.779 | -18.364 | -0.495 |
| 0 | -34.201 | -17.088 | 0.423 |
| 1 | -33.867 | -16.558 | -0.092 |
| 2 | -21.557 | -11.374 | — |

## Sélection

- seuil : `-1` ;
- poids ajusté : `-1.538768` ;
- gain NLL train : `0.014220` ;
- gain NLL validation : `0.017207`.

## Contrôle nul

Le contrôle retient le seuil `-1` : la famille doit rester candidate.

## Statut

`CANDIDATE` : un seul mélange nul ne constitue pas une calibration
familiale suffisante. La règle ne rejoint pas encore `S-LEARNED`.
