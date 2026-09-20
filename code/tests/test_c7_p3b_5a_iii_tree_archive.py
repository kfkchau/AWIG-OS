# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a freestanding kernel body serving the whole gov-os source+tests tree as CONTENT — ONE archive on
# its bespoke on-disk record format, resolved by a path finder that streams a file's exact bytes off
# the disk, as in the seL4/gVisor/Fuchsia and osdev literature). NON-GOAL: no offensive capability; the
# body reads its OWN disk's content and refuses a name not in the archive; validated by building/reading
# a real booted body, never by attack (governance-work-method). Every kernel touch is the guest's nested
# qemu (L11 / EP-00 rule 9 / §A21). Full declaration: SCOPE-STATEMENT.md.
"""C7 P3b-5a-iii acceptance — THE TREE ARCHIVE + FINDER (design/54 §7 P3b-5a; archi countersign :4257;
the manager's 5a sub-split, plan STOP f — slice THREE of three: acceptance A6 only. Slice one 5a-i built
the BODYFS02 format; slice two 5a-ii built the /rec/ namespace acts A2-A5; this builds A6).

The whole gov-os SOURCE+TESTS tree is staged as ONE archive blob "govtree" on the BODYFS02 record disk
(mkdisk.py, GOVOS_TREE=1). A finder EXTENDING 4g's record-disk resolver (serve.c serve_tree_open,
reachable through serve_openat_fs's "/rec/" path for the on-body interpreter that 5b will host) resolves
"/rec/<tree-path>" to the file's EXACT bytes, STREAMED on demand from the disk (files run past any single
buffer — opdefs.py 218 KiB, test_ep29.py 931 KiB). A name NOT in the archive refuses -ENOENT. This is the
content path the on-body ledger (row P3b-5b) imports gov-os from — the tree is CONTENT here, NEVER
re-homed into src and NEVER inside the borrowed sealed interpreter image (I7).

  A6  a KNOWN tree file read through the finder returns its EXACT bytes (byte-identical to the repo file);
      a name not in the archive refuses -ENOENT. Proven on the booted body (the DISK phase's self-check
      prints CHECK TREE-A6 + TREE-ACTS + TREE-ENOENT + a TREE-FILE line per known file with its len+crc),
      cross-checked byte-for-byte against the repo file off the body. PLANTS (a check that cannot fail is
      not a check): PLANT_TREE_TAMPER (a served byte flipped -> the crc byte-compare reds, L19) and
      PLANT_TREE_GHOST (a not-in-archive name served -> the ENOENT check reds).

The boot acceptances build+boot in the NESTED guest and skip when the pinned guest is not reachable over
SSH; the source/format checks run in main. Every kernel touch is the guest's nested qemu; the host kernel
is never touched (L11 / EP-00 rule 9 / §A21). Validated by building/reading a real booted body, never by
attack (governance-work-method).

NOTE on ACTS: a TREE image carries the extra "govtree" blob, so the P3b-2 disk self-check's check_body_read
(which asserts a pristine 3-entry disk: record/founding-pack/self-a) counts it and prints ACTS: FAIL —
IDENTICAL to how a 4g GATE image behaves (its gate blobs do the same); NOT a regression and NOT asserted
here. The standing P3b-2 suite boots a PLAIN (non-tree) image and stays green (its check_body_read is c==3).
"""

import os
import re
import subprocess
import sys
import unittest
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
SRC = os.path.join(ROOT, "src")
BODY = os.path.join(SRC, "body")
sys.path.insert(0, SRC)

# the known files the body's self-check resolves (serve.c TREE_KNOWN_SMALL / TREE_KNOWN_LARGE / TREE_ABSENT).
KNOWN_SMALL = "src/body/serial.c"      # a small hand-written source file
KNOWN_LARGE = "src/kernel/opdefs.py"   # > 64 KiB — proves streaming on demand, past any single buffer
ABSENT = "src/__gov-not-in-archive__.zzz"


def _read(rel):
    with open(os.path.join(BODY, rel), encoding="utf-8") as f:
        return f.read()


def _repo_len_crc(rel):
    with open(os.path.join(ROOT, rel), "rb") as f:
        data = f.read()
    return len(data), zlib.crc32(data) & 0xFFFFFFFF


# ── the source / format checks (main; no guest) ─────────────────────────────────────────────────
class TestSourceShapeAndFormat(unittest.TestCase):
    def test_no_new_src_member_attested_holds_at_88(self):
        from kernel import attestation
        self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88,
                         "5a-iii edits members in place (serve.c / mkdisk.py) — no new .c")
        for rel in ("body/serve.c", "body/mkdisk.py"):
            self.assertIn(rel, attestation.ATTESTED_MEMBERS, "%s is an attested member (edit-in-place)" % rel)

    def test_src_body_is_thirty_one_files_no_new_file(self):
        names = sorted(n for n in os.listdir(BODY)
                       if n != "__pycache__" and not n.endswith((".pyc", ".pyo")))
        self.assertEqual(len(names), 31, "src/body is 31 files (5a-iii adds none): %r" % names)

    def test_no_founding_act_kinds_twelve_pack_unchanged(self):
        import json
        from bridge.host_seam import ACT_KINDS
        self.assertEqual(len(ACT_KINDS), 12, "no new act kind — a finder is a body-read, not a kind (archi :4248)")
        pack = os.path.join(SRC, "founding", "founding-pack.json")
        with open(pack) as f:
            self.assertEqual(json.load(f)["founding_version"], "1.55.0", "no founding on a body slice")

    def test_serve_has_the_tree_finder_and_plants(self):
        sv = _read("serve.c")
        self.assertIn("static int serve_tree_open(const char *treepath)", sv, "the finder exists")
        self.assertIn("static void serve_tree_selfcheck(void)", sv, "the body-side A6 proof exists")
        self.assertIn('fs_find("govtree")', sv, "the finder resolves the ONE tree archive blob")
        self.assertIn('mem_eq(g_tree_scan, "GOVTREE1", 8)', sv, "the finder checks the GOVTREE1 magic")
        self.assertIn("serve_tree_open(rb)", sv, "the finder extends the /rec/ resolver (interpreter path, 5b)")
        for plant in ("PLANT_TREE_TAMPER", "PLANT_TREE_GHOST"):
            self.assertIn(plant, sv, "%s plant exists (a check that cannot fail is not a check)" % plant)

    def test_mkdisk_stages_the_whole_tree_as_one_archive(self):
        with open(os.path.join(BODY, "mkdisk.py"), encoding="utf-8") as f:
            mk = f.read()
        self.assertIn('TREE_MAGIC = b"GOVTREE1"', mk, "the GOVTREE1 archive magic is defined")
        self.assertIn("def _tree_files(", mk, "the tree walk (through host().walk) exists")
        self.assertIn("host().walk(", mk, "the tree is enumerated THROUGH THE SEAM (no direct os.walk; C7 P2)")
        self.assertIn('_entry("govtree", FT_BLOB', mk, "the tree is ONE archive blob on the record disk")

    def test_host_crossing_census_stays_clean(self):
        # mkdisk.py is censused as core (src/body); its tree walk must route through host(), never os.walk.
        from tools.conformance import host_crossing_census as census
        bad = census.undeclared_crossings()
        self.assertEqual(bad, {}, "a core module crosses to the host directly: %r" % bad)


# ── the archive round-trip (main; no guest): mkdisk's archive holds known files byte-identical ────
class TestArchiveRoundTripInPython(unittest.TestCase):
    """Build the tree image in-process and parse the GOVTREE1 archive exactly as the body's C finder
    does — proving the format + byte-identity of known files WITHOUT the guest (a fast regression that
    the booted-body test then confirms on the metal)."""

    @classmethod
    def setUpClass(cls):
        sys.argv_backup = None
        from body import mkdisk
        cls.mk = mkdisk
        with mkdisk.host().open_read_binary(mkdisk.PACK_PATH) as f:
            pack = f.read()
        cls.img, cls.info = mkdisk.build_image(pack, None, mkdisk._tree_files())

    def _archive(self):
        import struct
        SEC, ENTRY, NAME = 512, 256, 128
        base = 1 * SEC
        gv = None
        for i in range(1024 * 2):
            e = self.img[base + i * ENTRY: base + i * ENTRY + ENTRY]
            if e == b"\x00" * ENTRY:
                continue
            nm = e[:NAME].split(b"\x00")[0].decode("ascii", "replace")
            _, present, start, length, _, _, _, _ = struct.unpack("<8I", e[NAME:NAME + 32])
            if present and nm == "govtree":
                gv = (start, length)
        self.assertIsNotNone(gv, "the govtree archive blob is present in the directory")
        ab = gv[0] * SEC
        magic = self.img[ab:ab + 8]
        version, count, total = struct.unpack("<III", self.img[ab + 8:ab + 20])
        self.assertEqual(magic, b"GOVTREE1")
        self.assertEqual(version, 1)
        TPATH, TENT = 116, 128
        tbl = {}
        for i in range(count):
            b = ab + 512 + i * TENT
            ent = self.img[b:b + TENT]
            p = ent[:TPATH].split(b"\x00")[0].decode("ascii", "replace")
            off, ln, crc = struct.unpack("<III", ent[TPATH:TPATH + 12])
            tbl[p] = (ab + off, ln, crc)
        return count, tbl

    def test_known_files_are_byte_identical_to_the_repo(self):
        count, tbl = self._archive()
        self.assertGreater(count, 100, "the whole tree (hundreds of files) is staged")
        for rel in (KNOWN_SMALL, KNOWN_LARGE):
            self.assertIn(rel, tbl, "%s is in the tree archive" % rel)
            pos, ln, stored = tbl[rel]
            served = self.img[pos:pos + ln]
            with open(os.path.join(ROOT, rel), "rb") as f:
                repo = f.read()
            self.assertEqual(served, repo, "%s served bytes are byte-identical to the repo file" % rel)
            self.assertEqual(stored, zlib.crc32(repo) & 0xFFFFFFFF, "the stored crc equals the repo file's crc")

    def test_absent_name_is_not_in_the_archive(self):
        _, tbl = self._archive()
        self.assertNotIn(ABSENT, tbl, "a not-in-archive name is genuinely absent (the finder will ENOENT it)")

    def test_the_archive_and_a_module_scratch_coexist_in_the_64_mib_region(self):
        # A6/A7 sizing: the read-only tree archive + a module's per-module scratch worlds must coexist.
        free = self.info["free_after_staged_bytes"]
        per_module_max = 34.16 * 1024 * 1024  # test_ep24c per-module max write volume (5a-i basis)
        self.assertGreater(free, per_module_max,
                           "free space after the tree archive (%d bytes) must exceed the per-module max "
                           "scratch (%.0f bytes)" % (free, per_module_max))


# ── the nested-guest bridge (isolated per-unit scratch; every boot the guest's nested qemu) ──────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p3b5aiii-accept"


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
_SERIAL_CACHE = {}


def _seed_guest():
    """Seed the WHOLE gov-os source+tests tree in a repo-like layout (<WD>/src, <WD>/tests) so mkdisk can
    stage the tree archive. Excludes Python bytecode caches (regenerable) and the frozen tests/archive/
    subtree (owner-ruled STAY OUT ENTIRELY) — the same set mkdisk excludes."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(
        ["tar", "--exclude=__pycache__", "--exclude=*.pyc", "--exclude=*.pyo",
         "--exclude=./tests/archive", "-czf", "-", "-C", ROOT, "src", "tests"],
        capture_output=True, timeout=120)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s && tar -xzf - -C %s" % (_WD, _WD, _WD)],
                   input=tar.stdout, capture_output=True, timeout=120, check=True)
    _SEEDED["done"] = True


def _guest_build(outdir, fault=""):
    _seed_guest()
    b = subprocess.run(_SSH + ["bash %s/src/body/build.sh %s/src/body %s %s" % (_WD, _WD, outdir, fault)],
                       capture_output=True, timeout=180)
    if b.returncode != 0:
        raise AssertionError("guest build failed (%s): %s" % (fault, b.stderr.decode(errors="replace")))
    return outdir


def _guest_mkdisk(img):
    m = subprocess.run(
        _SSH + ["cd %s && PYTHONPATH=%s/src GOVOS_TREE=1 python3 src/body/mkdisk.py %s" % (_WD, _WD, img)],
        capture_output=True, timeout=120)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    if b"tree archive" not in m.stdout:
        raise AssertionError("the tree archive was not staged: " + m.stdout.decode(errors="replace"))
    return img


def _guest_boot(outdir, img):
    # SERIALIZED: one nested qemu at a time. Serial -> a guest FILE (survives the timeout SIGKILL), read
    # back after. -pidfile reaps by pid (no pattern that could self-match this shell). 45s: the tree
    # self-check streams a 218 KiB file (opdefs.py) on top of the standard boot.
    ser = "%s/serial.txt" % outdir
    pidf = "%s/qemu.pid" % outdir
    subprocess.run(
        _SSH + ["rm -f %s %s; timeout --signal=KILL 45 qemu-system-x86_64 -kernel %s/body.img "
                "-drive file=%s,format=raw,if=ide,index=0 -serial file:%s -display none -no-reboot "
                "-m 256 -pidfile %s </dev/null >/dev/null 2>&1; "
                "[ -f %s ] && kill -9 $(cat %s) 2>/dev/null; true"
                % (ser, pidf, outdir, img, ser, pidf, pidf, pidf)],
        capture_output=True, timeout=90)
    r = subprocess.run(_SSH + ["cat %s 2>/dev/null" % ser], capture_output=True, timeout=20)
    return r.stdout.decode(errors="replace").replace("\r", "")


def _serial(fault=""):
    """Build (with the fault), format a fresh TREE disk, boot in nested qemu — cached per fault tag.
    One nested qemu at a time (SERIALIZED)."""
    tag = fault or "clean"
    if tag not in _SERIAL_CACHE:
        out = _guest_build("%s/out-%s" % (_WD, tag), fault)
        img = _guest_mkdisk("%s/disk-%s.img" % (_WD, tag))
        _SERIAL_CACHE[tag] = _guest_boot(out, img)
    return _SERIAL_CACHE[tag]


def _serial_tree_file(serial, rel):
    """Parse a `TREE-FILE <rel> len=0x.. crc=0x.. stored=0x..` line -> (len, crc) ints, or None."""
    m = re.search(r"TREE-FILE %s len=0x([0-9a-f]+) crc=0x([0-9a-f]+) stored=0x([0-9a-f]+)"
                  % re.escape(rel), serial)
    if not m:
        return None
    return int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16)


def tearDownModule():
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                       capture_output=True, timeout=20)


# ── clean boot: the finder resolves known files byte-identical; a not-in-archive name -> ENOENT ──
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestTreeFinderPerformClean(unittest.TestCase):
    def test_clean_boot_a6_passes_and_bytes_are_identical_to_the_repo(self):
        serial = _serial()
        self.assertIn("DISK: OK", serial, "the BODYFS02 tree image mounts on the metal")
        self.assertIn("CHECK TREE-A6: PASS", serial, "a known tree file resolves byte-identical (A6)")
        self.assertIn("TREE-ENOENT: PASS", serial, "a not-in-archive name refuses -ENOENT (A6)")
        self.assertIn("TREE-ACTS: PASS", serial, "the aggregate tree-archive proof passes")
        # the 5a-ii namespace acts stay green on the tree image (no coupling); twelve rows unchanged.
        self.assertIn("NS-ACTS: PASS", serial, "the /rec/ namespace acts (5a-ii) still pass (regression)")
        self.assertIn("ROWS-COUNT: 0000000c", serial, "twelve rows (0x0c) — a finder is not a new act kind")
        # byte-identity to the REPO, off the body: the served (len, crc) equal the repo file's.
        for rel in (KNOWN_SMALL, KNOWN_LARGE):
            parsed = _serial_tree_file(serial, rel)
            self.assertIsNotNone(parsed, "the body reported a TREE-FILE line for %s" % rel)
            got_len, got_crc, stored = parsed
            exp_len, exp_crc = _repo_len_crc(rel)
            self.assertEqual(got_len, exp_len, "%s served length equals the repo file's" % rel)
            self.assertEqual(got_crc, exp_crc, "%s served bytes are byte-identical to the repo file" % rel)
            self.assertEqual(got_crc, stored, "%s streamed crc equals the archive's stored crc" % rel)

    def test_large_file_streams_past_a_single_buffer(self):
        serial = _serial()
        parsed = _serial_tree_file(serial, KNOWN_LARGE)
        self.assertIsNotNone(parsed, "the > 64 KiB file was served")
        self.assertGreater(parsed[0], 65536, "%s is served whole (> 64 KiB), proving on-demand streaming"
                           % KNOWN_LARGE)


# ── PLANT_TREE_TAMPER: a served byte flipped -> the byte-compare reds (L19) ───────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
class TestTamperRedsTheByteCompare(unittest.TestCase):
    def test_a_tampered_archive_byte_reds_a6(self):
        serial = _serial("PLANT_TREE_TAMPER")
        self.assertIn("CHECK TREE-A6: FAIL", serial,
                      "a tampered served byte reds the known-file byte-compare (L19)")
        self.assertIn("TREE-ACTS: FAIL", serial, "the aggregate reds")
        # the served crc no longer equals the repo file's crc (the byte-compare, off the body).
        parsed = _serial_tree_file(serial, KNOWN_SMALL)
        if parsed is not None:
            _, got_crc, _ = parsed
            _, exp_crc = _repo_len_crc(KNOWN_SMALL)
            self.assertNotEqual(got_crc, exp_crc, "the tampered served bytes differ from the repo file")


# ── PLANT_TREE_GHOST: a not-in-archive name served -> the ENOENT check reds ───────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the body run needs the pinned guest + nested qemu")
class TestGhostRedsTheEnoentCheck(unittest.TestCase):
    def test_a_not_in_archive_name_served_reds_enoent(self):
        serial = _serial("PLANT_TREE_GHOST")
        self.assertIn("TREE-ENOENT: FAIL", serial, "a not-in-archive name served (not ENOENT) reds the check")
        self.assertIn("CHECK TREE-A6: FAIL", serial, "the aggregate reds")
        self.assertIn("TREE-ACTS: FAIL", serial, "the aggregate reds")


if __name__ == "__main__":
    unittest.main()
