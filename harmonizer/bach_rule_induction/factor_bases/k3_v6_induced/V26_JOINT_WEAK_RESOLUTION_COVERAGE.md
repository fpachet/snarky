# V26 — couverture faible × résolution

Audit exécuté avant l'apprentissage. Chaque sonorité faible résiduelle
reçoit son rôle V25 et un statut binaire de la sonorité suivante :
accord nommé ou triade consonante incomplète, contre reste non licencié.

- Chorals : `32`.
- Blocs faibles résiduels : `552`.
- Partition exhaustive : `true`.

| État conjoint | Blocs Bach | Chorals Bach | Alternatives | Chorals possibles | Seuil |
|---|---:|---:|---:|---:|:---:|
| `exact_named_ambiguous__acceptable_following_sonority` | 32 | 15 | 2390 | 32 | oui |
| `exact_named_ambiguous__unacceptable_following_sonority` | 6 | 3 | 1045 | 30 | oui |
| `incomplete_consonant_triad__acceptable_following_sonority` | 38 | 18 | 8678 | 32 | oui |
| `incomplete_consonant_triad__unacceptable_following_sonority` | 20 | 13 | 6022 | 32 | oui |
| `triad_plus_one_ambiguous__acceptable_following_sonority` | 0 | 0 | 5005 | 32 | oui |
| `triad_plus_one_ambiguous__unacceptable_following_sonority` | 0 | 0 | 2468 | 30 | oui |
| `triad_plus_passing__acceptable_following_sonority` | 14 | 3 | 1438 | 30 | oui |
| `triad_plus_passing__unacceptable_following_sonority` | 2 | 1 | 457 | 22 | oui |
| `triad_plus_neighbor__acceptable_following_sonority` | 0 | 0 | 409 | 20 | oui |
| `triad_plus_neighbor__unacceptable_following_sonority` | 0 | 0 | 124 | 14 | oui |
| `triad_plus_suspension__acceptable_following_sonority` | 14 | 7 | 2332 | 32 | oui |
| `triad_plus_suspension__unacceptable_following_sonority` | 6 | 5 | 624 | 27 | oui |
| `triad_plus_appoggiatura__acceptable_following_sonority` | 0 | 0 | 638 | 29 | oui |
| `triad_plus_appoggiatura__unacceptable_following_sonority` | 0 | 0 | 184 | 18 | oui |
| `triad_plus_unlicensed__acceptable_following_sonority` | 88 | 28 | 26728 | 32 | oui |
| `triad_plus_unlicensed__unacceptable_following_sonority` | 16 | 11 | 10815 | 31 | oui |
| `other_unlicensed__acceptable_following_sonority` | 282 | 32 | 56773 | 32 | oui |
| `other_unlicensed__unacceptable_following_sonority` | 34 | 16 | 34356 | 32 | oui |

Les cellules insuffisamment couvertes restent dans la partition
conjointe ; elles ne sont ni sélectionnées seules ni transformées
en contraintes dures.
