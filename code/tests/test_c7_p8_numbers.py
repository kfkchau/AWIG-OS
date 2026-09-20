# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-verification · machine register.
# Vocabulary is OS-architecture / benchmarking: the four published figures of design/50 §4 (rows appended
# per second under group commit; the enforcement carve-out's decision latency for one compiled rule; the
# verify-without-engine time and the Merkle localisation-proof SIZE; the memory floor of a chained append)
# MEASURED under two performers — the Linux carrier and gov-os's own core — the SAME acts, published side by
# side EACH WITH ITS BASIS. NON-GOAL: no offensive capability; this MEASURES and reproduces figures and
# checks that the published table is well formed. It changes no core (C7 P8, A6: measurement only). The
# three plants are checks that CAN fail (L19). Full declaration: SCOPE-STATEMENT.md.
"""C7 P8 — THE FOUR NUMBERS, reproduced with their plants + the side-by-side table asserted present.

TWO ROLES, ONE MODULE (design/54 B9 — the same acts under two performers):
  * `TestBodyMeasure` MEASURES #1/#2/#3 with a small, body-safe N, prints one `P8FIG ...` marker per
    figure to stdout (which is the body's serial line under LEDGER mode), and asserts each figure is sane.
    It runs on BOTH performers unchanged: on the Linux carrier as an ordinary unittest, and on gov-os's own
    core when the body-hosted interpreter runs it via LEDGER mode (GOVOS_RUNMOD). Because it is the SAME
    code, the seam act set it exercises is IDENTICAL by construction — B9's check made mechanical below.
  * `TestPlantsTableFence` is the HOST-side acceptance: the three plants (each shown able to fail on
    planted-bad data), the side-by-side table asserted present with BOTH runs in evidence, and A6 (no core
    move: ACT_KINDS 12, ATTESTED 88). It reads the evidence the tools/bench drivers produce; it SKIPS where
    that evidence is absent (so it never reds on the body, whose runmod is TestBodyMeasure alone).

The measurement FUNCTIONS are shared: tools/bench/bench_linux.py imports them for the production-N Linux
run; TestBodyMeasure calls them with a small N. tools/bench/bench_body.py drives the body run and the #4
freestanding memory sweep over SSH (one nested boot at a time).
"""

import json
import os
import platform
import resource
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bridge import host_seam                                   # noqa: E402
from bridge.host_seam import HostSeam, using, ACT_KINDS        # noqa: E402
from bridge import checkpoint, merkle, replay_snapshot         # noqa: E402
from kernel.store import EventStore                            # noqa: E402
from kernel.compose import build_full_kernel                   # noqa: E402


# ---------------------------------------------------------------------------------------------------
# The identical-act-set instrument (design/54 B9): a performer that RECORDS the act KIND of every
# crossing and delegates to the real one. It wraps whatever performer is beneath the seam — RealHost
# on the Linux carrier, and the same RealHost on the body (whose file/clock/entropy syscalls are served
# by gov-os's own core). Because the measured code is identical, the recorded kind-set is identical by
# construction, which is exactly what B9 asks us to put in evidence — and a plant that crosses a
# different act changes the set, so the check CAN fail.
# ---------------------------------------------------------------------------------------------------
class ActRecorder(HostSeam):
    """Wrap a performer; record the act kind of every crossing; delegate the call unchanged."""

    def __init__(self, inner):
        self._inner = inner
        self.kinds = set()
        self.calls = []          # ordered (method, kind), for the evidence trail


def _install_recorder_methods():
    for _method, (_kind, _label) in HostSeam.ACTS.items():
        def _make(m, k):
            def _f(self, *a, **kw):
                self.kinds.add(k)
                self.calls.append((m, k))
                return getattr(self._inner, m)(*a, **kw)
            return _f
        setattr(ActRecorder, _method, _make(_method, _kind))


_install_recorder_methods()


def _record_manifest(do):
    """Run `do()` beneath an ActRecorder and return the sorted set of act kinds it crossed. A SEPARATE
    pass from the timed one, so recording overhead never distorts a figure."""
    inner = host_seam.host()
    rec = ActRecorder(inner)
    with using(rec):
        do()
    return sorted(rec.kinds)


def performer():
    """Which performer this process is: 'body' when the body-hosted interpreter runs us (its sys.path is
    seeded with /rec, /rec/src, /rec/tests by enclosure.c), else 'linux' — the Linux carrier."""
    for p in sys.path:
        if p == "/rec" or p.startswith("/rec/"):
            return "body"
    return "linux"


def machine_basis():
    """The machine half of every figure's basis — stated, never assumed. os.uname is NOT among the
    fifty syscalls gov-os's core serves (P3b-4s), so platform.uname()/machine() raise ENOSYS on the
    body; the body reports what it can (it is x86_64 long mode, L18) and names the reason."""
    try:
        uname = " ".join(platform.uname())
        machine = platform.machine()
    except OSError:
        uname = "gov-os body (nested qemu; os.uname not served by the core)"
        machine = "x86_64"          # the body runs in the machine's long mode (design/54 L18)
    return {
        "performer": performer(),
        "uname": uname,
        "machine": machine,
        "python": platform.python_version(),
    }


def _getrusage_self():
    """getrusage is not among the core's served syscalls, so it raises ENOSYS on the body. Returns the
    rusage or None; callers fall back to wall time / omit RSS on the body."""
    try:
        return resource.getrusage(resource.RUSAGE_SELF)
    except OSError:
        return None


def _figure(name, value, unit, basis, manifest, **extra):
    """One published figure, always carrying ITS BASIS and ITS ACT MANIFEST (B9)."""
    out = {"figure": name, "performer": performer(), "value": value, "unit": unit,
           "basis": basis, "manifest": list(manifest)}
    out.update(extra)
    return out


def emit(fig):
    """Print one figure as a single-line marker for the body serial / the host capturer to parse."""
    sys.stdout.write("P8FIG " + json.dumps(fig, sort_keys=True) + "\n")
    sys.stdout.flush()


# ---------------------------------------------------------------------------------------------------
# The four measurement functions (design/50 §4). Each returns a figure dict with its basis and the
# act manifest it crossed. N is a parameter: TestBodyMeasure uses a small N; bench_linux a production N.
# ---------------------------------------------------------------------------------------------------
BENCH_ROW = {"actor": "BODY", "action": "bench-append", "object": "row"}


def measure_rows_per_sec(n):
    """#1 — rows appended per second, one pen, the group-commit path (store._append -> the commit window
    -> the record pen -> one covering barrier). Batch shape: width 1 (one caller, one barrier per row,
    the group-commit floor). Timed with the monotonic clock; the manifest is recorded in a separate pass
    over 3 rows so timing stays clean."""
    d = tempfile.mkdtemp(prefix="p8_fig1_")
    rec = os.path.join(d, "record.jsonl")
    store = EventStore(rec, require_rule_cited=False)
    # a stable row size, stated as basis
    row_bytes = len(json.dumps(dict(BENCH_ROW, object="o0")).encode())
    t0 = time.perf_counter()
    for i in range(n):
        store._append({"actor": "BODY", "action": "bench-append", "object": "o%d" % i})
    dt = time.perf_counter() - t0
    rate = n / dt if dt > 0 else 0.0

    def _mani():
        d2 = tempfile.mkdtemp(prefix="p8_fig1m_")
        s2 = EventStore(os.path.join(d2, "record.jsonl"), require_rule_cited=False)
        for i in range(3):
            s2._append({"actor": "BODY", "action": "bench-append", "object": "o%d" % i})
    manifest = _record_manifest(_mani)
    basis = dict(machine_basis(), pen="one", batch_shape="width 1 (one caller, one covering barrier per row)",
                 row_bytes=row_bytes, n_rows=n, elapsed_s=round(dt, 6), clock="time.perf_counter (monotonic)")
    return _figure("rows_per_sec", round(rate, 3), "rows/sec", basis, manifest)


def measure_decide_latency(reps):
    """#2 — decision latency of the enforcement carve-out for ONE COMPILED RULE. One active structural
    don't (a '-' polarity recorded rule with a real `when`) is installed; the carve-out (gate._full_form_pass,
    the executable-law pass, step 6 of the decide pipeline) is timed evaluating one act against that one
    rule. Pure in-memory evaluation (no append) — the OPA-comparable policy-eval latency. The manifest is
    the seam acts the carve-out crosses (none: the decision reads folds, not the host)."""
    d = tempfile.mkdtemp(prefix="p8_fig2_")
    rec = os.path.join(d, "record.jsonl")
    store, gate, views, blobs, subs = build_full_kernel(
        rec, os.path.join(d, "blobs"), os.path.join(d, "vault"))
    gate.execute("CREATE-RULE", "owner", {"rule_id": "BENCH-DONT", "polarity": "-",
                 "text": "bench refuses", "when": [{"action": "NONMATCH-ACT"}],
                 "then": [{"refuse": "BENCH-DONT"}]})
    one = {k: v for k, v in views.active_rules().items() if v.get("rule_id") == "BENCH-DONT"}
    assert len(one) == 1, "exactly one compiled rule under test, found %d" % len(one)
    draft = {"actor": "someone", "action": "some-act", "object": "x", "payload": {}}
    # warm
    for _ in range(50):
        gate._full_form_pass("someone", "some-act", draft, rules=one)
    t0 = time.perf_counter()
    for _ in range(reps):
        gate._full_form_pass("someone", "some-act", draft, rules=one)
    dt = time.perf_counter() - t0
    per = dt / reps * 1e6 if reps else 0.0
    manifest = _record_manifest(lambda: gate._full_form_pass("someone", "some-act", draft, rules=one))
    basis = dict(machine_basis(), rules_active=1,
                 carve_out="gate._full_form_pass (the executable-law enforcement pass, one compiled rule)",
                 reps=reps, total_s=round(dt, 6), append="none (pure decision)",
                 clock="time.perf_counter (monotonic)")
    return _figure("decide_latency_us", round(per, 4), "microseconds/decision", basis, manifest)


def _small_tree(gate):
    """Three files at the record root — a real, fixed tree shape whose inclusion proof size is
    size- and engine-independent (the cross-performer figure of record)."""
    for nm, body in (("a.txt", "hello world"), ("c.txt", "second file"), ("e.txt", "third here")):
        gate.execute("FILE-CREATE", "owner", {"path": "/" + nm})
        gate.execute("FILE-WRITE", "owner", {"path": "/" + nm, "content": body})


def measure_verify_and_proof(n):
    """#3 — verify-without-engine time for an N-row record + the SIZE of a Merkle localisation proof.
    A fixed 3-leaf tree is written for the proof; then N rows are appended (the record the air rider
    re-reads and re-folds with no engine). `checkpoint.verify` reads the record and the blobs ALONE,
    recomputes the tree, the chain head, the founding-pack sha and the attestation head. The inclusion
    proof for one leaf is produced and its byte size recorded — size- and engine-independent, the
    cross-performer figure. On the body N is a SCOPED count within the 8 MiB record cap; the full
    1,000,000-row verify runs under Linux only (1M rows ~450 MB >> the body's 8 MiB record, disk.h /
    mkdisk.py:56 — never run on the body, stop (b))."""
    d = tempfile.mkdtemp(prefix="p8_fig3_")
    rec = os.path.join(d, "record.jsonl")
    bd = os.path.join(d, "blobs")
    store, gate, views, blobs, subs = build_full_kernel(rec, bd, os.path.join(d, "vault"))
    _small_tree(gate)
    base = len(store.all())
    for i in range(n):
        store._append({"actor": "BODY", "action": "bench-append", "object": "o%d" % i,
                       "rule_cited": "bench"})
    total_rows = len(store.all())
    cp = checkpoint.create(store, rec, bd, root="/")
    ru0 = _getrusage_self()
    t0 = time.perf_counter()
    ver = checkpoint.verify(cp, rec, bd)
    wall = time.perf_counter() - t0
    if ru0 is not None:
        ru1 = _getrusage_self()
        cpu = (ru1.ru_utime - ru0.ru_utime) + (ru1.ru_stime - ru0.ru_stime)
        cpu_from = "getrusage(RUSAGE_SELF)"
    else:
        cpu = wall                    # getrusage not served on the body -> wall is the time figure
        cpu_from = "wall (getrusage not served by the core)"
    assert ver.get("ok") is True, "verify must be green: %r" % (ver,)
    tree = replay_snapshot.snapshot(rec, bd, root="/")
    root = merkle.merkle_root(tree)
    proof = merkle.inclusion_proof(tree, "a.txt")
    assert proof is not None, "the inclusion proof for a.txt must exist"
    proof_bytes = len(json.dumps(proof, sort_keys=True).encode())
    proof_ok = merkle.verify_inclusion(proof, root)
    assert proof_ok is True, "the inclusion proof must verify against the root"
    basis = dict(machine_basis(), n_rows=total_rows, appended_rows=n, tree_leaves=len(tree),
                 verify="bridge.checkpoint.verify (read record+blobs, re-fold tree, chain head, "
                        "founding-pack sha, attestation head; no engine)",
                 proof="bridge.merkle.inclusion_proof (audit path, one leaf), verify_inclusion True",
                 cpu_from=cpu_from, clock="time.perf_counter (wall) + %s" % cpu_from)
    return _figure("verify_and_proof", round(cpu, 4), "cpu_seconds",
                   basis, verify_manifest(), verify_wall_s=round(wall, 4), verify_cpu_s=round(cpu, 4),
                   localisation_proof_bytes=proof_bytes, proof_verifies=proof_ok, rows=total_rows)


# The verify/proof act manifest is captured once (verify+proof read files through the seam). Recording
# around the full verify would double a heavy run, so it is captured over a tiny record with the SAME
# acts (build kernel + small tree + a few rows + verify + proof).
def _capture_verify_manifest():
    def _do():
        d = tempfile.mkdtemp(prefix="p8_fig3m_")
        rec = os.path.join(d, "record.jsonl")
        bd = os.path.join(d, "blobs")
        store, gate, views, blobs, subs = build_full_kernel(rec, bd, os.path.join(d, "vault"))
        _small_tree(gate)
        for i in range(3):
            store._append({"actor": "BODY", "action": "bench-append", "object": "o%d" % i,
                           "rule_cited": "bench"})
        cp = checkpoint.create(store, rec, bd, root="/")
        checkpoint.verify(cp, rec, bd)
        tree = replay_snapshot.snapshot(rec, bd, root="/")
        merkle.inclusion_proof(tree, "a.txt")
    return _record_manifest(_do)


_MANIFEST_VERIFY = None            # filled lazily; see TestBodyMeasure / bench


def verify_manifest():
    global _MANIFEST_VERIFY
    if _MANIFEST_VERIFY is None:
        _MANIFEST_VERIFY = _capture_verify_manifest()
    return _MANIFEST_VERIFY


def measure_chained_append_floor_linux(n):
    """#4 (Linux side) — the Linux carrier has NO boot-RAM floor (demand-paged virtual memory: there is
    no fixed RAM at which the process is denied a boot). So the boot-RAM sweep the body runs is NOT
    mechanical here; the Linux datapoint is the PEAK RSS of a chained append of n rows into the append-only
    record (each row chained by the store), with its basis. The body side brackets the real floor by boot."""
    d = tempfile.mkdtemp(prefix="p8_fig4_")
    rec = os.path.join(d, "record.jsonl")
    store = EventStore(rec, require_rule_cited=False)
    ru0 = resource.getrusage(resource.RUSAGE_SELF)
    for i in range(n):
        store._append({"actor": "BODY", "action": "bench-append", "object": "o%d" % i})
    ru1 = resource.getrusage(resource.RUSAGE_SELF)
    rss_mb = ru1.ru_maxrss // 1024
    basis = dict(machine_basis(), n_rows=n, workload="chained append into the append-only record "
                 "(each row chained by the store); one pen",
                 mechanism="no boot-RAM floor on Linux (demand-paged virtual memory) — RSS baseline, "
                           "not a sweep", metric="peak RSS via getrusage(RUSAGE_SELF)")
    return _figure("memory_floor", rss_mb, "peak_rss_MB (baseline, not a boot floor)", basis,
                   _record_manifest(lambda: EventStore(
                       os.path.join(tempfile.mkdtemp(prefix="p8_fig4m_"), "r.jsonl"),
                       require_rule_cited=False)._append(dict(BENCH_ROW, object="o0"))))


# ---------------------------------------------------------------------------------------------------
# THE THREE PLANTS — each a check that CAN fail (design/54 L19). They are pure functions; the tests
# below run each on GOOD data (the check passes) and on PLANTED-BAD data (the check reds).
# ---------------------------------------------------------------------------------------------------
def check_identical_act_sets(linux_manifest, body_manifest):
    """B9's check: the two performers' act sets are IDENTICAL where both run a figure. Returns True iff
    the two manifests are the same set. A differing set (a plant that crosses an extra/missing act) reds."""
    return sorted(set(linux_manifest)) == sorted(set(body_manifest))


def check_floor_bracketed(sweep):
    """#4's check: the memory floor is BRACKETED by a REAL red boot and a real green boot, the red being
    one grid step below the smallest green (L19 — the bracket is real, never an un-bracketed floor).
    `sweep` is a list of {mib, green: bool}. Returns True iff there is >=1 green and >=1 red, and the
    largest red sits exactly one grid step below the smallest green."""
    greens = sorted(s["mib"] for s in sweep if s.get("green"))
    reds = sorted(s["mib"] for s in sweep if not s.get("green"))
    if not greens or not reds:
        return False                       # an un-bracketed floor (only green, or only red) reds
    smallest_green = greens[0]
    below = [m for m in (s["mib"] for s in sweep) if m < smallest_green]
    if not below:
        return False                       # nothing below the smallest green — floor not bracketed
    step_below = max(below)
    return (step_below in reds)            # the step immediately below the smallest green must be RED


def check_basis_present(figure):
    """Every published figure carries ITS BASIS: a non-empty basis mapping naming the machine/performer
    and the figure-specific parameters. A figure without its basis reds."""
    b = figure.get("basis")
    if not isinstance(b, dict) or not b:
        return False
    required = ("performer", "machine")
    return all(b.get(k) for k in required)


# ---------------------------------------------------------------------------------------------------
# THE TABLE — assembled from both performers' figures, each WITH ITS BASIS, identical acts where both run.
# ---------------------------------------------------------------------------------------------------
CROSS_PERFORMER_FIGURES = ("rows_per_sec", "decide_latency_us")   # #1, #2 run on both, same acts


def build_side_by_side(linux_figs, body_figs):
    """Return the side-by-side table structure: per figure, both performers' value+basis, and (where both
    run) the identical-act-set verdict. Raises if a figure lacks its basis (basis-present) or if a
    cross-performer pair's act sets differ (identical-act-set)."""
    by_name_l = {f["figure"]: f for f in linux_figs}
    by_name_b = {f["figure"]: f for f in body_figs}
    rows = []
    for name in sorted(set(by_name_l) | set(by_name_b)):
        l = by_name_l.get(name)
        b = by_name_b.get(name)
        for f in (l, b):
            if f is not None and not check_basis_present(f):
                raise AssertionError("figure %r published without its basis: %r" % (name, f))
        row = {"figure": name, "linux": l, "body": b}
        if l is not None and b is not None:
            row["act_sets_identical"] = check_identical_act_sets(l["manifest"], b["manifest"])
            if name in CROSS_PERFORMER_FIGURES and not row["act_sets_identical"]:
                raise AssertionError("cross-performer figure %r has differing act sets: linux=%r body=%r"
                                     % (name, l["manifest"], b["manifest"]))
        rows.append(row)
    return {"rows": rows,
            "note": "the four figures of design/50 §4 under two performers (design/54 B9); #1/#2 green on "
                    "both with identical acts; #3 the 1M verify under Linux only, a body scoped-N with the "
                    "identical acts, the localisation-proof SIZE the cross-performer figure; #4 the body's "
                    "memory floor bracketed by a bounded sweep, the Linux side a baseline."}


# ---------------------------------------------------------------------------------------------------
EVID = os.path.join(os.path.dirname(__file__), "..", "planning", "evidence", "C7-P8-NUMBERS-AND-REVIEW")


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class TestBodyMeasure(unittest.TestCase):
    """MEASURES #1/#2/#3 with a small, body-safe N and EMITS one marker per figure. This is the class the
    body-hosted interpreter runs (GOVOS_RUNMOD=test_c7_p8_numbers.TestBodyMeasure); it runs on the Linux
    carrier too (the same code -> identical acts). Small N so it finishes within a boot, and N is stated in
    the basis. The body scoped-N is far within the 8 MiB record cap; the 1M verify is Linux-only."""

    BODY_N1 = 200        # #1 appends
    BODY_N2 = 2000       # #2 decide reps
    BODY_N3 = 500        # #3 scoped rows (well within the 8 MiB / ~18k-row record cap)

    def test_1_rows_per_sec(self):
        fig = measure_rows_per_sec(self.BODY_N1)
        emit(fig)
        self.assertGreater(fig["value"], 0.0, "rows/sec must be positive")
        self.assertTrue(check_basis_present(fig), "figure #1 must carry its basis")
        self.assertIn("record-pen", fig["manifest"], "#1 must cross the record pen")
        self.assertIn("commit-window", fig["manifest"], "#1 must cross the commit window")

    def test_2_decide_latency(self):
        fig = measure_decide_latency(self.BODY_N2)
        emit(fig)
        self.assertGreater(fig["value"], 0.0, "decide latency must be positive")
        self.assertTrue(check_basis_present(fig), "figure #2 must carry its basis")
        self.assertEqual(fig["basis"]["rules_active"], 1, "exactly one compiled rule under test")

    def test_3_verify_and_proof(self):
        fig = dict(measure_verify_and_proof(self.BODY_N3))
        fig["manifest"] = verify_manifest()
        emit(fig)
        self.assertTrue(fig["proof_verifies"], "the inclusion proof must verify")
        self.assertGreater(fig["localisation_proof_bytes"], 0, "proof size must be positive")
        self.assertTrue(check_basis_present(fig), "figure #3 must carry its basis")
        self.assertLess(self.BODY_N3 * 500, 8 * 1024 * 1024,
                        "the body scoped-N must sit within the 8 MiB record cap")


class TestPlants(unittest.TestCase):
    """The three plants: each check is exercised on GOOD data (passes) and on PLANTED-BAD data (reds).
    Pure functions, so this runs anywhere; it is the mechanical proof the B9 / L19 checks CAN fail."""

    def test_identical_act_set_accepts_equal(self):
        self.assertTrue(check_identical_act_sets(["commit-window", "record-pen"],
                                                 ["record-pen", "commit-window"]))

    def test_identical_act_set_rejects_differing(self):
        # PLANT: the body run crosses an extra act (entropy) the Linux run did not -> the sets differ.
        self.assertFalse(check_identical_act_sets(["commit-window", "record-pen"],
                                                  ["commit-window", "record-pen", "entropy"]),
                         "a differing act set must red (B9)")

    def test_floor_bracketed_accepts_real_bracket(self):
        sweep = [{"mib": 32, "green": True}, {"mib": 24, "green": False}, {"mib": 16, "green": False}]
        self.assertTrue(check_floor_bracketed(sweep), "a real red+green bracket passes")

    def test_floor_bracketed_rejects_unbracketed(self):
        # PLANT: only green boots, no red bracket -> an un-bracketed floor reds (L19).
        sweep = [{"mib": 256, "green": True}, {"mib": 128, "green": True}, {"mib": 64, "green": True}]
        self.assertFalse(check_floor_bracketed(sweep), "an un-bracketed floor must red (L19)")

    def test_floor_bracketed_rejects_all_red(self):
        # PLANT: the append never ran at any tested size (no green boot) -> not a real bracket (L19).
        sweep = [{"mib": 32, "green": False}, {"mib": 16, "green": False}, {"mib": 8, "green": False}]
        self.assertFalse(check_floor_bracketed(sweep), "an all-red sweep (no green boot) must red")

    def test_floor_bracketed_needs_step_below_smallest_green(self):
        # the grid step immediately below the smallest green must itself be RED; a bracket where the
        # smallest green is the lowest point tested (nothing below it) is not a real floor bracket.
        sweep = [{"mib": 64, "green": True}, {"mib": 48, "green": True}]
        self.assertFalse(check_floor_bracketed(sweep),
                         "greens with no red below the smallest is an un-bracketed floor")

    def test_basis_present_accepts_full_basis(self):
        self.assertTrue(check_basis_present({"basis": {"performer": "linux", "machine": "x86_64"}}))

    def test_basis_present_rejects_missing_basis(self):
        # PLANT: a figure published without its basis reds.
        self.assertFalse(check_basis_present({"basis": {}}), "an empty basis must red")
        self.assertFalse(check_basis_present({"value": 1.0}), "a missing basis must red")


class TestSideBySideTableAndFence(unittest.TestCase):
    """The HOST-side acceptance: the side-by-side table is present with BOTH runs in evidence, each figure
    carries its basis, the cross-performer act sets are identical, and A6 holds (no core move). SKIPS when
    the evidence is absent (the body run's runmod is TestBodyMeasure alone, so this never reds on the body)."""

    def _need(self, path):
        if not os.path.exists(path):
            self.skipTest("SKIP BODY-BOOT: evidence not built yet: %s (run tools/bench first)" % path)

    def test_table_present_with_both_runs(self):
        tpath = os.path.join(EVID, "SIDE-BY-SIDE-TABLE.json")
        self._need(tpath)
        table = _load_json(tpath)
        rows = {r["figure"]: r for r in table["rows"]}
        for name in ("rows_per_sec", "decide_latency_us", "verify_and_proof", "memory_floor"):
            self.assertIn(name, rows, "the table must publish figure %r" % name)
        # #1 and #2 are on BOTH performers with identical acts
        for name in CROSS_PERFORMER_FIGURES:
            r = rows[name]
            self.assertIsNotNone(r.get("linux"), "%s missing the Linux run" % name)
            self.assertIsNotNone(r.get("body"), "%s missing the body run" % name)
            self.assertTrue(r.get("act_sets_identical"), "%s act sets must be identical (B9)" % name)

    def test_every_figure_carries_its_basis(self):
        tpath = os.path.join(EVID, "SIDE-BY-SIDE-TABLE.json")
        self._need(tpath)
        table = _load_json(tpath)
        for r in table["rows"]:
            for perf in ("linux", "body"):
                f = r.get(perf)
                if f is not None:
                    self.assertTrue(check_basis_present(f),
                                    "figure %r (%s) must carry its basis" % (r["figure"], perf))

    def test_3_1M_linux_and_body_scoped_N_and_proof_size(self):
        lpath = os.path.join(EVID, "linux", "verify_and_proof.json")
        bpath = os.path.join(EVID, "body", "verify_and_proof.json")
        self._need(lpath)
        self._need(bpath)
        lin = _load_json(lpath)
        bod = _load_json(bpath)
        self.assertGreaterEqual(lin["basis"]["n_rows"], 1000000,
                                "the Linux #3 verify is over the FULL one-million-row record")
        self.assertLess(bod["basis"]["n_rows"], 1000000,
                        "the body #3 is a SCOPED N, never presented as the 1M's equal")
        self.assertLessEqual(bod["basis"]["n_rows"] * 500, 8 * 1024 * 1024,
                             "the body scoped-N sits within the 8 MiB record cap")
        # the localisation-proof SIZE is the cross-performer figure (size- and engine-independent)
        self.assertEqual(lin["localisation_proof_bytes"], bod["localisation_proof_bytes"],
                         "the proof SIZE is the cross-performer figure — equal on both performers")

    def test_4_floor_bracketed_on_body(self):
        spath = os.path.join(EVID, "body", "memory_sweep.json")
        self._need(spath)
        sweep = _load_json(spath)
        self.assertTrue(check_floor_bracketed(sweep["grid"]),
                        "the body memory floor must be bracketed by a real red and green boot (L19)")

    def test_A6_no_core_move(self):
        # ACT_KINDS stays 12; the attested member set stays 88 — measurement only, no founding/core edit.
        self.assertEqual(len(ACT_KINDS), 12, "ACT_KINDS must stay 12 (A6)")
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertEqual(len(ATTESTED_MEMBERS), 88, "ATTESTED must stay 88 (A6)")


if __name__ == "__main__":
    unittest.main()
