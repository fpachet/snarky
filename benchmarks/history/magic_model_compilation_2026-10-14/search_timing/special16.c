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

const char *batch_model_key(void) { return "9dbff3c1aa8cce56a3675291a85e139f2d215d394ebf98353b549aef28536437"; }

static const int sum_shape_0_starts[] = {0,256,512,768,1024,1280,1536,1792,2048,2304,2560,2816,3072,3328,3584,3840,4096};
static const int sum_shape_0_masks[] = {0,4,8,12,16,20,24,28,32,36,40,44,48,52,56,60,64};
static inline int sum_shape_0(void *pointer, const uint64_t *masks, uint64_t *output) {
const int target = 2040;

    Sum *s = pointer;
    if (!s || target < 0 || target > MAX_SPAN) return -1;
    int lo[MAX_N], hi[MAX_N], count[MAX_N], width[MAX_N], holes[MAX_N];
    int active[MAX_N], k = 0, lower = 0, span = 0, widest = 0, max_holes = 0;
    memcpy(output, masks, 64 * sizeof(uint64_t));
    for (int i = 0; i < 16; ++i) {
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
        for (int i = 0; i < 16; ++i) {
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
case 0: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 32);break;
case 1: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 21);break;
case 2: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 21);batch_enqueue(b, 33);break;
case 3: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 28);break;
case 4: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 25);break;
case 5: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 19);break;
case 6: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 30);break;
case 7: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 27);break;
case 8: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 22);break;
case 9: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 28);break;
case 10: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 19);break;
case 11: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 32);break;
case 12: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 28);batch_enqueue(b, 34);break;
case 13: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 27);break;
case 14: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 23);break;
case 15: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 32);break;
case 16: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 27);break;
case 17: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 20);break;
case 18: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 17);break;
case 19: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 23);break;
case 20: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 29);break;
case 21: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 20);break;
case 22: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 23);break;
case 23: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 26);break;
case 24: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 21);break;
case 25: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 29);break;
case 26: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 25);break;
case 27: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 18);break;
case 28: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 24);break;
case 29: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 19);break;
case 30: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 28);break;
case 31: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 32);break;
case 32: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 28);break;
case 33: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 29);break;
case 34: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 18);break;
case 35: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 17);batch_enqueue(b, 33);batch_enqueue(b, 35);batch_enqueue(b, 36);batch_enqueue(b, 37);batch_enqueue(b, 39);break;
case 36: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 27);break;
case 37: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 30);break;
case 38: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 31);break;
case 39: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 29);break;
case 40: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 27);break;
case 41: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 19);batch_enqueue(b, 33);break;
case 42: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 17);break;
case 43: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 30);batch_enqueue(b, 34);break;
case 44: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 22);break;
case 45: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 22);break;
case 46: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 32);break;
case 47: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 24);break;
case 48: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 31);break;
case 49: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 20);break;
case 50: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 17);break;
case 51: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 30);batch_enqueue(b, 33);break;
case 52: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 30);break;
case 53: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 27);break;
case 54: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 21);break;
case 55: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 23);break;
case 56: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 20);break;
case 57: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 30);break;
case 58: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 20);break;
case 59: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 29);break;
case 60: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 28);break;
case 61: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 18);break;
case 62: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 18);break;
case 63: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 29);batch_enqueue(b, 34);break;
case 64: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 17);break;
case 65: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 19);break;
case 66: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 22);break;
case 67: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 20);break;
case 68: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 24);break;
case 69: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 21);break;
case 70: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 21);break;
case 71: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 21);break;
case 72: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 20);break;
case 73: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 30);break;
case 74: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 23);batch_enqueue(b, 34);break;
case 75: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 25);break;
case 76: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 21);break;
case 77: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 26);break;
case 78: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 21);break;
case 79: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 31);batch_enqueue(b, 33);break;
case 80: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 29);break;
case 81: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 23);break;
case 82: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 29);batch_enqueue(b, 33);break;
case 83: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 25);break;
case 84: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 28);break;
case 85: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 19);break;
case 86: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 26);batch_enqueue(b, 34);break;
case 87: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 32);batch_enqueue(b, 33);batch_enqueue(b, 37);break;
case 88: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 25);break;
case 89: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 31);break;
case 90: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 27);break;
case 91: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 25);batch_enqueue(b, 33);break;
case 92: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 24);break;
case 93: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 19);break;
case 94: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 22);break;
case 95: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 22);break;
case 96: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 27);break;
case 97: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 28);break;
case 98: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 27);break;
case 99: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 17);break;
case 100: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 26);break;
case 101: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 26);break;
case 102: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 22);break;
case 103: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 25);break;
case 104: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 18);break;
case 105: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 18);break;
case 106: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 21);break;
case 107: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 20);break;
case 108: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 31);break;
case 109: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 22);batch_enqueue(b, 34);break;
case 110: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 28);break;
case 111: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 30);break;
case 112: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 24);break;
case 113: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 19);break;
case 114: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 18);break;
case 115: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 25);break;
case 116: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 30);break;
case 117: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 18);break;
case 118: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 25);break;
case 119: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 24);break;
case 120: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 32);break;
case 121: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 23);break;
case 122: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 18);break;
case 123: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 19);break;
case 124: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 21);batch_enqueue(b, 34);break;
case 125: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 26);break;
case 126: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 19);break;
case 127: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 17);break;
case 128: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 32);break;
case 129: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 17);break;
case 130: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 29);break;
case 131: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 22);batch_enqueue(b, 33);break;
case 132: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 28);break;
case 133: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 30);break;
case 134: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 22);break;
case 135: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 30);break;
case 136: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 32);break;
case 137: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 32);break;
case 138: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 24);batch_enqueue(b, 33);break;
case 139: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 26);batch_enqueue(b, 33);break;
case 140: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 27);batch_enqueue(b, 33);break;
case 141: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 17);break;
case 142: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 30);break;
case 143: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 21);break;
case 144: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 18);batch_enqueue(b, 33);break;
case 145: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 28);break;
case 146: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 27);break;
case 147: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 22);break;
case 148: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 27);break;
case 149: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 27);break;
case 150: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 29);break;
case 151: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 19);batch_enqueue(b, 34);break;
case 152: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 26);break;
case 153: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 23);break;
case 154: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 18);break;
case 155: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 19);break;
case 156: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 20);break;
case 157: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 26);break;
case 158: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 32);break;
case 159: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 22);break;
case 160: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 17);break;
case 161: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 31);break;
case 162: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 20);break;
case 163: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 22);break;
case 164: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 25);batch_enqueue(b, 34);break;
case 165: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 29);break;
case 166: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 30);break;
case 167: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 21);break;
case 168: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 28);break;
case 169: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 25);break;
case 170: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 30);break;
case 171: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 27);break;
case 172: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 23);break;
case 173: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 24);batch_enqueue(b, 34);break;
case 174: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 27);batch_enqueue(b, 34);break;
case 175: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 30);break;
case 176: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 31);break;
case 177: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 31);break;
case 178: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 31);break;
case 179: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 32);batch_enqueue(b, 34);batch_enqueue(b, 35);batch_enqueue(b, 38);break;
case 180: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 20);batch_enqueue(b, 34);break;
case 181: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 28);break;
case 182: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 24);break;
case 183: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 18);break;
case 184: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 26);break;
case 185: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 20);break;
case 186: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 20);batch_enqueue(b, 33);break;
case 187: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 23);break;
case 188: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 21);break;
case 189: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 31);break;
case 190: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 18);break;
case 191: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 23);break;
case 192: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 26);break;
case 193: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 25);break;
case 194: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 25);break;
case 195: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 26);break;
case 196: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 30);break;
case 197: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 27);break;
case 198: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 26);break;
case 199: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 31);break;
case 200: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 23);break;
case 201: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 21);break;
case 202: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 25);break;
case 203: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 28);break;
case 204: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 20);break;
case 205: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 24);break;
case 206: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 32);break;
case 207: batch_enqueue(b, 0);batch_enqueue(b, 5);batch_enqueue(b, 17);break;
case 208: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 22);break;
case 209: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 18);break;
case 210: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 32);break;
case 211: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 20);break;
case 212: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 19);break;
case 213: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 26);break;
case 214: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 17);batch_enqueue(b, 34);batch_enqueue(b, 36);batch_enqueue(b, 38);break;
case 215: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 21);break;
case 216: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 23);break;
case 217: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 31);break;
case 218: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 28);batch_enqueue(b, 33);break;
case 219: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 17);break;
case 220: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 17);break;
case 221: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 22);break;
case 222: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 29);break;
case 223: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 24);break;
case 224: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 20);break;
case 225: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 24);break;
case 226: batch_enqueue(b, 0);batch_enqueue(b, 8);batch_enqueue(b, 31);break;
case 227: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 32);break;
case 228: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 22);break;
case 229: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 29);break;
case 230: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 24);break;
case 231: batch_enqueue(b, 0);batch_enqueue(b, 1);batch_enqueue(b, 29);break;
case 232: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 18);batch_enqueue(b, 34);break;
case 233: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 28);break;
case 234: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 29);break;
case 235: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 19);break;
case 236: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 24);break;
case 237: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 23);batch_enqueue(b, 33);break;
case 238: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 23);break;
case 239: batch_enqueue(b, 0);batch_enqueue(b, 11);batch_enqueue(b, 23);break;
case 240: batch_enqueue(b, 0);batch_enqueue(b, 10);batch_enqueue(b, 17);break;
case 241: batch_enqueue(b, 0);batch_enqueue(b, 6);batch_enqueue(b, 32);break;
case 242: batch_enqueue(b, 0);batch_enqueue(b, 12);batch_enqueue(b, 25);break;
case 243: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 25);break;
case 244: batch_enqueue(b, 0);batch_enqueue(b, 3);batch_enqueue(b, 26);break;
case 245: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 26);break;
case 246: batch_enqueue(b, 0);batch_enqueue(b, 7);batch_enqueue(b, 17);break;
case 247: batch_enqueue(b, 0);batch_enqueue(b, 15);batch_enqueue(b, 24);break;
case 248: batch_enqueue(b, 0);batch_enqueue(b, 9);batch_enqueue(b, 31);break;
case 249: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 24);break;
case 250: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 18);break;
case 251: batch_enqueue(b, 0);batch_enqueue(b, 14);batch_enqueue(b, 29);break;
case 252: batch_enqueue(b, 0);batch_enqueue(b, 4);batch_enqueue(b, 19);break;
case 253: batch_enqueue(b, 0);batch_enqueue(b, 16);batch_enqueue(b, 31);break;
case 254: batch_enqueue(b, 0);batch_enqueue(b, 13);batch_enqueue(b, 19);break;
case 255: batch_enqueue(b, 0);batch_enqueue(b, 2);batch_enqueue(b, 31);batch_enqueue(b, 34);break;
default: break; } }
static int batch_step_0(Batch *b) {
int status;
memcpy(b->input+0, b->domains+140, 32);
memcpy(b->input+4, b->domains+760, 32);
memcpy(b->input+8, b->domains+116, 32);
memcpy(b->input+12, b->domains+268, 32);
memcpy(b->input+16, b->domains+860, 32);
memcpy(b->input+20, b->domains+652, 32);
memcpy(b->input+24, b->domains+220, 32);
memcpy(b->input+28, b->domains+920, 32);
memcpy(b->input+32, b->domains+460, 32);
memcpy(b->input+36, b->domains+780, 32);
memcpy(b->input+40, b->domains+684, 32);
memcpy(b->input+44, b->domains+120, 32);
memcpy(b->input+48, b->domains+924, 32);
memcpy(b->input+52, b->domains+228, 32);
memcpy(b->input+56, b->domains+644, 32);
memcpy(b->input+60, b->domains+716, 32);
memcpy(b->input+64, b->domains+256, 32);
memcpy(b->input+68, b->domains+576, 32);
memcpy(b->input+72, b->domains+40, 32);
memcpy(b->input+76, b->domains+816, 32);
memcpy(b->input+80, b->domains+4, 32);
memcpy(b->input+84, b->domains+264, 32);
memcpy(b->input+88, b->domains+800, 32);
memcpy(b->input+92, b->domains+996, 32);
memcpy(b->input+96, b->domains+772, 32);
memcpy(b->input+100, b->domains+852, 32);
memcpy(b->input+104, b->domains+384, 32);
memcpy(b->input+108, b->domains+580, 32);
memcpy(b->input+112, b->domains+132, 32);
memcpy(b->input+116, b->domains+700, 32);
memcpy(b->input+120, b->domains+1020, 32);
memcpy(b->input+124, b->domains+632, 32);
memcpy(b->input+128, b->domains+640, 32);
memcpy(b->input+132, b->domains+836, 32);
memcpy(b->input+136, b->domains+164, 32);
memcpy(b->input+140, b->domains+740, 32);
memcpy(b->input+144, b->domains+280, 32);
memcpy(b->input+148, b->domains+636, 32);
memcpy(b->input+152, b->domains+864, 32);
memcpy(b->input+156, b->domains+112, 32);
memcpy(b->input+160, b->domains+104, 32);
memcpy(b->input+164, b->domains+976, 32);
memcpy(b->input+168, b->domains+788, 32);
memcpy(b->input+172, b->domains+12, 32);
memcpy(b->input+176, b->domains+236, 32);
memcpy(b->input+180, b->domains+172, 32);
memcpy(b->input+184, b->domains+704, 32);
memcpy(b->input+188, b->domains+184, 32);
memcpy(b->input+192, b->domains+880, 32);
memcpy(b->input+196, b->domains+108, 32);
memcpy(b->input+200, b->domains+1008, 32);
memcpy(b->input+204, b->domains+744, 32);
memcpy(b->input+208, b->domains+276, 32);
memcpy(b->input+212, b->domains+176, 32);
memcpy(b->input+216, b->domains+764, 32);
memcpy(b->input+220, b->domains+728, 32);
memcpy(b->input+224, b->domains+332, 32);
memcpy(b->input+228, b->domains+608, 32);
memcpy(b->input+232, b->domains+392, 32);
memcpy(b->input+236, b->domains+672, 32);
memcpy(b->input+240, b->domains+252, 32);
memcpy(b->input+244, b->domains+292, 32);
memcpy(b->input+248, b->domains+192, 32);
memcpy(b->input+252, b->domains+44, 32);
memcpy(b->input+256, b->domains+828, 32);
memcpy(b->input+260, b->domains+416, 32);
memcpy(b->input+264, b->domains+620, 32);
memcpy(b->input+268, b->domains+624, 32);
memcpy(b->input+272, b->domains+8, 32);
memcpy(b->input+276, b->domains+32, 32);
memcpy(b->input+280, b->domains+56, 32);
memcpy(b->input+284, b->domains+476, 32);
memcpy(b->input+288, b->domains+16, 32);
memcpy(b->input+292, b->domains+400, 32);
memcpy(b->input+296, b->domains+160, 32);
memcpy(b->input+300, b->domains+48, 32);
memcpy(b->input+304, b->domains+320, 32);
memcpy(b->input+308, b->domains+532, 32);
memcpy(b->input+312, b->domains+796, 32);
memcpy(b->input+316, b->domains+512, 32);
memcpy(b->input+320, b->domains+564, 32);
memcpy(b->input+324, b->domains+244, 32);
memcpy(b->input+328, b->domains+340, 32);
memcpy(b->input+332, b->domains+224, 32);
memcpy(b->input+336, b->domains+572, 32);
memcpy(b->input+340, b->domains+524, 32);
memcpy(b->input+344, b->domains+748, 32);
memcpy(b->input+348, b->domains+188, 32);
memcpy(b->input+352, b->domains+300, 32);
memcpy(b->input+356, b->domains+792, 32);
memcpy(b->input+360, b->domains+696, 32);
memcpy(b->input+364, b->domains+336, 32);
memcpy(b->input+368, b->domains+660, 32);
memcpy(b->input+372, b->domains+148, 32);
memcpy(b->input+376, b->domains+712, 32);
memcpy(b->input+380, b->domains+964, 32);
memcpy(b->input+384, b->domains+984, 32);
memcpy(b->input+388, b->domains+136, 32);
memcpy(b->input+392, b->domains+492, 32);
memcpy(b->input+396, b->domains+288, 32);
memcpy(b->input+400, b->domains+804, 32);
memcpy(b->input+404, b->domains+376, 32);
memcpy(b->input+408, b->domains+948, 32);
memcpy(b->input+412, b->domains+272, 32);
memcpy(b->input+416, b->domains+972, 32);
memcpy(b->input+420, b->domains+344, 32);
memcpy(b->input+424, b->domains+360, 32);
memcpy(b->input+428, b->domains+128, 32);
memcpy(b->input+432, b->domains+100, 32);
memcpy(b->input+436, b->domains+24, 32);
memcpy(b->input+440, b->domains+756, 32);
memcpy(b->input+444, b->domains+824, 32);
memcpy(b->input+448, b->domains+168, 32);
memcpy(b->input+452, b->domains+732, 32);
memcpy(b->input+456, b->domains+452, 32);
memcpy(b->input+460, b->domains+648, 32);
memcpy(b->input+464, b->domains+304, 32);
memcpy(b->input+468, b->domains+180, 32);
memcpy(b->input+472, b->domains+88, 32);
memcpy(b->input+476, b->domains+552, 32);
memcpy(b->input+480, b->domains+656, 32);
memcpy(b->input+484, b->domains+628, 32);
memcpy(b->input+488, b->domains+64, 32);
memcpy(b->input+492, b->domains+240, 32);
memcpy(b->input+496, b->domains+600, 32);
memcpy(b->input+500, b->domains+540, 32);
memcpy(b->input+504, b->domains+904, 32);
memcpy(b->input+508, b->domains+480, 32);
memcpy(b->input+512, b->domains+876, 32);
memcpy(b->input+516, b->domains+420, 32);
memcpy(b->input+520, b->domains+260, 32);
memcpy(b->input+524, b->domains+428, 32);
memcpy(b->input+528, b->domains+668, 32);
memcpy(b->input+532, b->domains+588, 32);
memcpy(b->input+536, b->domains+484, 32);
memcpy(b->input+540, b->domains+692, 32);
memcpy(b->input+544, b->domains+364, 32);
memcpy(b->input+548, b->domains+736, 32);
memcpy(b->input+552, b->domains+212, 32);
memcpy(b->input+556, b->domains+812, 32);
memcpy(b->input+560, b->domains+156, 32);
memcpy(b->input+564, b->domains+208, 32);
memcpy(b->input+568, b->domains+992, 32);
memcpy(b->input+572, b->domains+544, 32);
memcpy(b->input+576, b->domains+960, 32);
memcpy(b->input+580, b->domains+488, 32);
memcpy(b->input+584, b->domains+940, 32);
memcpy(b->input+588, b->domains+196, 32);
memcpy(b->input+592, b->domains+752, 32);
memcpy(b->input+596, b->domains+408, 32);
memcpy(b->input+600, b->domains+296, 32);
memcpy(b->input+604, b->domains+820, 32);
memcpy(b->input+608, b->domains+352, 32);
memcpy(b->input+612, b->domains+556, 32);
memcpy(b->input+616, b->domains+144, 32);
memcpy(b->input+620, b->domains+932, 32);
memcpy(b->input+624, b->domains+888, 32);
memcpy(b->input+628, b->domains+680, 32);
memcpy(b->input+632, b->domains+432, 32);
memcpy(b->input+636, b->domains+124, 32);
memcpy(b->input+640, b->domains+508, 32);
memcpy(b->input+644, b->domains+456, 32);
memcpy(b->input+648, b->domains+848, 32);
memcpy(b->input+652, b->domains+84, 32);
memcpy(b->input+656, b->domains+284, 32);
memcpy(b->input+660, b->domains+436, 32);
memcpy(b->input+664, b->domains+956, 32);
memcpy(b->input+668, b->domains+892, 32);
memcpy(b->input+672, b->domains+412, 32);
memcpy(b->input+676, b->domains+92, 32);
memcpy(b->input+680, b->domains+560, 32);
memcpy(b->input+684, b->domains+440, 32);
memcpy(b->input+688, b->domains+520, 32);
memcpy(b->input+692, b->domains+568, 32);
memcpy(b->input+696, b->domains+356, 32);
memcpy(b->input+700, b->domains+840, 32);
memcpy(b->input+704, b->domains+200, 32);
memcpy(b->input+708, b->domains+468, 32);
memcpy(b->input+712, b->domains+20, 32);
memcpy(b->input+716, b->domains+896, 32);
memcpy(b->input+720, b->domains+496, 32);
memcpy(b->input+724, b->domains+912, 32);
memcpy(b->input+728, b->domains+688, 32);
memcpy(b->input+732, b->domains+900, 32);
memcpy(b->input+736, b->domains+968, 32);
memcpy(b->input+740, b->domains+308, 32);
memcpy(b->input+744, b->domains+596, 32);
memcpy(b->input+748, b->domains+872, 32);
memcpy(b->input+752, b->domains+916, 32);
memcpy(b->input+756, b->domains+444, 32);
memcpy(b->input+760, b->domains+152, 32);
memcpy(b->input+764, b->domains+908, 32);
memcpy(b->input+768, b->domains+72, 32);
memcpy(b->input+772, b->domains+616, 32);
memcpy(b->input+776, b->domains+1016, 32);
memcpy(b->input+780, b->domains+720, 32);
memcpy(b->input+784, b->domains+96, 32);
memcpy(b->input+788, b->domains+380, 32);
memcpy(b->input+792, b->domains+952, 32);
memcpy(b->input+796, b->domains+944, 32);
memcpy(b->input+800, b->domains+676, 32);
memcpy(b->input+804, b->domains+980, 32);
memcpy(b->input+808, b->domains+592, 32);
memcpy(b->input+812, b->domains+388, 32);
memcpy(b->input+816, b->domains+328, 32);
memcpy(b->input+820, b->domains+664, 32);
memcpy(b->input+824, b->domains+708, 32);
memcpy(b->input+828, b->domains+548, 32);
memcpy(b->input+832, b->domains+516, 32);
memcpy(b->input+836, b->domains+248, 32);
memcpy(b->input+840, b->domains+604, 32);
memcpy(b->input+844, b->domains+232, 32);
memcpy(b->input+848, b->domains+424, 32);
memcpy(b->input+852, b->domains+832, 32);
memcpy(b->input+856, b->domains+324, 32);
memcpy(b->input+860, b->domains+368, 32);
memcpy(b->input+864, b->domains+776, 32);
memcpy(b->input+868, b->domains+404, 32);
memcpy(b->input+872, b->domains+28, 32);
memcpy(b->input+876, b->domains+528, 32);
memcpy(b->input+880, b->domains+1004, 32);
memcpy(b->input+884, b->domains+204, 32);
memcpy(b->input+888, b->domains+868, 32);
memcpy(b->input+892, b->domains+60, 32);
memcpy(b->input+896, b->domains+396, 32);
memcpy(b->input+900, b->domains+928, 32);
memcpy(b->input+904, b->domains+372, 32);
memcpy(b->input+908, b->domains+68, 32);
memcpy(b->input+912, b->domains+312, 32);
memcpy(b->input+916, b->domains+884, 32);
memcpy(b->input+920, b->domains+612, 32);
memcpy(b->input+924, b->domains+988, 32);
memcpy(b->input+928, b->domains+472, 32);
memcpy(b->input+932, b->domains+768, 32);
memcpy(b->input+936, b->domains+52, 32);
memcpy(b->input+940, b->domains+724, 32);
memcpy(b->input+944, b->domains+80, 32);
memcpy(b->input+948, b->domains+784, 32);
memcpy(b->input+952, b->domains+316, 32);
memcpy(b->input+956, b->domains+0, 32);
memcpy(b->input+960, b->domains+856, 32);
memcpy(b->input+964, b->domains+1000, 32);
memcpy(b->input+968, b->domains+504, 32);
memcpy(b->input+972, b->domains+844, 32);
memcpy(b->input+976, b->domains+216, 32);
memcpy(b->input+980, b->domains+536, 32);
memcpy(b->input+984, b->domains+76, 32);
memcpy(b->input+988, b->domains+448, 32);
memcpy(b->input+992, b->domains+808, 32);
memcpy(b->input+996, b->domains+500, 32);
memcpy(b->input+1000, b->domains+584, 32);
memcpy(b->input+1004, b->domains+36, 32);
memcpy(b->input+1008, b->domains+936, 32);
memcpy(b->input+1012, b->domains+464, 32);
memcpy(b->input+1016, b->domains+1012, 32);
memcpy(b->input+1020, b->domains+348, 32);
if (batch_cached(b, 0, 1024)) return 1;
++b->counts[1];
status = alldiff_supports(b->plans[0], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+0, b->output, 8192); b->cached[0] = 1;
status = batch_store(b, 0, 35, 0, 140, 4);
if (status < 0) return status;
status = batch_store(b, 0, 190, 4, 760, 4);
if (status < 0) return status;
status = batch_store(b, 0, 29, 8, 116, 4);
if (status < 0) return status;
status = batch_store(b, 0, 67, 12, 268, 4);
if (status < 0) return status;
status = batch_store(b, 0, 215, 16, 860, 4);
if (status < 0) return status;
status = batch_store(b, 0, 163, 20, 652, 4);
if (status < 0) return status;
status = batch_store(b, 0, 55, 24, 220, 4);
if (status < 0) return status;
status = batch_store(b, 0, 230, 28, 920, 4);
if (status < 0) return status;
status = batch_store(b, 0, 115, 32, 460, 4);
if (status < 0) return status;
status = batch_store(b, 0, 195, 36, 780, 4);
if (status < 0) return status;
status = batch_store(b, 0, 171, 40, 684, 4);
if (status < 0) return status;
status = batch_store(b, 0, 30, 44, 120, 4);
if (status < 0) return status;
status = batch_store(b, 0, 231, 48, 924, 4);
if (status < 0) return status;
status = batch_store(b, 0, 57, 52, 228, 4);
if (status < 0) return status;
status = batch_store(b, 0, 161, 56, 644, 4);
if (status < 0) return status;
status = batch_store(b, 0, 179, 60, 716, 4);
if (status < 0) return status;
status = batch_store(b, 0, 64, 64, 256, 4);
if (status < 0) return status;
status = batch_store(b, 0, 144, 68, 576, 4);
if (status < 0) return status;
status = batch_store(b, 0, 10, 72, 40, 4);
if (status < 0) return status;
status = batch_store(b, 0, 204, 76, 816, 4);
if (status < 0) return status;
status = batch_store(b, 0, 1, 80, 4, 4);
if (status < 0) return status;
status = batch_store(b, 0, 66, 84, 264, 4);
if (status < 0) return status;
status = batch_store(b, 0, 200, 88, 800, 4);
if (status < 0) return status;
status = batch_store(b, 0, 249, 92, 996, 4);
if (status < 0) return status;
status = batch_store(b, 0, 193, 96, 772, 4);
if (status < 0) return status;
status = batch_store(b, 0, 213, 100, 852, 4);
if (status < 0) return status;
status = batch_store(b, 0, 96, 104, 384, 4);
if (status < 0) return status;
status = batch_store(b, 0, 145, 108, 580, 4);
if (status < 0) return status;
status = batch_store(b, 0, 33, 112, 132, 4);
if (status < 0) return status;
status = batch_store(b, 0, 175, 116, 700, 4);
if (status < 0) return status;
status = batch_store(b, 0, 255, 120, 1020, 4);
if (status < 0) return status;
status = batch_store(b, 0, 158, 124, 632, 4);
if (status < 0) return status;
status = batch_store(b, 0, 160, 128, 640, 4);
if (status < 0) return status;
status = batch_store(b, 0, 209, 132, 836, 4);
if (status < 0) return status;
status = batch_store(b, 0, 41, 136, 164, 4);
if (status < 0) return status;
status = batch_store(b, 0, 185, 140, 740, 4);
if (status < 0) return status;
status = batch_store(b, 0, 70, 144, 280, 4);
if (status < 0) return status;
status = batch_store(b, 0, 159, 148, 636, 4);
if (status < 0) return status;
status = batch_store(b, 0, 216, 152, 864, 4);
if (status < 0) return status;
status = batch_store(b, 0, 28, 156, 112, 4);
if (status < 0) return status;
status = batch_store(b, 0, 26, 160, 104, 4);
if (status < 0) return status;
status = batch_store(b, 0, 244, 164, 976, 4);
if (status < 0) return status;
status = batch_store(b, 0, 197, 168, 788, 4);
if (status < 0) return status;
status = batch_store(b, 0, 3, 172, 12, 4);
if (status < 0) return status;
status = batch_store(b, 0, 59, 176, 236, 4);
if (status < 0) return status;
status = batch_store(b, 0, 43, 180, 172, 4);
if (status < 0) return status;
status = batch_store(b, 0, 176, 184, 704, 4);
if (status < 0) return status;
status = batch_store(b, 0, 46, 188, 184, 4);
if (status < 0) return status;
status = batch_store(b, 0, 220, 192, 880, 4);
if (status < 0) return status;
status = batch_store(b, 0, 27, 196, 108, 4);
if (status < 0) return status;
status = batch_store(b, 0, 252, 200, 1008, 4);
if (status < 0) return status;
status = batch_store(b, 0, 186, 204, 744, 4);
if (status < 0) return status;
status = batch_store(b, 0, 69, 208, 276, 4);
if (status < 0) return status;
status = batch_store(b, 0, 44, 212, 176, 4);
if (status < 0) return status;
status = batch_store(b, 0, 191, 216, 764, 4);
if (status < 0) return status;
status = batch_store(b, 0, 182, 220, 728, 4);
if (status < 0) return status;
status = batch_store(b, 0, 83, 224, 332, 4);
if (status < 0) return status;
status = batch_store(b, 0, 152, 228, 608, 4);
if (status < 0) return status;
status = batch_store(b, 0, 98, 232, 392, 4);
if (status < 0) return status;
status = batch_store(b, 0, 168, 236, 672, 4);
if (status < 0) return status;
status = batch_store(b, 0, 63, 240, 252, 4);
if (status < 0) return status;
status = batch_store(b, 0, 73, 244, 292, 4);
if (status < 0) return status;
status = batch_store(b, 0, 48, 248, 192, 4);
if (status < 0) return status;
status = batch_store(b, 0, 11, 252, 44, 4);
if (status < 0) return status;
status = batch_store(b, 0, 207, 256, 828, 4);
if (status < 0) return status;
status = batch_store(b, 0, 104, 260, 416, 4);
if (status < 0) return status;
status = batch_store(b, 0, 155, 264, 620, 4);
if (status < 0) return status;
status = batch_store(b, 0, 156, 268, 624, 4);
if (status < 0) return status;
status = batch_store(b, 0, 2, 272, 8, 4);
if (status < 0) return status;
status = batch_store(b, 0, 8, 276, 32, 4);
if (status < 0) return status;
status = batch_store(b, 0, 14, 280, 56, 4);
if (status < 0) return status;
status = batch_store(b, 0, 119, 284, 476, 4);
if (status < 0) return status;
status = batch_store(b, 0, 4, 288, 16, 4);
if (status < 0) return status;
status = batch_store(b, 0, 100, 292, 400, 4);
if (status < 0) return status;
status = batch_store(b, 0, 40, 296, 160, 4);
if (status < 0) return status;
status = batch_store(b, 0, 12, 300, 48, 4);
if (status < 0) return status;
status = batch_store(b, 0, 80, 304, 320, 4);
if (status < 0) return status;
status = batch_store(b, 0, 133, 308, 532, 4);
if (status < 0) return status;
status = batch_store(b, 0, 199, 312, 796, 4);
if (status < 0) return status;
status = batch_store(b, 0, 128, 316, 512, 4);
if (status < 0) return status;
status = batch_store(b, 0, 141, 320, 564, 4);
if (status < 0) return status;
status = batch_store(b, 0, 61, 324, 244, 4);
if (status < 0) return status;
status = batch_store(b, 0, 85, 328, 340, 4);
if (status < 0) return status;
status = batch_store(b, 0, 56, 332, 224, 4);
if (status < 0) return status;
status = batch_store(b, 0, 143, 336, 572, 4);
if (status < 0) return status;
status = batch_store(b, 0, 131, 340, 524, 4);
if (status < 0) return status;
status = batch_store(b, 0, 187, 344, 748, 4);
if (status < 0) return status;
status = batch_store(b, 0, 47, 348, 188, 4);
if (status < 0) return status;
status = batch_store(b, 0, 75, 352, 300, 4);
if (status < 0) return status;
status = batch_store(b, 0, 198, 356, 792, 4);
if (status < 0) return status;
status = batch_store(b, 0, 174, 360, 696, 4);
if (status < 0) return status;
status = batch_store(b, 0, 84, 364, 336, 4);
if (status < 0) return status;
status = batch_store(b, 0, 165, 368, 660, 4);
if (status < 0) return status;
status = batch_store(b, 0, 37, 372, 148, 4);
if (status < 0) return status;
status = batch_store(b, 0, 178, 376, 712, 4);
if (status < 0) return status;
status = batch_store(b, 0, 241, 380, 964, 4);
if (status < 0) return status;
status = batch_store(b, 0, 246, 384, 984, 4);
if (status < 0) return status;
status = batch_store(b, 0, 34, 388, 136, 4);
if (status < 0) return status;
status = batch_store(b, 0, 123, 392, 492, 4);
if (status < 0) return status;
status = batch_store(b, 0, 72, 396, 288, 4);
if (status < 0) return status;
status = batch_store(b, 0, 201, 400, 804, 4);
if (status < 0) return status;
status = batch_store(b, 0, 94, 404, 376, 4);
if (status < 0) return status;
status = batch_store(b, 0, 237, 408, 948, 4);
if (status < 0) return status;
status = batch_store(b, 0, 68, 412, 272, 4);
if (status < 0) return status;
status = batch_store(b, 0, 243, 416, 972, 4);
if (status < 0) return status;
status = batch_store(b, 0, 86, 420, 344, 4);
if (status < 0) return status;
status = batch_store(b, 0, 90, 424, 360, 4);
if (status < 0) return status;
status = batch_store(b, 0, 32, 428, 128, 4);
if (status < 0) return status;
status = batch_store(b, 0, 25, 432, 100, 4);
if (status < 0) return status;
status = batch_store(b, 0, 6, 436, 24, 4);
if (status < 0) return status;
status = batch_store(b, 0, 189, 440, 756, 4);
if (status < 0) return status;
status = batch_store(b, 0, 206, 444, 824, 4);
if (status < 0) return status;
status = batch_store(b, 0, 42, 448, 168, 4);
if (status < 0) return status;
status = batch_store(b, 0, 183, 452, 732, 4);
if (status < 0) return status;
status = batch_store(b, 0, 113, 456, 452, 4);
if (status < 0) return status;
status = batch_store(b, 0, 162, 460, 648, 4);
if (status < 0) return status;
status = batch_store(b, 0, 76, 464, 304, 4);
if (status < 0) return status;
status = batch_store(b, 0, 45, 468, 180, 4);
if (status < 0) return status;
status = batch_store(b, 0, 22, 472, 88, 4);
if (status < 0) return status;
status = batch_store(b, 0, 138, 476, 552, 4);
if (status < 0) return status;
status = batch_store(b, 0, 164, 480, 656, 4);
if (status < 0) return status;
status = batch_store(b, 0, 157, 484, 628, 4);
if (status < 0) return status;
status = batch_store(b, 0, 16, 488, 64, 4);
if (status < 0) return status;
status = batch_store(b, 0, 60, 492, 240, 4);
if (status < 0) return status;
status = batch_store(b, 0, 150, 496, 600, 4);
if (status < 0) return status;
status = batch_store(b, 0, 135, 500, 540, 4);
if (status < 0) return status;
status = batch_store(b, 0, 226, 504, 904, 4);
if (status < 0) return status;
status = batch_store(b, 0, 120, 508, 480, 4);
if (status < 0) return status;
status = batch_store(b, 0, 219, 512, 876, 4);
if (status < 0) return status;
status = batch_store(b, 0, 105, 516, 420, 4);
if (status < 0) return status;
status = batch_store(b, 0, 65, 520, 260, 4);
if (status < 0) return status;
status = batch_store(b, 0, 107, 524, 428, 4);
if (status < 0) return status;
status = batch_store(b, 0, 167, 528, 668, 4);
if (status < 0) return status;
status = batch_store(b, 0, 147, 532, 588, 4);
if (status < 0) return status;
status = batch_store(b, 0, 121, 536, 484, 4);
if (status < 0) return status;
status = batch_store(b, 0, 173, 540, 692, 4);
if (status < 0) return status;
status = batch_store(b, 0, 91, 544, 364, 4);
if (status < 0) return status;
status = batch_store(b, 0, 184, 548, 736, 4);
if (status < 0) return status;
status = batch_store(b, 0, 53, 552, 212, 4);
if (status < 0) return status;
status = batch_store(b, 0, 203, 556, 812, 4);
if (status < 0) return status;
status = batch_store(b, 0, 39, 560, 156, 4);
if (status < 0) return status;
status = batch_store(b, 0, 52, 564, 208, 4);
if (status < 0) return status;
status = batch_store(b, 0, 248, 568, 992, 4);
if (status < 0) return status;
status = batch_store(b, 0, 136, 572, 544, 4);
if (status < 0) return status;
status = batch_store(b, 0, 240, 576, 960, 4);
if (status < 0) return status;
status = batch_store(b, 0, 122, 580, 488, 4);
if (status < 0) return status;
status = batch_store(b, 0, 235, 584, 940, 4);
if (status < 0) return status;
status = batch_store(b, 0, 49, 588, 196, 4);
if (status < 0) return status;
status = batch_store(b, 0, 188, 592, 752, 4);
if (status < 0) return status;
status = batch_store(b, 0, 102, 596, 408, 4);
if (status < 0) return status;
status = batch_store(b, 0, 74, 600, 296, 4);
if (status < 0) return status;
status = batch_store(b, 0, 205, 604, 820, 4);
if (status < 0) return status;
status = batch_store(b, 0, 88, 608, 352, 4);
if (status < 0) return status;
status = batch_store(b, 0, 139, 612, 556, 4);
if (status < 0) return status;
status = batch_store(b, 0, 36, 616, 144, 4);
if (status < 0) return status;
status = batch_store(b, 0, 233, 620, 932, 4);
if (status < 0) return status;
status = batch_store(b, 0, 222, 624, 888, 4);
if (status < 0) return status;
status = batch_store(b, 0, 170, 628, 680, 4);
if (status < 0) return status;
status = batch_store(b, 0, 108, 632, 432, 4);
if (status < 0) return status;
status = batch_store(b, 0, 31, 636, 124, 4);
if (status < 0) return status;
status = batch_store(b, 0, 127, 640, 508, 4);
if (status < 0) return status;
status = batch_store(b, 0, 114, 644, 456, 4);
if (status < 0) return status;
status = batch_store(b, 0, 212, 648, 848, 4);
if (status < 0) return status;
status = batch_store(b, 0, 21, 652, 84, 4);
if (status < 0) return status;
status = batch_store(b, 0, 71, 656, 284, 4);
if (status < 0) return status;
status = batch_store(b, 0, 109, 660, 436, 4);
if (status < 0) return status;
status = batch_store(b, 0, 239, 664, 956, 4);
if (status < 0) return status;
status = batch_store(b, 0, 223, 668, 892, 4);
if (status < 0) return status;
status = batch_store(b, 0, 103, 672, 412, 4);
if (status < 0) return status;
status = batch_store(b, 0, 23, 676, 92, 4);
if (status < 0) return status;
status = batch_store(b, 0, 140, 680, 560, 4);
if (status < 0) return status;
status = batch_store(b, 0, 110, 684, 440, 4);
if (status < 0) return status;
status = batch_store(b, 0, 130, 688, 520, 4);
if (status < 0) return status;
status = batch_store(b, 0, 142, 692, 568, 4);
if (status < 0) return status;
status = batch_store(b, 0, 89, 696, 356, 4);
if (status < 0) return status;
status = batch_store(b, 0, 210, 700, 840, 4);
if (status < 0) return status;
status = batch_store(b, 0, 50, 704, 200, 4);
if (status < 0) return status;
status = batch_store(b, 0, 117, 708, 468, 4);
if (status < 0) return status;
status = batch_store(b, 0, 5, 712, 20, 4);
if (status < 0) return status;
status = batch_store(b, 0, 224, 716, 896, 4);
if (status < 0) return status;
status = batch_store(b, 0, 124, 720, 496, 4);
if (status < 0) return status;
status = batch_store(b, 0, 228, 724, 912, 4);
if (status < 0) return status;
status = batch_store(b, 0, 172, 728, 688, 4);
if (status < 0) return status;
status = batch_store(b, 0, 225, 732, 900, 4);
if (status < 0) return status;
status = batch_store(b, 0, 242, 736, 968, 4);
if (status < 0) return status;
status = batch_store(b, 0, 77, 740, 308, 4);
if (status < 0) return status;
status = batch_store(b, 0, 149, 744, 596, 4);
if (status < 0) return status;
status = batch_store(b, 0, 218, 748, 872, 4);
if (status < 0) return status;
status = batch_store(b, 0, 229, 752, 916, 4);
if (status < 0) return status;
status = batch_store(b, 0, 111, 756, 444, 4);
if (status < 0) return status;
status = batch_store(b, 0, 38, 760, 152, 4);
if (status < 0) return status;
status = batch_store(b, 0, 227, 764, 908, 4);
if (status < 0) return status;
status = batch_store(b, 0, 18, 768, 72, 4);
if (status < 0) return status;
status = batch_store(b, 0, 154, 772, 616, 4);
if (status < 0) return status;
status = batch_store(b, 0, 254, 776, 1016, 4);
if (status < 0) return status;
status = batch_store(b, 0, 180, 780, 720, 4);
if (status < 0) return status;
status = batch_store(b, 0, 24, 784, 96, 4);
if (status < 0) return status;
status = batch_store(b, 0, 95, 788, 380, 4);
if (status < 0) return status;
status = batch_store(b, 0, 238, 792, 952, 4);
if (status < 0) return status;
status = batch_store(b, 0, 236, 796, 944, 4);
if (status < 0) return status;
status = batch_store(b, 0, 169, 800, 676, 4);
if (status < 0) return status;
status = batch_store(b, 0, 245, 804, 980, 4);
if (status < 0) return status;
status = batch_store(b, 0, 148, 808, 592, 4);
if (status < 0) return status;
status = batch_store(b, 0, 97, 812, 388, 4);
if (status < 0) return status;
status = batch_store(b, 0, 82, 816, 328, 4);
if (status < 0) return status;
status = batch_store(b, 0, 166, 820, 664, 4);
if (status < 0) return status;
status = batch_store(b, 0, 177, 824, 708, 4);
if (status < 0) return status;
status = batch_store(b, 0, 137, 828, 548, 4);
if (status < 0) return status;
status = batch_store(b, 0, 129, 832, 516, 4);
if (status < 0) return status;
status = batch_store(b, 0, 62, 836, 248, 4);
if (status < 0) return status;
status = batch_store(b, 0, 151, 840, 604, 4);
if (status < 0) return status;
status = batch_store(b, 0, 58, 844, 232, 4);
if (status < 0) return status;
status = batch_store(b, 0, 106, 848, 424, 4);
if (status < 0) return status;
status = batch_store(b, 0, 208, 852, 832, 4);
if (status < 0) return status;
status = batch_store(b, 0, 81, 856, 324, 4);
if (status < 0) return status;
status = batch_store(b, 0, 92, 860, 368, 4);
if (status < 0) return status;
status = batch_store(b, 0, 194, 864, 776, 4);
if (status < 0) return status;
status = batch_store(b, 0, 101, 868, 404, 4);
if (status < 0) return status;
status = batch_store(b, 0, 7, 872, 28, 4);
if (status < 0) return status;
status = batch_store(b, 0, 132, 876, 528, 4);
if (status < 0) return status;
status = batch_store(b, 0, 251, 880, 1004, 4);
if (status < 0) return status;
status = batch_store(b, 0, 51, 884, 204, 4);
if (status < 0) return status;
status = batch_store(b, 0, 217, 888, 868, 4);
if (status < 0) return status;
status = batch_store(b, 0, 15, 892, 60, 4);
if (status < 0) return status;
status = batch_store(b, 0, 99, 896, 396, 4);
if (status < 0) return status;
status = batch_store(b, 0, 232, 900, 928, 4);
if (status < 0) return status;
status = batch_store(b, 0, 93, 904, 372, 4);
if (status < 0) return status;
status = batch_store(b, 0, 17, 908, 68, 4);
if (status < 0) return status;
status = batch_store(b, 0, 78, 912, 312, 4);
if (status < 0) return status;
status = batch_store(b, 0, 221, 916, 884, 4);
if (status < 0) return status;
status = batch_store(b, 0, 153, 920, 612, 4);
if (status < 0) return status;
status = batch_store(b, 0, 247, 924, 988, 4);
if (status < 0) return status;
status = batch_store(b, 0, 118, 928, 472, 4);
if (status < 0) return status;
status = batch_store(b, 0, 192, 932, 768, 4);
if (status < 0) return status;
status = batch_store(b, 0, 13, 936, 52, 4);
if (status < 0) return status;
status = batch_store(b, 0, 181, 940, 724, 4);
if (status < 0) return status;
status = batch_store(b, 0, 20, 944, 80, 4);
if (status < 0) return status;
status = batch_store(b, 0, 196, 948, 784, 4);
if (status < 0) return status;
status = batch_store(b, 0, 79, 952, 316, 4);
if (status < 0) return status;
status = batch_store(b, 0, 0, 956, 0, 4);
if (status < 0) return status;
status = batch_store(b, 0, 214, 960, 856, 4);
if (status < 0) return status;
status = batch_store(b, 0, 250, 964, 1000, 4);
if (status < 0) return status;
status = batch_store(b, 0, 126, 968, 504, 4);
if (status < 0) return status;
status = batch_store(b, 0, 211, 972, 844, 4);
if (status < 0) return status;
status = batch_store(b, 0, 54, 976, 216, 4);
if (status < 0) return status;
status = batch_store(b, 0, 134, 980, 536, 4);
if (status < 0) return status;
status = batch_store(b, 0, 19, 984, 76, 4);
if (status < 0) return status;
status = batch_store(b, 0, 112, 988, 448, 4);
if (status < 0) return status;
status = batch_store(b, 0, 202, 992, 808, 4);
if (status < 0) return status;
status = batch_store(b, 0, 125, 996, 500, 4);
if (status < 0) return status;
status = batch_store(b, 0, 146, 1000, 584, 4);
if (status < 0) return status;
status = batch_store(b, 0, 9, 1004, 36, 4);
if (status < 0) return status;
status = batch_store(b, 0, 234, 1008, 936, 4);
if (status < 0) return status;
status = batch_store(b, 0, 116, 1012, 464, 4);
if (status < 0) return status;
status = batch_store(b, 0, 253, 1016, 1012, 4);
if (status < 0) return status;
status = batch_store(b, 0, 87, 1020, 348, 4);
if (status < 0) return status;
return 1; }
static int batch_step_1(Batch *b) {
int status;
memcpy(b->input+0, b->domains+140, 32);
memcpy(b->input+4, b->domains+760, 32);
memcpy(b->input+8, b->domains+116, 32);
memcpy(b->input+12, b->domains+268, 32);
memcpy(b->input+16, b->domains+860, 32);
memcpy(b->input+20, b->domains+652, 32);
memcpy(b->input+24, b->domains+220, 32);
memcpy(b->input+28, b->domains+920, 32);
memcpy(b->input+32, b->domains+460, 32);
memcpy(b->input+36, b->domains+780, 32);
memcpy(b->input+40, b->domains+684, 32);
memcpy(b->input+44, b->domains+120, 32);
memcpy(b->input+48, b->domains+924, 32);
memcpy(b->input+52, b->domains+228, 32);
memcpy(b->input+56, b->domains+644, 32);
memcpy(b->input+60, b->domains+716, 32);
if (batch_cached(b, 1, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[1], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1024, b->output, 512); b->cached[1] = 1;
status = batch_store(b, 1, 35, 0, 140, 4);
if (status < 0) return status;
status = batch_store(b, 1, 190, 4, 760, 4);
if (status < 0) return status;
status = batch_store(b, 1, 29, 8, 116, 4);
if (status < 0) return status;
status = batch_store(b, 1, 67, 12, 268, 4);
if (status < 0) return status;
status = batch_store(b, 1, 215, 16, 860, 4);
if (status < 0) return status;
status = batch_store(b, 1, 163, 20, 652, 4);
if (status < 0) return status;
status = batch_store(b, 1, 55, 24, 220, 4);
if (status < 0) return status;
status = batch_store(b, 1, 230, 28, 920, 4);
if (status < 0) return status;
status = batch_store(b, 1, 115, 32, 460, 4);
if (status < 0) return status;
status = batch_store(b, 1, 195, 36, 780, 4);
if (status < 0) return status;
status = batch_store(b, 1, 171, 40, 684, 4);
if (status < 0) return status;
status = batch_store(b, 1, 30, 44, 120, 4);
if (status < 0) return status;
status = batch_store(b, 1, 231, 48, 924, 4);
if (status < 0) return status;
status = batch_store(b, 1, 57, 52, 228, 4);
if (status < 0) return status;
status = batch_store(b, 1, 161, 56, 644, 4);
if (status < 0) return status;
status = batch_store(b, 1, 179, 60, 716, 4);
if (status < 0) return status;
return 1; }
static int batch_step_2(Batch *b) {
int status;
memcpy(b->input+0, b->domains+256, 32);
memcpy(b->input+4, b->domains+576, 32);
memcpy(b->input+8, b->domains+40, 32);
memcpy(b->input+12, b->domains+816, 32);
memcpy(b->input+16, b->domains+4, 32);
memcpy(b->input+20, b->domains+264, 32);
memcpy(b->input+24, b->domains+800, 32);
memcpy(b->input+28, b->domains+996, 32);
memcpy(b->input+32, b->domains+772, 32);
memcpy(b->input+36, b->domains+852, 32);
memcpy(b->input+40, b->domains+384, 32);
memcpy(b->input+44, b->domains+580, 32);
memcpy(b->input+48, b->domains+132, 32);
memcpy(b->input+52, b->domains+700, 32);
memcpy(b->input+56, b->domains+1020, 32);
memcpy(b->input+60, b->domains+632, 32);
if (batch_cached(b, 2, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[2], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1088, b->output, 512); b->cached[2] = 1;
status = batch_store(b, 2, 64, 0, 256, 4);
if (status < 0) return status;
status = batch_store(b, 2, 144, 4, 576, 4);
if (status < 0) return status;
status = batch_store(b, 2, 10, 8, 40, 4);
if (status < 0) return status;
status = batch_store(b, 2, 204, 12, 816, 4);
if (status < 0) return status;
status = batch_store(b, 2, 1, 16, 4, 4);
if (status < 0) return status;
status = batch_store(b, 2, 66, 20, 264, 4);
if (status < 0) return status;
status = batch_store(b, 2, 200, 24, 800, 4);
if (status < 0) return status;
status = batch_store(b, 2, 249, 28, 996, 4);
if (status < 0) return status;
status = batch_store(b, 2, 193, 32, 772, 4);
if (status < 0) return status;
status = batch_store(b, 2, 213, 36, 852, 4);
if (status < 0) return status;
status = batch_store(b, 2, 96, 40, 384, 4);
if (status < 0) return status;
status = batch_store(b, 2, 145, 44, 580, 4);
if (status < 0) return status;
status = batch_store(b, 2, 33, 48, 132, 4);
if (status < 0) return status;
status = batch_store(b, 2, 175, 52, 700, 4);
if (status < 0) return status;
status = batch_store(b, 2, 255, 56, 1020, 4);
if (status < 0) return status;
status = batch_store(b, 2, 158, 60, 632, 4);
if (status < 0) return status;
return 1; }
static int batch_step_3(Batch *b) {
int status;
memcpy(b->input+0, b->domains+640, 32);
memcpy(b->input+4, b->domains+836, 32);
memcpy(b->input+8, b->domains+164, 32);
memcpy(b->input+12, b->domains+740, 32);
memcpy(b->input+16, b->domains+280, 32);
memcpy(b->input+20, b->domains+636, 32);
memcpy(b->input+24, b->domains+864, 32);
memcpy(b->input+28, b->domains+112, 32);
memcpy(b->input+32, b->domains+104, 32);
memcpy(b->input+36, b->domains+976, 32);
memcpy(b->input+40, b->domains+788, 32);
memcpy(b->input+44, b->domains+12, 32);
memcpy(b->input+48, b->domains+236, 32);
memcpy(b->input+52, b->domains+172, 32);
memcpy(b->input+56, b->domains+704, 32);
memcpy(b->input+60, b->domains+184, 32);
if (batch_cached(b, 3, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[3], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1152, b->output, 512); b->cached[3] = 1;
status = batch_store(b, 3, 160, 0, 640, 4);
if (status < 0) return status;
status = batch_store(b, 3, 209, 4, 836, 4);
if (status < 0) return status;
status = batch_store(b, 3, 41, 8, 164, 4);
if (status < 0) return status;
status = batch_store(b, 3, 185, 12, 740, 4);
if (status < 0) return status;
status = batch_store(b, 3, 70, 16, 280, 4);
if (status < 0) return status;
status = batch_store(b, 3, 159, 20, 636, 4);
if (status < 0) return status;
status = batch_store(b, 3, 216, 24, 864, 4);
if (status < 0) return status;
status = batch_store(b, 3, 28, 28, 112, 4);
if (status < 0) return status;
status = batch_store(b, 3, 26, 32, 104, 4);
if (status < 0) return status;
status = batch_store(b, 3, 244, 36, 976, 4);
if (status < 0) return status;
status = batch_store(b, 3, 197, 40, 788, 4);
if (status < 0) return status;
status = batch_store(b, 3, 3, 44, 12, 4);
if (status < 0) return status;
status = batch_store(b, 3, 59, 48, 236, 4);
if (status < 0) return status;
status = batch_store(b, 3, 43, 52, 172, 4);
if (status < 0) return status;
status = batch_store(b, 3, 176, 56, 704, 4);
if (status < 0) return status;
status = batch_store(b, 3, 46, 60, 184, 4);
if (status < 0) return status;
return 1; }
static int batch_step_4(Batch *b) {
int status;
memcpy(b->input+0, b->domains+880, 32);
memcpy(b->input+4, b->domains+108, 32);
memcpy(b->input+8, b->domains+1008, 32);
memcpy(b->input+12, b->domains+744, 32);
memcpy(b->input+16, b->domains+276, 32);
memcpy(b->input+20, b->domains+176, 32);
memcpy(b->input+24, b->domains+764, 32);
memcpy(b->input+28, b->domains+728, 32);
memcpy(b->input+32, b->domains+332, 32);
memcpy(b->input+36, b->domains+608, 32);
memcpy(b->input+40, b->domains+392, 32);
memcpy(b->input+44, b->domains+672, 32);
memcpy(b->input+48, b->domains+252, 32);
memcpy(b->input+52, b->domains+292, 32);
memcpy(b->input+56, b->domains+192, 32);
memcpy(b->input+60, b->domains+44, 32);
if (batch_cached(b, 4, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[4], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1216, b->output, 512); b->cached[4] = 1;
status = batch_store(b, 4, 220, 0, 880, 4);
if (status < 0) return status;
status = batch_store(b, 4, 27, 4, 108, 4);
if (status < 0) return status;
status = batch_store(b, 4, 252, 8, 1008, 4);
if (status < 0) return status;
status = batch_store(b, 4, 186, 12, 744, 4);
if (status < 0) return status;
status = batch_store(b, 4, 69, 16, 276, 4);
if (status < 0) return status;
status = batch_store(b, 4, 44, 20, 176, 4);
if (status < 0) return status;
status = batch_store(b, 4, 191, 24, 764, 4);
if (status < 0) return status;
status = batch_store(b, 4, 182, 28, 728, 4);
if (status < 0) return status;
status = batch_store(b, 4, 83, 32, 332, 4);
if (status < 0) return status;
status = batch_store(b, 4, 152, 36, 608, 4);
if (status < 0) return status;
status = batch_store(b, 4, 98, 40, 392, 4);
if (status < 0) return status;
status = batch_store(b, 4, 168, 44, 672, 4);
if (status < 0) return status;
status = batch_store(b, 4, 63, 48, 252, 4);
if (status < 0) return status;
status = batch_store(b, 4, 73, 52, 292, 4);
if (status < 0) return status;
status = batch_store(b, 4, 48, 56, 192, 4);
if (status < 0) return status;
status = batch_store(b, 4, 11, 60, 44, 4);
if (status < 0) return status;
return 1; }
static int batch_step_5(Batch *b) {
int status;
memcpy(b->input+0, b->domains+828, 32);
memcpy(b->input+4, b->domains+416, 32);
memcpy(b->input+8, b->domains+620, 32);
memcpy(b->input+12, b->domains+624, 32);
memcpy(b->input+16, b->domains+8, 32);
memcpy(b->input+20, b->domains+32, 32);
memcpy(b->input+24, b->domains+56, 32);
memcpy(b->input+28, b->domains+476, 32);
memcpy(b->input+32, b->domains+16, 32);
memcpy(b->input+36, b->domains+400, 32);
memcpy(b->input+40, b->domains+160, 32);
memcpy(b->input+44, b->domains+48, 32);
memcpy(b->input+48, b->domains+320, 32);
memcpy(b->input+52, b->domains+532, 32);
memcpy(b->input+56, b->domains+796, 32);
memcpy(b->input+60, b->domains+512, 32);
if (batch_cached(b, 5, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[5], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1280, b->output, 512); b->cached[5] = 1;
status = batch_store(b, 5, 207, 0, 828, 4);
if (status < 0) return status;
status = batch_store(b, 5, 104, 4, 416, 4);
if (status < 0) return status;
status = batch_store(b, 5, 155, 8, 620, 4);
if (status < 0) return status;
status = batch_store(b, 5, 156, 12, 624, 4);
if (status < 0) return status;
status = batch_store(b, 5, 2, 16, 8, 4);
if (status < 0) return status;
status = batch_store(b, 5, 8, 20, 32, 4);
if (status < 0) return status;
status = batch_store(b, 5, 14, 24, 56, 4);
if (status < 0) return status;
status = batch_store(b, 5, 119, 28, 476, 4);
if (status < 0) return status;
status = batch_store(b, 5, 4, 32, 16, 4);
if (status < 0) return status;
status = batch_store(b, 5, 100, 36, 400, 4);
if (status < 0) return status;
status = batch_store(b, 5, 40, 40, 160, 4);
if (status < 0) return status;
status = batch_store(b, 5, 12, 44, 48, 4);
if (status < 0) return status;
status = batch_store(b, 5, 80, 48, 320, 4);
if (status < 0) return status;
status = batch_store(b, 5, 133, 52, 532, 4);
if (status < 0) return status;
status = batch_store(b, 5, 199, 56, 796, 4);
if (status < 0) return status;
status = batch_store(b, 5, 128, 60, 512, 4);
if (status < 0) return status;
return 1; }
static int batch_step_6(Batch *b) {
int status;
memcpy(b->input+0, b->domains+564, 32);
memcpy(b->input+4, b->domains+244, 32);
memcpy(b->input+8, b->domains+340, 32);
memcpy(b->input+12, b->domains+224, 32);
memcpy(b->input+16, b->domains+572, 32);
memcpy(b->input+20, b->domains+524, 32);
memcpy(b->input+24, b->domains+748, 32);
memcpy(b->input+28, b->domains+188, 32);
memcpy(b->input+32, b->domains+300, 32);
memcpy(b->input+36, b->domains+792, 32);
memcpy(b->input+40, b->domains+696, 32);
memcpy(b->input+44, b->domains+336, 32);
memcpy(b->input+48, b->domains+660, 32);
memcpy(b->input+52, b->domains+148, 32);
memcpy(b->input+56, b->domains+712, 32);
memcpy(b->input+60, b->domains+964, 32);
if (batch_cached(b, 6, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[6], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1344, b->output, 512); b->cached[6] = 1;
status = batch_store(b, 6, 141, 0, 564, 4);
if (status < 0) return status;
status = batch_store(b, 6, 61, 4, 244, 4);
if (status < 0) return status;
status = batch_store(b, 6, 85, 8, 340, 4);
if (status < 0) return status;
status = batch_store(b, 6, 56, 12, 224, 4);
if (status < 0) return status;
status = batch_store(b, 6, 143, 16, 572, 4);
if (status < 0) return status;
status = batch_store(b, 6, 131, 20, 524, 4);
if (status < 0) return status;
status = batch_store(b, 6, 187, 24, 748, 4);
if (status < 0) return status;
status = batch_store(b, 6, 47, 28, 188, 4);
if (status < 0) return status;
status = batch_store(b, 6, 75, 32, 300, 4);
if (status < 0) return status;
status = batch_store(b, 6, 198, 36, 792, 4);
if (status < 0) return status;
status = batch_store(b, 6, 174, 40, 696, 4);
if (status < 0) return status;
status = batch_store(b, 6, 84, 44, 336, 4);
if (status < 0) return status;
status = batch_store(b, 6, 165, 48, 660, 4);
if (status < 0) return status;
status = batch_store(b, 6, 37, 52, 148, 4);
if (status < 0) return status;
status = batch_store(b, 6, 178, 56, 712, 4);
if (status < 0) return status;
status = batch_store(b, 6, 241, 60, 964, 4);
if (status < 0) return status;
return 1; }
static int batch_step_7(Batch *b) {
int status;
memcpy(b->input+0, b->domains+984, 32);
memcpy(b->input+4, b->domains+136, 32);
memcpy(b->input+8, b->domains+492, 32);
memcpy(b->input+12, b->domains+288, 32);
memcpy(b->input+16, b->domains+804, 32);
memcpy(b->input+20, b->domains+376, 32);
memcpy(b->input+24, b->domains+948, 32);
memcpy(b->input+28, b->domains+272, 32);
memcpy(b->input+32, b->domains+972, 32);
memcpy(b->input+36, b->domains+344, 32);
memcpy(b->input+40, b->domains+360, 32);
memcpy(b->input+44, b->domains+128, 32);
memcpy(b->input+48, b->domains+100, 32);
memcpy(b->input+52, b->domains+24, 32);
memcpy(b->input+56, b->domains+756, 32);
memcpy(b->input+60, b->domains+824, 32);
if (batch_cached(b, 7, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[7], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1408, b->output, 512); b->cached[7] = 1;
status = batch_store(b, 7, 246, 0, 984, 4);
if (status < 0) return status;
status = batch_store(b, 7, 34, 4, 136, 4);
if (status < 0) return status;
status = batch_store(b, 7, 123, 8, 492, 4);
if (status < 0) return status;
status = batch_store(b, 7, 72, 12, 288, 4);
if (status < 0) return status;
status = batch_store(b, 7, 201, 16, 804, 4);
if (status < 0) return status;
status = batch_store(b, 7, 94, 20, 376, 4);
if (status < 0) return status;
status = batch_store(b, 7, 237, 24, 948, 4);
if (status < 0) return status;
status = batch_store(b, 7, 68, 28, 272, 4);
if (status < 0) return status;
status = batch_store(b, 7, 243, 32, 972, 4);
if (status < 0) return status;
status = batch_store(b, 7, 86, 36, 344, 4);
if (status < 0) return status;
status = batch_store(b, 7, 90, 40, 360, 4);
if (status < 0) return status;
status = batch_store(b, 7, 32, 44, 128, 4);
if (status < 0) return status;
status = batch_store(b, 7, 25, 48, 100, 4);
if (status < 0) return status;
status = batch_store(b, 7, 6, 52, 24, 4);
if (status < 0) return status;
status = batch_store(b, 7, 189, 56, 756, 4);
if (status < 0) return status;
status = batch_store(b, 7, 206, 60, 824, 4);
if (status < 0) return status;
return 1; }
static int batch_step_8(Batch *b) {
int status;
memcpy(b->input+0, b->domains+168, 32);
memcpy(b->input+4, b->domains+732, 32);
memcpy(b->input+8, b->domains+452, 32);
memcpy(b->input+12, b->domains+648, 32);
memcpy(b->input+16, b->domains+304, 32);
memcpy(b->input+20, b->domains+180, 32);
memcpy(b->input+24, b->domains+88, 32);
memcpy(b->input+28, b->domains+552, 32);
memcpy(b->input+32, b->domains+656, 32);
memcpy(b->input+36, b->domains+628, 32);
memcpy(b->input+40, b->domains+64, 32);
memcpy(b->input+44, b->domains+240, 32);
memcpy(b->input+48, b->domains+600, 32);
memcpy(b->input+52, b->domains+540, 32);
memcpy(b->input+56, b->domains+904, 32);
memcpy(b->input+60, b->domains+480, 32);
if (batch_cached(b, 8, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[8], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1472, b->output, 512); b->cached[8] = 1;
status = batch_store(b, 8, 42, 0, 168, 4);
if (status < 0) return status;
status = batch_store(b, 8, 183, 4, 732, 4);
if (status < 0) return status;
status = batch_store(b, 8, 113, 8, 452, 4);
if (status < 0) return status;
status = batch_store(b, 8, 162, 12, 648, 4);
if (status < 0) return status;
status = batch_store(b, 8, 76, 16, 304, 4);
if (status < 0) return status;
status = batch_store(b, 8, 45, 20, 180, 4);
if (status < 0) return status;
status = batch_store(b, 8, 22, 24, 88, 4);
if (status < 0) return status;
status = batch_store(b, 8, 138, 28, 552, 4);
if (status < 0) return status;
status = batch_store(b, 8, 164, 32, 656, 4);
if (status < 0) return status;
status = batch_store(b, 8, 157, 36, 628, 4);
if (status < 0) return status;
status = batch_store(b, 8, 16, 40, 64, 4);
if (status < 0) return status;
status = batch_store(b, 8, 60, 44, 240, 4);
if (status < 0) return status;
status = batch_store(b, 8, 150, 48, 600, 4);
if (status < 0) return status;
status = batch_store(b, 8, 135, 52, 540, 4);
if (status < 0) return status;
status = batch_store(b, 8, 226, 56, 904, 4);
if (status < 0) return status;
status = batch_store(b, 8, 120, 60, 480, 4);
if (status < 0) return status;
return 1; }
static int batch_step_9(Batch *b) {
int status;
memcpy(b->input+0, b->domains+876, 32);
memcpy(b->input+4, b->domains+420, 32);
memcpy(b->input+8, b->domains+260, 32);
memcpy(b->input+12, b->domains+428, 32);
memcpy(b->input+16, b->domains+668, 32);
memcpy(b->input+20, b->domains+588, 32);
memcpy(b->input+24, b->domains+484, 32);
memcpy(b->input+28, b->domains+692, 32);
memcpy(b->input+32, b->domains+364, 32);
memcpy(b->input+36, b->domains+736, 32);
memcpy(b->input+40, b->domains+212, 32);
memcpy(b->input+44, b->domains+812, 32);
memcpy(b->input+48, b->domains+156, 32);
memcpy(b->input+52, b->domains+208, 32);
memcpy(b->input+56, b->domains+992, 32);
memcpy(b->input+60, b->domains+544, 32);
if (batch_cached(b, 9, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[9], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1536, b->output, 512); b->cached[9] = 1;
status = batch_store(b, 9, 219, 0, 876, 4);
if (status < 0) return status;
status = batch_store(b, 9, 105, 4, 420, 4);
if (status < 0) return status;
status = batch_store(b, 9, 65, 8, 260, 4);
if (status < 0) return status;
status = batch_store(b, 9, 107, 12, 428, 4);
if (status < 0) return status;
status = batch_store(b, 9, 167, 16, 668, 4);
if (status < 0) return status;
status = batch_store(b, 9, 147, 20, 588, 4);
if (status < 0) return status;
status = batch_store(b, 9, 121, 24, 484, 4);
if (status < 0) return status;
status = batch_store(b, 9, 173, 28, 692, 4);
if (status < 0) return status;
status = batch_store(b, 9, 91, 32, 364, 4);
if (status < 0) return status;
status = batch_store(b, 9, 184, 36, 736, 4);
if (status < 0) return status;
status = batch_store(b, 9, 53, 40, 212, 4);
if (status < 0) return status;
status = batch_store(b, 9, 203, 44, 812, 4);
if (status < 0) return status;
status = batch_store(b, 9, 39, 48, 156, 4);
if (status < 0) return status;
status = batch_store(b, 9, 52, 52, 208, 4);
if (status < 0) return status;
status = batch_store(b, 9, 248, 56, 992, 4);
if (status < 0) return status;
status = batch_store(b, 9, 136, 60, 544, 4);
if (status < 0) return status;
return 1; }
static int batch_step_10(Batch *b) {
int status;
memcpy(b->input+0, b->domains+960, 32);
memcpy(b->input+4, b->domains+488, 32);
memcpy(b->input+8, b->domains+940, 32);
memcpy(b->input+12, b->domains+196, 32);
memcpy(b->input+16, b->domains+752, 32);
memcpy(b->input+20, b->domains+408, 32);
memcpy(b->input+24, b->domains+296, 32);
memcpy(b->input+28, b->domains+820, 32);
memcpy(b->input+32, b->domains+352, 32);
memcpy(b->input+36, b->domains+556, 32);
memcpy(b->input+40, b->domains+144, 32);
memcpy(b->input+44, b->domains+932, 32);
memcpy(b->input+48, b->domains+888, 32);
memcpy(b->input+52, b->domains+680, 32);
memcpy(b->input+56, b->domains+432, 32);
memcpy(b->input+60, b->domains+124, 32);
if (batch_cached(b, 10, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[10], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1600, b->output, 512); b->cached[10] = 1;
status = batch_store(b, 10, 240, 0, 960, 4);
if (status < 0) return status;
status = batch_store(b, 10, 122, 4, 488, 4);
if (status < 0) return status;
status = batch_store(b, 10, 235, 8, 940, 4);
if (status < 0) return status;
status = batch_store(b, 10, 49, 12, 196, 4);
if (status < 0) return status;
status = batch_store(b, 10, 188, 16, 752, 4);
if (status < 0) return status;
status = batch_store(b, 10, 102, 20, 408, 4);
if (status < 0) return status;
status = batch_store(b, 10, 74, 24, 296, 4);
if (status < 0) return status;
status = batch_store(b, 10, 205, 28, 820, 4);
if (status < 0) return status;
status = batch_store(b, 10, 88, 32, 352, 4);
if (status < 0) return status;
status = batch_store(b, 10, 139, 36, 556, 4);
if (status < 0) return status;
status = batch_store(b, 10, 36, 40, 144, 4);
if (status < 0) return status;
status = batch_store(b, 10, 233, 44, 932, 4);
if (status < 0) return status;
status = batch_store(b, 10, 222, 48, 888, 4);
if (status < 0) return status;
status = batch_store(b, 10, 170, 52, 680, 4);
if (status < 0) return status;
status = batch_store(b, 10, 108, 56, 432, 4);
if (status < 0) return status;
status = batch_store(b, 10, 31, 60, 124, 4);
if (status < 0) return status;
return 1; }
static int batch_step_11(Batch *b) {
int status;
memcpy(b->input+0, b->domains+508, 32);
memcpy(b->input+4, b->domains+456, 32);
memcpy(b->input+8, b->domains+848, 32);
memcpy(b->input+12, b->domains+84, 32);
memcpy(b->input+16, b->domains+284, 32);
memcpy(b->input+20, b->domains+436, 32);
memcpy(b->input+24, b->domains+956, 32);
memcpy(b->input+28, b->domains+892, 32);
memcpy(b->input+32, b->domains+412, 32);
memcpy(b->input+36, b->domains+92, 32);
memcpy(b->input+40, b->domains+560, 32);
memcpy(b->input+44, b->domains+440, 32);
memcpy(b->input+48, b->domains+520, 32);
memcpy(b->input+52, b->domains+568, 32);
memcpy(b->input+56, b->domains+356, 32);
memcpy(b->input+60, b->domains+840, 32);
if (batch_cached(b, 11, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[11], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1664, b->output, 512); b->cached[11] = 1;
status = batch_store(b, 11, 127, 0, 508, 4);
if (status < 0) return status;
status = batch_store(b, 11, 114, 4, 456, 4);
if (status < 0) return status;
status = batch_store(b, 11, 212, 8, 848, 4);
if (status < 0) return status;
status = batch_store(b, 11, 21, 12, 84, 4);
if (status < 0) return status;
status = batch_store(b, 11, 71, 16, 284, 4);
if (status < 0) return status;
status = batch_store(b, 11, 109, 20, 436, 4);
if (status < 0) return status;
status = batch_store(b, 11, 239, 24, 956, 4);
if (status < 0) return status;
status = batch_store(b, 11, 223, 28, 892, 4);
if (status < 0) return status;
status = batch_store(b, 11, 103, 32, 412, 4);
if (status < 0) return status;
status = batch_store(b, 11, 23, 36, 92, 4);
if (status < 0) return status;
status = batch_store(b, 11, 140, 40, 560, 4);
if (status < 0) return status;
status = batch_store(b, 11, 110, 44, 440, 4);
if (status < 0) return status;
status = batch_store(b, 11, 130, 48, 520, 4);
if (status < 0) return status;
status = batch_store(b, 11, 142, 52, 568, 4);
if (status < 0) return status;
status = batch_store(b, 11, 89, 56, 356, 4);
if (status < 0) return status;
status = batch_store(b, 11, 210, 60, 840, 4);
if (status < 0) return status;
return 1; }
static int batch_step_12(Batch *b) {
int status;
memcpy(b->input+0, b->domains+200, 32);
memcpy(b->input+4, b->domains+468, 32);
memcpy(b->input+8, b->domains+20, 32);
memcpy(b->input+12, b->domains+896, 32);
memcpy(b->input+16, b->domains+496, 32);
memcpy(b->input+20, b->domains+912, 32);
memcpy(b->input+24, b->domains+688, 32);
memcpy(b->input+28, b->domains+900, 32);
memcpy(b->input+32, b->domains+968, 32);
memcpy(b->input+36, b->domains+308, 32);
memcpy(b->input+40, b->domains+596, 32);
memcpy(b->input+44, b->domains+872, 32);
memcpy(b->input+48, b->domains+916, 32);
memcpy(b->input+52, b->domains+444, 32);
memcpy(b->input+56, b->domains+152, 32);
memcpy(b->input+60, b->domains+908, 32);
if (batch_cached(b, 12, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[12], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1728, b->output, 512); b->cached[12] = 1;
status = batch_store(b, 12, 50, 0, 200, 4);
if (status < 0) return status;
status = batch_store(b, 12, 117, 4, 468, 4);
if (status < 0) return status;
status = batch_store(b, 12, 5, 8, 20, 4);
if (status < 0) return status;
status = batch_store(b, 12, 224, 12, 896, 4);
if (status < 0) return status;
status = batch_store(b, 12, 124, 16, 496, 4);
if (status < 0) return status;
status = batch_store(b, 12, 228, 20, 912, 4);
if (status < 0) return status;
status = batch_store(b, 12, 172, 24, 688, 4);
if (status < 0) return status;
status = batch_store(b, 12, 225, 28, 900, 4);
if (status < 0) return status;
status = batch_store(b, 12, 242, 32, 968, 4);
if (status < 0) return status;
status = batch_store(b, 12, 77, 36, 308, 4);
if (status < 0) return status;
status = batch_store(b, 12, 149, 40, 596, 4);
if (status < 0) return status;
status = batch_store(b, 12, 218, 44, 872, 4);
if (status < 0) return status;
status = batch_store(b, 12, 229, 48, 916, 4);
if (status < 0) return status;
status = batch_store(b, 12, 111, 52, 444, 4);
if (status < 0) return status;
status = batch_store(b, 12, 38, 56, 152, 4);
if (status < 0) return status;
status = batch_store(b, 12, 227, 60, 908, 4);
if (status < 0) return status;
return 1; }
static int batch_step_13(Batch *b) {
int status;
memcpy(b->input+0, b->domains+72, 32);
memcpy(b->input+4, b->domains+616, 32);
memcpy(b->input+8, b->domains+1016, 32);
memcpy(b->input+12, b->domains+720, 32);
memcpy(b->input+16, b->domains+96, 32);
memcpy(b->input+20, b->domains+380, 32);
memcpy(b->input+24, b->domains+952, 32);
memcpy(b->input+28, b->domains+944, 32);
memcpy(b->input+32, b->domains+676, 32);
memcpy(b->input+36, b->domains+980, 32);
memcpy(b->input+40, b->domains+592, 32);
memcpy(b->input+44, b->domains+388, 32);
memcpy(b->input+48, b->domains+328, 32);
memcpy(b->input+52, b->domains+664, 32);
memcpy(b->input+56, b->domains+708, 32);
memcpy(b->input+60, b->domains+548, 32);
if (batch_cached(b, 13, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[13], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1792, b->output, 512); b->cached[13] = 1;
status = batch_store(b, 13, 18, 0, 72, 4);
if (status < 0) return status;
status = batch_store(b, 13, 154, 4, 616, 4);
if (status < 0) return status;
status = batch_store(b, 13, 254, 8, 1016, 4);
if (status < 0) return status;
status = batch_store(b, 13, 180, 12, 720, 4);
if (status < 0) return status;
status = batch_store(b, 13, 24, 16, 96, 4);
if (status < 0) return status;
status = batch_store(b, 13, 95, 20, 380, 4);
if (status < 0) return status;
status = batch_store(b, 13, 238, 24, 952, 4);
if (status < 0) return status;
status = batch_store(b, 13, 236, 28, 944, 4);
if (status < 0) return status;
status = batch_store(b, 13, 169, 32, 676, 4);
if (status < 0) return status;
status = batch_store(b, 13, 245, 36, 980, 4);
if (status < 0) return status;
status = batch_store(b, 13, 148, 40, 592, 4);
if (status < 0) return status;
status = batch_store(b, 13, 97, 44, 388, 4);
if (status < 0) return status;
status = batch_store(b, 13, 82, 48, 328, 4);
if (status < 0) return status;
status = batch_store(b, 13, 166, 52, 664, 4);
if (status < 0) return status;
status = batch_store(b, 13, 177, 56, 708, 4);
if (status < 0) return status;
status = batch_store(b, 13, 137, 60, 548, 4);
if (status < 0) return status;
return 1; }
static int batch_step_14(Batch *b) {
int status;
memcpy(b->input+0, b->domains+516, 32);
memcpy(b->input+4, b->domains+248, 32);
memcpy(b->input+8, b->domains+604, 32);
memcpy(b->input+12, b->domains+232, 32);
memcpy(b->input+16, b->domains+424, 32);
memcpy(b->input+20, b->domains+832, 32);
memcpy(b->input+24, b->domains+324, 32);
memcpy(b->input+28, b->domains+368, 32);
memcpy(b->input+32, b->domains+776, 32);
memcpy(b->input+36, b->domains+404, 32);
memcpy(b->input+40, b->domains+28, 32);
memcpy(b->input+44, b->domains+528, 32);
memcpy(b->input+48, b->domains+1004, 32);
memcpy(b->input+52, b->domains+204, 32);
memcpy(b->input+56, b->domains+868, 32);
memcpy(b->input+60, b->domains+60, 32);
if (batch_cached(b, 14, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[14], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1856, b->output, 512); b->cached[14] = 1;
status = batch_store(b, 14, 129, 0, 516, 4);
if (status < 0) return status;
status = batch_store(b, 14, 62, 4, 248, 4);
if (status < 0) return status;
status = batch_store(b, 14, 151, 8, 604, 4);
if (status < 0) return status;
status = batch_store(b, 14, 58, 12, 232, 4);
if (status < 0) return status;
status = batch_store(b, 14, 106, 16, 424, 4);
if (status < 0) return status;
status = batch_store(b, 14, 208, 20, 832, 4);
if (status < 0) return status;
status = batch_store(b, 14, 81, 24, 324, 4);
if (status < 0) return status;
status = batch_store(b, 14, 92, 28, 368, 4);
if (status < 0) return status;
status = batch_store(b, 14, 194, 32, 776, 4);
if (status < 0) return status;
status = batch_store(b, 14, 101, 36, 404, 4);
if (status < 0) return status;
status = batch_store(b, 14, 7, 40, 28, 4);
if (status < 0) return status;
status = batch_store(b, 14, 132, 44, 528, 4);
if (status < 0) return status;
status = batch_store(b, 14, 251, 48, 1004, 4);
if (status < 0) return status;
status = batch_store(b, 14, 51, 52, 204, 4);
if (status < 0) return status;
status = batch_store(b, 14, 217, 56, 868, 4);
if (status < 0) return status;
status = batch_store(b, 14, 15, 60, 60, 4);
if (status < 0) return status;
return 1; }
static int batch_step_15(Batch *b) {
int status;
memcpy(b->input+0, b->domains+396, 32);
memcpy(b->input+4, b->domains+928, 32);
memcpy(b->input+8, b->domains+372, 32);
memcpy(b->input+12, b->domains+68, 32);
memcpy(b->input+16, b->domains+312, 32);
memcpy(b->input+20, b->domains+884, 32);
memcpy(b->input+24, b->domains+612, 32);
memcpy(b->input+28, b->domains+988, 32);
memcpy(b->input+32, b->domains+472, 32);
memcpy(b->input+36, b->domains+768, 32);
memcpy(b->input+40, b->domains+52, 32);
memcpy(b->input+44, b->domains+724, 32);
memcpy(b->input+48, b->domains+80, 32);
memcpy(b->input+52, b->domains+784, 32);
memcpy(b->input+56, b->domains+316, 32);
memcpy(b->input+60, b->domains+0, 32);
if (batch_cached(b, 15, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[15], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1920, b->output, 512); b->cached[15] = 1;
status = batch_store(b, 15, 99, 0, 396, 4);
if (status < 0) return status;
status = batch_store(b, 15, 232, 4, 928, 4);
if (status < 0) return status;
status = batch_store(b, 15, 93, 8, 372, 4);
if (status < 0) return status;
status = batch_store(b, 15, 17, 12, 68, 4);
if (status < 0) return status;
status = batch_store(b, 15, 78, 16, 312, 4);
if (status < 0) return status;
status = batch_store(b, 15, 221, 20, 884, 4);
if (status < 0) return status;
status = batch_store(b, 15, 153, 24, 612, 4);
if (status < 0) return status;
status = batch_store(b, 15, 247, 28, 988, 4);
if (status < 0) return status;
status = batch_store(b, 15, 118, 32, 472, 4);
if (status < 0) return status;
status = batch_store(b, 15, 192, 36, 768, 4);
if (status < 0) return status;
status = batch_store(b, 15, 13, 40, 52, 4);
if (status < 0) return status;
status = batch_store(b, 15, 181, 44, 724, 4);
if (status < 0) return status;
status = batch_store(b, 15, 20, 48, 80, 4);
if (status < 0) return status;
status = batch_store(b, 15, 196, 52, 784, 4);
if (status < 0) return status;
status = batch_store(b, 15, 79, 56, 316, 4);
if (status < 0) return status;
status = batch_store(b, 15, 0, 60, 0, 4);
if (status < 0) return status;
return 1; }
static int batch_step_16(Batch *b) {
int status;
memcpy(b->input+0, b->domains+856, 32);
memcpy(b->input+4, b->domains+1000, 32);
memcpy(b->input+8, b->domains+504, 32);
memcpy(b->input+12, b->domains+844, 32);
memcpy(b->input+16, b->domains+216, 32);
memcpy(b->input+20, b->domains+536, 32);
memcpy(b->input+24, b->domains+76, 32);
memcpy(b->input+28, b->domains+448, 32);
memcpy(b->input+32, b->domains+808, 32);
memcpy(b->input+36, b->domains+500, 32);
memcpy(b->input+40, b->domains+584, 32);
memcpy(b->input+44, b->domains+36, 32);
memcpy(b->input+48, b->domains+936, 32);
memcpy(b->input+52, b->domains+464, 32);
memcpy(b->input+56, b->domains+1012, 32);
memcpy(b->input+60, b->domains+348, 32);
if (batch_cached(b, 16, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[16], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+1984, b->output, 512); b->cached[16] = 1;
status = batch_store(b, 16, 214, 0, 856, 4);
if (status < 0) return status;
status = batch_store(b, 16, 250, 4, 1000, 4);
if (status < 0) return status;
status = batch_store(b, 16, 126, 8, 504, 4);
if (status < 0) return status;
status = batch_store(b, 16, 211, 12, 844, 4);
if (status < 0) return status;
status = batch_store(b, 16, 54, 16, 216, 4);
if (status < 0) return status;
status = batch_store(b, 16, 134, 20, 536, 4);
if (status < 0) return status;
status = batch_store(b, 16, 19, 24, 76, 4);
if (status < 0) return status;
status = batch_store(b, 16, 112, 28, 448, 4);
if (status < 0) return status;
status = batch_store(b, 16, 202, 32, 808, 4);
if (status < 0) return status;
status = batch_store(b, 16, 125, 36, 500, 4);
if (status < 0) return status;
status = batch_store(b, 16, 146, 40, 584, 4);
if (status < 0) return status;
status = batch_store(b, 16, 9, 44, 36, 4);
if (status < 0) return status;
status = batch_store(b, 16, 234, 48, 936, 4);
if (status < 0) return status;
status = batch_store(b, 16, 116, 52, 464, 4);
if (status < 0) return status;
status = batch_store(b, 16, 253, 56, 1012, 4);
if (status < 0) return status;
status = batch_store(b, 16, 87, 60, 348, 4);
if (status < 0) return status;
return 1; }
static int batch_step_17(Batch *b) {
int status;
memcpy(b->input+0, b->domains+140, 32);
memcpy(b->input+4, b->domains+256, 32);
memcpy(b->input+8, b->domains+640, 32);
memcpy(b->input+12, b->domains+880, 32);
memcpy(b->input+16, b->domains+828, 32);
memcpy(b->input+20, b->domains+564, 32);
memcpy(b->input+24, b->domains+984, 32);
memcpy(b->input+28, b->domains+168, 32);
memcpy(b->input+32, b->domains+876, 32);
memcpy(b->input+36, b->domains+960, 32);
memcpy(b->input+40, b->domains+508, 32);
memcpy(b->input+44, b->domains+200, 32);
memcpy(b->input+48, b->domains+72, 32);
memcpy(b->input+52, b->domains+516, 32);
memcpy(b->input+56, b->domains+396, 32);
memcpy(b->input+60, b->domains+856, 32);
if (batch_cached(b, 17, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[17], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+2048, b->output, 512); b->cached[17] = 1;
status = batch_store(b, 17, 35, 0, 140, 4);
if (status < 0) return status;
status = batch_store(b, 17, 64, 4, 256, 4);
if (status < 0) return status;
status = batch_store(b, 17, 160, 8, 640, 4);
if (status < 0) return status;
status = batch_store(b, 17, 220, 12, 880, 4);
if (status < 0) return status;
status = batch_store(b, 17, 207, 16, 828, 4);
if (status < 0) return status;
status = batch_store(b, 17, 141, 20, 564, 4);
if (status < 0) return status;
status = batch_store(b, 17, 246, 24, 984, 4);
if (status < 0) return status;
status = batch_store(b, 17, 42, 28, 168, 4);
if (status < 0) return status;
status = batch_store(b, 17, 219, 32, 876, 4);
if (status < 0) return status;
status = batch_store(b, 17, 240, 36, 960, 4);
if (status < 0) return status;
status = batch_store(b, 17, 127, 40, 508, 4);
if (status < 0) return status;
status = batch_store(b, 17, 50, 44, 200, 4);
if (status < 0) return status;
status = batch_store(b, 17, 18, 48, 72, 4);
if (status < 0) return status;
status = batch_store(b, 17, 129, 52, 516, 4);
if (status < 0) return status;
status = batch_store(b, 17, 99, 56, 396, 4);
if (status < 0) return status;
status = batch_store(b, 17, 214, 60, 856, 4);
if (status < 0) return status;
return 1; }
static int batch_step_18(Batch *b) {
int status;
memcpy(b->input+0, b->domains+760, 32);
memcpy(b->input+4, b->domains+576, 32);
memcpy(b->input+8, b->domains+836, 32);
memcpy(b->input+12, b->domains+108, 32);
memcpy(b->input+16, b->domains+416, 32);
memcpy(b->input+20, b->domains+244, 32);
memcpy(b->input+24, b->domains+136, 32);
memcpy(b->input+28, b->domains+732, 32);
memcpy(b->input+32, b->domains+420, 32);
memcpy(b->input+36, b->domains+488, 32);
memcpy(b->input+40, b->domains+456, 32);
memcpy(b->input+44, b->domains+468, 32);
memcpy(b->input+48, b->domains+616, 32);
memcpy(b->input+52, b->domains+248, 32);
memcpy(b->input+56, b->domains+928, 32);
memcpy(b->input+60, b->domains+1000, 32);
if (batch_cached(b, 18, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[18], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+2112, b->output, 512); b->cached[18] = 1;
status = batch_store(b, 18, 190, 0, 760, 4);
if (status < 0) return status;
status = batch_store(b, 18, 144, 4, 576, 4);
if (status < 0) return status;
status = batch_store(b, 18, 209, 8, 836, 4);
if (status < 0) return status;
status = batch_store(b, 18, 27, 12, 108, 4);
if (status < 0) return status;
status = batch_store(b, 18, 104, 16, 416, 4);
if (status < 0) return status;
status = batch_store(b, 18, 61, 20, 244, 4);
if (status < 0) return status;
status = batch_store(b, 18, 34, 24, 136, 4);
if (status < 0) return status;
status = batch_store(b, 18, 183, 28, 732, 4);
if (status < 0) return status;
status = batch_store(b, 18, 105, 32, 420, 4);
if (status < 0) return status;
status = batch_store(b, 18, 122, 36, 488, 4);
if (status < 0) return status;
status = batch_store(b, 18, 114, 40, 456, 4);
if (status < 0) return status;
status = batch_store(b, 18, 117, 44, 468, 4);
if (status < 0) return status;
status = batch_store(b, 18, 154, 48, 616, 4);
if (status < 0) return status;
status = batch_store(b, 18, 62, 52, 248, 4);
if (status < 0) return status;
status = batch_store(b, 18, 232, 56, 928, 4);
if (status < 0) return status;
status = batch_store(b, 18, 250, 60, 1000, 4);
if (status < 0) return status;
return 1; }
static int batch_step_19(Batch *b) {
int status;
memcpy(b->input+0, b->domains+116, 32);
memcpy(b->input+4, b->domains+40, 32);
memcpy(b->input+8, b->domains+164, 32);
memcpy(b->input+12, b->domains+1008, 32);
memcpy(b->input+16, b->domains+620, 32);
memcpy(b->input+20, b->domains+340, 32);
memcpy(b->input+24, b->domains+492, 32);
memcpy(b->input+28, b->domains+452, 32);
memcpy(b->input+32, b->domains+260, 32);
memcpy(b->input+36, b->domains+940, 32);
memcpy(b->input+40, b->domains+848, 32);
memcpy(b->input+44, b->domains+20, 32);
memcpy(b->input+48, b->domains+1016, 32);
memcpy(b->input+52, b->domains+604, 32);
memcpy(b->input+56, b->domains+372, 32);
memcpy(b->input+60, b->domains+504, 32);
if (batch_cached(b, 19, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[19], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+2176, b->output, 512); b->cached[19] = 1;
status = batch_store(b, 19, 29, 0, 116, 4);
if (status < 0) return status;
status = batch_store(b, 19, 10, 4, 40, 4);
if (status < 0) return status;
status = batch_store(b, 19, 41, 8, 164, 4);
if (status < 0) return status;
status = batch_store(b, 19, 252, 12, 1008, 4);
if (status < 0) return status;
status = batch_store(b, 19, 155, 16, 620, 4);
if (status < 0) return status;
status = batch_store(b, 19, 85, 20, 340, 4);
if (status < 0) return status;
status = batch_store(b, 19, 123, 24, 492, 4);
if (status < 0) return status;
status = batch_store(b, 19, 113, 28, 452, 4);
if (status < 0) return status;
status = batch_store(b, 19, 65, 32, 260, 4);
if (status < 0) return status;
status = batch_store(b, 19, 235, 36, 940, 4);
if (status < 0) return status;
status = batch_store(b, 19, 212, 40, 848, 4);
if (status < 0) return status;
status = batch_store(b, 19, 5, 44, 20, 4);
if (status < 0) return status;
status = batch_store(b, 19, 254, 48, 1016, 4);
if (status < 0) return status;
status = batch_store(b, 19, 151, 52, 604, 4);
if (status < 0) return status;
status = batch_store(b, 19, 93, 56, 372, 4);
if (status < 0) return status;
status = batch_store(b, 19, 126, 60, 504, 4);
if (status < 0) return status;
return 1; }
static int batch_step_20(Batch *b) {
int status;
memcpy(b->input+0, b->domains+268, 32);
memcpy(b->input+4, b->domains+816, 32);
memcpy(b->input+8, b->domains+740, 32);
memcpy(b->input+12, b->domains+744, 32);
memcpy(b->input+16, b->domains+624, 32);
memcpy(b->input+20, b->domains+224, 32);
memcpy(b->input+24, b->domains+288, 32);
memcpy(b->input+28, b->domains+648, 32);
memcpy(b->input+32, b->domains+428, 32);
memcpy(b->input+36, b->domains+196, 32);
memcpy(b->input+40, b->domains+84, 32);
memcpy(b->input+44, b->domains+896, 32);
memcpy(b->input+48, b->domains+720, 32);
memcpy(b->input+52, b->domains+232, 32);
memcpy(b->input+56, b->domains+68, 32);
memcpy(b->input+60, b->domains+844, 32);
if (batch_cached(b, 20, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[20], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+2240, b->output, 512); b->cached[20] = 1;
status = batch_store(b, 20, 67, 0, 268, 4);
if (status < 0) return status;
status = batch_store(b, 20, 204, 4, 816, 4);
if (status < 0) return status;
status = batch_store(b, 20, 185, 8, 740, 4);
if (status < 0) return status;
status = batch_store(b, 20, 186, 12, 744, 4);
if (status < 0) return status;
status = batch_store(b, 20, 156, 16, 624, 4);
if (status < 0) return status;
status = batch_store(b, 20, 56, 20, 224, 4);
if (status < 0) return status;
status = batch_store(b, 20, 72, 24, 288, 4);
if (status < 0) return status;
status = batch_store(b, 20, 162, 28, 648, 4);
if (status < 0) return status;
status = batch_store(b, 20, 107, 32, 428, 4);
if (status < 0) return status;
status = batch_store(b, 20, 49, 36, 196, 4);
if (status < 0) return status;
status = batch_store(b, 20, 21, 40, 84, 4);
if (status < 0) return status;
status = batch_store(b, 20, 224, 44, 896, 4);
if (status < 0) return status;
status = batch_store(b, 20, 180, 48, 720, 4);
if (status < 0) return status;
status = batch_store(b, 20, 58, 52, 232, 4);
if (status < 0) return status;
status = batch_store(b, 20, 17, 56, 68, 4);
if (status < 0) return status;
status = batch_store(b, 20, 211, 60, 844, 4);
if (status < 0) return status;
return 1; }
static int batch_step_21(Batch *b) {
int status;
memcpy(b->input+0, b->domains+860, 32);
memcpy(b->input+4, b->domains+4, 32);
memcpy(b->input+8, b->domains+280, 32);
memcpy(b->input+12, b->domains+276, 32);
memcpy(b->input+16, b->domains+8, 32);
memcpy(b->input+20, b->domains+572, 32);
memcpy(b->input+24, b->domains+804, 32);
memcpy(b->input+28, b->domains+304, 32);
memcpy(b->input+32, b->domains+668, 32);
memcpy(b->input+36, b->domains+752, 32);
memcpy(b->input+40, b->domains+284, 32);
memcpy(b->input+44, b->domains+496, 32);
memcpy(b->input+48, b->domains+96, 32);
memcpy(b->input+52, b->domains+424, 32);
memcpy(b->input+56, b->domains+312, 32);
memcpy(b->input+60, b->domains+216, 32);
if (batch_cached(b, 21, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[21], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+2304, b->output, 512); b->cached[21] = 1;
status = batch_store(b, 21, 215, 0, 860, 4);
if (status < 0) return status;
status = batch_store(b, 21, 1, 4, 4, 4);
if (status < 0) return status;
status = batch_store(b, 21, 70, 8, 280, 4);
if (status < 0) return status;
status = batch_store(b, 21, 69, 12, 276, 4);
if (status < 0) return status;
status = batch_store(b, 21, 2, 16, 8, 4);
if (status < 0) return status;
status = batch_store(b, 21, 143, 20, 572, 4);
if (status < 0) return status;
status = batch_store(b, 21, 201, 24, 804, 4);
if (status < 0) return status;
status = batch_store(b, 21, 76, 28, 304, 4);
if (status < 0) return status;
status = batch_store(b, 21, 167, 32, 668, 4);
if (status < 0) return status;
status = batch_store(b, 21, 188, 36, 752, 4);
if (status < 0) return status;
status = batch_store(b, 21, 71, 40, 284, 4);
if (status < 0) return status;
status = batch_store(b, 21, 124, 44, 496, 4);
if (status < 0) return status;
status = batch_store(b, 21, 24, 48, 96, 4);
if (status < 0) return status;
status = batch_store(b, 21, 106, 52, 424, 4);
if (status < 0) return status;
status = batch_store(b, 21, 78, 56, 312, 4);
if (status < 0) return status;
status = batch_store(b, 21, 54, 60, 216, 4);
if (status < 0) return status;
return 1; }
static int batch_step_22(Batch *b) {
int status;
memcpy(b->input+0, b->domains+652, 32);
memcpy(b->input+4, b->domains+264, 32);
memcpy(b->input+8, b->domains+636, 32);
memcpy(b->input+12, b->domains+176, 32);
memcpy(b->input+16, b->domains+32, 32);
memcpy(b->input+20, b->domains+524, 32);
memcpy(b->input+24, b->domains+376, 32);
memcpy(b->input+28, b->domains+180, 32);
memcpy(b->input+32, b->domains+588, 32);
memcpy(b->input+36, b->domains+408, 32);
memcpy(b->input+40, b->domains+436, 32);
memcpy(b->input+44, b->domains+912, 32);
memcpy(b->input+48, b->domains+380, 32);
memcpy(b->input+52, b->domains+832, 32);
memcpy(b->input+56, b->domains+884, 32);
memcpy(b->input+60, b->domains+536, 32);
if (batch_cached(b, 22, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[22], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+2368, b->output, 512); b->cached[22] = 1;
status = batch_store(b, 22, 163, 0, 652, 4);
if (status < 0) return status;
status = batch_store(b, 22, 66, 4, 264, 4);
if (status < 0) return status;
status = batch_store(b, 22, 159, 8, 636, 4);
if (status < 0) return status;
status = batch_store(b, 22, 44, 12, 176, 4);
if (status < 0) return status;
status = batch_store(b, 22, 8, 16, 32, 4);
if (status < 0) return status;
status = batch_store(b, 22, 131, 20, 524, 4);
if (status < 0) return status;
status = batch_store(b, 22, 94, 24, 376, 4);
if (status < 0) return status;
status = batch_store(b, 22, 45, 28, 180, 4);
if (status < 0) return status;
status = batch_store(b, 22, 147, 32, 588, 4);
if (status < 0) return status;
status = batch_store(b, 22, 102, 36, 408, 4);
if (status < 0) return status;
status = batch_store(b, 22, 109, 40, 436, 4);
if (status < 0) return status;
status = batch_store(b, 22, 228, 44, 912, 4);
if (status < 0) return status;
status = batch_store(b, 22, 95, 48, 380, 4);
if (status < 0) return status;
status = batch_store(b, 22, 208, 52, 832, 4);
if (status < 0) return status;
status = batch_store(b, 22, 221, 56, 884, 4);
if (status < 0) return status;
status = batch_store(b, 22, 134, 60, 536, 4);
if (status < 0) return status;
return 1; }
static int batch_step_23(Batch *b) {
int status;
memcpy(b->input+0, b->domains+220, 32);
memcpy(b->input+4, b->domains+800, 32);
memcpy(b->input+8, b->domains+864, 32);
memcpy(b->input+12, b->domains+764, 32);
memcpy(b->input+16, b->domains+56, 32);
memcpy(b->input+20, b->domains+748, 32);
memcpy(b->input+24, b->domains+948, 32);
memcpy(b->input+28, b->domains+88, 32);
memcpy(b->input+32, b->domains+484, 32);
memcpy(b->input+36, b->domains+296, 32);
memcpy(b->input+40, b->domains+956, 32);
memcpy(b->input+44, b->domains+688, 32);
memcpy(b->input+48, b->domains+952, 32);
memcpy(b->input+52, b->domains+324, 32);
memcpy(b->input+56, b->domains+612, 32);
memcpy(b->input+60, b->domains+76, 32);
if (batch_cached(b, 23, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[23], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+2432, b->output, 512); b->cached[23] = 1;
status = batch_store(b, 23, 55, 0, 220, 4);
if (status < 0) return status;
status = batch_store(b, 23, 200, 4, 800, 4);
if (status < 0) return status;
status = batch_store(b, 23, 216, 8, 864, 4);
if (status < 0) return status;
status = batch_store(b, 23, 191, 12, 764, 4);
if (status < 0) return status;
status = batch_store(b, 23, 14, 16, 56, 4);
if (status < 0) return status;
status = batch_store(b, 23, 187, 20, 748, 4);
if (status < 0) return status;
status = batch_store(b, 23, 237, 24, 948, 4);
if (status < 0) return status;
status = batch_store(b, 23, 22, 28, 88, 4);
if (status < 0) return status;
status = batch_store(b, 23, 121, 32, 484, 4);
if (status < 0) return status;
status = batch_store(b, 23, 74, 36, 296, 4);
if (status < 0) return status;
status = batch_store(b, 23, 239, 40, 956, 4);
if (status < 0) return status;
status = batch_store(b, 23, 172, 44, 688, 4);
if (status < 0) return status;
status = batch_store(b, 23, 238, 48, 952, 4);
if (status < 0) return status;
status = batch_store(b, 23, 81, 52, 324, 4);
if (status < 0) return status;
status = batch_store(b, 23, 153, 56, 612, 4);
if (status < 0) return status;
status = batch_store(b, 23, 19, 60, 76, 4);
if (status < 0) return status;
return 1; }
static int batch_step_24(Batch *b) {
int status;
memcpy(b->input+0, b->domains+920, 32);
memcpy(b->input+4, b->domains+996, 32);
memcpy(b->input+8, b->domains+112, 32);
memcpy(b->input+12, b->domains+728, 32);
memcpy(b->input+16, b->domains+476, 32);
memcpy(b->input+20, b->domains+188, 32);
memcpy(b->input+24, b->domains+272, 32);
memcpy(b->input+28, b->domains+552, 32);
memcpy(b->input+32, b->domains+692, 32);
memcpy(b->input+36, b->domains+820, 32);
memcpy(b->input+40, b->domains+892, 32);
memcpy(b->input+44, b->domains+900, 32);
memcpy(b->input+48, b->domains+944, 32);
memcpy(b->input+52, b->domains+368, 32);
memcpy(b->input+56, b->domains+988, 32);
memcpy(b->input+60, b->domains+448, 32);
if (batch_cached(b, 24, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[24], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+2496, b->output, 512); b->cached[24] = 1;
status = batch_store(b, 24, 230, 0, 920, 4);
if (status < 0) return status;
status = batch_store(b, 24, 249, 4, 996, 4);
if (status < 0) return status;
status = batch_store(b, 24, 28, 8, 112, 4);
if (status < 0) return status;
status = batch_store(b, 24, 182, 12, 728, 4);
if (status < 0) return status;
status = batch_store(b, 24, 119, 16, 476, 4);
if (status < 0) return status;
status = batch_store(b, 24, 47, 20, 188, 4);
if (status < 0) return status;
status = batch_store(b, 24, 68, 24, 272, 4);
if (status < 0) return status;
status = batch_store(b, 24, 138, 28, 552, 4);
if (status < 0) return status;
status = batch_store(b, 24, 173, 32, 692, 4);
if (status < 0) return status;
status = batch_store(b, 24, 205, 36, 820, 4);
if (status < 0) return status;
status = batch_store(b, 24, 223, 40, 892, 4);
if (status < 0) return status;
status = batch_store(b, 24, 225, 44, 900, 4);
if (status < 0) return status;
status = batch_store(b, 24, 236, 48, 944, 4);
if (status < 0) return status;
status = batch_store(b, 24, 92, 52, 368, 4);
if (status < 0) return status;
status = batch_store(b, 24, 247, 56, 988, 4);
if (status < 0) return status;
status = batch_store(b, 24, 112, 60, 448, 4);
if (status < 0) return status;
return 1; }
static int batch_step_25(Batch *b) {
int status;
memcpy(b->input+0, b->domains+460, 32);
memcpy(b->input+4, b->domains+772, 32);
memcpy(b->input+8, b->domains+104, 32);
memcpy(b->input+12, b->domains+332, 32);
memcpy(b->input+16, b->domains+16, 32);
memcpy(b->input+20, b->domains+300, 32);
memcpy(b->input+24, b->domains+972, 32);
memcpy(b->input+28, b->domains+656, 32);
memcpy(b->input+32, b->domains+364, 32);
memcpy(b->input+36, b->domains+352, 32);
memcpy(b->input+40, b->domains+412, 32);
memcpy(b->input+44, b->domains+968, 32);
memcpy(b->input+48, b->domains+676, 32);
memcpy(b->input+52, b->domains+776, 32);
memcpy(b->input+56, b->domains+472, 32);
memcpy(b->input+60, b->domains+808, 32);
if (batch_cached(b, 25, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[25], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+2560, b->output, 512); b->cached[25] = 1;
status = batch_store(b, 25, 115, 0, 460, 4);
if (status < 0) return status;
status = batch_store(b, 25, 193, 4, 772, 4);
if (status < 0) return status;
status = batch_store(b, 25, 26, 8, 104, 4);
if (status < 0) return status;
status = batch_store(b, 25, 83, 12, 332, 4);
if (status < 0) return status;
status = batch_store(b, 25, 4, 16, 16, 4);
if (status < 0) return status;
status = batch_store(b, 25, 75, 20, 300, 4);
if (status < 0) return status;
status = batch_store(b, 25, 243, 24, 972, 4);
if (status < 0) return status;
status = batch_store(b, 25, 164, 28, 656, 4);
if (status < 0) return status;
status = batch_store(b, 25, 91, 32, 364, 4);
if (status < 0) return status;
status = batch_store(b, 25, 88, 36, 352, 4);
if (status < 0) return status;
status = batch_store(b, 25, 103, 40, 412, 4);
if (status < 0) return status;
status = batch_store(b, 25, 242, 44, 968, 4);
if (status < 0) return status;
status = batch_store(b, 25, 169, 48, 676, 4);
if (status < 0) return status;
status = batch_store(b, 25, 194, 52, 776, 4);
if (status < 0) return status;
status = batch_store(b, 25, 118, 56, 472, 4);
if (status < 0) return status;
status = batch_store(b, 25, 202, 60, 808, 4);
if (status < 0) return status;
return 1; }
static int batch_step_26(Batch *b) {
int status;
memcpy(b->input+0, b->domains+780, 32);
memcpy(b->input+4, b->domains+852, 32);
memcpy(b->input+8, b->domains+976, 32);
memcpy(b->input+12, b->domains+608, 32);
memcpy(b->input+16, b->domains+400, 32);
memcpy(b->input+20, b->domains+792, 32);
memcpy(b->input+24, b->domains+344, 32);
memcpy(b->input+28, b->domains+628, 32);
memcpy(b->input+32, b->domains+736, 32);
memcpy(b->input+36, b->domains+556, 32);
memcpy(b->input+40, b->domains+92, 32);
memcpy(b->input+44, b->domains+308, 32);
memcpy(b->input+48, b->domains+980, 32);
memcpy(b->input+52, b->domains+404, 32);
memcpy(b->input+56, b->domains+768, 32);
memcpy(b->input+60, b->domains+500, 32);
if (batch_cached(b, 26, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[26], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+2624, b->output, 512); b->cached[26] = 1;
status = batch_store(b, 26, 195, 0, 780, 4);
if (status < 0) return status;
status = batch_store(b, 26, 213, 4, 852, 4);
if (status < 0) return status;
status = batch_store(b, 26, 244, 8, 976, 4);
if (status < 0) return status;
status = batch_store(b, 26, 152, 12, 608, 4);
if (status < 0) return status;
status = batch_store(b, 26, 100, 16, 400, 4);
if (status < 0) return status;
status = batch_store(b, 26, 198, 20, 792, 4);
if (status < 0) return status;
status = batch_store(b, 26, 86, 24, 344, 4);
if (status < 0) return status;
status = batch_store(b, 26, 157, 28, 628, 4);
if (status < 0) return status;
status = batch_store(b, 26, 184, 32, 736, 4);
if (status < 0) return status;
status = batch_store(b, 26, 139, 36, 556, 4);
if (status < 0) return status;
status = batch_store(b, 26, 23, 40, 92, 4);
if (status < 0) return status;
status = batch_store(b, 26, 77, 44, 308, 4);
if (status < 0) return status;
status = batch_store(b, 26, 245, 48, 980, 4);
if (status < 0) return status;
status = batch_store(b, 26, 101, 52, 404, 4);
if (status < 0) return status;
status = batch_store(b, 26, 192, 56, 768, 4);
if (status < 0) return status;
status = batch_store(b, 26, 125, 60, 500, 4);
if (status < 0) return status;
return 1; }
static int batch_step_27(Batch *b) {
int status;
memcpy(b->input+0, b->domains+684, 32);
memcpy(b->input+4, b->domains+384, 32);
memcpy(b->input+8, b->domains+788, 32);
memcpy(b->input+12, b->domains+392, 32);
memcpy(b->input+16, b->domains+160, 32);
memcpy(b->input+20, b->domains+696, 32);
memcpy(b->input+24, b->domains+360, 32);
memcpy(b->input+28, b->domains+64, 32);
memcpy(b->input+32, b->domains+212, 32);
memcpy(b->input+36, b->domains+144, 32);
memcpy(b->input+40, b->domains+560, 32);
memcpy(b->input+44, b->domains+596, 32);
memcpy(b->input+48, b->domains+592, 32);
memcpy(b->input+52, b->domains+28, 32);
memcpy(b->input+56, b->domains+52, 32);
memcpy(b->input+60, b->domains+584, 32);
if (batch_cached(b, 27, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[27], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+2688, b->output, 512); b->cached[27] = 1;
status = batch_store(b, 27, 171, 0, 684, 4);
if (status < 0) return status;
status = batch_store(b, 27, 96, 4, 384, 4);
if (status < 0) return status;
status = batch_store(b, 27, 197, 8, 788, 4);
if (status < 0) return status;
status = batch_store(b, 27, 98, 12, 392, 4);
if (status < 0) return status;
status = batch_store(b, 27, 40, 16, 160, 4);
if (status < 0) return status;
status = batch_store(b, 27, 174, 20, 696, 4);
if (status < 0) return status;
status = batch_store(b, 27, 90, 24, 360, 4);
if (status < 0) return status;
status = batch_store(b, 27, 16, 28, 64, 4);
if (status < 0) return status;
status = batch_store(b, 27, 53, 32, 212, 4);
if (status < 0) return status;
status = batch_store(b, 27, 36, 36, 144, 4);
if (status < 0) return status;
status = batch_store(b, 27, 140, 40, 560, 4);
if (status < 0) return status;
status = batch_store(b, 27, 149, 44, 596, 4);
if (status < 0) return status;
status = batch_store(b, 27, 148, 48, 592, 4);
if (status < 0) return status;
status = batch_store(b, 27, 7, 52, 28, 4);
if (status < 0) return status;
status = batch_store(b, 27, 13, 56, 52, 4);
if (status < 0) return status;
status = batch_store(b, 27, 146, 60, 584, 4);
if (status < 0) return status;
return 1; }
static int batch_step_28(Batch *b) {
int status;
memcpy(b->input+0, b->domains+120, 32);
memcpy(b->input+4, b->domains+580, 32);
memcpy(b->input+8, b->domains+12, 32);
memcpy(b->input+12, b->domains+672, 32);
memcpy(b->input+16, b->domains+48, 32);
memcpy(b->input+20, b->domains+336, 32);
memcpy(b->input+24, b->domains+128, 32);
memcpy(b->input+28, b->domains+240, 32);
memcpy(b->input+32, b->domains+812, 32);
memcpy(b->input+36, b->domains+932, 32);
memcpy(b->input+40, b->domains+440, 32);
memcpy(b->input+44, b->domains+872, 32);
memcpy(b->input+48, b->domains+388, 32);
memcpy(b->input+52, b->domains+528, 32);
memcpy(b->input+56, b->domains+724, 32);
memcpy(b->input+60, b->domains+36, 32);
if (batch_cached(b, 28, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[28], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+2752, b->output, 512); b->cached[28] = 1;
status = batch_store(b, 28, 30, 0, 120, 4);
if (status < 0) return status;
status = batch_store(b, 28, 145, 4, 580, 4);
if (status < 0) return status;
status = batch_store(b, 28, 3, 8, 12, 4);
if (status < 0) return status;
status = batch_store(b, 28, 168, 12, 672, 4);
if (status < 0) return status;
status = batch_store(b, 28, 12, 16, 48, 4);
if (status < 0) return status;
status = batch_store(b, 28, 84, 20, 336, 4);
if (status < 0) return status;
status = batch_store(b, 28, 32, 24, 128, 4);
if (status < 0) return status;
status = batch_store(b, 28, 60, 28, 240, 4);
if (status < 0) return status;
status = batch_store(b, 28, 203, 32, 812, 4);
if (status < 0) return status;
status = batch_store(b, 28, 233, 36, 932, 4);
if (status < 0) return status;
status = batch_store(b, 28, 110, 40, 440, 4);
if (status < 0) return status;
status = batch_store(b, 28, 218, 44, 872, 4);
if (status < 0) return status;
status = batch_store(b, 28, 97, 48, 388, 4);
if (status < 0) return status;
status = batch_store(b, 28, 132, 52, 528, 4);
if (status < 0) return status;
status = batch_store(b, 28, 181, 56, 724, 4);
if (status < 0) return status;
status = batch_store(b, 28, 9, 60, 36, 4);
if (status < 0) return status;
return 1; }
static int batch_step_29(Batch *b) {
int status;
memcpy(b->input+0, b->domains+924, 32);
memcpy(b->input+4, b->domains+132, 32);
memcpy(b->input+8, b->domains+236, 32);
memcpy(b->input+12, b->domains+252, 32);
memcpy(b->input+16, b->domains+320, 32);
memcpy(b->input+20, b->domains+660, 32);
memcpy(b->input+24, b->domains+100, 32);
memcpy(b->input+28, b->domains+600, 32);
memcpy(b->input+32, b->domains+156, 32);
memcpy(b->input+36, b->domains+888, 32);
memcpy(b->input+40, b->domains+520, 32);
memcpy(b->input+44, b->domains+916, 32);
memcpy(b->input+48, b->domains+328, 32);
memcpy(b->input+52, b->domains+1004, 32);
memcpy(b->input+56, b->domains+80, 32);
memcpy(b->input+60, b->domains+936, 32);
if (batch_cached(b, 29, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[29], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+2816, b->output, 512); b->cached[29] = 1;
status = batch_store(b, 29, 231, 0, 924, 4);
if (status < 0) return status;
status = batch_store(b, 29, 33, 4, 132, 4);
if (status < 0) return status;
status = batch_store(b, 29, 59, 8, 236, 4);
if (status < 0) return status;
status = batch_store(b, 29, 63, 12, 252, 4);
if (status < 0) return status;
status = batch_store(b, 29, 80, 16, 320, 4);
if (status < 0) return status;
status = batch_store(b, 29, 165, 20, 660, 4);
if (status < 0) return status;
status = batch_store(b, 29, 25, 24, 100, 4);
if (status < 0) return status;
status = batch_store(b, 29, 150, 28, 600, 4);
if (status < 0) return status;
status = batch_store(b, 29, 39, 32, 156, 4);
if (status < 0) return status;
status = batch_store(b, 29, 222, 36, 888, 4);
if (status < 0) return status;
status = batch_store(b, 29, 130, 40, 520, 4);
if (status < 0) return status;
status = batch_store(b, 29, 229, 44, 916, 4);
if (status < 0) return status;
status = batch_store(b, 29, 82, 48, 328, 4);
if (status < 0) return status;
status = batch_store(b, 29, 251, 52, 1004, 4);
if (status < 0) return status;
status = batch_store(b, 29, 20, 56, 80, 4);
if (status < 0) return status;
status = batch_store(b, 29, 234, 60, 936, 4);
if (status < 0) return status;
return 1; }
static int batch_step_30(Batch *b) {
int status;
memcpy(b->input+0, b->domains+228, 32);
memcpy(b->input+4, b->domains+700, 32);
memcpy(b->input+8, b->domains+172, 32);
memcpy(b->input+12, b->domains+292, 32);
memcpy(b->input+16, b->domains+532, 32);
memcpy(b->input+20, b->domains+148, 32);
memcpy(b->input+24, b->domains+24, 32);
memcpy(b->input+28, b->domains+540, 32);
memcpy(b->input+32, b->domains+208, 32);
memcpy(b->input+36, b->domains+680, 32);
memcpy(b->input+40, b->domains+568, 32);
memcpy(b->input+44, b->domains+444, 32);
memcpy(b->input+48, b->domains+664, 32);
memcpy(b->input+52, b->domains+204, 32);
memcpy(b->input+56, b->domains+784, 32);
memcpy(b->input+60, b->domains+464, 32);
if (batch_cached(b, 30, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[30], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+2880, b->output, 512); b->cached[30] = 1;
status = batch_store(b, 30, 57, 0, 228, 4);
if (status < 0) return status;
status = batch_store(b, 30, 175, 4, 700, 4);
if (status < 0) return status;
status = batch_store(b, 30, 43, 8, 172, 4);
if (status < 0) return status;
status = batch_store(b, 30, 73, 12, 292, 4);
if (status < 0) return status;
status = batch_store(b, 30, 133, 16, 532, 4);
if (status < 0) return status;
status = batch_store(b, 30, 37, 20, 148, 4);
if (status < 0) return status;
status = batch_store(b, 30, 6, 24, 24, 4);
if (status < 0) return status;
status = batch_store(b, 30, 135, 28, 540, 4);
if (status < 0) return status;
status = batch_store(b, 30, 52, 32, 208, 4);
if (status < 0) return status;
status = batch_store(b, 30, 170, 36, 680, 4);
if (status < 0) return status;
status = batch_store(b, 30, 142, 40, 568, 4);
if (status < 0) return status;
status = batch_store(b, 30, 111, 44, 444, 4);
if (status < 0) return status;
status = batch_store(b, 30, 166, 48, 664, 4);
if (status < 0) return status;
status = batch_store(b, 30, 51, 52, 204, 4);
if (status < 0) return status;
status = batch_store(b, 30, 196, 56, 784, 4);
if (status < 0) return status;
status = batch_store(b, 30, 116, 60, 464, 4);
if (status < 0) return status;
return 1; }
static int batch_step_31(Batch *b) {
int status;
memcpy(b->input+0, b->domains+644, 32);
memcpy(b->input+4, b->domains+1020, 32);
memcpy(b->input+8, b->domains+704, 32);
memcpy(b->input+12, b->domains+192, 32);
memcpy(b->input+16, b->domains+796, 32);
memcpy(b->input+20, b->domains+712, 32);
memcpy(b->input+24, b->domains+756, 32);
memcpy(b->input+28, b->domains+904, 32);
memcpy(b->input+32, b->domains+992, 32);
memcpy(b->input+36, b->domains+432, 32);
memcpy(b->input+40, b->domains+356, 32);
memcpy(b->input+44, b->domains+152, 32);
memcpy(b->input+48, b->domains+708, 32);
memcpy(b->input+52, b->domains+868, 32);
memcpy(b->input+56, b->domains+316, 32);
memcpy(b->input+60, b->domains+1012, 32);
if (batch_cached(b, 31, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[31], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+2944, b->output, 512); b->cached[31] = 1;
status = batch_store(b, 31, 161, 0, 644, 4);
if (status < 0) return status;
status = batch_store(b, 31, 255, 4, 1020, 4);
if (status < 0) return status;
status = batch_store(b, 31, 176, 8, 704, 4);
if (status < 0) return status;
status = batch_store(b, 31, 48, 12, 192, 4);
if (status < 0) return status;
status = batch_store(b, 31, 199, 16, 796, 4);
if (status < 0) return status;
status = batch_store(b, 31, 178, 20, 712, 4);
if (status < 0) return status;
status = batch_store(b, 31, 189, 24, 756, 4);
if (status < 0) return status;
status = batch_store(b, 31, 226, 28, 904, 4);
if (status < 0) return status;
status = batch_store(b, 31, 248, 32, 992, 4);
if (status < 0) return status;
status = batch_store(b, 31, 108, 36, 432, 4);
if (status < 0) return status;
status = batch_store(b, 31, 89, 40, 356, 4);
if (status < 0) return status;
status = batch_store(b, 31, 38, 44, 152, 4);
if (status < 0) return status;
status = batch_store(b, 31, 177, 48, 708, 4);
if (status < 0) return status;
status = batch_store(b, 31, 217, 52, 868, 4);
if (status < 0) return status;
status = batch_store(b, 31, 79, 56, 316, 4);
if (status < 0) return status;
status = batch_store(b, 31, 253, 60, 1012, 4);
if (status < 0) return status;
return 1; }
static int batch_step_32(Batch *b) {
int status;
memcpy(b->input+0, b->domains+716, 32);
memcpy(b->input+4, b->domains+632, 32);
memcpy(b->input+8, b->domains+184, 32);
memcpy(b->input+12, b->domains+44, 32);
memcpy(b->input+16, b->domains+512, 32);
memcpy(b->input+20, b->domains+964, 32);
memcpy(b->input+24, b->domains+824, 32);
memcpy(b->input+28, b->domains+480, 32);
memcpy(b->input+32, b->domains+544, 32);
memcpy(b->input+36, b->domains+124, 32);
memcpy(b->input+40, b->domains+840, 32);
memcpy(b->input+44, b->domains+908, 32);
memcpy(b->input+48, b->domains+548, 32);
memcpy(b->input+52, b->domains+60, 32);
memcpy(b->input+56, b->domains+0, 32);
memcpy(b->input+60, b->domains+348, 32);
if (batch_cached(b, 32, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[32], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+3008, b->output, 512); b->cached[32] = 1;
status = batch_store(b, 32, 179, 0, 716, 4);
if (status < 0) return status;
status = batch_store(b, 32, 158, 4, 632, 4);
if (status < 0) return status;
status = batch_store(b, 32, 46, 8, 184, 4);
if (status < 0) return status;
status = batch_store(b, 32, 11, 12, 44, 4);
if (status < 0) return status;
status = batch_store(b, 32, 128, 16, 512, 4);
if (status < 0) return status;
status = batch_store(b, 32, 241, 20, 964, 4);
if (status < 0) return status;
status = batch_store(b, 32, 206, 24, 824, 4);
if (status < 0) return status;
status = batch_store(b, 32, 120, 28, 480, 4);
if (status < 0) return status;
status = batch_store(b, 32, 136, 32, 544, 4);
if (status < 0) return status;
status = batch_store(b, 32, 31, 36, 124, 4);
if (status < 0) return status;
status = batch_store(b, 32, 210, 40, 840, 4);
if (status < 0) return status;
status = batch_store(b, 32, 227, 44, 908, 4);
if (status < 0) return status;
status = batch_store(b, 32, 137, 48, 548, 4);
if (status < 0) return status;
status = batch_store(b, 32, 15, 52, 60, 4);
if (status < 0) return status;
status = batch_store(b, 32, 0, 56, 0, 4);
if (status < 0) return status;
status = batch_store(b, 32, 87, 60, 348, 4);
if (status < 0) return status;
return 1; }
static int batch_step_33(Batch *b) {
int status;
memcpy(b->input+0, b->domains+140, 32);
memcpy(b->input+4, b->domains+576, 32);
memcpy(b->input+8, b->domains+164, 32);
memcpy(b->input+12, b->domains+744, 32);
memcpy(b->input+16, b->domains+8, 32);
memcpy(b->input+20, b->domains+524, 32);
memcpy(b->input+24, b->domains+948, 32);
memcpy(b->input+28, b->domains+552, 32);
memcpy(b->input+32, b->domains+364, 32);
memcpy(b->input+36, b->domains+556, 32);
memcpy(b->input+40, b->domains+560, 32);
memcpy(b->input+44, b->domains+872, 32);
memcpy(b->input+48, b->domains+328, 32);
memcpy(b->input+52, b->domains+204, 32);
memcpy(b->input+56, b->domains+316, 32);
memcpy(b->input+60, b->domains+348, 32);
if (batch_cached(b, 33, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[33], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+3072, b->output, 512); b->cached[33] = 1;
status = batch_store(b, 33, 35, 0, 140, 4);
if (status < 0) return status;
status = batch_store(b, 33, 144, 4, 576, 4);
if (status < 0) return status;
status = batch_store(b, 33, 41, 8, 164, 4);
if (status < 0) return status;
status = batch_store(b, 33, 186, 12, 744, 4);
if (status < 0) return status;
status = batch_store(b, 33, 2, 16, 8, 4);
if (status < 0) return status;
status = batch_store(b, 33, 131, 20, 524, 4);
if (status < 0) return status;
status = batch_store(b, 33, 237, 24, 948, 4);
if (status < 0) return status;
status = batch_store(b, 33, 138, 28, 552, 4);
if (status < 0) return status;
status = batch_store(b, 33, 91, 32, 364, 4);
if (status < 0) return status;
status = batch_store(b, 33, 139, 36, 556, 4);
if (status < 0) return status;
status = batch_store(b, 33, 140, 40, 560, 4);
if (status < 0) return status;
status = batch_store(b, 33, 218, 44, 872, 4);
if (status < 0) return status;
status = batch_store(b, 33, 82, 48, 328, 4);
if (status < 0) return status;
status = batch_store(b, 33, 51, 52, 204, 4);
if (status < 0) return status;
status = batch_store(b, 33, 79, 56, 316, 4);
if (status < 0) return status;
status = batch_store(b, 33, 87, 60, 348, 4);
if (status < 0) return status;
return 1; }
static int batch_step_34(Batch *b) {
int status;
memcpy(b->input+0, b->domains+716, 32);
memcpy(b->input+4, b->domains+1020, 32);
memcpy(b->input+8, b->domains+172, 32);
memcpy(b->input+12, b->domains+252, 32);
memcpy(b->input+16, b->domains+48, 32);
memcpy(b->input+20, b->domains+696, 32);
memcpy(b->input+24, b->domains+344, 32);
memcpy(b->input+28, b->domains+656, 32);
memcpy(b->input+32, b->domains+692, 32);
memcpy(b->input+36, b->domains+296, 32);
memcpy(b->input+40, b->domains+436, 32);
memcpy(b->input+44, b->domains+496, 32);
memcpy(b->input+48, b->domains+720, 32);
memcpy(b->input+52, b->domains+604, 32);
memcpy(b->input+56, b->domains+928, 32);
memcpy(b->input+60, b->domains+856, 32);
if (batch_cached(b, 34, 64)) return 1;
++b->counts[1];
status = sum_shape_0(b->plans[34], b->input, b->output);
if (status <= 0) return status;
memcpy(b->cache+3136, b->output, 512); b->cached[34] = 1;
status = batch_store(b, 34, 179, 0, 716, 4);
if (status < 0) return status;
status = batch_store(b, 34, 255, 4, 1020, 4);
if (status < 0) return status;
status = batch_store(b, 34, 43, 8, 172, 4);
if (status < 0) return status;
status = batch_store(b, 34, 63, 12, 252, 4);
if (status < 0) return status;
status = batch_store(b, 34, 12, 16, 48, 4);
if (status < 0) return status;
status = batch_store(b, 34, 174, 20, 696, 4);
if (status < 0) return status;
status = batch_store(b, 34, 86, 24, 344, 4);
if (status < 0) return status;
status = batch_store(b, 34, 164, 28, 656, 4);
if (status < 0) return status;
status = batch_store(b, 34, 173, 32, 692, 4);
if (status < 0) return status;
status = batch_store(b, 34, 74, 36, 296, 4);
if (status < 0) return status;
status = batch_store(b, 34, 109, 40, 436, 4);
if (status < 0) return status;
status = batch_store(b, 34, 124, 44, 496, 4);
if (status < 0) return status;
status = batch_store(b, 34, 180, 48, 720, 4);
if (status < 0) return status;
status = batch_store(b, 34, 151, 52, 604, 4);
if (status < 0) return status;
status = batch_store(b, 34, 232, 56, 928, 4);
if (status < 0) return status;
status = batch_store(b, 34, 214, 60, 856, 4);
if (status < 0) return status;
return 1; }
static int batch_step_35(Batch *b) {
int status;
memcpy(b->input+0, b->domains+140, 32);
memcpy(b->input+4, b->domains+716, 32);
if (batch_cached(b, 35, 8)) return 1;
++b->counts[1];
status = batch_inequality(b->plans[35], b->input, 254, 1, b->output);
if (status <= 0) return status;
memcpy(b->cache+3200, b->output, 64); b->cached[35] = 1;
status = batch_store(b, 35, 35, 0, 140, 4);
if (status < 0) return status;
status = batch_store(b, 35, 179, 4, 716, 4);
if (status < 0) return status;
return 1; }
static int batch_step_36(Batch *b) {
int status;
memcpy(b->input+0, b->domains+140, 32);
memcpy(b->input+4, b->domains+856, 32);
if (batch_cached(b, 36, 8)) return 1;
++b->counts[1];
status = batch_inequality(b->plans[36], b->input, 254, 1, b->output);
if (status <= 0) return status;
memcpy(b->cache+3208, b->output, 64); b->cached[36] = 1;
status = batch_store(b, 36, 35, 0, 140, 4);
if (status < 0) return status;
status = batch_store(b, 36, 214, 4, 856, 4);
if (status < 0) return status;
return 1; }
static int batch_step_37(Batch *b) {
int status;
memcpy(b->input+0, b->domains+140, 32);
memcpy(b->input+4, b->domains+348, 32);
if (batch_cached(b, 37, 8)) return 1;
++b->counts[1];
status = batch_inequality(b->plans[37], b->input, 254, 1, b->output);
if (status <= 0) return status;
memcpy(b->cache+3216, b->output, 64); b->cached[37] = 1;
status = batch_store(b, 37, 35, 0, 140, 4);
if (status < 0) return status;
status = batch_store(b, 37, 87, 4, 348, 4);
if (status < 0) return status;
return 1; }
static int batch_step_38(Batch *b) {
int status;
memcpy(b->input+0, b->domains+716, 32);
memcpy(b->input+4, b->domains+856, 32);
if (batch_cached(b, 38, 8)) return 1;
++b->counts[1];
status = batch_inequality(b->plans[38], b->input, 254, 1, b->output);
if (status <= 0) return status;
memcpy(b->cache+3224, b->output, 64); b->cached[38] = 1;
status = batch_store(b, 38, 179, 0, 716, 4);
if (status < 0) return status;
status = batch_store(b, 38, 214, 4, 856, 4);
if (status < 0) return status;
return 1; }
static int batch_step_39(Batch *b) {
int status;
memcpy(b->input+0, b->domains+140, 32);
if (batch_cached(b, 39, 4)) return 1;
++b->counts[1];
status = batch_inequality(b->plans[39], b->input, 127, 1, b->output);
if (status <= 0) return status;
memcpy(b->cache+3232, b->output, 32); b->cached[39] = 1;
status = batch_store(b, 39, 35, 0, 140, 4);
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
case 21: return batch_step_21(b);
case 22: return batch_step_22(b);
case 23: return batch_step_23(b);
case 24: return batch_step_24(b);
case 25: return batch_step_25(b);
case 26: return batch_step_26(b);
case 27: return batch_step_27(b);
case 28: return batch_step_28(b);
case 29: return batch_step_29(b);
case 30: return batch_step_30(b);
case 31: return batch_step_31(b);
case 32: return batch_step_32(b);
case 33: return batch_step_33(b);
case 34: return batch_step_34(b);
case 35: return batch_step_35(b);
case 36: return batch_step_36(b);
case 37: return batch_step_37(b);
case 38: return batch_step_38(b);
case 39: return batch_step_39(b);
default: return -1; } }