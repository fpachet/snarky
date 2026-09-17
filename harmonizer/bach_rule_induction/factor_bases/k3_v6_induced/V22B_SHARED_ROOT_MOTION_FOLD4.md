# K3-V22B-SHARED-ROOT-MOTION-STABILITY-1 — apprentissage conjoint d'un RuleGroup

Les 24 cellules du groupe
`named_root_motion_mode` sont apprises simultanément plutôt que
mises en concurrence comme des règles indépendantes. La projection
d'identifiabilité est appliquée après chaque pas proximal.

## Trajectoire de régularisation

| Candidat | λ groupe | NLL validation/pièce | e.s. | norme retenue | norme terminale | cellules |
|---|---:|---:|---:|---:|---:|---:|
| socle V20B réajusté | groupe absent | 0.891869 | 0.042633 | 0.000000 | 0.000000 | 0 |
| groupe λ=0.3 | 0.3 | 0.881731 | 0.044326 | 1.548524 | 1.548524 | 21 | **← retenu**

## Comparaisons appariées au socle

| Candidat | Gain moyen | e.s. appariée | IC bootstrap 95 % | Pièces améliorées |
|---|---:|---:|---:|---:|
| groupe λ=0.3 | +0.010138 | 0.005007 | [+0.001460, +0.019716] | 6/8 |

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
| major | quarte ascendante / quinte descendante | +0.568030 |
| major | triton | +0.365045 |
| major | tierce mineure descendante | +0.352135 |
| major | quinte ascendante / quarte descendante | +0.201623 |
| major | seconde majeure ascendante | +0.179147 |
| minor | triton | +0.162152 |
| minor | seconde majeure ascendante | +0.160517 |
| minor | quarte ascendante / quinte descendante | +0.159356 |
| major | tierce majeure descendante | +0.152843 |
| minor | seconde mineure ascendante | +0.142277 |
| major | seconde mineure ascendante | +0.114328 |
| minor | quinte ascendante / quarte descendante | +0.094037 |

### Interactions négatives les plus fortes

| Mode | Cas partagé | Poids |
|---|---:|---:|
| major | seconde mineure descendante | -0.703981 |
| minor | tierce majeure descendante | -0.689285 |
| major | seconde majeure descendante | -0.592676 |
| major | maintien | -0.393988 |
| major | tierce majeure ascendante | -0.316559 |
| minor | maintien | -0.079491 |
| minor | seconde mineure descendante | -0.059501 |
| minor | tierce mineure descendante | -0.022319 |
| minor | seconde majeure descendante | +0.013664 |
| minor | tierce majeure ascendante | +0.029041 |
| major | tierce mineure ascendante | +0.074052 |
| minor | tierce mineure ascendante | +0.089553 |