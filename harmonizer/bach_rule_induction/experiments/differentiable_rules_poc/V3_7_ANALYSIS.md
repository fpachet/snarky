# Analyse du POC V3.7 — compression harmonique cross-fittée

## But

V3.6 représentait la première règle tonale par deux colonnes imbriquées :

1. un proxy local court ;
2. un renforcement lorsque la candidate forme exactement `vii°6→I6`.

V3.7 cherche une représentation plus compacte, apprise par gradient, sans
perdre le gain prédictif. La sélection utilise cinq plis internes aux 251
chorals de train. Les variantes de soprano identiques restent dans le même pli
et le modèle d'un pli n'utilise jamais ce pli pour choisir son arrêt.

## Les treize cas décisifs

La définition candidat-dépendante retrouve :

- 11 contextes couverts par le proxy mais pas par la spécialisation exacte ;
- 2 contextes harmoniques exacts où l'alto ne résout pas ;
- donc 13 cas atypiques au train.

L'audit complet est conservé dans le JSON canonique. Il montre notamment :

- deux résolutions avec une quarte suspendue dans la cible `{0,4,5,7}` ;
- des sources enrichies `{2,5,7,11}` ou `{2,5,9,11}` ;
- deux sources `{2,6,11}` qui ne résolvent pas ;
- deux répétitions de `bwv317` où l'accord pourrait devenir `I6`, mais où
  l'alto conserve la sensible ;
- une cible sans degré `7`, également non résolue.

Le statut fonctionnel minimal « source dominante vers noyau tonique » élimine
les trois contextes les moins compatibles. Il couvre 51 cas train, dont 47
résolutions, contre 47/54 pour le proxy brut.

## Compression graduée

La meilleure représentation est une seule feature ordinale :

```text
harmonic_resolution_strength(candidate) =
    0  hors contexte
    1  si le proxy local recommande la résolution
    2  si, en plus, la candidate forme exactement vii°6→I6
```

Un seul poids positif est appris par gradient. Cette représentation correspond
à une règle générale dont la force double dans son noyau harmonique, plutôt
qu'à deux règles indépendantes.

## Résultats cross-fittés

| Modèle | Paramètres | Bits descriptifs | NLL cross-fit | Gain conservé |
|---|---:|---:|---:|---:|
| baseline | 0 | 0 | 1,281680 | — |
| proxy | 1 | 108 | 1,278527 | 87,89 % |
| proxy + exact | 2 | 240 | 1,278093 | 100 % |
| `graded_exact` | 1 | 144 | **1,278094** | **99,96 %** |
| `graded_vii_core` | 1 | 144 | 1,278251 | 95,58 % |
| `graded_dominant_core` | 1 | 144 | 1,278223 | 96,36 % |

La différence entre `graded_exact` et les deux poids libres n'est que de
`0,0000016` NLL par décision. Sur la validation historique, la compression est
même légèrement meilleure : `1,268430` contre `1,268457`.

Le bootstrap cross-fitté de `graded_exact` contre la baseline donne :

```text
médiane  0,003403
95 %     [0,001588 ; 0,005555]
P(gain > 0) = 1,000
```

## Contrôle nul

Sur les réponses mélangées, les bornes basses bootstrap de tous les modèles
candidats sont négatives. Le sélecteur retourne donc `null` au lieu de choisir
artificiellement le meilleur bruit.

## Décision gelée

`graded_exact` est retenu avant ouverture du test :

- un paramètre au lieu de deux ;
- 144 bits descriptifs contre 240 ;
- 99,96 % du gain cross-fitté ;
- borne bootstrap strictement positive ;
- aucun modèle retenu sous le contrôle nul.

La généralisation `graded_dominant_core` reste une hypothèse intéressante,
mais n'est pas substituée après coup au vainqueur cross-fitté. Son éventuelle
étude ultérieure constituera une nouvelle famille avec un nouveau test.

Le protocole confirmatoire est figé dans
[`FROZEN_V3_8_TEST_PROTOCOL.json`](FROZEN_V3_8_TEST_PROTOCOL.json). Toute
lecture des 51 chorals de test doit passer par ce protocole sans modification
de la feature ni des seuils.
