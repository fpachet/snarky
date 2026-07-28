# V6 — correction générative contrôlée, structure gelée

Les 30 facteurs restent strictement identiques. Le vecteur de poids est
déplacé une seule fois selon la correction linéaire minimale estimée
sur le train par la matrice de covariance. Aucun réglage sur validation
n'est effectué et le test réservé n'est pas chargé.

## Paramètres

- Échelle demandée : `1.000000`.
- Échelle effectivement appliquée : `1.000000`.
- Rayon maximal du pas : `0.05`.
- Facteurs modifiés : `30`.
- Plus grand déplacement : `0.039832`.
- NLL conditionnelle validation : `1.241166` → `1.238870`.

La décision dépend maintenant d'un nouvel audit génératif sur les mêmes
pièces et graines que les modèles précédents.
