# Baselines

Ce dossier accueillera les adaptateurs reproductibles des systèmes comparés :

- `S0` et `S1` pour Snarky ;
- `E0` pour la reconstruction de CHORAL ;
- `D0-legacy` et `D0-modern` pour DeepBach ;
- `H0` pour les combinaisons hybrides.

Les modèles externes restent dans `third_party/`. Un adaptateur doit enregistrer
révision, environnement, paramètres, graine, entrée, sortie et empreinte des
artefacts utilisés.

Le projet frère
[`deepbach-reference/`](../../../../deepbach-reference/README.md) fournit déjà
`D0-compat`, une exécution Keras 3 déterministe des poids Keras 2.0.2
historiques. Elle deviendra `D0-legacy` uniquement après comparaison avec
TensorFlow 1.1 sur Linux/x86.
