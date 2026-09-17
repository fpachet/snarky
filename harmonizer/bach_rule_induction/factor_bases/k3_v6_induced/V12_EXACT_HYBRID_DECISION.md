# V12 — décision sur la correction hybride exacte

## Question

Peut-on corriger les dérives du Gibbs sans abandonner les facteurs appris par
pseudo-vraisemblance exacte ?

V12 garde les 30 facteurs et toutes les activations de V10. Aucun facteur
expert ni aucune règle historique n'est ajouté. Les poids seuls sont déplacés
dans une direction estimée par les covariances entre facteurs et dix
diagnostics génératifs sur les chorals de train. Chaque déplacement est borné
par une région de confiance et par une garde sur la NLL conditionnelle exacte
de validation.

## Résultat

La réponse méthodologique est **oui**, mais V12.2 ne devient pas le meilleur
générateur.

- La matrice de contrôle V10 atteint le rang `10/10`.
- V12.1 limite le plus grand déplacement de poids à `0,10`.
- V12.2 agrège trois estimations indépendantes, puis limite le déplacement
  supplémentaire à `0,05`.
- La NLL exacte de validation passe de `0,757960` pour V10 à `0,761169` pour
  V12.2 : la dégradation conditionnelle reste faible et explicitement bornée.
- Aucun nouveau facteur n'est introduit et le test réservé reste fermé.

À 30 sweeps sur 10 chorals de développement, V12.2 rapproche de Bach les dix
diagnostics suivis par rapport à V12.1. Ce résultat montre que la correction
des moments génératifs fonctionne aussi à horizon long et n'est pas un simple
artefact de mélange incomplet.

Sur les 50 chorals de validation, trois graines et 6 sweeps, V12.2 améliore
sept diagnostics sur dix par rapport à V10 :

| Mesure | Bach | V10 | V12.2 |
|---|---:|---:|---:|
| Demi-tons à la basse | 25,67 % | 28,39 % | 26,40 % |
| Répétitions à la basse | 3,37 % | 4,26 % | 4,16 % |
| Sauts de basse > 4 demi-tons | 26,76 % | 31,43 % | 32,76 % |
| Basse hors gamme naturelle | 8,15 % | 13,03 % | 12,51 % |
| Blocs triadiques | 52,74 % | 52,29 % | 52,41 % |
| Blocs forts non triadiques | 28,72 % | 39,85 % | 37,94 % |
| Dissonances par bloc faible | 0,987 | 0,878 | 0,859 |
| Dissonances par bloc fort | 0,410 | 0,607 | 0,548 |
| `{0,3,6,8}` sur bloc fort | 2,17 % | 1,91 % | 1,94 % |
| `{0,3,6,8}` sur bloc faible | 2,93 % | 3,31 % | 3,40 % |

## Décision

V12.2 est retenu comme **validation de la boucle hybride**, mais n'est pas
promu comme modèle génératif de référence. `Iteration2` reste le checkpoint
retenu : sur la validation complète, il est sensiblement plus proche de Bach
pour les grands sauts, les notes de basse hors gamme et les sonorités fortes.

Les erreurs résiduelles ont une interprétation structurelle :

1. des statistiques globales peuvent réduire le chromatisme moyen sans savoir
   quels demi-tons ou altérations sont licites dans un contexte précis ;
2. une pénalité globale sur les blocs non triadiques ne distingue pas une
   dissonance préparée et résolue d'un accord accidentel ;
3. le compromis sur dix moments permet de déplacer une erreur vers un
   diagnostic corrélé, comme les grands sauts de basse.

La prochaine itération ne doit donc pas simplement augmenter l'amplitude du
contrôle. Elle doit enrichir le catalogue avec des facteurs locaux lisibles :

- basse conditionnée par degré relatif, métrique et direction du mouvement ;
- intervalles verticaux conditionnés par paire de voix et force métrique ;
- préparation et résolution sur le noyau K3 ;
- licences explicites de passage et de broderie sur temps faible.

Ces facteurs resteront candidats appris du corpus. L'expert fournit la
grammaire observable, pas leur signe ni leur poids.

## Artefacts

- `v12_v10_train32_controllability.json` : contrôlabilité initiale ;
- `v12_iteration2_multiseed_control.json` : direction consensuelle ;
- `v12_exact_hybrid_iteration2_model.json` : modèle audité ;
- `V12_EXACT_HYBRID_ITERATION2_FULL_VALIDATION_GENERATION_AUDIT.md` :
  validation complète ;
- `V12_EXACT_HYBRID_ITERATION2_SWEEP30_DEVELOPMENT_GENERATION_AUDIT.md` :
  audit à horizon long ;
- `V12_EXACT_HYBRID_ITERATION2_BWV108_6_GENERATION.md` : exemple noté.
