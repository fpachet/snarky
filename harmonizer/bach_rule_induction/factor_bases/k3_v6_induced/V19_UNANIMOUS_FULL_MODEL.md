# V19 — noyau triadique unanime réappris sur le corpus complet

Les 18 prédicats présents dans les cinq réinductions de structure sont gelés. Seuls les profils auxiliaires et leurs poids sont réappris sur les 251 chorals de train, avec arrêt sur les 50 de validation.

## Résultat

- Train : `251` chorals, `53604` décisions.
- Validation : `50` chorals, `10414` décisions.
- Règles : `18`.
- NLL validation sans règles : `2.406648`.
- NLL validation avec noyau unanime : `0.887879`.
- Gain : `1.518768`.
- Test réservé chargé : `false`.

| # | Règle | Poids complet |
|---:|---|---:|
| 1 | any_pair_central_abs_class_target_passing(all_voices)=10 | +1.438632 |
| 2 | any_pair_central_abs_class_target_passing(all_voices)=9 | +0.788653 |
| 3 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.703433 |
| 4 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.966948 |
| 5 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -1.805272 |
| 6 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -1.796999 |
| 7 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -1.124980 |
| 8 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.844641 |
| 9 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -1.252191 |
| 10 | au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | +0.447324 |
| 11 | basse : répète par une nouvelle attaque la note précédente | -1.793174 |
| 12 | basse avec ténor : intervalle vertical de classe 9 (sixte majeure modulo l’octave) | -1.141295 |
| 13 | bloc central : triade majeure ou mineure complète sur temps faible | +0.926829 |
| 14 | bloc central : triade majeure ou mineure complète sur temps fort | +1.457887 |
| 15 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.411916 |
| 16 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.103878 |
| 17 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.835948 |
| 18 | ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | -1.094462 |

Cette étape gèle le modèle explicatif destiné aux RuleCards et à la
compilation Snarky. La génération reste un audit externe.
