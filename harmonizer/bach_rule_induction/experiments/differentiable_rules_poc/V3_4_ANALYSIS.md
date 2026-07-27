# Analyse du POC V3.4 — calibration familiale répétée

## Pourquoi une nouvelle calibration

Le V3.3 retenait sept raffinements et aucun candidat dans un contrôle nul
unique. Ce résultat ne suffisait pas : lorsqu'on cherche 864 clauses, la plus
grande statistique d'une permutation peut être élevée par hasard même si
aucune clause ne passe les seuils finaux.

Le V3.4 rejoue donc 49 fois le pipeline nul complet :

1. permutation des choix à l'intérieur de chaque voix et de chaque choral ;
2. réajustement des quatre baselines ;
3. scan des 864 clauses ;
4. calcul, pour chaque clause suffisamment supportée, de
   `min(z_train, z_validation)` ;
5. conservation du maximum de cette statistique sur toute la famille.

La p-valeur empirique corrigée pour la recherche familiale est :

```text
(1 + nombre de maxima nuls >= statistique observée) / (1 + 49)
```

Le test final de 51 chorals reste scellé.

## Distribution sous le nul

| Résumé des 49 maxima | Valeur |
|---|---:|
| médiane | 3,611 |
| quantile 90 % | 4,613 |
| quantile 95 % | 4,817 |
| maximum | 6,205 |

Le maximum à `6,205` est particulièrement instructif : un z apparemment très
fort peut émerger quelque part dans la famille nulle. Le contrôle répété est
donc beaucoup plus discriminant que le contrôle unique du V3.3.

## Résultat corrigé famille

| Mode | Voix | Basse | min-z | Dépassements | p FWER |
|---|---|---:|---:|---:|---:|
| majeur | alto | `2→4` | 8,050 | 0/49 | **0,02** |
| mineur | alto | `7→3` | 4,379 | 8/49 | 0,18 |
| majeur | alto | `2→0` | 3,479 | 30/49 | 0,62 |
| majeur | ténor | `5→4` | 3,136 | 35/49 | 0,72 |
| mineur | soprano | `7→0` | 2,898 | 39/49 | 0,80 |
| mineur | alto | `2→0` | 2,745 | 42/49 | 0,86 |
| mineur | ténor | `7→8` | 2,683 | 44/49 | 0,90 |

Une seule clause survit donc à 5 % :

```text
mode == majeur
AND voix == alto
AND classe_source_voix == 11
AND classe_source_basse == 2
AND classe_cible_basse == 4
→ voix_cible == voix_source + 1
```

Elle est observée dans 47 cas sur 54 au train et 19 cas sur 19 en validation.
Son interprétation postérieure est un proxy numérique de la résolution de la
sensible dans `vii°6 → I6`.

## Interprétation scientifique

Le V3.4 ne réfute pas les six autres patrons comme descriptions musicales. Il
montre qu'ils ne sont pas distinguables des maxima produits par cette famille
de recherche avec le corpus et le protocole actuels. Ils doivent rester des
hypothèses et ne pas être promus en règles induites.

Le patron `alto majeur, basse 2→4` est le premier raffinement tonal à franchir
une correction empirique de famille. Il reste néanmoins `CANDIDATE` jusqu'à :

- l'audit indépendant des ensembles de classes formant les accords source et
  cible ;
- la vérification qu'il ne dépend pas de quelques variantes proches ;
- l'ablation de son gain conditionnel dans le catalogue conjoint ;
- le gel de la clause avant l'ouverture du test final.
