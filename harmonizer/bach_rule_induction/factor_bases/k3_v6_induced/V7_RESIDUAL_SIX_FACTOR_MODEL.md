# V7 — six facteurs résiduels, socle V6 gelé

V7 ajoute exactement deux facteurs par famille résiduelle : un gradient
positif et un gradient négatif. Les 30 facteurs V6, leurs poids, les
baselines de registre et de tonalité restent inchangés.

## Facteurs ajoutés

| Facteur | Famille | Description | Poids appris |
|---|---|---|---:|
| `F-K3-V7-001` | `bass_motion` | basse : classe d'intervalle entrant 2 | +0.230894 |
| `F-K3-V7-002` | `bass_motion` | basse : saut entrant supérieur à 2 demi-tons | -0.223823 |
| `F-K3-V7-003` | `vertical_context` | intervalle vertical 7 présent sur bloc métrique fort | +0.222403 |
| `F-K3-V7-004` | `vertical_context` | intervalle vertical 8 présent sur bloc métrique faible | -0.206842 |
| `F-K3-V7-005` | `sonority_transition` | transition {0, 4, 7} → {0, 4, 7, 10} | +0.238808 |
| `F-K3-V7-006` | `sonority_transition` | transition {0, 3, 6, 8} → {0, 3, 6, 8} | -0.203623 |

## Apprentissage train

- MAE des six moments : `0.045283` → `0.005009`.
- NLL conditionnelle validation : `1.241166` → `1.225843`.
- Époque retenue : `6`.

Le modèle reste candidat jusqu'aux audits génératifs appariés à 6 et
30 sweeps. Le test réservé n'est pas chargé.
