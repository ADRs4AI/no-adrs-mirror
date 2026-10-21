#!/usr/bin/env python3
"""Live integration test: the two-phase engine against REAL GitHub repos.

Needs (never committed — env only):
  INTEGRATION_TOKEN   a token able to push Contents+Workflows to BOTH repos
  INT_SRC_REPO        owner/repo — a dedicated TEST source (history gets reset!)
  INT_MIRROR_REPO     owner/repo — the test mirror (history gets reset!)

What it proves, end to end on the hosted platform:
  1. Phase A: fixture history -> filter build -> force-push epoch.
  2. Phase B: new source commit -> incremental build (state branch round-trips
     through the hosted source) -> fast-forward push with NO force; every
     phase-A mirror SHA still reachable from the new tip.
  3. The fail-closed teaching path: state present + unreachable mirror raises.

Run: INTEGRATION_TOKEN=... INT_SRC_REPO=o/r INT_MIRROR_REPO=o/r2 python3 tests/integration/run.py
Both repos are DEDICATED test fixtures; this script force-resets them.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HERE))
import mirror  # noqa: E402


def sh(args, cwd=None, **kw):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True, **kw)


def main() -> int:
    token = os.environ["INTEGRATION_TOKEN"]
    src_slug = os.environ["INT_SRC_REPO"]
    mir_slug = os.environ["INT_MIRROR_REPO"]
    auth = f"https://x-access-token:{token}@github.com/"
    work = pathlib.Path(tempfile.mkdtemp(prefix="noadrs-int-"))
    sh(["git", "config", "--global", f"url.{auth}.insteadOf", "https://github.com/"])
    try:
        # --- seed the source with a fixture history (reset) ---------------
        src = work / "src"
        sh(["git", "init", "-q", "-b", "main", str(src)])
        sh(["git", "config", "user.name", "integration"], src)
        sh(["git", "config", "user.email", "integration@invalid"], src)
        (src / "src").mkdir()
        (src / "src/app.py").write_text("A = 1\n")
        (src / "docs/adr").mkdir(parents=True)
        (src / "docs/adr/0001-pick.md").write_text("# ADR-0001: pick\nsecret reasoning\n")
        sh(["git", "add", "-A"], src)
        sh(["git", "commit", "-q", "-m", "feat: app + record"], src)
        (src / "src/b.py").write_text("B = 2\n")
        sh(["git", "add", "-A"], src)
        sh(["git", "commit", "-q", "-m", "feat: b"], src)
        sh(["git", "remote", "add", "origin", f"https://github.com/{src_slug}.git"], src)
        # reset BOTH test repos to a clean slate (dedicated fixtures by contract)
        sh(["git", "push", "-q", "--force", "origin", "main"], src)
        for ref in ("refs/heads/no-adrs-mirror/state",):
            subprocess.run(["git", "-C", str(src), "push", "-q", "origin", f"+:{ref}"],
                           capture_output=True)
        subprocess.run(["git", "-C", str(src), "push", "-q", "--force",
                        f"https://github.com/{mir_slug}.git", "+main:main"],
                       capture_output=True)  # best effort pre-clean; phase A force-pushes anyway

        def build_and_push(tag: str) -> dict:
            out = work / f"m-{tag}"
            cfg = mirror.BuildConfig(
                source=src, out=out, repo_slug=src_slug, history="filter",
                state_objects=f"https://github.com/{mir_slug}.git",
            )
            stats = mirror.build_filtered(cfg)
            mirror.write_notice(cfg, stats, None)
            mirror.commit_all(cfg, stats)
            mirror.push(out, mir_slug, create=False)
            # persist state to the HOSTED source (the action's persist step)
            sh(["git", "push", "-q", "origin",
                "+refs/heads/no-adrs-mirror/state:refs/heads/no-adrs-mirror/state"], src)
            return stats

        # --- phase A -------------------------------------------------------
        s1 = build_and_push("a")
        assert s1["phase"] == "epoch", s1
        lsA = sh(["git", "ls-remote", f"https://github.com/{mir_slug}.git", "main"]).stdout.split()[0]
        print(f"phase A ok: epoch pushed, mirror tip {lsA[:12]}")

        # --- phase B -------------------------------------------------------
        (src / "src/c.py").write_text("C = 3\n")
        sh(["git", "add", "-A"], src)
        sh(["git", "commit", "-q", "-m", "feat: c"], src)
        sh(["git", "push", "-q", "origin", "main"], src)
        # fresh working clone, as a new CI run would see the world
        src2 = work / "src2"
        sh(["git", "clone", "-q", f"https://github.com/{src_slug}.git", str(src2)])
        sh(["git", "-C", str(src2), "fetch", "-q", "origin",
            "+refs/heads/no-adrs-mirror/state:refs/heads/no-adrs-mirror/state"])
        out2 = work / "m-b"
        cfg2 = mirror.BuildConfig(
            source=src2, out=out2, repo_slug=src_slug, history="filter",
            state_objects=f"https://github.com/{mir_slug}.git",
        )
        s2 = mirror.build_filtered(cfg2)
        assert s2["phase"] == "incremental", s2
        mirror.write_notice(cfg2, s2, None)
        mirror.commit_all(cfg2, s2)
        mirror.push(out2, mir_slug, create=False)  # NO force: FF by construction
        probe = work / "probe"
        sh(["git", "clone", "-q", f"https://github.com/{mir_slug}.git", str(probe)])
        reach = sh(["git", "-C", str(probe), "merge-base", "--is-ancestor", lsA, "HEAD"])
        print("phase B ok: incremental, fast-forward, phase-A tip still reachable")
        print("INTEGRATION: ALL GREEN")
        return 0
    finally:
        subprocess.run(["git", "config", "--global", "--unset-all",
                        f"url.{auth}.insteadOf"], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
