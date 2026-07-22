# Prompt Codex — Reconstruction de la partie III de l’Éthique de Spinoza

## Mission générale

Utiliser la partie III de l’*Éthique* de Spinoza comme corpus de référence et banc d’essai d’un moteur de règles inspiré de SNARK et BOOJUM.

L’objectif est de :

1. reconstruire une base de faits et de règles à partir du texte ;
2. distinguer les règles explicitement formulées par Spinoza des règles interprétatives ajoutées par le formalisateur ;
3. vérifier automatiquement certaines démonstrations par chaînage avant ;
4. retrouver et étendre le travail historique *Spinolog*, réalisé en 1987 par Michel Gondran et Fabrice Cavarretta en SNARK puis implémenté en BOOJUM ;
5. tester en particulier les règles d’ordre 2, dans lesquelles des propositions complètes apparaissent comme objets d’autres propositions.

La présentation historique fournie montre une formalisation du début de la partie III et des démonstrations des propositions 19, 21, 22 et 33, avec un objectif annoncé couvrant les propositions 19 à 55.

---

## 1. Objectifs scientifiques

Le projet doit permettre de répondre aux questions suivantes :

- Quelles parties des démonstrations de Spinoza peuvent être représentées comme des règles explicites ?
- Quelles étapes nécessitent des règles implicites ou interprétatives ?
- Les démonstrations peuvent-elles être reproduites par un moteur de chaînage avant ?
- Certaines règles utilisées historiquement dans SNARK/BOOJUM sont-elles plus fortes que le texte de Spinoza ?
- Certaines propositions sont-elles obtenues de plusieurs manières ?
- Quelles dépendances entre propositions, définitions, postulats, corollaires et scolies sont effectivement nécessaires ?
- Le moteur peut-il expliquer pourquoi une proposition n’est pas démontrable à partir de la base disponible ?
- La formalisation révèle-t-elle des lacunes, ambiguïtés, cycles ou engagements interprétatifs cachés ?

---

## 2. Corpus de référence

Le corpus principal sera constitué de la partie III de l’*Éthique*, « De l’origine et de la nature des affections ».

Il doit inclure :

- les définitions initiales ;
- les postulats ;
- les propositions 1 à 59 ;
- leurs démonstrations ;
- leurs corollaires ;
- leurs scolies ;
- les définitions des affects placées à la fin de la partie III.

Choisir une traduction française principale, probablement celle de Charles Appuhn, tout en conservant :

- le texte source exact ;
- la référence canonique ;
- la possibilité de comparer avec le latin ;
- la possibilité de comparer avec une autre traduction.

Chaque unité textuelle doit comporter :

```yaml
id: E3P21
type: proposition
source_text: "..."
translation: Appuhn
references:
  - E3P13S
  - E3P19
formalization_status: candidate
```

Types possibles :

- `definition`
- `postulate`
- `axiom`
- `proposition`
- `demonstration`
- `corollary`
- `scholium`
- `definition_of_affect`

---

## 3. Principe méthodologique

Ne pas convertir immédiatement chaque proposition en une règle contenant déjà sa conclusion.

Pour tester réellement le moteur, une proposition doit être traitée comme un théorème à démontrer à partir :

- des définitions ;
- des postulats ;
- des propositions antérieures ;
- des règles de compilation logique autorisées ;
- des éventuelles règles interprétatives explicitement déclarées.

Par exemple, la proposition 19 ne doit pas être validée en ajoutant directement :

```text
SI x aime y
ET x imagine (y est détruit)
ALORS x est triste
```

Elle doit, autant que possible, être obtenue en plusieurs étapes à partir de la définition de l’amour et des règles antérieures pertinentes.

---

## 4. Représentation des connaissances

### 4.1 Faits simples

Utiliser des triplets récursifs :

```text
(x aime y)
(x hait y)
(x est_semblable_à y)
(x est joyeux)
(x est triste)
```

### 4.2 Faits portant sur des faits

Le moteur doit pouvoir représenter :

```text
(x imagine (y est existant))
(x imagine (y est inexistant))
(x imagine (y est triste))
(x imagine (z affecte_de_joie y))
(x s_efforce_que (y est existant))
(x s_efforce_que (y aime x))
```

Une proposition complète peut donc apparaître comme troisième élément d’un autre triplet.

### 4.3 Contextes intentionnels

Ne jamais appliquer implicitement le schéma :

```text
x imagine P
donc P
```

Distinguer au minimum :

```text
P
x imagine P
x croit P
x s_efforce_que P
x désire P
x nie P
```

Les règles doivent préserver ces contextes.

### 4.4 Statuts

Prendre en charge au minimum :

- `VRAI`
- `FAUX`
- `INEXISTANT`
- `INCONNU`

Ne pas assimiler :

- l’absence d’un fait ;
- un fait faux ;
- un objet inexistant ;
- une valeur inconnue.

### 4.5 Ordres de règles

Supporter :

- ordre 0 : aucune variable ;
- ordre 1 : variables représentant des individus ou des valeurs ;
- ordre 2 : variables représentant des relations ou des propositions complètes.

Exemple d’ordre 2 :

```text
SI    x imagine (z affecte_de_joie y)
ET    x porte_sentiment_à y
ET    x est_semblable_à y
ALORS x imagine (z affecte_de_joie x)
```

---

## 5. Typologie des règles extraites

Toute règle doit recevoir une catégorie explicite.

### A. Règle textuelle

La règle correspond directement à une définition, un postulat, une proposition ou une phrase identifiable de Spinoza.

```yaml
origin: textual
source: E3P13S
```

### B. Règle de compilation

La règle explicite une opération logique ou représentationnelle nécessaire à l’exécution :

- instanciation universelle ;
- substitution ;
- égalité ;
- symétrie déclarée ;
- normalisation lexicale ;
- décomposition d’un triplet.

```yaml
origin: compilation
```

### C. Règle interprétative

La règle est introduite pour rendre la démonstration exécutable, mais n’est pas explicitement énoncée par Spinoza.

```yaml
origin: interpretative
justification: "..."
```

Une règle interprétative ne doit jamais être ajoutée silencieusement.

### D. Règle historique

La règle provient de la présentation SNARK/BOOJUM ou d’une autre reconstruction historique, mais sa fidélité au texte doit encore être évaluée.

```yaml
origin: historical_model
source: Spinolog
```

---

## 6. Workflow d’extraction

Pour chaque proposition :

1. enregistrer le texte de la proposition ;
2. enregistrer sa démonstration ;
3. identifier les références explicites ;
4. segmenter la démonstration en étapes ;
5. déterminer les faits initiaux ou hypothèses ;
6. formaliser la conclusion attendue ;
7. extraire des règles candidates ;
8. classifier chaque règle ;
9. exécuter le moteur ;
10. comparer la preuve obtenue avec le texte ;
11. signaler les étapes non justifiées ;
12. proposer, sans les valider automatiquement, les règles manquantes éventuelles.

Le LLM peut proposer les formalismes, mais le moteur symbolique décide si la conclusion est dérivable.

---

## 7. Usage du LLM

Le LLM peut être utilisé pour :

- segmenter les démonstrations ;
- reconnaître les références ;
- proposer des prédicats normalisés ;
- suggérer des règles candidates ;
- repérer des variantes lexicales ;
- identifier des étapes implicites ;
- comparer la preuve produite avec le texte ;
- générer une explication lisible.

Workflow obligatoire :

```text
Texte source
    ↓
Extraction candidate par le LLM
    ↓
Formalisation structurée
    ↓
Validation humaine ou automatique
    ↓
Exécution par le moteur
    ↓
Comparaison avec la conclusion attendue
```

Une règle générée par le LLM doit rester `candidate` tant qu’elle n’a pas été validée.

---

## 8. Exemples historiques initiaux

### 8.1 Amour

Règle historique candidate :

```text
SI    x aime y
ALORS x imagine (y affecte_de_joie x)
```

Réciproque historique candidate :

```text
SI    x imagine (y affecte_de_joie x)
ET    x != y
ALORS x aime y
```

Vérifier si cette réciprocité est directement justifiée par le texte ou relève d’une reconstruction.

### 8.2 Haine

```text
SI    x hait y
ALORS x imagine (y affecte_de_tristesse x)
```

### 8.3 Proposition 19

Conclusion attendue :

```text
SI    x aime y
ET    x imagine (y est inexistant)
ALORS x est triste
```

Mais la preuve de test doit passer par au moins une étape intermédiaire :

```text
x aime y
→ x imagine (y affecte_de_joie x)
```

puis par une règle reliant la destruction imaginée de la cause de joie à la tristesse.

### 8.4 Proposition 21

```text
SI    x aime y
ET    x imagine (y est joyeux)
ALORS x est joyeux
```

Version négative :

```text
SI    x aime y
ET    x imagine (y est triste)
ALORS x est triste
```

### 8.5 Proposition 22

```text
SI    x aime y
ET    x imagine (z affecte_de_joie y)
ALORS x aime z
```

Version négative :

```text
SI    x aime y
ET    x imagine (z affecte_de_tristesse y)
ALORS x hait z
```

### 8.6 Proposition 33

```text
SI    x aime y
ET    x est_semblable_à y
ALORS x s_efforce_que (y aime x)
```

Ce test doit être reconstruit par plusieurs étapes et servir de test de chaînage profond.

---

## 9. Création d’objets

La présentation historique contient une action de type :

```text
Créer(z)
```

Le projet doit déterminer sa sémantique exacte ou proposer une reconstruction explicite parmi :

- constante fraîche ;
- témoin existentiel ;
- terme de Skolem ;
- objet local à une preuve ;
- objet persistant ajouté à la base.

Chaque usage doit être traçable et borné pour éviter une création infinie.

---

## 10. Algèbre des affects

La reconstruction historique semble exploiter des oppositions :

- joie / tristesse ;
- amour / haine ;
- existence / destruction ;
- augmentation / diminution de puissance.

Étudier si certaines règles peuvent être généralisées par une polarité :

```text
polarité(joie) = +1
polarité(tristesse) = -1
polarité(amour) = +1
polarité(haine) = -1
```

Mais ne pas imposer cette représentation si elle ne respecte pas le texte.

Comparer deux modèles :

1. règles explicites séparées ;
2. règles génériques paramétrées par polarité.

---

## 11. Production et validation des preuves

Pour chaque fait dérivé, stocker :

- la règle utilisée ;
- la substitution ;
- les prémisses ;
- la profondeur ;
- le cycle d’inférence ;
- le statut de chaque règle ;
- les références textuelles.

Exemple :

```text
1. x0 aime y0
   HYPOTHÈSE

2. x0 imagine (y0 est inexistant)
   HYPOTHÈSE

3. x0 imagine (y0 affecte_de_joie x0)
   PAR règle E3-amour
   DE 1

4. x0 est triste
   PAR règle E3-destruction-cause-de-joie
   DE 2, 3
```

Le système doit pouvoir signaler :

- preuve réussie ;
- preuve impossible ;
- preuve dépendant d’une règle interprétative ;
- preuve cyclique ;
- preuve comportant une règle plus forte que la proposition ;
- plusieurs preuves alternatives.

---

## 12. Protocole expérimental

### Palier A — Reproduction historique

Reproduire les démonstrations présentes dans les diapositives :

- E3P19 ;
- E3P21 ;
- E3P22 ;
- E3P33.

### Palier B — Propositions 19 à 59 — réalisé

Formaliser et tester les propositions 19 à 59. Ce palier est désormais
exécutable dans `spinoza/systematic/`, avec provenance et contre-cas.

Pour chaque proposition, produire un statut :

```yaml
result: proved
```

ou :

```yaml
result: not_proved
missing:
  - "..."
```

ou :

```yaml
result: proved_with_interpretative_rules
rules:
  - "..."
```

### Palier C — Propositions 1 à 18 — réalisé

Revenir aux propositions précédentes afin de reconstruire les prémisses
utilisées par 19 à 59. Ce socle est désormais lui aussi exécutable.

### Palier D — Analyse critique — réalisée pour les propositions

Comparer :

- le texte de Spinoza ;
- le modèle historique Spinolog ;
- la nouvelle formalisation ;
- la preuve générée.

Les rapports de `spinoza/systematic/reports/` consignent cette comparaison
jusqu'à E3P59. La formalisation des définitions finales E3DA01–E3DA48 reste un
chantier séparé.

---

## 13. Structure de dépôt proposée

```text
spinoza/
  README.md

  sources/
    ethics_III_fr.txt
    ethics_III_latin.txt
    passages.json
    bibliography.yaml

  ontology/
    predicates.yaml
    affect_relations.yaml
    oppositions.yaml
    lexical_variants.yaml

  rules/
    textual.rules
    historical.rules
    compilation.rules
    interpretative.rules
    candidates.rules

  theorems/
    E3P01.yaml
    E3P02.yaml
    ...
    E3P59.yaml

  proofs/
    historical/
    generated/
    failed/

  extraction/
    prompts/
    raw_llm_outputs/
    normalized/

  reports/
    coverage.md
    missing_rules.md
    interpretative_rules.md
    divergences.md
    dependency_graph.md
```

---

## 14. Format d’un théorème

Exemple :

```yaml
id: E3P19
title: "..."
source_text: "..."

initial_facts:
  - "(x0 aime y0)"
  - "(x0 imagine (y0 est inexistant))"

goal:
  - "(x0 est triste)"

allowed_rule_origins:
  - textual
  - compilation
  - historical_model

forbidden_rules:
  - E3P19_as_direct_rule

expected:
  status: proved
  minimum_depth: 2

historical_proof:
  available: true
  source: Spinolog
```

---

## 15. Critères d’acceptation

Le corpus est considéré comme opérationnel lorsque :

1. les preuves historiques de E3P19, E3P21, E3P22 et E3P33 sont reproduites ;
2. les objets propositionnels imbriqués sont préservés ;
3. les contextes `imagine` et `s_efforce_que` ne sont pas aplatis ;
4. les règles d’ordre 2 sont nécessaires dans au moins un test ;
5. chaque règle possède une provenance ;
6. les règles interprétatives sont identifiées ;
7. une proposition ne peut pas être utilisée pour se démontrer elle-même ;
8. le système explique les échecs ;
9. les dépendances entre propositions sont exportables ;
10. les effets d’une modification de règle sont recalculés automatiquement.

---

## 16. Première tâche à exécuter

Commencer par :

1. créer la structure du corpus ;
2. importer la présentation historique comme source ;
3. extraire manuellement ou semi-automatiquement les règles visibles dans les diapositives ;
4. marquer ces règles `historical_model` ;
5. créer les fichiers de test E3P19, E3P21, E3P22 et E3P33 ;
6. vérifier les références exactes dans le texte de la partie III ;
7. signaler les divergences entre les diapositives et le texte ;
8. produire `reports/historical_reconstruction.md` ;
9. ne lancer l’extraction exhaustive qu’après validation de ces quatre cas.
