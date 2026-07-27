# V5.6 — réinduction K3 avec contexte tonal et vertical

## Ajouts

- Tonique et mode globaux déclarés dans le MusicXML.
- Distribution catégorielle apprise des classes relatives par mode.
- Répétition attaquée distincte d'une tenue.
- Nombre de classes distinctes, éventuellement conditionné par la métrique.
- Fingerprints verticaux mécaniquement énumérés relativement à la tonique
  ou à la basse.
- Aucune règle historique ni étiquette d'accord chargée.
- Test fermé non chargé.

## Baselines

- NLL validation registre absolu : `2.594465`.
- NLL validation registre + tonalité : `2.440822`.
- Gain tonal seul : `0.153644`.

## Modèle réinduit

- Catalogue total : `950` prédicats.
- Règles retenues : `18`.
- NLL validation finale : `1.150282`.
- Gain total : `1.444184`.

| # | Lecture numérique | Poids | z de sélection |
|---:|---|---:|---:|
| 1 | any_voice_adjacent_step_gt(all_voices)=2 | -1.323172 | -283.953 |
| 2 | ensemble vertical relatif à la basse [0, 4, 7] | +1.765359 | +197.553 |
| 3 | ensemble vertical relatif à la basse [0, 3, 7] | +1.307605 | +110.814 |
| 4 | any_voice_adjacent_abs_class(all_voices)=1 | +1.485769 | +108.318 |
| 5 | ensemble vertical relatif à la basse [0, 3, 8] | +1.305780 | +102.129 |
| 6 | any_voice_adjacent_abs_class(all_voices)=2 | +0.914414 | +79.017 |
| 7 | any_adjacent_central_ordered_gap_le(all_voices)=2 | -1.201376 | -68.941 |
| 8 | ensemble vertical relatif à la basse [0, 3, 6, 8] | +1.718224 | +60.175 |
| 9 | any_pair_central_abs_class(all_voices)=11 | -1.617219 | -55.279 |
| 10 | any_pair_central_abs_class(all_voices)=10 | -1.185017 | -54.231 |
| 11 | any_pair_abs_class_preserved_same_sign(all_voices)=0 | -1.983192 | -56.197 |
| 12 | any_pair_abs_class_preserved_same_sign(all_voices)=7 | -1.961924 | -54.344 |
| 13 | any_pair_central_abs_class(all_voices)=1 | -1.355458 | -50.013 |
| 14 | any_voice_adjacent_step_gt(all_voices)=7 | -1.202834 | -47.726 |
| 15 | any_pair_arrival_abs_class_same_sign(all_voices)=2 | -1.467429 | -46.277 |
| 16 | bloc central avec 2 classes distinctes | -1.423058 | -45.435 |
| 17 | bloc central avec 3 classes distinctes au niveau métrique 0 | -1.178244 | -44.258 |
| 18 | previous_ordered_gap_le(v0,v1)=2 | +1.288550 | +42.330 |

Les fingerprints restent des ensembles numériques. Les noms d'accords
ne seront attribués qu'après gel et comparaison musicologique.
