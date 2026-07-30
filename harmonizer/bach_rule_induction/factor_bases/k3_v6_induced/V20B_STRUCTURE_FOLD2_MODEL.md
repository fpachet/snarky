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
| 0 | 0 | 2.466308 | 0.051999 |
| 1 | 1 | 1.748677 | 0.049466 |
| 2 | 3 | 1.513456 | 0.052086 |
| 3 | 4 | 1.322707 | 0.034006 |
| 4 | 6 | 1.175038 | 0.028460 |
| 5 | 7 | 1.105776 | 0.030022 |
| 6 | 8 | 1.054020 | 0.033835 |
| 7 | 12 | 1.025822 | 0.037247 |
| 8 | 13 | 0.984278 | 0.036160 |
| 9 | 17 | 0.925567 | 0.035194 |
| 10 | 18 | 0.870366 | 0.035150 |
| 11 | 22 | 0.827148 | 0.037229 |
| 12 | 23 | 0.810565 | 0.038088 |
| 13 | 24 | 0.803408 | 0.039137 |
| 14 | 25 | 0.794091 | 0.038999 |
| 15 | 26 | 0.789137 | 0.036381 |
| 16 | 28 | 0.784873 | 0.036800 |
| 17 | 30 | 0.778926 | 0.037195 |
| 18 | 31 | 0.777617 | 0.036849 |
| 19 | 33 | 0.769021 | 0.037688 |
| 20 | 37 | 0.751485 | 0.036937 |
| 21 | 38 | 0.741208 | 0.035402 |
| 22 | 39 | 0.740613 | 0.035977 |
| 23 | 40 | 0.736459 | 0.037111 |
| 24 | 41 | 0.733204 | 0.038254 |
| 25 | 42 | 0.732760 | 0.037371 |
| 26 | 43 | 0.722490 | 0.034935 | **← retenu**
| 27 | 45 | 0.703917 | 0.036587 |
| 28 | 46 | 0.702859 | 0.035573 |
| 29 | 48 | 0.700707 | 0.036837 |
| 30 | 49 | 0.690561 | 0.036922 |

## Base retenue

- Règles : `26`.
- Complexité totale : `43`.
- NLL validation par pièce : `0.722490`.
- Seuil d'une erreur standard : `0.727483`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.154794 | avoidance |
| 2 | bloc central : triade majeure à l’état fondamental | +2.409611 | preference |
| 3 | bloc central : accord complet au premier renversement | +1.073106 | preference |
| 4 | bloc central : triade mineure à l’état fondamental | +1.755342 | preference |
| 5 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.593720 | avoidance |
| 6 | bloc central : septième de dominante complète | +1.045337 | preference |
| 7 | any_pair_central_abs_class_target_passing(all_voices)=9 | +0.713571 | preference |
| 8 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.925601 | avoidance |
| 9 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -1.913156 | avoidance |
| 10 | basse : répète par une nouvelle attaque la note précédente | -1.487832 | avoidance |
| 11 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -1.835039 | avoidance |
| 12 | basse avec ténor : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.709797 | preference |
| 13 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -1.237286 | avoidance |
| 14 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -1.087473 | avoidance |
| 15 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.457847 | preference |
| 16 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -1.208046 | avoidance |
| 17 | any_pair_central_abs_class_metric(all_voices)=7,1 | +0.377610 | preference |
| 18 | ténor : mouvement vers la note suivante supérieur à 1 demi-tons | +0.712679 | preference |
| 19 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 10 | -0.764611 | avoidance |
| 20 | any_pair_central_abs_class_target_passing(all_voices)=10 | +1.285287 | preference |
| 21 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | -0.964621 | avoidance |
| 22 | bloc central : septième majeure complète | +0.995017 | preference |
| 23 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.490406 | avoidance |
| 24 | soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | +1.235633 | preference |
| 25 | soprano avec alto : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | +1.402206 | preference |
| 26 | basse avec alto : intervalle vertical de classe 6 (triton) | -1.163281 | avoidance |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
