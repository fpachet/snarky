#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
TARGET_ROOT="$PROJECT_ROOT/third_party/test_rulebases"

if [ -e "$TARGET_ROOT" ]; then
    echo "Refusing to overwrite existing directory: $TARGET_ROOT" >&2
    exit 1
fi

SCRATCH_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/boojum-rulebases.XXXXXX")
cleanup() {
    rm -rf "$SCRATCH_ROOT"
}
trap cleanup EXIT HUP INT TERM

mkdir -p "$TARGET_ROOT"

clone_sparse() {
    name=$1
    url=$2
    revision=$3
    shift 3
    checkout="$SCRATCH_ROOT/$name"
    git clone --filter=blob:none --no-checkout "$url" "$checkout"
    git -C "$checkout" sparse-checkout init --cone
    git -C "$checkout" sparse-checkout set "$@"
    git -C "$checkout" checkout --detach "$revision"
}

clone_sparse n3 https://github.com/w3c/N3.git \
    b975fc59ab5d2ad2d28e7206f1c34c716977d2ad tests
mkdir -p "$TARGET_ROOT/n3-w3c/tests"
rsync -a --exclude .git --exclude N3Tests/01etc/ \
    "$SCRATCH_ROOT/n3/tests/" "$TARGET_ROOT/n3-w3c/tests/"
cp "$SCRATCH_ROOT/n3/README.md" "$TARGET_ROOT/n3-w3c/README.upstream.md"

clone_sparse chasebench https://github.com/dbunibas/chasebench.git \
    7427e1c1e3196769ee4ea04557465965ec26d02b \
    scenarios/correctness scenarios/deep
mkdir -p "$TARGET_ROOT/chasebench/scenarios"
cp -R "$SCRATCH_ROOT/chasebench/scenarios/correctness" \
    "$TARGET_ROOT/chasebench/scenarios/"
cp -R "$SCRATCH_ROOT/chasebench/scenarios/deep" \
    "$TARGET_ROOT/chasebench/scenarios/"
cp "$SCRATCH_ROOT/chasebench/README.md" \
    "$TARGET_ROOT/chasebench/README.upstream.md"

clone_sparse souffle https://github.com/souffle-lang/souffle.git \
    a1303be3c0166400dee3d1f36f0d96abe03e6901 \
    tests/evaluation tests/semantic tests/provenance tests/scheduler \
    tests/syntactic licenses
mkdir -p "$TARGET_ROOT/souffle/tests"
cp -R "$SCRATCH_ROOT/souffle/tests/evaluation" \
    "$SCRATCH_ROOT/souffle/tests/semantic" \
    "$SCRATCH_ROOT/souffle/tests/provenance" \
    "$SCRATCH_ROOT/souffle/tests/scheduler" \
    "$SCRATCH_ROOT/souffle/tests/syntactic" \
    "$TARGET_ROOT/souffle/tests/"
cp -R "$SCRATCH_ROOT/souffle/licenses" "$TARGET_ROOT/souffle/"
cp "$SCRATCH_ROOT/souffle/LICENSE" "$SCRATCH_ROOT/souffle/README.md" \
    "$TARGET_ROOT/souffle/"

clone_sparse eye https://github.com/josd/eye.git \
    f14729b5bd1c6f25b54ab6490d6c17639f7353cf \
    reasoning/bnode-scope reasoning/deep-taxonomy reasoning/derived-rule \
    reasoning/meta-interpretation reasoning/n3-star reasoning/path \
    reasoning/reif reasoning/socrates reasoning/universal reasoning/zebra
mkdir -p "$TARGET_ROOT/eye/reasoning"
for case_name in bnode-scope deep-taxonomy derived-rule meta-interpretation \
    n3-star path reif socrates universal zebra
do
    cp -R "$SCRATCH_ROOT/eye/reasoning/$case_name" \
        "$TARGET_ROOT/eye/reasoning/"
done
cp "$SCRATCH_ROOT/eye/LICENSE" "$SCRATCH_ROOT/eye/README.md" \
    "$TARGET_ROOT/eye/"

clone_sparse rbench \
    https://gitlab.informatik.uni-halle.de/brass/rbench.git \
    1dda8ded0c43ecddee9bdb73430784e2f898b3c5 \
    xsb xsb_pure souffle join1_data graph_data sg_size
mkdir -p "$TARGET_ROOT/rbench"
cp -R "$SCRATCH_ROOT/rbench/xsb" "$SCRATCH_ROOT/rbench/xsb_pure" \
    "$SCRATCH_ROOT/rbench/souffle" "$SCRATCH_ROOT/rbench/join1_data" \
    "$SCRATCH_ROOT/rbench/graph_data" "$SCRATCH_ROOT/rbench/sg_size" \
    "$TARGET_ROOT/rbench/"
cp "$SCRATCH_ROOT/rbench/README.md" \
    "$TARGET_ROOT/rbench/README.upstream.md"

download() {
    url=$1
    output=$2
    expected=$3
    curl -L --fail --max-time 120 -o "$output" "$url"
    actual=$(shasum -a 256 "$output" | awk '{print $1}')
    if [ "$actual" != "$expected" ]; then
        echo "Checksum mismatch for $output" >&2
        exit 1
    fi
}

download \
    https://sourceforge.net/projects/clipsrules/files/CLIPS/6.4.2/clips_examples_642.zip/download \
    "$SCRATCH_ROOT/clips_examples_642.zip" \
    63c989b0e607604ace7c0c4a85396b8da91ade2797780bd14eeec5918479f6fc
download \
    https://sourceforge.net/projects/clipsrules/files/CLIPS/6.4.2/clips_feature_tests_642.zip/download \
    "$SCRATCH_ROOT/clips_feature_tests_642.zip" \
    c43b735f5c29f42cc4ce0aa1079972efb22829bef34f6f5ba7fe96c0035748f4
mkdir -p "$TARGET_ROOT/clips-6.4.2"
unzip -q "$SCRATCH_ROOT/clips_examples_642.zip" \
    -d "$TARGET_ROOT/clips-6.4.2"
unzip -q "$SCRATCH_ROOT/clips_feature_tests_642.zip" \
    -d "$TARGET_ROOT/clips-6.4.2"

mkdir -p "$TARGET_ROOT/rif-1.22/BLD" "$TARGET_ROOT/rif-1.22/Core" \
    "$TARGET_ROOT/rif-1.22/PRD"
download https://www.w3.org/2005/rules/test/repository/zips/BLD_v1.22.zip \
    "$SCRATCH_ROOT/BLD_v1.22.zip" \
    d32541d91ef612e7dbf145a03bea386273d974500eef926c41f21d3062841721
download https://www.w3.org/2005/rules/test/repository/zips/Core_v1.22.zip \
    "$SCRATCH_ROOT/Core_v1.22.zip" \
    421e80f2e2671e4ee95bf0f9c424d0fd83955f5cecf67fb9104422eeb9f3887a
download https://www.w3.org/2005/rules/test/repository/zips/PRD_v1.22.zip \
    "$SCRATCH_ROOT/PRD_v1.22.zip" \
    16fe5437b06ff6492c60b5c41588745a7870311347ca1f1d85f8876cb41c5e36
unzip -q "$SCRATCH_ROOT/BLD_v1.22.zip" -d "$TARGET_ROOT/rif-1.22/BLD"
unzip -q "$SCRATCH_ROOT/Core_v1.22.zip" -d "$TARGET_ROOT/rif-1.22/Core"
unzip -q "$SCRATCH_ROOT/PRD_v1.22.zip" -d "$TARGET_ROOT/rif-1.22/PRD"

echo "Rule-base corpora downloaded to $TARGET_ROOT"
