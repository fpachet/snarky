# K3-V22B-SHARED-ROOT-MOTION-STABILITY-1 — apprentissage conjoint d'un RuleGroup

Les 24 cellules du groupe
`named_root_motion_mode` sont apprises simultanément plutôt que
mises en concurrence comme des règles indépendantes. La projection
d'identifiabilité est appliquée après chaque pas proximal.

## Trajectoire de régularisation

| Candidat | λ groupe | NLL validation/pièce | e.s. | norme retenue | norme terminale | cellules |
|---|---:|---:|---:|---:|---:|---:|
| socle V20B réajusté | groupe absent | 0.734248 | 0.040767 | 0.000000 | 0.000000 | 0 |
| groupe λ=0.3 | 0.3 | 0.722873 | 0.040918 | 1.426144 | 1.426144 | 22 | **← retenu**

## Comparaisons appariées au socle

| Candidat | Gain moyen | e.s. appariée | IC bootstrap 95 % | Pièces améliorées |
|---|---:|---:|---:|---:|
| groupe λ=0.3 | +0.011374 | 0.003185 | [+0.005318, +0.016890] | 7/8 |

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
| major | quarte ascendante / quinte descendante | +0.487388 |
| major | tierce mineure descendante | +0.436989 |
| major | seconde mineure ascendante | +0.283221 |
| major | quinte ascendante / quarte descendante | +0.240756 |
| major | triton | +0.237958 |
| minor | triton | +0.227828 |
| minor | quarte ascendante / quinte descendante | +0.222440 |
| major | seconde majeure ascendante | +0.188593 |
| minor | seconde majeure ascendante | +0.157043 |
| minor | seconde mineure ascendante | +0.135049 |
| minor | quinte ascendante / quarte descendante | +0.074225 |
| major | tierce mineure ascendante | +0.069323 |

### Interactions négatives les plus fortes

| Mode | Cas partagé | Poids |
|---|---:|---:|
| major | seconde mineure descendante | -0.661991 |
| major | seconde majeure descendante | -0.560631 |
| major | maintien | -0.419477 |
| minor | tierce majeure descendante | -0.371176 |
| major | tierce majeure ascendante | -0.266231 |
| minor | maintien | -0.201554 |
| minor | seconde majeure descendante | -0.161966 |
| minor | seconde mineure descendante | -0.080434 |
| minor | tierce mineure descendante | -0.062200 |
| major | tierce majeure descendante | -0.035897 |
| minor | tierce mineure ascendante | -0.007901 |
| minor | tierce majeure ascendante | +0.068646 |