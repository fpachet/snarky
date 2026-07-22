# Plan de modélisation systématique de l’Éthique III

## Finalité

Le modèle doit représenter explicitement le caractère ontologique et
inférentiel du texte, sans transformer immédiatement chaque proposition en une
règle qui contient déjà sa conclusion.

Le corpus textuel, la reconstruction historique de Gondran et le modèle
systématique restent trois couches distinctes :

1. le corpus conserve le texte et ses références ;
2. le modèle historique reproduit les résultats de la présentation ;
3. le modèle systématique reconstruit les démonstrations depuis les
   définitions, postulats, résultats antérieurs et choix interprétatifs
   déclarés.

## Invariants méthodologiques

Pour toute proposition `E3Pxx` :

- la règle réutilisable correspondant à `E3Pxx` est interdite pendant sa
  propre démonstration ;
- les dépendances venant des parties I et II sont nommées et isolées ;
- les règles sont classées `textual`, `external_textual`, `compilation`,
  `interpretative` ou `historical_model` ;
- les contextes tels que `imagine` et `s_efforce_que` ne sont jamais aplatis ;
- l'absence d'un fait ne vaut ni `FAUX` ni `INEXISTANT` ;
- toute impossibilité est représentée par un statut explicite ou par une
  contrainte déclarée ;
- toute limite du moteur ou perte de sens est inscrite dans le manifeste du
  théorème ;
- une preuve systématique conserve sa chaîne minimale de règles et l'origine
  de chacune d'elles.

## Cycle de travail d'une proposition

Chaque proposition est traitée selon le même cycle :

1. relire l'énoncé, la démonstration, les corollaires et les scolies ;
2. résoudre les références canoniques, y compris « proposition précédente »
   et « même scolie » ;
3. identifier les entités, relations, états, contextes et oppositions ;
4. définir une ou plusieurs instanciations ground des hypothèses ;
5. définir les buts positifs, `FAUX` ou `INEXISTANT` ;
6. charger seulement les définitions, dépendances externes et propositions
   antérieures autorisées ;
7. exécuter le moteur et inspecter la provenance ;
8. ajouter des contre-tests qui ne doivent pas produire la conclusion ;
9. déclarer toute règle de compilation ou interprétative nécessaire ;
10. après validation, publier une règle réutilisable pour les propositions
    suivantes.

Les résultats possibles sont :

```text
proved
proved_with_external_textual_bridges
proved_with_compilation_rules
proved_with_interpretative_rules
not_proved
blocked_by_engine_capability
```

## Tranche 1 — E3P01–E3P03 : activité et passivité

Statut : premier fragment exécutable.

Concepts introduits :

```text
cause adéquate / cause partielle
idée adéquate / idée inadéquate
activité / passivité
action / passion
pensée / étendue
```

Ce fragment sert de fondation aux affects actifs de E3P58–E3P59. Il documente
également le recours à un témoin explicite pour E1P36, faute de création
existentielle dans le moteur actuel.

## Tranche 2 — E3P04–E3P08 : destruction et conatus

Statut : fragment exécutable achevé.

Concepts à introduire :

```text
cause_exterieure
detruit
affirme_essence
nie_essence
est_contraire_a
peut_coexister_avec
s_efforce_de_perseverer
essence_actuelle
duree_indefinie
```

Objectifs :

- E3P04 : expliciter pourquoi une chose ne peut être détruite que par une
  cause extérieure ;
- E3P05 : représenter l'incompatibilité de choses capables de se détruire ;
- E3P06 : dériver le conatus à partir de la conservation de la chose ;
- E3P07 : relier le conatus à l'essence actuelle ;
- E3P08 : représenter sa durée indéfinie.

Question moteur principale : déterminer si les statuts explicites suffisent
pour la contrariété et l'incompatibilité, ou si une primitive de contrainte est
nécessaire.

Critère de sortie : cinq manifestes exécutables, avec au moins un contre-test
par proposition et aucune négation par défaut.

Résultat : critère atteint. Les statuts `FAUX` suffisent pour ce fragment sans
ajout d'une primitive de contrainte. E3P05 et E3P08 utilisent une réfutation
bornée : une hypothèse nommée affirme un terme propositionnel, puis devient
`FAUX` quand ce terme est explicitement réfuté. Cette solution devra être
réévaluée si une proposition ultérieure exige une incompatibilité globale ou
une preuve par contradiction non bornée.

## Tranche 3 — E3P09–E3P11 : désir, joie et tristesse

Priorité immédiate.

Concepts à introduire :

```text
conscient_de
volonte
appetit
desir
puissance_agir
perfection
passage_vers_perfection_plus_grande
passage_vers_perfection_moindre
joie
tristesse
```

Objectifs : établir la relation entre conatus, volonté, appétit et désir, puis
représenter joie et tristesse comme passages entre états de puissance plutôt
que comme simples étiquettes.

Question moteur principale : choisir une représentation qualitative des
variations de puissance qui pourra ultérieurement recevoir une intensité
numérique ou symbolique.

## Tranche 4 — E3P12–E3P18 : imagination et association

Concepts à introduire :

```text
imagine
pose_existence
exclut_existence
association_memorielle
cause_accidentelle
similitude
fluctuation_ame
passe / present / futur
```

Objectifs : stabiliser les contextes intentionnels, l'imagination de présence,
les associations d'affects, les causes accidentelles et la temporalité.

Critère de sortie : aucune règle ne doit dériver `P` de `x imagine P` sans une
règle textuelle explicitement justifiée.

## Jalon A — E3P19–E3P22

Reconstruire systématiquement E3P19, E3P20, E3P21 et E3P22 depuis les tranches
précédentes, puis comparer :

1. la démonstration textuelle de Spinoza ;
2. la démonstration historique de Gondran ;
3. la démonstration systématique produite par Snarky.

Ce jalon doit identifier les règles historiques trop fortes, les étapes
condensées et les différences de profondeur de preuve. E3P21 doit aussi
documenter la dimension quantitative de l'intensité des affects.

## Tranche 5 — E3P23–E3P32 : affects sociaux et imitation

Concepts principaux : joie ou tristesse de la chose haïe, commisération,
faveur, indignation, envie, imitation des affects, similitude, ambition et
humanité.

E3P27 constitue le test principal des règles d'ordre 2 : les propositions
imaginées et les affects d'autrui doivent rester des termes imbriqués.

## Tranche 6 — E3P33–E3P44 : réciprocité, gloire et haine

Objectifs : reprendre systématiquement E3P33, puis représenter l'amour
réciproque, la gloire, la jalousie, les désirs issus des affects, la vengeance
et la transformation de la haine en amour.

Jalon B : la nouvelle preuve de E3P33 doit réellement utiliser la similitude,
contrairement à la chaîne historique actuelle.

## Tranche 7 — E3P45–E3P59 : généralisation et affects actifs

Concepts principaux : transfert des affects aux classes d'individus,
association des causes, étonnement, considération, considération de soi,
orgueil, abjection, diversité individuelle et affects actifs.

E3P58–E3P59 doivent réutiliser explicitement les résultats de E3P01–E3P03,
fermant ainsi la boucle architecturale de la partie III.

## Tranche 8 — définitions finales des affects

Les 48 définitions finales ne doivent pas devenir un simple glossaire. Pour
chacune :

1. identifier les propositions dont elle dépend ;
2. définir ses conditions nécessaires et distinctives ;
3. vérifier sa compatibilité avec les faits déjà dérivés ;
4. ajouter des contre-exemples distinguant les affects proches ;
5. signaler les définitions qui exigent intensité, temporalité ou modalité.

La définition générale des affects servira de test de cohérence global entre
corps, idée, puissance et détermination de la pensée.

## Ordre des extensions du moteur

Les extensions ne sont ajoutées que lorsqu'une démonstration les rend
nécessaires :

1. incompatibilité et contradiction explicites, à partir de E3P04–E3P05 ;
2. création existentielle bornée et témoins frais ;
3. contraintes qualitatives puis quantitatives sur l'intensité ;
4. disjonctions structurées et branches alternatives ;
5. preuve par contradiction ;
6. quantification plus formelle ;
7. méta-interprétation de règles représentées comme faits.

Chaque extension doit préserver les résultats du moteur de référence et rester
séparée des choix interprétatifs propres à Spinoza.

## Livrables de chaque tranche

Une tranche est terminée lorsque le dépôt contient :

- les nouveaux concepts ontologiques ;
- les règles exécutables et leur catalogue de provenance ;
- un manifeste par proposition ;
- des cas positifs et négatifs ;
- les chaînes minimales de preuve ;
- un rapport des règles interprétatives et capacités moteur manquantes ;
- une couverture mise à jour ;
- des tests différentiels garantissant que le modèle historique reste intact.

## Définition d'achèvement de l’Éthique III

Le travail systématique sera considéré comme complet lorsque :

- les 59 propositions auront un statut explicite et reproductible ;
- toutes les dépendances canoniques seront résolues ;
- les 48 définitions des affects seront reliées aux propositions ;
- toute règle interprétative sera identifiable ;
- chaque échec sera accompagné d'une explication ou d'une capacité moteur
  manquante ;
- les preuves historiques auront été comparées aux preuves systématiques ;
- les modifications de l'ontologie ou des règles recalculeront automatiquement
  les preuves et la couverture.
