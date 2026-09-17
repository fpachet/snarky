# V5.16 — interpolation tenue à part des corrections de basse

V5.14 sous-corrigeait le mouvement de basse et V5.15 le surcorrigeait.
Le facteur `0,5` a été choisi sur les dix premiers chorals de validation
utilisés comme développement. Les dix suivants restent tenus à part pour
la confirmation. Le test scellé reste fermé.

Seuls les quatre deltas V5.15 sont interpolés ;
le socle harmonique V5.14 est inchangé.

| Correction | Delta V5.15 | Delta V5.16 |
|---|---:|---:|
| saut de basse supérieur à 4 demi-tons | +0.4658 | +0.2329 |
| saut de basse supérieur à 2 demi-tons | +0.4614 | +0.2307 |
| classe d'intervalle entrant 1 à la basse | -0.4534 | -0.2267 |
| directions K3 de basse (-1, +0) | -0.4754 | -0.2377 |

NLL conditionnelle de validation après interpolation : `1.153861`.

Cette interpolation est un hyperparamètre de calibration générative,
pas une nouvelle règle musicale. Les deltas devront être fusionnés
avec les poids des clauses identiques dans la base finale.
