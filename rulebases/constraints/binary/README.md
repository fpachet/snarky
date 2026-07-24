# Propagation de contraintes binaires

Cette base implémente une forme d'arc-consistance pour les contraintes
binaires tabulaires. Une valeur est retirée d'un domaine lorsqu'elle ne
possède plus aucun support compatible dans le domaine opposé.

Le groupe `propagate_binary_constraints` contient deux règles symétriques :

- `revise_left_domain` ;
- `revise_right_domain`.

Le groupe `classify_csp_domains` reconnaît les domaines singletons et retire
une ancienne affectation devenue invalide. `classify_csp_problems` détecte
ensuite les domaines vides et les problèmes entièrement affectés.

## Scénarios simultanés

### Chaîne bicolore

```text
chain-a != chain-b != chain-c != chain-d
```

`chain-a` ne possède que `red`; les autres variables commencent avec
`{red, blue}`. La propagation trouve sans recherche :

```text
chain-a = red
chain-b = blue
chain-c = red
chain-d = blue
```

### Triangle à trois couleurs

Les trois sommets sont reliés deux à deux. `triangle-a = red`; les deux autres
domaines commencent avec `{red, green, blue}`. La propagation retire `red`
des deux domaines mais laisse :

```text
triangle-b ∈ {green, blue}
triangle-c ∈ {green, blue}
```

Le problème est cohérent mais non résolu. Il constitue l'oracle du futur
protocole déclaratif de choix et de recherche.

### Paire impossible

Deux variables limitées toutes deux à `red` sont reliées par la contrainte
d'inégalité bicolore. La propagation vide les deux domaines et les règles
ajoutent :

```text
(impossible-pair state contradiction)
(impossible-pair empty_domain impossible-left)
(impossible-pair empty_domain impossible-right)
```

Ce troisième problème vérifie que le noyau distingue bien `solved`, point
fixe incomplet et contradiction.

## Exécution

```sh
uv run python -m rulebases.runner constraints/binary --trace
```

La base ne contient aucun algorithme CSP Python. Le moteur Snarky ne voit que
des faits, deux règles de propagation et des règles de classification.

## Efficacité actuelle

Sur les trois scénarios réunis, la stratégie semi-naïve atteint le point fixe
en huit cycles cumulés, 18 activations et environ 3,59 ms sur la machine de
référence. Elle est ×12,32 plus rapide que l'oracle naïf (44,19 ms) et
légèrement plus rapide que l'indexation exhaustive (3,72 ms).

Cette mesure est un test de coût minimal. Le benchmark paramétrique complète
désormais ce résultat : sur une chaîne de 64 variables et des domaines de 64
valeurs, le temps passe de 2,566 s à 1,684 s et les matchings de 560 196 à
310 212. Le gain vaut ×1,52 et la baisse de matching 44,6 %.

Le moteur construit à la demande deux index sur les chemins partiellement liés
de `SEQ[left right]`, commence la recherche existentielle par le plus petit
bucket, conserve au plus deux supports alternatifs et utilise une
représentation de retrait adaptée aux grandes mémoires. Ces mécanismes sont
généraux : ils ne connaissent ni `candidate`, ni `allows`, ni la notion de
CSP.

Le protocole reproductible et les résultats détaillés se trouvent dans
[`benchmarks/constraint_propagation.py`](../../../benchmarks/constraint_propagation.py)
,
[`benchmarks/constraint_scaling.py`](../../../benchmarks/constraint_scaling.py)
et
[`benchmarks/constraint_support_churn.py`](../../../benchmarks/constraint_support_churn.py).
Les mesures A/B sont conservées dans
[`benchmarks/results/constraint_indexing_optimizations_2026-07-24.csv`](../../../benchmarks/results/constraint_indexing_optimizations_2026-07-24.csv).
