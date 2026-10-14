"""Opt-in full ALLDIFF C filter; reversible domain mutation stays in Python."""

from __future__ import annotations

import ctypes as ct
import sys
import weakref
from collections import Counter
from pathlib import Path

from snarky.finite.alldifferent import AllDifferentPlan, AllDifferentPlans

from .magic_residual_enumeration import Kernel


class AllDiffKernel(Kernel):
    def __init__(self, library):
        self.library = ct.CDLL(str(Path(library).resolve()))
        ip, up = ct.POINTER(ct.c_int), ct.POINTER(ct.c_uint64)
        self.create = self.library.alldiff_create
        self.create.argtypes = [ct.c_int, ct.c_int, ip, ip]
        self.create.restype = ct.c_void_p
        self.free = self.library.alldiff_free
        self.free.argtypes = [ct.c_void_p]
        self.free.restype = None
        self.function = self.library.alldiff_supports
        self.function.argtypes = [ct.c_void_p, up, up]
        self.function.restype = ct.c_int
        self.matching = self.library.alldiff_matching
        self.matching.argtypes = [ct.c_void_p, ip, ip]
        self.matching.restype = None

    @classmethod
    def build(cls, output, *, cache_dir=None):
        return super().build(
            output,
            cache_dir=cache_dir or "generated/neural_attention/alldiff_kernel_cache",
            source=Path(__file__).with_name("alldiff_support.c"),
        )


class NativeAllDifferentPlan(AllDifferentPlan):
    def __init__(self, original, kernel, stats, audit=False):
        super().__init__(
            original.variables,
            original.columns,
            len(original.owners),
            original._domain_store,
        )
        if sys.byteorder != "little":
            raise ValueError("native mask packing requires little-endian storage")
        if not 1 <= len(self.variables) <= 2048 or not self.owners:
            raise ValueError("unsupported ALLDIFF dimensions")
        self.kernel, self.stats = kernel, stats
        self.reference = original if audit else None
        starts, positions, lengths = [0], [], []
        for column in self.columns:
            positions.extend(column.positions)
            starts.append(len(positions))
            lengths.append(8 * ((len(column.positions) + 63) // 64))
        self.lengths = tuple(lengths)
        self.byte_offsets = tuple(sum(lengths[:i]) for i in range(len(lengths) + 1))
        self.handle = kernel.create(
            len(self.variables),
            len(self.owners),
            (ct.c_int * len(starts))(*starts),
            (ct.c_int * len(positions))(*positions),
        )
        if not self.handle:
            raise ValueError("ALLDIFF workspace rejected")
        self._finalizer = weakref.finalize(self, kernel.free, self.handle)
        words = sum(lengths) // 8
        self.inputs = (ct.c_uint64 * words)()
        self.outputs = (ct.c_uint64 * words)()
        self.audit_matching = (ct.c_int * len(self.variables))() if audit else None
        self.audit_owners = (ct.c_int * len(self.owners))() if audit else None
        stats["compiled_plans"] += 1

    def supports(self, domains):
        local = (
            domains.masks_at(self.indices)
            if domains is self._domain_store and self.indices is not None
            else tuple(domains.mask(v) for v in self.variables)
        )
        self.input_masks = local
        self.stats["calls"] += 1
        if not all(local):
            answer = None
            self.stats["empty_calls"] += 1
        elif local == self.last_supported:
            answer = local
            self.stats["cached_calls"] += 1
        else:
            packed = b"".join(
                mask.to_bytes(length, sys.byteorder)
                for mask, length in zip(local, self.lengths, strict=True)
            )
            ct.memmove(self.inputs, packed, len(packed))
            status = self.kernel.function(self.handle, self.inputs, self.outputs)
            self.stats["native_calls"] += 1
            if status < 0:
                raise RuntimeError("invalid ALLDIFF kernel input")
            if status == 0:
                answer = None
            else:
                result = ct.string_at(self.outputs, len(packed))
                answer = (
                    local
                    if result == packed
                    else tuple(
                        int.from_bytes(result[a:b], sys.byteorder)
                        for a, b in zip(
                            self.byte_offsets, self.byte_offsets[1:], strict=False
                        )
                    )
                )
                self.last_supported = answer
        if self.reference is not None:
            reference = self.reference.supports(domains)
            assert answer == reference, (local, answer, reference)
            self.kernel.matching(self.handle, self.audit_matching, self.audit_owners)
            assert list(self.audit_matching) == self.reference.matching
            assert list(self.audit_owners) == self.reference.owners
            assert self.last_supported == self.reference.last_supported
            self.stats["audited_calls"] += 1
        return answer


class NativeAllDifferentPlans(AllDifferentPlans):
    def __init__(self, domains, kernel, *, audit=False):
        super().__init__(domains)
        self.kernel, self.audit = kernel, audit
        self.stats = Counter()

    def _compile(self, constraint):
        original = super()._compile(constraint)
        if original is None:
            return None
        try:
            return NativeAllDifferentPlan(original, self.kernel, self.stats, self.audit)
        except ValueError:
            self.stats["fallback_plans"] += 1
            return original


def enable(native, kernel, *, audit=False):
    """Install explicitly, before propagation; never change public defaults."""
    if native._initialized:
        raise ValueError("enable the ALLDIFF experiment before propagation")
    native._alldifferent = NativeAllDifferentPlans(native.domains, kernel, audit=audit)
    return native
