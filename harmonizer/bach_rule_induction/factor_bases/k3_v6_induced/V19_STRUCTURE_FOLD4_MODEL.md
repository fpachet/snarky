# V18 — MaxEnt parcimonieux à règles lisibles

V18 conserve la pseudo-vraisemblance exacte. Chaque colonne est un
prédicat K3 autonome et lisible ; les poids sont réestimés conjointement
après chaque ajout. Aucune statistique de génération n'intervient.

## Protocole

- Catalogue exact initial : `1052`.
- Candidats lisibles : `914`.
- Famille exclue : `observed_vertical_set` (bitsets verticaux opaques).
- Pièces structure train/validation : `24/8`.
- Test réservé chargé : `false`.
- Sélection finale : règle d'une erreur standard.

## Frontière qualité–complexité

| Règles | Complexité | NLL validation par pièce | Erreur standard |
|---:|---:|---:|---:|
| 0 | 0 | 2.292360 | 0.059553 |
| 1 | 1 | 1.750656 | 0.066672 |
| 2 | 3 | 1.621729 | 0.072284 |
| 3 | 5 | 1.480576 | 0.079983 |
| 4 | 6 | 1.434168 | 0.070731 |
| 5 | 10 | 1.403827 | 0.064138 |
| 6 | 14 | 1.349953 | 0.071332 |
| 7 | 15 | 1.283207 | 0.066033 |
| 8 | 16 | 1.241667 | 0.062062 |
| 9 | 20 | 1.177850 | 0.064546 |
| 10 | 21 | 1.156894 | 0.068978 |
| 11 | 22 | 1.148633 | 0.068535 |
| 12 | 23 | 1.122885 | 0.061451 |
| 13 | 24 | 1.103216 | 0.060098 |
| 14 | 25 | 1.063623 | 0.054892 |
| 15 | 26 | 1.031843 | 0.055945 |
| 16 | 27 | 1.027002 | 0.056775 |
| 17 | 28 | 1.013556 | 0.056146 |
| 18 | 30 | 0.998620 | 0.053640 |
| 19 | 34 | 0.988357 | 0.051680 |
| 20 | 35 | 0.971963 | 0.045619 |
| 21 | 37 | 0.950546 | 0.042560 |
| 22 | 38 | 0.942895 | 0.043526 |
| 23 | 39 | 0.938748 | 0.043207 |
| 24 | 40 | 0.934163 | 0.041286 |
| 25 | 41 | 0.916313 | 0.038702 |
| 26 | 42 | 0.908312 | 0.038350 | **← retenu**
| 27 | 43 | 0.898440 | 0.039438 |
| 28 | 44 | 0.887820 | 0.039140 |
| 29 | 45 | 0.888373 | 0.039582 |
| 30 | 46 | 0.873382 | 0.036873 |

## Base retenue

- Règles : `26`.
- Complexité totale : `42`.
- NLL validation par pièce : `0.908312`.
- Seuil d'une erreur standard : `0.910255`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.152167 | avoidance |
| 2 | bloc central : triade majeure ou mineure complète sur temps fort | +1.398028 | preference |
| 3 | bloc central : triade majeure ou mineure complète sur temps faible | +0.974337 | preference |
| 4 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.693929 | avoidance |
| 5 | any_pair_central_abs_class_target_passing(all_voices)=9 | +0.952003 | preference |
| 6 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -2.064698 | avoidance |
| 7 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.917678 | avoidance |
| 8 | basse : répète par une nouvelle attaque la note précédente | -1.762671 | avoidance |
| 9 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -2.033566 | avoidance |
| 10 | au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | +0.475812 | preference |
| 11 | au moins une paire de voix : intervalle vertical de classe 3 (tierce mineure modulo l’octave) | +0.426462 | preference |
| 12 | basse avec ténor : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.481273 | preference |
| 13 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -1.328136 | avoidance |
| 14 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -1.391052 | avoidance |
| 15 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.371192 | preference |
| 16 | basse avec ténor : intervalle vertical de classe 9 (sixte majeure modulo l’octave) | -1.285794 | avoidance |
| 17 | ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | -1.031939 | avoidance |
| 18 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 10 | -0.900868 | avoidance |
| 19 | any_pair_central_abs_class_target_passing(all_voices)=10 | +1.425954 | preference |
| 20 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.663255 | avoidance |
| 21 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.966281 | avoidance |
| 22 | soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | +1.443730 | preference |
| 23 | soprano avec alto : intervalle vertical de classe 5 (quarte juste modulo l’octave) | +0.965379 | preference |
| 24 | soprano avec alto : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | +1.397408 | preference |
| 25 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | -0.850703 | avoidance |
| 26 | soprano avec basse : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | +1.131466 | preference |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
