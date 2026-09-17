# V5.10 — audit résiduel des licences chromatiques

Après gel des huit pénalités V5.9, les statuts non sélectionnés sont
réévalués sur 16 chorals du train avec de nouvelles chaînes Gibbs.
Le test et la validation ne sont pas consultés.

Un gradient positif signifie que Bach emploie le statut davantage que le
Gibbs : il s'agit d'une licence positive candidate.

## Plus forts gradients positifs

| Statut | Bach | Gibbs | Gradient | z |
|---|---:|---:|---:|---:|
| broderie immédiate, Alto, majeur | 0.553 % | 0.145 % | +0.409 pp | +1.80 |
| empreinte verticale [0, 3, 6, 9], Alto, majeur | 0.405 % | 0.070 % | +0.335 pp | +1.82 |
| arrivée sans pas, Alto, mineur | 0.293 % | 0.000 % | +0.293 pp | +1.39 |
| note courte sans résolution, Tenor, mineur | 0.625 % | 0.324 % | +0.301 pp | +0.89 |
| empreinte verticale [0, 3, 6, 9], Bass, mineur | 0.231 % | 0.000 % | +0.231 pp | +1.00 |
| empreinte verticale [0, 3, 6, 9], Tenor, majeur | 0.381 % | 0.170 % | +0.210 pp | +1.02 |
| empreinte verticale [0, 3, 9], Alto, mineur | 0.394 % | 0.192 % | +0.202 pp | +1.00 |
| arrivée sans pas, Tenor, majeur | 0.416 % | 0.229 % | +0.187 pp | +0.78 |
| empreinte verticale [0, 4, 7, 10], Tenor, majeur | 0.306 % | 0.124 % | +0.182 pp | +0.99 |
| empreinte verticale [0, 2, 6, 9], Tenor, mineur | 0.108 % | 0.000 % | +0.108 pp | +1.00 |
| empreinte verticale [0, 3, 6, 9], Tenor, mineur | 0.216 % | 0.070 % | +0.145 pp | +0.63 |
| empreinte verticale [0, 2, 6, 9], Bass, majeur | 0.087 % | 0.000 % | +0.087 pp | +1.00 |

## Plus forts gradients négatifs

| Statut | Bach | Gibbs | Gradient | z |
|---|---:|---:|---:|---:|
| classe rare, Tenor, mineur | 2.141 % | 4.822 % | -2.682 pp | -2.36 |
| classe rare, Tenor, majeur | 2.170 % | 4.475 % | -2.305 pp | -1.96 |
| approche par pas, Tenor, mineur | 1.788 % | 4.306 % | -2.518 pp | -2.25 |
| approche par pas, Tenor, majeur | 1.754 % | 4.246 % | -2.492 pp | -2.11 |
| résolution immédiate par pas, Tenor, mineur | 1.014 % | 2.652 % | -1.638 pp | -2.70 |
| niveau métrique faible, Tenor, mineur | 0.904 % | 2.228 % | -1.324 pp | -2.35 |
| niveau métrique fort, Bass, majeur | 0.241 % | 1.313 % | -1.071 pp | -2.88 |
| résolution immédiate par pas, Tenor, majeur | 1.421 % | 2.900 % | -1.479 pp | -1.85 |
| niveau métrique fort, Tenor, mineur | 1.237 % | 2.595 % | -1.358 pp | -2.01 |
| niveau métrique fort, Tenor, majeur | 0.320 % | 1.460 % | -1.140 pp | -2.35 |
| empreinte verticale [0, 3, 6, 8], Bass, majeur | 0.328 % | 1.616 % | -1.287 pp | -2.76 |
| empreinte verticale [0, 3, 6, 8], Bass, mineur | 0.276 % | 1.510 % | -1.234 pp | -2.67 |

## Décision

Aucune licence positive n'est assez stable, même parmi les `22` interactions avec une empreinte verticale relative à la basse. La prochaine feature doit être un statut tonal local latent sur les trois blocs, et non une nouvelle pénalisation chromatique.
