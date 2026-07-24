# Ensemble de conflit et stratégie MEA

Par défaut, Snarky conserve son exécution déterministe : les règles sont
visitées dans leur ordre source et toutes leurs activations éligibles sont
déclenchées pendant le cycle.

Une session peut maintenant recevoir une `ConflictResolutionStrategy`. Dans ce
mode, le moteur :

1. maintient l’ensemble complet des activations courantes ;
2. écarte les activations réfractées ou dont un support a disparu ;
3. demande à la stratégie d’en choisir exactement une ;
4. journalise ce choix ;
5. exécute l’activation ;
6. invalide et recalcule les seules règles potentiellement touchées.

Le mode explicite ne modifie donc jamais la sémantique par défaut.

## `MEAConflictStrategy`

MEA signifie *means-ends analysis*. La stratégie implémentée suit les critères
OPS décrits dans la thèse :

1. fraîcheur du fait filtré par la prémisse `FOCUS`, ou par la première
   prémisse factuelle si aucun focus n'est déclaré ;
2. vecteur LEX décroissant des `timeTag` de tous les supports ;
3. nombre de prémisses de la règle ;
4. ordre textuel de la règle et de l’activation.

Chaque fait initial reçoit un `timeTag` suivant son ordre d’insertion. Un ajout
effectif reçoit le prochain numéro ; un fait retiré perd son numéro et une
réinsertion est donc fraîche.

Pour obtenir une fraîcheur locale des buts, une base marque explicitement la
prémisse correspondante :

```text
RULE solve_subgoal
WHEN
    FOCUS ($goal status active)
    ...
THEN
    ...
END
```

Une règle accepte au plus un `FOCUS`, nécessairement au premier niveau. Un
sous-but nouvellement créé est ainsi choisi avant son parent encore actif,
sans imposer l'ordre des autres jointures. Ce contrôle n’est ni du
backtracking, ni une recherche par hypothèses.

## API

```python
from snarky import ForwardEngine, MEAConflictStrategy

session = ForwardEngine(
    (),
    conflict_strategy=MEAConflictStrategy(),
).create_session(initial_facts)
session.run_group(group)
```

Chaque choix produit un `AgendaSelection` accessible dans le résultat et dans
`session.agenda_selections`. Il contient la règle, la substitution, les
supports, le fait de focus, son `timeTag`, le vecteur LEX et le cycle.

`session.inspect_agenda(group)` expose les candidats sans en choisir.
`session.agenda_metrics` compte les reconstructions initiales, les règles
recalculées et les règles réutilisées.

Avec une stratégie de conflit, `ONE_CYCLE` signifie une sélection d’agenda.
`FIRST_CHANGE` et `UNTIL` restent évalués après une activation atomique.

## Maintenance incrémentale

La première visite matérialise les activations de chaque règle. Après une
mutation, un index conservatif des constantes factuelles désigne les règles
susceptibles d'être affectées. Les lignes inchangées sont réutilisées ; les
lignes touchées reçoivent le `FactDelta` et profitent des index, watchers et
mémoires de jointures de la stratégie d'instanciation.

MEA doit toujours comparer le conflit complet pour garantir son ordre. Le gain
porte donc sur le matching et la construction des activations, pas sur la
lecture finale des candidats. Le benchmark
`python -m benchmarks.agenda_incremental` mesure séparément ces deux coûts.

MEA est une stratégie publique écrite en Python, pas une méta-base de règles
inspectant réflexivement l’agenda. La fraîcheur locale est exprimée par
`FOCUS`; `type_hierarchy_group()` couvre séparément l'héritage explicable.

Le cas complet est
[`monkey_bananas/neopus_mea`](../rulebases/thesis/monkey_bananas/neopus_mea/README.md).
