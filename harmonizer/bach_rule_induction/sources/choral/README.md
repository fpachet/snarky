# Extraction structurée de l’appendice B de CHORAL

Ce répertoire fournit un inventaire exploitable et traçable de l’appendice B
du rapport d’Ebcioğlu, sans publier la transcription complète de la source.

## Périmètre

- PDF local : `docs/RC12628-Ebcioglu-CHORAL.pdf`
- SHA-256 attendu :
  `1e15961a4855bb8b6610fe5fc1c5db6bfdddf54f6129f36cee5f5a7d26643d8c`
- pages PDF : 243–320 incluses
- pages imprimées : 234–311 incluses
- contenu : règles de production, contraintes, heuristiques, définitions,
  procédures, commentaires diagnostiques et tables de l’appendice B

Les pages 242 et 321 ont servi au contrôle des frontières. Les 78 pages du
périmètre ont été rendues et inspectées visuellement.

## Fichiers publics

- `appendix_b_source_units.metadata.jsonl` : registre des unités sources sans
  leur texte complet ;
- `appendix_b_cards.jsonl` : cartes interprétatives atomiques et paraphrasées ;
- `tables.jsonl` : métadonnées des tables et catalogues structurés ;
- `choral_items.schema.json` : schéma JSON des trois types d’enregistrement ;
- `INDEX.md` : index par section, type, vue, force, statut et
  représentabilité ;
- `EXTRACTION_REPORT.md` : méthode, couverture, statistiques, limites et
  résultats ;
- `VALIDATION_REPORT.json` : validation machine et listes de revue ;
- `PROGRESS.json` : état reproductible de l’extraction.

Chaque carte pointe vers une ou plusieurs unités par `source_unit_ids`.
Chaque unité publique fournit page PDF, page imprimée, chemin de section,
boîte englobante, statut de correction, incertitudes, empreinte du texte
corrigé et liens réciproques vers ses cartes.

## Espace de travail privé

`work/` est ignoré par Git. Il contient :

- `page_images/` : rendus PNG à 250 dpi ;
- `ocr/` : texte Tesseract, TSV avec coordonnées, texte Poppler et sorties
  Apple Vision ;
- `source_units.full.jsonl` : OCR brut et transcription corrigée, avec la même
  identité que les métadonnées publiques ;
- `tables.full.jsonl` : lignes/cellules OCR positionnées, corrections,
  incertitudes et liens d’unités pour les sept structures ;
- le binaire temporaire de reconnaissance Vision.

La transcription intégrale et les corps de tables ne doivent pas sortir de
`work/`. Les fichiers publics n’exposent que des reformulations, de courts
repères, des emplacements, des empreintes et des classifications.

## Reconstruction

Les artefacts publics peuvent être reconstruits à partir du contenu privé déjà
présent :

```sh
python3 tools/extract_appendix_b.py
python3 tools/validate_extraction.py
python3 tools/build_index.py
```

Pour reconstruire les images depuis la racine du dépôt :

```sh
pdftoppm -f 243 -l 320 -r 250 -gray -png \
  docs/RC12628-Ebcioglu-CHORAL.pdf \
  harmonizer/bach_rule_induction/sources/choral/work/page_images/page
```

Tesseract est exécuté par page avec `eng`, `--psm 3`, sortie texte et TSV.
`pdftotext -layout` apporte une seconde couche. `tools/vision_ocr.swift`
produit la troisième couche sur macOS. `extract_appendix_b.py` est
déterministe à entrées identiques.

## Statuts de correction

- `raw_ocr` : sortie non contrôlée ;
- `ocr_checked` : contrôles textuels croisés ;
- `visually_verified` : page inspectée et aucun jeton faible restant dans
  l’unité ;
- `needs_review` : notation ou jeton OCR faible conservé explicitement.

La couverture est complète, mais `needs_review` ne signifie pas « corrigé par
supposition ». Le bloc, son image, ses OCR concurrents et son empreinte restent
disponibles pour une revue philologique ciblée.

## Identifiants stables

- unité source : `CHORAL-B-P0234-U001` ;
- carte : `CHORAL-CARD-0001` ;
- table : `CHORAL-TABLE-P0239-T01`.

Le numéro `P` emploie la pagination imprimée. `document_order` et
`unit_index_on_page` rendent l’ordre documentaire explicite. Les identifiants
ne dépendent pas de la classification interprétative.

## Droits et usage

Les droits de redistribution du rapport et d’une transcription complète ne
sont pas établis. Le PDF, les images, les OCR et le texte corrigé doivent donc
rester des matériaux de travail locaux. Le catalogue versionnable est une
œuvre de repérage et d’analyse : métadonnées factuelles, courts indices,
paraphrases indépendantes et formalisation.

Cette extraction documente CHORAL comme baseline historique. Elle ne confère
pas automatiquement le statut `MUST` à une règle et ne transforme pas les
procédures de recherche en pseudo-features opaques.
