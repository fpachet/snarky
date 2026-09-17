# V5.7 — boucle générative avant/après

Même soprano, même squelette rythmique, même graine `5517` et `12`
balayages Gibbs. Les 51 chorals de test restent fermés.

| Version | Tonalité analysée | Répétitions basse | Répétitions voix inférieures | Attaques tonales rares | Blocs triadiques | Blocs structurels | Blocs à 2 classes |
|---|---|---:|---:|---:|---:|---:|---:|
| Bach | b minor | 0 | 30 | 0.68 % | 45.92 % | 52.04 % | 2.04 % |
| V5.5 | A major | 20 | 59 | 7.88 % | 25.51 % | 25.51 % | 5.10 % |
| V5.6 | b minor | 19 | 45 | 3.08 % | 52.04 % | 65.31 % | 1.02 % |
| V5.7 | b minor | 7 | 27 | 3.42 % | 47.96 % | 62.24 % | 0.00 % |

## Pouvoir prédictif tenu à part

| Modèle | Règles | NLL validation |
|---|---:|---:|
| V5.5 | 12 | 1.449123 |
| V5.6 | 18 | 1.150282 |
| V5.7 | 20 | 1.120257 |

## Lacune ciblée

La répétition attaquée générale n'entrait pas dans le budget V5.6.
Après séparation par voix, la clause numérique
`attacked_repeat_from_previous(v3)` est sélectionnée au rang `19` :

- z de sélection : `-41.235` ;
- poids appris : `-1.588788` ;
- facteur d'odds isolé : `0.204`.

## Lecture

- V5.6 corrige principalement la tonalité et les sonorités verticales.
- V5.7 conserve cette amélioration et réduit fortement les répétitions
  de basse sans les interdire.
- Les taux génératifs portent sur un seul choral du train et ne
  remplacent pas une campagne multi-pièces tenue à part.
- Les exports canoniques sont produits par MuSES ; music21 n'est utilisé
  que pour importer le corpus MXL et conserver une vue de sa notation.
