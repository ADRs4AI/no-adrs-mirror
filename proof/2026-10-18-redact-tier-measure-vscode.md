# Tier 1.5 (redact) measured against the live corpus — 2026-10-18

Dictionary: `dictgen` over both hive registries + founder terms → **45 terms, 8 builtin patterns** (ids, QST handles, Addresses, It-N, №, version parens).

Applied to all **563 surviving subjects** of `ADRs4AI/vscode-adrs4ai`:

| Result | Count |
|---|---|
| Untouched by the dictionary | 427 |
| Redacted (≥1 token replaced) | 136 |

**The specimen that defines the tier's limit** (kept verbatim as the canonical example of bounded recall):

> BEFORE: `fix: a malformed ANS slot was prefilled as his draft — "PARALYZING" (v0.7.136)`
> AFTER:  `fix: a malformed ANS slot was prefilled as his draft — "PARALYZING" ‹…›`

The version tag goes; the quoted founder word and the narrative voice **survive** — no dictionary can know them. Conclusion, as positioned in the README ladder: `redact` is right for terse-conventional repos where known tokens are the only leak class; narrative houses (this one) stay on `map`. The sample mirror therefore remains on tier 1; this measure is why.

— Covenant 5 (Claude Fable 5), measured live, dictionary sha in the notice when used
