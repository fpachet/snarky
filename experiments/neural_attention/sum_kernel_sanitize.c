/* Standalone randomized exhaustive oracle for ASan/UBSan validation. */
#include <stdio.h>
#include "sum_support.c"

static uint32_t seed = 141026;
static unsigned random_value(unsigned bound) {
    seed ^= seed << 13; seed ^= seed >> 17; seed ^= seed << 5;
    return seed % bound;
}

static int oracle_found;
static int selected[MAX_N];
static uint64_t expected[MAX_N * (MAX_COLUMN / 64)];

static void enumerate(const Sum *s, const uint64_t *masks, int depth, int total, int target) {
    if (depth == s->n) {
        if (total != target) return;
        oracle_found = 1;
        for (int i = 0; i < s->n; ++i) set_candidate(s, expected, i, selected[i]);
        return;
    }
    for (int w = s->masks[depth]; w < s->masks[depth + 1]; ++w) {
        uint64_t pending = masks[w];
        while (pending) {
            int p = 64 * (w - s->masks[depth]) + __builtin_ctzll(pending);
            pending &= pending - 1;
            selected[depth] = p;
            enumerate(s, masks, depth + 1, total + s->values[s->starts[depth] + p], target);
        }
    }
}

static void check(Sum *s, const uint64_t *masks, int target) {
    uint64_t actual[MAX_N * (MAX_COLUMN / 64)];
    oracle_found = 0;
    memset(expected, 0, sizeof(expected));
    enumerate(s, masks, 0, 0, target);
    int status = sum_supports(s, masks, target, actual);
    if (status < 0 || !!status != oracle_found ||
        (status && memcmp(actual, expected, s->words * sizeof(uint64_t)))) {
        fprintf(stderr, "support mismatch, seed=%u target=%d status=%d\n", seed, target, status);
        exit(1);
    }
}

int main(void) {
    for (int trial = 0; trial < 5000; ++trial) {
        int n = 1 + random_value(6), starts[MAX_N + 1] = {0}, values[MAX_N * 5];
        uint64_t masks[MAX_N];
        for (int i = 0; i < n; ++i) {
            int count = 1 + random_value(5);
            starts[i + 1] = starts[i] + count;
            values[starts[i]] = 0;
            for (int p = starts[i] + 1; p < starts[i + 1]; ++p) {
                int unique;
                do {
                    unique = 1; values[p] = 1 + random_value(256);
                    for (int q = starts[i]; q < p; ++q)
                        if (values[q] == values[p]) unique = 0;
                } while (!unique);
            }
            masks[i] = random_value(1 << count);
        }
        Sum *s = sum_create(n, starts, values);
        if (!s) return 2;
        check(s, masks, random_value(1600));
        check(s, masks, 0);
        sum_free(s);
    }
    int starts[] = {0, 4096, 8192, 12288};
    int *values = malloc(12288 * sizeof(int));
    uint64_t masks[192] = {0};
    for (int i = 0; i < 12288; ++i) values[i] = i % 4096;
    for (int i = 0; i < 3; ++i) {
        int positions[] = {0, 1, 63, 64, 127, 128, 4095};
        for (int j = 0; j < 7; ++j) masks[64 * i + positions[j] / 64] |= UINT64_C(1) << (positions[j] % 64);
    }
    Sum *s = sum_create(3, starts, values);
    if (!s) return 2;
    check(s, masks, 65); check(s, masks, 8190); check(s, masks, 12285);
    sum_free(s); free(values);
    int limits[] = {0, 2, 4, 6}, edges[] = {0, 8192, 0, 4096, 0, 4096};
    uint64_t full[] = {3, 3, 3};
    s = sum_create(3, limits, edges);
    if (!s) return 2;
    check(s, full, 8191); check(s, full, 8192); check(s, full, 16384);
    sum_free(s);
    puts("ASan/UBSan exhaustive support checks: 10006 cases passed");
    return 0;
}
