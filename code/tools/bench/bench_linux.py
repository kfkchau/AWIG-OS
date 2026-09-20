# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-tooling · machine register.
# The Linux-carrier arm of the C7 P8 four-number benchmark. Drives the acts that already exist and reads
# the figures out; changes no core (A6, measurement only). #3's full 1,000,000-row verify runs HERE and
# only here (the body's 8 MiB record cannot hold 1M — the body runs a scoped N). Full declaration:
# SCOPE-STATEMENT.md.
"""Measure the four figures on the Linux carrier and write them to planning/evidence/.../linux/.

Usage:
    python3 tools/bench/bench_linux.py fast          # #1, #2, #4 (seconds)
    python3 tools/bench/bench_linux.py verify1m      # #3 the FULL 1M verify (minutes; memory-heavy)
    python3 tools/bench/bench_linux.py all           # everything

#3 the 1M verify is memory-heavy as BUILT (bridge.checkpoint.verify reads the whole record and re-folds
it — the trial-balance-style "verify without the vendor"), so the record is BUILT memory-efficiently here
(bulk file write, no live 1M-event store) and only the verify is measured. The figure OF RECORD is the CPU
time (swap-insensitive) plus the localisation-proof SIZE; wall time and peak RSS are reported beside it.
"""

import gc
import json
import os
import resource
import sys
import tempfile
import time

import measure_common as mc
import test_c7_p8_numbers as p8

from bridge import host_seam
from bridge.host_seam import RealHost, using
from bridge import checkpoint, merkle, replay_snapshot
from bridge.checkpoint import canonical_hash, founding_pack_sha_of, ATTESTATION_ACTION
from kernel.compose import build_full_kernel


N1 = 5000          # #1 append rows (each with a covering barrier)
REPS2 = 50000      # #2 decide reps (pure CPU)
N3_1M = 1_000_000  # #3 the FULL one-million-row record (Linux only)
N4 = 5000          # #4 chained-append RSS baseline


class _NoSync(RealHost):
    """A setup-only performer that skips the durability barrier so BUILDING the 1M-row record is not a
    million disk syncs. Only the record BYTES matter to verify (a same-process read sees the flushed
    buffer); the barrier is durability, irrelevant to the verify time being measured. NOT used for any
    figure — only to build the record #3 verifies."""
    def fdatasync(self, fd):
        return None

    def fsync_dir(self, dirpath):
        return None


def _build_million_row_record(n, d):
    """Found a small real kernel (founding + attestation + a fixed 3-leaf tree), then bulk-append n-few
    synthetic rows straight to the record file (append-only, no live event store held). Returns the
    record path, blob dir, and the total row count."""
    rec = os.path.join(d, "record.jsonl")
    bd = os.path.join(d, "blobs")
    with using(_NoSync()):
        store, gate, views, blobs, subs = build_full_kernel(rec, bd, os.path.join(d, "vault"))
        p8._small_tree(gate)
        base = len(store.all())
    del store, gate, views, blobs, subs
    gc.collect()
    seq = base
    with open(rec, "a", encoding="utf-8") as f:
        buf = []
        for i in range(n):
            seq += 1
            row = {"record_id": "bench_%d" % seq, "seq": seq,
                   "record_time": "2026-09-19T00:00:00.000000+00:00",
                   "submission_time": "2026-09-19T00:00:00.000000+00:00",
                   "occurrence_time": "2026-09-19T00:00:00.000000+00:00",
                   "origin": {"subsystem_id": "kernel", "built_id": 0},
                   "actor": "BODY", "action": "bench-append", "object": "o%d" % i,
                   "target": None, "rule_cited": "bench", "evidence_summary": None,
                   "provenance": {"asserted_by": "BODY", "source": "system", "could_read": []},
                   "content_form": "inline", "refs": [], "payload": {}}
            buf.append(json.dumps(row))
            if len(buf) >= 20000:
                f.write("\n".join(buf) + "\n")
                buf = []
        if buf:
            f.write("\n".join(buf) + "\n")
    return rec, bd, base + n


def _manual_checkpoint(rec, bd):
    """Build the checkpoint without a live 1M-event store: tree via snapshot, chain head from the last
    record line, attestation head via a streaming scan, founding-pack sha from the pack."""
    tree = replay_snapshot.snapshot(rec, bd, root="/")
    with open(rec, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - 8192))
        last_line = f.read().decode(errors="replace").strip().splitlines()[-1]
    last = json.loads(last_line)
    att = None
    with open(rec, encoding="utf-8") as f:
        for ln in f:
            if not ln.strip():
                continue
            r = json.loads(ln)
            if r.get("action") == ATTESTATION_ACTION:
                att = r
    return {"kind": "checkpoint", "scope": {"row_id": None, "root": "/"}, "tree": tree,
            "provenance": {"chain_head": canonical_hash(last),
                           "founding_pack_sha": founding_pack_sha_of(),
                           "attestation_head": canonical_hash(att) if att is not None else None}}


def measure_verify_1m(n=N3_1M):
    d = tempfile.mkdtemp(prefix="p8_1m_")
    t_build = time.perf_counter()
    rec, bd, rows = _build_million_row_record(n, d)
    build_s = time.perf_counter() - t_build
    cp = _manual_checkpoint(rec, bd)
    gc.collect()
    ru0 = resource.getrusage(resource.RUSAGE_SELF)
    t0 = time.perf_counter()
    ver = checkpoint.verify(cp, rec, bd)
    wall = time.perf_counter() - t0
    ru1 = resource.getrusage(resource.RUSAGE_SELF)
    cpu = (ru1.ru_utime - ru0.ru_utime) + (ru1.ru_stime - ru0.ru_stime)
    rss_mb = ru1.ru_maxrss // 1024
    majflt = ru1.ru_majflt - ru0.ru_majflt
    assert ver.get("ok") is True, "1M verify must be green: %r" % (ver,)
    tree = replay_snapshot.snapshot(rec, bd, root="/")
    root = merkle.merkle_root(tree)
    proof = merkle.inclusion_proof(tree, "a.txt")
    proof_bytes = len(json.dumps(proof, sort_keys=True).encode())
    proof_ok = merkle.verify_inclusion(proof, root)
    basis = dict(p8.machine_basis(), n_rows=rows, appended_rows=n, tree_leaves=len(tree),
                 verify="bridge.checkpoint.verify (read record+blobs, re-fold tree, chain head, "
                        "founding-pack sha, attestation head; no engine)",
                 proof="bridge.merkle.inclusion_proof (audit path, one leaf), verify_inclusion True",
                 build_s=round(build_s, 2), record_bytes=os.path.getsize(rec),
                 note="the figure OF RECORD is CPU time (swap-insensitive) + the proof SIZE; wall/RSS "
                      "reported beside it. verify-without-engine is a full record re-fold, super-linear "
                      "at scale (a measured characteristic).",
                 clock="time.perf_counter (wall) + getrusage (cpu/rss/majflt)")
    fig = p8._figure("verify_and_proof", round(cpu, 4), "cpu_seconds", basis, p8.verify_manifest(),
                     verify_wall_s=round(wall, 3), verify_cpu_s=round(cpu, 4),
                     peak_rss_mb=rss_mb, major_faults=majflt,
                     localisation_proof_bytes=proof_bytes, proof_verifies=proof_ok, rows=rows)
    return fig


def run_fast():
    figs = {
        "rows_per_sec": p8.measure_rows_per_sec(N1),
        "decide_latency_us": p8.measure_decide_latency(REPS2),
        "memory_floor": p8.measure_chained_append_floor_linux(N4),
    }
    for name, fig in figs.items():
        path = mc.write_json(os.path.join(mc.EVID_LINUX, "%s.json" % name), fig)
        print("wrote", path, "value=", fig["value"], fig["unit"])
    return figs


def run_verify1m():
    fig = measure_verify_1m(N3_1M)
    path = mc.write_json(os.path.join(mc.EVID_LINUX, "verify_and_proof.json"), fig)
    print("wrote", path, "cpu_s=", fig["verify_cpu_s"], "wall_s=", fig["verify_wall_s"],
          "rss_mb=", fig["peak_rss_mb"], "proof_bytes=", fig["localisation_proof_bytes"],
          "rows=", fig["rows"])
    return fig


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("fast", "all"):
        run_fast()
    if what in ("verify1m", "all"):
        run_verify1m()
    print("DONE", what)
