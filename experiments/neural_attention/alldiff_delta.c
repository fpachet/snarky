/* Reconcile the residual graph from actual masks and validated matching.
 * Every changed arc updates its transpose immediately. This is safe after
 * failed matching repair and domain widening too. SCC/reachability remain
 * full recomputations; no cached connectivity or support witness is trusted.
 */
static void alldiff_delta_graph(AllDiff *p) {
    int w = p->words;
    memset(p->occupied, 0, (size_t)w*sizeof(uint64_t));
    memset(p->allowed, 0, (size_t)w*sizeof(uint64_t));
    for (int v = 0; v < p->count; ++v) {
        int owner = p->owners[v];
        const uint64_t *row = owner >= 0 ? p->masks+owner*w : NULL;
        if (owner >= 0) {
            SET(p->occupied, v);
            if (p->sizes[owner] == 1) SET(p->allowed, v);
        }
        for (int k = 0; k < w; ++k) {
            uint64_t desired = row ? row[k] : 0;
            uint64_t changed = p->graph[v*w+k] ^ desired;
            while (changed) {
                int destination = 64*k+__builtin_ctzll(changed); changed &= changed-1;
                uint64_t *reverse = p->reverse+destination*w+(v>>6);
                if (desired & BIT(destination)) *reverse |= BIT(v);
                else *reverse &= ~BIT(v);
            }
            p->graph[v*w+k] = desired;
        }
    }
}
