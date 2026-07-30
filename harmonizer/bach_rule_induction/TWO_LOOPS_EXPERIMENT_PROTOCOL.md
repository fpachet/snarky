# Protocole des deux boucles : induction puis génération

## 1. But et séparation stricte

Le projet comporte deux boucles qui communiquent par une base de connaissance
gelée et versionnée :

1. la **boucle d'induction** découvre une théorie lisible à partir du corpus ;
2. la **boucle de génération** cherche des harmonisations satisfaisant cette
   théorie avec Snarky.

La génération ne modifie jamais les features, règles, contraintes, poids ou
seuils qu'elle reçoit. Une mauvaise génération devient un contre-exemple pour
une nouvelle itération d'induction ; elle ne provoque pas un ajustement
opportuniste du générateur courant.

```text
corpus Bach
    │
    ▼
boucle 1 : induction, MLE, calibration, validation
    │
    ▼
base gelée Tn
    │
    ▼
boucle 2 : propagation, choix, score, backtracking
    │
    ├── solutions satisfaisantes
    └── résidus et échecs ─────► prochaine induction Tn+1
```

## 2. Contrat produit par la boucle d'induction

Une théorie `Tn` est valide seulement si elle contient les éléments suivants :

| Élément | Contenu |
|---|---|
| Vocabulaire | faits observables et statuts musicaux définis |
| Features | prédicats locaux K3 avec portée et complexité |
| Règles | déductions de statuts, sans effet probabiliste |
| Contraintes | interdictions et obligations persistantes |
| Facteurs | conditions d'activation pures et lisibles |
| Poids | paramètres appris conjointement par MLE conditionnel |
| Score | formule normalisée identique en apprentissage et génération |
| Seuils | planchers globaux et, si retenus, par groupe |
| Agrégats | éventuelles bandes de proportions apprises |
| Compilations | programmes Snarky `.rules`, `.constraints`, `.factors` |
| Provenance | corpus, split, code, paramètres et résultats de validation |

Les règles historiques expertes restent dans une autre base. Pour la base
apprise, l'expert définit la grammaire des prédicats admissibles et les
critères statistiques ; le corpus détermine les instances retenues, leur
statut et les poids.

## 3. Boucle 1 — identifier la théorie

### 3.1 Préenregistrement

Avant de consulter les résultats de l'itération, un manifeste doit fixer :

- corpus et partitions par pièce ;
- localité, actuellement trois blocs verticaux consécutifs `K3` ;
- domaine des alternatives pour chaque voix ;
- grammaire des features, opérateurs et statuts disponibles ;
- nombre maximal de clauses et budget de complexité ;
- couverture minimale par prédicat ;
- critère d'admission d'une interdiction ou obligation dure ;
- régularisation et méthode de sélection des facteurs ;
- politique de calibration du seuil de score ;
- groupes de facteurs et éventuels seuils par groupe ;
- métriques de validation et règle d'arrêt.

Changer l'un de ces éléments crée une nouvelle expérience identifiée.

### 3.2 Construire les décisions et alternatives

Pour chaque choix authentique de Bach :

1. conserver le contexte observable : soprano, rythme, métrique, tonalité,
   voix voisines et conditions aux limites ;
2. produire toutes les alternatives locales appartenant au domaine gelé ;
3. propager les tenues et les contraintes structurelles ;
4. calculer les mêmes features sur le choix authentique et les alternatives.

Le choix authentique doit rester dans son domaine. Toute exclusion est une
erreur de représentation à corriger avant l'apprentissage.

### 3.3 Générer et sélectionner les prédicats

La grammaire peut construire :

- des prédicats simples ;
- des conjonctions bornées ;
- des implications `contexte => conséquence` ;
- des partitions mutuellement exclusives de statuts ;
- des relations entre les trois blocs K3.

Chaque prédicat possède un coût descriptif. La recherche optimise une
frontière qualité–complexité et non la vraisemblance seule.

### 3.4 Déterminer le rôle de chaque énoncé

Trois rôles sont possibles :

- **interdiction** : une activation retire la candidate ;
- **obligation** : lorsque l'antécédent est actif, une conséquence doit être
  réalisable ;
- **facteur** : l'activation reste légale et contribue au score.

Une fréquence nulle observée ne suffit pas à créer automatiquement une
contrainte. La promotion dure exige une couverture suffisante, une borne
d'incertitude préenregistrée, une stabilité par pièce et une validation
séparée. À défaut, le prédicat reste un facteur.

La recherche de structure est une boucle externe. Pour chaque structure
candidate, contraintes et vocabulaire sont gelés avant l'estimation des poids.

### 3.5 Apprendre conjointement les poids par MLE

Après retrait des alternatives interdites, tous les poids souples sont appris
simultanément. Pour le choix authentique \(x_i\) parmi \(C_i\) :

\[
P_\theta(x_i\mid C_i)=
\frac{\exp(\theta^\top f(x_i))}
{\sum_{y\in C_i}\exp(\theta^\top f(y))}
\]

La fonction maximisée est la log-pseudo-vraisemblance pénalisée :

\[
\mathcal L(\theta)=
\sum_i\log P_\theta(x_i\mid C_i)-\lambda R(\theta)
\]

Son gradient utilise les activations observées moins leur espérance sous le
softmax courant. Les interactions entre facteurs participent donc bien au
MLE ; aucun poids n'est ajusté indépendamment sur son marginal.

La sélection tient compte de la stabilité des poids, de leur utilité hors
apprentissage et du coût descriptif. Tout facteur retenu est ensuite réajusté
conjointement avec les autres.

### 3.6 Définir le score d'une séquence

Le score de satisfaction n'est pas l'énergie brute, qui dépend de la longueur
et du contexte. Pour une séquence \(x\), on utilise la
log-pseudo-vraisemblance moyenne :

\[
S_\theta(x)=\frac{1}{N_x}
\sum_{i=1}^{N_x}\log P_\theta(x_i\mid C_i)
\]

Les ensembles \(C_i\), les contraintes et la normalisation doivent être
canoniques et identiques dans les deux boucles. Le score ne doit pas dépendre
du chemin de recherche Snarky.

Le score reste explicable par les activations et contributions
\(\theta_k f_k\). Un rapport sépare au minimum :

- conduite mélodique ;
- sonorité verticale ;
- mouvements conjoints de voix ;
- basse et tonalité ;
- préparation et résolution ;
- attaques, tenues et répétitions.

### 3.7 Apprendre le threshold

Les scores utilisés pour calibrer le seuil doivent être hors apprentissage par
pièce : validation séparée ou prédictions croisées où le choral scoré n'a pas
servi à apprendre ses poids.

Deux politiques sont admises, mais celle choisie doit être préenregistrée :

- **couverture stricte** : \(\tau=\min_x S_\theta(x)\), tous les chorals de
  calibration sont acceptés ;
- **couverture robuste** : \(\tau\) est un quantile inférieur fixé à l'avance.

Des seuils par groupe peuvent compléter le seuil global afin d'empêcher une
bonne mélodie de compenser de mauvais accords. De même, une proportion de
features ne devient une contrainte globale que si sa bande acceptable est
apprise, préenregistrée et validée. Sinon elle reste un diagnostic.

### 3.8 Validation, compilation et gel

Une théorie candidate doit passer :

1. stabilité de la structure et des poids par pièce ;
2. gain prédictif tenu à part ;
3. couverture du score au seuil annoncé ;
4. discrimination de Bach contre alternatives et corruptions contrôlées ;
5. audit des mauvaises générations non détectées ;
6. parité des activations et scores entre l'évaluateur d'apprentissage et
   Snarky ;
7. audit de lisibilité et de complexité.

Le test final reste scellé pendant la découverte et le choix des seuils.

La sortie est immuable : catalogue des features, contraintes, facteurs,
poids MLE, seuils, programmes Snarky, hash des données et rapport de
validation.

### 3.9 Itération et arrêt de la boucle 1

Les faux négatifs — mauvaises solutions acceptées — sont classés par résidu.
Un nouveau groupe de features peut être proposé, puis toute la procédure est
rejouée sans modifier rétroactivement `Tn`.

La boucle s'arrête sur une frontière préenregistrée lorsque aucun groupe de
complexité admissible n'améliore simultanément généralisation, détection des
résidus et parcimonie. Une conclusion négative reste un résultat scientifique.

## 4. Boucle 2 — chercher une solution satisfaisante

### 4.1 Entrées immuables

La génération reçoit :

- une théorie gelée `Tn` ;
- un soprano et un rythme ;
- tonalité, métrique et conditions aux limites ;
- un budget de recherche et un nombre de solutions demandé.

Elle ne consulte ni les voix cachées de Bach, ni les données de validation.

### 4.2 Initialisation et propagation

Snarky crée les variables et domaines, ajoute les faits observables, déduit
les statuts puis atteint un point fixe avec les contraintes persistantes.

Une interdiction, une obligation impossible, un domaine vide ou une
incohérence structurelle produit immédiatement `CONTRADICTION`.

### 4.3 Choix

Si plusieurs valeurs restent possibles, `CHOICE` les ordonne avec les facteurs
et poids MLE gelés. Un checkpoint réversible est créé avant la décision.

Le poids influence l'ordre d'exploration ; il ne transforme pas à lui seul une
candidate faible en contradiction.

### 4.4 Propagation du score minimal

Pour chaque fenêtre entièrement déterminée, la contribution normalisée au
score devient fixe. Pour les fenêtres non résolues, le moteur calcule une
borne optimiste du meilleur score encore atteignable.

Si :

\[
S_{\mathrm{fixé}}+U_{\mathrm{futur}}<N\tau
\]

alors aucune continuation ne peut satisfaire le seuil. Une contrainte
persistante de score ajoute `CONTRADICTION`, et Snarky restaure le dernier
checkpoint. La même opération s'applique aux seuils de groupes et aux bandes
d'agrégats gelées.

Ce mécanisme n'est pas une optimisation branch-and-bound : il ne compare pas
la branche à la meilleure solution connue. Il vérifie seulement si le niveau
minimal appris reste atteignable.

### 4.5 Acceptation ou backtracking

Une solution complète est acceptée uniquement si :

- toutes les contraintes dures sont satisfaites ;
- toutes les obligations sont satisfaites ;
- le score global est supérieur ou égal à \(\tau\) ;
- les éventuels seuils de groupes sont satisfaits ;
- les éventuelles bandes globales préenregistrées sont respectées.

Sinon la solution devient une contradiction explicable et déclenche un
backtrack. La trace doit préciser la règle, la contrainte, le groupe de score
ou l'agrégat responsable.

### 4.6 Terminaison et sorties

La boucle termine dans l'un des états :

- nombre demandé de solutions satisfaisantes atteint ;
- espace de recherche épuisé : aucune solution ne satisfait `Tn` ;
- budget de recherche atteint : résultat indéterminé.

Chaque solution contient la partition, ses activations, ses scores global et
par groupe, ses agrégats et la trace des choix. Chaque échec conserve les
causes de contradiction et le nombre de backtracks.

Les étrangetés musicales acceptées alimentent l'audit résiduel de la prochaine
boucle 1. Aucun poids ou seuil n'est changé pendant la boucle 2.

## 5. Tests obligatoires de l'interface entre les boucles

Une théorie ne peut être utilisée pour générer sans les tests suivants :

1. parité feature par feature entre Python et Snarky ;
2. parité de chaque contribution \(\theta_k f_k\) ;
3. parité des normalisations locales et du score de séquence ;
4. parité des seuils globaux et par groupe ;
5. exemple de contradiction dure suivi d'un backtrack ;
6. exemple de score maximal restant sous le seuil suivi d'un backtrack ;
7. exemple accepté au-dessus de tous les seuils ;
8. preuve que le résultat est indépendant de l'ordre des règles ;
9. reproductibilité de la trace avec la même politique et la même graine.

## 6. État de complétude

Les deux boucles sont désormais **complètes comme architecture et contrat
expérimental** : leurs responsabilités, données, formules, sorties, causes de
backtracking et critères de terminaison sont définis.

Elles ne sont pas encore **complètement instanciées ni implémentées**. Avant la
prochaine expérience, il reste à geler dans un manifeste machine-readable :

1. la grammaire exhaustive des features et son budget de complexité ;
2. les critères numériques de promotion en contrainte ou obligation ;
3. la régularisation et la règle de sélection MLE ;
4. la politique exacte du seuil : strict ou quantile fixé ;
5. la liste définitive des groupes soumis à un seuil ;
6. le statut des pourcentages : diagnostics ou bandes contraignantes ;
7. le domaine génératif complet, au-delà du POC `top-pitches` ;
8. les budgets et la politique de parcours Snarky.

Il manque également l'implémentation de la contrainte persistante de score et
sa borne optimiste. Les artefacts V22/V24 actuels valident une partie de la
compilation, mais ne constituent pas encore une instance complète de ce
protocole.
