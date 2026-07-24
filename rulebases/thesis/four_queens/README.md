# Quatre reines

Cette base trouve les deux solutions du problème des quatre reines uniquement
par saturation de règles. Elle ne reçoit aucune disposition préétablie et
n'appelle aucun solveur Python.

Le scénario part seulement de la taille de l'échiquier et des quatre axes
d'attaque. Il exécute quatre groupes :

1. `build_board` engendre les indices `1..n`, le produit cartésien des cases
   et leurs deux diagonales ;
2. `derive_attacks` dérive une relation explicable entre toutes les cases
   partageant une ligne, une colonne ou une diagonale ;
3. `solve_four_queens_direct` reproduit la seconde formulation NéOpus ;
4. `solve_n_queens` construit un arbre de placements partiels de taille
   arbitraire.

```sh
uv run python -m rulebases.runner thesis/four_queens
```

Les deux formulations retrouvent exactement :

```text
(2, 4, 1, 3)
(3, 1, 4, 2)
```

où la position `i` indique la ligne de la reine placée dans la colonne `i`.

## Formulation directe fidèle à NéOpus

La règle `find_four_queens` lie une case de la colonne 1, puis une de la
colonne 2, et compare immédiatement leurs lignes et diagonales. Elle répète
ce procédé pour les colonnes 3 et 4. L'ordre des prémisses réalise ainsi la
propagation « à la main » décrite dans la thèse : une branche incompatible
est rejetée avant de lier la colonne suivante.

Le matcher engendre lui-même les combinaisons. La partie action ajoute une
séquence `queens_solution`; aucune boucle, recherche ou contrainte métier
n'est cachée dans Python.

Les inégalités de lignes et de diagonales sont désormais aussi reconnues par
le filtre adaptatif comme des contraintes de domaines. Sans changer cette
formulation fidèle, leur propagation spécialisée fait passer le benchmark
semi-naïf de 161,49 ms à 116,73 ms, soit un gain ×1,38. Les projections
persistantes ne lisent que 423 lignes et réutilisent deux états filtrés.

## Formulation générique par placements partiels

`solve_n_queens` réifie chaque nœud de recherche en candidat. Son identifiant
est le chemin structurel des choix déjà effectués :

```text
((queens-root chooses (2 cell 1)) next_column 2)
(((queens-root chooses (2 cell 1)) chooses (4 cell 2)) next_column 3)
```

Pour chaque case sûre de la colonne suivante, une activation :

- collecte les reines déjà placées ;
- vérifie par `NOT EXISTS` qu'aucune ne l'attaque ;
- construit le fils déterministe `($candidate chooses $cell)` ;
- copie le placement avec `FOR EACH` ;
- avance la colonne avec `LET`.

Toutes les branches compatibles coexistent dans la mémoire de travail. Il
n'y a ni backtracking implicite, ni appel à un solveur : le chaînage avant
sert directement de combinateur. Le fait `parent` et les supports de chaque
activation rendent l'arbre de recherche explicable. L'identité structurelle
est essentielle : même si un agrégat est réévalué de manière conservatrice,
la même décision produit le même nœud et les faits restent idempotents.

La règle finale `materialize_four_queen_solution` sert seulement à produire
un oracle ordonné pour le scénario 4x4. Le mécanisme d'extension qui trouve
les candidats complets dépend de la taille `n`, pas du nombre quatre.

## Intérêt

- comparaison d'une traduction NéOpus fidèle et d'une généralisation
  déclarative moderne ;
- génération de domaines et de combinaisons par règles ;
- propagation précoce des contraintes ;
- relation variable pour les axes d'attaque ;
- `COLLECT`, `NOT EXISTS`, `LET` et `FOR EACH` sur un cas concret ;
- arbre complet de recherche et provenance des solutions.

L'interface CSP/SAT générale de Snarky reste utile comme backend optionnel ou
comme point de comparaison. Elle n'est volontairement pas utilisée ici :
ce cas d'étude porte précisément sur la capacité des règles à trouver les
solutions.
