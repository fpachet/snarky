# Base de règles — Éthique III

Ce dossier contient deux paliers distincts et explicitement qualifiés.

## Palier A — reconstruction historique exécutable

La base [`rules/historical.rules`](rules/historical.rules) reconstruit les
diapositives 10 à 17 de `docs/Gondran.ppt`. Elle reproduit par chaînage avant :

- E3P19, destruction et conservation de la chose aimée ;
- E3P21, joie et tristesse partagées ;
- E3P22, amour et haine envers la cause imaginée d'un affect ;
- E3P33, effort pour obtenir l'amour réciproque.

Les règles ne sont pas présentées comme des traductions littérales de Spinoza.
Leur origine, les diapositives et leur degré de fidélité sont consignés dans
[`rules/rule_catalog.yaml`](rules/rule_catalog.yaml). Deux formes visibles mais
non exécutables sont conservées dans
[`rules/non_executable_rules.yaml`](rules/non_executable_rules.yaml) : l'action
`Créer(z)` et une réciproque dont la conclusion contient une variable non liée.

Chaque preuve est décrite dans son manifeste, par exemple
[`theorems/E3P19.yaml`](theorems/E3P19.yaml). Le moteur part uniquement des
hypothèses du cas et aucune règle nommée `E3Pxx_as_direct_rule` n'est autorisée.

## Palier B — toute la partie III

Le fichier [`sources/ethique_III_appuhn_1913.txt`](sources/ethique_III_appuhn_1913.txt)
permet de relire la partie III d'un seul tenant. Il est généré à partir de
[`sources/passages.json`](sources/passages.json), l'importation structurée de
la traduction Appuhn (1913) :

- 1 préface ;
- 3 définitions ;
- 2 postulats ;
- 59 propositions, avec démonstrations, corollaires et scolies ;
- 48 définitions d'affects ;
- 1 définition générale des affects.

Les 59 fichiers `theorems/E3P01.yaml` à `theorems/E3P59.yaml` rendent la suite
du travail incrémentale et vérifiable. Les quatre cas historiques sont
`proved`; les 55 autres sont volontairement `not_proved` et indiquent ce qui
manque. Une proposition ne doit devenir exécutable qu'après validation de ses
hypothèses, de son but et des règles antérieures qu'elle mobilise.

Le graphe [`reports/dependency_graph.json`](reports/dependency_graph.json)
exporte les références numériques détectées dans le texte. Ce sont des
`reference_candidate`, car les renvois « proposition précédente », « même
proposition » et les références aux définitions exigent encore une
normalisation éditoriale.

## Exécution

Depuis la racine du dépôt :

```sh
uv run --extra dev pytest tests/test_spinoza_ethics_iii.py
```

Pour exécuter un cas depuis Python :

```python
from pathlib import Path

from snarky.spinoza import run_case

result = run_case(Path("spinoza"), "E3P22", "amour")
assert result.proved
assert result.proof_depths == (3,)
```

## Régénération du corpus

Après avoir enregistré localement le HTML de la page Wikisource référencée
dans `sources/bibliography.yaml` :

```sh
python scripts/import_ethics_iii.py source.html spinoza/sources/passages.json
python scripts/export_ethics_iii_text.py \
  spinoza/sources/passages.json spinoza/sources/ethique_III_appuhn_1913.txt
python scripts/generate_spinoza_theorems.py \
  spinoza/sources/passages.json spinoza/theorems
python scripts/export_spinoza_dependencies.py \
  spinoza/sources/passages.json spinoza/reports/dependency_graph.json
```

L'importeur vérifie les cardinalités attendues et stocke le SHA-256 du HTML.
La régénération des théorèmes préserve les quatre fixtures historiques dans le
script générateur.
