# no-adrs mirror

**Publish a repository's code without publishing its reasoning.**

Projects built the ADRs-for-AI way keep a *deliberation record* — ADRs, seeds,
inboxes, the working apparatus of human–AI collaboration — alongside their code.
Sometimes the code is ready to be public before the record is. This action
produces and maintains a **mirror repository** (`<your-repo>-no-adrs`) that
carries the code, omits the record, and says so honestly: Every mirror ships a
`DELIBERATIONS-NOTICE.md` declaring that the record exists, how large it is,
what was withheld, and how to cite it.

The point is *poise*: The private repository stays the source of truth, the
mirror stays ready, and opening the record later is one decision — not a
migration.

## The modes

| Mode | What ships | What it says |
|---|---|---|
| **none** | Nothing — no mirror | The default state of any private repo |
| **closed** | Code + the notice | "A record exists; it is withheld" |
| **digest** | Code + notice + a model-written summary per ADR, each carrying its source's canonical `adr://` Address | "Here is the shape of the record; the Address is the citation" |
| **open** | Code + the record itself | No mirror needed — flip the source repo |

The notice is not optional. A mirror that hides the record's *existence* would
be a different product; this one is built on the claim that keeping reasoning
and disclosing that you keep it are both features.

## The law

**The Action never changes repository visibility.** It creates a missing
mirror **private**, and there is deliberately no input that does otherwise.
After you make a mirror public, each successful sync publishes its newly
selected contents immediately — which is why *what may cross* is a reviewed
contract (see `docs/adr/0001`, QST-SYNC-CONSENT), never just the complement of
a filename list. Making a mirror public is a visibility act reserved to the
repo owner's own explicit, per-repo decision. Build everything up to the flip;
the flip is human.

## Live demo (real numbers)

Dry-run against `ADRs4AI/vscode-adrs4ai` (the ADRs-for-AI VS Code extension,
a repository whose record is two-thirds of its tree):

```
files:   443 kept · 872 withheld (docs/adr, docs/inbox, docs/vignettes,
         docs/handoffs, CLAUDE.md, AGENTS.md, .claude, .pneumatic — the
         defaults as of that run; current defaults also withhold
         docs/continuity and docs/HANDOFF-*.md)
commits: 975 record-only · 617 code-only · 149 MIXED
history: snapshot → one commit, zero message leakage
digests: 44 staged (dry-run; each carries adr://v1/repo/ADRs4AI/vscode-adrs4ai/adr/<n>)
```

Run it yourself — one command, local only, nothing pushed, no API call:

```bash
./dry-run.sh /path/to/source-repo owner/slug
```

## The mixed-commit metric (why `snapshot` is the default)

Stripping the record from the *tree* does not strip it from *history*: Commit
messages narrate the reasoning. `filter` mode (via `git filter-repo`) prunes
record-only commits *with* their messages — but **mixed commits** (code + record
in one commit) survive, and their messages leak. Measured on real repositories,
even *code-only* commit subjects carry deliberation in projects that practice
this methodology seriously. So:

- **`snapshot`** (default): one commit, no history, no leakage. Honest always.
- **`filter` + `scrub`**: code history preserved, every surviving message
  replaced. Honest, at the cost of narrative history.
- `filter` + `subject`: offered for repos with disciplined terse subjects —
  the `report` subcommand prints your mixed-commit count so the choice is
  measured, never assumed.

## Message tiers (what surviving commits say)

Filter mode keeps real history; these tiers decide what each surviving commit's
message becomes. Safety-ordered, and the degrade law is fixed: **messages may
degrade down in warmth, never in privacy** — when a better tier is unavailable,
the engine falls to `mechanical`, never to the original text.

| Tier | Mode | What you get | Needs |
|---|---|---|---|
| 1 | `map` | Model-written neutral one-liners (ConventionalCommit form), keyed by original SHA; unmapped survivors fall back to tier 2 | A map file (model access to produce it) |
| 1.5 | `redact` | Original subjects with known tokens replaced by ‹…› — names (from registries), record ids, handles, Addresses, version tags. **Recall is bounded by the dictionary**; best for terse-conventional repos | `dictgen` output |
| 2 | `mechanical` | `type: update <paths> (N files)` — deterministic, zero egress, byte-verifiable by anyone | Nothing |
| 3 | `scrub` | One constant line | Nothing (explicit opt-in; it reads like redaction bars) |

The notice discloses the tier and its provenance (map/dictionary hash), so a
reader always knows which kind of message they are reading. Build a dictionary
with `mirror.py dictgen --registry agent-sessions.json --extra "<term>" --out dict.json`;
terms match case-sensitively (seat names are often common words), patterns
(ids, handles, Addresses) match case-insensitively.

## The notice (what a mirror reader sees)

```markdown
# Deliberations notice

This repository is a **mirror without its deliberation record** ("Closed
Deliberations" mode). The record exists: **44 ADRs** and **39 seeds** are
maintained alongside the source at `ADRs4AI/vscode-adrs4ai` (source commit
`8bbb7e5b9e71`), and were withheld from this copy together with 872 files.

**Terms**: Access to the record is governed by the terms published at
https://adrs.systems.

**Citing the record**: each ADR has a canonical Address of the form
`adr://v1/repo/<owner>/<repo>/adr/<number>#<anchor>`; a resolving Address is
the citation.
```

## Quick start

The whole integration is one step — a call to this action (which is, at
bottom, a robust wrapper around `mirror.py`, a single typed Python file you
can read in one sitting):

```yaml
# .github/workflows/no-adrs-mirror.yml — on the PRIVATE source repo
on:
  push: { branches: [main] }
jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }        # filter mode needs full history
      - uses: ADRs4AI/no-adrs-mirror@v1
        with:
          token: ${{ secrets.MIRROR_TOKEN }}
          create_if_missing: "true"      # creates PRIVATE, always
          history_mode: filter
          messages: mechanical           # or map / redact — see Message tiers
          disable_workflows: |           # publish workflows never run in a mirror
            release.yml
```

`workflows/mirror.yml` in this repo is the same thing with every knob shown.

1. Copy `workflows/mirror.yml` into your repo as
   `.github/workflows/no-adrs-mirror.yml` (or start from the snippet above).
2. Add the `MIRROR_TOKEN` secret (PAT or App token able to push to the mirror;
   the default `GITHUB_TOKEN` cannot push cross-repo). Add `ANTHROPIC_API_KEY`
   only if you want digests.
3. Push to `main`. The mirror appears — private — at `<your-repo>-no-adrs`.

## Inputs (the ones that matter)

| Input | Default | Notes |
|---|---|---|
| `mirror_repo` | `<this-repo>-no-adrs` | Target `owner/repo` |
| `strip_paths` | the record + apparatus | Newline-separated paths/globs |
| `history_mode` | `snapshot` | or `filter` (see the metric above) |
| `message_mode` | `scrub` | filter mode only: `keep` / `subject` / `scrub` |
| `digest` | `none` | `index` / `per-adr`; requires `anthropic_api_key` |
| `digest_model` | `claude-sonnet-5` | model, prompt-hash, timestamp recorded per digest |
| `create_if_missing` | `false` | creates **private**, always |
| `dry_run` | `false` | build + upload artifact; push nothing |

## Provenance

Engine and design: HQ `adr:0034` (the Open Deliberations charter) — built
2026-08-26, live-verified 2026-10-11/12, productionized 2026-10-13. Tests:
`tests/test_mirror.py` (pytest). The digest prompt is `prompts/adr-digest.md`
and every digest records the model, the prompt's hash, and the generation time
— digests are pointers to the record, never substitutes for it.
