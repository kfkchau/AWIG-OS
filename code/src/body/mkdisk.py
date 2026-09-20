# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS body — the disk-image build tool (C7 P3b-2; design/54 §7 P3b-2, §9).

An ATTESTED src member (§9 mechanism 1: ONE attested list). It formats a raw BODYFS disk image the
nested qemu presents to the body: the superblock, the directory, an EMPTY append-only record file,
and the founding pack (its exact bytes + a crc32). The body MOUNTS this image and performs the five
record acts on it; the body never formats. This tool mirrors the on-disk layout in src/body/disk.h
and src/body/bodyfs.c byte-for-byte — an mkfs tool mirrors its filesystem driver.

THE SEAM BINDS THIS PYTHON (mgr :4013, C7 P2). This is core src/ code (the census zones src/body as
CORE), so its file I/O routes through the host seam — the pack read through host().open_read_binary
and the image written through host().write_bytes, never a direct builtin open(). A direct open()
here would red the C7 P2 host-crossing census. The body's own C block driver (ata.c) is the metal
performer BENEATH the seam — it is not a host crossing; the seam-routing binds THIS host-side tool.

WHAT IS ON THE DISK, HONESTLY: the pack bytes are HOST DATA laid onto the image by this tool; the
body reads them back and matches their crc to the recorded one — "the founding pack read from the
body's own disk equal to the pack". Nothing here stands the body as a production performer, edits
the pack, or touches a host kernel (design/54 §6 I6; L11).

Run from the repo root (or a guest scratch with body/ bridge/ founding/ siblings on the path):
    PYTHONPATH=src python3 src/body/mkdisk.py <out.img>
"""

import os
import pathlib
import struct
import sys
import zlib

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, os.pardir))
sys.path.insert(0, _SRC)

from bridge.host_seam import host  # noqa: E402

PACK_PATH = os.path.join(_SRC, "founding", "founding-pack.json")

# ── the BODYFS02 layout, mirrored from src/body/disk.h byte-for-byte ──────────────────────────
# C7 P3b-5a-i: BODYFS02 grows the format to carry path-named namespaces, sized by the measurement
# (planning/evidence/C7-P3b-5s2-WRITE-CLASSES + the 5a pre-flight, archi :4257): name[128] >= the
# 92-byte longest path; 2048 entries >= the 1,230 per-module max path count (test_ep40); a 64 MiB
# data region >= 1.9x the 34.16 MiB per-module max write volume (test_ep24c). A fresh image / module.
SECTOR = 512
MAGIC = b"BODYFS02"
VERSION = 2
NAME_MAX = 128                                        # struct bfs_entry.name[128] (path names)
ENTRY_SIZE = 256                                      # name[128] + 8 u32 (32) + pad -> 2 entries/sector
DIR_START = 1
DIR_SECTORS = 1024                                    # 1024 * 2 = 2048 entries
DATA_START = DIR_START + DIR_SECTORS                  # 1025
ENTRIES_PER_SECTOR = SECTOR // ENTRY_SIZE             # 2
MAX_ENTRIES = DIR_SECTORS * ENTRIES_PER_SECTOR        # 2048
DATA_REGION_SECTORS = (64 * 1024 * 1024) // SECTOR    # 131072 sectors = 64 MiB
FT_FREE, FT_RECORD, FT_BLOB, FT_PACK = 0, 1, 2, 3

RECORD_CAPACITY_SECTORS = 16384                       # 8 MiB append-only record log (was 64 = 32 KiB)

# ── C7 P3b-4g — GATE ON THE BODY: AWIG OS's OWN gate as CONTENT on the record disk ──────────────
# The gate's Python governing code (keys/crypto/canonical/signer + the seam) reaches the body as
# CONTENT on its record disk (:4091 c — imported BY NAME by the body-hosted interpreter, NEVER
# inside the borrowed sealed image; the two witness classes kept apart, I7). Plus a guest TEST key
# (:4091 d — the owner's key material never on the body). Staged ONLY when GOVOS_GATE is set, so a
# non-GATE image is byte-identical to before. The on-disk entry names match the interpreter's
# record-disk finder (enclosure.c g_gate_script _MODMAP).
GATE_MODULES = [
    ("ker_init.py", os.path.join("kernel", "__init__.py")),
    ("keys.py", os.path.join("kernel", "keys.py")),
    ("crypto.py", os.path.join("kernel", "crypto.py")),
    ("canonical.py", os.path.join("kernel", "canonical.py")),
    ("signer.py", os.path.join("kernel", "signer.py")),
    ("brg_init.py", os.path.join("bridge", "__init__.py")),
    ("host_seam.py", os.path.join("bridge", "host_seam.py")),
]
# a guest TEST signing seed — NOT the owner's key material (:4091 d). Fixed bytes so the build is
# reproducible and the off-body reader can bind the same custody.
GATE_TEST_SEED = b"gov-os-guest-test-signing-seed-p3b4g-not-the-owners-key-01"


def _gate_files():
    """Read the AWIG OS gate source (the CURRENT shipping bytes) + the guest test seed, THROUGH THE
    SEAM (C7 P2 — no direct builtin open()). Returns an ordered list of (entry_name, bytes)."""
    out = []
    for entry, rel in GATE_MODULES:
        with host().open_read_binary(os.path.join(_SRC, rel)) as f:
            out.append((entry, f.read()))
    out.append(("syskey", GATE_TEST_SEED))
    return out


# ── C7 P3b-5a-iii — THE WHOLE AWIG OS SOURCE+TESTS TREE AS CONTENT ON THE RECORD DISK (A6, I7) ────
# The AWIG OS tree reaches the body as CONTENT — ONE archive blob on the record disk (BODYFS02),
# resolved by a finder EXTENDING 4g's (serve.c serve_tree_open). The tree is NEVER re-homed into src
# and NEVER placed inside the borrowed sealed interpreter image (I7 — two witness classes kept apart).
# This is the content path the on-body ledger (row P3b-5b) imports AWIG OS from. Staged ONLY when
# GOVOS_TREE is set, so a non-TREE image is byte-identical to before (5a-i/5a-ii invariant held).
#
# THE ARCHIVE FORMAT (GOVTREE1) — the body's finder (serve.c) mirrors this byte-for-byte:
#   sector 0  header (512): magic "GOVTREE1"(8) + version u32(=1) + count u32 + total_len u32 + pad
#   sector 1+ entry table: `count` × 128-byte entries {path[116] nul-padded, offset u32, length u32,
#             crc32 u32}, 4 entries/sector, sorted by path (byte-reproducible)
#   next sec  file-byte region: each file's bytes at its byte-exact `offset` (from archive start)
# offset/length/crc are read by the body's streaming finder; crc32 is IEEE-reflected (== zlib.crc32),
# so the body's own crc32 (bodyfs.c) matches this for a byte-identity self-check that CAN fail.
TREE_MAGIC = b"GOVTREE1"
TREE_VERSION = 1
TREE_PATH_MAX = 116                                   # >= the longest tree path (measured max 52 bytes)
TREE_ENTRY_SIZE = 128                                 # path[116] + 3 u32 (12) -> 4 entries / sector
TREE_ENTRIES_PER_SECTOR = SECTOR // TREE_ENTRY_SIZE    # 4
# the tree is src/ + tests/ (the LIVE source+tests tree). Excluded: Python bytecode caches (regenerable
# artifacts, not source) and the FROZEN tests/archive/ subtree (owner-ruled STAY OUT ENTIRELY; retired
# docs, not the live importable tree the ledger imports AWIG OS from). The set is reported at build.
TREE_ROOTS = ("src", "tests")
TREE_EXCLUDE_DIRS = ("__pycache__",)
TREE_EXCLUDE_SUFFIXES = (".pyc", ".pyo")
TREE_EXCLUDE_PREFIXES = ("tests/archive/", "tests/archive")


def _tree_files():
    """Walk the LIVE AWIG OS source+tests tree THROUGH THE SEAM (host().walk — a declared body-read act,
    never a direct os.walk; C7 P2), read each file's CURRENT shipping bytes through the seam, and return
    a list of (relpath, bytes) SORTED by relpath (byte-reproducible). `relpath` is repo-root-relative
    (e.g. "src/kernel/opdefs.py") — the exact name the body's /rec/<tree-path> finder resolves."""
    repo_root = os.path.dirname(_SRC)
    out = []
    for top in TREE_ROOTS:
        top_abs = os.path.join(repo_root, top)
        for dirpath, dirnames, filenames in host().walk(top_abs):
            dirnames[:] = [d for d in dirnames if d not in TREE_EXCLUDE_DIRS]
            for name in filenames:
                if name.endswith(TREE_EXCLUDE_SUFFIXES):
                    continue
                abs_path = os.path.join(dirpath, name)
                rel = os.path.relpath(abs_path, repo_root).replace(os.sep, "/")
                if rel.startswith(TREE_EXCLUDE_PREFIXES):
                    continue
                with host().open_read_binary(abs_path) as f:
                    out.append((rel, f.read()))
    out.sort(key=lambda pb: pb[0])
    return out


def _build_tree_archive(tree_files):
    """The GOVTREE1 archive bytes: header sector + entry table + file-byte region. `tree_files` is the
    SORTED (relpath, bytes) list from _tree_files. Returns the archive bytes (padded to a sector)."""
    count = len(tree_files)
    table_sectors = (count + TREE_ENTRIES_PER_SECTOR - 1) // TREE_ENTRIES_PER_SECTOR
    region_start = (1 + table_sectors) * SECTOR                # file bytes begin sector-aligned

    entries = bytearray()
    region = bytearray()
    cursor = region_start                                       # byte offset from archive start
    for rel, data in tree_files:
        rb = rel.encode("ascii")
        if len(rb) > TREE_PATH_MAX:                             # REFUSED, never truncated (a path collision)
            raise ValueError("tree path %r is %d bytes > TREE_PATH_MAX %d" % (rel, len(rb), TREE_PATH_MAX))
        rb = rb + b"\x00" * (TREE_PATH_MAX - len(rb))
        crc = zlib.crc32(data) & 0xFFFFFFFF
        entries += rb + struct.pack("<III", cursor, len(data), crc)
        region += data
        cursor += len(data)
    entries += b"\x00" * (table_sectors * SECTOR - len(entries))   # pad the table to a sector boundary

    total_len = region_start + len(region)
    header = TREE_MAGIC + struct.pack("<III", TREE_VERSION, count, total_len)
    header = header + b"\x00" * (SECTOR - len(header))
    archive = bytearray()
    archive += header
    archive += entries
    archive += region
    if len(archive) % SECTOR:                                   # pad the whole archive to a sector
        archive += b"\x00" * (SECTOR - (len(archive) % SECTOR))
    return bytes(archive)


def _ceil_sectors(nbytes):
    return (nbytes + SECTOR - 1) // SECTOR


def _superblock(next_free, total_sectors, dir_count):
    """Sector 0 — struct bfs_super, little-endian, padded to 512 bytes."""
    head = MAGIC + struct.pack(
        "<8I", VERSION, SECTOR, DIR_START, DIR_SECTORS, DATA_START,
        next_free, total_sectors, dir_count)
    return head + b"\x00" * (SECTOR - len(head))


def _entry(name, type_, present, start_sector, length, capacity_sectors, crc32, append_only):
    """A 256-byte struct bfs_entry, little-endian (BODYFS02). A name longer than the field is
    REFUSED, never truncated (names are paths — a truncated name could collide with a shorter one)."""
    nm = name.encode("ascii")
    if len(nm) > NAME_MAX:
        raise ValueError("bodyfs name %r is %d bytes > NAME_MAX %d (never truncated)"
                         % (name, len(nm), NAME_MAX))
    nm = nm + b"\x00" * (NAME_MAX - len(nm))
    body = nm + struct.pack("<8I", type_, present, start_sector, length,
                            capacity_sectors, crc32, append_only, 0)
    return body + b"\x00" * (ENTRY_SIZE - len(body))          # pad to ENTRY_SIZE (256)


def build_image(pack_bytes, gate_files=None, tree_files=None, runmod=None):
    """The raw BODYFS image bytes: superblock + directory + empty record + the founding pack. With
    `gate_files` (C7 P3b-4g), the AWIG OS gate source + the guest test key are staged as write-once
    BLOB entries AFTER the pack (content on the record disk, :4091 c/d). With `tree_files` (C7 P3b-5a-iii,
    A6/I7), the WHOLE AWIG OS source+tests tree is staged as ONE GOVTREE1 archive BLOB "govtree" — the
    content the on-body ledger imports AWIG OS from, resolved by serve.c's finder. With `runmod` (C7
    P3b-5b-i, precision 2), the estate test module to run is named as DATA in a "runmod" blob — the
    per-module fresh image names its module; the body lays the argv from it. A non-GATE, non-TREE,
    non-RUNMOD image is byte-identical to before (the 5a-i/5a-ii invariant)."""
    pack_len = len(pack_bytes)
    pack_crc = zlib.crc32(pack_bytes) & 0xFFFFFFFF

    record_start = DATA_START
    pack_start = record_start + RECORD_CAPACITY_SECTORS
    pack_capacity = _ceil_sectors(pack_len)

    # the directory: entry 0 = the append-only record (empty), entry 1 = the founding pack.
    entries = [
        _entry("record", FT_RECORD, 1, record_start, 0, RECORD_CAPACITY_SECTORS, 0, 1),
        _entry("founding-pack", FT_PACK, 1, pack_start, pack_len, pack_capacity, pack_crc, 0),
    ]
    # C7 P3b-4g: stage the gate content as blobs after the pack, each sector-aligned.
    cur = pack_start + pack_capacity
    blob_layout = []                                    # (start_sector, bytes) in entry order
    for name, data in (gate_files or []):
        cap = _ceil_sectors(len(data)) or 1
        entries.append(_entry(name, FT_BLOB, 1, cur, len(data), cap, 0, 0))
        blob_layout.append((cur, data))
        cur += cap
    # C7 P3b-5b-i: the module to run, named as DATA (a "runmod" blob) — the body reads it and lays argv.
    if runmod is not None:
        rm = runmod.encode("ascii")
        cap = _ceil_sectors(len(rm)) or 1
        entries.append(_entry("runmod", FT_BLOB, 1, cur, len(rm), cap, 0, 0))
        blob_layout.append((cur, rm))
        cur += cap
    # C7 P3b-5a-iii: the whole tree as ONE archive blob "govtree", sector-aligned after the gate (A6).
    tree_archive = None
    tree_start = 0
    if tree_files is not None:
        tree_archive = _build_tree_archive(tree_files)
        cap = _ceil_sectors(len(tree_archive)) or 1
        tree_start = cur
        entries.append(_entry("govtree", FT_BLOB, 1, cur, len(tree_archive), cap, 0, 0))
        blob_layout.append((cur, tree_archive))
        cur += cap
    next_free = cur
    # the data region is exactly 64 MiB (>= 1.9x the 34.16 MiB per-module max write volume); the blob
    # allocator hands out sectors from next_free up to total_sectors. The tree archive is READ-ONLY
    # content, SEPARATE from a module's per-module scratch worlds — both coexist within this region.
    total_sectors = DATA_START + DATA_REGION_SECTORS
    assert total_sectors > next_free, \
        "the staged content (record cap + pack + gate + tree archive) overflows the 64 MiB data region"

    while len(entries) < MAX_ENTRIES:
        entries.append(b"\x00" * ENTRY_SIZE)
    assert len(entries) <= MAX_ENTRIES, "too many bodyfs entries (max %d)" % MAX_ENTRIES

    img = bytearray(total_sectors * SECTOR)
    used = len([e for e in entries if e != b"\x00" * ENTRY_SIZE])   # real entries (free padding excluded)
    img[0:SECTOR] = _superblock(next_free, total_sectors, used)
    dir_bytes = b"".join(entries)
    img[DIR_START * SECTOR: DIR_START * SECTOR + len(dir_bytes)] = dir_bytes
    img[pack_start * SECTOR: pack_start * SECTOR + pack_len] = pack_bytes
    for start, data in blob_layout:
        img[start * SECTOR: start * SECTOR + len(data)] = data
    info = {"pack_len": pack_len, "pack_crc": pack_crc,
            "total_sectors": total_sectors, "next_free": next_free,
            "pack_start": pack_start,
            "gate_entries": len(gate_files or []),
            "tree_entries": (len(tree_files) if tree_files is not None else 0),
            "tree_start": tree_start,
            "tree_archive_bytes": (len(tree_archive) if tree_archive is not None else 0),
            "data_region_bytes": DATA_REGION_SECTORS * SECTOR,
            "free_after_staged_bytes": (total_sectors - next_free) * SECTOR}
    return bytes(img), info


# ── C7 P3b-5b-i — THE PLANT (staged only; the repo test file is NEVER edited, L19) ─────────────────────
# Appending a REAL failing assertion to the STAGED bytes of ONE module proves the run stack carries a real
# failure faithfully: the real interpreter runs the real (now-failing) module and the real exit status reds.
# No runner of ours reads or fabricates a test's outcome (design/54 §5 L19; §7 P3b-5b precision 5). Staged
# in the tree archive only — the repo file is untouched.
_PLANT_SUFFIX = (
    b"\n\n# C7 P3b-5b-i PLANT (staged only; the repo file is never edited, L19).\n"
    b"import unittest as _pl_ut\n"
    b"class _Plant5biFaithfulFailure(_pl_ut.TestCase):\n"
    b"    def test_plant_5bi_a_real_assertion_reddens_the_run(self):\n"
    b"        self.assertEqual('intact', 'planted',\n"
    b"            'PLANT 5b-i: a real assertion planted in a real module reddens the real run (L19)')\n")


def _plant_assertion(tree_files, mod):
    """Append a REAL failing assertion to the STAGED bytes of tests/<mod>.py (never the repo file)."""
    rel = "tests/%s.py" % mod
    out, hit = [], False
    for r, data in tree_files:
        if r == rel:
            data = data + _PLANT_SUFFIX
            hit = True
        out.append((r, data))
    if not hit:
        raise ValueError("plant target %r not in the tree archive" % rel)
    return out


def generate(out_path, pack_path=PACK_PATH, gate=False, tree=False, runmod=None, plant_mod=None):
    # read the pack bytes + write the image THROUGH THE SEAM (C7 P2) — no direct builtin open().
    with host().open_read_binary(pack_path) as f:
        pack_bytes = f.read()
    gate_files = _gate_files() if gate else None
    tree_files = _tree_files() if tree else None
    if tree_files is not None and plant_mod:
        tree_files = _plant_assertion(tree_files, plant_mod)   # C7 P3b-5b-i: stage a planted variant
    img, info = build_image(pack_bytes, gate_files, tree_files, runmod=runmod)
    host().write_bytes(pathlib.Path(out_path), img)
    info["runmod"] = runmod
    info["plant_mod"] = plant_mod
    return info


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "disk.img"
    gate = os.environ.get("GOVOS_GATE") == "1" or "--gate" in sys.argv[2:]
    tree = os.environ.get("GOVOS_TREE") == "1" or "--tree" in sys.argv[2:]
    runmod = os.environ.get("GOVOS_RUNMOD") or None
    plant_mod = os.environ.get("GOVOS_PLANT_MOD") or None
    meta = generate(out, gate=gate, tree=tree, runmod=runmod, plant_mod=plant_mod)
    print("wrote %s: %d sectors, pack %d bytes crc 0x%08x at sector %d%s%s%s%s"
          % (out, meta["total_sectors"], meta["pack_len"], meta["pack_crc"], meta["pack_start"],
             (", gate content: %d entries" % meta["gate_entries"]) if gate else "",
             (", tree archive: %d files %d bytes at sector %d (%d bytes free after staged)"
              % (meta["tree_entries"], meta["tree_archive_bytes"], meta["tree_start"],
                 meta["free_after_staged_bytes"])) if tree else "",
             (", runmod=%s" % runmod) if runmod else "",
             (", PLANTED %s" % plant_mod) if plant_mod else ""))
