# `mini_snarky` en action

`mini_snarky` est la petite base de règles utilisée pour développer et
déboguer le moteur d’inférence. Il s’agit d’un fixture moderne du projet, et
non d’un artefact historique de BOOJUM.

La base contient neuf faits initiaux et quatre règles choisies pour exercer :

1. une jointure entre deux prémisses (`grand_parent`) ;
2. une variable en position relation et le chaînage récursif
   (`transitive_relation`) ;
3. des propositions imbriquées (`knows_modus_ponens`) ;
4. un statut explicite différent de `VRAI` (`expose_alarm_status`).

Les fichiers sont les suivants :

- [`mini_snarky.rules`](mini_snarky.rules) : règles dans le DSL textuel ;
- [`initial_facts.yaml`](initial_facts.yaml) : neuf faits initiaux ;
- [`expected.yaml`](expected.yaml) : six conclusions et leurs preuves
  attendues.

## 1. Une jointure simple

La première règle recherche deux liens de parenté partageant la même personne
intermédiaire :

```text
RULE grand_parent
WHEN
    ($x parent_de $y)
    ($y parent_de $z)
THEN
    ADD ($x grand_parent_de $z)
END
```

À partir de :

```text
(alice parent_de bob)
(bob parent_de clara)
```

le moteur déduit :

```text
(alice grand_parent_de clara)
```

## 2. Une relation variable et récursive

Dans cette règle d’ordre 2, `$r` représente la relation elle-même :

```text
RULE transitive_relation
WHEN
    ($r est_transitive VRAI)
    ($x $r $y)
    ($y $r $z)
    $x != $z
THEN
    ADD ($x $r $z)
END
```

Les faits initiaux déclarent `ancetre_de` transitive et forment une chaîne :

```text
(ancetre_de est_transitive VRAI)
(alice ancetre_de bob)
(bob ancetre_de clara)
(clara ancetre_de david)
```

Le premier passage produit notamment `(bob ancetre_de david)`. Ce nouveau fait
réactive ensuite la même règle, qui produit à la profondeur de preuve 2 :

```text
(alice ancetre_de david)
```

## 3. Une proposition comme objet

Les variables `$a` et `$b` représentent ici des propositions complètes, donc
des triplets imbriqués :

```text
RULE knows_modus_ponens
WHEN
    ($person sait ($a implique $b))
    ($person sait $a)
THEN
    ADD ($person sait $b)
END
```

Avec les deux faits :

```text
(alice sait ((bob humain VRAI) implique (bob mortel VRAI)))
(alice sait (bob humain VRAI))
```

la conclusion est :

```text
(alice sait (bob mortel VRAI))
```

## 4. Un statut explicite

La syntaxe apostrophe inspecte le statut du fait au lieu de tester seulement
sa présence :

```text
RULE expose_alarm_status
WHEN
    alarme ' $status
THEN
    ADD (alarme possede_statut $status)
END
```

Le fait `alarme` ayant le statut `FAUX`, le moteur produit :

```text
(alarme possede_statut FAUX)
```

Il ne confond donc pas `FAUX`, `INEXISTANT` et l’absence d’un fait.

## Exécuter la démonstration

Depuis la racine du dépôt, le test d’intégration exécute la base jusqu’au point
fixe et compare chaque conclusion avec `expected.yaml` :

```sh
uv run --extra dev pytest tests/test_forward_engine.py
```

Pour inspecter directement les conclusions et leur provenance :

```python
from pathlib import Path

from snarky import ForwardEngine, parse_rules, render_term
from snarky.serialization import load_facts

root = Path("tests/rulebases/debug")
rules = parse_rules((root / "mini_snarky.rules").read_text(encoding="utf-8"))
initial_facts = load_facts(root / "initial_facts.yaml")
result = ForwardEngine(rules).run(initial_facts)

for fact in result.derived_facts:
    proof = result.provenance.minimal_derivation(fact)
    print(
        f"[{proof.rule_name}, profondeur {proof.proof_depth}] "
        f"{render_term(fact.entity)}"
    )
```

La sortie obtenue est :

```text
[grand_parent, profondeur 1] (alice grand_parent_de clara)
[transitive_relation, profondeur 1] (alice ancetre_de clara)
[transitive_relation, profondeur 1] (bob ancetre_de david)
[knows_modus_ponens, profondeur 1] (alice sait (bob mortel VRAI))
[expose_alarm_status, profondeur 1] (alarme possede_statut FAUX)
[transitive_relation, profondeur 2] (alice ancetre_de david)
```

Le point fixe contient donc 15 faits : les neuf faits initiaux et les six faits
dérivés. Les futures stratégies optimisées devront produire exactement le même
ensemble de faits et les mêmes profondeurs minimales de preuve.
