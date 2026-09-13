# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary; NON-GOAL: no offensive capability. Full declaration: SCOPE-STATEMENT.md.
"""EP-20 campaign-2 REVIEW probe — THE PROBE-EXTINCTION MATRIX (design/31 J10; the extinction lens).

Runs the campaign-1 adversarial ledger (brick / action-blind brick / constitutional mint /
forge-launder / data-passthrough insertion / bare-retire-core / non-root amend-core /
master-view supersession / audit-floor drop) PLUS lawful controls in FOUR authority columns,
in a DISPOSABLE test world where the founding openness grant has been narrowed to NOTHING:

  (a) NO ACCOUNT      — a bare caller, no account, no grant  -> must refuse (no chain)
  (b) ACCOUNT, NO GRANT — a founded account, no grant        -> must refuse (no chain)
  (c) ACCOUNT + GRANT ELSEWHERE — a grant in another space   -> must refuse (wrong scope)
  (d) ACCOUNT + COVERING GRANT — a covering grant            -> the LAWFUL act SUCCEEDS;
                                                               the ADVERSARIAL act still
                                                               refuses at the constitution
                                                               (a covering grant buys no brick).

This is simultaneously T-OPENNESS-CAN-RETIRE (design/31 EP-20 extinction-lens addendum):
columns a-c ARE the openness-retired world (a LEAK = anything passing ungranted); column d is
the grant-what-a-working-set-needs world (a WEDGE = a lawful granted act, VALUE AND ALL,
refusing). A grant covers the ACTION and never licenses a VALUE the constitution bars, so an
act refused on its value — a constitutional-tier claim — is an ADVERSARIAL row and not a
wedge: the wedge rule reads "every lawful act WHOSE VALUE IS ALSO PERMITTED passes under its
covering grant" (owner ruling 2026-08-13, carried to this file by the build manager). It closes
with T-TOTAL-ROUNDTRIP-2 (kill EVERYTHING derived + the vault, replay from the record file +
vault dir alone, identical INCLUDING the authority answers).
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import build, check, run_report  # noqa: E402
from kernel.errors import OpError  # noqa: E402

MOTHER = "space:root"

# the campaign-1 adversarial acts + lawful controls. kind: LAWFUL (d succeeds) or ADVERSARIAL
# (d refuses at the constitution/floor with the named cite). op/params are built per column so a
# committed lawful act carries a unique object.
DEF = {"description": "amended", "params": {"region": "required", "bytes": "required"},
       "law_cited": "MEM-LAW-BUDGET", "object_param": "region",
       "payload_from": ["region", "bytes"], "checks": [],
       "structural_params": ["region", "bytes"]}   # EP-41A vocabulary door (design/46 member 2): classify the fields


def _brick(col):
    return {"rule_id": f"law:brick-{col}", "polarity": "-",
            "when": [{"action": "CREATE-RULE"}], "then": [{"refuse": "law:brick"}]}


LEDGER = [
    # label,               op,             params(col)->dict,                                        kind,          d_cite
    ("lawful:create-info", "CREATE-INFO", lambda c: {"content": f"doc-{c}"},                         "LAWFUL",      None),
    ("lawful:dict-entry",  "DICT-ENTRY",  lambda c: {"term": f"t-{c}", "entity_kind": "action"},     "LAWFUL",      None),
    ("lawful:ordinary-rule","CREATE-RULE",lambda c: {"rule_id": f"law:ok-{c}", "value": 1},          "LAWFUL",      None),
    ("lawful:targeted-dont","CREATE-RULE",lambda c: {"rule_id": f"law:tg-{c}", "polarity": "-",
                                                      "when": [{"action": "CREATE-RULE"}, {"actor": "zzz"}],
                                                      "then": [{"refuse": f"law:tg-{c}"}]},          "LAWFUL",      None),
    ("lawful:silencing-writeactivity", "WRITE-ACTIVITY",
        lambda c: {"about": f"junk-{c}", "obligation_ref": "ob:none"},                                "LAWFUL",     None),
    ("adversarial:brick",  "CREATE-RULE", lambda c: _brick(c),                                        "ADVERSARIAL","BOOT-INT"),
    ("adversarial:action-blind-brick", "CREATE-RULE",
        lambda c: {"rule_id": f"law:all-{c}", "polarity": "-", "when": [{}],
                   "then": [{"refuse": "law:all"}]},                                                  "ADVERSARIAL","BOOT-INT"),
    # THE CONSTITUTIONAL MINT — the campaign-1 ledger act this module's docstring has always named,
    # and it is ADVERSARIAL: the covering grant reaches the ACTION, the refusal lands on the VALUE
    # (constitutional law is genesis-only), so a grant buys no constitutional law exactly as it buys
    # no brick. UNTIL CREATE-RULE DECLARED THE FIELDS IT WRITES (EP-28ZD), `tier` was absent from its
    # payload_from, the claim never reached the payload the constitution guard reads, and the rule
    # minted ORDINARY with the claim silently discarded — so this row was carried as LAWFUL under the
    # label `lawful:const-mint-claim-dropped`, a label that described a defect while wearing the shape
    # of a permission. A constitutional law was never obtainable through this door either way; the door
    # now says no instead of appearing to say yes. Re-classified on the owner's ruling of 2026-08-13
    # (wording the build manager's, not the owner's prose). (FORGE, which always carried tier, is the
    # laundering case below.)
    ("adversarial:const-mint", "CREATE-RULE",
        lambda c: {"rule_id": f"law:evil-{c}", "tier": "constitutional"},                            "ADVERSARIAL","BOOT-INT"),
    ("adversarial:forge-launder", "FORGE",
        lambda c: {"rule_id": "CONST-SELF-PROTECT", "tier": "ordinary"},                              "ADVERSARIAL","BOOT-INT"),
    ("adversarial:insertion-passthrough", "WRITE-ACTIVITY",
        lambda c: {"data": _brick(c)},                                                                "ADVERSARIAL","BOOT-INT"),
    ("adversarial:bare-retire-core", "RETIRE-OP", lambda c: {"name": "MEM-GRANT"},                    "ADVERSARIAL","BOOT-INT"),
    ("adversarial:amend-core-nonroot", "AMEND-OP",
        lambda c: {"name": "MEM-GRANT", "definition": DEF},                                           "ADVERSARIAL","BOOT-INT"),
    ("adversarial:master-supersede", "CREATE-VIEW",
        lambda c: {"name": "rule-master", "when": {"actor": "x"}, "then": {"move_to": "ch:j"}},       "ADVERSARIAL","BOOT-INT"),
    ("adversarial:audit-floor-drop", "AMEND-PACK",
        lambda c: {"name": "dual-audit-actions", "levels": ["MOUNT"]},                                "ADVERSARIAL","CONST-RECORDING-TOTAL"),
]


def _run(gate, actor, op, params):
    """Run one act; return (refused, cite, ok). refused=True with the cite when it raised OpError."""
    try:
        gate.execute(op, actor, params)
        return (False, None, True)
    except OpError as e:
        return (True, e.rule, False)


def matrix():
    s, g, v, p, path = build()

    # ---- prove the chain-end can still govern with openness gone, and NARROW OPENNESS TO ZERO ----
    ce = v.chain_end()
    check("chain-end resolves to the founding root (owner)", ce == "owner", detail=ce)
    # owner founds a FORGE op (so forge-launder is a single-step act in every column) + the test
    # world's spaces/accounts/grants — all lawful root acts, done while open.
    g.execute("CREATE-OP", "owner", {"name": "FORGE", "definition": {
        "law_cited": "P4-REFUSE", "params": {"rule_id": "required"},
        "object_param": "rule_id", "payload_from": ["rule_id", "tier"], "checks": [],
        "structural_params": ["rule_id"]}})   # EP-41A vocabulary door (design/46 member 2): classify the field
    g.execute("CREATE-SPACE", "owner", {"name": "other", "parent": MOTHER})     # a sibling space for column c
    for a in ("acct_b", "acct_c", "acct_d"):
        g.execute("CREATE-ACCOUNT", "owner", {"account_id": a, "actor_class": "human"})
    g.execute("GRANT", "owner", {"grant_id": "g_c", "grantee": "acct_c",
                                 "actions": "*", "info": "*", "space": "space:other"})   # (c) wrong space
    g.execute("GRANT", "owner", {"grant_id": "g_d", "grantee": "acct_d",
                                 "actions": "*", "info": "*", "space": MOTHER})          # (d) covering

    # THE NARROWING: revoke the founding openness grant. openness -> nothing.
    g.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
    check("openness grant is gone after REVOKE", "grant:founding-openness" not in v.grants())
    # a fresh bare caller, no account, no grant -> the zero-scaffolding world for column (a)
    check("power_view of an ungranted caller is empty (computed complement)",
          v.power_view("nobody_a")["grants"] == [])

    COLS = [("a", "nobody_a"), ("b", "acct_b"), ("c", "acct_c"), ("d", "acct_d")]
    print("\n  PROBE-EXTINCTION MATRIX (openness narrowed to zero)")
    print("  a=no-account  b=account/no-grant  c=account/grant-elsewhere  d=account/covering-grant")
    print("  " + "-" * 96)
    print(f"  {'probe act':38} | {'a':>12} | {'b':>12} | {'c':>12} | {'d':>14}")
    print("  " + "-" * 96)

    leaks, wedges, regressions = [], [], []
    for label, op, mk, kind, d_cite in LEDGER:
        cells = {}
        for col, actor in COLS:
            refused, cite, ok = _run(g, actor, op, mk(col))
            cells[col] = (refused, cite, ok)
            if col in ("a", "b", "c") and not refused:
                leaks.append(f"{label}[{col}] PASSED ungranted (leak)")
            if col == "d":
                if kind == "LAWFUL" and refused:
                    wedges.append(f"{label}[d] refused a lawful granted act ({cite}) (wedge)")
                if kind == "ADVERSARIAL" and not refused:
                    regressions.append(f"{label}[d] adversarial act PASSED under a covering grant (regression)")
                if kind == "ADVERSARIAL" and refused and cite != d_cite:
                    regressions.append(f"{label}[d] refused with {cite}, expected {d_cite}")

        def fmt(col):
            refused, cite, ok = cells[col]
            return (cite or "REFUSE") if refused else "PASS"
        print(f"  {label:38} | {fmt('a'):>12} | {fmt('b'):>12} | {fmt('c'):>12} | {fmt('d'):>14}")
        # the (a)==(b) collapse: no-account and account/no-grant both die at ROOT-NEG-1 (identity is
        # the SUBJECT of grants, not a separate act-gate — the positive-grant model computes the
        # complement). Recorded as an OBSERVATION, verified here, not a defect.
        check(f"{label}: (a) and (b) both refuse ROOT-NEG-1 (account-existence is not an act-gate)",
              cells["a"][1] == "ROOT-NEG-1" and cells["b"][1] == "ROOT-NEG-1",
              detail=f"a={cells['a'][1]} b={cells['b'][1]}")
        check(f"{label}: (c) refuses ROOT-NEG-3 (a chain reaches, wrong scope)",
              cells["c"][1] == "ROOT-NEG-3", detail=str(cells["c"]))
    print("  " + "-" * 96)

    # THE TIER CLAIM IS REFUSED, NOT DROPPED, AND THE REFUSAL IS ON THE RECORD. Two halves, each able
    # to fail on its own: nothing minted at that id AT ANY TIER (a silent ORDINARY mint would fail the
    # first half, which is the pre-EP-28ZD behaviour this row used to assert), and the record carries
    # EXACTLY ONE constitutional-tier refusal citing BOOT-INT, targeting column d's actor — columns a-c
    # never reach the constitution guard, dying earlier at authority, so a second match would mean an
    # ungranted caller got that far. (The predecessor read the minted rule's tier back; with nothing
    # minted it read None and failed. Owner ruling 2026-08-13.)
    check("constitutional-mint attempt minted NOTHING: no rule 'law:evil-d' at any tier",
          "law:evil-d" not in v.active_rules(), detail=str(v.active_rules().get("law:evil-d")))
    const_refusals = [e for e in s.by_action("op-refused")
                      if e.get("rule_cited") == "BOOT-INT"
                      and (e.get("payload") or {}).get("op") == "CREATE-RULE"
                      and "genesis-only" in ((e.get("payload") or {}).get("message") or "")]
    check("constitutional-mint attempt is RECORDED as a refusal citing BOOT-INT — exactly one, column d's",
          len(const_refusals) == 1 and const_refusals[0].get("target") == "acct_d",
          detail=f"n={len(const_refusals)} targets={[e.get('target') for e in const_refusals]}")

    check("NO LEAK: nothing ungranted passed in columns a-c", not leaks, detail=str(leaks))
    check("NO WEDGE: every lawful act whose VALUE is also permitted passed under its covering grant (d)",
          not wedges, detail=str(wedges))
    check("NO REGRESSION: every adversarial act still refused at the constitution under a grant (d)",
          not regressions, detail=str(regressions))

    # ---- prove the columns CAN fail: a grant one dimension too narrow MUST refuse (design/31 EP-20) ----
    g.execute("GRANT", "owner", {"grant_id": "g_narrow", "grantee": "acct_narrow",
                                 "actions": ["CREATE-INFO"], "info": "*", "space": MOTHER})
    g.execute("CREATE-ACCOUNT", "owner", {"account_id": "acct_narrow", "actor_class": "human"})
    refused_wrong_action, cite_wa, _ = _run(g, "acct_narrow", "CREATE-RULE", {"rule_id": "law:na", "value": 1})
    check("column-d mutation (grant one action too narrow) MUST refuse — proves the column can fail",
          refused_wrong_action and cite_wa == "ROOT-NEG-3", detail=f"{refused_wrong_action}/{cite_wa}")
    ok_right_action, _, _2 = _run(g, "acct_narrow", "CREATE-INFO", {"content": "narrow-ok"})
    check("...and the exactly-covered act still passes (the grant is load-bearing, not accidental)",
          ok_right_action[0] is False if isinstance(ok_right_action, tuple) else ok_right_action is False)

    # ---- T-OPENNESS-CAN-RETIRE, both directions, explicit verdict ----
    check("T-OPENNESS-CAN-RETIRE dir-1 (no wedge): explicitly-granted work still runs with openness=0",
          not wedges)
    check("T-OPENNESS-CAN-RETIRE dir-2 (no leak): everything ungranted refuses with citation",
          not leaks)


def _norm(d):
    if d == "*":
        return "*"
    if isinstance(d, (set, frozenset)):
        return sorted(d)
    return d


def _fingerprint(gate, views):
    """A canonical fingerprint of EVERY derived surface — registry, views, queues, power views,
    accounts, AND the authority answers (covers / power_view / sealed-secret hash / chain-end /
    successor). This is what T-TOTAL-ROUNDTRIP-2 demands be identical live vs replayed."""
    import json
    from kernel.store import frozen_default

    def canon(x):
        return json.dumps(x, sort_keys=True, default=frozen_default)

    accts = sorted(views.accounts().keys())
    covers_q = [("acct_x", "CREATE-RULE", "law", MOTHER), ("acct_x", "CREATE-INFO", None, "space:s1"),
                ("nobody", "CREATE-RULE", "law", MOTHER), ("acct_y", "SEAL-SECRET", None, MOTHER)]
    pv = {a: {"actions": _norm(views.power_view(a)["actions"]), "info": _norm(views.power_view(a)["info"]),
              "spaces": sorted(views.power_view(a)["spaces"]), "n": len(views.power_view(a)["grants"])}
          for a in accts + ["acct_x", "acct_y", "nobody"]}
    return {
        "registry": sorted(gate.ops.keys()),
        "op_defs": canon(views.op_definitions()),
        "view_defs": canon(views.view_definitions()),
        "active_rules": canon(views.active_rules()),
        "accounts": canon(views.accounts()),
        "spaces": canon(views.spaces()),
        "grants": canon(views.grants()),
        "roles": canon(views.roles()),
        "chain_end": views.chain_end(),
        "current_successor": views.current_successor(),
        "queues": canon({k: [e["seq"] for e in val] for k, val in views.queues().items()}),
        "metabolism": canon(views.metabolism()),
        "dictionary": canon({str(k): dict(val) for k, val in views.dictionary().items()}),
        "power_views": canon(pv),
        "covers": canon([[a, act, ik, sp, views.covers(a, act, ik, sp)] for (a, act, ik, sp) in covers_q]),
        "sealed": canon({n: views.sealed_secret_hash(n) for n in ("db-pw", "api-key", "absent")}),
    }


def roundtrip2():
    """T-TOTAL-ROUNDTRIP-2 (design/31 §6): kill EVERYTHING derived — registry, views, queues, power
    views, accounts surface, the vault handle — and replay from the record file (+ the vault dir)
    alone; the whole state, INCLUDING the authority answers, reconstructs identically."""
    import tempfile
    from kernel.compose import build_full_kernel

    d = tempfile.mkdtemp()
    rec = os.path.join(d, "r.jsonl")
    blob = os.path.join(d, "blobs")
    vault = os.path.join(d, "vault")
    store, gate, views, blobs, subs = build_full_kernel(rec, blob, vault)

    # a broad authority + secret + succession + dictionary + narrowing workload
    gate.execute("CREATE-SPACE", "owner", {"name": "s1", "parent": MOTHER})
    for a, cls in (("acct_x", "human"), ("acct_y", "human"), ("succ", "human")):
        gate.execute("CREATE-ACCOUNT", "owner", {"account_id": a, "actor_class": cls})
    gate.execute("VERIFY-ACCOUNT", "owner", {"account": "succ", "evidence_hash": "sha256:deadbeef"})
    gate.execute("GRANT", "owner", {"grant_id": "gx", "grantee": "acct_x",
                                    "actions": ["CREATE-RULE", "CREATE-INFO"], "info": "*", "space": MOTHER})
    gate.execute("GRANT", "owner", {"grant_id": "gy", "grantee": "acct_y",
                                    "actions": "*", "info": "*", "space": "space:s1"})
    gate.execute("SEAL-SECRET", "owner", {"name": "db-pw", "value": "hunter2"})
    gate.execute("SEAL-SECRET", "owner", {"name": "api-key", "value": "k-abc"})
    gate.execute("VERIFY-SECRET", "owner", {"name": "db-pw", "candidate": "hunter2"})
    gate.execute("VERIFY-SECRET", "owner", {"name": "db-pw", "candidate": "wrong"})
    gate.execute("DICT-ENTRY", "owner", {"term": "grant", "entity_kind": "action", "tags": {"v": 1}})
    gate.execute("DESIGNATE-SUCCESSOR", "owner", {"successor": "succ"})
    gate.execute("ACCEPT-SUCCESSION", "succ", {})
    gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})   # narrow openness in the roundtrip world

    live = _fingerprint(gate, views)
    check("roundtrip-2 workload: successor fold is live (verified+human accepted)",
          views.current_successor() == "succ")
    check("roundtrip-2 workload: a sealed secret verifies MATCH from the record",
          any((e.get("payload") or {}).get("result") == "MATCH" for e in store.by_action("VERIFY-SECRET")))

    # KILL EVERYTHING DERIVED — a brand-new kernel over the SAME record file + SAME vault dir.
    store2, gate2, views2, blobs2, subs2 = build_full_kernel(rec, blob, vault)
    replayed = _fingerprint(gate2, views2)

    for key in live:
        check(f"roundtrip-2: '{key}' identical live vs replayed", live[key] == replayed[key],
              detail=f"live={str(live[key])[:80]} rep={str(replayed[key])[:80]}")


if __name__ == "__main__":
    matrix()
    roundtrip2()
    run_report("extinction_matrix_probes")
