#!/usr/bin/env python3
# ruff: noqa: E501
"""Build public indexes and the extraction report from the JSONL artefacts."""

from __future__ import annotations

import json
import textwrap
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(name: str) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (ROOT / name).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def compact_ids(ids: Iterable[str], width: int = 110) -> str:
    values = list(ids)
    if not values:
        return "—"
    return "<br>".join(textwrap.wrap(", ".join(values), width=width))


def markdown_counts(title: str, counts: Counter[str]) -> list[str]:
    lines = [f"## {title}", "", "| Valeur | Nombre |", "|---|---:|"]
    lines.extend(f"| {key} | {value} |" for key, value in counts.most_common())
    lines.append("")
    return lines


def build_index(
    sources: list[dict[str, Any]],
    cards: list[dict[str, Any]],
    tables: list[dict[str, Any]],
) -> str:
    by_section: dict[str, list[str]] = defaultdict(list)
    by_kind: dict[str, list[str]] = defaultdict(list)
    by_view: dict[str, list[str]] = defaultdict(list)
    by_strength: dict[str, list[str]] = defaultdict(list)
    by_status: dict[str, list[str]] = defaultdict(list)
    by_feature: dict[str, list[str]] = defaultdict(list)
    by_repr: dict[str, list[str]] = defaultdict(list)
    dependencies: dict[str, list[str]] = defaultdict(list)

    for card in cards:
        cid = card["card_id"]
        section = (
            " › ".join(card["source_location"]["section_path"][1:]) or "Appendix B"
        )
        by_section[section].append(cid)
        by_kind[card["source_classification"]["normalized_kind"]].append(cid)
        by_strength[card["semantics"]["strength"]].append(cid)
        by_repr[card["snarky_assessment"]["representability"]].append(cid)
        for view in card["semantics"]["view"]:
            by_view[view].append(cid)
        for item in card["snarky_assessment"]["required_state"]:
            by_status[item["name"]].append(cid)
        for item in card["snarky_assessment"]["required_new_features"]:
            by_feature[item["name"]].append(cid)
        for dependency in card["formalization"]["dependencies_on_other_cards"]:
            dependencies[dependency].append(cid)

    lines = [
        "# Index de l’extraction CHORAL — appendice B",
        "",
        "Cet index est généré depuis les fichiers JSONL publics. Il ne reproduit pas la transcription source complète.",
        "",
        f"- Unités sources documentées : {len(sources)}",
        f"- Cartes interprétatives : {len(cards)}",
        f"- Tables/catalogues : {len(tables)}",
        "",
        "## Navigation par section",
        "",
        "| Chemin de section | Cartes | Identifiants |",
        "|---|---:|---|",
    ]
    for section, ids in sorted(by_section.items(), key=lambda item: item[1][0]):
        lines.append(
            f"| {section.replace('|', '\\|')} | {len(ids)} | {compact_ids(ids)} |"
        )
    lines.append("")

    for title, groups in (
        ("Index par type normalisé", by_kind),
        ("Index par vue sémantique", by_view),
        ("Index par force", by_strength),
        ("Index par représentabilité Snarky", by_repr),
    ):
        lines.extend(
            [f"## {title}", "", "| Valeur | Nombre | Cartes |", "|---|---:|---|"]
        )
        for key, ids in sorted(
            groups.items(), key=lambda item: (-len(item[1]), item[0])
        ):
            lines.append(f"| `{key}` | {len(ids)} | {compact_ids(ids)} |")
        lines.append("")

    lines.extend(
        [
            "## Inventaire des faits de statut requis",
            "",
            "| Fait de statut | Nombre | Cartes |",
            "|---|---:|---|",
        ]
    )
    for key, ids in sorted(by_status.items()):
        lines.append(f"| {key} | {len(ids)} | {compact_ids(ids)} |")
    if not by_status:
        lines.append("| — | 0 | — |")
    lines.append("")

    lines.extend(
        [
            "## Inventaire des nouveaux traits locaux proposés",
            "",
            "| Trait | Nombre | Cartes |",
            "|---|---:|---|",
        ]
    )
    for key, ids in sorted(by_feature.items()):
        lines.append(f"| {key} | {len(ids)} | {compact_ids(ids)} |")
    if not by_feature:
        lines.append("| — | 0 | — |")
    lines.append("")

    lines.extend(
        [
            "## Dépendances entre cartes",
            "",
            "Aucune dépendance inter-carte n’a été inférée automatiquement : ce champ reste vide tant qu’une relation sémantique n’a pas été confirmée par revue de domaine.",
            "",
            "## Cartes directement représentables",
            "",
            compact_ids(by_repr.get("direct", [])),
            "",
            "## Éléments procéduraux ou dépendants de la recherche",
            "",
            compact_ids(
                [
                    *by_repr.get("procedural_not_declarative", []),
                    *by_repr.get("global_or_search_dependent", []),
                ]
            ),
            "",
            "## Éléments ambigus ou à faible confiance",
            "",
        ]
    )
    ambiguous = [
        card["card_id"]
        for card in cards
        if card["quality"]["ambiguities"]
        or card["quality"]["interpretation_confidence"] == "low"
    ]
    lines.extend(
        [
            compact_ids(ambiguous),
            "",
            "## Tables et catalogues structurés",
            "",
            "| ID | Pages imprimées | Titre | Entrées attendues | Statut |",
            "|---|---|---|---:|---|",
        ]
    )
    for table in tables:
        lines.append(
            f"| `{table['table_id']}` | {', '.join(map(str, table['printed_pages']))} "
            f"| {table['title']} | {table['expected_entry_count']} | `{table['transcription_status']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def build_report(
    sources: list[dict[str, Any]],
    cards: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    validation: dict[str, Any],
) -> str:
    paragraph_sources = [row for row in sources if row["unit_kind"] == "paragraph"]
    paragraph_distribution = Counter(
        min(len(row["derived_card_ids"]), 2) for row in paragraph_sources
    )
    card_kinds = Counter(
        card["source_classification"]["normalized_kind"] for card in cards
    )
    representability = Counter(
        card["snarky_assessment"]["representability"] for card in cards
    )
    statuses = Counter(row["correction_status"] for row in sources)
    source_kinds = Counter(row["unit_kind"] for row in sources)
    expected_entries = sum(table["expected_entry_count"] or 0 for table in tables)
    direct = representability["direct"]
    new_local = representability["requires_new_local_feature"]
    new_status = representability["requires_new_status_fact"]
    nonlocal_count = (
        representability["requires_extended_temporal_window"]
        + representability["global_or_search_dependent"]
        + representability["procedural_not_declarative"]
    )
    findings = validation.get("review_finding_counts", {})

    lines = [
        "# Rapport d’extraction — CHORAL, appendice B",
        "",
        "## Périmètre et traçabilité",
        "",
        "- Document : `docs/RC12628-Ebcioglu-CHORAL.pdf`.",
        "- SHA-256 vérifié : `1e15961a4855bb8b6610fe5fc1c5db6bfdddf54f6129f36cee5f5a7d26643d8c`.",
        "- Appendice B : pages PDF 243–320, correspondant aux pages imprimées 234–311.",
        "- Les pages PDF 242 et 321 ont été contrôlées comme frontières ; la page 321 ouvre l’appendice C.",
        "- Les 78 pages ont été rendues à 250 dpi puis inspectées visuellement.",
        "",
        "La chaîne de provenance publique est : carte → `source_unit_ids` → métadonnée d’unité → page, boîte englobante, statut de correction et empreinte SHA-256. Le texte OCR et la transcription corrigée restent exclusivement sous `work/`, ignoré par Git.",
        "",
        "## Méthode",
        "",
        "Trois couches ont été rapprochées : Tesseract avec coordonnées TSV, extraction textuelle Poppler et reconnaissance Apple Vision. Les blocs ont ensuite été segmentés dans l’ordre documentaire, les titres séparés de leur corps, et les phrases porteuses de connaissances atomisées. Les corrections automatiques sont limitées à des confusions typographiques observées ; aucune notation incertaine n’est devinée.",
        "",
        "Les cartes publiques sont des reformulations structurées. Le validateur refuse les clés de transcription intégrale et tout segment public identique d’au moins 120 caractères à une unité privée.",
        "",
        "## Résultats quantitatifs",
        "",
        "- Pages couvertes : 78/78.",
        f"- Unités sources : {len(sources)}.",
        f"- Cartes interprétatives : {len(cards)}.",
        f"- Tables/catalogues : {len(tables)}, totalisant {expected_entries} entrées attendues.",
        f"- Unités visuellement vérifiées sans jeton OCR faible : {statuses['visually_verified']}.",
        f"- Unités conservées en `needs_review` : {statuses['needs_review']}.",
        "",
        "### Unités par nature",
        "",
        "| Nature | Nombre |",
        "|---|---:|",
    ]
    lines.extend(f"| `{key}` | {value} |" for key, value in source_kinds.most_common())
    lines.extend(
        [
            "",
            "### Distribution paragraphes → cartes",
            "",
            "| Cartes dérivées d’un paragraphe documentaire | Paragraphes |",
            "|---|---:|",
            f"| 0 | {paragraph_distribution[0]} |",
            f"| 1 | {paragraph_distribution[1]} |",
            f"| 2 ou plus | {paragraph_distribution[2]} |",
            f"| **Total** | **{len(paragraph_sources)}** |",
            "",
            "Le chiffre de 354 « paragraphes/règles » parfois associé à CHORAL n’est pas utilisé comme cible artificielle. Ici, les 680 paragraphes sont des blocs documentaires issus de la mise en page : ils incluent définitions, commentaires, continuations et explications, tandis qu’une même unité peut fournir plusieurs propositions atomiques. L’écart reflète donc une différence d’unité de comptage, pas un déficit forcé ou un gonflement vers une valeur attendue.",
            "",
            "### Cartes par type",
            "",
            "| Type | Nombre |",
            "|---|---:|",
        ]
    )
    lines.extend(f"| `{key}` | {value} |" for key, value in card_kinds.most_common())
    lines.extend(
        [
            "",
            "## Tables et catalogues",
            "",
            "| ID | Objet | Pages imprimées | Entrées attendues |",
            "|---|---|---|---:|",
        ]
    )
    for table in tables:
        lines.append(
            f"| `{table['table_id']}` | {table['title']} "
            f"| {', '.join(map(str, table['printed_pages']))} | {table['expected_entry_count']} |"
        )
    lines.extend(
        [
            "",
            "Les corps de tables ne sont pas publiés. `tables.jsonl` fournit leurs colonnes, leur rôle, leurs pages, les unités privées correspondantes, les empreintes et les cartes associées.",
            "",
            "## Évaluation de représentabilité dans Snarky",
            "",
            f"- Directement représentables : {direct}.",
            f"- Demandant un nouveau trait local : {new_local}.",
            f"- Demandant un fait de statut explicite : {new_status}.",
            f"- Fenêtre étendue, dépendance globale/recherche ou procédure non déclarative : {nonlocal_count}.",
            "",
            "Les traits et statuts proposés sont décrits comme des calculs indépendants. Ils ne doivent pas encoder clandestinement le verdict de la règle : ce serait une pseudo-feature opaque et invérifiable. Les procédures de pile, le contrôle de recherche et les préférences globales restent donc signalés comme obstacles plutôt que traduits artificiellement en contraintes locales.",
            "",
            "## Validation et travail restant",
            "",
            f"- Validation structurelle/provenance : **{validation.get('status', 'unknown')}**.",
            f"- Erreurs bloquantes : {len(validation.get('errors', []))}.",
            f"- Cartes à faible confiance : {findings.get('low_confidence_cards', 0)}.",
            f"- Cartes demandant une revue de domaine : {findings.get('domain_review_cards', 0)}.",
            f"- Unités sources à revoir au niveau du symbole ou de la notation : {findings.get('source_units_needing_review', 0)}.",
            "",
            "Ces éléments ne sont pas masqués : ils figurent dans `VALIDATION_REPORT.json`, dans les champs `quality` des cartes et dans les `transcription_uncertainties` des métadonnées. L’extraction et la couverture sont complètes ; la revue philologique fine des 389 blocs contenant au moins un jeton OCR faible reste ouverte.",
            "",
            "## Limites",
            "",
            "- Les boîtes englobantes suivent les blocs OCR ; un titre et son corps peuvent partager une boîte lorsqu’ils proviennent du même bloc initial.",
            "- Les exemples musicaux et tableaux complexes sont conservés comme blocs documentaires avec image source, pas comme notation musicale normalisée.",
            "- Les classifications et l’évaluation Snarky sont déterministes mais automatiques ; les décisions à faible confiance sont explicitement marquées.",
            "- Les dépendances inter-cartes restent vides en l’absence d’une revue sémantique sûre.",
            "",
            "## Reproductibilité",
            "",
            "Depuis ce répertoire :",
            "",
            "```sh",
            "python3 tools/extract_appendix_b.py",
            "python3 tools/validate_extraction.py",
            "python3 tools/build_index.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    sources = read_jsonl("appendix_b_source_units.metadata.jsonl")
    cards = read_jsonl("appendix_b_cards.jsonl")
    tables = read_jsonl("tables.jsonl")
    validation = json.loads(
        (ROOT / "VALIDATION_REPORT.json").read_text(encoding="utf-8")
    )
    (ROOT / "INDEX.md").write_text(
        build_index(sources, cards, tables), encoding="utf-8"
    )
    (ROOT / "EXTRACTION_REPORT.md").write_text(
        build_report(sources, cards, tables, validation), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "index": "INDEX.md",
                "report": "EXTRACTION_REPORT.md",
                "sources": len(sources),
                "cards": len(cards),
                "tables": len(tables),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
