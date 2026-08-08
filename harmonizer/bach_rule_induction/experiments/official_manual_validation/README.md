# Validation de la base Snarky du manuel Bach

Cette expérience valide le langage et le moteur séparément de l'induction.
La base `official_manual` n'hérite ni de la base historique ni de la base
apprise. Elle utilise les douze extraits authentiques et les douze mutations
contrôlées du manuel externe.

## Couches testées

1. un adaptateur MusicXML sans dépendance à music21 produit des faits
   observables de positions, transitions, fenêtres de trois événements et
   résumés de lignes ;
2. des `RuleGroup` dérivent satisfactions et violations ;
3. des `FactorGroup` purs appliquent uniquement les poids déjà confirmés ;
4. trois profils séparent diagnostic, Bach empirique et pédagogie stricte ;
5. `CHOICE` et le moteur de recherche peuvent rejeter un candidat en conflit,
   revenir en arrière et essayer une autre réalisation ;
6. le vérificateur est indépendant du générateur.

## Exécution

```bash
PYTHONPATH=.:src python \
  harmonizer/bach_rule_induction/experiments/official_manual_validation/run_manual_pair_audit.py
```

Le test différentiel doit augmenter la violation ciblée dans la variante, ou
diminuer la satisfaction ciblée lorsque le chapitre décrit une préférence
positive. Il ne prétend pas encore que les douze règles suffisent pour rendre
une génération musicalement convaincante.

Une partition SATB arbitraire se vérifie sans `music21` avec :

```bash
PYTHONPATH=.:src python \
  harmonizer/bach_rule_induction/experiments/official_manual_validation/audit_score.py \
  partition.musicxml --profile diagnostic --output diagnostic.json
```

Le profil `diagnostic` observe sans rejeter. `pedagogical_strict` transforme
les violations déclarées du profil en contradiction et renvoie le code 2. Les
enveloppes de `bach_empirical` sont gelées après calibration sur `train251`,
promotion sur `validation50` et rapport final séparé sur `test51`.

## Ce qui est validé, et ce qui ne l'est pas

- les douze mutations pédagogiques sont distinguées de leur original par le
  prédicat ciblé : validation différentielle du codage ;
- les facteurs n'ajoutent aucun fait et ne déclenchent aucune règle : ils sont
  une couche de score pure ;
- une violation dure provoque bien un backtrack dans une recherche à choix ;
- les métriques de ligne exposent notamment saut maximal, taux de mouvement
  conjoint et longueur de répétition ;
- les seuils globaux et cinq poids seulement sont encore provisoires : le
  score actuel n'est donc pas un test complet de qualité bachienne.

## Génération homorythmique note à note

Une expérience distincte abandonne tout squelette harmonique. Chaque attaque
du soprano ouvre un seul choix Snarky portant conjointement sur alto, ténor et
basse. Les quatre voix partagent exactement les attaques et durées du soprano ;
chaque position doit être un accord du vocabulaire choisi. Les accords sont
réifiés en domaines finis observables (notes, qualité, fondamentale et
renversement), sans squelette ni état harmonique caché.

Depuis V40, les couches ont des rôles distincts :

- les contraintes du profil strict sont compilées en supports binaires entre
  accords voisins et en filtres ternaires sur les fenêtres de suspension ;
- les retraits de domaine sont des faits persistants Snarky et atteignent un
  point fixe avant chaque `CHOICE` ;
- les 57 facteurs K3 nouvellement décidables sont calculés en batch, puis leur
  pseudo-vraisemblance conditionnelle pondère le `CHOICE` ;
- les cinq facteurs officiels du manuel sont lus depuis le fichier `.factors`
  et ajoutent leur contribution sans produire aucun fait ;
- les critères globaux (sauts, répétitions, mouvement conjoint et budget
  conjoint) fournissent des bornes optimistes capables de déclencher un
  backtrack avant la fin.

Le résultat et ses ablations sont décrits dans
[HOMORHYTHMIC_NOTE_BY_NOTE_RESULT.md](results/HOMORHYTHMIC_NOTE_BY_NOTE_RESULT.md).

Le résultat détaillé de cette architecture est décrit dans
[REIFIED_FACTOR_CONSTRAINT_RESULT.md](results/REIFIED_FACTOR_CONSTRAINT_RESULT.md).
La prochaine étape n'est pas d'ajouter un squelette, mais d'évaluer à l'écoute
la solution stricte, puis de réintroduire accords diminués et septièmes avec
leurs conditions locales de préparation et résolution.

Voir aussi [l'audit Bach/génération](results/FULL_SCORE_COMPARISON.md), qui
mesure explicitement les limites de cette première base.

La calibration et la première génération contrainte sont maintenant
disponibles dans :

- [EMPIRICAL_BUDGET_CALIBRATION.md](results/EMPIRICAL_BUDGET_CALIBRATION.md) ;
- [EMPIRICAL_GENERATION_RESULT.md](results/EMPIRICAL_GENERATION_RESULT.md).
