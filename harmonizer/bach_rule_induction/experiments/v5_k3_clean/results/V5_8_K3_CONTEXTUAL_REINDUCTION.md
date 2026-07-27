# V5_8-K3-CONTEXTUAL-REINDUCTION — réinduction contextuelle K3

## Ajouts

- Tonique et mode globaux déclarés dans le MusicXML.
- Distribution catégorielle apprise des classes relatives par voix et mode.
- Répétition attaquée distincte d'une tenue.
- Statuts chromatiques appris : rareté marginale, approche, résolution, passage, broderie et niveau métrique.
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

- Catalogue total : `1026` prédicats.
- Règles retenues : `28`.
- NLL validation finale : `1.060328`.
- Gain total : `1.534138`.

| # | Lecture numérique | Poids | z de sélection |
|---:|---|---:|---:|
| 1 | any_voice_adjacent_step_gt(all_voices)=2 | -1.255190 | -282.435 |
| 2 | ensemble vertical relatif à la basse [0, 4, 7] | +1.777065 | +195.567 |
| 3 | ensemble vertical relatif à la basse [0, 3, 7] | +1.290652 | +111.001 |
| 4 | ensemble vertical relatif à la basse [0, 3, 8] | +1.166267 | +108.762 |
| 5 | any_voice_adjacent_abs_class(all_voices)=1 | +1.349922 | +104.096 |
| 6 | any_voice_adjacent_abs_class(all_voices)=2 | +0.797934 | +79.485 |
| 7 | any_adjacent_central_ordered_gap_le(all_voices)=2 | -1.015438 | -68.736 |
| 8 | ensemble vertical relatif à la basse [0, 3, 6, 8] | +1.810147 | +60.887 |
| 9 | any_pair_central_abs_class(all_voices)=11 | -1.627243 | -56.367 |
| 10 | any_pair_abs_class_preserved_same_sign(all_voices)=7 | -1.948238 | -54.828 |
| 11 | any_pair_central_abs_class(all_voices)=10 | -1.371472 | -52.664 |
| 12 | any_pair_abs_class_preserved_same_sign(all_voices)=0 | -2.029179 | -55.750 |
| 13 | any_pair_central_abs_class(all_voices)=1 | -1.446116 | -49.020 |
| 14 | any_voice_adjacent_step_gt(all_voices)=7 | -1.160194 | -47.803 |
| 15 | any_pair_arrival_abs_class_same_sign(all_voices)=2 | -1.200072 | -46.670 |
| 16 | bloc central avec 2 classes distinctes | -1.436130 | -45.237 |
| 17 | bloc central avec 3 classes distinctes au niveau métrique 0 | -1.189084 | -43.996 |
| 18 | previous_ordered_gap_le(v0,v1)=2 | +1.319618 | +41.714 |
| 19 | attaque répétant exactement la hauteur précédente (Bass) | -1.542546 | -41.235 |
| 20 | any_pair_central_abs_class(all_voices)=2 | -0.933406 | -37.714 |
| 21 | ensemble vertical relatif à la basse [0, 2, 3, 7] | +2.221808 | +42.927 |
| 22 | ensemble vertical relatif à la basse [0, 5, 7] | +1.276427 | +39.206 |
| 23 | three_block_sign_shape(v1)=0,-1 | +1.663681 | +32.358 |
| 24 | ensemble vertical relatif à la basse [0, 3, 7, 9] | +1.648903 | +30.958 |
| 25 | any_voice_three_block_sign_shape(all_voices)=-1,-1 | +0.951201 | +30.128 |
| 26 | any_pair_abs_class_preserved_same_sign(all_voices)=3 | +0.884179 | +30.524 |
| 27 | ensemble vertical relatif à la basse [0, 4, 10] | +1.763438 | +27.604 |
| 28 | ensemble vertical relatif à la basse [0, 4, 7, 10] | +1.201683 | +29.458 |

Les fingerprints restent des ensembles numériques. Les noms d'accords
ne seront attribués qu'après gel et comparaison musicologique.
