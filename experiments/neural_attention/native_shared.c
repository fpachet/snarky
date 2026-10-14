/* Experimental shared-domain DFS. The Batch domain array is authoritative.
 * Word trails cover propagation and branching; sizes update with every write.
 * Sparse pre-rollback snapshots preserve the original sorted initial queue,
 * including when transient restorations ultimately leave a variable unchanged.
 */
#include <limits.h>
#include <math.h>
typedef struct { int at; uint64_t old; } SharedChange;
typedef struct { int variable; size_t mark; } SharedFrame;
typedef struct {
    Batch *b;
    SharedChange *trail;
    size_t used, capacity;
    int *sizes, *word_variables, *dirty_variables, dirty_count;
    unsigned char *dirty;
    uint64_t *before, *stats;
} SharedSearch;

static double search_time(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t) != 0) return -1;
    return (double)t.tv_sec+(double)t.tv_nsec*1e-9;
}

static void shared_touch(SharedSearch *s, int v) {
    if (s->dirty[v]) return;
    s->dirty[v] = 1; s->dirty_variables[s->dirty_count++] = v;
    int at = s->b->offsets[v], words = s->b->offsets[v+1]-at;
    memcpy(s->before+at, s->b->domains+at, (size_t)words*sizeof(uint64_t));
}

static int shared_write(void *state, int at, uint64_t value) {
    SharedSearch *s = state;
    uint64_t old = s->b->domains[at];
    if (old == value) return 1;
    if ((value & ~old) || s->used >= s->capacity) return 0;
    s->trail[s->used++] = (SharedChange){at, old};
    s->sizes[s->word_variables[at]] += __builtin_popcountll(value)-__builtin_popcountll(old);
    s->b->domains[at] = value;
    if (s->used > s->stats[8]) s->stats[8] = s->used;
    return 1;
}

static int shared_propagate(SharedSearch *s, int first, double seconds) {
    Batch *b = s->b;
    memset(b->counts, 0, sizeof(b->counts)); b->counts[4] = UINT64_C(1469598103934665603);
    b->head = b->tail = b->used = 0; memset(b->queued, 0, (size_t)b->nc);
    b->log = NULL; b->log_count = 0;
    int all = first || b->prior_status <= 0;
    for (int j = 0; j < s->dirty_count; ++j) {
        int v = s->dirty_variables[j], at = b->offsets[v], words = b->offsets[v+1]-at;
        s->dirty[v] = 0;
        if (!all && memcmp(s->before+at, b->domains+at, (size_t)words*sizeof(uint64_t)))
            for (int k = b->adjstarts[v]; k < b->adjstarts[v+1]; ++k)
                b->queued[b->adjacency[k]] = 1;
    }
    s->dirty_count = 0;
    for (int c = 0; c < b->nc; ++c) if (all || b->queued[c]) {
        b->queued[c] = 0; batch_enqueue(b, c);
    }
    double started = search_time();
    int status = 1;
    if (started < 0) status = -5;
    while (status > 0 && b->used) {
        double now = search_time();
        if (now < 0) { status = -5; break; }
        if (now-started >= seconds) { status = -4; break; }
        if (b->counts[0] >= INT_MAX) { status = -3; break; }
        int c = b->queue[b->head]; b->head = (b->head+1) % (b->nc+1);
        --b->used; b->queued[c] = 0; ++b->counts[0];
        status = batch_generic_step(b, c);
        if (status == 0) b->counts[5] = (uint64_t)c+1;
    }
    b->have_domains = 1; b->prior_status = status;
    return status;
}

int native_search(void *handle, const uint64_t *initial, int policy,
                  uint64_t max_nodes, uint64_t max_solutions, double seconds,
                  int *solutions, int collect_limit, uint64_t *stats) {
    Batch *b = handle;
    if (!b || !initial || !solutions || !stats || collect_limit < 1 ||
        collect_limit > 10000 || policy < 0 || policy > 1 ||
        !isfinite(seconds) || seconds < 0) return -1;
    memset(stats, 0, 10*sizeof(uint64_t)); stats[9] = UINT64_C(1469598103934665603);
    SharedSearch s = {.b=b, .stats=stats};
    int max_words = 0;
    for (int v = 0; v < b->nv; ++v) {
        int width = b->offsets[v+1]-b->offsets[v];
        if (width > max_words) max_words = width;
        s.capacity += (size_t)b->lengths[v];
        if ((b->lengths[v]&63) && initial[b->offsets[v+1]-1] >> (b->lengths[v]&63)) return -1;
    }
    s.trail = calloc(s.capacity, sizeof(*s.trail));
    s.sizes = calloc((size_t)b->nv, sizeof(int));
    s.word_variables = calloc((size_t)b->words, sizeof(int));
    s.dirty_variables = calloc((size_t)b->nv, sizeof(int));
    s.dirty = calloc((size_t)b->nv, 1);
    s.before = calloc((size_t)b->words, sizeof(uint64_t));
    SharedFrame *frames = calloc((size_t)b->nv, sizeof(*frames));
    uint64_t *choices = calloc((size_t)b->nv*max_words, sizeof(uint64_t));
    uint64_t *weights = calloc((size_t)b->nc, sizeof(uint64_t));
    int status = -6, depth = 0, first = 1, empty = 0;
    if (!s.trail || !s.sizes || !s.word_variables || !s.dirty_variables || !s.dirty ||
        !s.before || !frames || !choices || !weights) goto done;
    memcpy(b->domains, initial, (size_t)b->words*sizeof(uint64_t));
    for (int v = 0; v < b->nv; ++v) {
        for (int w = b->offsets[v]; w < b->offsets[v+1]; ++w) {
            s.word_variables[w] = v; s.sizes[v] += __builtin_popcountll(b->domains[w]);
        }
        if (!s.sizes[v]) empty = 1;
    }
    for (int c = 0; c < b->nc; ++c) weights[c] = 1;
    b->writer = shared_write; b->writer_state = &s;
    double started = search_time();
    if (started < 0) { status = -5; goto done; }
enter:
    if (max_nodes && stats[0] >= max_nodes) { status = 2; goto done; }
    double now = search_time();
    if (now < 0) { status = -5; goto done; }
    double remaining = seconds-(now-started);
    if (remaining <= 0) { status = 3; goto done; }
    ++stats[0];
    if (empty) {
        ++stats[1];
        stats[9] = (stats[9]^UINT64_C(1469598103934665603))*UINT64_C(1099511628211);
        stats[9] *= UINT64_C(1099511628211);
        status = 0; goto done;
    }
#ifdef PROFILE_NATIVE
    double profile_before = search_time();
#endif
    status = shared_propagate(&s, first, remaining); first = 0;
#ifdef PROFILE_NATIVE
    b->profile_seconds[2] += search_time()-profile_before;
#endif
    for (int j = 0; j < 4; ++j) stats[j+2] += b->counts[j];
    stats[9] = (stats[9]^b->counts[4])*UINT64_C(1099511628211);
    stats[9] = (stats[9]^b->counts[5])*UINT64_C(1099511628211);
    now = search_time();
    if (now < 0) { status = -5; goto done; }
    if (status == -4 || now-started >= seconds) { status = 3; goto done; }
    if (status < 0) goto done;
    if (status == 0) {
        ++stats[1]; if (b->counts[5]) ++weights[b->counts[5]-1]; goto advance;
    }
    int variable = -1;
    double best = HUGE_VAL;
    for (int v = 0; v < b->nv; ++v) {
        if (s.sizes[v] <= 1) continue;
        uint64_t weight = 0;
        if (policy) for (int j = b->adjstarts[v]; j < b->adjstarts[v+1]; ++j)
            weight += weights[b->adjacency[j]];
        double score = policy ? (double)s.sizes[v]/(double)(weight ? weight : 1) : (double)s.sizes[v];
        if (score < best) { variable = v; best = score; }
    }
    if (variable < 0) {
        if (stats[6] < (uint64_t)collect_limit)
            for (int v = 0; v < b->nv; ++v)
                for (int w = b->offsets[v]; w < b->offsets[v+1]; ++w)
                    if (b->domains[w]) solutions[stats[6]*(uint64_t)b->nv+v] =
                        64*(w-b->offsets[v])+__builtin_ctzll(b->domains[w]);
        ++stats[6];
        if (max_solutions && stats[6] >= max_solutions) { status = 1; goto done; }
        goto advance;
    }
    if (depth >= b->nv) { status = -6; goto done; }
    frames[depth] = (SharedFrame){variable, s.used};
    memcpy(choices+(size_t)depth*max_words, b->domains+b->offsets[variable],
           (size_t)(b->offsets[variable+1]-b->offsets[variable])*sizeof(uint64_t));
    ++depth; if ((uint64_t)depth > stats[7]) stats[7] = (uint64_t)depth;
advance:
    while (depth) {
        SharedFrame *f = &frames[depth-1];
        while (s.used > f->mark) {
            SharedChange change = s.trail[--s.used];
            int v = s.word_variables[change.at]; shared_touch(&s, v);
            s.sizes[v] += __builtin_popcountll(change.old)-__builtin_popcountll(b->domains[change.at]);
            b->domains[change.at] = change.old;
        }
        int at = b->offsets[f->variable], width = b->offsets[f->variable+1]-at;
        uint64_t *available = choices+(size_t)(depth-1)*max_words;
        for (int w = 0; w < width; ++w) if (available[w]) {
            uint64_t bit = available[w] & (UINT64_C(0)-available[w]); available[w] &= available[w]-1;
            shared_touch(&s, f->variable);
            for (int k = 0; k < width; ++k)
                if (!shared_write(&s, at+k, k == w ? bit : 0)) { status = -6; goto done; }
            goto enter;
        }
        --depth;
    }
    status = 0;
done:
    b->writer = NULL; b->writer_state = NULL; b->log = NULL;
    free(s.trail); free(s.sizes); free(s.word_variables); free(s.dirty_variables);
    free(s.dirty); free(s.before); free(frames); free(choices); free(weights);
    return status;
}
