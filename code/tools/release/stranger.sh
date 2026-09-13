#!/bin/bash
# stranger.sh — run the public suite under the :3460 gate form, as a script the ledger runs.
#
# THE :3460 GATE FORM (owner ruling, EP-RELEASE-COPYOUT-2 C6(2)): every public-suite figure
# is taken on a CLEAN SCRATCH and a STOCK HOME. The earlier "clean" figures were tainted by
# ~/gov-lab on the import path (fusepy imported from ~/gov-lab/fuse.py), so a stock machine's
# result differed from the estate's. This script makes the honest form mechanical:
#
#   CLEAN SCRATCH : /tmp/govos-conformance removed before the run (the conformance fixtures'
#                   standing world is not a shipped dependency; a downloader has no warm world).
#   STOCK HOME    : HOME set to a fresh empty dir with no ~/gov-lab, so os.path.expanduser("~/...")
#                   resolves nowhere and any third-party adapter (fusepy) is genuinely absent —
#                   its tests skip, exactly as on "python3 and nothing else".
#
# Usage:   tools/release/stranger.sh <shipped-code-dir>
#   e.g.   tools/release/stranger.sh ../awig-os/code
# Exit:    the public suite's own rc (0 = 0 failures / 0 errors); prints the modules: summary line.
set -u

CODE="${1:?usage: stranger.sh <shipped-code-dir> (the folder holding run_public_suite.py)}"
if [ ! -f "$CODE/run_public_suite.py" ]; then
  echo "stranger.sh: no run_public_suite.py under $CODE" >&2
  exit 2
fi

STOCKHOME="$(mktemp -d /tmp/govos-stockhome.XXXXXX)"
cleanup() { rm -rf "$STOCKHOME"; }
trap cleanup EXIT

# CLEAN SCRATCH — remove the conformance fixtures' standing world (a downloader has none).
rm -rf /tmp/govos-conformance 2>/dev/null

# STOCK HOME — no ~/gov-lab on the path; the third-party adapter is genuinely absent.
( cd "$CODE" && HOME="$STOCKHOME" python3 run_public_suite.py )
rc=$?

echo "stranger.sh: gate form = clean scratch (/tmp/govos-conformance removed) + stock HOME ($STOCKHOME); public-suite rc=$rc"
exit $rc
