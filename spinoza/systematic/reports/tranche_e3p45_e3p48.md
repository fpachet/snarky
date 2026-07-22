# Tranche E3P45–E3P48 : transfert social et réattribution causale

## Résultat

E3P45 à E3P48 sont exécutables sans règle historique et sans modification du
moteur. La tranche introduit le transfert triangulaire de la haine, la
généralisation aux membres d'une classe ou d'une nation, la coexistence d'une
joie et d'une tristesse, puis la destruction ou la diminution d'un affect par
réattribution de sa cause.

Deux écarts signalés par Cavarretta deviennent des invariants testés : E3P45
ne produit pas les conclusions annexes de SpinoLog, et E3P48 ne réduit pas une
révision causale à un doute ou à une négation absolue.

## E3P45 : un triangle conservé sous imagination

L'amant imagine qu'un tiers hait la chose aimée. L'application de E3P40 est
une compilation contextuelle : elle produit `imagine(aimee hait tiers)` et non
un fait brut. Cette haine imaginée expose une tristesse de la chose aimée ;
E3P21 la transmet à l'amant, puis l'idée du tiers accompagne sa tristesse et
E3P13 conclut à la haine.

La similitude de la chose aimée et du tiers est requise. Les faits
`fluctuation`, `stable`, `jalousie` et `dérision`, annoncés comme conclusions
annexes par SpinoLog, sont explicitement interdits. Le rapport historique
compte 41 inférences et 41 faits pour ce cas ; la clôture systématique reste
volontairement limitée à l'énoncé et à ses intermédiaires nécessaires.

## E3P46 : le nom général n'est pas l'appartenance

L'idée de l'individu est représentée à la fois comme idée de cet individu et
comme idée de l'individu sous le nom général d'une classe ou d'une nation. La
joie ou la tristesse reçoit alors l'idée générale comme cause ; E3P13 nomme
l'amour ou la haine envers la classe, puis E3P16 transfère l'affect aux membres
explicitement déclarés.

Un individu extérieur à la classe n'est jamais atteint. Réciproquement, la
seule appartenance sans présentation de la cause sous le nom général ne suffit
pas à généraliser l'affect.

## E3P47 : une extension interprétative déclarée

E3P47 cite E3P27 pour conclure à quelque tristesse lorsque la chose haïe et
semblable subit un mal. Or E3P27 exige une absence préalable d'affect, tandis
que l'objet de E3P47 est déjà haï. Cette difficulté, également relevée par
Cavarretta, n'est pas masquée : la transmission porte l'origine
`interpretative` et exige simultanément haine, similitude et tristesse
imaginée.

La joie provenant du mal et la tristesse imitée restent deux témoins. Le
scolie ajoute un souvenir vivace qui réactive une détermination triste ; une
image excluant l'existence de la chose réduit cette détermination sans
l'abolir, et renouvelle la joie liée au mal passé.

## E3P48 : causalité, non doute

L'amour et la haine sont réifiés avec la joie ou la tristesse qu'ils
enveloppent. Si l'objet initial est entièrement retiré comme cause et que
l'affect est joint à l'idée d'une autre cause, l'affection envers l'objet est
déclarée détruite. S'il demeure cause partielle sans être cause unique,
l'affection est seulement diminuée et varie qualitativement avec sa part
causale.

SpinoLog conclut plutôt `doute(aime)` ou `doute(hait)` et précise lui-même que
ce fait représente une remise en cause plutôt qu'une négation absolue. Le
modèle systématique sépare les trois notions : retrait causal, diminution et
doute. Il ne produit ni `FAUX` sur l'amour ou la haine, ni fait de doute.

Le contrôle a été effectué sur les pages PDF 41 à 43 du
[`rapport Cavarretta`](../../../docs/Cavarretta-X1988-SpinozaExpertSystem.pdf).

## Audit des clôtures

| Cas | Faits initiaux | Faits dérivés | Dérivations | Profondeur maximale des buts |
|---|---:|---:|---:|---:|
| E3P45, triangle de haine | 14 | 13 | 14 | 5 |
| E3P46, joie sous nom de classe | 13 | 14 | 15 | 3 |
| E3P47, destruction d'une chose similaire | 14 | 10 | 10 | 3 |
| E3P48, réattribution totale | 18 | 4 | 4 | 1 |

Ces nombres incluent les cinq postulats communs. Les règles historiques ne
sont jamais chargées et les deux exceptions de provenance, `compilation` pour
E3P45 et `interpretative` pour E3P47, sont vérifiées par les tests.

## Prochaine frontière

La couverture atteint E3P48, soit 48 propositions sur 59. E3P49 doit comparer
les affects envers une cause imaginée libre ou nécessaire sans remplacer
l'ordre qualitatif par le `doute` employé dans SpinoLog. E3P50–E3P52 traiteront
ensuite présages, variabilité individuelle et étonnement.
