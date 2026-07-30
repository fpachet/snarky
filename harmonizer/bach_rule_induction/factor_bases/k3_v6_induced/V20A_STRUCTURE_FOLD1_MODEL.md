# V18 — MaxEnt parcimonieux à règles lisibles

V18 conserve la pseudo-vraisemblance exacte. Chaque colonne est un
prédicat K3 autonome et lisible ; les poids sont réestimés conjointement
après chaque ajout. Aucune statistique de génération n'intervient.

## Protocole

- Catalogue exact initial : `1278`.
- Candidats lisibles : `1140`.
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
| 5 | 8 | 1.235372 | 0.063153 |
| 6 | 9 | 1.178186 | 0.058331 |
| 7 | 10 | 1.146201 | 0.055924 |
| 8 | 11 | 1.120500 | 0.058218 |
| 9 | 15 | 1.074770 | 0.059374 |
| 10 | 19 | 1.034079 | 0.056599 |
| 11 | 20 | 1.016617 | 0.055057 |
| 12 | 24 | 1.001888 | 0.054333 |
| 13 | 25 | 0.986033 | 0.049418 |
| 14 | 26 | 0.974402 | 0.050171 |
| 15 | 27 | 0.947213 | 0.050906 |
| 16 | 28 | 0.933203 | 0.047986 |
| 17 | 29 | 0.926666 | 0.048602 |
| 18 | 31 | 0.904603 | 0.043583 |
| 19 | 32 | 0.893580 | 0.042502 |
| 20 | 33 | 0.879395 | 0.044146 |
| 21 | 34 | 0.873193 | 0.042769 |
| 22 | 35 | 0.869622 | 0.044337 |
| 23 | 36 | 0.863431 | 0.045697 | **← retenu**
| 24 | 37 | 0.859778 | 0.044684 |
| 25 | 38 | 0.856547 | 0.043371 |
| 26 | 39 | 0.849840 | 0.043917 |
| 27 | 40 | 0.843224 | 0.042521 |
| 28 | 41 | 0.836830 | 0.042505 |
| 29 | 42 | 0.827143 | 0.042177 |
| 30 | 43 | 0.821296 | 0.043085 |

## Base retenue

- Règles : `23`.
- Complexité totale : `36`.
- NLL validation par pièce : `0.863431`.
- Seuil d'une erreur standard : `0.864380`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.377032 | avoidance |
| 2 | bloc central : triade majeure à l’état fondamental | +2.765792 | preference |
| 3 | bloc central : accord complet au premier renversement | +1.159336 | preference |
| 4 | bloc central : triade mineure à l’état fondamental | +1.952241 | preference |
| 5 | bloc central : septième de dominante complète sur temps faible | +1.378907 | preference |
| 6 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.566893 | avoidance |
| 7 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.986468 | avoidance |
| 8 | basse : répète par une nouvelle attaque la note précédente | -1.900828 | avoidance |
| 9 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -2.159569 | avoidance |
| 10 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -1.877061 | avoidance |
| 11 | basse avec ténor : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.532496 | preference |
| 12 | any_pair_central_abs_class_target_passing(all_voices)=10 | +1.379971 | preference |
| 13 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -1.048497 | avoidance |
| 14 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -1.118529 | avoidance |
| 15 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.611217 | avoidance |
| 16 | ténor : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | -0.898084 | avoidance |
| 17 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | -1.000475 | avoidance |
| 18 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.950383 | avoidance |
| 19 | soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | +1.378464 | preference |
| 20 | alto : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | -0.720535 | avoidance |
| 21 | basse avec alto : intervalle vertical de classe 6 (triton) | -1.317660 | avoidance |
| 22 | soprano avec basse : intervalle vertical de classe 3 (tierce mineure modulo l’octave) | +0.949747 | preference |
| 23 | bloc central : septième majeure complète | +1.010320 | preference |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
