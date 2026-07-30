# V6 — correction consensus multigraine, itération 3

Trois estimations indépendantes utilisent les mêmes 32 chorals de train,
deux chaînes par pièce et un budget fixe. Le test réservé n'est pas
chargé et la structure des 30 facteurs reste gelée.

## Diagnostic d'instabilité

- Cosinus des corrections presque non régularisées : `0.124, 0.361, 0.157`.
- Signes identiques sur les trois graines : `9/30`.

L'inversion sans régularisation est donc rejetée.

## Direction retenue

- Ridge sélectionné : `30.0`.
- Cosinus inter-graines après régularisation : `0.825, 0.922, 0.871`.
- Plus grand déplacement proposé : `0.029572`.
- Résidu standardisé restant, ensemble : `0.925`.

| Graine | Résidu restant | Amélioration projetée |
|---:|---:|---:|
| 10103 | 0.925 | 7.5 % |
| 20207 | 0.947 | 5.3 % |
| 30313 | 0.911 | 8.9 % |

## Correction par facteur

| Facteur | Delta consensus |
|---|---:|
| `LEARNED-001` | +0.022659 |
| `LEARNED-002` | +0.007583 |
| `LEARNED-003` | +0.002831 |
| `LEARNED-004` | -0.001605 |
| `LEARNED-005` | -0.000216 |
| `LEARNED-006` | +0.002002 |
| `LEARNED-007` | -0.004399 |
| `LEARNED-008` | +0.000289 |
| `LEARNED-009` | +0.007019 |
| `LEARNED-010` | +0.000388 |
| `LEARNED-011` | +0.001537 |
| `LEARNED-012` | -0.000806 |
| `LEARNED-013` | -0.000398 |
| `LEARNED-014` | -0.003802 |
| `LEARNED-015` | -0.005175 |
| `LEARNED-016` | -0.007372 |
| `LEARNED-017` | -0.001792 |
| `LEARNED-018` | -0.029572 |
| `LEARNED-019` | -0.000158 |
| `LEARNED-020` | -0.004957 |
| `LEARNED-021` | -0.001070 |
| `LEARNED-022` | +0.000754 |
| `LEARNED-023` | -0.003867 |
| `LEARNED-024` | +0.001285 |
| `LEARNED-025` | -0.000945 |
| `LEARNED-026` | -0.000350 |
| `LEARNED-027` | +0.002092 |
| `LEARNED-028` | -0.000512 |
| `LEARNED-029` | +0.001533 |
| `LEARNED-030` | -0.000948 |

Cette direction est apprise exclusivement sur train. Elle doit encore
passer l'audit génératif de développement ; une projection linéaire
positive n'est pas une preuve d'amélioration après rééchantillonnage.
