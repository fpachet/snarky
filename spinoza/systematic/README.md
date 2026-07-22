# Modèle systématique de l’Éthique III

Ce modèle repart des définitions, postulats et dépendances textuelles. Il ne
charge jamais la reconstruction historique de Gondran, conservée séparément
dans `spinoza/rules/historical.rules`.

Le texte français de référence est conservé dans
[`../sources/ethique_III_appuhn_1913.txt`](../sources/ethique_III_appuhn_1913.txt),
et le déroulement complet du travail est défini dans
[`reports/roadmap.md`](reports/roadmap.md).

L'objectif n'est pas de transformer immédiatement chaque proposition en une
règle qui contient déjà sa conclusion. Pour tester `E3Pxx`, le manifeste :

1. fournit une instanciation finie des hypothèses ontologiques ;
2. charge seulement les définitions, résultats externes et propositions
   antérieures déclarés dans `rule_files` ;
3. interdit toute règle `E3Pxx_as_direct_rule` ;
4. demande au moteur de dériver des faits représentant l'énoncé ;
5. conserve la chaîne minimale des règles effectivement employées.

## Fragments exécutables : E3P01–E3P11

Le fragment initial formalise :

- l'opposition cause adéquate / cause partielle ;
- l'opposition activité / passivité ;
- les idées adéquates et inadéquates comme causes d'effets ;
- l'indépendance causale des attributs pensée et étendue ;
- l'origine adéquate des actions et inadéquate des passions.

Les règles provenant des parties I et II sont isolées dans
`rules/external.rules`. Elles ne sont donc ni silencieuses ni confondues avec
des propositions déjà établies dans la partie III.

E3P04–E3P08 ajoutent :

- l'impossibilité explicite d'une destruction interne ;
- la contrariété de choses capables de se détruire ;
- le conatus comme expression de puissance et effort de persévérance ;
- son identité ontologique avec l'essence actuelle ;
- sa durée indéfinie, obtenue par réfutation d'un temps fini.

Chaque proposition de ce bloc possède un contre-cas `must_not_derive`. Celui-ci
vérifie qu'une conclusion ne suit pas quand une prémisse décisive manque, sans
produire pour autant un fait `FAUX`. Après validation, la règle résumant une
proposition est publiée dans `rules/validated/` et ne peut servir qu'aux
propositions suivantes.

Les étapes propres à une démonstration se trouvent séparément dans
`rules/proofs/E3Pxx.rules`. Un manifeste du bloc conatus charge exactement son
fichier de preuve courant et, si nécessaire, des fichiers `validated/E3Pyy`
avec `yy < xx` ; il ne voit donc aucune démonstration future.

E3P09–E3P11 prolongent ce socle avec la conscience du conatus, la volonté,
l'appétit et le désir, puis avec les quatre variations qualitatives de
puissance. Les scolies sont exécutables : le modèle distingue joie, tristesse,
chatouillement, gaieté, douleur et mélancolie, et marque positivement désir,
joie et tristesse comme affects primitifs.

Le sens causal du scolie de E3P09 est protégé par un contre-cas : le fait de
juger un objet bon ne suffit jamais à dériver que l'homme s'efforce vers lui,
le veut, l'appète ou le désire. De même, `persevere_en_tant_qu_elle_a` conserve
l'idée adéquate ou inadéquate comme argument au lieu d'effacer ce contexte.

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

Dans E3P05 et E3P08, la preuve par l'absurde est locale et réifiée : une
hypothèse est un terme du modèle, et sa réfutation exige un fait `FAUX`
explicite. Il ne s'agit pas encore d'un mécanisme général de raisonnement par
contradiction. L'identité de E3P07 est également ontologique
(`est_identique_ontologiquement_a`) et non une fusion syntaxique des termes.

Les variations de puissance de E3P11 sont encore qualitatives. Le modèle ne
compare pas leur intensité et n'interprète pas l'absence d'un quatrième affect
primitif comme sa fausseté ; ces deux propriétés demanderont respectivement
une extension quantitative et une fermeture déclarée du domaine.
