# Getting started: from nothing to a readable mirror

You have a **private repository** that holds code and thinking. In four steps
you will have a **private mirror** holding only the code — and you will have
*read* exactly what crossed before anything existed anywhere.

Most steps run from the terminal with [GitHub's `gh` CLI](https://cli.github.com)
(`brew install gh` on macOS, [other installs](https://github.com/cli/cli#installation);
then `gh auth login` once).

## Step 1 — preview locally (nothing leaves your machine)

From a clone of this Action's repo, or with `mirror.py` downloaded:

```bash
./dry-run.sh /path/to/your-repo your-org/your-repo
```

It prints: the strip report (what stays, what is withheld, rule by rule), the
mirror's log, the generated `DELIBERATIONS-NOTICE.md`, and the folder holding
the full built tree. Read it like a stranger would. No push, no API call.

## Step 2 — install the workflow (still nothing public)

In your private repo, create `.github/workflows/no-adrs-mirror.yml` — copy the
snippet from the [README's Quick start](../../README.md#quick-start), keeping
`dry_run: "true"` on. Push. The run uploads the built mirror as a **workflow
artifact** (dotfiles and rewritten history included) and its **step summary
shows what every strip rule removed**. Download the artifact; read it.

```bash
gh run list --workflow no-adrs-mirror.yml     # find the run
gh run download <run-id>                      # fetch the preview artifact
```

## Step 3 — the token (your only account act)

The default CI token cannot push to another repository. Create one that can:

- **Fine-grained PAT** (Settings → Developer settings): resource owner = your
  org; repository access = the mirror repo (or all, if it doesn't exist yet);
  permissions = **Contents: Read and write** AND **Workflows: Read and write**
  (mirrors deliberately carry your live CI — GitHub refuses workflow files
  without it).
- Store it where only Actions can read it — never in a file, never in chat:

```bash
gh secret set MIRROR_TOKEN -R your-org/your-repo    # paste at the hidden prompt
```

## Step 4 — go live, private

Remove the `dry_run` line (or set `"false"`), push. The mirror appears at
`your-repo-no-adrs`, **private, always** — the Action has no input that makes
anything public. Check it:

```bash
gh repo view your-org/your-repo-no-adrs             # exists, private
gh api repos/your-org/your-repo-no-adrs --jq .private   # true
```

Read the mirror itself the way a stranger would — then, when you are ready for
strangers, continue to [Going public](02-going-public.md).
