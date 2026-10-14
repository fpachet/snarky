/* Experimental finite DFS over Batch propagators. No Python callbacks.
 * Candidate indices follow the original model alphabet order. Failure weights
 * persist across rollback; domains use a bounded word trail. Propagator scratch
 * reconciles actual masks through batch_run, including widening after rollback.
 * This deliberately retains the batch engine's full input/output scan per node.
 */
#include <limits.h>
#include <math.h>
typedef struct { int at; uint64_t old; } SearchChange;
typedef struct { int variable; size_t mark; } SearchFrame;

static double search_time(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t) != 0) return -1;
    return (double)t.tv_sec + (double)t.tv_nsec * 1e-9;
}

/* statuses: 0 exhausted, 1 solution limit, 2 node limit, 3 time limit.
 * Negative means an error/resource interruption, never an UNSAT certificate.
 * stats: nodes, failures, revisions, support calls, cache hits, reductions,
 * solutions, peak depth, peak trail entries, propagation-work digest.
 * Collected witnesses are candidate indices; only fully propagated leaves
 * are published. The caller owns the Batch handle and every output buffer.
 */
int native_search(void *handle, const uint64_t *initial, int policy,
                  uint64_t max_nodes, uint64_t max_solutions, double seconds,
                  int *solutions, int collect_limit, uint64_t *stats) {
    Batch *b = handle;
    if (!b || !initial || !solutions || !stats || collect_limit < 1 ||
        collect_limit > 10000 || policy < 0 || policy > 1 ||
        !isfinite(seconds) || seconds < 0) return -1;
    memset(stats, 0, 10*sizeof(uint64_t));
    stats[9] = UINT64_C(1469598103934665603);
    int max_words = 0;
    size_t capacity = 0;
    for (int v = 0; v < b->nv; ++v) {
        int width = b->offsets[v+1]-b->offsets[v];
        if (width > max_words) max_words = width;
        capacity += (size_t)b->lengths[v];
        if ((b->lengths[v]&63) &&
            initial[b->offsets[v+1]-1] >> (b->lengths[v]&63)) return -1;
    }
    SearchChange *trail = calloc(capacity, sizeof(*trail));
    SearchFrame *frames = calloc((size_t)b->nv, sizeof(*frames));
    uint64_t *choices = calloc((size_t)b->nv*max_words, sizeof(*choices));
    uint64_t *domains = calloc((size_t)b->words, sizeof(*domains));
    uint64_t *output = calloc((size_t)b->words, sizeof(*output));
    uint64_t *weights = calloc((size_t)b->nc, sizeof(*weights));
    int status = -6, depth = 0, first = 1;
    size_t used = 0;
    if (!trail || !frames || !choices || !domains || !output || !weights) goto done;
    memcpy(domains, initial, (size_t)b->words*sizeof(uint64_t));
    for (int c = 0; c < b->nc; ++c) weights[c] = 1;
    double started = search_time();
    if (started < 0) { status = -5; goto done; }
#define SEARCH_WRITE(index, value) do { \
    int search_at = (index); uint64_t search_value = (value); \
    if (domains[search_at] != search_value) { \
        if (used >= capacity) { status = -6; goto done; } \
        trail[used++] = (SearchChange){search_at, domains[search_at]}; \
        domains[search_at] = search_value; \
        if (used > stats[8]) stats[8] = used; \
    } \
} while (0)
enter:
    if (max_nodes && stats[0] >= max_nodes) { status = 2; goto done; }
    double now = search_time();
    if (now < 0) { status = -5; goto done; }
    double remaining = seconds-(now-started);
    if (remaining <= 0) { status = 3; goto done; }
    ++stats[0];
    uint64_t counts[6] = {0};
    status = batch_run(b, domains, output, first, NULL, 0, counts, INT_MAX, remaining);
    first = 0;
    for (int j = 0; j < 4; ++j) stats[j+2] += counts[j];
    stats[9] = (stats[9]^counts[4])*UINT64_C(1099511628211);
    stats[9] = (stats[9]^counts[5])*UINT64_C(1099511628211);
    now = search_time();
    if (now < 0) { status = -5; goto done; }
    if (status == -4 || now-started >= seconds) { status = 3; goto done; }
    if (status < 0) goto done;
    if (status == 0) {
        ++stats[1];
        if (counts[5]) ++weights[counts[5]-1];
        goto advance;
    }
    for (int w = 0; w < b->words; ++w) SEARCH_WRITE(w, output[w]);
    int variable = -1;
    double best = HUGE_VAL;
    for (int v = 0; v < b->nv; ++v) {
        int size = 0;
        for (int w = b->offsets[v]; w < b->offsets[v+1]; ++w)
            size += __builtin_popcountll(domains[w]);
        if (!size) { ++stats[1]; goto advance; }
        if (size == 1) continue;
        uint64_t weight = 0;
        if (policy) for (int j = b->adjstarts[v]; j < b->adjstarts[v+1]; ++j)
            weight += weights[b->adjacency[j]];
        double score = policy ? (double)size/(double)(weight ? weight : 1) : (double)size;
        if (score < best) { variable = v; best = score; }
    }
    if (variable < 0) {
        if (stats[6] < (uint64_t)collect_limit)
            for (int v = 0; v < b->nv; ++v)
                for (int w = b->offsets[v]; w < b->offsets[v+1]; ++w)
                    if (domains[w]) solutions[stats[6]*(uint64_t)b->nv+v] =
                        64*(w-b->offsets[v])+__builtin_ctzll(domains[w]);
        ++stats[6];
        if (max_solutions && stats[6] >= max_solutions) { status = 1; goto done; }
        goto advance;
    }
    if (depth >= b->nv) { status = -6; goto done; }
    frames[depth] = (SearchFrame){variable, used};
    memcpy(choices+(size_t)depth*max_words, domains+b->offsets[variable],
           (size_t)(b->offsets[variable+1]-b->offsets[variable])*sizeof(uint64_t));
    ++depth;
    if ((uint64_t)depth > stats[7]) stats[7] = (uint64_t)depth;
advance:
    while (depth) {
        SearchFrame *f = &frames[depth-1];
        while (used > f->mark) { --used; domains[trail[used].at] = trail[used].old; }
        int at = b->offsets[f->variable], width = b->offsets[f->variable+1]-at;
        uint64_t *available = choices+(size_t)(depth-1)*max_words;
        for (int w = 0; w < width; ++w) if (available[w]) {
            uint64_t bit = available[w] & (UINT64_C(0)-available[w]);
            available[w] &= available[w]-1;
            for (int k = 0; k < width; ++k) SEARCH_WRITE(at+k, k == w ? bit : 0);
            goto enter;
        }
        --depth;
    }
    status = 0;
done:
    /* A later call always begins a fresh search, regardless of interruption. */
    b->log = NULL;
    free(trail); free(frames); free(choices); free(domains); free(output); free(weights);
    return status;
#undef SEARCH_WRITE
}
