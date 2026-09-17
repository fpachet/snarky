# V7 — 4 facteurs résiduels, socle V6 gelé

V7 ajoute deux facteurs par famille résiduelle retenue : un gradient
positif et un gradient négatif. Les 30 facteurs V6, leurs poids, les
baselines de registre et de tonalité restent inchangés.

## Facteurs ajoutés

| Facteur | Famille | Description | Poids appris |
|---|---|---|---:|
| `F-K3-V7-001` | `vertical_context` | intervalle vertical 7 présent sur bloc métrique fort | +0.247661 |
| `F-K3-V7-002` | `vertical_context` | intervalle vertical 8 présent sur bloc métrique faible | -0.242220 |
| `F-K3-V7-003` | `sonority_transition` | transition {0, 4, 7} → {0, 4, 7, 10} | +0.313348 |
| `F-K3-V7-004` | `sonority_transition` | transition {0, 3, 6, 8} → {0, 3, 6, 8} | -0.164732 |

## Apprentissage train

- MAE des six moments : `0.019144` → `0.005749`.
- NLL conditionnelle validation : `1.241166` → `1.241741`.
- Époque retenue : `8`.

Le modèle reste candidat jusqu'aux audits génératifs appariés à 6 et
30 sweeps. Le test réservé n'est pas chargé.
