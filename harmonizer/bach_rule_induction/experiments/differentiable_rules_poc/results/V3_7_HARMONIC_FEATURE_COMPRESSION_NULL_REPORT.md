# POC V3.7 — compression des statuts harmoniques

## Protocole

- Contrôle nul : `True`.
- Cinq plis par groupes de chorals, sans sélection sur le pli tenu à part.
- Les groupes de sopranos dupliqués restent dans le même pli.
- Gradient conditionnel Adam avec parcimonie L1.
- Bootstrap par chorals entiers à pertes cross-fittées fixes.
- Test final non ouvert.

## Audit des cas atypiques

- train : 11 cas proxy seuls, 34 exceptions du contexte exact, soit 45 cas atypiques.
- validation : 7 cas proxy seuls, 9 exceptions du contexte exact, soit 16 cas atypiques.

## Modèles

| Modèle | Paramètres | Bits descriptifs | NLL cross-fit | Gain conservé | NLL validation |
|---|---:|---:|---:|---:|---:|
| baseline | 0 | 0 | 2.341773 | 0.000 | 2.346328 |
| proxy | 1 | 108 | 2.341631 | 1.275 | 2.345765 |
| exact | 1 | 132 | — | — | 2.345870 |
| both | 2 | 240 | 2.341661 | 1.000 | 2.345773 |
| vii_core | 1 | 132 | — | — | 2.345552 |
| dominant_core | 1 | 132 | — | — | 2.345743 |
| graded_exact | 1 | 144 | 2.341617 | 1.392 | 2.345762 |
| graded_vii_core | 1 | 144 | 2.341614 | 1.426 | 2.345642 |
| graded_dominant_core | 1 | 144 | 2.341616 | 1.406 | 2.345750 |

## Sélection gelable

Modèle retenu : `None`.
Seuil de conservation du gain cross-fitté : `0.950`.
