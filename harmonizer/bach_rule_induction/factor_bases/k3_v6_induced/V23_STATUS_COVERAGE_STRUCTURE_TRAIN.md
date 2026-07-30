# V23 — couverture structure-train des deux groupes

Cet audit est antérieur à l'apprentissage. Il ne consulte ni le signe
d'un effet, ni la NLL de validation : il vérifie seulement qu'un facteur
peut changer entre le choix authentique et ses alternatives exactes.

- Décisions : `7273` sur `32` chorals.
- Seuil descriptif : `100` opportunités et `10` chorals.

## `bass_tonal_strong_mode`

- Cellules : `24`.
- Cellules franchissant le seuil : `24/24`.

| Statut | Opportunités | Chorals possibles | Activations Bach | Chorals Bach | Seuil |
|---|---:|---:|---:|---:|:---:|
| basse temps fort, mode majeur, degré I | 402 | 12 | 748 | 12 | oui |
| basse temps fort, mode majeur, degré ♭II | 445 | 12 | 16 | 2 | oui |
| basse temps fort, mode majeur, degré II | 428 | 12 | 297 | 11 | oui |
| basse temps fort, mode majeur, degré ♭III | 445 | 12 | 17 | 2 | oui |
| basse temps fort, mode majeur, degré III | 433 | 12 | 512 | 11 | oui |
| basse temps fort, mode majeur, degré IV | 430 | 12 | 406 | 11 | oui |
| basse temps fort, mode majeur, degré ♯IV | 444 | 12 | 130 | 7 | oui |
| basse temps fort, mode majeur, degré V | 416 | 12 | 639 | 12 | oui |
| basse temps fort, mode majeur, degré ♭VI | 444 | 12 | 29 | 3 | oui |
| basse temps fort, mode majeur, degré VI | 425 | 12 | 387 | 12 | oui |
| basse temps fort, mode majeur, degré ♭VII | 443 | 12 | 40 | 4 | oui |
| basse temps fort, mode majeur, degré VII | 437 | 12 | 170 | 8 | oui |
| basse temps fort, mode mineur, degré I | 549 | 20 | 1019 | 20 | oui |
| basse temps fort, mode mineur, degré ♭II | 585 | 20 | 83 | 5 | oui |
| basse temps fort, mode mineur, degré II | 576 | 20 | 262 | 16 | oui |
| basse temps fort, mode mineur, degré ♭III | 553 | 20 | 647 | 18 | oui |
| basse temps fort, mode mineur, degré III | 585 | 20 | 36 | 5 | oui |
| basse temps fort, mode mineur, degré IV | 570 | 20 | 595 | 19 | oui |
| basse temps fort, mode mineur, degré ♯IV | 585 | 20 | 42 | 3 | oui |
| basse temps fort, mode mineur, degré V | 565 | 20 | 727 | 19 | oui |
| basse temps fort, mode mineur, degré ♭VI | 573 | 20 | 450 | 17 | oui |
| basse temps fort, mode mineur, degré VI | 575 | 20 | 123 | 7 | oui |
| basse temps fort, mode mineur, degré ♭VII | 574 | 20 | 431 | 19 | oui |
| basse temps fort, mode mineur, degré VII | 574 | 20 | 98 | 8 | oui |

## `unique_chord_family_inversion_strong`

- Cellules : `14`.
- Cellules franchissant le seuil : `14/14`.

| Statut | Opportunités | Chorals possibles | Activations Bach | Chorals Bach | Seuil |
|---|---:|---:|---:|---:|:---:|
| triades majeures/mineures, fondamentale | 1562 | 32 | 3621 | 32 | oui |
| triades majeures/mineures, premier renversement | 1557 | 32 | 1251 | 32 | oui |
| triades majeures/mineures, deuxième renversement | 854 | 32 | 157 | 12 | oui |
| triades diminuées/augmentées, fondamentale | 419 | 32 | 27 | 1 | oui |
| triades diminuées/augmentées, premier renversement | 420 | 32 | 149 | 11 | oui |
| triades diminuées/augmentées, deuxième renversement | 175 | 32 | 6 | 1 | oui |
| septièmes dominante/majeure/mineure, fondamentale | 1094 | 32 | 150 | 13 | oui |
| septièmes dominante/majeure/mineure, premier renversement | 798 | 32 | 414 | 17 | oui |
| septièmes dominante/majeure/mineure, deuxième renversement | 329 | 32 | 8 | 1 | oui |
| septièmes dominante/majeure/mineure, troisième renversement | 615 | 32 | 112 | 7 | oui |
| septièmes altérées, fondamentale | 461 | 32 | 52 | 5 | oui |
| septièmes altérées, premier renversement | 366 | 32 | 197 | 15 | oui |
| septièmes altérées, deuxième renversement | 138 | 30 | 12 | 1 | oui |
| septièmes altérées, troisième renversement | 276 | 31 | 45 | 5 | oui |

Une cellule rare n'est pas supprimée parce que son poids semble faible
ou défavorable. La décision de factorisation doit porter sur un schéma
entier et être prise avant l'ajustement des poids.
