#!/usr/bin/env python3
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
