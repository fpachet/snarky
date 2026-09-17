# K3-V22-SHARED-ROOT-MOTION-GROUP-1 — apprentissage conjoint d'un RuleGroup

Les 24 cellules du groupe
`named_root_motion_mode` sont apprises simultanément plutôt que
mises en concurrence comme des règles indépendantes. La projection
d'identifiabilité est appliquée après chaque pas proximal.

## Trajectoire de régularisation

| Candidat | λ groupe | NLL validation/pièce | e.s. | norme retenue | norme terminale | cellules |
|---|---:|---:|---:|---:|---:|---:|
| socle V20B réajusté | groupe absent | 0.820727 | 0.081510 | 0.000000 | 0.000000 | 0 |
| groupe λ=0.3 | 0.3 | 0.803764 | 0.083421 | 1.464392 | 1.464392 | 21 | **← retenu**
| groupe λ=0.1 | 0.1 | 0.801559 | 0.083611 | 1.769166 | 1.769166 | 20 |
| groupe λ=0.03 | 0.03 | 0.800810 | 0.083694 | 1.879777 | 1.870882 | 20 |
| groupe λ=0.01 | 0.01 | 0.800600 | 0.083720 | 1.916821 | 1.901652 | 20 |
| groupe λ=0.003 | 0.003 | 0.800546 | 0.083741 | 1.930525 | 1.912714 | 21 |
| groupe λ=0 | 0 | 0.800514 | 0.083745 | 1.936327 | 1.917506 | 21 |

## Comparaisons appariées au socle

| Candidat | Gain moyen | e.s. appariée | IC bootstrap 95 % | Pièces améliorées |
|---|---:|---:|---:|---:|
| groupe λ=0.3 | +0.016963 | 0.004846 | [+0.007952, +0.026077] | 9/10 |
| groupe λ=0.1 | +0.019168 | 0.005409 | [+0.009074, +0.029254] | 9/10 |
| groupe λ=0.03 | +0.019917 | 0.005694 | [+0.009261, +0.030460] | 9/10 |
| groupe λ=0.01 | +0.020127 | 0.005776 | [+0.009407, +0.030804] | 9/10 |
| groupe λ=0.003 | +0.020181 | 0.005798 | [+0.009399, +0.030918] | 9/10 |
| groupe λ=0 | +0.020213 | 0.005811 | [+0.009378, +0.030980] | 9/10 |

## Décision

- Meilleur candidat brut : `groupe λ=0`.
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
| major | quarte ascendante / quinte descendante | +0.559785 |
| major | tierce mineure descendante | +0.434587 |
| major | triton | +0.312401 |
| minor | triton | +0.231901 |
| minor | quarte ascendante / quinte descendante | +0.228182 |
| major | seconde majeure ascendante | +0.186957 |
| major | seconde mineure ascendante | +0.185500 |
| minor | seconde majeure ascendante | +0.180316 |
| minor | seconde mineure ascendante | +0.161033 |
| major | quinte ascendante / quarte descendante | +0.157116 |
| minor | quinte ascendante / quarte descendante | +0.094782 |
| major | tierce majeure descendante | +0.086314 |

### Interactions négatives les plus fortes

| Mode | Cas partagé | Poids |
|---|---:|---:|
| major | seconde mineure descendante | -0.627694 |
| minor | tierce majeure descendante | -0.473559 |
| major | seconde majeure descendante | -0.459275 |
| major | maintien | -0.432770 |
| major | tierce majeure ascendante | -0.399249 |
| minor | seconde majeure descendante | -0.228793 |
| minor | maintien | -0.154694 |
| minor | seconde mineure descendante | -0.119975 |
| major | tierce mineure ascendante | -0.003671 |
| minor | tierce mineure ascendante | +0.005342 |
| minor | tierce mineure descendante | +0.023399 |
| minor | tierce majeure ascendante | +0.052066 |