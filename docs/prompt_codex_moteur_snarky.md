# Prompt Codex — Conception de Snarky, moteur moderne inspiré de BOOJUM

## Mission générale

Construire en Python **Snarky**, un moteur de règles moderne, testable et documenté, inspiré de **SNARK et surtout de BOOJUM**, capable de manipuler des règles d’ordres 0, 1 et 2, des faits récursifs, des faits portant sur des faits et des instanciations obtenues par propagation de contraintes.

Le projet ne doit pas prétendre reproduire exactement le logiciel historique BOOJUM, dont le code source et plusieurs détails d’implémentation ne sont pas disponibles. Il doit produire :

1. une reconstruction documentée des éléments décrits dans les sources ;
2. une sémantique opérationnelle explicite pour les éléments non complètement spécifiés ;
3. une implémentation Python claire et modulaire ;
4. une batterie de tests unitaires et fonctionnels ;
5. des benchmarks comparant plusieurs stratégies d’instanciation ;
6. une API permettant ultérieurement d’utiliser le corpus Spinoza comme test d’intégration.

---

## Sources principales

### Source principale

Jean-Luc Dormoy,  
**« Amélioration de l’efficacité du pattern matching dans le langage à base de règles BOOJUM »**, Convention IA 1989 :

```text
https://dormoy.org/JLuc/Papers/Boojum89.pdf
```

Cette source doit constituer la référence principale pour :

- la représentation des objets et des faits ;
- la syntaxe générale des règles ;
- les règles d’ordres 0, 1 et 2 ;
- l’instanciation d’une règle comme CSP ;
- la représentation centrée sur les variables ;
- les deux moteurs de propagation ;
- les variables libres ;
- les variables prioritaires ;
- les prémisses négatives ;
- les mots-clés et les index ;
- la récursivité et l’auto-récursivité ;
- la stratégie générale de chaînage avant.

### Sources historiques citées dans le papier

Rechercher, lorsqu’elles sont publiquement accessibles :

- Jean-Luc Dormoy, *Notice du langage et guide d’utilisation de S2.BOOJUM*, 1986 ;
- Jean-Luc Dormoy, *Résolution qualitative : complétude, interprétation physique et contrôle. Mise en œuvre dans un langage à base de règles : BOOJUM*, thèse, 1987 ;
- Jean-Louis Laurière et Michèle Vialatte, *Manuel d’utilisation de SNARK*, 1985 ;
- Michèle Vialatte, travaux ou thèse relatifs à SNARK ;
- Jean-Louis Laurière, travaux sur ALICE ;
- Roger Mohr et Thomas Henderson, *Arc and Path Consistency Revisited*, 1986 ;
- Charles Forgy, *RETE: A Fast Algorithm for the Many Pattern/Many Object Pattern Match Problem*, 1982.

Ne jamais substituer automatiquement une description moderne de RETE, Datalog ou CSP à ce qui est effectivement décrit dans BOOJUM.

### Source applicative

Utiliser la présentation fournie sur la formalisation de l’Éthique de Spinoza en SNARK/BOOJUM comme source de cas de test, sans commencer dans ce projet l’extraction exhaustive de l’Éthique.

Cette présentation montre notamment :

- des triplets récursifs ;
- des propositions utilisées comme objets ;
- des règles d’ordre deux ;
- des contraintes de différence ;
- une action `Créer(z)` ;
- des preuves par chaînage avant ;
- plusieurs étapes d’inférence en cascade.

---

## Règle méthodologique fondamentale

Pour chaque caractéristique du moteur, indiquer dans la documentation son statut :

```text
HISTORICAL
```

Explicitement décrit dans une source historique.

```text
INFERRED
```

Reconstruction raisonnable à partir de la source, mais non spécifiée complètement.

```text
MODERN_EXTENSION
```

Ajout moderne destiné à améliorer l’API, les performances, la sûreté ou l’utilisabilité.

Ne jamais présenter une extension moderne comme une caractéristique historique de BOOJUM.

---

## 1. Livrable initial : rapport de reconstruction

Avant de coder le moteur complet, produire :

```text
docs/historical_reconstruction.md
```

Ce document devra contenir :

1. la liste des sources trouvées ;
2. ce que chacune permet de savoir ;
3. la grammaire récupérable ;
4. la sémantique récupérable ;
5. les algorithmes décrits ;
6. les points ambigus ou absents ;
7. les décisions proposées pour l’implémentation moderne ;
8. un tableau de traçabilité.

Exemple :

| Fonctionnalité | Source | Statut | Décision d’implémentation |
|---|---|---|---|
| triplets récursifs | Boojum89 §2.1 | HISTORICAL | structure immuable `Triple` |
| statut par défaut VRAI | Boojum89 §2.1 | HISTORICAL | normalisation à l’insertion |
| choix de la première règle | Boojum89 | HISTORICAL | stratégie configurable |
| gestion exacte de `Créer` | insuffisant | INFERRED | témoin frais contrôlé |

Ne commencer l’implémentation avancée qu’après avoir produit ce document.

---

## 2. Périmètre fonctionnel

### 2.1 Objets

Implémenter une structure immuable :

```python
Atom
Number
Triple(subject, relation, object)
```

Les trois positions d’un triplet doivent accepter récursivement n’importe quel objet.

Exemples :

```python
Triple(Atom("Toto"), Atom("Est_Pere_de"), Atom("Lulu"))

Triple(
    Atom("Zonzon"),
    Atom("Sait"),
    Triple(Atom("Toto"), Atom("Est_Pere_de"), Atom("Lulu")),
)
```

Les objets doivent être :

- immuables ;
- hachables ;
- comparables structurellement ;
- sérialisables ;
- utilisables comme clés d’index.

Ne pas supposer que la position centrale est toujours un prédicat atomique. BOOJUM autorise des objets et variables dans toutes les positions.

### 2.2 Variables

Créer un type distinct :

```python
Variable(name)
```

Ne pas représenter les variables uniquement par des chaînes commençant par `?`.

Une variable pourra apparaître :

- dans le sujet ;
- dans la relation ;
- dans l’objet ;
- dans le statut ;
- dans un triplet imbriqué ;
- comme proposition complète.

Exemple d’ordre deux :

```python
Triple(Variable("x"), Variable("relation"), Variable("y"))
```

### 2.3 Faits et statuts

Un fait est un couple :

```python
Fact(entity: Term, status: Term)
```

La base doit prendre en charge :

- le statut par défaut `VRAI` ;
- `FAUX` ;
- `INEXISTANT` ;
- le statut implicite `NOMBRE` pour les nombres ;
- des statuts arbitraires ;
- des faits portant sur des triplets imbriqués.

Décider explicitement si une même entité peut posséder plusieurs statuts simultanés.

Le papier semble présenter le statut comme la valeur d’un objet, avec des exemples suggérant parfois une valeur fonctionnelle. Cette question doit être documentée et rendue configurable si nécessaire :

```python
FunctionalStatusStore
MultiStatusStore
```

### 2.4 Règles

Une règle contient :

```python
Rule(
    name,
    premises,
    actions,
    metadata,
)
```

Supporter au minimum les prémisses suivantes.

#### Présence ou comparaison de statut

```text
objet ' comparateur statut
```

#### Matching structurel d’un triplet

Une prémisse peut matcher un fait triplet et récupérer le triplet complet.

#### Comparaison entre termes

```text
x == y
x != y
x < y
x <= y
x > y
x >= y
```

#### Négation explicite

Distinguer :

```text
P ' FAUX
```

de :

```text
absence de P
```

et de :

```text
P ' INEXISTANT
```

Ne pas confondre ces trois notions.

### 2.5 Actions

Supporter :

- ajout d’un fait ;
- liaison arithmétique locale et déterministe pour les actions suivantes ;
- mise à jour d’un statut ;
- suppression contrôlée d’un fait ;
- création d’un symbole frais ;
- ajout de plusieurs conséquents ;
- arrêt ou signalement éventuel ;
- appel ultérieur à une fonction externe, via une interface isolée.

Exemple :

```python
AddFact(...)
Let(Variable("somme"), expression)
SetStatus(...)
RemoveFact(...)
CreateFresh("z")
```

La création d’un objet frais doit être déterministe dans les tests :

```text
_z_000001
_z_000002
```

---

## 3. Sémantique formelle minimale

Produire :

```text
docs/semantics.md
```

Ce document doit définir précisément :

- ce qu’est un terme ;
- ce qu’est une substitution ;
- l’application d’une substitution ;
- le matching ;
- l’unification éventuellement supportée ;
- une prémisse satisfaite ;
- une instanciation partielle ;
- une instanciation complète ;
- une règle applicable ;
- le déclenchement d’une règle ;
- la base de faits après déclenchement ;
- le point fixe ;
- les conditions de terminaison.

### Matching ou unification

Ne pas confondre les deux.

Le moteur de base devra au minimum supporter le matching orienté :

```text
pattern de règle → fait de la base
```

Étudier séparément l’intérêt d’une véritable unification bidirectionnelle.

Créer deux composants distincts si les deux sont supportés :

```python
PatternMatcher
Unifier
```

La version initiale du chaînage avant utilisera le matching orienté, sauf justification historique contraire.

---

## 4. Architecture logicielle souhaitée

```text
src/snarky/
    terms.py
    variables.py
    facts.py
    substitutions.py
    matching.py
    unification.py
    premises.py
    actions.py
    rules.py
    parser.py
    compiler.py

    stores/
        base.py
        naive.py
        indexed.py

    instantiation/
        base.py
        naive_join.py
        premise_centered.py
        variable_centered.py
        propagation.py
        arc_consistency.py

    engine/
        agenda.py
        conflict_resolution.py
        forward.py
        recursion.py
        provenance.py

    explanation/
        proof.py
        render_text.py
        render_graphviz.py

    serialization/
        json_format.py
        yaml_format.py

    cli.py
```

Éviter les dépendances lourdes dans le cœur du moteur.

Cible :

```text
Python 3.12+
```

Utiliser :

- `dataclasses` ou classes immuables équivalentes ;
- type hints complets ;
- `pytest` ;
- `ruff` ;
- `mypy` ou `pyright` ;
- éventuellement `lark` pour la grammaire.

---

## 5. Stratégies d’instanciation

Le projet devra implémenter plusieurs stratégies interchangeables.

### 5.1 Matcher naïf de référence

```python
NaiveInstantiationStrategy
```

Il pourra :

- examiner les prémisses dans leur ordre ;
- scanner les faits ;
- effectuer les jointures par backtracking ;
- produire toutes les substitutions complètes.

Cette stratégie servira d’oracle de correction aux stratégies optimisées.

### 5.2 Stratégie centrée sur les prémisses

```python
PremiseCenteredStrategy
```

Représenter les ensembles de faits possibles pour chaque prémisse et les joindre progressivement.

### 5.3 Stratégie centrée sur les variables

Implémenter l’idée centrale présentée dans BOOJUM :

- associer à chaque variable un domaine d’instanciation ;
- projeter les faits candidats sur les positions occupées par cette variable ;
- réduire ces domaines ;
- choisir dynamiquement la variable la plus contrainte ;
- propager le choix sur les prémisses concernées ;
- poursuivre jusqu’à une substitution complète.

Créer des structures explicites :

```python
VariableDomain
PartialInstantiation
ConstraintNetwork
InstantiationState
```

Ne pas masquer toute la logique dans une fonction récursive opaque.

### 5.4 Premier moteur de propagation

Reconstituer le premier algorithme décrit par Dormoy :

1. déterminer les couples variable–prémisse candidats ;
2. estimer leur degré de contrainte ;
3. choisir le plus contraint ;
4. réduire le domaine ;
5. propager localement ;
6. effectuer un choix si nécessaire ;
7. backtracker en cas d’échec.

Lorsque le papier ne précise pas exactement une heuristique, utiliser une interface :

```python
ChoiceHeuristic
```

Variantes possibles :

```python
SmallestDomainFirst
MostConnectedVariable
PriorityThenSmallestDomain
HistoricalApproximation
```

### 5.5 Second moteur et consistance d’arcs

Implémenter ensuite :

```python
ArcConsistencyStrategy
```

Cette stratégie doit être inspirée du mécanisme décrit dans BOOJUM et des travaux de Mohr et Henderson.

Ne pas l’appeler « algorithme exact de BOOJUM » si la reconstruction est incomplète.

Documenter :

- les variables ;
- les contraintes correspondant aux prémisses ;
- les arcs ;
- la procédure de révision ;
- les files de propagation ;
- la condition d’arrêt ;
- les différences avec AC-3 ou AC-4 ;
- ce qui est historique et ce qui est moderne.

---

## 6. Variables particulières

### 6.1 Variables libres

Détecter les variables qui n’apparaissent que dans une prémisse ou qui ne contraignent pas le reste :

```python
RuleAnalysis.free_variables
```

Tester leur traitement en dernier lorsque cela est sûr.

### 6.2 Variables prioritaires

Détecter les variables fonctionnellement déterminées après l’instanciation d’un autre terme :

```python
RuleAnalysis.priority_variables
```

Cette notion doit dépendre des propriétés déclarées du stockage.

### 6.3 Prémisses négatives

Les prémisses négatives ne doivent être évaluées que lorsque les variables nécessaires sont suffisamment instanciées.

Créer :

```python
NegativePremise.required_bound_variables()
```

Refuser ou signaler les règles dont une prémisse négative contient des variables entièrement non bornées.

---

## 7. Indexation et compilation

### 7.1 Analyse des patterns

Extraire les constantes et structures caractéristiques :

```python
PatternSignature
```

Index possibles :

- type de terme ;
- constante en position 0 ;
- constante en position 1 ;
- constante en position 2 ;
- statut ;
- chemin dans un triplet imbriqué ;
- combinaison de positions.

### 7.2 Index adaptatifs

Ne pas construire tous les index possibles.

Le compilateur analyse les règles et demande les index nécessaires :

```python
IndexPlan
```

Comparer :

- aucun index ;
- index fixes ;
- index dérivés des règles.

### 7.3 Filtrage des règles

Créer :

```python
RuleCandidateIndex
```

Lorsqu’un fait change, identifier les règles potentiellement affectées par leurs mots-clés ou signatures.

---

## 8. Agenda et chaînage avant

### 8.1 Stratégie historique

Prévoir :

```python
FirstApplicableRule
```

Documenter précisément si elle déclenche :

- la première instanciation trouvée ;
- toutes les instanciations de la règle ;
- une seule instanciation avant de recommencer.

Rendre le choix configurable si les sources ne permettent pas de trancher.

### 8.2 Stratégies modernes

Ajouter comme extensions modernes :

```python
AllNewInstantiations
SalienceThenOrder
BreadthFirstAgenda
LowestProofDepth
```

### 8.3 Refraction

Empêcher qu’un même couple :

```text
(règle, substitution)
```

se déclenche indéfiniment sans changement pertinent.

Créer :

```python
ActivationKey
```

---

## 9. Récursivité et auto-récursivité

Distinguer :

- récursivité entre règles ;
- auto-récursivité positive ;
- auto-récursivité négative ;
- cycles stériles ;
- cycles créant de nouveaux objets.

Créer :

```python
RecursionAnalyzer
RecursionPolicy
```

Le moteur doit :

- terminer sur les programmes monotones finis ;
- détecter les cycles stériles ;
- limiter les créations existentielles ;
- fournir un diagnostic de non-terminaison probable ;
- permettre `max_cycles`, `max_facts` et `max_fresh_objects`.

Conserver une implémentation simple et correcte comme référence, même si une reconstruction plus fidèle est ensuite ajoutée.

---

## 10. Provenance et preuves

Chaque fait dérivé doit avoir une provenance :

```python
Derivation(
    fact,
    rule_name,
    substitution,
    premises,
    cycle,
)
```

Un fait peut avoir plusieurs dérivations.

Le système doit pouvoir :

- produire une preuve minimale ;
- produire plusieurs preuves jusqu’à une limite ;
- détecter les cycles ;
- expliquer pourquoi une règle n’est pas applicable ;
- indiquer quelle prémisse échoue ;
- produire un graphe Graphviz.

Prévoir :

```python
engine.explain(fact)
engine.why_not(goal)
```

---

## 11. Langage externe

### 11.1 API Python

```python
from snarky import Atom, Variable, Triple, Fact, Rule, when, add

x = Variable("x")
y = Variable("y")
z = Variable("z")

rule = Rule(
    name="grand_parent",
    premises=[
        when(Triple(x, Atom("parent_de"), y)),
        when(Triple(y, Atom("parent_de"), z)),
    ],
    actions=[
        add(Triple(x, Atom("grand_parent_de"), z)),
    ],
)
```

### 11.2 DSL textuel

```text
RULE grand_parent
WHEN
    ($x parent_de $y)
    ($y parent_de $z)
THEN
    ADD ($x grand_parent_de $z)
END
```

Triplets imbriqués :

```text
RULE modus_ponens_savoir
WHEN
    ($p sait ($a implique $b))
    ($p sait $a)
THEN
    ADD ($p sait $b)
END
```

Le parser doit produire un AST et ne jamais utiliser `eval`.

---

## 12. Tests fonctionnels obligatoires

### 12.1 Ordre zéro

```text
SI alarme = active
ALORS sirène = active
```

### 12.2 Ordre un

```text
SI x parent_de y
ET y parent_de z
ALORS x grand_parent_de z
```

### 12.3 Ordre deux

```text
SI p sait (a implique b)
ET p sait a
ALORS p sait b
```

`a` et `b` peuvent eux-mêmes être des triplets.

### 12.4 Variable en position relation

```text
SI (x r y)
ET (r est_transitive VRAI)
ET (y r z)
ALORS (x r z)
```

### 12.5 Statut variable

```text
SI objet ' statut
ALORS (objet possède_statut statut)
```

### 12.6 Négation

Tester séparément :

- `FAUX` ;
- `INEXISTANT` ;
- absence ;
- négation par défaut.

### 12.7 Création d’objet

```text
SI x imagine (y est existant)
ALORS créer z
      x imagine (z affecte_de_joie y)
```

### 12.8 Auto-récursivité

Créer :

- un cas positif terminant ;
- un cycle stérile ;
- un cas génératif potentiellement infini ;
- un cas où un nouveau fait crée de nouvelles instanciations de la même règle.

### 12.9 Test Spinoza minimal

```text
x aime y
x imagine (y est inexistant)

x aime y
    → x imagine (y affecte_de_joie x)

x imagine (y est inexistant)
ET x imagine (y affecte_de_joie x)
    → x est triste
```

Le moteur doit produire la conclusion et une trace en deux étapes.

---

## 13. Tests différentiels

Pour tout petit programme :

1. exécuter le matcher naïf ;
2. exécuter la stratégie centrée sur les variables ;
3. exécuter la stratégie avec propagation ;
4. comparer les activations et les faits produits.

Utiliser Hypothesis :

```python
test_optimized_strategy_equals_naive_strategy()
```

La stratégie naïve constitue l’oracle sémantique.

---

## 14. Benchmarks

Séparer les dimensions suivantes :

- nombre de faits ;
- nombre de règles ;
- profondeur des triplets ;
- nombre de variables ;
- nombre de prémisses ;
- sélectivité ;
- partage de variables ;
- prémisses négatives ;
- récursivité ;
- nombre d’activations.

Comparer :

1. scan naïf ;
2. indexation simple ;
3. ordre fixe ;
4. ordre dynamique MRV ;
5. propagation centrée sur les variables ;
6. consistance d’arcs.

Mesurer :

- temps ;
- faits examinés ;
- matchings tentés ;
- domaines révisés ;
- backtracks ;
- mémoire approximative.

Ne pas annoncer que le moteur bat RETE sans benchmark sérieux.

---

## 15. Extensions différées

Prévoir des interfaces, sans les implémenter initialement, pour :

- solveur CSP externe ;
- contraintes arithmétiques générales au-delà de l’évaluation déterministe
  des actions `LET` ;
- propagation d’intervalles ;
- règles probabilistes ;
- truth-maintenance system ;
- non-monotonie générale ;
- appels LLM ;
- extraction automatique de règles ;
- parallélisation ;
- stockage persistant ;
- exécution distribuée.

Le cœur initial doit rester déterministe et symbolique.

---

## 16. Plan de développement

### Phase 0 — Recherche

- récupérer les sources ;
- produire `historical_reconstruction.md` ;
- identifier les ambiguïtés ;
- proposer les décisions sémantiques.

### Phase 1 — Modèle de données

- termes ;
- triplets ;
- variables ;
- faits ;
- substitutions ;
- sérialisation.

### Phase 2 — Matching naïf

- matching récursif ;
- prémisses ;
- règles ;
- actions ;
- chaînage avant simple.

### Phase 3 — Provenance

- dérivations ;
- traces ;
- preuves minimales.

### Phase 4 — Stockage indexé

- signatures ;
- index ;
- sélection des faits ;
- sélection des règles.

### Phase 5 — Instanciation centrée sur les variables

- domaines ;
- projections ;
- MRV ;
- propagation ;
- backtracking.

### Phase 6 — Variables particulières

- variables libres ;
- variables prioritaires ;
- négation sûre.

### Phase 7 — Récursivité

- refraction ;
- auto-récursivité ;
- diagnostics ;
- limites.

### Phase 8 — DSL

- grammaire ;
- parser ;
- erreurs ;
- pretty-printer.

### Phase 9 — Benchmarks

- générateurs ;
- comparaisons ;
- rapport reproductible.

### Phase 10 — Préparation de Spinoza

- test minimal ;
- objets propositionnels ;
- création fraîche ;
- preuves riches.

---

## 17. Critères d’acceptation

Le projet est utilisable lorsque :

1. les objets récursifs sont supportés ;
2. les variables peuvent apparaître partout ;
3. les règles d’ordres 0, 1 et 2 sont exécutables ;
4. le matcher naïf est testé ;
5. une stratégie centrée sur les variables donne les mêmes résultats ;
6. l’indexation évite des scans inutiles ;
7. le chaînage atteint un point fixe sur les exemples finis ;
8. les déclenchements répétés inutiles sont évités ;
9. chaque fait inféré possède une provenance ;
10. le moteur produit une preuve lisible ;
11. `FAUX`, `INEXISTANT` et absence sont distingués ;
12. les relations variables fonctionnent ;
13. les symboles frais sont contrôlés ;
14. le test minimal Spinoza réussit ;
15. toutes les décisions non établies par les sources sont documentées.

---

## 18. Exigences de qualité

- Pas de fichiers monolithiques.
- Pas de fonctions aux responsabilités multiples.
- Types dédiés plutôt que chaînes non typées.
- Pas de mutation cachée des substitutions.
- Pas de `eval`.
- Erreurs explicites et typées.
- Tests avant optimisation.
- Documentation des invariants.
- Benchmarks reproductibles.
- Résultats déterministes par défaut.
- API publique minimale.
- Optimisations désactivables.

---

## 19. Première tâche à exécuter

Ne pas commencer immédiatement par coder toutes les fonctionnalités.

Commencer par :

1. créer la structure du dépôt ;
2. télécharger ou référencer les sources historiques ;
3. lire intégralement `Boojum89.pdf` ;
4. produire `docs/historical_reconstruction.md` ;
5. produire `docs/open_questions.md` ;
6. proposer une sémantique minimale ;
7. implémenter ensuite seulement :
   - `Term`,
   - `Atom`,
   - `Number`,
   - `Variable`,
   - `Triple`,
   - `Fact`,
   - `Substitution`,
   - le matching récursif ;
8. ajouter des tests ;
9. présenter un bilan avant de poursuivre vers le moteur complet.

Dans `open_questions.md`, inclure notamment :

- unicité ou multiplicité des statuts ;
- sémantique exacte d’`INEXISTANT` ;
- différence entre absence et inexistence ;
- matching ou unification ;
- syntaxe et sémantique de la capture `:I` ;
- stratégie exacte de choix des règles ;
- stratégie exacte de choix des instanciations ;
- conséquences multiples ;
- suppression de faits ;
- création de symboles ;
- refraction ;
- gestion historique des preuves ;
- négation ;
- terminaison ;
- récursivité négative.

Ne prendre aucune décision silencieuse sur ces questions.
