#!/usr/bin/env bash
# gov-os body build — GUEST-ONLY (C7 P3b-1; L11 / EP-00 rule 9 / charter §A21).
#
# Compiles the freestanding body (boot.S + the hand-written C) into an x86_64 multiboot1 ELF that
# qemu -kernel boots as a NESTED guest inside the pinned guest. The multiboot1 loader enters the
# 32-bit entry (boot.S), which TRAMPOLINES into the machine's own long mode (C7 P3b-4L). It never
# loads anything into the host kernel — the only kernel that runs is the body itself, under the
# nested qemu. Build artifacts (.o/.elf/.img) are written to <outdir>, NEVER back into the source tree
# (neither the body .elf nor the sealed worker image is a signed source member, §9 mechanism 3).
#
# C7 P3b-4a — THE WORKER'S ENCLOSURE: the body hosts OUR small test worker beneath the seam. The worker
# (worker.S + worker.ld) is built FIRST into a SEALED IMAGE (worker.elf, an ELF64); the body carries the
# image's sha256 (WORKER_IMG_SHA256HEX) and incbins the image (enclosure.S), and the body's own ELF64
# loader DIGEST-CHECKS the image before loading it. The built worker image is a binary, NEVER a member.
#
# Usage: build.sh <srcdir> <outdir> [FAULT]
#   FAULT (optional): inject a single self-check fault (A2/A5 near-miss — the check can fail). One of:
#     memory (P3b-1): PLANT_VMM_WRONG | PLANT_HEAP_OVERLAP
#     disk   (P3b-2): PLANT_RECORD_READBACK_WRONG | PLANT_RECORD_OVERWRITE_ALLOWED |
#                     PLANT_WRITEONCE_OVERWRITE | PLANT_REMOVE_LEAVES | PLANT_WALK_MISSES | PLANT_PACK_WRONG
#     clock  (P3b-3): PLANT_BAD_GATE | PLANT_TIMER_DEAD | PLANT_MONO_BACKWARDS | PLANT_ENTROPY_CONSTANT |
#                     PLANT_ENTROPY_UNSEEDED | PLANT_HANG
#     mode   (P3b-4L): PLANT_NO_LONGMODE
#     enclosure (P3b-4a):
#                     PLANT_WORKER_RING0          the worker returns into ring 0 -> CHECK RING3 reds
#                     PLANT_BODY_USER_ACCESSIBLE  a body page is mapped USER -> the direct reach does not
#                                                 fault -> CHECK TRESPASS reds
#                     PLANT_NO_SYSCALL_MSR        the SYSCALL MSRs are not set -> the worker's SYSCALL #UDs
#                                                 -> CHECK CROSSING reds
#                     PLANT_OUTOFSET_SERVED       the out-of-set request is served -> CHECK REFUSAL reds
#                     PLANT_REFUSAL_NOT_NATIVE    a gov-os-shaped refusal, not native -> CHECK REFUSAL reds
#                     PLANT_TRAIL_SKIP            a crossing is not recorded as a row -> CHECK TRAIL reds
#                     PLANT_WORKER_IMAGE_TAMPER   the sealed image's bytes are changed AFTER sealing -> the
#                                                 loader refuses it (LOAD: REFUSED) — a digest change is refused
#     serve  (P3b-4b — the forty-nine served; each reds exactly its own SERVE CHECK):
#                     PLANT_SERVE_TRAIL_SKIP       an acts'-share crossing (mmap) not recorded -> WITNESSED reds
#                     PLANT_BODY_SIGNS_ROW         an acts'-share row carries a signature (a key) -> KEYLESS reds
#                     PLANT_ACT_ROW_IN_CHAIN       an acts'-share row appended into the signed chain -> UNSIGNED reds
#                     PLANT_ENTROPY_NOT_AT_BRINGUP the bring-up entropy draw deferred -> ENTROPY-BRINGUP reds
#                     PLANT_MEM_FORK_SHARED        the memory act serves fork-shareable memory -> MEM-PRIVATE reds
#                     PLANT_THREAD_NO_SETTLS       thread-create drops SETTLS -> THREAD-SHAPE reds
#                     PLANT_COMMIT_NOT_ABSOLUTE    the commit-window deadline not absolute -> COMMIT-ABSOLUTE reds
#                     PLANT_FUTEX_WRONG_SHAPE      the wait not PRIVATE bitset realtime -> FUTEX-SHAPE reds
#                     PLANT_FS_WALK_SERVED         the module-discovery scan served (a fs walk) -> REFUSAL-MODULE reds
#                     PLANT_SOCKET_SERVED          the network-socket share served, not refused -> SOCKET-REFUSED reds
#                     PLANT_SERVE_CATEGORY_E       a category-E call declared served, not excluded -> EXCLUDED reds
#     net    (P3b-6a): PLANT_NET_TX_DEAD           the transmit queue is not kicked -> no frame goes on the
#                                                  wire -> the gateway has nothing to answer -> the receive
#                                                  poll times out -> CHECK WIRE-ROUNDTRIP reds (a REAL
#                                                  mechanism: no frame, no reply — never a flag)
set -euo pipefail

SRCDIR="${1:?usage: build.sh <srcdir> <outdir> [FAULT]}"
OUT="${2:?usage: build.sh <srcdir> <outdir> [FAULT]}"
FAULT="${3:-}"

mkdir -p "$OUT"

# -m64 with the kernel-safe flags: -mno-red-zone (an interrupt must not clobber a leaf's red zone),
# and no MMX/SSE (the body never enables the FPU/SSE state, so integer-only codegen avoids a #UD /
# state corruption on a vector op). Long mode divides 64-bit natively, so still no libgcc helper.
CFLAGS="-m64 -mno-red-zone -mno-mmx -mno-sse -mno-sse2 -ffreestanding -fno-pie -fno-stack-protector -fno-asynchronous-unwind-tables -fno-unwind-tables -nostdlib -Wall -Wextra -O2 -std=gnu11 -I$SRCDIR"

# ── OUR small test worker (C7 P3b-4a), built FIRST into a SEALED IMAGE. Deterministic link (no
# build-id) so the image and its seal are byte-reproducible. The body incbins worker.elf and carries
# its sha256; the loader refuses an image whose bytes do not fold to it.
gcc $CFLAGS -c "$SRCDIR/worker.S" -o "$OUT/worker.o"
ld --build-id=none -z noexecstack -T "$SRCDIR/worker.ld" -o "$OUT/worker.elf" "$OUT/worker.o"
WORKER_SHA=$(sha256sum "$OUT/worker.elf" | cut -d' ' -f1)

# PLANT_WORKER_IMAGE_TAMPER (A3 near-miss): change one byte of the sealed image AFTER computing its
# seal. The body's loader folds the (now different) bytes and REFUSES the load — a digest change is
# refused AT LOAD. The seal WORKER_SHA stays the intact digest; only the incbin'd bytes differ.
if [ "$FAULT" = "PLANT_WORKER_IMAGE_TAMPER" ]; then
    python3 -c "b=bytearray(open('$OUT/worker.elf','rb').read()); b[64]^=0xff; open('$OUT/worker.elf','wb').write(b)"
    FAULT=""   # the tamper IS the fault; it is not a -D code flag
fi

# ── C7 P3b-4f-i — THE STATIC SINGLE-THREAD PROVER (design/54 §5 L19). Built ONLY when PROVER_SRC names a
# fixture (the test under tests/ sets it); the worker-only P3b-4a/4b/4L/4m builds leave it unset and are
# byte-for-byte unchanged. An ORDINARY `gcc -static` single-threaded glibc program built by the guest's OWN
# toolchain with NO link-base or position flag of any kind — so its first PT_LOAD sits at the x86_64
# canonical base 0x400000 (archi :4122). It is NOT written to fit the body (L19); only the built binary is
# staged, sealed by its sha256 (PROVER_IMG_SHA256HEX), and embedded by enclosure.S's .incbin. The built
# prover IMAGE is a binary, NEVER a signed member (§9 mechanism 3), exactly like worker.elf and body.elf.
# C7 P3b-4f-ii — THE CONCURRENCY FLOOR: the prover is the FROZEN 4f A1 threaded program, built `gcc -static
# -pthread` (PROVER_PTHREAD=1), and the body is built with -DCONCURRENCY_FLOOR (CONCURRENCY=1) so kmain runs
# floor2_run (real threads/scheduler/futex) instead of the single-thread floor_run. The prover is still an
# ORDINARY program (NOT shaped to the body, L19); only the built binary is staged, sealed and embedded.
PROVER_SRC="${PROVER_SRC:-}"
PROVER_PTHREAD="${PROVER_PTHREAD:-}"
CONCURRENCY="${CONCURRENCY:-}"
PROVER_DEF=""
if [ -n "$PROVER_SRC" ] && [ -f "$PROVER_SRC" ]; then
    PROVER_CC_EXTRA=""
    if [ -n "$PROVER_PTHREAD" ]; then PROVER_CC_EXTRA="-pthread"; fi
    gcc -static -O2 $PROVER_CC_EXTRA -Wl,--build-id=none "$PROVER_SRC" -o "$OUT/prover.elf"
    PROVER_SHA=$(sha256sum "$OUT/prover.elf" | cut -d' ' -f1)
    PROVER_DEF="-DPROVER_PRESENT -DPROVER_IMG_SHA256HEX=\"$PROVER_SHA\""
    if [ -n "$CONCURRENCY" ]; then PROVER_DEF="$PROVER_DEF -DCONCURRENCY_FLOOR"; fi
fi

# ── C7 P3b-4d — THE DYNAMIC FLOOR: a DYNAMICALLY-linked threaded prover + a SEALED IMAGE. The prover is an
# ORDINARY `gcc -pthread -no-pie` program (dynamic, ET_EXEC at the canonical base 0x400000; NOT shaped to the
# body, L19) — the small prover_image the loader embeds (enclosure.S .incbin, well under the base). The SEALED
# IMAGE stages the guest's OWN ld.so + libc (the prover's real DT_NEEDED / PT_INTERP) into ONE GOVSIMG1 archive
# carrying directory entries (so it is served by listing, Q15/:4134). C7-MAINT-4D-BOOT-AS-MODULE: the ~2.26 MB
# sealed image is CARRIED AS A BOOT-TIME MULTIBOOT MODULE (boot with -initrd <out>/sealed.img, read through the
# body's direct map via g_sealed_module_phys — exactly as the 4c interpreter / 5b ledger paths do), NOT embedded
# into the body's own image: embedding pushed the body's _bss_end over the 4 MiB canonical base and triple-faulted
# at the CR3 switch (FINDINGS.md F1/F2). Both are built/borrowed artifacts, NEVER signed members (§9 mechanism 3).
DYN_PROVER_SRC="${DYN_PROVER_SRC:-}"
SEALED_SHA=""
if [ -n "$DYN_PROVER_SRC" ] && [ -f "$DYN_PROVER_SRC" ]; then
    gcc -O2 -pthread -no-pie -Wl,--build-id=none "$DYN_PROVER_SRC" -o "$OUT/prover.elf"
    PROVER_SHA=$(sha256sum "$OUT/prover.elf" | cut -d' ' -f1)
    # stage the sealed image from the prover's OWN interpreter + shared-library needs (ldd/readelf).
    python3 - "$OUT/prover.elf" "$OUT/sealed.img" <<'PYSEAL'
import sys, os, re, struct, subprocess
prover, outimg = sys.argv[1], sys.argv[2]
rl = subprocess.run(["readelf","-lW",prover], capture_output=True, text=True).stdout
m = re.search(r"Requesting program interpreter:\s*([^\]]+)\]", rl)
interp = m.group(1).strip() if m else "/lib64/ld-linux-x86-64.so.2"
ldd = subprocess.run(["ldd",prover], capture_output=True, text=True).stdout
paths = set()
for line in ldd.splitlines():
    mm = re.search(r"=>\s*(/\S+)", line)            # "libc.so.6 => /lib/.../libc.so.6 (0x..)"
    if mm: paths.add(mm.group(1)); continue
    mm2 = re.match(r"\s*(/\S+)", line)              # "/lib64/ld-linux-x86-64.so.2 (0x..)"
    if mm2: paths.add(mm2.group(1))
paths.add(interp)
files = {}
for p in sorted(paths):
    if "vdso" in p: continue                        # the vDSO is kernel-provided, not a file
    try:
        with open(p,"rb") as f: files[p] = f.read() # the STAGED path is where ld.so opens it (Q8)
    except OSError: pass
if interp not in files:
    with open(interp,"rb") as f: files[interp] = f.read()
dirs = set()
for p in files:                                     # every ancestor directory (so the image is listable)
    parts = p.strip("/").split("/")
    for i in range(1, len(parts)): dirs.add("/" + "/".join(parts[:i]))
entries = [(d,1,b"") for d in sorted(dirs)] + [(p,0,files[p]) for p in sorted(files)]
HDR, ENT = 16, 128
cur = HDR + len(entries)*ENT
table, blob = bytearray(), bytearray()
for path, flag, body in entries:
    pb = path.encode()
    assert len(pb) < 104, path
    off = 0 if flag else cur
    length = 0 if flag else len(body)
    table += struct.pack("<104sQQII", pb, off, length, flag, 0)
    if not flag: blob += body; cur += len(body)
with open(outimg,"wb") as f:
    f.write(struct.pack("<8sII", b"GOVSIMG1", 1, len(entries))); f.write(table); f.write(blob)
sys.stderr.write("sealed %d entries (%d dirs), %d bytes; interp=%s\n"
                 % (len(entries), len(dirs), HDR+len(table)+len(blob), interp))
PYSEAL
    SEALED_SHA=$(sha256sum "$OUT/sealed.img" | cut -d' ' -f1)
    # PLANT_SEAL_TAMPER (A2): change one byte of the sealed image AFTER computing its seal — the body folds
    # the (now different) bytes and REFUSES the load; the prover never starts. The seal stays the intact
    # digest; only the incbin'd bytes differ. (It is the tamper itself, not a -D code flag.)
    if [ "$FAULT" = "PLANT_SEAL_TAMPER" ]; then
        python3 -c "b=bytearray(open('$OUT/sealed.img','rb').read()); b[len(b)//2]^=0xff; open('$OUT/sealed.img','wb').write(b)"
        FAULT=""
    fi
    PROVER_DEF="-DPROVER_PRESENT -DPROVER_IMG_SHA256HEX=\"$PROVER_SHA\" -DDYNAMIC_FLOOR -DSEALED_IMG_SHA256HEX=\"$SEALED_SHA\""
fi

# ── C7 P3b-4c — THE INTERPRETER RUNS ON THE BODY. Stage the ONE SEALED IMAGE carrying the REAL
# /usr/bin/python3 + its measured file set (the C library + loader-visible pieces + the standard library as
# REAL FILES served by path AND by listing; the .py present + stat-validated so the timestamp .pyc is used
# without opening the .py). The file SET is driven by the interpreter's OWN strace manifest — faithful (real
# files, real mtimes, no fabrication — L19) and self-binding to the CURRENT guest binary (the re-seal/re-pin
# at dispatch). The interpreter is NOT a separate incbin'd prover (it is IN the one sealed image), and the
# ~21 MB image is too large to incbin beneath the program's 0x400000 base, so it is carried as a multiboot
# MODULE (boot with -initrd <out>/sealed.img) and digest-checked as one unit (B6). NO founding, no pack edit.
INTERP="${INTERP:-}"
GATE="${GATE:-}"
# C7 P3b-6c slice (ii): BRIDGE builds the COMBINED body — the interpreter's sealed image (this INTERP block,
# with the bridge script) AND the lwIP worker's prover_image (the NET_WORKER block, with the bridge glue) —
# and merges both PROVER_DEFs plus -DBRIDGE (see the NET_WORKER block). BRIDGE implies INTERP + NET_WORKER.
BRIDGE="${BRIDGE:-}"
if [ -n "$BRIDGE" ]; then INTERP=1; fi
# C7 P3b-6c slice (iii): SOCKET_ACT builds the COMBINED body — the interpreter's sealed image (this INTERP
# block, with the socket-act script) AND the lwIP op-server worker's prover_image (the NET_WORKER block, with
# the slice-iii glue) — with the live NIC, and merges both PROVER_DEFs plus -DSOCKET_ACT (NET_WORKER block).
# SOCKET_ACT implies INTERP + NET_WORKER; it is DISTINCT from BRIDGE (the persistent coroutine, the 8 shapes).
SOCKET_ACT="${SOCKET_ACT:-}"
if [ -n "$SOCKET_ACT" ]; then INTERP=1; fi
# C7 P3b-6c slice (iii) A1 — THE GRANT-FIRST BOOT: gov-os's OWN gate composes on the freestanding body and
# records the network-open as a rule-citing decision FIRST, then hands ONLY a granted decision to the proven
# relay. It needs BOTH the LEDGER whole-stdlib sealed image (so build_full_kernel's 30-module closure imports
# off the record disk) AND the SOCKET_ACT relay + lwIP worker (so a granted decision reaches one real
# connection). So GRANT implies LEDGER (the image) + NET_WORKER (the worker), and adds -DSOCKET_ACT (kmain
# dispatches floor_socket_act_run) + -DGRANT_FIRST (the -c grant program + the grant-first verdict) in the
# NET_WORKER block. GRANT does NOT set INTERP — no narrow per-script strace image; the LEDGER block stages
# the whole stdlib. GRANT_REFUSED builds the refused-decision variant (the gate raises, NO relay); the
# relay-on-refusal plant rides the FAULT arg (PLANT_GRANT_BYPASS). SOCKET_ACT stays UNSET as an env var, so a
# plain SOCKET_ACT boot is byte-identical (the g_sa_script relay is unchanged; every GRANT addition is #ifdef
# GRANT_FIRST-gated).
GRANT="${GRANT:-}"
GRANT_REFUSED="${GRANT_REFUSED:-}"
if [ -n "$GRANT" ]; then LEDGER=1; NET_WORKER=1; fi
if [ -n "$INTERP" ]; then
    PROGRAM=/usr/bin/python3.12
    INTERPLD=/lib64/ld-linux-x86-64.so.2
    # the -c program the body will run (argv); its IMPORTS drive the manifest. Must match enclosure.c's
    # g_py_script import set so the staged set is exactly what the real interpreter opens.
    SCRIPT='import hmac,hashlib,json,base64,unicodedata,threading,os,io,struct,time,datetime
print(2+2)
def w():
    print("thread-ran")
t=threading.Thread(target=w)
t.start()
t.join()'
    GOVSRC=""
    if [ -n "$GATE" ]; then
        # C7 P3b-4g — GATE ON THE BODY: the on-body program is gov-os's OWN gate, run as content off
        # the record disk (enclosure.c g_gate_script). Its imports pull a WIDER stdlib closure (the key
        # family's socket/mmap/collections/contextlib/re/... plus importlib.abc/machinery). The strace
        # SCRIPT imports+exercises the REAL key family so that closure is measured into the sealed image;
        # the gov-os SOURCE it opens is EXCLUDED below (it is CONTENT on the record disk, :4091 c — NOT
        # in the borrowed image, I7). Must match g_gate_script's import set.
        GOVSRC="$(cd "$SRCDIR/.." && pwd)"
        SCRIPT="import sys
sys.path.insert(0, '$GOVSRC')
import json, base64, hashlib, importlib.abc, importlib.machinery
from kernel import keys, signer, crypto
from kernel.canonical import canonical_hash
sk = signer.SigningKeyStore(); c = sk.seal(b'guest-test')
m = keys.countersign({'seq': 1, 'record_time': 't'}, c)
assert keys.verify_countersign(m, {'seq': 1, 'record_time': 't'}, c)
canonical_hash({'a': 1, 'b': [1, 2]})
print('gate-manifest-ok')"
    fi
    if [ -n "$BRIDGE" ]; then
        # C7 P3b-6c (ii): the bridge program — the REAL interpreter issues ONE socket-family syscall per
        # relay via ctypes -> glibc's syscall wrapper -> SYS_socket, so the enclosed run routes it to the
        # ring-0 bridge. Its imports (ctypes -> _ctypes.so + libffi) drive the manifest; MUST match
        # enclosure.c's g_bridge_script. On the guest strace the socket calls are real+harmless (a fd, then
        # an invalid-proto -1); the enclosed run relays them instead.
        SCRIPT="import ctypes
libc=ctypes.CDLL(None,use_errno=True)
libc.syscall.restype=ctypes.c_long
r1=libc.syscall(41,2,1,0)
print('PYSOCK-R1',r1)
print('PYSOCK-DONE')"
        GOVSRC=""
    fi
    if [ -n "$SOCKET_ACT" ]; then
        # C7 P3b-6c (iii): the socket-act manifest program — imports ctypes+struct (the runtime g_sa_script's
        # closure: _ctypes.so + libffi). A single non-blocking socket() is harmless on the guest strace; the
        # enclosed run relays the whole client connection. MUST match enclosure.c's g_sa_script import set.
        SCRIPT="import ctypes,struct
libc=ctypes.CDLL(None,use_errno=True)
libc.syscall.restype=ctypes.c_long
libc.syscall(ctypes.c_long(41),ctypes.c_long(2),ctypes.c_long(1),ctypes.c_long(0))
print('PYSOCK-MANIFEST')"
        GOVSRC=""
    fi
    strace -f -qq -o "$OUT/manifest.trace" "$PROGRAM" -I -S -c "$SCRIPT" >/dev/null 2>&1 || true
    python3 - "$OUT/manifest.trace" "$OUT/sealed.img" "$INTERPLD" "$PROGRAM" "$GOVSRC" <<'PYSTAGE4C'
import sys, os, re, struct
tracef, outimg, interp_path, program_path = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
govsrc = sys.argv[5] if len(sys.argv) > 5 else ""   # C7 P3b-4g: gov-os source is EXCLUDED (record-disk content)
files, dirs = {}, set()
def _excluded(p):
    return bool(govsrc) and (p == govsrc or p.startswith(govsrc + "/"))   # gov-os source -> record disk, not the image
def add_file(p):
    if p in files or _excluded(p): return
    with open(p, "rb") as f: b = f.read()          # open() FOLLOWS symlinks -> the bytes the kernel serves
    files[p] = (b, int(os.stat(p).st_mtime) & 0xFFFFFFFF)   # .pyc timestamp format == 32-bit mtime
def add_ancestors(p):
    if _excluded(p): return
    parts = p.strip("/").split("/")
    for i in range(1, len(parts)):
        d = "/" + "/".join(parts[:i])
        if not _excluded(d): dirs.add(d)
add_file(program_path); add_ancestors(program_path)
add_file(interp_path);  add_ancestors(interp_path)
opened, dir_opens, stat_py = set(), set(), set()
for line in open(tracef, errors="replace"):
    if re.search(r'\bopenat\(', line) and "= -1" not in line:
        m = re.search(r'"(/[^"]+)"', line)
        if m:
            (dir_opens if "O_DIRECTORY" in line else opened).add(m.group(1))
    if re.search(r'\bnewfstatat\(', line) and "= -1" not in line:
        m = re.search(r'"(/[^"]+\.py)"', line)
        if m: stat_py.add(m.group(1))
for p in sorted(dir_opens):
    if not _excluded(p): dirs.add(p); add_ancestors(p)
for p in sorted(opened):    add_file(p); add_ancestors(p)
for p in sorted(stat_py):   add_file(p); add_ancestors(p)
entries = [(d, 1, b"", 0) for d in sorted(dirs)] + \
          [(p, 0, files[p][0], files[p][1]) for p in sorted(files)]
HDR, ENT = 16, 128
cur = HDR + len(entries) * ENT
table, blob = bytearray(), bytearray()
for path, flag, body, mt in entries:
    pb = path.encode(); assert len(pb) < 104, path
    off = 0 if flag else cur; length = 0 if flag else len(body)
    table += struct.pack("<104sQQII", pb, off, length, flag, mt)
    if not flag: blob += body; cur += len(body)
with open(outimg, "wb") as f:
    f.write(struct.pack("<8sII", b"GOVSIMG1", 1, len(entries))); f.write(table); f.write(blob)
sys.stderr.write("STAGED %d entries (%d dirs, %d files), %d bytes\n"
                 % (len(entries), len(dirs), len(files), HDR + len(table) + len(blob)))
PYSTAGE4C
    SEALED_SHA=$(sha256sum "$OUT/sealed.img" | cut -d' ' -f1)
    # PLANT_SEAL_TAMPER (A1): flip one byte AFTER sealing — the body folds the changed bytes and REFUSES
    # the load; the REAL interpreter never starts. The seal stays the intact digest. (The tamper IS the
    # fault, not a -D code flag.)
    if [ "$FAULT" = "PLANT_SEAL_TAMPER" ]; then
        python3 -c "b=bytearray(open('$OUT/sealed.img','rb').read()); b[len(b)//2]^=0xff; open('$OUT/sealed.img','wb').write(b)"
        FAULT=""
    fi
    PROVER_DEF="-DPROVER_PRESENT -DDYNAMIC_FLOOR -DINTERP_FLOOR -DSEALED_IMG_SHA256HEX=\"$SEALED_SHA\""
    if [ -n "$GATE" ]; then PROVER_DEF="$PROVER_DEF -DGATE_ON_BODY"; fi
fi

# ── C7 P3b-5b-i — THE LEDGER RUN STACK: the WHOLE SHIPPED stdlib image (design/54 §7 P3b-5b, precision 1;
# archi :4303). Stage the REAL /usr/bin/python3.12 + its ld + the WHOLE shipped standard library AT SHIPPED
# PATHS (EXCLUDING test/, idlelib, tkinter, turtledemo, ensurepip, lib2to3, and site-/dist-packages) + the
# DT_NEEDED closure of the program and every lib-dynload C extension (libcrypto/libssl/libffi/… the stdlib
# actually dlopens) + openssl.cnf, into ONE GOVSIMG1 image, digest-checked WHOLE (B6). NO per-script strace
# manifest (retired for the ledger — a per-module manifest over 106 modules is the curated subset :4235
# refuses). The image is FIXED across all ledger modules; the per-module part is the record disk (the module
# name as data + the tree). The longest staged path MUST be < SI_PATH_MAX (104, serve.c:72), asserted here.
# 5b-i MEASURES the boot cost of this image size in the nested guest (-m 256). Enclosed worker, NEVER a
# member (I3/I7); no founding, no pack edit.
LEDGER="${LEDGER:-}"
if [ -n "$LEDGER" ]; then
    python3 - "$OUT/sealed.img" <<'PYSTAGE5B'
import sys, os, re, struct, subprocess
outimg = sys.argv[1]
LIB = "/usr/lib/python3.12"
EXCL_TOP = {"test", "idlelib", "tkinter", "turtledemo", "ensurepip", "lib2to3"}
prog = "/usr/bin/python3.12"; ld = "/lib64/ld-linux-x86-64.so.2"
def ldd_libs(p):
    out = set()
    try: r = subprocess.run(["ldd", p], capture_output=True, text=True).stdout
    except Exception: return out
    for line in r.splitlines():
        m = re.search(r"=>\s*(/\S+)", line) or re.match(r"\s*(/\S+)", line)
        if m and "vdso" not in m.group(1) and os.path.exists(m.group(1)): out.add(m.group(1))
    return out
stdlib = []
for root, dirs, fns in os.walk(LIB):
    rel = os.path.relpath(root, LIB); top = rel.split(os.sep)[0] if rel != "." else ""
    if top in EXCL_TOP: dirs[:] = []; continue
    dirs[:] = [d for d in dirs if d not in ("site-packages", "dist-packages")]
    for fn in fns: stdlib.append(os.path.join(root, fn))
syslibs = set([ld]); syslibs |= ldd_libs(prog)
dyn = os.path.join(LIB, "lib-dynload")
if os.path.isdir(dyn):
    for f in os.listdir(dyn):
        if f.endswith(".so"): syslibs |= ldd_libs(os.path.join(dyn, f))
syslibs = {x for x in syslibs if not x.startswith(LIB)}       # stdlib .so already counted in stdlib
cfg = []
if any(("libcrypto" in x or "libssl" in x) for x in syslibs):
    for c in ("/usr/lib/ssl/openssl.cnf", "/etc/ssl/openssl.cnf"):
        if os.path.exists(c): cfg.append(c)
allpaths = sorted(set(stdlib) | syslibs | {prog} | set(cfg))
files, dirs = {}, set()
def add_anc(p):
    parts = p.strip("/").split("/")
    for i in range(1, len(parts)): dirs.add("/" + "/".join(parts[:i]))
for p in allpaths:
    try:
        with open(p, "rb") as f: b = f.read()                 # open() follows symlinks -> the served bytes
    except OSError: continue
    files[p] = (b, int(os.stat(p).st_mtime) & 0xFFFFFFFF); add_anc(p)
longest = max((len(p) for p in list(files) + list(dirs)), default=0)
assert longest < 104, "longest staged path %d >= SI_PATH_MAX 104" % longest
entries = [(d, 1, b"", 0) for d in sorted(dirs)] + \
          [(p, 0, files[p][0], files[p][1]) for p in sorted(files)]
HDR, ENT = 16, 128
cur = HDR + len(entries) * ENT
table, blob = bytearray(), bytearray()
for path, flag, body, mt in entries:
    pb = path.encode(); assert len(pb) < 104, path
    off = 0 if flag else cur; length = 0 if flag else len(body)
    table += struct.pack("<104sQQII", pb, off, length, flag, mt)
    if not flag: blob += body; cur += len(body)
with open(outimg, "wb") as f:
    f.write(struct.pack("<8sII", b"GOVSIMG1", 1, len(entries))); f.write(table); f.write(blob)
sys.stderr.write("LEDGER STAGED %d entries (%d dirs, %d files), %d bytes, longest path %d\n"
                 % (len(entries), len(dirs), len(files), HDR + len(table) + len(blob), longest))
PYSTAGE5B
    SEALED_SHA=$(sha256sum "$OUT/sealed.img" | cut -d' ' -f1)
    # PLANT_SEAL_TAMPER: flip one byte AFTER sealing — the body folds the changed bytes and REFUSES the load;
    # the REAL interpreter never starts. The seal stays the intact digest. (The tamper IS the fault.)
    if [ "$FAULT" = "PLANT_SEAL_TAMPER" ]; then
        python3 -c "b=bytearray(open('$OUT/sealed.img','rb').read()); b[len(b)//2]^=0xff; open('$OUT/sealed.img','wb').write(b)"
        FAULT=""
    fi
    PROVER_DEF="-DPROVER_PRESENT -DDYNAMIC_FLOOR -DINTERP_FLOOR -DGATE_ON_BODY -DLEDGER_ON_BODY -DSEALED_IMG_SHA256HEX=\"$SEALED_SHA\""
fi

# ── C7 P3b-6b — THE BORROWED TCP ENCLOSED: build the sealed static NO_SYS lwIP worker (the prover_image).
# NET_WORKER is set by the 6b test, which fetches the lwIP 2.2.0 SOURCE (apt-get source liblwip-dev,
# provenance-pinned .dsc/orig sha256 — mgr's dispatch pre-flight) into LWIP_SRC and stages the config-only
# glue fixture (GLUE_SRC) + lwipopts.h + arch/cc.h under LWIP_PORT. The worker is lwIP's UNMODIFIED core +
# its OWN example (src/apps/lwiperf/lwiperf.c) + our config-only glue, linked -static (ELF64 ET_EXEC at the
# canonical base — NOT shaped to the body, L5/L19). It is CONTENT — sealed by its sha256 and embedded by
# enclosure.S's .incbin (the prover_image slot), NEVER a signed member (§9 mechanism 3 / I3). NO founding.
NET_WORKER="${NET_WORKER:-}"
LWIP_SRC="${LWIP_SRC:-}"
GLUE_SRC="${GLUE_SRC:-}"
LWIP_PORT="${LWIP_PORT:-}"
if [ -n "$BRIDGE" ]; then NET_WORKER=1; fi   # C7 P3b-6c (ii): the combined build needs the lwIP worker too
if [ -n "$SOCKET_ACT" ]; then NET_WORKER=1; fi   # C7 P3b-6c (iii): the socket-act build needs the op-server too
if [ -n "$NET_WORKER" ]; then
    [ -d "$LWIP_SRC" ] || { echo "NET_WORKER: LWIP_SRC ($LWIP_SRC) absent — mgr's dispatch pre-flight fetches it (apt-get source liblwip-dev)"; exit 2; }
    [ -f "$GLUE_SRC" ] || { echo "NET_WORKER: GLUE_SRC ($GLUE_SRC) absent"; exit 2; }
    [ -f "$LWIP_PORT/lwipopts.h" ] || { echo "NET_WORKER: LWIP_PORT/lwipopts.h absent"; exit 2; }
    NW_INC="-I$LWIP_PORT -I$LWIP_SRC/src/include"
    NW_CF="-static -O2 -Wall -Wextra -std=gnu11 -Wno-unused-parameter -Wl,--build-id=none"
    NW_PLANT=""
    if [ "$FAULT" = "PLANT_LWIP_OVERREACH" ]; then NW_PLANT="-DPLANT_LWIP_OVERREACH"; fi   # a WORKER-side plant
    # shellcheck disable=SC2086
    gcc $NW_CF $NW_INC $NW_PLANT \
        "$LWIP_SRC"/src/core/*.c "$LWIP_SRC"/src/core/ipv4/*.c \
        "$LWIP_SRC/src/netif/ethernet.c" "$LWIP_SRC/src/apps/lwiperf/lwiperf.c" \
        "$GLUE_SRC" -o "$OUT/prover.elf"
    PROVER_SHA=$(sha256sum "$OUT/prover.elf" | cut -d' ' -f1)
    # PLANT_NETW_IMAGE_TAMPER (A1): flip one byte AFTER sealing — the loader folds the changed bytes and
    # REFUSES the load; the borrowed worker never starts. The seal stays the intact digest. (Tamper IS the fault.)
    if [ "$FAULT" = "PLANT_NETW_IMAGE_TAMPER" ]; then
        python3 -c "b=bytearray(open('$OUT/prover.elf','rb').read()); b[len(b)//2]^=0xff; open('$OUT/prover.elf','wb').write(b)"
        FAULT=""
    fi
    if [ "$FAULT" = "PLANT_LWIP_OVERREACH" ]; then FAULT=""; fi   # consumed by the worker build above
    if [ -n "$BRIDGE" ]; then
        # C7 P3b-6c (ii): the COMBINED build — MERGE the interpreter's PROVER_DEF (set by the INTERP block:
        # -DPROVER_PRESENT -DDYNAMIC_FLOOR -DINTERP_FLOOR -DSEALED_IMG_SHA256HEX=...) with the worker's image
        # seal, and add -DNET_WORKER -DBRIDGE. Both the sealed interpreter image and the incbin'd worker are
        # embedded; floor_bridge_run boots them RESIDENT TOGETHER.
        PROVER_DEF="$PROVER_DEF -DPROVER_IMG_SHA256HEX=\"$PROVER_SHA\" -DNET_WORKER -DBRIDGE"
    elif [ -n "$SOCKET_ACT" ]; then
        # C7 P3b-6c (iii): the socket-act combined build — MERGE the interpreter's PROVER_DEF (the INTERP
        # block: -DPROVER_PRESENT -DDYNAMIC_FLOOR -DINTERP_FLOOR -DSEALED_IMG_SHA256HEX=...) with the
        # op-server worker's image seal, and add -DNET_WORKER -DSOCKET_ACT (the persistent coroutine relay).
        PROVER_DEF="$PROVER_DEF -DPROVER_IMG_SHA256HEX=\"$PROVER_SHA\" -DNET_WORKER -DSOCKET_ACT"
    elif [ -n "$GRANT" ]; then
        # C7 P3b-6c (iii) A1 — THE GRANT-FIRST COMBINED BUILD: MERGE the LEDGER whole-stdlib PROVER_DEF (set
        # by the LEDGER block: -DPROVER_PRESENT -DDYNAMIC_FLOOR -DINTERP_FLOOR -DGATE_ON_BODY -DLEDGER_ON_BODY
        # -DSEALED_IMG_SHA256HEX=... over the WHOLE stdlib) with the op-server worker's image seal, and add
        # -DNET_WORKER -DSOCKET_ACT (kmain -> floor_socket_act_run, the relay) + -DGRANT_FIRST (the -c grant
        # program runs gov-os's own build_full_kernel -> CREATE-ACCOUNT -> open_real_socket_under_grant off
        # the record disk, then hands a granted decision to the relay). GRANT_REFUSED builds the refused
        # variant whose verdict expects NO relay (the plant PLANT_GRANT_BYPASS drives it anyway -> reds).
        PROVER_DEF="$PROVER_DEF -DPROVER_IMG_SHA256HEX=\"$PROVER_SHA\" -DNET_WORKER -DSOCKET_ACT -DGRANT_FIRST"
        if [ -n "$GRANT_REFUSED" ]; then PROVER_DEF="$PROVER_DEF -DGRANT_REFUSED"; fi
    else
        PROVER_DEF="-DPROVER_PRESENT -DPROVER_IMG_SHA256HEX=\"$PROVER_SHA\" -DNET_WORKER"
    fi
fi

# ── C7 P3b-6c (i) — THE MAPS PROVER: OUR small bare static ring-3 test enclosure, built from a tests/
# FIXTURE (MAPS_PROVER_SRC + MAPS_PROVER_LD, staged by the test — NEVER a src/body member, so ATTESTED
# stays 88). Deterministic link (no build-id) so the image and its seal are byte-reproducible; enclosure.S
# incbins maps.elf and the loader refuses a digest mismatch. Sets -DMAPS_PROVER so kmain runs floor_maps_run
# (the per-enclosure address-map proof). The plants are -D FAULT flags (PLANT_MAPS_*), handled below.
MAPS_PROVER_SRC="${MAPS_PROVER_SRC:-}"
MAPS_PROVER_LD="${MAPS_PROVER_LD:-}"
MAPS_DEF=""
if [ -n "$MAPS_PROVER_SRC" ] && [ -f "$MAPS_PROVER_SRC" ]; then
    gcc $CFLAGS -c "$MAPS_PROVER_SRC" -o "$OUT/maps.o"
    ld --build-id=none -z noexecstack -T "$MAPS_PROVER_LD" -o "$OUT/maps.elf" "$OUT/maps.o"
    MAPS_SHA=$(sha256sum "$OUT/maps.elf" | cut -d' ' -f1)
    MAPS_DEF="-DMAPS_PROVER -DMAPS_PROVER_IMG_SHA256HEX=\"$MAPS_SHA\""
fi

DEF="-DWORKER_IMG_SHA256HEX=\"$WORKER_SHA\" $PROVER_DEF $MAPS_DEF"
if [ -n "$FAULT" ]; then
    DEF="$DEF -D$FAULT"
fi

# -I$OUT lets enclosure.S find worker.elf for its .incbin. enclosure.S -> enclosure_asm.o (enclosure.c
# is enclosure.o); they are distinct objects.
gcc $CFLAGS $DEF -I"$OUT" -c "$SRCDIR/boot.S"      -o "$OUT/boot.o"
gcc $CFLAGS $DEF -I"$OUT" -c "$SRCDIR/isr.S"       -o "$OUT/isr.o"
gcc $CFLAGS $DEF -I"$OUT" -c "$SRCDIR/enclosure.S" -o "$OUT/enclosure_asm.o"
for unit in serial pmm vmm heap ata bodyfs diskcheck idt clock entropy clkcheck sha256 enclosure serve net kmain; do
    gcc $CFLAGS $DEF -c "$SRCDIR/$unit.c" -o "$OUT/$unit.o"
done

# No -lgcc: the body uses no 128-bit arithmetic and x86_64 divides 64-bit natively, so it references
# no libgcc helper. A freestanding link with -nostdlib and no runtime is exactly the read-whole
# intent (§9): nothing linked in that is not in the signed source. -z max-page-size=0x1000 keeps the
# LOAD segments 4 KiB-aligned in the elf64 image (the default 2 MiB alignment would push the
# multiboot header out of qemu's first-8 KiB scan window and bloat the image).
gcc -m64 -mno-red-zone -ffreestanding -nostdlib -fno-pie -no-pie -Wl,--build-id=none \
    -Wl,-z,max-page-size=0x1000 -T "$SRCDIR/linker.ld" \
    -o "$OUT/body.elf" \
    "$OUT/boot.o" "$OUT/isr.o" "$OUT/enclosure_asm.o" "$OUT/serial.o" "$OUT/pmm.o" "$OUT/vmm.o" \
    "$OUT/heap.o" "$OUT/ata.o" "$OUT/bodyfs.o" "$OUT/diskcheck.o" "$OUT/idt.o" "$OUT/clock.o" \
    "$OUT/entropy.o" "$OUT/clkcheck.o" "$OUT/sha256.o" "$OUT/enclosure.o" "$OUT/serve.o" "$OUT/net.o" "$OUT/kmain.o"

# Flatten the linked x86_64 ELF to a raw image: qemu's -kernel multiboot loader ELF-parses only
# 32-bit ELFs, so the FLAT image (loaded by the a.out-kludge address fields in the multiboot header)
# is what qemu boots. objcopy -O binary is deterministic, so a byte-reproducible body.elf yields a
# byte-reproducible body.img. The .elf is the recorded/reproducibility artifact (A3); the .img is the
# bootable one. Neither is ever a signed source member (§9 mechanism 3).
objcopy -O binary "$OUT/body.elf" "$OUT/body.img"

# ── C7 P5 — THE RELEASED CORE IMAGE, STAGED BY THE PIPELINE (design/54 §3 B6, §5 L9; countersign archi
# :4620/:4622, READING 2). The body's OWN released image (body.img) is ALSO staged, by THIS pipeline, as a
# verbatim copy core.img — so a REAL boot of the released configuration carries it as a second multiboot
# module beside the sealed interpreter (-initrd sealed.img,core.img) and hashes it on the metal. This is
# the SAME production invocation every B6 boot uses; the staging lives HERE in the build pipeline, NEVER
# fabricated in a test (that was the retired rig, :4620 READING 2). The -kernel body.img is loaded per the
# multiboot LOAD segments (not a verbatim contiguous file), so the released image is carried ALSO as a
# module the body can hash byte-for-byte — core.img == body.img byte-for-byte. Like body.img/sealed.img it
# is a built/borrowed artifact, NEVER a signed source member (§9 mechanism 3). The core is OUR OWN kernel
# (L9, read whole and signed); staging its image for a real-boot self-hash is plain buildable mechanism,
# not the owner's Q2 one-way step.
cp "$OUT/body.img" "$OUT/core.img"
CORE_SHA=$(sha256sum "$OUT/core.img" | cut -d' ' -f1)

echo "built $OUT/body.elf and $OUT/body.img (worker image seal sha256 $WORKER_SHA${PROVER_SHA:+, prover image seal sha256 $PROVER_SHA}${SEALED_SHA:+, sealed image seal sha256 $SEALED_SHA}, core image seal sha256 $CORE_SHA)"
