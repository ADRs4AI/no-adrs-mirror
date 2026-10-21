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

## Two runs racing

The shipped snippets carry a `concurrency` block (newest run wins, older one
cancels). If you removed it, racing pushes can force-push over each other —
put it back.

## Reading any failure

Every stop writes a teaching block to the run's **step summary** — start
there, not in the raw log. The summary also carries the per-rule removal log
on every successful build.
