# V5-K3-CLEAN — premier cycle d'induction

## Protocole

- Base musicale initiale vide.
- Une note masquée et trois blocs verticaux consécutifs.
- Domaine commun de hauteurs dérivé du seul train.
- Aucun manifeste ni fichier de règles V1–V4 chargé.
- Sélection des colonnes sur le gradient résiduel du train.
- Les noms musicologiques ne sont appliqués qu'après sélection.
- Données authentiques, sans permutation.

## Corpus

- Train : `251` chorals, `68263` décisions.
- Validation : `50` chorals, `13202` décisions.
- Ancien test : `51` chorals non chargés.
- Domaine commun train : MIDI `36` à `81`.
- Choix validation hors domaine : `0`.

## Modèle

- NLL validation registre seul : `2.594465`.
- Meilleure NLL validation : `1.449123`.
- Gain : `1.145342`.
- Règles locales retenues : `12`.

| # | Clause numérique | Poids | z au moment de la sélection | Modalité |
|---:|---|---:|---:|---|
| 1 | `any_voice_adjacent_step_gt(all_voices)=2` | -1.654188 | -284.796 | évitement |
| 2 | `any_pair_central_abs_class(all_voices)=1` | -1.699181 | -109.500 | évitement |
| 3 | `any_pair_central_abs_class(all_voices)=11` | -1.864991 | -102.821 | évitement |
| 4 | `any_pair_central_abs_class(all_voices)=2` | -1.427930 | -102.273 | évitement |
| 5 | `any_pair_central_abs_class(all_voices)=10` | -1.276725 | -94.666 | évitement |
| 6 | `any_adjacent_central_ordered_gap_le(all_voices)=1` | -1.426639 | -80.532 | évitement |
| 7 | `any_voice_adjacent_step_gt(all_voices)=7` | -1.301362 | -61.046 | évitement |
| 8 | `any_pair_central_abs_class(all_voices)=7` | +0.725760 | +58.468 | préférence |
| 9 | `any_pair_abs_class_preserved_same_sign(all_voices)=0` | -2.091950 | -56.367 | évitement |
| 10 | `any_pair_abs_class_preserved_same_sign(all_voices)=7` | -2.069681 | -54.846 | évitement |
| 11 | `previous_ordered_gap_le(v0,v1)=2` | +1.285055 | +51.872 | préférence |
| 12 | `any_voice_adjacent_abs_class(all_voices)=1` | +0.565046 | +46.763 | préférence |

## Benchmark externe après gel

- `melodic_class_6` : `non retrouvé`
- `preserved_pair_class_0` : `retrouvé`
- `preserved_pair_class_7` : `retrouvé`
- `arrival_pair_class_0` : `non retrouvé`
- `arrival_pair_class_7` : `non retrouvé`
- `previous_or_central_order_boundary` : `non retrouvé`

Ce benchmark ne change ni les colonnes ni les poids. Les absences sont
des résultats négatifs du premier budget, pas des motifs d'ajustement
manuel.
