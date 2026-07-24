# Quatre reines

Le scénario valide la disposition classique `(2, 4, 1, 3)` sur un échiquier
4×4. Les lignes, colonnes et deux identifiants de diagonale sont des propriétés
ordinaires des cases. Une règle à relation variable détecte qu'une paire de
reines partage un axe d'attaque ; un second groupe déclare la disposition
valide si quatre reines sont placées et qu'aucun conflit n'a été dérivé.

## Intérêt

- contrainte combinatoire exprimée par des faits ;
- relation variable ;
- `COUNT` et `NOT EXISTS` ;
- séparation entre détection des violations et validation globale.

```sh
uv run python -m rulebases.runner thesis/four_queens
```

## Extension proposée

La base valide une disposition, mais ne choisit pas elle-même les quatre
positions. Une résolution générale demanderait une recherche de choix ou un
pont vers un solveur de contraintes. Cette extension profiterait également au
Sudoku lorsque les seules techniques humaines disponibles aboutissent à
`STUCK`.
