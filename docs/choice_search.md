# Choix pondérés et backtracking

Le chaînage avant de Snarky reste déterministe et ne crée aucune recherche
implicite. La recherche est une couche publique distincte qui pilote des
sessions, des groupes de règles et des faits d'hypothèse.

## Objets publics

`ChoicePoint` nomme une variable de décision et contient des
`ChoiceAlternative`. Chaque alternative :

- affirme un ou plusieurs faits dans sa branche ;
- possède une valeur optionnelle pour les traces ;
- porte un poids fini et positif ou nul ;
- peut conserver des métadonnées métier.

`SessionChoiceSearch` reçoit :

1. les groupes à saturer après chaque décision ;
2. une fonction produisant les points encore ouverts depuis les faits ;
3. un prédicat de but ;
4. un prédicat optionnel de contradiction ;
5. une politique, un ordre de parcours et des limites.

La politique MRV choisit le plus petit domaine et ordonne par poids
décroissant. `WeightedRandomChoicePolicy` échantillonne sans remise,
proportionnellement aux poids, avec une graine reproductible. Un poids nul
reste faisable mais vient après les poids positifs.

Les parcours disponibles sont profondeur, largeur et meilleur poids d'abord.
Le score d'un chemin est la somme des logarithmes des poids. Il s'agit d'un
score de priorité : les contraintes et les règles déterminent seules la
faisabilité.

## Cycle d'une branche

```text
fork de la session
      ↓
assertion des faits de décision
      ↓
saturation des groupes jusqu'au point fixe
      ↓
contradiction ? abandon et backtrack
but atteint ? solution
sinon ? nouveau ChoicePoint
```

La session fournie au solveur n'est jamais modifiée. Une branche hérite de la
réfraction, des faits, de la provenance et de l'historique, puis évolue de
manière isolée. Les projets CSP reconstruisent un matcher semi-naïf vierge
dans chaque fork afin d'éviter la copie de ses caches volumineux.

La trace distingue `choice`, `decision`, `contradiction`, `backtrack`,
`solution`, `dead_end` et `limit`. Les limites techniques ne sont pas
confondues avec une contradiction logique.

## Statut du trail

Ce premier jalon restaure l'état en abandonnant le fork fautif. Il réutilise
donc la sémantique éprouvée d'`InferenceSession.fork()`, mais recopie encore la
mémoire de travail, la provenance et l'historique.

`PropagationState` possède déjà un trail local très moins coûteux pour les
domaines et les masques. Le prochain palier raccordera progressivement ce
trail au pilote :

1. checkpoint avant décision ;
2. réduction du domaine et propagation incrémentale ;
3. rollback des domaines, masques et deltas ;
4. restauration cohérente de la mémoire de travail et de la réfraction.

Cette optimisation ne doit pas changer l'API ni les traces observables.

## Applications de validation

[`csp_solver`](../csp_solver/README.md) exprime un CSP binaire par des faits et
des règles, sans appeler le solveur Python historique.
[`harmonizer`](../harmonizer/README.md) utilise le même protocole avec des
voicings SATB, des contraintes musicales dures et des poids dérivés de
marginales.
