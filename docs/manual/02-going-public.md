# Going public: the consent gate, the flip, and what strangers see

Making the mirror public is one click — which is exactly why everything on
this page happens **before** it.

## 1 — declare `approved_paths` (the fail-closed consent gate)

List the top-level roots that kept files may live under, in the workflow:

```yaml
          approved_paths: |
            src
            tests
            README.md
            LICENSE
```

The contract this buys you: **any kept path outside these roots stops the sync
before anything is written**, naming the new entries — a file added next month
in a folder you never reviewed can never ride a sync silently. And a PUBLIC
mirror with no `approved_paths` at all refuses to push entirely (the failure
prints the roots it would need).

Where does the list come from? Your preview's step summary (every rule, every
kept top) — or let the gate generate it: flip first, push once, and the
fail-closed stop prints exactly the roots a deliberate approval needs.

**If you use `history_mode: filter`**, the gate checks every path that **ever
existed** in your history, not just today's tree — history publishes deleted
files' paths too. The failure message says which historical entries need a
verdict: approve them, or strip them (e.g. `*.vsix` build artifacts you
deleted years ago).

## 2 — the flip (always yours)

```bash
gh repo edit your-org/your-repo-no-adrs --visibility public --accept-visibility-change-consequences
```

The Action never does this, has no input for it, and never will — build
everything up to the flip; the flip is human.

## 3 — after the flip

- Every successful sync now **publishes immediately**; the gate above is what
  makes that safe.
- The `DELIBERATIONS-NOTICE.md` is now a public page: it declares your record
  exists, counts it, and says who decides its release — a statement of
  custody. Set the `terms` input if a truer sentence exists for your project.
- Your live CI runs publicly (test workflows stay enabled by design; publish
  workflows were moved to `.github/workflows-disabled/` with a note).
- Contributions: the mirror's code is byte-identical to yours on every kept
  path, so patches port exactly. Until automated round-trip ships, say in your
  mirror's description where contributions belong.
