/* Experimental native fixpoint executor. Filtering primitives are unchanged.
 * Input/output coordinates are immutable local candidate bitsets per variable.
 * Matching and exact-result hints are validated by masks after widening too.
 */
#include <time.h>
typedef struct {
    int nv, nc, words, scope_entries, local_words, max_local_words;
    int *lengths, *offsets, *starts, *variables, *kind, *ops, *targets;
    int *local, *cache_offsets, *adjstarts, *adjacency, *queue;
    unsigned char *queued, *cached;
    void **plans;
    uint64_t *domains, *input, *output, *cache;
    uint64_t *log, counts[6];
    int head, tail, used, have_domains, prior_status, log_capacity, log_count, log_stride;
} Batch;

#ifdef MODEL_SPECIALIZED
static int batch_special_step(Batch *, int);
static void batch_special_notify(Batch *, int);
#endif

static void batch_enqueue(Batch *b, int c) {
    if (b->queued[c]) return;
    b->queued[c] = 1;
    b->queue[b->tail] = c; b->tail = (b->tail+1) % (b->nc+1); ++b->used;
}

static void batch_notify(Batch *b, int v) {
#ifdef MODEL_SPECIALIZED
    batch_special_notify(b, v);
#else
    for (int j = b->adjstarts[v]; j < b->adjstarts[v+1]; ++j)
        batch_enqueue(b, b->adjacency[j]);
#endif
}

void batch_free(void *handle) {
    Batch *b = handle;
    if (!b) return;
    for (int c = 0; c < b->nc; ++c) {
        if (b->kind[c] == 0) alldiff_free(b->plans[c]);
        else sum_free(b->plans[c]);
    }
    free(b->lengths); free(b->offsets); free(b->starts); free(b->variables);
    free(b->kind); free(b->ops); free(b->targets); free(b->local);
    free(b->cache_offsets); free(b->adjstarts); free(b->adjacency);
    free(b->queue); free(b->queued); free(b->cached); free(b->plans);
    free(b->domains); free(b->input); free(b->output); free(b->cache); free(b);
}

/* Ownership of plans transfers only on successful creation. */
void *batch_create(int nv, int nc, const int *lengths, const int *starts,
                   const int *variables, const int *kind, const int *ops,
                   const int *targets, void *const *plans) {
    if (nv < 1 || nv > 2048 || nc < 1 || nc > 4096 || !lengths || !starts ||
        !variables || !kind || !ops || !targets || !plans || starts[0] != 0) return NULL;
    int words = 0, entries = 0, local_words = 0, max_local = 0, max_words = 0;
    for (int v = 0; v < nv; ++v) {
        if (lengths[v] < 1 || lengths[v] > 2048) return NULL;
        entries += lengths[v]; words += (lengths[v]+63)/64;
        if ((lengths[v]+63)/64 > max_words) max_words = (lengths[v]+63)/64;
    }
    if (entries > 1048576) return NULL;
    for (int c = 0; c < nc; ++c) {
        if (starts[c+1] <= starts[c] || starts[c+1] > 262144 ||
            kind[c] < 0 || kind[c] > 1 || ops[c] < 0 || ops[c] > 2 || !plans[c]) return NULL;
        int row = 0;
        for (int j = starts[c]; j < starts[c+1]; ++j) {
            int v = variables[j];
            if (v < 0 || v >= nv) return NULL;
            for (int k = starts[c]; k < j; ++k) if (variables[k] == v) return NULL;
            row += (lengths[v]+63)/64;
        }
        local_words += row;
        if (row > max_local) max_local = row;
    }
    if (local_words > 1048576) return NULL;
    Batch *b = calloc(1, sizeof(*b));
    if (!b) return NULL;
#define B_ALLOC(field, size, type) do { \
    b->field = calloc((size_t)(size), sizeof(type)); \
    if (!b->field) { batch_free(b); return NULL; } \
} while (0)
    B_ALLOC(lengths, nv, int); B_ALLOC(offsets, nv+1, int);
    B_ALLOC(starts, nc+1, int); B_ALLOC(variables, starts[nc], int);
    B_ALLOC(kind, nc, int); B_ALLOC(ops, nc, int); B_ALLOC(targets, nc, int);
    B_ALLOC(local, starts[nc], int); B_ALLOC(cache_offsets, nc+1, int);
    B_ALLOC(adjstarts, nv+1, int); B_ALLOC(adjacency, starts[nc], int);
    B_ALLOC(queue, nc+1, int); B_ALLOC(queued, nc, unsigned char);
    B_ALLOC(cached, nc, unsigned char); B_ALLOC(plans, nc, void *);
    B_ALLOC(domains, words, uint64_t); B_ALLOC(input, max_local, uint64_t);
    B_ALLOC(output, max_local, uint64_t); B_ALLOC(cache, local_words, uint64_t);
#undef B_ALLOC
    b->nv = nv; b->words = words; b->scope_entries = starts[nc];
    b->local_words = local_words; b->max_local_words = max_local;
    b->log_stride = max_words+2;
    memcpy(b->lengths, lengths, (size_t)nv*sizeof(int));
    memcpy(b->starts, starts, (size_t)(nc+1)*sizeof(int));
    memcpy(b->variables, variables, (size_t)starts[nc]*sizeof(int));
    memcpy(b->kind, kind, (size_t)nc*sizeof(int));
    memcpy(b->ops, ops, (size_t)nc*sizeof(int));
    memcpy(b->targets, targets, (size_t)nc*sizeof(int));
    for (int v = 0; v < nv; ++v) b->offsets[v+1] = b->offsets[v]+(lengths[v]+63)/64;
    for (int c = 0; c < nc; ++c) {
        int offset = 0;
        for (int j = starts[c]; j < starts[c+1]; ++j) {
            int v = variables[j]; b->local[j] = offset;
            offset += b->offsets[v+1]-b->offsets[v]; ++b->adjstarts[v+1];
        }
        b->cache_offsets[c+1] = b->cache_offsets[c]+offset;
    }
    for (int v = 0; v < nv; ++v) b->adjstarts[v+1] += b->adjstarts[v];
    for (int v = 0; v < nv; ++v) {
        int at = b->adjstarts[v];
        for (int c = 0; c < nc; ++c)
            for (int j = starts[c]; j < starts[c+1]; ++j)
                if (variables[j] == v) b->adjacency[at++] = c;
    }
    memcpy(b->plans, plans, (size_t)nc*sizeof(void *));
    b->nc = nc; /* Publish ownership only after every allocation succeeds. */
    return b;
}

#if !defined(MODEL_SPECIALIZED) || defined(MODEL_HAS_INEQUALITY)
static inline int batch_inequality(Sum *s, const uint64_t *input, int target, int op,
                            uint64_t *output) {
    int low[MAX_N], high[MAX_N], lower = 0, upper = 0;
    memcpy(output, input, (size_t)s->words*sizeof(uint64_t));
    for (int i = 0; i < s->n; ++i) {
        low[i] = MAX_SPAN+1; high[i] = -1;
        for (int w = s->masks[i]; w < s->masks[i+1]; ++w) {
            uint64_t bits = input[w];
            while (bits) {
                int p = 64*(w-s->masks[i])+__builtin_ctzll(bits); bits &= bits-1;
                int v = s->values[s->starts[i]+p];
                if (v < low[i]) low[i] = v;
                if (v > high[i]) high[i] = v;
            }
        }
        if (high[i] < 0) return 0;
        lower += low[i]; upper += high[i];
    }
    if ((op == 1 && lower > target) || (op == 2 && upper < target)) return 0;
    for (int i = 0; i < s->n; ++i)
        for (int w = s->masks[i]; w < s->masks[i+1]; ++w) {
            uint64_t bits = input[w];
            while (bits) {
                int p = 64*(w-s->masks[i])+__builtin_ctzll(bits); bits &= bits-1;
                int v = s->values[s->starts[i]+p];
                if ((op == 1 && v+lower-low[i] > target) ||
                    (op == 2 && v+upper-high[i] < target))
                    output[w] &= ~(UINT64_C(1) << (p&63));
            }
        }
    return 1;
}
#endif

static int batch_cached(Batch *b, int c, int words) {
    if (b->cached[c] && memcmp(b->input, b->cache+b->cache_offsets[c],
                               (size_t)words*sizeof(uint64_t)) == 0) {
        ++b->counts[2]; return 1;
    }
    return 0;
}

static int batch_store(Batch *b, int c, int v, int local, int offset, int words) {
    int changed = 0;
    for (int w = 0; w < words; ++w)
        if ((b->domains[offset+w] & b->output[local+w]) != b->domains[offset+w]) changed = 1;
    if (!changed) return 1;
    if (b->log && b->log_count >= b->log_capacity) return -2;
    uint64_t *log = b->log ? b->log+(size_t)b->log_count*b->log_stride : NULL;
    if (log) {
        memset(log, 0, (size_t)b->log_stride*sizeof(uint64_t)); log[0] = (uint64_t)c; log[1] = (uint64_t)v;
    }
    b->counts[4] = (b->counts[4] ^ (uint64_t)c)*UINT64_C(1099511628211);
    b->counts[4] = (b->counts[4] ^ (uint64_t)v)*UINT64_C(1099511628211);
    for (int w = 0; w < words; ++w) {
        b->domains[offset+w] &= b->output[local+w];
        if (log) log[w+2] = b->domains[offset+w];
        b->counts[4] = (b->counts[4] ^ b->domains[offset+w])*UINT64_C(1099511628211);
    }
    ++b->log_count; ++b->counts[3]; batch_notify(b, v);
    return 1;
}

#ifndef MODEL_SPECIALIZED
static int batch_generic_step(Batch *b, int c) {
    int words = b->cache_offsets[c+1]-b->cache_offsets[c];
    for (int j = b->starts[c]; j < b->starts[c+1]; ++j) {
        int v = b->variables[j], offset = b->offsets[v];
        memcpy(b->input+b->local[j], b->domains+offset,
               (size_t)(b->offsets[v+1]-offset)*sizeof(uint64_t));
    }
    if (batch_cached(b, c, words)) return 1;
    ++b->counts[1];
    int status;
    if (b->kind[c] == 0) status = alldiff_supports(b->plans[c], b->input, b->output);
    else if (b->ops[c] == 0) {
        if (b->targets[c] < 0 || b->targets[c] > MAX_SPAN) status = 0;
        else status = sum_supports(b->plans[c], b->input, b->targets[c], b->output);
    } else status = batch_inequality(b->plans[c], b->input, b->targets[c], b->ops[c], b->output);
    if (status <= 0) return status;
    memcpy(b->cache+b->cache_offsets[c], b->output, (size_t)words*sizeof(uint64_t)); b->cached[c] = 1;
    for (int j = b->starts[c]; j < b->starts[c+1]; ++j) {
        int v = b->variables[j], offset = b->offsets[v];
        status = batch_store(b, c, v, b->local[j], offset, b->offsets[v+1]-offset);
        if (status < 0) return status;
    }
    return 1;
}
#endif

/* Six counters: revisions, support calls, cache hits, reductions, digest,
 * first failing constraint + 1 (0 = no named failure). Negative status is
 * interruption/error and must never be interpreted as infeasibility.
 */
int batch_run(void *handle, const uint64_t *input, uint64_t *output, int reset,
              uint64_t *log, int capacity, uint64_t *counts, int max_revisions,
              double seconds) {
    Batch *b = handle;
    if (!b || !input || !output || !counts || capacity < 0 || max_revisions < 1) return -1;
    memset(b->counts, 0, sizeof(b->counts)); b->counts[4] = UINT64_C(1469598103934665603);
    b->head = b->tail = b->used = 0; memset(b->queued, 0, (size_t)b->nc);
    b->log = log; b->log_capacity = capacity; b->log_count = 0;
    int status = 1, begun = 0, all = reset || !b->have_domains || b->prior_status <= 0;
    struct timespec start, now;
    if (seconds >= 0 && timespec_get(&start, TIME_UTC) != TIME_UTC) return -5;
    for (int v = 0; v < b->nv; ++v) {
        int at = b->offsets[v], words = b->offsets[v+1]-at, length = b->lengths[v], nonempty = 0;
        if ((length&63) && (input[at+words-1] >> (length&63))) { status = -1; goto done; }
        for (int w = 0; w < words; ++w) if (input[at+w]) nonempty = 1;
        if (!nonempty) { status = 0; goto done; }
        if (all || memcmp(input+at, b->domains+at, (size_t)words*sizeof(uint64_t)) != 0)
            for (int j = b->adjstarts[v]; j < b->adjstarts[v+1]; ++j)
                b->queued[b->adjacency[j]] = 1;
    }
    memcpy(b->domains, input, (size_t)b->words*sizeof(uint64_t));
    begun = 1;
    for (int c = 0; c < b->nc; ++c) if (all || b->queued[c]) {
        b->queued[c] = 0; batch_enqueue(b, c);
    }
    while (b->used) {
        if (seconds >= 0) {
            if (timespec_get(&now, TIME_UTC) != TIME_UTC) { status = -5; break; }
            double elapsed = (double)(now.tv_sec-start.tv_sec)+(double)(now.tv_nsec-start.tv_nsec)*1e-9;
            if (elapsed >= seconds) { status = -4; break; }
        }
        if (b->counts[0] >= (uint64_t)max_revisions) { status = -3; break; }
        int c = b->queue[b->head]; b->head = (b->head+1) % (b->nc+1); --b->used; b->queued[c] = 0;
        ++b->counts[0];
#ifdef MODEL_SPECIALIZED
        status = batch_special_step(b, c);
#else
        status = batch_generic_step(b, c);
#endif
        if (status <= 0) { if (status == 0) b->counts[5] = (uint64_t)c+1; break; }
    }
    b->have_domains = 1;
done:
    if (!begun) memcpy(b->domains, input, (size_t)b->words*sizeof(uint64_t));
    b->prior_status = status;
    memcpy(output, b->domains, (size_t)b->words*sizeof(uint64_t));
    memcpy(counts, b->counts, sizeof(b->counts));
    return status;
}
