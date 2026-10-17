# ADR-0002: The PR round-trip — tree identity, patch-port, and history stability

- **Date**: 2026-10-15
- **Iteration**: 1
- **Status**: Draft
- **Deciders**: Jérémie Lumbroso (rights-holder; "is it possible?" is his question); Covenant 5 / Claude Fable 5 (author); seasoning: Operator 5 @ lumbroso-hq
- **Cross-reference**: HQ `adr://v1/repo/ADRs4AI/initial-meta-repository/adr/0034#qst-closed-history` — this ADR is that question's second axis, grown 2026-10-13

**TL;DR**: Yes, a contribution made against the public mirror can be moved back to the private original *exactly* — because the trees are identical on every non-stripped path even though the SHAs are not — and the design that makes it routine is: a **tree-identity CI check** (the invariant), a **patch-port flow** (`gh pr diff` / `format-patch` → `git am`, authorship preserved), and, for synced mirrors, **append-only mirror history with a persistent commit-map** so a contributor's branch survives re-syncs.

## Context

The founder, verbatim (founding seed): *"Is it possible if somebody contributes to the code base that's mirrored with no ADRs? to then move their exact change back to the original repository. Since the change delta is applying on code that exists. And both code bases exactly. But the … history would have been rewritten in the mirror."* His intuition is exactly right on both halves: the deltas apply (trees match), and rewritten history is the obstacle (orphaned commits).

## The invariant: tree identity on non-stripped paths

After every mirror build, for every path not in the strip set, `git hash-object` of the mirror's file equals the source's. This is what makes a mirror-side diff apply cleanly to the source. **It becomes a CI check in the Action** (cheap: compare `git ls-tree -r` filtered digests), so the invariant is enforced, not assumed — and its failure message teaches: which path diverged, and that the usual cause is a strip-glob edit between syncs.

## The flow (patch-port, the recommended middle)

1. Contributor opens a PR against the public mirror.
2. The port: `gh pr diff <n> --patch` (or `format-patch` off their branch) → `git am --committer-date-is-author-date` onto the private original. `Author:` survives; a `Co-authored-by:` trailer is added when the port squashes.
3. The private repo's next sync carries the change back out — now in the mirror's own main, under the contributor's name.
4. A bot comment closes the mirror PR: merged-via-port, with credit and the mirror-side commit link.
5. `DELIBERATIONS-NOTICE.md` gains one sentence so nobody is surprised: *"Pull requests here are ported to the private original with your authorship preserved; they land in this mirror on the next sync."*

## History stability (the second axis)

One-shot mirrors may stay `snapshot` (one commit, zero leakage — the proven default). A **synced** mirror that re-snapshots on every push orphans every contributor branch between syncs. So synced mode keeps **append-only mirror history**: each sync adds commits on top of the mirror's existing main (tree-to-tree diff committed as one "sync" commit, or filter-repo with a persisted commit-map for repos that want code history). Leakage discipline is unchanged — synced commits carry generated messages (`sync: <source-sha-prefix> without the record`), never source messages.

## Questions

### QST-ROUNDTRIP-V2: Which contribution posture ships in v2?
- Status: unanswered — his product call; the engineering is priced below
- Why asking: this decides what a mirror's "Pull requests" tab means, fleet-wide.
- Need: pick a letter (or override — any shape answers)

Options:
- **A — PRs disabled + CONTRIBUTING pointer.** The honest minimum: the mirror says where contribution happens (issues, or the maintainers' channel). Zero machinery; zero promise.
- **B — Patch-port flow (semi-automated).** PRs open; a maintainer (or dispatch-triggered workflow) runs the port; bot closes with credit. The machinery above, human-triggered.
- **C — Stable-SHA two-way (full automation).** Ports run automatically on PR label; commit-map maintained; mirror history never rewritten. The expensive ideal — build cost and failure surface are both real.

**Recommendation**: (by Claude Fable 5)
**B — patch-port, human-triggered, with A as every mirror's default posture until its owner opts in.** *Rationale*: B delivers his "move their exact change back" with authorship intact at a tenth of C's machinery, and keeping the trigger human preserves the private repo's epistemic gate (the gated-mode trust posture — contributions are *reviewed into* the source of truth, per his 09-01 dictation; an auto-port would bypass exactly that). A-as-default means no mirror ever silently promises more than its owner staffs. *Confidence*: 0.7. *If wrong*: if adoption shows port volume that outgrows human triggers, C's commit-map is the upgrade path and nothing in B's design blocks it — B is C minus automation, not a different shape.

**ANS:** (by Jérémie)
[Fill this in]   <!-- literal placeholder — parser-significant, do not paraphrase -->

---

### QST: History mode for synced mirrors — append-only confirmed?
- Status: deferred — rides the §1.1 combined readback already in front of the rights-holder (via Operator; one surface, no double-ask); recorded here so this ADR is self-contained when his word lands
- Why asking: the two-axis line — snapshot for one-shot (leakage), append-only + commit-map for synced (contribution) — is one confirm.

**Recommendation**: (by Kintsugi 5, Claude Fable 5 — porcelain lane, the consulted fourth reviewer, 2026-10-17; the commit-map question is mine per HQ `adr:0034#qst-closed-history`, answered there this same pass)

**Append-only + commit-map concurred — and the commit-map is MIRROR-MACHINERY state, homed SOURCE-SIDE, with the lock laws inherited.** Three rulings from the kinship lane, one catch:

1. **Mirror-state, not porcelain-state.** The porcelain lock maps *artifact → canonical version* (file lineage across template releases); the commit-map maps *commit → commit across a privacy transform* (history lineage across the strip boundary). Different algebra, different lifecycle (per-sync, not per-update), different owner — it belongs to this Action, and kintsugi will never read it. But it is **lock-class**, so it inherits the lock laws wholesale: tool-written only, never hand-edited; append-only (entries are fossils — arrival order, immutable, the №90 doctrine); and **loss degrades to re-ask, never corruption** (a lost map ⇒ the synced mirror falls back to snapshot-from-here or rebuilds by tree-matching, loudly — never guesses a correspondence).
2. **Home: the PRIVATE source repo** (e.g. `.no-adrs/commit-map.jsonl`, the events-ledger shape), not the mirror and not Action cache. Because the build runs source-side, the map's only audience is the port operator (who has private access by definition), cache is fragile, and the mirror copy would ship a structural metadata trail of private history for zero reader benefit.
3. **The port flow needs a mirror-only-paths guard — this is the catch.** `DELIBERATIONS-NOTICE.md`, the digest index, and `docs/deliberations-digest/` exist only in the mirror: they are outside the tree-identity set, and `git am` does not know that — a contributor's patch touching the NOTICE would apply onto the private original and *create the mirror artifact in the source*. The port step must refuse any patch whose diff touches generated paths, with a teaching refusal: *"this file is generated by the mirror on every sync; propose the change against the Action (its repo) or the mirror policy — it cannot be accepted as a source edit."* One path-filter line in the port runbook; a real incident the first time a stranger "fixes a typo in the notice" otherwise.

*Confidence*: High on 1–2 (the kinship boundary is clean and the lock laws are paid-for); High on 3 (it is a mechanical consequence of the invariant's own definition — generated files are neither stripped nor source). *If wrong*: if a federated port flow someday runs mirror-side without source access, the map's home reopens — and the answer then is a *redacted projection* of the source-side map (mirror-sha-only), never relocation of the full one. 🏺

**ANS:** (by Jérémie)
[Fill this in]   <!-- literal placeholder — parser-significant, do not paraphrase -->

---

## Action Items

- [ ] Tree-identity CI check in the Action (with a teaching failure message) — Owner: Covenant 5
- [ ] Notice sentence (the port promise) added to the template on QST-ROUNDTRIP-V2's answer — Owner: Covenant 5
- [ ] Port runbook (`PORTING.md`): the four commands + the bot-comment template — Owner: Covenant 5

## Iterations

- **Iteration 1** (2026-10-15, Covenant 5 / Claude Fable 5): staked from the founding seed under the premium ruling; Operator's seasoning folded (tree-identity as CI check; the three postures priced); the gated-mode rationale made explicit in B's recommendation — the human trigger IS the epistemic gate, not a limitation.
