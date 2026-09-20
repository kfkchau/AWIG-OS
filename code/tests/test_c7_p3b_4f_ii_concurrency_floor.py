# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test · OS-architecture vocabulary
# (a freestanding body completing the CONCURRENCY floor on the metal — real thread contexts (clone3), a
# preemptive scheduler on the body's timer switching each thread's own %fs base and SSE state only outside
# an act, a real futex wait queue with timeouts and wake, a thread's own end (SYS_exit) clearing the child
# id so a join returns — proven by an ORDINARY statically-linked THREADED C program built by the guest's own
# gcc -static -pthread against the real C library + libpthread) as in the seL4/gVisor/Fuchsia and osdev
# literature. NON-GOAL: no offensive capability — this DRIVES the acceptance of C7 P3b-4f-ii: our own
# kernel's body runs real threads that truly take turns and truly wait on one another, proven by running one
# (L19); it stands nothing as production, binds no key, touches no host kernel (every boot the guest's
# nested qemu).
"""C7 P3b-4f-ii acceptance — THE CONCURRENCY FLOOR (design/54 §5 L19; §7 row P3b-4f, mgr's size-split
4f-i/4f-ii board :4113/:4114; archi countersign :4116 + the re-mint :4140; the pre-flight FINDINGS Q-D/Q6).

On the static single-thread floor (P3b-4f-i), with P3b-4b's classification kept as the router, the body
becomes a real home for MANY threads: clone3 creates a real thread context with its own stack + TLS; a
PREEMPTIVE SCHEDULER on the P3b-3 timer switches between contexts, saving and restoring each thread's own
%fs base AND its SSE state (per-thread fxsave/fxrstor) only at a crossing's return or in ring-3 time, never
inside an act; a real FUTEX wait QUEUE blocks and wakes with real timeouts; a thread's own end (SYS_exit —
the fiftieth measured shape the census missed, Q15/:4134) clears + wakes the child id so a join returns. It
is PROVEN, per L19, by the FROZEN P3b-4f A1 full `gcc -static -pthread` glibc program VERBATIM — two threads
under a mutex reach the exact count, a timed wait times out, a join returns, malloc works — and each plant
makes THAT program fail (never a body-side flag).

  A1  the threaded glibc prover runs to completion (reaches main, two threads reach the exact count under a
      mutex, a timed wait times out, the joins return, malloc works, PROVER2-DONE rc=0); the enclosure and
      the forty-nine still pass; the twelve rows' digest still on serial (nested guest); FLOOR2: PASS
  A2  threads are real preempted contexts (clone3 + the timer), the switch saves/restores each thread's own
      %fs + SSE: a planted fake thread id makes the JOIN HANG (the workers never run); a planted no-SSE-save
      switch clobbers a thread's running FP accumulator so its result no longer matches (PROVER2-FP: FAIL)
  A3  the wait is a real queue with timeout + wake (futex): a planted no-queue futex makes the timed wait
      never time out (no PROVER2-TIMEDWAIT: OK, no completion)
  A4  a thread's own end is served (SYS_exit) and clears + wakes the child id (CHILD_CLEARTID) so a join
      returns: a planted no-clear makes the JOIN HANG
  A5  P3b-4b's classification kept as the router; NO new src/body file (edit-in-place, ATTESTED 87 / 30);
      the prover source is a fixture under tests/ not src/body; the prover/body IMAGE never a member; no
      switch inside an act (a planted mid-act switch reds the FLOOR2-SWITCH-IN-ACT check); guest-only;
      revertable; host-crossing census clean; no interpreter
  A6  no founding (ACT_KINDS twelve, pack sha 95631e8f byte-unchanged, founding 1.55.0); the ATTESTED
      count-pins stand at 87 / 30 (edit-in-place — no new src/body file)

A1..A4 and the A5 mid-act-switch build+boot in the NESTED guest (a bodyfs disk attached as P3b-2) and skip
when the pinned guest is not reachable over SSH; the rest run in main. Register: OS bring-up on a disposable
guest, described by function — a body that runs real threads and proves it with an ordinary threaded C
program; validated by building/reading, never by attack (governance-work-method). Every kernel touch is the
guest's nested qemu; the host kernel is never touched (L11 / EP-00 rule 9 / charter §A21).
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

ROWS_DIGEST = "sha256:b16ee8a33d50424c8e4ed10474a3f2fed49f6693aa7b1b0492256d9ef842cfdb"

# the prover fixture (ordinary gcc -static -pthread glibc C), built by the guest toolchain, staged into the body.
PROVER_FIXTURE = os.path.join(HERE, "c7_p3b_4f_ii_prover_threaded.c")

# ── the nested-guest bridge (isolated per-unit scratch; every boot the guest's nested qemu) ───────────
_KEY = "<HOME><KEYPATH>"
_SSH = ["<SSH-INVOCATION>", "-i", _KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "<GUEST>"]
_WD = "/tmp/p3b4fii-accept"
_QEMU = "qemu-system-x86_64 -cpu max -serial stdio -display none -no-reboot -m 256 -rtc base=utc"

_GDB_BASE = 2500 + (os.getpid() % 1400)
_boot_n = [0]


def _next_gdb_port():
    p = _GDB_BASE + (_boot_n[0] % 1400)
    _boot_n[0] += 1
    return p


def _guest_reachable():
    """True only if the PINNED guest (6.8.0-134-generic) answers over SSH AND the nested boot engine
    (qemu-system-x86_64) is present. Observes a state the check did not create (§A19)."""
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
    """Copy src/body + src/bridge + src/founding AND the threaded prover fixture to the guest ONCE."""
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


def _guest_build(fault="", tag=None):
    """Build the body WITH the staged THREADED prover (PROVER_SRC + PROVER_PTHREAD + CONCURRENCY) in the
    guest; return the outdir. The concurrency floor (floor2_run) is built, not the single-thread floor."""
    _seed_guest()
    tag = tag or (fault or "clean")
    out = "%s/out-%s" % (_WD, tag)
    b = subprocess.run(
        _SSH + ["cd %s && PROVER_SRC=%s/prover.c PROVER_PTHREAD=1 CONCURRENCY=1 bash body/build.sh body %s %s"
                % (_WD, _WD, out, fault)],
        capture_output=True, timeout=300)
    if b.returncode != 0:
        raise AssertionError("guest build failed: " + b.stderr.decode(errors="replace"))
    out_txt = b.stdout.decode(errors="replace")
    assert "prover image seal sha256" in out_txt, "the prover was not sealed/embedded: " + out_txt
    return out


def _guest_mkdisk(img):
    m = subprocess.run(_SSH + ["cd %s && PYTHONPATH=%s python3 body/mkdisk.py %s" % (_WD, _WD, img)],
                       capture_output=True, timeout=60)
    if m.returncode != 0:
        raise AssertionError("guest mkdisk failed: " + m.stderr.decode(errors="replace"))
    return img


def _guest_boot(outdir, img, timeout_s):
    """Boot the body in a NESTED qemu with `img` as a virtual IDE disk (gdb stub from the first line, L17);
    return serial text. Every boot is the guest's nested qemu — no host kernel. Boots are SERIALIZED."""
    boot = subprocess.run(
        _SSH + ["timeout --signal=TERM %d %s -gdb tcp::%d -kernel %s/body.img "
                "-drive file=%s,format=raw,if=ide,index=0 </dev/null 2>/dev/null; true"
                % (timeout_s, _QEMU, _next_gdb_port(), outdir, img)],
        capture_output=True, timeout=timeout_s + 40)
    return boot.stdout.decode(errors="replace").replace("\r", "")


def _serial(fault="", tag=None, timeout_s=150):
    """Build a fresh disk + build+boot once per (fault/tag), cached (each guest boot is serialized)."""
    key = tag or (fault or "clean")
    if key not in _SERIAL_CACHE:
        out = _guest_build(fault, tag=key)
        img = _guest_mkdisk("%s/disk-%s.img" % (_WD, key))
        _SERIAL_CACHE[key] = _guest_boot(out, img, timeout_s)
    return _SERIAL_CACHE[key]


def _body_source_names():
    return sorted(n for n in os.listdir(BODY)
                  if n != "__pycache__" and not n.endswith((".pyc", ".pyo")))


def tearDownModule():
    """Leave the guest as found: no nested-qemu boot survives this module (serialized guest)."""
    if GUEST:
        subprocess.run(_SSH + ["pkill -9 -f 'qemu-system.*body.img' 2>/dev/null; true"],
                       capture_output=True, timeout=20)


# ── A1 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A1 needs the pinned guest (6.8.0-134) + nested qemu over SSH -p 2222")
class TestA1ThreadedGlibcProverRunsToCompletion(unittest.TestCase):
    def test_an_ordinary_threaded_glibc_program_runs_to_completion_on_the_body(self):
        serial = _serial()
        self.assertIn("MULTIBOOT: OK", serial, "qemu is the multiboot bootloader; no Linux beneath")
        self.assertIn("LONGMODE: OK", serial, "the body is in the machine's long mode (P3b-4L)")
        self.assertIn("FLOOR-LOAD: OK (digest matches the seal)", serial, "the sealed threaded prover digest-checked")
        self.assertIn("PROVER2-START", serial, "the prover reached main")
        self.assertIn("PROVER2-CREATE: OK", serial, "both threads were created (clone3 real contexts)")
        self.assertIn("PROVER2-TIMEDWAIT: OK (timed out)", serial, "the timed wait really timed out (futex timeout)")
        self.assertIn("PROVER2-JOIN: OK", serial, "both joins returned (SYS_exit cleared + woke the child id)")
        self.assertIn("PROVER2-COUNT: OK 4000", serial, "two threads reached the EXACT count under the mutex")
        self.assertIn("PROVER2-FP: OK", serial, "each thread's own SSE accumulator survived every turn")
        self.assertIn("PROVER2-MALLOC: OK", serial, "malloc over the growing break works with threads up")
        self.assertIn("PROVER2-DONE rc=0", serial, "the ordinary threaded glibc program ran to completion")
        self.assertIn("FLOOR2: PASS", serial, "the concurrency-floor self-check passes as a group")
        self.assertIn("FLOOR2-ACTS: PASS", serial)

    def test_the_scheduler_did_real_concurrency_work(self):
        serial = _serial()
        self.assertIn("FLOOR2-THREADS: 0x00000002", serial, "two real thread contexts were created (clone3)")
        self.assertIn("FLOOR2-EXITS: 0x00000002", serial, "both threads ended via SYS_exit")
        self.assertIn("FLOOR2-SWITCH-IN-ACT: 0x00000000", serial, "the scheduler NEVER switched inside an act (:4107 a)")
        m = re.search(r"FLOOR2-PREEMPTS: 0x([0-9a-f]+)", serial)
        self.assertIsNotNone(m, "the preempt counter is on serial")
        self.assertGreater(int(m.group(1), 16), 0, "the timer preempted a running context at least once")

    def test_the_enclosure_and_forty_nine_router_still_pass_unchanged(self):
        serial = _serial()
        self.assertIn("ENCLOSURE: PASS", serial, "the enclosure MECHANISM still passes (P3b-4a, unchanged)")
        self.assertIn("SERVE: PASS", serial, "the forty-nine classification kept as the router (P3b-4b, A5)")
        self.assertIn("SERVE-ACTS: PASS", serial)
        self.assertIn("ROWS-DIGEST: " + ROWS_DIGEST, serial, "the twelve rows' digest, still on serial")
        self.assertIn("ROWS-COUNT: 0000000c", serial, "twelve rows (0x0c)")


# ── A2 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A2 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA2ThreadsRealContextsPerThreadFsAndSse(unittest.TestCase):
    def test_a_fake_thread_id_makes_the_join_hang(self):
        clean = _serial()
        self.assertIn("PROVER2-JOIN: OK", clean, "clean: the joins return")
        # a fake tid creates NO running context: the workers never run and pthread_join never returns.
        plant = _serial("PLANT_FAKE_TID", timeout_s=45)
        self.assertIn("PROVER2-CREATE: OK", plant, "clone3 returned a (fake) tid to the parent")
        self.assertNotIn("PROVER2-JOIN: OK", plant, "a fake tid → pthread_join HANGS (no real context to join)")
        self.assertNotIn("PROVER2-DONE", plant, "the program never completes with a fake thread id")

    def test_no_per_thread_sse_save_clobbers_a_threads_fp_accumulator(self):
        clean = _serial()
        self.assertIn("PROVER2-FP: OK", clean, "clean: each thread's SSE accumulator survives every turn")
        # the switch does not save/restore per-thread SSE: a thread's running xmm accumulator is clobbered
        # by the other thread's work across a turn, so its result no longer matches the reference.
        plant = _serial("PLANT_NO_SSE_SWITCH")
        self.assertIn("PROVER2-FP: FAIL", plant, "no per-thread SSE save → a thread's FP accumulator is clobbered")
        self.assertNotIn("PROVER2-DONE", plant, "the program does not complete once its FP result is wrong")


# ── A3 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A3 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA3RealFutexQueueWithTimeout(unittest.TestCase):
    def test_a_no_queue_futex_makes_the_timed_wait_never_time_out(self):
        clean = _serial()
        self.assertIn("PROVER2-TIMEDWAIT: OK (timed out)", clean, "clean: the timed wait blocks and times out")
        # a futex that returns at once (no queue / no timeout) makes sem_timedwait never reach its deadline:
        # glibc re-loops forever and the timed wait never completes (no OK, no DONE).
        plant = _serial("PLANT_FUTEX_NO_QUEUE", timeout_s=45)
        self.assertIn("PROVER2-CREATE: OK", plant, "the threads were created")
        self.assertNotIn("PROVER2-TIMEDWAIT: OK", plant, "a no-queue futex → the timed wait never times out")
        self.assertNotIn("PROVER2-DONE", plant, "the program never completes")


# ── A4 ───────────────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: A4 needs the pinned guest + nested qemu over SSH -p 2222")
class TestA4ThreadExitClearsChildId(unittest.TestCase):
    def test_not_clearing_the_child_id_on_exit_makes_the_join_hang(self):
        clean = _serial()
        self.assertIn("PROVER2-JOIN: OK", clean, "clean: a thread's end clears + wakes the child id; the join returns")
        # the child id is neither cleared nor woken on SYS_exit: pthread_join futex-waits on it forever.
        plant = _serial("PLANT_NO_CHILD_CLEAR", timeout_s=150)
        self.assertIn("PROVER2-CREATE: OK", plant, "the threads ran")
        self.assertIn("PROVER2-TIMEDWAIT: OK (timed out)", plant, "the timed wait still works")
        self.assertNotIn("PROVER2-JOIN: OK", plant, "no CHILD_CLEARTID → pthread_join HANGS")
        self.assertNotIn("PROVER2-DONE", plant, "the program never completes")


# ── A5 ───────────────────────────────────────────────────────────────────────────────────────────
def _host_kernel_load_tokens(text):
    return [tok for tok in ("insmod", "modprobe") if tok in text]


# ── C7 MAINT-BODY-SCANS: the "no borrowed interpreter in the body" property, at its real home ──────────
# The scan below once read the body's SOURCE TEXT for the words "cpython"/"libpython"; P3b-4c/4g added
# LEGITIMATE comments naming the real borrowed interpreter (design/54 L19) to serve.c/enclosure.c, so a
# word scan reddened on a comment while property I3 (no borrowed code INSIDE the signed base) held intact.
# The property lives in TWO places — the body.elf link (build.sh, where "linked into body.elf" is decided)
# and the attested member list — and is checked there, never in prose.
def _body_elf_link_command(build_text):
    """The single gcc invocation that links body.elf, with backslash-continuations joined."""
    joined = re.sub(r"\\\n[ \t]*", " ", build_text)
    for line in joined.splitlines():
        if line.lstrip().startswith("gcc") and '-o "$OUT/body.elf"' in line:
            return line
    return None


def _link_inputs(link_command):
    """The object files and library-link flags actually linked into body.elf."""
    objs = re.findall(r'"\$OUT/([A-Za-z0-9_.+-]+\.o)"', link_command)
    libs = re.findall(r"(?:^|\s)(-l[:\w.+-]+)", link_command)
    return objs, libs


def _borrowed_interpreter_link_inputs(objs, libs):
    """Any link input that is a borrowed interpreter / C-library object or a flag pulling one."""
    bad = [o for o in objs if any(t in o.lower() for t in ("cpython", "libpython", "python"))]
    bad += [l for l in libs if l.startswith("-lpython") or l in ("-lc", "-lpython3")]
    return bad


def _interpreter_members(members):
    """Any attested member whose path is a borrowed interpreter file (never a signed member, §9 mech 3)."""
    return [m for m in members
            if any(t in m.lower() for t in ("cpython", "libpython", "ld-linux", "libc.so"))]


class TestA5RouterKeptEditInPlaceProverNotAMember(unittest.TestCase):
    def test_no_new_src_body_file_attested_stays_87_and_30(self):
        from kernel.attestation import ATTESTED_MEMBERS, law_guard_surface, twin_uncovered
        on_disk = sorted("body/" + f for f in _body_source_names())
        self.assertEqual(len(on_disk), 31, "31 src/body files (this slice adds none; C7 P3b-6a added net.c)")
        for rel in on_disk:
            self.assertIn(rel, ATTESTED_MEMBERS, "%s under src/body is not attested" % rel)
        self.assertEqual(len(ATTESTED_MEMBERS), 88, "edit-in-place — ATTESTED stands at 88 (C7 P3b-6a's net.c)")
        self.assertEqual(ATTESTED_MEMBERS, tuple(sorted(ATTESTED_MEMBERS)), "the list stays sorted")
        self.assertEqual(law_guard_surface(), sorted(ATTESTED_MEMBERS), "the walk-guard covers src/body")
        self.assertEqual(twin_uncovered(), [], "nothing under src/ outside the attested list (I7)")

    def test_the_prover_source_is_a_fixture_under_tests_not_src_body(self):
        self.assertTrue(os.path.exists(PROVER_FIXTURE), "the prover source is a fixture under tests/")
        self.assertFalse(os.path.exists(os.path.join(BODY, "c7_p3b_4f_ii_prover_threaded.c")),
                         "the prover source is NOT under src/body (where the walk-guard would make it a member)")

    def test_the_built_prover_and_body_images_are_never_signed_members(self):
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertFalse(any(m.endswith((".elf", ".o", ".img")) for m in ATTESTED_MEMBERS),
                         "§9 mechanism 3: the built prover/worker/body images are NEVER signed members")

    def test_the_classification_is_kept_as_the_router_with_real_concurrency_machinery(self):
        with open(os.path.join(BODY, "serve.c"), encoding="utf-8") as f:
            serve = f.read()
        for token in ("serve_request", "CAT_ACT", "MODULE_SEARCH_SENTINEL", "SV_REFUSED"):
            self.assertIn(token, serve, "the P3b-4b classification router is kept (%s)" % token)
        # the canned concurrency answers are replaced by real machinery when the floor is active.
        for token in ("sched_clone3", "sched_futex", "sched_thread_exit", "SYS_exit"):
            self.assertIn(token, serve, "the canned concurrency answers are replaced by real machinery (%s)" % token)

    def test_no_host_kernel_load_in_the_body_c(self):
        for name in ("serve.c", "serve.h", "enclosure.c", "enclosure.h", "enclosure.S", "kmain.c", "idt.c"):
            with open(os.path.join(BODY, name), encoding="utf-8", errors="replace") as f:
                self.assertEqual(_host_kernel_load_tokens(f.read()), [],
                                 "src/body/%s loads a module into the host kernel (forbidden, L11)" % name)
        self.assertEqual(_host_kernel_load_tokens("insmod x.ko"), ["insmod"])   # the scan CAN fail

    def test_no_borrowed_interpreter_in_this_rung(self):
        # RE-POINTED (C7 MAINT-BODY-SCANS): from a source-TEXT word scan (which reddened on the legitimate
        # P3b-4c/4g comments naming the real interpreter) to the PROPERTY I3 those comments do not breach —
        # (A2) body.elf links no interpreter / borrowed C-library object, and (A3) no attested member is an
        # interpreter file. This rung is proven with an ordinary threaded borrowed program run as a sealed
        # image/module (P3b-4c/4d), never linked into the body and never a signed member.
        from kernel.attestation import ATTESTED_MEMBERS

        # (A2) the body.elf link — where "linked into body.elf" is decided.
        with open(os.path.join(BODY, "build.sh"), encoding="utf-8") as _bf:
            link = _body_elf_link_command(_bf.read())
        self.assertIsNotNone(link, "the body.elf link command was not found in src/body/build.sh")
        self.assertIn("-nostdlib", link, "the body link must be freestanding (no borrowed C runtime linked)")
        objs, libs = _link_inputs(link)
        self.assertEqual(_borrowed_interpreter_link_inputs(objs, libs), [],
                         "body.elf links a borrowed interpreter / C-library object (I3 breach)")
        # PLANT: a linked interpreter object / a -lpython flag reds the check (the scan CAN fail).
        self.assertEqual(_borrowed_interpreter_link_inputs(objs + ["libpython3.12.so"], libs),
                         ["libpython3.12.so"], "the linked-artifact scan cannot fail")
        self.assertEqual(_borrowed_interpreter_link_inputs(objs, libs + ["-lpython3.12"]),
                         ["-lpython3.12"], "the library-flag scan cannot fail")

        # (A3) no attested member is an interpreter file.
        self.assertEqual(_interpreter_members(ATTESTED_MEMBERS), [],
                         "an attested member is a borrowed interpreter file (I3 breach)")
        # PLANT: an interpreter file name in a FIXTURE copy of the member list reds (never the real manifest).
        planted = tuple(ATTESTED_MEMBERS) + ("body/libpython3.12.so.1.0",)
        self.assertEqual(_interpreter_members(planted), ["body/libpython3.12.so.1.0"],
                         "the member-list scan cannot fail")

    def test_the_p2_host_crossing_census_stays_clean(self):
        from tools.conformance import host_crossing_census as census
        self.assertEqual(census.undeclared_crossings(), {}, "the core (src/body included) is host-clean")


@unittest.skipUnless(GUEST, "SKIP BODY-BOOT: the mid-act-switch plant needs the pinned guest + nested qemu over SSH -p 2222")
class TestA5NoSwitchInsideAnAct(unittest.TestCase):
    def test_clean_never_switches_inside_an_act(self):
        serial = _serial()
        self.assertIn("FLOOR2-SWITCH-IN-ACT: 0x00000000", serial, "clean: the scheduler never switched inside an act")

    def test_a_planted_mid_act_switch_reds_the_check(self):
        # the plant lets the timer fire during a ring-0 act and switch there; the body counts the violation.
        plant = _serial("PLANT_SWITCH_INSIDE_ACT", timeout_s=60)
        m = re.search(r"FLOOR2-SWITCH-IN-ACT: 0x([0-9a-f]+)", plant)
        self.assertIsNotNone(m, "the switch-in-act counter is on serial")
        self.assertGreater(int(m.group(1), 16), 0, "a planted mid-act switch is counted (the check CAN fail)")
        self.assertIn("FLOOR2: FAIL", plant, "the concurrency-floor self-check reds when a switch happened inside an act")


# ── A6 ───────────────────────────────────────────────────────────────────────────────────────────
class TestA6NoFoundingTwelveActs(unittest.TestCase):
    def test_no_founding_act_kinds_twelve_pack_byte_unchanged(self):
        import hashlib
        import json
        from kernel.boot import ACT_KIND_RECORD_KIND

        pack_path = os.path.join(SRC, "founding", "founding-pack.json")
        with open(pack_path, "rb") as f:
            raw = f.read()
        self.assertTrue(hashlib.sha256(raw).hexdigest().startswith("95631e8f"),
                        "the founding pack is byte-unchanged (sha256 95631e8f…) — no founding")
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
        kinds = {r["seam_kind"] for r in rows}
        self.assertEqual(len(kinds), 12, "ACT_KINDS stays twelve — the concurrency floor adds no act")


if __name__ == "__main__":
    unittest.main()
