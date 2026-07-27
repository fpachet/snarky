# Experiments

Une expérience devra être entièrement décrite par une configuration versionnée
et produire des résultats machine-readable.

Elle enregistrera notamment :

- manifeste et partition du corpus ;
- versions des systèmes et du catalogue de règles ;
- graines et nombre d'échantillons ;
- informations conditionnées à l'entrée ;
- critères d'exclusion préenregistrés ;
- sorties brutes, métriques et classification des désaccords.

Le jeu de test final reste fermé jusqu'au gel des features, règles et métriques
principales.

## Premier POC différentiable

[`differentiable_rules_poc/`](differentiable_rules_poc/) apprend des clauses
locales depuis les hauteurs du corpus historique. Le gradient de la
vraisemblance conditionnelle guide la recherche, puis une compression
symbolique propose des prédicats locaux réutilisables. Le premier résultat
retrouve notamment les patrons numériques correspondant aux quintes et octaves
parallèles, sans exposer ces noms pendant l'apprentissage.

Le second incrément ajoute une véritable génération de colonnes sur le résidu
du modèle courant. Il isole ensuite les classes numériques `0` et `7` dans la
famille des arrivées après saut en même direction. La comparaison postérieure
sur un domaine local fini classe les deux clauses comme équivalentes aux règles
Snarky de mouvement direct ; le contrôle mélangé ne les sélectionne pas. Un
audit postérieur regroupe les variantes exactes de soprano, produit un partage
canonique `251/50/51` sans fuite détectée et confirme le résultat par 1 000
bootstraps de pièces.

Le troisième incrément couvre les quatre voix et les paires adjacentes. Un
contraste local de taux distingue une classe ou une frontière singulière d'une
simple pente de rareté. Il récupère la classe mélodique `6` et le seuil
d'overlap `0`; le contrôle permuté ne sélectionne aucune des deux familles.

Le quatrième incrément recherche les parallèles dans les six paires SATB. Un
budget de deux règles sur les douze classes retient `0` et `7`, contre aucune
classe dans le contrôle nul. Les formules sont équivalentes aux deux règles
Snarky de référence sur 1 130 364 états valides par classe.

Le cinquième incrément ajuste conjointement les sept règles récupérées. Elles
améliorent la NLL de validation de `0,068188`, soit environ 10,8 fois le gain
du contrôle permuté. Une neutralisation à poids fixes attribue l'essentiel du
gain propre aux deux règles de parallèles.

Le sixième incrément réentraîne le modèle après retrait de chaque groupe.
Toutes les pénalités authentiques restent positives ; celle des parallèles
atteint `0,051384` et tombe à environ zéro dans le contrôle permuté.

Le septième incrément traite une obligation positive. Un scan aveugle des
douze classes relatives à la tonique retient seulement `11` pour la conclusion
« monter d'un demi-ton ». Les raffinements suivants énumèrent la voix, les
classes de basse source/cible, puis le mode. Ils isolent sept contextes
lisibles, dont des proxys de `vii°6→I`, `V4/2→I6`, `V→i`, `V→VI` et `V→III`.
Le contrôle permuté n'en retient aucun ; ces clauses restent candidates jusqu'à
la calibration familiale répétée.
