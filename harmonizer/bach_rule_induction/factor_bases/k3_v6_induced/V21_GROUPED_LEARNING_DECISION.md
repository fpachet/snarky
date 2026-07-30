# V21 — décision sur l'apprentissage conjoint d'un RuleGroup

## Hypothèse

V20C mettait les 288 transitions de fondamentales en concurrence comme des
colonnes indépendantes. V21 teste l'hypothèse inverse : ces cellules
constituent une seule règle structurée, une matrice
`mode × fondamentale précédente × fondamentale courante`, dont tous les poids
sont appris simultanément.

La matrice est doublement centrée. Ses sommes par ligne et par colonne sont
nulles : elle ne peut donc pas recopier les simples préférences marginales
pour une fondamentale de départ ou d'arrivée.

## V21A — premier découpage

Sur le découpage 32/10, l'ajustement conjoint produit un signal que V20C ne
détectait pas cellule par cellule :

- socle V20B réajusté : `0,820727` de NLL moyenne par pièce ;
- groupe non pénalisé : `0,802396` ;
- amélioration appariée moyenne : `0,018331 ± 0,007126` ;
- 8 chorals améliorés sur 10 ;
- intervalle bootstrap 95 % : `[0,00590 ; 0,03238]`.

Le critère historique à une erreur standard sur la NLL **absolue** retient
encore le socle, car l'hétérogénéité entre chorals est beaucoup plus grande
que l'incertitude de leur différence appariée. Ce conflit motive une
réplication, pas une promotion.

## V21B/V21C — quatre plis disjoints

La pénalité `λ=0,03`, gelée avant les quatre plis, et l'ablation sans pénalité
aboutissent à la même conclusion. La matrice s'éloigne bien de zéro et réduit
la NLL du train, mais la validation se dégrade dans les quatre plis.

Pour l'ablation non pénalisée, la différence terminale de NLL de décision
`groupe - socle` vaut :

| Pli | Dégradation validation |
|---:|---:|
| 1 | `+0,031847` |
| 2 | `+0,019043` |
| 3 | `+0,012126` |
| 4 | `+0,030554` |

Le `norm=0` rendu par les fichiers de plis est le checkpoint d'arrêt précoce :
le meilleur point de validation est l'initialisation sans groupe. Ce n'est ni
une absence d'activations dans le cache, ni une annulation du gradient. Les
matrices terminales atteignent des normes comprises entre `4,18` et `4,52`,
mais surapprennent.

## Décision

- L'idée d'apprendre un groupe conjointement est **implémentée et
  fonctionnelle**.
- La table libre de 288 paramètres est **rejetée** : son gain initial ne se
  reproduit pas hors pli.
- Aucun ajustement sur les 251 chorals et aucune génération ne sont lancés.
- Les transitions V20C ne seront pas réintroduites cellule par cellule.
- Le test réservé reste fermé.

Le résultat ne condamne pas les RuleGroups. Il montre qu'un groupe ne doit pas
être seulement un sac de paramètres appris ensemble. Il doit partager de la
structure : symétries, paramètres communs, hiérarchie ou faible rang, afin que
son nombre effectif de degrés de liberté reste compatible avec une règle
humaine.

## Conséquence pour règles et contraintes

La prochaine représentation doit séparer :

1. des **contraintes candidates**, prédicats presque invariants possédant
   beaucoup d'occasions contrefactuelles, testés sur plusieurs plis avant
   toute promotion en filtre dur ;
2. des **RuleGroups souples de faible dimension**, dans lesquels plusieurs
   cas partagent réellement un petit nombre de paramètres ;
3. leurs exceptions explicites, conservées comme facteurs souples plutôt que
   cachées dans une table de 288 coefficients.

Cette étape doit commencer par un audit de dimension et d'invariants, pas par
une nouvelle génération.
