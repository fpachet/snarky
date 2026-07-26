# Modèle de données CHORAL

Le schéma normatif est `choral_items.schema.json`. Les trois fichiers JSONL
publics contiennent respectivement des unités sources, des cartes et des
tables. Un objet JSON occupe une ligne.

## Unités sources

Une unité est un bloc documentaire ordonné, pas nécessairement une règle.
Elle peut être un titre, paragraphe, exemple, table, entrée de table ou autre
bloc.

Champs essentiels :

- `source_unit_id` : identité stable fondée sur page imprimée et rang ;
- `document_order` : ordre global strict ;
- `pdf_page`, `printed_page` : double pagination ;
- `section_path` : hiérarchie de titres active ;
- `unit_kind`, `unit_index_on_page`, `source_bbox` : nature et ancrage visuel ;
- `correction_status`, `transcription_uncertainties` : état de revue ;
- `corrected_text_sha256` : empreinte du texte privé corrigé ;
- `derived_card_ids` : liens inverses ;
- `short_source_cue` : repère très court, jamais transcription longue.

La contrepartie privée dans `work/source_units.full.jsonl` ajoute
`original_text_ocr`, `original_text_corrected` et les détails de correction.

## Cartes interprétatives

Une carte représente une proposition interprétée. Plusieurs cartes peuvent
provenir d’un même bloc.

- `source_unit_ids` et `source_location` assurent la provenance ;
- `source_classification` distingue label explicite et type normalisé ;
- `faithful_paraphrase` et `atomic_statement` sont des reformulations
  indépendantes ;
- `semantics` décrit vues, portée, conditions, action, exceptions, force et
  polarité ;
- `formalization` prépare variables, prédicats, antécédent, conséquent, faits
  de statut et dépendances ;
- `choral_system_role` situe la phase et la mémoire de travail ;
- `snarky_assessment` évalue la traduction déclarative ;
- `quality` conserve confiance, ambiguïtés et besoins de revue.

Types normalisés :

`production_rule`, `hard_constraint`, `heuristic`, `preference`,
`definition`, `procedure`, `diagnostic`, `search_control`.

## Tables et catalogues

`tables.jsonl` ne contient pas les cellules sources. Il enregistre :

- identité, titre, pages, colonnes et rôle ;
- nombre d’entrées attendu ;
- unités privées qui portent la transcription ;
- empreinte du texte privé agrégé ;
- chemins vers les OCR et le registre corrigé ;
- cartes qui mentionnent ou dérivent de la structure ;
- statut de transcription.

Les sept structures recensées couvrent les accords légaux, clichés, cadences,
tessitures, deux tables de motifs mélodiques et le catalogue typé des
attributs du parseur schenkerien.

Le fichier privé `work/tables.full.jsonl` conserve les lignes/cellules OCR,
leurs boîtes, leur version corrigée et leurs incertitudes. Les frontières de
colonnes musicales que le scan ne permet pas d’établir sûrement restent des
blocs positionnés plutôt que d’être inventées.

## Chaîne de provenance

```text
carte publique
  → source_unit_ids
    → métadonnée publique (page, bbox, statut, SHA-256)
      → unité privée de même ID
        → OCR + texte corrigé + image de page
```

Le validateur contrôle les liens dans les deux sens, les empreintes, la
pagination, l’unicité, l’ordre et la couverture des 78 pages.

## Représentabilité Snarky

Valeurs de `representability` :

- `direct` ;
- `requires_new_local_feature` ;
- `requires_new_status_fact` ;
- `requires_extended_temporal_window` ;
- `global_or_search_dependent` ;
- `procedural_not_declarative`.

Chaque nouveau trait ou statut précise définition, calcul, domaine, localité,
coût conceptuel et risque d’opacité. Un statut n’est acceptable que s’il peut
être calculé et testé indépendamment de la règle qui le consomme. Encoder le
verdict dans une feature contournerait le moteur de règles et est explicitement
signalé comme risque.

## Atomicité, dépendances et ambiguïtés

`atomicity_verified` atteste que la carte porte une seule proposition
opérationnelle au niveau retenu. Ce drapeau ne garantit pas une interprétation
musicologique définitive. Les dépendances inter-cartes sont laissées vides
plutôt que devinées.

Une incertitude OCR est propagée de l’unité aux cartes. Une carte ambiguë garde
`needs_domain_review=true` et une confiance basse ; elle n’est ni supprimée ni
silencieusement corrigée.

## Validation

```sh
python3 tools/validate_extraction.py
```

Le script valide le sous-ensemble Draft 2020-12 utilisé par le schéma, puis :

- l’unicité et la forme des identifiants ;
- l’ordre et la couverture des pages ;
- les liens carte ↔ unité et les références de tables ;
- les empreintes privées lorsqu’elles sont disponibles ;
- l’absence de clés de transcription complète dans les fichiers publics ;
- l’absence de segment public verbatim d’au moins 120 caractères ;
- les cartes non atomiques, ambiguës, illisibles ou à faible confiance.

Les erreurs structurelles provoquent un code de sortie non nul. Les éléments
de revue sont publiés comme constats et n’invalident pas la couverture.
