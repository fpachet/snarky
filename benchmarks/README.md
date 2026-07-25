# Benchmarks Snarky

Les benchmarks sont des programmes reproductibles séparés des tests de
correction. Ils produisent du JSON afin de pouvoir comparer plusieurs
versions du moteur.

## Choix, backtracking et applications

`choice_search` mesure les deux premiers projets qui utilisent
`SessionChoiceSearch` :

```sh
PYTHONPATH=src python -m benchmarks.choice_search --repeat 5
```

Mesure finale du 25 juillet 2026 sur macOS ARM64 avec Python 3.13.11 :

| Projet | Médiane | Nœuds explorés | Branches en échec | Solutions |
|---|---:|---:|---:|---:|
| quatre reines | 15,43 ms | 4 | 1 | 2 |
| harmoniseur SATB, 2 positions | 37,31 ms | 13 | 0 | 3 |
| harmoniseur SATB, 4 positions | 549,50 ms | 124 | 0 | 3 |

Le solveur des reines propage trois affectations après la première décision.
L'harmoniseur utilise 15 voicings sur la première position et 9 sur la
seconde.

Le DFS utilise un trail de session. Les frontières BFS et best-first stockent
des alternatives différées et ne créent une session qu'au moment de les
explorer. Le fork initialise directement le magasin et la provenance clonés ;
les snapshots de faits sont mis en cache ; les branches repartent d'un index
présemé ; `RuleChoiceProvider` partage une vue de cet index et les deltas
nets ne rescannent plus tous les faits. Best-first utilise un tas stable et
BFS une `deque`.

Le passage du générateur Python à la règle déclarative `CHOICE ... FROM`
reste inclus dans ces mesures.

Le résultat JSON courant est conservé dans
[`results/choice_search_optimized_2026-07-25.json`](results/choice_search_optimized_2026-07-25.json) ;
les mesures précédentes restent disponibles dans
[`results/choice_search_2026-07-25.json`](results/choice_search_2026-07-25.json)
et
[`results/choice_search_2026-07-24.json`](results/choice_search_2026-07-24.json).

### Décomposition des gains

Sur la phrase extensionnelle de deux positions, les paliers successifs
passent de 259,20 à 139,92 ms avec la frontière paresseuse, puis 114,16 ms
avec le fork rapide et 108,78 ms avec les snapshots. Après partage d'index,
vue de requête et delta direct, la mesure finale extensionnelle vaut
99,31 ms. Face à la baseline publiée de 257,78 ms, le gain propre au noyau
vaut ×2,60 (`-61,5 %`).

La formulation intensionnelle réduit ensuite 401 faits à 32 et atteint
37,60 ms : ×2,64 supplémentaire, ou ×6,86 (`-85,4 %`) depuis la baseline.
Les 13 nœuds et l'ordre des solutions restent identiques.

## Trail de choix sur N reines

`choice_trail` compare le DFS à forks paresseux, conservé comme oracle, au
DFS réversible :

```sh
PYTHONPATH=.:src python benchmarks/choice_trail.py --repeat 3
```

| Taille | Forks paresseux | Trail | Gain propre au trail | Nœuds / échecs |
|---:|---:|---:|---:|---:|
| 8 | 516,74 ms | 440,12 ms | ×1,17 (`-14,8 %`) | 16 / 10 |
| 10 | 1,568 s | 1,206 s | ×1,30 (`-23,1 %`) | 27 / 16 |
| 12 | 2,867 s | 2,031 s | ×1,41 (`-29,2 %`) | 27 / 13 |
| 14 | 4,125 s | 2,748 s | ×1,50 (`-33,4 %`) | 20 / 8 |

Le gain augmente avec la taille de la mémoire de travail. Il ne vient pas
d'une meilleure heuristique : nœuds, échecs et profondeur de solution sont
identiques dans les deux modes.

Une baseline de développement prise immédiatement avant ces optimisations
utilisait encore les forks matérialisés pour tous les frères. La comparaison
de bout en bout est :

| Taille | Forks avides initiaux | Trail final | Accélération totale |
|---:|---:|---:|---:|
| 8 | 907,15 ms | 592,86 ms | ×1,53 (`-34,6 %`) |
| 10 | 3,638 s | 1,883 s | ×1,93 (`-48,2 %`) |
| 12 | 9,099 s | 3,539 s | ×2,57 (`-61,1 %`) |
| 14 | 16,035 s | 4,749 s | ×3,38 (`-70,4 %`) |

Pour N=14, les paliers mesurés ont été : 16,035 s avec création avide de
tous les frères, 8,985 s avec frères paresseux, 5,935 s avec les forks
paresseux et la provenance spécialisée, puis 4,749 s avec rollback en place.

Les résultats reproductibles des deux modes courants sont dans
[`results/choice_trail_optimized_2026-07-25.json`](results/choice_trail_optimized_2026-07-25.json).

## Formulations extensionnelles et intensionales

`choice_formulations` mesure séparément l'effet du modèle, sur le même moteur
optimisé :

```sh
PYTHONPATH=.:src python benchmarks/choice_formulations.py --repeat 3
```

| Cas | Extensionnel | Intensionnel | Faits ext. → int. | Gain |
|---|---:|---:|---:|---:|
| N-reines N=14 | 2,675 s | 1,145 s | 15 513 → 253 | ×2,34 (`-57,2 %`) |
| harmonie, 2 positions | 99,31 ms | 37,60 ms | 401 → 32 | ×2,64 (`-62,1 %`) |
| harmonie, 4 positions | 2,573 s | 562,00 ms | 1 171 → 64 | ×4,58 (`-78,2 %`) |

Les solutions et compteurs de recherche sont identiques. Les reines
intensionnelles utilisent une règle de recherche de supports avec trois
comparaisons arithmétiques. L'harmoniseur utilise deux règles de révision
dirigée et un prédicat musical pur enregistré. Aucun des deux chemins
intensionnels n'appelle un solveur Python.

Depuis le début de cette tranche, N=14 passe de 4,749 à 1,145 s : ×4,15
(`-75,9 %`). Depuis les forks avides initiaux à 16,035 s, le gain cumulé vaut
×14,0 (`-92,9 %`), tout en conservant 20 nœuds et 8 échecs.

Les données brutes sont dans
[`results/choice_formulations_2026-07-25.json`](results/choice_formulations_2026-07-25.json).

## CSP générique et harmoniseur note par note

Le benchmark du jalon suivant compare les chemins applicatifs, construction
du modèle comprise :

```sh
PYTHONPATH=.:src python -m benchmarks.csp_harmonizer_next --repeat 5
```

| Cas | Médiane | Nœuds | Échecs | Solutions |
|---|---:|---:|---:|---:|
| Sudoku p2, règles humaines complètes | 294,36 ms | — | 0 | 1 |
| Sudoku p2, Naked Singles + recherche | 1,942 s | 11 | 4 | 1 |
| harmoniseur, choix d'un voicing | 34,92 ms | 13 | 0 | 3 |
| harmoniseur, variables de notes | 145,06 ms | 19 | 0 | 3 |

Le Sudoku de recherche ne vise pas à battre les règles humaines : il les
limite volontairement pour tester une contradiction et un rollback réels.
L'harmoniseur note par note paie ×4,15 pour exposer les variables, la
canalisation et les marginales conditionnelles. Ces résultats constituent la
baseline à optimiser lors de l'ajout des règles `ROY_1998`.

Les résultats bruts sont conservés dans
[`results/csp_harmonizer_next_2026-07-25.json`](results/csp_harmonizer_next_2026-07-25.json).

## Frontière MuSES de l'harmoniseur

Ce benchmark isole le coût applicatif du trajet objet complet par rapport à
l'entrée symbolique directe :

```sh
PYTHONPATH=.:src python -m benchmarks.muses_harmonizer --repeat 7
```

Mesure du 25 juillet 2026 sur macOS ARM64 avec Python 3.13.11 :

| Chemin, 2 positions, 1 solution | Médiane | Décisions |
|---|---:|---:|
| tuple de hauteurs → harmoniseur | 66,09 ms | 4 |
| `TemporalCollection` → faits → règles → `Piece` | 69,81 ms | 4 |

Le codec, l'import par règle et la reconstruction des quatre collections
ajoutent 3,72 ms, soit `+5,6 %`. Le nombre de décisions et la solution ne
changent pas : le coût reste dominé par la génération, la propagation et la
recherche du modèle musical.

L'orchestration explicite retire en outre le groupe de contraintes binaires
qui ne rencontrait aucun fait dans ce modèle. Par rapport aux mesures
précédentes, cela réduit le chemin symbolique de `11,0 %` et le pipeline MuSES
de `12,3 %`, sans changer les résultats ni les décisions.

Le script emploie des classes structurellement compatibles afin de rester
reproductible sans dépendance optionnelle. Les tests d'intégration exécutent
le même chemin avec les vraies classes MuSES lorsqu'elles sont disponibles.
Les données brutes sont dans
[`results/muses_harmonizer_2026-07-25.json`](results/muses_harmonizer_2026-07-25.json).

## Filtrage des domaines avant instanciation

`constraint_instantiation` propose quatre scénarios : triangle favorable,
jointure neutre, triangle dense défavorable et longue chaîne acyclique. Il
compare l'indexé, les balayages complets, la file de propagateurs et le
sélecteur adaptatif :

```sh
uv run python -m benchmarks.constraint_instantiation \
    --scenario favorable --size 40 --repeat 9
```

Mesure du 24 juillet 2026 sur macOS ARM64 avec Python 3.13.11 :

| Scénario | Taille | Indexée | Filtrage forcé | Adaptative | Gain adaptatif |
|---|---:|---:|---:|---:|---:|
| Favorable | 40 | 189,52 ms | 17,23 ms | 17,23 ms | ×11,00 |
| Neutre | 200 | 2,987 ms | 5,035 ms | 2,826 ms | ×1,06 |
| Défavorable | 20 | 52,03 ms | 58,24 ms | 52,17 ms | ×1,00 |
| Chaîne | 40 | 6,741 ms | 8,706 ms | 6,413 ms | ×1,05 |

Dans le cas favorable, la jointure textuelle crée beaucoup d'états
intermédiaires : le matcher final passe de 65 640 à 120 tentatives, après
3 201 matchings préparatoires. Le gain vient donc de la suppression des
produits intermédiaires, pas d'un matching élémentaire moins cher.

Le neutre et le défavorable montrent pourquoi le filtrage forcé ne doit pas
être le défaut. Le sélecteur les refuse et reste dans le bruit de mesure de
la jointure indexée.

La chaîne mesure spécifiquement le point fixe. La file examine 4 802 lignes
en 122 révisions, contre 67 242 lignes et 1 722 révisions pour les balayages
complets. Le temps de filtrage passe de 43,06 à 8,71 ms, soit ×4,95. La
jointure indexée reste néanmoins meilleure ; le graphe acyclique permet au
sélecteur de ne pas lancer le filtre.

Le script accepte :

```sh
--scenario favorable
--scenario neutral
--scenario adverse
--scenario chain
```

La stratégie adaptative est encore expérimentale et n'est pas le défaut.
Les résultats sont conservés dans
[`results/constraint_instantiation_2026-07-24.csv`](results/constraint_instantiation_2026-07-24.csv).

## Contraintes arithmétiques spécialisées

`arithmetic_constraints` construit deux domaines de 200 entiers et fixe leur
somme à 2 avec :

```text
CONSTRAINT $left + $right == $total
```

```sh
uv run python -m benchmarks.arithmetic_constraints \
    --size 200 --repeat 9
```

| Stratégie | Médiane | Matchings finaux | Travail de contrainte |
|---|---:|---:|---:|
| indexée | 346,36 ms | 160 400 | — |
| domaines, produit cartésien | 82,42 ms | 6 | 40 001 combinaisons |
| spécialisé, tables scannées | 2,292 ms | 6 | 801 lignes |
| spécialisé, bitsets | 2,025 ms | 6 | 398 retraits |
| spécialisé, jointure compacte | 2,010 ms | 6 | 398 retraits |
| adaptative | 2,049 ms | 6 | 398 retraits |

Le propagateur choisit entre les paires `(left, right)`, `(left, total)` et
`(right, total)`. Comme `total` est singleton, il effectue un parcours
linéaire au lieu d'énumérer le produit des trois domaines. L'état persistant
évite aussi la seconde propagation identique. Le gain vaut environ ×41 entre
filtre générique et spécialisé, et ×169 entre indexé et adaptatif.

Les résultats sont conservés dans
[`results/arithmetic_constraints_2026-07-24.csv`](results/arithmetic_constraints_2026-07-24.csv).

## Contraintes globales

`global_constraints` mesure `NVALUE` puis `ALL_DIFFERENT` :

```sh
uv run python -m benchmarks.global_constraints --size 200 --repeat 7
```

| Scénario | Indexée | Domaines reconstruits | Domaines persistants | Adaptative |
|---|---:|---:|---:|---:|
| `NVALUE`, N = 1 | 414,61 ms | 2,47 ms | 2,06 ms | 2,13 ms |
| `ALL_DIFFERENT`, Hall triple | 67,36 ms | 68,33 ms | 69,39 ms | 44,88 ms |

Sur `NVALUE`, le filtre ramène 160 402 tentatives de matching à 8 et
l'adaptatif gagne ×194,7. La persistance réduit les 1 206 lignes projetées
par les deux passages à 402 et ne propage qu'une fois.

Le scénario `ALL_DIFFERENT` doit réellement produire 1 182 solutions. Son
gain adaptatif plus modeste, ×1,51, vient du retrait précoce de l'ensemble de
Hall et du repli semi-naïf au cycle suivant. Cette différence illustre que le
coût utile dépend autant du nombre de solutions que de la force du filtre.

Les résultats sont conservés dans
[`results/global_constraints_2026-07-24.csv`](results/global_constraints_2026-07-24.csv).

## Propagation de contraintes déclarative

Le benchmark exécute les trois problèmes de
[`constraints/binary`](../rulebases/constraints/binary/README.md) : une
chaîne résolue, un triangle réduit à un point fixe incomplet et une paire
contradictoire. Les règles produisent dans chaque cas 84 faits, 18
activations et huit cycles cumulés :

```sh
uv run python -m benchmarks.constraint_propagation \
    --repeat 7 --batch-size 20
```

Mesure courante du 24 juillet 2026 sur macOS ARM64 avec Python 3.13.11 :

| Stratégie | Médiane | Gain sur le naïf |
|---|---:|---:|
| Naïve | 44,190 ms | référence |
| Indexée | 3,725 ms | ×11,82 |
| Semi-naïve | 3,577 ms | ×12,31 |
| Adaptative | 3,597 ms | ×12,24 |

L'indexation élimine donc déjà l'essentiel du coût sur cet exemple. L'écart
de 3 % entre indexé et semi-naïf n'est pas significatif à cette échelle : le
cas est court et son temps est dominé par les coûts fixes de session,
d'indexation et de groupes.

La stratégie adaptative ne lance aucun filtrage sur ces règles et ajoute
0,021 ms, soit 0,6 %, au semi-naïf. Les optimisations profondes restent
volontairement désactivées lorsque leur coût ne peut pas être amorti.

Les mesures sont conservées dans
[`results/constraint_propagation_2026-07-24.csv`](results/constraint_propagation_2026-07-24.csv).

### Construction incrémentale des domaines

Le benchmark Sudoku peut désactiver la persistance pour reproduire l'ancienne
reconstruction :

```sh
uv run python -m benchmarks.sudoku_rules \
    --levels 1 6 7 --repeat 7 --strategy domain-state
```

| Niveau | Reconstruction | Persistant | Lignes projetées avant | Après |
|---|---:|---:|---:|---:|
| p1 | 0,361 s | 0,356 s | 15 920 | 998 |
| p6 | 0,651 s | 0,639 s | 21 595 | 1 033 |
| p7 | 0,910 s | 0,899 s | 24 533 | 1 005 |

Les compteurs et réinitialisations par composante suppriment 93,7 à 95,9 %
des projections. Le gain temporel n'est pourtant que de 1 à 2 % : le coût de
construction est désormais faible devant les révisions de tables et la
jointure finale. Cette mesure ne justifie donc pas encore une représentation
bitset plus complexe.

Les données A/B sont dans
[`results/domain_state_2026-07-24.csv`](results/domain_state_2026-07-24.csv).

### Coût résiduel des rescans

Sur Sudoku p6, le filtrage forcé fournit un profil plus réaliste avec
ajouts, retraits et comparaisons :

| Variante | Médiane | Lignes d'entrée | Lignes examinées | Révisions |
|---|---:|---:|---:|---:|
| balayages complets | 0,721 s | 20 562 | 41 124 | 290 |
| file de propagateurs | 0,714 s | 20 562 | 21 701 | 174 |

La file supprime toujours 94,5 % des relectures de lignes : seulement 1 139
examens sur 21 701 ne correspondent pas au passage initial obligatoire.
Depuis que les comparaisons n'énumèrent plus leur produit cartésien, ce gain
structurel ne représente toutefois qu'environ 1 % du temps. Le profil suivant
a donc traité ensemble les supports et le travail redondant de la jointure.

### Compact-Tables et jointure directe

`compact_tables` compare trois chemins sur le même filtre :

```sh
uv run python -m benchmarks.compact_tables \
    --levels 1 6 7 --repeat 7
```

- `scanned` : ancien scan des lignes puis matcher compilé ;
- `bitset-filter` : supports `(variable, valeur)` et lignes actives en
  bitsets, mais ancienne jointure ;
- `compact` : mêmes bitsets, consommés directement par la jointure.

| Problème | Scan | Bitset seul | Compact complet | Gain |
|---|---:|---:|---:|---:|
| Sudoku p1 | 0,377 s | 0,358 s | 0,287 s | ×1,31 |
| Sudoku p6 | 0,656 s | 0,640 s | 0,576 s | ×1,14 |
| Sudoku p7 | 0,926 s | 0,907 s | 0,804 s | ×1,15 |
| arithmétique, taille 200 | 2,292 ms | 2,025 ms | 2,010 ms | ×1,14 |
| `NVALUE`, taille 200 | 2,302 ms | 2,062 ms | 2,061 ms | ×1,12 |
| `ALL_DIFFERENT`, taille 200 | 69,928 ms | 68,929 ms | 69,388 ms | ×1,01 |
| quatre reines adaptatif | 117,44 ms | 116,78 ms | 104,06 ms | ×1,13 |

Les rescans passent de 15 467, 18 187 et 21 588 lignes à zéro sur les trois
Sudoku. Le filtre traite seulement 346, 483 et 361 événements de retrait de
valeur. Le bitset seul apporte 2 à 5 % ; la majeure partie du gain vient de
la jointure directe, qui ne recherche ni ne rematche des lignes déjà
validées. `ALL_DIFFERENT` reste neutre parce qu'il doit produire 1 182
solutions : l'énumération réelle domine.

Les masques sont mis à jour avec `FactDelta`. Les compteurs de benchmark sont
`domain_bitset_value_events`, `domain_bitset_support_checks`,
`domain_bitset_intersections` et `domain_compact_join_rows`.
Les données A/B sont conservées dans
[`results/compact_tables_2026-07-24.csv`](results/compact_tables_2026-07-24.csv).

### Jointure delta et trail pré-backtracking

La jointure Compact applique désormais le delta jusqu'à l'énumération finale.
Elle construit une variante par prémisse ayant reçu une ligne nouvelle et
saute le join lorsqu'aucune table de la règle n'est concernée :

| Niveau | Matchings avant | Après | Réduction | Temps avant | Après | Gain |
|---|---:|---:|---:|---:|---:|---:|
| p1 | 63 946 | 49 531 | 22,5 % | 0,287 s | 0,254 s | ×1,13 |
| p6 | 138 846 | 126 198 | 9,1 % | 0,576 s | 0,534 s | ×1,08 |
| p7 | 216 643 | 195 160 | 9,9 % | 0,804 s | 0,731 s | ×1,10 |

Le sélecteur adaptatif peut également mesurer filtre et repli semi-naïf dans
les cas ambigus. La sonde est différée jusqu'à huit usages par défaut : le
cas favorable, qui retire 97,5 % des lignes, reste à 14,23 ms et ne paie
aucun chemin contre-factuel. Quatre reines effectue cinq reports et aucune
sonde ; sa médiane Compact est 106,8 ms. Les compteurs sont
`domain_cost_probes`, `domain_cost_probe_deferrals` et
`domain_cost_probe_rejections`.

Le benchmark de l'état réversible compare un trail local avec la copie de
tous les domaines :

```sh
uv run python -m benchmarks.propagation_trail \
    --variables 1000 --domain-size 9 --touched 3 \
    --iterations 200 --repeat 7
```

| État | Copie complète | Trail | Gain |
|---|---:|---:|---:|
| 1 000 domaines, 3 touchés | 30,706 ms | 1,103 ms | ×27,84 |

Les données sont dans
[`results/pre_backtracking_2026-07-24.csv`](results/pre_backtracking_2026-07-24.csv).

## Suite transversale des bases documentées

`rulebase_suite` vérifie les oracles de onze bases avec les stratégies indexée,
semi-naïve et adaptative :

```sh
uv run python -m benchmarks.rulebase_suite --repeat 7
```

Les scénarios incluent les contraintes globales, factorielle,
`COMBINATIONS`/`FOR EACH`, égalité, date, Petri, les deux singes/bananes,
MusES, quatre reines et Hanoï. Les
petites bases restent dans le matcher semi-naïf : leur volume ne permet pas
d'amortir la construction des domaines. Quatre reines active en revanche
deux règles filtrées, 21 révisions spécialisées et 240 vérifications de
valeurs. Sur les deux cas les plus longs :

| Base | Semi-naïve | Adaptative | Écart |
|---|---:|---:|---:|
| quatre reines | 160,46 ms | 104,06 ms | −35,1 % |
| Hanoï, 5 disques | 38,12 ms | 38,34 ms | +0,6 % |

Quatre reines constitue ainsi le premier gain sur une base métier existante :
l'adaptatif est ×1,54 plus rapide que le semi-naïf sans modifier les règles.
Hanoï, Fibonacci et les petits scénarios ne déclenchent aucun filtre ; leurs
écarts restent du bruit ou le faible coût du sélecteur. Les résultats complets
sont dans
[`results/rulebase_suite_2026-07-24.csv`](results/rulebase_suite_2026-07-24.csv).

### Passage à l'échelle et index structurels

`constraint_scaling` génère une chaîne d'égalité : la première variable est
singleton, toutes les autres commencent avec le domaine complet, et la
propagation doit retirer `(n - 1) × (d - 1)` candidats.

```sh
uv run python -m benchmarks.constraint_scaling \
    --variables 64 --domain-size 64 --repeat 5
```

Le commit `54d5196` sert de baseline A/B. Les deux versions utilisent le même
interpréteur, les mêmes règles et les mêmes faits :

| Variables × domaine | Avant | Maintenant | Gain | Matchings avant | Maintenant |
|---|---:|---:|---:|---:|---:|
| 64 × 24 | 0,732 s | 0,677 s | ×1,08 | 173 236 | 139 012 |
| 64 × 64 | 2,566 s | 1,684 s | ×1,52 | 560 196 | 310 212 |

À 64 × 64, les index de chemins structurés et l'ordre adaptatif retirent
44,6 % des matchings. Deux signatures seulement sont construites, pour les
deux orientations de `SEQ[left right]`; 7 937 décisions de jointure commencent
alors par le bucket le plus sélectif.

Le stockage conserve des rangs stables. À partir de 1 500 faits initiaux, la
séquence active devient un ensemble ordonné permettant les retraits directs ;
en dessous, une liste reste plus rapide. Les buckets top-level demeurent des
listes compactes. Ces seuils proviennent des mesures, pas de la sémantique.

### Témoins existentiels résiduels

Le benchmark suivant retire successivement 64 supports dans un domaine de
1 024 valeurs, dont une sur huit possède un support :

```sh
uv run python -m benchmarks.constraint_support_churn \
    --domain-size 1024 --support-stride 8 --steps 64 --repeat 7
```

| Variante | Médiane | Matchings | Invalidations | Promotions |
|---|---:|---:|---:|---:|
| Sans témoins alternatifs | 60,578 ms | 2 275 | 64 | 0 |
| Deux témoins résiduels | 56,991 ms | 1 253 | 32 | 32 |

Le gain vaut ×1,06 et la baisse de matchings 44,9 %. La mémoire reste bornée à
deux témoins par corrélation. Lorsqu'un support disparaît, l'alternative est
promue sans réévaluer le bloc.

Comme garde de non-régression, Sudoku conserve exactement ses matchings :
47 051 pour p1 et 106 449 pour p6. Dans l'A/B local, les médianes varient de
0,273 à 0,279 s pour p1 et de 0,504 à 0,513 s pour p6, soit un surcoût fixe de
2 % environ. Fibonacci `F(15)` conserve ses 9 125 matchings et varie de 0,439
à 0,450 s.

La série complète se trouve dans
[`results/constraint_indexing_optimizations_2026-07-24.csv`](results/constraint_indexing_optimizations_2026-07-24.csv).

## Agenda MEA incrémental

Le benchmark construit 200 règles indépendantes, initialise une activation par
règle, puis ajoute un fait qui ne peut concerner que la première. Il compare
une construction froide du conflit et la mise à jour d'une session chaude :

```sh
uv run python -m benchmarks.agenda_incremental --rules 200 --repeat 20
```

Mesure du 24 juillet 2026 sur macOS ARM64 avec Python 3.13.11 :

| Mise à jour | Médiane | Règles recalculées | Règles réutilisées |
|---|---:|---:|---:|
| Construction froide | 2,206 ms | 200 | 0 |
| Delta ciblé | 0,572 ms | 1 | 199 |

Le gain temporel est ×3,86 et la réduction algorithmique du recalcul vaut
×200. MEA parcourt encore tous les candidats pour les comparer : le benchmark
isole donc le gain de matching, pas une modification de sa politique.
Les données sont conservées dans
[`results/agenda_incremental_2026-07-24.csv`](results/agenda_incremental_2026-07-24.csv).

## Sudoku déclaratif

Le benchmark Sudoku mesure par défaut les niveaux p1, p6 et p7 cinq fois avec
les stratégies indexée, semi-naïve et adaptative :

```sh
uv run python -m benchmarks.sudoku_rules --levels 1 6 7 --repeat 5
```

Mesure du 23 juillet 2026 sur macOS ARM64 avec Python 3.13.11, après la
séquence complète : plans compilés, cadre mutable, deltas de suppression,
watchers et compteurs négatifs, mémoires de jointure bornées et agrégats :

| Niveau | Médiane | Matchings | Avant cette séquence | Matchings précédents |
|---|---:|---:|---:|---:|
| p1 | 0,323 s | 47 051 | 0,523 s | 69 793 |
| p5 | 0,720 s | 125 298 | 1,504 s | 217 880 |
| p6 | 0,639 s | 106 449 | 1,462 s | 210 908 |

Cette passe ajoute un gain ×1,62 à ×2,29 et réduit encore les matchings de
33 à 50 %. Depuis la baseline initiale, le gain total vaut ×7,18 sur p1,
×8,26 sur p5 et ×8,74 sur p6. Les résultats synthétiques sont conservés dans
[`results/sudoku_matching_optimizations_2026-07-23.csv`](results/sudoku_matching_optimizations_2026-07-23.csv).

X-Wing p7, ajouté le 24 juillet 2026, prend 0,659 s en médiane sur trois
passages, avec 171 804 tentatives de matching et 490 activations. Cette mesure
est un point de départ pour le niveau avancé, pas une comparaison avant/après.

### Propagateurs de comparaison

Une mesure A/B force le filtre de domaines avec, d'une part, l'ancien produit
cartésien générique et, d'autre part, les propagateurs spécialisés de `!=` et
des ordres numériques :

```sh
uv run python -m benchmarks.sudoku_rules \
    --levels 1 6 7 --repeat 7 --strategy comparisons
```

| Niveau | Filtre générique | Filtre spécialisé | Gain |
|---|---:|---:|---:|
| p1 | 0,426 s | 0,366 s | ×1,17 |
| p6 | 0,743 s | 0,656 s | ×1,13 |
| p7 | 0,978 s | 0,924 s | ×1,06 |

Les vérifications spécialisées remplacent respectivement 36 126, 48 762 et
33 210 combinaisons cartésiennes. En sélection adaptative, p1 passe de
0,395 s en semi-naïf à 0,355 s, soit −10,2 %. Sur p6 et p7, le filtre reste
respectivement 3,4 et 0,25 % plus lent que le semi-naïf ; la stratégie indexée
reste donc le choix par défaut. Le profil montre que ni les comparaisons ni la
projection initiale ne sont plus leur goulot d'étranglement.

Les mesures détaillées sont conservées dans
[`results/comparison_propagators_2026-07-24.csv`](results/comparison_propagators_2026-07-24.csv).

### Hashes structurels précalculés

Mesure du 24 juillet 2026, sur la même machine et avec sept passages par
niveau. `Atom`, `Number`, `Variable`, `Triple` et `Fact` conservent désormais
leur hash structurel calculé une seule fois à la construction :

| Niveau | Avant le cache | Après le cache | Gain | Matchings |
|---|---:|---:|---:|---:|
| p1 | 0,325 s | 0,247 s | ×1,32 | 47 051 |
| p5 | 0,728 s | 0,535 s | ×1,36 | 125 298 |
| p6 | 0,639 s | 0,468 s | ×1,37 | 106 449 |

La baisse temporelle vaut 24 à 27 % sans aucun changement du travail logique.
Depuis la baseline Sudoku initiale, le gain total atteint ×9,38 sur p1,
×11,11 sur p5 et ×11,94 sur p6. Après p5, les slots de hash des objets encore
vivants représentent environ 46,6 Ko supplémentaires.

Le même changement est plus sensible sur Fibonacci, qui manipule beaucoup de
faits récursifs : `F(15)` semi-naïf passe de 6,084 s à 0,953 s en médiane,
soit un gain ×6,39, avec les mêmes 9 125 tentatives de matching. Les mesures
A/B sont conservées dans
[`results/hash_cache_optimizations_2026-07-24.csv`](results/hash_cache_optimizations_2026-07-24.csv).

## Fibonacci explicite — état courant

Mesure fraîche du 24 juillet 2026 avec Python 3.13.11 sur macOS ARM64, après
compilation des plans de réfraction négative par groupe. Une session dont
aucune règle n’a de dépendance négative ne lance désormais aucune
réconciliation après les ajouts :

| Rang | Avant | État courant | Gain | Passages | Faits | Matchings |
|---:|---:|---:|---:|---:|---:|---:|
| 15 | 0,919 s | 0,338 s | ×2,72 | 5 | 3 656 | 9 125 |
| 16 | 2,238 s | 0,614 s | ×3,64 | 5 | 5 918 | 14 792 |
| 17 | 6,248 s | 1,206 s | ×5,18 | 5 | 9 578 | 23 928 |
| 18 | 18,896 s | 2,330 s | ×8,11 | 5 | 15 500 | 38 747 |
| 19 | 53,603 s | 4,618 s | ×11,61 | 5 | 25 082 | 62 686 |
| 20 | — | 8,791 s | — | 3 | 40 586 | 101 462 |
| 21 | — | 12,309 s | — | 1 | 65 672 | 164 159 |

Les faits, activations et tentatives de matching restent identiques : le gain
vient uniquement de la suppression d’un balayage inutile des activations déjà
tirées. Dans le profil instrumenté de `F(17)`,
`_reconcile_negative_refraction` occupait 12,923 s sur 17,489 s avant le
correctif ; elle disparaît du profil après celui-ci, dont le temps total tombe
de 17,2 s à 4,0 s.

Sur cette machine, `F(20)` devient la limite interactive sous 10 secondes et
`F(21)` reste raisonnable sous 30 secondes. `F(22)` matérialiserait environ
106 000 faits et dépasserait donc la garde par défaut de 100 000 faits. La
base construit volontairement tout l’arbre récursif sans mémoïsation : sa
taille reste exponentielle.

La série complète est conservée dans
[`results/fibonacci_explicit_current_2026-07-24.csv`](results/fibonacci_explicit_current_2026-07-24.csv).
La comparaison avant/après est conservée dans
[`results/negative_refraction_fast_path_2026-07-24.csv`](results/negative_refraction_fast_path_2026-07-24.csv).
Elle se reproduit en une commande avec le mode de plage inclusive :

```sh
uv run python benchmarks/fibonacci_explicit.py \
    --range 15 21 --repeat 3 --strategy semi-naive
```

`--n 17` conserve le format JSON historique d’un cas unique. Avec `--range`,
la sortie contient une liste `cases` ordonnée par rang.

### Comparaison historique avec NéOpus

La thèse décrivant NéOpus rapporte en 1992 le même benchmark à trois règles
sur une architecture RETE en Smalltalk. La charge logique est directement
comparable : `F(10)` crée 109 objets et déclenche 163 règles dans NéOpus,
contre 109 nœuds et 163 activations dans Snarky ; pour `F(15)`, les deux
valeurs sont respectivement 1 219 et 1 828.

Sur Macintosh FX, NéOpus annonçait au plus 1,2 s pour `F(10)` et 57 s pour
`F(15)` ; sur Sparc 1, 0,8 s et 45 s. Une mesure Snarky dédiée de dix passages
sur le MacBook Pro M1 Pro donne des médianes de 0,0214 s et 0,346 s. Les
rapports bruts mélangent matériel, langage et architecture et ne constituent
donc pas un classement algorithmique.

La croissance interne est plus instructive : de `F(10)` à `F(15)`, la charge
logique est multipliée par environ 11,2, le temps Snarky par 16,2, et le temps
NéOpus par 47,5 sur Macintosh FX ou 56,3 sur Sparc 1. Le coût Snarky par
activation ne croît que de ×1,44, contre ×4,24 à ×5,02 pour NéOpus. La thèse
attribue justement une part importante du coût RETE de NéOpus à la
manipulation des listes de tokens. Fibonacci réutilise peu de jointures
partielles et favorise ainsi l’indexation semi-naïve ; cette observation ne
préjuge pas des charges où RETE amortit mieux ses mémoires.

La source présente 57 s dans le texte et 55 s dans son tableau récapitulatif ;
la comparaison ci-dessus retient la valeur textuelle. Voir
[`pachet-92b.pdf`, sections V.1.2.1 et V.1.4](https://www.francoispachet.fr/wp-content/uploads/2021/01/pachet-92b.pdf#page=92).

## Fibonacci explicite — séries historiques

Les sous-sections suivantes conservent les mesures du 22 juillet 2026,
obtenues à des étapes antérieures du moteur. Elles documentent les gains
successifs de l’indexation et de l’évaluation semi-naïve, mais ne constituent
pas une mesure du snapshot courant. Pour celui-ci, la série `F(15)` à `F(21)`
présentée juste au-dessus est la référence.

La commande suivante calcule trois fois `F(10)` avec l'oracle naïf, la stratégie
indexée exhaustive, la stratégie semi-naïve puis la stratégie adaptative :

```sh
uv run python benchmarks/fibonacci_explicit.py \
    --n 10 --repeat 3 --strategy all
```

Le scénario construit l'arbre récursif complet, sans mémoïsation. Pour
`F(10)`, les deux stratégies obtiennent exactement :

- `F(10) = 55` ;
- 109 nœuds de calcul ;
- 325 faits dérivés et 326 faits au point fixe ;
- 163 activations déclenchées en 17 cycles.

Mesure du 22 juillet 2026 sur macOS ARM64, avec Python 3.13.11 :

| Stratégie | Temps moyen | Tentatives de matching | Gain temporel |
|---|---:|---:|---:|
| Naïve | 7,142 s | 557 302 | référence |
| Indexée persistante | 0,167 s | 8 963 | ×42,7 |
| Semi-naïve | 0,053 s | 1 369 | ×136,0 |

La stratégie semi-naïve produit exactement les 163 activations qui seront
déclenchées, contre 1 782 auparavant. Les temps dépendent de la machine ; les
compteurs algorithmiques sont les mesures les plus stables.

Pour ne mesurer que la stratégie indexée :

```sh
uv run python benchmarks/fibonacci_explicit.py \
    --n 10 --repeat 5 --strategy indexed
```

### Limite pratique initiale

Cette série constitue la baseline de la première stratégie indexée avec
arithmétique native `LET`. La mesure de `F(10)` est la moyenne de trois
passages ; les rangs suivants sont
des passages uniques destinés à situer la limite pratique. Ils ont été mesurés
dans le même environnement que le tableau précédent.

| Rang | Résultat | Temps | Faits | Activations produites | Matchings tentés |
|---:|---:|---:|---:|---:|---:|
| 10 | 55 | 0,245 s | 326 | 1 782 | 8 963 |
| 11 | 89 | 0,494 s | 530 | 3 233 | 16 305 |
| 12 | 144 | 0,991 s | 860 | 5 792 | 29 234 |
| 13 | 233 | 1,972 s | 1 394 | 10 275 | 51 908 |
| 14 | 377 | 3,918 s | 2 258 | 18 081 | 91 338 |
| 15 | 610 | 7,738 s | 3 656 | 31 605 | 159 687 |
| 16 | 987 | 14,648 s | 5 918 | 54 932 | 277 458 |
| 17 | 1 597 | 27,914 s | 9 578 | 95 013 | 479 862 |

Avec une limite interactive de 10 secondes, `F(15)` est confortable. Avec une
limite de 30 secondes, `F(17)` est le dernier rang raisonnable observé. Comme
la base construit l'arbre complet sans mémoïsation, le nombre de nœuds vaut
`2 × F(n) - 1` et la croissance reste exponentielle.

Les données complètes sont conservées dans
[`results/fibonacci_explicit_native_arithmetic_baseline_2026-07-22.csv`](results/fibonacci_explicit_native_arithmetic_baseline_2026-07-22.csv).

### Index persistant et évaluation semi-naïve

La deuxième série mesure `SemiNaiveInstantiationStrategy`. Chaque règle
conserve son index entre les cycles et ne joint que les combinaisons contenant
au moins un fait nouveau depuis sa propre évaluation précédente. Les variantes
delta sont dédupliquées et triées dans l'ordre observable du moteur naïf.

| Rang | Résultat | Temps | Faits | Activations produites | Matchings tentés |
|---:|---:|---:|---:|---:|---:|
| 10 | 55 | 0,053 s | 326 | 163 | 1 369 |
| 11 | 89 | 0,097 s | 530 | 265 | 2 248 |
| 12 | 144 | 0,181 s | 860 | 430 | 3 683 |
| 13 | 233 | 0,318 s | 1 394 | 697 | 5 999 |
| 14 | 377 | 0,576 s | 2 258 | 1 129 | 9 782 |
| 15 | 610 | 1,053 s | 3 656 | 1 828 | 15 867 |
| 16 | 987 | 1,884 s | 5 918 | 2 959 | 25 815 |
| 17 | 1 597 | 3,338 s | 9 578 | 4 789 | 41 789 |
| 18 | 2 584 | 5,770 s | 15 500 | 7 750 | 67 900 |
| 19 | 4 181 | 10,871 s | 25 082 | 12 541 | 109 820 |
| 20 | 6 765 | 19,905 s | 40 586 | 20 293 | 178 274 |
| 21 | 10 946 | 32,042 s | 65 672 | 32 836 | 288 252 |

Sur `F(17)`, le temps passe de 27,914 s à 3,338 s, soit un gain ×8,4 par
rapport à la première baseline indexée. Les activations produites passent de
95 013 à 4 789 et les tentatives de matching de 479 862 à 41 789. Le seuil de
10 secondes avance de `F(15)` à `F(18)` et celui de 30 secondes de `F(17)` à
`F(20)`.

Les mesures complètes sont conservées dans
[`results/fibonacci_explicit_semi_naive_2026-07-22.csv`](results/fibonacci_explicit_semi_naive_2026-07-22.csv).

### Protocole de comparaison des optimisations

Après chaque phase, rejouer au minimum les rangs 10 à 20 avec la même version
de Python et consigner :

1. le temps d'exécution et le nombre de faits au point fixe ;
2. les activations produites et effectivement déclenchées ;
3. les tentatives de matching et les constructions d'index ;
4. l'égalité des faits et dérivations avec l'oracle naïf sur les petits rangs ;
5. le plus grand rang terminé en moins de 10 puis de 30 secondes.

Les optimisations seront comparées prioritairement sur les compteurs
algorithmiques. Les temps seront interprétés comme une mesure secondaire,
sensible à la machine et à la charge du système.
