# V6 — correction consensus multigraine, itération 3

Trois estimations indépendantes utilisent les mêmes 32 chorals de train,
deux chaînes par pièce et un budget fixe. Le test réservé n'est pas
chargé et la structure des 30 facteurs reste gelée.

## Diagnostic d'instabilité

- Cosinus des corrections presque non régularisées : `-0.228, -0.022, 0.496`.
- Signes identiques sur les trois graines : `7/30`.

L'inversion sans régularisation est donc rejetée.

## Direction retenue

- Ridge sélectionné : `10.0`.
- Cosinus inter-graines après régularisation : `0.848, 0.907, 0.944`.
- Plus grand déplacement proposé : `0.054689`.
- Résidu standardisé restant, ensemble : `0.788`.

| Graine | Résidu restant | Amélioration projetée |
|---:|---:|---:|
| 10103 | 0.834 | 16.6 % |
| 20207 | 0.744 | 25.6 % |
| 30313 | 0.796 | 20.4 % |

## Correction par facteur

| Facteur | Delta consensus |
|---|---:|
| `LEARNED-001` | +0.030356 |
| `LEARNED-002` | +0.016051 |
| `LEARNED-003` | +0.004644 |
| `LEARNED-004` | -0.005799 |
| `LEARNED-005` | +0.002824 |
| `LEARNED-006` | -0.008945 |
| `LEARNED-007` | -0.003677 |
| `LEARNED-008` | +0.008940 |
| `LEARNED-009` | +0.001776 |
| `LEARNED-010` | +0.003894 |
| `LEARNED-011` | -0.000548 |
| `LEARNED-012` | -0.000556 |
| `LEARNED-013` | -0.006918 |
| `LEARNED-014` | -0.001777 |
| `LEARNED-015` | -0.054689 |
| `LEARNED-016` | -0.003461 |
| `LEARNED-017` | -0.012325 |
| `LEARNED-018` | -0.007111 |
| `LEARNED-019` | -0.003675 |
| `LEARNED-020` | -0.002121 |
| `LEARNED-021` | -0.017559 |
| `LEARNED-022` | +0.020223 |
| `LEARNED-023` | -0.003668 |
| `LEARNED-024` | -0.001836 |
| `LEARNED-025` | -0.004220 |
| `LEARNED-026` | +0.000378 |
| `LEARNED-027` | -0.000041 |
| `LEARNED-028` | -0.000857 |
| `LEARNED-029` | +0.000342 |
| `LEARNED-030` | +0.000457 |

Cette direction est apprise exclusivement sur train. Elle doit encore
passer l'audit génératif de développement ; une projection linéaire
positive n'est pas une preuve d'amélioration après rééchantillonnage.
