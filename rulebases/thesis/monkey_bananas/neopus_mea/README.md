# Reformulation NéOpus avec MEA

Cette base reformule le premier exemple « singe et bananes » du chapitre VII.1
de la thèse. Elle ne connaît pas le plan à l’avance : le seul but initial est
que le singe tienne la banane.

```text
(goal-1 goal_type holds)
(goal-1 object banana)
(goal-1 status active)
```

Les règles découvrent ensuite qu’il faut déplacer l’échelle, en descendre,
la prendre, la porter sous la banane, la lâcher, y monter et enfin saisir la
banane. Chaque obstacle devient un objet-but créé par `FRESH`.

## Exécution et trace

```sh
uv run python -m rulebases.runner \
  thesis/monkey_bananas/neopus_mea --trace
```

La trace montre, pour chaque choix :

- la règle sélectionnée dans l’ensemble de conflit ;
- le but actif marqué `FOCUS` ;
- son `timeTag` de fraîcheur ;
- les faits ajoutés et retirés par l’activation.

Les identifiants `goal-2`, `goal-3`, etc. sont déterministes. Les relations
`parent` et `spawned` permettent de reconstruire l’arbre complet des buts ; la
trace indente automatiquement les sélections selon cette profondeur.

## Pourquoi MEA est nécessaire

Le but parent reste actif pendant qu’un sous-but est résolu. Plusieurs règles
peuvent donc être simultanément applicables. `MEAConflictStrategy` privilégie
le fait filtré par la prémisse `FOCUS` ; toutes les règles de résolution
marquent ainsi `($goal status active)`. Un sous-but nouvellement créé possède
un `timeTag` supérieur à celui de son parent et passe devant lui.

Après ce critère principal, les égalités sont départagées par un vecteur de
fraîcheur de type LEX, la spécificité de la règle, puis l’ordre source.

## Fidélité et limites

La base suit les trois catégories historiques :

1. génération de sous-buts ;
2. satisfaction avec modification des objets ;
3. satisfaction sans modification des objets.

Elle reprend aussi le lancement où le singe se trouve sur l’échelle, l’échelle
et la couverture près de la fenêtre, et la banane au plafond au centre. La
thèse indique que la base originale complète contient 26 règles, mais renvoie
à une autre publication pour leur texte intégral. Cette reformulation contient
les règles générales nécessaires au scénario publié ; elle n’est donc pas une
transcription littérale des 26 règles OPS5.

Sont volontairement différés :

- l’héritage intégré au filtrage, remplacé ici par des faits `type` ;
- la méta-base réflexive `OPSMEA`, remplacée par une stratégie publique ;
- la méta-règle de terminaison et la règle `impossible`.

Aucun backtracking ni `InferenceSession.fork()` n’est utilisé.

Référence : [thèse, p. 190–198](https://www.francoispachet.fr/wp-content/uploads/2021/01/pachet-92b.pdf#page=190).
