# Plan de développement de l'harmoniseur

## Jalon 1 — livré

- projet autonome et exécutable ;
- voicings SATB finis ;
- contraintes verticales essentielles ;
- trois relations de transition ;
- choix pondérés et best-first ;
- exposition des notes choisies par règles Snarky.
- benchmark reproductible et tests de contraintes verticales.

## Jalon 2 — variables de notes

Remplacer le choix initial d'un voicing complet par les quatre variables de
notes préconisées dans la spécification. Propager tessitures, ordre,
espacements et règles mélodiques avant la construction différée des voicings.
Déplacer simultanément la génération et l'élimination des candidats musicaux
du compilateur Python vers des groupes de règles explicables.

Ce jalon peut désormais utiliser plusieurs `CHOICE` séquentiels dans une même
règle pour instancier soprano, alto, ténor et basse, tout en laissant les
règles de propagation éliminer les valeurs incompatibles entre les décisions.

## Jalon 3 — profil dur `ROY_1998`

Ajouter degrés, renversements, vocabulaire, doublures, sensible, cadence,
progressions et exceptions. Chaque règle stable `R-*` recevra ses cas positif,
négatif, limite et exception.

## Jalon 4 — préférences et probabilités

Ajouter objectifs lexicographiques, coûts de conduite des voix, probabilités
conditionnelles ou marginales, N meilleures solutions et échantillonnage
reproductible.

## Jalon 5 — `FOUR_PART_COMPLETE`

Ajouter six-quatre fonctionnels, accords de septième, notes étrangères,
métrique et modulations uniquement après validation du profil historique.
