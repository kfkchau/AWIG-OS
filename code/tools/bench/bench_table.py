# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-tooling · machine register.
# Assemble the C7 P8 side-by-side table from both performers' figures — each WITH ITS BASIS, identical acts
# where both run (design/54 B9). Measurement only (A6). Full declaration: SCOPE-STATEMENT.md.
"""Read planning/evidence/.../linux/ and .../body/, build the side-by-side table (JSON + Markdown).

    python3 tools/bench/bench_table.py

Raises if a figure lacks its basis (basis-present) or a cross-performer pair's act sets differ
(identical-act-set) — the same checks the acceptance tests assert.
"""

import json
import os

import measure_common as mc
import test_c7_p8_numbers as p8

FIG_ORDER = ["rows_per_sec", "decide_latency_us", "verify_and_proof", "memory_floor"]
FIG_TITLE = {
    "rows_per_sec": "#1 rows appended per second (group commit)",
    "decide_latency_us": "#2 decision latency, enforcement carve-out, one compiled rule",
    "verify_and_proof": "#3 verify-without-engine + Merkle localisation-proof SIZE",
    "memory_floor": "#4 memory floor of a chained append",
}


def _load_dir(d):
    figs = []
    if not os.path.isdir(d):
        return figs
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json") and not fn.startswith("_") and fn not in (
                "ledger_result.json", "caps.json", "memory_sweep.json"):
            figs.append(mc.read_json(os.path.join(d, fn)))
    return figs


def _fmt(fig):
    if fig is None:
        return "—"
    v = fig["value"]
    return "%s %s" % (v, fig["unit"])


def build():
    linux = _load_dir(mc.EVID_LINUX)
    body = _load_dir(mc.EVID_BODY)
    caps = mc.read_json(os.path.join(mc.EVID_BODY, "caps.json")) if os.path.exists(
        os.path.join(mc.EVID_BODY, "caps.json")) else None
    sweep = mc.read_json(os.path.join(mc.EVID_BODY, "memory_sweep.json")) if os.path.exists(
        os.path.join(mc.EVID_BODY, "memory_sweep.json")) else None
    table = p8.build_side_by_side(linux, body)
    table["body_caps"] = caps
    table["body_memory_sweep_summary"] = None if sweep is None else {
        "smallest_green_mib": sweep.get("smallest_green_mib"),
        "largest_red_below_mib": sweep.get("largest_red_below_mib"),
        "grid": sweep.get("grid")}
    mc.write_json(os.path.join(mc.EVID, "SIDE-BY-SIDE-TABLE.json"), table)
    _write_md(table, linux, body, caps, sweep)
    print("wrote SIDE-BY-SIDE-TABLE.json / .md  (linux figs=%d, body figs=%d)" % (len(linux), len(body)))
    return table


def _by_name(figs):
    return {f["figure"]: f for f in figs}


def _write_md(table, linux, body, caps, sweep):
    L = _by_name(linux)
    B = _by_name(body)
    out = []
    out.append("# C7 P8 — THE FOUR NUMBERS, side by side under two performers\n")
    out.append("design/50 §4, read under the Linux carrier AND under gov-os's own core (design/54 B9). "
               "Each figure carries ITS BASIS; #1/#2 run on both with IDENTICAL act sets; #3's full "
               "one-million-row verify runs under Linux only (the body's 8 MiB record cannot hold 1M — a "
               "named limit), the body runs a scoped N with the identical acts, and the localisation-proof "
               "SIZE (size- and engine-independent) is the cross-performer figure of record; #4's memory "
               "floor is bracketed by a bounded sweep on the body.\n")
    out.append("| figure | Linux carrier | gov-os core (body) | identical act set? |")
    out.append("|---|---|---|---|")
    for name in FIG_ORDER:
        row = next((r for r in table["rows"] if r["figure"] == name), None)
        if row is None:
            continue
        ident = row.get("act_sets_identical")
        ident_s = "—" if ident is None else ("YES" if ident else "**NO**")
        out.append("| %s | %s | %s | %s |" % (FIG_TITLE.get(name, name), _fmt(row.get("linux")),
                                              _fmt(row.get("body")), ident_s))
    out.append("")
    # per-figure basis
    for name in FIG_ORDER:
        out.append("## %s\n" % FIG_TITLE.get(name, name))
        for perf, D in (("Linux carrier", L), ("gov-os core (body)", B)):
            f = D.get(name)
            if f is None:
                out.append("- **%s:** not run.\n" % perf)
                continue
            out.append("- **%s:** %s %s" % (perf, f["value"], f["unit"]))
            out.append("  - act set: `%s`" % ", ".join(f.get("manifest") or []) or "(none)")
            for k, v in sorted(f.get("basis", {}).items()):
                out.append("  - basis.%s: %s" % (k, v))
            if name == "verify_and_proof":
                out.append("  - localisation_proof_bytes: %s (the cross-performer figure of record)"
                           % f.get("localisation_proof_bytes"))
                for extra in ("verify_wall_s", "verify_cpu_s", "peak_rss_mb", "major_faults", "rows"):
                    if extra in f:
                        out.append("  - %s: %s" % (extra, f[extra]))
            out.append("")
    if caps:
        out.append("## The body's as-built caps (measured limits, published — a named limit is architecture)\n")
        out.append("- directory entries: %s (%s)" % (caps["directory_entries_max"], caps["directory_entries_source"]))
        out.append("- fixed append-only record: %s MiB (%s)" % (caps["fixed_record_MiB"], caps["fixed_record_source"]))
        out.append("- data region: %s MiB (%s)" % (caps["data_region_MiB"], caps["data_region_source"]))
        out.append("- %s\n" % caps["one_million_rows_note"])
    if sweep:
        out.append("## #4 the memory floor, bracketed (body, freestanding)\n")
        out.append("- workload: %s" % sweep["workload"])
        out.append("- sweep grid (MiB): %s" % sweep["grid_mib"])
        out.append("- smallest GREEN boot: %s MiB; largest RED boot below it: %s MiB (the real bracket, L19)"
                   % (sweep["smallest_green_mib"], sweep["largest_red_below_mib"]))
        out.append("")
        out.append("| -m (MiB) | boot |")
        out.append("|---|---|")
        for g in sweep["grid"]:
            out.append("| %s | %s |" % (g["mib"], "GREEN" if g["green"] else "RED"))
        out.append("")
    out.append("_%s_\n" % table["note"])
    with open(os.path.join(mc.EVID, "SIDE-BY-SIDE-TABLE.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))


if __name__ == "__main__":
    build()
