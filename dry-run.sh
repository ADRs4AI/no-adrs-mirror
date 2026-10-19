#!/usr/bin/env bash
# dry-run.sh — one command, full proof pack. Builds a no-ADRs mirror of a real
# repository LOCALLY (snapshot history, digest dry-run, nothing pushed, no API
# call) and prints everything a reviewer needs: the strip report, the mirror's
# single-commit log, the DELIBERATIONS-NOTICE, the tree, and a suggested README
# line for the source repo.
#
#   ./dry-run.sh <source-repo-path> <owner/slug> [out-dir]
#
# Exit 0 = proof complete. Any failure stops the script (set -e).
set -euo pipefail

SRC="${1:?usage: dry-run.sh <source-repo-path> <owner/slug> [out-dir]}"
SLUG="${2:?usage: dry-run.sh <source-repo-path> <owner/slug> [out-dir]}"
OUT="${3:-$(mktemp -d)/mirror}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "══════════════════════════════════════════════════════════════════"
echo " no-adrs-mirror — DRY-RUN PROOF"
echo " source: $SRC"
echo " slug:   $SLUG"
echo " out:    $OUT   (local only; nothing is pushed, no API call is made)"
echo "══════════════════════════════════════════════════════════════════"

echo
echo "── 1. strip report (what stays, what is withheld, the leak metric) ──"
python3 "$HERE/mirror.py" report --source "$SRC" --repo-slug "$SLUG"

echo
echo "── 2. build: snapshot history, digest index (dry-run) ──"
python3 "$HERE/mirror.py" build --source "$SRC" --repo-slug "$SLUG" \
  --out "$OUT" --history snapshot --digest index --digest-dry-run

echo
echo "── 3. the mirror's entire history (snapshot = one commit, zero leaks) ──"
git -C "$OUT" log --oneline

echo
echo "── 4. DELIBERATIONS-NOTICE.md (the honest badge, verbatim) ──"
cat "$OUT/DELIBERATIONS-NOTICE.md"

echo
echo "── 5. mirror tree (top level) ──"
ls -1 "$OUT"

echo
echo "── 6. suggested README line for the source repo ──"
N_ADR=$(ls "$SRC/docs/adr/" 2>/dev/null | grep -Ec '^[0-9]{4}-' || true)
N_SEED=$(ls "$SRC/docs/adr/" 2>/dev/null | grep -c '^seed-' || true)
echo "  > Deliberation record: $N_ADR ADRs + $N_SEED seeds, maintained with the source; this mirror ships the code. See DELIBERATIONS-NOTICE.md."

echo
echo "══════════════════════════════════════════════════════════════════"
echo " PROOF COMPLETE — nothing pushed, nothing public, no model called."
echo " The flip to public, if ever, is the owner's own act."
echo "══════════════════════════════════════════════════════════════════"
