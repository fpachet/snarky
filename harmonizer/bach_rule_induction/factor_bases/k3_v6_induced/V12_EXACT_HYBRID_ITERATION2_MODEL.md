# V12 — correction générative sous garde conditionnelle exacte

La structure V10 reste gelée. Une direction issue des covariances
Gibbs sur train est appliquée une seule fois. Son amplitude respecte
à la fois un rayon de confiance et une limite de dégradation de la
pseudo-vraisemblance exacte sur validation.

- Échelle demandée : `1.000000`.
- Échelle appliquée : `0.914261`.
- Plus grand déplacement de poids : `0.050000`.
- NLL validation exacte : `0.758702` → `0.761169`.
- Budget de dégradation : `0.010000`.
- Facteurs ajoutés : `0`.
- Test réservé chargé : `false`.

Les audits appariés confirment que cette deuxième correction rapproche les dix
diagnostics de Bach par rapport à V12.1 à 30 sweeps et sept sur dix par rapport
à V10 sur les 50 chorals de validation. Le modèle n'est toutefois pas promu :
les grands sauts de basse et les blocs forts non triadiques restent excessifs.
La décision complète est dans `V12_EXACT_HYBRID_DECISION.md`.
