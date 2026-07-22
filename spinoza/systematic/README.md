# Modèle systématique de l’Éthique III

Ce modèle repart des définitions, postulats et dépendances textuelles. Il ne
charge jamais la reconstruction historique de Gondran, conservée séparément
dans `spinoza/rules/historical.rules`.

L'objectif n'est pas de transformer immédiatement chaque proposition en une
règle qui contient déjà sa conclusion. Pour tester `E3Pxx`, le manifeste :

1. fournit une instanciation finie des hypothèses ontologiques ;
2. charge seulement les définitions, résultats externes et propositions
   antérieures déclarés dans `rule_files` ;
3. interdit toute règle `E3Pxx_as_direct_rule` ;
4. demande au moteur de dériver des faits représentant l'énoncé ;
5. conserve la chaîne minimale des règles effectivement employées.

## Premier fragment : E3P01–E3P03

Le fragment initial formalise :

- l'opposition cause adéquate / cause partielle ;
- l'opposition activité / passivité ;
- les idées adéquates et inadéquates comme causes d'effets ;
- l'indépendance causale des attributs pensée et étendue ;
- l'origine adéquate des actions et inadéquate des passions.

Les règles provenant des parties I et II sont isolées dans
`rules/external.rules`. Elles ne sont donc ni silencieuses ni confondues avec
des propositions déjà établies dans la partie III.

E1P36 affirme l'existence d'un effet sans le nommer. Comme Snarky ne possède
pas encore de création existentielle, chaque cas fournit un témoin `effet0` et
la règle externe dérive explicitement qu'il suit nécessairement de l'idée.

## Limites assumées

La quantification universelle est testée par instanciations ground. Dans E3P03,
« des seules idées » est représenté par les prédicats
`nait_seulement_d_idee_adequate` et `depend_seulement_d_idee_inadequate` ; cela
n'introduit aucune négation par défaut. Une formalisation ultérieure devra
préciser si l'exclusivité exige un raisonnement par contraintes ou une logique
plus expressive.
