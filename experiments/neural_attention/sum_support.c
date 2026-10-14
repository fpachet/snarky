/* Experimental exact equality supports. Immutable normalized contributions;
   caller-owned domains/trail. One private scratch workspace per numeric plan. */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define MAX_N 64
#define MAX_SPAN 16384
#define MAX_WORDS (MAX_SPAN / 64 + 1)
#define MAX_COLUMN 4096
#define MAX_ENTRIES 1048576

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
