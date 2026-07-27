# Bach rule induction

Ce dossier est le point d'entrée du projet de recherche visant à extraire des
règles lisibles des chorals de Bach, à les compiler pour Snarky et à les
comparer à CHORAL et DeepBach.

Le projet est volontairement séparé du prototype
[`harmonizer/`](../README.md) : les règles apprises n'entreront dans
l'harmoniseur principal qu'après validation, avec une provenance et des tests
explicites.

## Objectif expérimental

Comparer sur les mêmes pièces et la même tâche :

| ID | Système |
|---|---|
| `S0` | harmoniseur Snarky expert actuel |
| `S1` | Snarky enrichi de règles induites |
| `E0` | règles historiques de CHORAL reconstruites |
| `D0-legacy` | [DeepBach historique](../../../deepbach-reference/README.md), poids et code figés |
| `D0-modern` | port DeepBach maintenu et validé différentiellement |
| `H0` | combinaison DeepBach–Snarky |

La première tâche commune est l'harmonisation SATB d'un soprano imposé, avec
rythme, métrique, fermatas et métadonnées tonales contrôlés.

## Hypothèse centrale

Une part substantielle de la connaissance des chorals pourrait être comprimée
dans une petite base de règles intelligibles, locales et indépendantes,
conservant l'essentiel de la qualité musicale. Les informations de contexte
plus étendues — tonalité, métrique, phase de phrase, cadence ou rôle
structurel — sont représentées par des faits de statut explicites et testables.
Une règle consulte ces faits dans un voisinage borné, mais n'appelle jamais une
autre règle et ne dépend pas de l'ordre d'application.

Le résultat principal sera une frontière qualité–complexité : qualité tenue à
part en fonction du nombre de faits, de règles et de conditions. La complexité
des faits de statut est comptée afin de ne pas cacher le problème dans des
features opaques. Une conclusion négative — qualité exigeant beaucoup de
clauses, des règles non locales ou des statuts inintelligibles — répondrait elle
aussi à la question scientifique.

## État expérimental au 27 juillet 2026

Les fondations reproductibles sont en place :

- le manifeste historique Music21 3.1.0 reproduit les 352 chorals et les
  2 503 transpositions de l'article DeepBach ;
- un audit a regroupé dix familles de mélodies identiques et supprimé six
  traversées entre partitions ; le partage canonique réserve désormais
  251 chorals au train, 50 à la validation et 51 à un test encore scellé ;
- la baseline DeepBach Keras historique génère de nouveau des chorals dans le
  projet frère `deepbach-reference` ;
- l'appendice B de CHORAL est couvert sur 78 pages par 1 293 unités sources,
  775 cartes structurées et 7 tables ; la structure passe le validateur, mais
  389 unités restent explicitement en revue philologique ;
- un [premier POC différentiable](experiments/differentiable_rules_poc/) a
  extrait 20 350 décisions de soprano et appris des clauses depuis des
  hauteurs numériques.

Le POC retrouve sans noms musicologiques l'évitement des sauts supérieurs à
l'octave, une abstraction locale de mouvement de même signe entre soprano et
basse, puis les répétitions fortement évitées des classes numériques `0` et
`7`. Après dévoilement, celles-ci correspondent aux octaves/unissons et aux
quintes parallèles.

Les scores de validation de ces deux patrons sont `z = -4,410` et
`z = -4,715`. Ils deviennent positifs dans le contrôle où les choix sont
mélangés à l'intérieur de chaque pièce.

Le [POC V2.1](experiments/differentiable_rules_poc/V2_ANALYSIS.md) ajoute une
génération de colonnes sur les résidus. Après absorption des coûts généraux, il
sélectionne exactement les classes `0` et `7` pour les arrivées après saut en
même direction. Les deux clauses ont des poids négatifs, améliorent la
validation et sont extensionnellement équivalentes à `R-DIRECT-001/002` sur
301 401 états locaux valides par classe. Le contrôle mélangé ne sélectionne
aucune classe. Sur le partage sans fuite, le catalogue passe de 52 clauses
actives dans le V1 à 34 dans le V2, avec une NLL de validation de `1,624531`.
Le bootstrap groupé conserve un signe négatif sur validation dans 100 % des
réplications pour `0` et 99,6 % pour `7`.

Le [POC V2.2](experiments/differentiable_rules_poc/V2_2_ANALYSIS.md) étend
ensuite la tâche aux quatre voix. Avec un budget d'une règle par famille et un
contraste local contre les valeurs numériques voisines, il sélectionne la
classe mélodique `6` et la frontière d'overlap `0`. Le même sélecteur ne retient
rien après permutation des choix dans chaque voix et chaque choral. Les deux
formules sont équivalentes à `R-MELODY-002` et `R-OVERLAP-001` sur 1 993 et
534 050 états locaux testés.

Le [POC V2.3](experiments/differentiable_rules_poc/V2_3_ANALYSIS.md) a depuis
généralisé les parallèles aux six paires de voix. Il retient exactement les
classes `0` et `7`, contre aucune dans le contrôle permuté, et retrouve
`R-PARALLEL-001/002` sans désaccord sur 1 130 364 états par classe.

Le test final reste scellé.

Le [POC V2.4](experiments/differentiable_rules_poc/V2_4_ANALYSIS.md) réunit
enfin les sept règles récupérées dans un même modèle. Le catalogue améliore la
NLL de validation de `0,068188`, contre `0,006307` dans le contrôle permuté.
Chaque règle porte encore une contribution positive lorsque son poids est
neutralisé, les deux parallèles dominant l'ablation.

Le [POC V2.5](experiments/differentiable_rules_poc/V2_5_ANALYSIS.md) réentraîne
ensuite le modèle après retrait de chaque groupe. Aucun groupe n'est totalement
compensé : les pénalités restent positives pour les parallèles (`0,051384`),
la mélodie (`0,008753`), l'overlap (`0,005419`) et les mouvements directs
(`0,000997`). Le contrôle permuté ramène la contribution des parallèles à
environ zéro.

Le [POC V3.1](experiments/differentiable_rules_poc/V3_1_ANALYSIS.md) ouvre les
obligations. En testant uniformément les douze classes relatives à la tonique
globale, il retient uniquement `11` pour la conclusion « monter d'un
demi-ton ». Le taux de validation est `0,5259` contre `0,3074` attendu
(`z = 17,093`). Un contraste local, ajouté après diagnostic d'un faux positif,
rejette la classe dans le contrôle permuté.

Les [POC V3.2](experiments/differentiable_rules_poc/V3_2_ANALYSIS.md) et
[V3.3](experiments/differentiable_rules_poc/V3_3_ANALYSIS.md) raffinent cette
tendance avec des clauses courtes sur la voix, le mouvement de basse et le
mode. Le V3.3 retient sept proxys de progressions lisibles sur 864 candidats,
contre aucun dans le contrôle nul. Il distingue notamment le patron mineur
assimilable à `V→VI`, vérifié 25/25 fois au train et 11/11 en validation, de
son homologue majeur qui ne résout jamais dans les occurrences observées.

Le [POC V3.4](experiments/differentiable_rules_poc/V3_4_ANALYSIS.md) corrige
ensuite la recherche multiple par le maximum de 49 permutations complètes.
Les maxima nuls atteignent `6,205`. Une seule des sept clauses V3.3 reste
significative au niveau familial : `majeur + alto + basse 2→4`, proxy de
`vii°6→I6`, avec `min-z = 8,050` et `p FWER = 0,02`.

Le [POC V3.5](experiments/differentiable_rules_poc/V3_5_ANALYSIS.md) vérifie
ensuite cette étiquette sur les quatre voix. La progression exacte
`vii°6→I6` couvre 41/54 contextes train et 12/19 validation, tous résolus.
Elle constitue donc un noyau net, mais non une équivalence : la clause apprise
englobe aussi des accords de dominante ou des états ornés sur la même basse.

## Organisation

```text
bach_rule_induction/
├── README.md             point d'entrée et état du chantier
├── PLAN.md               protocole scientifique complet
├── sources/              audits de DeepBach et de CHORAL
├── corpus/               manifeste, partitions et transformations
├── features/             registre des descripteurs musicaux
├── rules/                RuleCards et règles Snarky induites
├── baselines/            adaptateurs S0, E0, D0 et H0
└── experiments/          configurations, sorties et métriques
```

Les partitions ou modèles externes volumineux ne doivent pas être recopiés
ici. Ils restent dans `third_party/` ou dans le cache ignoré du projet frère
[`deepbach-reference/`](../../../deepbach-reference/README.md) ; ce dossier ne
conserve que leurs manifestes, empreintes, licences et transformations
reproductibles.

## Plan d'action

### Phase 0 — sources et protocole

État : en cours.

- [x] copier et auditer le dépôt DeepBach, ses poids et son cache ;
- [x] conserver le rapport IBM RC 12628 et inventorier CHORAL ;
- [x] rédiger le protocole général ;
- [ ] trancher les décisions ouvertes minimales : unité temporelle, corpus,
      critères d'exclusion et tâche exacte.

### Phase 1 — corpus canonique

- [x] extraire les identifiants du corpus historique `music21` ;
- [x] vérifier les 352 pièces et 2 503 transpositions annoncées par l'article
      DeepBach ;
- [x] produire un manifeste avec empreinte, inclusion et motif d'exclusion ;
- [x] regrouper les variantes exactes de soprano avant le partage canonique ;
- auditer ensuite les variantes mélodiques proches ;
- [x] figer un premier partage déterministe par pièce avant toute augmentation ;
- convertir chaque pièce vers une représentation SATB commune et testée.

Livrable : `corpus/manifest.yaml`, les trois listes d'identifiants et des tests
de conservation notes–voix–rythme–fermata.

### Phase 2 — vocabulaire musical

- inventorier les faits déjà exposés par l'harmoniseur ;
- définir les features tonales, métriques, cadentielles et contrapuntiques ;
- associer définition, type, provenance et tests à chaque feature ;
- représenter explicitement les informations manquantes révélées par les
  erreurs de DeepBach.

Livrable : registre versionné dans `features/`.

### Phase 3 — règles humaines et CHORAL

- choisir dix règles pédagogiques comme formulations parentes ;
- [x] produire l'extraction structurée complète de CHORAL avec références de
      page et provenance ;
- revoir manuellement les unités et cartes signalées à faible confiance ;
- mesurer support, exceptions et dépendance au contexte dans Bach ;
- exprimer les variantes comme `MUST`, `NORMALLY`, `PREFER` ou `OBSERVED`.

Livrable : premières RuleCards vérifiées dans `rules/`.

### Phase 4 — induction et compilation Snarky

- [x] implémenter un premier énumérateur de patrons interprétables et bornés ;
- [x] lancer une première redécouverte aveugle sur sauts et parallèles ;
- [x] guider la recherche et les poids par gradient conditionnel avec L1 ;
- [x] exécuter un contrôle nul par mélange intra-pièce ;
- [x] remplacer la présélection marginale par une génération de colonnes
      réellement résiduelle ;
- tracer la frontière qualité–complexité sous plusieurs budgets ;
- sélectionner les règles par support, gain, stabilité et coût descriptif ;
- mesurer effets marginaux, ablations, redondances et interactions résiduelles ;
- enrichir les faits de statut sans introduire de dépendances entre règles ;
- [x] définir un premier statut tonal global et redécouvrir la classe `11` ;
- [x] utiliser les exceptions pour proposer `global_key_mode` comme feature ;
- [x] calibrer la première famille tonale sur 49 maxima de permutations ;
- [x] auditer harmoniquement la seule clause survivante ;
- comparer par ablation la clause chromatique et son noyau `vii°6→I6` ;
- valider sur un sous-ensemble non consulté pendant la découverte ;
- compiler les règles retenues en `R-LEARNED-*` ;
- vérifier chaque règle sur exemples, contre-exemples et cas limites.

Livrable : baseline `S1` reproductible.

Le premier résultat attendu n'est pas une règle nouvelle, mais le benchmark
[`rules/KNOWN_RULE_RECOVERY.md`](rules/KNOWN_RULE_RECOVERY.md) : le mineur doit
retrouver des sauts, chevauchements, parallèles et mouvements directs sans
accéder aux règles de référence pendant l'apprentissage.

La méthode d'induction est décrite dans
[`rules/INDUCTION_ALGORITHM.md`](rules/INDUCTION_ALGORITHM.md) : les notes
candidates d'une même position forment un groupe de décision, un beam search
génère des clauses courtes, puis un MaxEnt conditionnel sparse sélectionne une
base additive par génération de colonnes.

La boucle interne est :

```text
chercher → valider → expliquer → compiler → tester
→ diagnostiquer → modifier minimalement → sélectionner → recommencer
```

Elle s'exécute sur `train` et `validation` jusqu'à stabilisation du coude de la
frontière qualité–complexité. Elle ne vise pas zéro erreur. Les faits, règles,
seuils et métriques sont ensuite gelés avant l'unique ouverture du test final.

### Phase 5 — baseline DeepBach

- [x] démarrer `D0-legacy` dans un environnement isolé et sans réseau ;
- [x] enregistrer des sorties de référence avec graines fixes ;
- porter l'inférence vers `D0-modern` ;
- comparer les distributions et sorties des deux versions ;
- réentraîner sur le partage commun uniquement après validation du port.

Livrable : adaptateur DeepBach versionné et test différentiel.

### Phase 6 — désaccords et systèmes hybrides

- générer plusieurs harmonisations par soprano sans sélection manuelle ;
- auditer toutes les sorties avec Snarky ;
- classifier violations, règles manquantes et features manquantes ;
- construire des paires minimales ;
- tester rejet, réparation, masquage et ordre des choix Snarky par DeepBach.

Livrable : atlas des désaccords et comparaison `S0/S1/E0/D0/H0`.

### Phase 7 — évaluation et publication

- ouvrir le test final après gel du vocabulaire et des métriques ;
- mesurer correction, fidélité stylistique, nouveauté, stabilité et coût ;
- organiser une écoute en aveugle ;
- publier règles, statistiques, exemples, exceptions et résultats négatifs.

Livrable : traité exécutable de règles fondées sur corpus.

## Prochain sprint

Le premier sprint de provenance est terminé. L'ordre de travail immédiat est
désormais :

1. préenregistrer les seuils d'encoche, budgets et le partage groupé ;
2. [x] définir et tester les premiers faits de tonalité globale et de classe
   mélodique relative ;
3. dédupliquer les paires lors des attaques simultanées et mesurer la
   sensibilité ;
4. [x] extraire et analyser un premier lot d'exceptions authentiques ;
5. [x] ajouter les faits tonals minimaux et retrouver la première obligation ;
6. revoir les cartes CHORAL à faible confiance pertinentes pour ces familles ;
7. calibrer les maxima de familles sur plusieurs permutations ;
8. auditer les variantes mélodiques proches avant d'ouvrir le test.

La définition exhaustive des lots, métriques, risques et critères de sortie se
trouve dans [`PLAN.md`](PLAN.md).

## Sources déjà acquises

- [`sources/DEEPBACH.md`](sources/DEEPBACH.md) : audit du dépôt, des
  environnements et des ressources ;
- [`sources/CHORAL.md`](sources/CHORAL.md) : source primaire, organisation et
  protocole de reconstruction des règles d'Ebcioğlu.
