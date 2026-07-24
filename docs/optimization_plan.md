# Plan d’optimisation de Snarky

## Objectif

Snarky conserve un moteur naïf, déterministe et volontairement simple comme
définition exécutable de la sémantique et oracle de correction. Le moteur
utilise cependant la stratégie semi-naïve par défaut afin d'offrir des
performances adaptées aux bases réelles. Toutes les stratégies doivent produire
exactement les mêmes faits et les mêmes preuves minimales.

Les optimisations doivent préserver les propriétés suivantes :

- termes récursifs immuables et hachables ;
- variables autorisées dans les trois positions d’un triplet ;
- propositions utilisées comme termes ;
- distinction entre `VRAI`, `FAUX`, `INEXISTANT` et l’absence ;
- résultats déterministes par défaut ;
- réfraction des activations ;
- provenance vérifiable ;
- point fixe identique à celui du moteur naïf.

## État au 24 juillet 2026

| Phase | État | Résultat ou prochaine étape |
|---|---|---|
| 0 — Mesures | Terminée pour le socle | Benchmarks Fibonacci et Sudoku p1–p6, acceptation Sudoku p1–p7, durées pytest et compteurs d'instanciation disponibles |
| 1 — Activations paresseuses | Différée | MEA exige le conflit complet ; ne pas complexifier les autres chemins sans profil dominant |
| 2 — Indexation | Terminée | Index exact partagé, index composés sur deux positions, ajouts incrémentaux et retraits en lot |
| 3 — Deltas | Terminée | Deltas nets par règle pour ajouts, suppressions et réinsertions |
| 4 — Plans et jointures | Terminée pour le socle | Prémisses compilées, MRV delta et mémoires partielles bornées avec repli |
| 5 — Substitutions et négation | Terminée | Cadre mutable, hashes précalculés, watchers indexés, compteurs simples et requêtes corrélées persistantes |
| 6 — Sélection des règles | Terminée | Plans négatifs, index positif conservatif, focus MEA et agenda incrémental mesurable |
| 7 — Agrégats | Terminée pour `COUNT`/`UNIQUE` ; socle `COLLECT` livré | DSL, API Python, oracle naïf et réfraction ; projection `COLLECT` encore recalculée |
| 8 à 10 | Partielles | Backend CSP/SAT fini livré ; provenance configurable, stratégie centrée variables et backend externe restent à faire |

L'extension fonctionnelle `LET` est terminée : Fibonacci utilise désormais
l'arithmétique native du moteur et ne dépend plus de tables de sommes et de
prédécesseurs.

La stratégie semi-naïve est le comportement par défaut. La stratégie naïve
reste disponible explicitement avec `strategy=NaiveInstantiationStrategy()` et
sert d'oracle de correction. Les tests différentiels vérifient l'égalité des
faits, des dérivations, des cycles et des activations.

Trois passes de profilage Sudoku ont conduit aux optimisations générales
suivantes :

- table de recherche O(1) dans les substitutions immuables, tout en conservant
  leur tuple ordonné pour le rendu déterministe ;
- extension groupée des substitutions et matcher ground utilisant un cadre
  mutable temporaire par fait candidat ;
- résolution paresseuse des seules positions variables lors du choix d’un
  bucket ;
- index composés `(sujet, relation)`, `(relation, objet)` et `(sujet, objet)` ;
- mémoire de témoins `EXISTS`/`NOT EXISTS` maintenue sélectivement entre les
  snapshots ;
- réfraction négative filtrée par les prémisses susceptibles de matcher un
  fait ajouté, avec expiration directe des bloqueurs simples corrélés ;
- plans de réfraction compilés au premier enregistrement du groupe et
  réconciliation entièrement omise lorsqu’aucun plan n’est nécessaire ;
- cache des variables visibles dans les blocs existentiels.
- compilation immuable des patterns, résolveurs de positions et blocs de
  prémisses ;
- `BindingFrame` mutable avec trail et rollback pendant toute une jointure,
  figé uniquement pour une activation observable ;
- `FactDelta` net et révisionné, incluant ajouts, suppressions et
  réinsertions ;
- watchers de requêtes indexés par signature résolue, au lieu d’un balayage
  global à chaque mutation ;
- compteurs exacts incrémentaux pour les requêtes factuelles simples ;
- mémoires de préfixes de jointure, activées uniquement sous un budget
  cardinal et abandonnées au profit du chemin exhaustif lorsqu’elles seraient
  trop grandes ;
- prémisses corrélées `COUNT` et `UNIQUE`, utilisées dans la base Sudoku.
- catalogue de provenance Spinoza validé une seule fois par version de
  fichier, au lieu d’un parsing YAML pour chacun des 199 cas.
- hashes structurels de `Atom`, `Number`, `Variable`, `Triple` et `Fact`
  calculés une fois puis conservés dans un slot privé.

Sur la machine de développement, les médianes Sudoku après la seconde passe
sont :

| Mesure | Baseline initiale | Passe précédente | État actuel |
|---|---:|---:|---:|
| résolution p1 | 2,32 s | 0,325 s | 0,247 s |
| résolution p5 | 5,95 s | 0,728 s | 0,535 s |
| résolution p6 | 5,58 s | 0,639 s | 0,468 s |
| suite pytest complète | 76,50 s | 8,38 s | environ 6,8 s |
| suite sans `slow` | — | 2,36 s | 2,39 s |

Sur la dernière séquence seule, les tentatives de matching passent de 69 793
à 47 051 sur p1, de 217 880 à 125 298 sur p5 et de 210 908 à 106 449 sur p6.
La baisse supplémentaire vaut 33 à 50 %, pour un gain temporel de ×1,62 à
×2,29. Depuis la baseline initiale, le gain total vaut ×7,18 à ×8,74. À cette
étape de mesure, la suite comptait 285 tests. Elle en compte maintenant 314 et
s’exécute en environ 7,9 s après l’ajout des nouvelles capacités et bases ; ce
temps élargi ne remplace pas la mesure contrôlée du tableau. Le protocole
exécutable est `python -m benchmarks.sudoku_rules`.

La passe de hachage précalculé ne change aucun compteur logique. Elle réduit
encore les médianes Sudoku de 24 à 27 % et porte le gain total depuis la
baseline initiale à ×9,38–×11,94. Sur le snapshot exact précédant cette passe,
`F(15)` semi-naïf prenait 6,084 s ; il prend désormais 0,953 s, soit ×6,39.
La suite complète passe d’une mesure contrôlée de 8,38 s à environ 6,8 s,
soit près de 19 %. Le surcoût retenu après p5 est d’environ 46,6 Ko, à raison
de huit octets par objet concerné encore vivant.

Le plan de dépendances de réfraction est désormais compilé lors du premier
enregistrement de chaque groupe. S’il ne contient aucune règle négative ou
agrégée, les ajouts évitent entièrement la réconciliation :

| Rang | Avant | État courant | Gain | Passages | Matchings |
|---:|---:|---:|---:|---:|---:|
| 15 | 0,919 s | 0,338 s | ×2,72 | 5 | 9 125 |
| 16 | 2,238 s | 0,614 s | ×3,64 | 5 | 14 792 |
| 17 | 6,248 s | 1,206 s | ×5,18 | 5 | 23 928 |
| 18 | 18,896 s | 2,330 s | ×8,11 | 5 | 38 747 |
| 19 | 53,603 s | 4,618 s | ×11,61 | 5 | 62 686 |
| 20 | — | 8,791 s | — | 3 | 101 462 |
| 21 | — | 12,309 s | — | 1 | 164 159 |

Le profil instrumenté de `F(17)` passe de 17,2 s à 4,0 s et
`_reconcile_negative_refraction`, auparavant responsable de 12,923 s,
disparaît entièrement. Les compteurs logiques restent identiques. `F(20)` est
maintenant sous 10 secondes et `F(21)` sous 30 secondes ; `F(22)` dépasserait
la garde par défaut de 100 000 faits.

Ces mesures sont des baselines locales, pas des garanties multi-machines.
Les caches ne réutilisent que des résultats déterministes tant que la mémoire
de travail reste inchangée.

La baisse de la suite complète de 26,05 s à 7,69 s ne vient pas du moteur de
matching : le chargeur Spinoza reparsait auparavant le même catalogue YAML de
58 Ko pour chaque cas. Le catalogue validé est désormais partagé sous forme
immuable et sa clé inclut la date de modification nanoseconde et la taille du
fichier. Une modification sur disque déclenche donc automatiquement un nouveau
parsing.

La stratégie `SemiNaiveInstantiationStrategy` combine les index persistants,
un delta propre à chaque règle et une planification locale des jointures. Dans
la série historique du 22 juillet 2026, elle abaissait le temps de `F(17)` de
27,914 s à 3,338 s et ne produisait que les 4 789 activations effectivement
déclenchées, au lieu de 95 013. Ces chiffres retracent cette étape de
développement ; la comparaison A/B courante du cache de hash est celle de
`F(15)` donnée plus haut.

## Situation initiale

Avant l'indexation, le moteur effectuait une jointure exhaustive par
backtracking. Pour chaque prémisse factuelle, il parcourait la totalité de la
base. À chaque cycle, il recalculait également les instanciations anciennes
avant de les éliminer par réfraction.

Les principaux coûts identifiés sont :

1. absence d’index sur les statuts et les positions des triplets ;
2. copie de la base dans un tuple pour chaque règle et chaque cycle ;
3. matérialisation de toutes les activations avant leur exécution ;
4. recalcul des jointures ne contenant aucun fait nouveau ;
5. ordre des prémisses fixé par leur ordre textuel ;
6. recherche linéaire dans les substitutions immuables ;
7. évaluation de toutes les règles après chaque changement ;
8. conservation potentiellement coûteuse de toutes les dérivations.

Une mesure exploratoire de la fermeture transitive d’une chaîne a donné les
résultats suivants sur la machine de développement :

| Nœuds | Faits au point fixe | Activations | Cycles | Temps |
|---:|---:|---:|---:|---:|
| 10 | 46 | 120 | 5 | 0,022 s |
| 20 | 191 | 1 140 | 6 | 0,373 s |
| 30 | 436 | 4 060 | 6 | 1,331 s |
| 40 | 781 | 9 880 | 7 | 5,435 s |

Ces chiffres sont indicatifs et ne remplacent pas un benchmark reproductible.
Ils montrent néanmoins que l’implémentation de référence ne convient pas
encore aux grandes bases récursives.

Les trois paragraphes suivants décrivent les séries historiques du 22 juillet
2026, et non les performances du snapshot courant.

Le benchmark reproductible `benchmarks/fibonacci_explicit.py` couvre désormais
le scénario Fibonacci explicite. Pour `F(10)`, trois passages sur la machine de
développement donnaient 7,243 s avec la stratégie naïve contre 0,245 s avec la
première stratégie indexée. Les deux produisaient les mêmes 326 faits et les
mêmes dérivations. Les tentatives de matching passaient de 557 302 à 8 963.

La baseline indexée initiale couvre les rangs 10 à 17. Le temps croît de
0,245 s à 27,914 s, le point fixe de 326 à 9 578 faits et les activations
produites de 1 782 à 95 013. `F(15)` reste sous 10 secondes et `F(17)` sous 30
secondes. Le tableau complet et sa version CSV se trouvent dans
`benchmarks/README.md` et `benchmarks/results/`.

La baseline semi-naïve couvre les rangs 10 à 21. `F(18)` reste sous 10 secondes
et `F(20)` sous 30 secondes ; `F(21)` prend 32,042 s. Sur `F(17)`, les tentatives
de matching passent de 479 862 à 41 789 et les constructions d'index de 93 à
3. Le gain temporel mesuré est ×8,4 par rapport à la première stratégie
indexée.

## Principe d’architecture

Les stratégies partagent actuellement cette interface commune :

```python
class InstantiationStrategy(Protocol):
    metrics: InstantiationMetrics

    def instantiate(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
        delta: tuple[Fact, ...] | None = None,
    ) -> tuple[Activation, ...]: ...
```

Les phases 2 et 3 ont enrichi cette interface avec un delta optionnel, sans
modifier les modèles publics de règles et de faits. La phase 1 devra encore
remplacer le tuple d'activations par un itérateur ou une vue bornée.

Le moteur naïf reste disponible sous le nom `NaiveInstantiationStrategy`.
Chaque nouvelle stratégie est testée
différentiellement contre lui sur de petites bases.

Les optimisations devront être séparées en composants observables :

```text
IndexedFactStore
PatternSignature
IndexPlan
JoinPlan
RuleCandidateIndex
SemiNaiveInstantiationStrategy
VariableCenteredStrategy
ConstraintNetwork
```

## Phase 0 — Mesures reproductibles

**État : partielle.** Le répertoire `benchmarks/`, la sortie JSON, les mesures
de temps, cycles, faits, activations et tentatives de matching sont disponibles
pour Fibonacci explicite. Restent notamment le pic mémoire, le détail du temps
de parsing et les autres formes de jointure.

Pour mesurer les progrès, chaque phase devra rejouer au minimum la plage
`F(10)` à `F(20)`, prolongée autant que le temps raisonnable le permet,
rapporter les ratios par rapport au CSV de référence et indiquer les plus
grands rangs passant sous 10 et 30 secondes. L'égalité différentielle avec
l'oracle naïf reste obligatoire sur les rangs où son coût est acceptable.

Avant de modifier les algorithmes :

1. créer un répertoire `benchmarks/` ;
2. ajouter un générateur de fermetures transitives paramétré par `n` ;
3. mesurer séparément parsing, instanciation, exécution et provenance ;
4. compter les faits examinés, matchings tentés, substitutions créées,
   activations produites et activations réfractées ;
5. mesurer le temps, le pic mémoire et le nombre de cycles ;
6. enregistrer les résultats en JSON pour permettre les comparaisons ;
7. fournir une commande unique de reproduction.

Premiers scénarios :

- `mini_snarky`, pour la non-régression fonctionnelle ;
- fermeture transitive d’une chaîne et d’un graphe dense ;
- jointure en étoile avec une variable centrale ;
- règle d’ordre 2 avec relation variable ;
- propositions profondément imbriquées ;
- Fibonacci explicite, désormais couvert par une création structurelle des
  sous-problèmes et les actions arithmétiques natives `LET` ;
- sélections adaptées des corpus externes.

## Phase 1 — Activations paresseuses

**État : à faire.** La première optimisation mesurée a directement ciblé
l'indexation, principal coût révélé par Fibonacci. Le streaming reste utile
pour réduire la mémoire consommée par la stratégie semi-naïve et borner la
matérialisation des activations.

Transformer la stratégie naïve pour produire un itérateur d’activations au
lieu d’un tuple complet.

Résultats attendus :

- réduction du pic mémoire ;
- possibilité d’arrêter une recherche après la première activation ;
- suppression d’une copie intermédiaire ;
- aucun changement sémantique.

Cette phase doit rester petite afin de constituer une première mesure fiable de
l’effet du streaming.

## Phase 2 — Stockage indexé

**État : terminée pour les index top-level et structurels adaptatifs prévus.**

Implémenter `IndexedFactStore` en conservant le stockage naïf pour référence.

Index initiaux :

- statut ;
- type du terme racine ;
- constante en position sujet ;
- constante en position relation ;
- constante en position objet ;
- combinaisons fréquentes, par exemple relation et statut.

Le compilateur de règles produira une `PatternSignature` pour chaque prémisse.
Le stockage retournera le plus petit ensemble candidat connu, puis le matcher
structurel vérifiera les candidats.

`IndexedInstantiationStrategy` maintient désormais un index persistant partagé
sur l’entité, le statut, le sujet, la relation et l’objet, ainsi que sur les
trois paires de positions top-level. Les suffixes de faits nouveaux l’étendent
une seule fois, même lorsque plusieurs règles les voient. Les retraits sont
accumulés puis appliqués en lot avant le prochain matching. Le plus petit
bucket compatible avec la substitution courante est proposé au matcher.
L’ordre textuel des prémisses et l’ordre d’insertion des candidats sont
préservés.

Les mesures de propagation binaire ont depuis justifié des index plus
profonds. `FactIndex` aplatit à la demande les chemins résolus d'une
`FiniteSequence` imbriquée et construit une signature composée uniquement
lorsque le meilleur bucket top-level dépasse huit faits. Deux signatures
suffisent à la relation `SEQ[left right]`; les ajouts et retraits les
maintiennent ensuite incrémentalement.

Les rangs d'insertion sont stables après les retraits. Une mémoire initiale
d'au moins 1 500 faits emploie un ensemble ordonné pour sa séquence active ;
les mémoires plus petites conservent une liste. Cette décision adaptative
évite de faire payer aux petites bases le coût d'une structure optimisée pour
des milliers de suppressions.

Critère de validation : le nombre de faits proposés au matcher doit diminuer
sans modifier les activations produites.

Ce critère est satisfait sur Fibonacci `F(10)` : l'index exhaustif persistant
conserve 8 963 candidats, mais les constructions d'index passent de 51 à 3 et
le temps de 0,245 s à 0,167 s.

## Phase 3 — Évaluation semi-naïve et deltas mutables

**État : terminée pour le socle actuel.** Le benchmark `F(10)` produit
exactement 163 activations pour 163 déclenchements, contre 1 782 activations
avant cette phase.

Le point fixe doit distinguer :

- `known`, tous les faits connus ;
- `delta`, les faits ajoutés lors du cycle précédent ;
- `next_delta`, les nouveaux faits du cycle courant.

Pour une règle comportant plusieurs prémisses, seules les jointures contenant
au moins un fait de `delta` doivent être recalculées. Les combinaisons composées
uniquement de faits anciens ont déjà été examinées.

Cette phase est prioritaire pour les règles récursives. Elle doit réduire
fortement le travail effectué avant la réfraction et rendre le coût plus proche
du nombre réel de nouvelles conséquences.

Points à tester particulièrement :

- plusieurs prémisses pouvant recevoir le fait nouveau ;
- absence de doublons entre les variantes semi-naïves d’une règle ;
- plusieurs règles récursives mutuellement dépendantes ;
- profondeur et provenance identiques au moteur naïf.

Ces cas sont couverts par les tests différentiels, y compris les deltas pouvant
satisfaire plusieurs prémisses, la récursivité mutuelle et les comparaisons
utilisées comme barrières textuelles.

Pour une session mutable, le moteur transmet maintenant un `FactDelta` propre
à chaque règle. Il réduit le journal depuis la précédente évaluation en deux
ensembles nets, `added` et `removed`, accompagnés d’une révision globale. Une
suppression suivie d’une réinsertion est représentée dans les deux ensembles
afin de préserver l’ordre d’insertion. Les index, compteurs et mémoires
partielles consomment ce même delta.

## Phase 4 — Planification des jointures

**État : socle compilé et ordre existentiel adaptatif terminés.** Chaque règle possède un `CompiledRule`
réutilisable contenant ses patterns, résolveurs d’index et blocs corrélés.
Une variante semi-naïve commence par sa prémisse delta, puis choisit dans le
bloc courant la prémisse ayant le moins de candidats. Une comparaison ferme le
bloc et empêche tout réordonnancement qui modifierait la sémantique textuelle.

Pour les règles positives suffisamment sélectives, la stratégie conserve les
préfixes de jointure et les met à jour avec les deux composantes de
`FactDelta`. Une estimation conservative et une limite configurable de 2 048
états empêchent toute explosion mémoire ; au-delà, le moteur reprend
automatiquement la jointure compilée exhaustive.

Ne plus imposer systématiquement l’ordre textuel des prémisses.

Le compilateur construira un `JoinPlan` à partir de :

- la cardinalité estimée des ensembles candidats ;
- les variables déjà liées ;
- le nombre de constantes dans le pattern ;
- la profondeur des structures imbriquées ;
- la sélectivité observée des index ;
- la sûreté des comparaisons et prémisses négatives.

Heuristique initiale : choisir la prémisse exécutable ayant le moins de
candidats, puis favoriser celle qui partage le plus de variables déjà liées.

Le plan choisi doit être inspectable afin d’expliquer une mauvaise performance
et de comparer plusieurs heuristiques.

Les blocs existentiels composés uniquement de faits utilisent maintenant le
plus petit bucket lorsqu'au moins un pattern structuré partiellement lié est
indexable et que la mémoire dépasse 128 faits. La généralisation immédiate à
tous les blocs a été rejetée par mesure : sur les longues conjonctions, les
estimations répétées coûtaient davantage que les matchings évités. L'ordre
adaptatif reste donc gardé et les supports sont remis dans l'ordre textuel.

## Phase 5 — Substitutions et matching

**État : terminée pour le socle actuel.** Les substitutions publiques
conservent une table O(1) et leur ordre immuable. L’instanciation compilée
utilise cependant un `BindingFrame` mutable unique, muni d’un trail : chaque
branche pose un checkpoint puis annule uniquement ses nouvelles liaisons. Le
cadre n’est figé en `Substitution` qu’à la production d’une activation ou d’un
état partiel mémorisé.

Les recherches existentielles traversent les snapshots. Des watchers indexés
par entité, combinaison de positions ou signature de chemin ne réévaluent que
les corrélations compatibles avec le fait muté. Les blocs composés d’une seule
prémisse factuelle maintiennent directement leur cardinalité et leur premier
témoin. Les blocs factuels structurés conservent au plus deux témoins
résiduels : la disparition du premier promeut le second sans rematching. Les
autres blocs complexes conservent un chemin de recalcul compilé sûr.

Sur 64 retraits de supports dans un domaine clairsemé de 1 024 valeurs, ce
cache borné réduit les invalidations de 64 à 32, les matchings de 2 275 à
1 253 et le temps de 60,578 à 56,991 ms.

Les termes et faits immuables conservent leur hash structurel dans un slot
privé. La formule reste exactement celle des dataclasses antérieures, et le
cache est reconstruit par le constructeur après désérialisation. Il n’apparaît
ni dans l’égalité, ni dans le `repr`, ni dans les champs publics de dataclass.

Optimiser seulement après profilage les opérations de bas niveau :

- accès moyen en temps constant aux variables liées ;
- application structurelle évitant de reconstruire un triplet inchangé ;
- représentation compacte des variables compilées par identifiant entier ;
- partage structurel des substitutions parentes ;
- cache prudent des signatures de termes.

Le modèle public `Variable` doit rester lisible. Une représentation compilée
interne pourra être introduite sans modifier l’API.

## Phase 6 — Sélection des règles candidates

**État : terminée.** Les ajouts sont
filtrés par les signatures des prémisses négatives. Lorsqu’un `NOT EXISTS`
top-level ne contient qu’une prémisse factuelle, le nouveau fait est testé
directement contre chaque substitution déclenchée et seules les clés réellement
bloquées sont expirées. Les négations composées utilisent encore l’oracle
indexé exhaustif.

`_RuleDependencyIndex` relie une signature factuelle discriminante à chaque
règle et conserve un repli wildcard pour les patterns généraux. L'agenda garde
les activations par règle ; après mutation, seules les lignes candidates
reçoivent le delta. `AgendaMetrics` expose le travail effectué.

Sur 200 règles indépendantes, l'ajout ciblé recalcule 1 règle et en réutilise
199. La médiane passe de 2,206 ms pour une construction froide à 0,572 ms pour
la mise à jour, soit ×3,86. Voir
[`../benchmarks/results/agenda_incremental_2026-07-24.csv`](../benchmarks/results/agenda_incremental_2026-07-24.csv).

Les activations restent matérialisées parce que MEA doit comparer le conflit
complet. Une API réellement paresseuse ne sera introduite que si un profil
montre un gain hors des chemins exigeant un tri ou un choix global.

## Phase 7 — Agrégats corrélés

**État : terminée pour `COUNT` et `UNIQUE`, première version correcte de
`COLLECT`.** Les trois prémisses partagent la portée locale de `EXISTS` :

```text
COUNT == 2
    ($cell candidate $value)
END_COUNT

UNIQUE
    ($cell selected $value)
END_UNIQUE

COLLECT $values := $value
    ($cell candidate $value)
END_COLLECT
```

`COUNT` accepte les six comparateurs numériques contre un entier positif ou
nul. `UNIQUE` est la forme exacte-un. Les variables locales ne s’échappent
pas. L’oracle naïf énumère toutes les solutions locales ; la stratégie indexée
réutilise les compteurs et supports mémorisés. Ajouts et retraits mettent à
jour la réfraction comme pour les négations corrélées.

`COLLECT` projette les valeurs distinctes dans un `FiniteSet` et conserve tous
les supports de provenance. Les trois stratégies produisent les mêmes
résultats. Sa première implémentation réénumère toutefois la projection après
une invalidation ; une maintenance incrémentale par valeur projetée ne sera
justifiée que par un profil montrant ce coût sur une base réelle.

## Phase 8 — Provenance configurable

Proposer plusieurs politiques :

- `MinimalProofOnly` : conserver uniquement la meilleure preuve connue ;
- `AllProofs(limit=n)` : conserver plusieurs preuves avec une limite ;
- `CountOnly` : compter les dérivations sans les matérialiser ;
- `NoProvenance` : mode benchmark explicitement demandé.

La provenance complète restera le comportement de référence. Les politiques
réduites devront être choisies explicitement et ne devront jamais produire une
preuve incorrecte.

## Phase 9 — Instanciation centrée sur les variables

**État : premier palier hybride livré.**

L’approche historique de BOOJUM est découpée afin de ne pas introduire
simultanément propagation, énumération et retour arrière :

1. ~~construire un domaine candidat pour chaque variable ;~~
2. ~~projeter les faits candidats sur les positions correspondantes ;~~
3. ~~propager sûrement les réductions des règles positives ;~~
4. ~~passer les tables filtrées au matcher compilé existant ;~~
5. ~~choisir automatiquement entre filtrage et repli semi-naïf selon le coût
   estimé ;~~
6. ~~réviser seulement les propagateurs voisins par une file d'incidence ;~~
7. ~~compiler les comparaisons et égalités arithmétiques en propagateurs
   spécialisés ;~~
8. ~~maintenir par compteurs les projections `(variable, valeur)` et
   réinitialiser seulement les composantes élargies ;~~
9. ~~ouvrir une interface `DomainPropagator` et ajouter `NVALUE` ainsi que
   `ALL_DIFFERENT` avec ensembles de Hall bornés ;~~
10. ~~conserver des supports par ligne et valeur sous forme de Compact-Tables
    bitset et les réutiliser dans la jointure ;~~
11. ~~propager `FactDelta` jusqu'à la jointure Compact semi-naïve ;~~
12. ~~séparer les définitions de tables de l'état mutable et fournir un trail
    réversible avec contradictions observables ;~~
13. ~~ajouter une sonde de coût observé, différée pour rester amortissable ;~~
14. choisir la variable la plus contrainte ;
15. backtracker localement uniquement lorsque la propagation ne suffit pas.

`ConstraintInstantiationStrategy` conserve aujourd'hui ses tables par règle,
les met à jour depuis `FactDelta` et maintient les domaines de base par
compteurs. Une suppression poursuit la réduction depuis le point fixe
précédent ; un ajout réinitialise uniquement la composante connexe touchée
afin de restaurer les valeurs redevenues possibles. Un delta sans ligne
pertinente réutilise directement le résultat filtré. Les prémisses non prises
en charge retombent sur `SemiNaiveInstantiationStrategy`. Aucun contexte
d'inférence n'est copié.
`AdaptiveInstantiationStrategy` sélectionne les graphes cycliques de volume
et de sélectivité suffisants, ainsi que les comparaisons dotées d'un
propagateur rapide, puis mémorise la décision par règle.

La matrice de benchmarks donne :

| Scénario | Indexée | Filtrage | Adaptative | Décision |
|---|---:|---:|---:|---|
| dense sélectif, taille 40 | 189,52 ms | 17,23 ms | 17,23 ms | filtrer |
| neutre, taille 200 | 2,987 ms | 5,035 ms | 2,826 ms | repli |
| dense sans réduction, taille 20 | 52,03 ms | 58,24 ms | 52,17 ms | repli |
| chaîne, taille 40 | 6,741 ms | 8,706 ms | 6,413 ms | repli |

Sur la chaîne, la file réduit les révisions de 1 722 à 122 et les lignes
examinées de 67 242 à 4 802 par rapport aux balayages complets. Ces compteurs
indiquent que les prochains gains éventuels devront viser le coût interne
d'une révision de table. Le profil Sudoku p6 précise cependant que la file
ne relit que 1 139 lignes au-delà des 20 562 lectures initiales obligatoires,
soit 5,5 %. Un mécanisme AC-4/AC-6 n'est donc pas prioritaire à ce stade.

Les comparaisons simples utilisent maintenant des propagateurs en O(n) :
intersection pour `==`, singleton pour `!=`, bornes pour les ordres et
supports pour `DIVISIBLE`. `CONSTRAINT $x + $y == $z` étend les opérandes de
comparaison à l'AST arithmétique de `LET`. Sur deux domaines de 200 valeurs et
une somme fixée à 2, la médiane passe de 346,36 ms pour la jointure indexée et
82,42 ms pour le filtre cartésien à 2,05 ms en adaptatif. Les matchings
finaux passent de 160 400 à 6 ; la persistance évite la seconde propagation
identique. Le gain total est ×169.

Sur Sudoku, les compteurs ramènent les projections relues de 15 920 à 998
pour p1, de 21 595 à 1 033 pour p6 et de 24 533 à 1 005 pour p7, soit une
réduction de 93,7 à 95,9 %. Le gain temporel reste de 1 à 2 % : la projection
des domaines n'est donc plus le goulot dominant et une représentation bitset
spécifique n'est pas prioritaire.

Le palier suivant vise un autre coût : les révisions de tables et le second
matching structurel. Chaque ligne possède désormais un slot stable, chaque
couple `(variable, valeur)` un masque de supports, et chaque table un masque
de lignes actives. Les suppressions sont propagées comme événements de valeur
par opérations bitset. La jointure
intersecte ces mêmes masques avec les liaisons courantes puis injecte
directement les liaisons déjà validées dans le `BindingFrame`.

Sur sept répétitions, le remplacement complet du scan et du second matching
donne :

| Scénario | Tables scannées | Compact-Table | Gain |
|---|---:|---:|---:|
| Sudoku p1 | 0,377 s | 0,287 s | ×1,31 |
| Sudoku p6 | 0,656 s | 0,576 s | ×1,14 |
| Sudoku p7 | 0,926 s | 0,804 s | ×1,15 |
| arithmétique, taille 200 | 2,292 ms | 2,010 ms | ×1,14 |
| quatre reines | 117,44 ms | 104,06 ms | ×1,13 |

Les 15 467 à 21 588 examens de lignes des trois Sudoku tombent à zéro. Le
filtrage bitset seul apporte 2 à 5 % ; le reste du gain vient principalement
de la réutilisation des lignes actives par la jointure. C'est cette seconde
partie qui rend l'optimisation substantielle.

Le delta est maintenant conservé jusqu'à cette jointure. Par rapport à la
colonne Compact-Table ci-dessus, les médianes passent à 0,254 s, 0,534 s et
0,731 s sur Sudoku p1, p6 et p7. Les matchings baissent respectivement de
63 946 à 49 531, de 138 846 à 126 198 et de 216 643 à 195 160. Un cycle sans
ligne pertinente ne lance plus la jointure.

Les lignes et masques de support partagés sont distincts des domaines et
masques actifs mutables. `DomainStore` produit des réductions motivées et une
contradiction structurée ; `PropagationState` journalise les modifications.
Sur 1 000 domaines dont trois sont modifiés par branche, 200
checkpoints/rollbacks prennent 1,103 ms contre 30,706 ms avec une copie
complète, soit ×27,84.

Une première sonde de coût contre-factuelle a montré pourquoi elle doit être
amortie : lancée immédiatement, elle faisait passer le scénario favorable de
14 à 192 ms et quatre reines de 104 à 144 ms. La version retenue accepte
directement une forte réduction et diffère la sonde des cas ambigus jusqu'à
huit usages. Le scénario favorable revient à 14,23 ms ; quatre reines ne
sonde pas pendant ses cinq usages ambigus et reste à 106,8 ms.

`DomainPropagator` constitue maintenant l'extension publique commune.
`NVALUE` filtre des bornes sûres et traite exactement les cas serrés `N = 1`
et `N = nombre de variables`. `ALL_DIFFERENT` propage les singletons et les
ensembles de Hall de taille au plus trois. Sur le scénario `NVALUE` à deux
domaines de 200 valeurs, l'adaptatif passe de 414,61 à 2,13 ms, soit ×194,7.
Le benchmark `ALL_DIFFERENT` passe de 67,36 à 44,88 ms, soit ×1,50.

La stratégie complète pourra être représentée explicitement par :

```text
VariableDomain
PartialInstantiation
ConstraintNetwork
InstantiationState
ChoiceHeuristic
```

Le choix MRV, le pilote de backtracking, le solveur CSP pédagogique et le
premier harmoniseur à quatre voix sont maintenant livrés. Le DFS matérialise
les alternatives à la demande et restaure ses branches sœurs par un trail
complet d'`InferenceSession`. BFS et best-first conservent des forks pour leurs
frontières multiples, avec un clone spécialisé de la provenance. Le cap
complet est décrit dans
[`choice_backtracking_and_applications.md`](choice_backtracking_and_applications.md).

La première version possède déjà des tests différentiels ciblés, y compris
variables en position relation et deltas d'ajout/suppression. Trente petits
programmes positifs générés, avec et sans différence, sont aussi comparés au
matcher naïf avant chaque validation.

## Phase 10 — Raisonnement par contraintes

Le couplage avec OR-Tools ou d’autres solveurs interviendra après stabilisation
du moteur symbolique indexé.

Une interface de backend devra permettre :

1. de traduire certaines prémisses en contraintes ;
2. de transmettre les domaines et relations au solveur ;
3. de récupérer zéro, une ou plusieurs solutions ;
4. de convertir ces solutions en substitutions Snarky ;
5. de réinjecter conclusions et contradictions avec leur provenance.

Le solveur externe restera optionnel. Le cœur de Snarky ne devra pas dépendre
directement d’OR-Tools.

## Validation différentielle

Pour chaque stratégie optimisée et chaque petite base générée :

```text
faits_naifs == faits_optimises
activations_naives == activations_optimisees
profondeurs_naives == profondeurs_optimisees
```

Les tests utiliseront des exemples déterministes et, ensuite, Hypothesis pour
générer de petits programmes comportant :

- constantes et variables dans toutes les positions ;
- variables répétées ;
- statuts multiples ;
- comparaisons ;
- triplets imbriqués ;
- règles récursives ;
- plusieurs preuves d’un même fait.

## Critères de passage entre phases

Une phase est acceptée lorsque :

1. tous les tests existants passent ;
2. les tests différentiels ne montrent aucune divergence ;
3. `ruff` et `mypy` passent ;
4. le benchmark est reproductible ;
5. le gain ou la réduction mémoire est mesuré ;
6. aucune optimisation n’est activée silencieusement si elle modifie la
   provenance ou l’ordre observable ;
7. une option permet de revenir au moteur naïf.

## Ordre de réalisation recommandé

L’ordre offrant le meilleur rapport gain/risque est :

1. instrumentation et benchmarks ;
2. activations paresseuses ;
3. stockage indexé ;
4. évaluation semi-naïve ;
5. planification des jointures ;
6. sélection des règles candidates ;
7. optimisation des substitutions guidée par profilage ;
8. provenance configurable ;
9. stratégie centrée sur les variables ;
10. intégration des solveurs de contraintes.

Le moteur naïf doit rester simple tout au long de ce travail. Sa lenteur est
acceptable : sa fonction principale est de fournir un résultat de référence
facile à comprendre et à vérifier.

## Prochaine tranche concrète

1. profiler `F(20)` et `F(21)` après suppression du coût de réfraction
   négative, pour départager substitutions, jointures, tri et provenance ;
2. profiler les activations hors agenda avant de décider d'une API paresseuse ;
3. partager éventuellement un index global entre les règles si le profilage
   montre que les trois index persistants restent significatifs ;
4. ~~ajouter une sélection générale des règles positives candidates
   réveillées par chaque delta ;~~
5. mesurer la mémoire des préfixes de jointure et ajuster leur budget par
   charge ;
6. étendre les benchmarks aux fermetures transitives et jointures en étoile ;
7. profiler `COLLECT` sur MusES et les prochains cas p8+, puis maintenir ses
   valeurs projetées incrémentalement seulement si ce coût devient mesurable.
8. ~~profiler et rendre incrémental le conflit MEA avec l’index positif des
   règles.~~ Étendre la mesure au singe et à de futures bases MEA plus larges.

Le critère de sortie sera un nouveau gain mesuré sur la baseline semi-naïve,
avec identité complète des faits, dérivations, cycles et profondeurs. Les
seuils actuels à dépasser sont `F(20)` sous 10 secondes et `F(21)` sous 30
secondes ; au-delà, la garde de faits doit être rendue explicite dans le
protocole.
