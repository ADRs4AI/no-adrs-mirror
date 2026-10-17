# First live trial — ADRs4AI/vscode-adrs4ai → ADRs4AI/vscode-adrs4ai-no-adrs (PRIVATE)

- **Date**: 2026-10-17 · **Operator**: Covenant 5 (Claude Fable 5), at the founder's step-3 word: *"pick a repo of our constellation that is still private, and trial the action and make the NO-adrs mirror PRIVATE AS WELL."*
- **Source**: fresh clone of `ADRs4AI/vscode-adrs4ai` at `a036144f9c70` (origin state, never a live worktree)
- **Command pair**: `mirror.py build --history snapshot --digest none` → `mirror.py push --mirror ADRs4AI/vscode-adrs4ai-no-adrs --create`

## Results (verified from the GitHub API, not the tool's own output)

| Check | Result |
|---|---|
| Mirror visibility | **PRIVATE** (`gh repo view --json visibility`) |
| History | **1 commit** (`repos/.../commits` length) — snapshot, zero message leakage |
| Notice | `DELIBERATIONS-NOTICE.md` present, 831 bytes |
| Strip (defaults) | `docs/adr`, `docs/inbox`, `docs/vignettes`, `docs/handoffs`, `CLAUDE.md`, `AGENTS.md`, `.claude`, `.pneumatic` — all absent |
| Source leak metric | 149 mixed · 1001 record-only · 647 code-only commits (none carried; snapshot) |
| The law, at runtime | `created ADRs4AI/vscode-adrs4ai-no-adrs PRIVATE — flipping it public is the owner's own act, by design` |

## The finding (the trial's real yield)

**The default strip list under-strips this repository.** Surviving `docs/` entries include record-class material kept outside the conventional paths: `PRIVACY-THOUGHTS.md`, `JEREMIE-TODO.md`, `CREW-LEGACY.md`, `LAUNCH-COPY-velocity-and-honesty.md`, `QST-DETECTION-LEDGER.md`, `SPRINT-PLAN.md`, `theory/`, `handbooks/`, `submissions/`, `research/`. A crew that thinks on disk thinks *everywhere* — defaults cannot know a given repo's dialect.

**Consequence** (feeds ADR-0001's profile seam and Kintsugi's review directly): a record-heavy repo requires a **per-repo withhold profile** (`kintsugi.yaml` `profiles: public-mirror:` — Kintsugi's standing ruling, now with its first empirical proof) before any mirror of it could ever be considered for a flip. The mirror being private-by-law is what made this finding free: the under-strip was discovered with zero exposure — which is the trial design working exactly as the founder specified it.

**Disposition**: the trial mirror stays as-is, private, as the specimen; the re-run with a vscode-specific profile is the next trial, after the profile seam lands.
