# Jalon CSP générique et harmoniseur note par note

## But

Ce jalon reprend le socle `CHOICE`, propagation et rollback pour construire
deux applications qui exercent réellement les mêmes primitives :

1. un solveur CSP fini générique, validé par un Sudoku nécessitant des choix ;
2. un harmoniseur dont les décisions portent sur les notes SATB et non plus
   sur un voicing opaque, avec n'importe laquelle des quatre voix donnée ;
3. une frontière MuSES qui transforme une `TemporalCollection` en faits et
   les solutions en `Piece` à quatre voix.

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

### Variables de notes et d'harmonie

Chaque couple `(position, voix)` est une variable CSP distincte. Deux
variables supplémentaires choisissent accord et renversement :

```text
(roy_note_harmonization variable note_0_alto)
(note_0_alto candidate 60)
(note_0_alto voice alto)
(note_0_alto position note_position_0)
(note_position_0 chord_variable harmony_0_chord)
(harmony_0_chord candidate degree_I)
(note_position_0 inversion_variable harmony_0_inversion)
(harmony_0_inversion candidate root)
```

La voix donnée devient un domaine singleton ; elle peut être soprano, alto,
ténor ou basse. Une politique générique `PriorityMRVChoicePolicy` applique
MRV à l'intérieur de l'étape courante. Le programme expose les `CHOICE` en
deux étapes : accords d'abord, puis renversements et notes. L'absence de choix
harmonique fait avancer vers la réalisation sans supprimer les points de
retour harmoniques.

### Construction différée des voicings

`note_generation.rules` croise les domaines d'accord, renversement et notes
après leur création.
Les règles écrivent explicitement :

- `R-ORDER-001` par trois comparaisons ;
- `R-SPACING-001` à `003` par trois contraintes arithmétiques ;
- l'appartenance des voix aux hauteurs de l'accord ;
- la basse correspondant au renversement ;
- la complétude de la triade ou de `V7` par `NVALUE`.

Le cas `C5–A4–B4–C5` produit `30, 30, 17, 30` voicings complets, puis
`20, 24, 7, 20` après les règles verticales. La préparation de la forme
parfaite conserve `3, 24, 5, 3` supports avant la recherche. Python construit
le vocabulaire factuel indexé ; la règle effectue les jointures et décide quels sextuplets
`accord–renversement–soprano–alto–ténor–basse` existent.

### Canalisation et transitions

`note_propagation.rules` maintient un encodage lié :

- un voicing disparaît dès qu'une de ses six composantes n'est plus candidate ;
- un accord, renversement ou note disparaît dès qu'aucun voicing ne le
  supporte.

`voice_leading_conformance.rules` décrit chaque paire voisine, produit des
faits `violates R-*`, puis classe les paires sans violation. Les règles
arithmétiques couvrent :

- progression de degrés autorisée ;
- mouvement mélodique légal ;
- absence de quintes, octaves et unissons parallèles ;
- mouvements directs vers les quintes et octaves aux voix extrêmes ;
- résolution de la sensible, de la septième et du `I64`.

`note_transition.rules` recherche ensuite un support légal dans la position
voisine et joint explicitement le `voicing_candidate` encore vivant. Dans ce
profil sans ajout de valeurs, la classification ground est préparée une fois ;
la révision de support reste dans le point fixe de chaque branche. Une
`CHOICE` retire des composantes, la canalisation retire les voicings, puis les
supports sont révisés avant la décision suivante. Aucun `ComputedPredicate`
musical n'est enregistré par ce modèle.

## Probabilités

Chaque note et chaque accord reçoit une marginale statique. Lorsqu'une valeur
précédente est connue, `update_contextual_note_weights` remplace cette
marginale par une table conditionnelle :

```text
P(note[v,t] | note[v,t-1])
P(chord[t] | chord[t-1])
```

Les faits `choice_weight` sont donc branch-locales et restaurés par rollback.
Ils modifient seulement l'ordre des alternatives.

Deux usages sont disponibles :

- best-first déterministe pour les meilleures réalisations ;
- `PriorityWeightedRandomChoicePolicy` pour un tirage pondéré reproductible
  avec une graine.

Les probabilités ne transforment jamais une interdiction en préférence.

## Performances historiques et tonales

Mesure du 25 juillet 2026, macOS ARM64, Python 3.13.11, cinq répétitions :

| Cas | Médiane | Nœuds | Échecs | Solutions |
|---|---:|---:|---:|---:|
| Sudoku p2, règles humaines complètes | 294,36 ms | — | 0 | 1 |
| Sudoku p2, Naked Singles + recherche | 1,942 s | 11 | 4 | 1 |
| harmoniseur, choix d'un voicing | 34,92 ms | 13 | 0 | 3 |
| harmoniseur historique, variables de notes, 2 positions | 145,06 ms | 19 | 0 | 3 |
| harmoniseur tonal enrichi, `I–ii–V7–I`, 4 positions | 896,27 ms | 8 | 0 | 1 |
| pipeline MuSES tonal complet | 910,59 ms | 8 | 0 | 1 |

Le coût supplémentaire est attendu :

- le Sudoku générique remplace une technique humaine très déterminante par
  quatre branches réfutées ;
- l'harmoniseur tonal expose six variables par position, génère les voicings
  de six triades et `V7`, puis propage accords, renversements, doublures,
  résolutions et notes.

Les 145,06 ms historiques et les 896,27 ms tonales ne mesurent pas le même
problème. La frontière MuSES n'ajoute que 14,32 ms (`+1,6 %`). Face au premier
squelette tonal à 962,38 ms, le filtrage des doublures réduit le temps de
6,9 % et les nœuds de 14 à 8.

### Mesure du catalogue de conformité déclaratif

Après remplacement des callbacks musicaux par les faits de violation `R-*`,
une mesure isolée du 25 juillet 2026 donne :

| Cas | Préparation | Recherche | Faits préparés | Nœuds | Échecs |
|---|---:|---:|---:|---:|---:|
| 2 notes, cadence parfaite | 0,307 s | 0,059 s | 1 144 | 3 | 0 |
| 4 notes, `I–ii–V7–I` | 0,984 s | 0,732 s | 4 547 | 8 | 0 |
| 8 notes, rythme `0,1,2,3,4,4,5,6` | 4,428 s | 20,261 s | 14 096 | 57 | 3 |
| 16 notes / 8 mesures, mélodie seule, étapes réversibles | 9,793 s | 9,752 s | — | 28 | 0 |

La dernière ligne est une mesure indicative du 26 juillet 2026 après
suppression du profil harmonique imposé. La préparation matérialise des
chemins et paires de voix afin que chaque
violation reste explicable. Classer ces paires une fois, puis joindre le
candidat voisin vivant pendant la révision, ramène la recherche 8 notes de
68,831 s à 20,261 s sans déplacer de règle musicale en Python. Le coût restant
est celui du catalogue explicable et de ses faits de provenance ; il ne vise
pas la performance d'un solveur d'harmonie spécialisé.

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

## Incrément musical livré et suite

Le modèle couvre désormais `I`, `ii`, `IV`, `V`, `V7`, `vi`, `vii°`,
fondamentale/premier renversement, `I64` cadentiel, les règles de doublure du
sous-ensemble, sensible et septième résolues, quatre profils cadentiels et un
rythme harmonique explicite. Plusieurs notes d'un même événement partagent les
mêmes variables harmoniques. Un plan harmonique optionnel ajoute un degré
factuel par événement ; la règle `remove_chord_outside_harmonic_plan` filtre
le domaine sans imposer les notes ni les renversements. Il n'est pas utilisé
dans l'exemple étendu : les règles filtrent les accords depuis la soprano, la
cadence et les relations `harmonic_successor`, puis l'étape `harmonic_plan`
choisit `I–IV–I–IV–I–IV–ii–V–I` avant l'étape `satb_realization`.

Le prochain travail reste :

1. renversements de `V7` et autres accords de septième ;
2. six-quatre de passage, pédale et arpège ;
3. exceptions complètes de sensible et de doublure ;
4. autres catégories de notes étrangères, métrique, tonalités et modulations ;
5. extension de la matrice positif/négatif/limite/exception déjà livrée pour
   les identifiants du noyau.

Un premier palier de notes étrangères est également livré. Le groupe
`derive_melodic_roles` reconnaît passages conjoints et broderies dans la
soprano donnée. Une note ornementale peut sortir de la triade si les trois
voix inférieures en réalisent toutes les classes. `V7`, suspensions et
dissonances accentuées attendent respectivement une politique d'omission, une
sémantique de préparation/résolution et une force métrique explicite.

Ce palier ne soustrait aucune attaque au problème harmonique. Par défaut,
chaque note reçoit ses propres variables d'accord et de renversement et toutes
les règles s'appliquent normalement ; par exemple, D dans `C-D-E` peut être
une note de l'accord de V. L'interprétation ornementale n'est ouverte que si
le client impose explicitement un événement harmonique partagé.

Un mécanisme avancé de recherche ne sera ajouté que si ces règles produisent
un profil et un oracle qui le justifient.
