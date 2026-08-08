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
- `render_piano_mp3.py` : neutralise les programmes vocaux du MIDI, force le
  programme General MIDI 0 et rend un piano acoustique avec `MS Basic.sf3` ;
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
- `run_v24_snarky_search.py` : premier générateur V24 sans Gibbs ; il compile
  les facteurs appris en préférences de fenêtres, les filtres V22 en
  contraintes persistantes, puis confie propagation, choix et rollback à la
  recherche CSP de Snarky ;
- `run_two_loop_score_floor_experiment.py` : calibre un threshold strict sur
  les pseudo-vraisemblances exactes du modèle MLE V23, propage une borne
  optimiste du score et transforme un plancher devenu inaccessible en
  contradiction Snarky et backtrack ;
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
- `grammar_v10_interval_context.yaml` et `grammar_v11_tonal_licenses.yaml` :
  extensions gelées pour les licences locales d'intervalle puis les classes
  tonales rares définies sur train ;
- `grammar_v13_directed_metric_context.yaml` et
  `grammar_v14_directed_metric_trajectory.yaml` : clauses dirigées par paire
  de voix, métrique et trajectoire de préparation/résolution ;
- `export_v6_factor_program.py` : export des 30 facteurs sélectionnés dans le
  DSL Snarky ;
- `refit_v6_generative_weights.py` : réajustement des seuls paramètres par
  contraste de moments Bach−Gibbs, structure factorielle gelée ;
- `run_v6_factor_controllability.py` : estimation train du Jacobien
  diagnostics×facteurs par covariance et projection minimale standardisée ;
  trajectoires locales par worker, cache explicite des chaînes persistantes,
  arrêt adaptatif sur les moments du gradient et ordonnanceur coloré optionnel ;
- `apply_exact_control_delta.py` : applique une direction générative avec
  rayon de confiance et dichotomie sous garde de NLL Gibbs exacte ;
- `ablate_exact_feature.py` : retire exactement une colonne sans réajustement
  afin de comparer son gain conditionnel et son effet causal génératif ;
- `rank_exact_hybrid_candidates.py` : présélectionne le top-K conditionnel
  exact sous un modèle existant, sans l'admettre avant son audit génératif ;
- `aggregate_v16_candidate_admission.py` : agrège les sensibilités du top-K
  sur plusieurs graines et applique le garde-fou de Pareto avant admission ;
- `refit_exact_admitted_candidate.py` : ajoute une seule clause admise et
  réajuste conjointement les poids et paramètres auxiliaires sur les mondes
  Gibbs exacts ;
- `run_v17_paired_finite_difference.py` : perturbe réellement le sampler avec
  le même état initial et le même flux aléatoire pour mesurer les candidats
  aux horizons finis sans hypothèse d'équilibre ;
- `make_v17_joint_candidate.py` : construit une correction conjointe bornée
  entre une nouvelle colonne et un seul facteur existant pour réplication
  appariée ;
- `run_v18_explanatory_sparse_induction.py` : apprend une frontière
  qualité–complexité de prédicats lisibles par pseudo-vraisemblance exacte,
  avec `L1` pondéré par leur longueur descriptive et sélection à une erreur
  standard ;
- `run_v18_weight_stability.py` : réapprend les poids de la base V18 sur quatre
  replis par pièce sans confondre stabilité paramétrique et stabilité de la
  découverte ;
- `prepare_v18_structure_stability.py` et
  `aggregate_v18_structure_stability.py` : répètent la découverte complète sur
  quatre sous-corpus et extraient le noyau unanime ;
- `fit_v18_unanimous_full.py` : réapprend ce noyau sur les 251 chorals de train
  avec arrêt sur les 50 de validation ;
- `export_v18_explanatory_artifacts.py` : produit les RuleCards, le catalogue
  factoriel et le programme Snarky de la base explicative ;
- `audit_v18_snarky_parity.py` : compare les activations, contributions et
  probabilités du modèle Python au programme `FACTOR` Snarky ;
- `build_v19_exact_catalogue.py` : matérialise le catalogue qui ajoute les
  statuts triadiques fort/faible et les contextes intervalliques métriques ;
- les utilitaires V18 de stabilité, réajustement, export et parité acceptent
  désormais des identifiants et sorties V19 sans dupliquer le protocole ;
- `run_v12_context_residual_audit.py` : localise sur train les résidus par
  paire de voix, force métrique, statut de résolution et transition tonale de
  basse ;
- `apply_v6_control_delta.py` : application d'une direction apprise avec
  région de confiance et contrôle de NLL conditionnelle ;
- `run_explicit_generation_audit.py` : ordonnance toutes les générations
  pièce×modèle×graine en parallèle et mesure dix diagnostics explicites ;
- `grouped_maxent.py` et `run_v21_grouped_transition.py` : apprennent un
  `RuleGroup` complet avec projection d'identifiabilité, pénalité proximale et
  sélection bootstrap appariée ;
- `aggregate_v22_shared_root_motion.py` : agrège les quatre folds V22, la
  validation complète et la stabilité des 24 poids partagés ;
- `export_v22_shared_root_motion.py` : produit le modèle génératif, la carte de
  groupe et les 43 facteurs Snarky (19 de socle + 24 du groupe) ;
- `build_v22_constraint_ablation.py` : compile 23 prédicats zéro-exception en
  filtres pré-test, sans les déclarer `MUST` ;
- `build_v23_selected_cache.py` et `audit_v23_status_coverage.py` :
  matérialisent les 38 cellules V23 et vérifient leur testabilité avant tout
  ajustement ;
- `run_v23_metric_bass_harmony.py`, `run_v23_stability_fold.py` et
  `aggregate_v23_metric_bass_harmony.py` : apprennent les groupes basse et
  harmonie, exécutent les ablations et consolident quatre folds puis le
  contrôle 251/50 ;
- `export_v23_metric_harmony.py` : exporte les 43 facteurs V22 et les 14
  statuts harmoniques retenus en modèle génératif, catalogue et programme
  `FACTOR` Snarky ;
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
- [`../../factor_bases/k3_v6_induced/V10_V11_CONTEXT_LICENSE_DECISION.md`](../../factor_bases/k3_v6_induced/V10_V11_CONTEXT_LICENSE_DECISION.md),
  gain des licences d'intervalle, échec des licences tonales plates et
  nécessité d'une sélection hybride conditionnelle–générative ;
- [`../../factor_bases/k3_v6_induced/V12_EXACT_HYBRID_DECISION.md`](../../factor_bases/k3_v6_induced/V12_EXACT_HYBRID_DECISION.md),
  validation d'une correction des moments génératifs sous garde de
  pseudo-vraisemblance exacte, sans promotion du candidat ;
- [`../../factor_bases/k3_v6_induced/V13_DIRECTED_METRIC_DECISION.md`](../../factor_bases/k3_v6_induced/V13_DIRECTED_METRIC_DECISION.md),
  localisation des incompatibilités de contexte, réinduction V13 et rejet
  génératif avant validation complète ;
- [`../../factor_bases/k3_v6_induced/V14_V15_HYBRID_STRUCTURE_DECISION.md`](../../factor_bases/k3_v6_induced/V14_V15_HYBRID_STRUCTURE_DECISION.md),
  ablation causale d'une clause prédictive mais générativement nuisible et
  protocole d'admission hybride V16 ;
- [`../../factor_bases/k3_v6_induced/V16_HYBRID_ADMISSION_DECISION.md`](../../factor_bases/k3_v6_induced/V16_HYBRID_ADMISSION_DECISION.md),
  top-K exact, échec du gradient de covariance transitoire et remplacement
  prévu par des différences finies appariées du sampler ;
- [`../../factor_bases/k3_v6_induced/V17_PAIRED_FINITE_DIFFERENCE_DECISION.md`](../../factor_bases/k3_v6_induced/V17_PAIRED_FINITE_DIFFERENCE_DECISION.md),
  écran apparié des douze facteurs à horizon court et rejet de la première
  itération sans relâchement rétrospectif des seuils ;
- [`../../factor_bases/k3_v6_induced/V18_EXPLANATORY_DECISION.md`](../../factor_bases/k3_v6_induced/V18_EXPLANATORY_DECISION.md),
  retour à une induction MaxEnt de règles indépendantes et lisibles ;
- [`../../factor_bases/k3_v6_induced/V19_VERTICAL_STATUS_DECISION.md`](../../factor_bases/k3_v6_induced/V19_VERTICAL_STATUS_DECISION.md),
  découverte stable de la préférence pour les triades complètes, distinction
  métrique apprise et amélioration générative tenue hors apprentissage ;
- [`../../factor_bases/k3_v6_induced/V20_NON_DUPLICATION_GATE.md`](../../factor_bases/k3_v6_induced/V20_NON_DUPLICATION_GATE.md),
  inventaire des familles déjà testées et critères d'admission d'une
  représentation harmonique réellement nouvelle ;
- [`../../factor_bases/k3_v6_induced/V20B_IDENTIFIABLE_HARMONIC_STATUS_DECISION.md`](../../factor_bases/k3_v6_induced/V20B_IDENTIFIABLE_HARMONIC_STATUS_DECISION.md),
  stabilité de quatre statuts verticaux nommés après correction de
  l'identifiabilité de la grammaire ;
- [`../../factor_bases/k3_v6_induced/V20C_NAMED_ROOT_TRANSITIONS_DECISION.md`](../../factor_bases/k3_v6_induced/V20C_NAMED_ROOT_TRANSITIONS_DECISION.md),
  audit de nouveauté face à V13 puis rejet conditionnel des 288 transitions
  de fondamentales, sans réplications ni génération redondantes ;
- [`../../factor_bases/k3_v6_induced/V21_GROUPED_LEARNING_DECISION.md`](../../factor_bases/k3_v6_induced/V21_GROUPED_LEARNING_DECISION.md),
  apprentissage conjoint de la table de transitions, gain apparié initial,
  puis rejet hors pli de ses 288 degrés de liberté ;
- [`../../factor_bases/k3_v6_induced/V22_SHARED_ROOT_MOTION_DECISION.md`](../../factor_bases/k3_v6_induced/V22_SHARED_ROOT_MOTION_DECISION.md),
  remplacement de V21 par une règle partagée de 24 paramètres, stable dans
  quatre folds et sur la validation complète ;
- [`../../factor_bases/k3_v6_induced/V22_RULEGROUP_CONSTRAINTS_VALIDATION10X1_SWEEP6.md`](../../factor_bases/k3_v6_induced/V22_RULEGROUP_CONSTRAINTS_VALIDATION10X1_SWEEP6.md),
  ablation générative séparant socle, groupe appris et filtres candidats ;
- [`../../factor_bases/k3_v6_induced/V23_METRIC_BASS_HARMONY_DECISION.md`](../../factor_bases/k3_v6_induced/V23_METRIC_BASS_HARMONY_DECISION.md),
  rétention du groupe de 14 statuts harmoniques forts et rejet parcimonieux
  des 24 paramètres supplémentaires de basse ;
- [`../../factor_bases/k3_v6_induced/V23_V22_CONTROLLED_GENERATION_VALIDATION10X1_SWEEP6.md`](../../factor_bases/k3_v6_induced/V23_V22_CONTROLLED_GENERATION_VALIDATION10X1_SWEEP6.md),
  comparaison générative contrôlée de V22, V23 et des filtres candidats ;
- [`../../factor_bases/k3_v6_induced/V24_RESIDUAL_SONORITY_DECISION.md`](../../factor_bases/k3_v6_induced/V24_RESIDUAL_SONORITY_DECISION.md),
  rejet conditionnel, calibration MaxEnt générative, validation V23–V24,
  ablation du Gibbs conjoint et compilation Snarky du vocabulaire résiduel ;
- [`run_full_snarky_score_floor_generation.py`](run_full_snarky_score_floor_generation.py),
  génération Snarky des 229 segments d'alto, ténor et basse sur les 98 blocs
  de BWV 108.6, avec soprano et rythme seuls imposés ;
- [`../../factor_bases/k3_v6_induced/TWO_LOOP_FULL_GENERATION.md`](../../factor_bases/k3_v6_induced/TWO_LOOP_FULL_GENERATION.md),
  résultat et diagnostic de cette première génération complète ;
- [`../../factor_bases/k3_v6_induced/V26_JOINT_WEAK_RESOLUTION_DECISION.md`](../../factor_bases/k3_v6_induced/V26_JOINT_WEAK_RESOLUTION_DECISION.md),
  induction conjointe du rôle faible et de la qualité de résolution ;
- [`../../factor_bases/k3_v6_induced/V27_V28_BASS_DECISION.md`](../../factor_bases/k3_v6_induced/V27_V28_BASS_DECISION.md),
  séparation apprise entre appartenance harmonique, trajectoire et mouvement
  de basse, avec confirmation sur 50 chorals ;
- [`../../factor_bases/k3_v6_induced/V28_SNARKY_GENERATION_AUDIT.md`](../../factor_bases/k3_v6_induced/V28_SNARKY_GENERATION_AUDIT.md),
  audit apparié Bach/V23/V26/V27/V28 de la génération complète ;
- [`../../factor_bases/k3_v6_induced/V29_V30_STRONG_SUCCESSION_DECISION.md`](../../factor_bases/k3_v6_induced/V29_V30_STRONG_SUCCESSION_DECISION.md),
  confirmation V29, génération appariée et rejet du groupe V30 ;
- [`audit_v31_two_note_cycles.py`](audit_v31_two_note_cycles.py),
  audit des retours `ABA` et des continuations `ABAB` sur notes attaquées ;
- [`run_v31_cycle_induction.py`](run_v31_cycle_induction.py),
  premier groupe K3 de cycles, conservé comme résultat négatif selon le
  protocole de découverte ;
- [`fit_v31_cycle_conditional.py`](fit_v31_cycle_conditional.py),
  réplication ponctuelle stricte V31, rejetée sans relâchement rétrospectif ;
- [`fit_v32_cycle_factor.py`](fit_v32_cycle_factor.py),
  confirmation indépendante sur les 219 chorals d'apprentissage restants et
  MLE parcimonieux de deux facteurs finis alto–ténor/basse ;
- [`../../factor_bases/k3_v6_induced/V32_ATTACK_CYCLE_FACTOR_MODEL.md`](../../factor_bases/k3_v6_induced/V32_ATTACK_CYCLE_FACTOR_MODEL.md),
  définition, estimation et confirmation du groupe séquentiel V32 ;
- [`../../factor_bases/k3_v6_induced/V32_GENERATION_AUDIT.md`](../../factor_bases/k3_v6_induced/V32_GENERATION_AUDIT.md),
  audit causal V29/V32 : suppression des cycles, mais dégradation harmonique
  qui interdit de promouvoir V32 comme modèle global ;
- [`audit_v33_strong_unlicensed.py`](audit_v33_strong_unlicensed.py),
  fréquence corpus des statuts forts `triad_plus_unlicensed` et
  `other_unlicensed` avant toute transformation en contrainte ;
- [`audit_v33_generation.py`](audit_v33_generation.py),
  audit apparié Bach/V29/V32/V33 de l'ablation stricte ;
- [`../../factor_bases/k3_v6_induced/V33_GENERATION_AUDIT.md`](../../factor_bases/k3_v6_induced/V33_GENERATION_AUDIT.md),
  suppression causale des cinq statuts visés, 66 backtracks et décision de ne
  pas promouvoir une interdiction absolue contredite par Bach ;
- [`audit_v34_named_resolution.py`](audit_v34_named_resolution.py),
  extraction déterministe des familles d'accords nommés, de leur sonorité
  forte suivante et des résolutions de voix observables ;
- [`fit_v34_harmonic_budget.py`](fit_v34_harmonic_budget.py),
  MLE catégoriel, sélection BIC, réplication et budgets binomiaux V34 ;
- [`../../factor_bases/k3_v6_induced/V34_HARMONIC_SEARCH_DECISION.md`](../../factor_bases/k3_v6_induced/V34_HARMONIC_SEARCH_DECISION.md),
  rejet statistique du modèle et diagnostic des deux recherches Snarky
  bornées sans génération complète ;
- [`audit_v29_strong_succession_coverage.py`](audit_v29_strong_succession_coverage.py)
  et [`audit_v30_joint_strong_resolution_coverage.py`](audit_v30_joint_strong_resolution_coverage.py),
  audits de couverture exécutés avant l'ajustement des poids ;
- [`export_v29_strong_succession.py`](export_v29_strong_succession.py),
  export des 137 facteurs confirmés V29 vers Snarky ;
- [`../../../generated/v24_contrastive_bwv108_6_seed_22304_piano.mp3`](../../../generated/v24_contrastive_bwv108_6_seed_22304_piano.mp3),
  exemple V24 BWV 108.6 à 30 balayages, rendu au piano acoustique ;
- [`../../../generated/v16_rank5_local_piano/README.md`](../../../generated/v16_rank5_local_piano/README.md),
  exemple BWV 108.6 à 30 balayages du petit pas V16 utile en régime long,
  rendu explicitement avec un piano acoustique ;
- `v5_1_k3_compact_model.json`, modèle complet pour le Gibbs.

Le protocole complet est
[`../../V5_K3_CLEAN_PROTOCOL.md`](../../V5_K3_CLEAN_PROTOCOL.md), et les
expériences remplacées comme axe principal sont résumées dans
[`../../EXPERIMENT_HISTORY.md`](../../EXPERIMENT_HISTORY.md).
