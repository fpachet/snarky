# K3-V22C-SHARED-ROOT-MOTION-FULL-1 — apprentissage conjoint d'un RuleGroup

Les 24 cellules du groupe
`named_root_motion_mode` sont apprises simultanément plutôt que
mises en concurrence comme des règles indépendantes. La projection
d'identifiabilité est appliquée après chaque pas proximal.

## Trajectoire de régularisation

| Candidat | λ groupe | NLL validation/pièce | e.s. | norme retenue | norme terminale | cellules |
|---|---:|---:|---:|---:|---:|---:|
| socle V20B réajusté | groupe absent | 0.829956 | 0.024913 | 0.000000 | 0.000000 | 0 |
| groupe λ=0.3 | 0.3 | 0.808481 | 0.025207 | 1.580026 | 1.580026 | 24 | **← retenu**

## Comparaisons appariées au socle

| Candidat | Gain moyen | e.s. appariée | IC bootstrap 95 % | Pièces améliorées |
|---|---:|---:|---:|---:|
| groupe λ=0.3 | +0.021475 | 0.001993 | [+0.017585, +0.025329] | 46/50 |

## Décision

- Meilleur candidat brut : `groupe λ=0.3`.
- Sélection : IC bootstrap apparié strictement positif.
- Candidat retenu : `groupe λ=0.3`.
- Groupe retenu : `true`.

Le groupe apporte collectivement assez d'information pour
survivre au critère à une erreur standard. Les coefficients
extrêmes ci-dessous restent des cellules d'une même règle
structurée, et non 288 règles autonomes.

### Interactions positives les plus fortes

| Mode | Cas partagé | Poids |
|---|---:|---:|
| major | quarte ascendante / quinte descendante | +0.427073 |
| minor | quarte ascendante / quinte descendante | +0.377034 |
| major | triton | +0.375683 |
| minor | triton | +0.346178 |
| major | seconde mineure ascendante | +0.337091 |
| major | seconde majeure ascendante | +0.324748 |
| minor | seconde majeure ascendante | +0.305631 |
| major | tierce mineure descendante | +0.282766 |
| minor | seconde mineure ascendante | +0.272321 |
| minor | quinte ascendante / quarte descendante | +0.245549 |
| major | quinte ascendante / quarte descendante | +0.227959 |
| minor | tierce mineure descendante | +0.133050 |

### Interactions négatives les plus fortes

| Mode | Cas partagé | Poids |
|---|---:|---:|
| major | seconde mineure descendante | -0.491773 |
| minor | seconde mineure descendante | -0.482313 |
| minor | seconde majeure descendante | -0.428157 |
| minor | tierce majeure descendante | -0.396743 |
| major | seconde majeure descendante | -0.353396 |
| major | tierce majeure descendante | -0.337710 |
| major | tierce mineure ascendante | -0.287689 |
| major | maintien | -0.256061 |
| major | tierce majeure ascendante | -0.248693 |
| minor | maintien | -0.150338 |
| minor | tierce mineure ascendante | -0.148410 |
| minor | tierce majeure ascendante | -0.073802 |