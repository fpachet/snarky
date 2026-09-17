# V18 — MaxEnt parcimonieux à règles lisibles

V18 conserve la pseudo-vraisemblance exacte. Chaque colonne est un
prédicat K3 autonome et lisible ; les poids sont réestimés conjointement
après chaque ajout. Aucune statistique de génération n'intervient.

## Protocole

- Catalogue exact initial : `1256`.
- Candidats lisibles : `1118`.
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
| 6 | 8 | 1.114557 | 0.089407 |
| 7 | 12 | 1.084338 | 0.091743 |
| 8 | 13 | 1.059672 | 0.092651 |
| 9 | 17 | 1.003146 | 0.096994 |
| 10 | 18 | 0.957200 | 0.101074 |
| 11 | 22 | 0.918446 | 0.099652 |
| 12 | 23 | 0.902455 | 0.096234 |
| 13 | 27 | 0.879277 | 0.090524 |
| 14 | 29 | 0.858103 | 0.089590 |
| 15 | 31 | 0.850943 | 0.090730 |
| 16 | 32 | 0.843741 | 0.090254 |
| 17 | 34 | 0.842686 | 0.088518 |
| 18 | 36 | 0.836218 | 0.084010 |
| 19 | 37 | 0.820487 | 0.082117 | **← retenu**
| 20 | 38 | 0.810555 | 0.082710 |
| 21 | 39 | 0.806605 | 0.082188 |
| 22 | 40 | 0.800720 | 0.081800 |
| 23 | 41 | 0.792876 | 0.083156 |
| 24 | 42 | 0.786427 | 0.080531 |
| 25 | 43 | 0.785568 | 0.081336 |
| 26 | 44 | 0.773338 | 0.079076 |
| 27 | 45 | 0.764847 | 0.080169 |
| 28 | 46 | 0.762015 | 0.080245 |
| 29 | 47 | 0.755187 | 0.080821 |
| 30 | 49 | 0.752477 | 0.080243 |

## Base retenue

- Règles : `19`.
- Complexité totale : `37`.
- NLL validation par pièce : `0.820487`.
- Seuil d'une erreur standard : `0.832720`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.163234 | avoidance |
| 2 | bloc central : triade majeure à l’état fondamental | +2.928742 | preference |
| 3 | bloc central : accord complet au premier renversement | +1.614436 | preference |
| 4 | bloc central : triade mineure à l’état fondamental | +2.163020 | preference |
| 5 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.753650 | avoidance |
| 6 | bloc central : septième de dominante complète | +1.401128 | preference |
| 7 | any_pair_central_abs_class_target_passing(all_voices)=9 | +0.798144 | preference |
| 8 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -1.061989 | avoidance |
| 9 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -2.015247 | avoidance |
| 10 | basse : répète par une nouvelle attaque la note précédente | -1.626831 | avoidance |
| 11 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -1.984723 | avoidance |
| 12 | au moins une paire de voix : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.511038 | preference |
| 13 | any_pair_central_abs_class_target_passing(all_voices)=10 | +1.174099 | preference |
| 14 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 3 | +0.297179 | preference |
| 15 | any_pair_central_abs_class_metric(all_voices)=7,1 | +0.457165 | preference |
| 16 | soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | +1.483195 | preference |
| 17 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 10 | -0.907745 | avoidance |
| 18 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.902581 | avoidance |
| 19 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.361915 | preference |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
