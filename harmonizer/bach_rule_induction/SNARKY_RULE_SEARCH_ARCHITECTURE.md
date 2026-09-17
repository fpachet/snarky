# Architecture cible — apprendre une théorie, chercher avec Snarky

Le contrat opérationnel détaillé des deux boucles est défini dans
[`TWO_LOOPS_EXPERIMENT_PROTOCOL.md`](TWO_LOOPS_EXPERIMENT_PROTOCOL.md).

## Objectif

Le but n'est pas de reconstruire DeepBach sous forme de facteurs. Il est
d'induire une théorie locale, compacte et lisible du style choral de Bach,
puis d'utiliser un moteur symbolique pour trouver des réalisations qui
satisfont cette théorie.

La localité K3 — trois blocs verticaux consécutifs — borne le vocabulaire des
prédicats. Elle ne force ni une génération gloutonne, ni un échantillonnage
Gibbs : des contraintes K3 qui se recouvrent propagent sur toute la pièce.

## Séparation des responsabilités

| Phase | Entrée | Sortie | Ce qu'elle ne fait pas |
|---|---|---|---|
| Induction | corpus Bach train | prédicats et statistiques | générer la pièce finale |
| Estimation | activations conjointes | poids MaxEnt/pseudo-vraisemblance | déclarer seule une loi absolue |
| Validation | pièces réservées | statut retenu/rejeté, stabilité | modifier les règles |
| Compilation | base gelée | faits, contraintes et facteurs Snarky | réapprendre |
| Recherche | soprano, rythme, limites | une ou plusieurs solutions et leur trace | imiter un réseau neuronal |

Les trois rôles déclaratifs doivent rester distincts :

- **interdiction** : l'activation rend une candidate impossible ;
- **obligation** : dans un contexte défini, au moins une réalisation du
  conséquent doit subsister ;
- **préférence** : l'activation ajoute un poids appris, sans rendre les autres
  candidates impossibles.

Une règle peut déduire un statut musical (`passage`, `retard`, `cadence`,
etc.). Une contrainte portant sur ce statut reste persistante et participe à
la propagation. Un facteur ne déduit rien : il note un monde déjà décrit.

## POC V24 actuel

Le script
[`run_v24_snarky_search.py`](experiments/v5_k3_clean/run_v24_snarky_search.py)
construit un fragment SATB avec soprano et rythme fixés.

- Chaque bloc SATB est une variable finie.
- Chaque fenêtre de trois blocs est une variable factorielle.
- Une contrainte de table relie la fenêtre aux trois blocs qu'elle décrit.
- Les 23 prédicats V22 sans exception train/validation sont instanciés comme
  contraintes persistantes locales. Leur statut reste
  `EMPIRICAL_PRETEST_FILTER`, pas `MUST`.
- Les 65 facteurs V24 donnent les poids positifs des alternatives par
  exponentiation de la somme de leurs log-poids.
- La recherche Snarky atteint un point fixe, choisit, propage à nouveau et
  rollback en cas de contradiction.

Sur le fragment de référence (six blocs, trois hauteurs apprises par voix
inférieure), Snarky résout en trois décisions et quatre nœuds, sans Gibbs.
La somme factorielle réévaluée par le programme `.factors` coïncide avec le
modèle appris à `6,661 × 10⁻¹⁶`.

L'absence de backtrack dans cet exemple est un résultat, pas une option
désactivée : la première branche pondérée reste cohérente. Le moteur conserve
ses checkpoints réversibles et produira `CONTRADICTION` puis `BACKTRACK`
lorsqu'une contrainte rendra une branche impossible.

## Ce que le POC ne prouve pas

Le domaine `top-pitches` est volontairement petit afin de rendre l'énumération
des tables K3 contrôlable. Ce n'est pas le domaine musical final. Les blocs de
bord sont des conditions aux limites et les hauteurs maintenues depuis ces
bords sont ajoutées au domaine sans recopier les choix intérieurs de Bach.

Dans ce petit domaine, les 23 filtres V22 ne retirent actuellement aucune
valeur à la racine. La solution favorise aussi des répétitions. Cela établit
deux faits utiles :

1. la chaîne compilation–score–recherche fonctionne ;
2. la base V22/V24 ne suffit pas encore comme théorie générative.

Il serait incorrect de masquer ce second résultat par une pénalité experte
ajoutée au générateur. La boucle scientifique doit plutôt chercher un groupe
lisible qui explique le résidu.

## Prochaine boucle d'induction

La priorité est un groupe conjoint portant sur :

- classe de sonorité verticale et statut métrique ;
- fonction ou classe tonale de la basse ;
- préparation et résolution dans K3 ;
- répétition attaquée versus tenue ;
- compatibilité de la transition avec les deux fenêtres voisines.

Pour chaque groupe candidat :

1. geler le vocabulaire et sa complexité avant l'ajustement ;
2. mesurer couverture et valeurs extrêmes sur train ;
3. apprendre les poids conjointement par pseudo-vraisemblance ;
4. tester stabilité par pièces et gain tenu à part ;
5. tester séparément une version contrainte si le taux d'exception est nul ou
   sous un seuil préenregistré ;
6. compiler le groupe admis et relancer exactement la même recherche Snarky ;
7. comparer nombre de solutions, éliminations par propagation, backtracks,
   score tenu à part et diagnostics musicaux.

Le critère d'arrêt n'est pas « aucune fausse note dans un exemple ». C'est une
frontière reproductible où aucun groupe de complexité admissible n'améliore
simultanément la prédiction tenue à part, les diagnostics génératifs et la
parcimonie de la théorie.

## Première expérience de score minimal

[`run_two_loop_score_floor_experiment.py`](experiments/v5_k3_clean/run_two_loop_score_floor_experiment.py)
utilise les 57 facteurs V23 appris conjointement par MLE. Le minimum des
pseudo-vraisemblances moyennes de dix chorals de calibration fixe le threshold
strict à `−1,412463`.

Sur six blocs de BWV 108.6 :

- la première solution sans seuil obtient `−2,188816` et est rejetée ;
- 21 contradictions de score produisent 21 backtracks ;
- la première solution satisfaisante obtient `−1,277364` ;
- Bach authentique obtient `−0,277475` sur le même fragment, uniquement pour
  le diagnostic et sans participer à la recherche.

La seconde boucle est donc validée mécaniquement. La solution satisfaisante
reste toutefois très répétitive : le score global V23 ne suffit pas encore à
détecter cette pathologie. Ce faux négatif devient l'entrée prioritaire de la
prochaine boucle d'induction.

## Passage à l'échelle V28

La génération complète de BWV 108.6 utilise maintenant les 101 facteurs V28,
le soprano et le rythme authentiques, mais aucune des trois voix inférieures
de Bach. Les contraintes K3 déjà apprises sont propagées avant chaque choix :
une alternative qui complète une fenêtre interdite est retirée du domaine, et
un domaine vide déclenche immédiatement un backtrack.

La recherche résout les 98 blocs en explorant 801 nœuds. Elle préfiltre
10 536 alternatives et effectue 551 backtracks. La solution satisfait le
threshold appris (`−0,597431 > −1,394179`) et ne contient aucun croisement de
voix.

Cette propagation améliore le comportement observable sans transformer les
facteurs en contraintes cachées : les 23 contraintes empiriques déterminent
la faisabilité, les facteurs appris ordonnent les alternatives et le
threshold contrôle la qualité globale. Les diagnostics complets sont dans
[`V28_SNARKY_GENERATION_AUDIT.md`](factor_bases/k3_v6_induced/V28_SNARKY_GENERATION_AUDIT.md).
