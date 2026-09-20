# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: engine-test · OS-architecture
# vocabulary (the kernel's definition as records, its code derived at build, a delete-and-regenerate
# round-trip, a boot-time conformance verdict) as in the seL4/gVisor/Fuchsia literature. NON-GOAL: no
# offensive capability — this proves OUR OWN kernel's definition lives as rows and its act set derives
# from them; it attacks nothing. Full declaration: SCOPE-STATEMENT.md.
"""C7 P3 — OUR OWN KERNEL GENERATED FROM THE RECORD (design/54 §3 B11, §5 L16; §9 Q8; archi :3993).

The twelve KINDS OF WORK the kernel asks its host to perform (bridge/host_seam.py ACT_KINDS, each with
its portability label and meaning) are genesis-seeded as twelve CREATE-RULE rows of law; the seam's act
set is DERIVED from those rows at build by a fold; deleting the built act set and regenerating it from the
record returns the same twelve; and at every waking the running kernel is checked against the rows — by
hash and by declared work — after the two-body check (P6) and before the first actor act, or the first
act is refused.

  A1  DELETE-AND-REGENERATE (the owner's bar, "like the demo").
  A2  the twelve rows, each with its contract; derived == the prior twelve; a divergence CAUGHT (A2 +
      the site-vs-row label check, precision b — the check can fail).
  A3  the waking check + the planted-divergence refusal; recorded before the refusal; ordered after the
      two-body check; the unrecordable case still refuses (Q8b).
  A4  nothing above the seam changes but the derivation; ACT_KINDS not widened; a thirteenth still refused.
  A5  the one-way door held (no device-level commitment / key / ceremony / socket), everything revertable.

Per-module: PYTHONPATH=src:tests python3 -m unittest tests.test_c7_p3_kernel_from_record -v
"""

import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kernel import boot                                          # noqa: E402
from kernel.compose import build_full_kernel                     # noqa: E402
from bridge import host_seam                                     # noqa: E402
from founding import install                                     # noqa: E402

_PACK = os.path.join(os.path.dirname(__file__), "..", "src", "founding", "founding-pack.json")

#: The twelve kinds the code held at HEAD (A2's "derived == the prior twelve"). Pinned here so a drift
#: in either the rows or the code is caught against a fixed reference.
THE_TWELVE = frozenset({
    "record-pen", "atomic-write-once", "remove", "single-writer-lock", "recording-clock",
    "commit-window", "entropy", "concurrency", "network-socket", "body-read",
    "founding-pack-read", "memory",
})

#: The canonical label each kind's row (and each of its sites) must carry (precision b).
EXPECTED_LABELS = {
    "record-pen": "portable-host-primitive", "atomic-write-once": "portable-host-primitive",
    "remove": "portable-host-primitive", "single-writer-lock": "least-portable",
    "recording-clock": "portable-host-primitive", "commit-window": "portable-host-primitive",
    "entropy": "portable-host-primitive", "concurrency": "portable-host-primitive",
    "network-socket": "guest-gated-capability", "body-read": "portable-host-primitive",
    "founding-pack-read": "portable-host-primitive", "memory": "portable-host-primitive",
}


def _fresh():
    """A full governed kernel in a fresh temp world. Returns (store, gate, views, record_path)."""
    td = tempfile.mkdtemp(prefix="c7p3-")
    rp = os.path.join(td, "record.jsonl")
    store, gate, views, _blobs, _subs = build_full_kernel(rp, os.path.join(td, "blobs"))
    return store, gate, views, rp


def _second_image(rp):
    """A second, separate image (a copy of the record recomposed over its own store) — no shared path."""
    td = tempfile.mkdtemp(prefix="c7p3-img2-")
    rp2 = os.path.join(td, "record.jsonl")
    shutil.copyfile(rp, rp2)   # C7 P3b-5c: copy CONTENT only, never file-mode (I7) — copystat is refused on the body
    store, gate, views, _blobs, _subs = build_full_kernel(rp2, os.path.join(td, "blobs"))
    return store, gate, views, rp2


def _load_pack():
    with open(_PACK, encoding="utf-8") as fh:
        return json.load(fh)


# ================================================================================================
# A1 — DELETE-AND-REGENERATE (the owner's bar: "as long as that delete and regen work, like the demo")
# ================================================================================================
class TestA1DeleteAndRegenerate(unittest.TestCase):
    def test_the_built_act_set_deletes_and_regenerates_identical(self):
        store, gate, views, _rp = _fresh()
        built = host_seam.derived_act_kinds()                     # the act set the build derived
        self.assertIsNotNone(built, "the build derived no act set from the rows")
        captured = {k: dict(v) for k, v in built.items()}
        self.assertEqual(len(captured), 12)

        host_seam.clear_derived_act_kinds()                       # DELETE the built act set
        self.assertIsNone(host_seam.derived_act_kinds())

        regen = boot.live_act_kinds(store)                        # REGENERATE from the record (a fold)
        self.assertEqual(regen, captured, "delete-and-regenerate did not return the same set")
        for kind in THE_TWELVE:                                   # each with the SAME contract
            self.assertEqual(regen[kind]["label"], EXPECTED_LABELS[kind])
            self.assertTrue(regen[kind]["meaning"])
        # re-install so a shared module leaves the world's derivation in place for other tests
        host_seam.install_derived_act_kinds(regen)

    def test_the_act_set_is_a_fold_not_a_stored_status(self):
        # L16: never a truth beside the record. Two independent folds of the SAME record agree, and the
        # fold reads the record only — a fresh recompose (a new store over the same file) re-derives it.
        store, gate, views, rp = _fresh()
        again = boot.live_act_kinds(store)
        yet_again = boot.live_act_kinds(store)
        self.assertEqual(again, yet_again)                        # a fold is deterministic
        # a stored status would survive a store that never founded the rows; the fold does not
        empty_store, _g, _v, _rp = None, None, None, None
        from kernel.store import EventStore
        es = EventStore(os.path.join(tempfile.mkdtemp(prefix="c7p3-empty-"), "r.jsonl"),
                        require_rule_cited=True)
        self.assertEqual(boot.live_act_kinds(es), {}, "the act set is a fold of the record, not a cache")


# ================================================================================================
# A2 — THE TWELVE ROWS, EACH WITH ITS CONTRACT; derived == prior; a divergence CAUGHT (precision b)
# ================================================================================================
class TestA2RowsAndContracts(unittest.TestCase):
    def _act_kind_rows(self, pack):
        return [r for s in pack["steps"] for r in s["records"]
                if r.get("action") == "CREATE-RULE"
                and (r.get("payload") or {}).get("kind") == "seam_act_definition"]

    def test_the_twelve_kinds_are_genesis_rows_each_with_its_contract(self):
        pack = _load_pack()
        rows = self._act_kind_rows(pack)
        self.assertEqual(len(rows), 12, "the twelve act kinds are not twelve rows")
        seen = {}
        for r in rows:
            p = r["payload"]
            self.assertEqual(r["action"], "CREATE-RULE")          # rows of LAW, not CREATE-OP (precision a)
            self.assertNotEqual(r["action"], "CREATE-OP")
            self.assertNotIn("definition", p)                     # not an op_definition (the cell untouched)
            self.assertFalse(p.get("root"))                       # not a constitution root law
            for field in ("seam_kind", "label", "meaning", "text"):
                self.assertIn(field, p, "row %r lacks %s" % (p.get("rule_id"), field))
            seen[p["seam_kind"]] = p["label"]
        self.assertEqual(frozenset(seen), THE_TWELVE)             # exactly the twelve
        self.assertEqual(seen, EXPECTED_LABELS)                   # each carries its portability label

    def test_the_rows_are_not_op_definitions_and_not_root_laws(self):
        # precision (a): an act kind is a rule, not an operation; and not a constitution root law.
        self.assertEqual(len(install.op_definitions()), 94, "an act-kind row leaked into the op set")
        pack = _load_pack()
        act_kind_ids = {r["payload"]["rule_id"] for r in self._act_kind_rows(pack)}
        self.assertEqual(len(act_kind_ids), 12)
        root_ids = {rid for rid, *_ in install.root_laws()}
        self.assertEqual(act_kind_ids & root_ids, set(), "an act-kind rule id is a constitution root law")

    def test_the_derived_act_set_equals_the_prior_twelve(self):
        store, _g, _v, _rp = _fresh()
        derived = boot.live_act_kinds(store)
        self.assertEqual(frozenset(derived), THE_TWELVE)          # derived == the frozenset the code held
        self.assertEqual(frozenset(derived), frozenset(host_seam.ACT_KINDS))
        self.assertEqual({k: derived[k]["label"] for k in derived}, EXPECTED_LABELS)

    def test_thirty_sites_twelve_kinds_uniform_labels(self):
        # precision (b): 30 declare_act sites, 12 kinds; every site's label is its kind's canonical label.
        acts = host_seam.HostSeam.ACTS
        self.assertEqual(len(acts), 30)
        kinds = {kind for _m, (kind, _l) in acts.items()}
        self.assertEqual(kinds, THE_TWELVE)
        for _method, (kind, label) in acts.items():
            self.assertEqual(label, EXPECTED_LABELS[kind])

    def test_a_kind_absent_from_the_rows_is_caught(self):
        # A2: a kind in the code path absent from the rows (or the reverse) is CAUGHT — the check can fail.
        store, _g, _v, _rp = _fresh()
        derived = boot.live_act_kinds(store)
        short = dict(derived); short.pop("memory")                # a kind in the code absent from the rows
        with self.assertRaises(host_seam.HostSeamError):
            host_seam.reconcile_derived_act_kinds(short)
        extra = dict(derived); extra["thirteenth"] = {"label": "portable-host-primitive", "meaning": "x"}
        with self.assertRaises(host_seam.HostSeamError):          # a kind in the rows absent from the code
            host_seam.reconcile_derived_act_kinds(extra)

    def test_a_disagreeing_site_label_is_caught(self):
        # precision (b): a row whose label disagrees with its kind's site is CAUGHT (the check can fail).
        store, _g, _v, _rp = _fresh()
        derived = boot.live_act_kinds(store)
        wrong = copy.deepcopy(derived)
        wrong["entropy"]["label"] = "least-portable"              # entropy's sites declare portable
        with self.assertRaises(host_seam.HostSeamError):
            host_seam.reconcile_derived_act_kinds(wrong)

    def test_a_tampered_row_reds_the_build_reconcile(self):
        # A world founded from a pack whose act-kind row carries a wrong label cannot build — the build
        # reconcile (A2 + precision b) refuses it. Proven against a tampered pack copy.
        pack = copy.deepcopy(_load_pack())
        for s in pack["steps"]:
            for r in s["records"]:
                p = r.get("payload") or {}
                if p.get("kind") == "seam_act_definition" and p.get("seam_kind") == "remove":
                    p["label"] = "least-portable"                 # a plausible-but-wrong label
        saved = install.load_pack
        td = tempfile.mkdtemp(prefix="c7p3-tamper-")
        try:
            install.load_pack = lambda path=None: pack
            from kernel.boot import build_kernel
            with self.assertRaises(host_seam.HostSeamError):
                build_kernel(os.path.join(td, "r.jsonl"))
        finally:
            install.load_pack = saved


# ================================================================================================
# A3 — THE RUNNING KERNEL CHECKED AGAINST THE ROWS AT EVERY WAKING, OR THE FIRST ACT REFUSED (Q8)
# ================================================================================================
def _conformance_row(store):
    rows = [e for e in store.by_action("WRITE-ACTIVITY")
            if e.get("object") == boot.KERNEL_CONFORMANCE_OBJECT]
    return rows[-1] if rows else None


class TestA3WakingCheck(unittest.TestCase):
    def test_a_healthy_kernel_passes_and_records_the_verdict(self):
        store, gate, views, _rp = _fresh()
        before = _conformance_row(store)
        v = boot.check_kernel_against_rows(store, gate)
        self.assertTrue(v["ok"])
        self.assertEqual(v["rows_digest"], v["running_digest"])   # by hash: the rows == the running kernel
        row = _conformance_row(store)                             # recorded as a genesis row (the one pen)
        self.assertIsNotNone(row)
        self.assertIsNot(row, before)
        self.assertTrue(row["payload"]["ok"])
        self.assertEqual(row["payload"]["kind"], "kernel-conformance")

    def test_after_the_two_body_check_then_conformance_then_the_first_act(self):
        # THE ORDERING (Q8): wake (P4) -> two-body (P6) -> conformance (P3) -> the first actor act.
        sa, ga, va, rpa = _fresh()
        sb, gb, vb, rpb = _second_image(rpa)
        boot.wake(sa, ga, va)                                     # P4: the six verdicts pass
        receipt = boot.genesis_pair_wake(boot.WitnessBody("chip", sa, va),
                                         boot.WitnessBody("disk", sb, vb), ga)   # P6: two bodies agree
        self.assertTrue(receipt["agree"])
        v = boot.check_kernel_against_rows(sa, ga)                # P3: the conformance verdict, AFTER P6
        self.assertTrue(v["ok"], "the running kernel diverged from its rows on a healthy world")

    def test_a_planted_declared_set_refuses_the_first_act(self):
        # a planted kernel whose DECLARED closed set carries a kind not in the rows refuses (BY DECLARED
        # WORK). Recorded before the refusal (the divergence is a fact of the record).
        store, gate, views, _rp = _fresh()
        saved = host_seam.ACT_KINDS
        try:
            host_seam.ACT_KINDS = frozenset(set(saved) | {"planted-kind"})
            with self.assertRaises(boot.KernelConformanceRefused) as ctx:
                boot.check_kernel_against_rows(store, gate)
            self.assertIn("planted-kind", str(ctx.exception))
        finally:
            host_seam.ACT_KINDS = saved
        row = _conformance_row(store)
        self.assertIsNotNone(row)
        self.assertFalse(row["payload"]["ok"])                   # recorded as refused

    def test_a_planted_site_kind_refuses_the_first_act(self):
        store, gate, views, _rp = _fresh()
        saved = host_seam.HostSeam.ACTS
        try:
            host_seam.HostSeam.ACTS = dict(saved, planted=("planted-kind", "portable-host-primitive"))
            with self.assertRaises(boot.KernelConformanceRefused):
                boot.check_kernel_against_rows(store, gate)
        finally:
            host_seam.HostSeam.ACTS = saved

    def test_a_planted_site_label_reds_the_hash(self):
        # BY HASH: a planted label the running kernel declares differently from its row reds the check.
        store, gate, views, _rp = _fresh()
        saved = host_seam.HostSeam.ACTS
        try:
            host_seam.HostSeam.ACTS = dict(saved, urandom=("entropy", "least-portable"))
            with self.assertRaises(boot.KernelConformanceRefused) as ctx:
                boot.check_kernel_against_rows(store, gate)
            self.assertIn("hash mismatch", str(ctx.exception))
        finally:
            host_seam.HostSeam.ACTS = saved

    def test_the_check_can_pass_and_can_fail(self):
        # a verdict that cannot fail is not a verdict — one pass and one fail on the same world.
        store, gate, views, _rp = _fresh()
        self.assertTrue(boot.kernel_conformance_verdict(store)[0])
        saved = host_seam.ACT_KINDS
        try:
            host_seam.ACT_KINDS = frozenset(set(saved) | {"x"})
            self.assertFalse(boot.kernel_conformance_verdict(store)[0])
        finally:
            host_seam.ACT_KINDS = saved

    def test_the_unrecordable_genesis_row_still_refuses(self):
        # Q8b: a world whose genesis row cannot be appended STILL refuses the first act, the failure
        # carried. Simulated with a gate whose WRITE-ACTIVITY raises, and a planted divergence.
        store, gate, views, _rp = _fresh()

        class _UnrecordableGate:
            def execute(self, *a, **k):
                raise RuntimeError("the record cannot fold — the genesis row is unrecordable")

        saved = host_seam.ACT_KINDS
        try:
            host_seam.ACT_KINDS = frozenset(set(saved) | {"planted-kind"})
            with self.assertRaises(boot.KernelConformanceRefused):
                boot.check_kernel_against_rows(store, _UnrecordableGate())
        finally:
            host_seam.ACT_KINDS = saved


# ================================================================================================
# A4 — NOTHING ABOVE THE SEAM CHANGES BUT THE DERIVATION; ACT_KINDS NOT WIDENED; the pins hold
# ================================================================================================
class TestA4NoWiden(unittest.TestCase):
    def test_act_kinds_is_the_same_twelve_not_widened(self):
        self.assertEqual(len(host_seam.ACT_KINDS), 12)
        self.assertEqual(frozenset(host_seam.ACT_KINDS), THE_TWELVE)

    def test_declare_act_still_refuses_a_thirteenth_store_free(self):
        # the closed-set gate is unchanged in behaviour — a thirteenth kind is refused with NO store.
        with self.assertRaises(host_seam.HostSeamError):
            host_seam.declare_act("thirteenth-kind", host_seam.PORTABLE)
        with self.assertRaises(host_seam.HostSeamError):
            host_seam.declare_act("entropy", "not-a-label")       # the label gate is unchanged too

    def test_the_derived_set_is_exactly_twelve_no_widen(self):
        store, _g, _v, _rp = _fresh()
        self.assertEqual(len(boot.live_act_kinds(store)), 12)


# ================================================================================================
# A5 — THE ONE-WAY DOOR HELD, EVERYTHING REVERTABLE
# ================================================================================================
class TestA5OneWayDoorHeld(unittest.TestCase):
    def test_the_act_kind_rows_carry_no_device_commit_key_or_ceremony(self):
        # the rows are pure DEFINITIONS (name + label + meaning); no device-level commitment, no key
        # bind, no ceremony is seeded by this unit (A5; design/54 §6, I6).
        pack = _load_pack()
        for s in pack["steps"]:
            if s["step"] != "13-act-kind-definitions":
                continue
            blob = json.dumps(s).lower()
            for banned in ("private_key", "ceremony", "bare-metal", "bind-device", "public release"):
                self.assertNotIn(banned, blob, "an act-kind row smuggled a one-way-door artifact")

    def test_the_derivation_is_performer_independent(self):
        # the derivation reads the RECORD and the seam's own declaration — it performs no host act, so it
        # commits our core to no device. It runs under a stub performer (no real disk / socket / clock).
        store, _g, _v, _rp = _fresh()
        with host_seam.using(host_seam.StubHost()):
            derived = boot.live_act_kinds(store)                  # a pure record fold, no host act
            host_seam.reconcile_derived_act_kinds(derived)        # reads only the seam declaration
        self.assertEqual(frozenset(derived), THE_TWELVE)

    def test_the_guest_gated_socket_stays_gated_not_performed(self):
        # network-socket is still declared GUEST_GATED and is not stood as a production performer here.
        self.assertEqual(EXPECTED_LABELS["network-socket"], "guest-gated-capability")
        self.assertIn("network-socket", host_seam.ACT_KINDS)

    def test_the_founding_moved_exactly_one_minor(self):
        self.assertEqual(install.founding_version(), "1.55.0")


if __name__ == "__main__":
    unittest.main()
