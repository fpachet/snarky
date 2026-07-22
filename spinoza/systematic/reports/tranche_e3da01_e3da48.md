# Tranche E3DA01–E3DA48 — définitions finales des affects

## Résultat

Les 48 définitions particulières et la définition générale des affects sont
désormais exécutables. La tranche contient :

- 49 manifestes dans `definitions/` ;
- 49 fichiers de règles textuelles dans `rules/definitions/` ;
- 49 fichiers de règles validées dans `rules/validated/` ;
- 101 cas exécutables : 51 reconnaissances positives et 50 frontières
  négatives ;
- une carte complète des dépendances canoniques dans
  `definitions/dependencies.yaml`.

Les règles validées restent interdites pendant le test de leur propre
définition. Une définition est donc reconnue depuis ses constituants
ontologiques explicites, et non depuis une étiquette déjà acquise.

## Organisation conceptuelle

| Bloc | Définitions | Distinctions principales |
|---|---|---|
| Affects primitifs et attention | E3DA01–E3DA05 | désir, passage de perfection, étonnement, mépris |
| Causes de joie et de tristesse | E3DA06–E3DA11 | cause extérieure ou accidentelle, amour, haine, dérision |
| Temporalité et incertitude | E3DA12–E3DA17 | doute, disparition du doute, passé inespéré |
| Affects sociaux | E3DA18–E3DA24 | similitude, bien ou mal d'autrui, évaluation affective |
| Considération de soi | E3DA25–E3DA31 | puissance, faiblesse, libre décret imaginé, louange, blâme |
| Désirs composés | E3DA32–E3DA43 | mémoire, imitation, réciprocité, danger, comparaison aux pairs |
| Désirs spécifiés par l'objet | E3DA44–E3DA48 | gloire, chère, boisson, richesses, union des corps |
| Définition générale | E3DA-GENERAL | idée confuse, variation corporelle, orientation de la pensée |

## Principes de formalisation

Les définitions sont des règles de classification. Contrairement à une
proposition, leur conclusion peut donc donner le nom de l'affect, mais
seulement lorsque toutes les conditions distinctives du texte sont présentes.
Aucune réciproque implicite n'est ajoutée.

Les distinctions suivantes sont protégées par des contre-cas :

- une perfection possédée statiquement n'est pas un passage de joie ou de
  tristesse ;
- une simple privation n'est pas une tristesse ;
- une cause intérieure n'est pas une cause extérieure ;
- une cause efficiente n'est pas automatiquement une cause accidentelle ;
- la sécurité et le désespoir exigent la disparition positive du doute ;
- croire une action libre, louée ou blâmée reste un contexte intentionnel ;
- la cruauté et la gourmandise conservent leurs alternatives textuelles ;
- ivrognerie et avarice exigent conjointement désir immodéré et amour ;
- l'idée adéquate ne satisfait pas la définition générale d'une passion.

La définition générale est décomposée en trois composantes indépendantes :

1. l'affect est une idée confuse dans l'âme ;
2. il affirme une force d'exister corporelle plus grande ou moindre
   qu'auparavant ;
3. sa présence détermine la pensée vers une chose plutôt qu'une autre.

## Relation aux propositions

`definitions/dependencies.yaml` relie chaque définition aux propositions ou
scolies qui fournissent son arrière-plan. Ce fichier est contrôlé par les
tests : ses 49 clés doivent être complètes et toute référence `E3Pxx` doit
correspondre à un manifeste propositionnel existant.

Cette relation est documentaire et ontologique. Les cas des définitions
instancient les constituants établis dans la couche propositionnelle, mais ne
rejouent pas à chaque fois toute la démonstration de la proposition citée.
Cela préserve des tests locaux lisibles et évite de confondre définition et
théorème.

## Moteur

Le moteur `ForwardEngine` n'a pas été modifié. Le lanceur de manifestes sait
seulement résoudre les identifiants `E3DA*` dans le nouveau répertoire
`definitions/`. Les alternatives du texte sont représentées par plusieurs
règles ordinaires ; aucune primitive de disjonction n'a été nécessaire.

## Portée de la couverture

La métrique 48/48 porte sur les énoncés définitionnels eux-mêmes, et 1/1 sur
la définition générale. Le corpus contient en outre 27 sections intitulées
« Explication ». Leur atomisation est comptée séparément afin de ne pas
modifier artificiellement la métrique canonique 48/48 ; elle est
maintenant documentée dans
[`tranche_e3da_explanations.md`](tranche_e3da_explanations.md).
