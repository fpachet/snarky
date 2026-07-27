# POC V3.9 — sonde conditionnelle DeepBach

## Protocole

- Les 12 contextes proviennent du test Bach gelé.
- Le réseau d'alto reçoit les 16 pas gauche/droite et les autres voix.
- Aucune sortie DeepBach n'est utilisée pour modifier la règle.
- Les poids historiques ont vu le corpus : audit, pas test indépendant.
- Port Keras 3 opérationnel ; certification TensorFlow 1.1 en attente.

## Résultats

| Sous-ensemble | N | Résolutions Bach | Probabilité DeepBach moyenne | Résolution top-1 | Rang moyen |
|---|---:|---:|---:|---:|---:|
| all | 12 | 10 | 0.9246 | 12 | 1.00 |
| exact | 9 | 9 | 0.9351 | 9 | 1.00 |
| nonexact | 3 | 1 | 0.8931 | 3 | 1.00 |
