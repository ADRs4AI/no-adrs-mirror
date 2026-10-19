# FINDINGS — cold rewrite of subprojects/no-adrs-mirror/README.md

Draft: `README-draft.md` (same folder). 220 lines / 11,191 bytes vs the
current README's 223 / 11,194 — under on both. The three founder-ratified
voice passages are byte-identical (verified mechanically, whitespace-
normalized); only their position changed, which the brief allows. Every
factual claim below was checked against `action.yml`, `mirror.py`,
`dry-run.sh`, `workflows/mirror.yml`, `MIRROR-OUTPUT-NOTE.md`, `proof/`, and
the repo's git tags.

## Verification (claims that did not match the ground truth)

1. **The dry-run stats block's numbers match no receipt in this repo.** The
   README claims `443 kept · 872 withheld`, `975 record-only · 617 code-only ·
   149 MIXED`, `44 staged`, and the sample notice claims `44 ADRs`, source
   commit `8bbb7e5b9e71`. The in-repo proof pack
   (`proof/2026-10-13-vscode-adrs4ai-dry-run.txt`) records `455/884`,
   `995/644/149`, `45 staged`, `45 ADRs`, commit `e4f821910bc1`. Replaced all
   of them with the receipted run and cited the transcript path. The old
   numbers are *plausible* as an earlier HQ-side staging run (ADR-0001 mentions
   `../mirror-action-staging/proof/` at HQ) — **flagged, not disproven**; I
   could not verify them from here.
2. **"live-verified 2026-10-11/12" (Provenance) has no receipt here** — the
   earliest live-trial receipt in `proof/` is 2026-10-17 (titled "first live
   trial"). Replaced with "first live trial 2026-10-17 (`proof/`)"; kept
   "built 2026-08-26" (mirror.py docstring) and "productionized 2026-10-13"
   (action.yml author line), both verifiable.
3. **Sample notice updated to match what `write_notice` actually emits**:
   added the real "…withheld … under: `docs/adr`, …" tail of paragraph 1 and
   the closing "History mode: … Generated … by no-adrs-mirror 0.1.0." line
   (timestamp left as `<UTC timestamp>` — not fabricated); Terms line set to
   the actual `action.yml` default (the old sample silently showed a custom
   `terms` value); citation line uses the run's real slug instead of mixing
   `<owner>/<repo>` placeholders into an otherwise-concrete sample. Sample is
   labeled "counts from the receipted run; prose as `write_notice` writes it
   today" — honest about being a composite.
4. **`@v1` verified**: the tag exists on the repo; the quick-start pin is real.
5. **Mechanical tier made exact**: it keeps the original's conventional-commit
   type (else `chore`); scrub's actual constant line
   `code commit (message withheld)` is now shown (both from the
   `MECHANICAL`/scrub callbacks in mirror.py).
6. **Degrade-law wording scoped to the code**: mirror.py degrades *per-commit*
   (a map miss → mechanical); a missing companion *file* is a hard
   `RuntimeError`, not a degrade. The draft claims only the per-commit
   fallback. NOTE for the crew: `action.yml`'s `message_mode` description
   ("a missing companion file degrades DOWN in warmth") overstates the code —
   not mine to fix in a README pass, but it is the same defect class.

## Inference (places a cold reader must guess — removed the guesswork)

7. **"Modes" implied a `mode` input that does not exist.** The old table
   (none/closed/digest/open) never said how a mode is obtained; a reader scans
   `action.yml` for `mode:` and finds nothing. Reframed as "four postures (no
   `mode` input)" with a "How you get it" column mapping each to real
   configuration (`digest: index|per-adr`, default run, don't install, flip
   the source).
8. **"The mirror" is now defined before it is used** — "a second/separate
   GitHub repository", in the lede, the intro, and the diagram header (the
   founder's "the no-adrs mirror is not clear": the old copy never said the
   mirror is a *repo* until a parenthetical).
9. **"Dry run" is defined before the term is leaned on** (the founder's "what
   is the 'dry-run'?"): first sentence of the section states the mechanism
   (full build, push skipped, nothing leaves), then the two concrete forms —
   local `./dry-run.sh` vs the `dry_run` input — as separate bullets. The old
   section led with the term and folded the CI form into a parenthetical.
10. **Force-push behavior surfaced** ("every run rebuilds and force-pushes;
    the mirror is output — work in the source"): real `push --force` default
    in mirror.py that a stranger would otherwise learn by losing a commit.
11. **Notice non-optionality made precise**: "the Action has no input that
    removes it" (true — `--no-notice` exists only on the CLI and the Action
    never passes it) instead of the bare assertion "The notice is not optional."

## Overclaim (asserted more than the evidence)

12. **"a robust wrapper around `mirror.py`"** → "a wrapper … single typed
    Python file — stdlib only; `anthropic` and `git-filter-repo` installed
    only when used": "robust" is self-certification; verifiable properties
    replace it.
13. **Tier-1 "Needs: A map file (model access to produce it)"** → "a
    `{sha: line}` JSON **you** produce (e.g. model-written)": the Action never
    generates the map; the old parenthetical implied built-in tooling.
14. **"mixed commits survive, and their messages leak"** → "the residual leak
    surface … which is why filter mode pairs with a message tier": under the
    default `scrub` nothing leaks; the flat "leak" overclaimed inevitability
    while the tiers section contradicted it.
15. **"says so honestly" (lede) cut**; "Honest always." / "Honest, at the cost
    of…" (history bullets) replaced by the property that made them true
    ("no messages, nothing to leak"; every surviving message rewritten per
    tier). "Honest" now appears zero times as decoration.

## Gloss / blathm (deleted under the deletion test)

16. **"The point is *poise*: …" paragraph deleted** — names no mechanism; its
    content (source stays the truth; opening later is one decision) is already
    carried by the lede, the law, and voice passage (b).
17. **"The whole integration is one step — a call to this action"** deleted —
    contradicted by the three numbered steps directly below it.
18. **"What it says" column of the modes table** folded away — its content
    ("a record exists; it is withheld") is the notice section's job, where it
    is shown rather than paraphrased.
19. **Heading "Preview before anything ships (the dry run)"** → "Dry run:
    build everything, push nothing" — the heading now states the mechanism
    instead of gesturing at it.

## Structure (reordered or added for the cold reader; wording-neutral)

20. **H1 is `no-adrs-mirror`** (hyphenated, per the pending naming ruling) and
    the draft contains zero occurrences of unhyphenated "no-adrs mirror"
    (mechanically checked), so a later global substitution is one `sed`. The
    engine's own output strings already print the hyphenated form.
21. **Concrete lede first; ratified voice repositioned under "## Why"** right
    after the diagram — the founder's critique arrived against the
    voice-first ordering; the ten-second screen now answers what / to what /
    the one generated artifact, plus the visibility fact.
22. **`token` — the only *required* input — added to the inputs table** (it
    was absent); `terms` row added (it shapes the notice); remaining
    fine-tuning inputs listed by name with a pointer to `action.yml`.
23. **Quick start aligned with the repo's own canonical sample**
    (`workflows/mirror.yml`, snapshot): the old snippet demonstrated
    `history_mode: filter` + `message_mode: mechanical`, contradicting the
    README's own "snapshot is the default" argument; filter stays reachable
    from the snippet as a commented line pointing at Message tiers, and a
    commented `dry_run: "true"` models the safe first run.
24. **Under-strip caution added from the 2026-10-17 live-trial receipt**
    ("record-class files outside the defaults — dry-run first") in the law
    section: a receipted, concrete failure mode the defaults cannot catch.
25. **License paragraph added**: Apache-2.0 + MIRROR-OUTPUT-NOTE's grant
    (generated files belong to the mirror's owner) — the first question a
    launch-page stranger asks that the old README never answered.
26. **Full default strip list (all 10 paths) stated once, up front** — the old
    README only ever showed 3 + "…" in the diagram and 8 in a stats
    parenthetical.

## Could NOT verify (flagged, not guessed)

- The old stats block / old sample-notice numbers (finding 1) — possibly an
  earlier HQ-side run; receipt not in this repo.
- "live-verified 2026-10-11/12" (finding 2) — dropped rather than repeated.
- GitHub's transfer behavior (stars/watchers/issues/redirects) — kept as in
  the original with its GitHub-docs link; not re-tested from here.
- The `ADRs4AI/vscode-adrs4ai` slug (vs the ecosystem's `vscode-adrs-for-ai`
  naming) — kept exactly as the proof transcript records it.
