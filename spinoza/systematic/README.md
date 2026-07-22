# Modèle systématique de l’Éthique III

Ce modèle repart des définitions, postulats et dépendances textuelles. Il ne
charge jamais la reconstruction historique de Gondran, conservée séparément
dans `spinoza/rules/historical.rules`.

Le texte français de référence est conservé dans
[`../sources/ethique_III_appuhn_1913.txt`](../sources/ethique_III_appuhn_1913.txt),
et le déroulement complet du travail est défini dans
[`reports/roadmap.md`](reports/roadmap.md).

Le rapport historique complet de Cavarretta et les enrichissements qu'il
suggère sont analysés séparément dans
[`../reports/spinolog_1988_enrichment.md`](../reports/spinolog_1988_enrichment.md).

L'objectif n'est pas de transformer immédiatement chaque proposition en une
règle qui contient déjà sa conclusion. Pour tester `E3Pxx`, le manifeste :

1. fournit une instanciation finie des hypothèses ontologiques ;
2. charge seulement les définitions, résultats externes et propositions
   antérieures déclarés dans `rule_files` ;
3. interdit toute règle `E3Pxx_as_direct_rule` ;
4. demande au moteur de dériver des faits représentant l'énoncé ;
5. conserve la chaîne minimale des règles effectivement employées.

## Fragments exécutables : E3P01–E3P22

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

E3P12–E3P18 construisent une couche intentionnelle explicite. `imagine`,
`se_souvient_de`, `imagine_sous_temps` et `affirme_dans_imagination` gardent
leurs contenus comme arguments, y compris lorsqu'il s'agit de propositions
imbriquées. Les tests vérifient notamment que :

- considérer imaginativement un objet comme présent ne le rend pas présent ;
- imaginer qu'une chose possède un trait ne lui attribue pas réellement ce
  trait ;
- affirmer une existence dans l'imagination ne produit pas un fait brut
  d'existence.

Cette tranche rend également exécutables les causes accidentelles, sympathie
et antipathie, la coexistence d'amour et de haine, la fluctuation de l'âme et
les six affects temporels définis dans le scolie de E3P18.

E3P19–E3P22 forment le premier jalon comparatif avec Gondran et Cavarretta. Le
modèle distingue la conservation ou la destruction imaginée des faits réels,
reconstruit la joie et la tristesse partagées, transmet un ordre qualitatif
d'intensité dans E3P21 et rattache explicitement l'affect de E3P22 à l'idée de
sa cause extérieure. Le scolie de E3P22 ajoute commisération, faveur et
indignation. Les chaînes, clôtures et divergences avec SpinoLog sont détaillées
dans
[`reports/milestone_e3p19_e3p22.md`](reports/milestone_e3p19_e3p22.md).

Le lanceur expose pour chaque cas le nombre de faits initiaux et dérivés, le
nombre de dérivations et toutes les règles activées. Ces données permettent un
audit en lecture seule de la clôture sans modifier le moteur d'inférence.

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

Les variations de puissance de E3P11 restent qualitatives et l'absence d'un
quatrième affect primitif n'est pas interprétée comme sa fausseté. E3P21
compare désormais l'ordre de deux intensités affectives, sans coefficient ni
calcul numérique. Une métrique quantitative demanderait encore une extension
distincte ; la fermeture du domaine des affects primitifs reste également à
formaliser.

E3P18 établit l'identité qualitative de l'affect à travers les images passée,
présente et future. Il ne prouve pas encore une égalité numérique d'intensité,
qui dépendra de la future extension quantitative du moteur ou de l'ontologie.
