# Extensions générales pour la résolution de problèmes

Ce document regroupe les primitives ajoutées après Sudoku p1–p7 et les
exemples de la thèse. Elles sont toutes optionnelles : le chaînage avant
déterministe historique reste le comportement par défaut.

## Séquences, fenêtres et combinaisons

`FiniteSequence` est un terme immuable ordonné qui conserve les doublons. Sa
forme DSL est `SEQ[a b a]`, distincte du `FiniteSet` `[a b]`.

Une fenêtre est un macro-motif sur une relation de succession :

```text
WINDOW $window := SEQ[$first $second $third] VIA next
```

Cette ligne développe deux prémisses factuelles, puis lie `$window` à la
séquence reconnue. Elle ne suppose aucune notion de temps propre au moteur :
`next` est une relation ordinaire.

`COMBINATIONS` énumère les sous-séquences de taille fixe d'un ensemble ou
d'une séquence :

```text
COMBINATIONS $pair SIZE 2 FROM $window
```

`FOR EACH` applique un bloc d'actions atomique à chaque élément :

```text
FOR EACH $item IN $pair
    ADD ($item selected true)
END_FOR_EACH
```

Les trois stratégies d'instanciation donnent les mêmes substitutions,
supports et faits. Ces constructions servent à la musique, aux traces, aux
réseaux décrits par arcs et aux techniques Sudoku portant sur des groupes de
cases.

## Focus MEA explicite et agenda incrémental

`FOCUS` désigne la prémisse factuelle dont le `timeTag` guide MEA :

```text
FOCUS ($goal status active)
```

Une seule prémisse de premier niveau peut être focalisée. Sans `FOCUS`, le
premier support conserve la sémantique antérieure. Le choix ne dépend donc
plus d'un réordonnancement artificiel des autres prémisses.

`session.inspect_agenda(group)` expose le conflit courant sans le modifier.
Les activations sont mémorisées par règle. Un index conservatif des signatures
positives (`entity`, `relation`, `subject`, `object`, `status`) ne réévalue
après une mutation que les règles potentiellement concernées. Les compteurs
`session.agenda_metrics` distinguent reconstructions, règles recalculées et
règles réutilisées.

Une stratégie comme MEA exige néanmoins de comparer tous les candidats
courants. « Incrémental » signifie ici que leurs activations ne sont pas
rematchées inutilement, pas que la stratégie choisit sans voir le conflit
complet.

## Groupes paramétrés et récursion bornée

`RuleGroupTemplate` spécialise des variables déclarées lors de la construction
d'un groupe. Les variables locales de `BIND`, `COLLECT`, `LET`, `FRESH`,
`COMBINATIONS`, `FOR EACH` et des prédicats calculés ne peuvent pas être des
paramètres : cette séparation évite toute capture ambiguë.

`GroupCall` et `RecursiveGroupProcedure` fournissent un contrôle DFS ou BFS.
La fonction `expand` retourne explicitement les appels suivants et
`max_calls` garantit la terminaison opérationnelle. La récursion appartient à
la couche de contrôle ; une activation de règle demeure atomique et ne lance
pas implicitement un autre groupe.

## Prédicats calculés sûrs

Un `ComputedPredicate` encapsule une fonction pure nommée. Seules les fonctions
présentes dans un `PredicateRegistry` peuvent être appelées depuis le DSL :

```text
COMPUTE $distance := distance ARGS SEQ[$point_a $point_b]
CHECK perpendicular ARGS SEQ[$line_a $line_b]
```

`COMPUTE` doit retourner un terme ground et lie sa cible. `CHECK` doit retourner
un booléen. Les arguments doivent déjà être ground. Il n'y a ni `eval`, ni
résolution dynamique de nom, ni accès implicite à la session.

`type_hierarchy_group()` fournit en complément une fermeture `subtype` et la
propagation `instance_of` sous forme de règles Snarky ordinaires. Les
inférences de type gardent ainsi leur provenance.

## Recherche par hypothèses

`HypothesisSearch` explore en largeur ou en profondeur des `Hypothesis`
produites par une fonction explicite. Chaque enfant est créé avec
`InferenceSession.fork()`, puis ses faits sont ajoutés par `assume()`. Les
groupes choisis saturent la branche avant les tests de contradiction et de
but.

Le résultat conserve le chemin d'hypothèses, le nombre de nœuds explorés et
les chemins rejetés. Aucun backtracking n'est ajouté au moteur de règles :
la session racine n'est jamais modifiée et la politique de choix reste un
objet public.

## CSP et SAT

`ConstraintProblem`, `ConstraintVariable`, `FiniteConstraint` et le protocole
`ConstraintSolver` définissent la frontière avec les solveurs. Le
`BacktrackingConstraintSolver` inclus est un backend fini, déterministe et
portable destiné aux tests et aux petits problèmes.

`SatProblem`, `SatClause` et `SatLiteral` traduisent une formule CNF vers cette
interface. `ConstraintSolution.as_facts()` réinjecte une affectation sous la
forme `(variable assigned valeur)`. Un adaptateur OR-Tools pourra implémenter
le même protocole sans rendre cette dépendance obligatoire.

Cette couche résout des choix finis ; elle ne remplace pas les règles
explicatives. Une architecture hybride typique laisse les règles construire
le problème, appelle un solver, puis laisse d'autres règles interpréter les
faits de solution.

Cette architecture est optionnelle. La base des quatre reines fournit le
contrepoint entièrement déclaratif : une règle fidèle à NéOpus engendre les
quadruplets par jointure, tandis qu'une seconde formulation construit par
chaînage avant un arbre de placements partiels et le filtre au moyen de
relations `attacks`. Aucun solveur n'intervient dans cet exemple.

## Maintenance de vérité optionnelle

`InferenceSession(..., truth_maintenance=True)` active la rétraction en
cascade des conclusions qui n'appartiennent plus à la fermeture des
justifications positives groundées. `session.retract(fact)` supprime le fait,
recalcule la fermeture depuis les faits initiaux et les hypothèses encore
actives, puis journalise les retraits induits.

Le mode est désactivé par défaut. Il couvre les dépendances positives et
élimine correctement les cycles sans support externe. Il ne constitue pas
encore un ATMS : les environnements alternatifs, les nogoods et la provenance
complète des prémisses négatives restent des extensions séparées.

## Classification historique

- `FiniteSequence`, `WINDOW`, `COMBINATIONS`, `FOR EACH`, groupes paramétrés,
  recherche, CSP/SAT et TMS : `MODERN_EXTENSION` ;
- focus explicite et agenda incrémental : clarification et optimisation de
  l'extension MEA, sans prétention à reproduire exactement NéOpus ;
- hiérarchie fournie comme règles : mécanisme moderne, explication ordinaire.

Les garanties communes restent : ordre déterministe, limites explicites,
absence d'évaluation de code textuel, API typée et tests différentiels avec
l'oracle naïf.
