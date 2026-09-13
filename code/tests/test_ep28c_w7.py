"""EP-28C W7, SUITE-SIDE ARM — the store benchmark, and the measurement DESIGN as rows.

WHAT IS HERE AND WHAT IS NOT. W7 has two halves. The CONTENDED half — N concurrent writer
processes against the mount in the guest — is BLOCKED behind W4e (AMENDMENT 8 §8.1), and
W4e stopped on its own clause (`tests/test_ep28c_w4e.py`). **The suite-side store benchmark
is stated READY AND UNBLOCKED at AMENDMENT 8 §8.1 and it is what this file takes**, because
its subject is the STORE's barrier amortisation, which needs many submitters in one process
and not many callers through a channel.

THE HEADLINE IS A COUNTABLE AND THE DURATION RIDES BESIDE IT. `design/36` ADDENDUM L §L.5,
as amended 2026-07-31: countables are unaffected by the host's memory condition, comparative
conclusions survive when both arms are taken in one session under one condition, and
ABSOLUTE DURATIONS from a pressured window carry a condition they do not state. This host is
under memory pressure at this writing, measured and recorded beside the figures. So the
load-bearing number is **syncs per record** — `batches / members`, which is what group
commit actually changes and what no amount of paging can move — and the durations are
reported with their spread and their substrate, never as the claim.

**[CORRECTED IN PLACE 2026-08-03, BY THIS FILE'S OWN FIRST RUN, and the paragraph above
stands because the record of what was believed is part of the record.] `syncs_per_record`
COUNTS BARRIER CALLS AND NOT BARRIER WORK, and the two do not move together under
concurrency.** The mechanism: `fdatasync` is cumulative, so with many publishers in flight a
width-1 barrier already finds most of the file's dirty data flushed by its neighbours'
barriers and is cheap, while a barrier covering a whole batch must flush all of it and costs
proportionally more. Fewer barriers are therefore not proportionally less barrier.
**A countable chosen as a proxy for a cost is a proxy one step away from the quantity that
matters** — `design/36` ADDENDUM Q's own class ("name the DEPENDENCY, never a variable")
arriving in a measurement instrument. The corrected headline is BARRIER MILLISECONDS PER
RECORD, taken directly by `barrier_arm`, still comparative and still taken in one session
under one condition. The relation between the two ratios is asserted by
`test_the_CALL_countable_and_the_COST_it_stands_for_do_not_move_together`; **the figures
themselves live in `planning/build/MEASUREMENTS.md` and not in this docstring, because a
number written into a description is a number that will be wrong later.**

**CONSEQUENCE FOR THE BLOCKED CONTENDED ARM, stated here because it is where it will be
read:** W7's guest-side arm must report barrier COST per record. Reporting barrier CALLS
per record would announce a lever roughly twice the size of the one that exists, in the
arc's headline deliverable — §A46's adjective wearing a countable's clothes.

THE FOUR MEASUREMENT RULES, BUILT IN RATHER THAN PROMISED:

  INTERLEAVED, NEVER SEQUENTIAL. `run_arms` rotates the widths within every repetition, so
  any drift over the run's own span lands on all three arms alike. A sequential comparison
  measures drift as if it were effect, and `test_RED_WORLD_*` drives exactly that: an
  injected monotone drift that the sequential design attributes to an arm and the
  interleaved design does not. That is the can-fail proof of the design itself.

  SPREAD BESIDE THE CENTRAL VALUE, NEVER A BARE MEDIAN. Every arm reports min, median, max
  and the spread, and `same_within_spread` is the estate's own rule made executable: a
  difference smaller than one arm's spread is not a difference.

  SUBSTRATE STATED. `substrate()` reads the box, the filesystem the record sits on, and the
  HOST's free memory and swap, per §L.5's amendment. It is taken at the run, not carried.

  TAKEN OR CARRIED, LABELLED. Every figure this file produces is TAKEN, and it says so.
  The 5.6x/13.5x band it is compared against is CARRIED from EP-28's W8 instrument, and the
  comparison says that too. §A46's extension: a figure carried is not a figure taken, and
  the seat whose function is confirmation can carry.

WHAT THE UNITTEST ROWS ASSERT is the DESIGN — that the arms interleave, that the spread is
reported, that the subject is non-empty, that the amortisation countable moves in the
direction the design predicts — on small samples, so the suite pays milliseconds. THE
FIGURES are taken by the declared invocation:

    python3 -m tests.test_ep28c_w7 --measure

which prints the table that goes into `planning/build/MEASUREMENTS.md` with its conditions.
"""

import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from kernel import store as store_mod                              # noqa: E402

#: The widths the order names. Data, so the enumeration is readable.
WIDTHS = (1, 8, 16)


# =====================================================================================
# the substrate, read rather than remembered
# =====================================================================================

def _utc_now():
    """A wall-clock anchor with MILLISECONDS, because whole seconds are not an anchor for a
    run that takes less than one — a report whose two anchors read identically cannot be
    checked against anything from inside itself, which is the whole reason anchors are
    required."""
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds")


def substrate(record_path):
    """The conditions this run's figures carry. §L.5, including the HOST's own memory."""
    out = {
        "box": platform.node(),
        "kernel": platform.release(),
        "python": platform.python_version(),
        "cpus": os.cpu_count(),
        "record_on": None,
        "mem_free_mb": None,
        "mem_available_mb": None,
        "swap_used_mb": None,
    }
    try:
        out["record_on"] = subprocess.run(
            ["df", "--output=fstype,source", os.path.dirname(record_path)],
            capture_output=True, text=True, timeout=10).stdout.strip().splitlines()[-1].strip()
    except Exception:                                              # noqa: BLE001
        pass
    try:
        with open("/proc/meminfo", encoding="utf-8") as fh:
            mi = {}
            for line in fh:
                k, _, v = line.partition(":")
                mi[k] = int(v.split()[0]) // 1024
        out["mem_free_mb"] = mi.get("MemFree")
        out["mem_available_mb"] = mi.get("MemAvailable")
        out["swap_used_mb"] = (mi.get("SwapTotal", 0) or 0) - (mi.get("SwapFree", 0) or 0)
    except Exception:                                              # noqa: BLE001
        pass
    return out


# =====================================================================================
# the instrument
# =====================================================================================

class Trial:
    """ONE trial: `n` submitters released together against a fresh store at one width."""

    def __init__(self, root, width, n, delay=0.0):
        self.width, self.n, self.delay = width, n, delay
        self.dir = tempfile.mkdtemp(prefix="w7-", dir=root)
        self.rec = os.path.join(self.dir, "rec.jsonl")

    def run(self):
        store = store_mod.EventStore(self.rec)
        store.group_commit.width = self.width
        errors = []
        gate = threading.Barrier(self.n, timeout=60)

        def one(i):
            try:
                gate.wait()
                store._append({"actor": "sub-%03d" % i, "action": "probe",
                               "rule_cited": "M1-OBSERVATION", "payload": {"i": i}})
            except BaseException as exc:                            # noqa: BLE001
                errors.append(exc)
                gate.abort()

        threads = [threading.Thread(target=one, args=(i,)) for i in range(self.n)]
        for t in threads:
            t.start()
        t0 = time.monotonic()
        # THE DRIFT INJECTION POINT, used only by the red world. A trial that is uniformly
        # slower stands in for any condition that changes over a run's span — a warming
        # cache, a host under growing pressure, another process arriving.
        if self.delay:
            time.sleep(self.delay)
        for t in threads:
            t.join(timeout=120)
        elapsed = time.monotonic() - t0
        for t in threads:
            assert not t.is_alive(), "a submitter never returned — the queue wedged"
        assert not errors, "trial raised: %r" % (errors[0],)
        gc = store.group_commit
        out = {
            "width": self.width,
            "n": self.n,
            "seconds": elapsed,
            "ms_per_record": (elapsed * 1000.0) / self.n,
            "records": len(store.all()),
            "batches": gc.batches,
            "members": gc.members,
            "largest_batch": gc.largest_batch,
            "syncs_per_record": gc.batches / float(gc.members) if gc.members else None,
        }
        store.close()
        shutil.rmtree(self.dir, ignore_errors=True)
        return out


def barrier_arm(root, width, n=32, reps=7):
    """One arm, timing EVERY barrier call so the amortisation can be read as WORK.

    The store's `_commit_batch` is wrapped, not replaced: the real barrier runs, and the
    only addition is a clock either side of it. What comes back is the per-call cost and
    the total barrier cost per record — the second being the figure that actually answers
    "what did batching buy"."""
    per_call, per_record, calls, members = [], [], 0, 0
    for _ in range(reps):
        d = tempfile.mkdtemp(dir=root)
        store = store_mod.EventStore(os.path.join(d, "rec.jsonl"))
        store.group_commit.width = width
        real = store._commit_batch
        taken = []

        def timed(batch, _real=real, _taken=taken):
            t0 = time.perf_counter()
            out = _real(batch)
            _taken.append((time.perf_counter() - t0) * 1000.0)
            return out

        store.group_commit._commit_batch = timed
        errors = []
        gate = threading.Barrier(n, timeout=60)

        def one(i):
            try:
                gate.wait()
                store._append({"actor": "s%03d" % i, "action": "probe",
                               "rule_cited": "M1-OBSERVATION", "payload": {"i": i}})
            except BaseException as exc:                            # noqa: BLE001
                errors.append(exc)
                gate.abort()

        threads = [threading.Thread(target=one, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=120)
        assert not errors, "barrier arm raised: %r" % (errors[0],)
        per_call.extend(taken)
        per_record.append(sum(taken) / float(n))
        calls += store.group_commit.batches
        members += store.group_commit.members
        store.close()
        shutil.rmtree(d, ignore_errors=True)
    return {
        "width": width,
        "barrier_calls": calls,
        "records": members,
        "calls_per_record": calls / float(members),
        "per_call_ms": {"median": statistics.median(per_call),
                        "min": min(per_call), "max": max(per_call),
                        "spread": max(per_call) - min(per_call)},
        "barrier_ms_per_record": {"median": statistics.median(per_record),
                                  "min": min(per_record), "max": max(per_record),
                                  "spread": max(per_record) - min(per_record)},
    }


def readable_median(arm, key):
    """An arm's median READ rather than assumed: the finite float, or None when the arm
    produced no reading at all.

    WHY THIS EXISTS AS A SEPARATE READ. The CALL-vs-COST row below stopped gating the build
    on its condition, so the one thing left that the estate can still be held to is whether
    the condition was READ. That half is ours; the condition itself is the box's. A sensor
    that cannot read its own condition and stays green is a fail-open wearing a sensor's
    clothes, which is why the unreadable case keeps its red while the false case does not.
    Same form as the memory-condition row's `assertIsNotNone` two rows down."""
    try:
        value = arm[key]["median"]
    except (KeyError, TypeError, IndexError):
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value != value or value in (float("inf"), float("-inf")):   # NaN, ±inf
        return None
    return float(value)


#: WHERE AN INVERSION IS RECORDED, and it is a ledger rather than a log line because a
#: citability guard that suppresses figures SILENTLY is the true-but-invisible family
#: again: its failure mode is not a false red, it is a slow loss of citable figures with
#: no alarm. Appended and never overwritten, so "this inverts often" is answerable — which
#: is what lets the estate tell a substrate that CHANGED from a guard that is ALWAYS
#: TRIPPING. Those two look identical from inside any single run.
INVERSION_LEDGER = os.path.join(REPO, "planning", "build", "MEASUREMENTS.md")


def record_substrate_inversion(call_ratio, cost_ratio, wide_per_call, one_per_call):
    """Append one inversion to the measurement ledger and return what was written.

    DELIBERATELY NOT WRAPPED IN A `try`. An inversion that cannot be recorded is an alarm
    that did not sound, and swallowing that would rebuild the exact silence this record
    exists to break."""
    entry = (
        "\n### SUBSTRATE INVERSION — w7's CALL-versus-COST sensor declared its condition\n\n"
        "Written by `test_the_CALL_countable_and_the_COST_it_stands_for_do_not_move_together`\n"
        "(`tests/test_ep28c_w7.py`) at the moment of inversion. APPEND-ONLY; one entry per\n"
        "inversion, never overwritten. MAINT-1 A3.\n\n"
        "- date (UTC): %s\n"
        "- run: `python3 -m unittest tests.test_ep28c_w7` on box `%s`, kernel `%s`\n"
        "- barrier CALLS per record, width 1 / width 16: **%.4f**\n"
        "- barrier COST per record, width 1 / width 16: **%.4f**\n"
        "- per-call ms median: width 16 %.6f vs width 1 %.6f (wide did NOT exceed one)\n"
        "- READING: ON THIS SUBSTRATE THE CALL COUNTABLE IS THE COST COUNTABLE, THE W7\n"
        "  CORRECTION DOES NOT APPLY HERE, AND NO FIGURE CITING IT MAY BE TAKEN FROM THIS RUN.\n"
        % (_utc_now(), platform.node(), platform.release(),
           call_ratio, cost_ratio, wide_per_call, one_per_call))
    with open(INVERSION_LEDGER, "a", encoding="utf-8") as handle:
        handle.write(entry)
    return entry


def run_arms(root, widths=WIDTHS, n=16, reps=5, interleaved=True, drift_per_trial=0.0):
    """Drive every width `reps` times.

    INTERLEAVED (the shipped design): the widths rotate WITHIN each repetition, and the
    rotation advances, so no arm always runs first. SEQUENTIAL (the red world only): every
    trial of one width, then the next. `drift_per_trial` adds a growing delay to each
    successive trial, which is the world where the two designs give different answers."""
    order = []
    if interleaved:
        for r in range(reps):
            rot = list(widths[r % len(widths):]) + list(widths[:r % len(widths)])
            order.extend(rot)
    else:
        for w in widths:
            order.extend([w] * reps)

    results = {w: [] for w in widths}
    started = time.time()
    for idx, w in enumerate(order):
        results[w].append(Trial(root, w, n, delay=drift_per_trial * idx).run())
    finished = time.time()
    return {"order": order, "results": results,
            "wall_start": started, "wall_end": finished}


def arm_summary(trials, key="ms_per_record"):
    """Central value AND spread. Never a bare median (§A46's own shape in a figure)."""
    vals = sorted(t[key] for t in trials)
    return {
        "n_trials": len(vals),
        "min": vals[0],
        "median": statistics.median(vals),
        "max": vals[-1],
        "spread": vals[-1] - vals[0],
    }


def same_within_spread(a, b):
    """The estate's rule, executable: a difference smaller than one arm's spread is not a
    difference. `one arm's` is read as the LARGER of the two spreads, because the weaker
    claim is the honest one."""
    return abs(a["median"] - b["median"]) < max(a["spread"], b["spread"])


# =====================================================================================
# the rows: the DESIGN, on small samples
# =====================================================================================

class MeasurementDesignCase(unittest.TestCase):
    """The design's own properties, asserted. These are cheap and they run every suite."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ep28c-w7-")
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_NON_VACUITY_every_arm_actually_ran_and_recorded_what_it_claims(self):
        run = run_arms(self.root, n=8, reps=2)
        for w in WIDTHS:
            trials = run["results"][w]
            self.assertEqual(len(trials), 2, "width %d did not run twice" % w)
            for t in trials:
                self.assertEqual(t["records"], t["n"],
                                 "width %d recorded %d of %d submissions — an arm that "
                                 "wrote nothing agrees with anything"
                                 % (w, t["records"], t["n"]))
                self.assertGreater(t["members"], 0)
                self.assertIsNotNone(t["syncs_per_record"])

    def test_the_arms_are_INTERLEAVED_and_no_arm_always_runs_first(self):
        """Asserted on the ORDER the instrument produced, not on a comment claiming it."""
        run = run_arms(self.root, n=4, reps=3)
        order = run["order"]
        self.assertEqual(len(order), 9)
        # No arm occupies a contiguous block, and the first slot rotates.
        firsts = {order[0], order[3], order[6]}
        self.assertEqual(len(firsts), 3,
                         "the same width led every repetition — that is a sequential "
                         "design wearing an interleaved name")
        for w in WIDTHS:
            positions = [i for i, x in enumerate(order) if x == w]
            self.assertNotEqual(positions, list(range(positions[0], positions[0] + 3)),
                                "width %d ran as a contiguous block" % w)

    def test_the_summary_carries_a_SPREAD_beside_every_central_value(self):
        run = run_arms(self.root, n=4, reps=3)
        for w in WIDTHS:
            s = arm_summary(run["results"][w])
            for k in ("min", "median", "max", "spread", "n_trials"):
                self.assertIn(k, s)
            self.assertGreaterEqual(s["spread"], 0)
            self.assertLessEqual(s["min"], s["median"])
            self.assertLessEqual(s["median"], s["max"])

    def test_the_AMORTISATION_countable_moves_and_it_is_the_headline(self):
        """SYNCS PER RECORD is what group commit changes, and it is a COUNTABLE — immune to
        the host's memory condition, which is why §L.5 makes it the load-bearing evidence
        rather than any duration. At width 1 every record buys its own barrier; at a wider
        cap a batch's members share one."""
        run = run_arms(self.root, n=16, reps=3)
        one = statistics.median(t["syncs_per_record"] for t in run["results"][1])
        sixteen = statistics.median(t["syncs_per_record"] for t in run["results"][16])
        self.assertEqual(one, 1.0,
                         "at width 1 a record must buy exactly one barrier; got %r" % one)
        self.assertLess(sixteen, 1.0,
                        "the shipped width never amortised a barrier across a batch, so "
                        "there is nothing here to measure")
        self.assertGreater(max(t["largest_batch"] for t in run["results"][16]), 1)

    def test_RED_WORLD_a_sequential_design_attributes_an_INJECTED_DRIFT_to_an_arm(self):
        """THE CAN-FAIL PROOF OF THE MEASUREMENT DESIGN, driven rather than argued.

        A monotone drift is injected — each successive trial is slower by a fixed step,
        standing in for any condition that changes over a run's span. Under the SEQUENTIAL
        design the last arm runs last and eats all of it, so the arms separate by an amount
        that is entirely drift. Under the INTERLEAVED design the same drift lands on every
        arm alike and the separation collapses.

        The assertion is a COMPARISON BETWEEN THE TWO DESIGNS in one world, not a threshold
        on either — a threshold would be a fact about this box."""
        step = 0.02
        seq = run_arms(self.root, n=4, reps=3, interleaved=False, drift_per_trial=step)
        inter = run_arms(self.root, n=4, reps=3, interleaved=True, drift_per_trial=step)

        def spread_between_arms(run):
            meds = [statistics.median(t["seconds"] for t in run["results"][w])
                    for w in WIDTHS]
            return max(meds) - min(meds)

        s_seq = spread_between_arms(seq)
        s_int = spread_between_arms(inter)
        self.assertGreater(s_seq, s_int,
                           "the sequential design did not inflate the between-arm "
                           "separation under an injected drift, so this red world proves "
                           "nothing about why interleaving is required "
                           "(sequential %.4fs vs interleaved %.4fs)" % (s_seq, s_int))
        print("[EP-28C W7 red world] injected drift %.3fs/trial: between-arm separation "
              "SEQUENTIAL %.4fs vs INTERLEAVED %.4fs — the sequential design reports "
              "drift as effect" % (step, s_seq, s_int))

    def test_the_CALL_countable_and_the_COST_it_stands_for_do_not_move_together(self):
        """THE CORRECTION THIS FILE'S FIRST RUN FORCED ON ITSELF, asserted so it cannot be
        forgotten. Barrier CALLS per record and barrier COST per record are different
        quantities, and a design that reports the first as if it were the second overstates
        the lever. Asserted as a RELATION between the two ratios rather than as a threshold
        on either — a threshold would be a fact about this box, and the relation is the
        mechanism: `fdatasync` is cumulative, so a barrier covering more records costs
        more, and fewer-but-larger barriers do not save what fewer-and-equal ones would.

        THIS ROW KEEPS SENSING AND STOPS GATING [DOCUMENTED FLIP, MAINT-1, 2026-08-20,
        serving BUILD-PROMPT-STANDARD's §1 extension — a property test asserts a COUNTABLE,
        never a duration — in the FORM ruled at board :1086 after :1064's cure was withdrawn
        on a read]. WHAT STOOD HERE: `assertGreater(wide["per_call_ms"]["median"],
        one["per_call_ms"]["median"], ...)`, carrying the message kept verbatim below. WHY
        IT WAS WRONG, AND IT IS NOT WHAT THE FIRST RULING THOUGHT: `per_call_ms` IS a
        duration and the row WAS load-exposed, so the breach was real — but the law's usual
        cure was unavailable here, because the countable it would have substituted is
        ALREADY SHIPPED THREE LINES ABOVE as `call_ratio`, and substituting it would have
        re-committed in 2026 the very error this file corrected in place on 2026-08-03: A
        COUNTABLE CHOSEN AS A PROXY FOR A COST IS A PROXY ONE STEP AWAY FROM THE QUANTITY
        THAT MATTERS. You cannot assert that two quantities do not move together without
        measuring both. THE REAL DIAGNOSIS: this row is A SENSOR OF THE SUBSTRATE SITTING
        INSIDE A GATE FOR THE CODE. Its falsifier is `fdatasync`'s cumulative behaviour — a
        property of filesystem and kernel that no pass of ours moves — so a red here never
        meant a regression and could never be repaired by changing the engine. SO THE CURE
        IS FORM, NOT LOCATION, and the row is NOT deleted: it is the only detector for this
        file's own correction going stale. On inversion it now DECLARES the substrate
        condition instead of failing the build — loud, recorded to the measurement ledger,
        and distinguishable from a code regression by its own text — and the run's figures
        are marked uncitable. WHY THAT IS LAWFUL WHERE THE GATE WAS NOT: the action taken on
        the signal is correct whether the signal is real or noise. A citability guard under
        a noise inversion costs one run's figures; a build gate under the same noise blocks
        the line on a lie. ONE RED SURVIVES, and it is the only estate-answerable case — the
        condition CANNOT BE READ, matching the memory-condition row two rows down."""
        one = barrier_arm(self.root, 1, n=16, reps=3)
        wide = barrier_arm(self.root, 16, n=16, reps=3)
        call_ratio = one["calls_per_record"] / wide["calls_per_record"]
        cost_ratio = (one["barrier_ms_per_record"]["median"]
                      / wide["barrier_ms_per_record"]["median"])
        self.assertGreater(call_ratio, 1.0,
                           "the shipped width did not reduce the number of barrier calls, "
                           "so there is no amortisation here to attribute")
        wide_per_call = readable_median(wide, "per_call_ms")
        one_per_call = readable_median(one, "per_call_ms")
        self.assertIsNotNone(wide_per_call,
                             "the width-16 per-call barrier cost could not be READ, so this "
                             "row's condition is UNKNOWN rather than false — and a sensor "
                             "that cannot read its own condition while staying green is a "
                             "fail-open wearing a sensor's clothes")
        self.assertIsNotNone(one_per_call,
                             "the width-1 per-call barrier cost could not be READ, so this "
                             "row's condition is UNKNOWN rather than false — and a sensor "
                             "that cannot read its own condition while staying green is a "
                             "fail-open wearing a sensor's clothes")
        if wide_per_call <= one_per_call:
            entry = record_substrate_inversion(call_ratio, cost_ratio,
                                               wide_per_call, one_per_call)
            print("\n" + "=" * 86)
            # EVERY LOAD-BEARING PHRASE SITS INTACT ON ONE LINE, deliberately: the first
            # check written against this text matched a substring across a line break and
            # refused a declaration that said exactly what it had to. A phrase a reader
            # sees as one sentence must be greppable as one sentence.
            print("[EP-28C W7] SUBSTRATE DECLARATION — "
                  "THIS IS NOT A FAILURE AND NOT A CODE REGRESSION.")
            print("Nothing in this estate changed to produce it. A barrier covering a whole")
            print("batch did not cost more than one covering a single record, so:")
            print("ON THIS SUBSTRATE THE CALL COUNTABLE IS THE COST COUNTABLE, "
                  "THE W7 CORRECTION DOES NOT APPLY HERE, "
                  "AND NO FIGURE CITING IT MAY BE TAKEN FROM THIS RUN.")
            print("The falsifier is fdatasync's cumulative behaviour — a property of the")
            print("filesystem and the kernel, which no pass of ours moves. Recorded to")
            print("planning/build/MEASUREMENTS.md:")
            print(entry.strip())
            print("=" * 86 + "\n")
        else:
            print("[EP-28C W7] barrier CALLS/record ratio %.2fx vs barrier COST/record "
                  "ratio %.2fx — the countable overstates the lever by %.2fx on this "
                  "substrate"
                  % (call_ratio, cost_ratio, call_ratio / cost_ratio if cost_ratio else 0))

    def test_the_substrate_is_READ_and_names_the_hosts_memory_condition(self):
        """§L.5's amendment: a host under memory pressure is a different substrate from the
        same host at rest, and that condition was never stated beside a figure. It is read
        here rather than remembered, and its absence is a red."""
        sub = substrate(self.root)
        self.assertTrue(sub["box"])
        self.assertTrue(sub["kernel"])
        self.assertIsNotNone(sub["mem_available_mb"],
                             "the host's memory condition could not be read, so no figure "
                             "from this run may be cited as an absolute duration")
        self.assertIsNotNone(sub["swap_used_mb"])


# =====================================================================================
# --measure: the figures, with their conditions
# =====================================================================================

def measure(n=32, reps=9):
    root = tempfile.mkdtemp(prefix="ep28c-w7-measure-")
    try:
        before = substrate(root)
        wall_open = _utc_now()
        run = run_arms(root, n=n, reps=reps)
        wall_close = _utc_now()
        after = substrate(root)
        out = {
            "TAKEN_or_CARRIED": "TAKEN — every figure below was measured by this run",
            "wall_clock_open": wall_open,
            "wall_clock_close": wall_close,
            "submitters_per_trial": n,
            "repetitions_per_width": reps,
            "arm_order": run["order"],
            "substrate_at_open": before,
            "substrate_at_close": after,
            "arms": {},
        }
        for w in WIDTHS:
            trials = run["results"][w]
            out["arms"][w] = {
                "ms_per_record": arm_summary(trials, "ms_per_record"),
                "seconds_per_trial": arm_summary(trials, "seconds"),
                "syncs_per_record_median": statistics.median(
                    t["syncs_per_record"] for t in trials),
                "largest_batch_seen": max(t["largest_batch"] for t in trials),
                "records_per_trial": trials[0]["records"],
            }
        base = out["arms"][1]["ms_per_record"]
        for w in WIDTHS:
            arm = out["arms"][w]["ms_per_record"]
            out["arms"][w]["speedup_vs_width_1"] = (
                base["median"] / arm["median"] if arm["median"] else None)
            out["arms"][w]["difference_is_within_spread_of_width_1"] = same_within_spread(
                base, arm)
            out["arms"][w]["sync_amortisation_vs_width_1"] = (
                out["arms"][1]["syncs_per_record_median"]
                / out["arms"][w]["syncs_per_record_median"])
        # THE ATTRIBUTION, taken in the same session so its comparison is lawful.
        out["barrier_attribution"] = {w: barrier_arm(root, w, n=n) for w in WIDTHS}
        one, wide = out["barrier_attribution"][1], out["barrier_attribution"][16]
        out["the_countable_overstates_the_lever_by"] = (
            (one["calls_per_record"] / wide["calls_per_record"])
            / (one["barrier_ms_per_record"]["median"]
               / wide["barrier_ms_per_record"]["median"]))
        out["CARRIED_for_comparison"] = {
            "source": "design/36 ADDENDUM L §L.4, EP-28 W8's instrument, guest substrate",
            "band": "5.6x at batch 8, 13.5x at batch 16",
            "note": "CARRIED, not taken here. Different substrate (qcow2 on virtio in the "
                    "guest, below the syscall line) and a different subject (a whole gated "
                    "act through the channel). The comparable quantity across the two is "
                    "the COUNTABLE — syncs per record — not the duration.",
        }
        return out
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    if "--measure" in sys.argv:
        print(json.dumps(measure(), indent=1, sort_keys=True, default=str))
    else:
        unittest.main()
