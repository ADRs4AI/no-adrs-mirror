# Seed: Marketplace, sync, PR round-trip — and the "too important" reframe

- **Date**: 2026-10-13
- **Source**: Jérémie Lumbroso, dictation ~19:15 ET, reacting to the Action's birth (`ff4eae7`, Mint №92); staked verbatim at `lumbroso-hq/intake/daily/2026-10-13/no-adrs-mirror-marketplace-pr-roundtrip-dictation-VERBATIM.md`; routed by Operator 5 (brief `2026-10-13-2325`, ADRs4AI HQ inbox)
- **Captured by**: Covenant 5 (Claude Fable 5, iron-gall #1F3A93)
- **Status**: captured; chunking into this repo's first ADRs is this week's work

**TL;DR**: The founder's design round for this Action: publish it to the GitHub Marketplace as *the* standardized way to ship a no-ADRs mirror; add a continuous-sync mode (private-side workflow, scoped token); design the PR round-trip (mirror contributions transplanted to the private original with authorship intact); and — his ruling — author all of this as ADRs **in this repository itself**, because the tool that strips records ships with its own record open.

## His words, verbatim (dictation; transcription artifacts kept)

> but I think that ideally it would be nice to make it a legitimate GitHub action that we publish on Marketplace. to make it sort of like the standardized way to publish a no ADR's mirror. And so we need to think about how it works. Is is is this like an act like a workflow that's put on the private repo with a token to the public repo? And it pushes like every time there's an update it it synchronizes with that with the deliberation and optionally additional files stripped Well like if I if I'm not so here's the thing that I realized, if I'm not demoing a big repo with all my deliberations then maybe I'm demoing what you do when your deliberations are too important. Because I've been releasing a lot of small repositories with full deliberations as examples. So I don't have to give the most precious ones. But if I can show a toolkey way of doing what I've done, that would be very helpful. [toolkey = likely "turnkey"] The only other thing that I want to think about is like how do you do pull requests? Is it possible if somebody contributes to the code base that's mirrored with no ADRs? to then move their exact change back to the original repository. Since the change delta is applying on code that exists. And both code bases exactly. But the the commit the history would have been rewritten in the mirror because we would have stripped files completely

And his closing line, typed, carrying the ruling that placed this file here:

> All of this is probably ADRs that are going to be in the mirror itself, well the action itself

## The four threads (to be chunked into this repo's ADRs)

1. **Marketplace destiny** — a legitimate, published Action: branding block in `action.yml`, semver + a moving `v1` major alias (the tag exists), README as the listing page, name uniqueness on the Marketplace, and the token security story told plainly. *Listing is an outward act: it happens on his word, not before.*
2. **Sync architecture** — his sketch, confirmed sound by Operator and by this lane: the workflow lives on the **private** repo; a fine-grained PAT or deploy key scoped to only the mirror is its secret; every push re-synchronizes. The mode matrix gains a dimension: **(none / closed / digest / open) × (one-shot / synced)**. The engraved law holds in both: the Action never creates public; the flip is the owner's per-repo word.
3. **PR round-trip** — his question "is it possible?": yes, and the invariant that makes it so is **tree identity on non-stripped paths** (worth a CI check). The shape to price: `gh pr diff` / `format-patch` off the mirror PR → `git am` onto the private original, authorship preserved → next sync carries the change back out under the contributor's name → a bot closes the mirror PR with credit and the link. The catch this lane already measured: fresh-snapshot syncs orphan the contributor's mirror-side commit every time — so synced mode argues for **append-only mirror history with a persistent commit-map**. QST-CLOSED-HISTORY (HQ `adr:0034`) has grown a second axis: *snapshot-vs-filtered was about leakage; one-shot-vs-stable-history is about contribution.* Alternatives to price in the ADR: PRs-disabled + CONTRIBUTING pointer (honest minimum); patch-port bot (recommendation-shaped); stable-SHA two-way (the expensive ideal). A DCO/attribution sentence belongs in `DELIBERATIONS-NOTICE.md` ("PRs here are ported upstream with your authorship").
4. **The reframe (the gem)** — small repos demo Open Deliberations; *this Action demos what you do when your deliberations are too important to open* — "a turnkey way of doing what I've done." Closed/digest mode becomes a story, not an apology. This sentence belongs in the README's opening the day the repo goes public.

## NOT: no open questions in this seed

The one live ask — the now two-axis history-mode confirmation — rides the founder's §1.1 readback surface via Operator (one surface, no double-ask). The ADRs chunked from this seed will carry their own QSTs.

## Thread

### 2026-10-17 — the founder names what this process is for (verbatim, dictation artifact kept)

> This process we are inventing is a crucial part of the whole thing — it's the key thing that will allow people to put their intellectual thoughts so deeply, and to emediate, granularly what is public and not.

[emediate = likely "mediate"] Said while commissioning the four-seat review round (Pharos: story; Parallax: cross-vendor; Shipwright: craft; Kintsugi: profiles — "last person to consult: Kintsugi!") and the first live trial (step 3: a still-private constellation repo, mirror created **private as well**). The sentence is the tool's mission statement: granular, mediated publicness is what makes deep thinking in the record safe — the README's story (ADR-0003) should eventually carry this in its own words. Staked by Covenant 5.

## Derived Into

- ADR-0001 — sync architecture: the private-side workflow, token scoping, and the mode matrix *(staked 2026-10-15)*
- ADR-0002 — the PR round-trip: tree-identity invariant, patch-port, and history stability *(staked 2026-10-15)*
- ADR-0003 — Marketplace readiness: branding, semver discipline, the security story *(staked 2026-10-15)*
- Cross-link: HQ `adr://v1/repo/ADRs4AI/initial-meta-repository/adr/0034` Iteration 5 records this round in the lane's spine

— Covenant 5 (Claude Fable 5, iron-gall #1F3A93), 2026-10-13
