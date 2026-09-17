# V8 — décision sur la pseudo-vraisemblance conjointe

> **Rectificatif.** Cette expérience additionnait correctement tous les
> facteurs du noyau central, mais pas toutes les instances des noyaux voisins
> que le sampler recompte lorsqu'une attaque et sa tenue changent. Son résultat
> génératif est conservé comme diagnostic historique. La formulation corrigée
> et son nouvel audit se trouvent dans
> [V8_EXACT_JOINT_PSEUDOLIKELIHOOD_DECISION.md](V8_EXACT_JOINT_PSEUDOLIKELIHOOD_DECISION.md).

## Question

L'apprentissage séparé de résidus marginaux est remplacé par un modèle
log-linéaire conditionnel. Pour chaque choix authentique de Bach, les
contributions de tous les facteurs sont additionnées avant le softmax sur les
46 hauteurs candidates. Les 48 poids sont ensuite appris simultanément par
pseudo-vraisemblance régularisée.

Les 30 facteurs V6 fournissent seulement l'initialisation de l'optimiseur. Ils
ne sont pas gelés. Les 18 facteurs résiduels proviennent du diagnostic
multigraine sur train. Le test réservé reste fermé.

## Vérification de l'implémentation

Le gradient analytique est comparé par test aux différences finies. Il est
calculé à partir de la même matrice d'activations que le score des candidats :

\[
\nabla_j \mathcal L =
E_{P_\theta(c\mid contexte)}[f_j] - f_j(c_{\mathrm{Bach}})
\]

La probabilité utilisée dans cette espérance dépend de la somme des 48
contributions. L'apprentissage des poids est donc réellement conjoint.

## Résultat conditionnel

| Modèle | NLL train | NLL validation |
|---|---:|---:|
| V6 pseudo-vraisemblance, 30 facteurs | 1,043839 | 1,048935 |
| Iteration 2, poids calibrés pour Gibbs | — | 1,241166 |
| V8 conjointe, 48 facteurs | 0,996693 | **0,998314** |

Le gain tenu à part contre V6 est de `0,050621` nat par décision. Les courbes
train et validation restent proches. L'optimum de validation est atteint à
l'étape 60 sur 100.

Le changement de signe de certains facteurs par rapport à leur résidu
univarié confirme l'intérêt du modèle conjoint : une marginale positive ne
garantit pas un poids positif lorsque les autres facteurs expliquent déjà la
même information.

## Audit génératif apparié

Dix chorals de validation, trois graines et le même protocole sont comparés à
Iteration 2.

### Six sweeps

V8 est plus proche de Bach sur 3 diagnostics sur 10. Elle améliore notamment
le taux triadique et certains diagnostics de sonorité, mais surcorrige la
basse :

| Diagnostic | Bach | Iteration 2 | V8 |
|---|---:|---:|---:|
| Sauts de basse > 4 demi-tons | 27,87 % | 28,67 % | **10,03 %** |
| Demi-tons à la basse | 25,00 % | 25,03 % | **39,58 %** |
| Basse hors gamme naturelle globale | 7,14 % | 8,06 % | **16,06 %** |

Les trois écarts V8–Bach excluent zéro à 95 %.

### Trente sweeps

V8 est plus proche sur 4 diagnostics sur 10. Les métriques verticales sont
convaincantes :

- dissonances fortes par bloc : Bach `0,3566`, V8 `0,3592` ;
- taux triadique : Bach `50,87 %`, V8 `51,82 %` ;
- dissonances faibles par bloc : Bach `1,0323`, V8 `1,0415`.

Mais la basse dérive davantage :

- sauts > 4 : `7,04 %` ;
- demi-tons : `42,62 %` ;
- notes hors gamme naturelle globale : `15,40 %`.

## Interprétation

La pseudo-vraisemblance répond correctement à la question locale : retrouver
une note de Bach lorsque ses voisins authentiques sont connus. Dans une chaîne
de Gibbs, ces voisins sont eux-mêmes générés. Les facteurs mélodiques qui
rendent la vraie note facile à reconnaître localement peuvent alors créer une
distribution stationnaire trop concentrée sur les pas et les demi-tons.

Ce résultat ne remet pas en cause la pseudo-vraisemblance. Il valide la
séparation en deux étapes :

1. apprendre conjointement et efficacement les poids par
   pseudo-vraisemblance ;
2. calibrer ensuite la distribution globale avec les moments de générations
   longues, sans revenir à des ajustements facteur par facteur.

## Décision

**V8 n'est pas promue comme générateur.** Iteration 2 reste le checkpoint
génératif de référence.

V8 devient en revanche le meilleur modèle conditionnel et la nouvelle
initialisation de recherche. La prochaine expérience doit réajuster
conjointement ses 48 poids avec un objectif hybride :

\[
\mathcal L_{\mathrm{PL}}(\theta)
+ \lambda\,
\|M_{\mathrm{Gibbs}}(\theta)-M_{\mathrm{Bach}}\|^2
\]

La pseudo-vraisemblance préservera la prédiction locale ; le terme génératif
corrigera la basse et la distribution stationnaire.

## Exemple d'écoute

- [MP3 V8](../../../generated/v8_joint_pl_listening/v8_joint_pl_bwv108_6.mp3)
- [MusicXML MuSES](../../../generated/v8_joint_pl_listening/v8_joint_pl_bwv108_6.musicxml)
- [MIDI](../../../generated/v8_joint_pl_listening/v8_joint_pl_bwv108_6.mid)

L'exemple utilise BWV 108.6, son soprano et son rythme, la graine `5517` et
`30` sweeps. Il est expérimental et non promu.
