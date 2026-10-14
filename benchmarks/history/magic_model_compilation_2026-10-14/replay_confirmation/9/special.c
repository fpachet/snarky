#define MODEL_SPECIALIZED 1

/* Experimental exact equality supports. Immutable normalized contributions;
   caller-owned domains/trail. One private scratch workspace per numeric plan. */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define MAX_N 64
#define MAX_SPAN 16384
#define MAX_WORDS (MAX_SPAN / 64 + 1)
#define MAX_COLUMN 4096
#define MAX_ENTRIES 262144

typedef struct {
    int n, entries, words, stride;
    int starts[MAX_N + 1], masks[MAX_N + 1], positions[MAX_N + 1];
    int *values, *lookup;
    uint64_t *prefix;
    uint64_t backward[MAX_WORDS], next[MAX_WORDS], shifted[MAX_WORDS];
} Sum;

void sum_free(void *pointer) {
    Sum *s = pointer;
    if (!s) return;
    free(s->values); free(s->lookup); free(s->prefix); free(s);
}

void *sum_create(int n, const int *starts, const int *values) {
    if (n < 1 || n > MAX_N || starts[0] != 0) return NULL;
    int span = 0, mask_words = 0;
    for (int i = 0; i < n; ++i) {
        int count = starts[i + 1] - starts[i], high = 0, low = MAX_SPAN;
        if (count < 1 || count > MAX_COLUMN || starts[i + 1] > MAX_ENTRIES)
            return NULL;
        for (int p = starts[i]; p < starts[i + 1]; ++p) {
            if (values[p] < 0 || values[p] > MAX_SPAN) return NULL;
            if (values[p] > high) high = values[p];
            if (values[p] < low) low = values[p];
        }
        if (low != 0 || span + high > MAX_SPAN) return NULL;
        span += high;
        mask_words += (count + 63) / 64;
    }
    Sum *s = calloc(1, sizeof(Sum));
    if (!s) return NULL;
    s->n = n; s->entries = starts[n]; s->words = mask_words;
    s->stride = (span / 2 + 64) / 64;
    memcpy(s->starts, starts, (n + 1) * sizeof(int));
    s->values = malloc(starts[n] * sizeof(int));
    s->lookup = malloc((span + n) * sizeof(int));
    s->prefix = malloc((size_t)(n + 1) * s->stride * sizeof(uint64_t));
    if (!s->values || !s->lookup || !s->prefix) { sum_free(s); return NULL; }
    memcpy(s->values, values, starts[n] * sizeof(int));
    for (int p = 0; p < span + n; ++p) s->lookup[p] = -1;
    for (int i = 0; i < n; ++i) {
        int high = 0, count = starts[i + 1] - starts[i];
        s->masks[i + 1] = s->masks[i] + (count + 63) / 64;
        for (int p = starts[i]; p < starts[i + 1]; ++p) {
            int value = values[p];
            if (value > high) high = value;
            int *position = &s->lookup[s->positions[i] + value];
            if (*position >= 0) { sum_free(s); return NULL; }
            *position = p - starts[i];
        }
        s->positions[i + 1] = s->positions[i] + high + 1;
    }
    return s;
}

static int member(const Sum *s, const uint64_t *masks, int i, int value) {
    if (value < 0 || value >= s->positions[i + 1] - s->positions[i]) return -1;
    int p = s->lookup[s->positions[i] + value];
    if (p < 0 || !(masks[s->masks[i] + p / 64] & (UINT64_C(1) << (p % 64))))
        return -1;
    return p;
}

static void set_candidate(const Sum *s, uint64_t *output, int i, int p) {
    output[s->masks[i] + p / 64] |= UINT64_C(1) << (p % 64);
}

static void shift_left_or(uint64_t *dst, const uint64_t *src, int words, int offset) {
    int whole = offset / 64, part = offset % 64;
    for (int j = 0; j + whole < words; ++j) {
        dst[j + whole] |= src[j] << part;
        if (part && j + whole + 1 < words)
            dst[j + whole + 1] |= src[j] >> (64 - part);
    }
}

/* Return 0 on contradiction, 1..6 for the successful computation path,
   -1 on unsupported input. No partial reduction may be used after -1. */
int sum_supports(void *pointer, const uint64_t *masks, int target, uint64_t *output) {
    Sum *s = pointer;
    if (!s || target < 0 || target > MAX_SPAN) return -1;
    int lo[MAX_N], hi[MAX_N], count[MAX_N], width[MAX_N], holes[MAX_N];
    int active[MAX_N], k = 0, lower = 0, span = 0, widest = 0, max_holes = 0;
    memcpy(output, masks, s->words * sizeof(uint64_t));
    for (int i = 0; i < s->n; ++i) {
        count[i] = 0; lo[i] = MAX_SPAN; hi[i] = 0;
        int size = s->starts[i + 1] - s->starts[i];
        if (size % 64 && masks[s->masks[i + 1] - 1] >> (size % 64)) return -1;
        for (int w = s->masks[i]; w < s->masks[i + 1]; ++w) {
            uint64_t pending = masks[w];
            while (pending) {
                int p = 64 * (w - s->masks[i]) + __builtin_ctzll(pending);
                pending &= pending - 1;
                int value = s->values[s->starts[i] + p];
                if (value < lo[i]) lo[i] = value;
                if (value > hi[i]) hi[i] = value;
                count[i]++;
            }
        }
        if (!count[i]) return 0;
        lower += lo[i]; width[i] = hi[i] - lo[i]; span += width[i];
        holes[i] = width[i] + 1 - count[i];
        if (width[i] > widest) widest = width[i];
        if (holes[i] > max_holes) max_holes = holes[i];
        if (count[i] > 1) active[k++] = i;
    }
    int residual = target - lower;
    if (residual < 0 || residual > span) return 0;
    if (!k) return 1;
    if (k == 1) {
        int i = active[0], p = member(s, masks, i, residual + lo[i]);
        if (p < 0) return 0;
        memset(output + s->masks[i], 0, (s->masks[i + 1] - s->masks[i]) * sizeof(uint64_t));
        set_candidate(s, output, i, p);
        return 2;
    }
    if (k == 2) {
        int a = active[0], b = active[1];
        if (count[a] > count[b]) { int swap = a; a = b; b = swap; }
        memset(output + s->masks[a], 0, (s->masks[a + 1] - s->masks[a]) * sizeof(uint64_t));
        memset(output + s->masks[b], 0, (s->masks[b + 1] - s->masks[b]) * sizeof(uint64_t));
        int found = 0, remaining = residual + lo[a] + lo[b];
        for (int w = s->masks[a]; w < s->masks[a + 1]; ++w) {
            uint64_t pending = masks[w];
            while (pending) {
                int p = 64 * (w - s->masks[a]) + __builtin_ctzll(pending);
                pending &= pending - 1;
                int q = member(s, masks, b, remaining - s->values[s->starts[a] + p]);
                if (q >= 0) { set_candidate(s, output, a, p); set_candidate(s, output, b, q); found = 1; }
            }
        }
        return found ? 3 : 0;
    }
    if (!max_holes) {
        for (int i = 0; i < s->n; ++i) {
            int min = residual - span + hi[i], max = residual + lo[i];
            if (lo[i] >= min && hi[i] <= max) continue;
            for (int w = s->masks[i]; w < s->masks[i + 1]; ++w) {
                uint64_t pending = masks[w];
                while (pending) {
                    int bit = __builtin_ctzll(pending);
                    pending &= pending - 1;
                    int value = s->values[s->starts[i] + 64 * (w - s->masks[i]) + bit];
                    if (value < min || value > max) output[w] &= ~(UINT64_C(1) << bit);
                }
            }
        }
        return 4;
    }
    if (widest <= residual && residual <= span - widest) {
        int anchor[3] = {-1, -1, -1};
        for (int j = 0; j < k; ++j) {
            int i = active[j];
            for (int a = 0; a < 3; ++a) {
                int old = anchor[a];
                if (old < 0 || holes[i] < holes[old] || (holes[i] == holes[old] && width[i] > width[old])) {
                    for (int b = 2; b > a; --b) anchor[b] = anchor[b - 1];
                    anchor[a] = i; break;
                }
            }
        }
        int margin = holes[anchor[1]] + holes[anchor[2]];
        int w0 = width[anchor[0]], w1 = width[anchor[1]], w2 = width[anchor[2]];
        if (w0 > w1) { int t = w0; w0 = w1; w1 = t; }
        if (w1 > w2) { int t = w1; w1 = w2; w2 = t; }
        if (w0 > w1) { int t = w0; w0 = w1; w1 = t; }
        if (margin <= w0 && w0 + w1 - 2 * margin >= max_holes &&
            widest + margin <= residual && residual <= span - widest - margin) return 5;
    }
    int reflect = residual > span - residual;
    if (reflect) residual = span - residual;
    for (int i = 1; i < k; ++i) {
        int j = i, v = active[i];
        while (j && count[active[j - 1]] > count[v]) { active[j] = active[j - 1]; --j; }
        active[j] = v;
    }
    int boundary = active[k - 2];
    for (int i = k - 2; i > 0; --i) active[i] = active[i - 1];
    active[0] = boundary;
    int words = residual / 64 + 1;
    uint64_t tail = UINT64_MAX >> (63 - residual % 64);
    memset(s->prefix, 0, words * sizeof(uint64_t)); s->prefix[0] = 1;
    for (int j = 0; j < k - 1; ++j) {
        int i = active[j];
        uint64_t *previous = s->prefix + j * s->stride;
        uint64_t *next = s->prefix + (j + 1) * s->stride;
        memset(next, 0, words * sizeof(uint64_t));
        for (int w = s->masks[i]; w < s->masks[i + 1]; ++w) {
            uint64_t pending = masks[w];
            while (pending) {
                int p = 64 * (w - s->masks[i]) + __builtin_ctzll(pending);
                pending &= pending - 1;
                int value = s->values[s->starts[i] + p];
                int offset = reflect ? hi[i] - value : value - lo[i];
                if (offset <= residual) shift_left_or(next, previous, words, offset);
            }
        }
        next[words - 1] &= tail;
    }
    memset(s->backward, 0, words * sizeof(uint64_t));
    int last = active[k - 1], found = 0;
    memset(output + s->masks[last], 0, (s->masks[last + 1] - s->masks[last]) * sizeof(uint64_t));
    uint64_t *previous = s->prefix + (k - 1) * s->stride;
    for (int w = s->masks[last]; w < s->masks[last + 1]; ++w) {
        uint64_t pending = masks[w];
        while (pending) {
            int p = 64 * (w - s->masks[last]) + __builtin_ctzll(pending);
            pending &= pending - 1;
            int value = s->values[s->starts[last] + p];
            int offset = reflect ? hi[last] - value : value - lo[last];
            int sum = residual - offset;
            if (sum >= 0 && (previous[sum / 64] & (UINT64_C(1) << (sum % 64)))) {
                set_candidate(s, output, last, p); s->backward[sum / 64] |= UINT64_C(1) << (sum % 64); found = 1;
            }
        }
    }
    if (!found) return 0;
    for (int j = k - 2; j > 0; --j) {
        int i = active[j];
        memset(output + s->masks[i], 0, (s->masks[i + 1] - s->masks[i]) * sizeof(uint64_t));
        memset(s->next, 0, words * sizeof(uint64_t));
        previous = s->prefix + j * s->stride;
        for (int w = s->masks[i]; w < s->masks[i + 1]; ++w) {
            uint64_t pending = masks[w];
            while (pending) {
                int p = 64 * (w - s->masks[i]) + __builtin_ctzll(pending);
                pending &= pending - 1;
                int value = s->values[s->starts[i] + p];
                int offset = reflect ? hi[i] - value : value - lo[i];
                if (offset > residual) continue;
                int whole = offset / 64, part = offset % 64, supported = 0;
                for (int a = 0; a < words; ++a) {
                    uint64_t value = a + whole < words ? s->backward[a + whole] >> part : 0;
                    if (part && a + whole + 1 < words) value |= s->backward[a + whole + 1] << (64 - part);
                    s->shifted[a] = value;
                    if (previous[a] & value) supported = 1;
                }
                if (supported) {
                    set_candidate(s, output, i, p);
                    for (int a = 0; a < words; ++a) s->next[a] |= s->shifted[a];
                }
            }
        }
        memcpy(s->backward, s->next, words * sizeof(uint64_t));
    }
    int first = active[0];
    memset(output + s->masks[first], 0, (s->masks[first + 1] - s->masks[first]) * sizeof(uint64_t));
    for (int w = s->masks[first]; w < s->masks[first + 1]; ++w) {
        uint64_t pending = masks[w];
        while (pending) {
            int p = 64 * (w - s->masks[first]) + __builtin_ctzll(pending);
            pending &= pending - 1;
            int value = s->values[s->starts[first] + p];
            int offset = reflect ? hi[first] - value : value - lo[first];
            if (offset <= residual && (s->backward[offset / 64] & (UINT64_C(1) << (offset % 64)))) set_candidate(s, output, first, p);
        }
    }
    return 6;
}

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
    if (entries > 262144) return NULL;
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

const char *batch_model_key(void) { return "3504e66d343f598c1f9b2110cbd29169dcc38ef0b93af0e3b5888a646467822c"; }

static const int sum_shape_0_starts[] = {0,81,162,243,324,405,486,567,648,729};
static const int sum_shape_0_masks[] = {0,2,4,6,8,10,12,14,16,18};
static inline int sum_shape_0(void *pointer, const uint64_t *masks, uint64_t *output) {
const int target = 360;

    Sum *s = pointer;
    if (!s || target < 0 || target > MAX_SPAN) return -1;
    int lo[MAX_N], hi[MAX_N], count[MAX_N], width[MAX_N], holes[MAX_N];
    int active[MAX_N], k = 0, lower = 0, span = 0, widest = 0, max_holes = 0;
    memcpy(output, masks, 18 * sizeof(uint64_t));
    for (int i = 0; i < 9; ++i) {
        count[i] = 0; lo[i] = MAX_SPAN; hi[i] = 0;
        int size = sum_shape_0_starts[i + 1] - sum_shape_0_starts[i];
        if (size % 64 && masks[sum_shape_0_masks[i + 1] - 1] >> (size % 64)) return -1;
        for (int w = sum_shape_0_masks[i]; w < sum_shape_0_masks[i + 1]; ++w) {
            uint64_t pending = masks[w];
            while (pending) {
                int p = 64 * (w - sum_shape_0_masks[i]) + __builtin_ctzll(pending);
                pending &= pending - 1;
                int value = s->values[sum_shape_0_starts[i] + p];
                if (value < lo[i]) lo[i] = value;
                if (value > hi[i]) hi[i] = value;
                count[i]++;
            }
        }
        if (!count[i]) return 0;
        lower += lo[i]; width[i] = hi[i] - lo[i]; span += width[i];
        holes[i] = width[i] + 1 - count[i];
        if (width[i] > widest) widest = width[i];
        if (holes[i] > max_holes) max_holes = holes[i];
        if (count[i] > 1) active[k++] = i;
    }
    int residual = target - lower;
    if (residual < 0 || residual > span) return 0;
    if (!k) return 1;
    if (k == 1) {
        int i = active[0], p = member(s, masks, i, residual + lo[i]);
        if (p < 0) return 0;
        memset(output + sum_shape_0_masks[i], 0, (sum_shape_0_masks[i + 1] - sum_shape_0_masks[i]) * sizeof(uint64_t));
        set_candidate(s, output, i, p);
        return 2;
    }
    if (k == 2) {
        int a = active[0], b = active[1];
        if (count[a] > count[b]) { int swap = a; a = b; b = swap; }
        memset(output + sum_shape_0_masks[a], 0, (sum_shape_0_masks[a + 1] - sum_shape_0_masks[a]) * sizeof(uint64_t));
        memset(output + sum_shape_0_masks[b], 0, (sum_shape_0_masks[b + 1] - sum_shape_0_masks[b]) * sizeof(uint64_t));
        int found = 0, remaining = residual + lo[a] + lo[b];
        for (int w = sum_shape_0_masks[a]; w < sum_shape_0_masks[a + 1]; ++w) {
            uint64_t pending = masks[w];
            while (pending) {
                int p = 64 * (w - sum_shape_0_masks[a]) + __builtin_ctzll(pending);
                pending &= pending - 1;
                int q = member(s, masks, b, remaining - s->values[sum_shape_0_starts[a] + p]);
                if (q >= 0) { set_candidate(s, output, a, p); set_candidate(s, output, b, q); found = 1; }
            }
        }
        return found ? 3 : 0;
    }
    if (!max_holes) {
        for (int i = 0; i < 9; ++i) {
            int min = residual - span + hi[i], max = residual + lo[i];
            if (lo[i] >= min && hi[i] <= max) continue;
            for (int w = sum_shape_0_masks[i]; w < sum_shape_0_masks[i + 1]; ++w) {
                uint64_t pending = masks[w];
                while (pending) {
                    int bit = __builtin_ctzll(pending);
                    pending &= pending - 1;
                    int value = s->values[sum_shape_0_starts[i] + 64 * (w - sum_shape_0_masks[i]) + bit];
                    if (value < min || value > max) output[w] &= ~(UINT64_C(1) << bit);
                }
            }
        }
        return 4;
    }
    if (widest <= residual && residual <= span - widest) {
        int anchor[3] = {-1, -1, -1};
        for (int j = 0; j < k; ++j) {
            int i = active[j];
            for (int a = 0; a < 3; ++a) {
                int old = anchor[a];
                if (old < 0 || holes[i] < holes[old] || (holes[i] == holes[old] && width[i] > width[old])) {
                    for (int b = 2; b > a; --b) anchor[b] = anchor[b - 1];
                    anchor[a] = i; break;
                }
            }
        }
        int margin = holes[anchor[1]] + holes[anchor[2]];
        int w0 = width[anchor[0]], w1 = width[anchor[1]], w2 = width[anchor[2]];
        if (w0 > w1) { int t = w0; w0 = w1; w1 = t; }
        if (w1 > w2) { int t = w1; w1 = w2; w2 = t; }
        if (w0 > w1) { int t = w0; w0 = w1; w1 = t; }
        if (margin <= w0 && w0 + w1 - 2 * margin >= max_holes &&
            widest + margin <= residual && residual <= span - widest - margin) return 5;
    }
    int reflect = residual > span - residual;
    if (reflect) residual = span - residual;
    for (int i = 1; i < k; ++i) {
        int j = i, v = active[i];
        while (j && count[active[j - 1]] > count[v]) { active[j] = active[j - 1]; --j; }
        active[j] = v;
    }
    int boundary = active[k - 2];
    for (int i = k - 2; i > 0; --i) active[i] = active[i - 1];
    active[0] = boundary;
    int words = residual / 64 + 1;
    uint64_t tail = UINT64_MAX >> (63 - residual % 64);
    memset(s->prefix, 0, words * sizeof(uint64_t)); s->prefix[0] = 1;
    for (int j = 0; j < k - 1; ++j) {
        int i = active[j];
        uint64_t *previous = s->prefix + j * s->stride;
        uint64_t *next = s->prefix + (j + 1) * s->stride;
        memset(next, 0, words * sizeof(uint64_t));
        for (int w = sum_shape_0_masks[i]; w < sum_shape_0_masks[i + 1]; ++w) {
            uint64_t pending = masks[w];
            while (pending) {
                int p = 64 * (w - sum_shape_0_masks[i]) + __builtin_ctzll(pending);
                pending &= pending - 1;
                int value = s->values[sum_shape_0_starts[i] + p];
                int offset = reflect ? hi[i] - value : value - lo[i];
                if (offset <= residual) shift_left_or(next, previous, words, offset);
            }
        }
        next[words - 1] &= tail;
    }
    memset(s->backward, 0, words * sizeof(uint64_t));
    int last = active[k - 1], found = 0;
    memset(output + sum_shape_0_masks[last], 0, (sum_shape_0_masks[last + 1] - sum_shape_0_masks[last]) * sizeof(uint64_t));
    uint64_t *previous = s->prefix + (k - 1) * s->stride;
    for (int w = sum_shape_0_masks[last]; w < sum_shape_0_masks[last + 1]; ++w) {
        uint64_t pending = masks[w];
        while (pending) {
            int p = 64 * (w - sum_shape_0_masks[last]) + __builtin_ctzll(pending);
            pending &= pending - 1;
            int value = s->values[sum_shape_0_starts[last] + p];
            int offset = reflect ? hi[last] - value : value - lo[last];
            int sum = residual - offset;
            if (sum >= 0 && (previous[sum / 64] & (UINT64_C(1) << (sum % 64)))) {
                set_candidate(s, output, last, p); s->backward[sum / 64] |= UINT64_C(1) << (sum % 64); found = 1;
            }
        }
    }
    if (!found) return 0;
    for (int j = k - 2; j > 0; --j) {
        int i = active[j];
        memset(output + sum_shape_0_masks[i], 0, (sum_shape_0_masks[i + 1] - sum_shape_0_masks[i]) * sizeof(uint64_t));
        memset(s->next, 0, words * sizeof(uint64_t));
        previous = s->prefix + j * s->stride;
        for (int w = sum_shape_0_masks[i]; w < sum_shape_0_masks[i + 1]; ++w) {
            uint64_t pending = masks[w];
            while (pending) {
                int p = 64 * (w - sum_shape_0_masks[i]) + __builtin_ctzll(pending);
                pending &= pending - 1;
                int value = s->values[sum_shape_0_starts[i] + p];
                int offset = reflect ? hi[i] - value : value - lo[i];
                if (offset > residual) continue;
                int whole = offset / 64, part = offset % 64, supported = 0;
                for (int a = 0; a < words; ++a) {
                    uint64_t value = a + whole < words ? s->backward[a + whole] >> part : 0;
                    if (part && a + whole + 1 < words) value |= s->backward[a + whole + 1] << (64 - part);
                    s->shifted[a] = value;
                    if (previous[a] & value) supported = 1;
                }
                if (supported) {
                    set_candidate(s, output, i, p);
                    for (int a = 0; a < words; ++a) s->next[a] |= s->shifted[a];
                }
            }
        }
        memcpy(s->backward, s->next, words * sizeof(uint64_t));
    }
    int first = active[0];
    memset(output + sum_shape_0_masks[first], 0, (sum_shape_0_masks[first + 1] - sum_shape_0_masks[first]) * sizeof(uint64_t));
    for (int w = sum_shape_0_masks[first]; w < sum_shape_0_masks[first + 1]; ++w) {
        uint64_t pending = masks[w];
        while (pending) {
            int p = 64 * (w - sum_shape_0_masks[first]) + __builtin_ctzll(pending);
            pending &= pending - 1;
            int value = s->values[sum_shape_0_starts[first] + p];
            int offset = reflect ? hi[first] - value : value - lo[first];
            if (offset <= residual && (s->backward[offset / 64] & (UINT64_C(1) << (offset % 64)))) set_candidate(s, output, first, p);
        }
    }
    return 6;
}

static void batch_special_notify(Batch *b, int v) { switch (v) {
case 0: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 10);batch_enqueue(b, 19);break;
case 1: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 11);break;
case 2: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 12);break;
case 3: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 13);break;
case 4: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 14);break;
case 5: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 15);break;
case 6: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 16);break;
case 7: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 17);break;
case 8: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 18);batch_enqueue(b, 20);break;
case 9: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 10);break;
case 10: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 11);batch_enqueue(b, 19);break;
case 11: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 12);break;
case 12: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 13);break;
case 13: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 14);break;
case 14: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 15);break;
case 15: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 16);break;
case 16: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 17);batch_enqueue(b, 20);break;
case 17: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 18);break;
case 18: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 10);break;
case 19: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 11);break;
case 20: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 12);batch_enqueue(b, 19);break;
case 21: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 13);break;
case 22: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 14);break;
case 23: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 15);break;
case 24: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 16);batch_enqueue(b, 20);break;
case 25: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 17);break;
case 26: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 18);break;
case 27: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 10);break;
case 28: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 11);break;
case 29: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 12);break;
case 30: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 13);batch_enqueue(b, 19);break;
case 31: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 14);break;
case 32: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 15);batch_enqueue(b, 20);break;
case 33: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 16);break;
case 34: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 17);break;
case 35: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 18);break;
case 36: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 10);break;
case 37: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 11);break;
case 38: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 12);break;
case 39: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 13);break;
case 40: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 14);batch_enqueue(b, 19);batch_enqueue(b, 20);break;
case 41: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 15);break;
case 42: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 16);break;
case 43: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 17);break;
case 44: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 18);break;
case 45: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 10);break;
case 46: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 11);break;
case 47: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 12);break;
case 48: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 13);batch_enqueue(b, 20);break;
case 49: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 14);break;
case 50: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 15);batch_enqueue(b, 19);break;
case 51: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 16);break;
case 52: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 17);break;
case 53: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 18);break;
case 54: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 10);break;
case 55: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 11);break;
case 56: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 12);batch_enqueue(b, 20);break;
case 57: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 13);break;
case 58: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 14);break;
case 59: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 15);break;
case 60: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 16);batch_enqueue(b, 19);break;
case 61: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 17);break;
case 62: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 18);break;
case 63: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 10);break;
case 64: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 11);batch_enqueue(b, 20);break;
case 65: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 12);break;
case 66: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 13);break;
case 67: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 14);break;
case 68: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 15);break;
case 69: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 16);break;
case 70: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 17);batch_enqueue(b, 19);break;
case 71: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 18);break;
case 72: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 10);batch_enqueue(b, 20);break;
case 73: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 11);break;
case 74: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 12);break;
case 75: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 13);break;
case 76: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 14);break;
case 77: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 15);break;
case 78: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 16);break;
case 79: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 17);break;
case 80: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 18);batch_enqueue(b, 19);break;
default: break; } }
static int batch_step_0(Batch *b) {
int status;
memcpy(b->input+0, b->domains+0, 16);
memcpy(b->input+2, b->domains+2, 16);
memcpy(b->input+4, b->domains+4, 16);
memcpy(b->input+6, b->domains+6, 16);
memcpy(b->input+8, b->domains+8, 16);
memcpy(b->input+10, b->domains+10, 16);
memcpy(b->input+12, b->domains+12, 16);
memcpy(b->input+14, b->domains+14, 16);
memcpy(b->input+16, b->domains+16, 16);
memcpy(b->input+18, b->domains+18, 16);
memcpy(b->input+20, b->domains+20, 16);
memcpy(b->input+22, b->domains+22, 16);
memcpy(b->input+24, b->domains+24, 16);
memcpy(b->input+26, b->domains+26, 16);
memcpy(b->input+28, b->domains+28, 16);
memcpy(b->input+30, b->domains+30, 16);
memcpy(b->input+32, b->domains+32, 16);
memcpy(b->input+34, b->domains+34, 16);
memcpy(b->input+36, b->domains+36, 16);
memcpy(b->input+38, b->domains+38, 16);
memcpy(b->input+40, b->domains+40, 16);
memcpy(b->input+42, b->domains+42, 16);
memcpy(b->input+44, b->domains+44, 16);
memcpy(b->input+46, b->domains+46, 16);
memcpy(b->input+48, b->domains+48, 16);
memcpy(b->input+50, b->domains+50, 16);
memcpy(b->input+52, b->domains+52, 16);
memcpy(b->input+54, b->domains+54, 16);
memcpy(b->input+56, b->domains+56, 16);
memcpy(b->input+58, b->domains+58, 16);
memcpy(b->input+60, b->domains+60, 16);
memcpy(b->input+62, b->domains+62, 16);
memcpy(b->input+64, b->domains+64, 16);
memcpy(b->input+66, b->domains+66, 16);
memcpy(b->input+68, b->domains+68, 16);
memcpy(b->input+70, b->domains+70, 16);
memcpy(b->input+72, b->domains+72, 16);
memcpy(b->input+74, b->domains+74, 16);
memcpy(b->input+76, b->domains+76, 16);
memcpy(b->input+78, b->domains+78, 16);
memcpy(b->input+80, b->domains+80, 16);
memcpy(b->input+82, b->domains+82, 16);
memcpy(b->input+84, b->domains+84, 16);
memcpy(b->input+86, b->domains+86, 16);
memcpy(b->input+88, b->domains+88, 16);
memcpy(b->input+90, b->domains+90, 16);
memcpy(b->input+92, b->domains+92, 16);
memcpy(b->input+94, b->domains+94, 16);
memcpy(b->input+96, b->domains+96, 16);
memcpy(b->input+98, b->domains+98, 16);
memcpy(b->input+100, b->domains+100, 16);
memcpy(b->input+102, b->domains+102, 16);
memcpy(b->input+104, b->domains+104, 16);
memcpy(b->input+106, b->domains+106, 16);
memcpy(b->input+108, b->domains+108, 16);
memcpy(b->input+110, b->domains+110, 16);
memcpy(b->input+112, b->domains+112, 16);
memcpy(b->input+114, b->domains+114, 16);
memcpy(b->input+116, b->domains+116, 16);
memcpy(b->input+118, b->domains+118, 16);
memcpy(b->input+120, b->domains+120, 16);
memcpy(b->input+122, b->domains+122, 16);
memcpy(b->input+124, b->domains+124, 16);
memcpy(b->input+126, b->domains+126, 16);
memcpy(b->input+128, b->domains+128, 16);
memcpy(b->input+130, b->domains+130, 16);
memcpy(b->input+132, b->domains+132, 16);
memcpy(b->input+134, b->domains+134, 16);
memcpy(b->input+136, b->domains+136, 16);
memcpy(b->input+138, b->domains+138, 16);
memcpy(b->input+140, b->domains+140, 16);
memcpy(b->input+142, b->domains+142, 16);
memcpy(b->input+144, b->domains+144, 16);
memcpy(b->input+146, b->domains+146, 16);
memcpy(b->input+148, b->domains+148, 16);
memcpy(b->input+150, b->domains+150, 16);
memcpy(b->input+152, b->domains+152, 16);
memcpy(b->input+154, b->domains+154, 16);
memcpy(b->input+156, b->domains+156, 16);
memcpy(b->input+158, b->domains+158, 16);
memcpy(b->input+160, b->domains+160, 16);
if (batch_cached(b, 0, 162)) return 1;
++b->counts[1];
status = alldiff_supports(b->plans[0], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+0, b->output, 1296); b->cached[0] = 1;
status = batch_store(b, 0, 0, 0, 0, 2);
if (status < 0) return status;
status = batch_store(b, 0, 1, 2, 2, 2);
if (status < 0) return status;
status = batch_store(b, 0, 2, 4, 4, 2);
if (status < 0) return status;
status = batch_store(b, 0, 3, 6, 6, 2);
if (status < 0) return status;
status = batch_store(b, 0, 4, 8, 8, 2);
if (status < 0) return status;
status = batch_store(b, 0, 5, 10, 10, 2);
if (status < 0) return status;
status = batch_store(b, 0, 6, 12, 12, 2);
if (status < 0) return status;
status = batch_store(b, 0, 7, 14, 14, 2);
if (status < 0) return status;
status = batch_store(b, 0, 8, 16, 16, 2);
if (status < 0) return status;
status = batch_store(b, 0, 9, 18, 18, 2);
if (status < 0) return status;
status = batch_store(b, 0, 10, 20, 20, 2);
if (status < 0) return status;
status = batch_store(b, 0, 11, 22, 22, 2);
if (status < 0) return status;
status = batch_store(b, 0, 12, 24, 24, 2);
if (status < 0) return status;
status = batch_store(b, 0, 13, 26, 26, 2);
if (status < 0) return status;
status = batch_store(b, 0, 14, 28, 28, 2);
if (status < 0) return status;
status = batch_store(b, 0, 15, 30, 30, 2);
if (status < 0) return status;
status = batch_store(b, 0, 16, 32, 32, 2);
if (status < 0) return status;
status = batch_store(b, 0, 17, 34, 34, 2);
if (status < 0) return status;
status = batch_store(b, 0, 18, 36, 36, 2);
if (status < 0) return status;
status = batch_store(b, 0, 19, 38, 38, 2);
if (status < 0) return status;
status = batch_store(b, 0, 20, 40, 40, 2);
if (status < 0) return status;
status = batch_store(b, 0, 21, 42, 42, 2);
if (status < 0) return status;
status = batch_store(b, 0, 22, 44, 44, 2);
if (status < 0) return status;
status = batch_store(b, 0, 23, 46, 46, 2);
if (status < 0) return status;
status = batch_store(b, 0, 24, 48, 48, 2);
if (status < 0) return status;
status = batch_store(b, 0, 25, 50, 50, 2);
if (status < 0) return status;
status = batch_store(b, 0, 26, 52, 52, 2);
if (status < 0) return status;
status = batch_store(b, 0, 27, 54, 54, 2);
if (status < 0) return status;
status = batch_store(b, 0, 28, 56, 56, 2);
if (status < 0) return status;
status = batch_store(b, 0, 29, 58, 58, 2);
if (status < 0) return status;
status = batch_store(b, 0, 30, 60, 60, 2);
if (status < 0) return status;
status = batch_store(b, 0, 31, 62, 62, 2);
if (status < 0) return status;
status = batch_store(b, 0, 32, 64, 64, 2);
if (status < 0) return status;
status = batch_store(b, 0, 33, 66, 66, 2);
if (status < 0) return status;
status = batch_store(b, 0, 34, 68, 68, 2);
if (status < 0) return status;
status = batch_store(b, 0, 35, 70, 70, 2);
if (status < 0) return status;
status = batch_store(b, 0, 36, 72, 72, 2);
if (status < 0) return status;
status = batch_store(b, 0, 37, 74, 74, 2);
if (status < 0) return status;
status = batch_store(b, 0, 38, 76, 76, 2);
if (status < 0) return status;
status = batch_store(b, 0, 39, 78, 78, 2);
if (status < 0) return status;
status = batch_store(b, 0, 40, 80, 80, 2);
if (status < 0) return status;
status = batch_store(b, 0, 41, 82, 82, 2);
if (status < 0) return status;
status = batch_store(b, 0, 42, 84, 84, 2);
if (status < 0) return status;
status = batch_store(b, 0, 43, 86, 86, 2);
if (status < 0) return status;
status = batch_store(b, 0, 44, 88, 88, 2);
if (status < 0) return status;
status = batch_store(b, 0, 45, 90, 90, 2);
if (status < 0) return status;
status = batch_store(b, 0, 46, 92, 92, 2);
if (status < 0) return status;
status = batch_store(b, 0, 47, 94, 94, 2);
if (status < 0) return status;
status = batch_store(b, 0, 48, 96, 96, 2);
if (status < 0) return status;
status = batch_store(b, 0, 49, 98, 98, 2);
if (status < 0) return status;
status = batch_store(b, 0, 50, 100, 100, 2);
if (status < 0) return status;
status = batch_store(b, 0, 51, 102, 102, 2);
if (status < 0) return status;
status = batch_store(b, 0, 52, 104, 104, 2);
if (status < 0) return status;
status = batch_store(b, 0, 53, 106, 106, 2);
if (status < 0) return status;
status = batch_store(b, 0, 54, 108, 108, 2);
if (status < 0) return status;
status = batch_store(b, 0, 55, 110, 110, 2);
if (status < 0) return status;
status = batch_store(b, 0, 56, 112, 112, 2);
if (status < 0) return status;
status = batch_store(b, 0, 57, 114, 114, 2);
if (status < 0) return status;
status = batch_store(b, 0, 58, 116, 116, 2);
if (status < 0) return status;
status = batch_store(b, 0, 59, 118, 118, 2);
if (status < 0) return status;
status = batch_store(b, 0, 60, 120, 120, 2);
if (status < 0) return status;
status = batch_store(b, 0, 61, 122, 122, 2);
if (status < 0) return status;
status = batch_store(b, 0, 62, 124, 124, 2);
if (status < 0) return status;
status = batch_store(b, 0, 63, 126, 126, 2);
if (status < 0) return status;
status = batch_store(b, 0, 64, 128, 128, 2);
if (status < 0) return status;
status = batch_store(b, 0, 65, 130, 130, 2);
if (status < 0) return status;
status = batch_store(b, 0, 66, 132, 132, 2);
if (status < 0) return status;
status = batch_store(b, 0, 67, 134, 134, 2);
if (status < 0) return status;
status = batch_store(b, 0, 68, 136, 136, 2);
if (status < 0) return status;
status = batch_store(b, 0, 69, 138, 138, 2);
if (status < 0) return status;
status = batch_store(b, 0, 70, 140, 140, 2);
if (status < 0) return status;
status = batch_store(b, 0, 71, 142, 142, 2);
if (status < 0) return status;
status = batch_store(b, 0, 72, 144, 144, 2);
if (status < 0) return status;
status = batch_store(b, 0, 73, 146, 146, 2);
if (status < 0) return status;
status = batch_store(b, 0, 74, 148, 148, 2);
if (status < 0) return status;
status = batch_store(b, 0, 75, 150, 150, 2);
if (status < 0) return status;
status = batch_store(b, 0, 76, 152, 152, 2);
if (status < 0) return status;
status = batch_store(b, 0, 77, 154, 154, 2);
if (status < 0) return status;
status = batch_store(b, 0, 78, 156, 156, 2);
if (status < 0) return status;
status = batch_store(b, 0, 79, 158, 158, 2);
if (status < 0) return status;
status = batch_store(b, 0, 80, 160, 160, 2);
if (status < 0) return status;
return 1; }
static int batch_step_1(Batch *b) {
int status;
memcpy(b->input+0, b->domains+0, 16);
memcpy(b->input+2, b->domains+2, 16);
memcpy(b->input+4, b->domains+4, 16);
memcpy(b->input+6, b->domains+6, 16);
memcpy(b->input+8, b->domains+8, 16);
memcpy(b->input+10, b->domains+10, 16);
memcpy(b->input+12, b->domains+12, 16);
memcpy(b->input+14, b->domains+14, 16);
memcpy(b->input+16, b->domains+16, 16);
if (batch_cached(b, 1, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[1], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+162, b->output, 144); b->cached[1] = 1;
status = batch_store(b, 1, 0, 0, 0, 2);
if (status < 0) return status;
status = batch_store(b, 1, 1, 2, 2, 2);
if (status < 0) return status;
status = batch_store(b, 1, 2, 4, 4, 2);
if (status < 0) return status;
status = batch_store(b, 1, 3, 6, 6, 2);
if (status < 0) return status;
status = batch_store(b, 1, 4, 8, 8, 2);
if (status < 0) return status;
status = batch_store(b, 1, 5, 10, 10, 2);
if (status < 0) return status;
status = batch_store(b, 1, 6, 12, 12, 2);
if (status < 0) return status;
status = batch_store(b, 1, 7, 14, 14, 2);
if (status < 0) return status;
status = batch_store(b, 1, 8, 16, 16, 2);
if (status < 0) return status;
return 1; }
static int batch_step_2(Batch *b) {
int status;
memcpy(b->input+0, b->domains+18, 16);
memcpy(b->input+2, b->domains+20, 16);
memcpy(b->input+4, b->domains+22, 16);
memcpy(b->input+6, b->domains+24, 16);
memcpy(b->input+8, b->domains+26, 16);
memcpy(b->input+10, b->domains+28, 16);
memcpy(b->input+12, b->domains+30, 16);
memcpy(b->input+14, b->domains+32, 16);
memcpy(b->input+16, b->domains+34, 16);
if (batch_cached(b, 2, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[2], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+180, b->output, 144); b->cached[2] = 1;
status = batch_store(b, 2, 9, 0, 18, 2);
if (status < 0) return status;
status = batch_store(b, 2, 10, 2, 20, 2);
if (status < 0) return status;
status = batch_store(b, 2, 11, 4, 22, 2);
if (status < 0) return status;
status = batch_store(b, 2, 12, 6, 24, 2);
if (status < 0) return status;
status = batch_store(b, 2, 13, 8, 26, 2);
if (status < 0) return status;
status = batch_store(b, 2, 14, 10, 28, 2);
if (status < 0) return status;
status = batch_store(b, 2, 15, 12, 30, 2);
if (status < 0) return status;
status = batch_store(b, 2, 16, 14, 32, 2);
if (status < 0) return status;
status = batch_store(b, 2, 17, 16, 34, 2);
if (status < 0) return status;
return 1; }
static int batch_step_3(Batch *b) {
int status;
memcpy(b->input+0, b->domains+36, 16);
memcpy(b->input+2, b->domains+38, 16);
memcpy(b->input+4, b->domains+40, 16);
memcpy(b->input+6, b->domains+42, 16);
memcpy(b->input+8, b->domains+44, 16);
memcpy(b->input+10, b->domains+46, 16);
memcpy(b->input+12, b->domains+48, 16);
memcpy(b->input+14, b->domains+50, 16);
memcpy(b->input+16, b->domains+52, 16);
if (batch_cached(b, 3, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[3], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+198, b->output, 144); b->cached[3] = 1;
status = batch_store(b, 3, 18, 0, 36, 2);
if (status < 0) return status;
status = batch_store(b, 3, 19, 2, 38, 2);
if (status < 0) return status;
status = batch_store(b, 3, 20, 4, 40, 2);
if (status < 0) return status;
status = batch_store(b, 3, 21, 6, 42, 2);
if (status < 0) return status;
status = batch_store(b, 3, 22, 8, 44, 2);
if (status < 0) return status;
status = batch_store(b, 3, 23, 10, 46, 2);
if (status < 0) return status;
status = batch_store(b, 3, 24, 12, 48, 2);
if (status < 0) return status;
status = batch_store(b, 3, 25, 14, 50, 2);
if (status < 0) return status;
status = batch_store(b, 3, 26, 16, 52, 2);
if (status < 0) return status;
return 1; }
static int batch_step_4(Batch *b) {
int status;
memcpy(b->input+0, b->domains+54, 16);
memcpy(b->input+2, b->domains+56, 16);
memcpy(b->input+4, b->domains+58, 16);
memcpy(b->input+6, b->domains+60, 16);
memcpy(b->input+8, b->domains+62, 16);
memcpy(b->input+10, b->domains+64, 16);
memcpy(b->input+12, b->domains+66, 16);
memcpy(b->input+14, b->domains+68, 16);
memcpy(b->input+16, b->domains+70, 16);
if (batch_cached(b, 4, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[4], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+216, b->output, 144); b->cached[4] = 1;
status = batch_store(b, 4, 27, 0, 54, 2);
if (status < 0) return status;
status = batch_store(b, 4, 28, 2, 56, 2);
if (status < 0) return status;
status = batch_store(b, 4, 29, 4, 58, 2);
if (status < 0) return status;
status = batch_store(b, 4, 30, 6, 60, 2);
if (status < 0) return status;
status = batch_store(b, 4, 31, 8, 62, 2);
if (status < 0) return status;
status = batch_store(b, 4, 32, 10, 64, 2);
if (status < 0) return status;
status = batch_store(b, 4, 33, 12, 66, 2);
if (status < 0) return status;
status = batch_store(b, 4, 34, 14, 68, 2);
if (status < 0) return status;
status = batch_store(b, 4, 35, 16, 70, 2);
if (status < 0) return status;
return 1; }
static int batch_step_5(Batch *b) {
int status;
memcpy(b->input+0, b->domains+72, 16);
memcpy(b->input+2, b->domains+74, 16);
memcpy(b->input+4, b->domains+76, 16);
memcpy(b->input+6, b->domains+78, 16);
memcpy(b->input+8, b->domains+80, 16);
memcpy(b->input+10, b->domains+82, 16);
memcpy(b->input+12, b->domains+84, 16);
memcpy(b->input+14, b->domains+86, 16);
memcpy(b->input+16, b->domains+88, 16);
if (batch_cached(b, 5, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[5], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+234, b->output, 144); b->cached[5] = 1;
status = batch_store(b, 5, 36, 0, 72, 2);
if (status < 0) return status;
status = batch_store(b, 5, 37, 2, 74, 2);
if (status < 0) return status;
status = batch_store(b, 5, 38, 4, 76, 2);
if (status < 0) return status;
status = batch_store(b, 5, 39, 6, 78, 2);
if (status < 0) return status;
status = batch_store(b, 5, 40, 8, 80, 2);
if (status < 0) return status;
status = batch_store(b, 5, 41, 10, 82, 2);
if (status < 0) return status;
status = batch_store(b, 5, 42, 12, 84, 2);
if (status < 0) return status;
status = batch_store(b, 5, 43, 14, 86, 2);
if (status < 0) return status;
status = batch_store(b, 5, 44, 16, 88, 2);
if (status < 0) return status;
return 1; }
static int batch_step_6(Batch *b) {
int status;
memcpy(b->input+0, b->domains+90, 16);
memcpy(b->input+2, b->domains+92, 16);
memcpy(b->input+4, b->domains+94, 16);
memcpy(b->input+6, b->domains+96, 16);
memcpy(b->input+8, b->domains+98, 16);
memcpy(b->input+10, b->domains+100, 16);
memcpy(b->input+12, b->domains+102, 16);
memcpy(b->input+14, b->domains+104, 16);
memcpy(b->input+16, b->domains+106, 16);
if (batch_cached(b, 6, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[6], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+252, b->output, 144); b->cached[6] = 1;
status = batch_store(b, 6, 45, 0, 90, 2);
if (status < 0) return status;
status = batch_store(b, 6, 46, 2, 92, 2);
if (status < 0) return status;
status = batch_store(b, 6, 47, 4, 94, 2);
if (status < 0) return status;
status = batch_store(b, 6, 48, 6, 96, 2);
if (status < 0) return status;
status = batch_store(b, 6, 49, 8, 98, 2);
if (status < 0) return status;
status = batch_store(b, 6, 50, 10, 100, 2);
if (status < 0) return status;
status = batch_store(b, 6, 51, 12, 102, 2);
if (status < 0) return status;
status = batch_store(b, 6, 52, 14, 104, 2);
if (status < 0) return status;
status = batch_store(b, 6, 53, 16, 106, 2);
if (status < 0) return status;
return 1; }
static int batch_step_7(Batch *b) {
int status;
memcpy(b->input+0, b->domains+108, 16);
memcpy(b->input+2, b->domains+110, 16);
memcpy(b->input+4, b->domains+112, 16);
memcpy(b->input+6, b->domains+114, 16);
memcpy(b->input+8, b->domains+116, 16);
memcpy(b->input+10, b->domains+118, 16);
memcpy(b->input+12, b->domains+120, 16);
memcpy(b->input+14, b->domains+122, 16);
memcpy(b->input+16, b->domains+124, 16);
if (batch_cached(b, 7, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[7], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+270, b->output, 144); b->cached[7] = 1;
status = batch_store(b, 7, 54, 0, 108, 2);
if (status < 0) return status;
status = batch_store(b, 7, 55, 2, 110, 2);
if (status < 0) return status;
status = batch_store(b, 7, 56, 4, 112, 2);
if (status < 0) return status;
status = batch_store(b, 7, 57, 6, 114, 2);
if (status < 0) return status;
status = batch_store(b, 7, 58, 8, 116, 2);
if (status < 0) return status;
status = batch_store(b, 7, 59, 10, 118, 2);
if (status < 0) return status;
status = batch_store(b, 7, 60, 12, 120, 2);
if (status < 0) return status;
status = batch_store(b, 7, 61, 14, 122, 2);
if (status < 0) return status;
status = batch_store(b, 7, 62, 16, 124, 2);
if (status < 0) return status;
return 1; }
static int batch_step_8(Batch *b) {
int status;
memcpy(b->input+0, b->domains+126, 16);
memcpy(b->input+2, b->domains+128, 16);
memcpy(b->input+4, b->domains+130, 16);
memcpy(b->input+6, b->domains+132, 16);
memcpy(b->input+8, b->domains+134, 16);
memcpy(b->input+10, b->domains+136, 16);
memcpy(b->input+12, b->domains+138, 16);
memcpy(b->input+14, b->domains+140, 16);
memcpy(b->input+16, b->domains+142, 16);
if (batch_cached(b, 8, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[8], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+288, b->output, 144); b->cached[8] = 1;
status = batch_store(b, 8, 63, 0, 126, 2);
if (status < 0) return status;
status = batch_store(b, 8, 64, 2, 128, 2);
if (status < 0) return status;
status = batch_store(b, 8, 65, 4, 130, 2);
if (status < 0) return status;
status = batch_store(b, 8, 66, 6, 132, 2);
if (status < 0) return status;
status = batch_store(b, 8, 67, 8, 134, 2);
if (status < 0) return status;
status = batch_store(b, 8, 68, 10, 136, 2);
if (status < 0) return status;
status = batch_store(b, 8, 69, 12, 138, 2);
if (status < 0) return status;
status = batch_store(b, 8, 70, 14, 140, 2);
if (status < 0) return status;
status = batch_store(b, 8, 71, 16, 142, 2);
if (status < 0) return status;
return 1; }
static int batch_step_9(Batch *b) {
int status;
memcpy(b->input+0, b->domains+144, 16);
memcpy(b->input+2, b->domains+146, 16);
memcpy(b->input+4, b->domains+148, 16);
memcpy(b->input+6, b->domains+150, 16);
memcpy(b->input+8, b->domains+152, 16);
memcpy(b->input+10, b->domains+154, 16);
memcpy(b->input+12, b->domains+156, 16);
memcpy(b->input+14, b->domains+158, 16);
memcpy(b->input+16, b->domains+160, 16);
if (batch_cached(b, 9, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[9], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+306, b->output, 144); b->cached[9] = 1;
status = batch_store(b, 9, 72, 0, 144, 2);
if (status < 0) return status;
status = batch_store(b, 9, 73, 2, 146, 2);
if (status < 0) return status;
status = batch_store(b, 9, 74, 4, 148, 2);
if (status < 0) return status;
status = batch_store(b, 9, 75, 6, 150, 2);
if (status < 0) return status;
status = batch_store(b, 9, 76, 8, 152, 2);
if (status < 0) return status;
status = batch_store(b, 9, 77, 10, 154, 2);
if (status < 0) return status;
status = batch_store(b, 9, 78, 12, 156, 2);
if (status < 0) return status;
status = batch_store(b, 9, 79, 14, 158, 2);
if (status < 0) return status;
status = batch_store(b, 9, 80, 16, 160, 2);
if (status < 0) return status;
return 1; }
static int batch_step_10(Batch *b) {
int status;
memcpy(b->input+0, b->domains+0, 16);
memcpy(b->input+2, b->domains+18, 16);
memcpy(b->input+4, b->domains+36, 16);
memcpy(b->input+6, b->domains+54, 16);
memcpy(b->input+8, b->domains+72, 16);
memcpy(b->input+10, b->domains+90, 16);
memcpy(b->input+12, b->domains+108, 16);
memcpy(b->input+14, b->domains+126, 16);
memcpy(b->input+16, b->domains+144, 16);
if (batch_cached(b, 10, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[10], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+324, b->output, 144); b->cached[10] = 1;
status = batch_store(b, 10, 0, 0, 0, 2);
if (status < 0) return status;
status = batch_store(b, 10, 9, 2, 18, 2);
if (status < 0) return status;
status = batch_store(b, 10, 18, 4, 36, 2);
if (status < 0) return status;
status = batch_store(b, 10, 27, 6, 54, 2);
if (status < 0) return status;
status = batch_store(b, 10, 36, 8, 72, 2);
if (status < 0) return status;
status = batch_store(b, 10, 45, 10, 90, 2);
if (status < 0) return status;
status = batch_store(b, 10, 54, 12, 108, 2);
if (status < 0) return status;
status = batch_store(b, 10, 63, 14, 126, 2);
if (status < 0) return status;
status = batch_store(b, 10, 72, 16, 144, 2);
if (status < 0) return status;
return 1; }
static int batch_step_11(Batch *b) {
int status;
memcpy(b->input+0, b->domains+2, 16);
memcpy(b->input+2, b->domains+20, 16);
memcpy(b->input+4, b->domains+38, 16);
memcpy(b->input+6, b->domains+56, 16);
memcpy(b->input+8, b->domains+74, 16);
memcpy(b->input+10, b->domains+92, 16);
memcpy(b->input+12, b->domains+110, 16);
memcpy(b->input+14, b->domains+128, 16);
memcpy(b->input+16, b->domains+146, 16);
if (batch_cached(b, 11, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[11], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+342, b->output, 144); b->cached[11] = 1;
status = batch_store(b, 11, 1, 0, 2, 2);
if (status < 0) return status;
status = batch_store(b, 11, 10, 2, 20, 2);
if (status < 0) return status;
status = batch_store(b, 11, 19, 4, 38, 2);
if (status < 0) return status;
status = batch_store(b, 11, 28, 6, 56, 2);
if (status < 0) return status;
status = batch_store(b, 11, 37, 8, 74, 2);
if (status < 0) return status;
status = batch_store(b, 11, 46, 10, 92, 2);
if (status < 0) return status;
status = batch_store(b, 11, 55, 12, 110, 2);
if (status < 0) return status;
status = batch_store(b, 11, 64, 14, 128, 2);
if (status < 0) return status;
status = batch_store(b, 11, 73, 16, 146, 2);
if (status < 0) return status;
return 1; }
static int batch_step_12(Batch *b) {
int status;
memcpy(b->input+0, b->domains+4, 16);
memcpy(b->input+2, b->domains+22, 16);
memcpy(b->input+4, b->domains+40, 16);
memcpy(b->input+6, b->domains+58, 16);
memcpy(b->input+8, b->domains+76, 16);
memcpy(b->input+10, b->domains+94, 16);
memcpy(b->input+12, b->domains+112, 16);
memcpy(b->input+14, b->domains+130, 16);
memcpy(b->input+16, b->domains+148, 16);
if (batch_cached(b, 12, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[12], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+360, b->output, 144); b->cached[12] = 1;
status = batch_store(b, 12, 2, 0, 4, 2);
if (status < 0) return status;
status = batch_store(b, 12, 11, 2, 22, 2);
if (status < 0) return status;
status = batch_store(b, 12, 20, 4, 40, 2);
if (status < 0) return status;
status = batch_store(b, 12, 29, 6, 58, 2);
if (status < 0) return status;
status = batch_store(b, 12, 38, 8, 76, 2);
if (status < 0) return status;
status = batch_store(b, 12, 47, 10, 94, 2);
if (status < 0) return status;
status = batch_store(b, 12, 56, 12, 112, 2);
if (status < 0) return status;
status = batch_store(b, 12, 65, 14, 130, 2);
if (status < 0) return status;
status = batch_store(b, 12, 74, 16, 148, 2);
if (status < 0) return status;
return 1; }
static int batch_step_13(Batch *b) {
int status;
memcpy(b->input+0, b->domains+6, 16);
memcpy(b->input+2, b->domains+24, 16);
memcpy(b->input+4, b->domains+42, 16);
memcpy(b->input+6, b->domains+60, 16);
memcpy(b->input+8, b->domains+78, 16);
memcpy(b->input+10, b->domains+96, 16);
memcpy(b->input+12, b->domains+114, 16);
memcpy(b->input+14, b->domains+132, 16);
memcpy(b->input+16, b->domains+150, 16);
if (batch_cached(b, 13, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[13], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+378, b->output, 144); b->cached[13] = 1;
status = batch_store(b, 13, 3, 0, 6, 2);
if (status < 0) return status;
status = batch_store(b, 13, 12, 2, 24, 2);
if (status < 0) return status;
status = batch_store(b, 13, 21, 4, 42, 2);
if (status < 0) return status;
status = batch_store(b, 13, 30, 6, 60, 2);
if (status < 0) return status;
status = batch_store(b, 13, 39, 8, 78, 2);
if (status < 0) return status;
status = batch_store(b, 13, 48, 10, 96, 2);
if (status < 0) return status;
status = batch_store(b, 13, 57, 12, 114, 2);
if (status < 0) return status;
status = batch_store(b, 13, 66, 14, 132, 2);
if (status < 0) return status;
status = batch_store(b, 13, 75, 16, 150, 2);
if (status < 0) return status;
return 1; }
static int batch_step_14(Batch *b) {
int status;
memcpy(b->input+0, b->domains+8, 16);
memcpy(b->input+2, b->domains+26, 16);
memcpy(b->input+4, b->domains+44, 16);
memcpy(b->input+6, b->domains+62, 16);
memcpy(b->input+8, b->domains+80, 16);
memcpy(b->input+10, b->domains+98, 16);
memcpy(b->input+12, b->domains+116, 16);
memcpy(b->input+14, b->domains+134, 16);
memcpy(b->input+16, b->domains+152, 16);
if (batch_cached(b, 14, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[14], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+396, b->output, 144); b->cached[14] = 1;
status = batch_store(b, 14, 4, 0, 8, 2);
if (status < 0) return status;
status = batch_store(b, 14, 13, 2, 26, 2);
if (status < 0) return status;
status = batch_store(b, 14, 22, 4, 44, 2);
if (status < 0) return status;
status = batch_store(b, 14, 31, 6, 62, 2);
if (status < 0) return status;
status = batch_store(b, 14, 40, 8, 80, 2);
if (status < 0) return status;
status = batch_store(b, 14, 49, 10, 98, 2);
if (status < 0) return status;
status = batch_store(b, 14, 58, 12, 116, 2);
if (status < 0) return status;
status = batch_store(b, 14, 67, 14, 134, 2);
if (status < 0) return status;
status = batch_store(b, 14, 76, 16, 152, 2);
if (status < 0) return status;
return 1; }
static int batch_step_15(Batch *b) {
int status;
memcpy(b->input+0, b->domains+10, 16);
memcpy(b->input+2, b->domains+28, 16);
memcpy(b->input+4, b->domains+46, 16);
memcpy(b->input+6, b->domains+64, 16);
memcpy(b->input+8, b->domains+82, 16);
memcpy(b->input+10, b->domains+100, 16);
memcpy(b->input+12, b->domains+118, 16);
memcpy(b->input+14, b->domains+136, 16);
memcpy(b->input+16, b->domains+154, 16);
if (batch_cached(b, 15, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[15], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+414, b->output, 144); b->cached[15] = 1;
status = batch_store(b, 15, 5, 0, 10, 2);
if (status < 0) return status;
status = batch_store(b, 15, 14, 2, 28, 2);
if (status < 0) return status;
status = batch_store(b, 15, 23, 4, 46, 2);
if (status < 0) return status;
status = batch_store(b, 15, 32, 6, 64, 2);
if (status < 0) return status;
status = batch_store(b, 15, 41, 8, 82, 2);
if (status < 0) return status;
status = batch_store(b, 15, 50, 10, 100, 2);
if (status < 0) return status;
status = batch_store(b, 15, 59, 12, 118, 2);
if (status < 0) return status;
status = batch_store(b, 15, 68, 14, 136, 2);
if (status < 0) return status;
status = batch_store(b, 15, 77, 16, 154, 2);
if (status < 0) return status;
return 1; }
static int batch_step_16(Batch *b) {
int status;
memcpy(b->input+0, b->domains+12, 16);
memcpy(b->input+2, b->domains+30, 16);
memcpy(b->input+4, b->domains+48, 16);
memcpy(b->input+6, b->domains+66, 16);
memcpy(b->input+8, b->domains+84, 16);
memcpy(b->input+10, b->domains+102, 16);
memcpy(b->input+12, b->domains+120, 16);
memcpy(b->input+14, b->domains+138, 16);
memcpy(b->input+16, b->domains+156, 16);
if (batch_cached(b, 16, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[16], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+432, b->output, 144); b->cached[16] = 1;
status = batch_store(b, 16, 6, 0, 12, 2);
if (status < 0) return status;
status = batch_store(b, 16, 15, 2, 30, 2);
if (status < 0) return status;
status = batch_store(b, 16, 24, 4, 48, 2);
if (status < 0) return status;
status = batch_store(b, 16, 33, 6, 66, 2);
if (status < 0) return status;
status = batch_store(b, 16, 42, 8, 84, 2);
if (status < 0) return status;
status = batch_store(b, 16, 51, 10, 102, 2);
if (status < 0) return status;
status = batch_store(b, 16, 60, 12, 120, 2);
if (status < 0) return status;
status = batch_store(b, 16, 69, 14, 138, 2);
if (status < 0) return status;
status = batch_store(b, 16, 78, 16, 156, 2);
if (status < 0) return status;
return 1; }
static int batch_step_17(Batch *b) {
int status;
memcpy(b->input+0, b->domains+14, 16);
memcpy(b->input+2, b->domains+32, 16);
memcpy(b->input+4, b->domains+50, 16);
memcpy(b->input+6, b->domains+68, 16);
memcpy(b->input+8, b->domains+86, 16);
memcpy(b->input+10, b->domains+104, 16);
memcpy(b->input+12, b->domains+122, 16);
memcpy(b->input+14, b->domains+140, 16);
memcpy(b->input+16, b->domains+158, 16);
if (batch_cached(b, 17, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[17], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+450, b->output, 144); b->cached[17] = 1;
status = batch_store(b, 17, 7, 0, 14, 2);
if (status < 0) return status;
status = batch_store(b, 17, 16, 2, 32, 2);
if (status < 0) return status;
status = batch_store(b, 17, 25, 4, 50, 2);
if (status < 0) return status;
status = batch_store(b, 17, 34, 6, 68, 2);
if (status < 0) return status;
status = batch_store(b, 17, 43, 8, 86, 2);
if (status < 0) return status;
status = batch_store(b, 17, 52, 10, 104, 2);
if (status < 0) return status;
status = batch_store(b, 17, 61, 12, 122, 2);
if (status < 0) return status;
status = batch_store(b, 17, 70, 14, 140, 2);
if (status < 0) return status;
status = batch_store(b, 17, 79, 16, 158, 2);
if (status < 0) return status;
return 1; }
static int batch_step_18(Batch *b) {
int status;
memcpy(b->input+0, b->domains+16, 16);
memcpy(b->input+2, b->domains+34, 16);
memcpy(b->input+4, b->domains+52, 16);
memcpy(b->input+6, b->domains+70, 16);
memcpy(b->input+8, b->domains+88, 16);
memcpy(b->input+10, b->domains+106, 16);
memcpy(b->input+12, b->domains+124, 16);
memcpy(b->input+14, b->domains+142, 16);
memcpy(b->input+16, b->domains+160, 16);
if (batch_cached(b, 18, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[18], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+468, b->output, 144); b->cached[18] = 1;
status = batch_store(b, 18, 8, 0, 16, 2);
if (status < 0) return status;
status = batch_store(b, 18, 17, 2, 34, 2);
if (status < 0) return status;
status = batch_store(b, 18, 26, 4, 52, 2);
if (status < 0) return status;
status = batch_store(b, 18, 35, 6, 70, 2);
if (status < 0) return status;
status = batch_store(b, 18, 44, 8, 88, 2);
if (status < 0) return status;
status = batch_store(b, 18, 53, 10, 106, 2);
if (status < 0) return status;
status = batch_store(b, 18, 62, 12, 124, 2);
if (status < 0) return status;
status = batch_store(b, 18, 71, 14, 142, 2);
if (status < 0) return status;
status = batch_store(b, 18, 80, 16, 160, 2);
if (status < 0) return status;
return 1; }
static int batch_step_19(Batch *b) {
int status;
memcpy(b->input+0, b->domains+0, 16);
memcpy(b->input+2, b->domains+20, 16);
memcpy(b->input+4, b->domains+40, 16);
memcpy(b->input+6, b->domains+60, 16);
memcpy(b->input+8, b->domains+80, 16);
memcpy(b->input+10, b->domains+100, 16);
memcpy(b->input+12, b->domains+120, 16);
memcpy(b->input+14, b->domains+140, 16);
memcpy(b->input+16, b->domains+160, 16);
if (batch_cached(b, 19, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[19], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+486, b->output, 144); b->cached[19] = 1;
status = batch_store(b, 19, 0, 0, 0, 2);
if (status < 0) return status;
status = batch_store(b, 19, 10, 2, 20, 2);
if (status < 0) return status;
status = batch_store(b, 19, 20, 4, 40, 2);
if (status < 0) return status;
status = batch_store(b, 19, 30, 6, 60, 2);
if (status < 0) return status;
status = batch_store(b, 19, 40, 8, 80, 2);
if (status < 0) return status;
status = batch_store(b, 19, 50, 10, 100, 2);
if (status < 0) return status;
status = batch_store(b, 19, 60, 12, 120, 2);
if (status < 0) return status;
status = batch_store(b, 19, 70, 14, 140, 2);
if (status < 0) return status;
status = batch_store(b, 19, 80, 16, 160, 2);
if (status < 0) return status;
return 1; }
static int batch_step_20(Batch *b) {
int status;
memcpy(b->input+0, b->domains+16, 16);
memcpy(b->input+2, b->domains+32, 16);
memcpy(b->input+4, b->domains+48, 16);
memcpy(b->input+6, b->domains+64, 16);
memcpy(b->input+8, b->domains+80, 16);
memcpy(b->input+10, b->domains+96, 16);
memcpy(b->input+12, b->domains+112, 16);
memcpy(b->input+14, b->domains+128, 16);
memcpy(b->input+16, b->domains+144, 16);
if (batch_cached(b, 20, 18)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[20], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+504, b->output, 144); b->cached[20] = 1;
status = batch_store(b, 20, 8, 0, 16, 2);
if (status < 0) return status;
status = batch_store(b, 20, 16, 2, 32, 2);
if (status < 0) return status;
status = batch_store(b, 20, 24, 4, 48, 2);
if (status < 0) return status;
status = batch_store(b, 20, 32, 6, 64, 2);
if (status < 0) return status;
status = batch_store(b, 20, 40, 8, 80, 2);
if (status < 0) return status;
status = batch_store(b, 20, 48, 10, 96, 2);
if (status < 0) return status;
status = batch_store(b, 20, 56, 12, 112, 2);
if (status < 0) return status;
status = batch_store(b, 20, 64, 14, 128, 2);
if (status < 0) return status;
status = batch_store(b, 20, 72, 16, 144, 2);
if (status < 0) return status;
return 1; }
static int batch_special_step(Batch *b, int c) { switch (c) {
case 0: return batch_step_0(b);
case 1: return batch_step_1(b);
case 2: return batch_step_2(b);
case 3: return batch_step_3(b);
case 4: return batch_step_4(b);
case 5: return batch_step_5(b);
case 6: return batch_step_6(b);
case 7: return batch_step_7(b);
case 8: return batch_step_8(b);
case 9: return batch_step_9(b);
case 10: return batch_step_10(b);
case 11: return batch_step_11(b);
case 12: return batch_step_12(b);
case 13: return batch_step_13(b);
case 14: return batch_step_14(b);
case 15: return batch_step_15(b);
case 16: return batch_step_16(b);
case 17: return batch_step_17(b);
case 18: return batch_step_18(b);
case 19: return batch_step_19(b);
case 20: return batch_step_20(b);
default: return -1; } }