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

## Correspondance du jalon tonal

Le second incrément suit maintenant la section 5 de la spécification :

| Élément normatif | Implémentation |
|---|---|
| variables `note[v,t]` | un objet `csp_variable` par voix et position |
| variables `chord[t]` | un `csp_variable` parmi `I`, `ii`, `IV`, `V`, `V7`, `vi`, `vii°` |
| variables `inversion[t]` | fondamentale, premier renversement, ou second renversement cadentiel |
| ligne donnée | domaine singleton de la voix SATB choisie |
| `R-ORDER-001` | comparaisons de `note_generation.rules` |
| `R-SPACING-001..003` | contraintes arithmétiques de génération |
| construction différée | groupe `generate_candidate_voicings` |
| compatibilité verticale | `NVALUE` pour la complétude, basse du renversement et règles `COUNT` de doublure |
| canalisation | accord–renversement–notes–voicing dans `maintain_note_voicing_channel` |
| progression fonctionnelle | table `allows_successor`, faits de violation, révision dans les deux directions |
| forme | `I` initial ; cadence parfaite, plagale, rompue ou demi-cadence |
| `R-CADENCE-004` | préparation sans `I`/`V`, sauf `I64` cadentiel |
| `R-DOUBLING-001..007` | règles `vertical_conformance.rules`, sans prédicat Python |
| `R-LEADING-001..002` | résolution de la sensible, avec exception intérieure `V→vi` explicite |
| `R-EXT-7CHORD-001..003` | `V7` complet et `R-SEVENTH-001` descendant |
| `R-EXT-64-001` | règles `R-CAD64-*` : `I64→V`, basse pédale, `6→5` et `4→3` |
| rythme harmonique | plusieurs notes peuvent partager les mêmes variables harmoniques |
| `R-MELODY-001/002` | contraintes arithmétiques sur les faits `voice_path` |
| `R-OVERLAP-001` | règles corrélées sur les paires de voix adjacentes |
| `R-PARALLEL-001/002` | règles modulo 12 pour octaves/unissons et quintes |
| `R-DIRECT-001/002` | mouvement direct des voix extrêmes vers octave ou quinte |
| `R-GLOBAL-MOTION-001` | deux règles explicites, mouvement entièrement ascendant/descendant |
| first fail | `PriorityMRVChoicePolicy` |
| optimisation/échantillonnage | poids conditionnels des notes et accords |

Ce jalon couvre maintenant un sous-ensemble substantiel des degrés,
renversements, doublures, résolutions et cadences, mais ne revendique pas
encore le profil `ROY_1998`. Restent les accords de septième autres que `V7`,
leurs renversements, les six-quatre non cadentiels, toutes les exceptions,
les suspensions et autres dissonances, la métrique, les modulations et la
totalité du catalogue. Dans le modèle note par note, aucun prédicat calculé ne
porte une règle musicale : les faits ground, contraintes arithmétiques,
agrégats et blocs existentiels constituent l'oracle de conformité lui-même.

## Sémantique de conformité

La génération verticale suit quatre étapes inspectables :

1. `melodic_roles.rules` analyse le contour de la soprano donnée ;
2. `note_generation.rules` joint accord, renversement, rôle et quatre
   hauteurs ;
3. `NVALUE` impose la complétude aux quatre voix pour un accord normal ou aux
   trois voix inférieures pour une triade sous soprano ornementale ;
4. `describe_candidate_voicings` expose un fait `tone` par voix ;
5. les règles `R-DOUBLING-*`, `R-EXT-7CHORD-*` et `R-CAD64-*` retirent les
   candidats non conformes.

Une transition est représentée par :

```text
SEQ[
  left SEQ[source_chord source_inversion S A T B]
  right SEQ[target_chord target_inversion S A T B]
]
```

Les règles en dérivent les chemins de voix et les six paires de voix, puis
ajoutent `(transition violates R-...)`. Une règle de classification ajoute
`(transition state legal)` seulement en l'absence de violation. La révision
d'arc exige simultanément le `voicing_candidate` voisin courant et ce support
légal. Cette jointure est essentielle : les descriptions calculées restent
des connaissances sur une paire ground, mais un candidat retiré ne doit plus
constituer un support de domaine.

Dans ce profil « cas 1 », la légalité d'une paire ground ne dépend pas de
l'état futur des domaines. Les groupes Snarky la calculent donc une fois
pendant la préparation. Une `CHOICE` de note, accord ou renversement retire
des voicings par canalisation ; la révision joint la relation légale préparée
au `voicing_candidate` voisin encore présent, puis propage les retraits avant
la décision suivante ou avant un retour arrière. Si des règles pouvaient
ajouter de nouvelles valeurs de domaine, cette classification devrait revenir
dans le point fixe dynamique.

## Frontière d'expressivité observée

Le noyau SATB livré ne nécessite aucune extension du moteur. `NVALUE`,
`COUNT`, négation corrélée, séquences ground, modulo et comparaisons suffisent.
Trois absences rendent cependant le catalogue plus répétitif :

- pas de macros de règles paramétrées par voix ou paire de voix ;
- pas d'expression arithmétique `ABS` ;
- pas de disjonction logique dans une prémisse.

Le catalogue emploie donc des règles séparées pour les directions montante et
descendante ainsi que pour quintes et octaves. Il ne s'agit pas d'un blocage
sémantique sur des domaines finis. En revanche, tonalités multiples,
orthographe enharmonique, force métrique, suspensions et modulation exigent
d'abord un vocabulaire musical explicite. Les préférences `SHOULD` avec
optimisation lexicographique ne sont pas encore une construction native :
les poids actuels ordonnent les choix sans relâcher une règle `MUST`.

## Vocabulaire tonal exécutable

Les hauteurs candidates couvrent les notes diatoniques de do majeur dans les
tessitures SATB. Chaque accord expose les hauteurs permises par voix et les
basses permises pour ses renversements :

| Degré | Classes de hauteur | Transitions autorisées |
|---|---|---|
| `I` | C E G | `I`, `ii`, `IV`, `V`, `V7`, `vi`, `vii°` |
| `ii` | D F A | `ii`, `V`, `V7` |
| `IV` | F A C | `IV`, `I`, `ii`, `V`, `V7` |
| `V` | G B D | `V`, `V7`, `I`, `vi` |
| `V7` | G B D F | `V7`, `I`, `vi` |
| `vi` | A C E | `vi`, `ii`, `IV` |
| `vii°` | B D F | `vii°`, `I` |

Un voicing candidat est le terme :

```text
SEQ[chord inversion soprano alto tenor bass]
```

Il doit avoir les quatre notes dans l'accord, contenir ses trois ou quatre
classes de hauteur, respecter l'ordre strict, les espacements SATB et les
doublures, puis placer à la basse la note du renversement. Les douze règles de
canalisation maintiennent les supports dans les deux directions.

La forme est paramétrée par `cadence` : `perfect`, `plagal`, `deceptive` ou
`half`. À partir de trois événements harmoniques, elle ajoute `I` fondamental
au début. Pour la cadence parfaite, l'événement pré-cadentiel refuse `I` et
`V`, sauf `I64`. Par défaut, chaque attaque de la soprano reçoit ses propres
variables d'accord et de renversement. `harmonic_rhythm` peut explicitement
associer plusieurs notes au même événement : elles partagent alors les mêmes
variables d'accord et de renversement, tandis que leurs voicings restent
distincts. Ce partage est une contrainte fournie par l'utilisateur, et non une
analyse implicite des notes mélodiques.

`harmonic_plan` peut en outre fournir un degré ou `None` par événement. Python
ne fait que traduire les étiquettes `I`, `ii`, `IV`, `V`, `V7`, `vi`, `vii°`
en faits :

```text
(note_position_0 planned_chord degree_I)
```

La règle `remove_chord_outside_harmonic_plan` effectue la restriction du
domaine. Le plan n'impose ni renversement ni note SATB et peut donc servir de
squelette partiel. Il doit rester compatible avec le profil cadentiel.

Le cas nominal n'a besoin ni de `harmonic_plan` ni d'un profil prédéterminé.
Python ajoute la cadence demandée comme donnée :

```text
(roy_note_harmonization cadence perfect)
```

ainsi que les rôles structurels et relations `harmonic_successor`. Le groupe
`derive_harmonic_plan` déduit les restrictions initiales et cadentielles. La
canalisation verticale et les transitions filtrent ensuite les domaines
d'accord à partir de la soprano ; les règles classent chaque accord sélectionné
comme `tonic`, `predominant` ou `dominant`.

Le programme est découpé en deux étapes déclaratives dans
`note_harmonizer.program` :

```text
STEP harmonic_plan
    GROUP choose_harmonic_plan
END_STEP
STEP satb_realization
    GROUP choose_satb_realization
END_STEP
```

La première étape choisit uniquement les accords encore ambigus. Son point
fixe atteint, la seconde choisit renversements et hauteurs. Le passage d'une
étape à l'autre n'est pas un engagement irréversible : une contradiction SATB
peut restaurer la branche et essayer un autre accord. L'exemple de huit
mesures et seize notes obtient ainsi `I–IV–I–IV–I–IV–ii–V–I` depuis la
soprano, le rythme harmonique et la cadence seuls.

Le profil historique `extended_tonal_arc` reste accepté comme contrainte
optionnelle de compatibilité et comme oracle ciblé ; il n'est plus utilisé par
l'exemple principal.

## Harmonisation de chaque note et notes étrangères

Une hauteur n'est pas étrangère en elle-même : son rôle dépend de l'accord
choisi. Sans `harmonic_rhythm`, chaque note de la soprano reçoit le domaine
harmonique complet et traverse les mêmes règles de choix d'accord, de
renversement, de verticalité et de conduite des voix. Ainsi, dans l'ouverture
`C5-D5-E5`, le D peut être une note d'accord de V (ou d'un autre accord
diatonique qui le contient) ; il n'est pas pré-étiqueté comme passage.

Chaque position possède désormais une variable CSP `melodic_role_variable`
ainsi que les faits `metric_strength strong|weak` et `note_duration N`. Son
domaine contient toujours `chord_tone`.

`classify_melodic_durations` dérive :

```text
(note_position_1 duration_role short)
```

si la note ne dépasse pas une noire et n'est plus longue qu'aucune de ses deux
voisines. Pour une soprano donnée, `derive_melodic_roles` examine ensuite les
trois hauteurs consécutives, la métrique et cette classe de durée, puis peut
ajouter :

```text
(note_position_1 melodic_role_candidate passing_tone)
(note_position_1 melodic_role_candidate upper_neighbor)
(note_position_1 melodic_role_candidate lower_neighbor)
(note_position_1 melodic_role_candidate suspension)
(note_position_1 melodic_role_candidate anticipation)
```

`prepare_melodic_role_domains` transforme ces analyses en candidats de la
variable. `choose_melodic_role`, dans l'étape `harmonic_plan`, choisit donc le
rôle avec l'accord ; ce n'est plus une étiquette calculée après la solution.

La canalisation impose :

- `chord_tone` : appartenance de la soprano à l'accord courant ;
- passage ou broderie : note courte, métrique faible, mouvement conjoint
  approprié et même accord disponible aux trois positions ;
- suspension : métrique forte, préparation par note commune à l'accord
  précédent, nouvel accord maintenu jusqu'à la résolution descendante ;
- anticipation : note courte, métrique faible, maintien de l'accord précédent et
  appartenance de la note à l'accord suivant.

Pour passage, broderie et anticipation, alto–ténor–basse réalisent toutes les
classes de la triade. Pour la suspension, ils réalisent exactement les deux
autres classes et omettent celle de la résolution : la dissonance suspendue
remplace temporairement ce membre. Ordre, espacements, renversement, doublures
et conduite des voix restent appliqués normalement.

Le résultat expose un rôle par note dans `NoteHarmonization.melodic_roles`.
`NoteHarmonization.metric_strengths` expose aussi les faits métriques.
`NoteHarmonization.note_durations` expose les durées. Les deux vecteurs peuvent
être fournis directement ; la frontière MuSES les déduit des débuts et durées
de notes ainsi que de la mesure. `V7` orné, appoggiatures, échappées et
métrique hiérarchique restent hors de ce palier.

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

La frontière traduit également les débuts de notes en faits métriques
`strong|weak` d'après la signature temporelle. Cette traduction ne choisit
aucun rôle : les candidats et leurs compatibilités restent déclaratifs.

Après résolution, chaque tuple SATB fournit une hauteur à chacune des quatre
voix. Les attributs temporels positionnels de la ligne source sont recopiés,
les collections sont encodées puis décodées par le même codec et assemblées
dans une `Piece`. Cette reconstruction est un snapshot de solution, pas une
mutation de la collection d'entrée.

Ce premier contrat considère que les quatre voix partagent le même rythme.
Il refuse une ligne polyphonique ou une durée non positive et limite le
raisonnement au vocabulaire C majeur du noyau courant.
