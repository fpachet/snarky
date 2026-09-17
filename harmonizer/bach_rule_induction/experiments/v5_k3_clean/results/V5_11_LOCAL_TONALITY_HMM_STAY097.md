# V5.11 — statut tonal local latent

Un HMM non supervisé possède douze états transposables de référence tonale.
Chaque émission observe seulement les hauteurs des trois blocs K3 ; une
transition locale favorise la persistance entre noyaux adjacents.
Aucun accord, degré, modulation ou exemple de validation n'est fourni
pendant l'apprentissage.

Le mot « tonique locale » reste ici opérationnel : sans annotation
musicologique, l'état peut aussi se comporter comme un centre ou une
racine harmonique locale.

## Ajustement

- Chorals train : `251`.
- Chorals validation : `50`.
- Itérations EM : `15`.
- Probabilité de conserver le statut : `0.970`.
- Test scellé non chargé.

## Validation tenue à part

| Mesure | Valeur |
|---|---:|
| Gain de log-évidence par état sur tonique globale fixe | +1.345731 |
| États différents de la tonique globale | 32.63 % |
| Changements entre états adjacents | 8.44 % |
| Entropie postérieure normalisée | 0.028 |
| Classes rares avec référence globale | 3.780 % |
| Classes rares avec statut local | 1.348 % |
| Choix globalement rares devenant localement communs | 77.96 % |

## Lecture

Le statut latent améliore l'évidence tenue à part et requalifie une part substantielle des choix globalement rares sans devenir indéterminé. Il peut être ajouté comme fait local candidat à la prochaine induction.

Ce POC évalue l'utilité statistique du statut. Il ne prétend pas encore
que chaque état MAP correspond à une modulation analysée par un humain.
