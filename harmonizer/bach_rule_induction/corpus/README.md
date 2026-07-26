# Corpus

Ce dossier contiendra les manifestes et transformations reproductibles, jamais
une copie implicite ou non licenciée du corpus.

Chaque pièce devra enregistrer au minimum :

- identifiant stable et source ;
- empreinte du fichier source ;
- version de `music21` ou du fournisseur ;
- motif d'inclusion ou d'exclusion ;
- diagnostics SATB, rythme, silences, accords et orthographe ;
- transformations appliquées ;
- groupe de doublons ou variantes ;
- partition `train`, `validation` ou `test`.

Le partage est effectué par pièce avant transposition et fenêtrage. Les données
brutes et caches volumineux restent hors Git.

## Corpus DeepBach historique retrouvé

Le snapshot Keras original fixe `music21==3.1.0`.
[`build_music21_3_manifest.py`](build_music21_3_manifest.py) reproduit son
inventaire avec cette version exacte :

- 402 partitions XML/MXL retournées par `getBachChorales()` ;
- 357 partitions à quatre parties ;
- 354 sans notes simultanées dans une partie ;
- 352 avec les libellés explicites `Soprano/Alto/Tenor/Bass` ;
- 2 503 transpositions respectant les ambitus globaux.

Les deux derniers nombres reproduisent exactement ceux publiés dans l'article
DeepBach. Les deux partitions qui passent les filtres de code mais dont les
libellés sont abrégés sont `bwv140.7` et `bwv253`. Le critère sur les libellés
est donc une reconstruction opérationnelle de l'exclusion des « parties
instrumentales » décrite dans l'article, pas une condition visible dans le
snapshot de code.

Le manifeste versionné est
[`manifest.music21-3.1.0.json`](manifest.music21-3.1.0.json). Il contient les
352 inclusions, les 50 exclusions avec leur motif, les empreintes des fichiers,
les ambitus et le nombre de transpositions par pièce. Les partitions elles-mêmes
restent dans l'archive Music21 mise en cache hors Git.

Reconstruction depuis la racine Boojum, avec Python 3.9 :

```sh
python3.9 -m venv /tmp/deepbach-music21-3
/tmp/deepbach-music21-3/bin/python -m pip install \
  --no-build-isolation --no-deps \
  ../deepbach-reference/resources/cache/music21-3.1.0.tar.gz
/tmp/deepbach-music21-3/bin/python \
  harmonizer/bach_rule_induction/corpus/build_music21_3_manifest.py
```
