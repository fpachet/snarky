# V22 — audit des candidats contraintes

Une contrainte candidate est recherchée uniquement parmi les prédicats
lisibles et seulement dans les décisions où ce prédicat peut changer
entre deux notes candidates. Aucun candidat n'est encore transformé en
filtre dur.

## Protocole

- Prédicats lisibles audités : `1142`.
- Décisions train/validation : `9230/2708`.
- Occasions train minimales : `100`.
- Support train minimal : `10` chorals.
- Occasions validation minimales : `30`.
- Taux maximal d'exception pour « presque invariant » : `1.00 %`.
- Test réservé chargé : `false`.

## Résumé

- `exact_empirical_prohibition` : `88`.
- `near_empirical_prohibition` : `161`.

## Interdictions candidates

| Statut | Prédicat | Train exceptions/occasions | Validation exceptions/occasions |
|---|---|---:|---:|
| `exact_empirical_prohibition` | ténor : intervalle depuis la note précédente de classe 11 (septième majeure modulo l’octave) | 0/2451 | 0/688 |
| `exact_empirical_prohibition` | ténor : mouvement depuis la note précédente supérieur à 12 demi-tons | 0/2451 | 0/688 |
| `exact_empirical_prohibition` | ténor et soprano : écart ordonné ≤ -1 demi-tons au bloc central | 0/2451 | 0/688 |
| `exact_empirical_prohibition` | ténor et soprano : écart ordonné ≤ -1 demi-tons au bloc précédent | 0/2451 | 0/685 |
| `exact_empirical_prohibition` | ténor et soprano : écart ordonné ≤ -2 demi-tons au bloc central | 0/2450 | 0/688 |
| `exact_empirical_prohibition` | ténor et soprano : écart ordonné ≤ -2 demi-tons au bloc précédent | 0/2450 | 0/685 |
| `exact_empirical_prohibition` | alto : intervalle depuis la note précédente de classe 11 (septième majeure modulo l’octave) | 0/2413 | 0/717 |
| `exact_empirical_prohibition` | alto : mouvement depuis la note précédente supérieur à 12 demi-tons | 0/2413 | 0/717 |
| `exact_empirical_prohibition` | basse et soprano : écart ordonné ≤ -1 demi-tons au bloc central | 0/2413 | 0/698 |
| `exact_empirical_prohibition` | basse et soprano : écart ordonné ≤ 0 demi-tons au bloc central | 0/2413 | 0/698 |
| `exact_empirical_prohibition` | basse et soprano : écart ordonné ≤ 1 demi-tons au bloc central | 0/2413 | 0/698 |
| `exact_empirical_prohibition` | basse et soprano : écart ordonné ≤ 2 demi-tons au bloc central | 0/2413 | 0/698 |
| `exact_empirical_prohibition` | basse et alto : écart ordonné ≤ -1 demi-tons au bloc central | 0/2413 | 0/698 |
| `exact_empirical_prohibition` | basse et alto : écart ordonné ≤ -2 demi-tons au bloc central | 0/2413 | 0/698 |
| `exact_empirical_prohibition` | basse et soprano : écart ordonné ≤ -1 demi-tons au bloc précédent | 0/2413 | 0/695 |
| `exact_empirical_prohibition` | basse et soprano : écart ordonné ≤ -2 demi-tons au bloc central | 0/2412 | 0/698 |
| `exact_empirical_prohibition` | basse et soprano : écart ordonné ≤ -2 demi-tons au bloc précédent | 0/2412 | 0/695 |
| `exact_empirical_prohibition` | alto et basse : écart ordonné ≤ -1 demi-tons au bloc central | 0/2411 | 0/717 |
| `exact_empirical_prohibition` | alto et basse : écart ordonné ≤ -2 demi-tons au bloc central | 0/2411 | 0/717 |
| `exact_empirical_prohibition` | alto et basse : écart ordonné ≤ -1 demi-tons au bloc précédent | 0/2411 | 0/717 |
| `exact_empirical_prohibition` | alto et basse : écart ordonné ≤ -2 demi-tons au bloc précédent | 0/2411 | 0/717 |
| `exact_empirical_prohibition` | soprano : intervalle depuis la note précédente de classe 10 (septième mineure modulo l’octave) | 0/1953 | 0/605 |
| `exact_empirical_prohibition` | soprano : intervalle depuis la note précédente de classe 11 (septième majeure modulo l’octave) | 0/1953 | 0/605 |
| `exact_empirical_prohibition` | soprano : intervalle depuis la note précédente de classe 6 (triton) | 0/1953 | 0/605 |
| `exact_empirical_prohibition` | soprano : mouvement depuis la note précédente supérieur à 12 demi-tons | 0/1953 | 0/605 |
| `exact_empirical_prohibition` | soprano et ténor : écart ordonné ≤ -1 demi-tons au bloc central | 0/1953 | 0/605 |
| `exact_empirical_prohibition` | soprano et ténor : écart ordonné ≤ -2 demi-tons au bloc central | 0/1953 | 0/605 |
| `exact_empirical_prohibition` | soprano et basse : écart ordonné ≤ 0 demi-tons au bloc central | 0/1953 | 0/605 |
| `exact_empirical_prohibition` | soprano et basse : écart ordonné ≤ 1 demi-tons au bloc central | 0/1953 | 0/605 |
| `exact_empirical_prohibition` | soprano et basse : écart ordonné ≤ 2 demi-tons au bloc central | 0/1953 | 0/605 |
| `exact_empirical_prohibition` | soprano et ténor : écart ordonné ≤ -1 demi-tons au bloc précédent | 0/1953 | 0/605 |
| `exact_empirical_prohibition` | soprano et ténor : écart ordonné ≤ -2 demi-tons au bloc précédent | 0/1953 | 0/605 |
| `exact_empirical_prohibition` | soprano et basse : écart ordonné ≤ 0 demi-tons au bloc précédent | 0/1953 | 0/605 |
| `exact_empirical_prohibition` | soprano et basse : écart ordonné ≤ 1 demi-tons au bloc précédent | 0/1953 | 0/605 |
| `exact_empirical_prohibition` | soprano et basse : écart ordonné ≤ 2 demi-tons au bloc précédent | 0/1953 | 0/605 |
| `exact_empirical_prohibition` | soprano et basse : écart ordonné ≤ -1 demi-tons au bloc central | 0/1952 | 0/605 |
| `exact_empirical_prohibition` | soprano et basse : écart ordonné ≤ -2 demi-tons au bloc central | 0/1952 | 0/605 |
| `exact_empirical_prohibition` | soprano et basse : écart ordonné ≤ -1 demi-tons au bloc précédent | 0/1951 | 0/605 |
| `exact_empirical_prohibition` | soprano et basse : écart ordonné ≤ -2 demi-tons au bloc précédent | 0/1951 | 0/605 |
| `exact_empirical_prohibition` | ténor : intervalle vers la note suivante de classe 11 (septième majeure modulo l’octave) | 0/1722 | 0/489 |

## Obligations candidates

| Statut | Prédicat | Train exceptions/occasions | Validation exceptions/occasions |
|---|---|---:|---:|

Ces lignes restent des invariants empiriques. Une absence dans un
petit corpus ne prouve pas une impossibilité logique. La promotion
en contrainte requiert encore la stabilité inter-plis, l'examen des
doublons logiques et une validation sur le corpus train complet.
