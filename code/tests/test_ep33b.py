# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-33B — the campaign-close REVIEW's own red worlds, committed to the suite so the
evidence outlives the session (A5). THE REVIEW GRADES; IT DOES NOT FIX. Two of the four
classes below are POSITIVE (a property driven able to fail, then shown holding); one PINS
a raised FINDING so a later fix flips it and forces a re-read (the estate's
`test_a_whole_record_guard_is_green_on_this_defect` pattern); one mechanises the
assumption-outside guard (R3) so the no-findings bar has a control.

Every probe here is the reviewer's own — not the paper author's (charter §5 cap 1). Each
runs the estate's OWN gate/views and reads their designed behaviour; nothing crafts an
input against the source (governance-work-method: validate by reading/running the guards).
"""
import os
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from collections.abc import Mapping                        # noqa: E402
from kernel.boot import build_kernel                      # noqa: E402
from kernel.blobs import BlobStore                         # noqa: E402
from kernel.errors import OpError                          # noqa: E402
from kernel.store import StaleIndex                        # noqa: E402
from subsystems.memory import MemoryView                   # noqa: E402
from subsystems.scheduling import SchedulingView           # noqa: E402
from subsystems.files import FilesView                     # noqa: E402
from subsystems.comms import CommsView                     # noqa: E402
from subsystems.devices import DevicesView                 # noqa: E402
from bridge.custody import formal_name                     # noqa: E402

MOTHER = "space:root"


class _World(unittest.TestCase):
    """A booted kernel over a fresh, disposable record. tearDown deletes it, so every
    narrowing below lives only inside a throwaway world — the live openness grant is never
    touched (T-OPENNESS-UNTOUCHED owns that, in test_ep25)."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep33b-")
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views = build_kernel(self.record)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def narrow_to_zero(self):
        """Revoke the founding openness grant IN THIS THROWAWAY WORLD so the authority
        columns are evaluated against real grants, not against openness."""
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        self.assertNotIn("grant:founding-openness", self.views.grants())


# =====================================================================================
# A2 / R1 — T-CUSTODY-MATRIX at OS scale, ACROSS EVERY ASSUMED SUBSYSTEM
# The files seed (test_ep25 TestCustodyMatrix) proved the four columns over a file act and
# deferred "the full matrix at OS scale" to EP-33. This drives it over a real MEMORY act and
# a real SCHEDULING act too, proving K6: no subsystem acquires its own authority path — the
# ONE gate carries the four-dimension grant law for all of them.
# =====================================================================================
class TestCustodyMatrixAcrossSubsystems(_World):

    #: (subsystem, op, params-builder). Each op is a real custody DECISION that crosses the
    #: ONE gate. `actor` is filled in per column.
    OPS = {
        "file":       ("FILE-OPEN",   lambda a: {"path": "/m.txt", "inode": 7,
                       "provenance": {"asserted_by": a, "source": "fuse-port",
                                      "could_read": [], "uid": 4242}}),
        "memory":     ("MEM-GRANT",   lambda a: {"region": "r1", "size": 10, "holder": a}),
        "scheduling": ("SCHED-ADMIT", lambda a: {"proc": "p1"}),
    }

    def _four_columns(self, subsystem):
        op, mk = self.OPS[subsystem]
        self.narrow_to_zero()

        # column 1 — NO ACCOUNT: nothing founds this actor, no chain reaches it.
        with self.assertRaises(OpError) as c1:
            self.gate.execute(op, "nobody", mk("nobody"))
        self.assertEqual(c1.exception.rule, "ROOT-NEG-1", "%s col1" % subsystem)

        # column 2 — ACCOUNT, NO GRANT.
        self.gate.execute("CREATE-ACCOUNT", "owner",
                          {"account_id": "ann", "actor_class": "human"})
        with self.assertRaises(OpError) as c2:
            self.gate.execute(op, "ann", mk("ann"))
        self.assertEqual(c2.exception.rule, "ROOT-NEG-1", "%s col2" % subsystem)

        # column 3 — GRANT IN THE WRONG SPACE.
        self.gate.execute("CREATE-SPACE", "owner", {"name": "elsewhere", "parent": MOTHER})
        self.gate.execute("GRANT", "owner", {"grant_id": "g-wrong", "grantee": "ann",
                          "actions": [op], "info": "*", "space": "space:elsewhere"})
        with self.assertRaises(OpError) as c3:
            self.gate.execute(op, "ann", mk("ann"))
        self.assertEqual(c3.exception.rule, "ROOT-NEG-3", "%s col3" % subsystem)

        # column 4 — A COVERING GRANT: the act passes.
        self.gate.execute("GRANT", "owner", {"grant_id": "g-ok", "grantee": "ann",
                          "actions": [op, "AMEND-BUDGET"], "info": "*", "space": MOTHER})
        rec = self.gate.execute(op, "ann", mk("ann"))
        self.assertEqual(rec["actor"], "ann", "%s col4 served" % subsystem)
        self.assertEqual(rec["action"], op)

    def test_the_four_columns_over_a_file_act(self):
        self._four_columns("file")

    def test_the_four_columns_over_a_memory_act(self):
        self._four_columns("memory")

    def test_the_four_columns_over_a_scheduling_act(self):
        self._four_columns("scheduling")

    def test_every_column_can_fail_a_covering_grant_one_dimension_short_still_refuses(self):
        """R1 / the coverage-sweep law: the PASS column (col4) is proven able to fail. A grant
        covering the op but not in the space asked about refuses — so col4's green is a check
        that could have failed, not a column that passes everything."""
        for subsystem, (op, mk) in sorted(self.OPS.items()):
            with self.subTest(subsystem=subsystem):
                self.setUp()  # fresh world per subsystem
                try:
                    self.narrow_to_zero()
                    self.gate.execute("CREATE-ACCOUNT", "owner",
                                      {"account_id": "bob", "actor_class": "human"})
                    self.gate.execute("CREATE-SPACE", "owner",
                                      {"name": "other", "parent": MOTHER})
                    # a grant that covers the action but ONLY in a space the act is not in
                    self.gate.execute("GRANT", "owner", {"grant_id": "g-elsewhere",
                                      "grantee": "bob", "actions": [op], "info": "*",
                                      "space": "space:other"})
                    with self.assertRaises(OpError) as e:
                        self.gate.execute(op, "bob", mk("bob"))
                    self.assertEqual(e.exception.rule, "ROOT-NEG-3")
                finally:
                    self.tearDown()

    def test_the_protected_core_actor_keeps_authority_after_the_narrow(self):
        """The control that keeps the matrix honest: narrowing to zero must not disarm SYSTEM,
        or the columns above would be measuring a dead world rather than a governed one."""
        self.narrow_to_zero()
        for subsystem, (op, mk) in sorted(self.OPS.items()):
            with self.subTest(subsystem=subsystem):
                rec = self.gate.execute(op, "SYSTEM", mk("SYSTEM"))
                self.assertEqual(rec["actor"], "SYSTEM")


# =====================================================================================
# A3 / R2 — T-TOTAL-ROUNDTRIP-3, the WHOLE world: kill everything derived, replay from
# the record alone, identical answers across governance + memory + scheduling.
# =====================================================================================
class TestWholeWorldRoundtrip(_World):

    def _build_world(self):
        g = self.gate
        g.execute("CREATE-ACCOUNT", "owner", {"account_id": "ann", "actor_class": "human"})
        g.execute("GRANT", "owner", {"grant_id": "g1", "grantee": "ann",
                  "actions": ["MEM-GRANT", "AMEND-BUDGET", "SCHED-ADMIT"],
                  "info": "*", "space": MOTHER})
        g.execute("AMEND-BUDGET", "SYSTEM", {"holder": "ann", "ceiling": 1000})
        g.execute("MEM-GRANT", "ann", {"region": "r1", "size": 100, "holder": "ann"})
        g.execute("MEM-GRANT", "ann", {"region": "r2", "size": 200, "holder": "ann"})
        g.execute("SCHED-ADMIT", "ann", {"proc": "p1"})
        g.execute("SCHED-ADMIT", "ann", {"proc": "p2"})

    @staticmethod
    def _answers(store, views):
        return {
            "grants": sorted(views.grants()),
            "mem_resident_ann": MemoryView(store).resident_size("ann"),
            "sched_runnable": sorted(SchedulingView(store).runnable()),
            "n_events": len(store.all()),
        }

    def test_kill_every_derived_thing_replay_from_the_record_alone_is_identical(self):
        self._build_world()
        live = self._answers(self.store, self.views)
        # a completely fresh kernel + fresh views, given ONLY the record file
        store2, _gate2, views2 = build_kernel(self.record)
        replay = self._answers(store2, views2)
        self.assertEqual(live, replay,
                         "the replayed world differs from the live one — some answer was "
                         "carried in derived state rather than derived from the record")

    def test_the_roundtrip_reds_on_a_withheld_derivation_then_greens_when_restored(self):
        """R2: withhold ONE recorded decision from the replay and the rebuilt world must
        differ; restore it and it is identical again. A roundtrip that stayed identical with a
        record missing would be reading its answer from somewhere other than the record."""
        self._build_world()
        full = self._answers(self.store, self.views)

        with open(self.record, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        missing = os.path.join(self.dir, "record_missing.jsonl")
        with open(missing, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines[:-1]) + "\n")     # drop the last decision (SCHED-ADMIT p2)
        s_miss, _g, v_miss = build_kernel(missing)
        self.assertNotEqual(self._answers(s_miss, v_miss)["sched_runnable"],
                            full["sched_runnable"],
                            "a record missing a decision replayed to the SAME answer")

        restored = os.path.join(self.dir, "record_restored.jsonl")
        with open(restored, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        s_ok, _g2, v_ok = build_kernel(restored)
        self.assertEqual(self._answers(s_ok, v_ok)["sched_runnable"], full["sched_runnable"])


# =====================================================================================
# A1 / K12 — THE FINDING, CLOSED (MAINT-K12-FAMILY-INDEX, resolving EP-33B Finding 2).
# K12 (design/36 ADDENDUM S): "a derived answer costs its own dependencies ... not the whole
# record." The files custody subsystem satisfied it first (a per-family index). ADDENDUM S §S.1
# binds K12 to "every remaining subsystem ... EP-31's memory, EP-32's scheduling", each authoring
# naming how its read paths satisfy it. The memory and scheduling derived views USED to iterate
# the whole event stream on every call; they now read their family's records through the existing
# RecordProjection mechanism (subsystems.memory.MemoryProjection / subsystems.scheduling.
# SchedulingProjection), so a fixed answer costs only its family's records. This class DROVE the
# raised finding; the fix FLIPS it — the assertions below now prove the bound holds. Per EP-24B's
# owner-ruled standard (EP-25 W0) the property is asserted as a COUNTABLE — the records the fold
# iterates — never as a duration, and each bound has a same-family control that makes it fail.
# =====================================================================================
class TestK12CrossSubsystemReadCostClosed(_World):

    def _fold_reads(self, make_view, read, n_unrelated=0, family_extra=()):
        """Build a seeded world, append `family_extra` records that DO belong to the read's
        family and `n_unrelated` records its answer does NOT depend on, then return (records the
        fold iterates, answer). The count is `len(view._records.all())` — the family-keyed
        projection's own contents, i.e. exactly the records the fold walks (the EP-24B countable,
        `len(index.all())`), with the whole-record refresh excluded as amortized maintenance."""
        self.setUp()
        try:
            self._seed()
            for op, actor, params in family_extra:
                self.gate.execute(op, actor, params)
            for i in range(n_unrelated):
                self.gate.execute("CREATE-INFO", "SYSTEM", {"object": "i:%d" % i, "content": "x"})
            view = make_view(self.store)
            answer = read(view)
            return len(view._records.all()), answer
        finally:
            self.tearDown()

    def _seed(self):
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "web", "ceiling": 10 ** 9})
        self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 10, "holder": "web"})
        self.gate.execute("SCHED-ADMIT", "SYSTEM", {"proc": "p1"})
        self.gate.execute("SCHED-ADMIT", "SYSTEM", {"proc": "p2"})

    # ---- scheduling: runnable() costs its family, not the stream ----
    def test_scheduling_runnable_reads_only_its_family_not_unrelated_records(self):
        mk = lambda s: SchedulingView(s)                                     # noqa: E731
        rd = lambda v: sorted(v.runnable())                                  # noqa: E731
        base_reads, base_ans = self._fold_reads(mk, rd, n_unrelated=0)
        grown_reads, grown_ans = self._fold_reads(mk, rd, n_unrelated=5000)
        self.assertEqual(base_ans, grown_ans,
                         "the arms answered different questions — cannot attribute cost")
        self.assertEqual(base_ans, ["p1", "p2"])
        # THE FIX: identical answer, and the fold reads the SAME number of records — 5000
        # unrelated records did not move its cost. K12 met.
        self.assertEqual(grown_reads, base_reads,
                         "runnable() read more records after 5000 unrelated ones were added — "
                         "the K12 family bound is not holding; re-read design/36 ADDENDUM S")

    def test_scheduling_runnable_reads_grow_with_its_OWN_family(self):
        """The control that makes the bound above meaningful: adding SCHEDULING-family records
        DOES move what the fold reads, so its family bound is a check that can fail."""
        mk = lambda s: SchedulingView(s)                                     # noqa: E731
        rd = lambda v: v.runnable()                                          # noqa: E731
        base_reads, _ = self._fold_reads(mk, rd)
        extra = [("SCHED-ADMIT", "SYSTEM", {"proc": "q%d" % i}) for i in range(50)]
        grown_reads, _ = self._fold_reads(mk, rd, family_extra=extra)
        self.assertEqual(grown_reads, base_reads + 50,
                         "scheduling-family growth did not move what runnable() reads — the "
                         "projection is not actually selecting the family")

    # ---- memory: resident_size() costs its family, not the stream ----
    def test_memory_resident_size_reads_only_its_family_not_unrelated_records(self):
        mk = lambda s: MemoryView(s)                                         # noqa: E731
        rd = lambda v: v.resident_size("web")                               # noqa: E731
        base_reads, base_ans = self._fold_reads(mk, rd, n_unrelated=0)
        grown_reads, grown_ans = self._fold_reads(mk, rd, n_unrelated=5000)
        self.assertEqual(base_ans, grown_ans)
        self.assertEqual(base_ans, 10)
        self.assertEqual(grown_reads, base_reads,
                         "resident_size() read more records after 5000 unrelated ones were "
                         "added — the K12 family bound is not holding; re-read ADDENDUM S")

    def test_memory_resident_size_reads_grow_with_its_OWN_family(self):
        """The same-family control for memory: MEMORY-family growth DOES move what the fold
        reads, so the family bound is a check that can fail."""
        mk = lambda s: MemoryView(s)                                         # noqa: E731
        rd = lambda v: v.resident_size("web")                               # noqa: E731
        base_reads, _ = self._fold_reads(mk, rd)
        extra = [("MEM-GRANT", "web", {"region": "x%d" % i, "size": 1, "holder": "web"})
                 for i in range(50)]
        grown_reads, _ = self._fold_reads(mk, rd, family_extra=extra)
        self.assertEqual(grown_reads, base_reads + 50,
                         "memory-family growth did not move what resident_size() reads — the "
                         "projection is not actually selecting the family")


# =====================================================================================
# MAINT-K12-CEILING-FOLD (archi board :2727, A2) — the ceiling check's WHOLE-STORE fold moved
# to its config-keyed family. This differential holds the change to ONE variable, the iteration
# SOURCE (store.all() -> the held {aggregate_action, removal_action} projection): the fold body
# is byte-identical, so the OLD whole-store fold and the NEW family fold must agree on every
# interleave world, and the two docstring hazards — ordered OVERWRITE and holder-UNFILTERED
# removal — must survive the move. `_old_fold` below is the pre-change body, verbatim, run as the
# oracle over store.all(); the new source is store.action_set_projection(...).all(). Nothing here
# crafts an input against the source: it drives the estate's own gate and reads its designed
# behaviour (governance-work-method: validate by reading / running the guards).
# =====================================================================================
class TestK12CeilingFoldFamilySource(_World):

    # The MEM-GRANT ceiling row, mirrored from founding-pack.json (steps[14]/records[4]/payload/
    # definition/checks[0]). Stated here so the test is an INDEPENDENT oracle rather than reading
    # the config back through the code under test.
    C = {"policy_key_prefix": "budget:", "holder_param": "holder", "aggregate_action": "MEM-GRANT",
         "holder_field": "holder", "key_param": "region", "aggregate_field": "size",
         "removal_action": "MEM-EVICT", "amount_param": "size", "cite": "MEM-LAW-BUDGET"}

    @staticmethod
    def _old_fold(records, holder, c):
        """The pre-change `_ceiling_check` body, VERBATIM, as the differential oracle. Returns
        (used, agg) so a divergence names the region as well as the total."""
        agg = {}
        for e in records:
            a, pp = e["action"], (e.get("payload") or {})
            if a == c["aggregate_action"] and pp.get(c["holder_field"]) == holder:
                agg[pp.get(c["key_param"])] = pp.get(c["aggregate_field"], 0)
            elif a == c["removal_action"]:
                agg.pop(pp.get(c["key_param"]), None)
        return sum(agg.values()), dict(agg)

    def _family(self):
        return self.store.action_set_projection(
            {self.C["aggregate_action"], self.C["removal_action"]})

    def _assert_sources_agree(self, holder, msg):
        """The heart of A2: OLD whole-store fold == NEW family fold, used AND agg."""
        whole = self._old_fold(self.store.all(), holder, self.C)
        fam = self._old_fold(self._family().all(), holder, self.C)
        self.assertEqual(whole, fam, msg + " — the family source diverged from the whole-store fold")
        return whole

    def _grant(self, actor, region, size, holder):
        try:
            self.gate.execute("MEM-GRANT", actor, {"region": region, "size": size, "holder": holder})
            return "ALLOW"
        except OpError as e:
            if e.rule == "MEM-LAW-BUDGET":
                return "REFUSE"
            raise

    # ---- interleave world: sources agree, unrelated records do not move the answer ----
    def test_source_differential_over_grant_evict_regrant_and_unrelated(self):
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "web", "ceiling": 500})
        self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 100, "holder": "web"})
        self.gate.execute("CREATE-INFO", "SYSTEM", {"object": "i:0", "content": "x"})   # unrelated
        self.gate.execute("MEM-GRANT", "web", {"region": "r2", "size": 50, "holder": "web"})
        self.gate.execute("MEM-EVICT", "web", {"region": "r1"})
        self.gate.execute("CREATE-INFO", "SYSTEM", {"object": "i:1", "content": "y"})   # unrelated
        self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 30, "holder": "web"})  # re-grant
        used, agg = self._assert_sources_agree("web", "grant/evict/re-grant + unrelated")
        self.assertEqual(used, 80)                      # r1=30 (re-granted) + r2=50
        self.assertEqual(agg, {"r1": 30, "r2": 50})

    # ---- HAZARD 1: ordered OVERWRITE survives (a re-grant-LARGER world) ----
    def test_hazard_ordered_overwrite_regrant_larger_survives(self):
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "web", "ceiling": 100})
        self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 40, "holder": "web"})
        self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 60, "holder": "web"})  # OVERWRITE larger
        used, agg = self._assert_sources_agree("web", "ordered overwrite (re-grant larger)")
        # overwrite, not additive: r1 is 60 (the LATER size), not 40 (kept-first) and not 100
        # (40+60 double-count). A set-based 'granted minus evicted' port regresses to one of
        # those; the ordered keyed fold gives the identical correct total old and new.
        self.assertEqual((used, agg), (60, {"r1": 60}))
        # the live gate (new fold) uses that 60: r2=41 tips it to 101 and is refused. If the fold
        # had wrongly kept r1=40, 40+41=81 would have fit — so the REFUSE proves the overwrite.
        self.assertEqual(self._grant("web", "r2", 41, "web"), "REFUSE")

    def test_hazard_ordered_overwrite_regrant_smaller_frees_room(self):
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "web", "ceiling": 100})
        self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 60, "holder": "web"})
        self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 40, "holder": "web"})  # OVERWRITE smaller
        used, _ = self._assert_sources_agree("web", "ordered overwrite (re-grant smaller)")
        self.assertEqual(used, 40)                                       # not additive 100
        self.assertEqual(self._grant("web", "r2", 60, "web"), "ALLOW")   # 40+60==100, fits iff overwrite

    # ---- HAZARD 2: holder-UNFILTERED removal survives (evict by ANOTHER holder frees budget) ----
    def test_hazard_holder_unfiltered_removal_cross_holder_evict_frees_budget(self):
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "web", "ceiling": 100})
        self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 100, "holder": "web"})
        self.assertEqual(self._assert_sources_agree("web", "before cross-holder evict")[0], 100)
        # a MEM-EVICT carries NO holder (payload_from is [region] only); a DIFFERENT actor names
        # r1, and the removal frees it UNFILTERED by holder. A holder-filtered port would leave
        # web's 100 resident and silently stop the eviction freeing budget.
        self.gate.execute("MEM-EVICT", "db", {"region": "r1"})
        self.assertEqual(self._assert_sources_agree("web", "after cross-holder evict")[0], 0)
        self.assertEqual(self._grant("web", "r2", 100, "web"), "ALLOW")  # freed -> fits again

    # ---- the live gate decision (new fold) tracks the oracle (old fold) across a mixed script ----
    def test_gate_allow_refuse_tracks_the_old_fold_oracle(self):
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "web", "ceiling": 100})
        seen = set()
        for region, size in [("r1", 60), ("r2", 60), ("r3", 20), ("r3", 50)]:
            used_before, _ = self._old_fold(self.store.all(), "web", self.C)
            predict = "REFUSE" if used_before + size > 100 else "ALLOW"
            got = self._grant("web", region, size, "web")
            seen.add(got)
            self.assertEqual(got, predict,
                             "gate decision diverged from the old-fold oracle at %s=%d" % (region, size))
        self.assertEqual(seen, {"ALLOW", "REFUSE"}, "the script exercised only one branch")

    # ---- COST: the ceiling family read is bounded to its family, not the stream ----
    def _ceiling_reads(self, n_unrelated=0, family_extra=()):
        self.setUp()
        try:
            self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "web", "ceiling": 10 ** 9})
            self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 10, "holder": "web"})
            self.gate.execute("MEM-EVICT", "web", {"region": "r1"})
            for region, size in family_extra:
                self.gate.execute("MEM-GRANT", "web", {"region": region, "size": size, "holder": "web"})
            for i in range(n_unrelated):
                self.gate.execute("CREATE-INFO", "SYSTEM", {"object": "u:%d" % i, "content": "x"})
            fam = self.store.action_set_projection({"MEM-GRANT", "MEM-EVICT"})
            return len(fam.all())
        finally:
            self.tearDown()

    def test_ceiling_family_reads_only_its_family_not_unrelated_records(self):
        base = self._ceiling_reads(n_unrelated=0)
        grown = self._ceiling_reads(n_unrelated=5000)
        self.assertEqual(base, 2, "seed is 1 grant + 1 evict = 2 family records")
        self.assertEqual(grown, base,
                         "the ceiling fold read more records after 5000 unrelated ones were added "
                         "— the K12 family bound is not holding; re-read design/36 ADDENDUM S")

    def test_ceiling_family_reads_grow_with_its_OWN_family(self):
        """The same-family control that makes the bound above a check that can fail: adding
        MEMORY-family records DOES move what the ceiling fold reads."""
        base = self._ceiling_reads()
        grown = self._ceiling_reads(family_extra=[("x%d" % i, 1) for i in range(50)])
        self.assertEqual(grown, base + 50,
                         "memory-family growth did not move what the ceiling fold reads — the "
                         "config-keyed projection is not actually selecting the family")

    # ---- kill the held cache and replay from the record alone: identical ----
    def test_kill_the_ceiling_cache_and_replay_are_identical(self):
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "web", "ceiling": 100})
        self.gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 40, "holder": "web"})
        self.gate.execute("MEM-EVICT", "web", {"region": "r1"})
        self.gate.execute("MEM-GRANT", "web", {"region": "r2", "size": 70, "holder": "web"})
        live = self._old_fold(self._family().all(), "web", self.C)
        self._family().kill()                                # (a) kill the held projection
        killed = self._old_fold(self._family().all(), "web", self.C)
        self.assertEqual(live, killed, "killing the held cache changed the ceiling answer")
        store2, _g2, _v2 = build_kernel(self.record)         # (b) fresh kernel, same record file
        fam2 = store2.action_set_projection({"MEM-GRANT", "MEM-EVICT"})
        replay = self._old_fold(fam2.all(), "web", self.C)
        self.assertEqual(live, replay, "a fresh kernel over the record replayed a different answer")

    # ---- the parameterization is a subclass, not a growth of the EP-24B six-name surface ----
    def test_the_config_keyed_projection_grew_no_public_surface(self):
        proj = self.store.action_set_projection({"MEM-GRANT", "MEM-EVICT"})
        public = {n for n in dir(proj) if not n.startswith("_")}
        self.assertEqual(public, {"all", "by_action", "catchups", "is_current", "kill", "refresh"},
                         "the config-keyed projection grew a surface beyond selecting records")

    def test_an_empty_action_set_refuses_rather_than_serving_nothing(self):
        from kernel.store import StaleIndex
        with self.assertRaises(StaleIndex):
            self.store.action_set_projection(set())


# =====================================================================================
# R3 — THE ASSUMPTION-OUTSIDE GUARD (item 31): the no-findings bar's own control.
# A7 grades whether the campaign's claims survive WITHOUT their vocabulary/premises. R3
# requires the method to CATCH a planted claim that does not. Mechanised: a claim survives
# only if its support is machine evidence that holds regardless of vocabulary; a claim whose
# only support is a citation into the canon is flagged. A planted citation-only claim must be
# caught, or the assumption-outside leg cannot be trusted to have any teeth.
# =====================================================================================
class TestAssumptionOutsideGuard(unittest.TestCase):

    @staticmethod
    def _survives_without_vocabulary(claim):
        """A claim survives iff it is backed by evidence a reader who grants NO premises can
        reproduce — a command, a measurement, an external surface (POSIX, git, a power cut).
        Support that is only a pointer into the canon does not survive: 'it holds because the
        design doc says so' is exactly what the assumption-outside reader refuses."""
        support = claim.get("support", "")
        machine_kinds = ("command", "measurement", "external-surface", "roundtrip")
        return claim.get("support_kind") in machine_kinds and bool(support)

    def test_a_claim_backed_by_machine_evidence_survives(self):
        good = {"claim": "kill the derived state, replay the record, the world is identical",
                "support_kind": "roundtrip",
                "support": "test_ep33b.TestWholeWorldRoundtrip green"}
        self.assertTrue(self._survives_without_vocabulary(good))

    def test_a_planted_citation_only_claim_is_caught(self):
        """R3, the plant. A claim whose only support is a reference into the design canon —
        no command, no measurement — is flagged as NOT surviving. If this ever passes silently,
        the assumption-outside leg has stopped being able to fail."""
        planted = {"claim": "the campaign's group-commit lever delivers the 5.6x/13.5x band",
                   "support_kind": "citation",
                   "support": "design/36 ADDENDUM L"}
        self.assertFalse(self._survives_without_vocabulary(planted),
                         "a citation-only claim was treated as surviving without its "
                         "vocabulary — the assumption-outside guard cannot catch a plant")


# =====================================================================================
# MAINT-K12-SUBSYSTEM-VIEWS (mgr board :2736, AUTHORISED-BY archi :2735) — the THIRD K12 limb.
# A cold independence pass caught three more subsystem folds reading store.all() for a
# family-scoped answer — files (tree / perms / history), comms (live_channels /
# declared_roles / message_ledger), devices (bindings). archi ruled them the SAME violation
# as the already-fixed SchedulingView/MemoryView folds. Each read now routes through its
# family via the EXISTING config-keyed projection (store.action_set_projection), so the fold
# body is byte-identical and only the iteration SOURCE moves (store.all() -> family.all()).
#
# THE DIFFERENTIAL HOLDS THE CHANGE TO ONE VARIABLE. `_old_*` below are the pre-change fold
# bodies, VERBATIM, run as oracles over BOTH sources: the answer over store.all() (the whole
# record) must equal the answer over the family projection, on churn worlds INCLUDING as_of
# points, and the SHIPPED view method (which now reads the family) must equal both. A wrong
# action-set must make the differential FAIL — the check has teeth only if it can. Nothing
# here crafts an input against the source: it drives the estate's own gate and reads its
# designed behaviour (governance-work-method: validate by reading / running the guards).
# =====================================================================================
class TestK12SubsystemViewsFamilySource(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep33b-k12views-")
        self.record = os.path.join(self.dir, "record.jsonl")
        self.blobs = BlobStore(os.path.join(self.dir, "blobs"))
        self.store, self.gate, self.views = build_kernel(self.record, blobs=self.blobs)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    # ---- the pre-change fold bodies, VERBATIM, as differential oracles ----
    @staticmethod
    def _old_tree(records):
        present = {}
        for e in records:
            a, p = e["action"], (e.get("payload") or {})
            if a == "FILE-CREATE":
                identity = p.get("inode")
                if identity is None:
                    identity = formal_name(e.get("seq"))
                present[p["path"]] = identity
            elif a == "FILE-LINK":
                present[p["new_path"]] = present.get(p["target_path"], p["target_path"])
            elif a == "FILE-UNLINK":
                present.pop(p["path"], None)
        return present

    @staticmethod
    def _old_perms(records, path):
        perm = None
        for e in records:
            a, p = e["action"], (e.get("payload") or {})
            if p.get("path") == path and a in ("FILE-CREATE", "FILE-PERM"):
                perm = p.get("perm", perm)
        return perm

    @staticmethod
    def _old_history(records, path):
        return [e for e in records
                if (e.get("payload") or {}).get("path") == path
                and e["action"] in ("FILE-CREATE", "FILE-WRITE", "FILE-PERM", "FILE-UNLINK")]

    @staticmethod
    def _old_live_channels(records):
        live = {}
        for e in records:
            a, p = e["action"], (e.get("payload") or {})
            if a == "COMMS-OPEN":
                live[(p.get("entity"), p["channel"])] = p.get("role")
            elif a == "COMMS-CLOSE":
                for key in [k for k in live if k[1] == p["channel"]]:
                    live.pop(key, None)
        return live

    @staticmethod
    def _old_declared_roles(records):
        roles = ()
        for e in records:
            p = e.get("payload") or {}
            definition = p.get("definition")
            if p.get("name") == "COMMS-OPEN" and isinstance(definition, Mapping):
                for c in (definition.get("checks") or []):
                    if c.get("check") == "value_domain" and c.get("param") == "role":
                        roles = tuple(c.get("domain") or ())
        return roles

    @staticmethod
    def _old_message_ledger(records, channel):
        return [e for e in records
                if e["action"] in ("COMMS-SEND", "COMMS-RECV")
                and (e.get("payload") or {}).get("channel") == channel]

    @staticmethod
    def _old_bindings(records):
        b = {}
        for e in records:
            a, p = e["action"], (e.get("payload") or {})
            if a == "BIND-DEVICE":
                b[p["device"]] = p["driver"]
            elif a == "UNBIND":
                b.pop(p["device"], None)
        return b

    # ---- world builders driven through the shipped gate ----
    def _fam(self, actions):
        return self.store.action_set_projection(set(actions))

    def _unrelated(self, n):
        for i in range(n):
            self.gate.execute("CREATE-INFO", "SYSTEM", {"object": "u:%d" % i, "content": "x"})

    def _files_churn(self):
        """create / write / perm / link / unlink / re-create + cross-actor + unrelated, so a
        wrong family (a missing UNLINK/LINK/PERM) diverges. Returns the seqs to probe as_of at."""
        seqs = {}
        seqs["c_a"] = self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/a", "perm": "644"})["seq"]
        self.gate.execute("CREATE-INFO", "SYSTEM", {"object": "u:0", "content": "x"})   # unrelated
        self.gate.execute("FILE-WRITE", "SYSTEM", {"path": "/a", "content": "v1"})
        seqs["perm_a"] = self.gate.execute("FILE-PERM", "SYSTEM", {"path": "/a", "perm": "600"})["seq"]
        self.gate.execute("FILE-CREATE", "db", {"path": "/b"})                          # cross-actor
        seqs["link"] = self.gate.execute("FILE-LINK", "SYSTEM",
                                         {"target_path": "/a", "new_path": "/c"})["seq"]
        self.gate.execute("CREATE-INFO", "SYSTEM", {"object": "u:1", "content": "y"})   # unrelated
        self.gate.execute("FILE-UNLINK", "SYSTEM", {"path": "/b"})
        self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/b", "perm": "755"})       # re-create
        return seqs

    def _asof_points(self, seqs):
        return [None] + sorted(seqs.values())

    # ---------- FILES: tree / perms / history differentials incl. as_of ----------
    def test_files_tree_source_differential_incl_asof(self):
        seqs = self._files_churn()
        fv = FilesView(self.store, self.blobs)
        fam = {"FILE-CREATE", "FILE-LINK", "FILE-UNLINK"}
        for as_of in self._asof_points(seqs):
            whole = self._old_tree(self.store.all(as_of))
            family = self._old_tree(self._fam(fam).all(as_of))
            self.assertEqual(whole, family,
                             "tree: family source diverged from whole-store at as_of=%r" % as_of)
            self.assertEqual(fv.tree(as_of), whole,
                             "tree: shipped view diverged from the oracle at as_of=%r" % as_of)

    def test_files_perms_source_differential_incl_asof(self):
        seqs = self._files_churn()
        fv = FilesView(self.store, self.blobs)
        fam = {"FILE-CREATE", "FILE-PERM"}
        for as_of in self._asof_points(seqs):
            for path in ("/a", "/b"):
                whole = self._old_perms(self.store.all(as_of), path)
                family = self._old_perms(self._fam(fam).all(as_of), path)
                self.assertEqual(whole, family,
                                 "perms(%s): family diverged at as_of=%r" % (path, as_of))
                self.assertEqual(fv.perms(path, as_of), whole,
                                 "perms(%s): shipped diverged at as_of=%r" % (path, as_of))

    def test_files_history_source_differential_incl_asof(self):
        seqs = self._files_churn()
        fv = FilesView(self.store, self.blobs)
        fam = {"FILE-CREATE", "FILE-WRITE", "FILE-PERM", "FILE-UNLINK"}
        for as_of in self._asof_points(seqs):
            for path in ("/a", "/b"):
                whole = self._old_history(self.store.all(as_of), path)
                family = self._old_history(self._fam(fam).all(as_of), path)
                self.assertEqual(whole, family,
                                 "history(%s): family diverged at as_of=%r" % (path, as_of))
                self.assertEqual(fv.history(path, as_of), whole,
                                 "history(%s): shipped diverged at as_of=%r" % (path, as_of))

    def test_files_tree_wrong_action_set_makes_the_differential_FAIL(self):
        """The teeth: a family MISSING FILE-UNLINK answers a tree that still holds an unlinked
        name, so it DIVERGES from the whole-store fold. If this ever agreed, the differential
        would be proving nothing."""
        # A TERMINAL removal (no re-create after), so dropping FILE-UNLINK actually changes the
        # answer — a churn world that re-creates the name would mask the divergence.
        self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/x"})
        self.gate.execute("FILE-UNLINK", "SYSTEM", {"path": "/x"})
        wrong = self._old_tree(self._fam({"FILE-CREATE", "FILE-LINK"}).all())  # UNLINK dropped
        whole = self._old_tree(self.store.all())
        self.assertNotEqual(wrong, whole,
                            "a family without FILE-UNLINK matched the whole-store tree — the "
                            "differential cannot fail and so proves nothing")

    # ---------- COMMS: live_channels / declared_roles / message_ledger ----------
    def _comms_churn(self):
        seqs = {}
        for ent in ("p1", "p2"):
            self.gate.execute("CREATE-ACCOUNT", "SYSTEM", {"account_id": ent, "actor_class": "process"})
        seqs["open1"] = self.gate.execute("COMMS-OPEN", "p1",
                                          {"channel": "c1", "entity": "p1", "role": "user-facing"})["seq"]
        self.gate.execute("CREATE-INFO", "SYSTEM", {"object": "u:0", "content": "x"})   # unrelated
        self.gate.execute("COMMS-OPEN", "p2", {"channel": "c2", "entity": "p2", "role": "system-facing"})
        s = self.gate.execute("COMMS-SEND", "p1", {"channel": "c1", "message": "ping", "to": "p2"})
        seqs["send"] = s["seq"]
        self.gate.execute("COMMS-RECV", "p2",
                          {"channel": "c1", "message_hash": s["payload"]["message_hash"]})
        seqs["close"] = self.gate.execute("COMMS-CLOSE", "p2", {"channel": "c2"})["seq"]  # EP-49C: p2 holds c2 (whose-keyed close)
        return seqs

    def test_comms_live_channels_source_differential_incl_asof(self):
        seqs = self._comms_churn()
        cv = CommsView(self.store)
        fam = {"COMMS-OPEN", "COMMS-CLOSE"}
        for as_of in self._asof_points(seqs):
            whole = self._old_live_channels(self.store.all(as_of))
            family = self._old_live_channels(self._fam(fam).all(as_of))
            self.assertEqual(whole, family,
                             "live_channels: family diverged at as_of=%r" % as_of)
            self.assertEqual(cv.live_channels(as_of), whole,
                             "live_channels: shipped diverged at as_of=%r" % as_of)

    def test_comms_declared_roles_reads_the_op_definition_family_not_the_stream(self):
        """declared_roles reads the OP-DEFINITION family (CREATE-OP / AMEND-OP), NOT the COMMS
        DECISION family: the role vocabulary lives in COMMS-OPEN's founding op definition. The
        family source must give the identical answer to the whole-store fold, and unrelated
        records must not move it."""
        self._comms_churn()
        self._unrelated(200)
        cv = CommsView(self.store)
        fam = {"CREATE-OP", "AMEND-OP"}
        whole = self._old_declared_roles(self.store.all())
        family = self._old_declared_roles(self._fam(fam).all())
        self.assertEqual(whole, family, "declared_roles: family diverged from whole-store")
        self.assertEqual(cv.declared_roles(), whole, "declared_roles: shipped diverged from oracle")
        self.assertEqual(tuple(sorted(whole)), ("system-facing", "user-facing"))

    def test_comms_message_ledger_source_differential_incl_asof(self):
        seqs = self._comms_churn()
        cv = CommsView(self.store)
        fam = {"COMMS-SEND", "COMMS-RECV"}
        for as_of in self._asof_points(seqs):
            whole = self._old_message_ledger(self.store.all(as_of), "c1")
            family = self._old_message_ledger(self._fam(fam).all(as_of), "c1")
            self.assertEqual(whole, family,
                             "message_ledger: family diverged at as_of=%r" % as_of)
            self.assertEqual(cv.message_ledger("c1", as_of), whole,
                             "message_ledger: shipped diverged at as_of=%r" % as_of)

    # ---------- DEVICES: bindings differential incl. as_of ----------
    def _devices_churn(self):
        seqs = {}
        self.gate.execute("REGISTER-CAPABILITY", "SYSTEM", {"driver": "nvme0", "device_class": "block"})
        self.gate.execute("REGISTER-CAPABILITY", "SYSTEM", {"driver": "e1000", "device_class": "net"})
        seqs["bind0"] = self.gate.execute("BIND-DEVICE", "SYSTEM",
                                          {"device": "d0", "driver": "nvme0"})["seq"]
        self.gate.execute("CREATE-INFO", "SYSTEM", {"object": "u:0", "content": "x"})   # unrelated
        self.gate.execute("BIND-DEVICE", "SYSTEM", {"device": "d1", "driver": "e1000"})
        seqs["unbind"] = self.gate.execute("UNBIND", "SYSTEM", {"device": "d0"})["seq"]
        self.gate.execute("BIND-DEVICE", "SYSTEM", {"device": "d0", "driver": "e1000"})  # re-bind
        return seqs

    def test_devices_bindings_source_differential_incl_asof(self):
        seqs = self._devices_churn()
        dv = DevicesView(self.store)
        fam = {"BIND-DEVICE", "UNBIND"}
        for as_of in self._asof_points(seqs):
            whole = self._old_bindings(self.store.all(as_of))
            family = self._old_bindings(self._fam(fam).all(as_of))
            self.assertEqual(whole, family,
                             "bindings: family diverged at as_of=%r" % as_of)
            self.assertEqual(dv.bindings(as_of), whole,
                             "bindings: shipped diverged at as_of=%r" % as_of)

    def test_devices_bindings_wrong_action_set_makes_the_differential_FAIL(self):
        """The teeth for devices: a family MISSING UNBIND leaves an unbound device present, so it
        diverges from the whole-store fold."""
        # A TERMINAL unbind (no re-bind after), so dropping UNBIND actually changes the answer.
        self.gate.execute("REGISTER-CAPABILITY", "SYSTEM", {"driver": "nvme0"})
        self.gate.execute("BIND-DEVICE", "SYSTEM", {"device": "d0", "driver": "nvme0"})
        self.gate.execute("UNBIND", "SYSTEM", {"device": "d0"})
        wrong = self._old_bindings(self._fam({"BIND-DEVICE"}).all())      # UNBIND dropped
        whole = self._old_bindings(self.store.all())
        self.assertNotEqual(wrong, whole,
                            "a family without UNBIND matched the whole-store bindings — the "
                            "differential cannot fail and so proves nothing")

    # ---------- COST: each read costs its family, not unrelated records (+ same-family control) ----------
    def _family_reads(self, actions, build_family, n_unrelated=0):
        self.setUp()
        try:
            build_family()
            base = len(self._fam(actions).all())
            self._unrelated(n_unrelated)
            return base, len(self._fam(actions).all())
        finally:
            self.tearDown()

    def test_files_tree_family_reads_only_its_family_not_unrelated_records(self):
        fam = {"FILE-CREATE", "FILE-LINK", "FILE-UNLINK"}
        def build():
            self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/a"})
            self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/b"})
            self.gate.execute("FILE-UNLINK", "SYSTEM", {"path": "/b"})
        base, grown = self._family_reads(fam, build, n_unrelated=5000)
        self.assertEqual(base, 3, "seed is 2 creates + 1 unlink = 3 family records")
        self.assertEqual(grown, base,
                         "the files tree fold read more records after 5000 unrelated ones — the "
                         "K12 family bound is not holding; re-read design/36 ADDENDUM S")

    def test_files_tree_family_reads_grow_with_its_OWN_family(self):
        fam = {"FILE-CREATE", "FILE-LINK", "FILE-UNLINK"}
        def build():
            self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/a"})
        base, _ = self._family_reads(fam, build, n_unrelated=0)
        self.setUp()
        try:
            self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/a"})
            for i in range(50):
                self.gate.execute("FILE-CREATE", "SYSTEM", {"path": "/f%d" % i})
            grown = len(self._fam(fam).all())
        finally:
            self.tearDown()
        self.assertEqual(grown, base + 50,
                         "files-family growth did not move what the tree fold reads — the "
                         "projection is not actually selecting the family")

    def test_devices_bindings_family_reads_only_its_family_not_unrelated_records(self):
        fam = {"BIND-DEVICE", "UNBIND"}
        def build():
            self.gate.execute("REGISTER-CAPABILITY", "SYSTEM", {"driver": "nvme0"})
            self.gate.execute("BIND-DEVICE", "SYSTEM", {"device": "d0", "driver": "nvme0"})
            self.gate.execute("UNBIND", "SYSTEM", {"device": "d0"})
        base, grown = self._family_reads(fam, build, n_unrelated=5000)
        self.assertEqual(base, 2, "seed is 1 bind + 1 unbind = 2 family records")
        self.assertEqual(grown, base,
                         "the bindings fold read more records after 5000 unrelated ones — the "
                         "K12 family bound is not holding; re-read design/36 ADDENDUM S")

    def test_comms_live_channels_family_reads_only_its_family_not_unrelated_records(self):
        fam = {"COMMS-OPEN", "COMMS-CLOSE"}
        def build():
            self.gate.execute("CREATE-ACCOUNT", "SYSTEM", {"account_id": "p1", "actor_class": "process"})
            self.gate.execute("COMMS-OPEN", "p1", {"channel": "c1", "entity": "p1", "role": "user-facing"})
            self.gate.execute("COMMS-CLOSE", "p1", {"channel": "c1"})
        base, grown = self._family_reads(fam, build, n_unrelated=5000)
        self.assertEqual(base, 2, "seed is 1 open + 1 close = 2 family records")
        self.assertEqual(grown, base,
                         "live_channels read more records after 5000 unrelated ones — the K12 "
                         "family bound is not holding; re-read design/36 ADDENDUM S")

    # ---------- kill the held cache and replay from the record alone: identical ----------
    def test_kill_the_family_cache_and_replay_are_identical(self):
        seqs = self._files_churn()
        fam = {"FILE-CREATE", "FILE-LINK", "FILE-UNLINK"}
        live = self._old_tree(self._fam(fam).all())
        self._fam(fam).kill()                                       # (a) kill the held projection
        killed = self._old_tree(self._fam(fam).all())
        self.assertEqual(live, killed, "killing the held cache changed the tree answer")
        store2, _g2, _v2 = build_kernel(self.record, blobs=self.blobs)  # (b) fresh kernel, same file
        replay = self._old_tree(store2.action_set_projection(fam).all())
        self.assertEqual(live, replay, "a fresh kernel over the record replayed a different tree")
        _ = seqs

    def test_an_empty_action_set_refuses_rather_than_serving_nothing(self):
        with self.assertRaises(StaleIndex):
            self.store.action_set_projection(set())


if __name__ == "__main__":
    unittest.main()
