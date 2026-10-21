# no-adrs-mirror

**A GitHub Action for a private repository: each push rebuilds a second
repository — the mirror — with the same code, the configured record paths
removed, and one generated file, `DELIBERATIONS-NOTICE.md`, stating what was
withheld.**

You work in a **private repository** that holds code *and* thinking — ADRs
(architecture decision records), agent inboxes, `CLAUDE.md` (a *deliberation
record*, in [ADRs-for-AI](https://adrs.systems/) practice). Each push to `main` rebuilds
the mirror, a **separate GitHub repository**:

```text
your-repo (PRIVATE — you work here)      your-repo-no-adrs (the mirror)
├── src/                                 ├── src/     ← identical, byte for byte
├── tests/                               ├── tests/   ← identical
├── docs/adr/        ─┐                  └── DELIBERATIONS-NOTICE.md
├── docs/inbox/       ├─ stays home           ← the ONE generated file: what
└── CLAUDE.md, …     ─┘                         exists, what was withheld
```

Withheld by default: `docs/adr`, `docs/inbox`, `docs/vignettes`,
`docs/handoffs`, `docs/continuity`, `docs/HANDOFF-*.md`, `CLAUDE.md`,
`AGENTS.md`, `.claude`, `.pneumatic`, `.working`, `.mcp.json` — the record
plus the tooling's working exhaust (override: `strip_paths`). The mirror is
created **private**; you make it public when you choose — the Action never does.

## Why

This Action serves a discipline where every deliberation is kept and
publication is a granular choice: ship the code, declare the record, choose
which records to publish. **Closed is still ahead of gone.**

Shipping and disclosing are two decisions; this Action lets them keep separate
clocks — open, digest, closed, **or not yet**. "Not yet" is a setting, not a
confession.

## The law

**The Action never changes repository visibility.** `create_if_missing`
creates a missing mirror **private**; there is deliberately no input that does
otherwise. Making a mirror public is the owner's own explicit, per-repo
decision. Build everything up to the flip; the flip is human.

- Syncs are **incremental and fast-forward**: prior mirror commits — and every
  link anyone made to them — stay reachable, forever. Only a **declared epoch**
  (`history_epoch: "new"`) rewrites and force-pushes, and the notice says so.
  The mirror is still output: work in the source, not the mirror.
- The Action copies tracked files outside `strip_paths` — **reviewing what
  crosses is the operator's job**, and once a mirror is public, each sync
  publishes its selected contents immediately. Defaults cannot know your
  repo's dialect: the first recorded trial found record-class files outside
  them (`proof/`). Dry-run first. And the contract is enforceable: declare
  `approved_paths` and **any kept path outside them stops the sync before
  anything is written**; a PUBLIC mirror refuses to push until they are
  declared (`docs/adr/0001`, QST-SYNC-CONSENT — fail-closed by design).

## Preview the mirror (dry run)

A **dry run** builds the complete mirror for inspection and pushes nothing to
the mirror repository. Previews make **no model calls** either: when digests
are enabled, their prompts are staged in place of summaries, so you read what
*would* be sent before anything is. Two forms:

- **Local**: `./dry-run.sh /path/to/repo owner/slug [out-dir]` — a snapshot
  preview; prints the strip report, the mirror's log, the notice, and the
  `out:` folder holding the full tree.
- **In CI**: `dry_run: "true"` — runs your configured build and uploads it as
  the `no-adrs-mirror` artifact (hidden files included — the rewritten `.git`
  history among them) in the workflow run's **Artifacts** section; nothing is
  pushed.

A recorded trial against `ADRs4AI/vscode-adrs4ai` (the ADRs-for-AI VS Code
extension — its record is two-thirds of its tree; full transcript:
`proof/2026-10-13-vscode-adrs4ai-dry-run.txt`):

```text
files:   455 kept · 884 withheld (that run's defaults; today's also
         withholds docs/continuity and docs/HANDOFF-*.md)
commits: 995 record-only · 644 code-only · 149 MIXED
history: snapshot → one commit, zero message leakage
digests: 45 staged (dry run — prompts recorded, no API call)
```

## Quick start

> **Wiring this with a model?** Have it load [`.claude/skills/no-adrs-mirror/SKILL.md`](.claude/skills/no-adrs-mirror/SKILL.md) — the wiring walkthrough: the dry-run-first ladder, the fail-closed gates, and the laws, kept true against `action.yml`.

```yaml
# .github/workflows/no-adrs-mirror.yml — on the PRIVATE source repo
on:
  push: { branches: [main] }
concurrency:            # racing pushes queue up; the newest wins — never two
  group: no-adrs-mirror #   concurrent rebuilds force-pushing over each other
  cancel-in-progress: true
jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with: { fetch-depth: 0 }     # filter mode needs full history
      - uses: ADRs4AI/no-adrs-mirror@v1
        with:
          token: ${{ secrets.MIRROR_TOKEN }}
          create_if_missing: "true"  # creates PRIVATE, always
          dry_run: "true"            # first run: preview only — nothing pushes
          # approved_paths: |        # required once the mirror is PUBLIC (fail-closed)
          #   src
          #   README.md
          # history_mode: filter   # keep code history; see Message tiers
```

1. Copy the snippet (or `workflows/mirror.yml` here, every knob shown) to
   `.github/workflows/no-adrs-mirror.yml`.
2. Add the `MIRROR_TOKEN` secret: a PAT or GitHub App token able to push to —
   and create — the mirror (the default `GITHUB_TOKEN` cannot push
   cross-repo). **It needs workflow authority too** (fine-grained: Contents
   *and* Workflows, Read and write; classic: `repo` + `workflow`): mirrors
   deliberately carry your live CI workflows, and GitHub refuses to push
   `.github/workflows/` without it. `ANTHROPIC_API_KEY` only for digests.
3. Push to `main`. The first run uploads a **preview artifact** — read it,
   then remove the `dry_run` line (or set it `"false"`): the mirror appears —
   private — at `<your-repo>-no-adrs`.

The Action is a wrapper around `mirror.py`, a single typed Python file —
stdlib only; `anthropic` and `git-filter-repo` are installed only when used.

**New to this? The [manual](docs/manual/README.md)** walks the whole path in
three sittings: [getting started](docs/manual/01-getting-started.md) (preview
first, always), [going public](docs/manual/02-going-public.md), and
[troubleshooting](docs/manual/03-troubleshooting.md) — every error our own
first runs hit, with its fix.

## The notice (what a mirror reader sees)

Counts from the receipted run; prose as `write_notice` writes it today:

```markdown
# Deliberations notice

This repository is a **mirror without its deliberation record** ("Closed
Deliberations" mode — ADRs-for-AI practice: https://adrs.systems). The record
exists: **45 ADRs** and **39 seeds** (early-stage records) are
maintained alongside the source at `ADRs4AI/vscode-adrs4ai` (source commit
`e4f821910bc1`), and were withheld from this copy together with 884 files
under: `docs/adr`, `docs/inbox`, `docs/vignettes`, …

These records are kept whole. The source maintainers retain them privately and
decide whether and when to release them — not at all, later, or gradually. The
disclosure decision keeps its own clock, and this notice declares, counts, and
gates it.

**Terms**: Access to the record is governed by the source repository's
maintainers; its license is decided separately from this code's.

**Citing the record**: each ADR has a canonical Address of the form
`adr://v1/repo/ADRs4AI/vscode-adrs4ai/adr/<number>#<anchor>`; a resolving
Address is the citation.

History mode: `snapshot`. Generated <UTC timestamp> by [no-adrs-mirror](https://github.com/marketplace/actions/no-adrs-mirror) 0.3.0.
```

## The four postures (no `mode` input — each is a configuration)

| Posture | What the mirror holds | How you get it |
|---|---|---|
| **none** | No mirror | Don't install the Action |
| **closed** | Code + the notice | The default run |
| **digest** | Code + notice + a model-written summary per ADR, each carrying its source's `adr://` Address | `digest: index` (one file) or `per-adr` (one per record), plus `anthropic_api_key` |
| **open** | Code + the record itself | Make the source repo public — no mirror needed |

The notice is never optional — the Action has no input that removes it. A
mirror that hid the record's *existence* would be a different product: keeping
reasoning and disclosing that you keep it are both features.

## History modes (why `snapshot` is the default)

Stripping the record from the *tree* does not strip it from *history*: commit
messages narrate the reasoning.

- **`snapshot`** (default): the kept files at source HEAD as **one commit**
  per sync — the first sync starts the mirror, each later one appends. No
  source history, no messages, nothing to leak.
- **`filter`** (via `git filter-repo`): code history kept; commits that only
  touched the record vanish *with* their messages. What survives is the
  **mixed commits** — code + record in one commit, the residual leak surface —
  which is why filter mode pairs with a message tier (below).

Both modes are **incremental by default**. Filter mode keeps a state branch
(`no-adrs-mirror/state`, in your **private** source) so each sync processes
only new commits: rewritten SHAs stay byte-stable across syncs, pushes are
plain fast-forwards, and links into the mirror never die. A full rebuild
happens only when you declare it (`history_epoch: "new"`) — and the notice
discloses which kind of sync produced it.

`python3 mirror.py report --source <repo>` prints your counts (the run above:
149 mixed) — the choice is measured, never assumed.

## Message tiers (filter mode: what surviving commits say)

| Tier | `message_mode` | Each surviving message becomes | Needs |
|---|---|---|---|
| 1 | `map` | Your supplied one-liner (e.g. model-written), keyed by original SHA; commits the map misses get tier 2 | `message_map`: a `{sha: line}` JSON you produce |
| 1.5 | `redact` | Original subjects with known tokens replaced by ‹…› — seat (agent) names, record ids, `adr://` Addresses, version tags. **Recall is bounded by the dictionary** | `redact_dict` from `dictgen` |
| 2 | `mechanical` | `type: update <top dirs> (N files)` — keeps the original's conventional-commit type (else `chore`); deterministic, no model | Nothing |
| 3 | `scrub` (default) | The constant line `code commit (message withheld)` | Nothing |

If the map has no entry for a commit, the `mechanical` message is used — never
the original text. `subject` and `keep` also exist for
terse-subject repos — though measured on our own repositories, even
*code-only* subjects carry deliberation; the default stays
`scrub`. The notice discloses the tier in use and the
map/dictionary hash. Build a dictionary with
`python3 mirror.py dictgen --registry agent-sessions.json --extra "<term>" --out dict.json`
(terms case-sensitive — seat names are often common words; patterns are not).

## Already public? Stars survive

Adopting this on an existing public repo doesn't cost its standing:

- **Stars travel.** Transferring a repository carries its stars, watchers, and
  issues, with permanent redirects from the old URL
  ([GitHub docs](https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository)).
- **The inverted flow keeps your public repo in place**: it *becomes the
  mirror target* — keeping its name, stars, issues — while a private clone
  becomes the deliberating source. Trade-offs:
  [`docs/adr/0004`](docs/adr/0004-inverted-adoption-converting-an-existing-public-repo.md).

## Inputs (the ones that matter)

| Input | Default | Notes |
|---|---|---|
| `token` | — **(required)** | PAT/App token able to push to and create the mirror, **with workflow authority** (mirrors carry live CI); `GITHUB_TOKEN` cannot push cross-repo |
| `mirror_repo` | `<owner>/<repo>-no-adrs` | Target repository |
| `strip_paths` | the 12 defaults above | Newline-separated paths/globs to withhold (setting this replaces the whole list) |
| `additional_strip_paths` | — | Newline-separated paths/globs **added** to the list — withhold more without re-declaring the defaults |
| `approved_paths` | — | Fail-closed consent roots: kept files outside them stop the sync; **required once the mirror is public** |
| `history_mode` | `snapshot` | or `filter` |
| `history_epoch` | `auto` | incremental whenever state allows; `"new"` DECLARES a full rebuild (force-push, said in the notice) |
| `message_mode` | `scrub` | filter mode only: `map` / `redact` / `mechanical` / `scrub` / `subject` / `keep` |
| `message_map` | — | `map`: repo-relative path to the `{sha: line}` JSON |
| `redact_dict` | — | `redact`: repo-relative path to `dictgen` output |
| `digest` | `none` | `index` / `per-adr`; requires `anthropic_api_key` |
| `digest_model` | `claude-sonnet-5` | each digest records model, prompt hash, timestamp |
| `disable_workflows` | — | filenames moved to `.github/workflows-disabled/` (publish/release workflows; keep test/lint live) |
| `terms` | see `action.yml` | one sentence: the notice's **Terms** line |
| `create_if_missing` | `false` | creates **private**, always |
| `dry_run` | `false` | build + upload as a workflow artifact; push nothing |

Fine-tuning (`digest_effort`, `digest_style`, `digest_glob`, `digest_prompt`,
`digest_prompt_text`, `python_version`): input-by-input in [`action.yml`](action.yml).

## License and provenance

The Action is Apache-2.0 ([`LICENSE`](LICENSE)); files it generates **into
your mirror** belong to the mirror's owner
([`MIRROR-OUTPUT-NOTE.md`](MIRROR-OUTPUT-NOTE.md)). Design: ADR-0034 of the
maintainers' own deliberation record — kept closed, exactly the practice this
Action serves — and `docs/adr/` here. Built 2026-08-26;
productionized 2026-10-13; first live trial 2026-10-17 (`proof/`).
Tests: `tests/test_mirror.py`. The digest prompt is
`prompts/adr-digest.md`; every digest records model, prompt hash, and
generation time — digests are pointers to the record, never substitutes for it.
