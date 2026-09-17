# V6 — réajustement génératif des poids

La structure des 30 facteurs est strictement gelée. Seuls leurs poids
sont ajustés par `E_Bach[f] - E_Gibbs[f]` sur un sous-ensemble de train.
Aucune nouvelle feature, règle historique ou contrainte experte n'est
introduite. Le test reste fermé.

## Résultat d'apprentissage

- Pièces train : `16`.
- Époques : `10`.
- MAE des moments : `0.035206` → `0.013355`.
- NLL conditionnelle validation : `1.048935` → `1.159607`.
- Plus grand déplacement de poids : `0.502723`.

La décision de promotion dépend d'un audit génératif séparé sur les
mêmes pièces et graines que V5.16.
