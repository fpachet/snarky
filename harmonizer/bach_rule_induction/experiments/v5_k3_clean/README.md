# V5-K3-CLEAN

Expérience clean-room fondée sur une seule hypothèse musicale structurelle :
les règles portent sur trois blocs verticaux consécutifs.

Le dossier ne charge aucun fichier de `rules/` ni aucun manifeste de
`rule_bases/historical` ou `rule_bases/learned`.

## Composants

- `k3.py` : représentation du corpus, catalogue numérique, gradient et Gibbs ;
- `run_induction.py` : construction du corpus et génération de colonnes ;
- `run_gibbs_diagnostic.py` : génération dense avec le modèle appris ;
- `run_k3_ablation.py` : retrait d'une règle et réajustement des autres ;
- `run_k3_null_max_calibration.py` : calibration familiale de la première règle ;
- `run_rhythmic_gibbs.py` : génération des hauteurs sur une grille polyphonique
  réelle d'attaques et de tenues ;
- `run_contextual_induction.py` : réinduction depuis zéro avec tonalité,
  métrique, répétitions attaquées et fingerprints verticaux ;
- `run_contextual_generation_comparison.py` : comparaison contrôlée
  Bach/V5.5/V5.6/V5.7 sur le même soprano et le même rythme ;
- `run_chromatic_residual_audit.py` : calibration conditionnelle des classes
  tonales empiriquement rares sur validation ;
- `run_multichoral_generation_audit.py` : campagne Gibbs reproductible sur
  plusieurs chorals et plusieurs graines ;
- `run_chromatic_loop_comparison.py` : décision avant/après et protocole V5.9 ;
- `run_generative_moment_calibration.py` : calibration de huit règles maximum
  par contraste de moments Bach−Gibbs sur train ;
- `run_v5_9_comparison.py` : validation appariée V5.7/V5.8/V5.9 et retour sur
  BWV 108.6 ;
- `run_generative_residual_audit.py` : second tour sur les licences restantes
  et les interactions avec les empreintes verticales locales ;
- `local_tonality.py` : HMM transposable et apprentissage EM d'un statut tonal
  latent à partir des noyaux K3 ;
- `run_local_tonality_poc.py` : ajustement train et évaluation tenue à part ;
- `run_local_tonality_sensitivity.py` : robustesse à la persistance du statut ;
- `run_v5_12_explicit_calibration.py` : contraste génératif de faits
  observables de basse, métrique, sonorité et transition ;
- `run_explicit_generation_audit.py` : audit apparié des mouvements de basse
  et sonorités sur des tranches distinctes de validation ;
- `make_v5_16_interpolated_model.py` : interpolation reproductible des quatre
  corrections de basse V5.15 sur le socle V5.14 ;
- `export_v5_16_factor_catalogue.py` : fusion des corrections additives et
  export des portées, instanciations et poids probabilistes canoniques ;
- `snarky_choice_bridge.py` : compilation fidèle de ces facteurs en poids
  positifs pour `CHOICE`, avec explication factorielle de chaque candidate ;
- `export_v5_16_factor_program.py` : migration du POC gelé vers le DSL pur
  `FACTOR` ;
- `run_v6_factor_induction.py` : génération de colonnes depuis la grammaire
  V6 gelée, calibration nulle familiale et apprentissage conditionnel ;
- `fit_joint_pseudolikelihood.py` : somme les activations de tous les facteurs
  avant le softmax et réapprend conjointement les 48 poids V6+résiduels ;
- `fit_exact_joint_pseudolikelihood.py` : construit chaque monde candidat
  attaque/tenue avec toutes les portées K3 affectées, vérifie la parité Gibbs
  et réapprend les 48 poids sur les conditionnelles globales exactes ;
- `run_exact_factor_reinduction.py` : repart des 954 facteurs gelés, classe
  leurs gradients sur les conditionnelles Gibbs exactes et réapprend
  conjointement la structure, le registre, le profil tonal et les poids ;
- `export_v6_factor_program.py` : export des 30 facteurs sélectionnés dans le
  DSL Snarky ;
- `refit_v6_generative_weights.py` : réajustement des seuls paramètres par
  contraste de moments Bach−Gibbs, structure factorielle gelée ;
- `run_v6_factor_controllability.py` : estimation train du Jacobien
  diagnostics×facteurs par covariance et projection minimale standardisée ;
  trajectoires locales par worker, cache explicite des chaînes persistantes,
  arrêt adaptatif sur les moments du gradient et ordonnanceur coloré optionnel ;
- `apply_v6_control_delta.py` : application d'une direction apprise avec
  région de confiance et contrôle de NLL conditionnelle ;
- `run_explicit_generation_audit.py` : ordonnance toutes les générations
  pièce×modèle×graine en parallèle et mesure dix diagnostics explicites ;
- `results/` : artefacts et rapports reproductibles.

`V5.0` conserve le premier catalogue spécialisé, qui a appris huit variantes
de la même préférence mélodique. `V5.1` ajoute des prédicats invariants par
voix et symétriques dans le temps afin que la loi générale soit sélectionnée
avant d'éventuelles spécialisations.

Résultats principaux :

- [`V5_1_K3_COMPACT_REPORT.md`](results/V5_1_K3_COMPACT_REPORT.md) ;
- [`V5_1_K3_COMPACT_NULL_REPORT.md`](results/V5_1_K3_COMPACT_NULL_REPORT.md) ;
- [`V5_1_AUTHENTIC_NULL_COMPARISON.md`](results/V5_1_AUTHENTIC_NULL_COMPARISON.md) ;
- [`V5_2_FIRST_RULE_AUDIT.md`](results/V5_2_FIRST_RULE_AUDIT.md), audit du
  seuil mélodique `> 2` ;
- [`V5_3_K3_REFIT_ABLATION.md`](results/V5_3_K3_REFIT_ABLATION.md), contribution
  conditionnelle de chaque règle après réajustement des onze autres ;
- [`V5_4_K3_FIRST_COLUMN_NULL_MAX.md`](results/V5_4_K3_FIRST_COLUMN_NULL_MAX.md),
  calibration de la première découverte contre le maximum des faux signaux ;
- [`V5_5_K3_RHYTHMIC_GIBBS.md`](results/V5_5_K3_RHYTHMIC_GIBBS.md), premier
  choral avec croches, doubles-croches et tenues par voix ;
- [`V5_6_K3_CONTEXTUAL_REINDUCTION.md`](results/V5_6_K3_CONTEXTUAL_REINDUCTION.md),
  redécouverte numérique des principales sonorités triadiques ;
- [`V5_7_K3_CONTEXTUAL_REINDUCTION.md`](results/V5_7_K3_CONTEXTUAL_REINDUCTION.md),
  raffinement tonal et répétition attaquée par voix ;
- [`V5_7_CONTEXTUAL_GENERATION_COMPARISON.md`](results/V5_7_CONTEXTUAL_GENERATION_COMPARISON.md),
  mesure avant/après des défauts observés dans la partition ;
- [`V5_8_CHROMATIC_RESIDUAL_AUDIT.md`](results/V5_8_CHROMATIC_RESIDUAL_AUDIT.md),
  contraste entre choix rares observés et attendus sur validation ;
- [`V5_8_MULTICHORAL_GENERATION_AUDIT.md`](results/V5_8_MULTICHORAL_GENERATION_AUDIT.md),
  première campagne générative V5.7 sur 20 chorals ;
- [`V5_8_CHROMATIC_LOOP_COMPARISON.md`](results/V5_8_CHROMATIC_LOOP_COMPARISON.md),
  rejet génératif de V5.8 et définition du gradient V5.9 ;
- [`V5_9_GENERATIVE_CALIBRATION.md`](results/V5_9_GENERATIVE_CALIBRATION.md),
  poids appris par les chaînes persistantes sur train ;
- [`V5_9_GENERATIVE_VALIDATION_COMPARISON.md`](results/V5_9_GENERATIVE_VALIDATION_COMPARISON.md),
  promotion expérimentale de V5.9 après validation multi-chorals ;
- [`V5_10_GENERATIVE_RESIDUAL_AUDIT.md`](results/V5_10_GENERATIVE_RESIDUAL_AUDIT.md),
  clôture négative des licences simples et verticales ;
- [`V5_11_LOCAL_TONALITY_HMM.md`](results/V5_11_LOCAL_TONALITY_HMM.md),
  exploration d'une origine transposable latente, sans interprétation de
  tonalité locale ;
- [`V5_11_LOCAL_TONALITY_SENSITIVITY.md`](results/V5_11_LOCAL_TONALITY_SENSITIVITY.md),
  robustesse à trois probabilités de persistance ;
- [`V5_12_TO_V5_16_BASS_SONORITY_LOOP.md`](results/V5_12_TO_V5_16_BASS_SONORITY_LOOP.md),
  correction de l'énergie conjointe et boucle complète sur la basse et les
  sonorités ;
- [`V5_16_CONFIRMATION_GENERATION_AUDIT.md`](results/V5_16_CONFIRMATION_GENERATION_AUDIT.md),
  confirmation sur dix chorals non utilisés pour choisir l'interpolation ;
- [`V5_16_MULTISEED_CONFIRMATION_AUDIT.md`](results/V5_16_MULTISEED_CONFIRMATION_AUDIT.md),
  réplication de la confirmation avec trois graines ;
- [`V5_16_SNARKY_CHOICE_BRIDGE.md`](results/V5_16_SNARKY_CHOICE_BRIDGE.md),
  parité numérique entre le modèle V5.16 et ses poids de `CHOICE` ;
- [`../../factor_bases/k3_v5_16_reference/`](../../factor_bases/k3_v5_16_reference/),
  référence factorielle V5.16 gelée ;
- [`../../factor_bases/k3_v6_induced/V6_RESEARCH_LOOP_SUMMARY.md`](../../factor_bases/k3_v6_induced/V6_RESEARCH_LOOP_SUMMARY.md),
  induction V6 depuis zéro, réajustement génératif et audit ;
- [`../../factor_bases/k3_v6_induced/V6_WEIGHT_LEARNING_SCALING_AND_CONTROL.md`](../../factor_bases/k3_v6_induced/V6_WEIGHT_LEARNING_SCALING_AND_CONTROL.md),
  mise à l'échelle, Jacobien multivarié, région de confiance et validation ;
- [`../../factor_bases/k3_v6_induced/V6_SAMPLING_OPTIMIZATION.md`](../../factor_bases/k3_v6_induced/V6_SAMPLING_OPTIMIZATION.md),
  parité du moteur par trajectoire et gain mesuré des chaînes persistantes ;
- [`../../factor_bases/k3_v6_induced/V6_ITERATION3_MULTISEED_DECISION.md`](../../factor_bases/k3_v6_induced/V6_ITERATION3_MULTISEED_DECISION.md),
  estimation multigraine, régularisation du problème inverse et rejet de la
  promotion après contrôle à 30 sweeps ;
- [`../../factor_bases/k3_v6_induced/V6_ITERATION3_RESIDUAL_FEATURE_DIAGNOSTIC.md`](../../factor_bases/k3_v6_induced/V6_ITERATION3_RESIDUAL_FEATURE_DIAGNOSTIC.md),
  classement train multigraine des mouvements de basse, contextes métriques et
  transitions de sonorités encore absents de V6 ;
- [`../../factor_bases/k3_v6_induced/V7_RESIDUAL_FACTOR_DECISION.md`](../../factor_bases/k3_v6_induced/V7_RESIDUAL_FACTOR_DECISION.md),
  apprentissage, ablation et rejet de trois candidats V7, avec paire d'écoute
  contrôlée Iteration 2/V7-Sonority ;
- [`../../factor_bases/k3_v6_induced/V8_JOINT_PSEUDOLIKELIHOOD_DECISION.md`](../../factor_bases/k3_v6_induced/V8_JOINT_PSEUDOLIKELIHOOD_DECISION.md),
  apprentissage conjoint de 48 poids, gain conditionnel tenu à part et rejet
  génératif après audits appariés à 6 et 30 sweeps ;
- [`../../factor_bases/k3_v6_induced/V8_EXACT_JOINT_PSEUDOLIKELIHOOD_DECISION.md`](../../factor_bases/k3_v6_induced/V8_EXACT_JOINT_PSEUDOLIKELIHOOD_DECISION.md),
  rectification des portées, parité exacte avec les logits Gibbs, apprentissage
  complet et audits génératifs du modèle corrigé ;
- [`../../factor_bases/k3_v6_induced/V9_EXACT_REINDUCTION_DECISION.md`](../../factor_bases/k3_v6_induced/V9_EXACT_REINDUCTION_DECISION.md),
  réinduction exacte depuis zéro, gain conditionnel compact et diagnostic des
  dissonances contextuelles apprises comme préférences globales ;
- `v5_1_k3_compact_model.json`, modèle complet pour le Gibbs.

Le protocole complet est
[`../../V5_K3_CLEAN_PROTOCOL.md`](../../V5_K3_CLEAN_PROTOCOL.md), et les
expériences remplacées comme axe principal sont résumées dans
[`../../EXPERIMENT_HISTORY.md`](../../EXPERIMENT_HISTORY.md).
