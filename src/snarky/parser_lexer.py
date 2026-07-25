"""Lexical primitives shared by the Snarky rule parsers."""

from __future__ import annotations

import re
from dataclasses import dataclass


class ParseError(ValueError):
    """Raised when text does not conform to the supported DSL."""


@dataclass(frozen=True, slots=True)
class _Token:
    kind: str
    value: str


_TOKEN_RE = re.compile(
    r"\s*(?:"
    r"(?P<LPAREN>\()|(?P<RPAREN>\))|"
    r"(?P<LBRACKET>\[)|(?P<RBRACKET>\])|"
    r"(?P<OP>==|!=|<=|>=|<|>)|(?P<QUOTE>')|"
    r"(?P<VARIABLE>\$[^\s()\[\]'<>!=]+)|"
    r"(?P<NUMBER>-?(?:\d+(?:\.\d*)?|\.\d+))|"
    r"(?P<ATOM>[^\s()\[\]'<>!=]+)"
    r")"
)
_ARITH_TOKEN_RE = re.compile(
    r"\s*(?:"
    r"(?P<LPAREN>\()|(?P<RPAREN>\))|(?P<OP>[+*/%-])|"
    r"(?P<VARIABLE>\$[^\s()+*/%-]+)|"
    r"(?P<NUMBER>(?:\d+(?:\.\d*)?|\.\d+))"
    r")"
)


def _only_whitespace_remains(text: str, position: int) -> bool:
    while position < len(text):
        if not text[position].isspace():
            return False
        position += 1
    return True


def _normalized_lines(text: str) -> tuple[str, ...]:
    return tuple(
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def _tokenize_arithmetic(text: str) -> tuple[_Token, ...]:
    tokens: list[_Token] = []
    position = 0
    while position < len(text):
        if _only_whitespace_remains(text, position):
            break
        match = _ARITH_TOKEN_RE.match(text, position)
        if match is None:
            raise ParseError(
                f"invalid arithmetic token near {text[position:]!r}"
            )
        kind = match.lastgroup
        if kind is None:
            raise ParseError(
                f"invalid arithmetic token near {text[position:]!r}"
            )
        tokens.append(_Token(kind, match.group(kind)))
        position = match.end()
    if not tokens:
        raise ParseError("expected an arithmetic expression")
    return tuple(tokens)


def _tokenize(text: str) -> tuple[_Token, ...]:
    tokens: list[_Token] = []
    position = 0
    while position < len(text):
        if _only_whitespace_remains(text, position):
            break
        match = _TOKEN_RE.match(text, position)
        if match is None:
            raise ParseError(f"invalid token near {text[position:]!r}")
        kind = match.lastgroup
        if kind is None:
            raise ParseError(f"invalid token near {text[position:]!r}")
        tokens.append(_Token(kind, match.group(kind)))
        position = match.end()
    if not tokens:
        raise ParseError("expected a term")
    return tuple(tokens)
