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
| 0 | 0 | 2.491689 | 0.041237 |
| 1 | 1 | 1.825555 | 0.070614 |
| 2 | 3 | 1.614267 | 0.074538 |
| 3 | 4 | 1.463876 | 0.061865 |
| 4 | 6 | 1.300864 | 0.062822 |
| 5 | 7 | 1.226108 | 0.060569 |
| 6 | 8 | 1.188822 | 0.059717 |
| 7 | 9 | 1.156549 | 0.056976 |
| 8 | 10 | 1.131147 | 0.059548 |
| 9 | 14 | 1.085461 | 0.060418 |
| 10 | 18 | 1.044793 | 0.057581 |
| 11 | 22 | 1.026090 | 0.056846 |
| 12 | 23 | 1.008966 | 0.055274 |
| 13 | 25 | 0.995455 | 0.055723 |
| 14 | 29 | 0.958410 | 0.055695 |
| 15 | 30 | 0.951075 | 0.056243 |
| 16 | 31 | 0.940116 | 0.054522 |
| 17 | 33 | 0.922160 | 0.049638 |
| 18 | 34 | 0.913729 | 0.046030 |
| 19 | 35 | 0.905913 | 0.047133 |
| 20 | 36 | 0.895812 | 0.048507 |
| 21 | 37 | 0.880081 | 0.048342 |
| 22 | 39 | 0.859092 | 0.050303 | **← retenu**
| 23 | 40 | 0.852551 | 0.049349 |
| 24 | 41 | 0.844338 | 0.048241 |
| 25 | 42 | 0.838439 | 0.048693 |
| 26 | 43 | 0.835775 | 0.048048 |
| 27 | 44 | 0.830827 | 0.048021 |
| 28 | 45 | 0.822335 | 0.049489 |
| 29 | 46 | 0.815917 | 0.050454 |
| 30 | 47 | 0.811887 | 0.053251 |

## Base retenue

- Règles : `22`.
- Complexité totale : `39`.
- NLL validation par pièce : `0.859092`.
- Seuil d'une erreur standard : `0.865138`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.156370 | avoidance |
| 2 | bloc central : triade majeure à l’état fondamental | +2.902798 | preference |
| 3 | bloc central : accord complet au premier renversement | +1.367737 | preference |
| 4 | bloc central : triade mineure à l’état fondamental | +2.153124 | preference |
| 5 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.474666 | avoidance |
| 6 | bloc central : septième de dominante complète | +1.091031 | preference |
| 7 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.979805 | avoidance |
| 8 | basse : répète par une nouvelle attaque la note précédente | -1.650858 | avoidance |
| 9 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -2.080283 | avoidance |
| 10 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -1.900139 | avoidance |
| 11 | any_pair_central_abs_class_target_passing(all_voices)=10 | +1.197974 | preference |
| 12 | au moins une paire de voix : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.286176 | preference |
| 13 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 3 | +0.257013 | preference |
| 14 | any_pair_central_abs_class_target_passing(all_voices)=9 | +0.667704 | preference |
| 15 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | -0.984037 | avoidance |
| 16 | soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | +1.315274 | preference |
| 17 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.888309 | avoidance |
| 18 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -0.930280 | avoidance |
| 19 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -0.930218 | avoidance |
| 20 | bloc central : septième majeure complète | +1.260340 | preference |
| 21 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.304405 | preference |
| 22 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 10 | -0.869885 | avoidance |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
