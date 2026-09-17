# V20 — décision de couverture des statuts harmoniques

## Protocole

Avant toute induction, dix qualités nommées ont été définies :

- triades majeure, mineure, diminuée et augmentée ;
- septièmes de dominante, majeure, mineure, demi-diminuée, diminuée et
  mineure-majeure.

Pour chaque bloc, l'analyse calcule directement la fondamentale relative à la
tonique déclarée, la qualité et le renversement. Aucun état latent, modèle
externe ou annotation d'accord n'est utilisé. Une sonorité symétrique conserve
toutes ses analyses possibles.

L'audit porte uniquement sur les 251 chorals de train.

## Résultat

| Mesure | Valeur |
|---|---:|
| blocs verticaux | `24 452` |
| accord complet nommé | `78,21 %` |
| analyse unique | `76,77 %` |
| analyse ambiguë | `1,44 %` |
| accord complet nommé sur temps fort | `86,13 %` |
| accord complet nommé sur temps faible | `74,05 %` |
| triade plus une classe étrangère | `6,90 %` |
| accord nommé ou triade plus une étrangère | `85,11 %` |
| triades exactes | `14 058` |
| accords de septième exacts | `5 067` |

Les accords de septième ne sont pas marginaux. La septième de dominante seule
apparaît dans `2 243` blocs et les `251` chorals de train. Les septièmes
mineures (`1 214` blocs), majeures (`668`) et demi-diminuées (`641`) ont
également un support large.

## Décision

**La porte de couverture est franchie.** Le vocabulaire nommé couvre assez de
blocs pour être testé sans revenir aux empreintes arbitraires.

La première grammaire V20 restera volontairement factorisée. Elle autorisera
seulement :

- qualité ;
- degré de fondamentale ;
- renversement ;
- qualité × force métrique ;
- degré × force métrique ;
- degré × qualité ;
- qualité × renversement.

Elle n'ajoutera pas encore :

- une prime triadique globale, déjà testée ;
- les anciens bitsets verticaux ;
- les transitions de bitsets V7–V8 ;
- un état tonal latent ;
- une conjonction complète
  degré × qualité × renversement × métrique ;
- des transitions harmoniques.

Cette première étape permettra de savoir si l'identité verticale lisible entre
dans un petit noyau stable. Les transitions entre degrés ne seront ouvertes
que si un résidu conditionnel subsiste après ce test.

Le test réservé reste fermé.
