"""Frozen benchmark kernel before fixed-term shortcuts; never used by runtime."""


class NumericPlan:
    def _equality_supports(
        self, masks: tuple[int, ...], target: int
    ) -> tuple[int, ...] | None:
        extrema = [c.extrema(m) for c, m in zip(self.columns, masks, strict=True)]
        lower = sum(low for low, _ in extrema)
        span = sum(high - low for low, high in extrema)
        residual = target - lower
        if not 0 <= residual <= span:
            return None
        # Normalizing current minima handles signed coefficients and enormous
        # translations without using absolute integer magnitudes as bit indexes.
        reflect = residual > span - residual
        if reflect:
            residual = span - residual
        candidates = []
        for column, mask, (low, high) in zip(self.columns, masks, extrema, strict=True):
            offsets = []
            while mask:
                bit = mask & -mask
                mask ^= bit
                value = column.values[bit.bit_length() - 1]
                shifted = high - value if reflect else value - low
                if shifted <= residual:
                    offsets.append((bit, shifted))
            candidates.append(offsets)
        limit = (1 << (residual + 1)) - 1
        prefix = [1]
        for offsets in candidates:
            reachable = 0
            for _, shifted in offsets:
                reachable |= prefix[-1] << shifted
            prefix.append(reachable & limit)
        if not prefix[-1] & (1 << residual):
            return None
        backward = 1 << residual
        supported = [0] * len(masks)
        for index in range(len(masks) - 1, -1, -1):
            reachable = 0
            for bit, shifted in candidates[index]:
                suffix = backward >> shifted
                if prefix[index] & suffix:
                    supported[index] |= bit
                    reachable |= suffix
            backward = reachable
        return tuple(supported)
