# Jalon E3P19–E3P22 : comparaison et audit de clôture

## Périmètre

Ce jalon compare quatre niveaux qui ne doivent pas être confondus :

1. le texte français de l’*Éthique* III et ses démonstrations ;
2. la reconstruction de la présentation de Gondran dans la couche historique ;
3. les résultats publiés par Cavarretta pour SpinoLog en juillet 1988 ;
4. la reconstruction systématique, qui ne charge aucune règle historique.

Les propositions E3P19 à E3P22 sont désormais exécutables dans
[`../theorems`](../theorems). E3P20, absente des quatre exemples de la
présentation de Gondran, est également couverte. Chaque proposition possède au
moins un contre-cas de non-dérivation.

## Chaînes systématiques

| Proposition | Chaîne explicitée | Profondeur du résultat principal |
|---|---|---:|
| E3P19 | amour → effort de conservation → image qui pose/exclut l’existence → passage de perfection → joie/tristesse | 3 |
| E3P20 | haine → effort d’écarter → destruction imaginée → effort secondé → joie | 3 |
| E3P21 | affect imaginé → existence posée/exclue → E3P19 → correspondance des affects → ordre d’intensité transmis | 5 |
| E3P22 | action extérieure imaginée → affect de la chose aimée → E3P21 → idée de la cause → E3P13S → amour/haine | 7 |

Ces profondeurs sont supérieures aux profondeurs 2, 2 et 3 des chaînes
historiques pour E3P19, E3P21 et E3P22. La différence est intentionnelle : les
règles SpinoLog P13, P19 et P22 condensent plusieurs transitions textuelles que
le modèle systématique représente séparément.

## Contextes et témoins

`ame imagine P` ne produit jamais `P`. Ainsi, imaginer qu’un objet est conservé
ou détruit qualifie la proposition imaginée comme posant ou excluant son
existence, mais ne dérive ni conservation, ni destruction, ni existence réelle.

Les affects résultants et l’affect causé dans la chose aimée sont des témoins
nommés dans les manifestes. Cette solution rend les dépendances existentielles
visibles sans introduire `QQCHOSE` ni modifier le moteur.

## Intensité de E3P21

Spinoza affirme une covariance : l’affect de l’amant est plus grand ou moindre
selon celui de la chose aimée. SpinoLog indique explicitement ne pas démontrer
cette fin de la proposition.

Le fragment systématique représente une première version non numérique :

- chaque affect de l’amant `correspond_a_affect_imagine` un affect source ;
- il `varie_selon_degre_de` cet affect ;
- un ordre imaginé `est_plus_intense_que` entre deux affects sources est
  transmis aux deux affects correspondants de l’amant.

Cette formalisation préserve l’ordre qualitatif sans prétendre mesurer les
intensités ni imposer leur égalité numérique.

## Audit SpinoLog

Le rapport 1988 annonce 45 inférences et 46 faits déduits pour E3P19, E3P20 et
E3P21. Pour E3P21, il cite notamment un objet générique `QQCHOSE`, l’amour et la
jalousie envers cet objet, ainsi que la gloire. Ces conclusions ne sont pas des
conséquences textuelles immédiates de E3P21.

Les contre-tests systématiques vérifient donc que ces quatre familles de faits
ne sont pas dérivées. De même, la « proposition 20bis » produite par SpinoLog —
la conservation imaginée d’une chose haïe rendrait triste — reste hors du
modèle tant qu’une justification textuelle propre n’est pas établie.

La reconstruction locale de la présentation, plus petite que la base complète
de 1988, produit actuellement 6 faits dérivés pour les cas E3P19 et E3P21, 11
pour l’amour de E3P22 et 8 pour sa haine. Les cas systématiques produisent 6
faits pour E3P19–20, 15 pour chaque branche avec intensité de E3P21 et 14 pour
chaque branche de E3P22. Ces nombres sont observables via les champs de clôture
de `CaseResult` ; ils ne sont pas des seuils normatifs.

## Scolie de E3P22

Le scolie rend exécutables trois notions :

- commisération : tristesse née du dommage d’autrui ;
- faveur : amour envers celui qui a fait du bien à autrui ;
- indignation : haine envers celui qui a fait du mal à autrui.

L’extension de la commisération à une chose seulement semblable est réservée à
E3P27, conformément au renvoi explicite du texte.

## Critère de sortie

Le jalon est atteint : les quatre propositions, les deux branches affectives,
l’intensité qualitative et le scolie de E3P22 sont exécutables ; les règles
historiques restent isolées ; les conclusions annexes de SpinoLog sont auditées
par non-dérivation. La prochaine tranche commence à E3P23.
