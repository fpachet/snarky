"""Independent raw-window oracle for the paper's pitch experiment; no Snarky."""

from collections import Counter
from fractions import Fraction
from pathlib import Path

CORPUS = Path(__file__).parent / "data/di_meola_v1/corpus.json"
MODES = ("fixed", "smoothing", "max_order", "algebraic")


def counts(sequences, max_order):
    rows = [
        Counter(tuple(s[i : i + k + 1]) for s in sequences for i in range(len(s) - k))
        for k in range(max_order + 1)
    ]
    totals = [Counter() for _ in rows]
    for k, table in enumerate(rows):
        for word, count in table.items():
            totals[k][word[:-1]] += count
    return rows, totals


def step(tables, history, symbol, mode, order, forbidden=None, initial="unit"):
    rows, totals = tables
    if (
        forbidden is not None
        and len(history) >= forbidden
        and (*history[-forbidden:], symbol) in rows[forbidden]
    ):
        return None
    eligible = min(order, len(history))
    probabilities = []
    for k in range(eligible + 1):
        context = tuple(history[-k:]) if k else ()
        probabilities.append(
            Fraction(rows[k].get((*context, symbol), 0), totals[k].get(context, 1))
        )
    supported = [k for k, p in enumerate(probabilities) if p]
    if not supported or (eligible and 1 not in supported):
        return None
    selected = max(supported)
    if mode == "algebraic":
        return selected**2
    if not eligible:
        return probabilities[0] if initial == "marginal" else Fraction(1)
    if mode == "fixed":
        return probabilities[eligible] or None
    if mode == "smoothing":
        return sum(probabilities[1:]) / eligible
    return probabilities[selected]


def score(
    sequences, sequence, mode, order, *, forbidden=None, prefix=(), initial="unit"
):
    tables = counts(sequences, max(order, forbidden or 0))
    total = 0 if mode == "algebraic" else Fraction(1)
    history = tuple(prefix)
    for symbol in sequence:
        value = step(tables, history, symbol, mode, order, forbidden, initial)
        if value is None:
            return None
        total = total + value if mode == "algebraic" else total * value
        history += (symbol,)
    return total


def optimum(
    sequences,
    domains,
    mode,
    order,
    *,
    forbidden=None,
    prefix=(),
    initial="unit",
    contour=None,
    alpha=Fraction(1),
):
    """Independent DP retaining raw windows, without suffix-state compression."""
    memory = max(order, forbidden or 0)
    tables = counts(sequences, memory)
    start = tuple(prefix[-memory:])
    current = {start: (0 if mode == "algebraic" else Fraction(1), ())}
    for i, domain in enumerate(domains):
        following = {}
        for history, (partial, path) in current.items():
            for symbol in domain:
                value = step(tables, history, symbol, mode, order, forbidden, initial)
                if value is None:
                    continue
                if contour is not None:
                    distance = (symbol - contour[i]) ** 2
                    a, b = alpha.numerator, alpha.denominator
                    value = (
                        a * value - (b - a) * distance
                        if mode == "algebraic"
                        else value**a * Fraction(2) ** (-(b - a) * distance)
                    )
                candidate = partial + value if mode == "algebraic" else partial * value
                target = (*history, symbol)[-memory:]
                if target not in following or candidate > following[target][0]:
                    following[target] = candidate, (*path, symbol)
        current = following
    return max(current.values(), key=lambda v: v[0]) if current else None
