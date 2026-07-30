# V13 — décision sur les contextes dirigés et métriques

## Origine

L'audit V12.3 sur train localise deux incompatibilités que les facteurs
globaux ne peuvent pas résoudre :

- sur temps fort, V12.2 surproduit les dissonances soprano–basse de `+6,24`
  points et soprano–ténor de `+5,60`, mais sous-produit soprano–alto de `−6,10` ;
- les licences de passage sont beaucoup trop fréquentes sur temps fort,
  jusqu'à `+27,10` points selon la paire ;
- à la basse, les demi-tons faibles sont surproduits de `+11,25` points et les
  grands sauts faibles de `+4,19`, tandis que les grands sauts forts sont
  sous-produits de `−11,14`.

Une pénalité globale ne peut pas corriger des écarts de signes opposés.

## Grammaire V13

La grammaire gelée ajoute 610 candidats neutres au catalogue V10 :

- 288 classes d'intervalle par paire dirigée et force métrique ;
- 24 licences de passage par classe d'intervalle et force métrique ;
- 10 seuils de mouvement de basse par force métrique ;
- 288 transitions de basse relatives à la tonique par force métrique.

Aucune cellule observée dans le diagnostic n'est copiée. Toutes les classes,
paires et transitions sont engendrées ; l'induction choisit leurs signes et
leurs poids.

## Induction

Le catalogue exact contient `1660` candidats. Trente facteurs sont réinduits
depuis zéro :

- NLL validation V10 : `0,757960` ;
- NLL validation V13 : `0,759483` ;
- test réservé chargé : `false`.

Le corpus remplace bien les licences V10 générales par :

- classe 9 × passage × temps faible, poids `+0,929315` ;
- classe 10 × passage × temps faible, poids `+1,466944`.

Il sélectionne aussi au rang 22 une préférence dirigée
`soprano–alto × classe 1 × temps fort`, poids `+1,458502`. Cette clause est
plus précise qu'une licence globale, mais elle ne dit toujours pas si la
dissonance est préparée, tenue ou résolue.

## Audit génératif

Sur 20 chorals de développement, trois graines et 6 sweeps :

| Mesure | Bach | V10 | V13 |
|---|---:|---:|---:|
| Demi-tons à la basse | 25,37 % | 28,29 % | 26,51 % |
| Grands sauts de basse | 27,95 % | 31,39 % | 29,63 % |
| Basse hors gamme | 8,61 % | 12,40 % | 12,91 % |
| Dissonances par bloc faible | 0,962 | 0,866 | 0,906 |
| Dissonances par bloc fort | 0,381 | 0,587 | 0,600 |
| Blocs forts non triadiques | 27,56 % | 39,04 % | 40,16 % |
| `{0,3,6,8}` fort | 1,60 % | 1,79 % | 3,26 % |

V13 corrige donc une partie du mouvement de basse et des dissonances faibles,
mais aggrave les erreurs harmoniques structurelles sur temps fort.

## Décision

V13 n'est pas promu et la validation complète n'est pas ouverte pour ce
candidat. `Iteration2` reste le modèle génératif de référence.

L'expérience confirme néanmoins une règle de méthode :

> les dimensions pertinentes ne doivent pas seulement exister séparément ;
> leur conjonction locale doit être disponible comme facteur candidat.

V14 devra rendre exprimables, sans pré-étiquetage musicologique :

- paire dirigée × classe d'intervalle × métrique × résolution par pas ;
- paire dirigée × classe d'intervalle × métrique × passage ou broderie ;
- paire dirigée × classe d'intervalle × métrique × autre voix tenue ;
- empreinte verticale × métrique × trajectoire de résolution ;
- mouvement de basse × degré relatif × métrique.

Le budget ou l'objectif de sélection devra aussi permettre aux facteurs de
basse d'entrer avant que les 30 places soient consommées par les empreintes
verticales.
