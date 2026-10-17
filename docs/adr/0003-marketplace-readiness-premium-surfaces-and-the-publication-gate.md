# ADR-0003: Marketplace readiness — premium surfaces and the publication gate

- **Date**: 2026-10-15
- **Iteration**: 1
- **Status**: Draft
- **Deciders**: Jérémie Lumbroso (rights-holder; the listing is his word); Covenant 5 / Claude Fable 5 (author); coordinates: Pharos 5 (public story), Mint 5 (names, №92 holder), Operator 5 @ lumbroso-hq (calendar)

**TL;DR**: The Action is ruled "one of the main tools of our toolkit — polished and premium" (the rights-holder, 2026-10-15). This ADR fixes what premium means surface by surface, so the repo is ready to list on the GitHub Marketplace *the day he says so* (~Feb slot per the hub calendar) — and names the two things listing must never change: the visibility law, and the honesty of the notice.

## Context

His words, staked at lumbroso-hq intake: *"a legitimate GitHub action that we publish on Marketplace … the standardized way to publish a no ADR's mirror"* (10-13) and *"I really need this tool to be polished and premium — and as smooth as everything else"* (10-15). The seed carries the story sentence that leads the listing: demoing *what you do when your deliberations are too important* — Closed mode as the product, not the apology.

## The premium surface list (decision, proposed)

1. **README as the listing page**: the two-sentence "too important" story up top; the mode matrix table; a real demo pair (source repo → its `-no-adrs` mirror) with live numbers; the `DELIBERATIONS-NOTICE.md` preview; badges (tests; Marketplace once listed). The README already carries most of this — the demo *pair* lands when the first mirror flips public at his word.
2. **`action.yml` branding block** (`icon`/`color` — candidates routed through Pharos's surface, QST below) + input names and defaults exactly as taught in the README's table — no drift between the two, enforced by eyeball at every release until a doc-check exists.
3. **Error surfaces that teach** (the pharoscan-register rule: announce, never fail silent): tree-identity check failure names the diverged path and the usual cause; token-scope failure says which scope was missing and the one-line remedy; filter-mode runs print the mixed-commit count with one sentence of meaning. No stack trace reaches an adopter without a sentence above it.
4. **Digest output stays addressed and attributed** — model, prompt hash, timestamp per digest; the Address is the citation. (Already the design; premium means never regressing it.)
5. **`dry-run.sh` output is the proof artifact** — readable enough to paste to the rights-holder whole. (Already true; kept under test by the proof files committed per run.)
6. **Semver discipline**: tags are immutable; `v1` is a moving major alias re-pointed at each `v1.x.y`; breaking input changes mean `v2`. The adopting workflow pins the major alias.

## What listing never changes

- **The visibility law**: `create_if_missing` creates private, always; no public flag exists. A Marketplace reviewer asking for "convenience" gets the law quoted, not relaxed.
- **The notice**: every mirror ships `DELIBERATIONS-NOTICE.md`. A mirror that hides the record's existence is a different product; this one's listing says so.

## Questions

### QST-BRANDING: Icon and color for the Marketplace branding block?
- Status: unanswered — Pharos's surface to coin, his to ratify; the block is two fields
- Why asking: `action.yml` branding is the listing's face; name-adjacent, so it follows the naming discipline (collision + connotation + praxigenic pass).
- Need: a pick in any shape — a feather icon says "record"; candidates below are starters, Pharos may coin better

Options:
- **A — `icon: copy`, `color: blue`.** A mirror is a copy; house blue (the record's ink).
- **B — `icon: eye-off`, `color: gray-dark`.** Names the withholding honestly; risks reading as secrecy rather than poise.
- **C — `icon: git-branch`, `color: blue`.** Mechanism-flavored; says nothing of the subtraction (the №92 doctrine cuts against it).

**Recommendation**: (by Claude Fable 5)
**A — `copy` + `blue`.** *Rationale*: the №92 doctrine (name the subtraction, never the subtracted) governs *names*; an icon's praxigenic job is gentler — say what the thing does at a glance, and "copy" is what a mirror does; `eye-off` makes the withholding the identity, which contradicts the "too important" story's confidence. Blue is the record's own color across the toolkit. *Confidence*: 0.55 — this is Pharos's craft, not mine; the letter exists so the block isn't empty while their pass runs. *If wrong*: Pharos coins better and this letter yields — their surface, his ratify.

**Recommendation**: (by Pharos 5, Claude Fable 5 — the routed register pass, 2026-10-17)
**Coin: `icon: book`, `color: blue`.** *Rationale*: The icon should carry the object of care, not the mechanism — `copy` says duplication and misses the story entirely; `eye-off` makes withholding the identity (concurring with the starter's own rejection); a **closed book** says "a record exists, bound and kept" at a glance. It enacts the "too important" story rather than illustrating the plumbing, and it pre-names the family grammar: `book-open` stands ready if an Open-Deliberations sibling ever ships — the flip is, literally, a book opening. Blue stays: The record's ink across the toolkit. Three-test pass: Collision mild (documentation tools use `book`; distinctive within this product family); connotation clean (kept is not hidden); praxigenic (the glance teaches what the product protects, and the open/closed axis maps onto the mode matrix). *Confidence*: 0.75 — icon semantics are my craft, but the Marketplace renders Feather glyphs small: If `book` reads as "docs tool" at listing size to the founder's eye, that is the falsifier, not a cost. *If wrong*: Starter A (`copy` + `blue`) is the clean runner-up; nothing else changes.

**ANS:** (by Jérémie, after Pharos's pass)
[Fill this in]   <!-- literal placeholder — parser-significant, do not paraphrase -->

---

### QST-LICENSE: What license does this repository itself carry?
- Status: unanswered — NEW founder-ball from Parallax's review (2026-10-17): the repo has no root LICENSE (API-verified), so outsiders have no permission to use, modify, or redistribute the Action at all — no outside adoption is possible without this answer, and the catch lands on the licensing seat's own repo, owned with the full irony
- Why asking: license posture is per-repo and the rights-holder's alone (HQ `adr:0033`, It-9 doctrine: license artifacts travel by ruling, never by default).
- Need: pick a letter (or override — any shape answers); nothing lands in the tree before your word, and the repo is private until your flip regardless

Options:
- **A — MIT at root, nothing else.** The toolkit's established code posture (template, pneumatic, kintsugi all MIT); simplest, badge-clean.
- **B — MIT at root + a short output note for generated files.** Same MIT, plus a `MIRROR-OUTPUT-NOTE.md` (never appended to LICENSE — the badge lesson is law) stating that files the Action *generates into a mirror* (`DELIBERATIONS-NOTICE.md`, digests) belong to the mirror's owner, carrying the record's terms where one applies — the template-output-grant pattern, applied to this tool's outputs.
- **C — Defer to the counsel round.** Ships nothing until the QST-COUNSEL route runs; blocks any outside adoption meanwhile.

**Recommendation**: (by Claude Fable 5)
**B — MIT root plus the separate output note.** *Rationale*: A alone leaves the generated-files question to inference, and this tool's whole product is other people's repos — the note answers "whose is the notice in MY mirror?" before a stranger asks it; the pattern is already proven on the template (launch night's split restored the badge, and It-9 made the receipt doctrine law); MIT itself is standard text and ships on your go alone per QST-COUNSEL's standing shape, while the note's wording can take a counsel pass before the PUBLIC flip without blocking the private estate. *Confidence*: 0.75. *If wrong*: if counsel reads any output note as inviting more questions than it settles, A + the same sentence as plain README prose — the established fallback.

**ANS:** (by Jérémie)
[Fill this in]   <!-- literal placeholder — parser-significant, do not paraphrase -->

---

### QST-LISTING-GO: Publish to the Marketplace?
- Status: deferred — the publication gate is absolute and this is its named slot: his word, expected at the ~Feb calendar window, after the PR-round-trip ADR settles and one live demo pair exists; nothing is owed by anyone until then
- Why asking: so the gate is legible in the record rather than ambient — the listing is an outward act.

**ANS:** (by Jérémie, when the day comes)
[Fill this in]   <!-- literal placeholder — parser-significant, do not paraphrase -->

---

## Action Items

- [ ] Branding block in `action.yml` once QST-BRANDING settles — Owner: Covenant 5
- [ ] Teaching error surfaces (tree-identity, token-scope, mixed-commit) in the v2 build — Owner: Covenant 5
- [ ] Marketplace name-availability check for "no-adrs mirror" at listing time (names drift; check at the gate, not now) — Owner: Covenant 5
- [ ] Listing copy pass — Owner: Pharos 5, at his go

## Iterations

- **Iteration 1** (2026-10-15, Covenant 5 / Claude Fable 5): staked the hour the premium ruling arrived (Operator's `1340`); the surface list is Operator's read refined into decisions; the two never-changes named so Marketplace pressure has a wall to meet.
