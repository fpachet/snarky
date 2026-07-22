# Actions arithmétiques `LET`

Snarky évalue les expressions arithmétiques déterministes dans la conclusion
d'une règle. Elles ne constituent pas des prémisses : elles servent à calculer
des valeurs locales nécessaires aux actions suivantes.

## Syntaxe

```text
LET $variable := expression
```

La grammaire des expressions est :

```text
expression  ::= produit (("+" | "-") produit)*
produit     ::= unaire (("*" | "/") unaire)*
unaire      ::= ("+" | "-") unaire | primaire
primaire    ::= nombre | variable | "(" expression ")"
```

La multiplication et la division sont prioritaires sur l'addition et la
soustraction. Les opérateurs binaires de même priorité sont associatifs à
gauche. Les parenthèses permettent d'imposer un autre ordre.

## Sémantique

Les actions d'une règle sont exécutées séquentiellement :

1. l'activation fournit la substitution issue des prémisses ;
2. `LET` évalue son expression avec cette substitution ;
3. le résultat, représenté par un `Number`, est lié à la variable cible ;
4. cette substitution enrichie est transmise aux actions suivantes ;
5. `LET` ne crée lui-même aucun fait ;
6. les faits produits par `ADD` enregistrent la substitution enrichie dans
   leur provenance.

Une variable cible déjà liée doit avoir exactement la valeur calculée. Une
liaison contradictoire, une variable opérande non liée, une valeur non
numérique ou une division par zéro provoque une erreur explicite et arrête
l'exécution. La division `/` est une division réelle et peut donc produire un
nombre flottant.

Le parseur construit un AST arithmétique dédié et n'utilise jamais `eval`.

## Exemple

```text
RULE calculer
WHEN
    ($objet valeur $n)
THEN
    LET $double := $n * 2
    LET $resultat := $double + 1
    ADD ($objet resultat $resultat)
END
```

Avec `(objet valeur 5)`, la règle ajoute `(objet resultat 11)`.

## Limite fonctionnelle

`LET` est un évaluateur déterministe, pas un solveur de contraintes. Tous les
opérandes doivent être connus au moment de l'action. Par exemple :

```text
LET $z := $x + $y
```

calcule `$z` lorsque `$x` et `$y` sont liés. En revanche, résoudre
`$x + $y == 10` avec deux inconnues relève du futur raisonnement par
contraintes.
