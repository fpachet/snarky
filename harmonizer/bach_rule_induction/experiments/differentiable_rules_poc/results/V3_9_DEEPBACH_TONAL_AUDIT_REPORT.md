# POC V3.9 — audit de générations DeepBach

## Portée

- Générations Keras 3 avec poids Keras 2 historiques inchangés.
- Compatibilité opérationnelle ; comparaison TensorFlow 1.1 en attente.
- Métadonnées générées en do majeur.
- Audit sur les attaques d'alto, sans réparation Snarky.

## Comparaison

| Corpus | Proxy résolu | Noyau exact résolu |
|---|---:|---:|
| Bach test gelé | 10/12 | 9/9 |
| DeepBach généré | 0/0 | 0/0 |

Violations DeepBach observées : `0`.

Le support généré est insuffisant pour une comparaison de taux.
Le résultat sert d'audit de cas, pas d'estimation statistique.
