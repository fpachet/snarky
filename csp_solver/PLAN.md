# Plan du solveur CSP

## Livré dans le premier incrément

- domaines finis représentés par des faits `candidate` ;
- contraintes binaires extensionnelles ;
- propagation jusqu'au point fixe par règles ;
- choix MRV ;
- poids optionnels par alternative ;
- branches isolées et retour arrière ;
- énumération de plusieurs solutions ;
- quatre reines comme oracle.

## Paliers suivants

1. exposer directement le trail de `PropagationState` au pilote de recherche ;
2. ajouter des contraintes n-aires et globales déclarées comme objets ;
3. comparer systématiquement avec `BacktrackingConstraintSolver` ;
4. ajouter coloration, Sudoku miniature et problèmes aléatoires ;
5. apprendre éventuellement des nogoods ;
6. benchmarker DFS, MRV, best-first et choix pondéré.
