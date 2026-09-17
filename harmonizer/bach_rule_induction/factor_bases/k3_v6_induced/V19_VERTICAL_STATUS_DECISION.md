# V19 — décision sur les statuts verticaux lisibles

## Question

V18 comprime le choix local de Bach dans quatorze règles stables, mais ses
générations ne forment que `38,68 %` de blocs triadiques et produisent
`53,90 %` de blocs forts non triadiques, contre respectivement `50,87 %` et
`26,91 %` chez Bach. La question V19 est donc précise :

> une définition humaine simple du **statut triadique** suffit-elle à faire
> découvrir au corpus une règle verticale générale, stable et utile, sans
> régler les poids à partir des générations ?

## Extension de la grammaire

La grammaire
[`grammar_v19_vertical_status.yaml`](grammar_v19_vertical_status.yaml) étend
la grammaire métrique V10. Elle ajoute deux prédicats :

- bloc central formant une triade majeure ou mineure complète sur temps
  faible ;
- même statut sur temps fort.

Une triade complète est définie par les six ensembles relatifs à la basse
correspondant aux triades majeures et mineures et à leurs trois renversements.
Cette définition est écrite par l'expert et lisible. En revanche :

- aucun signe n'est imposé ;
- aucun poids n'est imposé ;
- aucune des deux clauses n'est forcée dans le modèle ;
- aucune métrique de génération n'intervient dans l'apprentissage ;
- aucune règle n'en active une autre ;
- les empreintes verticales observées opaques restent exclues.

Le corpus décide donc si le statut est utile, s'il doit être préféré ou évité,
et avec quelle intensité.

## Découverte sur 32 chorals

Le catalogue exact contient `1 052` facteurs, dont `914` restent admissibles
après exclusion des empreintes opaques. Sur `7 273` décisions de train et
`2 103` décisions de validation, la sélection à une erreur standard retient
20 règles.

Les deux statuts triadiques sont sélectionnés aux rangs 2 et 3 :

| Statut | Poids au moment de l'entrée |
|---|---:|
| triade complète, temps fort | `+1,887` |
| triade complète, temps faible | `+1,644` |

Le corpus apprend ainsi deux résultats simples : les triades complètes sont
préférées, et cette préférence est plus forte sur les temps forts.

## Stabilité de la structure

La découverte complète est répétée sur quatre partitions 24/8 des 32 chorals.
Le modèle 32/10 et les quatre replis sélectionnent respectivement
`[20, 24, 23, 26, 26]` règles. Le Jaccard moyen vaut `0,735`, contre `0,620`
pour V18.

Le noyau unanime contient 18 règles. Les deux statuts triadiques y figurent
5 fois sur 5, toujours avec un poids positif :

| Statut | Étendue des poids après réajustement de chaque base |
|---|---:|
| triade complète, temps fort | `[+1,268 ; +1,398]` |
| triade complète, temps faible | `[+0,805 ; +0,974]` |

Le résultat n'est donc pas propre à un découpage particulier.

## Réajustement complet

Les 18 prédicats unanimes sont gelés, puis seuls leurs poids et les profils
auxiliaires sont réappris sur 251 chorals. Les 50 chorals de validation servent
à l'arrêt ; les 51 chorals de test restent fermés.

| Modèle | NLL de validation |
|---|---:|
| profils auxiliaires sans règles | `2,406648` |
| noyau V18 | `0,981894` |
| noyau V19 | `0,887879` |

Sur le corpus complet, les poids triadiques valent `+1,457887` sur temps fort
et `+0,926829` sur temps faible.

Le programme
[`v19_unanimous_full.factors`](v19_unanimous_full.factors) et les 18
[RuleCards V19](../../rules/v19_unanimous/) sont exportés. La parité entre
l'évaluateur Python et les contributions `FACTOR` Snarky passe sur
128 décisions × 46 alternatives, avec une erreur maximale de
`8,882 × 10⁻¹⁶`.

## Audit génératif tenu à l'écart de l'apprentissage

V18 et V19 sont comparés sur les mêmes dix chorals de validation, trois graines
et trente balayages. Le soprano, le rythme, les blocs de bord et les flux
aléatoires sont contrôlés.

| Diagnostic | Bach | V18 | V19 |
|---|---:|---:|---:|
| blocs triadiques | `50,87 %` | `38,68 %` | `52,58 %` |
| blocs forts non triadiques | `26,91 %` | `53,90 %` | `32,44 %` |
| dissonances de paires / bloc fort | `0,357` | `0,765` | `0,533` |
| dissonances de paires / bloc faible | `1,032` | `1,104` | `0,936` |
| répétitions attaquées de basse | `3,71 %` | `5,32 %` | `4,27 %` |
| demi-tons mélodiques à la basse | `25,00 %` | `29,28 %` | `28,36 %` |
| basse hors gamme naturelle globale | `7,14 %` | `12,95 %` | `13,36 %` |

Par rapport à V18, V19 gagne `+13,90` points de blocs triadiques et retire
`−21,46` points de blocs forts non triadiques. Le progrès génératif est donc
une conséquence externe de l'ajout explicatif, et non la cible utilisée pour
ajuster ses poids.

## Décision

**V19 est retenu comme nouveau checkpoint explicatif appris, mais rejeté
comme générateur musical après écoute.** Il montre
qu'une notion musicale définie par l'expert peut rester déclarative tandis que
son importance, son signe et sa force sont appris du corpus. Il améliore à la
fois la pseudo-vraisemblance, la stabilité de la base et les générations.

Les métriques agrégées ne suffisent cependant pas à garantir la justesse
musicale. L'écoute de BWV 108.6 révèle de nombreuses fausses notes ; le
[diagnostic après écoute](V19_LISTENING_DIAGNOSIS.md) montre notamment que la
notion de triade ignore sa fondamentale et sa fonction. V19 sous-produit aussi
les accords de septième de dominante et son indicateur de basse hors gamme
naturelle globale reste trop élevé. La prochaine boucle ne doit pas retoucher
ses poids à partir de ces diagnostics. Elle doit :

1. calculer sur le **train seulement** les résidus conditionnels du modèle V19 ;
2. tester une petite grammaire de statuts lisibles d'accords de septième et de
   fonctions chromatiques de basse ;
3. refaire sélection, stabilité de structure et réajustement complet ;
4. ne rouvrir l'audit génératif qu'après gel du nouveau modèle.

Le test réservé reste fermé.
