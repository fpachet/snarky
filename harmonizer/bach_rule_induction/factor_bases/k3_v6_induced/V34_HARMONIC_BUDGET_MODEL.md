# V34 — modèle compact de résolution et budgets harmoniques

Le modèle observe chaque accord nommé dissonant sur un temps fort
et classe le prochain temps fort en triade, autre accord nommé
dissonant ou sonorité résiduelle. Le BIC choisit une distribution
partagée plutôt qu'une table distincte par famille.

## Estimation

- Train : `0.164139` d'accords nommés dissonants par transition forte.
- Validation : `0.145985`.
- Train : `0.158718` de chaînes dissonant→dissonant.
- Validation : `0.127273`.
- Confirmation : `False`.

## Budgets pour 25 transitions fortes

- Accords nommés dissonants : au plus `7`.
- Chaînes, conditionnellement à ce budget : au plus `3`.

Ces maxima sont des quantiles binomiaux appris, pas des
interdictions musicologiques ajoutées à la main.
