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

## Fragments exécutables : E3P01–E3P52

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

E3P23–E3P26 inversent explicitement les affects portant sur une chose haïe,
définissent l'envie, l'orgueil, la surestime et la mésestime, puis représentent
les efforts d'affirmer et de nier sans réduire leur contenu à un état
`EXISTANT` ou `INEXISTANT`. La comparaison avec SpinoLog et les audits de
clôture sont consignés dans
[`reports/tranche_e3p23_e3p26.md`](reports/tranche_e3p23_e3p26.md).

E3P27–E3P32 introduisent l'imitation affective, les conduites orientées par
la joie et la tristesse, l'approbation sociale, la considération de soi,
l'accord affectif et l'envie liée à une possession exclusive. La similitude
pertinente est construite depuis les corps de l'observateur et d'autrui ; une
simple ressemblance de trait ne suffit pas. L'absence préalable d'affect et
l'exclusivité d'un objet sont toujours des faits positifs. Les choix de
formalisation et la comparaison avec SpinoLog sont consignés dans
[`reports/tranche_e3p27_e3p32.md`](reports/tranche_e3p27_e3p32.md).

E3P33–E3P36 rendent exécutables la réciprocité amoureuse, la covariance entre
affection réciproque et gloire, les deux haines et l'envie constitutives de la
jalousie, puis le désir de retrouver un objet avec les circonstances de sa
jouissance passée. La comparaison directe avec Gondran et SpinoLog est publiée
dans
[`reports/tranche_e3p33_e3p36.md`](reports/tranche_e3p33_e3p36.md).

E3P37–E3P40 transmettent des ordres qualitatifs des affects aux désirs et de
l'amour passé à la haine, puis distinguent projet nuisible, effort, inhibition
et action accomplie. La peur d'un mal plus grand, la honte, la colère et la
vengeance deviennent exécutables. L'audit comparatif est publié dans
[`reports/tranche_e3p37_e3p40.md`](reports/tranche_e3p37_e3p40.md).

E3P41–E3P44 ferment cette séquence : amour réciproque, gloire, gratitude,
cruauté et ingratitude sont distingués, puis la haine réciproque est séparée
de la haine initiale. La victoire de l'amour résulte d'un ordre qualitatif
explicite entre deux efforts et devient une transition affective qui conserve
l'histoire de la haine. L'audit est publié dans
[`reports/tranche_e3p41_e3p44.md`](reports/tranche_e3p41_e3p44.md).

E3P45–E3P48 ouvrent la généralisation sociale. E3P45 conserve le triangle
amant–chose aimée–tiers sous imagination ; E3P46 exige un nom général et des
appartenances positives avant d'étendre amour ou haine. E3P47 rend explicite
une extension interprétative de E3P27 pour produire la tristesse mêlée à la
joie, et E3P48 distingue réattribution totale, causalité partagée et doute.
L'audit avec SpinoLog est publié dans
[`reports/tranche_e3p45_e3p48.md`](reports/tranche_e3p45_e3p48.md).

E3P49–E3P52 distinguent cause imaginée libre et cause imaginée nécessaire à
motif égal, puis font dépendre les présages d'une association affective
positive. La diversité des constitutions corporelles et celle d'un même homme
dans le temps deviennent des faits nommés. Enfin, l'attention prolongée à un
trait singulier exige une absence associative explicite et produit les
variantes textuelles de l'étonnement ou du mépris. L'audit est publié dans
[`reports/tranche_e3p49_e3p52.md`](reports/tranche_e3p49_e3p52.md).

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

E3P27 emploie une similitude corporelle contextualisée, mais ne prétend pas
encore définir une métrique générale de similitude. Dans E3P31, amour, désir et
haine restent des relations distinctes. Dans E3P32, l'absence du fait positif
`ne_peut_etre_possede_que_par_un` ne permet pas de conclure que l'objet est
partageable.

E3P33 utilise une compilation locale pour appliquer la définition de l'amour
à l'intérieur de `s_efforce_que`, sans conclure à un amour réel. E3P34–E3P35
conservent des ordres qualitatifs et non des intensités numériques. E3P36
réifie les circonstances comme une configuration finie explicitement fournie
par le manifeste.

E3P37–E3P38 restent qualitatifs. E3P39 exige un fait positif d'absence de
crainte avant de libérer l'effort nuisible ; E3P40 exige séparément similitude,
absence préalable d'affect et croyance de n'avoir donné aucune cause de haine.

E3P41 reconstruit l'amour réciproque par une joie imitée dans son cas ground,
mais sa règle publiée conserve les seules conditions de l'énoncé. E3P42 réifie
l'attente de réciprocité ; E3P43–E3P44 comparent des efforts et affects sans
addition numérique. L'extirpation n'efface jamais rétroactivement la haine et
le refus de l'auto-dommage dans le scolie de E3P44 reste une réfutation bornée.

E3P45 applique E3P40 sous `imagine` au moyen d'une compilation contextuelle.
E3P46 ne ferme pas extensionnellement les classes. E3P47 marque
`interpretative` la transmission de tristesse malgré une haine préalable,
car E3P27 exige littéralement une absence d'affect. E3P48 réifie destruction
et diminution de l'affection sans les convertir en statut `FAUX` ni en doute.
E3P49 reste ordinal et exige un motif égal explicite. E3P50 ne transforme pas
une simple chose en présage sans association d'espoir ou de crainte. E3P51
réifie les épisodes corporels et temporels sans les réduire à une identité
globale de la personne. E3P52 compare qualitativement des durées d'attention,
sans horloge numérique, et exige un fait positif d'absence d'alternative.
