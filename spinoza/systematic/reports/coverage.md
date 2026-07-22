# Couverture du modèle systématique

| Proposition | Cas exécutables | Résultat | Dépendances non-III |
|---|---:|---|---|
| E3P01 | 2 | prouvée | E1P36, E2P11C |
| E3P02 | 1 | prouvée avec faits `FAUX` explicites | E2P06, E2P07 |
| E3P03 | 2 | prouvée avec règle de compilation | E3P01 |
| E3P04 | 2 | prouvée avec statuts `FAUX` explicites | — |
| E3P05 | 2 | prouvée par réfutation d'une cohabitation nommée | E3P04 |
| E3P06 | 2 | prouvée avec témoin explicite du conatus | E1P25C, E1P34, E3P04, E3P05 |
| E3P07 | 2 | prouvée comme identité ontologique explicite | E1P29, E1P36, E3P06 |
| E3P08 | 2 | prouvée par réfutation du temps fini | E3P04, E3P06 |
| E3P09 | 5 | prouvée avec scolie et contextes « en tant que » | E2P23, E3P03, E3P06–E3P08 |
| E3P10 | 2 | prouvée avec exclusion `FAUX` et contrariété | E2P09C, E2P11, E2P13, E3P05–E3P07 |
| E3P11 | 4 | quatre variations et scolie joie–tristesse prouvées | E2P07, E2P14, E3P09S |
| E3P12 | 2 | effort d'imaginer, sans présence réelle implicite | E2P17, E3P06, E3P11 |
| E3P13 | 3 | souvenir excluant, aversion, amour et haine | E2P17, E3P09, E3P11 |
| E3P14 | 2 | association mémorielle réactivant une affection | E2P16C2, E2P18 |
| E3P15 | 2 | causes accidentelles et corollaire exécutables | E3P11, E3P14 |
| E3P16 | 2 | ressemblance imaginée sans propriété réelle dérivée | E3P14, E3P15 |
| E3P17 | 3 | amour/haine simultanés et fluctuation | E3P13, E3P16 |
| E3P18 | 4 | passé/futur et deux scolies exécutables | E2P16C2, E2P17, E2P44S |
| E3P19 | 3 | conservation/destruction imaginées, joie et tristesse | E3P11, E3P13 |
| E3P20 | 2 | destruction de la chose haïe et frontière SpinoLog 20bis | E3P11, E3P13, E3P19 |
| E3P21 | 3 | affects partagés et ordre qualitatif d’intensité | E3P11, E3P13, E3P19 |
| E3P22 | 4 | causes extérieures, amour/haine et affects sociaux | E3P11, E3P13, E3P19, E3P21 |
| E3P23 | 3 | inversion des affects et ordre qualitatif d’intensité | E3P11, E3P13, E3P20, E3P21 |
| E3P24 | 4 | inversion envers la cause extérieure et envie | E3P13, E3P22, E3P23 |
| E3P25 | 3 | affirmation et négation contextualisées | E3P11, E3P13, E3P19, E3P21, E3P22 |
| E3P26 | 3 | affirmation/négation de la chose haïe et estimations | E3P22, E3P23 |

Couverture actuelle : 26 propositions sur 59. Toutes les propositions depuis
E3P04 possèdent au moins un contre-cas de non-dérivation. E3P09 et E3P11
exécutent aussi les principaux fragments ontologiques de leurs scolies :
volonté, appétit, désir, jugement de bonté, joie, tristesse et leurs variantes
corporelles. E3P12–E3P18 ajoutent imagination, aversion, association,
ressemblance, fluctuation et affects temporels. E3P19–E3P22 ajoutent les
affects portant sur la chose aimée, une intensité ordinale, les causes
extérieures et commisération, faveur et indignation. E3P23–E3P26 ajoutent
l'inversion affective envers la chose haïe, l'envie, les efforts contextualisés
d'affirmer ou de nier, l'orgueil, la surestime et la mésestime. La prochaine
frontière est E3P27, test central de la similitude.

L'ordre des tranches, leurs concepts et leurs critères de sortie sont décrits
dans [`roadmap.md`](roadmap.md).

Les résultats « prouvée » signifient ici qu'une instanciation ground de chaque
branche de l'énoncé atteint ses buts. Ils ne constituent pas encore une preuve
dans un calcul quantifié complet.

Pour E3P05 et E3P08, la réfutation n'est pas une négation par défaut : une
hypothèse réifiée est marquée `FAUX` seulement lorsque la proposition qu'elle
affirme a elle-même été dérivée avec le statut `FAUX`. Les règles réutilisables
publiées dans `rules/validated/` restent exclues de la preuve de leur propre
proposition.

E3P09 préserve l'idée sous laquelle l'âme persévère dans le terme dérivé ; le
contexte « en tant que » n'est donc pas effacé. Son contre-test causal établit
également que `juge_bon` ne permet jamais de reconstruire `s_efforce_vers`,
`veut`, `appete` ou `desire`.

E3P11 conserve quatre relations qualitatives distinctes pour augmenter,
diminuer, seconder et réduire la puissance. Les intensités et l'exclusion
formelle de tout quatrième affect primitif restent hors du fragment actuel.

Les contre-cas de E3P12, E3P16 et E3P18 vérifient directement la frontière
intentionnelle : imaginer un objet présent, imaginer qu'il possède un trait ou
affirmer son existence dans l'imagination ne produit respectivement ni
présence, ni trait, ni existence comme fait brut. E3P18 conserve la qualité de
l'affect à travers le temps, mais pas encore son intensité numérique.

E3P19–E3P22 conservent la même frontière : ni destruction, ni conservation,
ni action extérieure imaginée ne devient un fait brut. E3P21 transmet un ordre
qualitatif entre affects sources et affects de l'amant. Ses contre-tests
interdisent les conclusions annexes `QQCHOSE`, gloire et jalousie de SpinoLog ;
E3P20 n'importe pas sa proposition 20bis. Le rapport détaillé est
[`milestone_e3p19_e3p22.md`](milestone_e3p19_e3p22.md).

E3P23–E3P26 n'aplatissent pas davantage les contextes. En particulier,
`s_efforce_d_affirmer` et `s_efforce_de_nier` portent sur une proposition qui
conserve le contenu et sa cible ; aucun état brut `EXISTANT` ou `INEXISTANT`
n'est produit. La tranche et sa divergence avec SpinoLog sont détaillées dans
[`tranche_e3p23_e3p26.md`](tranche_e3p23_e3p26.md).
