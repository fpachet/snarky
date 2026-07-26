# Benchmark de redécouverte de règles connues

## But

Avant de rechercher une règle nouvelle, vérifier que le mineur peut retrouver
à partir du corpus des règles déjà connues, sans recevoir leur formulation ni
leurs verdicts pendant l'apprentissage.

Les règles exécutables actuelles de Snarky constituent un oracle tenu à part.
Elles ne servent qu'après induction pour mesurer la proximité sémantique entre
une règle apprise et une règle de référence.

## Prévention de la fuite de connaissance

Le mineur reçoit des faits primitifs :

- voix et paire de voix ;
- hauteurs et classes de hauteur ;
- degrés relatifs à la tonalité locale ;
- intervalles source et cible ;
- directions et amplitudes des mouvements ;
- attaque, tenue, métrique et fermata ;
- accord, renversement et statut cadentiel lorsqu'ils sont disponibles.

Il ne reçoit pas de faits composites contenant déjà la conclusion :

- pas de `creates_parallel_fifth` ;
- pas de `violates_voice_overlap` ;
- pas de `resolves_leading_tone` ;
- pas de `must_double_cadential_bass`.

Par exemple, la redécouverte des quintes parallèles doit combiner elle-même :

```text
intervalle_source == quinte_parfaite
AND intervalle_cible == quinte_parfaite
AND direction_haute == direction_basse != immobile
→ éviter
```

Les identifiants `R-*`, les fichiers `.rules` et les verdicts de l'oracle ne
sont pas accessibles au processus de recherche.

## Catalogue caché

### Niveau A — faits de hauteur et de mouvement

Ces règles ne nécessitent aucune analyse harmonique :

| Référence | Connaissance à redécouvrir |
|---|---|
| `R-MELODY-001` | éviter les sauts mélodiques supérieurs à l'octave |
| `R-MELODY-002` | éviter le triton mélodique |
| `R-OVERLAP-001` | éviter le chevauchement de voix adjacentes |
| `R-PARALLEL-001` | éviter les octaves ou unissons parallèles |
| `R-PARALLEL-002` | éviter les quintes parallèles |
| `R-DIRECT-001/002` | éviter certains mouvements directs des voix extrêmes vers octave ou quinte |

### Niveau B — faits tonals et harmoniques

| Référence | Connaissance à redécouvrir |
|---|---|
| `R-LEADING-001` | résolution ascendante de la sensible |
| `R-SEVENTH-001` | résolution descendante de la septième de dominante |
| `R-DOUBLING-002` | éviter de doubler la sensible |
| `R-EXT-7CHORD-003` | employer les quatre membres de `V7` |

### Niveau C — statuts contextuels explicites

| Référence | Connaissance à redécouvrir |
|---|---|
| `R-LEADING-002` | exception de résolution intérieure sur cadence rompue |
| `R-CAD64-001` | doubler la basse du six-quatre cadentiel |
| `R-CAD64-002..005` | résolution vers la dominante, position fondamentale, basse tenue et mouvements `6→5`, `4→3` |

Le niveau suivant n'est ouvert que lorsque le niveau précédent a permis de
séparer les échecs du mineur des faits manquants.

## Deux évaluations complémentaires

### Redécouverte descriptive

Le mineur observe seulement les réalisations authentiques. Il cherche les
implications locales courtes ayant support, confirmation et stabilité élevés.
Cette piste teste si la règle est visible dans la distribution positive.

### Redécouverte par choix contrefactuel

Pour chaque note de Bach, le pipeline énumère les autres notes localement
possibles. Le mineur doit apprendre une clause qui classe le choix de Bach
devant les alternatives créant la violation de référence. Une alternative non
choisie n'est pas étiquetée « faute » ; l'apprentissage reste un classement
conditionnel.

L'oracle Snarky annote les alternatives uniquement après apprentissage pour
mesurer si la clause découverte sépare les mêmes cas.

## Mesure de la récupération

Une égalité textuelle entre règles est trop stricte : deux clauses différentes
peuvent être logiquement équivalentes. Chaque candidate est donc comparée à la
référence sur un domaine local fini et sur les opportunités tenues à part.

Pour chaque règle cachée, publier :

- rang de la première candidate sémantiquement proche ;
- précision, rappel et `F1` de ses verdicts face à l'oracle ;
- gain prédictif sur `validation` ;
- support en événements et en pièces ;
- stabilité par bootstrap de pièces ;
- nombre de conditions de la candidate et de la référence ;
- exceptions authentiques où corpus et oracle divergent ;
- résultat de l'ablation en génération.

La classification finale est :

- `RECOVERED_EQUIVALENT` : même comportement sur le domaine testé ;
- `RECOVERED_REFINED` : règle connue retrouvée avec une condition contextuelle
  supplémentaire validée ;
- `RECOVERED_WEAKER` : tendance correcte mais force ou couverture inférieure ;
- `CONTRADICTED_BY_CORPUS` : exceptions authentiques nombreuses ou stables ;
- `MISSING_FACT` : les cas ne sont pas séparables avec le vocabulaire courant ;
- `NOT_RECOVERED` : faits disponibles, mais aucune clause stable n'est trouvée.

## Critère du premier jalon

Le premier mineur est crédible s'il récupère, sans faits composites :

- au moins quatre des six familles du niveau A ;
- au moins une règle mélodique et une règle entre deux voix ;
- une formulation de trois conditions musicales au plus pour les règles qui
  possèdent une forme de référence aussi courte ;
- un résultat stable sur `validation`, et non uniquement sur `train`.

Un échec est conservé comme résultat. Il peut révéler une règle pédagogique
peu visible dans Bach, une exception importante, un mauvais ensemble de choix
contrefactuels ou un fait de statut manquant.

## Références exécutables

Les oracles actuels sont :

- [`../../voice_leading_conformance.rules`](../../voice_leading_conformance.rules) ;
- [`../../vertical_conformance.rules`](../../vertical_conformance.rules) ;
- leurs tests dans
  [`../../../tests/test_harmonizer_conformance.py`](../../../tests/test_harmonizer_conformance.py).
