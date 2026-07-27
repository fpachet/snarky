from pathlib import Path

from snarky import parse_rule_groups
from snarky.cli import main
from snarky.formatting import format_source
from snarky.tooling import (
    DiagnosticSeverity,
    discover_source_files,
    validate_paths,
    validate_source,
)


def test_formatter_preserves_comments_and_canonicalizes_blocks() -> None:
    source = """\
GROUP example
# group comment
RULE reject
WHEN
(item state open)
NOT EXISTS
(item blocked true)
END_EXISTS
THEN
ADD (item state accepted)
END
END_GROUP
"""
    expected = """\
GROUP example
    # group comment
    RULE reject
    WHEN
        (item state open)
        NOT EXISTS
            (item blocked true)
        END_NOT_EXISTS
    THEN
        ADD (item state accepted)
    END
END_GROUP
"""

    formatted = format_source(source)

    assert formatted == expected
    assert format_source(formatted) == formatted
    assert parse_rule_groups(formatted) == parse_rule_groups(source)


def test_formatter_understands_program_steps_and_constraint_scopes() -> None:
    program = """\
PROGRAM example
STEP solve
GROUP choices
CONSTRAINT domains
END_STEP
END_PROGRAM
"""
    constraint = """\
CONSTRAINT distinct
KIND ALL_DIFFERENT
SCOPE $variable
FROM
($variable kind cell)
END_SCOPE
END
"""

    assert format_source(program) == """\
PROGRAM example
    STEP solve
        GROUP choices
        CONSTRAINT domains
    END_STEP
END_PROGRAM
"""
    assert format_source(constraint) == """\
CONSTRAINT distinct
KIND ALL_DIFFERENT
SCOPE $variable
FROM
    ($variable kind cell)
END_SCOPE
END
"""


def test_validator_reports_the_line_of_a_malformed_action() -> None:
    source = """\
RULE broken
WHEN
    (item state open)
THEN
    REPLACE (item state closed)
END
"""

    diagnostics = validate_source(source, path="broken.rules")

    assert len(diagnostics) == 1
    assert diagnostics[0].severity is DiagnosticSeverity.ERROR
    assert diagnostics[0].code == "SNK100"
    assert diagnostics[0].line == 5
    assert diagnostics[0].column == 5
    assert "unsupported action" in diagnostics[0].message


def test_validator_warns_about_the_legacy_not_exists_terminator() -> None:
    source = """\
RULE accepted_legacy_form
WHEN
    (item state open)
    NOT EXISTS
        (item blocked true)
    END_EXISTS
THEN
    ADD (item state accepted)
END
"""

    diagnostics = validate_source(source, path="legacy.rules")

    assert len(diagnostics) == 1
    assert diagnostics[0].severity is DiagnosticSeverity.WARNING
    assert diagnostics[0].code == "SNK101"
    assert diagnostics[0].line == 6


def test_project_validation_can_make_program_links_strict(
    tmp_path: Path,
) -> None:
    rules = tmp_path / "groups.rules"
    rules.write_text(
        """\
GROUP declared
    RULE noop
    WHEN
        (item state open)
    THEN
        ADD (item state closed)
    END
END_GROUP
""",
        encoding="utf-8",
    )
    program = tmp_path / "solver.program"
    program.write_text(
        """\
PROGRAM solver
    PREPARE declared
    PROPAGATE supplied_by_python
END_PROGRAM
""",
        encoding="utf-8",
    )

    ordinary = validate_paths((tmp_path,))
    strict = validate_paths((tmp_path,), strict_links=True)

    assert ordinary.ok
    assert ordinary.warnings[0].code == "SNK201"
    assert ordinary.warnings[0].line == 3
    assert not strict.ok
    assert strict.errors[0].code == "SNK201"


def test_constraint_validation_uses_the_companion_parser() -> None:
    diagnostics = validate_source(
        """\
CONSTRAINT distinct
KIND ALL_DIFFERENT
SCOPE $variable
FROM
    ($variable kind cell)
END_SCOPE
END
""",
        path="distinct.constraints",
    )

    assert diagnostics == ()


def test_cli_check_and_format_modes(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "example.rules"
    source.write_text(
        """\
RULE close
WHEN
(item state open)
THEN
ADD (item state closed)
END
""",
        encoding="utf-8",
    )

    assert main(("format", "--check", str(source))) == 1
    assert "would reformat" in capsys.readouterr().out
    assert main(("format", str(source))) == 0
    assert main(("check", "--format", str(source))) == 0
    assert source.read_text(encoding="utf-8") == """\
RULE close
WHEN
    (item state open)
THEN
    ADD (item state closed)
END
"""


def test_discovery_skips_vendored_directories(tmp_path: Path) -> None:
    source = tmp_path / "kept.rules"
    source.write_text("", encoding="utf-8")
    vendored = tmp_path / "third_party" / "ignored.rules"
    vendored.parent.mkdir()
    vendored.write_text("", encoding="utf-8")

    assert discover_source_files((tmp_path,)) == (source,)


def test_validation_rejects_missing_and_unsupported_paths(
    tmp_path: Path,
) -> None:
    unsupported = tmp_path / "rules.txt"
    unsupported.write_text("", encoding="utf-8")

    result = validate_paths((tmp_path / "missing.rules", unsupported))

    assert [diagnostic.code for diagnostic in result.errors] == [
        "SNK002",
        "SNK003",
    ]
