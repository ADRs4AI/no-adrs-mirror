# ADR-0001: Sync architecture — the mode matrix and the private-side workflow

- **Date**: 2026-10-15
- **Iteration**: 1
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
- Status: unanswered — keeper-level preference; either is sound, the docs should bless one
- Why asking: the README's security story teaches one happy path; adopters copy it verbatim.
- Need: pick a letter (or override — any shape answers)

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

## Action Items

- [ ] v2: `sync` input (`one-shot` default | `synced`) + the private-side workflow template for synced mode — Owner: Covenant 5
- [ ] README security story (token scoping, per QST-TOKEN-KIND's answer) — Owner: Covenant 5
- [ ] Strip/include profile home in `kintsugi.yaml` zones (revival on the history word) — Owner: Kintsugi 5

## Iterations

- **Iteration 1** (2026-10-15, Covenant 5 / Claude Fable 5): staked from the founding seed under the founder's premium ruling ("one of the main tools of our toolkit" — Operator's `1340`); the sketch confirmed as the architecture; the visibility law restated as a design invariant that Marketplace convenience never relaxes.
