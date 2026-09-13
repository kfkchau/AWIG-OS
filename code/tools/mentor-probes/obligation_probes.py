"""Obligation probes (EP-07/07B families). Promises that keep themselves: firing evidence
is the outcome happening; forged markers cannot silence; amendments re-arm; one broken
commitment gags nothing; and it all fires from the record alone (the reboot column)."""
from _harness import build, rebuild, check, refuses, run_report


def main():
    import importlib
    obligations = importlib.import_module("kernel.obligations")
    due, run_due = obligations.due, obligations.run_due

    s, g, v, p, path = build()

    # forged fired-marker via a DIFFERENT action cannot silence (evidence = the outcome op)
    g.execute("CREATE-OBLIGATION", "SYSTEM", {"rule_id": "ob:r", "when": {"elapsed_since": 5},
              "then": {"op": "CREATE-INFO", "params": {"content": "review"}}})
    g.execute("WRITE-ACTIVITY", "alice", {"about": "junk", "obligation_ref": "ob:r"})
    g.execute("TICK", "SYSTEM", {"now": 10})
    check("forged ref (wrong action) does not silence — still due",
          [o["rule_id"] for o in due(s)] == ["ob:r"])
    r = run_due(s, g)
    check("run_due returns {fired, refused} and fires once", r.get("fired") == ["ob:r"])
    check("payloadless outcome op still records evidence (the R25 lesson)",
          any((e.get("payload") or {}).get("obligation_ref") == "ob:r"
              and e["action"] == "CREATE-INFO" for e in s.all()))
    g.execute("TICK", "SYSTEM", {"now": 50})
    check("never twice per version", due(s) == [])

    # amendment re-arms; fires once more; never twice per version
    g.execute("CREATE-OBLIGATION", "SYSTEM", {"rule_id": "ob:r", "when": {"elapsed_since": 3},
              "then": {"op": "CREATE-INFO", "params": {"content": "review-v2"}}})
    g.execute("TICK", "SYSTEM", {"now": 60})
    check("amended obligation re-arms", [o["rule_id"] for o in due(s)] == ["ob:r"])
    run_due(s, g)
    check("re-armed version fires once, then silent", due(s) == [])

    # isolation: a broken commitment gags nothing behind it
    g.execute("CREATE-OBLIGATION", "SYSTEM", {"rule_id": "ob:bad", "when": {"elapsed_since": 1},
              "then": {"op": "GHOST-OP", "params": {}}})
    g.execute("CREATE-OBLIGATION", "SYSTEM", {"rule_id": "ob:good", "when": {"elapsed_since": 1},
              "then": {"op": "CREATE-INFO", "params": {"content": "ok"}}})
    g.execute("TICK", "SYSTEM", {"now": 70})
    r = run_due(s, g)
    check("refused firing recorded-and-continued (no gag)",
          "ob:good" in r.get("fired", []) and "ob:bad" in r.get("refused", []))

    # THE REBOOT COLUMN: a fresh kernel fires ripe obligations from the record alone
    s2, g2, v2, p2 = rebuild(path)
    g2.execute("CREATE-OBLIGATION", "SYSTEM", {"rule_id": "ob:cold", "when": {"elapsed_since": 2},
               "then": {"op": "CREATE-INFO", "params": {"content": "cold"}}})
    g2.execute("TICK", "SYSTEM", {"now": 100})
    s3, g3, v3, p3 = rebuild(path)
    r = run_due(s3, g3)
    check("replay-alone firing (no wall clock anywhere in the loop)",
          "ob:cold" in r.get("fired", []))

    run_report("obligation_probes")


if __name__ == "__main__":
    main()
