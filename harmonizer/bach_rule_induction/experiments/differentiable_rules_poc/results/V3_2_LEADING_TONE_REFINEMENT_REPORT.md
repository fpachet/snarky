# POC V3.2 — raffinements de la résolution de la sensible

## Protocole

- Prémisse fixe : classe source relative à la tonique `11`.
- Conclusion : mouvement ascendant exact d'un demi-ton.
- Contextes énumérés : voix × classe de basse source × classe de basse cible.
- 432 contextes numériques testés uniformément.
- Le test final reste scellé.
- Chorals authentiques.

## Raffinements retenus

| Mode | Voix | Basse | Support train/val. | Confirmation train/val. | z train/val. | Bootstrap val. médian [95 %] | Interprétation |
|---|---|---|---:|---:|---:|---:|---|
| all | Alto | 2→0 | 92/28 | 0.902/0.964 | 6.686/4.429 | 4.384 [3.016 ; 5.721] | `LEADING_TONE_CHORD_6_TO_TONIC_ROOT_PROXY` |
| ↳ audit | — | — | — | — | — | — | major: train 34/43, val. 15/16; minor: train 49/49, val. 12/12 |
| all | Alto | 2→4 | 56/19 | 0.875/1.000 | 12.367/8.050 | 7.984 [5.221 ; 10.460] | `LEADING_TONE_CHORD_6_TO_TONIC_6_PROXY` |
| ↳ audit | — | — | — | — | — | — | major: train 47/54, val. 19/19; minor: train 2/2, val. 0/0 |
| all | Tenor | 7→8 | 33/13 | 0.758/0.846 | 3.568/2.305 | 2.253 [0.418 ; 3.536] | `UNINTERPRETED_NUMERIC_REFINEMENT` |
| ↳ audit | — | — | — | — | — | — | major: train 0/8, val. 0/2; minor: train 25/25, val. 11/11 |
| all | Soprano | 7→0 | 123/25 | 0.724/0.880 | 7.236/4.214 | 4.237 [1.945 ; 5.953] | `OUTER_DOMINANT_TO_TONIC_CADENTIAL_PROXY` |
| ↳ audit | — | — | — | — | — | — | major: train 57/89, val. 11/14; minor: train 32/34, val. 11/11 |

Ces résultats restent des raffinements candidats malgré le contrôle
nul et l'audit des exemples. Une calibration familiale répétée et
une analyse harmonique indépendante précèdent le statut `SUPPORTED`.
