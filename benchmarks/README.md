# Benchmarks Snarky

Les benchmarks sont des programmes reproductibles séparés des tests de
correction. Ils produisent du JSON afin de pouvoir comparer plusieurs
versions du moteur.

## Sudoku déclaratif

Le benchmark Sudoku mesure les niveaux p1, p5 et p6 cinq fois avec la stratégie
indexée exhaustive utilisée par le solveur :

```sh
uv run python -m benchmarks.sudoku_rules --levels 1 5 6 --repeat 5
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
indexée exhaustive, puis la stratégie semi-naïve :

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
