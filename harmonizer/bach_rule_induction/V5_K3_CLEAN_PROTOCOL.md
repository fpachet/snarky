# Protocole V5 — induction clean-room sur noyau K3

## Hypothèse structurelle unique

Toute règle utilisée pour choisir une note doit être exprimable sur :

```text
K3(v,t) = bloc précédent
        + bloc central avec la note (v,t) masquée
        + bloc suivant
        + statuts locaux explicitement déclarés
```

Un bloc vertical contient les quatre hauteurs entendues et quatre indicateurs
attaque/tenue. Les blocs sont les états successifs créés par une attaque dans
au moins une voix. Cette définition évite qu'une tenue répétée soit confondue
avec une nouvelle attaque.

La localité K3 est une hypothèse falsifiable. Aucun rayon supérieur n'est
autorisé dans V5. Si des résidus stables demeurent, une expérience ultérieure
comparera `K1`, `K3` et `K5` sans modifier rétroactivement V5.

## Zéro connaissance harmonique initiale

La base `S-K3-LEARNED` commence sans règle et sans poids V1–V4. Sont autorisés :

- identité et ordre des quatre voix ;
- hauteur MIDI, classe modulo 12, différence, valeur absolue, signe et ordre ;
- positions précédente, centrale et suivante ;
- attaque ou tenue ;
- un domaine commun de hauteurs dérivé du seul `train`.

Les ambitus par voix ne sont pas fournis. Une distribution catégorielle de
registre par voix est estimée sur `train` à partir de poids nuls ; elle fait
partie du modèle publié, mais n'est pas interprétée comme règle harmonique.

## Décisions et alternatives

Pour chaque attaque authentique de la voix `v` au bloc central :

1. conserver les deux blocs voisins de Bach ;
2. masquer la hauteur centrale de `v` ;
3. la remplacer par chaque hauteur du domaine commun ;
4. propager cette hauteur dans le bloc suivant lorsque celui-ci contient une
   tenue de la même note ;
5. comparer le choix de Bach à toutes ces alternatives.

Le partage est effectué par choral avant la création des fenêtres. `train` et
`validation` utilisent le partage groupé de variantes existant. Les 51 chorals
de l'ancien test restent fermés.

## Langage de recherche

Le catalogue est généré mécaniquement à partir d'opérations numériques :

- classe et amplitude du mouvement vers le bloc précédent ou suivant ;
- classe verticale et ordre entre toute paire de voix ;
- conservation d'une classe entre deux blocs ;
- arrivée sur une classe après mouvements de même signe ;
- forme directionnelle sur trois blocs.

Les prédicats invariants par voix et symétriques entre bloc précédent et bloc
suivant sont évalués avant leurs spécialisations. Une spécialisation ne peut
donc entrer que si elle explique un résidu que la loi générale laisse encore.

Les libellés sont numériques et ne contiennent pas les termes « parallèle »,
« direct », « overlap » ou « sensible ». Ces noms ne sont appliqués qu'après le
gel d'un résultat, pendant le benchmark externe.

Chaque colonne est une règle locale indépendante. À chaque itération :

1. calcul des probabilités du modèle courant ;
2. calcul du gradient observé moins attendu de chaque colonne restante ;
3. sélection de la meilleure colonne sous pénalité descriptive ;
4. réajustement conjoint des poids par gradient et pénalité L1 ;
5. mesure sur `validation` et contrôle de stabilité par pièce.

Un gradient négatif propose un évitement ; un gradient positif propose une
préférence. Une règle ne devient dure qu'après une expérience spécifique sur
les opportunités, les exceptions et les intervalles de confiance.

## Génération cohérente

Le générateur V5 est un échantillonneur Gibbs :

```text
partition courante
→ choisir une cellule centrale non fixée
→ construire son K3
→ scorer toutes les hauteurs avec le modèle appris
→ tirer une nouvelle hauteur
→ répéter
```

Le POC initial travaille sur une grille dense de blocs, donc une attaque par
voix et par bloc. Le passage aux rythmes originaux devra propager une hauteur
sur ses blocs de tenue et sommer toutes les énergies locales affectées.

## Barrières scientifiques

- aucune importation des manifestes `S-LEARNED` ou `S-HISTORICAL` ;
- aucune ouverture adaptative de l'ancien test ;
- sélection sur `train`, arrêt et coude sur `validation` ;
- contrôles mélangés et bootstrap groupé avant promotion ;
- comparaison aux règles connues uniquement après gel ;
- publication des règles non récupérées et des résultats négatifs.

## Critères du premier jalon

- extraction déterministe de fenêtres K3 ;
- domaine commun calculé sur `train` seulement ;
- induction depuis une liste de règles vide ;
- poids positifs et négatifs possibles ;
- génération Gibbs utilisant exactement le même évaluateur K3 ;
- artefact machine-readable et rapport humain ;
- test garantissant l'absence de dépendance aux bases antérieures.

## Audit V5.2 de la première règle

Le premier seuil sélectionné n'est pas interprété comme une interdiction des
sauts. Sur validation, le ratio observé/attendu vaut `3,266` pour une taille
maximale de deux demi-tons, puis `0,362` pour trois. Un seuil souple à un
paramètre bat une pénalité linéaire de même complexité de `0,214919` NLL.

La formulation lisible retenue pour la suite est donc :

```text
PREFER mouvement vers chaque bloc voisin ≤ 2 demi-tons
ADD_PENALTY si mouvement > 7 demi-tons
```

Les quatre voix suivent cette direction, mais les exceptions sont plus
fréquentes à la basse. Cette formulation reste pondérée et ne rend aucun saut
illégal.

## Ablation V5.3

Les douze poids V5.1 ont été réajustés conjointement, puis chaque colonne a été
retirée à son tour avant de réapprendre les onze autres. Les douze retraits
augmentent la NLL de validation. La contribution conditionnelle varie de
`+0,012102` à `+0,269848` NLL ; elle ne repose donc pas seulement sur des
colonnes redondantes qui décriraient plusieurs fois le même phénomène.

En particulier, les deux prédicats numériques découverts après gel comme
préservation des classes `0` et `7` avec mouvements de même signe conservent
respectivement `+0,031190` et `+0,034538` NLL après réajustement. Cette
expérience établit leur utilité conditionnelle dans la base fixée, pas encore
leur validité familiale après le processus adaptatif complet.

## Calibration V5.4 de la première colonne

La première sélection a été comparée à 49 permutations des choix authentiques
au sein de chaque pièce et de chaque voix. Pour chaque permutation, le test
retient le plus grand score absolu parmi les 777 prédicats testables du
catalogue de 791 prédicats.

Le signal authentique de `any_voice_adjacent_step_gt(all_voices)=2` vaut
`-284,796`. Le maximum nul médian vaut `56,450` et le plus grand des 49 maxima
nuls vaut `58,465`. Aucun corpus permuté ne rejoint donc le signal authentique ;
le p familial empirique est `1/50 = 0,020`, qui est la résolution minimale de
cette expérience.

Cette conclusion protège uniquement la première colonne, évaluée avant tout
choix adaptatif antérieur. Elle ne doit pas être étendue aux onze colonnes
résiduelles. Leur contrôle exige de rejouer sous chaque permutation la
sélection et le réajustement séquentiels complets.

## Génération temporelle V5.5

La grille dense du premier diagnostic est remplacée par l'union des attaques
des quatre voix d'un choral réel. Chaque cellule contient un indicateur
`ATTACK` ou `HOLD`. Une variable générative correspond à une attaque et
contrôle la hauteur de tous ses blocs de tenue jusqu'à l'attaque suivante.

Lorsqu'une hauteur change, le sampler additionne les énergies de toutes les
décisions centrées sur une attaque dont le K3 intersecte la durée modifiée.
Cette sémantique évite de compter une blanche comme quatre noires répétées et
conserve les interactions avec les attaques des autres voix.

Le premier diagnostic utilise `bach/bwv108.6`, appartenant au train :

- `98` blocs verticaux ;
- `292` segments d'attaque, dont `223` rééchantillonnés ;
- soprano et rythme polyphonique fixés ;
- `100` cellules de tenue ;
- durées de `0,25`, `0,5`, `1` et `2` noires dans la partition produite ;
- cohérence des tenues exacte et aucun croisement de voix observé ;
- MusicXML et MIDI relus avec quatre parties.

Ce jalon démontre la génération de hauteurs apprises sur des rythmes
polyphoniques distincts. Il ne génère pas encore le rythme lui-même. Il révèle
aussi une lacune attendue du vocabulaire initial : aucune feature ne représente
la tonalité locale ou le degré d'échelle.

## Protocole ultérieur proposé pour apprendre le rythme

La prochaine expérience quantifie chaque choral à la double-croche, comme
DeepBach, avec le domaine local :

```text
ATTACK(pitch) | HOLD | REST
```

Pour isoler les sources de gain, l'induction sera effectuée en trois étapes :

1. hauteurs de Bach fixées, apprendre `ATTACK/HOLD` selon voix, position
   métrique et K3 ;
2. rythme fixé, réapprendre les hauteurs avec tonalité locale et degré
   d'échelle comme statuts explicites ;
3. sampler conjointement rythme et hauteur, puis mesurer séparément NLL
   rythmique, NLL de hauteur et qualité des partitions entières.

Une note courte en mouvement conjoint de même direction pourra ainsi être
découverte comme configuration statistique avant de recevoir, après gel, le
nom de « note de passage ». Les règles et poids gelés seront ensuite compilés
dans la base `S-K3-LEARNED` de Snarky ; V5.5 utilise encore directement
l'évaluateur K3 Python.

## Boucle contextuelle V5.6–V5.7

L'inspection de la première partition V5.5 a révélé trois défauts audibles et
visibles : chromatisme non contrôlé, sonorités verticales incohérentes et
répétitions attaquées fréquentes à la basse. Ces observations ont été
converties en mesures, puis en extensions minimales du vocabulaire :

- tonique et mode globaux déclarés par la partition ;
- distribution des classes relatives à la tonique, d'abord par mode puis par
  voix et mode ;
- fingerprint de l'ensemble vertical relativement à la basse ou à la tonique ;
- nombre de classes distinctes, conditionnable par niveau métrique ;
- répétition attaquée distinguée d'une tenue et spécialisable par voix.

La réinduction V5.6 repart d'une base vide avec 950 prédicats. Après la règle
générale de mouvement, elle sélectionne spontanément :

```text
{0,4,7} relatif à la basse
{0,3,7} relatif à la basse
{0,3,8} relatif à la basse
```

Les étiquettes « triade majeure », « triade mineure » et « triade majeure au
premier renversement » ne sont appliquées qu'après gel. Avec 18 règles, la NLL
validation atteint `1,150282`, contre `1,449123` pour V5.5.

L'analyse résiduelle montre ensuite que la répétition attaquée générale est
trop grossière : Bach répète légitimement les voix supérieures, alors que la
basse du choral diagnostique ne répète aucune de ses attaques rapides. V5.7
ajoute seulement la voix au statut et réinduit encore depuis zéro. La clause
numérique `attacked_repeat_from_previous(v3)` entre au rang 19 avec :

- z de sélection `-41,235` ;
- poids `-1,588788` ;
- facteur d'odds isolé `0,204`.

Sur le même soprano, le même rythme, la même graine et douze balayages :

| Mesure | Bach | V5.5 | V5.6 | V5.7 |
|---|---:|---:|---:|---:|
| répétitions attaquées basse | 0 | 20 | 19 | 7 |
| attaques tonalement rares | 0,68 % | 7,88 % | 3,08 % | 3,42 % |
| blocs triadiques | 45,92 % | 25,51 % | 52,04 % | 47,96 % |
| blocs structurels sélectionnés | 52,04 % | 25,51 % | 65,31 % | 62,24 % |
| blocs à deux classes | 2,04 % | 5,10 % | 1,02 % | 0,00 % |

Ces taux génératifs sur un choral du train sont diagnostiques. Ils ne
remplacent ni une campagne multi-pièces ni l'ouverture finale du test.

## Boucle chromatique V5.8

L'audit conditionnel est d'abord effectué sur les 50 chorals de validation,
sans charger le test. Les classes rares sont définies mécaniquement par une
fréquence train inférieure à 2 %, séparément par voix et mode. V5.7 les
**sous-estime** dans ses conditionnelles : `2,364 %` attendus contre `3,780 %`
observés chez Bach (`z=+11,41`). Une interdiction chromatique globale serait
donc contraire au corpus.

Le traitement local est très structuré : 82 % des choix rares authentiques
sont approchés par pas, 56 % ont une résolution immédiate par pas, 21 % sont
des broderies et 25 % des passages. Une campagne Gibbs porte ensuite sur 20
chorals de validation, deux graines et six balayages, avec soprano et rythme
authentiques :

| Modèle | NLL validation | Bach rare | Généré rare | Écart apparié |
|---|---:|---:|---:|---:|
| V5.7 | 1,120257 | 4,828 % | 5,925 % | +1,728 pp |
| V5.8 | 1,060328 | 4,828 % | 8,029 % | +3,654 pp |

V5.8 repart de zéro avec 1 026 prédicats, dont 72 interactions de licence
chromatique. Elle reconstruit exactement les vingt règles V5.7 puis ajoute huit
régularités verticales et mélodiques ; aucune interaction chromatique n'est
retenue. L'écart V5.8–Bach est pourtant significatif, IC95 `+1,466` à
`+5,841` points. V5.8 est donc **rejetée comme successeur génératif**, malgré
sa meilleure pseudo-vraisemblance.

Cette expérience établit la nécessité d'un second gradient pour V5.9 :

```text
g_r = E_Bach[f_r] - E_Gibbs[f_r]
```

Le premier terme récompense toujours les règles prédictives sur les choix
authentiques ; le second pénalise les moments que la génération amplifie. Les
poids restent signés et lisibles : une rareté générale peut recevoir un poids
négatif pendant que passage, broderie ou résolution reçoivent des licences
positives. Le test scellé reste fermé pendant ce calibrage.

## Frontière MusicXML et MuSES

Le corpus historique est distribué sous forme `.mxl`. MuSES ne possède pas
encore d'import MusicXML round-trip ; music21 reste donc l'adaptateur de lecture
à la frontière du corpus. Il permet également une vue optionnelle conservant
mesures, fermatas et autres détails de la notation source.

Le résultat généré canonique est désormais reconstruit comme une `Piece` MuSES
et exporté par MuSES en MIDI et MusicXML. Son titre et son compositeur valent
explicitement `Snarky / MuSES`. La vue conservant la mise en page historique
porte le suffixe `_source_layout` et corrige les mêmes métadonnées. music21
n'est ni le modèle, ni le générateur, ni l'auteur de la partition.
