# Projet Sudoku

Ce sous-projet utilise un Sudoku 9×9 comme banc d’essai pour faire évoluer
Snarky vers une résolution symbolique progressive et explicable, proche des
techniques employées par un humain.

Il ne s’agit pas d’écrire un solveur spécialisé en Python. La connaissance du
domaine doit rester dans des groupes de règles déclaratifs ; l’orchestrateur
Python ne doit connaître que l’ordre des groupes, les conditions d’arrêt et la
notion générale de progrès.

## État actuel

La base native est exécutable et résout les six niveaux essentiels p1 à p6.
Elle utilise :

- `RuleGroup` pour nommer une famille de règles ;
- `InferenceSession` pour partager faits, réfraction et provenance ;
- les modes `SATURATE`, `ONE_CYCLE`, `FIRST_CHANGE` et `UNTIL` ;
- `FactExists` pour arrêter un groupe lorsqu’un motif apparaît ;
- `REMOVE` et le journal d’`InferenceEvent` pour les éliminations ;
- `NOT EXISTS` corrélé pour reconnaître singles, verrouillages et paires ;
- `TechniquePlan` pour essayer les techniques par difficulté croissante et
  recommencer au début après chaque groupe efficace.

Le [plan d’implémentation](docs/implementation_plan.md) décrit leur sémantique,
les jalons réalisés et les extensions avancées restantes.

## Périmètre essentiel

Le premier objectif couvre les niveaux p1 à p6 de l’exemple CLIPS :

| Niveau | Technique nouvelle |
|---|---|
| p1 | Naked Single |
| p2 | Hidden Single |
| p3 | Locked Candidate Single Line |
| p4 | Locked Candidate Multiple Lines |
| p5 | Naked Pairs |
| p6 | Hidden Pairs |

Cette cible doit être résolue sans recherche exhaustive, sans OR-Tools et sans
retour arrière. Chaque valeur finale devra être expliquée par une suite
rejouable d’éliminations.

Les niveaux p7 à p18 — X-Wing, triples, coloriage, chaînes et rectangle
unique — constitueront des paliers ultérieurs.

## Organisation

```text
sudoku/
├── README.md
├── __init__.py
├── domain.py
├── rulebase.py
├── solver.py
├── docs/
│   └── implementation_plan.md
├── fixtures/
│   ├── README.md
│   └── grid3x3-p1.yaml … grid3x3-p6.yaml
├── rules/
│   ├── README.md
│   ├── catalog.yaml
│   └── *.rules
└── tests/
    └── test_*.py
```

- [`rules/catalog.yaml`](rules/catalog.yaml) inventorie les groupes et règles
  de la base essentielle, ainsi que les fonctionnalités dont ils dépendent ;
- [`rules/README.md`](rules/README.md) fixe la convention de représentation et
  l’organisation des fichiers exécutables ;
- [`fixtures/README.md`](fixtures/README.md) décrit les oracles p1 à p6 à
  présent transcrits dans un format natif ;
- [`docs/implementation_plan.md`](docs/implementation_plan.md) contient le
  chemin critique, les décisions sémantiques et les critères d’acceptation ;
- [`domain.py`](domain.py) charge et valide les grilles, [`rulebase.py`](rulebase.py)
  charge les groupes et [`solver.py`](solver.py) les orchestre ;
- [`tests`](tests) vérifie l’organisation, les oracles, les solutions, les
  techniques nécessaires et le rejeu des événements.

## Corpus de référence

Les sources officielles CLIPS restent inchangées dans
[`third_party/test_rulebases/clips-6.4.2/clips_examples_642/sudoku`](../third_party/test_rulebases/clips-6.4.2/clips_examples_642/sudoku).

Cette séparation est intentionnelle :

- `third_party/` contient l’oracle externe dans son langage d’origine ;
- `sudoku/` contient sa reformulation native, sa documentation et ses tests ;
- `src/snarky/` contient uniquement les capacités génériques du moteur.

La comparaison porte sur les résultats et les techniques nécessaires, pas sur
une reproduction de la salience ou de l’agenda CLIPS.

## Modèle de faits

Une case et ses candidats sont représentés avec les triplets ordinaires de
Snarky :

```text
(r1c1 row 1)
(r1c1 column 1)
(r1c1 box 1)
(r1c1 candidate 5)
```

Une case donnée ne possède qu’un candidat initial. Une case vide en possède
neuf. Les règles retirent progressivement les candidats impossibles.

Les groupes sont appelés du plus simple au plus complexe. Après chaque
mutation, l’orchestrateur repart du premier groupe. L’exécution se termine
avec l’un des états génériques `SOLVED`, `STUCK`, `INCONSISTENT` ou
`LIMIT_REACHED`.

## Exécution

Depuis la racine du dépôt :

```sh
uv run python -c \
  'from sudoku import solve_level; print(solve_level(6).techniques_used)'
```

La grille finale est comparée à l’oracle CLIPS et la suite complète
d’événements peut être rejouée indépendamment du moteur.

Le benchmark de performance reproductible est lancé depuis la racine avec :

```sh
uv run python -m benchmarks.sudoku_rules --levels 1 5 6 --repeat 5
```

La baseline mesurée et les compteurs algorithmiques sont documentés dans
[`../benchmarks/README.md`](../benchmarks/README.md).

## Prochain jalon

Le prochain palier commence à p7 avec X-Wing. Il servira à décider, sur
mesures, si Snarky doit recevoir des agrégats `COUNT`/`COLLECT` ou une
abstraction générale d’ensembles finis avant les techniques de coloriage et
de chaînes.
