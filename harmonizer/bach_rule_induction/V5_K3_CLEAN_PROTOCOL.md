# Protocole V5 — induction clean-room sur noyau K3

## Hypothèse structurelle unique

Toute règle utilisée pour choisir une note doit être exprimable sur :

```text
K3(v,t) = bloc précédent
        + bloc central avec la note (v,t) masquée
        + bloc suivant
        + statuts locaux explicitement déclarés
```

Un bloc vertical contient les quatre hauteurs entendues et quatre indicateurs
attaque/tenue. Les blocs sont les états successifs créés par une attaque dans
au moins une voix. Cette définition évite qu'une tenue répétée soit confondue
avec une nouvelle attaque.

La localité K3 est une hypothèse falsifiable. Aucun rayon supérieur n'est
autorisé dans V5. Si des résidus stables demeurent, une expérience ultérieure
comparera `K1`, `K3` et `K5` sans modifier rétroactivement V5.

## Zéro connaissance harmonique initiale

La base `S-K3-LEARNED` commence sans règle et sans poids V1–V4. Sont autorisés :

- identité et ordre des quatre voix ;
- hauteur MIDI, classe modulo 12, différence, valeur absolue, signe et ordre ;
- positions précédente, centrale et suivante ;
- attaque ou tenue ;
- un domaine commun de hauteurs dérivé du seul `train`.

Les ambitus par voix ne sont pas fournis. Une distribution catégorielle de
registre par voix est estimée sur `train` à partir de poids nuls ; elle fait
partie du modèle publié, mais n'est pas interprétée comme règle harmonique.

## Décisions et alternatives

Pour chaque attaque authentique de la voix `v` au bloc central :

1. conserver les deux blocs voisins de Bach ;
2. masquer la hauteur centrale de `v` ;
3. la remplacer par chaque hauteur du domaine commun ;
4. propager cette hauteur dans le bloc suivant lorsque celui-ci contient une
   tenue de la même note ;
5. comparer le choix de Bach à toutes ces alternatives.

Le partage est effectué par choral avant la création des fenêtres. `train` et
`validation` utilisent le partage groupé de variantes existant. Les 51 chorals
de l'ancien test restent fermés.

## Langage de recherche

Le catalogue est généré mécaniquement à partir d'opérations numériques :

- classe et amplitude du mouvement vers le bloc précédent ou suivant ;
- classe verticale et ordre entre toute paire de voix ;
- conservation d'une classe entre deux blocs ;
- arrivée sur une classe après mouvements de même signe ;
- forme directionnelle sur trois blocs.

Les prédicats invariants par voix et symétriques entre bloc précédent et bloc
suivant sont évalués avant leurs spécialisations. Une spécialisation ne peut
donc entrer que si elle explique un résidu que la loi générale laisse encore.

Les libellés sont numériques et ne contiennent pas les termes « parallèle »,
« direct », « overlap » ou « sensible ». Ces noms ne sont appliqués qu'après le
gel d'un résultat, pendant le benchmark externe.

Chaque colonne est une règle locale indépendante. À chaque itération :

1. calcul des probabilités du modèle courant ;
2. calcul du gradient observé moins attendu de chaque colonne restante ;
3. sélection de la meilleure colonne sous pénalité descriptive ;
4. réajustement conjoint des poids par gradient et pénalité L1 ;
5. mesure sur `validation` et contrôle de stabilité par pièce.

Un gradient négatif propose un évitement ; un gradient positif propose une
préférence. Une règle ne devient dure qu'après une expérience spécifique sur
les opportunités, les exceptions et les intervalles de confiance.

## Génération cohérente

Le générateur V5 est un échantillonneur Gibbs :

```text
partition courante
→ choisir une cellule centrale non fixée
→ construire son K3
→ scorer toutes les hauteurs avec le modèle appris
→ tirer une nouvelle hauteur
→ répéter
```

Le POC initial travaille sur une grille dense de blocs, donc une attaque par
voix et par bloc. Le passage aux rythmes originaux devra propager une hauteur
sur ses blocs de tenue et sommer toutes les énergies locales affectées.

## Barrières scientifiques

- aucune importation des manifestes `S-LEARNED` ou `S-HISTORICAL` ;
- aucune ouverture adaptative de l'ancien test ;
- sélection sur `train`, arrêt et coude sur `validation` ;
- contrôles mélangés et bootstrap groupé avant promotion ;
- comparaison aux règles connues uniquement après gel ;
- publication des règles non récupérées et des résultats négatifs.

## Critères du premier jalon

- extraction déterministe de fenêtres K3 ;
- domaine commun calculé sur `train` seulement ;
- induction depuis une liste de règles vide ;
- poids positifs et négatifs possibles ;
- génération Gibbs utilisant exactement le même évaluateur K3 ;
- artefact machine-readable et rapport humain ;
- test garantissant l'absence de dépendance aux bases antérieures.
