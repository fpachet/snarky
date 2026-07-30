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
| 0 | 0 | 2.491689 | 0.041237 |
| 1 | 1 | 1.825555 | 0.070614 |
| 2 | 3 | 1.685872 | 0.072967 |
| 3 | 5 | 1.471003 | 0.070460 |
| 4 | 6 | 1.395453 | 0.063232 |
| 5 | 10 | 1.336525 | 0.062730 |
| 6 | 11 | 1.306195 | 0.065274 |
| 7 | 12 | 1.270945 | 0.063973 |
| 8 | 16 | 1.223189 | 0.065825 |
| 9 | 17 | 1.186129 | 0.065453 |
| 10 | 18 | 1.143137 | 0.057213 |
| 11 | 19 | 1.121225 | 0.053744 |
| 12 | 20 | 1.096493 | 0.052792 |
| 13 | 21 | 1.059556 | 0.052703 |
| 14 | 25 | 1.041861 | 0.052507 |
| 15 | 26 | 1.029480 | 0.051778 |
| 16 | 30 | 0.990006 | 0.052859 |
| 17 | 31 | 0.976462 | 0.054480 |
| 18 | 32 | 0.974798 | 0.053329 |
| 19 | 34 | 0.958907 | 0.054064 |
| 20 | 35 | 0.955895 | 0.054260 |
| 21 | 36 | 0.948715 | 0.055510 |
| 22 | 40 | 0.939847 | 0.054935 |
| 23 | 42 | 0.920697 | 0.051676 |
| 24 | 43 | 0.902633 | 0.049229 | **← retenu**
| 25 | 44 | 0.894404 | 0.048009 |
| 26 | 45 | 0.885791 | 0.046991 |
| 27 | 46 | 0.881062 | 0.047667 |
| 28 | 47 | 0.877845 | 0.048499 |
| 29 | 48 | 0.874697 | 0.049293 |
| 30 | 49 | 0.870893 | 0.048510 |

## Base retenue

- Règles : `24`.
- Complexité totale : `43`.
- NLL validation par pièce : `0.902633`.
- Seuil d'une erreur standard : `0.919403`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.089717 | avoidance |
| 2 | bloc central : triade majeure ou mineure complète sur temps fort | +1.387476 | preference |
| 3 | bloc central : triade majeure ou mineure complète sur temps faible | +0.805178 | preference |
| 4 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.627796 | avoidance |
| 5 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -1.970859 | avoidance |
| 6 | basse : répète par une nouvelle attaque la note précédente | -1.649617 | avoidance |
| 7 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.960170 | avoidance |
| 8 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -2.232870 | avoidance |
| 9 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -1.372855 | avoidance |
| 10 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -1.227194 | avoidance |
| 11 | ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | -1.168335 | avoidance |
| 12 | au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | +0.471623 | preference |
| 13 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.421177 | preference |
| 14 | au moins une paire de voix : conserve l’intervalle de classe 3 par mouvement direct non nul | +0.494391 | preference |
| 15 | basse avec ténor : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.341555 | preference |
| 16 | any_pair_central_abs_class_target_passing(all_voices)=9 | +0.793055 | preference |
| 17 | basse avec ténor : intervalle vertical de classe 9 (sixte majeure modulo l’octave) | -1.279819 | avoidance |
| 18 | alto avec basse : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | +0.883408 | preference |
| 19 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 10 | -0.678769 | avoidance |
| 20 | soprano avec basse : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | +1.139535 | preference |
| 21 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | -0.899343 | avoidance |
| 22 | any_pair_central_abs_class_target_passing(all_voices)=10 | +1.369862 | preference |
| 23 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.867271 | avoidance |
| 24 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.606949 | avoidance |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
