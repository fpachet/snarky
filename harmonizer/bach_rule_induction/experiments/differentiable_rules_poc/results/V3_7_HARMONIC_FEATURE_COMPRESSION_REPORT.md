# POC V3.7 — compression des statuts harmoniques

## Protocole

- Contrôle nul : `False`.
- Cinq plis par groupes de chorals, sans sélection sur le pli tenu à part.
- Les groupes de sopranos dupliqués restent dans le même pli.
- Gradient conditionnel Adam avec parcimonie L1.
- Bootstrap par chorals entiers à pertes cross-fittées fixes.
- Test final non ouvert.

## Audit des cas atypiques

- train : 11 cas proxy seuls, 2 exceptions du contexte exact, soit 13 cas atypiques.
- validation : 7 cas proxy seuls, 0 exceptions du contexte exact, soit 7 cas atypiques.

## Modèles

| Modèle | Paramètres | Bits descriptifs | NLL cross-fit | Gain conservé | NLL validation |
|---|---:|---:|---:|---:|---:|
| baseline | 0 | 0 | 1.281680 | 0.000 | 1.276210 |
| proxy | 1 | 108 | 1.278527 | 0.879 | 1.269022 |
| exact | 1 | 132 | — | — | 1.270669 |
| both | 2 | 240 | 1.278093 | 1.000 | 1.268457 |
| vii_core | 1 | 132 | — | — | 1.269976 |
| dominant_core | 1 | 132 | — | — | 1.268920 |
| graded_exact | 1 | 144 | 1.278094 | 1.000 | 1.268430 |
| graded_vii_core | 1 | 144 | 1.278251 | 0.956 | 1.268428 |
| graded_dominant_core | 1 | 144 | 1.278223 | 0.964 | 1.268154 |

## Sélection gelable

Modèle retenu : `graded_exact`.
Seuil de conservation du gain cross-fitté : `0.950`.
