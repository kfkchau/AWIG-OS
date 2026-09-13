#!/usr/bin/env python3
"""C8 — THE CLEAN-FROM-CUT CHECK (planning/exec/RELEASE-NAMING-AND-HEADERS-DRAFT.md v2 §8;
EP-RELEASE-RENDERING §3 C8). A git-add-date gate: a src/, tests/ or tools/ file whose FIRST
commit is AFTER the naming cut must carry no laptop path (<HOME>) and no seat-transcript
path; history is exempt BY CONSTRUCTION (a file added before the cut is never scanned).

Enforced (green/red), the rule the planted control exercises:
  a post-cut src/tests/tools file must contain none of render.FORBIDDEN_OUTPUT
  (the laptop path, the transcript path). A post-cut file that carries one is NAMED.

Advisory (reported, never red):
  product prose  — a post-cut file that names the product should say "AWIG OS"; the estate's
                   internal `gov-os provenance` banner and codename identifiers are NOT product
                   prose and are not flagged (the estate keeps its codename by design).
  env names      — a post-cut tests/tools file that sets a GOVOS_ override should also offer the
                   AWIGOS_ name; but a test that deliberately exercises the GOVOS_ alias path is
                   legitimate, so this is advisory, never a failure.

Scope note: tools/release/** is EXEMPT from the path scan — it is the rendering tooling that
DEFINES render.FORBIDDEN_OUTPUT and so must spell those patterns; exempting it is what lets the
tool encode the very rule it enforces without self-flagging. The path rule still binds every
other post-cut file in src/, tests/, tools/.

Run from the repo root:
  python3 tools/release/check_clean_from_cut.py            # scan the real estate (exit 0 = green)
  python3 tools/release/check_clean_from_cut.py --selftest # planted control: a post-cut file with
                                                           # a <HOME> path must be NAMED
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render  # noqa: E402  (for FORBIDDEN_OUTPUT — imported, never re-spelled here)

# The naming cut: the owner's word 2026-09-07 that made "AWIG OS" the product name and the
# rendering a build output. Files first committed strictly before this date are history, exempt.
CUT_ISO = "2026-09-07"

ROOTS = ("src", "tests", "tools")
PATH_SCAN_EXEMPT = ("tools/release/",)  # the tooling that defines the forbidden patterns
ADV_ENV = ("GOVOS_COMMIT_WIDTH", "GOVOS_COMMIT_WINDOW_MS", "GOVOS_MSG_MAX")
PROSE_CODENAME = re.compile(rb"gov-os")  # only the hyphenated product-form matters for prose


def first_add_date(rel):
    """ISO date (YYYY-MM-DD) of the file's FIRST commit, or None if git knows no add event."""
    out = subprocess.run(["git", "-C", REPO, "log", "--diff-filter=A", "--follow",
                          "--format=%aI", "--", rel], capture_output=True, text=True).stdout
    dates = [ln.strip()[:10] for ln in out.splitlines() if ln.strip()]
    return dates[-1] if dates else None


def tracked_files():
    out = subprocess.check_output(["git", "-C", REPO, "ls-files", *ROOTS], text=True)
    return [ln for ln in out.splitlines() if ln]


def scan_path_rule(rel, data):
    """The ENFORCED rule. Returns a list of named violations (empty = clean)."""
    hits = []
    for bad in render.FORBIDDEN_OUTPUT:
        idx = data.find(bad)
        if idx != -1:
            line = data[:idx].count(b"\n") + 1
            hits.append("%s:%d carries %r" % (rel, line, bad.decode()))
    return hits


def advisories(rel, data):
    notes = []
    # product prose: hyphenated gov-os in a file that never says AWIG OS (banner/identifiers ignored)
    prose = [m for m in PROSE_CODENAME.finditer(data)
             if b"provenance" not in data[data.rfind(b"\n", 0, m.start()) + 1:
                                          data.find(b"\n", m.end()) if data.find(b"\n", m.end()) != -1 else len(data)]]
    if prose and b"AWIG OS" not in data:
        notes.append("%s: uses 'gov-os' prose and never 'AWIG OS'" % rel)
    if rel.startswith(("tests/", "tools/")):
        for env in ADV_ENV:
            if env.encode() in data and env.replace("GOVOS_", "AWIGOS_").encode() not in data:
                notes.append("%s: sets %s without the AWIGOS_ name" % (rel, env))
    return notes


def main(argv):
    if "--selftest" in argv:
        return selftest()
    violations, adv, scanned, exempt_hist = [], [], 0, 0
    for rel in tracked_files():
        d = first_add_date(rel)
        if d is None or d < CUT_ISO:
            exempt_hist += 1
            continue
        with open(os.path.join(REPO, rel), "rb") as fh:
            data = fh.read()
        scanned += 1
        if not any(rel.startswith(p) for p in PATH_SCAN_EXEMPT):
            violations += scan_path_rule(rel, data)
        adv += advisories(rel, data)
    print("cut=%s  scanned %d post-cut file(s), %d pre-cut file(s) exempt by history" %
          (CUT_ISO, scanned, exempt_hist))
    for a in adv:
        print("ADVISORY %s" % a)
    if violations:
        for v in violations:
            print("FAIL %s" % v)
        print("\nRED: %d post-cut file(s) carry a laptop/transcript path" % len(violations))
        return 1
    print("GREEN: no post-cut src/tests/tools file carries a laptop or transcript path")
    return 0


def selftest():
    """Planted control: a post-cut file carrying a <HOME> path MUST be named."""
    laptop = render.FORBIDDEN_OUTPUT[0]  # b"<HOME>", imported not spelled
    planted = b"# a new post-cut test\nPATH = " + laptop + b"/apps/gov-os/x\n"
    hits = scan_path_rule("tests/test_planted_postcut.py", planted)
    clean = scan_path_rule("tests/test_clean_postcut.py", b"# clean\nPATH = 'relative/x'\n")
    print("CONTROL planted post-cut <HOME> file ->", hits)
    print("CONTROL clean post-cut file ->", clean or "no violation (correct)")
    ok = bool(hits) and not clean
    print("\n%s: the check %s name a planted laptop path" % ("PASS" if ok else "FAIL",
                                                             "can" if ok else "CANNOT"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
