from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SUDOKU_ROOT = PROJECT_ROOT / "sudoku"
CLIPS_PUZZLES = (
    PROJECT_ROOT
    / "third_party/test_rulebases/clips-6.4.2"
    / "clips_examples_642/sudoku/puzzles"
)


def test_sudoku_project_documents_and_rule_catalog_are_localized() -> None:
    assert (SUDOKU_ROOT / "README.md").is_file()
    assert (SUDOKU_ROOT / "docs/implementation_plan.md").is_file()
    assert (SUDOKU_ROOT / "fixtures/README.md").is_file()
    assert (SUDOKU_ROOT / "rules/README.md").is_file()

    catalog = yaml.safe_load(
        (SUDOKU_ROOT / "rules/catalog.yaml").read_text(encoding="utf-8")
    )

    assert catalog["status"] == "planned_non_executable"
    assert [group["name"] for group in catalog["groups"]] == [
        "derive_solved_cells",
        "naked_singles",
        "hidden_singles",
        "locked_candidates_single_line",
        "locked_candidates_multiple_lines",
        "naked_pairs",
        "hidden_pairs",
        "validate_state",
    ]


def test_p1_to_p6_clips_oracles_are_present() -> None:
    for level in range(1, 7):
        assert (CLIPS_PUZZLES / f"grid3x3-p{level}.clp").is_file()
