"""Generic snapshot codecs for Python objects."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, TypeVar

from ..facts import Fact
from ..terms import Atom

T = TypeVar("T")


class FactCodec(Protocol[T]):
    """Project one Python object to facts and materialize a fresh snapshot.

    Codecs never mutate the source object. During inference the fact set is
    the authoritative branch-local state; ``decode`` constructs a new Python
    object from any selected solution.
    """

    def encode(
        self,
        value: T,
        *,
        identity: Atom,
    ) -> tuple[Fact, ...]: ...

    def decode(
        self,
        identity: Atom,
        facts: Iterable[Fact],
    ) -> T: ...
