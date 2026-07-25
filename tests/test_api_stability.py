import snarky
from snarky.api_stability import (
    ADVANCED_API,
    EXPERIMENTAL_API,
    INTEGRATION_API,
    LEGACY_TOP_LEVEL_API,
    STABLE_CORE_API,
)


def test_api_categories_are_disjoint_and_cover_legacy_exports() -> None:
    categories = (
        STABLE_CORE_API,
        ADVANCED_API,
        INTEGRATION_API,
        EXPERIMENTAL_API,
    )

    for index, category in enumerate(categories):
        for other in categories[index + 1 :]:
            assert category.isdisjoint(other)
    assert frozenset(snarky._LEGACY_ALL) == LEGACY_TOP_LEVEL_API


def test_wildcard_api_contains_only_the_stable_core() -> None:
    assert snarky.__all__ == sorted(STABLE_CORE_API)


def test_legacy_explicit_imports_remain_available() -> None:
    for name in LEGACY_TOP_LEVEL_API:
        assert getattr(snarky, name) is not None
