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
- une variable CSP de rôle par note, choisie dans l'étape harmonique ;
- canalisation bidirectionnelle rôle–accord–voicing et support harmonique
  précédent/suivant ;
- triade complète sous passage, broderie ou anticipation ;
- politique d'omission de la note de résolution sous une suspension ;
- rôle et métrique sélectionnés exposés dans la solution ;
- exemple MuSES de huit mesures couvrant les cinq rôles étrangers avec cinq
  ancrages harmoniques locaux, sans plan complet ni étiquette de rôle.

L'exemple MuSES de huit mesures harmonise désormais chaque attaque
indépendamment. Sa première phrase parcourt toute la gamme ascendante de do
majeur et reçoit `I–V–I–IV–I–IV–V–I`. Le D reçoit le même domaine et les
mêmes contraintes que les autres notes. Une note étrangère n'est jamais
déduite de sa seule hauteur ; elle est relative à un accord explicitement
prolongé.

Suite musicale : hiérarchie métrique, appoggiatures et échappées, puis
politique d'omission pour les accords de quatre sons.

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
