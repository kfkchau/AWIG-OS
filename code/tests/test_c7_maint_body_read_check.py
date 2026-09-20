# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-tooling · machine register.
# The freestanding kernel body's boot self-check of what its OWN record disk holds (check_body_read),
# re-pointed to the CURRENT on-disk layout AS DATA after the tree archive entry (govtree) was staged.
# NON-GOAL: no offensive capability; it fixes a boot self-check that reads its own disk and re-points it
# to the layout the disk now carries, keeping the unexpected-entry refusal. Every kernel touch is the
# guest's nested qemu (L11 / EP-00 rule 9 / charter §A21). Validate by building/reading, never by attack.
# Full declaration: SCOPE-STATEMENT.md.
"""C7-MAINT-BODY-READ-CHECK acceptance — THE BODY'S BOOT SELF-CHECK OF ITS OWN RECORD DISK, RE-POINTED
TO THE CURRENT LAYOUT AS DATA (design/54 §5 L14; archi :4338; GREEN, no countersign as :4254 / :4268).

src/body/diskcheck.c check_body_read pinned the record disk to EXACTLY THREE entries (the P3b-2 layout:
record / founding-pack / self-a). Since P3b-5a-iii staged the whole-tree archive blob `govtree` (and
P3b-5b-i the `runmod` blob, P3b-4g the gate blobs), a clean boot's disk carries MORE than three entries,
so `c == 3` was false and `govtree` tripped `unexpected` — the boot printed `CHECK BODY-READ: FAIL` on
every TREE boot (documented at test_c7_p3b_5a_iii §NOTE), a stale check of a LOCATION, never a real
defect. This unit re-points the check to the CURRENT layout as data (L14 — the location re-points, the
property held), keeping the unexpected-entry refusal and adding a clean-boot-no-FAIL standing assertion.

  A1  the re-pointed check PASSES on a clean boot against the CURRENT expected set taken as DATA — the
      names src/body/mkdisk.py stages (record, founding-pack, the gate blobs, runmod, govtree) plus the
      self-check's own self-a, self-b removed; a clean boot prints CHECK BODY-READ: PASS. PLANT: a GHOST
      entry (a name in no expected set) → check_body_read reds (the unexpected-entry refusal, L14).
  A2  the unexpected-entry refusal AND the missing-entry failure are PRESERVED — an entry OUTSIDE the
      expected set reds (the ghost plant); a MISSING expected entry reds (PLANT_WALK_MISSES drops one).
  A3  a clean boot prints NO `CHECK …: FAIL` and NO `SERVE CHECK …: FAIL` line — a standing assertion
      that CAN fail. PLANT: force one check to FAIL (the ghost of A1) → the assertion reds.
  MIRROR (host, as DATA)  the expected-optional set diskcheck.c accepts IS the set of names mkdisk.py
      stages — parsed from both sources and cross-checked, so a staging change reds until the check
      re-points (never a frozen hand-count; L14, the :4234 lesson).

Register: OS boot self-check bring-up on a disposable guest, described by function — a record-disk
self-check re-pointed to the layout its own mkfs tool writes; validated by building/reading, never by
attack (governance-work-method). The guest boot cases build+boot in the NESTED guest and skip when the
pinned guest is not reachable; each boot uses a FRESH disk image (a booted image carries a record and
takes the reboot path, so a fresh self-check needs a fresh image). One nested qemu at a time.
"""

import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
SRC = os.path.join(ROOT, "src")
BODY = os.path.join(SRC, "body")
MKDISK = os.path.join(BODY, "mkdisk.py")
DISKCHECK = os.path.join(BODY, "diskcheck.c")


# ══ THE AS-DATA MIRROR (host only — the expected set is DERIVED from mkdisk.py, never hand-counted) ══
def _mkdisk_staged_optional_names():
    """The OPTIONAL content names src/body/mkdisk.py can stage on the record disk, parsed from its
    source: the C7 P3b-4g gate blob entry names (GATE_MODULES first elements) + the "syskey" test key,
    the C7 P3b-5b-i "runmod" blob, and the C7 P3b-5a-iii "govtree" tree archive. `record` and
    `founding-pack` are the always-present core (staged unconditionally) and are checked separately."""
    with open(MKDISK, encoding="utf-8") as f:
        text = f.read()
    names = set()
    # GATE_MODULES = [ ("ker_init.py", os.path.join("kernel", "__init__.py")), ... ] — the ENTRY NAME is
    # the FIRST tuple string, the one immediately followed by ", os.path.join(" (never the join's args).
    block = re.search(r"GATE_MODULES\s*=\s*\[(.*?)\]", text, re.S)
    assert block, "GATE_MODULES list not found in mkdisk.py"
    for m in re.finditer(r"\(\s*\"([^\"]+)\"\s*,\s*os\.path\.join\(", block.group(1)):
        names.add(m.group(1))
    assert len(names) == 7, "expected 7 gate module entry names, parsed %s" % sorted(names)
    # the guest test key staged by _gate_files: out.append(("syskey", GATE_TEST_SEED))
    assert re.search(r'out\.append\(\(\s*"syskey"', text), "the syskey blob is staged by mkdisk.py"
    names.add("syskey")
    # the runmod blob (P3b-5b-i) and the govtree archive (P3b-5a-iii) — staged _entry(...) names.
    assert re.search(r'_entry\(\s*"runmod"', text), "the runmod blob is staged by mkdisk.py"
    names.add("runmod")
    assert re.search(r'_entry\(\s*"govtree"', text), "the govtree archive is staged by mkdisk.py"
    names.add("govtree")
    return names


def _diskcheck_accepted_optional_names():
    """The optional-content names check_body_read accepts (body_read_is_staged_content), parsed from
    src/body/diskcheck.c — the fs_name_eq(nm, "...") literals in that helper."""
    with open(DISKCHECK, encoding="utf-8") as f:
        text = f.read()
    fn = re.search(r"body_read_is_staged_content\(const char \*nm\)\s*\{(.*?)\n\}", text, re.S)
    assert fn, "body_read_is_staged_content() not found in diskcheck.c"
    return set(re.findall(r'fs_name_eq\(nm,\s*"([^"]+)"\)', fn.group(1)))


class TestBodyReadExpectedSetIsMkdiskDataMirror(unittest.TestCase):
    """MIRROR — the check's expected-optional set IS the names mkdisk.py stages, cross-checked as DATA."""

    def test_the_accepted_set_equals_the_names_mkdisk_stages(self):
        staged = _mkdisk_staged_optional_names()
        accepted = _diskcheck_accepted_optional_names()
        self.assertEqual(accepted, staged,
                         "diskcheck.c must accept EXACTLY the optional content names mkdisk.py stages "
                         "(re-pointed as data, not a frozen hand-count) — mkdisk=%s diskcheck=%s"
                         % (sorted(staged), sorted(accepted)))
        # the gate family, runmod and govtree are all present (the layout that stood P3b-4g..5b).
        for expected in ("govtree", "runmod", "syskey", "host_seam.py"):
            self.assertIn(expected, accepted, "%s is an accepted staged-content name" % expected)

    def test_the_required_core_and_selfb_absence_are_kept_and_the_c3_hand_count_is_gone(self):
        with open(DISKCHECK, encoding="utf-8") as f:
            text = f.read()
        fn = re.search(r"static int check_body_read\(void\)\s*\{(.*?)\n\}", text, re.S)
        self.assertIsNotNone(fn, "check_body_read() must be present")
        body = fn.group(1)
        # the required core + self-b absence + unexpected refusal are the PROPERTY (kept, L14).
        self.assertIn("has_record && has_pack && has_self_a && !has_self_b && !unexpected", body,
                      "the required-present + self-b-absent + unexpected-refusal property is kept")
        # the stale LOCATION — the exact three-entry hand-count — is gone (re-pointed, L14).
        self.assertNotRegex(body, r"c\s*==\s*3",
                            "the stale `c == 3` three-entry hand-count is removed (the location re-points)")


# ══ THE NESTED-GUEST BOOTS (each a FRESH disk image; one nested qemu at a time) ═══════════════════════
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes",
        "<GUEST>"]
_WD = "/tmp/c7maint-bodyread-accept"
_RUNMOD = "test_gate"   # any small module — its NAME is data on the disk; the plain body does not run it


def _guest_reachable():
    try:
        r = subprocess.run(_SSH + ["uname -r; command -v qemu-system-x86_64 >/dev/null && echo QEMU"],
                           capture_output=True, timeout=20)
    except Exception:
        return False
    out = r.stdout.decode(errors="replace")
    return r.returncode == 0 and "6.8.0-134-generic" in out and "QEMU" in out


GUEST = _guest_reachable()
_SEEDED = {"done": False}
_BUILT = {}


def _seed():
    """Seed the WHOLE src+tests tree once (GOVOS_TREE walks src/ + tests/, so both are needed)."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", ROOT, "src", "tests"], capture_output=True, timeout=180)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s" % (_WD, _WD)], capture_output=True, timeout=30, check=True)
    subprocess.run(_SSH + ["tar -xzf - -C %s" % _WD], input=tar.stdout, capture_output=True, timeout=180, check=True)
    _SEEDED["done"] = True


def _build(tag, fault=""):
    """Build the body (optionally with a -D plant FAULT) into out-<tag>; cached per tag."""
    if tag in _BUILT:
        return _BUILT[tag]
    _seed()
    out = "%s/out-%s" % (_WD, tag)
    b = subprocess.run(_SSH + ["cd %s/src && bash body/build.sh body %s %s" % (_WD, out, fault)],
                       capture_output=True, timeout=300)
    if b.returncode != 0:
        raise AssertionError("guest build (%s) failed: %s" % (tag, b.stderr.decode(errors="replace")))
    _BUILT[tag] = out
    return out


def _mkdisk_fresh(tag, tree=False):
    """A FRESH disk image (empty record) — a booted image would take the reboot path, so every
    self-check boot needs its own fresh image. `tree` stages GOVOS_TREE + GOVOS_RUNMOD (govtree+runmod)."""
    img = "%s/disk-%s.img" % (_WD, tag)
    env = ("GOVOS_TREE=1 GOVOS_RUNMOD=%s " % _RUNMOD) if tree else ""
    m = subprocess.run(
        _SSH + ["cd %s && %sPYTHONPATH=%s/src python3 src/body/mkdisk.py %s" % (_WD, env, _WD, img)],
        capture_output=True, timeout=120)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk (%s) failed: %s" % (tag, m.stderr.decode(errors="replace")))
    return img


def _boot(out, img, timeout_s=90):
    """Boot the body in a NESTED qemu (foreground, synchronous), return the serial. Kill any stray
    body qemu afterwards (single lane)."""
    boot = subprocess.run(
        _SSH + ["timeout --signal=KILL %d qemu-system-x86_64 -kernel %s/body.img "
                "-drive file=%s,format=raw,if=ide,index=0 -serial stdio -display none -no-reboot "
                "-m 256 -cpu qemu64 </dev/null 2>/dev/null; "
                "pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true" % (timeout_s, out, img)],
        capture_output=True, timeout=timeout_s + 40)
    return boot.stdout.decode(errors="replace")


def _check_fail_lines(serial):
    """Every `CHECK …: FAIL` / `SERVE CHECK …: FAIL` line in the serial (the A3 assertion's subject)."""
    return [ln for ln in serial.splitlines() if re.search(r"CHECK .*: FAIL", ln)]


@unittest.skipUnless(GUEST, "needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestBodyReadCheckOnBody(unittest.TestCase):

    # A1 / A3 — a clean PLAIN boot (record, founding-pack, self-a): the check passes, no FAIL line.
    def test_a1_a3_clean_plain_boot_passes_and_prints_no_fail_line(self):
        out = _build("plain")
        img = _mkdisk_fresh("plain")
        serial = _boot(out, img)
        self.assertIn("BODY-HALT", serial, "the body reaches BODY-HALT (a completed boot)")
        self.assertIn("DISK: OK", serial, "the record disk mounts")
        self.assertIn("CHECK BODY-READ: PASS", serial, "the re-pointed check passes on a plain boot")
        self.assertEqual(_check_fail_lines(serial), [],
                         "a clean boot prints NO CHECK/SERVE-CHECK FAIL line (A3)")

    # A1 / A3 — a clean TREE boot (record, founding-pack, govtree, runmod, self-a): the boot that USED
    # TO RED (test_c7_p3b_5a_iii §NOTE). The re-pointed check accepts govtree+runmod as data → PASS.
    def test_a1_a3_clean_tree_boot_passes_and_prints_no_fail_line(self):
        out = _build("plain")                 # a plain body reads the tree-staged disk; the disk carries govtree/runmod
        img = _mkdisk_fresh("tree", tree=True)
        serial = _boot(out, img)
        self.assertIn("BODY-HALT", serial, "the body reaches BODY-HALT")
        self.assertIn("DISK: OK", serial, "the record disk mounts")
        self.assertIn("CHECK BODY-READ: PASS", serial,
                      "the re-pointed check passes with govtree+runmod staged (was FAIL before, 5a-iii NOTE)")
        self.assertEqual(_check_fail_lines(serial), [],
                         "a clean TREE boot prints NO CHECK/SERVE-CHECK FAIL line (A3)")

    # A1 PLANT / A2 (unexpected) / A3 PLANT — a GHOST entry on the disk reds check_body_read (the
    # unexpected-entry refusal, L14) and thereby makes the A3 no-FAIL assertion able to fail.
    def test_a1_a2_a3_ghost_entry_reds_the_check(self):
        out = _build("ghost", fault="PLANT_BODY_READ_GHOST")
        img = _mkdisk_fresh("ghost")
        serial = _boot(out, img)
        self.assertIn("BODY-HALT", serial, "even a red self-check reaches BODY-HALT (a completed boot)")
        self.assertIn("CHECK BODY-READ: FAIL", serial,
                      "a ghost entry (a name in no expected set) reds the check (unexpected-entry refusal)")
        self.assertIn("ACTS: FAIL", serial, "the aggregate ACTS line reds with it")
        # only the body-read act reds — the ghost does not disturb the other record acts.
        self.assertIn("CHECK RECORD-PEN: PASS", serial, "the record-pen act is unaffected")
        # A3's assertion is genuinely able to fail: this boot DOES carry a CHECK …: FAIL line.
        self.assertIn("CHECK BODY-READ: FAIL", _check_fail_lines(serial),
                      "A3's no-FAIL assertion can fail — a forced FAIL is caught")

    # A2 — the MISSING-entry failure is preserved: PLANT_WALK_MISSES drops a present entry (record) →
    # the required core is missing → check_body_read reds (the guard still fails on a missing file).
    def test_a2_missing_entry_reds_the_check(self):
        out = _build("walkmiss", fault="PLANT_WALK_MISSES")
        img = _mkdisk_fresh("walkmiss")
        serial = _boot(out, img)
        self.assertIn("BODY-HALT", serial, "the body reaches BODY-HALT")
        self.assertIn("CHECK BODY-READ: FAIL", serial,
                      "a dropped (missing) expected entry reds the check (the missing-entry failure kept)")
        self.assertIn("ACTS: FAIL", serial, "the aggregate ACTS line reds with it")


if __name__ == "__main__":
    unittest.main()
