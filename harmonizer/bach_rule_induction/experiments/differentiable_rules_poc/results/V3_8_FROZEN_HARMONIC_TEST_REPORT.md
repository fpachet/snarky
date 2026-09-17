# POC V3.8 — test final gelé

## Protocole

- Feature et seuils gelés avant l'ouverture.
- Ajustement sur 301 chorals de développement.
- Évaluation unique sur 51 chorals de test.
- Aucun réajustement autorisé après lecture.

## Résultats

| Modèle | NLL test | Gain contre baseline | Poids |
|---|---:|---:|---:|
| baseline | 1.234034 | — | — |
| both | 1.229618 | +0.00441545 | 1.998, 2.051 |
| graded_exact | 1.229620 | +0.00441387 | 2.021 |

## Décision

Accepté : `True`.
Gain conservé face aux deux poids : `1.000`.
