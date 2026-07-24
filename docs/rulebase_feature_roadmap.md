# Feuille de route guidée par les bases de règles

Cette feuille de route part d'exemples exécutables plutôt que d'une liste
abstraite de fonctionnalités. Le catalogue correspondant se trouve dans
[`rulebases/catalog.yaml`](../rulebases/catalog.yaml).

## État vérifié

Snarky exprime aujourd'hui :

- Fibonacci et factorielle explicites ;
- transitivité d'objets égalité et hiérarchies de types ;
- date du lendemain avec calcul interne des années bissextiles ;
- un réseau de Petri borné déterministe ;
- une classification géométrique avec objets intermédiaires frais ;
- l'instance déterministe et la reformulation à sous-buts MEA du singe et des
  bananes ;
- intervalles, accords et progression harmonique inspirés de MusES ;
- recherche des quatre reines par une règle combinatoire fidèle à NéOpus et
  par construction incrémentale de placements partiels ;
- Hanoï de taille arbitraire dérécursivé en quatre règles, avec sous-problèmes
  et synchronisation représentés par des faits ;
- arc-consistance de contraintes binaires tabulaires, domaines singletons et
  contradictions exprimés par des groupes de règles réutilisables ;
- index structurels adaptatifs, rangs stables, témoins existentiels résiduels
  et ordre de jointure sélectif validés sur des domaines jusqu'à 64 valeurs ;
- groupes paramétrés, appels récursifs bornés et résolution de petits CSP/SAT
  comme infrastructures optionnelles indépendantes ;
- Sudoku p1 à p7, y compris X-Wing.

Ces bases et leurs tests avancés couvrent récursion, jointures, agrégats,
négation, mutations, groupes, séquences, hypothèses, contraintes,
classification, explication et point fixe.

## Extensions réalisées

### P1 — Arithmétique entière

`LET` accepte `%` sur deux entiers et les prémisses acceptent
`DIVISIBLE valeur BY diviseur`. La date du lendemain calcule les années
bissextiles ; MusES calcule ses intervalles modulo 12.

`CONSTRAINT expression opérateur expression` fournit désormais la forme
relationnelle. Les comparaisons simples et les égalités arithmétiques binaires
propagent leurs domaines avant le matching ; `CONSTRAINT $x + $y == $z`
travaille dans les trois directions sans transformer `LET` en opération
réversible.

`NVALUE $n OF SEQ[...]` et `ALL_DIFFERENT SEQ[...]` ajoutent les premières
contraintes globales. Leurs propagateurs partagent le protocole public
`DomainPropagator`; le premier filtre des bornes sûres, le second les
singletons et ensembles de Hall jusqu'aux triplets.

### P2 — Symboles frais

`FRESH $x PREFIX frame` lie un atome déterministe sans collision et l'enregistre
dans la substitution de provenance. Géométrie et Hanoï l'utilisent. L'arbre
des reines emploie plutôt une identité structurelle fondée sur le chemin des
choix, afin qu'une réévaluation reste idempotente.

### P3 — Collections, séquences et itération

`FiniteSet` et `COLLECT` matérialisent les valeurs distinctes d'une requête
corrélée. `FiniteSequence` conserve ordre et doublons sous la forme
`SEQ[...]`. `WINDOW` reconnaît une fenêtre bornée sur une relation,
`COMBINATIONS` énumère les sous-séquences de taille fixe et `FOR EACH` applique
un bloc d'actions.

Les multiensembles restent distincts : ils demanderont une sémantique de
quantités avant d'être ajoutés.

### P4 — Contextes isolés et recherche explicite

`InferenceSession.fork()` produit une continuation indépendante.
`HypothesisSearch` orchestre au-dessus de cette primitive un parcours BFS ou
DFS, la détection des états visités, des conditions de but et contradiction,
une limite et un chemin d'hypothèses observable.

Il n'existe ni `commit`, ni retour arrière implicite. Le singe et les bananes
NéOpus utilise des sous-buts MEA et ne dépend pas de cette recherche.

### P5 — Prédicats calculés et hiérarchie de types

`ComputedPredicate` et `PredicateRegistry` forment une liste blanche de
fonctions pures. Le DSL `CHECK`/`COMPUTE ... ARGS SEQ[...]` n'effectue aucune
résolution dynamique et impose des arguments ground.

`type_hierarchy_group()` fournit séparément la clôture `subtype` et la
propagation `instance_of` sous forme de règles ordinaires, donc avec
provenance.

### P6 — Focus MEA et agenda incrémental

`FOCUS` désigne le support dont le `timeTag` guide MEA ; le premier support
reste le repli compatible. `inspect_agenda()` expose les candidats et
`AgendaSelection` journalise les choix.

Un index conservatif des dépendances positives et une mémoire d'activations
par règle évitent de rematcher les règles non touchées. `AgendaMetrics` rend
reconstructions, recalculs et réutilisations mesurables.

### P7 — Groupes paramétrés et récursion bornée

`RuleGroupTemplate` spécialise des paramètres de construction.
`RecursiveGroupProcedure` exécute des `GroupCall` produits dynamiquement, en
DFS ou BFS, avec une limite explicite. La récursion reste dans la couche de
contrôle et ne coupe jamais une activation.

Hanoï montre toutefois qu'un problème récursif n'exige pas nécessairement ce
contrôle : lorsque les appels, leurs dépendances et leur terminaison peuvent
être réifiés, quatre règles de chaînage avant suffisent. La connaissance
spécifique du domaine reste alors entièrement déclarative.

### P8 — CSP et SAT

`ConstraintSolver` définit une interface indépendante. Le backend fini de
référence résout `ConstraintProblem`; `SatProblem` traduit une CNF vers ce
format. `ConstraintSolution.as_facts()` réinjecte les affectations. Un backend
OR-Tools pourra être ajouté sans rendre sa dépendance obligatoire.

Les quatre reines n'utilisent volontairement pas cette interface. Elles
servent d'oracle démontrant que le matcher et des placements partiels réifiés
peuvent engendrer et filtrer les combinaisons uniquement par règles. Le
solveur CSP reste un backend pour les problèmes où ce découplage est choisi,
pas un remplacement implicite de la formulation déclarative.

### P8b — Filtrage des domaines pendant l'instanciation

`ConstraintInstantiationStrategy` livre le premier étage historique inspiré
de BOOJUM : tables de prémisses positives, domaines de variables, point fixe
par file de propagateurs et candidats filtrés remis au matcher actuel. Les
tables et projections suivent les deltas par compteurs. Une suppression
poursuit le point fixe précédent ; un ajout ne réinitialise que la composante
touchée. Un sélecteur adaptatif protège les chaînes et jointures sans
réduction. Le choix MRV et le backtracking local restent différés.

### P9 — Maintenance de vérité positive

Le mode `truth_maintenance=True` rétracte après `retract()` les conclusions
hors de la fermeture des justifications positives groundées. Il élimine les
cycles sans support externe et reste désactivé par défaut.

Il ne s'agit pas d'un ATMS : environnements alternatifs, nogoods et
justifications négatives complètes restent séparés.

## Extensions encore proposées

- prémisses de collection `MEMBER` et `SIZE`, validées d'abord par les naked
  triples de Sudoku ;
- protocole factuel `choice` reliant les règles à `HypothesisSearch` ;
- affinement et généralisation de `AdaptiveInstantiationStrategy`, désormais
  validée sur des jointures favorables, neutres, défavorables et acycliques ;
- multiensembles et quantités pour des réseaux de Petri généraux ;
- adaptateur OR-Tools derrière `ConstraintSolver` ;
- coûts et heuristiques pour `HypothesisSearch` ;
- langage déclaratif unifié de procédures de groupes ;
- ATMS et provenance complète des prémisses négatives ;
- réflexion sur les règles et méta-règles NéOpus ;
- modifications partielles de faits ;
- Sudoku p8 et niveaux suivants, seulement à partir d'oracles précis.

## Ordre recommandé actualisé

1. ~~Arithmétique entière et divisibilité.~~
2. ~~Symboles frais.~~
3. ~~Ensembles, `COLLECT` et continuations isolées.~~
4. ~~Stratégie MEA et singe à sous-buts.~~
5. ~~Séquences, fenêtres, combinaisons et itération.~~
6. ~~Groupes paramétrés, prédicats sûrs et hiérarchie.~~
7. ~~Recherche explicite, CSP/SAT et TMS positif optionnel.~~
8. ~~Réifier domaines et contraintes binaires et propager l'arc-consistance
   par règles.~~
9. ~~Optimiser cette propagation par retraits à rangs stables, index de
   chemins, témoins résiduels et ordre existentiel adaptatif.~~
10. ~~Maintenir les domaines incrémentaux et ajouter `NVALUE`,
    `ALL_DIFFERENT` et les ensembles de Hall bornés.~~
11. Produire des choix déclaratifs à partir des domaines non singletons, puis
   les connecter à des branches isolées.
12. Ajouter `MEMBER` et `SIZE`, puis implémenter les naked triples de Sudoku p8
    avec `COMBINATIONS`.
13. Mesurer une éventuelle consistance généralisée de `ALL_DIFFERENT`.
14. Ne retenir les extensions restantes qu'avec une base et un oracle
    reproductibles.

La comparaison détaillée de ces voies se trouve dans
[`constraints_propagation_and_search.md`](constraints_propagation_and_search.md).
Le cap vers `choice`, le solveur CSP pédagogique et l'harmoniseur à quatre
voix est fixé dans
[`choice_backtracking_and_applications.md`](choice_backtracking_and_applications.md).

Les primitives n'ont pas changé le modèle d'exécution fondamental. MEA ajoute
un agenda explicite ; recherche, contraintes et TMS restent des sous-systèmes
optionnels. Le balayage déterministe et la stratégie naïve demeurent les
oracles par défaut.
