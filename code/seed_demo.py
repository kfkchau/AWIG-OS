#!/usr/bin/env python3
"""AWIG OS seed demo. One rule, one act allowed, one act refused, one replay.

Run it:  python3 seed_demo.py

Everything it prints, it computed in this run. The record it writes is the only
durable thing; every state it shows is derived from that record and nothing else.
"""

import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
import time

def require_durable_sync():
    """Say why this platform cannot run it, before the engine says it in a traceback.

    The store refuses to append a record it cannot prove reached the disk. On a
    platform with no os.fdatasync that refusal is correct and it fires at the first
    append, three exceptions deep, where a reader cannot see what happened. The
    refusal is the same either way; this one is readable.
    """
    if hasattr(os, "fdatasync"):
        return
    name = os.path.basename(sys.argv[0]) or "seed_demo.py"
    sys.stderr.write(
        "\nThis platform has no os.fdatasync, so a record cannot be proved durable\n"
        "and the engine will not append one. That is the system refusing, not a\n"
        "bug: it does not record an act it cannot show reached the disk.\n"
        "\nYou are most likely on Windows. Run it under WSL:\n"
        "\n    wsl python3 %s\n"
        "\nVerified on Linux, Python 3.12.3. See Platforms in README.md.\n\n" % name
    )
    sys.exit(1)


require_durable_sync()

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))

from kernel.boot import build_kernel                     # noqa: E402
from kernel.errors import OpError                        # noqa: E402
from kernel.canonical import canonical_hash, strip_derivation   # noqa: E402

RULE = "ROOT-NEG-6"
KEY = "demo_setting"


def rule(ch="-", n=72):
    print(ch * n)


def head(n, title):
    print()
    rule("=")
    print("%d. %s" % (n, title))
    rule("=")


def field(name, value, gloss=""):
    """One record field: its name, its value, and one clause saying what it is for.

    Two spaces always separate the value from the clause, so a value wider than its
    column reads as a value that overflowed and never as part of the sentence after it.
    """
    shown = "(empty)" if value is None else str(value)
    print(("    %-12s %-15s  %s" % (name, shown, gloss)).rstrip())


def record_line(path, object_id):
    """Find the line of the record file that carries object_id. Returns (number, bytes).

    Nothing is interpreted here: the line comes back exactly as it sits on disk, so
    what the demo prints next can be checked against the file with an editor.
    """
    with open(path, encoding="utf-8") as fh:
        number = 0
        for line in fh:
            if not line.strip():
                continue
            number += 1
            if json.loads(line).get("object") == object_id:
                return number, line.rstrip("\n")
    raise SystemExit("no record carries %s" % object_id)


def puts_a_law_in_force(entry, laws):
    """True if this record is the one that put some law into the derived law list."""
    named = entry.get("object")
    return named in laws or ("op:%s" % named) in laws or ("view:%s" % named) in laws


def world_of(views):
    """The whole derived world this demo cares about. Computed, never stored."""
    return {
        "laws_in_force": strip_derivation(views.active_rules()),
        "operations": strip_derivation(views.op_definitions()),
        "accounts": strip_derivation(views.accounts()),
        "spaces": strip_derivation(views.spaces()),
        KEY: views.policy_value(KEY),
    }


def exclusive_holders(views, key):
    """Every law in force that fixes `key` exclusively, and to what value.

    These are the same three fields the engine's own consistency check reads, off the
    same view: policy_key, exclusive, value. What prints from this is the INPUT that
    check was handed, not a second opinion computed some other way, and the refusal
    in step 3 quotes the engine's own words back so the two can be compared.
    """
    return [(rid, r.get("value")) for rid, r in views.active_rules().items()
            if r.get("policy_key") == key and r.get("exclusive")]


def holders_line(views, key):
    held = exclusive_holders(views, key)
    return "      laws in force fixing %s exclusively: %s" % (
        key, ", ".join("%s = %s" % h for h in held) if held else "none")


def tally(w):
    """The five readings the fingerprint covers, each with one clause saying what it is.

    Printed in the same shape before and after the replay, so the two blocks can be
    read side by side without deciding whether a difference in wording is a difference
    in fact.
    """
    laws = w["laws_in_force"]
    rows = [
        ("laws in force", len(laws), "every rule the record has put in force"),
        ("operations defined", len(w["operations"]), "the kinds of act the gate will decide"),
        ("accounts", len(w["accounts"]), "the actors the record knows can act"),
        ("spaces", len(w["spaces"]), "the named place rules are scoped to: %s"
                                     % ", ".join(sorted(w["spaces"]))),
        (KEY, w[KEY], "the setting step 2's rule fixed; this demo's own"),
    ]
    return "\n".join("    %-18s %4s   %s" % row for row in rows)


def freeze_line():
    path = os.path.join(HERE, "FREEZE.txt")
    with open(path, encoding="utf-8") as fh:
        return fh.read().strip()


def main():
    started = time.time()
    root = tempfile.mkdtemp(prefix="awig-seed-")
    live = os.path.join(root, "world")
    os.makedirs(live)
    record_path = os.path.join(live, "record.jsonl")

    print()
    print("AWIG OS seed demo")
    print("github.com/kfkchau/AWIG-OS")
    print(freeze_line())
    print("verified platform: Linux. This run: %s %s, Python %s"
          % (platform.system(), platform.machine(), platform.python_version()))
    print("working directory for this run: %s" % root)

    # ---------------------------------------------------------------- 1. the rule
    head(1, "THE RULE, READ BACK OUT OF THE RECORD")
    store, gate, views = build_kernel(record_path)
    founding = store.all()
    laws = views.active_rules()
    from_founding = sum(1 for e in founding if puts_a_law_in_force(e, laws))
    print("  The record now holds %d records. The constitution founded itself into it."
          % len(founding))
    print("  %d of those records each put one law in force. The other %d recorded the"
          % (from_founding, len(founding) - from_founding))
    print("  accounts, the space and the rest. That is the whole relationship between a")
    print("  record and a law here: a law is what a record did, read back.")
    print()

    number, raw = record_line(record_path, RULE)
    print("  The rule this demo runs on is line %d of the record file. Those are its own"
          % number)
    print("  bytes below, %d of them, copied off disk with nothing added or taken away:"
          % len(raw.encode("utf-8")))
    print()
    for start in range(0, len(raw), 84):
        print("      %s" % raw[start:start + 84])
    print()
    print("  Read back out of those bytes, and out of nothing else:")
    law = laws[RULE]
    payload = json.loads(raw)["payload"]
    then = json.dumps(payload["then"], separators=(",", ":"))
    field("rule_id", law["rule_id"], "its name, which decisions cite")
    field("polarity", law["polarity"], "its sign: '-' forbids, '+' requires or permits")
    field("text", law["text"])
    field("enforced_by", law["enforced_by"], "what performs the check")
    field("then", then, "the outcome it names: refuse")
    print()
    print("  Every one of those five values is inside the line printed above it. The line")
    print("  carries %d fields in all, and these five are the ones this demo turns on; the"
          % len(json.loads(raw)))
    print("  rest are the record's own bookkeeping. One of those is worth naming here:")
    print("  record_time, which is UTC, and which is when THIS run founded the rule, not")
    print("  the cut date on the third line of this output.")
    print()
    print("  In plain words, read as it is written: no rule activates until a contradiction")
    print("  check has been run over it. It does not say what the check must find. It says")
    print("  the check is not optional. Both of the next two acts cite this rule for that")
    print("  reason: the same check runs on both, and the check is what decides each one.")
    print()
    print("  A LIMIT, BEFORE YOU READ FURTHER. This rule carries a sentence for a human")
    print("  and an outcome, refuse. It does NOT carry a machine-readable condition")
    print("  saying WHEN to refuse: that lives in the machinery it names in enforced_by,")
    print("  the consistency check. So the record proves which rule was cited and what")
    print("  outcome it names. What the check actually ASKED is shown in steps 2 and 3,")
    print("  and in step 3 the check's own words land in the record where you can read")
    print("  them.")

    # ------------------------------------------------------------- 2. act allowed
    head(2, "AN ACT, ALLOWED, CITING THAT RULE")
    print("  Asking the gate to make a new law: %s = 4, and no other law may set it." % KEY)
    print()
    print("  %s is this demo's own invention. Nothing in the engine reads it, and" % KEY)
    print("  4 is not the point. The point is that it can only be fixed by an act that")
    print("  passes a gate and cites a rule, and that a second law contradicting it is")
    print("  refused and written down. The value is not what is being shown here. The")
    print("  governing of it is.")
    print()
    print("  So, before the gate decides, the check %s requires has to run. Its" % RULE)
    print("  whole question: is any law already in force fixing %s, exclusively," % KEY)
    print("  to some other value? Asked of the world this record derives, right now:")
    print(holders_line(views, KEY))
    print("  Nothing to refuse. Watch the same question get a different answer in step 3.")
    print()
    gate.execute("CREATE-RULE", "SYSTEM",
                 {"rule_id": "law:demo", "policy_key": KEY, "value": 4, "exclusive": True})
    appended = store.all()[-1]
    print("  ALLOWED. One record was appended. Every record in this system carries the")
    print("  same fields; which of them are filled is what tells an act from a refusal:")
    field("seq", appended["seq"], "its place in the record; it never moves")
    field("actor", appended["actor"], "who acted")
    field("action", appended["action"], "which of the defined operations was run")
    field("object", appended["object"], "what the act created")
    field("target", appended["target"], "who a refusal goes back to; none was made")
    field("rule_cited", appended["rule_cited"], "the rule the decision was taken under")
    print()
    op_no, op_raw = record_line(record_path, "op:CREATE-RULE")
    op_def = json.loads(op_raw)["payload"]["definition"]
    op_check = op_def["checks"][0]
    print("  The decision cites %s, and that rule's sign is '-'. An allowed act" % RULE)
    print("  cites a prohibition when the prohibition was TESTED and did not bite. Line %d"
          % op_no)
    print("  of this record defines the CREATE-RULE operation. It names %s as"
          % op_def["law_cited"])
    print("  the law this operation acts under, and hangs one check on it, \"%s\","
          % op_check["check"])
    print("  citing %s if it refuses. That check ran here, over the list shown"
          % op_check.get("cite"))
    print("  above, and had nothing to say. Step 3 is the same check, on the same")
    print("  operation, with something to say.")
    print()
    print("  ONE LIMIT, STATED RATHER THAN IMPLIED: this allowed record does NOT carry a")
    print("  note that the check ran. It carries the rule the decision was taken under,")
    print("  and no more than that. What you can check on this screen is the refusal in")
    print("  step 3, where the check's own words are inside the record itself.")
    print()
    print("  The state that follows from the decision, derived:")
    print("    %s is now %s" % (KEY, views.policy_value(KEY)))

    # ------------------------------------------------------------- 3. act refused
    head(3, "A SECOND ACT, REFUSED, CITING THE SAME RULE")
    print("  Asking the gate for a second law setting the same key to 10.")
    print()
    print("  The same check, on the same operation, asks the same question of a world")
    print("  one record older than the one it asked in step 2:")
    print(holders_line(views, KEY))
    held_id, held_value = exclusive_holders(views, KEY)[0]
    print("  The proposal is 10, and 10 is not 4. This time the check has something to")
    print("  say, and the answer changed because the RECORD changed, not because the")
    print("  question did.")
    print()
    before = len(store.all())
    try:
        gate.execute("CREATE-RULE", "SYSTEM",
                     {"rule_id": "law:demo-2", "policy_key": KEY, "value": 10, "exclusive": True})
        print("  IT WAS NOT REFUSED. That is a failure of this demo.")
        return 1
    except OpError:
        refusal = store.all()[-1]
        print("  REFUSED. The refusal is itself a record, appended like any other. It")
        print("  carries the same fields as the record above, with a different set filled:")
        field("seq", refusal["seq"], "its place in the record; it never moves")
        field("actor", refusal["actor"], "who acted")
        field("action", refusal["action"], "the record's own name for a refusal")
        field("payload.op", refusal["payload"]["op"], "the operation that was refused")
        field("object", refusal["object"], "what was created: nothing, it was refused")
        field("target", refusal["target"], "who the refusal was handed back to")
        field("rule_cited", refusal["rule_cited"], "the same rule as the act above")
        field("refused", refusal["refused"], "the field that makes it a refusal")
        field("reason", refusal["payload"]["message"])
        print()
        print("  That reason is the check's OWN words and it is inside the record, not")
        print("  added by this demo. Follow the chain, and every link of it is on this")
        print("  screen: %s names \"%s\" in enforced_by; line %d hangs a"
              % (RULE, law["enforced_by"], op_no))
        print("  check named \"%s\" on CREATE-RULE citing %s; that check asked"
              % (op_check["check"], op_check.get("cite")))
        print("  the question shown above and found %s fixing %s to %s; the"
              % (held_id, KEY, held_value))
        print("  reason field says exactly that; and the rule's own \"then\" named the")
        print("  outcome all along:  %s" % then)
        print("  Rule, machinery, question, reason, outcome.")
        print()
        print("  And the citation, which is the part worth slowing down for. The refusal")
        print("  cites %s NOT because the new law contradicts %s. It cites"
              % (RULE, RULE))
        print("  it because %s is the rule that made the check compulsory in the" % RULE)
        print("  first place. When the check speaks, it speaks in that rule's name. That")
        print("  is also why a rule about a missing check is the rule a duplicate key is")
        print("  refused under.")
        print()
        print("  The caller was handed that same reason as a raised error, so code cannot")
        print("  carry on unaware of a no. The record and the error say one thing, not two.")
    print()
    print("  Records before the refusal: %d. After: %d. A no costs a record, same as a yes."
          % (before, len(store.all())))
    print("  And the world did not move: %s is still %s" % (KEY, views.policy_value(KEY)))

    # ---------------------------------------------------------------- 4. replay
    head(4, "KILL THE WORLD, REPLAY THE RECORD, COMPARE")
    world_before = world_of(views)
    hash_before = canonical_hash(world_before)
    derived_path = os.path.join(live, "derived-state.json")
    with open(derived_path, "w", encoding="utf-8") as fh:
        json.dump(world_before, fh, indent=1, default=str, sort_keys=True)
    print("  The derived world, written down once so you can watch it be destroyed.")
    print("  These five readings are what the fingerprint below covers, all of them:")
    print(tally(world_before))
    print("    fingerprint  %s" % hash_before)
    print()
    print("  The %d operations are counted inside the %d laws: defining an operation is"
          % (len(world_before["operations"]), len(world_before["laws_in_force"])))
    print("  making a law here, and CREATE-RULE, the act in step 2, is one of them. The")
    print("  %d is the %d founding put in force plus the one step 2 made."
          % (len(world_before["laws_in_force"]), from_founding))
    print()
    print("  Before the kill, %s holds: %s" % (live, sorted(os.listdir(live))))

    replay_dir = os.path.join(root, "replay")
    os.makedirs(replay_dir)
    replay_path = os.path.join(replay_dir, "record.jsonl")
    shutil.copy(record_path, replay_path)
    record_bytes = os.path.getsize(replay_path)
    store.close()
    del store, gate, views
    shutil.rmtree(live)

    print("  KILLED. Does %s still exist? %s"
          % (live, "yes" if os.path.exists(live) else "no, it is gone"))
    print("  Carried across, and nothing else: the record, %d bytes." % record_bytes)
    print("  %s holds: %s" % (replay_dir, sorted(os.listdir(replay_dir))))
    print()
    print("  Rebuilding from that file alone. No cache, no snapshot, no saved state.")
    store2, _gate2, views2 = build_kernel(replay_path)
    world_after = world_of(views2)
    hash_after = canonical_hash(world_after)
    print("    %d records replayed" % len(store2.all()))
    print(tally(world_after))
    print("    fingerprint  %s" % hash_after)
    print()
    print("    before  %s" % hash_before)
    print("    after   %s" % hash_after)
    match = hash_before == hash_after
    print("    %s" % ("IDENTICAL. The world came back, hash for hash." if match
                      else "DIFFERENT. The replay did not return the same world."))
    store2.close()

    rule("=")
    print("Wall clock inside this program: %.2f seconds, first line to last, so Python's"
          % (time.time() - started))
    print("own start-up is not in it. `time python3 seed_demo.py` reads a little higher,")
    print("and the README's timing band is that larger, shell-measured figure.")
    print("The record this ran on is at %s if you want to read it." % replay_path)
    print("Line %d of it is the rule shown in step 1, byte for byte as printed there."
          % number)
    print("Everything this run recorded is under %s, and that directory is" % root)
    print("left in place on purpose so you can read it. Deleting it is safe and undoes")
    print("the whole run. The only other thing written was __pycache__, Python's own")
    print("compiled cache, one beside each of the three packages under src/, which Python")
    print("writes for any program it runs.")
    print("To check all of this independently: python3 check.py")
    rule("=")
    print()
    return 0 if match else 1


if __name__ == "__main__":
    sys.exit(main())
