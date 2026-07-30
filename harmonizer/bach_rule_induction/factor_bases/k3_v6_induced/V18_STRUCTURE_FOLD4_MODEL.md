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
| 0 | 0 | 2.292360 | 0.059553 |
| 1 | 1 | 1.750656 | 0.066672 |
| 2 | 2 | 1.687571 | 0.075479 |
| 3 | 3 | 1.576723 | 0.064917 |
| 4 | 4 | 1.556307 | 0.062604 |
| 5 | 8 | 1.489379 | 0.068999 |
| 6 | 9 | 1.416320 | 0.064822 |
| 7 | 10 | 1.366649 | 0.058617 |
| 8 | 11 | 1.314354 | 0.056390 |
| 9 | 12 | 1.281146 | 0.051655 |
| 10 | 13 | 1.215765 | 0.037839 |
| 11 | 14 | 1.201956 | 0.037381 |
| 12 | 18 | 1.129331 | 0.042494 |
| 13 | 19 | 1.092392 | 0.039137 |
| 14 | 20 | 1.073822 | 0.035894 |
| 15 | 21 | 1.039485 | 0.039142 |
| 16 | 22 | 1.025262 | 0.040330 |
| 17 | 24 | 1.002499 | 0.040273 |
| 18 | 25 | 0.991561 | 0.040762 |
| 19 | 26 | 0.987494 | 0.041400 |
| 20 | 28 | 0.980659 | 0.039734 |
| 21 | 29 | 0.962238 | 0.035119 |
| 22 | 30 | 0.957461 | 0.037182 |
| 23 | 31 | 0.947794 | 0.035761 |
| 24 | 32 | 0.937504 | 0.034387 | **← retenu**
| 25 | 34 | 0.927557 | 0.041651 |
| 26 | 35 | 0.926610 | 0.044910 |
| 27 | 36 | 0.915957 | 0.046277 |
| 28 | 37 | 0.910884 | 0.044481 |
| 29 | 39 | 0.896255 | 0.049066 |
| 30 | 40 | 0.895791 | 0.046718 |

## Base retenue

- Règles : `24`.
- Complexité totale : `32`.
- NLL validation par pièce : `0.937504`.
- Seuil d'une erreur standard : `0.942509`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.357375 | avoidance |
| 2 | bloc central : 3 classes de hauteur distinctes | +0.478324 | preference |
| 3 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.725360 | avoidance |
| 4 | au moins une paire de voix : intervalle vertical de classe 3 (tierce mineure modulo l’octave) | +0.614328 | preference |
| 5 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -2.173931 | avoidance |
| 6 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -1.778717 | avoidance |
| 7 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.738264 | avoidance |
| 8 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -1.555520 | avoidance |
| 9 | basse : répète par une nouvelle attaque la note précédente | -1.842484 | avoidance |
| 10 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.890080 | avoidance |
| 11 | au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | +0.691565 | preference |
| 12 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -2.102429 | avoidance |
| 13 | au moins une paire de voix : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | +0.472826 | preference |
| 14 | basse avec ténor : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.887029 | preference |
| 15 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.472020 | preference |
| 16 | ténor : mouvement vers la note suivante supérieur à 1 demi-tons | +0.625187 | preference |
| 17 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -1.026984 | avoidance |
| 18 | ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | -1.518417 | avoidance |
| 19 | basse avec ténor : intervalle vertical de classe 9 (sixte majeure modulo l’octave) | -0.897153 | avoidance |
| 20 | toutes voix : directions successives (-1, -1) | +0.509595 | preference |
| 21 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | -0.932610 | avoidance |
| 22 | au moins une paire de voix : intervalle vertical de classe 5 (quarte juste modulo l’octave) | +0.416244 | preference |
| 23 | alto avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | -1.070682 | avoidance |
| 24 | soprano et alto : écart ordonné ≤ 2 demi-tons au bloc central | +1.207364 | preference |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
