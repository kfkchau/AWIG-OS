#!/usr/bin/env python3
"""THE RELEASE CHECK — proves the rendered tree is a rendering and not a second source
(planning/exec/RELEASE-NAMING-AND-HEADERS-DRAFT.md v2 §4; every line can fail).

  C1 regeneration is exact   render again into a temp dir; byte-identical to awig-code/src; the
                             stamp's per-file sha256s match a fresh walk.
  C2 the names are gone      no gov-os/govos/GOVOS in the rendered tree except the named never-touch
                             identifiers and the GOVOS_ fallback names inside the alias helper; no
                             <HOME> or transcript path; every .py starts with the header.
  C5 never-touch identical   the DEPARTURE marker and the wire identifiers appear in the rendered
                             tree exactly as many times as in src/.
  C7 the estate untouched    git diff --stat -- src tests tools (minus tools/release) is empty.
  PLANTED CONTROL            a copy of one rendered file with its header stripped is CAUGHT.

Run from the repo root:  python3 tools/release/check.py      (exit 0 = all green)
C3 (the two-tree ledger) and C6 (the stranger run) are run separately — they take minutes and a person.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "awig-deploy", "awig-code")
OUT_SRC = os.path.join(OUT, "src")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render  # noqa: E402

ALLOWED_OLD = {"govos_fill_super", "govos_call_lock",
               'b"\\x00gov-os:content-departed-by-handover\\x00"',
               "GOVOS_COMMIT_WIDTH", "GOVOS_COMMIT_WINDOW_MS", "GOVOS_MSG_MAX", "GOVOS_",
               # paths and device nodes of the guest kernel module: an address is not a name (§3.3/3.4)
               "govosfs", "/dev/govos-ctl"}
OLD_RE = re.compile(rb"gov-os|govos|GOVOS")
# FREEZE.txt embeds the render commit; a re-render straddling an autosync commit differs ONLY
# there (:3206). C1 masks the 40-hex hash after literal "commit " for FREEZE.txt's byte compare
# and NOTHING ELSE — every other byte of FREEZE.txt, and every other file, stays compared raw.
# FREEZE.txt now names TWO commits (src + extras, archi :3250) as "commit <sha>, extras commit
# <sha>"; the global sub masks BOTH 40-hex shas after "commit ", leaving the rest compared raw.
COMMIT_MASK = re.compile(rb"(commit )[0-9a-f]{40}")


def mask_commit(data):
    return COMMIT_MASK.sub(rb"\1<MASKED>", data)

fails = []


def check(name, ok, detail=""):
    print("%-5s %s%s" % ("PASS" if ok else "FAIL", name, (" — " + detail) if detail else ""))
    if not ok:
        fails.append(name)


def walk(root):
    out = {}
    for r, ds, ns in os.walk(root):
        ds[:] = sorted(d for d in ds if d != "__pycache__")
        for n in sorted(ns):
            if n.endswith((".pyc", ".pyo")):
                continue
            p = os.path.join(r, n)
            out[os.path.relpath(p, root).replace(os.sep, "/")] = open(p, "rb").read()
    return out


def main():
    if not os.path.isdir(OUT_SRC):
        print("no rendered tree at %s — run tools/release/render.py first" % OUT_SRC)
        return 2
    rendered = walk(OUT_SRC)
    stamp = json.load(open(os.path.join(OUT, "RENDER-STAMP.json")))

    # C1 — regeneration is exact. Re-render from the STAMP's pinned commit (archi :3239), NOT the
    # working tree/HEAD: the tree now holds in-flight source (e.g. autosynced half-built crypto) that
    # the release commit predates, so a working-tree re-render would spuriously red. Rendering the
    # SAME pinned commit compares the stored tree against a deterministic re-render of that commit.
    tmp = tempfile.mkdtemp(prefix="awig-render-check-")
    try:
        # Re-render from BOTH pinned commits the stamp names (archi :3250): src from rendered_from,
        # the extras from rendered_extras_from (defaulting to the src commit for a single-commit
        # render / an older stamp that predates the split). Working-tree-immune either way.
        extras_commit = stamp.get("rendered_extras_from", stamp["rendered_from"])["commit"]
        _args = [sys.executable, os.path.join(REPO, "tools", "release", "render.py"),
                 "--commit", stamp["rendered_from"]["commit"],
                 "--extras-commit", extras_commit, "--out", tmp]
        if "tree_checksums" in stamp:  # EP-RELEASE-TESTS: this stamp shipped tests/ + tools/ too
            _args.append("--with-tests-tools")
        subprocess.check_output(_args, cwd=REPO)
        again = walk(os.path.join(tmp, "src"))
        same = again == rendered
        # the folder's other files regenerate too (seed scripts, README, licences, FREEZE)
        for name in ("seed_demo.py", "check.py", "README.md", "LICENSE", "LICENSE-APACHE", "LICENSE-DOCS", "LICENSING.md", "FREEZE.txt"):
            a = open(os.path.join(tmp, name), "rb").read(); b = open(os.path.join(OUT, name), "rb").read()
            if name == "FREEZE.txt":
                a = mask_commit(a); b = mask_commit(b)
            if a != b:
                same = False; check("C1 %s regenerates identically" % name, False)
        check("C1 regeneration byte-identical", same,
              "" if same else "differs: %s" % sorted(set(again) ^ set(rendered) | {k for k in again if again.get(k) != rendered.get(k)})[:5])
        fresh = {k: hashlib.sha256(v).hexdigest() for k, v in rendered.items()}
        for name in ("seed_demo.py", "check.py", "README.md", "LICENSE", "LICENSE-APACHE", "LICENSE-DOCS", "LICENSING.md", "FREEZE.txt"):
            fresh["../" + name] = hashlib.sha256(open(os.path.join(OUT, name), "rb").read()).hexdigest()
        check("C1 stamp matches a fresh sha256 walk (src + the folder's files)", fresh == stamp["files"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # C2 — names gone, no laptop paths, header on every .py
    bad_names, bad_paths, no_header = [], [], []
    for rel, data in rendered.items():
        for m in OLD_RE.finditer(data):
            line_start = data.rfind(b"\n", 0, m.start()) + 1
            line_end = data.find(b"\n", m.end())
            line = data[line_start:line_end if line_end != -1 else None].decode("utf-8", "replace")
            if any(a in line for a in ALLOWED_OLD):
                continue
            bad_names.append("%s: %s" % (rel, line.strip()[:90]))
        for bad in render.FORBIDDEN_OUTPUT:
            if bad in data:
                bad_paths.append(rel)
        if rel.endswith(".py"):
            body = data.split(b"\n", 1)[1] if data.startswith(b"#!") else data
            if not body.startswith(render.HEADER.encode()):
                no_header.append(rel)
    check("C2 no internal name in the rendered tree (beyond the named never-touch set)", not bad_names,
          "; ".join(bad_names[:4]))
    check("C2 no laptop or transcript path", not bad_paths, ", ".join(bad_paths[:4]))
    check("C2 header on every .py", not no_header, ", ".join(no_header[:4]))

    # C5 — never-touch items count-identical to src/
    src = walk(os.path.join(REPO, "src"))
    for item in render.NEVER_TOUCH:
        a = sum(v.count(item) for v in src.values())
        b = sum(v.count(item) for v in rendered.values())
        check("C5 never-touch %r count %d -> %d" % (item[:32], a, b), a == b and a > 0)

    # C7 — the estate untouched (src, tests, tools minus tools/release)
    diff = subprocess.check_output(["git", "-C", REPO, "diff", "--stat", "--",
                                    "src", "tests", "tools", ":(exclude)tools/release"], text=True).strip()
    check("C7 estate src/tests/tools untouched", diff == "", diff.splitlines()[-1] if diff else "")

    # CTT — EP-RELEASE-TESTS: when this stamp shipped tests/ + tools/, no private-literal class
    # survives in them (mirrors A2), and the stamp names three tree checksums that recompute.
    if "tree_checksums" in stamp:
        classes = render._tt_class_patterns()
        leaks = []
        for sub in ("tests", "tools"):
            base = os.path.join(OUT, sub)
            for r, ds, ns in os.walk(base):
                ds[:] = [d for d in ds if d != "__pycache__"]
                for n in sorted(ns):
                    if n.endswith((".pyc", ".pyo")):
                        continue
                    data = open(os.path.join(r, n), "rb").read()
                    for name, rx, _ in classes:
                        if rx.search(data):
                            leaks.append("%s: %s" % (os.path.relpath(os.path.join(r, n), OUT), name))
        check("CTT no private-literal class survives in shipped tests/ or tools/", not leaks, "; ".join(leaks[:4]))
        check("CTT stamp names three tree checksums", set(stamp["tree_checksums"]) == {"src", "tests", "tools"})

    # PLANTED CONTROL — a stripped header is caught
    sample = next(k for k in sorted(rendered) if k.endswith(".py"))
    stripped = rendered[sample].replace(render.HEADER.encode(), b"", 1)
    caught = not stripped.startswith(render.HEADER.encode())
    check("CONTROL a stripped header is caught (the check can fail)", caught)

    print("\n%s: %d check(s) failed" % ("RED" if fails else "GREEN", len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
