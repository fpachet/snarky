# Décision V17.1 — aucun facteur isolé ne passe le filtre court

## Décision

Aucune des douze colonnes présélectionnées n'est admise. Aucun refit n'est
lancé et le test réservé reste fermé.

Cette décision est prise avec le critère gelé avant l'expérience :

- amélioration de la distance générative standardisée ;
- amélioration pour chaque graine, pas seulement après leur moyenne ;
- absence de régression sur les grands sauts de basse, les blocs forts non
  triadiques et les dissonances fortes ;
- passage obligatoire à six balayages avant l'évaluation à 30 balayages.

## Protocole

V13 et chaque perturbation utilisent :

- les mêmes huit chorals de train ;
- les mêmes deux graines ;
- le même état initial ;
- le même ordre de mises à jour et les mêmes tirages uniformes ;
- six balayages Gibbs ;
- le signe demandé par le gradient conditionnel exact ;
- un poids borné à `±0,15`.

La différence mesurée est donc celle du sampler réel à horizon fini. Aucune
identité de covariance d'équilibre n'est utilisée.

## Écran des douze candidats

| Rang | Résidu relatif | Deux graines améliorées | Trois gardes |
|---:|---:|---|---|
| 12 | 0,773 | non | non |
| 9 | 0,863 | oui | non |
| 7 | 0,868 | non | non |
| 4 | 0,951 | non | non |
| 11 | 0,963 | non | oui |
| 1 | 0,995 | non | oui |
| 8 | 1,013 | non | non |
| 10 | 1,043 | non | non |
| 2 | 1,050 | non | non |
| 3 | 1,133 | non | non |
| 5 | 1,162 | non | non |
| 6 | 1,198 | non | non |

Le rang 5, utile à 30 balayages dans V16, est bien défavorable à l'horizon
court. V17 reproduit donc directement le conflit d'horizon.

## Dichotomie des deux meilleurs cas

Le rang 9 à `−0,15` est le seul à améliorer les deux graines. Il réduit les
blocs forts non triadiques et les dissonances fortes, mais augmente l'erreur
sur les grands sauts de basse de `0,00635`.

À `−0,075` :

- la distance moyenne reste meilleure (`0,838` du résidu V13) ;
- les trois gardes deviennent favorables ;
- les deux graines prises séparément régressent (`1,070` et `1,165`).

L'amélioration de la moyenne provient donc d'une compensation entre graines,
pas d'un effet robuste.

Le rang 12 à `−0,075` reste instable (`0,753` et `1,276`) et continue
d'aggraver les grands sauts de basse.

## Conclusion

La première itération V17 ne trouve aucun facteur local isolé qui améliore
robustement le début de chaîne tout en respectant les trois gardes musicales.
Ce résultat ne nie pas l'utilité du rang 5 en régime long ; il montre que les
deux horizons exigent des corrections différentes.

## Seconde itération : correction conjointe

La seconde itération combine le rang 9 à un renforcement intelligible du
facteur V13 :

```text
any_voice_adjacent_step_gt(all_voices)=2
```

Son poids, déjà négatif, est diminué de `0,025`, `0,05` ou `0,075` pour
compenser les grands sauts. Sur le petit écran 8 pièces × 2 graines, les trois
variantes améliorent la distance brute ; `−0,075` est la meilleure :

| Modèle | Distance L1 |
|---|---:|
| V13 | 0,3194 |
| correction conjointe `−0,025` | 0,2762 |
| correction conjointe `−0,050` | 0,2702 |
| correction conjointe `−0,075` | 0,2500 |

La meilleure variante est alors répliquée sur 32 pièces × 3 graines à six
balayages. Le gain ne se confirme pas :

| Modèle | Distance L1 | Grands sauts |
|---|---:|---:|
| V13 | 0,5208 | 32,04 % |
| correction conjointe `−0,075` | 0,5422 | 30,45 % |

La correction atteint son objectif étroit sur la basse, mais dégrade notamment
les demi-tons, les blocs triadiques et l'empreinte forte `{0,3,6,8}`. Le petit
écran surestimait donc sa robustesse.

## Arrêt de V17

La seconde et dernière itération bornée est négative. Conformément au critère
d'arrêt, elle ne passe ni à 30 balayages ni au refit exact.

Le protocole envisagé était :

1. conserver le rang 9, qui améliore harmonie et distance moyenne à court
   terme ;
2. présélectionner quelques facteurs existants capables de compenser son effet
   sur les grands sauts et sa variabilité inter-graines ;
3. mesurer directement ces petites corrections conjointes avec le même
   protocole apparié ;
4. arrêter si aucune combinaison ne passe simultanément les horizons 6 et 30.

Il ne faut pas relâcher après coup le critère « chaque graine » ni les gardes
musicales pour fabriquer une promotion.

Ce point d'arrêt suggère que la prochaine avancée ne viendra probablement pas
d'un nouveau réglage marginal de poids isolés. Il faudra soit apprendre des
interactions explicites entre règles, soit modifier le protocole de génération
pour traiter séparément le régime transitoire et le régime long.
