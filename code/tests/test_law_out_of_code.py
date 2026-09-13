"""EP-02 acceptance battery: law out of code + deep freeze (design 28 §2, §I5).

T-DEEP-FREEZE       — a stored record is immutable all the way down, on append AND on load.
T-PACKS-CARRY-POLICY— the dual-audit action list and the syscall map are RECORDS; behaviour
                      follows the record (amend the pack, behaviour changes) not the code.
T-NO-LAW-IN-CODE    — first cut: root-law text lives only in the genesis seed, never in the
                      engine; the relocated vocabularies survive in code only as labeled
                      fallbacks; the two permitted engine vocabularies are present.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.store import EventStore  # noqa: E402
from kernel.compose import build_full_kernel  # noqa: E402
from kernel.protection import Protection  # noqa: E402
from kernel.syscall_port import SyscallPort  # noqa: E402
from kernel.errors import OpError  # noqa: E402
# EP-14: the constitution is no longer a boot.py literal — it lives in the founding pack
# (founding/founding-pack.json), read back through the installer accessor. The no-law-in-code
# guarantee tightens accordingly: the law text and full-form literals must live ONLY under
# founding/, and a hit anywhere else in src/ (boot.py now INCLUDED) fails.
from founding.install import root_laws, load_pack, PACK_PATH  # noqa: E402
ROOT_RULES = root_laws()

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
FOUNDING_DIR = os.path.join(SRC, "founding")


def _read(rel):
    with open(os.path.join(SRC, rel), encoding="utf-8") as f:
        return f.read()


def _src_py_outside_founding():
    """Every .py under src/ EXCEPT those under founding/ — the tightened scan surface:
    the law lives only in founding/, so a law literal anywhere here is a leak."""
    for root, _dirs, files in os.walk(SRC):
        if os.path.abspath(root).startswith(os.path.abspath(FOUNDING_DIR)):
            continue
        for name in files:
            if name.endswith(".py"):
                p = os.path.join(root, name)
                with open(p, encoding="utf-8") as f:
                    yield os.path.relpath(p, SRC).replace(os.sep, "/"), f.read()


def _pack_record(name, levels):
    """An amendment to a category_pack: a later CREATE-INFO with the same name wins."""
    return {"actor": "owner", "action": "CREATE-INFO", "object": f"pack:{name}",
            "rule_cited": "BOOT-INT",
            "payload": {"kind": "category_pack", "name": name, "levels": levels}}


class TestDeepFreeze(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")

    def _nested(self):
        return {"actor": "SYSTEM", "action": "X", "rule_cited": "R",
                "payload": {"flat": 1, "nested": {"k": "v"}, "list": [1, 2]}}

    def test_appended_record_is_immutable_all_the_way_down(self):
        s = EventStore(self.path)
        rec = s._append(self._nested())
        with self.assertRaises(TypeError):
            rec["actor"] = "z"                       # envelope frozen (as before)
        with self.assertRaises(TypeError):
            rec["payload"]["flat"] = 9               # payload interior frozen (new)
        with self.assertRaises(TypeError):
            rec["payload"]["nested"]["k"] = "z"      # recursively frozen
        self.assertIsInstance(rec["payload"]["list"], tuple)  # a list becomes an immutable tuple
        with self.assertRaises(AttributeError):
            rec["payload"]["list"].append(3)

    def test_reloaded_record_is_also_frozen(self):
        EventStore(self.path)._append(self._nested())
        r = EventStore(self.path).all()[0]           # freeze happens on load too, not only append
        with self.assertRaises(TypeError):
            r["payload"]["nested"]["k"] = "z"
        self.assertIsInstance(r["payload"]["list"], tuple)


class TestPacksCarryPolicy(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views, self.blobs, self.v = build_full_kernel(
            os.path.join(self.dir, "record.jsonl"), os.path.join(self.dir, "blobs"))
        # EP-13B/W6: the shipped composition wires the dual-audit mirror by DEFAULT, so use that one
        # rather than instantiating a SECOND Protection over the same store (a second mirror would
        # double every audit record). build_full_kernel exposes it as views.protection.
        self.prot = self.views.protection
        self.sp = SyscallPort(self.gate, self.views)

    def test_the_vocabularies_are_records(self):
        packs = self.views.category_packs()
        self.assertIn("GRANT-READ", packs["dual-audit-actions"]["levels"])
        ops = {l["syscall"]: l["op"] for l in packs["syscall-ops"]["levels"]}
        self.assertEqual(ops["open"], "FILE-CREATE")
        self.assertIn("rule-errno", packs)

    def test_mirror_follows_the_pack_not_the_code(self):
        with self.assertRaises(OpError):
            self.gate.execute("NOPE", "x", {})       # op-refused: in the seeded pack -> mirrored
        self.assertEqual(len(self.store.by_action("dual-audit-record")), 1)
        # amend the pack to EXCLUDE op-refused: the mirror must now follow the record
        self.store._append(_pack_record("dual-audit-actions", ["MOUNT"]))
        with self.assertRaises(OpError):
            self.gate.execute("ALSO-NOPE", "x", {})  # another op-refused
        self.assertEqual(len(self.store.by_action("dual-audit-record")), 1)  # NOT mirrored now

    def test_syscall_errno_follows_the_pack_not_the_code(self):
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "web", "ceiling": 10})
        r = self.sp.syscall("mmap", "web", {"addr": "r1", "length": 100, "holder": "web"})
        self.assertEqual(r["errno"], "ENOMEM")       # per the seeded rule-errno pack
        # amend rule-errno: the same governed refusal must now map to the new errno
        self.store._append(_pack_record("rule-errno", [{"rule": "MEM-LAW-BUDGET", "errno": "EDQUOT"}]))
        r2 = self.sp.syscall("mmap", "web", {"addr": "r2", "length": 100, "holder": "web"})
        self.assertEqual(r2["errno"], "EDQUOT")

    def test_malformed_pack_does_not_wedge_the_write_path(self):
        # a junk dual-audit-actions pack (no `levels`) must NOT crash the on-append mirror;
        # governed writes keep committing, the fold EXCLUDES the junk record, so the previous
        # well-formed pack still stands and the audit keeps running from THAT. No fallback is
        # involved and none ever was: the audit's only source is the recorded pack, and after
        # EP-20B retired the boot fallback there is no other source to name.
        self.store._append({"actor": "owner", "action": "CREATE-INFO",
                            "object": "pack:dual-audit-actions", "rule_cited": "BOOT-INT",
                            "payload": {"kind": "category_pack", "name": "dual-audit-actions"}})
        with self.assertRaises(OpError):                     # must be the Closure Hit, NOT a TypeError
            self.gate.execute("NOPE", "x", {})
        self.assertEqual(len(self.store.by_action("op-refused")), 1)        # the write committed
        self.assertGreaterEqual(len(self.store.by_action("dual-audit-record")), 1)  # audit still ran
        # and it survives reload (the junk record replays; the fold still excludes it)
        s2 = EventStore(self.store.file_path)
        self.assertEqual(len(s2.by_action("op-refused")), 1)

    def test_conformance_lists_only_serviceable_syscalls(self):
        # a pack syscall with no code arg-mapper is not serviceable -> not claimed
        self.store._append(_pack_record("syscall-ops", [
            {"syscall": "open", "op": "FILE-CREATE"}, {"syscall": "ptrace", "op": "SOME-OP"}]))
        conf = self.sp.conformance()
        self.assertIn("open", conf)
        self.assertNotIn("ptrace", conf)
        self.assertEqual(self.sp.syscall("ptrace", "p", {}).get("errno"), "ENOSYS")


class TestNoLawInCode(unittest.TestCase):
    # The S-plane engine (design 28 §10): mechanism only, zero governance content.
    ENGINE = ["kernel/store.py", "kernel/gate.py", "kernel/views.py", "kernel/opdefs.py",
              "kernel/blobs.py"]

    def test_root_law_text_lives_only_in_the_founding_pack(self):
        # EP-14 tightening: the law text lived in a boot.py literal (ROOT_RULES) until now;
        # it now lives ONLY in founding/. The scan therefore covers ALL of src/ outside
        # founding/ — boot.py INCLUDED — and any hit fails.
        texts = [entry[2] for entry in ROOT_RULES]  # (rule_id, polarity, text[, extras])
        self.assertTrue(texts, "no root laws read from the founding pack")
        for rel, src in _src_py_outside_founding():
            for t in texts:
                self.assertNotIn(t, src, f"root-law text leaked into {rel}: {t!r}")

    def test_the_law_text_actually_lives_in_the_founding_pack(self):
        # the positive half: the constitution is not merely absent from code — it is PRESENT
        # as data under founding/. A future founding's diff is a document diff (F4).
        pack_src = _read(os.path.join("founding", "founding-pack.json"))
        for _rid, _pol, text, _extras in ROOT_RULES:
            self.assertIn(text, pack_src, f"root-law text missing from the founding pack: {text!r}")

    def test_relocated_vocabularies_are_read_from_records(self):
        # DOCUMENTED FLIP (EP-20B, R20-1). Both relocated vocabularies still read their policy
        # from the pack; what changed is what stands BEHIND that read. syscall_port.py keeps a
        # LABELED boot fallback (unchanged, and the label is what makes it honest). protection.py
        # keeps NONE: its fallback was unreachable and had drifted from the live pack, so it was
        # retired, and a composition whose record lacks the pack now refuses at boot instead of
        # substituting a code-resident list. No labeled second copy is the stronger state of the
        # same law (I5) — this test asserts the stronger state for protection.py, not the weaker.
        for rel in ["kernel/protection.py", "kernel/syscall_port.py"]:
            self.assertIn("category_packs()", _read(rel), f"{rel} does not read its policy from the pack")
        self.assertIn("FALLBACK", _read("kernel/syscall_port.py"),
                      "kernel/syscall_port.py keeps a policy literal without a fallback label")
        self.assertNotIn("DUAL_AUDIT_ACTIONS = ", _read("kernel/protection.py"),
                         "the retired dual-audit action list is back in kernel/protection.py")

    def test_the_two_permitted_engine_vocabularies_exist(self):
        self.assertIn("OP_CHECKS", _read("kernel/opdefs.py"))            # the check vocabulary
        self.assertIn("VIEW_FILTER_DIMENSIONS", _read("kernel/views.py"))  # the view triggers

    def test_executable_full_form_lives_only_in_the_founding_pack(self):
        # EP-06 (R2): law is in full trigger->outcome form. EP-14 tightening: its `when`
        # triggers and `then` outcomes live ONLY in founding/ (they were boot.py literals until
        # now). The engine reads them GENERICALLY (rule.get("when")/("then"), step.get("refuse"))
        # and hardcodes no law's trigger/outcome. Every root law's when/then STEP, rendered as a
        # "key": "value" literal, must appear in NO src/ file outside founding/ (boot.py included).
        srcs = list(_src_py_outside_founding())
        for entry in ROOT_RULES:
            extras = entry[3] if len(entry) > 3 else {}
            for step in list(extras.get("when") or []) + list(extras.get("then") or []):
                for k, v in step.items():
                    if not isinstance(v, str):
                        continue
                    frag = f'"{k}": "{v}"'
                    for rel, src in srcs:
                        self.assertNotIn(frag, src, f"full-form law literal {frag!r} leaked into {rel}")

    def test_the_law_trigger_vocabulary_is_not_re_declared_in_the_engine(self):
        # the six trigger dimensions are ONE named surface (views.VIEW_FILTER_DIMENSIONS); the gate's
        # full-form pass reuses it and must not carry a second copy (no duplicate governance vocab).
        self.assertNotIn("LAW_TRIGGER_DIMENSIONS", _read("kernel/gate.py"))


if __name__ == "__main__":
    unittest.main()
