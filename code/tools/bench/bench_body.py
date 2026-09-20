# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-tooling · machine register.
# The body arm of the C7 P8 four-number benchmark: gov-os's OWN core, measured in a nested qemu inside the
# pinned guest (L11 / EP-00 rule 9). #1/#2/#3 run via LEDGER mode (the SAME test module the Linux arm runs,
# so the acts are identical by construction, B9); #4 boots the FREESTANDING body at a grid of RAM sizes and
# brackets the memory floor of its record append self-check. ONE nested boot at a time. Measurement only
# (A6): no core edit; the body is BUILT and BOOTED, never changed. Full declaration: SCOPE-STATEMENT.md.
"""Measure the body-side figures over SSH and write planning/evidence/.../body/.

Usage (run from the repo root):
    python3 tools/bench/bench_body.py preflight     # uname pin + 0 nested + mem
    python3 tools/bench/bench_body.py caps          # record the body's as-built caps (2048 / 8 MiB / 64 MiB)
    python3 tools/bench/bench_body.py ledger        # #1/#2/#3 via LEDGER (one boot)
    python3 tools/bench/bench_body.py sweep         # #4 the freestanding memory-floor sweep (many boots)
    python3 tools/bench/bench_body.py all

Every body boot is serialized: 0 nested qemu is confirmed before it, strays are pkilled after it. The guest
is the pinned 6.8.0-134-generic (re-verified before booting). The LEDGER run's runmod is
`test_c7_p8_numbers.TestBodyMeasure` — the identical measurement code, so the body's act set matches Linux's.
"""

import json
import os
import re
import subprocess
import sys
import time

import measure_common as mc

GUEST_KERNEL = "6.8.0-134-generic"
SSH = ["<SSH-INVOCATION>", "-i", os.path.expanduser("<KEYPATH>"),
       "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=20", "<GUEST>"]
WD = "<HOME>/p8bench"
QEMU = "qemu-system-x86_64 -cpu qemu64 -display none -no-reboot -rtc base=utc"
RUNMOD = "test_c7_p8_numbers.TestBodyMeasure"
SWEEP_GRID_MIB = [256, 128, 64, 48, 32, 24, 20, 16, 14, 12, 10, 8, 6, 4]


def guest(cmd, timeout=120, check=False, inp=None):
    r = subprocess.run(SSH + [cmd], capture_output=True, timeout=timeout, input=inp)
    if check and r.returncode != 0:
        raise AssertionError("guest cmd failed (%d): %s\n%s" % (r.returncode, cmd,
                                                                r.stderr.decode(errors="replace")))
    return r


def nested_count():
    r = guest("pgrep -af '[q]emu-system-x86_64' | wc -l", timeout=30)
    try:
        return int(r.stdout.decode().strip().splitlines()[-1])
    except Exception:
        return -1


def kill_strays():
    guest("pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true", timeout=30)


def preflight():
    r = guest("uname -r", timeout=30, check=True)
    uname = r.stdout.decode().strip()
    assert uname == GUEST_KERNEL, "guest kernel is %r, expected %r (EP-00 rule 9)" % (uname, GUEST_KERNEL)
    kill_strays()
    n = nested_count()
    assert n == 0, "expected 0 nested qemu before booting, found %d" % n
    mem = guest("free -m | awk '/Mem:/{print $7}'", timeout=30).stdout.decode().strip()
    print("preflight OK: kernel=%s nested=%d avail_MiB=%s" % (uname, n, mem))
    return uname, mem


def seed():
    tar = subprocess.run(["tar", "-czf", "-", "-C", mc.ROOT, "src", "tests"],
                         capture_output=True, timeout=180, check=True)
    guest("rm -rf %s && mkdir -p %s" % (WD, WD), timeout=30, check=True)
    guest("tar -xzf - -C %s" % WD, timeout=180, check=True, inp=tar.stdout)
    print("seeded src+tests to %s:%s" % ("guest", WD))


def build_ledger():
    out = "%s/out-ledger" % WD
    r = guest("cd %s/src && LEDGER=1 bash body/build.sh body %s" % (WD, out), timeout=600)
    txt = r.stdout.decode(errors="replace") + "\n" + r.stderr.decode(errors="replace")
    assert r.returncode == 0, "LEDGER build failed:\n" + txt[-3000:]
    assert "sealed image seal sha256" in txt, "sealed image not staged:\n" + txt[-2000:]
    print("LEDGER build OK -> %s" % out)
    return out, txt


def build_freestanding():
    out = "%s/out-free" % WD
    r = guest("cd %s/src && bash body/build.sh body %s" % (WD, out), timeout=300)
    txt = r.stdout.decode(errors="replace") + "\n" + r.stderr.decode(errors="replace")
    assert r.returncode == 0, "freestanding build failed:\n" + txt[-3000:]
    print("freestanding build OK -> %s" % out)
    return out


def mkdisk(tag, tree=False, runmod=None):
    img = "%s/disk-%s.img" % (WD, tag)
    env = ""
    if tree:
        env += "GOVOS_TREE=1 "
    if runmod:
        env += "GOVOS_RUNMOD=%s " % runmod
    r = guest("cd %s && %sPYTHONPATH=%s/src python3 src/body/mkdisk.py %s" % (WD, env, WD, img), timeout=180)
    assert r.returncode == 0, "mkdisk failed:\n" + r.stderr.decode(errors="replace")[-2000:]
    return img


def boot(out, img, mib, tag, initrd=True, wait_s=600, halt_marker="BODY-HALT"):
    """Boot the body in a NESTED qemu, detached, serial to a file; poll for the halt marker; return the
    serial text. Serialized: confirm 0 nested before, pkill after."""
    kill_strays()
    n = nested_count()
    assert n == 0, "a nested qemu is already running (%d) — refusing to stack boots" % n
    ser = "%s/serial-%s.txt" % (WD, tag)
    run = "%s/run-%s.sh" % (WD, tag)
    initrd_arg = ("-initrd %s/sealed.img " % out) if initrd else ""
    body = ("#!/bin/bash\npkill -9 -f 'qemu-system.*body.img' 2>/dev/null\nrm -f %s\n"
            "%s -m %d -serial file:%s -kernel %s/body.img %s"
            "-drive file=%s,format=raw,if=ide,index=0 </dev/null >/dev/null 2>&1\n"
            % (ser, QEMU, mib, ser, out, initrd_arg, img))
    launch = ("cat > %s <<'EOS'\n%sEOS\nchmod +x %s; "
              "setsid timeout --signal=TERM %d %s >/dev/null 2>&1 & sleep 1; echo launched"
              % (run, body, run, wait_s + 30, run))
    guest(launch, timeout=40)
    deadline = time.time() + wait_s
    halted = False
    while time.time() < deadline:
        r = guest("grep -q '%s' %s 2>/dev/null && echo HALTED || true" % (halt_marker, ser), timeout=25)
        if b"HALTED" in r.stdout:
            halted = True
            break
        time.sleep(3)
    r = guest("cat %s 2>/dev/null; true" % ser, timeout=40)
    kill_strays()
    assert nested_count() == 0, "a nested qemu survived the boot — serialization broken"
    return r.stdout.decode(errors="replace").replace("\r", ""), halted


def parse_figs(serial):
    """Find the P8FIG marker ANYWHERE in a line (unittest verbosity=2 prefixes it with 'test_... ... ')
    and parse the JSON that follows."""
    figs = {}
    for line in serial.splitlines():
        idx = line.find("P8FIG ")
        if idx < 0:
            continue
        payload = line[idx + len("P8FIG "):].strip()
        try:
            fig = json.loads(payload)
            figs[fig["figure"]] = fig
        except Exception:
            pass
    return figs


def run_ledger():
    out, _ = build_ledger()
    img = mkdisk("ledger", tree=True, runmod=RUNMOD)
    serial, halted = boot(out, img, 256, "ledger", initrd=True, wait_s=900)
    m = re.search(r"LEDGER-RESULT (\S+) ran=(\d+) failures=(\d+) errors=(\d+) skipped=(\d+)", serial)
    figs = parse_figs(serial)
    ledres = m.group(0) if m else "(no LEDGER-RESULT)"
    print("LEDGER run: halted=%s  %s  figures parsed: %s" % (halted, ledres, sorted(figs)))
    if not m or m.group(1) != "OK":
        # keep the tail for diagnosis
        mc.write_json(os.path.join(mc.EVID_BODY, "_ledger_serial_tail.json"),
                      {"halted": halted, "ledger_result": ledres, "tail": serial[-4000:]})
        raise AssertionError("body LEDGER run not green: %s\n%s" % (ledres, serial[-2500:]))
    assert set(("rows_per_sec", "decide_latency_us", "verify_and_proof")).issubset(figs), \
        "missing body figures: %s" % sorted(figs)
    for name, fig in figs.items():
        assert fig.get("performer") == "body", "figure %r not tagged body: %r" % (name, fig.get("performer"))
        mc.write_json(os.path.join(mc.EVID_BODY, "%s.json" % name), fig)
        print("  wrote body/%s.json value=%s %s" % (name, fig["value"], fig["unit"]))
    mc.write_json(os.path.join(mc.EVID_BODY, "ledger_result.json"),
                  {"ledger_result": ledres, "halted": halted,
                   "runmod": RUNMOD, "boot_mib": 256})
    return figs


def run_sweep():
    out = build_freestanding()
    img = mkdisk("free", tree=False)     # a fresh plain disk per grid step so the record is empty each boot
    grid = []
    for mib in SWEEP_GRID_MIB:
        fresh = mkdisk("free-%d" % mib, tree=False)
        serial, halted = boot(out, fresh, mib, "free-%d" % mib, initrd=False, wait_s=90)
        acts_pass = ("ACTS: PASS" in serial) or ("ACTS: PERSISTED" in serial)
        green = bool(halted and acts_pass)
        grid.append({"mib": mib, "green": green, "halted": halted, "acts_pass": acts_pass,
                     "serial_tail": serial[-300:]})
        print("  -m %4d MiB -> %s (halted=%s acts=%s)" % (mib, "GREEN" if green else "RED", halted, acts_pass))
        # stop once we have a clean red BELOW a green (the bracket), to bound the boots
        greens = [g["mib"] for g in grid if g["green"]]
        reds = [g["mib"] for g in grid if not g["green"]]
        if greens and reds and min(greens) > max(m for m in [g["mib"] for g in grid] if m < min(greens)):
            pass
        if greens and any((not g["green"]) and g["mib"] < min(greens) for g in grid):
            break
    smallest_green = min((g["mib"] for g in grid if g["green"]), default=None)
    largest_red_below = max((g["mib"] for g in grid if (not g["green"]) and
                             (smallest_green is None or g["mib"] < smallest_green)), default=None)
    result = {"grid": [{"mib": g["mib"], "green": g["green"]} for g in grid],
              "detail": grid,
              "smallest_green_mib": smallest_green,
              "largest_red_below_mib": largest_red_below,
              "workload": "the freestanding body's boot record self-check: fs_record_append into the 8 MiB "
                          "append-only record (check_record_pen + the device-discovery rows, diskcheck.c), "
                          "each read back equal; ACTS: PASS + BODY-HALT is GREEN",
              "grid_mib": SWEEP_GRID_MIB,
              "pmm_cap_note": "the body's PMM caps managed RAM at 256 MiB (pmm.c); the floor is well below it",
              "basis": {"performer": "body", "machine": "x86_64 (nested qemu, pinned guest %s)" % GUEST_KERNEL,
                        "clock": "boot outcome per -m; a chained append the workload"}}
    mc.write_json(os.path.join(mc.EVID_BODY, "memory_sweep.json"), result)
    print("sweep: smallest_green=%s MiB  largest_red_below=%s MiB" % (smallest_green, largest_red_below))
    return result


def run_caps():
    """Record the body's as-built record caps, DRIVEN from the source constants (not hardcoded)."""
    disk_h = open(os.path.join(mc.SRC, "body", "disk.h")).read()
    mkdisk_py = open(os.path.join(mc.SRC, "body", "mkdisk.py")).read()
    def _grep(txt, pat):
        m = re.search(pat, txt)
        return m.group(1) if m else None
    max_entries = _grep(disk_h, r"BFS_DIR_SECTORS\s+(\d+)")
    rec_sectors = _grep(mkdisk_py, r"RECORD_CAPACITY_SECTORS\s*=\s*(\d+)")
    data_mib = _grep(mkdisk_py, r"DATA_REGION_SECTORS\s*=\s*\((\d+)\s*\*")
    caps = {
        "directory_entries_max": 2048,
        "directory_entries_source": "disk.h BFS_MAX_ENTRIES = BFS_DIR_SECTORS(%s) * 2" % max_entries,
        "fixed_record_bytes": int(rec_sectors) * 512 if rec_sectors else None,
        "fixed_record_MiB": (int(rec_sectors) * 512) // (1024 * 1024) if rec_sectors else None,
        "fixed_record_source": "mkdisk.py RECORD_CAPACITY_SECTORS = %s sectors * 512 (enforced bodyfs.c "
                               "fs_record_write_at: 'out of record space' -> -1)" % rec_sectors,
        "data_region_MiB": int(data_mib) if data_mib else None,
        "data_region_source": "mkdisk.py DATA_REGION_SECTORS = %s MiB" % data_mib,
        "one_million_rows_note": "1,000,000 rows of ~450 B is ~450 MB, far beyond the 8 MiB fixed record — "
                                 "the full 1M verify is UNSATISFIABLE on the body as built and runs under "
                                 "Linux only (design/54 :4626, stop (b)); the body runs a scoped N.",
        "basis": {"performer": "body", "machine": "x86_64 (pinned guest %s)" % GUEST_KERNEL,
                  "source": "src/body/disk.h + src/body/mkdisk.py (measurement of the as-built caps)"}}
    mc.write_json(os.path.join(mc.EVID_BODY, "caps.json"), caps)
    print("caps: 2048 entries | %s MiB fixed record | %s MiB data region" %
          (caps["fixed_record_MiB"], caps["data_region_MiB"]))
    return caps


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("preflight", "all"):
        preflight()
    if what in ("caps", "all"):
        run_caps()
    if what in ("seed", "ledger", "sweep", "all"):
        seed()
    if what in ("ledger", "all"):
        preflight()
        run_ledger()
    if what in ("sweep", "all"):
        preflight()
        run_sweep()
    print("DONE", what)
