# Learned factor bases

Ce dossier contient uniquement des facteurs probabilistes issus d'un corpus.
Il est distinct de `rule_bases/`, qui contient les règles déclaratives écrites
par des experts, et des propagateurs de contraintes dures.

Un facteur comporte :

- un prédicat booléen sans effet de bord ;
- une portée locale explicite ;
- un paramètre logarithmique appris ;
- la provenance de sa sélection et de son ajustement.

Les activations ne sont jamais ajoutées à la mémoire de travail et ne peuvent
donc pas déclencher d'autres facteurs.

La séparation d'architecture est la suivante :

| Objet | Auteur | Effet |
|---|---|---|
| `RULE` | expert | dérive ou retire des faits |
| `CONSTRAINT` | expert | définit la faisabilité et propage des domaines |
| `FACTOR` | algorithme d'induction | décrit un motif booléen local et pur |
| `LOG_WEIGHT` | algorithme d'apprentissage | contribue au score probabiliste |
| `CHOICE`/Gibbs | moteur d'inférence | normalise les scores et échantillonne |

La grammaire de candidats et les primitives observables restent bien sûr des
choix méthodologiques humains. En revanche, pour `k3_v6_induced`, la sélection
des facteurs, leur signe et leurs paramètres ne sont pas écrits par l'expert.

- `k3_v5_16_reference/` conserve le POC V5.16 comme référence d'ingénierie ;
- `k3_v6_induced/` repart d'une grammaire gelée et apprend depuis zéro la
  structure et les paramètres.
