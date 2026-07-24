# Le singe et les bananes

Cette famille contient deux formulations complémentaires :

- [`simple`](simple/README.md), quatre transitions déterministes qui isolent
  les mutations `ADD`/`REMOVE` et la provenance ;
- [`neopus_mea`](neopus_mea/README.md), une reformulation à buts dynamiques
  pilotée par la stratégie de conflit MEA.

La seconde est le cas historique principal. Elle représente les buts comme des
faits, crée des sous-buts avec `FRESH` et traite le plus récent avant son parent.
Elle reprend ainsi la séparation décrite dans la thèse entre :

1. règles générant des sous-buts ;
2. règles satisfaisant un but par une action ;
3. règles satisfaisant un but sans modifier le monde.

L’héritage Smalltalk et les méta-règles NéOpus ne sont pas reproduits. Les
types sont des faits ordinaires et MEA est pour l’instant une stratégie Python
explicite du moteur.

Référence : [thèse, chapitre VII.1, p. 190 et suivantes](https://www.francoispachet.fr/wp-content/uploads/2021/01/pachet-92b.pdf#page=190).
