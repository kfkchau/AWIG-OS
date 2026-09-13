# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary; NON-GOAL: no offensive capability. Full declaration: SCOPE-STATEMENT.md.
"""EP-20 campaign-2 REVIEW probe — the five flips LIVE, the protection-fallback reachability
answer, and the named narrowing-time subtleties. Companion to extinction_matrix_probes.py.

Verifies by RUNNING (validate-by-reading confirmed the code paths; these re-check behaviour):
  * CONST-AUTHORITY-ANCHORED live — the anchor guard refuses a non-root designation, an
    unverified successor, a non-human successor, and a handover with no valid successor.
  * CONST-SECRETS live — verify-never-reveal: no read op EXISTS (Closure Hit), the chain-end
    cannot read a secret, and the plaintext is absent from the record file.
  * ROOT-NEG-1/-3 + PACK-SCOPE are exercised in extinction_matrix_probes.py (this file adds the
    anchor + secrets halves).
  * PROTECTION FALLBACK (EP-19 raise #3 / EP-20 carry-item 1 -> R20-1, CLOSED by EP-20B). This
    probe is a DOCUMENTED FLIP: it used to assert that protection.DUAL_AUDIT_ACTIONS existed,
    was UNREACHABLE (every composed world seeds the pack) and was STALE (it lacked the
    campaign-2 members VERIFY-ACCOUNT / VERIFY-SECRET). Both findings stand on the record and
    are what licensed the retirement; the constant is now GONE, so the probe asserts its
    ABSENCE — under its own name and under any other.
  * NARROWING-TIME SUBTLETY: a bare CREATE-INFO derives info-kind None, so under a grant narrowed
    by info-kind it is coverable only by info='*' (surfaces exactly as EP-17 raise #4 records).
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import build, check, refuses, run_report  # noqa: E402

MOTHER = "space:root"


def anchor_flip():
    s, g, v, p, path = build()
    # a non-root actor may not designate a successor (the anchor guard, not grant-gated)
    check("CONST-AUTHORITY-ANCHORED: a non-root DESIGNATE-SUCCESSOR refuses",
          refuses(lambda: g.execute("DESIGNATE-SUCCESSOR", "mallory", {"successor": "x"}),
                  "CONST-AUTHORITY-ANCHORED"))
    # an unverified successor refuses (verification bottoms out at the founding)
    g.execute("CREATE-ACCOUNT", "owner", {"account_id": "unv", "actor_class": "human"})
    check("CONST-AUTHORITY-ANCHORED: designating an UNVERIFIED successor refuses",
          refuses(lambda: g.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": "unv"}),
                  "CONST-AUTHORITY-ANCHORED"))
    # a verified but NON-HUMAN successor refuses (root never passes to a pure-agentic actor)
    g.execute("CREATE-ACCOUNT", "owner", {"account_id": "bot", "actor_class": "agent"})
    g.execute("VERIFY-ACCOUNT", "owner", {"account": "bot", "evidence_hash": "sha256:aa"})
    check("CONST-AUTHORITY-ANCHORED: a verified NON-HUMAN successor refuses",
          refuses(lambda: g.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": "bot"}),
                  "CONST-AUTHORITY-ANCHORED"))
    # a HANDOVER with no valid successor refuses (authority never orphans)
    check("CONST-AUTHORITY-ANCHORED: HANDOVER without a valid successor refuses (never orphans)",
          refuses(lambda: g.execute("HANDOVER", "owner", {}), "CONST-AUTHORITY-ANCHORED"))
    # the lawful path succeeds: verify+human, accept, then the successor fold is live
    g.execute("CREATE-ACCOUNT", "owner", {"account_id": "heir", "actor_class": "human"})
    g.execute("VERIFY-ACCOUNT", "owner", {"account": "heir", "evidence_hash": "sha256:bb"})
    g.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": "heir"})
    g.execute("ACCEPT-SUCCESSION", "heir", {})
    check("CONST-AUTHORITY-ANCHORED: a verified+human accepted successor makes the fold live",
          v.current_successor() == "heir")


def secrets_flip():
    from kernel.compose import build_full_kernel
    d = tempfile.mkdtemp()
    rec = os.path.join(d, "r.jsonl")
    store, gate, views, blobs, subs = build_full_kernel(rec, os.path.join(d, "b"), os.path.join(d, "v"))
    gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": "hunter2-PLAINTEXT"})
    m = gate.execute("VERIFY-SECRET", "owner", {"name": "db-pw", "candidate": "hunter2-PLAINTEXT"})
    check("CONST-SECRETS: a correct candidate verifies MATCH", m["payload"]["result"] == "MATCH")
    n = gate.execute("VERIFY-SECRET", "owner", {"name": "db-pw", "candidate": "wrong"})
    check("CONST-SECRETS: a wrong candidate verifies NO-MATCH", n["payload"]["result"] == "NO-MATCH")
    # the closure: NO read op exists — reading a secret back is a Closure Hit, not a refusal
    for op in ("REVEAL-SECRET", "READ-SECRET", "GET-SECRET", "OPEN-SECRET", "UNSEAL-SECRET"):
        check(f"CONST-SECRETS: {op} does not exist (closure, P3 — the read op is ABSENT)",
              refuses(lambda op=op: gate.execute(op, "owner", {"name": "db-pw"}), "P3-CLOSURE"))
    # the plaintext lives nowhere in the record (only the hash + MATCH/NO-MATCH)
    text = open(rec).read()
    check("CONST-SECRETS: the plaintext is ABSENT from the record file (only the hash is recorded)",
          "hunter2-PLAINTEXT" not in text)


def protection_fallback_answer():
    """EP-20 carry-item 1, CLOSED by EP-20B: the fallback is retired, so the question is no longer
    'is the constant reachable' but 'is the pack the only source, and did the corpse stay buried'."""
    from kernel.compose import build_full_kernel
    from kernel import protection as prot_mod
    d = tempfile.mkdtemp()
    rec = os.path.join(d, "r.jsonl")
    store, gate, views, blobs, subs = build_full_kernel(rec, os.path.join(d, "b"), os.path.join(d, "v"))
    prot = views.protection
    pack = views.category_packs().get("dual-audit-actions")
    check("protection-fallback: the dual-audit-actions pack IS present in every composed world",
          pack is not None)
    live_floor = prot._audit_actions()
    # the live floor is the PACK, and it carries the campaign-2 members the stale constant lacked
    # (VERIFY-ACCOUNT via V5; VERIFY-SECRET via EP-19).
    check("protection-fallback: the live floor is the PACK, and it carries VERIFY-ACCOUNT",
          "VERIFY-ACCOUNT" in live_floor)
    check("protection-fallback: the code-resident constant is GONE (EP-20B retirement)",
          not hasattr(prot_mod, "DUAL_AUDIT_ACTIONS"))
    check("protection-fallback: no RENAMED module-level copy of the floor survives either",
          not [n for n, o in vars(prot_mod).items()
               if isinstance(o, (set, frozenset, list, tuple)) and any(a in o for a in live_floor)])
    # VERDICT (closed): the pack is the only source of the dual-audit action list. The failure mode
    # that replaces the fallback is a REFUSAL — a composition whose record lacks the pack refuses at
    # boot citing CONST-RECORDING-TOTAL rather than mirroring against code (tests/test_ep20b.py).


def narrowing_subtlety():
    """A bare CREATE-INFO derives info-kind None (EP-17 raise #4): under a grant narrowed by
    info-kind it is coverable ONLY by info='*'. Surfaced in the zero-scaffolding world."""
    s, g, v, p, path = build()
    g.execute("CREATE-ACCOUNT", "owner", {"account_id": "u", "actor_class": "human"})
    g.execute("GRANT", "owner", {"grant_id": "gu", "grantee": "u",
                                 "actions": "*", "info": ["law"], "space": MOTHER})   # info narrowed to 'law'
    g.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
    check("narrowing subtlety: an info='law' grant does NOT cover a bare CREATE-INFO (info None)",
          refuses(lambda: g.execute("CREATE-INFO", "u", {"content": "x"}), "ROOT-NEG-3"))
    # a covering CREATE-RULE (info-kind 'law') DOES pass under the same grant
    check("...but the same grant covers a CREATE-RULE (info-kind 'law') — the subtlety is info-kind, not a leak",
          g.execute("CREATE-RULE", "u", {"rule_id": "law:z", "value": 1})["action"] == "CREATE-RULE")


if __name__ == "__main__":
    anchor_flip()
    secrets_flip()
    protection_fallback_answer()
    narrowing_subtlety()
    run_report("campaign2_flips_probes")
