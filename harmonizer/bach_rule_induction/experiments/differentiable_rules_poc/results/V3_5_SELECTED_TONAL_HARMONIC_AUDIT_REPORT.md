# POC V3.5 — audit harmonique de la clause tonale retenue

## Protocole

- Entrée : clauses passant la calibration familiale V3.4.
- Audit indépendant : ensembles complets de classes des quatre voix.
- Ces ensembles n'ont pas participé à la sélection V3.1–V3.4.
- Le test final reste scellé.

## major · Alto · basse 2→4

Hypothèse postérieure : `vii°6_to_I6`, source `[2, 5, 11]`, cible `[0, 4, 7]`.

| Split | Occurrences | Résolutions | Source exacte | Cible exacte | Progression exacte | Résolution exacte/autre |
|---|---:|---:|---:|---:|---:|---:|
| train | 54 | 47/54 | 46/54 | 45/54 | 41/54 | 41/41 vs 6/13 |
| validation | 19 | 19/19 | 12/19 | 19/19 | 12/19 | 12/12 vs 7/7 |

Classification : `PITCH_CLASS_PROXY_PARTIAL`.
Fisher unilatéral train, progression exacte contre autres contextes : `p = 9.68941e-06`.
