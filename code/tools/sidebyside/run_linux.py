# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-tooling · machine register.
# The Linux-carrier arm of the C7 side-by-side: runs the scripted stretch (tests/test_c7_side_by_side.py —
# the SAME module the body runs) in fresh governed worlds and writes the canonical results to evidence.
# Runs and reports only (A5): no core change, the switch not taken. Full declaration: SCOPE-STATEMENT.md.
"""Run the stretch on the Linux carrier and write planning/evidence/C7-SIDE-BY-SIDE/linux/ + STRETCH.json.

    python3 tools/sidebyside/run_linux.py

Writes: linux/run-1.json (with rows), linux/run-2.json (digests only — determinism across runs),
linux/plant-content.json (with rows — the real content divergence, Linux side), STRETCH.json (N + basis +
the body's caps driven from src).
"""

import os

import sbs_common as sc
import test_c7_side_by_side as sbs


def run():
    r1 = sbs.run_stretch(label="run-1")
    r2 = sbs.run_stretch(label="run-2")
    pl = sbs.run_stretch(plant="content", label="plant-content")
    assert r1["performer"] == "linux", r1["performer"]
    assert sbs.check_records_agree(r1, r2), "Linux runs must agree (determinism)"
    assert not sbs.check_records_agree(r1, pl), "the Linux content plant must red"
    sc.write_json(os.path.join(sc.EVID_LINUX, "run-1.json"), sc.slim(r1, True))
    sc.write_json(os.path.join(sc.EVID_LINUX, "run-2.json"), sc.slim(r2, False))
    sc.write_json(os.path.join(sc.EVID_LINUX, "plant-content.json"), sc.slim(pl, True))
    stretch = {
        "n_acts": sbs.N_ACTS,
        "rounds": sbs.ROUNDS,
        "acts_per_round": sbs.ACTS_PER_ROUND,
        "file_tree": [n for n, _ in sbs.FILE_TREE],
        "basis": sbs.STRETCH_BASIS,
        "excluded_fields": list(sbs.EXCLUDED_FIELDS),
        "per_run_fields": list(sbs.PER_RUN_FIELDS),
        "raw_bytes_anti_measure": sbs.RAW_BYTES_ANTI_MEASURE,
        "measure": "kernel.canonical.canonical_hash over the ORDERED list of projected rows (row minus the "
                   "closed excluded set); per-row canonical_hash for localisation; the checkpoint tree-state "
                   "merkle root and a computed-views digest published beside it",
        "body_cap": sc.body_caps(),
        "linux_measured": {"n_rows": r1["n_rows"], "genesis_rows": r1["genesis_rows"],
                           "stretch_rows": r1["stretch_rows"], "record_bytes": r1["record_bytes"],
                           "record_bytes_over_cap": round(r1["record_bytes"] / float(sc.body_caps()["fixed_record_bytes"]), 4)},
    }
    sc.write_json(os.path.join(sc.EVID, "STRETCH.json"), stretch)
    print("linux: run-1 %s | run-2 %s | plant %s | rows %d (genesis %d) | bytes %d | manifest %s" % (
        r1["stretch_digest"][:23], r2["stretch_digest"][:23], pl["stretch_digest"][:23], r1["n_rows"],
        r1["genesis_rows"], r1["record_bytes"], r1["manifest"]))
    print("divergent rows (run-1 vs plant):", sbs.divergent_rows(r1["row_digests"], pl["row_digests"]))
    return r1, r2, pl


if __name__ == "__main__":
    run()
    print("DONE linux")
