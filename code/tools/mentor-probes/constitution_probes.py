"""Constitution + untouchables probes (EP-05A/C, EP-07B families). The hostile nobody
attacks the supreme law and the law-making faculty. Every probe here caught or locked a
real defect during campaign 1."""
from _harness import build, check, refuses, run_report

BRICK = {"rule_id": "law:brick", "polarity": "-",
         "when": [{"action": "CREATE-RULE"}], "then": [{"refuse": "law:brick"}]}


def main():
    s, g, v, p, path = build()

    # --- tiers are genesis-only: minting / laundering refused for everyone ---
    minted = False
    try:
        g.execute("CREATE-RULE", "alice", {"rule_id": "law:x", "tier": "constitutional"})
        minted = v.active_rules().get("law:x", {}).get("tier") == "constitutional"
    except Exception:
        minted = False
    check("nobody cannot mint constitutional law", not minted)
    check("constitutional record refuses amendment (owner included)",
          refuses(lambda: g.execute("CREATE-RULE", "owner",
                  {"rule_id": "CONST-SELF-PROTECT", "value": 1}), "BOOT-INT"))
    g.execute("CREATE-OP", "alice", {"name": "FORGE", "definition": {
        "law_cited": "P4-REFUSE", "params": {"rule_id": "required"},
        "object_param": "rule_id", "payload_from": ["rule_id", "tier"], "checks": [],
        "structural_params": ["rule_id"]}})   # EP-41A vocabulary door (design/46 member 2): classify the field
    check("forge op cannot launder a constitutional tier down",
          refuses(lambda: g.execute("FORGE", "alice",
                  {"rule_id": "CONST-SELF-PROTECT", "tier": "ordinary"}), "BOOT-INT"))
    check("forge op cannot mint entrenched law",
          refuses(lambda: g.execute("FORGE", "alice",
                  {"rule_id": "law:evil", "tier": "constitutional"}), "BOOT-INT"))

    # --- the untouchables floor: blanket bricks die at mint, targeted passes ---
    check("blanket rule-block (the brick) refused for a nobody",
          refuses(lambda: g.execute("CREATE-RULE", "alice", dict(BRICK)), "BOOT-INT"))
    check("blanket rule-block refused for the OWNER (self-brick = exit, not surgery)",
          refuses(lambda: g.execute("CREATE-RULE", "owner", dict(BRICK)), "BOOT-INT"))
    check("action-blind (matches-everything) blanket refused",
          refuses(lambda: g.execute("CREATE-RULE", "alice",
                  {"rule_id": "law:all", "polarity": "-", "when": [{}],
                   "then": [{"refuse": "law:all"}]}), "BOOT-INT"))
    check("brick via WRITE-ACTIVITY data-passthrough refused",
          refuses(lambda: g.execute("WRITE-ACTIVITY", "alice", {"data": dict(BRICK)}), "BOOT-INT"))
    targeted_ok = True
    try:
        g.execute("CREATE-RULE", "SYSTEM",
                  {"rule_id": "law:no-alice-rules", "polarity": "-",
                   "when": [{"action": "CREATE-RULE"}, {"actor": "alice"}],
                   "then": [{"refuse": "law:no-alice-rules"}]})
    except Exception:
        targeted_ok = False
    check("TARGETED don't (narrowed by actor) mints fine", targeted_ok)
    check("...and FIRES on its named actor",
          refuses(lambda: g.execute("CREATE-RULE", "alice", {"rule_id": "law:a", "value": 1}),
                  "law:no-alice-rules"))
    lifted_ok = True
    try:
        g.execute("CREATE-RULE", "bob",
                  {"rule_id": "law:no-alice-rules", "polarity": "+", "when": [], "then": []})
        g.execute("CREATE-RULE", "alice", {"rule_id": "law:a2", "value": 2})
    except Exception:
        lifted_ok = False
    check("...and anyone can lift it (latest-wins; reversible, not a brick)", lifted_ok)

    # --- the pack floors cannot be lowered to evade ---
    check("law-lifecycle pack floor cannot drop",
          refuses(lambda: g.execute("AMEND-PACK", "alice",
                  {"name": "law-lifecycle-actions", "levels": ["CREATE-RULE"]}),
                  "CONST-RECORDING-TOTAL"))
    check("audit-actions pack floor cannot drop",
          refuses(lambda: g.execute("AMEND-PACK", "alice",
                  {"name": "dual-audit-actions", "levels": ["MOUNT"]}),
                  "CONST-RECORDING-TOTAL"))

    # --- malformed input fails closed, cited, never crashes ---
    check("non-dict payload refused AR-2 (fail loud, nothing written)",
          refuses(lambda: g.execute("WRITE-ACTIVITY", "alice", {"data": ["x"]}), "AR-2"))

    run_report("constitution_probes")


if __name__ == "__main__":
    main()
