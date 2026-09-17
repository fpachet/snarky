# V5.12–V5.16 — boucle explicite sur la basse et les sonorités

## Point de départ

L'inspection de la génération V5.9 de `bach/bwv108.6` révélait une basse trop
chromatique et des sonorités étranges. L'ancien taux agrégé de classes rares
ne mesurait pas directement ces phénomènes.

Sur le même squelette rythmique :

| Mesure | Bach | V5.9 |
|---|---:|---:|
| mouvements attaqués de basse par demi-ton | 29,35 % | 43,48 % |
| attaques de basse hors gamme mineure naturelle globale | 15,05 % | 23,66 % |
| répétitions attaquées de basse | 0,00 % | 7,61 % |
| dissonances par bloc faible | 0,875 | 1,097 |

Le modèle contenait une préférence générale forte pour la classe mélodique 1
dans toute voix (`+1,4269`). Le prédicat était valable globalement mais trop
général pour la basse.

## Vocabulaire explicite ajouté

Toutes les nouvelles variables restent observables dans K3 :

- classe et taille du mouvement de basse ;
- directions de la basse dans les trois blocs ;
- sonorité relative à la basse, séparée par niveau métrique ;
- présence d'une classe d'intervalle verticale sur bloc fort ou faible ;
- transition entre la sonorité centrale et la suivante ;
- statut triadique couvrant les six renversements majeurs et mineurs.

Aucun état latent V5.11 n'est chargé. Les poids sont guidés par :

`g_r = E_Bach[f_r] - E_Gibbs[f_r]`.

## Résultat négatif V5.12

V5.12 sélectionnait principalement des gradients négatifs. Elle réduisait bien
les demi-tons, mais remplaçait les sonorités problématiques par trop d'accords
triadiques :

| 10 chorals de développement | Bach | V5.9 | V5.12 |
|---|---:|---:|---:|
| demi-tons de basse | 25,00 % | 34,92 % | 18,38 % |
| grands sauts de basse | 27,87 % | 18,04 % | 30,08 % |
| blocs triadiques | 50,87 % | 59,18 % | 66,63 % |
| blocs forts non triadiques | 26,91 % | 20,81 % | 9,02 % |

V5.12 est rejetée. Elle démontre qu'apprendre seulement des interdictions
produit une harmonie artificiellement consonante. V5.13 imposait donc un
budget symétrique de gradients positifs et négatifs, mais son audit à 20
balayages a révélé un défaut plus profond du moteur.

## Correction de l'énergie conjointe

Une sonorité verticale était exposée dans la conditionnelle de chaque voix qui
attaquait, ce qui est correct pour la pseudo-vraisemblance. Le générateur
additionnait ensuite cette même énergie une fois par attaque simultanée. Une
sonorité à quatre attaques pouvait donc recevoir quatre fois le poids appris.

Depuis V5.14 :

- une règle mélodique reste comptée pour la voix concernée ;
- une règle de sonorité ou de transition est comptée exactement une fois par
  bloc dans l'énergie conjointe ;
- l'équivalence entre calcul vectorisé et mondes scalaires est testée ;
- un test dédié vérifie qu'un potentiel de sonorité n'est pas quadruplé.

Les gradients V5.12–V5.13, estimés avec l'ancienne énergie, sont invalidés pour
la promotion générative. Les rapports restent conservés comme historique.

## V5.14, V5.15 et interpolation V5.16

V5.14 réinduit interdictions et licences avec l'énergie corrigée. Sur dix
chorals de développement, ses statistiques harmoniques deviennent proches de
Bach, mais la basse reste trop lisse :

| Mesure | Bach | V5.14 |
|---|---:|---:|
| demi-tons de basse | 25,00 % | 29,97 % |
| grands sauts > 4 demi-tons | 27,87 % | 15,52 % |
| blocs triadiques | 50,87 % | 54,12 % |
| dissonances par bloc fort | 0,357 | 0,357 |

V5.15 ne réajuste que quatre règles de basse. Elle surcorrige :

| Mesure | Bach | V5.15 |
|---|---:|---:|
| demi-tons de basse | 25,00 % | 18,38 % |
| grands sauts > 4 demi-tons | 27,87 % | 35,60 % |

V5.16 interpole à `0,5` les quatre deltas V5.15 sur le socle V5.14. Ce facteur
est choisi sur les dix premiers chorals de validation, puis gelé. Sa NLL
conditionnelle de validation vaut `1,153861`, entre V5.14 (`1,133933`) et la
surcorrection V5.15 (`1,184205`).

## Confirmation tenue à part

Les dix chorals suivants, jamais consultés pour le facteur d'interpolation,
donnent :

| Mesure | Bach | V5.16 | Écart apparié, IC95 |
|---|---:|---:|---:|
| demi-tons de basse | 25,73 % | 26,32 % | +0,59 pp [-3,75 ; +4,93] |
| répétitions de basse | 3,11 % | 4,61 % | +1,49 pp [-1,60 ; +4,59] |
| grands sauts > 4 demi-tons | 28,03 % | 24,35 % | -3,69 pp [-9,37 ; +2,00] |
| blocs triadiques | 53,86 % | 56,08 % | +2,22 pp [-2,57 ; +7,00] |
| blocs forts non triadiques | 28,20 % | 27,52 % | -0,68 pp [-8,71 ; +7,35] |
| dissonances par bloc fort | 0,406 | 0,362 | -0,044 [-0,175 ; +0,086] |

La seule différence stable de ce petit audit est la sonorité `{0,3,6,8}` sur
bloc faible : `5,77 %` contre `3,20 %`, écart `+2,57` points, IC95
`+1,15–+4,00`.

### Réplication sur trois graines

La même tranche de confirmation est ensuite générée avec trois graines. Les
graines sont moyennées par pièce avant le calcul apparié :

| Mesure | Bach | V5.16 | Écart apparié, IC95 |
|---|---:|---:|---:|
| demi-tons de basse | 25,73 % | 25,86 % | +0,12 pp [-3,76 ; +4,01] |
| répétitions de basse | 3,11 % | 5,06 % | +1,94 pp [-0,92 ; +4,80] |
| grands sauts > 4 demi-tons | 28,03 % | 24,94 % | -3,09 pp [-7,26 ; +1,07] |
| blocs triadiques | 53,86 % | 56,42 % | +2,56 pp [-0,41 ; +5,52] |
| blocs forts non triadiques | 28,20 % | 23,71 % | -4,50 pp [-11,85 ; +2,85] |
| `{0,3,6,8}` faible | 3,20 % | 4,24 % | +1,04 pp [-0,22 ; +2,30] |

Après réplication, aucun des dix résidus audités ne possède un IC95 excluant
zéro. La pénalisation supplémentaire de `{0,3,6,8}` faible n'est donc pas
justifiée. V5.16 reste gelée sans nouvelle règle.

## Retour sur BWV 108.6

À 20 balayages et avec la même graine :

| Mesure | Bach | V5.9 | V5.16 |
|---|---:|---:|---:|
| demi-tons de basse | 29,35 % | 43,48 % | 32,61 % |
| grands sauts > 4 demi-tons | 26,09 % | 6,52 % | 16,30 % |
| basse hors gamme naturelle | 15,05 % | 23,66 % | 15,05 % |
| blocs triadiques | 56,12 % | 52,04 % | 46,94 % |
| dissonances par bloc faible | 0,875 | 1,097 | 1,056 |

V5.16 améliore nettement le défaut signalé, sans le supprimer sur cette graine.
Les répétitions de basse restent trop nombreuses (`9,78 %` contre zéro), et la
sonorité `{0,3,6,8}` faible reste surproduite.

## Décision

V5.16 est le meilleur **candidat expérimental confirmé**, mais n'est pas encore
une base finale :

- l'énergie conjointe corrigée remplace définitivement l'ancien comptage ;
- V5.12, V5.13 et V5.15 ne sont pas promues ;
- le test scellé reste fermé ;
- la campagne à trois graines ne révèle aucun résidu stable à pénaliser ;
- la prochaine étape est l'export canonique des facteurs V5.16, puis leur
  compilation Snarky sans modifier le modèle probabiliste gelé.
