# V29 — couverture des successions fortes

La partition croise trois types de sonorité précédente, trois types
de sonorité courante et quatre tailles d'arrivée de basse. Une seule
cellule est active par bloc fort et par alternative.

| État conjoint | Blocs Bach | Chorals Bach | Alternatives | Chorals possibles | Seuil |
|---|---:|---:|---:|---:|:---:|
| `consonant_scaffold__to__consonant_scaffold__with__repeated_bass` | 16 | 10 | 899 | 32 | oui |
| `consonant_scaffold__to__consonant_scaffold__with__semitone_arrival` | 64 | 25 | 3108 | 32 | oui |
| `consonant_scaffold__to__consonant_scaffold__with__whole_tone_arrival` | 52 | 28 | 3460 | 31 | oui |
| `consonant_scaffold__to__consonant_scaffold__with__skip_or_leap_arrival` | 177 | 32 | 11924 | 32 | oui |
| `consonant_scaffold__to__other_named_sonority__with__repeated_bass` | 5 | 4 | 515 | 28 | oui |
| `consonant_scaffold__to__other_named_sonority__with__semitone_arrival` | 20 | 12 | 2802 | 31 | oui |
| `consonant_scaffold__to__other_named_sonority__with__whole_tone_arrival` | 38 | 20 | 3345 | 32 | oui |
| `consonant_scaffold__to__other_named_sonority__with__skip_or_leap_arrival` | 40 | 15 | 8966 | 32 | oui |
| `consonant_scaffold__to__residual_sonority__with__repeated_bass` | 3 | 2 | 2374 | 31 | oui |
| `consonant_scaffold__to__residual_sonority__with__semitone_arrival` | 12 | 9 | 8290 | 32 | oui |
| `consonant_scaffold__to__residual_sonority__with__whole_tone_arrival` | 33 | 16 | 10477 | 32 | oui |
| `consonant_scaffold__to__residual_sonority__with__skip_or_leap_arrival` | 18 | 12 | 29860 | 32 | oui |
| `other_named_sonority__to__consonant_scaffold__with__repeated_bass` | 4 | 2 | 338 | 30 | oui |
| `other_named_sonority__to__consonant_scaffold__with__semitone_arrival` | 113 | 30 | 5114 | 32 | oui |
| `other_named_sonority__to__consonant_scaffold__with__whole_tone_arrival` | 108 | 27 | 5341 | 32 | oui |
| `other_named_sonority__to__consonant_scaffold__with__skip_or_leap_arrival` | 100 | 29 | 8474 | 32 | oui |
| `other_named_sonority__to__other_named_sonority__with__repeated_bass` | 8 | 4 | 486 | 28 | oui |
| `other_named_sonority__to__other_named_sonority__with__semitone_arrival` | 6 | 5 | 3306 | 32 | oui |
| `other_named_sonority__to__other_named_sonority__with__whole_tone_arrival` | 30 | 17 | 3823 | 32 | oui |
| `other_named_sonority__to__other_named_sonority__with__skip_or_leap_arrival` | 5 | 4 | 5707 | 32 | oui |
| `other_named_sonority__to__residual_sonority__with__repeated_bass` | 1 | 1 | 1386 | 31 | oui |
| `other_named_sonority__to__residual_sonority__with__semitone_arrival` | 25 | 16 | 11823 | 32 | oui |
| `other_named_sonority__to__residual_sonority__with__whole_tone_arrival` | 6 | 4 | 11263 | 32 | oui |
| `other_named_sonority__to__residual_sonority__with__skip_or_leap_arrival` | 11 | 7 | 18701 | 32 | oui |
| `residual_sonority__to__consonant_scaffold__with__repeated_bass` | 14 | 7 | 539 | 20 | oui |
| `residual_sonority__to__consonant_scaffold__with__semitone_arrival` | 17 | 9 | 774 | 16 | oui |
| `residual_sonority__to__consonant_scaffold__with__whole_tone_arrival` | 38 | 16 | 1840 | 25 | oui |
| `residual_sonority__to__consonant_scaffold__with__skip_or_leap_arrival` | 39 | 18 | 3022 | 25 | oui |
| `residual_sonority__to__other_named_sonority__with__repeated_bass` | 3 | 2 | 307 | 19 | oui |
| `residual_sonority__to__other_named_sonority__with__semitone_arrival` | 4 | 4 | 746 | 23 | oui |
| `residual_sonority__to__other_named_sonority__with__whole_tone_arrival` | 3 | 3 | 935 | 23 | oui |
| `residual_sonority__to__other_named_sonority__with__skip_or_leap_arrival` | 3 | 2 | 1971 | 25 | oui |
| `residual_sonority__to__residual_sonority__with__repeated_bass` | 0 | 0 | 1130 | 24 | oui |
| `residual_sonority__to__residual_sonority__with__semitone_arrival` | 2 | 2 | 1879 | 30 | oui |
| `residual_sonority__to__residual_sonority__with__whole_tone_arrival` | 15 | 12 | 4534 | 28 | oui |
| `residual_sonority__to__residual_sonority__with__skip_or_leap_arrival` | 6 | 4 | 7209 | 30 | oui |

Cellules éligibles : `36/36`.

L'audit ne charge ni génération ni résultat de validation et
n'ajuste aucun poids.
