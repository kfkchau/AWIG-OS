"""Separation probes (EP-09/10 families). The blind streams cannot collude; the brake
freezes without darkness; the unbrakables REFUSE (never accept-and-ignore — the R28
lesson); the maker never reviews its own object; delivery appends nothing."""
from _harness import build, check, refuses, run_report


def main():
    s, g, v, prot, path = build()

    # --- blind streams: mutual blindness both directions, independent agreement ---
    g.execute("GRANT-READ", "SYSTEM", {"grantee": "bob", "target": "doc1"})
    a = list(s.by_action("dual-audit-record"))
    b = list(s.by_action("dual-audit-b-record"))
    check("both streams mirrored the referent", len(a) == 1 and len(b) == 1)
    check("B never digested an A-record (blind)",
          not ({m["payload"]["ref_seq"] for m in b} & {m["seq"] for m in a}))
    check("A never digested a B-record (blind)",
          not ({m["payload"]["ref_seq"] for m in a} & {m["seq"] for m in b}))
    check("blind digests AGREE independently",
          a[0]["payload"]["digest"] == b[0]["payload"]["digest"])
    check("third-party cross-check clean on a clean store",
          prot.dual_blind_divergences() == [])

    # --- the brake: freezes, records, restores; unbrakables REFUSE ---
    g.execute("HALT-WATCHER", "bob", {"watcher": "wanda"})
    before = len(list(s.all()))
    check("halted watcher's act refuses AND records (never dark)",
          refuses(lambda: g.execute("GRANT-READ", "wanda", {"grantee": "x", "target": "y"}))
          and len(list(s.all())) > before)
    check("braking SYSTEM refuses (not accept-and-ignore — R28)",
          refuses(lambda: g.execute("HALT-WATCHER", "bob", {"watcher": "SYSTEM"}), "BOOT-INT"))
    check("braking the owner refuses",
          refuses(lambda: g.execute("HALT-WATCHER", "bob", {"watcher": "owner"}), "BOOT-INT"))
    check("non-owner resolve refuses",
          refuses(lambda: g.execute("RESOLVE-WATCHER", "carol", {"watcher": "wanda"}), "BOOT-INT"))
    restored = False
    try:
        g.execute("RESOLVE-WATCHER", "owner", {"watcher": "wanda"})
        restored = g.execute("GRANT-READ", "wanda",
                             {"grantee": "x", "target": "y"})["action"] == "GRANT-READ"
    except Exception:
        restored = False
    check("owner resolve restores the watcher", restored)

    # --- SOP: the maker never reviews its own object ---
    g.execute("CREATE-INFO", "mia", {"content": "her-doc"})
    check("maker refused reviewing own object",
          refuses(lambda: g.execute("REVIEW", "mia", {"object": "her-doc"}), "SOP"))
    other_ok = False
    try:
        other_ok = g.execute("REVIEW", "rex", {"object": "her-doc"})["action"] == "REVIEW"
    except Exception:
        other_ok = False
    check("a different actor reviews fine", other_ok)

    # --- gauges + delivery: derivations append nothing ---
    n = len(list(s.all()))
    v.metabolism(); v.paper_tigers(); v.queues()
    check("gauges and queues appended nothing", len(list(s.all())) == n)

    run_report("separation_probes")


if __name__ == "__main__":
    main()
