/* Exact ALLDIFF support filtering in immutable canonical value coordinates.
 * The matching is a validated hint, including after domain widening/rollback.
 * No allocation inside alldiff_supports; domain mutation remains in Python.
 */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define MAX_VALUES 2048
#define MAX_ENTRIES 262144
#define BIT(v) (UINT64_C(1) << ((v) & 63))
#define HAS(a,v) (((a)[(v) >> 6] & BIT(v)) != 0)
#define SET(a,v) ((a)[(v) >> 6] |= BIT(v))

typedef struct {
    int n, count, words, local_words;
    int *starts, *positions, *offsets, *identity;
    int *matching, *owners, *unmatched, *sizes, *parents, *queue;
    int *order, *stack, *cursor, *components;
    uint64_t *masks, *graph, *reverse, *universe, *occupied, *seen, *reaches, *allowed;
} AllDiff;

void alldiff_free(void *handle) {
    AllDiff *p = handle;
    if (!p) return;
    free(p->starts); free(p->positions); free(p->offsets); free(p->identity);
    free(p->matching); free(p->owners); free(p->unmatched); free(p->sizes);
    free(p->parents); free(p->queue); free(p->order); free(p->stack);
    free(p->cursor); free(p->components);
    free(p->masks); free(p->graph); free(p->reverse); free(p->universe);
    free(p->occupied); free(p->seen); free(p->reaches); free(p->allowed);
    free(p);
}

void *alldiff_create(int n, int count, const int *starts, const int *positions) {
    if (n < 1 || n > MAX_VALUES || count < 1 || count > MAX_VALUES ||
        !starts || !positions || starts[0] != 0) return NULL;
    for (int i = 0; i < n; ++i)
        if (starts[i+1] <= starts[i] || starts[i+1]-starts[i] > count ||
            starts[i+1] > MAX_ENTRIES) return NULL;
    AllDiff *p = calloc(1, sizeof(*p));
    if (!p) return NULL;
    p->n = n; p->count = count; p->words = (count+63)/64;
#define ALLOC(field, size, type) do { \
    p->field = calloc((size_t)(size), sizeof(type)); \
    if (!p->field) { alldiff_free(p); return NULL; } \
} while (0)
    ALLOC(starts, n+1, int); ALLOC(positions, starts[n], int);
    ALLOC(offsets, n+1, int); ALLOC(identity, n, int);
    ALLOC(matching, n, int); ALLOC(owners, count, int);
    ALLOC(unmatched, n, int); ALLOC(sizes, n, int);
    ALLOC(parents, count, int); ALLOC(queue, count+1, int);
    ALLOC(order, count, int); ALLOC(stack, count, int);
    ALLOC(cursor, count, int); ALLOC(components, count, int);
    ALLOC(masks, n*p->words, uint64_t);
    ALLOC(graph, count*p->words, uint64_t);
    ALLOC(reverse, count*p->words, uint64_t);
    ALLOC(universe, p->words, uint64_t); ALLOC(occupied, p->words, uint64_t);
    ALLOC(seen, p->words, uint64_t); ALLOC(reaches, p->words, uint64_t);
    ALLOC(allowed, p->words, uint64_t);
#undef ALLOC
    memcpy(p->starts, starts, (size_t)(n+1)*sizeof(int));
    memcpy(p->positions, positions, (size_t)starts[n]*sizeof(int));
    for (int v = 0; v < count; ++v) p->owners[v] = -1;
    for (int i = 0; i < n; ++i) {
        p->matching[i] = -1;
        int length = starts[i+1]-starts[i];
        p->offsets[i+1] = p->offsets[i]+(length+63)/64;
        memset(p->seen, 0, (size_t)p->words*sizeof(uint64_t));
        p->identity[i] = 1;
        for (int j = 0; j < length; ++j) {
            int v = positions[starts[i]+j];
            if (v < 0 || v >= count || HAS(p->seen, v)) {
                alldiff_free(p); return NULL;
            }
            SET(p->seen, v);
            if (v != j) p->identity[i] = 0;
        }
    }
    p->local_words = p->offsets[n];
    return p;
}

static int match(AllDiff *p) {
    int repairs = 0, w = p->words;
    for (int i = 0; i < p->n; ++i) {
        int v = p->matching[i];
        if (v >= 0 && HAS(p->masks+i*w, v)) continue;
        if (v >= 0) { p->matching[i] = -1; p->owners[v] = -1; }
        /* Stable insertion sort, same repair order as Python. */
        int j = repairs++;
        while (j > 0 && p->sizes[p->unmatched[j-1]] > p->sizes[i]) {
            p->unmatched[j] = p->unmatched[j-1]; --j;
        }
        p->unmatched[j] = i;
    }
    if (!repairs) return 1;
    memset(p->occupied, 0, (size_t)w*sizeof(uint64_t));
    for (int i = 0; i < p->n; ++i)
        if (p->matching[i] >= 0) SET(p->occupied, p->matching[i]);
    for (int r = 0; r < repairs; ++r) {
        int start = p->unmatched[r], end = -1;
        const uint64_t *row = p->masks+start*w;
        for (int k = 0; k < w; ++k) {
            uint64_t free_values = row[k] & ~p->occupied[k];
            if (free_values) { end = 64*k+__builtin_ctzll(free_values); break; }
        }
        if (end >= 0) {
            p->matching[start] = end; p->owners[end] = start;
            SET(p->occupied, end); continue;
        }
        memset(p->seen, 0, (size_t)w*sizeof(uint64_t));
        int head = 0, tail = 1;
        p->queue[0] = start;
        while (head < tail && end < 0) {
            int variable = p->queue[head++];
            row = p->masks+variable*w;
            for (int k = 0; k < w; ++k) {
                uint64_t choices = row[k] & ~p->seen[k];
                p->seen[k] |= choices;
                while (choices) {
                    int v = 64*k+__builtin_ctzll(choices);
                    choices &= choices-1;
                    p->parents[v] = variable;
                    int owner = p->owners[v];
                    if (owner < 0) { end = v; break; }
                    p->queue[tail++] = owner;
                }
                if (end >= 0) break;
            }
        }
        if (end < 0) return 0;
        SET(p->occupied, end);
        while (end >= 0) {
            int variable = p->parents[end], previous = p->matching[variable];
            p->matching[variable] = end; p->owners[end] = variable;
            end = previous;
        }
    }
    return 1;
}

/* Flood reverse edges, using the preallocated queue. */
static void reach_free(AllDiff *p) {
    int head = 0, tail = 0, w = p->words;
    for (int k = 0; k < w; ++k) {
        uint64_t bits = p->universe[k] & ~p->occupied[k];
        p->reaches[k] = bits;
        while (bits) {
            p->queue[tail++] = 64*k+__builtin_ctzll(bits); bits &= bits-1;
        }
    }
    while (head < tail) {
        const uint64_t *row = p->reverse+p->queue[head++]*w;
        for (int k = 0; k < w; ++k) {
            uint64_t bits = row[k] & ~p->reaches[k];
            p->reaches[k] |= bits;
            while (bits) {
                p->queue[tail++] = 64*k+__builtin_ctzll(bits); bits &= bits-1;
            }
        }
    }
}

static void components(AllDiff *p) {
    int w = p->words, used = 0;
    memset(p->seen, 0, (size_t)w*sizeof(uint64_t));
    for (int v = 0; v < p->count; ++v) p->components[v] = -1;
    /* Iterative Kosaraju: each row cursor advances monotonically. */
    for (int root = 0; root < p->count; ++root) {
        if (!HAS(p->allowed, root) || HAS(p->seen, root)) continue;
        int depth = 1;
        p->stack[0] = root; p->cursor[root] = 0; SET(p->seen, root);
        while (depth) {
            int v = p->stack[depth-1], k = p->cursor[v], child = -1;
            const uint64_t *row = p->graph+v*w;
            while (k < w) {
                uint64_t bits = row[k] & p->allowed[k] & ~p->seen[k];
                if (bits) { child = 64*k+__builtin_ctzll(bits); break; }
                ++k;
            }
            p->cursor[v] = k;
            if (child < 0) { p->order[used++] = v; --depth; }
            else {
                SET(p->seen, child); p->cursor[child] = 0;
                p->stack[depth++] = child;
            }
        }
    }
    int component = 0;
    while (used) {
        int root = p->order[--used];
        if (p->components[root] >= 0) continue;
        int head = 0, tail = 1;
        p->queue[0] = root; p->components[root] = component;
        while (head < tail) {
            const uint64_t *row = p->reverse+p->queue[head++]*w;
            for (int k = 0; k < w; ++k) {
                uint64_t bits = row[k] & p->allowed[k];
                while (bits) {
                    int child = 64*k+__builtin_ctzll(bits); bits &= bits-1;
                    if (p->components[child] < 0) {
                        p->components[child] = component;
                        p->queue[tail++] = child;
                    }
                }
            }
        }
        ++component;
    }
}

/* 1 = exact supports, 0 = no matching, -1 = invalid caller input. */
int alldiff_supports(void *handle, const uint64_t *input, uint64_t *output) {
    AllDiff *p = handle;
    if (!p || !input || !output) return -1;
    int w = p->words;
    memset(p->universe, 0, (size_t)w*sizeof(uint64_t));
    memset(p->masks, 0, (size_t)p->n*w*sizeof(uint64_t));
    for (int i = 0; i < p->n; ++i) {
        int length = p->starts[i+1]-p->starts[i], words = p->offsets[i+1]-p->offsets[i];
        const uint64_t *local = input+p->offsets[i];
        uint64_t *row = p->masks+i*w;
        if ((length & 63) && (local[words-1] >> (length & 63))) return -1;
        int size = 0;
        for (int k = 0; k < words; ++k) {
            uint64_t bits = local[k];
            size += __builtin_popcountll(bits);
            if (p->identity[i]) row[k] = bits;
            else while (bits) {
                int j = 64*k+__builtin_ctzll(bits); bits &= bits-1;
                SET(row, p->positions[p->starts[i]+j]);
            }
        }
        if (!size) return 0;
        p->sizes[i] = size;
        for (int k = 0; k < w; ++k) p->universe[k] |= row[k];
    }
    int size = 0;
    for (int k = 0; k < w; ++k) size += __builtin_popcountll(p->universe[k]);
    if (size < p->n || !match(p)) return 0;
    memset(p->graph, 0, (size_t)p->count*w*sizeof(uint64_t));
    memset(p->reverse, 0, (size_t)p->count*w*sizeof(uint64_t));
    memset(p->occupied, 0, (size_t)w*sizeof(uint64_t));
    memset(p->allowed, 0, (size_t)w*sizeof(uint64_t));
    for (int i = 0; i < p->n; ++i) {
        int v = p->matching[i];
        const uint64_t *row = p->masks+i*w;
        memcpy(p->graph+v*w, row, (size_t)w*sizeof(uint64_t)); SET(p->occupied, v);
        if (p->sizes[i] == 1) SET(p->allowed, v); /* singleton exclusion */
        for (int k = 0; k < w; ++k) {
            uint64_t bits = row[k];
            while (bits) {
                int destination = 64*k+__builtin_ctzll(bits); bits &= bits-1;
                SET(p->reverse+destination*w, v);
            }
        }
    }
    reach_free(p);
    for (int k = 0; k < w; ++k)
        p->allowed[k] = p->universe[k] & ~(p->allowed[k] | p->reaches[k]);
    components(p);
    memset(output, 0, (size_t)p->local_words*sizeof(uint64_t));
    for (int i = 0; i < p->n; ++i) {
        int own = p->matching[i], component = p->components[own];
        const uint64_t *local = input+p->offsets[i];
        uint64_t *supported = output+p->offsets[i];
        for (int k = 0; k < p->offsets[i+1]-p->offsets[i]; ++k) {
            uint64_t bits = local[k];
            while (bits) {
                int j = 64*k+__builtin_ctzll(bits); bits &= bits-1;
                int v = p->positions[p->starts[i]+j];
                if (v == own || HAS(p->reaches, v) ||
                    (component >= 0 && p->components[v] == component)) SET(supported, j);
            }
        }
    }
    return 1;
}

void alldiff_matching(void *handle, int *matching, int *owners) {
    AllDiff *p = handle;
    if (!p || !matching || !owners) return;
    memcpy(matching, p->matching, (size_t)p->n*sizeof(int));
    memcpy(owners, p->owners, (size_t)p->count*sizeof(int));
}
