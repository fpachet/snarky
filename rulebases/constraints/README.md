# Contraintes déclaratives

Ce répertoire étudie la construction d'un moteur de propagation de
contraintes au moyen de règles Snarky ordinaires. Variables, domaines,
contraintes et tables de compatibilité sont des faits. Les propagateurs sont
des groupes de règles réutilisables.

```text
constraints/
├── README.md
└── binary/
    ├── README.md
    ├── rules.rules
    ├── initial_facts.yaml
    ├── expected_facts.yaml
    └── scenario.yaml
```

Le premier noyau, [`binary`](binary/README.md), implémente l'arc-consistance
de contraintes binaires tabulaires. Il ne dépend ni de
`ConstraintProblem`, ni de `BacktrackingConstraintSolver`, ni d'une fonction
métier Python.

## Conventions

Un problème référence ses variables :

```text
(problem variable x)
(x kind csp_variable)
(x candidate red)
(x candidate blue)
```

Une relation binaire contient les couples autorisés :

```text
(different-colors kind binary_relation)
(different-colors allows SEQ[red blue])
(different-colors allows SEQ[blue red])
```

Une contrainte applique cette relation à deux variables :

```text
(constraint-1 kind binary_constraint)
(constraint-1 problem problem)
(constraint-1 relation different-colors)
(constraint-1 left x)
(constraint-1 right y)
```

Les domaines ne font que décroître. Chaque retrait reste un événement
Snarky ordinaire et possède donc une provenance.

## Étapes suivantes

1. exposer les choix encore ouverts sous forme de faits ;
2. connecter ces choix à des sessions hypothétiques ;
3. ajouter `MEMBER` et `SIZE` pour les contraintes globales locales ;
4. définir `ALL_DIFFERENT` et les sous-ensembles de Hall ;
5. comparer ce noyau à un solveur CSP externe servant d'oracle.

L'analyse architecturale complète se trouve dans
[`docs/constraints_propagation_and_search.md`](../../docs/constraints_propagation_and_search.md).
