# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-tooling · machine register.
# The body arm of the C7 side-by-side: gov-os's OWN core, booted in a nested qemu inside the pinned guest
# (L11 / EP-00 rule 9), running the SAME stretch module via LEDGER mode (the P8 one-module-on-both form),
# one nested boot at a time. Reuses tools/bench/bench_body.py's preflight/seed/build/mkdisk/boot (not
# re-authored) with its own guest scratch. Runs and reports only (A5): the body is BUILT and BOOTED, never
# changed; the switch not taken. Full declaration: SCOPE-STATEMENT.md.
"""Run the stretch on gov-os's own core over SSH and write planning/evidence/C7-SIDE-BY-SIDE/body/.

    python3 tools/sidebyside/run_body.py build      # preflight + seed src/tests + the LEDGER body build
    python3 tools/sidebyside/run_body.py boot       # re-seed, then TWO serialized boots: agree + plant
    python3 tools/sidebyside/run_body.py all

Every boot: 0 nested qemu confirmed before it, strays pkilled after it; the guest kernel re-verified as the
pinned 6.8.0-134-generic. The agree boot's runmod is test_c7_side_by_side.TestBodyStretch (two runs in one
boot, the first with rows); the plant boot's is …TestBodyStretchPlanted (a clean control + the planted run).
"""

import os
import re
import sys

import sbs_common as sc
import bench_body as bb            # tools/bench — the P8 body driver, reused
import test_c7_side_by_side as sbs

bb.WD = "<HOME>/sbs"         # this unit's own guest scratch; P8's p8bench untouched
RUNMOD_AGREE = "test_c7_side_by_side.TestBodyStretch"
RUNMOD_PLANT = "test_c7_side_by_side.TestBodyStretchPlanted"
BOOT_MIB = 256
WAIT_S = 1500


def resync_tree():
    """Re-sync ONLY src/ and tests/ into the guest scratch (the CURRENT tree — the stretch module as it
    stands). bench_body.seed() does `rm -rf WD`, which would wipe the LEDGER build output that lives inside
    WD (out-ledger/) — the boot would then launch qemu with no kernel file. So the two trees are replaced
    in place and the build output is left alone."""
    import subprocess
    tar = subprocess.run(["tar", "-czf", "-", "-C", sc.ROOT, "src", "tests"],
                         capture_output=True, timeout=180, check=True)
    bb.guest("mkdir -p %s && rm -rf %s/src %s/tests" % (bb.WD, bb.WD, bb.WD), timeout=60, check=True)
    bb.guest("tar -xzf - -C %s" % bb.WD, timeout=180, check=True, inp=tar.stdout)
    print("re-synced src+tests to guest:%s (build output kept)" % bb.WD, flush=True)


def build():
    bb.preflight()
    bb.seed()
    out, txt = bb.build_ledger()
    m = re.search(r"sealed image seal sha256\s*[:=]?\s*([0-9a-f]{64})", txt)
    info = {"out": out, "guest_kernel": bb.GUEST_KERNEL, "wd": bb.WD,
            "sealed_image_sha256": m.group(1) if m else None,
            "build_tail": txt[-1500:]}
    sc.write_json(os.path.join(sc.EVID_BODY, "build.json"), info)
    print("build: out=%s sealed=%s" % (out, info["sealed_image_sha256"]))
    return out


def _boot(out, runmod, tag):
    img = bb.mkdisk(tag, tree=True, runmod=runmod)
    serial, halted = bb.boot(out, img, BOOT_MIB, tag, initrd=True, wait_s=WAIT_S)
    sc.write_text(os.path.join(sc.EVID_BODY, "serial-%s.txt" % tag), serial)
    m = re.search(r"LEDGER-RESULT (\S+) ran=(\d+) failures=(\d+) errors=(\d+) skipped=(\d+)", serial)
    ledres = m.group(0) if m else "(no LEDGER-RESULT)"
    results = sbs.parse_markers(serial)
    sc.write_json(os.path.join(sc.EVID_BODY, "ledger-%s.json" % tag),
                  {"ledger_result": ledres, "halted": halted, "runmod": runmod, "boot_mib": BOOT_MIB,
                   "results_parsed": [r.get("label") for r in results], "serial_bytes": len(serial)})
    print("boot %s: halted=%s %s parsed=%s" % (tag, halted, ledres, [r.get("label") for r in results]))
    if not m or m.group(1) != "OK":
        raise AssertionError("body run %s not green: %s\n%s" % (tag, ledres, serial[-3000:]))
    return results


def _pick(results, label):
    for r in results:
        if r.get("label") == label:
            assert r.get("performer") == "body", "result %r not tagged body: %r" % (label, r.get("performer"))
            return r
    raise AssertionError("no result labelled %r in %r" % (label, [r.get("label") for r in results]))


def boot(out=None):
    if out is None:
        out = sc.read_json(os.path.join(sc.EVID_BODY, "build.json"))["out"]
    resync_tree()                                      # the CURRENT tree; out-ledger/ untouched
    bb.preflight()
    r = bb.guest("test -f %s/body.img && test -f %s/sealed.img && echo IMAGES-OK" % (out, out), timeout=30)
    assert b"IMAGES-OK" in r.stdout, "the LEDGER build output is missing at %s — run `build` first" % out
    agree = _boot(out, RUNMOD_AGREE, "agree")
    a = _pick(agree, "agree")
    a2 = _pick(agree, "agree-rerun")
    assert a["rows"] and len(a["rows"]) == a["n_rows"], "the agree run's rows crossed the serial"
    assert sbs.stretch_digest(a["rows"]) == a["stretch_digest"], "transfer integrity: rows re-digest on the host"
    sc.write_json(os.path.join(sc.EVID_BODY, "agree.json"), sc.slim(a, True))
    sc.write_json(os.path.join(sc.EVID_BODY, "agree-rerun.json"), sc.slim(a2, False))
    print("  body agree %s | rerun %s | rows %d | bytes %d | manifest %s" % (
        a["stretch_digest"][:23], a2["stretch_digest"][:23], a["n_rows"], a["record_bytes"], a["manifest"]))
    bb.preflight()
    plant = _boot(out, RUNMOD_PLANT, "plant-content")
    c = _pick(plant, "clean-in-plant-boot")
    p = _pick(plant, "plant-content")
    assert p["rows"] and len(p["rows"]) == p["n_rows"], "the planted run's rows crossed the serial"
    assert sbs.stretch_digest(p["rows"]) == p["stretch_digest"], "transfer integrity (plant)"
    sc.write_json(os.path.join(sc.EVID_BODY, "plant-boot-clean.json"), sc.slim(c, False))
    sc.write_json(os.path.join(sc.EVID_BODY, "plant-content.json"), sc.slim(p, True))
    print("  body plant-boot clean %s | planted %s | divergent rows %s" % (
        c["stretch_digest"][:23], p["stretch_digest"][:23], sbs.divergent_rows(c["row_digests"], p["row_digests"])))
    assert bb.nested_count() == 0, "guest must return to 0 nested qemu"
    return a, a2, c, p


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    out = None
    if what in ("build", "all"):
        out = build()
    if what in ("boot", "all"):
        boot(out)
    print("DONE", what)
