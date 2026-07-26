# Programmes explicites de groupes de règles

## Motivation

Un `RuleGroup` est une unité de contrôle, mais une application réaliste en
compose plusieurs : préparation des faits, production des choix, propagation
et interprétation. Lorsque cette composition reste enfouie dans un solveur
Python, la base effectivement exécutée ne peut pas être comprise en lisant le
projet applicatif.

`RuleProgram` fournit un manifeste général et inspectable :

```python
program = RuleProgram(
    "generator",
    preparation_groups=(load_objects, generate_candidates),
    choice_groups=(choose_shape,),
    propagation_groups=(maintain_geometry,),
    interpretation_groups=(materialize_result,),
)
```

Les phases ont la sémantique suivante :

- `preparation_groups` est exécuté une fois par le constructeur du modèle ;
- `choice_groups`, `propagation_groups` et `interpretation_groups` forment,
  dans cet ordre, `search_groups` ;
- l'orchestrateur de recherche sature tous les `search_groups` jusqu'au point
  fixe à chaque nœud ;
- `RuleChoiceProvider` extrait les actions `CHOICE` de leurs règles et conserve
  les règles déterministes pour la saturation.

`manifest()` rend la composition sérialisable pour les tests, traces et outils
de visualisation.

## Étapes séquentielles et réversibles

Une simple liste de groupes ne suffit pas lorsqu'une application doit d'abord
construire un objet abstrait, puis le réaliser. `RuleStep` reprend la notion
d'« étape » de Laurière :

```text
PROGRAM satb_harmonizer
    PREPARE generate_candidate_voicings
    STEP harmonic_plan
        GROUP choose_harmonic_plan
    END_STEP
    STEP satb_realization
        GROUP choose_satb_realization
    END_STEP
    PROPAGATE maintain_note_voicing_channel
    INTERPRET interpret_note_harmonization
END_PROGRAM
```

`parse_rule_program()` résout les noms de groupes dans un catalogue. Une ligne
`CONSTRAINT nom` peut également référencer un propagateur de session fourni au
parseur. La syntaxe décrit donc l'orchestration sans enfouir l'ordre des phases
dans le solveur applicatif.

À chaque nœud, les groupes communs et ceux de l'étape courante alternent avec
ses contraintes jusqu'au point fixe. Seuls les `CHOICE` de cette étape sont
alors visibles. Leur absence fait avancer à l'étape suivante.

Ce passage n'est pas un *commit*. Les points de choix de `harmonic_plan`
restent dans le trail : si `satb_realization` aboutit à une contradiction, la
recherche revient essayer un autre plan harmonique. La séparation guide donc
l'ordre de construction sans rendre la recherche incomplète.

## `CHOICE` ne dépend pas du CSP

`RuleProgram` et `CHOICE` appartiennent au cœur Snarky. Une base peut choisir
une couleur sans adopter le vocabulaire `csp_problem`, `csp_variable`,
`candidate` ou `value` :

```snark
GROUP choose_color
    RULE choose_one_color
    WHEN
        (painting state open)
    THEN
        CHOICE (painting color $color)
        FROM
            (palette color $color)
        END_CHOICE
    END
END_GROUP
```

Le projet `csp_solver` fournit seulement un protocole réutilisable lorsque le
problème possède effectivement des variables à domaines finis. Sa bibliothèque
publique expose séparément :

- `choices` ;
- `binary_constraints` ;
- `domains` ;
- `problems`.

Une application peut donc sélectionner uniquement les modules pertinents.
L'ancien comportement de `solve_finite_csp`, qui charge toute la bibliothèque
avant les groupes métier, reste le défaut compatible. Le paramètre
`rule_groups` permet de fournir une composition exacte.

## Programme de l'harmoniseur

Le modèle note par note expose son programme dans `model.program`. Avec une
entrée MuSES, son manifeste est :

```text
preparation
  import_muses_given_voice
  generate_candidate_voicings

step:harmonic_plan
  choose_harmonic_plan

step:satb_realization
  choose_satb_realization

propagation
  apply_harmonizer_decisions
  classify_csp_domains
  enforce_tonal_form
  maintain_note_voicing_channel
  update_contextual_note_weights
  propagate_note_harmonic_transitions
  classify_csp_problems

interpretation
  interpret_note_harmonization
```

Le groupe
`propagate_binary_constraints`, auparavant ajouté implicitement, n'est plus
chargé : le modèle musical ne construit aucun fait `binary_constraint`.

Le programme conserve une seule mémoire de faits et un seul arbre de
recherche. L'étape harmonique choisit uniquement les variables d'accord ;
l'étape SATB choisit les renversements et hauteurs encore indéterminés. Une
décision retire des candidats, les règles musicales retirent alors les
voicings sans support, puis la classification générique détecte les
singletons, contradictions ou solutions.
