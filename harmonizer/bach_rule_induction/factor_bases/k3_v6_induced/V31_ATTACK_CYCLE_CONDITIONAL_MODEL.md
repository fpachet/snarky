# V31 — facteur conditionnel de continuation ABAB

Le domaine d'activation est limité aux retours à retard 2. Le facteur
demande alors si le retour courant prolonge un cycle déjà commencé :
`... A B A -> B`. Les autres choix ne font pas partie de ce petit
modèle conditionnel.

## Estimation

- Train (32 chorals) : `123 / 954` = `12.893 %`.
- Test intact (51 chorals) : `203 / 1337` = `15.183 %`.
- Poids log-odds MLE : `-1.910445`.
- Granularité retenue par BIC sur train : `shared_lower_voice_factor`.
- Confirmation indépendante : `False`.

## Interprétation déclarative

Ce n'est pas une interdiction de `ABA` ni de `ABAB`. Quand une
alternative prolongerait `ABAB`, Snarky active exactement un facteur
négatif. Sa portée est une voix et quatre attaques successives ; il
n'active aucune autre règle.

Le test K3 général tenté auparavant reste rejeté selon son protocole
de sélection. Ce facteur-ci est un modèle conditionnel distinct,
normalisé seulement sur le domaine rare qu'il décrit.
