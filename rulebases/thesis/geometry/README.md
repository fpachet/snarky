# Classification géométrique

Cette base construit d'abord deux diagonales dotées d'identifiants frais, puis
classe des figures à partir de propriétés géométriques déjà établies. Le
scénario reconnaît un carré et un triangle rectangle isocèle.

Les inférences sont volontairement décomposées : un quadrilatère aux côtés
opposés parallèles devient un parallélogramme ; les angles droits donnent un
rectangle ; l'égalité des côtés donne un losange ; rectangle et losange
donnent enfin un carré.

## Intérêt

- chaînage profond et explication de classification ;
- appartenance simultanée à plusieurs types ;
- taxonomie construite par des règles ordinaires ;
- exemple plus proche d'une base de connaissances que d'un calcul.

```sh
uv run python -m rulebases.runner thesis/geometry
```

## Prédicats calculés et types

Le noyau suppose fournis les prédicats `opposite_sides_parallel`,
`all_angles_right`, etc. Une reconstruction géométrique complète demanderait :

- des prédicats calculés sûrs (`distance`, `midpoint`, `perpendicular`) ;
- une hiérarchie de types déclarative, pour éviter de réécrire toutes les
  propagations `is-a`.

`FRESH` couvre le nommage des constructions. `computed_example.py` montre
maintenant comment enregistrer explicitement un prédicat pur et l'appeler avec
`CHECK`, sans exposer une fonction Python arbitraire au texte.
`type_hierarchy_group()` fournit la clôture `subtype` et la propagation
`instance_of` avec provenance. Le scénario historique conserve ses règles de
classification détaillées car elles expliquent mieux les conditions
géométriques qu'une simple taxonomie.
