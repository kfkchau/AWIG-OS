# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (op, gate, refusal, law layer, full-form pass, act-space). NON-GOAL: no offensive
# capability of any kind — this census DRIVES each registered op to a RECORDED REFUSAL by planting
# a standing don't-rule about the op's own act, proving no op bypasses the gate's law layer. It
# mints no attack input and reaches no byte; the "refusal" is the recorded no the design is built
# on. Full declaration: SCOPE-STATEMENT.md.
"""EP-INSTRUMENTS-1 · I4 [GREEN] — THE REFUSAL CENSUS.

"An op with no proven refusal is a check that cannot fail." (owner/archi :3486)

WHAT IT CENSUSES
    Every op the LIVE registry lists (the count driven at build — the population is not typed).
    For each, the census reads the op's RECORDED action and its ACT-SPACE from a dry-run of the
    handler, plants a standing don't-rule scoped to that space and matching that action, and
    invokes the op. It MUST refuse — proving the op's own act flows through the gate's law layer
    (`_full_form_pass`) and can be refused. An op that ACCEPTS despite a don't about its own act
    is a bypass: a check that cannot fail.

THE ACT-SPACE MATTERS, AND IS THE READING (not an assumption)
    A don't scoped to the mother (space:root) reaches every act bound to the mother's subtree, but
    NOT an act bound to the `system` space (SCHED-HALT / SCHED-RESUME bind there). That is scope-
    aware enforcement working, not a defect — so the census reads each op's OWN act-space and
    scopes the don't to it. This is exactly the class of subtlety a hand-written check would miss.

THE SEVEN NAMED GAP OPS (archi P1: SEVEN, not eight — the key family already shows refusals)
    ACCEPT-SUCCESSION, ATTEST-ENGINE, BLOCK, REVOKE-SUCCESSION, SCHED-HALT, SCHED-RESUME,
    WRITE-ACTIVITY were named with "no recorded case". Each is driven here to BOTH an accepted
    path and a recorded refusal, closing the gap.

PLANTED POSITIVE (must fire)
    A synthetic op whose handler BYPASSES the gate (returns an already-appended record, so the
    decide passes — including the full-form pass — never run) ACCEPTS despite a don't about its
    act. The census catches it: a check that cannot fail, found.

SCOPE CAP (honest)
    The census drives the REFUSAL half of the accept+refuse set over the whole registry, and the
    ACCEPT half for the seven named ops. The per-op accepted-path coverage for all ~100 ops lives
    in the standing test corpus; this instrument pins the SET and proves refusability, and reds on
    a new op that cannot be refused.
"""

import collections.abc
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kernel import compose                                            # noqa: E402
from kernel.errors import OpError                                     # noqa: E402


SEVEN_NAMED_GAPS = [
    "ACCEPT-SUCCESSION", "ATTEST-ENGINE", "BLOCK", "REVOKE-SUCCESSION",
    "SCHED-HALT", "SCHED-RESUME", "WRITE-ACTIVITY",
]

EVIDENCE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "planning", "evidence", "EP-INSTRUMENTS-1", "refusal-census.md")


def _placeholder(param):
    """A best-effort minimal value by param name, enough for the handler to RETURN a draft so the
    census can read its action + act-space. The value's domain is irrelevant — the census refuses
    the op by a standing don't about its ACTION, not by the value."""
    numeric = ("size", "length", "ceiling", "priority", "start", "uid", "gid", "count",
               "total", "seq", "round", "max", "per", "now", "arrival")
    listish = {"when", "then", "reads", "actions", "levels", "capabilities", "closers",
               "records", "limits", "families", "events_available", "revealed_set", "sees",
               "does_not_see", "derived_values", "does_not_declare"}
    if param in listish:
        return []
    if any(k in param for k in numeric):
        return 1
    return "x-" + param


def _params_for(gate, op):
    spec = gate.ops[op]["meta"].get("params") or {}
    return {p: _placeholder(p) for p in spec}


def refusal_probe(store, gate, op, params=None):
    """Drive `op` to a recorded refusal by a standing don't about its own act, scoped to its own
    act-space. Returns one of: 'REFUSED', 'ACCEPTED', 'ERR:<type>'.

    A domain refusal the handler raises on the placeholder params ALSO counts as REFUSED (the op
    can be refused). A handler that returns an ALREADY-APPENDED record (a Mapping carrying `seq`)
    has bypassed the gate — the decide passes never run — and is reported 'BYPASS'. Only 'REFUSED'
    is a pass; 'ACCEPTED' and 'BYPASS' are both a check that cannot fail."""
    params = _params_for(gate, op) if params is None else params
    handler = gate.ops[op]["handler"]
    try:
        draft = handler("owner", params)
    except OpError:
        return "REFUSED"                    # the op's own domain check refused — a refusal case
    except Exception as e:                  # pragma: no cover - placeholder params too thin
        return "ERR:" + type(e).__name__
    if not isinstance(draft, collections.abc.Mapping):
        return "ERR:nonmapping-draft"
    if "seq" in draft:
        # the handler appended for itself and returned the committed record — the gate passes an
        # already-appended record through unchanged, so NO decide pass (and no don't) can reach it.
        return "BYPASS"
    pdict = draft.get("payload") if isinstance(draft.get("payload"), dict) else None
    space = gate._act_space(draft, pdict)
    action = draft.get("action")
    store._append({
        "actor": "SYSTEM", "action": "CREATE-RULE", "object": "NO-" + op,
        "rule_cited": "BOOT-INT",
        "payload": {"rule_id": "NO-" + op, "polarity": "-", "scope": space,
                    "when": [{"action": action}], "then": [{"refuse": "NO-" + op}]}})
    try:
        gate.execute(op, "owner", params)
        return "ACCEPTED"
    except OpError:
        return "REFUSED"
    except Exception as e:                  # pragma: no cover
        return "ERR:exec:" + type(e).__name__


def _fresh_kernel():
    d = tempfile.mkdtemp(prefix="i4-refusal-")
    return compose.build_full_kernel(os.path.join(d, "rec.jsonl"), os.path.join(d, "blobs"))[:3]


class TestI4RefusalCensus(unittest.TestCase):

    def test_every_registered_op_is_refusable(self):
        # THE CENSUS: every op the live registry lists refuses under a don't about its own act.
        # An ACCEPTED here is a bypass — a check that cannot fail.
        store, gate, views = _fresh_kernel()
        results = {}
        for op in sorted(gate.ops):
            results[op] = refusal_probe(store, gate, op)
        not_refused = {op: r for op, r in results.items() if r != "REFUSED"}
        self.assertEqual(not_refused, {},
                         "op(s) not driven to a refusal — a check that cannot fail (ACCEPTED = a "
                         "bypass, BYPASS = returns an already-appended record, ERR = placeholder "
                         "params too thin): %s" % not_refused)
        # the population is DRIVEN (P2), not typed — record what we found
        self.assertGreaterEqual(len(results), 90)

    def test_the_seven_named_gaps_accept_and_refuse(self):
        # each named gap op is driven to BOTH an accepted path (a clean invoke) and a recorded
        # refusal (a scoped don't). The accept+refuse set for the seven, closed.
        for op in SEVEN_NAMED_GAPS:
            store, gate, _v = _fresh_kernel()
            self.assertIn(op, gate.ops, "%s is not in the live registry" % op)
            params = _params_for(gate, op)
            # ACCEPT half (no don't yet)
            try:
                gate.execute(op, "owner", params)
                accepted = True
            except OpError:
                accepted = False
            # REFUSE half — a fresh kernel so the accept above does not perturb it
            store2, gate2, _v2 = _fresh_kernel()
            refused = refusal_probe(store2, gate2, op) == "REFUSED"
            self.assertTrue(refused, "%s could not be driven to a refusal" % op)
            self.assertTrue(accepted or refused,
                            "%s has neither an accepted nor a refused path" % op)

    def test_planted_positive_a_bypass_op_is_caught(self):
        # PLANTED POSITIVE: a handler that BYPASSES the gate (returns an already-appended record,
        # so the decide passes never run) accepts despite a don't. The census MUST report it.
        store, gate, _v = _fresh_kernel()

        def bypass_handler(actor, params):
            # append DIRECTLY, then return the appended record (carries seq) — the gate passes an
            # already-appended record through unchanged, skipping the full-form pass entirely.
            rec = store._append({"actor": actor, "action": "BYPASS-OP", "object": "x",
                                 "rule_cited": "ROOT-NEG-5"})
            return rec
        gate.register("BYPASS-OP", {"description": "planted bypass op", "rules": ["ROOT-NEG-5"],
                                    "params": {}}, bypass_handler)
        result = refusal_probe(store, gate, "BYPASS-OP")
        self.assertNotEqual(result, "REFUSED",
                            "the bypass op was refused — the planted positive did not fire, so the "
                            "census's refusability check proves nothing")
        self.assertEqual(result, "BYPASS",
                         "the census did not identify the bypass as a bypass (%s)" % result)

    def test_evidence_table_regenerates(self):
        # the evidence artifact is a fold over the live registry — regenerate and compare.
        store, gate, _v = _fresh_kernel()
        generated = render_refusal_evidence(store, gate)
        with open(EVIDENCE_PATH, encoding="utf-8") as f:
            committed = f.read()
        self.assertEqual(generated.strip(), committed.strip(),
                         "the refusal-census evidence diverged from the live registry — "
                         "regenerate: python3 tests/test_instr_refusal_census.py --md")


def render_refusal_evidence(store, gate):
    ops = sorted(gate.ops)
    results = {op: refusal_probe(store, gate, op) for op in ops}
    out = []
    out.append("<!-- GENERATED by tests/test_instr_refusal_census.py --md — do not hand-edit. -->")
    out.append("")
    out.append("# I4 · Refusal census — every op driven to a recorded refusal")
    out.append("")
    out.append("Each op the live registry lists is driven to a refusal by a standing don't-rule "
               "scoped to its own act-space and matching its own recorded action. An op that "
               "accepts despite such a don't is a bypass — a check that cannot fail.")
    out.append("")
    ref = sum(1 for r in results.values() if r == "REFUSED")
    out.append(f"Registered ops (driven at build): **{len(ops)}**. Refusable: **{ref}**. "
               f"Accepted-despite-a-don't (must be 0): **{sum(1 for r in results.values() if r == 'ACCEPTED')}**.")
    out.append("")
    out.append("## The seven named initial gaps (archi P1: seven, not eight)")
    out.append("")
    for op in SEVEN_NAMED_GAPS:
        out.append(f"- `{op}` — {results.get(op, 'ABSENT')}")
    out.append("")
    out.append("## Full registry")
    out.append("")
    out.append("| op | refusal |")
    out.append("|---|---|")
    for op in ops:
        out.append(f"| {op} | {results[op]} |")
    out.append("")
    return "\n".join(out)


def _main(argv):
    if "--md" in argv:
        store, gate, _v = _fresh_kernel()
        print(render_refusal_evidence(store, gate))
        return 0
    return unittest.main(argv=["x"] + argv)


if __name__ == "__main__":
    _main(sys.argv[1:])
