# Tranche E3P23–E3P26 : inversion et affirmation affectives

## Résultat

E3P23 à E3P26 sont exécutables sans règle historique et sans modification du
moteur. Elles prolongent le jalon E3P19–E3P22 selon deux axes :

- l’affect de la chose haïe produit dans l’observateur un affect de valence
  contraire ;
- l’observateur s’efforce d’affirmer ou de nier un contenu en fonction de
  l’affect qui en résulte.

Chaque manifeste possède au moins un contre-cas de non-dérivation et interdit
l’aplatissement d’une proposition imaginée vers un fait brut.

## E3P23–E3P24 : inversion de valence

E3P23 garde une relation explicite
`correspond_a_affect_contraire_imagine` :

- la tristesse imaginée de la chose haïe produit la joie ;
- sa joie imaginée produit la tristesse ;
- l’ordre qualitatif d’intensité de l’affect source est transmis à l’affect
  contraire de l’observateur.

E3P24 réutilise cette inversion. L’idée de la cause extérieure accompagne
l’affect transmis, puis E3P13S conclut à la haine envers la cause de la joie ou
à l’amour envers la cause de la tristesse. Son scolie définit l’envie par la
conjonction de la haine, de la disposition à se réjouir du mal d’autrui et de
la disposition à s’attrister de son bien.

Le combat intérieur annoncé dans le scolie de E3P23 dépend de la similitude et
de l’imitation des affects ; il est donc réservé à E3P27.

## E3P25–E3P26 : contenu et sujet de l’effort

Le modèle représente l’effort par des propositions imbriquées :

```text
ame s_efforce_d_affirmer (contenu est_affirme_de cible)
ame s_efforce_de_nier (contenu est_nie_de cible)
```

Le contenu et la cible restent ainsi distincts. Aucun de ces efforts ne dérive
le contenu, sa vérité, sa fausseté, son existence ou son inexistence.

E3P25 traite séparément la chose aimée et le sujet lui-même. E3P26 réutilise
E3P23 pour inverser l’affect envers la chose haïe. Son scolie rend exécutables
l’orgueil, la surestime et la mésestime ; l’orgueil est en outre classé comme
une espèce de délire.

## Comparaison avec SpinoLog 1988

Le rapport Cavarretta annonce 45 inférences et 46 faits pour E3P23, puis 43
inférences et 43 faits pour chacune des propositions E3P24 à E3P26. Il indique
également que l’intensité de E3P23 n’est pas traitée.

Pour E3P25–E3P26, SpinoLog traduit l’effort d’affirmer ou de nier par un effort
portant sur l’état `EXISTANT` ou `INEXISTANT` d’un objet. Cette compilation est
utile opérationnellement, mais elle perd le sujet auquel le contenu est
attribué. Le modèle systématique ne l’importe donc pas. Des faits interdits
vérifient explicitement l’absence de ces conclusions aplaties.

Les clôtures systématiques produisent actuellement :

| Cas | Faits dérivés | Dérivations | Profondeur maximale des buts |
|---|---:|---:|---:|
| E3P23, chaque valence avec intensité | 15 | 15 | 5 |
| E3P24, chaque cause extérieure | 11 | 11 | 4 |
| E3P25, chose aimée | 28 | 28 | 6 |
| E3P25, sujet lui-même | 14 | 14 | 3 |
| E3P26, chose haïe | 14 | 14 | 3 |
| E3P26, scolie des estimations | 5 | 5 | 1 |

Ces nombres décrivent les fixtures actuelles ; ils ne cherchent pas à
reproduire les clôtures de la base SpinoLog complète.

## Prochaine frontière

La couverture atteint E3P26. Avant E3P27, il faut formaliser la similitude
comme une relation typée et contextuelle, distinguer similitude corporelle,
pertinente pour l’affect, et simple ressemblance de trait, puis garantir
l’absence préalable d’amour ou de haine sans recourir à la négation par défaut.
