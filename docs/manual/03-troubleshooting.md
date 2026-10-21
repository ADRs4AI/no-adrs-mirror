# Troubleshooting: every failure our own first runs hit

This Action was dogfooded on its own founding repositories; each failure below
fired for real, taught something, and became a guard. If you hit one, it is
working as designed — here is the fix.

## "token input is empty — set the MIRROR_TOKEN secret"

The preflight, before anything builds. Create the token
([Getting started §3](01-getting-started.md)) and store it:
`gh secret set MIRROR_TOKEN -R your-org/your-repo`. Previews (`dry_run: "true"`)
need no token at all.

## "refusing to allow a Personal Access Token to create or update workflow"

GitHub's rule, at push time: mirrors carry your live CI workflows, and the
token lacks workflow authority. Fine-grained PAT → edit it → add
**Workflows: Read and write** (no re-mint needed). Classic PAT → it needs the
`workflow` scope.

## "approved-paths gate: N kept path(s) outside the approved roots"

The fail-closed consent gate, stopping **before** anything is written. The
message names the new top-level entries. For each: approve it (add to
`approved_paths`) or strip it (add to `additional_strip_paths`). In filter
mode the gate checks paths from your **entire history** — deleted files
included, because published history includes them.

## "mirror is PUBLIC and no approved_paths are declared"

The public-era bootstrap: a public mirror never receives an unreviewed push.
The failure prints this build's top-level roots — review, declare, re-run.

## "cannot determine the mirror's visibility"

The lookup failed and `create_if_missing` is off — unknown stops, it never
means "private". Usually the token can't see the target: check its repository
access, or enable `create_if_missing` if the mirror genuinely doesn't exist.

## "push target resolves to <other-name> via a rename redirect"

The named mirror was renamed away; pushing through the redirect would land on
the OLD repository and its object store. Name the real repo, or enable
`create_if_missing` to create the named repo fresh (which breaks the redirect).

## "state persist failed — grant 'permissions: contents: write'"

Filter mode pushes its state branch (`no-adrs-mirror/state`) back to the
source repo, and the workflow's default `GITHUB_TOKEN` is read-only. Add at
the top level of the calling workflow:

```yaml
permissions:
  contents: write
```

The run fails loudly instead of silently rebuilding next time.

## "incremental state is present but the mirror's objects are unreachable"

Phase B continues the previous rewrite, whose objects live in the mirror —
the build must be able to *read* the mirror. Usually the token can't see it:
fix credentials/URL, or **declare** a rebuild with `history_epoch: "new"`.
The engine never silently rebuilds: that would break every link without a
declared epoch.

## "phase B push was not a fast-forward"

The mirror's history diverged from what this sync extends (someone pushed to
the mirror by hand, or an epoch happened elsewhere). Reconcile by hand, or
declare a new epoch (`history_epoch: "new"` — full rebuild, force-push, said
in the notice). Incremental syncs never force.

## "TypeError: %b requires a bytes-like object … not 'int'" (inside git-filter-repo)

Upstream git-filter-repo 2.47.0 crashes writing its run metadata on an
incremental (`--state-branch`) sync whose delta contains **pruned
commits** — for this Action, any record-only commit, the most common push
in a deliberating repo. The engine ships a pinned shim
(`filter_repo_shim.py`) that resolves the offending integer marks through
filter-repo's own `target-marks` mapping, so a current version of the
Action never shows this error. If you see it, you are running an engine
older than v0.5.0 or invoking `git filter-repo` directly: update the
Action (`@v1` floats), or run the shim in place of the bare tool.
Full forensic: ADR-0001 Iterations 8–9.

## "metadata references mark N but target-marks has no hash for it"

The shim's own refusal: a rewritten object this run never materialized, and
persisting state that references it would break the *next* sync. Declare a
rebuild with `history_epoch: "new"` (full epoch, disclosed in the notice) and
report the occurrence — this path is believed unreachable after the engine's
record-only short-circuit, so a sighting is valuable data.

## Two runs racing

The shipped snippets carry a `concurrency` block (newest run wins, older one
cancels). If you removed it, racing pushes can force-push over each other —
put it back.

## Reading any failure

Every stop writes a teaching block to the run's **step summary** — start
there, not in the raw log. The summary also carries the per-rule removal log
on every successful build.
