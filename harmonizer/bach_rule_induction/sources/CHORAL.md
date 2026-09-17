# Source historique — règles du système CHORAL d'Ebcioğlu

## Résultat de la recherche

Le jeu de règles détaillé du système CHORAL est disponible dans une source
primaire :

> Kemal Ebcioğlu, *Report on the CHORAL Project: An Expert System for
> Harmonizing Four-Part Chorales*, IBM Research Report RC 12628, 20 mars 1987,
> 328 pages.

PDF publié sur le site de l'auteur :

<https://global-supercomputing.com/people/kemal.ebcioglu/pdf/RC12628.pdf>

Copie locale de référence :

[`docs/RC12628-Ebcioglu-CHORAL.pdf`](../../../docs/RC12628-Ebcioglu-CHORAL.pdf)

Le rapport est fondé sur la thèse d'Ebcioğlu :

> *An Expert System for Harmonization of Chorales in the Style of J. S. Bach*,
> Technical Report 86-09, SUNY Buffalo, mars 1986, 289 pages.

Le rapport IBM ajoute environ un an de travail à la thèse. Il constitue donc la
source à privilégier pour reconstruire l'état le plus développé de CHORAL.

L'appendice B, pages imprimées 234 à 311, est intitulé :

> *Production rules, constraints and heuristics of the CHORAL system*

Il annonce la description complète, en anglais condensé, des règles et
heuristiques de la version ayant produit la majorité des exemples du rapport.
Ebcioğlu y compte **354 paragraphes** décrivant chacun une règle de production,
une contrainte ou une heuristique. Les tables consultées par ces règles ne sont
pas incluses dans ce décompte.

Le rapport indique également environ :

- 11 700 lignes de BSL pour les bases de connaissances, ordonnanceurs et
  traducteurs de vues ;
- 2 400 lignes de C pour les graphismes et le prétraitement des mélodies ;
- 3 000 lignes de VM/Lisp pour le compilateur BSL.

Le texte proposait de communiquer le programme aux chercheurs intéressés, mais
aucune archive publique vérifiée du code BSL de CHORAL n'a été trouvée pendant
cette recherche. L'appendice B est donc la meilleure source publique connue
pour reconstruire la base de connaissances.

## Autres sources primaires

### Article AAAI 1986

Kemal Ebcioğlu, *An Expert System for Chorale Harmonization*, AAAI-86,
pages 784–788 :

<https://cdn.aaai.org/AAAI/1986/AAAI86-130.pdf>

Cet article décrit une version de plus de 270 règles, l'architecture à vues
multiples, BSL, la recherche avec backtracking et quelques exemples. Il ne
contient pas le catalogue complet.

### Article ICMC 1986

Kemal Ebcioğlu, *An Expert System for Harmonizing Four-Part Chorales*,
ICMC 1986 :

<https://quod.lib.umich.edu/i/icmc/bbp2372.1986.086>

Il s'agit d'une présentation courte de trois pages, utile pour confirmer les
principes du système mais insuffisante pour reconstruire les règles.

### Article de synthèse 1990

Kemal Ebcioğlu, *An Expert System for Harmonizing Chorales in the Style of
J. S. Bach*, *The Journal of Logic Programming*, volume 8, pages 145–185,
1990, DOI `10.1016/0743-1066(90)90055-A`.

Cette version publiée décrit le système plus précisément que les articles de
conférence, mais le rapport RC 12628 reste la source du catalogue complet.

## Organisation de la base CHORAL

CHORAL ne présente pas la musique sous la forme d'une seule suite de notes.
Plusieurs vues redondantes et synchronisées expriment naturellement des règles
différentes. Une décision incompatible avec une autre vue provoque un retour
arrière.

### 1. Vue du squelette d'accords — pages 234–267

Cette vue représente une suite d'accords sans rythme, accompagnés de la
tonalité, du degré, du renversement, des fermatas et de quelques motifs
harmoniques identifiés comme clichés.

Ses principales familles sont :

- génération des hauteurs structurelles du soprano, de l'alto, du ténor et de
  la basse ;
- choix et compatibilité des altérations ;
- classification des accords et renversements ;
- degrés admis en majeur et en mineur ;
- transitions entre degrés ;
- entrées dans une nouvelle tonalité et modulations ;
- clichés internes et cadentiels ;
- contraintes mélodiques sur les voix structurelles ;
- contraintes harmoniques et contrapuntiques ;
- heuristiques ordonnées pour guider les choix.

Les contraintes et préférences couvrent notamment :

- étendue, espacement, croisements et intervalles mélodiques ;
- mouvement et doublure de la sensible ;
- quintes et octaves consécutives, y compris certaines relations par mouvement
  contraire ;
- mouvements directs vers quintes et octaves ;
- contexte, préparation et résolution des septièmes ;
- accords diminués ;
- fausses relations ;
- accords de six-quatre cadentiels ou non cadentiels ;
- débuts et fins de phrases ;
- cadences et modulations ;
- choix du renversement et de la doublure ;
- continuité des progressions linéaires ;
- répétitions mélodiques, angles supérieurs et monotonie ;
- mouvement chromatique et écriture trop arpégée ;
- syncopes harmoniques ;
- clichés « bachiens ».

### 2. Vues du processus de remplissage — pages 268–290

Le squelette est réalisé avec une résolution d'une croche. Quatre automates,
un par voix, choisissent des notes de passage, broderies, suspensions et autres
notes non structurelles. Quatre représentations coopèrent :

- la vue `fill-in`, organisée par états de chaque voix ;
- la chaîne mélodique avec toutes les attaques ;
- la chaîne mélodique fusionnant les répétitions ;
- la vue verticale par tranches temporelles.

Les familles de règles comprennent :

- production des attaques fortes et faibles ;
- états normal, suspension et passage descendant accentué ;
- patrons de notes de passage et de broderie ;
- restrictions mélodiques sur deux ou plusieurs attaques ;
- ambitus, tritons et intervalles augmentés ou diminués ;
- répétitions rythmiques problématiques ;
- sauts simultanés et densité d'attaques ;
- ornementation de la sensible ;
- préparation et résolution des septièmes ;
- réalisation des cadences ;
- débuts, fins et frontières de phrases ;
- mouvement chromatique ;
- préparation, durée et résolution des suspensions ;
- quintes et octaves produites par les notes non structurelles ;
- mouvements directs et dissonances exposées ;
- fausses relations introduites par les ornements ;
- croisements de voix ;
- contexte des demi-notes ;
- heuristiques sur les suspensions, le mouvement conjoint, les lignes, les
  tierces et sixtes parallèles et la variété rythmique.

### 3. Vue d'analyse schenkerienne — pages 291–311

Cette vue analyse séparément le soprano et la basse à l'aide de deux analyseurs
ascendants non déterministes. Elle représente :

- les notes et liaisons analytiques ;
- les progressions linéaires ;
- l'arpégiation tonique–dominante–tonique de la basse ;
- une pile de progressions interrompues puis reprises ;
- des opérations `push`, `pop` et `hold` ;
- des transferts de registre et attentes structurelles ;
- une ligne fondamentale de tierce, quinte ou octave.

La base contient des règles de production des étapes d'analyse, des contraintes
sur les états et la pile, et des heuristiques choisissant les réductions
préférées.

Cette partie ne doit pas être confondue avec les règles de surface. Elle peut
néanmoins fournir à Snarky des features de longue portée : progression
linéaire, prolongation, attente structurelle, niveau d'une note et relation
entre squelette et ornement.

## Quelques règles représentatives

Les formulations ci-dessous sont des paraphrases de repérage. La transcription
normative devra retourner aux pages correspondantes du rapport.

### Progressions harmoniques

- En majeur, `I` peut conduire à `II`, `IV`, `VI`, `V` ou `VII`.
- `II` ou `IIp` conduit normalement à `V`.
- `II` ou `IIp` peut conduire à `I`, ou à `VI` en position fondamentale,
  lorsqu'une voix autre que la basse monte d'une tierce depuis la quinte de
  `II` vers la tonique.
- `VII` conduit à `I`.
- Le `I6/4` cadentiel peut être approché depuis certaines fonctions
  prédominantes et doit conduire à `V`.
- Les règles mineures sont distinctes et comportent des degrés associés aux
  formes ascendante et descendante du mode mélodique.

### Modulation

- La tonalité courante est conservée jusqu'à ce qu'une altération étrangère ou
  un contexte de fin de phrase motive une nouvelle analyse.
- Une nouvelle tonalité peut être abordée par sa dominante ou son septième
  degré sous des conditions portant sur les racines, les altérations et le
  mouvement des voix.
- D'autres entrées sont décrites comme plagales ou comme changements
  majeur–mineur à une frontière de phrase.
- Les modulations sont à la fois filtrées par des contraintes et classées par
  des heuristiques.

### Conduite des voix

- Certaines quintes diminuées suivies de quintes justes sont admises lorsque
  les voix montent conjointement ; cette exception résulte de l'observation des
  chorals et corrige la formulation pédagogique ordinaire.
- La préparation et la résolution d'une septième sont conditionnées par le
  type d'accord, la voix et le contexte.
- Les fausses relations sont généralement refusées, mais plusieurs exceptions
  précises dépendent de la voix portant la note altérée, de l'accord, du
  mouvement chromatique et de la frontière de phrase.
- Les croisements sont interdits dans le modèle, tout en étant explicitement
  reconnus comme une simplification qui ne décrit pas fidèlement tous les
  chorals de Bach.

### Ornements et suspensions

- La note de résolution d'une suspension ne doit normalement pas être entendue
  au-dessus de la suspension.
- Plusieurs suspensions consécutives dans une même voix forment une préférence
  stylistique forte.
- Une broderie ordinaire n'est admise que lorsqu'elle appartient à un contexte
  linéaire plus large.
- Certaines notes de passage sont imposées pour atténuer une fausse relation
  produite par le squelette.
- Les contraintes distinguent les fautes présentes au squelette de celles
  introduites par une note non structurelle.

### Préférences

- Continuer une progression linéaire, surtout à la basse.
- Préférer le mouvement conjoint ou par tierce.
- Éviter la répétition des mêmes sommets mélodiques.
- Éviter une écriture formée de plusieurs sauts successifs dans la même
  direction.
- Favoriser certains clichés cadentiels et certaines chaînes de suspensions.
- Préférer généralement les triades aux accords de septième, avec exceptions.
- Préférer certains renversements et certaines doublures selon le contexte.

## Pertinence directe pour le projet Snarky

Le rapport formule déjà plusieurs constats qui motivent notre projet :

- les règles des traités sont conçues pour des exercices et doivent être
  corrigées pour décrire les chorals réels ;
- les exceptions conditionnelles prolifèrent lorsqu'on cherche une fidélité
  absolue ;
- l'observation du corpus et le raisonnement inductif sont des sources
  légitimes de règles ;
- contraintes absolues et heuristiques doivent rester distinctes ;
- les heuristiques évitent de transformer chaque passage médiocre en une
  interdiction complexe ;
- reproduire algorithmiquement un passage de Bach permet de rechercher les
  raisons plausibles de chaque décision ;
- le rapport consacre une section entière à la possibilité d'un système
  découvrant ses propres règles et heuristiques.

CHORAL doit donc devenir une baseline historique `E0`, et non être utilisé
comme un oracle infaillible. Ebcioğlu documente lui-même :

- des simplifications de son modèle ;
- des licences de Bach volontairement refusées ;
- des exceptions non exhaustives ;
- une tendance excessive de CHORAL à moduler ;
- des sorties techniquement acceptables qui ne reproduisent pas entièrement le
  style de Bach.

## Extraction structurée disponible

L'appendice B est désormais inventorié dans
[`choral/`](choral/README.md). Le sous-répertoire contient :

- 1 293 unités sources ordonnées et localisées ;
- 775 cartes publiques atomiques et paraphrasées ;
- 7 tables ou catalogues structurés ;
- un [index thématique](choral/INDEX.md), un
  [rapport d'extraction](choral/EXTRACTION_REPORT.md), le
  [schéma](choral/SCHEMA.md) et un validateur reproductible.

La chaîne carte → unité → page/boîte/empreinte est publique. La transcription
complète, les images et les OCR restent sous `choral/work/`, ignoré par Git,
car les droits de redistribution ne sont pas établis. Les unités comportant
une notation ou un jeton OCR faible restent explicitement en `needs_review` ;
elles ne sont pas corrigées par supposition.

## Protocole de reconstruction

### Identité de source

Le PDF utilisé pour ce repérage avait l'empreinte SHA-256 :

```text
1e15961a4855bb8b6610fe5fc1c5db6bfdddf54f6129f36cee5f5a7d26643d8c
```

La copie locale est une référence de travail demandée explicitement pour
préserver l'accès à cette source ancienne. Ses droits de redistribution ne sont
pas établis : elle doit rester exclue des distributions Python et des versions
publiques étiquetées jusqu'à clarification. L'OCR brut n'est pas conservé dans
le dépôt. Les règles publiées par le projet doivent être des paraphrases
structurées et des implémentations indépendantes avec références de pages.

### Identifiants

L'extraction réalisée utilise trois espaces d'identifiants stables :

```text
CHORAL-B-P0234-U001   # unité source, page imprimée 234
CHORAL-CARD-0001      # proposition interprétée
CHORAL-TABLE-P0239-T01
```

L'identité d'une unité dépend de sa page imprimée et de son rang documentaire,
pas d'une classification interprétative susceptible d'évoluer. Lorsqu'un bloc
contient plusieurs propositions, celles-ci reçoivent des cartes séparées qui
pointent vers la même unité. `document_order`, `section_path` et
`unit_index_on_page` rendent la reconstruction déterministe.

### Fiche d'import

Chaque règle reconstruite doit enregistrer :

- page et section de la source ;
- empreinte du texte anglais privé et paraphrase publique fidèle ;
- vue CHORAL d'origine ;
- nature : production, contrainte ou heuristique ;
- conditions et conclusion normalisées ;
- exemples et réserves d'Ebcioğlu ;
- dépendances envers des tables ou d'autres règles ;
- features Snarky requises ;
- traduction Snarky éventuelle ;
- statut de validation sur corpus ;
- relation avec une règle `R-*` existante ;
- décision : fidèle, adaptée, rejetée ou différée.

### Ordre d'import recommandé

1. Contraintes du squelette déjà représentables par les faits Snarky.
2. Contraintes du `fill-in` sur suspensions, notes de passage et dissonances.
3. Heuristiques du squelette et du `fill-in`.
4. Règles de modulation nécessitant la tonalité locale.
5. Clichés et règles dépendant de patrons plus longs.
6. Features et règles schenkeriennes.

### Contrôles

- Vérification manuelle sur l'image de chaque page : l'OCR du scan est très
  bruité.
- Conservation séparée du sens historique et de l'adaptation moderne.
- Tests sur les exemples cités par Ebcioğlu lorsqu'ils sont identifiables.
- Mesure sur le corpus Bach avant de classer une règle comme `MUST`.
- Recherche systématique des contre-exemples authentiques.
- Comparaison avec la règle Snarky experte et la règle induite correspondante.

## Comparaison à produire

Pour chaque famille, le catalogue final doit permettre une comparaison à
quatre colonnes :

| Source | Formulation | Statut | Validation |
|---|---|---|---|
| Traité pédagogique | règle générale | prescriptive | non mesurée |
| CHORAL/Ebcioğlu | règle et exceptions manuelles | contrainte ou heuristique | exemples choisis |
| Snarky expert | règle exécutable actuelle | `MUST` ou préférence | tests ciblés |
| Snarky induit | raffinement appris | `MUST`, `NORMALLY`, `PREFER` ou `OBSERVED` | train/validation/test |

Cette comparaison permettra de déterminer :

- ce que Snarky redécouvre indépendamment ;
- ce que CHORAL décrit déjà plus précisément que les traités ;
- ce que le corpus moderne contredit ou nuance ;
- ce qui exige une nouvelle feature ;
- ce qui relève réellement d'une préférence propre au style.
