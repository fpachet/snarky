# V6 — bilan de la boucle factorielle

## Architecture exécutée

Snarky distingue maintenant trois objets :

- `RULE` et `CONSTRAINT` restent des déclarations expertes ;
- `FACTOR` est un prédicat booléen local, pur et sans action ;
- `LOG_WEIGHT` est un paramètre appris séparément.

Une activation de facteur n'entre jamais dans la mémoire de travail. Elle ne
peut donc ni déclencher une règle, ni un autre facteur, ni dépendre de l'ordre
d'évaluation. La couche d'inférence additionne les poids des activations,
normalise les scores des candidats et effectue le `CHOICE` ou le Gibbs.

## Induction conditionnelle

La grammaire `K3-V6-GRAMMAR-1` a été gelée avant l'exécution. Elle autorise
954 facteurs numériques locaux sur trois blocs, sans noms d'accords, règles
historiques, cartes CHORAL ou contraintes expertes.

La génération de colonnes a retenu 30 facteurs, tous au-delà du maximum absolu
de leur famille sous permutation. La NLL de validation passe de `2,422315` à
`1,048935`. Le test réservé de 51 chorals n'a pas été chargé.

## Diagnostic génératif

Les poids conditionnels ont d'abord produit des générations trop chromatiques
et trop dissonantes. Cela ne réfute pas la structure apprise : une
pseudo-vraisemblance locale et une distribution jointe Gibbs n'imposent pas les
mêmes moments.

La structure des 30 facteurs a donc été gelée, puis seuls les poids ont été
réajustés par le gradient :

```text
E_Bach[f] - E_Gibbs[f]
```

sur 16 chorals du train. Aucun facteur n'a été ajouté ou retiré. La MAE des
moments train passe de `0,035206` à `0,013355`.

Sur dix chorals de développement, trois graines par pièce :

| Mesure | Bach | V6 initial | V6 réajusté |
|---|---:|---:|---:|
| demi-tons de basse | 25,73 % | 39,41 % | 25,29 % |
| basse hors gamme globale | 10,08 % | 17,67 % | 9,31 % |
| blocs triadiques | 53,86 % | 46,41 % | 53,66 % |
| dissonances par bloc faible | 0,893 | 1,017 | 0,873 |
| dissonances par bloc fort | 0,406 | 0,663 | 0,530 |

Ce premier réajustement laissait deux résidus stables dans ce petit audit :
les répétitions attaquées de basse (`6,87 %` contre `3,11 %`) et les
dissonances sur bloc fort (`0,530` contre `0,406`).

## Mise à l'échelle et contrôle multivarié

Le contraste de moments a ensuite été porté à 64 puis aux 248 chorals de train
compatibles avec la grille rythmique continue. Trois chorals contenant des
pauses internes non représentées sont exclus explicitement. La meilleure MAE
des 30 moments atteint `0,012867` sur 248 pièces.

Un Jacobien train de dix diagnostics explicites par rapport aux 30 poids,
estimé par covariance, a un rang `10/10`. Cela indique que les défauts observés
sont localement contrôlables par les facteurs existants. Une première
projection multivariée, puis une seconde projection recalculée autour des
nouveaux poids et bornée à `0,15`, produisent le checkpoint
`v6_train64_multimetric_iteration2_model.json`.

Sur dix chorals de développement à 30 sweeps, aucun des dix écarts appariés
n'est stable. Sur les 50 chorals de validation à 6 sweeps, deux écarts faibles
restent stables : répétitions de basse (`4,42 %` contre `3,37 %`) et empreinte
`{0,3,6,8}` sur bloc faible (`4,24 %` contre `2,93 %`). Les huit autres
mesures, dont le chromatisme, les accords forts non triadiques et les
dissonances fortes, recouvrent Bach.

Le protocole et les résultats complets sont décrits dans
[`V6_WEIGHT_LEARNING_SCALING_AND_CONTROL.md`](V6_WEIGHT_LEARNING_SCALING_AND_CONTROL.md).

## Génération canonique

Un exemple sur `bach/bwv108.6` conserve le soprano, les attaques, tenues et
durées du choral source. Les 30 facteurs et leurs poids réajustés génèrent les
trois autres voix. Le MusicXML et le MIDI sont écrits par MuSES ; `music21`
ne sert qu'à importer la partition source et à produire une copie de contrôle
de sa mise en page.

## Décision scientifique

La nouvelle syntaxe factorielle est validée et la boucle complète est
exécutable. Le résultat confirme qu'il faut apprendre deux choses distinctes :

1. la structure courte des facteurs depuis les choix authentiques ;
2. leurs paramètres génératifs depuis les moments de la distribution jointe.

Le rang complet du Jacobien ne justifie pas encore de nouvelle clause. La
prochaine itération doit améliorer l'estimation des poids et le mélange des
chaînes sans être choisie après inspection répétée de la validation. Toute
extension de la grammaire doit être préenregistrée comme une nouvelle version.
Le test reste scellé.

## Itération 3 multigraine

Une troisième itération a ensuite vérifié cette hypothèse avec trois
estimations indépendantes sur 32 chorals × 2 chaînes. L'inversion brute du
Jacobien est instable : les cosinus entre corrections ne valent que `0,473`,
`0,199` et `0,468`. Un ridge sélectionné par un seuil de stabilité
préexplicite produit néanmoins un petit pas consensus, améliore la NLL
conditionnelle et réduit les dissonances fortes à 6 sweeps.

Le contrôle à 30 sweeps révèle toutefois que ce pas accentue un taux triadique
déjà excessif. L'itération 3 n'est donc pas promue ; l'itération 2 reste le
meilleur checkpoint génératif. Le résultat complet est consigné dans
[`V6_ITERATION3_MULTISEED_DECISION.md`](V6_ITERATION3_MULTISEED_DECISION.md).

Cette expérience invalide l'idée de poursuivre seulement les poids : le
contraste `triadique/non triadique` est trop grossier. La prochaine grammaire
doit distinguer les empreintes de sonorités, leur statut métrique, le mouvement
de basse et leur résolution dans le même noyau K3.
