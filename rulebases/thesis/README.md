# Bases reformulées depuis la thèse NéOpus

Ces exemples s'inspirent de *NéOpus : un système réflexif de règles de
production* (François Pachet, 1992). Ils ne prétendent pas reproduire le code
Smalltalk octet pour octet : ils rendent explicite l'intersection entre sa
sémantique et celle de Snarky.

| Base | Noyau actuel | Rôle principal | Source |
|---|---|---|---|
| [`equality_transitivity`](equality_transitivity/README.md) | complet | benchmark historique de jointures | [p. 114](https://www.francoispachet.fr/wp-content/uploads/2021/01/pachet-92b.pdf#page=114) |
| [`tomorrow_date`](tomorrow_date/README.md) | complet avec calendrier fourni | raisonnement humain par étapes | [p. 105](https://www.francoispachet.fr/wp-content/uploads/2021/01/pachet-92b.pdf#page=105) |
| [`petri_net`](petri_net/README.md) | réseau borné déterministe | mutations atomiques | [p. 110](https://www.francoispachet.fr/wp-content/uploads/2021/01/pachet-92b.pdf#page=110) |
| [`geometry`](geometry/README.md) | classification symbolique | taxonomie et explications | [p. 117](https://www.francoispachet.fr/wp-content/uploads/2021/01/pachet-92b.pdf#page=117) |
| [`monkey_bananas`](monkey_bananas/README.md) | version simple et reformulation à sous-buts MEA | planification et contrôle de conflit | [p. 190](https://www.francoispachet.fr/wp-content/uploads/2021/01/pachet-92b.pdf#page=190) |
| [`muses`](muses/README.md) | reconnaissance harmonique symbolique | séquences et regroupements | [p. 250](https://www.francoispachet.fr/wp-content/uploads/2021/01/pachet-92b.pdf#page=250) |
| [`four_queens`](four_queens/README.md) | validation d'une disposition | contraintes combinatoires | chapitre V.1.1 |
| [`hanoi`](hanoi/README.md) | instance à deux disques | contrôle récursif séquentiel | chapitre V.1.2 |

Chaque README indique les extensions qui seraient nécessaires pour passer du
noyau exécutable à une reproduction plus générale. Ces besoins sont synthétisés
dans [`../../docs/rulebase_feature_roadmap.md`](../../docs/rulebase_feature_roadmap.md).
