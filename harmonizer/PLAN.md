# Plan de développement de l'harmoniseur

## Jalon 1 — livré

- projet autonome et exécutable ;
- voicings SATB finis ;
- contraintes verticales essentielles ;
- trois relations de transition ;
- choix pondérés et best-first ;
- exposition des notes choisies par règles Snarky ;
- transitions intensionales révisées dans les deux directions ;
- formulation extensionnelle conservée comme oracle ;
- benchmark reproductible à deux et quatre positions.

## Jalon 2 — variables de notes — livré pour le noyau

Le choix initial d'un voicing complet est remplacé par les quatre variables de
notes préconisées dans la spécification. Tessitures, ordre, espacements et
règles mélodiques précèdent la construction différée des voicings. La
génération et l'élimination des candidats musicaux sont pilotées par des
groupes de règles explicables.

Le jalon livre maintenant :

- une variable CSP par voix et position ;
- une ligne donnée sélectionnable parmi soprano, alto, ténor et basse ;
- une construction différée des voicings par règle ;
- ordre et espacements écrits dans le DSL ;
- canalisation réversible notes–voicings ;
- transitions intensives par recherche de supports ;
- trace des éliminations et décisions.

## Jalon 2b — frontière MuSES — livré

- encodage d'une `TemporalCollection` donnée en faits Snarky ;
- import de ses hauteurs dans les domaines par un groupe de règles ;
- exécution du noyau note par note et de sa recherche ;
- reconstruction factuelle de quatre `TemporalCollection` ;
- assemblage d'une `Piece` MuSES SATB ;
- préservation du rythme et des métadonnées sans mutation de la source ;
- API injectable, test sans dépendance et validation avec les vraies classes ;
- exemple exécutable et benchmark séparant moteur et frontière objet.
- orchestration inspectable par `RuleProgram`, sans groupe CSP inactif.

## Jalon 3a — squelette tonal — livré

- tessitures diatoniques complètes en do majeur ;
- variables d'accord et de renversement à chaque position ;
- degrés `I`, `ii`, `IV`, `V`, `vi` ;
- fondamentale et premier renversement ;
- génération déclarative de voicings à six composantes ;
- canalisation accord–renversement–notes–voicing ;
- table de progressions fonctionnelles ;
- forme initiale `I` et cadence finale `V → I` à l'état fondamental ;
- marginales conditionnelles des accords ;
- exemple MuSES `C5–A4–B4–C5` harmonisé depuis la ligne seule et oracle
  ciblé `I–ii–V7–I` pour la septième de dominante.

## Jalon 3b — enrichissement tonal — premier palier livré

- `vii°` au premier renversement ;
- `V7` complet à l'état fondamental ;
- `I64` cadentiel avec basse pédale et résolutions `6→5`, `4→3` ;
- règles `R-DOUBLING-001..007` applicables au sous-ensemble courant ;
- résolution de la sensible et de la septième de dominante ;
- cadences parfaite, plagale, rompue et demi-cadence ;
- rythme harmonique explicite par partage des variables d'accord ;
- oracles ciblés et nouvelle baseline de performance.
- exemple MuSES long de huit notes, `I–V–I–IV6–ii–ii–V7–I`, exporté en
  MIDI et MusicXML.
- programme à étapes réversibles : choix du plan harmonique, puis réalisation
  SATB, avec retour possible vers un autre plan ;
- exemple MuSES étendu de huit mesures et seize notes produisant
  `I–IV–I–IV–I–IV–ii–V–I` depuis la seule soprano, le rythme et la cadence,
  exporté en MIDI et MusicXML ;
- complétude par `NVALUE` et doublures par `COUNT`, sans callback musical ;
- faits de violation `R-*` pour mouvement, chevauchement, parallèles,
  mouvements directs, sensible, septième et `I64` ;
- tests positifs, négatifs, limites et exceptions du noyau de conformité.

## Jalon 3c — rôles mélodiques conjoints — livré

- analyse déclarative du contour précédent–courant–suivant ;
- passages ascendants et descendants conjoints ;
- broderies supérieures et inférieures ;
- suspensions préparées et résolues, anticipations ;
- faits métriques forts/faibles dérivés des débuts MuSES ou fournis à l'API ;
- faits de durée et classification déclarative des notes contextuellement
  courtes ;
- une variable CSP de rôle par note, choisie dans l'étape harmonique ;
- canalisation bidirectionnelle rôle–accord–voicing, avec maintien exact du
  voicing inférieur pour les rôles de continuation ;
- triade complète sous passage, broderie ou anticipation ;
- politique d'omission de la note de résolution sous une suspension ;
- rôle et métrique sélectionnés exposés dans la solution ;
- fusion à l'export des voix inférieures tenues, sans réarticulation à chaque
  note de soprano ;
- exemple MuSES de huit mesures harmonisant la majorité des attaques et
  illustrant broderie inférieure, suspension et anticipation avec deux
  ancrages harmoniques locaux, sans plan complet ni étiquette de rôle ;
- couverture ciblée par tests des passages et broderies supérieures.

Passages, broderies et anticipations exigent désormais une durée d'au plus une
noire et non supérieure à celles des deux notes voisines. Une note conjointe
faible mais longue reste donc une note structurelle à harmoniser.

### Attaques et tenues déclaratives — livré

La décision musicale « attaquer ou prolonger » est exposée par le programme
Snarky sous forme de faits par voix, par exemple :

```text
(position_1 continues_voice_from SEQ[alto position_0])
```

Les règles les dérivent pour passage, broderie, anticipation, échappée,
suspension et appoggiature lorsque les hauteurs sélectionnées sont identiques.
La solution les expose comme
`VoiceContinuation(position, voice, previous_position)`.
L'adaptateur MuSES ne consulte plus `melodic_roles` : il consomme uniquement
ces continuations, vérifie position précédente, égalité de hauteur et
contiguïté, puis calcule la durée et sérialise MIDI/MusicXML.

Deux hauteurs adjacentes identiques restent donc réarticulées en l'absence de
fait de continuation. Les règles décident seules de la réarticulation ou de la
tenue ; Python ne réalise que la projection temporelle du résultat symbolique.

L'exemple MuSES de huit mesures couvre toutes les classes de hauteur de do
majeur. Le D faible est une échappée sur I ; le C accentué est une
appoggiature de V résolue sur B. Une note étrangère n'est jamais déduite de sa
seule hauteur : le contour et le niveau métrique ajoutent un candidat, puis
l'accord et le voicing sélectionnés décident si ce candidat est réalisable.

## Jalon 3d — métrique hiérarchique et politiques de rôle — livré

- niveaux métriques `0..3` : subdivision, pulsation, accent secondaire et
  temps principal de mesure ;
- dérivation Snarky de la vue forte/faible, avec compatibilité de l'ancienne
  API binaire ;
- consommation de `muses.metric_positions` pour les niveaux, y compris les
  groupes de pulsations des mesures composées, sans second calcul dans
  l'adaptateur Snarky ;
- appoggiatures supérieures et inférieures, attaquées par saut au niveau 3 et
  résolues par mouvement conjoint opposé ;
- échappées supérieures et inférieures, courtes aux niveaux 0–1, approchées par
  mouvement conjoint et quittées par saut opposé ;
- faits de politique `accompaniment_policy` et `lower_voice_policy` séparant
  la catégorie musicale de son comportement de canalisation ;
- règles génériques de maintien depuis l'accord précédent ou vers l'accord de
  résolution, sans tests négatifs énumérant les rôles connus ;
- cas positifs, négatifs, limites métriques et ambiguïtés harmoniques ;
- exemple MuSES de huit mesures couvrant toutes les classes de hauteur de do
  majeur, une échappée et une appoggiature, avec seulement deux ancrages
  harmoniques locaux et aucune étiquette de rôle.

Suite musicale : politique d'omission pour les accords de quatre sons, retards
ascendants et autres ornements, puis contexte de tonalité et modulation.

Restent aussi les renversements de `V7`, autres septièmes, six-quatre de
passage ou de pédale, exceptions complètes et tonalités multiples. Chaque
nouvelle extension stable `R-*` recevra ses cas positif, négatif, limite et
exception sur le modèle de `tests/test_harmonizer_conformance.py`.

## Jalon 4 — préférences et probabilités — premier palier livré

Les marginales statiques, les marginales conditionnelles à la note précédente,
les N meilleures solutions best-first et l'échantillonnage reproductible sont
livrés. Restent les objectifs lexicographiques et un modèle probabiliste appris
ou calibré sur corpus.

## Jalon 5 — `FOUR_PART_COMPLETE`

Ajouter les six-quatre non cadentiels, les autres accords de septième, autres
catégories de notes étrangères, métrique et modulations uniquement après
validation du profil historique.
