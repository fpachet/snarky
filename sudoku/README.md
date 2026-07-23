# Projet Sudoku

Ce sous-projet utilise un Sudoku 9×9 comme banc d’essai pour faire évoluer
Snarky vers une résolution symbolique progressive et explicable, proche des
techniques employées par un humain.

Il ne s’agit pas d’écrire un solveur spécialisé en Python. La connaissance du
domaine doit rester dans des groupes de règles déclaratifs ; l’orchestrateur
Python ne doit connaître que l’ordre des groupes, les conditions d’arrêt et la
notion générale de progrès.

## État actuel

Les fondations génériques nécessaires au pilotage sont disponibles :

- `RuleGroup` pour nommer une famille de règles ;
- `InferenceSession` pour partager faits, réfraction et provenance ;
- les modes `SATURATE`, `ONE_CYCLE`, `FIRST_CHANGE` et `UNTIL` ;
- `FactExists` pour arrêter un groupe lorsqu’un motif apparaît.

La base Sudoku native est cependant encore **non exécutable**. Deux capacités
générales du moteur manquent :

1. retirer un fait de la mémoire de travail tout en conservant son histoire ;
2. exprimer un `NOT EXISTS` corrélé à des variables déjà liées.

Le [plan d’implémentation](docs/implementation_plan.md) décrit leur sémantique,
les tests requis et l’ordre des jalons.

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
├── docs/
│   └── implementation_plan.md
├── fixtures/
│   └── README.md
├── rules/
│   ├── README.md
│   └── catalog.yaml
└── tests/
    └── test_project_structure.py
```

- [`rules/catalog.yaml`](rules/catalog.yaml) inventorie les groupes et règles
  de la base essentielle, ainsi que les fonctionnalités dont ils dépendent ;
- [`rules/README.md`](rules/README.md) fixe la convention de représentation et
  la future organisation des fichiers exécutables ;
- [`fixtures/README.md`](fixtures/README.md) décrit les oracles p1 à p6 à
  transcrire dans un format natif ;
- [`docs/implementation_plan.md`](docs/implementation_plan.md) contient le
  chemin critique, les décisions sémantiques et les critères d’acceptation ;
- [`tests/test_project_structure.py`](tests/test_project_structure.py) vérifie
  l’intégrité de cette organisation et la présence des oracles CLIPS p1 à p6.

## Corpus de référence

Les sources officielles CLIPS restent inchangées dans
[`third_party/test_rulebases/clips-6.4.2/clips_examples_642/sudoku`](../third_party/test_rulebases/clips-6.4.2/clips_examples_642/sudoku).

Cette séparation est intentionnelle :

- `third_party/` contient l’oracle externe dans son langage d’origine ;
- `sudoku/` contient sa reformulation native, sa documentation et ses tests ;
- `src/snarky/` contient uniquement les capacités génériques du moteur.

La comparaison porte sur les résultats et les techniques nécessaires, pas sur
une reproduction de la salience ou de l’agenda CLIPS.

## Modèle de faits prévu

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

## Prochain jalon

Le premier jalon visible est la résolution de p1 par le groupe
`naked_singles`. Il dépend des phases 0 à 4 du plan :

1. fixtures et validateur indépendant ;
2. action `REMOVE` et journal de mutations ;
3. réfraction et index compatibles avec les retraits ;
4. prémisse `NOT EXISTS` corrélée ;
5. règles de singles et validation de la grille.
