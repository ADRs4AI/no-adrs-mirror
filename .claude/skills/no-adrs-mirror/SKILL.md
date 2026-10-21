---
name: no-adrs-mirror
description: Use when a human wants a repository's code public (or shareable) while its deliberation record — ADRs, inboxes, CLAUDE.md — stays private: wiring the no-adrs-mirror GitHub Action. Covers the dry-run-first ladder, the fail-closed consent gates, history/message/digest modes, and the one law — the Action never changes visibility; the flip is always the owner's.
---

<!-- skill version: tracks action.yml in this same repo — teach ONLY what that file's inputs say; on divergence, action.yml wins and this file has rotted. -->

# Wiring no-adrs-mirror: ship the code, withhold the record, say so

A GitHub Action for a **private** repo: each push rebuilds a second repo — the mirror — with the same code, the record paths removed, and one generated file, `DELIBERATIONS-NOTICE.md`, stating what exists and was withheld. Shipping and disclosing keep separate clocks; "not yet" is a setting, not a confession. You, the seat, wire it; the two acts that are never yours: creating the token, and making anything public.

## The ladder — wire in this order, never skip ahead

1. **Dry run first.** `dry_run: "true"` builds the tree and uploads it as a workflow artifact (dotfiles and rewritten `.git` included) instead of pushing. No token needed; digest prompts are staged, never sent.
2. **Read the artifact as a stranger.** Code present? Record absent? `DELIBERATIONS-NOTICE.md` honest? If digests are on: read the staged prompts — that is exactly what would egress.
3. **Go live, private.** Add the token (step below), set `create_if_missing: "true"` — the mirror is created **PRIVATE, always**; the Action deliberately offers no way to make it public.
4. **Declare `approved_paths` now, from what you reviewed** — the top-level roots kept files may live under. It is the fail-closed consent gate for the public era: a PUBLIC mirror with no `approved_paths` never receives a push (the failure prints the roots it would need). Declaring them at review time means the first post-flip sync doesn't stop.
5. **The flip is the owner's own click** on the mirror repo — never yours, never the Action's. Offer the moment; never perform it.

## The minimal workflow (in the PRIVATE repo, `.github/workflows/mirror.yml`)

```yaml
name: mirror
on:
  push:
    branches: [main]
permissions: { contents: write }   # filter mode persists state to this repo
concurrency: { group: no-adrs-mirror, cancel-in-progress: true }
jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0        # filter mode needs history; harmless for snapshot
      - uses: ADRs4AI/no-adrs-mirror@v1
        with:
          token: ${{ secrets.MIRROR_TOKEN }}
          create_if_missing: "true"
          # dry_run: "true"     # ← the ladder's step 1: start with this line on
```

**The token** (the human's act — walk them, never absorb it): the default `GITHUB_TOKEN` cannot push to another repository. They create a fine-grained PAT (or GitHub App token) able to push to — and, with `create_if_missing`, create — the mirror, and paste it into the private repo's secrets as `MIRROR_TOKEN`. Secret box only; if it ever appears anywhere else, revoke and remint. An empty token fails the preflight with teaching, before anything builds.

## The decisions, grouped (defaults are the honest ones)

- **What is withheld**: `strip_paths` defaults to the record plus the tooling's working exhaust (`docs/adr`, `docs/inbox`, `docs/vignettes`, `docs/handoffs`, `docs/continuity`, `docs/HANDOFF-*.md`, `CLAUDE.md`, `AGENTS.md`, `.claude`, `.pneumatic`, `.working`, `.mcp.json`). To withhold more, use `additional_strip_paths` — additive, so the defaults never need re-declaring.
- **History**: `history_mode: snapshot` (default — one commit per sync, no source history, no message leaks) or `filter` (code history kept, record-only commits pruned with their messages). **Both are incremental**: syncs fast-forward and prior mirror SHAs stay stable (filter keeps a `no-adrs-mirror/state` branch in the private source); only a DECLARED `history_epoch: "new"` rewrites and force-pushes. Filter mode brings `message_mode`, default `scrub` — measured on this house's own repos, even code-only commit *subjects* carry deliberation. The degrade law: a commit the map doesn't cover degrades DOWN in warmth (to mechanical), never to its original text; a missing companion file fails the build.
- **Digests** (`digest: index | per-adr`): model-written summaries of the withheld record, into the mirror. Needs `anthropic_api_key` as a secret. In dry runs, prompts are staged beside the artifact instead of sent — read them before going live.
- **Workflows**: the calling workflow is auto-disabled in the mirror (a mirror must not mirror the mirror); list publish/release workflows that need absent secrets in `disable_workflows`. Test and lint workflows should stay live — green checks on public code are part of the trust story.
- **The notice's terms line**: `terms` — one sentence on how the record can be requested. The default says maintainers decide; say something truer if something truer exists.

## The laws (quote these when a human asks "can it just…")

- **The Action never changes repository visibility.** Mirrors are born private; going public is the owner's explicit, per-repo act, and the Action offers no input for it.
- **Unknown stops.** If the mirror's visibility cannot be determined, the push halts — unknown never means "private". (One safe unknown: target absent + `create_if_missing` — creation is private by construction.)
- **Public + no `approved_paths` = no push**, and the failure names the roots a deliberate approval would need.
- Every input reaches the shell via `env`, never textual substitution — the quote() injection class, closed by construction.

## Verify (each rung has its check)

Dry run: the artifact holds the code, none of the record paths, an honest NOTICE. Live private: same checks on the mirror repo itself. After the owner's flip: the next push lands green with `approved_paths` declared — and the NOTICE is now the public's first page of the story.

---

*Written 2026-10-20 by Shipwright 5 (Claude Fable 5, ADRs4AI HQ), at the founder's question "should no-adrs-mirror come with its own skill?", against this repo's `action.yml` and `README.md` of the same day. The tool's own record lives in `docs/adr/`; this skill is the wiring walkthrough, not the design history.*
