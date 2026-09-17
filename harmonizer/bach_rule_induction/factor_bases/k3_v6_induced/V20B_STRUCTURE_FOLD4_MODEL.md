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
| 0 | 0 | 2.292360 | 0.059553 |
| 1 | 1 | 1.750656 | 0.066672 |
| 2 | 3 | 1.524690 | 0.082001 |
| 3 | 4 | 1.407394 | 0.082109 |
| 4 | 6 | 1.298111 | 0.075090 |
| 5 | 7 | 1.257703 | 0.070494 |
| 6 | 8 | 1.211790 | 0.075787 |
| 7 | 12 | 1.184404 | 0.072081 |
| 8 | 13 | 1.121047 | 0.063948 |
| 9 | 14 | 1.095886 | 0.058460 |
| 10 | 18 | 1.035633 | 0.057295 |
| 11 | 22 | 1.017447 | 0.055130 |
| 12 | 26 | 0.985871 | 0.059271 |
| 13 | 27 | 0.959253 | 0.048518 |
| 14 | 29 | 0.951111 | 0.042763 |
| 15 | 31 | 0.943192 | 0.043606 |
| 16 | 32 | 0.936353 | 0.043912 |
| 17 | 34 | 0.926234 | 0.044299 |
| 18 | 35 | 0.920105 | 0.044094 |
| 19 | 36 | 0.916251 | 0.046570 |
| 20 | 38 | 0.898753 | 0.046517 |
| 21 | 39 | 0.893300 | 0.044716 |
| 22 | 40 | 0.881315 | 0.044762 |
| 23 | 41 | 0.861142 | 0.043510 | **← retenu**
| 24 | 42 | 0.854355 | 0.041392 |
| 25 | 43 | 0.852087 | 0.040676 |
| 26 | 45 | 0.840444 | 0.044083 |
| 27 | 46 | 0.835527 | 0.042678 |
| 28 | 47 | 0.832874 | 0.043959 |
| 29 | 48 | 0.826312 | 0.044049 |
| 30 | 49 | 0.820337 | 0.044764 |

## Base retenue

- Règles : `23`.
- Complexité totale : `41`.
- NLL validation par pièce : `0.861142`.
- Seuil d'une erreur standard : `0.865101`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.331899 | avoidance |
| 2 | bloc central : triade majeure à l’état fondamental | +2.842889 | preference |
| 3 | bloc central : accord complet au premier renversement | +1.401660 | preference |
| 4 | bloc central : triade mineure à l’état fondamental | +2.047554 | preference |
| 5 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.590924 | avoidance |
| 6 | bloc central : septième de dominante complète | +1.061569 | preference |
| 7 | any_pair_central_abs_class_target_passing(all_voices)=9 | +0.714710 | preference |
| 8 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.927248 | avoidance |
| 9 | basse : répète par une nouvelle attaque la note précédente | -1.929231 | avoidance |
| 10 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -1.969186 | avoidance |
| 11 | any_pair_central_abs_class_target_passing(all_voices)=10 | +1.031320 | preference |
| 12 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -1.989969 | avoidance |
| 13 | au moins une paire de voix : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.267151 | preference |
| 14 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 3 | +0.247907 | preference |
| 15 | any_pair_central_abs_class_metric(all_voices)=7,1 | +0.444695 | preference |
| 16 | soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | +1.429209 | preference |
| 17 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 10 | -1.142478 | avoidance |
| 18 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -0.819331 | avoidance |
| 19 | ténor : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | -0.874439 | avoidance |
| 20 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.984330 | avoidance |
| 21 | alto : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | -0.807114 | avoidance |
| 22 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -0.720678 | avoidance |
| 23 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | -0.917767 | avoidance |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
