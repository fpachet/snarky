# État de propagation observable et réversible

Snarky possède maintenant les briques d'état nécessaires au futur
`choice`/backtracking, sans encore introduire de recherche implicite dans le
moteur de règles.

## Séparation entre définition et état

Une Compact-Table est séparée en deux parties :

- la définition partageable contient les lignes, leurs slots stables et les
  masques de support `(variable, valeur)` ;
- l'état mutable contient le masque des lignes encore actives et les domaines
  déjà appliqués.

Une future branche pourra donc partager les lignes et les index, puis ne
journaliser que ses réductions de domaines et changements de masques.

## API publique

`DomainStore` est une table de domaines finis. Les opérations `retain`,
`remove` et `restrict` enregistrent un `DomainReduction` avec un
`PropagationReason`. Une réduction qui vide un domaine produit une
`PropagationContradiction`.

`PropagationResult` fournit une vue immuable :

- domaines après point fixe ;
- réductions et leurs causes ;
- contradiction éventuelle ;
- ensemble des variables modifiées.

`ConstraintInstantiationStrategy.last_propagation_results[rule]` expose le
dernier résultat d'une règle filtrée. Cette trace est structurelle : elle
indique par exemple `table/premise 2` ou `comparison/...`, sans prétendre
encore construire une explication minimale.

## Checkpoint et rollback

`DomainStore.checkpoint()` retourne une position de trail. Avec
`PropagationState`, le checkpoint couvre à la fois les domaines et les masques
actifs :

```python
checkpoint = state.checkpoint()
state.domains.restrict(variable, value, reason)
state.set_active_mask(table, mask)
state.rollback(checkpoint)
```

Le rollback est proportionnel au nombre de modifications depuis le
checkpoint, pas à la taille totale de l'état. Le filtre sans branche conserve
les réductions observables mais désactive l'enregistrement du trail inutile.

Ce mécanisme ne restaure pas encore une `InferenceSession`, la réfraction ou
la provenance : il s'agit du trail local d'instanciation qui sera consommé
par le futur pilote de recherche.

## Jointure semi-naïve des tables filtrées

Les Compact-Tables suivent maintenant aussi les lignes ajoutées par
`FactDelta`. Lors d'un cycle append-only, la jointure n'énumère que les
activations contenant au moins une ligne nouvelle. Les variantes sont
partitionnées par prémisse d'ancrage, comme dans le matcher semi-naïf, puis
dédupliquées. Un delta sans ligne pertinente saute entièrement la jointure.
Une suppression conserve le chemin exhaustif nécessaire à la correction.

Les métriques correspondantes sont `domain_delta_join_variants` et
`domain_delta_join_skips`.

## Sélecteur fondé sur le coût observé

La garde adaptative continue d'éliminer statiquement les petits cas, graphes
acycliques et jointures sans réduction. Une réduction très forte sélectionne
directement le filtre. Pour un cas ambigu et récurrent, Snarky peut
chronométrer une fois le filtre et le repli semi-naïf, puis mémoriser le
meilleur chemin par règle.

La sonde contre-factuelle est différée par défaut jusqu'à huit utilisations
afin de ne pas doubler le travail d'une règle exécutée une seule fois. Les
seuils `cost_probe_reduction_ceiling`, `minimum_cost_probe_uses` et
`minimum_observed_speedup` sont configurables. Les métriques distinguent
sondes, reports, refus et temps des deux chemins.

## Mesures du 24 juillet 2026

Par rapport aux Compact-Tables précédentes, la jointure delta réduit les
matchings Sudoku :

| Niveau | Avant | Après | Réduction | Temps avant | Temps après |
|---|---:|---:|---:|---:|---:|
| p1 | 63 946 | 49 531 | 22,5 % | 0,287 s | 0,254 s |
| p6 | 138 846 | 126 198 | 9,1 % | 0,576 s | 0,534 s |
| p7 | 216 643 | 195 160 | 9,9 % | 0,804 s | 0,731 s |

Sur un état synthétique de 1 000 domaines de taille 9 où une branche touche
trois variables, 200 checkpoints/rollbacks prennent 1,103 ms avec le trail
contre 30,706 ms par copies complètes, soit ×27,84.

Commandes :

```sh
python -m benchmarks.compact_tables --levels 1 6 7 --repeat 7
python -m benchmarks.propagation_trail --repeat 7
```

Les mesures sont conservées dans
[`../benchmarks/results/pre_backtracking_2026-07-24.csv`](../benchmarks/results/pre_backtracking_2026-07-24.csv).

## Palier suivant

Les prochaines primitives peuvent maintenant rester petites et
incrémentales :

1. choisir une variable non singleton avec MRV ;
2. poser une décision dans un `PropagationState` ;
3. relancer la file de propagateurs à partir des seules variables modifiées ;
4. convertir une contradiction structurée en échec de branche ;
5. rollback puis essayer l'alternative suivante ;
6. exposer une trace `decision → propagation → contradiction/backtrack`.

Le solveur CSP pédagogique et l'harmoniseur à quatre voix resteront les tests
d'intégration ; le noyau ne contiendra aucune connaissance Sudoku ou musicale.
