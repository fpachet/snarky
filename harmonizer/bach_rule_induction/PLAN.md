# Plan d'action — induction de règles lisibles à partir des chorals de Bach

## 1. Vision

Construire, à partir d'un corpus de chorals à quatre voix de J. S. Bach, une
grammaire musicale :

- exécutable par Snarky ;
- lisible et critiquable par un musicien ;
- plus précise et plus contextuelle que les règles pédagogiques usuelles ;
- accompagnée de statistiques, d'exemples et de contre-exemples ;
- évaluée face à DeepBach sur des tâches et des données identiques.

DeepBach n'est pas seulement un concurrent. Ses générations servent aussi de
contre-exemples pour découvrir :

- des règles absentes de la base Snarky ;
- des conditions manquantes dans une règle existante ;
- des features musicales que le vocabulaire courant ne sait pas représenter ;
- des règles Snarky trop strictes, contredites par des passages authentiques.

Le résultat visé est à la fois un harmoniseur, un outil d'analyse différentielle
et un traité de conduite des voix exécutable et fondé sur corpus.

Le protocole d'exécution de la première base apprise autonome est gelé dans
[`V4_PROTOCOL.md`](V4_PROTOCOL.md). Il définit la frontière entre échafaudage
et connaissance musicale, la politique de données après l'ouverture V3.8 et
les critères du premier banc génératif.

Le nouvel axe principal est
[`V5-K3-CLEAN`](V5_K3_CLEAN_PROTOCOL.md). Il repart d'une base vide avec une
seule hypothèse structurelle : toute règle inspecte trois blocs verticaux
consécutifs. Les règles et poids V1–V4 restent un benchmark externe, résumé
dans [`EXPERIMENT_HISTORY.md`](EXPERIMENT_HISTORY.md), et ne sont jamais
chargés pendant cette induction.

### 1.0 Jalon V5.1 exécuté

- [x] construire 68 263 décisions `train` et 13 202 décisions `validation` ;
- [x] dériver un domaine commun MIDI `36–81` du seul `train` ;
- [x] propager correctement une alternative dans le bloc suivant en cas de
      tenue ;
- [x] partir de zéro avec une distribution de registre apprise ;
- [x] générer 791 prédicats numériques sans noms de règles historiques ;
- [x] sélectionner et réajuster un budget compact de 12 règles ;
- [x] retrouver après gel les classes préservées `0` et `7` avec mouvement de
      même signe ;
- [x] exécuter un contrôle permuté de même budget ;
- [x] obtenir un gain NLL validation `1,145342`, contre `0,106239` sous le
      contrôle nul ;
- [x] alimenter un échantillonneur Gibbs avec le même évaluateur K3.

Les ablations réajustées sont terminées : chacune des douze règles conserve un
gain de validation positif après réapprentissage des onze autres. La première
colonne est aussi validée contre le maximum de 49 contrôles permutés sur tout
le catalogue. Avant toute promotion de la base complète, il reste à calibrer
le processus séquentiel entier sous permutations, auditer la clause
spécialisée de rang 11 et apprendre le rythme. Le Gibbs respecte désormais les
tenues réelles d'un squelette polyphonique et produit MusicXML/MIDI avec durées
distinctes ; il ne choisit pas encore lui-même `ATTACK/HOLD`.

### 1.0.1 Boucle générative contextuelle exécutée

- [x] convertir les chromaticismes observés en statut tonal explicite ;
- [x] apprendre une distribution relative à la tonique par voix et mode ;
- [x] énumérer mécaniquement les fingerprints verticaux sans noms d'accords ;
- [x] redécouvrir les ensembles `{0,4,7}`, `{0,3,7}` et `{0,3,8}` ;
- [x] distinguer une répétition attaquée d'une tenue ;
- [x] identifier automatiquement l'évitement spécialisé à la basse ;
- [x] comparer Bach, V5.5, V5.6 et V5.7 à rythme et graine identiques ;
- [x] utiliser MuSES comme exporteur canonique et music21 comme adaptateur
      d'import ou de mise en page source seulement.

### 1.0.2 Boucle chromatique multi-chorals exécutée

- [x] auditer les conditionnelles V5.7 sur les 50 chorals de validation ;
- [x] mesurer 20 chorals générés, deux graines par pièce ;
- [x] distinguer rareté globale et licences locales de passage, broderie,
      approche, résolution et métrique ;
- [x] réinduire V5.8 depuis zéro avec 72 interactions candidates ;
- [x] constater qu'aucune interaction chromatique n'entre dans les 28 règles ;
- [x] rejeter V5.8 malgré sa meilleure NLL, car ses générations sont
      significativement plus chromatiques ;
- [x] ajouter à V5.9 un gradient génératif
      `E_Bach[f] - E_Gibbs[f]` ;
- [x] sélectionner une base sur prédiction **et** fidélité des moments
      génératifs, avant ouverture du test scellé.

La conclusion méthodologique est importante : la pseudo-vraisemblance locale
ne suffit pas à sélectionner une base destinée à la génération Gibbs. V5.8
améliore la NLL validation de `1,120257` à `1,060328`, mais fait passer le taux
pondéré de classes rares générées de `5,925 %` à `8,029 %`, contre `4,828 %`
chez Bach. La génération libre du rythme reste postérieure à ce calibrage.

### 1.0.3 Calibration générative V5.9 exécutée

- [x] choisir 16 chorals du train par hash, sans sélection musicale ;
- [x] initialiser et maintenir des chaînes Gibbs persistantes ;
- [x] classer 54 statuts chromatiques des voix générées par contraste de
      moments ;
- [x] limiter la couche générative à huit règles lisibles ;
- [x] réduire la distance des moments train de `0,028467` à `0,016242` ;
- [x] geler les poids avant la campagne sur validation ;
- [x] réutiliser exactement les 20 pièces, deux graines et six balayages ;
- [x] ramener le taux rare pondéré à `4,529 %`, contre `4,828 %` chez Bach ;
- [x] réduire la MAE par pièce de `4,401` à `3,107` points ;
- [x] conserver le test scellé fermé.

V5.9 remplace V5.7 comme modèle chromatiquement calibré expérimental. Le gain
de MAE sur V5.7 est de `1,293` point, IC95 `0,384–2,203`, avec 14 pièces
améliorées sur 20. La NLL conditionnelle passe seulement de `1,120257` à
`1,130530`. La prochaine lacune n'est plus la surproduction moyenne, mais la
sous-production dans les chorals authentiquement très chromatiques : il faut
apprendre des licences positives et un statut de tonalité locale.

### 1.0.4 Audit résiduel V5.10

- [x] rééchantillonner de nouvelles chaînes V5.9 sur les 16 pièces train ;
- [x] auditer les 46 statuts de mouvement et métrique non sélectionnés ;
- [x] ajouter 22 interactions rares × empreinte verticale relative à la basse ;
- [x] constater qu'aucune licence positive ne dépasse à la fois `+0,5` point
      et `z=2` ;
- [x] apprendre un statut tonal local latent sur les trois blocs ;
- [x] tester si ce statut explique les chromaticismes authentiques que les
      empreintes instantanées ne distinguent pas.

La meilleure licence simple est la broderie rare d'alto en majeur
(`+0,409` point, `z=1,80`). La meilleure interaction verticale est l'ensemble
`{0,3,6,9}` relatif à la basse avec une classe rare d'alto en majeur
(`+0,335` point, `z=1,82`). Ces signaux sont plausibles mais insuffisamment
stables. Le prochain statut doit donc représenter une référence tonale locale
persistante, et non seulement une sonorité centrale.

### 1.0.5 Statut tonal latent V5.11

- [x] dédupliquer les attaques simultanées en 23 950 états train ;
- [x] apprendre par EM un HMM à douze références transposables ;
- [x] limiter chaque émission aux trois blocs K3 ;
- [x] tenir la validation entièrement hors de l'ajustement ;
- [x] comparer à un profil global MLE propre ;
- [x] obtenir un gain d'évidence validation de `+1,380406` par état ;
- [x] reclasser `80,96 %` des choix globalement rares comme localement communs ;
- [x] vérifier la robustesse pour des persistances `0,85`, `0,92` et `0,97`.

À la persistance centrale `0,92`, 33,38 % des états diffèrent de la tonique
globale, mais seulement 9,52 % des transitions changent de statut. L'entropie
postérieure normalisée vaut `0,030` : le HMM n'est pas indéterminé. Le taux
rare des 13 202 décisions de validation passe opérationnellement de `3,780 %`
avec référence globale à `1,242 %` avec référence locale.

Le statut peut désormais entrer dans le langage de règles. Pour la génération,
il faudra échantillonner alternativement les notes et les états latents afin de
ne jamais utiliser les voix authentiques cachées comme contexte.

Deux résultats scientifiques distincts sont recherchés :

1. **compression explicable** : déterminer quelle qualité d'harmonisation une
   petite base de règles locales et intelligibles peut atteindre face à
   DeepBach ;
2. **connaissance nouvelle sur Bach** : identifier ce que les traités, CHORAL
   et la base Snarky historique n'expriment pas, expriment trop généralement,
   ou présentent à tort comme absolu.

Le second objectif ne se réduit pas à produire de meilleures générations. Il
vise un **traité empirique du choral de Bach** : règles, domaines
d'application, forces, exceptions, exemples dans les partitions et gains
prédictifs tenus à part.

### 1.1 Hypothèse scientifique centrale

Le projet teste l'hypothèse qu'une part substantielle de la connaissance
nécessaire à l'harmonisation des chorals peut être comprimée dans une **petite
base de règles locales, indépendantes et musicalement intelligibles**, sans
perdre l'essentiel de la qualité obtenue par un modèle neuronal.

Cette hypothèse comporte cinq affirmations séparables :

1. **compacité** : le gain de qualité se concentre dans un nombre limité de
   règles et de conditions ;
2. **localité des règles** : toute règle porte sur la décision courante et un
   voisinage explicitement borné ;
3. **statuts explicites** : les informations de contexte plus étendues sont
   résumées par des faits intelligibles et bien définis — tonalité locale,
   position métrique, rôle structurel, phase de phrase ou type de cadence ;
4. **indépendance structurelle** : une règle ne déclenche, n'appelle ni ne
   modifie une autre règle ; son sens et son effet peuvent être examinés
   séparément, et l'ordre d'application ne change pas la sémantique ;
5. **résidu caractérisable** : ce que la base compacte n'explique pas révèle en
   priorité l'absence d'un fait de statut ou d'une règle locale, puis
   éventuellement une composante irréductiblement distributionnelle.

Une règle peut donc consulter un fait `authentic_cadence` sans devenir
non locale : la détection de la cadence appartient à la couche des faits, et la
règle reste locale sur la représentation enrichie. Cette séparation ne doit
pas dissimuler la complexité. Chaque fait de statut doit posséder une
définition musicale, un calcul testable, une provenance et un coût descriptif.
Un état latent neuronal ou un identifiant mémorisant un passage ne constitue
pas un statut intelligible.

« Indépendantes » signifie ici indépendantes dans l'architecture et dans leur
interprétation, non disjointes statistiquement : plusieurs règles peuvent
s'appliquer au même événement. Les conflits sont exposés et résolus par leur
statut déclaré (`MUST`, `NORMALLY`, `PREFER`, `OBSERVED`) et une sémantique
générale, jamais par un ordre caché ou par l'appel d'une règle à une autre.

L'hypothèse serait réfutée si une qualité compétitive exigeait des centaines de
micro-règles, de longues conjonctions, des règles inspectant directement des
fenêtres non bornées, des dépendances entre règles, ou des statuts opaques qui
ne feraient que déplacer le problème. Ce résultat négatif serait lui-même
important : il indiquerait précisément la limite d'une réduction symbolique du
style.

### 1.2 Reprise moderne d'un problème ancien

Ebcioğlu avait déjà posé une grande partie du problème scientifique avec
CHORAL : les traités ne suffisent pas, les règles doivent être confrontées aux
chorals réels, les exceptions sont contextuelles et les contraintes absolues
doivent être distinguées des heuristiques.

Le projet ne vise toutefois pas à reproduire CHORAL à l'identique :

1. le système exécutable, son environnement BSL et sa base de code ne sont plus
   disponibles publiquement sous une forme utilisable ;
2. nous disposons aujourd'hui d'un corpus symbolique numérisé, d'outils
   d'analyse musicale, de méthodes statistiques, de synthèse de règles, de
   modèles neuronaux conditionnels et d'une puissance de calcul sans commune
   mesure avec celle de 1987 ;
3. Snarky permet de représenter séparément faits, contraintes, préférences,
   choix, backtracking et provenance ;
4. DeepBach peut produire en quantité des exemples limites et contre-exemples
   que CHORAL ne pouvait pas exploiter ;
5. validation tenue à part, bootstrap, MDL, paires minimales et études d'écoute
   permettent de tester les règles plutôt que de dépendre uniquement de
   l'intuition du concepteur.

Les règles CHORAL constituent donc un état historique très élaboré de la
théorie manuelle. Le but moderne est de les récupérer comme hypothèses, puis de
les confirmer, les nuancer, les simplifier ou les dépasser par induction sur
corpus.

### 1.3 Deux bases de règles, puis leur union

La provenance des règles doit rester visible jusque dans les expériences et
les traces d'exécution. Trois configurations Snarky sont donc maintenues :

- `S-HISTORICAL` : règles écrites manuellement dans l'harmoniseur historique,
  conservées intactes ;
- `S-LEARNED` : uniquement les règles induites du corpus et compilées sous des
  identifiants `R-LEARNED-*` ;
- `S-HYBRID` : union déclarative des deux bases, sans copie ni changement
  silencieux du statut des règles.

La base apprise peut utiliser un fait musical conçu par l'humain sans que la
règle elle-même soit manuelle. Chaque entrée conserve donc deux provenances :

- `rule_origin` : `HUMAN_SNARKY`, `TREATISE`, `CHORAL`, `INDUCED` ou
  `HYBRID_REVISION` ;
- `feature_origin` : `OBSERVED`, `HUMAN_DEFINED`, `CORPUS_ANNOTATED`,
  `SYMBOLICALLY_INVENTED` ou `LEARNED_OPAQUE`.

Une règle dont le poids et les conditions sont sélectionnés sur corpus, mais
qui consulte les statuts harmoniques humains `vii°6` et `I6`, appartient bien à
`S-LEARNED`. Elle ne constitue toutefois pas une découverte autonome de ces
concepts. Cette nuance doit apparaître dans sa `RuleCard`.

`S-HISTORICAL` demeure un patrimoine et une baseline : l'induction ne le
réécrit jamais. Toute correction ou extension proposée est créée dans une base
séparée et évaluée par ablation.

## 2. Questions de recherche

1. Quelle part du style des chorals peut être décrite par une base compacte de
   règles symboliques strictement locales sur des faits de statut explicites ?
2. Quelles règles traditionnelles deviennent plus exactes lorsqu'on explicite
   la voix, la métrique, la fonction harmonique, le renversement, la phrase ou
   la cadence ?
3. Quelles régularités sont suffisamment stables pour devenir des contraintes,
   et lesquelles doivent rester des préférences probabilistes ?
4. Quelles erreurs de DeepBach correspondent à une règle connue, à une règle
   absente ou à une feature encore inexistante ?
5. Quelles tournures authentiques rejetées par Snarky révèlent une exception ou
   une formulation symbolique trop générale ?
6. Un système hybride peut-il conserver la diversité de DeepBach tout en
   apportant les garanties, la provenance et les explications de Snarky ?
7. Quelle précision descriptive peut-on gagner par rapport aux formulations
   pédagogiques sans produire un catalogue illisible de cas particuliers ?
8. Quelles règles du système historique CHORAL d'Ebcioğlu sont retrouvées,
   précisées, contredites ou simplifiées par l'induction sur corpus ?
9. Où se situe le coude de la frontière entre complexité symbolique et qualité :
   combien de faits, de règles et de conditions faut-il avant que les
   gains supplémentaires deviennent négligeables ?
10. Les interactions apparentes entre règles peuvent-elles être reformulées
    comme des statuts musicaux explicites tout en conservant des règles locales
    et indépendantes ?
11. Quelles décisions de Bach restent systématiquement mal classées après
    conditionnement sur les règles des traités, de CHORAL et de Snarky ?
12. Parmi ces résidus, lesquels révèlent une règle absente, un raffinement
    contextuel, une exception régulière ou une formulation historique trop
    stricte ?
13. Une grammaire empirique enrichie explique-t-elle les chorals tenus à part
    significativement mieux que les règles pédagogiques seules, à complexité
    explicitement mesurée ?
14. Quelles régularités sont propres à Bach, par opposition aux conventions
    plus générales du choral tonal observables chez d'autres compositeurs ?

## 3. Livrables

### 3.1 Corpus canonique

Une représentation commune aux expériences Snarky et DeepBach, conservant :

- les quatre voix et leur orthographe musicale ;
- hauteurs, classes de hauteur et degrés relatifs à la tonalité locale ;
- attaques, tenues, silences, durées et liens de prolongation ;
- position et niveau métriques ;
- tonalités et tonicisations locales ;
- phrases, fermatas et cadences ;
- accords, fonctions et renversements, avec provenance de l'analyse ;
- mouvements mélodiques et intervalles verticaux.

### 3.2 Registre de features

Chaque feature doit posséder :

- un identifiant stable ;
- une définition musicale ;
- une sémantique de calcul non ambiguë ;
- son domaine et ses unités ;
- sa provenance : donnée, annotation, analyse ou dérivation Snarky ;
- des exemples positifs, négatifs et limites ;
- une indication de disponibilité à l'entraînement et à la génération.

### 3.3 Catalogue de règles

Chaque règle découverte doit être publiée sous trois formes :

1. une formulation destinée au musicien ;
2. une fiche empirique avec statistiques et exceptions ;
3. une formulation Snarky exécutable avec un identifiant `R-LEARNED-*`.

Le catalogue publie séparément les manifestes de `S-HISTORICAL`,
`S-LEARNED` et `S-HYBRID`. Une règle apprise ne doit jamais être rangée dans le
dossier historique, même lorsqu'elle redécouvre exactement une règle humaine.
Dans ce cas, la `RuleCard` induite pointe vers l'implémentation historique et
enregistre l'équivalence sans dupliquer le code.

### 3.4 Banc d'essai reproductible

Le banc compare au minimum :

- `S-HISTORICAL` : harmoniseur Snarky expert actuel ;
- `S-LEARNED` : solveur avec seulement les règles induites et une politique de
  choix par défaut explicitement neutre ;
- `S-HYBRID` : Snarky historique enrichi des règles induites ;
- `E0` : règles CHORAL d'Ebcioğlu reconstruites ou sous-ensemble déclaré ;
- `D0` : DeepBach reproduit avec une version et des poids identifiés ;
- `H0` : DeepBach comme heuristique ou générateur, Snarky comme contrôleur.

`BACH-REFERENCE` désigne la réalisation authentique tenue à part. Ce n'est pas
un générateur supplémentaire : elle fournit, pour chaque entrée commune, le
choix observé, les statistiques descriptives et l'ancrage de l'évaluation
humaine.

La comparaison principale harmonise le même soprano de test avec toutes les
bases. Une seconde condition peut imposer soprano et basse. Plusieurs sorties
à graines fixées sont conservées sans sélection manuelle. La base
`S-LEARNED`, nécessairement incomplète dans les premières versions, doit
déclarer sa politique de choix par défaut afin de ne pas attribuer aux règles
apprises les préférences cachées du solveur.

La source, les ressources distribuées, leurs empreintes et les limites de
reproductibilité de `D0` sont consignées dans
[`sources/DEEPBACH.md`](sources/DEEPBACH.md). L'audit distingue `D0-legacy`,
nécessaire pour vérifier le comportement historique, et `D0-modern`, port
maintenu utilisant un manifeste de corpus et un partage par pièce.

### 3.5 Atlas des désaccords

Une collection inspectable de paires minimales et de cas complets où :

- DeepBach viole une règle Snarky ;
- Snarky rejette un passage de Bach ;
- Snarky et DeepBach proposent des réalisations différentes ;
- une erreur perceptible n'est pas exprimable avec les features disponibles.

### 3.6 Baseline historique CHORAL

Reconstruire un catalogue versionné des règles du système CHORAL d'Ebcioğlu à
partir de l'appendice B du rapport IBM RC 12628. La source, son organisation et
le protocole de reconstruction sont documentés dans
[`sources/CHORAL.md`](sources/CHORAL.md).

Cette baseline, nommée `E0`, distingue fidèlement :

- règles de production ;
- contraintes absolues ;
- heuristiques ordonnées ;
- vues du squelette, du remplissage, des tranches verticales, des lignes
  mélodiques et de l'analyse schenkerienne.

`E0` est une source historique et une hypothèse musicale à tester, pas un oracle
de vérité sur Bach.

### 3.7 Traité empirique de Bach

Le livrable scientifique final n'est pas seulement un fichier de règles. Il
présente chaque famille sous une forme consultable par un musicien :

- formulation pédagogique ou historique de départ ;
- formulation empirique enrichie ;
- contexte exact où la règle gagne ou perd en force ;
- statut `MUST`, `NORMALLY`, `PREFER` ou `OBSERVED` ;
- exemples authentiques, exceptions et paires minimales ;
- support par pièce, incertitude et résultat tenu à part ;
- différence prédictive par rapport à la formulation historique ;
- code Snarky et provenance de chaque fait consulté.

Ce traité distingue explicitement :

1. `REDISCOVERY` : équivalence avec une règle connue ;
2. `REFINEMENT` : domaine, force ou exceptions d'une règle connue rendus plus
   précis ;
3. `NEW_REGULARITY` : information prédictive stable et non redondante dont
   aucune formulation équivalente n'a été retrouvée dans les sources auditées ;
4. `CONTRADICTION` : comportement authentique et régulier incompatible avec la
   formulation historique ;
5. `UNRESOLVED` : effet statistique encore sans interprétation musicale
   suffisamment claire.

## 4. Principes méthodologiques

### 4.1 Séparer description et prescription

La fréquence d'une tournure dans Bach ne suffit pas à en faire une obligation.
Le système distingue :

- `MUST` : contrainte sans exception connue dans le périmètre déclaré ;
- `NORMALLY` : règle très stable avec exceptions caractérisées ;
- `PREFER` : préférence stylistique ou distributionnelle ;
- `OBSERVED` : régularité descriptive encore insuffisamment interprétée.

Une absence dans un corpus limité n'est jamais, à elle seule, la preuve d'une
interdiction musicale.

### 4.2 Séparer découverte et évaluation

- Les features candidates peuvent être conçues à partir du corpus
  d'entraînement et des erreurs de développement.
- Les seuils et règles sont sélectionnés sans consulter le test final.
- Le jeu de test n'est ouvert qu'après gel du vocabulaire, des règles et des
  métriques principales.
- Toute modification motivée par le test final crée une nouvelle version de
  l'expérience et exige un nouveau test indépendant.

### 4.3 Privilégier la stabilité

Une règle intéressante doit :

- se retrouver dans plusieurs chorals et non dans une seule œuvre ;
- rester stable par bootstrap et par sous-corpus ;
- apporter une information au-delà d'une règle plus générale ;
- résister aux changements raisonnables d'analyse harmonique ;
- être formulable avec un petit nombre de conditions musicales intelligibles.

### 4.4 Conserver les exceptions

Les exceptions ne sont ni supprimées ni noyées dans une moyenne. Elles sont
classées comme :

- erreur ou ambiguïté du corpus ;
- erreur d'analyse automatique ;
- modulation ou tonicisation mal représentée ;
- licence contrapuntique attestée ;
- rôle mélodique ou structurel absent ;
- exception expliquée par une feature supplémentaire ;
- cas encore inexpliqué.

### 4.5 Apprendre au-delà des traités

La recherche de nouveauté est **résiduelle**. Avant de proposer une règle
nouvelle, on ajuste une baseline contenant les règles historiques
représentables et on recherche les clauses qui expliquent encore les choix de
Bach mal classés :

```text
traités + CHORAL + Snarky historique
→ prédictions sur les décisions de Bach
→ résidus conditionnels
→ recherche de clauses locales courtes
→ règle candidate
→ ablation contre la baseline historique
```

La nouveauté n'est jamais déduite de l'absence d'un énoncé dans un seul traité.
Une candidate ne reçoit le statut `NEW_REGULARITY` que si :

- elle améliore la prédiction sur des pièces jamais utilisées pour la
  découvrir ;
- son gain reste positif lorsque les règles historiques proches sont déjà
  présentes ;
- elle est stable par bootstrap de pièces et sous analyses harmoniques
  plausibles ;
- une version plus courte ou une règle connue ne fournit pas la même
  information ;
- sa formulation et ses exceptions sont auditables musicalement ;
- la recherche bibliographique et l'audit de CHORAL ne trouvent pas
  d'équivalent.

Un `REFINEMENT` est un résultat scientifique à part entière. Préciser la voix,
la métrique, la fonction, le renversement ou les exceptions d'une règle
générale peut mieux rendre compte de Bach qu'une nouvelle interdiction
spectaculaire mais rare.

Enfin, « propre à Bach » exige un contraste. Une règle induite uniquement sur
Bach est d'abord qualifiée de **descriptive de Bach**. Elle ne devient
**bachienne différentielle** que si son support ou sa force diffère
significativement dans un corpus comparable d'autres compositeurs, avec la
même représentation et le même protocole.

## 5. Corpus et protocole de partage

### 5.1 Corpus principal

Reprendre autant que possible le corpus `music21` et les critères de filtrage
de l'expérience DeepBach originale. L'article DeepBach indique 352 pièces
après retrait des chorals instrumentaux et de certains passages non
monophoniques :

<https://proceedings.mlr.press/v70/hadjeres17a.html>

Le manifeste du corpus doit enregistrer pour chaque pièce :

- identifiant et source ;
- empreinte du fichier ;
- motifs d'inclusion ou d'exclusion ;
- problèmes de voix, de rythme ou d'orthographe ;
- transformations appliquées ;
- appartenance à `train`, `validation` ou `test`.

### 5.2 Corpus secondaire

Le corpus DCML peut servir d'audit externe et fournir des annotations
harmoniques. Sa documentation signale toutefois des altérations incorrectes
issues de certaines conversions MuseScore ; ces données ne doivent donc pas
être traitées comme un oracle sans contrôle :

<https://dcmlab.github.io/bach_chorales/>

Un corpus de contraste, constitué de chorals comparables d'autres compositeurs,
sera ajouté dans une expérience séparée. Il ne sert pas à sélectionner les
règles descriptives de Bach, mais à tester ensuite leur spécificité. Les
différences de période, fonction liturgique, instrumentation, longueur et
qualité d'encodage devront être contrôlées avant toute qualification de règle
« bachienne ».

### 5.3 Prévention des fuites

- Partager par pièce avant toute transposition ou augmentation.
- Regrouper les variantes d'un même choral dans le même sous-ensemble.
- Détecter les doublons ou quasi-doublons de mélodie.
- Ne jamais placer une transposition dans un autre sous-ensemble que son
  original.
- Publier les identifiants des trois sous-ensembles.
- Calculer la nouveauté des générations par rapport au train seulement.

### 5.4 Tâche commune initiale

Commencer par une tâche contrôlable :

> Harmoniser un soprano imposé en conservant son rythme, sa métrique, ses
> fermatas et les métadonnées tonales autorisées.

Les quatre systèmes reçoivent exactement les mêmes informations. Les
expériences ultérieures pourront couvrir la basse donnée, l'inpainting
arbitraire, la réparation locale et la génération moins contrainte.

## 6. Ontologie musicale et familles de features

### 6.1 Features déjà proches du modèle Snarky actuel

- voix, tessiture, hauteur et classe de hauteur ;
- accord, degré, fonction et renversement ;
- position métrique hiérarchique ;
- rôle mélodique ;
- mouvement conjoint, saut et direction ;
- intervalles verticaux et leur classe ;
- doublure et complétude de l'accord ;
- cadence et rythme harmonique ;
- attaque, tenue et continuation de voix.

### 6.2 Extensions prioritaires

- tonalité locale, tonicisation et modulation ;
- orthographe enharmonique et intervalle diatonique ;
- frontières et profondeur de phrase ;
- note structurelle contre ornement local ;
- dissonance préparée, attaquée, tenue et résolue ;
- échange et croisement temporaire de voix ;
- mouvement composé sur plusieurs attaques ;
- fausses relations chromatiques ;
- six-quatre de passage, de broderie et de pédale ;
- accords de septième et renversements supplémentaires ;
- séquences, pédales et prolongations harmoniques ;
- densité, registre et direction à l'échelle de la phrase.

Une nouvelle feature n'entre dans le registre qu'avec une définition, un
calcul testable et au moins un cas où elle distingue une paire autrement
indiscernable.

## 7. Forme d'une règle humaine

Une `RuleCard` contient au minimum :

```yaml
id: R-LEARNED-TENDENCY-001
title: Résolution cadentielle de la sensible au soprano
status: NORMALLY
statement: >
  Au soprano, une sensible appartenant à la dominante d'une cadence
  authentique se résout normalement vers la tonique par mouvement conjoint.
scope:
  voices: [soprano]
  context: authentic_cadence
conditions:
  - local_scale_degree == 7
  - harmonic_role == dominant
  - next_harmonic_role == tonic
conclusion:
  - next_local_scale_degree == 1
  - melodic_motion == ascending_step
statistics:
  train_support: null
  train_confirmation: null
  validation_support: null
  validation_confirmation: null
exceptions: []
bach_examples: []
counterexamples: []
snarky_rule: rules/learned/R-LEARNED-TENDENCY-001.rules
```

Les statistiques finales seront calculées par le pipeline, jamais saisies à la
main.

### 7.1 Raffinement d'une règle pédagogique

Le système doit pouvoir transformer :

> La sensible monte à la tonique.

en une famille plus précise :

- comportement au soprano dans une cadence authentique ;
- comportement dans une voix intérieure ;
- dominante résolue sur `vi` ;
- sensible ornementale ;
- tonicisation locale ;
- note tenue ou échange de voix.

La précision vient de conditions musicales interprétables, pas de
l'identifiant de la pièce ni d'une conjonction arbitraire de hauteurs.

## 8. Induction des règles

### 8.1 Langage de patrons borné

Énumérer des patrons sur :

- une position verticale ;
- une transition entre deux positions ;
- un contour mélodique de trois positions ;
- les faits de statut attachés à ces positions.

Les patrons peuvent tester voix, métrique, rôle, fonction, renversement,
intervalle, direction, durée et tonalité locale. Une règle ne parcourt pas une
phrase et n'appelle pas une autre règle : phrase, cadence, prolongation ou rôle
structurel doivent être représentés par des faits explicites. Une limite sur le
voisinage et sur le nombre de conditions empêche la mémorisation du corpus.

L'algorithme concret combine beam search de clauses, MaxEnt conditionnel sparse
et génération de colonnes. Sa spécification détaillée se trouve dans
[`rules/INDUCTION_ALGORITHM.md`](rules/INDUCTION_ALGORITHM.md).

### 8.2 Statistiques

Pour chaque candidat, calculer :

- support et nombre de pièces distinctes ;
- taux de confirmation et intervalle d'incertitude ;
- gain d'information par rapport à la règle parente ;
- taux d'exception ;
- stabilité par bootstrap ;
- stabilité entre tonalités, voix et sous-corpus ;
- longueur descriptive.

### 8.3 Sélection

Utiliser un objectif inspiré de MDL :

```text
qualité tenue à part + couverture + stabilité
- nombre de règles
- nombre total de conditions
- nombre et coût descriptif des faits de statut
- exceptions inexpliquées
```

Préférer une règle générale avec deux exceptions musicales intelligibles à
vingt règles microscopiques.

Ne pas réduire ces termes à une pondération arbitraire unique. Produire une
frontière de Pareto qualité–complexité sous plusieurs budgets préenregistrés,
puis identifier son coude. Pour chaque point, publier au minimum le nombre de
faits et de règles, le nombre total et maximal de conditions, le voisinage
local maximal et la qualité sur données tenues à part.

### 8.4 Test de l'architecture faits–règles

Comparer des bases utilisant le même langage de règles locales avec des
vocabulaires de faits progressivement enrichis :

1. faits directement observés : voix, hauteur, durée, métrique ;
2. statuts tonals, harmoniques et cadentiels explicites ;
3. statuts structurels supplémentaires proposés par l'analyse des résidus.

Pour chaque règle et famille de règles, mesurer :

- le gain marginal lorsqu'elle est ajoutée à la base ;
- la perte par ablation lorsqu'elle en est retirée ;
- la redondance avec les autres règles ;
- les interactions apparentes entre règles ;
- la stabilité de ces effets entre pièces, tonalités et voix ;
- la possibilité de prédire l'effet conjoint à partir des effets séparés.

Une interaction persistante déclenche la recherche d'un fait de statut
explicite qui rende les deux règles indépendantes. Si cela exige un fait opaque,
une dépendance entre règles ou une explosion du catalogue, le cas est conservé
comme contre-exemple à l'hypothèse. Le catalogue publie le graphe biparti
`règles → faits consultés`, mais aucune arête `règle → règle`. La base préférée
est la plus petite située au coude de la frontière de Pareto, pas nécessairement
celle qui maximise la qualité absolue.

### 8.5 Validation humaine

Avant publication, chaque règle est relue pour déterminer :

- si ses conditions ont un sens musical ;
- si elle reformule une règle connue ou apporte une précision nouvelle ;
- si ses exceptions sont auditables ;
- si le vocabulaire convient à un musicien ;
- si son statut `MUST`, `NORMALLY`, `PREFER` ou `OBSERVED` est justifié.

L'algorithme propose des règles ; il ne décide pas seul de leur interprétation
théorique.

### 8.6 Boucle d'apprentissage et de révision

La boucle est une induction guidée par contre-exemples :

```text
faits et résidus
→ recherche de règles candidates
→ validation statistique par pièce
→ formulation humaine
→ compilation Snarky
→ tests descriptifs, différentiels et génératifs
→ diagnostic des contre-exemples
→ révision minimale
→ sélection sur la frontière qualité–complexité
→ nouveaux résidus
```

Chaque itération utilise uniquement `train` pour rechercher ou modifier les
règles et `validation` pour les sélectionner. Les tests unitaires et musicaux
peuvent être exécutés à chaque tour, mais le corpus `test` final reste fermé
jusqu'au gel des faits, du catalogue, des seuils et des métriques. Une règle
modifiée après consultation du test appartient à une nouvelle expérience et
exige un nouveau test indépendant.

#### Étape A — proposer

Rechercher sur `train` une implication locale courte qui explique un résidu,
classe mieux le choix de Bach parmi les choix localement possibles ou distingue
une paire minimale. Une candidate doit utiliser uniquement des faits
enregistrés, respecter le voisinage maximal et le budget de conditions.

#### Étape B — filtrer statistiquement

Mesurer le support en **pièces distinctes**, pas seulement en événements, car
les notes d'un même choral ne sont pas indépendantes. Exiger :

- un effet et un support minimaux préenregistrés ;
- un intervalle d'incertitude calculé en regroupant par pièce ;
- une stabilité par bootstrap de pièces et par tonalité ;
- un gain conditionnel au catalogue déjà retenu ;
- une correction pour la multiplicité des candidats explorés ;
- une confirmation sur `validation`.

Une faible valeur `p` ne suffit jamais. Une candidate rare, redondante,
instable ou gagnante uniquement sur `train` est rejetée ou conservée comme
`OBSERVED`.

#### Étape C — rendre intelligible et compiler

Produire simultanément :

1. une phrase musicale compréhensible ;
2. une `RuleCard` avec faits, portée, statistiques et exemples ;
3. une règle Snarky exécutable.

Le cycle de vie technique
`CANDIDATE → SUPPORTED → COMPILED → ACCEPTED → FROZEN` est distinct de la force
musicale `MUST`, `NORMALLY`, `PREFER` ou `OBSERVED`. La significativité
statistique ne détermine pas automatiquement cette force.

#### Étape D — tester à quatre niveaux

1. **formel** : tests positifs, négatifs, limites, invariance par transposition
   et indépendance vis-à-vis de l'ordre des règles ;
2. **descriptif** : couverture, exceptions et pouvoir prédictif sur `train` et
   `validation` ;
3. **différentiel** : paires minimales, passages de Bach rejetés, sorties
   DeepBach et ablation de la règle ;
4. **génératif** : satisfaisabilité, qualité, diversité, temps de recherche et
   nouveaux défauts produits avec et sans la règle.

Une règle peut être statistiquement exacte et néanmoins inutilisable si elle
rend la génération impossible, duplique une autre règle ou dégrade fortement
la diversité.

#### Étape E — diagnostiquer et modifier

Chaque contre-exemple est d'abord classé. Une révision applique une seule
opération explicite :

- **spécialiser** en ajoutant un fait de statut intelligible ;
- **généraliser** en retirant une condition inutile ;
- **scinder** une règle en deux contextes musicaux nommés ;
- **fusionner** des règles redondantes ;
- **assouplir** de `MUST` vers `NORMALLY` ou `PREFER` ;
- **durcir** seulement après validation indépendante et examen des exceptions ;
- **ajouter un fait** si deux cas localement indiscernables exigent des
  décisions différentes ;
- **supprimer** une règle instable, redondante ou nuisible.

La règle révisée reçoit une nouvelle version et repasse toute la boucle. Les
exceptions ne sont jamais réparées par un identifiant de pièce, une hauteur
absolue arbitraire, un appel à une autre règle ou un ordre d'application caché.

#### Étape F — sélectionner et arrêter

À chaque tour, conserver la plus petite base non dominée sur la frontière
qualité–complexité. La boucle ne cherche pas zéro erreur. Elle s'arrête et gèle
une version lorsque les conditions préenregistrées suivantes sont réunies :

- aucun nouveau fait ou règle n'améliore significativement `validation` sous
  le budget de complexité ;
- plusieurs tours consécutifs n'ont pas déplacé le coude de la frontière ;
- les gains marginaux des règles restantes sont négligeables ou instables ;
- les conflits, exceptions et résidus importants sont classés et publiés ;
- les ablations confirment que chaque règle retenue apporte un effet propre ;
- la base reste satisfaisable, générative et relisible par un humain ;
- le budget maximal de règles, de conditions et de faits est respecté.

Après ce gel, le jeu `test` est ouvert une seule fois. Il estime la
généralisation de la base figée ; il ne sert pas à lancer une nouvelle révision
silencieuse. Le résultat final est donc le **coude stable d'une frontière**, et
non un catalogue ayant mémorisé toutes les exceptions du corpus.

## 9. DeepBach comme générateur de contre-exemples

### 9.1 Production contrôlée

Pour chaque soprano du jeu d'évaluation :

- produire plusieurs échantillons avec des graines enregistrées ;
- conserver les probabilités ou rangs disponibles ;
- interdire la sélection manuelle des meilleurs exemples ;
- sérialiser entrée, sortie, paramètres et version du modèle ;
- analyser chaque sortie avec les mêmes règles Snarky.

### 9.2 Taxonomie des désaccords

Chaque erreur ou désaccord reçoit une catégorie :

1. `KNOWN_RULE_VIOLATION` : une règle existante la détecte ;
2. `MISSING_RULE` : les features existent, mais aucune règle ne les combine ;
3. `MISSING_FEATURE` : le jugement ne peut pas être formulé ;
4. `OVERSTRICT_RULE` : Snarky rejette une tournure authentique ou acceptable ;
5. `ANALYSIS_ERROR` : tonalité, accord, rôle ou segmentation erronés ;
6. `CORPUS_ERROR` : donnée source douteuse ;
7. `AESTHETIC_DISAGREEMENT` : préférence non consensuelle ;
8. `UNEXPLAINED` : cas conservé pour analyse ultérieure.

### 9.3 Paires minimales

Pour une sortie fautive, chercher une correction minimale :

- modifier une note ou une tenue ;
- conserver autant que possible le reste du contexte ;
- recalculer les faits Snarky ;
- déterminer le plus petit ensemble de features qui sépare les deux versions.

Si aucune feature existante ne les sépare, le cas devient un candidat
`MISSING_FEATURE`.

### 9.4 Boucle de raffinement

```text
génération DeepBach
        ↓
audit Snarky et écoute
        ↓
classification du désaccord
        ↓
paire minimale
        ↓
feature ou règle candidate
        ↓
cycle complet de validation et révision § 8.6
        ↓
nouvelle campagne de génération
```

Cette boucle s'applique symétriquement aux chorals authentiques rejetés par
Snarky.

## 10. Systèmes hybrides

Évaluer progressivement :

1. **Audit** : DeepBach génère, Snarky annote sans modifier.
2. **Rejet** : éliminer les échantillons qui violent une contrainte `MUST`.
3. **Réparation** : rouvrir les seules notes impliquées et chercher une
   correction minimale.
4. **Masquage** : restreindre les notes disponibles à partir des domaines
   Snarky avant l'échantillonnage.
5. **Heuristique** : utiliser les probabilités DeepBach pour ordonner ou
   pondérer les `CHOICE` Snarky.

L'étape 5 est la cible hybride privilégiée : Snarky conserve la sémantique des
contraintes et DeepBach fournit une préférence apprise. Une probabilité
neuronale ne doit jamais être présentée comme la justification d'une règle.

## 11. Évaluation

### 11.1 Conformité

- violations par famille `R-*` et par nombre d'attaques ;
- proportion de sorties sans violation `MUST` ;
- taux d'échec de génération ;
- satisfaction des notes, rythmes et cadences imposés.

### 11.2 Fidélité stylistique

- distributions d'intervalles mélodiques par voix ;
- mouvements relatifs entre voix ;
- accords, fonctions, renversements et transitions ;
- doublures et espacements ;
- traitement des dissonances ;
- métrique des changements harmoniques ;
- profils et préparations de cadence.

Les distances sont calculées globalement et par contexte afin d'éviter qu'une
bonne moyenne masque une erreur systématique.

### 11.3 Généralisation et nouveauté

- résultat sur pièces tenues à part ;
- plus proche fragment du corpus d'entraînement ;
- taux de motifs copiés à différentes longueurs ;
- diversité entre échantillons pour une même entrée ;
- stabilité après transposition.

### 11.4 Qualité des règles

- couverture du corpus ;
- précision sur validation et test ;
- frontière qualité–nombre de règles ;
- nombre total, moyen et maximal de conditions ;
- voisinage local maximal ;
- nombre de faits de statut et coût descriptif de leur définition ;
- proportion des règles dont tous les faits sont jugés intelligibles ;
- gain marginal et perte par ablation de chaque règle ;
- redondances et interactions résiduelles entre règles ;
- nombre d'exceptions expliquées et inexpliquées ;
- stabilité par bootstrap ;
- proportion jugée compréhensible et utile par des musiciens ;
- gain de précision par rapport à l'énoncé pédagogique de départ.

### 11.5 Évaluation humaine

Préparer une écoute en aveugle comprenant Bach, Snarky, DeepBach et hybride,
sans sélection opportuniste. Séparer les questions :

- correction contrapuntique ;
- naturel des lignes individuelles ;
- cohérence harmonique ;
- qualité cadentielle ;
- ressemblance avec le style visé ;
- préférence globale.

Les évaluateurs peuvent ensuite consulter l'explication Snarky dans une phase
distincte ; l'explication ne doit pas influencer l'écoute aveugle.

### 11.6 Coût et explicabilité

- temps de génération ;
- nœuds de recherche et retours arrière ;
- mémoire ;
- taille de la trace ;
- proportion des décisions associées à une provenance lisible ;
- temps nécessaire pour diagnostiquer et corriger un cas.

### 11.7 Expérience comparative principale

L'évaluation sépare trois questions qui ne doivent pas être confondues.

**Pouvoir descriptif.** Sur chaque décision tenue à part, mesurer le rang ou la
probabilité du choix authentique de Bach sous `S-HISTORICAL`, `S-LEARNED`,
`S-HYBRID` et `D0-modern`. Les différences
`S-HYBRID - S-HISTORICAL` et `S-LEARNED - politique neutre` mesurent
respectivement l'information ajoutée aux traités et l'information portée par la
base apprise seule.

**Pouvoir génératif.** Pour chaque soprano de test, générer un nombre fixé de
réalisations avec les mêmes informations disponibles :

- `BACH-REFERENCE` : réalisation authentique ;
- `S-HISTORICAL` ;
- `S-LEARNED` ;
- `S-HYBRID` ;
- `D0-modern` ;
- éventuellement `H0`.

Les sorties sont évaluées sans présélection par conformité, statistiques de
style, diversité, nouveauté, satisfaisabilité et écoute en aveugle.

**Valeur théorique.** Pour chaque règle apprise, mesurer son gain conditionnel
à la baseline historique, sa perte par ablation, son coût descriptif, la
stabilité de ses exceptions et sa relation aux sources. C'est cette troisième
analyse, et non une préférence d'écoute isolée, qui permet de conclure qu'une
formulation empirique rend mieux compte de Bach qu'un énoncé de traité.

Le checkpoint `D0-legacy`, entraîné historiquement sur un corpus augmenté qui
peut contenir les pièces d'évaluation, reste un audit exploratoire. Une
comparaison confirmatoire exige `D0-modern` réentraîné sur exactement les mêmes
pièces `train`, sans transposition ni variante issue de `validation` ou
`test`.

## 12. Lots de travail

### Lot 0 — protocole figé

- [ ] Définir précisément la première tâche d'harmonisation.
- [ ] Fixer corpus, filtres, licence et identifiants.
- [x] Publier un partage train/validation/test groupé par variantes exactes de
      soprano, sans promouvoir d'ancienne donnée exposée dans le test.
- [x] Archiver la source DeepBach, ses branches, ses poids et son cache avec
      leurs empreintes.
- [ ] Choisir la reproduction DeepBach et figer son environnement.
- [ ] Préenregistrer métriques principales et règles d'exclusion.

**Critère de sortie :** une expérience peut être rejouée à partir d'un
manifeste sans décision manuelle non enregistrée.

### Lot 1 — représentation canonique

- [ ] Importer les chorals sans perdre orthographe, durées et fermatas.
- [ ] Construire les événements et continuations SATB.
- [ ] Normaliser relativement à la tonalité locale.
- [ ] Exporter les mêmes entrées vers Snarky et DeepBach.
- [ ] Ajouter des tests de conservation aller-retour.

**Critère de sortie :** notes, voix, durées, attaques et métadonnées sont
identiques après import et export sur tout le corpus accepté.

### Lot 2 — registre de features

- [ ] Inventorier les faits déjà produits par l'harmoniseur.
- [x] Définir les premiers identifiants tonals globaux et leur provenance.
- [ ] Ajouter les features tonales, phraséologiques et contrapuntiques
      prioritaires.
- [x] Fournir les premiers tests positifs et négatifs des statuts tonals.

**Critère de sortie :** tout prédicat utilisé par une règle apprise possède une
fiche testée.

### Lot 3 — mineur de règles

- [ ] Définir le langage de patrons borné.
- [ ] Énumérer les candidats sans consulter le test.
- [ ] Calculer support, confirmation, gain et stabilité.
- [ ] Préenregistrer plusieurs budgets de faits, règles et conditions.
- [ ] Tracer la frontière qualité–complexité et sélectionner son coude.
- [ ] Comparer plusieurs vocabulaires de faits avec les mêmes règles locales.
- [ ] Mesurer ablations, redondances et interactions résiduelles.
- [x] Mesurer une première ablation conjointe à poids fixes : les sept règles
      ont une pénalité positive et le gain authentique vaut 10,8 fois celui du
      contrôle permuté.
- [x] Réajuster les autres poids après ablation des groupes mélodie, overlap,
      parallèles et direct ; tous gardent une pénalité positive sur validation.
- [ ] Vérifier qu'aucune règle ne dépend de l'ordre ni d'une autre règle.
- [x] Exporter les deux premières `RuleCard` de mouvement direct avec
      provenance, bootstrap et équivalence Snarky.
- [x] Exporter aussi les `RuleCard` du triton mélodique et de l'overlap avec
      provenance, contrôle nul, bootstrap et équivalence Snarky.
- [x] Exporter les deux `RuleCard` de parallèles généralisées aux six paires
      de voix.
- [x] Exporter une `RuleCard` candidate pour la première obligation tonale et
      ses raffinements contextuels.
- [ ] Généraliser automatiquement l'export de `RuleCard` à toute famille
      retenue.

**Critère de sortie :** une campagne déterministe produit la même frontière et
le même catalogue à partir du même manifeste et de la même configuration ;
chaque règle est locale et indépendante, et chaque fait qu'elle consulte
possède une définition musicale testée.

### Lot 3a — redécouverte aveugle de règles connues

- [x] Masquer les règles de référence et leurs verdicts pendant le premier POC.
- [x] Exposer uniquement les faits primitifs, jamais un prédicat qui encode
      déjà la règle cible.
- [x] Tenter d'abord les règles mélodiques, parallèles et mouvements directs
      entre soprano et basse.
- [x] Retrouver sur `validation` les patrons numériques correspondant aux
      octaves/unissons et quintes parallèles.
- [x] Exécuter un contrôle nul par mélange des choix à l'intérieur des pièces.
- [x] Auditer les variantes exactes : dix groupes dupliqués, six traversées
      supprimées, partage canonique `251/50/51`.
- [x] Mesurer la stabilité des mouvements directs par 1 000 bootstraps de
      chorals entiers sur train et validation.
- [x] Étendre l'expérience aux quatre voix et au chevauchement adjacent.
- [x] Récupérer la classe mélodique `6` et le seuil d'overlap `0` avec un
      budget d'une règle par famille et un contraste local de forme.
- [x] Récupérer les classes parallèles `0` et `7` dans les six paires de voix,
      avec zéro sélection dans le contrôle permuté.
- [x] Isoler le mouvement direct des coûts généraux du saut et du mouvement
      semblable par génération de colonnes résiduelle.
- [x] Ajouter les faits de tonique, mode et classe chromatique relative, puis
      retrouver la tendance ascendante de la classe `11`.
- [x] Utiliser les exceptions pour séparer par mode un proxy de résolution
      trompeuse `V→VI`.
- [x] Calibrer les 864 raffinements tonals sur les maxima de 49 permutations
      indépendantes ; une clause survit à `p FWER = 0,02`.
- [x] Auditer indépendamment le contenu harmonique de cette clause : le noyau
      `vii°6→I6` est sans exception observée mais seulement partiellement
      équivalent au proxy numérique.
- [x] Comparer par ablation le proxy numérique et sa spécialisation harmonique
      exacte ; le proxy conserve le gain propre le plus robuste et les deux
      colonnes forment une hiérarchie plutôt que deux règles indépendantes.
- [x] Ajouter un premier vocabulaire candidat-dépendant de noyaux harmoniques,
      auditer les 13 cas atypiques et compresser la hiérarchie en un statut
      ordinal à un poids.
- [x] Geler le modèle, les hyperparamètres et les critères confirmatoires avant
      toute ouverture des 51 chorals de test.
- [x] Ouvrir le test une seule fois : les trois critères sont satisfaits et le
      statut gradué conserve 99,964 % du gain des deux poids.
- [x] Compiler le statut local en Snarky et vérifier ses 256 états abstraits
      sans désaccord.
- [x] Auditer deux générations DeepBach puis sonder conditionnellement les 12
      contextes du test ; documenter le support nul des générations libres et
      les deux exceptions où DeepBach préfère la norme au choix de Bach.
- [ ] Ajouter ensuite les faits harmoniques nécessaires aux autres résolutions
      et aux doublures.
- [x] Comparer sémantiquement les clauses de mouvement direct aux oracles
      Snarky sur un domaine local fini : zéro désaccord sur 301 401 états
      valides par classe.
- [x] Comparer le triton et l'overlap aux oracles Snarky : zéro désaccord sur
      1 993 et 534 050 états locaux.
- [x] Comparer les parallèles aux oracles Snarky : zéro désaccord sur
      1 130 364 états locaux par classe.
- [ ] Classer chaque cible comme équivalente, raffinée, plus faible,
      contredite, non identifiable ou non retrouvée.
- [ ] Ne lancer la recherche de règles inédites qu'après publication de ce
      résultat.

**Critère de sortie :** au moins quatre des six familles sans analyse
harmonique sont retrouvées sur `validation`, dont une règle mélodique et une
règle entre voix, sans fait composite révélant la réponse.

### Lot 3b — reconstruction de la baseline CHORAL

- [x] Couvrir les 78 pages de l'appendice B et conserver les unités dans leur
      ordre documentaire sans forcer le décompte historique de 354.
- [x] Produire 1 293 unités sources, 775 cartes et 7 tables avec provenance.
- [x] Vérifier visuellement toutes les pages et valider la structure.
- [ ] Revoir manuellement les 389 unités contenant encore une incertitude OCR.
- [x] Classer productions, contraintes et heuristiques par vue.
- [x] Évaluer automatiquement leur représentabilité avec les features Snarky.
- [ ] Relire musicalement les cartes à faible confiance avant import.
- [ ] Relier chaque entrée à une règle experte, apprise ou encore absente.
- [ ] Tester les règles sur le corpus au lieu de conserver automatiquement leur
      statut absolu historique.

**Critère de sortie :** chaque règle CHORAL importée possède une référence de
page, une formulation vérifiée, un type historique, une traduction formelle ou
un motif de report, et des statistiques sur corpus.

### Lot 3c — induction résiduelle au-delà des traités

- [ ] Figer un manifeste des règles de traités, CHORAL et Snarky servant de
      baseline de connaissance connue.
- [ ] Calculer les résidus décisionnels de cette baseline sur `train`.
- [ ] Chercher des clauses courtes conditionnellement aux règles déjà connues.
- [ ] Comparer chaque candidate à sa règle historique par ablation et paires
      minimales.
- [ ] Classer les candidates en `REDISCOVERY`, `REFINEMENT`,
      `NEW_REGULARITY`, `CONTRADICTION` ou `UNRESOLVED`.
- [ ] Soumettre les revendications de nouveauté à l'audit des sources et à une
      relecture musicologique.
- [ ] Tester séparément la spécificité bachienne sur un corpus de contraste
      comparable.

**Critère de sortie :** toute règle présentée comme nouvelle apporte un gain
tenu à part au-delà de la baseline connue, reste intelligible sous le budget de
complexité et ne possède pas d'équivalent identifié dans les sources auditées.

### Lot 4 — compilation Snarky

- [ ] Compiler les règles sélectionnées en `R-LEARNED-*`.
- [ ] Créer des manifestes séparés `S-HISTORICAL`, `S-LEARNED` et
      `S-HYBRID`.
- [ ] Garantir par test que charger `S-LEARNED` n'importe aucune règle
      historique et que `S-HISTORICAL` reste inchangée.
- [ ] Définir et mesurer la politique neutre utilisée lorsque la base apprise
      ne classe pas les candidates.
- [ ] Séparer contraintes, violations, préférences et observations.
- [ ] Vérifier chaque règle sur ses exemples et contre-exemples.
- [ ] Conserver les statistiques et la provenance dans les traces.

**Critère de sortie :** chaque règle publiée est exécutable et reliée à sa
fiche empirique ; les trois configurations peuvent être chargées et comparées
sans ambiguïté de provenance.

### Lot 5 — banc DeepBach

- [x] Reproduire une baseline DeepBach historique versionnée.
- [x] Produire une seconde génération canonique et auditer la première règle
      tonale confirmée.
- [x] Comparer les probabilités conditionnelles DeepBach dans les contextes
      Bach sans les utiliser pour réajuster la règle.
- [x] Générer des sorties canoniques à graines fixes.
- [ ] Générer un nombre fixé d'échantillons par entrée du banc commun.
- [ ] Auditer automatiquement toutes les sorties avec Snarky.
- [ ] Produire la taxonomie des désaccords.
- [ ] Construire les premières paires minimales.

**Critère de sortie :** aucune sortie utilisée dans les statistiques n'a été
sélectionnée ou rejetée manuellement sans motif enregistré.

### Lot 6 — raffinement guidé par contre-exemples

- [ ] Trier les cas `MISSING_RULE` et `MISSING_FEATURE`.
- [ ] Appliquer une seule opération de révision explicite par version.
- [ ] Repasser toute règle modifiée par validation, compilation et ablation.
- [ ] Vérifier leur valeur sur le corpus tenu à part.
- [ ] Réviser les règles `OVERSTRICT_RULE`.
- [ ] Mesurer le déplacement du coude qualité–complexité à chaque tour.
- [ ] Arrêter après le nombre préenregistré de tours sans amélioration.
- [ ] Versionner chaque évolution du vocabulaire et du catalogue.

**Critère de sortie :** chaque ajout de fait ou modification de règle est
justifié par des cas différentiels, améliore une mesure définie à l'avance et
ne dépend pas du jeu de test final.

### Lot 7 — hybrides

- [ ] Implémenter audit, rejet et réparation.
- [ ] Tester l'ordre des `CHOICE` par probabilités DeepBach.
- [ ] Mesurer qualité, diversité, coût et garanties.
- [ ] Réaliser les ablations Snarky seul, DeepBach seul et hybride.

**Critère de sortie :** le rôle exact de chaque composant est mesurable et une
explication symbolique ne dépend pas d'un score neuronal opaque.

### Lot 8 — publication musicale

- [ ] Relire les règles avec des musiciens et théoriciens.
- [ ] Comparer chaque famille à sa formulation pédagogique usuelle.
- [ ] Publier séparément redécouvertes, raffinements, contradictions et
      nouvelles régularités.
- [ ] Publier exemples, contre-exemples, partitions et statistiques.
- [ ] Documenter les résultats négatifs et règles instables.
- [ ] Préparer l'étude d'écoute en aveugle.

**Critère de sortie :** le catalogue peut être consulté comme un traité
musical empirique, indépendamment du code, et chaque prétention de précision
supérieure aux traités est reliée à une comparaison tenue à part.

## 13. MVP

Le premier incrément doit rester volontairement limité :

- corpus principal compatible avec l'expérience DeepBach ;
- soprano donné ;
- tonalités majeures et mineures normalisées, sans modulation complexe ;
- patrons verticaux, transitions et contours sur trois positions ;
- 15 à 30 familles de règles candidates ;
- transcription vérifiée d'au moins 20 règles représentatives de CHORAL ;
- comparaison `S-HISTORICAL`, `S-LEARNED`, `S-HYBRID`, `E0` et `D0` ;
- audit automatique des violations ;
- dix paires minimales documentées ;
- au moins une feature nouvelle justifiée par les erreurs de DeepBach ;
- au moins une règle existante assouplie grâce à un contre-exemple de Bach.

Le MVP est réussi s'il produit quelques règles réellement plus précises que
leur équivalent pédagogique, montre une amélioration mesurable avant et au
coude de la frontière qualité–complexité, et quantifie explicitement ce que la
base compacte de règles locales indépendantes n'explique pas. Il n'a pas besoin
de couvrir déjà toute l'écriture de Bach.

## 14. Risques

### Analyse harmonique circulaire

Une règle ne doit pas sembler vraie uniquement parce que l'algorithme
d'annotation applique déjà cette règle. Conserver la provenance des analyses,
tester plusieurs analyses plausibles et distinguer annotations humaines et
inférées.

### Surapprentissage symbolique

Limiter la longueur des patrons, partager par pièce, tester la stabilité et
interdire les identifiants ou hauteurs absolues non justifiées.

### Confusion entre rareté et faute

Une faible fréquence produit une préférence ou une observation, pas
automatiquement une interdiction.

### Features opaques

Une feature apprise par un réseau mais sans interprétation musicale ne peut
pas servir directement dans le catalogue humain. Elle peut seulement signaler
une zone à étudier.

### Biais de sélection

Fixer le nombre d'échantillons, conserver toutes les sorties et publier les
critères d'exclusion avant l'expérience.

### Vieillissement de DeepBach

Séparer la reproduction historique du modèle et son adaptation technique. Une
réécriture moderne doit être validée contre des sorties ou métriques de
référence avant de porter le nom de baseline DeepBach.

## 15. Décisions ouvertes

- Corpus exact et politique de correction des erreurs.
- Usage d'annotations harmoniques existantes ou analyse indépendante.
- Unité temporelle commune et traitement des ornements.
- Définition opérationnelle de la tonalité locale.
- Seuils séparant `MUST`, `NORMALLY`, `PREFER` et `OBSERVED`.
- Objectif MDL et budget maximal de complexité.
- Format final des partitions et exemples interactifs.
- Population et protocole de l'étude humaine.
- Modalité d'intégration des probabilités DeepBach dans les `CHOICE`.

## 16. Première séquence d'exécution

1. Figer le corpus et le partage par pièce.
2. Construire la représentation canonique et ses tests.
3. Inventorier les features actuelles de l'harmoniseur.
4. Sélectionner et vérifier vingt règles représentatives de CHORAL.
5. Formaliser dix règles pédagogiques comme règles parentes.
6. Relier traités, CHORAL, Snarky expert et formulations induites.
7. Chercher leurs raffinements contextuels sur le train.
8. Valider leur stabilité sur la validation.
9. Reproduire DeepBach sur la même tâche.
10. Auditer toutes ses sorties avec le catalogue gelé.
11. Extraire dix paires minimales et classifier les manques.
12. Ajouter une première feature justifiée empiriquement.
13. Réinduire les règles et mesurer le gain.
14. Geler le protocole final avant ouverture du test.
