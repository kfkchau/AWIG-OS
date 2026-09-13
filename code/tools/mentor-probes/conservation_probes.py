"""Conservation probes (EP-05C, EP-08B, R18 families). The careless owner and the reboot:
protection must survive the documented amendment path AND a replay. The reboot column has
caught three half-fixes; never skip it."""
from _harness import build, rebuild, check, refuses, run_report

DEF = {"description": "amended", "params": {"region": "required", "bytes": "required"},
       "law_cited": "MEM-LAW-BUDGET", "object_param": "region",
       "payload_from": ["region", "bytes"], "checks": [],
       "structural_params": ["region", "bytes"]}   # EP-41A vocabulary door (design/46 member 2): classify the fields


def main():
    s, g, v, p, path = build()

    # --- ops: the shield never drops through amendment ---
    check("bare retire of an owner-tier core refused (owner included)",
          refuses(lambda: g.execute("RETIRE-OP", "owner", {"name": "MEM-GRANT"}), "BOOT-INT"))
    check("nobody cannot AMEND-OP a core",
          refuses(lambda: g.execute("AMEND-OP", "alice",
                  {"name": "MEM-GRANT", "definition": DEF}), "BOOT-INT"))
    amended = False
    try:
        g.execute("AMEND-OP", "owner", {"name": "MEM-GRANT", "definition": DEF})
        amended = (v.op_definitions()["MEM-GRANT"]["tier"] == "owner"
                   and g.has("MEM-GRANT"))
    except Exception:
        amended = False
    check("owner amends in place: tier conserved, op live throughout", amended)
    check("demotion shape via passthrough refused",
          refuses(lambda: g.execute("WRITE-ACTIVITY", "alice",
                  {"data": {"kind": "op_definition", "name": "MEM-GRANT",
                            "definition": DEF}}), "BOOT-INT"))
    check("content-def amendment in a BARE (blobless) kernel refused (the R18 lesson)",
          refuses(lambda: g.execute("AMEND-OP", "owner", {"name": "MEM-GRANT",
                  "definition": {**DEF, "params": {"region": "required", "content": "required"},
                                 "content_params": {"content": "content_hash"}}}), "BOOT-INT"))

    # --- master views: conservation reaches the view surface (EP-08B) ---
    check("nobody cannot supersede a master view",
          refuses(lambda: g.execute("CREATE-VIEW", "alice",
                  {"name": "rule-master", "when": {"actor": "x"},
                   "then": {"move_to": "ch:j"}}), "BOOT-INT"))
    owner_rebind = False
    try:
        g.execute("CREATE-VIEW", "owner", {"name": "rule-master", "bind": "active_rules", "then": {}})
        owner_rebind = (v.view_definitions()["rule-master"]["tier"] == "owner"
                        and v.master("rule-master") is not None)
    except Exception:
        owner_rebind = False
    check("owner re-binds a master: tier conserved, master live", owner_rebind)
    ordinary_free = True
    try:
        g.execute("CREATE-VIEW", "alice", {"name": "mine", "when": {"actor": "z"}, "then": {"move_to": "ch:m"}})
        g.execute("CREATE-VIEW", "bob", {"name": "mine", "when": {"actor": "q"}, "then": {"move_to": "ch:m"}})
    except Exception:
        ordinary_free = False
    check("ordinary views stay free (v1 unchanged)", ordinary_free)

    # --- THE REBOOT COLUMN: live state == replayed state, always ---
    s2, g2, v2, p2 = rebuild(path)
    check("reboot: amended core live at owner tier after replay",
          g2.has("MEM-GRANT") and v2.op_definitions()["MEM-GRANT"]["tier"] == "owner")
    check("reboot: master tier conserved after replay",
          v2.view_definitions()["rule-master"]["tier"] == "owner"
          and v2.master("rule-master") is not None)
    check("reboot: registry surfaces identical live vs replayed",
          set(v.op_definitions()) == set(v2.op_definitions())
          and set(v.view_definitions()) == set(v2.view_definitions()))

    run_report("conservation_probes")


if __name__ == "__main__":
    main()
