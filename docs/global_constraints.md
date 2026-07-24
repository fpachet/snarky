# Contraintes globales

Snarky fournit deux premières contraintes globales au niveau des prémisses :

```text
NVALUE $count OF SEQ[$x $y $z]
ALL_DIFFERENT SEQ[$x $y $z]
```

Elles appartiennent au filtre d'instanciation. Elles réduisent temporairement
les domaines d'une règle avant que le matcher ground produise les activations.
Elles n'ajoutent aucun fait, ne font aucun choix et n'introduisent aucun
backtracking.

## `NVALUE`

`NVALUE N OF SEQ[X1 ... Xk]` réussit lorsque `N` est le nombre de valeurs
distinctes prises par les termes de la séquence.

Le propagateur calcule :

- une borne inférieure depuis les valeurs déjà forcées ;
- une borne supérieure depuis l'union des domaines et l'arité ;
- l'intersection de tous les domaines lorsque `N = 1` ;
- `ALL_DIFFERENT` lorsque `N = k` ;
- l'interdiction de toute nouvelle valeur lorsque la borne inférieure est
  déjà égale à `N`.

Ce filtrage est sûr mais volontairement incomplet. La consistance généralisée
de `NVALUE` est difficile en général ; Snarky privilégie ici un coût borné et
la vérification finale par le matcher.

## `ALL_DIFFERENT`

`ALL_DIFFERENT SEQ[X1 ... Xk]` est sémantiquement équivalent à
`NVALUE k OF SEQ[X1 ... Xk]`, mais possède un filtrage propre :

1. deux singletons égaux produisent une contradiction ;
2. la valeur d'un singleton est retirée des autres domaines ;
3. un sous-ensemble de `p` variables dont l'union contient moins de `p`
   valeurs produit une contradiction ;
4. si cette union contient exactement `p` valeurs, celles-ci sont retirées des
   autres domaines.

Le paramètre `maximum_hall_size`, égal à 3 par défaut, borne l'énumération des
ensembles de Hall. Il couvre les paires et triplets utiles à Sudoku sans
engager le coût d'une consistance généralisée par matching biparti.

## Extension

`DomainPropagator` est un protocole public :

```python
class DomainPropagator(Protocol):
    def accepts(self, premise: ComparisonPremise) -> bool: ...

    def revise(
        self,
        premise: ComparisonPremise,
        domains: MutableMapping[Variable, set[Term]],
        metrics: InstantiationMetrics,
    ) -> set[Variable] | None: ...
```

Un propagateur supplémentaire peut être transmis à
`ConstraintInstantiationStrategy` ou `AdaptiveInstantiationStrategy`. Il doit
être sûr : toute valeur retirée doit être impossible. Retourner `None`
demande au moteur d'essayer un autre propagateur ou le repli cartésien borné.

## Incrémentalité

Les lignes factuelles alimentent des compteurs `(variable, valeur)`. Les
domaines de base ne sont donc pas reprojetés à chaque cycle.

- une suppression ne peut que réduire le point fixe ;
- un ajout peut restaurer une valeur et réinitialise la composante connexe
  touchée ;
- un delta sans ligne pertinente réutilise domaines et candidats.

Les modes `use_incremental_domains=False` et
`use_specialized_comparisons=False` existent uniquement pour les benchmarks
A/B.

Chaque table maintient aussi un masque de lignes présentes et un masque de
supports pour chaque `(variable, valeur)`. Les retraits de valeurs deviennent
des événements bitset locaux ; aucune ligne Python n'est rescannée. Les lignes
actives alimentent directement la jointure, qui n'a plus à rematcher leur
structure. La jointure suit aussi les lignes nouvelles du `FactDelta` et saute
les cycles sans table pertinente. `use_compact_tables=False` et
`use_compact_join=False` conservent les deux anciens chemins uniquement pour
les mesures A/B.

## Limite architecturale

Cette couche est un noyau de propagation, pas encore un solveur CSP.
`DomainStore` et `PropagationState` fournissent déjà réductions,
contradictions et rollback local. Le futur langage de `choice` et son pilote
de backtracking utiliseront cet état et les mêmes propagateurs, comme décrit
dans [`reversible_propagation.md`](reversible_propagation.md) et
[`choice_backtracking_and_applications.md`](choice_backtracking_and_applications.md).

## Références

- F. Pachet et P. Roy, *Automatic Generation of Music Programs* : la contrainte
  `NVALUE` y est introduite comme nombre de valeurs distinctes d'une collection
  de variables ([article CP 1999](https://www.francoispachet.fr/wp-content/uploads/2021/01/pachet-99m.pdf)).
- J.-C. Régin, *A Filtering Algorithm for Constraints of Difference in CSPs* :
  algorithme de consistance généralisée pour `ALL_DIFFERENT`
  ([AAAI 1994](https://m.aaai.org/Library/AAAI/1994/aaai94-055.php)).
