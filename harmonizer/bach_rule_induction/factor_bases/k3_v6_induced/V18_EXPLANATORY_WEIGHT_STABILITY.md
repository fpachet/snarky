# V18 — stabilité des poids explicatifs

Les 32 chorals de structure sont divisés en quatre groupes par pièce.
Chaque estimation apprend les mêmes 19 règles sur 24 chorals et mesure
la NLL sur les huit chorals retirés. Ce test porte sur la stabilité des
poids conditionnellement à la structure retenue, pas encore sur la
stabilité de la découverte elle-même.

## Résumé

- Règles testées : `19`.
- Signes stables : `19`.
- Poids non nuls dans les quatre replis : `19`.

| Règle | Poids complet | Moyenne replis | Étendue | Signe stable |
|---|---:|---:|---:|:---:|
| toutes voix : mouvement mélodique supérieur à 2 demi-tons | -1.3766 | -1.1501 | [-1.1680, -1.1288] | oui |
| bloc central : 3 classes de hauteur distinctes | +0.4592 | +0.5252 | [+0.5096, +0.5376] | oui |
| au moins deux voix adjacentes : écart ordonné ≤ 2 demi-tons au bloc central | -0.6494 | -0.5215 | [-0.5735, -0.4869] | oui |
| au moins une paire de voix : intervalle vertical de classe 3 (tierce mineure modulo l’octave) | +0.4785 | +0.5141 | [+0.4630, +0.5601] | oui |
| au moins une paire de voix : conserve l’intervalle de classe 0 par mouvement direct non nul | -2.1805 | -1.5202 | [-1.5401, -1.5033] | oui |
| au moins une paire de voix : intervalle vertical de classe 11 (septième majeure modulo l’octave) | -1.6902 | -1.3280 | [-1.3441, -1.3124] | oui |
| au moins une paire de voix : intervalle vertical de classe 10 (septième mineure modulo l’octave) | -0.6863 | -0.5997 | [-0.6088, -0.5777] | oui |
| au moins une paire de voix : intervalle vertical de classe 1 (seconde mineure modulo l’octave) | -1.4411 | -1.1501 | [-1.1852, -1.1196] | oui |
| basse : répète par une nouvelle attaque la note précédente | -1.7751 | -1.5421 | [-1.6186, -1.4683] | oui |
| toutes voix : mouvement mélodique supérieur à 7 demi-tons | -0.9190 | -0.7192 | [-0.7715, -0.6836] | oui |
| au moins une paire de voix : conserve l’intervalle de classe 7 par mouvement direct non nul | -2.1898 | -1.4956 | [-1.5151, -1.4793] | oui |
| au moins une paire de voix : intervalle vertical de classe 7 (quinte juste modulo l’octave) | +0.6307 | +0.5977 | [+0.5772, +0.6219] | oui |
| au moins une paire de voix : intervalle vertical de classe 4 (tierce majeure modulo l’octave) | +0.4316 | +0.4371 | [+0.4042, +0.4566] | oui |
| basse avec ténor : intervalle vertical de classe 0 (unisson ou octave modulo l’octave) | +0.8185 | +0.7642 | [+0.7338, +0.7807] | oui |
| toutes voix : mouvement adjacent de classe 1 (seconde mineure modulo l’octave) | +0.5124 | +0.5367 | [+0.5140, +0.5813] | oui |
| ténor : mouvement vers la note suivante supérieur à 1 demi-tons | +0.7386 | +0.6685 | [+0.5894, +0.7152] | oui |
| au moins une paire de voix : arrive par mouvement direct sur la classe d’intervalle 2 | -0.9872 | -0.8368 | [-0.9032, -0.8002] | oui |
| ténor avec basse : intervalle vertical de classe 5 (quarte juste modulo l’octave) | -1.0051 | -0.9274 | [-1.0019, -0.8932] | oui |
| au moins deux voix adjacentes : écart ordonné ≤ -1 demi-tons au bloc central | -0.8798 | -0.5359 | [-0.5512, -0.5143] | oui |

## NLL des chorals retirés

| Repli | Sans règles | Avec 19 règles | Gain |
|---:|---:|---:|---:|
| 1 | 2.476715 | 1.018679 | 1.458037 |
| 2 | 2.479603 | 0.928963 | 1.550640 |
| 3 | 2.411021 | 0.994801 | 1.416219 |
| 4 | 2.324990 | 1.002236 | 1.322754 |
