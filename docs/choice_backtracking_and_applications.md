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
des descripteurs différés dans leurs frontières multiples. Le fork rapide,
dont la provenance partage les faits immuables au lieu d'utiliser `deepcopy`,
n'est créé qu'au retrait.

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
tags temporels. Après rollback, le matcher repart d'un index présemé ; ses
mémoires de jointure et de négation sont recréées pour isoler strictement les
branches.

Une autre extension possible consiste à confier quelques alternatives
coûteuses à des processus isolés. Chaque processus recevrait un fork au point
de partage puis utiliserait le DFS réversible dans son sous-arbre. Cette
politique reste différée et ne modifierait ni `CHOICE` ni les règles. Voir
[`parallel_choice_search.md`](parallel_choice_search.md).

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
reines donnent exactement leurs deux solutions. Une seconde formulation
N-reines remplace les tables de couples autorisés par une règle
d'arc-consistance et des comparaisons arithmétiques.

### Harmoniseur à quatre voix dans le style de Bach

Le projet [`harmonizer`](../harmonizer/README.md) livre un premier noyau
exécutable à deux positions. Il combine déjà :

- voicings SATB finis et soprano imposé ;
- contraintes de tessiture, espacement, mouvement et doublure ;
- règles intensionales de conduite des voix, révisées dans les deux
  directions ;
- choix progressifs, poids marginaux et recherche best-first ;
- exposition des notes choisies par des règles.

Le profil `ROY_1998`, les variables de notes séparées, les préférences
lexicographiques et le catalogue complet de règles restent planifiés. Le
compilateur de candidats Python du premier jalon sera progressivement remplacé
par des connaissances Snarky déclaratives.

Les optimisations de recherche et les reformulations A/B sont terminées et
mesurées dans
[`choice_search_optimization_plan.md`](choice_search_optimization_plan.md).

## Critère de décision

Une optimisation du noyau est prioritaire si elle améliore plusieurs de ces
applications sans introduire de vocabulaire métier. Une primitive nouvelle
est justifiée si elle rend une connaissance importante plus déclarative ou
si elle fournit une brique réutilisable au futur mécanisme de recherche.
