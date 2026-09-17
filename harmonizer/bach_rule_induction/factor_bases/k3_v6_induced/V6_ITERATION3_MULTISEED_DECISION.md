# V6 — décision sur l'itération 3 multigraine

## Question

Le meilleur checkpoint V6, l'itération 2, possède-t-il encore un résidu
contrôlable par un simple réajustement des 30 poids, ou faut-il rouvrir la
structure factorielle ?

Le test réservé reste fermé. Les facteurs, leurs portées et leurs prédicats
restent strictement inchangés pendant toute cette expérience.

## Estimation multigraine sur train

Trois campagnes indépendantes utilisent :

- 32 chorals de train ;
- 2 chaînes par pièce ;
- 6 sweeps de burn-in ;
- 8 états conservés, espacés de 2 sweeps ;
- les 10 diagnostics explicites ;
- le sampler séquentiel compilé ;
- les graines `10103`, `20207` et `30313`.

Les trois Jacobiennes ont le rang complet `10`. Les résidus gardent le même
signe sur huit diagnostics sur dix. En revanche, l'inversion presque non
régularisée est instable :

- cosinus des corrections : `0,473`, `0,199`, `0,468` ;
- seulement `13/30` poids gardent le même signe.

Il serait donc incorrect d'appliquer directement l'une de ces corrections.

## Régularisation de stabilité

Une grille de ridge est parcourue dans l'ordre croissant. Le premier niveau
retenu doit simultanément :

1. produire un cosinus minimal de `0,80` entre les trois corrections ;
2. améliorer la projection sur chacune des trois graines ;
3. conserver tout déplacement absolu sous `0,05`.

Le premier niveau admissible est `ridge = 1`. Le pas consensus possède :

- un déplacement maximal de `0,039832` ;
- un résidu standardisé ensemble restant de `0,534` ;
- des améliorations linéaires projetées de `28,2 %`, `57,4 %` et `39,6 %`.

La NLL conditionnelle de validation, non utilisée pour construire le pas,
baisse de `1,241166` à `1,238870`.

## Audit génératif apparié à 6 sweeps

L'itération 2 et l'itération 3 sont comparées sur les mêmes 50 chorals de
validation et les mêmes trois graines.

| Diagnostic | Itération 2 − Bach | Itération 3 − Bach | I3 − I2 | IC95 apparié |
|---|---:|---:|---:|---:|
| Grands sauts de basse | +0,00498 | +0,01042 | +0,00544 | −0,00494 à +0,01581 |
| Basse hors gamme naturelle | +0,01522 | +0,01296 | −0,00227 | −0,00788 à +0,00335 |
| Répétitions de basse | +0,01051 | +0,01436 | +0,00385 | −0,00100 à +0,00871 |
| Demi-tons à la basse | +0,00461 | −0,00521 | −0,00982 | −0,02003 à +0,00040 |
| Accords forts non triadiques | +0,02575 | +0,00921 | **−0,01654** | **−0,03131 à −0,00176** |
| Dissonances par bloc fort | +0,03954 | −0,00441 | **−0,04395** | **−0,07035 à −0,01755** |
| Taux triadique | −0,00514 | +0,00270 | +0,00784 | −0,00281 à +0,01849 |

Six diagnostics sur dix se rapprochent de Bach. Les deux gains harmoniques
principaux sont significatifs.

## Contrôle à 30 sweeps

Le contrôle long reprend dix chorals de développement et trois graines.

| Diagnostic | Itération 2 − Bach | Itération 3 − Bach | I3 − I2 | IC95 apparié |
|---|---:|---:|---:|---:|
| Répétitions de basse | +0,00228 | +0,00201 | −0,00028 | −0,01318 à +0,01263 |
| Accords forts non triadiques | −0,02127 | −0,03667 | −0,01540 | −0,05305 à +0,02225 |
| Dissonances par bloc fort | −0,00759 | −0,00982 | −0,00223 | −0,07836 à +0,07389 |
| Taux triadique | +0,03902 | +0,05618 | **+0,01715** | **+0,00096 à +0,03335** |

À l'horizon long, l'itération 2 produit déjà trop de blocs triadiques et trop
peu de blocs forts non triadiques sur ce sous-ensemble. L'itération 3 accentue
ce biais. Le gain court n'est donc pas une amélioration uniforme de la loi
stationnaire.

## Décision

**L'itération 3 n'est pas promue comme meilleur checkpoint.** L'itération 2
reste la référence générative.

Le résultat est informatif : les poids peuvent réduire les dissonances fortes
à court horizon, mais les diagnostics actuels poussent surtout une opposition
trop grossière entre `triadique` et `non triadique`. Continuer les petits pas
de poids risquerait de produire des accords plus simples sans mieux modéliser
les accords bachiques.

La prochaine boucle doit donc rouvrir l'induction de façon ciblée, sans
recommencer les 30 facteurs :

1. décomposer les blocs non triadiques par empreinte transposable et statut
   métrique ;
2. distinguer les accords bachiques fréquents des sonorités réellement
   résiduelles ;
3. ajouter le mouvement de basse et les notes non harmoniques résolues dans le
   même noyau K3 ;
4. induire quelques facteurs courts sur les résidus de l'itération 2 ;
5. accepter une nouvelle structure uniquement si elle améliore à la fois les
   audits à 6 et 30 sweeps.

## Premier diagnostic de structure résiduelle

Les 192 états finaux déjà produits — 32 pièces, 3 graines et 2 chaînes — sont
réutilisés pour comparer 782 facteurs lisibles, pièce par pièce. Une candidate
n'est prioritaire que si son gradient garde le même signe sur les trois
graines et si `|z| ≥ 2`.

Dix-huit candidates passent ces filtres, dont :

- favoriser la seconde entrante à la basse : Bach `0,3686`, Gibbs `0,2825` ;
- éviter les sauts de basse supérieurs à deux demi-tons : Bach `0,3289`,
  Gibbs `0,4079` ;
- favoriser l'intervalle vertical 7 sur bloc fort ;
- favoriser la sonorité `{0,4,9}` relative à la basse sur bloc faible ;
- éviter `{0,5,8}` sur bloc fort ;
- éviter la répétition de la sonorité `{0,3,6,8}` ;
- distinguer les transitions `{0,4,7} → {0,4,7,10}` et
  `{0,4,7,10} → {0,4,7}`.

Ces résultats confirment la lacune : l'identité métrique des sonorités et leur
trajectoire locale portent une information que le taux triadique global perd.
Le classement complet est dans
[`V6_ITERATION3_RESIDUAL_FEATURE_DIAGNOSTIC.md`](V6_ITERATION3_RESIDUAL_FEATURE_DIAGNOSTIC.md).
