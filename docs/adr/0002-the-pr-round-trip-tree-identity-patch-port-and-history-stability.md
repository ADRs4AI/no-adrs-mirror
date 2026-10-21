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

## NOT: the tree-identity check, cut for CI (Shipwright 5's commissioned engineering read, 2026-10-17)

The design is CI-shaped and endorsed, with one sharper cut: **compare blob OIDs, never re-hashed digests.** Git already stores the content hash — `git -C <src> ls-tree -r HEAD --format='%(objectname) %(path)'`, filtered by the strip set, against the same listing in the mirror's HEAD: identical bytes ⟺ identical OIDs, zero hashing work, one command per side. The check is **set-equality both ways plus per-path OID equality**: a path missing from the mirror fails, a path extra in the mirror fails *unless it is on the generated-files allowlist* (`DELIBERATIONS-NOTICE.md`, `DELIBERATIONS-DIGEST.md`, `docs/deliberations-digest/`) — and that allowlist must derive from the build config, never be hardcoded twice. Two companion fixes make the invariant true at the source instead of merely detected late: **build from `git archive HEAD`** rather than copying the working tree (`shutil.copy2` today ships uncommitted edits under a HEAD-stamped notice, and follows symlinks — a tracked symlink can embed a stripped or out-of-tree file's *content* into the mirror; `git archive` closes both in one move), after which the CI check becomes the regression net rather than the primary defense. The teaching failure names the diverged path and both usual causes: a strip-glob edit between syncs, and a dirty working tree at build time. *(Full engineering review: HQ inbox, shipwright → covenant, 2026-10-17.)*

---

## Questions

### QST-ROUNDTRIP-V2: Which contribution posture ships in v2?
- Status: answered — by the rights-holder, in-file, 2026-10-18
- Why asking: this decides what a mirror's "Pull requests" tab means, fleet-wide.
- Need: pick a letter (or override — any shape answers)

Options:
- **A — PRs disabled + CONTRIBUTING pointer.** The honest minimum: the mirror says where contribution happens (issues, or the maintainers' channel). Zero machinery; zero promise.
- **B — Patch-port flow (semi-automated).** PRs open; a maintainer (or dispatch-triggered workflow) runs the port; bot closes with credit. The machinery above, human-triggered.
- **C — Stable-SHA two-way (full automation).** Ports run automatically on PR label; commit-map maintained; mirror history never rewritten. The expensive ideal — build cost and failure surface are both real.

**Recommendation**: (by Claude Fable 5)
**B — patch-port, human-triggered, with A as every mirror's default posture until its owner opts in.** *Rationale*: B delivers his "move their exact change back" with authorship intact at a tenth of C's machinery, and keeping the trigger human preserves the private repo's epistemic gate (the gated-mode trust posture — contributions are *reviewed into* the source of truth, per his 09-01 dictation; an auto-port would bypass exactly that). A-as-default means no mirror ever silently promises more than its owner staffs. *Confidence*: 0.7. *If wrong*: if adoption shows port volume that outgrows human triggers, C's commit-map is the upgrade path and nothing in B's design blocks it — B is C minus automation, not a different shape.

**Stacked** (Parallax, cross-vendor review 2026-10-17, folded by Covenant 5): **Concur B as destination, with A as the actual PUBLIC default until B's complete contract exists** — the contract being: every mirror base commit bound to its exact source SHA + profile hash + generated-path allowlist; PR validation against that mapped base (portable paths only); a real three-way merge path with conflicts surfaced, never declared impossible; untrusted PR content handled as data (no contributor code in credential-holding jobs); and precise attribution language. Two of their catches amended into this ADR's own text: (1) the invariant is *necessary, not sufficient* — tree identity proves one boundary, not that yesterday's-base PR applies to today's HEAD; (2) the promise conflict: §flow item 3 said the change returns "under the contributor's name" while history-stability permits a bot-authored sync commit — the promise is narrowed to **attribution preserved in the private source**; the mirror shows it when the sync replays author-preserving commits, and a generated-files unportability guard joins the port (Kintsugi's same-day catch: `git am` must never create mirror-only generated files in the source). Until v2 ships the contract, every mirror's notice carries "PR porting is unsupported here" rather than an open PR tab implying a staffed round trip.

**ANS:** (by Jérémie Lumbroso)
OK, approving the updated recommendation. In practice, I expect open source / closed deliberations to work like this: A team of opt-in maintainers will have access to the private repo with deliberations. I think what would be nice is that every PR could be evaluated against the existing store of ADRs. But the recommendation should be made privately, or can it be made only visible to the maintainers of the private repo, not publicly?

---

### QST: History mode for synced mirrors — append-only confirmed?
- Status: answered — by the rights-holder directly, in-session 2026-10-18 (supersedes the §1.1 readback line; Operator notified), adding a THIRD axis to the staked two: **trust-legibility** — his reaction to the snapshot sample, verbatim: *"a commit history of one and this obscure… I think it's very untrustworthy"*
- Why asking: the two-axis line — snapshot for one-shot (leakage), append-only + commit-map for synced (contribution) — is one confirm.

**Recommendation**: (by Kintsugi 5, Claude Fable 5 — porcelain lane, the consulted fourth reviewer, 2026-10-17; the commit-map question is mine per HQ `adr:0034#qst-closed-history`, answered there this same pass)

**Append-only + commit-map concurred — and the commit-map is MIRROR-MACHINERY state, homed SOURCE-SIDE, with the lock laws inherited.** Three rulings from the kinship lane, one catch:

1. **Mirror-state, not porcelain-state.** The porcelain lock maps *artifact → canonical version* (file lineage across template releases); the commit-map maps *commit → commit across a privacy transform* (history lineage across the strip boundary). Different algebra, different lifecycle (per-sync, not per-update), different owner — it belongs to this Action, and kintsugi will never read it. But it is **lock-class**, so it inherits the lock laws wholesale: tool-written only, never hand-edited; append-only (entries are fossils — arrival order, immutable, the №90 doctrine); and **loss degrades to re-ask, never corruption** (a lost map ⇒ the synced mirror falls back to snapshot-from-here or rebuilds by tree-matching, loudly — never guesses a correspondence).
2. **Home: the PRIVATE source repo** (e.g. `.no-adrs/commit-map.jsonl`, the events-ledger shape), not the mirror and not Action cache. Because the build runs source-side, the map's only audience is the port operator (who has private access by definition), cache is fragile, and the mirror copy would ship a structural metadata trail of private history for zero reader benefit.
3. **The port flow needs a mirror-only-paths guard — this is the catch.** `DELIBERATIONS-NOTICE.md`, the digest index, and `docs/deliberations-digest/` exist only in the mirror: they are outside the tree-identity set, and `git am` does not know that — a contributor's patch touching the NOTICE would apply onto the private original and *create the mirror artifact in the source*. The port step must refuse any patch whose diff touches generated paths, with a teaching refusal: *"this file is generated by the mirror on every sync; propose the change against the Action (its repo) or the mirror policy — it cannot be accepted as a source edit."* One path-filter line in the port runbook; a real incident the first time a stranger "fixes a typo in the notice" otherwise.

*Confidence*: High on 1–2 (the kinship boundary is clean and the lock laws are paid-for); High on 3 (it is a mechanical consequence of the invariant's own definition — generated files are neither stripped nor source). *If wrong*: if a federated port flow someday runs mirror-side without source access, the map's home reopens — and the answer then is a *redacted projection* of the source-side map (mirror-sha-only), never relocation of the full one. 🏺

**ANS:** (by Jérémie, 2026-10-18, verbatim; mechanism + proof appended by Covenant 5)

> I am hoping you find that you can have the actions rewrite the git history from the source repo to the target repo by stripping the stuff with filter-branch and rewrite it. But every rewrite is going to create different commits. If anybody is referencing anything in the codebase it completely breaks every refresh. That's its own kind of debilitating because it means the codebase loses a particular kind of legibility — it can't be linked to externally. Perhaps that's a feature! Not one I would use, it's sort of an evil feature. So ideally, there are two phases:
> - the target repo doesn't exist (or the parameters are changed catastrophically in a way that requires rewriting everything): start from scratch filter-branch, nothing can be done
> - if the target repo exists: is it possible to append to its existing commit history rather than rewriting it all?

**Mechanism, verified by proof the same night**: yes — `git filter-repo --state-branch <ref>` persists the commit-map between runs; later runs filter only NEW source commits and graft them onto the previously-filtered history, old SHAs untouched. Synthetic proof (~04:30 UTC): epoch-1 filter → HEAD `d714c98`; one new source commit; incremental re-run → the new commit atop the UNCHANGED old head, `merge-base --is-ancestor` fast-forward confirmed, old SHA still valid. **Appended, not rewritten** — external links survive every refresh. The state ref is precisely the commit-map Kintsugi homed source-side above (lock laws apply to it). His "evil feature" aside is recorded: per-sync rewrite (anti-linkability) remains available as a deliberate posture, never the default for anything meant to be referenced. The sample mirror was rebuilt the same hour as a full-history filter+scrub epoch-1: 797 commits live, private.

---

## Action Items

- [x] **Build from the committed tree** (the archive half of Shipwright's build-from-archive hand): `build_snapshot` now extracts `git archive HEAD` instead of copying worktree bytes — closes the symlink-materialization and dirty-worktree escapes Parallax's second look (2026-10-20) proved against `shutil.copy2`; kill tests pinned (`tests/test_mirror.py`: symlink + dirty-worktree). The two-way tree/OID identity CHECK remains with the tree-identity item below — DONE 2026-10-20, Covenant 5 (v0.3.0)
- [x] **Two-phase history engine** (the rights-holder's 10-18 design) — **BUILT 2026-10-21 (v0.4.0), at his "ASAP"**: phase A = full rewrite + force-push, disclosed in the notice ("epoch rebuild — history re-derived this sync"); phase B = incremental via `--state-branch` persisted in the PRIVATE source (`no-adrs-mirror/state`), the mirror's prior objects fetched to back the state map (unreachable mirror + present state fails closed, never silently rebuilds), the previous tip woven in as the second parent of an `-s ours` merge so **every push is a true fast-forward and every prior mirror SHA stays reachable**; a non-FF fails closed with the teaching message and awaits the human word (`history_epoch: "new"`). Snapshot mode is incremental by the same merge construction (one appended commit per sync). Sandbox-tested offline (SHA-stability + no-force kill tests, 25/25); the LIVE two-phase proof runs via `tests/integration/run.py` + `.github/workflows/integration.yml` against the founder's two dedicated fixture repos (token pending). Epoch NUMBERING in the notice (N, dates) remains a refinement — Owner: Covenant 5
- [ ] Tree-identity CI check in the Action (with a teaching failure message) — Owner: Covenant 5
- [ ] Notice sentence (the port promise) added to the template on QST-ROUNDTRIP-V2's answer — Owner: Covenant 5
- [ ] Port runbook (`PORTING.md`): the four commands + the bot-comment template — Owner: Covenant 5
- [ ] **ADR-aware PR evaluation, private-visible** (his ROUNDTRIP ANS, new thread): every mirror PR evaluated against the private repo's record store; the evaluation runs source-side and surfaces ONLY to the private repo's maintainers (a check/issue there — the public PR never carries it; answer to his "can it be made only visible?": yes, by construction, because the evaluator needs the record and the record is private). Design with the retention seed's sitting — Owner: Covenant 5 with Jérémie

## Iterations

- **Iteration 1** (2026-10-15, Covenant 5 / Claude Fable 5): staked from the founding seed under the premium ruling; Operator's seasoning folded (tree-identity as CI check; the three postures priced); the gated-mode rationale made explicit in B's recommendation — the human trigger IS the epistemic gate, not a limitation.
