# Feuille de route guidée par les bases de règles

Cette feuille de route part d'exemples exécutables plutôt que d'une liste
abstraite de fonctionnalités. Le catalogue correspondant se trouve dans
[`rulebases/catalog.yaml`](../rulebases/catalog.yaml).

## État vérifié

Snarky exprime aujourd'hui :

- Fibonacci et factorielle explicites ;
- transitivité d'objets égalité ;
- date du lendemain avec calcul interne des années bissextiles ;
- un réseau de Petri borné déterministe ;
- une classification géométrique avec objets intermédiaires frais ;
- l'instance déterministe et la reformulation à sous-buts MEA du singe et des
  bananes ;
- intervalles, accords et progression harmonique inspirés de MusES ;
- la validation des quatre reines ;
- Hanoï borné à deux disques ;
- Sudoku p1 à p7, y compris X-Wing.

Ces bases couvrent récursion, jointures, agrégats, négation, mutations,
groupes, séquencement, classification, explication et point fixe.

## Extensions réalisées

### P1 — Arithmétique entière

`LET` accepte `%` sur deux entiers et les prémisses acceptent
`DIVISIBLE valeur BY diviseur`. Les nombres flottants et le zéro sont rejetés
explicitement.

La date du lendemain calcule maintenant les années bissextiles ; MusES calcule
ses intervalles modulo 12.

### P2 — Symboles frais

L'action `FRESH $x PREFIX frame` lie un nouvel atome pour la suite de
l'activation. Les noms sont déterministes, évitent tous les atomes déjà
réservés et sont enregistrés dans la substitution de provenance.

La géométrie l'utilise pour ses diagonales et Hanoï pour ses mouvements.

### P3 — Collections finies et `COLLECT`

`FiniteSet` est un terme immuable, dédupliqué et sérialisable dans le DSL sous
la forme `[a b c]`. Une prémisse corrélée :

```text
COLLECT $ensemble := $projection
    ...
END_COLLECT
```

lie l'ensemble des projections satisfaisant le bloc. Les variables locales ne
s'échappent pas, les supports participent à la provenance et les changements
de faits réactivent correctement la règle.

La sémantique actuelle est celle d'un ensemble non ordonné. Restent à étudier,
si un cas les exige :

- collection ordonnée ;
- multiensembles ;
- combinaisons de taille fixée ;
- itération d'actions sur une collection.

MusES matérialise maintenant ses ensembles de notes avec `COLLECT`.

### P4 — Contextes isolés, sans recherche automatique

`InferenceSession.fork()` produit une continuation indépendante qui hérite des
faits, de la provenance, de la réfraction et des compteurs de symboles frais.
Les mutations de la branche n'affectent jamais la session parente. Il n'existe
ni `commit`, ni choix automatique, ni retour arrière implicite.

Cette primitive sert à simuler explicitement une alternative. Elle ne fait pas
partie de la reproduction du singe et des bananes : cet exemple NéOpus utilise
des sous-buts et la stratégie MEA. La thèse décrit séparément un retour arrière
« objet », non générique et non intégré au système de base
([thèse, p. 227](https://www.francoispachet.fr/wp-content/uploads/2021/01/pachet-92b.pdf#page=227)).

## Extensions encore proposées

### P5 — Séquences

Introduire une abstraction minimale de relation d'ordre ou de fenêtre, plutôt
qu'un type musical spécialisé. Les faits `next` suffisent pour les motifs
courts ; les besoins nouveaux sont les chemins bornés, fenêtres, débuts/fins et
groupes reconnus.

Cas demandeurs : MusES, analyse de traces, texte et workflows.

### P6 — Recherche optionnelle

Les contextes isolés sont disponibles. Un module distinct pourrait un jour
piloter plusieurs branches :

- choix déterministe et alternatives ;
- détection d'états déjà visités ;
- coût ou heuristique ;
- justification d'une solution et d'un échec.

Cas demandeurs : quatre reines génératif, Sudoku bloqué et certaines chaînes
forcées. Le singe et les bananes historique n'en dépend pas. Un adaptateur de
solveur de contraintes pourra partager la même interface sans remplacer les
techniques humaines.

### P7 — Prédicats calculés et hiérarchie de types

Permettre des prédicats purs enregistrés explicitement, avec types d'arguments
et déterminisme vérifiable. Ajouter séparément une petite relation `subtype`
dont la clôture reste visible dans la provenance.

Cas demandeurs : géométrie calculée, unités et dimensions, ontologies de
domaine. Le moteur ne doit jamais exécuter arbitrairement une fonction Python
référencée par du texte.

### P8 — Stratégie d’agenda MEA réalisée, réflexion différée

`ConflictResolutionStrategy` rend la politique publique et
`MEAConflictStrategy` sélectionne une activation selon la fraîcheur locale du
premier support, puis LEX, spécificité et ordre source. Les choix sont
journalisés dans des `AgendaSelection`.

La base `monkey_bananas/neopus_mea` crée et satisfait six buts en profondeur,
sans plan préchargé ni backtracking. Reste à plus long terme l’exposition de
l’agenda et des règles comme données manipulables par les méta-règles NéOpus.

## Ordre recommandé

1. ~~`%`/`DIVISIBLE`.~~
2. ~~Symboles frais déterministes.~~
3. ~~Ensembles finis, `COLLECT` et contextes isolés.~~
4. Implémenter p8 Sudoku avec les primitives disponibles.
5. Ajouter combinaisons ou séquences seulement à partir d'un oracle concret.
6. ~~Ajouter une stratégie MEA publique et la valider sur les sous-buts du
   singe et des bananes.~~
7. Garder recherche, prédicats calculés et réflexion comme modules séparés.

Les primitives de langage n’ont pas changé le modèle d’exécution fondamental.
MEA ajoute un mode d’agenda explicite, tandis que la recherche et la réflexion
restent des sous-systèmes distincts. Le balayage déterministe actuel demeure
l’oracle par défaut.
