# V20B — décision sur les statuts harmoniques identifiables

## Question

V20B corrige uniquement la dépendance linéaire de V20A. Il conserve le même
corpus, le même vocabulaire d'accords, le même budget de règles et le même
critère de sélection. La question est donc : les statuts harmoniques nommés
réapparaissent-ils sous une paramétrisation identifiable ?

## Réponse

Oui. Les cinq inductions complètes retiennent respectivement
`[19, 22, 26, 26, 23]` règles. Leur Jaccard moyen est `0,718` et quinze règles
sont présentes dans les cinq bases.

Quatre facteurs harmoniques lisibles sont unanimes et toujours positifs :

| Facteur | Étendue des poids |
|---|---:|
| triade majeure à l'état fondamental | `[+2,410 ; +2,929]` |
| triade mineure à l'état fondamental | `[+1,755 ; +2,163]` |
| accord complet au premier renversement | `[+1,073 ; +1,614]` |
| septième de dominante complète | `[+1,045 ; +1,401]` |

La septième majeure n'apparaît que dans deux bases sur cinq. Elle ne rejoint
pas le noyau.

## Résultat négatif important

Aucun facteur de degré de fondamentale relatif à la tonique n'est sélectionné
dans les cinq bases. Les facteurs statiques distinguent donc mieux un accord
complet plausible d'une sonorité quelconque, mais ne disent pas si le contexte
appelle `I`, `IV`, `V`, etc.

Ce manque explique pourquoi un réajustement complet et une nouvelle
génération seraient prématurés : ils amélioreraient vraisemblablement la
forme verticale globale sans résoudre le choix fonctionnel à l'origine des
« fausses notes » entendues.

## Décision

- V20B est **validé comme couche explicative de statut vertical**.
- V20B n'est **pas encore validé comme générateur**.
- Aucun nouveau bonus triadique ne sera essayé.
- Aucun bitset harmonique ancien ne sera réintroduit.
- Le test réservé reste fermé.

La seule étude suivante autorisée est un audit train-only des transitions
entre fondamentales **analysées**. Cette relation est comparée explicitement
aux transitions entre notes de basse de V13. Elle ne sera induite que si sa
couverture est suffisante et si les renversements lui donnent une information
substantiellement différente.
