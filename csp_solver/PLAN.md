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
- benchmark A/B extensionnel/intensionnel jusqu'à N=14 ;
- protocole généralisé `FiniteCSP`, avec alias `BinaryCSP` compatible ;
- Sudoku p2 résolu par Naked Singles, `CHOICE` et quatre backtracks.

## Paliers suivants

1. ajouter un problème où un nogood serait réellement réutilisé ;
2. comparer systématiquement avec `BacktrackingConstraintSolver` ;
3. ajouter coloration et problèmes aléatoires ;
4. mesurer impact, backjumping et nogoods sur ces oracles ;
5. ne retenir un mécanisme avancé que s'il réduit les nœuds ou le temps.
