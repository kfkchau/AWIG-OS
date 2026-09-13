"""EP-28C W4e — THE STANDING STOP CLAUSE, ASKED AND ANSWERED.

[THE EXPIRY FIRED, 2026-08-04, EP-28K. Read this note before the body, because the body
below describes a world that is now HALF gone.

WHAT IS DISCHARGED: the three EXISTENCE-shaped outcomes. `FILE-CREATE`, `FILE-MKDIR`,
`FILE-SYMLINK` (name taken), `FILE-RMDIR`, `FILE-UNLINK`, `FILE-RENAME` (name absent) and
`FILE-LINK` (target absent, new name taken) now DECLARE those preconditions and the gate
answers them inside its own decide region, so check-then-act is one unit and the second
create refuses. The three rows that pinned that race are REMOVED rather than widened, which
is what this file's own expiry clause directs. The exhibit did not die with them: it MOVED
to `tests/test_ep28k.py`'s red world, where the lifted-out-of-the-region composition is
driven through the real gate every run and reproduces two records for one path.

WHAT IS NOT DISCHARGED, AND IT IS WHY THIS FILE STILL EXISTS: the port's precondition read
is STILL outside the region — `src/bridge/` took zero lines, and its retirement is W4e's
own work against the new law — and FIVE of the port's outcomes are NOT carried by it. The
`ENOTDIR` / `EISDIR` / `EPERM` outcomes ask about a node's KIND; `ENOTEMPTY` asks about a
directory's CONTENTS; and the parent-`ENOENT` on the create family asks about a key
computed by path arithmetic, which is namespace grammar the engine deliberately does not
hold. Each of those still races exactly as the body describes. Deleting this file whole
would have reported a partial fix as a whole one (§A55), which is the thing the estate
found more dangerous than no fix at all. The file's final disposition is RAISED, not taken.]

W4e's order (AMENDMENT 8 §8.1) is: remove `govosfs.c`'s one-caller lowering, correlate
request and reply by transport id, and let the user-space half submit concurrently into
W1's queue — **with the standing stop clause verbatim: if admitting multiple in-flight
requests would change what any DECLARED operation records or returns — the combinations
the declarations permit, not the traffic you observe — that is a STOP-and-raise naming
the operation.**

THE CLAUSE FIRED. This file is the finding EXHIBITED rather than attested (charter §A42),
and it is the whole of what W4e built: no channel line was written, because writing one
would be improvising around a definitive the clause reserves to a ruling.

THE FINDING IN ONE SENTENCE: the port's ABSENCE-classed precondition read and the
`gate.execute` that acts on it are not atomic against each other, so two in-flight
requests for one path both read "absent", both decide, and both RECORD.

WHY THE DECIDE REGION DOES NOT REACH IT, AND WHY THAT RULING WAS RIGHT. EP-28G AMENDMENT 4
ruled READING B on exactly this span: a precondition returning `EEXIST` produces NO record,
so under ADDENDUM 1's identity — the decision IS the record — it is not a decision, and a
region whose subject is decisions does not extend over it. That ruling is correct about the
SITE. **It is silent about the COMPOSITION**, and the composition is what runs: an
absence-classed read that is the GUARD on a decision, followed by the decision it guards.
The race is between the guard and the thing guarded, and its outcome is not two absences —
it is two DECISION RECORDS. Charter §A41 EXTENSION 3's own shape: a disposal scoped to the
instance does not cover the composition, and the recurrence returns in a shape the ruling
did not model.

THE SEVEN OPERATIONS, named as the clause requires, with what changes:

  FILE-CREATE   two in flight for one path: both pass `exists()`, both record a create,
  FILE-MKDIR    the second caller gets 0 where the serialized channel gives -EEXIST.
  FILE-SYMLINK  The gate refuses neither: all three carry `"checks": []`.
  FILE-RMDIR    `ENOTEMPTY` read against a directory a concurrent create fills before the
                gate runs: an rmdir records against a directory that is not empty.
  FILE-UNLINK   `ENOENT`/`EISDIR` read against a node a concurrent unlink removes first:
                two unlinks record for one node.
  FILE-RENAME   `ENOENT` on the source, `ENOTEMPTY` on the destination, same shape.
  FILE-LINK     `ENOENT` on the target and `EEXIST` on the new name, same shape.

All seven were read from the founding pack rather than remembered, and the check-set is
asserted below so the enumeration cannot go stale silently (§A38's shape: the clause that
makes the other clauses trustworthy).

WHAT IS ALREADY TRUE TODAY, WHICH IS THE PART THAT DECIDES THE URGENCY. The port is
ALREADY driven concurrently by this suite — `test_ep28c_w4b.py:375` runs 24 threads through
`KernelPort.handle` — and the race does not fire there because every thread uses a DISTINCT
path, which the row chose for the identity question it was written for. **The composition is
unguarded now; W4e is what would make it reachable from below the syscall line.** So this is
not a prediction about a world W4e would create. It is a measurement of the world that
exists, taken because W4e's clause required asking.

THE THREE DISPOSITIONS, with their costs, because the clause asks for a raise and a raise
derives everything derivable at zero evidence cost (charter §A24):

  1. Hold the gate's decide region across the port's precondition read and its execute.
     In this fence by FILE (`kernel_port.py`), but it CHANGES THE REGION'S SPAN, which
     EP-28G ruled at READING B. Improvising around a definitive.
  2. Give the port its own construct over (precondition, execute). Also `kernel_port.py`
     only, and it adds no serialization the region does not already impose on the decide
     half — but it is a SECOND construct for one property, which is §A52's own diagnostic
     one layer over: count the places the property is established; one is a boundary, two
     is a convention wearing a boundary's name.
  3. Move the preconditions into the op definitions as `checks`, so the gate answers them
     inside its own region. The correct-looking shape, and it is FOUNDING work: out of
     this fence by the fence's own words, and it changes what a refusal RECORDS (an
     absence-classed `EEXIST` today appends nothing; a check-based one appends a refusal),
     which is a governance change and not an engine one.

Ruling this is the mentor's. Building it is not this seat's.

THE EXPIRY IS BEHAVIOURAL, NOT TEXTUAL (§A47 and its extension: an expiry trigger must key
on the same KIND of thing the discharge changes). `test_THE_EXPIRY_*` asserts the racy
outcome. When any of the three dispositions lands, the composition becomes atomic and that
row goes RED — forcing this file to be DELETED rather than widened. A text proxy over
`kernel_port.py` would have been the shape §A47's own extension was filed against.
"""

import json
import os
import shutil
import sys
import tempfile

import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from bridge.kernel_port import KernelPort                          # noqa: E402
from bridge.mount import build_brain                               # noqa: E402

FOUNDING = os.path.join(REPO, "src", "founding", "founding-pack.json")
GOVOSFS_C = os.path.join(REPO, "planning", "vm", "govosfs", "govosfs.c")

#: The operations whose recorded or returned behaviour changes. Data, so the enumeration is
#: readable and so the row below can prove it is not empty.
NAMED_BY_THE_STOP = ("FILE-CREATE", "FILE-MKDIR", "FILE-SYMLINK", "FILE-RMDIR",
                     "FILE-UNLINK", "FILE-RENAME", "FILE-LINK")


def _wire(op, cls="DECISION", uid=1000, gid=1000, pid=42, **kw):
    f = {"id": "1", "op": op, "class": cls,
         "uid": str(uid), "gid": str(gid), "pid": str(pid)}
    f.update({k: str(v) for k, v in kw.items()})
    return f


def _op_definitions():
    """Every op definition in the founding pack, read from the STRUCTURE.

    Charter §A51: an enumeration over a structured artifact reads the structure, not the
    names. This walks for records carrying a `payload.definition` and keys them by
    `payload.name` — so an op whose name does not match anybody's idea of an op name is
    still in the set."""
    with open(FOUNDING, encoding="utf-8") as fh:
        doc = json.load(fh)
    found = {}

    def walk(o):
        if isinstance(o, list):
            for i in o:
                walk(i)
        elif isinstance(o, dict):
            p = o.get("payload")
            if isinstance(p, dict) and p.get("name") and isinstance(p.get("definition"), dict):
                found[p["name"]] = p["definition"]
            for v in o.values():
                walk(v)

    walk(doc)
    return found


class _Port(unittest.TestCase):
    """A brain composed exactly as the guest's daemon composes it."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="w4e-")
        self.store, self.gate, self.views, self.blobs = build_brain(
            os.path.join(self.dir, "rec.jsonl"), os.path.join(self.dir, "blobs"))
        self.port = KernelPort(self.store, self.gate, self.views, self.blobs)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def call(self, op, cls="DECISION", payload=b"", **kw):
        return self.port.handle(_wire(op, cls, **kw), payload)

    # [`creates_of` and `race_two_creates` REMOVED 2026-08-04 by EP-28K, with the three rows
    # they served. `race_two_creates` was a SCHEDULER over the port's create precondition and
    # nothing else can now be exhibited with it: the create race is closed at the gate. The
    # port's five UNCARRIED outcomes still race and W4e will need a scheduler over each of
    # them, but a scheduler written for a discharged outcome is not that instrument — it is
    # scaffolding that reads as coverage. Leaving it would have been the stale-instrument
    # class this estate keeps finding, so it goes with its rows and W4e writes its own.]


class TestTheSubjectExists(_Port):
    """NON-VACUITY, first (AMENDMENT 8.1, close item 49's clause). Every row below is a
    statement about a set of operations and a fold; a row over an empty set or an empty
    world agrees with anything. These clauses are what make the rest trustworthy."""

    def test_the_seven_named_operations_are_all_declared_in_the_founding(self):
        defs = _op_definitions()
        self.assertGreaterEqual(len(defs), 1, "no op definitions were read at all")
        missing = [n for n in NAMED_BY_THE_STOP if n not in defs]
        self.assertEqual(missing, [], "the stop clause names an operation the founding "
                                      "does not declare — the enumeration has gone stale")

    def test_all_seven_now_carry_the_declared_existence_check_the_gate_answers(self):
        """[DOCUMENTED FLIP, EP-28K, and the flip is this row's OWN directed action: it read
        "all seven carry an EMPTY check list" and its failure message said *an op grew a check
        since this finding was taken — re-ask the stop clause against the new check rather
        than trusting this row*. The check arrived; the clause is re-asked here.

        WHAT IT NOW ASSERTS, and it is the same question pointed the other way: every one of
        the seven declares a `binding` check, so the existence answer the race turned on comes
        from the GATE, inside the region, and not from the port's read. The row that says the
        port's read is still outside the region is below and is unmoved — the two together are
        what say this file is half discharged rather than whole.]"""
        defs = _op_definitions()
        without = [n for n in NAMED_BY_THE_STOP
                   if not [c for c in (defs[n].get("checks") or [])
                           if c.get("check") == "binding"]]
        self.assertEqual(without, [],
                         "an operation this finding names lost its declared existence check — "
                         "the race it pinned is reachable again")

    def test_the_GATE_answers_for_all_seven_and_the_fold_it_reads_is_not_empty(self):
        """DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS
        READING: `self.port._posix_precondition(...)`, called directly, twice, to prove the
        finding's subject — "EEXIST is the port's answer and it is what races", and that each
        of the seven was actually answered by the port's read.

        THE SUBJECT MOVED RATHER THAN VANISHED, and that is the whole discharge: each of the
        seven is answered, and the answerer is now the GATE's declared check. So the row asks
        the same question through the real path and asserts the same seven, plus the half
        that could not be asserted before — the answer is RECORDED."""
        self.call("FILE-MKDIR", path="/d", perm="755")
        self.assertTrue(self.port.state.exists("/d"), "the fold this row reads is empty")
        status, _f, _p = self.call("FILE-CREATE", path="/d", perm="644")
        self.assertEqual(status, -17, "EEXIST is the answer, and the gate is what gives it")
        # ONE WIRE PER OP, EACH BUILT TO REACH ITS OWN DECLARED CHECK. A single shared wire
        # cannot do this and quietly did not: `path="/nope"` is a SUCCESSFUL create, and the
        # create then made the next op's refusal come from the world the previous row built
        # rather than from the check under test.
        self.call("FILE-CREATE", path="/x", perm="644")
        wires = {
            "FILE-CREATE":  {"path": "/x", "perm": "644"},          # bound     -> EEXIST
            "FILE-MKDIR":   {"path": "/x", "perm": "755"},          # bound     -> EEXIST
            "FILE-SYMLINK": {"path": "/x", "target": "/d"},         # bound     -> EEXIST
            "FILE-RMDIR":   {"path": "/gone"},                      # unbound   -> ENOENT
            "FILE-UNLINK":  {"path": "/gone"},                      # unbound   -> ENOENT
            "FILE-RENAME":  {"path": "/gone", "new_path": "/g2"},   # unbound   -> ENOENT
            "FILE-LINK":    {"target_path": "/gone", "new_path": "/g3"},
        }
        self.assertEqual(sorted(wires), sorted(NAMED_BY_THE_STOP),
                         "a wire is missing for an operation the stop clause names")
        answered = []
        for op in NAMED_BY_THE_STOP:
            before = len(self.store.all())
            code, _f, _p = self.call(op, **wires[op])
            recorded = [e for e in self.store.all()[before:] if e["action"] == "op-refused"]
            if code != 0 and recorded:
                answered.append(op)
        self.assertEqual(sorted(answered), sorted(NAMED_BY_THE_STOP),
                         "an operation this finding names is not refused-and-recorded by the "
                         "gate's declared check — the discharge's own subject would be wrong")
        self.assertFalse(hasattr(self.port, "_posix_precondition"),
                         "the port still holds the read this file's finding was about")


class TestTheCompositionIsNotAtomic(_Port):
    """THE FINDING, DRIVEN. The structural half and the behavioural half, separately, so a
    reader can tell which one moved if either does."""

    def test_no_precondition_read_sits_outside_the_region_and_the_survivors_are_NAMED(self):
        """DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS
        READING: `self.port._posix_precondition`, read into `real_pre` and wrapped to observe
        `decide_region_held()` at the precondition. Its own failure message named the
        discharge condition — "the precondition read is inside the region — the finding is
        closed and this file should be deleted."

        THE FINDING IS CLOSED THE OTHER WAY: the read is not inside the region, it is GONE,
        and the outcomes it answered are decided inside the region by declared checks. The
        file is NOT deleted, because two of its rows have a live subject — the channel — and
        deleting the whole would report a partial discharge as a whole one (§A55).

        WHAT THIS ROW NOW PROTECTS, and it is the reason it survives its own subject: the
        pre-gate reads that REMAIN are named and observed outside the region. Raise 3b drove
        all of them and capped each; this row is the structural half that reds if a new one
        appears, or if `gate.execute` is ever entered with the region already held.

        STILL ASSERTED ON BEHAVIOUR RATHER THAN SOURCE TEXT — W4a's lesson, which is why the
        predicate is observed from two positions and never read off a literal."""
        from kernel.gate import decide_region_held

        seen = {}
        real_params = self.port._params_for

        def watched_params(op, f, payload):
            seen["at_params"] = decide_region_held()
            return real_params(op, f, payload)

        real_prov = self.port._prov

        def watched_prov(f):
            seen["at_prov"] = decide_region_held()
            return real_prov(f)

        real_exec = self.gate.execute

        def watched_exec(name, actor, params=None):
            seen["at_execute"] = decide_region_held()
            inside = decide_region_held()
            out = real_exec(name, actor, params)
            seen["inside_the_act"] = seen.get("inside_the_act") or inside
            return out

        self.port._params_for = watched_params
        self.port._prov = watched_prov
        self.gate.execute = watched_exec
        try:
            self.call("FILE-CREATE", path="/f", perm="644")
        finally:
            self.port._params_for = real_params
            self.port._prov = real_prov
            self.gate.execute = real_exec

        self.assertFalse(hasattr(self.port, "_posix_precondition"),
                         "the retired read is back, and every cap in this file re-opens")
        self.assertEqual(seen.get("at_prov"), False,
                         "the provenance fold read is inside the region")
        self.assertEqual(seen.get("at_params"), False,
                         "the parameter fold read is inside the region")
        self.assertEqual(seen.get("at_execute"), False,
                         "`gate.execute` is entered with the region already held, which "
                         "would mean some caller above it took the region")
        # NON-VACUITY: three Falses are what an always-False predicate returns too, so the
        # predicate is shown answering TRUE somewhere. An on-append listener is the position
        # that answers True, because the store publishes to its listeners from inside the
        # appending thread's region — which is also the fact `tests/test_ep28c_w4e_c.py`'s
        # composition class rests on.
        #
        # [A CLAUSE THAT COULD NOT FAIL STOOD HERE AND WAS REMOVED, 2026-08-07, same session,
        # my own: `assertTrue(any(h is False for h in held) or held == [])`. The `or held ==
        # []` arm made it pass on an empty list, which is what a wrapper that never ran also
        # produces, and it duplicated the `at_execute` observation above. One real True
        # observation is the non-vacuity; a second unfalsifiable clause beside it was noise
        # that read as rigour.]
        observed = {}

        def note(*_a, **_k):
            observed["inside"] = decide_region_held()
        self.store.on_append(note)
        self.call("FILE-CREATE", path="/probe", perm="644")
        self.assertTrue(observed.get("inside"),
                        "non-vacuity: the region predicate never answered True anywhere, so "
                        "the three Falses above are a constant and not an observation")

    # [THE THREE DISCHARGED ROWS, REMOVED 2026-08-04 by EP-28K — not widened, which is what
    # this file's expiry clause directs. They were:
    #
    #   test_THE_EXPIRY_two_in_flight_creates_of_one_path_both_record_and_both_return_zero
    #   test_the_fold_ends_with_ONE_node_under_TWO_records_which_is_why_nothing_reds
    #   test_UNSCHEDULED_the_window_is_narrow_and_the_row_says_so_rather_than_claiming_more
    #
    # All three pinned the same-path create race. The declared existence check refuses the
    # second create inside the region, so the first two REDDEN and the third would have gone
    # green over a race that can no longer fire — a row measuring nothing, which is the defect
    # class this estate keeps finding rather than a harmless leftover.
    #
    # THE EXHIBIT MOVED RATHER THAN DIED, which is the only reason removing them is honest:
    # `tests/test_ep28k.py` drives the SAME composition — the liveness read taken outside the
    # region, then the act — through the real gate, and reproduces two records for one path
    # every run. What was a pin on a defect is now a red world for the law that closed it.]


class TestTheChannelWasNotTouched(unittest.TestCase):
    """W4e BUILT NO CHANNEL LINE, and the row proves it rather than the entry claiming it.

    The stop clause reserves the disposition to a ruling, so building the channel would
    have been improvising around a definitive. What is asserted here is the state the STOP
    left the tree in: the one-caller lowering is exactly where it was."""

    def test_the_one_caller_lowering_is_still_in_place(self):
        with open(GOVOSFS_C, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("govos_call_lock", src,
                      "the channel lock is gone — W4e was built, so this file's premise is "
                      "wrong and the stop it records has been overtaken")
        self.assertIn("mutex_lock(&govos_call_lock)", src)

    def test_the_wire_ALREADY_carries_the_transport_id_the_order_asks_for(self):
        """Derived at zero evidence cost and worth the ruling seat's attention: the
        correlation W4e is asked to build is HALF PRESENT. The module stamps `id=` onto
        every request (`govos_call`), the daemon echoes it into every reply
        (`kernel_port.build_reply`), and the kernel never reads it back. What W4e adds is a
        pending-request table and the daemon's concurrency — not a wire change."""
        with open(GOVOSFS_C, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn('"id=%llu\\t"', src, "the request no longer carries a transport id")
        from bridge.kernel_port import build_reply
        reply = build_reply("7", 0)
        self.assertTrue(reply.startswith(b"id=7\t"),
                        "the reply no longer carries the transport id it is correlated by")


if __name__ == "__main__":
    unittest.main()
