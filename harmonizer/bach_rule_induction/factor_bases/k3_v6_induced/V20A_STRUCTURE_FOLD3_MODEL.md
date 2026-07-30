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
| 0 | 0 | 2.421588 | 0.077398 |
| 1 | 1 | 1.789318 | 0.052260 |
| 2 | 3 | 1.585639 | 0.047308 |
| 3 | 5 | 1.477728 | 0.041005 |
| 4 | 6 | 1.295593 | 0.027129 |
| 5 | 8 | 1.269976 | 0.023489 |
| 6 | 9 | 1.212546 | 0.016869 |
| 7 | 13 | 1.177561 | 0.013893 |
| 8 | 14 | 1.135463 | 0.019252 |
| 9 | 18 | 1.093408 | 0.020325 |
| 10 | 19 | 1.052829 | 0.019269 |
| 11 | 23 | 1.018777 | 0.022183 |
| 12 | 24 | 1.008150 | 0.027046 |
| 13 | 26 | 1.003410 | 0.031825 |
| 14 | 30 | 0.983420 | 0.029218 |
| 15 | 32 | 0.972633 | 0.030961 |
| 16 | 33 | 0.957163 | 0.030713 |
| 17 | 34 | 0.949137 | 0.031718 |
| 18 | 36 | 0.938340 | 0.030443 |
| 19 | 37 | 0.918639 | 0.029791 |
| 20 | 38 | 0.906744 | 0.028868 |
| 21 | 40 | 0.887554 | 0.027589 |
| 22 | 41 | 0.880753 | 0.025368 |
| 23 | 43 | 0.872716 | 0.025107 |
| 24 | 44 | 0.865547 | 0.024348 |
| 25 | 45 | 0.857204 | 0.023280 |
| 26 | 46 | 0.852122 | 0.025609 |
| 27 | 48 | 0.844516 | 0.024291 | **← retenu**
| 28 | 49 | 0.844516 | 0.024291 |
| 29 | 50 | 0.840271 | 0.025076 |
| 30 | 51 | 0.827121 | 0.023014 |

## Base retenue

- Règles : `27`.
- Complexité totale : `48`.
- NLL validation par pièce : `0.844516`.
- Seuil d'une erreur standard : `0.850135`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.319097 | avoidance |
| 2 | bloc central : triade majeure à l’état fondamental | +2.872388 | preference |
| 3 | bloc central : triade mineure à l’état fondamental | +2.133799 | preference |
| 4 | bloc central : accord complet au premier renversement | +1.365692 | preference |
| 5 | bloc central : septième de dominante complète sur temps faible | +1.458877 | preference |
| 6 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.454352 | avoidance |
| 7 | any_pair_central_abs_class_target_passing(all_voices)=9 | +0.699512 | preference |
| 8 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.766389 | avoidance |
| 9 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -1.936749 | avoidance |
| 10 | basse : répète par une nouvelle attaque la note précédente | -1.694787 | avoidance |
| 11 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -2.109231 | avoidance |
| 12 | au moins une paire de voix : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.302128 | preference |
| 13 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 3 | +0.251888 | preference |
| 14 | any_pair_central_abs_class_target_passing(all_voices)=10 | +1.076343 | preference |
| 15 | any_pair_central_abs_class_metric(all_voices)=7,1 | +0.457128 | preference |
| 16 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | -0.766641 | avoidance |
| 17 | ténor : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | -0.862809 | avoidance |
| 18 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 10 | -0.956786 | avoidance |
| 19 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -0.896983 | avoidance |
| 20 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -0.864864 | avoidance |
| 21 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.902329 | avoidance |
| 22 | alto : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | -0.982392 | avoidance |
| 23 | alto : directions successives (+0, -1) | +1.074562 | preference |
| 24 | bloc central : septième majeure complète | +1.126040 | preference |
| 25 | soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | +1.194264 | preference |
| 26 | toutes voix : mouvement mélodique supérieur à 12 demi-tons | -1.254436 | avoidance |
| 27 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 7 | -0.277294 | avoidance |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
