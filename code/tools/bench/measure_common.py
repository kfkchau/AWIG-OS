# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-tooling · machine register.
# The four-number benchmark drivers' shared helpers (C7 P8): locate the repo, put the measurement
# functions on the path, and read/write the evidence tree. Measurement only (A6): reads acts that
# already exist and writes figures out; changes no core. Full declaration: SCOPE-STATEMENT.md.
"""Shared plumbing for the C7 P8 benchmark drivers.

The MEASUREMENT logic lives in tests/test_c7_p8_numbers.py (so the identical code runs on BOTH
performers — on the Linux carrier here, and on gov-os's own core via LEDGER mode). This module only
locates that code, and reads/writes the evidence directory the digest consumes.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(ROOT, "src")
TESTS = os.path.join(ROOT, "tests")
EVID = os.path.join(ROOT, "planning", "evidence", "C7-P8-NUMBERS-AND-REVIEW")
EVID_LINUX = os.path.join(EVID, "linux")
EVID_BODY = os.path.join(EVID, "body")

for _p in (SRC, TESTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")
    return path


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)
