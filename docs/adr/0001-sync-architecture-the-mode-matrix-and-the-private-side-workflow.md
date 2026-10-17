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
- Status: unanswered — NEW founder-ball from Parallax's cross-vendor review (P0.2, 2026-10-17): once a mirror is public, every successful sync is a publication act, and today the denylist's complement publishes automatically — a filename the policy has never classified ships the moment it exists
- Why asking: the live trial already proved defaults cannot infer a repo's dialect (record-class files found throughout kept paths); the same blindness applies forward in time to every file not yet written.
- Need: pick a letter (or override — any shape answers)

Options:
- **A — Denylist continuity.** Every future unstripped path publishes automatically; the flip is standing consent to the policy's complement, forever.
- **B — Fail-closed classification.** The owner approves stable public roots (`src/**`, `tests/**`, chosen docs); new paths outside them STOP the sync pending review; withholds stay as defense in depth.

**Recommendation**: (by Claude Fable 5, concurring with Parallax at 0.9)
**B — fail-closed.** *Rationale*: this is the gated-mode trust posture applied to the tool's own output boundary — "what may cross" should be a first-class contract, not the complement of a filename list; approving roots once keeps it one decision rather than one click per file, and a stopped sync is a cheap, legible failure where a leaked path is an irreversible one (the reversibility asymmetry that governs this whole lane). *Confidence*: 0.85. *If wrong*: real adopters show a complete public-root profile is less reviewable than the denylist — then A with a mandatory new-path report in the sync log, which preserves the review moment without the stop.

**ANS:** (by Jérémie)
[Fill this in]   <!-- literal placeholder — parser-significant, do not paraphrase -->

---

### QST-DIGEST-APPROVAL: May a changed digest publish unattended, or does it stage for human approval?
- Status: unanswered — NEW founder-ball from Parallax's review (2026-10-17): digest mode writes model output straight into the next public commit; generation is not declassification
- Why asking: *"A model may draft the public boundary, but should not silently become the authority that moves it"* (Parallax). The digest's one permitted verbatim sentence and preserved names are exactly the content whose publication wants a human moment; this is the mirror-scale instance of the house's own publication gate.
- Need: pick a letter (or override — any shape answers)

Options:
- **A — Unattended.** Digest mode enabled means every regenerated digest publishes on the next sync.
- **B — Staged by default.** Unchanged approved digests republish freely (cached); a CHANGED digest stages for the owner's approval; a repo may explicitly opt into unattended publication under a recorded policy.

**Recommendation**: (by Claude Fable 5, concurring with Parallax at 0.9)
**B — staged by default, opt-in to unattended.** *Rationale*: it is the digest-as-duty design (the gated mode's own shape: disclosure mandatory, text at the owner's tempo) carried to the artifact level; caching makes the steady state zero-touch, so the approval moment costs attention only when the boundary actually moved — which is precisely when attention is owed. *Confidence*: 0.85. *If wrong*: a record class with a human-approved prompt + validator demonstrating every permissible output is pre-authorized — then A for that class, recorded.

**ANS:** (by Jérémie)
[Fill this in]   <!-- literal placeholder — parser-significant, do not paraphrase -->

---

## Action Items

- [ ] v2: `sync` input (`one-shot` default | `synced`) + the private-side workflow template for synced mode — Owner: Covenant 5
- [ ] README security story (token scoping, per QST-TOKEN-KIND's answer) — Owner: Covenant 5
- [ ] Strip/include profile home in `kintsugi.yaml` zones (revival on the history word) — Owner: Kintsugi 5

## Iterations

- **Iteration 2** (2026-10-17, Covenant 5 / Claude Fable 5): **first live trial executed at the founder's step-3 word** — `ADRs4AI/vscode-adrs4ai` → `ADRs4AI/vscode-adrs4ai-no-adrs`, mirror created **private** by the engine's own law (the runtime line printed it), 1 commit, notice present, all API-verified (`proof/2026-10-17-first-live-trial-vscode-adrs4ai.md`). **Finding**: the default strip list under-strips record-heavy repos — vscode keeps deliberation-class files outside the conventional paths (`PRIVACY-THOUGHTS.md`, `theory/`, `handbooks/`, …). Consequence for this ADR: the per-repo withhold profile (`kintsugi.yaml` zones, decision point 4's seam) is **required, not optional, before any flip of a record-heavy repo's mirror** — first empirical proof of Kintsugi's one-home ruling; folded into their review ask the same day. Also this day: the founder's mission sentence for the tool staked in the seed's Thread ("…mediate, granularly, what is public and not"), and the four-seat review round commissioned (Pharos, Parallax, Shipwright, Kintsugi).
- **Iteration 1** (2026-10-15, Covenant 5 / Claude Fable 5): staked from the founding seed under the founder's premium ruling ("one of the main tools of our toolkit" — Operator's `1340`); the sketch confirmed as the architecture; the visibility law restated as a design invariant that Marketplace convenience never relaxes.
