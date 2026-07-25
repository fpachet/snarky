"""Recursive term parsing for the Snarky rule language."""

from __future__ import annotations

from .parser_lexer import ParseError, _Token, _tokenize
from .terms import (
    Atom,
    FiniteSequence,
    FiniteSet,
    Number,
    Status,
    Term,
    Triple,
    Variable,
)

_STATUSES = {status.value: status for status in Status}


def parse_term(text: str) -> Term:
    """Parse exactly one recursive term without using ``eval``."""

    return _parse_all(_tokenize(text))


def _parse_all(tokens: tuple[_Token, ...]) -> Term:
    term, position = _parse_term_tokens(tokens, 0)
    if position != len(tokens):
        raise ParseError(f"unexpected token {tokens[position].value!r}")
    return term


def _parse_term_tokens(
    tokens: tuple[_Token, ...],
    position: int,
) -> tuple[Term, int]:
    if position >= len(tokens):
        raise ParseError("expected a term")
    token = tokens[position]
    if token.kind == "LPAREN":
        subject, position = _parse_term_tokens(tokens, position + 1)
        relation, position = _parse_term_tokens(tokens, position)
        object_, position = _parse_term_tokens(tokens, position)
        if position >= len(tokens) or tokens[position].kind != "RPAREN":
            raise ParseError("a triple must contain exactly three terms")
        return Triple(subject, relation, object_), position + 1
    if token.kind == "LBRACKET":
        elements: list[Term] = []
        position += 1
        while position < len(tokens) and tokens[position].kind != "RBRACKET":
            element, position = _parse_term_tokens(tokens, position)
            elements.append(element)
        if position >= len(tokens):
            raise ParseError("unclosed finite set")
        return FiniteSet(tuple(elements)), position + 1
    if (
        token.kind == "ATOM"
        and token.value == "SEQ"
        and position + 1 < len(tokens)
        and tokens[position + 1].kind == "LBRACKET"
    ):
        elements = []
        position += 2
        while position < len(tokens) and tokens[position].kind != "RBRACKET":
            element, position = _parse_term_tokens(tokens, position)
            elements.append(element)
        if position >= len(tokens):
            raise ParseError("unclosed finite sequence")
        return FiniteSequence(tuple(elements)), position + 1
    if token.kind == "VARIABLE":
        return Variable(token.value[1:]), position + 1
    if token.kind == "NUMBER":
        value = float(token.value) if "." in token.value else int(token.value)
        return Number(value), position + 1
    if token.kind == "ATOM":
        return _STATUSES.get(token.value, Atom(token.value)), position + 1
    raise ParseError(f"expected a term, got {token.value!r}")
