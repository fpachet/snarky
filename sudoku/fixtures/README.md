# Fixtures Sudoku

Ce répertoire contient les grilles natives et les solutions attendues des
niveaux `grid3x3-p1` à `grid3x3-p7`.

Les oracles sont actuellement les fichiers CLIPS situés dans
[`third_party/test_rulebases/clips-6.4.2/clips_examples_642/sudoku/puzzles`](../../third_party/test_rulebases/clips-6.4.2/clips_examples_642/sudoku/puzzles).

Chaque fixture native contient :

- l’identifiant et le chemin de la source CLIPS ;
- les 81 valeurs initiales, avec `0` pour une case vide ;
- les 81 valeurs de la solution attendue ;
- la liste minimale des techniques annoncées par le corpus ;
- une somme de contrôle ou une autre vérification contre les données
  transcrites.

Le chargeur vérifie la somme SHA-256 de la source CLIPS. Un validateur Python
indépendant des règles vérifie ensuite les lignes, colonnes, boîtes et indices
initiaux avant toute comparaison avec Snarky.
