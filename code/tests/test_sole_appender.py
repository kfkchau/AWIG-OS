"""T-ONE-APPENDER, RE-AIMED AT BEHAVIOUR (EP-28C W4a) — formerly T-GATE-SOLE-APPENDER.

THE PROPERTY: every append to the record issues from one loop, and the only callers that
may enter that loop are the sanctioned ones. `design/28` §I2; EP-01 step 3.

WHY THIS FILE WAS RE-AIMED, stated first because it is the whole reason the row exists in
this shape. Until 2026-08-03 the guard was a SOURCE-TEXT SCAN: it read every file under
`src/` and refused the literal `._append(` outside a sanctioned set. EP-28G then split the
store's write path into `store._publish` (mint, write, flush, publish) and
`store._await_durable` (the covering barrier), lawfully and by direction. Seven assertions
in the estate were falsified by that split and were caught BECAUSE THEY BROKE. This one was
not falsified. It kept passing, because `store._publish` is a route its literal cannot see —
so the guard over the single-writer law went BLIND and stayed green about it. Same coupling,
opposite symptom, and the symptom that hides landed on the load-bearing guard.

THE REPAIR IS NOT A SECOND LITERAL, and that is a ruling rather than a preference (mentor
verdict, EP-28G close, 2026-08-03). Adding `._publish(` beside `._append(` rebuilds the trap
for the THIRD route, and this arc's whole point is that the write path can move lawfully. A
source-text scan is not the property; it is a proxy for it that a lawful refactor retires.

SO THE GUARD OBSERVES THE EXECUTING PATH INSTEAD. Every record that reaches the record file
is written at exactly one site — `store._append_one` — and the store's own on-append listener
contract fires from inside that write, so a listener's stack IS the writing path. The guard
walks that stack outward past the store's own machinery and asks ONE question: which file
ENTERED the store? It never asks what any file says. A route renamed, a route added, a route
reached by indirection: all three are the same observation, because the observation is of the
call that happened rather than of the text that describes it.

WHAT THE SCOPE IS AND IS NOT — unchanged from the retired form, deliberately. The retired
scan read `src/` only, so product code is the subject and a test or a tool driving the store
directly is not. The behavioural form keeps exactly that boundary: an entry from outside the
product root is out of scope, and the product root is a parameter rather than a constant so a
red world can be driven with a rogue that really executes.
"""

import os
import sys
import tempfile
import textwrap
import traceback
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel import commit as commit_mod  # noqa: E402
from kernel import store as store_mod  # noqa: E402
from kernel.compose import build_full_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from kernel.store import EventStore  # noqa: E402

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

#: THE STORE'S OWN MACHINERY. These frames are the funnel itself, not callers of it, so the
#: walk steps over them to find whoever entered. Identified by the MODULE'S OWN FILE rather
#: than by a path string, so the set stays correct under any product root a red world uses.
ENGINE = frozenset({os.path.abspath(store_mod.__file__), os.path.abspath(commit_mod.__file__)})

#: The only product files that may ENTER the appender: the gate (its one write and its
#: refusal), the founding installer (the constitutional seed — EP-14 relocated genesis here
#: out of boot.py), and the dual-audit mirror (design/28 §7). Everything else in `src/` must
#: reach the record through the gate. This is the retired scan's own sanctioned set, minus
#: `kernel/store.py`, which was in it only because the definition lives there — under a
#: behavioural walk the definition is ENGINE and never an entry.
SANCTIONED_ENTRY = frozenset({"kernel/gate.py", "founding/install.py", "kernel/protection.py"})


def entry_file(stack):
    """WHO ENTERED THE STORE, from a real stack. `stack` is `traceback.extract_stack()`
    order — outermost first.

    From the innermost frame: advance to the first ENGINE frame (that is `_append_one`
    calling the listener), skip every contiguous ENGINE frame above it, and return the first
    frame that is not the store's own machinery. That frame is the caller that entered.

    Returns the absolute filename, or None if the stack holds no engine frame at all — which
    the caller treats as a failure to observe rather than as a pass (§A38: a check whose pass
    condition is an absence must prove its subject non-empty).
    """
    files = [os.path.abspath(f.filename) for f in stack]
    i = len(files) - 1
    while i >= 0 and files[i] not in ENGINE:      # step off the listener's own frames
        i -= 1
    if i < 0:
        return None                               # no engine frame: nothing was observed
    while i >= 0 and files[i] in ENGINE:          # step over the funnel
        i -= 1
    return files[i] if i >= 0 else None


def unsanctioned_entries(stacks, product_root):
    """The guard's one predicate. Every observed write whose entry frame lies inside
    `product_root` must be a sanctioned entry; the rest are out of scope exactly as they were
    under the retired scan. Returns the offending relative paths, in first-seen order."""
    root = os.path.abspath(product_root)
    bad = []
    for stack in stacks:
        f = entry_file(stack)
        if f is None or not f.startswith(root + os.sep):
            continue
        rel = os.path.relpath(f, root).replace(os.sep, "/")
        if rel not in SANCTIONED_ENTRY and rel not in bad:
            bad.append(rel)
    return bad


#: THE RETIRED FORM, kept as an EXHIBIT and never as a guard. It is the predicate this file
#: carried until 2026-08-03, reproduced verbatim in shape so the red worlds below can be
#: driven through it and shown blind. Nothing in this file asserts anything on its output
#: except that it fails to see what the behavioural form sees.
_RETIRED_TOKEN = "._append("


def retired_text_scan(source_text):
    """The scan as it stood: does this file's TEXT name the private appender?"""
    return _RETIRED_TOKEN in source_text


# ---- the rogue modules the red worlds execute ---------------------------------------
#
# EACH ONE REALLY RUNS AND REALLY APPENDS. §A42: a red world must run the SAME CODE PATH the
# true positive runs, or it exhibits a property of an expression rather than of the
# instrument. These are written into a temporary product root, imported, and called; the
# record grows; the listener captures the real stack; the real predicate reads it.
ROGUE_NEW_ROUTE = textwrap.dedent('''\
    """A rogue reaching the route EP-28G created. Its text names the literal."""
    def sneak(store, draft):
        return store._publish(draft)
    ''')

ROGUE_OLD_ROUTE = textwrap.dedent('''\
    """A rogue reaching the route that existed before the split."""
    def sneak(store, draft):
        return store._append(draft)
    ''')

ROGUE_NO_LITERAL = textwrap.dedent('''\
    """A rogue that names NO route literal at all — the call is assembled at run time.
    No text scan can ever see this one, in any token set, however many literals it grows."""
    def sneak(store, draft):
        route = "_" + "publ" + "ish"
        return getattr(store, route)(draft)
    ''')


class _Observed:
    """A kernel with every append's executing path captured."""

    def __init__(self):
        d = tempfile.mkdtemp()
        (self.store, self.gate, self.views,
         self.blobs, self.sv) = build_full_kernel(os.path.join(d, "record.jsonl"),
                                                  os.path.join(d, "blobs"))
        self.stacks = []
        self.store.on_append(lambda _rec: self.stacks.append(traceback.extract_stack()))

    def close(self):
        self.store.close()


class TestEveryAppendEntersFromASanctionedCaller(unittest.TestCase):
    """THE PROPERTY, ASSERTED ON BEHAVIOUR."""

    def setUp(self):
        """THE OBSERVATION IS ESTABLISHED HERE, NOT IN A SIBLING ROW, AND THE PLACEMENT IS
        THE CLAUSE (§A48). Every row below has a pass condition that is an ABSENCE — no
        unsanctioned entry — so every one of them would green over a run that observed
        nothing at all. `unittest` orders methods alphabetically, so a precedence stated in
        prose is void; asserted here, no row in this class can run over an unproven subject.
        """
        self.obs = _Observed()
        self.addCleanup(self.obs.close)
        # Real governed traffic through the real gate: a permitted act and a refused one.
        self.obs.gate.execute("REGISTER-CAPABILITY", "SYSTEM",
                              {"driver": "nvme", "device_class": "block"})
        with self.assertRaises(OpError):
            self.obs.gate.execute("BIND-DEVICE", "SYSTEM", {"device": "sda", "driver": "ghost"})
        # SUBJECT PROVEN NON-EMPTY, twice over: writes were observed at all, and each one
        # resolved to a real entry frame rather than to None.
        self.assertGreaterEqual(len(self.obs.stacks), 2,
                                "no append was observed — the guard has nothing to read")
        self.entries = [entry_file(s) for s in self.obs.stacks]
        self.assertNotIn(None, self.entries,
                         "an observed append had no engine frame on its stack, so the walk "
                         "could not find who entered — the instrument, not the build")

    def test_every_observed_append_entered_from_a_sanctioned_caller(self):
        self.assertEqual(unsanctioned_entries(self.obs.stacks, SRC), [])

    def test_the_gate_and_the_mirror_are_both_actually_seen(self):
        """The set is proven POSITIVELY as well as by absence. A shipped composition runs the
        two mutually-blind audit streams, which append from inside an on-append listener — so
        the walk has to step over a store frame, a commit frame, a store frame AND the outer
        write to find `protection.py`. If the walk were shallow it would report the store and
        this row would fail while the emptiness row above stayed green."""
        seen = {os.path.relpath(f, SRC).replace(os.sep, "/") for f in self.entries}
        self.assertIn("kernel/gate.py", seen)
        self.assertIn("kernel/protection.py", seen, sorted(seen))
        self.assertTrue(seen <= set(SANCTIONED_ENTRY), sorted(seen))

    def test_the_store_exposes_no_public_appender(self):
        """The retired file's other text scan — `store.append(` outside the gate — asserted
        as the fact it was a proxy for. The public writer does not exist, which is a question
        about the object rather than about anybody's source."""
        self.assertFalse(hasattr(EventStore, "append"),
                         "the public writer exists again; every caller could reach the record")
        self.assertFalse(hasattr(self.obs.store, "append"))


class TestARogueIsCaughtWhicheverRouteItTakes(unittest.TestCase):
    """THE RED WORLDS, GENERATED AND EXECUTED. Each rogue is written into its own product
    root, imported, and called with a real store. Nothing is simulated."""

    def _drive(self, source):
        """Run a rogue through the real store and return (entry-relative-path, root, record).

        The rogue lives under a temporary PRODUCT ROOT rather than under `src/`, because a
        red world that writes into the tree it is grading would be the instrument corrupting
        its subject. The engine set is by module file, so the walk is unaffected."""
        root = tempfile.mkdtemp(prefix="rogue-root-")
        path = os.path.join(root, "rogue_module.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(source)
        obs = _Observed()
        self.addCleanup(obs.close)
        sys.path.insert(0, root)
        try:
            import importlib
            import importlib.util
            spec = importlib.util.spec_from_file_location("rogue_module_%d" % id(source), path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            importlib.invalidate_caches()
            before = len(obs.store.all())
            mod.sneak(obs.store, {"actor": "rogue", "action": "SNEAK",
                                  "rule_cited": "ROOT-NEG-1"})
            obs.store._await_durable()
        finally:
            sys.path.remove(root)
        self.assertEqual(len(obs.store.all()), before + 1,
                         "the rogue did not actually append — the red world proved nothing")
        return unsanctioned_entries(obs.stacks, root), root

    def test_red_world_the_new_route_is_caught(self):
        """The route EP-28G created, reached by name from an unsanctioned file."""
        bad, _root = self._drive(ROGUE_NEW_ROUTE)
        self.assertEqual(bad, ["rogue_module.py"])

    def test_red_world_the_old_route_is_still_caught(self):
        """THE RE-AIM IS NOT A SWAP OF BLINDNESS. The route the retired scan did see is still
        caught by the form that replaced it, so nothing was traded away."""
        bad, _root = self._drive(ROGUE_OLD_ROUTE)
        self.assertEqual(bad, ["rogue_module.py"])

    def test_red_world_a_route_named_by_no_literal_at_all_is_caught(self):
        """THE ROW THAT SETTLES WHY A LITERAL WAS REFUSED. This rogue's text contains neither
        `_append` nor `_publish` — the attribute name is assembled at run time — so NO token
        set of any size could ever see it. The behavioural form catches it identically to the
        other two, because it reads the call that happened."""
        bad, _root = self._drive(ROGUE_NO_LITERAL)
        self.assertEqual(bad, ["rogue_module.py"])

    def test_a_sanctioned_entry_in_the_same_position_is_NOT_reported(self):
        """THE COMPLEMENT, so the predicate is not merely reporting everything it sees. The
        gate's own writes run the identical walk and come back clean."""
        obs = _Observed()
        self.addCleanup(obs.close)
        obs.gate.execute("REGISTER-CAPABILITY", "SYSTEM",
                         {"driver": "ahci", "device_class": "block"})
        self.assertGreaterEqual(len(obs.stacks), 1)
        self.assertEqual(unsanctioned_entries(obs.stacks, SRC), [])


class TestTheRetiredFormIsShownBlind(unittest.TestCase):
    """THE EXHIBITION OF WHY THE SCAN RETIRED, driven over the SAME decoys the behavioural
    form catches. This is the evidence for the ruling rather than a restatement of it."""

    def test_the_retired_scan_reports_two_of_the_three_rogues_as_clean(self):
        self.assertFalse(retired_text_scan(ROGUE_NEW_ROUTE),
                         "the retired scan saw the new route — then it was never blind")
        self.assertFalse(retired_text_scan(ROGUE_NO_LITERAL))
        # AND THE ONE IT DID SEE, so the exhibit is a comparison rather than a complaint:
        # the retired form was correct about the route it was written for and about nothing
        # else, which is exactly what a proxy is.
        self.assertTrue(retired_text_scan(ROGUE_OLD_ROUTE))

    def test_adding_a_second_literal_would_still_leave_the_third_route_open(self):
        """THE RULING'S OWN ARGUMENT, DRIVEN. A scan extended to both known routes still
        reports the indirection rogue clean — which is the reason a literal was refused as
        the repair, exhibited instead of asserted."""
        extended = ("._append(", "._publish(")
        self.assertTrue(any(t in ROGUE_NEW_ROUTE for t in extended))
        self.assertTrue(any(t in ROGUE_OLD_ROUTE for t in extended))
        self.assertFalse(any(t in ROGUE_NO_LITERAL for t in extended),
                         "the two-literal scan saw the indirection rogue — then the third "
                         "route argument does not hold and this repair needs re-deriving")


class TestTheGatesRecordArithmetic(unittest.TestCase):
    """THE FUNCTIONAL HALF, CARRIED UNCHANGED from the retired file: the consequence of the
    property. Exactly one governed record per op, minted by the gate's write; a refusal is
    itself exactly one record and produces no decision."""

    _MIRROR = ("dual-audit-record", "dual-audit-b-record")

    def _governed(self, store):
        return [e for e in store.all() if e["action"] not in self._MIRROR]

    def _kernel(self):
        d = tempfile.mkdtemp()
        return build_full_kernel(os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"))

    def test_every_op_yields_exactly_one_record_minted_by_the_gate(self):
        store, gate, _views, _blobs, _sv = self._kernel()
        self.addCleanup(store.close)
        before = len(self._governed(store))
        rec = gate.execute("REGISTER-CAPABILITY", "SYSTEM",
                           {"driver": "nvme", "device_class": "block"})
        self.assertEqual(len(self._governed(store)), before + 1)
        self.assertEqual(rec["action"], "REGISTER-CAPABILITY")
        self.assertIs(store.by_seq(rec["seq"]), rec)
        extra = [e["action"] for e in store.all() if e["seq"] > rec["seq"]]
        self.assertTrue(all(a in self._MIRROR for a in extra), extra)

    def test_refusal_is_one_record_and_no_decision(self):
        store, gate, _views, _blobs, _sv = self._kernel()
        self.addCleanup(store.close)
        before = len(self._governed(store))
        with self.assertRaises(OpError):
            gate.execute("BIND-DEVICE", "SYSTEM", {"device": "sda", "driver": "ghost"})
        self.assertEqual(len(self._governed(store)), before + 1)
        self.assertEqual(len(store.by_action("BIND-DEVICE")), 0)


if __name__ == "__main__":
    unittest.main()
