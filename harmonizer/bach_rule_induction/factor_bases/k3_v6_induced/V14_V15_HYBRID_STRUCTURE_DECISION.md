# Décision V14–V15 — une règle prédictive peut dégrader la génération

## Décision

V14, V14-Ablation, V15.1 et V15.2 ne remplacent pas le checkpoint génératif
retenu `v6_train64_multimetric_iteration2_model.json`.

Ces expériences établissent néanmoins un résultat important pour la méthode :
la pseudo-vraisemblance exacte et la qualité des trajectoires générées ne sont
pas deux mesures interchangeables. Une clause peut améliorer la probabilité
conditionnelle du choix de Bach tout en dégradant la distribution stationnaire
obtenue lorsque le modèle rééchantillonne librement toutes les voix.

## Ce que V14 a ajouté

V14 croise dans une même clause :

- la paire de voix ordonnée ;
- la classe d'intervalle ;
- la force métrique ;
- le statut de réarticulation, tenue, mouvement conjoint, passage, voisin ou
  résolution de chacune des deux voix.

La grammaire ajoute 2 016 candidats au catalogue V13, soit 3 676 candidats au
total. La réinduction exacte sélectionne 30 facteurs et atteint une NLL de
validation de `0,749295`, contre `0,759483` pour V13 et `0,757960` pour V10.

Un seul nouveau facteur de trajectoire est sélectionné :

```text
central_pair_abs_class_metric_target_rearticulated(v1,v0)=2,1
weight = +2.065987
```

Il favorise, sur temps fort, une seconde entre alto et soprano lorsque l'alto
est réarticulé. Le corpus explique en partie cette association par la
résolution ultérieure de l'autre voix : les secondes fortes observées ne sont
donc pas de simples accords stables.

## Pourquoi V14 est rejeté

Sur le développement apparié, V14 est moins proche de Bach que V13 pour chacun
des dix diagnostics. Les dégradations les plus visibles sont :

| Diagnostic | Bach | V13 | V14 |
|---|---:|---:|---:|
| mouvements de basse par demi-ton | 25,37 % | 26,51 % | 28,89 % |
| grands sauts de basse | 27,95 % | 29,63 % | 31,27 % |
| blocs forts non triadiques | 27,56 % | 40,16 % | 44,66 % |
| dissonance forte moyenne | 0,381 | 0,600 | 0,697 |

La meilleure NLL conditionnelle de la série ne suffit donc pas à autoriser la
promotion générative.

## Ablation causale

Le nouveau facteur de trajectoire a été retiré seul, sans réajuster les 29
autres poids.

- NLL exacte de validation : `0,749295` → `0,760977` ;
- blocs forts non triadiques : `44,66 %` → `41,05 %` ;
- dissonance forte moyenne : `0,697` → `0,598`.

Le facteur n'est ni inutile ni dû à une erreur d'implémentation : il est
prédictif dans les mondes contrefactuels exacts. Mais il a un effet causal
défavorable sur l'équilibre génératif. C'est précisément le type de facteur
qu'une sélection uniquement conditionnelle ne sait pas refuser.

## Ce que V15 a montré

La covariance des chaînes persistantes détecte automatiquement le conflit. Le
résidu génératif demande moins de dissonances fortes, tandis que la sensibilité
du facteur V14 les augmente. Le pas de correction proposé pour son poids est
donc négatif.

V15.1 applique une correction multidiagnostic sous région de confiance et
budget de NLL exacte :

- NLL de validation : `0,749295` → `0,752978` ;
- amélioration de 9 diagnostics sur 10 par rapport à V14 ;
- blocs forts non triadiques : `44,66 %` → `40,88 %` ;
- dissonance forte moyenne : `0,697` → `0,599`.

V15.1 constitue une récupération méthodologique, pas une promotion : sa
distance générative agrégée à Bach reste supérieure à celle de V13.

V15.2 agrège trois nouvelles estimations indépendantes. Malgré une direction
inverse régularisée bien conditionnée, il n'améliore que 4 diagnostics sur 10
par rapport à V15.1 et porte la NLL à `0,753692`. Il est rejeté.

## Boucle V16 : admission hybride des facteurs

La correction générative ne doit plus intervenir seulement après avoir figé
une structure conditionnelle. Elle devient un garde-fou au moment même où une
nouvelle colonne est admise.

À chaque itération :

1. calculer sur train le gradient conditionnel exact de tous les candidats et
   conserver un petit top-K ;
2. faire évoluer des chaînes persistantes avec le modèle courant, une seule
   campagne servant à tous les candidats du top-K ;
3. estimer pour chaque candidat son effet sur les moments génératifs par
   covariance, avec au moins trois graines indépendantes ;
4. construire un petit pas contrefactuel dans la direction du candidat ;
5. déclarer le candidat admissible seulement si :
   - son gain conditionnel est positif ;
   - il ne dégrade pas au-delà d'une tolérance gelée la distance standardisée
     entre moments de Bach et moments Gibbs ;
   - le signe de son effet génératif est stable entre graines ;
   - le pas respecte une région de confiance ;
6. choisir parmi les candidats admissibles le point non dominé offrant le
   meilleur gain conditionnel, puis réajuster conjointement tous les poids ;
7. arrêter lorsqu'aucun candidat n'est admissible, lorsque la validation
   conditionnelle cesse de progresser, ou lorsque le budget de clauses est
   atteint.

Le critère d'admission est volontairement de Pareto, sans somme arbitraire
entre « qualité conditionnelle » et « qualité générative ». Un coefficient de
pondération pourra être étudié plus tard, mais il n'est pas nécessaire pour le
premier test scientifique.

La sélection de structure et les moments cibles restent strictement calculés
sur train. La validation sert à l'arrêt et aux hyperparamètres gelés. Le test
reste fermé jusqu'au choix d'un modèle final.

## Hypothèse testable

Si V16 fonctionne, le facteur V14 sera soit refusé lors de son admission, soit
admis avec un poids plus faible parce que son gain conditionnel devra payer son
coût génératif. Inversement, une règle légèrement moins spectaculaire en
pseudo-vraisemblance mais neutre ou corrective pour les accords pourra être
préférée.

Cette hypothèse distingue clairement :

- l'intelligibilité de la clause, fournie par la grammaire déclarative ;
- son utilité conditionnelle, apprise sur les choix authentiques ;
- son effet génératif, appris sur les chaînes du modèle ;
- la décision d'admission, prise sur le front de Pareto des deux objectifs.
