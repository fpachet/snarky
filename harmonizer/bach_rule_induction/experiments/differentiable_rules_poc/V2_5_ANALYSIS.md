# Analyse du POC V2.5 — ablation par groupe avec réajustement

## Question

Dans le V2.4, neutraliser un poids sans réentraîner le modèle montrait que
chaque colonne portait de l'information. Le V2.5 pose une question plus forte :
les autres règles et le socle peuvent-ils compenser un groupe retiré après
réajustement complet ?

Quatre modèles sont réentraînés depuis zéro, en retirant successivement :

- `melody` : grand saut et triton ;
- `overlap` : chevauchement adjacent ;
- `parallels` : octaves/unissons et quintes parallèles ;
- `direct` : mouvements directs vers octave et quinte.

Chaque expérience réestime les paramètres de nuisance et les règles restantes
dans les quatre voix. Le test final reste scellé.

## Résultat sur les chorals authentiques

La NLL de validation du catalogue complet V2.4 est `1,287062`.

| Groupe retiré | NLL validation réajustée | Pénalité |
|---|---:|---:|
| Parallèles | 1,338445 | +0,051384 |
| Mélodie | 1,295815 | +0,008753 |
| Overlap | 1,292481 | +0,005419 |
| Mouvements directs | 1,288059 | +0,000997 |

Toutes les pénalités restent positives après compensation. Le catalogue n'est
donc pas réductible à un seul de ces groupes.

## Comparaison au contrôle permuté

| Groupe | Pénalité authentique | Pénalité nulle | Excès authentique |
|---|---:|---:|---:|
| Parallèles | +0,051384 | -0,000007 | +0,051391 |
| Mélodie | +0,008753 | +0,005754 | +0,002999 |
| Overlap | +0,005419 | +0,000603 | +0,004816 |
| Mouvements directs | +0,000997 | +0,000002 | +0,000995 |

Les parallèles constituent le résultat le plus net : leur contribution
disparaît entièrement lorsque l'ordre des choix est détruit. L'overlap et les
mouvements directs ont également un excès presque intégralement authentique.

La mélodie conserve une pénalité importante dans le contrôle. Cela confirme
que les règles de grand saut et de triton résument simultanément :

1. une propriété de l'ordre mélodique authentique ;
2. une propriété du vocabulaire de hauteurs conservé par la permutation.

Le critère d'encoche locale du V2.2 reste donc nécessaire pour interpréter le
triton comme règle séquentielle, même si la colonne améliore la prédiction.

## Relation avec l'hypothèse de règles indépendantes

Le résultat soutient une version nuancée de l'hypothèse :

- les groupes sont locaux et aucun n'est entièrement absorbé par les autres ;
- leur importance est très inégale ;
- une règle peut être logiquement indépendante tout en n'apportant qu'un petit
  gain résiduel ;
- les règles mélodiques partagent de l'information avec les distributions
  tonales globales.

L'indépendance doit donc être évaluée à deux niveaux :

```text
indépendance logique de la clause
ET
contribution statistique conditionnelle après réajustement
```

## Ce qui est établi

1. Le groupe des parallèles possède une forte contribution propre, absente du
   contrôle.
2. L'overlap reste utile après réajustement des autres règles.
3. Les mouvements directs ne sont pas totalement redondants avec les
   parallèles, malgré leur faible gain.
4. Le groupe mélodique apporte un signal authentique mesurable, mais aussi un
   composant tonal visible dans le contrôle.
5. Un catalogue compact de règles locales peut être quantitativement
   décomposé sans ouvrir le test final.

## Limites

- Les quatre règles d'un groupe ne sont pas ablatées individuellement avec
  réajustement ; le V2.4 fournit seulement leur neutralisation individuelle.
- Les poids restent propres à chaque voix.
- Les paires simultanées ne sont pas encore dédupliquées.
- Les intervalles de confiance des pénalités réajustées ne sont pas encore
  estimés par bootstrap, car cela nécessiterait de nombreux réentraînements.

## Prochaine étape

Le niveau A est maintenant assez stable pour commencer les obligations
tonales. Le premier candidat sera la résolution de la sensible. Avant toute
induction, il faut définir et tester :

- la tonalité locale ;
- le degré de chaque note ;
- le statut `leading_tone` ;
- l'attaque suivante dans la même voix ;
- les statuts cadentiels susceptibles de créer des exceptions.

La recherche devra autoriser simultanément :

```text
SI contexte ALORS obligation
```

et :

```text
SI contexte ET exception_locale ALORS relâcher l'obligation
```
