# Contributing

Snarky welcomes focused research and engineering contributions, but the
project is still pre-release and has not selected a redistribution license.
Discuss substantial work in a GitHub issue before investing in it.

## Development setup

```sh
git clone https://github.com/fpachet/snarky.git
cd snarky
python -m pip install -e ".[dev]"
snarky check --syntax-only --format .
pytest
ruff check .
mypy src
```

Python 3.12 or newer is required.

## Change requirements

- preserve deterministic observable semantics unless the change explicitly
  proposes a versioned semantic revision;
- compare optimized inference behavior with the naive reference;
- add direct tests for bug fixes and public behavior;
- record raw A/B measurements for performance claims;
- keep domain knowledge outside `src/snarky`;
- write publication-facing engine and application documentation in English;
- keep the Spinoza corpus and its French formalization in French;
- update `CHANGELOG.md` for user-facing changes.

Run the complete local gate before requesting review:

```sh
snarky check --syntax-only --format .
ruff check .
mypy src
pytest
python scripts/check_markdown_links.py
python -m build --outdir dist
python scripts/check_distribution.py dist
python scripts/check_wheel_install.py dist
```

## External material

Do not add papers, books, presentations, datasets, rule corpora, media, or
other third-party files without the provenance and redistribution information
required by [THIRD_PARTY.md](THIRD_PARTY.md). A public URL is not sufficient
evidence of permission.

Generated artifacts belong in an ignored output directory unless a documented
scientific-reproducibility reason requires tracking them.

## Contribution rights

By submitting a contribution, you affirm that you created it or otherwise have
the right to submit it. Because the project license is unresolved, acceptance
of a contribution does not imply that the repository may already be
redistributed. The licensing decision and any contributor agreement must be
settled before a public release.
