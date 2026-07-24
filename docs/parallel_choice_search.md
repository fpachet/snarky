# Exploration parallèle des alternatives de `CHOICE`

## Statut

Cette note décrit une extension possible. Elle ne correspond à aucune API
implémentée et n'ajoute aucun parallélisme au moteur actuel.

L'objectif est d'exécuter simultanément plusieurs alternatives coûteuses d'un
`ChoicePoint`, tout en conservant :

- la sémantique déclarative de `CHOICE` ;
- l'isolation des branches ;
- le trail réversible à l'intérieur de chaque exploration ;
- des solutions et des traces déterministes par défaut ;
- un chemin séquentiel simple servant d'oracle.

Le parallélisme est une politique d'exécution de la recherche. Il ne doit pas
changer la manière dont une règle produit ses alternatives.

## Pourquoi le trail courant ne peut pas être partagé

Le DFS réversible actuel utilise une session mutable unique :

```text
checkpoint
    → alternative A
    → propagation
rollback
    → alternative B
```

Deux alternatives ne peuvent pas modifier simultanément cette session. Elles
écriraient dans les mêmes faits, journaux, compteurs de réfraction, caches et
trails. Ajouter des verrous sérialiserait précisément le travail que l'on
cherche à paralléliser et rendrait l'ordre observable difficile à définir.

Le bon niveau d'isolation est donc le travailleur :

```text
                         ┌─ fork A → DFS local avec trail
ChoicePoint coordonné ───┼─ fork B → DFS local avec trail
                         └─ fork C → DFS local avec trail
```

Un fork est créé pour chaque sous-arbre effectivement confié à un travailleur.
À l'intérieur de ce sous-arbre, les choix suivants réutilisent le trail
réversible. On évite ainsi une copie par nœud sans partager un état mutable.

## Processus plutôt que threads

Le matching et la propagation sont principalement des calculs CPU Python.
Des threads offriraient peu de parallélisme à cause du GIL et les sessions ne
sont pas conçues pour être thread-safe.

Le premier backend à étudier devrait donc utiliser des processus :

- espace mutable et matcher indépendants par travailleur ;
- aucune synchronisation fine pendant la propagation ;
- crash ou annulation confinés à une branche ;
- possibilité d'exploiter plusieurs cœurs.

Ce choix déplace le risque vers le transfert de l'état. Sur macOS, le démarrage
en mode `spawn` sérialise normalement les données. Une base N-reines de grande
taille contient des milliers de faits extensionnels ; recopier toute cette base
pour une alternative courte peut coûter davantage que son exploration.

## Architecture hybride recommandée

Le coordinateur reste responsable de :

1. saturer l'état courant ;
2. sélectionner le `ChoicePoint` selon MRV ou la politique demandée ;
3. calculer une seule fois l'ordre pondéré des alternatives ;
4. décider si le point est assez coûteux pour être partagé ;
5. distribuer quelques sous-arbres ;
6. fusionner les solutions, statistiques et traces ;
7. appliquer limites et annulations.

Chaque travailleur :

1. reçoit un état isolé et un chemin de décisions ;
2. affirme son alternative racine ;
3. propage jusqu'au point fixe ;
4. poursuit en DFS réversible local ;
5. retourne solutions, échec, compteurs et trace étiquetée.

Le parallélisme doit rester borné. La première expérience ne partagerait que
le premier point de choix, avec au plus un sous-arbre par cœur. Un découpage
récursif et dynamique ne serait envisagé qu'après mesure d'un gain réel.

## Granularité et seuil d'activation

Tous les choix ne justifient pas un processus. Le coordinateur devrait rester
séquentiel lorsque :

- le point ne contient qu'une ou deux alternatives très courtes ;
- la propagation locale estimée est faible ;
- la mémoire de travail est grande par rapport au sous-arbre ;
- le nombre de solutions demandé est déjà presque atteint ;
- des travailleurs existants ont encore du travail.

Les premiers paramètres expérimentaux pourraient être :

```text
max_workers
split_depth
minimum_alternatives
minimum_estimated_cost
```

Ils décriraient la politique de recherche, pas la règle `CHOICE`. Aucun de ces
noms ne constitue encore une API publique.

Une estimation simple peut combiner :

- nombre d'alternatives ;
- nombre de faits actifs ;
- coût de la dernière saturation ;
- nombre de règles réveillées ;
- taille du sous-arbre observée pour les alternatives déjà terminées.

## Déterminisme

L'ordre d'arrivée des travailleurs ne doit pas devenir l'ordre logique des
solutions par défaut.

Chaque travail distribué reçoitrait :

- un identifiant de branche ;
- son chemin de `ChoiceDecision` ;
- un rang logique déterminé par la politique séquentielle ;
- éventuellement sa priorité pondérée.

Le coordinateur peut exécuter spéculativement plusieurs branches mais publier
leurs résultats dans l'ordre séquentiel de référence. Si B termine avant A,
son résultat est conservé jusqu'à ce que le sort logique de A soit connu.

Deux modes pourraient être distingués à terme :

- **strict** : première solution, liste des solutions et trace logique
  reproduisent l'ordre séquentiel ;
- **throughput** : les solutions peuvent être livrées à l'arrivée, avec un
  ordre explicitement non déterministe.

Seul le mode strict pourrait devenir le comportement par défaut.

Le travail spéculatif ne doit pas fausser les compteurs. Les métriques
devraient séparer :

- nœuds logiquement explorés dans la recherche publiée ;
- nœuds spéculatifs réellement calculés ;
- branches annulées ;
- temps de calcul des travailleurs ;
- temps de sérialisation et de coordination.

## Poids et politiques probabilistes

Les poids ne changent jamais la faisabilité. Le coordinateur calcule l'ordre
des alternatives avec l'unique générateur pseudo-aléatoire et transmet cet
ordre aux travailleurs. Une graine donnée reste donc reproductible.

Pour le best-first de l'harmoniseur, plusieurs états de la frontière peuvent
être développés simultanément. Leur ordre de fin ne doit pas remplacer
l'ordre de priorité. Une implémentation stricte attribuerait des tickets lors
du retrait de la file et ne publierait une solution qu'après résolution des
travaux antérieurs susceptibles de la précéder.

Le parallélisme n'autorise pas à interpréter les poids comme des probabilités
jointes. Il accélère seulement la politique de recherche existante.

## Représentation de l'état

Trois paliers sont possibles :

1. **fork sérialisé complet** : simple, mais probablement coûteux ;
2. **base immuable partagée + delta de branche** : faits initiaux et
   structures compilées partagés, mutations et provenance locales ;
3. **snapshot compact spécialisé** : représentation transférable de la
   mémoire de travail, de la réfraction et du chemin de décisions.

Le premier palier suffit pour mesurer le coût plancher de l'orchestration.
Le second est probablement nécessaire pour obtenir un gain substantiel sur
les CSP extensionnels et l'harmoniseur.

Le partage doit rester en lecture seule. Les caches mutables du matcher et le
trail appartiennent toujours à un seul travailleur.

## Annulation et limites

Quand `max_solutions` est atteint, le coordinateur demande l'annulation des
travaux devenus inutiles. L'annulation doit être coopérative, entre deux
cycles ou deux nœuds de recherche, et non interrompre une mutation au milieu
d'une activation.

Les limites globales demandent une sémantique explicite :

- `max_nodes` logique pour préserver le résultat séquentiel ;
- budget spéculatif séparé pour borner le calcul réellement consommé ;
- délai global optionnel ;
- limite de mémoire ou de travaux en vol.

Une branche annulée n'est ni une contradiction ni un `dead_end`. La trace
devrait employer un événement technique distinct.

## Plan expérimental différé

Si cette piste devient prioritaire :

1. définir le format minimal d'un travail et de son résultat ;
2. paralléliser uniquement le premier choix ;
3. garder un DFS réversible séquentiel dans chaque travailleur ;
4. fournir le mode strict avant tout mode opportuniste ;
5. mesurer séparément calcul, copie, sérialisation et fusion ;
6. n'ajouter un partage dynamique que si le premier palier accélère des cas
   réels.

Les benchmarks initiaux seraient :

- N-reines N=12 à N=16 ;
- harmoniseur sur des phrases plus longues que les deux positions actuelles ;
- un problème étroit et profond, pour vérifier que le parallélisme se
  désactive ;
- un problème large avec branches équilibrées ;
- 1, 2 et 4 travailleurs.

Pour chaque cas, il faut comparer :

- temps mur et temps CPU total ;
- pic mémoire ;
- temps de transfert ;
- nombre de nœuds logiques et spéculatifs ;
- solutions, poids, décisions et traces ;
- speedup face au DFS ou best-first séquentiel courant.

## Critères avant implémentation

L'implémentation ne devrait commencer que si :

1. une application réelle présente plusieurs sous-arbres assez coûteux ;
2. le coût de transfert de session est mesuré ;
3. la sémantique du mode strict est fixée ;
4. le DFS séquentiel reste disponible comme oracle ;
5. la parallélisation ne nécessite aucune modification du DSL `CHOICE`.

Cette extension est donc compatible avec l'architecture actuelle, mais elle
n'est pas une priorité immédiate. L'étape préparatoire la plus utile serait
une représentation compacte « base immuable + delta de branche », également
profitable aux forks BFS et best-first même sans parallélisme.
