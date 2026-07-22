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

Le moteur supporte l’action monotone `ADD` et la liaison arithmétique locale
`LET`. Les actions sont exécutées dans leur ordre textuel. `LET` évalue une
expression numérique déterministe, enrichit la substitution de l'activation
et ne crée aucun fait. Les actions suivantes voient immédiatement la nouvelle
liaison. `ADD` applique la substitution courante à son entité et à son statut,
puis refuse tout résultat non ground.

Les expressions `LET` acceptent les nombres, les variables, les parenthèses et
les opérateurs `+`, `-`, `*` et `/` avec leur précédence usuelle. Leurs
opérandes doivent être numériques et déjà liés ; il ne s'agit pas encore de
résolution de contraintes. Une division par zéro ou un opérande invalide est
une erreur d'exécution explicite. Voir [`arithmetic_actions.md`](arithmetic_actions.md).

Les mises à jour, suppressions, négations par défaut et créations de symboles
frais restent différées.

## Instanciation et point fixe

La stratégie naïve examine les prémisses dans leur ordre et joint les faits par
backtracking. Une instanciation complète contient la substitution obtenue et
les faits ayant satisfait les prémisses.

La stratégie indexée maintient un index exact persistant pour chaque règle et
l'étend uniquement avec les faits ajoutés depuis son évaluation précédente.
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

Une activation est identifiée par `(règle, substitution des prémisses)`. Les
liaisons locales calculées par `LET` sont déterministes et ne changent pas son
identité. La réfraction
empêche son second déclenchement. Les actions de toutes les nouvelles
activations sont appliquées jusqu’à ce qu’un cycle n’ajoute plus aucun fait.
Sur une base initiale finie et des règles monotones sans création de termes, ce
processus termine. Des limites explicites de cycles et de faits protègent les
exécutions futures qui étendront ce périmètre.

## Provenance

Chaque fait initial a une profondeur de preuve nulle. Chaque fait dérivé
enregistre la règle, la substitution, les faits prémisses, le cycle et une
profondeur égale à `1 + max(profondeur des prémisses)`. Plusieurs dérivations
peuvent être conservées pour un même fait ; `proof_depth` renvoie la profondeur
minimale connue. Pour un fait produit après `LET`, la substitution enregistrée
inclut les liaisons arithmétiques locales.
