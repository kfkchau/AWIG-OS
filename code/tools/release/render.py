#!/usr/bin/env python3
"""THE RELEASE RENDERING — the AWIG OS tree as a BUILD OUTPUT (planning/exec/RELEASE-NAMING-AND-
HEADERS-DRAFT.md v2; charter 'THE RELEASE RENDERING', 2026-09-07).

Reads the estate's `src/` at a NAMED COMMIT (`--commit <sha>`, obtained via `git archive` into a
temp tree — never the working tree) and writes `awig-deploy/awig-code/src/`:
  1. the public licensing map's per-file header (verbatim, awig-os/LICENSING.md §4) on every .py;
  2. `gov-os` -> `AWIG OS` in COMMENTS and DOCSTRINGS only, located by the tokenizer + AST — never a
     text replace (code strings, identifiers and byte constants are untouched);
  3. the environment names read ADDITIVELY: `AWIGOS_<X>` first, `GOVOS_<X>` second (kernel/commit.py's
     two reads), so past tests that set the old names pass unchanged against the rendered tree;
  4. REFUSES (exit 2, naming file:line) to emit any output carrying this laptop's paths, a seat
     transcript path, or a file lacking the header; REFUSES if a never-touch item (the DEPARTURE
     byte marker, the guest-module wire identifiers) would change;
  5. STAMPS the output: RENDER-STAMP.json (source commit, this tool's sha256, per-file sha256s).

WHY --commit (archi :3239): the release must render from a PINNED COMMIT, never the working tree.
Autosync commits in-flight source (e.g. half-built crypto) into HEAD, so a working-tree render would
ship it. `--commit <sha>` extracts THAT commit's tree (src + the extras' sources) via `git archive`
into a temp dir and renders from there; the stamp/FREEZE name that commit. Without --commit the tool
keeps the working-tree behaviour (back-compat); the release always passes --commit.

Deterministic: same source commit + same tool -> same bytes (the stamp's generated_utc is the only
non-source byte, and it is not part of any byte-compare — see tools/release/check.py C1). No clock
inside the rendered files (the stamp carries the date; the files do not). Never edits `src/`,
`tests/`, `tools/` (this file is new under tools/release/). Run from the repo root:
  python3 tools/release/render.py [--commit SHA] [--extras-commit SHA] [--out DIR]

--extras-commit (archi :3250) renders the EXTRAS (README source, vendored licences, staged seed
scripts) from a SEPARATE pinned commit, so src/ can ship from a crypto-free commit while the extras
ship from a later commit carrying the corrected licence map. It defaults to --commit's value, so a
single-commit render is unchanged. Both commits are named in FREEZE.txt and RENDER-STAMP.json.
"""
import ast
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO, "src")
OUT_DEFAULT = os.path.join(REPO, "awig-deploy", "awig-code")

HEADER = """# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""

OLD_NAME, NEW_NAME = "gov-os", "AWIG OS"

# NEVER-TOUCH: byte constants and wire identifiers that must survive rendering byte-identical.
NEVER_TOUCH = [
    b'b"\\x00gov-os:content-departed-by-handover\\x00"',   # the DEPARTURE marker (record format)
    b"govos_fill_super", b"govos_call_lock",             # guest kernel-module wire identifiers
]
FORBIDDEN_OUTPUT = [b"<HOME>", b"<PROJECTS>"]

# ---------------------------------------------------------------------------
# EP-RELEASE-TESTS: shipping tests/ and tools/ beside src/ (the second release).
# The renderer git-archives the pinned commit and, under --with-tests-tools, emits
# tests/ and tools/ under the exclusions below, rewriting every PRIVATE LITERAL to a
# NAMED placeholder at render (never editing a past test or tool file). The eight
# classes are the ones pushscan refuses; the placeholder NAMES (never a private value)
# live in the shipped map tools/release/placeholder-map.json.
MAP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "placeholder-map.json")

# Directories/files NEVER shipped (RELEASE-C4-PLAN §8 / EP §5). A tool that READS planning/
# is excluded too; the one such tool is tools/brief/briefcheck.py (named), and a render-time
# guard below refuses to ship any tool whose bytes open a planning/ path, so a new one cannot
# leak silently.
EXCLUDE_DIRS = ("tests/archive", "tools/transport", "tools/comms")
EXCLUDE_TOOL_FILES = ("tools/brief/briefcheck.py",       # reads planning/ (verified)
                      "tools/postman/s3drive.py")        # reads planning/ (verified, absolute EP path)


def _tt_class_patterns():
    """The eight private-literal classes as (name, compiled byte-regex, wrap_quotes). Each pattern
    matches the PRIVATE FORM and is specific enough not to match its own placeholder token (the
    tokens carry no '/home/', '@gmail', '127.0.0.1:<n>', ':kfkchau/gov-os' etc.), so a rewritten
    byte never re-matches and the A2 grep over the shipped tree is EMPTY. repository_url is scoped
    to the PRIVATE forms (the ssh clone form and the codename repo) so the PUBLIC repo url is left
    intact. wrap_quotes=True marks a match that INCLUDES its surrounding double-quotes (an argv
    element like "<SSH-INVOCATION>"); its token is emitted QUOTED ("<...>") so the shipped file
    stays valid Python. Every other pattern matches INSIDE a string, so the bare token keeps the
    string valid. Applied in this order (most specific first)."""
    return [
        ("ssh_invocation", re.compile(rb'"ssh",\s*"-p",\s*"\d+"'), True),
        ("ssh_invocation", re.compile(rb'\bssh\s+-p\s+\d+'), False),
        ("guest_user", re.compile(rb'[a-z][a-z0-9_-]*@127\.0\.0\.1'), False),
        ("loopback_port", re.compile(rb'127\.0\.0\.1:\d+'), False),
        ("key_path", re.compile(rb'~?/?\.ssh/[A-Za-z0-9_.-]+'), False),
        ("repository_url", re.compile(rb'(?:git@github\.com:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+|github\.com/kfkchau/gov-os)'), False),
        ("claude_projects_path", re.compile(rb'\<PROJECTS>[A-Za-z0-9_./-]*'), False),
        ("private_email", re.compile(rb'[A-Za-z0-9._%+-]+@gmail\.com'), False),
        ("home_laptop_path", re.compile(rb'/home/[A-Za-z0-9_.-]+'), False),
    ]


def load_placeholder_map():
    """class -> placeholder TOKEN (bytes), from the shipped map. Asserts the map's class set equals
    the renderer's pattern set (a drift between the two would ship an un-covered class)."""
    m = json.load(open(MAP_PATH))["classes"]
    pat_names = {n for n, _, _ in _tt_class_patterns()}
    if set(m) != pat_names:
        fail("placeholder-map.json classes %s != renderer classes %s" % (sorted(m), sorted(pat_names)))
    return {k: v.encode("utf-8") for k, v in m.items()}


def rewrite_private(data, patterns, tokens):
    """Rewrite every private-literal match in `data` to its class token. Returns (out, hits) where
    hits is {class: count}. The tokens contain no private form, so one pass suffices."""
    hits = {}
    out = data
    for name, rx, wrap in patterns:
        repl = (b'"' + tokens[name] + b'"') if wrap else tokens[name]
        n = 0

        def _sub(_m, repl=repl):
            nonlocal n
            n += 1
            return repl
        out = rx.sub(_sub, out)
        if n:
            hits[name] = hits.get(name, 0) + n
    return out, hits


def tree_checksum(files):
    """A deterministic checksum over a rendered tree: sha256 of sorted 'relpath\\0sha256\\n' lines.
    `files` is {relpath: sha256hex}. Order-independent, content-bound."""
    h = hashlib.sha256()
    for rel in sorted(files):
        h.update(rel.encode("utf-8"))
        h.update(b"\x00")
        h.update(files[rel].encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def _excluded(rel):
    """True if a tests/ or tools/ relpath must not ship (EP §5 exclusions)."""
    r = rel.replace(os.sep, "/")
    if any(r == d or r.startswith(d + "/") for d in EXCLUDE_DIRS):
        return True
    if r in EXCLUDE_TOOL_FILES:
        return True
    if r.endswith(".jsonl"):
        return True
    if r.startswith("tools/postman/") and r.endswith(".json"):
        return True
    return False


def render_extra_tree(subdir, src_root, out_root, patterns, tokens):
    """Walk src_root/<subdir> (tests or tools), apply the exclusions, rewrite private literals in
    every shipped file's bytes to placeholder tokens, write to out_root/<subdir>. Returns
    (files {relpath_under_root: sha256hex}, hits {class: count}). A guard refuses to ship a tool
    that opens a planning/ path (defence in depth over the named exclusion)."""
    base = os.path.join(src_root, subdir)
    files = {}
    total_hits = {}
    for root, dirs, names in os.walk(base):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in sorted(names):
            if name.endswith((".pyc", ".pyo")):
                continue
            path = os.path.join(root, name)
            rel_sub = os.path.relpath(path, base).replace(os.sep, "/")
            rel = subdir + "/" + rel_sub
            if _excluded(rel):
                continue
            with open(path, "rb") as fh:
                data = fh.read()
            if subdir == "tools" and rel not in EXCLUDE_TOOL_FILES:
                if re.search(rb'(?:open|Path|read_text|read_bytes|glob|check_output|run)\([^)\n]{0,60}planning/', data):
                    fail("%s reads planning/ but is not excluded — add it to EXCLUDE_TOOL_FILES" % rel)
            out, hits = rewrite_private(data, patterns, tokens)
            for k, v in hits.items():
                total_hits[k] = total_hits.get(k, 0) + v
            for bad in FORBIDDEN_OUTPUT:  # defence: the rewrite must have removed these
                if bad in out:
                    idx = out.index(bad)
                    fail("%s:%d still carries forbidden output %r after rewrite"
                         % (rel, out[:idx].count(b"\n") + 1, bad.decode()))
            dest = os.path.join(out_root, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as fh:
                fh.write(out)
            files[rel] = hashlib.sha256(out).hexdigest()
    return files, total_hits


# SKIP_TABLE — the shipped test modules that CANNOT run in the public tree, each with a reason and
# the private dependency it names (EP §2 B5). Determined by running the shipped suite over the
# rendered tree: a module reads a file outside src/tests/tools, reads the estate git history, or
# reaches the guest/conformance fixtures by an absolute estate path. The public runner skips exactly
# these; the census asserts this SET (add-one/drop-one REDS). Every OTHER module runs and MUST be
# green. Filled from the empirical classification (see the close's skip census).
SKIP_TABLE = [
    # (module_filename, reason, private_dependency)
    ('ep24b_differential.py', 'reads a private estate file outside the shipped src/tests/tools', 'design/28-TARGET-STATE-HOST-KERNEL.md'),
    ('test_checkvocab.py', 'reads a private estate file outside the shipped src/tests/tools', 'design/28-TARGET-STATE-HOST-KERNEL.md'),
    ('test_ep14.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep16.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep24.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep24d.py', 'reaches the conformance fixtures by an absolute estate path', 'tools/conformance/fixtures (absolute estate path)'),
    ('test_ep25.py', 'needs the fusepy adapter, a third-party package outside the shipped stdlib core', 'fusepy (third-party adapter, not shipped)'),
    ('test_ep28.py', 'needs the fusepy adapter, a third-party package outside the shipped stdlib core', 'fusepy (third-party adapter, not shipped)'),
    ('test_ep28_w8.py', 'reads a private estate file outside the shipped src/tests/tools', 'planning/vm/govosfs/govosfs.c'),
    ('test_ep28c_w4b.py', 'reads a private estate file outside the shipped src/tests/tools', 'planning/vm/govosfs/govosfs.c'),
    ('test_ep28c_w4d.py', 'asserts an estate-host property (the runner kernel differs from the pinned guest)', 'the pinned guest kernel'),
    ('test_ep28c_w4e.py', 'reads a private estate file outside the shipped src/tests/tools', 'planning/vm/govosfs/govosfs.c'),
    ('test_ep28c_w4e_c.py', 'reads a private estate file outside the shipped src/tests/tools', 'planning/vm/govosfs/govosfs.c'),
    ('test_ep28c_w4e_c2.py', 'reads a private estate file outside the shipped src/tests/tools', 'planning/vm/govosfs/govosfs.c'),
    ('test_ep28c_w8.py', 'reads a private estate file outside the shipped src/tests/tools', 'planning/vm/govosfs/govosfs.c'),
    ('test_ep28e_w2.py', 'needs the fusepy adapter, a third-party package outside the shipped stdlib core', 'fusepy (third-party adapter, not shipped)'),
    ('test_ep28e_w5.py', 'needs the fusepy adapter, a third-party package outside the shipped stdlib core', 'fusepy (third-party adapter, not shipped)'),
    ('test_ep28f.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep28h.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep28i.py', 'reads a private estate file outside the shipped src/tests/tools', 'planning/build/BUILD-PROGRESS_v3.md'),
    ('test_ep28j.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep28k.py', 'reads a private estate file outside the shipped src/tests/tools', 'planning/build/BUILD-PROGRESS_v3.md'),
    ('test_ep28m.py', 'reaches the conformance fixtures by an absolute estate path', 'tools/conformance/fixtures (absolute estate path)'),
    ('test_ep28m_census.py', 'reaches the conformance fixtures by an absolute estate path', 'tools/conformance/fixtures (absolute estate path)'),
    ('test_ep28n.py', 'reads a private estate file outside the shipped src/tests/tools', 'planning/build/BUILD-PROGRESS_v3.md'),
    ('test_ep28n2.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep28p.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep28r.py', 'reads a private estate file outside the shipped src/tests/tools', 'planning/vm/govosfs/govosfs.c'),
    ('test_ep28z.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep28zd.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep29.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep30.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep30_c1.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep30_c2.py', 'reads a private estate file outside the shipped src/tests/tools', 'DOC-MAP_v3.md'),
    ('test_ep30_c3.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep30_c4.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep30_c4w.py', 'reads a private estate file outside the shipped src/tests/tools', 'design/28-TARGET-STATE-HOST-KERNEL.md'),
    ('test_ep30_c6.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep30_k1.py', 'reads a private estate file outside the shipped src/tests/tools', 'design/36-CAMPAIGN-3-DEPTH.md'),
    ('test_ep30_k2.py', 'reads a private estate file outside the shipped src/tests/tools', 'design/28-TARGET-STATE-HOST-KERNEL.md'),
    ('test_ep31.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep32.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep33a.py', 'reads a private estate file outside the shipped src/tests/tools', 'CLAUDE.md'),
    ('test_ep35.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep36.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep37.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_ep39.py', 'reads the estate git history (the public tree carries no .git)', 'the estate .git history'),
    ('test_founding_is_logged.py', 'reads a private estate file outside the shipped src/tests/tools', 'planning/build/BUILD-PROGRESS_v3.md'),
]

# The refusal battery injected into the shipped check.py (EP §2 B3): one planted row per class. Each
# row proves the scanner finds NO private form in the shipped src/tests/tools AND refuses a planted
# SYNTHETIC example of its class (a check that can fail). The synthetic strings are assembled from
# fragments so this source never carries a contiguous private FORM (pushscan stays clean over the
# shipped set); the temp input the row writes carries it, and the scanner is watched refusing it.
REFUSAL_BATTERY = rb'''

# --- EP-RELEASE-TESTS: the eight private-literal refusal rows (injected at render) --------------
import re as _re
import tempfile as _tempfile

_REFUSE = [
    ("home_laptop_path", _re.compile(rb"/home/[A-Za-z0-9_.-]+"), (b"/home/", b"exampleuser")),
    ("ssh_invocation", _re.compile(rb'(?:"ssh",\s*"-p",\s*"\d+"|\bssh\s+-p\s+\d+)'), (b"ssh -p ", b"2200 example@dest")),
    ("key_path", _re.compile(rb"~?/?\.ssh/[A-Za-z0-9_.-]+"), (b"~/.ssh/", b"example_key")),
    ("loopback_port", _re.compile(rb"127\.0\.0\.1:\d+"), (b"127.0.0.1:", b"8080")),
    ("guest_user", _re.compile(rb"[a-z][a-z0-9_-]*@127\.0\.0\.1"), (b"exampleuser@", b"127.0.0.1")),
    ("repository_url", _re.compile(rb"(?:git@github\.com:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+|github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"), (b"git@", b"github.com:example/private.git")),
    ("claude_projects_path", _re.compile(rb"\.claude/" rb"projects[A-Za-z0-9_./-]*"), (b".claude/", b"projects/example")),
    ("private_email", _re.compile(rb"[A-Za-z0-9._%+-]+@gmail\.com"), (b"someone@", b"gmail.com")),
]


def _refuse_scan_bytes(data):
    return {name for name, rx, _ in _REFUSE if rx.search(data)}


def _refuse_scan_trees():
    hits = {}
    for sub in ("src", "tests", "tools"):
        base = os.path.join(HERE, sub)
        if not os.path.isdir(base):
            continue
        for r, ds, ns in os.walk(base):
            ds[:] = [d for d in ds if d != "__pycache__"]
            for n in ns:
                if n.endswith((".pyc", ".pyo")):
                    continue
                for name in _refuse_scan_bytes(open(os.path.join(r, n), "rb").read()):
                    hits.setdefault(name, []).append(os.path.relpath(os.path.join(r, n), HERE))
    return hits


class ReleaseRefusalRows(unittest.TestCase):
    """One planted-refusal row per private-literal class (EP-RELEASE-TESTS A3)."""

    def _row(self, idx):
        name, rx, frags = _REFUSE[idx]
        leaked = _refuse_scan_trees().get(name)
        self.assertIsNone(leaked, "%s leaked into the shipped tree: %s" % (name, leaked))
        with _tempfile.NamedTemporaryFile() as fh:
            fh.write(b"harmless line\n" + frags[0] + frags[1] + b"\nharmless line\n")
            fh.flush()
            found = _refuse_scan_bytes(open(fh.name, "rb").read())
        self.assertIn(name, found, "the %s scanner cannot refuse a planted synthetic string" % name)

    def test_refuses_home_laptop_path(self):
        self._row(0)

    def test_refuses_ssh_invocation(self):
        self._row(1)

    def test_refuses_key_path(self):
        self._row(2)

    def test_refuses_loopback_port(self):
        self._row(3)

    def test_refuses_guest_user(self):
        self._row(4)

    def test_refuses_repository_url(self):
        self._row(5)

    def test_refuses_claude_projects_path(self):
        self._row(6)

    def test_refuses_private_email(self):
        self._row(7)
'''


def inject_refusal_battery(data):
    """Inject the refusal battery into the shipped check.py bytes and extend its runner to run it."""
    if b"class ReleaseRefusalRows" in data:
        return data
    anchor = b'\nif __name__ == "__main__":'
    if anchor not in data:
        fail("check.py: cannot find the __main__ anchor to inject the refusal battery")
    data = data.replace(anchor, REFUSAL_BATTERY + anchor, 1)
    old = b'    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SeedCheck)\n'
    new = (b'    suite = unittest.TestSuite()\n'
           b'    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(SeedCheck))\n'
           b'    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(ReleaseRefusalRows))\n')
    if old not in data:
        fail("check.py: cannot find the SeedCheck suite line to extend")
    data = data.replace(old, new, 1)
    data = data.replace(b"Zero means all eight passed",
                        b"Zero means all checks passed (eight machinery + eight release-refusal rows)", 1)
    return data


RUNNER_SRC = r'''#!/usr/bin/env python3
"""Run the AWIG OS public test suite over this folder. Modules that need private estate context
(files outside src/tests/tools, the estate git history, or the guest/conformance fixtures reached by
an absolute estate path) are SKIPPED with a stated reason naming what they need; every other module
runs and MUST be green. It names its world: the three tree checksums it ran against are printed."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP = {}
with open(os.path.join(HERE, "tests", "RELEASE-SKIP-LIST.txt"), encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        mod, reason, dep = line.split("\t")
        SKIP[mod] = (reason, dep)
try:
    tc = json.load(open(os.path.join(HERE, "RENDER-STAMP.json"))).get("tree_checksums", {})
except Exception:
    tc = {}
tests_dir = os.path.join(HERE, "tests")
mods = sorted(f for f in os.listdir(tests_dir) if f.endswith(".py"))
passed = failed = 0
skipped = []
for f in mods:
    if f in SKIP:
        skipped.append((f,) + SKIP[f])
        continue
    rc = subprocess.call([sys.executable, os.path.join(tests_dir, f)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if rc == 0:
        passed += 1
    else:
        failed += 1
        print("FAILED  %s (rc %s)" % (f, rc))
print()
print("AWIG OS public suite ran against: src %s  tests %s  tools %s"
      % (tc.get("src", "?")[:12], tc.get("tests", "?")[:12], tc.get("tools", "?")[:12]))
for f, reason, dep in skipped:
    print("SKIP    %s -- %s (%s)" % (f, reason, dep))
print()
print("modules: %d ran (%d passed, %d failed), %d skipped naming their private dependency"
      % (passed + failed, passed, failed, len(skipped)))
sys.exit(0 if failed == 0 else 1)
'''

CENSUS_SRC = r'''#!/usr/bin/env python3
"""EP-RELEASE-TESTS census: the shipped skip list equals the renderer's manifest (SET equality),
every skipped module exists in this tree, and each carries its reason and named private file.
add-one or drop-one REDS."""
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _read_skiplist():
    out = {}
    with open(os.path.join(HERE, "RELEASE-SKIP-LIST.txt"), encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            mod, reason, dep = line.split("\t")
            out[mod] = (reason, dep)
    return out


class ReleaseSkipCensus(unittest.TestCase):
    def setUp(self):
        self.manifest = json.load(open(os.path.join(ROOT, "RELEASE-TESTS-MANIFEST.json")))
        self.skiplist = _read_skiplist()

    def test_skip_list_set_equals_the_manifest(self):
        man = {e["module"] for e in self.manifest["skip_list"]}
        self.assertEqual(set(self.skiplist), man, "shipped skip list != renderer manifest skip set")

    def test_every_skipped_module_exists_in_this_tree(self):
        for mod in self.skiplist:
            self.assertTrue(os.path.exists(os.path.join(HERE, mod)), "skipped module absent: %s" % mod)

    def test_each_skip_names_its_reason_and_private_file(self):
        man = {e["module"]: e for e in self.manifest["skip_list"]}
        for mod, (reason, dep) in self.skiplist.items():
            self.assertIn(mod, man)
            self.assertEqual(man[mod]["reason"], reason)
            self.assertEqual(man[mod]["private_file"], dep)
            self.assertTrue(reason and dep)

    def test_tree_checksums_present(self):
        self.assertEqual(set(self.manifest.get("tree_checksums", {})), {"src", "tests", "tools"})


if __name__ == "__main__":
    unittest.main()
'''


def emit_public_suite(out_root, tree_checksums, token_map):
    """Write the shipped skip list, manifest, public runner, and census test (EP §2 B5). The skip
    list and census live under tests/; the manifest and runner at the root. They are release
    scaffolding, NOT part of the three rendered-from-commit trees, so they are excluded from the
    tree checksums (which pin exactly what was rendered from the commit)."""
    tests_dir = os.path.join(out_root, "tests")
    with open(os.path.join(tests_dir, "RELEASE-SKIP-LIST.txt"), "w", encoding="utf-8") as fh:
        fh.write("# module\treason\tprivate dependency (EP-RELEASE-TESTS skip census)\n")
        for mod, reason, dep in SKIP_TABLE:
            fh.write("%s\t%s\t%s\n" % (mod, reason, dep))
    manifest = {
        "unit": "EP-RELEASE-TESTS",
        "placeholder_map": {k: v.decode("utf-8") for k, v in token_map.items()},
        "tree_checksums": tree_checksums,
        "skip_list": [{"module": m, "reason": r, "private_file": d} for (m, r, d) in SKIP_TABLE],
    }
    with open(os.path.join(out_root, "RELEASE-TESTS-MANIFEST.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")
    with open(os.path.join(out_root, "run_public_suite.py"), "w", encoding="utf-8") as fh:
        fh.write(RUNNER_SRC)
    with open(os.path.join(tests_dir, "test_release_census.py"), "w", encoding="utf-8") as fh:
        fh.write(CENSUS_SRC)
# ---------------------------------------------------------------------------

# The additive env alias: exactly these reads in kernel/commit.py become new-first, old-second.
ENV_READ_SITES = {
    "kernel/commit.py": [
        ("os.environ.get(WIDTH_ENV)", "_awig_env(WIDTH_ENV)"),
        ("os.environ.get(WINDOW_ENV)", "_awig_env(WINDOW_ENV)"),
    ]
}
ENV_HELPER_ANCHOR = 'WINDOW_ENV = "GOVOS_COMMIT_WINDOW_MS"\n'
ENV_HELPER = ENV_HELPER_ANCHOR + '''

def _awig_env(old_name):
    """AWIG OS reads the calibration override under its own name FIRST (AWIGOS_...), and under the
    estate's internal codename second (GOVOS_...), so a command written for either works. New first,
    old second; neither set -> the shipped default. (The release rendering, additive; never a rename.)"""
    new_name = "AWIGOS_" + old_name[len("GOVOS_"):] if old_name.startswith("GOVOS_") else old_name
    value = os.environ.get(new_name)
    return value if value is not None else os.environ.get(old_name)
'''


def fail(msg):
    sys.stderr.write("RENDER REFUSED: %s\n" % msg)
    sys.exit(2)


def extract_commit(sha):
    """Extract the whole tree at <sha> into a fresh temp dir via `git archive` (NEVER the working
    tree — archi :3239). Returns (full_sha, tmpdir). The caller removes tmpdir."""
    try:
        full = subprocess.check_output(["git", "-C", REPO, "rev-parse", "--verify", "%s^{commit}" % sha],
                                       text=True).strip()
    except subprocess.CalledProcessError:
        fail("--commit %s does not resolve to a commit in this repository" % sha)
    tmp = tempfile.mkdtemp(prefix="awig-render-src-")
    archive = subprocess.Popen(["git", "-C", REPO, "archive", "--format=tar", full], stdout=subprocess.PIPE)
    untar = subprocess.Popen(["tar", "-x", "-C", tmp], stdin=archive.stdout)
    archive.stdout.close()
    untar.communicate()
    archive.wait()
    if archive.returncode != 0 or untar.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        fail("git archive of %s failed (archive rc=%s, tar rc=%s)" % (sha, archive.returncode, untar.returncode))
    return full, tmp


def docstring_spans(source):
    """(lineno, col) start positions of every docstring Expr node — module, class, def."""
    spans = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
                    and isinstance(body[0].value.value, str):
                spans.add((body[0].value.lineno, body[0].value.col_offset))
    return spans


def rename_prose(source):
    """Replace OLD_NAME -> NEW_NAME inside COMMENT tokens and docstring STRING tokens only."""
    lines = source.splitlines(keepends=True)
    doc = docstring_spans(source)
    edits = []  # (line_idx, col_start, col_end, new_text) on single-line tokens; multi-line handled by span
    toks = list(tokenize.generate_tokens(io.StringIO(source).readline))
    for tok in toks:
        if tok.type == tokenize.COMMENT and OLD_NAME in tok.string:
            edits.append((tok.start, tok.end, tok.string.replace(OLD_NAME, NEW_NAME)))
        elif tok.type == tokenize.STRING and OLD_NAME in tok.string and (tok.start[0], tok.start[1]) in doc:
            edits.append((tok.start, tok.end, tok.string.replace(OLD_NAME, NEW_NAME)))
    if not edits:
        return source, 0
    # apply edits from the end backwards on a flat offset basis
    offsets = [0]
    for ln in lines:
        offsets.append(offsets[-1] + len(ln))
    flat = source
    for (sl, sc), (el, ec), new in sorted(edits, key=lambda e: e[0], reverse=True):
        a = offsets[sl - 1] + sc
        b = offsets[el - 1] + ec
        flat = flat[:a] + new + flat[b:]
    return flat, len(edits)


def add_header(source):
    if source.startswith(HEADER):
        return source
    if source.startswith("#!"):
        first, rest = source.split("\n", 1)
        return first + "\n" + HEADER + rest
    return HEADER + source


def alias_env(rel, source):
    sites = ENV_READ_SITES.get(rel)
    if not sites:
        return source, 0
    n = 0
    for old, new in sites:
        if source.count(old) != 1:
            fail("%s: expected exactly one %r read site, found %d" % (rel, old, source.count(old)))
        source = source.replace(old, new)
        n += 1
    if source.count(ENV_HELPER_ANCHOR) != 1:
        fail("%s: the env helper anchor is not unique" % rel)
    source = source.replace(ENV_HELPER_ANCHOR, ENV_HELPER)
    return source, n


def render_file(rel, data):
    """Returns rendered bytes and a small report for one file."""
    if rel.endswith(".py"):
        source = data.decode("utf-8")
        before_touch = [source.encode("utf-8").count(t) for t in NEVER_TOUCH]
        source, n_prose = rename_prose(source)
        source, n_env = alias_env(rel, source)
        source = add_header(source)
        out = source.encode("utf-8")
        after_touch = [out.count(t) for t in NEVER_TOUCH]
        if before_touch != after_touch:
            fail("%s: a never-touch item changed count %s -> %s" % (rel, before_touch, after_touch))
        if not (out.startswith(HEADER.encode()) or out.split(b"\n", 1)[1].startswith(HEADER.encode())):
            fail("%s: header missing after render" % rel)
        report = {"prose": n_prose, "env": n_env}
    else:
        out, report = data, {"copied": True}
    for bad in FORBIDDEN_OUTPUT:
        if bad in out:
            idx = out.index(bad)
            line = out[:idx].count(b"\n") + 1
            fail("%s:%d carries forbidden output %r" % (rel, line, bad.decode()))
    return out, report


def main(argv):
    out_root = OUT_DEFAULT
    if "--out" in argv:
        out_root = os.path.abspath(argv[argv.index("--out") + 1])
    out_src = os.path.join(out_root, "src")
    tool_sha = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()

    # --commit <sha> renders from a PINNED COMMIT TREE (archi :3239): extract it via git archive into
    # a temp dir and read src + the extras' sources from THERE. Without --commit: the working tree.
    tmp_src = None
    tmp_extras = None
    if "--commit" in argv:
        commit, tmp_src = extract_commit(argv[argv.index("--commit") + 1])
        src_root = tmp_src
    else:
        commit = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"], text=True).strip()
        src_root = REPO
    src_dir = os.path.join(src_root, "src")

    # --extras-commit <sha> (archi :3250): the EXTRAS (the README source, the vendored licences, the
    # staged seed scripts) render from THIS commit, while src/ renders from --commit. This lets the
    # release ship src from a crypto-free commit AND the extras from a LATER commit that carries the
    # corrected licence map + the doc-cite provenance paragraph. DEFAULTS to --commit's value (or HEAD
    # when --commit is absent), so a single-commit render is byte-for-byte unchanged (back-compat).
    # Like src, a distinct extras tree is git-archived — NEVER the working tree.
    if "--extras-commit" in argv:
        extras_commit, tmp_extras = extract_commit(argv[argv.index("--extras-commit") + 1])
        extras_root = tmp_extras
    else:
        extras_commit = commit
        extras_root = src_root

    try:
        files = {}
        reports = {}
        for root, dirs, names in os.walk(src_dir):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            for name in sorted(names):
                if name.endswith((".pyc", ".pyo")):
                    continue
                path = os.path.join(root, name)
                rel = os.path.relpath(path, src_dir).replace(os.sep, "/")
                with open(path, "rb") as fh:
                    data = fh.read()
                out, rep = render_file(rel, data)
                dest = os.path.join(out_src, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as fh:
                    fh.write(out)
                files[rel] = hashlib.sha256(out).hexdigest()
                reports[rel] = rep
        src_files = dict(files)  # src-only snapshot, for the src tree checksum

        # --with-tests-tools (EP-RELEASE-TESTS): ALSO emit tests/ and tools/ beside src/, from the
        # SAME pinned commit tree, under the §5 exclusions, every private literal rewritten AT RENDER
        # to a placeholder token (no past test or tool file edited). Kept in SEPARATE stamp keys so a
        # release-1 (src-only) stamp and check.py C1's src comparison are byte-for-byte unchanged.
        with_tt = "--with-tests-tools" in argv
        tests_files, tools_files, tt_hits = {}, {}, {}
        tree_checksums = {"src": tree_checksum(src_files)}
        if with_tt:
            patterns = _tt_class_patterns()
            tokens = load_placeholder_map()
            tests_files, h1 = render_extra_tree("tests", src_root, out_root, patterns, tokens)
            tools_files, h2 = render_extra_tree("tools", src_root, out_root, patterns, tokens)
            for h in (h1, h2):
                for k, v in h.items():
                    tt_hits[k] = tt_hits.get(k, 0) + v
            # ship the class->placeholder map INTO the tools tree (B2: kept in tools/release/, shipped)
            map_bytes = open(MAP_PATH, "rb").read()
            map_dest = os.path.join(out_root, "tools", "release", "placeholder-map.json")
            os.makedirs(os.path.dirname(map_dest), exist_ok=True)
            with open(map_dest, "wb") as fh:
                fh.write(map_bytes)
            tools_files["tools/release/placeholder-map.json"] = hashlib.sha256(map_bytes).hexdigest()
            tree_checksums["tests"] = tree_checksum(tests_files)
            tree_checksums["tools"] = tree_checksum(tools_files)

        pack = json.load(open(os.path.join(src_dir, "founding", "founding-pack.json")))
        stamp = {
            "product": "AWIG OS",
            "rendered_from": {"repo": "the estate's src/ (private mirror)", "commit": commit,
                              "founding_version": pack.get("founding_version")},
            "rendered_extras_from": {"repo": "the estate's src/ (private mirror)", "commit": extras_commit},
            "tool": {"path": "tools/release/render.py", "sha256": tool_sha},
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "files": files,
            "summary": {"files": len(files),
                        "prose_edits": sum(r.get("prose", 0) for r in reports.values()),
                        "env_alias_sites": sum(r.get("env", 0) for r in reports.values())},
        }
        if with_tt:
            stamp["tests_files"] = tests_files
            stamp["tools_files"] = tools_files
            stamp["tree_checksums"] = tree_checksums
            stamp["summary"]["tests_files"] = len(tests_files)
            stamp["summary"]["tools_files"] = len(tools_files)
            stamp["summary"]["private_rewrites"] = tt_hits
        # THE FOLDER'S OTHER FILES, all from named sources (never hand-written into the output) and,
        # under --commit/--extras-commit, read from THE PINNED EXTRAS COMMIT TREE (extras_root) — which
        # defaults to src_root, so a single-commit render is unchanged (archi :3250):
        #   seed_demo.py + check.py  from the staged seed (awig-deploy/seed-stage/public/seed) — the
        #                            public repository's tested copies carry the platform guard (fix 2);
        #   README.md                from tools/release/awig-code-README.md (the guidance source);
        #   the four licence texts   from tools/release/licenses/ (vendored verbatim from the public repo);
        #   FREEZE.txt               written from the stamp.
        os.makedirs(out_root, exist_ok=True)
        extras = {
            "seed_demo.py": os.path.join(extras_root, "awig-deploy", "seed-stage", "public", "seed", "seed_demo.py"),
            "check.py": os.path.join(extras_root, "awig-deploy", "seed-stage", "public", "seed", "check.py"),
            "README.md": os.path.join(extras_root, "tools", "release", "awig-code-README.md"),
            "LICENSE": os.path.join(extras_root, "tools", "release", "licenses", "LICENSE"),
            "LICENSE-APACHE": os.path.join(extras_root, "tools", "release", "licenses", "LICENSE-APACHE"),
            "LICENSE-DOCS": os.path.join(extras_root, "tools", "release", "licenses", "LICENSE-DOCS"),
            "LICENSING.md": os.path.join(extras_root, "tools", "release", "licenses", "LICENSING.md"),
        }
        for name, src_path in extras.items():
            with open(src_path, "rb") as fh:
                data = fh.read()
            if name in ("seed_demo.py", "check.py") and b"require_durable_sync" not in data:
                fail("%s: the staged seed script lacks the platform guard (fix 2) — sync it from the public repo first" % name)
            if with_tt and name == "check.py":
                data = inject_refusal_battery(data)  # the eight planted-refusal rows (EP §2 B3)
            for bad in FORBIDDEN_OUTPUT:
                if bad in data:
                    fail("%s carries forbidden output %r" % (name, bad.decode()))
            with open(os.path.join(out_root, name), "wb") as fh:
                fh.write(data)
            files["../" + name] = hashlib.sha256(data).hexdigest()
        freeze = ("AWIG OS rendering, founding %s, commit %s, extras commit %s, "
                  "rendered by tools/release/render.py %s.\n") % (
            pack.get("founding_version"), commit, extras_commit, tool_sha[:12])
        if with_tt:
            # FREEZE names the THREE tree checksums (src, tests, tools) — EP §2 B4.
            freeze += ("tree checksums: src %s, tests %s, tools %s.\n"
                       % (tree_checksums["src"], tree_checksums["tests"], tree_checksums["tools"]))
        with open(os.path.join(out_root, "FREEZE.txt"), "w", encoding="utf-8") as fh:
            fh.write(freeze)
        files["../FREEZE.txt"] = hashlib.sha256(freeze.encode("utf-8")).hexdigest()
        with open(os.path.join(out_root, "RENDER-STAMP.json"), "w", encoding="utf-8") as fh:
            json.dump(stamp, fh, indent=1, sort_keys=True)
            fh.write("\n")
        if with_tt:
            emit_public_suite(out_root, tree_checksums, tokens)  # skip list, manifest, runner, census
        print("rendered %d files -> %s" % (len(files), out_src))
        print("commit %s  extras %s  tool %s" % (commit[:12], extras_commit[:12], tool_sha[:12]))
        print("prose edits %d, env alias sites %d" % (stamp["summary"]["prose_edits"], stamp["summary"]["env_alias_sites"]))
        if with_tt:
            print("tests files %d, tools files %d, private rewrites %s"
                  % (len(tests_files), len(tools_files), sum(tt_hits.values())))
            print("tree checksums: src %s tests %s tools %s"
                  % (tree_checksums["src"][:12], tree_checksums["tests"][:12], tree_checksums["tools"][:12]))
        return 0
    finally:
        if tmp_src:
            shutil.rmtree(tmp_src, ignore_errors=True)
        if tmp_extras:
            shutil.rmtree(tmp_extras, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
