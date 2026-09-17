# POC V3.4 — calibration familiale des règles tonales

## Protocole

- 49 permutations indépendantes, avec réajustement complet de la baseline à chaque réplication.
- Famille : 864 clauses mode × voix × basse source × basse cible.
- Statistique : `min(z train, z validation)`.
- Maximum calculé parmi toutes les clauses qui passent les seuils de support, avant les seuils de confirmation et de z.
- p empirique corrigé famille : `(1 + dépassements) / (1 + B)`.
- Le test final reste scellé.

## Distribution du maximum sous le nul

| Maxima définis | Médiane | q90 | q95 | Maximum observé |
|---:|---:|---:|---:|---:|
| 49/49 | 3.611 | 4.613 | 4.817 | 6.205 |

## Candidats authentiques

| Mode | Voix | Basse | min-z | Dépassements/B | p FWER | Statut |
|---|---|---:|---:|---:|---:|---|
| major | Alto | 2→4 | 8.050 | 0/49 | 0.0200 | `PASSES_EMPIRICAL_FWER_0_05` |
| minor | Alto | 7→3 | 4.379 | 8/49 | 0.1800 | `DOES_NOT_PASS_EMPIRICAL_FWER_0_05` |
| major | Alto | 2→0 | 3.479 | 30/49 | 0.6200 | `DOES_NOT_PASS_EMPIRICAL_FWER_0_05` |
| major | Tenor | 5→4 | 3.136 | 35/49 | 0.7200 | `DOES_NOT_PASS_EMPIRICAL_FWER_0_05` |
| minor | Soprano | 7→0 | 2.898 | 39/49 | 0.8000 | `DOES_NOT_PASS_EMPIRICAL_FWER_0_05` |
| minor | Alto | 2→0 | 2.745 | 42/49 | 0.8600 | `DOES_NOT_PASS_EMPIRICAL_FWER_0_05` |
| minor | Tenor | 7→8 | 2.683 | 44/49 | 0.9000 | `DOES_NOT_PASS_EMPIRICAL_FWER_0_05` |

## Interprétation

La résolution empirique minimale est ici de `0,02`. Une seule
clause passe le seuil familial de 5 % ; les autres restent des
hypothèses descriptives, non des règles statistiquement retenues.

Le contrôle porte sur le meilleur résultat recherché dans la famille
entière, et non sur chaque clause considérée isolément.
