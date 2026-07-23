# Groupes de règles et sessions d’inférence

Snarky permet de regrouper des règles sous un nom et d’appeler plusieurs
groupes successivement dans une même session d’inférence. Cette fonctionnalité
est une `MODERN_EXTENSION` inspirée de la notion d’« expertise » de SHAL.

Une session conserve entre les appels :

- la mémoire de travail, donc tous les faits ajoutés ;
- la réfraction, afin de ne pas déclencher deux fois la même règle avec la
  même substitution dans un même groupe ;
- les index et deltas utilisés par l’évaluation semi-naïve ;
- la provenance, enrichie du nom du groupe qui a produit chaque dérivation.

## Déclaration

Les groupes peuvent être construits avec l’API Python :

```python
from snarky import RuleGroup

preparation = RuleGroup("preparation", (rule_a, rule_b))
resolution = RuleGroup("resolution", (rule_c, rule_d))
```

Le DSL accepte également des blocs `GROUP` :

```text
GROUP preparation
    RULE make_candidate
    WHEN
        problem
    THEN
        ADD candidate
    END
END_GROUP

GROUP resolution
    RULE accept_candidate
    WHEN
        candidate
    THEN
        ADD solution
    END
END_GROUP
```

Ils sont lus par `parse_rule_groups`. Les noms de groupes doivent être uniques
dans le texte et les noms de règles doivent être uniques à l’intérieur d’un
groupe.

## Exécution persistante

```python
from snarky import ForwardEngine, parse_rule_groups

preparation, resolution = parse_rule_groups(source)
session = ForwardEngine(()).create_session(initial_facts)

session.run_group(preparation)
session.run_group(resolution)
result = session.snapshot()
```

`ForwardEngine(rules).run(facts)` reste disponible et conserve sa sémantique
antérieure : les règles constituent alors un groupe implicite nommé
`default`, saturé jusqu’au point fixe dans une session neuve.

Un nom de groupe désigne une définition stable pendant toute la session.
Présenter plus tard un groupe différent sous le même nom provoque une erreur,
car cela rendrait la réfraction et les deltas ambigus.

## Modes d’appel

`InferenceSession.run_group` accepte quatre valeurs de `GroupExecutionMode` :

- `SATURATE` : enchaînement avant jusqu’au point fixe ;
- `ONE_CYCLE` : un seul balayage ordonné des règles, puis retour ;
- `FIRST_CHANGE` : retour après la première activation qui ajoute au moins un
  fait ;
- `UNTIL` : enchaînement jusqu’à ce qu’une condition d’arrêt soit satisfaite,
  ou jusqu’au point fixe si elle ne peut pas l’être.

Un « cycle » est un balayage des règles dans leur ordre de déclaration. Une
règle située plus loin dans le groupe voit les faits ajoutés par les règles
précédentes pendant le même cycle.

`FIRST_CHANGE` et `UNTIL` respectent l’atomicité d’une activation : toutes les
actions d’une règle sont exécutées avant de tester l’arrêt. Cela évite de
laisser une conclusion partiellement produite.

## Arrêt sur un but

`FactExists` est la première condition déclarative fournie par Snarky. Elle
réussit si un fait de la session correspond à un motif :

```python
from snarky import FactExists, GroupExecutionMode, parse_term, when

result = session.run_group(
    resolution,
    mode=GroupExecutionMode.UNTIL,
    until=FactExists(when(parse_term("($problem state solved)"))),
)
```

Le test est effectué avant tout déclenchement, puis après chaque activation
complète. Le résultat indique pourquoi l’appel s’est arrêté au moyen de
`stop_reason` : `condition_met`, `fixed_point`, `one_cycle` ou
`first_change`.

Une condition Python respectant l’interface `StopCondition` peut aussi être
utilisée. Cette ouverture sert à expérimenter de nouveaux contrôles ; les
conditions générales et réutilisables ont vocation à devenir des objets
déclaratifs du moteur, comme `FactExists`.

## Portée actuelle

Les groupes organisent et pilotent le chaînage avant monotone existant. Ils ne
constituent pas encore un langage de plans SHAL complet : il n’existe pas
encore de DSL pour enchaîner conditionnellement des groupes, gérer un échec,
faire du retour arrière ou appeler un solveur de contraintes.

Cette séparation est intentionnelle. Les stratégies de résolution peuvent
d’abord rester de petits orchestrateurs Python appelant des groupes de règles
déclaratifs. Les séquences qui se révèlent générales et stables pourront
ensuite être représentées par un langage de plans, sans déplacer la logique
métier des règles vers Python.

Le [projet Sudoku](../sudoku/README.md) sert de premier cas d’étude pour cette
architecture : chaque technique humaine est un groupe, et un orchestrateur
générique les appelle par difficulté croissante avant de recommencer au
premier groupe après chaque progrès.
