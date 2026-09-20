# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-tooling · machine register.
# The C7 side-by-side drivers' shared plumbing: locate the repo, put the stretch module on the path, read/write
# the evidence tree, drive the body's caps from its source. Runs and compares only (A5): changes no core.
# Full declaration: SCOPE-STATEMENT.md.
"""Shared plumbing for tools/sidebyside (C7 SIDE-BY-SIDE, planning/exec/C7-SIDE-BY-SIDE.md).

The STRETCH and the MEASURE live in tests/test_c7_side_by_side.py so the identical code runs on BOTH
performers (the Linux carrier here; gov-os's own core via LEDGER mode). This module only locates that code
and reads/writes planning/evidence/C7-SIDE-BY-SIDE/.
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(ROOT, "src")
TESTS = os.path.join(ROOT, "tests")
BENCH = os.path.join(ROOT, "tools", "bench")
EVID = os.path.join(ROOT, "planning", "evidence", "C7-SIDE-BY-SIDE")
EVID_LINUX = os.path.join(EVID, "linux")
EVID_BODY = os.path.join(EVID, "body")

for _p in (SRC, TESTS, BENCH):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, sort_keys=True, separators=(",", ":"))
        f.write("\n")
    return path


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def slim(result, with_rows):
    """An evidence copy of a stretch result: never the in-process raw rows; rows only where asked."""
    drop = {"raw_rows"} | (set() if with_rows else {"rows"})
    return {k: v for k, v in result.items() if k not in drop}


def body_caps():
    """The body's as-built caps DRIVEN from src/body (the P8 run_caps idiom), never hardcoded."""
    with open(os.path.join(SRC, "body", "disk.h")) as f:
        disk_h = f.read()
    with open(os.path.join(SRC, "body", "mkdisk.py")) as f:
        mkdisk = f.read()
    sectors = int(re.search(r"BFS_DIR_SECTORS\s+(\d+)", disk_h).group(1))
    rec_sectors = int(re.search(r"RECORD_CAPACITY_SECTORS\s*=\s*(\d+)", mkdisk).group(1))
    return {
        "directory_entries_max": sectors * 2,
        "directory_entries_source": "src/body/disk.h BFS_MAX_ENTRIES = BFS_DIR_SECTORS(%d) * 2" % sectors,
        "fixed_record_bytes": rec_sectors * 512,
        "fixed_record_source": "src/body/mkdisk.py RECORD_CAPACITY_SECTORS = %d sectors * 512 (enforced "
                               "bodyfs.c fs_record_write_at)" % rec_sectors,
    }
