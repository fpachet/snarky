# Première expérience des deux boucles — score minimal appris

Les 57 facteurs V23 et leurs poids proviennent du MLE conditionnel
conjoint. Le threshold est calibré sur les pseudo-vraisemblances
exactes par choral. Gibbs n'est pas utilisé pour générer.

## Calibration

- Split : `validation`.
- Politique : `strict_minimum`.
- Chorals : `10`.
- Couverture : `10/10`.
- Threshold moyen : `-1.412463`.
- Moyenne par décision : `-0.798403`.

## Recherche Snarky

- Statut : `solved`.
- Nœuds explorés : `32`.
- Branches en échec : `21`.
- Contradictions de score : `21`.
- Dont contradictions avant assignation complète : `0`.
- Backtracks : `21`.
- Solutions : `1`.
- Verdict du protocole : `PASS`.

## Comparaison contrôlée

- Première solution sans seuil : `-2.188816`.
- Bach authentique (diagnostic seulement) : `-0.277475`.
- Score de la solution : `-1.277364`.
- Marge au threshold : `+0.135100`.

## Blocs retenus

| Bloc | Soprano | Alto | Ténor | Basse |
|---:|---:|---:|---:|---:|
| 0 | 71 | 66 | 62 | 47 |
| 1 | 71 | 66 | 62 | 47 |
| 2 | 71 | 66 | 62 | 47 |
| 3 | 71 | 66 | 62 | 47 |
| 4 | 71 | 66 | 62 | 47 |
| 5 | 78 | 66 | 62 | 59 |

## Limites observées

- Le threshold est calibré sur dix chorals complets, tandis que la
  recherche porte ici sur un fragment court de huit décisions.
- Les 23 filtres V22 restent des contraintes empiriques pré-test.
- Sur six blocs, les portées exactes se recouvrent toutes : les 21
  contradictions apparaissent après assignation complète.
- La solution acceptée est très répétitive : V23 manque donc encore
  un détecteur ou un seuil de groupe pour cette pathologie.

## Interprétation

Une branche est rejetée lorsque la somme de ses contributions
déjà fixées est inférieure au score total requis, même en donnant
la contribution maximale zéro à toutes les décisions restantes.
Il s'agit d'une contrainte de satisfaction, pas d'une recherche du
maximum global.

Le seuil élimine bien la première solution, mais la solution
acceptée reste très répétitive. Cela prouve le mécanisme de
backtracking tout en révélant que le score global V23 ne détecte
pas encore toutes les mauvaises solutions musicales.
