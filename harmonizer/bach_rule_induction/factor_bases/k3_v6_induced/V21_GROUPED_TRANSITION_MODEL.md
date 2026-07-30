# V21 — apprentissage conjoint du groupe de transitions

Les 288 transitions de fondamentales ne concourent plus comme des règles
individuelles. Elles forment une matrice apprise conjointement, avec
sommes nulles par ligne et colonne pour séparer interactions et
marginaux de départ/arrivée.

## Trajectoire de régularisation

| Candidat | λ groupe | NLL validation/pièce | e.s. | norme retenue | norme terminale | cellules |
|---|---:|---:|---:|---:|---:|---:|
| socle V20B réajusté | groupe absent | 0.820727 | 0.081510 | 0.000000 | 0.000000 | 0 | **← retenu**
| groupe λ=0.03 | 0.03 | 0.802765 | 0.083927 | 4.043573 | 4.043573 | 201 |
| groupe λ=0.01 | 0.01 | 0.802515 | 0.083996 | 4.131359 | 4.131359 | 203 |
| groupe λ=0.003 | 0.003 | 0.802431 | 0.084020 | 4.162724 | 4.162724 | 204 |
| groupe λ=0.001 | 0.001 | 0.802408 | 0.084027 | 4.171754 | 4.171754 | 204 |
| groupe λ=0.0003 | 0.0003 | 0.802400 | 0.084029 | 4.174921 | 4.174921 | 204 |
| groupe λ=0.0001 | 0.0001 | 0.802397 | 0.084030 | 4.175827 | 4.175827 | 204 |
| groupe λ=0 | 0 | 0.802396 | 0.084030 | 4.176280 | 4.176280 | 204 |

## Comparaisons appariées au socle

| Candidat | Gain moyen | e.s. appariée | IC bootstrap 95 % | Pièces améliorées |
|---|---:|---:|---:|---:|
| groupe λ=0.03 | +0.017962 | 0.006866 | [+0.006073, +0.031434] | 8/10 |
| groupe λ=0.01 | +0.018212 | 0.007037 | [+0.006046, +0.032106] | 8/10 |
| groupe λ=0.003 | +0.018296 | 0.007099 | [+0.005994, +0.032387] | 8/10 |
| groupe λ=0.001 | +0.018319 | 0.007117 | [+0.005944, +0.032350] | 8/10 |
| groupe λ=0.0003 | +0.018327 | 0.007124 | [+0.005914, +0.032342] | 8/10 |
| groupe λ=0.0001 | +0.018330 | 0.007125 | [+0.005904, +0.032330] | 8/10 |
| groupe λ=0 | +0.018331 | 0.007126 | [+0.005900, +0.032378] | 8/10 |

## Décision

- Meilleur candidat brut : `groupe λ=0`.
- Seuil à une erreur standard : `0.886427`.
- Candidat retenu : `socle V20B réajusté`.
- Groupe retenu : `false`.

Le modèle sans table de transitions reste dans l'intervalle
à une erreur standard du meilleur candidat. La sélection
groupée rejette donc la famille entière ; elle ne transforme
pas artificiellement les grands marginaux en règles.
