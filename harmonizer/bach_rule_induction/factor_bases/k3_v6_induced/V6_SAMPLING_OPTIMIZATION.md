# V6 — optimisation de la boucle d'échantillonnage

## Goulet mesuré

Le temps de l'apprentissage des poids est dominé par Gibbs. Le calcul du
Jacobien, de la projection et du bootstrap est court en comparaison.

L'ancien moteur effectuait un appel au pool de processus pour le burn-in, puis
un nouvel appel pour chaque observation. Les partitions et états de chaînes
étaient donc sérialisés plusieurs fois.

Le mode `trajectory` envoie désormais chaque chaîne une seule fois à un
worker. Celui-ci réalise localement :

```text
burn-in
  → sweeps entre observations
  → diagnostics
  → activations des facteurs
  → état final
```

Seuls les statistiques suffisantes et l'état final reviennent au processus
principal.

## Parité

Benchmark de parité :

- 4 chorals de train ;
- 1 chaîne par pièce ;
- burn-in de 2 sweeps ;
- 3 observations espacées d'un sweep ;
- 2 workers ;
- graine `9917`.

Le mode `trajectory` et l'ancien mode `staged` produisent des objets JSON
strictement identiques pour :

- les diagnostics ;
- le Jacobien et ses valeurs singulières ;
- les intervalles bootstrap ;
- la correction proposée ;
- les sensibilités factorielles ;
- les résultats par pièce.

Les temps sont `17,381 s` pour `staged` et `17,347 s` pour `trajectory`.
Ce petit test confirme que les transferts interprocessus n'étaient pas le
principal goulet : le gain doit venir de la réduction du nombre de sweeps.

## Cache de chaînes persistantes

Les états finaux peuvent être sauvegardés dans un NPZ explicite :

```text
--final-chain-cache work/v6-chains.npz
```

L'itération suivante peut les restaurer :

```text
--initial-chain-cache work/v6-chains.npz
--warm-start-burn-in-sweeps 1
```

Le cache contient :

- un identifiant stable par pièce et réplique ;
- les blocs SATB finaux ;
- le domaine de hauteurs ;
- la graine ;
- le chemin du modèle source ;
- le hash SHA-256 du vecteur de poids.

À la lecture, le moteur vérifie le domaine, la forme de chaque grille, les
notes fixes, les frontières et la cohérence des tenues.

## Gain mesuré

Benchmark sur 8 chorals, 1 chaîne par pièce, 3 observations espacées d'un
sweep et 4 workers :

| Exécution | Burn-in | Temps |
|---|---:|---:|
| froide | 6 sweeps | 40,258 s |
| cache restauré | 1 sweep | 18,057 s |

Le gain est `×2,23`. Le cache compressé occupe `4,5 Ko`.

Ce gain ne doit pas être interprété comme une preuve qu'un seul sweep suffit
après n'importe quel changement. Il est justifié pour un modèle identique et
constitue une approximation contrôlée après un petit pas en région de
confiance. Une correction plus grande doit conserver davantage de burn-in et
faire l'objet d'un diagnostic de convergence.

## Deux profils de travail

### Boucle rapide

```text
8–16 chorals
1 chaîne par pièce
cache restauré
1 sweep de rééquilibrage
2–3 observations
```

Ce profil sert à vérifier une implémentation ou estimer une direction
exploratoire. Il ne décide pas d'une promotion.

Un cache local de ce type a été préparé pour le checkpoint itération 2 :

```text
experiments/v5_k3_clean/work/
  v6_iteration2_quick_chains_seed_10103.npz
```

Il contient 16 chaînes, occupe `8,6 Ko` et a demandé `47,377 s` à froid.
Il est volontairement placé dans `work/` et n'est pas versionné.

### Confirmation scientifique

```text
64 chorals ou plus
2 chaînes par pièce
plusieurs observations espacées
contrôle à 6 et 30 sweeps
audit multi-graines sur validation
```

Ce profil reste nécessaire pour une conclusion.

## Compilation de l'énergie candidate

Le sampler limite exactement le calcul au segment modifié et aux noyaux K3
qui l'intersectent. L'ancienne voie reconstruisait toutefois, pour chacune des
49 hauteurs candidates, un mini-`K3Dataset`, puis interprétait les 30
prédicats.

La nouvelle voie compile une décision locale en une seule évaluation :

```text
contexte K3 + vecteur de 49 candidates
  → vecteurs d'activation
  → énergie locale
```

Les composantes invariantes par rapport à la candidate — attaques, métrique,
tonalité, hauteurs des autres voix et parties inchangées du noyau — seront
construites une fois. Surtout, quand un monde contrefactuel possède déjà sa
hauteur choisie, les prédicats n'évaluent plus les 49 colonnes inutiles :
cela élimine un calcul quadratique candidate×candidate.

Sur BWV 108.6, avec 223 segments mutables et les 30 facteurs de l'itération 2 :

| Évaluateur | Temps médian par sweep |
|---|---:|
| voie initiale avant compilation | 2,009 s |
| voie compilée complète | 0,625 s |

Le gain mesuré est donc `×3,21`. La voie compilée et l'oracle historique
produisent les mêmes énergies et, à graine égale, exactement la même
trajectoire séquentielle. Une voie `legacy` reste disponible pour les tests de
parité.

## Arrêt adaptatif sur les moments du gradient

Un nombre fixe d'observations gaspille du calcul sur les chaînes déjà stables
et peut arrêter trop tôt les autres. L'option `--adaptive-sampling` considère
désormais `--samples` comme un minimum et `--max-samples` comme une borne.

La convergence ne porte pas seulement sur les deux diagnostics visibles. Elle
surveille le vecteur :

```text
diagnostics
+ activations factorielles
+ diagnostics × activations factorielles
```

Ces trois termes déterminent les moyennes et
`Cov(diagnostic, activation)`, donc le Jacobien utilisé par le gradient. Après
chaque observation, le moteur calcule :

- un ESS approché à partir de l'autocorrélation de retard 1 ;
- le quantile 95 % de la dérive standardisée entre deux fenêtres récentes.

La chaîne s'arrête lorsque le quantile 5 % des ESS dépasse la cible et que la
dérive passe sous le seuil. Un smoke test réel sur 2 chorals × 2 chaînes, avec
6 observations minimum et 12 maximum, donne :

| Politique | Observations min/moy/max | Temps |
|---|---:|---:|
| borne stricte, seuil volontairement impossible | 12/12/12 | 9,415 s |
| ESS ≥ 4 et dérive q95 ≤ 1,5 | 6/7,75/11 | 6,308 s |

Le gain de ce petit test est `33 %`. Il calibre le mécanisme ; il ne remplace
pas la confirmation multi-chaînes sur 64 chorals.

## Gibbs coloré exact

Chaque segment est associé aux centres de facteurs K3 que sa modification
peut affecter. Un coloriage glouton regroupe uniquement des segments dont ces
ensembles sont disjoints. Leurs lois conditionnelles sont alors indépendantes
et les choix peuvent être calculés sur le même état, puis appliqués ensemble,
sans changer la distribution cible.

Sur BWV 108.6, les 223 segments se répartissent en 9 couleurs, soit 24,8
segments par couleur en moyenne et 32 au maximum. En exécution NumPy
monoprocessus, le temps médian passe de 0,592 s à 0,579 s par sweep : le gain
immédiat est faible (`2,2 %`) et compatible avec du bruit de mesure. La valeur
principale du coloriage est double :

- plusieurs mises à jour exactes sont effectuées dans une même étape logique,
  ce qui peut améliorer le mélange ;
- les groupes constituent une frontière sûre pour une future évaluation
  réellement vectorisée ou parallèle.

Le mode reste donc optionnel ; le séquentiel demeure le défaut.

## Checkpoint comparatif intermédiaire

Les trois politiques ont été comparées à partir du même cache et des mêmes
poids sur 8 chorals × 2 chaînes, avec un sweep entre états, 8 workers et la
graine `10103`.

| Politique | États min/moy/max | Chaînes convergées | Temps | ESS q05 min |
|---|---:|---:|---:|---:|
| séquentiel fixe | 12/12/12 | n/a | 24,614 s | 3,423 |
| coloré fixe | 12/12/12 | n/a | 25,247 s | 2,137 |
| coloré adaptatif | 7/10,69/12 | 10/16 | 24,189 s | 2,137 |

Conclusions de ce checkpoint :

- le coloriage exact ne mérite pas encore de devenir le défaut : il n'améliore
  ni le temps total ni l'ESS minimal dans cette configuration ;
- l'arrêt adaptatif économise 21 états sur 192, mais six chaînes atteignent la
  borne, ce qui limite le gain mural à `4,2 %` par rapport au coloré fixe ;
- le gradient adaptatif reste proche du coloré fixe : cosinus des corrections
  `0,956`, RMSE des deltas `0,0314` et RMSE des coefficients du Jacobien
  `0,0171` ;
- cette proximité est encourageante, mais un seul checkpoint ne permet pas de
  déclarer les corrections interchangeables.

Par conséquent, la prochaine grande campagne doit utiliser la compilation
avec le sampler séquentiel. L'adaptatif peut servir à l'exploration et doit
publier le diagnostic de chaque chaîne ; le coloré demeure une voie de
recherche pour une véritable évaluation groupée.

## État avant transfert

Les optimisations propres à la boucle Bach sont donc en place :

1. trajectoires locales par worker et cache persistant ;
2. énergie candidate compilée, `×3,21` sur le cas de référence ;
3. convergence adaptative sur les moments effectivement utilisés par le
   gradient ;
4. coloriage exact des mises à jour indépendantes, conservé comme option
   expérimentale après un checkpoint négatif sur sa performance immédiate.

Le checkpoint mono-graine de taille intermédiaire est exécuté. Avant une
affirmation scientifique sur l'arrêt adaptatif, il reste à le répliquer sur
plusieurs graines et à vérifier la correction proposée par un audit génératif
tenu à part. Ce travail n'est pas nécessaire pour transférer la compilation,
le cache et les statistiques de convergence vers une infrastructure
générique : leurs contrats sont maintenant explicites et testés.
