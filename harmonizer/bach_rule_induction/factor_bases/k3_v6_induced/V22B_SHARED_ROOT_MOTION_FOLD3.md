# K3-V22B-SHARED-ROOT-MOTION-STABILITY-1 — apprentissage conjoint d'un RuleGroup

Les 24 cellules du groupe
`named_root_motion_mode` sont apprises simultanément plutôt que
mises en concurrence comme des règles indépendantes. La projection
d'identifiabilité est appliquée après chaque pas proximal.

## Trajectoire de régularisation

| Candidat | λ groupe | NLL validation/pièce | e.s. | norme retenue | norme terminale | cellules |
|---|---:|---:|---:|---:|---:|---:|
| socle V20B réajusté | groupe absent | 0.913081 | 0.022062 | 0.000000 | 0.000000 | 0 |
| groupe λ=0.3 | 0.3 | 0.893010 | 0.021402 | 1.593807 | 1.593807 | 20 | **← retenu**

## Comparaisons appariées au socle

| Candidat | Gain moyen | e.s. appariée | IC bootstrap 95 % | Pièces améliorées |
|---|---:|---:|---:|---:|
| groupe λ=0.3 | +0.020071 | 0.004718 | [+0.011024, +0.028201] | 7/8 |

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
| major | quarte ascendante / quinte descendante | +0.641930 |
| major | tierce mineure descendante | +0.487712 |
| minor | quarte ascendante / quinte descendante | +0.416907 |
| minor | triton | +0.414900 |
| major | triton | +0.392111 |
| minor | seconde majeure ascendante | +0.215329 |
| major | tierce majeure descendante | +0.166842 |
| minor | seconde mineure ascendante | +0.138781 |
| major | seconde majeure ascendante | +0.123265 |
| major | quinte ascendante / quarte descendante | +0.082328 |
| minor | quinte ascendante / quarte descendante | +0.049036 |
| major | seconde mineure ascendante | +0.041906 |

### Interactions négatives les plus fortes

| Mode | Cas partagé | Poids |
|---|---:|---:|
| major | seconde mineure descendante | -0.561997 |
| major | seconde majeure descendante | -0.453284 |
| major | maintien | -0.423063 |
| major | tierce majeure ascendante | -0.422374 |
| minor | seconde majeure descendante | -0.383678 |
| minor | tierce majeure descendante | -0.366042 |
| minor | seconde mineure descendante | -0.200896 |
| minor | tierce mineure ascendante | -0.177103 |
| minor | maintien | -0.176818 |
| major | tierce mineure ascendante | -0.075375 |
| minor | tierce mineure descendante | +0.033089 |
| minor | tierce majeure ascendante | +0.036495 |