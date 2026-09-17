# V18 — MaxEnt parcimonieux à règles lisibles

V18 conserve la pseudo-vraisemblance exacte. Chaque colonne est un
prédicat K3 autonome et lisible ; les poids sont réestimés conjointement
après chaque ajout. Aucune statistique de génération n'intervient.

## Protocole

- Catalogue exact initial : `1256`.
- Candidats lisibles : `1118`.
- Famille exclue : `observed_vertical_set` (bitsets verticaux opaques).
- Pièces structure train/validation : `24/8`.
- Test réservé chargé : `false`.
- Sélection finale : règle d'une erreur standard.

## Frontière qualité–complexité

| Règles | Complexité | NLL validation par pièce | Erreur standard |
|---:|---:|---:|---:|
| 0 | 0 | 2.421588 | 0.077398 |
| 1 | 1 | 1.789318 | 0.052260 |
| 2 | 3 | 1.585639 | 0.047308 |
| 3 | 5 | 1.477728 | 0.041005 |
| 4 | 6 | 1.295593 | 0.027129 |
| 5 | 7 | 1.268656 | 0.025507 |
| 6 | 8 | 1.207257 | 0.018218 |
| 7 | 12 | 1.175240 | 0.014455 |
| 8 | 13 | 1.134199 | 0.020871 |
| 9 | 17 | 1.093488 | 0.021538 |
| 10 | 18 | 1.053274 | 0.020351 |
| 11 | 22 | 1.019298 | 0.021950 |
| 12 | 23 | 1.007280 | 0.026472 |
| 13 | 27 | 0.988263 | 0.027752 |
| 14 | 29 | 0.979662 | 0.028900 |
| 15 | 31 | 0.968899 | 0.029043 |
| 16 | 33 | 0.957877 | 0.028488 |
| 17 | 34 | 0.949957 | 0.029883 |
| 18 | 35 | 0.935271 | 0.029286 |
| 19 | 37 | 0.918506 | 0.027614 |
| 20 | 38 | 0.905828 | 0.025047 |
| 21 | 39 | 0.897243 | 0.021922 |
| 22 | 40 | 0.896853 | 0.021967 |
| 23 | 41 | 0.881097 | 0.021463 |
| 24 | 42 | 0.875724 | 0.020737 |
| 25 | 43 | 0.864737 | 0.021441 |
| 26 | 45 | 0.858241 | 0.021880 | **← retenu**
| 27 | 46 | 0.852818 | 0.024257 |
| 28 | 47 | 0.842981 | 0.027579 |
| 29 | 49 | 0.836184 | 0.025758 |
| 30 | 50 | 0.834660 | 0.025406 |

## Base retenue

- Règles : `26`.
- Complexité totale : `45`.
- NLL validation par pièce : `0.858241`.
- Seuil d'une erreur standard : `0.860066`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.339064 | avoidance |
| 2 | bloc central : triade majeure à l’état fondamental | +2.879229 | preference |
| 3 | bloc central : triade mineure à l’état fondamental | +2.101117 | preference |
| 4 | bloc central : accord complet au premier renversement | +1.340260 | preference |
| 5 | bloc central : septième de dominante complète | +1.288989 | preference |
| 6 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.476984 | avoidance |
| 7 | any_pair_central_abs_class_target_passing(all_voices)=9 | +0.666452 | preference |
| 8 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.935406 | avoidance |
| 9 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -2.132708 | avoidance |
| 10 | basse : répète par une nouvelle attaque la note précédente | -1.687125 | avoidance |
| 11 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -2.119682 | avoidance |
| 12 | au moins une paire de voix : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.376455 | preference |
| 13 | any_pair_central_abs_class_target_passing(all_voices)=10 | +1.091046 | preference |
| 14 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 3 | +0.263025 | preference |
| 15 | any_pair_central_abs_class_metric(all_voices)=7,1 | +0.415313 | preference |
| 16 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 10 | -0.980917 | avoidance |
| 17 | ténor : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | -0.857437 | avoidance |
| 18 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | -0.914827 | avoidance |
| 19 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.934914 | avoidance |
| 20 | soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | +1.281717 | preference |
| 21 | alto : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | -0.941778 | avoidance |
| 22 | bloc central : accord complet au troisième renversement | +0.760466 | preference |
| 23 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -0.739350 | avoidance |
| 24 | basse avec alto : intervalle vertical de classe 6 (triton) | -1.305662 | avoidance |
| 25 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -0.689909 | avoidance |
| 26 | alto : directions successives (+0, -1) | +0.957354 | preference |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
