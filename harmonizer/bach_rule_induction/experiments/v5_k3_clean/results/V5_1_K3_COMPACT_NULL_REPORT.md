# V5-K3-CLEAN — premier cycle d'induction

## Protocole

- Base musicale initiale vide.
- Une note masquée et trois blocs verticaux consécutifs.
- Domaine commun de hauteurs dérivé du seul train.
- Aucun manifeste ni fichier de règles V1–V4 chargé.
- Sélection des colonnes sur le gradient résiduel du train.
- Les noms musicologiques ne sont appliqués qu'après sélection.
- Contrôle nul : choix permutés au sein de chaque pièce et voix.

## Corpus

- Train : `251` chorals, `68263` décisions.
- Validation : `50` chorals, `13202` décisions.
- Ancien test : `51` chorals non chargés.
- Domaine commun train : MIDI `36` à `81`.
- Choix validation hors domaine : `0`.

## Modèle

- NLL validation registre seul : `2.594465`.
- Meilleure NLL validation : `2.488226`.
- Gain : `0.106239`.
- Règles locales retenues : `12`.

| # | Clause numérique | Poids | z au moment de la sélection | Modalité |
|---:|---|---:|---:|---|
| 1 | `any_voice_adjacent_abs_class(all_voices)=0` | +0.327662 | +56.450 | préférence |
| 2 | `any_pair_central_abs_class(all_voices)=0` | +0.232347 | +50.517 | préférence |
| 3 | `any_pair_central_abs_class(all_voices)=6` | -0.434084 | -41.410 | évitement |
| 4 | `any_voice_adjacent_step_gt(all_voices)=7` | -0.300793 | -34.902 | évitement |
| 5 | `any_voice_adjacent_abs_class(all_voices)=6` | -0.506193 | -35.109 | évitement |
| 6 | `any_voice_three_block_sign_shape(all_voices)=0,0` | +0.405956 | +29.956 | préférence |
| 7 | `any_pair_central_abs_class(all_voices)=1` | -0.353645 | -25.463 | évitement |
| 8 | `any_pair_central_abs_class(all_voices)=11` | -0.259455 | -19.248 | évitement |
| 9 | `any_pair_central_abs_class(all_voices)=7` | +0.225854 | +15.459 | préférence |
| 10 | `any_pair_central_abs_class(all_voices)=5` | +0.201859 | +18.547 | préférence |
| 11 | `any_voice_adjacent_step_gt(all_voices)=12` | -0.596924 | -14.594 | évitement |
| 12 | `abs_step_from_previous_gt(v0)=7` | -0.444921 | -10.975 | évitement |

## Benchmark externe après gel

- `melodic_class_6` : `retrouvé`
- `preserved_pair_class_0` : `non retrouvé`
- `preserved_pair_class_7` : `non retrouvé`
- `arrival_pair_class_0` : `non retrouvé`
- `arrival_pair_class_7` : `non retrouvé`
- `previous_or_central_order_boundary` : `non retrouvé`

Ce benchmark ne change ni les colonnes ni les poids. Les absences sont
des résultats négatifs du premier budget, pas des motifs d'ajustement
manuel.
