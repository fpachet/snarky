# Fibonacci explicite

Cette base d'ordre 1 calcule `F(8) = 21` avec exactement trois règles :

1. `fibonacci_base` donne la valeur 1 aux rangs 1 et 2 ;
2. `fibonacci_creer_fils` crée explicitement les calculs `F(n - 1)` et
   `F(n - 2)` ;
3. `fibonacci_additionner` attend les deux résultats et les additionne.

Il ne s'agit pas d'une version mémoïsée. Chaque fils est un terme structurel
qui contient son parent et sa branche. Deux occurrences de `F(5)` situées à
des endroits différents de l'arbre sont donc deux nœuds différents. Pour
`F(8)`, la base construit 41 nœuds de calcul : 20 nœuds internes et 21
feuilles.

Le petit DSL Snarky ne possède pas encore d'expressions arithmétiques. Les
relations `predecesseur` et `plus` sont donc des faits initiaux. Le statut du
fait `(a plus b)` porte la somme numérique :

```text
(1 plus 1) ' 2
```

La graine du calcul est :

```text
(racine fibonacci 8)
```

Au point fixe, on obtient notamment :

```text
(racine resultat 21)
```

Pour tester un autre rang, modifier la graine et compléter au besoin les faits
`predecesseur` et `plus`. Le nombre de nœuds construits satisfait
`T(1) = T(2) = 1` et `T(n) = 1 + T(n - 1) + T(n - 2)`.

## Test de charge `F(10)`

Le programme [`benchmarks/fibonacci_explicit.py`](../../../benchmarks/fibonacci_explicit.py)
génère automatiquement les faits arithmétiques nécessaires pour un rang
quelconque. Pour `F(10)`, il construit 109 nœuds et atteint 343 faits.

Sur la machine de développement, trois exécutions donnent en moyenne 8,800 s
avec la stratégie naïve et 0,267 s avec la stratégie indexée, soit un gain de
×32,9. Voir la [documentation des benchmarks](../../../benchmarks/README.md)
pour la commande exacte et les compteurs algorithmiques.
