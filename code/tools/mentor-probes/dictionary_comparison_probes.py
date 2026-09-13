# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary; NON-GOAL: no offensive capability. Full declaration: SCOPE-STATEMENT.md.
"""EP-13 extension probes — the newest surfaces (EP-10 gauges / EP-11 verdicts / EP-12 dictionary),
attacked through the three archetypes (hostile nobody / careless owner / reboot). Committed so the
adversarial ledger covers the moat's last-built halves, not just the constitution/conservation core.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import build, rebuild, check, refuses, run_report  # noqa: E402


def probes():
    # ---- the HOSTILE NOBODY ----
    store, gate, views, _prot, path = build()

    # comparison: a nobody can add a same-frame verdict that CONTRADICTS the owner's — and the
    # contradiction view (a pure derivation) catches it, while a DIFFERENT frame never conflicts.
    gate.execute("COMPARE", "owner", {"a": "x", "b": "y", "frame": "cost", "verdict": "gt"})
    gate.execute("COMPARE", "mallory", {"a": "x", "b": "y", "frame": "cost", "verdict": "lt"})
    gate.execute("COMPARE", "mallory", {"a": "x", "b": "y", "frame": "speed", "verdict": "lt"})
    c = views.contradictions()
    check("verdict: same-frame incompatibility is flagged, cross-frame is NOT",
          len(c) == 1 and c[0]["frame"] == "cost", detail=str(c))
    check("verdict: both cross-frame verdicts kept, never merged",
          len([e for e in store.by_action("COMPARE")]) == 3)

    # dictionary: a nobody disputes the current entry — latest-UNDISPUTED wins (fold, not a status),
    # and the conflict routes to the owner queue as an append-nothing view.
    e2 = None
    gate.execute("DICT-ENTRY", "owner", {"term": "grant", "entity_kind": "action", "tags": {"v": 1}})
    e2 = gate.execute("DICT-ENTRY", "bob", {"term": "grant", "entity_kind": "action", "tags": {"v": 2}})
    gate.execute("DISPUTE", "mallory", {"ref_seq": e2["seq"]})
    cur = views.dictionary("action").get(("action", "grant"))
    check("dict: latest-undisputed-wins (disputed v2 -> falls back to v1)",
          cur is not None and cur["tags"]["v"] == 1, detail=str(cur))
    check("dict: the disputed term routes to the owner queue",
          {"entity_kind": "action", "term_key": "grant"} in views.disputed_terms())

    # definition_ref integrity-at-use: a dangling ref refuses AT USE; a live CODE op resolves (R29).
    gate.execute("DICT-ENTRY", "owner", {"term": "frob", "entity_kind": "action", "definition_ref": "op:NO-SUCH"})
    check("dict: dangling definition_ref refuses AT USE (not creation)",
          refuses(lambda: gate.execute("USE-TERM", "mallory", {"entity_kind": "action", "term": "frob"}), "CAP-IS-LAW"))
    gate.execute("DICT-ENTRY", "owner", {"term": "mkinfo", "entity_kind": "action", "definition_ref": "op:CREATE-INFO"})
    check("dict: definition_ref to a live CODE op resolves at use (R29 fixed)",
          not refuses(lambda: gate.execute("USE-TERM", "mallory", {"entity_kind": "action", "term": "mkinfo"})))

    # ---- the CARELESS OWNER (legitimate wide power through the documented path) ----
    store, gate, views, _prot, path = build()
    gate.execute("DICT-ENTRY", "owner", {"term": "grant", "entity_kind": "action", "tags": {"v": 1}})
    gate.execute("DICT-ENTRY", "owner", {"term": "grant", "entity_kind": "action", "tags": {"v": 9}})  # amend in place
    check("dict: re-asserting a term supersedes latest-wins (no delete, append-only)",
          views.dictionary("action")[("action", "grant")]["tags"]["v"] == 9)
    before = len(store.all())
    views.metabolism(); views.paper_tigers(); views.contradictions(); views.disputed_terms(); views.dictionary()
    check("gauges/dictionary are pure derivations — reading them appended NOTHING",
          len(store.all()) == before)

    # ---- the REBOOT (kill everything derived, replay, demand identity) ----
    store, gate, views, _prot, path = build()
    gate.execute("CREATE-VIEW", "owner", {"name": "idle", "when": {"action": "COMPARE"},
                                          "then": {"move_to": "in"}, "refresh": "hourly"})   # a mandated view (paper tiger)
    gate.execute("COMPARE", "owner", {"a": "p", "b": "q", "frame": "cost", "verdict": "gt"})
    gate.execute("COMPARE", "bob", {"a": "p", "b": "q", "frame": "cost", "verdict": "lt"})
    de = gate.execute("DICT-ENTRY", "alice", {"term": "grant", "entity_kind": "action"})
    gate.execute("DISPUTE", "carol", {"ref_seq": de["seq"]})

    def snap(vw):
        return (sorted(str(k) for k in vw.dictionary()),
                sorted(x["frame"] for x in vw.contradictions()),
                sorted(str(x) for x in vw.disputed_terms()),
                vw.metabolism()["per_kind"],
                sorted(t["name"] for t in vw.paper_tigers()))

    live = snap(views)
    store2, gate2, views2, _p2 = rebuild(path)     # KILL DERIVED: replay from the record alone
    check("reboot: dictionary/contradictions/disputes/metabolism/paper-tigers identical after replay",
          snap(views2) == live, detail=f"live={live} rep={snap(views2)}")


if __name__ == "__main__":
    probes()
    run_report("dictionary_comparison_probes")
