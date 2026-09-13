# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (op, door, param, declared value, refuse-or-declared-lawful). NON-GOAL: no offensive
# capability of any kind — this is a CONFORMANCE sweep: the boundary values come from the op's OWN
# declared param schema, and the assertion is "the door refuses OR the definition declares it
# lawful". It is not an attack; it drives no exploit and reaches no byte. Full declaration:
# SCOPE-STATEMENT.md.
"""EP-INSTRUMENTS-1 · I5 [GREEN] — THE BOUNDARY SWEEP AT THE DOOR.

GENERATED from the pack's OWN param declarations (P2: every op the LIVE registry lists, the count
read at build — not typed). For every declared param the sweep drives boundary values:

    numeric params   ->  negative, zero, huge
    bytes/string     ->  empty, non-UTF-8

and classifies the door's answer: REFUSED (an OpError — the door or the handler's own check said
no), ACCEPTED (recorded), or REJECTED (the canonical encoder refused a malformed value by raising,
so it was never silently recorded). The conformance assertion is refuse-or-declared-lawful: a
NEGATIVE value for a NON-NEGATIVE quantity (size, ceiling, length, ...) MUST be refused; zero/huge
and an empty string are boundary-but-lawful; a non-UTF-8 value must not be silently recorded.

PLANTED SANITY (B5): MEM-GRANT's negative `size` is one row of the sweep and MUST refuse (remove
the B5 sign check and this reds).

THE FINDING THIS SWEEP PRODUCED ON ITS FIRST RUN IS NOW CLOSED (EP-MAINT-OUTSIDE-2 C-1):
    Five ops silently ACCEPTED a negative for a non-negative quantity (AMEND-BUDGET.ceiling,
    MEM-GRANT.size on the ungoverned path, FILE-LOCK/UNLOCK/TRUNCATE.length). C-1's QUANTITIES
    declaration on the op META + the door's call-time quantity guard now refuse a negative or
    non-integer declared quantity at the door (AR-2, with a row), so all five read REFUSED. The
    malformed-accept baseline is now EMPTY; a NEW silently-accepted-malformed row (a regression, or
    an unvalidated new op) reds this instrument.

A SECOND CLASS, PINNED AND TRACKED, NOT FIXED HERE (EP-MAINT-OUTSIDE-2 C-4; archi :3507): eight rows
read REJECTED:BatchFailed — a malformed text param (non-UTF-8, or empty required) raises inside the
canonical/batch encoder rather than refusing cleanly at the door. The door-refusal for the crash
class is OUT of this unit's scope (the architect ruled the eight rows a disclosed finding the sweep
TRACKS, not a fix). They are PINNED as `KNOWN_REJECTED`: a NEW REJECTED row, or a pinned one that stops
crashing, reds this instrument and names what moved.

PLANTED POSITIVES (must fire): a synthetic op with an unvalidated numeric `size` param accepts a
negative value (the malformed-accept detector); a synthetic op whose handler raises a non-OpError on a
boundary value reads REJECTED (the crash detector). Both prove the sweep's classes can go red.
"""

import collections.abc
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kernel import compose                                            # noqa: E402
from kernel.errors import OpError                                     # noqa: E402


# EXACT param names (not substrings — "account" contains "count" but is not numeric). Read against
# the live registry's 152 declared params.
#
# NON-NEGATIVE QUANTITIES: a count of bytes / a size / a ceiling — a negative value is MALFORMED
# and must be refuse-or-declared-lawful.
NONNEG_PARAMS = frozenset({"size", "length", "ceiling", "arrival_count", "byte_total",
                           "max_arrivals", "arrivals_per_admitted_act"})
# other numeric scalars — swept for coverage (negative/zero/huge) but a negative is NOT flagged
# malformed (a priority, an offset, a timestamp may legitimately be any sign).
OTHER_NUMERIC_PARAMS = frozenset({"priority", "start", "uid", "gid", "round", "atime", "mtime", "now"})
NUMERIC_PARAMS = NONNEG_PARAMS | OTHER_NUMERIC_PARAMS
# bytes/string CONTENT params the door might canonicalise — a non-UTF-8 value is MALFORMED.
BYTESSTR_PARAMS = frozenset({"value", "content", "bytes", "text", "message", "address", "term"})

# LISTish params (a schema list, not a scalar) — a placeholder must be [] so the handler runs.
LIST_PARAMS = frozenset({"when", "then", "reads", "actions", "levels", "capabilities", "closers",
                         "records", "limits", "families", "events_available", "revealed_set",
                         "sees", "does_not_see", "derived_values", "does_not_declare",
                         "coalesced_events", "protected_packs"})

HUGE = 10 ** 19

# THE KNOWN-FINDINGS BASELINE — silently-accepted MALFORMED rows (a NEGATIVE value recorded for a
# non-negative quantity). NOW EMPTY: the five findings this sweep surfaced on its first run
# (AMEND-BUDGET.ceiling, MEM-GRANT.size ungoverned, FILE-LOCK/UNLOCK/TRUNCATE.length) are CLOSED by
# EP-MAINT-OUTSIDE-2 C-1 — the PARAM-KINDS `quantity` declaration on the op META plus the door's
# call-time guard refuse a negative or non-integer declared quantity at the door (AR-2, with a row).
# The sweep asserts the malformed-accept SET equals exactly this baseline: a NEW row (a regression,
# or a newly-unvalidated op) reds; a row that starts accepting a malformed value again reds.
KNOWN_MALFORMED_ACCEPTS = set()

# THE REJECTED FINDING CLASS — the crash where the record write owes a refusal (EP-MAINT-OUTSIDE-2
# C-3/C-4; archi :3520). The crash is commit.py's BatchFailed: a value that is not JSON-serialisable
# (a raw non-UTF-8 byte string) reaches the group commit and fails it for the whole barrier. C-3
# CLOSED the crash for TEXT params at the door: a `text`-kind param handed raw bytes refuses AR-2
# BEFORE the group commit, so the six text rows (CREATE-INFO.content, CREATE-RULE.value+text,
# DICT-ENTRY.term, FILE-XATTR-LAW.value — and the CREATE-RULE.text[empty] that was collateral of a
# sibling row's crash corrupting the shared kernel) now read REFUSED or ACCEPTED, never REJECTED.
# NOW EMPTY (EP-MAINT-OUTSIDE-3; archi :3575). The two rows that remained were NOT alike, and each is
# closed BY ITS DECLARED KIND:
#   FILE-XATTR-SET.value is a GENUINE byte payload — the door now ENCODES a raw-bytes value to the B8
#     tagged form (gate.py PART 1) BEFORE the group commit, so its nonutf8 row reads ACCEPTED, not
#     REJECTED (an encoded, canonical-safe value; still bytesstr by its declared `bytes` kind).
#   FILE-READ-AGGREGATE.bytes is a MIS-KINDED int byte-TOTAL — re-kinded `bytes -> quantity` in the pack
#     (PART 2), so the sweep drives it as a numeric (neg/zero/huge) and the door's quantity guard refuses
#     a negative or non-integer total; it has NO nonutf8 row any more, so nothing crashes.
# The REJECTED finding CLASS is KEPT as a guard: a NEW REJECTED row reds (test_rejected_class_equals_the
# _known_baseline), and the planted handler-crash positive proves the class can still fire.
KNOWN_REJECTED = set()


def rejected_rows(rows):
    """The (op, param, label) of every row the door REJECTED (the encoder raised a non-OpError, so the
    value was never silently recorded) — the crash class C-4 pins and tracks."""
    return {(op, param, label) for op, param, label, _m, outcome in rows if outcome.startswith("REJECTED")}

EVIDENCE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "planning", "evidence", "EP-INSTRUMENTS-1", "boundary-sweep.md")


def _category(param, kind=None):
    # DECLARED KIND FIRST (EP-MAINT-OUTSIDE-3 PART 3; archi :3575). A param's sweep category is derived
    # from its op's `param_kinds` declaration, not from its NAME: a `quantity` (and a `measurement`,
    # which is a non-negative numeric EXACTLY AS TODAY) is numeric; a `text`/`bytes` payload is
    # bytesstr. An UNDECLARED param — or a declared kind outside this closed set — falls back to the
    # NAME lists below, so today's sweep is preserved for every param but the ones the pack re-kinds.
    if kind in ("quantity", "measurement"):
        return "numeric"
    if kind in ("text", "bytes"):
        return "bytesstr"
    if param in NUMERIC_PARAMS:
        return "numeric"
    if param in BYTESSTR_PARAMS:
        return "bytesstr"
    return "opaque"


def _is_nonneg(param, kind=None):
    # A declared `quantity`/`measurement` is non-negative BY KIND (its neg boundary is malformed and the
    # door's quantity guard refuses it); otherwise the NAME list governs (undeclared params).
    if kind in ("quantity", "measurement"):
        return True
    return param in NONNEG_PARAMS


def _boundaries(param, kind=None):
    """The boundary values for a param, by category (derived from its DECLARED KIND, name-fallback for
    an undeclared param). Returns [(label, value, malformed?)].

    A NEGATIVE value for a non-negative quantity is MALFORMED (a size/length/ceiling/byte-total cannot
    be < 0). Zero and huge are boundary-but-lawful. A non-UTF-8 value of a CONTENT/bytes param is
    LAWFUL by design (binary content and binary xattr must round-trip — EP-MAINT-OUTSIDE-1 B8), so
    it is swept for coverage but never flagged malformed; the door refusing it would be the defect.
    """
    c = _category(param, kind)
    if c == "numeric":
        return [("neg", -5, _is_nonneg(param, kind)), ("zero", 0, False), ("huge", HUGE, False)]
    if c == "bytesstr":
        return [("empty", "", False), ("nonutf8", b"\xff\xfe\x00\x80", False)]
    return []


def _placeholder(param, suffix=""):
    if param in LIST_PARAMS:
        return []
    if param in NUMERIC_PARAMS:
        return 1
    return "x-" + param + suffix


def _params_for(gate, op, suffix=""):
    spec = gate.ops[op]["meta"].get("params") or {}
    return {p: _placeholder(p, suffix) for p in spec}


def sweep_row(store, gate, op, param, value, suffix=""):
    """Drive `op` with `param` set to `value` (other params minimal, made unique per row by
    `suffix` so an accepted write on a shared kernel does not collide with the next). Returns
    'REFUSED'|'ACCEPTED'|'REJECTED:<exc>'."""
    params = _params_for(gate, op, suffix)
    params[param] = value
    try:
        gate.execute(op, "owner", params)
        return "ACCEPTED"
    except OpError:
        return "REFUSED"
    except Exception as e:
        # the canonical encoder (or a type check) refused a malformed value by raising — the value
        # was NEVER silently recorded. Not a clean OpError, but not silent acceptance either.
        return "REJECTED:" + type(e).__name__


def run_sweep(gate_factory, extra_ops=()):
    """Generate + run the whole sweep. A FRESH kernel PER OP (fast — one build per op — and
    isolated, so one op's accepted writes never flip another op's reading). Within an op, each
    row's identifying params carry a unique suffix. `extra_ops` names ops registered by the
    factory beyond the base registry (for the planted positive). Returns (rows, malformed_accepts).
    rows: list of (op, param, label, value_malformed, outcome).
    malformed_accepts: set of (op, param, label) where a MALFORMED value was ACCEPTED."""
    rows = []
    malformed_accepts = set()
    _s0, gate0, _v0 = gate_factory()
    ops = sorted(set(gate0.ops) | set(extra_ops))
    for op in ops:
        meta = gate0.ops[op]["meta"]
        spec = meta.get("params") or {}
        kinds = meta.get("param_kinds") or {}              # the op's DECLARED param kinds (PART 3)
        swept = [(p, b) for p in spec for b in _boundaries(p, kinds.get(p))]
        if not swept:
            continue
        store, gate, _v = gate_factory()          # a fresh, clean kernel for this op
        n = 0
        for param in spec:
            for label, value, malformed in _boundaries(param, kinds.get(param)):
                n += 1
                outcome = sweep_row(store, gate, op, param, value, suffix="-%d" % n)
                rows.append((op, param, label, malformed, outcome))
                if malformed and outcome == "ACCEPTED":
                    malformed_accepts.add((op, param, label))
    return rows, malformed_accepts


def _factory():
    d = tempfile.mkdtemp(prefix="i5-sweep-")
    return compose.build_full_kernel(os.path.join(d, "rec.jsonl"), os.path.join(d, "blobs"))[:3]


# memoise the base sweep (no planted op): the coverage / conformance / evidence tests share it.
_BASE_SWEEP = None


def base_sweep():
    global _BASE_SWEEP
    if _BASE_SWEEP is None:
        _BASE_SWEEP = run_sweep(_factory)
    return _BASE_SWEEP


class TestI5BoundarySweep(unittest.TestCase):

    def test_coverage_every_declared_scalar_param_is_swept(self):
        # the sweep is GENERATED from the live registry (P2): every declared numeric/bytes-string
        # param of every op contributes rows. Coverage is driven, not asserted by a typed count.
        _s, gate, _v = _factory()
        declared_scalar = 0
        for op in gate.ops:
            meta = gate.ops[op]["meta"]
            kinds = meta.get("param_kinds") or {}
            for p in (meta.get("params") or {}):
                if _category(p, kinds.get(p)) in ("numeric", "bytesstr"):
                    declared_scalar += 1
        rows, _ = base_sweep()
        swept_params = {(op, p) for op, p, _l, _m, _o in rows}
        self.assertEqual(len(swept_params), declared_scalar,
                         "a declared scalar param was not swept — the generator missed it")
        self.assertGreater(len(rows), 50)   # a real sweep, not an empty one

    def test_malformed_accepts_equal_the_known_baseline(self):
        # THE CONFORMANCE ASSERTION: a malformed value (a negative non-negative-quantity, a
        # non-UTF-8 content) is refuse-or-declared-lawful — i.e. NOT silently accepted, EXCEPT the
        # pinned known findings. A new silently-accepted-malformed row reds here.
        _rows, malformed_accepts = base_sweep()
        new_findings = malformed_accepts - KNOWN_MALFORMED_ACCEPTS
        fixed = KNOWN_MALFORMED_ACCEPTS - malformed_accepts
        self.assertEqual(new_findings, set(),
                         "NEW silently-accepted-malformed row(s) — a param the door does not "
                         "validate (a regression or an unvalidated new op): %s" % new_findings)
        self.assertEqual(fixed, set(),
                         "a known-finding row no longer accepts a malformed value — it was fixed; "
                         "update KNOWN_MALFORMED_ACCEPTS and the close: %s" % fixed)

    def test_b5_planted_sanity_mem_grant_negative_size_refuses(self):
        # B5 is one row of the sweep: on the GOVERNED path (the actor holds a budget) a negative
        # grant size MUST refuse. Remove B5's sign check and this reds. (The UNGOVERNED path — no
        # budget — is the pinned finding above: the sign check lives in the budget arm.)
        store, gate, _v = _factory()
        gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "owner", "ceiling": 100})
        try:
            gate.execute("MEM-GRANT", "owner", {"region": "r-b5", "size": -5})
            refused = False
        except OpError:
            refused = True
        self.assertTrue(refused, "MEM-GRANT accepted a negative size on the governed path — B5's "
                                 "sign check is gone")

    def test_planted_positive_unvalidated_numeric_param_is_caught(self):
        # PLANTED POSITIVE: a synthetic op whose handler ignores its `size` param accepts a
        # negative value. The sweep's malformed-accept detector MUST catch it.
        def factory_with_bad_op():
            s, gate, v = _factory()

            def bad(actor, params):
                return {"actor": actor, "action": "UNVALIDATED-SIZE-OP", "object": "x",
                        "rule_cited": "ROOT-NEG-5", "payload": {"size": params.get("size")}}
            gate.register("UNVALIDATED-SIZE-OP",
                          {"description": "planted op with an unvalidated numeric param",
                           "rules": ["ROOT-NEG-5"], "params": {"size": "required"}}, bad)
            return s, gate, v

        _rows, malformed_accepts = run_sweep(factory_with_bad_op)
        self.assertIn(("UNVALIDATED-SIZE-OP", "size", "neg"), malformed_accepts,
                      "the sweep did not catch the unvalidated negative size — the planted "
                      "positive did not fire, so the sweep proves nothing")

    def test_rejected_class_equals_the_known_baseline(self):
        # THE REJECTED FINDING CLASS (EP-MAINT-OUTSIDE-2 C-4; archi :3507): a crash where the door owes
        # a refusal is a NAMED, PINNED finding — distinct from ACCEPTED-malformed and from a clean
        # REFUSED. The sweep asserts the REJECTED set equals exactly the pinned baseline: a NEW crash
        # (a regression, or a newly-crashing op) reds; a pinned row that stops crashing (the door
        # refusal landing) also reds so the fix is noticed and the baseline updated then.
        rows, _ = base_sweep()
        rejected = rejected_rows(rows)
        new_crashes = rejected - KNOWN_REJECTED
        stopped = KNOWN_REJECTED - rejected
        self.assertEqual(new_crashes, set(),
                         "NEW REJECTED row(s) — a param the door crashes on where it owes a refusal "
                         "(a regression or a newly-crashing op): %s" % new_crashes)
        self.assertEqual(stopped, set(),
                         "a pinned REJECTED row no longer crashes — the door-refusal fix landed; "
                         "update KNOWN_REJECTED and the close: %s" % stopped)

    def test_c3_declared_text_params_refuse_raw_bytes_at_the_door(self):
        # C-3 (EP-MAINT-OUTSIDE-2; archi :3520): every param the live registry declares `text`-kind
        # must REFUSE a raw non-UTF-8 (bytes) value at the door — never crash it (REJECTED), never
        # accept it. This is the positive conformance the door provides, driven from the pack's own
        # param_kinds. Able to fail: a text param that accepted or crashed a raw-bytes value reds here.
        _s, gate, _v = _factory()
        text_params = {(op, p) for op in gate.ops
                       for p, kind in (gate.ops[op]["meta"].get("param_kinds") or {}).items()
                       if kind == "text"}
        self.assertTrue(text_params, "no text-kind params declared — the door guard proves nothing")
        rows, _ = base_sweep()
        by = {(op, p, l): o for op, p, l, _m, o in rows}
        for op, p in sorted(text_params):
            key = (op, p, "nonutf8")
            if key in by:                                    # the sweep drives a nonutf8 row for it
                self.assertEqual(by[key], "REFUSED",
                                 "%s.%s is declared text but did not REFUSE a raw-bytes value at the "
                                 "door (got %s)" % (op, p, by[key]))

    def test_planted_positive_a_handler_crash_reads_rejected(self):
        # PLANTED POSITIVE for the crash class: a synthetic op whose handler RAISES a non-OpError on a
        # boundary value must read REJECTED (never ACCEPTED, never a clean REFUSED). Proves the REJECTED
        # class can fire — a class never seen firing is not known to be checking anything.
        def factory_with_crashing_op():
            s, gate, v = _factory()

            def crashes(actor, params):
                raise RuntimeError("planted crash: the handler raised where the door owes a refusal")
            gate.register("CRASH-ON-TEXT-OP",
                          {"description": "planted op whose handler crashes on a text param",
                           "rules": ["ROOT-NEG-5"], "params": {"text": "required"}}, crashes)
            return s, gate, v

        rows, _ = run_sweep(factory_with_crashing_op)
        crash_rows = {(op, param, label) for op, param, label, _m, o in rows
                      if op == "CRASH-ON-TEXT-OP" and o.startswith("REJECTED")}
        self.assertTrue(crash_rows,
                        "the sweep did not read the planted handler crash as REJECTED — the crash "
                        "detector did not fire, so the REJECTED class proves nothing")

    def test_evidence_table_regenerates(self):
        generated = render_sweep_evidence()
        with open(EVIDENCE_PATH, encoding="utf-8") as f:
            committed = f.read()
        self.assertEqual(generated.strip(), committed.strip(),
                         "the boundary-sweep evidence diverged from the live registry — "
                         "regenerate: python3 tests/test_instr_boundary_sweep.py --md")


def render_sweep_evidence():
    rows, malformed_accepts = base_sweep()
    ops = sorted({op for op, *_ in rows})
    out = []
    out.append("<!-- GENERATED by tests/test_instr_boundary_sweep.py --md — do not hand-edit. -->")
    out.append("")
    out.append("# I5 · Boundary sweep at the door — generated from the pack's param declarations")
    out.append("")
    out.append("Every declared numeric/bytes-string param of every op the live registry lists is "
               "driven with boundary values from its own schema category. The assertion is "
               "refuse-or-declared-lawful: a malformed value (negative non-negative-quantity, "
               "non-UTF-8 content) is never SILENTLY recorded.")
    out.append("")
    rejected = rejected_rows(rows)
    out.append(f"Ops with swept params: **{len(ops)}**. Sweep rows: **{len(rows)}**. "
               f"Silently-accepted-malformed rows: **{len(malformed_accepts)}**. "
               f"REJECTED (crash where the door owes a refusal) rows: **{len(rejected)}** "
               f"(pinned and tracked, EP-MAINT-OUTSIDE-2 C-4).")
    out.append("")
    out.append("## Silently-accepted-malformed findings")
    out.append("")
    out.append("The negative-quantity class (five rows) is CLOSED by EP-MAINT-OUTSIDE-2 C-1 — the "
               "PARAM-KINDS `quantity` declaration on the op META plus the door's call-time guard now "
               "refuse a negative or non-integer declared quantity at the door (AR-2, with a row).")
    out.append("")
    for op, param, label in sorted(malformed_accepts):
        out.append(f"- `{op}`.`{param}` accepts a **{label}** value (should refuse-or-declare-lawful)")
    if not malformed_accepts:
        out.append("_none — the negative-quantity class is closed at the door._")
    out.append("")
    out.append("## REJECTED findings (a crash where the record write owes a refusal)")
    out.append("")
    out.append("The crash is commit.py's BatchFailed: a non-serialisable (raw non-UTF-8) value reaches "
               "the group commit and fails it. EP-MAINT-OUTSIDE-2 C-3 CLOSED it for TEXT params at the "
               "door (a `text`-kind param handed raw bytes refuses AR-2 before the write). The rows "
               "below are BYTES-KIND by ruling (:3520) — a byte payload lawfully carries non-UTF-8, so "
               "the door is exempt; driven RAW (bypassing the adapter's B8 encoding) the lawful bytes "
               "still crash the write. Pinned and tracked, not the malformed-value crash the door closes.")
    out.append("")
    for op, param, label in sorted(rejected):
        out.append(f"- `{op}`.`{param}` **{label}** crashes (REJECTED) where the door owes a refusal")
    if not rejected:
        out.append("_none_")
    out.append("")
    out.append("## Full sweep")
    out.append("")
    out.append("| op | param | boundary | malformed | outcome |")
    out.append("|---|---|---|---|---|")
    for op, param, label, malformed, outcome in rows:
        out.append(f"| {op} | {param} | {label} | {'yes' if malformed else ''} | {outcome} |")
    out.append("")
    return "\n".join(out)


def _main(argv):
    if "--md" in argv:
        print(render_sweep_evidence())
        return 0
    return unittest.main(argv=["x"] + argv)


if __name__ == "__main__":
    _main(sys.argv[1:])
