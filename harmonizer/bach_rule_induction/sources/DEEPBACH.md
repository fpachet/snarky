# Audit de la source DeepBach

## Verdict

DeepBach est suffisamment accessible pour servir de baseline, être étudié et
être porté vers un environnement moderne. La copie locale contient :

- l'historique Git complet ;
- la branche PyTorch actuelle ;
- la branche Keras originale, plus proche du code de l'article ICML 2017 ;
- les tags `v1.0` et `v2.0` ;
- les quatre modèles PyTorch préentraînés ;
- le cache de dataset distribué par les auteurs.

Il n'est toutefois pas autonome au sens d'une expérience immédiatement
reproductible sur une machine actuelle. Les environnements datent de 2017–2019,
le corpus brut vient de `music21`, les ressources binaires ne contiennent pas de
manifeste des pièces et le découpage entraînement/validation/test du port
PyTorch est effectué sur des fenêtres augmentées plutôt que sur des identifiants
de chorals.

## Copie locale figée

| Élément | Valeur |
|---|---|
| Dépôt officiel | <https://github.com/Ghadjeres/DeepBach> |
| Projet local autonome | [`deepbach-reference/`](../../../../deepbach-reference/README.md) |
| Clone amont complet | `deepbach-reference/upstream/deepbach/` |
| Révision auditée | `6d75cb940f3aa53e02f9eade34d58e472e0c95d7` |
| Date de la révision | `2022-08-17T11:49:52+02:00` |
| Branche principale | `master` |
| Branche historique | `origin/original_keras` |
| Tags présents | `v1.0`, `v2.0` |
| Licence du code | MIT |
| Taille locale totale | environ 1,2 Gio |

Les révisions pertinentes sont également conservées, sans modification, dans
le projet frère
[`deepbach-reference/`](../../../../deepbach-reference/README.md). Le tag Keras
`v2.0` contemporain de l'article y est distingué de la tête Keras de 2018 et
du port PyTorch officiel ultérieur.

Le répertoire local est une copie de travail scientifique, pas une dépendance
vendue avec Snarky. Le code amont est sous licence MIT, mais l'archive de
modèles et de données ne contient pas de licence séparée ni de manifeste de
provenance suffisamment précis. Elle reste donc exclue des distributions et
des releases publiques tant que ce point n'est pas clarifié.

## Ressources téléchargées

L'archive référencée par `dl_dataset_and_models.sh` était encore accessible au
moment de l'audit. Elle a été conservée, vérifiée contre les traversées de
chemins, puis extraite sans exécuter ni désérialiser son contenu.

| Ressource | Octets | SHA-256 |
|---|---:|---|
| `deepbach_pytorch_resources.tar.gz` | 50 225 895 | `1baa60ed9e931cea0d1c30143bbf9af37cc66a536f226566fa80498c2b158ec3` |
| description sérialisée du dataset | 5 380 | `e81d46a43e2b42cdec1ffe49957fe344fa3ddb573c432a4631b204be9eeb87cb` |
| dataset tensoriel sérialisé | 1 002 667 375 | `fdf79cdfcd2a42a0709508b103b004c515cbe7e1428e55311c2e61dfad5be510` |
| modèle soprano, voix 0 | 8 919 356 | `fbb9b1c863a2322338cd5e2c4dcf9147f1b69568775d57ae4d0c356c55c0c9a2` |
| modèle alto, voix 1 | 8 926 552 | `a1060898b36e7d0bc6eb904ad73e6a75283dff5d4bfb0d3f2df9540598538b1d` |
| modèle ténor, voix 2 | 8 923 468 | `3249b550dfdb6fa88f0c2812923441fb1e9df423d1bd3685853c59c0070b945d` |
| modèle basse, voix 3 | 8 944 028 | `824c25dfa298dfc20c1e1658d7f67b977fa5067b843fbeb38f804e7ce628c750` |

Les noms exacts des fichiers sont produits par `repr()` et contiennent la
configuration du modèle :

```text
ChoraleDataset([0, 1, 2, 3], bach_chorales,
               ['fermata', 'tick', 'key'], 8, 4)
VoiceModel(..., voice_index, 20, 20, 2, 256, 0.5, 256)
```

## Degré d'autonomie

| Composant | Présent localement | Limite |
|---|---|---|
| Source et historique | oui | dernière révision de 2022 |
| Code de l'article, Keras | oui | Keras 2.0.2, TensorFlow 1.1, `music21` 3.1 |
| Port PyTorch | oui | Python 3.6.8, PyTorch 1.0, `music21` 5.5 |
| Poids PyTorch | oui | format ancien chargé par `torch.load` |
| Cache tensoriel | oui | sérialisé, sans identité des pièces |
| Partitions train/validation/test | non | calculées implicitement par indices |
| Partitions par choral | non | à reconstruire pour notre protocole |
| Partitions brutes MusicXML | non | fournies par le corpus de `music21` |
| Docker | recette présente | image CUDA 10 ancienne et téléchargements réseau |
| Plugin MuseScore | présent | déclaré obsolète par le dépôt |

## Ce que le code permet d'extraire

La copie suffit pour documenter précisément :

- l'encodage de chaque voix, des tenues, silences et symboles de bord ;
- les métadonnées `fermata`, position métrique, tonalité et numéro de voix ;
- les fenêtres de huit temps quantifiées en doubles croches ;
- l'augmentation par toutes les transpositions compatibles avec les
  tessitures observées ;
- les quatre modèles conditionnels, un par voix ;
- les contextes gauche, droit et simultané ;
- l'architecture des embeddings, LSTM et couches linéaires ;
- l'échantillonnage pseudo-Gibbs parallèle et son recuit ;
- les contraintes de voix et de région utilisées pour l'inpainting ;
- les différences entre la version Keras originale et le port PyTorch.

Cela couvre les informations nécessaires à l'audit architectural, au portage et
à la génération de contre-exemples. Cela ne couvre pas encore la reconstruction
certifiée de l'expérience publiée, car il manque un manifeste immuable des
partitions et des fichiers de partition originaux.

## Problèmes de reproductibilité identifiés

### Environnement ancien

`environment.yml` cible Linux, Python 3.6.8, PyTorch 1.0.0, CUDA 10,
NumPy 1.15.4 et `music21` 5.5.0. Il contient même le chemin personnel de
l'environnement Conda de l'auteur. La branche Keras utilise Python 3.6.1,
Keras 2.0.2, TensorFlow 1.1.0 et `music21` 3.1.0. Une installation directe sur
un macOS moderne ne doit pas être considérée comme fiable.

Le `Dockerfile` ne résout pas entièrement le problème : il part d'une image
CUDA ancienne, clone la branche courante au moment du build et télécharge les
ressources en direct. Il ne fige donc ni le code ni toutes les entrées.

### Corpus et filtrage

Le port PyTorch utilise `music21.corpus.chorales.Iterator`. Les partitions
MusicXML brutes ne sont pas incluses dans le dépôt ni dans l'archive de
ressources. Pour retrouver exactement le corpus, il faut conserver la version
de `music21`, énumérer ses identifiants et exporter les partitions avec leurs
empreintes.

Le filtre `is_valid` du port PyTorch vérifie uniquement que la partition
contient quatre parties. Le commentaire indiquant qu'il faudrait détecter les
accords n'est pas implémenté. Nous devons donc expliciter nos propres critères
d'inclusion au lieu de traiter le cache comme un corpus canonique.

### Fuite entre sous-ensembles

Le port PyTorch construit d'abord toutes les fenêtres et transpositions, puis
découpe séquentiellement le tenseur à 85 % / 10 % / 5 %. Il ne publie ni
identifiant de choral par exemple ni manifeste par pièce. Une frontière peut
donc séparer des fenêtres ou transpositions issues du même choral.

La branche Keras originale utilise un découpage 80 % / 20 % sur une liste où
les transpositions ont déjà été produites. Elle ne fournit pas non plus le
manifeste par œuvre exigé par notre protocole.

Pour la comparaison Snarky–DeepBach, le partage doit être refait par pièce avant
toute transposition ou fenêtrage, et les variantes d'un même choral doivent
rester dans le même sous-ensemble.

### Sérialisation

Les datasets et poids anciens sont lus avec `torch.load`. Ce mécanisme repose
historiquement sur une désérialisation de type pickle. Ces fichiers ne seront
chargés que dans un environnement isolé et après validation de leur provenance ;
l'audit initial se limite aux noms, tailles, empreintes et au code source.

## Décision pour la baseline `D0`

Conserver deux références distinctes :

1. `D0-legacy` : exécution isolée du tag Keras `v2.0`, puis de la tête Keras
   de 2018 si les poids distribués l'exigent, afin de vérifier que quelques
   sorties de référence peuvent être reproduites ;
2. `D0-modern` : port minimal vers un PyTorch maintenu, avec tests différentiels
   contre `D0-legacy`, corpus manifesté et partage par pièce.

La branche Keras reste la référence historique pour interpréter l'article. Le
port PyTorch et ses poids sont la voie la plus courte vers une baseline
exécutable, sous réserve de réussir le chargement contrôlé des artefacts.

### État d'exécution du 26 juillet 2026

Le projet frère
[`deepbach-reference/`](../../../../deepbach-reference/README.md) fournit
désormais une baseline Keras exécutable sur macOS ARM64 :

- reconstruction sous Keras 3 des architectures YAML Keras 2.0.2 ;
- chargement des quatre modèles avec vérification bit à bit de chaque tableau
  de poids HDF5 ;
- chargement restreint du dataset officiel de 1 696 chorals augmentés ;
- reprise du prétraitement, des métadonnées et du pseudo-Gibbs parallèle de la
  tête Keras 2018 ;
- génération canonique de 160 ticks et 19 968 mises à jour effectives ;
- reproductibilité exacte sur deux exécutions, tenseur
  `310dbdc70c3b855231ed9276bbdf3f35d52f8f0b8f46b45727dc046e78a183d2`.

Cette exécution est `D0-compat`, pas encore `D0-legacy` : TensorFlow 2.20 sur
ARM64 doit encore être comparé à TensorFlow 1.1 sur Linux/x86. Le correctif
numérique nécessaire pour les probabilités inférieures à `1e-7` est explicite
et documenté dans la couche de compatibilité.

## Prochaines actions

1. [x] exporter l'inventaire exact du corpus Keras `music21` 3.1.0 ;
2. [x] retrouver les 352 pièces et 2 503 transpositions de l'article ;
3. figer le partage par pièce du manifeste commun à Snarky et DeepBach ;
4. construire un environnement isolé capable de lire un modèle sans réseau ;
5. produire une génération déterministe de fumée avec graines et empreintes ;
6. porter l'inférence, puis comparer logits et échantillons sur des entrées
   fixes ;
7. ne réentraîner qu'après gel du corpus et du protocole commun.
