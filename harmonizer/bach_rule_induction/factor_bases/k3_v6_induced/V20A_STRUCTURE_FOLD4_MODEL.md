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
| 0 | 0 | 2.292360 | 0.059553 |
| 1 | 1 | 1.750656 | 0.066672 |
| 2 | 3 | 1.524690 | 0.082001 |
| 3 | 4 | 1.407394 | 0.082109 |
| 4 | 6 | 1.298111 | 0.075090 |
| 5 | 7 | 1.257703 | 0.070494 |
| 6 | 9 | 1.207848 | 0.076164 |
| 7 | 13 | 1.181732 | 0.072781 |
| 8 | 14 | 1.119076 | 0.064833 |
| 9 | 15 | 1.093816 | 0.059081 |
| 10 | 19 | 1.033606 | 0.057703 |
| 11 | 23 | 0.995735 | 0.062013 |
| 12 | 24 | 0.981073 | 0.061576 |
| 13 | 25 | 0.961945 | 0.058428 |
| 14 | 27 | 0.955424 | 0.051783 |
| 15 | 28 | 0.942053 | 0.046388 |
| 16 | 30 | 0.934960 | 0.049330 |
| 17 | 31 | 0.930730 | 0.052280 |
| 18 | 33 | 0.919975 | 0.050918 |
| 19 | 34 | 0.915388 | 0.049058 |
| 20 | 36 | 0.897788 | 0.048248 |
| 21 | 37 | 0.887480 | 0.047276 |
| 22 | 41 | 0.879108 | 0.047207 |
| 23 | 42 | 0.858867 | 0.045520 | **← retenu**
| 24 | 43 | 0.853454 | 0.043910 |
| 25 | 45 | 0.841626 | 0.047421 |
| 26 | 46 | 0.839259 | 0.046853 |
| 27 | 47 | 0.831742 | 0.044807 |
| 28 | 48 | 0.826694 | 0.044635 |
| 29 | 49 | 0.822152 | 0.043048 |
| 30 | 50 | 0.820440 | 0.042566 |

## Base retenue

- Règles : `23`.
- Complexité totale : `42`.
- NLL validation par pièce : `0.858867`.
- Seuil d'une erreur standard : `0.863006`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.321621 | avoidance |
| 2 | bloc central : triade majeure à l’état fondamental | +2.875782 | preference |
| 3 | bloc central : accord complet au premier renversement | +1.377132 | preference |
| 4 | bloc central : triade mineure à l’état fondamental | +2.067573 | preference |
| 5 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.611235 | avoidance |
| 6 | bloc central : septième de dominante complète sur temps faible | +1.132620 | preference |
| 7 | any_pair_central_abs_class_target_passing(all_voices)=9 | +0.718087 | preference |
| 8 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.937462 | avoidance |
| 9 | basse : répète par une nouvelle attaque la note précédente | -1.917267 | avoidance |
| 10 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -1.981514 | avoidance |
| 11 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -1.912640 | avoidance |
| 12 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -0.893390 | avoidance |
| 13 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -0.793252 | avoidance |
| 14 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 3 | +0.234705 | preference |
| 15 | basse avec ténor : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.712118 | preference |
| 16 | any_pair_central_abs_class_metric(all_voices)=7,1 | +0.432833 | preference |
| 17 | ténor : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | -0.893013 | avoidance |
| 18 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 10 | -1.150439 | avoidance |
| 19 | alto : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | -0.799606 | avoidance |
| 20 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -1.002858 | avoidance |
| 21 | soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | +1.383314 | preference |
| 22 | any_pair_central_abs_class_target_passing(all_voices)=10 | +0.954855 | preference |
| 23 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | -0.931602 | avoidance |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
