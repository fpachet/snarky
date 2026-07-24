# Ensembles finis, symboles frais et contextes isolés

## Ensembles finis

`FiniteSet` est un terme immuable à sémantique d'ensemble. Son ordre
d'affichage est le premier ordre d'insertion observé, mais l'égalité et le hash
ne dépendent pas de cet ordre. Les doublons sont éliminés.

La syntaxe textuelle est :

```text
[c e g]
[]
```

Une prémisse `COLLECT` exécute une requête locale corrélée et lie l'ensemble
des projections :

```text
($chord type chord)
COLLECT $notes := $note
    ($chord contains $note)
END_COLLECT
ADD ($chord note_set $notes)
```

Les variables liées avant le bloc sont visibles à l'intérieur. Les variables
locales, comme `$note`, ne sont pas visibles après le bloc ; seule la cible
`$notes` est exportée. Une collection vide est un résultat valide `[]`.

Tous les faits témoins sont attachés à la provenance. Un ajout ou retrait
susceptible de changer l'ensemble invalide la réfraction de l'ancienne
activation. La première implémentation recalcule la projection ; elle ne
maintient pas encore un index incrémental propre aux éléments collectés.

## Symboles frais

L'action :

```text
FRESH $diagonal PREFIX diagonal
ADD ($shape diagonal $diagonal)
```

lie `$diagonal` à un atome tel que `diagonal-1`. La liaison est locale aux
actions suivantes de l'activation. Les noms :

- sont déterministes pour une même exécution ;
- n'entrent en collision avec aucun atome déjà observé ou réservé ;
- restent réservés même si le fait qui les contient est ensuite retiré ;
- figurent dans les événements et la provenance.

Deux branches isolées peuvent produire le même nom après leur séparation :
leurs mémoires de travail sont des mondes distincts.

## Contextes isolés

`InferenceSession.fork()` clone l'état logique courant :

```python
branch = session.fork()
branch.run_group(simulation)
```

La branche hérite des faits, événements, preuves, règles enregistrées,
réfraction, cycles et compteurs de symboles frais. Ses mutations n'affectent
pas la session parente.

Ce mécanisme ne choisit aucune règle, ne parcourt aucun arbre et ne revient
pas automatiquement en arrière. Il fournit seulement la primitive d'isolation
sur laquelle un planificateur ou un solveur pourrait être construit
ultérieurement.

Dans la reconstruction NéOpus, il ne faut pas l'assimiler au contrôle du singe
et des bananes, qui utilise désormais des sous-buts et
`MEAConflictStrategy`. La thèse présente séparément un mécanisme applicatif
d'objets « backtrackables », non intégré au moteur de base.
