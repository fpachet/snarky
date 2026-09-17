# V34 — accords nommés, résolution et recherche Snarky

## Question

V33 supprimait les sonorités fortes non licenciées, mais conservait trop
d'accords nommés dissonants et trop de chaînes dissonance → dissonance. V34
demande si un petit état harmonique observable sur deux temps forts suffit à
expliquer et à contraindre ce phénomène.

L'état n'est pas latent : il est calculé déterministement à partir des quatre
hauteurs, de la fondamentale éventuelle, de la famille d'accord et de la
sonorité forte suivante. Les cinq familles dissonantes sont septième de
dominante, septième commune, famille diminuée, accord altéré nommé et accord
nommé ambigu. Les issues compactes sont : triade suivante, autre accord nommé
dissonant, ou sonorité résiduelle.

## Estimation corpus

Sur les 251 chorals de train, 1 342 des 8 176 transitions fortes (`16,414 %`)
partent d'un accord nommé dissonant. Parmi elles, `67,884 %` arrivent sur une
triade, `15,872 %` sur un autre accord nommé dissonant et `16,244 %` sur une
sonorité résiduelle. Le BIC préfère la table commune à trois issues
(`2296,70`) à cinq tables propres aux familles (`2329,16`).

Les poids sont des MLE catégoriels explicites. Pour 25 transitions fortes, le
quantile binomial supérieur à 95 % donne au plus sept accords nommés
dissonants et trois chaînes dissonance → dissonance.

La réplication stricte échoue cependant : le taux vaut `14,599 %` sur les 50
chorals de validation et `12,328 %` sur les 51 chorals de test, sous
l'intervalle de Wilson du train `[15,627 % ; 17,233 %]`. Le taux de chaîne
échoue de même. Le modèle V34 reste donc `REJECTED`; ses budgets ne peuvent
servir qu'à une ablation explicitement étiquetée.

## Compilation et propagation

Le moteur sait désormais :

- ajouter les quatre facteurs V34 aux énergies locales ;
- maintenir deux comptes persistants (accords dissonants et chaînes) ;
- déclencher une contradiction au dépassement ;
- préfiltrer un candidat dès qu'il ferme une transition hors budget ;
- refuser de charger ce modèle rejeté sans l'option d'ablation explicite.

Ce préfiltrage ne modifie pas le modèle ni l'ensemble des solutions : les
comptes sont monotones, donc une branche déjà au-dessus du maximum ne peut
plus redevenir admissible.

## Résultat de recherche

La recherche chronologique sans look-ahead atteint 5 000 nœuds et 4 600
domaines vides. Elle élimine 37 420 candidats par le budget harmonique et
54 986 par les contraintes K3, sans trouver de solution complète.

Une seconde stratégie assigne d'abord les 78 segments qui contrôlent les 26
temps forts, puis les 151 segments faibles. Elle atteint elle aussi la limite
de 5 000 nœuds, avec 4 674 domaines vides et 135 546 alternatives éliminées
par les contraintes. Le budget harmonique n'est alors pas la cause immédiate
des échecs : basse, ténor et alto sont choisis séparément et de nombreuses
paires partielles n'admettent aucune troisième voix.

Il n'existe donc pas de nouvelle génération V34 à écouter. Conserver le
dernier résultat `limit_reached` est préférable à relâcher les seuils après
observation.

## Décision

V34 produit deux résultats négatifs utiles et séparés :

1. le petit modèle harmonique est intelligible mais ne réplique pas ses taux
   entre les splits ; il n'est pas promu ;
2. un choix note par note avec backtrack chronologique est une mauvaise
   compilation des contraintes verticales, même lorsque celles-ci sont
   connues.

La prochaine expérience doit conserver exactement les facteurs et
contraintes admis, mais compiler les trois voix inférieures d'un temps fort
en une variable d'accord conjointe. Son domaine sera obtenu par propagation
des contraintes V33 existantes, et non par l'ajout manuel de la règle
« accord nommé obligatoire », que le corpus contredit. Après choix du
squelette, les segments faibles seront remplis dans leurs noyaux K3. Cette
modification concerne le moteur de résolution, pas l'induction musicale.

## Artefacts

- `v34_named_resolution_audit.json` : états observables et audit des splits ;
- `v34_harmonic_budget_model.json` : MLE, BIC, confirmation et budgets ;
- `v34_harmonic_resolution.factors` : facteurs exportés ;
- `two_loop_full_generation_v34.json` : dernière recherche bornée ;
- `TWO_LOOP_FULL_GENERATION_V34.md` : rapport généré automatiquement.
