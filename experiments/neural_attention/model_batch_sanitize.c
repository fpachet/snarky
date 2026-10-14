/* Independent bounded assignment oracle for the generic fixpoint executor. */
#include <assert.h>
#include <stdio.h>
#include "sum_support.c"
#include "alldiff_support.c"
#include "model_batch_runtime.c"

static uint32_t rng = 141026;
static uint32_t random_mask(void) {
    rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5;
    return rng & 15;
}

int main(void) {
    const int starts[] = {0,4,8,12};
    const int values[] = {0,2,3,5, 0,2,3,5, 0,2,3,5};
    const int positions[] = {0,1,2,3, 0,1,2,3, 0,1,2,3};
    const int lengths[] = {4,4,4}, rows[] = {0,3,6}, variables[] = {0,1,2,0,1,2};
    const int kinds[] = {0,1}, ops[] = {0,0}, targets[] = {0,7};
    void *plans[2] = {alldiff_create(3,4,starts,positions),sum_create(3,starts,values)};
    assert(plans[0] && plans[1]);
    Batch *b = batch_create(3,2,lengths,rows,variables,kinds,ops,targets,plans);
    assert(b);
    for (int trial = 0; trial < 12000; ++trial) {
        uint64_t input[] = {random_mask(),random_mask(),random_mask()}, output[3], counts[6], log[36];
        if (trial%4 == 0) input[0] = input[1] = input[2] = 15;
        int status = batch_run(b,input,output,trial%2,log,12,counts,1000,-1);
        assert(status >= 0);
        for (int a = 0; a < 4; ++a) for (int c = 0; c < 4; ++c) for (int d = 0; d < 4; ++d) {
            if (!(input[0] & (UINT64_C(1)<<a)) || !(input[1] & (UINT64_C(1)<<c)) ||
                !(input[2] & (UINT64_C(1)<<d))) continue;
            if (a == c || a == d || c == d || values[a]+values[c]+values[d] != 7) continue;
            assert(status > 0);
            assert((output[0] & (UINT64_C(1)<<a)) && (output[1] & (UINT64_C(1)<<c)) &&
                   (output[2] & (UINT64_C(1)<<d)));
        }
        if (status > 0) {
            assert(output[0] && output[1] && output[2]);
            for (int i = 0; i < 3; ++i) assert(!(output[i] & ~input[i]));
        }
    }
    uint64_t input[] = {15,15,15}, output[3], counts[6];
    assert(batch_run(b,input,output,1,NULL,0,counts,1000,0) == -4);
    batch_free(b);
    puts("Native fixpoint oracle cases: 12000; timeout status checked");
    return 0;
}
