#!/usr/bin/env python3
"""planstate — compare a plan's §1 STATE FIELDS against the fold.

WHY THIS EXISTS. mtr's :2309, in its own words: this estate is an append-only
record with every current state a computed view, and §1's state fields are the
one place that rule is broken BY DESIGN — a hand-maintained COPY of the record,
living inside a signed object. Nothing recomputes them and nothing compares them.

EP-30-K1R's §1 read "STATUS: AUTHORED — awaiting countersign" against a board
carrying five lifecycle events. A builder read the object, read the record, and
STOPPED rather than picking. No instrument could have made that catch, because
nothing compared the two. This is that comparison.

THE THIRD INSTANCE OF ONE CLASS IN ONE NIGHT, each trusted because of where it
sits: CLAUDE.md item 49 (:2285), a handover's owed-list (:2296), a signed plan
header (:2309). A stored copy of a computed fact.

SUCCESS ACTION IS INERT. It prints and it exits. It writes nothing, anywhere.
That is deliberate and it is the whole reason this is a separate file rather
than another branch inside the append gate: :2293 — A NEAR-MISS BATTERY IS SAFE
ONLY WHERE THE CHECK'S SUCCESS ACTION IS INERT. The append gate's success action
is a write to the live board, so its own twin harness landed two false events on
the record. This one can be driven against anything, including itself, forever.

    exit 0   §1 agrees with the fold, or carries no state field to disagree
    exit 1   §1 disagrees — the stale-copy defect, reported with both values
    exit 2   the plan or the fold could not be read
    exit 3   input refusal
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

#: §1's fields that are a COPY of something the fold computes. `BUILDER:` is
#: deliberately NOT here — mtr's :2309 keeps it as authored with the tier
#: discrepancy recorded beside it, because "an author editing it to agree with a
#: mistake would launder the mistake." The field that BINDS is not a copy.
STATE_FIELDS = ("STATUS", "TIER")

RE_FIELD = re.compile(r"^\s*(?P<key>STATUS|TIER)\s*:\s*(?P<val>.+?)\s*$", re.M)

#: The closed verb set, matched literally. A §1 STATUS naming no verb at all
#: ("awaiting countersign", "not set here") is not a disagreement — it is an
#: ABSTENTION, and this check does not invent a claim in order to refuse it.
VERBS = (
    "DISPATCHED", "CLOSED", "STOPPED", "RELEASED", "ACCEPTED", "RESUMED",
    "HELD", "OWED", "CORRECTED", "NOTED", "RULED", "COUNTERSIGNED",
    "AUTHORED", "DISAMBIGUATED", "SEATED",
)


def fold_state(item):
    """The item's state AS THE FOLD COMPUTES IT. Never parsed from a summary
    grep — :2311, where counting mentions instead of states put phantom debts
    on two seats including the owner."""
    try:
        out = subprocess.run(
            [sys.executable, "tools/board/board.py", "--board"],
            cwd=REPO, capture_output=True, text=True, timeout=180,
        )
    except Exception as exc:                                   # noqa: BLE001
        print(f"REFUSED: could not drive the fold: {exc}")
        raise SystemExit(2)
    if out.returncode != 0:
        print("REFUSED: the fold does not fold. Nothing is compared against a "
              "broken record.")
        raise SystemExit(2)
    for line in out.stdout.splitlines():
        if line.startswith(item + " ") or line == item:
            rest = line[len(item):].strip()
            for verb in VERBS:
                if rest.startswith(verb):
                    return verb, rest
            return None, rest
    return None, None


def plan_fields(path):
    text = Path(path).read_text(encoding="utf-8")
    return {m.group("key"): m.group("val") for m in RE_FIELD.finditer(text)}


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[0])
        print("usage: planstate.py <planning/exec/EP-XX.md>")
        return 3
    plan = Path(argv[1])
    if not plan.is_file():
        print(f"REFUSED: '{plan}' is not a readable file.")
        return 3
    item = plan.stem

    fields = plan_fields(plan)
    verb, statecol = fold_state(item)

    print(f"PLAN  : {plan}")
    print(f"ITEM  : {item}")
    print(f"FOLD  : {statecol if statecol else 'NO STATE EVENT / UNKNOWN-ITEM'}")
    for key in STATE_FIELDS:
        print(f"§1 {key:<7}: {fields.get(key, '(absent)')}")

    if verb is None:
        print("\nCLEAN — the fold computes no lifecycle state for this item, so "
              "§1 has nothing to disagree with.")
        return 0

    claimed = fields.get("STATUS", "")
    claimed_verbs = [v for v in VERBS if re.search(rf"\b{v}\b", claimed)]

    if not claimed_verbs:
        print(f"\nCLEAN — §1 STATUS names no verb of the closed set, so it makes "
              f"no claim this check can contradict. It ABSTAINS; the fold says "
              f"{verb}.")
        print("        (An abstention is not agreement. A reader still gets the "
              "state from the fold and never from the header.)")
        return 0

    if verb in claimed_verbs:
        print(f"\nCLEAN — §1 STATUS names {verb} and the fold computes {verb}.")
        return 0

    print(f"\nSTALE — §1 STATUS claims {'/'.join(claimed_verbs)} and the fold "
          f"computes {verb}.")
    print("        §1's state fields are a HAND-MAINTAINED COPY of a computed "
          "fact (mtr :2309). The fold is the record; the header is a memory.")
    print("        The splice of §1's STATUS and TIER is the AUTHOR'S act. This "
          "check reports; it never edits.")
    print()
    print("        THIS VERDICT NAMES A DISCREPANCY AND NEVER A CULPRIT (archi, "
          "2026-08-26).")
    print("        A COMPARATOR REPORTS DIVERGENCE AND NEVER DIRECTION. Do NOT "
          "read STALE as")
    print("        'the header is wrong'. EP-30-K1R is the worked example: its "
          "header said")
    print("        STOPPED and was OPERATIONALLY RIGHT, while the fold said RULED "
          "because a")
    print("        later verb from another seat had consumed the state slot. THE "
          "COMPUTED SIDE")
    print("        WAS THE DAMAGED ONE. Only the owners of the two facts know "
          "which lies, which")
    print("        is exactly why this check reports and never edits.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
