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
