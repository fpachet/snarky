# V5.7-K3-CONTEXTUAL-REINDUCTION — réinduction contextuelle K3

## Ajouts

- Tonique et mode globaux déclarés dans le MusicXML.
- Distribution catégorielle apprise des classes relatives par voix et mode.
- Répétition attaquée distincte d'une tenue.
- Nombre de classes distinctes, éventuellement conditionné par la métrique.
- Fingerprints verticaux mécaniquement énumérés relativement à la tonique
  ou à la basse.
- Aucune règle historique ni étiquette d'accord chargée.
- Test fermé non chargé.

## Baselines

- NLL validation registre absolu : `2.594465`.
- NLL validation registre + tonalité : `2.422315`.
- Gain tonal seul : `0.172151`.

## Modèle réinduit

- Catalogue total : `954` prédicats.
- Règles retenues : `20`.
- NLL validation finale : `1.120257`.
- Gain total : `1.474209`.

| # | Lecture numérique | Poids | z de sélection |
|---:|---|---:|---:|
| 1 | any_voice_adjacent_step_gt(all_voices)=2 | -1.360779 | -282.435 |
| 2 | ensemble vertical relatif à la basse [0, 4, 7] | +1.688977 | +195.567 |
| 3 | ensemble vertical relatif à la basse [0, 3, 7] | +1.178894 | +111.001 |
| 4 | ensemble vertical relatif à la basse [0, 3, 8] | +1.189255 | +108.762 |
| 5 | any_voice_adjacent_abs_class(all_voices)=1 | +1.426859 | +104.096 |
| 6 | any_voice_adjacent_abs_class(all_voices)=2 | +0.892116 | +79.485 |
| 7 | any_adjacent_central_ordered_gap_le(all_voices)=2 | -1.017883 | -68.736 |
| 8 | ensemble vertical relatif à la basse [0, 3, 6, 8] | +1.816219 | +60.887 |
| 9 | any_pair_central_abs_class(all_voices)=11 | -1.653188 | -56.367 |
| 10 | any_pair_abs_class_preserved_same_sign(all_voices)=7 | -1.963852 | -54.828 |
| 11 | any_pair_central_abs_class(all_voices)=10 | -1.222029 | -52.664 |
| 12 | any_pair_abs_class_preserved_same_sign(all_voices)=0 | -2.009454 | -55.750 |
| 13 | any_pair_central_abs_class(all_voices)=1 | -1.450865 | -49.020 |
| 14 | any_voice_adjacent_step_gt(all_voices)=7 | -1.236929 | -47.803 |
| 15 | any_pair_arrival_abs_class_same_sign(all_voices)=2 | -1.217050 | -46.670 |
| 16 | bloc central avec 2 classes distinctes | -1.516893 | -45.237 |
| 17 | bloc central avec 3 classes distinctes au niveau métrique 0 | -1.289445 | -43.996 |
| 18 | previous_ordered_gap_le(v0,v1)=2 | +1.373419 | +41.714 |
| 19 | attaque répétant exactement la hauteur précédente (Bass) | -1.588788 | -41.235 |
| 20 | any_pair_central_abs_class(all_voices)=2 | -0.838788 | -37.714 |

Les fingerprints restent des ensembles numériques. Les noms d'accords
ne seront attribués qu'après gel et comparaison musicologique.
