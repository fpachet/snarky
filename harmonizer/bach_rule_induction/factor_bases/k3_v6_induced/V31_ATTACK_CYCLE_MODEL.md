# V31 — induction des cycles de deux notes

Huit facteurs sont appris conjointement : premier retour `ABA` et
continuation `ABAB`, séparément pour chaque voix. L'historique ne
compte que les attaques ; les tenues sont exclues.

| Candidat | Gain découverte | IC 95 % | Pièces + |
|---|---:|---:|---:|
| socle V29 réajusté | — | — | — |
| groupe V31 cycles λ=0.6 | +0.000221 | [-0.001627, +0.001870] | 7/10 |
| groupe V31 cycles λ=0.3 | +0.000593 | [-0.001518, +0.002606] | 6/10 |
| groupe V31 cycles λ=0.1 | +0.000628 | [-0.001734, +0.002913] | 6/10 |
| groupe V31 cycles λ=0.03 | +0.000616 | [-0.001812, +0.002992] | 6/10 |
| groupe V31 cycles λ=0 | +0.000607 | [-0.001847, +0.002995] | 6/10 |

- Sélection découverte : `socle V29 réajusté`.
- Groupe retenu : `false`.
- Confirmation 40 pièces : `+0.002307` ; IC 95 % `[+0.001139, +0.003432]` ; `28/40` pièces.

| Statut | Poids |
|---|---:|
| `soprano__first_aba_return` | +0.000000 |
| `soprano__continued_abab_cycle` | +0.000000 |
| `alto__first_aba_return` | +0.004968 |
| `alto__continued_abab_cycle` | -0.405959 |
| `tenor__first_aba_return` | -0.066566 |
| `tenor__continued_abab_cycle` | -0.160174 |
| `bass__first_aba_return` | -0.342703 |
| `bass__continued_abab_cycle` | -0.199513 |
