# Analyse du POC V2.2 — contraintes locales SATB

## Résultat

Le POC étend la tâche de choix conditionnel aux quatre voix et aux trois
paires de voix adjacentes. Sans recevoir les mots *triton* ou
*chevauchement*, le sélecteur retient :

```text
abs(candidate - previous) % 12 == 6
→ éviter
```

```text
previous_lower - candidate_upper > 0
OR candidate_lower - previous_upper > 0
→ éviter
```

Après sélection, les valeurs numériques `6` et `0` sont comparées aux règles
Snarky cachées. Elles correspondent respectivement à `R-MELODY-002` et
`R-OVERLAP-001`, sans désaccord sur 1 993 états mélodiques et 534 050 états
valides de voix adjacentes. Le contrôle permuté ne sélectionne aucune famille.
Le jeu de test de 51 chorals reste scellé.

## Représentation et gradient

Le corpus fournit 94 363 décisions contiguës :

| Voix | Décisions |
|---|---:|
| Soprano | 20 335 |
| Alto | 24 422 |
| Tenor | 24 837 |
| Basse | 24 769 |

Quatre modèles de choix absorbent la tessiture, la direction, des seuils
génériques de saut, les classes d'intervalles harmoniques avec les trois
autres voix et un coût lisse d'espacement. Aucun de ces faits n'expose la
classe mélodique `6` ni la frontière d'overlap `0`.

Pour chaque candidate booléenne, le gradient résiduel est la somme de :

```text
1[candidate choisie satisfait la clause]
- P(clause | contexte)
```

Le z résiduel conditionnel sert de premier filtre. Un budget d'une règle par
famille impose ensuite la parcimonie.

## Pourquoi un contraste local est nécessaire

Un simple seuil de fréquence sélectionne trop de valeurs : les grands sauts
sont généralement rares et les seuils d'overlap sont emboîtés. De plus, le
contrôle permuté conserve la tonalité de chaque choral et contient donc déjà
peu de paires à six demi-tons.

Le sélecteur recherche donc une encoche dans la famille numérique. Pour une
valeur `k`, il calcule :

```text
log(taux_observé_k / taux_attendu_k)
- moyenne des mêmes log-ratios pour k-1 et k+1
```

Les classes mélodiques sont circulaires modulo 12. Ce critère distingue une
frontière ou une classe singulière d'une pente générale de rareté.

## Classe mélodique 6

| Partition | Taux observé | Taux attendu | z résiduel | Contraste local |
|---|---:|---:|---:|---:|
| Train, 251 pièces | 0,003796 | 0,012517 | -21,729 | -1,443 |
| Validation, 50 pièces | 0,002944 | 0,012430 | -10,422 | -1,667 |

Le bootstrap de 1 000 rééchantillonnages de chorals donne sur validation un z
médian de `-10,406`, avec intervalle à 95 % `[-11,614 ; -9,307]`. Dans le
contrôle permuté, le z reste négatif à cause du vocabulaire tonal, mais
l'encoche locale n'est que `-0,527/-0,491` et ne franchit pas le seuil
préenregistré de `-0,75`. La règle n'est donc retenue que dans l'ordre
authentique des notes.

## Frontière d'overlap 0

| Partition | Taux observé | Taux attendu | z résiduel | Contraste local |
|---|---:|---:|---:|---:|
| Train, 251 pièces | 0,030789 | 0,043388 | -18,508 | -0,237 |
| Validation, 50 pièces | 0,018943 | 0,035107 | -11,017 | -0,309 |

Le bootstrap de validation donne un z médian de `-10,995`, intervalle à 95 %
`[-12,744 ; -9,185]`. Le contrôle permuté conserve une faible pente de
tessiture, mais ses contrastes `-0,080/-0,104` ne franchissent pas le seuil
de `-0,20`. La discontinuité retenue est exactement la frontière stricte
séparant espacement et chevauchement.

## Ce qui est établi

1. Le même formalisme de décision locale couvre maintenant les quatre voix.
2. Le gradient seul signale les zones rares, mais ne suffit pas à faire une
   règle intelligible.
3. Un budget de clauses et un contraste local de forme éliminent les vastes
   régions de simple rareté.
4. Les classes `6` et `0` survivent sur validation et au bootstrap par choral.
5. Elles disparaissent avec le même sélecteur dans le contrôle permuté.
6. Les formules induites sont extensionnellement équivalentes aux deux règles
   Snarky cachées sur les domaines finis testés.

## Limites et suite

- Les seuils d'encoche sont exploratoires et doivent être gelés avant toute
  ouverture du test.
- Les tessitures sont celles de DeepBach ; il faudra auditer les notes du
  corpus qui en sortent.
- Les exceptions authentiques ne sont pas encore transformées en exemples
  musicaux ni analysées par contexte.
- Le prochain jalon de niveau A est la recherche uniforme des parallèles dans
  les six paires de voix, puis l'ablation conjointe des quatre familles déjà
  retrouvées.
- Les premières obligations demanderont ensuite des statuts tonals explicites
  (sensible, septième, cadence), conformément à l'hypothèse de règles locales
  sur des faits de statut bien définis.
