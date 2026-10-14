"""Opt-in exact SUM kernel; domain storage and propagation remain in Python."""

from __future__ import annotations

import ctypes as ct
import sys
import weakref
from collections import Counter
from pathlib import Path

from snarky.finite.constraints import ConstraintOperator
from snarky.finite.numeric import NumericPlan, NumericPlans

from .magic_residual_enumeration import Kernel

MAX_COLUMNS = 64
MAX_SPAN = 16384


class SumKernel(Kernel):
    def __init__(self, library):
        self.library = ct.CDLL(str(Path(library).resolve()))
        ip, up = ct.POINTER(ct.c_int), ct.POINTER(ct.c_uint64)
        self.create = self.library.sum_create
        self.create.argtypes = [ct.c_int, ip, ip]
        self.create.restype = ct.c_void_p
        self.free = self.library.sum_free
        self.free.argtypes = [ct.c_void_p]
        self.free.restype = None
        self.function = self.library.sum_supports
        self.function.argtypes = [ct.c_void_p, up, ct.c_int, up]
        self.function.restype = ct.c_int

    @classmethod
    def build(cls, output, *, cache_dir=None):
        return super().build(
            output,
            cache_dir=cache_dir or "generated/neural_attention/sum_kernel_cache",
            source=Path(__file__).with_name("sum_support.c"),
        )


class NativeEqualityPlan(NumericPlan):
    def __init__(self, original, kernel, stats, audit=False):
        super().__init__(original.columns, original.operator, original._domain_store)
        self.kernel, self.stats, self.audit = kernel, stats, audit
        self.origin = 0
        starts, values, lengths = [0], [], []
        span = 0
        if not 1 <= len(self.columns) <= MAX_COLUMNS:
            raise ValueError("unsupported number of SUM columns")
        for column in self.columns:
            contributions = column.values
            if not contributions or len(contributions) > 4096:
                raise ValueError("unsupported SUM alphabet size")
            if any(type(v) is not int for v in contributions):
                raise ValueError("unsupported noninteger contribution")
            low, high = min(contributions), max(contributions)
            span += high - low
            if span > MAX_SPAN or len(set(contributions)) != len(contributions):
                raise ValueError("unsupported SUM span or duplicate contributions")
            self.origin += low
            values.extend(v - low for v in contributions)
            starts.append(len(values))
            lengths.append(8 * ((len(contributions) + 63) // 64))
        self.span = span
        self.lengths = tuple(lengths)
        self.byte_offsets = tuple(sum(lengths[:i]) for i in range(len(lengths) + 1))
        self.handle = kernel.create(
            len(self.columns),
            (ct.c_int * len(starts))(*starts),
            (ct.c_int * len(values))(*values),
        )
        if not self.handle:
            raise ValueError("SUM workspace allocation or representation rejected")
        self._finalizer = weakref.finalize(self, kernel.free, self.handle)
        words = sum(lengths) // 8
        self.inputs = (ct.c_uint64 * words)()
        self.outputs = (ct.c_uint64 * words)()
        stats["compiled_plans"] += 1

    def _equality_supports(self, masks, target):
        self.stats["calls"] += 1
        normalized = target - self.origin
        if not 0 <= normalized <= self.span:
            answer = None
            self.stats["outside_original_bounds"] += 1
        else:
            packed = b"".join(
                mask.to_bytes(length, sys.byteorder)
                for mask, length in zip(masks, self.lengths, strict=True)
            )
            ct.memmove(self.inputs, packed, len(packed))
            status = self.kernel.function(
                self.handle, self.inputs, normalized, self.outputs
            )
            self.stats[f"path_{status}"] += 1
            if status < 0:
                self.stats["fallback_calls"] += 1
                answer = super()._equality_supports(masks, target)
            elif status == 0:
                answer = None
            else:
                result = ct.string_at(self.outputs, len(packed))
                answer = (
                    masks
                    if result == packed
                    else tuple(
                        int.from_bytes(result[a:b], sys.byteorder)
                        for a, b in zip(
                            self.byte_offsets, self.byte_offsets[1:], strict=False
                        )
                    )
                )
        if self.audit:
            reference = super()._equality_supports(masks, target)
            assert answer == reference, (masks, target, answer, reference)
            self.stats["audited_calls"] += 1
        return answer


class NativeSumPlans(NumericPlans):
    def __init__(self, domains, kernel, *, audit=False):
        super().__init__(domains)
        self.kernel, self.audit = kernel, audit
        self.stats = Counter()

    def _compile(self, terms, operator):
        plan = super()._compile(terms, operator)
        if plan is None or operator is not ConstraintOperator.EQUAL:
            return plan
        if len(plan.columns) <= 2:
            return plan
        try:
            return NativeEqualityPlan(plan, self.kernel, self.stats, self.audit)
        except ValueError:
            self.stats["fallback_plans"] += 1
            return plan


def enable(native, kernel, *, audit=False):
    """Explicit experimental adapter, before a state's first propagation."""
    if native._initialized:
        raise ValueError("enable the SUM experiment before propagation")
    native._numeric = NativeSumPlans(native.domains, kernel, audit=audit)
    return native
