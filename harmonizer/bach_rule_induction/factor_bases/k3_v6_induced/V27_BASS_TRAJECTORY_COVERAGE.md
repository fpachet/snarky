# V27 — couverture des trajectoires de basse

La partition est gelée avant l'apprentissage. Chaque bloc reçoit
exactement un statut harmonique ou mélodique de basse.

| Statut | Blocs Bach | Chorals Bach | Alternatives | Chorals possibles | Seuil |
|---|---:|---:|---:|---:|:---:|
| `named_chord_bass` | 2579 | 32 | 145265 | 32 | oui |
| `consonant_scaffold_chord_tone` | 183 | 31 | 80419 | 32 | oui |
| `diatonic_passing` | 137 | 31 | 20843 | 32 | oui |
| `chromatic_passing` | 3 | 3 | 3590 | 32 | oui |
| `diatonic_neighbor` | 18 | 9 | 4040 | 30 | oui |
| `chromatic_neighbor` | 1 | 1 | 959 | 31 | oui |
| `prepared_step_resolution` | 46 | 18 | 13746 | 32 | oui |
| `attacked_step_resolution` | 7 | 6 | 14858 | 32 | oui |
| `other_diatonic` | 275 | 32 | 107305 | 32 | oui |
| `other_chromatic` | 9 | 7 | 33555 | 32 | oui |

Les statuts chromatiques authentiques sont rares, mais toutes les
cellules disposent d'assez d'alternatives contrefactuelles pour un
apprentissage conjoint. Aucune rareté n'est convertie en interdit.
