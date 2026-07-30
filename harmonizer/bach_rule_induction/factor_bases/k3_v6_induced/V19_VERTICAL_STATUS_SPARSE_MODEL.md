# V18 — MaxEnt parcimonieux à règles lisibles

V18 conserve la pseudo-vraisemblance exacte. Chaque colonne est un
prédicat K3 autonome et lisible ; les poids sont réestimés conjointement
après chaque ajout. Aucune statistique de génération n'intervient.

## Protocole

- Catalogue exact initial : `1052`.
- Candidats lisibles : `914`.
- Famille exclue : `observed_vertical_set` (bitsets verticaux opaques).
- Pièces structure train/validation : `32/10`.
- Test réservé chargé : `false`.
- Sélection finale : règle d'une erreur standard.

## Frontière qualité–complexité

| Règles | Complexité | NLL validation par pièce | Erreur standard |
|---:|---:|---:|---:|
| 0 | 0 | 2.304205 | 0.067142 |
| 1 | 1 | 1.599701 | 0.062432 |
| 2 | 3 | 1.456632 | 0.076699 |
| 3 | 5 | 1.322082 | 0.081914 |
| 4 | 6 | 1.273964 | 0.078379 |
| 5 | 10 | 1.237836 | 0.082691 |
| 6 | 14 | 1.181823 | 0.086243 |
| 7 | 15 | 1.152182 | 0.085777 |
| 8 | 16 | 1.100384 | 0.089973 |
| 9 | 20 | 1.036196 | 0.094493 |
| 10 | 21 | 1.012149 | 0.092616 |
| 11 | 22 | 0.983678 | 0.090566 |
| 12 | 23 | 0.964510 | 0.095091 |
| 13 | 24 | 0.952019 | 0.093245 |
| 14 | 25 | 0.922739 | 0.093230 |
| 15 | 29 | 0.911958 | 0.095593 |
| 16 | 30 | 0.896373 | 0.095780 |
| 17 | 32 | 0.894925 | 0.093103 |
| 18 | 34 | 0.885732 | 0.087674 |
| 19 | 38 | 0.873191 | 0.085294 |
| 20 | 39 | 0.849082 | 0.082574 | **← retenu**
| 21 | 40 | 0.843364 | 0.081973 |
| 22 | 41 | 0.839857 | 0.083295 |
| 23 | 42 | 0.836608 | 0.082448 |
| 24 | 43 | 0.830302 | 0.080312 |
| 25 | 44 | 0.825410 | 0.080367 |
| 26 | 45 | 0.824488 | 0.079979 |
| 27 | 46 | 0.821693 | 0.079314 |
| 28 | 47 | 0.809923 | 0.077114 |
| 29 | 49 | 0.801939 | 0.074072 |
| 30 | 50 | 0.795571 | 0.072475 |

## Base retenue

- Règles : `20`.
- Complexité totale : `39`.
- NLL validation par pièce : `0.849082`.
- Seuil d'une erreur standard : `0.868045`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.107844 | avoidance |
| 2 | bloc central : triade majeure ou mineure complète sur temps fort | +1.353245 | preference |
| 3 | bloc central : triade majeure ou mineure complète sur temps faible | +0.946284 | preference |
| 4 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.776782 | avoidance |
| 5 | any_pair_central_abs_class_target_passing(all_voices)=9 | +0.856127 | preference |
| 6 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -2.091709 | avoidance |
| 7 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -1.014541 | avoidance |
| 8 | basse : répète par une nouvelle attaque la note précédente | -1.595759 | avoidance |
| 9 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -2.124048 | avoidance |
| 10 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -1.390364 | avoidance |
| 11 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -1.272902 | avoidance |
| 12 | au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | +0.459119 | preference |
| 13 | ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | -1.274160 | avoidance |
| 14 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.419081 | preference |
| 15 | au moins une paire de voix : conserve l’intervalle de classe 3 par mouvement direct non nul | +0.414644 | preference |
| 16 | basse avec ténor : intervalle vertical de classe 9 (sixte majeure modulo l’octave) | -1.280384 | avoidance |
| 17 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 10 | -0.772840 | avoidance |
| 18 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.978165 | avoidance |
| 19 | any_pair_central_abs_class_target_passing(all_voices)=10 | +1.394352 | preference |
| 20 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.695739 | avoidance |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
