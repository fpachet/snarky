# Harmoniseur tonal à quatre voix

Ce projet est le cas d'intégration de la génération hybride de Snarky :

- règles locales et relations extensionnelles ;
- propagation de domaines ;
- recherche avec `ChoicePoint` ;
- poids issus de probabilités marginales ;
- branches isolées et backtracking ;
- traces de décisions et contradictions.

## Premier incrément

La version actuelle harmonise une phrase test de deux positions en do majeur
avec des accords parfaits SATB. Un choix porte encore sur un voicing complet
par position.

Les domaines verticaux appliquent :

- `R-NOTE-001` : soprano imposé ;
- `R-ORDER-001` : ordre SATB ;
- `R-SPACING-001` à `003` ;
- `R-CHORD-001` à `003` : triade complète ;
- `R-DOUBLING-001` : multiplicité `2,1,1`.

Dans ce premier incrément, ce domaine vertical est compilé en Python sous
forme de faits `candidate`. Les règles Snarky génériques assurent ensuite la
réduction des domaines, les singletons, la contradiction et la reconnaissance
de solution. Ce découpage donne un oracle exécutable, mais le plan prévoit de
déplacer progressivement le vocabulaire musical et les éliminations dans des
groupes de règles.

Les relations entre deux positions appliquent :

- intervalle mélodique maximal et triton interdit ;
- absence de chevauchement temporel ;
- quintes, octaves et unissons parallèles ;
- interdiction du mouvement direct des quatre voix.

Les probabilités marginales de chaque voix sont multipliées pour former un
poids de proposition. Dans ce premier incrément, ce produit est uniquement un
score d'ordre de recherche, pas une probabilité jointe revendiquée.

```sh
PYTHONPATH=src python -m harmonizer.solver
```

Le moteur cherche les solutions par best-first. Les contraintes dures
déterminent la faisabilité ; les poids ne changent pas l'ensemble des
solutions.

## Limites explicites

Ce n'est pas encore la réimplémentation complète du profil `ROY_1998`.
Manquent notamment degrés, renversements, sensible, cadences, règles détaillées
de doublure, mouvements directs complets et optimisation stylistique
lexicographique.
