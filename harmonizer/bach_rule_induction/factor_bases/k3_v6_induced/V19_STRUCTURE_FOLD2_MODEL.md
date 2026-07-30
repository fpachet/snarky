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
| 0 | 0 | 2.466308 | 0.051999 |
| 1 | 1 | 1.748677 | 0.049466 |
| 2 | 3 | 1.577599 | 0.054730 |
| 3 | 5 | 1.371185 | 0.031541 |
| 4 | 6 | 1.306663 | 0.030054 |
| 5 | 10 | 1.269245 | 0.042166 |
| 6 | 14 | 1.205776 | 0.043200 |
| 7 | 15 | 1.158610 | 0.039815 |
| 8 | 16 | 1.105362 | 0.043882 |
| 9 | 20 | 1.035297 | 0.043763 |
| 10 | 21 | 0.999754 | 0.043179 |
| 11 | 22 | 0.967232 | 0.044322 |
| 12 | 23 | 0.939177 | 0.039651 |
| 13 | 24 | 0.926350 | 0.036364 |
| 14 | 25 | 0.910504 | 0.036150 |
| 15 | 29 | 0.868005 | 0.037279 |
| 16 | 31 | 0.867118 | 0.037317 |
| 17 | 32 | 0.853290 | 0.040343 |
| 18 | 33 | 0.847200 | 0.040947 |
| 19 | 34 | 0.830365 | 0.042358 |
| 20 | 38 | 0.803333 | 0.040746 |
| 21 | 39 | 0.802087 | 0.039273 |
| 22 | 40 | 0.795629 | 0.036656 |
| 23 | 42 | 0.790939 | 0.038281 | **← retenu**
| 24 | 43 | 0.783611 | 0.039558 |
| 25 | 45 | 0.778172 | 0.037587 |
| 26 | 46 | 0.777436 | 0.036497 |
| 27 | 50 | 0.774138 | 0.036381 |
| 28 | 51 | 0.765523 | 0.035823 |
| 29 | 52 | 0.762925 | 0.036225 |
| 30 | 53 | 0.758625 | 0.036135 |

## Base retenue

- Règles : `23`.
- Complexité totale : `42`.
- NLL validation par pièce : `0.790939`.
- Seuil d'une erreur standard : `0.794761`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.083525 | avoidance |
| 2 | bloc central : triade majeure ou mineure complète sur temps fort | +1.288231 | preference |
| 3 | bloc central : triade majeure ou mineure complète sur temps faible | +0.900831 | preference |
| 4 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.632088 | avoidance |
| 5 | any_pair_central_abs_class_target_passing(all_voices)=9 | +0.852466 | preference |
| 6 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -2.004022 | avoidance |
| 7 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.879678 | avoidance |
| 8 | basse : répète par une nouvelle attaque la note précédente | -1.529518 | avoidance |
| 9 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -1.851749 | avoidance |
| 10 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -1.330444 | avoidance |
| 11 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -1.275925 | avoidance |
| 12 | au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | +0.570325 | preference |
| 13 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.551362 | preference |
| 14 | basse avec ténor : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.464103 | preference |
| 15 | au moins une paire de voix : conserve l’intervalle de classe 3 par mouvement direct non nul | +0.358547 | preference |
| 16 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -1.095634 | avoidance |
| 17 | ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | -1.117439 | avoidance |
| 18 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.756946 | avoidance |
| 19 | basse avec ténor : intervalle vertical de classe 9 (sixte majeure modulo l’octave) | -1.145950 | avoidance |
| 20 | any_pair_central_abs_class_target_passing(all_voices)=10 | +1.239283 | preference |
| 21 | ténor : mouvement vers la note suivante supérieur à 1 demi-tons | +0.704676 | preference |
| 22 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | -0.936319 | avoidance |
| 23 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 7 | -0.302985 | avoidance |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
