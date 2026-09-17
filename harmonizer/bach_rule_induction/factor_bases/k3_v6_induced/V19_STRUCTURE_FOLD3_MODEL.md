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
| 0 | 0 | 2.421588 | 0.077398 |
| 1 | 1 | 1.789318 | 0.052260 |
| 2 | 3 | 1.617239 | 0.057353 |
| 3 | 5 | 1.444746 | 0.048985 |
| 4 | 6 | 1.373311 | 0.032280 |
| 5 | 10 | 1.332895 | 0.039614 |
| 6 | 14 | 1.285643 | 0.042192 |
| 7 | 15 | 1.239777 | 0.040929 |
| 8 | 16 | 1.194970 | 0.039507 |
| 9 | 20 | 1.150470 | 0.039640 |
| 10 | 21 | 1.120720 | 0.042252 |
| 11 | 22 | 1.073740 | 0.039349 |
| 12 | 23 | 1.053918 | 0.037411 |
| 13 | 25 | 1.042627 | 0.040528 |
| 14 | 26 | 1.008903 | 0.032287 |
| 15 | 27 | 0.989941 | 0.030497 |
| 16 | 28 | 0.974747 | 0.032127 |
| 17 | 29 | 0.957599 | 0.035700 |
| 18 | 30 | 0.947329 | 0.034131 |
| 19 | 34 | 0.923034 | 0.032142 |
| 20 | 36 | 0.903400 | 0.031836 |
| 21 | 37 | 0.893765 | 0.034818 |
| 22 | 38 | 0.890763 | 0.035556 |
| 23 | 39 | 0.886105 | 0.039181 |
| 24 | 41 | 0.879960 | 0.038820 |
| 25 | 42 | 0.877894 | 0.037797 |
| 26 | 43 | 0.872516 | 0.036357 | **← retenu**
| 27 | 44 | 0.869514 | 0.033458 |
| 28 | 45 | 0.861874 | 0.032481 |
| 29 | 46 | 0.854749 | 0.032542 |
| 30 | 47 | 0.846466 | 0.030764 |

## Base retenue

- Règles : `26`.
- Complexité totale : `43`.
- NLL validation par pièce : `0.872516`.
- Seuil d'une erreur standard : `0.877230`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.207202 | avoidance |
| 2 | bloc central : triade majeure ou mineure complète sur temps fort | +1.268259 | preference |
| 3 | bloc central : triade majeure ou mineure complète sur temps faible | +0.839961 | preference |
| 4 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.744490 | avoidance |
| 5 | any_pair_central_abs_class_target_passing(all_voices)=9 | +0.886139 | preference |
| 6 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -2.207431 | avoidance |
| 7 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.761673 | avoidance |
| 8 | basse : répète par une nouvelle attaque la note précédente | -1.501010 | avoidance |
| 9 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -2.194538 | avoidance |
| 10 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -1.423721 | avoidance |
| 11 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -1.308332 | avoidance |
| 12 | au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | +0.511863 | preference |
| 13 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 3 | +0.334099 | preference |
| 14 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.456256 | preference |
| 15 | basse avec ténor : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.401610 | preference |
| 16 | ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | -1.083469 | avoidance |
| 17 | basse avec ténor : intervalle vertical de classe 9 (sixte majeure modulo l’octave) | -1.242396 | avoidance |
| 18 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.769658 | avoidance |
| 19 | any_pair_central_abs_class_target_passing(all_voices)=10 | +1.193496 | preference |
| 20 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.897566 | avoidance |
| 21 | toutes voix : mouvement mélodique supérieur à 12 demi-tons | -1.568106 | avoidance |
| 22 | alto avec basse : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | +0.803019 | preference |
| 23 | ténor : mouvement vers la note suivante supérieur à 1 demi-tons | +0.626501 | preference |
| 24 | alto : directions successives (+0, -1) | +0.994833 | preference |
| 25 | soprano avec alto : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | +1.384603 | preference |
| 26 | soprano avec basse : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | +1.043489 | preference |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
