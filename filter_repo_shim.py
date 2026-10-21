#!/usr/bin/env python3
"""Pinned shim around git-filter-repo for incremental (--state-branch) runs.

WHY THIS EXISTS (ADR-0001 Iteration 9, 2026-10-21): upstream git-filter-repo
2.47.0 crashes on --state-branch incremental runs whenever the new delta
contains a pruned commit (for this Action: any record-only commit, the most
common push class in a deliberating repo):

    TypeError: %b requires a bytes-like object, ... not 'int'  (_record_metadata)

Mechanism, named by probe: RepoFilter._remap_to resolves a pruned commit to
its first unpruned ancestor via self._graph.git_hash[new_id] — and when that
ancestor's rewrite was made by a PREVIOUS run, the graph knows it only by its
imported fast-import MARK (an int), which then reaches the commit-map /
ref-map / first-changed-commits writers and detonates b'%s' formatting.
Reproduces with stock git-filter-repo on a 4-commit toy repo, two runs, no
engine code involved (tests/integration/upstream-repro.sh).

THE PATCH is additive and minimal: wrap _remap_to (metadata-only — all call
sites live in _compute_metadata) and translate an int result through
fast-import's own marks mapping (target-marks in results_tmp_dir), which maps
every prior-run mark to the real rewritten hash. A mark with no hash means an
object this run never materialized: writing state that references it would
poison the NEXT sync, so the shim refuses loudly instead (fail closed).

Invocation (mirror.py): python3 filter_repo_shim.py <git-filter-repo args>.
The upstream module is used byte-pristine: installed module if importable
(CI pip-installs git-filter-repo==2.47.0), else the PATH script loaded as a
module — auditable as "stock filter-repo plus this visible wrapper".
"""
from __future__ import annotations

import os
import sys


def _load_upstream():
    try:
        import git_filter_repo as gfr  # the pip distribution's module
        return gfr
    except ImportError:
        pass
    import importlib.util
    import shutil
    from importlib.machinery import SourceFileLoader

    script = shutil.which("git-filter-repo")
    if not script:
        sys.exit(
            "no-adrs-mirror filter-repo shim: git-filter-repo is not installed "
            "(no importable module, nothing on PATH). history=filter needs it: "
            "pip install git-filter-repo==2.47.0"
        )
    # The script file IS the module (upstream ships one file); the loader needs
    # to be explicit because the script has no .py extension. __name__ stays
    # 'git_filter_repo', so its __main__ guard does not fire here.
    loader = SourceFileLoader("git_filter_repo", script)
    spec = importlib.util.spec_from_loader("git_filter_repo", loader)
    gfr = importlib.util.module_from_spec(spec)
    sys.modules["git_filter_repo"] = gfr
    loader.exec_module(gfr)
    return gfr


def _mark_to_hash(repo_filter, mark: int) -> bytes:
    cache = getattr(repo_filter, "_noadrs_mark_to_hash", None)
    if cache is None:
        cache = {}
        marks_path = os.path.join(repo_filter.results_tmp_dir(), b"target-marks")
        try:
            with open(marks_path, "rb") as fh:
                for line in fh:
                    parts = line.split()
                    if len(parts) == 2 and parts[0].startswith(b":"):
                        cache[int(parts[0][1:])] = parts[1]
        except OSError:
            pass  # empty cache -> the KeyError teaching below names the mark
        repo_filter._noadrs_mark_to_hash = cache
    try:
        return cache[mark]
    except KeyError:
        sys.exit(
            "no-adrs-mirror filter-repo shim: metadata references mark %d but "
            "target-marks has no hash for it — a rewritten object this run "
            "never materialized. Refusing to persist state that references it "
            "(it would break the NEXT sync). If this repeats, declare a "
            'rebuild with history_epoch: "new" and report it at '
            "https://github.com/ADRs4AI/no-adrs-mirror/issues." % mark
        )


def main() -> None:
    gfr = _load_upstream()
    original_remap_to = gfr.RepoFilter._remap_to

    def patched_remap_to(self, oldish_hash):
        new_hash = original_remap_to(self, oldish_hash)
        if isinstance(new_hash, int):
            new_hash = _mark_to_hash(self, new_hash)
        return new_hash

    gfr.RepoFilter._remap_to = patched_remap_to
    sys.argv = ["git-filter-repo"] + sys.argv[1:]
    gfr.main()


if __name__ == "__main__":
    main()
