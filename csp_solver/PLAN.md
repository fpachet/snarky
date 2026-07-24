# Plan du solveur CSP

## Livré dans le premier incrément

- domaines finis représentés par des faits `candidate` ;
- contraintes binaires extensionnelles ;
- propagation jusqu'au point fixe par règles ;
- choix MRV ;
- poids optionnels par alternative ;
- instruction déclarative `CHOICE ... FROM` ;
- plusieurs choix séquentiels dans une règle ;
- branches isolées et retour arrière ;
- énumération de plusieurs solutions ;
- constructeur générique `n` reines et quatre reines comme oracle ;
- formulation N-reines intensionnelle par recherche de supports arithmétiques ;
- benchmark A/B extensionnel/intensionnel jusqu'à N=14.

## Paliers suivants

1. ajouter des contraintes n-aires et globales déclarées comme objets ;
2. comparer systématiquement avec `BacktrackingConstraintSolver` ;
3. ajouter coloration, Sudoku miniature et problèmes aléatoires ;
4. apprendre éventuellement des nogoods ;
5. benchmarker DFS, MRV, best-first et choix pondéré.
