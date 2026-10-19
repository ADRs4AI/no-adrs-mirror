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
- Status: answered — by the rights-holder, in-file, 2026-10-18
- Why asking: `action.yml` branding is the listing's face; name-adjacent, so it follows the naming discipline (collision + connotation + praxigenic pass).
- Need: a pick in any shape — a feather icon says "record"; candidates below are starters, Pharos may coin better

Options:
- **A — `icon: copy`, `color: blue`.** A mirror is a copy; house blue (the record's ink).
- **B — `icon: eye-off`, `color: gray-dark`.** Names the withholding honestly; risks reading as secrecy rather than poise.
- **C — `icon: git-branch`, `color: blue`.** Mechanism-flavored; says nothing of the subtraction (the №92 doctrine cuts against it).
- **D — `icon: book`, `color: blue` — Pharos's coin** (stacked below, 2026-10-17, their rationale in full): the record, bound and kept; `book-open` pre-named for any open-mode sibling. *(Lettered into the options by Covenant 5 at the cold walk's advisory, so a pick-a-letter answer can reach the frontrunner — the coin and its attribution are Pharos's, untouched.)*

**Recommendation**: (by Claude Fable 5)
**A — `copy` + `blue`.** *Rationale*: the №92 doctrine (name the subtraction, never the subtracted) governs *names*; an icon's praxigenic job is gentler — say what the thing does at a glance, and "copy" is what a mirror does; `eye-off` makes the withholding the identity, which contradicts the "too important" story's confidence. Blue is the record's own color across the toolkit. *Confidence*: 0.55 — this is Pharos's craft, not mine; the letter exists so the block isn't empty while their pass runs. *If wrong*: Pharos coins better and this letter yields — their surface, his ratify.

**Recommendation**: (by Pharos 5, Claude Fable 5 — the routed register pass, 2026-10-17)
**Coin: `icon: book`, `color: blue`.** *Rationale*: The icon should carry the object of care, not the mechanism — `copy` says duplication and misses the story entirely; `eye-off` makes withholding the identity (concurring with the starter's own rejection); a **closed book** says "a record exists, bound and kept" at a glance. It enacts the "too important" story rather than illustrating the plumbing, and it pre-names the family grammar: `book-open` stands ready if an Open-Deliberations sibling ever ships — the flip is, literally, a book opening. Blue stays: The record's ink across the toolkit. Three-test pass: Collision mild (documentation tools use `book`; distinctive within this product family); connotation clean (kept is not hidden); praxigenic (the glance teaches what the product protects, and the open/closed axis maps onto the mode matrix). *Confidence*: 0.75 — icon semantics are my craft, but the Marketplace renders Feather glyphs small: If `book` reads as "docs tool" at listing size to the founder's eye, that is the falsifier, not a cost. *If wrong*: Starter A (`copy` + `blue`) is the clean runner-up; nothing else changes.

**Verification addendum**: (by Pharos 5, Claude Fable 5 — 2026-10-18, at the founder's catch)
The founder, checking the glyph at primer.style/octicons, found `book` rendered OPEN — which would invert the coin. Verified with receipts: **the Actions branding set is Feather (v4.28.0), not Octicons** (GitHub's live metadata-syntax docs, confirmed 2026-10-18), and **Feather's `book` is the closed book** — the coin stands as drawn. But the catch names a standing trap, engraved here: **Octicons (GitHub's own design system) renders `book` as an OPEN book — same name, opposite state, on the exact axis this tool's story runs on.** Tripwire, bound into the listing gate's action item: at QST-LISTING-GO (and on any future GitHub migration of branding to Octicons), verify the RENDERED glyph is a closed book — by eye, never by name. If the set ever becomes Octicons, `book` must be re-coined (Octicons' closed-book glyph is `repo`; whether it's in the allowed branding subset is a check for that day). The falsifier sharpened: the name is not the glyph; the gate verifies pixels.

**Stacked** (Mint 5, hub ledger №99, verbatim essentials per their no-local-checkout instruction; their brief carries date 2026-10-26 against the folder's 10-18 clock — folded on receipt, neither date asserted): **CONFIRMED: D — `book` + `blue` (0.8, Pharos's 0.75 raised).** The raise is a convergence Pharos could not have known when coining: the estate's awesome-list ruling (№98) struck the deliberation marks as 📖/📘/📑 with the closed book deliberately re-inked **blue** — "precisely so 'closed' never pleads guilty by color." `book`+`blue` in Feather form **is 📘**: the branding block, the awesome-list rows, and every pattern-001 surface now speak one glyph-word. Kept standing: the `book-open` family grammar, Pharos's listing-size falsifier, and the scope note refined — №92 governs names; D names neither mechanism nor subtraction but *what is protected*.

**ANS:** (by Jérémie Lumbroso)
OK, approving Pharos' recommendation of `book` and `blue`.

---

### QST-STORY-OPENING: Which casting of the "too important" two sentences opens the README?
- Status: answered — Pharos drafted both castings (review F2, 2026-10-17) and routed the pick to the rights-holder ("his edit beats both"); the words are his reframe, so the voice is his to choose
- Why asking: the opening carries the whole launch-story reframe — Closed mode as the product, not the apology. Your own sentence staked this week names the stake: the process that lets people "mediate, granularly, what is public and not."
- Need: pick a letter, edit either freely, or write a third — any shape answers

Options:
- **A — Disciplined** (Pharos): "Small repositories can demonstrate this method by opening their entire record. This Action is the other discipline — **what you do when your deliberations are too important to open**: Ship the code, declare the record, keep the reasoning — a statement of worth, not an apology."
- **B — Closer to your dictation** (Pharos): "Open repositories demo the method with their whole record showing. This one demos **what you do when your deliberations are too important**: A turnkey way to ship the code while the record stays kept — and declared."

**Recommendation**: (by Claude Fable 5)
**A**, by a hair. *Rationale*: "a statement of worth, not an apology" lands the reframe's whole argument in six words, and the triplet "ship the code, declare the record, keep the reasoning" is the mode matrix made breathable; B's "turnkey" is your own word and keeps your cadence — which is why your edit beats both. *Confidence*: 0.55 — this is taste on your voice, which is yours. *If wrong*: B, or your third casting, lands with zero downstream cost; the placement (directly after the bold one-liner) holds either way.

**Recommendation**: (by Mint 5, Lumbroso HQ naming counsel — the delegated strike, 2026-10-26; hub ledger №100 as twice-amended; consolidates the founder's live iteration: "expansive" grist, the clean-room ask, "several levels of my strategy… deeply analyzed," and "take a beat… not at all or gradually")

**A three-tier strike, superseding the A/B binary — each surface faces its own reader (0.75; closed per the delegation, his voice overrides any line):**

1. **README opener** — recruits, by changing the comparison class (the skeptic's "why isn't this open?" dissolves instead of being answered, because the true baseline is that most repositories keep no record at all):

   > "Most repositories ship their code and lose their reasoning — there is nothing left to open. This Action serves the opposite discipline, where every deliberation is kept and publication is a granular choice: ship the code, declare the record, open what you rule. **Closed is still ahead of gone.**"

2. **README second beat** — teaches the product's truest description, which sat under every candidate adjective:

   > "Shipping and disclosing are two decisions; this Action lets them keep separate clocks — open, digest, closed, **or not yet**. 'Not yet' is a setting, not a confession."

3. **DELIBERATIONS-NOTICE story** (per-mirror, where the closed question is actually asked) — carries the founder's real reason, with "live" doing the work "important" wanted to do without the rank a skeptic can mock:

   > "These deliberations are kept whole and still in play — strategy analyzed in depth, across levels, that a game in progress doesn't publish. The disclosure decision keeps its own clock: not at all, later, or gradually — declared, counted, and gated. **A statement of custody, not an apology.**"

*Lineage, so nothing is lost*: Pharos's A triplet lives in tier 1; B's "turnkey" cadence may re-enter at his edit; the founder's "too important" instinct survives as the potency frame ("live"); his "expansive" survives in the claim-class analysis (shape-claims outlast status-claims — a skeptic can contest importance, never extent); his "take a beat" IS tier 2's second clock. *If wrong*: every line here is release-mutable README copy — his edit beats all of it, by standing law.

**ANS:** (by Jérémie Lumbroso, in-session, relayed by Mint 5, 2026-10-26)
"Yes, ship those. They are excellent." — the three-tier strike is ratified as written; tiers 1–2 to the README, tier 3 to the DELIBERATIONS-NOTICE story.

*Implementation note (Covenant 5 / Claude Fable 5, 2026-10-19, post-compaction wake)*: folded as ratified — tiers 1–2 open the README directly under the bold one-liner; tier 3 lands in `write_notice()` (every generated notice now carries the custody story) with the line regression-pinned in `tests/test_mirror.py` so it can be edited deliberately but never dropped silently. The README's sample notice shows it. 16/16 green.

*Amendment (by Jérémie Lumbroso via the publication pharoscan, 16:42 UTC 2026-10-19; folded by Covenant 5)*: tier 1's first sentence ("Most repositories ship their code and lose their reasoning — there is nothing left to open.") is **cut** from the shipped README at his word — Primer 5's blathm hunt filed it as Overclaim/Medium (deletion test: the next sentence carries the contrast; "most"/"nothing left" are unsourced absolutes), and his ruling: *"Good catch. Should be saved as a blathm example case study."* The rest of tier 1 ships as ratified; the strike's full original text stays above, unedited, as the record. The case study routes to Primer's local handbook drafts (publishing frozen per the founder's stop; logging locally allowed).

---

### QST-LICENSE: What license does this repository itself carry?
- Status: answered — by the rights-holder, in-file, 2026-10-18
- Why asking: license posture is per-repo and the rights-holder's alone (HQ `adr:0033`, It-9 doctrine: license artifacts travel by ruling, never by default).
- Need: pick a letter (or override — any shape answers); nothing lands in the tree before your word, and the repo is private until your flip regardless

Options:
- **A — MIT at root, nothing else.** The toolkit's established code posture (template, pneumatic, kintsugi all MIT); simplest, badge-clean.
- **B — MIT at root + a short output note for generated files.** Same MIT, plus a `MIRROR-OUTPUT-NOTE.md` (never appended to LICENSE — the badge lesson is law) stating that files the Action *generates into a mirror* (`DELIBERATIONS-NOTICE.md`, digests) belong to the mirror's owner, carrying the record's terms where one applies — the template-output-grant pattern, applied to this tool's outputs.
- **C — Defer to the counsel round.** Ships nothing until the QST-COUNSEL route runs; blocks any outside adoption meanwhile.

**Recommendation**: (by Claude Fable 5)
**B — MIT root plus the separate output note.** *Rationale*: A alone leaves the generated-files question to inference, and this tool's whole product is other people's repos — the note answers "whose is the notice in MY mirror?" before a stranger asks it; the pattern is already proven on the template (launch night's split restored the badge, and It-9 made the receipt doctrine law); MIT itself is standard text and ships on your go alone per QST-COUNSEL's standing shape, while the note's wording can take a counsel pass before the PUBLIC flip without blocking the private estate. *Confidence*: 0.75. *If wrong*: if counsel reads any output note as inviting more questions than it settles, A + the same sentence as plain README prose — the established fallback.

**ANS:** (by Jérémie Lumbroso)
Yes, Option B. But let's go with Apache 2.0 instead, for patent and trademark reasons, and just rigor.

---

### QST-LISTING-GO: Publish to the Marketplace?
- Status: answered
- Why asking: so the gate is legible in the record rather than ambient — the listing is an outward act.

**ANS:** (by Jérémie Lumbroso)
Yes. This is an important component: It's intimidating to commit your thinking, the good, the bad, the vulnerable — the parts that reveal more about what you think than code would. The most important scaffold to helping people get there is the ability to easily pull a screen of privacy, one that is robust, reliable, easy to access. Publication of `no-adrs-mirror` to the Marketplace is essential from Day 1.

---

## Action Items

- [ ] Branding block in `action.yml` once QST-BRANDING settles — Owner: Covenant 5
- [ ] Teaching error surfaces (tree-identity, token-scope, mixed-commit) in the v2 build — Owner: Covenant 5
- [ ] Marketplace name-availability check for "no-adrs-mirror" at listing time (names drift; check at the gate, not now) — Owner: Covenant 5
- [ ] Listing copy pass — Owner: Pharos 5, at his go
- [ ] **Companion docsite / manual** (the founder's 10-18 commission: the tool is a key user-experience point and a normalizing instrument — the manual teaches the practice, not just the inputs): home on adrs.systems (path tenancy like orrcf), structure = the story → modes → quick start → the laws (visibility, consent, approval) → recipes; drafts mine, surface Pharos's, publication his — Owner: Covenant 5 + Pharos 5
- [ ] Selective ADR retention + filter prompts (his 10-18 feature ask) — concept staked in `seed-2026-10-18-selective-adr-retention-and-filter-prompts.md`, iterating with him before the ADR cuts — Owner: Covenant 5 with Jérémie

## Iterations

- **Iteration 1** (2026-10-15, Covenant 5 / Claude Fable 5): staked the hour the premium ruling arrived (Operator's `1340`); the surface list is Operator's read refined into decisions; the two never-changes named so Marketplace pressure has a wall to meet.
