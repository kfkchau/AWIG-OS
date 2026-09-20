#!/usr/bin/env python3
"""Run the AWIG OS public test suite over this folder, and PROVE what it prints.

Before any module runs, an integrity gate recomputes the release's own pins from the bytes on disk,
so a green result cannot be a vacuous one:
  - INVENTORY: the set of files in each rendered tree (src, tests, tools) must equal the set the
    stamp recorded. A file added to a tree, or missing from it, is a refusal (exit 2, named).
  - CHECKSUMS: the three tree checksums are RECOMPUTED from the on-disk bytes -- not read from the
    stamp and reprinted -- and must equal both RENDER-STAMP.json and RELEASE-TESTS-MANIFEST.json.
    A single changed byte moves a recomputed checksum and is a refusal.
  - a run with no discovered module, or an empty skip list, is a refusal -- never a silent pass.
Then every discovered test_*.py runs (helpers such as era_pin.py are NOT modules); each module's
stdout and stderr are kept in a per-module log beside the run (public-suite-logs/), not discarded;
and the summary reports test CASES and within-module skips APART from module exit codes.
Modules that need private estate context (files outside src/tests/tools, the estate git history, or
the guest/conformance fixtures reached by an absolute estate path) are SKIPPED with a stated reason
naming what they need; every other module runs and MUST be green. It names its world: the three tree
checksums it RECOMPUTED and CONFIRMED against this folder are printed."""
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BYTECODE = ("__pycache__",)
# release scaffolding emitted INTO tests/ after the tree checksums were taken (so it is excluded
# from those checksums and from the inventory the stamp recorded):
TESTS_SCAFFOLDING = {"RELEASE-SKIP-LIST.txt", "test_release_census.py"}
LOGDIR = os.path.join(HERE, "public-suite-logs")


def _refuse(reason):
    """A named, non-zero refusal. Exit 2 marks an integrity refusal, distinct from a module failure."""
    print("REFUSED: " + reason)
    sys.exit(2)


def _tree_checksum(files):
    """The renderer's own tree checksum, byte for byte: sha256 over sorted per-file lines, each line
    being the relpath, then a NUL, then the file's sha256 hex, then a newline. `files` is
    {relpath: sha256hex}; order-independent, content-bound."""
    h = hashlib.sha256()
    for rel in sorted(files):
        h.update(rel.encode("utf-8"))
        h.update(bytes([0]))
        h.update(files[rel].encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def _walk_tree(subdir, key_prefix):
    """{key: fullpath} over the on-disk subdir, keyed exactly as the renderer keyed that tree
    (src has no prefix; tests/ and tools/ carry theirs), bytecode excluded."""
    base = os.path.join(HERE, subdir)
    out = {}
    for root, dirs, names in os.walk(base):
        dirs[:] = [d for d in dirs if d not in BYTECODE]
        for name in names:
            if name.endswith((".pyc", ".pyo")):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, base).replace(os.sep, "/")
            out[(key_prefix + rel) if key_prefix else rel] = path
    return out


def _integrity_gate():
    """Recompute the release's own pins from the bytes on disk; refuse on any drift. Returns the
    confirmed tree checksums for the summary line."""
    try:
        with open(os.path.join(HERE, "RENDER-STAMP.json"), encoding="utf-8") as fh:
            stamp = json.load(fh)
    except Exception as exc:
        _refuse("RENDER-STAMP.json is unreadable (%s)" % exc)
    try:
        with open(os.path.join(HERE, "RELEASE-TESTS-MANIFEST.json"), encoding="utf-8") as fh:
            manifest = json.load(fh)
    except Exception as exc:
        _refuse("RELEASE-TESTS-MANIFEST.json is unreadable (%s)" % exc)
    stamp_tc = stamp.get("tree_checksums", {})
    if set(stamp_tc) != {"src", "tests", "tools"}:
        _refuse("stamp tree_checksums are not the three trees (src, tests, tools)")
    if manifest.get("tree_checksums", {}) != stamp_tc:
        _refuse("manifest tree_checksums disagree with the stamp")
    # the stamp's per-file inventory, keyed as the renderer keyed each tree (src: no prefix and the
    # root '../' extras dropped; tests/ and tools/ carry their prefix):
    src_map = {k: v for k, v in stamp.get("files", {}).items() if not k.startswith("../")}
    trees = (
        ("src", src_map, _walk_tree("src", ""), set()),
        ("tests", stamp.get("tests_files", {}), _walk_tree("tests", "tests/"),
         {"tests/" + n for n in TESTS_SCAFFOLDING}),
        ("tools", stamp.get("tools_files", {}), _walk_tree("tools", "tools/"), set()),
    )
    for tree, stamp_map, disk_paths, scaffolding in trees:
        disk_keys = set(disk_paths) - scaffolding
        stamp_keys = set(stamp_map)
        added = disk_keys - stamp_keys
        missing = stamp_keys - disk_keys
        if added:
            _refuse("%s tree carries files absent from the release inventory: %s"
                    % (tree, ", ".join(sorted(added))))
        if missing:
            _refuse("%s tree is missing files the release inventory names: %s"
                    % (tree, ", ".join(sorted(missing))))
        recomputed = {}
        for key in stamp_map:
            with open(disk_paths[key], "rb") as fh:
                got = hashlib.sha256(fh.read()).hexdigest()
            if got != stamp_map[key]:
                _refuse("%s/%s differs from the release inventory -- a byte was changed" % (tree, key))
            recomputed[key] = got
        rolled = _tree_checksum(recomputed)
        if rolled != stamp_tc[tree]:
            _refuse("%s tree checksum recomputed %s but the stamp pins %s"
                    % (tree, rolled[:12], stamp_tc[tree][:12]))
    return stamp_tc


def main():
    stamp_tc = _integrity_gate()
    skip = {}
    try:
        with open(os.path.join(HERE, "tests", "RELEASE-SKIP-LIST.txt"), encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line or line.startswith("#"):
                    continue
                mod, reason, dep = line.split("\t")
                skip[mod] = (reason, dep)
    except FileNotFoundError:
        _refuse("tests/RELEASE-SKIP-LIST.txt is absent -- the runner cannot state what it skipped")
    if not skip:
        _refuse("the skip list is empty -- a public run with no stated skips certifies nothing")
    tests_dir = os.path.join(HERE, "tests")
    # DISCOVERY: test_*.py only. Helpers (era_pin.py, differential drivers) are not modules.
    mods = sorted(f for f in os.listdir(tests_dir)
                  if f.startswith("test_") and f.endswith(".py"))
    if not mods:
        _refuse("no test_*.py module discovered -- an empty collection cannot certify a release")
    os.makedirs(LOGDIR, exist_ok=True)
    ran_re = re.compile(r"^Ran (\d+) test", re.M)
    # A module that raises unittest.SkipTest AT IMPORT (before any test runs) exits non-zero with a
    # bare traceback ending in SkipTest and NO "Ran N tests" line. That is a stated skip, not a crash:
    # read it as a SKIP row naming its reason, never a FAILED row (RELEASE-4 round 2, board :4642 (3)).
    import_skip_re = re.compile(r"^(?:[\w.]+\.)?SkipTest: (.*)$", re.M)
    # THE TREE ROOT ON THE CHILD IMPORT PATH: each module runs as its OWN process, so a stranger's plain
    # run must find tools/ (and the tests package) without an environment incantation. HERE is the tree
    # root that holds src/ tests/ tools/; put it on PYTHONPATH for every child (board :4642 (3)).
    child_env = dict(os.environ)
    child_env["PYTHONPATH"] = (
        HERE + (os.pathsep + child_env["PYTHONPATH"] if child_env.get("PYTHONPATH") else ""))
    mod_passed = mod_failed = 0
    cases = case_fail = case_err = case_skip = 0
    skipped = []
    import_skipped = []
    failed_mods = []
    for f in mods:
        if f in skip:
            skipped.append((f,) + skip[f])
            continue
        logpath = os.path.join(LOGDIR, f + ".log")
        with open(logpath, "wb") as log:
            rc = subprocess.call([sys.executable, os.path.join(tests_dir, f)],
                                 stdout=log, stderr=subprocess.STDOUT, env=child_env)
        with open(logpath, encoding="utf-8", errors="replace") as log:
            text = log.read()
        match = ran_re.search(text)
        # import-time SkipTest: non-zero, no "Ran N" line, a SkipTest traceback -> a stated skip row.
        if rc != 0 and match is None:
            m_skip = import_skip_re.search(text)
            if m_skip:
                import_skipped.append((f, m_skip.group(1).strip()))
                continue
        cases += int(match.group(1)) if match else 0
        for kind, count in re.findall(r"(failures|errors|skipped)=(\d+)", text):
            if kind == "failures":
                case_fail += int(count)
            elif kind == "errors":
                case_err += int(count)
            else:
                case_skip += int(count)
        if rc == 0:
            mod_passed += 1
        else:
            mod_failed += 1
            failed_mods.append((f, rc))
    print()
    for f, rc in failed_mods:
        print("FAILED  %s (rc %s) -- output in public-suite-logs/%s.log" % (f, rc, f))
    print("AWIG OS public suite ran against (RECOMPUTED & CONFIRMED): src %s  tests %s  tools %s"
          % (stamp_tc["src"][:12], stamp_tc["tests"][:12], stamp_tc["tools"][:12]))
    for f, reason, dep in skipped:
        print("SKIP    %s -- %s (%s)" % (f, reason, dep))
    for f, reason in import_skipped:
        print("SKIP    %s -- %s (SkipTest at import)" % (f, reason))
    print()
    print("modules: %d ran (%d passed, %d failed), %d skipped naming their private dependency, "
          "%d skipped at import"
          % (mod_passed + mod_failed, mod_passed, mod_failed, len(skipped), len(import_skipped)))
    print("cases:   %d ran, %d failed, %d errored, %d skipped within modules"
          % (cases, case_fail, case_err, case_skip))
    print("per-module logs kept in public-suite-logs/")
    sys.exit(0 if mod_failed == 0 else 1)


if __name__ == "__main__":
    main()
