# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary.
# The body reclaims a finished thread's SLOT at the first safe point after it switches away (built, correct),
# proven by an ordinary gcc -static -pthread glibc program that creates + joins many threads a FEW AT A TIME:
# cumulative creations exceed the slot table (so it must be reused) while only a handful of 8 MiB stacks are
# ever live (so memory never binds). With the reclaim ON the program runs; with it OFF the slot table
# exhausts by the SLOT mechanism, distinct from any memory failure (L19). A slot is never reclaimed while a
# thread is live, so a live-slot reuse corrupts a join (the correctness surface). NON-GOAL: no offensive
# capability — this DRIVES C7-MAINT-5B-THREAD-SLOT-RECLAIM; every boot is the guest's nested qemu; it touches
# no host kernel (L11 / EP-00 rule 9 / charter §A21). Validate by building/reading, never by attack.
"""C7-MAINT-5B-THREAD-SLOT-RECLAIM acceptance (design/54 §5 L19; archi's reclaim ruling; mgr's memory-vs-slots STOP).

The reclaim is BUILT (sched_alloc reuses a safely finished T_ZOMBIE slot that is not g_cur, whose exit already
cleared + woke its waiter; SCHED_MAX_THREADS 32). This unit PROVES it load-bearing and safe:

  A1  a real program (a static gcc -pthread prover) creates + joins many threads a few at a time — cumulative
      43 > SCHED_MAX_THREADS-1 (31) but peak_live only 4 — and runs GREEN on the body (SLOTPROVER-DONE). The
      three lighter concurrency ledger modules (ep28g_w1/ep28g_w2/ep28c_w4e_3b) run green on the body. PLANT
      (distinct from memory, can-fail): reclaim disabled (PLANT_NO_RECLAIM) -> the churn exhausts the 32-slot
      table at EXACTLY created=31 with EAGAIN, only a handful of stacks live, the blocked workers UNTOUCHED
      -> no SLOTPROVER-DONE. Distinct from memory: the same peak_live=4 clean run creates 43 (>31), so memory
      is not the limit at that peak; and the pool was 252 MiB free at init versus ~32 MiB of live stacks.
  A2  the join is never corrupted: a slot is never reclaimed while live nor before its waiter is cleared.
      PLANT (can-fail): PLANT_RECLAIM_UNSAFE reuses a still-LIVE (blocked) worker's slot -> that worker's
      join HANGS -> no SLOTPROVER-KEEP-INTACT, no SLOTPROVER-DONE.
  A3  the concurrency-floor regression (test_c7_p3b_4f_ii_concurrency_floor) runs 17/17 unchanged.
  A4  SCHED_MAX_THREADS bounds PEAK (32), sized from the measured whole-ledger heaviest peak (ep28c_w1's
      submit_many(16) = 16 + main = 17) plus headroom, inside the 4 MiB layout ceiling; ACT_KINDS 12; ATTESTED
      88; no founding; the prover source is a fixture under tests/, never a signed member.

The prover build + boot tests are guest-gated (the pinned 6.8.0-134-generic guest + nested qemu over SSH) and
serialized — ONE nested boot at a time; the count/fixture tests run in main.
"""

import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
SRC = os.path.join(ROOT, "src")
BODY = os.path.join(SRC, "body")
sys.path.insert(0, SRC)

# the discriminating prover fixture (ordinary gcc -static -pthread glibc C), staged into the body.
PROVER_FIXTURE = os.path.join(HERE, "c7_maint_5b_slot_reclaim_prover.c")

# what the prover reports (measured on the body).
CLEAN_CREATED = 43          # KEEP(3) + ROUNDS(40); > SCHED_MAX_THREADS-1 (31)
CLEAN_PEAK = 4              # KEEP(3) + 1 churn live at a time
EXHAUST_CREATED = 31       # SCHED_MAX_THREADS(32) - 1 non-main slot: the reclaim-off table edge

# ── the nested-guest bridge (isolated per-unit scratch; every boot the guest's nested qemu) ───────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/slotreclaim-accept"
_QEMU = "qemu-system-x86_64 -cpu max -display none -no-reboot -m 256 -rtc base=utc"
_PORT = 3456 + (os.getpid() % 900)


def _guest_reachable():
    """True only if the PINNED guest (6.8.0-134-generic) answers over SSH AND nested qemu is present."""
    try:
        r = subprocess.run(_SSH + ["uname -r; command -v qemu-system-x86_64 >/dev/null && echo QEMU"],
                           capture_output=True, timeout=20)
    except Exception:
        return False
    out = r.stdout.decode(errors="replace")
    return r.returncode == 0 and "6.8.0-134-generic" in out and "QEMU" in out


GUEST = _guest_reachable()
_SEEDED = {"done": False}
_PROVER_SERIAL = {}


def _seed_prover_guest():
    """Copy src/body + src/bridge + src/founding AND the prover fixture to the guest ONCE."""
    if _SEEDED["done"]:
        return
    tar = subprocess.run(["tar", "-czf", "-", "-C", SRC, "body", "bridge", "founding"],
                         capture_output=True, timeout=120)
    subprocess.run(_SSH + ["rm -rf %s && mkdir -p %s && tar -xzf - -C %s" % (_WD, _WD, _WD)],
                   input=tar.stdout, capture_output=True, timeout=120, check=True)
    with open(PROVER_FIXTURE, "rb") as f:
        src = f.read()
    subprocess.run(_SSH + ["cat > %s/prover.c" % _WD], input=src, capture_output=True, timeout=60, check=True)
    _SEEDED["done"] = True


def _prover_serial(fault="", wait_s=110):
    """Build the body WITH the prover (PROVER_SRC + PROVER_PTHREAD + CONCURRENCY [+ fault]); boot it in a
    NESTED qemu DETACHED with serial to a file; poll for BODY-HALT (a corrupting plant HANGS and the poll
    times out); pkill; return serial text. Cached per fault. Serialized — one nested qemu at a time."""
    key = fault or "clean"
    if key in _PROVER_SERIAL:
        return _PROVER_SERIAL[key]
    _seed_prover_guest()
    out = "%s/out-%s" % (_WD, key)
    img = "%s/disk-%s.img" % (_WD, key)
    ser = "%s/serial-%s.txt" % (_WD, key)
    port = _PORT + (len(_PROVER_SERIAL) % 400)
    # NB: NO `set -e` — the poll loop's `grep && break` returns nonzero until BODY-HALT appears, which would
    # abort the script on the first iteration under `set -e`. Build failure is checked explicitly (body.img).
    script = (
        "cd %s || exit 1\n"
        "if [ ! -f %s/body.img ]; then "
        "  PROVER_SRC=%s/prover.c PROVER_PTHREAD=1 CONCURRENCY=1 bash body/build.sh body %s %s "
        "    > %s/build-%s.log 2>&1; fi\n"
        "[ -f %s/body.img ] || { echo BUILD-NO-BODY-IMG; tail -6 %s/build-%s.log 2>/dev/null; exit 1; }\n"
        "PYTHONPATH=%s python3 body/mkdisk.py %s > %s/mkdisk-%s.log 2>&1 || { echo MKDISK-FAIL; cat %s/mkdisk-%s.log; exit 1; }\n"
        "rm -f %s; pkill -9 -f '[b]ody.img' 2>/dev/null; sleep 1\n"
        "setsid timeout --signal=TERM %d %s -serial file:%s -gdb tcp::%d -kernel %s/body.img "
        "  -drive file=%s,format=raw,if=ide,index=0 </dev/null >/dev/null 2>&1 &\n"
        "for i in $(seq 1 %d); do if grep -qa BODY-HALT %s 2>/dev/null; then break; fi; sleep 1; done\n"
        "sleep 1; pkill -9 -f '[b]ody.img' 2>/dev/null; sleep 1\n"
        "cat %s 2>/dev/null\n"
        % (_WD, out, _WD, out, fault, _WD, key, out, _WD, key,
           _WD, img, _WD, key, _WD, key, ser, wait_s + 30, _QEMU, ser, port, out, img,
           wait_s, ser, ser)
    )
    r = subprocess.run(_SSH + ["bash -s"], input=script.encode(), capture_output=True, timeout=wait_s + 120)
    txt = r.stdout.decode(errors="replace").replace("\r", "")
    _PROVER_SERIAL[key] = txt
    return txt


def tearDownModule():
    """Leave the guest as found: no nested-qemu boot survives this module (serialized guest)."""
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f '[b]ody.img' 2>/dev/null; true"],
                       capture_output=True, timeout=20)


# ── A1 — the reclaim proven against a slot-bound prover (green) ───────────────────────────────────
@unittest.skipUnless(GUEST, "A1 needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestA1ReclaimGreenOnASlotBoundProver(unittest.TestCase):
    def test_the_prover_runs_green_reusing_slots_at_low_peak(self):
        serial = _prover_serial()
        self.assertIn("MULTIBOOT: OK", serial)
        self.assertIn("FLOOR-LOAD: OK (digest matches the seal)", serial, "the sealed prover digest-checked")
        self.assertIn("SLOTPROVER-START", serial, "the prover reached main")
        self.assertIn("SLOTPROVER-KEEP: OK 3 blocked (live)", serial, "a handful of workers stay live")
        self.assertIn("SLOTPROVER-CHURN: OK created=%d peak_live=%d" % (CLEAN_CREATED, CLEAN_PEAK), serial,
                      "cumulative %d > SCHED_MAX_THREADS-1 at peak %d — slots were reused" % (CLEAN_CREATED, CLEAN_PEAK))
        self.assertIn("SLOTPROVER-KEEP-COUNT: OK 3", serial, "the live workers joined cleanly (reclaim never touched them)")
        self.assertIn("SLOTPROVER-DONE created=%d peak_live=%d rc=0" % (CLEAN_CREATED, CLEAN_PEAK), serial,
                      "the ordinary threaded program ran to completion")
        self.assertIn("FLOOR2: PASS", serial, "the concurrency floor still passes as a group")

    def test_the_scheduler_created_more_threads_than_the_slot_table_holds(self):
        serial = _prover_serial()
        m = re.search(r"FLOOR2-THREADS: 0x([0-9a-f]+)", serial)
        self.assertIsNotNone(m, "the thread-created counter is on serial")
        self.assertEqual(int(m.group(1), 16), CLEAN_CREATED, "43 real thread contexts were created (0x2b)")
        me = re.search(r"FLOOR2-EXITS: 0x([0-9a-f]+)", serial)
        self.assertEqual(int(me.group(1), 16), CLEAN_CREATED, "43 threads ended via SYS_exit")
        # the slot table is 32; more than 32 were created -> the table MUST have been reused (reclaim).
        self.assertGreater(CLEAN_CREATED, 31, "cumulative creations exceed the 31 non-main slots")

    def test_memory_had_abundant_headroom_the_bound_was_slots_not_memory(self):
        serial = _prover_serial()
        m = re.search(r"PMM: init, free frames=0x([0-9a-f]+)", serial)
        self.assertIsNotNone(m, "the pool free-frame count is on serial")
        free_mib = int(m.group(1), 16) * 4096 // (1024 * 1024)
        # peak_live 4 stacks * 8 MiB = 32 MiB; the pool holds ~250 MiB — memory never approached its bound.
        self.assertGreater(free_mib, 8 * CLEAN_PEAK * 4, "the pool dwarfs the live stacks (bound is slots, not memory)")


# ── A1 PLANT — reclaim disabled: the slot table exhausts, distinct from memory ────────────────────
@unittest.skipUnless(GUEST, "the A1 plant needs the pinned guest + nested qemu over SSH -p 2222")
class TestA1PlantSlotTableExhaustsDistinctFromMemory(unittest.TestCase):
    def test_reclaim_off_exhausts_the_slot_table_at_its_exact_edge(self):
        clean = _prover_serial()
        self.assertIn("SLOTPROVER-DONE", clean, "clean: the prover completes (slots reused)")
        plant = _prover_serial("PLANT_NO_RECLAIM")
        # the create fails at EXACTLY created=31 (SCHED_MAX_THREADS-1 non-main slots) with EAGAIN — the
        # slot-table signature, not a memory failure at some arbitrary point.
        self.assertIn("SLOTPROVER-SLOT-EXHAUST rc=11 (EAGAIN: the slot table refused a slot) created=%d" % EXHAUST_CREATED,
                      plant, "reclaim-off: the 32-slot table exhausts at its exact edge with EAGAIN")
        self.assertNotIn("SLOTPROVER-DONE", plant, "the program never completes without reclaim")

    def test_the_failure_is_slots_not_memory_the_live_workers_are_untouched(self):
        plant = _prover_serial("PLANT_NO_RECLAIM")
        # only a handful of stacks were ever live and the blocked workers join cleanly: a slot-COUNT
        # exhaustion, not a memory exhaustion and not corruption.
        self.assertIn("peak_live=%d" % CLEAN_PEAK, plant, "only a handful of stacks were live at the failure")
        self.assertIn("SLOTPROVER-KEEP-INTACT: OK 3", plant, "the live workers were never disturbed (not corruption)")
        m = re.search(r"PMM: init, free frames=0x([0-9a-f]+)", plant)
        free_mib = int(m.group(1), 16) * 4096 // (1024 * 1024)
        self.assertGreater(free_mib, 8 * CLEAN_PEAK * 4, "the pool had abundant headroom — the bound was slots")

    def test_reclaim_on_creates_more_at_the_same_peak_so_memory_is_not_the_limit(self):
        clean = _prover_serial()
        plant = _prover_serial("PLANT_NO_RECLAIM")
        # THE DIFFERENTIAL: at the SAME peak_live, reclaim-ON creates 43 (>31) and completes while reclaim-OFF
        # stops at 31. The only thing that changed is slot reuse -> the bound is the slot table, distinct from
        # memory (which would have bound both runs identically at the same peak).
        self.assertIn("SLOTPROVER-CHURN: OK created=%d peak_live=%d" % (CLEAN_CREATED, CLEAN_PEAK), clean)
        self.assertIn("SLOTPROVER-SLOT-EXHAUST", plant)
        self.assertIn("created=%d" % EXHAUST_CREATED, plant)


# ── A2 PLANT — a live-slot reuse corrupts a join (the correctness surface) ────────────────────────
@unittest.skipUnless(GUEST, "the A2 plant needs the pinned guest + nested qemu over SSH -p 2222")
class TestA2ReclaimNeverCorruptsAJoin(unittest.TestCase):
    def test_an_unsafe_live_slot_reuse_hangs_the_join(self):
        clean = _prover_serial()
        self.assertIn("SLOTPROVER-KEEP-COUNT: OK 3", clean, "clean: the workers join cleanly")
        # PLANT_RECLAIM_UNSAFE reuses a still-LIVE (blocked) worker's slot when the table is full; that
        # worker's kernel context is reused under it, so joining it HANGS. The plant CAN fail (L19).
        plant = _prover_serial("PLANT_RECLAIM_UNSAFE", wait_s=45)
        self.assertIn("SLOTPROVER-SLOT-EXHAUST", plant, "the table still fills (no safe reclaim)")
        self.assertNotIn("SLOTPROVER-KEEP-INTACT: OK", plant, "a stolen live worker -> its join never returns")
        self.assertNotIn("SLOTPROVER-KEEP-COUNT: OK", plant, "the workers do not all join")
        self.assertNotIn("SLOTPROVER-DONE", plant, "the program never completes when a live slot is reused")


# ── A4 — counts and the prover's status (host-side, no boot) ──────────────────────────────────────
class TestA4CountsAndProverFixture(unittest.TestCase):
    def test_sched_max_threads_bounds_the_measured_whole_ledger_peak(self):
        with open(os.path.join(BODY, "enclosure.h"), encoding="utf-8") as f:
            h = f.read()
        m = re.search(r"#define\s+SCHED_MAX_THREADS\s+(\d+)u", h)
        self.assertIsNotNone(m, "SCHED_MAX_THREADS is defined")
        smax = int(m.group(1))
        self.assertEqual(smax, 32, "SCHED_MAX_THREADS is 32 (the built value)")
        # the measured whole-ledger heaviest PEAK is ep28c_w1's submit_many(16) = 16 workers + main = 17.
        WHOLE_LEDGER_PEAK = 17
        self.assertGreater(smax, WHOLE_LEDGER_PEAK, "32 bounds the measured peak (17) with headroom")

    def test_no_founding_act_kinds_twelve_attested_eighty_eight(self):
        import hashlib
        import json
        from kernel.boot import ACT_KIND_RECORD_KIND
        from kernel.attestation import ATTESTED_MEMBERS

        self.assertEqual(len(ATTESTED_MEMBERS), 88, "edit-in-place — ATTESTED stays 88 (this unit adds no src member)")
        pack_path = os.path.join(SRC, "founding", "founding-pack.json")
        with open(pack_path, "rb") as f:
            raw = f.read()
        pack = json.loads(raw.decode("utf-8"))
        self.assertEqual(pack["founding_version"], "1.55.0", "no founding — the version is unchanged")
        rows = []

        def scan(node):
            if isinstance(node, dict):
                if node.get("kind") == ACT_KIND_RECORD_KIND:
                    rows.append(node)
                for v in node.values():
                    scan(v)
            elif isinstance(node, list):
                for v in node:
                    scan(v)

        scan(pack)
        self.assertEqual(len({r["seam_kind"] for r in rows}), 12, "ACT_KINDS stays twelve — this unit adds no act")

    def test_the_prover_source_is_a_fixture_under_tests_not_a_member(self):
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertTrue(os.path.exists(PROVER_FIXTURE), "the prover source is a fixture under tests/")
        self.assertFalse(os.path.exists(os.path.join(BODY, "c7_maint_5b_slot_reclaim_prover.c")),
                         "the prover source is NOT under src/body (where the walk-guard would make it a member)")
        self.assertFalse(any(m.endswith((".elf", ".o", ".img")) for m in ATTESTED_MEMBERS),
                         "§9 mechanism 3: the built prover/body images are never signed members")

    def test_the_reclaim_reuses_only_a_safely_finished_slot_that_is_not_current(self):
        # the correctness surface, read (not attacked): the reclaim branch reuses a T_ZOMBIE slot that is not
        # g_cur; T_ZOMBIE is set only in sched_thread_exit, AFTER the child-id clear + futex wake.
        with open(os.path.join(BODY, "enclosure.c"), encoding="utf-8") as f:
            c = f.read()
        self.assertIn("g_threads[i].state == T_ZOMBIE && &g_threads[i] != g_cur", c,
                      "sched_alloc reclaims only a finished (T_ZOMBIE) slot that is not the current thread")
        self.assertIn("PLANT_NO_RECLAIM", c, "the reclaim-off plant exists (A1 can fail)")
        self.assertIn("PLANT_RECLAIM_UNSAFE", c, "the live-slot-reuse plant exists (A2 can fail)")


if __name__ == "__main__":
    unittest.main()
