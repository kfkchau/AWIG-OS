#!/usr/bin/env bash
# SYNTHETIC. Never executed. Its answer is written down HERE, before the lint ran,
# so the run below is a check that could have failed and not a demonstration.
#
# EXPECTED, decided before the first invocation:
#   the `grep | tail` read by `$?`          PRIMARY   EXPLICIT-$?    2 stages
#   the `LAST=$(grep | tail)` read by `$?`  PRIMARY   CAPTURE-RC     2 stages
#   the `if grep | grep -q`                 SECONDARY IMPLICIT-TEST  2 stages
#   the pipeline AFTER `set +o pipefail`    PRIMARY   EXPLICIT-$?    2 stages
#   and NOTHING for the pipeline that sits between `set -o pipefail` and
#   `set +o pipefail`, which is the negative half.
#
# DISCLOSED CORRECTION. The first draft of this block named LINE NUMBERS
# 12/16/20/27 and the lint reported 13/17/21/30. The lint is right and the
# hand-count was wrong: `grep -n` on this file puts those statements at 13, 17,
# 21 and 30. The prediction is restated above BY STATEMENT rather than by line
# so that a later edit to this header cannot silently falsify it again — and the
# part of the prediction that was load-bearing (WHICH statements, WHICH kind,
# WHICH are primary, and that the pipefail-protected one stays silent) was
# written before the run and held exactly.
set -u

grep DISPATCHED "$BOARD" | tail -1
rc=$?
[ "$rc" -eq 0 ] || echo "no dispatch found"

LAST=$(grep CLOSED "$BOARD" | tail -1)
rc=$?
[ "$rc" -eq 0 ] || echo "no close found"

if grep OWED "$BOARD" | grep -q pipe; then
  echo "the duty is open"
fi

set -o pipefail
grep OWED "$BOARD" | wc -l
rc=$?

set +o pipefail
grep OWED "$BOARD" | wc -l
rc=$?
