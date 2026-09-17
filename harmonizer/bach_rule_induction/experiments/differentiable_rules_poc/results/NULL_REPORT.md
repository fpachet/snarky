# Résultats du POC différentiable

## Périmètre

- 352 chorals historiques analysés, 20350 décisions de soprano.
- Train : 246 pièces / 14436 décisions.
- Validation : 53 pièces / 3029 décisions.
- Le test final n'a pas été ouvert.
- Contrôle nul : les choix de soprano ont été mélangés dans chaque pièce.

## Modèle

- Clauses ajustées conjointement : 56.
- Clauses actives (`|poids| >= 0.05`) : 50.
- L1 choisie sur validation : `0.001`.
- NLL uniforme : `3.091042`.
- NLL train : `2.731029`.
- NLL validation : `2.697298`.
- `LEARNED_PREDICATE_001` a été admis après détection des deux branches symétriques.

## Règles actives les plus fortes

| # | Modalité | Poids | Train obs./disp. | Validation obs./disp. | Clause |
|---:|---|---:|---:|---:|---|
| 1 | AVOID | -2.159 | 0.000 / 0.045 | 0.000 / 0.045 | `abs(prev_s-prev_b)%12 == 1 AND abs(candidate_s-current_b)%12 == 1 AND LEARNED_PREDICATE_001 == true` |
| 2 | FORBID_CANDIDATE | -1.620 | 0.003 / 0.133 | 0.003 / 0.130 | `abs(candidate_s-prev_s) > 12` |
| 3 | AVOID | -1.340 | 0.014 / 0.056 | 0.000 / 0.057 | `abs(prev_s-prev_b)%12 == 6 AND abs(candidate_s-current_b)%12 == 6 AND LEARNED_PREDICATE_001 == true` |
| 4 | AVOID | -1.156 | 0.026 / 0.053 | 0.000 / 0.048 | `abs(prev_s-prev_b)%12 == 11 AND abs(candidate_s-current_b)%12 == 11 AND LEARNED_PREDICATE_001 == true` |
| 5 | PREFER | 1.012 | 0.173 / 0.045 | 0.180 / 0.045 | `sign(candidate_s-prev_s) == zero` |
| 6 | AVOID | -0.924 | 0.012 / 0.047 | 0.013 / 0.047 | `abs(candidate_s-current_b)%12 == 1 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 7 | PREFER | 0.811 | 0.737 / 0.864 | 0.731 / 0.864 | `abs(candidate_s-prev_s) > 1` |
| 8 | AVOID | -0.798 | 0.015 / 0.047 | 0.010 / 0.047 | `abs(candidate_s-current_b)%12 == 6 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 9 | AVOID | -0.591 | 0.032 / 0.052 | 0.030 / 0.052 | `abs(prev_s-prev_b)%12 == 8 AND abs(candidate_s-current_b)%12 == 8 AND LEARNED_PREDICATE_001 == true` |
| 10 | AVOID | -0.538 | 0.047 / 0.222 | 0.040 / 0.214 | `sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 7` |
| 11 | AVOID | -0.512 | 0.019 / 0.047 | 0.025 / 0.047 | `abs(candidate_s-current_b)%12 == 11 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 12 | AVOID | -0.490 | 0.073 / 0.344 | 0.057 / 0.343 | `abs(candidate_s-prev_s) > 7` |
| 13 | PREFER | 0.475 | 0.058 / 0.047 | 0.051 / 0.047 | `abs(candidate_s-current_b)%12 == 7 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 14 | AVOID | -0.444 | 0.020 / 0.047 | 0.020 / 0.046 | `abs(candidate_s-current_b)%12 == 8 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 15 | AVOID | -0.438 | 0.049 / 0.226 | 0.035 / 0.229 | `sign(candidate_s-prev_s) == negative AND abs(candidate_s-prev_s) > 7` |
| 16 | PREFER | 0.414 | 0.051 / 0.048 | 0.043 / 0.047 | `abs(candidate_s-current_b)%12 == 5 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 17 | AVOID | -0.306 | 0.262 / 0.389 | 0.258 / 0.380 | `sign(candidate_s-prev_s) == positive AND abs(candidate_s-prev_s) > 2` |
| 18 | AVOID | -0.297 | 0.526 / 0.773 | 0.514 / 0.773 | `abs(candidate_s-prev_s) > 2` |
| 19 | PREFER | 0.292 | 0.178 / 0.045 | 0.174 / 0.045 | `sign(candidate_s-prev_s) == zero AND sign(current_b-prev_b) == positive` |
| 20 | AVOID | -0.289 | 0.072 / 0.344 | 0.057 / 0.343 | `sign(current_b-prev_b) == positive AND abs(candidate_s-prev_s) > 7` |
| 21 | AVOID | -0.286 | 0.024 / 0.047 | 0.028 / 0.047 | `abs(candidate_s-current_b)%12 == 4 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 22 | AVOID | -0.286 | 0.271 / 0.395 | 0.261 / 0.402 | `sign(candidate_s-prev_s) == negative AND abs(candidate_s-prev_s) > 2` |
| 23 | PREFER | 0.254 | 0.042 / 0.047 | 0.043 / 0.047 | `abs(candidate_s-current_b)%12 == 0 AND abs(candidate_s-prev_s) > 2 AND LEARNED_PREDICATE_001 == true` |
| 24 | AVOID | -0.253 | 0.273 / 0.593 | 0.249 / 0.594 | `abs(prev_s-prev_b)%12 == 3 AND abs(candidate_s-prev_s) > 4` |
| 25 | AVOID | -0.226 | 0.068 / 0.343 | 0.050 / 0.340 | `sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 7` |
| 26 | PREFER | 0.225 | 0.083 / 0.051 | 0.084 / 0.050 | `abs(prev_s-prev_b)%12 == 0 AND abs(candidate_s-current_b)%12 == 0 AND LEARNED_PREDICATE_001 == true` |
| 27 | AVOID | -0.212 | 0.041 / 0.220 | 0.032 / 0.221 | `sign(candidate_s-prev_s) == negative AND sign(current_b-prev_b) == negative AND abs(candidate_s-prev_s) > 7` |
| 28 | AVOID | -0.211 | 0.041 / 0.050 | 0.042 / 0.050 | `abs(prev_s-prev_b)%12 == 4 AND abs(candidate_s-current_b)%12 == 4 AND LEARNED_PREDICATE_001 == true` |
| 29 | PREFER | 0.199 | 0.170 / 0.045 | 0.192 / 0.045 | `sign(candidate_s-prev_s) == zero AND sign(current_b-prev_b) == negative` |
| 30 | PREFER | 0.173 | 0.088 / 0.050 | 0.069 / 0.051 | `abs(prev_s-prev_b)%12 == 7 AND abs(candidate_s-current_b)%12 == 7 AND LEARNED_PREDICATE_001 == true` |

Les deux taux sont calculés seulement dans les opportunités où la
propriété et son complément sont tous deux disponibles.

## Abstractions symétriques proposées après apprentissage

### Abstraction 1

- Conditions communes : `abs(candidate_s-prev_s) > 7`
- z montée/montée : `-30.411` ; z descente/descente : `-30.702`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 2

- Conditions communes : `abs(candidate_s-prev_s) > 4`
- z montée/montée : `-27.358` ; z descente/descente : `-27.572`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 3

- Conditions communes : `abs(candidate_s-prev_s) > 2`
- z montée/montée : `-22.564` ; z descente/descente : `-21.501`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 4

- Conditions communes : `abs(candidate_s-prev_s) > 12`
- z montée/montée : `-15.927` ; z descente/descente : `-14.645`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 5

- Conditions communes : `abs(candidate_s-current_b)%12 == 1`
- z montée/montée : `-11.624` ; z descente/descente : `-11.123`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 6

- Conditions communes : `abs(candidate_s-prev_s) > 1`
- z montée/montée : `-12.252` ; z descente/descente : `-10.727`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 7

- Conditions communes : `(aucune)`
- z montée/montée : `-12.521` ; z descente/descente : `-10.295`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 8

- Conditions communes : `abs(candidate_s-current_b)%12 == 1 AND abs(candidate_s-prev_s) > 4`
- z montée/montée : `-10.850` ; z descente/descente : `-9.764`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 9

- Conditions communes : `abs(candidate_s-current_b)%12 == 1 AND abs(candidate_s-prev_s) > 2`
- z montée/montée : `-11.524` ; z descente/descente : `-9.574`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 10

- Conditions communes : `abs(candidate_s-current_b)%12 == 6 AND abs(candidate_s-prev_s) > 2`
- z montée/montée : `-9.375` ; z descente/descente : `-9.917`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 11

- Conditions communes : `abs(candidate_s-current_b)%12 == 1 AND abs(candidate_s-prev_s) > 1`
- z montée/montée : `-11.481` ; z descente/descente : `-9.357`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 12

- Conditions communes : `abs(candidate_s-current_b)%12 == 1 AND abs(candidate_s-prev_s) > 7`
- z montée/montée : `-9.637` ; z descente/descente : `-9.117`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 13

- Conditions communes : `abs(candidate_s-current_b)%12 == 6 AND abs(candidate_s-prev_s) > 1`
- z montée/montée : `-8.855` ; z descente/descente : `-8.887`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 14

- Conditions communes : `abs(candidate_s-current_b)%12 == 6`
- z montée/montée : `-10.486` ; z descente/descente : `-8.578`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 15

- Conditions communes : `abs(candidate_s-current_b)%12 == 6 AND abs(candidate_s-prev_s) > 4`
- z montée/montée : `-8.470` ; z descente/descente : `-9.914`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 16

- Conditions communes : `abs(candidate_s-current_b)%12 == 11`
- z montée/montée : `-8.426` ; z descente/descente : `-8.611`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 17

- Conditions communes : `abs(candidate_s-current_b)%12 == 6 AND abs(candidate_s-prev_s) > 7`
- z montée/montée : `-8.292` ; z descente/descente : `-9.345`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 18

- Conditions communes : `abs(candidate_s-current_b)%12 == 11 AND abs(candidate_s-prev_s) > 2`
- z montée/montée : `-8.126` ; z descente/descente : `-9.003`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 19

- Conditions communes : `abs(candidate_s-current_b)%12 == 11 AND abs(candidate_s-prev_s) > 7`
- z montée/montée : `-7.759` ; z descente/descente : `-9.467`.
- Direction statistique : `selected_less_than_available`.
- Prédicat dérivé proposé :

```text
(delta_soprano > 0 AND delta_bass > 0) OR (delta_soprano < 0 AND delta_bass < 0)
```

### Abstraction 20

- Conditions communes : `abs(candidate_s-current_b)%12 == 11 AND abs(candidate_s-prev_s) > 4`
- z montée/montée : `-7.757` ; z descente/descente : `-10.332`.
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
| 0 | 6.192 | 3.016 | -1.963 | -0.684 |
| 1 | -0.900 | -0.309 | -14.918 | -6.727 |
| 2 | 0.100 | -1.585 | -5.727 | -1.969 |
| 3 | 0.714 | -0.178 | -7.971 | -5.122 |
| 4 | -1.926 | -0.709 | -9.661 | -3.842 |
| 5 | 1.189 | 0.904 | 1.580 | -0.875 |
| 6 | -3.849 | -2.214 | -13.646 | -7.140 |
| 7 | 7.976 | 1.728 | 4.447 | 0.733 |
| 8 | -3.267 | -1.497 | -11.147 | -5.087 |
| 9 | 2.831 | 3.180 | -5.036 | -2.591 |
| 10 | 1.453 | -1.131 | -6.236 | -4.756 |
| 11 | -1.048 | -0.928 | -12.100 | -4.498 |
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
