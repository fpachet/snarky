# Rapport d’extraction — CHORAL, appendice B

## Périmètre et traçabilité

- Document : `docs/RC12628-Ebcioglu-CHORAL.pdf`.
- SHA-256 vérifié : `1e15961a4855bb8b6610fe5fc1c5db6bfdddf54f6129f36cee5f5a7d26643d8c`.
- Appendice B : pages PDF 243–320, correspondant aux pages imprimées 234–311.
- Les pages PDF 242 et 321 ont été contrôlées comme frontières ; la page 321 ouvre l’appendice C.
- Les 78 pages ont été rendues à 250 dpi puis inspectées visuellement.

La chaîne de provenance publique est : carte → `source_unit_ids` → métadonnée d’unité → page, boîte englobante, statut de correction et empreinte SHA-256. Le texte OCR et la transcription corrigée restent exclusivement sous `work/`, ignoré par Git.

## Méthode

Trois couches ont été rapprochées : Tesseract avec coordonnées TSV, extraction textuelle Poppler et reconnaissance Apple Vision. Les blocs ont ensuite été segmentés dans l’ordre documentaire, les titres séparés de leur corps, et les phrases porteuses de connaissances atomisées. Les corrections automatiques sont limitées à des confusions typographiques observées ; aucune notation incertaine n’est devinée.

Les cartes publiques sont des reformulations structurées. Le validateur refuse les clés de transcription intégrale et tout segment public identique d’au moins 120 caractères à une unité privée.

## Résultats quantitatifs

- Pages couvertes : 78/78.
- Unités sources : 1293.
- Cartes interprétatives : 775.
- Tables/catalogues : 7, totalisant 130 entrées attendues.
- Unités visuellement vérifiées sans jeton OCR faible : 904.
- Unités conservées en `needs_review` : 389.

### Unités par nature

| Nature | Nombre |
|---|---:|
| `paragraph` | 680 |
| `heading` | 285 |
| `example` | 197 |
| `other` | 94 |
| `table_entry` | 32 |
| `table` | 5 |

### Distribution paragraphes → cartes

| Cartes dérivées d’un paragraphe documentaire | Paragraphes |
|---|---:|
| 0 | 243 |
| 1 | 298 |
| 2 ou plus | 139 |
| **Total** | **680** |

Le chiffre de 354 « paragraphes/règles » parfois associé à CHORAL n’est pas utilisé comme cible artificielle. Ici, les 680 paragraphes sont des blocs documentaires issus de la mise en page : ils incluent définitions, commentaires, continuations et explications, tandis qu’une même unité peut fournir plusieurs propositions atomiques. L’écart reflète donc une différence d’unité de comptage, pas un déficit forcé ou un gonflement vers une valeur attendue.

### Cartes par type

| Type | Nombre |
|---|---:|
| `production_rule` | 213 |
| `hard_constraint` | 213 |
| `heuristic` | 128 |
| `diagnostic` | 97 |
| `procedure` | 79 |
| `search_control` | 26 |
| `preference` | 11 |
| `definition` | 8 |

## Tables et catalogues

| ID | Objet | Pages imprimées | Entrées attendues |
|---|---|---|---:|
| `CHORAL-TABLE-P0239-T01` | Legal chord spellings by degree in C major and A minor | 239, 240 | 24 |
| `CHORAL-TABLE-P0245-T01` | Catalogue of phrase-ending and mid-phrase cliché patterns | 245, 246, 247, 248 | 11 |
| `CHORAL-TABLE-P0250-T01` | Cadence patterns | 250, 251 | 67 |
| `CHORAL-TABLE-P0254-T01` | Allowable ranges of the four voices | 254 | 4 |
| `CHORAL-TABLE-P0285-T01` | Permitted sharpened-sixth melodic-minor patterns | 285 | 5 |
| `CHORAL-TABLE-P0285-T02` | Permitted flattened-seventh melodic-minor patterns | 285 | 4 |
| `CHORAL-TABLE-P0297-T01` | Schenkerian parser function and attribute catalogue | 297, 298, 299 | 15 |

Les corps de tables ne sont pas publiés. `tables.jsonl` fournit leurs colonnes, leur rôle, leurs pages, les unités privées correspondantes, les empreintes et les cartes associées.

## Évaluation de représentabilité dans Snarky

- Directement représentables : 239.
- Demandant un nouveau trait local : 63.
- Demandant un fait de statut explicite : 232.
- Fenêtre étendue, dépendance globale/recherche ou procédure non déclarative : 241.

Les traits et statuts proposés sont décrits comme des calculs indépendants. Ils ne doivent pas encoder clandestinement le verdict de la règle : ce serait une pseudo-feature opaque et invérifiable. Les procédures de pile, le contrôle de recherche et les préférences globales restent donc signalés comme obstacles plutôt que traduits artificiellement en contraintes locales.

## Validation et travail restant

- Validation structurelle/provenance : **pass**.
- Erreurs bloquantes : 0.
- Cartes à faible confiance : 276.
- Cartes demandant une revue de domaine : 293.
- Unités sources à revoir au niveau du symbole ou de la notation : 389.

Ces éléments ne sont pas masqués : ils figurent dans `VALIDATION_REPORT.json`, dans les champs `quality` des cartes et dans les `transcription_uncertainties` des métadonnées. L’extraction et la couverture sont complètes ; la revue philologique fine des 389 blocs contenant au moins un jeton OCR faible reste ouverte.

## Limites

- Les boîtes englobantes suivent les blocs OCR ; un titre et son corps peuvent partager une boîte lorsqu’ils proviennent du même bloc initial.
- Les exemples musicaux et tableaux complexes sont conservés comme blocs documentaires avec image source, pas comme notation musicale normalisée.
- Les classifications et l’évaluation Snarky sont déterministes mais automatiques ; les décisions à faible confiance sont explicitement marquées.
- Les dépendances inter-cartes restent vides en l’absence d’une revue sémantique sûre.

## Reproductibilité

Depuis ce répertoire :

```sh
python3 tools/extract_appendix_b.py
python3 tools/validate_extraction.py
python3 tools/build_index.py
```
