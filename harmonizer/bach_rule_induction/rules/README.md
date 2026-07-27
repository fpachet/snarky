# Rule catalogue

Chaque règle sera stockée comme une `RuleCard` reliant :

- formulation destinée au musicien ;
- statut `MUST`, `NORMALLY`, `PREFER` ou `OBSERVED` ;
- conditions exprimées avec le registre de features ;
- statistiques séparées sur train, validation et test ;
- exemples de Bach, exceptions et contre-exemples DeepBach ;
- provenance pédagogique, CHORAL, experte ou induite ;
- règle Snarky exécutable lorsqu'elle est compilable.

Les manifestes futurs distinguent strictement :

- `S-HISTORICAL`, base Snarky écrite à la main et conservée intacte ;
- `S-LEARNED`, composée uniquement des `R-LEARNED-*` induites du corpus ;
- `S-HYBRID`, union explicite des deux bases.

Une `RuleCard` conserve séparément l'origine de la règle et celle de ses
features. Une règle induite peut donc consulter un statut harmonique défini par
l'humain sans être confondue avec une règle historique.

Avant toute recherche de nouveauté, le
[benchmark de redécouverte](KNOWN_RULE_RECOVERY.md) masque les règles Snarky
existantes et vérifie si le mineur les retrouve à partir du corpus.

L'algorithme proposé — groupes de décisions, beam search de clauses, MaxEnt
conditionnel sparse et génération de colonnes — est spécifié dans
[`INDUCTION_ALGORITHM.md`](INDUCTION_ALGORITHM.md).

## Premières RuleCards induites

- [`R-LEARNED-DIRECT-001.yaml`](R-LEARNED-DIRECT-001.yaml) : arrivée directe
  sur la classe numérique `0` ;
- [`R-LEARNED-DIRECT-002.yaml`](R-LEARNED-DIRECT-002.yaml) : arrivée directe
  sur la classe numérique `7`.
- [`R-LEARNED-MELODY-002.yaml`](R-LEARNED-MELODY-002.yaml) : classe mélodique
  numérique `6` modulo 12 ;
- [`R-LEARNED-OVERLAP-001.yaml`](R-LEARNED-OVERLAP-001.yaml) : frontière
  numérique `0` du chevauchement de voix adjacentes.
- [`R-LEARNED-PARALLEL-001.yaml`](R-LEARNED-PARALLEL-001.yaml) : répétition
  en mouvement conjoint de la classe numérique `0` ;
- [`R-LEARNED-PARALLEL-002.yaml`](R-LEARNED-PARALLEL-002.yaml) : répétition
  en mouvement conjoint de la classe numérique `7` ;
- [`R-LEARNED-LEADING-001.yaml`](R-LEARNED-LEADING-001.yaml) : tendance
  ascendante de la classe globale `11` et raffinements contextuels.
- [`R-LEARNED-ORDER-001.yaml`](R-LEARNED-ORDER-001.yaml) : première candidate
  V4 issue des croisements des générations apprises seules.

Les six premières cartes sont `SUPPORTED` et renvoient aux règles Snarky
expertes existantes, auxquelles elles sont extensionnellement équivalentes sur
le domaine local testé. Elles ne dupliquent donc pas leur compilation. La carte
de sensible est également `SUPPORTED` depuis le test gelé V3.8. Son statut
gradué combine le proxy `majeur + alto + basse 2→4` et un bonus pour le noyau
harmonique exact `vii°6→I6`. Il conserve `99,964 %` du gain des deux poids sur
les 51 chorals de test et sa compilation
[`learned_tonal_resolution.rules`](learned_tonal_resolution.rules) correspond
à l'oracle sur 256 états locaux abstraits. Il s'agit d'une préférence
`NORMALLY`, non d'une obligation dure.

`R-LEARNED-ORDER-001` reste `CANDIDATE`. La frontière de croisement strict
`-1` est beaucoup plus marquée dans les données authentiques que dans le
contrôle mélangé, mais ce dernier sélectionne encore la même forme avec un
effet faible. Une calibration familiale supplémentaire est requise avant
compilation et ajout au manifeste `S-LEARNED`.
