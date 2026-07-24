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

Les rangs et les sommes sont calculés par des actions arithmétiques `LET` dans
la conclusion des règles :

```text
LET $n_moins_1 := $n - 1
LET $n_moins_2 := $n - 2
LET $somme := $gauche + $droite
```

Les actions sont séquentielles : chaque liaison est disponible pour les `LET`
et `ADD` qui la suivent. Aucun fait `predecesseur` ou `plus` n'est nécessaire.

La graine du calcul est :

```text
(racine fibonacci 8)
```

Au point fixe, on obtient notamment :

```text
(racine resultat 21)
```

Pour tester un autre rang, il suffit de modifier la graine. Le nombre de nœuds
construits satisfait
`T(1) = T(2) = 1` et `T(n) = 1 + T(n - 1) + T(n - 2)`.

## Tests de charge

Le programme [`benchmarks/fibonacci_explicit.py`](../../../benchmarks/fibonacci_explicit.py)
ne fournit au moteur que la graine `(racine fibonacci n)`. Son calcul Python de
Fibonacci sert uniquement à vérifier le résultat final. Pour `F(10)`, Snarky
construit 109 nœuds et atteint 326 faits.

Les premières mesures indexées et semi-naïves sont conservées comme séries
historiques dans la
[documentation des benchmarks](../../../benchmarks/README.md). Elles ne
doivent pas être confondues avec l’état courant.

Après compilation des plans de réfraction négative, une base comme Fibonacci,
qui n’en contient aucune, évite entièrement cette réconciliation après les
ajouts. Les médianes courantes vont de 0,338 s pour `F(15)` à 8,791 s pour
`F(20)` ; `F(21) = 10 946` prend 12,309 s sur un passage avec 65 672 faits.
`F(20)` est donc le dernier rang observé sous 10 secondes et `F(21)` reste sous
30 secondes. `F(22)` dépasserait la garde par défaut de 100 000 faits.

Le benchmark accepte un rang ou une plage inclusive :

```sh
uv run python benchmarks/fibonacci_explicit.py \
    --range 15 21 --repeat 3 --strategy semi-naive
```
