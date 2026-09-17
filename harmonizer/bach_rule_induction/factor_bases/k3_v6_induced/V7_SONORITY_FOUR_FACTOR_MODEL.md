# V7-Sonority — ablation de la famille basse

Les deux facteurs `bass_motion` de V7 sont retirés après leur
surcorrection significative des grands sauts aux horizons 6 et 30.
Les 30 facteurs V6 et les quatre facteurs métriques/de transition
conservent exactement leurs poids.

- Facteurs retirés : `['F-K3-V7-001', 'F-K3-V7-002']`.
- Facteurs V7 conservés : `['F-K3-V7-003', 'F-K3-V7-004', 'F-K3-V7-005', 'F-K3-V7-006']`.
- NLL conditionnelle validation : `1.225843` → `1.241364`.

Ce modèle reste candidat jusqu'aux audits génératifs à 6 et 30 sweeps.
