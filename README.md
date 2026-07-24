# Snarky

Snarky est un moteur d’inférence symbolique en Python inspiré de SNARK, de
Jean-Louis Laurière, et de BOOJUM, développé par Jean-Luc Dormoy. Il ne cherche
pas à reproduire exactement BOOJUM : Snarky possède sa propre sémantique et
sera notamment enrichi par du raisonnement sous contraintes.

## Pourquoi « Snarky » ?

Le nom rend d’abord hommage au langage historique SNARK, l’une des principales
sources d’inspiration du projet. Il constitue aussi un clin d’œil à Snarky
Puppy, groupe emblématique de la fusion musicale.

Cette idée de fusion décrit l’ambition de Snarky : faire coopérer dans un même
moteur des langages de règles symboliques, des solveurs de contraintes tels
qu’OR-Tools et, à terme, d’autres algorithmes d’inférence. Snarky ne désigne donc
pas une réimplémentation de SNARK ou de BOOJUM, mais un moteur hybride qui en
prolonge certains principes.

L’objectif est de construire un moteur expressif, déterministe et testable,
capable de manipuler :

- des règles d’ordre 0, 1 et 2 ;
- des variables dans les trois positions d’un triplet, y compris en position
  relation ;
- des triplets récursifs et des propositions utilisées comme objets ;
- des statuts explicites tels que `VRAI`, `FAUX` et `INEXISTANT` ;
- le chaînage avant récursif, la réfraction et la provenance des faits ;
- plusieurs stratégies d’instanciation, d’un matcher naïf de référence à des
  stratégies centrées sur les variables et la propagation de contraintes.

Le projet ne prétend pas reproduire à l’identique le logiciel historique
BOOJUM. Chaque fonctionnalité devra être qualifiée comme `HISTORICAL`,
`INFERRED` ou `MODERN_EXTENSION`.

## Contraintes et filtrage du matching

Snarky peut maintenant utiliser les variables d'une règle comme des domaines
finis avant d'en énumérer les instanciations. Cette étape ne remplace pas le
matcher : elle élimine d'abord les valeurs et les lignes factuelles sans
support, puis le matcher compilé vérifie exactement les activations restantes.

```text
faits candidats
      ↓
tables de prémisses et domaines de variables
      ↓
propagation des contraintes jusqu'au point fixe
      ↓
lignes actives des Compact-Tables
      ↓
jointure semi-naïve sur les seuls faits nouveaux
      ↓
validation exacte par le matcher
```

Les contraintes simples peuvent être écrites directement dans les règles :

```text
CONSTRAINT $left + $right == $total
CONSTRAINT $start < $end
NVALUE $count OF SEQ[$x $y $z]
ALL_DIFFERENT SEQ[$x $y $z]
```

Le filtre possède des propagateurs spécialisés pour l'égalité, la différence,
les ordres, la divisibilité et l'arithmétique binaire. `NVALUE` propage des
bornes sur le nombre de valeurs distinctes ; `ALL_DIFFERENT` traite les
singletons et les ensembles de Hall jusqu'à la taille trois. L'interface
`DomainPropagator` permet d'ajouter d'autres contraintes globales.

Pour accélérer ce chemin :

- les tables, projections et domaines sont conservés entre les cycles ;
- `FactDelta` ne met à jour que les lignes ajoutées ou supprimées ;
- une file ne réveille que les propagateurs incidents aux domaines modifiés ;
- les supports `(variable, valeur)` et les lignes actives sont des bitsets ;
- la jointure réutilise les liaisons déjà validées des Compact-Tables ;
- un cycle append-only n'énumère que les activations contenant un fait
  nouveau ;
- `AdaptiveInstantiationStrategy` revient au matcher semi-naïf lorsque le
  filtrage ne paraît pas rentable.

Sur les trois Sudoku de référence, la dernière jointure delta réduit encore
les matchings de 9 à 22,5 % par rapport aux Compact-Tables initiales :

| Niveau | Matchings avant | Après | Temps avant | Après |
|---|---:|---:|---:|---:|
| p1 | 63 946 | 49 531 | 0,287 s | 0,254 s |
| p6 | 138 846 | 126 198 | 0,576 s | 0,534 s |
| p7 | 216 643 | 195 160 | 0,804 s | 0,731 s |

`DomainStore` et `PropagationState` exposent également les réductions,
contradictions, checkpoints et rollbacks des domaines et masques. Ce socle
est désormais complété par une première recherche explicite
`SessionChoiceSearch`. Voir
[`docs/reversible_propagation.md`](docs/reversible_propagation.md) et
[`benchmarks/README.md`](benchmarks/README.md).

## Choix pondérés et backtracking explicite

`ChoicePoint` représente un ensemble fini d'alternatives factuelles.
`SessionChoiceSearch` sélectionne un point, pose un checkpoint réversible,
sature les groupes de règles, puis conserve la solution, restaure la branche
sur contradiction ou poursuit jusqu'au but. Le DFS ne copie plus une session
par alternative. BFS et best-first placent des branches différées dans leur
frontière et ne créent leur session qu'au moment de l'exploration.

Le DSL peut maintenant produire ces choix en instanciant directement un
fait :

```text
RULE assign_queen
WHEN
    (n_queens variable $queen)
    NOT EXISTS ($queen value $known)
THEN
    CHOICE ($queen decision $row) WEIGHT $weight
    FROM
        ($queen candidate $row)
        ($queen choice_weight SEQ[$row $weight])
    END_CHOICE
END
```

Le `WHEN` établit le contexte de l'objet. La sous-requête `FROM` énumère les
instanciations possibles du fait cible. Plusieurs `CHOICE` dans la même règle
sont séquentiels : les variables choisies par le premier sont visibles dans
le suivant. Les actions déterministes placées après le dernier choix reprennent
quand tous les faits cibles existent dans la branche.

Le premier jalon fournit :

- sélection MRV et ordre déterministe par poids ;
- ordre probabiliste reproductible avec une graine ;
- parcours profondeur, largeur ou meilleur poids d'abord ;
- limites en nœuds et en solutions ;
- traces `choice`, `decision`, `contradiction`, `backtrack`, `solution` ;
- conservation de la session parente ;
- restauration des faits, provenance, réfraction et tags temporels par
  `InferenceSession.checkpoint()`, `rollback()` et `release()`.

Les formes existentielles simples s'écrivent sans terminateur :

```text
EXISTS ($item selected $value)
NOT EXISTS ($item rejected $value)
```

Les conjonctions utilisent toujours un bloc. `NOT EXISTS` se ferme désormais
par `END_NOT_EXISTS`; l'ancien `END_EXISTS` reste accepté pour compatibilité.

Un poids nul reste une possibilité faisable examinée après les poids positifs.
Les poids orientent la recherche et sont cumulés en log-espace ; ils ne
modifient jamais les contraintes dures.

Le DFS restaure maintenant ses branches sœurs par un trail complet de
`InferenceSession`, sans recopier les faits ni la provenance à chaque
alternative. Le trail local de `PropagationState` reste distinct et sert aux
domaines internes des propagateurs. La sémantique complète est décrite dans
[`docs/choice_search.md`](docs/choice_search.md).

La recherche partage aussi l'index factuel entre le matcher et le producteur
de choix, clone un index présemé pour les branches, met en cache les snapshots
de faits et maintient les deltas sans rescanner toute la mémoire. Best-first
utilise un tas stable, BFS une file double. Ces changements ne modifient ni les
solutions, ni les poids, ni les compteurs logiques.

## État actuel

Le dépôt contient un moteur Python semi-naïf par défaut, une stratégie naïve
servant de référence sémantique, une stratégie indexée exhaustive et une
première `ConstraintInstantiationStrategy`. Cette dernière conserve des
tables positives et des compteurs de projection par règle, maintient les
domaines entre les cycles, filtre jusqu'au point fixe, puis laisse le matcher
compilé produire les activations. Les suppressions réduisent l'état existant ;
un ajout ne réinitialise que la composante de contraintes concernée. Une
`AdaptiveInstantiationStrategy` réserve ce travail aux graphes cycliques,
assez grands et assez sélectifs ; les autres formes retombent automatiquement
sur la stratégie semi-naïve. Dans les cas ambigus et récurrents, elle peut
mesurer une fois les deux chemins et mémoriser le plus rapide ; cette sonde est
différée pour ne pas pénaliser les règles courtes. Les égalités, différences,
ordres et divisibilités simples possèdent désormais des propagateurs
spécialisés ; le mode adaptatif peut donc les sélectionner sans énumérer leur
produit cartésien. Le cœur prend en charge
les termes et triplets récursifs immuables, les variables dans toutes les
positions, le matching orienté, l’unification bidirectionnelle séparée, les
statuts explicites, le chaînage avant jusqu’au point fixe, la réfraction et la
provenance avec profondeur de preuve. Des groupes de règles nommés peuvent
désormais être appelés successivement dans une même session persistante, en
saturation, pour un cycle, jusqu’au premier changement ou jusqu’à un motif de
fait.

Le DSL sait également exécuter des actions arithmétiques séquentielles `LET`
et créer des symboles déterministes avec `FRESH` dans la conclusion des
règles. Cette fonctionnalité est une
`MODERN_EXTENSION` : elle évalue de manière sûre des expressions numériques
avec `+`, `-`, `*`, `/`, `%`, précédence et parenthèses, puis transmet les
liaisons calculées aux actions suivantes. La prémisse `DIVISIBLE` couvre les
tests de divisibilité entière. Une prémisse déclarative telle que
`CONSTRAINT $x + $y == $z` réutilise le même AST et filtre les domaines
numériques dans les trois directions. Le filtrage peut maintenant être suivi
d'un choix explicite et d'un backtracking piloté ; il ne déclenche toujours
aucune recherche implicite pendant l'instanciation d'une règle.

Les contraintes globales utilisent la même infrastructure :

```text
NVALUE $count OF SEQ[$x $y $z]
ALL_DIFFERENT SEQ[$x $y $z]
```

`NVALUE` propage des bornes sûres sur le nombre de valeurs distinctes.
`ALL_DIFFERENT` propage les singletons et les ensembles de Hall jusqu'à la
taille trois. L'interface publique `DomainPropagator` permet d'ajouter d'autres
propagateurs sans modifier les matchers.

Les tables extensionnelles du filtre utilisent des masques de bits persistants
par couple `(variable, valeur)`. Une suppression de valeur désactive seulement
les lignes qu'elle supportait, puis la jointure lie directement les lignes
actives déjà validées, sans refaire le matching structurel. Les définitions
de tables sont maintenant séparées de leur état mutable et la jointure suit
les lignes nouvelles de `FactDelta` : un cycle append-only ne produit que ses
nouvelles activations.

`DomainStore` et `PropagationState` exposent les réductions, contradictions,
checkpoints et rollbacks des domaines et masques actifs. Le trail local est
livré. `InferenceSession` expose aussi un checkpoint complet, utilisé par le
DFS de choix ; BFS et best-first gardent plusieurs descripteurs différés et
ne créent leur fork rapide qu'à l'exploration.

La mémoire de travail accepte maintenant `REMOVE`, avec un journal
chronologique des ajouts et retraits. Les prémisses corrélées `EXISTS` et
`NOT EXISTS` permettent de raisonner sur la présence ou l’absence d’une
configuration sans confondre cette absence avec le statut explicite
`INEXISTANT`.

Les ensembles finis immuables et la prémisse corrélée `COLLECT` permettent de
matérialiser les valeurs produites par une sous-requête. Les séquences
ordonnées `SEQ[...]`, `WINDOW`, `COMBINATIONS` et `FOR EACH` couvrent maintenant
les fenêtres, les choix de taille fixe et l'itération d'actions.

Une session peut être copiée avec `fork()`. `HypothesisSearch` construit
explicitement une recherche BFS ou DFS au-dessus de cette primitive, sans
ajouter de retour arrière caché au chaînage avant. Une interface CSP/SAT et un
solveur fini de référence fournissent également un premier couplage règles–
contraintes.

Une stratégie de conflit optionnelle `MEAConflictStrategy` permet de
sélectionner une activation à la fois selon la fraîcheur locale d'une prémisse
`FOCUS`, ou du premier fait support par compatibilité, puis selon un ordre LEX
déterministe. Son agenda mémorise les activations par règle et utilise un index
de dépendances pour ne rematcher que les règles touchées. La reformulation
NéOpus du singe et des bananes l’utilise pour traiter chaque sous-but avant son
but parent, sans backtracking.

Les groupes peuvent être spécialisés avec `RuleGroupTemplate` et pilotés par
des appels récursifs bornés. Les fonctions externes doivent être enregistrées
comme `ComputedPredicate`; la hiérarchie de types réutilisable reste exprimée
par des règles ordinaires. Une maintenance de vérité positive est disponible
sur option et ne modifie pas le comportement par défaut.

`TechniquePlan` fournit une orchestration générique de groupes ordonnés :
après chaque changement, il repart du groupe le plus simple et distingue les
terminaisons `SOLVED`, `STUCK`, `INCONSISTENT` et `LIMIT_REACHED`. Le projet
Sudoku valide conjointement ces capacités sur sept niveaux progressifs.

Le contenu actuel comprend :

- [l’atlas web de l’Éthique III](https://fpachet.github.io/snarky/), une
  exploration statique des textes, affects, 27 explications, règles, chaînes
  de preuve et dépendances producteur–consommateur entre règles, publiée
  automatiquement par GitHub Pages ;

- [`docs/prompt_codex_moteur_snarky.md`](docs/prompt_codex_moteur_snarky.md),
  la spécification détaillée du moteur ;
- [`docs/prompt_codex_spinoza_ethique_III.md`](docs/prompt_codex_spinoza_ethique_III.md),
  la spécification du cas d’étude Spinoza ;
- [`docs/Gondran.ppt`](docs/Gondran.ppt), la présentation historique de Michel
  Gondran sur la modélisation de l’*Éthique* en SNARK/BOOJUM ;
- [`docs/Cavarretta-X1988-SpinozaExpertSystem.pdf`](docs/Cavarretta-X1988-SpinozaExpertSystem.pdf),
  le rapport complet de Fabrice Cavarretta sur SpinoLog ; ses apports possibles
  au projet sont analysés dans
  [`spinoza/reports/spinolog_1988_enrichment.md`](spinoza/reports/spinolog_1988_enrichment.md) ;
- [`spinoza`](spinoza/README.md), le cas d'étude complet de l'*Éthique III* :
  corpus structuré des 59 propositions, reproduction historique des quatre
  preuves de Gondran et reconstruction systématique exécutable de E3P01 à
  E3P59 ainsi que des 48 définitions finales et de la définition générale des
  affects, avec faits, règles, provenance et contre-cas explicites ;
- [`third_party/test_rulebases`](third_party/test_rulebases/README.md), une
  sélection de corpus de règles externes ;
- [`tests/rulebases/debug`](tests/rulebases/debug/README.md), une petite base
  native destinée au debug du moteur ;
- [`rulebases`](rulebases/README.md), le catalogue unifié des exemples
  exécutables : exemples pédagogiques, propagation de contraintes binaires
  écrite en règles, contraintes globales `NVALUE`/`ALL_DIFFERENT` et huit
  reformulations issues de la thèse NéOpus,
  notamment Hanoï dérécursivé et les quatre reines engendrées entièrement par
  règles ;
- [`csp_solver`](csp_solver/README.md), un solveur CSP binaire pédagogique :
  variables, domaines, relations extensionnelles, propagation et
  contradictions sont des faits et règles Snarky ; les quatre reines en sont
  le premier oracle ;
- [`harmonizer`](harmonizer/README.md), le premier incrément de l'harmoniseur
  SATB : contraintes dures, propagation binaire, choix pondérés par des
  marginales et recherche best-first ;
- [`docs/semantics.md`](docs/semantics.md), les décisions sémantiques du moteur
  de référence ;
- [`docs/arithmetic_actions.md`](docs/arithmetic_actions.md), la syntaxe et la
  sémantique des liaisons arithmétiques séquentielles `LET` ;
- [`docs/global_constraints.md`](docs/global_constraints.md), la sémantique
  de `NVALUE`, `ALL_DIFFERENT`, des ensembles de Hall et de
  `DomainPropagator` ;
- [`docs/collections_fresh_and_contexts.md`](docs/collections_fresh_and_contexts.md),
  les ensembles finis, `COLLECT`, `FRESH` et les continuations isolées ;
- [`docs/rule_groups.md`](docs/rule_groups.md), les sessions persistantes, la
  syntaxe des groupes de règles et leurs différents modes d’appel ;
- [`docs/conflict_resolution.md`](docs/conflict_resolution.md), l’ensemble de
  conflit, les `timeTag`, la stratégie MEA et les traces d’agenda ;
- [`docs/advanced_problem_solving.md`](docs/advanced_problem_solving.md), les
  séquences, groupes paramétrés, prédicats sûrs, hypothèses, CSP/SAT et TMS ;
- [`docs/constraints_propagation_and_search.md`](docs/constraints_propagation_and_search.md),
  les architectures possibles pour combiner instanciation par contraintes,
  clauses combinatoires, propagation, choix explicites, solveurs externes et
  ATMS ;
- [`docs/reversible_propagation.md`](docs/reversible_propagation.md), l'état
  observable, le trail de domaines et masques, la jointure delta et leurs
  benchmarks ;
- [`docs/choice_backtracking_and_applications.md`](docs/choice_backtracking_and_applications.md),
  le cap architectural et l'état des deux applications de référence ;
- [`docs/choice_search.md`](docs/choice_search.md), l'API, la sémantique et
  les limites du premier pilote de choix/backtracking ;
- [`docs/parallel_choice_search.md`](docs/parallel_choice_search.md), la piste
  différée d'un fork par processus suivi d'un DFS local sur trail, avec
  déterminisme, granularité et benchmarks requis ;
- [`docs/choice_search_optimization_plan.md`](docs/choice_search_optimization_plan.md),
  le plan profilé désormais exécuté, ses décisions et ses gains avant
  l'extension du CSP et de l'harmoniseur ;
- [`docs/mutations_and_negation.md`](docs/mutations_and_negation.md), la
  suppression de faits, le journal de mutations et les blocs corrélés
  `EXISTS`/`NOT EXISTS` ;
- [`docs/rulebase_feature_roadmap.md`](docs/rulebase_feature_roadmap.md), la
  feuille de route des extensions motivées par les bases concrètes ;
- [`sudoku`](sudoku/README.md), le sous-projet autonome qui organise la base
  de règles, les fixtures natives, le solveur orchestré et le plan incrémental
  pour résoudre et expliquer les niveaux essentiels de l’exemple Sudoku
  CLIPS ;
- [`docs/optimization_plan.md`](docs/optimization_plan.md), le plan mesurable
  pour faire évoluer le moteur naïf vers des stratégies indexées, semi-naïves
  et centrées sur les contraintes ;
- [`benchmarks`](benchmarks/README.md), les scénarios reproductibles, leurs
  compteurs algorithmiques et les baselines de performance ;
- [`src/snarky`](src/snarky), le package Python et son API publique.

La base Fibonacci explicite utilise `LET $somme := $gauche + $droite` et ne
reçoit qu’un fait racine : les sommes et les rangs des fils ne sont plus
préchargés sous forme de tables.

Les modifications partielles de faits et un ATMS complet restent à
implémenter. L’adaptateur vers un solveur externe tel qu’OR-Tools reste
optionnel et futur ; le backend fini portable valide déjà l’interface.
Le choix MRV, le backtracking sur trail réversible et leurs deux applications
d'intégration sont maintenant livrés. Les prochains paliers enrichiront le
protocole déclaratif de choix, étudieront la restauration incrémentale des
caches du matcher et étendront progressivement l'harmoniseur vers le profil
`ROY_1998`. L’évaluation semi-naïve demeure le mode par défaut de
`ForwardEngine`.

## Démarrage rapide

Le projet cible Python 3.12 ou ultérieur. Depuis la racine du dépôt :

```sh
python -m pip install -e '.[dev]'
pytest
```

Pour une boucle locale rapide, les grands balayages d’intégration peuvent être
écartés avec `pytest -m "not slow"`. Si `pytest-xdist` est installé
séparément, la suite complète peut exploiter plusieurs cœurs avec
`pytest -n auto`.

Le plan et les baselines de performance, notamment pour Fibonacci et Sudoku,
sont consignés dans [`docs/optimization_plan.md`](docs/optimization_plan.md).

Exemple minimal avec l’API Python :

```python
from snarky import Atom, Fact, ForwardEngine, Rule, Triple, Variable, add, when

x = Variable("x")
y = Variable("y")
z = Variable("z")

rule = Rule(
    name="grand_parent",
    premises=(
        when(Triple(x, Atom("parent_de"), y)),
        when(Triple(y, Atom("parent_de"), z)),
    ),
    actions=(add(Triple(x, Atom("grand_parent_de"), z)),),
)

facts = (
    Fact(Triple(Atom("alice"), Atom("parent_de"), Atom("bob"))),
    Fact(Triple(Atom("bob"), Atom("parent_de"), Atom("clara"))),
)
result = ForwardEngine((rule,)).run(facts)
```

Le moteur utilise par défaut la stratégie semi-naïve. Elle maintient des index
persistants et ne recalcule que les jointures contenant un fait nouveau, sans
modifier l'ordre observable des activations. L'appel sans paramètre `strategy`
dans l'exemple ci-dessus utilise donc directement cette implémentation.

La stratégie naïve reste disponible comme oracle sémantique et comme option de
diagnostic explicite :

```python
from snarky import NaiveInstantiationStrategy

result = ForwardEngine(
    (rule,),
    strategy=NaiveInstantiationStrategy(),
).run(facts)
```

`IndexedInstantiationStrategy` reste disponible pour mesurer séparément le
bénéfice de l'indexation exhaustive.

Les contraintes binaires ont depuis motivé des optimisations générales :
rangs d'index stables, stockage de retrait adaptatif, index paresseux sur les
chemins de termes structurés, ordre sélectif des sous-jointures existentielles
et deux témoins résiduels par corrélation. Sur une chaîne de 64 variables à
64 valeurs, elles ramènent le matching de 560 196 à 310 212 tentatives et le
temps de 2,566 s à 1,684 s, soit un gain ×1,52. Les résultats A/B et les
gardes de non-régression Sudoku/Fibonacci se trouvent dans
[`benchmarks/README.md`](benchmarks/README.md).

Pour les sessions persistantes, les mutations, la négation et les plans de
groupes, voir respectivement
[`docs/rule_groups.md`](docs/rule_groups.md),
[`docs/mutations_and_negation.md`](docs/mutations_and_negation.md) et la
[spécification détaillée](docs/prompt_codex_moteur_snarky.md).

Le benchmark A/B du précalcul des hashes structurels ramenait `F(15)` de
6,084 s à 0,953 s, soit un gain ×6,39. Le chemin rapide qui désactive ensuite
la réconciliation négative pour les groupes sans dépendance négative ramène
`F(15)` de 0,919 s à 0,338 s et `F(19)` de 53,603 s à 4,618 s, sans modifier
les faits, activations ou matchings. `F(20)` prend désormais 8,791 s en
médiane et `F(21)` 12,309 s sur un passage : ce sont respectivement les
limites interactive et ponctuelle raisonnables sur la machine de
développement. `F(22)` dépasserait la garde par défaut de 100 000 faits.
Les séries antérieures sont conservées et explicitement datées dans la
documentation des benchmarks.
Le benchmark Sudoku mesure désormais p1 à 0,247 s, p5 à 0,535 s et p6 à
0,468 s en médiane. Après la réduction algorithmique des matchings, les hashes
structurels précalculés des termes et faits immuables ajoutent un gain de 24 à
27 % sans modifier leur nombre. Les commandes reproductibles et les compteurs
sont décrits dans
[`benchmarks/README.md`](benchmarks/README.md).

Sur le chemin de filtrage forcé, les Compact-Tables suppriment ensuite tous
les rescans de lignes et évitent le second matching structurel. Les médianes
A/B passent de 0,377 à 0,287 s sur p1, de 0,656 à 0,576 s sur p6 et de 0,926
à 0,804 s sur p7, soit des gains ×1,14 à ×1,31.

La jointure semi-naïve des mêmes tables réduit ensuite les matchings de
63 946 à 49 531 sur p1, de 138 846 à 126 198 sur p6 et de 216 643 à 195 160
sur p7. Les médianes Compact passent respectivement de 0,287 à 0,254 s, de
0,576 à 0,534 s et de 0,804 à 0,731 s, soit encore 7 à 12 %. Le benchmark du
trail mesure ×27,84 face à la copie complète d'un état de 1 000 domaines
lorsqu'une branche n'en touche que trois.

Le DFS de choix matérialise maintenant les frères à la demande puis restaure
la session en place. Sur N reines extensionnel, N=14 passe de 16,035 s avec
forks avides à 2,675 s avec le noyau actuel, soit ×5,99 (`-83,3 %`) à
20 nœuds et 8 échecs inchangés. La formulation intensionnelle réduit ensuite
15 513 faits à 253 et atteint 1,145 s : gain cumulé ×14,0 (`-92,9 %`).

Sur l'harmoniseur court, le noyau optimisé ramène la formulation extensionnelle
de 257,78 à 99,31 ms. Les règles de transition intensionales réduisent
401 faits à 32 et atteignent 37,60 ms, soit ×6,86 (`-85,4 %`) depuis cette
baseline. Sur quatre positions, la reformulation passe de 2,573 s et
1 171 faits à 562,00 ms et 64 faits, soit ×4,58.

Sur le micro-benchmark d'agenda à 200 règles indépendantes, une mutation ciblée
ne recalcule qu'une règle et en réutilise 199. La médiane passe de 2,206 ms
pour une construction froide à 0,572 ms pour la mise à jour incrémentale,
soit ×3,86.

La suite complète compte désormais 395 tests et s’exécute en moins de onze
secondes sur cette même machine, contre 26,05 s avant la mise en cache du
catalogue de provenance
Spinoza et 76,50 s avant les optimisations.

L'architecture et l'API réversibles sont détaillées dans
[`docs/reversible_propagation.md`](docs/reversible_propagation.md).

## Base de debug initiale

La base `mini_snarky` constitue le premier test d’intégration. Elle tient
en quatre règles et neuf faits initiaux, tout en testant :

1. une jointure sur deux prémisses ;
2. une relation variable ;
3. une clôture transitive récursive ;
4. des propositions imbriquées ;
5. une variable représentant une proposition complète ;
6. un statut explicite `FAUX`.

Le moteur semi-naïf par défaut et l'oracle naïf reproduisent le même point fixe
attendu : six faits dérivés, dont un à profondeur de preuve deux. Voir :

- [`mini_snarky.rules`](tests/rulebases/debug/mini_snarky.rules) ;
- [`initial_facts.yaml`](tests/rulebases/debug/initial_facts.yaml) ;
- [`expected.yaml`](tests/rulebases/debug/expected.yaml).

## Corpus externes

Le dépôt contient des sélections provenant de W3C N3, W3C RIF, CLIPS,
ChaseBench, rbench/OpenRuleBench, Soufflé et EYE. Les versions, chemins
sélectionnés, licences trouvées et sommes SHA-256 sont consignés dans
[`third_party/test_rulebases/manifest.yaml`](third_party/test_rulebases/manifest.yaml).

Ces corpus restent dans leur langage source. Ils devront être traduits par des
adaptateurs explicites ; les comparaisons ne seront valides que pour
l’intersection des sémantiques.

Les snapshots ChaseBench et rbench ne contiennent pas de licence explicite.
Leur redistribution doit donc être réévaluée avant de rendre ce dépôt public.

Pour reconstruire la sélection dans un dépôt propre :

```sh
./scripts/fetch_test_rulebases.sh
```

Le script vérifie les révisions et les sommes SHA-256, et refuse d’écraser un
répertoire existant.

## Projet Sudoku

Le répertoire [`sudoku`](sudoku/README.md) isole le cas d’étude Sudoku du cœur
du moteur et du corpus CLIPS original. Il contient :

- le [catalogue de la base de règles](sudoku/rules/catalog.yaml) p1 à p7 ;
- les règles natives et leur chargeur ;
- les fixtures natives vérifiées contre les sources CLIPS ;
- l’orchestrateur et le rendu des explications ;
- le [plan d’implémentation](sudoku/docs/implementation_plan.md), avec un
  critère d’acceptation pour chaque étape.

La base native est exécutable : les sept grilles p1 à p7 sont résolues avec les
familles de techniques annoncées par le corpus CLIPS, sans recherche
exhaustive ni solveur externe. Chaque retrait de candidat est conservé dans
une trace rejouable.

## Plan de développement

1. Produire la reconstruction historique et documenter les questions
   ouvertes.
2. ~~Définir la sémantique opérationnelle minimale.~~
3. ~~Implémenter les termes immuables, substitutions et matching récursif.~~
4. ~~Faire passer la base `mini_snarky` avec un moteur naïf de référence.~~
5. ~~Ajouter la réfraction et la provenance avec profondeur de preuve.~~
6. ~~Introduire l’action arithmétique séquentielle `LET`, documenter sa
   sémantique et reformuler Fibonacci sans tables de prédécesseurs ni de
   sommes.~~
7. ~~Ajouter une première stratégie d’instanciation indexée, des compteurs et
   une baseline Fibonacci reproductible jusqu’à `F(17)`.~~
8. ~~Ajouter des index persistants par règle et une évaluation semi-naïve
   pilotée par les faits nouveaux, avec ordre et provenance identiques au
   moteur naïf.~~
9. ~~Ajouter des groupes de règles nommés, une mémoire de travail persistante
   entre leurs appels et plusieurs modes de contrôle du chaînage avant.~~
10. ~~Ajouter les suppressions, un journal de mutations et les prémisses
    corrélées `EXISTS`/`NOT EXISTS`, puis résoudre les niveaux Sudoku p1 à
    p6 par techniques progressives.~~
11. Renforcer le moteur mutable par des tests génératifs 4×4, des tests
    différentiels sur les retraits et des mesures de reconstruction d’index.
12. ~~Reproduire les démonstrations Spinoza P19, P21, P22 et P33, importer la
    structure textuelle complète de l'Éthique III, puis rendre exécutables les
    59 propositions, les 48 définitions finales et la définition générale dans
    le modèle systématique.~~
13. ~~Ajouter une couche optionnelle de raisonnement par contraintes pour
   exprimer et résoudre des problèmes de satisfaction (CSP, SAT et variantes),
   avec une interface générique, un backend fini de référence et une
   réinjection des solutions comme faits.~~ Ajouter si nécessaire un
   adaptateur OR-Tools optionnel.
14. Exécuter les benchmarks externes adaptés, puis ajouter des cas de test
    dédiés au couplage entre règles et contraintes.
15. ~~Implémenter p7/X-Wing avec `COUNT` et `UNIQUE`.~~ Aborder le Sudoku
    avancé à partir de p8. Les ensembles finis, `COLLECT`, `FRESH` et les
    continuations isolées sont désormais disponibles ; la recherche explicite
    reste indépendante des techniques humaines déterministes.
16. ~~Compiler les prémisses, utiliser un cadre mutable interne, propager les
    deltas de suppression, maintenir les compteurs négatifs et conserver les
    jointures partielles sous budget. Ajouter un index de dépendances positives
    et un agenda incrémental. Ajouter des index de chemins adaptatifs, des
    retraits à rangs stables, des témoins résiduels et un ordre existentiel
    sélectif.~~ Mesurer les prochaines optimisations sur les conflits réellement
    dominants.
17. ~~Structurer un catalogue public de bases avec un exécuteur commun,
    des oracles et des README par problème.~~ Les exemples de la thèse ont
    motivé la divisibilité entière, le modulo, `FRESH`, `COLLECT` et les
    continuations isolées. ~~Ajouter ensuite une stratégie de conflit MEA et
    reformuler le singe et les bananes avec des sous-buts dynamiques. Ajouter
    `FOCUS`, les séquences, fenêtres, combinaisons et `FOR EACH`.~~
18. ~~Ajouter groupes paramétrés, récursion bornée, prédicats calculés sur
    registre, hiérarchie explicable, recherche par hypothèses, interface
    CSP/SAT et TMS positif optionnel.~~ Évaluer ces primitives sur les
    prochaines bases concrètes avant d'élargir leur DSL.
19. ~~Ajouter `ChoicePoint`, MRV, choix pondérés, branches isolées,
    backtracking et traces ; valider ce langage sur un solveur CSP des quatre
    reines et un premier harmoniseur SATB. Raccorder ensuite le pilote DFS au
    trail réversible.~~ Étendre progressivement le profil `ROY_1998`.

La cible est Python 3.12 ou ultérieur, avec `pytest`, `ruff`, `mypy` et des
tests différentiels. L’ajout de tests génératifs fondés sur Hypothesis reste
prévu.
Les solveurs externes, dont OR-Tools, resteront des dépendances optionnelles
derrière une interface générique afin de préserver un cœur symbolique léger et
de permettre l’utilisation future d’autres backends.
