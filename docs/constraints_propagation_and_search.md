# Contraintes, propagation et recherche dans Snarky

Ce document distingue les différentes manières de combiner règles,
contraintes et recherche. Elles ne répondent pas au même besoin et ne doivent
pas être confondues sous le seul terme de « CSP ».

L'objectif architectural reste le suivant : conserver la connaissance du
domaine dans des règles et des faits explicables, et ne placer dans Python que
des mécanismes généraux d'exécution.

## État actuel

Snarky possède déjà :

- un matching de prémisses par jointures indexées et propagation des
  substitutions ;
- des candidats explicites et des éliminations par règles dans Sudoku ;
- `COLLECT`, `COMBINATIONS` et `FOR EACH` pour de petites constructions
  combinatoires ;
- `InferenceSession.fork()` pour isoler une branche ;
- `HypothesisSearch` pour explorer explicitement des hypothèses produites par
  une fonction ;
- `ConstraintProblem`, `ConstraintSolver` et un backend fini de référence ;
- une traduction SAT élémentaire vers cette interface.
- une première `ConstraintInstantiationStrategy` hybride qui filtre les
  domaines de règles positives avant de confier l'énumération au matcher
  indexé existant.

Les deux dernières infrastructures ne sont utilisées que dans leurs tests.
Elles ne pilotent aucune base de règles principale. `HypothesisSearch`
demande encore une fonction Python pour engendrer les hypothèses.

La propagation existe en revanche déjà sous une forme spécialisée : Sudoku
représente chaque valeur possible par un fait `candidate`, puis les règles
retirent les candidats impossibles jusqu'au point fixe.

Le premier noyau générique est maintenant exécutable dans
[`rulebases/constraints/binary`](../rulebases/constraints/binary/README.md).
Deux règles symétriques y établissent l'arc-consistance de contraintes
binaires tabulaires. Une chaîne bicolore est entièrement résolue par
propagation ; un triangle à trois couleurs est réduit à deux domaines de deux
valeurs puis reste volontairement non résolu.

## Les niveaux d'intégration possibles

| Niveau | Question résolue | Effet sur le langage |
|---|---|---|
| CSP pour l'instanciation | Comment trouver plus vite les substitutions d'une règle ? | aucun si la sémantique reste identique |
| Clauses combinatoires | Comment énumérer et filtrer des choix locaux ? | nouvelles prémisses génériques |
| Propagation réifiée | Comment réduire les domaines sans faire de choix ? | contraintes représentées par des faits |
| Recherche par branches | Que faire lorsque la propagation est bloquée ? | protocole déclaratif de choix |
| Solveur externe | Comment obtenir rapidement une solution globale ? | frontière hybride explicite |
| ATMS | Comment maintenir plusieurs mondes simultanément ? | nouvelle sémantique de justification |

## 1. CSP comme stratégie d'instanciation

Une partie gauche de règle est déjà assimilable à un petit problème de
contraintes :

```text
($x relation $y)
($y property $z)
$x != $z
```

Les faits déterminent les domaines possibles et les prémisses contraignent
les substitutions. Le matcher actuel résout ce problème comme une suite de
jointures.

Cette lecture n'est pas une analogie moderne ajoutée après coup. Elle reprend
le principe central de BOOJUM décrit par Dormoy dans
[*Amélioration de l'efficacité du pattern matching dans le langage à base de
règles BOOJUM*](https://dormoy.org/JLuc/Papers/Boojum89.pdf) : examiner une
règle à la fois, associer un domaine à chacune de ses variables, propager les
contraintes, puis choisir la variable la plus contrainte. Le « second moteur »
de BOOJUM pousse cette idée jusqu'à la consistance d'arcs. En revanche,
conserver les tables entre deux examens et les mettre à jour par `FactDelta`
est une adaptation moderne de Snarky.

### Premier palier livré : filtrage hybride

`ConstraintInstantiationStrategy` réalise maintenant :

1. compiler une fois la partie gauche ;
2. représenter chaque prémisse factuelle comme une contrainte tabulaire ;
3. construire des domaines de `Term`, relations et propositions comprises ;
4. placer les propagateurs de tables dans une file de révision ;
5. ne réveiller après une réduction que les contraintes voisines dans le
   graphe d'incidence variable–prémisse ;
6. filtrer aussi une comparaison lorsque son produit de domaines reste
   explicitement borné ;
7. transmettre au matcher compilé les listes de faits encore compatibles ;
8. conserver les faits supports et la provenance ordinaires ;
9. mettre les tables à jour après ajouts et suppressions, puis recalculer le
   point fixe afin qu'un ajout puisse réélargir un domaine.

Cette stratégie devrait produire exactement les mêmes activations que le
matcher naïf. Elle constitue donc une optimisation interchangeable, pas une
nouvelle sémantique.

Le filtre est volontairement **sûr mais incomplet** : il peut laisser au
matcher une valeur qui échouera plus tard, mais ne doit jamais éliminer une
activation valable. La première version accepte les règles composées
uniquement de prémisses factuelles positives et de comparaisons dont toutes
les variables proviennent des faits. `EXISTS`, `NOT EXISTS`, agrégats,
liaisons calculées et combinatoires déclenchent automatiquement le repli sur
`SemiNaiveInstantiationStrategy`.

Ce palier n'introduit aucun nouveau backtracking. Le matcher actuel termine
l'énumération avec son `BindingFrame` et son trail local. Il ne copie ni ne
restaure la mémoire de travail.

### Incrémentalité et limites actuelles

Les tables extensionales sont persistantes par règle :

- un ajout n'est matché que contre les prémisses de cette règle ;
- une suppression enlève directement la ligne correspondante ;
- les projections `(variable, valeur)` sont maintenues par compteurs ;
- une suppression repart du point fixe précédent ;
- un ajout réinitialise seulement la composante connexe susceptible de
  s'élargir ;
- un delta sans ligne pertinente réutilise le résultat filtré.

Cette solution reste correcte en présence d'élargissements de domaines. Les
tables n'utilisent cependant plus le scan historique : chaque ligne possède
un slot, chaque `(variable, valeur)` le masque de ses lignes supports et la
table un masque actif. Une valeur retirée produit un événement local qui
désactive son masque. La vérification d'un support devient une intersection
de grands entiers Python.

Les métriques distinguent le coût préparatoire
(`domain_match_attempts`, tables, révisions et valeurs retirées) des
`match_attempts` du matcher final. `domain_bitset_value_events`,
`domain_bitset_support_checks`, `domain_bitset_intersections` et
`domain_compact_join_rows` décrivent le nouveau chemin.

Les métriques `domain_projection_rows_examined`,
`domain_projection_updates`, `domain_state_reuses` et
`domain_component_resets` isolent le coût de construction. Sur Sudoku p1,
p6 et p7, les projections relues baissent de 93,7 à 95,9 %, mais le temps
total seulement de 1 à 2 %. Ce résultat a écarté les bitsets pour la
construction des domaines, mais pas pour les révisions et la jointure, qui
constituaient le coût suivant.

### Compact-Tables et jointure directe

Après construction, les prémisses factuelles ne sont plus matchées une seconde
fois. La jointure intersecte le masque actif avec les masques des variables
déjà liées, parcourt seulement les slots restants et copie leurs liaisons
prévalidées dans le `BindingFrame`.

Sur sept répétitions :

| Scénario | Scan | Bitset seul | Bitset + jointure | Gain total |
|---|---:|---:|---:|---:|
| Sudoku p1 | 0,377 s | 0,358 s | 0,287 s | ×1,31 |
| Sudoku p6 | 0,656 s | 0,640 s | 0,576 s | ×1,14 |
| Sudoku p7 | 0,926 s | 0,907 s | 0,804 s | ×1,15 |
| `NVALUE`, taille 200 | 2,302 ms | 2,062 ms | 2,061 ms | ×1,12 |
| quatre reines | 117,44 ms | 116,78 ms | 104,06 ms | ×1,13 |

Le filtre bitset supprime tous les rescans — 15 467, 18 187 et 21 588 lignes
sur les trois Sudoku — mais son gain isolé reste modeste. La jointure directe
apporte la majeure partie de l'accélération en supprimant les recherches
d'index et le matching structurel redondants. Les données sont dans
[`../benchmarks/results/compact_tables_2026-07-24.csv`](../benchmarks/results/compact_tables_2026-07-24.csv).

### Intérêt attendu

Le bénéfice sera probablement faible pour deux ou trois triplets bien
indexés. Il peut devenir important avec :

- de nombreuses variables croisées ;
- des motifs de graphes fortement connectés ;
- `ALL_DIFFERENT` ;
- des contraintes arithmétiques ;
- des domaines fortement réductibles avant leur énumération.

Le benchmark `benchmarks.constraint_instantiation` utilise deux relations
denses et une troisième contrainte très sélective placée en dernier. À taille
40, le filtrage réduit les tentatives du matcher final de 65 640 à 120 ; la
construction des tables demande séparément 3 201 matchings. La médiane passe
de 193,0 ms à 17,2 ms, soit ×11,2. À taille 80, elle passe de 1,518 s à
67,4 ms, soit ×22,5. Ce cas valide le mécanisme, sans prétendre que toute
règle courte en bénéficiera.

`AdaptiveInstantiationStrategy` ajoute un sélecteur conservateur. Il vérifie
la taille des tables, la différence de sélectivité entre buckets et la
présence d'un cycle dans le graphe biparti variables–prémisses. Après un
premier filtrage candidat, il exige également une réduction minimale des
lignes. Les comparaisons simples et les égalités arithmétiques binaires ont
maintenant des propagateurs spécialisés et peuvent être sélectionnées. Les
formes imbriquées ou non spécialisées restent disponibles dans la stratégie
forcée avec un produit cartésien borné. La décision est mémorisée par règle ;
le repli est semi-naïf.

La prémisse `CONSTRAINT expression opérateur expression` réutilise l'AST
arithmétique sûr de `LET`. Contrairement à `LET`, elle est relationnelle :
`CONSTRAINT $x + $y == $z` filtre `$x`, `$y` et `$z`. Pour l'addition et la
soustraction, le propagateur choisit la paire de domaines au plus petit
produit et déduit la troisième valeur. Multiplication, division et modulo
énumèrent encore les deux opérandes, jamais le cube avec le résultat.

La même famille accueille les contraintes globales :

```text
NVALUE $count OF SEQ[$x $y $z]
ALL_DIFFERENT SEQ[$x $y $z]
```

Le protocole public `DomainPropagator` choisit un propagateur pour une
`ComparisonPremise` et révise les domaines sans produire d'activation.
`NVALUE` borne le nombre de valeurs distinctes par les valeurs déjà forcées et
l'union des domaines. Les cas `N = 1` et `N = arité` déclenchent
respectivement une intersection globale et `ALL_DIFFERENT`.
`ALL_DIFFERENT` propage les singletons et les ensembles de Hall de taille deux
ou trois. Le matcher ground réévalue toujours la contrainte complète : un
filtrage volontairement incomplet ne peut donc pas créer de solution fausse.

Les scénarios neutre et défavorable confirment l'intérêt de cette garde. Sur
une jointure alignée de 600 faits, l'indexé et l'adaptatif prennent
respectivement 2,826 et 2,818 ms, alors que le filtrage forcé prend 5,063 ms.
Sur un triangle dense sans réduction, le surcoût adaptatif reste dans le
bruit de mesure (environ 0,3 % sur la série courante).

### Propagateurs en file

Une chaîne de 40 contraintes met en évidence le coût du point fixe lui-même :

| Variante | Révisions | Lignes examinées | Médiane |
|---|---:|---:|---:|
| balayages complets | 1 722 | 67 242 | 43,06 ms |
| file de propagateurs | 122 | 4 802 | 8,71 ms |

La file divise donc le temps de filtrage par ×4,95 et le travail structurel
par ×14. La chaîne reste néanmoins mieux traitée par la jointure indexée
(6,74 ms), car elle est acyclique et fonctionnelle. Le sélecteur la détecte
et conserve 6,41 ms sans construire les domaines.

### Paliers suivants

1. ~~ajouter des tests différentiels sur des programmes positifs générés ;~~
2. ~~sélectionner automatiquement les règles où le filtrage amortit son
   coût ;~~
3. ~~maintenir les projections et domaines entre les cycles ;~~
4. ~~ajouter une interface de propagateur global, `NVALUE` et
   `ALL_DIFFERENT` avec Hall borné ;~~
5. ~~mémoriser les supports par valeur en Compact-Tables et les réutiliser
   dans la jointure ;~~
6. généraliser les index de chemins aux triples imbriqués d'ordre 2 ;
7. mesurer une consistance généralisée de `ALL_DIFFERENT` par matching
   biparti seulement sur un cas probant ;
8. remplacer éventuellement l'énumération finale par le choix MRV et un trail
   local, sans toucher à `InferenceSession` ;
9. traiter séparément les choix métier et la recherche par sessions.

Appeler un solveur complet à chaque cycle ou activation resterait au contraire
trop coûteux et compliquerait la provenance. Un backend externe conserve son
rôle d'oracle ou de moteur optionnel de recherche globale.

## 2. Clauses combinatoires dans les règles

La primitive actuelle :

```text
COMBINATIONS $pair SIZE 2 FROM $candidates
```

lie successivement `$pair` à chaque sous-séquence de deux éléments. Une
prémisse suivante peut filtrer cette combinaison comme n'importe quel terme.
Dans la conclusion :

```text
FOR EACH $member IN $pair
    ADD ($pair member $member)
END_FOR_EACH
```

exécute le bloc pour chacun de ses éléments.

### Exemple exécutable : binômes compatibles

La base
[`rulebases/small/combinations_foreach`](../rulebases/small/combinations_foreach/README.md)
part des faits :

```text
(workshop candidates [alice bob chloe])
(SEQ[alice bob] compatible true)
(SEQ[bob chloe] compatible true)
```

Sa règle est :

```text
RULE generate_compatible_pairs
WHEN
    ($workshop candidates $candidates)
    COMBINATIONS $pair SIZE 2 FROM $candidates
    ($pair compatible true)
THEN
    ADD ($pair kind working_pair)
    ADD ($pair workshop $workshop)
    FOR EACH $member IN $pair
        ADD ($pair member $member)
    END_FOR_EACH
END
```

`COMBINATIONS` engendre les trois choix possibles. La troisième prémisse ne
conserve que les deux choix déclarés compatibles. `FOR EACH` matérialise
ensuite les deux membres de chaque binôme.

Ce petit exemple montre la sémantique actuelle complète : génération,
filtrage factuel, actions itérées et provenance.

### Cas probant visé : naked triples de Sudoku

Pour exprimer directement les naked triples, l'algèbre de collections doit
être complétée :

```text
COLLECT $unsolved := $cell
    ($unit contains $cell)
    NOT EXISTS
        ($cell value $value)
    END_EXISTS
END_COLLECT

COMBINATIONS $cells SIZE 3 FROM $unsolved

COLLECT $values := $value
    MEMBER $cell IN $cells
    ($cell candidate $value)
END_COLLECT

SIZE $values == 3
```

Le sens est : choisir trois cases et vérifier que l'union de leurs candidats
contient exactement trois valeurs. Les actions retirent ensuite ces valeurs
des autres cases de l'unité.

Deux prémisses génériques suffiraient vraisemblablement :

- `MEMBER $item IN $collection` et sa négation éventuelle ;
- `SIZE $collection <op> n`.

`COLLECT` peut alors effectuer l'union sans primitive `UNION` particulière.
Ce cas doit guider la conception : il correspond à une technique humaine,
locale, bornée et explicable de Sudoku p8.

## 3. Contraintes réifiées et propagation par règles

Une contrainte peut devenir un objet ordinaire de la mémoire :

```text
(q1 candidate 1)
(q1 candidate 2)
(q2 candidate 1)
(q2 candidate 2)

(constraint-1 kind different)
(constraint-1 left q1)
(constraint-1 right q2)
```

Un groupe générique propage alors les affectations :

```text
RULE propagate_different
WHEN
    ($constraint kind different)
    ($constraint left $assigned)
    ($constraint right $other)
    ($assigned value $value)
    ($other candidate $value)
THEN
    REMOVE ($other candidate $value)
END
```

D'autres groupes peuvent reconnaître :

- un domaine singleton ;
- un domaine vide et donc une contradiction ;
- des contraintes binaires ;
- `ALL_DIFFERENT` ;
- des sous-ensembles de Hall ;
- des bornes arithmétiques simples.

Cette architecture généralise le fonctionnement actuel de Sudoku. Chaque
réduction de domaine demeure une mutation Snarky, avec événement et
provenance. Elle pourrait être réutilisée pour les reines, la coloration de
graphes, les carrés latins et les problèmes d'affectation.

### Noyau binaire réalisé

Le groupe `propagate_binary_constraints` applique déjà cette architecture à
des relations définies par leurs couples `allows`. Il retire une valeur à
gauche ou à droite lorsqu'un bloc `NOT EXISTS` ne trouve plus aucun support
dans le domaine opposé.

Les tests exécutent les mêmes règles avec les stratégies naïve, indexée et
semi-naïve. Ils vérifient :

- les affectations alternées de la chaîne ;
- les suppressions de candidats des cas résolu, incomplet et contradictoire ;
- la reconnaissance du problème résolu ;
- la conservation des quatre candidats encore cohérents du triangle ;
- l'absence de faux fait `solved` pour ce triangle ;
- la détection de deux domaines vides dans une paire impossible.

### Optimisations générales révélées par la propagation

La montée en taille de ce noyau a conduit à quatre optimisations du matcher,
sans primitive CSP spécialisée :

1. les rangs d'insertion de `FactIndex` restent stables après un retrait ;
2. les grandes mémoires utilisent un ensemble ordonné pour retirer un fait
   sans reconstruire la séquence active, tandis que les petites conservent la
   liste plus compacte ;
3. un pattern partiellement lié comme
   `SEQ[$left_value $right_value]` demande à la volée un index composé sur les
   chemins résolus de la structure ;
4. les blocs existentiels factuels choisissent le plus petit bucket et
   conservent au plus deux témoins résiduels.

Les mêmes signatures structurelles indexent les watchers. Un ajout portant
sur un autre élément de séquence ne réveille donc pas une corrélation
incompatible.

Les gardes sont empiriques : les index structurels ne sont construits que si
le meilleur bucket top-level dépasse huit faits ; l'ordre adaptatif et les
témoins alternatifs ne sont activés qu'à partir de 128 faits ; l'ensemble
ordonné global est retenu à partir de 1 500 faits initiaux. Ces seuils
n'affectent jamais les résultats.

Sur la chaîne d'égalité 64×64, ces mécanismes réduisent les matchings de
560 196 à 310 212 et le temps de 2,566 s à 1,684 s, soit ×1,52. Un benchmark
séparé de disparition des supports réduit les invalidations de 64 à 32 et les
matchings de 2 275 à 1 253 grâce aux témoins résiduels.

Les scripts reproductibles sont
[`constraint_scaling.py`](../benchmarks/constraint_scaling.py) et
[`constraint_support_churn.py`](../benchmarks/constraint_support_churn.py).
Ces résultats indiquent que l'infrastructure générale suffit encore pour la
propagation binaire étudiée. Une file AC-3 spécialisée n'est donc pas ajoutée
à ce stade.

## 4. Recherche et backtracking explicites

La propagation peut atteindre un point fixe sans résoudre le problème. Les
règles devraient alors produire un choix réifié :

```text
(choice-1 kind choice)
(choice-1 variable r3c7)
(choice-1 alternative 2)
(choice-1 alternative 8)
```

Un orchestrateur générique :

1. sature les groupes de propagation ;
2. teste les motifs `solved` et `contradiction` ;
3. lit un choix produit par les règles ;
4. crée une session fille par alternative ;
5. ajoute l'alternative comme hypothèse nommée ;
6. reprend la propagation dans chaque branche.

La connaissance du domaine reste déclarative : les règles décident quelle
variable choisir, quelles alternatives proposer et ce qui constitue une
contradiction. Le contrôleur ne connaît que le protocole général.

Ce modèle ne revient pas en arrière en annulant des mutations. Chaque branche
est une session isolée possédant ses hypothèses, événements, contradictions
et preuves. `HypothesisSearch` fournit déjà le parcours BFS/DFS et les limites,
mais son générateur Python doit être remplacé ou complété par cet adaptateur
de choix factuels.

## 5. Solveur CSP externe

Un solveur externe reste utile pour :

- servir d'oracle à une base déclarative ;
- vérifier le nombre de solutions ;
- générer des problèmes et contre-exemples ;
- comparer les performances ;
- terminer rapidement un problème après une réduction importante des
  domaines ;
- fournir un mode opérationnel lorsque l'explication n'est pas prioritaire.

Une solution CSP réinjectée doit conserver une origine explicite, par exemple
`solver_assumption`. Elle n'est pas une preuve produite par les règles et ne
doit pas être présentée comme telle.

L'interface `ConstraintSolver` existante constitue cette frontière. Un
adaptateur OR-Tools peut être ajouté ultérieurement sans modifier les bases
qui ne le demandent pas.

## 6. ATMS

Un ATMS associerait chaque fait aux ensembles d'hypothèses sous lesquels il
est vrai et maintiendrait des ensembles incompatibles, ou *nogoods*. Il
éviterait certaines copies de sessions et représenterait plusieurs mondes
simultanément.

Cette solution est élégante pour l'explication, mais elle affecte
profondément :

- la provenance ;
- la négation ;
- la réfraction ;
- les agrégats ;
- l'égalité des états ;
- la consommation mémoire.

Elle doit venir après une première recherche explicite par sessions, dont les
résultats fourniront un oracle de comportement.

## Séquence recommandée

1. ~~Implémenter un noyau générique de domaines et d'arc-consistance
   binaire.~~
2. Produire un fait `choice` pour le triangle non résolu et le connecter à un
   orchestrateur générique de sessions.
3. Ajouter `MEMBER` et `SIZE`.
4. Implémenter les naked triples de Sudoku avec `COMBINATIONS`.
5. ~~Ajouter `ALL_DIFFERENT` et les sous-ensembles de Hall au noyau de
   propagation.~~
6. Valider la recherche sur un Sudoku nécessitant réellement une hypothèse.
7. Expérimenter une stratégie d'instanciation CSP sur un benchmark de
   jointures fortement contraintes.
8. Garder les solveurs externes comme backends optionnels et oracles.
9. N'étudier un ATMS qu'avec les traces et mesures obtenues aux étapes
   précédentes.

## Critères communs

Toute extension retenue devra :

- rester déterministe à stratégie fixée ;
- conserver des limites explicites ;
- expliquer les faits ajoutés et candidats retirés ;
- distinguer déduction, hypothèse et résultat externe ;
- être comparée au matcher naïf ou à un oracle indépendant ;
- disposer d'au moins une base de règles réelle, pas seulement d'un test
  artificiel ;
- mesurer activations, substitutions intermédiaires, faits, mémoire et temps.
