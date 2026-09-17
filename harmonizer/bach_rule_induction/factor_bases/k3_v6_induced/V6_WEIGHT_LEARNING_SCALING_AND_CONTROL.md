# V6 — mise à l'échelle et contrôle génératif des poids

## Question

Les 30 facteurs V6 ont été sélectionnés sur les choix authentiques de Bach,
puis leurs poids conditionnels ont été appris par pseudo-vraisemblance. Cette
expérience demande si la même structure courte suffit aussi à contrôler la
distribution jointe produite par Gibbs, sans ajouter de règle experte ni de
nouveau facteur.

Le test réservé reste fermé dans toutes les étapes ci-dessous.

## Mise à l'échelle du contraste de moments

La structure factorielle est gelée. Seuls les poids sont réajustés par

```text
gradient(f) = E_Bach[f] - E_Gibbs[f]
```

sur des chaînes persistantes du train.

| Train génératif | MAE initiale | Meilleure MAE | NLL conditionnelle validation |
|---:|---:|---:|---:|
| 16 chorals | 0,035206 | 0,013355 | 1,159607 |
| 64 chorals | 0,031623 | 0,013214 | 1,162405 |
| 248 chorals | 0,029411 | 0,012867 | 1,156809 |

Le corpus conditionnel contient 251 chorals de train. Trois pièces sont
exclues de la génération rythmique continue, car une pause interne n'est pas
encore représentable comme un segment SATB :

- `bach/bwv437` ;
- `bach/bwv227.7` ;
- `bach/bwv119.9`.

Les 248 autres pièces sont compatibles. Les entrées décalées simples sont
désormais acceptées et une tenue qui change de hauteur est rejetée
explicitement.

La mise à l'échelle améliore les moments appris, mais ne garantit pas seule
les mesures musicales externes. Sur 50 chorals de validation, V6-248 réduit
les répétitions de basse par rapport à V6-64, mais dégrade légèrement les
sonorités verticales. Davantage de données ne remplace donc pas le choix des
diagnostics.

## Jacobien des diagnostics

Pour une mesure générative `g` et un facteur `f`, la sensibilité locale est
estimée sur le train par l'identité exponentielle :

```text
∂ E[g] / ∂ poids(f) = Cov(g, nombre_d_activations(f))
```

Dix diagnostics explicites sont utilisés : trois mouvements de basse,
chromatisme global de la basse, blocs triadiques, blocs forts non triadiques,
dissonances faibles et fortes, et deux occurrences métriques de l'empreinte
`{0,3,6,8}`.

Le Jacobien standardisé a un rang `10/10`. Les 30 facteurs existants
contrôlent donc localement ces dix directions : aucune nouvelle feature n'est
justifiée par un défaut de rang. Une correction minimale en norme projette
les dix résidus avec une erreur relative de `0,000352`.

## Boucle itérative

La première projection, appliquée en une fois, améliore fortement les sorties
mais déplace un poids jusqu'à `0,727985`. Une seconde estimation est donc
effectuée autour des nouveaux poids, uniquement sur 64 chorals du train.

Le second Jacobien conserve un rang `10/10` et propose un déplacement maximal
de `0,558983`. Une région de confiance limite cette seconde correction :

- échelle effective : `0,268345` ;
- déplacement maximal d'un poids : `0,150000` ;
- NLL conditionnelle validation : `1,242368` → `1,241166` ;
- facteurs ajoutés ou retirés : `0`.

La boucle réalisée est ainsi :

```text
poids
  -> échantillonnage Gibbs persistant sur train
  -> moments + activations
  -> covariance/Jacobien
  -> direction minimale standardisée
  -> pas borné par région de confiance
  -> nouveaux poids
```

Les activations, l'estimateur statistique, l'optimiseur et le sampler restent
des composants séparés. Cette séparation est la partie réutilisable dans
d'autres domaines ; les dix diagnostics de ce POC restent spécifiques au
choral.

## Audits génératifs

Sur dix chorals de développement, trois graines et 30 sweeps, le modèle après
la seconde correction ne présente aucun écart stable parmi les dix mesures.
Les dissonances fortes valent `0,406` pour Bach et `0,406` pour le modèle.

Sur les 50 chorals de validation, trois graines et 6 sweeps :

| Mesure | Bach | V6 itération 2 | Écart stable |
|---|---:|---:|:---:|
| Demi-tons de basse | 25,67 % | 26,13 % | non |
| Répétitions de basse | 3,37 % | 4,42 % | oui |
| Sauts de basse > 4 | 26,76 % | 27,25 % | non |
| Basse hors gamme globale | 8,15 % | 9,68 % | non |
| Blocs triadiques | 52,74 % | 52,23 % | non |
| Blocs forts non triadiques | 28,72 % | 31,30 % | non |
| Dissonances par bloc faible | 0,987 | 0,893 | non |
| Dissonances par bloc fort | 0,410 | 0,449 | non |
| `{0,3,6,8}` fort | 2,17 % | 1,92 % | non |
| `{0,3,6,8}` faible | 2,93 % | 4,24 % | oui |

La première correction laissait cinq écarts stables sur ce même audit ; la
seconde n'en laisse que deux. À 30 sweeps sur le développement, même ces deux
écarts ne sont pas stables, ce qui montre que la profondeur de Gibbs doit
faire partie du contrat expérimental.

## Décision

La structure des 30 facteurs est suffisante pour contrôler localement les dix
diagnostics étudiés. Le problème actuel porte sur l'estimation et
l'optimisation des poids, pas sur un manque démontré de features.

V6 itération 2 devient le meilleur checkpoint génératif appris, mais pas une
base finale : deux faibles résidus subsistent sur l'audit large, la NLL
conditionnelle s'est dégradée par rapport au modèle conditionnel, et aucune
comparaison finale avec DeepBach n'a encore été exécutée. Aucune nouvelle
correction ne doit être choisie après inspection de cette validation. Une
prochaine itération doit être préenregistrée, utiliser une nouvelle tranche de
développement ou attendre l'évaluation finale scellée.

Une
[`suite d'écoute contrôlée`](listening_suite/README.md)
permet d'entendre Bach et les quatre checkpoints avec le même soprano, le même
rythme, la même graine et 30 sweeps.
