# V24 — couverture du groupe de sonorités résiduelles

Cet audit est exécuté avant l'apprentissage. Les huit statuts couvrent
exactement le complément des accords nommés uniques V23 sur temps fort.
Aucun effet ni poids n'est consulté.

- Chorals : `32`.
- Blocs forts distincts : `1039`.
- Accords V23 nommés uniques : `858`.
- Blocs couverts par V24 : `181`.

| Statut V24 | Blocs Bach | Chorals Bach | Opportunités exactes | Chorals possibles | Seuil |
|---|---:|---:|---:|---:|:---:|
| `exact_named_ambiguous` | 16 | 11 | 544 | 32 | oui |
| `incomplete_consonant_triad` | 33 | 13 | 1252 | 32 | oui |
| `triad_plus_one_ambiguous` | 0 | 0 | 1224 | 32 | oui |
| `triad_plus_passing_or_neighbor` | 1 | 1 | 298 | 31 | oui |
| `triad_plus_suspension` | 4 | 2 | 148 | 26 | oui |
| `triad_plus_appoggiatura` | 3 | 2 | 179 | 25 | oui |
| `triad_plus_unlicensed` | 24 | 11 | 1742 | 32 | oui |
| `other_unlicensed` | 100 | 29 | 1819 | 32 | oui |

Le statut `other_unlicensed` n'est pas une règle experte : c'est le
reste déterministe du vocabulaire. Son signe et son poids seront
appris conjointement avec les sept autres cellules.
