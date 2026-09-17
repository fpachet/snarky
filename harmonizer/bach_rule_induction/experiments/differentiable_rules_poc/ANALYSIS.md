# Analyse du premier POC

## Résultat principal

Le POC fournit une première réponse positive, mais encore limitée, à
l'hypothèse de départ.

À partir des seules hauteurs, de leurs différences, de leur signe et de classes
numériques modulo 12, le système :

1. retrouve les queues extrêmes associées aux grands sauts mélodiques ;
2. apprend séparément que les branches montée/montée et
   descente/descente sont sous-sélectionnées ;
3. les factorise dans un prédicat dérivé anonyme de « même signe non nul » ;
4. découvre ensuite que la répétition en même signe des classes numériques
   `0` et `7` est presque catégoriquement évitée ;
5. conserve ces deux clauses avec des poids négatifs importants dans le modèle
   conditionnel ajusté par gradient ;
6. ne retrouve pas cet effet négatif dans le contrôle où les choix de soprano
   sont mélangés à l'intérieur de chaque pièce.

Ce comportement est extensionnellement très proche des règles connues
d'octaves/unissons parallèles et de quintes parallèles. Les noms
musicologiques n'ont pas été disponibles pendant la recherche.

## Données

- archive historique : Music21 3.1.0, hash vérifié ;
- corpus : 352 chorals du manifeste DeepBach historique ;
- décisions extraites : 20 350 attaques de soprano contiguës ;
- candidates : les 22 hauteurs MIDI de l'ambitus `60..81` ;
- apprentissage : 246 pièces, 14 436 décisions ;
- validation : 53 pièces, 3 029 décisions ;
- test scellé : 53 pièces, non consultées.

Le partage est effectué par pièce avant l'extraction des événements.

## Gradient et structure symbolique

Le modèle optimise la vraisemblance conditionnelle du choix de Bach :

```text
P(candidate | contexte) =
    softmax(somme poids_r × clause_r)
```

Le gradient au poids nul classe les clauses selon l'écart entre :

- la présence de la clause parmi les candidates disponibles ;
- sa présence dans le choix effectivement réalisé.

Les poids des clauses retenues sont ensuite appris conjointement par Adam avec
une pénalité L1. Les candidates non choisies ne sont jamais considérées
individuellement comme des erreurs.

## Concept local inventé

Deux clauses indépendantes sont apparues dans la même queue négative :

```text
sign(delta_soprano) == positive
AND sign(delta_bass) == positive
```

```text
sign(delta_soprano) == negative
AND sign(delta_bass) == negative
```

Leurs scores sur train sont respectivement :

```text
z = -25.748
z =  -9.456
```

La compression symbolique propose alors :

```text
LEARNED_PREDICATE_001 :=
    (delta_soprano > 0 AND delta_bass > 0)
 OR (delta_soprano < 0 AND delta_bass < 0)
```

Ce prédicat correspond, après l'expérience aveugle, à la notion de mouvement
de même direction non nul. Sa définition reste entièrement locale et
compilable.

## Règles numériques retrouvées

Une fois le prédicat admis, les douze classes `0..11` sont testées de manière
symétrique, sans privilégier une valeur.

### Répétition de la classe 0

```text
abs(prev_s - prev_b) % 12 == 0
AND abs(candidate_s - current_b) % 12 == 0
AND LEARNED_PREDICATE_001
```

| Mesure | Train | Validation |
|---|---:|---:|
| fréquence choisie | 0,00403 | 0 |
| disponibilité moyenne | 0,05090 | 0,04975 |
| score z | -8,907 | -4,410 |
| opportunités testables | 1 737 | 370 |

Poids conjoint appris : `-2,658`.

### Répétition de la classe 7

```text
abs(prev_s - prev_b) % 12 == 7
AND abs(candidate_s - current_b) % 12 == 7
AND LEARNED_PREDICATE_001
```

| Mesure | Train | Validation |
|---|---:|---:|
| fréquence choisie | 0,00285 | 0,00222 |
| disponibilité moyenne | 0,05008 | 0,05101 |
| score z | -9,952 | -4,715 |
| opportunités testables | 2 104 | 450 |

Poids conjoint appris : `-2,741`.

Après dévoilement sémantique :

- classe `0` : unisson ou octave modulo l'octave ;
- classe `7` : quinte parfaite modulo l'octave.

Le système retrouve donc les deux familles attendues sans recevoir ces
étiquettes.

## Contrastes découverts

Les classes `3` et `9` montrent au contraire une sur-sélection stable lors
d'une répétition dans le même sens :

| Classe | z train | z validation | choix validation | disponibilité |
|---:|---:|---:|---:|---:|
| 3 | +26,909 | +12,213 | 0,176 | 0,052 |
| 9 | +5,404 | +6,175 | 0,136 | 0,052 |

Le patron n'est donc pas simplement « éviter tout intervalle répété dans le
même sens ». Le contraste numérique isole bien certaines classes.

## Contrôle nul

Le contrôle conserve, pour chaque pièce, l'histogramme des hauteurs de
soprano, mais permute leurs choix entre les opportunités. Il brise ainsi les
relations locales sans remplacer les notes par du bruit uniforme.

| Mesure | Bach | Choix mélangés |
|---|---:|---:|
| NLL validation du modèle compact | 1,971 | 2,697 |
| classe 0, z validation | -4,410 | +3,019 |
| classe 7, z validation | -4,715 | +1,732 |

L'évitement spécifique de `0` et `7` disparaît et change même de signe. Cela
réduit fortement l'hypothèse d'un artefact créé uniquement par l'ambitus ou
par la fréquence marginale des hauteurs.

## Règles mélodiques

Le détecteur le plus extrême est :

```text
abs(candidate_s - prev_s) > 2
```

| Mesure | Train | Validation |
|---|---:|---:|
| fréquence choisie | 0,149 | 0,139 |
| disponibilité | 0,773 | 0,773 |
| score z | -178,969 | -83,236 |

Le seuil `> 7` est beaucoup plus proche d'une interdiction :

| Mesure | Train | Validation |
|---|---:|---:|
| fréquence choisie | 0,00658 | 0,00561 |
| disponibilité | 0,344 | 0,343 |
| score z | -85,974 | -39,417 |

Enfin, le seuil `> 12` possède zéro occurrence choisie sur train, avec
`z = -35,374`. Il retrouve directement la règle scolaire sur les sauts
supérieurs à l'octave. Le modèle compact privilégie néanmoins `> 7`, plus
prédictif mais moins catégorique : c'est un exemple de règle connue retrouvée
puis raffinée par une tendance plus stricte.

## Exceptions authentiques

La clause de classe `0` possède sept réalisations dans train et aucune dans
validation. La classe `7` en possède six dans train et une dans validation.

Exemples :

```text
classe 0
bach/bwv154.8      offset 11→12   S 74→73   B 50→49
bach/bwv302        offset 15→16   S 62→74   B 50→62
bach/bwv322        offset 23→24   S 60→67   B 36→43
bach/bwv413        offset 90→91   S 67→65   B 43→41

classe 7
bach/bwv113.8      offset 37→38   S 74→73   B 55→54
bach/bwv248.42-s   offset 24→27   S 67→72   B 48→53
bach/bwv73.5       offset 29→32   S 67→79   B 48→60
bach/bwv162.6-lpz  offset 59→60   S 74→73   B 55→54  [validation]
```

Ces cas ne doivent pas être supprimés. Ils peuvent signaler :

- une frontière de phrase ou une fermata encore absente des faits ;
- une répétition ou variante du corpus ;
- une exception réelle ;
- une insuffisance de la représentation modulo 12 ;
- un problème d'alignement à vérifier sur la partition.

`bwv302` et `bwv303` contiennent notamment le même patron chiffré ; les groupes
de variantes devront être pris en compte dans les futurs partages.

## Ce qui n'est pas encore retrouvé

### Mouvement direct

Le patron :

```text
LEARNED_PREDICATE_001
AND abs(delta_soprano) > 2
AND target_interval_class == k
```

est négatif pour presque toutes les classes. L'effet général d'un grand saut
dans le même sens domine encore le contraste propre aux classes `0` et `7`.
Le POC ne permet donc pas encore de déclarer la règle de mouvement direct
correctement identifiée.

Il faudra mesurer cette règle sur les résidus d'un modèle ayant déjà absorbé
les coûts du saut, de la direction et de la consonance verticale.

### Obligations

Aucune clause de ce premier vocabulaire n'atteint un marginal conditionnel
proche de 1 avec un support suffisant. Ce n'est pas surprenant : les obligations
connues, comme la résolution de la sensible ou de la septième, nécessitent au
minimum la tonalité, le degré et le statut harmonique.

Le mécanisme sait représenter une obligation comme la pénalisation de
`A AND NOT B`, mais ce premier POC teste surtout des interdictions de niveau A.

## Limites méthodologiques

1. Le modèle compact conserve encore 52 clauses actives. La parcimonie est
   insuffisante.
2. La première sélection structurale utilise le gradient marginal. Une vraie
   génération de colonnes résiduelle est nécessaire pour éviter les variantes
   corrélées d'une même règle.
3. L'opérateur modulo 12 encode déjà l'équivalence d'octave. Une expérience
   encore plus forte devrait apprendre elle-même ce regroupement depuis les
   distances brutes.
4. Seules la soprano et la basse sont considérées.
5. Les durées, fermatas, temps métriques et statuts de phrase ne sont pas
   encore exposés.
6. Le bootstrap par groupes de pièces et le regroupement des variantes ne sont
   pas encore implémentés.
7. Les seuils normatifs `MUST`, `NORMALLY` et `PREFER` ne sont pas gelés.
8. Le jeu de test final reste volontairement fermé.

## Conclusion provisoire

Le résultat intéressant n'est pas seulement que les classes `0` et `7` soient
rares. Le pipeline a successivement :

1. appris deux clauses directionnelles numériques ;
2. inventé leur abstraction symétrique ;
3. réutilisé cette abstraction dans douze hypothèses uniformes ;
4. sélectionné par gradient les classes `0` et `7` comme interdictions fortes ;
5. validé les mêmes queues sur des pièces séparées ;
6. montré leur disparition sous mélange intra-pièce.

Cela constitue un POC positif de redécouverte de règles connues et justifie une
seconde itération plus parcimonieuse.

La prochaine étape prioritaire est une véritable boucle de génération de
colonnes sur résidus, suivie de l'ajout des faits tonals minimaux pour rechercher
la première obligation.
