"""Experimental native propagation alternatives; historical sources stay intact."""

from pathlib import Path

from .model_batch import HERE, source
from .native_search import SearchKernel


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("native experiment source seam changed")
    return text.replace(old, new, 1)


def delta_alldiff(generated):
    text = (HERE / "alldiff_support.c").read_text()
    modified = replace_once(
        text,
        "    uint64_t *masks, *graph,",
        "    uint64_t *previous_local;\n    uint64_t *masks, *graph,",
    )
    modified = replace_once(
        modified,
        "    free(p->masks);",
        "    free(p->previous_local);\n    free(p->masks);",
    )
    modified = replace_once(
        modified,
        "    p->local_words = p->offsets[n];",
        "    p->local_words = p->offsets[n];\n"
        "    p->previous_local = calloc((size_t)p->local_words, sizeof(uint64_t));\n"
        "    if (!p->previous_local) { alldiff_free(p); return NULL; }",
    )
    modified = replace_once(
        modified, "    memset(p->masks, 0, (size_t)p->n*w*sizeof(uint64_t));\n", ""
    )
    old = """            else while (bits) {
                int j = 64*k+__builtin_ctzll(bits); bits &= bits-1;
                SET(row, p->positions[p->starts[i]+j]);
            }"""
    new = """            else {
                uint64_t changed = bits ^ p->previous_local[p->offsets[i]+k];
                while (changed) {
                    int j = 64*k+__builtin_ctzll(changed); changed &= changed-1;
                    int v = p->positions[p->starts[i]+j];
                    if (bits & BIT(j)) SET(row, v);
                    else row[v>>6] &= ~BIT(v);
                }
            }
            p->previous_local[p->offsets[i]+k] = bits;"""
    modified = replace_once(modified, old, new)
    begin = modified.index(
        "    memset(p->graph, 0,", modified.index("int alldiff_supports(")
    )
    end = modified.index("    reach_free(p);", begin)
    modified = modified[:begin] + "    alldiff_delta_graph(p);\n" + modified[end:]
    position = modified.index("/* 1 = exact supports, 0 = no matching")
    modified = (
        modified[:position]
        + (HERE / "alldiff_delta.c").read_text()
        + "\n"
        + modified[position:]
    )
    return replace_once(generated, text, modified)


def variant_source(mode, *, delta=False, shared=False, profile=False):
    if mode not in ("exact", "bounds", "staged", "budget"):
        raise ValueError("unknown SUM mode")
    generated = source()
    if mode != "exact":
        sums = (HERE / "sum_support.c").read_text()
        modified = replace_once(sums, "typedef struct {", "typedef struct Sum {")
        modified = replace_once(
            modified,
            "    int n, entries, words, stride;",
            "    struct LinearBounds *linear;\n    int n, entries, words, stride;",
        )
        modified = replace_once(
            modified,
            "    free(s->values);",
            "    linear_free(s->linear);\n    free(s->values);",
        )
        modified = replace_once(
            modified,
            "    return s;\n}",
            "    s->linear = linear_create(s);\n"
            "    if (!s->linear) { sum_free(s); return NULL; }\n"
            "    return s;\n}",
        )
        modified = (
            "struct Sum; struct LinearBounds;\n"
            "static struct LinearBounds *linear_create(struct Sum *);\n"
            "static void linear_free(struct LinearBounds *);\n" + modified
        )
        modified += "\n" + (HERE / "linear_bounds.c").read_text()
        generated = replace_once(generated, sums, modified)
        generated = replace_once(
            generated,
            "sum_supports(b->plans[c], b->input, b->targets[c], b->output)",
            "linear_filter(b->plans[c], b->input, b->targets[c], 0, b->output)",
        )
        generated = replace_once(
            generated,
            "batch_inequality(b->plans[c], b->input, b->targets[c], "
            "b->ops[c], b->output)",
            "linear_filter(b->plans[c], b->input, b->targets[c], b->ops[c], b->output)",
        )
        # A single bounds pass need not reach its own fixpoint. The batch
        # executor's output-tag cache assumes idempotent filtering, so certify
        # numeric cache entries only after a pass makes no reductions.
        generated = replace_once(
            generated,
            "b->cached[c] = 1;\n    for (int j = b->starts[c];",
            "b->cached[c] = b->kind[c] == 0 || "
            "((Sum *)b->plans[c])->linear->certified || "
            "memcmp(b->input, b->output, (size_t)words*sizeof(uint64_t)) == 0;\n"
            "    for (int j = b->starts[c];",
        )
        begin = generated.index(
            "#if !defined(MODEL_SPECIALIZED) || defined(MODEL_HAS_INEQUALITY)"
        )
        end = generated.index("#endif", begin) + len("#endif")
        generated = generated[:begin] + generated[end:]
    if delta:
        generated = delta_alldiff(generated)
    if shared:
        generated = replace_once(
            generated,
            "    int nv, nc, words, scope_entries, local_words, max_local_words;",
            "    int (*writer)(void *, int, uint64_t);\n    void *writer_state;\n"
            "    int nv, nc, words, scope_entries, local_words, max_local_words;",
        )
        generated = replace_once(
            generated,
            "        b->domains[offset+w] &= b->output[local+w];",
            "        uint64_t value = b->domains[offset+w] & b->output[local+w];\n"
            "        if (b->writer) {\n"
            "            if (!b->writer(b->writer_state, offset+w, value)) return -6;\n"
            "        } else b->domains[offset+w] = value;",
        )
    if profile:
        generated = replace_once(
            generated,
            "    uint64_t *log, counts[6];",
            "    double profile_seconds[3];\n    uint64_t *log, counts[6];",
        )
        generated = replace_once(
            generated,
            "    int status;\n    if (b->kind[c] == 0)",
            "    struct timespec profile_start, profile_end;\n"
            "    clock_gettime(CLOCK_MONOTONIC, &profile_start);\n"
            "    int status;\n    if (b->kind[c] == 0)",
        )
        generated = replace_once(
            generated,
            "    if (status <= 0) return status;\n    memcpy(b->cache",
            "    clock_gettime(CLOCK_MONOTONIC, &profile_end);\n"
            "    b->profile_seconds[b->kind[c]] += "
            "(double)(profile_end.tv_sec-profile_start.tv_sec)+"
            "(double)(profile_end.tv_nsec-profile_start.tv_nsec)*1e-9;\n"
            "    if (status <= 0) return status;\n    memcpy(b->cache",
        )
    search = (HERE / ("native_shared.c" if shared else "native_search.c")).read_text()
    if profile and not shared:
        search = replace_once(
            search,
            "    status = batch_run(b,",
            "    double profile_before = search_time();\n    status = batch_run(b,",
        )
        search = replace_once(
            search,
            "    first = 0;",
            "    b->profile_seconds[2] += search_time()-profile_before;\n"
            "    first = 0;",
        )
    if profile:
        search += (
            "\nvoid native_profile(void *handle, double *out) {\n"
            "    Batch *b = handle;\n"
            "    memcpy(out, b->profile_seconds, 3*sizeof(double));\n}\n"
        )
    return (
        "#define _POSIX_C_SOURCE 200809L\n"
        + ("#define PROFILE_NATIVE 1\n" if profile else "")
        + f"#define LINEAR_MODE {dict(exact=0, bounds=1, staged=2, budget=3)[mode]}\n"
        + generated
        + search
    )


class VariantKernel(SearchKernel):
    def __init__(self, library):
        import ctypes as ct

        super().__init__(library)
        if hasattr(self.library, "native_profile"):
            self._profile = self.library.native_profile
            self._profile.argtypes = [ct.c_void_p, ct.POINTER(ct.c_double)]
            self._profile.restype = None

            def metrics(handle):
                times = (ct.c_double * 3)()
                self._profile(handle, times)
                return dict(zip(("alldiff", "sum", "propagation"), times, strict=True))

            self.metrics = metrics

    @classmethod
    def build_variant(
        cls, output, mode, *, delta=False, shared=False, profile=False, cache_dir=None
    ):
        path = Path(output).with_suffix(".c")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            variant_source(mode, delta=delta, shared=shared, profile=profile)
        )
        return cls.build(
            output,
            source=path,
            cache_dir=cache_dir or "generated/neural_attention/native_variants_cache",
        )
