# V32 — facteur séquentiel de cycle de deux notes

V31 a rejeté la réplication exacte d'un taux ponctuel. V32 teste une
hypothèse différente et préenregistrée avant de charger les 219
chorals restants : parmi les retours `ABA`, prolonger `ABAB` doit
rester rare (borne Wilson supérieure < 25 %) et le taux appris sur
32 chorals doit mieux prédire le holdout qu'un Bernoulli neutre.

## Confirmation

- Initial 32 : `123 / 954` = `12.893 %`.
- Holdout 219 : `846 / 6241` = `13.556 %`.
- Train complet 251 : `969 / 7195` = `13.468 %`.
- Verdict : `CONFIRMED`.

## Modèle parcimonieux

La granularité choisie par BIC sur les 251 chorals est
 `inner_plus_bass`.

- `F-K3-V32-CYCLE-INNER` (Alto, Tenor) : `p=0.154537`, `log_weight=-1.699453`.
- `F-K3-V32-CYCLE-BASS` (Bass) : `p=0.081633`, `log_weight=-2.420368`.

Chaque facteur ne fait qu'ajouter son poids à l'alternative qui
transformerait `... A B A` en `... A B A B`. Il n'interdit ni
`ABA` ni `ABAB`, n'active aucune autre règle et ne lit que quatre
attaques d'une seule voix.
