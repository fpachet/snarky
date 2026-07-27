# POC V3.3 — raffinements de la résolution de la sensible

## Protocole

- Prémisse fixe : classe source relative à la tonique `11`.
- Conclusion : mouvement ascendant exact d'un demi-ton.
- Contextes énumérés : mode × voix × classe de basse source × classe de basse cible.
- 864 contextes numériques testés uniformément.
- Le test final reste scellé.
- Chorals authentiques.

## Raffinements retenus

| Mode | Voix | Basse | Support train/val. | Confirmation train/val. | z train/val. | Bootstrap val. médian [95 %] | Interprétation |
|---|---|---|---:|---:|---:|---:|---|
| minor | Alto | 2→0 | 49/12 | 1.000/1.000 | 5.615/2.745 | 2.740 [1.577 ; 3.727] | `LEADING_TONE_CHORD_6_TO_TONIC_ROOT_PROXY` |
| ↳ audit | — | — | — | — | — | — | minor: train 49/49, val. 12/12 |
| minor | Tenor | 7→8 | 25/11 | 1.000/1.000 | 4.165/2.683 | 2.610 [1.278 ; 3.774] | `MINOR_DECEPTIVE_CADENCE_PROXY` |
| ↳ audit | — | — | — | — | — | — | minor: train 25/25, val. 11/11 |
| minor | Soprano | 7→0 | 34/11 | 0.941/1.000 | 4.785/2.898 | 2.861 [1.648 ; 3.939] | `OUTER_DOMINANT_TO_TONIC_CADENTIAL_PROXY` |
| ↳ audit | — | — | — | — | — | — | minor: train 32/34, val. 11/11 |
| major | Tenor | 5→4 | 26/10 | 0.923/0.900 | 6.462/3.136 | 3.141 [0.957 ; 4.945] | `DOMINANT_SEVENTH_42_TO_TONIC_6_PROXY` |
| ↳ audit | — | — | — | — | — | — | major: train 24/26, val. 9/10 |
| major | Alto | 2→4 | 54/19 | 0.870/1.000 | 12.228/8.050 | 8.001 [5.364 ; 10.432] | `LEADING_TONE_CHORD_6_TO_TONIC_6_PROXY` |
| ↳ audit | — | — | — | — | — | — | major: train 47/54, val. 19/19 |
| major | Alto | 2→0 | 43/16 | 0.791/0.938 | 3.811/3.479 | 3.517 [1.780 ; 5.106] | `LEADING_TONE_CHORD_6_TO_TONIC_ROOT_PROXY` |
| ↳ audit | — | — | — | — | — | — | major: train 34/43, val. 15/16 |
| minor | Alto | 7→3 | 28/8 | 0.679/0.750 | 6.864/4.379 | 4.368 [-0.768 ; 8.332] | `MINOR_DOMINANT_TO_MEDIANT_DECEPTIVE_PROXY` |
| ↳ audit | — | — | — | — | — | — | minor: train 19/28, val. 6/8 |

Ces résultats restent des raffinements candidats malgré le contrôle
nul et l'audit des exemples. Une calibration familiale répétée et
une analyse harmonique indépendante précèdent le statut `SUPPORTED`.
