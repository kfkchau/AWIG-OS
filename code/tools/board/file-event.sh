#!/usr/bin/env bash
# APPEND GATE for planning/build/BOARD-EVENTS.log. Both halves, as a GATE and not
# a report.
#   BEFORE: drive the real fold. Refuse to append onto a broken board.
#   AFTER : drive the real fold. On refusal, REMOVE the line just added and restore.
# "A refusal you have to notice is not a gate." Nothing here depends on anyone
# reading the output.
#
# MOVED INTO THE REPO 2026-08-27. It lived in a /tmp scratchpad for its whole
# life and an app restart made it unreachable mid-arc — the tool enforcing this
# estate's append discipline was itself sitting somewhere that does not survive
# a restart. That is P4's own lesson (standing behaviour must live in files the
# harness reloads, never in ephemeral state) applied to the gate that enforces
# the rest of it. Four gaps were found and paid in this file on 2026-08-26; the
# comments below are kept because each one names what it cost.
set -uo pipefail
R=<HOME>/Documents/Claude/apps/gov-os
LOG=$R/planning/build/BOARD-EVENTS.log
BODY=${1:?usage: file-event.sh <file-containing-one-EVT-line>}

# GAP 3, found 2026-08-26 the only way this estate ever finds anything — by an
# ATTEMPT. Called with five args instead of one, `cat` failed, the redirect wrote
# ZERO bytes, and this script printed "FILED". A gate that reports success on a
# total no-op is the check-that-cannot-fail in its worst form: it does not merely
# miss a defect, it MANUFACTURES a green. Four guards, each able to fail:
[ -f "$BODY" ] || { echo "REFUSED: '$BODY' is not a readable file. This gate takes ONE argument: a file holding one EVT line."; exit 6; }
[ -s "$BODY" ] || { echo "REFUSED: '$BODY' is empty. An empty append is a no-op that used to print FILED."; exit 6; }
NL=$(grep -c '' "$BODY")
[ "$NL" -eq 1 ] || { echo "REFUSED: '$BODY' holds $NL lines; exactly 1 is required."; exit 6; }
grep -qE '^EVT \| [0-9]{4}-[0-9]{2}-[0-9]{2} \| [^|]+ \| [^|]+ \| [^|]+ \| ' "$BODY" \
  || { echo "REFUSED: '$BODY' does not match the EVT grammar (EVT | date | item | verb | seat | body)."; exit 6; }

cd "$R" || exit 9
python3 tools/board/board.py --board >/dev/null 2>&1 || { echo "REFUSED: board does not fold BEFORE the append — not writing onto a broken record"; exit 2; }

# :1577 — RESOLVE BEFORE ACTING. A lifecycle verb changes an item's STATE, and a
# state written on an envelope's word is a verb on evidence that may never land.
# "The file is truth, chat is the doorbell" — founding law, never a step until now.
LINE=$(cat "$BODY")
VERB=$(echo "$LINE" | awk -F' \\| ' '{print $4}' | sed 's/(.*//')
case "$VERB" in
  DISPATCHED|CLOSED|STOPPED|RELEASED|ACCEPTED|RESUMED|HELD|OWED)
    ITEM=$(echo "$LINE" | awk -F' \\| ' '{print $3}')
    REF=$(echo "$LINE" | grep -oE 'AUTHORISED-BY: :[0-9]+' | head -1 | grep -oE '[0-9]+')
    if [ -z "$REF" ]; then
      echo "REFUSED: verb '$VERB' changes STATE and names no AUTHORISED-BY: :N."
      echo "         A state written on an envelope's word is a verb on evidence that may never land."
      exit 4
    fi
    RN=$(wc -l < "$LOG")
    if [ "$REF" -lt 1 ] || [ "$REF" -gt "$RN" ]; then
      echo "REFUSED: AUTHORISED-BY: :$REF is out of range (board is $RN lines)"; exit 5; fi
    RITEM=$(sed -n "${REF}p" "$LOG" | awk -F' \\| ' '{print $3}')
    echo "AUTHORISED-BY :$REF -> $RITEM"

    # GAP 1, paid 2026-08-26. Bitten TWICE before this: :2189 cited :2176 naming a
    # different item and filed anyway; :2281 cited :2261 (EP-30-K2) from a line on
    # EP-30-K1R. The gate EXTRACTED the item and PRINTED it and never COMPARED it —
    # a check that computes the right value and then declines to use it.
    #
    # It does NOT refuse outright, because :2281 was SUBSTANTIVELY CORRECT: mtr's
    # ruling ON K2 is what authorised a K1R dispatch. Cross-item authority is real.
    # What must be impossible is cross-item authority ARRIVING BY ACCIDENT. So the
    # mismatch is lawful only when the line SAYS SO in its own body.
    if [ "$RITEM" != "$ITEM" ]; then
      if echo "$LINE" | grep -q 'CROSS-ITEM AUTHORITY:'; then
        echo "         cross-item, DECLARED in the body — allowed ($RITEM -> $ITEM)"
      else
        echo "REFUSED: AUTHORISED-BY :$REF names item '$RITEM' but this line is on '$ITEM'."
        echo "         Cross-item authority is LAWFUL and must never be ACCIDENTAL."
        echo "         If deliberate, say so in the body: CROSS-ITEM AUTHORITY: <why>."
        exit 10
      fi
    fi

    # GAP 2, paid the same turn. The gate never asked whether the cited line still
    # STANDS. :2113 cited :2102, which the fold marks VOID. Citing a voided act is
    # citing something the record has already withdrawn.
    #
    # HONEST CAP, filed at :2340: this resolves :N BY POSITION, and BOARD-GRAMMAR
    # holds that a line number is a ROLE and the event's identity is its CONTENT.
    # A surgical removal re-aims every :N above it. Driven 2026-08-26: no citation
    # filed below the one removal point pointed above it, so nothing has shifted —
    # but the exposure is structural and complete, and the correct form binds by
    # content digest. Owed by mgr.
    if python3 tools/board/board.py --ep "$RITEM" 2>/dev/null \
       | grep -E "^  :$REF " | grep -q 'VOID'; then
      echo "REFUSED: AUTHORISED-BY :$REF is marked VOID by the fold on item '$RITEM'."
      echo "         A voided act cannot authorise anything. Cite the line that stands."
      exit 11
    fi
    ;;
esac

# THE OUTWARD GATE — archi's :2253 ruling, built rather than written down.
# §5's concurrency clause guards INWARD: it protects this unit's arm from other
# seats' work. Nothing protects other seats' in-flight work from THIS unit's
# edits. The outward hazard is an INTERVAL OVERLAP and the only seat that sees
# both intervals is the one holding the conjunction. That is this seat.
#
# :2250 was this ruling's first performance and it was performed BY HAND, on a
# ground that turned out to be false. A hold placed on a condition that cannot
# occur discharges on nothing. THAT is why this is code.
#
# HONEST CAP, filed at :2335 and converging with the :848 OWED against mgr: this
# keys on a BOARD VERB as a proxy for live work. A board verb is a claim another
# seat can overwrite — it is the one signal in this estate a third party can
# change. A unit can fold DISPATCHED with its builder finished (refuses a safe
# dispatch), and a unit can have a LIVE builder while its slot says something
# else (allows an unsafe one). The correct form asks `ps` for a live arm and
# `git status` for a dirty fence, using the verb only as a third signal.
if [ "$VERB" = "DISPATCHED" ]; then
  DITEM=$(echo "$LINE" | awk -F' \\| ' '{print $3}')
  PLAN="planning/exec/${DITEM}.md"
  if [ -f "$PLAN" ]; then
    # §5 fence members under tests/ are the shared surface a suite run reads.
    SHARED=$(awk '/^# 5 —/,/^# 6 —/' "$PLAN" | grep -oE '(^|[[:space:]])tests/[A-Za-z0-9_./-]+\.py' | tr -d ' ' | sort -u)
    if [ -n "$SHARED" ]; then
      OTHERS=$(python3 tools/board/board.py --board 2>/dev/null \
               | awk '$2=="DISPATCHED"{print $1}' | grep -vx "$DITEM" || true)
      if [ -n "$OTHERS" ]; then
        echo "REFUSED: OUTWARD GATE (archi :2253). '$DITEM' fences shared test files:"
        echo "$SHARED" | sed 's/^/           /'
        echo "         and these items are DISPATCHED and may have work in the tree:"
        echo "$OTHERS" | sed 's/^/           /'
        echo "         §5 protects THIS unit's arm from them. Nothing protects THEM from this"
        echo "         unit's edits. Land or hold the others, or file a HELD naming a condition"
        echo "         that CAN occur — :2250's could not, and that is why this is a check."
        exit 8
      fi
    fi
  fi
fi

BEFORE=$(wc -l < "$LOG")

cat "$BODY" >> "$LOG"
AFTER=$(wc -l < "$LOG")

if ! python3 tools/board/board.py --board >/dev/null 2>&1; then
  echo "REFUSED: the line just appended BREAKS the fold. Removing it and restoring."
  python3 tools/board/board.py --board 2>&1 | head -2 | sed 's/^/    /'
  python3 - "$LOG" "$BEFORE" <<'PY'
import sys
p,keep=sys.argv[1],int(sys.argv[2])
ls=open(p,encoding='utf-8').read().split('\n')
open(p,'w',encoding='utf-8').write('\n'.join(ls[:keep])+'\n')
PY
  python3 tools/board/board.py --board >/dev/null 2>&1 && echo "    RESTORED, fold rc 0 at $(wc -l < "$LOG") lines" || echo "    RESTORE FAILED — STOP"
  exit 3
fi
if [ "$AFTER" -ne $((BEFORE + 1)) ]; then
  echo "REFUSED: the board went $BEFORE -> $AFTER. Exactly one line must land."
  echo "         This is the guard that would have caught GAP 3 at the write instead of the read."
  echo "         RESIDUAL, filed :2337: under a concurrent append from another seat this"
  echo "         fires on a line that DID land — a false alarm rather than a false green,"
  echo "         which is the safe direction and still wrong. The correct form identifies"
  echo "         its own line by content digest, not by arithmetic on a shared counter."
  exit 7
fi
echo "FILED    : line $AFTER (was $BEFORE)"
# GAP 4, found 2026-08-26 by a concurrent append from another seat. `tail -1`
# reports whatever is LAST AT READ TIME, not the line this call appended — so
# under concurrency it echoed ANOTHER SEAT'S line as confirmation of mine. The
# +1 count check was right and only the DISPLAY lied, which is the same family
# as GAP 3: a confirmation that reads as proof and is not.
echo "IDENTITY : $(sed -n "${AFTER}p" "$LOG" | cut -c1-60)"
echo "FOLD     : rc 0 before AND after"
