# Harmoniseur tonal à quatre voix

Ce projet est le cas d'intégration de la génération hybride de Snarky :

- règles locales et contraintes de transition intensionales ;
- propagation de domaines ;
- recherche avec `ChoicePoint` ;
- poids issus de probabilités marginales ;
- branches explicites et backtracking ;
- traces de décisions et contradictions.

## Oracle à voicing complet

L'oracle historique harmonise une phrase test de deux positions en do majeur
avec des accords parfaits SATB. Dans ce chemin de comparaison, un choix porte
sur un voicing complet par position.

Les domaines verticaux appliquent :

- `R-NOTE-001` : soprano imposé ;
- `R-ORDER-001` : ordre SATB ;
- `R-SPACING-001` à `003` ;
- `R-CHORD-001` à `003` : triade complète ;
- `R-DOUBLING-001` : multiplicité `2,1,1`.

Dans cet oracle, ce domaine vertical est compilé en Python sous
forme de faits `candidate`. Les règles Snarky génériques assurent ensuite la
réduction des domaines, les singletons, la contradiction et la reconnaissance
de solution. Ce découpage donne un oracle exécutable, mais le plan prévoit de
déplacer progressivement le vocabulaire musical et les éliminations dans des
groupes de règles.

La sélection d'un voicing n'est plus construite par une boucle Python :
la règle CSP générique `choose_csp_value` utilise maintenant
`CHOICE ... FROM ... END_CHOICE`. Le fichier musical
[`rules.rules`](rules.rules) ne contient toutefois encore que l'exposition du
voicing choisi et la reconnaissance du résultat. Ce chemin reste disponible
pour comparer résultats, compteurs et performances avec la représentation
note par note.

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
solutions. Best-first conserve plusieurs états simultanés et n'utilise donc
pas le trail DFS. Sa frontière est néanmoins paresseuse : une alternative ne
crée sa session que lorsqu'elle est retirée du tas stable.

## Transitions intensionales

Le mode par défaut ne matérialise plus tous les couples de voicings autorisés.
[`intensional_transition.rules`](intensional_transition.rules) révise chaque
paire de positions successives dans les deux directions. Un candidat est
retiré s'il n'existe plus de voicing compatible chez son voisin.

La compatibilité musicale est exposée comme un `ComputedPredicate` pur et
enregistré explicitement. Les règles restent responsables du point fixe, des
supports, des retraits et de la trace ; Python ne pilote ni la recherche ni
les décisions. `intensional_transitions=False` conserve la table extensionnelle
comme oracle.

| Phrase | Extensionnel | Intensionnel | Faits ext. → int. | Gain |
|---|---:|---:|---:|---:|
| 2 positions | 99,31 ms | 37,60 ms | 401 → 32 | ×2,64 |
| 4 positions | 2,573 s | 562,00 ms | 1 171 → 64 | ×4,58 |

Les trois premières solutions, leur ordre et les compteurs de nœuds sont
identiques. Depuis la baseline de 257,78 ms antérieure à cette tranche,
l'harmoniseur court atteint 37,60 ms, soit ×6,86 (`-85,4 %`).

Le benchmark comparatif s'exécute avec :

```sh
PYTHONPATH=.:src python benchmarks/choice_formulations.py --repeat 3
```

## Harmoniseur note par note

[`note_solver.py`](note_solver.py) suit maintenant l'architecture en deux
phases de la spécification. Chaque voix de chaque position est une variable
CSP. Le soprano donné est singleton ; alto, ténor et basse sont décidés par le
`CHOICE` générique.

[`note_generation.rules`](note_generation.rules) construit les voicings après
création des domaines. La règle expose directement l'ordre vertical SATB, les
trois espacements maximaux et la complétude de la triade.

[`note_propagation.rules`](note_propagation.rules) maintient la canalisation
bidirectionnelle entre notes et voicings.
[`note_transition.rules`](note_transition.rules) rend visibles dans la
recherche de supports les contraintes mélodiques, les parallélismes interdits
et le mouvement global.

```python
from harmonizer import harmonize_notes

solutions = harmonize_notes((67, 72), max_solutions=3)
```

La phrase test engendre par règles les mêmes domaines de 15 et 9 voicings que
l'oracle. Les trois premières solutions demandent 19 nœuds et quatre à cinq
décisions de notes.

### Marginales contextuelles

Chaque variable possède une marginale statique. Lorsque la note précédente de
la même voix est connue, `update_contextual_note_weights` la remplace par une
marginale conditionnelle. Le poids est donc recalculé dans la branche et
restauré par rollback.

Best-first fournit les meilleures réalisations déterministes. Un tirage
pondéré reproductible est également public :

```python
from harmonizer import sample_harmonization

sample = sample_harmonization((67, 72), seed=7)
```

Les poids ordonnent ou échantillonnent les solutions ; ils ne changent jamais
les contraintes dures.

### Coût du modèle explicite

Sur la phrase de deux positions, trois solutions prennent 34,92 ms avec le
choix d'un voicing complet et 145,06 ms avec les variables de notes. Le
facteur ×4,15 est la baseline du modèle explicatif : il manipule davantage de
variables et maintient le canal notes–voicings.

Voir [`docs/csp_harmonizer_next.md`](../docs/csp_harmonizer_next.md) pour
l'architecture, les mesures et les décisions sur nogoods, backjumping et
parallélisme.

## Limites explicites

Ce n'est pas encore la réimplémentation complète du profil `ROY_1998`.
Manquent notamment degrés, renversements, sensible, cadences, règles détaillées
de doublure, mouvements directs complets et optimisation stylistique
lexicographique.
