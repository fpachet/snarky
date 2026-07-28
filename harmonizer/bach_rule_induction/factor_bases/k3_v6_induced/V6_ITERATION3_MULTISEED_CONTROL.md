# V6 — correction consensus multigraine, itération 3

Trois estimations indépendantes utilisent les mêmes 32 chorals de train,
deux chaînes par pièce et un budget fixe. Le test réservé n'est pas
chargé et la structure des 30 facteurs reste gelée.

## Diagnostic d'instabilité

- Cosinus des corrections presque non régularisées : `0.473, 0.199, 0.468`.
- Signes identiques sur les trois graines : `13/30`.

L'inversion sans régularisation est donc rejetée.

## Direction retenue

- Ridge sélectionné : `1.0`.
- Cosinus inter-graines après régularisation : `0.847, 0.801, 0.927`.
- Plus grand déplacement proposé : `0.039832`.
- Résidu standardisé restant, ensemble : `0.534`.

| Graine | Résidu restant | Amélioration projetée |
|---:|---:|---:|
| 10103 | 0.718 | 28.2 % |
| 20207 | 0.426 | 57.4 % |
| 30313 | 0.604 | 39.6 % |

## Correction par facteur

| Facteur | Delta consensus |
|---|---:|
| `F-K3-V6-001` | -0.008071 |
| `F-K3-V6-002` | +0.011138 |
| `F-K3-V6-003` | +0.011812 |
| `F-K3-V6-004` | +0.006695 |
| `F-K3-V6-005` | -0.039832 |
| `F-K3-V6-006` | +0.021618 |
| `F-K3-V6-007` | -0.008738 |
| `F-K3-V6-008` | -0.025227 |
| `F-K3-V6-009` | -0.005425 |
| `F-K3-V6-010` | +0.000826 |
| `F-K3-V6-011` | -0.009530 |
| `F-K3-V6-012` | +0.001876 |
| `F-K3-V6-013` | -0.005781 |
| `F-K3-V6-014` | -0.009025 |
| `F-K3-V6-015` | -0.000476 |
| `F-K3-V6-016` | +0.001236 |
| `F-K3-V6-017` | +0.018184 |
| `F-K3-V6-018` | +0.000484 |
| `F-K3-V6-019` | +0.017324 |
| `F-K3-V6-020` | -0.027936 |
| `F-K3-V6-021` | -0.000897 |
| `F-K3-V6-022` | +0.000983 |
| `F-K3-V6-023` | -0.002538 |
| `F-K3-V6-024` | -0.000880 |
| `F-K3-V6-025` | -0.006569 |
| `F-K3-V6-026` | -0.005685 |
| `F-K3-V6-027` | -0.000946 |
| `F-K3-V6-028` | +0.000766 |
| `F-K3-V6-029` | +0.003562 |
| `F-K3-V6-030` | +0.000435 |

Cette direction est apprise exclusivement sur train. Elle doit encore
passer l'audit génératif de développement ; une projection linéaire
positive n'est pas une preuve d'amélioration après rééchantillonnage.
