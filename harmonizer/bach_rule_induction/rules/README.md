# Rule catalogue

Chaque règle sera stockée comme une `RuleCard` reliant :

- formulation destinée au musicien ;
- statut `MUST`, `NORMALLY`, `PREFER` ou `OBSERVED` ;
- conditions exprimées avec le registre de features ;
- statistiques séparées sur train, validation et test ;
- exemples de Bach, exceptions et contre-exemples DeepBach ;
- provenance pédagogique, CHORAL, experte ou induite ;
- règle Snarky exécutable lorsqu'elle est compilable.

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
  en mouvement conjoint de la classe numérique `7`.

Les six cartes sont `SUPPORTED` et renvoient aux règles Snarky expertes
existantes, auxquelles elles sont extensionnellement équivalentes sur le
domaine local testé. Elles ne dupliquent donc pas leur compilation.
