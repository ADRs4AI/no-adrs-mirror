#!/usr/bin/env python3
"""no-adrs-mirror — publish a repository's code without its deliberation record.

Prototype, 2026-08-26, Covenant 5 (Claude Fable 5) at Jérémie Lumbroso's ask
("prototype the GitHub Action for when I'm up"). Design context: HQ ADR-0034 §4
(Closed Deliberations mode) and its Iteration 2 (the digest mode).

What it does
  build   Produce a mirror working tree from a source repo:
            - strips a parameterized list of paths (default: the deliberation
              record — docs/adr, docs/inbox, docs/vignettes, docs/handoffs —
              plus the deliberative apparatus: CLAUDE.md, AGENTS.md, .claude,
              .pneumatic)
            - history mode `snapshot` (default): ONE commit, no history, no
              message leaks; `filter`: git filter-repo keeps code history minus
              the stripped paths, prunes commits that become empty (docs-only
              commits vanish WITH their messages — Jérémie's point), and can
              reduce the surviving messages to subject-only or scrub them
              (the residual leak is exactly the MIXED commits: code + record in
              one commit; `--report` counts them)
            - optional DIGEST: a model-written summary of each ADR (default
              model claude-sonnet-5, prompt in prompts/adr-digest.md, fully
              parameterizable) written to docs/deliberations-digest/, every
              file carrying the canonical Address of its source
              (adr://v1/repo/<owner>/<repo>/adr/<locator>) so the digest is
              a pointer to the record, not a substitute that loses citability
            - DELIBERATIONS-NOTICE.md: the honest badge — the record exists,
              how big it is, what was withheld, under what terms it's available
  push    Push the built tree to the mirror repository (creates it if asked).
  report  Print the mixed-commit count and the strip preview without building.

Runs with the standard library only; `anthropic` is imported lazily and only
when a digest is actually generated. Tested with tests/test_mirror.py.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import fnmatch
import hashlib
import json
import os
import re
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Protocol

__version__ = "0.4.0"

# Operator-facing narration goes through `log` (stderr; stdout stays the
# machine interface — the JSON result). On a GitHub runner, anything worth a
# human's glance ALSO lands in the job's Summary page via step_summary().
# Verbosity: NO_ADRS_LOG=debug|info|warning (default info).
log = logging.getLogger("no-adrs-mirror")
logging.basicConfig(
    stream=sys.stderr,
    level=getattr(logging, os.environ.get("NO_ADRS_LOG", "info").upper(), logging.INFO),
    format="%(levelname)s no-adrs-mirror: %(message)s",
)


def step_summary(markdown: str) -> None:
    """Append a Markdown block to $GITHUB_STEP_SUMMARY when running in
    Actions; a silent no-op elsewhere. Failures to write are logged, never
    fatal — the summary is a courtesy surface, the log is the record."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    try:
        with open(path, "a") as fh:
            fh.write(markdown.rstrip() + "\n\n")
    except OSError as exc:  # pragma: no cover - runner-environment specific
        log.warning("could not write GITHUB_STEP_SUMMARY (%s)", exc)

DEFAULT_STRIP = [
    "docs/adr",
    "docs/inbox",
    "docs/vignettes",
    "docs/handoffs",
    "docs/continuity",       # personal handoffs + compaction prompts (voice-laden by design)
    "docs/HANDOFF-*.md",     # the template's EMERGENCY handoff lands in docs/ root
    "CLAUDE.md",
    "AGENTS.md",
    ".claude",
    ".pneumatic",
    ".working",              # extension working substrate: drafts + error ledgers
    ".mcp.json",             # local MCP server config (machine paths, commands)
    # DELIBERATELY NOT STRIPPED: kintsugi.yaml + kintsugi.lock — the rights-holder,
    # 2026-10-19: "I'm not sure about the kintsugi.yaml and lock files, since that
    # role models our tooling." Visible pending his final word (ADR-0001 It-3).
]
DEFAULT_DIGEST_GLOB = "docs/adr/[0-9]*.md"
DEFAULT_DIGEST_MODEL = "claude-sonnet-5"
DEFAULT_DIGEST_EFFORT = "medium"
DIGEST_DIR = "docs/deliberations-digest"
NOTICE_FILE = "DELIBERATIONS-NOTICE.md"
# Two-phase history (the rights-holder's law, ADR-0002): the state branch —
# persisted in the PRIVATE source repo — lets git-filter-repo process only the
# commits since the last sync, so prior mirror SHAs stay stable and pushes are
# plain fast-forwards. Its absence (or a declared new epoch) is phase A.
STATE_BRANCH = "no-adrs-mirror/state"
PHASE_SUFFIX = ".phase"  # sibling marker next to the built tree: epoch | incremental
INDEX_FILE = "DELIBERATIONS-DIGEST.md"
HERE = Path(__file__).resolve().parent
DEFAULT_PROMPT_PATH = HERE / "prompts" / "adr-digest.md"


# --------------------------------------------------------------------------- git


def git(args: list[str], cwd: Path, check: bool = True) -> str:
    """Run a git command in `cwd` and return stdout; raises on failure when
    `check` (the default) so no git error can pass silently."""
    result = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed in {cwd}:\n{result.stderr}")
    return result.stdout


def tracked_files(source: Path) -> list[str]:
    out = git(["ls-files", "-z"], source)
    return [p for p in out.split("\0") if p]


def head_sha(source: Path) -> str:
    return git(["rev-parse", "HEAD"], source).strip()


# ------------------------------------------------------------------- strip rules


def normalize_patterns(patterns: Iterable[str]) -> list[str]:
    cleaned: list[str] = []
    for raw in patterns:
        p = raw.strip().strip("/")
        if not p or p.startswith("#"):
            continue
        cleaned.append(p)
    return cleaned


def is_stripped(path: str, patterns: list[str]) -> bool:
    """A path is stripped if it equals a pattern, lives under a pattern
    directory, or fnmatch-es a glob pattern."""
    for pat in patterns:
        if path == pat or path.startswith(pat + "/"):
            return True
        if any(ch in pat for ch in "*?[") and fnmatch.fnmatch(path, pat):
            return True
    return False


def partition(paths: Iterable[str], patterns: list[str]) -> tuple[list[str], list[str]]:
    """Split paths into (kept, stripped) under the withhold patterns — the
    single boundary function every mode shares, so 'what crosses' has exactly
    one implementation to audit."""
    kept, stripped = [], []
    for p in paths:
        (stripped if is_stripped(p, patterns) else kept).append(p)
    return kept, stripped


# ----------------------------------------------------------------- history math


def mixed_commit_count(source: Path, patterns: list[str]) -> tuple[int, int, int]:
    """Count (mixed, record-only, code-only) commits in the source. Mixed
    commits are filter mode's residual message-leak surface; `report` prints
    these so the history-mode choice is measured, never assumed."""
    """(mixed, record_only, code_only) over the source's full history.

    Mixed commits are the residual leak of `filter` mode: their messages
    survive because they still touch kept paths. Record-only commits vanish
    entirely (with their messages) under --prune-empty=always."""
    log = git(["log", "--format=%x00%H", "--name-only"], source)
    mixed = record_only = code_only = 0
    for chunk in log.split("\0"):
        lines = [l for l in chunk.splitlines() if l.strip()]
        if not lines:
            continue
        files = lines[1:]
        if not files:
            continue
        any_stripped = any(is_stripped(f, patterns) for f in files)
        any_kept = any(not is_stripped(f, patterns) for f in files)
        if any_stripped and any_kept:
            mixed += 1
        elif any_stripped:
            record_only += 1
        else:
            code_only += 1
    return mixed, record_only, code_only


# -------------------------------------------------------------------- building


@dataclass
class BuildConfig:
    source: Path
    out: Path
    strip: list[str] = field(default_factory=lambda: list(DEFAULT_STRIP))
    history: str = "snapshot"  # snapshot | filter
    messages: str = "subject"  # keep | subject | scrub | map | mechanical | redact (filter mode only)
    message_map: Path | None = None  # messages=map: JSON {original_sha: neutral line}
    redact_dict: Path | None = None  # messages=redact: JSON {terms:[], patterns:[]} (dictgen)
    disable_workflows: list[str] = field(default_factory=list)  # moved to workflows-disabled/
    repo_slug: str = ""  # owner/repo of the SOURCE, for Addresses
    mirror_slug: str = ""  # owner/repo-no-adrs
    digest: str = "none"  # none | index | per-adr
    digest_glob: str = DEFAULT_DIGEST_GLOB
    digest_model: str = DEFAULT_DIGEST_MODEL
    digest_effort: str = DEFAULT_DIGEST_EFFORT
    digest_prompt: Path = DEFAULT_PROMPT_PATH
    digest_prompt_text: str = ""  # inline prompt; wins over digest_prompt when set
    digest_style: str = "full"  # full | brief (one-sentence bullets — the ADR index summary)
    digest_dry_run: bool = False
    history_epoch: str = "auto"  # auto | new — "new" DECLARES a full rebuild (phase A)
    state_objects: str = ""  # phase B: URL/path of the mirror, whose rewritten objects the state maps to
    approved_roots: list[str] = field(default_factory=list)  # fail-closed path consent
    notice: bool = True
    # "Governed by", never "available under": in closed mode the record is
    # precisely NOT available, and the notice must not promise what the mode
    # withholds (Pharos review F1, 2026-10-17).
    terms: str = (
        "Access to the record is governed by the source repository's "
        "maintainers; its license is decided separately from this code's."
    )


def check_approved(cfg: BuildConfig) -> None:
    """Fail-closed path-consent gate (ADR-0001 QST-SYNC-CONSENT, the answered
    B): with approved roots declared, any kept path OUTSIDE them stops the
    build before anything is written — a NEW path never rides a sync
    unreviewed. No roots declared = no gate (the action layer decides when
    declaring them is mandatory, e.g. for a public mirror)."""
    if not cfg.approved_roots:
        return
    paths = tracked_files(cfg.source)
    if cfg.history == "filter":
        # Filter mode publishes HISTORY: a never-approved path added and
        # deleted before HEAD would be invisible to a HEAD-only check yet
        # still ride the public history (Parallax's second look, gap 2.2).
        # Classify the union of every path that ever existed in the source.
        hist = git(["-c", "core.quotePath=false", "log", "--format=", "--name-only",
                    "--no-renames"], cfg.source)
        paths = sorted({l.strip() for l in hist.splitlines() if l.strip()} | set(paths))
    kept, _ = partition(paths, cfg.strip)
    roots = [r.strip().strip("/") for r in cfg.approved_roots if r.strip()]

    def _ok(p: str) -> bool:
        return any(p == r or p.startswith(r + "/") for r in roots)

    new = sorted(p for p in kept if not _ok(p))
    if new:
        tops = sorted({p.split("/")[0] for p in new})
        step_summary(
            f"**Sync stopped (fail-closed)**: {len(new)} kept path(s) fall outside "
            "the approved roots — new top-level entries: "
            + ", ".join(f"`{t}`" for t in tops)
            + ". Review them, then extend `approved_paths` (or strip them). "
            "Nothing was built or pushed."
        )
        hist_note = (" — history mode `filter` checks every path that EVER existed, "
                     "not only the current tree" if cfg.history == "filter" else "")
        raise RuntimeError(
            f"approved-paths gate: {len(new)} kept path(s) outside the approved "
            f"roots (new top-level entries: {', '.join(tops)}); "
            f"first: {', '.join(new[:5])}{hist_note}"
        )


def removal_summary(cfg: BuildConfig) -> str:
    """A per-rule removal log for $GITHUB_STEP_SUMMARY (the founder's ask,
    2026-10-21): the operator reviewing a run — especially a dry run — sees
    WHAT each strip rule removed without downloading the artifact. A rule
    that removed nothing shows 0: a legible absence, not a silent one."""
    kept, stripped = partition(tracked_files(cfg.source), cfg.strip)
    per: dict[str, list[str]] = {p: [] for p in cfg.strip}
    for f in stripped:
        for p in cfg.strip:
            if is_stripped(f, normalize_patterns([p])):
                per[p].append(f)
                break
    lines = [
        f"**Withheld: {len(stripped)} files · kept: {len(kept)}** — what each rule removed:",
        "",
        "| rule | files | first examples |",
        "|---|---|---|",
    ]
    for p in cfg.strip:
        fs = per[p]
        ex = ", ".join(f"`{x}`" for x in fs[:3]) + (" …" if len(fs) > 3 else "")
        lines.append(f"| `{p}` | {len(fs)} | {ex if fs else '— (matched nothing)'} |")
    if len(stripped) <= 400:
        lines += ["", "<details><summary>Every withheld path</summary>", ""]
        lines += [f"- `{f}`" for f in stripped]
        lines += ["", "</details>"]
    else:
        lines += ["", f"_Full list ({len(stripped)} paths) in the run's report JSON._"]
    return "\n".join(lines)


def build_snapshot(cfg: BuildConfig) -> dict:
    """One-commit mirror: the kept tree at source HEAD, zero history, zero
    message leakage. The quick-poise mode; filter mode is the linkable one.

    Built from `git archive HEAD` — the COMMITTED tree, never the worktree:
    a worktree copy follows symlinks (a tracked, kept symlink into stripped
    record content would materialize that content as a public regular file)
    and can carry uncommitted bytes while the notice stamps the HEAD sha.
    Both escapes closed per Parallax's second look (2026-10-20); the design
    was already accepted in ADR-0002."""
    log.info("snapshot build: %s -> %s", cfg.source, cfg.out)
    kept, stripped = partition(tracked_files(cfg.source), cfg.strip)
    if cfg.out.exists():
        shutil.rmtree(cfg.out)
    cfg.out.mkdir(parents=True)
    archive = subprocess.run(
        ["git", "-C", str(cfg.source), "archive", "HEAD"],
        capture_output=True, check=True,
    )
    subprocess.run(["tar", "-x", "-C", str(cfg.out)], input=archive.stdout, check=True)
    for rel in stripped:
        p = cfg.out / rel
        if p.is_symlink() or p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)
    # prune directories emptied by the strip (deepest first)
    for d in sorted((p for p in cfg.out.rglob("*") if p.is_dir()), reverse=True):
        try:
            d.rmdir()
        except OSError:
            pass
    sha = head_sha(cfg.source)
    git(["init", "-q", "-b", "main"], cfg.out)
    _set_mirror_identity(cfg.out)
    # Snapshot needs no rewrite state: every sync after the first appends one
    # commit via the push step's fast-forward merge (phase B by construction).
    phase = "epoch" if cfg.history_epoch == "new" else "incremental"
    (cfg.out.parent / (cfg.out.name + PHASE_SUFFIX)).write_text(phase)
    return {"kept": len(kept), "stripped": len(stripped), "source_sha": sha,
            "phase": phase}


def build_filtered(cfg: BuildConfig) -> dict:
    """Full-history mirror via git-filter-repo: record paths excised from
    every commit, record-only commits pruned WITH their messages, surviving
    messages rewritten per the tier ladder (map/redact/mechanical/scrub).
    Old mirror SHAs stay stable across incremental re-runs (phase B)."""
    log.info("filter build: %s -> %s (messages=%s)", cfg.source, cfg.out, cfg.messages)
    if shutil.which("git-filter-repo") is None:
        raise RuntimeError(
            "history=filter needs git-filter-repo (pip install git-filter-repo)"
        )
    if cfg.out.exists():
        shutil.rmtree(cfg.out)
    # --single-branch: the mirror syncs ONE branch, so the rewrite (and the
    # state map) must cover exactly that branch — rewriting every source
    # branch mints state entries for objects that never reach the mirror,
    # and the next incremental run dies fetching them (third live attempt).
    git(["clone", "-q", "--no-local", "--single-branch", str(cfg.source), str(cfg.out)],
        cfg.source.parent)
    # Identity FIRST: --state-branch makes filter-repo commit, and a bare CI
    # runner has no git identity ("Author identity unknown" — caught by the
    # public repo's own CI, not by a configured laptop).
    _set_mirror_identity(cfg.out)
    # Phase selection: a state branch in the source (riding into this clone)
    # means incremental — only new commits are processed and prior rewritten
    # SHAs stay byte-stable. "history_epoch: new" deletes it deliberately.
    # A clone keeps non-HEAD branches only as refs/remotes/origin/* — while
    # filter-repo's own lookup suffix-matches them. Materialize the exact
    # local ref first, then probe it FULLY QUALIFIED, so detection and
    # filter-repo can never disagree about whether state exists.
    subprocess.run(
        ["git", "-C", str(cfg.out), "fetch", "-q", "origin",
         f"+refs/heads/{STATE_BRANCH}:refs/heads/{STATE_BRANCH}"],
        capture_output=True,
    )
    state_probe = subprocess.run(
        ["git", "-C", str(cfg.out), "rev-parse", "--verify", "-q",
         f"refs/heads/{STATE_BRANCH}"],
        capture_output=True,
    )
    state_in_clone = state_probe.returncode == 0
    if cfg.history_epoch == "new" and state_in_clone:
        git(["branch", "-D", STATE_BRANCH], cfg.out)
        state_in_clone = False
    phase = "incremental" if state_in_clone else "epoch"
    log.info("filter phase: %s (state branch %s)", phase,
             "present" if state_in_clone else "absent")
    if state_in_clone:
        # The state maps source commits to REWRITTEN objects, which live only
        # in the mirror — a fresh clone must fetch them or fast-import dies
        # ("object not found"). Unreachable mirror + present state fails
        # closed: silently rebuilding would break every link WITHOUT a
        # declared epoch.
        fetched = subprocess.run(
            ["git", "-C", str(cfg.out), "fetch", "-q", cfg.state_objects or "/nonexistent",
             "+refs/heads/*:refs/no-adrs-mirror/prior/*"],
            capture_output=True, text=True,
        ) if cfg.state_objects else None
        if fetched is None or fetched.returncode != 0:
            raise RuntimeError(
                "incremental state is present but the mirror's objects are "
                "unreachable (no --state-objects URL, or the fetch failed). "
                "Fix the mirror URL/credentials — or DECLARE a rebuild with "
                'history_epoch: "new". Never both silently.'
            )
    args = ["filter-repo", "--force", "--invert-paths", "--prune-empty", "always",
            "--state-branch", STATE_BRANCH]
    for pat in cfg.strip:
        if any(ch in pat for ch in "*?["):
            args += ["--path-glob", pat]
        else:
            args += ["--path", pat]
    # The message-tier ladder (safety-ordered): map (model lines) → redact
    # (original subjects, dictionary-redacted — recall bounded by the dict) →
    # mechanical (deterministic type+diffstat, zero egress) → scrub (constant).
    # Degrade law: messages may degrade DOWN in warmth, never in privacy —
    # map's per-commit fallback is mechanical, never the original.
    MECHANICAL = (
        "import re\n"
        "msg = commit.message.decode('utf-8', 'replace')\n"
        "mt = re.match(r'^(feat|fix|chore|docs|test|refactor|perf|build|ci|style)\\b', msg)\n"
        "typ = mt.group(1) if mt else 'chore'\n"
        "files = [fc.filename.decode('utf-8', 'replace') for fc in commit.file_changes]\n"
        "tops = sorted({f.split('/')[0] for f in files})[:2]\n"
        "line = typ + ': update ' + (', '.join(tops) if tops else 'files')"
        " + ' (' + str(len(files)) + (' file)' if len(files) == 1 else ' files)')\n"
        "commit.message = (line + '\\n').encode()"
    )
    if cfg.messages == "subject":
        args += ["--message-callback", "return message.split(b'\\n', 1)[0] + b'\\n'"]
    elif cfg.messages == "scrub":
        args += ["--message-callback", "return b'code commit (message withheld)\\n'"]
    elif cfg.messages == "mechanical":
        args += ["--commit-callback", MECHANICAL]
    elif cfg.messages == "redact":
        # Original SUBJECT line with known tokens replaced by ‹…› — tier 1.5.
        # Recall is bounded by the dictionary; the notice must say so.
        if not cfg.redact_dict:
            raise RuntimeError("messages=redact needs --redact-dict <json from the dictgen subcommand>")
        dict_path = str(cfg.redact_dict.resolve()).replace("\\", "\\\\").replace("'", "\\'")
        args += ["--commit-callback", (
            "import json, re\n"
            f"d = globals().setdefault('_noadrs_dict', json.load(open('{dict_path}')))\n"
            "pats = globals().setdefault('_noadrs_pats', [re.compile(p, re.I) for p in d['patterns']]\n"
            "    + [re.compile(r'(?<!\\w)' + re.escape(t) + r'(?!\\w)') for t in d['terms']])\n"
            "subj = commit.message.decode('utf-8', 'replace').split('\\n', 1)[0]\n"
            "for p in pats:\n"
            "    subj = p.sub('\\u2039\\u2026\\u203a', subj)\n"
            "subj = re.sub(r'(\\u2039\\u2026\\u203a[\\s,;:/-]*)+', '\\u2039\\u2026\\u203a ', subj).strip()\n"
            "commit.message = (subj + '\\n').encode()"
        )]
    elif cfg.messages == "map":
        # Rewritten lines (e.g. model-written neutral summaries) keyed by the
        # ORIGINAL commit sha; absent keys fall back to the MECHANICAL line so
        # an incomplete map can never leak an original message.
        if not cfg.message_map:
            raise RuntimeError("messages=map needs --message-map <json of {original_sha: line}>")
        map_path = str(cfg.message_map.resolve()).replace("\\", "\\\\").replace("'", "\\'")
        args += ["--commit-callback", (
            "import json, re\n"
            f"m = globals().setdefault('_noadrs_msg_map', json.load(open('{map_path}')))\n"
            "line = m.get(commit.original_id.decode())\n"
            "if line is None:\n"
            + "".join("    " + l + "\n" for l in MECHANICAL.splitlines()[1:-1]) +
            "    commit.message = (line + '\\n').encode()\n"
            "else:\n"
            "    commit.message = (line.rstrip() + '\\n').encode()"
        )]
    git(args, cfg.out)
    # Persist the state back to the source so the NEXT run is phase B.
    # filter-repo deliberately removes the origin remote after rewriting;
    # re-point it at the source (local path, or the CI workspace — the action
    # then pushes it on to the hosted source with its own credentials).
    subprocess.run(["git", "-C", str(cfg.out), "remote", "remove", "origin"],
                   capture_output=True)
    git(["remote", "add", "origin", str(cfg.source)], cfg.out)
    git(["push", "-q", "origin", f"+refs/heads/{STATE_BRANCH}:refs/heads/{STATE_BRANCH}"],
        cfg.out)
    kept, stripped = partition(tracked_files(cfg.source), cfg.strip)
    _set_mirror_identity(cfg.out)
    (cfg.out.parent / (cfg.out.name + PHASE_SUFFIX)).write_text(phase)
    return {"kept": len(kept), "stripped": len(stripped),
            "source_sha": head_sha(cfg.source), "phase": phase}


def _set_mirror_identity(repo: Path) -> None:
    git(["config", "user.name", "no-adrs-mirror"], repo)
    git(["config", "user.email", "no-adrs-mirror@users.noreply.github.com"], repo)


# ---------------------------------------------------------------------- digest


class DigestClient(Protocol):
    def summarize(self, system: str, document: str, *, model: str, effort: str) -> str: ...


class AnthropicDigestClient:
    """Real client. Imported lazily; credentials resolve from the environment
    (ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN / an `ant auth login` profile)."""

    def __init__(self) -> None:
        import anthropic  # noqa: WPS433 — lazy on purpose

        self._anthropic = anthropic
        self._client = anthropic.Anthropic()

    def summarize(self, system: str, document: str, *, model: str, effort: str) -> str:
        a = self._anthropic
        try:
            response = self._client.messages.create(
                model=model,
                max_tokens=4000,
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": document}],
                output_config={"effort": effort},
            )
        except a.RateLimitError as exc:  # most specific first
            raise RuntimeError(f"rate limited: {exc}") from exc
        except a.APIStatusError as exc:
            raise RuntimeError(f"API error {exc.status_code}: {exc.message}") from exc
        except a.APIConnectionError as exc:
            raise RuntimeError(f"connection error: {exc}") from exc
        if response.stop_reason == "refusal":
            category = getattr(getattr(response, "stop_details", None), "category", None)
            return f"_Digest withheld: the model declined this document (category: {category})._"
        return "".join(b.text for b in response.content if b.type == "text").strip()


class DryRunDigestClient:
    """Writes what WOULD be sent; returns a placeholder. Zero API calls."""

    def __init__(self, sink: Path) -> None:
        self.sink = sink
        self.sink.mkdir(parents=True, exist_ok=True)
        self.calls = 0

    def summarize(self, system: str, document: str, *, model: str, effort: str) -> str:
        self.calls += 1
        (self.sink / f"call-{self.calls:03d}.prompt.txt").write_text(
            f"# model: {model}\n# effort: {effort}\n\n## system\n{system}\n\n## user\n{document}\n"
        )
        return f"_Dry run — no call made. Prompt recorded as call-{self.calls:03d}.prompt.txt._"


def adr_locator(rel_path: str) -> tuple[str, str]:
    """Return (kind, locator) for an Address: numbered ADRs cite by number
    (adr/0034), seeds by their slug (seed/2026-08-25-...), anything else by stem."""
    stem = Path(rel_path).stem
    m = re.match(r"^(\d{4})-", stem)
    if m:
        return "adr", m.group(1)
    if stem.startswith("seed-"):
        return "seed", stem[len("seed-"):]
    return "adr", stem


def address_for(repo_slug: str, rel_path: str) -> str:
    kind, loc = adr_locator(rel_path)
    slug = repo_slug or "<owner>/<repo>"
    return f"adr://v1/repo/{slug}/{kind}/{loc}"


def first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "(untitled)"


def digest_documents(cfg: BuildConfig, client: DigestClient, now: str | None = None) -> dict:
    """Write the digest index (and per-record files in per-adr mode): one
    model-written summary per record, each carrying its source's canonical
    Address. `digest_prompt_text` (inline string) wins over the prompt file —
    a workflow-inline prompt is self-contained and versioned with the caller,
    where a path must exist in the source tree (error-prone across repos).
    `digest_style=brief` asks for one-sentence bullets (the ADR index
    summary); `full` is the standard digest. Approval posture: the
    rights-holder's staged-by-default ruling (ADR-0001 QST-DIGEST-APPROVAL)
    governs when changed output may publish."""
    prompt = cfg.digest_prompt_text or cfg.digest_prompt.read_text()
    if cfg.digest_style == "brief":
        prompt += ("\nSTYLE OVERRIDE: exactly ONE sentence per record, "
                   "bullet-friendly, max 25 words. No headings, no lists inside the summary.")
    prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()[:12]
    log.info("digest: mode=%s style=%s model=%s dry_run=%s",
             cfg.digest, cfg.digest_style, cfg.digest_model, cfg.digest_dry_run)
    now = now or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sources = sorted(
        p for p in tracked_files(cfg.source) if fnmatch.fnmatch(p, cfg.digest_glob)
    )
    out_dir = cfg.out / DIGEST_DIR
    entries: list[dict] = []
    for rel in sources:
        text = (cfg.source / rel).read_text(errors="replace")
        summary = client.summarize(prompt, text, model=cfg.digest_model, effort=cfg.digest_effort)
        address = address_for(cfg.repo_slug, rel)
        title = first_heading(text)
        entries.append({"path": rel, "address": address, "title": title, "summary": summary})
        if cfg.digest == "per-adr":
            out_dir.mkdir(parents=True, exist_ok=True)
            body = (
                f"---\n"
                f"source: {address}\n"
                f"source_path: {rel}\n"
                f"generated_by: {cfg.digest_model}\n"
                f"generated_at: {now}\n"
                f"prompt_sha256: {prompt_sha}\n"
                f"kind: deliberations-digest\n"
                f"---\n\n"
                f"# Digest: {title}\n\n"
                f"> Summary of a deliberation record that is **not included** in this mirror. "
                f"Cite the source by its Address: `{address}`.\n\n"
                f"{summary}\n"
            )
            (out_dir / Path(rel).name).write_text(body)
    index_lines = [
        f"# Deliberations digest",
        "",
        f"This mirror omits the deliberation record. Below, one model-written summary per "
        f"record ({cfg.digest_model}, prompt `{prompt_sha}`, generated {now}). "
        f"Each entry names the canonical Address of its source; the Address is the citation.",
        "",
    ]
    for e in entries:
        first = e["summary"].strip().splitlines()[0] if e["summary"].strip() else ""
        link = f"{DIGEST_DIR}/{Path(e['path']).name}" if cfg.digest == "per-adr" else None
        head = f"- **{e['title']}** — `{e['address']}`"
        if link:
            head += f" — [digest]({link})"
        index_lines.append(head)
        if cfg.digest == "index" and first:
            index_lines.append(f"  {first}")
    (cfg.out / INDEX_FILE).write_text("\n".join(index_lines) + "\n")
    return {"digested": len(entries), "prompt_sha256": prompt_sha, "entries": entries}


# ---------------------------------------------------------------------- notice


def write_notice(cfg: BuildConfig, stats: dict, digest_stats: dict | None, now: str | None = None) -> Path:
    now = now or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    all_files = tracked_files(cfg.source)
    adrs = [p for p in all_files if fnmatch.fnmatch(p, "docs/adr/[0-9]*.md")]
    seeds = [p for p in all_files if fnmatch.fnmatch(p, "docs/adr/seed-*.md")]
    slug = cfg.repo_slug or "<owner>/<repo>"
    lines = [
        "# Deliberations notice",
        "",
        f"This repository is a **mirror without its deliberation record** "
        f"(\"Closed Deliberations\" mode — ADRs-for-AI practice: https://adrs.systems). "
        f"The record exists: **{len(adrs)} ADRs** and "
        f"**{len(seeds)} seeds** (early-stage records) are maintained alongside the source at `{slug}` "
        f"(source commit `{stats['source_sha'][:12]}`), and were withheld from this copy "
        f"together with {stats['stripped']} files under: "
        + ", ".join(f"`{p}`" for p in cfg.strip)
        + ".",
        "",
        # The notice story (ADR-0003 QST-STORY-OPENING tier 3, as revised at the
        # rights-holder's word 2026-10-19 via Sounder 6's finding: the notice
        # states facts about custody; it does not praise records it hasn't read).
        "These records are kept whole. The source maintainers retain them "
        "privately and decide whether and when to release them — not at all, "
        "later, or gradually. The disclosure decision keeps its own clock, "
        "and this notice declares, counts, and gates it.",
        "",
        f"**Terms**: {cfg.terms}",
        "",
        f"**Citing the record**: each ADR has a canonical Address of the form "
        f"`adr://v1/repo/{slug}/adr/<number>#<anchor>`; a resolving Address is the citation.",
        "",
    ]
    if digest_stats:
        # In a dry run no summary exists yet; the notice must not claim one does.
        digest_claim = (
            f"{digest_stats['digested']} digest entries are STAGED (dry run — no model call made; "
            f"prompts recorded in place of summaries)"
            if cfg.digest_dry_run
            else f"{digest_stats['digested']} model-written summaries are included"
        )
        lines += [
            f"**Digest**: {digest_claim} "
            f"(see `{INDEX_FILE}`"
            + (f" and `{DIGEST_DIR}/`" if cfg.digest == "per-adr" else "")
            + "). They are pointers to the record, not the record.",
            "",
        ]
    msg_note = ""
    if cfg.history == "filter":
        tier = {
            "map": "model-written neutral summaries with mechanical fallback",
            "mechanical": "mechanical summaries (type + changed paths; deterministic, no model)",
            "redact": "original subjects with dictionary redaction — recall is bounded by the dictionary",
            "subject": "original subject lines, unredacted",
            "scrub": "withheld (constant line)",
            "keep": "original messages, unmodified",
        }.get(cfg.messages, cfg.messages)
        prov = ""
        if cfg.messages == "map" and cfg.message_map and cfg.message_map.exists():
            prov = f"; map sha256 `{hashlib.sha256(cfg.message_map.read_bytes()).hexdigest()[:12]}`"
        if cfg.messages == "redact" and cfg.redact_dict and cfg.redact_dict.exists():
            prov = f"; dictionary sha256 `{hashlib.sha256(cfg.redact_dict.read_bytes()).hexdigest()[:12]}`"
        msg_note = f" **Commit messages**: {tier}{prov}."
    lines += [
        f"History mode: `{cfg.history}`"
        + (" (incremental — prior mirror commits remain reachable)"
           if stats.get("phase") == "incremental"
           else (" (epoch rebuild — history re-derived this sync)"
                 if cfg.history == "filter" else ""))
        + "."
        + msg_note
        + f" Generated {now} by "
        + f"[no-adrs-mirror](https://github.com/marketplace/actions/no-adrs-mirror) "
        + f"{__version__}.",
        "",
    ]
    path = cfg.out / NOTICE_FILE
    path.write_text("\n".join(lines))
    return path


def disable_listed_workflows(cfg: BuildConfig) -> list[str]:
    """Move named workflow files to .github/workflows-disabled/ — visible and
    reversible (the notice pattern applied to workflows). Publish/release
    workflows need secrets a mirror deliberately does not hold; test/lint
    workflows should usually STAY live (green checks on public code are part
    of the trust story). Classification is the caller's; this only moves."""
    moved = []
    wf = cfg.out / ".github" / "workflows"
    dst = cfg.out / ".github" / "workflows-disabled"
    for name in cfg.disable_workflows:
        src = wf / name
        if not src.exists():
            log.warning("disable-workflow: %s not found in mirror tree — skipped (nothing to disable)", name)
            continue
        dst.mkdir(parents=True, exist_ok=True)
        src.rename(dst / name)
        log.info("disable-workflow: %s -> .github/workflows-disabled/", name)
        moved.append(name)
    if moved:
        step_summary("**Workflows disabled in the mirror** (need secrets/publish authority "
                     "the mirror does not hold): " + ", ".join(f"`{m}`" for m in moved)
                     + " — moved to `.github/workflows-disabled/`, test/lint workflows stay live.")
    if moved:
        (dst / "README.md").write_text(
            "# Disabled workflows\n\n"
            "These workflows were moved here by the no-adrs-mirror Action because they "
            "require secrets or publish authority the mirror deliberately does not "
            "hold (publishing runs from the private source). Test and lint "
            "workflows remain live in `.github/workflows/`. See "
            "`DELIBERATIONS-NOTICE.md` for what this mirror is.\n"
        )
    return moved


# ----------------------------------------------------------------------- commit


def commit_all(cfg: BuildConfig, stats: dict) -> str:
    """Stage and commit the mirror's own additions (notice, digests, moves)
    under the bot identity — the one commit in the mirror that is the tool's
    and not the source's."""
    git(["add", "-A"], cfg.out)
    slug = cfg.repo_slug or "source"
    msg = (
        f"mirror: {slug}@{stats['source_sha'][:12]} without the deliberation record\n\n"
        f"{stats['kept']} files kept, {stats['stripped']} withheld; history={cfg.history}; "
        f"digest={cfg.digest}. Generated by no-adrs-mirror {__version__}."
    )
    git(["commit", "-q", "--allow-empty", "-m", msg], cfg.out)
    return head_sha(cfg.out)


# ------------------------------------------------------------------------ push


def push(out: Path, mirror_slug: str, *, create: bool, branch: str = "main",
         force: bool | None = None, url_override: str | None = None) -> None:
    """Push the built tree to the mirror repo. With `create`, a missing repo
    is created PRIVATE — always; there is no public flag in this tool (the
    visibility law).

    Two-phase push (ADR-0002): the build leaves a sibling `.phase` marker.
    Phase B (incremental) NEVER forces: if the target's tip is not already an
    ancestor, it is woven in as the second parent of a `-s ours` merge, so the
    push is a true fast-forward and every prior mirror SHA survives. Only a
    declared epoch (phase A) force-pushes. `url_override` exists for the
    offline test sandbox."""
    if force is None:
        marker = out.parent / (out.name + PHASE_SUFFIX)
        phase = marker.read_text().strip() if marker.exists() else "epoch"
        force = phase == "epoch"
    url = url_override or f"https://github.com/{mirror_slug}.git"
    # Rename-redirect guard (Parallax wake, 2026-10-20): a renamed-away repo
    # leaves a redirect, so a probe "finds" the old repo and a push lands on
    # ITS object store — old under-stripped objects stay addressable. The
    # probe therefore verifies the RESOLVED name; a mismatch means the named
    # repo does not really exist (create takes the name and breaks the
    # redirect) — and without create authority it is a hard, teaching stop.
    if url_override is None:
        probe = subprocess.run(
            ["gh", "repo", "view", mirror_slug, "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            capture_output=True, text=True,
        )
        resolved = probe.stdout.strip()
        redirected = probe.returncode == 0 and resolved.lower() != mirror_slug.lower()
    else:
        probe = None
        resolved, redirected = mirror_slug, False
    if redirected and not create:
        raise RuntimeError(
            f"push target {mirror_slug} resolves to {resolved} via a rename redirect — "
            "pushing would land on the OLD repository and its object store. Name the "
            "real repo, or enable create_if_missing so the named repo is created fresh."
        )
    if create:
        if redirected:
            log.warning("probe for %s resolved to %s via a rename redirect — creating the "
                        "named repo fresh so the push never lands on the old object store",
                        mirror_slug, resolved)
        if probe is None or probe.returncode != 0 or redirected:
            # THE LAW (rights-holder, 2026-10-11): making a mirror PUBLIC is a
            # visibility act — the owner's explicit, per-repo word, every time.
            # This tool therefore creates PRIVATE only and offers no flag to do
            # otherwise; the owner flips visibility themselves, deliberately.
            subprocess.run(
                ["gh", "repo", "create", mirror_slug, "--private", "--description",
                 "Code mirror without the deliberation record (see DELIBERATIONS-NOTICE.md)"],
                check=True,
            )
            print(f"created {mirror_slug} PRIVATE — flipping it public is the owner's own act, by design")
            log.info("created %s PRIVATE (the visibility law)", mirror_slug)
            step_summary(f"**Mirror created PRIVATE**: `{mirror_slug}` — flipping it public is the owner's own act, by design.")
    remotes = git(["remote"], out).split()
    if "mirror" in remotes:
        git(["remote", "set-url", "mirror", url], out)
    else:
        git(["remote", "add", "mirror", url], out)
    if force:
        git(["push", "--force", "mirror", f"HEAD:{branch}"], out)
        return
    # Phase B. If the target has history and its tip is not an ancestor of
    # ours (it never is after a rewrite — the tip is the previous sync's bot
    # commit), weave it in as the second parent of an `-s ours` merge: the
    # tree stays exactly this build's, the push becomes a fast-forward, and
    # every SHA anyone linked to remains reachable.
    fetched = subprocess.run(["git", "-C", str(out), "fetch", "-q", "mirror", branch],
                             capture_output=True, text=True)
    if fetched.returncode == 0:
        old_tip = git(["rev-parse", "FETCH_HEAD"], out).strip()
        is_anc = subprocess.run(
            ["git", "-C", str(out), "merge-base", "--is-ancestor", old_tip, "HEAD"]
        ).returncode == 0
        if not is_anc:
            git(["merge", "-q", "-s", "ours", "--allow-unrelated-histories",
                 "-m", "mirror: sync — previous tip preserved as a parent "
                       "(fast-forward by construction)", "FETCH_HEAD"], out)
    try:
        git(["push", "mirror", f"HEAD:{branch}"], out)
    except RuntimeError as e:
        raise RuntimeError(
            "phase B push was not a fast-forward — the mirror's history has "
            "diverged from what this sync extends. A new epoch is a deliberate "
            'human act: set history_epoch: "new" (full rebuild, force-push, '
            "declared in the notice) or reconcile the mirror by hand."
        ) from e


# ------------------------------------------------------------------------- CLI


def _parse(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="mirror.py", description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--source", type=Path, default=Path("."))
        sp.add_argument("--strip", action="append", default=None,
                        help="path or glob to withhold; repeatable; default = the record + apparatus")
        sp.add_argument("--repo-slug", default=os.environ.get("GITHUB_REPOSITORY", ""))

    b = sub.add_parser("build", help="build the mirror tree")
    common(b)
    b.add_argument("--out", type=Path, required=True)
    b.add_argument("--history", choices=["snapshot", "filter"], default="snapshot")
    b.add_argument("--state-objects", default="", dest="state_objects",
                   help="phase B: URL/path of the mirror repo (its objects back the state map)")
    b.add_argument("--history-epoch", choices=["auto", "new"], default="auto",
                   dest="history_epoch",
                   help='"new" DECLARES a full rebuild (phase A: rewrite + force-push); '
                        "auto is incremental whenever state allows")
    b.add_argument("--messages", choices=["keep", "subject", "scrub", "map", "mechanical", "redact"],
                   default="subject")
    b.add_argument("--message-map", type=Path, default=None,
                   help="messages=map: JSON file of {original_sha: neutral line}")
    b.add_argument("--redact-dict", type=Path, default=None,
                   help="messages=redact: dictionary JSON from the dictgen subcommand")
    b.add_argument("--additional-strip", action="append", default=[], dest="additional_strip",
                   help="pattern appended to the strip list (defaults or --strip) — additive, never replacing")
    b.add_argument("--approved-root", action="append", default=[], dest="approved_roots",
                   help="fail-closed consent gate: a kept path outside every approved root stops the build")
    b.add_argument("--disable-workflow", action="append", default=[], dest="disable_workflows",
                   help="workflow filename to move to .github/workflows-disabled/ (repeatable); "
                        "use for publish/release workflows — keep secretless CI live")
    b.add_argument("--digest", choices=["none", "index", "per-adr"], default="none")
    b.add_argument("--digest-glob", default=DEFAULT_DIGEST_GLOB)
    b.add_argument("--digest-style", choices=["full", "brief"], default="full",
                   help="brief = one-sentence bullets (the ADR index summary)")
    b.add_argument("--digest-prompt-text", default="",
                   help="inline prompt string; wins over --digest-prompt")
    b.add_argument("--digest-model", default=DEFAULT_DIGEST_MODEL)
    b.add_argument("--digest-effort", default=DEFAULT_DIGEST_EFFORT,
                   choices=["low", "medium", "high", "xhigh", "max"])
    b.add_argument("--digest-prompt", type=Path, default=DEFAULT_PROMPT_PATH)
    b.add_argument("--digest-dry-run", action="store_true",
                   help="write the prompts that would be sent; make no API call")
    b.add_argument("--no-notice", action="store_true")
    b.add_argument("--terms", default=None)
    b.add_argument("--no-commit", action="store_true")

    r = sub.add_parser("report", help="mixed-commit count + strip preview, no build")
    common(r)

    q = sub.add_parser("push", help="push a built tree to the mirror repo")
    q.add_argument("--out", type=Path, required=True)
    q.add_argument("--mirror", required=True, help="owner/repo-no-adrs")
    q.add_argument("--create", action="store_true")
    q.add_argument("--branch", default="main")

    dg = sub.add_parser("dictgen", help="compile a redaction dictionary for messages=redact")
    dg.add_argument("--registry", type=Path, action="append", default=[],
                    help="agent-sessions.json (repeatable); seat/alias names become terms")
    dg.add_argument("--extra", action="append", default=[], help="extra term (repeatable)")
    dg.add_argument("--out", type=Path, required=True)
    return p.parse_args(argv)


# Builtin reference-shaped patterns (case-insensitive): record ids, handles,
# Addresses, iteration markers, ledger numbers, version parentheticals.
DICT_BUILTIN_PATTERNS = [
    r"\bADR-\d{3,4}\b",
    r"\bQST-[A-Z0-9][A-Z0-9-]*\b",
    r"adr://\S+",
    r"\bseed-\d{4}-[\w-]+",
    r"\bIt-\d+\b",
    r"\((?:v|version )\d[^)]*\)",
    r"\b(?:adr|seed):\d{4}(?:#[\w-]+)?\b",
    r"№\s?\d+\b",
]

_NAME_KEYS = {"name", "alias", "seat", "display_name", "author", "address_token"}


def dictgen(registries: list[Path], extra: list[str], out: Path) -> dict:
    """Terms are matched CASE-SENSITIVELY (registry casing) — seat names are
    often common words ('Mint', 'Slate'); case-sensitive matching avoids
    redacting ordinary prose. Add lowercase variants via --extra when wanted.
    Recall is bounded by this dictionary, by design — the notice says so."""
    terms: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in _NAME_KEYS and isinstance(v, str) and 2 <= len(v) <= 64:
                    terms.add(v.strip())
                else:
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for reg in registries:
        walk(json.loads(Path(reg).read_text()))
    terms.update(t for t in extra if t.strip())
    d = {"patterns": DICT_BUILTIN_PATTERNS, "terms": sorted(terms)}
    out.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    return d


def main(argv: list[str] | None = None) -> int:
    ns = _parse(argv)
    if ns.cmd == "dictgen":
        d = dictgen(ns.registry, ns.extra, ns.out)
        print(json.dumps({"out": str(ns.out), "terms": len(d["terms"]),
                          "patterns": len(d["patterns"])}))
        return 0
    if ns.cmd == "push":
        push(ns.out, ns.mirror, create=ns.create, branch=ns.branch)
        print(f"pushed {ns.out} → {ns.mirror}:{ns.branch}")
        return 0

    strip = normalize_patterns(ns.strip) if ns.strip else list(DEFAULT_STRIP)
    # Additive semantics (Parallax P0.1): --additional-strip appends to the
    # base list (defaults or an explicit --strip set) instead of replacing it.
    if getattr(ns, "additional_strip", None):
        strip += normalize_patterns(ns.additional_strip)
    source = ns.source.resolve()
    if ns.cmd == "report":
        kept, stripped = partition(tracked_files(source), strip)
        mixed, rec, code = mixed_commit_count(source, strip)
        print(json.dumps({
            "source": str(source), "strip": strip,
            "files": {"kept": len(kept), "stripped": len(stripped)},
            "commits": {"mixed": mixed, "record_only": rec, "code_only": code},
            "note": "mixed commits are the messages that survive filter mode; "
                    "record-only commits vanish with their messages",
        }, indent=2))
        return 0

    cfg = BuildConfig(
        source=source, out=ns.out.resolve(), strip=strip, history=ns.history,
        messages=ns.messages, message_map=ns.message_map, redact_dict=ns.redact_dict,
        disable_workflows=ns.disable_workflows,
        repo_slug=ns.repo_slug, digest=ns.digest,
        digest_glob=ns.digest_glob, digest_model=ns.digest_model,
        digest_effort=ns.digest_effort, digest_prompt=ns.digest_prompt,
        digest_prompt_text=ns.digest_prompt_text, digest_style=ns.digest_style,
        digest_dry_run=ns.digest_dry_run, notice=not ns.no_notice,
        history_epoch=ns.history_epoch, state_objects=ns.state_objects,
        approved_roots=ns.approved_roots,
    )
    if ns.terms:
        cfg.terms = ns.terms
    check_approved(cfg)  # fail-closed, before anything is written
    stats = build_filtered(cfg) if cfg.history == "filter" else build_snapshot(cfg)
    step_summary(removal_summary(cfg))
    digest_stats = None
    if cfg.digest != "none":
        client: DigestClient
        if cfg.digest_dry_run:
            client = DryRunDigestClient(cfg.out.parent / (cfg.out.name + ".prompts"))
        else:
            client = AnthropicDigestClient()
        digest_stats = digest_documents(cfg, client)
    if cfg.disable_workflows:
        disable_listed_workflows(cfg)
    if cfg.notice:
        write_notice(cfg, stats, digest_stats)
    sha = None if ns.no_commit else commit_all(cfg, stats)
    mixed, rec, code = mixed_commit_count(source, strip)
    print(json.dumps({
        "out": str(cfg.out), "history": cfg.history, "messages": cfg.messages,
        "files": {"kept": stats["kept"], "stripped": stats["stripped"]},
        "source_sha": stats["source_sha"], "mirror_sha": sha,
        "digest": {"mode": cfg.digest, "count": digest_stats["digested"] if digest_stats else 0,
                   "dry_run": cfg.digest_dry_run},
        "commits_in_source": {"mixed": mixed, "record_only": rec, "code_only": code},
    }, indent=2))
    step_summary(
        f"**no-adrs-mirror build** — history `{cfg.history}`, messages `{cfg.messages}`"
        f"{', digest ' + cfg.digest + '/' + cfg.digest_style if cfg.digest != 'none' else ''}\n\n"
        f"| kept | withheld | mixed commits in source |\n|---|---|---|\n"
        f"| {stats['kept']} | {stats['stripped']} | {mixed} |\n\n"
        f"Source `{stats['source_sha'][:12]}` → mirror `{(sha or 'uncommitted')[:12]}`. "
        f"The notice (`{NOTICE_FILE}`) carries the full disclosure."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
