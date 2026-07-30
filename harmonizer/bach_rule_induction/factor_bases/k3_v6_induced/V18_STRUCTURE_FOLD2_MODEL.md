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
| 0 | 0 | 2.466308 | 0.051999 |
| 1 | 1 | 1.748677 | 0.049466 |
| 2 | 2 | 1.665511 | 0.045682 |
| 3 | 3 | 1.520307 | 0.040503 |
| 4 | 4 | 1.454307 | 0.041918 |
| 5 | 8 | 1.368208 | 0.041569 |
| 6 | 9 | 1.305262 | 0.040322 |
| 7 | 10 | 1.238215 | 0.043440 |
| 8 | 11 | 1.184496 | 0.046733 |
| 9 | 12 | 1.134211 | 0.043919 |
| 10 | 16 | 1.064957 | 0.045180 |
| 11 | 17 | 1.007128 | 0.039660 |
| 12 | 18 | 0.996524 | 0.036437 |
| 13 | 19 | 0.950111 | 0.039183 |
| 14 | 20 | 0.926979 | 0.040569 |
| 15 | 22 | 0.922981 | 0.037798 |
| 16 | 23 | 0.908078 | 0.036939 |
| 17 | 25 | 0.906990 | 0.037361 |
| 18 | 26 | 0.902411 | 0.039751 |
| 19 | 27 | 0.879154 | 0.038812 |
| 20 | 28 | 0.867675 | 0.038476 |
| 21 | 29 | 0.855744 | 0.035645 |
| 22 | 30 | 0.851037 | 0.034655 |
| 23 | 31 | 0.851037 | 0.034655 |
| 24 | 33 | 0.834874 | 0.035462 | **← retenu**
| 25 | 35 | 0.830463 | 0.033705 |
| 26 | 37 | 0.827211 | 0.034302 |
| 27 | 38 | 0.825743 | 0.033993 |
| 28 | 39 | 0.819084 | 0.034768 |
| 29 | 40 | 0.811089 | 0.035783 |
| 30 | 41 | 0.799706 | 0.035215 |

## Base retenue

- Règles : `24`.
- Complexité totale : `33`.
- NLL validation par pièce : `0.834874`.
- Seuil d'une erreur standard : `0.834921`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.263281 | avoidance |
| 2 | bloc central : 3 classes de hauteur distinctes | +0.797312 | preference |
| 3 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.598477 | avoidance |
| 4 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -1.693182 | avoidance |
| 5 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -1.991300 | avoidance |
| 6 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.779033 | avoidance |
| 7 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -1.633263 | avoidance |
| 8 | basse : répète par une nouvelle attaque la note précédente | -1.522479 | avoidance |
| 9 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.863597 | avoidance |
| 10 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -2.031904 | avoidance |
| 11 | au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | +0.553131 | preference |
| 12 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.495442 | preference |
| 13 | au moins une paire de voix : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | -0.246489 | avoidance |
| 14 | ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | -1.083313 | avoidance |
| 15 | toutes voix : directions successives (-1, -1) | +0.530943 | preference |
| 16 | basse avec ténor : intervalle vertical de classe 9 (sixte majeure modulo l’octave) | -1.160070 | avoidance |
| 17 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -1.094442 | avoidance |
| 18 | alto avec basse : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | +1.000820 | preference |
| 19 | au moins une paire de voix : intervalle vertical de classe 3 (tierce mineure modulo l’octave) | +0.352268 | preference |
| 20 | soprano avec basse : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | +1.219334 | preference |
| 21 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | -1.031951 | avoidance |
| 22 | ténor : mouvement vers la note suivante supérieur à 1 demi-tons | +0.644123 | preference |
| 23 | soprano avec alto : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | +1.352017 | preference |
| 24 | bloc central : 4 classes distinctes au niveau métrique 0 | +1.027135 | preference |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
