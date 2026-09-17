# V18 — MaxEnt parcimonieux à règles lisibles

V18 conserve la pseudo-vraisemblance exacte. Chaque colonne est un
prédicat K3 autonome et lisible ; les poids sont réestimés conjointement
après chaque ajout. Aucune statistique de génération n'intervient.

## Protocole

- Catalogue exact initial : `1278`.
- Candidats lisibles : `1140`.
- Famille exclue : `observed_vertical_set` (bitsets verticaux opaques).
- Pièces structure train/validation : `32/10`.
- Test réservé chargé : `false`.
- Sélection finale : règle d'une erreur standard.

## Frontière qualité–complexité

| Règles | Complexité | NLL validation par pièce | Erreur standard |
|---:|---:|---:|---:|
| 0 | 0 | 2.304205 | 0.067142 |
| 1 | 1 | 1.599701 | 0.062432 |
| 2 | 3 | 1.399567 | 0.070494 |
| 3 | 4 | 1.297838 | 0.076656 |
| 4 | 6 | 1.195071 | 0.082615 |
| 5 | 7 | 1.153194 | 0.083716 |
| 6 | 9 | 1.116613 | 0.091525 |
| 7 | 13 | 1.085588 | 0.094827 |
| 8 | 14 | 1.060956 | 0.095903 |
| 9 | 18 | 1.003020 | 0.100132 |
| 10 | 19 | 0.957500 | 0.104012 |
| 11 | 23 | 0.918577 | 0.102335 |
| 12 | 24 | 0.898283 | 0.103495 |
| 13 | 28 | 0.877560 | 0.097605 |
| 14 | 29 | 0.861964 | 0.096655 |
| 15 | 30 | 0.857325 | 0.095846 |
| 16 | 31 | 0.839365 | 0.089963 |
| 17 | 33 | 0.821653 | 0.088072 |
| 18 | 34 | 0.813679 | 0.087942 | **← retenu**
| 19 | 35 | 0.799380 | 0.087198 |
| 20 | 36 | 0.793162 | 0.086407 |
| 21 | 37 | 0.788649 | 0.086455 |
| 22 | 39 | 0.782804 | 0.088160 |
| 23 | 41 | 0.781391 | 0.087988 |
| 24 | 43 | 0.773409 | 0.085083 |
| 25 | 44 | 0.772244 | 0.085128 |
| 26 | 46 | 0.759663 | 0.084416 |
| 27 | 47 | 0.754797 | 0.085882 |
| 28 | 48 | 0.742158 | 0.083636 |
| 29 | 49 | 0.740557 | 0.083545 |
| 30 | 50 | 0.737187 | 0.081675 |

## Base retenue

- Règles : `18`.
- Complexité totale : `34`.
- NLL validation par pièce : `0.813679`.
- Seuil d'une erreur standard : `0.818862`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.257958 | avoidance |
| 2 | bloc central : triade majeure à l’état fondamental | +2.686669 | preference |
| 3 | bloc central : accord complet au premier renversement | +1.204751 | preference |
| 4 | bloc central : triade mineure à l’état fondamental | +1.978465 | preference |
| 5 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.806192 | avoidance |
| 6 | bloc central : septième de dominante complète sur temps faible | +1.230150 | preference |
| 7 | any_pair_central_abs_class_target_passing(all_voices)=9 | +0.755987 | preference |
| 8 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -1.049285 | avoidance |
| 9 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -1.951254 | avoidance |
| 10 | basse : répète par une nouvelle attaque la note précédente | -1.726449 | avoidance |
| 11 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -1.925772 | avoidance |
| 12 | basse avec ténor : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.620766 | preference |
| 13 | any_pair_central_abs_class_target_passing(all_voices)=10 | +1.318407 | preference |
| 14 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -0.895764 | avoidance |
| 15 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -0.946315 | avoidance |
| 16 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.630974 | avoidance |
| 17 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.967806 | avoidance |
| 18 | soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | +1.377488 | preference |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
