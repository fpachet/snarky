# V5.11 — sensibilité de la persistance tonale locale

Même train, même validation, quinze itérations EM. Seule varie la
probabilité de conserver le statut entre deux noyaux adjacents.
Le test scellé reste fermé.

| Persistance | Gain d'évidence validation | États déplacés | Changements | Entropie | Rares reclassifiés |
|---:|---:|---:|---:|---:|---:|
| 0.85 | +1.367574 | 33.78 % | 10.33 % | 0.033 | 81.76 % |
| 0.92 | +1.380406 | 33.38 % | 9.52 % | 0.030 | 80.96 % |
| 0.97 | +1.345731 | 32.63 % | 8.44 % | 0.028 | 77.96 % |

Le résultat qualitatif est stable : même avec une transition beaucoup
plus ou moins persistante, le statut améliore fortement l'évidence et
reclasse environ quatre choix globalement rares sur cinq.
