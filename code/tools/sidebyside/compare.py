# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-tooling · machine register.
# Assemble the C7 side-by-side AGREEMENT REPORT from both performers' evidence: what agreed, over how long a
# stretch, by which canonical measure; the plants shown redding; the raw-bytes anti-measure named. Reports
# only (A5): the switch of the real record onto the core is NOT taken here — the report is the INPUT the
# owner's eventual switch decision consumes. Full declaration: SCOPE-STATEMENT.md.
"""Read planning/evidence/C7-SIDE-BY-SIDE/{linux,body}/ and write AGREEMENT-REPORT.json + .md.

    python3 tools/sidebyside/compare.py

Raises if any load-bearing check fails (the same checks tests/test_c7_side_by_side.py asserts).
"""

import os

import sbs_common as sc
import test_c7_side_by_side as sbs


def build():
    L1 = sc.read_json(os.path.join(sc.EVID_LINUX, "run-1.json"))
    L2 = sc.read_json(os.path.join(sc.EVID_LINUX, "run-2.json"))
    LP = sc.read_json(os.path.join(sc.EVID_LINUX, "plant-content.json"))
    B = sc.read_json(os.path.join(sc.EVID_BODY, "agree.json"))
    B2 = sc.read_json(os.path.join(sc.EVID_BODY, "agree-rerun.json"))
    BC = sc.read_json(os.path.join(sc.EVID_BODY, "plant-boot-clean.json"))
    BP = sc.read_json(os.path.join(sc.EVID_BODY, "plant-content.json"))
    ST = sc.read_json(os.path.join(sc.EVID, "STRETCH.json"))

    agree = sbs.check_records_agree(L1, B)
    body_rows_ok = sbs.stretch_digest(B["rows"]) == B["stretch_digest"]
    acts_identical = sbs.check_identical_act_sets(L1["manifest"], B["manifest"])
    plant_body_reds = not sbs.check_records_agree(L1, BP)
    plant_linux_reds = not sbs.check_records_agree(L1, LP)
    div_body = sbs.divergent_rows(L1["row_digests"], BP["row_digests"])
    div_linux = sbs.divergent_rows(L1["row_digests"], LP["row_digests"])
    det_linux = sbs.check_records_agree(L1, L2)
    det_body_in_boot = sbs.check_records_agree(B, B2)
    det_body_across_boots = sbs.check_records_agree(B, BC)
    incidental_cross = (L1["raw_sha256"] != B["raw_sha256"])      # raw bytes differ, canonical equal
    rep = {
        "switch_taken": False,
        "verdict": "AGREE" if agree else "DIVERGE",
        "measure": ST["measure"],
        "excluded_fields": ST["excluded_fields"],
        "raw_bytes_anti_measure": ST["raw_bytes_anti_measure"],
        "stretch": {"n_acts": ST["n_acts"], "rounds": ST["rounds"], "basis": ST["basis"],
                    "n_rows": L1["n_rows"], "genesis_rows": L1["genesis_rows"], "stretch_rows": L1["stretch_rows"],
                    "record_bytes_linux": L1["record_bytes"], "record_bytes_body": B["record_bytes"],
                    "body_cap": ST["body_cap"]},
        "A1_identical_act_sets": {"linux": L1["manifest"], "body": B["manifest"], "identical": acts_identical},
        "A2_canonical_agreement": {"linux_stretch_digest": L1["stretch_digest"], "body_stretch_digest": B["stretch_digest"],
                                   "equal": agree, "tree_root_linux": L1["tree_root"], "tree_root_body": B["tree_root"],
                                   "tree_root_equal": L1["tree_root"] == B["tree_root"],
                                   "views_digest_equal": L1["views_digest"] == B["views_digest"],
                                   "body_rows_redigest_on_host": body_rows_ok,
                                   "divergent_rows": sbs.divergent_rows(L1["row_digests"], B["row_digests"])},
        "A2_incidental_bytes_differ_canonical_equal": {"linux_raw_sha256": L1["raw_sha256"], "body_raw_sha256": B["raw_sha256"],
                                                       "raw_differ": incidental_cross, "canonical_equal": agree,
                                                       "note": "the recording clock (three per-run fields) differs on "
                                                               "every row between the performers; a raw compare reds, "
                                                               "the canonical measure agrees"},
        "A3_planted_content_divergence": {"body_plant_digest": BP["stretch_digest"], "reds_vs_linux": plant_body_reds,
                                          "divergent_rows_vs_linux": div_body,
                                          "divergent_actions": [L1["rows"][i]["action"] for i in div_body if isinstance(i, int)],
                                          "planted_object": "sbs-doc-%03d%s" % (sbs.PLANT_ROUND, sbs.PLANT_SUFFIX),
                                          "linux_plant_digest": LP["stretch_digest"], "linux_plant_reds": plant_linux_reds,
                                          "divergent_rows_linux_plant": div_linux,
                                          "plant_boot_clean_control_agrees_with_linux": sbs.check_records_agree(L1, BC)},
        "determinism_across_runs": {"linux_two_runs": det_linux, "body_two_runs_one_boot": det_body_in_boot,
                                    "body_two_boots": det_body_across_boots},
        "A5": {"switch_taken": False, "released_performer_changed": False,
               "note": "this unit RUNS and REPORTS; the switch of the real record onto the core is the owner's "
                       "one-way word, named once at DIGEST-C7 and NOT restated here"},
        "basis": {"linux": L1["basis"], "body": B["basis"]},
    }
    for k, v in (("A2 equal", agree), ("A1 identical", acts_identical), ("A3 body plant reds", plant_body_reds),
                 ("A3 linux plant reds", plant_linux_reds), ("transfer", body_rows_ok), ("det linux", det_linux),
                 ("det body in-boot", det_body_in_boot), ("det body across boots", det_body_across_boots),
                 ("incidental cross", incidental_cross)):
        if not v:
            raise AssertionError("agreement report: %s is False" % k)
    sc.write_json(os.path.join(sc.EVID, "AGREEMENT-REPORT.json"), rep)
    _md(rep)
    print("wrote AGREEMENT-REPORT.json / .md — verdict %s over %d acts / %d rows" % (rep["verdict"], ST["n_acts"], L1["n_rows"]))
    return rep


def _md(rep):
    s = rep["stretch"]
    a2 = rep["A2_canonical_agreement"]
    a3 = rep["A3_planted_content_divergence"]
    out = []
    out.append("# C7 SIDE-BY-SIDE — agreement report (the same governed acts on both performers)\n")
    out.append("The same scripted stretch of ordinary governed acts ran under the Linux carrier AND on gov-os's own "
               "freestanding core (a nested qemu inside the pinned guest, LEDGER mode, the same test module). The two "
               "records are compared by the estate's CANONICAL digest over their rows — never the raw bytes. "
               "**Verdict: %s.** The switch of the real record onto the core is NOT taken here (the owner's one-way word).\n"
               % rep["verdict"])
    out.append("| item | Linux carrier | gov-os core (body) | equal? |")
    out.append("|---|---|---|---|")
    out.append("| canonical stretch digest | `%s` | `%s` | %s |" % (a2["linux_stretch_digest"], a2["body_stretch_digest"], a2["equal"]))
    out.append("| checkpoint tree-state (merkle root) | `%s` | `%s` | %s |" % (a2["tree_root_linux"], a2["tree_root_body"], a2["tree_root_equal"]))
    out.append("| computed views digest | (equal) | (equal) | %s |" % a2["views_digest_equal"])
    out.append("| act set (A1) | %s | %s | %s |" % (", ".join(rep["A1_identical_act_sets"]["linux"]),
                                                   ", ".join(rep["A1_identical_act_sets"]["body"]),
                                                   rep["A1_identical_act_sets"]["identical"]))
    ib = rep["A2_incidental_bytes_differ_canonical_equal"]
    out.append("| raw record sha256 (ANTI-MEASURE, not used) | `%s` | `%s` | differ: %s |" % (ib["linux_raw_sha256"][:16] + "…", ib["body_raw_sha256"][:16] + "…", ib["raw_differ"]))
    out.append("| record bytes | %d | %d | (incidental) |" % (s["record_bytes_linux"], s["record_bytes_body"]))
    out.append("")
    out.append("**The stretch (A4):** N = %d governed acts through the gate (%d rounds × %d: create an actor, grant sight, "
               "a consume decided under that grant, an append; plus a fixed 3-file tree), producing %d rows over a %d-row "
               "genesis = %d rows, %d bytes — %.1f%% of the body's 8 MiB fixed record cap (%d entries / %d bytes, driven from "
               "src/body). Refusal-free by construction (no `op-refused` row; a refusal would spawn two dual-audit mirror rows). "
               "GRANT-READ is dual-audited, so each grant carries two SYSTEM mirror rows — deterministic content.\n"
               % (s["n_acts"], s["rounds"], sbs.ACTS_PER_ROUND, s["stretch_rows"], s["genesis_rows"], s["n_rows"],
                  s["record_bytes_body"], 100.0 * s["record_bytes_body"] / s["body_cap"]["fixed_record_bytes"],
                  s["body_cap"]["directory_entries_max"], s["body_cap"]["fixed_record_bytes"]))
    out.append("**The measure (A2):** %s. Excluded per row (closed, measured): %s. %s\n"
               % (rep["measure"], ", ".join(rep["excluded_fields"]), rep["raw_bytes_anti_measure"]))
    out.append("**The plants (A3, L19):** a REAL content divergence planted on the body (round %d's object `%s`) reds against "
               "Linux — %s; divergent rows %s (%s). The same plant on Linux reds — %s. The plant boot's clean control agrees "
               "with Linux — %s. An incidental-only difference (the recording clock on every row, the real cross-performer "
               "case) STILL agrees — raw bytes differ (%s), canonical equal (%s).\n"
               % (sbs.PLANT_ROUND, a3["planted_object"], a3["reds_vs_linux"], a3["divergent_rows_vs_linux"],
                  ", ".join(a3["divergent_actions"]), a3["linux_plant_reds"], a3["plant_boot_clean_control_agrees_with_linux"],
                  ib["raw_differ"], ib["canonical_equal"]))
    d = rep["determinism_across_runs"]
    out.append("**Determinism across runs:** Linux two runs %s; body two runs in one boot %s; body two boots %s.\n"
               % (d["linux_two_runs"], d["body_two_runs_one_boot"], d["body_two_boots"]))
    out.append("**A5:** the switch is NOT taken; no src/kernel, src/body or founding change; ACT_KINDS 12, ATTESTED 88. "
               "This report is the input the owner's eventual switch decision consumes.\n")
    sc.write_text(os.path.join(sc.EVID, "AGREEMENT-REPORT.md"), "\n".join(out) + "\n")


if __name__ == "__main__":
    build()
    print("DONE compare")
