# V5.16 — pont probabiliste vers `CHOICE`

## Résultat

Le modèle probabiliste V5.16 reste la définition de référence. Le pont
[`../snarky_choice_bridge.py`](../snarky_choice_bridge.py) ne réapprend et ne
modifie aucun paramètre. Il :

1. charge les 41 facteurs canoniques et leurs poids logarithmiques ;
2. évalue leurs prédicats sur chaque candidate du noyau K3 ;
3. ajoute les logits empiriques de registre et de classe tonale ;
4. calcule `exp(score_local - max_score_local)` ;
5. expose ces valeurs positives à un futur `CHOICE` Snarky ;
6. conserve, pour chaque candidate, les identifiants et contributions des
   facteurs actifs.

Les probabilités normalisées sont donc exactement :

```text
P(note = a | reste du noyau K3)
    = exp(score(a) - max_b score(b))
      / somme_b exp(score(b) - max_c score(c))
```

## Parité sémantique

L'export a fusionné 44 termes source en 41 facteurs : trois corrections
additives portent sur un prédicat déjà présent. Le test compare les deux
évaluations sur les 46 hauteurs du domaine appris, en majeur et en mineur.

| Quantité | Écart absolu maximal |
|---|---:|
| score local | `1.78e-15` |
| poids positif de `CHOICE` | `1.73e-17` |
| probabilité normalisée | `1.04e-17` |

Ces écarts sont uniquement ceux de l'arithmétique flottante. Les sommes de
probabilités valent `1.0`.

Les tests automatiques vérifient également :

- 41 facteurs chargés ;
- poids de choix strictement positifs ;
- normalisation de chaque distribution ;
- parité des scores, poids et probabilités ;
- explication de chaque candidate par les identifiants `F-K3-V5.16-*`.

## Portée exacte du jalon

Ce jalon résout la traduction numérique entre le modèle MaxEnt/Gibbs et
`CHOICE`. Il ne prétend pas encore avoir transcrit chaque prédicat K3 dans la
syntaxe textuelle `.rules` de Snarky. Cette dernière étape doit préserver la
même table d'activations, puis être testée prédicat par prédicat contre
`k3.feature_mask`.

