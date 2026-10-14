/* Experimental bounded enumeration. No domain propagation or solver hooks. */
#include <stdint.h>
#include <string.h>

#define NV 32
#define NC 64
#define VALUES 4096
#define WORDS (VALUES / 64)

typedef struct {
    int n, m, mode, all, found, aborted;
    const int *offsets, *values, *ops;
    const int64_t *targets;
    int x[NV], first[NV], last[NC], degree[NV];
    int incident[NV][NC], coefficient[NV][NC];
    unsigned char used[VALUES];
    uint64_t occupied[WORDS], (*domains)[WORDS];
    int first_word[NV], end_word[NV];
    int64_t sum[NC], low[NC][NV + 1], high[NC][NV + 1];
    uint64_t visits, leaves, solutions, limit;
} Context;

static int allowed(int op, int64_t low, int64_t high, int64_t target) {
    return op == 0 ? low <= target && target <= high
                   : op == 1 ? low <= target : high >= target;
}

static void visit_basic(Context *c, int depth) {
    if (depth == c->n) {
        c->leaves++;
        for (int q = 0; q < c->m; ++q)
            if (!allowed(c->ops[q], c->sum[q], c->sum[q], c->targets[q])) return;
        if (!c->found) memcpy(c->first, c->x, c->n * sizeof(int));
        c->found = 1;
        c->solutions++;
        return;
    }
    for (int p = c->offsets[depth]; p < c->offsets[depth + 1]; ++p) {
        if (c->visits >= c->limit) { c->aborted = 1; return; }
        c->visits++;
        int value = c->values[p];
        if (c->used[value]) continue;
        c->used[value] = 1;
        c->x[depth] = value;
        for (int z = 0; z < c->degree[depth]; ++z) {
            int q = c->incident[depth][z];
            c->sum[q] += (int64_t)c->coefficient[depth][z] * value;
        }
        int feasible = 1;
        for (int z = 0; feasible && z < c->degree[depth]; ++z) {
            int q = c->incident[depth][z];
            if (c->mode == 2)
                feasible = allowed(c->ops[q], c->sum[q] + c->low[q][depth + 1],
                                   c->sum[q] + c->high[q][depth + 1], c->targets[q]);
            else if (c->mode == 1 && c->last[q] == depth)
                feasible = allowed(c->ops[q], c->sum[q], c->sum[q], c->targets[q]);
        }
        if (feasible) visit_basic(c, depth + 1);
        for (int z = 0; z < c->degree[depth]; ++z) {
            int q = c->incident[depth][z];
            c->sum[q] -= (int64_t)c->coefficient[depth][z] * value;
        }
        c->used[value] = 0;
        if (c->aborted || (c->found && !c->all)) return;
    }
}

/* Floor/ceil division for signed bounds, with arithmetic restricted by the
   Python extractor to a conservative int64 range. */
static int64_t floor_div(int64_t x, int a) {
    if (a == 1) return x;
    if (a == -1) return -x;
    int64_t q = x / a, r = x % a;
    return q - (r != 0 && ((r < 0) != (a < 0)));
}
static int64_t ceil_div(int64_t x, int a) {
    if (a == 1) return x;
    if (a == -1) return -x;
    int64_t q = x / a, r = x % a;
    return q + (r != 0 && ((r < 0) == (a < 0)));
}

static void visit_filtered(Context *c, int depth);

static inline void filtered_candidate(Context *c, int depth, int value) {
    c->visits++;
    if (c->used[value]) return;
    c->used[value] = 1;
    if (c->mode == 4) c->occupied[value / 64] |= UINT64_C(1) << (value % 64);
    c->x[depth] = value;
    for (int z = 0; z < c->degree[depth]; ++z) {
        int q = c->incident[depth][z];
        c->sum[q] += (int64_t)c->coefficient[depth][z] * value;
    }
    visit_filtered(c, depth + 1);
    for (int z = 0; z < c->degree[depth]; ++z) {
        int q = c->incident[depth][z];
        c->sum[q] -= (int64_t)c->coefficient[depth][z] * value;
    }
    c->used[value] = 0;
    if (c->mode == 4) c->occupied[value / 64] &= ~(UINT64_C(1) << (value % 64));
}

static void visit_filtered(Context *c, int depth) {
    if (depth == c->n) {
        c->leaves++;
        /* Bounds checked on every row's last variable imply feasibility, but
           retain the independent final check while this is experimental. */
        for (int q = 0; q < c->m; ++q)
            if (!allowed(c->ops[q], c->sum[q], c->sum[q], c->targets[q])) return;
        if (!c->found) memcpy(c->first, c->x, c->n * sizeof(int));
        c->found = 1;
        c->solutions++;
        return;
    }
    /* Intersect cheap arithmetic intervals BEFORE iterating candidates. For a
       last variable in an equality, ceil/floor division derives its only
       possible value (or proves non-integrality). No domain mutation/queue. */
    int64_t lo = 0, hi = VALUES - 1;
    for (int z = 0; z < c->degree[depth]; ++z) {
        int q = c->incident[depth][z], a = c->coefficient[depth][z];
        int64_t lower = c->targets[q] - c->sum[q] - c->high[q][depth + 1];
        int64_t upper = c->targets[q] - c->sum[q] - c->low[q][depth + 1];
        if (!a) {
            if (!allowed(c->ops[q], c->sum[q] + c->low[q][depth + 1],
                         c->sum[q] + c->high[q][depth + 1], c->targets[q])) return;
            continue;
        }
        if (c->ops[q] != 1) {
            int64_t bound = a > 0 ? ceil_div(lower, a) : floor_div(lower, a);
            if (a > 0) { if (bound > lo) lo = bound; }
            else { if (bound < hi) hi = bound; }
        }
        if (c->ops[q] != 2) {
            int64_t bound = a > 0 ? floor_div(upper, a) : ceil_div(upper, a);
            if (a > 0) { if (bound < hi) hi = bound; }
            else { if (bound > lo) lo = bound; }
        }
        if (lo > hi) return;
    }
    if (c->mode == 4) {
        int begin = (int)lo / 64, end = (int)hi / 64;
        if (begin < c->first_word[depth]) begin = c->first_word[depth];
        if (end >= c->end_word[depth]) end = c->end_word[depth] - 1;
        for (int w = begin; w <= end; ++w) {
            uint64_t available = c->domains[depth][w] & ~c->occupied[w];
            if (w == lo / 64) available &= UINT64_MAX << (lo % 64);
            if (w == hi / 64) available &= UINT64_MAX >> (63 - hi % 64);
            while (available) {
                if (c->visits >= c->limit) { c->aborted = 1; return; }
                int bit = __builtin_ctzll(available);
                available &= available - 1;
                filtered_candidate(c, depth, 64 * w + bit);
                if (c->aborted || (c->found && !c->all)) return;
            }
        }
        return;
    }
    for (int p = c->offsets[depth]; p < c->offsets[depth + 1]; ++p) {
        int value = c->values[p];
        if (value < lo || value > hi || c->used[value]) continue;
        if (c->visits >= c->limit) { c->aborted = 1; return; }
        filtered_candidate(c, depth, value);
        if (c->aborted || (c->found && !c->all)) return;
    }
}

/* status: 0 exhausted, 1 witness, 2 incomplete, -1 unsupported input.
   counts: attempted values, complete tuples, valid tuples. */
int residual_enum(int n, const int *offsets, const int *values,
                  int m, const int *starts, const int *variables,
                  const int *coefficients, const int *ops, const int64_t *targets,
                  int mode, int all, uint64_t limit, int *first, uint64_t *counts) {
    if (n < 0 || n > NV || m < 0 || m > NC || mode < 0 || mode > 4) return -1;
    Context c = {0};
    uint64_t bit_domains[NV][WORDS];
    if (mode == 4) {
        memset(bit_domains, 0, sizeof(bit_domains));
        c.domains = bit_domains;
    }
    c.n = n; c.m = m; c.mode = mode; c.all = all; c.limit = limit;
    c.offsets = offsets; c.values = values; c.ops = ops; c.targets = targets;
    for (int i = 0; i < n; ++i) {
        if (offsets[i] == offsets[i + 1]) { memset(counts, 0, 3 * sizeof(uint64_t)); return 0; }
        c.first_word[i] = WORDS;
        for (int p = offsets[i]; p < offsets[i + 1]; ++p) {
            if (values[p] < 0 || values[p] >= VALUES) return -1;
            if (mode == 4) {
                int w = values[p] / 64;
                c.domains[i][w] |= UINT64_C(1) << (values[p] % 64);
                if (w < c.first_word[i]) c.first_word[i] = w;
                if (w + 1 > c.end_word[i]) c.end_word[i] = w + 1;
            }
        }
    }
    for (int q = 0; q < m; ++q) {
        c.last[q] = -1;
        int coeff[NV] = {0};
        for (int p = starts[q]; p < starts[q + 1]; ++p) {
            int v = variables[p];
            if (v < 0 || v >= n || c.degree[v] >= NC) return -1;
            coeff[v] = coefficients[p];
            int z = c.degree[v]++;
            c.incident[v][z] = q;
            c.coefficient[v][z] = coefficients[p];
            if (v > c.last[q]) c.last[q] = v;
        }
        if (c.last[q] < 0 && !allowed(ops[q], 0, 0, targets[q])) {
            memset(counts, 0, 3 * sizeof(uint64_t)); return 0;
        }
        for (int i = n - 1; i >= 0; --i) {
            int64_t lo = 0, hi = 0;
            if (coeff[i]) {
                lo = hi = (int64_t)coeff[i] * values[offsets[i]];
                for (int p = offsets[i] + 1; p < offsets[i + 1]; ++p) {
                    int64_t value = (int64_t)coeff[i] * values[p];
                    if (value < lo) lo = value;
                    if (value > hi) hi = value;
                }
            }
            c.low[q][i] = lo + c.low[q][i + 1];
            c.high[q][i] = hi + c.high[q][i + 1];
        }
    }
    if (mode <= 2) visit_basic(&c, 0);
    else visit_filtered(&c, 0);
    counts[0] = c.visits; counts[1] = c.leaves; counts[2] = c.solutions;
    if (c.found) memcpy(first, c.first, n * sizeof(int));
    return c.aborted ? 2 : c.found ? 1 : 0;
}
