# V20 — barrière de non-duplication

## Pourquoi cette barrière

L'écoute de V19 appelle naturellement davantage de contexte harmonique. Mais
plusieurs variantes de cette idée ont déjà été étudiées. V20 ne doit pas
rebaptiser une ancienne famille, relancer les mêmes calculs et présenter le
résultat comme une nouvelle expérience.

Cette note distingue :

- ce qui a déjà été testé et doit rester clos ;
- ce qui a été testé sous une forme opaque et peut seulement être remplacé par
  une représentation réellement plus intelligible ;
- la lacune précise que V20 est autorisé à explorer.

## Inventaire des expériences antérieures

| Idée | Expériences | Résultat | Décision V20 |
|---|---|---|---|
| préférence globale pour les triades et leurs renversements | V5.6, V6, V12, V19 | taux global contrôlable, mais un bon taux ne garantit pas le bon accord | **clos** : ne pas ajouter une nouvelle prime triadique |
| empreinte verticale relative à la basse | V6–V13 | signatures `central_bass_pcset` prédictives, mais opaques et sans fonction tonale | ne pas les réintroduire |
| empreinte verticale relative à la tonique globale | V6–V9 | certaines signatures sélectionnées, interprétation difficile et mauvaise généralisation générative | ne pas les réintroduire |
| transitions entre empreintes relatives à la basse | V7–V8 | plusieurs transitions apprises, puis rejetées comme modèle génératif | ne pas refaire des transitions de bitsets |
| classe tonale rare par voix et mode | V11 | aucun facteur sélectionné, même avec budget porté à 45 | **clos** |
| origine tonale locale à douze états latents | V5.11 | meilleure évidence, mais états non identifiés musicologiquement | **clos** tant que les statuts restent anonymes |
| intervalle × métrique × passage/broderie/résolution | V10, V13, V14 | quelques licences utiles ; une clause très prédictive dégrade fortement la génération | conserver les résultats, ne pas régénérer la même grille |
| mouvement de basse × degré relatif × métrique | V13 | 288 candidats proposés, aucun dans les trente facteurs retenus | ne pas relancer isolément |
| ajustement des poids par moments génératifs | V6–V17 | effets instables et interactions difficiles à expliquer | hors du cœur explicatif V20 |
| statut « triade complète » fort/faible | V19 | stable 5/5 et prédictif, mais ignore l'identité et la fonction de l'accord | conserver comme abstraction générale |

## Ce qui n'a pas encore été testé

Les anciennes empreintes encodent un ensemble de classes de hauteur par un
entier. Elles ne donnent pas simultanément et explicitement :

- la fondamentale relative à la tonique déclarée ;
- la qualité nommée de l'accord ;
- son renversement ;
- sa complétude ;
- la transition entre deux de ces analyses nommées.

Par exemple, une triade majeure en premier renversement sur le quatrième degré
est lisible comme un produit de quatre faits indépendants. Elle n'est pas
équivalente, pour l'humain, à `central_bass_pcset=529` accompagné d'un second
bitset relatif à la tonique.

Cette factorisation **degré × qualité × renversement × métrique × transition
K3** constitue la nouveauté admissible de V20.

## Résultat de V20A/V20B

V20A a confirmé l'intérêt de la représentation, mais aussi révélé une
dépendance linéaire exacte entre les facteurs généraux, faibles et forts.
V20B a supprimé cette redondance avant de répéter l'induction.

Sur cinq découvertes indépendantes, V20B obtient un noyau de quinze règles
unanimes (`Jaccard = 0,718`). Quatre statuts harmoniques nouveaux y figurent :

- triade majeure à l'état fondamental ;
- triade mineure à l'état fondamental ;
- accord complet au premier renversement ;
- septième de dominante complète.

Aucun degré de fondamentale statique n'est sélectionné. Le résultat apprend
donc **quelles formes d'accords** Bach privilégie, mais pas encore **quelle
fonction harmonique** doit apparaître à un endroit donné.

## Frontière après V20B

Les expériences suivantes restent interdites car elles répéteraient un test
déjà effectué :

- ajouter une nouvelle prime globale aux triades ou aux septièmes ;
- réintroduire les empreintes verticales anonymes ;
- relancer les transitions de notes de basse relatives à la tonique de V13 ;
- ajuster les mêmes poids à partir d'une nouvelle génération.

Une seule extension reste admissible : une relation entre les
**fondamentales analysées des accords nommés** de deux blocs voisins. Elle
n'est pas identique à la transition entre notes de basse de V13, car les
renversements séparent précisément fondamentale et basse.

Cette extension doit franchir deux contrôles avant induction :

1. mesurer la proportion de transitions dont les deux accords ont une analyse
   unique ;
2. mesurer la proportion de ces transitions qui diffère réellement de la
   transition entre notes de basse.

Si ce gain représentationnel est faible, la branche est close sans nouvelle
induction.

## Résultat V20C

Le gain représentationnel est fort (`67,58 %` des transitions analysées
diffèrent de la transition de basses), donc une induction unique a été
autorisée. Pourtant, aucune des 288 transitions symétriques n'est sélectionnée
parmi les trente colonnes. La base et la NLL sont exactement celles de V20B.

La famille est donc close sans réplication inter-plis ni génération. Les
progressions de fondamentales ont des marginaux musicologiquement familiers,
mais ne corrigent pas conditionnellement le modèle local sous cette
factorisation.

## Contraintes de conception

1. Aucun état harmonique latent ni case anonyme.
2. L'analyse d'un bloc est une fonction déterministe de ses notes, de sa basse
   et de la tonalité déclarée.
3. Les ambiguïtés sont conservées comme ambiguïtés ; elles ne sont pas
   résolues arbitrairement.
4. Les qualités proposées sont gelées avant l'induction.
5. L'expert définit le vocabulaire, jamais le signe, le poids ou la sélection
   d'une règle.
6. La première étape est un audit de couverture sur le train, pas une
   induction.
7. Si les accords complets nommés couvrent trop peu de blocs, V20 doit d'abord
   représenter explicitement les notes non harmoniques ; il ne doit pas
   compenser par une explosion de bitsets.

## Porte d'entrée vers l'induction

Une grammaire V20 ne sera construite que si l'audit train permet de répondre à
ces questions :

- quelle part des blocs forts et faibles reçoit une analyse unique ;
- quelle part est ambiguë ;
- quelle part est une triade reconnue plus une seule note étrangère ;
- quelles qualités et quels renversements ont un support sur plusieurs
  chorals ;
- combien de décisions deviennent effectivement distinguables par les
  nouveaux facteurs.

Cette porte évite de refaire V7/V8 sous un autre nom et de lancer une nouvelle
sélection avant de savoir ce que représente son vocabulaire.
