# Domaines et propagation : réduire le coût des opérations de base

Expérience du **13 octobre 2026**, après les
[optimisations du matching et du filtrage conjoint](../magic_sum_lookup_matching_2026-10-13/README.md).

## Modifications

Les masques de domaines restent des entiers Python. Cette expérience optimise
les opérations qui les entourent, sans changer les supports des contraintes,
les heuristiques de recherche, ni les paramètres sauvegardés.

1. **Explications différées.** Chaque réduction enregistre un triplet compact
   `(variable, bits retirés, cause)`. Les objets publics `DomainRemoval` et leurs
   ensembles de valeurs sont construits quand `removals` ou une solution les
   demande. Le préfixe déjà décodé est réutilisé après un ajout et tronqué lors
   d'une restauration. Les anciennes observations restent immuables ; une
   branche sœur avec autant d'événements ne peut pas réutiliser le mauvais cache.
2. **Statuts et affectations.** Les compteurs de domaines vides et non fixés
   donnent des tests `empty` et `complete` constants. Une affectation conserve
   directement le bit du candidat, sans ensemble singleton temporaire. Le
   coordinateur mixte consulte le nombre d'événements sans décoder leurs valeurs.
3. **Index numériques.** Les masques, alphabets, tailles et projections sont
   stockés en tableaux avec des identifiants de variables stables. Les plans
   compilés SUM/ALLDIFF lisent leurs masques par index. Les noms symboliques
   restent disponibles dans l'API, les résultats et les causes. Les index d'un
   plan ne sont utilisés qu'avec son magasin d'origine ; un autre magasin
   conserve l'accès symbolique. Les tailles et statuts sont restaurés depuis
   les masques lors du retour arrière.
4. **Masques réellement modifiés.** SUM/ALLDIFF comparent leurs supports aux
   masques d'entrée. Une révision sans changement évite toute la boucle
   d'application ; sinon seuls les domaines réduits appellent `retain_mask`.
   Le prototype conjoint bénéficie également de cette suppression des appels
   sans effet, y compris lors de l'application de ses supports supplémentaires.
5. **File de propagation.** Un tableau d'octets remplace l'ensemble des indices
   déjà en file. Les listes d'incidence sont indexées par variable et deux
   boucles évitent de construire un tuple temporaire incidents + gardes à chaque
   événement. L'ordre des ajouts est préservé, y compris pour les gardes hors
   portée et le slot supplémentaire de la coupe d'objectif.

Les compteurs dérivés ne sont pas des témoins de supports. Ils sont mis à jour
sur chaque réduction et restauration. Aucun changement d'algorithme arithmétique
ou de matching n'est introduit ici. Ces changements de base sont actifs dans
le solveur natif ; le filtrage conjoint SUM + ALLDIFF reste optionnel.

## Protocole et étapes

Cinq versions cohérentes de cinq modules sont figées :

| Version | Contenu cumulatif |
|---|---|
| `before` | État du workspace avant cette expérience, incluant le précédent chemin rapide du matching |
| `records` | Explications différées, statuts constants, affectation directe, comptage mixte sans décodage |
| `indexed` | Stockage en tableaux, tailles mémorisées et lectures des plans par index |
| `delta` | Application des seuls masques réellement réduits |
| `after` | Drapeaux de file et incidence indexée |

Le collecteur charge chaque version sous un espace de modules séparé. Les types
immuables de modèles, les kernels de repli inchangés et le contrôleur de recherche
restent partagés. Le filtre conjoint est lié à la classe native correspondante ;
son code avant et après est conservé. Cela évite de combiner une ancienne classe
de domaine avec une interface de plan récente incompatible.

Les exécutions sont séquentielles et mélangées de façon déterministe. Le temps
inclut construction du modèle, état, compilation, recherche et production des
explications des solutions. Imports, chargement des variantes, comparaison des
résultats et validation indépendante sont exclus. Les signatures exigent des
résultats logiques, recherches et explications identiques, hors temps écoulé.

15×15, 18×18 et 20×20 sont limités à 80, 30 et 30 nœuds. Ces lignes mesurent
seulement des préfixes, sans temps de résolution complète. Les audits des appels
et les microbenchmarks sont séparés des temps de résolution.

## Résolution native : comparaison finale

Médianes de trois exécutions par version, en secondes, avec les paramètres
sauvegardés. Chaque paire conserve exactement les mêmes nœuds, échecs,
révisions, solutions et explications. Le pourcentage est la variation du temps :
une valeur négative indique une amélioration.

| Taille | Avant | Après | Variation |
|---|---:|---:|---:|
| 6×6 | 0,050392 | 0,047089 | −6,6 % |
| 8×8 | 0,121079 | 0,110818 | −8,5 % |
| 9×9 | 2,239943 | 1,964841 | −12,3 % |
| 10×10 | 0,265411 | 0,250485 | −5,6 % |
| 11×11 | 0,464844 | 0,448130 | −3,6 % |
| 12×12 | 0,537879 | 0,525222 | −2,4 % |
| 13×13 | 2,354102 | 2,202718 | −6,4 % |
| 14×14 | 1,161241 | 1,143233 | −1,6 % |
| 16×16 | 6,719309 | 6,395325 | −4,8 % |

Les trois tailles suivantes restent des préfixes **sans solution**, et ne sont
pas des temps de résolution :

| Taille | Limite de nœuds | Avant | Après | Variation |
|---|---:|---:|---:|---:|
| 15×15 | 80 | 0,555035 | 0,532815 | −4,0 % |
| 18×18 | 30 | 0,612277 | 0,602055 | −1,7 % |
| 20×20 | 30 | 0,956000 | 0,944877 | −1,2 % |

Ces gains concernent les presets et la machine mesurés. Trois répétitions
n'établissent pas une garantie pour tous les modèles, et les écarts proches de
1–2 % sont modestes. Les deux variantes tournent dans le même processus Python,
avec le même ordre des ensembles symboliques. `PYTHONHASHSEED` n'était pas fixé :
une nouvelle invocation peut modifier cet ordre et les comptes de recherche,
mais l'équivalence avant/après est vérifiée dans chaque série. On ne compare
pas les temps absolus de deux séries indépendantes comme une même recherche.

## Coût des opérations

Audit séparé sur les 80 premiers nœuds, sans utiliser ses temps instrumentés :

| Mode / taille | Appels `retain_mask` avant | Sans effet avant | Appels après | Réductions effectives, chaque version |
|---|---:|---:|---:|---:|
| Natif 9×9 | 26 748 | 22 782 | 4 046 | 4 046 |
| Natif 16×16 | 83 413 | 65 899 | 17 594 | 17 594 |
| Conjoint exact 9×9 | 27 499 | 23 444 | 4 135 | 4 135 |
| Conjoint exact 16×16 | 83 415 | 65 899 | 17 596 | 17 596 |

Après optimisation, aucun appel audité n'est sans effet. Avant, l'affectation
singleton utilisait `retain` directement ; ses mutations sont comptées dans
la dernière colonne même si elles ne passent pas par `retain_mask`.

Le [microbenchmark](micro.json), sept répétitions par cas et version, isole
128 variables de 256 candidats. Construction et validation sont exclues.

| Cas | Avant, médiane | Après, médiane | Effet |
|---|---:|---:|---|
| 4 096 retraits d'un bit puis restauration | 4,558 ms | 2,952 ms | −35,2 % |
| 4 096 retraits, historique demandé tous les 128 événements | 4,075 ms | 5,148 ms | **+26,3 %** |
| 16 tours de 128 affectations singleton, statuts et restauration | 47,181 ms | 1,743 ms | environ 27× plus rapide |

Le dernier cas n'exige pas les explications des branches abandonnées. Il
mesure ensemble affectation, tests de statut et retour arrière, et ne prédit
pas un facteur 27 pour la résolution complète. Le décodage différé a un coût
quand le client demande constamment tout l'historique ; le préfixe déjà décodé
est réutilisé, mais ce cas reste plus lent. Les mesures de résolution ci-dessus
incluent bien la production des explications des solutions réussies.

## Vérification et provenance

- **1 241 tests non lents réussis**, 4 ignorés et 58 désélectionnés ;
  **56 tests lents réussis**, 3 ignorés et 1 244 désélectionnés.
- **111 tests expérimentaux SUM réussis**.
- Vingt nouveaux tests : 300 historiques aléatoires de 40 opérations, domaines
  symboliques et grands entiers signés, retours arrière imbriqués, branches
  sœurs, observations immuables, plans utilisés avec un autre magasin, absence
  d'appels sans effet, traces complètes sous MRV/dom_wdeg, objectifs min/max,
  règles mixtes et gardes hors portée.
- Mypy sur les 103 fichiers source, Ruff sur les fichiers modifiés et
  `git diff --check` réussissent.

Les [logs non lents](validation_core.txt), [lents](validation_slow.txt),
[expérimentaux](validation_experimental.txt) et [outils](validation_tools.txt)
conservent les sorties des vérifications. Les [sources figées](sources.tar.gz)
contiennent le runtime, les collecteurs, presets, tests et cinq étapes. Les
fichiers `.py.txt` évitent d'exécuter ou de linter les anciennes implémentations
comme du code courant.

Une première série avait laissé les références au modèle et à l'état du solve
précédent vivantes jusqu'au début du suivant. Leur libération pouvait alors
être incluse dans le temps de la nouvelle construction. Ses 225 exécutions
restent dans [initial_series](initial_series), mais leurs temps ne servent pas
aux tableaux finaux. La nouvelle série libère ces références et collecte les
cycles **hors chronométrage avant chaque exécution**. Cela ne change pas les
sources du solveur. La régression initiale 11×11 ne réapparaît pas dans la
comparaison native finale. Les audits et le microbenchmark sont conservés
séparément ; leurs conclusions ne dépendent pas de cette frontière entre solves.

## Filtre conjoint optionnel : comparaison finale

Le mode `exact` conserve son seuil de trois variables et 24 candidats actifs,
ainsi que son chemin rapide à deux variables. Cette comparaison avant/après
mesure les opérations de base, avec **les mêmes déductions conjointes**. Les
compteurs entiers du filtre sont également identiques ; seul son temps change.

| Taille | Avant | Après | Variation |
|---|---:|---:|---:|
| 6×6 | 0,046396 | 0,043136 | −7,0 % |
| 8×8 | 0,111355 | 0,104906 | −5,8 % |
| 9×9 | 1,883894 | 1,704555 | −9,5 % |
| 10×10 | 0,234353 | 0,222603 | −5,0 % |
| 11×11 | 0,400971 | 0,386861 | −3,5 % |
| 12×12 | 0,510483 | 0,496810 | −2,7 % |
| 13×13 | 0,774639 | 0,773603 | −0,1 % |
| 14×14 | 1,124372 | 1,110769 | −1,2 % |
| 16×16 | 5,239458 | 5,117558 | −2,3 % |
| 15×15 — préfixe 80 nœuds | 0,554462 | 0,531985 | −4,1 % |
| 18×18 — préfixe 30 nœuds | 0,612326 | 0,602860 | −1,5 % |
| 20×20 — préfixe 30 nœuds | 0,958494 | 0,943181 | −1,6 % |

13×13 est essentiellement inchangé. Cette série ne justifie pas d'activer le
filtre conjoint par défaut, ni d'affirmer une accélération uniforme pour tous
les modèles.

## Reproduire

Depuis la racine du projet, utiliser des répertoires de sortie neufs. Les
presets sauvegardés sont aussi conservés dans [presets.json](presets.json).

```sh
PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.domain_ops_benchmark \
  --sizes 6 8 9 10 11 12 13 14 15 16 18 20 --repeats 3 \
  --output generated/neural_attention/domain_ops_native_replay

PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.domain_ops_benchmark \
  --sizes 6 8 9 10 11 12 13 14 15 16 18 20 --mode exact --repeats 3 \
  --output generated/neural_attention/domain_ops_exact_replay

PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.domain_ops_benchmark \
  --sizes 8 9 13 16 --variants before records indexed delta after --repeats 3 \
  --output generated/neural_attention/domain_ops_ablation_replay

PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.domain_ops_benchmark \
  --sizes 9 16 --max-nodes 80 --repeats 1 --audit \
  --output generated/neural_attention/domain_ops_audit_replay

PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.domain_ops_micro \
  --output generated/neural_attention/domain_ops_micro_replay.json

.venv/bin/python -m pytest tests/test_domain_operations.py
```

Ajouter `--mode exact` à l'audit pour reproduire son autre mode. Le programme
compare toutes les données logiques et les explications dans chaque invocation
et vérifie les empreintes des sources à la fin. La vérification des carrés
rejoue chaque témoin indépendamment de la propagation.

## Contribution des étapes

Série native séparée, trois répétitions de chacune des cinq versions. Temps
médians en secondes ; les étapes sont cumulatives et la recherche reste
identique dans chaque ligne.

| Taille | Avant | Explications/statuts | Index | Masques modifiés | File finale |
|---|---:|---:|---:|---:|---:|
| 8×8 | 0,119886 | 0,118917 | 0,117190 | 0,110542 | 0,113072 |
| 9×9 | 2,175752 | 2,126270 | 2,068225 | 1,975772 | 1,983356 |
| 13×13 | 2,377978 | 2,348042 | 2,311089 | 2,210101 | 2,229918 |
| 16×16 | 6,683440 | 6,673264 | 6,593958 | 6,370734 | 6,333269 |

Éviter l'application des supports inchangés apporte ici le plus gros gain
supplémentaire. Le stockage indexé apporte un gain plus petit. L'effet marginal
de la nouvelle file est faible et mixte : légèrement plus lent sur trois tailles,
légèrement plus rapide sur 16×16. Il ne faut pas attribuer à chaque changement
isolé tout le gain de l'ensemble.

Les [données natives finales](final_series/native/summary.json),
[conjointes finales](final_series/exact/summary.json) et
[par étapes](final_series/ablation/summary.json) conservent tous les runs et
leurs temps, pas seulement les médianes. Chaque répertoire contient aussi
`runs.jsonl`, `frozen.json` et la version exacte du collecteur.

La [validation machine](validation.json) vérifie **429 exécutions complètes de
benchmark** : 204 finales et 225 initiales conservées pour provenance.
Elles contiennent **322 carrés validés indépendamment**, **107 préfixes limités
en nœuds** et aucun timeout. Les **42 mesures de composants** sont séparées.
« Exécution complète de benchmark » inclut un préfixe arrivé normalement à sa
limite et ne signifie pas que le problème a été résolu.

Les empreintes des sources de chaque série sont contrôlées, ainsi que
l'égalité des comptes, témoins, digests d'explications et statistiques conjointes
hors temps. Les snapshots `after` correspondent exactement au code courant.
Le [vérificateur d'origine](validate_evidence.py.txt) reste figé avec ses anciens
chemins. Depuis la racine du dépôt, vérifier les données déplacées avec
`.venv/bin/python scripts/check_benchmark_history.py --experiments magic_domain_ops_2026-10-13`.
Le [manifeste](source_manifest.json) donne aussi les empreintes des sources
archivées et du paquet de sources.
