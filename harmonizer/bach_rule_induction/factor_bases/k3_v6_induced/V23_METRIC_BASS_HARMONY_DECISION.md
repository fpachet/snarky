# V23 — décision sur les groupes basse métrique et harmonie

V23 teste deux ajouts interprétables à V22 : 14 statuts d'accord
nommé unique sur temps fort, puis 24 déviations tonales de basse sur
temps fort. Les variantes et λ=0,6 ont été gelés avant les quatre plis.

## Réplication

| Variante | Gain folds | IC 95 % | Chorals + | Gain 251/50 | IC 95 % | Chorals + |
|---|---:|---:|---:|---:|---:|---:|
| Harmonie seule | +0.002724 | [+0.000814, +0.004597] | 24/32 | +0.003276 | [+0.001885, +0.004723] | 38/50 |
| Basse + harmonie | +0.002921 | [+0.000884, +0.004874] | 23/32 | +0.003366 | [+0.001905, +0.004882] | 35/50 |

## Décision

- Le groupe harmonique est retenu : son gain est positif dans chacun
  des quatre plis et nettement positif sur les 50 chorals.
- L'ajout des 24 poids de basse à l'harmonie ne gagne que `+0.000089` sur les 50 chorals, IC 95 % `[-0.000337, +0.000522]`.
- Par parcimonie, V23 retient donc **harmonie seule** : 14 paramètres
  supplémentaires au lieu de 38.

## Poids harmoniques retenus

Un poids positif favorise ce statut par rapport à l'absence d'un accord
nommé unique ; un poids négatif le défavorise. Ils ne sont pas des
probabilités isolées.

| Statut sur temps fort | Poids |
|---|---:|
| triades majeures/mineures, fondamentale | +0.2808 |
| triades majeures/mineures, 1er renversement | +0.1407 |
| triades majeures/mineures, 2e renversement | -0.0526 |
| triades diminuées/augmentées, fondamentale | -0.1016 |
| triades diminuées/augmentées, 1er renversement | -0.2083 |
| triades diminuées/augmentées, 2e renversement | -0.2286 |
| 7es dominante/majeure/mineure, fondamentale | -0.0060 |
| 7es dominante/majeure/mineure, 1er renversement | -0.0701 |
| 7es dominante/majeure/mineure, 2e renversement | -0.2656 |
| 7es dominante/majeure/mineure, 3e renversement | +0.2739 |
| 7es altérées, fondamentale | -0.1757 |
| 7es altérées, 1er renversement | +0.2246 |
| 7es altérées, 2e renversement | -0.1471 |
| 7es altérées, 3e renversement | +0.2409 |

La chromaticité de basse reste donc un problème distinct : cette
première factorisation métrique de 24 degrés n'apporte pas assez
d'information au-delà de V22 pour être conservée.
