# Tranche E3P27–E3P32 : imitation et affects sociaux

## Résultat

E3P27 à E3P32 sont exécutables sans règle historique et sans modification du
moteur. Cette tranche établit la première ontologie explicite de la similitude
affective, puis la réutilise pour représenter l'imitation, l'approbation
sociale, la considération de soi, l'accord avec autrui et l'envie.

Chaque proposition possède un contre-cas de non-dérivation. Les propositions
imbriquées restent dans leur contexte et l'absence d'un fait ne vaut jamais sa
fausseté.

## E3P27 : similitude et imitation

La similitude pertinente n'est pas un prédicat générique. Le modèle relie le
corps d'autrui au corps dont l'âme de l'observateur est l'idée :

```text
autrui a_corps corps_autrui
ame est_idee_de corps_ame
corps_autrui a_nature_corporelle_similaire_a corps_ame
=> autrui est_semblable_affectivement_pour ame
```

Une simple ressemblance de trait ne déclenche pas cette règle. De même, la
condition selon laquelle l'observateur n'éprouve encore aucun affect envers
autrui est donnée par `est_sans_affect_prealable_envers` : elle n'est jamais
inférée par défaut.

Sur cette base, joie, tristesse et désir sont imités séparément. Les scolies et
corollaires rendent aussi exécutables commisération, émulation, amour ou haine
envers une cause extérieure et bienveillance née de la commisération.

## E3P28–E3P32

- E3P28 distingue l'effort pour procurer ou faire advenir une joie de l'effort
  pour écarter ou détruire ce qui mène à la tristesse.
- E3P29 transforme l'approbation ou l'aversion imaginée des hommes en conduite
  sociale ; ambition, humanité, louange et blâme restent des notions nommées.
- E3P30 passe par l'idée de soi comme cause intérieure de l'affect. La gloire
  et la honte exigent respectivement une louange et un blâme explicites ; joie
  ou tristesse intérieures seules donnent contentement de soi ou repentir.
- E3P31 garde amour, désir et haine distincts lorsqu'il formalise accord,
  constance, désaccord et fluctuation. Il ne compile donc pas le désir en
  amour.
- E3P32 exige le fait positif qu'un objet ne puisse être possédé que par un
  seul avant de transformer la possession d'autrui en obstacle, effort de
  retrait et envie. Le scolie ajoute l'imitation enfantine.

## Comparaison avec SpinoLog 1988

Le rapport Cavarretta annonce 47 inférences et 48 faits pour E3P27. Il signale
cependant que la similitude et l'absence préalable de sentiment sont
insuffisamment déterminées. Le modèle systématique rend précisément ces deux
conditions visibles et maintient hors de la clôture les nombreux faits annexes
de la base historique.

E3P28, E3P29 et E3P32 ne sont pas exploitées dans le rapport. Pour E3P30,
SpinoLog annonce 120 inférences et 122 faits, avec une propagation de la gloire
plus large que l'énoncé ; le contre-cas systématique interdit cette conclusion
sans louange explicite. Pour E3P31, les 46 inférences et 48 faits historiques
dépendent fortement de la similitude et assimilent opérationnellement désir et
amour, distinction que la nouvelle couche conserve.

Les clôtures représentatives du modèle systématique sont :

| Cas | Faits initiaux | Faits dérivés | Dérivations | Profondeur maximale des buts |
|---|---:|---:|---:|---:|
| E3P27, imitation de trois affects | 24 | 14 | 14 | 3 |
| E3P28, joie et tristesse | 11 | 7 | 7 | 1 |
| E3P29, approbation et aversion | 14 | 16 | 16 | 4 |
| E3P30, considération de soi | 23 | 19 | 19 | 4 |
| E3P31, accord amour/désir/haine | 15 | 6 | 6 | 2 |
| E3P32, possession exclusive | 17 | 11 | 11 | 6 |

Ces nombres décrivent les fixtures actuelles. Ils ne cherchent pas à
reproduire la clôture de la base SpinoLog complète.

## Prochaine frontière

La couverture atteint E3P32, soit 32 propositions sur 59. E3P33 doit maintenant
reconstruire l'effort pour être aimé par l'objet aimé en réutilisant E3P27,
E3P28 et E3P31. Ce jalon vérifiera notamment que la nouvelle preuve emploie
réellement la similitude, contrairement à certaines chaînes historiques.
