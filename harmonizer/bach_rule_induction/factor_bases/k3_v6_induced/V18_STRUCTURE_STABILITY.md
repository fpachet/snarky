# V18 — stabilité de la découverte des règles

La procédure complète de génération de colonnes et de sélection à une
erreur standard est répétée sur quatre partitions 24/8 des 32 chorals
de structure. Le modèle original 32/10 constitue la cinquième
réinduction.

## Résumé

- Tailles des cinq bases : `[19, 24, 24, 26, 24]`.
- Jaccard moyen entre bases : `0.620`.
- Règles présentes dans au moins 3/5 bases : `22`.
- Règles présentes dans au moins 4/5 bases : `17`.
- Noyau unanime 5/5 : `14`.

## Noyau explicatif unanime

| Règle | Étendue des poids |
|---|---:|
| au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | [-0.725, -0.598] |
| au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | [-1.094, -0.862] |
| au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | [-2.296, -1.991] |
| au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | [-2.289, -2.032] |
| au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | [-1.665, -1.441] |
| au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | [-0.830, -0.686] |
| au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | [-1.838, -1.690] |
| au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | [+0.503, +0.692] |
| basse : répète par une nouvelle attaque la note précédente | [-1.860, -1.508] |
| bloc central : 3 classes de hauteur distinctes | [+0.459, +0.797] |
| toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | [+0.384, +0.512] |
| toutes voix : mouvement mélodique supérieur à 2 demi-tons | [-1.377, -1.263] |
| toutes voix : mouvement mélodique supérieur à 7 demi-tons | [-0.938, -0.729] |
| ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | [-1.518, -1.005] |

## Tous les prédicats rencontrés

| Fréquence | Règle | Signe stable lorsqu'elle est sélectionnée |
|---:|---|:---:|
| 5/5 | au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | oui |
| 5/5 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | oui |
| 5/5 | au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | oui |
| 5/5 | au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | oui |
| 5/5 | au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | oui |
| 5/5 | au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | oui |
| 5/5 | au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | oui |
| 5/5 | au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | oui |
| 5/5 | basse : répète par une nouvelle attaque la note précédente | oui |
| 5/5 | bloc central : 3 classes de hauteur distinctes | oui |
| 5/5 | toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | oui |
| 5/5 | toutes voix : mouvement mélodique supérieur à 2 demi-tons | oui |
| 5/5 | toutes voix : mouvement mélodique supérieur à 7 demi-tons | oui |
| 5/5 | ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | oui |
| 4/5 | au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | oui |
| 4/5 | basse avec ténor : intervalle vertical de classe 9 (sixte majeure modulo l’octave) | oui |
| 4/5 | ténor : mouvement vers la note suivante supérieur à 1 demi-tons | oui |
| 3/5 | alto avec basse : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | oui |
| 3/5 | au moins une paire de voix : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | oui |
| 3/5 | au moins une paire de voix : intervalle vertical de classe 3 (tierce mineure modulo l’octave) | oui |
| 3/5 | bloc central : 4 classes distinctes au niveau métrique 0 | oui |
| 3/5 | toutes voix : directions successives (-1, -1) | oui |
| 2/5 | au moins une paire de voix : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | oui |
| 2/5 | basse avec alto : intervalle vertical de classe 6 (triton) | oui |
| 2/5 | basse avec ténor : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | oui |
| 2/5 | soprano avec alto : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | oui |
| 2/5 | soprano avec basse : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | oui |
| 1/5 | alto : directions successives (+0, -1) | oui |
| 1/5 | alto avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | oui |
| 1/5 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 3 | oui |
| 1/5 | au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 4 | oui |
| 1/5 | au moins une paire de voix : conserve l’intervalle de classe 3 par mouvement direct non nul | oui |
| 1/5 | au moins une paire de voix : intervalle vertical de classe 5 (quarte juste modulo l’octave) | oui |
| 1/5 | soprano avec alto : intervalle vertical de classe 2 (seconde majeure modulo l’octave) | oui |
| 1/5 | soprano et alto : écart ordonné ≤ 2 demi-tons au bloc central | oui |
| 1/5 | toutes voix : mouvement mélodique supérieur à 12 demi-tons | oui |
| 1/5 | ténor : intervalle vers la note suivante de classe 0 (unisson ou octave modulo l’octave) | oui |

Le noyau 5/5 est retenu pour le réapprentissage complet. Les règles
3/5 ou 4/5 restent des spécialisations candidates, mais ne sont pas
nécessaires pour établir la première base explicative robuste.
