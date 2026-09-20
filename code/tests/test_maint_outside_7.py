# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (door, declared kind, refusal row, serialisable, poison, durability). NON-GOAL: no
# offensive capability of any kind — every test asserts the CORRECT behaviour by function: a
# declared parameter value the record write cannot serialise is a RECORDED REFUSAL at the door
# (the existing AR-2 nonconforming-call form), never a crash that poisons the store; the store's
# poison stays reserved for the one thing it is for — a write that did not reach the disk. A `set`
# stands in for "any non-serialisable value", by function. Authored from the architect's round-3
# read (ARCHI-READ-3.md F3) + our own code at the cited lines; the outside harness was NOT read and
# NOT run. Full declaration: SCOPE-STATEMENT.md.
"""EP-MAINT-OUTSIDE-7 — the gate checks every declared kind for serialisability at the door.

The door's kind validator (kernel.gate._decide, the PARAM-KINDS guard) refused only bytes/bytearray
for kind `text` and never required `str`, so a Python `set` (or any non-serialisable value) passed
the door. Serialisation happens later at the append (kernel.store._append_one, `json.dumps(...,
default=frozen_default)`), where a non-serialisable value raises TypeError INSIDE the appender on the
decision row the gate had ALREADY decided to write — the refusal path is skipped, no row lands, and
`_poison` sets `_broken`, so every later publish and batch is refused forever. A non-serialisable
content value POISONED the store.

  A1  a `set` as a `text` content value is a RULE-CITED AR-2 REFUSAL ROW at the door and the store
      stays ALIVE (a subsequent lawful publish succeeds). PLANT (the leak, shown by the current code
      / by reverting the door's text-str requirement): the set passes the door and poisons the store.
  A2  every declared kind's value is checked for JSON-serialisability BEFORE publication — a
      non-serialisable value for a NON-text declared kind (a `measurement`, which has no scalar type
      guard) is refused at the door too, and a lawful serialisable value (including a NON-string one,
      e.g. an int `value`, which CREATE-RULE relies on) is admitted. PLANT: remove the general
      serialisability check and the measurement `set` reaches the append and poisons — so the check
      must cover EVERY declared kind, not only `text`.
      [RAISED, NOT SHIPPED: the plan's A2 clause "text requires `str` (not just 'not bytes')" is a
      false premise — CREATE-RULE lawfully carries a numeric `value` (an int, declared kind `text`,
      and serialisable), so tightening `text` to strict `str` reds tests/test_boot (the boot path).
      F3's poison leak is about NON-SERIALISABILITY, which an int is not; the serialisability net
      closes it without the str tightening. The str clause is raised for the architect's ruling.]
  A3  poisoning is RESERVED for a durability failure: a write that does NOT reach the disk still
      poisons (unchanged); a content-validation failure does NOT (it is a refusal). PLANT: a content
      failure poisoning the store reds A3's second assertion.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kernel import compose                                             # noqa: E402
from kernel import gate as gate_mod                                    # noqa: E402
from kernel import opdefs                                              # noqa: E402
from kernel.commit import BatchFailed                                  # noqa: E402
from kernel.errors import OpError                                      # noqa: E402


def _kernel():
    d = tempfile.mkdtemp(prefix="maint7-")
    store, gate, views = compose.build_full_kernel(
        os.path.join(d, "rec.jsonl"), os.path.join(d, "blobs"))[:3]
    return d, store, gate, views


def _refuses_at_door(case, gate, store, op, params):
    """The refusal is a RECORDED op-refused row citing AR-2, added by this call (the dual-audit
    mirror lands its own row after, so it is not necessarily store.all()[-1]); and the store is NOT
    poisoned — the refusal landed BEFORE the append that a non-serialisable value would have crashed.
    A poison (BatchFailed out of the append) is the pre-fix behaviour and reds `assertRaises(OpError)`
    (a BatchFailed is not an OpError) — which is exactly the leak this unit closes."""
    n = len(store.all())
    with case.assertRaises(OpError):
        gate.execute(op, "owner", params)
    added = store.all()[n:]
    refusals = [e for e in added if e.get("action") == "op-refused"
                and e.get("rule_cited") == "AR-2"
                and (e.get("payload") or {}).get("op") == op]
    case.assertTrue(refusals, "%s did not record an AR-2 refusal row at the door" % op)
    case.assertFalse(getattr(store, "_broken", None),
                     "%s poisoned the store instead of refusing at the door" % op)
    return refusals


# A synthetic op that declares a `measurement` param and simply ECHOES it into the payload — no
# structured-field check, so the value reaches the append. `measurement` has NO scalar type guard at
# the door (opdefs: the op's own structured-field refusal stands), so this op is the faithful vehicle
# for "a non-serialisable value for a non-text declared kind": without the door's general
# serialisability check, the echoed value crashes the record write and poisons the store. (A REAL
# measurement op's handler would refuse a malformed value before the append, hiding the leak; the
# synthetic echo is OUTSIDE-2's own idiom for exercising the door in isolation.)
def _register_measure_echo(gate):
    def handler(actor, params):
        return {"actor": actor, "action": "SYNTH-MEASURE-OP", "object": "x",
                "rule_cited": "ROOT-NEG-5",
                "payload": {"m": params.get("m")}}
    gate.register("SYNTH-MEASURE-OP",
                  {"description": "synthetic op echoing a declared measurement param into the payload",
                   "rules": ["ROOT-NEG-5"], "params": {"m": "required"},
                   opdefs.PARAM_KINDS: {"m": "measurement"}}, handler)


# ==================================================================================================
# A1 — a set as content is a refusal row; the store stays alive
# ==================================================================================================

class TestA1SetAsContentIsRefusalRow(unittest.TestCase):

    def test_a1_set_as_text_content_is_refusal_row(self):
        # A `set` handed to the `text`-kind param `term` (DICT-ENTRY: param_kinds {term: text}, no
        # checks, no custom handler) is a rule-cited AR-2 refusal row at the door. Pre-fix the set is
        # not bytes so it passes the door, reaches the append, `json.dumps` raises TypeError inside
        # `_append_one`, and `_poison` marks the store `_broken` — the plant (a poison, not a refusal).
        _d, store, gate, _v = _kernel()
        _refuses_at_door(self, gate, store, "DICT-ENTRY", {"term": {1, 2, 3}, "entity_kind": "x"})

    def test_a1_store_stays_alive_a_later_publish_succeeds(self):
        # THE STORE IS ALIVE: after the refused set, a subsequent LAWFUL DICT-ENTRY publishes and
        # lands. Pre-fix the set poisoned the store, so this later publish would itself be refused
        # (`_broken`) — the check can fail on the store-alive half too.
        _d, store, gate, _v = _kernel()
        _refuses_at_door(self, gate, store, "DICT-ENTRY", {"term": {1, 2, 3}, "entity_kind": "x"})
        gate.execute("DICT-ENTRY", "owner", {"term": "café — 汉字", "entity_kind": "x"})
        landed = [e for e in store.all() if e.get("action") == "DICT-ENTRY"
                  and (e.get("payload") or {}).get("term") == "café — 汉字"]
        self.assertTrue(landed, "the store did not stay alive — a later lawful publish did not land")
        self.assertFalse(getattr(store, "_broken", None))


# ==================================================================================================
# A2 — every declared kind checked (type + serialisability) before publication
# ==================================================================================================

class TestA2EveryDeclaredKindChecked(unittest.TestCase):

    def test_a2_a_lawful_nonstring_serialisable_text_value_is_admitted(self):
        # F3 is about NON-SERIALISABILITY, not str-ness. A serialisable non-string value for a
        # text-kind param is LAWFUL and MUST be admitted: CREATE-RULE carries a numeric `value` (an
        # int, declared kind `text`), an int is serialisable, so it never poisoned and must not be
        # refused. This is the anti-regression for the RAISED "text requires str" clause — tightening
        # `text` to strict `str` reds this and tests/test_boot (the boot path).
        _d, store, gate, _v = _kernel()
        gate.execute("CREATE-RULE", "SYSTEM",
                     {"rule_id": "law:q", "policy_key": "q", "value": 7})
        landed = [e for e in store.all() if e.get("action") == "CREATE-RULE"
                  and (e.get("payload") or {}).get("value") == 7]
        self.assertTrue(landed, "a lawful serialisable int text-value was refused — F3 over-tightened text")
        self.assertFalse(getattr(store, "_broken", None))

    def test_a2_nonserialisable_value_for_a_non_text_kind_refused(self):
        # THE GENERAL CHECK: a non-serialisable value (a `set`) for a `measurement`-kind param — which
        # has NO scalar type guard — is refused at the door, and the store stays alive. PLANT: with
        # only the text-str fix and NO general serialisability check, the set reaches the append and
        # poisons (the check must cover every declared kind, not only `text`).
        _d, store, gate, _v = _kernel()
        _register_measure_echo(gate)
        _refuses_at_door(self, gate, store, "SYNTH-MEASURE-OP", {"m": {1, 2, 3}})

    def test_a2_a_serialisable_value_is_admitted(self):
        # THE CHECK DISCRIMINATES: a serialisable measurement value (a plain dict of primitives) is
        # admitted through the door and the echoed record lands — the door refuses only what the write
        # cannot record, never a lawful value.
        _d, store, gate, _v = _kernel()
        _register_measure_echo(gate)
        gate.execute("SYNTH-MEASURE-OP", "owner", {"m": {"value": 1, "cell": "S"}})
        got = [e for e in store.all() if e.get("action") == "SYNTH-MEASURE-OP"]
        self.assertTrue(got, "a lawful serialisable measurement value was not admitted")
        self.assertFalse(getattr(store, "_broken", None))


# ==================================================================================================
# A3 — poisoning reserved for a durability failure
# ==================================================================================================

class _DeadHandle:
    """A write descriptor whose write does not reach the disk — the durability failure `_append_one`'s
    `except` exists for. `_require_fh` returns an already-set `_fh` untouched, so replacing it drives
    the append straight into the poison path without disturbing the reader/finalizer machinery."""
    def write(self, *_a):
        raise OSError("simulated: the write did not reach the disk")
    def flush(self):
        raise OSError("simulated: the flush did not reach the disk")


class TestA3PoisoningReservedForDurability(unittest.TestCase):

    def test_a3_a_durability_failure_still_poisons(self):
        # UNCHANGED: a write that does not reach the disk STILL poisons (`_broken`), and the poison
        # message stays the durability message it already was. This is the path the content-validation
        # case is being moved OUT of — it must keep working.
        _d, store, gate, _v = _kernel()
        store._fh = _DeadHandle()
        try:
            gate.execute("DICT-ENTRY", "owner", {"term": "ok", "entity_kind": "x"})
        except BaseException:
            pass
        self.assertIsNotNone(getattr(store, "_broken", None),
                             "a write that did not reach the disk did not poison the store")
        self.assertIsInstance(store._broken, BatchFailed)
        self.assertIn("did not reach the kernel", str(store._broken))

    def test_a3_a_content_validation_failure_does_not_poison(self):
        # THE CONTRAST (the plant made executable): a content-validation failure — a `set` as content
        # — is a REFUSAL, never a poison. Reds if a content failure poisons the store.
        _d, store, gate, _v = _kernel()
        with self.assertRaises(OpError):
            gate.execute("DICT-ENTRY", "owner", {"term": {1, 2, 3}, "entity_kind": "x"})
        self.assertFalse(getattr(store, "_broken", None),
                         "a content-validation failure poisoned the store — it must be a refusal")


if __name__ == "__main__":
    unittest.main()
