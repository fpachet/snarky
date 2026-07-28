# V8 — pseudo-vraisemblance exacte des mondes Gibbs

Chaque alternative remplace une attaque et toute sa tenue. Son
vecteur factoriel somme exactement tous les noyaux K3 et toutes les
portées que le sampler Gibbs recompte. Le soprano et les états de
bord sont fixes, comme pendant la génération.

## Corpus de développement

- Pièces train : `251`.
- Pièces validation : `50`.
- Choix train : `53604`.
- Choix validation : `10414`.
- Alternatives par choix : `46`.
- Facteurs appris conjointement : `48`.
- Test réservé : non chargé.

## NLL exacte

| Poids | Validation |
|---|---:|
| V6 pseudo-vraisemblance centrale | 1.039394 |
| Iteration 2 générative | 1.014606 |
| V8 pseudo-vraisemblance centrale | 0.989966 |
| V8 exacte | **0.829642** |

La promotion dépend des audits génératifs à 6 et 30 sweeps.
