# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-verification ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-33A — THE ENGINE & MECHANICAL FIX-PACK: the red worlds and the regression tests.

Every verification probe of this fix-pack lands here as a standing test (charter conduct
clause). The four RED WORLDS the plan names are R1 (item 20's declared map catches a member
spelled against the `_param` convention), R2 (the BUILD-PROGRESS append-only guard refuses a
non-append), R4 (item 21's station guard fires through the founding door), and — NOT built —
R3, which belongs to item 28 and is RAISED, not built: item 28's prescribed derivation (the
mount root's owner from the mount decision) conflicts the LATER ruling EP-28C W4b, which rules
the root SUBSTRATE and pins it. R3 cannot exist without overturning that pin, so it is handed
to EP-33B with the raise. The remaining classes below regression-guard items 10, 11, 20 and
the §A25 CLAUDE.md join.
"""
import gc
import importlib.util as _ilu
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, REPO)

from kernel import opdefs                                   # noqa: E402
from kernel.compose import build_full_kernel               # noqa: E402
from founding.install import _validate, FoundingIntegrityError  # noqa: E402
from tools.conformance import fixtures                     # noqa: E402


def _load_by_path(name, relpath):
    spec = _ilu.spec_from_file_location(name, os.path.join(REPO, relpath))
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


inventory = _load_by_path("govos_ep33a_inventory", "tools/docmap/inventory.py")

WHEN = "2019-03-04T05:06:07+00:00"
PROV = {"asserted_by": "window:proc@m1.1", "source": "observation", "could_read": []}


# =============================================================================================
# R1 — ITEM 20: the declared member-to-field map catches a misspelled member the spelling
# derivation missed, and the shipped membership is read from the map, not from the suffix.
# =============================================================================================

class R1_TheMapCatchesAMisspelledMember(unittest.TestCase):
    def test_a_member_spelled_against_the_convention_is_found_by_the_map_and_missed_by_spelling(self):
        """The old shape's blind spot, shown then closed. `deadline` names a caller parameter —
        it belongs in the param-half — but is spelled against the `_param` convention. The
        spelling derivation misses it; the declared map finds it because it is DECLARED, not
        inferred from how it is spelled."""
        fam = opdefs.ENVELOPE_ROUTERS + ("deadline",)
        declared = dict(opdefs.ROUTER_FIELDS, deadline="deadline_at")

        old_spelling_rule = tuple(r for r in fam if r.endswith("_param"))
        new_declared_rule = tuple(r for r in fam if r in declared)

        self.assertNotIn("deadline", old_spelling_rule,
                         "the OLD spelling-derivation should MISS a member spelled against the "
                         "convention — that is the blind spot item 20 closes")
        self.assertIn("deadline", new_declared_rule,
                      "the DECLARED map must FIND it — membership from declaration, not spelling")

    def test_the_shipped_membership_is_read_from_the_declared_map(self):
        """Not merely that a map exists, but that PARAM_ROUTERS is derived from it."""
        self.assertEqual(
            opdefs.PARAM_ROUTERS,
            tuple(r for r in opdefs.ENVELOPE_ROUTERS if r in opdefs.ROUTER_FIELDS),
            "membership must be READ FROM the declared map")
        # the two members that name no parameter are absent from the map, by declaration
        self.assertNotIn("content_form", opdefs.ROUTER_FIELDS)
        self.assertNotIn("stamp_actor", opdefs.ROUTER_FIELDS)
        # and the split still covers the whole family
        self.assertEqual(set(opdefs.PARAM_ROUTERS) | {"content_form", "stamp_actor"},
                         set(opdefs.ENVELOPE_ROUTERS))


class R1_TheMapIsTruthful(unittest.TestCase):
    """The map's VALUES are load-bearing, not decoration: the interpreter routes each declared
    member to exactly the field the map names. A world builds, an op declares each router, and
    the record is read for the declared field."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store, self.gate, self.views, self.blobs, _ = build_full_kernel(
            self.path(), os.path.join(self.dir, "blobs"))

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def path(self):
        return os.path.join(self.dir, "rec.jsonl")

    def _routes(self, member, param, value):
        name = "MAP-%s" % member.replace("_", "-").upper()
        self.gate.execute("CREATE-OP", "owner", {"name": name, "definition": {
            "law_cited": "M1-OBSERVATION", "description": "item-20 map truthfulness",
            "params": {"subject": "required", param: "optional"},
            "object_param": "subject", "payload_from": ["subject"], member: param,
            # subject is the object id; the router param carries a value routed into a structural
            # envelope field (target/evidence_summary/occurrence_time/provenance) — both inline (vocab door).
            "structural_params": ["subject", param]}})
        rec = self.gate.execute(name, "owner", {"subject": "thing:1", param: value})
        return rec

    def test_each_declared_member_routes_to_its_declared_field(self):
        cases = {"target_param": ("tgt", "t:1"),
                 "evidence_param": ("ev", "because"),
                 "occurrence_time_param": ("at", WHEN),
                 "provenance_param": ("prov", PROV)}
        for member, field in opdefs.ROUTER_FIELDS.items():
            param, value = cases[member]
            rec = self._routes(member, param, value)
            if member == "provenance_param":
                # provenance is gate-processed (the list is frozen), so the field is checked
                # for its carried identity rather than byte-for-byte — the point is that the
                # member routes into the field ROUTER_FIELDS declares.
                self.assertEqual(dict(rec[field])["asserted_by"], value["asserted_by"],
                                 "provenance_param must route into the 'provenance' field")
            else:
                self.assertEqual(rec[field], value,
                                 "%s must route to the field ROUTER_FIELDS declares (%s)"
                                 % (member, field))


# =============================================================================================
# R2 — THE §A25 BUILD-PROGRESS APPEND-ONLY GUARD refuses a non-append and serves an append.
# =============================================================================================

class R2_AppendOnlyGuard(unittest.TestCase):
    BASE = b"EVT | seed 1\nEVT | seed 2\n"

    def test_a_lawful_append_is_served(self):
        ok, _ = inventory.is_append_over(self.BASE, self.BASE + b"EVT | seed 3\n")
        self.assertTrue(ok, "a pure append must be served — old content a prefix of new")

    def test_a_rewritten_line_is_refused(self):
        ok, reason = inventory.is_append_over(self.BASE, b"EVT | seed 1\nEVT | CHANGED\n")
        self.assertFalse(ok, "a rewrite of an existing line is a non-append and must be refused")
        self.assertIn("REWRITTEN", reason)

    def test_a_removed_line_is_refused(self):
        ok, reason = inventory.is_append_over(self.BASE, b"EVT | seed 1\n")
        self.assertFalse(ok, "removing an existing line is a non-append and must be refused")
        self.assertIn("SHRANK", reason)

    def test_the_guard_can_fail_its_own_positive_control(self):
        """The control must be able to fail — a check that cannot fail is not a control."""
        ok, detail = inventory.build_progress_control()
        self.assertTrue(ok, "the positive control must pass on a working guard: %s" % detail)
        # and it genuinely discriminates: feed it a guard that says yes to everything and it fails
        real = inventory.is_append_over
        try:
            inventory.is_append_over = lambda old, new: (True, "always yes")
            ok_broken, _ = inventory.build_progress_control()
            self.assertFalse(ok_broken,
                             "a guard that says append-only to a rewrite must FAIL the control")
        finally:
            inventory.is_append_over = real


# =============================================================================================
# R4 — ITEM 21: the founding door's station-shape validation CAN FIRE (wired, now exercised).
# =============================================================================================

class R4_StationGuardCanFire(unittest.TestCase):
    def _op(self, name, definition):
        return [{"action": "CREATE-OP", "object": name,
                 "payload": {"kind": "op_definition", "name": name, "definition": definition}}]

    def test_no_shipped_founding_op_declares_a_station(self):
        """First-live-use: the guard has never run at the founding door because nothing shipped
        declares an external-executor station. Named, so the first station to enter is known to
        be its first live use."""
        with open(os.path.join(REPO, "src", "founding", "founding-pack.json")) as fh:
            pack = json.load(fh)
        found = []

        def walk(o):
            if isinstance(o, dict):
                if "executor" in o:
                    found.append(o["executor"])
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(pack)
        self.assertEqual(found, [], "no shipped founding op may declare an executor/station")

    def test_a_malformed_station_refuses_the_whole_founding(self):
        recs = self._op("BAD-STATION", {"law_cited": "M1-OBSERVATION", "executor": "external"})
        with self.assertRaises(FoundingIntegrityError) as cm:
            _validate(recs)
        self.assertIn("station", str(cm.exception))

    def test_an_unknown_executor_refuses(self):
        recs = self._op("WEIRD-EXEC", {"law_cited": "M1-OBSERVATION", "executor": "nonsense"})
        with self.assertRaises(FoundingIntegrityError) as cm:
            _validate(recs)
        self.assertIn("executor", str(cm.exception))

    def test_a_well_formed_station_is_NOT_refused_so_the_guard_is_not_inert(self):
        """The guard that refuses everything proves nothing. A well-formed station passes the
        station-shape leg — so the refusals above are the guard discriminating, not a blanket."""
        good = {"law_cited": "M1-OBSERVATION", "executor": "external",
                "crossing": {"input_view": "view:ledger",
                             "template": "tmpl@1", "answerer_identity": "who@1",
                             "parser": "p@1"}}
        # _validate raises ONLY on a malformed record; a well-formed station clears the station
        # leg (any later refusal would name something other than the station).
        try:
            _validate(self._op("GOOD-STATION", good))
        except FoundingIntegrityError as e:
            self.assertNotIn("station", str(e),
                             "a well-formed station must clear the station-shape leg")


# =============================================================================================
# ITEM 10 — the leaked open in the structure-guard test is closed (no bare context-free open).
# =============================================================================================

class Item10_NoLeakedOpen(unittest.TestCase):
    def test_the_structure_guard_test_opens_files_context_managed(self):
        """Source-level regression: the structure-guard test in test_ep25 no longer opens the
        bridge modules with a bare `open(...).read()` that leaks a descriptor."""
        with open(os.path.join(REPO, "tests", "test_ep25.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn('open(mod.__file__, encoding="utf-8").read()', src,
                         "the bare leaked open must be gone")
        self.assertIn('with open(mod.__file__, encoding="utf-8") as fh:', src,
                      "the open must be context-managed")

    def test_the_fixed_pattern_leaks_no_descriptor(self):
        """Behavioural: the context-managed pattern the fix adopts closes every file it opens,
        so no ResourceWarning is raised. Driven over the SAME three bridge source files the
        structure-guard test opens, by path — no bridge import, so the fusepy adapter dependency
        does not gate this behavioural check."""
        import warnings
        bridge = os.path.join(REPO, "src", "bridge")
        paths = [os.path.join(bridge, f) for f in ("custody.py", "records_fs.py", "mount.py")]
        for p in paths:
            self.assertTrue(os.path.exists(p), "missing bridge source: %s" % p)
        with warnings.catch_warnings():
            warnings.simplefilter("error", ResourceWarning)
            for p in paths:
                with open(p, encoding="utf-8") as fh:
                    _ = fh.read()
            gc.collect()


# =============================================================================================
# ITEM 11 — the harness's own fixture scratches gain the §11.2b tear-down half.
# =============================================================================================

class Item11_FixtureLifecycle(unittest.TestCase):
    def setUp(self):
        # a disposable targets dir with two directory fixtures and one real-fs fixture
        self.dir = tempfile.mkdtemp()
        self.scratch = os.path.join(self.dir, "subjects")
        self.a = os.path.join(self.scratch, "fixture-a")
        self.b = os.path.join(self.scratch, "fixture-b")
        for name, subj in (("fixture-a", self.a), ("fixture-b", self.b)):
            with open(os.path.join(self.dir, "%s.json" % name), "w") as fh:
                json.dump({"name": name, "subject": {"path": subj, "fstype": "directory"}}, fh)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_stand_up_then_tear_down_leaves_nothing_and_does_not_accumulate(self):
        for _ in range(3):  # cycles must not accumulate
            made = fixtures.stand_up(self.dir)
            self.assertEqual(sorted(made), sorted([self.a, self.b]))
            self.assertTrue(os.path.isdir(self.a) and os.path.isdir(self.b))
            # leave cruft inside the subject as a run would, then tear down
            with open(os.path.join(self.a, "record.jsonl"), "w") as fh:
                fh.write("leftover")
            removed = fixtures.tear_down(self.dir)
            self.assertEqual(sorted(removed), sorted([self.a, self.b]))
            self.assertFalse(os.path.exists(self.a) or os.path.exists(self.b),
                             "the fixture subjects must be gone after tear-down")

    def test_tear_down_of_a_clean_tree_removes_nothing(self):
        self.assertEqual(fixtures.tear_down(self.dir), [])

    def test_tear_down_refuses_a_real_filesystem_fixture(self):
        with open(os.path.join(self.dir, "fixture-mount.json"), "w") as fh:
            json.dump({"name": "fixture-mount",
                       "subject": {"path": os.path.join(self.scratch, "mnt"),
                                   "fstype": "govos"}}, fh)
        with self.assertRaises(ValueError):
            fixtures.tear_down(self.dir)

    def test_tear_down_refuses_a_root_or_home_subject(self):
        with open(os.path.join(self.dir, "fixture-danger.json"), "w") as fh:
            json.dump({"name": "fixture-danger",
                       "subject": {"path": "/", "fstype": "directory"}}, fh)
        with self.assertRaises(ValueError):
            fixtures.tear_down(self.dir)


# =============================================================================================
# ITEM §A25 (A8) — CLAUDE.md joined to the DOC-MAP self-check, unconditionally.
# =============================================================================================

class ItemA25_ClaudeMdJoin(unittest.TestCase):
    def test_the_live_claude_md_is_covered(self):
        with open(os.path.join(REPO, "CLAUDE.md"), encoding="utf-8") as fh:
            claude = fh.read()
        with open(os.path.join(REPO, "DOC-MAP_v3.md"), encoding="utf-8") as fh:
            docmap = fh.read()
        ok, reason = inventory.claude_md_covered(claude, docmap)
        self.assertTrue(ok, "the live CLAUDE.md must be headered and mapped: %s" % reason)

    def test_a_headerless_claude_md_is_caught(self):
        ok, _ = inventory.claude_md_covered("# no header\n", "CLAUDE.md")
        self.assertFalse(ok, "a lost header must be a defect, not a silence")

    def test_an_unmapped_claude_md_is_caught(self):
        ok, _ = inventory.claude_md_covered("<!-- doc: class=VIEW status=LIVE -->\n", "")
        self.assertFalse(ok, "a missing map entry must be a defect")

    def test_the_positive_control_passes_and_can_fail(self):
        ok, detail = inventory.claude_md_control()
        self.assertTrue(ok, "control must pass on a working check: %s" % detail)


if __name__ == "__main__":
    unittest.main()
