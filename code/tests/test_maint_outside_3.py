# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (gate, door, param kind, tagged bytes, quantity, founding). NON-GOAL: no offensive
# capability of any kind — every test asserts the CORRECT behaviour by function: a genuine byte
# payload is encoded to a canonical-safe form at the door, a mis-kinded byte-total is guarded as a
# non-negative quantity, and one founding MINOR bump is attested. Authored from the architect's read
# (:3575) + our own code at the cited line; the outside harness was NOT read and NOT run. Full
# declaration: SCOPE-STATEMENT.md.
"""EP-MAINT-OUTSIDE-3 — the two REJECTED bytes rows closed BY DECLARED KIND.

  A2 (PART 1)  a raw-bytes FILE-XATTR-SET.value is ENCODED at the door to the B8 tagged form (a
               genuine byte payload) — ACCEPTED, idempotent, never crashes the record write.
  A3 (PART 2)  FILE-READ-AGGREGATE.bytes is re-kinded `bytes -> quantity` (a mis-kinded int total);
               the door's quantity guard refuses a negative or non-integer total, a valid int passes.
  A4 (the founding move)  ONE MINOR bump 1.49.0 -> 1.50.0, ONE re-kind, OP_CHECKS and op-population
               unchanged (no new check kind, no new op); the §A57 three count families driven.

The I5 sweep arm (A1 — the sweep reads ZERO REJECTED by declared kind) lives in
tests/test_instr_boundary_sweep.py.
"""

import base64
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kernel import compose                                            # noqa: E402
from kernel import gate as gate_mod                                   # noqa: E402
from kernel.errors import OpError                                     # noqa: E402
from kernel.opdefs import OP_CHECKS                                   # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
PACK_PATH = os.path.join(_HERE, "..", "src", "founding", "founding-pack.json")


def _kernel():
    d = tempfile.mkdtemp(prefix="maint3-")
    store, gate, views = compose.build_full_kernel(
        os.path.join(d, "rec.jsonl"), os.path.join(d, "blobs"))[:3]
    return store, gate, views


def _pack():
    with open(PACK_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _op_kinds(pack, opname):
    """The `param_kinds` the pack declares for one op (read from the pack DATA, not the live meta)."""
    found = {}

    def rec(o):
        if isinstance(o, dict):
            if o.get("kind") == "op_definition" and o.get("name") == opname:
                found.update((o.get("definition") or {}).get("param_kinds") or {})
            for v in o.values():
                rec(v)
        elif isinstance(o, list):
            for v in o:
                rec(v)
    rec(pack)
    return found


def _op_population(pack):
    ops = set()

    def rec(o):
        if isinstance(o, dict):
            if o.get("kind") == "op_definition":
                ops.add(o.get("name"))
            for v in o.values():
                rec(v)
        elif isinstance(o, list):
            for v in o:
                rec(v)
    rec(pack)
    return len(ops)


def _recorded_value(store, n, op="FILE-XATTR-SET"):
    """The `value` field of the op's own decision row among the records added since index n (the
    dual-audit mirror lands its own row after, so the decision is not necessarily store.all()[-1])."""
    for e in store.all()[n:]:
        if e.get("action") == op:
            return (e.get("payload") or {}).get("value")
    return None


# ==================================================================================================
# A2 — PART 1: FILE-XATTR-SET.value raw bytes ENCODED at the door to the B8 tagged form (idempotent)
# ==================================================================================================

class TestXattrEncoded(unittest.TestCase):

    def test_the_door_tag_is_the_records_fs_b8_tag_byte_identical(self):
        # The kernel cannot import the bridge adapter (records_fs imports kernel.errors — kernel->bridge
        # would be circular), so the B8 tag is RE-USED at the door, not imported. Prove the two strings
        # are byte-identical: the door encodes to the SAME form the FUSE port's getxattr reads back.
        from bridge.records_fs import _XATTR_BYTES_TAG as fs_tag
        self.assertEqual(gate_mod._XATTR_BYTES_TAG, fs_tag)

    def test_a_raw_nonutf8_value_is_encoded_to_the_tagged_form_and_accepted(self):
        # A raw non-UTF-8 byte value crashes the record write pre-PART-1 (BatchFailed: not JSON
        # serialisable). PART 1 encodes it at the door to the B8 tagged base64 dict, so it is ACCEPTED
        # and the recorded value is the tagged form (byte-faithful, canonical-safe). Reds pre-encode.
        store, gate, _v = _kernel()
        raw = b"\xff\xfe\x00\x80"
        n = len(store.all())
        gate.execute("FILE-XATTR-SET", "owner",
                     {"path": "/f", "name": "user.x", "value": raw, "provenance": "p"})
        self.assertFalse(getattr(store, "_broken", None), "the raw byte value crashed the store")
        rec = _recorded_value(store, n)
        self.assertEqual(rec, {gate_mod._XATTR_BYTES_TAG: base64.b64encode(raw).decode("ascii")},
                         "a raw non-UTF-8 value was not recorded in the B8 tagged form")

    def test_a_raw_utf8_value_is_recorded_as_a_plain_string(self):
        # The encode DISCRIMINATES: a valid-UTF-8 byte value becomes a plain string (byte-identical to
        # text), not the tagged form. Reds pre-encode (raw bytes crash the write).
        store, gate, _v = _kernel()
        n = len(store.all())
        gate.execute("FILE-XATTR-SET", "owner",
                     {"path": "/g", "name": "user.x", "value": b"hello", "provenance": "p"})
        self.assertFalse(getattr(store, "_broken", None))
        self.assertEqual(_recorded_value(store, n), "hello")

    def test_the_encode_is_idempotent_for_an_already_tagged_or_string_value(self):
        # IDEMPOTENT: an already-encoded value (the tagged dict, or a plain str) is not `bytes`, so the
        # door leaves it untouched — a second pass through the door is a no-op (the FUSE adapter already
        # B8-encodes, so the door must not double-encode).
        tagged = {gate_mod._XATTR_BYTES_TAG: base64.b64encode(b"\xff\xfe").decode("ascii")}
        store, gate, _v = _kernel()
        n = len(store.all())
        gate.execute("FILE-XATTR-SET", "owner",
                     {"path": "/h", "name": "user.x", "value": tagged, "provenance": "p"})
        self.assertEqual(_recorded_value(store, n), tagged, "an already-tagged value was re-encoded")
        store, gate, _v = _kernel()
        n = len(store.all())
        gate.execute("FILE-XATTR-SET", "owner",
                     {"path": "/i", "name": "user.x", "value": "plain", "provenance": "p"})
        self.assertEqual(_recorded_value(store, n), "plain", "a plain string value was altered")


# ==================================================================================================
# A3 — PART 2: FILE-READ-AGGREGATE.bytes re-kinded `quantity`, guarded at the door
# ==================================================================================================

class TestReadAggregateReKinded(unittest.TestCase):

    _BASE = {"path": "/f", "inode": 1, "reads": 3, "provenance": "p"}

    def test_the_pack_declares_bytes_a_quantity(self):
        # PART 2: the pack re-kinds FILE-READ-AGGREGATE.bytes from `bytes` to `quantity`. Reds against
        # the pre-move pack (kind `bytes`). Read from the pack DATA and from the live op meta.
        self.assertEqual(_op_kinds(_pack(), "FILE-READ-AGGREGATE").get("bytes"), "quantity")
        _s, gate, _v = _kernel()
        self.assertEqual(gate.ops["FILE-READ-AGGREGATE"]["meta"]["param_kinds"].get("bytes"), "quantity")

    def _refuses_at_door(self, value):
        store, gate, _v = _kernel()
        n = len(store.all())
        with self.assertRaises(OpError):
            gate.execute("FILE-READ-AGGREGATE", "owner", {**self._BASE, "bytes": value})
        added = store.all()[n:]
        refusals = [e for e in added if e.get("action") == "op-refused"
                    and e.get("rule_cited") == "AR-2"
                    and (e.get("payload") or {}).get("op") == "FILE-READ-AGGREGATE"]
        self.assertTrue(refusals, "no AR-2 refusal row for bytes=%r" % (value,))

    def test_a_negative_total_is_refused_at_the_door(self):
        # A negative byte-total is malformed for a quantity (a count of bytes cannot be < 0) — the
        # door's quantity guard refuses it (AR-2, a row). Reds pre-move, where bytes was `bytes`-kind
        # and the guard did not apply (a negative total was silently ACCEPTED).
        self._refuses_at_door(-5)

    def test_a_non_integer_total_is_refused_bool_and_float(self):
        # A quantity is an INT: a boolean (an int in Python, excluded FIRST) and a float both refuse.
        self._refuses_at_door(True)
        self._refuses_at_door(1.5)

    def test_a_valid_int_total_is_admitted(self):
        # The guard DISCRIMINATES: a valid non-negative int total (zero included) is ACCEPTED.
        for total in (0, 100):
            store, gate, _v = _kernel()
            n = len(store.all())
            gate.execute("FILE-READ-AGGREGATE", "owner",
                         {**self._BASE, "path": "/f-%d" % total, "bytes": total})
            self.assertTrue([e for e in store.all()[n:] if e.get("action") == "FILE-READ-AGGREGATE"],
                            "a valid int byte-total was not recorded")

    def test_its_rejected_row_is_gone_no_crash(self):
        # The re-kind removes the `bytes`-kind nonutf8 row entirely: bytes is numeric now, driven with
        # neg/zero/huge, none of which crashes the write. Drive the neg boundary: it REFUSES cleanly,
        # never crashes the store.
        store, gate, _v = _kernel()
        try:
            gate.execute("FILE-READ-AGGREGATE", "owner", {**self._BASE, "bytes": -5})
        except OpError:
            pass
        self.assertFalse(getattr(store, "_broken", None), "the re-kinded quantity crashed the store")


# ==================================================================================================
# A4 — THE FOUNDING MOVE: MINOR bump 1.49.0 -> 1.50.0, ONE re-kind, counts unchanged (§A57)
# ==================================================================================================

class TestFoundingBump(unittest.TestCase):

    def test_the_founding_is_one_minor_above_the_base(self):
        # ONE MINOR bump for the re-kind (a DATA-born move). Reds against the base 1.49.0.
        self.assertEqual(_pack()["founding_version"], "1.50.0")

    def test_the_one_param_is_re_kinded_quantity(self):
        # EXACTLY the one re-kind: FILE-READ-AGGREGATE.bytes -> quantity; FILE-XATTR-SET.value stays
        # `bytes` (a genuine payload, encoded not re-kinded).
        pack = _pack()
        self.assertEqual(_op_kinds(pack, "FILE-READ-AGGREGATE").get("bytes"), "quantity")
        self.assertEqual(_op_kinds(pack, "FILE-XATTR-SET").get("value"), "bytes")

    def test_no_check_kind_minted_op_checks_unchanged(self):
        # §A57 family 1 — OP_CHECKS: the `quantity` guard already exists (EP-MAINT-OUTSIDE-2); a re-kind
        # of an existing param mints NO new check kind.
        self.assertEqual(len(OP_CHECKS), 19)

    def test_no_op_added_op_population_unchanged(self):
        # §A57 family 2 — op-population: a re-kind adds no op.
        self.assertEqual(_op_population(_pack()), 93)

    def test_the_founding_version_moved_family_3(self):
        # §A57 family 3 — the whole-file version/hash MOVED (the pack changed): the version is above the
        # base. (The pack sha is attested in BUILD-PROGRESS_v3.md and pinned in test_ep51; the
        # bump-attestation guard test_founding_is_logged binds version+sha in one entry.)
        self.assertEqual(_pack()["founding_version"], "1.50.0")


if __name__ == "__main__":
    unittest.main()
