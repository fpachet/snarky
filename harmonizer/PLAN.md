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

## Jalon 3 — profil dur `ROY_1998`

Ajouter degrés, renversements, vocabulaire, doublures, sensible, cadence,
progressions et exceptions. Chaque règle stable `R-*` recevra ses cas positif,
négatif, limite et exception. Étendre parallèlement l'entrée MuSES aux
tonalités supportées, silences et informations métriques réellement utilisées
par ces règles.

## Jalon 4 — préférences et probabilités — premier palier livré

Les marginales statiques, les marginales conditionnelles à la note précédente,
les N meilleures solutions best-first et l'échantillonnage reproductible sont
livrés. Restent les objectifs lexicographiques et un modèle probabiliste appris
ou calibré sur corpus.

## Jalon 5 — `FOUR_PART_COMPLETE`

Ajouter six-quatre fonctionnels, accords de septième, notes étrangères,
métrique et modulations uniquement après validation du profil historique.
