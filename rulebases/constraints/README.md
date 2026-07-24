# Contraintes déclaratives

Ce répertoire étudie la construction d'un moteur de propagation de
contraintes au moyen de règles Snarky ordinaires. Variables, domaines,
contraintes et tables de compatibilité sont des faits. Les propagateurs sont
des groupes de règles réutilisables.

```text
constraints/
├── README.md
├── binary/
│   └── ...
└── global/
    └── ...
```

Le premier noyau, [`binary`](binary/README.md), implémente l'arc-consistance
de contraintes binaires tabulaires. Il ne dépend ni de
`ConstraintProblem`, ni de `BacktrackingConstraintSolver`, ni d'une fonction
métier Python.

La base [`global`](global/README.md) exerce les prémisses `NVALUE` et
`ALL_DIFFERENT`. Elle montre le filtrage de cardinalité distincte, des
singletons et des ensembles de Hall sans recherche cachée.

Ce noyau sert aussi de benchmark d'indexation générale. Les grandes mémoires
profitent de rangs stables, d'index paresseux sur les éléments de `SEQ[...]`,
d'un ordre adaptatif dans les recherches de support et de deux témoins
résiduels bornés. Aucun de ces mécanismes ne connaît le vocabulaire CSP.

Il faut distinguer ces contraintes métier réifiées du filtrage interne des
variables d'une règle. La prémisse générique :

```text
CONSTRAINT $x + $y == $z
```

réduit temporairement les domaines d'instanciation sans ajouter ni retirer de
fait métier. Elle convient aux comparaisons et à l'arithmétique locale d'une
règle ; les faits `binary_constraint` restent utiles lorsqu'une contrainte
doit être inspectée, expliquée ou propagée par la base elle-même.

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

1. exposer les choix encore ouverts sous forme de faits `choice` ;
2. connecter ces choix à des sessions hypothétiques avec un backtracking
   explicite et traçable ;
3. ajouter `MEMBER` et `SIZE` pour les contraintes globales locales ;
4. mesurer une éventuelle consistance généralisée de `ALL_DIFFERENT` par
   matching biparti ;
5. comparer ce noyau à un solveur CSP externe servant d'oracle ;
6. mesurer si certaines contraintes réifiées peuvent réutiliser les
   propagateurs internes sans perdre leur provenance explicite.

L'analyse architecturale complète se trouve dans
[`docs/constraints_propagation_and_search.md`](../../docs/constraints_propagation_and_search.md).
