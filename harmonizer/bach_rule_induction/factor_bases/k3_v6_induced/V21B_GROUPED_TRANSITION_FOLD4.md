# V21 — apprentissage conjoint du groupe de transitions

Les 288 transitions de fondamentales ne concourent plus comme des règles
individuelles. Elles forment une matrice apprise conjointement, avec
sommes nulles par ligne et colonne pour séparer interactions et
marginaux de départ/arrivée.

## Trajectoire de régularisation

| Candidat | λ groupe | NLL validation/pièce | e.s. | norme retenue | norme terminale | cellules |
|---|---:|---:|---:|---:|---:|---:|
| socle V20B réajusté | groupe absent | 0.858279 | 0.040635 | 0.000000 | 0.000000 | 0 | **← retenu**
| groupe λ=0.03 | 0.03 | 0.858279 | 0.040635 | 0.000000 | 4.390147 | 0 |

## Comparaisons appariées au socle

| Candidat | Gain moyen | e.s. appariée | IC bootstrap 95 % | Pièces améliorées |
|---|---:|---:|---:|---:|
| groupe λ=0.03 | +0.000000 | 0.000000 | [+0.000000, +0.000000] | 0/8 |

## Décision

- Meilleur candidat brut : `socle V20B réajusté`.
- Seuil à une erreur standard : `0.898914`.
- Candidat retenu : `socle V20B réajusté`.
- Groupe retenu : `false`.

Le modèle sans table de transitions reste dans l'intervalle
à une erreur standard du meilleur candidat. La sélection
groupée rejette donc la famille entière ; elle ne transforme
pas artificiellement les grands marginaux en règles.
