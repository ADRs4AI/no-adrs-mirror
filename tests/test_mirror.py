"""Tests for the no-adrs-mirror prototype (Third–Fifth Directives: each test
pins a claim the README makes; run before commit).

    <venv>/bin/pytest tests/ -q   (from the repo root)
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import mirror  # noqa: E402


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True)


def _commit(repo: Path, files: dict[str, str], msg: str) -> None:
    for rel, content in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    _git(["add", "-A"], repo)
    _git(["commit", "-q", "-m", msg], repo)


ADR_0001 = """# ADR-0001: Pick a queue

- **Status**: Accepted

## Questions

### QST-BACKEND: Redis or Postgres?
- Status: unanswered

**Recommendation**: (by Test 5)
**B — Postgres.** Because we already run it.

**ANS:** (by Someone)
[Fill this in]
"""


@pytest.fixture
def source(tmp_path: Path) -> Path:
    repo = tmp_path / "src"
    repo.mkdir()
    _git(["init", "-q", "-b", "main"], repo)
    _git(["config", "user.name", "t"], repo)
    _git(["config", "user.email", "t@example.com"], repo)
    _commit(repo, {"src/app.py": "print('hi')\n", "README.md": "# app\n"}, "feat: app (code only)")
    _commit(repo, {"docs/adr/0001-pick-a-queue.md": ADR_0001, "CLAUDE.md": "# CLAUDE\nseat: Test 5\n"},
            "docs: ADR-0001 pick a queue — the founder said Postgres, I flagged the cost (RECORD ONLY)")
    _commit(repo, {"src/queue.py": "Q = 'pg'\n", "docs/adr/seed-2026-01-01-thoughts.md": "# SEED: thoughts\n",
                   "docs/inbox/2026-01-01-0000-a-to-b-hello.md": "# hello\n"},
            "docs+feat: queue + seed (MIXED — this subject survives filter mode)")
    return repo


class FakeDigest:
    def __init__(self):
        self.calls = []

    def summarize(self, system, document, *, model, effort):
        self.calls.append((model, effort, len(system), len(document)))
        return f"**Decision** — fake digest of {document.splitlines()[0]}\n\n**Open questions**\n- QST-BACKEND — Redis or Postgres? (unanswered)\n"


def test_partition_strips_record_and_apparatus():
    files = ["src/app.py", "docs/adr/0001-x.md", "docs/adr/seed-1.md", "docs/inbox/x.md",
             "CLAUDE.md", ".claude/settings.json", "docs/README.md"]
    kept, stripped = mirror.partition(files, mirror.DEFAULT_STRIP)
    assert kept == ["src/app.py", "docs/README.md"]
    assert "CLAUDE.md" in stripped and ".claude/settings.json" in stripped


def test_glob_patterns_strip_too():
    assert mirror.is_stripped("notes/private-2026.md", mirror.normalize_patterns(["notes/private-*.md"]))
    assert not mirror.is_stripped("notes/public.md", mirror.normalize_patterns(["notes/private-*.md"]))


def test_mixed_commit_count(source: Path):
    mixed, record_only, code_only = mirror.mixed_commit_count(source, mirror.DEFAULT_STRIP)
    assert (mixed, record_only, code_only) == (1, 1, 1)


def test_snapshot_has_code_no_record_one_commit(source: Path, tmp_path: Path):
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out", repo_slug="acme/app")
    stats = mirror.build_snapshot(cfg)
    mirror.write_notice(cfg, stats, None, now="2026-08-26T00:00:00Z")
    mirror.commit_all(cfg, stats)
    out = cfg.out
    assert (out / "src/app.py").exists() and (out / "src/queue.py").exists()
    assert not (out / "docs/adr").exists() and not (out / "docs/inbox").exists()
    assert not (out / "CLAUDE.md").exists()
    log = subprocess.run(["git", "log", "--format=%s"], cwd=out, capture_output=True, text=True).stdout
    assert len(log.strip().splitlines()) == 1
    assert "RECORD ONLY" not in log and "MIXED" not in log
    notice = (out / mirror.NOTICE_FILE).read_text()
    assert "1 ADRs" in notice and "1 seeds" in notice and "acme/app" in notice
    assert "adr://v1/repo/acme/app/adr/<number>#<anchor>" in notice
    # The notice story (tier 3 as revised at the rights-holder's word,
    # 2026-10-19 — facts about custody, no praise of unread records):
    # release-mutable copy, but never silently droppable.
    assert "decide whether and when to release them" in notice


@pytest.mark.skipif(shutil.which("git-filter-repo") is None, reason="git-filter-repo not installed")
def test_filter_prunes_record_only_commits_and_keeps_subjects(source: Path, tmp_path: Path):
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out", history="filter", messages="subject")
    mirror.build_filtered(cfg)
    out = cfg.out
    assert not (out / "docs/adr").exists() and not (out / "CLAUDE.md").exists()
    assert (out / "src/queue.py").exists()
    log = subprocess.run(["git", "log", "--format=%B"], cwd=out, capture_output=True, text=True).stdout
    assert "RECORD ONLY" not in log            # the docs-only commit vanished with its message
    assert "MIXED" in log                       # the mixed commit's SUBJECT survives (the residual leak)
    subjects = subprocess.run(["git", "log", "--format=%s"], cwd=out, capture_output=True, text=True).stdout
    assert len(subjects.strip().splitlines()) == 2


@pytest.mark.skipif(shutil.which("git-filter-repo") is None, reason="git-filter-repo not installed")
def test_filter_scrub_removes_all_messages(source: Path, tmp_path: Path):
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out", history="filter", messages="scrub")
    mirror.build_filtered(cfg)
    log = subprocess.run(["git", "log", "--format=%s"], cwd=cfg.out, capture_output=True, text=True).stdout
    assert set(log.strip().splitlines()) == {"code commit (message withheld)"}


def test_disable_workflow_moves_file_and_writes_readme(source: Path, tmp_path: Path):
    # Publish workflows move to workflows-disabled/ (visible, reversible);
    # workflows NOT listed stay live; a missing name is a skip, never a crash.
    _commit(source, {".github/workflows/release.yml": "name: release\n",
                     ".github/workflows/ci.yml": "name: ci\n"}, "ci: add workflows")
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out",
                             disable_workflows=["release.yml", "nonexistent.yml"])
    mirror.build_snapshot(cfg)
    mirror.disable_listed_workflows(cfg)
    assert not (cfg.out / ".github/workflows/release.yml").exists()
    assert (cfg.out / ".github/workflows-disabled/release.yml").exists()
    assert (cfg.out / ".github/workflows/ci.yml").exists()            # untouched, stays live
    readme = (cfg.out / ".github/workflows-disabled/README.md").read_text()
    assert "secrets" in readme and "remain live" in readme


@pytest.mark.skipif(shutil.which("git-filter-repo") is None, reason="git-filter-repo not installed")
def test_filter_map_rewrites_messages_and_falls_back_neutral(source: Path, tmp_path: Path):
    # messages=map: surviving commits get their mapped neutral line (keyed by
    # ORIGINAL sha); an unmapped survivor falls back to a constant so an
    # incomplete map can never leak an original message.
    import json
    shas = subprocess.run(["git", "log", "--format=%H %s"], cwd=source,
                          capture_output=True, text=True).stdout.strip().splitlines()
    mixed_sha = next(l.split()[0] for l in shas if "MIXED" in l)
    mapping = {mixed_sha: "Neutral mapped line for the mixed change"}
    map_file = tmp_path / "map.json"
    map_file.write_text(json.dumps(mapping))
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out", history="filter",
                             messages="map", message_map=map_file)
    mirror.build_filtered(cfg)
    subjects = subprocess.run(["git", "log", "--format=%s"], cwd=cfg.out,
                              capture_output=True, text=True).stdout.strip().splitlines()
    assert "Neutral mapped line for the mixed change" in subjects
    others = [s for s in subjects if s != "Neutral mapped line for the mixed change"]
    # Unmapped survivors degrade to the MECHANICAL line (type + paths), never the original.
    import re as _re
    assert others and all(_re.match(r"^(feat|fix|chore|docs|test|refactor|perf|build|ci|style): update ", s) for s in others)
    full = subprocess.run(["git", "log", "--format=%B"], cwd=cfg.out,
                          capture_output=True, text=True).stdout
    assert "MIXED" not in full  # no original text survives anywhere


@pytest.mark.skipif(shutil.which("git-filter-repo") is None, reason="git-filter-repo not installed")
def test_filter_mechanical_messages_are_deterministic_type_plus_paths(source: Path, tmp_path: Path):
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out", history="filter", messages="mechanical")
    mirror.build_filtered(cfg)
    subjects = subprocess.run(["git", "log", "--format=%s"], cwd=cfg.out,
                              capture_output=True, text=True).stdout.strip().splitlines()
    import re as _re
    assert subjects and all(_re.match(r"^(feat|fix|chore|docs|test|refactor|perf|build|ci|style): update .+ \(\d+ files?\)$", s) for s in subjects)
    full = subprocess.run(["git", "log", "--format=%B"], cwd=cfg.out, capture_output=True, text=True).stdout
    assert "MIXED" not in full and "founder" not in full


@pytest.mark.skipif(shutil.which("git-filter-repo") is None, reason="git-filter-repo not installed")
def test_filter_redact_replaces_dictionary_tokens_only(source: Path, tmp_path: Path):
    import json as _json
    _commit(source, {"src/extra.py": "x = 1\n"},
            "fix: QST-BACKEND per ADR-0001 — Postgres said no (v1.2) TOKENTEST")
    d = {"patterns": mirror.DICT_BUILTIN_PATTERNS, "terms": ["Postgres"]}
    dict_file = tmp_path / "dict.json"
    dict_file.write_text(_json.dumps(d))
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out", history="filter",
                             messages="redact", redact_dict=dict_file)
    mirror.build_filtered(cfg)
    subjects = subprocess.run(["git", "log", "--format=%s"], cwd=cfg.out,
                              capture_output=True, text=True).stdout
    line = next(s for s in subjects.splitlines() if "TOKENTEST" in s)
    # Known tokens redacted (handle, record id, version paren, term)…
    assert "QST-BACKEND" not in line and "ADR-0001" not in line
    assert "(v1.2)" not in line and "Postgres" not in line and "‹…›" in line
    # …but novel words pass through: recall is bounded by the dictionary.
    assert "said no" in line


def test_digest_brief_style_and_inline_prompt(source: Path, tmp_path: Path):
    # brief style appends the one-sentence override; inline prompt text wins
    # over the prompt file; both are visible in the dry-run prompt sink.
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out", repo_slug="acme/app",
                             digest="index", digest_style="brief",
                             digest_prompt_text="CUSTOM-INLINE-PROMPT for the index.",
                             digest_dry_run=True)
    (tmp_path / "out").mkdir()
    client = mirror.DryRunDigestClient(tmp_path / "prompts")
    mirror.digest_documents(cfg, client, now="2026-01-01T00:00:00Z")
    sent = next((tmp_path / "prompts").glob("*.prompt.txt")).read_text()
    assert "CUSTOM-INLINE-PROMPT" in sent and "exactly ONE sentence" in sent


def test_dictgen_collects_registry_names_and_builtins(tmp_path: Path):
    import json as _json
    reg = tmp_path / "agent-sessions.json"
    reg.write_text(_json.dumps({"sessions": [
        {"name": "Mint 5", "alias": "mint", "model": "x"},
        {"name": "Covenant 5", "address_token": "advocate"},
    ]}))
    d = mirror.dictgen([reg], ["Jérémie"], tmp_path / "dict.json")
    assert {"Mint 5", "mint", "Covenant 5", "advocate", "Jérémie"} <= set(d["terms"])
    assert any("ADR-" in p for p in d["patterns"])


def test_digest_per_adr_writes_pointer_files(source: Path, tmp_path: Path):
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out", repo_slug="acme/app", digest="per-adr",
                             digest_model="claude-sonnet-5", digest_effort="low")
    stats = mirror.build_snapshot(cfg)
    fake = FakeDigest()
    d = mirror.digest_documents(cfg, fake, now="2026-08-26T00:00:00Z")
    assert d["digested"] == 1 and fake.calls[0][:2] == ("claude-sonnet-5", "low")
    f = cfg.out / mirror.DIGEST_DIR / "0001-pick-a-queue.md"
    text = f.read_text()
    assert "source: adr://v1/repo/acme/app/adr/0001" in text
    assert "generated_by: claude-sonnet-5" in text and "prompt_sha256:" in text
    assert "QST-BACKEND" in text
    index = (cfg.out / mirror.INDEX_FILE).read_text()
    assert "ADR-0001: Pick a queue" in index and "adr://v1/repo/acme/app/adr/0001" in index
    mirror.write_notice(cfg, stats, d, now="2026-08-26T00:00:00Z")
    assert "1 model-written summaries" in (cfg.out / mirror.NOTICE_FILE).read_text()


def test_digest_dry_run_makes_no_calls_but_records_prompts(source: Path, tmp_path: Path):
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out", repo_slug="acme/app", digest="index")
    mirror.build_snapshot(cfg)
    sink = tmp_path / "prompts"
    client = mirror.DryRunDigestClient(sink)
    mirror.digest_documents(cfg, client, now="2026-08-26T00:00:00Z")
    files = sorted(sink.glob("*.prompt.txt"))
    assert len(files) == 1
    body = files[0].read_text()
    assert "# model: claude-sonnet-5" in body and "## system" in body and "QST-BACKEND" in body
    assert (cfg.out / mirror.INDEX_FILE).exists()
    assert not (cfg.out / mirror.DIGEST_DIR).exists()   # index mode writes no per-ADR files


def test_address_locators():
    assert mirror.address_for("acme/app", "docs/adr/0034-foo.md") == "adr://v1/repo/acme/app/adr/0034"
    assert mirror.address_for("acme/app", "docs/adr/seed-2026-08-25-x.md") == "adr://v1/repo/acme/app/seed/2026-08-25-x"


def test_cli_report(source: Path, capsys):
    rc = mirror.main(["report", "--source", str(source)])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"mixed": 1' in out and '"record_only": 1' in out


def test_approved_roots_gate_fails_closed(source: Path, tmp_path: Path):
    # ADR-0001 QST-SYNC-CONSENT (answer B): a kept path outside the approved
    # roots stops the build BEFORE anything is written — a new path never
    # rides a sync unreviewed. The fixture keeps src/ and README-less tops,
    # so approving only "src" must trip on nothing-else-kept... the fixture
    # also keeps docs/README-class files; approve src alone and expect a stop.
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out",
                             repo_slug="acme/app", approved_roots=["src"])
    kept, _ = mirror.partition(mirror.tracked_files(source), cfg.strip)
    outside = [p for p in kept if not p.startswith("src/")]
    assert outside, "fixture must keep something outside src/ for this test"
    with pytest.raises(RuntimeError, match="approved-paths gate"):
        mirror.check_approved(cfg)
    assert not (tmp_path / "out").exists()  # nothing was written


def test_approved_roots_gate_passes_when_covered(source: Path, tmp_path: Path):
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out", repo_slug="acme/app")
    kept, _ = mirror.partition(mirror.tracked_files(source), cfg.strip)
    tops = sorted({p.split("/")[0] for p in kept})
    cfg.approved_roots = tops
    mirror.check_approved(cfg)  # must not raise


def test_snapshot_builds_from_committed_tree_not_worktree(source: Path, tmp_path: Path):
    # Parallax second look (2026-10-20): a worktree copy can publish
    # UNCOMMITTED bytes while the notice stamps the HEAD sha. The archive
    # build must carry committed content only.
    (source / "src" / "app.py").write_text("DIRTY = 'uncommitted'\n")
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out", repo_slug="acme/app")
    mirror.build_snapshot(cfg)
    assert "DIRTY" not in (tmp_path / "out" / "src" / "app.py").read_text()


def test_snapshot_symlink_cannot_materialize_stripped_content(source: Path, tmp_path: Path):
    # Parallax second look: shutil.copy2 followed symlinks, so a tracked,
    # KEPT symlink pointing into stripped record content became a public
    # regular file holding that content. The archive build preserves the
    # symlink as a symlink (a path string, dangling after the strip).
    (source / "src" / "leak.md").symlink_to("../docs/adr/seed-2026-01-01-thoughts.md")
    _git(["add", "src/leak.md"], source)
    _git(["commit", "-q", "-m", "feat: add handy link"], source)
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out", repo_slug="acme/app")
    mirror.build_snapshot(cfg)
    out_link = tmp_path / "out" / "src" / "leak.md"
    assert not out_link.is_file()  # is_file() follows symlinks: a regular file
    #                                with record bytes would be the escape


def test_filter_mode_approval_sees_historical_paths(source: Path, tmp_path: Path):
    # Parallax second look, gap 2.2: a never-approved path added and deleted
    # BEFORE HEAD is invisible to a HEAD-only check yet rides the published
    # history. Filter mode must classify the union of every path that ever
    # existed.
    _commit(source, {"secrets-dump/creds.txt": "x\n"}, "chore: add dump")
    _git(["rm", "-q", "secrets-dump/creds.txt"], source)
    _git(["commit", "-q", "-m", "chore: remove dump"], source)
    kept, _ = mirror.partition(mirror.tracked_files(source), mirror.DEFAULT_STRIP)
    tops = sorted({p.split("/")[0] for p in kept})
    assert "secrets-dump" not in tops  # gone from HEAD — the trap is set
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out", repo_slug="acme/app",
                             history="filter", approved_roots=tops)
    with pytest.raises(RuntimeError, match="EVER existed"):
        mirror.check_approved(cfg)


def test_removal_summary_names_each_rule(source: Path, tmp_path: Path):
    # The founder's ask (2026-10-21): the step summary teaches WHAT each rule
    # removed — including rules that removed nothing (legible absence).
    cfg = mirror.BuildConfig(source=source, out=tmp_path / "out", repo_slug="acme/app")
    s = mirror.removal_summary(cfg)
    assert "| `docs/adr` | 2 |" in s          # fixture has a seed + an adr-dir file? counts real
    assert "matched nothing" in s              # at least one default rule is idle here
    assert "Every withheld path" in s          # the collapsible full list (small repo)


def test_additional_strip_is_additive(source: Path, tmp_path: Path, capsys):
    # Parallax P0.1: --additional-strip appends to the defaults instead of
    # replacing them — docs/adr (a default) AND src/queue.py (the addition)
    # must both be stripped in the same run.
    rc = mirror.main(["build", "--source", str(source), "--out", str(tmp_path / "out"),
                      "--repo-slug", "acme/app", "--additional-strip", "src/queue.py",
                      "--no-notice", "--no-commit"])
    assert rc == 0
    assert (tmp_path / "out" / "src" / "app.py").exists()
    assert not (tmp_path / "out" / "src" / "queue.py").exists()   # the addition
    assert not (tmp_path / "out" / "docs" / "adr").exists()       # defaults kept
