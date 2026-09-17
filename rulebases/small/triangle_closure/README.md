# Fermeture incrémentale de triangles

Cette petite base illustre une règle conjonctive alimentée par événements.
Un hub connaît des nœuds gauches et droits. Un arc entre un nœud gauche et
un nœud droit ferme un triangle :

```snarky
RULE close_triangle
WHEN
    ($hub left $left)
    ($hub right $right)
    $left != $right
    ($left edge $right)
THEN
    ADD ($hub triangle SEQ[$left $right])
END
```

La comparaison est déjà liée par les deux premières prémisses. Snarky peut
donc compiler la règle en gestionnaire delta factorisé : lorsqu'un fait
`edge` arrive, il fournit directement `$left` et `$right`, puis deux recherches
indexées retrouvent le hub. Aucun produit de toutes les paires gauche/droite
n'est matérialisé.

Exécution complète de l'oracle :

```sh
uv run python -m rulebases.runner small/triangle_closure --trace
```

Le runner charge ici les deux arcs avec les faits initiaux afin de garder un
scénario autonome. Le benchmark
[`claire_triangle_closure`](../../../benchmarks/claire_triangle_closure.py)
prépare d'abord les appartenances, puis ajoute chaque arc séparément pour
mesurer le chemin événementiel et le comparer à CLAIRE4.

La spécialisation est conservatrice. Si une comparaison emploie une variable
qui n'était pas liée à sa position textuelle, si la règle contient une
prémisse négative ou agrégée, ou si le delta comporte une suppression, le
moteur utilise automatiquement le chemin général.
