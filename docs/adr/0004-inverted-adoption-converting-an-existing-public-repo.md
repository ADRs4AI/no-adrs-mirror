# ADR-0004: Inverted adoption — converting an existing public repo into a deliberating one

- **Date**: 2026-10-19
- **Iteration**: 1
- **Status**: Proposed (commissioned by the rights-holder; design staked, build not started)
- **Deciders**: Jérémie Lumbroso (rights-holder; the commission is his, verbatim below); Covenant 5 / Claude Fable 5 (author)
- **Cross-reference**: ADR-0001 (mode matrix, QST-SYNC-CONSENT), ADR-0002 (two-phase history, tree identity), HQ `adr://v1/repo/ADRs4AI/initial-meta-repository/adr/0034` (Open Deliberations charter)

**TL;DR**: Today's flow assumes a private source that *births* a `-no-adrs` mirror. Every existing OSS maintainer has the opposite topology: a public repo with standing — stars, issues, links, name. The inverted flow makes that public repo the **mirror target**: a private clone becomes the deliberating source where the record accrues, and code commits flow *back* to the repo the world already watches. Identity, stars, and history are preserved **by construction**, because the public repo is never replaced — it is appended to.

## Context — the commission

The founder, verbatim (2026-10-19, staked at `lumbroso-hq/intake/daily/2026-10-18/repos-0002-responses-0123Z.json`, relayed by Operator 5): *"we should make it possible to convert an existing repo into an ADR one by getting the existing public one to receive commits from a clone made private, and in which ADRs are rebuilt."*

This is the adoption path for the largest audience the Action has: maintainers who already ship in public and want to *start* keeping a record without paying a migration. The companion objection-softener (his commission A, same relay) landed in the README the same night: stars travel with transfers and renames, and in this flow nothing even has to travel.

## The design sketch

1. **Bootstrap** — the maintainer clones their public repo into a new **private** repo (their own hands; the Action's visibility law is untouched — it still never creates anything public and never flips anything). The two histories now share their entire prefix. **No rewrite is needed, ever**: the public repo's existing history *is* the declared epoch, and the sync state starts at the shared tip. This is ADR-0002's phase B from day one — the cleanest possible instantiation of the two-phase law.
2. **The record accrues privately** — `docs/adr/`, seeds, inbox, apparatus: all of it exists only in the private source, exactly as in the forward flow. "ADRs are rebuilt" (his phrase) happens here: the record can be reconstructed retroactively for past decisions at whatever depth the maintainer wants, because it never has to be pushed anywhere.
3. **Sync runs inverted** — the Action, installed on the private source, builds the stripped view and **fast-forwards the public repo**. Append-only is not a preference here but a hard constraint: `history_mode: snapshot` must be *refused* for a target with existing history it did not generate (it would replace the public history the flow exists to preserve), and non-fast-forward fails closed, per ADR-0002. Message tiers apply to the new commits only; pre-adoption public history is never touched.
4. **The notice is the declaration moment** — the first sync lands `DELIBERATIONS-NOTICE.md` in the public repo: the record exists, here is its size, here is how disclosure will be decided. The repo keeps its name — no `-no-adrs` suffix — so the notice alone carries the mirror's self-description.

## What it costs (the honest ledger)

- The first sync writes to an **already-public** target: there is no private dress-rehearsal state. The consent contract (ADR-0001 QST-SYNC-CONSENT, fail-closed) was designed for exactly this class of moment, but the inverted bootstrap deserves its own teaching surface (QST below).
- Contributions keep arriving at the public repo; the round-trip (ADR-0002 patch-port) becomes the *standing* intake path, not an occasional one. The tree-identity invariant does the heavy lifting.
- The maintainer's muscle memory must move: day-to-day pushes go to the private source, not the repo they've pushed to for years. The flow should make the wrong push hard (QST below).

### QST-INV-REFUSALS: Which guardrails are hard refusals at sync time for an inverted target?
- Status: unanswered
- Why asking: an inverted target is public and has pre-existing history; a misconfigured sync is an irreversible public act. The forward flow's guardrails (private creation, non-FF fails closed) cover most of it, but snapshot-mode-against-existing-history is new.
- Need: confirm the refusal set — any shape answers

**Recommendation**: (by Claude Fable 5)
**Refuse, at build time, with a teaching message**: (a) `history_mode: snapshot` when the target's HEAD is not an ancestor the Action generated (detectable: no prior notice/state marker), (b) any non-fast-forward push (already law), (c) first sync to a public target without the consent contract reviewed (already SYNC-CONSENT B — extend its `$GITHUB_STEP_SUMMARY` block with an inverted-bootstrap paragraph naming what is about to become public, before anything pushes). *Confidence*: 0.7. *If wrong*: each refusal is independently relaxable; none forecloses the others.

### QST-INV-WRONG-PUSH: How does the flow protect against the maintainer's habitual push to the public repo?
- Status: unanswered
- Why asking: years of `git push origin main` habit now point at the mirror target; a direct human push to the target desynchronizes it from the source (and may race a sync).
- Need: a mechanism pick — any shape answers

**Recommendation**: (by Claude Fable 5)
**Document-first, enforce-optional**: the conversion guide tells the maintainer to flip their local remotes (public repo becomes `mirror`, private becomes `origin`) — one command, and the habit keeps working *correctly*; optionally, a branch-protection rule on the public repo restricting pushes to the sync identity makes the wrong push impossible rather than merely unlikely. The Action itself should *tolerate* a human commit on the target by failing closed (non-FF) and saying exactly what happened and how to port the stray commit back (ADR-0002's patch-port, in the other direction). *Confidence*: 0.65.

### QST-INV-SCOPE: Is inverted adoption a mode of this Action or a separate guide + the existing Action?
- Status: unanswered
- Why asking: steps 1–4 above need almost no new engine — the strip/tier/notice machinery is identical; what's new is bootstrap detection, the snapshot refusal, and documentation. A "mode" implies inputs and code paths; a "guide" implies the docsite (ADR-0003's companion-manual commission) carries it.
- Need: scope ruling — any shape answers

**Recommendation**: (by Claude Fable 5)
**Both, thin**: one input's worth of engine (the existing-history detection + snapshot refusal — safety belongs in code), and the conversion walkthrough as a first-class docsite page (the audience is exactly the stranger the docsite is for). No `inverted: true` flag — the Action can *detect* the topology (target exists, has history, no prior state marker) and apply the stricter rules automatically, which is one less praxigenic hazard than an input someone forgets. *Confidence*: 0.6 on the no-flag detection claim — it must be falsified against the bootstrap-vs-steady-state split in practice before it hardens.

## Iterations

- **Iteration 1** (2026-10-19, Covenant 5 / Claude Fable 5): ADR founded on the rights-holder's commission (Operator relay, staked). Design sketch staked as the two-phase law's cleanest instantiation (shared-prefix bootstrap = phase B from day one, no rewrite ever). Three QSTs opened with recommendations: refusal set, wrong-push protection, mode-vs-guide scope. Commission A (stars-transfer pointer) landed in the README the same night — this ADR is commission B. Nothing is built; the sample-first discipline (ADR-0001) applies here too: the first inverted conversion should be one of the house's own repos before the flow is documented for strangers.
- **Iteration 2** (2026-10-19, Covenant 5 / Claude Fable 5): **the founder's dictation, same-page check — his frame confirms the sketch and widens it in three load-bearing places.** His words, verbatim (in-session, launch day):

  > *"There's a project. It already exists. it doesn't have ADRs. It wants to try it out, but it wants to do so in private. So it keeps its public repository and we create some sort of mechanism. Maybe it's a it's a porcelain that's dedicated to it. Maybe it's a subprocedure in Docket, but it essentially creates like either a copy of the repository or or it creates a copy of our template and then it imports like the original repository on top of it. but polices it to receive ADRs or something like that. And the idea is that we want to allow the developers to develop in the c the the ADR-based one and for their work to be transferred back to the public repo. And for the public repo to cons continue receiving updates, but they're they're mediated from the ADR one and the ADR one has to keep also pulling syncing things back from the original repos. So for instance, if there's public contributors that are making pull requests and they're merged, then those need to be brought back with the contributors. And in the future, you know, we should allow for the private repo to have the tools to add responses to issues or responses to pull requests that factor the ADRs which aren't public. Does that make sense? But so that's really what this ADR004 should be about. I think there's part of that, but I just want to make sure that we're on the same page"*

  **Same-page mapping** (what It-1 already held ✓ / what his dictation adds ➕):
  1. ✓ Public repo keeps its identity and becomes the mediated target; private clone is where developers actually work; outbound updates flow mediated (sketch steps 1–3).
  2. ➕ **The bootstrap is richer than a clone**: his second variant — *instantiate the template, then import the original repository on top, "policed to receive ADRs"* — means the private side is born a full methodology instance (CLAUDE.md, record apparatus, gates), not a bare clone that later grows one. This becomes the preferred bootstrap: the convert flow's product is *a template instance containing your repo*, which is exactly "wants to try it out."
  3. ➕ **The inbound leg is standing, not occasional**: merged public PRs sync back continuously, **contributors preserved** (authorship travels — ADR-0002's patch-port invariant, `git am` keeping Author). It-1 called the round-trip the standing intake; his dictation makes bidirectional sync the flow's definition, not a feature of it.
  4. ➕ **The third leg is new and scoped in**: tooling for the private side to respond to public issues/PRs with answers that *factor the non-public ADRs* — ADR-0002's "ADR-aware private-only PR evaluation" action item now lives HERE as this flow's future stage (the record informs the answer; the answer ships without the record — the digest discipline applied to conversation).
  5. ➕ **Tooling home widened**: his "dedicated porcelain" / "subprocedure in Docket" options supersede It-1's thin-engine-plus-guide frame — he wants a *mechanism*. QST-INV-SCOPE annotated below rather than rewritten; division of labor that keeps each tool honest: **bootstrap = porcelain-family tooling** (dedicated or a docket verb — naming routes to Mint when built), **standing sync = this Action** (it already owns the outbound leg; inbound rides the ADR-0002 machinery), **response tooling = the future leg**, its own design round when it opens.

  *QST-INV-SCOPE annotation (stacked, It-1 recommendation stands as written for its narrower question)*: the founder's dictation adds options — **B′: a dedicated porcelain** / **C′: a docket subprocedure** — for the *bootstrap/conversion* step specifically. Updated read: B′/C′ for bootstrap (a one-time act wants a tool, not an Action input), this Action for the standing legs; whether B′ or C′ is Mint-and-his at build time. Confidence 0.6; falsifier: if the bootstrap turns out to be three commands, the docsite guide (It-1's answer) was right all along and the porcelain is ceremony.
