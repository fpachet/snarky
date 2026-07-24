# Benchmarks Snarky

Les benchmarks sont des programmes reproductibles séparés des tests de
correction. Ils produisent du JSON afin de pouvoir comparer plusieurs
versions du moteur.

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
| indexée | 339,20 ms | 160 400 | — |
| domaines, produit cartésien | 80,69 ms | 6 | 40 001 combinaisons |
| domaines, propagateur spécialisé | 2,06 ms | 6 | 201 vérifications |
| adaptative | 2,04 ms | 6 | 201 vérifications |

Le propagateur choisit entre les paires `(left, right)`, `(left, total)` et
`(right, total)`. Comme `total` est singleton, il effectue un parcours
linéaire au lieu d'énumérer le produit des trois domaines. L'état persistant
évite aussi la seconde propagation identique. Le gain vaut ×39,2 entre filtre
générique et spécialisé, et ×166,3 entre indexé et adaptatif.

Les résultats sont conservés dans
[`results/arithmetic_constraints_2026-07-24.csv`](results/arithmetic_constraints_2026-07-24.csv).

## Contraintes globales

`global_constraints` mesure `NVALUE` puis `ALL_DIFFERENT` :

```sh
uv run python -m benchmarks.global_constraints --size 200 --repeat 7
```

| Scénario | Indexée | Domaines reconstruits | Domaines persistants | Adaptative |
|---|---:|---:|---:|---:|
| `NVALUE`, N = 1 | 406,58 ms | 2,85 ms | 2,12 ms | 2,10 ms |
| `ALL_DIFFERENT`, Hall triple | 65,54 ms | 68,28 ms | 67,70 ms | 43,54 ms |

Sur `NVALUE`, le filtre ramène 160 402 tentatives de matching à 8 et
l'adaptatif gagne ×193,9. La persistance réduit les 1 206 lignes projetées
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
structurel ne représente toutefois qu'environ 1 % du temps. Des compteurs de
supports AC-4/AC-6 ajouteraient donc plus de complexité qu'ils ne peuvent
actuellement en économiser.

## Suite transversale des bases documentées

`rulebase_suite` vérifie les oracles de onze bases avec les stratégies indexée,
semi-naïve et adaptative :

```sh
uv run python -m benchmarks.rulebase_suite --repeat 9
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
| quatre reines | 161,49 ms | 116,73 ms | −27,7 % |
| Hanoï, 5 disques | 37,19 ms | 39,07 ms | +5,1 % |

Quatre reines constitue ainsi le premier gain sur une base métier existante :
l'adaptatif est ×1,38 plus rapide que le semi-naïf sans modifier les règles.
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
