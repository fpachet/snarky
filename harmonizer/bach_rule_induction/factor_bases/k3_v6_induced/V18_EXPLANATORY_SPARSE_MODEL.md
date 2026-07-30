# V18 — MaxEnt parcimonieux à règles lisibles

V18 conserve la pseudo-vraisemblance exacte. Chaque colonne est un
prédicat K3 autonome et lisible ; les poids sont réestimés conjointement
après chaque ajout. Aucune statistique de génération n'intervient.

## Protocole

- Catalogue exact initial : `954`.
- Candidats lisibles : `816`.
- Famille exclue : `observed_vertical_set` (bitsets verticaux opaques).
- Pièces structure train/validation : `32/10`.
- Test réservé chargé : `false`.
- Sélection finale : règle d'une erreur standard.

## Frontière qualité–complexité

| Règles | Complexité | NLL validation par pièce | Erreur standard |
|---:|---:|---:|---:|
| 0 | 0 | 2.304205 | 0.067142 |
| 1 | 1 | 1.599701 | 0.062432 |
| 2 | 2 | 1.554880 | 0.067071 |
| 3 | 3 | 1.447283 | 0.068551 |
| 4 | 4 | 1.397466 | 0.067840 |
| 5 | 8 | 1.330945 | 0.073064 |
| 6 | 9 | 1.282886 | 0.072017 |
| 7 | 10 | 1.243441 | 0.074010 |
| 8 | 11 | 1.194095 | 0.071781 |
| 9 | 12 | 1.141648 | 0.075528 |
| 10 | 13 | 1.110317 | 0.075942 |
| 11 | 17 | 1.046167 | 0.081897 |
| 12 | 18 | 0.999828 | 0.087117 |
| 13 | 19 | 0.960839 | 0.084651 |
| 14 | 20 | 0.942612 | 0.083535 |
| 15 | 21 | 0.911156 | 0.084478 |
| 16 | 22 | 0.903533 | 0.081766 |
| 17 | 24 | 0.884447 | 0.078676 |
| 18 | 25 | 0.877959 | 0.077594 |
| 19 | 26 | 0.870633 | 0.077420 | **← retenu**
| 20 | 28 | 0.862940 | 0.074887 |
| 21 | 29 | 0.854589 | 0.073549 |
| 22 | 31 | 0.840528 | 0.078009 |
| 23 | 33 | 0.838131 | 0.076871 |
| 24 | 34 | 0.837342 | 0.077189 |
| 25 | 35 | 0.831919 | 0.077747 |
| 26 | 36 | 0.819284 | 0.075695 |
| 27 | 38 | 0.811743 | 0.073436 |
| 28 | 39 | 0.810896 | 0.073392 |
| 29 | 40 | 0.806174 | 0.072708 |
| 30 | 41 | 0.805173 | 0.071725 |

## Base retenue

- Règles : `19`.
- Complexité totale : `26`.
- NLL validation par pièce : `0.870633`.
- Seuil d'une erreur standard : `0.876898`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.376630 | avoidance |
| 2 | bloc central : 3 classes de hauteur distinctes | +0.459183 | preference |
| 3 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.649367 | avoidance |
| 4 | au moins une paire de voix : intervalle vertical de classe 3 (tierce mineure modulo l’octave) | +0.478473 | preference |
| 5 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -2.180480 | avoidance |
| 6 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -1.690173 | avoidance |
| 7 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.686309 | avoidance |
| 8 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -1.441133 | avoidance |
| 9 | basse : répète par une nouvelle attaque la note précédente | -1.775075 | avoidance |
| 10 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.919020 | avoidance |
| 11 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -2.189788 | avoidance |
| 12 | au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | +0.630667 | preference |
| 13 | au moins une paire de voix : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | +0.431636 | preference |
| 14 | basse avec ténor : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.818518 | preference |
| 15 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.512402 | preference |
| 16 | ténor : mouvement vers la note suivante supérieur à 1 demi-tons | +0.738589 | preference |
| 17 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.987153 | avoidance |
| 18 | ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | -1.005103 | avoidance |
| 19 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | -0.879847 | avoidance |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
