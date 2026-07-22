# Plan d’optimisation de Snarky

## Objectif

Snarky possède actuellement un moteur naïf, déterministe et volontairement
simple. Il sert de définition exécutable de la sémantique et d’oracle de
correction. L’objectif des optimisations n’est pas de le remplacer, mais
d’ajouter des stratégies interchangeables qui produisent exactement les mêmes
faits et les mêmes preuves minimales avec de meilleures performances.

Les optimisations doivent préserver les propriétés suivantes :

- termes récursifs immuables et hachables ;
- variables autorisées dans les trois positions d’un triplet ;
- propositions utilisées comme termes ;
- distinction entre `VRAI`, `FAUX`, `INEXISTANT` et l’absence ;
- résultats déterministes par défaut ;
- réfraction des activations ;
- provenance vérifiable ;
- point fixe identique à celui du moteur naïf.

## État au 22 juillet 2026

| Phase | État | Résultat ou prochaine étape |
|---|---|---|
| 0 — Mesures | Partielle | Benchmark Fibonacci reproductible et compteurs d'instanciation disponibles ; autres scénarios et mémoire à ajouter |
| 1 — Activations paresseuses | À faire | Les stratégies matérialisent encore leurs activations dans un tuple |
| 2 — Indexation | Première tranche terminée | Index exacts par snapshot disponibles ; stockage indexé persistant à construire |
| 3 — Semi-naïf | Prochaine priorité | Ne recalculer que les jointures contenant au moins un fait nouveau |
| 4 à 9 | À faire | À engager après mesure des phases 2 persistante et 3 |

L'extension fonctionnelle `LET` est terminée : Fibonacci utilise désormais
l'arithmétique native du moteur et ne dépend plus de tables de sommes et de
prédécesseurs.

La stratégie indexée est volontairement optionnelle : le moteur naïf reste le
comportement par défaut et l'oracle de correction. Les tests différentiels
vérifient l'égalité des faits, des dérivations, des cycles et des activations.

## Situation initiale

Le moteur actuel effectue une jointure exhaustive par backtracking. Pour chaque
prémisse factuelle, il parcourt la totalité de la base. À chaque cycle, il
recalcule également les instanciations anciennes avant de les éliminer par
réfraction.

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

Le benchmark reproductible `benchmarks/fibonacci_explicit.py` couvre désormais
le scénario Fibonacci explicite. Pour `F(10)`, trois passages sur la machine de
développement donnent 7,243 s avec la stratégie naïve contre 0,245 s avec la
première stratégie indexée. Les deux produisent les mêmes 326 faits et les
mêmes dérivations. Les tentatives de matching passent de 557 302 à 8 963.

La baseline indexée couvre maintenant les rangs 10 à 17. Le temps croît de
0,245 s à 27,914 s, le point fixe de 326 à 9 578 faits et les activations
produites de 1 782 à 95 013. `F(15)` reste sous 10 secondes et `F(17)` sous 30
secondes. Le tableau complet et sa version CSV se trouvent dans
`benchmarks/README.md` et `benchmarks/results/`.

## Principe d’architecture

Les stratégies partagent actuellement cette interface commune :

```python
class InstantiationStrategy(Protocol):
    metrics: InstantiationMetrics

    def instantiate(
        self,
        rule: Rule,
        facts: tuple[Fact, ...],
    ) -> tuple[Activation, ...]: ...
```

Les phases 1 à 3 feront évoluer cette interface vers une vue stable, un delta
optionnel et un itérateur, sans modifier les modèles publics de règles et de
faits.

Le moteur naïf restera disponible sous le nom
`NaiveInstantiationStrategy`. Chaque nouvelle stratégie sera testée
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

Pour mesurer les progrès, chaque phase devra rejouer la plage `F(10)` à
`F(17)`, rapporter les ratios par rapport au CSV de référence et indiquer les
plus grands rangs passant sous 10 et 30 secondes. L'égalité différentielle
avec l'oracle naïf reste obligatoire sur les rangs où son coût est acceptable.

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
pour réduire la mémoire et préparer l'évaluation semi-naïve.

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

**État : première tranche terminée.**

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

Une première tranche est implémentée par `IndexedInstantiationStrategy`. Elle
construit, pour chaque vue stable des faits, des index exacts sur l’entité, le
statut, le sujet, la relation et l’objet, puis sélectionne le plus petit bucket
compatible avec la substitution courante. L’ordre textuel des prémisses et
l’ordre d’insertion des candidats sont préservés. Un futur `IndexedFactStore`
persistant évitera la reconstruction de ces index à chaque règle et cycle.

Les index plus profonds, portant sur des chemins dans les triplets imbriqués,
ne seront ajoutés qu’après mesure de leur utilité.

Critère de validation : le nombre de faits proposés au matcher doit diminuer
sans modifier les activations produites.

Ce critère est satisfait sur Fibonacci `F(10)` : 8 963 faits candidats contre
557 302 pour l'oracle naïf, avec les mêmes 1 782 activations produites et les
mêmes 163 activations effectivement déclenchées. Les 51 reconstructions
d'index observées constituent la prochaine limite propre à cette phase.

## Phase 3 — Évaluation semi-naïve

**État : prochaine priorité.** Le benchmark `F(10)` produit encore 1 782
activations au fil des cycles avant que la réfraction ne les ramène à 163
déclenchements uniques. Cette différence fournit le compteur principal pour
évaluer cette phase.

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

## Phase 4 — Planification des jointures

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

## Phase 5 — Substitutions et matching

Optimiser seulement après profilage les opérations de bas niveau :

- accès moyen en temps constant aux variables liées ;
- cache du hachage immuable ;
- application structurelle évitant de reconstruire un triplet inchangé ;
- représentation compacte des variables compilées par identifiant entier ;
- partage structurel des substitutions parentes ;
- cache prudent des signatures de termes.

Le modèle public `Variable` doit rester lisible. Une représentation compilée
interne pourra être introduite sans modifier l’API.

## Phase 6 — Sélection des règles candidates

Créer un `RuleCandidateIndex` reliant les signatures de faits aux prémisses de
règles susceptibles de les accepter.

Lorsqu’un fait est ajouté, le moteur ne doit réveiller que les règles dont au
moins une prémisse peut matcher ce fait. Les règles contenant une relation
variable ou un pattern très général conserveront un chemin de repli correct.

## Phase 7 — Provenance configurable

Proposer plusieurs politiques :

- `MinimalProofOnly` : conserver uniquement la meilleure preuve connue ;
- `AllProofs(limit=n)` : conserver plusieurs preuves avec une limite ;
- `CountOnly` : compter les dérivations sans les matérialiser ;
- `NoProvenance` : mode benchmark explicitement demandé.

La provenance complète restera le comportement de référence. Les politiques
réduites devront être choisies explicitement et ne devront jamais produire une
preuve incorrecte.

## Phase 8 — Instanciation centrée sur les variables

Implémenter ensuite l’approche inspirée de BOOJUM :

1. construire un domaine candidat pour chaque variable ;
2. projeter les faits candidats sur les positions correspondantes ;
3. propager les réductions de domaines ;
4. choisir la variable la plus contrainte ;
5. backtracker uniquement lorsqu’une propagation ne suffit pas.

Cette stratégie sera représentée explicitement par :

```text
VariableDomain
PartialInstantiation
ConstraintNetwork
InstantiationState
ChoiceHeuristic
```

Elle devra produire les mêmes activations que les stratégies naïve et
semi-naïve sur les programmes de test.

## Phase 9 — Raisonnement par contraintes

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

1. introduire une vue de faits indexée persistante, mise à jour à chaque ajout,
   afin de supprimer les 51 reconstructions observées sur `F(10)` ;
2. exposer le delta de chaque cycle à la stratégie d'instanciation ;
3. ajouter les variantes semi-naïves sans dupliquer les activations lorsqu'un
   fait nouveau peut satisfaire plusieurs prémisses ;
4. étendre les tests différentiels aux règles mutuellement récursives ;
5. rejouer le benchmark Fibonacci et consigner temps, candidats, activations
   produites et mémoire maximale dans une nouvelle série comparable au CSV de
   référence ;
6. comparer explicitement les seuils de 10 et 30 secondes avec `F(15)` et
   `F(17)`, limites observées de la première stratégie indexée.

Le critère de sortie est l'identité complète avec le moteur naïf, accompagnée
d'une baisse mesurée des 51 constructions d'index et des 1 782 activations
produites, sans imposer à l'avance un objectif temporel dépendant de la
machine.
