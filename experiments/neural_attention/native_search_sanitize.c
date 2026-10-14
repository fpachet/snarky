/* Standalone independent enumeration oracle, including workspace reuse. */
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <stdio.h>
#include "sum_support.c"
#include "alldiff_support.c"
#include "model_batch_runtime.c"
#include "native_search.c"

/* Cross the old 262144-entry allocation guard (23x23 global ALLDIFF). */
static void check_large_capacity(void) {
    const int n = 529, words = (n+63)/64;
    int *starts = calloc((size_t)n+1, sizeof(int));
    int *positions = calloc((size_t)n*n, sizeof(int));
    int *lengths = calloc((size_t)n, sizeof(int));
    int *variables = calloc((size_t)n, sizeof(int));
    int *solutions = calloc((size_t)n, sizeof(int));
    uint64_t *input = calloc((size_t)n*words, sizeof(uint64_t)), stats[10];
    assert(starts && positions && lengths && variables && solutions && input);
    for (int i = 0; i < n; ++i) {
        starts[i+1] = (i+1)*n; lengths[i] = n; variables[i] = i;
        for (int j = 0; j < n; ++j) positions[i*n+j] = j;
        for (int w = 0; w < words; ++w) input[i*words+w] = UINT64_MAX;
        input[(i+1)*words-1] = (UINT64_C(1) << (n&63))-1;
    }
    int rows[] = {0,n}, kinds[] = {0}, ops[] = {0}, targets[] = {0};
    void *plans[] = {alldiff_create(n,n,starts,positions)};
    assert(plans[0]);
    Batch *b = batch_create(n,1,lengths,rows,variables,kinds,ops,targets,plans);
    assert(b);
    assert(native_search(b,input,1,1,1,30,solutions,1,stats) == 2);
    memset(input, 0, (size_t)n*words*sizeof(uint64_t));
    for (int i = 0; i < n; ++i) input[i*words+(i>>6)] = UINT64_C(1) << (i&63);
    assert(native_search(b,input,1,0,1,30,solutions,1,stats) == 1);
    for (int i = 0; i < n; ++i) assert(solutions[i] == i);
    input[words] = 1; /* x0 == x1, contradiction. */
    assert(native_search(b,input,1,0,1,30,solutions,1,stats) == 0);
    input[words] = 2;
    assert(native_search(b,input,1,0,1,30,solutions,1,stats) == 1);
    batch_free(b);
    free(starts); free(positions); free(lengths); free(variables);
    free(solutions); free(input);
}

int main(void) {
    const int starts[] = {0,4,8,12}, values[] = {0,2,3,5, 0,2,3,5, 0,2,3,5};
    const int positions[] = {0,1,2,3, 0,1,2,3, 0,1,2,3};
    const int lengths[] = {4,4,4}, rows[] = {0,3,6}, variables[] = {0,1,2,0,1,2};
    const int kinds[] = {0,1}, ops[] = {0,0}, targets[] = {0,7};
    void *plans[] = {alldiff_create(3,4,starts,positions),sum_create(3,starts,values)};
    assert(plans[0] && plans[1]);
    Batch *b = batch_create(3,2,lengths,rows,variables,kinds,ops,targets,plans);
    assert(b);
    for (int a = 0; a < 16; ++a) for (int c = 0; c < 16; ++c) for (int d = 0; d < 16; ++d) {
        uint64_t input[] = {(uint64_t)a,(uint64_t)c,(uint64_t)d}, stats[10];
        int solutions[192], expected = 0, seen[64] = {0};
        for (int i = 0; i < 4; ++i) for (int j = 0; j < 4; ++j) for (int k = 0; k < 4; ++k)
            if ((a&(1<<i)) && (c&(1<<j)) && (d&(1<<k)) && i != j && i != k && j != k &&
                values[i]+values[j]+values[k] == 7) { seen[16*i+4*j+k] = 1; ++expected; }
        for (int policy = 0; policy < 2; ++policy) {
            assert(native_search(b,input,policy,0,0,10,solutions,64,stats) == 0);
            assert(stats[6] == (uint64_t)expected);
            int actual[64] = {0};
            for (int i = 0; i < expected; ++i) {
                int x = solutions[3*i], y = solutions[3*i+1], z = solutions[3*i+2];
                assert(x >= 0 && x < 4 && y >= 0 && y < 4 && z >= 0 && z < 4);
                int at = 16*x+4*y+z; assert(seen[at] && !actual[at]); actual[at] = 1;
            }
        }
    }
    uint64_t input[] = {15,15,15}, stats[10]; int solutions[3];
    assert(native_search(b,input,0,0,1,0,solutions,1,stats) == 3);
    assert(native_search(b,input,0,1,0,10,solutions,1,stats) == 2);
    assert(native_search(b,input,0,0,1,10,solutions,1,stats) == 1);
    batch_free(b);
    check_large_capacity();
    puts("Native DFS: 8192 exhaustive domain/policy cases; reuse and cutoffs checked");
    puts("Large capacity: 529-variable ALLDIFF, 279841 entries; cutoff, solution and contradiction checked");
    return 0;
}
