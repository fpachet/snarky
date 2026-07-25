# Jalon CSP générique et harmoniseur note par note

## But

Ce jalon reprend le socle `CHOICE`, propagation et rollback pour construire
deux applications qui exercent réellement les mêmes primitives :

1. un solveur CSP fini générique, validé par un Sudoku nécessitant des choix ;
2. un harmoniseur dont les décisions portent sur les notes SATB et non plus
   sur un voicing opaque.

Le moteur de règles ne lance toujours aucune recherche implicitement.
`SessionChoiceSearch` orchestre les décisions, mais variables, domaines,
contraintes, contradictions et buts restent des faits ou des règles.

## Architecture commune

```text
faits de variables et candidats
             ↓
groupes de propagation métier
             ↓
classification des singletons et contradictions
             ↓
CHOICE déclaratif + politique de variable
             ↓
checkpoint, saturation, contradiction ou solution
             ↓
rollback et alternative suivante
```

`FiniteCSP` remplace le nom trop restrictif `BinaryCSP`. L'ancien nom reste
un alias compatible. Une relation binaire extensionnelle n'est plus supposée :
les groupes supplémentaires peuvent exprimer des contraintes intensives,
n-aires, globales ou propres à l'application.

## Sudoku avec recherche

`sudoku.search.solve_puzzle_with_search` réutilise sans traduction :

- les 81 objets cellules ;
- leurs faits `candidate`, `row`, `column`, `box` et `unit` ;
- les groupes humains sélectionnés ;
- les règles génériques de classification CSP ;
- la règle `CHOICE ... FROM` commune ;
- le trail complet d'`InferenceSession`.

L'oracle est la solution native déjà validée contre le corpus CLIPS. Le test
principal limite volontairement p2 aux Naked Singles. Les règles seules sont
alors incomplètes ; MRV choisit un domaine, les règles propagent et quatre
branches contradictoires sont restaurées avant la solution.

Ce scénario explore 11 nœuds, rencontre 4 contradictions à profondeur 4 et
termine avec 3 décisions sur le chemin solution. Il démontre donc un vrai
backtracking, pas une simple énumération sans échec.

## Harmoniseur note par note

La nouvelle architecture suit les deux phases de la spécification Roy.

### Phase des notes

Chaque couple `(position, voix)` est une variable CSP distincte. Les faits
exposent :

```text
(roy_note_harmonization variable note_0_alto)
(note_0_alto candidate 60)
(note_0_alto voice alto)
(note_0_alto position note_position_0)
```

Le soprano donné devient un domaine singleton. Une politique générique
`PriorityMRVChoicePolicy` impose les phases temporelles puis applique MRV
dans la phase courante.

### Construction différée des voicings

`note_generation.rules` croise les domaines de notes après leur création.
Les règles écrivent explicitement :

- `R-ORDER-001` par trois comparaisons ;
- `R-SPACING-001` à `003` par trois contraintes arithmétiques ;
- la complétude de la triade par un prédicat calculé pur.

La règle produit respectivement 15 et 9 voicings pour la phrase `(67, 72)`,
comme l'oracle historique. Python ne filtre pas ces produits : il ne construit
que les domaines et pilote la frontière entre les deux phases.

### Canalisation et transitions

`note_propagation.rules` maintient un encodage dual :

- un voicing disparaît dès qu'une de ses quatre notes n'est plus candidate ;
- une note disparaît dès qu'aucun voicing ne la supporte.

`note_transition.rules` recherche ensuite un support dans la position voisine.
La conjonction est visible dans la règle :

- mouvement mélodique légal ;
- absence de quintes, octaves et unissons parallèles ;
- mouvement global légal.

Les opérations musicales élémentaires sont des `ComputedPredicate` enregistrés
et purs. Elles testent un couple donné ; elles ne choisissent aucune valeur et
ne pilotent ni propagation ni backtracking.

## Probabilités

Chaque note reçoit une marginale statique. Lorsqu'une note précédente de la
même voix est connue, `update_contextual_note_weights` remplace cette
marginale par une table conditionnelle :

```text
P(note[v,t] | note[v,t-1])
```

Les faits `choice_weight` sont donc branch-locales et restaurés par rollback.
Ils modifient seulement l'ordre des alternatives.

Deux usages sont disponibles :

- best-first déterministe pour les meilleures réalisations ;
- `PriorityWeightedRandomChoicePolicy` pour un tirage pondéré reproductible
  avec une graine.

Les probabilités ne transforment jamais une interdiction en préférence.

## Performances

Mesure du 25 juillet 2026, macOS ARM64, Python 3.13.11, cinq répétitions :

| Cas | Médiane | Nœuds | Échecs | Solutions |
|---|---:|---:|---:|---:|
| Sudoku p2, règles humaines complètes | 294,36 ms | — | 0 | 1 |
| Sudoku p2, Naked Singles + recherche | 1,942 s | 11 | 4 | 1 |
| harmoniseur, choix d'un voicing | 34,92 ms | 13 | 0 | 3 |
| harmoniseur, variables de notes | 145,06 ms | 19 | 0 | 3 |

Le coût supplémentaire est attendu :

- le Sudoku générique remplace une technique humaine très déterminante par
  quatre branches réfutées ;
- l'harmoniseur expose jusqu'à six variables de notes non singleton au lieu
  de deux variables de voicings.

Ces chiffres sont une baseline fonctionnelle, pas encore une cible
d'optimisation.

## Évaluation des mécanismes avancés

### Nogoods

Différés. Le cache d'états élimine déjà les états factuels identiques. Le
Sudoku mesuré ne revisite aucune contradiction, et l'harmoniseur ne rencontre
aucun échec sur les trois premières solutions. Un nogood appris ne serait donc
jamais réutilisé dans ces cas.

### Backjumping

Différé. Les quatre contradictions Sudoku arrivent à la même profondeur 4
dans un arbre de seulement 11 nœuds. Il faut d'abord un problème où une
contradiction possède un sous-ensemble explicable de décisions non
chronologiques.

### Parallélisme

Différé. Les sous-arbres actuels sont trop courts pour amortir sérialisation,
démarrage d'un processus et fusion déterministe. Le protocole reste celui de
`parallel_choice_search.md`.

### Overlays persistants

Différés. Les profils précédents ne placent plus le fork parmi les coûts
dominants. Le modèle note par note est actuellement dominé par les règles de
canalisation et la recherche de supports.

## Prochain incrément musical

Le prochain travail doit enrichir les connaissances, sans changer
l'architecture :

1. degrés et renversements comme variables d'accord ;
2. règles de doublure identifiées `R-DOUBLING-*` ;
3. vocabulaire `R-VOCAB-001` ;
4. cadence et sensible ;
5. tests positif, négatif, limite et exception par identifiant stable.

Un mécanisme avancé de recherche ne sera ajouté que si ces règles produisent
un profil et un oracle qui le justifient.
