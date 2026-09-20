#!/usr/bin/env python3
# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test ·
# RELEASE-4 round 3 (owner order, board :4656 / dispatch :4657): the release's loopback-with-port
# exemption is ONE file (tests/test_p17_honest_state.py, the honest-state test's own socket data) held
# in THREE enforcers — the renderer's rewrite, pushscan's file-scoped allow, and the shipped check's
# refusal row — or the release refuses itself; plus RENDER-NO-GIT guards on the two cases that shell out
# to git. Every verification probe of the round lands here as a regression test (charter). NON-GOAL: no
# offensive capability — release hygiene instruments proving their own agreement, by function. Full
# declaration: SCOPE-STATEMENT.md.
"""Regression battery for RELEASE-4 round 3 (board :4656 / :4657).

ITEM 1 — the loopback exemption, narrowed to ONE file in THREE places:
  A1  render.py, pushscan.py and the EMITTED check name the SAME one basename (the three-place
      agreement; a drift between any two would make the release refuse itself), and the exempt
      source carries exactly the three literals the exemption exists for.
  A2  the renderer's rewrite, synthetic tree: the exempt file keeps its loopback literals RAW and is
      still rewritten under every OTHER rule; every other tests/ file, a near-name file, and every
      tools/ file get the placeholder token.
  A3  the REAL tests/ tree after render: no shipped test but the exempt one carries a raw
      loopback-with-port; the exempt one carries its source's count (three); the rewrite count equals
      the raw count over the non-exempt sources; pushscan over the rendered files raises no loopback
      refusal.
  A4  pushscan: the exempt basename is ALLOWED under the loopback rule in every path form, still
      REFUSED under another rule, and any other file is REFUSED under the loopback rule (the rule can
      fail); the CLI exits 0 / CLEAN over the allowed file and 1 / REFUSED with a plant.
  A5  the emitted check: test_refuses_loopback_port PASSES over a release tree whose exempt file
      carries raw loopback literals, and FAILS naming the leak when any other file does; the whole
      emitted battery passes over a clean synthetic release.
ITEM 2 — RENDER-NO-GIT on two cases only:
  B1  each guarded case SKIPS by name when git is genuinely absent (a PATH with no git binary).
  B2  each guarded case RUNS (no skip) in the lab, where git and the checkout are present.
Every private FORM this file needs is ASSEMBLED at runtime from fragments, so this source never
carries one contiguous — the renderer would rewrite it in the shipped copy and pushscan would refuse
it; the assembled bytes live only in temp files. This module runs in the shipped tree too (it reads
only src/tests/tools and needs git for B2 alone, which skips by name without it).
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELEASE_DIR = os.path.join(ROOT, "tools", "release")
EXEMPT = "test_p17_honest_state.py"
LOOPBACK_RULE = "loopback with a port"          # pushscan's rule name
LOOPBACK_CLASS = "loopback_port"                 # the renderer's / the emitted check's class name
SLOT = b"__LOOPBACK_PORT_EXEMPT_BASENAMES__"     # the battery's substitution slot


def _load(name, filename):
    """Load a release tool from its source WITHOUT writing bytecode. pushscan.py assembles the owner's
    email from fragments so its SOURCE carries no private form, but the compiler constant-folds the
    fragments into one literal in its .pyc; a cached tools/release/__pycache__/pushscan.*.pyc left in
    a rendered tree by this module would then be refused by a directory-form pushscan run after the
    suite. So this loader leaves no cache behind (driven at the round-3 close)."""
    spec = importlib.util.spec_from_file_location(name, os.path.join(RELEASE_DIR, filename))
    mod = importlib.util.module_from_spec(spec)
    was = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = was
    return mod


RENDER = _load("_govos_render_r3", "render.py")
PUSHSCAN = _load("_govos_pushscan_r3", "pushscan.py")
LOOPBACK_RX = next(rx for name, rx, _ in RENDER._tt_class_patterns() if name == LOOPBACK_CLASS)
TOKENS = RENDER.load_placeholder_map()


def _lb(port):
    """A loopback-with-port literal, ASSEMBLED (never contiguous in this source)."""
    return "127.0.0.1" + ":" + str(port)


def _key_path():
    """A private-key path of the key_path class (the renderer's AND pushscan's), ASSEMBLED. Chosen as
    the "other rule" because its placeholder is NOT in the renderer's FORBIDDEN_OUTPUT: in a SHIPPED
    tree the renderer's own forbidden literals have been rewritten to the <HOME>/<PROJECTS> tokens, so
    the shipped render_extra_tree refuses any input carrying those two tokens (a property of shipping
    the renderer through itself, disclosed at the round-3 close; not this unit's subject)."""
    return "~/." + "ssh/id_example"


def _is_rendered_tree(root):
    """True when ROOT is itself a release rendering (the renderer stamps its output at the root)."""
    return os.path.exists(os.path.join(root, "RENDER-STAMP.json"))


def _count_raw(data):
    return len(LOOPBACK_RX.findall(data))


def _write(path, data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


def _read(*parts):
    with open(os.path.join(*parts), "rb") as fh:
        return fh.read()


def _git_history_available():                                          # SKIP RENDER-NO-GIT precondition
    try:
        return subprocess.run(["git", "-C", ROOT, "rev-parse", "--verify", "HEAD"],
                              capture_output=True, timeout=10).returncode == 0
    except Exception:
        return False


_GIT_OK = _git_history_available()

# A minimal seed check.py carrying exactly the anchors inject_refusal_battery needs (the real one is
# the staged seed's; its eight machinery readings are not the subject here).
CHECK_STUB = (
    b"import os\nimport sys\nimport unittest\n\n"
    b"HERE = os.path.dirname(os.path.abspath(__file__))\n\n\n"
    b"class SeedCheck(unittest.TestCase):\n"
    b"    def test_1_machinery(self):\n"
    b"        self.assertTrue(True)\n\n\n"
    b'if __name__ == "__main__":\n'
    b"    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SeedCheck)\n"
    b"    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)\n"
    b"    sys.exit(0 if result.wasSuccessful() else 1)\n"
)

EXEMPT_BODY = "ADDR = %r\nBIND = %r\nRECEIPT = %r\n" % (_lb(0), _lb(0), _lb(443))   # the three, in shape


# =================================================================================================
# A1 — THE THREE PLACES NAME THE SAME ONE FILE
# =================================================================================================

class TestA1ThreePlacesAgree(unittest.TestCase):
    def test_render_and_pushscan_name_the_same_one_file(self):
        self.assertEqual(RENDER.LOOPBACK_PORT_EXEMPT_BASENAMES, (EXEMPT,))
        self.assertEqual(PUSHSCAN.CONTENT_RULE_FILE_EXEMPT, {LOOPBACK_RULE: (EXEMPT,)})   # one rule, one file
        self.assertEqual(tuple(PUSHSCAN.CONTENT_RULE_FILE_EXEMPT[LOOPBACK_RULE]),
                         tuple(RENDER.LOOPBACK_PORT_EXEMPT_BASENAMES))

    def test_the_emitted_check_carries_the_renderers_tuple(self):
        self.assertEqual(RENDER.REFUSAL_BATTERY.count(SLOT), 1)          # exactly one slot in the source
        emitted = RENDER.inject_refusal_battery(CHECK_STUB)
        self.assertNotIn(SLOT, emitted)                                  # filled, not shipped raw
        self.assertIn(b'_REFUSE_EXEMPT = {"loopback_port": '
                      + repr(tuple(RENDER.LOOPBACK_PORT_EXEMPT_BASENAMES)).encode("ascii") + b"}", emitted)
        self.assertIn(b"class ReleaseRefusalRows", emitted)
        self.assertEqual(RENDER.inject_refusal_battery(emitted), emitted)  # idempotent

    def test_the_exempt_source_carries_exactly_its_three_loopback_literals(self):
        # the exemption's whole premise (owner :4656): the honest-state test's ONLY loopback literals
        # are the three named (:69 / :285 / :321 in the estate) — its own data.
        self.assertEqual(_count_raw(_read(ROOT, "tests", EXEMPT)), 3)


# =================================================================================================
# A2 — THE RENDERER'S REWRITE, SYNTHETIC TREE
# =================================================================================================

class TestA2RenderRewrite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="r3-render-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _render(self, files):
        """files: {relpath under a synthetic source root: text}. Renders tests/ and tools/ exactly as
        the release does (render_extra_tree, the shipped patterns and map). Returns (out_root, hits)."""
        src_root = os.path.join(self.tmp, "src_root")
        out_root = os.path.join(self.tmp, "out")
        for rel, text in files.items():
            _write(os.path.join(src_root, rel), text)
        patterns = RENDER._tt_class_patterns()
        hits = {}
        for sub in ("tests", "tools"):
            if os.path.isdir(os.path.join(src_root, sub)):
                _files, h = RENDER.render_extra_tree(sub, src_root, out_root, patterns, TOKENS)
                for k, v in h.items():
                    hits[k] = hits.get(k, 0) + v
        return out_root, hits

    def test_exempt_file_raw_every_other_file_rewritten(self):
        other = "PORT = %r\n" % _lb(2222)
        out, hits = self._render({"tests/" + EXEMPT: EXEMPT_BODY,
                                  "tests/test_other.py": other,
                                  "tests/sub/test_nested.py": other,
                                  "tests/test_p17_honest_state_extra.py": other,   # a NEAR name is not exempt
                                  "tools/x/fwd.py": other})
        token = TOKENS[LOOPBACK_CLASS]
        self.assertEqual(_read(out, "tests", EXEMPT), EXEMPT_BODY.encode("utf-8"))   # byte-identical, raw
        self.assertEqual(_count_raw(_read(out, "tests", EXEMPT)), 3)
        for rel in ("tests/test_other.py", "tests/sub/test_nested.py",
                    "tests/test_p17_honest_state_extra.py", "tools/x/fwd.py"):
            got = _read(out, rel)
            self.assertEqual(_count_raw(got), 0, rel)                    # scrubbed
            self.assertIn(token, got, rel)                               # to the named placeholder
        self.assertEqual(hits.get(LOOPBACK_CLASS), 4)                    # the exempt file's three not counted

    def test_exemption_is_one_rule_not_a_blanket(self):
        body = "ADDR = %r\nKEY = %r\n" % (_lb(0), _key_path())
        out, hits = self._render({"tests/" + EXEMPT: body})
        got = _read(out, "tests", EXEMPT)
        self.assertEqual(_count_raw(got), 1)                             # the loopback literal kept
        self.assertNotIn(_key_path().encode("utf-8"), got)               # the key path rewritten
        self.assertIn(TOKENS["key_path"], got)
        self.assertEqual(hits, {"key_path": 1})


# =================================================================================================
# A3 — THE REAL tests/ TREE AFTER RENDER
# =================================================================================================

class TestA3RealTree(unittest.TestCase):
    def test_after_render_only_the_exempt_test_carries_raw_loopback_and_pushscan_is_clean(self):
        """In the ESTATE: render the real tests/ tree and read the result. In a SHIPPED tree (this
        module ships and runs there): the tree IS the render — read it directly, since the shipped
        renderer refuses its own tokens (see _key_path). Same assertions over the rendered files."""
        tmp = tempfile.mkdtemp(prefix="r3-real-")
        try:
            exempt_rel = "tests/" + EXEMPT
            if _is_rendered_tree(ROOT):
                rendered_root = ROOT
                files = sorted(os.path.join("tests", n) for n in os.listdir(os.path.join(ROOT, "tests"))
                               if n.endswith(".py"))
            else:
                rendered_root = tmp
                files, hits = RENDER.render_extra_tree("tests", ROOT, tmp, RENDER._tt_class_patterns(), TOKENS)
                src_raw = {rel: _count_raw(_read(ROOT, rel)) for rel in files}   # the SAME shipped set
                expected = sum(v for rel, v in src_raw.items() if rel != exempt_rel)
                self.assertGreater(expected, 0)                          # the estate carries raw ones to rewrite
                self.assertEqual(hits.get(LOOPBACK_CLASS, 0), expected)  # eight in the estate at :4656
            self.assertIn(exempt_rel, files)
            leaks = []
            for rel in files:
                data = _read(rendered_root, rel)
                n = _count_raw(data)
                if rel == exempt_rel:
                    self.assertEqual(n, 3)                               # raw, its own three
                elif n:
                    leaks.append(rel)
                refusals, _infos, _allowed = PUSHSCAN.scan_one(rel, data)
                self.assertEqual([r for r in refusals if r[0] == LOOPBACK_RULE], [], rel)
            self.assertEqual(leaks, [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# =================================================================================================
# A4 — PUSHSCAN'S FILE-SCOPED ALLOW
# =================================================================================================

class TestA4Pushscan(unittest.TestCase):
    def test_exempt_basename_allowed_under_the_loopback_rule_in_every_path_form(self):
        data = EXEMPT_BODY.encode("utf-8")
        for rel in ("tests/" + EXEMPT, EXEMPT, "code/tests/" + EXEMPT, "tests\\" + EXEMPT):
            refusals, _infos, allowed = PUSHSCAN.scan_one(rel, data)
            self.assertEqual(refusals, [], rel)
            self.assertEqual([a[0] for a in allowed], [LOOPBACK_RULE], rel)
            self.assertEqual(allowed[0][1], _lb(0), rel)                 # the match is still reported

    def test_any_other_file_is_refused_under_the_loopback_rule(self):
        data = ("PORT = %r\n" % _lb(2222)).encode("utf-8")
        for rel in ("tests/test_other.py", "tests/test_p17_honest_state_extra.py", "tools/release/x.py"):
            refusals, _infos, allowed = PUSHSCAN.scan_one(rel, data)
            self.assertEqual([r[0] for r in refusals], [LOOPBACK_RULE], rel)
            self.assertEqual(allowed, [], rel)

    def test_exempt_file_still_refused_under_another_rule(self):
        data = ("ADDR = %r\nKEY = %r\n" % (_lb(0), _key_path())).encode("utf-8")
        refusals, _infos, allowed = PUSHSCAN.scan_one("tests/" + EXEMPT, data)
        self.assertEqual([r[0] for r in refusals], ["private key path"])
        self.assertEqual([a[0] for a in allowed], [LOOPBACK_RULE])

    def test_cli_clean_over_the_allowed_file_then_refused_with_a_plant(self):
        tmp = tempfile.mkdtemp(prefix="r3-pushscan-")
        try:
            _write(os.path.join(tmp, "tests", EXEMPT), EXEMPT_BODY)
            _write(os.path.join(tmp, "tests", "test_clean.py"), "X = 1\n")
            cmd = [sys.executable, os.path.join(RELEASE_DIR, "pushscan.py"), tmp]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            out = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, out)
            self.assertIn("CLEAN", out)
            self.assertIn("0 refusal(s)", out)
            self.assertIn("ALLOWED", out)                                # the allow is visible, never silent
            self.assertIn("tests/" + EXEMPT, out)
            self.assertIn("1 file(s) under a file-scoped allow", out)
            _write(os.path.join(tmp, "tests", "test_leak.py"), "PORT = %r\n" % _lb(2222))   # PLANT
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            out = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 1, out)
            self.assertIn("REFUSE", out)
            self.assertIn("test_leak.py", out)
            self.assertIn(LOOPBACK_RULE, out)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# =================================================================================================
# A5 — THE EMITTED CHECK'S ROW
# =================================================================================================

class TestA5EmittedCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="r3-check-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _release(self, leak_port=None):
        """A synthetic rendered tree: the emitted check.py at the root, the exempt test carrying its raw
        literals, another test carrying only the placeholder (as the renderer leaves it), and an
        optional PLANT — a third test carrying a raw loopback literal."""
        rel = tempfile.mkdtemp(dir=self.tmp)
        _write(os.path.join(rel, "check.py"), RENDER.inject_refusal_battery(CHECK_STUB))
        _write(os.path.join(rel, "tests", EXEMPT), EXEMPT_BODY)
        _write(os.path.join(rel, "tests", "test_other.py"),
               "PORT = %r\n" % TOKENS[LOOPBACK_CLASS].decode("ascii"))
        _write(os.path.join(rel, "src", "mod.py"), "VALUE = 1\n")
        _write(os.path.join(rel, "tools", "util.py"), "HELPER = 2\n")
        if leak_port is not None:
            _write(os.path.join(rel, "tests", "test_leak.py"), "PORT = %r\n" % _lb(leak_port))
        return rel

    def _run_row(self, rel):
        proc = subprocess.run([sys.executable, "-m", "unittest", "-v",
                               "check.ReleaseRefusalRows.test_refuses_loopback_port"],
                              cwd=rel, capture_output=True, text=True, timeout=120)
        return proc.returncode, proc.stdout + proc.stderr

    def test_row_passes_with_the_exempt_files_raw_literals_in_the_tree(self):
        rc, out = self._run_row(self._release())
        self.assertEqual(rc, 0, out)
        self.assertIn("test_refuses_loopback_port", out)
        self.assertIn("OK", out)

    def test_row_fails_naming_a_leak_in_any_other_file(self):
        rc, out = self._run_row(self._release(leak_port=2222))
        self.assertNotEqual(rc, 0, out)                                  # the row can fail
        self.assertIn("leaked into the shipped tree", out)
        self.assertIn("test_leak.py", out)

    def test_whole_emitted_battery_passes_over_a_clean_synthetic_release(self):
        rel = self._release()
        proc = subprocess.run([sys.executable, os.path.join(rel, "check.py")],
                              cwd=rel, capture_output=True, text=True, timeout=120)
        out = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("Ran 9 tests", out)                                # 1 stub reading + 8 refusal rows


# =================================================================================================
# B — RENDER-NO-GIT ON THE TWO GUARDED CASES
# =================================================================================================

GUARDED = (
    ("tests.test_p9_rule_citation",
     "TestCitationThroughTheLocalCopyNoNewField."
     "test_A4_A5_the_founding_pack_is_byte_unchanged_no_new_field_no_founding"),
    ("tests.test_vt4_overlap_checks", "TestNoFounding.test_the_founding_pack_is_byte_unchanged"),
)


def _run_case(module, case, env):
    proc = subprocess.run([sys.executable, "-m", "unittest", "-v", "%s.%s" % (module, case)],
                          cwd=ROOT, env=env, capture_output=True, text=True, timeout=600)
    return proc.returncode, proc.stdout + proc.stderr


class TestBRenderNoGitGuards(unittest.TestCase):
    def _env(self, with_git):
        env = dict(os.environ)
        env["PYTHONPATH"] = ROOT + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        if not with_git:
            env["PATH"] = self.nogit                                     # an existing, EMPTY directory
        return env

    def setUp(self):
        self.nogit = tempfile.mkdtemp(prefix="r3-nogit-")

    def tearDown(self):
        shutil.rmtree(self.nogit, ignore_errors=True)

    def test_B1_each_guarded_case_skips_by_name_when_git_is_absent(self):
        for module, case in GUARDED:
            rc, out = _run_case(module, case, self._env(with_git=False))
            self.assertEqual(rc, 0, out)
            self.assertIn("Ran 1 test", out, out)
            self.assertIn("skipped=1", out, out)                         # skipped, not errored
            self.assertIn("SKIP RENDER-NO-GIT", out, out)                # by name

    @unittest.skipUnless(_GIT_OK, "SKIP RENDER-NO-GIT: git unavailable — the in-lab half needs a git checkout")
    def test_B2_each_guarded_case_runs_in_the_lab(self):
        for module, case in GUARDED:
            rc, out = _run_case(module, case, self._env(with_git=True))
            self.assertEqual(rc, 0, out)
            self.assertIn("Ran 1 test", out, out)
            self.assertNotIn("skipped", out, out)                        # it RAN
            self.assertIn("OK", out, out)


if __name__ == "__main__":
    unittest.main()
