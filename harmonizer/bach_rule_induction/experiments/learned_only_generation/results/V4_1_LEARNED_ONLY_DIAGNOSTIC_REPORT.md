# V4.1 — Génération diagnostique `S-LEARNED`

## Protocole

- cinq fragments de quatre attaques, pris dans le `train` ;
- deux graines enregistrées par fragment ;
- soprano et tonalité globale donnés ;
- domaines des voix inférieures issus des fréquences du `train` ;
- sept règles apprises, aucune règle historique ;
- toutes les sorties conservées.

Cette campagne est exploratoire. Les poids joints de niveau A sont une
projection des poids V2.4, pas un réajustement confirmatoire.

## Résumé

- générations : `10` ;
- croisements verticaux : `3` ;
- unissons de voix adjacentes : `7` ;
- espacements soprano–alto ou alto–ténor > octave : `2` ;
- espacements ténor–basse > 19 demi-tons : `0` ;
- sonorités avec moins de trois classes : `7` ;
- activations apprises : `5`.

Activations par règle :

- `R-LEARNED-OVERLAP-001` : `5`

## Sorties

| Pièce | Graine | Soprano | Alto | Ténor | Basse | Activations |
|---|---:|---|---|---|---|---:|
| `bach/bwv10.7` | 0 | `74 77 74 74` | `67 66 62 67` | `59 59 59 60` | `52 50 55 48` | 0 |
| `bach/bwv10.7` | 1 | `74 77 74 74` | `62 64 62 62` | `60 59 59 62` | `48 55 55 50` | 0 |
| `bach/bwv101.7` | 0 | `69 69 65 67` | `67 66 62 67` | `59 59 59 57` | `52 50 55 55` | 2 |
| `bach/bwv101.7` | 1 | `69 69 65 67` | `62 64 62 62` | `60 59 59 60` | `48 55 55 50` | 0 |
| `bach/bwv104.6` | 0 | `69 71 73 74` | `67 66 62 67` | `59 59 59 60` | `52 50 55 48` | 0 |
| `bach/bwv104.6` | 1 | `69 71 73 74` | `62 66 62 62` | `60 57 59 62` | `48 48 55 50` | 0 |
| `bach/bwv108.6` | 0 | `71 71 71 78` | `67 66 62 67` | `59 59 59 60` | `52 50 55 48` | 0 |
| `bach/bwv108.6` | 1 | `71 71 71 78` | `62 64 62 62` | `60 59 59 62` | `48 55 55 50` | 0 |
| `bach/bwv11.6` | 0 | `62 62 64 66` | `67 66 62 67` | `59 59 59 57` | `52 50 55 55` | 3 |
| `bach/bwv11.6` | 1 | `62 62 64 66` | `62 62 62 62` | `60 62 57 60` | `48 52 55 55` | 0 |

## Lecture

Le succès technique attendu est l'existence de sorties traçables sous
`S-LEARNED`. Les croisements, unissons et autres défauts ne sont pas
corrigés après coup : ils désignent les prochaines familles à induire.
