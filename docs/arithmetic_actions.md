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
produit     ::= unaire (("*" | "/" | "%") unaire)*
unaire      ::= ("+" | "-") unaire | primaire
primaire    ::= nombre | variable | "(" expression ")"
```

La multiplication et la division sont prioritaires sur l'addition et la
soustraction. Le modulo `%` a la même priorité que `*` et `/`. Les opérateurs
binaires de même priorité sont associatifs à
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
numérique, une division ou un modulo par zéro provoque une erreur explicite et
arrête l'exécution. La division `/` est une division réelle et peut donc
produire un nombre flottant. `%` exige deux entiers et suit la sémantique du
modulo Python, y compris pour les valeurs négatives.

Le parseur construit un AST arithmétique dédié et n'utilise jamais `eval`.

## Prémisse `DIVISIBLE`

La divisibilité entière peut être testée directement dans la partie gauche :

```text
WHEN
    (current year $year)
    DIVISIBLE $year BY 4
THEN
    ADD ($year divisible_by 4)
END
```

Les deux opérandes doivent être des `Number` entiers liés et le diviseur doit
être non nul. `DIVISIBLE` est une comparaison pure : elle ne crée aucune
liaison ni aucun fait.

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

## Contraintes arithmétiques déclaratives

`LET` est un évaluateur déterministe, pas un solveur de contraintes. Tous les
opérandes doivent être connus au moment de l'action. Par exemple :

```text
LET $z := $x + $y
```

calcule `$z` lorsque `$x` et `$y` sont liés. La forme relationnelle s'écrit
maintenant dans la partie gauche :

```text
WHEN
    (left candidate $x)
    (right candidate $y)
    (total candidate $z)
    CONSTRAINT $x + $y == $z
THEN
    ADD (SEQ[$x $y] sums_to $z)
END
```

`CONSTRAINT` accepte les expressions de `LET` de chaque côté de `==`, `!=`,
`<`, `<=`, `>` et `>=`. Toutes les variables doivent recevoir un domaine fini
depuis les prémisses factuelles. La prémisse ne crée aucune valeur : elle
retire seulement les valeurs sans support, puis le matcher final réévalue
l'expression devenue ground.

Le propagateur spécialisé traite les égalités binaires utilisant `+`, `-`,
`*`, `/` et `%`. Pour `+` et `-`, il choisit le plus petit des trois produits
de domaines `(x,y)`, `(x,z)` et `(y,z)` et déduit la troisième valeur ; une
cible singleton transforme ainsi un produit cubique en parcours linéaire.
Les comparaisons simples utilisent intersection, singleton ou bornes. Les
expressions imbriquées ou relations non spécialisées conservent le repli
cartésien borné de la stratégie forcée.

Il n'y a ni création d'hypothèse ni backtracking caché. Si le filtrage ne
suffit pas, le matcher ordinaire énumère les candidats restants.
