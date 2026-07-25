# Périmètre de la spécification musicale

Le cahier des charges de référence est la version 1.0 de la spécification
« harmonisation tonale à quatre voix », fondée sur le chapitre
d'harmonisation de la thèse de Pierre Roy (1998).

Il distingue :

- le profil historique `ROY_1998` ;
- le profil étendu `FOUR_PART_COMPLETE` ;
- les règles `MUST`, préférences `SHOULD` et extensions `MAY` ;
- les règles attestées, incomplètes, ajoutées ou paramétriques ;
- les phases variables de notes puis variables d'accords ;
- la propagation, le choix, le retour arrière et l'optimisation ;
- les critères de test et d'explication par identifiant `R-*`.

Le premier incrément implémente seulement le noyau documenté dans
[`README.md`](README.md). Le document complet devra rester la source normative
lors de l'import du catalogue de règles et de leurs cas de test.

## Correspondance du jalon note par note

Le second incrément suit maintenant la section 5 de la spécification :

| Élément normatif | Implémentation |
|---|---|
| variables `note[v,t]` | un objet `csp_variable` par voix et position |
| ligne donnée | domaine singleton de la voix SATB choisie |
| `R-ORDER-001` | comparaisons de `note_generation.rules` |
| `R-SPACING-001..003` | contraintes arithmétiques de génération |
| construction différée | groupe `generate_candidate_voicings` |
| compatibilité verticale | triade complète enregistrée comme prédicat pur |
| canalisation | groupe `maintain_note_voicing_channel` |
| `R-MELODY-001/002` | prédicat `melodic_transition` dans la règle de support |
| `R-PARALLEL-001/002` | prédicat `no_parallel_perfects` |
| `R-GLOBAL-MOTION-001` | prédicat `legal_global_motion` |
| first fail | `PriorityMRVChoicePolicy` |
| optimisation/échantillonnage | poids conditionnels et politique pondérée |

Les degrés, renversements, cadences, sensible et règles détaillées de doublure
restent le prochain jalon `ROY_1998`. Les prédicats calculés ne contiennent
aucune recherche : ils évaluent une opération musicale élémentaire sur des
termes ground fournis par une règle.

## Frontière MuSES

La ligne donnée peut être une `TemporalCollection` MuSES désignée comme
soprano, alto, ténor ou basse. Chaque note reçoit une identité factuelle stable
et expose hauteur, rang, début, durée, vélocité et canal. La collection expose
son ordre et ses métadonnées.

Le groupe `import_muses_given_voice` est la frontière déclarative minimale :
pour chaque note source associée à une variable Snarky, il transforme
`muses_pitch` en `candidate`. La hauteur donnée n'est donc pas injectée dans le
domaine par une boucle Python cachée. Le reste de la base ne dépend pas de
MuSES et conserve son modèle factuel.

Après résolution, chaque tuple SATB fournit une hauteur à chacune des quatre
voix. Les attributs temporels positionnels de la ligne source sont recopiés,
les collections sont encodées puis décodées par le même codec et assemblées
dans une `Piece`. Cette reconstruction est un snapshot de solution, pas une
mutation de la collection d'entrée.

Ce premier contrat considère que les quatre voix partagent le même rythme.
Il refuse une ligne polyphonique ou une durée non positive et limite le
raisonnement au vocabulaire C majeur du noyau courant.
