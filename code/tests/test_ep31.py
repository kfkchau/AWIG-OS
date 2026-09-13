"""EP-31 (BUILD) — M6: GOVERN MEMORY AT THE METAL. The battery + the red worlds.

design/22 is the stage brief, entire: the memory-event classification (§2), the pure-S hot
path (§3), reconstruction f(LAW, DECISIONS, INPUTS) (§4), the worked eviction decision (§5).

THE ONE SENTENCE: memory is the acid test because the hot path happens a million times a
second and must record NOTHING; governance counts governed DECISIONS, never machine ACTIVITY.
The proof is the falsifiable form — records-per-fault FALLS toward the governance floor as the
fault rate rises — never a bound the pass declares.

SPLIT (host vs guest/MAX). Everything here runs on the HOST at the record/model level. A3's
records-per-fault MEASUREMENT at real load levels under a kernel fault storm is owner-ruled
MAX tier and runs in the GUEST — a SEPARATE dispatch. This file builds the A3 FRAME (the
pure-S fault path whose ratio the MAX dispatch measures) and drives its STRUCTURAL shape and
its teeth (R2/R3); it does NOT boot the guest and produces no records-per-fault-at-load figure.

MODE: every verdict here is DRIVEN (a command over the tree), never READ.
"""

import copy
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # so `import era_pin` resolves (EP-28Z)
import era_pin  # noqa: E402  — the estate's one home for reading a path at a named commit
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from kernel.opdefs import OP_CHECKS, validate_definition_shape  # noqa: E402
from subsystems.memory import (  # noqa: E402
    MemoryView, classify, EVENT_CLASS, RECORDED, REALISED_BY, is_memory_record)
from observe.classmap import DECISION, LAW, INPUT, CACHE, STREAM  # noqa: E402
from founding.install import (  # noqa: E402
    load_pack, records as pack_records, _validate, FoundingIntegrityError, founding_version,
)

MEM_LAW_FAMILY = ("MEM-LAW-BUDGET", "MEM-LAW-ALLOC", "MEM-LAW-EVICT", "MEM-LAW-PROTECT")

#: EP-31's LANDING era — the commit at which this suite first landed with EP-31's MEM-LAW-BUDGET
#: create in the founding (founding_version 1.31.0, the MINOR move from 1.30.0). test_a5's minor-bump
#: assertion is a stored copy of a computable value (the estate's named class, test_ep26:1234) and
#: reads THIS era's founding rather than the live tree, so a later lawful bump (EP-35's 1.31.0 -> 1.32.0
#: era boundary) no longer reds a claim that was only ever about EP-31's own landing.
EP31_LANDING_COMMIT = "a4fe11181937ba05187f8be5c77e45d405f7700d"


def created_rules(recs):
    """The rule_ids the pack CREATES (a CREATE-RULE record declares one)."""
    return {r["payload"]["rule_id"] for r in recs if r.get("action") == "CREATE-RULE"}


def mem_grant_ceiling_row(recs):
    """The ceiling check row on MEM-GRANT, read from the pack (never carried)."""
    for r in recs:
        pl = r.get("payload") or {}
        if pl.get("name") == "MEM-GRANT":
            for c in (pl.get("definition") or {}).get("checks") or []:
                if c.get("check") == "ceiling":
                    return c
    raise AssertionError("MEM-GRANT has no ceiling row")


class _Mem(unittest.TestCase):
    """A booted kernel + memory view over a fresh record."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views = build_kernel(self.record)
        self.mv = MemoryView(self.store)

    def budget(self, holder, ceiling):
        self.gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": holder, "ceiling": ceiling})

    def grant(self, region, size, holder="web", **kw):
        return self.gate.execute("MEM-GRANT", holder, {"region": region, "size": size,
                                                        "holder": holder, **kw})

    def evict(self, region, actor="web"):
        return self.gate.execute("MEM-EVICT", actor, {"region": region})


# ---------------------------------------------------------------------------------------
# A1 — DRIVEN, FIRST. The wiring, in-shape vs in-force. (archi :2642 binding.)
# ---------------------------------------------------------------------------------------
class A1_WiringInShapeVsInForce(_Mem):
    """This row assumes NEITHER; it reports what IS. Driven finding: the ceiling is IN FORCE
    (an over-budget grant is refused, an under-budget one serves), and after this build the law
    it cites EXISTS — the citation that was a phantom (a dangling MEM-LAW-BUDGET) is now real."""

    def test_a1_ceiling_is_in_force_not_only_in_shape(self):
        self.budget("web", 100)
        self.grant("r1", 100)                     # under -> serves
        self.assertEqual(self.mv.resident_size("web"), 100)
        with self.assertRaises(OpError) as cm:    # over -> refuses, IN FORCE
            self.grant("r2", 1)
        self.assertEqual(cm.exception.rule, "MEM-LAW-BUDGET")

    def test_a1_the_cited_law_is_no_longer_a_phantom(self):
        # the ceiling row cites MEM-LAW-BUDGET; after A5 that name is a created rule, so the
        # refusal above cites a law the founding CONTAINS (not a phantom).
        cited = mem_grant_ceiling_row(pack_records(load_pack()))["cite"]
        self.assertEqual(cited, "MEM-LAW-BUDGET")
        self.assertIn(cited, created_rules(pack_records(load_pack())))


# ---------------------------------------------------------------------------------------
# A2 — DRIVEN. The classification (design/22 §2).
# ---------------------------------------------------------------------------------------
class A2_MemoryEventsClassified(_Mem):
    def test_a2_every_event_lands_to_its_class_per_design22_sec2(self):
        # design/22 §2's table, each row citing §2 by construction (the module encodes §2).
        self.assertEqual(classify("mmap"), DECISION)
        self.assertEqual(classify("mprotect"), DECISION)
        self.assertEqual(classify("munmap"), DECISION)
        self.assertEqual(classify("budget-amendment"), LAW)
        self.assertEqual(classify("first-touch-fault"), DECISION)
        self.assertEqual(classify("eviction"), DECISION)
        self.assertEqual(classify("oom-kill"), DECISION)
        self.assertEqual(classify("minor-fault"), CACHE)          # the load-bearing row
        self.assertEqual(classify("major-fault-completion"), INPUT)
        self.assertEqual(classify("accessed-dirty-bit"), STREAM)
        self.assertEqual(classify("load-store"), STREAM)

    def test_a2_only_decision_and_law_events_record(self):
        # RECORDED tracks the class: DECISION/LAW record; CACHE/INPUT/STREAM do not.
        self.assertTrue(RECORDED["mmap"] and RECORDED["budget-amendment"] and RECORDED["eviction"])
        self.assertFalse(RECORDED["minor-fault"] or RECORDED["accessed-dirty-bit"]
                         or RECORDED["load-store"] or RECORDED["major-fault-completion"])

    def test_a2_the_behaviour_matches_the_table(self):
        # DECISION/LAW events append exactly one record each; the CACHE fill (fault) appends none.
        n = len(self.store.all())
        self.budget("web", 10 ** 9)               # LAW
        self.grant("r1", 10)                       # DECISION (mmap)
        self.gate.execute("MEM-PROTECT", "web", {"region": "r1", "prot": "r"})  # DECISION
        self.evict("r1")                           # DECISION (eviction)
        self.assertEqual(len(self.store.all()) - n, 4)   # four governed acts, four records
        n = len(self.store.all())
        self.grant("r2", 10)
        for _ in range(500):
            self.mv.fault("r2")                    # CACHE fills — record NOTHING
        self.assertEqual(len(self.store.all()) - n, 1)   # only the grant recorded, not the faults


# ---------------------------------------------------------------------------------------
# A3 — THE MAX CRUX (the FRAME here; the MEASUREMENT is the guest/MAX dispatch).
# ---------------------------------------------------------------------------------------
class A3_TheFrame_RecordsPerFaultFalls(_Mem):
    """BUILT HERE: the pure-S fault-path frame and its STRUCTURAL shape. NOT built here: the
    records-per-fault MEASUREMENT at real load levels under a kernel fault storm — owner-ruled
    MAX tier, guest dispatch, deferred. Stop condition 4: if the frame made the ratio flat or
    rising, that is evidence AGAINST the architecture's central claim — STOP, not tune."""

    def _fault_phase_records(self, n_faults):
        """records appended DURING a fault storm of n minor faults, decisions fixed beforehand."""
        self.budget("web", 10 ** 9)
        self.grant("r1", 10)
        before = len(self.store.all())
        for _ in range(n_faults):
            self.mv.fault("r1")
        return len(self.store.all()) - before

    def test_a3_frame_fault_phase_records_nothing(self):
        self.assertEqual(self._fault_phase_records(2000), 0)

    def test_a3_frame_ratio_falls_toward_the_floor_as_rate_rises(self):
        # records-per-fault = |records in storm| / faults. With decisions fixed and the hot path
        # recording nothing, the ratio is 0 at every rate and 10x the faults keeps it at the floor
        # (0) — the frame's shape. A frame that recorded per fault would floor at >=1 (R2).
        for f in (100, 1000, 10000):
            self.setUp()                            # fresh record per level
            self.assertEqual(self._fault_phase_records(f), 0)

    def test_a3_frame_decision_bound_ratio_strictly_falls(self):
        # The falling made explicit at the model: total records over the whole storm are the
        # DECISIONS (fixed D) plus zero-per-fault, so records/fault = D/F falls strictly as F
        # rises and tends to the floor 0 — records track DECISIONS, not faults.
        ratios = []
        for f in (100, 1000):
            self.setUp()
            self.budget("web", 10 ** 9)
            self.grant("r1", 10)                    # D counted: the LAW + the grant
            d = len(self.store.all())
            for _ in range(f):
                self.mv.fault("r1")
            total = len(self.store.all())
            self.assertEqual(total, d)              # nothing added by the faults
            ratios.append(d / f)
        self.assertLess(ratios[1], ratios[0])       # falls toward the floor as F rises


# ---------------------------------------------------------------------------------------
# A4 — DRIVEN. ceiling completed, guards MEM-GRANT.
# ---------------------------------------------------------------------------------------
class A4_CeilingGuardsMemGrant(_Mem):
    def test_a4_over_budget_refuses_one_under_serves(self):
        self.budget("web", 100)
        self.grant("r1", 60)                        # under -> serves
        self.assertEqual(self.mv.resident_size("web"), 60)
        with self.assertRaises(OpError) as cm:      # 60 + 50 > 100 -> refuse
            self.grant("r2", 50)
        self.assertEqual(cm.exception.rule, "MEM-LAW-BUDGET")
        self.assertEqual(self.mv.resident_size("web"), 60)   # the refused grant left no residency


# ---------------------------------------------------------------------------------------
# A5 — DRIVEN. MEM-LAW-BUDGET created through the founding door.
# ---------------------------------------------------------------------------------------
class A5_MemLawBudgetCreated(_Mem):
    def test_a5_mem_law_budget_is_created_and_active(self):
        self.assertIn("MEM-LAW-BUDGET", created_rules(pack_records(load_pack())))
        self.assertIn("MEM-LAW-BUDGET", self.views.active_rules())

    def test_a5_founding_minor_bump(self):
        # [DOCUMENTED FLIP — MAINT-EP31-32-VERSION-REPIN, 2026-09-03, charter §A57 era-stabilization
        # (board :2772, AUTHORISED-BY :2761). CAUSE: a LATER lawful founding move — EP-35's era-boundary
        # create, 1.31.0 -> 1.32.0. This row read `founding_version()` LIVE and asserted minor == 31, so
        # EP-35's bump reddened a claim about EP-31's OWN landing. ASSERTED: EP-31's landing era at
        # `EP31_LANDING_COMMIT`, whose founding is 1.31.0 (minor 31) — the computable value AT EP-31's era,
        # robust to any future lawful bump. SUPERSEDED: the read of `founding_version()` live. REMAINS
        # TRUE: a new LAW surface is a MINOR move; major unchanged, patch 0 (1.30.0 -> 1.31.0). GIVEN UP:
        # nothing; the live tree was never a coordinate of EP-31's landing.]
        major, minor, patch = (
            int(x) for x in era_pin.pack_at(EP31_LANDING_COMMIT)["founding_version"].split("."))
        self.assertEqual((major, patch), (1, 0))
        self.assertEqual(minor, 31)


# ---------------------------------------------------------------------------------------
# A6 — DRIVEN. The §A51 resolution, inside the law's wording — no new kind.
# ---------------------------------------------------------------------------------------
class A6_A51ResolutionInTheWording(_Mem):
    def test_a6_the_law_wording_carries_population_and_basis(self):
        text = self.views.active_rules()["MEM-LAW-BUDGET"]["text"]
        for token in ("§A51", "POPULATION", "BASIS", "FOLD", "NEVER STORED"):
            self.assertIn(token, text.upper() if token.isupper() or token == "§A51" else text,
                          "MEM-LAW-BUDGET wording is missing %r" % token)

    def test_a6_no_new_check_kind_was_minted(self):
        # the ceiling kind ALREADY exists; the §A51 resolution is wording + a leash on the
        # existing kind, NOT a seventeenth operator. OP_CHECKS is unchanged by this build.
        self.assertIn("ceiling", OP_CHECKS)
        self.assertEqual(len(OP_CHECKS), 19)

    def test_a6_the_ceiling_row_declares_its_population_and_basis(self):
        # the machine half of §A51: the summed value's population and basis are DECLARED FIELDS
        # on the ceiling row, not hidden in a scalar.
        c = mem_grant_ceiling_row(pack_records(load_pack()))
        self.assertEqual(c["aggregate_field"], "size")        # BASIS
        self.assertEqual(c["aggregate_action"], "MEM-GRANT")  # POPULATION
        self.assertEqual(c["holder_field"], "holder")         # POPULATION scope
        self.assertEqual(c["removal_action"], "MEM-EVICT")    # POPULATION removals
        self.assertEqual(c["cite"], "MEM-LAW-BUDGET")


# ---------------------------------------------------------------------------------------
# A7 — DRIVEN. T-CACHE-KILL-SWAP.
# ---------------------------------------------------------------------------------------
class A7_CacheKillSwap(_Mem):
    """Kill every page-derived structure, replay the mapping/eviction/IO decisions THROUGH A
    SWAP CYCLE, reconstruct identical structure and content. PLATFORM DEPENDENCY, STATED not
    blind (design/22 §4; order intake, close-ledger 25): anonymous pages never written are zero
    ONLY while the platform zeroes freed frames — a freed frame carrying old content would be a
    replay-determinism divergence. At the record/model level here, page CONTENT reconstructs
    through the file subsystem's content-addressed guarantee (design/22 §4); the real-swap-device
    exhibition is the guest's, and this row proves the DECISION-replay half."""

    def test_a7_kill_page_state_replay_through_swap_reconstructs(self):
        self.budget("web", 10 ** 9)
        self.grant("r1", 10, prot="rw")
        self.grant("r2", 20, prot="r")
        self.evict("r1")                            # page-out (swap-out): a recorded DECISION
        self.grant("r1", 10, prot="rw")             # page-in (major fault re-materialises): DECISION
        live = self.mv.mappings()
        # KILL every page-derived structure: a fresh store replays the record from scratch, and a
        # fresh MemoryView folds it — no page table, VMA tree or free-list survives the kill.
        store2, _, _ = build_kernel(self.record)
        rebuilt = MemoryView(store2).mappings()
        self.assertEqual(live, rebuilt)             # identical structure and content
        self.assertIn("r1", rebuilt)                # swapped-out-then-in region reconstructs
        self.assertEqual(rebuilt["r1"]["size"], 10)


# ---------------------------------------------------------------------------------------
# A8 — DRIVEN. T-EVICTION-EVIDENCE.
# ---------------------------------------------------------------------------------------
class A8_EvictionEvidence(_Mem):
    def test_a8_eviction_embeds_evidence_and_reconstructs_from_the_decision_alone(self):
        self.budget("web", 10 ** 9)
        self.grant("r1", 10)
        ev = self.evict("r1")
        # the decision FROZE the aggregate it acted on (design/22 §5)
        self.assertIsNotNone(ev.get("evidence_summary"))
        region, evidence = self.mv.evictions()[0]
        self.assertEqual(region, "r1")
        self.assertIsNotNone(evidence)
        # NO RAW-ACCESS JOURNAL EXISTS: nothing per-access was recorded; the only record about r1's
        # cooling is the one eviction decision (the raw accesses were STREAM).
        self.assertEqual(len(self.mv.evictions()), 1)
        # replay reconstructs the post-eviction state from the record alone
        store2, _, _ = build_kernel(self.record)
        self.assertNotIn("r1", MemoryView(store2).mappings())


# ---------------------------------------------------------------------------------------
# A9 — DRIVEN. The dangling set re-driven, and the three held gates.
# ---------------------------------------------------------------------------------------
class A9_DanglingSetAndHeldGates(_Mem):
    def test_a9_budget_left_the_dangling_set_the_three_are_held(self):
        created = created_rules(pack_records(load_pack()))
        self.assertIn("MEM-LAW-BUDGET", created)               # created (A5) -> left the dangle
        for held in ("MEM-LAW-ALLOC", "MEM-LAW-EVICT", "MEM-LAW-PROTECT"):
            self.assertNotIn(held, created,                    # HELD owner-gates: NOT created
                             "%s was created — it is a HELD owner-gate, not this 2-yes" % held)

    def test_a9_the_held_three_are_still_cited_so_they_remain_scheduled_danglers(self):
        recs = pack_records(load_pack())
        cited = set()
        for r in recs:
            d = (r.get("payload") or {}).get("definition") or {}
            if str(d.get("law_cited", "")).startswith("MEM-LAW"):
                cited.add(d["law_cited"])
        self.assertTrue({"MEM-LAW-ALLOC", "MEM-LAW-EVICT", "MEM-LAW-PROTECT"} <= cited)


# =======================================================================================
# RED WORLDS — mandatory, never empty. Each drives BOTH verdicts through the instrument.
# =======================================================================================
class R1_FoundingDoorRefusesAnUnwordedCreate(unittest.TestCase):
    """A create that cannot be refused is not a gate. Attempt a BARE SUMMABLE ceiling — one that
    sums a field without declaring its §A51 population/basis — and the founding door refuses it;
    restore the wording and it admits. Driven THROUGH install._validate (the real founding door),
    both verdicts."""

    def test_r1_bare_summable_refused_worded_admits(self):
        good = load_pack()
        _validate(pack_records(good))               # the worded pack admits (control / restore)
        bad = copy.deepcopy(good)
        row = mem_grant_ceiling_row(pack_records(bad))
        del row["aggregate_action"]                 # strip the POPULATION -> a bare summable
        with self.assertRaises(FoundingIntegrityError) as cm:
            _validate(pack_records(bad))
        self.assertIn("§A51", str(cm.exception))
        # near-miss control: the same pack with the field restored is admitted again
        row["aggregate_action"] = "MEM-GRANT"
        _validate(pack_records(bad))


class R2_TheScalingTestCanFail(_Mem):
    """The acid test's teeth. Force records-per-fault to NOT fall — record something per minor
    fault — and the ratio floors at >=1 instead of tending to 0. Restore pure-S and it falls.
    THIS IS THE FALSIFIABLE FORM: the architecture's central claim put where it can lose."""

    def _ratio(self, fault_fn, n_faults):
        self.setUp()
        self.budget("web", 10 ** 9)
        self.grant("r1", 10)
        before = len(self.store.all())
        for _ in range(n_faults):
            fault_fn("r1")
        return (len(self.store.all()) - before) / n_faults

    def _recording_fault(self, region):
        # the WRONG frame: a "fault" that appends a record (per-fault journalling — the named
        # wrong reference). This is a planted bad path, never memory.py's real fault().
        self.gate.execute("MEM-PROTECT", "web", {"region": region, "prot": "rw"})

    def test_r2_recording_per_fault_floors_the_ratio_pure_S_falls(self):
        # WRONG frame: ratio is 1.0 at every rate and never approaches the floor -> the scaling
        # invariant reds (a per-fault-recording frame cannot fall to 0).
        for f in (100, 1000):
            self.assertGreaterEqual(self._ratio(self._recording_fault, f), 1.0)
        # RIGHT frame (memory.py's real fault): ratio is 0 at every rate -> at the floor, passes.
        self.assertEqual(self._ratio(self.mv.fault, 100), 0.0)
        self.assertEqual(self._ratio(self.mv.fault, 1000), 0.0)


class R3_AMinorFaultThatRecordsSomethingReds(_Mem):
    """T-MINOR-FAULT-RECORDS-NOTHING: a fault storm must append zero records. Plant one append on
    the fault path and the invariant reds; the real path greens."""

    def _minor_fault_records_nothing(self, fault_fn):
        self.setUp()
        self.budget("web", 10 ** 9)
        self.grant("r1", 10)
        before = len(self.store.all())
        for _ in range(50):
            fault_fn("r1")
        return len(self.store.all()) == before

    def test_r3_planted_append_reds_removed_greens(self):
        planted = lambda region: self.gate.execute("MEM-PROTECT", "web",
                                                    {"region": region, "prot": "rw"})
        self.assertFalse(self._minor_fault_records_nothing(planted))   # planted -> REDS
        self.assertTrue(self._minor_fault_records_nothing(self.mv.fault))  # real path -> green


class R4_AMissingDecisionBreaksReconstruction(_Mem):
    """Drop one eviction decision before replay and the reconstructed image differs; restore it
    and the image is identical. Reconstruction is f(DECISIONS) — a missing decision is a
    different world, driven both ways."""

    def test_r4_drop_eviction_reds_restore_greens(self):
        self.budget("web", 10 ** 9)
        self.grant("r1", 10)
        self.evict("r1")
        full = [e for e in self.store.all()]
        # RESTORE (control): replay the full record -> r1 absent, reconstruction matches live
        replay_full = self._replay(full).mappings()
        self.assertEqual(replay_full, self.mv.mappings())
        self.assertNotIn("r1", replay_full)
        # DROP the eviction decision -> r1 wrongly resident -> reconstruction DIFFERS (reds)
        without_evict = [e for e in full if e.get("action") != "MEM-EVICT"]
        replay_dropped = self._replay(without_evict).mappings()
        self.assertNotEqual(replay_dropped, self.mv.mappings())
        self.assertIn("r1", replay_dropped)

    def _replay(self, events):
        # A faithful minimal store: the family-keyed projection MemoryView reads through resolves
        # each record by its own `seq`, so this stub carries `events` and a seq-keyed `by_seq`
        # (a dict, so the drop-a-record arm still resolves the survivors across the gap it leaves).
        class _S:
            def __init__(s, evs):
                s.events = list(evs)
                s._by_seq = {e["seq"]: e for e in s.events}
            def all(s, as_of=None):
                if as_of is None:
                    return list(s.events)
                return [e for e in s.events if e["seq"] <= as_of]
            def by_seq(s, seq):
                return s._by_seq.get(seq)
        return MemoryView(_S(events))


class R5_AnUngatedFamilyLawCreateIsRefused(unittest.TestCase):
    """The held gate is MECHANICAL, not a note. The 2-yes spends on MEM-LAW-BUDGET only; the
    family does not ride it. A guard that reds if any MEM-LAW beyond BUDGET is created: plant a
    MEM-LAW-ALLOC create and the guard reds; the real pack greens."""

    def _family_gate_holds(self, recs):
        created = created_rules(recs)
        beyond = [l for l in created if l.startswith("MEM-LAW") and l != "MEM-LAW-BUDGET"]
        return beyond == []

    def test_r5_planted_family_create_reds_real_pack_greens(self):
        self.assertTrue(self._family_gate_holds(pack_records(load_pack())))   # real pack -> held
        planted = copy.deepcopy(load_pack())
        planted["steps"][-1]["records"].append({
            "actor": "PC_RUNTIME", "action": "CREATE-RULE", "object": "MEM-LAW-ALLOC",
            "rule_cited": "BOOT-INT",
            "payload": {"rule_id": "MEM-LAW-ALLOC", "text": "ungated family create",
                        "scope": "space:root"}})
        self.assertFalse(self._family_gate_holds(pack_records(planted)))       # planted -> REDS


# ---------------------------------------------------------------------------------------
# K12 (design/36 ADDENDUM S) — the memory read paths cost their family, not the stream.
# MAINT-K12-FAMILY-INDEX: resident_size()/mappings() read the memory family through a held
# RecordProjection. The projection holds locations, never answers, so killing it changes nothing.
# ---------------------------------------------------------------------------------------
class K12_FamilyProjection(_Mem):

    def test_resident_size_reads_its_family_not_unrelated_records(self):
        self.budget("web", 10 ** 9)
        self.grant("r1", 100)
        self.grant("r2", 50)
        for i in range(200):                                   # records the answer does not read
            self.gate.execute("CREATE-INFO", "SYSTEM", {"object": "u:%d" % i, "content": "x"})
        self.assertEqual(self.mv.resident_size("web"), 150)    # answer unchanged by the noise
        # the fold iterates the two MEM-GRANT records, not the 202-record stream
        self.assertEqual(len(self.mv._records.all()), 2)
        self.assertTrue(all(is_memory_record(e) for e in self.mv._records.all()))

    def test_kill_the_projection_replay_from_the_record_alone_is_identical(self):
        self.budget("web", 10 ** 9)
        self.grant("r1", 100)
        self.grant("r2", 50)
        self.evict("r1")
        before = self.mv.mappings("web")
        self.mv._records.kill()                                # T-ACCELERATION-IS-DERIVED
        self.assertEqual(self.mv.mappings("web"), before)      # rebuilt from the record, identical
        self.assertEqual(MemoryView(self.store).mappings("web"), before)  # a fresh view agrees


if __name__ == "__main__":
    unittest.main()
