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

Une future `ConstraintInstantiationStrategy` pourrait :

1. compiler une fois la partie gauche ;
2. représenter chaque prémisse factuelle comme une contrainte tabulaire ;
3. propager égalités, inégalités et domaines ;
4. énumérer seulement les substitutions restantes ;
5. conserver pour chaque activation ses faits supports et sa provenance ;
6. mettre à jour les domaines incrémentalement après une mutation.

Cette stratégie devrait produire exactement les mêmes activations que le
matcher naïf. Elle constituerait donc une optimisation, pas une nouvelle
sémantique.

### Intérêt attendu

Le bénéfice sera probablement faible pour deux ou trois triplets bien
indexés. Il peut devenir important avec :

- de nombreuses variables croisées ;
- des motifs de graphes fortement connectés ;
- `ALL_DIFFERENT` ;
- des contraintes arithmétiques ;
- des domaines fortement réductibles avant leur énumération.

Un premier benchmark contrôlé pourrait reconnaître des cliques de taille
fixe ou instancier une règle directe des huit reines. L'implémentation ne
devrait être retenue que si elle réduit effectivement le nombre de
substitutions intermédiaires et le temps total. Appeler un solveur complet à
chaque cycle ou activation serait au contraire trop coûteux.

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
5. Ajouter `ALL_DIFFERENT` et les sous-ensembles de Hall au noyau de
   propagation.
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
