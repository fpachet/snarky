# V18 — MaxEnt parcimonieux à règles lisibles

V18 conserve la pseudo-vraisemblance exacte. Chaque colonne est un
prédicat K3 autonome et lisible ; les poids sont réestimés conjointement
après chaque ajout. Aucune statistique de génération n'intervient.

## Protocole

- Catalogue exact initial : `954`.
- Candidats lisibles : `816`.
- Famille exclue : `observed_vertical_set` (bitsets verticaux opaques).
- Pièces structure train/validation : `24/8`.
- Test réservé chargé : `false`.
- Sélection finale : règle d'une erreur standard.

## Frontière qualité–complexité

| Règles | Complexité | NLL validation par pièce | Erreur standard |
|---:|---:|---:|---:|
| 0 | 0 | 2.491689 | 0.041237 |
| 1 | 1 | 1.825555 | 0.070614 |
| 2 | 2 | 1.722652 | 0.072312 |
| 3 | 3 | 1.567152 | 0.061522 |
| 4 | 4 | 1.507029 | 0.064452 |
| 5 | 8 | 1.433983 | 0.061228 |
| 6 | 9 | 1.369861 | 0.061933 |
| 7 | 10 | 1.295667 | 0.053799 |
| 8 | 11 | 1.266659 | 0.057575 |
| 9 | 12 | 1.233183 | 0.058721 |
| 10 | 16 | 1.192648 | 0.060956 |
| 11 | 17 | 1.137126 | 0.056250 |
| 12 | 18 | 1.112342 | 0.054469 |
| 13 | 19 | 1.087542 | 0.050823 |
| 14 | 20 | 1.052221 | 0.050637 |
| 15 | 24 | 1.037434 | 0.051642 |
| 16 | 25 | 1.033504 | 0.050578 |
| 17 | 26 | 1.021736 | 0.050201 |
| 18 | 27 | 1.017900 | 0.050716 |
| 19 | 28 | 1.005605 | 0.047579 |
| 20 | 29 | 1.000412 | 0.048677 |
| 21 | 31 | 0.979473 | 0.048986 |
| 22 | 32 | 0.972777 | 0.048303 |
| 23 | 33 | 0.962749 | 0.047884 |
| 24 | 35 | 0.945200 | 0.046732 | **← retenu**
| 25 | 36 | 0.941696 | 0.045847 |
| 26 | 37 | 0.932873 | 0.044498 |
| 27 | 39 | 0.927146 | 0.045950 |
| 28 | 41 | 0.916868 | 0.046251 |
| 29 | 42 | 0.914689 | 0.047912 |
| 30 | 44 | 0.907937 | 0.048061 |

## Base retenue

- Règles : `24`.
- Complexité totale : `35`.
- NLL validation par pièce : `0.945200`.
- Seuil d'une erreur standard : `0.955998`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.314459 | avoidance |
| 2 | bloc central : 3 classes de hauteur distinctes | +0.711488 | preference |
| 3 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.688483 | avoidance |
| 4 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -1.812153 | avoidance |
| 5 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -2.110789 | avoidance |
| 6 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.771617 | avoidance |
| 7 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -1.568047 | avoidance |
| 8 | basse : répète par une nouvelle attaque la note précédente | -1.860310 | avoidance |
| 9 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.937785 | avoidance |
| 10 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -2.289234 | avoidance |
| 11 | au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | +0.503113 | preference |
| 12 | ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | -1.315422 | avoidance |
| 13 | au moins une paire de voix : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | -0.428403 | avoidance |
| 14 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.383981 | preference |
| 15 | au moins une paire de voix : conserve l’intervalle de classe 3 par mouvement direct non nul | +0.454526 | preference |
| 16 | alto avec basse : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | +1.014556 | preference |
| 17 | basse avec ténor : intervalle vertical de classe 9 (sixte majeure modulo l’octave) | -1.212529 | avoidance |
| 18 | soprano avec basse : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | +1.134938 | preference |
| 19 | ténor : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | -0.731260 | avoidance |
| 20 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | -0.875528 | avoidance |
| 21 | bloc central : 4 classes distinctes au niveau métrique 0 | +1.084115 | preference |
| 22 | basse avec alto : intervalle vertical de classe 6 (triton) | -1.274450 | avoidance |
| 23 | soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | +1.276964 | preference |
| 24 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.861670 | avoidance |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
