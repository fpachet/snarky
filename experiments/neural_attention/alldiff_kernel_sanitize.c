/* Standalone ASan/UBSan check with an independent exhaustive assignment oracle. */
#include <assert.h>
#include <stdio.h>
#include "alldiff_support.c"

static uint32_t state = 141026;
static uint32_t random_value(void) {
    state ^= state << 13; state ^= state >> 17; state ^= state << 5;
    return state;
}

static void enumerate(int i, int n, const int *starts, const int *positions,
                      const uint64_t *input, uint64_t used, int *chosen,
                      uint64_t *expected, int *found) {
    if (i == n) {
        *found = 1;
        for (int j = 0; j < n; ++j) expected[j] |= UINT64_C(1) << chosen[j];
        return;
    }
    for (int j = 0; j < starts[i+1]-starts[i]; ++j) {
        int v = positions[starts[i]+j];
        if ((input[i] & (UINT64_C(1) << j)) && !(used & (UINT64_C(1) << v))) {
            chosen[i] = j;
            enumerate(i+1, n, starts, positions, input, used | (UINT64_C(1) << v),
                      chosen, expected, found);
        }
    }
}

int main(void) {
    int cases = 0;
    for (int trial = 0; trial < 1000; ++trial) {
        int n = 1+(int)(random_value()%6), count = 2+(int)(random_value()%8);
        int starts[7] = {0}, positions[24];
        for (int i = 0; i < n; ++i) {
            int length = 1+(int)(random_value()%(count < 4 ? count : 4));
            uint64_t used = 0;
            for (int j = 0; j < length; ++j) {
                int v;
                do { v = (int)(random_value()%(unsigned)count); } while (HAS(&used, v));
                SET(&used, v); positions[starts[i]+j] = v;
            }
            starts[i+1] = starts[i]+length;
        }
        void *handle = alldiff_create(n, count, starts, positions);
        assert(handle);
        for (int step = 0; step < 24; ++step) {
            uint64_t input[6], output[6], expected[6] = {0};
            int chosen[6], found = 0;
            for (int i = 0; i < n; ++i) {
                uint64_t full = (UINT64_C(1) << (starts[i+1]-starts[i]))-1;
                input[i] = step%3 == 0 ? full : random_value() & full;
            }
            enumerate(0, n, starts, positions, input, 0, chosen, expected, &found);
            int status = alldiff_supports(handle, input, output);
            assert(status == found);
            if (found) assert(memcmp(output, expected, (size_t)n*sizeof(uint64_t)) == 0);
            ++cases;
        }
        alldiff_free(handle);
    }
    /* Large immutable alphabets with candidates at every machine-word boundary. */
    int count = 2048, starts[4] = {0, 2048, 4096, 6144};
    int *positions = malloc(6144*sizeof(int));
    assert(positions);
    for (int i = 0; i < 6144; ++i) positions[i] = i%2048;
    void *handle = alldiff_create(3, count, starts, positions);
    assert(handle);
    for (int v = 0; v < count; ++v) {
        uint64_t input[96] = {0}, output[96];
        SET(input, v); SET(input+32, (v+1)%count); SET(input+64, (v+2)%count);
        assert(alldiff_supports(handle, input, output) == 1);
        assert(memcmp(input, output, sizeof(input)) == 0);
        ++cases;
    }
    alldiff_free(handle); free(positions);
    int bad_starts[2] = {0, 2}, duplicate[2] = {0, 0};
    assert(!alldiff_create(1, 2, bad_starts, duplicate));
    printf("Independent exhaustive/word-boundary cases: %d\n", cases);
    return 0;
}
