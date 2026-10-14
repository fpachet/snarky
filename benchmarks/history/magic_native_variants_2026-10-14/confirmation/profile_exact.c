#define _POSIX_C_SOURCE 200809L
#define PROFILE_NATIVE 1
#define LINEAR_MODE 0

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
    double profile_seconds[3];
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
    struct timespec profile_start, profile_end;
    clock_gettime(CLOCK_MONOTONIC, &profile_start);
    int status;
    if (b->kind[c] == 0) status = alldiff_supports(b->plans[c], b->input, b->output);
    else if (b->ops[c] == 0) {
        if (b->targets[c] < 0 || b->targets[c] > MAX_SPAN) status = 0;
        else status = sum_supports(b->plans[c], b->input, b->targets[c], b->output);
    } else status = batch_inequality(b->plans[c], b->input, b->targets[c], b->ops[c], b->output);
    clock_gettime(CLOCK_MONOTONIC, &profile_end);
    b->profile_seconds[b->kind[c]] += (double)(profile_end.tv_sec-profile_start.tv_sec)+(double)(profile_end.tv_nsec-profile_start.tv_nsec)*1e-9;
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

const char *batch_model_key(void) { return ""; }
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
    double profile_before = search_time();
    status = batch_run(b, domains, output, first, NULL, 0, counts, INT_MAX, remaining);
    b->profile_seconds[2] += search_time()-profile_before;
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

void native_profile(void *handle, double *out) {
    Batch *b = handle;
    memcpy(out, b->profile_seconds, 3*sizeof(double));
}
