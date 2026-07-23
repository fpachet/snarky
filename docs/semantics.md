# Sémantique minimale du moteur de référence

Ce document décrit le premier noyau exécutable de Snarky. Il constitue une
décision de conception moderne (`MODERN_EXTENSION`) lorsque les sources
historiques ne permettent pas encore d’attribuer précisément un comportement à
BOOJUM.

## Termes et propositions

Un terme est un `Atom`, un `Number`, un `Variable`, un `Status` standard ou un
`Triple(subject, relation, object)`. Les trois composantes d’un triplet sont à
leur tour des termes. Une proposition est donc un triplet, éventuellement
imbriqué dans un autre triplet. Tous les termes sont immuables, hachables et
comparés structurellement.

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

Le moteur supporte `ADD`, `REMOVE` et la liaison arithmétique locale `LET`.
Les actions sont instanciées avant mutation, puis appliquées dans leur ordre
textuel. `LET` évalue une expression numérique déterministe, enrichit la
substitution de l'activation et ne crée aucun fait. Les actions suivantes
voient immédiatement la nouvelle liaison. `ADD` et `REMOVE` appliquent la
substitution courante à leur entité et à leur statut, puis refusent tout
résultat non ground. Retirer un fait absent est une non-opération.

Les expressions `LET` acceptent les nombres, les variables, les parenthèses et
les opérateurs `+`, `-`, `*` et `/` avec leur précédence usuelle. Leurs
opérandes doivent être numériques et déjà liés ; il ne s'agit pas encore de
résolution de contraintes. Une division par zéro ou un opérande invalide est
une erreur d'exécution explicite. Voir [`arithmetic_actions.md`](arithmetic_actions.md).

Les prémisses `EXISTS` et `NOT EXISTS` contiennent une conjonction locale
corrélée. Elles voient les variables déjà liées, mais leurs variables locales
ne s’échappent pas. Les comparaisons doivent utiliser des variables liées.
L’absence testée par `NOT EXISTS` reste distincte du statut `INEXISTANT`.

Les modifications partielles, créations de symboles frais et hypothèses avec
retour arrière restent différées. Voir
[`mutations_and_negation.md`](mutations_and_negation.md).

## Instanciation et point fixe

La stratégie naïve examine les prémisses dans leur ordre et joint les faits par
backtracking. Une instanciation complète contient la substitution obtenue et
les faits ayant satisfait les prémisses.

La stratégie indexée maintient un index exact persistant pour chaque règle et
l'étend uniquement avec les faits ajoutés depuis son évaluation précédente.
Une suppression invalide les index append-only, qui sont reconstruits avant
l’instanciation suivante.
La stratégie semi-naïve ajoute un delta propre à chaque règle : après sa
première évaluation exhaustive, elle ne produit que les jointures contenant au
moins un fait de ce delta. Si plusieurs prémisses peuvent recevoir un fait
nouveau, les variantes sont partitionnées puis dédupliquées.

`ForwardEngine` sélectionne cette stratégie semi-naïve par défaut. La stratégie
exhaustive de référence reste accessible explicitement avec
`strategy=NaiveInstantiationStrategy()` pour le diagnostic et les tests
différentiels.

Pour réduire les jointures intermédiaires, une variante semi-naïve commence par
sa prémisse delta et choisit ensuite la prémisse factuelle ayant le moins de
candidats. Les comparaisons forment des barrières textuelles qui ne sont jamais
franchies par cette réorganisation. Les faits prémisses sont finalement remis
dans leur ordre textuel et les activations dans l'ordre d'insertion naïf. Cette
discipline préserve les faits, les dérivations, les cycles et la provenance.

Dans une session persistante, une activation est identifiée par
`(groupe, règle, substitution des prémisses)`. Les liaisons locales calculées
par `LET` sont déterministes et ne changent pas son identité. La réfraction
empêche son second déclenchement tant qu’elle reste continûment valide. Un
retrait de support ou l’invalidation d’une prémisse négative expire la
réfraction correspondante. Les actions de toutes les nouvelles activations
sont appliquées jusqu’à ce qu’un cycle ne modifie plus aucun fait. Un point
fixe mutable est atteint lorsqu’un cycle n’ajoute ni ne retire de fait. Des
limites explicites de cycles et de faits protègent l’exécution.

## Groupes de règles et sessions persistantes

Un `RuleGroup` est un ensemble nommé de règles dont les noms sont uniques. Une
`InferenceSession` conserve la mémoire de travail, les deltas semi-naïfs, la
réfraction et la provenance entre plusieurs appels de groupes.

Quatre modes sont disponibles :

- `SATURATE`, jusqu’au point fixe ;
- `ONE_CYCLE`, pour un balayage ordonné des règles ;
- `FIRST_CHANGE`, jusqu’à la première activation modifiant la mémoire ;
- `UNTIL`, jusqu’à une condition déclarative ou au point fixe.

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
