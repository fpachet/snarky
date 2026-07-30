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

## Noyau explicatif V18

Le dossier [`v18_unanimous/`](v18_unanimous/) contient quatorze RuleCards
présentes dans cinq réinductions complètes sur cinq. Leurs poids sont réappris
sur 251 chorals et validés sur 50 ; le test de 51 chorals reste fermé. Elles
sont compilées comme préférences factorielles, jamais comme interdictions
absolues, dans
[`v18_unanimous_full.factors`](../factor_bases/k3_v6_induced/v18_unanimous_full.factors).

## Noyau explicatif V19

Le dossier [`v19_unanimous/`](v19_unanimous/) contient les dix-huit RuleCards
du noyau V19, présentes dans cinq découvertes complètes sur cinq. V19 ajoute
un vocabulaire déclaratif minimal pour reconnaître une triade majeure ou
mineure complète et distingue temps fort et temps faible. Le corpus, et non
l'expert, sélectionne ces deux facteurs, apprend leur signe positif et leur
poids.

Le programme
[`v19_unanimous_full.factors`](../factor_bases/k3_v6_induced/v19_unanimous_full.factors)
est numériquement identique à l'évaluateur Python à `8,88 × 10⁻¹⁶` près.
V19 est le checkpoint explicatif courant ; les règles V18 sont conservées
comme base de comparaison historique.

## RuleGroup V22 et contraintes candidates

[`v22_shared_root_motion/RG-LEARNED-V22-001.yaml`](v22_shared_root_motion/RG-LEARNED-V22-001.yaml)
décrit une seule règle structurée `mode × mouvement dirigé de fondamentale`.
Ses 24 poids sont appris conjointement et compilés avec le socle dans
[`v22_shared_root_motion_full.factors`](../factor_bases/k3_v6_induced/v22_shared_root_motion_full.factors).

Le dossier [`v22_candidate_constraints/`](v22_candidate_constraints/) contient
23 prédicats sans exception sur 251 chorals de train et 50 de validation. Ils
sont compilés comme filtres d'ablation dans `candidate_constraints.rules`,
mais restent `EMPIRICAL_PRETEST_FILTERS_NOT_MUST`. L'absence dans le corpus
n'est pas, à elle seule, une certification logique.

## RuleGroup V23

[`v23_metric_harmony/RG-LEARNED-V23-001.yaml`](v23_metric_harmony/RG-LEARNED-V23-001.yaml)
décrit le groupe `famille d'accord nommée unique × renversement` sur temps
fort. Ses quatorze poids sont appris conjointement ; l'absence d'analyse
unique constitue l'état de référence. Le groupe se réplique dans quatre folds
et sur la validation 251/50.

Le programme
[`v23_metric_harmony_full.factors`](../factor_bases/k3_v6_induced/v23_metric_harmony_full.factors)
contient les 43 facteurs V22 et les 14 nouveaux facteurs V23. Sa parité avec
l'évaluateur Python est passée à `8,88 × 10⁻¹⁶`. Les 23 filtres empiriques
restent hors du manifeste V23 retenu : leur combinaison générative avec V23
n'est pas favorable dans la première ablation.

## RuleGroup V24

[`v24_residual_sonority/RG-LEARNED-V24-001.yaml`](v24_residual_sonority/RG-LEARNED-V24-001.yaml)
décrit huit statuts exhaustifs pour les sonorités fortes que V23 laisse sans
analyse unique. Le vocabulaire de complétude et de licences
passage–retard–appoggiature est défini par l'analyste ; les huit poids sont
appris par les écarts de moments entre Bach et les générations.

Le groupe n'est pas retenu par pseudo-vraisemblance, mais améliore les
métriques harmoniques génératives sur validation. Son statut est donc
`GENERATIVELY_SUPPORTED_PRETEST`, pas `SUPPORTED` au sens explicatif. Le
programme
[`v24_contrastive_full.factors`](../factor_bases/k3_v6_induced/v24_contrastive_full.factors)
contient 65 facteurs et reproduit les scores Python à `8,88 × 10⁻¹⁶` près.
