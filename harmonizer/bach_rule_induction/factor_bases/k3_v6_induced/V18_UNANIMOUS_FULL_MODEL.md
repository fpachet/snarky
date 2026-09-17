# V18 — noyau unanime réappris sur le corpus complet

Les quatorze prédicats présents dans les cinq réinductions de structure
sont gelés. Seuls les profils auxiliaires et leurs poids sont réappris
sur les 251 chorals de train, avec arrêt sur les 50 de validation.

## Résultat

- Train : `251` chorals, `53604` décisions.
- Validation : `50` chorals, `10414` décisions.
- Règles : `14`.
- NLL validation sans règles : `2.406648`.
- NLL validation avec noyau unanime : `0.981894`.
- Gain : `1.424754`.
- Test réservé chargé : `false`.

| # | Règle | Poids complet |
|---:|---|---:|
| 1 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.921344 |
| 2 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -1.075316 |
| 3 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -1.931205 |
| 4 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -1.852317 |
| 5 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -1.300369 |
| 6 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.754909 |
| 7 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -1.517677 |
| 8 | au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | +0.526404 |
| 9 | basse : répète par une nouvelle attaque la note précédente | -1.927338 |
| 10 | bloc central : 3 classes de hauteur distinctes | +0.512340 |
| 11 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.470940 |
| 12 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.270309 |
| 13 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.788612 |
| 14 | ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | -1.217689 |

Cette étape gèle le modèle explicatif destiné aux RuleCards et à la
compilation Snarky. La génération reste un audit externe.
