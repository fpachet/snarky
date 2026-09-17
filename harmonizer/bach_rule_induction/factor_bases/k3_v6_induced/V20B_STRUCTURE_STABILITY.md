# V20B — stabilité des statuts harmoniques identifiables

La procédure complète de génération de colonnes et de sélection à une
erreur standard est répétée sur quatre partitions 24/8 des 32 chorals
de structure. Le modèle original 32/10 constitue la cinquième
réinduction.

## Résumé

- Tailles des cinq bases : `[19, 22, 26, 26, 23]`.
- Jaccard moyen entre bases : `0.718`.
- Règles présentes dans au moins 3/5 bases : `22`.
- Règles présentes dans au moins 4/5 bases : `21`.
- Noyau unanime 5/5 : `15`.

## Noyau explicatif unanime

| Règle | Étendue des poids |
|---|---:|
| any_pair_central_abs_class_target_passing(all_voices)=10 | [+1.031, +1.285] |
| any_pair_central_abs_class_target_passing(all_voices)=9 | [+0.666, +0.798] |
| au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | [-0.754, -0.475] |
| au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 10 | [-1.142, -0.765] |
| au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | [-1.208, -0.888] |
| au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | [-2.120, -1.835] |
| au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | [-2.133, -1.913] |
| basse : répète par une nouvelle attaque la note précédente | [-1.929, -1.488] |
| bloc central : accord complet au premier renversement | [+1.073, +1.614] |
| bloc central : septième de dominante complète | [+1.045, +1.401] |
| bloc central : triade majeure à l’état fondamental | [+2.410, +2.929] |
| bloc central : triade mineure à l’état fondamental | [+1.755, +2.163] |
| soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | [+1.236, +1.483] |
| toutes voix : mouvement mélodique supérieur à 2 demi-tons | [-1.339, -1.155] |
| toutes voix : mouvement mélodique supérieur à 7 demi-tons | [-1.062, -0.926] |

## Tous les prédicats rencontrés

| Fréquence | Règle | Signe stable lorsqu'elle est sélectionnée |
|---:|---|:---:|
| 5/5 | any_pair_central_abs_class_target_passing(all_voices)=10 | oui |
| 5/5 | any_pair_central_abs_class_target_passing(all_voices)=9 | oui |
| 5/5 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | oui |
| 5/5 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 10 | oui |
| 5/5 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | oui |
| 5/5 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | oui |
| 5/5 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | oui |
| 5/5 | basse : répète par une nouvelle attaque la note précédente | oui |
| 5/5 | bloc central : accord complet au premier renversement | oui |
| 5/5 | bloc central : septième de dominante complète | oui |
| 5/5 | bloc central : triade majeure à l’état fondamental | oui |
| 5/5 | bloc central : triade mineure à l’état fondamental | oui |
| 5/5 | soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | oui |
| 5/5 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | oui |
| 5/5 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | oui |
| 4/5 | any_pair_central_abs_class_metric(all_voices)=7,1 | oui |
| 4/5 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | oui |
| 4/5 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 3 | oui |
| 4/5 | au moins une paire de voix : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | oui |
| 4/5 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | oui |
| 4/5 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | oui |
| 3/5 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | oui |
| 2/5 | alto : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | oui |
| 2/5 | basse avec alto : intervalle vertical de classe 6 (triton) | oui |
| 2/5 | bloc central : septième majeure complète | oui |
| 2/5 | ténor : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | oui |
| 1/5 | alto : directions successives (+0, -1) | oui |
| 1/5 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | oui |
| 1/5 | basse avec ténor : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | oui |
| 1/5 | bloc central : accord complet au troisième renversement | oui |
| 1/5 | soprano avec alto : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | oui |
| 1/5 | ténor : mouvement vers la note suivante supérieur à 1 demi-tons | oui |

Le noyau 5/5 est retenu pour le réapprentissage complet. Les règles
3/5 ou 4/5 restent des spécialisations candidates, mais ne sont pas
nécessaires pour établir la première base explicative robuste.
