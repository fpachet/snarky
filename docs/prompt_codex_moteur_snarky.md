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

## État d’implémentation — juillet 2026

Ce document reste la spécification détaillée et la feuille de route de
Snarky. Les formulations au futur décrivent la cible complète ; le présent
encadré fixe l’état effectivement livré.

Sont disponibles et testés :

- termes et triplets récursifs immuables, variables dans toutes les positions
  et statuts explicites ;
- matching orienté, unification séparée, comparaisons, actions `LET` et
  génération déterministe `FRESH` ;
- chaînage avant déterministe, réfraction, limites et provenance ;
- stratégies naïve, indexée et semi-naïve interchangeables ;
- première stratégie d'instanciation par domaines : tables positives
  incrémentales, projections maintenues par compteurs, point fixe par file de
  propagateurs, Compact-Tables bitset, jointure semi-naïve directe des lignes
  actives, relations d'ordre 2, sélection adaptative avec sonde de coût
  amortie et repli automatique sur le matcher semi-naïf ;
- état de propagation observable et réversible : définitions de tables
  partageables, `DomainStore`, contradictions structurées, checkpoints et
  rollback des domaines et masques actifs ;
- groupes de règles nommés, sessions persistantes et modes `SATURATE`,
  `ONE_CYCLE`, `FIRST_CHANGE` et `UNTIL` ;
- mémoire de travail mutable avec `REMOVE` et journal chronologique
  d’`InferenceEvent` ;
- prémisses corrélées `EXISTS` et `NOT EXISTS`, avec portée locale des
  variables ;
- agrégats corrélés `COUNT`, `UNIQUE` et `COLLECT`, avec termes ensembles
  finis ;
- modulo entier, prémisse `DIVISIBLE` et continuations de session isolées par
  `fork()` ;
- ensemble de conflit explicite, `timeTag`, stratégie
  `MEAConflictStrategy` et journal d’`AgendaSelection` ;
- règles compilées, cadre mutable interne, deltas nets de suppression,
  watchers, compteurs et mémoires de jointures partielles bornées ;
- hashes structurels précalculés des termes et faits immuables ;
- plans génériques de techniques avec les états `SOLVED`, `STUCK`,
  `INCONSISTENT` et `LIMIT_REACHED` ;
- cas d’étude Spinoza complet et base Sudoku native p1–p7 résolue sans
  recherche exhaustive ;
- Hanoï dérécursivé par quatre règles et recherche des quatre reines par
  génération directe ou placements partiels, sans contrôleur métier ni
  solveur externe ;
- arc-consistance binaire tabulaire et classification de domaines exprimées
  par des groupes de règles ordinaires dans `rulebases/constraints` ;
- protocole public `DomainPropagator`, contraintes globales `NVALUE` et
  `ALL_DIFFERENT`, singletons et ensembles de Hall bornés ;
- reformulation du singe et des bananes avec buts dynamiques, parcours MEA et
  trace complète de l’agenda.

Restent notamment différés : mise à jour partielle d’un fait, ATMS complet,
adaptateur de contraintes externe, raccordement du choix/backtracking au trail
local, stratégie BOOJUM complète, méta-règles réflexives et techniques Sudoku avancées
p8–p18. Les
séquences, la recherche explicite, le choix MRV pondéré, le backtracking par
branches isolées, un backend CSP/SAT fini et un TMS positif optionnel sont
désormais réalisés.

Les décisions opérationnelles exactes sont précisées dans
[`semantics.md`](semantics.md), [`rule_groups.md`](rule_groups.md),
[`conflict_resolution.md`](conflict_resolution.md) et
[`advanced_problem_solving.md`](advanced_problem_solving.md). Le cas d’acceptation
Sudoku et ses prochains paliers sont détaillés dans
[`../sudoku/docs/implementation_plan.md`](../sudoku/docs/implementation_plan.md).
Les options d'intégration futures entre matching, propagation, recherche et
solveurs sont comparées dans
[`constraints_propagation_and_search.md`](constraints_propagation_and_search.md).
Le cap et le premier jalon livré — langage de choix, solveur CSP pédagogique
et harmoniseur à quatre voix — sont fixés dans
[`choice_backtracking_and_applications.md`](choice_backtracking_and_applications.md).

Toutes les capacités ajoutées pour le contrôle moderne, la mutation et
l’orchestration sont des `MODERN_EXTENSION`, sauf attribution historique
explicite contraire.

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

La négation par absence actuellement implémentée utilise des blocs corrélés :

```text
NOT EXISTS
    ($cell candidate $other)
    $other != $value
END_EXISTS
```

`EXISTS` et `NOT EXISTS` portent sur une conjonction locale. Les variables
déjà liées sont visibles dans le bloc ; celles introduites dans le bloc ne
s’échappent pas.

### 2.5 Agrégats corrélés

`COUNT` compare le nombre de solutions locales et `UNIQUE` exige exactement
une solution :

```text
COUNT == 2
    ($cell candidate $value)
END_COUNT

UNIQUE
    ($item selected $choice)
END_UNIQUE
```

Ils suivent les mêmes règles de corrélation et de portée locale que les blocs
existentiels.

`COLLECT` projette les valeurs distinctes de ses solutions dans un ensemble
fini immuable et n’exporte que sa variable cible :

```text
COLLECT $notes := $note
    ($chord contains $note)
END_COLLECT
```

### 2.6 Arithmétique entière et symboles frais

Les expressions `LET` acceptent aussi `%` sur deux entiers. La prémisse
`DIVISIBLE x BY y` teste la divisibilité entière et rejette un diviseur nul.
L’action `FRESH $x PREFIX node` produit un atome déterministe sans collision
dans la session et transmet cette liaison aux actions suivantes.

Une expression arithmétique peut aussi devenir une relation :

```text
CONSTRAINT $x + $y == $z
```

Les premières contraintes globales ont la syntaxe :

```text
NVALUE $count OF SEQ[$x $y $z]
ALL_DIFFERENT SEQ[$x $y $z]
```

Leur filtrage reste sûr et peut être incomplet ; le matcher ground demeure
l'oracle sémantique.

### 2.7 Groupes et plans d’exécution

Une base peut séparer ses familles de règles :

```text
GROUP preparation
    ...
END_GROUP

GROUP resolution
    ...
END_GROUP
```

Une `InferenceSession` conserve faits, réfraction, index, provenance et
journal entre les appels. `TechniquePlan` fournit un ordonnancement générique :
il essaie les groupes du plus simple au plus complexe et repart du premier
après chaque mutation effective.

Lors du premier enregistrement d’un `RuleGroup`, la session compile également
les plans de dépendances susceptibles d’invalider une activation par ajout de
fait (`NOT EXISTS`, agrégats et dépendances existentielles complexes). Les
règles sans une telle dépendance ne sont pas conservées dans ces plans. Si la
session n’en contient aucun, le chemin d’ajout saute entièrement la
réconciliation négative ; la sémantique de réfraction des groupes concernés
reste inchangée.

### 2.7 Actions

Capacités disponibles :

- ajout d’un fait ;
- liaison arithmétique locale et déterministe pour les actions suivantes ;
- suppression contrôlée d’un fait ;
- ajout de plusieurs conséquents.

Capacités encore différées :

- mise à jour partielle ou fonctionnelle d’un statut ;
- création d’un symbole frais ;
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

## 4. Architecture logicielle

```text
src/snarky/
    terms.py
    facts.py
    substitutions.py
    matching.py
    unification.py
    premises.py
    actions.py
    rules.py
    parser.py
    plans.py

    stores/
        naive.py

    instantiation/
        base.py
        naive_join.py
        indexed.py

    engine/
        forward.py
        events.py
        provenance.py

sudoku/
    domain.py
    rulebase.py
    solver.py
    fixtures/
    rules/
    tests/
```

Cette arborescence est l’architecture actuelle. Les composants de compilation,
propagation par contraintes, explication spécialisée, sérialisation et CLI ne
seront ajoutés que lorsqu’un besoin validé le justifiera. Le cœur doit
continuer d’éviter les dépendances lourdes.

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

Dans toute cette section, le mot « backtracking » concerne l’énumération
interne des liaisons d’une jointure : le matcher annule un choix local de
variable et essaie le suivant. Ce n’est pas un mécanisme de résolution de
problèmes qui poserait une hypothèse, modifierait la mémoire de travail puis
restaurerait un état antérieur.

### 5.2 Stratégie centrée sur les prémisses

```python
PremiseCenteredStrategy
```

Représenter les ensembles de faits possibles pour chaque prémisse et les joindre progressivement.

### 5.3 Stratégie centrée sur les variables

Le premier palier de l’idée centrale présentée dans BOOJUM est livré :

- ~~associer à chaque variable un domaine d’instanciation ;~~
- ~~projeter les faits candidats sur les positions occupées par cette
  variable ;~~
- ~~réduire sûrement ces domaines et passer les candidats restants au matcher
  existant ;~~
- ~~maintenir leurs projections et points fixes entre les cycles ;~~
- ~~ouvrir un protocole de propagateurs globaux avec `NVALUE` et
  `ALL_DIFFERENT` ;~~
- ~~maintenir les supports par valeur en bitsets et réutiliser les lignes
  actives dans la jointure ;~~
- choisir dynamiquement la variable la plus contrainte ;
- propager le choix sur les prémisses concernées ;
- poursuivre jusqu’à une substitution complète.

Les tables positives et leurs projections sont maintenues par delta. Une
suppression poursuit le point fixe précédent ; un ajout réinitialise seulement
la composante connexe qui peut s'élargir. Les structures explicites suivantes
restent la cible de la version complète :

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

L’implémentation actuelle maintient les index top-level simples et les trois
combinaisons de deux positions : `(sujet, relation)`, `(relation, objet)` et
`(sujet, objet)`. Elle choisit le plus petit bucket disponible après résolution
des seules positions variables. Les prémisses sont compilées en arbres de
matching et résolveurs d’index réutilisables.

Elle maintient également des index adaptatifs de chemins pour les structures
ordonnées partiellement résolues. Un pattern tel que
`($relation allows SEQ[$left $right])` peut créer les signatures composées
`(sujet, relation, objet[0])` et `(sujet, relation, objet[1])`. L'index est
construit au premier lookup seulement lorsque les buckets top-level dépassent
le seuil mesuré de huit candidats. Les ajouts et retraits suivants le
maintiennent incrémentalement.

### 7.2 Index adaptatifs

Ne pas construire tous les index possibles.

Le pattern compilé et les liaisons courantes demandent les index nécessaires :

```python
IndexPlan
```

L'implémentation combine actuellement :

- index fixes top-level ;
- signatures structurelles dérivées des règles et créées paresseusement ;
- sélection du plus petit bucket ;
- watchers utilisant les mêmes signatures ;
- seuils empêchant les index de petite taille de coûter plus qu'un scan.

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
(groupe, règle, substitution)
```

se déclenche indéfiniment sans changement pertinent.

Créer :

```python
ActivationKey
```

Après une suppression, les activations dont un fait support a disparu
redeviennent éligibles. Après un ajout, une activation fondée sur
`NOT EXISTS`, `COUNT`, `UNIQUE` ou `COLLECT` peut cesser d’être éligible ou
changer de valeur. Chaque règle reçoit un `FactDelta` révisionné avec ajouts et
retraits nets. Les watchers de requêtes sont indexés par leur signature résolue
et ne visitent que les corrélations compatibles. Les blocs factuels simples
mettent à jour leur compteur et leur premier témoin directement ; les blocs
composés conservent un recalcul compilé paresseux comme chemin de repli.

### 8.4 Groupes, sessions et modes de contrôle

`RuleGroup` est l’unité de contrôle explicite. `InferenceSession.run_group`
propose :

- `SATURATE` : point fixe du groupe ;
- `ONE_CYCLE` : un cycle complet ;
- `FIRST_CHANGE` : retour après la première mutation effective ;
- `UNTIL` : exécution jusqu’à satisfaction d’une condition déclarative.

`ForwardEngine.run` reste l’API compatible : il crée une session neuve et
sature un groupe implicite `default`.

`TechniquePlan` orchestre plusieurs groupes sans connaître le domaine. Il
sépare groupes de maintenance et techniques, mémorise les groupes essayés et
efficaces, puis renvoie un statut terminal explicite.

`InferenceSession.fork()` copie l’état observable et interne nécessaire à une
continuation indépendante : faits, réfraction, provenance, compteurs, deltas
et générateurs `FRESH`. Muter la copie ne modifie pas sa session source. Cette
primitive ne formule aucune hypothèse et n’implémente aucune boucle de
recherche ou de retour arrière ; une telle politique resterait à construire
au-dessus.

### 8.5 Ensemble de conflit et MEA

Une `ConflictResolutionStrategy` optionnelle peut remplacer le balayage
complet par une sélection d’agenda. `MEAConflictStrategy` privilégie le
`timeTag` du support marqué `FOCUS`, ou le premier support par compatibilité,
puis un vecteur LEX, la spécificité et l’ordre source. Le choix est observable
dans un `AgendaSelection`.

Dans une base à buts, `FOCUS ($goal status active)` nomme la fraîcheur locale :
un sous-but récemment ajouté passe alors devant son parent. Un index de
dépendances et une mémoire par règle maintiennent le conflit
incrémentalement. Cette stratégie publique n’est pas une méta-base réflexive.

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

Chaque ajout ou retrait effectif produit aussi un `InferenceEvent` contenant :

```python
InferenceEvent(
    sequence,
    kind,
    fact,
    rule_name,
    rule_group,
    substitution,
    premises,
    cycle,
)
```

La provenance explique les faits dérivés ; le journal explique l’évolution
chronologique, y compris les faits ensuite retirés.

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

API de contrôle :

```python
from snarky import (
    FactExists,
    ForwardEngine,
    GroupExecutionMode,
    TechniquePlan,
    parse_rule_groups,
)

groups = parse_rule_groups(rule_text)
session = ForwardEngine(()).create_session(initial_facts)
session.run_group(groups[0], mode=GroupExecutionMode.SATURATE)

plan = TechniquePlan(tuple(groups))
result = plan.solve(session, solved=FactExists(goal_premise))
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

Extensions DSL disponibles :

```text
GROUP consume
    RULE consume_pending
    WHEN
        ($item state pending)
        NOT EXISTS
            ($item blocked VRAI)
        END_EXISTS
    THEN
        REMOVE ($item state pending)
        ADD ($item state done)
    END
END_GROUP
```

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
- négation corrélée `NOT EXISTS`.

### 12.7 Création d’objet — test différé

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

### 12.10 Mutations et négation corrélée

Tester :

- ajout et retrait dans une même activation ;
- retrait absent comme non-changement ;
- ordre exact du journal ;
- invalidation d’index après retrait ;
- expiration et rééligibilité de la réfraction ;
- `EXISTS` et `NOT EXISTS` corrélés et imbriqués ;
- portée des variables locales ;
- équivalence naïve, indexée et semi-naïve.

### 12.11 Groupes et plans

Tester :

- persistance des faits, de la provenance et de la réfraction entre groupes ;
- quatre modes d’exécution ;
- retour à la technique la plus simple après progrès ;
- arrêts `SOLVED`, `STUCK`, `INCONSISTENT` et `LIMIT_REACHED`.

### 12.12 Sudoku p1–p7

Pour chaque grille :

- vérifier la fixture contre la source CLIPS et sa somme SHA-256 ;
- comparer exactement la solution finale ;
- vérifier la famille de techniques attendue ;
- vérifier que désactiver la dernière technique requise produit `STUCK` ;
- rejouer le journal indépendamment du moteur.

Le benchmark `python -m benchmarks.sudoku_rules` mesure séparément le temps,
les candidats proposés, les matchings, les cycles et les accès au cache de
témoins. La baseline du 23 juillet 2026 couvre p1, p5 et p6 sur cinq passages.

### 12.13 Catalogue des bases documentées

Chaque scénario public de `rulebases/` doit posséder un README, des règles,
des faits initiaux, un oracle minimal et un fichier d'orchestration. Le test
paramétré `tests/test_documented_rulebases.py` exécute tous les scénarios et
vérifie que `rulebases/catalog.yaml` ne contient ni entrée orpheline ni exemple
non inventorié.

Une version bornée ou symbolique doit le dire explicitement et distinguer :

- le noyau effectivement exécutable ;
- la partie du problème laissée à l'extérieur ;
- les capacités génériques qui permettraient une généralisation.

La priorisation de ces capacités est maintenue dans
[`rulebase_feature_roadmap.md`](rulebase_feature_roadmap.md).

---

## 13. Tests différentiels

Pour tout petit programme du noyau actuellement supporté :

1. exécuter le matcher naïf ;
2. exécuter la stratégie indexée exhaustive ;
3. exécuter la stratégie semi-naïve ;
4. comparer les activations, événements et faits produits.

Utiliser Hypothesis :

```python
test_optimized_strategy_equals_naive_strategy()
```

La stratégie naïve constitue l’oracle sémantique.

La première stratégie de filtrage possède des tests différentiels ciblés. Elle
devra être ajoutée au protocole génératif complet avant toute sélection par
défaut.

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
3. évaluation semi-naïve ;
4. ordre fixe et réordonnancement borné par les barrières de comparaison ;
5. filtrage forcé par domaines ;
6. file de propagateurs et sélection adaptative ;
7. comparaisons spécialisées et prémisses arithmétiques relationnelles ;
8. domaines persistants, `NVALUE`, `ALL_DIFFERENT` et ensembles de Hall ;
9. Compact-Tables, événements de retrait de valeur et jointure directe ;
10. jointure delta, sonde de coût amortie et trail local.

Le premier filtrage centré sur les variables et ses contraintes globales est
mesuré séparément. Le trail local est livré ; la sélection MRV, son pilote de
branches et la consistance généralisée de `ALL_DIFFERENT` restent des cibles
futures.

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
- contraintes arithmétiques non linéaires et globales au-delà des égalités
  binaires finies déjà couvertes par `CONSTRAINT` ;
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

Le Sudoku avancé et les bases de la thèse servent de bancs d’essai pour décider
ces ajouts à partir de besoins observés. Les quatre primitives générales
suivantes sont maintenant disponibles :

- modulo et divisibilité entière pour le calendrier et les intervalles ;
- ensembles finis et `COLLECT` pour matérialiser une projection ;
- `FRESH` pour nommer déterministement les objets construits ;
- `InferenceSession.fork()` pour isoler une continuation ;
- `MEAConflictStrategy` et `FOCUS` pour sélectionner les sous-buts ;
- séquences, fenêtres, combinaisons et itération d'actions ;
- groupes paramétrés et appels récursifs bornés ;
- recherche explicite, prédicats enregistrés, CSP/SAT fini et TMS positif.

Elles ne fournissent toujours ni méta-règles réflexives, ni ATMS. En
particulier, un fork n’est pas un « contexte hypothétique » tant que
`HypothesisSearch` ou un autre orchestrateur n’y ajoute pas explicitement une
hypothèse.

---

## 16. Plan de développement

### Réalisé

1. Sémantique opérationnelle minimale documentée.
2. Termes, substitutions, matching, unification séparée et DSL sûr.
3. Moteur naïf, réfraction, provenance et limites.
4. Stratégies indexée et semi-naïve avec métriques et benchmarks Fibonacci.
5. Actions arithmétiques `LET`.
6. Groupes nommés, sessions persistantes et modes de contrôle.
7. Mémoire mutable, événements, `EXISTS` et `NOT EXISTS` corrélés.
8. `TechniquePlan` et cas d’acceptation Sudoku p1–p7.
9. Cas Spinoza systématique exécutable et atlas de preuves.
10. Plans compilés, cadre mutable, deltas de suppression, compteurs,
    watchers et mémoires partielles bornées.
11. Agrégats corrélés `COUNT` et `UNIQUE`, avec oracle différentiel.
12. Hashes structurels précalculés, exclus de l’égalité et reconstruits après
    désérialisation.
13. Plans de réfraction négative compilés par groupe, avec chemin d’ajout
    direct lorsqu’aucune dépendance susceptible d’être invalidée n’existe.
14. Modulo entier et prémisse `DIVISIBLE`.
15. Ensembles finis et agrégat corrélé `COLLECT`.
16. Symboles déterministes `FRESH`.
17. Continuations de session isolées par `InferenceSession.fork()`, sans
    stratégie de recherche implicite.
18. Ensemble de conflit explicite, stratégie MEA, traces d’agenda et
    reformulation du singe et des bananes par sous-buts dynamiques.
19. Focus MEA explicite, index positif de règles et agenda incrémental.
20. Séquences ordonnées, fenêtres, combinaisons et boucles `FOR EACH`.
21. Groupes paramétrés et procédures récursives bornées.
22. Prédicats calculés sur registre et hiérarchie de types explicable.
23. Recherche d’hypothèses explicite au-dessus de `fork()`.
24. Interface CSP/SAT, backend fini et réinjection des solutions.
25. Maintenance de vérité positive optionnelle avec cascade.
26. Arc-consistance binaire tabulaire exprimée uniquement par groupes de
    règles, avec cas résolu, incomplet et contradictoire.
27. Rangs stables, stockage de retrait adaptatif, index de chemins
    structurels, watchers correspondants, ordre existentiel sélectif et
    témoins résiduels bornés.

### Travail documentaire historique encore ouvert

1. Produire `docs/historical_reconstruction.md`.
2. Produire `docs/open_questions.md`.
3. Consolider la traçabilité précise entre sources historiques, décisions
   inférées et extensions modernes.

### Prochain palier — robustesse du moteur mutable

1. Ajouter des tests génératifs sur de petites bases mutables et des Sudoku
   4×4.
2. Comparer naïf, indexé et semi-naïf sur les mêmes séquences d’ajouts et
   retraits.
3. ~~Mesurer reconstructions d’index, activations et matching sur p1–p6.~~
   Compléter par une mesure de mémoire.
4. ~~Filtrer les réveils négatifs, surveiller les bloqueurs simples et
   généraliser la sélection aux règles positives avec un agenda
   incrémental.~~
5. Enrichir les explications groupées par activation.

### Palier Sudoku avancé

1. ~~Implémenter p7/X-Wing avec `COUNT` et `UNIQUE`.~~
2. Implémenter p8 avec les primitives disponibles, notamment `COLLECT` si une
   projection finie simplifie réellement les règles.
3. Introduire uniquement les abstractions supplémentaires justifiées par
   plusieurs domaines.
4. Aborder ensuite triples, Swordfish, coloriage, chaînes et rectangle unique
   par paliers indépendants.

### Palier contraintes et contrôle avancé

1. ~~Définir une interface générique et un backend fini de solveur de
   contraintes.~~
2. ~~Exprimer et optimiser une première propagation binaire uniquement par
   règles.~~
3. ~~Maintenir les domaines incrémentaux et ajouter `NVALUE`,
   `ALL_DIFFERENT` et Hall borné.~~
4. ~~Séparer l'état mutable des tables, propager le delta jusqu'à la jointure
   et fournir checkpoints, rollback et contradictions structurées.~~
5. ~~Produire des faits `choice` à partir des domaines non singletons et
   spécifier leur branchement et leur backtracking explicites.~~ Raccorder
   ensuite les branches au trail réversible.
6. Ajouter un adaptateur optionnel vers OR-Tools.
7. ~~Construire une stratégie explicite d’hypothèses et de recherche au-dessus
   des sessions isolées.~~ Les coûts, poids, MRV et oracles quatre
   reines/harmoniseur sont maintenant livrés ; étudier ensuite nogoods et
   heuristiques d'impact.
8. ~~Livrer le premier filtrage centré sur les variables de BOOJUM avec un
   benchmark différentiel, le trail local, la sélection MRV et le pilote de
   branches.~~ Intégrer le trail au pilote.
9. Étudier séparément les méta-règles réflexives capables d’inspecter et de
   transformer l’agenda.

---

## 17. Critères d’acceptation

Le jalon courant du moteur est accepté lorsque :

1. les objets récursifs sont supportés ;
2. les variables peuvent apparaître partout ;
3. les règles d’ordres 0, 1 et 2 sont exécutables ;
4. le matcher naïf est testé ;
5. les stratégies indexée et semi-naïve donnent les mêmes résultats ;
6. l’indexation évite des scans inutiles sur les benchmarks couverts ;
7. le chaînage atteint un point fixe sur les exemples finis ;
8. les déclenchements répétés inutiles sont évités ;
9. chaque fait inféré possède une provenance ;
10. le moteur produit une preuve lisible ;
11. `FAUX`, `INEXISTANT` et absence sont distingués ;
12. les relations variables fonctionnent ;
13. les groupes partagent une session persistante sous quatre modes ;
14. les mutations et la négation corrélée sont journalisées et testées ;
15. Spinoza et Sudoku p1–p7 réussissent leurs tests d’intégration ;
16. `%`, `DIVISIBLE`, `COLLECT`, `FRESH` et `fork()` ont une sémantique
    déterministe testée ;
17. MEA traite les sous-buts du singe avant leurs parents, respecte `FOCUS`,
    maintient son agenda incrémental et journalise ses choix ;
18. séquences, fenêtres, combinaisons et `FOR EACH` sont testés sur les trois
    stratégies ;
19. groupes paramétrés, recherche explicite, prédicats enregistrés, CSP/SAT et
    TMS positif sont optionnels, bornés et testés ;
20. Hanoï et les quatre reines sont résolus par leurs seules règles, avec
    ordre des mouvements et ensembles de solutions vérifiés ;
21. toutes les décisions non établies par les sources sont documentées.

La stratégie centrée complète avec recherche locale, l’adaptateur OR-Tools et
l’ATMS ont leurs propres critères d’acceptation futurs ; ils ne bloquent pas
le jalon.

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

## 19. Séquence de démarrage initialement prescrite

La première séquence de travail était :

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

La structure, la sémantique minimale, le noyau et ses tests sont réalisés.
Les rapports dédiés `historical_reconstruction.md` et `open_questions.md`
restent toutefois à produire ; cette dette documentaire est reprise dans le
plan ci-dessus.

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
- politique historique de création et de nommage des symboles ;
- refraction ;
- gestion historique des preuves ;
- négation ;
- terminaison ;
- récursivité négative.

Ne prendre aucune décision silencieuse sur ces questions.

---

## 20. Spécification des extensions avancées réalisées

### 20.1 Termes séquentiels

`FiniteSequence(elements)` est immuable, hashable, ordonné et conserve les
doublons. Matching, substitution, plans compilés et cadre mutable le
parcourent récursivement. Sa syntaxe canonique est `SEQ[...]`.

`WINDOW cible := SEQ[...] VIA relation` est un macro de parsing : il produit
les prémisses factuelles adjacentes, puis un `BindPremise` vers la séquence
ground. `CombinationsPremise` produit une activation par combinaison de taille
fixe. `ForEach` possède une substitution locale par élément ; ses actions
restent dans la transaction de l’activation englobante.

### 20.2 Focus et agenda

`FactPremise.focused` est vrai pour au plus une prémisse factuelle de premier
niveau. `_activation_focus_fact` retrouve son support effectif. Sans focus, le
premier support reste utilisé.

Une `_AgendaMemory` conserve les activations par règle et la révision du
journal. `_RuleDependencyIndex` associe les constantes factuelles à des règles
et garde une classe wildcard. Après mutation, seules les lignes candidates
reçoivent le `FactDelta`. Les résultats delta-only de la stratégie semi-naïve
sont fusionnés avec les activations positives retenues ; les requêtes
non-monotones sont remplacées par leur recalcul complet.

### 20.3 Groupes paramétrés

`RuleGroupTemplate.instantiate()` applique une substitution de construction à
toutes les prémisses, actions et expressions arithmétiques. Les paramètres ne
peuvent pas être des variables de liaison locales. `RecursiveGroupProcedure`
exécute les appels produits par une fonction publique, selon DFS ou BFS, et
lève une erreur lorsque `max_calls` est atteint.

### 20.4 Fonctions calculées

`PredicateRegistry` est la seule résolution de noms autorisée.
`ComputedPremise.resolve()` reçoit l’interface minimale `TermBindings`.
Un guard retourne exclusivement `bool`; une liaison retourne exclusivement un
`Term` ground. Le DSL transmet ses arguments comme une séquence explicite.

### 20.5 Recherche

`InferenceSession.assume()` ajoute des prémisses de profondeur zéro dans une
branche et journalise leur origine. `HypothesisSearch` sature ses groupes avant
les tests de contradiction et de but, déduplique les états par ensemble de
faits et ne modifie jamais la racine.

### 20.6 Contraintes

`ConstraintSolver` reçoit un `ConstraintProblem` fini et renvoie des
`ConstraintSolution`. Le backend de référence ordonne les variables par taille
de domaine, conserve l’ordre initial comme second critère et coupe une branche
dès qu’une contrainte entièrement liée échoue. La traduction SAT utilise les
atomes `true` et `false`.

### 20.7 Maintenance de vérité

Lorsque `truth_maintenance=True`, `retract()` calcule la fermeture minimale
des faits initiaux, hypothèses actives et dérivations dont tous les supports
sont déjà dans la fermeture. Tout autre fait présent est retiré et journalisé.
Cette définition élimine les cycles auto-supportés. Elle ne modélise pas les
environnements d’un ATMS ni les dépendances négatives comme justifications.

### 20.8 Dérécursivation et génération combinatoire déclaratives

Les procédures de groupes et les solveurs de contraintes ne doivent pas
absorber une connaissance métier exprimable par les règles ordinaires.

Hanoï réifie chaque appel récursif comme un sujet possédant `disks`, `from`,
`to`, `via`, `first_child`, `second_child` et `state`. `FRESH` crée les
sous-problèmes, `LET` calcule `n - 1`, et les faits `state done`
synchronisent l'appel suivant et le retour au père. La saturation d'un groupe
de quatre règles produit ainsi le plan complet dans l'ordre causal.

Les quatre reines possèdent deux oracles déclaratifs. La traduction fixe lie
une case par colonne et place les comparaisons sitôt chaque nouvelle case
connue. La traduction générique réifie les placements partiels, utilise
`NOT EXISTS` sur la relation dérivée `attacks`, puis copie chaque branche sûre
avec `COLLECT`, un identifiant structurel `($parent chooses $cell)` et
`FOR EACH`. Cette identité rend la génération idempotente même après une
réévaluation conservatrice d'agrégat. Toutes les branches coexistent dans la
mémoire de travail ; il n'existe aucun backtracking implicite.

Ces deux bases constituent des critères architecturaux : l'interface CSP/SAT
et `RecursiveGroupProcedure` restent disponibles comme mécanismes généraux,
mais ne sont pas nécessaires à ces résolutions et ne doivent pas en devenir
les implémentations principales.
