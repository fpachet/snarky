# Tranche E3DA*-EXP — explications annexes

## Résultat

Les 27 sections du corpus intitulées « Explication » sont maintenant une
couche systématique exécutable, séparée des 48 définitions canoniques et de la
définition générale :

- 27 manifestes dans `explanations/` ;
- 27 fichiers dans `rules/explanations/` ;
- 44 règles d'origine `textual_explanation` ;
- 54 cas exécutables, soit un cas positif et une frontière négative par
  explication ;
- 27 textes sources repris directement de `sources/passages.json` dans
  l'atlas.

Les identifiants suivent la définition expliquée : `E3DA01-EXP` jusqu'à
`E3DA48-EXP`, avec `E3DA-GENERAL-EXP` pour l'explication générale. L'absence
d'une explication pour certaines définitions n'est pas un trou de couverture :
seules 27 des 49 unités définitionnelles possèdent une section ainsi intitulée
dans le texte importé.

## Principaux engagements formalisés

La tranche rend explicites :

- l'identité de l'appétit avec ou sans conscience et l'extension du Désir aux
  efforts, impulsions et volitions ;
- la Joie et la Tristesse comme passages plutôt que perfections statiques ;
- l'exclusion de l'Étonnement des trois affects primitifs ;
- la distinction entre essence de l'Amour et propriété d'union ;
- la réciprocité structurale de l'Espoir et de la Crainte ;
- les deux sens du Contentement de soi et leurs opposés ;
- le rôle de l'éducation et de la coutume dans l'association des actes à la
  Joie, à la Tristesse, au Repentir ou à la Gloire ;
- les distinctions Honte–Pudeur, imitation–Émulation et passion–puissance de
  l'âme ;
- les quatre composantes de l'explication générale : confusion de l'idée,
  état actuel du corps, variation effective de réalité et valeur de l'idée
  suivant son objet.

Les absences, différences culturelles, temporalités et alternatives restent
des faits positifs explicites. Aucune négation par défaut, disjonction native,
création existentielle ou comparaison quantitative n'a été ajoutée.

## Graphe des règles et des prédicats

Le générateur de l'atlas analyse les relations de premier niveau des prémisses
factuelles et des actions `ADD`. Pour chaque règle, il publie :

- les prédicats d'entrée ;
- les prédicats de sortie ;
- une arête dirigée `R1 → R2` pour chaque prédicat produit par `R1` et consommé
  par `R2` ;
- des voisinages secondaires entre règles qui partagent un prédicat sans
  former une dépendance dirigée.

À ce jalon, le modèle contient 652 règles, 745 prédicats distincts et 13 107
couples producteur–consommateur agrégés. Ces nombres sont recalculés à chaque
construction du site. Une relation imbriquée dans le sujet ou l'objet d'un
fait n'est pas traitée comme le prédicat de ce fait : ce choix respecte le
matching effectivement utilisé par le moteur.

La vue web affiche un voisinage local plutôt que les 652 nœuds simultanément.
Elle limite le nombre de nœuds dessinés mais conserve les compteurs complets,
la recherche par règle ou prédicat et les liens vers le code Snark.

## Moteur

`ForwardEngine` n'a pas été modifié. Le lanceur de manifestes reconnaît
seulement le nouveau répertoire `explanations/`. Le graphe est une analyse
statique dérivée des règles ; il ne change ni le matching, ni la clôture, ni la
provenance des preuves.
