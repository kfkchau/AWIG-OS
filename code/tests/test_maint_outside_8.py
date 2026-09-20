#!/usr/bin/env python3
# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test ·
# EP-MAINT-OUTSIDE-8: the public suite runner (render.py RUNNER_SRC, emitted as run_public_suite.py)
# must PROVE what it prints. This test drives the ACTUAL emitted runner over hermetic synthetic
# release fixtures built to the renderer's own stamp/manifest schema (render.tree_checksum reused for
# byte-exact compatibility). Every check is shown able to FAIL: each plant flips the runner from a
# clean pass to a named refusal, so a downloader's green means what it says. Authored from the round-3
# read (ARCHI-READ-3.md F4) and OUR OWN code (tools/release/render.py); the reviewer's material was
# NOT read and NOT run. NON-GOAL: no offensive capability — a release instrument proving its own pins,
# by function. Full declaration: SCOPE-STATEMENT.md.
"""Regression battery for the emitted public-suite runner.

A1  inventory enforced against the stamp — an added or missing tree file is refused (+ plant).
A2  the three tree checksums RECOMPUTED from disk and compared — a changed byte, and a lone
    stamp-vs-recompute drift, are both refused (+ plants).
A3  an empty discovered collection, and an empty skip list, are refused — never a vacuous pass.
A4  each module's stdout/stderr kept in a per-module log beside the run — a failing module's
    output is readable after the run.
A5  discovery is test_*.py ONLY — helpers such as era_pin.py are not run as modules.
A6  test CASES and within-module skips are reported APART from module exit codes.
Positive control: the runner PASSES (exit 0) on a clean synthetic release — the gate is not a
constant refusal.
"""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER_PY = os.path.join(ROOT, "tools", "release", "render.py")


def _load_render():
    spec = importlib.util.spec_from_file_location("_govos_render_ep8", RENDER_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RENDER = _load_render()

# --- synthetic module bodies (self-contained unittest, import nothing from src) ---------------------
ALPHA = (
    "import unittest\n"
    "class Alpha(unittest.TestCase):\n"
    "    def test_a(self): self.assertTrue(True)\n"
    "    def test_b(self): self.assertTrue(True)\n"
    "    def test_c(self): self.assertTrue(True)\n"
    "if __name__ == '__main__':\n"
    "    unittest.main()\n"
)
BETA = (
    "import unittest\n"
    "class Beta(unittest.TestCase):\n"
    "    def test_ok(self): self.assertTrue(True)\n"
    "    def test_bad(self): self.assertEqual(1, 2)  # this case fails\n"
    "if __name__ == '__main__':\n"
    "    unittest.main()\n"
)
# would exit 3 (a loud failure) if it were ever RUN — it is in the skip list, so it must not be.
SKIPME = "import sys\nsys.exit(3)\n"
# a NON-test_ helper: it must never be discovered or run as a module.
ERA_PIN = "HELPER = 42  # a tests/ helper, not a test module\n"


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _write(path, data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


class RunnerFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ep8-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- build a valid synthetic release, keyed exactly as the renderer keys each tree ---------------
    def build(self, test_modules, write_census=False):
        """test_modules: {filename: body} written under tests/. The era_pin helper and the skip list
        are always present; the census scaffolding is optional (it too is a test_*.py, so when present
        the runner discovers and runs it — mirroring a real release). Returns the release root. A
        clean tree passes the runner's integrity gate."""
        rel = tempfile.mkdtemp(dir=self.tmp)
        src_bytes = {"mod.py": b"VALUE = 1\n"}                       # src keys carry NO prefix
        tools_bytes = {"tools/util.py": b"HELPER = 2\n"}            # tools keys carry their prefix
        tests_bytes = {"tests/era_pin.py": ERA_PIN.encode("utf-8")}  # tests keys carry their prefix
        for name, body in test_modules.items():
            tests_bytes["tests/" + name] = body.encode("utf-8")
        for key, body in src_bytes.items():
            _write(os.path.join(rel, "src", key), body)
        for key, body in tools_bytes.items():
            _write(os.path.join(rel, key), body)
        for key, body in tests_bytes.items():
            _write(os.path.join(rel, key), body)
        # scaffolding emitted into tests/ AFTER the checksums — excluded from checksums and inventory
        _write(os.path.join(rel, "tests", "RELEASE-SKIP-LIST.txt"),
               "# module\treason\tprivate dependency\n"
               "test_skipme.py\tneeds a private estate fixture\t/estate/private/thing\n")
        if write_census:
            _write(os.path.join(rel, "tests", "test_release_census.py"),
                   "# emitted census placeholder\n")
        src_map = {k: _sha(v) for k, v in src_bytes.items()}
        tools_map = {k: _sha(v) for k, v in tools_bytes.items()}
        tests_map = {k: _sha(v) for k, v in tests_bytes.items()}
        tc = {"src": RENDER.tree_checksum(src_map),
              "tests": RENDER.tree_checksum(tests_map),
              "tools": RENDER.tree_checksum(tools_map)}
        # a '../' root-extra entry in files -> the runner must FILTER it out of the src inventory
        files = dict(src_map)
        files["../FREEZE.txt"] = _sha(b"freeze\n")
        stamp = {"files": files, "tests_files": tests_map, "tools_files": tools_map,
                 "tree_checksums": tc}
        _write(os.path.join(rel, "RENDER-STAMP.json"), json.dumps(stamp, indent=1, sort_keys=True))
        manifest = {"tree_checksums": tc,
                    "skip_list": [{"module": "test_skipme.py",
                                   "reason": "needs a private estate fixture",
                                   "private_file": "/estate/private/thing"}]}
        _write(os.path.join(rel, "RELEASE-TESTS-MANIFEST.json"),
               json.dumps(manifest, indent=1, sort_keys=True))
        _write(os.path.join(rel, "run_public_suite.py"), RENDER.RUNNER_SRC)
        return rel

    def standard(self):
        return self.build({"test_alpha.py": ALPHA, "test_beta.py": BETA, "test_skipme.py": SKIPME})

    def run_runner(self, rel):
        proc = subprocess.run([sys.executable, os.path.join(rel, "run_public_suite.py")],
                              capture_output=True, text=True)
        return proc.returncode, proc.stdout + proc.stderr

    # ================================================================================================
    # Positive control — the gate is NOT a constant refusal
    # ================================================================================================
    def test_00_clean_all_pass_exits_zero(self):
        rel = self.build({"test_alpha.py": ALPHA, "test_skipme.py": SKIPME})
        rc, out = self.run_runner(rel)
        self.assertEqual(rc, 0, out)
        self.assertNotIn("REFUSED", out)
        self.assertIn("RECOMPUTED & CONFIRMED", out)
        self.assertIn("modules: 1 ran (1 passed, 0 failed), 1 skipped", out)

    # ================================================================================================
    # A1 — INVENTORY ENFORCED AGAINST THE STAMP
    # ================================================================================================
    def test_A1_added_tree_file_refused(self):
        rel = self.standard()
        # baseline: the clean tree does NOT refuse on inventory
        rc0, out0 = self.run_runner(rel)
        self.assertNotIn("absent from the release inventory", out0)
        # PLANT: a file present in the tree but absent from the inventory
        _write(os.path.join(rel, "src", "sneaked_in.py"), b"SURPRISE = 1\n")
        rc, out = self.run_runner(rel)
        self.assertEqual(rc, 2, out)
        self.assertIn("REFUSED", out)
        self.assertIn("src tree carries files absent from the release inventory", out)
        self.assertIn("sneaked_in.py", out)  # src keys carry no prefix, as the renderer keys them

    def test_A1_missing_tree_file_refused(self):
        rel = self.standard()
        # PLANT: a file the inventory names, removed from the tree
        os.remove(os.path.join(rel, "tests", "era_pin.py"))
        rc, out = self.run_runner(rel)
        self.assertEqual(rc, 2, out)
        self.assertIn("is missing files the release inventory names", out)
        self.assertIn("tests/era_pin.py", out)

    # ================================================================================================
    # A2 — TREE CHECKSUMS RECOMPUTED AND COMPARED
    # ================================================================================================
    def test_A2_tampered_byte_refused(self):
        rel = self.standard()
        # PLANT: change one byte of a shipped file, leave the stamp untouched
        p = os.path.join(rel, "src", "mod.py")
        with open(p, "wb") as fh:
            fh.write(b"VALUE = 2\n")  # was 1
        rc, out = self.run_runner(rel)
        self.assertEqual(rc, 2, out)
        self.assertIn("a byte was changed", out)
        self.assertIn("src/mod.py", out)

    def test_A2_recompute_vs_stamp_drift_refused(self):
        rel = self.standard()
        # PLANT: files intact, but BOTH stamp and manifest pin a wrong src tree checksum. The per-file
        # shas still match, so ONLY the recompute-vs-pin roll-up can catch this.
        wrong = "0" * 64
        for name in ("RENDER-STAMP.json", "RELEASE-TESTS-MANIFEST.json"):
            path = os.path.join(rel, name)
            with open(path) as fh:
                doc = json.load(fh)
            doc["tree_checksums"]["src"] = wrong
            _write(path, json.dumps(doc, indent=1, sort_keys=True))
        rc, out = self.run_runner(rel)
        self.assertEqual(rc, 2, out)
        self.assertIn("tree checksum recomputed", out)
        self.assertIn("the stamp pins", out)

    def test_A2_manifest_disagrees_with_stamp_refused(self):
        rel = self.standard()
        # PLANT: the manifest's checksums no longer equal the stamp's
        path = os.path.join(rel, "RELEASE-TESTS-MANIFEST.json")
        with open(path) as fh:
            doc = json.load(fh)
        doc["tree_checksums"]["tests"] = "f" * 64
        _write(path, json.dumps(doc, indent=1, sort_keys=True))
        rc, out = self.run_runner(rel)
        self.assertEqual(rc, 2, out)
        self.assertIn("manifest tree_checksums disagree with the stamp", out)

    # ================================================================================================
    # A3 — EMPTY COLLECTION / EMPTY SKIP LIST REFUSED
    # ================================================================================================
    def test_A3_empty_collection_refused(self):
        # a tree whose inventory is CONSISTENT but has no test_*.py to run
        rel = self.build({})  # only era_pin helper + scaffolding
        rc, out = self.run_runner(rel)
        self.assertEqual(rc, 2, out)
        self.assertIn("no test_*.py module discovered", out)

    def test_A3_empty_skip_list_refused(self):
        rel = self.standard()
        # PLANT: the skip list emptied of entries (a comment only) — the integrity gate is unaffected
        # (the skip list is scaffolding), so the empty-skip check itself must fire.
        _write(os.path.join(rel, "tests", "RELEASE-SKIP-LIST.txt"), "# only a comment, no entries\n")
        rc, out = self.run_runner(rel)
        self.assertEqual(rc, 2, out)
        self.assertIn("the skip list is empty", out)

    # ================================================================================================
    # A4 — PER-MODULE LOGS KEPT
    # ================================================================================================
    def test_A4_failing_module_output_kept_in_log(self):
        rel = self.standard()
        rc, out = self.run_runner(rel)
        self.assertEqual(rc, 1, out)  # beta fails a case -> the module exits non-zero
        logdir = os.path.join(rel, "public-suite-logs")
        self.assertTrue(os.path.isdir(logdir), "per-module log dir not created")
        betalog = os.path.join(logdir, "test_beta.py.log")
        self.assertTrue(os.path.exists(betalog), "failing module's log absent")
        with open(betalog, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        self.assertIn("test_bad", body)          # the failing case's output survived the run
        self.assertIn("FAIL", body)
        alphalog = os.path.join(logdir, "test_alpha.py.log")
        self.assertTrue(os.path.exists(alphalog), "passing module's log absent")

    # ================================================================================================
    # A5 — DISCOVERY test_*.py ONLY
    # ================================================================================================
    def test_A5_helper_not_run_as_module(self):
        rel = self.standard()
        rc, out = self.run_runner(rel)
        logdir = os.path.join(rel, "public-suite-logs")
        # the helper is never run: no log, and it is not counted among the modules
        self.assertFalse(os.path.exists(os.path.join(logdir, "era_pin.py.log")),
                         "helper era_pin.py was run as a module")
        # only test_alpha and test_beta ran (test_skipme skipped, era_pin not discovered)
        self.assertIn("modules: 2 ran (1 passed, 1 failed), 1 skipped", out)
        self.assertTrue(os.path.exists(os.path.join(logdir, "test_alpha.py.log")),
                        "a real test module was not run")

    def test_A5_test_prefixed_module_is_discovered(self):
        # positive half: a test_*.py IS discovered and run
        rel = self.build({"test_alpha.py": ALPHA, "test_skipme.py": SKIPME})
        rc, out = self.run_runner(rel)
        self.assertTrue(os.path.exists(os.path.join(rel, "public-suite-logs", "test_alpha.py.log")))

    # ================================================================================================
    # A6 — CASES AND SKIPS REPORTED APART FROM MODULE EXITS
    # ================================================================================================
    def test_A6_cases_distinct_from_module_exits(self):
        rel = self.standard()
        rc, out = self.run_runner(rel)
        # 2 modules ran, but 5 CASES (alpha 3 + beta 2) — a module is not one case
        self.assertIn("modules: 2 ran (1 passed, 1 failed), 1 skipped", out)
        self.assertIn("cases:   5 ran, 1 failed, 0 errored, 0 skipped within modules", out)


if __name__ == "__main__":
    unittest.main()
