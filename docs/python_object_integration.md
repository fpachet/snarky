# Intégration des objets Python

## But

Snarky travaille sur des termes et faits immuables afin de préserver
l'indexation, le déterminisme, la provenance et le rollback. Les objets métier
Python sont souvent mutables et possèdent une identité qui ne coïncide pas
avec leur égalité. L'intégration retenue utilise donc des **snapshots
factuels** :

```text
objet Python
    -> FactCodec.encode()
    -> faits Snarky immuables
    -> règles, CHOICE et backtracking
    -> FactCodec.decode()
    -> nouvel objet Python
```

L'objet source n'est jamais modifié pendant l'inférence. Les faits de la
session constituent l'état logique de chaque branche ; une solution acceptée
est matérialisée sous la forme d'un nouvel objet.

## Protocole générique

`FactCodec[T]` est volontairement petit :

```python
class FactCodec(Protocol[T]):
    def encode(
        self,
        value: T,
        *,
        identity: Atom,
    ) -> tuple[Fact, ...]: ...

    def decode(
        self,
        identity: Atom,
        facts: Iterable[Fact],
    ) -> T: ...
```

L'identité est fournie explicitement par l'appelant. Elle doit rester stable
entre l'encodage, les règles et la matérialisation. Ce premier palier n'ajoute
pas d'objet Python mutable au type `Term` et ne change donc ni le matcher ni
ses index.

## Premier codec MuSES

Le module `snarky.integrations` fournit :

- `MusesTemporalNoteCodec` pour `TemporalNote` ;
- `MusesTemporalCollectionCodec` pour une collection ordonnée de notes.

MuSES reste une dépendance optionnelle. Avec les deux projets siblings :

```sh
python -m pip install -e ../muses
```

Puis :

```python
from muses.base.temporals import TemporalCollection, TemporalNote
from snarky import Atom, ForwardEngine
from snarky.integrations import MusesTemporalCollectionCodec

melody = TemporalCollection(
    name="phrase",
    temporals=(
        TemporalNote(60, 0.0, 1.0),
        TemporalNote(64, 1.0, 1.0),
    ),
    instrument="piano",
)
identity = Atom("phrase_1")
codec = MusesTemporalCollectionCodec()
facts = codec.encode(melody, identity=identity)
session = ForwardEngine(()).create_session(facts)

# Les règles, les choix et les rollbacks modifient uniquement session.facts.
result = codec.decode(identity, session.facts)
```

`decode()` importe MuSES paresseusement. Pour les tests ou un modèle
compatible, les constructeurs de note et de collection peuvent être injectés
explicitement dans les codecs.

## Vocabulaire factuel

Une collection et une note sont projetées ainsi :

```text
(phrase_1 muses_type muses_temporal_collection)
(phrase_1 muses_contains muses_note_cGhyYXNlXzE_0)
(muses_note_cGhyYXNlXzE_0 muses_index 0)
(muses_note_cGhyYXNlXzE_0 muses_type muses_temporal_note)
(muses_note_cGhyYXNlXzE_0 muses_pitch 60)
(muses_note_cGhyYXNlXzE_0 muses_start_beat 0.0)
(muses_note_cGhyYXNlXzE_0 muses_duration 1.0)
(muses_note_cGhyYXNlXzE_0 muses_velocity 60)
(muses_note_cGhyYXNlXzE_0 muses_midi_channel 0)
```

Les métadonnées de collection `name`, `instrument`, `program_change`,
`melody_type` et `end_beat` sont également conservées. Les chaînes sont
encodées dans des atomes Base64 URL-safe afin de représenter sans ambiguïté
les chaînes vides, espaces et caractères Unicode sans introduire encore un
nouveau terme texte dans le cœur.

L'identité d'une note contenue est dérivée de l'identité de la collection et
de son rang. `muses_index` conserve l'ordre même si les faits sont reçus dans
un autre ordre.

## Rollback

Une décision peut remplacer un fait tel que :

```text
(note_0 muses_pitch 60)
```

par :

```text
(note_0 muses_pitch 67)
```

Le checkpoint de `InferenceSession` restaure les faits. Le codec matérialise
alors soit la note transposée dans la branche, soit la hauteur d'origine après
rollback. L'objet MuSES fourni à `encode()` conserve toujours sa valeur
initiale.

Cette discipline évite de construire un second trail spécialisé pour chaque
bibliothèque Python et empêche les effets de bord d'une branche abandonnée.

## Limites du premier palier

- une `TemporalCollection` ne peut contenir que des `TemporalNote`; tout autre
  `TemporalObject` est refusé explicitement ;
- une mutation Python effectuée après `encode()` n'est pas observée
  automatiquement : il faut produire un nouveau snapshot ;
- il n'existe pas encore de registre général `ObjectRef -> object` ;
- les deltas objets ne sont pas encore calculés automatiquement ;
- la reconstruction ne signifie pas que tous les faits d'une solution ont
  une provenance musicale minimale.

## Harmoniseur MuSES livré

Le cas applicatif est maintenant disponible dans
`harmonizer.muses_harmonizer` :

```python
from harmonizer import harmonize_temporal_collection

solutions = harmonize_temporal_collection(
    given_collection,
    given_voice="bass",
    max_solutions=3,
)
piece = solutions[0].piece
```

Le pipeline encode la collection, importe ses hauteurs par une règle Snarky,
exécute la génération et la recherche, puis encode et reconstruit quatre
collections distinctes avant de créer une `Piece`. Le résultat symbolique
conserve les accords, les renversements, le profil cadentiel, le rythme
harmonique, les quatre voicings, les faits source, les faits de chaque voix et
la trace. Le vocabulaire tonal couvre `I`, `ii`, `IV`, `V`, `V7`, `vi`,
`vii°`, les états fondamental/premier renversement, `I64` cadentiel, quatre
formes cadentielles et les résolutions de tendance du noyau courant.

Cette validation montre que les atomes stables et les snapshots suffisent au
premier harmoniseur : aucun `ObjectRef` natif ni mutation d'objet sur le trail
n'a été nécessaire.

## Suite proposée

Les extensions restantes seront ajoutées seulement à partir d'usages
concrets :

1. ajouter un petit `ObjectSession` calculant les deltas d'un remplacement
   d'objet ;
2. introduire `ObjectRef` comme terme natif seulement si l'usage d'atomes
   stables devient réellement limitant ;
3. étendre le codec aux silences ou autres objets temporels lorsqu'une règle
   musicale les consommera ;
4. envisager un DSL Python déclaratif séparément, sans rendre les fonctions
   arbitraires opaques au matcher.
