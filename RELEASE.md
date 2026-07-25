# Release procedure

No public release may be tagged or uploaded while a mandatory gate below is
open.

## Legal and provenance gates

- [ ] Select and add the project `LICENSE`.
- [ ] Confirm contributor rights for the intended license.
- [ ] Update `pyproject.toml` and `CITATION.cff` with the license.
- [ ] Resolve or remove every `review required` item in `THIRD_PARTY.md`.
- [ ] Verify that required third-party notices accompany any released corpus.
- [ ] Confirm that no private reference document appears in the Git tag.

## Version and documentation

- [ ] Choose a Semantic Versioning number and update `pyproject.toml`.
- [ ] Move relevant entries from `Unreleased` in `CHANGELOG.md`.
- [ ] Review the stable, advanced, integration, and experimental API lists.
- [ ] Verify README examples and all local documentation links.
- [ ] Update `CITATION.cff` with the final version and release date.

## Quality and distribution

```sh
ruff check .
mypy src
pytest
python scripts/check_markdown_links.py
python -m build --outdir dist
python scripts/check_distribution.py dist
python scripts/check_wheel_install.py dist
```

- [ ] Run representative differential benchmarks and archive raw results.
- [ ] Inspect wheel and sdist contents.
- [ ] Install the wheel in an isolated environment away from the checkout.
- [ ] Verify that PDF/PPT/DOC references, third-party corpora, Spinoza source
      texts, generated music, and benchmark results are absent.
- [ ] Check the GitHub Actions quality workflow on the release commit.

## Publication

- [ ] Create a signed or annotated `vX.Y.Z` tag only after all gates pass.
- [ ] Build artifacts from that exact tag.
- [ ] Upload with provenance attestations appropriate to the target registry.
- [ ] Create GitHub release notes from the changelog.
- [ ] Verify installation from the public artifact.

Until the legal gates are resolved, local builds are validation artifacts only
and must not be uploaded to a package index.
