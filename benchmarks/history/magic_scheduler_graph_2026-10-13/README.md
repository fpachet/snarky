# Choix de variable, ordre de propagation et graphe ALLDIFF

Expérience du **13 octobre 2026**, sur le solveur commité `b8e06c1`, après
les [optimisations des opérations de domaines](../magic_domain_ops_2026-10-13/README.md).

**Résultat retenu : l'agrégation sélective du graphe ALLDIFF est activée.**
Les médianes natives diminuent de 11,8 % sur 8×8, 20,8 % sur 11×11 et 13,8 %
sur 16×16, avec les mêmes recherches et explications. 9×9 gagne seulement 1 %.
Les totaux dom/wdeg et les deux files restent expérimentaux. Les tableaux
ci-dessous séparent résolutions complètes, filtre conjoint optionnel et préfixes.

## Les trois idées testées

1. **Totaux dom/wdeg.** Remplacer la somme des poids incidents recalculée à
   chaque décision par un total par variable. Un échec incrémente les totaux
   des variables de la contrainte responsable. Ces totaux restent globaux
   entre branches, exactement comme les poids précédents. Les portées sont
   dédupliquées ; les coupes d'objectif hors modèle ne créent pas de poids.
2. **Propagation en deux files.** Traiter d'abord les contraintes ordinaires,
   dont SUM, puis ALLDIFF. Toute réduction réactive les deux familles ; la
   propagation atteint toujours son point fixe avant le choix d'une variable.
   Les gardes et coupes d'objectif restent prises en compte. L'ordre des
   explications et la contrainte détectant un échec peuvent changer, donc
   dom/wdeg peut explorer une recherche différente.
3. **Construction du graphe ALLDIFF.** Tester l'agrégation des lignes identiques
   et l'émission des arêtes manquantes pour les lignes denses. Les graphes et
   supports restent exacts. Matching et composantes fortement connexes sont
   inchangés ; aucun témoin de support ou état de branche n'est mémorisé.

Les étapes figées sont `before`, `weights`, `batch`, `group`, `complement`,
`graph` (groupement + complément), `weights_group`, `weights_graph`, `combined`
(poids + deux files + graphe), `selective` et `weights_selective`.

Dans `selective`, les lignes d'au plus **huit candidats** émettent leurs arêtes
comme auparavant. Les autres sont groupées par masque de domaine. Pour des
sources ayant le même masque, une seule opération OR par destination suffit
pour ajouter tous les bits sources au graphe inverse. Cela produit exactement
la transposée obtenue en visitant chaque arête séparément. La table des groupes
est reconstruite depuis les masques courants à chaque appel et n'est jamais
réutilisée entre révisions ou branches.

## Protocole

Versions cohérentes de domaines, plans numériques, ALLDIFF, propagation,
coordinateur mixte et recherche chargées dans des espaces de modules séparés.
Les modèles immuables et kernels inchangés sont partagés. Le prototype conjoint
optionnel est lié à la classe native de chaque version.

Les runs sont **séquentiels**, dans un ordre mélangé déterministe, avec
`PYTHONHASHSEED=0` et les presets sauvegardés. Le temps inclut construction du
modèle, compilation, recherche et explications des solutions. Imports,
validation indépendante, libération du run précédent et collecte des cycles
avant le suivant sont exclus. Audits, profils et microbenchmarks sont séparés.

Les versions de poids et de graphe exigent des résultats logiques et des
explications exactement identiques, y compris comptes de recherche. Pour les
deux files, chaque solution est validée et les ensembles complets de solutions
sont comparés sur de petits modèles ; on ne prétend pas préserver la recherche.
15×15, 18×18 et 20×20 restent des préfixes limités en nœuds.

## Premier tri et attribution

Les [40 runs pilotes](pilot/summary.json) servent au tri des candidats, pas à
annoncer une précision issue de répétitions. Le [profil séparé](profile)
confirme un coût important dans `AllDifferentPlan.supports` : pour le préfixe
16×16 de 80 nœuds, 163 appels et environ 4,96 millions d'appels à `bit_length`
dans l'ensemble du profil. Les temps sous cProfile ne sont pas des temps de
résolution ordinaires.

La première comparaison répétée sépare les totaux de poids du groupement,
avec trois runs par version. Médianes en secondes :

| Taille | Avant | Poids | Groupement | Poids + groupement |
|---|---:|---:|---:|---:|
| 8×8 | 0,110444 | 0,109895 | 0,098466 | 0,098685 |
| 9×9 | 1,955623 | 1,956244 | 1,947094 | 1,956776 |
| 11×11 | 0,435004 | 0,425352 | 0,344917 | 0,343228 |
| 13×13 | 2,095250 | 2,088933 | 1,919951 | 1,926788 |
| 16×16 | 6,205426 | 6,190362 | 5,578371 | 5,615699 |

Le gain des poids seuls reste faible : environ 2,2 % sur 11×11 et 0–0,5 % sur
les autres tailles de cette série. Le groupement apporte l'essentiel du gain.
Les deux mécanismes ne doivent pas recevoir chacun le crédit du gain combiné.

## Ordre de propagation : résultat mixte

Les deux files sont correctes dans les tests mais changent les causes d'échec
et l'ordre de recherche. Dans le pilote natif :

| Taille | Nœuds avant | Nœuds deux files | Temps avant | Temps deux files |
|---|---:|---:|---:|---:|
| 9×9 | 2 962 | 2 962 | 1,957 s | 1,765 s |
| 11×11 | 258 | 321 | 0,429 s | 0,454 s |
| 13×13 | 1 488 | 5 011 | 2,118 s | 5,530 s |
| 16×16 | 2 536 | 2 854 | 6,358 s | 5,827 s |

Ces temps pilotes proviennent d'un seul run par variante. Ils montrent une
régression importante sur 13×13 et ne justifient pas une activation générale.
Une hausse des révisions SUM peut accompagner une baisse des appels ALLDIFF.
Les versions à deux files sont conservées comme expériences optionnelles.

## Changement retenu dans le solveur

**Seule la construction sélective du graphe ALLDIFF est activée.** Les totaux
pondérés, les deux files et la variante par complément restent des expériences
archivées. La recherche, son heuristique, les supports, les causes et l'ordre
normal de propagation ne changent pas. Les presets restent inchangés.

Le microbenchmark distingue les domaines répétés des domaines tous différents.
Grouper toutes les petites lignes ajoute environ 9–18 % au seul coût de
construction dans les cas synthétiques clairsemés. La sélection à huit
candidats ramène ce surcoût à environ 1–3 %, tout en gardant les gros gains
sur les lignes larges répétées. Ce seuil est un compromis empirique, pas une
nouvelle règle de filtrage ; il ne peut changer les supports.

### Résolution native

Médianes de trois runs avant/après. Les cinq tailles principales viennent de
[selective_runs](selective_runs/summary.json) ; les autres de
[controls](controls/summary.json). Les comparaisons sont appariées au sein de
chaque série. Les nœuds, échecs, révisions et explications restent identiques.

| Taille | Avant | Après sélection | Variation |
|---|---:|---:|---:|
| 6×6 | 0,046262 s | 0,043516 s | −5,9 % |
| 8×8 | 0,110352 s | 0,097281 s | −11,8 % |
| 9×9 | 1,949828 s | 1,930853 s | −1,0 % |
| 10×10 | 0,254033 s | 0,203072 s | −20,1 % |
| 11×11 | 0,426527 s | 0,337799 s | −20,8 % |
| 12×12 | 0,521806 s | 0,361576 s | −30,7 % |
| 13×13 | 2,088857 s | 1,841803 s | −11,8 % |
| 14×14 | 1,125839 s | 0,749134 s | −33,5 % |
| 16×16 | 6,171570 s | 5,320453 s | −13,8 % |

Préfixes uniquement, **aucune solution dans ces runs** :

| Taille | Limite | Avant | Après sélection | Variation |
|---|---:|---:|---:|---:|
| 15×15 | 80 nœuds | 0,527715 s | 0,161034 s | −69,5 % |
| 18×18 | 30 nœuds | 0,598276 s | 0,219283 s | −63,3 % |
| 20×20 | 30 nœuds | 0,940089 s | 0,325288 s | −65,4 % |

Le gain dépend surtout du nombre de domaines larges identiques, souvent en
début de recherche. Il ne croît pas simplement avec la taille du carré : les
états tardifs du 9×9 bénéficient peu du groupement. Les faibles écarts de 1–2 %
restent modestes avec trois répétitions, et ces presets ne garantissent pas
les mêmes gains sur d'autres CSP ou des carrés partiellement remplis.

### Avec le filtre conjoint exact optionnel

Mêmes trois répétitions, paramètres et déductions conjointes identiques :

| Taille | Avant | Après sélection | Variation |
|---|---:|---:|---:|
| 8×8 | 0,105458 s | 0,092080 s | −12,7 % |
| 9×9 | 1,707987 s | 1,676740 s | −1,8 % |
| 11×11 | 0,418345 s | 0,327859 s | −21,6 % |
| 13×13 | 0,755692 s | 0,523022 s | −30,8 % |
| 16×16 | 5,074033 s | 4,116761 s | −18,9 % |

Ces chiffres sont des effets du graphe à travail identique dans chaque paire.
Comparer directement la colonne native et la colonne conjointe mélangerait
ce gain avec la différence de filtrage et de recherche entre les deux modes.
Le filtre conjoint reste optionnel.

## Mécanisme et coûts séparés

L'[audit](audit/runs.jsonl) des 80 premiers nœuds compare les appels, sans
utiliser ses temps instrumentés comme résultats de performance :

| Taille | ALLDIFF avant/sélection | ALLDIFF deux files | SUM avant/sélection | SUM deux files |
|---|---:|---:|---:|---:|
| 9×9 | 196 | 130 | 1 384 | 1 828 |
| 13×13 | 161 | 159 | 2 140 | 2 357 |
| 16×16 | 163 | 158 | 2 646 | 2 884 |

Le graphe sélectif réduit le coût de chaque construction et conserve les mêmes
appels. Les deux files échangent des appels ALLDIFF contre des appels SUM,
avec un effet dépendant du modèle et de la recherche.

Les profils 16×16 avant/après conservent 163 révisions ALLDIFF, mais les appels
à `bit_length` dans tout le profil passent de 4 958 279 à 459 497. Le temps propre
instrumenté de `AllDifferentPlan.supports` passe d'environ 0,972 s à 0,021 s.
Cette attribution décrit seulement les 80 premiers nœuds, et inclut l'effet du
profilage. Le gain du solve complet est celui du tableau non instrumenté.

Le [microbenchmark initial](micro_initial.json) compare émission normale,
groupement, complément et combinaison. Le [microbenchmark sélectif](micro_selective.json)
ajoute la sélection des petites lignes. Les mêmes graphes directs, inverses,
masques de valeurs appariées et comptes d'arêtes sont exigés. Les cas couvrent
32/128/256 valeurs, domaines pleins, blocs répétés, domaines clairsemés/moyens/
denses tous différents et univers avec valeurs libres et indices inutilisés.
Chaque mesure répète 20 constructions, avec sept mesures par cas et variante.
Aucune accélération de composant n'est présentée comme celle du solveur entier.

## Vérification, sources et reproduction

La [validation machine](validation.json) contrôle les **245 exécutions** et
leurs empreintes de sources, dont **214 carrés validés indépendamment**,
**31 préfixes limités en nœuds**, aucun timeout, et les médianes recalculées.
Les 192 runs répétés (`main`, `selective_runs`, `exact`, `controls`) sont
séparés des 40 runs pilotes et des 13 runs d'audit/profilage. Les **1 008 mesures
de composants** sont encore séparées et ne sont pas des résolutions.

Les tests couvrent les supports exacts, le matching après rétrécissement et
restauration, les grands graphes à lignes répétées/denses/clairsemées, des
alphabets réordonnés, les indices de valeurs inutilisés, les traces complètes
MRV/dom_wdeg et les objectifs min/max. Les expériences à deux files comparent
points fixes et ensembles complets de solutions sur de petits modèles, avec
règles mixtes, gardes et coupes d'objectif.

Un nouveau test du solveur contrôle le graphe inverse réellement fourni à la
traversée, en le comparant à une transposition indépendante arête par arête,
sur des masques répétés et uniques et des branches restaurées. Les tests
existants comparent également les supports à l'oracle d'énumération et au
propagateur de référence.

Les [sources de départ](baseline_sources.tar.gz), [sources mesurées et finales](sources.tar.gz),
[patch de production](production.patch) et [presets](presets.json) sont conservés.
Chaque répertoire de mesure contient `frozen.json`, `runs.jsonl`, `summary.json`,
`equivalence.json` et son collecteur exact sous forme `.py.txt`. Les variantes
source restent également des `.py.txt` pour éviter leur exécution accidentelle
ou leur inclusion dans le lint du code courant.

Depuis la racine du projet, utiliser des sorties neuves :

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.scheduler_graph_benchmark \
  --variants before weights group weights_group --sizes 8 9 11 13 16 --repeats 3 \
  --output generated/neural_attention/scheduler_graph_scores_replay

PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.scheduler_graph_benchmark \
  --variants before group selective weights_selective --sizes 8 9 11 13 16 --repeats 3 \
  --output generated/neural_attention/scheduler_graph_native_replay

PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.scheduler_graph_benchmark \
  --variants before selective --sizes 8 9 11 13 16 --mode exact --repeats 3 \
  --output generated/neural_attention/scheduler_graph_exact_replay

PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.scheduler_graph_benchmark \
  --variants before selective --sizes 6 10 12 14 15 18 20 --repeats 3 \
  --output generated/neural_attention/scheduler_graph_controls_replay

PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.scheduler_graph_benchmark \
  --variants before batch selective --sizes 9 13 16 --max-nodes 80 --repeats 1 --audit \
  --output generated/neural_attention/scheduler_graph_audit_replay

PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python -m experiments.neural_attention.scheduler_graph_micro \
  --output generated/neural_attention/scheduler_graph_micro_replay.json

PYTHONHASHSEED=0 .venv/bin/python -m pytest experiments/neural_attention/test_scheduler_graph.py
.venv/bin/python scripts/check_benchmark_history.py --experiments magic_scheduler_graph_2026-10-13
```

Les deux files peuvent être testées à solution complète en remplaçant les
variantes par `before batch combined`, sans `--max-nodes`. Pour un profil séparé,
utiliser `--variants before selective --sizes 9 16 --max-nodes 80 --repeats 1
--profile --audit` et un autre répertoire. Les temps de ces profils et audits
restent exclus des tableaux de performance.

### Résultats des vérifications finales

- [Non lents](validation_core.txt) : **1 242 réussis**, 4 ignorés,
  58 désélectionnés, 28,38 s.
- [Lents](validation_slow.txt) : **56 réussis**, 3 ignorés,
  1 245 désélectionnés, 162,45 s. Total : **1 298 tests core réussis**.
- [Nouveaux prototypes et couplage](validation_experimental.txt) : **104 réussis** ;
  [autres expériences SUM](validation_experimental_other.txt) : **37 réussis**.
  Total : **141 tests expérimentaux réussis**, dont 30 nouveaux tests de cette
  expérience et les 111 tests SUM existants.
- [Outils](validation_tools.txt) : Ruff sur les fichiers modifiés, mypy sur les
  103 fichiers source, liens Markdown et `git diff --check` réussissent.

Le [vérificateur d'origine](validate_evidence.py.txt) conserve les contrôles
effectués sur le code de l'expérience, avec ses anciens chemins. Le
[vérificateur actuel](../../../scripts/check_benchmark_history.py) contrôle les
sources archivées, les données et les témoins après déplacement du répertoire,
sans exiger que le solveur courant corresponde à une version historique.
Le [manifeste](source_manifest.json) conserve les empreintes des sources,
archives et patch.
