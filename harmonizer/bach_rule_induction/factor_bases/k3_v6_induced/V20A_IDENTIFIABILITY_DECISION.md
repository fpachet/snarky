# V20A — décision d'identifiabilité

## Résultat positif

V20A n'est pas une répétition de V19. Sur cinq découvertes complètes, trois
nouveaux prédicats nommés sont unanimes et toujours positifs :

- triade majeure à l'état fondamental ;
- triade mineure à l'état fondamental ;
- accord complet au premier renversement.

Une préférence pour la septième de dominante est également présente dans les
cinq découvertes : quatre sélectionnent la version « temps faible » et une la
version générale. La septième majeure générale apparaît dans trois bases.

Sur le découpage 32/10, la base à une erreur standard contient 18 règles et
atteint `0,813679` de NLL moyenne par pièce, contre `0,849082` pour V19.

## Défaut de la grammaire

V20A proposait simultanément, pour une qualité donnée :

- `qualité` ;
- `qualité × temps faible` ;
- `qualité × temps fort`.

Or, pour chaque monde candidat :

```text
qualité = qualité×faible + qualité×fort
```

La matrice possède donc une dépendance linéaire exacte. Le choix entre la
version générale et les versions métriques ne peut pas être structurellement
stable. Le même défaut existe pour le degré de fondamentale.

Cette redondance explique que la septième de dominante soit sémantiquement
stable 5/5 mais pas sous une clé de facteur unique. Elle ne doit pas être
résolue en abaissant après coup le seuil d'unanimité.

## Autre résultat négatif

Aucun facteur de degré de fondamentale n'est sélectionné dans les cinq bases.
Les statuts verticaux statiques expliquent donc la qualité et le renversement,
mais pas encore **quel accord** doit apparaître à un endroit donné.

## Décision

**V20A n'est ni réajusté sur le corpus complet ni généré.**

V20B corrige uniquement l'identifiabilité :

- la qualité générale reste le niveau de base ;
- `qualité × temps fort` devient une déviation additionnelle ;
- la variante faible redondante est supprimée ;
- le même codage est appliqué au degré de fondamentale.

Cette correction est algébrique et décidée avant toute nouvelle induction.
Elle ne modifie ni les qualités, ni les seuils, ni le budget, ni les données.
Les transitions harmoniques restent fermées.

Le test réservé reste fermé.
