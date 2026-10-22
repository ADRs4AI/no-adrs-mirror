# Upstream issue draft — git-filter-repo: `--state-branch` incremental runs crash on pruned commits (`TypeError: %b requires a bytes-like object … not 'int'`)

- **Status**: FILED 2026-10-22 as
  [newren/git-filter-repo#775](https://github.com/newren/git-filter-repo/issues/775)
  — the founder's word in ADR-0001 `QST-UPSTREAM-FILE` (Option A, his hand).
- **Target**: https://github.com/newren/git-filter-repo/issues
- **Version**: 2.47.0 (pypi and Homebrew, `a40bce548d2c`); upstream HEAD as of
  2026-10-21 has no fix (newest script-touching commits: typos, signatures,
  gpgsig, LFS).
- **Found by**: the no-adrs-mirror Action's continuous incremental syncs
  (ADRs4AI/no-adrs-mirror, ADR-0001 Iterations 8–9); reduced to a pure
  filter-repo repro with no Action code involved.

## Proposed issue body

### Summary

On a second (or later) `--state-branch` run, if the new commits since the
previous run include any commit that gets pruned (`--prune-empty always`
with path filters that empty it), the run crashes while writing metadata:

```
  File ".../git-filter-repo", line 4802, in _record_metadata
    f.write(b'%s %s\n' % (commit, undeleted_self_or_ancestor))
TypeError: %b requires a bytes-like object, or an object that implements __bytes__, not 'int'
```

Depending on where the pruned commit sits in the delta, the crash fires in
the `ref-map` writer (line 4792, all new commits pruned), or the
`first-changed-commits` writer (line 4802, pruned commit anywhere in the
delta). The rewrite itself completes; only metadata/state writing dies, which
aborts the run after fast-import has already run.

### Mechanism

`RepoFilter._remap_to` resolves a pruned commit to its first unpruned
ancestor via `self._graph.git_hash[new_id]`. When that ancestor's rewrite was
produced by a **previous** run (its objects arrived through
`--import-marks`), the graph knows it only by its integer fast-import mark —
so `_remap_to` returns an `int`, which flows into `ref_maps` /
`first_changes` and detonates the `b'%s'` formatting in `_record_metadata`.
First runs never hit it (every rewrite is in this run's graph); any
incremental run whose delta contains a pruned commit does.

### Minimal reproduction (two runs, four commits, fresh clone each run)

Each run starts from a fresh clone of the original history plus the persisted
state branch — the shape any incremental pipeline has. (An earlier draft
reused run 1's rewritten clone and tried to `merge --ff-only` the new
upstream commit; after a rewrite those histories have diverged, so the merge
can only fail and a run with no new commit shows no bug — founder-caught,
2026-10-21.)

```sh
#!/bin/sh
set -e
W="$PWD/gfr-repro"; rm -rf "$W"; mkdir -p "$W/upstream"
cd "$W/upstream"
git init -q -b main .
git config user.name repro; git config user.email repro@invalid
mkdir -p docs src
echo "code1" > src/a.txt;  git add -A; git commit -q -m "feat: a"
echo "doc1"  > docs/x.md;  git add -A; git commit -q -m "docs: x"
echo "code2" > src/b.txt;  git add -A; git commit -q -m "feat: b"

# run 1: fresh clone, filter with persistent state
git clone -q --no-local . "$W/work1"
cd "$W/work1"
git filter-repo --force --invert-paths --path docs --prune-empty always --state-branch sb
echo "=== run 1 OK ==="

# a new record-only commit lands upstream
cd "$W/upstream"
echo "doc2" > docs/y.md; git add -A; git commit -q -m "docs: y"

# run 2: fresh clone of the ORIGINAL history + run 1's state + run 1's
# rewritten objects (in a real pipeline, fetched from wherever run 1's
# result was pushed; a non-heads ref keeps them out of the rewrite)
git clone -q --no-local . "$W/work2"
cd "$W/work2"
git fetch -q "$W/work1" sb:sb
git fetch -q "$W/work1" main:refs/mirror/prior
git filter-repo --force --invert-paths --path docs --prune-empty always --state-branch sb
echo "=== run 2 OK (bug absent) ==="
```

Run 2 crashes on 2.47.0 at the `ref-map` writer (line 4792 — the delta's
only commit is pruned, so `refs/heads/main` maps to an int mark). With a kept
commit after the pruned one in the delta, the same int reaches the
`first-changed-commits` writer (line 4802) instead.

### Suggested fix

Translate integer marks through the run's `target-marks` mapping (which maps
every imported mark to its real hash) before metadata formatting — e.g. in
`_remap_to`, or at the three `_record_metadata` write sites. We carry exactly
that as a local wrapper
(ADRs4AI/no-adrs-mirror `filter_repo_shim.py`: wrap `_remap_to`, resolve
`int` results via `results_tmp_dir()/target-marks`, fail loudly if a mark has
no hash) and it restores correct, byte-stable metadata in all three shapes.
Happy to turn it into a PR if useful.
