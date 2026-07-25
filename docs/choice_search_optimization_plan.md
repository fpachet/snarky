# Plan d'optimisation de la recherche `CHOICE`

## Objet et statut

Ce document consigne la tranche d'optimisation exécutée avant la reprise de
l'enrichissement fonctionnel du solveur CSP et de l'harmoniseur.

La tranche P1–P7 a été exécutée le 25 juillet 2026. P8 reste volontairement
différée : après les optimisations précédentes, les profils ne montrent plus
la copie complète des sessions comme centre de coût dominant. Le parallélisme
reste lui aussi un projet ultérieur.

Le but n'était pas de modifier la sémantique de `CHOICE`, MRV, des poids ou du
backtracking, mais de supprimer les coûts techniques observés initialement
autour de chaque nœud :

- branches matérialisées mais jamais explorées ;
- initialisations redondantes pendant un fork ;
- snapshots identiques reconstruits plusieurs fois ;
- index du matcher détruits puis reconstruits après rollback ;
- points de choix réinterrogés sans exploiter les deltas ;
- journaux reparcourus pour reconstituer les mêmes deltas ;
- relations extensionnelles beaucoup plus grandes que le problème logique.

Les sections P1–P7 conservent le problème initial, la réalisation retenue et
les mesures correspondantes. Leur ordre privilégiait les changements
localisés, mesurables et réversibles.

## Invariants

Toutes les étapes doivent préserver :

1. les faits et leur ordre observable ;
2. les solutions et leur ordre par défaut ;
3. les chemins de `ChoiceDecision` et leurs poids ;
4. les nombres logiques de nœuds explorés et de branches en échec ;
5. la réfraction positive et négative ;
6. la provenance et les profondeurs minimales ;
7. les tags temporels et l'ordre MEA ;
8. le caractère déterministe d'une graine donnée ;
9. la session parente ;
10. les chemins de référence naïfs ou à forks.

Une optimisation doit conserver un interrupteur A/B lorsqu'elle introduit un
nouvel algorithme non trivial. Les tests différentiels compareront les deux
chemins avant que l'ancien ne soit éventuellement relégué au seul benchmark.

## Profils de départ

Mesures fonctionnelles du 25 juillet 2026, macOS ARM64, Python 3.13.11 :

| Cas | Médiane | Nœuds | Échecs | Solutions |
|---|---:|---:|---:|---:|
| quatre reines | 17,60 ms | 4 | 1 | 2 |
| N-reines N=8 | 592,86 ms | 16 | 10 | 1 |
| N-reines N=10 | 1,883 s | 27 | 16 | 1 |
| N-reines N=12 | 3,539 s | 27 | 13 | 1 |
| N-reines N=14 | 4,749 s | 20 | 8 | 1 |
| harmoniseur, deux positions | 257,78 ms | 13 | 0 | 3 |

Ces chiffres incluent déjà :

- les alternatives DFS paresseuses ;
- le trail complet d'`InferenceSession` ;
- le clone spécialisé de provenance ;
- un matcher semi-naïf neuf après rollback.

Le profil instrumenté de N=14 compte environ 91 millions d'appels sous
`cProfile`. Les proportions sont indicatives, car l'instrumentation multiplie
la durée, mais les comptes structurels sont fiables :

| Poste | Observation |
|---|---:|
| propagation | 20 appels, environ 84 % du profil |
| `run_group` | 188 appels |
| instanciation semi-naïve | 562 appels, environ 64 % |
| construction de `FactIndex` | 31 constructions |
| lecture de `facts` | 1 143 snapshots |
| parcours du magasin | 17,8 millions d'éléments |
| production des points de choix | 11 appels, environ 12 % |
| reconstruction des deltas | 543 appels |

Le profil de l'harmoniseur montre un autre régime :

| Poste | Observation |
|---|---:|
| nœuds logiquement explorés | 13 |
| forks créés | 108 |
| temps profilé dans `fork()` | environ 51 % |
| reconstruction des noms d'atomes | environ 41 % |
| propagation | environ 38 % |

La première priorité est donc différente pour best-first et pour le DFS :
supprimer les branches spéculatives avides dans le premier, puis conserver
davantage d'état incrémental dans le second.

## Méthode de mesure

Après chaque palier :

1. exécuter les tests ciblés de choix, sessions, CSP et harmoniseur ;
2. exécuter Ruff et mypy ;
3. mesurer au minimum cinq répétitions pour les cas courts et trois pour
   N=8, 10, 12 et 14 ;
4. comparer médiane, minimum, maximum et compteurs logiques ;
5. conserver les résultats JSON datés ;
6. relancer un profil seulement si le centre de coût a changé.

Les gains doivent être rapportés :

- face au palier immédiatement précédent ;
- face à la baseline de ce document ;
- en précisant si le nombre de nœuds ou la formulation du problème change.

Les benchmarks micro ne suffisent pas. Une optimisation n'est retenue que si
elle ne régresse pas significativement les cas d'intégration.

## P1 — Frontières BFS et best-first paresseuses

### Problème

Le moteur construit aujourd'hui tous les enfants d'un `ChoicePoint` :

```text
pour chaque alternative :
    fork(parent)
    assume(alternative)
    ajouter le nœud à la frontière
```

Best-first connaît pourtant le score de l'enfant avant de créer sa session.
La majorité des 108 forks de l'harmoniseur n'est jamais explorée.

### Changement

Placer dans la frontière un descripteur différé :

```text
parent_session
alternative
decisions
log_weight
insertion_order
```

Le fork et l'assertion de l'alternative ne sont réalisés qu'au retrait de ce
descripteur. La session parente est immuable après expansion et peut être
référencée par plusieurs descripteurs.

BFS utilisera la même représentation. Best-first remplacera le balayage
linéaire de la liste par un tas stable si la mesure montre que la frontière
devient assez grande.

### Validation

- même ordre de solutions en BFS et best-first ;
- mêmes décisions, poids et événements logiques ;
- nombre de forks instrumenté ;
- harmoniseur : 108 forks doivent devenir proches du nombre de nœuds
  effectivement retirés de la frontière.

### Risques

- durée de vie plus longue de la session parente ;
- comptage de limite lorsque la frontière contient des descripteurs ;
- ordre stable en cas d'égalité de poids.

## P2 — Chemin rapide de `InferenceSession.fork()`

### Problème

Le constructeur générique :

1. reparcourt tous les faits ;
2. reconstruit leurs nœuds de magasin ;
3. recalcule tous les noms d'atomes réservés ;
4. crée une provenance initiale ;
5. remplace ensuite ces structures par les copies du parent.

Le calcul des noms d'atomes est immédiatement jeté.

### Changement

Introduire un chemin de clonage interne qui initialise directement :

- le magasin cloné ;
- la provenance clonée ;
- l'ensemble des atomes réservé copié ;
- les tags temporels et compteurs hérités.

Le constructeur public conserve son comportement simple. Le chemin rapide
reste une primitive interne de `fork()`.

Un premier `NaiveFactStore.clone()` peut encore être O(n), mais doit éviter
les validations et calculs redondants. Une représentation persistante
base-plus-overlay ne sera envisagée qu'après ce palier.

### Validation

- test différentiel de toutes les propriétés copiées ;
- mutation de la branche sans effet sur le parent ;
- `FRESH`, provenance, MEA et réfraction identiques ;
- profil de l'harmoniseur sans domination de `_atom_names_in`.

## P3 — Cache des snapshots de faits

### Problème

`NaiveFactStore.facts` reconstruit un tuple par parcours de la liste chaînée à
chaque lecture. Or plusieurs consommateurs lisent exactement la même révision :

- propagation avant et après un groupe ;
- instanciation de plusieurs règles ;
- prédicats de but et contradiction ;
- calcul de l'état déjà vu ;
- producteur de choix.

### Changement

Le magasin conserve :

```text
_revision
_snapshot_revision
_snapshot
```

`add`, `remove` et `rollback` invalident le cache. Deux lectures sans mutation
retournent le même tuple. Le rollback peut restaurer le snapshot du
checkpoint si cette conservation est sûre ; le premier incrément se contente
de l'invalider.

### Validation

- ordre exact après ajout, retrait, réinsertion et rollback imbriqué ;
- identité du tuple entre deux lectures de la même révision ;
- invalidation après toute mutation ;
- compte du nombre de reconstructions dans N=14.

## P4 — Matcher réversible

### Problème

Le rollback de session restaure correctement la logique, mais invalide le
matcher. Le prochain frère reconstruit son `FactIndex`, ses watchers et
plusieurs mémoires.

### Architecture progressive

#### P4a — Index de faits réversible

Ajouter au minimum :

- checkpoint de révision ;
- trail des ajouts et suppressions de l'index ;
- restauration de l'ordre stable ;
- restauration du delta traité.

L'index ne doit plus être détruit quand la mémoire de travail revient à un
état connu.

#### P4b — Mémoires de règles

Journaliser ou versionner :

- `_rule_memories` ;
- `_positive_join_memories` ;
- `_pending_removed` ;
- caches de témoins et compteurs simples affectés ;
- enregistrements de watchers créés dans la branche.

Une solution acceptable au premier palier peut conserver l'index et invalider
sélectivement les mémoires de règles touchées.

#### P4c — Interface de stratégie

Étendre prudemment le protocole d'instanciation avec des opérations
optionnelles :

```text
checkpoint()
rollback(checkpoint)
release(checkpoint)
```

`InferenceSession` et `SessionChoiceSearch` détectent cette capacité. Les
stratégies naïves ou tierces continuent à utiliser `invalidate()`.

### Validation

- oracle actuel avec stratégie reconstruite ;
- tests sur ajout, suppression, réinsertion et négation ;
- agrégats et provenance inchangés ;
- métriques d'index comparées ;
- N=14 doit construire sensiblement moins de 31 index complets.

### Risques

C'est le palier le plus délicat. Les watchers négatifs et les mémoires de
jointure ne doivent jamais conserver un témoin issu d'une branche abandonnée.
Le développement doit donc commencer par l'index seul et ajouter les caches
un par un.

### Réalisation retenue

Le palier sûr P4a a été livré sous forme d'un index de branche présemé :
`FactIndex.clone()` partage les faits et les termes immuables, copie les
buckets ordonnés et évite de reparcourir toute la mémoire de travail.
Le checkpoint de recherche mémorise un gabarit de stratégie ; chaque branche
sœur repart de cet index exact au lieu de le reconstruire.

Les mémoires de jointures et de négation restent neuves dans chaque branche.
Ce choix conserve un oracle simple et exclut qu'un témoin d'une branche
abandonnée survive au rollback. Le profil N=14 passe de 31 constructions
d'index complet à 12 à ce palier. P5 ramène ensuite ce nombre à une seule.
Le trail complet des caches P4b/P4c n'est donc plus prioritaire.

## P5 — `RuleChoiceProvider` incrémental

### Problème

Chaque appel construit un nouvel `IndexedInstantiationStrategy` et réinterroge
toutes les règles de choix sur tous les faits.

### Changement

Compiler les règles une fois et maintenir un état par session ou révision :

- index de faits du producteur ;
- dernière révision observée ;
- points de choix par contexte ;
- dépendances entre règles de choix et tokens de faits ;
- invalidation des seuls contextes touchés par le delta.

Le producteur ne doit pas cacher de connaissance métier. Il reste une vue
incrémentale des règles `CHOICE`.

Une première étape moins risquée peut partager le `FactIndex` courant sans
mémoriser les `ChoicePoint`.

### Réalisation retenue

`RuleChoiceProvider` utilise maintenant une vue de requête du matcher courant.
Elle partage son `FactIndex`, mais possède des mémoires de règles locales :
les alternatives ne peuvent donc pas polluer la propagation. Cette première
étape supprime les réindexations complètes observées sans introduire un cache
de `ChoicePoint` délicat à invalider.

### Validation

- oracle sans cache ;
- choix séquentiels multiples dans une règle ;
- poids et ordre identiques ;
- ajout et retrait d'un candidat ;
- invalidation par une nouvelle affectation ;
- diminution du coût des 11 appels observés sur N=14.

## P6 — Deltas nets maintenus directement

### Problème

Les curseurs `_previous_event_counts` indiquent où commencer, mais
`_fact_delta` reparcourt les événements et reconstitue les ajouts et retraits
nets à chaque évaluation de règle.

### Changement

Maintenir un journal de mutations compact par révision, ou un accumulateur
net consommable par règle :

```text
fact → état initial / état final / dernier rang d'ajout
```

Les propriétés nécessaires sont :

- ajout puis retrait : aucune addition nette ;
- retrait puis ajout : réinsertion visible avec ordre correct ;
- plusieurs règles consommant le même intervalle ;
- rollback restaurant les curseurs et accumulateurs.

Une structure globale indexée par révision est préférable à une copie du même
delta pour chaque règle.

### Réalisation retenue

Le profil a montré que le principal coût résiduel n'était pas le parcours de
la courte tranche d'événements, mais le balayage de tous les faits courants
pour remettre les ajouts nets dans l'ordre. `_fact_delta` conserve donc son
oracle événementiel, mais ordonne directement les ajouts par le rang de leur
dernier événement `ADD`. Le balayage de la mémoire de travail disparaît et
`_fact_delta` sort des fonctions dominantes du profil. Un accumulateur
révisionné plus complexe n'est pas justifié à ce stade.

### Validation

- comparaison stricte avec `_fact_delta` ;
- scénarios append-only, remove-only et oscillants ;
- rollback imbriqué ;
- métriques de lignes d'événements parcourues.

## P7 — Représentations moins extensionnelles

Ce palier change le modèle des applications et doit donc venir après la
stabilisation du noyau. Les gains devront distinguer amélioration du moteur et
amélioration de formulation.

### N-reines

La version actuelle matérialise les couples autorisés pour chaque paire de
colonnes. Sa taille croît approximativement comme O(n⁴).

La version intensive réalisée utilise un domaine de ligne par reine et une
règle d'arc-consistance. Un candidat `(colonne, ligne)` est retiré lorsqu'une
autre colonne ne possède plus aucun candidat qui satisfasse simultanément :

- lignes différentes ;
- diagonales `ligne - colonne` différentes ;
- diagonales `ligne + colonne` différentes.

Cette formulation exerce directement `NOT EXISTS`, les comparaisons
arithmétiques, `REMOVE`, le point fixe et `CHOICE`. Elle évite à la fois le
solveur Python et la matérialisation d'une table de couples autorisés. Une
variante `ALL_DIFFERENT` reste intéressante comme futur exercice de
propagateurs globaux, mais n'est pas nécessaire à cette optimisation.

L'objectif n'est pas d'appeler un solveur Python, mais d'exercer les
propagateurs et `CHOICE` Snarky.

Les deux formulations resteront disponibles :

- extensionnelle comme oracle du CSP binaire ;
- intensive comme benchmark réaliste des contraintes globales.

### Harmoniseur

La version à deux positions matérialise les couples de voicings autorisés.
Pour des phrases plus longues, il faut distinguer :

- contraintes verticales calculables sur un voicing ;
- contraintes horizontales locales entre deux positions ;
- préférences et poids ;
- connaissances réellement tabulaires.

Les contraintes calculables doivent devenir des règles ou propagateurs
intensifs. Les relations tabulaires restantes utiliseront des supports
compacts réutilisés entre positions de même type.

Un benchmark de quatre positions au minimum est nécessaire avant de choisir
la représentation finale.

### Réalisation retenue

Les transitions musicales sont maintenant évaluées par deux règles
d'arc-consistance, dans les deux directions. Un `CHECK` enregistré et pur
évalue la transition entre deux voicings ; seuls les liens entre positions
successives sont matérialisés. La formulation extensionnelle reste disponible
comme oracle A/B.

Le cas de quatre positions confirme que le gain grandit avec le nombre de
paires évitées : 1 171 faits deviennent 64, sans changer les 124 nœuds
explorés.

## Bilan d'exécution

### Paliers du noyau

Les mesures intermédiaires ci-dessous utilisent la même phrase de deux
positions et la formulation extensionnelle. Elles isolent donc le coût du
moteur :

| Palier | Médiane | Gain du palier |
|---|---:|---:|
| départ de cette tranche | 259,20 ms | référence locale |
| P1, frontière paresseuse | 139,92 ms | ×1,85 (`-46,0 %`) |
| P2, fork rapide | 114,16 ms | ×1,23 (`-18,4 %`) |
| P3, snapshot des faits | 108,78 ms | ×1,05 (`-4,7 %`) |
| P4–P6, index partagé, vue de choix et delta direct | 99,31 ms | ×1,10 (`-8,7 %`) |

Le gain cumulé du noyau vaut ×2,64 environ sur cette série. La mesure
reproductible finale face à la baseline documentée de 257,78 ms vaut
×2,60 (`-61,5 %`).

Sur N-reines extensionnel N=14, la baseline de 4,749 s devient 2,675 s :
×1,77 (`-43,7 %`), avec toujours 20 nœuds et 8 échecs. Le profil ne construit
plus qu'un index complet, contre 31 au départ.

### Formulations intensionales

| Cas | Extensionnel | Intensionnel | Faits ext. → int. | Gain |
|---|---:|---:|---:|---:|
| N-reines N=14 | 2,675 s | 1,145 s | 15 513 → 253 | ×2,34 (`-57,2 %`) |
| harmonie, 2 positions | 99,31 ms | 37,60 ms | 401 → 32 | ×2,64 (`-62,1 %`) |
| harmonie, 4 positions | 2,573 s | 562,00 ms | 1 171 → 64 | ×4,58 (`-78,2 %`) |

Les compteurs logiques et les solutions sont identiques dans chaque
comparaison. En cumulant moteur et formulation, N=14 passe de 4,749 s à
1,145 s, soit ×4,15 (`-75,9 %`). L'harmoniseur court passe de 257,78 ms à
37,60 ms, soit ×6,86 (`-85,4 %`).

### Frontières

Best-first utilise maintenant un tas stable au lieu d'un balayage linéaire ;
BFS utilise une `deque`. Les descripteurs différés ne créent une session que
lorsqu'ils sont effectivement retirés. L'ordre déterministe, les poids et les
solutions restent identiques au chemin avide conservé pour les tests A/B.

Les résultats bruts sont conservés dans :

- [`../benchmarks/results/choice_search_optimized_2026-07-25.json`](../benchmarks/results/choice_search_optimized_2026-07-25.json) ;
- [`../benchmarks/results/choice_trail_optimized_2026-07-25.json`](../benchmarks/results/choice_trail_optimized_2026-07-25.json) ;
- [`../benchmarks/results/choice_formulations_2026-07-25.json`](../benchmarks/results/choice_formulations_2026-07-25.json).

## P8 — Base immuable et overlays de branches

Ce palier n'a pas été exigé avant la reprise fonctionnelle. Il ne redeviendra
pertinent que si de futurs profils montrent que les forks dominent de
nouveau :

```text
base de faits immuable partagée
    + ajouts locaux
    + tombstones locaux
    + provenance locale
```

Il bénéficierait à BFS, best-first et au futur parallélisme. P1 et P2 ont
cependant supprimé assez de forks pour rendre cette complexité inutile à court
terme.

Voir [`parallel_choice_search.md`](parallel_choice_search.md) pour le lien
avec l'exécution multiprocessus.

## Ordre exécuté

1. P1 — frontières paresseuses ;
2. P2 — fork rapide ;
3. P3 — snapshots de faits ;
4. reprofiler les deux applications ;
5. P4 — index puis matcher réversibles ;
6. P5 — producteur de choix incrémental ;
7. P6 — deltas directs ;
8. P7 — formulations intensives ;
9. décider P8 à partir des nouveaux profils — décision : différer.

## Critères de sortie et résultat

La tranche devait rendre la priorité aux règles CSP et musicales quand :

1. les forks best-first sont proches des nœuds réellement explorés ;
2. le fork ne rescane plus les atomes ;
3. les snapshots identiques ne sont plus reconstruits ;
4. le matcher conserve au moins son index à travers un rollback ;
5. le producteur de choix n'indexe plus toute la session à chaque appel ;
6. les compteurs logiques restent identiques ;
7. N=14 et l'harmoniseur montrent un gain reproductible ;
8. les formulations intensives disposent chacune d'un oracle extensionnel.

Le parallélisme n'est pas un critère de sortie. Il doit venir après la
suppression de ces coûts séquentiels.

Tous ces critères sont atteints. Les prochains travaux peuvent donc revenir
aux fonctionnalités et aux règles du solveur CSP et de l'harmoniseur.
