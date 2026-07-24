# Cap général : langage de choix, backtracking et applications

Snarky n'a pas pour objectif immédiat de devenir un solveur CSP spécialisé.
Le projet construit d'abord un langage de règles efficace, déclaratif,
incrémental et explicable. Les domaines et propagateurs livrés maintenant
préparent le mécanisme générique de choix et de retour arrière ; ils ne le
remplacent pas.

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

Le futur mécanisme de recherche devra donc réutiliser :

- les domaines finis déjà construits pendant l'instanciation ;
- la file d'incidence des propagateurs ;
- les comparaisons, `CONSTRAINT`, `NVALUE` et `ALL_DIFFERENT` ;
- les deltas d'ajout et de suppression ;
- les groupes de règles et leurs modes d'exécution ;
- la réfraction, la provenance et les traces.

Il ne devra pas cacher une recherche métier dans une fonction Python. Python
restera la couche d'orchestration et de stockage du trail ; les choix
possibles, les contraintes et les conséquences devront être représentables
dans le langage.

## Palier `choice` et backtracking

Le trail local, les checkpoints et les contradictions structurées sont
maintenant livrés. Le prochain grand palier comporte donc :

1. une prémisse ou un fait déclaratif produisant un ensemble fini de choix ;
2. une heuristique publique, MRV en premier lieu ;
3. ~~un trail local enregistrant l'ancienne valeur des domaines et des
   masques ;~~
4. une propagation jusqu'au point fixe après chaque choix ;
5. ~~une contradiction observable ;~~
6. un pilote de retour arrière qui restaure le trail sans recopier toute la
   session ;
7. une trace distinguant décision, propagation et échec.

Les Compact-Tables et `PropagationState` fournissent la représentation et le
trail :
un choix réduira des domaines et des masques de lignes actives ; un
backtrack pourra restaurer leurs anciennes valeurs sans recopier les faits ni
reconstruire les tables de la règle.

Le détail de cette couche, ses garanties et ses mesures est dans
[`reversible_propagation.md`](reversible_propagation.md).

La recherche locale d'instanciation et les hypothèses métier devront rester
deux notions séparées. La première trouve une substitution d'une règle ; la
seconde explore différents états du problème.

## Deux applications de référence

### Solveur de contraintes écrit en Snarky

Un petit solveur CSP constituera un exercice d'intégration. Les variables,
domaines, contraintes et choix seront des faits ou constructions Snarky. Il
servira à vérifier que le langage suffit à exprimer propagation, choix,
contradiction et backtracking sans dépendre du backend
`BacktrackingConstraintSolver` déjà fourni comme oracle Python.

### Harmoniseur à quatre voix dans le style de Bach

L'harmoniseur sera le cas d'étude complet. Il pourra combiner :

- génération des notes et accords candidats ;
- contraintes de tessiture, mouvement et doublure ;
- `ALL_DIFFERENT`, `NVALUE` et contraintes arithmétiques ;
- règles d'ordre 2 sur les relations harmoniques ;
- groupes de règles par famille stylistique ;
- choix progressifs et retour arrière ;
- explications indiquant les règles musicales ayant éliminé ou choisi chaque
  possibilité.

Cette application ne doit pas être codée comme un solveur monolithique. Son
intérêt est précisément d'utiliser toute la panoplie de Snarky et de montrer
la coopération entre connaissances symboliques, propagation et recherche.

## Critère de décision

Une optimisation du noyau est prioritaire si elle améliore plusieurs de ces
applications sans introduire de vocabulaire métier. Une primitive nouvelle
est justifiée si elle rend une connaissance importante plus déclarative ou
si elle fournit une brique réutilisable au futur mécanisme de recherche.
