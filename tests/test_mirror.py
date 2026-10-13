"""Tests for the no-adrs mirror prototype (Third–Fifth Directives: each test
pins a claim the README makes; run before commit).

    <venv>/bin/pytest scripts/ephemeral/2026-08-26-no-adrs-mirror-action/tests -q
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
