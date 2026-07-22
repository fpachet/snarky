# Benchmarks Snarky

Les benchmarks sont des programmes reproductibles séparés des tests de
correction. Ils produisent du JSON afin de pouvoir comparer plusieurs
versions du moteur.

## Fibonacci explicite

La commande suivante calcule trois fois `F(10)` avec l'oracle naïf, puis avec
la stratégie indexée :

```sh
uv run python benchmarks/fibonacci_explicit.py \
    --n 10 --repeat 3 --strategy both
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
| Naïve | 7,243 s | 557 302 | référence |
| Indexée | 0,245 s | 8 963 | ×29,6 |

L'indexation divise donc le nombre de faits présentés au matcher par environ
62,2. Les temps dépendent de la machine ; les compteurs algorithmiques sont
les mesures les plus stables.

Pour ne mesurer que la stratégie indexée :

```sh
uv run python benchmarks/fibonacci_explicit.py \
    --n 10 --repeat 5 --strategy indexed
```

## Limite pratique initiale

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

## Protocole de comparaison des optimisations

Après chaque phase, rejouer au minimum les rangs 10 à 17 avec la même version
de Python et consigner :

1. le temps d'exécution et le nombre de faits au point fixe ;
2. les activations produites et effectivement déclenchées ;
3. les tentatives de matching et les constructions d'index ;
4. l'égalité des faits et dérivations avec l'oracle naïf sur les petits rangs ;
5. le plus grand rang terminé en moins de 10 puis de 30 secondes.

Les optimisations seront comparées prioritairement sur les compteurs
algorithmiques. Les temps seront interprétés comme une mesure secondaire,
sensible à la machine et à la charge du système.
