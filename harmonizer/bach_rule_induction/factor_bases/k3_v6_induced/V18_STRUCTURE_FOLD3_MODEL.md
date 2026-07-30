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
| 0 | 0 | 2.421588 | 0.077398 |
| 1 | 1 | 1.789318 | 0.052260 |
| 2 | 2 | 1.688933 | 0.065960 |
| 3 | 3 | 1.534387 | 0.044287 |
| 4 | 7 | 1.474368 | 0.054378 |
| 5 | 8 | 1.421800 | 0.056365 |
| 6 | 9 | 1.371200 | 0.048839 |
| 7 | 10 | 1.298664 | 0.045047 |
| 8 | 11 | 1.249067 | 0.043555 |
| 9 | 12 | 1.198065 | 0.036965 |
| 10 | 16 | 1.146669 | 0.039307 |
| 11 | 17 | 1.105181 | 0.037973 |
| 12 | 18 | 1.079004 | 0.035703 |
| 13 | 19 | 1.059332 | 0.036532 |
| 14 | 20 | 1.020749 | 0.031905 |
| 15 | 22 | 1.016515 | 0.035204 |
| 16 | 24 | 1.016336 | 0.032003 |
| 17 | 25 | 0.999584 | 0.034499 |
| 18 | 26 | 0.992789 | 0.037747 |
| 19 | 27 | 0.982194 | 0.041820 |
| 20 | 28 | 0.975907 | 0.043770 |
| 21 | 29 | 0.968361 | 0.044366 |
| 22 | 31 | 0.961755 | 0.045756 |
| 23 | 33 | 0.945412 | 0.047776 |
| 24 | 35 | 0.930954 | 0.045918 |
| 25 | 36 | 0.928623 | 0.045267 |
| 26 | 38 | 0.915151 | 0.044019 | **← retenu**
| 27 | 40 | 0.905293 | 0.040194 |
| 28 | 41 | 0.900709 | 0.040209 |
| 29 | 42 | 0.892053 | 0.039140 |
| 30 | 43 | 0.888155 | 0.037578 |

## Base retenue

- Règles : `26`.
- Complexité totale : `38`.
- NLL validation par pièce : `0.915151`.
- Seuil d'une erreur standard : `0.925733`.

| # | Interprétation autonome | Poids | Modalité |
|---:|---|---:|---|
| 1 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.340006 | avoidance |
| 2 | bloc central : 3 classes de hauteur distinctes | +0.705076 | preference |
| 3 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.685018 | avoidance |
| 4 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -2.295571 | avoidance |
| 5 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -1.837520 | avoidance |
| 6 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.829893 | avoidance |
| 7 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -1.664921 | avoidance |
| 8 | basse : répète par une nouvelle attaque la note précédente | -1.507972 | avoidance |
| 9 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.728938 | avoidance |
| 10 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -2.198767 | avoidance |
| 11 | au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | +0.566818 | preference |
| 12 | au moins une paire de voix : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | -0.393795 | avoidance |
| 13 | ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | -1.267628 | avoidance |
| 14 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.453331 | preference |
| 15 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 3 | +0.352316 | preference |
| 16 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 4 | +0.190917 | preference |
| 17 | basse avec ténor : intervalle vertical de classe 9 (sixte majeure modulo l’octave) | -1.095280 | avoidance |
| 18 | ténor : mouvement vers la note suivante supérieur à 1 demi-tons | +0.613481 | preference |
| 19 | toutes voix : mouvement mélodique supérieur à 12 demi-tons | -1.596307 | avoidance |
| 20 | basse avec alto : intervalle vertical de classe 6 (triton) | -1.194770 | avoidance |
| 21 | alto avec basse : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | +0.718964 | preference |
| 22 | alto : directions successives (+0, -1) | +1.076899 | preference |
| 23 | toutes voix : directions successives (-1, -1) | +0.476549 | preference |
| 24 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.864908 | avoidance |
| 25 | soprano avec alto : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | +1.457557 | preference |
| 26 | bloc central : 4 classes distinctes au niveau métrique 0 | +1.005416 | preference |

Ces poids sont des estimations conjointes : la table ne prétend pas
encore transformer une forte pénalité en interdiction absolue. La
stabilité inter-échantillons et le test fermé restent requis avant
une RuleCard scientifique finale.
