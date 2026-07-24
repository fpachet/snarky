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
en huit cycles cumulés, 18 activations et environ 3,30 ms sur la machine de
référence. Elle est ×13,28 plus rapide que l'oracle naïf (43,82 ms) et
légèrement plus rapide que l'indexation exhaustive (3,40 ms).

Cette mesure est un test de coût minimal, pas encore un résultat de passage à
l'échelle. La table d'une relation peut contenir `d²` couples et les
prémisses `NOT EXISTS` recherchent un support compatible après les retraits.
Il faudra donc mesurer des chaînes, graphes et domaines de taille croissante
avant de décider si le moteur général suffit ou s'il faut une file de
propagation et des supports résiduels spécialisés.

Le protocole reproductible et les résultats détaillés se trouvent dans
[`benchmarks/constraint_propagation.py`](../../../benchmarks/constraint_propagation.py)
et
[`benchmarks/results/constraint_propagation_2026-07-24.csv`](../../../benchmarks/results/constraint_propagation_2026-07-24.csv).
