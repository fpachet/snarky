# Cap général : langage de choix, backtracking et applications

Snarky n'a pas pour objectif immédiat de devenir un solveur CSP spécialisé.
Le projet construit d'abord un langage de règles efficace, déclaratif,
incrémental et explicable. Les domaines, propagateurs et le premier pilote
générique de choix et de retour arrière sont maintenant livrés.

## Étagement architectural

```text
règles, groupes et mémoire de travail
                ↓
matching indexé et semi-naïf
                ↓
domaines incrémentaux et propagateurs
                ↓
trail local et contradictions observables
                ↓
choice + hypothèse + pilote de backtracking
                ↓
applications écrites en Snarky
```

Le mécanisme de recherche réutilise :

- les groupes de règles et leurs modes d'exécution ;
- la réfraction et la provenance restaurées par checkpoint ;
- les contradictions et buts représentés par des faits ;
- une trace explicite des choix, décisions, échecs et solutions.

Le DFS utilise maintenant un trail de session : les alternatives sont créées
paresseusement, la mémoire de travail et la provenance sont annulées en place,
et une copie n'est conservée que pour une solution. BFS et best-first gardent
des forks, indispensables à leurs frontières multiples, mais la provenance y
est clonée sans `deepcopy` des faits immuables.

Il ne devra pas cacher une recherche métier dans une fonction Python. Python
restera la couche d'orchestration et de stockage du trail ; les choix
possibles, les contraintes et les conséquences devront être représentables
dans le langage.

## Palier `choice` et backtracking

Le premier palier comporte :

1. `CHOICE ... FROM`, `ChoicePoint` et `ChoiceAlternative` pour instancier des
   faits parmi des choix finis ;
2. MRV, ordre par poids et échantillonnage pondéré reproductible ;
3. parcours DFS, BFS et best-first ;
4. saturation des groupes après chaque décision ;
5. branches DFS réversibles et détection de contradiction ;
6. limites en nœuds et solutions ;
7. traces distinguant décision, propagation logique, échec et backtrack.

`InferenceSession.checkpoint()` complète le trail local des Compact-Tables et
de `PropagationState`. Il restaure faits, provenance, réfraction, journaux et
tags temporels. Le matcher est actuellement invalidé ou recréé au rollback ;
sa restauration incrémentale constitue une optimisation ultérieure, distincte
de la sémantique du backtracking.

Le détail de cette couche, ses garanties et ses mesures est dans
[`reversible_propagation.md`](reversible_propagation.md).

La recherche locale d'instanciation et les hypothèses métier devront rester
deux notions séparées. La première trouve une substitution d'une règle ; la
seconde explore différents états du problème.

## Deux applications de référence

### Solveur de contraintes écrit en Snarky

Le projet [`csp_solver`](../csp_solver/README.md) est maintenant exécutable.
Les variables, domaines, relations binaires et choix sont des faits ou
constructions Snarky. La règle `choose_csp_value` produit elle-même ses
alternatives, sans générateur de points métier en Python. Il vérifie que le
langage sait exprimer propagation, choix,
contradiction et backtracking sans dépendre du backend
`BacktrackingConstraintSolver` déjà fourni comme oracle Python. Les quatre
reines donnent exactement leurs deux solutions.

### Harmoniseur à quatre voix dans le style de Bach

Le projet [`harmonizer`](../harmonizer/README.md) livre un premier noyau
exécutable à deux positions. Il combine déjà :

- voicings SATB finis et soprano imposé ;
- contraintes de tessiture, espacement, mouvement et doublure ;
- relations binaires de conduite des voix ;
- choix progressifs, poids marginaux et recherche best-first ;
- exposition des notes choisies par des règles.

Le profil `ROY_1998`, les variables de notes séparées, les préférences
lexicographiques et le catalogue complet de règles restent planifiés. Le
compilateur de candidats Python du premier jalon sera progressivement remplacé
par des connaissances Snarky déclaratives.

## Critère de décision

Une optimisation du noyau est prioritaire si elle améliore plusieurs de ces
applications sans introduire de vocabulaire métier. Une primitive nouvelle
est justifiée si elle rend une connaissance importante plus déclarative ou
si elle fournit une brique réutilisable au futur mécanisme de recherche.
