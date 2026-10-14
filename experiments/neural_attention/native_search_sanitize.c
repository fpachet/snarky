/* Standalone independent enumeration oracle, including workspace reuse. */
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <stdio.h>
#include "sum_support.c"
#include "alldiff_support.c"
#include "model_batch_runtime.c"
#include "native_search.c"

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
    puts("Native DFS: 8192 exhaustive domain/policy cases; reuse and cutoffs checked");
    return 0;
}
