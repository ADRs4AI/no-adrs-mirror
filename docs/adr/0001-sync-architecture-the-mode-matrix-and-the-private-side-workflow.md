# ADR-0001: Sync architecture — the mode matrix and the private-side workflow

- **Date**: 2026-10-15
- **Iteration**: 2
- **Status**: Draft
- **Deciders**: Jérémie Lumbroso (rights-holder; sketch author); Covenant 5 / Claude Fable 5 (author, licensing lane); coordinates: Kintsugi 5 (strip/include profiles), Operator 5 @ lumbroso-hq (readback surface)

**TL;DR**: The mirror gains a second publishing dimension — **(none / closed / digest / open) × (one-shot / synced)** — and synced mode is implemented exactly as the rights-holder sketched it: a workflow living on the **private** repo, holding a secret scoped to only the mirror, re-publishing on every push. The Action never performs a visibility act in either mode.

## Context

The founder's sketch (2026-10-13 dictation, this repo's founding seed): *"a workflow that's put on the private repo with a token to the public repo? And it pushes … every time there's an update it synchronizes."* Confirmed sound here and by Operator's same-hour read. The one-shot engine already exists and is proven (`mirror.py`, 10/10 tests, dry-run proof in `../mirror-action-staging/proof/` at HQ and `proof/` here); this ADR fixes the architecture synced mode must honor before any v2 code lands.

## Decision (proposed)

1. **The workflow lives on the private repo** — never the mirror. The mirror holds no secrets, no workflow, no write path back; it is write-only from the private side's bot identity. This direction-of-trust is load-bearing: the private repo is the source of truth (the founder's own pattern), and a mirror that could reach back into its source would invert it.
2. **The secret is minimal**: a fine-grained PAT or deploy key scoped to exactly one repository — the mirror — with contents:write only. Never a classic PAT, never org-wide. The README documents this as the security story, in plain words.
3. **Trigger**: `on: push` to the published branch (plus `workflow_dispatch` for manual re-syncs). Every push re-builds and force-pushes the mirror per the mode's history rule (ADR-0002 owns what "history" means in synced mode).
4. **The mode matrix is the product's whole surface**, and both dimensions stay orthogonal: what ships (none/closed/digest/open) × how often (one-shot/synced). `action.yml` expresses this as two inputs, not a combined enum.
5. **The engraved law holds in every cell**: `create_if_missing` creates **private, always**; no input can create or flip public; the flip is the owner's own act, per-repo, forever. Marketplace convenience never relaxes this (the founder's 10-11 law; restated at his 10-15 premium ruling).

## Questions

### QST-TOKEN-KIND: Fine-grained PAT or deploy key as the documented default?
- Status: unresolved — RETRACTED from the founder's surface 2026-10-17 (Parallax's review proved the A/B framing incoherent: `create_if_missing` needs more authority than contents:write, a credential cannot pre-scope to a repo that doesn't exist, deploy keys are SSH while the code speaks HTTPS+`gh` — so "the Action's code is identical either way" was false, owned by the author). Back to the build bench: the repair is a bootstrap-vs-steady-state split (human creates the mirror, then installs an exact-repo write credential; creation stays an advanced path with separately named temporary authority). Re-stake for Jérémie only if a genuine preference question survives the repair.
- Why asking: the README's security story teaches one happy path; adopters copy it verbatim.
- Need: (parked — see Status)

Options:
- **A — Fine-grained PAT (repo-scoped, contents:write).** One UI, expiry dates enforce rotation, visible in the token dashboard.
- **B — Deploy key (per-mirror SSH key, write-enabled).** No account-wide surface at all; key lives on exactly one repo; no expiry pressure.
- **C — Document both, PAT first.** Fuller, slightly heavier page.

**Recommendation**: (by Claude Fable 5)
**A — fine-grained PAT, with B as the appendix for key-minded keepers.** *Rationale*: PATs carry enforced expiry (rotation by default — exactly what this month's estate-wide Postmark token death taught), the fine-grained scoping UI makes "exactly one repo, contents:write" checkable at a glance, and Marketplace adopters expect the PAT idiom. *Confidence*: 0.7. *If wrong*: if his infra preference is keys-everywhere, B leads and the PAT becomes the appendix — the Action's code is identical either way.

**ANS:** (by Jérémie)
[Fill this in]   <!-- literal placeholder — parser-significant, do not paraphrase -->

---

### QST: Sync trigger — every push, or batched?
- Status: deferred — design default chosen (`on: push` + manual dispatch); revisit only if a real adopter hits rate or noise limits
- Why asking: batching (cron) trades freshness for quiet; nothing today needs it.

**ANS:** (by Covenant 5)
[Fill this in]   <!-- literal placeholder — parser-significant, do not paraphrase -->

---

### QST-SYNC-CONSENT: What does the one-time public flip authorize — every future unclassified path, or only approved roots?
- Status: answered — by the rights-holder, in-file, 2026-10-18
- Why asking: the live trial already proved defaults cannot infer a repo's dialect (record-class files found throughout kept paths); the same blindness applies forward in time to every file not yet written.
- Need: pick a letter (or override — any shape answers)

Options:
- **A — Denylist continuity.** Every future unstripped path publishes automatically; the flip is standing consent to the policy's complement, forever.
- **B — Fail-closed classification.** The owner approves stable public roots (`src/**`, `tests/**`, chosen docs); new paths outside them STOP the sync pending review; withholds stay as defense in depth.

**Recommendation**: (by Claude Fable 5, concurring with Parallax at 0.9)
**B — fail-closed.** *Rationale*: this is the gated-mode trust posture applied to the tool's own output boundary — "what may cross" should be a first-class contract, not the complement of a filename list; approving roots once keeps it one decision rather than one click per file, and a stopped sync is a cheap, legible failure where a leaked path is an irreversible one (the reversibility asymmetry that governs this whole lane). *Confidence*: 0.85. *If wrong*: real adopters show a complete public-root profile is less reviewable than the denylist — then A with a mandatory new-path report in the sync log, which preserves the review moment without the stop.

**ANS:** (by Jérémie Lumbroso)
Yes, approving Option B. Fail-closed, such that specific files must be opted-in, potential by the models building themselves. The documentation for this needs to be clearly accessible, i.e., in the `$GITHUB_STEP_SUMMARY` or something like that, and maybe the fail-close emits a message towards documentation (perhaps even of the associated handbook, cc: Pharos 5 of ADRs4AI).

---

### QST-DIGEST-APPROVAL: May a changed digest publish unattended, or does it stage for human approval?
- Status: answered — by the rights-holder, in-file, 2026-10-18
- Why asking: *"A model may draft the public boundary, but should not silently become the authority that moves it"* (Parallax). The digest's one permitted verbatim sentence and preserved names are exactly the content whose publication wants a human moment; this is the mirror-scale instance of the house's own publication gate.
- Need: pick a letter (or override — any shape answers)

Options:
- **A — Unattended.** Digest mode enabled means every regenerated digest publishes on the next sync.
- **B — Staged by default.** Unchanged approved digests republish freely (cached); a CHANGED digest stages for the owner's approval; a repo may explicitly opt into unattended publication under a recorded policy.

**Recommendation**: (by Claude Fable 5, concurring with Parallax at 0.9)
**B — staged by default, opt-in to unattended.** *Rationale*: it is the digest-as-duty design (the gated mode's own shape: disclosure mandatory, text at the owner's tempo) carried to the artifact level; caching makes the steady state zero-touch, so the approval moment costs attention only when the boundary actually moved — which is precisely when attention is owed. *Confidence*: 0.85. *If wrong*: a record class with a human-approved prompt + validator demonstrating every permissible output is pre-authorized — then A for that class, recorded.

**ANS:** (by Jérémie Lumbroso)
Yes, Option B sounds about right: Staged by default, with the ability to opt-in to automation. Additionally the approval process should be seamless. I think on GitHub requiring a human approver to gate a workflow is one way to do it? I wonder if it's the most seamless? Probably? The most normal?

---

## Action Items

- [ ] **Fail-close must teach where the runner reads** (his SYNC-CONSENT ANS): a stopped sync writes the unclassified-path list + the remedy into `$GITHUB_STEP_SUMMARY`, and the message links the handbook's consent page — handbook anchor: Pharos 5 (docsite commission) — Owner: Covenant 5
- [ ] **Digest staging mechanism** (his DIGEST-APPROVAL ANS): GitHub-native — the publish step runs in an `environment` with required reviewers, so approval is one click in GitHub's own UI (the most normal shape; his instinct confirmed) — Owner: Covenant 5
- [ ] v2: `sync` input (`one-shot` default | `synced`) + the private-side workflow template for synced mode — Owner: Covenant 5
- [ ] README security story (token scoping, per QST-TOKEN-KIND's answer) — Owner: Covenant 5
- [ ] Strip/include profile home in `kintsugi.yaml` zones (revival on the history word) — Owner: Kintsugi 5

## Iterations

- **Iteration 7** (2026-10-21, Covenant 5 / Claude Fable 5): **the two-phase engine PROVEN LIVE on the hosted pair** — epoch run `39611503523` (tip `318faa0`) then incremental run `39611624870` (phase `incremental`, tip `a01cb82`, **no force**), state round-tripping through the hosted source, ancestry verified by merge-base: the epoch tip is reachable from the incremental tip, the sync merge commit reading exactly as designed ("previous tip preserved as a parent — fast-forward by construction"). **Four defect classes were caught by the live attempts themselves, each now a guard + a documented requirement on `v1`**: (1) bare-runner git identity (CI caught; identity set before filtering); (2) credential scoping (a global insteadOf routed source access through the mirror-scoped token — 403; the token now rides only the state-objects URL, and the push step unsets its rewrite); (3) the read-only default `GITHUB_TOKEN` (filter mode needs `permissions: contents: write` to persist state — fails LOUD with the stanza, documented in snippet/drop-in/skill/manual); (4) **tags**: the source's 40 release tags minted 40 target-only marks (objects that never reach the mirror — phase B died validating them), traced through the state branch's mark files; `--no-tags` closes the crash AND a leak class in one flag, since annotation messages bypass every message tier (tags-with-their-own-tier recorded as the designed future feature). 26/26 sandbox incl. the side-branch and secret-bearing-tag kill tests. Remaining for full rigor: the resettable fixture-repo integration run (his token setup).
- **Iteration 6** (2026-10-21, Covenant 5 / Claude Fable 5): **the incremental engine, at his word — and the mission sentence, banked verbatim**: *"the no-adrs-mirror needs to be perfect in execution, testing and manual — it's the tricycle version of deliberative programming for experienced programmers — where nobody will make fun of you, I really think nailing this is a big part of the solution."* His ruling: incremental ASAP ("that's what most people will expect"), even for the manual/dispatch posture, snapshot staying the shipped default. **Built (v0.4.0)**: both modes incremental by default — filter via the ADR-0002 two-phase engine (see its checked item), snapshot via the same fast-forward merge construction; `history_epoch: "new"` is the only path to a rewrite, and the notice discloses which kind of sync it was. One composition subtlety the sandbox caught before any live repo did: a clone keeps non-HEAD branches as remote refs while filter-repo suffix-matches them — detection and the tool could disagree about whether state existed; the exact ref is now materialized and probed fully qualified. Also this sitting, his notes: dep actions bumped v4/v5→v7 (the Node-20 deprecation he pasted), the notice self-reference is a Marketplace link in every mirror, the per-rule removal log in `$GITHUB_STEP_SUMMARY`, the human manual (`docs/manual/`), `concurrency` guards in every shipped snippet (his parallel-calls question — nothing guarded races before it), and the integration harness awaiting his two fixture repos + non-expiring token. The specimen stays dispatch-only until the live integration proof passes; then `on: push` becomes honest.
- **Iteration 5** (2026-10-20, Covenant 5 / Claude Fable 5): **Parallax's second look folded — "the HOLD narrows; it does not yet clear," and four of its exit conditions are now CODE (v0.3.0, 22/22 with three new kill tests).** Their confirmed-closed list (license/v1 identity, name/copy truth, additive strips, no-egress preview, current-tree consent, workflow-disable mechanism, token preflight) stands as the receipt of the week's work. Implemented this fold: (1) **snapshot builds from `git archive HEAD`** — the symlink-materialization and dirty-worktree escapes are dead (kill tests pinned; ADR-0002's archive item checked off); (2) **filter-mode consent now classifies the union of every path that EVER existed** (their gap 2.2; kill test: add-then-delete outside-root path trips the gate); (3) **unknown target visibility fails closed** (their gap 2.1; the one safe unknown: absent target + create_if_missing, private by construction); (4) **the calling workflow is auto-disabled in the mirror by construction** (`GITHUB_WORKFLOW_REF` basename — no adopter memory test); (5) the dry-run artifact now carries the staged digest prompts, making the README's "read what would be sent" true. **Specimen posture per their rail 4**: the vscode workflow is `workflow_dispatch`-only — each rebuild a deliberate phase-A epoch, continuous on-push filter rewriting OFF until phase B lands; its `approved_paths` is the REVIEWED historical union (receipt: seven historical `*.vsix` build artifacts stripped; all other tops approved). **Still open, named, owned**: approval-to-policy-hash binding (manifest + renewed-approval-on-change), the two-phase engine itself (ADR-0002), the digest generate/stage/publish split (their full exit condition recorded there), notice printing raw custom strip names, the contribution-interim sentence, and the "resolving Address" wording on private targets. The sample flip stays HELD on their receipt logic until the rebuilt target exists and is inspected — no new founder question, by their own verdict.
- **Iteration 4** (2026-10-19, Covenant 5 / Claude Fable 5, the founder's "Yes, make those fixes"): **QST-SYNC-CONSENT's answer B is ENFORCED, not just designed — v0.2.0.** (1) `check_approved()` in the engine: declared approved roots gate every build fail-closed, BEFORE anything is written; a kept path outside them stops the sync naming the new top-level entries (regression-tested both ways). (2) The action's push step adds the **bootstrap half**: a PUBLIC mirror with no `approved_paths` never receives a push — the step fails and prints exactly the roots a deliberate approval would need; private mirrors stay ungated (publication is the boundary, staging stays free; dry runs never gate). (3) **Additive strip semantics landed** (Parallax's P0.1): `additional_strip_paths` input + `--additional-strip` CLI flag append to the base list instead of replacing it — the replacement trap is closed, tested. (4) The staged-digest mechanism (QST-DIGEST-APPROVAL B) is documented where operators build: the drop-in workflow carries the `environment: mirror-publish` + required-reviewers recipe — enforcement by GitHub environment, the mechanism his answer named. (5) README reordered per Sounder 6's consult (act-fast path before configuration depth; content-preserving, scripted, receipted). Remaining open rails after this iteration: filter-state persistence (the two-phase engine arc) and digest-staging *wiring* beyond the documented environment pattern.
- **Iteration 3** (2026-10-19, Covenant 5 / Claude Fable 5): **the machinery-exhaust strip ruling, his verbatim**: *"One of the thing that should be stripped automatically are the pneumatic reporting folders, the . folders — I'm not sure about the kintsugi.yaml and lock files, since that role models our tooling."* — citing `adr://v1/repo/ADRs4AI/vscode-adrs4ai/adr/0023#qst-publicworking` (committed `.working/` vs born-public repos; Lintel's incident there proved visibility is not a stable property a policy can key on). **The mirror is that dilemma's answer**: the private repo keeps its committed substrate whole (the completist reversal intact), and the mirror strips the exhaust class on the way out — no visibility-keyed template rule needed. **Executed**: `DEFAULT_STRIP` += `.working` (drafts + error ledgers, the exact files in vscode's incident) and `.mcp.json` (machine paths, commands); `.claude`/`.pneumatic` already present; pneumatic's report stream (`docs/inbox/reports.jsonl`) rides the existing `docs/inbox` entry. **Deliberately NOT stripped: `kintsugi.yaml` + `kintsugi.lock`** — his hesitation recorded, not resolved ("role models our tooling"): the manifest visible in a mirror shows adopters the bill of materials; they stay until his final word, and the engraving sits beside `DEFAULT_STRIP` in the code. Note for strangers, now in the README's inputs row: setting `strip_paths` **replaces** the whole default list (the additive-semantics redesign remains the v2 item, Parallax's P0.1).
- **Iteration 2** (2026-10-17, Covenant 5 / Claude Fable 5): **first live trial executed at the founder's step-3 word** — `ADRs4AI/vscode-adrs4ai` → `ADRs4AI/vscode-adrs4ai-no-adrs`, mirror created **private** by the engine's own law (the runtime line printed it), 1 commit, notice present, all API-verified (`proof/2026-10-17-first-live-trial-vscode-adrs4ai.md`). **Finding**: the default strip list under-strips record-heavy repos — vscode keeps deliberation-class files outside the conventional paths (`PRIVACY-THOUGHTS.md`, `theory/`, `handbooks/`, …). Consequence for this ADR: the per-repo withhold profile (`kintsugi.yaml` zones, decision point 4's seam) is **required, not optional, before any flip of a record-heavy repo's mirror** — first empirical proof of Kintsugi's one-home ruling; folded into their review ask the same day. Also this day: the founder's mission sentence for the tool staked in the seed's Thread ("…mediate, granularly, what is public and not"), and the four-seat review round commissioned (Pharos, Parallax, Shipwright, Kintsugi).
- **Iteration 1** (2026-10-15, Covenant 5 / Claude Fable 5): staked from the founding seed under the founder's premium ruling ("one of the main tools of our toolkit" — Operator's `1340`); the sketch confirmed as the architecture; the visibility law restated as a design invariant that Marketplace convenience never relaxes.
