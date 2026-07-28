# V6 — correction générative contrôlée, structure gelée

Les 30 facteurs restent strictement identiques. Le vecteur de poids est
déplacé une seule fois selon la correction linéaire minimale estimée
sur le train par la matrice de covariance. Aucun réglage sur validation
n'est effectué et le test réservé n'est pas chargé.

## Paramètres

- Échelle préenregistrée : `1.000000`.
- Facteurs modifiés : `30`.
- Plus grand déplacement : `0.727985`.
- NLL conditionnelle validation : `1.162405` → `1.242368`.

La décision dépend maintenant d'un nouvel audit génératif sur les mêmes
pièces et graines que les modèles précédents.
