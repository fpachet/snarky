# Petites bases

Ces bases sont assez courtes pour être comprises intégralement. Elles servent
à la fois de tutoriels, de tests d'acceptation et, lorsque leurs compteurs sont
stables, de micro-benchmarks.

- [`fibonacci_explicit`](fibonacci_explicit/README.md) construit l'arbre
  récursif complet de Fibonacci et mesure le coût du matching.
- [`factorial_explicit`](factorial_explicit/README.md) isole la récursion
  linéaire et la multiplication.
- [`combinations_foreach`](combinations_foreach/README.md) engendre des
  binômes, les filtre par des faits et matérialise leurs membres avec
  `FOR EACH`.
- [`triangle_closure`](triangle_closure/README.md) montre une conjonction
  événementielle de trois faits exécutée sans produit partiel matérialisé.

Les fixtures de débogage purement internes restent dans `tests/rulebases` :
elles ne constituent pas des exemples publics.
