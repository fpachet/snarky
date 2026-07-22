# Atlas statique de l’Éthique III

Ce répertoire est le document racine publié sur GitHub Pages. Il ne dépend
d'aucun serveur d'application : `index.html`, `styles.css`, `app.js` et
`data/model.json` suffisent.

Le fichier `data/model.json` est généré depuis le corpus, les manifestes et les
preuves exécutées. Il contient aussi les 27 explications atomisées, le catalogue
complet des 652 règles, leur code Snark, leur provenance, leurs activations et
le graphe producteur–consommateur de 745 prédicats :

```sh
.venv/bin/python scripts/build_spinoza_site.py
```

Pour prévisualiser le site localement depuis la racine du dépôt :

```sh
python3 -m http.server 8000 --directory site
```

Puis ouvrir <http://localhost:8000/>. Les chemins relatifs rendent la même
version compatible avec `https://fpachet.github.io/snarky/`.

Le workflow `.github/workflows/pages.yml` régénère les données et publie le
répertoire lors de chaque modification pertinente de `main`. Dans les
paramètres GitHub du dépôt, la source de Pages doit être réglée sur
**GitHub Actions**.
