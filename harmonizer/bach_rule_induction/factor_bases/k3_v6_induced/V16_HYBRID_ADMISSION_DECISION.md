# Décision V16 — distinguer régime transitoire et régime long

## Décision

Aucun candidat V16 n'est promu. V13 reste le meilleur modèle de cette branche
conditionnelle, et `v6_train64_multimetric_iteration2_model.json` reste le
checkpoint génératif global.

V16 valide l'architecture générale « gain conditionnel + garde-fou
génératif ». Son premier estimateur, la covariance, se révèle informatif à
horizon long mais non fiable pour le sampler transitoire à six balayages. Une
admission scientifique doit donc mesurer explicitement les deux régimes.

## Présélection exacte

Sous les 30 facteurs V13, les gradients résiduels exacts ont été recalculés
pour les 3 676 clauses de la grammaire V14 :

- 69 clauses passent les seuils conditionnels ;
- 12 forment le top-K soumis au criblage génératif ;
- aucune clause n'est ajoutée pendant cette mesure ;
- le test réservé reste fermé.

Les activations des 12 candidats à poids nul sont observées dans une campagne
commune de chaînes persistantes : 32 chorals de train, deux chaînes par pièce,
trois graines indépendantes et dix diagnostics explicites.

## Premier filtre et réussite négative sur le facteur V14

Le premier filtre demande :

- un score conditionnel positif ;
- un cosinus minimal de `0,5` entre les effets estimés par graine ;
- une amélioration moyenne stricte ;
- au plus `2 %` de régression sur une graine ;
- un pas borné à `0,15`.

Quatre candidats sur douze passent. Surtout, la clause qui avait causé les
dissonances de V14 est maintenant refusée :

```text
central_pair_abs_class_metric_target_rearticulated(v1,v0)=1,1
minimum inter-seed cosine = -0.753
ensemble relative remaining = 1.001
```

Le garde-fou détecte donc correctement ce cas causal connu.

## Candidat rang 5 : échec court, succès long

Le candidat offrant le meilleur score conditionnel parmi les quatre admis est :

```text
any_voice_three_block_sign_shape(all_voices)=0,-1
```

Il favorise l'existence, dans une voix quelconque, d'une tenue suivie d'un
mouvement descendant. Le pas local `+0,15` prédit un résidu génératif restant
de `0,9918`.

Résultats exacts :

- NLL V13 : `0,759483` ;
- NLL avec le seul pas `+0,15` : `0,757944` ;
- NLL après réajustement conjoint, poids final `+0,519396` : `0,756250`.

Le gain conditionnel est réel. L'audit génératif de développement à six
balayages le rejette néanmoins :

| Modèle | Distance L1 aux dix moments de Bach |
|---|---:|
| V13 | 0,5088 |
| pas local `+0,15` | 0,5622 |
| réajustement conjoint | 0,5486 |

À six balayages, la dichotomie confirme l'absence de zone favorable :

| Poids | NLL validation | Distance générative |
|---:|---:|---:|
| 0 (V13) | 0,759483 | 0,5088 |
| +0,01875 | 0,759248 | 0,5222 |
| +0,0375 | 0,759025 | 0,5579 |
| +0,075 | 0,758616 | 0,5931 |
| +0,15 | 0,757944 | 0,5622 |

À 30 balayages, le même pas `+0,15` donne le résultat inverse :

| Modèle | Distance L1 à 30 balayages |
|---|---:|
| V13 | 0,5167 |
| candidat rang 5 | 0,4370 |

Le gain est de `15,4 %`. Sept diagnostics sur dix se rapprochent de Bach,
notamment les blocs forts non triadiques (`36,60 %` → `36,34 %`), les
dissonances faibles (`0,864` → `0,912`, cible `0,962`) et les dissonances
fortes (`0,576` → `0,561`, cible `0,381`). Les mouvements chromatiques et la
basse hors gamme restent en revanche problématiques.

Le réajustement exact ne conserve pas ce gain :

| Modèle | Poids du nouveau facteur | Distance L1 à 30 balayages |
|---|---:|---:|
| V13 | 0 | 0,5167 |
| candidat rang 5 local | +0,15 | 0,4370 |
| candidat rang 5 réajusté | +0,5194 | 0,5653 |

Le candidat rang 5 est donc prometteur pour le régime long, mais seulement
dans une région de confiance étroite. Il n'est pas promu : il régresse à six
balayages et le refit exact non borné quitte la zone générativement utile.

## Filtre renforcé et échec du candidat rang 9

Une marge minimale de `5 %` d'amélioration générative projetée est ensuite
imposée. Un seul candidat subsiste :

```text
any_pair_arrival_abs_class_same_sign(all_voices)=10
proposed step = -0.15
minimum inter-seed cosine = 0.765
ensemble relative remaining = 0.946
```

Sa NLL exacte passe à `0,758016`, mais sa distance générative de développement
atteint `0,6044`. Il est rejeté.

## Localisation du désaccord à horizon court

Les deux pas locaux ont enfin été rejoués sur les 32 chorals de train exacts
qui avaient servi au Jacobien :

| Modèle | Distance L1 train |
|---|---:|
| V13 | 0,5208 |
| candidat rang 5 | 0,5257 |
| candidat rang 9 | 0,5627 |

À six balayages, l'échec existe donc déjà sur train. Il ne s'explique pas
principalement par un transfert train→validation. Le succès du rang 5 à 30
balayages montre en revanche que le problème porte sur l'horizon du gradient,
pas sur son signe en régime suffisamment long.

## Pourquoi la covariance dépend de l'horizon

Pour une distribution d'équilibre

```text
p_w(x) ∝ exp(w F(x))
```

on a bien :

```text
∂ E_p[g] / ∂w = Cov_p(g, F)
```

Mais le générateur réellement évalué utilise une distribution transitoire :

```text
q_w^T = q_initial K_w^T
```

après un nombre fini `T` de balayages Gibbs. Sa dérivée dépend de la dérivée de
chaque transition du noyau `K_w` le long de la trajectoire. Elle n'est égale à
la covariance d'équilibre que si les chaînes ont suffisamment mélangé et si
les moments sont effectivement mesurés sous la loi stationnaire.

V16 utilisait un burn-in court, puis plusieurs états persistants espacés de
deux balayages. Son covariance résume donc un régime plus tardif que l'audit
court. Le rang plein du Jacobien et la stabilité inter-graines ne garantissent
pas son transfert vers un autre horizon. L'audit à 30 balayages confirme en
revanche que cette approximation peut devenir utile quand la chaîne se
rapproche du régime qu'elle résume.

Ce résultat ne remet pas en cause le modèle exponentiel ni la
pseudo-vraisemblance. Il interdit seulement d'utiliser la covariance comme
gradient universel du générateur quel que soit son horizon.

## V17 : différences finies appariées

Le prochain garde-fou doit mesurer directement la procédure utilisée pour
générer :

1. conserver le top-K conditionnel exact ;
2. proposer pour chaque candidat le signe conditionnel et une grille
   dichotomique de petits pas ;
3. générer avec V13 puis avec `V13 + pas`, depuis les mêmes pièces, états
   initiaux et flux aléatoires appariés ;
4. mesurer directement la variation des dix diagnostics aux horizons 6 et 30 ;
5. répéter sur plusieurs graines et bootstrapper par pièce ;
6. n'admettre qu'un candidat améliorant la distance standardisée sur train aux
   deux horizons, sans régression stable des dissonances fortes ni des grands
   sauts de basse ;
7. réajuster exactement sous une région de confiance qui interdit de dépasser
   le pas effectivement validé — V16 montre qu'un optimum conditionnel à
   `+0,5194` peut être moins bon que le pas validé à `+0,15` ;
8. refaire l'audit de développement, puis seulement envisager une promotion.

Pour contenir le coût, le premier écran peut utiliser 8 pièces × 2 graines,
puis les trois meilleurs candidats 32 pièces × 3 graines. Les lattices, états
initiaux et résultats V13 doivent être mis en cache et partagés par tous les
candidats.

La covariance reste utile comme heuristique peu coûteuse pour ordonner les
candidats de régime long. Elle ne décide plus seule de leur admission.
