# V6 — réajustement génératif des poids

La structure des 30 facteurs est strictement gelée. Seuls leurs poids
sont ajustés par `E_Bach[f] - E_Gibbs[f]` sur un sous-ensemble de train.
Aucune nouvelle feature, règle historique ou contrainte experte n'est
introduite. Le test réservé reste non chargé.

## Résultat d'apprentissage

- Pièces train : `248`.
- Pièces structurellement exclues avant sélection : `3`.
- Époques : `10`.
- Processus d'échantillonnage : `8`.
- MAE des moments : `0.029411` → `0.012867`.
- NLL conditionnelle validation : `1.048935` → `1.156809`.
- Plus grand déplacement de poids : `0.501036`.

La décision de promotion dépend d'un audit génératif séparé sur les
mêmes pièces et graines que V5.16.
