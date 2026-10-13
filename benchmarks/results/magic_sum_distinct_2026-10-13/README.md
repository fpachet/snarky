# Couplage SUM + ALLDIFF : bornes distinctes

Expérience du **13 octobre 2026**. Le solveur de production reste inchangé.

**Résultat : le filtrage sélectif apporte des gains mesurables.** La variante
limitée aux deux ou trois variables restantes résout le 13×13 en **0,92 s** contre
**2,36 s**, et le 16×16 en **6,39 s** contre **6,72 s**. Ce n'est pas une
amélioration universelle : 6×6 et 11×11 régressent légèrement avec cette variante.
Les bornes générales, appliquées largement, coûtent trop cher dans le premier
essai. Aucun réglage de recherche ni code de production n'a été remplacé.

## Principe et sécurité

Le prototype intervient dans la révision numérique, immédiatement après le
filtrage SUM natif. Il ne traite que les sommes entières à coefficients tous
égaux à +1, couvertes entièrement par un ALLDIFF inconditionnel du modèle.
Un ALLDIFF partiel ou gardé ne suffit pas. Les autres contraintes et les sommes
sans plan numérique compilé conservent leur comportement natif.

Après soustraction des contributions fixées et exclusion de leurs valeurs :

- Pour chaque candidat `v`, prendre les `k` plus petites et plus grandes valeurs
  distinctes de **l'union complète des domaines des autres variables**, sans `v`.
- Si la cible restante est hors de cet intervalle, supprimer `v`.
- Ces bornes sont conservatrices : elles ne garantissent pas que les valeurs
  extrêmes puissent être réparties entre les variables. Elles ne revendiquent
  donc pas une cohérence complète de la contrainte combinée.

Le cas à deux variables utilise une règle exacte et moins coûteuse :

```text
x + y = R, x ≠ y  ⇒  retirer R/2 des deux domaines, si R est pair.
```

La variante rapide trouve directement cette valeur dans les index numériques
existants. Elle évite de parcourir les domaines et ne construit pas d'union.
Les valeurs fixées hors de ce cas spécialisé continuent d'être traitées par le
ALLDIFF natif. La valeur de `R` est toujours recalculée pour la branche courante.

Un exemple vérifié dans Snarky montre l'apport du couplage : avec trois domaines
`{1,2,3,4}`, SUM=6 et ALLDIFF, les propagateurs séparés gardent 4. Les bornes
distinctes le suppriment, puisque `4+1+2 > 6`.

Cela explique aussi pourquoi ce filtrage peut réussir après les expériences de
rang linéaire : une équation peut conserver des variables libres, tout en ayant
des **valeurs particulières incompatibles avec l'unicité**.

Les réductions utilisent les masques, la pile de restauration et la file
d'événements natives. Aucun support, témoin ou résultat de filtrage n'est mis en
cache par le prototype. Le tuple de supports que SUM vient de calculer est
utilisé directement dans la révision en cours, sans modifier NumericPlan.

## Variantes comparées

| Nom dans les données | Filtrage |
|---|---|
| `baseline` | Solveur natif actuel |
| `fast_pair` | Règle spécialisée à deux variables non fixées |
| `tiny` | `fast_pair`, plus bornes distinctes pour trois variables avec au plus 24 candidats au total |

Le seuil de 24 concerne seulement les trois variables. Le cas à deux variables
reste actif quelle que soit la taille de leurs domaines. Ces seuils sont fixes
pour toutes les tailles, choisis après les essais exploratoires ; ils ne sont
pas présentés comme optimaux.

## Comparaison principale : temps de résolution

Médianes de **trois répétitions par variante**. Les 108 exécutions sont
séquentielles et leur ordre est mélangé de façon déterministe. Le temps comprend
la création du modèle, de l'état et des index, ainsi que toute la recherche.
Les imports et la validation indépendante des résultats sont exclus.

Chaque taille utilise ses paramètres sauvegardés, identiques entre variantes :
heuristique, ordre des valeurs et des variables, graine et symétries. Les sommes
et le ALLDIFF du modèle sont conservés.

| Carré | Natif | Deux variables | Deux ou trois variables |
|---|---:|---:|---:|
| 6×6 | 0,054971 s | 0,055307 s | 0,055688 s |
| 8×8 | 0,128476 s | 0,119120 s | 0,125389 s |
| 9×9 | 2,241288 s | 2,263617 s | 2,144643 s |
| 10×10 | 0,268157 s | 0,269637 s | 0,256682 s |
| 11×11 | 0,462042 s | 0,526393 s | 0,469379 s |
| 12×12 | 0,555161 s | 0,547030 s | 0,550855 s |
| 13×13 | 2,356629 s | 0,943783 s | 0,918941 s |
| 14×14 | 1,213744 s | 1,178846 s | 1,163556 s |
| 16×16 | 6,722612 s | 6,832413 s | 6,385560 s |

Pour `tiny`, la baisse de temps est d'environ 4,3 % sur 9×9 et 10×10, 61 % sur
13×13, et 5,0 % sur 16×16. Les régressions sont d'environ 1,3 % sur 6×6 et 1,6 %
sur 11×11. Les petits écarts restent sensibles au bruit de mesure ; le gain
13×13 est accompagné d'une forte baisse du travail de recherche.

## Travail de recherche

Les compteurs et les carrés retournés sont identiques entre répétitions d'une
même variante. Ils peuvent différer entre variantes, puisque le filtrage modifie
les domaines et donc les choix de recherche.

| Carré | Nœuds natifs | Nœuds deux variables | Nœuds deux ou trois variables |
|---|---:|---:|---:|
| 6×6 | 90 | 87 | 80 |
| 8×8 | 161 | 139 | 130 |
| 9×9 | 2 962 | 2 924 | 2 535 |
| 10×10 | 246 | 245 | 213 |
| 11×11 | 258 | 321 | 232 |
| 12×12 | 182 | 177 | 176 |
| 13×13 | 1 488 | 372 | 343 |
| 14×14 | 219 | 219 | 209 |
| 16×16 | 2 536 | 2 535 | 2 204 |

Dans une exécution `tiny`, le prototype applique 1 898 retraits de valeurs sur
9×9, 117 sur 13×13 et 1 361 sur 16×16. Il détecte respectivement 349, 28 et 194
contradictions. Ce sont des occurrences au cours de la recherche, incluant les
branches abandonnées, et non des valeurs distinctes supprimées définitivement.
Certains retraits auraient aussi pu être obtenus par un propagateur natif déjà
en attente ; ces compteurs ne mesurent pas seuls le gain marginal au point fixe.

Le compteur `removed_values` compte les retraits effectivement appliqués.
`bound_removals`, `pair_removals` et `fixed_exclusions` incluent aussi les tests
d'exclusion dans les révisions se terminant par une contradiction : leur somme
peut donc dépasser `removed_values`.

## Préfixes bornés : pas de solution mesurée

Ces exécutions ne sont **pas des temps de résolution**. Aucun carré n'est
retourné et aucun retrait supplémentaire n'est appliqué dans ces préfixes.

| Carré | Limite | Natif | Deux variables | Deux ou trois variables |
|---|---:|---:|---:|---:|
| 15×15 | 80 nœuds | 0,569115 s | 0,585518 s | 0,567948 s |
| 18×18 | 30 nœuds | 0,625082 s | 0,647929 s | 0,650321 s |
| 20×20 | 30 nœuds | 0,992215 s | 0,974598 s | 0,981633 s |

Les variations de temps dans ces lignes n'établissent aucun gain de filtrage.

## Essais exploratoires : pourquoi limiter le déclenchement ?

Un premier essai unique par configuration compare aussi les bornes sans limite
(`all`) et une limite de quatre variables/128 candidats (`small`). Ces versions
précèdent l'optimisation de la règle à deux variables et la réutilisation directe
du tuple que SUM vient de calculer. Elles ont leurs propres sources figées.

| Carré | Natif | Bornes sans limite | Nœuds natifs → sans limite |
|---|---:|---:|---:|
| 6×6 | 0,051656 s | 0,086945 s | 90 → 78 |
| 8×8 | 0,126969 s | 0,224620 s | 161 → 130 |
| 9×9 | 2,209779 s | 5,470994 s | 2 962 → 4 723 |
| 11×11 | 0,455025 s | 1,113284 s | 258 → 275 |
| 12×12 | 0,549767 s | 1,910287 s | 182 → 476 |

Le calcul large coûte cher. Un filtrage plus fort peut aussi augmenter les nœuds
avant la première solution : les domaines modifiés font choisir d'autres
variables à MRV ou dom_wdeg. 9×9 illustre cet effet même avec MRV, sans poids
d'échecs. La version limitée réduit ce coût, sans garantir que chaque taille
profite de la nouvelle trajectoire de recherche.

## Validation, portée et décision

**22 tests expérimentaux passent**, notamment :

- 400 cas de supports comparés à toutes les affectations distinctes possibles ;
- 60 petits problèmes avec ALLDIFF global et somme locale, chacun vérifié avec
  cinq configurations, soit 300 comparaisons exhaustives ;
- conservation des huit carrés magiques 3×3 avec trois configurations ;
- domaines troués, valeurs intérieures essentielles, valeurs négatives,
  translations de `10**40`, ordre d'alphabet différent et branches sœurs ;
- exclusion des ALLDIFF gardés/partiels et des sommes à coefficients signés.

Les 108 exécutions principales et les 32 essais exploratoires produisent
**113 carrés indépendamment validés**, sans dépassement de temps. Chaque variante
répétée conserve ses compteurs et son résultat. Les sources et les paramètres
sont figés par SHA-256. Ruff et les liens Markdown passent. La suite complète
du cœur n'a pas été relancée : aucun fichier sous `src/snarky` n'a changé.

Les échecs du couplage général n'ont pas de propriétaire SUM/ALLDIFF unique.
Le prototype leur donne une cause expérimentale qui n'incrémente aucun poids
original dom_wdeg. Cette convention fait partie de la variante mesurée ; les
effets heuristiques ne sont pas séparés des effets de propagation. `fast_pair`
ne produit pas d'échec direct : il retire seulement une valeur de domaines ayant
au moins deux candidats.

**Décision : conserver ces variantes en mode expérimental.** Le cas à deux
variables et les bornes très sélectives méritent davantage d'attention ; ajouter
les bornes partout n'est pas justifié. Aucun paramètre sauvegardé ni comportement
par défaut n'est modifié. L'essai porte sur des carrés vides et des paramètres
déjà sélectionnés : il ne constitue pas une validation sur des instances clouées
indépendantes. Les bornes fortes par matching de coût minimum/maximum n'ont pas
été implémentées dans cette expérience.

## Données et reproduction

- [Résumé complet](summary.json) et [validation](validation.json)
- [108 exécutions principales](comparison/runs.jsonl),
  [médianes et compteurs](comparison/summary.json),
  [sources, paramètres et ordre d'exécution](comparison/frozen.json)
- [Premier essai exploratoire](pilot/runs.jsonl) et
  [essai des déclenchements sélectifs avant optimisation](fast_pilot/runs.jsonl)
- [Prototype figé](sum_distinct.py.txt),
  [collecteur](magic_sum_distinct_benchmark.py.txt),
  [tests](test_sum_distinct.py.txt)
- [Prototype actuel](../../../experiments/neural_attention/sum_distinct.py)
  et [tests](../../../experiments/neural_attention/test_sum_distinct.py)

Chaque répertoire de comparaison contient ses propres sources exactes, y compris
les versions intermédiaires. Les sources de production sont celles de `edfe3c9`.
Les temps incluent l'instrumentation du prototype ; le compteur interne `seconds`
exclut certains contrôles de déclenchement et ne représente pas son coût total.

Depuis la racine du dépôt, choisir un nouveau répertoire de sortie :

```sh
PYTHONHASHSEED=0 PYTHONPATH=src:. .venv/bin/python \
  -m experiments.neural_attention.magic_sum_distinct_benchmark \
  --sizes 6 8 9 10 11 12 13 14 15 16 18 20 \
  --variants baseline fast_pair tiny --repeats 3 --limit 30 \
  --presets benchmarks/results/magic_sum_distinct_2026-10-13/presets.json \
  --output generated/neural_attention/sum_distinct_NEW

.venv/bin/pytest experiments/neural_attention/test_sum_distinct.py
```

## Suite : coût du déclenchement et des petits cas

Le [rapport suivant](../magic_sum_distinct_cost_2026-10-13/README.md) conserve les
mêmes réductions et recherches, avec un déclenchement arrêté plus tôt et une
spécialisation à trois variables par bitsets bornés. Les sources de cette
première comparaison restent figées ici ; le code actuel inclut cette suite.
