# Protocole V4 — base apprise autonome et induction générative

## Statut

Le cycle V1–V3.9 est clos. Il a démontré la redécouverte de règles connues,
confirmé une première préférence tonale graduée et ouvert une seule fois les
51 chorals de test pour cette hypothèse gelée.

V4 ouvre une phase **exploratoire distincte**. Les résultats du test V3.8 ne
servent plus à modifier les features, poids ou règles. Une confirmation globale
de la grammaire V4 exigera une validation imbriquée de la procédure complète ou
un corpus indépendant.

## Objectif du premier jalon

Produire un fragment SATB avec :

- le soprano et la tonalité globale donnés ;
- une politique initiale neutre ;
- uniquement des règles `R-LEARNED-*` ;
- aucune règle historique chargée ;
- une trace de chaque contribution apprise.

Ce jalon vérifie l'architecture. Il ne prétend pas encore rivaliser avec Bach,
la base historique ou DeepBach.

## Profils

- `S-HISTORICAL` : base humaine inchangée ;
- `S-LEARNED` : sept règles induites, compilées indépendamment ;
- `S-HYBRID` : union déclarative pour les futures ablations.

Les manifestes résident dans [`rule_bases/`](rule_bases/). Le chargeur rejette
tout identifiant ne commençant pas par `R-LEARNED-` dans `S-LEARNED` et vérifie
que chaque règle apprise possède exactement un poids déclaré.

## Frontière infrastructure–connaissance

Le smoke test V4.1 utilise seulement :

- quatre voix nommées ;
- quatre positions successives ;
- un soprano fixé ;
- une tonalité globale déclarée ;
- quatre hauteurs fréquentes par voix inférieure, estimées sur `train` ;
- des opérations numériques et une politique de choix neutre.

Il n'utilise ni vocabulaire d'accords, ni progression autorisée, ni cadence,
ni filtre de voicing, ni règle historique. Les petits domaines de hauteurs sont
un échafaudage computationnel exploratoire, publié dans
[`rule_bases/learned/scaffolding.yaml`](rule_bases/learned/scaffolding.yaml).

## Projection des poids

Les règles V2 avaient été ajustées comme contributions à une décision de note,
les autres voix étant observées. La génération V4 choisit une tranche SATB
complète. Pour le premier diagnostic seulement :

- les mouvements directs utilisent le poids soprano V2.4 ;
- mélodie, overlap et parallèles utilisent la moyenne des quatre poids de voix
  V2.4 ;
- la règle de sensible conserve son poids gelé V3.8 multiplié par la force
  `1` ou `2`.

Cette projection est enregistrée dans le manifeste. Elle n'est pas présentée
comme un nouvel ajustement statistique. Une future expérience apprendra
directement des potentiels sur des décisions SATB conjointes.

## Données V4

- `train` : induction, invention de features et diagnostic des générations ;
- `validation` : sélection des versions et du coude qualité–complexité ;
- ancien `test` : aucune nouvelle décision adaptative ;
- confirmation finale : validation imbriquée ou corpus externe préenregistré.

Les générations qui motivent une nouvelle feature proviennent exclusivement de
fragments `train`. Toutes les graines et toutes les sorties sont conservées.

## Boucle

```text
S-LEARNED gelé
→ générations diagnostiques sur train
→ taxonomie exhaustive des défauts
→ choix préenregistré d'une famille
→ induction et contrôle nul
→ sélection sur validation
→ compilation Snarky autonome
→ ablation et nouvelle campagne
```

Ordre initial des familles :

1. ordre, croisement, tessitures et espacement ;
2. sonorités verticales et doublures ;
3. mouvements mélodiques ;
4. relations entre voix ;
5. progressions et renversements ;
6. cadences ;
7. ornements et dissonances.

## Critères de passage du jalon V4.1

- les trois manifestes sont chargeables ;
- `S-LEARNED` n'hérite d'aucun fichier historique ;
- les six règles de niveau A et la règle tonale sont détectées par leurs
  compilations autonomes ;
- plusieurs graines produisent des solutions reproductibles ;
- chaque contribution sélectionnée est traçable ;
- les défauts sont publiés sans correction manuelle.

## Résultats exploratoires V4.1–V4.2

V4.1 a produit dix fragments MusicXML à partir de cinq soprani `train` et deux
graines. Sur 40 tranches, le diagnostic compte trois croisements, sept unissons
adjacents, deux espacements supérieurs à l'octave dans les voix supérieures et
sept sonorités de moins de trois classes.

V4.2 a donc ouvert la première famille préenregistrée. Le scan de cinq seuils
numériques sélectionne le croisement strict `-1` :

- poids conditionnel : `-1,538768` ;
- gain NLL validation : `0,017207` ;
- `z` validation : `-18,364` ;
- contraste local validation : `-0,495`.

Le contrôle mélangé retient aussi `-1`, mais avec un poids `-0,086940`, un gain
NLL `0,001174` et un contraste `-0,060`. La carte
[`R-LEARNED-ORDER-001`](rules/R-LEARNED-ORDER-001.yaml) reste donc
`CANDIDATE` jusqu'à une calibration familiale supplémentaire ; elle n'est pas
encore ajoutée à `S-LEARNED`.

## Critère d'arrêt de la phase d'induction

La grammaire est gelée lorsque plusieurs cycles préenregistrés ne déplacent
plus le coude qualité–complexité, qu'aucune règle courte n'apporte de gain
stable sur `validation`, que les ablations confirment chaque contribution et
que les principaux résidus sont classés. L'ouverture confirmatoire ne déclenche
aucune révision silencieuse.
