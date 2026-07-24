# Ensemble de conflit et stratégie MEA

Par défaut, Snarky conserve son exécution déterministe : les règles sont
visitées dans leur ordre source et toutes leurs activations éligibles sont
déclenchées pendant le cycle.

Une session peut maintenant recevoir une `ConflictResolutionStrategy`. Dans ce
mode, le moteur :

1. construit l’ensemble complet des activations courantes ;
2. écarte les activations réfractées ou dont un support a disparu ;
3. demande à la stratégie d’en choisir exactement une ;
4. journalise ce choix ;
5. exécute l’activation ;
6. reconstruit l’ensemble de conflit sur le nouvel état.

Le mode explicite ne modifie donc jamais la sémantique par défaut.

## `MEAConflictStrategy`

MEA signifie *means-ends analysis*. La stratégie implémentée suit les critères
OPS décrits dans la thèse :

1. fraîcheur du fait filtré par la première prémisse factuelle ;
2. vecteur LEX décroissant des `timeTag` de tous les supports ;
3. nombre de prémisses de la règle ;
4. ordre textuel de la règle et de l’activation.

Chaque fait initial reçoit un `timeTag` suivant son ordre d’insertion. Un ajout
effectif reçoit le prochain numéro ; un fait retiré perd son numéro et une
réinsertion est donc fraîche.

Pour obtenir une fraîcheur locale des buts, une base place le statut du but en
première prémisse :

```text
RULE solve_subgoal
WHEN
    ($goal status active)
    ...
THEN
    ...
END
```

Un sous-but nouvellement créé est ainsi choisi avant son parent encore actif.
Ce contrôle n’est ni du backtracking, ni une recherche par hypothèses.

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

Avec une stratégie de conflit, `ONE_CYCLE` signifie une sélection d’agenda.
`FIRST_CHANGE` et `UNTIL` restent évalués après une activation atomique.

## Limites actuelles

La première version reconstruit toutes les activations après chaque choix. Ce
coût est acceptable pour la base historique et fournit un oracle simple. Un
agenda incrémental pourra être ajouté après profilage.

MEA est une stratégie publique écrite en Python, pas encore une méta-base de
règles inspectant réflexivement l’agenda. La fraîcheur locale est exprimée par
l’ordre des prémisses, sans héritage de classe intégré.

Le cas complet est
[`monkey_bananas/neopus_mea`](../rulebases/thesis/monkey_bananas/neopus_mea/README.md).
