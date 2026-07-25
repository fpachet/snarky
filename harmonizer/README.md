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
CSP. La voix donnée — soprano, alto, ténor ou basse — est singleton ; les trois
autres sont décidées par le `CHOICE` générique.

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

### Orchestration explicite

Le modèle expose maintenant un `RuleProgram` inspectable au lieu de dépendre
de groupes CSP ajoutés invisiblement par le solveur :

```python
model = build_note_harmonizer_model()
print(model.program.manifest())
```

Le programme distingue préparation, choix, propagation et interprétation. Il
compose neuf groupes et vingt-deux règles pour l'entrée MuSES. Il sélectionne
les modules CSP `choices`, `domains` et `problems`, mais pas
`binary_constraints`, inutilisé par ce modèle. La composition complète est
détaillée dans
[`docs/rule_programs.md`](../docs/rule_programs.md).

`CHOICE` reste une primitive générale de Snarky. L'harmoniseur utilise le
protocole CSP parce que ses notes sont des variables à domaines finis ; une
autre base de génération peut employer `CHOICE` directement sans aucun fait
ni aucune règle CSP.

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

## Pipeline MuSES complet

[`muses_harmonizer.py`](muses_harmonizer.py) relie désormais le modèle à
l'API objet de MuSES. L'appel public accepte une `TemporalCollection`
monodique et rend une ou plusieurs `Piece`, chacune contenant les quatre
`TemporalCollection` dans l'ordre soprano, alto, ténor, basse :

```python
from harmonizer import harmonize_temporal_collection
from muses.base.temporals import TemporalCollection, TemporalNote

soprano = TemporalCollection(
    name="given_soprano",
    temporals=(
        TemporalNote(67, 0.0, 1.0),
        TemporalNote(72, 1.0, 1.0),
    ),
    instrument="choir",
)
result = harmonize_temporal_collection(
    soprano,
    given_voice="soprano",
    piece_name="generated_satb",
)[0]
piece = result.piece
```

Le trajet est réellement bidirectionnel :

1. `MusesTemporalCollectionCodec` produit un snapshot factuel immuable ;
2. le groupe [`muses_input.rules`](muses_input.rules) relie chaque
   `muses_pitch` à la variable de la voix donnée ;
3. tous les groupes de génération, canalisation, transition, choix et
   interprétation du noyau courant sont exécutés ;
4. chaque voix est réencodée en faits puis reconstruite en
   `TemporalCollection` ;
5. les quatre collections forment une vraie `Piece` MuSES.

Temps de départ, durées, vélocités, instrument, programme et fin de collection
sont conservés. La source n'est jamais mutée. `source_facts`, les quatre
`voice_facts`, les choix et toute la trace d'inférence restent accessibles
dans `MusesHarmonization`.

MuSES demeure optionnel pour le moteur. Avec les deux dépôts siblings :

```sh
python -m pip install -e ../muses
PYTHONPATH=src python -m harmonizer.example_muses
```

L'exemple construit deux mesures de soprano
`G4–E4–C4–E4–G4–C5`, calcule les quatre voix, puis appelle directement
`Piece.save_midi(...)` et `muses.io.write_musicxml(...)`. Il écrit :

- `harmonizer/generated/snarky_soprano_satb.mid` ;
- `harmonizer/generated/snarky_soprano_satb.musicxml`.

Le répertoire peut être remplacé avec
`--output-directory /chemin/de/sortie`.

Les constructeurs et codecs sont injectables ; la CI valide donc le contrat
structurel même sans installation de MuSES, puis un test optionnel vérifie les
classes réelles. La version actuelle accepte au moins deux notes
monophoniques, toute voix SATB donnée, et le profil restreint de do majeur.

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
lexicographique. Le pipeline MuSES ne traite encore ni silences, ni accords
dans la collection donnée, ni changement de tonalité, ni métrique musicale
dans le raisonnement ; le rythme est pour l'instant transmis au résultat.
