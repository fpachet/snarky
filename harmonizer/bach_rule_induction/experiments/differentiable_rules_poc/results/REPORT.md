# Résultats du POC différentiable

## Périmètre

- 352 chorals historiques analysés, 20350 décisions de soprano.
- Train : 246 pièces / 14436 décisions.
- Validation : 53 pièces / 3029 décisions.
- Le test final n'a pas été ouvert.
- Données authentiques, sans mélange des choix.

## Modèle

- Clauses ajustées conjointement : 56.
- Clauses actives (`|poids| >= 0.05`) : 52.
- L1 choisie sur validation : `0.001`.
- NLL uniforme : `3.091042`.
- NLL train : `1.998649`.
- NLL validation : `1.970562`.
- `LEARNED_PREDICATE_001` a été admis après détection des deux branches symétriques.

## Règles actives les plus fortes

| # | Modalité | Poids | Train obs./disp. | Validation obs./disp. | Clause |
|---:|---|---:|---:|---:|---|
| 1 | AVOID | -3.198 | 0.000 / 0.053 | 0.000 / 0.048 | `abs(prev_s-prev_b)%12 == 11 AND abs(candidate_s-current_b)%12 == 11 AND LEARNED_PREDICATE_001 == true` |
| 2 | AVOID | -2.837 | 0.000 / 0.045 | 0.000 / 0.045 | `abs(prev_s-prev_b)%12 == 1 AND abs(candidate_s-current_b)%12 == 1 AND LEARNED_PREDICATE_001 == true` |
| 3 | FORBID_CANDIDATE | -2.741 | 0.003 / 0.050 | 0.002 / 0.051 | `abs(prev_s-prev_b)%12 == 7 AND abs(candidate_s-current_b)%12 == 7 AND LEARNED_PREDICATE_001 == true` |
| 4 | FORBID_CANDIDATE | -2.725 | 0.004 / 0.051 | 0.000 / 0.049 | `abs(prev_s-prev_b)%12 == 10 AND abs(candidate_s-current_b)%12 == 10 AND LEARNED_PREDICATE_001 == true` |
| 5 | FORBID_CANDIDATE | -2.658 | 0.004 / 0.051 | 0.000 / 0.050 | `abs(prev_s-prev_b)%12 == 0 AND abs(candidate_s-current_b)%12 == 0 AND LEARNED_PREDICATE_001 == true` |
| 6 | FORBID_CANDIDATE | -2.585 | 0.005 / 0.056 | 0.012 / 0.057 | `abs(prev_s-prev_b)%12 == 6 AND abs(candidate_s-current_b)%12 == 6 AND LEARNED_PREDICATE_001 == true` |
| 7 | FORBID_CANDIDATE | -2.041 | 0.000 / 0.047 | 0.000 / 0.047 | `abs(candidate_s-current_b)%12 == 11 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 8 | FORBID_CANDIDATE | -2.000 | 0.000 / 0.047 | 0.001 / 0.047 | `abs(candidate_s-current_b)%12 == 10 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 9 | AVOID | -1.980 | 0.012 / 0.053 | 0.000 / 0.055 | `abs(prev_s-prev_b)%12 == 5 AND abs(candidate_s-current_b)%12 == 5 AND LEARNED_PREDICATE_001 == true` |
| 10 | FORBID_CANDIDATE | -1.939 | 0.000 / 0.047 | 0.000 / 0.047 | `abs(candidate_s-current_b)%12 == 1 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 11 | FORBID_CANDIDATE | -1.822 | 0.000 / 0.048 | 0.001 / 0.047 | `abs(candidate_s-current_b)%12 == 5 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 12 | FORBID_CANDIDATE | -1.512 | 0.002 / 0.047 | 0.002 / 0.047 | `abs(candidate_s-current_b)%12 == 6 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 13 | FORBID_CANDIDATE | -1.441 | 0.002 / 0.047 | 0.002 / 0.047 | `abs(candidate_s-current_b)%12 == 2 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 14 | AVOID | -1.183 | 0.023 / 0.049 | 0.023 / 0.054 | `abs(prev_s-prev_b)%12 == 2 AND abs(candidate_s-current_b)%12 == 2 AND LEARNED_PREDICATE_001 == true` |
| 15 | AVOID | -1.141 | 0.152 / 0.773 | 0.146 / 0.773 | `sign(current_b-prev_b) == zero AND abs(candidate_s-prev_s) > 2` |
| 16 | FORBID_CANDIDATE | -0.962 | 0.005 / 0.344 | 0.003 / 0.343 | `sign(current_b-prev_b) == positive AND abs(candidate_s-prev_s) > 7` |
| 17 | AVOID | -0.921 | 0.078 / 0.389 | 0.077 / 0.380 | `sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 2` |
| 18 | FORBID_CANDIDATE | -0.915 | 0.006 / 0.222 | 0.005 / 0.214 | `sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 7` |
| 19 | FORBID_CANDIDATE | -0.907 | 0.007 / 0.344 | 0.006 / 0.343 | `abs(candidate_s-prev_s) > 7` |
| 20 | FORBID_CANDIDATE | -0.900 | 0.002 / 0.226 | 0.002 / 0.229 | `sign(candidate_s-prev_s) == negative AND abs(candidate_s-prev_s) > 7` |
| 21 | PREFER | 0.895 | 0.025 / 0.047 | 0.022 / 0.047 | `abs(candidate_s-current_b)%12 == 3 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 22 | AVOID | -0.887 | 0.035 / 0.391 | 0.022 / 0.400 | `sign(candidate_s-prev_s) == negative AND sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 2` |
| 23 | PREFER | 0.871 | 0.326 / 0.045 | 0.341 / 0.045 | `abs(candidate_s-current_b)%12 == 7 AND sign(candidate_s-prev_s) == zero` |
| 24 | PREFER | 0.861 | 0.021 / 0.047 | 0.016 / 0.047 | `abs(candidate_s-current_b)%12 == 4 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 25 | PREFER | 0.844 | 0.302 / 0.773 | 0.272 / 0.773 | `abs(prev_s-prev_b)%12 == 0 AND abs(candidate_s-prev_s) > 2` |
| 26 | PREFER | 0.785 | 0.422 / 0.045 | 0.429 / 0.045 | `abs(candidate_s-current_b)%12 == 7 AND sign(candidate_s-prev_s) == zero AND sign(current_b-prev_b) == positive` |
| 27 | AVOID | -0.748 | 0.073 / 0.773 | 0.046 / 0.773 | `abs(prev_s-prev_b)%12 == 9 AND abs(candidate_s-prev_s) > 2` |
| 28 | AVOID | -0.745 | 0.109 / 0.773 | 0.092 / 0.773 | `sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 2` |
| 29 | AVOID | -0.739 | 0.149 / 0.773 | 0.139 / 0.773 | `abs(candidate_s-prev_s) > 2` |
| 30 | FORBID_CANDIDATE | -0.733 | 0.006 / 0.046 | 0.004 / 0.046 | `abs(candidate_s-current_b)%12 == 9 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |

Les deux taux sont calculés seulement dans les opportunités où la
propriété et son complément sont tous deux disponibles.

## Abstractions symétriques proposées après apprentissage

### Abstraction 1

- Conditions communes : `abs(candidate_s-prev_s) > 2`
- z montée/montée : `-52.187` ; z descente/descente : `-59.062`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 2

- Conditions communes : `abs(candidate_s-prev_s) > 4`
- z montée/montée : `-44.685` ; z descente/descente : `-51.077`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 3

- Conditions communes : `abs(candidate_s-prev_s) > 7`
- z montée/montée : `-36.802` ; z descente/descente : `-37.277`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 4

- Conditions communes : `abs(candidate_s-prev_s) > 1`
- z montée/montée : `-32.204` ; z descente/descente : `-21.480`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 5

- Conditions communes : `abs(prev_s-prev_b)%12 == 0 AND abs(candidate_s-prev_s) > 2`
- z montée/montée : `-16.837` ; z descente/descente : `-17.680`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 6

- Conditions communes : `abs(prev_s-prev_b)%12 == 0`
- z montée/montée : `-16.687` ; z descente/descente : `-16.258`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 7

- Conditions communes : `abs(candidate_s-current_b)%12 == 1`
- z montée/montée : `-15.540` ; z descente/descente : `-16.006`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 8

- Conditions communes : `abs(prev_s-prev_b)%12 == 0 AND abs(candidate_s-prev_s) > 4`
- z montée/montée : `-17.100` ; z descente/descente : `-15.181`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 9

- Conditions communes : `abs(candidate_s-prev_s) > 12`
- z montée/montée : `-15.927` ; z descente/descente : `-15.115`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 10

- Conditions communes : `abs(candidate_s-current_b)%12 == 11 AND abs(candidate_s-prev_s) > 1`
- z montée/montée : `-15.313` ; z descente/descente : `-14.727`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 11

- Conditions communes : `abs(candidate_s-current_b)%12 == 1 AND abs(candidate_s-prev_s) > 1`
- z montée/montée : `-14.816` ; z descente/descente : `-14.448`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 12

- Conditions communes : `abs(candidate_s-current_b)%12 == 11 AND abs(candidate_s-prev_s) > 2`
- z montée/montée : `-14.896` ; z descente/descente : `-14.397`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 13

- Conditions communes : `abs(candidate_s-current_b)%12 == 1 AND abs(candidate_s-prev_s) > 2`
- z montée/montée : `-14.312` ; z descente/descente : `-14.264`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 14

- Conditions communes : `abs(candidate_s-current_b)%12 == 10 AND abs(candidate_s-prev_s) > 2`
- z montée/montée : `-14.996` ; z descente/descente : `-14.262`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 15

- Conditions communes : `abs(candidate_s-current_b)%12 == 5 AND abs(candidate_s-prev_s) > 2`
- z montée/montée : `-14.672` ; z descente/descente : `-14.125`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 16

- Conditions communes : `abs(candidate_s-current_b)%12 == 2 AND abs(candidate_s-prev_s) > 2`
- z montée/montée : `-14.344` ; z descente/descente : `-13.686`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 17

- Conditions communes : `abs(candidate_s-current_b)%12 == 2`
- z montée/montée : `-15.046` ; z descente/descente : `-13.667`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 18

- Conditions communes : `abs(prev_s-prev_b)%12 == 0 AND abs(candidate_s-prev_s) > 1`
- z montée/montée : `-13.663` ; z descente/descente : `-16.731`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 19

- Conditions communes : `abs(candidate_s-current_b)%12 == 6`
- z montée/montée : `-13.593` ; z descente/descente : `-13.850`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 20

- Conditions communes : `abs(candidate_s-current_b)%12 == 2 AND abs(candidate_s-prev_s) > 1`
- z montée/montée : `-14.472` ; z descente/descente : `-13.462`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

## Scan aveugle des douze classes numériques

Ce scan est effectué seulement après que les deux branches de signe
commun ont suggéré une abstraction symétrique. Les classes restent
désignées par les nombres `0..11`.

| Classe | Répétition même signe z train | z validation | Arrivée après saut z train | z validation |
|---:|---:|---:|---:|---:|
| 0 | -8.907 | -4.410 | -18.335 | -8.715 |
| 1 | -0.900 | -0.309 | -20.206 | -9.319 |
| 2 | -1.786 | -0.915 | -19.818 | -9.226 |
| 3 | 26.909 | 12.213 | -9.335 | -5.010 |
| 4 | 4.854 | 1.585 | -11.190 | -6.202 |
| 5 | -2.835 | -1.661 | -20.366 | -9.333 |
| 6 | -4.685 | -1.732 | -19.281 | -8.854 |
| 7 | -9.952 | -4.715 | -14.804 | -7.444 |
| 8 | 7.937 | 0.876 | -15.171 | -5.662 |
| 9 | 5.404 | 6.175 | -17.280 | -8.186 |
| 10 | -3.282 | -1.737 | -20.695 | -9.396 |
| 11 | -2.072 | -0.928 | -20.717 | -9.555 |
## Limites

- Cette première expérience ne modélise que les choix de soprano avec
  le mouvement de basse comme contexte.
- Les candidates sont équiprobables avant application des règles ;
  l'ambitus est la seule faisabilité préimposée.
- Une clause extrême est une hypothèse empirique, pas encore une règle
  normative.
- La compression symétrique est postérieure au gradient et doit être
  confirmée par stabilité et par comparaison à des contrôles nuls.
- Le test scellé ne sera ouvert qu'après gel du vocabulaire et des
  hyperparamètres.
