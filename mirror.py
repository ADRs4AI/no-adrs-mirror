#!/usr/bin/env python3
"""no-adrs mirror — publish a repository's code without its deliberation record.

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
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Protocol

__version__ = "0.1.0"

DEFAULT_STRIP = [
    "docs/adr",
    "docs/inbox",
    "docs/vignettes",
    "docs/handoffs",
    "CLAUDE.md",
    "AGENTS.md",
    ".claude",
    ".pneumatic",
]
DEFAULT_DIGEST_GLOB = "docs/adr/[0-9]*.md"
DEFAULT_DIGEST_MODEL = "claude-sonnet-5"
DEFAULT_DIGEST_EFFORT = "medium"
DIGEST_DIR = "docs/deliberations-digest"
NOTICE_FILE = "DELIBERATIONS-NOTICE.md"
INDEX_FILE = "DELIBERATIONS-DIGEST.md"
HERE = Path(__file__).resolve().parent
DEFAULT_PROMPT_PATH = HERE / "prompts" / "adr-digest.md"


# --------------------------------------------------------------------------- git


def git(args: list[str], cwd: Path, check: bool = True) -> str:
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
    kept, stripped = [], []
    for p in paths:
        (stripped if is_stripped(p, patterns) else kept).append(p)
    return kept, stripped


# ----------------------------------------------------------------- history math


def mixed_commit_count(source: Path, patterns: list[str]) -> tuple[int, int, int]:
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
    messages: str = "subject"  # keep | subject | scrub   (filter mode only)
    repo_slug: str = ""  # owner/repo of the SOURCE, for Addresses
    mirror_slug: str = ""  # owner/repo-no-adrs
    digest: str = "none"  # none | index | per-adr
    digest_glob: str = DEFAULT_DIGEST_GLOB
    digest_model: str = DEFAULT_DIGEST_MODEL
    digest_effort: str = DEFAULT_DIGEST_EFFORT
    digest_prompt: Path = DEFAULT_PROMPT_PATH
    digest_dry_run: bool = False
    notice: bool = True
    terms: str = (
        "The record is available on request from the source repository's "
        "maintainers; its license is decided separately from this code's."
    )


def build_snapshot(cfg: BuildConfig) -> dict:
    kept, stripped = partition(tracked_files(cfg.source), cfg.strip)
    if cfg.out.exists():
        shutil.rmtree(cfg.out)
    cfg.out.mkdir(parents=True)
    for rel in kept:
        src = cfg.source / rel
        dst = cfg.out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    sha = head_sha(cfg.source)
    git(["init", "-q", "-b", "main"], cfg.out)
    _set_mirror_identity(cfg.out)
    return {"kept": len(kept), "stripped": len(stripped), "source_sha": sha}


def build_filtered(cfg: BuildConfig) -> dict:
    if shutil.which("git-filter-repo") is None:
        raise RuntimeError(
            "history=filter needs git-filter-repo (pip install git-filter-repo)"
        )
    if cfg.out.exists():
        shutil.rmtree(cfg.out)
    git(["clone", "-q", "--no-local", str(cfg.source), str(cfg.out)], cfg.source.parent)
    args = ["filter-repo", "--force", "--invert-paths", "--prune-empty", "always"]
    for pat in cfg.strip:
        if any(ch in pat for ch in "*?["):
            args += ["--path-glob", pat]
        else:
            args += ["--path", pat]
    if cfg.messages == "subject":
        args += ["--message-callback", "return message.split(b'\\n', 1)[0] + b'\\n'"]
    elif cfg.messages == "scrub":
        args += ["--message-callback", "return b'code commit (message withheld)\\n'"]
    git(args, cfg.out)
    kept, stripped = partition(tracked_files(cfg.source), cfg.strip)
    _set_mirror_identity(cfg.out)
    return {"kept": len(kept), "stripped": len(stripped), "source_sha": head_sha(cfg.source)}


def _set_mirror_identity(repo: Path) -> None:
    git(["config", "user.name", "no-adrs mirror"], repo)
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
    prompt = cfg.digest_prompt.read_text()
    prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()[:12]
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
        f"(\"Closed Deliberations\" mode). The record exists: **{len(adrs)} ADRs** and "
        f"**{len(seeds)} seeds** are maintained alongside the source at `{slug}` "
        f"(source commit `{stats['source_sha'][:12]}`), and were withheld from this copy "
        f"together with {stats['stripped']} files under: "
        + ", ".join(f"`{p}`" for p in cfg.strip)
        + ".",
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
    lines += [
        f"History mode: `{cfg.history}`"
        + (f" (messages: {cfg.messages})" if cfg.history == "filter" else "")
        + f". Generated {now} by no-adrs-mirror {__version__}.",
        "",
    ]
    path = cfg.out / NOTICE_FILE
    path.write_text("\n".join(lines))
    return path


# ----------------------------------------------------------------------- commit


def commit_all(cfg: BuildConfig, stats: dict) -> str:
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


def push(out: Path, mirror_slug: str, *, create: bool, branch: str = "main", force: bool = True) -> None:
    url = f"https://github.com/{mirror_slug}.git"
    if create:
        probe = subprocess.run(["gh", "repo", "view", mirror_slug], capture_output=True, text=True)
        if probe.returncode != 0:
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
    remotes = git(["remote"], out).split()
    if "mirror" in remotes:
        git(["remote", "set-url", "mirror", url], out)
    else:
        git(["remote", "add", "mirror", url], out)
    args = ["push", "mirror", f"HEAD:{branch}"]
    if force:
        args.insert(1, "--force")
    git(args, out)


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
    b.add_argument("--messages", choices=["keep", "subject", "scrub"], default="subject")
    b.add_argument("--digest", choices=["none", "index", "per-adr"], default="none")
    b.add_argument("--digest-glob", default=DEFAULT_DIGEST_GLOB)
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
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse(argv)
    if ns.cmd == "push":
        push(ns.out, ns.mirror, create=ns.create, branch=ns.branch)
        print(f"pushed {ns.out} → {ns.mirror}:{ns.branch}")
        return 0

    strip = normalize_patterns(ns.strip) if ns.strip else list(DEFAULT_STRIP)
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
        messages=ns.messages, repo_slug=ns.repo_slug, digest=ns.digest,
        digest_glob=ns.digest_glob, digest_model=ns.digest_model,
        digest_effort=ns.digest_effort, digest_prompt=ns.digest_prompt,
        digest_dry_run=ns.digest_dry_run, notice=not ns.no_notice,
    )
    if ns.terms:
        cfg.terms = ns.terms
    stats = build_filtered(cfg) if cfg.history == "filter" else build_snapshot(cfg)
    digest_stats = None
    if cfg.digest != "none":
        client: DigestClient
        if cfg.digest_dry_run:
            client = DryRunDigestClient(cfg.out.parent / (cfg.out.name + ".prompts"))
        else:
            client = AnthropicDigestClient()
        digest_stats = digest_documents(cfg, client)
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
