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

Deux résidus restent stables dans ce petit audit : les répétitions attaquées
de basse (`6,87 %` contre `3,11 %`) et les dissonances sur bloc fort
(`0,530` contre `0,406`). V6 n'est donc pas promue comme base finale.

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

La prochaine itération peut modifier les poids sur `train` et choisir un point
sur `validation`, mais elle ne doit pas inventer une nouvelle clause après
inspection de cet audit. Toute extension de la grammaire doit être
préenregistrée comme une nouvelle version. Le test reste scellé.
