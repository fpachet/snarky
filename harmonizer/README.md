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

## Harmoniseur tonal note par note

[`note_solver.py`](note_solver.py) suit maintenant l'architecture en deux
phases de la spécification. Chaque position possède désormais six variables
CSP :

- un degré d'accord parmi `I`, `ii`, `IV`, `V`, `vi` ;
- un renversement, fondamentale ou premier renversement ;
- les quatre notes SATB.

La voix donnée — soprano, alto, ténor ou basse — est singleton. Les tessitures
contiennent toutes les notes diatoniques de do majeur ; accords, renversements
et notes restantes utilisent le `CHOICE` générique.

[`note_generation.rules`](note_generation.rules) construit les voicings après
création des domaines. Chaque candidat relie explicitement accord,
renversement et quatre hauteurs. La règle expose l'ordre strict SATB, les trois
espacements maximaux, l'appartenance à l'accord, la basse imposée par le
renversement et la complétude de la triade.

[`harmonic_form.rules`](harmonic_form.rules) impose le premier squelette
fonctionnel :

- début sur `I` pour une phrase d'au moins trois positions ;
- cadence finale `V → I` ;
- dominante et tonique cadentielles à l'état fondamental.

[`note_propagation.rules`](note_propagation.rules) maintient la canalisation
bidirectionnelle entre accord, renversement, notes et voicings.
[`note_transition.rules`](note_transition.rules) rend visibles dans la
recherche de supports la progression fonctionnelle, les contraintes
mélodiques, les parallélismes interdits et le mouvement global.

```python
from harmonizer import harmonize_notes

solution = harmonize_notes((72, 69, 71, 72), max_solutions=1)[0]
assert solution.chords == (
    "degree_I",
    "degree_IV",
    "degree_V",
    "degree_I",
)
```

Le soprano `C5–A4–B4–C5` produit :

| Voix | Hauteurs MIDI |
|---|---|
| soprano | `72 69 71 72` |
| alto | `64 60 59 64` |
| ténor | `55 57 50 55` |
| basse | `48 41 43 36` |

La basse dessine donc `C–F–G–C`. Les accords ne sont pas recopiés depuis
Python : la forme, les supports verticaux et les transitions réduisent leurs
domaines. Sur une phrase ambiguë, la trace contient une véritable décision
`harmony_*_chord` produite par `CHOICE`.

### Orchestration explicite

Le modèle expose maintenant un `RuleProgram` inspectable au lieu de dépendre
de groupes CSP ajoutés invisiblement par le solveur :

```python
model = build_note_harmonizer_model()
print(model.program.manifest())
```

Le programme distingue préparation, choix, propagation et interprétation. Il
compose dix groupes et trente-et-une règles pour l'entrée MuSES. Il sélectionne
les modules CSP `choices`, `domains` et `problems`, mais pas
`binary_constraints`, inutilisé par ce modèle. La composition complète est
détaillée dans
[`docs/rule_programs.md`](../docs/rule_programs.md).

`CHOICE` reste une primitive générale de Snarky. L'harmoniseur utilise le
protocole CSP parce que ses notes sont des variables à domaines finis ; une
autre base de génération peut employer `CHOICE` directement sans aucun fait
ni aucune règle CSP.

### Marginales contextuelles

Chaque note, accord et renversement possède une marginale statique. Lorsque la
note ou l'accord précédent est connu, `update_contextual_note_weights`
sélectionne une marginale conditionnelle. Les transitions fonctionnelles
favorisent par exemple `I → IV`, `IV → V` et `V → I`. Le poids est recalculé
dans la branche et restauré par rollback.

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
        TemporalNote(72, 0.0, 2.0),
        TemporalNote(69, 2.0, 2.0),
        TemporalNote(71, 4.0, 2.0),
        TemporalNote(72, 6.0, 2.0),
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
`C5–A4–B4–C5`, calcule `I–IV–V–I` et les quatre voix, puis appelle directement
`Piece.save_midi(...)` et `muses.io.write_musicxml(...)`. Il écrit :

- `harmonizer/generated/snarky_soprano_satb.mid` ;
- `harmonizer/generated/snarky_soprano_satb.musicxml`.

Le répertoire peut être remplacé avec
`--output-directory /chemin/de/sortie`.

Les constructeurs et codecs sont injectables ; la CI valide donc le contrat
structurel même sans installation de MuSES, puis un test optionnel vérifie les
classes réelles. La version actuelle accepte au moins deux notes
monophoniques, toute voix SATB donnée, et le profil restreint de do majeur.

### Coût du modèle tonal

Sur le cas `I–IV–V–I` à quatre positions, une solution prend 962,38 ms depuis
un tuple de hauteurs et 975,65 ms avec le trajet MuSES complet. La frontière
objet ne coûte que 13,27 ms (`+1,4 %`) ; le coût est donc dans la génération
des voicings, la canalisation à six composantes et les supports entre
positions. L'ancien benchmark à 145,06 ms concernait seulement deux positions
et un accord de do fixe : il reste historique, mais ne mesure plus le même
problème.

Voir [`docs/csp_harmonizer_next.md`](../docs/csp_harmonizer_next.md) pour
l'architecture, les mesures et les décisions sur nogoods, backjumping et
parallélisme.

## Limites explicites

Ce n'est pas encore la réimplémentation complète du profil `ROY_1998`. Le
premier vocabulaire tonal couvre cinq triades diatoniques, deux renversements,
une table de progressions et une cadence parfaite. Manquent notamment `vii°`,
les six-quatre, accords de septième, sensible et résolutions détaillées,
doublures stylistiques, notes étrangères, rythme harmonique, autres cadences
et optimisation lexicographique. Le pipeline MuSES ne traite encore ni
silences, ni changement de tonalité, ni métrique musicale dans le
raisonnement ; le rythme est pour l'instant transmis au résultat.
