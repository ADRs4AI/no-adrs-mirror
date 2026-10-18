# Seed: selective ADR retention — named records kept in the mirror, optionally through a filter

- **Date**: 2026-10-18
- **Source**: Jérémie Lumbroso, in-session (launch day), verbatim below; staked by Covenant 5 (Claude Fable 5) for joint iteration on his return
- **Status**: concept staked; iterating with the rights-holder before any ADR is cut

**TL;DR**: The mirror gains per-record declassification: the owner names specific ADRs (by number, at least) to RETAIN in the mirror, each optionally passed through a **filter — a prompt applied by a small model** (Haiku-class) that redacts/reshapes the record for public eyes. This is the gated mode's "declassification at the owner's tempo" made granular: not record-or-no-record, but *this* record, *this much*, *now*.

## His words, verbatim

> The last thing is that we want a feature in the action to be able to selectively retain versions of certain adrs, named by number perhaps, and also what filters (if any to apply) — filters are prompts passed on to Haiku 5.5? Or you iterate on this concept in a seed with me if you prefer.

(Seed preferred — this is design-grade, and the iteration is the record.)

## The concept, placed

This completes the mode spectrum from the *record's* side. Today's modes act on the whole record (none / closed / digest / open); retention acts per record: a mirror can be closed-with-exceptions — ADR-0007 and ADR-0012 ship whole (or filtered), everything else stays withheld and counted in the notice. The notice then reports three classes honestly: withheld (N), retained verbatim (list), retained filtered (list, with filter provenance — prompt hash, model, timestamp, exactly like digests).

**The standing law that reaches into this feature**: *generation is not declassification* (Parallax, QST-DIGEST-APPROVAL). A filtered retention is model output crossing the public boundary — whatever posture the founder rules for changed digests (staged-by-default is the staked rec) applies at least as strongly here, because a filtered ADR *looks like* the record in a way a digest does not.

## Design axes to iterate (the next sitting's material, informal until then)

1. **Naming grammar**: numbers (`0007`), ranges (`0001..0010`), globs, or QST-handles? Lean: numbers + ranges first; the Address grammar already gives every record a canonical name, so the profile speaks `adr://`-compatible locators.
2. **Filter semantics**: one prompt per retained record, or named filter presets (`public-safe`, `names-redacted`, `decision-only`)? What a filter may NEVER do (invent content; drop the provenance header; strip attribution the license requires). Lean: presets + optional per-record prompt override; an immutable preamble the owner's prompt cannot remove.
3. **Placement in the mirror**: retained records at their original paths (`docs/adr/0007-….md` reappears) or a distinct `docs/retained-record/`? Lean: original paths WITH a retained-stamp header (reads naturally; the stamp + notice prevent "is this the whole record?" confusion).
4. **Approval posture**: filtered output staged for the owner by default (per the digest-approval shape); verbatim retention is owner-named so it is its own consent. Caching: filtered text frozen per (record blob, prompt, model) — regenerated only when the source record changes, then re-staged.
5. **Profile home**: the retention list lives with the strip profile (`kintsugi.yaml` zone / the Action's profile file) — one reviewed artifact that answers "what crosses," per QST-SYNC-CONSENT's fail-closed direction.

## NOT: why this matters beyond mechanics (design-relevant, carried from the founder's framing)

The reluctance to share one's deepest working thoughts is not an edge case — it is probably the common case. The mirror family is therefore a **normalizing tool**: it makes "keep the record, choose its publicness, granularly, at your own tempo" a turnkey practice instead of a personal risk. Selective retention is the finest grain of that promise, and the companion **docsite/manual** (staked in `adr:0003` this same day) is where the practice gets taught to strangers.

## Derived Into

- (pending the joint iteration — expected: ADR-0004 in this repo)

— Covenant 5 (Claude Fable 5, iron-gall #1F3A93), 2026-10-18
