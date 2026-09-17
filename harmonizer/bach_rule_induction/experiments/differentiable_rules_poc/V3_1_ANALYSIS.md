# Analyse du POC V3.1 — première obligation tonale

## Question

Le V3.1 demande si le même mécanisme résiduel qui a retrouvé des interdictions
peut aussi retrouver une obligation. Le mineur reçoit seulement :

```text
classe_source := (hauteur_source - tonique_globale) modulo 12
conclusion := candidate == source + 1
```

Il scanne uniformément les douze classes sources. Il ne reçoit ni le mot
*sensible*, ni une liste de degrés privilégiés, ni un accord, ni une cadence.

## Résultat

Avec un budget d'une règle, la seule classe retenue est `11`. Son
interprétation musicologique, attribuée après sélection, est la sensible
globale.

| Ensemble | Occurrences | Taux observé | Taux attendu | z résiduel |
|---|---:|---:|---:|---:|
| train | 4 235 | 0,5053 | 0,3002 | 34,761 |
| validation | 909 | 0,5259 | 0,3074 | 17,093 |

Le bootstrap de 1 000 rééchantillonnages de chorals donne sur validation une
médiane de `16,958`, avec un intervalle à 95 % `[14,219 ; 20,106]` et un signe
positif dans toutes les réplications.

## Pourquoi le pic local est nécessaire

Un premier sélecteur fondé seulement sur le z résiduel retenait aussi `11`
après permutation. Le modèle nul conservait la fréquence de la tonique, ce qui
créait un faux signal pour le mouvement d'un demi-ton.

Le protocole final exige donc que le taux de `11` forme un pic circulaire par
rapport aux classes voisines `10` et `0`. Les contrastes logarithmiques sont
`1,501` au train et `1,895` en validation. Dans le contrôle nul, ils tombent à
`0,906` et `1,067`, sous les seuils gelés ; aucune classe n'est alors retenue.

Cette correction est importante : elle montre qu'un marginal extrême n'est
pas encore une règle et qu'un contraste structurel doit séparer la propriété
recherchée des fréquences générales du corpus.

## Une tendance, pas encore la règle experte

Sur validation, la résolution apparaît dans les quatre voix :

| Voix | Résolutions / occurrences | Taux observé | Taux attendu |
|---|---:|---:|---:|
| soprano | 59 / 115 | 0,513 | 0,268 |
| alto | 190 / 385 | 0,494 | 0,262 |
| ténor | 115 / 208 | 0,553 | 0,311 |
| basse | 114 / 201 | 0,567 | 0,414 |

Environ la moitié des occurrences restent des exceptions. La formule globale
n'est donc pas extensionnellement équivalente à `R-LEADING-001`, qui consulte
le rôle de l'accord source et des exceptions explicites. Son statut est
`MISSING_CONTEXT_FOR_EQUIVALENCE`.

## Conclusion

Le POC retrouve bien une obligation connue à partir d'une conclusion positive,
et non seulement des interdictions. Il produit en même temps un diagnostic
utile : la tonalité globale suffit à révéler la sensible, mais pas à expliquer
quand sa résolution devient presque obligatoire. C'est cette question que
traitent V3.2 et V3.3.
