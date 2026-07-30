# V19 — stabilité des règles avec statut triadique

La procédure complète de génération de colonnes et de sélection à une
erreur standard est répétée sur quatre partitions 24/8 des 32 chorals
de structure. Le modèle original 32/10 constitue la cinquième
réinduction.

## Résumé

- Tailles des cinq bases : `[20, 24, 23, 26, 26]`.
- Jaccard moyen entre bases : `0.735`.
- Règles présentes dans au moins 3/5 bases : `23`.
- Règles présentes dans au moins 4/5 bases : `19`.
- Noyau unanime 5/5 : `18`.

## Noyau explicatif unanime

| Règle | Étendue des poids |
|---|---:|
| any_pair_central_abs_class_target_passing(all_voices)=10 | [+1.193, +1.426] |
| any_pair_central_abs_class_target_passing(all_voices)=9 | [+0.793, +0.952] |
| au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | [-0.777, -0.628] |
| au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | [-1.096, -0.867] |
| au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | [-2.207, -1.971] |
| au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | [-2.233, -1.852] |
| au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | [-1.328, -1.227] |
| au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | [-0.770, -0.607] |
| au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | [-1.424, -1.330] |
| au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | [+0.459, +0.570] |
| basse : répète par une nouvelle attaque la note précédente | [-1.763, -1.501] |
| basse avec ténor : intervalle vertical de classe 9 (sixte majeure modulo l’octave) | [-1.286, -1.146] |
| bloc central : triade majeure ou mineure complète sur temps faible | [+0.805, +0.974] |
| bloc central : triade majeure ou mineure complète sur temps fort | [+1.268, +1.398] |
| toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | [+0.371, +0.551] |
| toutes voix : mouvement mélodique supérieur à 2 demi-tons | [-1.207, -1.084] |
| toutes voix : mouvement mélodique supérieur à 7 demi-tons | [-1.015, -0.762] |
| ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | [-1.274, -1.032] |

## Tous les prédicats rencontrés

| Fréquence | Règle | Signe stable lorsqu'elle est sélectionnée |
|---:|---|:---:|
| 5/5 | any_pair_central_abs_class_target_passing(all_voices)=10 | oui |
| 5/5 | any_pair_central_abs_class_target_passing(all_voices)=9 | oui |
| 5/5 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | oui |
| 5/5 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | oui |
| 5/5 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | oui |
| 5/5 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | oui |
| 5/5 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | oui |
| 5/5 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | oui |
| 5/5 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | oui |
| 5/5 | au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | oui |
| 5/5 | basse : répète par une nouvelle attaque la note précédente | oui |
| 5/5 | basse avec ténor : intervalle vertical de classe 9 (sixte majeure modulo l’octave) | oui |
| 5/5 | bloc central : triade majeure ou mineure complète sur temps faible | oui |
| 5/5 | bloc central : triade majeure ou mineure complète sur temps fort | oui |
| 5/5 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | oui |
| 5/5 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | oui |
| 5/5 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | oui |
| 5/5 | ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | oui |
| 4/5 | basse avec ténor : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | oui |
| 3/5 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | oui |
| 3/5 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 10 | oui |
| 3/5 | au moins une paire de voix : conserve l’intervalle de classe 3 par mouvement direct non nul | oui |
| 3/5 | soprano avec basse : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | oui |
| 2/5 | alto avec basse : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | oui |
| 2/5 | soprano avec alto : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | oui |
| 2/5 | ténor : mouvement vers la note suivante supérieur à 1 demi-tons | oui |
| 1/5 | alto : directions successives (+0, -1) | oui |
| 1/5 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 3 | oui |
| 1/5 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 7 | oui |
| 1/5 | au moins une paire de voix : intervalle vertical de classe 3 (tierce mineure modulo l’octave) | oui |
| 1/5 | soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | oui |
| 1/5 | soprano avec alto : intervalle vertical de classe 5 (quarte juste modulo l’octave) | oui |
| 1/5 | toutes voix : mouvement mélodique supérieur à 12 demi-tons | oui |

Le noyau 5/5 est retenu pour le réapprentissage complet. Les règles
3/5 ou 4/5 restent des spécialisations candidates, mais ne sont pas
nécessaires pour établir la première base explicative robuste.
