#!/bin/bash
# loadflake-scan.sh — run the whole ledger UNDER LOAD three times; list the modules that flip.
#
# WHY (owner order :3486): a module whose per-module verdict is green in one loaded pass and
# red / no-result in another is TIMING-SENSITIVE, not defective. This scan finds them mechanically
# so they can be quarantined into tools/release/timing-arm.txt (run standalone) rather than read
# as real reds in the concurrent ledger. Nothing is deleted; the flippers stay in the ledger and
# move to the timing arm.
#
# METHOD: a light CPU load runs alongside (so the ledger runs "under load"), then every test
# module is run per-module three times. A module whose rc is not identical across all three runs
# is FLIPPED and printed with its three rcs (0 = green; non-zero = red or no-result under load).
# A module already in timing-arm.txt that flips only CONFIRMS its listing; a NEW flipper is a
# candidate to add (with a reason and this scan's date as the evidence coordinate).
#
# Usage:  tools/release/loadflake-scan.sh [out-file]     (default /tmp/loadflake-scan.out)
# Cost:   ~three whole-ledger passes under load; run it in the background.
set -u
cd "$(dirname "$0")/../.." || exit 2      # repo root
OUT="${1:-/tmp/loadflake-scan.out}"
RUNS=3

# a background CPU load so the scan genuinely runs under contention
python3 - <<'PY' &
import time, hashlib
end = time.time() + 5400
while time.time() < end:
    hashlib.sha256(b"x" * 100000).hexdigest()
PY
LOADPID=$!
trap 'kill $LOADPID 2>/dev/null' EXIT

declare -A rcs
for r in $(seq 1 "$RUNS"); do
  for f in tests/test_*.py; do
    m="$(basename "$f" .py)"
    PYTHONPATH=src:tests timeout 200 python3 -m unittest "tests.$m" >/dev/null 2>&1
    rcs[$m]="${rcs[$m]:-}$? "
  done
done
kill $LOADPID 2>/dev/null

{
  echo "# loadflake-scan: modules whose per-module rc FLIPPED across $RUNS loaded runs"
  echo "# 0 = green; non-zero = red or no-result under load. Date: $(date -u +%F)"
  for m in $(printf '%s\n' "${!rcs[@]}" | sort); do
    first=""; flip=0
    for v in ${rcs[$m]}; do [ -z "$first" ] && first="$v"; [ "$v" != "$first" ] && flip=1; done
    [ "$flip" -eq 1 ] && echo "$m	FLIPPED	rcs: ${rcs[$m]}"
  done
} > "$OUT"
echo "LOADFLAKE_SCAN_DONE" >> "$OUT"
cat "$OUT"
