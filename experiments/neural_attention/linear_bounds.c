/* Incremental contribution bounds over arbitrary immutable candidate order.
 * Cached bounds reconcile actual masks, including widening after backtracking.
 * Sorted ranks are built once. Interior deletions do not rescan candidates.
 * No allocation during filtering; all removals are certified by sum bounds.
 */
typedef struct { int value, position; } LinearRank;
struct LinearBounds {
    LinearRank *ranks;
    uint64_t *previous, *staged;
    int lo[MAX_N], hi[MAX_N], lower, upper;
    unsigned char initialized[MAX_N];
    int certified;
};

static int linear_compare(const void *a, const void *b) {
    const LinearRank *x = a, *y = b;
    return (x->value > y->value)-(x->value < y->value);
}

static void linear_free(struct LinearBounds *p) {
    if (!p) return;
    free(p->ranks); free(p->previous); free(p->staged); free(p);
}

static struct LinearBounds *linear_create(struct Sum *s) {
    struct LinearBounds *p = calloc(1, sizeof(*p));
    if (!p) return NULL;
    p->ranks = calloc((size_t)s->entries, sizeof(*p->ranks));
    p->previous = calloc((size_t)s->words, sizeof(uint64_t));
    p->staged = calloc((size_t)s->words, sizeof(uint64_t));
    if (!p->ranks || !p->previous || !p->staged) { linear_free(p); return NULL; }
    for (int i = 0; i < s->n; ++i) {
        int start = s->starts[i], size = s->starts[i+1]-start;
        for (int j = 0; j < size; ++j)
            p->ranks[start+j] = (LinearRank){s->values[start+j], j};
        qsort(p->ranks+start, (size_t)size, sizeof(*p->ranks), linear_compare);
    }
    return p;
}

static int linear_has(const uint64_t *mask, int position) {
    return (int)((mask[position/64] >> (position&63)) & 1);
}

/* op: 0 equality, 1 <=, 2 >=. Inputs and outputs must be disjoint. */
static int linear_filter(Sum *s, const uint64_t *input, int target, int op,
                         uint64_t *output) {
    struct LinearBounds *p = s->linear;
    p->certified = 0;
    memcpy(output, input, (size_t)s->words*sizeof(uint64_t));
    for (int i = 0; i < s->n; ++i) {
        int at = s->masks[i], words = s->masks[i+1]-at;
        if (p->initialized[i] && !memcmp(input+at, p->previous+at,
                                          (size_t)words*sizeof(uint64_t))) continue;
        int widening = !p->initialized[i];
        for (int w = at; w < at+words && !widening; ++w)
            if (input[w] & ~p->previous[w]) widening = 1;
        LinearRank *ranks = p->ranks+s->starts[i];
        int lo = widening ? 0 : p->lo[i];
        int hi = widening ? s->starts[i+1]-s->starts[i]-1 : p->hi[i];
        while (lo <= hi && !linear_has(input+at, ranks[lo].position)) ++lo;
        while (hi >= lo && !linear_has(input+at, ranks[hi].position)) --hi;
        if (lo > hi) return 0;
        p->lower += ranks[lo].value-(p->initialized[i] ? ranks[p->lo[i]].value : 0);
        p->upper += ranks[hi].value-(p->initialized[i] ? ranks[p->hi[i]].value : 0);
        p->lo[i] = lo; p->hi[i] = hi; p->initialized[i] = 1;
        memcpy(p->previous+at, input+at, (size_t)words*sizeof(uint64_t));
    }
    if ((op != 2 && p->lower > target) || (op != 1 && p->upper < target)) return 0;
    for (int i = 0; i < s->n; ++i) {
        LinearRank *ranks = p->ranks+s->starts[i];
        int at = s->masks[i];
        int low = target-(p->upper-ranks[p->hi[i]].value);
        int high = target-(p->lower-ranks[p->lo[i]].value);
        if (op != 1)
            for (int j = p->lo[i]; j <= p->hi[i] && ranks[j].value < low; ++j) {
                int position = ranks[j].position;
                output[at+position/64] &= ~(UINT64_C(1) << (position&63));
            }
        if (op != 2)
            for (int j = p->hi[i]; j >= p->lo[i] && ranks[j].value > high; --j) {
                int position = ranks[j].position;
                output[at+position/64] &= ~(UINT64_C(1) << (position&63));
            }
        uint64_t any = 0;
        for (int w = at; w < s->masks[i+1]; ++w) any |= output[w];
        if (!any) return 0;
    }
#if LINEAR_MODE >= 2
    if (op == 0) {
        int active = 0, candidates = 0;
        for (int i = 0; i < s->n; ++i) {
            int size = 0;
            for (int w = s->masks[i]; w < s->masks[i+1]; ++w)
                size += __builtin_popcountll(output[w]);
            if (size > 1) { ++active; candidates += size; }
        }
        /* Static, deliberately conservative first policy; not tuned per size. */
        int run_exact = active <= 2;
#if LINEAR_MODE == 2
        run_exact |= active <= 4 && candidates <= 64;
#else
        int residual = target-p->lower;
        if (p->upper-target < residual) residual = p->upper-target;
        run_exact |= (uint64_t)candidates*(uint64_t)(residual/64+1) <= UINT64_C(20000);
#endif
        if (run_exact) {
            memcpy(p->staged, output, (size_t)s->words*sizeof(uint64_t));
            int status = sum_supports(s, p->staged, target, output);
            p->certified = status > 0;
            return status;
        }
    }
#endif
    return 1;
}
