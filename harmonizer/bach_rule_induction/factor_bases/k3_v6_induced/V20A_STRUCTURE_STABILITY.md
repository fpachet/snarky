# V20A — stabilité des statuts harmoniques nommés

La procédure complète de génération de colonnes et de sélection à une
erreur standard est répétée sur quatre partitions 24/8 des 32 chorals
de structure. Le modèle original 32/10 constitue la cinquième
réinduction.

## Résumé

- Tailles des cinq bases : `[18, 23, 26, 27, 23]`.
- Jaccard moyen entre bases : `0.653`.
- Règles présentes dans au moins 3/5 bases : `24`.
- Règles présentes dans au moins 4/5 bases : `18`.
- Noyau unanime 5/5 : `14`.

## Noyau explicatif unanime

| Règle | Étendue des poids |
|---|---:|
| any_pair_central_abs_class_target_passing(all_voices)=10 | [+0.955, +1.380] |
| au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | [-0.806, -0.454] |
| au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | [-1.208, -0.902] |
| au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | [-2.109, -1.835] |
| au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | [-2.160, -1.913] |
| au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | [-1.237, -0.893] |
| au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | [-1.119, -0.793] |
| basse : répète par une nouvelle attaque la note précédente | [-1.917, -1.488] |
| bloc central : accord complet au premier renversement | [+1.073, +1.377] |
| bloc central : triade majeure à l’état fondamental | [+2.410, +2.876] |
| bloc central : triade mineure à l’état fondamental | [+1.755, +2.134] |
| soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | [+1.194, +1.383] |
| toutes voix : mouvement mélodique supérieur à 2 demi-tons | [-1.377, -1.155] |
| toutes voix : mouvement mélodique supérieur à 7 demi-tons | [-1.049, -0.766] |

## Tous les prédicats rencontrés

| Fréquence | Règle | Signe stable lorsqu'elle est sélectionnée |
|---:|---|:---:|
| 5/5 | any_pair_central_abs_class_target_passing(all_voices)=10 | oui |
| 5/5 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | oui |
| 5/5 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | oui |
| 5/5 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | oui |
| 5/5 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | oui |
| 5/5 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | oui |
| 5/5 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | oui |
| 5/5 | basse : répète par une nouvelle attaque la note précédente | oui |
| 5/5 | bloc central : accord complet au premier renversement | oui |
| 5/5 | bloc central : triade majeure à l’état fondamental | oui |
| 5/5 | bloc central : triade mineure à l’état fondamental | oui |
| 5/5 | soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | oui |
| 5/5 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | oui |
| 5/5 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | oui |
| 4/5 | any_pair_central_abs_class_target_passing(all_voices)=9 | oui |
| 4/5 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | oui |
| 4/5 | basse avec ténor : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | oui |
| 4/5 | bloc central : septième de dominante complète sur temps faible | oui |
| 3/5 | alto : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | oui |
| 3/5 | any_pair_central_abs_class_metric(all_voices)=7,1 | oui |
| 3/5 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 10 | oui |
| 3/5 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | oui |
| 3/5 | bloc central : septième majeure complète | oui |
| 3/5 | ténor : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | oui |
| 2/5 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 3 | oui |
| 2/5 | basse avec alto : intervalle vertical de classe 6 (triton) | oui |
| 1/5 | alto : directions successives (+0, -1) | oui |
| 1/5 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 7 | oui |
| 1/5 | au moins une paire de voix : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | oui |
| 1/5 | bloc central : septième de dominante complète | oui |
| 1/5 | soprano avec alto : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | oui |
| 1/5 | soprano avec basse : intervalle vertical de classe 3 (tierce mineure modulo l’octave) | oui |
| 1/5 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | oui |
| 1/5 | toutes voix : mouvement mélodique supérieur à 12 demi-tons | oui |
| 1/5 | ténor : mouvement vers la note suivante supérieur à 1 demi-tons | oui |

Le noyau 5/5 est retenu pour le réapprentissage complet. Les règles
3/5 ou 4/5 restent des spécialisations candidates, mais ne sont pas
nécessaires pour établir la première base explicative robuste.
