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

La formalisation probabiliste proposée après V5.16 est décrite dans
[`MAXENT_RULE_FACTOR_MODEL.md`](MAXENT_RULE_FACTOR_MODEL.md). Elle sépare les
moments observés, la structure des facteurs, leurs paramètres appris et
l'inférence par `CHOICE` ou Gibbs. Snarky possède maintenant une construction
`FACTOR` sans action, distincte de `RULE` et `CONSTRAINT`.

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
apprendre des licences positives et tester de nouveaux faits explicites.

### 1.0.4 Audit résiduel V5.10

- [x] rééchantillonner de nouvelles chaînes V5.9 sur les 16 pièces train ;
- [x] auditer les 46 statuts de mouvement et métrique non sélectionnés ;
- [x] ajouter 22 interactions rares × empreinte verticale relative à la basse ;
- [x] constater qu'aucune licence positive ne dépasse à la fois `+0,5` point
      et `z=2` ;
- [x] explorer une origine transposable latente sur les trois blocs ;
- [x] constater que son gain statistique ne lui confère pas une signification
      de tonalité locale intelligible ;
- [x] mettre V5.11 en quarantaine et revenir aux faits K3 observables.

La meilleure licence simple est la broderie rare d'alto en majeur
(`+0,409` point, `z=1,80`). La meilleure interaction verticale est l'ensemble
`{0,3,6,9}` relatif à la basse avec une classe rare d'alto en majeur
(`+0,335` point, `z=1,82`). Ces signaux sont plausibles mais insuffisamment
stables. Leur échec ne justifie pas d'interpréter automatiquement une variable
latente comme une région tonale.

### 1.0.5 Origine transposable latente V5.11 — quarantaine

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

Les douze états ont été créés par le modèle comme douze origines de
transposition d'un même profil. Le corpus choisit et ajuste ces origines, mais
ne leur donne aucune signification de tonique, fondamentale ou région tonale.
La reclassification de notes rares est en partie mécanique. V5.11 reste une
expérience statistique séparée et **n'entre ni dans le générateur ni dans le
langage de règles appris**.

### 1.0.6 Basse et sonorités explicites V5.12–V5.16

- [x] mesurer directement demi-tons, répétitions et grands sauts de basse ;
- [x] mesurer sonorités triadiques, dissonances fortes/faibles et transitions ;
- [x] montrer que V5.9 surproduit les demi-tons de basse sur BWV 108.6 ;
- [x] rejeter V5.12, qui apprend trop d'interdictions et surproduit les triades ;
- [x] découvrir que l'énergie conjointe comptait une sonorité une fois par voix
      attaquante ;
- [x] compter depuis V5.14 chaque potentiel de sonorité une seule fois par bloc ;
- [x] réinduire interdictions et licences avec cette sémantique corrigée ;
- [x] isoler une calibration de basse V5.15 et constater sa surcorrection ;
- [x] choisir l'interpolation V5.16 sur dix chorals de développement ;
- [x] confirmer V5.16 sur les dix chorals suivants, test scellé fermé.

Sur la confirmation, les demi-tons de basse valent `26,32 %` contre `25,73 %`
chez Bach, les grands sauts `24,35 %` contre `28,03 %`, les blocs triadiques
`56,08 %` contre `53,86 %` et les blocs forts non triadiques `27,52 %` contre
`28,20 %`. Tous ces écarts appariés ont un IC95 recouvrant zéro. La sonorité
`{0,3,6,8}` sur bloc faible reste surproduite de `+2,57` points et constitue
la prochaine lacune explicite. V5.16 est un candidat expérimental confirmé,
pas une base scientifique finale ; elle est désormais compilée comme référence
Snarky gelée.

La réplication avec trois graines ramène les demi-tons à `25,86 %`, les grands
sauts à `24,94 %` et `{0,3,6,8}` faible à `4,24 %`. Aucun des dix écarts
appariés audités n'exclut alors zéro à 95 %. V5.16 est gelée sans pénalité
résiduelle supplémentaire et conservée comme référence d'ingénierie dans
`F-K3-V5.16-REFERENCE`.

L'export factoriel est maintenant matérialisé dans
[`rule_bases/k3_clean/v5_16_factors.yaml`](rule_bases/k3_clean/v5_16_factors.yaml).
Les `44` termes de poids sont fusionnés en `41` facteurs canoniques ; trois
corrections additives V5.16 sont réintégrées dans le poids de leur feature
d'origine. Chaque facteur déclare sa portée et son instanciation
`once_per_target_voice_attack`, `once_per_attack_decision`,
`once_per_vertical_block` ou `once_per_k3_transition`. Cet artefact reste un
catalogue probabiliste : la compilation fidèle de ses prédicats dans le DSL
Snarky est maintenant réalisée dans une syntaxe `.factors` sans effet de bord.

Le
[pont probabiliste vers `CHOICE`](experiments/v5_k3_clean/results/V5_16_SNARKY_CHOICE_BRIDGE.md)
reproduit désormais les conditionnelles du modèle source à la précision
flottante, sans réapprentissage. Les 41 facteurs ont aussi été migrés vers le
DSL pur `.factors` et servent d'oracle de parité pour la nouvelle architecture.

### 1.0.7 Base factorielle V6 induite depuis zéro

- [x] introduire `FACTOR_GROUP`, `FACTOR`, `SCOPE`, `LOG_WEIGHT` et `WHEN`
      dans Snarky ;
- [x] interdire syntaxiquement toute action dans un facteur ;
- [x] séparer `FactorDefinition` et `FactorParameter` ;
- [x] garantir que les activations ne deviennent jamais des faits et ne
      peuvent pas se déclencher entre elles ;
- [x] migrer V5.16 dans `F-K3-V5.16-REFERENCE` avec parité numérique ;
- [x] geler une grammaire V6 de 954 candidats locaux sans noms historiques ;
- [x] apprendre 30 facteurs et leurs poids conditionnels depuis le corpus ;
- [x] calibrer chaque sélection contre le maximum nul de sa famille ;
- [x] geler la structure et réajuster uniquement les poids par le gradient
      génératif `E_Bach[f] - E_Gibbs[f]` ;
- [x] porter ce contraste à 248 chorals de train compatibles et consigner les
      trois exclusions rythmiques ;
- [x] estimer le Jacobien de dix diagnostics par covariance des activations ;
- [x] exécuter une seconde correction locale avec un pas borné à `0,15` ;
- [x] vérifier le checkpoint sur 10 chorals à 30 sweeps et 50 chorals à
      6 sweeps ;
- [x] produire un audit multi-chorals et un MusicXML/MIDI canonique ;
- [x] compiler l'énergie locale candidate et mesurer un gain `×3,21` par
      sweep sur BWV 108.6 avec parité exacte ;
- [x] ajouter les caches de chaînes, l'ESS/dérive des moments du gradient et
      un arrêt adaptatif borné ;
- [x] implémenter un coloriage exact des portées K3 indépendantes et conserver
      le séquentiel comme défaut après un checkpoint de performance négatif ;
- [x] estimer une troisième correction sur trois graines, rejeter l'inversion
      instable, puis construire un petit pas consensus par ridge ;
- [x] rejeter la promotion de ce pas après divergence entre les audits
      génératifs à 6 et 30 sweeps ;
- [x] classer 782 facteurs résiduels sur les états multigraines et retenir 18
      hypothèses dont le signe est stable sur les trois graines ;
- [x] tester six facteurs V7 puis l'ablation/refit des quatre facteurs de
      sonorité, et rejeter les trois candidats après audits génératifs ;
- [x] réapprendre conjointement par pseudo-vraisemblance les 30 facteurs V6
      et les 18 facteurs résiduels, sans poids gelé ;
- [x] obtenir une NLL validation de `0,998314`, contre `1,048935` pour la
      structure V6 conditionnelle ;
- [x] auditer V8 à 6 et 30 sweeps et rejeter sa promotion générative en raison
      d'une basse trop conjointe et trop chromatique ;
- [x] identifier que la première V8 apprenait seulement les activations du K3
      central alors que Gibbs recompte tous les noyaux affectés ;
- [x] construire les mondes contrefactuels exacts attaque/tenue et garantir
      par test la parité de leurs logits avec le sampler ;
- [x] réapprendre les 48 poids sur 251 chorals de train et 50 de validation,
      avec une NLL exacte de `0,829642` ;
- [x] vérifier que le correctif ramène à 30 sweeps les grands sauts de `7,04 %`
      à `21,46 %`, les demi-tons de `42,62 %` à `27,64 %` et la basse hors
      gamme de `15,40 %` à `7,43 %` ;
- [x] ne pas promouvoir ces poids après les audits génératifs, malgré la
      validation du correctif de portée ;
- [x] réinduire exactement la structure depuis les 954 candidats, en
      apprenant conjointement registre, profil tonal et 30 facteurs ;
- [x] obtenir une NLL de validation de `0,779783`, meilleure que les
      `0,829642` de V8 Exact avec 48 facteurs ;
- [x] rejeter V9 comme générateur après les audits à 6 et 30 sweeps :
      secondes soprano-alto positives sans licence contextuelle, dissonances
      fortes et chromaticisme de basse excessifs ;
- [ ] enrichir la grammaire K3 avec des licences lisibles de dissonance
      (métrique, attaque/tenue, préparation, passage/voisin et résolution) ;
- [x] ajouter 96 licences neutres vis-à-vis des classes d'intervalle et
      réinduire V10 depuis zéro ;
- [x] améliorer la NLL à `0,757960` et réduire nettement les dissonances de
      V9, sans résoudre le chromatisme de basse ;
- [x] tester 72 licences tonales rares définies sur train : aucune sélection
      à 30 ni à 45 facteurs, avec réapparition des secondes positives à grand
      budget ;
- [x] vérifier la contrôlabilité des dix diagnostics génératifs avec les 30
      poids V10 : matrice de covariance de rang `10/10` ;
- [x] appliquer deux corrections de poids sous région de confiance et garde de
      pseudo-vraisemblance exacte, dont une agrégation sur trois graines ;
- [x] confirmer à 30 sweeps que V12.2 améliore les dix diagnostics par rapport
      à V12.1, puis sur 50 chorals qu'il améliore sept diagnostics sur dix par
      rapport à V10 ;
- [x] ne pas promouvoir V12.2 : les grands sauts de basse et les sonorités
      fortes non triadiques restent excessifs, tandis qu'Iteration2 demeure
      globalement plus proche de Bach ;
- [x] localiser sur train les résidus V12.2 par paire de voix, force métrique,
      statut de résolution et transition tonale de basse ;
- [x] geler une grammaire V13 de 610 nouveaux candidats neutres et réinduire
      30 facteurs depuis un catalogue exact de 1660 clauses ;
- [x] apprendre spontanément les licences de passage des classes 9 et 10 sur
      temps faible, au lieu des licences générales de V10 ;
- [x] rejeter V13 sur développement : basse et dissonances faibles améliorées,
      mais blocs non triadiques et dissonances fortes aggravés ;
- [x] croiser dans V14 paire, intervalle, métrique et statut de
      préparation/résolution dans un même facteur candidat ;
- [x] répéter la calibration nulle familiale dans les mondes exacts puis
      réinduire structure et poids depuis zéro ;
- [x] montrer par ablation qu'un facteur V14 améliore la NLL exacte
      (`0,749295` contre `0,760977` sans lui) tout en causant davantage de
      dissonances fortes en génération ;
- [x] vérifier que la covariance générative retrouve automatiquement le signe
      correct de la correction et que V15.1 récupère neuf diagnostics sur dix ;
- [x] rejeter V14 et V15.2 après audit, et ne pas promouvoir V15.1 qui demeure
      globalement moins proche de Bach que V13 ;
- [x] implémenter V16 : sélectionner la structure avec un objectif hybride
      de Pareto préservant la
      pseudo-vraisemblance exacte et pénalisant la dérive des moments
      génératifs sur train ;
- [x] estimer l'effet génératif du top-K des colonnes avec une campagne de
      chaînes persistantes multigraine commune, puis n'admettre que les
      facteurs dont le signe est stable sous région de confiance ;
- [x] présélectionner 12 clauses parmi 3676, refuser automatiquement le
      facteur causalement nuisible de V14 et tester deux candidats admis ;
- [x] rejeter les candidats V16 à six balayages après pas local,
      réajustement, dichotomie et audit sur les mêmes 32 pièces de train ;
- [x] confirmer que le rang 5 devient utile à 30 balayages (`0,4370` contre
      `0,5167` pour V13) : la covariance décrit le régime long mais pas le
      sampler transitoire à horizon court ;
- [x] rejeter son refit exact non borné : le poids passe de `+0,15` à
      `+0,5194` et la distance longue remonte à `0,5653` ;
- [x] implémenter V17 avec différences finies appariées du sampler réel aux
      horizons 6 et 30, cache commun V13 et région de confiance bornée par le
      plus grand pas effectivement validé ;
- [x] cribler à six balayages les douze candidats sur huit pièces × deux
      graines : aucun ne combine amélioration de chaque graine et protection
      des grands sauts, blocs forts non triadiques et dissonances fortes ;
- [x] appliquer la dichotomie aux rangs 9 et 12 sans obtenir de candidat
      robuste ;
- [x] effectuer une seconde et dernière itération V17 avec une petite
      correction conjointe du rang 9 et de son résidu de basse, puis arrêter si
      aucun pas ne passe à la fois les horizons 6 et 30 ;
- [x] observer un gain sur 8 pièces × 2 graines, puis le rejeter après
      réplication sur 32 pièces × 3 graines (`0,5422` contre `0,5208` pour
      V13), malgré la réduction des grands sauts ;
- [x] arrêter la boucle de réglage marginal sans ouvrir le test réservé ;
- [x] geler V18 comme retour à l'objectif explicatif : prédicats K3 autonomes,
      aucune activation règle→règle et aucun réglage par métrique générative ;
- [x] exclure du premier catalogue explicatif les bitsets verticaux opaques,
      puis apprendre conjointement les poids de 816 prédicats lisibles par
      pseudo-vraisemblance exacte et `L1` pondéré par la complexité ;
- [x] sélectionner par la règle d'une erreur standard une base de 19 règles
      (complexité 26), ramenant la NLL validation par décision de `2,317000` à
      `0,875539` ;
- [x] vérifier sur quatre replis par pièce que les 19 poids gardent leur signe,
      restent non nuls et réduisent fortement la NLL des chorals retirés ;
- [x] répéter la découverte complète sur quatre partitions 24/8 et retenir un
      noyau unanime de 14 règles, présent dans cinq exécutions sur cinq
      (Jaccard moyen des bases : `0,620`) ;
- [x] réapprendre ces 14 règles sur 251 chorals et valider sur 50 :
      `2,406648 → 0,981894` de NLL, sans ouvrir le test ;
- [x] exporter 14 RuleCards, le catalogue factoriel et le programme Snarky,
      puis établir leur parité à `8,88 × 10⁻¹⁶` près ;
- [x] générer BWV 108.6 à 30 balayages et auditer V18 sur 10 chorals ×
      3 graines sans réinjecter les diagnostics dans l'apprentissage ;
- [x] constater que le noyau explicatif seul n'est pas une grammaire
      générative suffisante : `38,68 %` de blocs triadiques et `53,90 %` de
      blocs forts non triadiques, contre `50,87 %` et `26,91 %` chez Bach ;
- [x] définir V19 sans poids manuel : deux statuts lisibles « triade majeure
      ou mineure complète », séparés selon temps fort ou faible, plus les
      contextes intervalliques métriques de V10 ;
- [x] laisser la pseudo-vraisemblance sélectionner ces deux statuts aux rangs
      2 et 3 avec des poids positifs, plus fort sur temps fort ;
- [x] répéter la découverte complète et retenir un noyau V19 de 18 règles
      unanimes 5/5 (Jaccard moyen `0,735`, contre `0,620` pour V18) ;
- [x] réapprendre V19 sur 251 chorals et valider sur 50 :
      `2,406648 → 0,887879` de NLL, contre `0,981894` pour V18 ;
- [x] exporter 18 RuleCards et le programme Snarky V19, puis vérifier la
      parité à `8,88 × 10⁻¹⁶` près ;
- [x] comparer V18/V19 sur 10 chorals × 3 graines × 30 balayages : V19 ramène
      les blocs triadiques de `38,68 %` à `52,58 %` (Bach `50,87 %`) et les
      blocs forts non triadiques de `53,90 %` à `32,44 %`
      (Bach `26,91 %`) ;
- [x] soumettre l'exemple à l'écoute experte et rejeter V19 comme générateur :
      les métriques de sonorité masquent des notes fonctionnellement mal
      placées, l'absence des accords de septième et une basse sans direction ;
- [x] inventorier V5–V19 et poser une barrière de non-duplication interdisant
      une nouvelle prime triadique, les bitsets opaques et la répétition des
      transitions de basses V13 ;
- [x] auditer sur les 251 chorals de train un vocabulaire déterministe de dix
      qualités : `78,21 %` de blocs reçoivent un accord nommé exact et
      `85,11 %` un accord nommé ou une triade plus une note étrangère ;
- [x] réinduire V20A puis détecter une dépendance linéaire exacte entre le
      facteur général et ses variantes faible/forte, sans sauver le résultat
      par un changement rétrospectif de seuil ;
- [x] corriger uniquement cette identifiabilité dans V20B et obtenir quinze
      règles unanimes 5/5 (Jaccard moyen `0,718`), dont quatre nouveaux statuts
      verticaux positifs : triades majeure/mineure en position fondamentale,
      premier renversement et septième de dominante ;
- [x] constater qu'aucun degré de fondamentale statique n'est sélectionné et
      ne pas générer prématurément avec V20B ;
- [x] vérifier avant V20C que les transitions de fondamentales sont réellement
      distinctes de V13 : `58,33 %` d'arêtes analysables et `67,58 %` de
      transitions différentes de celles des basses ;
- [x] proposer symétriquement les 288 transitions mode × fondamentale
      précédente × fondamentale courante ; n'en voir sélectionner aucune
      parmi 30 colonnes, puis fermer la famille sans quatre réplications ni
      génération identiques à V20B ;
- [x] implémenter V21 : apprentissage simultané d'un `RuleGroup`, proximal de
      groupe et matrice doublement centrée pour retirer les effets marginaux ;
- [x] observer sur le découpage initial un gain collectif absent de V20C :
      `0,820727 → 0,802396`, amélioration appariée
      `0,018331 ± 0,007126`, positive sur 8 chorals sur 10 ;
- [x] ne pas confondre ce résultat exploratoire avec une validation et geler
      `λ=0,03` avant quatre plis disjoints ;
- [x] constater dans quatre plis sur quatre que la matrice réduit la NLL du
      train mais dégrade la validation ; reproduire le diagnostic sans
      pénalité et rejeter la table libre de 288 paramètres ;
- [ ] définir des RuleGroups de faible dimension avec partage réel des
      paramètres, ainsi qu'un protocole séparé de découverte d'invariants
      empiriques candidats à des contraintes ;
- [x] conserver le test réservé fermé.

Le résultat détaillé est dans
[`V6_RESEARCH_LOOP_SUMMARY.md`](factor_bases/k3_v6_induced/V6_RESEARCH_LOOP_SUMMARY.md).
La décision V9 et le diagnostic précis des dissonances non licenciées sont
consignés dans
[`V9_EXACT_REINDUCTION_DECISION.md`](factor_bases/k3_v6_induced/V9_EXACT_REINDUCTION_DECISION.md).
La validation de la correction hybride, son rejet comme nouveau générateur et
les facteurs contextuels à introduire ensuite sont consignés dans
[`V12_EXACT_HYBRID_DECISION.md`](factor_bases/k3_v6_induced/V12_EXACT_HYBRID_DECISION.md).
La localisation train-only des résidus et la décision de ne pas promouvoir la
première grammaire dirigée sont consignées dans
[`V13_DIRECTED_METRIC_DECISION.md`](factor_bases/k3_v6_induced/V13_DIRECTED_METRIC_DECISION.md).
Le paradoxe V14, son ablation causale, la récupération V15 et le protocole
d'admission hybride V16 sont consignés dans
[`V14_V15_HYBRID_STRUCTURE_DECISION.md`](factor_bases/k3_v6_induced/V14_V15_HYBRID_STRUCTURE_DECISION.md).
Le recentrage MaxEnt sur une frontière de règles lisibles et la première base
V18 de 19 règles sont consignés dans
[`V18_EXPLANATORY_DECISION.md`](factor_bases/k3_v6_induced/V18_EXPLANATORY_DECISION.md).
L'ajout V19 du statut triadique lisible, sa stabilité et son effet génératif
hors apprentissage sont consignés dans
[`V19_VERTICAL_STATUS_DECISION.md`](factor_bases/k3_v6_induced/V19_VERTICAL_STATUS_DECISION.md).
V19 reste le dernier checkpoint exécutable, mais son
[`diagnostic après écoute`](factor_bases/k3_v6_induced/V19_LISTENING_DIAGNOSIS.md)
interdit de le promouvoir comme générateur. Il reste incomplet pour la
fonction des accords, les accords de septième et les fonctions chromatiques de
basse.
La
[`décision V20B`](factor_bases/k3_v6_induced/V20B_IDENTIFIABLE_HARMONIC_STATUS_DECISION.md)
valide quatre statuts verticaux plus précis. La
[`décision V20C`](factor_bases/k3_v6_induced/V20C_NAMED_ROOT_TRANSITIONS_DECISION.md)
montre ensuite qu'une table pairwise de fondamentales dans la tonalité globale
n'ajoute aucune règle conditionnellement utile. Cette famille est close.
La
[`décision V21`](factor_bases/k3_v6_induced/V21_GROUPED_LEARNING_DECISION.md)
montre qu'une table apprise conjointement peut révéler un signal sur un
découpage tout en surapprenant systématiquement hors pli. Un RuleGroup
explicable doit donc réduire le nombre effectif de paramètres, et non seulement
regrouper un grand nombre de cellules.

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

### 1.3 Trois couches, puis des configurations explicites

La provenance doit rester visible jusque dans les expériences et les traces.
L'architecture distingue :

- `S-HISTORICAL` : `RULE` et `CONSTRAINT` écrites manuellement, conservées
  intactes ;
- `F-LEARNED` : `FACTOR` purs et paramètres induits depuis le corpus ;
- `S-HYBRID` : chargement explicite des objets experts et appris, sans copie ni
  changement silencieux de leur statut.

Un facteur appris peut utiliser un fait musical conçu par l'humain sans que sa
sélection ou son poids soient manuels. Chaque entrée conserve donc deux
provenances :

- `object_origin` : `HUMAN_SNARKY`, `TREATISE`, `CHORAL`, `INDUCED` ou
  `HYBRID_REVISION` ;
- `feature_origin` : `OBSERVED`, `HUMAN_DEFINED`, `CORPUS_ANNOTATED`,
  `SYMBOLICALLY_INVENTED` ou `LEARNED_OPAQUE`.

Un facteur dont le poids et les conditions sont sélectionnés sur corpus, mais
qui consulte les statuts harmoniques humains `vii°6` et `I6`, appartient bien à
`F-LEARNED`. Il ne constitue toutefois pas une découverte autonome de ces
concepts. Cette nuance doit apparaître dans sa `FactorCard`.

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

### 3.3 Catalogues de règles expertes et de facteurs appris

Chaque facteur découvert doit être publié sous trois formes :

1. une formulation destinée au musicien ;
2. une fiche empirique avec statistiques et exceptions ;
3. une formulation Snarky exécutable avec un identifiant `F-LEARNED-*`.

Le catalogue publie séparément les manifestes de `S-HISTORICAL`, `F-LEARNED`
et `S-HYBRID`. Un facteur appris ne doit jamais être rangé dans le dossier
historique, même lorsqu'il redécouvre exactement une règle humaine. Dans ce
cas, sa `FactorCard` pointe vers la `RuleCard` historique et enregistre
l'équivalence sans dupliquer le code.

### 3.4 Banc d'essai reproductible

Le banc compare au minimum :

- `S-HISTORICAL` : harmoniseur Snarky expert actuel ;
- `F-LEARNED` : solveur avec seulement les facteurs induits et une politique de
  choix par défaut explicitement neutre ;
- `S-HYBRID` : Snarky historique enrichi des facteurs induits ;
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
`F-LEARNED`, nécessairement incomplète dans les premières versions, doit
déclarer sa politique de choix par défaut afin de ne pas attribuer aux facteurs
appris les préférences cachées du solveur.

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
probabilité du choix authentique de Bach sous `S-HISTORICAL`, `F-LEARNED`,
`S-HYBRID` et `D0-modern`. Les différences
`S-HYBRID - S-HISTORICAL` et `F-LEARNED - politique neutre` mesurent
respectivement l'information ajoutée aux traités et l'information portée par la
base apprise seule.

**Pouvoir génératif.** Pour chaque soprano de test, générer un nombre fixé de
réalisations avec les mêmes informations disponibles :

- `BACH-REFERENCE` : réalisation authentique ;
- `S-HISTORICAL` ;
- `F-LEARNED` ;
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

- [x] Figer les 41 facteurs V5.16 et compiler leurs scores en poids positifs
      de `CHOICE`, avec parité exacte contre les 44 termes source fusionnés.
- [x] Introduire le DSL pur `FACTOR` et compiler les catalogues V5.16/V6.
- [x] Créer les manifestes factoriels séparés
      `F-K3-V5.16-REFERENCE` et `F-K3-V6-INDUCED`.
- [x] Garantir par test qu'une activation de facteur ne modifie pas la mémoire
      de travail et ne peut pas en déclencher une autre.
- [ ] Définir un manifeste exécutable hybride chargeant explicitement règles
      expertes, contraintes expertes et facteurs appris.
- [ ] Définir et mesurer la politique neutre utilisée lorsque la base apprise
      ne classe pas les candidates.
- [x] Séparer contraintes, règles à effets, préférences factorielles et
      paramètres probabilistes.
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
- comparaison `S-HISTORICAL`, `F-LEARNED`, `S-HYBRID`, `E0` et `D0` ;
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

## 17. Décision V22 et boucle suivante

V22 établit le protocole courant pour apprendre un groupe sans perdre
l'intelligibilité :

1. proposer une factorisation musicale de faible dimension ;
2. apprendre tous ses paramètres simultanément par pseudo-vraisemblance
   conditionnelle exacte et pénalité de groupe ;
3. geler la pénalité avant quatre folds par pièce ;
4. réapprendre sur 251 chorals et évaluer sur les 50 de validation ;
5. compiler le groupe en `FACTOR` Snarky et vérifier la parité ;
6. découvrir séparément les prédicats sans exception ;
7. les tester comme filtres d'ablation sans les promouvoir automatiquement en
   contraintes `MUST` ;
8. mesurer séparément prédiction conditionnelle et comportement génératif.

Le groupe `mode × mouvement dirigé de fondamentale` est retenu : 24 paramètres
au lieu des 288 de V21, gain positif dans les quatre folds, puis gain apparié
`+0,021475` sur 50 chorals (46/50 améliorés).

L'ablation générative révèle toutefois un résidu précis : trop de blocs forts
non triadiques, trop de dissonances fortes et une basse encore trop chromatique.
La prochaine factorisation candidate doit donc porter conjointement sur :

- statut tonal de la note de basse ;
- force métrique du bloc ;
- qualité/inversion de l'accord uniquement lorsque l'analyse est unique ;
- éventuellement mouvement de basse, avec partage des paramètres par classe
  tonale plutôt qu'une table de hauteurs.

Elle doit être comparée au V22 courant sans modifier les 23 filtres candidats,
afin de ne pas confondre le gain d'un nouveau facteur avec celui d'une
contrainte.

## 18. Décision V23 et résidu suivant

La factorisation V23 a été gelée avant apprentissage en deux groupes :

- `basse tonale sur temps fort × mode`, 24 paramètres centrés par mode ;
- `famille d'accord nommée unique × renversement sur temps fort`, 14
  paramètres utilisant l'absence d'analyse unique comme référence.

Les 38 cellules sont suffisamment testables, mais seule la partie harmonique
se réplique. Sur quatre folds, elle gagne `+0,002724` NLL sur 32 chorals
hors apprentissage, IC 95 % `[+0,000814 ; +0,004597]`. Sur le réapprentissage
251/50, elle gagne `+0,003276`, IC `[+0,001885 ; +0,004723]`, et améliore
38/50 chorals. Le groupe tonal de basse ajouté à l'harmonie ne produit qu'un
gain incrémental `+0,000089`, IC `[-0,000337 ; +0,000522]` ; il n'est pas
retenu.

Le modèle explicatif courant est donc V22 + le groupe harmonique V23, soit
57 facteurs. La parité de sa compilation Snarky est passée. Une ablation
générative contrôlée montre une réduction des dissonances fortes par rapport
à V22, mais l'ajout des 23 filtres empiriques dégrade cette version : les
facteurs probabilistes et les filtres doivent rester séparés.

La boucle suivante ne doit pas réintroduire une table plate de degrés de
basse. Le résidu de chromaticité devra être attaqué par une relation plus
structurée, par exemple :

1. distinguer notes d'accord, notes de passage et appoggiatures à la basse ;
2. représenter une trajectoire tonale locale, plutôt que le seul degré global ;
3. partager les paramètres selon fonction et direction de résolution ;
4. auditer la couverture avant apprentissage ;
5. comparer le nouveau groupe au V23 retenu, avec les filtres désactivés
   pendant l'estimation et évalués seulement dans une ablation séparée.

## 19. Décision V24 et boucle suivante

V24 complète l'état de référence opaque de V23 par huit statuts mutuellement
exclusifs sur les blocs forts : analyse ambiguë, triade incomplète, triade plus
note ambiguë, passage/broderie, retard, appoggiature, note étrangère non
licenciée, autre sonorité non licenciée. Le vocabulaire est défini par
l'analyste, mais ses poids sont appris sans règle experte.

La pseudo-vraisemblance ne réplique pas : le gain moyen des quatre folds vaut
`−0,000353`. Ce résultat ferme l'hypothèse selon laquelle le groupe fournirait
une amélioration conditionnelle stable de V23.

Une calibration générative séparée apprend ensuite les huit poids à partir du
gradient des moments `Bach − générations`, sans consulter la validation. Sur
dix chorals de validation et cinq graines, elle ramène :

- les blocs forts non triadiques de `35,17 %` à `32,02 %`
  (Bach : `26,91 %`) ;
- les dissonances fortes de `0,596` à `0,530`
  (Bach : `0,357`) ;
- le taux triadique de `49,42 %` à `50,17 %`
  (Bach : `50,87 %`).

V24 est donc retenu comme candidat génératif, mais pas comme groupe explicatif
validé par pseudo-vraisemblance. Sa compilation en 65 facteurs Snarky atteint
une parité de `8,882 × 10⁻¹⁶`.

Un Gibbs conjoint exact de deux voix a aussi été implémenté. Comme attendu, il
ne change pas la distribution cible et dégrade les mesures à horizon fini
dans l'ablation ; il est désactivé par défaut.

La prochaine boucle doit garder le vocabulaire V24 gelé et ouvrir deux
groupes distincts, afin de préserver l'interprétabilité :

1. licences de dissonance aux temps faibles, avec préparation et résolution
   dans K3 ;
2. fonction locale de la basse et direction de résolution, sans table plate
   de degrés.

Le protocole, les résultats et l'exemple d'écoute sont consignés dans
[`V24_RESIDUAL_SONORITY_DECISION.md`](factor_bases/k3_v6_induced/V24_RESIDUAL_SONORITY_DECISION.md).

## 20. Décision V25 et transition conjointe V26

V25 ouvre le premier des deux groupes annoncés par V24 : les licences de
sonorité aux temps faibles. Neuf états exclusifs séparent accords ambigus,
triades incomplètes, passages, broderies, suspensions, appoggiatures et deux
formes de résidu non licencié.

Le résultat est scientifiquement négatif mais informatif. Sur dix chorals de
validation et cinq graines, V25 rapproche les dissonances faibles de Bach
(`1,080 → 1,051`, Bach `1,032`), tout en dégradant les dissonances fortes
(`0,510 → 0,552`, Bach `0,357`). Le modèle réduit surtout la catégorie
`other_unlicensed`; il ne produit toujours pas assez de suspensions.

V25 n'est donc pas ajouté à la base Snarky retenue. Il montre que deux
descriptions marginales, même lisibles, ne suffisent pas : il faut représenter
explicitement la relation musicale entre une dissonance faible et sa
résolution.

V26 testera une partition K3 unique, exhaustive et mutuellement exclusive :

`rôle de la sonorité faible × qualité de la résolution forte`.

Les poids de ce groupe seront appris conjointement. Le critère de conservation
est fixé avant l'expérience : amélioration des temps faibles sans dégradation
des temps forts sur validation. L'induction structurée de la basse reste une
boucle indépendante ultérieure.

Le protocole complet et les audits sont consignés dans
[`V25_WEAK_SONORITY_DECISION.md`](factor_bases/k3_v6_induced/V25_WEAK_SONORITY_DECISION.md).

## 21. Recentrage : apprendre la théorie, chercher avec Snarky

Les boucles Gibbs restent utiles pour estimer ou diagnostiquer un modèle
MaxEnt. Elles ne doivent plus être confondues avec le générateur final. Le
pipeline cible est maintenant :

1. proposer automatiquement des prédicats K3 lisibles ;
2. déterminer sur train leur rôle candidat : interdiction, obligation ou
   préférence ;
3. apprendre conjointement les seuls poids des préférences ;
4. valider stabilité, parcimonie et généralisation avant de geler une base ;
5. compiler les interdictions/obligations en contraintes persistantes et les
   préférences en facteurs Snarky ;
6. générer par fermeture de propagation, `CHOICE` et rollback/backtracking ;
7. analyser chaque échec ou étrangeté comme une lacune explicite de la base,
   puis rouvrir l'induction sur train.

Un premier POC exécutable réalise les étapes 5–6 avec les artefacts existants
V22/V24 sur un fragment court. Il n'utilise pas Gibbs pour générer. Les
fenêtres K3 sont reliées par des contraintes de table persistantes et les
scores V24 ordonnent les choix. La parité factorielle Snarky est exacte à la
tolérance numérique.

Ce POC révèle aussi la prochaine question scientifique : dans le domaine
restreint testé, les 23 filtres V22 ne retirent aucune candidate et le MAP
local favorise des répétitions. Il faut donc apprendre des groupes de
contraintes réellement discriminants, notamment la cohérence harmonique
verticale et la trajectoire de basse, au lieu d'ajouter des correctifs manuels
au sampler.

La frontière entre apprentissage, compilation et recherche est détaillée dans
[`SNARKY_RULE_SEARCH_ARCHITECTURE.md`](SNARKY_RULE_SEARCH_ARCHITECTURE.md).

Le protocole exécutable attendu pour les expériences suivantes sépare
désormais deux boucles : induction/MLE/calibration, puis
propagation/score/backtracking. Leur contrat, les formules du score, les
conditions de gel et les tests d'interface sont définis dans
[`TWO_LOOPS_EXPERIMENT_PROTOCOL.md`](TWO_LOOPS_EXPERIMENT_PROTOCOL.md).
