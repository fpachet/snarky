# Sémantique minimale du moteur de référence

Ce document décrit le premier noyau exécutable de Snarky. Il constitue une
décision de conception moderne (`MODERN_EXTENSION`) lorsque les sources
historiques ne permettent pas encore d’attribuer précisément un comportement à
BOOJUM.

## Termes et propositions

Un terme est un `Atom`, un `Number`, un `Variable`, un `Status` standard, un
`FiniteSet` ou un `Triple(subject, relation, object)`. Les trois composantes
d’un triplet et les membres d’un ensemble sont à leur tour des termes. Une
proposition est donc un triplet, éventuellement imbriqué dans un autre triplet.
Tous les termes sont immuables, hachables et comparés structurellement. Un
`FiniteSet` élimine les doublons et son égalité ne dépend pas de l’ordre
d’insertion ; cet ordre est néanmoins conservé pour un rendu déterministe.

Le hash structurel d’un terme ou d’un fait immuable est calculé une fois à sa
construction puis conservé dans un slot privé. Ce cache ne participe ni à
l’égalité, ni au rendu, ni aux champs publics de dataclass ; une
désérialisation le reconstruit à partir des composantes structurelles.

Les faits stockés sont ground : ils ne contiennent aucune variable. Un fait est
le couple `(entity, status)`. Le stockage de référence est multistatut : deux
faits ayant la même entité et des statuts différents peuvent coexister.
`VRAI`, `FAUX` et `INEXISTANT` sont des valeurs explicites ; l’absence d’un fait
n’est égale à aucune d’entre elles.

## Substitutions, matching et unification

Une substitution immuable associe des variables à des termes. Son application
est récursive : elle traverse les triplets et suit les chaînes de variables
jusqu’à leur valeur finale.

Le matching utilisé par le chaînage est orienté du pattern de règle vers un
fait ground. Une variable non liée accepte le terme correspondant ; une
variable déjà liée exige l’égalité structurelle. Le matching traverse les trois
positions des triplets, y compris la relation, ainsi que leur statut.

Le composant d’unification bidirectionnelle est séparé. Il unifie deux termes,
compose leurs substitutions et applique un occurs check afin d’interdire une
liaison cyclique telle que `x = (x r y)`. Le moteur de référence n’utilise pas
cette unification pour le chaînage avant.

## Prémisses et actions

Une prémisse triplet sans statut explicite recherche un fait de statut `VRAI`.
La forme `entity ' status` matche simultanément l’entité et le statut du fait ;
le statut peut être une variable. Les comparaisons sont évaluées après
substitution et nécessitent des opérandes ground.

Le moteur supporte `ADD`, `REMOVE`, la liaison arithmétique locale `LET`, la
création de symbole `FRESH` et l'itération d'actions `FOR EACH`.
Les actions sont instanciées avant mutation, puis appliquées dans leur ordre
textuel. `LET` évalue une expression numérique déterministe, enrichit la
substitution de l'activation et ne crée aucun fait. Les actions suivantes
voient immédiatement la nouvelle liaison. `FRESH` lie sa variable à un atome
nouveau de la forme `préfixe-N`, de manière déterministe dans une session et
sans collision avec les atomes déjà observés. `ADD` et `REMOVE` appliquent la
substitution courante à leur entité et à leur statut, puis refusent tout
résultat non ground. Retirer un fait absent est une non-opération.

Les expressions `LET` acceptent les nombres, les variables, les parenthèses et
les opérateurs `+`, `-`, `*`, `/` et `%` avec leur précédence usuelle. Leurs
opérandes doivent être numériques et déjà liés ; il ne s'agit pas encore de
résolution de contraintes. Une division par zéro ou un opérande invalide est
une erreur d'exécution explicite. Le modulo exige deux entiers et rejette
également un diviseur nul. La comparaison `DIVISIBLE x BY y` est le prédicat
entier correspondant. Voir
[`arithmetic_actions.md`](arithmetic_actions.md).

Les prémisses `EXISTS` et `NOT EXISTS` contiennent une conjonction locale
corrélée. Elles voient les variables déjà liées, mais leurs variables locales
ne s’échappent pas. Dans un bloc existentiel, les comparaisons doivent utiliser
des variables déjà liées. Au niveau principal, une comparaison prématurée
conserve le comportement historique : elle échoue à l’instanciation sans
chercher une liaison dans une prémisse ultérieure. L’absence testée par
`NOT EXISTS` reste distincte du statut `INEXISTANT`.

Une seule prémisse s'écrit directement, par exemple
`NOT EXISTS ($cell solved $value)`. Une conjonction utilise
`EXISTS ... END_EXISTS` ou `NOT EXISTS ... END_NOT_EXISTS`. L'ancien
`END_EXISTS` négatif reste un alias rétrocompatible.

`COUNT` et `UNIQUE` utilisent la même portée corrélée. `COUNT` compare le
nombre de substitutions locales satisfaisantes à un entier avec `==`, `!=`,
`<`, `<=`, `>` ou `>=`. `UNIQUE` exige exactement une solution locale. Les
faits participant aux solutions acceptées deviennent des supports de
provenance, mais aucune variable locale ne s’échappe :

```text
COUNT == 2
    ($cell candidate $value)
END_COUNT

UNIQUE
    ($item selected $choice)
END_UNIQUE
```

`COLLECT $ensemble := $projection` évalue de même une conjonction corrélée,
projette un terme ground pour chaque solution et lie `$ensemble` au
`FiniteSet` des valeurs distinctes. Seule cette variable cible s’échappe du
bloc. Une collection vide est `[]` :

```text
COLLECT $notes := $note
    ($chord contains $note)
END_COLLECT
```

`FiniteSequence` représente une collection ordonnée avec doublons sous la
forme `SEQ[...]`. `BIND` lie un terme structuré déjà ground, `WINDOW` développe
une chaîne de prémisses sur une relation et `COMBINATIONS` énumère les
sous-séquences de taille fixe. Contrairement à `COLLECT`, ces deux dernières
constructions peuvent produire plusieurs activations.

Les prémisses calculées n'appellent que des `ComputedPredicate` présents dans
un `PredicateRegistry`. `CHECK` exige un booléen ; `COMPUTE` exige un terme
ground et lie une cible locale. Aucun code textuel n'est évalué.

Une `InferenceSession` peut être copiée avec `fork()`. La copie possède sa
propre mémoire de travail, sa réfraction, sa provenance, ses compteurs et ses
générateurs `FRESH`. `HypothesisSearch` peut orchestrer explicitement plusieurs
copies, mais `fork()` seul ne formule ni hypothèse ni politique de choix.

Une session expose aussi `checkpoint()`, `rollback()` et `release()`.
`rollback()` restaure exactement l'état logique et observable du checkpoint
actif sans le fermer, ce qui permet de l'utiliser pour plusieurs frères.
`release()` ferme le checkpoint en ordre LIFO et conserve l'état courant. Les
faits, leur ordre, la provenance, la réfraction, les journaux, les tags
temporels et les générateurs `FRESH` font partie de l'état restauré.

`SessionChoiceSearch` ajoute cette politique sans modifier le chaînage avant.
Un `ChoicePoint` contient des alternatives qui affirment des faits dans des
branches explicites. En DFS, une copie racine isole l'appelant puis un
checkpoint restaure chaque branche sœur en place. BFS et best-first gardent
plusieurs descripteurs vivants, mais le fork et l'affirmation correspondants
sont différés jusqu'au retrait de la frontière. Après saturation des groupes,
un prédicat de contradiction rejette la branche et un prédicat de but accepte
une solution. MRV, poids, graine, ordre de parcours et limites sont explicites.
Les poids ordonnent les branches mais ne changent jamais leur faisabilité.
Pour une cible triplet, `ChoicePoint.variable` désigne son sujet ground.
`PriorityMRVChoicePolicy` et `PriorityWeightedRandomChoicePolicy` peuvent donc
imposer des phases réutilisables sans connaître la règle productrice.

Une action déclarative :

```text
CHOICE ($object value $value) WEIGHT $weight
FROM
    ($object candidate $value)
    ($object choice_weight SEQ[$value $weight])
END_CHOICE
```

transforme chaque solution de `FROM` en instanciation possible du fait cible.
Plusieurs `CHOICE` d'une règle sont séquentiels et lient leurs variables pour
la suite. Les actions ordinaires placées après le dernier choix constituent
une continuation déclenchée quand tous les faits choisis existent.
`RuleChoiceProvider` extrait ces règles du chaînage avant ordinaire.

Les faits utilisés par `WEIGHT` appartiennent à la mémoire de la branche. Une
règle peut retirer une marginale statique et en ajouter une conditionnelle ;
le rollback restaure alors aussi le modèle de poids. Cette modification
n'affecte que l'ordre ou l'échantillonnage des alternatives encore faisables.

Les modifications partielles et un ATMS complet restent différés. Voir
[`collections_fresh_and_contexts.md`](collections_fresh_and_contexts.md) et
[`choice_search.md`](choice_search.md).

## Instanciation et point fixe

La stratégie naïve examine les prémisses dans leur ordre et joint les faits par
backtracking. Une instanciation complète contient la substitution obtenue et
les faits ayant satisfait les prémisses.

Ici, « backtracking » désigne uniquement l’algorithme interne qui énumère les
combinaisons d’une jointure puis annule ses liaisons temporaires. Il ne retire
aucun fait, ne restaure aucun état antérieur du moteur et ne constitue pas le
retour arrière d’un système de résolution de problèmes.

La stratégie indexée compile les règles en patterns et résolveurs d’index,
puis maintient un index exact partagé. Elle l’étend avec les faits ajoutés et
applique les retraits en lot avant l’instanciation suivante, sans reconstruire
les compartiments inchangés. Pendant le backtracking, un cadre mutable pose et
annule ses liaisons ; une substitution immuable n’est construite qu’à une
frontière observable.

Les rangs d'insertion de l'index sont monotones et ne sont plus renumérotés
après un retrait. Les petites mémoires conservent une liste active compacte ;
à partir de 1 500 faits initiaux, un ensemble ordonné rend ajout,
appartenance et retrait directs. Les buckets top-level restent des listes, plus
rapides à parcourir.

Si l'objet d'un triplet est une structure partiellement résolue, par exemple
`SEQ[$left $right]`, le matcher peut construire paresseusement un index
composé sur les chemins déjà liés. Un index n'est demandé que si le meilleur
bucket top-level contient plus de huit faits. Ses chemins et ses clés ne
dépendent que du pattern compilé et de la substitution, jamais du vocabulaire
du domaine.

Chaque règle reçoit un `FactDelta` net et révisionné contenant `added` et
`removed`. La stratégie semi-naïve ne produit que les jointures contenant au
moins un fait ajouté. Les mémoires indexées filtrent leurs supports supprimés
et mettent à jour les compteurs corrélés avec les deux composantes du delta.
Si plusieurs prémisses peuvent recevoir un fait nouveau, les variantes sont
partitionnées puis dédupliquées.

Les témoins et cardinalités sont mémorisés selon le bloc et la projection des
variables corrélées. Des watchers choisissent, à partir de la signature d’un
fait muté, les seules entrées potentiellement affectées. Les requêtes
factuelles simples mettent leur compteur à jour directement ; les requêtes
complexes sont invalidées puis recalculées paresseusement. Les signatures des
watchers incluent les mêmes chemins structurés que les index.

Au-delà de 128 faits, un bloc existentiel factuel structuré conserve au plus
deux témoins. Si le support principal disparaît mais que l'autre reste valide,
ce témoin résiduel est promu sans recalcul de la requête. La borne de deux
évite de transformer ce cache en mémoire RETE complète.

`ForwardEngine` sélectionne cette stratégie semi-naïve par défaut. La stratégie
exhaustive de référence reste accessible explicitement avec
`strategy=NaiveInstantiationStrategy()` pour le diagnostic et les tests
différentiels.

`ConstraintInstantiationStrategy` est une stratégie expérimentale explicite.
Pour une règle constituée uniquement de prémisses factuelles positives et de
comparaisons liées par ces faits, elle construit une table par prémisse,
réduit les domaines de `Term` jusqu'au point fixe, puis exécute le matching
compilé sur les faits encore compatibles. Le filtre est monotone pendant un
examen et sûr : toute valeur éliminée est sans support dans au moins une
prémisse, mais des valeurs globalement incompatibles peuvent subsister.

Les tables sont mises à jour avec les ajouts et suppressions de `FactDelta`.
Les projections de valeurs sont maintenues par compteurs. Une suppression
continue depuis les domaines filtrés précédents ; un ajout réinitialise la
seule composante connexe susceptible de s'élargir. Si le delta ne modifie
aucune table de la règle, domaines et candidats sont réutilisés. Une règle
comportant une négation, un agrégat, une liaison ou une construction
combinatoire utilise automatiquement `SemiNaiveInstantiationStrategy`.

Le point fixe utilise une file de propagateurs tabulaires. Une réduction de
domaine ne réveille que les prémisses et comparaisons incidentes à la
variable concernée. Dans une table, chaque ligne possède un slot stable et
chaque `(variable, valeur)` un masque de supports. Les valeurs supprimées sont
appliquées au masque actif comme événements fins, sans rescanner les lignes.
`use_propagation_queue=False` conserve uniquement un mode diagnostique de
balayage des contraintes.

`AdaptiveInstantiationStrategy` applique en plus une garde stable par règle :
volume minimal de lignes, graphe cyclique, rapport de sélectivité entre
buckets puis réduction réellement observée. Une règle refusée utilise le
matcher semi-naïf. Cette politique ne modifie jamais l'ensemble des
activations. Les formes spécialisées peuvent maintenant être sélectionnées
automatiquement. `==` intersecte les domaines, `!=` propage les singletons,
les ordres numériques propagent leurs bornes et `DIVISIBLE` conserve les
couples possédant un support. Les autres formes gardent le produit cartésien
borné comme repli explicite.

Les opérandes d'une `ComparisonPremise` peuvent être des termes ou des
expressions numériques. La syntaxe
`CONSTRAINT $x + $y == $z` construit le même AST sûr que `LET`, mais sa
sémantique est relationnelle : les trois domaines peuvent être réduits. Les
égalités arithmétiques binaires sont propagées exactement ; l'évaluation
ground du matcher reste l'oracle sémantique.

`DomainPropagator` est le protocole public de spécialisation. Les syntaxes :

```text
NVALUE $count OF SEQ[$x $y $z]
ALL_DIFFERENT SEQ[$x $y $z]
```

sont compilées comme des comparaisons sur le nombre de valeurs distinctes.
`NVALUE` maintient des bornes sûres ; `ALL_DIFFERENT` applique les singletons
et les ensembles de Hall de taille au plus trois. Ces propagateurs ne créent
ni faits ni décisions. Le matcher ground vérifie encore la contrainte globale
sur chaque activation conservée.

Les lignes factuelles, déjà validées lors de la construction de table, ne sont
pas rematchées pendant la jointure. Les liaisons courantes sélectionnent les
slots par intersection de masques, puis leurs liaisons sont injectées dans le
`BindingFrame`. `use_compact_tables=False` et `use_compact_join=False`
réactivent les anciens chemins à des fins de benchmark.

Sur un delta d'ajout, la jointure Compact applique la même sémantique
semi-naïve que le matcher principal : chaque variante impose une prémisse
contenant une ligne nouvelle et impose les lignes anciennes sur les prémisses
antérieures. L'union dédupliquée contient donc exactement les nouvelles
activations. Un delta sans ligne pertinente produit immédiatement zéro
activation ; une suppression repasse par la jointure complète.

La définition immuable d'une table (lignes, slots et supports) est distincte
de son état de propagation (masque actif et domaines appliqués). L'API
publique `DomainStore` enregistre des `DomainReduction` motivées par un
`PropagationReason`; `PropagationResult` expose ces réductions et une
`PropagationContradiction` éventuelle. Le dernier résultat filtré est
consultable dans `ConstraintInstantiationStrategy.last_propagation_results`.
`PropagationState` ajoute des checkpoints imbriqués et restaure domaines et
masques par trail.

Les métriques `domain_input_rows` et `domain_rows_examined` distinguent le
volume logique des anciens examens physiques. Avec les Compact-Tables,
`domain_rows_examined` tombe à zéro ; `domain_bitset_value_events`,
`domain_bitset_support_checks`, `domain_bitset_intersections` et
`domain_compact_join_rows` décrivent le travail restant.
`domain_projection_rows_examined`, `domain_projection_updates`,
`domain_state_reuses` et `domain_component_resets` mesurent séparément la
construction incrémentale des domaines. `domain_delta_join_variants` et
`domain_delta_join_skips` décrivent la jointure semi-naïve filtrée. Les
métriques `domain_cost_probes`, `domain_cost_probe_deferrals` et
`domain_cost_probe_rejections` rendent observable la sélection par coût.

Ce mécanisme ne crée encore aucune branche de session. Le trail est local aux
domaines et masques : il ne restaure ni mémoire de travail, ni réfraction, ni
provenance. L'énumération finale réutilise
le `BindingFrame` local et son rollback de liaisons ; elle ne modifie ni la
mémoire de travail, ni la réfraction, ni la provenance. Choix MRV et recherche
locale complète restent séparés de la recherche métier par `fork()`.

Pour réduire les jointures intermédiaires, une variante semi-naïve commence par
sa prémisse delta et choisit ensuite la prémisse factuelle ayant le moins de
candidats. Les comparaisons forment des barrières textuelles qui ne sont jamais
franchies par cette réorganisation. Les faits prémisses sont finalement remis
dans leur ordre textuel et les activations dans l'ordre d'insertion naïf. Cette
discipline préserve les faits, les dérivations, les cycles et la provenance.

Le même choix du plus petit bucket s'applique aux courtes conjonctions
factuelles des requêtes existentielles structurées. Il n'est pas généralisé
aveuglément aux grands blocs : les mesures montrent que recalculer leur
sélectivité à chaque liaison peut coûter plus cher que conserver leur plan
compilé.

Les règles positives de cardinalité estimée modérée conservent en plus leurs
préfixes de jointure. Une limite configurable borne cette mémoire ; si
l’estimation ou le nombre réel d’états dépasse la limite, la stratégie revient
automatiquement à la jointure compilée exhaustive.

Dans une session persistante, une activation est identifiée par
`(groupe, règle, substitution des prémisses)`. Les liaisons locales calculées
par `LET` ou `FRESH` ne changent pas son identité. La réfraction
empêche son second déclenchement tant qu’elle reste continûment valide. Un
retrait de support ou l’invalidation d’une prémisse négative expire la
réfraction correspondante. Les actions de toutes les nouvelles activations
sont appliquées jusqu’à ce qu’un cycle ne modifie plus aucun fait. Un point
fixe mutable est atteint lorsqu’un cycle n’ajoute ni ne retire de fait. Des
limites explicites de cycles et de faits protègent l’exécution.

Cette sémantique n’impose pas une vérification négative après chaque ajout. Au
premier enregistrement d’un groupe, la session compile les seules règles dont
la réfraction peut être invalidée par une addition. Si aucune n’existe dans
les groupes enregistrés, la réconciliation négative est entièrement omise.

## Ensemble de conflit et MEA

La résolution de conflit est optionnelle. Sans stratégie explicite, le moteur
conserve le balayage déterministe des règles et activations dans leur ordre
source.

Avec `MEAConflictStrategy`, l’ensemble complet des activations est maintenu et
une seule activation est choisie. Le critère principal est le `timeTag` du fait
support marqué `FOCUS`, ou du premier support par compatibilité, suivi d’un
vecteur LEX, de la spécificité et de l’ordre source. Chaque choix est conservé
dans un `AgendaSelection`.

Un index de dépendances factuelles et une mémoire par règle évitent de
réinstancier les règles non concernées par le delta. La stratégie voit malgré
tout tous les candidats au moment du choix.

Un fait initial reçoit un `timeTag` suivant son insertion. Un ajout effectif
reçoit le prochain numéro ; un retrait supprime le numéro et une réinsertion
est fraîche. Marquer `FOCUS ($goal status active)` donne ainsi aux buts une
fraîcheur locale : un sous-but nouveau passe devant son parent.

Ce mode reste du chaînage avant sans hypothèses ni retour arrière. Voir
[`conflict_resolution.md`](conflict_resolution.md).

## Groupes de règles et sessions persistantes

Un `RuleGroup` est un ensemble nommé de règles dont les noms sont uniques. Une
`InferenceSession` conserve la mémoire de travail, les deltas semi-naïfs, la
réfraction et la provenance entre plusieurs appels de groupes.

Quatre modes sont disponibles :

- `SATURATE`, jusqu’au point fixe ;
- `ONE_CYCLE`, pour un balayage ordonné des règles ;
- `FIRST_CHANGE`, jusqu’à la première activation modifiant la mémoire ;
- `UNTIL`, jusqu’à une condition déclarative ou au point fixe.

Lorsqu’une stratégie de conflit est active, `ONE_CYCLE` correspond à une
sélection d’agenda et non à un balayage complet de toutes les règles.

Une règle située plus loin dans un groupe voit les faits ajoutés plus tôt
pendant le même cycle. `FIRST_CHANGE` et `UNTIL` ne coupent jamais une
activation entre deux actions. `FactExists` fournit la première condition
d’arrêt déclarative en testant un motif de fait avant l’exécution, puis après
chaque activation complète.

Un nom de groupe désigne une définition stable pendant une session. Réutiliser
le groupe conserve sa réfraction ; présenter une autre définition sous le
même nom est une erreur. `ForwardEngine(rules).run(facts)` reste le raccourci
compatible : il crée une session neuve et sature un groupe implicite nommé
`default`.

La syntaxe et des exemples complets figurent dans
[`rule_groups.md`](rule_groups.md).

`TechniquePlan` ajoute une orchestration générique au-dessus des groupes. Il
exécute d’abord les groupes de maintenance, essaie les techniques dans l’ordre,
repart de la première après chaque mutation et renvoie `SOLVED`, `STUCK`,
`INCONSISTENT` ou `LIMIT_REACHED`. Il ne contient aucune connaissance du
domaine Sudoku.

`RuleGroupTemplate` spécialise des paramètres ground avant l'enregistrement du
groupe. `RecursiveGroupProcedure` enchaîne des `GroupCall` selon une expansion
DFS ou BFS bornée. Les appels sont une couche de contrôle Python observable ;
ils ne se produisent jamais au milieu d'une activation.

## Recherche, contraintes et maintenance de vérité

`HypothesisSearch` explore des branches isolées, sature les groupes choisis et
teste des objets `StopCondition` de but et de contradiction. Sa stratégie,
ses hypothèses et sa limite de nœuds sont explicites.

`ConstraintSolver` est un protocole indépendant du moteur. Le backend fini de
référence résout `ConstraintProblem`; la couche SAT traduit une CNF vers ce
format. Les solutions peuvent être converties en faits `assigned`, mais le
solveur ne modifie jamais implicitement une session.

Avec `truth_maintenance=True`, `retract()` calcule la plus petite fermeture des
justifications positives depuis les faits initiaux et hypothétiques encore
présents, puis retire le reste. Ce mode optionnel élimine les cycles sans
support externe. Il ne maintient ni environnements alternatifs ni nogoods et
n'est donc pas un ATMS.

## Provenance

Chaque fait initial a une profondeur de preuve nulle. Chaque fait dérivé
enregistre le groupe, la règle, la substitution, les faits prémisses, le cycle
et une profondeur égale à `1 + max(profondeur des prémisses)`. Plusieurs
dérivations peuvent être conservées pour un même fait ; `proof_depth` renvoie
la profondeur minimale connue. Pour un fait produit après `LET`, la
substitution enregistrée inclut les liaisons arithmétiques locales.

En complément, chaque ajout ou retrait effectif produit un `InferenceEvent`
chronologique. Ce journal n’est pas effacé lorsqu’un fait est retiré et permet
de rejouer les transformations de la mémoire.
