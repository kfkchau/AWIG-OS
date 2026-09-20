"""EP-29 W1a — THE DEVICE GROUP'S LAW-DATA, AMENDED. Founding 1.18.0 -> 1.19.0.

WHAT THIS BATTERY HOLDS SHUT, stated once. The device group's three ops — REGISTER-CAPABILITY,
BIND-DEVICE, UNBIND — have been SHIPPED AND CALLABLE since campaign 1, and W1a AMENDS them
rather than creating alongside them (mentor ruling, 2026-08-09). The ground that decides it
alone: a create would leave the undeclared-window silence standing under the names the world
can ALREADY CALL, so safety bought for new names is safety bought for nobody.

THREE THINGS LANDED AND EACH HAS ITS ROW HERE:

  1. `DEV-LAW-BIND` IS DECLARED. It was cited by BIND-DEVICE and UNBIND since campaign 1 and
     declared by NO record — one of THIRTEEN such law ids across devices, memory, scheduling
     and comms. This pass repairs ONLY the one its own amended definitions cite. The other
     twelve are RAISED and deliberately untouched; a row below PINS that they are still
     twelve, so a later pass repairing them by accident is visible rather than silent.
  2. THE INTERMEDIATE STATE IS AUTHORED, NOT INHERITED. Between W1a and W1b a registered,
     bound device attempting I/O meets a gate holding no declaration for the act. The law now
     SAYS what happens — refusal, recorded, citing the terminal rule — rather than relying on
     an engine default. That sentence is written in DEV-LAW-BIND and in BIND-DEVICE's own
     description, because a default filling a declaration gap with permission would be the
     second source of truth this estate refuses.
  3. UNBIND GAINS A `require_prior` ON BIND-DEVICE. An existing check kind PARAMETERIZED: no
     new check kind, no engine line. `OP_CHECKS` is asserted unchanged below.

THE WIDTH OF `T-FAIL-CLOSED-INTERMEDIATE`'s GREEN, DECLARED RATHER THAN LEFT TO BE READ WIDE.
Its red world is AN ENGINE DEFAULT GRANTING THE ACT, and that world is exhibited here. It is
GREEN BY CONSTRUCTION against the SECOND mechanism — A GATE NEVER CONSULTED — because a
default grants and a bypass never asks. The bypass's coverage home is W3's shim-chain rows
(no I/O record without a bind; interposition IS the claim that device traffic reaches the gate
at all), which are not in this stage. Named so the green is read at its true width.

WHAT THIS BATTERY DOES NOT COVER, pinned rather than described:
  * The I/O WINDOW DECLARATIONS themselves. They declare against the notification-surface
    inventory, which is a guest fact (W0g), and a window declared before its surfaces are
    established is law authored against a world nobody has read. W1b's, when its ground exists.
  * Whether a capability registration MUST enumerate what it covers. `device_class` and
    `capabilities` are declared OPTIONAL here — the true statement about the op and its
    callers. `required` would be a WIDENING of the law reddening nine out-of-fence call sites,
    and it is RAISED, not taken.
  * Whether the caller of UNBIND must be the actor that bound. It need not be, today, and that
    is why UNBIND is NOT declared `act_kind: release` — see TheReleaseClassMembershipIsEnumerated.

Runs on this box: `python3 -m unittest discover -s tests -p 'test_ep29.py'`

[BODY GREW, HEADER SAYS SO — 2026-08-12, EP-29 STAGE 2. Everything above describes W1a and
still holds unchanged. This file now ALSO carries STAGE 2's W0g establishment: the guest's
virtio validation set and the notification surfaces, driven at the guest through the
estate's own `src/observe/windows.py` probes. STAGE 2's W1b — the I/O window law — DID NOT
LAND: W0g established that no available surface sees device I/O and that the one surface
whose class is I/O arrivals is unavailable, so the window declarations had no referent and
the pass took C0's third state, STOP-AND-REPORT (ADDENDUM 5 §4), which is GREEN. The
founding therefore stands byte-unchanged at 1.19.0 — the ruled outcome for a stopped pass,
not the failing outcome for a landed one. The block at the foot of this file states it at
length; this bracket exists so a reader of the header is not told a stale story, which is
§A45's class and has cost this estate three documented instances.]
"""

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import era_pin                                              # noqa: E402  (the era-pin home, EP-28Z)
from test_ep28f import commit_identity                      # noqa: E402  (abbreviation-width home, MAINT-2)
from founding import install as install_module              # noqa: E402
from kernel import opdefs                                   # noqa: E402
from kernel.boot import build_kernel                        # noqa: E402
from kernel.errors import OpError                           # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")

#: THE ERA PIN. The commit whose tree holds the 1.18.0 pack — W1a's own BEFORE state,
#: captured before any write (§A53: `git checkout --` no longer undoes a write, so the commit
#: is taken rather than trusted). The differential below varies EXACTLY ONE THING: the pack
#: the ONE loader reads. Two loaders raced against each other would make every divergence
#: ambiguous, which is the shape EP-24B ruled against.
#:
#: [RENAMED — board item STALE-RELATIVE-CONSTANT (:575, :628, :780), 2026-08-15. WAS:
#: `BEFORE_COMMIT` / `OLD_VERSION` / `NEW_VERSION`. NOT ONE VALUE MOVED and no assertion
#: was wrong: every row below asserts about HISTORICAL commits, which genuinely carry these
#: versions. THE HAZARD WAS THE NAME. A constant called `NEW_VERSION` named W1a's after
#: (1.19.0) while the live founding walked to 1.24.0 — five transitions — so the next reader
#: reaching for "the current founding version" got a stale one WITH A GREEN TEST UNDER IT,
#: and "this pass's own BEFORE" in the prose above named a pass the reader had to guess.
#: The cure is not a warning, which is a note to a reader and not a mechanism: it is that
#: the NAME now states WHICH TRANSITION it belongs to, so it cannot go stale when 1.25.0
#: lands — the same shape every later era pin in this file already used (`W1B_`, `W2B_`,
#: `W3A_`, `W3A3_`), from which these three names are derived rather than invented.
#: SCOPE NOTE: `BEFORE_COMMIT` was renamed with its two siblings, though the board item
#: named only the version pair. It is the third member of the SAME W1a triple, carried the
#: SAME unqualified-name defect, and leaving it bare would have left one era pin in this
#: file spelled unlike every other — and unlike its own two siblings.]
W1A_BEFORE_COMMIT = "9d0822ce5f552d74ddb1c135621f4f9e3f67e6cb"
W1A_BEFORE_VERSION = "1.18.0"
W1A_AFTER_VERSION = "1.19.0"

#: The act class an intermediate-state device I/O attempt names. It holds NO definition at
#: 1.19.0 BY DESIGN — W1b declares the windows, and until then this law permits nothing.
UNDECLARED_IO_ACT = "DEVICE-IO-WINDOW-WRITE"

DEVICE_OPS = ("REGISTER-CAPABILITY", "BIND-DEVICE", "UNBIND")

#: THE DANGLING-LAW LEDGER. Every law id this pass found CITED BY AN OP AND DECLARED BY NO
#: RECORD, mapped to THE UNIT THAT CURED IT, or to `None` while it still dangles. PINNED so
#: that a later pass repairing one BY MOMENTUM is visible rather than absorbed.
#:
#: [DOCUMENTED FLIP — EP-30-C4R, 2026-08-26, §A57 cause-mapped repair, board :2128.
#: CAUSE: EP-30-C4 declared `COMM-LAW-SHARE-GRANT`, which its own §3 A6 says in writing it
#: would do — "`COMM-LAW-SHARE-GRANT` moves out of the dangling set by being created here".
#: THE ROW IS THE GROWTH FENCE AND IT FIRED CORRECTLY: it caught a thirteenth being cured and
#: went red. What it COULD NOT DO is tell a PLANNED cure from momentum, because it held A SET
#: AND NOT A LEDGER OF CAUSES, and a set has nowhere to put a reason.
#: ASSERTED: the same fence over a LEDGER. The standing population is COMPUTED from the
#: entries with no curer, and EVERY CURE MUST NAME ITS UNIT.
#: SUPERSEDED: the flat tuple, and the name that stored its size.
#: REMAINS TRUE, AND STRICTER: a thirteenth cured by momentum STILL REDS, because momentum
#: cannot supply a unit name; and a law recorded as cured that still dangles now reds too,
#: which the old form could not ask at all.
#: GIVEN UP: nothing. Shrink-only in the unrepaired direction still holds — an id leaves the
#: standing population by a RULING recorded as a curer here, never by a deletion.]
#:
#: THE RENAME IS PART OF THE SAME ACT AND IT IS NOT COSMETIC. The old name was
#: `THE_TWELVE_LEFT_STANDING` and the population is now ELEVEN. **A NAME THAT STATES A COUNT
#: IS A STORED FIGURE**, and this estate computes figures rather than storing them; leaving an
#: eleven called twelve would have filed today's lesson and breached it in one commit. The
#: new name says WHAT THE MEMBERS ARE and lets the count be read off them.
THE_DANGLING_LAW_LEDGER = {
    "COMM-LAW-CONTRACT": "EP-FND-COMMS-LAWS",   # CURED — the law record it cites now exists. :3162
    "COMM-LAW-QUEUE": "EP-FND-COMMS-LAWS",   # CURED — the law record it cites now exists. :3162
    "COMM-LAW-SHARE-GRANT": "EP-30-C4",   # CURED — the law record it cites now exists. :2078
    "MEM-LAW-ALLOC": None,
    "MEM-LAW-BUDGET": "EP-31",   # CURED — the law record it cites now exists. :2706
    "MEM-LAW-EVICT": None,
    "MEM-LAW-PROTECT": None,
    "SCHED-LAW-ADMIT": None,
    "SCHED-LAW-HALT": None,
    "SCHED-LAW-KILL-CHAIN": None,
    "SCHED-LAW-ORDER": None,
    "SCHED-LAW-PRIORITY": None,
}

#: COMPUTED, NEVER STORED — the ids still cited by an op and declared by no record.
THE_LAWS_LEFT_STANDING = tuple(sorted(
    law for law, cured_by in THE_DANGLING_LAW_LEDGER.items() if cured_by is None))


def pack_at(commit):
    """The pack as of one commit, read through git. The era's own bytes, never the live tree.

    [DOCUMENTED FLIP — EP-28Z, 2026-08-12. CAUSE: this body was one of EIGHTEEN copies of
    the era-pin act across TEN test files, re-derived once per pass because charter §A57
    states the duty and states no method (board :410). ASSERTED: a local `git show` spawn.
    SUPERSEDED: the same act, from `tests/era_pin.py`, the one home. REMAINS TRUE: every
    caller in this file is unchanged and the failure mode is unchanged — `check_output`
    raised `CalledProcessError` on an unresolvable pin and `missing="raise"` is that same
    behaviour by name. GIVEN UP: nothing. The name `pack_at` is kept so no call site moves.]
    """
    return era_pin.pack_at(commit)


def live_pack():
    with open(PACK_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def ops_of(pack):
    return {r["payload"]["name"]: r["payload"]["definition"]
            for st in pack["steps"] for r in st["records"] if r.get("action") == "CREATE-OP"}


def rules_of(pack):
    return {r["payload"]["rule_id"]: r["payload"]
            for st in pack["steps"] for r in st["records"] if r.get("action") == "CREATE-RULE"}


class _World:
    """A booted world. `pack` may be a dict, in which case it is installed INSTEAD of the live
    one by patching the installer's own loader — the ONE loader, handed a different source."""

    def __init__(self, pack=None):
        self.dir = tempfile.mkdtemp(prefix="ep29-")
        self.path = os.path.join(self.dir, "record.jsonl")
        if pack is None:
            self.store, self.gate, self.views = build_kernel(self.path)
        else:
            original = install_module.load_pack
            install_module.load_pack = lambda *a, **k: copy.deepcopy(pack)
            try:
                self.store, self.gate, self.views = build_kernel(self.path)
            finally:
                install_module.load_pack = original

    def call(self, op, actor="owner", **params):
        return self.gate.execute(op, actor, params)

    def refusals(self):
        return [e for e in self.store.all() if e.get("refused")]


# =======================================================================================
class TheFailClosedIntermediateState(unittest.TestCase):
    """T-FAIL-CLOSED-INTERMEDIATE (EP-29 ADDENDUM 4 §4, sharpened at §5).

    Through the real path: register and bind under W1a's landed law, then attempt a device
    I/O act with NO declared window. The gate REFUSES and the record holds the refusal citing
    the absence.

    ITEM-21 NON-VACUITY: THE BIND IS PROVEN LIVE BEFORE THE REFUSAL IS READ. A refusal over a
    dead bind is the empty world passing, and it reads identically on the page."""

    def setUp(self):
        self.w = _World()

    def test_the_bind_is_live_before_any_refusal_is_read(self):
        """THE NON-VACUITY GUARD. If this row skips or fails, the row below states nothing."""
        self.w.call("REGISTER-CAPABILITY", driver="drv-a", device_class="block",
                    capabilities=["irq:11"])
        rec = self.w.call("BIND-DEVICE", device="dev0", driver="drv-a")
        self.assertEqual(rec["action"], "BIND-DEVICE")
        self.assertEqual(self.w.views.op_definitions()["BIND-DEVICE"]["definition"]["law_cited"],
                         "DEV-LAW-BIND")
        # the DERIVED view, not the record: custody is a computed answer
        from subsystems.devices import DevicesView
        self.assertEqual(DevicesView(self.w.store).bindings(), {"dev0": "drv-a"},
                         "the bind is not live, so a refusal below would be the empty world "
                         "passing")

    def test_a_device_io_act_with_no_declared_window_is_refused_and_recorded(self):
        # [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12. THIS IS C5's FLIP AND IT IS THE POINT OF
        # THE PASS, not an incidental breakage. CAUSE: W1b DECLARED the windows and gave
        # `DEVICE-IO-WINDOW-WRITE` a definition, so that name is no longer an act class the law
        # founds no declaration for and no longer refuses with the terminal rule. ASSERTED:
        # `UNDECLARED_IO_ACT` ("DEVICE-IO-WINDOW-WRITE"). SUPERSEDED: `STILL_UNDECLARED_IO_ACT`
        # ("DEVICE-IO-WINDOW-READ"), an act class that STILL holds no declaration after W1b.
        # REMAINS TRUE, WORD FOR WORD, AND THAT IS WHAT C5 REQUIRES: an act class this law
        # founds no declaration for is permitted by nothing, refuses, and the refusal is
        # RECORDED citing the tip-level terminal rule. THE REFUSAL WAS NARROWED, NEVER REMOVED.
        # GIVEN UP: nothing — the WRITE name's new behaviour is asserted in both directions
        # below at TheWindowAdmissionFlippedAndTheRefusalNarrowed.]
        self.w.call("REGISTER-CAPABILITY", driver="drv-a", device_class="block",
                    capabilities=["irq:11"])
        self.w.call("BIND-DEVICE", device="dev0", driver="drv-a")
        from subsystems.devices import DevicesView
        self.assertEqual(DevicesView(self.w.store).bindings(), {"dev0": "drv-a"})   # live first

        before = len(self.w.store.all())
        with self.assertRaises(OpError) as ctx:
            self.w.call(STILL_UNDECLARED_IO_ACT, device="dev0", bytes=4)
        appended = list(self.w.store.all())[before:]

        self.assertEqual(ctx.exception.rule, "P3-CLOSURE",
                         "the refusal must cite the terminal rule that an act class no "
                         "declaration founds does not exist")
        self.assertEqual(len(appended), 1, "the refusal must be RECORDED, not merely raised")
        self.assertTrue(appended[0]["refused"])
        self.assertEqual(appended[0]["action"], "op-refused")
        self.assertEqual(appended[0]["rule_cited"], "P3-CLOSURE")
        self.assertEqual(dict(appended[0]["payload"])["op"], STILL_UNDECLARED_IO_ACT)

    def test_the_cited_terminal_rule_is_a_DECLARED_law_of_this_founding(self):
        """A refusal citing a law id no record declares is exactly the defect this pass
        repaired one instance of. The terminal rule must not be a second one."""
        self.assertIn("P3-CLOSURE", self.w.views.active_rules())
        self.assertIn("does not exist",
                      dict(self.w.views.active_rules()["P3-CLOSURE"])["text"])

    def test_the_law_ITSELF_says_so_rather_than_the_engine_defaulting(self):
        """§5 item 1: the window-absent case is DECLARED, written not defaulted. The law-data
        carries the sentence, so the answer does not depend on the engine's behaviour."""
        law = dict(self.w.views.active_rules()["DEV-LAW-BIND"])["text"]
        for clause in ("CUSTODY", "NOT I/O", "CITES A WINDOW DECLARATION BY NAME",
                       "PERMITTED BY NOTHING", "REFUSES"):
            self.assertIn(clause, law, "DEV-LAW-BIND does not state %r" % clause)
        bind = self.w.views.op_definitions()["BIND-DEVICE"]["definition"]["description"]
        self.assertIn("GRANTS CUSTODY AND NOT I/O", bind)


class TheRedWorldForTheIntermediateState(unittest.TestCase):
    """THE RED WORLD, EXHIBITED RATHER THAN DESCRIBED (the red-world law): AN ENGINE DEFAULT
    GRANTING THE ACT — the comforting fallback — must RED the row above.

    Constructed by giving the undeclared act class a DEFINITION that admits it with no window
    check, which is exactly what a permissive default would look like from the caller's side.
    IT REACHES ONLY THE NEW CLAUSE: the register and the bind are untouched and still pass, so
    a red here is the I/O clause going red and nothing else."""

    def _world_where_a_default_grants(self):
        pack = live_pack()
        step = [s for s in pack["steps"] if s["step"] == "08-op-definitions"][0]
        step["records"].append({
            "actor": "PC_RUNTIME", "action": "CREATE-OP",
            "object": "op:%s" % UNDECLARED_IO_ACT, "rule_cited": "CAP-IS-LAW",
            "payload": {
                "kind": "op_definition", "rule_id": "op:%s" % UNDECLARED_IO_ACT,
                "polarity": "+", "name": UNDECLARED_IO_ACT, "tier": "owner",
                "text": "a planted permissive default, minted in memory for this red world",
                "definition": {
                    "description": "THE COMFORTING FALLBACK: admits device I/O with no window",
                    "params": {"device": "required"},
                    "law_cited": "DEV-LAW-BIND",
                    "object_param": "device",
                    "payload_from": ["device"],
                    "structural_params": ["device"],   # device id, object_param, read inline (vocab door — design/46 member 2; mirrors the production op)
                    "cell": "S",   # C6 P8 (L28): a probe op founded against the CELL-LAW pack must declare a cell (structured record-mechanic, S) or the founding door refuses it
                    "checks": [],
                },
            },
        })
        return _World(pack)

    def test_the_red_world_admits_what_the_landed_law_refuses(self):
        w = self._world_where_a_default_grants()
        w.call("REGISTER-CAPABILITY", driver="drv-a", device_class="block", capabilities=["x"])
        w.call("BIND-DEVICE", device="dev0", driver="drv-a")
        rec = w.call(UNDECLARED_IO_ACT, device="dev0")      # ADMITTED — the row above would RED
        self.assertEqual(rec["action"], UNDECLARED_IO_ACT)
        self.assertFalse(rec.get("refused"))

    def test_the_red_world_leaves_the_earlier_clauses_passing(self):
        """A RED WORLD NAMES WHICH CLAUSE IT MAKES FAIL and must be unreachable by every clause
        that already passed. Register and bind still succeed here, so the only thing this world
        moves is the I/O clause."""
        w = self._world_where_a_default_grants()
        w.call("REGISTER-CAPABILITY", driver="drv-a", device_class="block", capabilities=["x"])
        w.call("BIND-DEVICE", device="dev0", driver="drv-a")
        from subsystems.devices import DevicesView
        self.assertEqual(DevicesView(w.store).bindings(), {"dev0": "drv-a"})
        with self.assertRaises(OpError):                     # the capability chain still bites
            w.call("BIND-DEVICE", device="dev1", driver="never-registered")


# =======================================================================================
class TheDeviceLawIsDeclared(unittest.TestCase):
    """T-DEV-LAW-DECLARED, as a DIFFERENTIAL varying exactly ONE thing: the pack ONE loader
    reads. Before this pass a lawful BIND-DEVICE cited a law id no record declared."""

    def test_before_this_pass_the_cited_law_resolved_to_nothing(self):
        old = _World(pack_at(W1A_BEFORE_COMMIT))
        self.assertEqual(pack_at(W1A_BEFORE_COMMIT)["founding_version"], W1A_BEFORE_VERSION)
        self.assertNotIn("DEV-LAW-BIND", old.views.active_rules())
        old.call("REGISTER-CAPABILITY", driver="d")
        rec = old.call("BIND-DEVICE", device="dev0", driver="d")
        self.assertEqual(rec["rule_cited"], "DEV-LAW-BIND")
        self.assertIsNone(old.views.active_rules().get(rec["rule_cited"]),
                          "the BEFORE world is supposed to exhibit the defect")

    def test_after_this_pass_the_cited_law_resolves_to_a_record(self):
        # [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12, charter §A57. CAUSE: the founding moved
        # 1.19.0 -> 1.20.0, so this row's guard against reading the wrong world named the wrong
        # world. ASSERTED: `W1A_AFTER_VERSION` (W1a's after, 1.19.0; spelled `NEW_VERSION` at the
        # time of this flip, renamed 2026-08-15 by STALE-RELATIVE-CONSTANT — value untouched).
        # SUPERSEDED: `W1B_AFTER_VERSION`.
        # REMAINS TRUE, and STAYS LIVE deliberately: the claim is that a lawful BIND-DEVICE's
        # cited law resolves TO A RECORD IN THE SHIPPED FOUNDING, which is a property W1b must
        # not break and which an era pin would stop checking. GIVEN UP: nothing.]
        # [DOCUMENTED FLIP — EP-28ZD, 2026-08-13, charter §A57. CAUSE: the founding moved
        # 1.20.0 -> 1.21.0, so the VERSION half of this row named a world that no longer
        # exists. ASSERTED: `live_pack()`. SUPERSEDED: `pack_at(W1B_AFTER_COMMIT)`, W1b's own
        # era. REMAINS TRUE AND STAYS LIVE: everything below the version line — a lawful
        # BIND-DEVICE's cited law still resolves to a record in the SHIPPED founding, checked
        # against `_World()`, which is the live tree. Only the guard against reading the wrong
        # world moved to the era it is a guard about. GIVEN UP: nothing.]
        new = _World()
        self.assertEqual(pack_at(W1B_AFTER_COMMIT)["founding_version"], W1B_AFTER_VERSION)
        self.assertIn("DEV-LAW-BIND", new.views.active_rules())
        new.call("REGISTER-CAPABILITY", driver="d")
        rec = new.call("BIND-DEVICE", device="dev0", driver="d")
        self.assertEqual(rec["rule_cited"], "DEV-LAW-BIND")
        self.assertIsNotNone(new.views.active_rules().get(rec["rule_cited"]))

    def test_exactly_one_of_the_thirteen_was_repaired_and_the_twelve_are_pinned(self):
        """THE GROWTH FENCE, AS A ROW. If a later pass repairs a thirteenth by momentum this
        goes red and names it, rather than the repair being absorbed and forgotten.

        [DOCUMENTED FLIP — EP-30-C4R, 2026-08-26, board :2128. The fence now runs over
        `THE_DANGLING_LAW_LEDGER` rather than a flat tuple; the cause is recorded at that
        constant. THE ROW'S NAME IS KEPT because it is what this pass DID — repaired exactly
        one of thirteen — and that is a historical fact which does not move. What moved is the
        POPULATION IT PINS, and that population is now computed rather than stored.]"""
        w = _World()
        rules = w.views.active_rules()
        ops = ops_of(live_pack())
        cited = {d.get("law_cited") for d in ops.values()}
        undeclared = sorted(c for c in cited if c not in rules)
        self.assertEqual(tuple(undeclared), THE_LAWS_LEFT_STANDING,
                         "the set of cited-but-undeclared law ids moved; this pass repaired "
                         "exactly one (DEV-LAW-BIND) and raised the rest")
        # EVERY CURE NAMES ITS UNIT, AND THE LEDGER IS CHECKED IN BOTH DIRECTIONS. A law
        # recorded as cured that still dangles is a claim the record does not support; a law
        # recorded as cured whose rule is not declared is the same claim from the other side.
        for law, cured_by in THE_DANGLING_LAW_LEDGER.items():
            if cured_by is None:
                continue
            self.assertNotIn(law, undeclared,
                             f"{law} is recorded as cured by {cured_by} and still dangles")
            self.assertIn(law, rules,
                          f"{law} is recorded as cured by {cured_by} and is not declared")
        self.assertNotIn("DEV-LAW-BIND", undeclared)
        # POSITIVE CONTROL on the walk that produced the twelve: it also finds declared ones.
        self.assertGreater(len([c for c in cited if c in rules]), 0,
                           "the walk cannot distinguish declared from undeclared, so its "
                           "twelve is uninterpretable")


# =======================================================================================
class TheUnbindCitesAPriorBind(unittest.TestCase):
    """C6's act: an EXISTING check kind PARAMETERIZED on a shipped op. Both directions."""

    def test_an_unbind_of_a_never_bound_device_refuses_citing_the_device_law(self):
        w = _World()
        with self.assertRaises(OpError) as ctx:
            w.call("UNBIND", device="never-bound")
        self.assertEqual(ctx.exception.rule, "DEV-LAW-BIND")
        self.assertIn("cites a prior bind", ctx.exception.message)
        self.assertTrue(w.refusals()[-1]["refused"])

    def test_an_unbind_of_a_bound_device_is_PERMITTED(self):
        """NON-VACUITY FOR THE ROW ABOVE: a check that refuses everything is not a check, and
        a refusal row over a dead op reads exactly like a working one."""
        w = _World()
        w.call("REGISTER-CAPABILITY", driver="drv-a")
        w.call("BIND-DEVICE", device="dev0", driver="drv-a")
        rec = w.call("UNBIND", device="dev0")
        self.assertEqual(rec["action"], "UNBIND")
        from subsystems.devices import DevicesView
        self.assertEqual(DevicesView(w.store).bindings(), {})

    def test_the_checks_WIDTH_is_pinned_rather_than_assumed(self):
        """`require_prior` reads HISTORY, not current state, so a SECOND unbind of an already
        unbound device is PERMITTED. That is stated in the definition and pinned here, because
        a reader who takes this check for 'the device is currently bound' has read a stronger
        law than the one that landed.

        [DOCUMENTED FLIP — EP-30-W1b, 2026-08-16, the declared stream key's first use.
        ASSERTED: `len(by_action("UNBIND")) == 2` — the two unbind records counted in the
        stream named after their own door, which was the only stream they could be in.
        SUPERSEDED: the same two records counted WHERE THEY NOW LIVE — inside BIND-DEVICE's
        stream — and identified BY THEIR RECORDED `action`. op:UNBIND declares
        `record_stream: BIND-DEVICE`, so `by_action("UNBIND")` is now 0 and a literal moved
        to 0 would leave this row asserting NOTHING AT ALL.
        REMAINS TRUE and unchanged in subject: A SECOND UNBIND OF AN ALREADY-UNBOUND DEVICE IS
        PERMITTED, because the check reads history and not state. Two acts, two records.
        GIVEN UP: nothing. THE ROW GAINED A JOB — counting unbinds by their RECORDED ACTION
        inside the GRANTING ACT'S stream is `:918` constraint 2, the door is never erased,
        stated as a number. If a later hand made the stream key overwrite `action` instead of
        adding beside it, these two records would become indistinguishable from binds and this
        count would read 0 while every derived view still agreed. This row is that witness.]"""
        w = _World()
        w.call("REGISTER-CAPABILITY", driver="drv-a")
        w.call("BIND-DEVICE", device="dev0", driver="drv-a")
        w.call("UNBIND", device="dev0")
        w.call("UNBIND", device="dev0")            # permitted — history, not state
        unbinds = [e for e in w.store.by_action("BIND-DEVICE") if e["action"] == "UNBIND"]
        self.assertEqual(len(unbinds), 2,
                         "a second unbind of an already-unbound device was not permitted, or "
                         "its record does not carry UNBIND as the act that wrote it")
        self.assertEqual([e.get("record_stream") for e in unbinds],
                         ["BIND-DEVICE", "BIND-DEVICE"],
                         "the unbind records are not in the granting act's stream")
        self.assertIn("does NOT refuse a second unbind",
                      ops_of(live_pack())["UNBIND"]["description"])

    def test_the_before_world_permitted_it_which_is_what_makes_this_a_change(self):
        old = _World(pack_at(W1A_BEFORE_COMMIT))
        rec = old.call("UNBIND", device="never-bound")       # no check existed
        self.assertEqual(rec["action"], "UNBIND")


# =======================================================================================
class TheDeclarationsAreComplete(unittest.TestCase):
    """C7 on the corrected population: EVERY DEFINITION THIS PASS AUTHORS OR AMENDS — three,
    not zero. Every parameter that reaches an amended op's record is DECLARED in `params`."""

    def test_every_field_the_three_amended_ops_write_is_a_declared_parameter(self):
        ops = ops_of(live_pack())
        for name in DEVICE_OPS:
            d = ops[name]
            known = set(d.get("params") or {}) | set(d.get("param_defaults") or {})
            written = set(d.get("payload_from") or list((d.get("params") or {}).keys()))
            self.assertEqual(written - known, set(),
                             "%s writes %r to its record without declaring it as a parameter — "
                             "a parameter form taken by silence" % (name, sorted(written - known)))

    def test_the_before_world_had_two_undeclared_parameters_and_that_is_the_change(self):
        """THE DIVERGENCE THIS ROW EXISTS FOR. Without it, the row above passes on a pack that
        never had the defect and proves nothing about the repair."""
        old = ops_of(pack_at(W1A_BEFORE_COMMIT))["REGISTER-CAPABILITY"]
        known = set(old.get("params") or {})
        written = set(old.get("payload_from") or [])
        self.assertEqual(sorted(written - known), ["capabilities", "device_class"])

    def test_the_completeness_walk_can_fail(self):
        """A PLANTED CASE. The walk above returns an empty set; an empty set from a walk that
        cannot report a non-empty one is not a result."""
        d = copy.deepcopy(ops_of(live_pack())["BIND-DEVICE"])
        d["payload_from"] = d["payload_from"] + ["planted_undeclared_field"]
        known = set(d.get("params") or {}) | set(d.get("param_defaults") or {})
        written = set(d["payload_from"])
        self.assertEqual(sorted(written - known), ["planted_undeclared_field"])


class TheVocabularyRateHeld(unittest.TestCase):
    """C6: no new check kind. The check vocabulary is engine law and a genuinely new kind is
    the §5 owner gate's, never a pass's quiet addition."""

    PINNED = ("require_prior", "sight", "ceiling", "consistency", "sop", "definition_ref",
              "entry_ref", "space_tree", "fingerprint", "binding", "kind", "contains")

    def test_OP_CHECKS_is_unchanged_by_this_pass(self):
        # [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14, charter §A57. CAUSE: the owner ruled the
        # check vocabulary grows twelve to thirteen and this pass landed `prior_value`, so a row
        # reading the LIVE tuple against W1a's twelve was falsified by a decision W1a could not
        # have known about. ASSERTED: `opdefs.OP_CHECKS`, the live tree. SUPERSEDED:
        # `kinds_at(W3A_AFTER_ERA_COMMIT)`, the vocabulary as it stood through W1a's whole life
        # and up to this pass's first write. REMAINS TRUE, and it is the row's actual claim: W1a
        # added NO check kind — it parameterized an existing one, which is a fact about W1a's
        # landing and was never a fact about today's tree. GIVEN UP: nothing — the LIVE
        # vocabulary is asserted, at thirteen and by name, by this pass's own battery
        # (TheVocabularyGrewBY_EXACTLY_THE_ONE_RULED_KIND), which is where that era belongs.
        # The constants and `kinds_at` live with the W3a3 section at the foot of this file.]
        self.assertEqual(kinds_at(W3A_AFTER_ERA_COMMIT), self.PINNED)

    #: THE PATHS THE ENGINE CLAIM IS MADE OVER. DIRECTORIES, deliberately, so an engine file
    #: ARRIVING is inside the subject. An enumeration of file names is the other form this
    #: estate uses for a byte-unchanged claim (`era_pin.blob_at` pairs, four rows in this very
    #: file) and it CANNOT see a new file appear — so the form is chosen by the shape of the
    #: subject and never by preference. Unmoved from what the row always read.
    ENGINE_PATHS = ("src/kernel/", "src/bridge/", "src/observe/", "src/subsystems/",
                    "src/founding/install.py", "src/founding/__init__.py")

    #: THE COMMIT W1a's WORK LANDED IN — the commit that CREATED this file, which is W1a's
    #: LAST write; its pack write landed two minutes earlier at `ba125bd` and is inside the
    #: range. Taken by `git log --diff-filter=A`, and a row below re-takes it rather than
    #: trusting this comment.
    W1A_LANDED_AT = "a96a34d"

    #: A RANGE THE ENGINE DID MOVE IN, for the red world below: W3a3's own pre-write commit to
    #: the commit its `src/kernel/opdefs.py` write landed in. CLOSED at both ends, so the world
    #: it names cannot drift as HEAD advances.
    A_RANGE_THE_ENGINE_MOVED_IN = ("be0d00e8", "c5e993a")

    def _engine_diff(self, before, after):
        """THE ONE READER for this claim, so the guard and its red world cannot drift apart —
        a red world driving a DIFFERENT command proves the command and not the guard."""
        out = subprocess.run(
            ["git", "diff", "--stat", "%s..%s" % (before, after), "--"] + list(self.ENGINE_PATHS),
            cwd=REPO, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        return out.stdout.strip()

    def test_the_engine_is_byte_unchanged_by_this_pass(self):
        """The stronger form of the row above: not merely that the vocabulary held, but that
        no engine line moved at all, which is what makes the ruled version test's MINOR
        answer mean what it says.

        [DOCUMENTED FLIP — GUARD-ASKS-THE-WORKING-TREE, 2026-08-14, board `:776`. CAUSE: the
        row asked the WORKING TREE whether anything had moved. Autosync commits every two
        minutes, so the tree is EMPTY before any suite reads it, and the row reported GREEN
        over W3a3 — a pass that moved 204 lines in `src/kernel/opdefs.py`. ASSERTED: the diff
        between W1a's own pre-write commit and W1a's own landing commit, which no commit can
        launder. SUPERSEDED: `git diff` against the working tree. REMAINS TRUE, and it is the
        row's actual claim: W1a moved no engine line. GIVEN UP: nothing — a working-tree read
        never carried the claim in the first place; it carried the two-minute timer.

        THE RANGE IS CLOSED AND NOT OPEN, and that is not a preference. EP-28G's flip on
        `tests/test_ep28h.py` ruled the point already: an open `X..HEAD` range reds by
        construction on the next pass that lawfully touches the paths, and W3a3 is exactly
        such a pass. A row whose world is a past event pins the range that event happened in.

        AND THIS IS THE ERA-PIN THAT WAS OMITTED. Board `:776` records two defects cancelling
        into a pass: §A57's pin was applied to the SIBLING five lines above and not to this
        row, and the instrument that would have shown the omission was already dead. For a
        DIFF row the era-pin IS the closed range — there is nothing else to pin — so this
        repair discharges the omission rather than merely surviving it.]"""
        self.assertEqual(
            self._engine_diff(W1A_BEFORE_COMMIT, self.W1A_LANDED_AT), "",
            "W1a moved engine lines inside its own range")

    def test_the_range_the_engine_row_reads_is_W1as_OWN_and_is_CLOSED(self):
        """§A39 on the row above: a claim is only as good as the range it is taken over, so
        the range is ASSERTED rather than assumed. Both ends must resolve, the near end must
        be an ancestor of the far end, and the far end must be W1a's own landing rather than
        whatever HEAD happens to be — otherwise the diff above could be empty for the wrong
        reason, which is the entire defect being repaired here."""
        for rev in (W1A_BEFORE_COMMIT, self.W1A_LANDED_AT):
            out = subprocess.run(["git", "rev-parse", "--verify", rev + "^{commit}"],
                                 cwd=REPO, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, "%s does not resolve: %s" % (rev, out.stderr))
        anc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", W1A_BEFORE_COMMIT, self.W1A_LANDED_AT],
            cwd=REPO, capture_output=True, text=True)
        self.assertEqual(anc.returncode, 0,
                         "W1a's pre-write commit is not an ancestor of its landing commit")
        created = subprocess.run(
            ["git", "log", "--format=%h", "--diff-filter=A", "--", "tests/test_ep29.py"],
            cwd=REPO, capture_output=True, text=True)
        self.assertEqual(created.returncode, 0, created.stderr)
        # [MAINT-2, 2026-08-26. THE RANGE WAS RIGHT AND THE COMPARISON WAS WRONG. `%h`
        # emits eight characters on this repository and `W1A_LANDED_AT` is seven, so this
        # row asserted STRING EQUALITY OF AN ABBREVIATION where its own docstring says
        # IDENTITY — `a96a34d` and `a96a34da` are one commit. Both sides resolve to full
        # object names now. What the row claims is unchanged: exactly one commit created
        # this file, and it is W1a's landing commit.]
        self.assertEqual([commit_identity(h) for h in created.stdout.split()],
                         [commit_identity(self.W1A_LANDED_AT)],
                         "the far end is not the commit W1a created this file in")

    def test_the_engine_guard_REDS_WHEN_A_LINE_MOVED(self):
        """THE NEGATIVE-RESULT TEST, and it is the whole reason this row exists. The guard
        above passes by PRODUCING NO OUTPUT, and a guard that cannot produce output is not a
        guard — which is exactly how the working-tree form reported green over a pass that
        moved 204 lines. Driven through the SAME reader over a range the engine DID move in,
        it must report, and the guard's own assertion must FAIL.

        The literals are HAND-READ from `git diff --numstat be0d00e8 c5e993a` over the same
        paths — a different flag from the one the row runs — and never produced by running
        this row. An expectation produced by running the code is a recording of behaviour."""
        before, after = self.A_RANGE_THE_ENGINE_MOVED_IN
        moved = self._engine_diff(before, after)
        self.assertIn("src/kernel/opdefs.py", moved)
        self.assertIn("204 insertions(+), 1 deletion(-)", moved)
        with self.assertRaises(AssertionError):
            self.assertEqual(moved, "", "the guard's own assertion, over a world that moved")

    def test_the_red_worlds_range_is_CLOSED_so_the_world_it_names_cannot_drift(self):
        """The red world is only a red world while its range still holds the move. Both ends
        resolve and neither is HEAD, so a later pass cannot quietly empty it."""
        for rev in self.A_RANGE_THE_ENGINE_MOVED_IN:
            out = subprocess.run(["git", "rev-parse", "--verify", rev + "^{commit}"],
                                 cwd=REPO, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, "%s does not resolve: %s" % (rev, out.stderr))
        self.assertEqual(self.A_RANGE_THE_ENGINE_MOVED_IN[0], W3A3_BEFORE_COMMIT[:8],
                         "the red world's near end is not W3a3's own pre-write commit")

    def test_every_check_the_amended_ops_declare_is_in_the_pinned_vocabulary(self):
        ops = ops_of(live_pack())
        kinds = {c["check"] for n in DEVICE_OPS for c in (ops[n].get("checks") or [])}
        self.assertTrue(kinds, "no checks at all would make this row vacuous")
        self.assertEqual(kinds - set(self.PINNED), set())


class TheReleaseClassMembershipIsEnumerated(unittest.TestCase):
    """ADDENDUM 1 item 4: the release-exemption class is applied to this group's release-shaped
    rows AT AUTHORING, and membership is ENUMERATED PER GROUP, NEVER ASSUMED.

    THE ENUMERATION AND ITS ANSWER: UNBIND is release-SHAPED and is NOT a release. Its whole
    effect ends a binding, but it takes only `device`, so ANY actor may end ANY actor's
    binding — which moves another actor's holdings. Declaring `act_kind: release` would be a
    FALSE sentence about what the op IS, chosen for the branch it takes. That is the
    stored-table trap in the vocabulary dimension and it is refused here."""

    def test_no_device_op_declares_act_kind(self):
        ops = ops_of(live_pack())
        for name in DEVICE_OPS:
            self.assertNotIn("act_kind", ops[name],
                             "%s declares act_kind; the enumeration below says it must not"
                             % name)

    def test_the_reason_is_DRIVEN_and_not_merely_asserted(self):
        """The claim 'any actor may end any actor's binding' is a fact about the landed law,
        so it is exhibited rather than argued."""
        w = _World()
        w.call("REGISTER-CAPABILITY", "alice", driver="drv-a")
        w.call("BIND-DEVICE", "alice", device="dev0", driver="drv-a")
        rec = w.call("UNBIND", "mallory", device="dev0")     # a different actor entirely
        self.assertEqual(rec["actor"], "mallory")
        from subsystems.devices import DevicesView
        self.assertEqual(DevicesView(w.store).bindings(), {},
                         "mallory could not end alice's binding, so the ground for refusing "
                         "the release declaration has moved and must be re-derived")

    def test_the_refusal_of_the_declaration_is_recorded_in_the_definition_itself(self):
        self.assertIn("NOT declared `act_kind: release`",
                      ops_of(live_pack())["UNBIND"]["description"])


class TheFoundingMoved(unittest.TestCase):
    """The founding MOVES here and byte-unchanged is the FAILING outcome for W1a."""

    def test_the_pack_version_moved_one_MINOR(self):
        # [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12, charter §A57. CAUSE: W1a's move is
        # 1.18.0 -> 1.19.0 FOREVER, and this row read its AFTER side off the live tree, which
        # stopped being W1a's era the moment W1b moved the founding to 1.20.0 — the §A57 class
        # exactly, one stage on from W1a doing this to EP-28I. ASSERTED: `live_pack()`.
        # SUPERSEDED: `pack_at(W1B_BEFORE_COMMIT)`, this pass's own pre-write commit, verified
        # to hold 1.19.0 before it was written down. REMAINS TRUE: W1a moved the founding by one
        # MINOR, unchanged. GIVEN UP: nothing — W1b's own move is asserted LIVE below at
        # TheFoundingMovedAgainAtStage2.]
        self.assertEqual(pack_at(W1A_BEFORE_COMMIT)["founding_version"], W1A_BEFORE_VERSION)
        self.assertEqual(pack_at(W1B_BEFORE_COMMIT)["founding_version"], W1A_AFTER_VERSION)

    def test_the_founding_designation_record_carries_the_new_version(self):
        # [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12, charter §A57, same cause as the row above:
        # W1a's designation record carried 1.19.0 in W1a's era. ASSERTED: `_World()`, live.
        # SUPERSEDED: a world booted from W1a's own era pack. REMAINS TRUE: the designation
        # record carries the pack's version rather than a constant of its own.]
        w = _World(pack_at(W1B_BEFORE_COMMIT))
        fs = [e for e in w.store.all() if e["action"] == "FOUND-STORE"][0]
        self.assertEqual(dict(fs["payload"])["founding_version"], W1A_AFTER_VERSION)

    def test_the_old_pack_byte_unchanged_still_loads_under_this_law(self):
        """THE RULED VERSION TEST, as a standing row rather than only a one-off run: this is
        what makes the MINOR answer re-checkable by anyone later.

        HONEST WIDTH: with zero engine lines moved this cannot fail, and that is stated in the
        pack's own description rather than hidden. The row below is what carries the weight."""
        install_module._validate(install_module.records(pack_at(W1A_BEFORE_COMMIT)))

    def test_the_loader_that_accepted_it_can_refuse(self):
        """Without this, the row above is an instrument that cannot report its own failure."""
        p = pack_at(W1A_BEFORE_COMMIT)
        for st in p["steps"]:
            for r in st["records"]:
                if (r.get("payload") or {}).get("name") == "UNBIND":
                    r["payload"]["definition"]["checks"] = [
                        {"check": "planted_unknown_kind", "cite": "DEV-LAW-BIND"}]
        with self.assertRaises(Exception) as ctx:
            install_module._validate(install_module.records(p))
        self.assertIn("planted_unknown_kind", str(ctx.exception))


class TheDeviceGroupStillFolds(unittest.TestCase):
    """The derived views over the amended ops, end to end. A law change that breaks the fold
    it governs would otherwise show only in a suite this stage cannot run."""

    def test_register_bind_unbind_round_trips_through_the_derived_views(self):
        w = _World()
        w.call("REGISTER-CAPABILITY", driver="drv-a", device_class="block",
               capabilities=["irq:11", "mmio:0xfe000000-0xfe000fff"])
        w.call("BIND-DEVICE", device="dev0", driver="drv-a")
        from subsystems.devices import DevicesView
        v = DevicesView(w.store)
        self.assertEqual(v.bindings(), {"dev0": "drv-a"})
        self.assertEqual(v.capabilities()["drv-a"]["device_class"], "block")
        # the store hands back an IMMUTABLE view, so a declared list reads as a tuple. Compared
        # as a sequence of the same members rather than as a list, because the container kind is
        # the store's answer and not this op's declaration.
        self.assertEqual(tuple(v.capabilities()["drv-a"]["capabilities"]),
                         ("irq:11", "mmio:0xfe000000-0xfe000fff"))
        w.call("UNBIND", device="dev0")
        self.assertEqual(v.bindings(), {})

    def test_a_bare_registration_still_registers_and_enumerates_nothing(self):
        """`device_class` and `capabilities` are declared OPTIONAL, so a bare registration is
        lawful — and the law says what a bare one covers: nothing.

        AND THE RECORD SAYS SO EXPLICITLY: a bare registration records `capabilities: None` —
        the record STATES that it enumerated nothing rather than being silent about it.

        THIS WAS ALREADY TRUE AT 1.18.0 AND MY FIRST VERSION OF THIS ROW CLAIMED OTHERWISE.
        Both fields were already in `payload_from`, and the payload builder writes every
        `payload_from` field whether or not it is a declared parameter — so the RECORD SHAPE IS
        UNCHANGED BY THIS AMENDMENT. Pinned in the row below, because the honest statement of
        what W1a did is narrower and sharper than what I first asserted: it changed what the
        founding SAYS about the op and changed no byte of any record."""
        w = _World()
        w.call("REGISTER-CAPABILITY", driver="drv-bare")
        from subsystems.devices import DevicesView
        cap = DevicesView(w.store).capabilities()["drv-bare"]
        self.assertIn("capabilities", cap)
        self.assertIsNone(cap["capabilities"])
        self.assertIsNone(cap["device_class"])
        self.assertIn("ENUMERATES NOTHING",
                      dict(w.views.active_rules()["DEV-LAW-BIND"])["text"])

    def test_the_RECORD_is_byte_for_byte_what_it_was_and_only_the_DECLARATION_moved(self):
        """THE AMENDMENT'S TRUE WIDTH, PINNED — and it is narrower than this builder first
        asserted, which is why it is a row rather than a sentence.

        W1a declared `device_class` and `capabilities` as parameters. It did NOT change what a
        registration records: both fields were already in `payload_from` at 1.18.0, so both
        worlds write `None` for a bare registration. WHAT MOVED IS WHAT THE FOUNDING SAYS: at
        1.18.0 the two fields reached the record while appearing in NO params entry, so the
        founding made no statement at all about whether they may be absent; at 1.19.0 it states
        `optional`, which is a decision where there was silence.

        The distinction this row protects is the estate's own: a claim about the LAW is not a
        claim about the RECORD, and a pass that moved only the first should not be read as
        having moved the second."""
        old = _World(pack_at(W1A_BEFORE_COMMIT))
        new = _World()
        old.call("REGISTER-CAPABILITY", driver="drv-bare")
        new.call("REGISTER-CAPABILITY", driver="drv-bare")
        from subsystems.devices import DevicesView
        self.assertEqual(dict(DevicesView(old.store).capabilities()["drv-bare"]),
                         dict(DevicesView(new.store).capabilities()["drv-bare"]),
                         "the amendment moved a recorded payload; it was only supposed to "
                         "move a declaration")
        # and the declaration IS what moved — both directions, so neither half is assumed
        self.assertEqual(ops_of(pack_at(W1A_BEFORE_COMMIT))["REGISTER-CAPABILITY"]["params"],
                         {"driver": "required"})
        self.assertEqual(ops_of(live_pack())["REGISTER-CAPABILITY"]["params"],
                         {"driver": "required", "device_class": "optional",
                          "capabilities": "optional"})

    def test_the_capability_chain_still_refuses_an_unregistered_driver(self):
        w = _World()
        with self.assertRaises(OpError) as ctx:
            w.call("BIND-DEVICE", device="dev0", driver="ghost")
        self.assertEqual(ctx.exception.rule, "CAP-IS-LAW")


# =======================================================================================
# EP-29 STAGE 2 — W0g: THE GUEST ESTABLISHMENT, AS ROWS [2026-08-12]
#
# WHY THESE ROWS EXIST AND WHY THE FOUNDING DID NOT MOVE BENEATH THEM. Stage 2 was
# dispatched as W0g (establish the guest facts) then W1b (author the I/O window law
# against them). W0g COMPLETED. W1b STOPPED at C0's third state — STOP-AND-REPORT,
# which ADDENDUM 5 §4 rules GREEN — because the establishment below found the ground
# W1b declares against to be ABSENT, not merely thin.
#
# THE ESTABLISHED INVENTORY, DRIVEN AT THE GUEST BY THE ESTATE'S OWN PROBES:
#
#     device@sysfs        AVAILABLE   and its OWN coverage says it does not see I/O
#     device@uevent       AVAILABLE   and its OWN coverage says it adds freshness only
#     arrival@tracepoints UNAVAILABLE and it is the surface whose class IS I/O arrivals
#
# So the referent set for an I/O WINDOW declaration is EMPTY. ADDENDUM 4 §3 states that
# the window declarations "declare against the notification-surface inventory" and that
# "a window declared before the surfaces are established is the wrong-reference class
# authored into law." Declaring a window against `arrival@tracepoints` cites a surface no
# probe reached (ADDENDUM 6 C2's red world verbatim). Declaring one against `device@sysfs`
# or `device@uevent` borrows an AVAILABLE surface's name for a subject it states in its own
# coverage that it does not carry — the same wrong reference wearing a reachable name.
#
# ADDENDUM 6 C4 routes this outcome by name: "an empty or tiny W0g inventory reaching W1b
# is C0's STOP-AND-REPORT, never a vacuous MINOR about a change never made." The founding
# therefore stands BYTE-UNCHANGED, and for a STOPPED pass that is the ruled outcome and not
# the failing one — the same distinction the mentor drew at W1a's own stop (board :372).
#
# EVERY ROW BELOW IS A PROBE THAT RAN. Nothing here is asserted from a document.
# =======================================================================================

import hashlib                                                  # noqa: E402
import platform                                                 # noqa: E402
import re                                                       # noqa: E402

#: The guest's pinned kernel (charter §A21). Used here ONLY to prove a probe CROSSED — a
#: reading taken on this host would report this host's kernel, which is a different string.
GUEST_KERNEL = "6.8.0-134-generic"

#: This pass's own pre-write commit, captured before any write (§A53: `git checkout --` no
#: longer undoes one, so the commit is taken rather than trusted). The §A57 sweep reads the
#: founding out of THIS commit through `tests/era_pin.py` — the one home, IMPORTED, never
#: re-derived (EP-28Z; the class it retired was eighteen copies across ten files).
STAGE2_PRE_WRITE_COMMIT = "cf0f1985a44c3bb3ef0fa96e474acc009e6b4c9a"

#: The three surfaces W0g establishes, and the ONE of them whose class is device I/O.
DEVICE_SURFACES = (("device", "sysfs"), ("device", "uevent"), ("arrival", "tracepoints"))
THE_IO_SURFACE = ("arrival", "tracepoints")

# =======================================================================================
# STAGE 2, RESUMED — the constants W1b adds. EP-29 ADDENDUM 6 §4 (2026-08-12) RULED the
# unblock: RE-HOME THE PRIVILEGE. The observer runs PRIVILEGED in the lab guest and the
# window law NAMES that cost instead of hiding it. Nothing about the guest changed; the
# OBSERVER's invocation did.
# =======================================================================================

#: THIS pass's own pre-write commit, captured with `git rev-parse HEAD` before any write and
#: verified to hold 1.19.0 (§A53). It is the 1.19.0 ERA — the world W1b moved off.
W1B_BEFORE_COMMIT = "801585bb595ba410eb86d6a22f6cee7107ede678"
W1B_BEFORE_VERSION = "1.19.0"
W1B_AFTER_VERSION = "1.20.0"

#: W1b's OWN ERA, added by EP-28ZD (2026-08-13, charter §A57) — the last commit at which the
#: shipped founding still read 1.20.0, captured with `git rev-parse HEAD` before that pass's
#: first write (§A53). Three rows below asserted W1b's after-version against the LIVE tree,
#: which was correct exactly until a later founding pass ran; EP-28ZD moved the founding to
#: 1.21.0 and falsified all three. They now read this era instead of the live tree.
#: PINNED BY CONTENT, NEVER BY VERSION NUMBER — `era_pin`'s own stated cap, the estate's most
#: expensive known trap: the blob at this rev hashes to `d170619962d39ea5…`, W1b's pack sha256
#: as its close recorded it, and `TheEraPinIsVerifiedByContent` below checks that rather than
#: trusting this comment.
W1B_AFTER_COMMIT = "7fc50e4b0de2a880cb933f1343f869d87ef4fbbb"
W1B_AFTER_PACK_SHA = "d170619962d39ea5b9d317beecf6bb75d4678b0b1784278b150da7688499e00f"

#: The two windows W1b declares, one per device class the validation set spans.
THE_DECLARED_WINDOWS = ("device-io@block", "device-io@net")

#: The act class that STILL holds no definition after W1b, so C5's "the refusal narrowed,
#: never vanished" has a live subject. Deliberately a READ where W1b declared a WRITE: the
#: ioctl split is C4's and per-driver, and W1b does not widen into it.
STILL_UNDECLARED_IO_ACT = "DEVICE-IO-WINDOW-READ"

SSH = ["<SSH-INVOCATION>", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
       "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=10",
       "-i", os.path.expanduser("<KEYPATH>"), "<GUEST>"]


def _carrier_up():
    """THE CARRIER LAYER, TAKEN SEPARATELY AND SAYING ONLY WHAT IT KNOWS. A TCP connect to
    <LOOPBACK-PORT> says THE TUNNEL IS OPEN and says nothing whatever about the guest behind
    it. ADDENDUM 6 §1 requires a skip to name its layer BY CITATION rather than by clause,
    and the three layers are only separable if they are measured separately."""
    import socket as _s
    c = _s.socket()
    c.settimeout(5)
    try:
        c.connect(("127.0.0.1", 2222))
        return True, "carrier up"
    except OSError as exc:                                        # noqa: BLE001
        return False, "CARRIER: %s" % exc
    finally:
        c.close()


def _guest_layer(case, cmd, timeout=90, _input=None):
    """Run `cmd` in the guest, or SKIP naming WHICH LAYER refused.

    CARRIER / AUTH / GUEST are distinguished because they fail for different reasons and a
    single "guest unreachable" skip cannot tell a closed tunnel from a rejected key. The
    estate's standing reading: `Permission denied` only ever means THE DAEMON ANSWERED, so
    it is an AUTH fact and evidence that carrier AND guest are both up."""
    ok, why = _carrier_up()
    if not ok:
        case.skipTest("SKIP LONG-BOOT: %s — the tunnel to the lab is not open, so this row cannot reach its "
                      "subject and declines to state a fact about it" % why)
    try:
        r = subprocess.run(SSH + [cmd], capture_output=True, text=True, timeout=timeout,
                           input=_input)
    except (OSError, subprocess.SubprocessError) as exc:          # noqa: BLE001
        case.skipTest("SKIP LONG-BOOT: GUEST: the ssh client could not complete (%s)" % exc)
    if r.returncode != 0:
        err = (r.stderr or "").strip()
        if "Permission denied" in err or "denied" in err.lower():
            case.skipTest("SKIP LONG-BOOT: AUTH: the guest's daemon ANSWERED and refused the key (%s) — "
                          "carrier and guest are both up and this is the auth layer"
                          % err[:120])
        case.skipTest("SKIP LONG-BOOT: GUEST: reached the carrier but the guest did not answer (%s)"
                      % (err[:160] or "rc=%d" % r.returncode))
    return r.stdout


def _observe_digest():
    """The bytes of the estate's own observe package that the guest probe will run."""
    h = hashlib.sha256()
    for rel in ("__init__.py", "seam.py", "windows.py"):
        with open(os.path.join(REPO, "src", "observe", rel), "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()


#: The probe DRIVER. It contains no probe LOGIC: every availability verdict and every
#: coverage statement below is produced by `src/observe/windows.py`'s own methods, run on
#: the guest. A hand-rolled re-statement of those predicates would measure this file's
#: reading of the estate rather than the estate, which is the wrong-reference class in an
#: instrument instead of in a law.
_PROBE_DRIVER = r'''
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from observe import windows as W
out = {"uname": os.uname().release, "surfaces": [], "virtio": {}, "paths": {}}
for cls in (W.DeviceWindow, W.UeventSource, W.ArrivalWindow):
    w = cls()
    ok, reason = w.available()
    cov = w.coverage()
    out["surfaces"].append({"window": w.name, "route": w.route, "version": w.version,
                            "available": bool(ok), "reason": reason,
                            "facility": cov.get("facility"), "sees": cov.get("sees") or [],
                            "does_not_see": cov.get("does_not_see") or []})
    try:
        w.close()
    except Exception:
        pass
snap = W.scan_devices()
out["virtio"] = {k: v for k, v in snap.items() if k.startswith("virtio/")}
out["bus_entries_total"] = len(snap)
out["buses_seen"] = sorted({k.split("/")[0] for k in snap})
def _raw(p):
    """THE OBSERVATION, NEVER THE CONCLUSION (EP-29 ADDENDUM 6 §5, the :582 line).

    This used to record `os.path.exists(p)`. That call answers False for BOTH an absent
    path and a TRAVERSAL DENIAL, so what got stored was a verdict with its cause already
    discarded — and the shipped fixture then froze that verdict as fact. The raw stat
    outcome is recorded instead: the errno keeps ENOENT and EACCES distinguishable, and
    `exists`/`readable` are COMPUTED from it by the reader."""
    try:
        s = os.stat(p)
        rec = {"stat_errno": None, "dev": s.st_dev, "ino": s.st_ino,
               "mode": oct(s.st_mode & 0o7777), "uid": s.st_uid}
    except OSError as e:
        rec = {"stat_errno": e.errno, "dev": None, "ino": None, "mode": None, "uid": None}
    rec["r_ok"] = os.access(p, os.R_OK)          # a syscall result, not a derived value
    return rec
for p in ("/sys/kernel/debug/tracing", "/sys/kernel/tracing", "/sys/kernel/debug"):
    out["paths"][p] = _raw(p)
print("PROBE-JSON:" + json.dumps(out))
'''

_PROBE_MEMO = {}


def guest_probe(case):
    """Ship the estate's OWN observe package to the guest and run its OWN probes there.

    Memoized per suite run: the answer is a property of the box and re-shipping 90KB per row
    would put a network round trip on every assertion for a value that does not move — the
    same reasoning `Window.available()` gives for probing once and holding.

    The guest directory is keyed BY THE MODULE DIGEST, so a changed `windows.py` gets a fresh
    directory and a stale probe can never be read as a current one. NOTHING IS DELETED ON THE
    GUEST: a removal here would be a destructive command built from a constructed path, which
    §9.2's class says to avoid where a scoped alternative exists, and /tmp is ephemeral."""
    digest = _observe_digest()
    if digest in _PROBE_MEMO:
        memo = _PROBE_MEMO[digest]
        if isinstance(memo, str):
            # THE SKIP IS MEMOIZED TOO, and that is not a convenience. Without it a downed
            # guest costs every row its own connect timeout, and a suite that takes minutes
            # to report an unreachable lab discourages the arm that would find it.
            case.skipTest(memo)
        return memo
    try:
        data = _run_guest_probe(case, digest)
    except unittest.SkipTest as skip:
        _PROBE_MEMO[digest] = str(skip)
        raise
    _PROBE_MEMO[digest] = data
    return data


def _run_guest_probe(case, digest):
    gdir = "/tmp/govos-observe-probe-%s" % digest[:12]
    tar = subprocess.run(["tar", "-cz", "--exclude=__pycache__",
                          "-C", os.path.join(REPO, "src"), "observe"],
                         capture_output=True)
    if tar.returncode != 0:
        case.fail("could not pack the observe package: %r" % tar.stderr[:200])
    ok, why = _carrier_up()
    if not ok:
        case.skipTest("SKIP LONG-BOOT: %s — the surface establishment cannot reach the guest" % why)
    try:
        ship = subprocess.run(SSH + ["mkdir -p %s && tar -xz -C %s" % (gdir, gdir)],
                              input=tar.stdout, capture_output=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as exc:          # noqa: BLE001
        case.skipTest("SKIP LONG-BOOT: GUEST: could not ship the probe (%s)" % exc)
    if ship.returncode != 0:
        err = (ship.stderr or b"").decode("utf-8", "replace").strip()
        layer = "AUTH" if "denied" in err.lower() else "GUEST"
        case.skipTest("SKIP LONG-BOOT: %s: could not ship the probe (%s)" % (layer, err[:160]))
    out = _guest_layer(case, "cat > %s/_driver.py && cd %s && python3 _driver.py"
                       % (gdir, gdir), _input=_PROBE_DRIVER)
    line = [ln for ln in out.splitlines() if ln.startswith("PROBE-JSON:")]
    if not line:
        case.fail("the guest probe produced no PROBE-JSON line: %r" % out[-400:])
    data = json.loads(line[0][len("PROBE-JSON:"):])
    data["_module_digest"] = digest
    return data


def surfaces_by_key(data):
    return {(s["window"], s["route"]): s for s in data["surfaces"]}


#: THREE-VALUED ON PURPOSE. `True` the path is there, `False` the kernel says it is not,
#: `None` THE OBSERVER WAS REFUSED AND PRESENCE IS UNDETERMINED. A two-valued answer here is
#: the defect W1c repairs, one layer up: it forces a refusal to be recorded as one of the two
#: things it is not. Callers assert `is True` / `is False` / `is None` and never a bare truth
#: test — `assertFalse(None)` PASSES, so a bare test would read UNDETERMINED as absent and
#: reintroduce the conflation inside the check written to catch it.
def path_exists(rec):
    e = rec["stat_errno"]
    if e is None:
        return True
    if e in (errno.ENOENT, errno.ENOTDIR):
        return False
    return None


def path_readable(rec):
    """`os.access(R_OK)` as measured. Kept a separate question from presence: a path can be
    there and closed, and collapsing the two is how the shipped probe came to name a
    kernel-configuration need it had never measured."""
    return rec["r_ok"]


# =======================================================================================
# STAGE 2's PROBES — the PRIVILEGED pair, and the ACCESS MECHANISM driven at the guest
# =======================================================================================
#
# WHY THE ACCESS MECHANISM IS DRIVEN AND NOT READ OFF `coverage()`. `ArrivalWindow._probe`
# tests `os.path.exists("/sys/kernel/debug/tracing")` and, on False, reports "no
# /sys/kernel/debug/tracing on this host … configuring the kernel for them is outside this
# EP's fence". THAT SENTENCE IS FALSE ON THIS GUEST. tracefs IS mounted at that path; the
# parent is mode 0700 root-owned, so the unprivileged `stat` fails with EACCES and
# `os.path.exists` reports False for an ACCESS refusal. The probe converts an ACCESS result
# into a CAPABILITY claim and a kernel-configuration need, and its truthful branch — "present
# but not readable by this observer (measured)" — is UNREACHABLE in this case.
#
# So the establishment below comes from the MOUNT TABLE, the DIRECTORY MODES, the ERRNO and a
# PRIVILEGED LISTING. Quoting the reason string as establishment would author this pass's law
# on a false cause. `src/observe/windows.py` is OUTSIDE this EP's fence and is NOT repaired
# here; the defect is RAISED with its file:line in the entry.

_PRIV_PROBE_DRIVER = r'''
import json, os, subprocess, sys
T = "/sys/kernel/tracing"
D = "/sys/kernel/debug/tracing"
out = {"uid": os.getuid(), "uname": os.uname().release}

with open("/proc/mounts") as fh:
    out["mounts"] = [l.split() for l in fh if " tracefs " in l or " debugfs " in l]

def st(p):
    try:
        s = os.stat(p)
        return {"exists": True, "dev": s.st_dev, "ino": s.st_ino,
                "mode": oct(s.st_mode & 0o7777), "uid": s.st_uid, "errno": None}
    except OSError as e:
        return {"exists": False, "dev": None, "ino": None, "mode": None, "uid": None,
                "errno": e.errno}
out["stat"] = {p: st(p) for p in (T, D, "/sys/kernel/debug")}
out["exists"] = {p: os.path.exists(p) for p in (T, D)}
out["readable"] = {p: os.access(p, os.R_OK) for p in (T, D)}

ev = os.path.join(T, "events")
try:
    fams = sorted(os.listdir(ev))
except OSError as e:
    fams = []
    out["families_errno"] = e.errno
out["families"] = fams
out["family_events"] = {}
for f in ("block", "irq", "net"):
    try:
        # `enable` and `filter` are CONTROL FILES, not events. Counted out by name so the
        # figure is the tracepoint count and not the directory-entry count.
        out["family_events"][f] = sorted(n for n in os.listdir(os.path.join(ev, f))
                                         if n not in ("enable", "filter"))
    except OSError as e:
        out["family_events"][f] = []
        out.setdefault("family_errno", {})[f] = e.errno
try:
    with open(os.path.join(T, "available_events")) as fh:
        out["available_events"] = sum(1 for _ in fh)
except OSError:
    out["available_events"] = None
out["sudo_n"] = subprocess.run(["sudo", "-n", "true"]).returncode
print("PRIV-JSON:" + json.dumps(out))
'''

_PRIV_MEMO = {}


def _priv_probe_raw(case, privileged):
    """The access-mechanism probe, run at the guest under a named privilege.

    Memoized per privilege for the same reason `guest_probe` is: the answer is a property of
    the box, and a network round trip per assertion would discourage the arm that finds it."""
    key = "priv" if privileged else "unpriv"
    if key in _PRIV_MEMO:
        memo = _PRIV_MEMO[key]
        if isinstance(memo, str):
            case.skipTest(memo)
        return memo
    prefix = "sudo -n " if privileged else ""
    try:
        out = _guest_layer(case, "cat > /tmp/govos-w1b-priv.py && %spython3 "
                                 "/tmp/govos-w1b-priv.py" % prefix, _input=_PRIV_PROBE_DRIVER)
    except unittest.SkipTest as skip:
        _PRIV_MEMO[key] = str(skip)
        raise
    line = [ln for ln in out.splitlines() if ln.startswith("PRIV-JSON:")]
    if not line:
        case.fail("the %s probe produced no PRIV-JSON line: %r" % (key, out[-400:]))
    data = json.loads(line[0][len("PRIV-JSON:"):])
    _PRIV_MEMO[key] = data
    return data


def priv_probe(case):
    return _priv_probe_raw(case, True)


def unpriv_probe(case):
    return _priv_probe_raw(case, False)


_SURFACE_MEMO = {}


def guest_probe_privileged(case):
    """The estate's OWN window probes, run PRIVILEGED — ADDENDUM 6 §4's ruled invocation.

    Same shipped bytes, same methods, one difference: the uid they run under. That is the
    whole of what the ruling changed, and running the identical driver under both privileges
    is what makes the pair evidence rather than two unrelated readings."""
    digest = _observe_digest()
    if digest in _SURFACE_MEMO:
        memo = _SURFACE_MEMO[digest]
        if isinstance(memo, str):
            case.skipTest(memo)
        return memo
    gdir = "/tmp/govos-observe-probe-%s" % digest[:12]
    try:
        guest_probe(case)                      # ships the package (and memoizes the unpriv read)
        out = _guest_layer(case, "cat > %s/_driver_priv.py && cd %s && sudo -n python3 "
                                 "_driver_priv.py" % (gdir, gdir), _input=_PROBE_DRIVER)
    except unittest.SkipTest as skip:
        _SURFACE_MEMO[digest] = str(skip)
        raise
    line = [ln for ln in out.splitlines() if ln.startswith("PROBE-JSON:")]
    if not line:
        case.fail("the privileged surface probe produced no PROBE-JSON line: %r" % out[-400:])
    data = json.loads(line[0][len("PROBE-JSON:"):])
    data["_module_digest"] = digest
    _SURFACE_MEMO[digest] = data
    return data


# ---------------------------------------------------------------------------------------
class TheProbeReachedTheGuestAndNotThisHost(unittest.TestCase):
    """NON-VACUITY FOR EVERY ROW BELOW. A surface probe run on the HOST would answer, and
    would answer about the wrong box. `test_ep28c_w4d.py` established this discipline for
    guest rows and it is followed rather than re-derived: the establishment is only about
    the guest if the reading could not have come from here."""

    def test_the_probe_reports_the_guests_pinned_kernel_and_not_this_hosts(self):
        data = guest_probe(self)
        self.assertEqual(data["uname"], GUEST_KERNEL,
                         "the probe did not report the pinned guest kernel")
        self.assertNotEqual(data["uname"], platform.release(),
                            "the probe reports THIS host's kernel, so it never crossed and "
                            "every surface row below would be about the wrong box")

    def test_the_bytes_that_ran_at_the_guest_are_the_repositorys_own(self):
        """The probe is the ESTATE'S code, not a re-derivation. If the shipped bytes were
        not the repository's, these rows would establish someone else's predicates."""
        data = guest_probe(self)
        self.assertEqual(data["_module_digest"], _observe_digest())

    def test_the_carrier_layer_is_measured_separately_from_the_guest_layer(self):
        """The layer split is exercised, not merely written. A carrier verdict that never
        differs from the guest verdict is one reading wearing two labels."""
        ok, why = _carrier_up()
        self.assertIsInstance(ok, bool)
        self.assertTrue(why.startswith("CARRIER") or ok,
                        "a carrier failure must name its own layer: %r" % why)


class TheVirtioValidationSetIsEstablished(unittest.TestCase):
    """W0g C1 — THE VIRTIO VALIDATION SET, DRIVEN AT THE GUEST AND CITED PER DEVICE.

    ADDENDUM 6 C1's red world: a set asserted from documents rather than driven REDS. The
    set below comes from the guest's own `/sys/bus/virtio/devices` walk, read through the
    estate's `scan_devices()`."""

    EXPECTED = {"virtio/virtio0": "virtio_net",
                "virtio/virtio1": "virtio_blk",
                "virtio/virtio2": "virtio_blk"}

    def test_the_bus_enumerates_exactly_the_three_validation_devices(self):
        data = guest_probe(self)
        self.assertEqual(sorted(data["virtio"]), sorted(self.EXPECTED),
                         "the guest's virtio inventory moved; the validation set is a "
                         "property of the lab and a changed set re-opens W0g")

    def test_every_validation_device_carries_a_BOUND_driver(self):
        """A device with no bound driver is a capability with no bind, and an I/O window
        over it would have nothing to admit."""
        data = guest_probe(self)
        for key, driver in sorted(self.EXPECTED.items()):
            self.assertEqual(data["virtio"][key]["driver"], driver,
                             "%s is not bound to %s" % (key, driver))

    def test_the_set_spans_exactly_two_device_classes(self):
        """D8's bound, as a fact rather than a plan: the per-class annex is needed only as
        far as the validation hardware reaches, and this lab reaches block and net."""
        data = guest_probe(self)
        drivers = {v["driver"] for v in data["virtio"].values()}
        self.assertEqual(drivers, {"virtio_net", "virtio_blk"})

    def test_the_bus_walk_can_report_devices_OTHER_than_virtio(self):
        """POSITIVE CONTROL. A walk that returns only what this row expects cannot be
        distinguished from a walk that returns a hard-coded answer."""
        data = guest_probe(self)
        self.assertGreater(data["bus_entries_total"], len(data["virtio"]),
                           "the bus walk saw only virtio, so it cannot discriminate")
        self.assertIn("pci", data["buses_seen"])


class TheNotificationSurfacesAreEstablished(unittest.TestCase):
    """W0g C2 — THE NOTIFICATION SURFACES EP-22's DEVICE WINDOW LEFT AVAILABLE, DRIVEN.

    ADDENDUM 6 C2's red world: a surface LISTED that no probe REACHED reds. Every verdict
    below is the window class's own `available()`, executed on the guest."""

    def test_all_three_candidate_surfaces_were_actually_probed(self):
        data = guest_probe(self)
        self.assertEqual(sorted(surfaces_by_key(data)), sorted(DEVICE_SURFACES),
                         "a surface in the inventory was never reached by a probe")

    def test_the_sysfs_device_surface_is_AVAILABLE(self):
        data = guest_probe(self)
        s = surfaces_by_key(data)[("device", "sysfs")]
        self.assertTrue(s["available"], s["reason"])
        self.assertEqual(s["reason"], "ok")
        self.assertIn("6.8.0-134-generic", s["version"])

    def test_the_uevent_device_surface_is_AVAILABLE(self):
        data = guest_probe(self)
        s = surfaces_by_key(data)[("device", "uevent")]
        self.assertTrue(s["available"], s["reason"])
        self.assertIn("NETLINK_KOBJECT_UEVENT", s["facility"])

    def test_the_device_window_read_the_guests_OWN_devices(self):
        """NON-VACUITY FOR THE TWO ROWS ABOVE: an `available` verdict from a window that
        then reads nothing is availability without coverage."""
        data = guest_probe(self)
        self.assertTrue(data["virtio"], "the available device surface read no devices")


class TheIOWindowGroundIsEstablishedAbsent(unittest.TestCase):
    """WHAT AN UNPRIVILEGED OBSERVER CAN REACH — the first stage-2 pass's establishment, kept.

    [SCOPE FLIP — EP-29 W1b, 2026-08-12, on ADDENDUM 6 §4's ruling. This class was written as
    W1b's STOP: the arrival surface is unavailable, so the window law has no referent. THE
    VERDICT WAS TRUE AND IT IS STILL TRUE — FOR AN UNPRIVILEGED OBSERVER, which is the only
    observer that had been run. §4 RULED THE OBSERVER PRIVILEGED IN THE LAB, so the ground now
    exists and W1b landed. NOTHING ABOUT THE GUEST CHANGED: no chmod, no remount, no kernel
    configuration. The class is therefore RE-SCOPED rather than retired — its rows say
    UNPRIVILEGED where they used to say absent, and the PRIVILEGED half is the new class
    below. Keeping both is what makes the change legible as a PRIVILEGE change instead of a
    world change, and it is the pair that proves it.

    THE ONE ROW THAT WAS NOT MERELY SCOPED is `test_no_window_declaration_entered_the_founding
    _at_this_pass`, whose subject W1b reversed outright; its flip is documented at its own
    position below.]

    A check whose correct answer is a count of zero inverts as the file grows. These rows
    therefore name the surfaces and read each one's OWN verdict and OWN coverage sentence,
    so the claim is carried by named rows rather than by an empty search."""

    def test_the_ONE_surface_whose_class_is_IO_arrivals_is_NOT_available_UNPRIVILEGED(self):
        data = guest_probe(self)
        s = surfaces_by_key(data)[THE_IO_SURFACE]
        self.assertEqual(data["uname"], GUEST_KERNEL)
        self.assertFalse(s["available"],
                         "the arrival surface is available to an UNPRIVILEGED observer now, "
                         "so the privilege ADDENDUM 6 §4 priced into the window law is no "
                         "longer being paid and the declarations overstate their cost")
        self.assertEqual(s["sees"], [],
                         "the arrival surface claims to see something while reporting "
                         "unavailable, which is a coverage statement contradicting itself")

    def test_each_AVAILABLE_surface_states_IN_ITS_OWN_COVERAGE_that_it_does_not_see_IO(self):
        """The decisive establishment. Neither available surface is a candidate referent for
        an I/O window, and the ground for saying so is the surface's OWN sentence rather
        than this file's opinion about what sysfs can do."""
        data = guest_probe(self)
        by = surfaces_by_key(data)
        sysfs = " ".join(by[("device", "sysfs")]["does_not_see"])
        self.assertIn("interrupts, I/O completions and device traffic", sysfs)
        uevent = " ".join(by[("device", "uevent")]["does_not_see"])
        self.assertIn("no coverage of its own", uevent)
        # and the same surfaces DO claim the custody crossings, which W1a already governs
        self.assertTrue(any("bind" in s for s in by[("device", "sysfs")]["sees"]))

    def test_the_arrival_surface_is_unreachable_under_BOTH_candidate_paths(self):
        """A FINDING, DRIVEN AND PINNED — and CORRECTED AT W1c, 2026-08-12.

        [WHAT THIS DOCSTRING USED TO SAY, kept visible because it was the defect in words:
        "the LEGACY debugfs path `/sys/kernel/debug/tracing`, WHICH THIS GUEST DOES NOT
        HAVE". THAT WAS FALSE. The guest mounts tracefs at BOTH names — driven privileged
        by `TheTracefsAccessMechanismIsEstablished`, dev 12 inode 1 at each. What this row
        had been reading was `os.path.exists` answering False for a TRAVERSAL DENIAL, and
        the sentence turned that access result into a fact about the guest. The row was
        believing the very thing W1c repairs, in the file that pinned the finding.]

        WHAT IS TRUE AND IS NOW ASSERTED: to an UNPRIVILEGED observer the legacy path's
        presence is UNDETERMINED — its parent `/sys/kernel/debug` is 0700, so the walk is
        refused with EACCES and nothing about the facility was measured. The modern path
        IS measurable: `/sys/kernel` is 0755, the stat succeeds, and the directory is
        `drwx------ root:root`, so R_OK is False. The window's verdict was correct under
        both spellings and remains so; only its reason was wrong."""
        data = guest_probe(self)
        legacy = data["paths"]["/sys/kernel/debug/tracing"]
        modern = data["paths"]["/sys/kernel/tracing"]
        self.assertIs(path_exists(legacy), None,
                      "the legacy path's presence is now DETERMINED to this observer "
                      "(stat_errno %r), so the traversal denial that made it undeterminable "
                      "has moved and this row's subject changed" % legacy["stat_errno"])
        self.assertEqual(legacy["stat_errno"], errno.EACCES,
                         "the unprivileged failure is not a permission denial, so the cause "
                         "is something other than the traversal refusal pinned here")
        self.assertIs(path_exists(modern), True,
                      "tracefs is not mounted at the modern path, or the walk to it was "
                      "refused: %r" % (modern,))
        self.assertIs(path_readable(modern), False,
                      "the modern tracing path IS readable by the observer now, so the "
                      "arrival surface would be available UNPRIVILEGED and W1b's priced "
                      "privilege is no longer being paid")

    def test_the_founding_declared_NO_IO_WINDOW_and_the_undeclared_act_refused(self):
        """C5's BEFORE direction, driven rather than assumed.

        [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12. CAUSE: W1b landed, so the LIVE world no
        longer refuses this name. ASSERTED: `_World()`, live. SUPERSEDED: a world booted from
        `pack_at(W1B_BEFORE_COMMIT)` — the stopped pass's own era, which is what a BEFORE
        direction was always about. REMAINS TRUE, and it is now doing the job it was written
        for: it is the BEFORE half of C5's flip, and the AFTER half is one class below.]"""
        w = _World(pack_at(W1B_BEFORE_COMMIT))
        w.call("REGISTER-CAPABILITY", driver="drv-a", device_class="block")
        w.call("BIND-DEVICE", device="dev0", driver="drv-a")
        from subsystems.devices import DevicesView
        self.assertEqual(DevicesView(w.store).bindings(), {"dev0": "drv-a"})   # live first
        with self.assertRaises(OpError) as ctx:
            w.call(UNDECLARED_IO_ACT, device="dev0", bytes=4)
        self.assertEqual(ctx.exception.rule, "P3-CLOSURE")

    def test_no_window_declaration_entered_the_founding_at_the_STOPPED_pass(self):
        """[DOCUMENTED FLIP — EP-29 W1b, 2026-08-12. CAUSE: this row asserted the STOP as a
        fact about the LIVE law, and W1b lifted the stop on ADDENDUM 6 §4's ruling — so the
        row's own escape sentence fired exactly as written: "W1b landed after all and this row
        is describing a world that no longer holds". ASSERTED: `live_pack()`. SUPERSEDED:
        `pack_at(W1B_BEFORE_COMMIT)`, the stopped pass's own era. REMAINS TRUE: at the moment
        the first stage-2 pass closed, no window declaration and no I/O act definition existed —
        which is what makes W1b's landing a CHANGE rather than a restatement. GIVEN UP: the live
        reach, deliberately and by ruling; the live claim is now the opposite one and is
        asserted at TheWindowLawLanded below.]"""
        era = pack_at(W1B_BEFORE_COMMIT)
        rules = rules_of(era)
        windowish = sorted(r for r in rules if "WINDOW" in r.upper())
        self.assertEqual(windowish, [], repr(windowish))
        self.assertNotIn(UNDECLARED_IO_ACT, ops_of(era))
        # NON-VACUITY: the same walk over the LIVE pack must find what W1b landed, or this row
        # is a filter that cannot match rather than an era that did not contain them.
        self.assertIn(UNDECLARED_IO_ACT, ops_of(live_pack()),
                      "the walk finds no I/O act definition in the LIVE pack either, so its "
                      "empty answer about the era says nothing")


class TheFoundingStandsUnmovedAndTheSweepPopulationIsEmpty(unittest.TestCase):
    """C4, ANSWERED IN THE DIRECTION THE FIRST STAGE-2 PASS TOOK — AND THEN THE OTHER ONE.

    [SCOPE FLIP — EP-29 W1b, 2026-08-12. This class recorded the STOPPED pass's outcome: the
    founding byte-unchanged, the §A57 sweep empty BY CONSTRUCTION. C4's red world has two
    halves routing to different doors — byte-unchanged after a LANDED W1b REDS, and an empty
    W0g inventory reaching W1b is C0's STOP-AND-REPORT, which is never reached because W1b
    never lawfully runs. THE FIRST PASS TOOK THE SECOND DOOR. W1b, resumed on ADDENDUM 6 §4's
    privilege ruling, TOOK THE FIRST: the founding MOVED 1.19.0 -> 1.20.0 and the sweep
    population was NOT empty — it was TWELVE ROWS ACROSS SEVEN FILES. Both outcomes are true
    of their own pass, so the rows below are re-pointed at the era each describes rather than
    deleted, and the landed half is asserted LIVE at TheFoundingMovedAgainAtStage2.]"""

    def test_the_pack_was_byte_identical_at_the_STOPPED_passs_own_pre_write_commit(self):
        """THE ERA PIN, IMPORTED FROM ITS ONE HOME. `era_pin.blob_at` returns BYTES, which is
        what a digest claim needs; a decode that normalised line endings would move it.

        [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12, charter §A57, and this row was NAMED ON THE
        STOPPED PASS'S OWN WORKLIST as one the next founding move would falsify — so it is
        being swept by the mechanism that predicted it. CAUSE: W1b moved the founding, so the
        live pack is no longer byte-identical to that pass's pre-write commit. ASSERTED: the
        LIVE bytes. SUPERSEDED: the bytes at THIS pass's pre-write commit, which is where the
        stopped pass's byte-state ended and W1b's began — the two commits hold the same pack,
        asserted here rather than assumed. REMAINS TRUE: the stopped pass moved no byte.]"""
        era = era_pin.blob_at(STAGE2_PRE_WRITE_COMMIT, era_pin.PACK_PATH)
        boundary = era_pin.blob_at(W1B_BEFORE_COMMIT, era_pin.PACK_PATH)
        self.assertEqual(hashlib.sha256(era).hexdigest(),
                         hashlib.sha256(boundary).hexdigest(),
                         "the founding moved between the stopped pass's close and W1b's open, "
                         "so some third party moved it and neither pass's account is complete")
        self.assertEqual(json.loads(era.decode("utf-8"))["founding_version"], W1A_AFTER_VERSION)

    def test_the_era_pin_reports_a_DIFFERENCE_when_there_is_one(self):
        """The instrument's own negative-result test. A comparison that cannot report
        inequality is not a comparison, and both rows above rest on this one."""
        older = era_pin.blob_at(W1A_BEFORE_COMMIT, era_pin.PACK_PATH)
        with open(PACK_PATH, "rb") as fh:
            live = fh.read()
        self.assertNotEqual(hashlib.sha256(older).hexdigest(),
                            hashlib.sha256(live).hexdigest())
        self.assertEqual(json.loads(older.decode("utf-8"))["founding_version"], W1A_BEFORE_VERSION)

    #: THE NEXT MOVE'S WORKLIST, NAMED RATHER THAN LEFT TO BE RE-DERIVED. These are the rows
    #: that compare a LIVE-tree founding read against the literal current version, so the
    #: NEXT founding pass falsifies exactly these and owes them the §A57 era-pin. Handed
    #: forward as a named list because the alternative is the eighteen-copy class arriving in
    #: a different dimension: every pass re-running the same walk.
    NEXT_MOVE_FALSIFIES = (
        ("tests/test_ep29.py", "TheDeviceLawIsDeclared."
                               "test_after_this_pass_the_cited_law_resolves_to_a_record"),
        ("tests/test_ep29.py", "TheFoundingMoved.test_the_pack_version_moved_one_MINOR"),
        ("tests/test_ep29.py", "TheFoundingMoved."
                               "test_the_founding_designation_record_carries_the_new_version"),
        ("tests/test_ep29.py", "TheFoundingStandsUnmovedAndTheSweepPopulationIsEmpty."
                               "test_the_pack_was_byte_identical_at_the_STOPPED_passs_own_pre_write_commit"),
    )

    def test_every_row_on_the_next_moves_worklist_exists_and_reads_the_LIVE_tree(self):
        """A worklist naming rows that do not exist is worse than no worklist. Each entry is
        resolved to a real test method here, so the list cannot rot silently."""
        for path, dotted in self.NEXT_MOVE_FALSIFIES:
            self.assertTrue(os.path.exists(os.path.join(REPO, path)), path)
            cls_name, meth = dotted.split(".")
            cls = globals().get(cls_name)
            self.assertIsNotNone(cls, "no such class: %s" % cls_name)
            self.assertTrue(hasattr(cls, meth), "no such row: %s" % dotted)

    def test_the_STOPPED_pass_falsified_none_of_them_because_it_moved_no_byte(self):
        """The stopped pass's sweep RESULT, and its ground stated so it is not read as a
        search that happened to come back empty.

        [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12. CAUSE: this row compared the stopped pass's
        era to the LIVE tree, and W1b moved the live tree. ASSERTED: `live_pack()`.
        SUPERSEDED: `pack_at(W1B_BEFORE_COMMIT)`, the boundary the row above pins. REMAINS
        TRUE: THAT pass falsified nothing because it moved no byte. THIS pass did move bytes
        and its sweep population is asserted, non-empty and named, at TheSweepWasNotEmpty.]"""
        era = era_pin.pack_at(STAGE2_PRE_WRITE_COMMIT)
        boundary = era_pin.pack_at(W1B_BEFORE_COMMIT)
        self.assertEqual(era["founding_version"], boundary["founding_version"])
        self.assertEqual(len(era["steps"]), len(boundary["steps"]))


# =======================================================================================
# THE RED WORLDS FOR W0g's ROWS — EXHIBITED THROUGH THE INSTRUMENT, ON SYNTHETIC SUBSTRATE
#
# §A64 and the red-world law: a structural row is untested until a NEAR-MISS has been driven
# against it, and "this row would fail if X" is an argument rather than an exhibition. Each
# row below plants a probe payload and RUNS THE REAL ROW against it, so no predicate is
# restated here — a red world that re-implements the assertion it is testing proves only
# that two copies agree.
#
# THE SUBSTRATE IS SYNTHETIC ON PURPOSE (§A42, and the census in `test_ep28z.py` does the
# same). A red world built by mutating the LIVE guest reading could only run when the lab is
# up, so the one class of row whose whole job is to fail would be the first to go silent when
# the estate most needs it. CONTROL FIRST: `test_the_synthetic_control_PASSES_every_row`
# proves the substrate is faithful, and without it a red below could be the synthetic being
# malformed rather than the clause biting.
# =======================================================================================

import io                                                        # noqa: E402


def _synthetic_probe():
    """A faithful recording of the 2026-08-12 guest establishment, used as red-world
    substrate. Its fidelity is not asserted from this comment: the control row below runs
    EVERY real W0g row against it and requires them all to pass."""
    return {
        "uname": GUEST_KERNEL,
        "_module_digest": _observe_digest(),
        "bus_entries_total": 186,
        "buses_seen": [
            "acpi",
            "clockevents",
            "clocksource",
            "container",
            "cpu",
            "edac",
            "event_source",
            "machinecheck",
            "memory",
            "memory_tiering",
            "node",
            "nvmem",
            "parport",
            "pci",
            "platform",
            "pnp",
            "scsi",
            "serial-base",
            "serio",
            "virtio",
            "workqueue",
        ],
        "virtio": {
            "virtio/virtio0": {
                "driver": "virtio_net",
                "subsystem": "virtio",
            },
            "virtio/virtio1": {
                "driver": "virtio_blk",
                "subsystem": "virtio",
            },
            "virtio/virtio2": {
                "driver": "virtio_blk",
                "subsystem": "virtio",
            },
        },
        "paths": {
            "/sys/kernel/debug": {
                "dev": 7,
                "ino": 1,
                "mode": "0o700",
                "r_ok": False,
                "stat_errno": None,
                "uid": 0,
            },
            "/sys/kernel/debug/tracing": {
                "dev": None,
                "ino": None,
                "mode": None,
                "r_ok": False,
                "stat_errno": 13,
                "uid": None,
            },
            "/sys/kernel/tracing": {
                "dev": 12,
                "ino": 1,
                "mode": "0o700",
                "r_ok": False,
                "stat_errno": None,
                "uid": 0,
            },
        },
        "surfaces": [
            {
                "available": True,
                "does_not_see": [
                    "devices with no bus entry — the class-only and platform-implicit "
                        "devices",
                    "interrupts, I/O completions and device traffic: those are the "
                        "INPUT/STREAM classes, whose window needs tracepoints and is "
                        "DEFERRED (see ArrivalWindow)",
                    "the crossing's own time — sysfs reports none, so every device "
                        "record carries a marked submission-time substitution",
                    "hotplug between two scans; the uevent socket is the live route and "
                        "its availability is reported separately",
                ],
                "facility": "/sys/bus/*/devices (scan)",
                "reason": "ok",
                "route": "sysfs",
                "sees": [
                    "a device appearing or leaving a bus (its capability)",
                    "a driver binding to or releasing a device (the bind)",
                ],
                "version": "m1.1-sysfs+6.8.0-134-generic",
                "window": "device",
            },
            {
                "available": True,
                "does_not_see": [
                    "anything on a quiescent box — this route reports change, never "
                        "state, so it adds freshness to the sysfs scan and no coverage of "
                        "its own",
                    "the crossing's own time — uevents carry a sequence number, not a "
                        "timestamp",
                    "events emitted before this socket was bound",
                ],
                "facility": "netlink NETLINK_KOBJECT_UEVENT (kernel group)",
                "reason": "ok",
                "route": "uevent",
                "sees": ["add / remove / bind / unbind announcements as the kernel emits them"],
                "version": "m1.1-uevent+6.8.0-134-generic",
                "window": "device",
            },
            {
                "available": False,
                "does_not_see": [
                    "every INPUT-class arrival — interrupts, I/O completions, timer "
                        "ticks: /sys/kernel/tracing is present but not readable by this "
                        "observer (measured) — the arrival routes stay DEFERRED; kernel "
                        "configuration is outside this EP's fence",
                    "consequently the INPUT class carries no M1 records, and no view "
                        "claims it does",
                ],
                "facility": "eBPF / tracepoints (DEFERRED)",
                "reason": "/sys/kernel/tracing is present but not readable by this observer "
                    "(measured) — the arrival routes stay DEFERRED; kernel configuration is "
                    "outside this EP's fence",
                "route": "tracepoints",
                "sees": [],
                "version": "m1.1-tracepoints+6.8.0-134-generic",
                "window": "arrival",
            },
        ],
    }


#: Every W0g row that reads the guest probe. Named as data so the control cannot pass by
#: quietly running fewer rows than exist.
_PROBE_ROWS = (
    (TheProbeReachedTheGuestAndNotThisHost,
     ("test_the_probe_reports_the_guests_pinned_kernel_and_not_this_hosts",
      "test_the_bytes_that_ran_at_the_guest_are_the_repositorys_own")),
    (TheVirtioValidationSetIsEstablished,
     ("test_the_bus_enumerates_exactly_the_three_validation_devices",
      "test_every_validation_device_carries_a_BOUND_driver",
      "test_the_set_spans_exactly_two_device_classes",
      "test_the_bus_walk_can_report_devices_OTHER_than_virtio")),
    (TheNotificationSurfacesAreEstablished,
     ("test_all_three_candidate_surfaces_were_actually_probed",
      "test_the_sysfs_device_surface_is_AVAILABLE",
      "test_the_uevent_device_surface_is_AVAILABLE",
      "test_the_device_window_read_the_guests_OWN_devices")),
    (TheIOWindowGroundIsEstablishedAbsent,
     ("test_the_ONE_surface_whose_class_is_IO_arrivals_is_NOT_available_UNPRIVILEGED",
      "test_each_AVAILABLE_surface_states_IN_ITS_OWN_COVERAGE_that_it_does_not_see_IO",
      "test_the_arrival_surface_is_unreachable_under_BOTH_candidate_paths")),
)


def _run_against(planted, cls, meth):
    """Run a REAL row of this file against a PLANTED probe payload; return its result.

    The row is executed by unittest's own machinery, so what is measured is the row that
    ships and not a paraphrase of it."""
    key = _observe_digest()
    sentinel = object()
    saved = _PROBE_MEMO.get(key, sentinel)
    _PROBE_MEMO[key] = planted
    try:
        return unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(cls(meth))
    finally:
        if saved is sentinel:
            _PROBE_MEMO.pop(key, None)
        else:
            _PROBE_MEMO[key] = saved


class TheW0gRowsCanBeMadeToFail(unittest.TestCase):
    """THE NEGATIVE-RESULT TEST, APPLIED TO THIS PASS'S OWN ESTABLISHMENT.

    What result would make each W0g row speak against me? If nothing would, the row is a
    sentence with a colon in it. Every red world below is DRIVEN and its output is this
    suite's own."""

    def assertRowFAILED(self, res, why):
        """A RED WORLD MUST RED FOR ITS OWN REASON. `wasSuccessful()` is False for an ERROR
        too, so a planted payload that breaks the instrument — a KeyError, a bad shape —
        would satisfy a bare `assertFalse` and read on the page exactly like the claim
        biting. This separates them: the row must FAIL, and it must not ERROR."""
        self.assertEqual(res.errors, [],
                         "the row ERRORED rather than failed, so the planted world broke "
                         "the instrument instead of the claim: %r" % (res.errors,))
        self.assertEqual(len(res.failures), 1, why)

    def test_the_synthetic_control_PASSES_every_row(self):
        """CONTROL. Without this, a red below could be the substrate being malformed rather
        than the clause biting — and the two read identically on the page."""
        ran = 0
        for cls, meths in _PROBE_ROWS:
            for meth in meths:
                res = _run_against(_synthetic_probe(), cls, meth)
                self.assertTrue(res.wasSuccessful(),
                                "the synthetic control FAILS %s.%s, so every red world below "
                                "is uninterpretable: %r"
                                % (cls.__name__, meth, res.failures + res.errors))
                ran += 1
        self.assertEqual(ran, sum(len(m) for _, m in _PROBE_ROWS))
        self.assertGreater(ran, 10, "non-vacuity: the control is not a stub")

    def test_an_AVAILABLE_arrival_surface_REDS_the_row_that_carries_the_stop(self):
        """THE MOST IMPORTANT RED WORLD IN THIS PASS. W1b stopped because the one surface
        whose class is device I/O is unavailable. If that surface ever becomes available the
        stop is lifted, and the row must SAY SO by going red rather than by staying quiet."""
        planted = _synthetic_probe()
        for s in planted["surfaces"]:
            if (s["window"], s["route"]) == THE_IO_SURFACE:
                s["available"] = True
                s["reason"] = "ok"
                s["sees"] = ["interrupt and I/O-completion arrivals"]
        res = _run_against(planted, TheIOWindowGroundIsEstablishedAbsent,
                           "test_the_ONE_surface_whose_class_is_IO_arrivals_is_NOT_available_UNPRIVILEGED")
        self.assertRowFAILED(res,
                         "the stop-carrying row passes in a world where the arrival surface "
                         "is AVAILABLE, so it cannot report the day W1b's ground arrives")

    def test_a_sysfs_surface_that_CLAIMED_to_see_IO_REDS_the_coverage_row(self):
        """The second half of the establishment: the available surfaces are ruled out as
        referents by their OWN coverage sentence. Delete that sentence and the row must red,
        or it was reading something else."""
        planted = _synthetic_probe()
        for s in planted["surfaces"]:
            if (s["window"], s["route"]) == ("device", "sysfs"):
                s["does_not_see"] = [d for d in s["does_not_see"]
                                     if "I/O completions" not in d]
        res = _run_against(
            planted, TheIOWindowGroundIsEstablishedAbsent,
            "test_each_AVAILABLE_surface_states_IN_ITS_OWN_COVERAGE_that_it_does_not_see_IO")
        self.assertRowFAILED(res, "the planted world did not red the row")

    def test_a_probe_that_ran_on_THIS_HOST_REDS_the_crossing_row(self):
        """The non-vacuity guard's own non-vacuity. A probe answering from the host would
        report a plausible surface inventory about the wrong box."""
        planted = _synthetic_probe()
        planted["uname"] = platform.release()
        res = _run_against(planted, TheProbeReachedTheGuestAndNotThisHost,
                           "test_the_probe_reports_the_guests_pinned_kernel_and_not_this_hosts")
        self.assertRowFAILED(res, "the planted world did not red the row")
        self.assertNotEqual(platform.release(), GUEST_KERNEL,
                            "this host and the guest run the same kernel string, so the "
                            "crossing row cannot discriminate and neither can this one")

    def test_a_READABLE_modern_tracing_path_REDS_the_two_path_finding(self):
        """The finding's own red world. The arrival surface is unreachable under BOTH paths;
        if the modern path became readable, repairing the probe path WOULD make the surface
        available, and the row must red rather than keep reporting a settled question.

        [W1c, 2026-08-12 — THE PLANT MOVED WITH THE FIXTURE, AND IT SAID SO BY GOING RED.
        This planted `readable`, which the fixture no longer carries: W1c made the fixture
        store the RAW observation (`r_ok`, `stat_errno`) and compute the verdicts. A plant
        writing a key nobody reads changes nothing, so this red world had quietly stopped
        biting. It is planted at `r_ok` now, and the key is ASSERTED PRESENT first so the
        next rename fails loudly here instead of turning this row back into a decoration.]"""
        planted = _synthetic_probe()
        rec = planted["paths"]["/sys/kernel/tracing"]
        self.assertIn("r_ok", rec,
                      "the raw readability key was renamed, so this plant writes a field no "
                      "row reads and this red world is inert: %r" % (sorted(rec),))
        rec["r_ok"] = True
        res = _run_against(planted, TheIOWindowGroundIsEstablishedAbsent,
                           "test_the_arrival_surface_is_unreachable_under_BOTH_candidate_paths")
        self.assertRowFAILED(res, "the planted world did not red the row")

    def test_a_CHANGED_virtio_inventory_REDS_the_validation_set_row(self):
        """The validation set is a property of the lab, and a lab that quietly gains or loses
        a device re-opens W0g rather than passing through it."""
        planted = _synthetic_probe()
        planted["virtio"].pop("virtio/virtio2")
        res = _run_against(planted, TheVirtioValidationSetIsEstablished,
                           "test_the_bus_enumerates_exactly_the_three_validation_devices")
        self.assertRowFAILED(res, "the planted world did not red the row")

    def test_an_UNBOUND_validation_device_REDS_the_bound_driver_row(self):
        planted = _synthetic_probe()
        planted["virtio"]["virtio/virtio1"]["driver"] = None
        res = _run_against(planted, TheVirtioValidationSetIsEstablished,
                           "test_every_validation_device_carries_a_BOUND_driver")
        self.assertRowFAILED(res, "the planted world did not red the row")

    def test_a_bus_walk_that_saw_ONLY_virtio_REDS_its_own_positive_control(self):
        planted = _synthetic_probe()
        planted["bus_entries_total"] = len(planted["virtio"])
        res = _run_against(planted, TheVirtioValidationSetIsEstablished,
                           "test_the_bus_walk_can_report_devices_OTHER_than_virtio")
        self.assertRowFAILED(res, "the planted world did not red the row")

    def test_an_UNPROBED_surface_REDS_the_inventory_completeness_row(self):
        """ADDENDUM 6 C2's red world in its own words: a surface listed that no probe
        reached. Here the listing keeps three and the probe returns two."""
        planted = _synthetic_probe()
        planted["surfaces"] = [s for s in planted["surfaces"]
                               if (s["window"], s["route"]) != THE_IO_SURFACE]
        res = _run_against(planted, TheNotificationSurfacesAreEstablished,
                           "test_all_three_candidate_surfaces_were_actually_probed")
        self.assertRowFAILED(res, "the planted world did not red the row")

    def test_a_LANDED_window_law_REDS_the_row_that_records_the_stop(self):
        """The stop is recorded as a fact about the founding. If a later pass lands the
        window law and leaves this row standing, the row must red and name itself stale
        rather than describe a world that no longer holds."""
        pack = live_pack()
        step = [s for s in pack["steps"] if s["step"] == "05g-device-laws"][0]
        step["records"].append({
            "actor": "PC_RUNTIME", "action": "CREATE-RULE", "object": "DEV-LAW-WINDOW",
            "rule_cited": "BOOT-INT",
            "payload": {"rule_id": "DEV-LAW-WINDOW", "text": "a planted window law",
                        "scope": "space:root", "enforcement": "live"}})
        windowish = sorted(r for r in rules_of(pack) if "WINDOW" in r.upper())
        self.assertEqual(windowish, ["DEV-LAW-WINDOW"],
                         "the walk that reports zero window laws cannot report one, so its "
                         "zero is not a result")

    def test_a_MOVED_founding_REDS_the_byte_identical_row(self):
        """C4's red world reaching this pass's own outcome. The byte-identity row is what
        says the founding did not move; a comparison that cannot report a move is not one.
        Driven against a real earlier era rather than a mutated string."""
        older = era_pin.blob_at(W1A_BEFORE_COMMIT, era_pin.PACK_PATH)
        with open(PACK_PATH, "rb") as fh:
            live = fh.read()
        self.assertNotEqual(hashlib.sha256(older).hexdigest(),
                            hashlib.sha256(live).hexdigest())

    # -- the availability and shape rows, so the exhibited fraction is not left at 8/20 --

    def test_an_UNAVAILABLE_sysfs_surface_REDS_its_availability_row(self):
        planted = _synthetic_probe()
        for s in planted["surfaces"]:
            if (s["window"], s["route"]) == ("device", "sysfs"):
                s["available"] = False
                s["reason"] = "no /sys/bus on this platform"
        res = _run_against(planted, TheNotificationSurfacesAreEstablished,
                           "test_the_sysfs_device_surface_is_AVAILABLE")
        self.assertRowFAILED(res, "an unavailable sysfs surface still reads as established")

    def test_an_UNAVAILABLE_uevent_surface_REDS_its_availability_row(self):
        planted = _synthetic_probe()
        for s in planted["surfaces"]:
            if (s["window"], s["route"]) == ("device", "uevent"):
                s["available"] = False
                s["reason"] = "netlink uevent bind failed: [Errno 1] Operation not permitted"
        res = _run_against(planted, TheNotificationSurfacesAreEstablished,
                           "test_the_uevent_device_surface_is_AVAILABLE")
        self.assertRowFAILED(res, "an unavailable uevent surface still reads as established")

    def test_an_AVAILABLE_surface_that_READ_NOTHING_REDS_the_non_vacuity_row(self):
        """Availability without coverage: the window says `ok` and then returns no device.
        The row that exists to catch exactly that must catch exactly that."""
        planted = _synthetic_probe()
        planted["virtio"] = {}
        res = _run_against(planted, TheNotificationSurfacesAreEstablished,
                           "test_the_device_window_read_the_guests_OWN_devices")
        self.assertRowFAILED(res, "an available surface that read nothing passed the "
                                  "non-vacuity guard")

    def test_a_THIRD_device_class_REDS_the_two_class_row(self):
        """D8's bound is a measured property of this lab, not a standing assumption. A third
        class arriving widens the per-class annex and must re-open W0g rather than pass."""
        planted = _synthetic_probe()
        planted["virtio"]["virtio/virtio3"] = {"subsystem": "virtio", "driver": "virtio_scsi"}
        res = _run_against(planted, TheVirtioValidationSetIsEstablished,
                           "test_the_set_spans_exactly_two_device_classes")
        self.assertRowFAILED(res, "a third device class did not re-open the class bound")

    def test_a_MISMATCHED_module_digest_REDS_the_estate_bytes_row(self):
        """The row that says the guest ran the ESTATE's code. If the shipped bytes were some
        other version, every surface verdict would be about predicates this repository does
        not contain."""
        planted = _synthetic_probe()
        planted["_module_digest"] = "0" * 64
        res = _run_against(planted, TheProbeReachedTheGuestAndNotThisHost,
                           "test_the_bytes_that_ran_at_the_guest_are_the_repositorys_own")
        self.assertRowFAILED(res, "a foreign module digest still read as the estate's own")


# =======================================================================================
class NoWindowInTheObserveLayerClaimsDeviceIO(unittest.TestCase):
    """W1b's STOP AT ITS FULL WIDTH, AND HOST-SIDE SO IT SURVIVES A GUEST OUTAGE.

    W0g's guest probe establishes the three DEVICE-window surfaces. But the claim the stop
    rests on is wider than three: "no established surface sees device I/O" is a statement
    about THE WHOLE OBSERVE LAYER, and checking three of seven windows would be a claim
    wider than its evidence — this estate's most-repeated defect class.

    So this class reads ALL SEVEN windows' own `coverage()` and asks each what it SEES. It
    needs no guest: the coverage statements are properties of the code, so the day the lab
    is down this row still answers, and it is the row a later pass should read first."""

    #: The whole layer, in `default_windows()` order plus the device window's second route.
    ALL_WINDOWS = ("ProcessWindow", "FileWindow", "MountWindow", "DeviceWindow",
                   "UeventSource", "ConnectionWindow", "ArrivalWindow")

    #: The subject an I/O WINDOW declaration would have to be observed through.
    IO_SUBJECT = re.compile(r"interrupt|I/O completion|device traffic", re.I)

    def _layer(self):
        from observe import windows as W
        out = {}
        for name in self.ALL_WINDOWS:
            cls = getattr(W, name)
            w = cls(()) if name == "FileWindow" else cls()
            out[name] = w.coverage()
            try:
                w.close()
            except Exception:                                     # noqa: BLE001
                pass
        return out

    def test_every_window_in_the_layer_answered_its_own_coverage(self):
        """NON-VACUITY FIRST: a walk that silently read five of seven would report the same
        empty result as a walk that read all seven and found nothing."""
        layer = self._layer()
        self.assertEqual(sorted(layer), sorted(self.ALL_WINDOWS))
        self.assertEqual(len(layer), 7)
        self.assertTrue(all("sees" in c for c in layer.values()))

    def test_NO_windows_SEES_list_names_device_IO(self):
        """THE ESTABLISHMENT'S WIDEST FORM. Every claim any window makes about what it SEES,
        checked against the subject an I/O window would need."""
        offenders = []
        for name, cov in self._layer().items():
            for s in (cov.get("sees") or []):
                if self.IO_SUBJECT.search(s):
                    offenders.append((name, s))
        self.assertEqual(offenders, [],
                         "a window now claims to SEE device I/O, so W1b's referent set is no "
                         "longer empty and the stop is lifted: %r" % (offenders,))

    def test_the_matcher_CAN_match_the_subject_it_searches_for(self):
        """THE POSITIVE CONTROL, and the row above is uninterpretable without it. A matcher
        that matches nothing returns an empty offender list over any input at all."""
        layer = self._layer()
        hits = [d for d in (layer["ArrivalWindow"].get("does_not_see") or [])
                if self.IO_SUBJECT.search(d)]
        self.assertTrue(hits, "the matcher finds device I/O NOWHERE in the layer, including "
                              "in the sentence that names it — so its empty result above is "
                              "a property of the matcher rather than of the windows")
        sysfs = [d for d in (layer["DeviceWindow"].get("does_not_see") or [])
                 if self.IO_SUBJECT.search(d)]
        self.assertTrue(sysfs, "the device window no longer disclaims device I/O")

    def test_the_ONE_window_whose_class_is_arrivals_sees_NOTHING(self):
        """`ArrivalWindow` is the INPUT class's window — interrupts, I/O completions, timer
        ticks — and it is DECLARED AND DEFERRED rather than silently absent. Its empty `sees`
        is the whole reason W1b has nothing to declare against."""
        layer = self._layer()
        self.assertEqual(layer["ArrivalWindow"].get("sees"), [],
                         "the arrival window now claims coverage; W1b's ground has arrived")
        self.assertIn("DEFERRED", layer["ArrivalWindow"].get("facility") or "")
        # and it is the ONLY window in the layer that claims nothing
        empty = [n for n, c in layer.items() if not (c.get("sees") or [])]
        self.assertEqual(empty, ["ArrivalWindow"])


# =======================================================================================
# STAGE 2, RESUMED — W0g RE-ESTABLISHED UNDER THE RULED PRIVILEGE, AND W1b's WINDOW LAW
#
# EP-29 ADDENDUM 6 §4 (2026-08-12) RULED: RE-HOME THE PRIVILEGE. The observer runs PRIVILEGED
# in the lab guest and the window law NAMES that cost. The first stage-2 pass's verdict —
# `arrival@tracepoints` NOT AVAILABLE — was CORRECT and its stated REASON was FALSE, and the
# re-establishment below does not inherit the reason: every access fact is driven from the
# MOUNT TABLE, the DIRECTORY MODES, the ERRNO and a PRIVILEGED LISTING, never from
# `coverage()`'s reason string.
# =======================================================================================

class ThePrivilegeIsAnINVOCATIONAndNotAConfigurationChange(unittest.TestCase):
    """§4 bounds the ruling: the privilege must be a way of RUNNING the observer, not a
    weakening of the guest. If this pass had chmod'd tracefs or remounted it, the privilege
    would have been paid by every process on the box — the concession §4 says this must not
    be — and the window declarations' access cost would be a false statement."""

    def test_passwordless_sudo_ALREADY_EXISTS_so_nothing_was_granted_here(self):
        d = priv_probe(self)
        self.assertEqual(d["uid"], 0, "the privileged probe did not run privileged")
        self.assertEqual(d["sudo_n"], 0,
                         "`sudo -n true` fails, so the privilege is not available "
                         "non-interactively and the ruled invocation cannot be made")

    def test_the_TRACEFS_MODES_ARE_UNTOUCHED_which_is_what_makes_it_a_privilege(self):
        """THE ROW THAT WOULD CATCH THE CONCESSION. A chmod would show up here as a widened
        mode, and the privilege would have been bought for the whole box instead of for one
        invocation."""
        d = priv_probe(self)
        for p in ("/sys/kernel/tracing", "/sys/kernel/debug"):
            st = d["stat"][p]
            self.assertEqual(st["mode"], "0o700",
                             "%s is no longer 0700 — something widened the filesystem "
                             "instead of raising the observer" % p)
            self.assertEqual(st["uid"], 0, p)


class TheTracefsAccessMechanismIsEstablished(unittest.TestCase):
    """W0g C2's ACCESS MECHANISM, DRIVEN — §4 requires the tracepoint set to be stated WITH
    its access mechanism, and the estate's own `coverage()` CANNOT supply it for this case.

    THE MECHANISM, ESTABLISHED HERE RATHER THAN ASSERTED: `os.path.exists` returns False for
    a TRAVERSAL DENIAL on a path that EXISTS. It is an ACCESS result. The shipped probe reads
    that False as absence-of-facility and reports a kernel-configuration need, which is why
    its verdict was right and its reason was wrong."""

    def test_tracefs_is_MOUNTED_at_both_names(self):
        d = priv_probe(self)
        points = {m[1] for m in d["mounts"]}
        self.assertIn("/sys/kernel/tracing", points)
        self.assertIn("/sys/kernel/debug/tracing", points)
        self.assertTrue(any(m[2] == "tracefs" for m in d["mounts"]),
                        "no tracefs mount at all: %r" % d["mounts"])

    def test_the_two_names_are_ONE_filesystem(self):
        """So there is no canonical-path question to resolve and no second surface to
        declare: one subject, two spellings."""
        d = priv_probe(self)
        a, b = d["stat"]["/sys/kernel/tracing"], d["stat"]["/sys/kernel/debug/tracing"]
        self.assertTrue(a["exists"] and b["exists"])
        self.assertEqual((a["dev"], a["ino"]), (b["dev"], b["ino"]),
                         "the two tracefs names are DIFFERENT filesystems, so the window law "
                         "would have to say which one it declares against")

    def test_UNPRIVILEGED_exists_is_FALSE_on_a_path_that_EXISTS_and_the_errno_says_why(self):
        """THE FALSE REASON, MEASURED. This is the whole of what blocked the first pass."""
        u = unpriv_probe(self)
        p = priv_probe(self)
        self.assertNotEqual(u["uid"], 0, "the unprivileged probe ran privileged")
        self.assertFalse(u["exists"]["/sys/kernel/debug/tracing"])
        self.assertTrue(p["exists"]["/sys/kernel/debug/tracing"],
                        "the path does not exist even privileged, so the reason string was "
                        "right and this pass's ground is wrong")
        self.assertEqual(u["stat"]["/sys/kernel/debug/tracing"]["errno"], errno.EACCES,
                         "the unprivileged failure is not a permission denial, so `exists` "
                         "False is NOT an access result and the mechanism is something else")

    def test_the_access_pair_DISCRIMINATES(self):
        """A probe that answered the same under both privileges would establish nothing."""
        u, p = unpriv_probe(self), priv_probe(self)
        self.assertFalse(u["readable"]["/sys/kernel/tracing"])
        self.assertTrue(p["readable"]["/sys/kernel/tracing"])


class TheTracepointSetIsEstablished(unittest.TestCase):
    """W0g C2 — THE TRACEPOINT SET, from a PRIVILEGED LISTING. ADDENDUM 6 C2's red world: a
    surface LISTED that no probe REACHED reds, so the set below is read off the filesystem."""

    def test_the_event_families_are_present_and_include_the_three_the_validation_set_needs(self):
        d = priv_probe(self)
        self.assertGreater(len(d["families"]), 0, "no event families were listed at all")
        for f in ("block", "irq", "net"):
            self.assertIn(f, d["families"])

    def test_each_needed_family_carries_events_and_the_arithmetic_is_shown(self):
        """A COUNT IS RECONCILED BY ARITHMETIC. `enable` and `filter` are control files and
        are counted OUT by name, which is why this figure is a tracepoint count rather than a
        directory-entry count — the difference is six across the three families."""
        d = priv_probe(self)
        per = {f: len(d["family_events"][f]) for f in ("block", "irq", "net")}
        for f, n in per.items():
            self.assertGreater(n, 0, "family %s listed no events" % f)
        self.assertEqual(sum(per.values()), per["block"] + per["irq"] + per["net"])
        self.assertNotIn("enable", d["family_events"]["block"])
        self.assertNotIn("filter", d["family_events"]["block"])

    def test_the_families_carry_the_IO_SUBJECT_by_name(self):
        """The surface does not merely exist: it carries device I/O, which is the subject the
        two available surfaces disclaim."""
        d = priv_probe(self)
        self.assertIn("block_rq_issue", d["family_events"]["block"])
        self.assertIn("block_rq_complete", d["family_events"]["block"])
        self.assertIn("irq_handler_entry", d["family_events"]["irq"])
        self.assertIn("net_dev_queue", d["family_events"]["net"])

    def test_available_events_reports_a_flat_set_too(self):
        d = priv_probe(self)
        self.assertIsNotNone(d["available_events"], "available_events could not be read")
        self.assertGreater(d["available_events"], sum(
            len(d["family_events"][f]) for f in ("block", "irq", "net")))

    def test_the_listing_is_UNREACHABLE_unprivileged(self):
        """The pair, again, at the listing rather than at the stat: this is the cost the
        window declarations name."""
        u = unpriv_probe(self)
        self.assertEqual(u["families"], [],
                         "an unprivileged observer listed the event families, so the "
                         "privilege the window law prices is not being paid")


class TheArrivalSurfaceIsAvailableToAPrivilegedObserver(unittest.TestCase):
    """W0g C2's VERDICT under the ruled invocation — the estate's OWN window class, the same
    shipped bytes, run at uid 0. THIS IS W1b's REFERENT SET, and it is not empty."""

    def test_the_SAME_shipped_probe_answers_differently_by_PRIVILEGE_ALONE(self):
        unpriv = surfaces_by_key(guest_probe(self))[THE_IO_SURFACE]
        priv = surfaces_by_key(guest_probe_privileged(self))[THE_IO_SURFACE]
        self.assertFalse(unpriv["available"])
        self.assertTrue(priv["available"],
                        "the arrival surface is NOT available even privileged — W1b's ground "
                        "does not exist and the window declarations cite an unreached "
                        "surface, which is C3's own red world: %s" % priv["reason"])
        self.assertEqual(priv["reason"], "ok")
        self.assertEqual(unpriv["version"], priv["version"],
                         "the two readings are of different window versions, so they are not "
                         "a pair and the privilege is not the only thing that varied")

    def test_the_surface_version_the_windows_declare_is_the_one_probed(self):
        priv = surfaces_by_key(guest_probe_privileged(self))[THE_IO_SURFACE]
        self.assertIn(GUEST_KERNEL, priv["version"])
        for w in window_declarations(live_pack()):
            self.assertEqual(w["surface_version"], priv["version"],
                             "%s declares a surface version no probe produced" % w["window"])

    def test_the_ADAPTER_is_still_deferred_and_the_law_does_not_pretend_otherwise(self):
        """THE HONEST WIDTH OF THIS ESTABLISHMENT. The SURFACE is available; the arrival
        ADAPTER is W2's product and is not built here. A window declares ADMISSION, and at
        what granularity an admitted act is RECORDED is the INTAKE declaration — W2's, and
        deliberately absent from this pass."""
        priv = surfaces_by_key(guest_probe_privileged(self))[THE_IO_SURFACE]
        self.assertEqual(priv["sees"], [])
        self.assertIn("DEFERRED", priv["facility"])
        for w in window_declarations(live_pack()):
            self.assertNotIn("granularity", w,
                             "%s declares a granularity; that is W2's first product and this "
                             "pass must not land it by drift" % w["window"])


# =======================================================================================
# W1b — THE WINDOW LAW
# =======================================================================================

class TheWindowLawLanded(unittest.TestCase):
    """C3 — the I/O WINDOW DECLARATIONS, against C2's ESTABLISHED inventory ONLY."""

    def test_exactly_the_two_established_windows_are_declared(self):
        got = tuple(sorted(w["window"] for w in window_declarations(live_pack())))
        self.assertEqual(got, tuple(sorted(THE_DECLARED_WINDOWS)))

    def test_every_window_cites_the_ESTABLISHED_surface_and_no_other(self):
        """C3's red world: a window declared against an UNESTABLISHED surface is the
        wrong-reference class authored into law. The two available surfaces DISCLAIM device
        I/O in their own coverage, so borrowing one would be the same class wearing a
        reachable name."""
        for w in window_declarations(live_pack()):
            self.assertEqual(w["surface"], "arrival@tracepoints",
                             "%s declares against %r" % (w["window"], w["surface"]))

    def test_every_window_PRICES_its_access_K12(self):
        """K12: every view costs its own dependencies, PRICED AT AUTHORING. A window whose
        surface only a privileged observer can read has bought a privilege, and a declaration
        that omitted it would price the view at zero."""
        for w in window_declarations(live_pack()):
            self.assertEqual(w["access"], "privileged", w["window"])
            self.assertIn("EACCES", w["access_mechanism"],
                          "%s states an access mechanism that does not name the measured "
                          "refusal" % w["window"])
            self.assertIn("LAB GUEST", w["access_scope"])
            self.assertIn("NO DEPLOYED UNPRIVILEGED", w["access_scope"],
                          "%s does not bound the privilege, so W3's kernel half and any "
                          "deployed component could read it as inherited" % w["window"])

    def test_every_window_states_what_it_does_NOT_see(self):
        """The window contract the estate's own observe layer already holds: a window states
        its blind spots. `sees` and `does_not_see` are REQUIRED parameters, which is the
        no-bare-form instruction extended from parameter forms to parameter ABSENCES."""
        for w in window_declarations(live_pack()):
            self.assertTrue(w["sees"], w["window"])
            self.assertGreaterEqual(len(w["does_not_see"]), 3, w["window"])
            blind = " ".join(w["does_not_see"])
            self.assertIn("STREAM", blind,
                          "%s does not classify content out; I/O CONTENT is STREAM traffic "
                          "and is never recorded" % w["window"])

    def test_the_two_new_ops_declare_an_EXPLICIT_form_for_every_parameter(self):
        """C7 on this pass's population: every definition it AUTHORS. A parameter form taken
        by silence is not declining the choice, it is taking it undecided."""
        ops = ops_of(live_pack())
        for name in ("DECLARE-IO-WINDOW", UNDECLARED_IO_ACT):
            d = ops[name]
            self.assertTrue(d.get("params"), name)
            for p, form in d["params"].items():
                self.assertIn(form, ("required", "optional"), "%s.%s = %r" % (name, p, form))
            known = set(d.get("params") or {}) | set(d.get("param_defaults") or {})
            self.assertEqual(set(d.get("payload_from") or []) - known, set(),
                             "%s writes a field it never declared" % name)

    def test_no_cited_law_id_of_this_passs_own_ops_is_UNDECLARED(self):
        """The UNDECLARED-LAW-ID lesson: declare what you cite. This binds THIS pass's own
        ops and claims nothing about the other twelve, which stay pinned above."""
        w = _World()
        rules = w.views.active_rules()
        ops = ops_of(live_pack())
        for name in ("DECLARE-IO-WINDOW", UNDECLARED_IO_ACT):
            d = ops[name]
            self.assertIn(d["law_cited"], rules, "%s cites an undeclared law" % name)
            for c in d.get("checks") or []:
                if c.get("cite"):
                    self.assertIn(c["cite"], rules,
                                  "%s's %s check cites an undeclared law" % (name, c["check"]))
        for rec in window_declarations(live_pack(), whole=True):
            self.assertIn(rec["rule_cited"], rules,
                          "a window declaration cites an undeclared law")

    def test_C6_holds_no_new_check_kind(self):
        """[DOCUMENTED FLIP -- EP-30-W3, 2026-08-19, charter §A57 BY FALSIFICATION; the one
        HISTORICAL-subject member of this pass's sweep population, taken from its own suite
        arm at BOTH widths. CAUSE: EP-30-W2 gave DEVICE-IO-WINDOW-WRITE a `prior_value`
        check over BIND-DEVICE's stream, so the LIVE kind set over these two operations is
        now {'require_prior', 'prior_value'}. ASSERTED: W1b's two operations declare checks
        of exactly one kind, read off THE WORKING TREE. SUPERSEDED: read off W1b's OWN CLOSE
        COMMIT -- both ends are now commits. REMAINS TRUE, unchanged in subject and in every
        literal: W1b ADDED NO NEW CHECK KIND, which is this row's whole claim and is a fact
        about W1b's LANDING rather than about today's law. GIVEN UP: nothing. A claim about
        the LIVE vocabulary was never this row's subject -- the live-vocabulary rows carry
        that and none of them is touched here.

        WHAT PUT THIS ROW IN THE POPULATION WAS THE OPEN END AND NOT A LITERAL, which is the
        same trap `TheFoundingStandsBYTEUNCHANGEDAfterW3b` records one movement earlier: this
        row names no version and it joined a founding move's sweep anyway, because
        `live_pack()` IS NOT A COMMIT. A CLOSED-RANGE READ IS IMMUNE; AN OPEN-ENDED ONE IS
        NOT, however carefully its literals were avoided.

        THE PIN IS DERIVED INDEPENDENTLY OF THE PROPERTY THIS ROW ASSERTS (`:1057`).
        `W1B_AFTER_COMMIT` was selected by EP-28ZD from the FOUNDING VERSION's history --
        the last commit at which the shipped founding still read 1.20.0 -- and this row
        asserts about CHECK KINDS on two named operations. A pin chosen as "the last commit
        whose kinds were still require_prior only" would have selected BY the assertion and
        left the row unable to fail; this one did not, so the row can still fail. THE AFTER
        END IS RECORDED BY DIGEST and checked below rather than trusted.

        POPULATION: DECLARE-IO-WINDOW and DEVICE-IO-WINDOW-WRITE as they stood at W1b's
        close. BASIS: their own `checks` declarations, read out of git through
        `tests/era_pin.py`, the one home, never off the live tree."""
        self.assertEqual(
            hashlib.sha256(era_pin.blob_at(W1B_AFTER_COMMIT, era_pin.PACK_PATH)).hexdigest(),
            W1B_AFTER_PACK_SHA,
            "the era's pack is not the one this pin was recorded against, so the reading "
            "below is about some other world")
        ops = ops_of(era_pin.pack_at(W1B_AFTER_COMMIT))
        kinds = {c["check"] for n in ("DECLARE-IO-WINDOW", UNDECLARED_IO_ACT)
                 for c in (ops[n].get("checks") or [])}
        self.assertTrue(kinds, "the new ops declare no checks at all, which would make the "
                               "window citation unenforced")
        self.assertEqual(kinds - set(opdefs.OP_CHECKS), set())
        self.assertEqual(kinds, {"require_prior"})


class TheWindowAdmissionFlippedAndTheRefusalNarrowed(unittest.TestCase):
    """C5 — after W1b, declared-window I/O ADMITS per its declaration and every undeclared
    case STILL refuses citing absence. THE REFUSAL WAS NARROWED, NEVER REMOVED.

    ITEM-21 NON-VACUITY: the bind is proven live before any admission or refusal is read."""

    def setUp(self):
        self.w = _World()
        self.w.call("REGISTER-CAPABILITY", driver="drv-blk", device_class="block",
                    capabilities=["irq:25"])
        self.w.call("BIND-DEVICE", device="virtio1", driver="drv-blk")
        from subsystems.devices import DevicesView
        self.assertEqual(DevicesView(self.w.store).bindings(), {"virtio1": "drv-blk"},
                         "the bind is not live, so everything below is the empty world")

    def test_a_DECLARED_window_ADMITS_and_the_record_carries_the_citation(self):
        rec = self.w.call(UNDECLARED_IO_ACT, device="virtio1", window="device-io@block",
                          bytes=4096)
        self.assertEqual(rec["action"], UNDECLARED_IO_ACT)
        self.assertFalse(rec.get("refused"))
        self.assertEqual(rec["rule_cited"], "DEV-LAW-BIND")
        self.assertEqual(dict(rec["payload"])["window"], "device-io@block")

    def test_an_UNDECLARED_window_NAME_refuses_and_is_recorded(self):
        before = len(list(self.w.store.all()))
        with self.assertRaises(OpError) as ctx:
            self.w.call(UNDECLARED_IO_ACT, device="virtio1", window="device-io@borrowed",
                        bytes=4096)
        appended = list(self.w.store.all())[before:]
        self.assertEqual(ctx.exception.rule, "DEV-LAW-BIND")
        self.assertEqual(len(appended), 1, "the refusal must be RECORDED, not merely raised")
        self.assertTrue(appended[0]["refused"])

    def test_a_LAW_ID_may_not_pass_as_a_window(self):
        """THE BORROWED-NAME BRANCH, SHUT BY CONSTRUCTION AND DRIVEN. The citation is keyed on
        the DECLARE-IO-WINDOW action rather than on law records generally, so no rule id in
        the founding answers for a window. Keying it on `CREATE-RULE`/`rule_id` would have
        admitted every one of them, which is why the check names the action it does."""
        for borrowed in ("CAP-IS-LAW", "DEV-LAW-BIND", "BOOT-INT"):
            with self.assertRaises(OpError) as ctx:
                self.w.call(UNDECLARED_IO_ACT, device="virtio1", window=borrowed, bytes=4)
            self.assertEqual(ctx.exception.rule, "DEV-LAW-BIND", borrowed)

    def test_IO_over_a_device_no_record_ever_bound_refuses(self):
        """A bind grants the custody I/O needs, so admission without one is refused even with
        a perfectly declared window."""
        with self.assertRaises(OpError) as ctx:
            self.w.call(UNDECLARED_IO_ACT, device="never-bound", window="device-io@block",
                        bytes=4)
        self.assertEqual(ctx.exception.rule, "DEV-LAW-BIND")

    def test_an_act_class_the_law_founds_NO_declaration_for_STILL_refuses(self):
        """C5's "never vanished" half, at the LIVE law rather than at an era."""
        with self.assertRaises(OpError) as ctx:
            self.w.call(STILL_UNDECLARED_IO_ACT, device="virtio1", window="device-io@block",
                        bytes=4)
        self.assertEqual(ctx.exception.rule, "P3-CLOSURE")

    def test_the_LAW_ITSELF_no_longer_says_the_windows_are_unlanded(self):
        law = dict(self.w.views.active_rules()["DEV-LAW-BIND"])["text"]
        self.assertNotIn("NOT in this founding yet", law)
        self.assertIn("THE WINDOW DECLARATIONS HAVE LANDED", law)

    def test_the_amendment_did_not_drop_the_clauses_W1a_authored(self):
        """A law amended by substitution can lose a sentence silently. Each clause W1a's own
        battery asserts is re-asserted here AFTER the amendment."""
        law = dict(self.w.views.active_rules()["DEV-LAW-BIND"])["text"]
        for clause in ("CUSTODY", "NOT I/O", "CITES A WINDOW DECLARATION BY NAME",
                       "PERMITTED BY NOTHING", "REFUSES"):
            self.assertIn(clause, law, "the amendment dropped %r" % clause)


class TheFoundingMovedAgainAtStage2(unittest.TestCase):
    """C4 — the founding MOVES and BYTE-UNCHANGED IS THE FAILING OUTCOME for a law pass."""

    def test_the_pack_version_moved_one_MINOR_from_the_STAGE_2_BEFORE(self):
        # [DOCUMENTED FLIP — EP-28ZD, 2026-08-13, charter §A57. CAUSE: the founding moved
        # 1.20.0 -> 1.21.0. ASSERTED: `live_pack()` as W1b's AFTER. SUPERSEDED:
        # `pack_at(W1B_AFTER_COMMIT)`. REMAINS TRUE: W1b moved the founding exactly one MINOR,
        # 1.19.0 -> 1.20.0, which is a fact about two commits and was never a fact about
        # today's tree — the same correction W1b itself made to W1a one stage back. GIVEN UP:
        # nothing; the LIVE tree's own version is asserted by EP-28ZD's own battery.]
        self.assertEqual(pack_at(W1B_BEFORE_COMMIT)["founding_version"], W1B_BEFORE_VERSION)
        self.assertEqual(pack_at(W1B_AFTER_COMMIT)["founding_version"], W1B_AFTER_VERSION)

    def test_the_founding_is_NOT_byte_unchanged(self):
        """C4's red world, at its own position: the founding standing byte-unchanged after
        W1b REDS, because byte-unchanged is the FAILING outcome for a law pass. The one
        exception — an empty W0g inventory, where W1b never lawfully runs and this world is
        never reached — does not apply: the inventory is non-empty and asserted so above."""
        era = era_pin.blob_at(W1B_BEFORE_COMMIT, era_pin.PACK_PATH)
        with open(PACK_PATH, "rb") as fh:
            live = fh.read()
        self.assertNotEqual(hashlib.sha256(era).hexdigest(),
                            hashlib.sha256(live).hexdigest(),
                            "the founding is byte-unchanged after a LANDED W1b")

    def test_the_designation_record_carries_the_NEW_version(self):
        # [DOCUMENTED FLIP — EP-28ZD, 2026-08-13, charter §A57. CAUSE: the founding moved
        # 1.20.0 -> 1.21.0, so a world booted from the LIVE tree stamps 1.21.0 and this row's
        # constant describes W1b's era. ASSERTED: `_World()`, the live tree. SUPERSEDED:
        # `_World(pack_at(W1B_AFTER_COMMIT))`, W1b's own era. REMAINS TRUE, and the row stays a
        # genuine TWO-SIDED check rather than becoming one reading wearing two labels
        # (test_ep26.py:1242's warning): a pack read out of git on one side, a designation
        # record stamped by the installer on the other. GIVEN UP: nothing — the LIVE stamp is
        # asserted against 1.21.0 by EP-28ZD's own battery, which is where that era belongs.]
        w = _World(pack_at(W1B_AFTER_COMMIT))
        fs = [e for e in w.store.all() if e["action"] == "FOUND-STORE"][0]
        self.assertEqual(dict(fs["payload"])["founding_version"], W1B_AFTER_VERSION)

    def test_THE_RULED_VERSION_TEST_the_1_19_0_pack_byte_unchanged_STILL_LOADS(self):
        """THE RULED TEST, BUILDER-EXECUTED: loads -> MINOR; does not -> MAJOR -> STOP TO THE
        MENTOR. It answered MINOR, and it is kept as a standing row so anyone later can
        re-check the answer rather than take it."""
        install_module._validate(install_module.records(pack_at(W1B_BEFORE_COMMIT)))

    def test_the_loader_that_accepted_it_CAN_REFUSE(self):
        """Without this the row above is an instrument that cannot report its own failure."""
        p = pack_at(W1B_BEFORE_COMMIT)
        for st in p["steps"]:
            for r in st["records"]:
                if (r.get("payload") or {}).get("name") == "BIND-DEVICE":
                    r["payload"]["definition"]["checks"] = [
                        {"check": "planted_unknown_kind", "cite": "DEV-LAW-BIND"}]
        with self.assertRaises(Exception) as ctx:
            install_module._validate(install_module.records(p))
        self.assertIn("planted_unknown_kind", str(ctx.exception))

    def test_the_new_ops_are_EXACTLY_the_two_this_pass_added(self):
        # [DOCUMENTED FLIP — EP-29 W2b, 2026-08-13, charter §A57. CAUSE: W2b adds a third op,
        # DECLARE-INTAKE, so the LIVE set minus W1b's BEFORE is three names and not two.
        # ASSERTED: `live_pack()` as W1b's AFTER. SUPERSEDED: `pack_at(W1B_AFTER_COMMIT)`,
        # the era EP-28ZD already pinned into this file and verified by content. REMAINS
        # TRUE: W1b added exactly those two, which is a fact about two commits. GIVEN UP:
        # nothing — W2b asserts its own single-op delta at TheFoundingMovedAtW2b.
        # WORTH THE LINE: this row was the ONLY one of the four on the previous pass's
        # NEXT_MOVE_FALSIFIES-style expectations that actually reddened here, and it was on
        # no worklist at all.]
        before = set(ops_of(pack_at(W1B_BEFORE_COMMIT)))
        now = set(ops_of(pack_at(W1B_AFTER_COMMIT)))
        self.assertEqual(sorted(now - before), ["DECLARE-IO-WINDOW", UNDECLARED_IO_ACT])
        self.assertEqual(before - now, set(), "this pass removed an op")


class TheSweepWasNotEmpty(unittest.TestCase):
    """§A57 BY FALSIFICATION — the sweep this pass owed, named row by row so a later reader
    can check the list rather than trust it.

    THE STOPPED PASS HANDED FORWARD A WORKLIST OF FOUR AND THE TRUE POPULATION WAS TWELVE
    ACROSS SEVEN FILES. That is not a criticism of the worklist: it named every row IT could
    see, which were the live-tree reads in its OWN file, and it could not see the population
    rows in six other files that only a pass ADDING AN OP would falsify. The finding is that a
    handed-forward worklist is a floor and never the bound, and the bound is a suite run."""

    #: (file, dotted row, what this pass's move falsified). Each is verified to exist below.
    SWEPT = (
        ("tests/test_ep28i.py", "TestThePopulationIsComputedNotCarried", "72 ops -> 74"),
        ("tests/test_ep28j.py", "TPopulation", "72 ops -> 74; name-shape 60 -> 62"),
        ("tests/test_ep28j.py", "TDivergenceTable", "partition 72 -> 74; absent 50 -> 52"),
        ("tests/test_ep28k.py", "TestThePopulationsAreComputedNotCarried", "72 ops -> 74"),
        ("tests/test_ep28k.py", "TestTheCheckSetComesFromStructure", "65 excluded -> 67"),
        ("tests/test_ep28n2.py", "TestAbsenceStaysAbsence", "67 untouched -> 69"),
        ("tests/test_ep28n2.py", "TestTheDiffIsTheChange", "two ops read as this pass's own"),
        ("tests/test_ep28p.py", "TestTheVERSIONQuestionWasEXECUTEDAndTookMINOR", "72 -> 74"),
        ("tests/test_ep29.py", "TheDeviceLawIsDeclared", "1.19.0 -> 1.20.0"),
        ("tests/test_ep29.py", "TheFoundingMoved", "1.19.0 -> 1.20.0"),
        ("tests/test_ep29.py", "TheFailClosedIntermediateState", "the I/O act gained a law"),
        ("tests/test_ep29.py", "TheIOWindowGroundIsEstablishedAbsent", "the stop was lifted"),
        ("tests/test_ep29.py", "TheFoundingStandsUnmovedAndTheSweepPopulationIsEmpty",
         "the founding moved"),
    )

    def test_every_swept_site_names_a_real_file(self):
        for path, _cls, _why in self.SWEPT:
            self.assertTrue(os.path.exists(os.path.join(REPO, path)), path)

    def test_every_swept_class_in_THIS_file_still_exists(self):
        """The rows in other files cannot be resolved from here without importing them, and
        importing six suites to check a list would run them. THIS file's are resolved."""
        for path, cls, _why in self.SWEPT:
            if path == "tests/test_ep29.py":
                self.assertIsNotNone(globals().get(cls), "no such class: %s" % cls)

    def test_the_sweep_touched_SIX_files_and_the_arithmetic_is_shown(self):
        """[CORRECTED IN THE SAME PASS THAT WROTE IT — this row was written asserting SEVEN
        and the list holds SIX. The seventh in my head was `tests/test_ep28n.py`, whose only
        red was the J9 attestation row, and a J9 red is NOT a §A57 flip: it is the standing
        obligation that the founding on disk be named with its own hash in one BUILD-PROGRESS
        entry, discharged by writing the entry rather than by editing a row. Recorded rather
        than silently corrected, because the near-miss is the useful part: an ATTESTATION red
        and a FALSIFICATION red look identical in a suite tail and route to different doors.]"""
        files = sorted({p for p, _c, _w in self.SWEPT})
        self.assertEqual(len(files), 6, files)
        self.assertNotIn("tests/test_ep28n.py", files,
                         "test_ep28n is on the flip list; its red was the J9 attestation, "
                         "which no edit to a row can fix")

    def test_the_ERA_PIN_METHOD_IS_IMPORTED_AND_NOT_RE_DERIVED(self):
        """C4's other red world: a re-derived era-pin idiom REDS, and the class it reds is the
        eighteen copies EP-28Z retired out of ten files.

        [WRITTEN TWICE, AND THE FIRST VERSION IS RECORDED BECAUSE IT IS THIS ESTATE'S
        MOST-REPEATED DEFECT COMMITTED INSIDE THE ROW MEANT TO CATCH IT. The first version
        asserted `'"show"' not in <this file's source>` — a filter that matched the ordinary
        English word in a docstring and reported a re-derivation that does not exist. It also
        opened with `assertIs(pack_at.__module__ and era_pin.pack_at, era_pin.pack_at)`, which
        is true for any two references to one object and could not fail. AN ABSENCE TEST OVER A
        GROWING FILE AND A COMPARISON OF A THING WITH ITSELF: two of §7.1's disguises in three
        lines. REPLACED BY A PRESENCE TEST — this file's era reads and the home's are shown to
        produce THE SAME BYTES, which fails loudly if `pack_at` ever stops delegating.]"""
        self.assertEqual(pack_at(W1B_BEFORE_COMMIT),
                         era_pin.pack_at(W1B_BEFORE_COMMIT),
                         "this file's era read and the one home's disagree")
        self.assertEqual(
            hashlib.sha256(era_pin.blob_at(W1B_BEFORE_COMMIT, era_pin.PACK_PATH)).hexdigest(),
            hashlib.sha256(json.dumps(pack_at(W1B_BEFORE_COMMIT), indent=2,
                                      ensure_ascii=False).encode("utf-8") + b"\n").hexdigest(),
            "the era read does not reproduce the era's own bytes")
        self.assertEqual(os.path.dirname(os.path.abspath(era_pin.__file__)),
                         os.path.join(REPO, "tests"),
                         "era_pin resolved to something other than the estate's one home")


class TheReHomedLiveClaims(unittest.TestCase):
    """CLAIMS THIS PASS'S §A57 SWEEP WOULD OTHERWISE HAVE NARROWED, RE-HOMED RATHER THAN LOST.

    Era-pinning a predecessor's row makes it honest about its own era and, where that row also
    carried a LIVE claim about whatever founding ships, silently narrows it. §A57's fence
    permits no NEW row in the swept file, so the live half lands here — in the pass that owns
    the current era. Each row below names the site it came from."""

    def test_the_whole_shipped_founding_still_validates(self):
        """RE-HOMED FROM tests/test_ep28i.py::TestThePopulationIsComputedNotCarried::
        test_every_declared_mint_passes_the_guard_in_the_shipped_pack, which now reads
        EP-28I's era. A guard whose only evidence is that nothing refused it has not been
        shown to admit anything either — so this validates every op that SHIPS."""
        ops = ops_of(live_pack())
        self.assertGreater(len(ops), 0)
        for name, d in ops.items():
            opdefs.validate_definition_shape(_ShapeDoor(), "FOUNDING", "SYSTEM", name, d)

    def test_the_shape_door_used_above_CAN_REFUSE(self):
        """Without this the row above is a guard that cannot report a failure."""
        with self.assertRaises(Exception):
            opdefs.validate_definition_shape(
                _ShapeDoor(), "FOUNDING", "SYSTEM", "PLANTED",
                {"law_cited": "CAP-IS-LAW",
                 "checks": [{"check": "planted_unknown_kind", "cite": "CAP-IS-LAW"}]})

    def test_the_ep28k_exclusion_arithmetic_can_still_fail(self):
        """RE-HOMED FROM tests/test_ep28k.py::TestTheCheckSetComesFromStructure::
        test_the_sixty_five_excluded_ops_carry_no_binding_declaration, whose frozen 72 this
        pass replaced with a count computed from the pack's structure. That arithmetic looks
        like a tautology and is not: |ops - ENUM| == |ops| - |ENUM| holds exactly when ENUM is
        a SUBSET of ops, so it reds if an enumerated op is ever retired. DRIVEN here."""
        ops = {"A": {}, "B": {}, "C": {}}
        enumerated = ("A", "B")
        excluded = set(ops) - set(enumerated)
        self.assertEqual(len(excluded), len(ops) - len(enumerated))   # the subset case
        retired = ("A", "GONE")                                       # one name not in ops
        excluded = set(ops) - set(retired)
        self.assertNotEqual(len(excluded), len(ops) - len(retired),
                            "the arithmetic cannot see a retired enumerated op, so it IS the "
                            "tautology it looks like and buys nothing")


class TheW1bRowsCanBeMadeToFail(unittest.TestCase):
    """RED WORLDS FOR THE WINDOW LAW, DRIVEN THROUGH THE REAL ROWS on synthetic packs.

    Each plants a defect in a COPY of the live pack and runs the ACTUAL row against it, so no
    predicate is restated — a red world that re-implements the assertion it tests proves only
    that two copies agree. CONTROL FIRST: the unmutated copy must PASS every row, or a red
    below could be the copy being malformed rather than the clause biting."""

    def _copy(self):
        return copy.deepcopy(live_pack())

    def _run(self, pack, meth):
        """Run one REAL row of `TheWindowLawLanded` against `pack` by pointing this file's
        `live_pack` at it for the call. The row's own body is what executes."""
        global live_pack
        original = live_pack
        live_pack = lambda: pack                              # noqa: E731
        try:
            case = TheWindowLawLanded(meth)
            res = unittest.TestResult()
            case.run(res)
            return res
        finally:
            live_pack = original

    def assertRowFAILED(self, res, why):
        """A RED WORLD MUST RED FOR ITS OWN REASON.

        [WRITTEN WEAK AND CORRECTED IN THE SAME PASS, RECORDED BECAUSE THE MECHANISM IS THE
        ESTATE'S MOST-REPEATED ONE. The first version was `assertTrue(res.failures or
        res.errors)`, which an ERROR satisfies — so a planted payload that broke the
        instrument (a KeyError, a bad shape) would have read on the page exactly like the
        claim biting. THE CORRECT HELPER WAS ALREADY IN THIS FILE, forty rows up, written by
        the previous pass with a docstring saying precisely this, AND I HAD READ IT. That is
        board :411 — reading a defect is not inheriting its fix — with a fifth data point, in
        the same file as the fourth.]"""
        self.assertEqual(res.errors, [],
                         "the row ERRORED rather than failed, so the planted pack broke the "
                         "instrument instead of the claim: %r" % (res.errors,))
        self.assertEqual(len(res.failures), 1, why)

    def test_the_synthetic_control_PASSES_every_row(self):
        """Without this, every red below is uninterpretable."""
        pack = self._copy()
        for meth in ("test_exactly_the_two_established_windows_are_declared",
                     "test_every_window_cites_the_ESTABLISHED_surface_and_no_other",
                     "test_every_window_PRICES_its_access_K12",
                     "test_every_window_states_what_it_does_NOT_see"):
            res = self._run(pack, meth)
            self.assertFalse(res.failures or res.errors,
                             "the unmutated copy fails %s: %r" % (meth, res.failures))

    def test_a_window_declared_against_an_UNESTABLISHED_surface_REDS(self):
        """C3's own red world: a window declared against a surface no probe reached is the
        wrong-reference class authored into law. Here it borrows `device@sysfs` — a surface
        that IS established and that DISCLAIMS device I/O in its own coverage, which is the
        exact branch ADDENDUM 6 §4 refused by name."""
        pack = self._copy()
        for st in pack["steps"]:
            for r in st["records"]:
                if r.get("action") == "DECLARE-IO-WINDOW":
                    r["payload"]["surface"] = "device@sysfs"
        res = self._run(pack, "test_every_window_cites_the_ESTABLISHED_surface_and_no_other")
        self.assertRowFAILED(res, "a window citing a surface that disclaims device I/O passes")

    def test_a_window_that_HIDES_its_access_cost_REDS(self):
        """K12's red world: a privileged view declared as free prices the dependency at zero."""
        pack = self._copy()
        for st in pack["steps"]:
            for r in st["records"]:
                if r.get("action") == "DECLARE-IO-WINDOW":
                    r["payload"]["access"] = "unprivileged"
        res = self._run(pack, "test_every_window_PRICES_its_access_K12")
        self.assertRowFAILED(res, "a window declaring free access to a privileged surface passes")

    def test_a_window_that_does_NOT_bound_the_privilege_to_the_lab_REDS(self):
        """§4's boundary is what keeps this architectural rather than a concession: W3's
        kernel half inherits nothing and no deployed unprivileged component reads tracefs."""
        pack = self._copy()
        for st in pack["steps"]:
            for r in st["records"]:
                if r.get("action") == "DECLARE-IO-WINDOW":
                    r["payload"]["access_scope"] = "wherever the observer runs"
        res = self._run(pack, "test_every_window_PRICES_its_access_K12")
        self.assertRowFAILED(res, "an unbounded privilege scope passes")

    def test_a_BARE_window_declaring_nothing_it_sees_REDS(self):
        """The no-bare-form instruction extended from parameter forms to parameter ABSENCES:
        a window declaring nothing it sees would still admit its act class while claiming no
        observability — the comforting fallback wearing a declaration."""
        pack = self._copy()
        for st in pack["steps"]:
            for r in st["records"]:
                if r.get("action") == "DECLARE-IO-WINDOW":
                    r["payload"]["sees"] = []
        res = self._run(pack, "test_every_window_states_what_it_does_NOT_see")
        self.assertRowFAILED(res, "a window seeing nothing passes")

    def test_a_window_that_declares_a_GRANULARITY_REDS(self):
        """W2's seam, guarded: the intake declaration's granularity is W2's first product and
        this pass must not land it by drift."""
        pack = self._copy()
        for st in pack["steps"]:
            for r in st["records"]:
                if r.get("action") == "DECLARE-IO-WINDOW":
                    r["payload"]["granularity"] = "per-interrupt"
        global live_pack
        original = live_pack
        live_pack = lambda: pack                              # noqa: E731
        try:
            case = TheArrivalSurfaceIsAvailableToAPrivilegedObserver(
                "test_the_ADAPTER_is_still_deferred_and_the_law_does_not_pretend_otherwise")
            res = unittest.TestResult()
            case.run(res)
        finally:
            live_pack = original
        if res.skipped:
            self.skipTest("SKIP LONG-BOOT: GUEST: the row this red world drives could not reach the guest "
                          "(%s)" % res.skipped[0][1][:120])
        self.assertRowFAILED(res, "a window declaring a granularity passes")

    def test_a_MISSING_window_REDS_the_enumeration(self):
        pack = self._copy()
        for st in pack["steps"]:
            st["records"] = [r for r in st["records"]
                             if not (r.get("action") == "DECLARE-IO-WINDOW"
                                     and r["payload"]["window"] == "device-io@net")]
        res = self._run(pack, "test_exactly_the_two_established_windows_are_declared")
        self.assertRowFAILED(res, "a missing window passes the enumeration")

    def test_an_op_taking_a_parameter_form_BY_SILENCE_REDS(self):
        """C7's red world at this pass's own population."""
        pack = self._copy()
        for st in pack["steps"]:
            for r in st["records"]:
                if (r.get("payload") or {}).get("name") == UNDECLARED_IO_ACT:
                    r["payload"]["definition"]["payload_from"] = (
                        r["payload"]["definition"]["payload_from"] + ["planted_undeclared"])
        res = self._run(pack, "test_the_two_new_ops_declare_an_EXPLICIT_form_for_every_parameter")
        self.assertRowFAILED(res, "an op writing an undeclared field passes")

    def test_an_op_citing_an_UNDECLARED_law_id_REDS(self):
        """The UNDECLARED-LAW-ID lesson's own red world — the defect W1a repaired one instance
        of, planted back into this pass's own ops."""
        pack = self._copy()
        for st in pack["steps"]:
            for r in st["records"]:
                if (r.get("payload") or {}).get("name") == "DECLARE-IO-WINDOW":
                    r["payload"]["definition"]["law_cited"] = "DEV-LAW-NOBODY-DECLARED"
        res = self._run(pack, "test_no_cited_law_id_of_this_passs_own_ops_is_UNDECLARED")
        self.assertRowFAILED(res, "an op citing an undeclared law id passes")


# =======================================================================================
# W1c — THE ARRIVAL PROBE'S THREE STATES, DRIVEN (EP-29 ADDENDUM 6 §5/§6)
#
# THE DEFECT REPAIRED: `ArrivalWindow._probe` tested `os.path.exists("/sys/kernel/debug/
# tracing")` and, on False, reported "no /sys/kernel/debug/tracing on this host … configuring
# the kernel for them is outside this EP's fence". `os.path.exists` RETURNS FALSE FOR A
# TRAVERSAL DENIAL ON A PATH THAT EXISTS, so that sentence asserted a host capability and a
# kernel-configuration need where an ACCESS RESULT had been measured — a view asserting what
# it did not measure, in the observe layer itself. The truthful branch was unreachable.
#
# WHY THE MIDDLE STATE IS DRIVEN AT A CONSTRUCTED WORLD AND NOT AT THE GUEST (EP-29 :599).
# The repair re-points the probe to `/sys/kernel/tracing`, whose parent `/sys/kernel` is 0755
# and therefore traversable — driven, and `/sys/kernel/NO_SUCH_THING` returning ENOENT rather
# than EACCES is what proves it. So at the guest the re-pointed probe stats successfully and
# yields PRESENT-BUT-UNREADABLE. THE RE-POINT RETIRES THE ONLY PATH THAT PRODUCED THE DENIED
# STATE, and after this repair the guest cannot produce it at all. A builder who drove this
# state at the guest would get the third state wearing the second one's name.
#
# NON-VACUITY, because these rows run on THIS HOST and the estate's standing discipline is
# that a host reading about the guest is a reading about the wrong box: THE SUBJECT HERE IS
# NOT THE GUEST. It is the shipped `_probe`'s own cause distinction, and the worlds it is
# driven against are built on disk by these rows. The one row whose subject IS the guest says
# so in its name and goes through `guest_probe`.
# =======================================================================================

import shutil                                                    # noqa: E402
from observe import windows as _W                                # noqa: E402

#: The window class the rows below drive. Named as DATA so a red world can plant a MUTANT
#: probe and run the REAL row against it — §A64's rule that a red world which re-implements
#: the assertion it is testing proves only that two copies agree.
_ARRIVAL_CLASS = [_W.ArrivalWindow]


def _arrival_at(path):
    """The shipped window class, pointed at a constructed path. NO PREDICATE IS RESTATED
    HERE: `_probe` is the estate's own method, exactly as the guest driver runs the estate's
    own methods rather than this file's reading of them."""
    return type("_ArrivalAt", (_ARRIVAL_CLASS[0],), {"tracefs_path": path})()


class TheArrivalProbeSpeaksThreeStates(unittest.TestCase):
    """The three states, each DRIVEN at a world built for it, and each read off the shipped
    method's own return value."""

    def setUp(self):
        if os.geteuid() == 0:
            self.skipTest("AUTH: this arm runs as root, and root is refused nothing — every "
                          "access-denial world below would collapse into its readable case "
                          "and the rows would pass without measuring anything")
        self.tmp = tempfile.mkdtemp(prefix="ep29-w1c-")

    def tearDown(self):
        for root, dirs, _ in os.walk(self.tmp):
            for d in dirs:
                os.chmod(os.path.join(root, d), 0o700)   # reopen what was closed, then remove
        os.chmod(self.tmp, 0o700)
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- the three worlds, each built and returned with the raw observation that defines it --

    def _absent(self):
        return os.path.join(self.tmp, "no-such-tracefs")

    def _denied(self):
        """A scratch path behind a MODE-000 PARENT: the child EXISTS and the walk to it is
        refused, which is the only shape that produces an undetermined presence."""
        parent = os.path.join(self.tmp, "closed-parent")
        os.mkdir(parent)
        child = os.path.join(parent, "tracing")
        os.mkdir(child)
        os.chmod(parent, 0o000)
        return child

    def _present_unreadable(self):
        p = os.path.join(self.tmp, "present-unreadable")
        os.mkdir(p)
        os.chmod(p, 0o000)
        return p

    def test_ABSENT_an_ENOENT_world_says_the_kernel_reports_it_not_there(self):
        path = self._absent()
        with self.assertRaises(FileNotFoundError):
            os.stat(path)                      # the raw observation this state is defined by
        ok, reason = _arrival_at(path)._probe()
        self.assertFalse(ok)
        self.assertIn("not there", reason)
        self.assertIn("errno 2", reason)
        self.assertNotIn("present", reason,
                         "an absent path is reported as present: %s" % reason)
        self.assertNotIn("UNDETERMINED", reason,
                         "the kernel answered ENOENT, so presence is DETERMINED and calling "
                         "it undetermined understates a real measurement: %s" % reason)

    def test_DENIED_a_traversal_refusal_says_PRESENCE_UNDETERMINED(self):
        """THE STATE THE SHIPPED PROBE COULD NOT SPEAK. It had two words for three worlds,
        so this one came out wearing the absent one's sentence."""
        path = self._denied()
        with self.assertRaises(PermissionError):
            os.stat(path)                      # the raw observation this state is defined by
        ok, reason = _arrival_at(path)._probe()
        self.assertFalse(ok)
        self.assertIn("UNDETERMINED", reason)
        self.assertIn("errno %d" % errno.EACCES, reason)
        self.assertNotIn("present", reason,
                         "THE REPAIR'S OWN RED WORLD, INVERTED: a refusal reported as "
                         "presence is the same forbidden class as a refusal reported as "
                         "absence, and it is what this row exists to catch: %s" % reason)
        self.assertNotIn("not there", reason,
                         "the ORIGINAL defect, restored: an access result reported as a "
                         "fact about the host's kernel: %s" % reason)

    def test_PRESENT_BUT_UNREADABLE_is_reachable_which_it_was_not_before(self):
        """The branch EP-29 §5 names as unreachable for the denied case. It is reached here
        by the world that actually justifies it: the stat SUCCEEDS and the read is refused."""
        path = self._present_unreadable()
        os.stat(path)                          # succeeds: the raw observation, not a verdict
        self.assertFalse(os.access(path, os.R_OK))
        ok, reason = _arrival_at(path)._probe()
        self.assertFalse(ok)
        self.assertIn("present but not readable by this observer (measured)", reason)

    def test_the_THREE_states_are_three_DISTINCT_sentences(self):
        """A three-state claim carried by one message repeated three times is a two-state
        probe with a longer string. The verdicts are compared to each other, not to a list."""
        said = {}
        for name, path in (("absent", self._absent()),
                           ("denied", self._denied()),
                           ("present", self._present_unreadable())):
            ok, reason = _arrival_at(path)._probe()
            self.assertFalse(ok, "%s reported the surface AVAILABLE" % name)
            said[name] = reason.replace(path, "<PATH>")   # the path itself is not the state
        self.assertEqual(len(set(said.values())), 3,
                         "two of the three states produce the SAME sentence, so the probe "
                         "does not distinguish them: %r" % said)

    def test_a_READABLE_world_is_the_fourth_outcome_so_False_is_not_structural(self):
        """Without this the rows above would be satisfied by a probe that returns False for
        everything, and every one of them would still pass."""
        p = os.path.join(self.tmp, "readable")
        os.mkdir(p)
        self.assertEqual(_arrival_at(p)._probe(), (True, "ok"))

    def test_the_OLD_ORACLE_is_SHOWN_returning_False_for_a_path_that_EXISTS(self):
        """THE DEFECT ITSELF, MEASURED RATHER THAN ARGUED — and it is why the repair could
        not be a better message on the same call."""
        denied = self._denied()
        self.assertFalse(os.path.exists(denied),
                         "os.path.exists no longer reports False for a traversal denial, so "
                         "the cause this repair was built on has moved")
        os.chmod(os.path.dirname(denied), 0o700)
        self.assertTrue(os.path.exists(denied),
                        "the path did not exist after all, so the world above was not a "
                        "DENIAL and this row establishes nothing")


class TheLiveGuestReportsTheAccessTruthUnprivileged(unittest.TestCase):
    """THE ROW WHOSE SUBJECT IS THE GUEST — EP-29 §5's sequencing: the repaired probe is
    driven under the CURRENT unprivileged observer and must print the access-result truth."""

    def test_the_guest_now_reports_PRESENT_BUT_NOT_READABLE_and_no_kernel_config_need(self):
        data = guest_probe(self)
        self.assertEqual(data["uname"], GUEST_KERNEL)
        reason = surfaces_by_key(data)[THE_IO_SURFACE]["reason"]
        self.assertIn("present but not readable by this observer (measured)", reason)
        self.assertNotIn("configuring the kernel for them", reason,
                         "the window still names a kernel-configuration need on a guest "
                         "whose tracefs is mounted and whose block is ACCESS: %s" % reason)

    def test_the_fixture_holds_the_OBSERVATION_and_the_verdict_is_COMPUTED(self):
        """The :582 rule, checked against the fixture rather than promised in a comment. The
        shipped fixture recorded `/sys/kernel/debug/tracing` as `exists: False` — the broken
        probe's belief, frozen — and no row could catch it, because every row read the same
        frozen value. The errno is what makes the two causes separable."""
        rec = _synthetic_probe()["paths"]["/sys/kernel/debug/tracing"]
        self.assertNotIn("exists", rec,
                         "the fixture stores a CONCLUSION again; `exists` is computed")
        self.assertEqual(rec["stat_errno"], errno.EACCES)
        self.assertIs(path_exists(rec), None,
                      "the fixture's own record now reads as determined absence, which is "
                      "exactly the conflation this rule was written to end")


class TheDeniedStateCannotBeReportedAsPresent(unittest.TestCase):
    """THE RED WORLD EP-29 §5 NAMES: the denied case printing "present" REDS.

    The forbidden lie class must not be reproduced by its own repair, inverted. The mutant
    below is NOT a strawman — it makes the repair's own first move, separating ENOENT from
    everything else, and then routes the REFUSAL into the present-but-unreadable branch. That
    is the most likely wrong repair, which is what a red world is for."""

    class _RefusalReadsAsPresent(_W.ArrivalWindow):
        def _probe(self):
            path = self.tracefs_path
            try:
                os.stat(path)
            except FileNotFoundError as exc:
                return False, (f"no {path} on this host — the kernel reports it not there "
                               f"(errno {exc.errno}, measured)")
            except OSError:
                pass                    # THE MIS-REPAIR: a refusal falls through as if stat'd
            if not os.access(path, os.R_OK):
                return False, (f"{path} is present but not readable by this observer "
                               "(measured)")
            return True, "ok"

    def _run_denied_row(self, planted):
        """Run the REAL denied row against a planted window class and return its result."""
        saved = _ARRIVAL_CLASS[0]
        _ARRIVAL_CLASS[0] = planted
        try:
            return unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
                TheArrivalProbeSpeaksThreeStates(
                    "test_DENIED_a_traversal_refusal_says_PRESENCE_UNDETERMINED"))
        finally:
            _ARRIVAL_CLASS[0] = saved

    def test_the_CONTROL_passes_with_the_SHIPPED_probe(self):
        """CONTROL FIRST. Without it the red below could be the harness being broken rather
        than the clause biting, and the two read identically on the page."""
        res = self._run_denied_row(_W.ArrivalWindow)
        self.assertTrue(res.wasSuccessful(),
                        "the shipped probe FAILS its own denied row, so the red world below "
                        "is uninterpretable: %r" % (res.failures + res.errors))

    def test_a_probe_that_reads_a_REFUSAL_as_PRESENT_REDS(self):
        res = self._run_denied_row(self._RefusalReadsAsPresent)
        self.assertEqual(res.errors, [],
                         "the row ERRORED rather than failed, so the mutant broke the "
                         "instrument instead of the claim: %r" % (res.errors,))
        self.assertEqual(len(res.failures), 1,
                         "a probe reporting an UNDETERMINED presence as PRESENT passes the "
                         "denied row, so the forbidden lie class can be reintroduced "
                         "inverted and nothing in this suite would say so")

    class _TheShippedProbeBeforeW1c(_W.ArrivalWindow):
        """THE ORIGINAL DEFECT, restored verbatim as a mutant so the OTHER axis is driven
        too. Reproduced from `src/observe/windows.py:929` as it stood at HEAD 5bca330."""

        tracefs_path = "/sys/kernel/debug/tracing"

        def _probe(self):
            path = self.tracefs_path
            if not os.path.exists(path):
                return False, (f"no {path} on this host — the tracepoint and eBPF routes for "
                               "interrupt/completion arrivals are unavailable to this "
                               "observer, and configuring the kernel for them is outside "
                               "this EP's fence")
            if not os.access(path, os.R_OK):
                return False, (f"{path} is present but not readable by this observer "
                               "(measured)")
            return True, "ok"

    def test_the_PRE_W1c_probe_REDS_the_denied_row_TOO(self):
        """THE SECOND AXIS. The row must catch the refusal reported as ABSENCE — the defect
        as it actually shipped — and not only the refusal reported as PRESENCE. A red world
        driven on one axis leaves the other one an argument."""
        res = self._run_denied_row(self._TheShippedProbeBeforeW1c)
        self.assertEqual(res.errors, [],
                         "the pre-W1c probe ERRORED rather than failed: %r" % (res.errors,))
        self.assertEqual(len(res.failures), 1,
                         "the probe this pass repairs PASSES the denied row, so the row does "
                         "not carry the repair and would not have caught the original")

    def test_the_mutant_is_a_MIS_REPAIR_and_not_a_broken_object(self):
        """A mutant that fails everything would redden the row for the wrong reason. This one
        is correct on the two states it does handle, and wrong only on the middle one."""
        tmp = tempfile.mkdtemp(prefix="ep29-w1c-mut-")
        try:
            gone = os.path.join(tmp, "nope")
            ok, reason = type("_M", (self._RefusalReadsAsPresent,),
                              {"tracefs_path": gone})()._probe()
            self.assertFalse(ok)
            self.assertIn("not there", reason)
            good = os.path.join(tmp, "readable")
            os.mkdir(good)
            self.assertEqual(type("_M", (self._RefusalReadsAsPresent,),
                                  {"tracefs_path": good})()._probe(), (True, "ok"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class _ShapeDoor:
    """A door that RAISES rather than records, so a refusal is observable without a store."""

    class Refused(Exception):
        pass

    def refuse(self, actor, op, rule, message):
        raise self.Refused("%s: %s" % (rule, message))


def window_declarations(pack, whole=False):
    """Every I/O window declaration in a pack. `whole=True` returns the records rather than
    their payloads, for the rows that read the envelope's own citation."""
    out = []
    for st in pack["steps"]:
        for r in st["records"]:
            if r.get("action") == "DECLARE-IO-WINDOW":
                out.append(r if whole else r["payload"])
    return out


import errno                                                        # noqa: E402


# =======================================================================================
# EP-29 W2a — CALIBRATE. ADDENDUM 7 §1 C0–C1, 2026-08-13.
#
# W2a MEASURES. It lands no law, moves no founding, builds no record: its whole product is
# a calibration table that W2b will derive the intake declaration's granularity FROM, cell
# by cell. That is why the six red worlds below are worth more than the figures — a wrong
# table poisons a law nobody will re-measure.
#
# THE INSTRUMENT LIVES HERE AND NOWHERE ELSE. `_CALIB_DRIVER` is the ONE home of the
# calibration observer's text: the suite ships it to the guest at the `retake` profile, and
# the pack's full table was produced by extracting THIS SAME STRING and running it at the
# `full` profile. The guest reports the sha256 of the bytes it received and a row below
# checks it against the bytes this file holds, so "the same instrument" is a checked claim
# and not a promise. Nothing of it is product: no line enters `src/`, and its outputs are
# quoted in the pack rather than committed.
#
# WHY A LIVE TABLE AT ALL, when the red worlds could be exhibited against planted ones: a
# reading that has only ever seen tables built to fail it is a reading with no subject. The
# retake drives the real guest at two real load levels so the same reading that reds the
# mutants is shown green against a table it did not construct.
# =======================================================================================

_CALIB_DRIVER = r'''#!/usr/bin/env python3
"""EP-29 W2a — THE CALIBRATION OBSERVER. GUEST-SIDE LAB INSTRUMENT, never product.

It measures ARRIVALS at the virtio validation set through the notification surfaces
W0g C2 established, at two or more load levels per device, and emits ONE JSON object.

Two independent routes per window, on purpose (a disagreement between them is a finding
about the instrument, not about the guest):
  R1  /proc/interrupts        per-IRQ counters, summed across CPUs, after minus before.
                              A kernel counter: no buffer, nothing to drop.
  R2  tracefs `trace` buffer  per-event lines in the window, attributed per device by IRQ
                              name / dev major:minor / interface name. Droppable, and the
                              drop is MEASURED (entries-written minus entries-in-buffer,
                              plus per-cpu overrun deltas) rather than assumed absent.

Every window records its subject at OPEN and at CLOSE (boot_id, machine-id, uptime,
readiness). A window whose subject moved is emitted with `subject_stable: false` and the
reader discards it whole — a spliced window is two populations wearing one label.

NOTHING ABOUT THE GUEST IS WEAKENED. No chmod, no remount, no mode widened: the observer
is invoked privileged (ADDENDUM 6 §4 — the privilege attaches to the OBSERVER, not to the
SURFACE) and tracefs stays 0700 root:root. The tracing pre-state is read first, restored
last, and the restore is VERIFIED field by field into the output.
"""
import json
import os
import re
import subprocess
import sys
import time

T = "/sys/kernel/tracing"
EVENTS = ("block:block_rq_issue", "block:block_rq_complete",
          "irq:irq_handler_entry", "net:net_dev_queue")

#: The UDP sender used as the net load. Sent to the DISCOVERED default gateway, which on
#: this lab is qemu's own user-mode stack inside the qemu process on this laptop: the
#: packets leave the guest through virtio0 and go no further.
UDP_CODE = ("import socket,sys;s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);"
            "d=b'x'*int(sys.argv[4]);a=(sys.argv[1],int(sys.argv[2]));"
            "[s.sendto(d,a) for _ in range(int(sys.argv[3]))];s.close()")

PROFILES = {
    # the pack's table
    "full":   {"repeats": 3, "control_s": 3.0, "block_iters": (1, 8), "block_count": 256,
               "net_packets": (200, 1600), "net_size": 512, "devices": "all"},
    # the suite's live re-take: same shape, same code, smaller
    "retake": {"repeats": 1, "control_s": 1.0, "block_iters": (1, 4), "block_count": 64,
               "net_packets": (0, 0), "net_size": 512, "devices": "block-primary"},
}


def rd(path, default=None):
    try:
        with open(path) as fh:
            return fh.read()
    except OSError as exc:
        return default if default is not None else "ERRNO:%d" % exc.errno


def wr(path, text):
    with open(path, "w") as fh:
        fh.write(text)


def run(argv, timeout=120):
    p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    return {"argv": argv, "command": " ".join(argv), "rc": p.returncode,
            "stderr_tail": (p.stderr or "")[-400:], "stdout_tail": (p.stdout or "")[-200:]}


# ---------------------------------------------------------------- subject and readiness
def meminfo_kb(key):
    for line in rd("/proc/meminfo", "").splitlines():
        if line.startswith(key + ":"):
            return int(line.split()[1])
    return None


def _readiness_pair():
    """ONE single-shot readiness reading: MemAvailable across a 0.2s pair, the figure
    AMENDMENT 13 named. On its own it occasionally catches a cold/paging outlier and
    mis-reads a warm guest as still-warming; it is the noise the median below is taken
    over. Returns the raw pair so the drift is reconstructable, never assumed."""
    a = meminfo_kb("MemAvailable")
    time.sleep(0.2)
    b = meminfo_kb("MemAvailable")
    return [a, b]


def warm_from_drifts(anchor, drifts, uptime_s):
    """THE WARM VERDICT, taken over the MEDIAN of the repeated drifts rather than a single
    one (board :2849 option C). The single-shot figure reds a warm guest whenever ONE pair
    catches a cold outlier; the median of three repeats drops one such outlier, while a
    guest whose MemAvailable is still climbing in the MAJORITY of repeats is still caught.
    Subject and meaning are AMENDMENT 13's unchanged — MemAvailable stable (<1% drift) and
    the box up past 600s — only the robustness to a single-run outlier changes. Fewer than
    three usable repeats is NOT warm: an incomplete reading never claims warmth. This same
    verdict is mirrored host-side in `_warm_verdict_from_samples`; the recorded drifts let
    the reader re-derive it and refuse a table whose emitted `warm` disagrees with its own
    repeats."""
    if not anchor or uptime_s is None or len(drifts) < 3:
        return False
    median_drift = sorted(drifts)[len(drifts) // 2]
    return bool(median_drift < max(1, anchor // 100) and uptime_s > 600.0)


def subject():
    """THE SUBJECT, taken the same way at OPEN and at CLOSE. `boot_id` is the sharp one: a
    guest that restarted mid-observation gets a new one and the window is discarded."""
    up = rd("/proc/uptime", "").split()
    uptime_s = float(up[0]) if up else None
    # THREE independent repeats of the single-shot readiness pair (median-of-3). Taken
    # back-to-back so all three read the SAME warm-up state; a single cold pair among them
    # is the outlier the median discards, and this is the whole of the de-flake.
    pairs = [_readiness_pair() for _ in range(3)]
    anchor = pairs[0][0]
    drifts = [abs(b - a) for a, b in pairs if a is not None and b is not None]
    return {"boot_id": rd("/proc/sys/kernel/random/boot_id", "").strip(),
            "machine_id": rd("/etc/machine-id", "").strip(),
            "hostname": rd("/proc/sys/kernel/hostname", "").strip(),
            "uptime_s": uptime_s,
            "monotonic": time.monotonic(),
            "mem_available_kb": list(pairs[0]),
            "mem_at_open_kb": anchor,
            "readiness_pairs_kb": pairs,
            "readiness_drift_kb": drifts,
            # AMENDMENT 13's physical non-vacuity, the signal named and its threshold stated
            # rather than implied, now taken over the MEDIAN of 3 repeated pairs so a single
            # cold outlier cannot flip it (board :2849 option C): the guest is WARM when the
            # median MemAvailable drift is <1% and the box has been up past 600s.
            "readiness_signal": "MemAvailable stable across the MEDIAN of 3 repeated 0.2s "
                                "pairs (<1% drift) AND uptime > 600s",
            "warm": warm_from_drifts(anchor, drifts, uptime_s)}


def stable(open_s, close_s):
    return (open_s["boot_id"] == close_s["boot_id"]
            and open_s["machine_id"] == close_s["machine_id"]
            and open_s["hostname"] == close_s["hostname"]
            and open_s["uptime_s"] is not None and close_s["uptime_s"] is not None
            and close_s["uptime_s"] >= open_s["uptime_s"])


# ---------------------------------------------------------------------- the device facts
IRQ_LINE = re.compile(r"^\s*(\d+):\s+(.*)$")


def interrupts():
    """Per-IRQ totals, summed across CPUs. Returns {irq_num: (total, name)}."""
    out = {}
    for line in rd("/proc/interrupts", "").splitlines():
        m = IRQ_LINE.match(line)
        if not m:
            continue
        nums, rest = m.group(1), m.group(2).split()
        counts, i = [], 0
        while i < len(rest) and rest[i].isdigit():
            counts.append(int(rest[i]))
            i += 1
        name = rest[-1] if rest else ""
        out[nums] = {"total": sum(counts), "name": name}
    return out


def validation_set():
    """The virtio devices, each with the identifiers its arrivals will be attributed by."""
    base = "/sys/bus/virtio/devices"
    devs = {}
    for name in sorted(os.listdir(base)):
        d = os.path.join(base, name)
        rec = {"device": rd(os.path.join(d, "device"), "").strip(),
               "vendor": rd(os.path.join(d, "vendor"), "").strip(),
               "status": rd(os.path.join(d, "status"), "").strip(),
               "driver": os.path.basename(os.path.realpath(os.path.join(d, "driver")))
                         if os.path.exists(os.path.join(d, "driver")) else None,
               "block": None, "netif": None, "devno": None, "class": None}
        bdir, ndir = os.path.join(d, "block"), os.path.join(d, "net")
        if os.path.isdir(bdir):
            names = sorted(os.listdir(bdir))
            if names:
                rec["block"] = names[0]
                rec["devno"] = rd("/sys/block/%s/dev" % names[0], "").strip()
                rec["class"] = "block"
        if os.path.isdir(ndir):
            names = sorted(os.listdir(ndir))
            if names:
                rec["netif"] = names[0]
                rec["class"] = "net"
        rec["irqs"] = sorted(k for k, v in interrupts().items()
                             if v["name"].startswith(name + "-"))
        devs[name] = rec
    return devs


def default_gateway():
    p = subprocess.run(["ip", "-4", "route", "show", "default"],
                       capture_output=True, text=True)
    m = re.search(r"default via (\S+)", p.stdout or "")
    return m.group(1) if m else None


# ------------------------------------------------------------------------- tracing state
TRACE_FIELDS = ("tracing_on", "current_tracer", "set_event", "events/enable",
                "buffer_size_kb")


def trace_state():
    st = {f: rd(os.path.join(T, f), "").strip() for f in TRACE_FIELDS}
    st["set_event_bytes"] = len(rd(os.path.join(T, "set_event"), ""))
    try:
        st["instances"] = sorted(os.listdir(os.path.join(T, "instances")))
    except OSError:
        st["instances"] = None
    return st


def restore_tracing(pre):
    """PUT BACK WHAT THIS RUN TOUCHED, and put it back FROM A `finally` SO A CRASH CANNOT
    SKIP IT.

    Written after the defect it exists to prevent, which this instrument committed: an
    early version raised inside the window loop AFTER writing `tracing_on 0` and never
    restored it. Every later run then read that 0 as its own pre-state, so `post == pre`
    kept answering True — A RESTORE CHECK WHOSE BASELINE IS ITS OWN DAMAGE. The guest sat
    with tracing disabled for an hour and no reading said so."""
    try:
        wr(os.path.join(T, "set_event"), "\n")
        wr(os.path.join(T, "current_tracer"), pre.get("current_tracer") or "nop")
        wr(os.path.join(T, "tracing_on"), (pre.get("tracing_on") or "1") + "\n")
    except OSError:
        pass


def overrun_total():
    tot, base = 0, os.path.join(T, "per_cpu")
    try:
        cpus = sorted(os.listdir(base))
    except OSError:
        return None
    for c in cpus:
        for line in rd(os.path.join(base, c, "stats"), "").splitlines():
            if line.startswith("overrun:"):
                tot += int(line.split()[1])
    return tot


TS_EVENT = re.compile(r"\d+\.\d+:\s+(\w+):\s*(.*)$")
IRQ_NAME = re.compile(r"irq=(\d+)\s+name=(\S+)")
NET_DEV = re.compile(r"dev=(\S+)")


def read_trace(devs):
    """Parse the buffer. Returns per-event totals, per-device attribution and the DROP
    figures the kernel itself reports, so a count that lost lines cannot read as a total."""
    txt = rd(os.path.join(T, "trace"), "")
    written = in_buffer = None
    by_event, per_dev, unattributed, lines = {}, {}, 0, 0
    # THE UNATTRIBUTED LINES ARE SAMPLED, NOT JUST COUNTED. A bare count of "lines this
    # instrument could not place" invites a guess about what they were; five raw lines
    # make the limit evidenced instead.
    unattributed_sample = []
    devno_to_dev = {d["devno"].replace(":", ","): n
                    for n, d in devs.items() if d.get("devno")}
    netif_to_dev = {d["netif"]: n for n, d in devs.items() if d.get("netif")}
    for line in txt.splitlines():
        if line.startswith("#"):
            m = re.search(r"entries-in-buffer/entries-written:\s*(\d+)/(\d+)", line)
            if m:
                in_buffer, written = int(m.group(1)), int(m.group(2))
            continue
        m = TS_EVENT.search(line)
        if not m:
            continue
        lines += 1
        ev, rest = m.group(1), m.group(2)
        by_event[ev] = by_event.get(ev, 0) + 1
        dev = None
        if ev == "irq_handler_entry":
            mm = IRQ_NAME.search(rest)
            if mm and "-" in mm.group(2):
                cand = mm.group(2).split("-")[0]
                dev = cand if cand in devs else None
        elif ev.startswith("block_rq_"):
            dev = devno_to_dev.get(rest.split()[0]) if rest.split() else None
        elif ev == "net_dev_queue":
            mm = NET_DEV.search(rest)
            dev = netif_to_dev.get(mm.group(1)) if mm else None
        if dev is None:
            unattributed += 1
            if len(unattributed_sample) < 5:
                unattributed_sample.append(line.strip()[-160:])
        else:
            per_dev.setdefault(dev, {})
            per_dev[dev][ev] = per_dev[dev].get(ev, 0) + 1
    return {"by_event": by_event, "per_device": per_dev, "unattributed": unattributed,
            "unattributed_sample": unattributed_sample,
            "parsed_lines": lines, "entries_in_buffer": in_buffer,
            "entries_written": written,
            "dropped": (None if (written is None or in_buffer is None)
                        else written - in_buffer)}


# ------------------------------------------------------------------------------ a window
def window(devs, device, level, kind, loads, note):
    """ONE CELL. Subject at open, arrivals by both routes, subject at close."""
    wr(os.path.join(T, "tracing_on"), "0")
    wr(os.path.join(T, "trace"), "")
    # ONE EVENT PER WRITE, and NOT through O_APPEND. `set_event` processes a single event
    # name per write() call, so a joined multi-line string would enable the first name and
    # silently drop the rest — an instrument measuring three events while believing it
    # measures four. tracefs rejects O_APPEND outright (EINVAL, driven), so each name goes
    # through its own O_WRONLY open: no truncation, which is what `>>` buys in the kernel's
    # own documentation of this file, and no append flag, which this filesystem refuses.
    wr(os.path.join(T, "set_event"), "\n")           # clear first: O_TRUNC is accepted here
    for ev in EVENTS:
        fd = os.open(os.path.join(T, "set_event"), os.O_WRONLY)
        try:
            os.write(fd, (ev + "\n").encode())
        finally:
            os.close(fd)
    enabled_now = sorted(x for x in rd(os.path.join(T, "set_event"), "").split() if x)
    ov0 = overrun_total()
    s_open = subject()
    irq0 = interrupts()
    t0 = time.monotonic()
    wr(os.path.join(T, "tracing_on"), "1")
    results = [run(argv) for argv in loads]
    if kind == "CONTROL":
        time.sleep(note["idle_s"])
    wr(os.path.join(T, "tracing_on"), "0")
    t1 = time.monotonic()
    irq1 = interrupts()
    tr = read_trace(devs)
    s_close = subject()
    ov1 = overrun_total()
    wr(os.path.join(T, "set_event"), "\n")

    irqs = devs[device]["irqs"]
    per_irq = {i: irq1.get(i, {"total": 0})["total"] - irq0.get(i, {"total": 0})["total"]
               for i in irqs}
    named = {i: irq0.get(i, {}).get("name") for i in irqs}
    elapsed = t1 - t0
    arrivals = sum(tr["per_device"].get(device, {}).values())
    interrupt_count = sum(per_irq.values())
    return {
        "device": device, "device_class": devs[device]["class"], "level": level,
        "level_kind": kind,
        "command": " ; ".join(r["command"] for r in results) or note.get("command", ""),
        "load_results": results,
        "load_size": requested_and_delivered(results),
        "taking": note["taking"],
        "open": s_open, "close": s_close,
        "subject_stable": stable(s_open, s_close),
        # FULL PRECISION, DELIBERATELY. The rates below are computed from THIS value, so a
        # reader can reconstruct them from the table's own cells. Storing a rounded elapsed
        # beside a rate computed from the unrounded one gives a figure that does not follow
        # from its own stated inputs — small, and unreconstructable is unreconstructable.
        "elapsed_s": elapsed,
        "interrupts": {"per_irq_delta": per_irq, "irq_names": named,
                       "count": interrupt_count,
                       "basis": "/proc/interrupts per-IRQ totals summed across CPUs, "
                                "after minus before, for the IRQs whose name begins "
                                "'%s-'" % device},
        "arrivals": {"count": arrivals,
                     "by_event": tr["per_device"].get(device, {}),
                     "basis": "tracefs `trace` lines in the window attributed to this "
                              "device by IRQ name / dev major:minor / interface name, "
                              "events enabled: " + ", ".join(EVENTS)},
        "events_enabled_at_open": enabled_now,
        "trace_totals": tr,
        "overrun_delta": (None if (ov0 is None or ov1 is None) else ov1 - ov0),
        "rate_interrupts_per_s": round(interrupt_count / elapsed, 3) if elapsed else None,
        "rate_arrivals_per_s": round(arrivals / elapsed, 3) if elapsed else None,
    }


#: WHAT THE PLAN SAYS THE GROUND IS. C0 is walked by COMPARING against these rather than
#: by reading them: a divergence is DETECTED mechanically and REPORTED, never accommodated
#: and never resolved here. `resolution` is a constant on purpose — ADDENDUM 5 §4's third
#: state is the only state this instrument can put a divergence in, because a builder (and
#: a fortiori its instrument) authoring a ruling is C0's own red world.
PLAN_GROUND = {
    "kernel": "6.8.0-134-generic",
    "validation_set": ["virtio0", "virtio1", "virtio2"],
    "device_classes": ["block", "net"],
    "tracefs_mode": "0o700",
    "tracefs_uid": 0,
    "surface_readable_unprivileged": False,
    "surface_readable_privileged": True,
}


def establishment(devs, unpriv_readable, priv_readable, modes, uname):
    found = {
        "kernel": uname,
        "validation_set": sorted(devs),
        "device_classes": sorted({d["class"] for d in devs.values() if d["class"]}),
        "tracefs_mode": modes["/sys/kernel/tracing"]["mode"],
        "tracefs_uid": modes["/sys/kernel/tracing"]["uid"],
        "surface_readable_unprivileged": unpriv_readable,
        "surface_readable_privileged": priv_readable,
    }
    divergences = [{"fact": k, "expected": PLAN_GROUND[k], "found": found[k],
                    "resolution": "STOP-AND-REPORT"}
                   for k in PLAN_GROUND if found[k] != PLAN_GROUND[k]]
    return {"plan_ground": PLAN_GROUND, "found": found, "divergences": divergences,
            "ground_true": not divergences}


def limits(out):
    """EVERY LIMIT NAMES ITS POPULATION AND ITS BASIS (charter §A51, the 2026-08-13
    bracket). These are MEASURED here rather than written in prose afterwards, so the
    population is the run's own and cannot be guessed at later."""
    ws = out["windows"]
    loaded = [w for w in ws if w["level_kind"] == "LOAD"]
    pop = ("the %d windows of this run (%d of them loaded) on %s, machine-id %s, "
           "boot_id %s, kernel %s"
           % (len(ws), len(loaded), out.get("hostname"), out.get("machine_id"),
              out.get("boot_id"), out["uname"]))
    drops = [w["trace_totals"]["dropped"] for w in ws
             if w["trace_totals"]["dropped"] is not None]
    overs = [w["overrun_delta"] for w in ws if w["overrun_delta"] is not None]
    unatt = sum(w["trace_totals"]["unattributed"] for w in ws)
    parsed = sum(w["trace_totals"]["parsed_lines"] for w in ws)
    best = max(loaded, key=lambda w: w["rate_arrivals_per_s"] or 0) if loaded else None

    cells = {}
    for w in loaded:
        cells.setdefault((w["device"], w["level"]), []).append(w)
    spread = []
    for (dev, lvl), ws in sorted(cells.items()):
        cs = [w["arrivals"]["count"] for w in ws]
        rs = [w["rate_arrivals_per_s"] or 0.0 for w in ws]
        spread.append({"device": dev, "level": lvl, "repeats": len(ws),
                       "count_min": min(cs), "count_max": max(cs),
                       "count_ratio": round(max(cs) / min(cs), 4) if min(cs) else None,
                       "rate_min": min(rs), "rate_max": max(rs),
                       "rate_ratio": round(max(rs) / min(rs), 4) if min(rs) else None})
    out_l = [
        {"limit": "arrival counts in this run are TOTALS and not floors only while no line "
                  "was lost; the largest single-window loss observed",
         "value": max(drops) if drops else None,
         "population": pop,
         "basis": "tracefs `trace` header `entries-in-buffer/entries-written` per window, "
                  "written minus in-buffer; plus per-cpu `overrun` deltas (largest "
                  "observed: %s)" % (max(overs) if overs else None)},
        {"limit": "arrival lines not attributable to any device in the validation set",
         "value": unatt,
         "population": pop + "; %d parsed trace lines in total" % parsed,
         "basis": "a line is attributed by IRQ name prefix (irq_handler_entry), by dev "
                  "major:minor against /sys/block/<name>/dev (block_rq_*), or by interface "
                  "name (net_dev_queue); anything else is counted unattributed"},
        {"limit": "the highest per-device arrival RATE this run reached",
         "value": (None if best is None else
                   {"device": best["device"], "level": best["level"],
                    "rate_arrivals_per_s": best["rate_arrivals_per_s"]}),
         "population": "the loaded windows of this run only, at the load levels this run "
                       "drove — NOT a ceiling of the device, the surface or the guest, "
                       "neither of which was driven to saturation here",
         "basis": "attributed trace lines divided by that window's own elapsed monotonic "
                  "seconds, measured inside the observer"},
        {"limit": "net arrivals here are TRANSMIT-path only",
         "value": "net_dev_queue",
         "population": "the net cells of this run",
         "basis": "the enabled event set is four literal names (%s); no receive-side "
                  "event was enabled, so a net figure is queued frames and not total "
                  "frames" % ", ".join(EVENTS)},
        {"limit": "the load a cell's COMMAND asks for is not always the load the device "
                  "gave: cells whose delivered count fell short of the requested count",
         "value": [{"device": w["device"], "level": w["level"],
                    "requested": w["load_size"]["requested_units"],
                    "delivered": w["load_size"]["delivered_units"]}
                   for w in loaded if w["load_size"]["truncated"]],
         "population": pop + "; the loaded cells whose tool reports delivery (dd)",
         "basis": "`count=` summed across the cell's dd invocations against dd's own "
                  "`records out`, read from the cell's captured stderr. A cell whose tool "
                  "reports no delivery figure is marked delivered_known false and is NOT "
                  "counted here as agreeing"},
        {"limit": "the COUNT column is reproducible across repeats and the RATE column is "
                  "NOT: the widest spread between repeats of one cell",
         "value": spread,
         "population": "the %d loaded cells of this run, %d repeats each; identical "
                       "commands, identical devices, one boot"
                       % (len({(w["device"], w["level"]) for w in loaded}),
                          out["instrument"]["params"]["repeats"]),
         "basis": "per (device, level): max/min of the repeats' arrival COUNTS against "
                  "max/min of their arrival RATES. The rate's denominator is the window's "
                  "own elapsed time, which is dominated by scheduling and first-touch at "
                  "these window sizes, so a value derived from the rate column inherits "
                  "that spread and a value derived from the count column does not"},
        {"limit": "every figure in this table is one guest, one boot",
         "value": out.get("boot_id"),
         "population": pop,
         "basis": "boot_id read at every window OPEN and CLOSE; a window whose boot_id "
                  "moved is emitted with subject_stable false and is discarded whole"},
    ]
    return out_l


RECORDS_OUT = re.compile(r"(\d+)\+(\d+) records out")


def requested_and_delivered(results):
    """WHAT THE COMMAND ASKED FOR AGAINST WHAT THE DEVICE GAVE, as a DECLARED FIELD.

    Driven, not anticipated: `dd ... count=256` against a 366 KiB device returns after 92
    blocks, so the command's own number is NOT the population of the figure beside it. A
    reader of the table who took `count=256` as the load would be reading a request as a
    measurement — §A51's class exactly, with the digits present and the population wrong."""
    req = deliv = 0
    known = True
    for r in results:
        argv = r["argv"]
        if argv and argv[0] == "dd":
            for a in argv:
                if a.startswith("count="):
                    req += int(a.split("=", 1)[1])
            m = RECORDS_OUT.search(r["stderr_tail"])
            if m:
                deliv += int(m.group(1)) + (1 if int(m.group(2)) else 0)
            else:
                known = False
        elif argv and argv[0] == "python3":
            # the UDP sender: the request is its argument, and what the device DELIVERED is
            # not reported by the tool — the surface's own net_dev_queue count is that
            # figure, and it is beside this one rather than inside it.
            req += int(argv[-2])
            known = False
    return {"requested_units": req or None,
            "delivered_units": deliv if known and req else None,
            "delivered_known": bool(known and req),
            "truncated": bool(known and req and deliv < req),
            "unit": "4096-byte direct reads (dd) or datagrams (udp sender)"}


def main():
    profile = sys.argv[1] if len(sys.argv) > 1 else "full"
    P = PROFILES[profile]
    if os.getuid() != 0:
        print("CALIB-JSON:" + json.dumps({"error": "not privileged", "uid": os.getuid()}))
        return 1
    src = open(os.path.abspath(__file__), "rb").read()
    import hashlib
    out = {"instrument": {"name": "ep29-w2a-calibration-observer", "profile": profile,
                          "params": P, "source_sha256": hashlib.sha256(src).hexdigest(),
                          "events_enabled": list(EVENTS)},
           "uname": os.uname().release, "uid": os.getuid(),
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    s0 = subject()
    out["hostname"] = s0["hostname"]
    out["machine_id"] = s0["machine_id"]
    out["boot_id"] = s0["boot_id"]
    out["run_open_subject"] = s0

    devs = validation_set()
    out["validation_set"] = devs
    gw = default_gateway()
    out["gateway"] = gw
    out["trace_pre_state"] = trace_state()
    out["surface_modes"] = {p: {"mode": oct(os.stat(p).st_mode & 0o7777),
                                "uid": os.stat(p).st_uid}
                            for p in ("/sys/kernel/tracing", "/sys/kernel/debug")}
    # the access PAIR, driven here rather than carried: this observer is root, so the
    # unprivileged half is taken by dropping to the invoking user with `sudo -u`.
    caller = os.environ.get("SUDO_USER") or "ubuntu"
    unpriv = subprocess.run(
        ["sudo", "-n", "-u", caller, "python3", "-c",
         "import os;print(os.access('/sys/kernel/tracing', os.R_OK))"],
        capture_output=True, text=True)
    out["unprivileged_probe"] = {"user": caller, "rc": unpriv.returncode,
                                 "stdout": (unpriv.stdout or "").strip(),
                                 "command": "sudo -n -u %s python3 -c \"import os;"
                                            "print(os.access('/sys/kernel/tracing', "
                                            "os.R_OK))\"" % caller}
    out["establishment"] = establishment(
        devs, out["unprivileged_probe"]["stdout"] == "True",
        os.access("/sys/kernel/tracing", os.R_OK), out["surface_modes"],
        out["uname"])

    order = sorted(devs)
    if P["devices"] == "block-primary":
        order = [n for n in order if devs[n]["block"] == "vda"] or order[:1]

    windows = []
    try:
     for dev in order:
         rec = devs[dev]
         cells = []
         if rec["class"] == "block" and rec["block"]:
             node = "/dev/" + rec["block"]
             for idx, iters in enumerate(P["block_iters"], start=1):
                 argvs = [["dd", "if=" + node, "of=/dev/null", "bs=4096",
                           "count=%d" % P["block_count"], "iflag=direct"]] * iters
                 cells.append(("L%d" % idx, "LOAD", argvs,
                               {"taking": "direct reads of %s, %d x %d x 4096 bytes, "
                                          "page cache bypassed with iflag=direct so every "
                                          "read reaches the device"
                                          % (node, iters, P["block_count"])}))
         elif rec["class"] == "net" and rec["netif"] and gw:
             for idx, n in enumerate(P["net_packets"], start=1):
                 if not n:
                     continue
                 argvs = [["python3", "-c", UDP_CODE, gw, "9", str(n),
                           str(P["net_size"])]]
                 cells.append(("L%d" % idx, "LOAD", argvs,
                               {"taking": "%d UDP datagrams of %d bytes to the discovered "
                                          "default gateway %s, transmitted through %s"
                                          % (n, P["net_size"], gw, rec["netif"])}))
         # the CONTROL is not a load level: it is the ambient reading the loaded cells are
         # read against, and without it a loaded figure has nothing to be larger than.
         cells.insert(0, ("L0", "CONTROL", [],
                          {"idle_s": P["control_s"],
                           "command": "sleep %s   # no load driven at this device"
                                      % P["control_s"],
                           "taking": "no load driven: %ss of ambient arrivals, the reading "
                                     "the loaded cells are compared against"
                                     % P["control_s"]}))
         for level, kind, argvs, note in cells:
             for rep in range(1, P["repeats"] + 1):
                 w = window(devs, dev, level, kind, argvs, note)
                 w["repeat"] = rep
                 windows.append(w)
    finally:
        # THE RESTORE RUNS EVEN IF A WINDOW RAISED. See restore_tracing above: the version
        # of this instrument without this clause left the guest's tracing disabled and
        # every later run mistook that residue for the world.
        restore_tracing(out["trace_pre_state"])
    out["windows"] = windows
    out["limits"] = limits(out)
    out["run_close_subject"] = subject()
    out["run_subject_stable"] = stable(out["run_open_subject"], out["run_close_subject"])
    out["trace_post_state"] = trace_state()
    out["restore_verified"] = out["trace_post_state"] == out["trace_pre_state"]
    print("CALIB-JSON:" + json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

#: The four codes the reading emits. A CLOSED set on purpose: a row asserting a mutant reds
#: names the code it expects, so a mutant that reds for the WRONG reason fails the row that
#: planted it rather than passing it.
CALIB_DEFECT_CODES = ("NO-COMMAND", "NO-TAKING", "SINGLE-LOAD", "SPLICED-WINDOW",
                      "LIMIT-NO-POPULATION", "LIMIT-NO-BASIS", "RULING-AUTHORED",
                      "NO-DIVERGENCE-LIST")

_CALIB_MEMO = {}


def calibration(case, profile="retake"):
    """Ship the calibration observer to the guest and run it PRIVILEGED (ADDENDUM 6 §4 —
    the privilege attaches to the OBSERVER, never to the surface; `sudo -n` already exists
    on this guest and nothing is granted, chmod'd or remounted here).

    Memoized per (profile, driver digest) for `guest_probe`'s own reason: the table is a
    property of the box under a stated load, and re-driving it per row would put minutes of
    guest work behind every assertion. The digest is in the key, so an edited instrument
    gets a fresh directory and a stale table can never be read as a current one."""
    digest = hashlib.sha256(_CALIB_DRIVER.encode("utf-8")).hexdigest()
    key = (profile, digest)
    if key in _CALIB_MEMO:
        memo = _CALIB_MEMO[key]
        if isinstance(memo, str):
            case.skipTest(memo)
        return memo
    gdir = "/tmp/govos-w2a-calib-%s" % digest[:12]
    cmd = ("mkdir -p %s && cat > %s/calib.py && sudo -n python3 %s/calib.py %s"
           % (gdir, gdir, gdir, profile))

    def _skip(why):
        _CALIB_MEMO[key] = why
        case.skipTest(why)

    ok, why = _carrier_up()
    if not ok:
        _skip("SKIP LONG-BOOT: %s — the calibration cannot reach its subject" % why)
    try:
        r = subprocess.run(SSH + [cmd], input=_CALIB_DRIVER, capture_output=True,
                           text=True, timeout=900)
    except (OSError, subprocess.SubprocessError) as exc:              # noqa: BLE001
        _skip("SKIP LONG-BOOT: GUEST: the ssh client could not complete (%s)" % exc)
    if r.returncode == 255:
        # ssh's OWN failure code. THE LAYER SPLIT IS THE POINT: 255 is the carrier, the
        # auth or the daemon, and a row that cannot reach its subject declines to state a
        # fact about it. ANY OTHER non-zero code is the INSTRUMENT failing on the guest,
        # and that is a FAILURE and never a skip — a broken observer that skipped would
        # leave every row below green with no subject, which is the check that cannot fail.
        err = (r.stderr or "").strip()
        layer = "AUTH" if "denied" in err.lower() else "CARRIER/GUEST"
        _skip("SKIP LONG-BOOT: %s: ssh itself refused (%s)" % (layer, err[:160]))
    if r.returncode != 0:
        case.fail("THE CALIBRATION OBSERVER FAILED ON THE GUEST (rc=%d). This is the "
                  "instrument, not the lab: stderr=%r stdout=%r"
                  % (r.returncode, (r.stderr or "")[-600:], (r.stdout or "")[-400:]))
    out = r.stdout
    line = [ln for ln in out.splitlines() if ln.startswith("CALIB-JSON:")]
    if not line:
        case.fail("the calibration observer produced no CALIB-JSON line: %r" % out[-500:])
    data = json.loads(line[0][len("CALIB-JSON:"):])
    data["_local_digest"] = digest
    _CALIB_MEMO[key] = data
    return data


def calibration_defects(table):
    """THE READING. Given a calibration table, return the sorted set of ADDENDUM 7 C0–C1
    red worlds it exhibits. An empty list is the only passing answer.

    Every clause here is a red world from the plan's own text, and each is checkable
    against a DECLARED FIELD rather than by hunting prose — charter §A51's refusal form
    (2026-08-13): a limit names its population as a field, so its absence is visible
    without reading sentences. Prose-hunting filters are the class that failed twice on
    the day that ruling was written."""
    d = []

    est = table.get("establishment")
    if not isinstance(est, dict) or "divergences" not in est:
        # C0's SILENT ACCOMMODATION. A table with no divergence list has not walked the
        # ground: it has agreed with the plan by not looking, which is the state ADDENDUM 5
        # §4 wrote its third state to prevent.
        d.append("NO-DIVERGENCE-LIST")
    else:
        for dv in est["divergences"]:
            if dv.get("resolution") != "STOP-AND-REPORT":
                # C0's BUILDER-AUTHORED RULING. A divergence may be REPORTED. Resolving it
                # is the architect's act, and an instrument that carries a resolution has
                # made the ruling on the builder's behalf.
                d.append("RULING-AUTHORED")

    levels = {}
    for w in table.get("windows", []):
        if not (w.get("command") or "").strip():
            d.append("NO-COMMAND")                       # a figure with no command REDS
        if not (w.get("taking") or "").strip():
            d.append("NO-TAKING")
        if not w.get("subject_stable"):
            # A SPLICED WINDOW is two populations wearing one label. The window is not
            # repaired and not partially credited: the table carrying it is defective.
            d.append("SPLICED-WINDOW")
        if w.get("level_kind") == "LOAD":
            levels.setdefault(w.get("device"), set()).add(w.get("level"))

    if not levels:
        d.append("SINGLE-LOAD")
    for dev in levels:
        if len(levels[dev]) < 2:
            # TWO IS THE FLOOR, NEVER THE COUNT (ADDENDUM 7, repaired at :663). The
            # derivation W2b runs needs spread, and one point has none.
            d.append("SINGLE-LOAD")

    lims = table.get("limits")
    if not lims:
        d.append("LIMIT-NO-POPULATION")
    for lim in lims or []:
        if not (lim.get("population") or "").strip():
            d.append("LIMIT-NO-POPULATION")
        if not (lim.get("basis") or "").strip():
            d.append("LIMIT-NO-BASIS")
    return sorted(set(d))


def _mutant(table, fn):
    """A DEEP COPY, mutated. The live table is never touched: a red-world row that damaged
    the subject the green rows read would make the suite order-dependent, and an
    order-dependent battery reports the order and not the world."""
    t = copy.deepcopy(table)
    fn(t)
    return t


def _plant_no_command(t):
    _loaded(t)[0]["command"] = ""


def _plant_no_taking(t):
    _loaded(t)[0]["taking"] = "   "


def _plant_single_load(t):
    """Two is the FLOOR, never the count: a table that drove one level has no spread and
    the derivation W2b runs cannot be made from it."""
    keep = _loaded(t)[0]["level"]
    t["windows"] = [w for w in t["windows"]
                    if w["level_kind"] != "LOAD" or w["level"] == keep]


def _plant_spliced_window(t):
    """The subject dropped mid-observation. The figures still look like figures, which is
    exactly why this is checked at the identity and not at the numbers."""
    w = _loaded(t)[0]
    w["close"]["boot_id"] = "00000000-0000-0000-0000-000000000000"
    w["subject_stable"] = False


def _plant_limit_no_population(t):
    t["limits"][0]["population"] = ""


def _plant_limit_no_basis(t):
    t["limits"][0]["basis"] = ""


def _plant_ruling_authored(t):
    """C0's second red world. The divergence is real and the resolution is invented — the
    shape that looks most like diligence, and the one the third state exists to refuse."""
    t["establishment"]["divergences"] = [
        {"fact": "validation_set", "expected": ["virtio0", "virtio1", "virtio2"],
         "found": ["virtio0", "virtio1"],
         "resolution": "accommodated: two devices are enough for the table"}]


def _plant_no_divergence_list(t):
    """C0's first. Agreement reached by not looking is indistinguishable from agreement
    reached by looking, unless the looking leaves a field behind."""
    t["establishment"].pop("divergences")


#: ONE HOME PER MUTATION. Each red-world row plants through this table and the positive
#: control walks it, so a mutation cannot drift between the row that names it and the
#: control that proves the reading can emit its code.
CALIB_DEFECT_PLANTERS = {
    "NO-COMMAND": _plant_no_command,
    "NO-TAKING": _plant_no_taking,
    "SINGLE-LOAD": _plant_single_load,
    "SPLICED-WINDOW": _plant_spliced_window,
    "LIMIT-NO-POPULATION": _plant_limit_no_population,
    "LIMIT-NO-BASIS": _plant_limit_no_basis,
    "RULING-AUTHORED": _plant_ruling_authored,
    "NO-DIVERGENCE-LIST": _plant_no_divergence_list,
}


def _loaded(table, device=None):
    return [w for w in table["windows"] if w["level_kind"] == "LOAD"
            and (device is None or w["device"] == device)]


def _controls(table, device=None):
    return [w for w in table["windows"] if w["level_kind"] == "CONTROL"
            and (device is None or w["device"] == device)]


def _warm_verdict_from_samples(anchor, drifts, uptime_s):
    """THE WARM VERDICT, HOST-SIDE, re-derived from the repeats the guest recorded. It is a
    byte-for-byte mirror of `warm_from_drifts` inside `_CALIB_DRIVER` (median of 3 drifts,
    <1% of the open anchor, box up past 600s). The mirror is deliberate: the observer runs
    at the guest and cannot be imported here, so the row that checks the emitted `warm`
    against its OWN recorded samples re-computes the median itself. What it catches is a
    table whose `warm` disagrees with the repeats it shipped — an all-cold triple wearing a
    warm flag, or a triple collapsed back to a single shot. What it CANNOT catch is the two
    copies being edited wrong together; that is the disclosed cost of a guest/host split,
    and the recorded drifts are the ground truth that makes the honest case checkable."""
    if not anchor or uptime_s is None or len(drifts) < 3:
        return False
    median_drift = sorted(drifts)[len(drifts) // 2]
    return bool(median_drift < max(1, anchor // 100) and uptime_s > 600.0)


# ---------------------------------------------------------------------------------------
class TheCalibrationRanAtTheGuestAndOnTheBytesWeSent(unittest.TestCase):
    """NON-VACUITY FOR EVERY W2a ROW. The same discipline `TheProbeReachedTheGuestAndNot
    ThisHost` applies to the surface probes: an observer that ran on this laptop would
    answer, and every answer would be about the wrong kernel."""

    def test_the_observer_ran_in_the_GUEST_at_the_pinned_kernel(self):
        t = calibration(self)
        self.assertEqual(t["uname"], GUEST_KERNEL,
                         "the calibration ran somewhere that is not the pinned lab guest")
        self.assertEqual(t["uid"], 0,
                         "the observer did not run privileged, so the arrival surface was "
                         "not readable and the table cannot be about tracepoints")

    def test_the_guest_ran_THE_BYTES_THIS_FILE_HOLDS(self):
        """One home, checked. The pack's full table was produced by extracting this same
        string; if the two ever diverge, this row is where it shows."""
        t = calibration(self)
        self.assertEqual(t["instrument"]["source_sha256"], t["_local_digest"],
                         "the guest hashed different bytes than this file shipped, so the "
                         "table was produced by an instrument nobody in this repo has read")


# ---------------------------------------------------------------------------------------
class TheCalibrationGroundIsTrueAtTheWalk(unittest.TestCase):
    """C0, THE THREE-STATE FORM (ADDENDUM 5 §4). The ground is COMPARED, never read: the
    instrument holds what the plan says the world is and reports every difference. Where a
    difference needs a ruling the state is STOP-AND-REPORT and it is GREEN — this row's
    failure message is that stop, addressed to the seat that can make the ruling."""

    def test_every_ground_fact_the_plan_asserts_is_TRUE_at_the_guest(self):
        t = calibration(self)
        est = t["establishment"]
        self.assertEqual(
            est["divergences"], [],
            "THE GROUND DIVERGES FROM THE PLAN. This is not a defect to accommodate and "
            "not one for a builder to rule on: report it with these citations and stop. "
            "%r" % (est["divergences"],))
        self.assertTrue(est["ground_true"])

    def test_the_ground_walk_covers_the_facts_the_TABLE_depends_on(self):
        """A walk that checked nothing load-bearing would pass by construction. Named
        rather than counted, so a shrunken walk is visible."""
        t = calibration(self)
        for fact in ("kernel", "validation_set", "device_classes", "tracefs_mode",
                     "surface_readable_unprivileged", "surface_readable_privileged"):
            self.assertIn(fact, t["establishment"]["plan_ground"])
            self.assertIn(fact, t["establishment"]["found"])

    def test_the_validation_set_AGREES_with_the_shipped_surface_probe(self):
        """TWO INSTRUMENTS, ONE SUBJECT. The calibration observer reads the virtio bus
        itself; `guest_probe` runs the estate's own `scan_devices()`. A disagreement here
        is a finding about an instrument, and it is cheaper to find it now than inside a
        law derived from the table."""
        t = calibration(self)
        probe = guest_probe(self)
        by_scan = sorted(k.split("/", 1)[1] for k in probe["virtio"])
        self.assertEqual(sorted(t["validation_set"]), by_scan,
                         "the calibration observer and the estate's own device scan "
                         "disagree about the validation set")


# ---------------------------------------------------------------------------------------
class TheCalibrationTableSatisfiesItsOwnReading(unittest.TestCase):
    """C1 GREEN, against a table this file did not construct."""

    def test_the_LIVE_table_exhibits_NO_red_world(self):
        t = calibration(self)
        self.assertEqual(calibration_defects(t), [],
                         "the live calibration table exhibits a red world of its own")

    def test_every_LOADED_cell_names_the_command_that_produced_it(self):
        t = calibration(self)
        loaded = _loaded(t)
        self.assertTrue(loaded, "the table drove no load at all")
        for w in loaded:
            self.assertTrue(w["command"].strip(), "%s %s" % (w["device"], w["level"]))
            self.assertTrue(w["taking"].strip(), "%s %s" % (w["device"], w["level"]))
            if w["device_class"] == "block":
                node = "/dev/" + t["validation_set"][w["device"]]["block"]
                self.assertIn(node, w["command"],
                              "%s %s: the recorded command does not name the device node "
                              "it claims to have driven: %r"
                              % (w["device"], w["level"], w["command"]))
            for res in w["load_results"]:
                self.assertEqual(res["rc"], 0,
                                 "%s %s: the load itself failed (%r), so the cell measures "
                                 "a load that did not run"
                                 % (w["device"], w["level"], res["stderr_tail"][-200:]))

    def test_at_least_TWO_load_levels_were_driven_per_device(self):
        t = calibration(self)
        per = {}
        for w in _loaded(t):
            per.setdefault(w["device"], set()).add(w["level"])
        self.assertTrue(per)
        for dev, ls in per.items():
            self.assertGreaterEqual(len(ls), 2, "%s: %r" % (dev, sorted(ls)))

    def test_every_limit_carries_its_POPULATION_and_its_BASIS(self):
        """§A51's 2026-08-13 bracket, its named first live use. A limit is a figure with no
        digits, and it carries what a figure carries."""
        t = calibration(self)
        self.assertTrue(t["limits"], "the table states no limits at all")
        for lim in t["limits"]:
            self.assertTrue((lim.get("population") or "").strip(), repr(lim))
            self.assertTrue((lim.get("basis") or "").strip(), repr(lim))

    def test_the_rate_limit_states_that_it_is_NOT_a_ceiling(self):
        """The population that is easiest to overstate is this one: a rate measured at the
        levels this run drove is not a property of the device, the surface or the guest."""
        t = calibration(self)
        rate = [l for l in t["limits"] if "arrival RATE" in l["limit"]]
        self.assertEqual(len(rate), 1, repr([l["limit"] for l in t["limits"]]))
        self.assertIn("NOT a ceiling", rate[0]["population"])


# ---------------------------------------------------------------------------------------
class TheCalibrationTableReadingCanFail(unittest.TestCase):
    """THE SIX RED WORLDS, DRIVEN. Each mutant is the live table with one thing wrong, and
    each row names the code it expects — a mutant that reds for a different reason fails
    the row that planted it instead of passing it.

    The negative-result test, applied to this class itself: if the reading could not fail,
    every row above would be a sentence with a colon in it."""

    def setUp(self):
        self.live = calibration(self)
        self.assertEqual(calibration_defects(self.live), [],
                         "the live table is already defective, so a mutant reddening "
                         "proves nothing about the mutation")

    def _reds(self, code):
        found = calibration_defects(_mutant(self.live, CALIB_DEFECT_PLANTERS[code]))
        self.assertIn(code, found, "planted %s, the reading found %r" % (code, found))

    def test_a_cell_with_no_command_REDS(self):
        self._reds("NO-COMMAND")

    def test_a_cell_with_no_taking_clause_REDS(self):
        self._reds("NO-TAKING")

    def test_a_SINGLE_LOAD_table_REDS(self):
        self._reds("SINGLE-LOAD")

    def test_a_SPLICED_window_REDS(self):
        self._reds("SPLICED-WINDOW")

    def test_a_limit_naming_NO_POPULATION_REDS(self):
        self._reds("LIMIT-NO-POPULATION")

    def test_a_limit_naming_NO_BASIS_REDS(self):
        self._reds("LIMIT-NO-BASIS")

    def test_a_BUILDER_AUTHORED_RULING_on_a_divergence_REDS(self):
        self._reds("RULING-AUTHORED")

    def test_SILENT_ACCOMMODATION_a_table_with_no_divergence_list_REDS(self):
        self._reds("NO-DIVERGENCE-LIST")

    def test_the_reading_finds_EVERY_code_IN_THE_CLOSED_SET(self):
        """THE POSITIVE CONTROL FOR THE READING ITSELF. A zero is not reported without an
        instrument shown to find a known-present case, and this is that showing — code by
        code, each planted alone, so an empty answer from the live table is an answer and
        not a silence.

        [WHAT THIS ROW FIRST ASSERTED, kept because the correction is the finding: that ONE
        mutant carrying every defect yields every code at once. It cannot, and the reading
        is right rather than wrong — NO-DIVERGENCE-LIST and RULING-AUTHORED are mutually
        exclusive BY CONSTRUCTION, because a table with no divergence list has no
        divergence to carry an authored ruling. The row was demanding a world that does not
        exist. Plant-each-alone is the stronger control anyway: it names which mutation
        produces which code, where the all-at-once form could have passed with two clauses
        wired to one defect.]"""
        for code, plant in sorted(CALIB_DEFECT_PLANTERS.items()):
            found = calibration_defects(_mutant(self.live, plant))
            self.assertIn(code, found,
                          "the reading did not find %s when it was planted alone (it "
                          "found %r), so an empty answer about the live table says "
                          "nothing about %s" % (code, found, code))
        self.assertEqual(sorted(CALIB_DEFECT_PLANTERS), sorted(CALIB_DEFECT_CODES),
                         "a code in the closed set has no planter, so nothing shows it "
                         "can ever be emitted")

    def test_the_two_DIVERGENCE_codes_are_mutually_exclusive_BY_CONSTRUCTION(self):
        """Stated and checked rather than left as the reason a stronger-looking row was
        weakened: a table with no divergence list cannot also carry a ruled divergence."""
        gone = calibration_defects(_mutant(self.live,
                                           CALIB_DEFECT_PLANTERS["NO-DIVERGENCE-LIST"]))
        ruled = calibration_defects(_mutant(self.live,
                                            CALIB_DEFECT_PLANTERS["RULING-AUTHORED"]))
        self.assertIn("NO-DIVERGENCE-LIST", gone)
        self.assertNotIn("RULING-AUTHORED", gone)
        self.assertIn("RULING-AUTHORED", ruled)
        self.assertNotIn("NO-DIVERGENCE-LIST", ruled)


# ---------------------------------------------------------------------------------------
class TheArrivalsAreMEASUREDAndNotAssumed(unittest.TestCase):
    """C1's substance. Arrivals MEASURED, never assumed — and measured by two routes that
    can disagree, because an instrument checked only against itself is checked by nobody.

      R1  /proc/interrupts per-IRQ deltas — a kernel counter, nothing to drop
      R2  tracefs `trace` lines attributed per device — the declared surface, droppable,
          and the drop MEASURED rather than assumed absent"""

    def test_a_LOADED_window_carries_MORE_arrivals_than_its_CONTROL(self):
        """THE POSITIVE CONTROL. Without it the loaded figures have nothing to be larger
        than, and a table of numbers is not a measurement of anything."""
        t = calibration(self)
        for dev in {w["device"] for w in _loaded(t)}:
            ctrl = _controls(t, dev)
            self.assertTrue(ctrl, "%s has no control window" % dev)
            base = max(w["arrivals"]["count"] for w in ctrl)
            top = max(w["arrivals"]["count"] for w in _loaded(t, dev))
            self.assertGreater(top, base,
                               "%s: the loaded windows produced no more arrivals than the "
                               "idle control (%d vs %d), so either the load missed the "
                               "device or the surface is not carrying its subject"
                               % (dev, top, base))

    def test_the_HIGHER_load_level_carries_MORE_arrivals_than_the_lower(self):
        """The spread the derivation needs. A table whose levels do not separate has two
        rows and one data point."""
        t = calibration(self)
        for dev in {w["device"] for w in _loaded(t)}:
            by_level = {}
            for w in _loaded(t, dev):
                by_level.setdefault(w["level"], []).append(w["arrivals"]["count"])
            ordered = sorted(by_level)
            lo = max(by_level[ordered[0]])
            hi = max(by_level[ordered[-1]])
            self.assertGreater(hi, lo, "%s: %r" % (dev, by_level))

    def test_the_TWO_ROUTES_agree_in_direction(self):
        """The interrupt counter and the tracepoint surface are independent readings of one
        world. They need not agree in magnitude — they count different things — but a load
        that raises one and not the other means one of them is not measuring this device."""
        t = calibration(self)
        for dev in {w["device"] for w in _loaded(t)}:
            ctrl = _controls(t, dev)[0]
            top = max(_loaded(t, dev), key=lambda w: w["arrivals"]["count"])
            self.assertGreater(top["arrivals"]["count"], ctrl["arrivals"]["count"], dev)
            self.assertGreater(top["interrupts"]["count"], ctrl["interrupts"]["count"],
                               "%s: the trace surface saw the load and the interrupt "
                               "counter did not (%r vs %r)"
                               % (dev, top["interrupts"], ctrl["interrupts"]))

    def test_every_cell_states_whether_it_LOST_lines(self):
        """A count that dropped lines is a FLOOR and not a total, and the difference is not
        recoverable later. The kernel's own header is read for it."""
        t = calibration(self)
        for w in t["windows"]:
            self.assertIsNotNone(w["trace_totals"]["dropped"],
                                 "%s %s cannot say whether it lost lines, so its count is "
                                 "neither a total nor a floor" % (w["device"], w["level"]))
            self.assertIsNotNone(w["overrun_delta"])

    def test_every_cell_carries_the_FOUR_events_it_claims_to_measure(self):
        """`set_event` takes ONE event per write. A joined write enables the first name and
        drops the rest, and the instrument would then measure a smaller surface than the
        one its basis line names."""
        t = calibration(self)
        for w in t["windows"]:
            self.assertEqual(sorted(w["events_enabled_at_open"]),
                             sorted(t["instrument"]["events_enabled"]),
                             "%s %s measured a different event set than it declares"
                             % (w["device"], w["level"]))

    def test_every_rate_is_computed_from_the_windows_OWN_elapsed_time(self):
        t = calibration(self)
        for w in t["windows"]:
            self.assertGreater(w["elapsed_s"], 0.0)
            expected = round(w["arrivals"]["count"] / w["elapsed_s"], 3)
            self.assertAlmostEqual(w["rate_arrivals_per_s"], expected, places=2,
                                   msg="%s %s" % (w["device"], w["level"]))

    def test_every_window_records_its_subject_at_OPEN_and_at_CLOSE(self):
        t = calibration(self)
        for w in t["windows"]:
            for end in ("open", "close"):
                self.assertTrue(w[end]["boot_id"])
                self.assertIsNotNone(w[end]["uptime_s"])
            self.assertTrue(w["subject_stable"], "%s %s spliced" % (w["device"], w["level"]))

    def test_every_window_opened_on_a_WARM_subject(self):
        """AMENDMENT 13's physical non-vacuity, inherited by citation rather than
        rediscovered: a figure taken while the readiness signal climbs measures paging.

        The verdict is now the MEDIAN of 3 repeated readiness pairs (board :2849 option C),
        so a single cold outlier no longer reds a warm guest. The subject and its meaning
        are unchanged; the sibling row below proves the verdict is that median and not a
        widened threshold."""
        t = calibration(self)
        for w in t["windows"]:
            self.assertTrue(w["open"]["warm"],
                            "%s %s opened COLD (%r) — the figure measures warm-up"
                            % (w["device"], w["level"], w["open"]["mem_available_kb"]))
            self.assertTrue(w["open"]["readiness_signal"].strip())

    def test_the_warm_verdict_is_the_MEDIAN_of_its_own_repeats(self):
        """THE DE-FLAKE MADE CHECKABLE, and the row the all-cold-triple control drives.

        The single-shot readiness figure occasionally caught a cold/paging outlier and
        mis-read a warm guest as still-warming — the flake board :2849 ruled de-flaked by
        median-of-repeats (option C). This row refuses two ways the fix could rot into a
        loosening: a triple SILENTLY COLLAPSED back to one shot (robustness in name only),
        and an emitted `warm` that DISAGREES with the median of its own recorded repeats (a
        widened threshold, or a verdict that stopped following its samples). It does NOT
        re-assert warmth — that is the row above; here the claim is only that the verdict is
        the honest median of exactly the repeats the window shipped."""
        t = calibration(self)
        for w in t["windows"]:
            o = w["open"]
            drifts = o.get("readiness_drift_kb", [])
            self.assertEqual(len(drifts), 3,
                             "%s %s carries %d readiness repeats, not the 3 the median is "
                             "taken over — a single-shot measurement cannot be robust to a "
                             "single-shot outlier" % (w["device"], w["level"], len(drifts)))
            rederived = _warm_verdict_from_samples(o.get("mem_at_open_kb"), drifts,
                                                   o.get("uptime_s"))
            self.assertEqual(rederived, o["warm"],
                             "%s %s emitted warm=%r but the median of its OWN repeats "
                             "(%r, anchor %r, uptime %r) says warm=%r — the verdict no "
                             "longer follows from its samples"
                             % (w["device"], w["level"], o["warm"], drifts,
                                o.get("mem_at_open_kb"), o.get("uptime_s"), rederived))


# ---------------------------------------------------------------------------------------
class TheCalibrationLeftTheGuestAsItFoundIt(unittest.TestCase):
    """THE ROW THAT WOULD CATCH A CONCESSION, at the calibration rather than at the probe.
    W1b's restore discipline, re-run: the tracing pre-state is read before the first window
    and compared field by field after the last, and the surface modes are re-read from the
    same run."""

    def test_the_tracing_state_was_RESTORED_field_by_field(self):
        t = calibration(self)
        self.assertEqual(t["trace_post_state"], t["trace_pre_state"],
                         "the calibration left the guest's tracing configuration changed")
        self.assertTrue(t["restore_verified"])

    def test_the_state_the_run_FOUND_is_the_state_W1b_RECORDED(self):
        """THE ROW THAT WOULD HAVE CAUGHT THIS PASS'S WORST DEFECT, and it is here because
        the pass committed it.

        `post == pre` is a comparison against WHATEVER THE RUN FOUND. An early version of
        this instrument raised inside the window loop after writing `tracing_on 0` and
        never put it back; every later run then read that 0 as its own pre-state and
        answered `restored: True` while the guest sat with tracing disabled. A RESTORE
        CHECK WHOSE BASELINE IS ITS OWN DAMAGE CANNOT FAIL.

        The baseline is therefore PINNED to the state W1b recorded and restored on
        2026-08-12, so the residue class is visible rather than absorbed. `buffer_size_kb`
        is deliberately NOT pinned: no prior pass recorded it, so a pin here would be this
        file inventing a baseline instead of citing one."""
        t = calibration(self)
        found = t["trace_pre_state"]
        for field, expected in (("tracing_on", "1"), ("current_tracer", "nop"),
                                ("set_event", ""), ("events/enable", "0")):
            self.assertEqual(found[field], expected,
                             "the run FOUND %s=%r where W1b recorded %r — something left "
                             "the guest's tracing configuration changed, and a post==pre "
                             "restore check would absorb it silently"
                             % (field, found[field], expected))
        self.assertEqual(found["instances"], [])
        self.assertEqual(found["set_event_bytes"], 0)

    def test_the_SURFACE_WAS_NOT_WIDENED_to_make_the_observer_work(self):
        """ADDENDUM 6 §4's boundary. The privilege attaches to the OBSERVER. A chmod would
        have bought it for every process on the box, and `tests/test_ep29.py`'s standing
        unprivileged rows would red — which is the architecture, not a side effect."""
        t = calibration(self)
        for p in ("/sys/kernel/tracing", "/sys/kernel/debug"):
            self.assertEqual(t["surface_modes"][p]["mode"], "0o700", p)
            self.assertEqual(t["surface_modes"][p]["uid"], 0, p)
        self.assertFalse(t["establishment"]["found"]["surface_readable_unprivileged"],
                         "the arrival surface is readable UNPRIVILEGED after the "
                         "calibration, so the priced privilege is no longer being paid")
        self.assertTrue(t["establishment"]["found"]["surface_readable_privileged"])

    def test_the_access_pair_DISCRIMINATES_inside_this_run_too(self):
        """Both halves taken by the same run, so the pair is a pair. A probe answering the
        same under both privileges would establish nothing about either."""
        t = calibration(self)
        self.assertEqual(t["unprivileged_probe"]["stdout"], "False",
                         repr(t["unprivileged_probe"]))
        self.assertTrue(t["unprivileged_probe"]["command"].startswith("sudo -n -u "))


# ---------------------------------------------------------------------------------------
def _synthetic_calibration():
    """A HAND-BUILT TABLE OF THE SAME SHAPE, so the red worlds below answer when the lab is
    down. The estate's own idiom, IMPORTED from `TheW0gRowsCanBeMadeToFail` rather than
    re-derived: plant a payload into the memo, run the REAL row through unittest's own
    machinery, read its result.

    Every figure here is INVENTED and none of it is evidence about anything. It exists so
    that the question "what would make this row speak against me" has a driven answer."""
    def win(level, kind, arrivals, irqs, elapsed, repeat=1):
        # A clean all-warm triple: three repeated 0.2s pairs with zero drift, well inside
        # the 1%-of-3.5M threshold, so the median-verdict row passes on the substrate the
        # red worlds mutate away from.
        subj = {"boot_id": "b-0000", "machine_id": "m-0000", "hostname": "gov-lab",
                "uptime_s": 70000.0 + repeat, "monotonic": 1.0, "warm": True,
                "mem_available_kb": [3500000, 3500000], "mem_at_open_kb": 3500000,
                "readiness_pairs_kb": [[3500000, 3500000], [3500000, 3500000],
                                       [3500000, 3500000]],
                "readiness_drift_kb": [0, 0, 0],
                "readiness_signal": "MemAvailable stable across the MEDIAN of 3 repeated "
                                    "0.2s pairs (<1% drift) AND uptime > 600s"}
        return {
            "device": "virtio1", "device_class": "block", "level": level,
            "level_kind": kind, "repeat": repeat,
            "command": ("dd if=/dev/vda of=/dev/null bs=4096 count=256 iflag=direct"
                        if kind == "LOAD" else "sleep 3.0   # no load driven"),
            "load_results": [], "taking": "a synthetic cell",
            "load_size": {"requested_units": 256 if kind == "LOAD" else None,
                          "delivered_units": 256 if kind == "LOAD" else None,
                          "delivered_known": kind == "LOAD", "truncated": False,
                          "unit": "4096-byte direct reads (dd) or datagrams (udp sender)"},
            "open": dict(subj), "close": dict(subj), "subject_stable": True,
            "elapsed_s": elapsed,
            "interrupts": {"per_irq_delta": {"25": irqs},
                           "irq_names": {"25": "virtio1-req.0"},
                           "count": irqs, "basis": "synthetic"},
            "arrivals": {"count": arrivals, "by_event": {"block_rq_issue": arrivals},
                         "basis": "synthetic"},
            "events_enabled_at_open": ["block:block_rq_complete", "block:block_rq_issue",
                                       "irq:irq_handler_entry", "net:net_dev_queue"],
            "trace_totals": {"by_event": {}, "per_device": {}, "unattributed": 0,
                             "unattributed_sample": [], "parsed_lines": arrivals,
                             "entries_in_buffer": arrivals, "entries_written": arrivals,
                             "dropped": 0},
            "overrun_delta": 0,
            "rate_interrupts_per_s": round(irqs / elapsed, 3),
            "rate_arrivals_per_s": round(arrivals / elapsed, 3),
        }

    found = {"kernel": GUEST_KERNEL, "validation_set": ["virtio0", "virtio1", "virtio2"],
             "device_classes": ["block", "net"], "tracefs_mode": "0o700", "tracefs_uid": 0,
             "surface_readable_unprivileged": False, "surface_readable_privileged": True}
    state = {"tracing_on": "1", "current_tracer": "nop", "set_event": "",
             "events/enable": "0", "buffer_size_kb": "1408", "set_event_bytes": 0,
             "instances": []}
    return {
        "instrument": {"name": "ep29-w2a-calibration-observer", "profile": "retake",
                       "params": {"repeats": 1},
                       "source_sha256": hashlib.sha256(
                           _CALIB_DRIVER.encode("utf-8")).hexdigest(),
                       "events_enabled": ["block:block_rq_issue", "block:block_rq_complete",
                                          "irq:irq_handler_entry", "net:net_dev_queue"]},
        "uname": GUEST_KERNEL, "uid": 0, "hostname": "gov-lab", "boot_id": "b-0000",
        "machine_id": "m-0000",
        "validation_set": {"virtio1": {"class": "block", "block": "vda", "devno": "253:0",
                                       "netif": None, "irqs": ["24", "25", "26"],
                                       "driver": "virtio_blk"}},
        "establishment": {"plan_ground": dict(found), "found": dict(found),
                          "divergences": [], "ground_true": True},
        "unprivileged_probe": {"user": "ubuntu", "rc": 0, "stdout": "False",
                               "command": "sudo -n -u ubuntu python3 -c ..."},
        "surface_modes": {"/sys/kernel/tracing": {"mode": "0o700", "uid": 0},
                          "/sys/kernel/debug": {"mode": "0o700", "uid": 0}},
        "windows": [win("L0", "CONTROL", 0, 0, 3.0),
                    win("L1", "LOAD", 768, 256, 0.05),
                    win("L2", "LOAD", 6144, 2048, 0.12)],
        "limits": [{"limit": "the highest per-device arrival RATE this run reached",
                    "value": None,
                    "population": "the loaded windows of this run only — NOT a ceiling of "
                                  "the device, the surface or the guest",
                    "basis": "attributed trace lines over the window's own elapsed"}],
        "trace_pre_state": dict(state), "trace_post_state": dict(state),
        "restore_verified": True,
        "_local_digest": hashlib.sha256(_CALIB_DRIVER.encode("utf-8")).hexdigest(),
    }


#: The rows the synthetic substrate can carry. `test_the_validation_set_AGREES_with_the_
#: shipped_surface_probe` is DELIBERATELY ABSENT: it reads the live `guest_probe` as well,
#: so planting only half its world would measure the plant. It is covered live and nowhere
#: else, and saying so is cheaper than a red world that proves the wrong thing.
_CALIB_ROWS = (
    (TheCalibrationRanAtTheGuestAndOnTheBytesWeSent,
     ("test_the_observer_ran_in_the_GUEST_at_the_pinned_kernel",
      "test_the_guest_ran_THE_BYTES_THIS_FILE_HOLDS")),
    (TheCalibrationGroundIsTrueAtTheWalk,
     ("test_every_ground_fact_the_plan_asserts_is_TRUE_at_the_guest",
      "test_the_ground_walk_covers_the_facts_the_TABLE_depends_on")),
    (TheCalibrationTableSatisfiesItsOwnReading,
     ("test_the_LIVE_table_exhibits_NO_red_world",
      "test_every_LOADED_cell_names_the_command_that_produced_it",
      "test_at_least_TWO_load_levels_were_driven_per_device",
      "test_every_limit_carries_its_POPULATION_and_its_BASIS",
      "test_the_rate_limit_states_that_it_is_NOT_a_ceiling")),
    (TheArrivalsAreMEASUREDAndNotAssumed,
     ("test_a_LOADED_window_carries_MORE_arrivals_than_its_CONTROL",
      "test_the_HIGHER_load_level_carries_MORE_arrivals_than_the_lower",
      "test_the_TWO_ROUTES_agree_in_direction",
      "test_every_cell_states_whether_it_LOST_lines",
      "test_every_cell_carries_the_FOUR_events_it_claims_to_measure",
      "test_every_rate_is_computed_from_the_windows_OWN_elapsed_time",
      "test_every_window_records_its_subject_at_OPEN_and_at_CLOSE",
      "test_every_window_opened_on_a_WARM_subject",
      "test_the_warm_verdict_is_the_MEDIAN_of_its_own_repeats")),
    (TheCalibrationLeftTheGuestAsItFoundIt,
     ("test_the_tracing_state_was_RESTORED_field_by_field",
      "test_the_state_the_run_FOUND_is_the_state_W1b_RECORDED",
      "test_the_SURFACE_WAS_NOT_WIDENED_to_make_the_observer_work",
      "test_the_access_pair_DISCRIMINATES_inside_this_run_too")),
)


def _run_calib_against(planted, cls, meth):
    """Run a REAL W2a row against a PLANTED table. The row is executed by unittest's own
    machinery, so what is measured is the row that ships and not a paraphrase of it."""
    key = ("retake", hashlib.sha256(_CALIB_DRIVER.encode("utf-8")).hexdigest())
    sentinel = object()
    saved = _CALIB_MEMO.get(key, sentinel)
    _CALIB_MEMO[key] = planted
    try:
        return unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(cls(meth))
    finally:
        if saved is sentinel:
            _CALIB_MEMO.pop(key, None)
        else:
            _CALIB_MEMO[key] = saved


class TheW2aRowsCanBeMadeToFail(unittest.TestCase):
    """THE NEGATIVE-RESULT TEST, APPLIED TO W2a's OWN CALIBRATION ROWS.

    The mutant rows above prove THE READING can fail. These prove THE ROWS can — a
    different claim, and the one that matters when the table is real and wrong rather than
    absent and planted."""

    def assertRowFAILED(self, res, why):
        """A RED WORLD MUST RED FOR ITS OWN REASON. `wasSuccessful()` is False for an ERROR
        too, so a planted table that breaks the row — a KeyError, a bad shape — would
        satisfy a bare `assertFalse` and read on the page exactly like the claim biting."""
        self.assertEqual(res.errors, [],
                         "the row ERRORED rather than failed, so the planted world broke "
                         "the instrument instead of the claim: %r" % (res.errors,))
        self.assertEqual(len(res.failures), 1, why)

    def test_the_synthetic_control_PASSES_every_row(self):
        """CONTROL, FIRST. Without it a red below could be the substrate being malformed
        rather than the clause biting, and the two read identically on the page."""
        ran = 0
        for cls, meths in _CALIB_ROWS:
            for meth in meths:
                res = _run_calib_against(_synthetic_calibration(), cls, meth)
                self.assertTrue(res.wasSuccessful(),
                                "the synthetic control FAILS %s.%s, so every red world "
                                "below is uninterpretable: %r"
                                % (cls.__name__, meth, res.failures + res.errors))
                ran += 1
        self.assertEqual(ran, sum(len(m) for _, m in _CALIB_ROWS))
        self.assertGreater(ran, 15, "non-vacuity: the control is not a stub")

    def _red(self, mutate, cls, meth, why):
        t = _synthetic_calibration()
        mutate(t)
        self.assertRowFAILED(_run_calib_against(t, cls, meth), why)

    def test_a_CONTROL_that_out_arrives_the_LOAD_REDS(self):
        """The load missed the device, or the surface is not carrying its subject. Either
        way the table's figures are about something else."""
        def m(t):
            t["windows"][0]["arrivals"]["count"] = 99999
        self._red(m, TheArrivalsAreMEASUREDAndNotAssumed,
                  "test_a_LOADED_window_carries_MORE_arrivals_than_its_CONTROL",
                  "a control out-arriving every load passes the positive-control row")

    def test_TWO_LEVELS_THAT_DO_NOT_SEPARATE_RED(self):
        """Two rows and one data point. W2b's derivation needs spread, and this is where
        its absence is supposed to become visible."""
        def m(t):
            t["windows"][2]["arrivals"]["count"] = t["windows"][1]["arrivals"]["count"]
        self._red(m, TheArrivalsAreMEASUREDAndNotAssumed,
                  "test_the_HIGHER_load_level_carries_MORE_arrivals_than_the_lower",
                  "levels that do not separate pass the spread row")

    def test_ONE_ROUTE_MOVING_WITHOUT_THE_OTHER_REDS(self):
        """The cross-check earns its keep here: a trace surface that saw the load while the
        kernel's own counter did not means one of the two is not measuring this device."""
        def m(t):
            for w in t["windows"]:
                w["interrupts"]["count"] = 7
        self._red(m, TheArrivalsAreMEASUREDAndNotAssumed,
                  "test_the_TWO_ROUTES_agree_in_direction",
                  "a flat interrupt counter under a load the surface saw passes the "
                  "two-route row")

    def test_A_CELL_THAT_CANNOT_SAY_WHETHER_IT_LOST_LINES_REDS(self):
        def m(t):
            t["windows"][2]["trace_totals"]["dropped"] = None
        self._red(m, TheArrivalsAreMEASUREDAndNotAssumed,
                  "test_every_cell_states_whether_it_LOST_lines",
                  "a cell that cannot say whether it dropped lines passes")

    def test_A_SHORTENED_EVENT_SET_REDS(self):
        """The `set_event` footgun, guarded: a cell measuring one event while its basis
        line names four."""
        def m(t):
            t["windows"][1]["events_enabled_at_open"] = ["block:block_rq_issue"]
        self._red(m, TheArrivalsAreMEASUREDAndNotAssumed,
                  "test_every_cell_carries_the_FOUR_events_it_claims_to_measure",
                  "a cell measuring one event of four passes the event-set row")

    def test_A_RATE_THAT_DOES_NOT_FOLLOW_FROM_ITS_OWN_INPUTS_REDS(self):
        """This row exists because the first draft of the instrument stored a ROUNDED
        elapsed beside a rate computed from the unrounded one, and the arithmetic did not
        close. Small, and unreconstructable is unreconstructable."""
        def m(t):
            t["windows"][1]["rate_arrivals_per_s"] = 1.0
        self._red(m, TheArrivalsAreMEASUREDAndNotAssumed,
                  "test_every_rate_is_computed_from_the_windows_OWN_elapsed_time",
                  "a rate unrelated to its own count and elapsed passes")

    def test_A_COLD_OPENED_WINDOW_REDS(self):
        """AMENDMENT 13's own red world, in its own words: a deliberately cold-opened run
        MUST be caught by this row, labelled and excluded. Unchanged by the median-of-3
        de-flake: it mutates the emitted verdict, and the row above still asserts it."""
        def m(t):
            t["windows"][2]["open"]["warm"] = False
        self._red(m, TheArrivalsAreMEASUREDAndNotAssumed,
                  "test_every_window_opened_on_a_WARM_subject",
                  "a cold-opened window passes the physical non-vacuity row")

    def test_an_ALL_COLD_TRIPLE_CLAIMING_WARM_REDS(self):
        """BOARD :2849's MUST-RED, DRIVEN. A genuinely cold measurement — every one of the
        three repeats drifting past the threshold — must still be caught. The de-flake drops
        ONE outlier, never a majority; a window whose WHOLE triple is cold while its flag
        says warm is the loosening the fix must not become, and this is the row that refuses
        it. If this passed, median-of-3 would have bought robustness by going blind."""
        def m(t):
            t["windows"][2]["open"]["readiness_drift_kb"] = [3500000, 3500000, 3500000]
        self._red(m, TheArrivalsAreMEASUREDAndNotAssumed,
                  "test_the_warm_verdict_is_the_MEDIAN_of_its_own_repeats",
                  "an all-cold triple wearing a warm flag passes the median-verdict row")

    def test_a_TRIPLE_COLLAPSED_TO_A_SINGLE_SHOT_REDS(self):
        """A silent revert to single-shot — the exact regression this de-flake exists to
        prevent — must red. A median taken over one repeat is robustness in name only, and
        the non-vacuity check refuses a triple that quietly became a single figure again."""
        def m(t):
            t["windows"][2]["open"]["readiness_drift_kb"] = [0]
        self._red(m, TheArrivalsAreMEASUREDAndNotAssumed,
                  "test_the_warm_verdict_is_the_MEDIAN_of_its_own_repeats",
                  "a single-shot measurement wearing the median row's name passes")

    def test_a_LONE_COLD_OUTLIER_AMONG_TWO_WARM_PASSES(self):
        """THE FLAKE ITSELF, NOW TOLERATED — and the proof the fix is a MEDIAN and not a
        widened threshold. The single cold pair that used to red a warm guest is, as one
        repeat of three, outvoted; the median of two warm reads and one cold outlier reads
        warm, while an all-cold triple still reads cold. This is a must-PASS: it shows the
        median-verdict row does NOT red on the precise input that was the flake."""
        # the median LOGIC itself: one cold outlier among two warm reads is warm ...
        self.assertTrue(_warm_verdict_from_samples(3500000, [0, 0, 3500000], 70001.0),
                        "the median of two warm repeats and one cold outlier must read WARM")
        # ... but a genuinely cold triple is not — the threshold was not widened
        self.assertFalse(_warm_verdict_from_samples(3500000,
                                                    [3500000, 3500000, 3500000], 70001.0),
                         "an all-cold triple must still read COLD")
        # and the LIVE median row passes on a table carrying exactly that outlier triple
        t = _synthetic_calibration()
        t["windows"][2]["open"]["readiness_drift_kb"] = [0, 0, 3500000]
        res = _run_calib_against(t, TheArrivalsAreMEASUREDAndNotAssumed,
                                 "test_the_warm_verdict_is_the_MEDIAN_of_its_own_repeats")
        self.assertEqual(res.errors, [], "the outlier triple broke the row: %r" % res.errors)
        self.assertTrue(res.wasSuccessful(),
                        "a lone cold outlier among two warm repeats red the median row, so "
                        "the de-flake did not tolerate the noise it exists for: %r"
                        % (res.failures,))

    def test_A_SPLICED_WINDOW_REDS_THE_LIVE_ROW_TOO(self):
        def m(t):
            t["windows"][1]["subject_stable"] = False
        self._red(m, TheArrivalsAreMEASUREDAndNotAssumed,
                  "test_every_window_records_its_subject_at_OPEN_and_at_CLOSE",
                  "a spliced window passes the subject-stability row")

    def test_A_DIVERGENT_GROUND_REDS_THE_C0_ROW(self):
        """C0's third state has to be REACHED to be worth having. This is the row that
        reaches it."""
        def m(t):
            t["establishment"]["divergences"] = [
                {"fact": "validation_set", "expected": ["virtio0", "virtio1", "virtio2"],
                 "found": ["virtio0"], "resolution": "STOP-AND-REPORT"}]
            t["establishment"]["ground_true"] = False
        self._red(m, TheCalibrationGroundIsTrueAtTheWalk,
                  "test_every_ground_fact_the_plan_asserts_is_TRUE_at_the_guest",
                  "a diverged ground passes the C0 row, so the stop would never be reached")

    def test_A_WIDENED_SURFACE_REDS(self):
        """THE CONCESSION ROW. A chmod would buy the privilege for every process on the box
        — the thing ADDENDUM 6 §4 says this must not be — and this is where it shows."""
        def m(t):
            t["surface_modes"]["/sys/kernel/tracing"]["mode"] = "0o755"
        self._red(m, TheCalibrationLeftTheGuestAsItFoundIt,
                  "test_the_SURFACE_WAS_NOT_WIDENED_to_make_the_observer_work",
                  "a widened tracefs mode passes the concession row")

    def test_AN_UNPRIVILEGED_READABLE_SURFACE_REDS(self):
        """The other half of the same architecture: if the surface became readable without
        privilege, the window law's priced cost is no longer being paid."""
        def m(t):
            t["unprivileged_probe"]["stdout"] = "True"
        self._red(m, TheCalibrationLeftTheGuestAsItFoundIt,
                  "test_the_access_pair_DISCRIMINATES_inside_this_run_too",
                  "an unprivileged-readable surface passes the access-pair row")

    def test_A_RESIDUE_BASELINE_REDS(self):
        """THE DEFECT THIS PASS COMMITTED, driven. A run that FINDS tracing already
        disabled is a run whose baseline is somebody's damage, and `post == pre` would
        answer True about it."""
        def m(t):
            t["trace_pre_state"]["tracing_on"] = "0"
            t["trace_post_state"]["tracing_on"] = "0"
        self._red(m, TheCalibrationLeftTheGuestAsItFoundIt,
                  "test_the_state_the_run_FOUND_is_the_state_W1b_RECORDED",
                  "a run that found tracing already off passes the baseline row")

    def test_AN_UNRESTORED_TRACING_STATE_REDS(self):
        def m(t):
            t["trace_post_state"]["set_event"] = "block:block_rq_issue"
            t["restore_verified"] = False
        self._red(m, TheCalibrationLeftTheGuestAsItFoundIt,
                  "test_the_tracing_state_was_RESTORED_field_by_field",
                  "a tracing state left changed passes the restore row")

    def test_A_TABLE_FROM_DIFFERENT_BYTES_REDS(self):
        """One home, checked. A table produced by an instrument this repo does not hold is
        a table nobody here has read."""
        def m(t):
            t["instrument"]["source_sha256"] = "0" * 64
        self._red(m, TheCalibrationRanAtTheGuestAndOnTheBytesWeSent,
                  "test_the_guest_ran_THE_BYTES_THIS_FILE_HOLDS",
                  "a table from foreign bytes passes the one-home row")

    def test_A_TABLE_TAKEN_ON_THIS_HOST_REDS(self):
        """The oldest trap in this file: an observer that ran on this laptop would answer,
        and every answer would be about the wrong kernel."""
        def m(t):
            t["uname"] = platform.uname().release
        self._red(m, TheCalibrationRanAtTheGuestAndOnTheBytesWeSent,
                  "test_the_observer_ran_in_the_GUEST_at_the_pinned_kernel",
                  "a table taken on this host passes the guest row")



# =======================================================================================
# EP-29 W2b — THE INTAKE LAW PASS (ADDENDUM 7 §1 claims C2 and C3, §2's W2b item)
#
# W2a MEASURED and W2b DERIVES AND LANDS. The seam between them is the only thing that makes
# this a measured law rather than an asserted one, so the rows below RECOMPUTE every landed
# value from W2a's own cells rather than asserting the number that shipped. A row that read
# the pack's 6144 and asserted 6144 would pass on any value the pack happened to carry.
#
# THE THREE CONSTRAINTS THE MEASUREMENT PUT ON THIS DERIVATION (EP-29 C2's :683 bracket, each
# established by W2a and each now LAW TEXT in DEV-LAW-INTAKE rather than advice):
#   1. a law value derives from the COUNT column ONLY, never from the RATE column
#   2. the cited cell's basis is DELIVERED, never REQUESTED
#   3. the declaration is PER DEVICE CLASS
# Each has a red world below, driven through a real row on a planted pack.
# =======================================================================================

#: THIS pass's own pre-write commit, taken with `git rev-parse HEAD` before any write
#: (§A53 — `git checkout --` no longer undoes a write since the 08-03 autosync repair, so
#: the commit is TAKEN and not trusted). It is the 1.21.0 ERA: the world W2b moved off.
#: PINNED BY CONTENT AND NEVER BY VERSION NUMBER — `era_pin`'s own stated cap and this
#: estate's most expensive known trap. `TheW2bSweep` checks the blob's digest against the
#: sha256 W2a's close recorded, rather than trusting this comment.
W2B_BEFORE_COMMIT = "3d187e217705bbf5d851c5d5f71cde8d19d6227d"
W2B_BEFORE_VERSION = "1.21.0"
W2B_AFTER_VERSION = "1.22.0"
W2B_BEFORE_PACK_SHA = "d079b573ba9e28d1b623033b5779662e4e8bc9282254c0f4423756b29e2fe4aa"

#: The two intakes W2b declares, one per device class the validation set spans. PER CLASS is
#: LAW here (DEV-LAW-INTAKE's third derivation constraint) rather than a convenience: net's
#: interrupt-per-datagram ratio doubled between runs while block's held at exactly 1.0, so
#: one value across both would be fitted to two behaviours.
THE_DECLARED_INTAKES = ("device-intake@block", "device-intake@net")

#: The device intake act class that STILL holds no definition after W2b. It is what makes
#: "the refusal was NARROWED, never removed" checkable at this layer, and it is also how the
#: fence between W2b and W3 is visible in the record: recording at the declared grade through
#: the gate is the shim's contract, so this pass declares the GRADE and builds no ENGINE.
UNBUILT_INTAKE_ACT = "DEVICE-INPUT-RECORD"

#: EP-29 W2a's CALIBRATION TABLE — the cells this law's values derive from, transcribed from
#: that pass's own BUILD-PROGRESS entry of 2026-08-13. Each row is
#: (device, level, delivered_units or None, the arrival COUNTS of the cell's three repeats).
#: THE COUNT COLUMN, AND ONLY IT. Constraint 1 bars the rate column from carrying law; the
#: rates are carried separately below so the bar can be DRIVEN rather than promised.
W2A_BLOCK_CELLS = (
    ("virtio1", "L1", 256, (768, 768, 768)),
    ("virtio1", "L2", 2048, (6144, 6144, 6144)),
    ("virtio2", "L1", 92, (276, 276, 276)),
    ("virtio2", "L2", 736, (2208, 2208, 2208)),
)
W2A_NET_CELLS = (
    ("virtio0", "L1", None, (384, 388, 390)),
    ("virtio0", "L2", None, (3518, 3509, 3489)),
)

#: WHAT THE COMMANDS ASKED FOR, kept in its own name because the whole of constraint 2 is
#: that this is a DIFFERENT number from what was delivered and only one of them is a
#: population. `virtio2` is 366 KiB, so `dd count=256` returned after 92 and `count=2048`
#: after 736; the net sender reports no delivery figure at all, so its cells carry
#: `delivered_known: false` and 200/1600 are requests that never became a population.
W2A_REQUESTED = {("virtio1", "L1"): 256, ("virtio1", "L2"): 2048,
                 ("virtio2", "L1"): 256, ("virtio2", "L2"): 2048,
                 ("virtio0", "L1"): 200, ("virtio0", "L2"): 1600}

#: THE RATE COLUMN. Never a law input — carried so that "a law value derived from the RATE
#: column REDS" is exhibited against real figures rather than invented ones. W2a measured the
#: count column at max/min ratio 1.0000 on every block cell and these at up to 1.6265.
W2A_BLOCK_RATES = (15794, 15496, 14493, 68951, 81719, 69403,
                   7499, 4611, 6531, 19578, 14493, 23450)
W2A_NET_RATES = (6570, 6796, 6159, 52191, 44100, 47153)


def intake_declarations(pack, whole=False):
    """The DECLARE-INTAKE records of a pack, read by ACTION off the structure. Not by name
    shape and not by step name: §A51's first half, and the step this pass added would be the
    only member of any name-pattern this file could write."""
    out = []
    for st in pack["steps"]:
        for r in st["records"]:
            if r.get("action") == "DECLARE-INTAKE":
                out.append(r if whole else r["payload"])
    return out


def cap_from_cells(cells):
    """THE CAP'S DERIVATION, WRITTEN ONCE AND APPLIED PER CLASS.

    The constraint is I9 — recording scales with governance, never with traffic. A window of
    A arrivals produces ceil(A / cap) covering records, so the record count stays at ONE for
    every window in the measured population exactly when cap >= max(A), and the SMALLEST such
    value is max(A) itself. Direction from the law, number from the count column, and
    smallest-satisfying because among the values meeting I9 the smallest records the most —
    the fail-closed direction FS-WRITE-COALESCING already names one subsystem over.

    THIS FUNCTION IS THE DERIVATION AND NOT A RESTATEMENT OF THE ANSWER. The rows below apply
    it to W2a's cells and compare the result with what the pack carries, so a law value moves
    only when the table moves. `test_the_derivations_are_not_constant_functions` shows it
    returns something else for a different table."""
    return max(max(reps) for _dev, _lvl, _delivered, reps in cells)


def unit_from_cells(cells):
    """THE PER-ACT UNIT'S DERIVATION: arrivals per DELIVERED act, or the reason there is none.

    Returns `(value, reason)`. THE TWO WAYS THERE CAN BE NO VALUE ARE KEPT APART, because
    they are different facts and collapsing them is how a class ends up with a plausible
    number: a class with NO delivered figure has no divisor that is a population at all
    (constraint 2), while a class whose ratio is not exact across its cells has a divisor and
    no single answer. Only the first applies to net in this table, and the declaration says
    so in its own basis field."""
    if any(delivered is None for _d, _l, delivered, _r in cells):
        return None, ("no delivered figure — the only available divisor is a REQUESTED "
                      "number, which constraint 2 bars from carrying a value")
    ratios = {r / delivered for _d, _l, delivered, reps in cells for r in reps}
    if len(ratios) != 1:
        return None, "the ratio is not exact across the cells: %r" % sorted(ratios)
    v = ratios.pop()
    return (int(v) if v == int(v) else v), "exact across every cell and every repeat, on delivered"


class TheIntakeLawLanded(unittest.TestCase):
    """C2 — THE INTAKE DECLARATION LANDED AS LAW-DATA, through the ordinary door."""

    def test_exactly_the_two_intakes_one_per_device_class_are_declared(self):
        got = tuple(sorted(d["intake"] for d in intake_declarations(live_pack())))
        self.assertEqual(got, tuple(sorted(THE_DECLARED_INTAKES)))
        classes = sorted(d["device_class"] for d in intake_declarations(live_pack()))
        self.assertEqual(classes, ["block", "net"],
                         "the declaration is PER DEVICE CLASS and the validation set spans "
                         "exactly these two")

    def test_every_intake_declares_WINDOW_grade(self):
        """The never-clause's positive half, and it is deliberately a PRESENCE test.

        An absence test — 'per-interrupt' appearing nowhere — is the class that inverted on
        this estate once already (failure record item 10: a check whose correct answer is a
        count of zero in a growing file is a check waiting to invert), and it would invert
        here for certain, because DEV-LAW-INTAKE's own text contains the words in order to
        forbid them. So the grade is asserted to BE `window`, and the red world plants
        `per-interrupt` into the grade rather than into the prose."""
        for d in intake_declarations(live_pack()):
            self.assertEqual(d["grade"], "window", d["intake"])

    def test_the_never_clause_is_LAW_TEXT_and_not_commentary(self):
        """C2: 'the never-clause as LAW TEXT, not commentary'. The clause is asserted in the
        RULE RECORD the world boots with, not in an op description and not in a comment."""
        law = dict(_World().views.active_rules()["DEV-LAW-INTAKE"])["text"]
        for clause in ("NEVER RECORDED AT PER-INTERRUPT GRADE",
                       "NO DECLARATION UNDER THIS LAW MAY SET A BOUND OF ONE",
                       "COUNT", "DELIVERED", "PER DEVICE CLASS"):
            self.assertIn(clause, law, "the law text does not carry %r" % clause)

    def test_no_declaration_sets_a_bound_of_ONE(self):
        """The never-clause's operational half: a covering record standing for exactly one
        arrival is the per-interrupt grade wearing a window's name.

        [DOCUMENTED FLIP — EP-29 W3a, 2026-08-13, §A57 BY FALSIFICATION.
        CAUSE: W3a WITHDREW `device-intake@net`'s threshold, so one declaration now carries
        `value: None` and `None > 1` is a TypeError rather than a verdict.
        ASSERTED: every declaration's threshold is greater than one.
        SUPERSEDED: every declaration CARRYING a threshold has one greater than one, AND a
        declaration carrying none carries `None` — never a number this row would have to
        judge. REMAINS TRUE: the never-clause's operational half, over its whole population.
        GIVEN UP: nothing. THE ROW IS SCOPED AND NOT ERA-PINNED, DELIBERATELY, and the
        distinction is the one this pass had to get right twice: an ERA PIN is correct for a
        row asserting what a PAST PASS LANDED, and it would be wrong here, because this row
        asserts a LIVE PROPERTY OF THE CURRENT LAW. Pinning it to 1.22.0 would have made the
        suite green by retiring a standing guard, and a retired guard reads on the page
        exactly like a repaired one.]"""
        judged = 0
        for d in intake_declarations(live_pack()):
            value = d["max_arrivals"]["value"]
            if value is None:
                continue
            self.assertGreater(value, 1, d["intake"])
            judged += 1
        self.assertGreater(judged, 0,
                           "no declaration carries a threshold at all, so this row judged "
                           "nothing and its green says nothing")

    def test_every_intake_cites_a_window_that_a_DECLARATION_founds(self):
        declared = {w["window"] for w in window_declarations(live_pack())}
        self.assertTrue(declared, "no windows at all would make this row vacuous")
        for d in intake_declarations(live_pack()):
            self.assertIn(d["window"], declared,
                          "%s declares a grade for an admission no window founds" % d["intake"])

    def test_every_intake_states_what_it_does_NOT_declare(self):
        """The no-bare-form instruction at parameter ABSENCES, the shape DECLARE-IO-WINDOW's
        required `does_not_see` already took. A declaration naming no absence reads as
        covering everything it did not mention — and the first absence each of these names is
        the intake ENGINE, which is W3's and not this pass's."""
        for d in intake_declarations(live_pack()):
            self.assertGreaterEqual(len(d["does_not_declare"]), 3, d["intake"])
            self.assertIn("ENGINE", " ".join(d["does_not_declare"]),
                          "%s does not disclaim the intake engine, so a reader could take "
                          "the recording path as landed here" % d["intake"])
            self.assertIn("STREAM", " ".join(d["does_not_declare"]),
                          "%s does not classify I/O content out" % d["intake"])

    def test_every_intake_carries_LIMITS_each_with_its_population_and_basis(self):
        """§A51's 2026-08-13 bracket, second live use and the first inside LAW: a limit is a
        figure with no digits and carries MEASURED OVER and HOW TAKEN as DECLARED FIELDS, so
        their absence is checkable without reading sentences."""
        for d in intake_declarations(live_pack()):
            self.assertTrue(d["limits"], d["intake"])
            for lim in d["limits"]:
                for key in ("limit", "population", "basis"):
                    self.assertTrue(lim.get(key),
                                    "%s carries a limit with no %s: %r"
                                    % (d["intake"], key, lim))

    def test_the_closers_are_EVENT_based_and_never_TIME_based(self):
        """Forced twice over rather than preferred: a duration would derive from the rate
        column constraint 1 bars, and a clock that schedules a record is clock-as-scheduler,
        which this estate admits only as clock-as-sensor."""
        for d in intake_declarations(live_pack()):
            self.assertTrue(d["closers"], d["intake"])
            names = [c.split(" ")[0] for c in d["closers"]]
            self.assertEqual(sorted(names), ["max_arrivals", "unbind"], d["intake"])

    def test_the_new_op_declares_an_EXPLICIT_form_for_every_parameter(self):
        """C7 on this pass's own population: every definition it AUTHORS, which is one. A
        parameter form taken by silence is not declining the choice, it is taking it
        undecided."""
        d = ops_of(live_pack())["DECLARE-INTAKE"]
        self.assertTrue(d.get("params"))
        for p, form in d["params"].items():
            self.assertIn(form, ("required", "optional"), "DECLARE-INTAKE.%s = %r" % (p, form))
        known = set(d.get("params") or {}) | set(d.get("param_defaults") or {})
        self.assertEqual(set(d.get("payload_from") or []) - known, set(),
                         "DECLARE-INTAKE writes a field it never declared")

    def test_no_cited_law_id_of_this_passs_own_op_is_UNDECLARED(self):
        """The UNDECLARED-LAW-ID lesson, third application: declare what you cite. Binds THIS
        pass's own op and its own declarations and claims nothing about anyone else's."""
        rules = _World().views.active_rules()
        d = ops_of(live_pack())["DECLARE-INTAKE"]
        self.assertIn(d["law_cited"], rules, "DECLARE-INTAKE cites an undeclared law")
        for c in d.get("checks") or []:
            if c.get("cite"):
                self.assertIn(c["cite"], rules,
                              "DECLARE-INTAKE's %s check cites an undeclared law" % c["check"])
        for rec in intake_declarations(live_pack(), whole=True):
            self.assertIn(rec["rule_cited"], rules,
                          "an intake declaration cites an undeclared law")

    def test_C6_holds_no_new_check_kind(self):
        """A genuinely new kind is a STOP to the §5 owner gate, never a quiet addition. This
        pass needed none: `require_prior` PARAMETERIZED carries the whole citation rule."""
        d = ops_of(live_pack())["DECLARE-INTAKE"]
        kinds = {c["check"] for c in (d.get("checks") or [])}
        self.assertTrue(kinds, "the new op declares no checks at all, which would leave the "
                               "window citation unenforced")
        self.assertEqual(kinds - set(opdefs.OP_CHECKS), set())
        self.assertEqual(kinds, {"require_prior"})

    def test_the_check_VOCABULARY_ITSELF_is_unchanged_by_this_pass(self):
        # [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14, charter §A57. CAUSE and reasoning identical
        # to `TheVocabularyRateHeld.test_OP_CHECKS_is_unchanged_by_this_pass` above, one pass
        # later: the owner's ruling landed a thirteenth kind. ASSERTED: the live tuple.
        # SUPERSEDED: the era's. REMAINS TRUE: W2b added no check kind — `require_prior`
        # PARAMETERIZED carried its whole citation rule, which is the row's real claim and is a
        # fact about W2b's landing. GIVEN UP: nothing.]
        self.assertEqual(kinds_at(W3A_AFTER_ERA_COMMIT), TheVocabularyRateHeld.PINNED)


class TheGranularityValuesAreDERIVEDAndNotASSERTED(unittest.TestCase):
    """C2's core and the whole defect class ADDENDUM 7 exists to refuse: a measured-law pass
    that ASSERTS its values. Every row here RECOMPUTES the landed value from W2a's cells."""

    def _by_class(self):
        return {d["device_class"]: d for d in intake_declarations(live_pack())}

    def test_every_derived_value_carries_its_CELL_POPULATION_BASIS_and_DERIVATION(self):
        """'A granularity value with no W2a cell behind it REDS' — made checkable as a MISSING
        KEY rather than as a missing sentence, which is §A51's refusal form."""
        for d in intake_declarations(live_pack()):
            self.assertTrue(d["derived_values"], d["intake"])
            for name in d["derived_values"]:
                v = d[name]
                for key in ("value", "cell", "population", "basis", "why_this_value"):
                    self.assertIn(key, v, "%s.%s declares no %s" % (d["intake"], name, key))
                self.assertTrue(v["population"], "%s.%s names no population" % (d["intake"], name))
                self.assertTrue(v["basis"], "%s.%s names no basis" % (d["intake"], name))
                if v["value"] is None:
                    self.assertIn("NOT ESTABLISHED", v["basis"],
                                  "%s.%s carries no value and does not say it is "
                                  "unestablished" % (d["intake"], name))
                else:
                    self.assertTrue(v["cell"], "%s.%s stands on no calibration cell"
                                    % (d["intake"], name))

    def test_derived_values_CANNOT_SHRINK_its_own_audited_population(self):
        """The escape this row shuts: a declaration that adds a measured value and leaves it
        off `derived_values` would be audited by the row above over a set it chose itself.
        Every parameter carrying a `value` key must be ON the list."""
        for d in intake_declarations(live_pack()):
            looks_derived = {k for k, v in d.items()
                             if isinstance(v, dict) and "value" in v}
            self.assertEqual(looks_derived - set(d["derived_values"]), set(),
                             "%s carries a measured value that is not on derived_values"
                             % d["intake"])
            self.assertEqual(set(d["derived_values"]) - looks_derived, set(),
                             "%s lists a derived value it does not carry" % d["intake"])

    def test_the_BLOCK_cap_is_RECOMPUTED_from_W2as_own_cells(self):
        self.assertEqual(self._by_class()["block"]["max_arrivals"]["value"],
                         cap_from_cells(W2A_BLOCK_CELLS))

    def test_the_NET_cap_is_RECOMPUTED_from_W2as_own_cells(self):
        """[DOCUMENTED FLIP — EP-29 W3a, 2026-08-13, §A57 BY FALSIFICATION.
        CAUSE: W3a WITHDREW this value. W2c's two further runs measured the net count
        column at max/min 1.3927 across three runs, which refutes for this class the very
        property `cap_from_cells` leans on, so the value left enforceable law.
        ASSERTED: the LIVE net threshold equals the one-run derivation.
        SUPERSEDED: the net threshold AT `W3A_BEFORE_COMMIT` equals it.
        REMAINS TRUE: what this row was written to say — that W2b DERIVED its net value
        from W2a's cells rather than asserting it. That is a fact about W2b's landing and
        it is unchanged by the value being withdrawn afterwards.
        GIVEN UP: this row no longer says anything about the CURRENT law's net threshold.
        Nothing is lost: `TheNetThresholdIsWithdrawnLawfully` asserts the current state, and
        one row cannot describe two eras.]"""
        era = {d["device_class"]: d
               for d in intake_declarations(pack_at(W3A_BEFORE_COMMIT))}
        self.assertEqual(era["net"]["max_arrivals"]["value"],
                         cap_from_cells(W2A_NET_CELLS))

    def test_the_BLOCK_cap_is_a_WHOLE_NUMBER_of_admitted_acts(self):
        """So the cap never falls inside one governed act: 6144 = 2048 x 3."""
        by = self._by_class()
        unit, _why = unit_from_cells(W2A_BLOCK_CELLS)
        self.assertEqual(by["block"]["max_arrivals"]["value"] % unit, 0)

    def test_the_two_caps_DIFFER_because_the_classes_DO(self):
        """Constraint 3's positive form: a single granularity value spanning device classes
        would be fitted to two behaviours, and here the two derivations return two numbers."""
        by = self._by_class()
        self.assertNotEqual(by["block"]["max_arrivals"]["value"],
                            by["net"]["max_arrivals"]["value"])
        self.assertNotEqual(cap_from_cells(W2A_BLOCK_CELLS), cap_from_cells(W2A_NET_CELLS))

    def test_the_BLOCK_per_act_unit_is_the_DELIVERED_ratio(self):
        value, _why = unit_from_cells(W2A_BLOCK_CELLS)
        self.assertEqual(self._by_class()["block"]["arrivals_per_admitted_act"]["value"], value)
        self.assertEqual(value, 3)

    def test_a_REQUESTED_basis_would_have_given_a_DIFFERENT_number(self):
        """Constraint 2, exhibited rather than promised. Re-deriving the block unit off the
        REQUESTED loads instead of the delivered ones does not merely give a worse answer, it
        gives NO single answer at all — because virtio2's command asked for 256 and the 366
        KiB device delivered 92. A pass that took the command's own number would have had to
        pick one of several ratios and would have had no way to see it was picking."""
        requested = tuple((dev, lvl, W2A_REQUESTED[(dev, lvl)], reps)
                          for dev, lvl, _delivered, reps in W2A_BLOCK_CELLS)
        on_delivered, _ = unit_from_cells(W2A_BLOCK_CELLS)
        on_requested, why = unit_from_cells(requested)
        self.assertEqual(on_delivered, 3)
        self.assertIsNone(on_requested,
                          "the requested basis returned a single ratio, so this row's whole "
                          "ground has moved and constraint 2 must be re-derived")
        self.assertIn("not exact", why)

    def test_the_NET_per_act_unit_is_declared_UNESTABLISHED_rather_than_divided_out(self):
        """Constraint 2 REFUSING a value rather than shaping one. The number a careless pass
        would have written is 3518 / 1600; the number this law carries is None with a reason."""
        v = self._by_class()["net"]["arrivals_per_admitted_act"]
        derived, why = unit_from_cells(W2A_NET_CELLS)
        self.assertIsNone(derived)
        self.assertIn("no delivered figure", why)
        self.assertIsNone(v["value"])
        self.assertIn("NOT ESTABLISHED", v["basis"])
        self.assertIn("delivered_known", v["basis"])

    def test_the_COUNT_and_RATE_columns_give_DIFFERENT_answers_so_the_choice_MATTERS(self):
        """Constraint 1's non-vacuity. If both columns produced the same value the bar would
        be a sentence with a colon in it; they do not, and the caps carried are the count
        column's.

        [DOCUMENTED FLIP — EP-29 W3a, 2026-08-13, §A57 BY FALSIFICATION. CAUSE and reasoning
        exactly as on `test_the_NET_cap_is_RECOMPUTED_from_W2as_own_cells` above.
        ASSERTED: the LIVE net cap came from the count column. SUPERSEDED: THE NET HALF ONLY
        is read at `W3A_BEFORE_COMMIT`; the BLOCK half still reads the live law, because
        block's cap is untouched and confirmed. REMAINS TRUE: both halves, each about its own
        era. GIVEN UP: nothing this row was asked to carry.]"""
        by = self._by_class()
        era = {d["device_class"]: d
               for d in intake_declarations(pack_at(W3A_BEFORE_COMMIT))}
        self.assertNotEqual(cap_from_cells(W2A_BLOCK_CELLS), max(W2A_BLOCK_RATES))
        self.assertNotEqual(cap_from_cells(W2A_NET_CELLS), max(W2A_NET_RATES))
        self.assertEqual(by["block"]["max_arrivals"]["value"], cap_from_cells(W2A_BLOCK_CELLS))
        self.assertEqual(era["net"]["max_arrivals"]["value"], cap_from_cells(W2A_NET_CELLS))

    def test_the_derivations_are_not_CONSTANT_FUNCTIONS(self):
        """The negative-result test on the instrument itself: a derivation that returns the
        same number whatever the table is not a derivation, and every row above rests on
        these two functions."""
        moved = tuple((dev, lvl, delivered, tuple(r + 1 for r in reps))
                      for dev, lvl, delivered, reps in W2A_BLOCK_CELLS)
        self.assertNotEqual(cap_from_cells(moved), cap_from_cells(W2A_BLOCK_CELLS))
        self.assertNotEqual(unit_from_cells(moved)[0], unit_from_cells(W2A_BLOCK_CELLS)[0])


class TheIntakeLawIsLIVEAtTheGate(unittest.TestCase):
    """C2 driven rather than read: the declarations are IN THE RECORD of a booted world, the
    citation check bites, and the act class this pass deliberately did not define still
    refuses.

    ITEM-21 NON-VACUITY: the two founding declarations are proven present in the record
    before any refusal below is read. A refusal in a world holding no declarations is the
    empty world passing, and it reads identically on the page."""

    def setUp(self):
        self.w = _World()
        self.landed = [dict(e["payload"])["intake"] for e in self.w.store.all()
                       if e["action"] == "DECLARE-INTAKE"]
        self.assertEqual(sorted(self.landed), sorted(THE_DECLARED_INTAKES),
                         "the founding's own intake declarations are not in the record, so "
                         "everything below is the empty world")

    def _params(self, **over):
        p = dict(intake="device-intake@probe", device_class="block",
                 window="device-io@block", grade="window",
                 max_arrivals={"value": 6144, "cell": "c", "population": "p", "basis": "b",
                               "why_this_value": "d"},
                 arrivals_per_admitted_act={"value": 3, "cell": "c", "population": "p",
                                            "basis": "b", "why_this_value": "d"},
                 derived_values=["max_arrivals", "arrivals_per_admitted_act"],
                 closers=["max_arrivals x", "unbind y"], records=["count"],
                 does_not_declare=["the ENGINE", "STREAM content", "other populations"],
                 limits=[{"limit": "l", "population": "p", "basis": "b"}], established="e")
        p.update(over)
        return p

    def test_the_founding_declarations_DERIVE_their_objects_from_the_intake_name(self):
        objs = sorted(e["object"] for e in self.w.store.all()
                      if e["action"] == "DECLARE-INTAKE")
        self.assertEqual(objs, ["intake:device-intake@block", "intake:device-intake@net"])

    def test_a_DECLARED_window_ADMITS_an_intake_and_the_record_cites_the_law(self):
        rec = self.w.call("DECLARE-INTAKE", **self._params())
        self.assertEqual(rec["action"], "DECLARE-INTAKE")
        self.assertFalse(rec.get("refused"))
        self.assertEqual(rec["rule_cited"], "DEV-LAW-INTAKE")
        self.assertEqual(dict(rec["payload"])["window"], "device-io@block")

    def test_an_UNDECLARED_window_NAME_refuses_and_is_RECORDED(self):
        before = len(list(self.w.store.all()))
        with self.assertRaises(OpError) as ctx:
            self.w.call("DECLARE-INTAKE", **self._params(window="device-io@nowhere"))
        appended = list(self.w.store.all())[before:]
        self.assertEqual(ctx.exception.rule, "DEV-LAW-INTAKE")
        self.assertEqual(len(appended), 1, "the refusal must be RECORDED, not merely raised")
        self.assertTrue(appended[0]["refused"])

    def test_a_LAW_ID_may_not_pass_as_a_window(self):
        """THE BORROWED-NAME BRANCH, SHUT BY CONSTRUCTION AND DRIVEN, exactly as W1b shut it
        one layer out: the citation is keyed on the DECLARE-IO-WINDOW ACTION and not on rule
        ids, so no law in the founding answers for a window."""
        for borrowed in ("DEV-LAW-INTAKE", "DEV-LAW-BIND", "CAP-IS-LAW", "BOOT-INT"):
            with self.assertRaises(OpError) as ctx:
                self.w.call("DECLARE-INTAKE", **self._params(window=borrowed))
            self.assertEqual(ctx.exception.rule, "DEV-LAW-INTAKE", borrowed)

    def test_the_INTAKE_ENGINE_is_NOT_built_here_and_its_act_class_STILL_refuses(self):
        """The W2b/W3 fence, in the record rather than in a sentence. Recording at the
        declared grade through the gate is the shim's contract; this pass declared the GRADE.
        An act class no declaration founds does not exist, and it refuses citing the
        tip-level terminal rule."""
        with self.assertRaises(OpError) as ctx:
            self.w.call(UNBUILT_INTAKE_ACT, device="virtio1",
                        intake="device-intake@block", arrivals=6144)
        self.assertEqual(ctx.exception.rule, "P3-CLOSURE")

    def test_this_pass_appended_NO_product_record(self):
        """ADDENDUM 7's not-claimed block: no product record lands at W2b. The only records
        this pass adds to a booted world are LAW — one rule, one op definition, two
        declarations — and they arrive through the founding rather than through traffic."""
        added = [e for e in self.w.store.all()
                 if e["action"] in ("DECLARE-INTAKE", "CREATE-OP", "CREATE-RULE")]
        self.assertTrue(added)
        for e in self.w.store.all():
            self.assertNotEqual(e["action"], UNBUILT_INTAKE_ACT)


class TheFoundingMovedAtW2b(unittest.TestCase):
    """C3 — the founding MOVES lawfully and BYTE-UNCHANGED IS THE FAILING OUTCOME.

    ADDENDUM 6 C4's empty-ground exception rides unchanged and is a CAP rather than a branch:
    where W2a's table is EMPTY, W2b never lawfully runs and the path is C0's STOP-AND-REPORT.
    W2a's table is NOT empty — 27 windows, 18 loaded — so this red world is reached."""

    def test_the_pack_version_moved_one_MINOR_from_W2bs_own_BEFORE(self):
        """[DOCUMENTED FLIP — EP-29 W3a, 2026-08-13, §A57 BY FALSIFICATION. CAUSE: W3a moved
        the founding 1.22.0 -> 1.23.0. ASSERTED: W2b's AFTER version read off the LIVE tree.
        SUPERSEDED: read off the pack at `W3A_BEFORE_COMMIT`, which is W2b's close state.
        REMAINS TRUE: W2b moved the version by exactly one MINOR, and both ends of that
        assertion are now inside W2b's own era. GIVEN UP: nothing — this row is the canonical
        §A57 case, and W2b's own worklist named it first.]"""
        self.assertEqual(pack_at(W2B_BEFORE_COMMIT)["founding_version"], W2B_BEFORE_VERSION)
        self.assertEqual(pack_at(W3A_BEFORE_COMMIT)["founding_version"], W2B_AFTER_VERSION)

    def test_the_founding_is_NOT_byte_unchanged(self):
        era = era_pin.blob_at(W2B_BEFORE_COMMIT, era_pin.PACK_PATH)
        with open(PACK_PATH, "rb") as fh:
            live = fh.read()
        self.assertNotEqual(hashlib.sha256(era).hexdigest(),
                            hashlib.sha256(live).hexdigest(),
                            "the founding is byte-unchanged after a LANDED W2b")

    def test_the_designation_record_carries_the_NEW_version(self):
        """[DOCUMENTED FLIP — EP-29 W3a, 2026-08-13, §A57 BY FALSIFICATION. CAUSE: W3a moved
        the founding, so the LIVE world's designation now stamps 1.23.0. ASSERTED: a world
        booted from the live pack. SUPERSEDED: a world booted from the pack at
        `W3A_BEFORE_COMMIT` — the ONE loader handed a different source, which is this file's
        own `_World(pack=...)` idiom and not a second boot path. REMAINS TRUE: W2b's landing
        stamped its own version into the designation record, driven through a real boot.
        GIVEN UP: nothing.]"""
        fs = [e for e in _World(pack=pack_at(W3A_BEFORE_COMMIT)).store.all()
              if e["action"] == "FOUND-STORE"][0]
        self.assertEqual(dict(fs["payload"])["founding_version"], W2B_AFTER_VERSION)

    def test_THE_RULED_VERSION_TEST_the_1_21_0_pack_byte_unchanged_STILL_LOADS(self):
        """THE RULED TEST, BUILDER-EXECUTED: loads -> MINOR; does not -> MAJOR -> STOP TO THE
        MENTOR. It answered MINOR and MAJOR was never reached. Kept as a standing row so a
        later reader can re-check the answer rather than take it."""
        install_module._validate(install_module.records(pack_at(W2B_BEFORE_COMMIT)))

    def test_THE_RULED_VERSION_TEST_the_GENESIS_RULE_RECORDS_load_under_the_new_law(self):
        """The second arm, at the population the dispatch names: the founding's own genesis
        CREATE-RULE records. FORTY-TWO before this pass, forty-three after — counted from the
        artifact in both eras rather than carried, which is the whole of §A51's second half.

        [DOCUMENTED FLIP — EP-30-C3R, 2026-08-21, charter §A57 BY FALSIFICATION, a RANGE
        CLOSURE. CAUSE: RANGE. SUBJECT-ERA: HISTORICAL for the census.
        CAUSE, DRIVEN: EP-30-C3 declared FS-LAW-CUSTODY-TRANSFER, taking the live CREATE-RULE
        census to 44 against this row's open AFTER end.
        ASSERTED: `live_pack()` as W2b's AFTER. SUPERSEDED: `pack_at(W3A_AFTER_ERA_COMMIT)`,
        the era through which W2b's statement was true — the same pin this class's op twin and
        its law twin both now carry, so all three of W2b's census rows finally close at one era
        instead of at three different ones.
        REMAINS TRUE, both literals unchanged: 42 genesis rule records before W2b, 43 after.
        AND THE ROW SHARPENS TOWARD ITS OWN TITLE: `_validate` is the LIVE installer, so
        validating the ERA's records through it is era DATA under TODAY's law — which is what
        THE RULED VERSION TEST names, and what a live-pack validation was never testing.
        GIVEN UP: nothing. The registry bridge below stays LIVE on purpose — `_World()` with no
        pack — so the row still asserts that every genesis rule of W2b's era reaches TODAY's
        active registry, a claim that can still fail the day a pass retires a rule.
        NAMED ON W2b's OWN `NEXT_MOVE_FALSIFIES` WORKLIST as owed this pin.]"""
        era = [r for r in install_module.records(pack_at(W2B_BEFORE_COMMIT))
               if r.get("action") == "CREATE-RULE"]
        now = [r for r in install_module.records(pack_at(W3A_AFTER_ERA_COMMIT))
               if r.get("action") == "CREATE-RULE"]
        self.assertEqual(len(era), 42)
        self.assertEqual(len(now), 43, "this pass declares exactly one new law")
        install_module._validate(install_module.records(pack_at(W3A_AFTER_ERA_COMMIT)))
        active = _World().views.active_rules()
        for r in now:
            self.assertIn(r["payload"]["rule_id"], active,
                          "a genesis rule record does not reach the live registry")

    def test_the_loader_that_accepted_them_CAN_REFUSE(self):
        """Without this the two rows above are an instrument that cannot report its own
        failure. The plant lands on THIS pass's own new definition rather than on an
        inherited one, so the negative control exercises the record the pass authored."""
        p = copy.deepcopy(live_pack())
        planted = 0
        for st in p["steps"]:
            for r in st["records"]:
                if (r.get("payload") or {}).get("name") == "DECLARE-INTAKE":
                    r["payload"]["definition"]["checks"] = [
                        {"check": "planted_unknown_kind", "cite": "DEV-LAW-INTAKE"}]
                    planted += 1
        self.assertEqual(planted, 1)
        with self.assertRaises(Exception) as ctx:
            install_module._validate(install_module.records(p))
        self.assertIn("planted_unknown_kind", str(ctx.exception))

    def test_the_new_op_is_EXACTLY_the_one_this_pass_added(self):
        # [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14, charter §A57. CAUSE: this pass minted
        # DEVICE-INTAKE-COVER, so the LIVE op set is no longer W2b's AFTER and the difference
        # read two operations where W2b added one. ASSERTED: `live_pack()` as W2b's AFTER.
        # SUPERSEDED: `pack_at(W3A_AFTER_ERA_COMMIT)`, the era through which W2b's statement was
        # true. REMAINS TRUE: W2b added EXACTLY ONE operation and removed none, which is a fact
        # about two commits and was never a fact about today's tree. GIVEN UP: nothing — the
        # LIVE op set is asserted by this pass's own census row, which names its one addition.]
        before = set(ops_of(pack_at(W2B_BEFORE_COMMIT)))
        now = set(ops_of(pack_at(W3A_AFTER_ERA_COMMIT)))
        self.assertEqual(sorted(now - before), ["DECLARE-INTAKE"])
        self.assertEqual(before - now, set(), "this pass removed an op")

    def test_the_new_LAW_is_EXACTLY_the_one_this_pass_declared(self):
        """[DOCUMENTED FLIP — EP-30-C3R, 2026-08-21, charter §A57 BY FALSIFICATION, a RANGE
        CLOSURE and not a meaning change. CAUSE: RANGE. SUBJECT-ERA: HISTORICAL — what W2b
        DECLARED is finished and cannot move again.
        CAUSE, DRIVEN: EP-30-C3 declared FS-LAW-CUSTODY-TRANSFER, so the difference this row
        computes read two laws where W2b declared one.
        ASSERTED: `live_pack()` as W2b's AFTER — an open range wearing a closed range's
        clothes, which is this file's own phrase for the trap and is diagnosed at length three
        classes down.
        SUPERSEDED: `pack_at(W3A_AFTER_ERA_COMMIT)`, the era through which W2b's statement was
        true — EXACTLY the pin its OP TWIN `test_the_new_op_is_EXACTLY_the_one_this_pass_added`
        took at W3a3, for the identical reason, four lines above this one.
        WHY THE TWIN WAS CLOSED THEN AND THIS ROW WAS NOT, because it is the finding and not an
        excuse: W3a3 minted an OPERATION and declared no law, so only the op half of the pair
        reddened and only the op half was repaired. A PAIR SPLIT BY WHICH HALF THE NEXT PASS
        HAPPENED TO MOVE — the law half sat open for three founding moves and cost nothing
        until a pass declared a law, which is C3. An open range is not found by the pass that
        opens it; it is found by the first pass unlucky enough to cross it.
        REMAINS TRUE, carrying its own literal unchanged: W2b declared exactly ONE law,
        DEV-LAW-INTAKE, and retired none.
        GIVEN UP: nothing — no claim about today's law set was ever this row's subject, and
        W2b's own `NEXT_MOVE_FALSIFIES` worklist named this row as owed this pin.]"""
        before = set(rules_of(pack_at(W2B_BEFORE_COMMIT)))
        now = set(rules_of(pack_at(W3A_AFTER_ERA_COMMIT)))
        self.assertEqual(sorted(now - before), ["DEV-LAW-INTAKE"])
        self.assertEqual(before - now, set(), "this pass retired a law")

    def test_the_ENGINE_moved_ZERO_lines_which_is_what_makes_MINOR_mean_what_it_says(self):
        """The two `src/` members of the fence's enumeration OTHER than the pack were inside
        this pass's reach and did not need to be touched. Asserted against the ERA's bytes
        rather than against `git diff`, because a working-tree diff empties out the moment
        the two-minute autosync commits and would then pass whatever had been written.

        [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14, charter §A57. CAUSE: a check kind IS engine
        vocabulary, so this pass's licensed landing moved `src/kernel/opdefs.py` — the first
        movement of this stage family whose landing is NOT pure law-data. ASSERTED: the era's
        engine bytes against the LIVE tree's. SUPERSEDED: against `W3A_AFTER_ERA_COMMIT`'s, the
        era through which W2b's statement was true. REMAINS TRUE, unchanged and re-checkable:
        W2b moved zero engine lines, which is what made its MINOR mean what it said. GIVEN UP:
        nothing — that the LIVE engine moved in exactly one file, and which one, is asserted by
        `TheFoundingMovedAtW3a3.test_the_ENGINE_moved_in_ONE_FILE_and_the_move_is_the_thirteenth_
        kind`, which is where this pass's own era belongs.]"""
        for path in ("src/kernel/opdefs.py", "src/subsystems/devices.py",
                     "src/founding/install.py"):
            era = era_pin.blob_at(W2B_BEFORE_COMMIT, path)
            after = era_pin.blob_at(W3A_AFTER_ERA_COMMIT, path)
            self.assertEqual(hashlib.sha256(era).hexdigest(),
                             hashlib.sha256(after).hexdigest(),
                             "%s moved in a pass whose landing is pure law-data" % path)


class TheW2bSweep(unittest.TestCase):
    """§A57 BY FALSIFICATION, with the method IMPORTED from `tests/era_pin.py`.

    THE POPULATION IS BY FALSIFICATION AND NOT BY ADJACENCY (the clause's own 2026-08-09
    repair), and the previous pass's finding is inherited as a FLOOR rather than as a bound:
    W1b's handed-forward worklist named four and the true population was twelve across six
    files. The list below is what a full suite run at both widths actually reddened."""

    #: (file, dotted row, what THIS pass's move falsified). Verified to resolve below.
    #: TEN FALSIFICATION REDS ACROSS TWO FILES, taken from a full suite arm and not from a
    #: worklist. Five further reds in the same arm were ATTESTATION reds — the J9 rows saying
    #: "the founding on disk is unattested" — and they are NOT flips: no edit to any row fixes
    #: them, and writing this pass's BUILD-PROGRESS entry naming 1.22.0 with the pack's own
    #: sha256 does. The two kinds look identical in a suite tail and route to different doors.
    SWEPT = (
        ("tests/test_ep28zd.py", "TheThreeSetDiffsClose."
                                 "test_diff_2_every_field_the_42_CARRY_is_DECLARED_somewhere",
         "42 CREATE-RULE records -> 43"),
        ("tests/test_ep28zd.py", "TheSevenAndTheSixAreNamedSets."
                                 "test_the_SIX_carry_the_counts_the_establishment_took",
         "text: 42 -> 43"),
        ("tests/test_ep28zd.py", "TheTierClaimBecameVisible."
                                 "test_the_LIVE_era_REFUSES_the_claim_and_RECORDS_the_refusal",
         "1.21.0 -> 1.22.0"),
        ("tests/test_ep28zd.py", "DeclaringScopeOpensNoNewReach."
         "test_the_LIVE_era_reaches_the_SAME_space_and_now_records_the_spelling",
         "1.21.0 -> 1.22.0"),
        ("tests/test_ep28zd.py", "TheUnchangedBehavioursAreMEASURED."
                                 "test_the_op_SET_did_not_move_this_pass", "74 ops -> 75"),
        ("tests/test_ep28zd.py", "TheFoundingMoved.test_the_version_moved_exactly_one_MINOR",
         "1.21.0 -> 1.22.0"),
        ("tests/test_ep28zd.py", "TheFoundingMoved."
                                 "test_the_designation_record_carries_the_NEW_version",
         "1.21.0 -> 1.22.0"),
        ("tests/test_ep28zd.py", "TheFoundingMoved.test_the_step_count_did_not_move",
         "25 steps -> 27"),
        ("tests/test_ep28zd.py", "TheVersionQuestionWasEXECUTEDAndTookMINOR."
         "test_ARM_2_the_42_GENESIS_RECORDS_LOAD_UNDER_THE_AMENDED_DECLARATION",
         "42 CREATE-RULE records -> 43"),
        ("tests/test_ep29.py", "TheFoundingMovedAgainAtStage2."
                               "test_the_new_ops_are_EXACTLY_the_two_this_pass_added",
         "a third op joins the live set"),
    )

    #: THE FIVE ATTESTATION REDS from the same arm, named so the two kinds are not conflated
    #: by a later reader counting "fifteen reds" and looking for fifteen flips.
    ATTESTATION_REDS = (
        "tests/test_ep28i.py::TestTheVersionMoves."
        "test_the_J9_instrument_is_live_and_binds_whatever_pack_ships",
        "tests/test_ep28k.py::TestTheVersionMoves."
        "test_J9_the_same_version_may_not_name_two_distinct_foundings",
        "tests/test_ep28n.py::TestTheVersionMoves."
        "test_J9_the_same_version_may_not_name_two_distinct_foundings",
        "tests/test_ep28n2.py::TestTheVersionMoves."
        "test_J9_the_same_version_may_not_name_two_distinct_foundings",
        "tests/test_founding_is_logged.py::TestTheFoundingOnDiskIsNamedInTheLog."
        "test_the_founding_version_and_pack_hash_are_named_together_in_one_entry",
    )

    def test_the_two_kinds_of_red_are_COUNTED_SEPARATELY(self):
        """A suite tail shows one number. These route to different doors: a flip is an edit to
        a row, an attestation red is discharged by writing the entry. Ten and five."""
        self.assertEqual(len(self.SWEPT), 10)
        self.assertEqual(len(self.ATTESTATION_REDS), 5)
        self.assertEqual(len({p for p, _c, _w in self.SWEPT}), 2,
                         "the flip population spans two files")

    def test_the_ATTESTATION_reds_name_real_files(self):
        for dotted in self.ATTESTATION_REDS:
            self.assertTrue(os.path.exists(os.path.join(REPO, dotted.split("::")[0])), dotted)

    def test_the_ERA_THIS_PASS_PLANTED_into_the_swept_file_is_the_ONE_IT_VERIFIED(self):
        """§A57's fence permits no NEW row in a swept file, so the constant this pass wrote
        into `tests/test_ep28zd.py` is checked HERE — against the same commit and the same
        digest this file pins. Without it the planted pin would be verified by a comment."""
        import test_ep28zd
        self.assertEqual(test_ep28zd.AFTER_COMMIT, W2B_BEFORE_COMMIT,
                         "the era planted into the swept file is not the era verified here")
        self.assertEqual(test_ep28zd.AFTER_PACK_SHA, W2B_BEFORE_PACK_SHA)
        self.assertEqual(
            hashlib.sha256(era_pin.blob_at(test_ep28zd.AFTER_COMMIT,
                                           era_pin.PACK_PATH)).hexdigest(),
            test_ep28zd.AFTER_PACK_SHA)

    #: THE NEXT MOVE'S WORKLIST — the rows that compare a LIVE-tree read against a literal
    #: this pass's era makes true, so the next founding pass falsifies exactly these and owes
    #: them the §A57 era-pin. A FLOOR AND NEVER THE BOUND: this pass can see the live-tree
    #: reads in its own file and cannot see population rows in files only an op-adding pass
    #: falsifies. The bound is a suite run.
    NEXT_MOVE_FALSIFIES = (
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW2b.test_the_pack_version_moved_one_MINOR_from_W2bs_own_BEFORE"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW2b.test_the_designation_record_carries_the_NEW_version"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW2b.test_the_new_op_is_EXACTLY_the_one_this_pass_added"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW2b.test_the_new_LAW_is_EXACTLY_the_one_this_pass_declared"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW2b."
         "test_the_ENGINE_moved_ZERO_lines_which_is_what_makes_MINOR_mean_what_it_says"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW2b."
         "test_THE_RULED_VERSION_TEST_the_GENESIS_RULE_RECORDS_load_under_the_new_law"),
    )

    def test_every_swept_site_names_a_real_file(self):
        for path, _cls, _why in self.SWEPT:
            self.assertTrue(os.path.exists(os.path.join(REPO, path)), path)

    def test_every_swept_class_in_THIS_file_still_exists(self):
        for path, cls, _why in self.SWEPT:
            if path == "tests/test_ep29.py":
                self.assertIsNotNone(globals().get(cls.split(".")[0]),
                                     "no such class: %s" % cls)

    def test_every_row_on_the_next_moves_worklist_EXISTS(self):
        """A worklist naming rows that do not exist is worse than no worklist."""
        self.assertTrue(self.NEXT_MOVE_FALSIFIES)
        for path, dotted in self.NEXT_MOVE_FALSIFIES:
            self.assertTrue(os.path.exists(os.path.join(REPO, path)), path)
            cls_name, meth = dotted.split(".")
            cls = globals().get(cls_name)
            self.assertIsNotNone(cls, "no such class: %s" % cls_name)
            self.assertTrue(hasattr(cls, meth), "no such row: %s" % dotted)

    def test_the_ERA_PIN_METHOD_IS_IMPORTED_AND_NOT_RE_DERIVED(self):
        """C3's other red world: a re-derived era idiom REDS, and the class it reds is the
        eighteen copies EP-28Z retired out of ten files. A PRESENCE test — this file's era
        read and the home's are shown to produce the same bytes — because the absence form
        (grepping this file for a `git show` spawn) is the one that inverted on the pass
        before last, matching an ordinary English word in a docstring."""
        self.assertEqual(pack_at(W2B_BEFORE_COMMIT), era_pin.pack_at(W2B_BEFORE_COMMIT),
                         "this file's era read and the one home's disagree")
        self.assertEqual(os.path.dirname(os.path.abspath(era_pin.__file__)),
                         os.path.join(REPO, "tests"),
                         "era_pin resolved to something other than the estate's one home")

    def test_the_era_pin_is_verified_BY_CONTENT_and_never_by_version_number(self):
        """`era_pin`'s own stated cap: it makes the READ uniform and can say nothing about
        whether a caller's PIN is the right commit. Choosing a pin by version number rather
        than by content is this estate's most expensive known trap, so the pin is checked
        against the sha256 W2a's close recorded for the pack it moved off."""
        blob = era_pin.blob_at(W2B_BEFORE_COMMIT, era_pin.PACK_PATH)
        self.assertEqual(hashlib.sha256(blob).hexdigest(), W2B_BEFORE_PACK_SHA)

    def test_the_era_pin_reports_a_DIFFERENCE_when_there_is_one(self):
        """The instrument's own negative-result test; both rows above rest on it."""
        with open(PACK_PATH, "rb") as fh:
            live = fh.read()
        self.assertNotEqual(hashlib.sha256(era_pin.blob_at(
            W2B_BEFORE_COMMIT, era_pin.PACK_PATH)).hexdigest(),
            hashlib.sha256(live).hexdigest())


class TheW2bRowsCanBeMadeToFail(unittest.TestCase):
    """RED WORLDS FOR THE INTAKE LAW, DRIVEN THROUGH THE REAL ROWS on planted packs.

    Each plants a defect in a COPY of the live pack and runs the ACTUAL row against it, so no
    predicate is restated — a red world that re-implements the assertion it tests proves only
    that two copies agree. CONTROL FIRST: the unmutated copy must PASS every covered row, or
    a red below could be the copy being malformed rather than the clause biting."""

    #: Every W2b row that reads the pack through `live_pack`. Named as DATA so the control
    #: cannot pass by quietly running fewer rows than exist.
    COVERED = (
        (TheIntakeLawLanded,
         ("test_exactly_the_two_intakes_one_per_device_class_are_declared",
          "test_every_intake_declares_WINDOW_grade",
          "test_no_declaration_sets_a_bound_of_ONE",
          "test_every_intake_cites_a_window_that_a_DECLARATION_founds",
          "test_every_intake_states_what_it_does_NOT_declare",
          "test_every_intake_carries_LIMITS_each_with_its_population_and_basis",
          "test_the_closers_are_EVENT_based_and_never_TIME_based",
          "test_the_new_op_declares_an_EXPLICIT_form_for_every_parameter",
          "test_C6_holds_no_new_check_kind")),
        (TheGranularityValuesAreDERIVEDAndNotASSERTED,
         ("test_every_derived_value_carries_its_CELL_POPULATION_BASIS_and_DERIVATION",
          "test_derived_values_CANNOT_SHRINK_its_own_audited_population",
          "test_the_BLOCK_cap_is_RECOMPUTED_from_W2as_own_cells",
          "test_the_NET_cap_is_RECOMPUTED_from_W2as_own_cells",
          "test_the_BLOCK_cap_is_a_WHOLE_NUMBER_of_admitted_acts",
          "test_the_two_caps_DIFFER_because_the_classes_DO",
          "test_the_BLOCK_per_act_unit_is_the_DELIVERED_ratio",
          "test_the_NET_per_act_unit_is_declared_UNESTABLISHED_rather_than_divided_out",
          "test_the_COUNT_and_RATE_columns_give_DIFFERENT_answers_so_the_choice_MATTERS")),
        (TheFoundingMovedAtW2b,
         ("test_the_founding_is_NOT_byte_unchanged",)),
    )

    #: THE ROW THIS FILE ERA-PINNED, SPLIT OUT RATHER THAN DROPPED. [ADDED — EP-29 W3a3,
    #: 2026-08-14, the same consequence TheW3aRowsCanBeMadeToFail's own COVERED_ERA block
    #: states at length: era-pinning moves a row's subject off the live tree, and a red world
    #: planting into a copy of the live pack then reaches nothing while looking healthy. The
    #: coverage is kept and re-aimed at the era read.]
    #: [SECOND MEMBER ADDED — EP-30-C3R, 2026-08-21, and it is THIS CONTROL'S OWN REPAIR.
    #:  EP-30-C3 declared a law, which falsified `test_the_new_LAW_is_EXACTLY_the_one_this_
    #:  pass_declared` and so falsified the control above it — a control over a row is red
    #:  whenever its subject is, and saying so is its whole function. Once that row was
    #:  era-pinned, leaving it in COVERED would have made the control pass it through the
    #:  LIVE-pack harness, WHICH REACHES NOTHING: a green with no plant behind it, which is
    #:  worse than the red it replaced. DRIVEN, NOT ARGUED: with the row pinned and still in
    #:  COVERED, this control PASSED — vacuously — and the drift red world below FAILED
    #:  0 != 1 because its plant no longer reached its subject. The move is what restores
    #:  both. This is the instruction W3a3's own NEXT_MOVE_FALSIFIES block carries forward in
    #:  its own words: WHEN YOU ERA-PIN A ROW, LOOK FOR WHAT PLANTS INTO IT.]
    COVERED_ERA = (
        (TheFoundingMovedAtW2b, ("test_the_new_op_is_EXACTLY_the_one_this_pass_added",
                                 "test_the_new_LAW_is_EXACTLY_the_one_this_pass_declared")),
    )

    def _copy(self):
        return copy.deepcopy(live_pack())

    def _era_copy(self):
        """The plant base for the era-pinned row: a copy of the world that row is ABOUT."""
        return copy.deepcopy(pack_at(W3A_AFTER_ERA_COMMIT))

    def _run_era(self, pack, cls, meth):
        """Run one REAL era-pinned row against `pack` by pointing this file's `pack_at` at it
        FOR THE AFTER-ERA COMMIT ONLY, so the row's BEFORE side still reads the genuine era."""
        global pack_at
        original = pack_at
        pack_at = lambda c: pack if c == W3A_AFTER_ERA_COMMIT else original(c)  # noqa: E731
        try:
            case = cls(meth)
            res = unittest.TestResult()
            case.run(res)
            return res
        finally:
            pack_at = original

    def _run(self, pack, cls, meth):
        """Run one REAL row against `pack` by pointing this file's `live_pack` at it for the
        call. The row's own body is what executes."""
        global live_pack
        original = live_pack
        live_pack = lambda: pack                              # noqa: E731
        try:
            case = cls(meth)
            res = unittest.TestResult()
            case.run(res)
            return res
        finally:
            live_pack = original

    def assertRowFAILED(self, res, why):
        """A RED WORLD MUST RED FOR ITS OWN REASON. `wasSuccessful()` is False for an ERROR
        too, so a planted pack that broke the row would satisfy a bare assertFalse and read
        on the page exactly like the claim biting. The helper is this file's own, taken from
        the two classes above it rather than re-derived — board :411's fifth data point was
        exactly this helper being read and not inherited."""
        self.assertEqual(res.errors, [],
                         "the row ERRORED rather than failed, so the planted pack broke the "
                         "instrument instead of the claim: %r" % (res.errors,))
        self.assertEqual(len(res.failures), 1, why)

    def _intakes(self, pack):
        return [r["payload"] for st in pack["steps"] for r in st["records"]
                if r.get("action") == "DECLARE-INTAKE"]

    def test_the_control_PASSES_every_covered_row(self):
        """CONTROL, FIRST. Without it every red below is uninterpretable.

        [EXTENDED — EP-29 W3a3, 2026-08-14: the control now runs BOTH populations, each through
        the reader its own rows use, for the reason TheW3aRowsCanBeMadeToFail's control states
        at length — an era-pinned row run through the live-pack harness passes because the
        harness never reaches it.]"""
        pack, era = self._copy(), self._era_copy()
        ran = 0
        for cls, meths in self.COVERED:
            for meth in meths:
                res = self._run(pack, cls, meth)
                self.assertTrue(res.wasSuccessful(),
                                "the unmutated copy FAILS %s.%s, so every red world below is "
                                "uninterpretable: %r"
                                % (cls.__name__, meth, res.failures + res.errors))
                ran += 1
        for cls, meths in self.COVERED_ERA:
            for meth in meths:
                res = self._run_era(era, cls, meth)
                self.assertTrue(res.wasSuccessful(),
                                "the unmutated ERA copy FAILS %s.%s, so the era red world "
                                "below is uninterpretable: %r"
                                % (cls.__name__, meth, res.failures + res.errors))
                ran += 1
        self.assertEqual(ran, sum(len(m) for _c, m in self.COVERED + self.COVERED_ERA))
        self.assertGreater(ran, 15, "non-vacuity: the control is not a stub")

    def test_the_ERA_HARNESS_ITSELF_can_reach_the_row_it_claims_to_plant_into(self):
        """THE CONTROL'S OWN CONTROL. `_run_era` is shown to CHANGE the era-pinned row's
        verdict, so the green above means the harness reached the row rather than missed it."""
        cls, meth = TheFoundingMovedAtW2b, "test_the_new_op_is_EXACTLY_the_one_this_pass_added"
        self.assertTrue(self._run_era(self._era_copy(), cls, meth).wasSuccessful(),
                        "the true era fails its own row, so the failure below says nothing")
        planted = self._era_copy()
        for st in planted["steps"]:
            if st["step"] == "08k-device-intake-ops":
                st["records"] = []
        self.assertRowFAILED(self._run_era(planted, cls, meth),
                             "the era harness cannot move the row's verdict, so the era red "
                             "world below plants into a pack the row never reads")

    def test_a_granularity_value_with_NO_W2a_CELL_behind_it_REDS(self):
        """C2's headline red world: a measured-law pass ASSERTING its values is the whole
        defect class ADDENDUM 7 exists to refuse."""
        pack = self._copy()
        for d in self._intakes(pack):
            d["max_arrivals"].pop("cell")
        self.assertRowFAILED(
            self._run(pack, TheGranularityValuesAreDERIVEDAndNotASSERTED,
                      "test_every_derived_value_carries_its_CELL_POPULATION_BASIS_and_DERIVATION"),
            "a granularity value standing on no calibration cell passes")

    def test_a_value_whose_CELL_NAMES_NO_POPULATION_REDS(self):
        pack = self._copy()
        for d in self._intakes(pack):
            d["max_arrivals"]["population"] = ""
        self.assertRowFAILED(
            self._run(pack, TheGranularityValuesAreDERIVEDAndNotASSERTED,
                      "test_every_derived_value_carries_its_CELL_POPULATION_BASIS_and_DERIVATION"),
            "a value naming no population passes — §A51's refusal form does not bite")

    def test_a_law_value_derived_from_the_RATE_COLUMN_REDS(self):
        """:683's first constraint, driven against a REAL rate figure rather than an invented
        one: 81719 is virtio1 L2's own measured arrival rate, and it is exactly the number a
        pass reading one column to the right would have carried."""
        pack = self._copy()
        for d in self._intakes(pack):
            if d["device_class"] == "block":
                d["max_arrivals"]["value"] = max(W2A_BLOCK_RATES)
        self.assertRowFAILED(
            self._run(pack, TheGranularityValuesAreDERIVEDAndNotASSERTED,
                      "test_the_BLOCK_cap_is_RECOMPUTED_from_W2as_own_cells"),
            "a cap taken from the rate column passes the recomputation")

    def test_a_value_standing_on_a_REQUESTED_number_REDS(self):
        """:683's second constraint. The planted value is 3518 / 1600 — the net cap over the
        DATAGRAMS THE COMMAND ASKED FOR — which is precisely the number a pass would write if
        it took `delivered_known: false` for a formality."""
        pack = self._copy()
        for d in self._intakes(pack):
            if d["device_class"] == "net":
                d["arrivals_per_admitted_act"]["value"] = 3518 / W2A_REQUESTED[("virtio0", "L2")]
        self.assertRowFAILED(
            self._run(pack, TheGranularityValuesAreDERIVEDAndNotASSERTED,
                      "test_the_NET_per_act_unit_is_declared_UNESTABLISHED_rather_than_divided_out"),
            "a per-act unit divided out of a requested load passes")

    def test_a_SINGLE_granularity_value_SPANNING_device_classes_REDS(self):
        """:683's third constraint: one value fitted to two behaviours."""
        pack = self._copy()
        block = [d for d in self._intakes(pack) if d["device_class"] == "block"][0]
        for d in self._intakes(pack):
            d["max_arrivals"]["value"] = block["max_arrivals"]["value"]
        self.assertRowFAILED(
            self._run(pack, TheGranularityValuesAreDERIVEDAndNotASSERTED,
                      "test_the_two_caps_DIFFER_because_the_classes_DO"),
            "one cap across both device classes passes")

    def test_a_derived_value_LEFT_OFF_the_audited_list_REDS(self):
        """The population-shrinking escape: add a measured value, omit it from
        `derived_values`, and the completeness row would audit a set the declaration chose."""
        pack = self._copy()
        for d in self._intakes(pack):
            d["arrivals_per_window_smuggled"] = {"value": 1}
        self.assertRowFAILED(
            self._run(pack, TheGranularityValuesAreDERIVEDAndNotASSERTED,
                      "test_derived_values_CANNOT_SHRINK_its_own_audited_population"),
            "a measured value off the audited list passes")

    def test_PER_INTERRUPT_GRADE_APPEARING_IN_THE_DECLARATION_REDS(self):
        """C2's other headline red world, planted where it would actually appear — in the
        GRADE — rather than hunted for in prose."""
        pack = self._copy()
        for d in self._intakes(pack):
            d["grade"] = "per-interrupt"
        self.assertRowFAILED(
            self._run(pack, TheIntakeLawLanded, "test_every_intake_declares_WINDOW_grade"),
            "a per-interrupt grade passes")

    def test_a_BOUND_OF_ONE_REDS(self):
        """The per-interrupt grade wearing a window's name. DEV-LAW-INTAKE forbids it in its
        own text and this row is what makes the sentence cost something."""
        pack = self._copy()
        for d in self._intakes(pack):
            d["max_arrivals"]["value"] = 1
        self.assertRowFAILED(
            self._run(pack, TheIntakeLawLanded, "test_no_declaration_sets_a_bound_of_ONE"),
            "a covering record standing for exactly one arrival passes")

    def test_an_intake_over_an_UNDECLARED_WINDOW_REDS(self):
        pack = self._copy()
        for d in self._intakes(pack):
            d["window"] = "device-io@borrowed"
        self.assertRowFAILED(
            self._run(pack, TheIntakeLawLanded,
                      "test_every_intake_cites_a_window_that_a_DECLARATION_founds"),
            "an intake declaring a grade for an admission no window founds passes")

    def test_a_BARE_PARAMETER_FORM_REDS(self):
        """C7: a parameter form taken by silence is not declining the choice, it is taking it
        undecided. The plant is the exact shape J's table found."""
        pack = self._copy()
        for st in pack["steps"]:
            for r in st["records"]:
                if (r.get("payload") or {}).get("name") == "DECLARE-INTAKE":
                    r["payload"]["definition"]["params"]["established"] = None
        self.assertRowFAILED(
            self._run(pack, TheIntakeLawLanded,
                      "test_the_new_op_declares_an_EXPLICIT_form_for_every_parameter"),
            "a bare parameter form passes")

    def test_a_NEW_CHECK_KIND_REDS(self):
        """C6: a genuinely new kind is a STOP to the §5 owner gate, never a quiet addition.
        This row is what makes that a gate rather than a preference."""
        pack = self._copy()
        for st in pack["steps"]:
            for r in st["records"]:
                if (r.get("payload") or {}).get("name") == "DECLARE-INTAKE":
                    r["payload"]["definition"]["checks"] = [
                        {"check": "granularity_bound", "cite": "DEV-LAW-INTAKE"}]
        self.assertRowFAILED(
            self._run(pack, TheIntakeLawLanded, "test_C6_holds_no_new_check_kind"),
            "a new check kind added by a pass rather than by the owner gate passes")

    def test_a_declaration_that_names_NO_LIMIT_REDS(self):
        pack = self._copy()
        for d in self._intakes(pack):
            d["limits"] = []
        self.assertRowFAILED(
            self._run(pack, TheIntakeLawLanded,
                      "test_every_intake_carries_LIMITS_each_with_its_population_and_basis"),
            "a law value generalising from one guest and one boot with no limit passes")

    def test_a_limit_naming_NO_BASIS_REDS(self):
        pack = self._copy()
        for d in self._intakes(pack):
            d["limits"][0]["basis"] = ""
        self.assertRowFAILED(
            self._run(pack, TheIntakeLawLanded,
                      "test_every_intake_carries_LIMITS_each_with_its_population_and_basis"),
            "a limit with no basis passes")

    def test_a_TIME_BASED_CLOSER_REDS(self):
        """A duration would have to come from the rate column constraint 1 bars, and a clock
        that schedules a record is clock-as-scheduler."""
        pack = self._copy()
        for d in self._intakes(pack):
            d["closers"] = ["max_arrivals x", "every_200ms y"]
        self.assertRowFAILED(
            self._run(pack, TheIntakeLawLanded,
                      "test_the_closers_are_EVENT_based_and_never_TIME_based"),
            "a time-based closer passes")

    def test_a_declaration_that_DISCLAIMS_NOTHING_REDS(self):
        pack = self._copy()
        for d in self._intakes(pack):
            d["does_not_declare"] = []
        self.assertRowFAILED(
            self._run(pack, TheIntakeLawLanded,
                      "test_every_intake_states_what_it_does_NOT_declare"),
            "a declaration naming no absence passes, so it reads as covering everything")

    def test_a_declaration_that_does_not_disclaim_the_ENGINE_REDS(self):
        """The W2b/W3 fence: a declaration silent about the engine reads as having landed the
        recording path."""
        pack = self._copy()
        for d in self._intakes(pack):
            d["does_not_declare"] = ["STREAM content", "an actor", "another population"]
        self.assertRowFAILED(
            self._run(pack, TheIntakeLawLanded,
                      "test_every_intake_states_what_it_does_NOT_declare"),
            "a declaration that does not disclaim the intake engine passes")

    def test_ONE_INTAKE_FOR_BOTH_CLASSES_REDS(self):
        pack = self._copy()
        dropped = 0
        for st in pack["steps"]:
            keep = []
            for r in st["records"]:
                if r.get("action") == "DECLARE-INTAKE" and \
                        r["payload"]["device_class"] == "net":
                    dropped += 1
                    continue
                keep.append(r)
            st["records"] = keep
        self.assertEqual(dropped, 1)
        self.assertRowFAILED(
            self._run(pack, TheIntakeLawLanded,
                      "test_exactly_the_two_intakes_one_per_device_class_are_declared"),
            "one intake covering both device classes passes")

    def test_a_BYTE_UNCHANGED_FOUNDING_REDS(self):
        """C3's red world at its own position, driven rather than argued. The planted pack is
        the ERA's own bytes: had this pass landed nothing, this is exactly what the tree would
        hold and exactly what the row must refuse."""
        pack = era_pin.pack_at(W2B_BEFORE_COMMIT)
        original = PACK_PATH
        try:
            globals()["PACK_PATH"] = os.path.join(
                tempfile.mkdtemp(prefix="w2b-era-"), "founding-pack.json")
            with open(globals()["PACK_PATH"], "wb") as fh:
                fh.write(era_pin.blob_at(W2B_BEFORE_COMMIT, era_pin.PACK_PATH))
            self.assertRowFAILED(
                self._run(pack, TheFoundingMovedAtW2b, "test_the_founding_is_NOT_byte_unchanged"),
                "a founding standing byte-unchanged after a LAW PASS passes")
        finally:
            globals()["PACK_PATH"] = original

    def test_a_pass_that_ADDED_A_SECOND_OP_by_drift_REDS(self):
        """The growth guard in the vocabulary dimension: this pass declares one op and an op
        arriving beside it by momentum is visible rather than absorbed."""
        pack = self._era_copy()
        for st in pack["steps"]:
            if st["step"] == "08k-device-intake-ops":
                extra = copy.deepcopy(st["records"][0])
                extra["payload"]["name"] = "DECLARE-INTAKE-DRIFTED"
                extra["payload"]["rule_id"] = "op:DECLARE-INTAKE-DRIFTED"
                st["records"].append(extra)
        self.assertRowFAILED(
            self._run_era(pack, TheFoundingMovedAtW2b,
                          "test_the_new_op_is_EXACTLY_the_one_this_pass_added"),
            "a second op added by drift passes")

    def test_a_pass_that_DECLARED_A_SECOND_LAW_by_drift_REDS(self):
        """[RE-AIMED AT THE ERA READ — EP-30-C3R, 2026-08-21, the identical consequence
        W3a3 recorded when it era-pinned this row's OP TWIN. An era-pin moves a row's subject
        OFF the live tree, so a plant into a copy of the LIVE pack reaches nothing and the row
        it plants into passes — which reads on the page as this red world failing 0 != 1, and
        that is exactly what it did at this hand before this edit. THE COVERAGE IS KEPT AND
        RE-AIMED, never dropped: the plant now lands in a copy of the era the row is ABOUT.]"""
        pack = self._era_copy()
        for st in pack["steps"]:
            if st["step"] == "05g-device-laws":
                extra = copy.deepcopy(st["records"][-1])
                extra["payload"] = dict(extra["payload"], rule_id="DEV-LAW-DRIFTED")
                st["records"].append(extra)
        self.assertRowFAILED(
            self._run_era(pack, TheFoundingMovedAtW2b,
                          "test_the_new_LAW_is_EXACTLY_the_one_this_pass_declared"),
            "a second law declared by drift passes")


# =======================================================================================
# EP-29 W2c — EXHIBIT (ADDENDUM 7 C4, 2026-08-13)
#
# ZERO INTERPOSITION, EXHIBITED RATHER THAN RECITED. With W2b's intake law landed, shadow
# covering records are built FROM OBSERVATION ALONE at the grade that law declares, the
# validation drivers are shown byte-identical across the whole of W2, and the observation
# path is enumerated as surfaces with each one's use.
#
# THIS MOVEMENT MOVES NO FOUNDING BYTE. W2b had to move it and W2c must not — the third
# different founding requirement in four units on this line, which is why it is asserted
# here rather than carried from the habit of the pass before.
#
# WHAT IS NOT CLAIMED, so nothing lands by drift: C9's scaling red — the ratio REQUIRED to
# fall as load rises — is W5's, and ADDENDUM 7's own not-claimed block says W2c does not
# rehearse it. The ratio row below is CONFORMANCE and nothing else: did the records do what
# the landed law says. And the shadow set is EVIDENCE, never record: the intake ENGINE is
# W3's shim contract and no product record is appended by this pass.
# =======================================================================================
import ast                                                       # noqa: E402
import math                                                      # noqa: E402

#: THE ERA THIS PASS PINS AGAINST — the commit before W2a's first write, taken from that
#: pass's own recorded pre-write HEAD. `blob_at` and nothing else reads it (EP-28Z's one
#: home; the mechanism is the blob read, and `rev-list` below is a repository fact and is
#: explicitly NOT the era-pin act, per that file's own near-miss controls).
W2_ERA_COMMIT = "0b2d9c7bc412e67b2680562c47fee748e65b6b5f"

#: W2b's own pre-write commit — the boundary between W2a's close and W2b's open. Used as
#: the era pin's NEGATIVE control: it holds the 1.21.0 pack, so a comparison against it
#: MUST report a difference, and a comparison that cannot report inequality is not one.
W2B_ERA_COMMIT = "3d187e217705bbf5d851c5d5f71cde8d19d6227d"

#: THIS pass's pre-write commit, captured before any write (§A53 — `git checkout --` no
#: longer undoes a write since the 2026-08-03 autosync repair, so the commit is TAKEN and
#: not trusted). The founding-unchanged claim is a comparison between this era and the live
#: tree, deliberately NOT an assertion of a version literal: a literal would join §A57's
#: sweep population at the next founding move and buy nothing this comparison does not.
W2C_PRE_WRITE_COMMIT = "54e8d5f7a79f965095f01d1fda2ed0e3759743e8"

#: The classes the landed law declares an intake for. Read from the pack by ACTION, never
#: hard-coded; this tuple is only the expectation the live reading is compared against.
THE_DECLARED_INTAKE_CLASSES = ("block", "net")

#: THE CENSUS SUBJECTS, handed identically to BOTH censuses so the before/after comparison
#: measures the path and not the argument list. This is an EXPECTATION and not an
#: assumption: a row compares it against the devices the observation actually found, which
#: is C0's own shape — the ground is walked by comparison and never by reading.
_CENSUS_SUBJECTS = ("vda,vdb", "ens3")

#: THE VALIDATION DRIVERS — the instruments that drive or probe the validation set, and
#: therefore the population C4's first clause is about. `_CENSUS_DRIVER` is DELIBERATELY NOT
#: a member: it drives no load and probes no device, it only reads the path's attachment
#: state. Membership is a PROPERTY and not a preference, and a row checks it rather than
#: taking this tuple's word.
VALIDATION_DRIVERS = ("_PROBE_DRIVER", "_PRIV_PROBE_DRIVER", "_CALIB_DRIVER")


# ---------------------------------------------------------------- the observation surfaces
_SURFACE_READ = {"rd", "ls", "listdir", "stat", "isdir", "exists", "realpath", "access",
                 "basename", "abspath"}
_SURFACE_WRITE = {"wr"}

#: The parameter name of the driver's own read/write WRAPPERS. A call site inside a wrapper
#: is the wrapper, not a distinct surface: every real path reaches the filesystem through
#: one of them, so counting them would double every entry. Named rather than dropped.
_WRAPPER_PARAMS = {"path"}


def _bindings(node):
    """(name, value) for a plain assignment AND for tuple unpacking. The driver binds
    `tot, base = 0, os.path.join(T, "per_cpu")` and `bdir, ndir = ..., ...`; a walker that
    only understood single targets reported six real sysfs surfaces as unresolved."""
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        return []
    t, v = node.targets[0], node.value
    if isinstance(t, ast.Name):
        return [(t.id, v)]
    if isinstance(t, (ast.Tuple, ast.List)) and isinstance(v, (ast.Tuple, ast.List)) \
            and len(t.elts) == len(v.elts):
        return [(a.id, b) for a, b in zip(t.elts, v.elts) if isinstance(a, ast.Name)]
    return []


class _PathResolver(object):
    """Module-level string and string-tuple constants, plus function-local constants and
    local path expressions. The CAP IS STATED because an enumerator's blind spot is the one
    thing it cannot report about itself: a path built from a value outside these two scopes
    is returned in `unresolved`, never dropped."""

    def __init__(self, tree):
        self.mod, self.mod_seq = {}, {}
        for node in tree.body:
            for name, v in _bindings(node):
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    self.mod[name] = v.value
                elif isinstance(v, (ast.Tuple, ast.List)) and v.elts and all(
                        isinstance(e, ast.Constant) and isinstance(e.value, str)
                        for e in v.elts):
                    self.mod_seq[name] = [e.value for e in v.elts]

    def locals_of(self, fn):
        out, exprs = dict(self.mod), {}
        for node in ast.walk(fn):
            for name, v in _bindings(node):
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    out[name] = v.value
                elif isinstance(v, (ast.Call, ast.BinOp)):
                    exprs[name] = v
        return out, exprs

    def loopvars_of(self, fn):
        """{loop variable: values} for `for x in <tuple>`. This is how `os.path.join(T, f)`
        over TRACE_FIELDS expands into its five real surfaces instead of collapsing into
        one unresolved site."""
        out = {}
        for node in ast.walk(fn):
            if not isinstance(node, (ast.For, ast.comprehension)):
                continue
            tgt, it = node.target, node.iter
            if not isinstance(tgt, ast.Name):
                continue
            if isinstance(it, ast.Name) and it.id in self.mod_seq:
                out[tgt.id] = self.mod_seq[it.id]
            elif isinstance(it, (ast.Tuple, ast.List)) and it.elts and all(
                    isinstance(e, ast.Constant) and isinstance(e.value, str)
                    for e in it.elts):
                out[tgt.id] = [e.value for e in it.elts]
        return out

    def resolve(self, node, names, loops, exprs=None, depth=0, inner=False):
        """-> candidate paths, or None when the expression is beyond this walker.

        `inner` marks a COMPONENT of a larger path: there an unknown name renders as a
        `<name>` placeholder, because the surface is the template and the substitution is a
        device name. At the top level an unknown name resolves to nothing, so a wrapper's
        `open(path)` is reported as indirect rather than invented."""
        exprs = exprs or {}
        if depth > 6:
            return None
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return [node.value]
        if isinstance(node, ast.Name):
            if node.id in names:
                return [names[node.id]]
            if node.id in loops:
                return list(loops[node.id])
            if node.id in exprs:
                return self.resolve(exprs[node.id], names, loops, exprs, depth + 1, inner)
            return ["<%s>" % node.id] if inner else None
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            return self.resolve(node.left, names, loops, exprs, depth + 1, inner)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ("join", "realpath", "abspath"):
            if node.func.attr != "join":
                return self.resolve(node.args[0], names, loops, exprs, depth + 1, inner)
            parts = [self.resolve(a, names, loops, exprs, depth + 1, True)
                     for a in node.args]
            if any(p is None for p in parts):
                return None
            outs = [""]
            for p in parts:
                outs = [(o.rstrip("/") + "/" + q.lstrip("/")) if o else q
                        for o in outs for q in p]
            return outs
        return None


def observation_surfaces(driver_text):
    """ADDENDUM 7 C4's enumeration, COMPUTED FROM THE INSTRUMENT'S OWN TEXT.

    -> ({path: [kinds]}, unresolved, structural)

    KINDS
      READ-FOR-DATA   the driver reads it and the reading IS the measurement
      CONTROL-WRITE   the driver writes it to arm, clear or restore the observation

    THE SPLIT IS THE POINT AND IT IS NOT A SOFTENING. C4's red world is a WRITE-CAPABLE
    ATTACHMENT TO THE I/O PATH, and none of the four written paths is on the I/O path: they
    are tracefs control files that arm and disarm STATIC tracepoints and clear a ring
    buffer. Nothing in this enumeration opens a block device, a socket or a queue. An
    enumeration that reported "read-only" over a set containing four writes would be a
    sentence rather than a measurement, so the writes are named and their subject stated.

    `structural` holds the two sites that cannot resolve BY CONSTRUCTION rather than by
    ignorance — a wrapper body and the instrument hashing its own source — so `unresolved`
    means what it says."""
    tree = ast.parse(driver_text)
    R = _PathResolver(tree)
    found, unresolved, structural = {}, [], []

    # FUNCTION SCOPES FIRST, module scope LAST. The module walk reaches every node in the
    # file, so visiting it first would consume every call site with an empty local scope
    # and no function-local name would ever resolve — a walker returning a confident,
    # short, wrong enumeration.
    scopes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            names, exprs = R.locals_of(node)
            scopes.append((node, names, R.loopvars_of(node), exprs))
    scopes.append((tree, R.mod, {}, {}))

    seen = set()
    for scope, names, loops, exprs in scopes:
        for node in ast.walk(scope):
            if not isinstance(node, ast.Call) or not node.args or id(node) in seen:
                continue
            f = node.func
            fname = (f.id if isinstance(f, ast.Name)
                     else f.attr if isinstance(f, ast.Attribute) else None)
            if fname in _SURFACE_WRITE:
                kind = "CONTROL-WRITE"
            elif fname in _SURFACE_READ:
                kind = "READ-FOR-DATA"
            elif fname == "open":
                flags = " ".join(ast.dump(a) for a in node.args[1:]) + \
                        " ".join(ast.dump(k) for k in node.keywords)
                kind = ("CONTROL-WRITE"
                        if ("O_WRONLY" in flags or "O_RDWR" in flags or "'w'" in flags)
                        else "READ-FOR-DATA")
            else:
                continue
            seen.add(id(node))
            paths = R.resolve(node.args[0], names, loops, exprs)
            if paths is None:
                a0 = node.args[0]
                if isinstance(a0, ast.Name) and a0.id in _WRAPPER_PARAMS:
                    structural.append({"line": node.lineno, "kind": kind,
                                       "class": "WRAPPER-INDIRECTION"})
                elif "__file__" in ast.dump(a0):
                    structural.append({"line": node.lineno, "kind": kind,
                                       "class": "INSTRUMENT-READS-ITS-OWN-SOURCE"})
                else:
                    unresolved.append({"line": node.lineno, "kind": kind,
                                       "source": ast.dump(a0)[:200]})
                continue
            for p in paths:
                if p.startswith("/"):
                    found.setdefault(p, set()).add(kind)
                else:
                    unresolved.append({"line": node.lineno, "kind": kind,
                                       "source": "not an absolute path: %r" % p})
    return ({p: sorted(k) for p, k in sorted(found.items())}, unresolved,
            sorted(structural, key=lambda x: (x["class"], x["line"])))


def executed_commands(text):
    """WHAT AN INSTRUMENT CAN EXECUTE, read off its own text.

    -> (literal command names, wrapper sites, indirect-argv sites)

    BY TOKEN AND NEVER BY THE WORD. The first version of the row below asked whether the
    string "dd" appeared anywhere in the census text; it appears inside "added", "handed"
    and "and", so the guard reddened on its own prose — the estate's standing
    word-versus-token lesson arriving inside a check written the same afternoon.

    THE THREE BUCKETS ARE THE POINT, and the discriminator is the third. A site whose argv
    is a bare parameter of its own function is the instrument's `run` WRAPPER, which every
    real call passes through. A site whose argv comes from anywhere else is executing
    SOMETHING ITS CALLER CHOSE — which is what driving a load is. An instrument with no
    indirect site can only ever run the commands visible in its own text."""
    tree = ast.parse(text)
    literals, wrapper, indirect = set(), [], []
    scopes = [(n, {a.arg for a in n.args.args}) for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef)] + [(tree, set())]
    seen = set()
    for scope, params in scopes:
        for node in ast.walk(scope):
            if not isinstance(node, ast.Call) or not node.args or id(node) in seen:
                continue
            f = node.func
            fname = (f.id if isinstance(f, ast.Name)
                     else f.attr if isinstance(f, ast.Attribute) else None)
            if fname not in ("run", "check_output", "call", "Popen"):
                continue
            seen.add(id(node))
            argv = node.args[0]
            if isinstance(argv, (ast.List, ast.Tuple)) and argv.elts \
                    and isinstance(argv.elts[0], ast.Constant) \
                    and isinstance(argv.elts[0].value, str):
                literals.add(argv.elts[0].value)
            elif isinstance(argv, ast.Name) and argv.id in params:
                wrapper.append(node.lineno)
            else:
                indirect.append(node.lineno)
    return sorted(literals), sorted(wrapper), sorted(indirect)


def write_call_sites(text):
    """Every call site in `text` that can WRITE a file. Run against the census instrument's
    own source: a read-only instrument holding a write call site is read-only BY PROMISE,
    and the paired-seat standard §9 prices exactly that distinction — a rule a seat can
    break by accident is not a control."""
    hits = []
    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        fname = (f.id if isinstance(f, ast.Name)
                 else f.attr if isinstance(f, ast.Attribute) else None)
        if fname in ("wr", "writelines", "truncate", "remove", "unlink", "rmdir",
                     "mkdir", "makedirs", "chmod", "chown", "rename", "mount", "umount"):
            hits.append(fname)
        elif fname == "write" and not (isinstance(f, ast.Attribute)
                                       and isinstance(f.value, ast.Name)
                                       and f.value.id == "sys"):
            hits.append("write")
        elif fname == "open":
            blob = " ".join(ast.dump(a) for a in node.args[1:]) + \
                   " ".join(ast.dump(k) for k in node.keywords)
            if any(t in blob for t in ("'w'", "'a'", "'r+'", "'x'", "O_WRONLY", "O_RDWR",
                                       "O_CREAT", "O_TRUNC", "O_APPEND")):
                hits.append("open-for-write")
    return sorted(set(hits))


# ------------------------------------------------------------------- the drivers, over time
def drivers_at(rev):
    """{validation driver: sha256 of its STRING VALUE} at one commit, parsed not grepped.

    THE VALUE AND NOT THE SOURCE LINES. Two drivers whose text is identical but whose
    surrounding comment moved are the same driver, and a digest over source lines would say
    otherwise. Read through `era_pin.blob_at`, the estate's one home for an era read."""
    src = era_pin.blob_at(rev, "tests/test_ep29.py").decode("utf-8")
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in VALIDATION_DRIVERS \
                and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            out[node.targets[0].id] = hashlib.sha256(
                node.value.value.encode("utf-8")).hexdigest()
    return out


def driver_history(era=W2_ERA_COMMIT):
    """{driver: [(commit, digest), ...]} across the era commit and EVERY commit that has
    touched this file since, oldest first.

    WHY THE WHOLE HISTORY AND NOT TWO ENDPOINTS. ADDENDUM 7 C4 asks for ONE comparison,
    before W2a against after W2c, and that comparison is made below and passes. It is also
    STRUCTURALLY UNABLE to see a driver that moved and moved back, and it has NO POPULATION
    AT ALL for a driver born inside W2 — an endpoint comparison over a name absent at one
    endpoint passes for the wrong reason. Both are answered by walking every point.

    `rev-list` is a REPOSITORY FACT and is named in `tests/era_pin.py`'s own near-miss
    controls as NOT the era-pin mechanism; the blob reads it feeds all go through that
    home."""
    revs = subprocess.run(["git", "rev-list", "--reverse", "%s..HEAD" % era, "--",
                           "tests/test_ep29.py"],
                          cwd=REPO, capture_output=True, text=True, check=True)
    out = {}
    for rev in [era] + revs.stdout.split():
        for name, digest in drivers_at(rev).items():
            out.setdefault(name, []).append((rev, digest))
    return out


def driver_freeze_defects(history, live):
    """Given the history and the LIVE digests, the reasons a driver is not frozen.

    THE RULE IS DERIVED AND NOT FITTED, in two halves that answer two different questions:

      1. THE PLAN'S OWN COMPARISON. A driver present at the era must carry the era's digest
         now. This is `before W2a against after W2c`, said exactly.
      2. THE FREEZE. From the first point at which a driver reached the digest it carries
         now, it must never have left it. That point is defined by the digest the law and
         the exhibition depend on — not by a date anyone picks — so a driver AUTHORED
         across several commits inside its own movement is not a driver that MOVED, while
         one edited after settling is caught wherever it happened.

    What the second half reports rather than reds: `authored_before_settling`, the digests a
    driver held while it was being written. `_CALIB_DRIVER` holds three, all inside W2a, and
    W2a's own entry names them as its three runs — so this reading confirms that record
    instead of discovering something it contradicts."""
    reds, authored = [], {}
    for name, points in sorted(history.items()):
        digests = [d for _, d in points]
        now = live.get(name)
        if now is None:
            reds.append("%s is gone from the live tree" % name)
            continue
        if digests[0] != now and points[0][0] == W2_ERA_COMMIT:
            reds.append("%s was %s at the era and is %s now — a driver byte moved across "
                        "the whole of W2" % (name, digests[0][:16], now[:16]))
        if now not in digests:
            reds.append("%s carries a digest no recorded commit holds" % name)
            continue
        first = digests.index(now)
        after = digests[first:]
        if any(d != now for d in after):
            reds.append("%s left its settled digest after reaching it: %r"
                        % (name, [d[:16] for d in after]))
        if first:
            authored[name] = [d[:16] for d in digests[:first]]
    return sorted(reds), authored


# ------------------------------------------------------------------- the law, read as data
def intake_by_class(pack):
    """{device_class: DECLARE-INTAKE payload}, KEYED OFF W2b's OWN `intake_declarations`
    rather than re-walking the pack.

    ONE HOME FOR THE READ. The first draft of this pass wrote its own walker, and the
    suite caught it immediately — a same-named second definition shadowed W2b's and broke
    thirty-five of its rows. The fix is the estate's own eighteen-copy lesson arriving one
    file in: a second walker drifts from the first the moment either changes, so this one
    only RE-KEYS what the existing reader already returns.

    Keyed on the ACTION and never on `founding_version`: a reader keyed on the version is
    falsified by the next founding move and joins §A57's sweep population for nothing the
    action name does not already give."""
    return {d["device_class"]: d for d in intake_declarations(pack)}


#: THE LAW W2c's EXHIBITION RAN UNDER, memoised so the era is read once rather than per row.
_W2C_LAW_MEMO = {}


def w2c_law():
    """W2c's declarations, read out of the era W2c ran in and never off the live tree.

    [DOCUMENTED FLIP — EP-29 W3a, 2026-08-13, §A57 BY FALSIFICATION.
    CAUSE: W3a WITHDREW `device-intake@net`'s threshold — `max_arrivals.value` is now
    `null` — and every W2c row that builds or reads a shadow covering record divides by
    that number. Twenty-six rows reddened in one arm, all in this file.
    ASSERTED: `intake_by_class(live_pack())` at the SIX sites the reddened rows read
    through — `w2c_world`, `synthetic_world` and four rows. TWO FURTHER SITES SPELL THE SAME
    READ AND ARE DELIBERATELY LEFT ALONE, because §A57's permission is bounded by
    FALSIFICATION and neither reddened: `live_shadow_set` is referenced by nothing in this
    file at all, and `test_a_class_the_law_declares_NOTHING_for_REFUSES...` replaces every
    window's device class before the declarations are consulted. Both are RAISED in this
    pass's entry rather than swept in by tidiness.
    SUPERSEDED: the same read against the pack as it stood at `W3A_BEFORE_COMMIT` — the
    constant is defined in the W3a section at the foot of this file, deliberately, because
    one commit gets ONE name here and a second constant spelling the same era is the alias
    proliferation this estate refuses.
    REMAINS TRUE: everything W2c claimed. Its exhibition ran on 2026-08-13 under v1.22.0,
    against a law that declared a net threshold of 3518, and the claim that the shadow
    records matched THAT law is unchanged by the law moving afterwards — which is §A57's
    own sentence: both sides of a historical assertion belong to that history's era, and
    the live tree is not one of them.
    GIVEN UP: the W2c rows no longer track a change to the CURRENT law's net declaration.
    That is not a loss this pass created — it is what era-pinning always costs, and the
    current law's net class is exercised instead by W3a's own rows and, when it is
    authored, by W3b's C7 refusal rows, which are where a live net intake belongs.
    NOT TAKEN, and named because it was the tempting repair: teaching `shadow_records` a
    branch for a declaration whose threshold is unestablished. That branch IS ADDENDUM 8
    C7 — `intake for a class whose threshold value is UNESTABLISHED refuses citing the
    absence` — it lands at W3b, and authoring it here would be a builder writing a claim
    another movement must drive, inside a unit that is closed.]"""
    if "declarations" not in _W2C_LAW_MEMO:
        _W2C_LAW_MEMO["declarations"] = intake_by_class(pack_at(W3A_BEFORE_COMMIT))
    return copy.deepcopy(_W2C_LAW_MEMO["declarations"])


# ------------------------------------------------- the projection: what the builder may see
#: OBSERVATION. Every field here is read off a notification surface.
_OBSERVED_FIELDS = ("device", "device_class", "level", "level_kind", "repeat",
                    "arrivals", "interrupts", "open", "close", "subject_stable",
                    "events_enabled_at_open", "trace_totals", "overrun_delta")

#: WITHHELD, and the two reasons are two different laws.
#:
#: THE DRIVER'S OWN REPORT — command, load_results, load_size, taking. C4 says the shadow
#: set is built from OBSERVATION ALONE, so the builder must be UNABLE to read what the load
#: says it did. `load_size.delivered_units` is the sharp one: it is the very figure W2b's
#: block unit was derived against, so a builder that could see it could reproduce the right
#: answer without observing anything and the exhibition would prove nothing.
#:
#: THE CLOCK — elapsed_s and both rates. DEV-LAW-INTAKE makes closers EVENT-BASED and
#: refuses a time bound of any kind, so the builder is built unable to reach a duration
#: rather than instructed not to use one. Forbidden versus unable, and this estate's answer
#: is always unable.
_WITHHELD_FIELDS = ("command", "load_results", "load_size", "taking",
                    "elapsed_s", "rate_arrivals_per_s", "rate_interrupts_per_s")


def observation_only(window):
    """The window as the record builder sees it."""
    return {k: copy.deepcopy(window[k]) for k in _OBSERVED_FIELDS if k in window}


_BYTE_TOTAL_BASIS = (
    "UNESTABLISHED IN THIS OBSERVATION, and DECLARED unestablished rather than omitted — "
    "the shape W2b's own net per-act unit already took. DEV-LAW-INTAKE says a covering "
    "record carries the BYTE TOTAL over the arrivals it covers. THE SURFACE CARRIES THAT "
    "DATUM AND THIS PASS READ THE SURFACE'S OWN FORMAT DECLARATION TO ESTABLISH IT: "
    "block:block_rq_issue declares `bytes` and `nr_sector`, net:net_dev_queue declares "
    "`len`, irq:irq_handler_entry declares neither. THE INSTRUMENT DOES NOT EXTRACT THEM: "
    "_CALIB_DRIVER's read_trace counts lines and parses no payload field, and that "
    "instrument is FROZEN for the whole of W2 because a driver byte moving is this claim's "
    "own red world. So the datum exists at the surface and not in this observation, and the "
    "value is null with its reason rather than a number with no basis.")

_IDENTITY_BASIS = (
    "UNESTABLISHED HERE BY DESIGN, and by the declaration's own words. Its `records` clause "
    "says the device is carried by the identity the estate's identity law gives it and "
    "NEVER by a hardware alias standing alone (ADDENDUM 2 §2 — alias equality never implies "
    "identity), and says the minting itself is EP-29 W4's and is not built by the "
    "declaration. So a shadow record carries the OBSERVED ALIAS marked as an alias and "
    "mints nothing.")

_NOT_CLOSED_BASIS = (
    "neither declared closer fired inside this observation window: the cap was not reached "
    "and no unbind occurred. THE OBSERVATION WINDOW ENDING IS NOT A CLOSER — DEV-LAW-INTAKE "
    "makes closers event-based and this declaration names exactly two, so a covering record "
    "that stopped at the edge of an observation would be closing on a boundary the law does "
    "not declare.")


def shadow_records(observation, declarations, provenance=None):
    """EVIDENCE, NEVER RECORD. Covering records built from OBSERVATION ALONE, at the grade
    the landed law declares.

    A window of A arrivals under a cap C produces ceil(A / C) covering records — the
    arithmetic the block cap's own `why_this_value` states — and CONTROL windows are not
    covered at all, because a control is the reading the loaded cells are compared against
    and not a load level.

    Nothing here is appended to any store: ADDENDUM 7's not-claimed block puts the intake
    ENGINE at W3's shim contract, so every record carries `evidence_not_record`."""
    out = []
    for w in observation.get("windows", []):
        if w.get("level_kind") != "LOAD":
            continue
        o = observation_only(w)
        cls = o["device_class"]
        arrivals = o["arrivals"]["count"]
        decl = declarations.get(cls)
        if decl is None:
            # DEV-LAW-BIND's direction, written into DEV-LAW-INTAKE: where the law declares
            # no intake for a class, arrivals are ADMITTED BY NOTHING, the intake refuses,
            # and THE REFUSAL IS THE RECORD. Nothing goes dark.
            out.append({"kind": "SHADOW-INTAKE-REFUSAL", "evidence_not_record": True,
                        "law_cited": "DEV-LAW-INTAKE", "device_class": cls,
                        "device": {"observed_alias": o["device"], "device_class": cls},
                        "refused_because": "no intake declaration founds this device class",
                        "arrivals_observed": arrivals, "level": o["level"],
                        "repeat": o.get("repeat")})
            continue
        cap = decl["max_arrivals"]["value"]
        unit = decl["arrivals_per_admitted_act"]["value"]
        n = int(math.ceil(arrivals / float(cap))) if arrivals else 0
        remaining = arrivals
        for i in range(n):
            covered = min(cap, remaining)
            remaining -= covered
            out.append({
                "kind": "SHADOW-COVERING-RECORD",
                "evidence_not_record": True,
                "law_cited": "DEV-LAW-INTAKE",
                "intake": decl["intake"],
                "window": decl["window"],
                "grade": decl["grade"],
                "bound": {"max_arrivals": cap},
                "covers": {"arrival_count": covered,
                           "byte_total": {"value": None, "basis": _BYTE_TOTAL_BASIS}},
                "admitted_acts": (
                    {"value": covered // unit, "unit": unit,
                     "basis": "arrivals covered divided by the declared "
                              "arrivals_per_admitted_act — from the arrival count alone, "
                              "and never from the load's own delivered figure, which this "
                              "builder cannot see"}
                    if unit else
                    {"value": None, "unit": None,
                     "basis": decl["arrivals_per_admitted_act"]["basis"]}),
                "device": {"observed_alias": o["device"], "device_class": cls,
                           "identity": {"value": None, "basis": _IDENTITY_BASIS}},
                "closed": covered == cap,
                "closed_by": "max_arrivals" if covered == cap else None,
                "not_closed_because": None if covered == cap else _NOT_CLOSED_BASIS,
                "sequence": {"index": i + 1, "of": n},
                "observed_window": {
                    "level": o["level"], "repeat": o.get("repeat"),
                    "arrivals_in_window": arrivals,
                    "interrupts_in_window": o["interrupts"]["count"],
                    "subject_stable": o["subject_stable"],
                    "open_boot_id": o["open"]["boot_id"],
                    "close_boot_id": o["close"]["boot_id"],
                    "open_uptime_s": o["open"]["uptime_s"],
                    "close_uptime_s": o["close"]["uptime_s"]},
                "provenance": provenance or {},
            })
    return out


def records_per_interrupt(observation, records):
    """THE SECONDARY CONFORMANCE ROW, AT EVERY DRIVEN LEVEL.

    [:663's repair, applied rather than quoted: C1's floor is TWO OR MORE and the cell once
    said "both", which left a builder driving three with no instruction for the third. Two
    is the FLOOR and never the count, so this walks whatever levels the table holds.]

    CONFORMANCE, NOT SCALING. C9's red — the ratio REQUIRED to fall as load rises — is W5's,
    and ADDENDUM 7's not-claimed block says W2c does not rehearse it. The question here is
    narrower and answerable from one table: did the records do what the landed law says."""
    rows = {}
    for w in observation.get("windows", []):
        if w.get("level_kind") != "LOAD":
            continue
        rows[(w["device"], w["level"], w.get("repeat"))] = {
            "device": w["device"], "device_class": w["device_class"],
            "level": w["level"], "repeat": w.get("repeat"),
            "arrivals": w["arrivals"]["count"],
            "interrupts": w["interrupts"]["count"], "records": 0}
    for r in records:
        if r["kind"] != "SHADOW-COVERING-RECORD":
            continue
        key = (r["device"]["observed_alias"], r["observed_window"]["level"],
               r["observed_window"]["repeat"])
        if key in rows:
            rows[key]["records"] += 1
    for row in rows.values():
        i = row["interrupts"]
        row["records_per_interrupt"] = (row["records"] / float(i)) if i else None
        row["interrupts_per_record"] = (i / float(row["records"])) if row["records"] else None
    return [rows[k] for k in sorted(rows)]


# ------------------------------------------------------------------------ C4's red worlds
def shadow_defects(records, declarations, observation, census_pair, live_drivers, history,
                   licensed=()):
    """The sorted set of C4 red worlds this exhibition exhibits. EMPTY is the only passing
    answer and the live exhibition returns it.

    THREE CODES, because ADDENDUM 7 C4 names three red worlds. Properties this pass also
    holds — a net record inventing a per-act unit, a record minting a device identity, a
    byte total asserted with no basis — are asserted by their OWN rows rather than folded in
    here, so the code set stays the plan's and does not drift into a builder-authored
    battery."""
    d = []

    reds, _ = driver_freeze_defects(history, live_drivers)
    if reds:
        d.append("DRIVER-MOVED")

    # THE LABEL IS THE WEAKEST OF THE FOUR READINGS. A record set can call itself `window`
    # and still be one record per interrupt; the RATIO cannot lie about that, so the ratio
    # is asked as well as the name.
    for r in records:
        if r["kind"] != "SHADOW-COVERING-RECORD":
            continue
        decl = declarations.get(r["device"]["device_class"], {})
        if r.get("grade") != decl.get("grade") or r.get("grade") == "per-interrupt":
            d.append("PER-INTERRUPT-GRADE")
        if (r.get("bound") or {}).get("max_arrivals", 0) <= 1:
            d.append("PER-INTERRUPT-GRADE")           # the law: no bound of one, ever
        if r["covers"]["arrival_count"] <= 1 \
                and r["observed_window"]["arrivals_in_window"] > 1:
            d.append("PER-INTERRUPT-GRADE")
    for row in records_per_interrupt(observation, records):
        if row["interrupts"] and row["records"] >= row["interrupts"]:
            d.append("PER-INTERRUPT-GRADE")

    if interposition_findings(census_pair, licensed):
        d.append("WRITE-CAPABLE-ATTACHMENT")
    return sorted(set(d))


#: Taint bits that mean code the distribution build does not account for is resident. The
#: rest are recorded by the census and not judged here.
_WRITE_CAPABLE_TAINT = ("PROPRIETARY_MODULE", "OOT_MODULE")


# ======================================================================================
# THE RESTATED TAINT READING
# [W2c-TAINT-BIND, RULED board :823, CLOSED :828, SEQUENCED :832 — a NEW UNIT under §10.
#  W2c's verdict STANDS and does not reopen: its rows were TRUE OF ITS WORLD, a world with
#  zero licensed out-of-tree loads. This is a restatement, never a relaxation.
#
#  WHAT WAS WRONG. The three rows' SUBJECT was never the taint VALUE. It is NO
#  WRITE-CAPABLE ATTACHMENT BY OBSERVATION, which the attachment census measures directly
#  and which held GREEN through the entire raise. `taint == 0` was a PROXY for it, and the
#  proxy diverged from its subject the moment the estate performed its first LICENSED load
#  (EP-29 W3b's required act) while the subject went on holding. THE PROXY IS RETIRED —
#  not patched — and the subject and its exercise condition enter the rule's own text.
#
#  THE RULE, IN TWO CLAUSES.
#    (1) EXERCISE CONDITION. `taint == 0` is the correct reading ONLY of a world with ZERO
#        licensed out-of-tree loads. That clause is rule text here rather than an unstated
#        assumption, and it is asserted rather than assumed: with an empty register the
#        reading below demands the raw value be exactly "0".
#    (2) DELTA FORM. From the estate's first licensed load onward — every load being a
#        recorded decision — the taint set equals EXACTLY the bits the licensed loads' own
#        records account for, and A BIT NO LICENSED RECORD ACCOUNTS FOR REDS.
#
#  THE TRIPWIRE SURVIVES PERMANENTLY, which is what makes this a cure and not a loosening:
#  an unlicensed load that sets any bit outside the accounted set still REDS, on any world,
#  forever. Clause (1) is not a special case bolted on — it FALLS OUT of clause (2) with an
#  empty register, which is why the two are one function and not two.
#
#  THE CAP, STATED HERE RATHER THAN DISCOVERED LATER, because it is the honest limit of a
#  kernel-wide flag word: TAINT BITS ARE NOT PER-MODULE. On a boot where a licensed
#  UNSIGNED OUT-OF-TREE load has already set bits 12 and 13, a SECOND and UNLICENSED
#  unsigned out-of-tree load sets NO NEW BIT and this reading CANNOT SEE IT. What sees that
#  case is the module-set half of the same census — `interposition_findings`' own
#  before/after comparison BY NAME — and W3b's C5 rows already record the same fact from
#  the other side (`test_THE_TAINT_FIELD_IS_DISCLOSED_AS_NO_LONGER_A_BRACKET_SIGNAL`). The
#  tripwire is carried by the two halves together; neither half alone is the claim.]
# ======================================================================================

#: bit position -> name. HAND-COMPUTED FROM THE KERNEL'S OWN TAINT DEFINITIONS AND HELD ON
#: THE HOST, deliberately a second table rather than a reuse of the guest instrument's.
#: `taint_bits` at the census driver decodes on the GUEST; this decodes the same raw value
#: on the HOST, and a row below compares the two answers. A single shared decoder would
#: make that comparison a check that cannot fail — it would be one table agreeing with
#: itself. Two tables that must agree is the whole point, and the divergence they can
#: report is exactly the class §7.1 calls an instrument that cannot report its own failure.
#:
#: THE HONEST LIMIT OF THAT CROSS-CHECK, since a comparison's cap belongs beside it: the
#: two tables are INDEPENDENTLY WRITTEN but not INDEPENDENTLY SOURCED — both spell the same
#: kernel's bit definitions, so a name that is wrong in the SAME WAY in both is invisible to
#: the comparison. What it does catch is the case that actually happens: one table edited,
#: extended, or truncated while the other stands. Bit COVERAGE, which is the failure mode a
#: name list cannot show at all, is caught by the raw-against-recomputed comparison instead
#: and does not depend on either table being complete.
_TAINT_BIT_NAMES = {0: "PROPRIETARY_MODULE", 1: "FORCED_MODULE", 2: "UNSAFE_SMP",
                    3: "FORCED_RMMOD", 4: "MACHINE_CHECK", 5: "BAD_PAGE", 6: "USER",
                    7: "DIE", 8: "OVERRIDDEN_ACPI_TABLE", 9: "WARN", 10: "CRAP",
                    11: "FIRMWARE_WORKAROUND", 12: "OOT_MODULE", 13: "UNSIGNED_MODULE",
                    14: "SOFTLOCKUP", 15: "LIVEPATCH", 16: "AUX", 17: "RANDSTRUCT"}


def taint_bits_host(value):
    """The host's own decode of `/proc/sys/kernel/tainted`. Sorted names, same convention
    as the guest's."""
    return sorted(_TAINT_BIT_NAMES[b] for b in sorted(_TAINT_BIT_NAMES)
                  if value & (1 << b))


def taint_value_of(names):
    """The INVERSE: names back to the integer they imply. Used to ask whether the raw value
    holds anything the name table does not cover — a bit at position 18 or beyond decodes
    to NO NAME AT ALL under either table, so a reading that compared only name lists would
    call such a world clean. Comparing the raw value against the value its own decoded
    names imply is what closes that hole, and it needs the inverse to exist."""
    inv = {n: b for b, n in _TAINT_BIT_NAMES.items()}
    v = 0
    for n in names or ():
        v |= 1 << inv[n]
    return v


#: THE LICENSED OUT-OF-TREE LOADS OF THIS ESTATE — the record set the taint reading is
#: accounted against, and the only thing that moves a bit from UNACCOUNTED to ACCOUNTED.
#:
#: EVERY LOAD IS A RECORDED DECISION. An entry here is a transcription of that record, and
#: `accounts_for` is a HAND-COMPUTED LITERAL read off the kernel's taint semantics — NEVER
#: off the guest's current value. That direction is the difference between a rule and a
#: rubber stamp: a register populated from the observed value would make the reading below
#: agree with any world it was ever shown, which is precisely the positive-control-shaped-
#: to-fit-the-filter disguise this estate has now been bitten by. A row below asserts that
#: the accounted set EXCLUDES a write-capable bit and that planting that bit still REDS.
THE_LICENSED_OUT_OF_TREE_LOADS = (
    {"module": "govshim",
     "record": "EP-29 W3b's required act — the shim load, ACCEPTED at board :832. The load "
               "is a recorded decision and this entry is that record's transcription.",
     "accounts_for": ("OOT_MODULE", "UNSIGNED_MODULE"),
     "basis": "HAND-COMPUTED from the kernel's own taint semantics and from nothing this "
              "guest reports: loading a module the distribution build does not account for "
              "sets bit 12 (OOT_MODULE), and loading one carrying no valid signature sets "
              "bit 13 (UNSIGNED_MODULE). Signing the module would clear ONLY bit 13, "
              "leaving 4096 and not 0 — which is why 'sign it and the row goes green' was "
              "never available and the rule had to be restated instead."},
)


def accounted_taint_bits(licensed):
    """The union of the bits the licensed loads' OWN RECORDS account for. An empty register
    yields an empty set, and that is the exercise condition falling out of the delta form
    rather than being written twice."""
    out = set()
    for rec in licensed or ():
        out.update(rec["accounts_for"])
    return sorted(out)


def taint_reading(census, licensed):
    """THE WHOLE READING, in one place, carrying its own population and basis (§A51).

    POPULATION: the taint word of the ONE census blob handed in — one guest at one instant
    and no other. BASIS: set difference over decoded bit NAMES, plus one comparison of the
    raw integer against the value its decoded names imply.

    `unaccounted` is the RED. `unexercised` is DISCLOSED AND IS NEVER A RED, and the reason
    is a derivation rather than a preference — see the row that reads it."""
    t = census.get("taint") or {}
    raw = ((t.get("raw") or {}).get("text") or "").strip()
    reported = t.get("bits")
    acc = accounted_taint_bits(licensed)
    out = {"raw": raw, "accounted": acc,
           "population": "the taint word of one attachment census blob, at the instant that "
                         "census ran, on the guest it ran on — and no other world",
           "basis": "set difference over decoded bit NAMES; the raw integer compared "
                    "against the value its own decoded names imply"}
    try:
        value = int(raw)
    except (TypeError, ValueError):
        # AN UNREADABLE TAINT WORD IS A LIMIT AND NEVER A CLEAN RESULT. Returning an empty
        # unaccounted set here would let a census that could not read its subject pass the
        # tripwire, which is the unrun check reported as an absence.
        out.update({"value": None, "bits_host": None, "bits_reported": reported,
                    "unaccounted": ["THE-TAINT-WORD-DID-NOT-READ"], "unexercised": [],
                    "decoder_disagreement": ["THE-TAINT-WORD-DID-NOT-READ"],
                    "value_covered_by_the_name_table": False})
        return out
    host = taint_bits_host(value)
    out.update({
        "value": value,
        "bits_host": host,
        "bits_reported": (None if reported is None else sorted(reported)),
        "unaccounted": sorted(set(host) - set(acc)),
        "unexercised": sorted(set(acc) - set(host)),
        # The guest decoded the same word with its own table. Disagreement means one of the
        # two tables is wrong, and neither is trustworthy until it is resolved.
        "decoder_disagreement": (["THE-GUEST-REPORTED-NO-BITS"] if reported is None else
                                 sorted(set(host) ^ set(reported))),
        # False exactly when the raw word carries a bit no name table covers.
        "value_covered_by_the_name_table": (value == taint_value_of(host)),
    })
    return out


def unaccounted_taint_bits(census, licensed):
    """THE TRIPWIRE, alone: bits present in this world that NO licensed record accounts
    for. EMPTY is the only passing answer, on every world, forever."""
    return taint_reading(census, licensed)["unaccounted"]


def interposition_findings(census_pair, licensed=()):
    """Every reason the driven I/O path is NOT bare, as plain sentences. EMPTY passes.

    THE AMBIENT / INTRODUCED SPLIT IS NOT MADE HERE, DELIBERATELY. This returns everything
    write-capable it can see; `ambient_path_state` names separately what was already there
    and why it is not this claim's subject. A reading that decided for itself which
    attachments did not count would be authoring the ruling C0's third state exists to
    refuse.

    `licensed` IS THE ONE EXCEPTION TO THAT SENTENCE AND IT IS NOT THIS FUNCTION'S
    JUDGEMENT — it is a RECORD SET handed in, per the restated rule above. The default is
    the EMPTY register, so every caller that hands nothing gets exactly the behaviour this
    function shipped with: with no licensed load recorded, every taint bit is unaccounted
    and speaks. Nothing about the other clauses moves."""
    before, after = census_pair
    out = []

    # THE SHARPEST READING FIRST, and it needs no judgement at all: the attachment state on
    # either side of an observation. Had observing attached anything, these would differ.
    for k in ("block_stacking", "device_mapper", "net_attachments", "netfilter", "bpf",
              "dynamic_instrumentation", "taint", "modules"):
        if json.dumps(before.get(k), sort_keys=True) != json.dumps(after.get(k),
                                                                  sort_keys=True):
            out.append("the attachment census MOVED across the observation at %r — the "
                       "observation changed the path it was observing" % k)

    c = after
    for dev, st in sorted((c.get("block_stacking") or {}).items()):
        for rel in ("holders", "slaves"):
            ents = (st.get(rel) or {}).get("entries")
            if ents:
                out.append("block device %s has %s %r — a stacked target sits in the path"
                           % (dev, rel, ents))
    dm = ((c.get("device_mapper") or {}).get("dmsetup") or {}).get("stdout") or ""
    if dm.strip() and "No devices found" not in dm:
        out.append("device-mapper reports targets: %r" % dm.strip()[:200])

    for nif, na in sorted((c.get("net_attachments") or {}).items()):
        if '"xdp"' in ((na.get("link") or {}).get("stdout") or ""):
            out.append("interface %s carries an XDP program" % nif)
        for side in ("filter_egress", "filter_ingress"):
            body = ((na.get(side) or {}).get("stdout") or "").strip()
            if body and body != "[]":
                out.append("interface %s carries a tc %s: %r" % (nif, side, body[:200]))

    for kind, r in sorted((c.get("netfilter") or {}).items()):
        # AN UNRUN CHECK IS A LIMIT AND NEVER A CLEAN RESULT. "the binary is absent" and
        # "the ruleset is empty" are the same empty string and different facts.
        if r.get("available") and (r.get("stdout") or "").strip():
            out.append("the netfilter ruleset read by %s is NOT empty" % kind)

    try:
        for entry in json.loads(((c.get("bpf") or {}).get("net_list") or {}).get("stdout")
                                or "[]"):
            for hook in ("xdp", "tc", "flow_dissector", "netfilter"):
                if entry.get(hook):
                    out.append("a BPF program is attached to the net path at hook %r" % hook)
    except ValueError:
        out.append("the BPF net attachment list did not parse — that check DID NOT RUN")

    # A CGROUP BPF PROGRAM REACHES A PROCESS ONLY THROUGH THAT PROCESS'S OWN CGROUP ANCESTOR
    # CHAIN. "is there a BPF program on this box" is therefore the wrong question and this
    # asks the right one. Asked at the SLICE rather than at the leaf scope, because the load
    # and the census run in sibling session scopes under the same user slice — so the answer
    # does not depend on a session number.
    try:
        for entry in json.loads(((c.get("bpf") or {}).get("cgroup_tree") or {}).get("stdout")
                                or "[]"):
            path = (entry.get("cgroup") or "").replace("/sys/fs/cgroup", "") or "/"
            if entry.get("programs") and (path == "/" or path.startswith("/user.slice")):
                out.append("a cgroup BPF program is attached at %r, which contains the "
                           "cgroup the load runs in" % path)
    except ValueError:
        out.append("the cgroup BPF tree did not parse — that check DID NOT RUN")

    dyn = c.get("dynamic_instrumentation") or {}
    for f in ("kprobe_events", "uprobe_events", "dynamic_events"):
        body = ((dyn.get(f) or {}).get("text") or "").strip()
        if body:
            out.append("%s is NOT empty (%r) — a dynamic probe can change what it observes, "
                       "which a static tracepoint cannot" % (f, body[:200]))
    tracer = ((dyn.get("current_tracer") or {}).get("text") or "").strip()
    if tracer and tracer != "nop":
        out.append("current_tracer is %r rather than `nop`" % tracer)

    # THE RESTATED CLAUSE. The question is no longer "is the kernel tainted" — a world
    # holding a lawful, recorded, licensed load answers YES for a reason that is not an
    # interposition. The question is whether a WRITE-CAPABLE bit is present that NO LICENSED
    # RECORD ACCOUNTS FOR, which is the tripwire the proxy was standing in for.
    for bit in unaccounted_taint_bits(c, licensed):
        if bit in _WRITE_CAPABLE_TAINT:
            out.append("the kernel is tainted %s and NO LICENSED LOAD'S RECORD ACCOUNTS "
                       "FOR IT — code the distribution build does not account for is "
                       "resident and nothing recorded a decision to put it there" % bit)
    return sorted(out)


def census_limits(census):
    """CHECKS THAT DID NOT RUN, as declared limits carrying population and basis (§A51's
    2026-08-13 bracket, whose first live use was W2a's). An absence this census cannot see
    is not an absence it may report."""
    lims = []
    s = census.get("subject") or {}
    pop = ("the lab guest %s, machine-id %s, boot_id %s, kernel %s, at uptime %s s — the "
           "moment this census ran and no other"
           % (s.get("hostname"), s.get("machine_id"), s.get("boot_id"), s.get("uname"),
              s.get("uptime_s")))

    def _walk(prefix, blob):
        for name, r in sorted((blob or {}).items()):
            if not isinstance(r, dict):
                continue
            if "available" in r and not r["available"]:
                lims.append({"limit": "the %s/%s check DID NOT RUN, so this census states "
                                      "nothing about it" % (prefix, name),
                             "population": pop,
                             "basis": r.get("why") or "the query command did not execute"})
            elif "available" not in r:
                _walk("%s/%s" % (prefix, name), r)

    for group in ("device_mapper", "net_attachments", "netfilter", "bpf"):
        _walk(group, census.get(group))
    return lims


def ambient_path_state(census):
    """WHAT WAS ALREADY IN THE PATH BEFORE ANY OBSERVATION, NAMED RATHER THAN SMOOTHED.

    C4's claim is that the OBSERVATION interposes nothing. It is not a claim that the
    guest's I/O path is bare, and reporting only the first while the second is false would
    be true and misleading. Each entry states why it is not this claim's subject, so a
    reader can disagree with the reasoning rather than never meet the fact."""
    out = []
    for nif, na in sorted((census.get("net_attachments") or {}).items()):
        q = ((na.get("qdisc") or {}).get("stdout") or "").strip()
        if q and q != "[]":
            out.append({"what": "interface %s carries a root qdisc" % nif,
                        "detail": q[:300],
                        "why_not_a_C4_red":
                            "a root queueing discipline is the distribution's own default, "
                            "present at boot, byte-identical either side of the "
                            "observation, and not something the observation attached. It "
                            "schedules and may drop under congestion; it rewrites nothing."})
    try:
        entries = json.loads(((census.get("bpf") or {}).get("cgroup_tree") or {}).get(
            "stdout") or "[]")
    except ValueError:
        entries = []
    carrying = [e for e in entries if e.get("programs")]
    if carrying:
        out.append({"what": "%d cgroups carry BPF programs" % len(carrying),
                    "detail": sorted(
                        (e["cgroup"].replace("/sys/fs/cgroup", ""),
                         tuple(sorted(p["attach_type"] for p in e["programs"])))
                        for e in carrying),
                    "why_not_a_C4_red":
                        "every one is attached under /system.slice, and a cgroup BPF "
                        "program reaches a process only through that process's own cgroup "
                        "ancestor chain. The load runs under /user.slice, whose chain "
                        "contains none of them, so none of them is in the driven path."})
    return out


# =======================================================================================
# THE BRACKETED EXHIBITION — census BEFORE, the FROZEN observer, census AFTER
#
# The census DRIVER TEXT lives here by the :682 ruling: driver text that exists solely to
# make a row drivable is part of the row, and the scratch rule's object is the instrument's
# EXECUTION and its OUTPUTS, which stay outside the repo. It is NOT a validation driver — it
# drives no load — so its existence moves nothing C4's first red world is about, and
# _CALIB_DRIVER above is untouched, which is the same claim said the other way.
# =======================================================================================
_CENSUS_DRIVER = r'''#!/usr/bin/env python3
"""EP-29 W2c — THE NON-INTERPOSITION CENSUS. GUEST-SIDE LAB INSTRUMENT, never product.

It answers ONE question with evidence rather than with a promise: is anything
WRITE-CAPABLE attached to the I/O path of the validation set? C4's third red world.

IT WRITES NOTHING. Every act here is a read: `open` for reading, `os.listdir`, `os.stat`,
and four query commands that print state. There is no `open(..., "w")`, no `os.open` with
a write flag, and no command that mutates. That is checkable and it is checked: the host
side parses THIS TEXT and reds if a write call site appears in it.

WHY A SEPARATE INSTRUMENT RATHER THAN A WIDER CALIBRATION OBSERVER. `_CALIB_DRIVER` is
FROZEN for the whole of W2 — C4's first red world is a driver byte moving — so the census
cannot be added to it, and the census drives no load, so it is not a validation driver and
its existence moves nothing this claim is about.

WHAT AN UNRUN CHECK MEANS, stated because absence of evidence is the trap this file is
most exposed to: a check whose tool is not installed records `checked: false` with the
reason. It NEVER records "nothing found". The host reading counts an unrun check as a
DECLARED LIMIT with its own population and basis, never as a clean result.

argv: <comma-separated block device names> <comma-separated interface names>
"""
import json
import os
import re
import subprocess
import sys

T = "/sys/kernel/tracing"

#: The four events `_CALIB_DRIVER` enables. Named here to read their FORMAT files, which
#: declare which fields the surface carries. This is how the byte question is answered by
#: reading the surface's own declaration rather than by asserting what a tracepoint holds.
EVENTS = (("block", "block_rq_issue"), ("block", "block_rq_complete"),
          ("irq", "irq_handler_entry"), ("net", "net_dev_queue"))


def rd(path):
    """Read, or say why not. A missing file and an unreadable one are different answers and
    both are recorded: a census that returns "" for both cannot tell absence from denial."""
    try:
        with open(path) as fh:
            return {"ok": True, "text": fh.read()}
    except OSError as exc:
        return {"ok": False, "errno": exc.errno, "strerror": exc.strerror}


def ls(path):
    try:
        return {"ok": True, "entries": sorted(os.listdir(path))}
    except OSError as exc:
        return {"ok": False, "errno": exc.errno, "strerror": exc.strerror}


def run(argv):
    """A query command. `available` is FALSE when the binary is absent, and that is not the
    same answer as an empty ruleset — the reading treats the two differently."""
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        return {"command": " ".join(argv), "available": False,
                "why": "the binary is not installed on this guest"}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"command": " ".join(argv), "available": False, "why": str(exc)}
    return {"command": " ".join(argv), "available": True, "rc": p.returncode,
            "stdout": p.stdout, "stderr": (p.stderr or "")[-400:]}


def taint_bits(value):
    """/proc/sys/kernel/tainted decomposed. Only two bits bear on interposition: a
    proprietary or an out-of-tree module is code in the kernel that the distribution's own
    build does not account for. The rest are recorded and not judged."""
    names = {0: "PROPRIETARY_MODULE", 1: "FORCED_MODULE", 2: "UNSAFE_SMP",
             3: "FORCED_RMMOD", 4: "MACHINE_CHECK", 5: "BAD_PAGE", 6: "USER",
             7: "DIE", 8: "OVERRIDDEN_ACPI_TABLE", 9: "WARN", 10: "CRAP",
             11: "FIRMWARE_WORKAROUND", 12: "OOT_MODULE", 13: "UNSIGNED_MODULE",
             14: "SOFTLOCKUP", 15: "LIVEPATCH", 16: "AUX", 17: "RANDSTRUCT"}
    return sorted(names.get(b, "BIT%d" % b)
                  for b in range(18) if value & (1 << b))


def tracepoint_fields(subsystem, name):
    """The surface's OWN declaration of what it carries. Read, never assumed: the byte
    question W2c raises is answered from this file and from nothing else."""
    r = rd(os.path.join(T, "events", subsystem, name, "format"))
    if not r["ok"]:
        return {"event": "%s:%s" % (subsystem, name), "readable": False, "why": r}
    fields = re.findall(r"field:[^;]*?(\w+)(?:\[\d*\])?;\s*offset:", r["text"])
    return {"event": "%s:%s" % (subsystem, name), "readable": True, "fields": fields,
            "byte_bearing_fields": [f for f in fields
                                    if f in ("bytes", "nr_sector", "len", "data_len")]}


def main():
    if os.getuid() != 0:
        print("CENSUS-JSON:" + json.dumps({"error": "not privileged",
                                           "uid": os.getuid()}))
        return 1
    blocks = [b for b in (sys.argv[1] if len(sys.argv) > 1 else "").split(",") if b]
    netifs = [n for n in (sys.argv[2] if len(sys.argv) > 2 else "").split(",") if n]

    import hashlib
    src = open(os.path.abspath(__file__), "rb").read()
    up = rd("/proc/uptime")
    out = {
        "instrument": {"name": "ep29-w2c-non-interposition-census",
                       "source_sha256": hashlib.sha256(src).hexdigest()},
        "subject": {"boot_id": (rd("/proc/sys/kernel/random/boot_id").get("text") or "").strip(),
                    "machine_id": (rd("/etc/machine-id").get("text") or "").strip(),
                    "hostname": (rd("/proc/sys/kernel/hostname").get("text") or "").strip(),
                    "uptime_s": float((up.get("text") or "0 0").split()[0]),
                    "uname": os.uname().release},
        "asked_about": {"block_devices": blocks, "interfaces": netifs},
        # THE CGROUP THIS PROCESS SITS IN. A cgroup-attached BPF program reaches a process
        # only through its own cgroup's ANCESTOR CHAIN, so "is there a BPF program on the
        # box" is the wrong question and "is one on a cgroup that contains the load" is the
        # right one. The load runs in a sibling session scope under the same user slice, so
        # the reading compares against the SLICE and not against this leaf.
        "self_cgroup": (rd("/proc/self/cgroup").get("text") or "").strip(),
    }

    # ---- 1. BLOCK STACKING. A holder is a target layered OVER this device: device-mapper,
    # md, or anything else that sits in the path and can rewrite what passes through it. A
    # slave is the inverse relation and is recorded so the direction is not guessed at.
    out["block_stacking"] = {
        b: {"holders": ls("/sys/block/%s/holders" % b),
            "slaves": ls("/sys/block/%s/slaves" % b),
            "devno": rd("/sys/block/%s/dev" % b)}
        for b in blocks}
    out["device_mapper"] = {"sysfs_present": os.path.exists("/sys/class/misc/device-mapper"),
                            "dmsetup": run(["dmsetup", "ls"])}

    # ---- 2. NET PATH ATTACHMENTS. XDP and tc actions can drop or rewrite frames; a qdisc
    # alone reorders and is recorded whole rather than filtered, so the reading judges it
    # and this instrument does not.
    out["net_attachments"] = {
        n: {"link": run(["ip", "-d", "-j", "link", "show", n]),
            "qdisc": run(["tc", "-j", "qdisc", "show", "dev", n]),
            "filter_egress": run(["tc", "-j", "filter", "show", "dev", n]),
            "filter_ingress": run(["tc", "-j", "filter", "show", "dev", n, "ingress"])}
        for n in netifs}
    out["netfilter"] = {"nft": run(["nft", "list", "ruleset"]),
                        "iptables": run(["iptables-save"]),
                        "ip6tables": run(["ip6tables-save"])}
    # `net list` reports XDP / tc / flow-dissector / netfilter attachments and reports
    # NOTHING about cgroup-attached programs, which are also in the packet path and can
    # also drop. Both are read, because a census that asked only the first question would
    # have returned an empty answer that was true of the wrong population.
    out["bpf"] = {"prog_list": run(["bpftool", "-j", "prog", "list"]),
                  "net_list": run(["bpftool", "-j", "net", "list"]),
                  "cgroup_tree": run(["bpftool", "-j", "cgroup", "tree"]),
                  "bpffs": ls("/sys/fs/bpf")}

    # ---- 3. DYNAMIC KERNEL INSTRUMENTATION. A tracepoint is static and read-only; a kprobe
    # can be placed anywhere and can change registers. The distinction is the whole reason
    # the observation path is defensible, so it is measured rather than argued.
    out["dynamic_instrumentation"] = {
        f: rd(os.path.join(T, f))
        for f in ("kprobe_events", "uprobe_events", "dynamic_events",
                  "current_tracer", "set_ftrace_filter", "set_event")}
    out["taint"] = {"raw": rd("/proc/sys/kernel/tainted")}
    try:
        out["taint"]["bits"] = taint_bits(int(out["taint"]["raw"]["text"].strip()))
    except (KeyError, TypeError, ValueError):
        out["taint"]["bits"] = None
    mods = rd("/proc/modules")
    out["modules"] = {"raw_ok": mods["ok"],
                      "names": sorted(l.split()[0] for l in (mods.get("text") or "").splitlines() if l.split()),
                      "count": len((mods.get("text") or "").splitlines())}

    # ---- 4. WHAT THE SURFACE DECLARES IT CARRIES. The byte question, read off the
    # tracepoint's own format file.
    out["tracepoint_formats"] = [tracepoint_fields(s, n) for s, n in EVENTS]

    # ---- 5. THE OBSERVATION PATH, STATTED. The path LIST is computed on the host by
    # parsing the calibration driver's own text and handed in on stdin, so this instrument
    # does not get to choose which surfaces it reports on.
    handed = json.loads(sys.stdin.read() or "[]") if not sys.stdin.isatty() else []
    surfaces = []
    for p in handed:
        st = {"path": p, "exists": os.path.exists(p)}
        if st["exists"]:
            try:
                s = os.stat(p)
                st.update({"mode": oct(s.st_mode & 0o7777), "uid": s.st_uid,
                           "is_dir": os.path.isdir(p),
                           "root_r_ok": os.access(p, os.R_OK),
                           "root_w_ok": os.access(p, os.W_OK)})
            except OSError as exc:
                st["stat_errno"] = exc.errno
        surfaces.append(st)
    out["observation_surfaces"] = surfaces

    # ---- 6. THE POSITIVE CONTROL FOR THIS INSTRUMENT'S OWN READS. Every emptiness above
    # is a claim, and an empty result from a reader that cannot read is the same shape as
    # an empty result from a world with nothing in it. These three reads MUST come back
    # non-empty on any live guest, so a census whose findings are all empty while these are
    # also empty is reporting the reader and not the world.
    out["reader_control"] = {
        "proc_modules_lines": out["modules"]["count"],
        "tracepoint_fields_seen": sum(len(t.get("fields") or []) for t in out["tracepoint_formats"]),
        "block_devices_listed": len(ls("/sys/block").get("entries") or []),
        # named here so the host can resolve the per-cpu stats surfaces without inventing a
        # cpu count: the enumeration's `<c>` component is a real directory listing.
        "tracing_per_cpu": ls(os.path.join(T, "per_cpu")).get("entries") or [],
    }
    print("CENSUS-JSON:" + json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

_W2C_MEMO = {}


def exhibition(case, profile="retake"):
    """One bracketed sequence at the guest: attachment census, THE FROZEN CALIBRATION
    OBSERVER, attachment census. Returns {"before", "observation", "after", ...}.

    MEMOIZED ON BOTH INSTRUMENT DIGESTS AND THE PROFILE, for `guest_probe`'s own reason:
    the exhibition is a property of the box under a stated load and re-driving it per row
    would put a minute of guest work behind every assertion. An edited instrument gets a
    fresh key, so a stale exhibition can never be read as a current one.

    THE SKIP/FAIL SPLIT IS THE ESTABLISHED ONE AND IS NOT SOFTENED: ssh's own 255 is the
    carrier, the auth or the daemon and a row that cannot reach its subject declines to
    state a fact about it; ANY OTHER non-zero code is the instrument failing on the guest,
    which is a FAILURE, because a broken observer that skipped would leave every row below
    green with no subject."""
    calib_d = hashlib.sha256(_CALIB_DRIVER.encode("utf-8")).hexdigest()
    census_d = hashlib.sha256(_CENSUS_DRIVER.encode("utf-8")).hexdigest()
    key = (profile, calib_d, census_d)
    if key in _W2C_MEMO:
        memo = _W2C_MEMO[key]
        if isinstance(memo, str):
            case.skipTest(memo)
        return memo

    def _skip(why):
        _W2C_MEMO[key] = why
        case.skipTest(why)

    ok, why = _carrier_up()
    if not ok:
        _skip("SKIP LONG-BOOT: %s — the exhibition cannot reach its subject" % why)

    gdir = "/tmp/govos-w2c-%s-%s" % (calib_d[:8], census_d[:8])

    def _ship(name, text):
        r = subprocess.run(SSH + ["mkdir -p %s && cat > %s/%s" % (gdir, gdir, name)],
                           input=text, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            _skip("GUEST: could not place %s (rc=%d %s)"
                  % (name, r.returncode, (r.stderr or "")[:160]))

    def _run(argv, stdin_text, marker, what, timeout=900):
        r = subprocess.run(SSH + ["sudo -n python3 %s/%s" % (gdir, argv)],
                           input=stdin_text, capture_output=True, text=True,
                           timeout=timeout)
        if r.returncode == 255:
            err = (r.stderr or "").strip()
            layer = "AUTH" if "denied" in err.lower() else "CARRIER/GUEST"
            _skip("SKIP LONG-BOOT: %s: ssh itself refused (%s)" % (layer, err[:160]))
        if r.returncode != 0:
            case.fail("THE %s FAILED ON THE GUEST (rc=%d). This is the instrument, not the "
                      "lab: stderr=%r stdout=%r"
                      % (what, r.returncode, (r.stderr or "")[-600:],
                         (r.stdout or "")[-400:]))
        line = [ln for ln in r.stdout.splitlines() if ln.startswith(marker)]
        if not line:
            case.fail("the %s produced no %s line: %r" % (what, marker, r.stdout[-500:]))
        return json.loads(line[0][len(marker):])

    _ship("calib.py", _CALIB_DRIVER)
    _ship("census.py", _CENSUS_DRIVER)

    # THE SURFACE LIST HANDED ON STDIN DIFFERS BETWEEN THE TWO CALLS AND THE ARGV DOES NOT.
    # The compared population is the ATTACHMENT fields, which the stdin list does not touch;
    # the surface paths only resolve once the observation has named the validation set, so
    # the BEFORE census is handed nothing and the AFTER census is handed the resolved set.
    # Said here rather than discovered by a reader wondering why the two calls differ.
    subjects = "%s %s" % _CENSUS_SUBJECTS
    before = _run("census.py " + subjects, "[]", "CENSUS-JSON:", "ATTACHMENT CENSUS", 300)
    obs = _run("calib.py %s" % profile, "", "CALIB-JSON:", "CALIBRATION OBSERVER")

    devs = obs.get("validation_set") or {}
    templates, unresolved, structural = observation_surfaces(_CALIB_DRIVER)
    blocks = sorted(r["block"] for r in devs.values() if r.get("block"))
    cpus = (before.get("reader_control") or {}).get("tracing_per_cpu") or ["cpu0"]
    resolved = set()
    for p in templates:
        if "%s" in p:
            resolved.update(p % b for b in blocks)
        elif "<name>" in p:
            resolved.update(p.replace("<name>", n) for n in sorted(devs))
        elif "<c>" in p:
            resolved.update(p.replace("<c>", c) for c in cpus)
        else:
            resolved.add(p)
    # THE SAME SUBJECTS ON BOTH SIDES, or the before/after comparison would be measuring
    # the argument list rather than the path. That the constant is the RIGHT list is not
    # assumed: a row compares it against what the observation actually found, which is C0's
    # own shape — the ground is walked by comparison and never by reading.
    after = _run("census.py " + subjects, json.dumps(sorted(resolved)),
                 "CENSUS-JSON:", "ATTACHMENT CENSUS", 300)

    out = {"before": before, "observation": obs, "after": after,
           "surface_templates": templates, "surface_unresolved": unresolved,
           "surface_structural": structural, "surface_resolved": sorted(resolved),
           "census_subjects": _CENSUS_SUBJECTS, "observed_blocks": blocks,
           "observed_netifs": sorted(r["netif"] for r in devs.values() if r.get("netif")),
           "calib_digest": calib_d, "census_digest": census_d, "profile": profile}
    _W2C_MEMO[key] = out
    return out


def live_shadow_set(case, profile="retake"):
    """The live exhibition turned into a shadow record set, with its provenance attached."""
    ex = exhibition(case, profile)
    decls = intake_by_class(live_pack())
    prov = {"instrument_sha256": ex["observation"]["instrument"]["source_sha256"],
            "profile": ex["profile"], "boot_id": ex["observation"]["boot_id"],
            "machine_id": ex["observation"]["machine_id"],
            "guest": ex["observation"]["hostname"]}
    return ex, decls, shadow_records(ex["observation"], decls, prov)


# =======================================================================================
# THE SYNTHETIC SUBSTRATE FOR W2c's RED WORLDS
#
# SYNTHETIC ON PURPOSE (§A42, and W0g/W2a before this). A red world built by mutating the
# LIVE exhibition could only run when the lab is up, so the one class of row whose whole job
# is to fail would be the first to go silent when the estate most needs it.
#
# AND IT CARRIES THREE LOAD LEVELS AND BOTH DEVICE CLASSES, WHICH THE LIVE `retake` PROFILE
# DOES NOT. Two is C1's FLOOR and never the count (:663), so a substrate with exactly two
# levels could not tell a reading that walks every level from one that hard-codes a pair;
# and `retake` drives the block-primary device only, so a synthetic net window is the only
# way the net class's unestablished-unit path is exercised at all.
# =======================================================================================
def _synthetic_subject(boot="11111111-2222-3333-4444-555555555555", uptime=90000.0):
    return {"boot_id": boot, "machine_id": "0" * 32, "hostname": "synthetic-guest",
            "uptime_s": uptime, "monotonic": uptime, "mem_available_kb": [1000, 1000],
            "readiness_signal": "synthetic", "warm": True}


def _synthetic_window(device, cls, level, kind, arrivals, interrupts, repeat=1):
    """A window carrying EVERY field the live instrument emits, including the ones the
    projection withholds. A substrate missing the withheld fields could not tell a builder
    that ignores them from one that never had them."""
    return {
        "device": device, "device_class": cls, "level": level, "level_kind": kind,
        "repeat": repeat,
        "command": "synthetic load line for %s %s" % (device, level),
        "load_results": [{"argv": ["synthetic"], "command": "synthetic", "rc": 0}],
        # THE DELIVERED FIGURE IS CONSISTENT WITH THE DECLARED BLOCK UNIT, and the net cell
        # reports none at all — the two real shapes. A substrate carrying an arbitrary
        # delivered figure would make the agreement row below fail for the substrate's
        # reason rather than the claim's, which is the defect a control exists to expose.
        "load_size": ({"requested_units": arrivals, "delivered_units": arrivals // 3,
                       "delivered_known": True, "truncated": False} if cls == "block"
                      else {"requested_units": arrivals, "delivered_units": None,
                            "delivered_known": False, "truncated": False}),
        "taking": "synthetic taking clause",
        "open": _synthetic_subject(), "close": _synthetic_subject(uptime=90001.0),
        "subject_stable": True,
        "elapsed_s": 0.5,
        "interrupts": {"count": interrupts, "per_irq_delta": {}, "irq_names": {},
                       "basis": "synthetic"},
        "arrivals": {"count": arrivals, "by_event": {}, "basis": "synthetic"},
        "events_enabled_at_open": ["block:block_rq_issue"],
        "trace_totals": {"dropped": 0, "unattributed": 0, "parsed_lines": arrivals},
        "overrun_delta": 0,
        "rate_arrivals_per_s": arrivals * 2.0,
        "rate_interrupts_per_s": interrupts * 2.0,
    }


def synthetic_observation():
    """A well-formed table: two classes, three load levels on the block device, two on the
    net device, one control each."""
    ws = [_synthetic_window("vblk0", "block", "L0", "CONTROL", 0, 0),
          _synthetic_window("vblk0", "block", "L1", "LOAD", 300, 100),
          _synthetic_window("vblk0", "block", "L2", "LOAD", 3000, 1000),
          _synthetic_window("vblk0", "block", "L3", "LOAD", 6000, 2000),
          _synthetic_window("vnet0", "net", "L0", "CONTROL", 0, 0),
          _synthetic_window("vnet0", "net", "L1", "LOAD", 400, 200),
          _synthetic_window("vnet0", "net", "L2", "LOAD", 3000, 1500)]
    return {"instrument": {"name": "synthetic", "profile": "synthetic",
                           "source_sha256": "0" * 64},
            "hostname": "synthetic-guest", "machine_id": "0" * 32,
            "boot_id": "11111111-2222-3333-4444-555555555555",
            "run_open_subject": _synthetic_subject(),
            "run_close_subject": _synthetic_subject(uptime=90010.0),
            "run_subject_stable": True,
            "establishment": {"divergences": [], "ground_true": True},
            "windows": ws, "limits": []}


def _synthetic_census():
    """A census over a BARE path. Every field a live census carries, every finding empty —
    so a red below is the mutation and never the substrate being malformed."""
    return {
        "instrument": {"name": "synthetic-census", "source_sha256": "0" * 64},
        "subject": {"boot_id": "11111111-2222-3333-4444-555555555555",
                    "machine_id": "0" * 32, "hostname": "synthetic-guest",
                    "uptime_s": 90000.0, "uname": "6.8.0-134-generic"},
        "self_cgroup": "0::/user.slice/user-1000.slice/session-1.scope",
        "asked_about": {"block_devices": ["vblk0"], "interfaces": ["vnet0"]},
        "block_stacking": {"vblk0": {"holders": {"ok": True, "entries": []},
                                     "slaves": {"ok": True, "entries": []},
                                     "devno": {"ok": True, "text": "253:0\n"}}},
        "device_mapper": {"sysfs_present": True,
                          "dmsetup": {"command": "dmsetup ls", "available": True, "rc": 0,
                                      "stdout": "No devices found\n", "stderr": ""}},
        "net_attachments": {"vnet0": {
            "link": {"command": "ip", "available": True, "rc": 0,
                     "stdout": '[{"ifname":"vnet0","qdisc":"fq_codel"}]', "stderr": ""},
            "qdisc": {"command": "tc", "available": True, "rc": 0,
                      "stdout": '[{"kind":"fq_codel","root":true}]', "stderr": ""},
            "filter_egress": {"command": "tc", "available": True, "rc": 0,
                              "stdout": "[]\n", "stderr": ""},
            "filter_ingress": {"command": "tc", "available": True, "rc": 0,
                               "stdout": "[]\n", "stderr": ""}}},
        "netfilter": {k: {"command": k, "available": True, "rc": 0, "stdout": "",
                          "stderr": ""} for k in ("nft", "iptables", "ip6tables")},
        "bpf": {"prog_list": {"command": "bpftool", "available": True, "rc": 0,
                              "stdout": "[]", "stderr": ""},
                "net_list": {"command": "bpftool", "available": True, "rc": 0,
                             "stdout": '[{"xdp":[],"tc":[],"flow_dissector":[],'
                                       '"netfilter":[]}]', "stderr": ""},
                "cgroup_tree": {"command": "bpftool", "available": True, "rc": 0,
                                "stdout": '[{"cgroup":"/sys/fs/cgroup/system.slice/'
                                          'x.service","programs":[{"id":1,"attach_type":'
                                          '"cgroup_inet_egress","name":"sd_fw_egress"}]}]',
                                "stderr": ""},
                "bpffs": {"ok": True, "entries": []}},
        "dynamic_instrumentation": {
            "kprobe_events": {"ok": True, "text": ""},
            "uprobe_events": {"ok": True, "text": ""},
            "dynamic_events": {"ok": True, "text": ""},
            "current_tracer": {"ok": True, "text": "nop\n"},
            "set_ftrace_filter": {"ok": True, "text": "#### all functions enabled ####\n"},
            "set_event": {"ok": True, "text": ""}},
        "taint": {"raw": {"ok": True, "text": "0\n"}, "bits": []},
        "modules": {"raw_ok": True, "names": ["virtio_net"], "count": 1},
        "tracepoint_formats": [{"event": "block:block_rq_issue", "readable": True,
                                "fields": ["dev", "bytes"],
                                "byte_bearing_fields": ["bytes"]}],
        "observation_surfaces": [],
        "reader_control": {"proc_modules_lines": 1, "tracepoint_fields_seen": 2,
                           "block_devices_listed": 1, "tracing_per_cpu": ["cpu0"]},
    }


def synthetic_census_pair():
    return (_synthetic_census(), _synthetic_census())


def synthetic_history_and_live():
    """A driver history in which every driver is frozen, plus one that was AUTHORED across
    two commits inside its own movement and settled — the shape `_CALIB_DRIVER` really has,
    so the reading's tolerance for authoring is exercised and not merely intended."""
    hist = {"_A_DRIVER": [(W2_ERA_COMMIT, "a" * 64), ("c1", "a" * 64), ("c2", "a" * 64)],
            "_B_DRIVER": [("c1", "b" * 64), ("c2", "d" * 64), ("c3", "d" * 64)]}
    live = {"_A_DRIVER": "a" * 64, "_B_DRIVER": "d" * 64}
    return hist, live


# ------------------------------------------------------------------ ONE HOME PER MUTATION
def _p_driver_moved_across_the_era(w):
    w["live"]["_A_DRIVER"] = "9" * 64


def _p_driver_edited_after_settling(w):
    w["history"]["_B_DRIVER"] = [("c1", "b" * 64), ("c2", "d" * 64), ("c3", "e" * 64),
                                 ("c4", "d" * 64)]


def _p_grade_says_per_interrupt(w):
    for r in w["records"]:
        r["grade"] = "per-interrupt"


def _p_bound_of_one(w):
    for r in w["records"]:
        r["bound"]["max_arrivals"] = 1


def _p_one_record_per_arrival(w):
    """The grade LABEL is untouched and the record set is one per arrival. This is the
    mutation the name-check alone cannot see, and the reason the ratio is asked too."""
    src = [r for r in w["records"] if r["kind"] == "SHADOW-COVERING-RECORD"][0]
    out = []
    for _ in range(src["observed_window"]["arrivals_in_window"]):
        r = copy.deepcopy(src)
        r["covers"]["arrival_count"] = 1
        r["sequence"] = {"index": 1, "of": 1}
        out.append(r)
    w["records"] = out


def _p_records_outnumber_interrupts(w):
    src = [r for r in w["records"] if r["kind"] == "SHADOW-COVERING-RECORD"][0]
    n = src["observed_window"]["interrupts_in_window"] + 1
    w["records"] = [copy.deepcopy(src) for _ in range(n)]


def _p_block_device_gains_a_holder(w):
    w["census"][1]["block_stacking"]["vblk0"]["holders"]["entries"] = ["dm-0"]


def _p_interface_gains_an_xdp_program(w):
    w["census"][1]["net_attachments"]["vnet0"]["link"]["stdout"] = \
        '[{"ifname":"vnet0","xdp":{"prog":{"id":7}}}]'


def _p_interface_gains_a_tc_filter(w):
    w["census"][1]["net_attachments"]["vnet0"]["filter_ingress"]["stdout"] = \
        '[{"kind":"matchall","options":{"actions":[{"kind":"gact","control_action":' \
        '{"type":"drop"}}]}}]'


def _p_netfilter_ruleset_appears(w):
    w["census"][1]["netfilter"]["nft"]["stdout"] = "table inet filter { chain in { } }"


def _p_bpf_attaches_to_the_netdev(w):
    w["census"][1]["bpf"]["net_list"]["stdout"] = \
        '[{"xdp":[{"devname":"vnet0","id":3}],"tc":[],"flow_dissector":[],"netfilter":[]}]'


def _p_cgroup_bpf_reaches_the_load(w):
    w["census"][1]["bpf"]["cgroup_tree"]["stdout"] = \
        '[{"cgroup":"/sys/fs/cgroup/user.slice","programs":[{"id":4,"attach_type":' \
        '"cgroup_inet_egress","name":"drop_all"}]}]'


def _p_a_kprobe_is_placed(w):
    w["census"][1]["dynamic_instrumentation"]["kprobe_events"]["text"] = \
        "p:probe/virtblk_request virtblk_request\n"


def _p_the_tracer_is_not_nop(w):
    w["census"][1]["dynamic_instrumentation"]["current_tracer"]["text"] = "function_graph\n"


def _p_the_kernel_is_tainted_out_of_tree(w):
    w["census"][1]["taint"]["bits"] = ["OOT_MODULE"]


def _p_the_census_moved_across_the_observation(w):
    """THE SHARPEST OF THEM. The path's attachment state is not the same on either side of
    the observation, which is what interposing WOULD look like."""
    w["census"][1]["modules"]["names"] = ["virtio_net", "an_interposing_module"]


#: code -> [(name, planter)]. PLANT EACH ALONE rather than one mutant carrying everything:
#: the all-at-once form can pass with two clauses wired to one defect, and W2a already paid
#: for discovering that a maximal mutant demands a world that cannot exist.
W2C_DEFECT_PLANTERS = {
    "DRIVER-MOVED": [
        ("a driver that moved across the era", _p_driver_moved_across_the_era),
        ("a driver edited after settling", _p_driver_edited_after_settling)],
    "PER-INTERRUPT-GRADE": [
        ("the grade says per-interrupt", _p_grade_says_per_interrupt),
        ("a bound of one", _p_bound_of_one),
        ("one record per arrival, label untouched", _p_one_record_per_arrival),
        ("records outnumber interrupts", _p_records_outnumber_interrupts)],
    "WRITE-CAPABLE-ATTACHMENT": [
        ("a stacked block target", _p_block_device_gains_a_holder),
        ("an XDP program on the interface", _p_interface_gains_an_xdp_program),
        ("a tc filter with a drop action", _p_interface_gains_a_tc_filter),
        ("a netfilter ruleset", _p_netfilter_ruleset_appears),
        ("a BPF program on the netdev", _p_bpf_attaches_to_the_netdev),
        ("a cgroup BPF program over the load's slice", _p_cgroup_bpf_reaches_the_load),
        ("a kprobe on the block path", _p_a_kprobe_is_placed),
        ("a tracer other than nop", _p_the_tracer_is_not_nop),
        ("an out-of-tree module", _p_the_kernel_is_tainted_out_of_tree),
        ("the census moved across the observation",
         _p_the_census_moved_across_the_observation)],
}




# ------------------------------------------------------- ONE PLACE A W2c ROW READS ITS WORLD
_W2C_WORLD_MEMO = {}


def w2c_world(case, profile="retake"):
    """{observation, declarations, records, census, history, live, exhibition} — everything
    a W2c row reads, assembled in ONE place.

    ONE HOME so a red world can plant it. Every row below reads through here, so the
    negative-result harness swaps a single memo entry and the REAL rows then run against
    the planted world — no predicate is restated anywhere, and a red world that
    re-implements the assertion it is testing proves only that two copies agree."""
    key = ("world", profile,
           hashlib.sha256(_CALIB_DRIVER.encode("utf-8")).hexdigest(),
           hashlib.sha256(_CENSUS_DRIVER.encode("utf-8")).hexdigest())
    if key in _W2C_WORLD_MEMO:
        return _W2C_WORLD_MEMO[key]
    ex = exhibition(case, profile)
    decls = w2c_law()                     # [FLIP — EP-29 W3a §A57; the note is on `w2c_law`]
    obs = ex["observation"]
    prov = {"instrument_sha256": obs["instrument"]["source_sha256"],
            "profile": ex["profile"], "boot_id": obs["boot_id"],
            "machine_id": obs["machine_id"], "guest": obs["hostname"]}
    hist = driver_history()
    world = {"exhibition": ex, "observation": obs, "declarations": decls,
             "records": shadow_records(obs, decls, prov),
             "census": [ex["before"], ex["after"]],
             "history": hist, "live": drivers_at("HEAD"),
             "live_working_tree": _live_driver_digests(),
             # THE LIVE WORLD'S LICENSED-LOAD REGISTER. Named on the world rather than
             # reached for inside a row, so a planted world can carry a DIFFERENT register
             # and the shipped rows cannot tell the difference structurally.
             "licensed_loads": THE_LICENSED_OUT_OF_TREE_LOADS}
    _W2C_WORLD_MEMO[key] = world
    return world


def _live_driver_digests():
    """The digests of the driver strings THIS MODULE HOLDS IN MEMORY. Distinct from
    `drivers_at("HEAD")`, which reads git: the two disagree exactly when the working tree
    has an uncommitted edit, and a freeze claim that could not tell those apart would be
    satisfied by a commit that had not happened yet."""
    out = {}
    for name in VALIDATION_DRIVERS:
        value = globals().get(name)
        if isinstance(value, str):
            out[name] = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return out


def read_world(w):
    """THE READING, over whatever world it is given.

    THE WORLD CARRIES ITS OWN LICENSED-LOAD REGISTER, so the reading is one function over
    two worlds rather than two readings. The synthetic world declares ZERO licensed loads
    and therefore still demands `taint == 0`; the live world declares W3b's recorded load
    and therefore demands the delta form. Neither world gets a different predicate."""
    return shadow_defects(w["records"], w["declarations"], w["observation"],
                          tuple(w["census"]), w["live"], w["history"],
                          w.get("licensed_loads") or ())


def synthetic_world():
    """The synthetic substrate in the SAME SHAPE as the live world, so the harness can plant
    one where the other stood and the real rows cannot tell the difference structurally."""
    obs = synthetic_observation()
    decls = w2c_law()                     # [FLIP — EP-29 W3a §A57; the note is on `w2c_law`]
    hist, live = synthetic_history_and_live()
    return {"exhibition": {"profile": "synthetic",
                           "surface_templates": {"/proc/interrupts": ["READ-FOR-DATA"],
                                                 "/sys/kernel/tracing/tracing_on":
                                                     ["CONTROL-WRITE"]},
                           "surface_unresolved": [], "surface_structural": [],
                           "surface_resolved": ["/proc/interrupts"],
                           "census_subjects": _CENSUS_SUBJECTS,
                           "observed_blocks": ["vda", "vdb"],
                           "observed_netifs": ["ens3"],
                           "before": _synthetic_census(), "after": _synthetic_census(),
                           "observation": obs},
            "observation": obs, "declarations": decls,
            "records": shadow_records(obs, decls, {"synthetic": True}),
            "census": list(synthetic_census_pair()),
            "history": hist, "live": live,
            "live_working_tree": {"_A_DRIVER": "a" * 64, "_B_DRIVER": "d" * 64},
            # STATED, NEVER INHERITED FROM A DEFAULT. This substrate is a world with ZERO
            # licensed out-of-tree loads — W2c's own world — so `taint == 0` is the correct
            # reading of it and every taint plant below still REDS against it exactly as it
            # did before the restatement. Writing the empty register out loud is what lets
            # a reader see WHICH world this is instead of inferring it.
            "licensed_loads": ()}


def synthetic_world_with_a_licensed_load():
    """THE SUBSTRATE FOR THE DELTA FORM: the same synthetic world, moved to the shape the
    LIVE world now has — one recorded licensed load, and a taint word holding exactly the
    bits that load's record accounts for.

    IT EXISTS BECAUSE `synthetic_world()` CANNOT EXERCISE THE RULE THAT WAS JUST WRITTEN.
    Its register is empty, so every row run against it exercises clause (1) and clause (2)
    never fires. A restatement whose only control is the world it was restated AWAY FROM
    has not been driven at all — which is §A64's whole complaint, arriving here as a
    substrate question rather than as a regex question."""
    w = synthetic_world()
    w["licensed_loads"] = THE_LICENSED_OUT_OF_TREE_LOADS
    for c in w["census"]:
        c["taint"] = {"raw": {"ok": True, "text": "12288\n"},
                      "bits": ["OOT_MODULE", "UNSIGNED_MODULE"]}
        c["modules"] = {"raw_ok": True, "names": ["govshim", "virtio_net"], "count": 2}
    w["exhibition"]["before"], w["exhibition"]["after"] = w["census"]
    return w


def _run_w2c_against(planted, cls, meth):
    """Run a REAL W2c row against a PLANTED world, through unittest's own machinery, so
    what is measured is the row that ships and not a paraphrase of it."""
    key = ("world", "retake",
           hashlib.sha256(_CALIB_DRIVER.encode("utf-8")).hexdigest(),
           hashlib.sha256(_CENSUS_DRIVER.encode("utf-8")).hexdigest())
    sentinel = object()
    saved = _W2C_WORLD_MEMO.get(key, sentinel)
    _W2C_WORLD_MEMO[key] = planted
    try:
        return unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(cls(meth))
    finally:
        if saved is sentinel:
            _W2C_WORLD_MEMO.pop(key, None)
        else:
            _W2C_WORLD_MEMO[key] = saved


# =======================================================================================
# THE W2c ROWS
# =======================================================================================
class TheW2cExhibitionRanAtTheGuestAndOnTheBytesWeSent(unittest.TestCase):
    """NON-VACUITY FOR EVERY W2c ROW BELOW. A shadow record set built from an observation
    nobody drove is the wrong-reference class arriving in an exhibition, so the subject is
    proven present before anything is asserted about it."""

    def test_the_exhibition_ran_in_the_GUEST_at_the_pinned_kernel(self):
        w = w2c_world(self)
        self.assertEqual(w["observation"]["uname"], "6.8.0-134-generic")
        self.assertNotEqual(w["observation"]["machine_id"], "")
        self.assertEqual(w["observation"]["hostname"], "gov-lab")
        self.assertEqual(w["observation"]["uid"], 0,
                         "the observer must be privileged in its INVOCATION — ADDENDUM 6 "
                         "§4 attaches the privilege to the observer and never to the "
                         "surface")

    def test_the_guest_ran_THE_BYTES_THIS_FILE_HOLDS(self):
        """The guest hashes what it received and reports the digest; this compares it
        against the bytes the file holds. Without it the table could have come from any
        instrument on that box."""
        w = w2c_world(self)
        self.assertEqual(w["observation"]["instrument"]["source_sha256"],
                         hashlib.sha256(_CALIB_DRIVER.encode("utf-8")).hexdigest())
        for c in w["census"]:
            self.assertEqual(c["instrument"]["source_sha256"],
                             hashlib.sha256(_CENSUS_DRIVER.encode("utf-8")).hexdigest())

    def test_the_bracket_is_a_BRACKET_and_not_two_readings_in_one_direction(self):
        """The censuses must straddle the observation in time, or "identical either side"
        is a claim about two readings taken the same side of it."""
        w = w2c_world(self)
        before, after = w["census"]
        obs = w["observation"]
        self.assertLessEqual(before["subject"]["uptime_s"],
                             obs["run_open_subject"]["uptime_s"])
        self.assertGreaterEqual(after["subject"]["uptime_s"],
                                obs["run_close_subject"]["uptime_s"])

    def test_the_SUBJECT_did_not_drop_between_the_two_censuses(self):
        """A spliced bracket is two populations wearing one label, exactly as a spliced
        window is. Checked at the identity and not at the numbers."""
        w = w2c_world(self)
        before, after = w["census"]
        self.assertEqual(before["subject"]["boot_id"], after["subject"]["boot_id"])
        self.assertEqual(before["subject"]["machine_id"], after["subject"]["machine_id"])
        self.assertEqual(before["subject"]["boot_id"], w["observation"]["boot_id"])
        self.assertTrue(w["observation"]["run_subject_stable"])

    def test_the_ground_is_TRUE_and_the_run_left_the_guest_as_it_found_it(self):
        w = w2c_world(self)
        self.assertEqual(w["observation"]["establishment"]["divergences"], [])
        self.assertTrue(w["observation"]["establishment"]["ground_true"])
        self.assertTrue(w["observation"]["restore_verified"],
                        "the tracing state this run touched was not put back, so a later "
                        "run would read this run's residue as the world")

    def test_the_census_SUBJECTS_are_the_devices_the_observation_FOUND(self):
        """The census argv is a CONSTANT so both sides are comparable; that the constant is
        right is COMPARED and never read — C0's own shape."""
        w = w2c_world(self)
        ex = w["exhibition"]
        self.assertEqual(",".join(ex["observed_blocks"]), ex["census_subjects"][0])
        self.assertEqual(",".join(ex["observed_netifs"]), ex["census_subjects"][1])

    def test_the_census_reader_can_READ_and_a_zero_is_therefore_about_the_world(self):
        """THE POSITIVE CONTROL FOR EVERY EMPTINESS BELOW. An empty result from a reader
        that cannot read has the same shape as an empty result from a bare path, and the
        findings this class supports are almost all emptinesses."""
        for c in w2c_world(self)["census"]:
            rc = c["reader_control"]
            self.assertGreater(rc["proc_modules_lines"], 0)
            self.assertGreater(rc["tracepoint_fields_seen"], 0)
            self.assertGreater(rc["block_devices_listed"], 0)


class TheValidationDriversAreByteIdenticalAcrossTheWholeOfW2(unittest.TestCase):
    """C4's FIRST CLAUSE. One comparison spanning all three movements, and then the stronger
    one the plan did not ask for."""

    def test_the_PLANS_OWN_COMPARISON_before_W2a_against_after_W2c(self):
        """Every driver that existed before W2a carries the same bytes now."""
        era = drivers_at(W2_ERA_COMMIT)
        now = drivers_at("HEAD")
        self.assertTrue(era, "the era pin resolved to a file holding no drivers at all")
        for name, digest in sorted(era.items()):
            self.assertEqual(now.get(name), digest,
                             "%s moved between the era before W2a and now" % name)

    def test_the_working_tree_agrees_with_the_commit(self):
        """`drivers_at("HEAD")` reads git and this module holds the working tree. The two
        disagree exactly when an edit is uncommitted, and a freeze claim that could not tell
        those apart would be satisfied by a commit that had not happened yet."""
        w = w2c_world(self)
        self.assertEqual(w["live_working_tree"], drivers_at("HEAD"))

    def test_NO_DRIVER_LEFT_ITS_SETTLED_DIGEST_at_any_recorded_point(self):
        """THE STRONGER COMPARISON, and the reason it is here: an endpoint comparison cannot
        see a driver that moved and moved back, and it has NO POPULATION AT ALL for a driver
        born inside W2 — it passes for the wrong reason. This walks every commit."""
        w = w2c_world(self)
        reds, _ = driver_freeze_defects(w["history"], w["live"])
        self.assertEqual(reds, [])

    def test_the_history_covers_the_era_and_EVERY_commit_since(self):
        """A history with one point would satisfy the row above by having nothing to
        compare. Non-vacuity for the walk itself."""
        w = w2c_world(self)
        for name, points in sorted(w["history"].items()):
            self.assertGreaterEqual(len(points), 1)
        self.assertGreaterEqual(
            max(len(p) for p in w["history"].values()), 3,
            "the driver history is too short to be a walk over W2's commits")
        first = [n for n, p in w["history"].items() if p[0][0] == W2_ERA_COMMIT]
        self.assertGreaterEqual(len(first), 2,
                                "at least the two pre-W2a drivers must appear at the era")

    def test_the_driver_AUTHORED_INSIDE_W2a_is_reported_and_not_hidden(self):
        """`_CALIB_DRIVER` was born at W2a and held three digests while it was being
        written — W2a's own entry names them as its three runs. A thing being AUTHORED is
        not a thing that MOVED, and the distinction is reported rather than silently
        absorbed, because a reading that absorbed it could absorb a real edit too."""
        w = w2c_world(self)
        _, authored = driver_freeze_defects(w["history"], w["live"])
        born = [n for n, p in w["history"].items() if p[0][0] != W2_ERA_COMMIT]
        for name in born:
            self.assertNotIn(name, drivers_at(W2_ERA_COMMIT),
                             "%s is claimed born inside W2 and exists at the era" % name)
        self.assertIsInstance(authored, dict)

    def test_the_era_pin_reports_a_DIFFERENCE_when_there_is_one(self):
        """THE INSTRUMENT'S OWN NEGATIVE-RESULT TEST. A comparison that cannot report
        inequality is not a comparison, and every row above rests on this one."""
        self.assertNotIn("_CALIB_DRIVER", drivers_at(W2_ERA_COMMIT))
        self.assertIn("_CALIB_DRIVER", drivers_at(W2B_ERA_COMMIT))
        self.assertNotEqual(
            era_pin.blob_at(W2_ERA_COMMIT, "tests/test_ep29.py"),
            era_pin.blob_at(W2B_ERA_COMMIT, "tests/test_ep29.py"))

    def test_the_freeze_reading_can_emit_BOTH_of_its_reasons(self):
        """The reading's own positive control. Two mutations, each alone."""
        hist, live = synthetic_history_and_live()
        self.assertEqual(driver_freeze_defects(hist, live)[0], [])
        moved = dict(live, _A_DRIVER="9" * 64)
        self.assertTrue(driver_freeze_defects(hist, moved)[0])
        h2 = dict(hist, _B_DRIVER=[("c1", "b" * 64), ("c2", "d" * 64), ("c3", "e" * 64),
                                   ("c4", "d" * 64)])
        self.assertTrue(driver_freeze_defects(h2, live)[0])


class TheObservationPathIsEnumeratedAsSurfaces(unittest.TestCase):
    """C4's THIRD CLAUSE. The observation path enumerated, each surface with its use."""

    def test_the_enumeration_is_COMPUTED_from_the_instruments_own_text(self):
        w = w2c_world(self)
        surfaces = w["exhibition"]["surface_templates"]
        self.assertGreater(len(surfaces), 10,
                           "an enumeration this short is a walker that resolved nothing")
        for path, kinds in surfaces.items():
            self.assertTrue(path.startswith("/"))
            self.assertTrue(set(kinds) <= {"READ-FOR-DATA", "CONTROL-WRITE"})

    def test_the_walker_reports_EVERYTHING_it_could_not_resolve(self):
        """A surface enumerator that silently omits the sites it does not understand is the
        filter-that-cannot-match defect with a longer output."""
        w = w2c_world(self)
        self.assertEqual(w["exhibition"]["surface_unresolved"], [])
        classes = sorted({s["class"] for s in w["exhibition"]["surface_structural"]})
        self.assertEqual(classes, ["INSTRUMENT-READS-ITS-OWN-SOURCE",
                                   "WRAPPER-INDIRECTION"],
                         "a structural class appeared that this file does not name")

    def test_the_walker_FINDS_A_SURFACE_a_shorter_walker_would_MISS(self):
        """The enumerator's own negative-result test, and it is not hypothetical: the first
        version resolved neither tuple-unpacked bindings nor loop variables, and returned a
        confident enumeration missing eleven real sysfs surfaces."""
        surfaces, unres, _ = observation_surfaces(_CALIB_DRIVER)
        self.assertIn("/sys/kernel/tracing/per_cpu/<c>/stats", surfaces)   # tuple unpacking
        self.assertIn("/sys/kernel/tracing/buffer_size_kb", surfaces)      # a loop variable
        self.assertIn("/sys/bus/virtio/devices/<name>/status", surfaces)   # a local expr
        self.assertEqual(unres, [])
        # A path expression the walker CANNOT reduce must be REPORTED and not dropped. The
        # unreducible case is a TOP-LEVEL bare name, not a join component: inside a join an
        # unknown name is a device placeholder and resolving it to a template is the right
        # answer, which this control asserts as well so the two cases stay distinguished.
        thin, thin_unres, _ = observation_surfaces(
            "import os\nT='/sys/kernel/tracing'\n"
            "def f(y):\n    return ls(y)\n"
            "def g(x):\n    return rd(os.path.join(T, x))\n")
        self.assertEqual(thin, {"/sys/kernel/tracing/<x>": ["READ-FOR-DATA"]})
        self.assertEqual(len(thin_unres), 1,
                         "a path the walker cannot reduce must be REPORTED, not dropped")
        self.assertEqual(thin_unres[0]["line"], 4)

    def test_every_enumerated_surface_RESOLVES_and_was_STATTED_at_the_guest(self):
        w = w2c_world(self)
        after = w["census"][1]
        statted = {s["path"]: s for s in after["observation_surfaces"]}
        self.assertEqual(sorted(statted), w["exhibition"]["surface_resolved"])
        missing = sorted(p for p, s in statted.items() if not s["exists"])
        # THE ONLY ABSENCES ALLOWED ARE THE CLASS-SPECIFIC SUBDIRECTORIES: a net device has
        # no `block` child and a block device has no `net` child. The instrument guards both
        # with isdir, so their absence is the world being consistent and not a gap.
        for p in missing:
            self.assertTrue(p.endswith("/block") or p.endswith("/net"),
                            "an enumerated surface does not exist on the guest: %s" % p)

    def test_the_WRITTEN_surfaces_are_NAMED_and_are_tracefs_CONTROL_files(self):
        """THE SPLIT SAID OUT LOUD RATHER THAN SOFTENED. The observation path contains
        WRITES, and an enumeration reporting "read-only" over a set containing writes would
        be a sentence with a colon in it. Every written path is a tracefs control file that
        arms or clears STATIC tracepoints; none of them is on the I/O path, which is what
        C4's red world is actually about."""
        w = w2c_world(self)
        written = sorted(p for p, k in w["exhibition"]["surface_templates"].items()
                         if "CONTROL-WRITE" in k)
        self.assertEqual(written, ["/sys/kernel/tracing/current_tracer",
                                   "/sys/kernel/tracing/set_event",
                                   "/sys/kernel/tracing/trace",
                                   "/sys/kernel/tracing/tracing_on"])

    def test_NO_enumerated_surface_is_a_BLOCK_DEVICE_NODE_or_a_SOCKET(self):
        """The I/O path itself is never opened by the observation. The load opens
        /dev/vda; the OBSERVER opens metadata and a ring buffer."""
        w = w2c_world(self)
        for path in w["exhibition"]["surface_templates"]:
            self.assertFalse(path.startswith("/dev/"), path)
        for path in w["exhibition"]["surface_resolved"]:
            self.assertFalse(path.startswith("/dev/"), path)

    def test_the_CENSUS_instrument_holds_NO_write_call_site(self):
        """A read-only instrument that is read-only by promise is not a control. This is
        the promise turned into a check over the instrument's own text."""
        self.assertEqual(write_call_sites(_CENSUS_DRIVER), [])
        self.assertTrue(write_call_sites(_CALIB_DRIVER),
                        "the write detector finds nothing in an instrument that DOES "
                        "write, so its empty answer above would mean nothing")

    def test_the_ARRIVAL_SURFACES_declare_a_BYTE_FIELD_that_this_pass_does_NOT_read(self):
        """THE GAP, MEASURED AT THE SURFACE RATHER THAN ASSERTED. DEV-LAW-INTAKE says a
        covering record carries a BYTE TOTAL; the surfaces declare byte-bearing fields and
        the FROZEN instrument parses none of them. Both halves are checked here so the
        shadow record's null byte total is a bounded gap and not an open one."""
        w = w2c_world(self)
        fmts = {f["event"]: f for f in w["census"][1]["tracepoint_formats"]}
        self.assertIn("bytes", fmts["block:block_rq_issue"]["byte_bearing_fields"])
        self.assertIn("len", fmts["net:net_dev_queue"]["byte_bearing_fields"])
        self.assertEqual(fmts["irq:irq_handler_entry"]["byte_bearing_fields"], [])
        for field in ("bytes", "len="):
            self.assertNotIn(field, _CALIB_DRIVER.split("def read_trace")[1]
                             .split("def window")[0],
                             "the frozen instrument parses %r after all, so the byte total "
                             "should not be declared unestablished" % field)


class TheShadowRecordsAreBuiltFromObservationALONE(unittest.TestCase):
    """C4's CENTRAL CLAUSE, exhibited STRUCTURALLY rather than promised. The builder is
    built UNABLE to read the load's own report or a clock, so "from observation alone" is a
    property of the code and not an undertaking in a docstring."""

    def test_the_projection_WITHHOLDS_the_loads_own_report(self):
        w = w2c_world(self)
        loaded = [x for x in w["observation"]["windows"] if x["level_kind"] == "LOAD"]
        self.assertTrue(loaded, "no loaded window: the projection has nothing to withhold")
        for win in loaded:
            proj = observation_only(win)
            for field in ("command", "load_results", "load_size", "taking"):
                self.assertIn(field, win, "the substrate does not carry %r, so withholding "
                                          "it proves nothing" % field)
                self.assertNotIn(field, proj)

    def test_the_projection_WITHHOLDS_every_clock(self):
        """DEV-LAW-INTAKE makes closers EVENT-BASED and refuses a time bound of any kind.
        Forbidden versus unable, and this estate's answer is always unable."""
        w = w2c_world(self)
        for win in w["observation"]["windows"]:
            proj = observation_only(win)
            for field in ("elapsed_s", "rate_arrivals_per_s", "rate_interrupts_per_s"):
                self.assertIn(field, win)
                self.assertNotIn(field, proj)

    def test_the_record_set_is_UNCHANGED_when_the_withheld_fields_are_STRIPPED(self):
        """THE DIFFERENTIAL. If the builder read any withheld field, deleting them all would
        change the answer or raise. It does neither."""
        w = w2c_world(self)
        thin = copy.deepcopy(w["observation"])
        for win in thin["windows"]:
            for field in _WITHHELD_FIELDS:
                win.pop(field, None)
        a = shadow_records(w["observation"], w["declarations"])
        b = shadow_records(thin, w["declarations"])
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        self.assertTrue(a, "an empty record set is trivially unchanged")

    def test_MOVING_the_delivered_figure_does_not_move_a_single_record(self):
        """The sharpest of the withheld fields, planted rather than argued: `delivered_units`
        is the figure W2b's block unit was derived AGAINST, so a builder that could see it
        could reproduce the right answer without observing anything."""
        w = w2c_world(self)
        lying = copy.deepcopy(w["observation"])
        for win in lying["windows"]:
            if "load_size" in win:
                win["load_size"]["delivered_units"] = 999999
                win["load_size"]["requested_units"] = 1
        self.assertEqual(
            json.dumps(shadow_records(lying, w["declarations"]), sort_keys=True),
            json.dumps(shadow_records(w["observation"], w["declarations"]), sort_keys=True))

    def test_MOVING_the_arrival_count_DOES_move_the_records(self):
        """The differential's own negative control. A builder that ignored EVERYTHING would
        pass both rows above, and the two are indistinguishable without this one."""
        w = w2c_world(self)
        moved = copy.deepcopy(w["observation"])
        for win in moved["windows"]:
            if win["level_kind"] == "LOAD":
                win["arrivals"]["count"] = win["arrivals"]["count"] + 1
        self.assertNotEqual(
            json.dumps(shadow_records(moved, w["declarations"]), sort_keys=True),
            json.dumps(shadow_records(w["observation"], w["declarations"]), sort_keys=True))

    def test_the_shadow_set_is_EVIDENCE_and_no_product_record_was_appended(self):
        """ADDENDUM 7's not-claimed block: the intake ENGINE is W3's shim contract, so
        NOTHING lands in a store here. Checked at the record and at the world."""
        w = w2c_world(self)
        for r in w["records"]:
            self.assertTrue(r["evidence_not_record"])
            self.assertTrue(r["kind"].startswith("SHADOW-"))
        world = _World()
        appended = [rec for rec in world.store.all()
                    if rec.get("action") in ("DEVICE-INPUT-RECORD", "DECLARE-INTAKE")
                    and rec.get("actor") != "PC_RUNTIME"]
        self.assertEqual(appended, [],
                         "a record under this law exists that the FOUNDING did not place, "
                         "and W2c appends none — the intake ENGINE is W3's shim contract")


class TheShadowRecordsAreAtTheDECLAREDGrade(unittest.TestCase):
    """The grade is READ OUT OF THE LANDED LAW and compared, never restated here. A row
    holding its own copy of `window`, `6144` and `3` would pass while the law said something
    else, which is the wrong-reference class at the last possible moment."""

    def test_the_reading_finds_NO_red_world_in_the_live_exhibition(self):
        """[RESTATED — W2c-TAINT-BIND, board :823 / :828, a NEW UNIT under §10. THE ROW'S
        NAME AND ITS ASSERTION ARE BOTH UNCHANGED and that is the finding worth recording:
        this row never named the proxy. It went red because `read_world` reached
        `WRITE-CAPABLE-ATTACHMENT` through a taint clause that had no notion of a licensed
        load. The cure landed one level down, in the reading, and this row inherited it —
        which is what a definitive-before-derivative fix looks like when the derivative
        needed no edit at all.]"""
        w = w2c_world(self)
        self.assertEqual(read_world(w), [])

    def test_every_declared_class_is_the_one_the_law_declares(self):
        w = w2c_world(self)
        self.assertEqual(sorted(w["declarations"]), sorted(THE_DECLARED_INTAKE_CLASSES))
        for cls, decl in sorted(w["declarations"].items()):
            self.assertEqual(decl["grade"], "window")
            self.assertGreater(decl["max_arrivals"]["value"], 1,
                               "the law forbids a bound of one, at any load and for any "
                               "class")

    def test_every_record_carries_the_LAWS_grade_bound_window_and_citation(self):
        w = w2c_world(self)
        covering = [r for r in w["records"] if r["kind"] == "SHADOW-COVERING-RECORD"]
        self.assertTrue(covering, "no covering record: the grade claim has no subject")
        for r in covering:
            decl = w["declarations"][r["device"]["device_class"]]
            self.assertEqual(r["grade"], decl["grade"])
            self.assertEqual(r["bound"]["max_arrivals"], decl["max_arrivals"]["value"])
            self.assertEqual(r["window"], decl["window"])
            self.assertEqual(r["intake"], decl["intake"])
            self.assertEqual(r["law_cited"], "DEV-LAW-INTAKE")

    def test_the_record_COUNT_is_the_laws_own_arithmetic_and_not_a_constant(self):
        """ceil(arrivals / cap), recomputed per window from the observation. Checked as
        arithmetic rather than as "one per window", because one per window is what this
        table happens to produce and not what the law says."""
        w = w2c_world(self)
        for row in records_per_interrupt(w["observation"], w["records"]):
            cap = w["declarations"][row["device_class"]]["max_arrivals"]["value"]
            self.assertEqual(row["records"],
                             int(math.ceil(row["arrivals"] / float(cap))))

    def test_the_arithmetic_produces_MORE_THAN_ONE_record_when_the_cap_is_exceeded(self):
        """The row above would be satisfied by a constant 1 on any table where no window
        exceeds its cap — which is every window this lab has driven. Driven on synthetic
        substrate so the arithmetic is exercised rather than assumed."""
        obs = synthetic_observation()
        decls = w2c_law()                     # [FLIP — EP-29 W3a §A57; the note is on `w2c_law`]
        cap = decls["block"]["max_arrivals"]["value"]      # from the law, never a literal
        for win in obs["windows"]:
            if win["level_kind"] == "LOAD" and win["device_class"] == "block":
                win["arrivals"]["count"] = cap * 2 + 1
        rows = records_per_interrupt(obs, shadow_records(obs, decls))
        block = [r for r in rows if r["device_class"] == "block"]
        self.assertTrue(block)
        for r in block:
            self.assertEqual(r["records"], 3)

    def test_the_covered_counts_SUM_to_the_arrivals_observed(self):
        """A covering record set that covers less than it observed makes an arrival
        invisible, which is the whole thing the never-clause is written to avoid costing."""
        w = w2c_world(self)
        by_window = {}
        for r in w["records"]:
            if r["kind"] != "SHADOW-COVERING-RECORD":
                continue
            ow = r["observed_window"]
            key = (r["device"]["observed_alias"], ow["level"], ow["repeat"])
            by_window.setdefault(key, [0, ow["arrivals_in_window"]])
            by_window[key][0] += r["covers"]["arrival_count"]
        self.assertTrue(by_window)
        for key, (covered, observed) in sorted(by_window.items()):
            self.assertEqual(covered, observed, key)

    def test_the_BLOCK_admitted_act_count_is_DERIVED_from_arrivals_and_the_declared_unit(self):
        w = w2c_world(self)
        block = [r for r in w["records"] if r["device"]["device_class"] == "block"]
        self.assertTrue(block)
        unit = w["declarations"]["block"]["arrivals_per_admitted_act"]["value"]
        for r in block:
            self.assertEqual(r["admitted_acts"]["unit"], unit)
            self.assertEqual(r["admitted_acts"]["value"],
                             r["covers"]["arrival_count"] // unit)

    def test_a_NET_record_states_NO_admitted_act_count_and_carries_the_laws_own_reason(self):
        """W2b declared the net per-act unit UNESTABLISHED for two independent reasons. A
        shadow record that filled it in would be the number a careless pass writes, arriving
        one layer further out. Driven on synthetic substrate because the live `retake`
        profile drives the block-primary device only."""
        obs = synthetic_observation()
        decls = w2c_law()                     # [FLIP — EP-29 W3a §A57; the note is on `w2c_law`]
        net = [r for r in shadow_records(obs, decls)
               if r["device"]["device_class"] == "net"]
        self.assertTrue(net)
        for r in net:
            self.assertIsNone(r["admitted_acts"]["value"])
            self.assertIsNone(r["admitted_acts"]["unit"])
            self.assertEqual(r["admitted_acts"]["basis"],
                             decls["net"]["arrivals_per_admitted_act"]["basis"])
            self.assertIn("NOT ESTABLISHED", r["admitted_acts"]["basis"])

    def test_no_record_MINTS_a_device_identity(self):
        """The declaration's own words: the minting is EP-29 W4's and alias equality never
        implies identity. The record carries the observed alias marked as one."""
        w = w2c_world(self)
        for r in w["records"]:
            if r["kind"] != "SHADOW-COVERING-RECORD":
                continue
            self.assertIsNone(r["device"]["identity"]["value"])
            self.assertTrue(r["device"]["identity"]["basis"].strip())
            self.assertTrue(r["device"]["observed_alias"])

    def test_the_BYTE_TOTAL_is_null_WITH_ITS_BASIS_rather_than_omitted(self):
        """UNESTABLISHED IS DECLARED, NEVER OMITTED — the shape W2b's own net unit took, and
        the shape DECLARE-IO-WINDOW's required `does_not_see` took before it."""
        w = w2c_world(self)
        for r in w["records"]:
            if r["kind"] != "SHADOW-COVERING-RECORD":
                continue
            bt = r["covers"]["byte_total"]
            self.assertIn("value", bt)
            self.assertIsNone(bt["value"])
            self.assertGreater(len(bt["basis"]), 200,
                               "a one-line basis for an unestablished value is an omission "
                               "with a field name on it")

    def test_a_record_CLOSES_only_on_a_DECLARED_closer(self):
        """The closers are `max_arrivals` and `unbind`. The observation window ENDING is
        neither, so a record that stopped at the edge of an observation is emitted OPEN with
        its reason. Both states are exhibited by this table."""
        w = w2c_world(self)
        covering = [r for r in w["records"] if r["kind"] == "SHADOW-COVERING-RECORD"]
        for r in covering:
            decl = w["declarations"][r["device"]["device_class"]]
            names = [c.split(" ")[0] for c in decl["closers"]]
            if r["closed"]:
                self.assertIn(r["closed_by"], names)
                self.assertEqual(r["covers"]["arrival_count"],
                                 decl["max_arrivals"]["value"])
                self.assertIsNone(r["not_closed_because"])
            else:
                self.assertIsNone(r["closed_by"])
                self.assertIn("NOT A CLOSER", r["not_closed_because"].upper())

    def test_the_admitted_act_count_AGREES_with_the_DELIVERED_load_it_cannot_see(self):
        """THE STRONGEST EVIDENCE THAT `FROM OBSERVATION ALONE` COSTS NOTHING, and the
        reason it is a row rather than a sentence in a report.

        The builder is structurally blind to `load_size.delivered_units` — the projection
        withholds it and a differential above shows a lie planted there moves nothing. Yet
        the admitted-act count it derives from arrivals and the declared unit EQUALS that
        delivered figure in every block window, INCLUDING the device whose delivered load
        fell to 36% of what its command requested. Observation alone reproduces the load's
        own report without being able to read it.

        Driven live rather than quoted: measured across 24 window-repeats in two full runs
        during this pass and re-taken at every arm on whatever the live profile drives."""
        w = w2c_world(self)
        by_window = {}
        for r in w["records"]:
            if r["kind"] != "SHADOW-COVERING-RECORD" or r["device"]["device_class"] != "block":
                continue
            ow = r["observed_window"]
            key = (r["device"]["observed_alias"], ow["level"], ow["repeat"])
            by_window.setdefault(key, 0)
            by_window[key] += r["admitted_acts"]["value"]
        checked = 0
        for win in w["observation"]["windows"]:
            if win["level_kind"] != "LOAD" or win["device_class"] != "block":
                continue
            key = (win["device"], win["level"], win.get("repeat"))
            delivered = (win.get("load_size") or {}).get("delivered_units")
            if not (win.get("load_size") or {}).get("delivered_known"):
                continue          # net cells report no delivery; nothing to agree with
            self.assertEqual(by_window.get(key), delivered,
                             "the admitted-act count derived from arrivals disagrees with "
                             "the delivered load at %r" % (key,))
            checked += 1
        self.assertGreater(checked, 0,
                           "no block window carried a known delivered figure, so this "
                           "agreement was never tested")

    def test_the_agreement_is_a_MEASUREMENT_and_not_an_identity(self):
        """The row above would be vacuous if the two numbers came from one source. They do
        not, and this shows it: moving the arrivals alone breaks the agreement, so what the
        row reports is two independent readings landing on the same number."""
        w = w2c_world(self)
        skewed = copy.deepcopy(w["observation"])
        for win in skewed["windows"]:
            if win["level_kind"] == "LOAD" and win["device_class"] == "block":
                win["arrivals"]["count"] = win["arrivals"]["count"] + 3
        recs = shadow_records(skewed, w["declarations"])
        block = [r for r in recs if r["device"]["device_class"] == "block"]
        self.assertTrue(block)
        for r in block:
            win = [x for x in skewed["windows"]
                   if x["device"] == r["device"]["observed_alias"]
                   and x["level"] == r["observed_window"]["level"]
                   and x.get("repeat") == r["observed_window"]["repeat"]][0]
            self.assertNotEqual(r["admitted_acts"]["value"],
                                (win.get("load_size") or {}).get("delivered_units"))

    def test_a_class_the_law_declares_NOTHING_for_REFUSES_and_the_refusal_IS_the_record(self):
        """DEV-LAW-INTAKE's fail-closed direction, which runs OPPOSITE to the files group's:
        recording more is this group's forbidden grade, so the direction is refusal, and
        nothing goes dark because the refusal is the record."""
        obs = synthetic_observation()
        for win in obs["windows"]:
            win["device_class"] = "undeclared-class"
        recs = shadow_records(obs, intake_by_class(live_pack()))
        self.assertTrue(recs)
        for r in recs:
            self.assertEqual(r["kind"], "SHADOW-INTAKE-REFUSAL")
            self.assertEqual(r["law_cited"], "DEV-LAW-INTAKE")
            self.assertTrue(r["refused_because"])
            self.assertTrue(r["evidence_not_record"])


class TheRecordsPerInterruptRowIsSECONDARYConformance(unittest.TestCase):
    """C4's ratio row. CONFORMANCE and nothing else — C9's scaling red is W5's and ADDENDUM
    7's own not-claimed block says W2c does not rehearse it."""

    def test_the_row_covers_EVERY_LEVEL_the_observation_drove(self):
        """[:663's repair applied: two is C1's FLOOR and never the count, so a row covering
        "both" would have no instruction for a third.]"""
        w = w2c_world(self)
        driven = {(x["device"], x["level"], x.get("repeat"))
                  for x in w["observation"]["windows"] if x["level_kind"] == "LOAD"}
        covered = {(r["device"], r["level"], r["repeat"])
                   for r in records_per_interrupt(w["observation"], w["records"])}
        self.assertEqual(covered, driven)
        self.assertTrue(driven)

    def test_the_row_covers_THREE_levels_when_three_were_driven(self):
        """The row above is satisfied on the live two-level table by a reading that hard
        codes a pair. Driven on a three-level substrate so it cannot be."""
        obs = synthetic_observation()
        rows = records_per_interrupt(obs, shadow_records(obs, w2c_law()))
        levels = sorted({r["level"] for r in rows if r["device_class"] == "block"})
        self.assertEqual(levels, ["L1", "L2", "L3"])

    def test_the_CONTROL_windows_are_NOT_in_the_row(self):
        """A control is the reading the loaded cells are compared against, not a load level,
        and a ratio asked to divide by an idle window is a ratio about nothing."""
        w = w2c_world(self)
        rows = records_per_interrupt(w["observation"], w["records"])
        self.assertTrue(all(r["level"] != "L0" for r in rows))

    def test_every_level_conforms_FAR_below_one_record_per_interrupt(self):
        """The conformance question, answered: did the records do what the landed law says.
        One covering record per window against hundreds or thousands of interrupts."""
        w = w2c_world(self)
        rows = records_per_interrupt(w["observation"], w["records"])
        self.assertTrue(rows)
        for r in rows:
            self.assertGreater(r["interrupts"], 0)
            self.assertLess(r["records_per_interrupt"], 1.0)
            self.assertGreater(r["interrupts_per_record"], 1.0)

    def test_the_ratio_is_recomputable_from_the_rows_OWN_two_numbers(self):
        """A figure that does not follow from its own stated inputs is unreconstructable,
        and unreconstructable is unreconstructable — W2a paid for this one already."""
        w = w2c_world(self)
        for r in records_per_interrupt(w["observation"], w["records"]):
            self.assertAlmostEqual(r["records_per_interrupt"],
                                   r["records"] / float(r["interrupts"]), places=12)

    def test_this_row_does_NOT_claim_the_scaling_red_that_belongs_to_W5(self):
        """SAID AS A ROW SO IT CANNOT LAND BY DRIFT. C9's claim is that the ratio is REQUIRED
        TO FALL as load rises. This pass asserts conformance at each level and asserts
        nothing across levels; a table on which the ratio did NOT fall would still satisfy
        every row in this class, and that is the intended reach."""
        obs = synthetic_observation()
        decls = w2c_law()                     # [FLIP — EP-29 W3a §A57; the note is on `w2c_law`]
        for win in obs["windows"]:
            if win["level_kind"] == "LOAD":
                win["interrupts"]["count"] = 100      # flat: the ratio cannot fall
        rows = records_per_interrupt(obs, shadow_records(obs, decls))
        self.assertTrue(rows)
        for r in rows:
            self.assertLess(r["records_per_interrupt"], 1.0)
        self.assertEqual(len({r["records_per_interrupt"] for r in rows}), 1,
                         "the substrate was meant to make the ratio flat across levels")


class NothingWriteCapableIsAttachedToTheIOPath(unittest.TestCase):
    """C4's THIRD RED WORLD, answered by a census and not by an undertaking."""

    def test_the_reading_finds_NO_write_capable_attachment_BY_OBSERVATION(self):
        """[RESTATED — W2c-TAINT-BIND, board :823 / :828, a NEW UNIT under §10. W2c's
        verdict STANDS: this row was TRUE OF ITS WORLD and is not being corrected.

        THE NAME GAINED THE THREE WORDS THE RULING PUTS AT THE CENTRE OF THE CLAIM.
        C4's subject is that OBSERVING attached nothing — not that the path is bare, and
        not that the kernel is pristine. A licensed, recorded, out-of-tree load is a lawful
        act of this estate and is not an observation; a row whose name omitted `BY
        OBSERVATION` read as the second claim and went red on the first world that did the
        lawful thing. The name is part of the rule, and a name that misstates the subject
        is the same defect as a proxy standing in for it.

        WHAT MOVED: the LICENSED REGISTER is now handed to the predicate. WHAT DID NOT: the
        predicate, every other clause in it, and the required answer — EMPTY.]"""
        w = w2c_world(self)
        self.assertEqual(interposition_findings(tuple(w["census"]),
                                                w["licensed_loads"]), [])

    def test_the_attachment_state_is_IDENTICAL_EITHER_SIDE_of_the_observation(self):
        """THE SHARPEST FORM OF THE CLAIM, and the one needing no judgement: had observing
        attached anything, these two readings would differ."""
        w = w2c_world(self)
        before, after = w["census"]
        for k in ("block_stacking", "device_mapper", "net_attachments", "netfilter",
                  "bpf", "dynamic_instrumentation", "taint", "modules"):
            self.assertEqual(json.dumps(before[k], sort_keys=True),
                             json.dumps(after[k], sort_keys=True), k)

    def test_the_bracket_comparison_DETECTS_a_difference_when_there_is_one(self):
        """The comparison's own negative-result test. Two readings of an unchanging world
        are equal for the same reason two readings of nothing are."""
        w = w2c_world(self)
        moved = copy.deepcopy(w["census"][1])
        moved["modules"]["names"] = list(moved["modules"]["names"]) + ["interposer"]
        self.assertTrue(interposition_findings((w["census"][0], moved)))

    def test_the_block_devices_carry_NO_stacked_target(self):
        w = w2c_world(self)
        after = w["census"][1]
        self.assertTrue(after["block_stacking"], "no block device was asked about")
        for dev, st in sorted(after["block_stacking"].items()):
            self.assertTrue(st["holders"]["ok"], dev)
            self.assertEqual(st["holders"]["entries"], [], dev)
            self.assertEqual(st["slaves"]["entries"], [], dev)

    def test_the_interface_carries_NO_filter_and_NO_XDP_program(self):
        w = w2c_world(self)
        for nif, na in sorted(w["census"][1]["net_attachments"].items()):
            self.assertTrue(na["link"]["available"], nif)
            self.assertNotIn('"xdp"', na["link"]["stdout"])
            for side in ("filter_egress", "filter_ingress"):
                self.assertEqual(na[side]["stdout"].strip(), "[]", (nif, side))

    def test_NO_DYNAMIC_probe_is_placed_and_the_tracer_is_nop(self):
        """The distinction the whole observation path rests on: a TRACEPOINT is static and
        read-only, a KPROBE can be placed anywhere and can change registers. If the second
        kind were present, "the observation reads and does not write" would be a claim about
        the wrong mechanism."""
        w = w2c_world(self)
        dyn = w["census"][1]["dynamic_instrumentation"]
        for f in ("kprobe_events", "uprobe_events", "dynamic_events"):
            self.assertTrue(dyn[f]["ok"], f)
            self.assertEqual(dyn[f]["text"].strip(), "", f)
        self.assertEqual(dyn["current_tracer"]["text"].strip(), "nop")

    def test_EVERY_netfilter_and_BPF_check_ACTUALLY_RAN(self):
        """AN UNRUN CHECK IS NOT A CLEAN RESULT. "the binary is absent" and "the ruleset is
        empty" are the same empty string and different facts, and this row is where the two
        are kept apart."""
        w = w2c_world(self)
        after = w["census"][1]
        for kind, r in sorted(after["netfilter"].items()):
            self.assertTrue(r["available"], "the %s check did not run" % kind)
            self.assertEqual(r["stdout"].strip(), "")
        for kind in ("prog_list", "net_list", "cgroup_tree"):
            self.assertTrue(after["bpf"][kind]["available"],
                            "the bpf/%s check did not run" % kind)
        self.assertEqual(census_limits(after), [],
                         "a check did not run, so this census states nothing about it and "
                         "that is a declared limit rather than a clean result")

    def test_NO_BPF_program_is_attached_to_the_netdev_or_to_the_LOADS_cgroup(self):
        """`bpftool net list` reports XDP / tc / flow-dissector / netfilter and reports
        NOTHING about cgroup-attached programs, which are also in the packet path and can
        also drop. Both questions are asked, because asking only the first would have
        returned an empty answer that was true of the wrong population."""
        w = w2c_world(self)
        after = w["census"][1]
        for entry in json.loads(after["bpf"]["net_list"]["stdout"]):
            for hook in ("xdp", "tc", "flow_dissector", "netfilter"):
                self.assertEqual(entry.get(hook), [], hook)
        for entry in json.loads(after["bpf"]["cgroup_tree"]["stdout"]):
            path = entry["cgroup"].replace("/sys/fs/cgroup", "") or "/"
            if entry.get("programs"):
                self.assertFalse(path == "/" or path.startswith("/user.slice"),
                                 "a cgroup BPF program at %s contains the cgroup the load "
                                 "runs in" % path)

    def test_the_AMBIENT_path_state_is_NAMED_rather_than_smoothed(self):
        """C4's claim is that the OBSERVATION interposes nothing. It is NOT a claim that the
        path is bare, and reporting only the first while the second is false would be true
        and misleading. This guest has a root qdisc and eight cgroups carrying systemd's own
        BPF programs; both are recorded with the reason they are not this claim's subject."""
        w = w2c_world(self)
        ambient = ambient_path_state(w["census"][1])
        self.assertTrue(ambient, "the ambient reading found nothing at all, which on a live "
                                 "systemd guest means it is not reading")
        for entry in ambient:
            self.assertTrue(entry["what"].strip())
            self.assertGreater(len(entry["why_not_a_C4_red"]), 80)

    def test_the_taint_set_is_EXACTLY_what_the_LICENSED_loads_records_account_for(self):
        """[RESTATED — W2c-TAINT-BIND, board :823 / :828, a NEW UNIT under §10.

        SUPERSEDES: `test_the_kernel_is_UNTAINTED_by_out_of_tree_code`, whose assertion was
        `raw == "0"` and `bits == []`.
        WHY THE NAME WENT WITH THE ASSERTION: `UNTAINTED` WAS THE PROXY, spelled into the
        row's own name. Leaving the name while restating the body would have left the
        retired proxy as the first thing a reader meets, and this estate has now been bitten
        twice by a label doing a test's job (:709, :823). The proxy is retired, name and
        all.
        REMAINS TRUE, ENTIRELY: everything the old row claimed about the world it ran in. A
        world with zero licensed loads still has to read `0` here, and that branch is
        asserted below rather than dropped — it is the same claim, now carrying the
        condition under which it is the right question.
        GIVEN UP: the right to ask `untainted now` of a world where lawful, recorded loads
        exist. That question had stopped being about attachment.]

        FOUR ASSERTIONS, AND THE ORDER IS THE ARGUMENT:
          1. the two decoders AGREE on this world's raw word (host table vs guest table);
          2. the raw word carries NOTHING the name tables do not cover;
          3. THE TRIPWIRE — no bit that no licensed record accounts for;
          4. THE EXERCISE CONDITION — with an empty register, the raw word is exactly "0".
        POPULATION and BASIS travel with the reading itself (§A51)."""
        w = w2c_world(self)
        r = taint_reading(w["census"][1], w["licensed_loads"])
        self.assertEqual(r["decoder_disagreement"], [],
                         "the host and the guest decoded the SAME taint word differently "
                         "(%r), so one of the two name tables is wrong and neither answer "
                         "may be relied on: %r" % (r["decoder_disagreement"], r))
        self.assertTrue(r["value_covered_by_the_name_table"],
                        "the raw taint word %r holds a bit NO NAME TABLE COVERS, so a "
                        "reading that compared only decoded names would call this world "
                        "clean while an unnamed bit stood set: %r" % (r["raw"], r))
        self.assertEqual(r["unaccounted"], [],
                         "a taint bit is set that NO LICENSED LOAD'S RECORD ACCOUNTS FOR "
                         "(%r) — an unlicensed attachment, which is what this row exists "
                         "to catch and what it will go on catching on every world: %r"
                         % (r["unaccounted"], r))
        if not w["licensed_loads"]:
            self.assertEqual(r["raw"], "0",
                             "this world records ZERO licensed out-of-tree loads, so the "
                             "correct reading of it is exactly 0 and it reads %r" % r["raw"])


class TheFoundingStandsBYTEUNCHANGEDAfterW2c(unittest.TestCase):
    """THIS MOVEMENT MUST NOT MOVE THE FOUNDING, and it is the third different requirement
    in four units on this line: W1c required it unchanged, W2a required it unchanged, W2b
    REQUIRED IT MOVED, and W2c requires it unchanged again. Asserted here rather than
    carried from the habit of the pass before.

    AS A COMPARISON BETWEEN TWO ERAS AND NEVER AS A VERSION LITERAL. A literal would join
    §A57's sweep population at the next founding move and buy nothing this comparison does
    not already give."""

    def test_the_pack_is_BYTE_IDENTICAL_to_this_passs_own_pre_write_commit(self):
        """[DOCUMENTED FLIP — EP-29 W3a, 2026-08-13, §A57 BY FALSIFICATION.
        CAUSE: W3a MOVED the founding, which is that movement's required outcome and the
        inverse of this one's. ASSERTED: W2c's pre-write blob against the LIVE tree.
        SUPERSEDED: W2c's pre-write blob against the blob at `W3A_BEFORE_COMMIT` — the
        state of the tree at the moment W2c closed and before W3a's first write.
        REMAINS TRUE: the claim itself, entirely. W2c moved no founding byte, and the
        comparison now runs between the two coordinates that bracket W2c instead of
        between one of them and whatever the tree holds today. GIVEN UP: nothing — the
        live tree was never a coordinate of W2c's history, which is why this row was
        falsified by a LATER pass doing its own lawful work.]"""
        era = era_pin.blob_at(W2C_PRE_WRITE_COMMIT, era_pin.PACK_PATH)
        after = era_pin.blob_at(W3A_BEFORE_COMMIT, era_pin.PACK_PATH)
        self.assertEqual(hashlib.sha256(era).hexdigest(),
                         hashlib.sha256(after).hexdigest(),
                         "W2c moved a founding byte, and movement is this movement's "
                         "FAILING outcome")

    def test_the_era_pin_reports_a_DIFFERENCE_when_there_is_one(self):
        """The instrument's own negative-result test: W2b's pre-write commit holds the pack
        BEFORE W2b landed, so a comparison against it MUST report inequality. Without this
        the row above is satisfied by a comparison that cannot fail."""
        older = era_pin.blob_at(W2B_ERA_COMMIT, era_pin.PACK_PATH)
        with open(PACK_PATH, "rb") as fh:
            live = fh.read()
        self.assertNotEqual(hashlib.sha256(older).hexdigest(),
                            hashlib.sha256(live).hexdigest())

    def test_the_step_count_and_the_declared_law_are_unmoved_since_the_pre_write_commit(self):
        """[DOCUMENTED FLIP — MAINT-EP29-K1-REPIN, 2026-09-02, charter §A57 era-stabilization
        (board :2706, AUTHORISED-BY :2664). CAUSE: a LATER lawful founding move — EP-31's
        MEM-LAW-BUDGET create, 1.30.0 -> 1.31.0, 27 -> 28 steps. This row read W2c's pre-write
        pack against the LIVE tree, so the later step made a claim about W2c's own window red
        on a movement that ran after W2c closed. ASSERTED: W2c's pre-write pack against W2c's
        OWN AFTER-ERA at `W3A_BEFORE_COMMIT` — the state of the tree at the moment W2c closed
        and before W3a's first write, which is the exact coordinate the sibling byte-identical
        row already uses. SUPERSEDED: the comparison against `live_pack()`. REMAINS TRUE: the
        claim itself — W2c moved no step and no intake class — now read between the two
        coordinates that bracket W2c instead of between one of them and today's tree. GIVEN UP:
        nothing; the live tree was never a coordinate of W2c's history.]"""
        era = era_pin.pack_at(W2C_PRE_WRITE_COMMIT)
        after = era_pin.pack_at(W3A_BEFORE_COMMIT)
        self.assertEqual(len(era["steps"]), len(after["steps"]))
        self.assertEqual(sorted(intake_by_class(era)),
                         sorted(intake_by_class(after)))

    def test_the_SWEEP_population_is_empty_BY_CONSTRUCTION_and_not_by_a_search(self):
        """§A57 governs version-assertion rows falsified by a founding pass. W2c moves no
        founding AND authors no version assertion — this class asserts an ERA COMPARISON and
        every other W2c row reads the law by ACTION NAME — so there is no population to
        sweep.

        WALKED OVER THE AST AND NOT GREPPED FOR A LITERAL. A grep for the current version
        string would MATCH ITSELF the moment it was written, which is failure-record item
        10's own class: a check whose correct answer is a count of zero in a growing file is
        a check waiting to invert. This looks for the SHAPE of a version constant inside
        W2c's own classes, and it carries the positive control that makes its zero mean
        something."""
        semver = re.compile(r"^\d+\.\d+\.\d+$")
        tree = ast.parse(open(os.path.abspath(__file__), encoding="utf-8").read())
        w2c_classes = [n for n in tree.body
                       if isinstance(n, ast.ClassDef) and n.name.startswith(
                           ("TheW2c", "TheValidationDrivers", "TheObservationPath",
                            "TheShadowRecords", "TheRecordsPerInterrupt",
                            "NothingWriteCapable", "TheFoundingStandsBYTE"))]
        self.assertGreaterEqual(len(w2c_classes), 8, "the class walk found almost nothing")
        found = [c.value for n in w2c_classes for c in ast.walk(n)
                 if isinstance(c, ast.Constant) and isinstance(c.value, str)
                 and semver.match(c.value)]
        self.assertEqual(found, [],
                         "a W2c row carries a version constant, so it joins the next "
                         "founding move's sweep population and must be era-pinned instead")
        planted = ast.parse('class TheW2cPlanted:\n    V = "1.99.0"\n')
        self.assertTrue([c.value for c in ast.walk(planted)
                         if isinstance(c, ast.Constant) and isinstance(c.value, str)
                         and semver.match(c.value)],
                        "the detector cannot find a version constant that IS there, so its "
                        "empty answer above says nothing")

    def test_the_CENSUS_driver_is_correctly_OUTSIDE_the_validation_driver_population(self):
        """Membership of `VALIDATION_DRIVERS` is a property and not a preference. The census
        drives no load and probes no device, so it is not a subject of C4's first clause —
        and that is checked over its text rather than asserted."""
        lit, wrap, indirect = executed_commands(_CENSUS_DRIVER)
        self.assertEqual(lit, ["bpftool", "dmsetup", "ip", "ip6tables-save",
                               "iptables-save", "nft", "tc"],
                         "the census can execute a command this row does not expect")
        self.assertEqual(len(wrap), 1, "the census has more than its own run wrapper")
        self.assertEqual(indirect, [],
                         "the census executes a caller-supplied argv, so it CAN be handed "
                         "a load and belongs in the frozen population")
        # THE POSITIVE CONTROL, and it is the discriminator rather than a formality: the
        # calibration observer DOES execute a caller-supplied argv, which is what driving a
        # load is, so the census's empty third bucket is a difference and not a default.
        c_lit, c_wrap, c_indirect = executed_commands(_CALIB_DRIVER)
        self.assertEqual(len(c_wrap), 1)
        self.assertTrue(c_indirect,
                        "the reader finds no indirect argv in the instrument that DOES "
                        "drive a load, so its answer about the census would mean nothing")
        self.assertIn("dd", _CALIB_DRIVER.split("argvs = ")[1][:20],
                      "the calibration observer no longer builds a dd argv, so the "
                      "population this row reasons about has changed")
        self.assertNotIn("socket", _CENSUS_DRIVER.split('"""')[2],
                         "the census opens a socket outside its own docstring")
        self.assertEqual(sorted(drivers_at("HEAD")), sorted(VALIDATION_DRIVERS))


#: The rows the synthetic substrate can carry, and therefore the rows a planted world can be
#: shown to REDDEN. Membership is a property and not a preference: a row is here exactly
#: when it reads `w2c_world`, because a row that does not read the world cannot be made to
#: fail by planting one.
#:
#: DELIBERATELY ABSENT, NAMED RATHER THAN OMITTED:
#:   TheW2cExhibitionRanAtTheGuestAndOnTheBytesWeSent  — every row asserts a LIVE guest fact
#:     (hostname, uname, the instrument digest the guest itself computed). Planting half its
#:     world would measure the plant. Covered live and nowhere else.
#:   TheObservationPathIsEnumeratedAsSurfaces — the enumeration is computed from the frozen
#:     `_CALIB_DRIVER`, so a planted world cannot move it; its own negative-result test
#:     drives a thinner instrument instead, which is the same claim by the right route.
#:   TheValidationDrivers…{PLANS_OWN_COMPARISON, working_tree, history_covers, era_pin} —
#:     these read git rather than the world, so a plant cannot reach them and their passing
#:     under one would prove nothing.
#:   TheFoundingStandsBYTEUNCHANGEDAfterW2c — reads the tree and the era pin, never the
#:     world.
#:   …AreAtTheDECLAREDGrade.{arithmetic_produces_MORE_THAN_ONE, NET_record, REFUSES} and
#:   …SECONDARYConformance.{THREE_levels, does_NOT_claim_the_scaling_red} — these BUILD
#:     their own substrate inside the row, so they are already synthetic and the harness
#:     would be planting under a world they do not read.
_W2C_ROWS = (
    (TheValidationDriversAreByteIdenticalAcrossTheWholeOfW2,
     ("test_NO_DRIVER_LEFT_ITS_SETTLED_DIGEST_at_any_recorded_point",
      "test_the_driver_AUTHORED_INSIDE_W2a_is_reported_and_not_hidden")),
    (TheShadowRecordsAreBuiltFromObservationALONE,
     ("test_the_projection_WITHHOLDS_the_loads_own_report",
      "test_the_projection_WITHHOLDS_every_clock",
      "test_the_record_set_is_UNCHANGED_when_the_withheld_fields_are_STRIPPED",
      "test_MOVING_the_delivered_figure_does_not_move_a_single_record",
      "test_MOVING_the_arrival_count_DOES_move_the_records",
      "test_the_shadow_set_is_EVIDENCE_and_no_product_record_was_appended")),
    (TheShadowRecordsAreAtTheDECLAREDGrade,
     ("test_the_reading_finds_NO_red_world_in_the_live_exhibition",
      "test_every_declared_class_is_the_one_the_law_declares",
      "test_every_record_carries_the_LAWS_grade_bound_window_and_citation",
      "test_the_record_COUNT_is_the_laws_own_arithmetic_and_not_a_constant",
      "test_the_covered_counts_SUM_to_the_arrivals_observed",
      "test_the_BLOCK_admitted_act_count_is_DERIVED_from_arrivals_and_the_declared_unit",
      "test_no_record_MINTS_a_device_identity",
      "test_the_BYTE_TOTAL_is_null_WITH_ITS_BASIS_rather_than_omitted",
      "test_a_record_CLOSES_only_on_a_DECLARED_closer",
      "test_the_admitted_act_count_AGREES_with_the_DELIVERED_load_it_cannot_see",
      "test_the_agreement_is_a_MEASUREMENT_and_not_an_identity")),
    (TheRecordsPerInterruptRowIsSECONDARYConformance,
     ("test_the_row_covers_EVERY_LEVEL_the_observation_drove",
      "test_the_CONTROL_windows_are_NOT_in_the_row",
      "test_every_level_conforms_FAR_below_one_record_per_interrupt",
      "test_the_ratio_is_recomputable_from_the_rows_OWN_two_numbers")),
    (NothingWriteCapableIsAttachedToTheIOPath,
     ("test_the_reading_finds_NO_write_capable_attachment_BY_OBSERVATION",
      "test_the_attachment_state_is_IDENTICAL_EITHER_SIDE_of_the_observation",
      "test_the_bracket_comparison_DETECTS_a_difference_when_there_is_one",
      "test_the_block_devices_carry_NO_stacked_target",
      "test_the_interface_carries_NO_filter_and_NO_XDP_program",
      "test_NO_DYNAMIC_probe_is_placed_and_the_tracer_is_nop",
      "test_EVERY_netfilter_and_BPF_check_ACTUALLY_RAN",
      "test_NO_BPF_program_is_attached_to_the_netdev_or_to_the_LOADS_cgroup",
      "test_the_AMBIENT_path_state_is_NAMED_rather_than_smoothed",
      "test_the_taint_set_is_EXACTLY_what_the_LICENSED_loads_records_account_for")),
)


class TheW2cRowsCanBeMadeToFail(unittest.TestCase):
    """THE NEGATIVE-RESULT TEST, APPLIED TO W2c's OWN ROWS.

    The reading's own controls prove THE READING can emit each code. These prove THE ROWS
    can red — a different claim, and the one that matters when the exhibition is real and
    wrong rather than absent and planted."""

    def assertRowFAILED(self, res, why):
        """A RED WORLD MUST RED FOR ITS OWN REASON. `wasSuccessful()` is False for an ERROR
        too, so a planted world that BREAKS the row would satisfy a bare `assertFalse` and
        read on the page exactly like the claim biting."""
        self.assertEqual(res.errors, [],
                         "the row ERRORED rather than failed, so the planted world broke "
                         "the instrument instead of the claim: %r" % (res.errors,))
        self.assertEqual(len(res.failures), 1, why)

    def test_the_synthetic_control_PASSES_every_row(self):
        """CONTROL, FIRST. Without it a red below could be the substrate being malformed
        rather than the clause biting, and the two read identically on the page."""
        ran = 0
        for cls, meths in _W2C_ROWS:
            for meth in meths:
                res = _run_w2c_against(synthetic_world(), cls, meth)
                self.assertTrue(res.wasSuccessful(),
                                "the synthetic control FAILS %s.%s, so every red world "
                                "below is uninterpretable: %r"
                                % (cls.__name__, meth, res.failures + res.errors))
                ran += 1
        self.assertEqual(ran, sum(len(m) for _, m in _W2C_ROWS))
        self.assertGreater(ran, 25, "non-vacuity: the control is not a stub")

    def test_every_registered_row_ACTUALLY_READS_the_world(self):
        """Membership of `_W2C_ROWS` is a property and not a preference. A row that never
        reads the world would sit in the control passing for a reason the control cannot
        see, and would be unreddenable by any plant."""
        src = open(os.path.abspath(__file__), encoding="utf-8").read()
        for cls, meths in _W2C_ROWS:
            body = src[src.index("class %s(" % cls.__name__):]
            for meth in meths:
                start = body.index("def %s(" % meth)
                nxt = body.find("\n    def ", start)
                chunk = body[start:nxt if nxt > 0 else start + 4000]
                self.assertIn("w2c_world(self)", chunk,
                              "%s.%s is registered and does not read the world"
                              % (cls.__name__, meth))

    def _red(self, planter, cls, meth, why):
        w = synthetic_world()
        planter(w)
        self.assertRowFAILED(_run_w2c_against(w, cls, meth), why)

    # ------------------------------------------------------------------- the reading itself
    def test_the_reading_emits_EACH_code_from_ITS_OWN_mutation_alone(self):
        """PLANT EACH ALONE. A single mutant carrying every defect can pass with two clauses
        wired to one defect, and W2a already paid for discovering that a maximal mutant can
        demand a world that cannot exist."""
        self.assertEqual(read_world(synthetic_world()), [],
                         "the unmutated synthetic world already exhibits a red world")
        seen = 0
        for code, planters in sorted(W2C_DEFECT_PLANTERS.items()):
            for name, planter in planters:
                w = synthetic_world()
                planter(w)
                self.assertEqual(read_world(w), [code],
                                 "planting %r under %s gave %r"
                                 % (name, code, read_world(w)))
                seen += 1
        self.assertEqual(seen, sum(len(v) for v in W2C_DEFECT_PLANTERS.values()))
        self.assertGreater(seen, 12, "non-vacuity: the planter set is not a stub")

    def test_the_reading_covers_EXACTLY_the_three_red_worlds_the_plan_names(self):
        """The code set is ADDENDUM 7 C4's and does not drift into a builder-authored
        battery. Properties this pass also holds get their own rows instead."""
        self.assertEqual(sorted(W2C_DEFECT_PLANTERS),
                         ["DRIVER-MOVED", "PER-INTERRUPT-GRADE",
                          "WRITE-CAPABLE-ATTACHMENT"])

    # -------------------------------------------------------------- A DRIVER BYTE MOVED
    def test_A_DRIVER_THAT_MOVED_ACROSS_THE_ERA_REDS(self):
        self._red(_p_driver_moved_across_the_era,
                  TheValidationDriversAreByteIdenticalAcrossTheWholeOfW2,
                  "test_NO_DRIVER_LEFT_ITS_SETTLED_DIGEST_at_any_recorded_point",
                  "a driver whose bytes differ from the era's passes the freeze row")

    def test_A_DRIVER_EDITED_AFTER_SETTLING_REDS(self):
        """The move an endpoint comparison cannot see: out and back again."""
        self._red(_p_driver_edited_after_settling,
                  TheValidationDriversAreByteIdenticalAcrossTheWholeOfW2,
                  "test_NO_DRIVER_LEFT_ITS_SETTLED_DIGEST_at_any_recorded_point",
                  "a driver that left its settled digest and returned passes the freeze row")

    # ------------------------------------------------- A SHADOW RECORD AT PER-INTERRUPT GRADE
    def test_A_RECORD_WHOSE_GRADE_SAYS_PER_INTERRUPT_REDS(self):
        self._red(_p_grade_says_per_interrupt, TheShadowRecordsAreAtTheDECLAREDGrade,
                  "test_the_reading_finds_NO_red_world_in_the_live_exhibition",
                  "a record set declaring the forbidden grade passes the reading")

    def test_A_BOUND_OF_ONE_REDS(self):
        """DEV-LAW-INTAKE: no declaration may set a bound of one, at any load and for any
        class — a covering record standing for exactly one arrival is the per-interrupt
        grade wearing a window's name."""
        self._red(_p_bound_of_one, TheShadowRecordsAreAtTheDECLAREDGrade,
                  "test_the_reading_finds_NO_red_world_in_the_live_exhibition",
                  "a bound of one passes the reading")

    def test_ONE_RECORD_PER_ARRIVAL_WITH_THE_LABEL_UNTOUCHED_REDS(self):
        """THE MUTATION THE NAME-CHECK CANNOT SEE, and the reason the ratio is asked as well
        as the label: a record set can call itself `window` and still be one per arrival."""
        self._red(_p_one_record_per_arrival, TheShadowRecordsAreAtTheDECLAREDGrade,
                  "test_the_reading_finds_NO_red_world_in_the_live_exhibition",
                  "one record per arrival passes the reading while the label says window")

    def test_RECORDS_OUTNUMBERING_INTERRUPTS_REDS(self):
        self._red(_p_records_outnumber_interrupts, TheShadowRecordsAreAtTheDECLAREDGrade,
                  "test_the_reading_finds_NO_red_world_in_the_live_exhibition",
                  "a record set larger than the interrupt count passes the reading")

    def test_A_RECORD_COUNT_THAT_IS_NOT_THE_LAWS_ARITHMETIC_REDS(self):
        self._red(_p_records_outnumber_interrupts, TheShadowRecordsAreAtTheDECLAREDGrade,
                  "test_the_record_COUNT_is_the_laws_own_arithmetic_and_not_a_constant",
                  "a record count unrelated to ceil(arrivals/cap) passes the arithmetic row")

    # -------------------------------------- ANY WRITE-CAPABLE ATTACHMENT TO THE I/O PATH
    def test_A_STACKED_BLOCK_TARGET_REDS(self):
        self._red(_p_block_device_gains_a_holder, NothingWriteCapableIsAttachedToTheIOPath,
                  "test_the_reading_finds_NO_write_capable_attachment_BY_OBSERVATION",
                  "a device-mapper target over the driven device passes the census reading")

    def test_AN_XDP_PROGRAM_REDS(self):
        self._red(_p_interface_gains_an_xdp_program, NothingWriteCapableIsAttachedToTheIOPath,
                  "test_the_reading_finds_NO_write_capable_attachment_BY_OBSERVATION",
                  "an XDP program on the driven interface passes the census reading")

    def test_A_TC_FILTER_WITH_A_DROP_ACTION_REDS(self):
        self._red(_p_interface_gains_a_tc_filter, NothingWriteCapableIsAttachedToTheIOPath,
                  "test_the_reading_finds_NO_write_capable_attachment_BY_OBSERVATION",
                  "a tc filter carrying a drop action passes the census reading")

    def test_A_NETFILTER_RULESET_REDS(self):
        self._red(_p_netfilter_ruleset_appears, NothingWriteCapableIsAttachedToTheIOPath,
                  "test_the_reading_finds_NO_write_capable_attachment_BY_OBSERVATION",
                  "a non-empty netfilter ruleset passes the census reading")

    def test_A_BPF_PROGRAM_ON_THE_NETDEV_REDS(self):
        self._red(_p_bpf_attaches_to_the_netdev, NothingWriteCapableIsAttachedToTheIOPath,
                  "test_the_reading_finds_NO_write_capable_attachment_BY_OBSERVATION",
                  "a BPF program attached to the netdev passes the census reading")

    def test_A_CGROUP_BPF_PROGRAM_OVER_THE_LOADS_SLICE_REDS(self):
        """The population question said as a red world: a program under /system.slice cannot
        reach the load and one over /user.slice can, so the reading must separate them."""
        self._red(_p_cgroup_bpf_reaches_the_load, NothingWriteCapableIsAttachedToTheIOPath,
                  "test_the_reading_finds_NO_write_capable_attachment_BY_OBSERVATION",
                  "a cgroup BPF program containing the load's own cgroup passes")

    def test_A_KPROBE_ON_THE_BLOCK_PATH_REDS(self):
        self._red(_p_a_kprobe_is_placed, NothingWriteCapableIsAttachedToTheIOPath,
                  "test_the_reading_finds_NO_write_capable_attachment_BY_OBSERVATION",
                  "a kprobe passes the census reading, and a kprobe is not a tracepoint")

    def test_A_TRACER_OTHER_THAN_NOP_REDS(self):
        self._red(_p_the_tracer_is_not_nop, NothingWriteCapableIsAttachedToTheIOPath,
                  "test_the_reading_finds_NO_write_capable_attachment_BY_OBSERVATION",
                  "dynamic function tracing passes the census reading")

    def test_AN_OUT_OF_TREE_MODULE_REDS(self):
        """UNDER A REGISTER WITH ZERO LICENSED LOADS, which is this substrate's world and
        was W2c's. The restatement did not weaken this: an out-of-tree bit nothing licensed
        still REDS, and the same plant is driven against the LICENSED-shaped world in
        `TheRestatedTaintReadingIsDrivenAgainstNearMisses` below."""
        self._red(_p_the_kernel_is_tainted_out_of_tree,
                  NothingWriteCapableIsAttachedToTheIOPath,
                  "test_the_reading_finds_NO_write_capable_attachment_BY_OBSERVATION",
                  "an out-of-tree module passes the census reading")

    def test_THE_CENSUS_MOVING_ACROSS_THE_OBSERVATION_REDS(self):
        """THE SHARPEST RED WORLD OF THE THREE. Interposition does not have to be recognised
        by name to be caught: it has to change the path, and this is that change."""
        self._red(_p_the_census_moved_across_the_observation,
                  NothingWriteCapableIsAttachedToTheIOPath,
                  "test_the_attachment_state_is_IDENTICAL_EITHER_SIDE_of_the_observation",
                  "an attachment state that moved across the observation passes the bracket")

    # --------------------------------------------------------------- the projection itself
    def test_A_BUILDER_THAT_COULD_SEE_THE_LOADS_REPORT_REDS(self):
        """The projection is the mechanism behind `from observation alone`, so widening it
        must be visible. Driven by adding a withheld field back into the projection."""
        def m(w):
            w["observation"]["windows"][1]["load_size"] = None
        original = tuple(_OBSERVED_FIELDS)
        try:
            globals()["_OBSERVED_FIELDS"] = original + ("load_size",)
            wrld = synthetic_world()
            m(wrld)
            self.assertRowFAILED(
                _run_w2c_against(wrld, TheShadowRecordsAreBuiltFromObservationALONE,
                                 "test_the_projection_WITHHOLDS_the_loads_own_report"),
                "a projection carrying the load's own report passes the withholding row")
        finally:
            globals()["_OBSERVED_FIELDS"] = original


# =======================================================================================
# W2c-TAINT-BIND — THE RESTATED TAINT READING, DRIVEN AGAINST NEAR-MISSES
#
# §A64 APPLIED TO THE RESTATEMENT ITSELF. The rule written above is a structural claim
# about a space of worlds, and §A64's whole complaint is that structural claims get READ
# rather than DRIVEN. A restatement nobody tried to fool has not been tested; worse, a
# restatement that only ever meets the world it was restated away from would go green on a
# reading that had quietly stopped catching anything.
#
# THE ONE WAY THIS UNIT CAN DO REAL DAMAGE is by removing the tripwire while appearing to
# restate it, so the tripwire is what gets driven hardest: an unaccounted bit REDS, and it
# reds every one of the three rows, from one plant, through the shipped rows and not
# through a paraphrase of them.
#
# EVERY TAINT VALUE BELOW IS A HAND-COMPUTED LITERAL and its arithmetic is written beside
# it. A value produced by running the decoder would be a recording of the decoder's
# behaviour rather than a test of it.
#
# AND EVERY TAINT PLANT IS PLACED AT **BOTH** CENSUS ENDPOINTS. THIS WAS FOUND BY DRIVING,
# NOT BY DESIGN, and it is the sharpest thing this unit learned. The first draft planted
# only on the AFTER blob, which made the taint word MOVE ACROSS THE BRACKET — so
# `interposition_findings`' DELTA half spoke and the row went red for a reason that had
# nothing to do with the accounting clause under test. A red for the wrong reason reads on
# the page exactly like a red for the right one. Planting at both endpoints silences the
# delta half BY CONSTRUCTION and leaves the accounting clause as the only thing that can
# speak, which is what makes each row below a test OF THE CLAUSE IT NAMES.
#
# NOTED, NOT TOUCHED: W2c's own `_p_the_kernel_is_tainted_out_of_tree` plants on the AFTER
# blob alone and therefore carries the same ambiguity. It is a shipped W2c row, its verdict
# stands, and §10 puts it outside this unit — recorded in the entry as a finding rather
# than edited here.
def _p_both_ends(w, taint):
    """One taint field, written to BOTH endpoints of the bracket. See the note above."""
    for c in w["census"]:
        c["taint"] = copy.deepcopy(taint)
    return w


def _p_an_UNACCOUNTED_write_capable_bit(w):
    """THE RED WORLD THE RULING NAMES: a bit no licensed record accounts for.
    12289 = 12288 + 1 = bit 12 | bit 13 | bit 0 — the two accounted bits, plus
    PROPRIETARY_MODULE, which no record in this estate licenses and which is write-capable.
    It must red ALL THREE restated rows."""
    _p_both_ends(w, {"raw": {"ok": True, "text": "12289\n"},
                     "bits": ["OOT_MODULE", "PROPRIETARY_MODULE", "UNSIGNED_MODULE"]})


def _p_an_UNACCOUNTED_bit_that_is_NOT_write_capable(w):
    """12296 = 12288 + 8 = bit 12 | bit 13 | bit 3 — FORCED_RMMOD, unaccounted and NOT in
    `_WRITE_CAPABLE_TAINT`. It must red the ACCOUNTING row and must NOT red the census
    reading. A plant that reddened both would show the two rows had collapsed into one
    question, and the estate would have one row wearing two names."""
    _p_both_ends(w, {"raw": {"ok": True, "text": "12296\n"},
                     "bits": ["FORCED_RMMOD", "OOT_MODULE", "UNSIGNED_MODULE"]})


def _p_a_bit_ABOVE_the_name_tables(w):
    """274432 = 262144 + 12288 = bit 18 | bit 12 | bit 13. NEITHER name table covers bit 18,
    so both decoders return the accounted pair and a reading that compared only decoded
    NAMES calls this world clean while an unnamed bit stands set. This is §7.1's filter that
    cannot match, arriving inside the cure — and the raw-against-recomputed comparison is
    the only assertion that sees it."""
    _p_both_ends(w, {"raw": {"ok": True, "text": "274432\n"},
                     "bits": ["OOT_MODULE", "UNSIGNED_MODULE"]})


def _p_the_two_decoders_DISAGREE(w):
    """The guest reports ONE bit for a word the host decodes as two. One of the two name
    tables is wrong and neither answer may be relied on until that is settled."""
    _p_both_ends(w, {"raw": {"ok": True, "text": "12288\n"}, "bits": ["OOT_MODULE"]})


def _p_the_taint_word_DID_NOT_READ(w):
    """AN UNRUN CHECK IS A LIMIT AND NEVER A CLEAN RESULT — the census's own standing rule,
    applied to its own taint field. A reading that returned an empty unaccounted set here
    would report an absence it could not see."""
    _p_both_ends(w, {"raw": {"ok": False, "errno": 13, "strerror": "Permission denied"},
                     "bits": None})


def _p_a_SECOND_and_UNLICENSED_out_of_tree_module(w):
    """THE CAP, MADE INTO A WORLD. The taint word does not move — bits 12 and 13 are already
    set and a second unsigned out-of-tree load adds nothing to a kernel-wide flag word — so
    the taint half is silent BY CONSTRUCTION and cannot be made loud by any wording. The
    module-set half is what speaks."""
    w["census"][1]["modules"] = {"raw_ok": True,
                                 "names": ["govshim", "rogue_oot", "virtio_net"],
                                 "count": 3}


def _p_a_TAINTED_word_under_a_register_that_licenses_NOTHING(w):
    """The exercise condition as a world: the live guest's own taint value, carried into a
    world whose register records ZERO licensed loads. `taint == 0` is the correct reading of
    THAT world, so this must red — which is what makes clause (1) an assertion rather than
    a sentence in a comment."""
    _p_both_ends(w, {"raw": {"ok": True, "text": "12288\n"},
                     "bits": ["OOT_MODULE", "UNSIGNED_MODULE"]})


_THE_ACCOUNTING_ROW = "test_the_taint_set_is_EXACTLY_what_the_LICENSED_loads_records_" \
                      "account_for"
_THE_CENSUS_ROW = "test_the_reading_finds_NO_write_capable_attachment_BY_OBSERVATION"
_THE_EXHIBITION_ROW = "test_the_reading_finds_NO_red_world_in_the_live_exhibition"


class TheRestatedTaintReadingIsDrivenAgainstNearMisses(unittest.TestCase):
    """THE RESTATEMENT'S OWN NEGATIVE-RESULT TEST.

    POPULATION: the three restated rows, run through unittest's own machinery against
    planted worlds — the rows that SHIP, never a paraphrase of them. BASIS: one plant at a
    time, each world differing from the control in exactly one field.

    THE CONTROL COMES FIRST AND IT IS A DIFFERENT CONTROL FROM W2c's. W2c's control is a
    world with an EMPTY register, which exercises clause (1) and never reaches the delta
    form. The control here carries a register, so a red below is the delta clause biting
    rather than the substrate being malformed — and the two controls together are the only
    way to tell those apart."""

    def _run(self, w, cls, meth):
        return _run_w2c_against(w, cls, meth)

    def _red(self, planter, cls, meth, why, world=None):
        w = synthetic_world_with_a_licensed_load() if world is None else world
        planter(w)
        res = self._run(w, cls, meth)
        self.assertEqual(res.errors, [],
                         "the row ERRORED rather than failed, so the planted world broke "
                         "the instrument instead of the claim: %r" % (res.errors,))
        self.assertEqual(len(res.failures), 1, why)

    def _green(self, planter, cls, meth, why):
        w = synthetic_world_with_a_licensed_load()
        planter(w)
        res = self._run(w, cls, meth)
        self.assertTrue(res.wasSuccessful(), "%s: %r" % (why, res.failures + res.errors))

    # ------------------------------------------------------------------- CONTROL, FIRST
    def test_THE_LICENSED_SHAPED_CONTROL_PASSES_ALL_THREE_RESTATED_ROWS(self):
        """Without this, every red below could be the licensed-shaped substrate being
        malformed rather than a clause biting, and the two read identically on the page."""
        for cls, meth in ((NothingWriteCapableIsAttachedToTheIOPath, _THE_ACCOUNTING_ROW),
                          (NothingWriteCapableIsAttachedToTheIOPath, _THE_CENSUS_ROW),
                          (TheShadowRecordsAreAtTheDECLAREDGrade, _THE_EXHIBITION_ROW)):
            res = self._run(synthetic_world_with_a_licensed_load(), cls, meth)
            self.assertTrue(res.wasSuccessful(),
                            "the licensed-shaped control FAILS %s, so every red below is "
                            "uninterpretable: %r" % (meth, res.failures + res.errors))

    def test_EVERY_TAINT_PLANT_LEAVES_THE_BRACKET_DELTA_SILENT(self):
        """THE CONTROL THAT CAUGHT THE FIRST DRAFT OF THIS CLASS, kept as a row so the
        mistake cannot come back quietly.

        Every red below is claimed to come from the ACCOUNTING clause. A taint field planted
        on the AFTER blob alone makes the taint word MOVE ACROSS THE BRACKET, and
        `interposition_findings`' delta half then reds the row for a reason that has nothing
        to do with accounting — a confident red, on the right row, for the wrong clause, and
        indistinguishable on the page from the real thing. This row asserts the delta half is
        SILENT under every taint plant, which is what leaves the accounting clause as the
        only possible speaker."""
        plants = [("an unaccounted write-capable bit", _p_an_UNACCOUNTED_write_capable_bit),
                  ("an unaccounted bit that is not write-capable",
                   _p_an_UNACCOUNTED_bit_that_is_NOT_write_capable),
                  ("a bit above the name tables", _p_a_bit_ABOVE_the_name_tables),
                  ("the two decoders disagreeing", _p_the_two_decoders_DISAGREE),
                  ("an unreadable taint word", _p_the_taint_word_DID_NOT_READ),
                  ("a tainted word under an empty register",
                   _p_a_TAINTED_word_under_a_register_that_licenses_NOTHING)]
        for name, planter in plants:
            w = synthetic_world_with_a_licensed_load()
            planter(w)
            moved = [f for f in interposition_findings(tuple(w["census"]),
                                                       w["licensed_loads"])
                     if "MOVED across the observation" in f]
            self.assertEqual(moved, [],
                             "planting %r moved the census across the bracket, so any red "
                             "it produces is the DELTA half speaking and says nothing about "
                             "the accounting clause: %r" % (name, moved))
        self.assertEqual(len(plants), 6, "non-vacuity: the plant list is not a stub")

    def test_the_ONE_PREDICATE_gives_TWO_VERDICTS_on_ONE_census(self):
        """THE STRONGEST FORM THIS ESTATE HAS FOR SHOWING A READING DISCRIMINATES: one
        predicate, one taint word, two registers, two different answers — and only the
        register changed between them. If the reading agreed with both, it would not be
        reading the register at all, and the whole restatement would be decoration."""
        census = {"taint": {"raw": {"ok": True, "text": "12288\n"},
                            "bits": ["OOT_MODULE", "UNSIGNED_MODULE"]}}
        self.assertEqual(taint_reading(census, THE_LICENSED_OUT_OF_TREE_LOADS)["unaccounted"],
                         [], "the delta form does not accept the world its own record "
                             "accounts for")
        self.assertEqual(taint_reading(census, ())["unaccounted"],
                         ["OOT_MODULE", "UNSIGNED_MODULE"],
                         "the SAME word under a register licensing NOTHING is accepted, so "
                         "the reading is not consulting the register")

    # ---------------------------------------------------- THE TRIPWIRE, DRIVEN
    def test_AN_UNACCOUNTED_WRITE_CAPABLE_BIT_REDS_THE_ACCOUNTING_ROW(self):
        self._red(_p_an_UNACCOUNTED_write_capable_bit,
                  NothingWriteCapableIsAttachedToTheIOPath, _THE_ACCOUNTING_ROW,
                  "a taint bit no licensed record accounts for passes the accounting row, "
                  "so the restatement removed the tripwire instead of restating it")

    def test_AN_UNACCOUNTED_WRITE_CAPABLE_BIT_REDS_THE_CENSUS_ROW(self):
        self._red(_p_an_UNACCOUNTED_write_capable_bit,
                  NothingWriteCapableIsAttachedToTheIOPath, _THE_CENSUS_ROW,
                  "an unlicensed write-capable taint bit passes the census reading")

    def test_AN_UNACCOUNTED_WRITE_CAPABLE_BIT_REDS_THE_EXHIBITION_ROW(self):
        self._red(_p_an_UNACCOUNTED_write_capable_bit,
                  TheShadowRecordsAreAtTheDECLAREDGrade, _THE_EXHIBITION_ROW,
                  "an unlicensed write-capable taint bit passes the exhibition reading")

    def test_AN_UNACCOUNTED_bit_that_is_NOT_write_capable_REDS_THE_ACCOUNTING_ROW(self):
        """The accounting row asks about ACCOUNTING and the census row asks about
        WRITE-CAPABILITY. Two questions, and this plant separates them."""
        self._red(_p_an_UNACCOUNTED_bit_that_is_NOT_write_capable,
                  NothingWriteCapableIsAttachedToTheIOPath, _THE_ACCOUNTING_ROW,
                  "a FORCED_RMMOD bit no record accounts for passes the accounting row")

    def test_the_SAME_bit_does_NOT_red_the_census_row(self):
        """The other half of the pair above. A plant that reddened both rows would prove
        the two had collapsed into one question wearing two names."""
        self._green(_p_an_UNACCOUNTED_bit_that_is_NOT_write_capable,
                    NothingWriteCapableIsAttachedToTheIOPath, _THE_CENSUS_ROW,
                    "a taint bit that is NOT write-capable reds the WRITE-CAPABLE census "
                    "reading, so that row is answering a question it does not claim")

    def test_A_BIT_ABOVE_THE_NAME_TABLES_REDS(self):
        """The hole a name-list comparison cannot see, driven."""
        self._red(_p_a_bit_ABOVE_the_name_tables,
                  NothingWriteCapableIsAttachedToTheIOPath, _THE_ACCOUNTING_ROW,
                  "a taint word carrying bit 18 — which no name table covers — passes the "
                  "accounting row, so an unnamed bit can stand set behind a clean name list")

    def test_THE_TWO_DECODERS_DISAGREEING_REDS(self):
        self._red(_p_the_two_decoders_DISAGREE,
                  NothingWriteCapableIsAttachedToTheIOPath, _THE_ACCOUNTING_ROW,
                  "the host and the guest decode the same word differently and the row is "
                  "green, so one wrong name table would never be found")

    def test_AN_UNREADABLE_TAINT_WORD_REDS_rather_than_reading_as_clean(self):
        self._red(_p_the_taint_word_DID_NOT_READ,
                  NothingWriteCapableIsAttachedToTheIOPath, _THE_ACCOUNTING_ROW,
                  "a census that could not read its taint word passes the accounting row, "
                  "which is an unrun check reported as an absence")

    def test_THE_EXERCISE_CONDITION_BITES_a_world_that_licensed_NOTHING(self):
        """CLAUSE (1) AS AN ASSERTION. The live guest's own taint value under W2c's own
        register — zero licensed loads — must still red, exactly as it did before this unit
        touched anything. This is the row that proves the restatement did not quietly turn
        `taint == 0` into a comment."""
        self._red(_p_a_TAINTED_word_under_a_register_that_licenses_NOTHING,
                  NothingWriteCapableIsAttachedToTheIOPath, _THE_ACCOUNTING_ROW,
                  "a tainted world whose register records ZERO licensed loads passes, so "
                  "the exercise condition is written down and not enforced",
                  world=synthetic_world())

    # ------------------------------------------------- THE REGISTER IS NOT A RUBBER STAMP
    def test_the_ACCOUNTED_SET_EXCLUDES_a_write_capable_bit_it_could_have_swallowed(self):
        """THE CONTROL AIMED AT THE CONTROLS. The newest disguise in this estate is a
        positive control shaped to fit the same wrong assumption as the filter it certifies,
        so the question to ask of every control here is: COULD THIS HAVE CAUGHT THE REGISTER
        BEING WRONG? This one could. A register populated from the observed value — the easy
        and fatal way to write it — would account for every bit the guest happens to hold and
        would therefore agree with any world it was ever shown. The accounted set is asserted
        against HAND-COMPUTED LITERALS and asserted NOT to contain a write-capable bit, so a
        register that had grown to swallow everything fails here first."""
        acc = accounted_taint_bits(THE_LICENSED_OUT_OF_TREE_LOADS)
        self.assertEqual(acc, ["OOT_MODULE", "UNSIGNED_MODULE"],
                         "the accounted set is not the hand-computed pair an unsigned "
                         "out-of-tree load implies: %r" % (acc,))
        self.assertNotIn("PROPRIETARY_MODULE", acc,
                         "the register accounts for PROPRIETARY_MODULE, which no load in "
                         "this estate performed — an accounted set that grows to fit the "
                         "world cannot red")
        self.assertLess(len(acc), len(_TAINT_BIT_NAMES),
                        "the register accounts for every nameable bit, so no bit is left "
                        "that could ever be unaccounted and the tripwire cannot fire")

    def test_the_REGISTER_names_the_module_this_estate_ACTUALLY_licensed(self):
        """The register is a transcription of a record, so its subject is checkable against
        the constant the shim rows use rather than being a name this file made up."""
        self.assertEqual([r["module"] for r in THE_LICENSED_OUT_OF_TREE_LOADS],
                         [GOVSHIM_MODULE])
        for r in THE_LICENSED_OUT_OF_TREE_LOADS:
            self.assertTrue(r["record"].strip(), "a licensed load with no record cited")
            self.assertGreater(len(r["basis"]), 80,
                               "the bits are stated with no basis, so a reader cannot tell "
                               "a hand-computed literal from a value read off the guest")
            for bit in r["accounts_for"]:
                self.assertIn(bit, set(_TAINT_BIT_NAMES.values()))

    def test_the_HOST_decoder_answers_HAND_COMPUTED_cases(self):
        """The host table is the thing the guest is checked against, so it is checked
        against arithmetic done by hand: 0 -> nothing; 1 = bit 0; 4096 = bit 12;
        12288 = 4096 + 8192 = bits 12 and 13; and the inverse round-trips."""
        self.assertEqual(taint_bits_host(0), [])
        self.assertEqual(taint_bits_host(1), ["PROPRIETARY_MODULE"])
        self.assertEqual(taint_bits_host(4096), ["OOT_MODULE"])
        self.assertEqual(taint_bits_host(12288), ["OOT_MODULE", "UNSIGNED_MODULE"])
        self.assertEqual(taint_value_of(["OOT_MODULE", "UNSIGNED_MODULE"]), 12288)
        self.assertEqual(taint_value_of([]), 0)
        self.assertNotEqual(taint_value_of(taint_bits_host(262144)), 262144,
                            "bit 18 round-trips through the name table, so the "
                            "coverage comparison could never report an uncovered bit")

    # ---------------------------------------------------------- THE CAP, DRIVEN NOT WRITTEN
    def test_a_SECOND_UNLICENSED_LOAD_moves_NO_TAINT_BIT_and_the_MODULE_SET_catches_it(self):
        """THE HONEST LIMIT OF THIS ROW, EXHIBITED RATHER THAN CONFESSED IN PROSE.

        Taint is a KERNEL-WIDE FLAG WORD, not a per-module ledger. On a boot where a
        licensed unsigned out-of-tree load has already set bits 12 and 13, a SECOND and
        entirely unlicensed unsigned out-of-tree load sets NO NEW BIT — so no wording of the
        accounting rule can make the taint half see it, and claiming otherwise would be the
        row promising a reach it does not have.

        WHAT ACTUALLY CATCHES IT is the module-set half of the same census, comparing NAMES
        across the bracket. Both halves are asserted here, in one row, because the claim
        that matters is the CONJUNCTION: the tripwire against unlicensed attachment survives,
        carried by two halves, and a reader who took either half alone would be wrong in
        opposite directions."""
        w = synthetic_world_with_a_licensed_load()
        before_bits = taint_reading(w["census"][1], w["licensed_loads"])
        _p_a_SECOND_and_UNLICENSED_out_of_tree_module(w)
        after_bits = taint_reading(w["census"][1], w["licensed_loads"])
        self.assertEqual(before_bits["raw"], after_bits["raw"],
                         "this substrate moved the taint word, so it is not exhibiting the "
                         "case it claims to exhibit")
        self.assertEqual(after_bits["unaccounted"], [],
                         "the taint half reports the second load, which it cannot do — the "
                         "substrate is wrong, not the rule")
        findings = interposition_findings(tuple(w["census"]), w["licensed_loads"])
        self.assertTrue([f for f in findings if "modules" in f],
                        "a SECOND, UNLICENSED out-of-tree module is resident and NEITHER "
                        "half of the census speaks — the tripwire is gone: %r" % (findings,))
        self._red(lambda _w: None, NothingWriteCapableIsAttachedToTheIOPath,
                  _THE_CENSUS_ROW,
                  "the shipped census row passes with an unlicensed module resident",
                  world=w)

    # ------------------------------------- THE ONE DIRECTION THAT IS DISCLOSED, NOT RED
    def test_a_RECORD_accounting_for_bits_the_world_does_NOT_show_is_DISCLOSED_not_RED(self):
        """RAISED AS A CORRECTION TO THE RULING'S WORDING, AND IMPLEMENTED THE SAFE WAY.

        :823 states the delta form as an EQUALITY — `the taint set equals EXACTLY the bits
        the licensed loads' own records account for` — and then names ONE failure: `a bit NO
        licensed record accounts for REDS`. The two are not the same rule. Equality also
        reds the OPPOSITE direction: a record accounting for bits the world does not show.

        THAT DIRECTION IS NEVER AN ATTACHMENT. A bit that is ABSENT is strictly LESS
        attachment, and reddening a row about attachment on a world holding less of it is
        the unsatisfiable-when-exercised defect this file has met four times. It is also
        reachable by lawful means: a guest rebooted before the recorded load runs reads 0
        against a register that accounts for two bits, and the acceptance arm's own ordering
        decides which side of that moment the census is taken on — so the strict reading
        would make the verdict depend on test order.

        SO: `unaccounted` REDS, always, on every world. `unexercised` is DISCLOSED on the
        reading and is never a red. The gap is RAISED in this unit's entry rather than
        filled silently, and this row is the mechanical statement of what was done."""
        w = synthetic_world()
        w["licensed_loads"] = THE_LICENSED_OUT_OF_TREE_LOADS   # register: two bits
        r = taint_reading(w["census"][1], w["licensed_loads"])  # world: taint 0
        self.assertEqual(r["raw"], "0")
        self.assertEqual(r["unexercised"], ["OOT_MODULE", "UNSIGNED_MODULE"],
                         "the reading does not disclose the direction it declines to red")
        self.assertEqual(r["unaccounted"], [])
        res = self._run(w, NothingWriteCapableIsAttachedToTheIOPath, _THE_ACCOUNTING_ROW)
        self.assertTrue(res.wasSuccessful(),
                        "a world holding LESS taint than its register accounts for reds "
                        "the accounting row: %r" % (res.failures + res.errors,))


# =======================================================================================
# EP-29 W3a — THE NET AMEND (ADDENDUM 8 §1 claims C0-C2, §2's W3a item)
#
# :712 MEASURED AND :722 RULED; THIS SECTION EXECUTES THE RULING. v1.22.0 declared
# `device-intake@net` a threshold of 3518 arrivals, derived from the arrival COUNT column
# on DEV-LAW-INTAKE's first derivation constraint — that the count column is EXACT where
# the rate column moves. W2c drove two further full runs and the constraint's own property
# FAILS FOR THIS CLASS ACROSS RUNS. So the value is WITHDRAWN FROM ENFORCEABLE LAW and
# declared UNESTABLISHED beside this declaration's own per-act unit, on the pack's own
# precedent.
#
# WHAT IS DELIBERATELY NOT DONE, because it is the trap the ruling names: NO MARGIN. A
# margin over four points on one guest and one boot is ASSERTED AND NOT DERIVED, which is
# the class DEV-LAW-INTAKE's own constraints refuse, and the careless numbers are planted
# as driven red worlds rather than described — exactly as W2b planted 3518 / 1600 when it
# withdrew this declaration's unit.
#
# THE ROWS RECOMPUTE THE WITHDRAWAL. A row that read the pack's `null` and asserted `null`
# would pass on any pack that happened to carry one and would say nothing about whether the
# withdrawal was earned. The derivation is re-run over the THREE-RUN table and it returns
# BLOCK'S NUMBER AND REFUSES NET'S — which is this law's PER-DEVICE-CLASS constraint
# measuring itself, and it is why block's cap is CONFIRMED here rather than merely left
# alone.
#
# THE FOUNDING MOVES AND BYTE-UNCHANGED IS THE FAILING OUTCOME. That is the fourth
# different requirement in six units on this line — W1c unchanged, W2a unchanged, W2b
# moved, W2c unchanged, W3a MOVED — and it is asserted here rather than carried from the
# habit of the pass before, which required the opposite.
# =======================================================================================

#: THIS pass's own pre-write commit, taken with `git rev-parse HEAD` before any write
#: (§A53 — `git checkout --` no longer undoes a write since the 2026-08-03 autosync repair,
#: so the commit is TAKEN and not trusted). It is the 1.22.0 ERA: the world W3a moved off,
#: and the era every W2b and W2c assertion this move falsified is pinned to.
#: PINNED BY CONTENT AND NEVER BY VERSION NUMBER — `era_pin`'s own stated cap and this
#: estate's most expensive known trap. A row checks the blob's digest against the sha256
#: W2b's close recorded rather than trusting this comment.
W3A_BEFORE_COMMIT = "ac0372516c8a2fe6d32dd48bfeefb3c0feb47790"
W3A_BEFORE_VERSION = "1.22.0"
W3A_AFTER_VERSION = "1.23.0"
W3A_BEFORE_PACK_SHA = "971abf9d0bafa1755fa67a68b1e1ba8b8cce69b25d029d113300ca39b280e6cc"

#: THE THREE-RUN ARRIVAL-COUNT TABLE — the measurement that withdrew net's threshold and
#: confirmed block's. Transcribed from EP-29 W2c's BUILD-PROGRESS entry of 2026-08-13 (the
#: raise-4 table) and from board `:712`, which routed it. Each row is
#: (device, device_class, level, (run 1 repeats, run 2 repeats, run 3 repeats)) where RUN 1
#: IS W2a's PACK RUN — the run every v1.22.0 value was derived from — and runs 2 and 3 are
#: the two full runs W2c drove on the SAME GUEST and the SAME BOOT with the same commands
#: and the same three repeats per cell.
#:
#: THE COUNT COLUMN AND ONLY IT, exactly as W2b's own table: DEV-LAW-INTAKE's first
#: derivation constraint bars the rate column from carrying law, and this table is what
#: measured that constraint's own premise.
W2_THREE_RUN_CELLS = (
    ("virtio0", "net", "L1", ((384, 388, 390), (379, 395, 395), (382, 382, 387))),
    ("virtio0", "net", "L2", ((3518, 3509, 3489), (2556, 3281, 2540), (3443, 2526, 2538))),
    ("virtio1", "block", "L1", ((768, 768, 768), (768, 768, 768), (768, 768, 768))),
    ("virtio1", "block", "L2", ((6144, 6144, 6144), (6144, 6144, 6144), (6144, 6144, 6144))),
    ("virtio2", "block", "L1", ((276, 276, 276), (276, 276, 276), (276, 276, 276))),
    ("virtio2", "block", "L2", ((2208, 2208, 2208), (2208, 2208, 2208), (2208, 2208, 2208))),
)

#: The three-run max/min ratios board `:712` states, per cell. Carried so the transcription
#: above is checked against the ruling's own figures rather than trusted, and so a
#: transposed digit is a red row instead of a silent change of ground.
W2_THREE_RUN_RATIOS = {("virtio0", "L1"): 1.0422, ("virtio0", "L2"): 1.3927,
                       ("virtio1", "L1"): 1.0000, ("virtio1", "L2"): 1.0000,
                       ("virtio2", "L1"): 1.0000, ("virtio2", "L2"): 1.0000}


def runs_of_class(cells, device_class):
    return tuple(c for c in cells if c[1] == device_class)


def cap_from_runs(cells):
    """THE THRESHOLD'S DERIVATION, RE-RUN OVER THREE RUNS. Returns `(value, reason)`, the
    shape `unit_from_cells` already established one field over.

    W2b's `cap_from_cells` derives the threshold as max(A) over the measured population, on
    I9: a window of A arrivals produces ceil(A / cap) covering records, so the record count
    stays at ONE for every window in the population exactly when cap >= max(A), and the
    smallest such value is max(A) itself.

    THAT DERIVATION NEEDS max(A) TO BE A PROPERTY OF THE DEVICE CLASS AND NOT OF ONE RUN,
    and the property it leans on is DEV-LAW-INTAKE's FIRST derivation constraint: the
    arrival COUNT column is EXACT where the rate column moves. This function asks that
    question of three runs instead of one.

    THE TEST IS EXACTNESS AND NOT A TOLERANCE, and that is the whole reason this pass
    declines to widen the number: the per-cell maximum must be the SAME NUMBER in every
    run. A tolerance would be a bound this pass invented from four points on one guest —
    asserted and not derived, the class DEV-LAW-INTAKE's own constraints refuse. It is the
    same exactness `unit_from_cells` applies to its ratio set: a set of size one, or no
    value at all."""
    moved = []
    for dev, _cls, lvl, runs in cells:
        maxima = tuple(max(rep) for rep in runs)
        if len(set(maxima)) != 1:
            moved.append("%s %s %s" % (dev, lvl, " / ".join(str(m) for m in maxima)))
    if moved:
        return None, ("the per-cell MAXIMUM moves between runs, so no count in this table is "
                      "the population's maximum: " + "; ".join(moved))
    return (max(max(rep) for _d, _c, _l, runs in cells for rep in runs),
            "the per-cell maximum is identical in every run, so max(A) is a property of the "
            "class and not of one run")


def careless_margin(cells):
    """THE NUMBER A PASS WOULD WRITE TO KEEP THIS CLASS ENFORCEABLE, computed the way that
    pass would compute it rather than typed in: the observed ceiling widened by the spread
    of the CELL THAT HOLDS IT, ceil(max(A) * max(A)/min(A)) over that cell. It has no
    derivation behind it, and it is planted as a red world below for exactly that reason.

    [THE FIRST DRAFT OF THIS FUNCTION TOOK max AND min ACROSS THE WHOLE CLASS and returned
    32656 — the L2 ceiling widened by the L1 floor, two different load levels divided into
    each other. It was caught by running it, not by reading it. Kept in the note because it
    is the same species as the value being withdrawn: a number whose population was never
    stated.]"""
    holder = max(cells, key=lambda c: max(x for rep in c[3] for x in rep))
    counts = [x for rep in holder[3] for x in rep]
    return int(math.ceil(max(counts) * (max(counts) / float(min(counts)))))


def _tolerant_cap(cells, tol):
    """THE DERIVATION `cap_from_runs` DELIBERATELY IS NOT: exactness replaced by a tolerance,
    so the choice between them can be exhibited rather than argued. Every cell's own
    three-run max/min must sit within `tol`, and then max(A) is returned."""
    for _d, _c, _l, runs in cells:
        counts = [x for rep in runs for x in rep]
        if max(counts) / float(min(counts)) > tol:
            return None
    return max(x for _d, _c, _l, runs in cells for rep in runs for x in rep)


class TheNetThresholdIsWithdrawnLawfully(unittest.TestCase):
    """C1 — :712's ruling EXECUTED: net's threshold value joins `net unit` as UNESTABLISHED,
    under the pack's OWN precedent, with the grade untouched and block's cap confirmed."""

    def _by_class(self):
        return {d["device_class"]: d for d in intake_declarations(live_pack())}

    def _era_by_class(self):
        return {d["device_class"]: d
                for d in intake_declarations(pack_at(W3A_BEFORE_COMMIT))}

    # ------------------------------------------------------------------ the withdrawal
    def test_the_NET_threshold_carries_NO_VALUE_AND_NO_CELL(self):
        """`3518 surviving as an enforceable ceiling REDS` — the plan's own red world, in
        the one field a consumer would read."""
        t = self._by_class()["net"]["max_arrivals"]
        self.assertIsNone(t["value"])
        self.assertIsNone(t["cell"], "a withdrawn value still names a calibration cell, so "
                                     "the cell it could not be derived from is still cited")

    def test_the_NET_threshold_is_DECLARED_unestablished_and_never_OMITTED(self):
        """DECLARE-INTAKE's own text: an unestablished value is declared unestablished,
        never omitted — the no-bare-form instruction at parameter ABSENCES. The value's
        absence must be visible as a MISSING NUMBER inside a PRESENT field, never as a
        missing field."""
        net = self._by_class()["net"]
        self.assertIn("max_arrivals", net)
        self.assertIn("max_arrivals", net["derived_values"],
                      "a withdrawn value dropped off `derived_values` would shrink the "
                      "audited population to hide its own absence")
        t = net["max_arrivals"]
        for key in ("value", "cell", "population", "basis", "why_this_value"):
            self.assertIn(key, t)
        self.assertIn("NOT ESTABLISHED", t["basis"])
        self.assertTrue(t["population"])

    def test_the_withdrawal_is_RECOMPUTED_from_the_THREE_RUN_table(self):
        """The row that makes this a MEASURED withdrawal rather than an asserted one: the
        derivation is re-run over the three runs and REFUSES, and the pack carries the
        refusal."""
        value, why = cap_from_runs(runs_of_class(W2_THREE_RUN_CELLS, "net"))
        self.assertIsNone(value, "the three-run table now yields a net threshold, so the "
                                 "ground of this whole amend has moved and it must be "
                                 "re-derived rather than kept")
        self.assertIn("MAXIMUM moves between runs", why)
        self.assertIsNone(self._by_class()["net"]["max_arrivals"]["value"])

    def test_the_BLOCK_cap_is_CONFIRMED_over_the_THREE_RUN_population(self):
        """`block's cap moving REDS`, and the confirmation is a RE-DERIVATION rather than a
        decision to leave it alone: the same function over the wider table returns the same
        number W2b derived from one run."""
        value, why = cap_from_runs(runs_of_class(W2_THREE_RUN_CELLS, "block"))
        self.assertEqual(value, 6144)
        self.assertIn("identical in every run", why)
        self.assertEqual(self._by_class()["block"]["max_arrivals"]["value"], value)
        self.assertEqual(cap_from_cells(W2A_BLOCK_CELLS), value,
                         "the one-run derivation and the three-run derivation disagree "
                         "about block, which would put block in net's position")

    def test_the_reproducibility_verdict_ANSWERS_BOTH_WAYS(self):
        """NON-VACUITY OF THE INSTRUMENT ITSELF. A test of reproducibility that refused
        every class would withdraw block's cap too and prove nothing about net; one that
        accepted every class could not have withdrawn anything. It must answer both ways on
        the SAME table, and it does."""
        self.assertIsNone(cap_from_runs(runs_of_class(W2_THREE_RUN_CELLS, "net"))[0])
        self.assertIsNotNone(cap_from_runs(runs_of_class(W2_THREE_RUN_CELLS, "block"))[0])

    def test_the_derivation_is_not_a_CONSTANT_FUNCTION(self):
        """The negative-result test on the instrument every row above rests on: a function
        returning the same verdict whatever the table is not a derivation. Moving ONE
        reading of ONE block run flips block from confirmed to refused."""
        cells = list(runs_of_class(W2_THREE_RUN_CELLS, "block"))
        dev, cls, lvl, runs = cells[0]
        bumped = (tuple(r + 1 for r in runs[0]),) + runs[1:]
        cells[0] = (dev, cls, lvl, bumped)
        self.assertIsNone(cap_from_runs(tuple(cells))[0])
        self.assertIsNotNone(cap_from_runs(runs_of_class(W2_THREE_RUN_CELLS, "block"))[0])

    def test_the_EXACTNESS_CHOICE_MATTERS_because_a_TOLERANCE_WOULD_HAVE_KEPT_THE_VALUE(self):
        """NON-VACUITY OF THE DERIVATION'S OWN CHOICE, and it is the trap in one comparison.
        If exactness and a tolerance gave the same verdict, refusing a tolerance would be a
        sentence with a colon in it. They do not: a tolerance of 1.40 — just wide enough to
        swallow this class's measured 1.3927 — returns EXACTLY the 3518 this pass withdrew.
        THE REASON NO TOLERANCE IS ADOPTED IS NOT THAT IT WOULD BE UNSAFE, IT IS THAT
        NOTHING IN THIS TABLE DERIVES ONE: four points on one guest and one boot name no
        number, and a tolerance chosen to fit them is the margin under another name."""
        net = runs_of_class(W2_THREE_RUN_CELLS, "net")
        self.assertIsNone(cap_from_runs(net)[0])
        self.assertEqual(_tolerant_cap(net, 1.40), 3518)
        self.assertIsNone(_tolerant_cap(net, 1.30),
                          "a tolerance below the measured spread already refuses, so the "
                          "exhibit above is not showing what it claims")
        self.assertEqual(_tolerant_cap(runs_of_class(W2_THREE_RUN_CELLS, "block"), 1.0), 6144,
                         "block is exact, so a tolerance of ZERO width still returns its cap "
                         "— which is why the split is between classes and not between tests")

    def test_the_transcribed_table_carries_THE_RATIOS_THE_RULING_CITES(self):
        """The table above is a transcription and a transposed digit would change the
        ground silently. Each cell's three-run max/min is recomputed and compared with the
        figure board `:712` and W2c's entry state, to four decimal places."""
        for dev, _cls, lvl, runs in W2_THREE_RUN_CELLS:
            counts = [c for rep in runs for c in rep]
            got = max(counts) / float(min(counts))
            self.assertAlmostEqual(got, W2_THREE_RUN_RATIOS[(dev, lvl)], places=4,
                                   msg="%s %s" % (dev, lvl))

    # ------------------------------------------------- what the amend must NOT have moved
    def test_the_GRADE_stands_UNTOUCHED_at_window_for_both_classes(self):
        """`the GRADE — window/threshold, never per-interrupt — stands untouched`. A
        PRESENCE test, for the reason W2b gave when it wrote the original: an absence test
        over the law's own forbidding sentence inverts, because the sentence contains the
        words in order to forbid them."""
        era = self._era_by_class()
        for cls, d in self._by_class().items():
            self.assertEqual(d["grade"], "window", cls)
            self.assertEqual(d["grade"], era[cls]["grade"], cls)

    def test_the_LAW_TEXT_itself_is_BYTE_UNMOVED(self):
        """The amend is to a DECLARATION and not to the law it is made under. DEV-LAW-INTAKE
        governs the grade; the grade did not move, so its text must not have either."""
        era = rules_of(pack_at(W3A_BEFORE_COMMIT))["DEV-LAW-INTAKE"]
        now = rules_of(live_pack())["DEV-LAW-INTAKE"]
        self.assertEqual(now, era, "the law text moved in a pass that amends a declaration")

    def test_BLOCKS_WHOLE_DECLARATION_is_BYTE_UNMOVED(self):
        """`block's cap CONFIRMED at :712 and untouched` — asserted over the whole
        declaration and not only over the number, because a confirmation that quietly moved
        a limit or a basis beside the value would read as untouched on the page."""
        self.assertEqual(self._by_class()["block"], self._era_by_class()["block"])

    def test_the_OTHER_UNESTABLISHED_VALUE_is_unmoved(self):
        """`net unit` is the precedent this amend follows and not a thing it may edit."""
        self.assertEqual(self._by_class()["net"]["arrivals_per_admitted_act"],
                         self._era_by_class()["net"]["arrivals_per_admitted_act"])

    def test_the_PRECEDENT_FORM_is_the_one_taken(self):
        """`under the pack's OWN precedent` made checkable: the two unestablished values in
        this declaration carry the SAME KEY SHAPE and the same two null fields, so the
        threshold's withdrawal is the unit's form and not a second invention."""
        net = self._by_class()["net"]
        unit, thresh = net["arrivals_per_admitted_act"], net["max_arrivals"]
        self.assertEqual(sorted(unit), sorted(thresh))
        for v in (unit, thresh):
            self.assertIsNone(v["value"])
            self.assertIsNone(v["cell"])
            self.assertIn("NOT ESTABLISHED", v["basis"])
            self.assertTrue(v["population"])
            self.assertTrue(v["why_this_value"])

    # ------------------------------------------------- what the withdrawal now declares
    def test_the_declaration_SAYS_it_bounds_no_window_while_the_threshold_is_unestablished(self):
        """A declaration naming no absence reads as covering everything it did not mention,
        which is DECLARE-INTAKE's own reason for requiring `does_not_declare`. The absence
        the withdrawal creates is the biggest one this declaration has ever carried."""
        net = self._by_class()["net"]
        joined = " ".join(net["does_not_declare"])
        self.assertIn("THRESHOLD", joined)
        self.assertIn("ADMITTED BY NOTHING", joined)
        self.assertIn("REFUSES", joined)
        self.assertEqual(len(net["does_not_declare"]),
                         len(self._era_by_class()["net"]["does_not_declare"]) + 1,
                         "the withdrawal added no absence, or added more than one")

    def test_the_CLOSER_that_cannot_fire_SAYS_SO(self):
        """The closers are unchanged in NAME — event-based, `max_arrivals` and `unbind` —
        and the one keyed on a withdrawn threshold states that it is inert. A closer
        described as firing on a cap that does not exist is law text misdescribing its own
        declaration."""
        net = self._by_class()["net"]
        self.assertEqual(sorted(c.split(" ")[0] for c in net["closers"]),
                         ["max_arrivals", "unbind"])
        self.assertIn("INERT", net["closers"][0])
        self.assertEqual(net["closers"][1], self._era_by_class()["net"]["closers"][1],
                         "the unbind closer moved and nothing in this amend touches it")

    def test_every_LIMIT_still_carries_its_POPULATION_and_BASIS(self):
        """§A51's declared-field form, over the limits this amend rewrote. A rewritten limit
        that dropped its population would be the clause failing at the one moment its
        subject changed."""
        for d in intake_declarations(live_pack()):
            self.assertTrue(d["limits"], d["intake"])
            for lim in d["limits"]:
                for key in ("limit", "population", "basis"):
                    self.assertTrue(lim.get(key), "%s: %r" % (d["intake"], lim))

    def test_the_LIMIT_COUNT_did_not_shrink(self):
        """Limits are AMENDED here, never dropped: a withdrawal that removed the limits
        whose subject it removed would delete the record of what was known."""
        self.assertEqual(len(self._by_class()["net"]["limits"]),
                         len(self._era_by_class()["net"]["limits"]))

    def test_the_ENGINE_HOLDS_NO_CONSUMER_OF_THIS_THRESHOLD(self):
        """WHAT THE WITHDRAWAL COSTS TODAY, measured rather than reasoned: nothing in `src/`
        reads this declaration at all, which is W2b's own raise 4 (`today an intake
        declaration is law nothing cites`) still standing. The intake ENGINE is W3b's shim
        contract, so the value leaves enforceable law before any code enforced it — and the
        row carries a POSITIVE CONTROL, because a search that cannot find anything would
        return this same zero."""
        src = os.path.join(REPO, "src")
        hits, control = [], []
        for root, _dirs, files in os.walk(src):
            for f in files:
                if not f.endswith(".py"):
                    continue
                p = os.path.join(root, f)
                with open(p, encoding="utf-8") as fh:
                    body = fh.read()
                if "max_arrivals" in body or "DEV-LAW-INTAKE" in body:
                    hits.append(os.path.relpath(p, REPO))
                if "OP_CHECKS" in body:
                    control.append(os.path.relpath(p, REPO))
        self.assertTrue(control, "the walk found no file containing a token that IS there, "
                                 "so its empty answer below says nothing")
        self.assertEqual(hits, [], "the engine reads the intake declaration, so withdrawing "
                                   "a value from it changes behaviour this pass has not "
                                   "measured")


class TheFoundingMovedAtW3a(unittest.TestCase):
    """C2 — the founding MOVES lawfully at W3a and BYTE-UNCHANGED IS THE FAILING OUTCOME.

    ADDENDUM 6 C4's empty-ground exception rides unchanged and is a CAP rather than a
    branch: it applies where the ground for the pass does not exist. The ground here is
    :722's ruling plus a three-run table, both of which exist, so the red world is reached
    and does not fire."""

    def test_the_pack_version_moved_one_MINOR_from_W3as_own_BEFORE(self):
        # [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14, charter §A57, and this row is the FIRST
        # NAMED MEMBER of the worklist W3a itself handed forward at NEXT_MOVE_FALSIFIES. CAUSE:
        # the founding moved 1.23.0 -> 1.24.0. ASSERTED: `live_pack()` as W3a's AFTER.
        # SUPERSEDED: `pack_at(W3A_AFTER_ERA_COMMIT)`. REMAINS TRUE: W3a moved the founding
        # exactly one MINOR, 1.22.0 -> 1.23.0, which is a fact about two commits. GIVEN UP:
        # nothing; the LIVE version is asserted by this pass's own battery.]
        self.assertEqual(pack_at(W3A_BEFORE_COMMIT)["founding_version"], W3A_BEFORE_VERSION)
        self.assertEqual(pack_at(W3A_AFTER_ERA_COMMIT)["founding_version"], W3A_AFTER_VERSION)

    def test_the_founding_is_NOT_byte_unchanged(self):
        era = era_pin.blob_at(W3A_BEFORE_COMMIT, era_pin.PACK_PATH)
        with open(PACK_PATH, "rb") as fh:
            live = fh.read()
        self.assertNotEqual(hashlib.sha256(era).hexdigest(),
                            hashlib.sha256(live).hexdigest(),
                            "the founding is byte-unchanged after a LANDED W3a, and this "
                            "movement's requirement is the inverse of the unit before it")

    def test_the_designation_record_carries_the_NEW_version(self):
        # [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14, charter §A57, W3a's own worklist member 2.
        # CAUSE: the founding moved, so a world booted from the LIVE tree stamps 1.24.0 and this
        # row's constant describes W3a's era. ASSERTED: `_World()`, the live tree. SUPERSEDED:
        # `_World(pack_at(W3A_AFTER_ERA_COMMIT))`, W3a's own era. REMAINS TRUE, and the row stays
        # a genuine TWO-SIDED check rather than one reading wearing two labels: a pack read out
        # of git on one side, a designation record stamped by the installer on the other. GIVEN
        # UP: nothing — the LIVE stamp is asserted against 1.24.0 by this pass's own battery.]
        fs = [e for e in _World(pack_at(W3A_AFTER_ERA_COMMIT)).store.all()
              if e["action"] == "FOUND-STORE"][0]
        self.assertEqual(dict(fs["payload"])["founding_version"], W3A_AFTER_VERSION)

    def test_THE_RULED_VERSION_TEST_the_1_22_0_pack_byte_unchanged_STILL_LOADS(self):
        """THE RULED TEST, BUILDER-EXECUTED: loads -> MINOR; does not -> MAJOR -> STOP TO
        THE MENTOR. It answered MINOR and MAJOR was never reached. Kept as a standing row so
        a later reader re-checks the answer rather than taking it."""
        install_module._validate(install_module.records(pack_at(W3A_BEFORE_COMMIT)))

    def test_THE_RULED_VERSION_TEST_the_GENESIS_RECORDS_load_under_the_amended_law(self):
        """The second arm. NOTHING IS DECLARED AND NOTHING RETIRED by this pass, so the
        census is the interesting number precisely because it does NOT move: the amendment
        is inside one declaration record and a census that moved would mean something was
        smuggled in beside it.

        [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14, charter §A57. CAUSE: this pass minted an
        operation, so the LIVE CREATE-OP count is 76 and no longer W3a's AFTER. ASSERTED:
        `live_pack()` and a world booted from it. SUPERSEDED: `pack_at(W3A_AFTER_ERA_COMMIT)`
        throughout, including the booted world the registry half reads — both sides move
        together or the row compares two eras and calls the difference a defect. REMAINS TRUE:
        W3a declared and retired nothing, 43 rules and 75 operations either side of its own
        move. GIVEN UP: nothing — this pass's census is asserted by its own battery, where the
        count moves by exactly one operation and the difference is NAMED.]"""
        era = install_module.records(pack_at(W3A_BEFORE_COMMIT))
        now = install_module.records(pack_at(W3A_AFTER_ERA_COMMIT))
        self.assertEqual(len([r for r in era if r.get("action") == "CREATE-RULE"]), 43)
        self.assertEqual(len([r for r in now if r.get("action") == "CREATE-RULE"]), 43)
        self.assertEqual(len([r for r in era if r.get("action") == "CREATE-OP"]), 75)
        self.assertEqual(len([r for r in now if r.get("action") == "CREATE-OP"]), 75)
        install_module._validate(now)
        active = _World(pack_at(W3A_AFTER_ERA_COMMIT)).views.active_rules()
        for r in now:
            if r.get("action") == "CREATE-RULE":
                self.assertIn(r["payload"]["rule_id"], active,
                              "a genesis rule record does not reach the live registry")

    def test_the_loader_that_accepted_them_CAN_REFUSE(self):
        """Without this the two rows above are an instrument that cannot report its own
        failure. The plant lands on the definition this pass's declaration is made under."""
        p = copy.deepcopy(live_pack())
        planted = 0
        for st in p["steps"]:
            for r in st["records"]:
                if (r.get("payload") or {}).get("name") == "DECLARE-INTAKE":
                    r["payload"]["definition"]["checks"] = [
                        {"check": "planted_unknown_kind", "cite": "DEV-LAW-INTAKE"}]
                    planted += 1
        self.assertEqual(planted, 1)
        with self.assertRaises(Exception) as ctx:
            install_module._validate(install_module.records(p))
        self.assertIn("planted_unknown_kind", str(ctx.exception))

    def test_the_DECLARED_LAW_CENSUS_did_not_move_in_either_direction(self):
        """C1's `the declared-law census before/after`, and its answer here is a pair of
        EMPTY SETS. A law amend that added or retired anything would be doing something
        beside the withdrawal, and the census is what makes that visible.

        [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14, charter §A57, W3a's own worklist member 3.
        CAUSE: this pass DECLARED an operation, which is exactly what this row reports as a
        defect — correctly, about a pass that is not W3a. ASSERTED: `live_pack()`. SUPERSEDED:
        `pack_at(W3A_AFTER_ERA_COMMIT)`. REMAINS TRUE: W3a's two census answers were a pair of
        EMPTY SETS. GIVEN UP: nothing — this pass's own census row names its one addition.]"""
        for reader in (ops_of, rules_of):
            era = set(reader(pack_at(W3A_BEFORE_COMMIT)))
            now = set(reader(pack_at(W3A_AFTER_ERA_COMMIT)))
            self.assertEqual(sorted(now - era), [], "this pass declared something new")
            self.assertEqual(sorted(era - now), [], "this pass retired something")

    def test_the_RECORD_and_STEP_counts_did_not_move(self):
        """The amend edits one record in place, on W1a's own AMEND precedent — it does not
        create beside it. A new step or a second declaration record would mint two names for
        one act class.

        [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14, charter §A57, W3a's own worklist member 4.
        CAUSE: this pass appended ONE CREATE-OP record, so the live record total is W3a's plus
        one. ASSERTED: `live_pack()`. SUPERSEDED: `pack_at(W3A_AFTER_ERA_COMMIT)`. REMAINS TRUE:
        W3a's amend edited one record IN PLACE and created nothing beside it. GIVEN UP: nothing
        — this pass's own row asserts records +1 with steps unmoved, which is the right claim
        about a pass that mints an operation.]"""
        era, now = pack_at(W3A_BEFORE_COMMIT), pack_at(W3A_AFTER_ERA_COMMIT)
        self.assertEqual(len(era["steps"]), len(now["steps"]))
        self.assertEqual(sum(len(s["records"]) for s in era["steps"]),
                         sum(len(s["records"]) for s in now["steps"]))
        self.assertEqual(len(intake_declarations(now)), 2)

    def test_the_ENGINE_moved_ZERO_lines(self):
        """Asserted against the ERA's bytes rather than against `git diff`, because a
        working-tree diff empties the moment the two-minute autosync commits and would then
        pass whatever had been written.

        [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14, charter §A57, W3a's own worklist member 5.
        CAUSE: a check kind IS engine vocabulary, so this pass's licensed landing moved
        `src/kernel/opdefs.py`. ASSERTED: the era's engine bytes against the LIVE tree's.
        SUPERSEDED: against `W3A_AFTER_ERA_COMMIT`'s. REMAINS TRUE: W3a moved zero engine lines,
        which is what made its MINOR mean what it said, and all four paths are still compared.
        GIVEN UP: nothing — that the live engine moved in exactly ONE file, and which, is
        asserted by this pass's own battery over a population of eleven engine surfaces.]"""
        for path in ("src/kernel/opdefs.py", "src/subsystems/devices.py",
                     "src/founding/install.py", "src/observe/windows.py"):
            era = era_pin.blob_at(W3A_BEFORE_COMMIT, path)
            after = era_pin.blob_at(W3A_AFTER_ERA_COMMIT, path)
            self.assertEqual(hashlib.sha256(era).hexdigest(),
                             hashlib.sha256(after).hexdigest(),
                             "%s moved in a pass whose landing is pure law-data" % path)

    def test_the_WORLD_BOOTS_IDENTICALLY_either_side_of_the_amend(self):
        """The withdrawal removes a NUMBER from a declaration and nothing else, so the
        booted world's shape must be unmoved: same record count, same active rules, same
        root rules. A shape that moved would mean the amend reached past its own field.

        [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14, charter §A57, W3a's own worklist member 6.
        CAUSE: this pass added an operation, so a world booted from the LIVE tree holds one more
        record and one more active rule (an op definition IS an active rule). ASSERTED:
        `_World()`. SUPERSEDED: `_World(pack=pack_at(W3A_AFTER_ERA_COMMIT))`. REMAINS TRUE:
        W3a's booted world was identical either side of its amend. GIVEN UP: nothing — this
        pass's own row states its world delta and NAMES the added rule rather than counting it.]
        """
        era = _World(pack=pack_at(W3A_BEFORE_COMMIT))
        now = _World(pack=pack_at(W3A_AFTER_ERA_COMMIT))
        self.assertEqual(len(list(era.store.all())), len(list(now.store.all())))
        self.assertEqual(len(era.views.active_rules()), len(now.views.active_rules()))
        self.assertEqual(len(era.views.root_rules()), len(now.views.root_rules()))

class TheW3aSweep(unittest.TestCase):
    """§A57 BY FALSIFICATION, with the method IMPORTED from `tests/era_pin.py`.

    THE POPULATION IS BY FALSIFICATION AND NOT BY ADJACENCY (the clause's own 2026-08-09
    repair), and it is TAKEN FROM A FULL SUITE ARM rather than from a worklist. The arm ran
    before any flip: `Ran 2613 tests`, `FAILED (failures=11, errors=26)` — THIRTY-SEVEN
    reds, split below into THIRTY-TWO falsification flips and FIVE attestation reds.

    EVERY FALSIFICATION RED IS IN THIS FILE, which is the shape of a family that keeps its
    whole battery in one place: no other file asserts anything about the device intake law.
    So no §A57 fence-relation recording in the `:400` form is owed by this pass, and that is
    a MEASURED statement rather than an assumption — the file column below is asserted.

    TWO TREATMENTS, AND CHOOSING BETWEEN THEM IS THE ONLY JUDGMENT IN THIS SWEEP:
      * ERA-PIN a row that asserts WHAT A PAST PASS LANDED. Both sides of a historical
        assertion belong to that history's era and the live tree is not one of them.
      * SCOPE a row that asserts A LIVE PROPERTY OF THE CURRENT LAW. Era-pinning one of
        those would make the suite green BY RETIRING A STANDING GUARD, and a retired guard
        reads on the page exactly like a repaired one. Exactly one row took this treatment
        — `TheIntakeLawLanded.test_no_declaration_sets_a_bound_of_ONE`, the never-clause's
        operational half — and it is the row where getting it wrong would have cost most.
    """

    SWEPT = (
        ("tests/test_ep29.py", "TheFoundingMovedAtW2b.test_the_designation_record_carries_the_NEW_version",
         "FAIL", "1.22.0 -> 1.23.0"),
        ("tests/test_ep29.py", "TheFoundingMovedAtW2b.test_the_pack_version_moved_one_MINOR_from_W2bs_own_BEFORE",
         "FAIL", "1.22.0 -> 1.23.0"),
        ("tests/test_ep29.py", "TheFoundingStandsBYTEUNCHANGEDAfterW2c.test_the_pack_is_BYTE_IDENTICAL_to_this_passs_own_pre_write_commit",
         "FAIL", "the pack moved off W2c's close state"),
        ("tests/test_ep29.py", "TheGranularityValuesAreDERIVEDAndNotASSERTED.test_the_COUNT_and_RATE_columns_give_DIFFERENT_answers_so_the_choice_MATTERS",
         "FAIL", "net's threshold withdrawn"),
        ("tests/test_ep29.py", "TheGranularityValuesAreDERIVEDAndNotASSERTED.test_the_NET_cap_is_RECOMPUTED_from_W2as_own_cells",
         "FAIL", "net's threshold withdrawn"),
        ("tests/test_ep29.py", "TheIntakeLawLanded.test_no_declaration_sets_a_bound_of_ONE",
         "ERROR", "net's threshold withdrawn: None is not comparable to 1"),
        ("tests/test_ep29.py", "TheRecordsPerInterruptRowIsSECONDARYConformance.test_the_row_covers_THREE_levels_when_three_were_driven",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheRecordsPerInterruptRowIsSECONDARYConformance.test_this_row_does_NOT_claim_the_scaling_red_that_belongs_to_W5",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheShadowRecordsAreAtTheDECLAREDGrade.test_a_NET_record_states_NO_admitted_act_count_and_carries_the_laws_own_reason",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheShadowRecordsAreAtTheDECLAREDGrade.test_every_declared_class_is_the_one_the_law_declares",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheShadowRecordsAreAtTheDECLAREDGrade.test_the_arithmetic_produces_MORE_THAN_ONE_record_when_the_cap_is_exceeded",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2bRowsCanBeMadeToFail.test_the_control_PASSES_every_covered_row",
         "FAIL", "consequence: three rows it covers reddened"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_AN_OUT_OF_TREE_MODULE_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_AN_XDP_PROGRAM_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_A_BOUND_OF_ONE_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_A_BPF_PROGRAM_ON_THE_NETDEV_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_A_BUILDER_THAT_COULD_SEE_THE_LOADS_REPORT_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_A_CGROUP_BPF_PROGRAM_OVER_THE_LOADS_SLICE_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_A_DRIVER_EDITED_AFTER_SETTLING_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_A_DRIVER_THAT_MOVED_ACROSS_THE_ERA_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_A_KPROBE_ON_THE_BLOCK_PATH_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_A_NETFILTER_RULESET_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_A_RECORD_COUNT_THAT_IS_NOT_THE_LAWS_ARITHMETIC_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_A_RECORD_WHOSE_GRADE_SAYS_PER_INTERRUPT_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_A_STACKED_BLOCK_TARGET_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_A_TC_FILTER_WITH_A_DROP_ACTION_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_A_TRACER_OTHER_THAN_NOP_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_ONE_RECORD_PER_ARRIVAL_WITH_THE_LABEL_UNTOUCHED_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_RECORDS_OUTNUMBERING_INTERRUPTS_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_THE_CENSUS_MOVING_ACROSS_THE_OBSERVATION_REDS",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_the_reading_emits_EACH_code_from_ITS_OWN_mutation_alone",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
        ("tests/test_ep29.py", "TheW2cRowsCanBeMadeToFail.test_the_synthetic_control_PASSES_every_row",
         "ERROR", "the shadow builder divides by net's withdrawn threshold"),
    )
    #: THE FIVE ATTESTATION REDS from the same arm, named so the two kinds are not
    #: conflated by a later reader counting thirty-seven and looking for thirty-seven flips.
    #: NO EDIT TO ANY ROW FIXES THESE — they say "the founding on disk is unattested", and
    #: what discharges them is THIS PASS'S BUILD-PROGRESS ENTRY naming 1.23.0 and the pack's
    #: own sha256 together. Same split W2b's sweep found, same two doors.
    ATTESTATION_REDS = (
        "tests/test_ep28i.py::TestTheVersionMoves."
        "test_the_J9_instrument_is_live_and_binds_whatever_pack_ships",
        "tests/test_ep28k.py::TestTheVersionMoves."
        "test_J9_the_same_version_may_not_name_two_distinct_foundings",
        "tests/test_ep28n.py::TestTheVersionMoves."
        "test_J9_the_same_version_may_not_name_two_distinct_foundings",
        "tests/test_ep28n2.py::TestTheVersionMoves."
        "test_J9_the_same_version_may_not_name_two_distinct_foundings",
        "tests/test_founding_is_logged.py::TestTheFoundingOnDiskIsNamedInTheLog."
        "test_the_founding_version_and_pack_hash_are_named_together_in_one_entry",
    )

    #: THE TWO SITES THAT SPELL THE FLIPPED READ AND DID NOT REDDEN, named rather than
    #: swept in. §A57's permission is bounded by FALSIFICATION, so a site that passed is
    #: out of population however much it looks like the six that did not — and BOTH ARE
    #: RAISED in this pass's entry, because each survived for a reason a later change
    #: removes. `live_shadow_set` is referenced by nothing in this file; the row replaces
    #: every window's device class before the declarations are consulted.
    NOT_SWEPT_BECAUSE_NOT_FALSIFIED = (
        ("tests/test_ep29.py", "live_shadow_set",
         "referenced nowhere in this file, so no row reads through it"),
        ("tests/test_ep29.py", "TheShadowRecordsAreAtTheDECLAREDGrade."
                               "test_a_class_the_law_declares_NOTHING_for_REFUSES_and_the_"
                               "refusal_is_the_record",
         "replaces every window's device_class, so no declaration is consulted"),
    )

    def test_the_two_kinds_of_red_are_COUNTED_SEPARATELY(self):
        """A suite tail shows one number. These route to different doors: a flip is an edit
        to a row, an attestation red is discharged by writing the entry. THIRTY-TWO AND
        FIVE, reconciling to the thirty-seven the sweep arm reported."""
        self.assertEqual(len(self.SWEPT), 32)
        self.assertEqual(len(self.ATTESTATION_REDS), 5)
        self.assertEqual(len(self.SWEPT) + len(self.ATTESTATION_REDS), 37)
        self.assertEqual({p for p, _r, _k, _w in self.SWEPT}, {"tests/test_ep29.py"},
                         "the flip population left this pass's own file, and §A57's fence "
                         "relation would then need recording in the :400 form")

    def test_the_swept_population_splits_by_KIND_and_the_split_is_a_number(self):
        """ELEVEN FAILURES AND TWENTY-SIX ERRORS in the arm; of those, one failure and five
        errors were outside this file. Recorded as arithmetic because 'mostly errors' is the
        kind of sentence that hides a miscount."""
        kinds = [k for _p, _r, k, _w in self.SWEPT]
        self.assertEqual((kinds.count("FAIL"), kinds.count("ERROR")), (6, 26))

    def test_every_swept_row_STILL_EXISTS_and_resolves(self):
        """A worklist naming rows that do not exist is worse than no worklist, and this one
        is a record of what was repaired."""
        for path, dotted, _kind, _why in self.SWEPT:
            self.assertTrue(os.path.exists(os.path.join(REPO, path)), path)
            cls_name, meth = dotted.split(".")
            cls = globals().get(cls_name)
            self.assertIsNotNone(cls, "no such class: %s" % cls_name)
            self.assertTrue(hasattr(cls, meth), "no such row: %s" % dotted)

    def test_the_ATTESTATION_reds_name_real_files(self):
        for dotted in self.ATTESTATION_REDS:
            self.assertTrue(os.path.exists(os.path.join(REPO, dotted.split("::")[0])), dotted)

    def test_the_UNSWEPT_sites_still_exist_and_are_named_for_what_they_are(self):
        for _path, name, _why in self.NOT_SWEPT_BECAUSE_NOT_FALSIFIED:
            head = name.split(".")[0]
            self.assertIsNotNone(globals().get(head), "no such name: %s" % head)

    #: THE NEXT MOVE'S WORKLIST — the rows that compare a LIVE-tree read against a literal
    #: THIS pass's era makes true, so the next founding pass falsifies exactly these and owes
    #: them the §A57 era-pin. A FLOOR AND NEVER THE BOUND, and this pass has the strongest
    #: evidence yet for saying so: W1b's worklist under-named by eight, W2b's over-named by
    #: four, and MY OWN sweep population was 32 where a worklist would have named 6. THE
    #: BOUND IS A SUITE RUN AND NOTHING ELSE IS.
    NEXT_MOVE_FALSIFIES = (
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a.test_the_pack_version_moved_one_MINOR_from_W3as_own_BEFORE"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a.test_the_designation_record_carries_the_NEW_version"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a.test_the_DECLARED_LAW_CENSUS_did_not_move_in_either_direction"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a.test_the_RECORD_and_STEP_counts_did_not_move"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a.test_the_ENGINE_moved_ZERO_lines"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a.test_the_WORLD_BOOTS_IDENTICALLY_either_side_of_the_amend"),
        ("tests/test_ep29.py",
         "TheNetThresholdIsWithdrawnLawfully.test_BLOCKS_WHOLE_DECLARATION_is_BYTE_UNMOVED"),
        ("tests/test_ep29.py",
         "TheNetThresholdIsWithdrawnLawfully.test_the_LAW_TEXT_itself_is_BYTE_UNMOVED"),
        ("tests/test_ep29.py",
         "TheNetThresholdIsWithdrawnLawfully.test_the_OTHER_UNESTABLISHED_VALUE_is_unmoved"),
    )

    def test_every_row_on_the_next_moves_worklist_EXISTS(self):
        self.assertTrue(self.NEXT_MOVE_FALSIFIES)
        for path, dotted in self.NEXT_MOVE_FALSIFIES:
            self.assertTrue(os.path.exists(os.path.join(REPO, path)), path)
            cls_name, meth = dotted.split(".")
            cls = globals().get(cls_name)
            self.assertIsNotNone(cls, "no such class: %s" % cls_name)
            self.assertTrue(hasattr(cls, meth), "no such row: %s" % dotted)

    def test_the_ERA_PIN_METHOD_IS_IMPORTED_AND_NOT_RE_DERIVED(self):
        """C2's own red world: a re-derived era idiom REDS, and the class it reds is the
        eighteen copies EP-28Z retired out of ten files. A PRESENCE test — this file's era
        read and the home's are shown to produce the same bytes — because the absence form
        inverted on an earlier pass, matching an ordinary English word in a docstring."""
        self.assertEqual(pack_at(W3A_BEFORE_COMMIT), era_pin.pack_at(W3A_BEFORE_COMMIT))
        self.assertEqual(os.path.dirname(os.path.abspath(era_pin.__file__)),
                         os.path.join(REPO, "tests"),
                         "era_pin resolved to something other than the estate's one home")

    def test_the_era_pin_is_verified_BY_CONTENT_and_never_by_version_number(self):
        """`era_pin`'s own stated cap: it makes the READ uniform and says nothing about
        whether a caller's PIN is the right commit. Choosing a pin by version number is this
        estate's most expensive known trap, so the pin is checked against the sha256 W2b's
        close recorded for the pack this pass moved off."""
        blob = era_pin.blob_at(W3A_BEFORE_COMMIT, era_pin.PACK_PATH)
        self.assertEqual(hashlib.sha256(blob).hexdigest(), W3A_BEFORE_PACK_SHA)

    def test_the_era_pin_reports_a_DIFFERENCE_when_there_is_one(self):
        """The instrument's own negative-result test; every era row in this pass rests on
        it, and after this pass the difference it must report is the one this pass made."""
        with open(PACK_PATH, "rb") as fh:
            live = fh.read()
        self.assertNotEqual(
            hashlib.sha256(era_pin.blob_at(W3A_BEFORE_COMMIT,
                                           era_pin.PACK_PATH)).hexdigest(),
            hashlib.sha256(live).hexdigest())

    def test_W2cs_LAW_READ_now_resolves_to_the_ERA_and_not_to_the_live_tree(self):
        """The flip's own row: `w2c_law` must return the law W2c ran under, and it must
        DIFFER from the live law in exactly the field this pass moved — otherwise the flip
        is a rename that changed nothing and the twenty-six rows it repaired were repaired
        by something else."""
        era, live = w2c_law(), intake_by_class(live_pack())
        self.assertEqual(sorted(era), sorted(live))
        self.assertEqual(era["block"], live["block"])
        self.assertEqual(era["net"]["max_arrivals"]["value"], 3518)
        self.assertIsNone(live["net"]["max_arrivals"]["value"])

    def test_w2c_law_HANDS_OUT_A_COPY_and_not_its_own_memo(self):
        """The memo is shared by every W2c row and the red worlds mutate what they are
        handed. A memo handed out by reference would let one planted world poison every row
        that ran after it, and the failure would look like an unrelated row breaking."""
        first = w2c_law()
        first["net"]["max_arrivals"]["value"] = "POISONED"
        self.assertEqual(w2c_law()["net"]["max_arrivals"]["value"], 3518)


class TheW3aRowsCanBeMadeToFail(unittest.TestCase):
    """RED WORLDS FOR THE NET AMEND, DRIVEN THROUGH THE REAL ROWS on planted packs.

    Each plants a defect in a COPY of the live pack and runs the ACTUAL row against it, so
    no predicate is restated — a red world that re-implements the assertion it tests proves
    only that two copies agree. CONTROL FIRST: the unmutated copy must PASS every covered
    row, or a red below could be the copy being malformed rather than the clause biting.

    THE THREE PLANTS THE PLAN NAMES BY NAME COME FIRST: `3518 surviving as an enforceable
    ceiling REDS`, `a margin invented from four points on one guest REDS`, and `block's cap
    moving REDS`. The margin is COMPUTED the way a careless pass would compute it rather
    than typed, so the red world is the temptation itself and not a number chosen to fail."""

    #: Every W3a row that reads the pack through `live_pack`. Named as DATA so the control
    #: cannot pass by quietly running fewer rows than exist.
    COVERED = (
        (TheNetThresholdIsWithdrawnLawfully,
         ("test_the_NET_threshold_carries_NO_VALUE_AND_NO_CELL",
          "test_the_NET_threshold_is_DECLARED_unestablished_and_never_OMITTED",
          "test_the_withdrawal_is_RECOMPUTED_from_the_THREE_RUN_table",
          "test_the_BLOCK_cap_is_CONFIRMED_over_the_THREE_RUN_population",
          "test_the_GRADE_stands_UNTOUCHED_at_window_for_both_classes",
          "test_the_LAW_TEXT_itself_is_BYTE_UNMOVED",
          "test_BLOCKS_WHOLE_DECLARATION_is_BYTE_UNMOVED",
          "test_the_OTHER_UNESTABLISHED_VALUE_is_unmoved",
          "test_the_PRECEDENT_FORM_is_the_one_taken",
          "test_the_declaration_SAYS_it_bounds_no_window_while_the_threshold_is_unestablished",
          "test_the_CLOSER_that_cannot_fire_SAYS_SO",
          "test_every_LIMIT_still_carries_its_POPULATION_and_BASIS",
          "test_the_LIMIT_COUNT_did_not_shrink")),
    )

    #: THE SAME QUESTION FOR THE ROWS THIS FILE ERA-PINNED, SPLIT OUT RATHER THAN DROPPED.
    #: [ADDED — EP-29 W3a3, 2026-08-14, and it is a consequence of that pass's §A57 flips that
    #: is worth meeting head-on. Era-pinning a row moves its subject from the LIVE tree to a
    #: commit, and a red world that plants into a copy of the live pack then reaches NOTHING:
    #: the three rows below went on passing while their planted defects sailed past them. A
    #: can-fail row that can no longer make its subject fail is §7.1's first disguise, and it
    #: had been introduced by the repair rather than by the pass being repaired. The coverage is
    #: kept and re-aimed: these rows are planted at the ERA READ, where they now look.]
    COVERED_ERA = (
        (TheFoundingMovedAtW3a,
         ("test_the_pack_version_moved_one_MINOR_from_W3as_own_BEFORE",
          "test_the_DECLARED_LAW_CENSUS_did_not_move_in_either_direction",
          "test_the_RECORD_and_STEP_counts_did_not_move")),
    )

    def _copy(self):
        return copy.deepcopy(live_pack())

    def _era_copy(self):
        """The plant base for the era-pinned rows: a copy of the world those rows are ABOUT."""
        return copy.deepcopy(pack_at(W3A_AFTER_ERA_COMMIT))

    def _run_era(self, pack, cls, meth):
        """Run one REAL era-pinned row against `pack` by pointing this file's `pack_at` at it
        FOR THE AFTER-ERA COMMIT ONLY, so the row's BEFORE side still reads the genuine era and
        the plant lands on exactly one of its two readings. The row's own body is what
        executes, unchanged — no predicate is restated here."""
        global pack_at
        original = pack_at
        pack_at = lambda c: pack if c == W3A_AFTER_ERA_COMMIT else original(c)  # noqa: E731
        try:
            case = cls(meth)
            res = unittest.TestResult()
            case.run(res)
            return res
        finally:
            pack_at = original

    def _run(self, pack, cls, meth):
        """Run one REAL row against `pack` by pointing this file's `live_pack` at it for the
        call. The row's own body is what executes."""
        global live_pack
        original = live_pack
        live_pack = lambda: pack                              # noqa: E731
        try:
            case = cls(meth)
            res = unittest.TestResult()
            case.run(res)
            return res
        finally:
            live_pack = original

    def assertRowFAILED(self, res, why):
        """A RED WORLD MUST RED FOR ITS OWN REASON. `wasSuccessful()` is False for an ERROR
        too, so a planted pack that broke the row would satisfy a bare assertFalse and read
        on the page exactly like the claim biting. Local to this class, taken from the five
        above it rather than re-derived — the file's own practice, and a sixth copy is
        raised in this pass's entry rather than quietly changed."""
        self.assertEqual(res.errors, [],
                         "the row ERRORED rather than failed, so the planted pack broke the "
                         "instrument instead of the claim: %r" % (res.errors,))
        self.assertEqual(len(res.failures), 1, why)

    def _intakes(self, pack):
        return [r["payload"] for st in pack["steps"] for r in st["records"]
                if r.get("action") == "DECLARE-INTAKE"]

    def _net(self, pack):
        return [d for d in self._intakes(pack) if d["device_class"] == "net"][0]

    def _block(self, pack):
        return [d for d in self._intakes(pack) if d["device_class"] == "block"][0]

    def test_the_control_PASSES_every_covered_row(self):
        """CONTROL, FIRST. Without it every red below is uninterpretable.

        [EXTENDED — EP-29 W3a3, 2026-08-14: the control now runs BOTH populations, each through
        the reader its own rows use. Running the era-pinned rows through the live-pack harness
        was the shape that hid the broken red worlds: they passed, because the harness never
        reached them, and a control that cannot fail for a row is not a control for that row.]"""
        pack, era = self._copy(), self._era_copy()
        ran = 0
        for cls, meths in self.COVERED:
            for meth in meths:
                res = self._run(pack, cls, meth)
                self.assertTrue(res.wasSuccessful(),
                                "the unmutated copy FAILS %s.%s, so every red world below is "
                                "uninterpretable: %r"
                                % (cls.__name__, meth, res.failures + res.errors))
                ran += 1
        for cls, meths in self.COVERED_ERA:
            for meth in meths:
                res = self._run_era(era, cls, meth)
                self.assertTrue(res.wasSuccessful(),
                                "the unmutated ERA copy FAILS %s.%s, so every era red world "
                                "below is uninterpretable: %r"
                                % (cls.__name__, meth, res.failures + res.errors))
                ran += 1
        self.assertEqual(ran, sum(len(m) for _c, m in self.COVERED + self.COVERED_ERA))
        self.assertGreater(ran, 12, "non-vacuity: the control is not a stub")

    def test_the_ERA_HARNESS_ITSELF_can_reach_the_rows_it_claims_to_plant_into(self):
        """THE CONTROL'S OWN CONTROL, and the row that would have caught this pass's harness
        defect at the moment it was introduced. `_run_era` is shown to CHANGE an era-pinned
        row's verdict — the same row passes on the true era and fails on a planted one — so a
        green control above means the harness reached the row rather than missed it.

        A red world's plumbing needs its own negative-result test exactly as much as a claim
        does: the three reds below all read as healthy while planting into a pack nobody
        looked at."""
        cls, meth = TheFoundingMovedAtW3a, "test_the_pack_version_moved_one_MINOR_from_W3as_own_BEFORE"
        self.assertTrue(self._run_era(self._era_copy(), cls, meth).wasSuccessful(),
                        "the true era fails its own row, so a failure below says nothing")
        planted = self._era_copy()
        planted["founding_version"] = "9.99.9"
        self.assertRowFAILED(self._run_era(planted, cls, meth),
                             "the era harness cannot move an era-pinned row's verdict, so every "
                             "era red world below plants into a pack the row never reads")

    # ------------------------------------------------- the three the plan names by name
    def test_THE_OBSERVED_CEILING_3518_RESTORED_AS_AN_ENFORCEABLE_VALUE_REDS(self):
        """`3518 surviving as an enforceable ceiling REDS`. The plant is the exact number
        v1.22.0 carried — the highest arrival count ever observed on this class, a ceiling
        with zero headroom — restored into the one field a consumer would read."""
        pack = self._copy()
        self._net(pack)["max_arrivals"]["value"] = 3518
        self.assertRowFAILED(
            self._run(pack, TheNetThresholdIsWithdrawnLawfully,
                      "test_the_withdrawal_is_RECOMPUTED_from_the_THREE_RUN_table"),
            "the withdrawn ceiling passes as an enforceable value")

    def test_A_MARGIN_INVENTED_FROM_THE_MEASURED_SPREAD_REDS(self):
        """`a margin invented from four points on one guest REDS — asserted-not-derived, the
        class this file refuses`. THE PLANT IS COMPUTED THE WAY THE CARELESS PASS WOULD
        COMPUTE IT — the ceiling widened by the very spread that refuted it — so this red
        world is the temptation rather than a number picked to fail."""
        pack = self._copy()
        margin = careless_margin(runs_of_class(W2_THREE_RUN_CELLS, "net"))
        self.assertEqual(margin, 4900, "the margin arithmetic moved, so the plant below is "
                                       "no longer the number a careless pass would write")
        self.assertGreater(margin, 3518, "a margin that does not widen is not a margin")
        self._net(pack)["max_arrivals"]["value"] = margin
        self.assertRowFAILED(
            self._run(pack, TheNetThresholdIsWithdrawnLawfully,
                      "test_the_withdrawal_is_RECOMPUTED_from_the_THREE_RUN_table"),
            "a threshold widened by a safety margin passes")

    def test_BLOCKS_CAP_MOVING_REDS(self):
        """`block's cap CONFIRMED at :712 and untouched` — its red world. One arrival either
        way, because a confirmation that tolerates a moved number confirms nothing."""
        for delta in (+1, -1):
            pack = self._copy()
            self._block(pack)["max_arrivals"]["value"] = 6144 + delta
            self.assertRowFAILED(
                self._run(pack, TheNetThresholdIsWithdrawnLawfully,
                          "test_the_BLOCK_cap_is_CONFIRMED_over_the_THREE_RUN_population"),
                "block's cap moved by %+d and passed" % delta)

    # ------------------------------------------------------- the form of the withdrawal
    def test_A_WITHDRAWN_VALUE_WITH_NO_REASON_REDS(self):
        """The precedent's own discipline: the absence is DECLARED with its reason in a
        required field, so a `null` that says nothing is a gap wearing a decision's shape."""
        pack = self._copy()
        self._net(pack)["max_arrivals"]["basis"] = "no cap is declared for this class"
        self.assertRowFAILED(
            self._run(pack, TheNetThresholdIsWithdrawnLawfully,
                      "test_the_NET_threshold_is_DECLARED_unestablished_and_never_OMITTED"),
            "a withdrawn value carrying no NOT ESTABLISHED reason passes")

    def test_A_THRESHOLD_OMITTED_RATHER_THAN_DECLARED_UNESTABLISHED_REDS(self):
        """DECLARE-INTAKE's own text — an unestablished value is declared unestablished,
        NEVER OMITTED. Deleting the field is how a withdrawal becomes invisible."""
        pack = self._copy()
        self._net(pack).pop("max_arrivals")
        self.assertRowFAILED(
            self._run(pack, TheNetThresholdIsWithdrawnLawfully,
                      "test_the_NET_threshold_is_DECLARED_unestablished_and_never_OMITTED"),
            "a threshold deleted rather than declared unestablished passes")

    def test_A_WITHDRAWN_VALUE_DROPPED_OFF_derived_values_REDS(self):
        """The population-shrinking escape, aimed at the withdrawal: a declaration that took
        its withdrawn value off the audited list would be audited over a set it chose."""
        pack = self._copy()
        net = self._net(pack)
        net["derived_values"] = [n for n in net["derived_values"] if n != "max_arrivals"]
        self.assertRowFAILED(
            self._run(pack, TheNetThresholdIsWithdrawnLawfully,
                      "test_the_NET_threshold_is_DECLARED_unestablished_and_never_OMITTED"),
            "a withdrawn value off the audited list passes")

    def test_A_STILL_CITED_CALIBRATION_CELL_REDS(self):
        """A withdrawn value that still names the cell it could not be derived from reads as
        derived from it, which is the whole defect the withdrawal exists to remove."""
        pack = self._copy()
        self._net(pack)["max_arrivals"]["cell"] = \
            "EP-29 W2a calibration table, virtio0 L2"
        self.assertRowFAILED(
            self._run(pack, TheNetThresholdIsWithdrawnLawfully,
                      "test_the_NET_threshold_carries_NO_VALUE_AND_NO_CELL"),
            "a withdrawn value still citing a calibration cell passes")

    # ------------------------------------------------------ what must not have moved
    def test_THE_GRADE_MOVING_TO_PER_INTERRUPT_REDS(self):
        """`the GRADE stands untouched` — planted where the grade actually lives rather than
        hunted for in prose, which is W2b's own reason and it holds unchanged here."""
        pack = self._copy()
        for d in self._intakes(pack):
            d["grade"] = "per-interrupt"
        self.assertRowFAILED(
            self._run(pack, TheNetThresholdIsWithdrawnLawfully,
                      "test_the_GRADE_stands_UNTOUCHED_at_window_for_both_classes"),
            "a grade moved to per-interrupt passes an amend that may not touch it")

    def test_THE_LAW_TEXT_MOVING_REDS(self):
        """The amend is to a DECLARATION. A pass that edited DEV-LAW-INTAKE while withdrawing
        a value would be changing the grade's own law under cover of a data repair."""
        pack = self._copy()
        for st in pack["steps"]:
            for r in st["records"]:
                if (r.get("payload") or {}).get("rule_id") == "DEV-LAW-INTAKE":
                    r["payload"]["text"] = r["payload"]["text"] + " AND ONE MORE SENTENCE."
        self.assertRowFAILED(
            self._run(pack, TheNetThresholdIsWithdrawnLawfully,
                      "test_the_LAW_TEXT_itself_is_BYTE_UNMOVED"),
            "an edited law text passes a pass that amends only a declaration")

    def test_THE_PRECEDENTS_OWN_VALUE_BEING_EDITED_REDS(self):
        """`net unit` is the precedent this amend follows, not a thing it may tidy while it
        is in the same record."""
        pack = self._copy()
        self._net(pack)["arrivals_per_admitted_act"]["why_this_value"] = "re-worded"
        self.assertRowFAILED(
            self._run(pack, TheNetThresholdIsWithdrawnLawfully,
                      "test_the_OTHER_UNESTABLISHED_VALUE_is_unmoved"),
            "an edited precedent passes")

    def test_A_DECLARATION_SILENT_ABOUT_THE_ABSENCE_IT_NOW_CARRIES_REDS(self):
        """A declaration naming no absence reads as covering everything it did not mention,
        and the absence this withdrawal creates is that the declaration bounds NO window."""
        pack = self._copy()
        net = self._net(pack)
        net["does_not_declare"] = net["does_not_declare"][:-1]
        self.assertRowFAILED(
            self._run(pack, TheNetThresholdIsWithdrawnLawfully,
                      "test_the_declaration_SAYS_it_bounds_no_window_while_the_threshold_is_"
                      "unestablished"),
            "a declaration silent about the absence it now carries passes")

    def test_A_CLOSER_LEFT_DESCRIBING_A_CAP_THAT_DOES_NOT_EXIST_REDS(self):
        """The era's own closer text, restored. It was true under v1.22.0 and it is law text
        misdescribing its own declaration under v1.23.0."""
        pack = self._copy()
        era_net = [d for d in intake_declarations(pack_at(W3A_BEFORE_COMMIT))
                   if d["device_class"] == "net"][0]
        self._net(pack)["closers"][0] = era_net["closers"][0]
        self.assertRowFAILED(
            self._run(pack, TheNetThresholdIsWithdrawnLawfully,
                      "test_the_CLOSER_that_cannot_fire_SAYS_SO"),
            "a closer keyed on a withdrawn threshold and silent about it passes")

    def test_A_LIMIT_DROPPED_RATHER_THAN_AMENDED_REDS(self):
        """A withdrawal that removed the limits whose subject it removed would delete the
        record of what was known, which is the opposite of declaring an absence."""
        pack = self._copy()
        self._net(pack)["limits"].pop()
        self.assertRowFAILED(
            self._run(pack, TheNetThresholdIsWithdrawnLawfully,
                      "test_the_LIMIT_COUNT_did_not_shrink"),
            "a dropped limit passes")

    def test_A_REWRITTEN_LIMIT_THAT_LOST_ITS_POPULATION_REDS(self):
        """§A51's refusal form, aimed at the one moment it is most likely to fail: the limits
        this amend rewrote."""
        pack = self._copy()
        self._net(pack)["limits"][0]["population"] = ""
        self.assertRowFAILED(
            self._run(pack, TheNetThresholdIsWithdrawnLawfully,
                      "test_every_LIMIT_still_carries_its_POPULATION_and_BASIS"),
            "a rewritten limit naming no population passes")

    # ------------------------------------------------------------ the founding's own reds
    def test_A_BYTE_UNCHANGED_FOUNDING_REDS(self):
        """MOVEMENT IS THIS MOVEMENT'S REQUIRED OUTCOME and the inverse of the unit before
        it, so the failing world is planted from the ERA'S OWN BYTES — exactly what the tree
        would hold had this pass landed nothing."""
        era = pack_at(W3A_BEFORE_COMMIT)
        self.assertRowFAILED(
            self._run_era(era, TheFoundingMovedAtW3a,
                          "test_the_pack_version_moved_one_MINOR_from_W3as_own_BEFORE"),
            "the era's own pack passes a row that requires the founding to have moved")

    def test_A_LAW_DECLARED_BESIDE_THE_WITHDRAWAL_REDS(self):
        """The census's whole point: a law amend that added something while withdrawing a
        value would be doing two things and reporting one."""
        pack = self._era_copy()
        pack["steps"][-1]["records"].append(
            {"actor": "PC_RUNTIME", "action": "CREATE-RULE", "object": "rule:PLANTED",
             "rule_cited": "P3-CLOSURE",
             "payload": {"rule_id": "PLANTED-LAW", "text": "planted"}})
        self.assertRowFAILED(
            self._run_era(pack, TheFoundingMovedAtW3a,
                          "test_the_DECLARED_LAW_CENSUS_did_not_move_in_either_direction"),
            "a law declared beside the withdrawal passes the census")

    def test_A_SECOND_DECLARATION_CREATED_BESIDE_THE_AMENDED_ONE_REDS(self):
        """W1a's AMEND ruling, at this layer: a create beside the shipped name would mint two
        names for one act class and leave the withdrawn value standing under the name the
        world can already call."""
        pack = self._era_copy()
        step = [s for s in pack["steps"] if s["step"] == "08l-device-intake-declarations"][0]
        step["records"].append(copy.deepcopy(step["records"][1]))
        self.assertRowFAILED(
            self._run_era(pack, TheFoundingMovedAtW3a,
                          "test_the_RECORD_and_STEP_counts_did_not_move"),
            "a second net declaration created beside the amended one passes")


# =======================================================================================
# EP-29 W3b — THE C0 WALK'S PINNED FACTS (2026-08-14)
#
# W3b STOPPED AND REPORTED under ADDENDUM 5 §4's third state: the walk found that the INTAKE
# crossing C3 requires and the unestablished-threshold refusal C7 requires have no operation
# able to carry them, and landing one is a LAW PASS that W3b is not (ADDENDUM 8 C2 holds the
# founding BYTE-UNCHANGED at this movement, and §3's fence gives W3b no founding member).
#
# THESE ROWS ARE THE SCOPE-NEUTRAL HALF OF THAT WALK, on the EP-27B W6 precedent: a stop
# lands the probes that stay true whichever way the ruling goes, and lands nothing that
# encodes the state the ruling will change.
#
# WHY NO ROW HERE ASSERTS THE FINDING ITSELF — "no live operation can carry a covering
# record". That is a COUNT OF ZERO over a vocabulary that is about to grow, and this estate
# has already paid for an absence test that inverted as its absence was documented. Every row
# below is PRESENCE-shaped: it names a subject and pins that subject's own shape, so it reds
# when THAT subject moves, which is exactly the moment a reader should be stopped. The
# finding is DERIVED from these three facts in the BUILD-PROGRESS entry, where a derivation
# can be re-checked, rather than frozen into an assertion that would quietly become a lie.
#
# WHAT IS DELIBERATELY NOT ADDED: a fifth assertion that the terminal-rule citation is
# P3-CLOSURE. This file already drives that at four sites (the first at
# TheFailClosedIntermediateState), so C7's undeclared-class half is ALREADY an in-suite
# driven fact and a fifth copy would be the eighteen-copy shape at one quarter the size.
# Named here so the absence reads as a decision.

#: What DEV-LAW-INTAKE'S OWN TEXT says a covering record CARRIES. Quoted from the law record
#: so the requirement belongs to the law and not to this file: a later pass that narrows the
#: requirement to fit an operation reds here instead of passing quietly.
COVERING_RECORD_CARRIERS = (
    "the COUNT of arrivals covered",
    "the BYTE TOTAL over them",
    "the device the arrivals were attributed to",
    "the window they were admitted under by name",
    "this law's citation together with the intake declaration's name",
)

#: DEVICE-IO-WINDOW-WRITE's payload, and DECLARE-INTAKE's parameters, as W3b's walk found
#: them at founding 1.23.0. Named as tuples so a change shows up as a set difference with
#: both directions printed, never as a bare count.
IO_WINDOW_WRITE_PAYLOAD = ("bytes", "device", "window")
DECLARE_INTAKE_PARAMS = (
    "arrivals_per_admitted_act", "closers", "derived_values", "device_class", "established",
    "grade", "intake", "limits", "max_arrivals", "records", "does_not_declare", "window",
)


def carriers_present(law_text):
    """THE ONE PREDICATE, called by the claim AND by its control — never two copies agreeing
    with each other. Returns which of the law's own carrier phrases the given text states."""
    return tuple(c for c in COVERING_RECORD_CARRIERS if c in law_text)


def op_record(pack, name):
    """The CREATE-OP record for `name` in `pack`, so a control can move ONE operation's shape
    and change nothing else."""
    for st in pack["steps"]:
        for r in st["records"]:
            if r.get("action") == "CREATE-OP" and r["payload"]["name"] == name:
                return r
    raise AssertionError("no CREATE-OP record for %r — the control cannot be built" % name)


class TheW3bWalksPinnedFacts(unittest.TestCase):
    """EP-29 W3b C0 — the three facts the stop rests on, each DRIVEN at a booted world and
    each with a control that proves the row can say no.

    POPULATION: one world booted from src/founding/founding-pack.json at the dispatch tree.
    BASIS: the live rule records, the live op definitions, and the records the gate actually
    appends — never the pack read as a file and never this file's belief about either."""

    def setUp(self):
        self.w = _World()

    # ------------------------------------------------------------------ non-vacuity, first
    def test_the_world_is_live_and_holds_the_device_group_before_any_shape_is_read(self):
        """ITEM-21 NON-VACUITY. Every row below reads a shape out of this world; over an empty
        world they would all pass while stating nothing, and they would read identically."""
        rules = self.w.views.active_rules()
        for law in ("DEV-LAW-BIND", "DEV-LAW-INTAKE"):
            self.assertIn(law, rules, "the device laws are not live, so nothing below states "
                                      "anything about this estate")
        defs = self.w.views.op_definitions()
        for op in ("REGISTER-CAPABILITY", "BIND-DEVICE", "DEVICE-IO-WINDOW-WRITE",
                   "DECLARE-INTAKE"):
            self.assertIn(op, defs, "%s is not live" % op)
        self.assertGreater(len(defs), 60, "the world booted with almost no vocabulary")

    # ------------------------------------------------- FACT 1 — the requirement is LAW TEXT
    def test_DEV_LAW_INTAKE_states_every_carrier_a_covering_record_must_hold(self):
        """WHAT A COVERING RECORD CARRIES IS THE LAW'S SENTENCE, NOT AN IMPLEMENTATION'S.

        Pinned because the cheapest way past W3b's stop is to narrow the requirement until an
        operation that already exists satisfies it. The requirement is read from the live rule
        record here, so that narrowing has to happen in the open."""
        law = dict(self.w.views.active_rules()["DEV-LAW-INTAKE"])["text"]
        self.assertEqual(carriers_present(law), COVERING_RECORD_CARRIERS,
                         "DEV-LAW-INTAKE no longer states every carrier it stated at W3b's "
                         "walk — missing: %r"
                         % (set(COVERING_RECORD_CARRIERS) - set(carriers_present(law)),))
        self.assertIn("NEVER RECORDED AT PER-INTERRUPT GRADE", law,
                      "the never-clause is the law's point and it is law text, not commentary")

    def test_the_carrier_predicate_REPORTS_A_MISSING_CARRIER(self):
        """THE CONTROL, THROUGH THE SAME PREDICATE. A test that only ever sees the true text
        cannot distinguish a predicate that reads from one that returns its own argument."""
        law = dict(self.w.views.active_rules()["DEV-LAW-INTAKE"])["text"]
        for dropped in COVERING_RECORD_CARRIERS:
            narrowed = law.replace(dropped, "")
            self.assertNotIn(dropped, carriers_present(narrowed),
                             "the predicate still reports %r after it was removed" % dropped)
            self.assertEqual(len(carriers_present(narrowed)),
                             len(COVERING_RECORD_CARRIERS) - 1,
                             "removing one carrier moved the count by something other than one")

    # ------------------------------- FACT 2 — what the I/O crossing's record actually holds
    def test_the_IO_crossing_records_its_payload_and_cites_DEV_LAW_BIND(self):
        """DRIVEN THROUGH THE GATE, AND THE RECORD IS READ RATHER THAN THE DEFINITION: the
        question is what this operation PUTS IN A RECORD, and a definition is a claim about
        that while the appended record is the answer."""
        self.w.call("REGISTER-CAPABILITY", driver="drv-a", device_class="block",
                    capabilities=["irq:11"])
        self.w.call("BIND-DEVICE", device="virtio1", driver="drv-a")
        from subsystems.devices import DevicesView
        self.assertEqual(DevicesView(self.w.store).bindings(), {"virtio1": "drv-a"},
                         "the bind is not live, so the write below would be over a dead world")

        rec = self.w.call("DEVICE-IO-WINDOW-WRITE", device="virtio1",
                          window="device-io@block", bytes=4096)
        self.assertEqual(rec["action"], "DEVICE-IO-WINDOW-WRITE")
        self.assertEqual(rec["rule_cited"], "DEV-LAW-BIND",
                         "the I/O crossing records under the ADMISSION law; DEV-LAW-INTAKE "
                         "governs the RECORD'S GRADE and is a different law")
        self.assertEqual(tuple(sorted(dict(rec["payload"]).keys())), IO_WINDOW_WRITE_PAYLOAD,
                         "DEVICE-IO-WINDOW-WRITE's recorded payload moved: %r"
                         % (sorted(dict(rec["payload"]).keys()),))

    def test_the_payload_comparison_SEES_A_MOVED_PAYLOAD(self):
        """THE CONTROL, DRIVEN AT A BUILT WORLD rather than argued: give the same operation one
        more recorded field and the row above must notice. A shape assertion that could not see
        its subject move is a sentence with a colon in it."""
        pack = copy.deepcopy(live_pack())
        d = op_record(pack, "DEVICE-IO-WINDOW-WRITE")["payload"]["definition"]
        d["params"] = dict(d["params"], arrival_count="optional")
        d["payload_from"] = list(d["payload_from"]) + ["arrival_count"]
        # the planted field is recorded inline (added to payload_from above), so it is a
        # structural count scalar, not reachable content — classify it to match (vocab door,
        # design/46 member 2). Same nature as DECLARE-INTAKE's own max_arrivals scalar.
        d["structural_params"] = list(d.get("structural_params") or []) + ["arrival_count"]
        w = _World(pack)
        w.call("REGISTER-CAPABILITY", driver="drv-a", device_class="block",
               capabilities=["irq:11"])
        w.call("BIND-DEVICE", device="virtio1", driver="drv-a")
        rec = w.call("DEVICE-IO-WINDOW-WRITE", device="virtio1", window="device-io@block",
                     bytes=4096, arrival_count=6144)
        moved = tuple(sorted(dict(rec["payload"]).keys()))
        self.assertNotEqual(moved, IO_WINDOW_WRITE_PAYLOAD,
                            "the planted field did not reach the record, so the row above "
                            "would not have seen it either and its green means nothing")
        self.assertIn("arrival_count", moved)

    # ------------------------------------- FACT 3 — DECLARE-INTAKE declares, and only that
    def test_DECLARE_INTAKE_carries_declaration_parameters_and_is_the_only_op_under_its_law(self):
        """THE DECLARING OPERATION IS NOT A RECORDING ONE. Pinned because `DECLARE-INTAKE`
        cites DEV-LAW-INTAKE, which makes it the operation a reader reaches for first when
        looking for the intake crossing — and its parameters are the twelve a DECLARATION
        takes, with no arrival count and no byte total among them."""
        defs = self.w.views.op_definitions()
        params = tuple(sorted(dict(defs["DECLARE-INTAKE"]["definition"]["params"]).keys()))
        self.assertEqual(params, tuple(sorted(DECLARE_INTAKE_PARAMS)),
                         "DECLARE-INTAKE's parameters moved: %r" % (list(params),))
        # [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14, charter §A57, AND IT IS THE ONE FLIP THIS
        # SECTION PREDICTED IN ITS OWN WORDS. The superseded assertion carried the instruction
        # "if this reds because an intake RECORDING operation landed, that is EP-29 W3b's stop
        # being answered and this row is the place to update" — it redded for exactly that
        # reason, and this is that update. CAUSE: DEVICE-INTAKE-COVER landed at W3a3. ASSERTED:
        # DECLARE-INTAKE is the ONLY op under this law. SUPERSEDED: the declarer and the recorder
        # are both under it, and the row now pins WHICH TWO. REMAINS TRUE, and it is the half
        # W3b's walk actually rested on: the DECLARING operation is not a recording one — its
        # twelve parameters are asserted above and carry no arrival count and no byte total.
        # GIVEN UP: nothing. The row is NOT era-pinned, deliberately: its subject is the live
        # registry, and a reader asking "what writes an intake record" must be answered about
        # today. A THIRD operation arriving under this law reds here, which is the question this
        # row exists to keep asking.]
        under = sorted(n for n, e in defs.items()
                       if dict(e["definition"]).get("law_cited") == "DEV-LAW-INTAKE")
        self.assertEqual(under, sorted(OPS_UNDER_THE_INTAKE_LAW),
                         "the operations citing DEV-LAW-INTAKE are now %r — the declarer and "
                         "the recorder are the two this law has, and a third is scope nobody "
                         "ruled on" % (under,))

    def test_the_law_citation_search_FINDS_A_PLANTED_SECOND_OP(self):
        """THE CONTROL FOR THE SEARCH ABOVE, and the one that matters most here: a search whose
        empty result carries a finding must be shown to find a known-present case. A builder in
        this estate shipped a consumer search whose positive control also returned empty, so
        its zero proved nothing — this is that lesson applied to my own search."""
        pack = copy.deepcopy(live_pack())
        planted = copy.deepcopy(op_record(pack, "DECLARE-INTAKE"))
        planted["object"] = "op:PLANTED-INTAKE-RECORDER"
        planted["payload"] = dict(planted["payload"], name="PLANTED-INTAKE-RECORDER",
                                  rule_id="op:PLANTED-INTAKE-RECORDER")
        op_record(pack, "DECLARE-INTAKE")  # the original stays; this is an addition
        [st for st in pack["steps"] if st["step"] == "08k-device-intake-ops"][0]["records"] \
            .append(planted)
        # [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14, charter §A57. CAUSE: the same landing. The
        # CONTROL still plants one operation; there are now two real ones beside it. ASSERTED:
        # the planted op plus DECLARE-INTAKE. SUPERSEDED: the planted op plus BOTH real ones.
        # REMAINS TRUE, and the control's whole point is untouched: the search finds a planted
        # member, so its answer above is a measurement and not a filter that cannot match.]
        defs = _World(pack).views.op_definitions()
        under = sorted(n for n, e in defs.items()
                       if dict(e["definition"]).get("law_cited") == "DEV-LAW-INTAKE")
        self.assertEqual(under, sorted(OPS_UNDER_THE_INTAKE_LAW + ("PLANTED-INTAKE-RECORDER",)),
                         "the search did not find a planted extra operation under the law, "
                         "so its answer above proves nothing")


# =======================================================================================
# EP-29 W3a2 — THE EXPRESSIBILITY ESTABLISHMENT (2026-08-14)
#
# W3a2 was dispatched to MINT DEV-LAW-INTAKE's operational half and to MOVE the founding
# (ADDENDUM 8 C8 and C2's second move). C8 puts a GATE in front of that landing and drives
# it FIRST: can the live check kinds express "the cited declaration's threshold field IS A
# VALUE"? Expressible -> parameterize and land. NOT expressible -> STOP-AND-REPORT, GREEN,
# and the architect shapes the §5 owner question, because a new check kind is engine
# vocabulary and never lands quietly.
#
# THE ESTABLISHMENT WAS DRIVEN AND IT SEPARATED NOTHING. Seventeen formulations spanning all
# twelve kinds, each minted into the live pack's own op-definition step and CALLED at a
# booted world against the two shipped declarations, which differ in exactly the field the
# question is about. None admitted block and refused net. So the founding did NOT move: the
# green third state (ADDENDUM 5 §4), not the failing outcome of a landing that ran.
#
# WHY THE CHECK IS LOAD-BEARING RATHER THAN DECORATIVE, so a later reader does not conclude
# the op could have landed without it. ADDENDUM 8 C7 makes the unestablished-threshold
# refusal the DEVICE LAYER'S FAIL-CLOSED DIRECTION, and net's own declaration says an
# arrival of its class "is ADMITTED BY NOTHING, the intake REFUSES". An intake op landed
# without this check admits net, which is C7's red world in its own words — and moving the
# question to the shim would put it outside the gate, which is the second-source-of-truth
# DEV-LAW-BIND refuses by name.
#
# THESE ROWS PIN EACH CANDIDATE'S OWN VERDICT PAIR, never a bare count of zero. W3b's block
# above states the reason and this section obeys it: a count of zero over a vocabulary about
# to grow is a check waiting to invert (failure-record item 10). Every candidate names its
# subject and pins what that subject DID, so the table reds when a kind's behaviour moves —
# and `THE_LIVE_CHECK_KINDS` reds when the vocabulary itself moves, which is the moment this
# walk must be re-driven rather than trusted.
#
# ========================= THE FINDING RE-OPENED AND WAS RE-TAKEN =========================
# [EP-29 W3a3, 2026-08-14. THE PINNED-POPULATION ROW REDDENED, WHICH IS THE MECHANISM WORKING
# AND NOT A REGRESSION, and it is the first named member of this pass's §A57 sweep.
#
# WHAT HAPPENED: the establishment above went to the owner as the §5 gate's evidence, and the
# owner RULED on 2026-08-14, by explicit act, that the vocabulary grows TWELVE TO THIRTEEN.
# `prior_value` landed with the intake operation as one law pass. So a kind entered OP_CHECKS,
# `THE_LIVE_CHECK_KINDS` redded exactly as its own comment promised, and the walk below was
# RE-DRIVEN over thirteen rather than repaired to pass over twelve. Making it pass would have
# been the defect: the row exists to stop a reader at this moment.
#
# WHAT THE RE-TAKE CHANGED, and nothing else moved: the population is THIRTEEN; the walk
# carries an eighteenth candidate, the licensed kind, driven in the same harness against the
# same two declarations; and the answer row now states EXACTLY ONE SEPARATOR AND NAMES IT,
# where it previously stated none. THE TWELVE STILL SEPARATE NOTHING — every one of their
# verdict pairs is unmoved, which is what makes the new pair a fact about the new kind rather
# than about a harness that changed underneath.
#
# THE CLASS NAME IS KEPT DELIBERATELY. It names an ESTABLISHMENT — a historical act whose
# answer was true of the world it was taken in — and it is cited by that name in the board
# (:751), in W3a2's BUILD-PROGRESS entry with its full seventeen-row table, and in this
# section's own §A57 row. Renaming it would falsify three records to tidy one string. This
# bracket is the estate's own answer to a stale self-description (the file header carries the
# same shape): the name stands, the reader is told, and the rows say what is true now.
#
# TWO ROW NAMES DID MOVE, and only the two whose own words carried the falsified number —
# documented as flips with their cause below, no row added and none removed.]
# ==========================================================================================

#: THIS PASS'S OWN PRE-WRITE COMMIT, taken with `git rev-parse HEAD` before any write (§A53 —
#: `git checkout --` no longer undoes a write since the 2026-08-03 autosync repair, so the commit
#: is TAKEN and not trusted). It is the 1.23.0 ERA: the world W3a3 moved off, and the era every
#: assertion this move falsified is pinned to.
#: PINNED BY CONTENT AND NEVER BY VERSION NUMBER — `era_pin`'s own stated cap and this estate's
#: most expensive known trap. A row below checks the blob's digest against the sha256 W3a's close
#: recorded rather than trusting this comment.
W3A3_BEFORE_COMMIT = "be0d00e8a046634e0c86566fa7e2507a1d852dfd"
W3A3_BEFORE_VERSION = "1.23.0"
W3A3_AFTER_VERSION = "1.24.0"
W3A3_BEFORE_PACK_SHA = "199e6dac38ab85f26c8df0304ddcdba200bcdbcc9021485899de3b811d5bba05"

#: THE SAME COMMIT UNDER THE NAME THIS PASS'S §A57 FLIPS USE IT BY, because the two names answer
#: two different questions and a reader of a flipped row should meet the right one. To this pass
#: it is the BEFORE. To every row this pass falsified it is the world those rows were true of —
#: W3a's own AFTER era, which W3a2's green stop left byte-unchanged.
#:
#: AND THAT IS ESTABLISHED BY CONTENT RATHER THAN BY ADJACENCY, which is the whole of §A57's own
#: repair: the pack at this commit hashes to the digest W3a's close recorded, asserted by
#: `TheFoundingMovedAtW3a3.test_the_era_pin_is_verified_BY_CONTENT_and_never_by_version_number`.
#: Choosing a pin by version number is this estate's most expensive known trap, and choosing one
#: by "the commit before mine" is the same trap wearing a timestamp.
W3A_AFTER_ERA_COMMIT = W3A3_BEFORE_COMMIT

#: W3a3'S OWN CLOSE — THE AFTER END OF THIS PASS'S ENGINE-DIFF RANGE [EP-30-R1, 2026-08-16,
#: charter §A57 backward era-pin, discharged for ONE row]. The engine-diff row below had its
#: BEFORE end pinned and its AFTER end LIVE, which is an open range wearing a closed range's
#: clothes: its subject was not what W3a3 moved but everything that has moved since, forever.
#:
#: DERIVED AND NEVER ADOPTED, and the derivation is the point, because THE OBVIOUS CHECK DOES
#: NOT DISCRIMINATE HERE. The eleven-path comparison against the BEFORE era answers
#: `moved == ['src/kernel/opdefs.py']` AND `founding_version == '1.24.0'` at THREE DISTINCT
#: COMMITS — 51da0898, c5e993a2 and 8b4ddeed — and the last of those is EP-30-W1a's FIRST
#: commit, which belongs to a LATER PASS. So the row's own content check ADMITS THE NEXT
#: PASS'S WORK AS THIS ONE'S, and a pin taken by "the commit that answers right" would have
#: recorded a false era while every assertion stayed green.
#:
#: THE DIGEST IS THE PIN AND THE COMMIT IS ITS ALIAS (board :962). The three candidates are
#: separated by `src/kernel/opdefs.py`'s own bytes AND BY NOTHING ELSE:
#:     51da0898  4dfb4fc844fe78c1…   the pack's own landing, engine not yet at its close
#:     c5e993a2  7744aa0962f78332…   THIS PIN — W3a3's last engine write
#:     8b4ddeed  158d66144d20c130…   W1a's first commit, a later pass, already +99 lines here
#: Derived from the path's COMPLETE history (`git log -- src/kernel/opdefs.py`, whose whole
#: record is 20 commits) and NEVER from a window over the repository's 1,998: choosing a pin
#: by adjacency, by version number, or by a search window is this estate's most expensive
#: known trap and the one §A57's own 2026-08-09 repair retired.
W3A3_AFTER_COMMIT = "c5e993a232d3f5f24a3ada9059c5782d6b41e489"
W3A3_AFTER_OPDEFS_SHA = "7744aa0962f783325aa3c0dd785b4fab5c9f5890c665967b22e5461807a0ff8e"

#: THE ESTATE'S ONE READER FOR THE CHECK VOCABULARY, loaded by path and IMPORTED RATHER THAN
#: RE-DERIVED — `tools/docmap/checkvocab.py` reads `OP_CHECKS` by AST, refuses loudly on anything
#: it cannot read exactly, and is the home EP-28V built for exactly this question. A second AST
#: walk here would be the eighteen-copy shape arriving at a vocabulary instead of at an era pin.
#: `sys.path` is deliberately NOT touched: unittest runs the whole estate in one process, and a
#: row that prepends a directory changes what every other module resolves.
def _checkvocab():
    spec = importlib.util.spec_from_file_location(
        "govos_ep29_checkvocab", os.path.join(REPO, "tools", "docmap", "checkvocab.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def kinds_at(commit):
    """The check vocabulary AS IT STOOD at a commit — the era's own source, through the one
    reader. Used by every row this pass's widening falsified, so a historical claim about the
    vocabulary is checked against the history it was made about and never against today."""
    return _checkvocab().check_kinds_from_source(
        era_pin.text_at(commit, "src/kernel/opdefs.py"))

#: THE CHECK VOCABULARY THIS WALK WAS DRIVEN OVER. [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14.
#: CAUSE: the owner's §5 ruling landed `prior_value`, so this pass's own move falsified the
#: twelve-member pin — §A57's population, by falsification, and this is its first named
#: member. ASSERTED: the twelve kinds ADDENDUM 3 C6 held shut. SUPERSEDED: the thirteen the
#: owner licensed. REMAINS TRUE: the pin's whole function — the establishment's answer is
#: bound to a POPULATION, and a kind entering or leaving OP_CHECKS reds here and means the
#: walk states nothing until it is re-driven. GIVEN UP: nothing; the row is not era-pinned,
#: because a live vocabulary is exactly what it must keep watching.]
#: [DOCUMENTED FLIP — EP-30-C1R, 2026-08-21, ruled at board `:1618`. CAUSE: RANGE. EP-30-C1
#: landed `value_domain` and `live_slot` under the owner's SECOND act (`:1603`), so the
#: thirteen-member pin was falsified. SUBJECT-ERA: LIVE — this constant's own comment above
#: says why, and it is unchanged: "the row is not era-pinned, because a live vocabulary is
#: exactly what it must keep watching". ASSERTED: thirteen. SUPERSEDED: fifteen. REMAINS
#: TRUE: the pin's whole function, which is to STOP a reader the moment the vocabulary moves.
#: GIVEN UP: nothing.
#:
#: AND THE ROWS THAT DEPENDED ON IT SPLIT IN TWO DIRECTIONS, which is the ruling's substance
#: and not a filing convenience: rows whose subject is THE VOCABULARY BEFORE THE OWNER'S
#: 2026-08-14 RULING are HISTORICAL and now read `THE_PRE_RULING_VOCABULARY` below; rows whose
#: subject is the LIVE vocabulary re-derive against fifteen. SAME FILE, SAME VARIABLE,
#: OPPOSITE LAWFUL REPAIRS, AND ONLY SUBJECT-ERA SEPARATES THEM.]
#: [DOCUMENTED FLIP — EP-30-K2W, 2026-09-02, on the yes-branch of the RAISE the owner ruled
#: STANDS (board `:2639`, carried by archi `:2640`). THE SEVERANCE SUCCESSOR: the tuple pin
#: severed from EP-30-K2R at `:2392` was red because THIS constant answered about FIFTEEN kinds
#: while OP_CHECKS held SEVENTEEN — the walk never reached `bound_field` (K1's sixteenth) or
#: `every_member` (K2's seventeenth). This flip re-pins the constant to seventeen, AND IT
#: FOLLOWS THE DRIVE AND NEVER PRECEDES IT — a re-pin before the drive is option A, which the
#: tuple pin's own docstring forbids. CAUSE: the walk below was extended over the two absent
#: members and each was DRIVEN through `_separates` before this line moved.
#:
#: THE FINDING THAT GATED THIS RE-PIN, now settled: the STRONGEST formulation of EACH new kind
#: produces (ADMIT, REFUSE) on the threshold read — bound_field by comparing the bound record's
#: threshold value to block's own literal, every_member by quantifying prior_value. That tripped
#: stop condition 2 and stopped this unit at its owner-gate. THE OWNER RULED STANDS: bound_field's
#: separation is a COINCIDENCE of the `value_domain` class (it tracks the caller literal 6144 and
#: STILL separates when net is established to 3518, so its verdict reads a number the test supplied
#: and not the record's establishment), and every_member's is a CONFIRMATION (it separates ONLY by
#: borrowing prior_value as its inner, and confirms rather than refutes that prior_value was the
#: necessary separator). The PROPERTY-AIMED formulations walked below do NOT separate, so
#: `THE_SEPARATORS` is unchanged and the §5 record — prior_value the one necessary separator — is
#: undisturbed. Evidence: planning/evidence/EP-30-K2W/A3-THE-FINDING-do-they-separate.txt and the
#: RAISE at planning/evidence/EP-30-K2W/RAISE-stop-condition-2.txt.
#: ASSERTED: fifteen. SUPERSEDED: seventeen. REMAINS TRUE: the pin's whole function — the
#: establishment's answer is bound to a POPULATION, and a kind entering or leaving OP_CHECKS reds
#: here and means the walk states nothing until it is re-driven. GIVEN UP: nothing; the row is not
#: era-pinned, because a live vocabulary is exactly what it must keep watching. ORDER IS EXACT:
#: this literal records what the drive returned (seventeen, in OP_CHECKS order), never the walk
#: fitted to a pin.]
#: [DOCUMENTED FLIP — EP-49C, 2026-09-08, the owner's TWO-KIND ruling (board :3354/:3355, "go
#: yes"). SUBJECT-ERA: LIVE — this constant's own function, unchanged since its first flip: "a
#: kind entering or leaving OP_CHECKS reds here", and it must keep watching the live vocabulary,
#: so it re-pins rather than era-pins. CAUSE: the FIRST vocabulary growth since design/40 — the
#: owner ruled `live_present` (the polarity complement of live_slot) and `fold_threshold` (a fold
#: vs a threshold), code-born in opdefs. ASSERTED: seventeen. SUPERSEDED: nineteen. FOLLOWS THE
#: DRIVE AND NEVER PRECEDES IT: the two kinds are in OP_CHECKS at positions 18 and 19 (driven from
#: the live tuple this hand); this literal records that order. REMAINS TRUE: the pin's whole
#: function. GIVEN UP: nothing.]
THE_LIVE_CHECK_KINDS = ("require_prior", "sight", "ceiling", "consistency", "sop",
                        "definition_ref", "entry_ref", "space_tree", "fingerprint",
                        "binding", "kind", "contains", "prior_value",
                        "value_domain", "live_slot", "bound_field", "every_member",
                        "live_present", "fold_threshold")

#: THE VOCABULARY AS IT STOOD BEFORE THE OWNER'S RULING OF 2026-08-14, AS ITS OWN LITERAL.
#: [ADDED — EP-30-C1R, 2026-08-21, ruled at board `:1618`. It was twelve, it IS twelve, and it
#: will always be twelve: it names a FINISHED WORLD. It was previously DERIVED as the live set
#: minus the licensed thirteenth, and that derivation worked exactly until the live set moved
#: for an unrelated reason — DERIVING A HISTORICAL POPULATION FROM A LIVE ONE is the root
#: defect here, not the number. Moving the derived form to fourteen would have swept in
#: `value_domain` and `live_slot`, kinds the owner ruled on in a DIFFERENT act months of
#: campaign later, and made the rows below assert something about them NOBODY HAS ESTABLISHED.
#: That changes what a row claims, so it is an S-stop and never a sweep.
#:
#: THE TELL THAT MADE THESE ROWS FINDABLE, kept because the next hand will need it: a row that
#: ASSERTS ITS OWN COUNT IN ITS TITLE — `ALL_TWELVE`, `NOT_ONE_OF_THE_TWELVE` — while DERIVING
#: that count from a live set is the stored-versus-computed defect wearing the answer as a
#: label, and one of them had a docstring boasting of the derivation the next line defeated.]
THE_PRE_RULING_VOCABULARY = ("require_prior", "sight", "ceiling", "consistency", "sop",
                             "definition_ref", "entry_ref", "space_tree", "fingerprint",
                             "binding", "kind", "contains")

#: THE ONE KIND THE OWNER LICENSED, named on its own so "exactly one" is a NAMED ROW and never
#: a count (failure-record item 10: a check whose right answer is a number in a growing file is
#: a check waiting to invert). A second kind riding this licence reds the arithmetic below.
THE_LICENSED_THIRTEENTH = "prior_value"

#: THE CHECK-ROW GRAMMAR — every declaration key any SHIPPED check row uses. Pinned beside
#: the kinds because the two pins catch different events, and only one of them is obvious: a
#: NEW KIND reds `THE_LIVE_CHECK_KINDS`, but an EXISTING kind gaining reach through a new
#: declaration key would not, and that is the likeliest shape of an answer to W3a2's stop
#: (C6 asks for kinds PARAMETERIZED before it asks for a new one). A key arriving here means
#: the walk below was driven over a grammar that no longer exists.
THE_CHECK_ROW_GRAMMAR = [
    "action", "aggregate_action", "aggregate_field", "amount_param", "binds_kind", "check",
    "cite", "cite_correlation", "cite_cycle", "cite_missing", "crossing_param",
    "entity_kind_param", "effect", "field", "forbid", "holder_field", "holder_param",
    "id_param", "key_of", "key_param", "message", "param", "parent_param",
    "policy_key_param", "policy_key_prefix", "removal_action", "require", "seq_param",
    "target_param", "term_param", "value_param",
    # [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14. CAUSE: this pass's own move; the pin's own
    # comment named this exact event as the one the kind pin cannot see, and it fired. ASSERTED:
    # 31 keys. SUPERSEDED: 32. REMAINS TRUE: everything else, and the arrival is BOUNDED — the
    # licensed kind adds exactly ONE key and speaks the rest of its row in grammar the twelve
    # already spoke, which is asserted as arithmetic against the era two rows below.]
    "value_field",
    # [DOCUMENTED FLIP — EP-30-C1R, 2026-08-21. CAUSE: RANGE. SUBJECT-ERA: LIVE — this pin's
    # whole function is to watch the SHIPPED grammar now, so it RE-POPULATES and is never
    # era-pinned: an era-pin here would compare the live pack's rows to a historical grammar
    # and go green while asserting nothing. ASSERTED: 32 keys. SUPERSEDED: 37. REMAINS TRUE:
    # the pin's function and its exact mechanism, unchanged — it reds on the NEXT key.
    # GIVEN UP: nothing. RE-POPULATION IS NOT WEAKENING: a weakened control asserts LESS; this
    # one asserts THE SAME THING about a moved world, and A11 drives it against the old
    # population to show it still reds there.
    #
    # THE FIVE ARRIVALS ARE EXACTLY EP-30-C1'S TWO KINDS' DECLARATION KEYS AND NOTHING ELSE,
    # which is what keeps the licence bound readable: `domain` is value_domain's whole
    # declaration, and `open_action`/`close_action`/`instance_param`/`slot_params` are
    # live_slot's four. No existing kind gained a key.]
    "domain",
    "open_action", "close_action", "instance_param", "slot_params",
    # [DOCUMENTED FLIP — EP-30-K1R, 2026-08-26. CAUSE: RANGE. SUBJECT-ERA: LIVE, and that is
    # NOT a choice made here — the C1R flip four lines above already ruled this pin's era, in
    # this pin's own comment: its whole function is to watch the SHIPPED grammar NOW, so it
    # RE-POPULATES and is never era-pinned, because an era-pin here would compare the live
    # pack's rows to a historical grammar and go green while asserting nothing. ASSERTED: 37
    # keys. SUPERSEDED: 38. REMAINS TRUE: the pin's function and its exact mechanism — it reds
    # on the NEXT key, and A3 drives that rather than promising it.
    #
    # THE ARRIVAL IS EXACTLY ONE KEY AND IT IS BOUNDED, which is the whole content of the
    # claim and the reason this is a re-population rather than a loosening. `when_unbound` is
    # `bound_field`'s ONE new declaration key — EP-30-K1's sixteenth kind — and `bound_field`
    # speaks the rest of its row (`action`, `field`, `key_param`, `value_field`, `param`,
    # `cite`, `message`) in grammar the fifteen already spoke. NO EXISTING KIND GAINED A KEY.
    #
    # AND THE ROW IS SINGLY CAUSED, DRIVEN RATHER THAN ASSUMED: exactly one shipped check row
    # in the whole pack uses `when_unbound` — FILE-CUSTODY-TRANSFER's `bound_field` check —
    # and EP-30-K2's seventeenth kind `every_member` has NO shipped user in the pack at all,
    # so it contributed zero keys here. A pin re-taken to 38 is therefore not stale on the day
    # it lands, which is the test mtr `:2304` set for whether a re-pin may be authored at all.
    "when_unbound",
    # [DOCUMENTED FLIP — EP-49C, 2026-09-08, the owner's TWO-KIND ruling (board :3354/:3355).
    # SUBJECT-ERA: LIVE, by this pin's own standing function (four lines up): it watches the
    # SHIPPED grammar NOW and re-populates rather than era-pins. CAUSE: RANGE — `live_present` and
    # `fold_threshold` land as founding check rows on COMMS-SEND/RECV/CLOSE and speak NINE keys no
    # shipped row spoke before. ASSERTED: 38 keys. SUPERSEDED: 47. REMAINS TRUE: the pin's function
    # and its exact mechanism — it reds on the NEXT key. THE ARRIVALS ARE EXACTLY THE TWO KINDS'
    # DECLARATION KEYS AND NOTHING ELSE: `key_params`/`present`/`close_actor_key` are live_present's
    # (it speaks `open_action`/`close_action`/`check`/`cite`/`message` in grammar already present),
    # and `add_action`/`sub_action`/`key_field`/`operator`/`threshold`/`fold_name` are
    # fold_threshold's. NO EXISTING KIND GAINED A KEY. GIVEN UP: nothing.]
    "key_params", "present", "close_actor_key",
    "add_action", "sub_action", "key_field", "operator", "threshold", "fold_name",
]
THE_CHECK_ROW_GRAMMAR = sorted(THE_CHECK_ROW_GRAMMAR)

#: The op name every candidate is minted under. Never founded; it exists only inside the
#: in-memory packs this section builds.
_PROBE = "INTAKE-PROBE"

#: The two shipped declarations, and the field the question is about. The pair is the whole
#: subject: they were declared by ONE op under ONE law at ONE grade and differ in exactly
#: this field, so a formulation that separates them separates on the threshold and on
#: nothing else available to it.
_BLOCK_INTAKE, _NET_INTAKE = "device-intake@block", "device-intake@net"
_THRESHOLD_FIELD = "max_arrivals"


def _mint_candidate(pack, params, checks, extra_records=()):
    """Put ONE candidate op into a pack's own op-definition step, plus any planted records.

    The candidate is a full definition through the ORDINARY door, so a formulation the
    founding installer refuses is refused here for the installer's reason and not for a
    shape this file invented."""
    step = [s for s in pack["steps"] if s["step"] == "08-op-definitions"][0]
    for rec in extra_records:
        step["records"].insert(0, rec)
    step["records"].append({
        "actor": "PC_RUNTIME", "action": "CREATE-OP", "object": "op:%s" % _PROBE,
        "rule_cited": "CAP-IS-LAW",
        "payload": {"kind": "op_definition", "rule_id": "op:%s" % _PROBE, "polarity": "+",
                    "name": _PROBE, "tier": "owner",
                    "text": "an expressibility candidate, minted in memory for W3a2's walk",
                    "definition": {"description": "W3a2 expressibility candidate",
                                   # C6 P8 (L28): a candidate minted into the CELL-LAW pack must declare
                                   # a cell (structured record-mechanic, S) or the founding door refuses
                                   # it — this candidate tests check-kind expressibility, cell orthogonal.
                                   "cell": "S",
                                   "params": params, "law_cited": "DEV-LAW-INTAKE",
                                   "payload_from": sorted(params),
                                   # the candidate records EVERY param inline (payload_from == all
                                   # params, above), so by the op's own shape every field is a
                                   # structural governance scalar/handle read inline, never blob-homed
                                   # content — classify them to match (vocab door — design/46 member 2).
                                   # The op's shape (payload_from) overrides any name-mirror (e.g. ek/hs):
                                   # a field written inline into the row cannot be CONTENT by construction.
                                   "structural_params": sorted(params), "checks": checks}},
    })
    return pack


def _verdicts(params, checks, call_a, call_b, extra_records=(), actor="owner", pack=None):
    """THE ONE PREDICATE, called by the claim AND by both controls — never two copies
    agreeing with each other.

    Returns the pair of gate verdicts for the two calls: "ADMIT", "REFUSE:<rule>",
    "ERROR:<class>", or "DEFINITION-REFUSED" when the founding door rejects the formulation.
    A verdict is what the GATE did, never a reading of the row.

    `pack` overrides the base the candidate is minted into. [ADDED at EP-30-C1R, 2026-08-21,
    so the tracking control below can drive THE SAME PREDICATE against a world where the
    property is absent. A second predicate for that job would be two copies agreeing with
    each other, which this docstring already forbids.]"""
    try:
        w = _World(_mint_candidate(live_pack() if pack is None else pack,
                                   params, checks, extra_records))
    except Exception:                       # the installer refused the formulation itself
        return ("DEFINITION-REFUSED", "DEFINITION-REFUSED")
    out = []
    for call in (call_a, call_b):
        try:
            w.call(_PROBE, actor=actor, **call)
            out.append("ADMIT")
        except OpError as exc:
            out.append("REFUSE:%s" % exc.rule)
        except Exception as exc:
            out.append("ERROR:%s" % type(exc).__name__)
    return tuple(out)


def _separates(pair):
    """The property, stated once: admits the class whose threshold IS a value and refuses
    the class whose threshold is not. Any other pair is not the property."""
    return pair[0] == "ADMIT" and pair[1].startswith("REFUSE")


def _intake_payload(pack, name):
    for st in pack["steps"]:
        for r in st["records"]:
            if r.get("action") == "DECLARE-INTAKE" and r["payload"]["intake"] == name:
                return r["payload"]
    raise AssertionError("no DECLARE-INTAKE record for %r" % name)


def _declaration_seqs(world):
    """The two declarations' record seqs, resolved AT RUN TIME by action. Never pinned as
    literals: a seq is a position in a growing record and a literal one would be a version
    constant wearing an integer."""
    return {(e.get("payload") or {}).get("intake"): e["seq"]
            for e in world.store.all() if e["action"] == "DECLARE-INTAKE"}


class TheThresholdReadIsNotExpressibleInTheLiveVocabulary(unittest.TestCase):
    """EP-29 W3a2 C8 — the vocabulary question, DRIVEN and answered.

    POPULATION: the twelve kinds of `opdefs.OP_CHECKS` at this pass's tree, each in the
    strongest formulation aimed at the property, plus the two-row conjunction attempt —
    seventeen candidates.
    BASIS: each candidate is minted into the live pack, a world is BOOTED from that pack,
    and the op is CALLED once per declaration. The verdict is the gate's."""

    def setUp(self):
        self.w = _World()
        self.pack = live_pack()

    # ------------------------------------------------------------------ non-vacuity, first
    def test_the_two_declarations_are_live_and_their_threshold_fields_DIFFER(self):
        """ITEM-21 NON-VACUITY, and it is the sharpest one this section needs: if the two
        declarations did not differ in this field, EVERY candidate below would fail to
        separate them for a reason that has nothing to do with the vocabulary, and the whole
        walk would read identically on the page."""
        landed = sorted((e.get("payload") or {})["intake"] for e in self.w.store.all()
                        if e["action"] == "DECLARE-INTAKE")
        self.assertEqual(landed, [_BLOCK_INTAKE, _NET_INTAKE],
                         "the founding's own intake declarations are not in the record, so "
                         "the walk below is the empty world")
        blk = _intake_payload(self.pack, _BLOCK_INTAKE)[_THRESHOLD_FIELD]
        net = _intake_payload(self.pack, _NET_INTAKE)[_THRESHOLD_FIELD]
        self.assertIsNotNone(blk["value"], "block's threshold is not a value, so there is "
                                           "nothing for a candidate to admit on")
        self.assertIsNone(net["value"], "net's threshold IS a value, so there is nothing "
                                        "for a candidate to refuse on")
        self.assertEqual(sorted(blk), sorted(net),
                         "the two declarations' threshold fields no longer carry the same "
                         "keys, so a separation could come from shape and not from value")

    def test_the_check_vocabulary_IS_THE_PINNED_POPULATION_this_walk_was_driven_over(self):
        """THE PINNED-POPULATION ROW. [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14. Renamed from
        `test_the_check_vocabulary_IS_THE_TWELVE_this_walk_was_driven_over`: the name carried
        the falsified number in its own words, and a row named for twelve while asserting
        thirteen is the stale self-description class. CAUSE: the owner's §5 ruling. ASSERTED:
        twelve. SUPERSEDED: thirteen. REMAINS TRUE: the row's whole function, which is why the
        new name states the FUNCTION and no number — so the next ruling costs a constant and
        not a rename.]

        THIS ROW DID ITS JOB AND THE JOB LOOKED LIKE A FAILURE, which is worth leaving on the
        record where the next reader stands: it reddened the moment the thirteenth kind landed,
        and the correct response was to re-drive the walk, not to make the row pass. The answer
        below is an answer ABOUT A POPULATION; a kind added or retired makes it an answer about
        a population that no longer exists."""
        self.assertEqual(tuple(opdefs.OP_CHECKS), THE_LIVE_CHECK_KINDS,
                         "the check vocabulary moved: %r. This walk was driven over the pinned "
                         "population above and states nothing about a kind outside it — "
                         "re-drive it before reading its answer, and note that a new kind is "
                         "the §5 owner gate's own subject"
                         % (list(opdefs.OP_CHECKS),))

    # ------------------------------------------------------------------- the two controls
    def test_the_predicate_SEPARATES_on_a_property_that_IS_expressible(self):
        """CONTROL ONE. A zero needs a positive control, and this estate has shipped a
        consumer search whose control also returned empty, so its zero proved nothing.
        `require_prior` over DECLARE-IO-WINDOW is a property the vocabulary DOES express:
        a declared window admits and a name nobody declared refuses."""
        pair = _verdicts(
            {"intake": "required", "window": "required"},
            [{"check": "require_prior", "action": "DECLARE-IO-WINDOW", "field": "window",
              "param": "window", "cite": "DEV-LAW-INTAKE"}],
            {"intake": _BLOCK_INTAKE, "window": "device-io@block"},
            {"intake": _NET_INTAKE, "window": "device-io@nowhere"})
        self.assertTrue(_separates(pair),
                        "the predicate cannot separate on a property the vocabulary is "
                        "known to express (%r), so its empty answer below says nothing "
                        "about the vocabulary and everything about this harness" % (pair,))

    def test_the_predicate_separates_ON_THE_INTAKE_RECORDS_THEMSELVES(self):
        """CONTROL TWO, and it is the one that narrows the finding to its true width. The
        first control reaches a DIFFERENT action's records; this one discriminates on the
        DECLARE-INTAKE records the question is about, through the same kind, in the same
        harness. It passing while every candidate fails is what makes the finding a fact
        about THE SHAPE — read a nested field of the record my parameter names, and test it
        for presence-of-a-value — rather than about reach into these records."""
        pair = _verdicts(
            {"intake": "required", "device_class": "required"},
            [{"check": "require_prior", "action": "DECLARE-INTAKE", "field": "device_class",
              "param": "device_class", "cite": "DEV-LAW-INTAKE"}],
            {"intake": _BLOCK_INTAKE, "device_class": "block"},
            {"intake": _NET_INTAKE, "device_class": "ether"})
        self.assertTrue(_separates(pair),
                        "the predicate cannot discriminate on the intake records at all "
                        "(%r), so the walk below measures the harness" % (pair,))

    # --------------------------------------------------------------------------- the walk
    def _candidates(self):
        """The seventeen, with the calls each is driven with. Built here rather than at
        module scope because two of them resolve a record seq from a booted world."""
        blk = _intake_payload(self.pack, _BLOCK_INTAKE)[_THRESHOLD_FIELD]
        net = _intake_payload(self.pack, _NET_INTAKE)[_THRESHOLD_FIELD]
        seqs = _declaration_seqs(self.w)
        base = {"intake": "required", "count": "required"}
        A, B = {"intake": _BLOCK_INTAKE, "count": 10}, {"intake": _NET_INTAKE, "count": 10}
        rp = "require_prior"
        return (
            ("require_prior/the-declaration-exists", base,
             [{"check": rp, "action": "DECLARE-INTAKE", "field": "intake", "param": "intake",
               "cite": "DEV-LAW-INTAKE"}], A, B),
            ("require_prior/threshold-dict-vs-block's-own", dict(base, probe="required"),
             [{"check": rp, "action": "DECLARE-INTAKE", "field": _THRESHOLD_FIELD,
               "param": "probe", "cite": "DEV-LAW-INTAKE"}],
             dict(A, probe=blk), dict(B, probe=blk)),
            ("require_prior/threshold-dict-vs-each-class's-own", dict(base, probe="required"),
             [{"check": rp, "action": "DECLARE-INTAKE", "field": _THRESHOLD_FIELD,
               "param": "probe", "cite": "DEV-LAW-INTAKE"}],
             dict(A, probe=blk), dict(B, probe=net)),
            ("require_prior/nested-field-path", dict(base, probe="required"),
             [{"check": rp, "action": "DECLARE-INTAKE", "field": _THRESHOLD_FIELD + ".value",
               "param": "probe", "cite": "DEV-LAW-INTAKE"}],
             dict(A, probe=blk["value"]), dict(B, probe=blk["value"])),
            ("require_prior/two-row-conjunction", dict(base, probe="required"),
             [{"check": rp, "action": "DECLARE-INTAKE", "field": "intake", "param": "intake",
               "cite": "DEV-LAW-INTAKE"},
              {"check": rp, "action": "DECLARE-INTAKE", "field": _THRESHOLD_FIELD,
               "param": "probe", "cite": "DEV-LAW-INTAKE"}],
             dict(A, probe=blk), dict(B, probe=blk)),
            ("sight/target-is-the-intake-name", base,
             [{"check": "sight", "target_param": "intake"}], A, B),
            ("ceiling/aggregate-the-threshold-fields", dict(base, holder="required"),
             [{"check": "ceiling", "holder_param": "holder",
               "policy_key_prefix": "intake.threshold.", "aggregate_action": "DECLARE-INTAKE",
               "holder_field": "intake", "key_param": "intake",
               "aggregate_field": _THRESHOLD_FIELD, "removal_action": "RETIRE-INTAKE",
               "amount_param": "count", "cite": "DEV-LAW-INTAKE"}],
             dict(A, holder=_BLOCK_INTAKE), dict(B, holder=_NET_INTAKE)),
            ("consistency/policy-key-is-the-intake-name", base,
             [{"check": "consistency", "policy_key_param": "intake", "value_param": "count",
               "cite": "DEV-LAW-INTAKE"}], A, B),
            ("sop/target-is-the-intake-name", base,
             [{"check": "sop", "target_param": "intake"}], A, B),
            ("definition_ref/intake-name-as-a-dictionary-term", dict(base, ek="required"),
             [{"check": "definition_ref", "entity_kind_param": "ek", "term_param": "intake",
               "cite": "DEV-LAW-INTAKE"}], dict(A, ek="intake"), dict(B, ek="intake")),
            ("entry_ref/name-the-declaration-by-seq", dict(base, ref_seq="required"),
             [{"check": "entry_ref", "seq_param": "ref_seq", "cite": "DEV-LAW-INTAKE"}],
             dict(A, ref_seq=seqs[_BLOCK_INTAKE]), dict(B, ref_seq=seqs[_NET_INTAKE])),
            ("space_tree/intake-name-as-a-parent-space", base,
             [{"check": "space_tree", "parent_param": "intake", "cite_cycle": "BOOT-INT",
               "cite_missing": "DEV-LAW-INTAKE"}], A, B),
            ("fingerprint/cite-the-declaration-as-a-hand-out", dict(base, hs="required"),
             [{"check": "fingerprint", "crossing_param": "hs"}],
             dict(A, hs=seqs[_BLOCK_INTAKE]), dict(B, hs=seqs[_NET_INTAKE])),
            ("binding/require-the-intake-name-bound", base,
             [{"check": "binding", "key_param": "intake", "require": "bound",
               "cite": "DEV-LAW-INTAKE"}], A, B),
            ("kind/require-a-class-meaning-threshold-established", base,
             [{"check": "kind", "key_param": "intake", "require": "intake-with-threshold",
               "cite": "DEV-LAW-INTAKE"}], A, B),
            ("kind/forbid-a-class-meaning-threshold-unestablished", base,
             [{"check": "kind", "key_param": "intake", "forbid": "intake-unestablished",
               "cite": "DEV-LAW-INTAKE"}], A, B),
            ("contains/require-the-intake-name-to-hold-nothing", base,
             [{"check": "contains", "key_param": "intake", "require": "empty",
               "cite": "DEV-LAW-INTAKE"}], A, B),
            # THE EIGHTEENTH CANDIDATE — the kind the owner licensed, driven in the SAME harness
            # against the SAME two declarations as the seventeen that could not. [ADDED at the
            # W3a3 re-take, 2026-08-14. It is the only candidate that separates, and the answer
            # row below names it rather than counting it.]
            ("prior_value/the-cited-declarations-threshold-IS-a-value", base,
             [{"check": "prior_value", "action": "DECLARE-INTAKE", "field": "intake",
               "param": "intake", "value_field": _THRESHOLD_FIELD + ".value",
               "require": "established", "cite": "DEV-LAW-INTAKE"}], A, B),
            # THE NINETEENTH AND TWENTIETH CANDIDATES — the two kinds the owner ruled on at
            # board `:1603`, driven in the SAME harness against the SAME two declarations.
            # [ADDED at EP-30-C1R, 2026-08-21. They are here because the coverage row below
            # asks whether the walk reaches every kind in the LIVE vocabulary and the live
            # vocabulary is now fifteen; a walk over thirteen answering about fifteen is a
            # filter that cannot match wearing a census, which is that row's own sentence.
            #
            # THE FORMULATIONS ARE THE GENERALS OF THE SPECIALS ALREADY WALKED, STATED IN THE
            # SAME SYMBOLIC CONVENTION. design/28 §5 names `value_domain` the general of
            # `kind` and `binding`, and `live_slot` the general of `binding`'s bound/unbound
            # pair. `kind/require-a-class-meaning-threshold-established` states the class
            # SYMBOLICALLY; its general states the same content as a one-member domain.
            #
            # AND THE ALTERNATIVE WAS REJECTED BY A DRIVE, NOT BY TASTE — it is the finding
            # this pass owes the next reader. A `value_domain` row whose domain is a LITERAL
            # LIST NAMING THE BLOCK DECLARATION returns ("ADMIT", "REFUSE:DEV-LAW-INTAKE") and
            # would read here as a SECOND SEPARATOR. It is not one. Driven in a world where
            # NET's threshold IS established, that formulation STILL refuses net, while
            # `prior_value` correctly stops separating: ITS VERDICT DOES NOT TRACK THE
            # PROPERTY, because it never reads the record — it is a stored answer, and
            # `_separates` would be reading a coincidence. The row directly below pins that
            # discrimination so it is a check and not a note.
            ("value_domain/domain-is-a-class-meaning-threshold-established", base,
             [{"check": "value_domain", "param": "intake",
               "domain": ["intake-with-threshold"], "cite": "DEV-LAW-INTAKE"}], A, B),
            ("live_slot/the-intake-name-is-a-slot-its-declaration-takes", base,
             [{"check": "live_slot", "open_action": "DECLARE-INTAKE",
               "close_action": "RETIRE-INTAKE", "instance_param": "intake",
               "slot_params": ["intake"], "cite": "DEV-LAW-INTAKE"}], A, B),
            # THE TWENTY-FIRST AND TWENTY-SECOND CANDIDATES — `bound_field` (EP-30-K1's sixteenth
            # kind) and `every_member` (EP-30-K2's seventeenth), the two vocabulary members the
            # walk had never reached, driven in the SAME harness against the SAME two declarations.
            # [ADDED at EP-30-K2W, 2026-09-02, on the yes-branch of the RAISE the owner ruled
            # STANDS (board `:2639`). The coverage row below asks whether the walk reaches every
            # kind in the LIVE vocabulary, and the live vocabulary is now seventeen; a walk over
            # fifteen answering about seventeen is the filter-wearing-a-census the row forbids.
            #
            # THESE ARE THE PROPERTY-AIMED FORMULATIONS, AND THEY DO NOT SEPARATE — which is the
            # whole point of walking them here rather than their strongest cousins. The STRONGEST
            # formulation of each DOES produce (ADMIT, REFUSE), and that is exactly what stopped
            # this unit at its owner-gate (stop condition 2): bound_field can compare the bound
            # record's threshold value to block's own literal, and every_member can quantify
            # prior_value. The owner ruled both are false separators — bound_field's is the
            # `value_domain` COINCIDENCE class (it tracks the caller literal 6144, and STILL
            # separates when net is established to a DIFFERENT value 3518, so it reads a number the
            # test supplied and not the record's establishment), and every_member's is a
            # CONFIRMATION (it separates ONLY by borrowing prior_value as its inner). Both drives,
            # with the C1R falsification applied, are at planning/evidence/EP-30-K2W/ —
            # drive_falsify.py and drive_every_member.py; the finding is A3-THE-FINDING-*.txt.
            #
            # bound_field aimed at the property WITHOUT block's literal: compare the bound
            # record's threshold value to a GENERIC caller value (count=10, the same for both
            # calls). It refuses both — the threshold value is 6144, never 10 — so it does not
            # separate, and its verdict is a real drive: strip its check row and both calls admit.
            ("bound_field/threshold-value-vs-a-generic-caller-value", base,
             [{"check": "bound_field", "action": "DECLARE-INTAKE", "field": "intake",
               "key_param": "intake", "value_field": _THRESHOLD_FIELD + ".value",
               "param": "count", "cite": "DEV-LAW-INTAKE"}], A, B),
            # every_member aimed at the property WITHOUT borrowing prior_value: quantify a
            # non-separating inner (`require_prior` over the threshold field) across a single-member
            # list carrying each call's OWN intake name. Both intakes DO carry the threshold field,
            # so the quantified existence question admits nothing to refuse and both calls refuse
            # on the member — it does not separate, and it is a real drive: strip its check row and
            # both calls admit.
            ("every_member/quantify-the-threshold-existence-over-the-cited-name",
             dict(base, names="required"),
             [{"check": "every_member", "param": "names", "member_param": "one_intake",
               "on_empty": "refuse",
               "inner": {"check": "require_prior", "action": "DECLARE-INTAKE",
                         "field": _THRESHOLD_FIELD, "param": "one_intake",
                         "cite": "DEV-LAW-INTAKE"},
               "cite": "DEV-LAW-INTAKE"}],
             dict(A, names=[_BLOCK_INTAKE]), dict(B, names=[_NET_INTAKE])),
            # THE TWENTY-THIRD AND TWENTY-FOURTH CANDIDATES — `live_present` and `fold_threshold`,
            # the two kinds the owner ruled at board `:3354/:3355` (EP-49C, 2026-09-08), driven in
            # the SAME harness against the SAME two declarations. The coverage row asks whether the
            # walk reaches every kind in the LIVE vocabulary, now nineteen; a walk over seventeen
            # answering about nineteen is the filter-wearing-a-census that row forbids.
            #
            # NEITHER SEPARATES, and neither CAN reach the threshold read: live_present asks whether
            # a member is PRESENT in a set folded from open/close acts (both intakes are declared, so
            # both ADMIT), and fold_threshold compares a COUNT to a threshold (each intake is declared
            # once, so the count is above zero for both, both ADMIT). Neither reads a FIELD'S VALUE
            # inside a cited record, which is prior_value's separating power — so THE_SEPARATORS below
            # is unchanged and the §5 answer stands. Both pairs are DRIVEN at this hand; the drive
            # output set these literals, never the other way round.
            ("live_present/the-intake-name-is-present-in-its-declaration-set", base,
             [{"check": "live_present", "open_action": "DECLARE-INTAKE",
               "close_action": "RETIRE-INTAKE", "key_params": ["intake"],
               "present": {"intake": "intake"}, "cite": "DEV-LAW-INTAKE"}], A, B),
            ("fold_threshold/count-the-declarations-of-the-intake-name", base,
             [{"check": "fold_threshold", "add_action": "DECLARE-INTAKE",
               "sub_action": "RETIRE-INTAKE", "key_param": "intake", "key_field": "intake",
               "operator": ">", "threshold": 0, "fold_name": "declaration_count",
               "cite": "DEV-LAW-INTAKE"}], A, B),
        )

    #: WHAT EACH CANDIDATE DID, pinned per candidate rather than summed into a zero. A
    #: behaviour moving here is a reader being stopped at exactly the right moment: it is
    #: either a kind changing under this estate's feet, or the §5 question being answered.
    CANDIDATE_VERDICTS = {
        "require_prior/the-declaration-exists": ("ADMIT", "ADMIT"),
        "require_prior/threshold-dict-vs-block's-own": ("ADMIT", "ADMIT"),
        "require_prior/threshold-dict-vs-each-class's-own": ("ADMIT", "ADMIT"),
        "require_prior/nested-field-path": ("REFUSE:DEV-LAW-INTAKE", "REFUSE:DEV-LAW-INTAKE"),
        "require_prior/two-row-conjunction": ("ADMIT", "ADMIT"),
        "sight/target-is-the-intake-name": ("ADMIT", "ADMIT"),
        "ceiling/aggregate-the-threshold-fields": ("ADMIT", "ADMIT"),
        "consistency/policy-key-is-the-intake-name": ("ADMIT", "ADMIT"),
        "sop/target-is-the-intake-name": ("ADMIT", "ADMIT"),
        "definition_ref/intake-name-as-a-dictionary-term":
            ("REFUSE:DEV-LAW-INTAKE", "REFUSE:DEV-LAW-INTAKE"),
        "entry_ref/name-the-declaration-by-seq":
            ("REFUSE:DEV-LAW-INTAKE", "REFUSE:DEV-LAW-INTAKE"),
        "space_tree/intake-name-as-a-parent-space":
            ("REFUSE:DEV-LAW-INTAKE", "REFUSE:DEV-LAW-INTAKE"),
        "fingerprint/cite-the-declaration-as-a-hand-out":
            ("REFUSE:CROSSING-CORRELATION", "REFUSE:CROSSING-CORRELATION"),
        "binding/require-the-intake-name-bound": ("DEFINITION-REFUSED", "DEFINITION-REFUSED"),
        "kind/require-a-class-meaning-threshold-established":
            ("DEFINITION-REFUSED", "DEFINITION-REFUSED"),
        "kind/forbid-a-class-meaning-threshold-unestablished":
            ("DEFINITION-REFUSED", "DEFINITION-REFUSED"),
        "contains/require-the-intake-name-to-hold-nothing": ("ADMIT", "ADMIT"),
        # [ADDED at the W3a3 re-take, 2026-08-14 — the licensed kind, and the ONLY pair in this
        # table that separates. Its presence here is what makes the row below a statement about
        # WHICH kind answers the question rather than a count that inverted.]
        "prior_value/the-cited-declarations-threshold-IS-a-value":
            ("ADMIT", "REFUSE:DEV-LAW-INTAKE"),
        # [ADDED at EP-30-C1R, 2026-08-21 — the two kinds of the owner's SECOND act. Neither
        # separates, so THE_SEPARATORS below is unchanged and the establishment's answer is
        # unchanged: the ruling of 2026-08-14 still bought exactly the kind that answers this
        # question. Both pairs are DRIVEN, at the builder's hand, in this harness.]
        "value_domain/domain-is-a-class-meaning-threshold-established":
            ("REFUSE:DEV-LAW-INTAKE", "REFUSE:DEV-LAW-INTAKE"),
        "live_slot/the-intake-name-is-a-slot-its-declaration-takes":
            ("REFUSE:DEV-LAW-INTAKE", "REFUSE:DEV-LAW-INTAKE"),
        # [ADDED at EP-30-K2W, 2026-09-02, owner ruled STANDS `:2639` — the two members the walk
        # had never reached, in their PROPERTY-AIMED formulations. NEITHER separates, so
        # THE_SEPARATORS below is unchanged and the §5 answer is unchanged: prior_value is still
        # the one kind that genuinely separates the threshold read. Both pairs are DRIVEN, at this
        # builder's hand, in this harness — the drive output is what set these literals, never the
        # other way round (planning/evidence/EP-30-K2W/A2-formulations-added-and-driven.txt).]
        "bound_field/threshold-value-vs-a-generic-caller-value":
            ("REFUSE:DEV-LAW-INTAKE", "REFUSE:DEV-LAW-INTAKE"),
        "every_member/quantify-the-threshold-existence-over-the-cited-name":
            ("REFUSE:DEV-LAW-INTAKE", "REFUSE:DEV-LAW-INTAKE"),
        # [ADDED at EP-49C, 2026-09-08 — the two kinds the owner ruled (:3354/:3355). NEITHER
        # separates (both intakes are declared, so both ADMIT), so THE_SEPARATORS is unchanged and
        # prior_value remains the one kind that separates the threshold read. Both pairs DRIVEN.]
        "live_present/the-intake-name-is-present-in-its-declaration-set": ("ADMIT", "ADMIT"),
        "fold_threshold/count-the-declarations-of-the-intake-name": ("ADMIT", "ADMIT"),
    }

    #: THE SEPARATOR, NAMED. [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14. CAUSE: the owner's §5
    #: ruling landed the thirteenth kind, so the answer row's empty list was falsified by this
    #: pass's own move. ASSERTED: no live kind separates. SUPERSEDED: exactly one does, and it
    #: is named here rather than counted. REMAINS TRUE: none of the TWELVE separates, which is
    #: the establishment's substance and is asserted below over the twelve by name.]
    THE_SEPARATORS = ("prior_value/the-cited-declarations-threshold-IS-a-value",)

    def test_EXACTLY_THE_LICENSED_KIND_separates_the_two_declarations_on_the_threshold(self):
        """C8's answer, RE-DRIVEN AT W3a3 over thirteen kinds. [DOCUMENTED FLIP, 2026-08-14 —
        renamed from `test_NO_live_check_kind_separates_the_two_declarations_on_the_threshold_
        field`, because that name asserted the falsified half in its own words. CAUSE: the
        owner licensed the thirteenth kind and this pass landed it. ASSERTED: no live kind
        separates. SUPERSEDED: exactly one does. REMAINS TRUE: the whole body below, unchanged
        in mechanism — every candidate's pair compared against what it did, so the row still
        reds when a kind's behaviour moves AND when the separator set changes.]

        THE ROW STILL CANNOT PASS VACUOUSLY, and that matters more after the flip than before:
        the separator is compared as a NAMED SET rather than as a count, so a fourteenth kind
        that also separated would red here instead of being absorbed into a number."""
        driven = {}
        for label, params, checks, call_a, call_b in self._candidates():
            driven[label] = _verdicts(params, checks, call_a, call_b)
        self.assertEqual(driven, self.CANDIDATE_VERDICTS,
                         "a candidate's verdict pair moved since the W3a3 re-take")
        hits = tuple(sorted(l for l, pair in driven.items() if _separates(pair)))
        self.assertEqual(hits, self.THE_SEPARATORS,
                         "the separator set is %r. Exactly one kind is licensed to answer this "
                         "question (owner, 2026-08-14) and it is %r; anything else here is a "
                         "kind that gained reach nobody ruled on"
                         % (list(hits), THE_LICENSED_THIRTEENTH))
        # ------------------------------------------------------------------------------
        # AND EVERY SEPARATOR'S VERDICT MUST TRACK THE PROPERTY, OR `_separates` IS READING
        # A COINCIDENCE. [ADDED at EP-30-C1R, 2026-08-21. It is FOLDED INTO THIS ROW rather
        # than given its own because this pass's A1 pins COLLECTED_BY_LOADER at a
        # hand-computed 2952 and a new method moves it; the tension is named in the close.
        #
        # WHY IT EXISTS, and it is a finding this pass paid for rather than a formality:
        # `_separates` asks only whether the pair is (ADMIT, REFUSE). It cannot tell a
        # verdict DERIVED FROM THE RECORD from one HARDCODED BY THE CANDIDATE'S OWN
        # LITERALS. Until the owner's second act there was no kind that could do the
        # latter; `value_domain` reads a caller parameter against a set the row declares,
        # so a domain listing the block declaration by name separates the two while
        # reading nothing. THE DISCRIMINATOR IS FALSIFICATION: establish NET's threshold —
        # the property the walk is about — and a candidate that TRACKS it must stop
        # separating. `prior_value` does. A hardcoded domain does not.]
        established = copy.deepcopy(self.pack)
        _intake_payload(established, _NET_INTAKE)[_THRESHOLD_FIELD]["value"] = \
            _intake_payload(self.pack, _BLOCK_INTAKE)[_THRESHOLD_FIELD]["value"]
        self.assertIsNotNone(_intake_payload(established, _NET_INTAKE)[_THRESHOLD_FIELD]["value"],
                             "the mutation did not establish net's threshold, so the control "
                             "below is driven against the world it was meant to change")
        for label, params, checks, call_a, call_b in self._candidates():
            if label not in hits:
                continue
            self.assertFalse(
                _separates(_verdicts(params, checks, call_a, call_b, pack=established)),
                "%s still separates the two declarations in a world where BOTH thresholds "
                "ARE values, so its verdict does not track the property and this row's "
                "separator set is reading a coincidence rather than an answer" % label)

    def test_NOT_ONE_OF_THE_TWELVE_separates_which_is_what_the_owner_ruled_on(self):
        """THE ESTABLISHMENT'S SUBSTANCE, PRESERVED ACROSS THE FLIP AND ASSERTED OVER THE TWELVE
        BY NAME. The row above now permits a separator, so on its own it no longer says what the
        owner's decision rested on. This one does, and it is the row that would catch the event
        that would most quietly undermine that decision: one of the TWELVE starting to separate,
        which would mean the ruling bought a kind the estate did not need.

        [DOCUMENTED FLIP — EP-30-C1R, 2026-08-21, ruled at board `:1618`. CAUSE: RANGE.
        SUBJECT-ERA: HISTORICAL, and that is what decides the repair. This docstring used to
        end "The twelve are computed as the live vocabulary MINUS the one licensed kind, so a
        fourteenth arrival joins this row's population automatically rather than slipping past
        a literal list" — A DERIVATION THE NEXT LINE DEFEATED, since that line asserted the
        result was 12. The owner's SECOND act (`:1603`) landed two more kinds and the
        derivation went to fourteen while the assertion still said twelve. ASSERTED: none of
        the twelve pre-ruling kinds separates the two declarations. SUPERSEDED: nothing —
        the claim, its population and its literal are unchanged; only the SOURCE closes, from
        a live derivation to `THE_PRE_RULING_VOCABULARY`. REMAINS TRUE: everything the row
        protects, which is that the ruling did not buy a kind the estate already had.
        GIVEN UP: the automatic-arrival property — DELIBERATELY, because a kind arriving under
        a LATER act is not this row's subject and absorbing it silently is the defect.]"""
        twelve = THE_PRE_RULING_VOCABULARY
        self.assertEqual(len(twelve), 12, "the pre-ruling vocabulary is no longer twelve: %r"
                                         % (list(twelve),))
        driven = {}
        for label, params, checks, call_a, call_b in self._candidates():
            if all(c["check"] in twelve for c in checks):
                driven[label] = _verdicts(params, checks, call_a, call_b)
        self.assertEqual(len(driven), 17, "the twelve kinds' seventeen formulations are no "
                                          "longer seventeen: %d" % len(driven))
        self.assertEqual(sorted(l for l, pair in driven.items() if _separates(pair)), [],
                         "one of the TWELVE kinds the owner ruled against now separates the two "
                         "declarations, so the thirteenth kind may have been unnecessary and the "
                         "§5 record should be re-read against this")

    def test_the_walk_COVERED_every_kind_in_the_pinned_vocabulary(self):
        """A walk over eleven kinds answering about twelve is a filter that cannot match
        wearing a census. The coverage is computed from the candidates' own rows."""
        walked = {c["check"] for _, _, checks, _, _ in self._candidates() for c in checks}
        self.assertEqual(sorted(walked), sorted(THE_LIVE_CHECK_KINDS),
                         "the walk did not reach every kind: missing %r"
                         % (sorted(set(THE_LIVE_CHECK_KINDS) - walked),))

    # ------------------------------------------- the three facts the answer actually rests on
    def test_require_prior_compares_ONE_TOP_LEVEL_FIELD_against_a_CALLER_SUPPLIED_value(self):
        """FACT ONE, and it is why the nearest kind is not near enough. `require_prior`'s
        field is a LITERAL KEY, so a nested path finds nothing and refuses the class whose
        threshold IS a value; and its comparison value comes from a PARAMETER, so the caller
        supplies what the record is measured against."""
        blk = _intake_payload(self.pack, _BLOCK_INTAKE)[_THRESHOLD_FIELD]
        nested = _verdicts(
            {"intake": "required", "probe": "required"},
            [{"check": "require_prior", "action": "DECLARE-INTAKE",
              "field": _THRESHOLD_FIELD + ".value", "param": "probe",
              "cite": "DEV-LAW-INTAKE"}],
            {"intake": _BLOCK_INTAKE, "probe": blk["value"]},
            {"intake": _NET_INTAKE, "probe": blk["value"]})
        self.assertEqual(nested, ("REFUSE:DEV-LAW-INTAKE", "REFUSE:DEV-LAW-INTAKE"),
                         "a dotted field name now reaches inside a payload, which would "
                         "make the threshold read expressible")
        # and the same row over the TOP-LEVEL key admits both, which is the pair above
        # inverted by nothing but the dot.
        flat = _verdicts(
            {"intake": "required", "probe": "required"},
            [{"check": "require_prior", "action": "DECLARE-INTAKE", "field": _THRESHOLD_FIELD,
              "param": "probe", "cite": "DEV-LAW-INTAKE"}],
            {"intake": _BLOCK_INTAKE, "probe": blk},
            {"intake": _NET_INTAKE, "probe": blk})
        self.assertEqual(flat, ("ADMIT", "ADMIT"))

    def test_two_require_prior_rows_are_satisfied_by_TWO_DIFFERENT_RECORDS(self):
        """FACT TWO, and it is the decisive one. The obvious escape is to bind the record
        with one row and ask about its value with a second. It does not hold: each row is an
        INDEPENDENT existence scan, so the conjunction is satisfied by two different records
        — here the net call passes while citing net and carrying BLOCK's threshold dict, and
        nothing in the vocabulary requires the two rows to have met the same record."""
        blk = _intake_payload(self.pack, _BLOCK_INTAKE)[_THRESHOLD_FIELD]
        rp = "require_prior"
        pair = _verdicts(
            {"intake": "required", "probe": "required"},
            [{"check": rp, "action": "DECLARE-INTAKE", "field": "intake", "param": "intake",
              "cite": "DEV-LAW-INTAKE"},
             {"check": rp, "action": "DECLARE-INTAKE", "field": _THRESHOLD_FIELD,
              "param": "probe", "cite": "DEV-LAW-INTAKE"}],
            {"intake": _BLOCK_INTAKE, "probe": blk},
            {"intake": _NET_INTAKE, "probe": blk})
        self.assertEqual(pair, ("ADMIT", "ADMIT"),
                         "the two-row conjunction now separates, which would mean the rows "
                         "are being required to meet the same record")
        # THE CONTROL FOR THIS ROW: the first row alone DOES refuse an intake nobody
        # declared, so the conjunction's green above is two records agreeing and not a row
        # that never ran.
        alone = _verdicts(
            {"intake": "required"},
            [{"check": rp, "action": "DECLARE-INTAKE", "field": "intake", "param": "intake",
              "cite": "DEV-LAW-INTAKE"}],
            {"intake": _BLOCK_INTAKE}, {"intake": "device-intake@nobody-declared-this"})
        self.assertTrue(_separates(alone),
                        "the binding row cannot refuse an undeclared intake, so it never "
                        "ran and the conjunction above proves nothing")

    def test_ceiling_cannot_read_a_threshold_the_law_REQUIRES_to_be_structured(self):
        """FACT THREE, and it is a collision between two requirements rather than a gap.
        `ceiling` is the one kind that reads a numeric field out of prior records and
        compares it — but it SUMS that field, and this law's values may not be bare numbers
        (§A51), so the field it would read cannot be summed. Driven with a budget IN FORCE,
        because without one the kind returns early on `unlimited` and the row would pass
        without reaching its aggregate.

        THE REQUIREMENT IS READ FROM ITS TWO OWN HOMES AND FROM THE RECORD, never from one
        remembered phrase. A first draft of this row asserted the words "STRUCTURED FIELD AND
        NOT A BARE NUMBER" against the LAW's text, where they are not: they are DECLARE-
        INTAKE's, and the law states the same requirement in its own words. The filter was
        wrong about the document's form, which is the class this estate has now paid for four
        times, and it was caught by reading the failure rather than by trusting the phrase."""
        law = dict(self.w.views.active_rules()["DEV-LAW-INTAKE"])["text"]
        self.assertIn("names the calibration cell it derives from, that cell's POPULATION "
                      "and its BASIS", law,
                      "the LAW no longer requires a cell, a population and a basis per "
                      "value, so this collision may have dissolved and the kind is worth "
                      "re-driving")
        declare = self.w.views.op_definitions()["DECLARE-INTAKE"]["definition"]["description"]
        self.assertIn("STRUCTURED FIELD AND NOT A BARE NUMBER", declare,
                      "DECLARE-INTAKE no longer requires structured values")
        # AND THE FACT ITSELF, out of the shipped record rather than out of either sentence:
        # the field `ceiling` would aggregate is a mapping in both declarations.
        for name in (_BLOCK_INTAKE, _NET_INTAKE):
            self.assertIsInstance(_intake_payload(self.pack, name)[_THRESHOLD_FIELD], dict,
                                  "%s's threshold field is not structured, so `ceiling` "
                                  "might now be able to sum it" % name)
        budget = {"actor": "PC_RUNTIME", "action": "CREATE-RULE", "object": "W3A2-PROBE-BUDGET",
                  "rule_cited": "BOOT-INT",
                  "payload": {"rule_id": "W3A2-PROBE-BUDGET",
                              "policy_key": "intake.threshold." + _BLOCK_INTAKE, "value": 100,
                              "text": "planted so the ceiling row reaches its aggregate"}}
        checks = [{"check": "ceiling", "holder_param": "holder",
                   "policy_key_prefix": "intake.threshold.",
                   "aggregate_action": "DECLARE-INTAKE", "holder_field": "intake",
                   "key_param": "intake", "aggregate_field": _THRESHOLD_FIELD,
                   "removal_action": "RETIRE-INTAKE", "amount_param": "count",
                   "cite": "DEV-LAW-INTAKE"}]
        pair = _verdicts({"intake": "required", "count": "required", "holder": "required"},
                         checks,
                         {"intake": _BLOCK_INTAKE, "count": 10, "holder": _BLOCK_INTAKE},
                         {"intake": _NET_INTAKE, "count": 10, "holder": _NET_INTAKE},
                         (budget,))
        self.assertEqual(pair, ("ERROR:TypeError", "ADMIT"),
                         "the ceiling kind's behaviour over a structured field moved")

    def test_the_key_space_kinds_are_REFUSED_AT_THE_FOUNDING_DOOR_under_this_law(self):
        """FACT FOUR — the class question, which is the shape closest to "this name is of a
        kind meaning its threshold is established", is not merely unhelpful here: it is
        refused at the door, and the two refusals name two different reasons. Both are the
        installer's own words, so a later reader sees WHY rather than that it did not work.
        """
        for checks, needle in (
                ([{"check": "binding", "key_param": "intake", "require": "bound",
                   "cite": "DEV-LAW-INTAKE"}],
                 "the law whose acts bind and unbind names, and declares no binding"),
                ([{"check": "kind", "key_param": "intake", "require": "x",
                   "cite": "DEV-LAW-INTAKE"}],
                 "does not require that key to be bound")):
            with self.assertRaises(Exception) as ctx:
                _World(_mint_candidate(live_pack(), {"intake": "required"}, checks))
            self.assertIn(needle, str(ctx.exception),
                          "the founding door refused this formulation for a different "
                          "reason than it did at W3a2's establishment")

    def test_EXACTLY_THE_LICENSED_ROW_READS_INSIDE_A_RECORD_and_the_ROW_GRAMMAR_is_pinned(self):
        """FACT FIVE, and it closes a hole in this section's OWN pinning. `THE_LIVE_CHECK_KINDS`
        reds when a KIND arrives — but the other way this property could become expressible is
        an EXISTING kind gaining reach through a new declaration key, which that pin would not
        see. So the ROW GRAMMAR is pinned too: the whole set of keys any shipped check row uses.

        [DOCUMENTED FLIP — EP-29 W3a3, 2026-08-14. Renamed from
        `test_NO_SHIPPED_CHECK_ROW_READS_INSIDE_A_RECORD_and_the_ROW_GRAMMAR_is_pinned`. CAUSE:
        this pass's own move. The estate's law was searched for a nested-path precedent before
        the vocabulary was called short and there was NONE; the owner then licensed one, and
        this pass shipped it. ASSERTED: no shipped check row addresses a nested path; the
        grammar is 31 keys. SUPERSEDED: EXACTLY ONE row does and it is named; the grammar is 32.
        REMAINS TRUE: both pins' function, and the second is unchanged in mechanism.

        AND THE FLIP MAKES THIS ROW STRONGER RATHER THAN WEAKER, which is why it was re-taken
        this way instead of being scoped or era-pinned. It was an ABSENCE test — a count of zero
        in a growing file, the shape this estate has already watched invert. It is now a NAMED
        ROW: the one licensed reader is named, so a SECOND row reading inside a record reds here
        by name. That is the licence bound made mechanical — "one kind was ruled, one kind
        lands" — rather than a promise in a dispatch note.]"""
        rows = [(r["payload"]["name"], c) for st in self.pack["steps"] for r in st["records"]
                if r.get("action") == "CREATE-OP"
                for c in (r["payload"]["definition"].get("checks") or [])]
        self.assertGreater(len(rows), 30, "the check-row census found almost nothing, so its "
                                          "answers below are about an empty population")
        # THE POSITIVE CONTROL FOR THE CENSUS, first: it finds a known-present case.
        self.assertEqual(sorted(n for n, c in rows if c.get("action") == "DECLARE-IO-WINDOW"),
                         ["DECLARE-INTAKE", "DEVICE-IO-WINDOW-WRITE"],
                         "the census cannot find check rows it is known to contain, so its "
                         "answers below say nothing")
        addressed = sorted((n, c["check"]) for n, c in rows
                           if any(isinstance(v, str) and "." in v for k, v in c.items()
                                  if k not in ("message", "cite", "cite_cycle", "cite_missing",
                                               "cite_correlation")))
        self.assertEqual(addressed, [("DEVICE-INTAKE-COVER", THE_LICENSED_THIRTEENTH)],
                         "the shipped rows that address a nested path are %r. EXACTLY ONE kind "
                         "was licensed to read inside a record (owner, 2026-08-14) and exactly "
                         "one operation carries it; a second reader here is reach nobody ruled "
                         "on, whichever kind it wears" % (addressed,))
        self.assertEqual(
            sorted({k for _, c in rows for k in c}), THE_CHECK_ROW_GRAMMAR,
            "the check-row grammar moved. This walk's answer is about the grammar above; a new "
            "declaration key can give an EXISTING kind reach the walk never tested, which is "
            "the event the kind pin cannot see")

    def test_the_GRAMMAR_grew_by_EXACTLY_the_licensed_kinds_one_new_key(self):
        """THE LICENCE BOUND AT THE GRAMMAR LAYER, and it is a different question from the row
        above: that one asks WHO reads inside a record, this one asks HOW MUCH NEW VOCABULARY the
        licence spent. One kind was ruled; the cheapest honest implementation of it adds ONE
        declaration key, and every other key it speaks is grammar the twelve already spoke.

        A kind arriving with four new keys would pass every row in this section and would still
        be a wider constitutional change than the one that was ruled on. This row is where that
        shows up, and its expectation is a HAND-COMPUTED literal: 31 keys at the era, one key
        added, 32 now.

        [DOCUMENTED FLIP — EP-30-C1R, 2026-08-21, a §A57 RANGE CLOSURE. CAUSE: RANGE.
        SUBJECT-ERA: HISTORICAL — the subject is HOW MUCH VOCABULARY W3a3'S LICENCE SPENT,
        a finished question, so an era-pin is the lawful repair. The row was HALF-PINNED:
        `era` read W3a3's own before-commit and `now` read the LIVE tree, which made it a
        claim about every key that has arrived since, forever. EP-30-C1's two kinds added
        five keys under a LATER act (`:1603`) and reddened it. ASSERTED: 31 at the era, 32
        after the licence, the difference exactly ["value_field"]. SUPERSEDED: nothing —
        every literal and the whole claim are unchanged; only the AFTER end closes, from the
        live tree to W3b's pre-write commit, where the grammar is 32 (driven at this hand).
        GIVEN UP: nothing. The LIVE grammar is pinned, at 37 and by name, by
        `THE_CHECK_ROW_GRAMMAR` and the row above — which is where that population belongs.]"""
        era = era_pin.pack_at(W3A3_BEFORE_COMMIT)
        keys_at = lambda pack: sorted({k for st in pack["steps"] for r in st["records"]
                                       if r.get("action") == "CREATE-OP"
                                       for c in (r["payload"]["definition"].get("checks") or [])
                                       for k in c})
        before, now = keys_at(era), keys_at(era_pin.pack_at(W3B_PRE_WRITE_COMMIT))
        self.assertEqual(len(before), 31, "the era's grammar is not the 31 keys W3a2 pinned")
        self.assertEqual(len(now), 32, "the licensed era's grammar is not 31 + 1")
        self.assertEqual(sorted(set(now) - set(before)), ["value_field"])
        self.assertEqual(sorted(set(before) - set(now)), [],
                         "this pass removed a declaration key, which no licence covers")

    def test_the_property_IS_computable_from_the_record_and_only_the_VOCABULARY_cannot_say_it(self):
        """THE ROW THAT DECIDES WHAT THE STOP IS ABOUT, and it is the one a reader of the §5
        question needs most. A walk that separates nothing has two readings: the property is
        unsatisfiable, or the vocabulary cannot express a property that is perfectly real.
        Only the second licenses an owner question about the vocabulary.

        Read straight off the two shipped records, in ordinary Python, with no engine and no
        check row: the property SEPARATES THEM CLEANLY. So there is something to say, and
        the twelve kinds are what cannot say it."""
        def threshold_is_a_value(payload):
            return payload.get(_THRESHOLD_FIELD, {}).get("value") is not None

        blk = _intake_payload(self.pack, _BLOCK_INTAKE)
        net = _intake_payload(self.pack, _NET_INTAKE)
        self.assertTrue(threshold_is_a_value(blk),
                        "the property does not hold of the class it must admit")
        self.assertFalse(threshold_is_a_value(net),
                         "the property holds of the class it must refuse, so it is not the "
                         "property C7 needs")
        # AND THE PREDICATE IS SHOWN ABLE TO SAY NO TO A CLASS THAT DOES CARRY A VALUE —
        # otherwise it separates by returning False for everything it is handed.
        self.assertFalse(threshold_is_a_value({}), "the predicate answers about an absent field")
        self.assertTrue(threshold_is_a_value({_THRESHOLD_FIELD: {"value": 1}}))

    # -------------------------------------------------------------------------- §A57
    def test_the_SWEEP_population_is_empty_BY_CONSTRUCTION_and_not_by_a_search(self):
        """§A57 sweeps every version, diff and era-pinned row A FOUNDING PASS'S OWN MOVE
        FALSIFIES. W3a2 moved no founding byte — the movement stopped before its landing —
        so the population is empty at its root, and this section authors no version constant
        that would join a LATER move's population either.

        WALKED OVER THE AST AND NOT GREPPED FOR A LITERAL, on this file's own precedent: a
        grep for the current version string matches itself the moment it is written."""
        semver = re.compile(r"^\d+\.\d+\.\d+$")
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        mine = [n for n in tree.body if isinstance(n, ast.ClassDef)
                and n.name == "TheThresholdReadIsNotExpressibleInTheLiveVocabulary"]
        self.assertEqual(len(mine), 1, "the class walk did not find this section")
        found = [c.value for n in mine for c in ast.walk(n)
                 if isinstance(c, ast.Constant) and isinstance(c.value, str)
                 and semver.match(c.value)]
        self.assertEqual(found, [],
                         "a W3a2 row carries a version constant, so it joins the next "
                         "founding move's sweep population and must be era-pinned instead")
        planted = ast.parse('class TheW3a2Planted:\n    V = "1.99.0"\n')
        self.assertTrue([c.value for c in ast.walk(planted)
                         if isinstance(c, ast.Constant) and isinstance(c.value, str)
                         and semver.match(c.value)],
                        "the detector cannot find a version constant that IS there, so its "
                        "empty answer above says nothing")


# =======================================================================================
# EP-29 W3a3 — THE THIRTEENTH CHECK KIND AND THE INTAKE OPERATION, ONE LAW PASS (2026-08-14)
#
# THE OWNER RULED THE §5 GATE on 2026-08-14, by explicit act: the check vocabulary grows TWELVE
# TO THIRTEEN. The evidence was the establishment above — seventeen formulations across all
# twelve live kinds, zero separating the two shipped intake declarations, both positive controls
# separating, and the property separating them cleanly in plain code. This section is what
# landed on that licence, and it is a LAW PASS: the founding MOVES, and byte-unchanged would be
# the failing outcome rather than the safe one.
#
# THE LICENCE IS A NUMBER AND NOT A PROMISE, so the bound is mechanical here rather than
# asserted in prose. ONE kind was ruled and ONE lands: the vocabulary census moves by exactly
# that kind against the era, the check-row grammar grows by exactly one declaration key, and the
# nested-path census names its single reader instead of counting to one. A second kind riding
# this licence reds three separate rows, and an undocumented one reds the estate's own
# comparator.
#
# WHY THE EVALUATOR LIVES IN `src/kernel/opdefs.py` — DERIVED AT THE WALK AND NEVER CHOSEN. The
# dispatch clause names the site as "where the twelve live kinds' evaluators already live", and
# `TheThirteenthKindsSiteWasDerivedFromItsSiblings` below quotes that site out of the module
# rather than out of a dispatch note: all twelve are dispatched from one `elif` chain in one
# file, so the thirteenth goes beside them and no builder chose a name.
# =======================================================================================

import importlib.util                                            # noqa: E402

#: THE OPERATION THIS PASS MINTS, and the two operations that then cite the intake law. Named as
#: tuples so a change shows up as a set difference with both directions printed.
THE_INTAKE_OP = "DEVICE-INTAKE-COVER"
OPS_UNDER_THE_INTAKE_LAW = ("DECLARE-INTAKE", THE_INTAKE_OP)

#: What the covering record must CARRY, keyed to the law's own five phrases (W3b's
#: `COVERING_RECORD_CARRIERS`, read out of the law record). This maps each phrase to the
#: parameter that carries it, so a carrier the operation drops is a KeyError-shaped red rather
#: than a sentence nobody re-read. The law's citation is the definition's `law_cited` and the
#: declaration's name is `intake`, which is why one phrase maps to a pair.
CARRIER_TO_PARAM = {
    "the COUNT of arrivals covered": ("arrival_count",),
    "the BYTE TOTAL over them": ("byte_total",),
    "the device the arrivals were attributed to": ("device",),
    "the window they were admitted under by name": ("window",),
    "this law's citation together with the intake declaration's name": ("intake",),
}

#: The two shipped classes and what this law says about each, for the fail-closed rows. Block's
#: cap is CONFIRMED at :712 and net's is WITHDRAWN — the pair is the whole subject, because one
#: check over one law-data field must produce two different verdicts.
_ADMITTED, _REFUSED = ("device-intake@block", "device-io@block"), ("device-intake@net", "device-io@net")


def _cover_world(test):
    """A booted world with custody in place for both validation devices, and THE CUSTODY PROVEN
    LIVE BEFORE ANY REFUSAL IS READ (item-21 non-vacuity). A refusal over a dead bind is the
    empty world passing, and it reads identically on the page."""
    w = _World()
    w.call("REGISTER-CAPABILITY", driver="drv-a", device_class="block", capabilities=["irq:11"])
    for dev in ("virtio1", "virtio0"):
        rec = w.call("BIND-DEVICE", device=dev, driver="drv-a")
        test.assertEqual(rec["action"], "BIND-DEVICE")
    from subsystems.devices import DevicesView
    test.assertEqual(DevicesView(w.store).bindings(), {"virtio1": "drv-a", "virtio0": "drv-a"})
    return w


def _cover(w, intake, window, device, arrival_count=64, byte_total=262144):
    """One DEVICE-INTAKE-COVER call, returning ("ADMIT", record) or ("REFUSE:<rule>", record).
    THE VERDICT IS WHAT THE GATE DID and the RECORD is what it appended — never a reading of
    either. The refusal record is fetched rather than inferred, because "refused and recorded"
    is two claims and this estate has a rule about the second."""
    before = len(w.store.all())
    try:
        rec = w.call(THE_INTAKE_OP, intake=intake, window=window, device=device,
                     arrival_count=arrival_count, byte_total=byte_total)
        return "ADMIT", rec
    except OpError as exc:
        appended = list(w.store.all())[before:]
        return "REFUSE:%s" % exc.rule, (appended[0] if appended else None)


class TheThirteenthKindsSiteWasDerivedFromItsSiblings(unittest.TestCase):
    """C8b's fence half, DRIVEN. The dispatch put the evaluator "at the site the twelve live
    kinds' evaluators already live" and made that membership DERIVED and VERIFIED at the walk,
    never chosen — so the walk is a row and not a sentence in a report.

    POPULATION: the thirteen kinds of `opdefs.OP_CHECKS` at this tree.
    BASIS: the engine module's own AST, walked for the dispatch comparison each kind is run
    from. Never a grep for a name and never this file's belief about where anything lives."""

    def _dispatch_sites(self):
        """{kind: lineno} for every kind dispatched by a `c["check"] == "<literal>"` comparison.
        THE SAME STRUCTURE `tests/test_ep28g_w2.py`'s enumerator reads, re-derived here for one
        reason only: that file asks whether every declared kind CAN RUN, and this one asks WHERE
        the twelve are so the thirteenth's site is established rather than assumed."""
        src = open(os.path.join(REPO, "src", "kernel", "opdefs.py"), encoding="utf-8").read()
        sites = {}
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Compare) and node.comparators:
                left, right = node.left, node.comparators[0]
                if (isinstance(left, ast.Subscript)
                        and isinstance(getattr(left, "slice", None), ast.Constant)
                        and left.slice.value == "check"
                        and isinstance(right, ast.Constant)):
                    sites.setdefault(right.value, node.lineno)
        return sites

    def test_ALL_TWELVE_prior_kinds_are_dispatched_from_ONE_file_which_is_the_site(self):
        """THE DERIVATION ITSELF. The site is not named in this row — it is COMPUTED from where
        the siblings are, and only then compared to the one file the pass wrote.

        [DOCUMENTED FLIP — EP-30-C1R, 2026-08-21, ruled at board `:1618` CLAIM 5. CAUSE:
        RANGE. SUBJECT-ERA: HISTORICAL — the subject is THE PRIOR kinds, the set the
        thirteenth had to be dispatched beside. Same repair as its sibling above and for the
        same reason: the population is read from `THE_PRE_RULING_VOCABULARY` instead of
        derived from a live set that has since moved under a different act.]"""
        sites = self._dispatch_sites()
        twelve = list(THE_PRE_RULING_VOCABULARY)
        missing = [k for k in twelve if k not in sites]
        self.assertEqual(missing, [], "a prior kind is dispatched nowhere, so the site the "
                                      "thirteenth derives from is not established: %r" % missing)
        self.assertEqual(len(twelve), 12)

    def test_the_THIRTEENTH_is_dispatched_BESIDE_them_and_from_the_same_chain(self):
        """The membership, verified. `beside` is asserted as ADJACENCY IN THE SAME CHAIN and not
        merely as same-file: the new site sits after the last of the twelve with no other
        dispatch between, which is what "beside its siblings" means structurally.

        [DOCUMENTED FLIP — EP-30-C1R, 2026-08-21, board `:1618`. CAUSE: RANGE. SUBJECT-ERA:
        HISTORICAL — the subject is where W3a3 put the thirteenth RELATIVE TO THE TWELVE IT
        JOINED, which is finished. Left deriving from the live set it would have gone red for
        the right reason at the wrong row: `value_domain` and `live_slot` are dispatched AFTER
        `prior_value`, so a live population would have made this row report that "the
        thirteenth is dispatched before its siblings" about kinds that are not its siblings.]"""
        sites = self._dispatch_sites()
        self.assertIn(THE_LICENSED_THIRTEENTH, sites,
                      "the licensed kind is declared and dispatched nowhere — a check kind that "
                      "cannot run, which is the one shape the enumerator in test_ep28g_w2 reds")
        twelve = sorted(sites[k] for k in THE_PRE_RULING_VOCABULARY)
        mine = sites[THE_LICENSED_THIRTEENTH]
        self.assertGreater(mine, twelve[-1], "the thirteenth is dispatched before its siblings")
        between = [k for k, ln in sites.items() if twelve[-1] < ln < mine]
        self.assertEqual(between, [], "something is dispatched between the twelve and the "
                                      "thirteenth: %r" % between)

    def test_the_site_walk_CAN_FAIL_over_a_module_that_dispatches_elsewhere(self):
        """THE POSITIVE CONTROL, pointed at a known-present case rather than at nothing: the
        walker is shown to find a dispatch in synthetic source and to find none where there is
        none. Without it the two rows above are a description of `opdefs.py` wearing a test's
        clothes."""
        found = {}
        for node in ast.walk(ast.parse('if c["check"] == "planted_kind":\n    pass\n')):
            if isinstance(node, ast.Compare) and node.comparators:
                left, right = node.left, node.comparators[0]
                if (isinstance(left, ast.Subscript)
                        and isinstance(getattr(left, "slice", None), ast.Constant)
                        and left.slice.value == "check"
                        and isinstance(right, ast.Constant)):
                    found[right.value] = node.lineno
        self.assertEqual(sorted(found), ["planted_kind"],
                         "the walker cannot find a dispatch that IS there")
        self.assertEqual(
            [n for n in ast.walk(ast.parse('if c["other"] == "x":\n    pass\n'))
             if isinstance(n, ast.Compare) and isinstance(n.left, ast.Subscript)
             and n.left.slice.value == "check"], [],
            "the walker matches a comparison that is not a check dispatch")


class TheVocabularyGrewBY_EXACTLY_THE_ONE_RULED_KIND(unittest.TestCase):
    """C8b's census: `OP_CHECKS` changes by EXACTLY the one ruled kind, and the design/28 §5 row
    lands in the SAME PASS so the vocabulary census stays green.

    POPULATION: the check vocabulary at two trees — the 1.23.0 era and this one.
    BASIS: the engine's own tuple read by AST through `tools/docmap/checkvocab.py`, the estate's
    one comparator, and design/28 §5's table read by the same tool. Never a count typed here."""

    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "govos_w3a3_checkvocab", os.path.join(REPO, "tools", "docmap", "checkvocab.py"))
        self.cv = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.cv)

    def test_the_COMPARATORS_OWN_CONTROL_passes_before_any_of_its_answers_is_read(self):
        """The tool's own positive control, run FIRST. Every finding it reports is an ABSENCE, so
        a structurally broken comparator returns exactly the clean result a healthy one returns.
        A zero not backed by this row is uninterpretable and is never reported as a count."""
        ok, detail = self.cv.positive_control()
        self.assertTrue(ok, "the comparator's own control failed: %s" % detail)

    def test_the_vocabulary_moved_by_EXACTLY_the_one_ruled_kind(self):
        """THE LICENCE AS ARITHMETIC AND AS A NAMED SET, both, because they fail differently: a
        count catches a second arrival, and the named difference catches a SWAP that keeps the
        count. Expectations are HAND-COMPUTED literals — twelve at the era, thirteen now.

        [DOCUMENTED FLIP — EP-30-C1R, 2026-08-21, a §A57 RANGE CLOSURE. CAUSE: RANGE.
        SUBJECT-ERA: HISTORICAL — the subject is W3a3'S OWN MOVE, one kind against the twelve
        it joined, which is finished. The row was HALF-PINNED, `era` closed and `now` LIVE, so
        its claim drifted to "whatever OP_CHECKS holds later"; the owner's SECOND act
        (`:1603`) landed two more kinds and reddened it. ASSERTED: twelve at the era,
        thirteen after, the difference exactly the licensed kind. SUPERSEDED: nothing — every
        literal, the arithmetic and the named difference are unchanged; only the AFTER end
        closes, from the live tree to W3b's pre-write commit, read through THE SAME
        COMPARATOR. GIVEN UP: nothing. The LIVE vocabulary is asserted, at fifteen and by
        name, by `THE_LIVE_CHECK_KINDS` and the pinned-population row that watches it.]"""
        era = self.cv.check_kinds_from_source(
            era_pin.text_at(W3A3_BEFORE_COMMIT, "src/kernel/opdefs.py"))
        now = self.cv.check_kinds_from_source(
            era_pin.text_at(W3B_PRE_WRITE_COMMIT, "src/kernel/opdefs.py"))
        self.assertEqual(len(era), 12, "the era's vocabulary is not the twelve the owner ruled "
                                       "on: %r" % (list(era),))
        self.assertEqual(len(now), 13, "the licensed era's vocabulary is not twelve plus one: %r"
                                       % (list(now),))
        self.assertEqual(sorted(set(now) - set(era)), [THE_LICENSED_THIRTEENTH],
                         "the kinds this pass added are %r — one kind was ruled and one lands"
                         % (sorted(set(now) - set(era)),))
        self.assertEqual(sorted(set(era) - set(now)), [],
                         "this pass RETIRED a check kind, which no licence covers and which is "
                         "its own design amendment")
        self.assertEqual(tuple(now), THE_PRE_RULING_VOCABULARY + (THE_LICENSED_THIRTEENTH,),
                         "the licensed era's vocabulary and this file's pin disagree")

    def test_design28_S5_carries_the_new_kinds_ROW_and_the_two_sides_do_not_diverge(self):
        """'An undocumented kind REDS' — the vocabulary census's own ground, and the reason the
        row lands in the SAME pass as the kind. Both directions, through the estate's comparator
        rather than by reading the table."""
        src = open(self.cv.OPDEFS, encoding="utf-8").read()
        doc = open(self.cv.DESIGN28, encoding="utf-8").read()
        undocumented, unbacked = self.cv.defect4(src, doc)
        self.assertEqual(undocumented, [], "check kinds live in OP_CHECKS with no row in "
                                           "design/28 §5: %r" % (undocumented,))
        self.assertEqual(unbacked, [], "design/28 §5 names a kind the engine does not have: %r"
                                       % (unbacked,))
        rows = dict(self.cv.check_rows_from_doc(doc))
        self.assertIn(THE_LICENSED_THIRTEENTH, rows,
                      "the licensed kind has no row in the table that is its law")
        row = rows[THE_LICENSED_THIRTEENTH]
        self.assertIn("2026-08-14", row, "the row does not date the owner's act")
        self.assertFalse(self.cv.has_legitimate_absence(row),
                         "the new kind's row carries a legitimate-ABSENCE marker, which would "
                         "switch the comparator off for the very kind it was added to police")

    def test_the_reconciliation_carries_no_remainder_at_the_NEW_size(self):
        """A count is the weaker check wearing the stronger one's name, so state the arithmetic.
        HAND-COMPUTED: 17 live kinds + 2 legitimate absences = 19 rows.

        [DOCUMENTED FLIP — EP-30-C1R, 2026-08-21. CAUSE: RANGE. SUBJECT-ERA: LIVE — this row
        reconciles the LIVE engine against the LIVE table, so it RE-DERIVES and is never
        era-pinned; an era-pin would reconcile a historical engine against today's table and
        go green while asserting nothing. ASSERTED: (13, 2, 15). SUPERSEDED: (15, 2, 17).
        REMAINS TRUE: the claim, which is the ARITHMETIC IDENTITY — live kinds plus legitimate
        absences equals table rows, with no remainder in either direction — unchanged in
        mechanism and in what it reds on. GIVEN UP: nothing. RE-POPULATION IS NOT WEAKENING.]

        [DOCUMENTED FLIP — EP-30-K2R, 2026-08-27, under the `:2304` ownership ruling. CAUSE:
        RANGE. SUBJECT-ERA: LIVE, unchanged and for the reason above. ASSERTED: (17, 2, 19).
        SUPERSEDED: (15, 2, 17).

        THE RE-PIN IS MADE ONCE, TO THE POPULATION THAT EXISTS AFTER THE LAST MOVE, AND THAT
        IS WHY IT IS THIS UNIT'S. The vocabulary went 15 -> 17 by TWO moves — EP-30-K1's
        `bound_field` and EP-30-K2's `every_member` — so this row was JOINTLY falsified and
        neither move alone explains the value it now reads. A re-pin by the earlier mover
        would have authored a row already false on the day it landed.

        THE THREE MEMBERS WERE EACH READ FROM A COMMAND AND NONE WAS ADJUSTED UNTIL THEY SUM.
        Driven through the estate's one comparator before this literal was typed, and the
        arithmetic closed on the first reading: 17 + 2 = 19, no remainder in either direction.
        The drive is quoted in planning/evidence/EP-30-K2R/A7-the-population-pins-RE-DRIVEN.txt
        AHEAD of this constant, so the record shows the pin FOLLOWING the walk. A triple whose
        members were chosen to sum is a check with no subject.

        REMAINS TRUE: the claim and the mechanism, whole. GIVEN UP: nothing. The row still
        reds on any movement of either side — §4's R5 plants an eighteenth kind and drives it
        red rather than promising it would.]

        [DOCUMENTED FLIP — EP-49C, 2026-09-08. CAUSE: RANGE. SUBJECT-ERA: LIVE, unchanged and for
        the reason in the first note. ASSERTED: (19, 2, 21). SUPERSEDED: (17, 2, 19). EP-49C's
        AMEND-OP added two CODE-BORN kinds — `live_present`, `fold_threshold` — and the architect
        authored their two rows in design/28 §5, so both sides moved by two: 19 live kinds + 2
        legitimate absences = 21 table rows. THE THREE MEMBERS WERE EACH READ FROM A COMMAND AND
        NONE ADJUSTED UNTIL THEY SUM (planning/evidence/EP-49C/A7-count-pin-companions-RE-DRIVEN.txt,
        19 + 2 = 21, remainder 0), quoted ahead of this literal. REMAINS TRUE: the arithmetic
        identity and the mechanism, whole. GIVEN UP: nothing.]"""
        src = open(self.cv.OPDEFS, encoding="utf-8").read()
        doc = open(self.cv.DESIGN28, encoding="utf-8").read()
        kinds = self.cv.check_kinds_from_source(src)
        rows = self.cv.check_rows_from_doc(doc)
        legitimate = [n for n, t in rows if self.cv.has_legitimate_absence(t)]
        self.assertEqual(sorted(legitimate), ["attenuation", "due"],
                         "the legitimate absences moved, and each is a row that switches the "
                         "comparator off for itself")
        self.assertEqual((len(kinds), len(legitimate), len(rows)), (19, 2, 21),
                         "live kinds %d + legitimate absences %d != table rows %d"
                         % (len(kinds), len(legitimate), len(rows)))

    def test_A_SECOND_KIND_RIDING_THE_LICENCE_REDS(self):
        """C8b's first red world, DRIVEN and not promised. A second kind planted into the engine
        source is reported UNDOCUMENTED by the comparator against the real table — so the estate
        already reds on the act the licence forbids, and this row proves the mechanism rather
        than restating the rule.

        THE PLANT IS AN ADDITION TO THE LIVE SOURCE IN MEMORY, never to the file: the subject is
        the comparator's behaviour, and writing a second kind to disk to test the guard against
        second kinds would be the act the guard exists to catch.

        [DOCUMENTED FLIP — EP-30-C1R, 2026-08-21. CAUSE: CONTROL. SUBJECT-ERA: LIVE. The plant
        was a source substitution anchored on `'"contains", "prior_value")'`, the tail
        `OP_CHECKS` had when this row was written. EP-30-C1 appended two kinds, so the anchor
        matched nothing and the row's OWN guard fired — "the plant did not land, so this row
        tests nothing". THE ROW COULD STILL FAIL; IT COULD NO LONGER PLANT, which is the
        sharper half and is why the cause is CONTROL and not RANGE. ASSERTED: a second kind
        beside the licensed one is reported undocumented. SUPERSEDED: nothing. REMAINS TRUE:
        the whole claim and the whole mechanism, over a moved source. GIVEN UP: nothing.
        THE ANCHOR IS NOW THE TUPLE'S CLOSING PAREN AFTER ITS CURRENT LAST MEMBER, and the
        row's own "the plant did not land" guard is what will announce the next move — it
        already did its job once, and it is left exactly as it is.]

        [RE-ANCHORED — EP-30-K2R, 2026-08-27, under the `:2304` ownership ruling. CAUSE:
        CONTROL, the same cause and the same shape as the flip above. SUBJECT-ERA: LIVE.

        IT ANNOUNCED THE NEXT MOVE EXACTLY AS THAT NOTE PREDICTED IT WOULD. Two kinds landed
        after the anchor was last set — EP-30-K1's `bound_field` and EP-30-K2's
        `every_member` — the anchor matched nothing, and the row redded on its own guard
        rather than on its subject. THAT RED WAS THE SENTINEL WORKING. The repair is a
        RE-ANCHOR to the live tail and it belongs to the LAST mover, because an earlier
        re-anchor would have pointed at a tail that had already moved again.

        THE ANCHOR IS A LITERAL ON PURPOSE AND MUST STAY ONE. Deriving it from the engine's
        own tuple would make it match forever, and a plant that always lands is a control
        that can no longer report that its subject moved — which is this row's whole function.
        §4's R5 is the row that holds this repair to it: an eighteenth kind is planted into a
        copy of the source and THIS ROW MUST RED. A re-anchor that survives that plant has
        deleted the sentinel and kept its name.

        THE GUARD NOW NAMES THE MOVEMENT. It previously said only that the plant had not
        landed, which is true and leaves the reader to find out what changed; it now reports
        the tail it expected against the tail the source carries, so the next move is legible
        from the failure line alone. ASSERTED: unchanged — a second kind beside the licensed
        one is reported undocumented. SUPERSEDED: the anchor text only. GIVEN UP: nothing.]

        [RE-ANCHORED — EP-49C, 2026-09-08. CAUSE: CONTROL, the same shape as both notes above.
        SUBJECT-ERA: LIVE. It announced the move exactly as the K2R note said it would: EP-49C's
        AMEND-OP added two CODE-BORN kinds — `live_present` and `fold_threshold` — the anchor
        `"bound_field", "every_member")` matched nothing, and the row redded on its own "the
        plant did not land" guard rather than on its subject. THAT RED WAS THE SENTINEL WORKING.
        The re-anchor is to the live tail read from a command (tail[-2:] = ('live_present',
        'fold_threshold'), planning/evidence/EP-49C/A7-count-pin-companions-RE-DRIVEN.txt) and it
        belongs to EP-49C as the last mover. NOT WIDENED — the anchor stays a two-member literal
        so §4's R5 eighteenth-kind plant still reds. ASSERTED: unchanged. SUPERSEDED: the anchor
        text only. GIVEN UP: nothing.]"""
        src = open(self.cv.OPDEFS, encoding="utf-8").read()
        doc = open(self.cv.DESIGN28, encoding="utf-8").read()
        anchor = '"live_present", "fold_threshold")'
        planted = src.replace(anchor, '"live_present", "fold_threshold", "planted_second_kind")', 1)
        if planted == src:
            # NOT assertNotEqual, and the reason is this row's own legibility. That form prints
            # BOTH operands on failure — two copies of the engine source, some three hundred
            # kilobytes, with the sentence that says what moved buried at the end of it. THE
            # REPORT IS THE ONLY THING THIS GUARD PRODUCES, so it is printed and nothing else.
            self.fail("the plant did not land, so this row tests nothing — the check "
                      "vocabulary's tail has MOVED away from the anchor this row pins. "
                      "Anchored on %s; the source this row READ ends %r. RE-DRIVE the walk "
                      "and RE-ANCHOR to the live tail; do not widen the anchor until it "
                      "matches again, which would silence this report permanently."
                      % (anchor, tuple(self.cv.check_kinds_from_source(src))[-2:]))
        undocumented, _unbacked = self.cv.defect4(planted, doc)
        self.assertEqual(undocumented, ["planted_second_kind"],
                         "a second check kind added beside the licensed one is not reported as "
                         "an undocumented addition, so the licence bound has no instrument")

    def test_AN_UNDOCUMENTED_KIND_REDS_even_when_it_is_THE_LICENSED_ONE(self):
        """C8b's second red world, and it is pointed at THIS pass rather than at a hypothetical:
        the licensed kind's own row is removed from the table in memory, and the comparator must
        report the licensed kind undocumented. Without this the green above cannot distinguish
        'the row is there' from 'the comparator never looked at this kind'."""
        src = open(self.cv.OPDEFS, encoding="utf-8").read()
        doc = open(self.cv.DESIGN28, encoding="utf-8").read()
        rows = dict(self.cv.check_rows_from_doc(doc))
        stripped = doc.replace(rows[THE_LICENSED_THIRTEENTH] + "\n", "", 1)
        self.assertNotEqual(stripped, doc, "the row was not removed, so this row tests nothing")
        undocumented, _unbacked = self.cv.defect4(src, stripped)
        self.assertEqual(undocumented, [THE_LICENSED_THIRTEENTH],
                         "removing the licensed kind's own row does not red the comparator, so "
                         "its presence above proves nothing about this kind")


class ThePriorValueKindReadsTheRecordItLocated(unittest.TestCase):
    """THE THIRTEENTH KIND'S WHOLE ADDITION TO THE VOCABULARY, driven: the locate and the read
    MEET THE SAME RECORD. Everything else it does, the twelve could already do.

    POPULATION: the two shipped intake declarations, which were made by ONE op under ONE law at
    ONE grade and differ in exactly the field the kind reads.
    BASIS: candidate ops minted into the live pack through the ORDINARY door and CALLED at a
    booted world, exactly as the establishment above took its answer. A verdict is the gate's."""

    def setUp(self):
        self.pack = live_pack()

    def _row(self, **over):
        row = {"check": "prior_value", "action": "DECLARE-INTAKE", "field": "intake",
               "param": "intake", "value_field": _THRESHOLD_FIELD + ".value",
               "require": "established", "cite": "DEV-LAW-INTAKE"}
        row.update(over)
        return [row]

    def _drive(self, checks, params=None, a=None, b=None):
        params = params or {"intake": "required"}
        return _verdicts(params, checks,
                         a or {"intake": _BLOCK_INTAKE}, b or {"intake": _NET_INTAKE})

    def test_the_kind_SEPARATES_the_two_declarations_which_is_why_it_was_licensed(self):
        pair = self._drive(self._row())
        self.assertTrue(_separates(pair),
                        "the licensed kind does not admit the class whose threshold IS a value "
                        "and refuse the class whose threshold is not: %r" % (pair,))
        self.assertEqual(pair, ("ADMIT", "REFUSE:DEV-LAW-INTAKE"))

    def test_INVERTING_the_requirement_INVERTS_the_verdicts_which_no_inert_row_can_do(self):
        """§7.1's fourth disguise, pointed at my own kind: an assertion the data cannot move is
        a sentence with a colon in it. `require: unestablished` must produce the MIRROR of the
        row above from the same world and the same records — so the verdict is a function of the
        law-data and of the requirement, and of nothing incidental."""
        pair = self._drive(self._row(require="unestablished"))
        self.assertEqual(pair, ("REFUSE:DEV-LAW-INTAKE", "ADMIT"),
                         "the requirement does not move the verdict, so the row above may be "
                         "separating on something other than what it asks: %r" % (pair,))

    def test_TWO_require_prior_ROWS_STILL_DO_NOT_SEPARATE_which_is_the_contrast(self):
        """THE DECISIVE CONTRAST, driven BESIDE the kind rather than quoted from the
        establishment. Two `require_prior` rows are two INDEPENDENT existence scans, so the net
        call passes while citing net and carrying BLOCK's threshold dict. One `prior_value` row
        over the same world refuses it. Same harness, same records, same two calls — the only
        thing that differs is whether the locate and the read met one record."""
        blk = _intake_payload(self.pack, _BLOCK_INTAKE)[_THRESHOLD_FIELD]
        rp = "require_prior"
        conjunction = self._drive(
            [{"check": rp, "action": "DECLARE-INTAKE", "field": "intake", "param": "intake",
              "cite": "DEV-LAW-INTAKE"},
             {"check": rp, "action": "DECLARE-INTAKE", "field": _THRESHOLD_FIELD,
              "param": "probe", "cite": "DEV-LAW-INTAKE"}],
            params={"intake": "required", "probe": "required"},
            a={"intake": _BLOCK_INTAKE, "probe": blk}, b={"intake": _NET_INTAKE, "probe": blk})
        self.assertEqual(conjunction, ("ADMIT", "ADMIT"),
                         "the two-row conjunction now separates, which would mean the rows are "
                         "being required to meet the same record and this kind is redundant")
        self.assertTrue(_separates(self._drive(self._row())),
                        "the one-row form does not separate either, so this contrast is about "
                        "the harness and not about the kinds")

    def test_the_ANSWER_COMES_FROM_THE_RECORD_and_no_parameter_can_move_it(self):
        """WHAT SEPARATES A LICENCE TEST FROM A CHECK THE CALLER SATISFIES BY CONSTRUCTION.
        `require_prior` compares a record's field against a CALLER-SUPPLIED value; this kind
        reads the law-data itself. Driven: the same two calls carrying wildly different extra
        parameter values return the identical pair.

        [CORRECTED BEFORE LANDING, and the correction is kept because the trap is general: the
        first draft passed `probe=None` on one arm, and a `required` parameter carrying None is
        refused AR-2 by the gate BEFORE any check runs. The row then reported that a parameter had
        moved the verdict, when what moved it was the harness reaching a different door. Every
        value below is non-None, so all four calls reach this kind's own branch.]"""
        first = _verdicts({"intake": "required", "probe": "required"}, self._row(),
                          {"intake": _BLOCK_INTAKE, "probe": 6144},
                          {"intake": _NET_INTAKE, "probe": 6144})
        second = _verdicts({"intake": "required", "probe": "required"}, self._row(),
                           {"intake": _BLOCK_INTAKE, "probe": "anything at all"},
                           {"intake": _NET_INTAKE, "probe": 0})
        self.assertEqual(first, second, "a parameter moved the verdict, so the caller can "
                                        "satisfy the licence test it is supposed to be subject to")
        self.assertTrue(_separates(first))
        # AND THE CONTROL FOR THIS ROW: the two argument sets really are different, so the
        # equality above is two runs agreeing and not one run compared with itself.
        self.assertNotEqual(("anything at all", 0), (6144, 6144))

    def test_AN_UNRESOLVED_PATH_IS_NOT_THE_UNESTABLISHED_CASE_and_refuses_on_its_own_terms(self):
        """THE THREE-STATE FORM, and the state a reader is most likely to think redundant. This
        law says an unestablished value is DECLARED unestablished and NEVER OMITTED, so a
        declaration silent about the field has not said 'no value' — it has said nothing, and
        nothing filled by a default is the fail-open trap. Driven at a path no declaration
        carries: BOTH classes refuse, including the one whose threshold IS established, because
        the question was about a field neither of them declares."""
        pair = self._drive(self._row(value_field="max_arrivals.no_such_key"))
        self.assertEqual(pair, ("REFUSE:DEV-LAW-INTAKE", "REFUSE:DEV-LAW-INTAKE"),
                         "an unresolved path does not refuse both classes, so it is being read "
                         "as an answer rather than as a silence: %r" % (pair,))
        # AND `require: unestablished` REFUSES IT TOO — the state is UNRESOLVED, not "no value",
        # so neither requirement is satisfied by it. This is the row that proves the third state
        # is a state and not a spelling of the second.
        self.assertEqual(self._drive(self._row(value_field="max_arrivals.no_such_key",
                                               require="unestablished")),
                         ("REFUSE:DEV-LAW-INTAKE", "REFUSE:DEV-LAW-INTAKE"),
                         "an unresolved path satisfies `unestablished`, which would make a "
                         "MISSING field indistinguishable from a DECLARED absence")

    def test_A_DECLARATION_NOBODY_MADE_refuses_and_the_record_does_NOT_claim_it_said_anything(self):
        """A DEFECT OF MINE, CAUGHT BY DRIVING THE PATHS AND KEPT AS A ROW. The first draft let
        the row's own `message` override reach the declaration-ABSENT refusal, so an act naming a
        declaration nobody made recorded a refusal reading 'this intake declaration leaves its
        threshold UNESTABLISHED' — a record asserting what nothing measured, which is the one lie
        class this estate refuses, produced by the check written to prevent it.

        The engine words the two absences and the row words only the mismatch. This row is
        pointed at the wording because the CITATION is identical in both cases, so a reader of
        the record has nothing but the message to tell the two states apart."""
        w = _cover_world(self)
        verdict, rec = _cover(w, "device-intake@nobody-declared-this", "device-io@block",
                              "virtio1")
        self.assertEqual(verdict, "REFUSE:P3-CLOSURE")
        self.assertIsNotNone(rec, "the refusal was raised and not recorded")
        message = dict(rec["payload"]).get("message") or ""
        self.assertIn("no DECLARE-INTAKE names", message,
                      "the refusal does not say that no declaration names this intake: %r"
                      % (message,))
        self.assertNotIn("UNESTABLISHED", message,
                         "the record claims a declaration that does not exist says something "
                         "about its threshold: %r" % (message,))
        # AND THE CONTROL: the class whose declaration DOES exist and DOES say unestablished
        # records exactly that wording, so the row above is a discriminator and not a filter
        # that matches nothing.
        _v, net = _cover(w, _REFUSED[0], _REFUSED[1], "virtio0")
        self.assertIn("UNESTABLISHED", dict(net["payload"]).get("message") or "",
                      "the genuinely-unestablished refusal does not carry that wording either, "
                      "so the assertion above cannot tell the two states apart")

    def test_the_PATH_WALKER_answers_in_THREE_states_with_a_positive_control_for_each(self):
        """The helper on its own terms, because the gate rows above cannot reach the case where a
        path meets a NON-MAPPING: no shipped declaration has one. RESOLVED-AND-None is not the
        same answer as UNRESOLVED, and a walker returning None for both would erase exactly the
        distinction its caller exists to make."""
        self.assertEqual(opdefs._resolve_field_path({"a": {"b": 6144}}, "a.b"), (True, 6144))
        self.assertEqual(opdefs._resolve_field_path({"a": {"b": None}}, "a.b"), (True, None))
        self.assertEqual(opdefs._resolve_field_path({"a": {}}, "a.b"), (False, None))
        self.assertEqual(opdefs._resolve_field_path({"a": 3}, "a.b"), (False, None),
                         "the walker indexes into a non-mapping, so a path could resolve "
                         "through something that is not a record structure")
        self.assertEqual(opdefs._resolve_field_path({}, "a"), (False, None))
        self.assertEqual(opdefs._resolve_field_path({"a": 1}, "a"), (True, 1))


class ThePriorValueLeashRefusesAtTheDefinitionDoor(unittest.TestCase):
    """THE LEASH THIS DECLARATION ARRIVED WITH, IN THE SAME ROUND IT DID (design-soul §2), and at
    DEFINITION time — the way an unknown check kind is already refused, because a policy that
    does not exist should not wait for a caller to discover it.

    POPULATION: the six malformations the leash names.
    BASIS: each is minted into the live pack through the ORDINARY door and the installer's own
    refusal is read. A malformation the door ACCEPTS is a rule nobody enforces."""

    def _refused(self, checks, params=None):
        with self.assertRaises(Exception) as ctx:
            _World(_mint_candidate(live_pack(), params or {"intake": "required"}, checks))
        return str(ctx.exception)

    def test_the_WELL_FORMED_row_LOADS_which_is_this_classs_positive_control(self):
        """Every row below asserts a refusal. Without this one, a door that refused EVERYTHING
        would pass the whole class, and it would read identically on the page."""
        w = _World(_mint_candidate(live_pack(), {"intake": "required"},
                                   [{"check": "prior_value", "action": "DECLARE-INTAKE",
                                     "field": "intake", "param": "intake",
                                     "value_field": _THRESHOLD_FIELD + ".value",
                                     "require": "established", "cite": "DEV-LAW-INTAKE"}]))
        self.assertIn(_PROBE, w.views.op_definitions(),
                      "the well-formed candidate did not register, so every refusal below may "
                      "be the door refusing this shape for a reason nobody declared")

    def test_the_SIX_malformations_are_each_refused_with_their_own_reason(self):
        """One row, six subjects, each pinned to the phrase the leash refuses it with — so a
        refusal arriving for a DIFFERENT reason reds instead of counting as a pass. A single
        `assertRaises` over six shapes would be one row that cannot tell them apart."""
        full = {"check": "prior_value", "action": "DECLARE-INTAKE", "field": "intake",
                "param": "intake", "value_field": _THRESHOLD_FIELD + ".value",
                "require": "established", "cite": "DEV-LAW-INTAKE"}
        cases = (
            ("no action", {k: v for k, v in full.items() if k != "action"},
             "names no action"),
            ("no field", {k: v for k, v in full.items() if k != "field"},
             "names no field"),
            ("no param", {k: v for k, v in full.items() if k != "param"},
             "names no param"),
            ("no value_field", {k: v for k, v in full.items() if k != "value_field"},
             "names no value_field"),
            ("param the op does not take", dict(full, param="not_a_parameter"),
             "which this operation does not take"),
            ("unknown requirement", dict(full, require="probably"),
             "not a state a declared value can be in"),
        )
        for label, row, needle in cases:
            self.assertIn(needle, self._refused([row]), label)

    def test_a_row_REQUIRING_NOTHING_is_refused_as_decoration(self):
        """The seventh shape, and it is separated from the six above because its absence has a
        DIFFERENT failure mode: a row with no `require` would not refuse anything at run time,
        so it would read as law and change no outcome — and the evaluator's own early return
        makes that silence total."""
        full = {"check": "prior_value", "action": "DECLARE-INTAKE", "field": "intake",
                "param": "intake", "value_field": _THRESHOLD_FIELD + ".value",
                "cite": "DEV-LAW-INTAKE"}
        self.assertIn("requires nothing is decoration", self._refused([full]))

    def test_an_UNKNOWN_CHECK_KIND_is_still_refused_which_is_the_gates_own_ground(self):
        """The vocabulary is CLOSED and this pass did not open it. A planted unknown kind must
        still be refused at the door, or the widening was a widening of the door rather than of
        the vocabulary."""
        self.assertIn("planted_unknown_kind",
                      self._refused([{"check": "planted_unknown_kind",
                                      "cite": "DEV-LAW-INTAKE"}]))


class TheIntakeOperationCoversWhatItsLawDescribes(unittest.TestCase):
    """C8 — DEV-LAW-INTAKE's OPERATIONAL HALF. The law has governed THE RECORD since v1.22.0 and
    supplied no operation that writes one; this is that operation.

    POPULATION: one world booted from src/founding/founding-pack.json at this tree.
    BASIS: the live op definitions and the records the gate actually appends — never the pack
    read as a file and never this file's belief about either."""

    def setUp(self):
        self.w = _World()

    def test_the_world_is_live_and_holds_both_device_laws_before_any_shape_is_read(self):
        """ITEM-21 NON-VACUITY, first. Every row below reads a shape out of this world; over an
        empty one they would all pass while stating nothing."""
        rules = self.w.views.active_rules()
        for law in ("DEV-LAW-BIND", "DEV-LAW-INTAKE", "P3-CLOSURE"):
            self.assertIn(law, rules, "%s is not live, so nothing below states anything" % law)

    def test_the_operation_is_REGISTERED_through_the_ordinary_door(self):
        defs = self.w.views.op_definitions()
        self.assertIn(THE_INTAKE_OP, defs,
                      "the operation this pass minted is not in the live registry, so it "
                      "entered no door at all")

    def test_the_operations_under_the_intake_law_are_now_THE_DECLARER_AND_THE_RECORDER(self):
        """W3b's own census row, on the other side of its stop. [The row it flips is
        `TheW3bWalksPinnedFacts.test_DECLARE_INTAKE_carries_declaration_parameters_and_is_the_
        only_op_under_its_law`, whose message names this pass as the place to update.]"""
        defs = self.w.views.op_definitions()
        under = tuple(sorted(n for n, e in defs.items()
                             if dict(e["definition"]).get("law_cited") == "DEV-LAW-INTAKE"))
        self.assertEqual(under, tuple(sorted(OPS_UNDER_THE_INTAKE_LAW)),
                         "the operations citing DEV-LAW-INTAKE are %r" % (list(under),))

    def test_the_record_is_FILED_UNDER_THE_INTAKE_LAW_and_not_under_the_admission_law(self):
        """C8's wrong-law red world, verified at :739 and driven here: 'the record filed under
        DEV-LAW-BIND REDS'. The FILING law is the definition's `law_cited`, which is what decides
        the record's `rule_cited` — so this row reads the appended record and not the definition
        alone."""
        d = self.w.views.op_definitions()[THE_INTAKE_OP]["definition"]
        self.assertEqual(dict(d)["law_cited"], "DEV-LAW-INTAKE")
        w = _cover_world(self)
        verdict, rec = _cover(w, _ADMITTED[0], _ADMITTED[1], "virtio1")
        self.assertEqual(verdict, "ADMIT")
        self.assertEqual(rec["rule_cited"], "DEV-LAW-INTAKE",
                         "the covering record is filed under %r" % (rec["rule_cited"],))
        self.assertEqual(rec["action"], THE_INTAKE_OP)

    def test_the_record_CARRIES_EVERY_CARRIER_THE_LAW_NAMES_and_never_the_content(self):
        """The law's own five-phrase list (W3b's `COVERING_RECORD_CARRIERS`, quoted out of the law
        record) mapped to the parameters that carry it, so a dropped carrier is a red and not a
        sentence nobody re-read. AND THE CONTENT IS ABSENT: device I/O content is STREAM and is
        classified out, so no parameter of this operation takes bytes of it."""
        law = dict(self.w.views.active_rules()["DEV-LAW-INTAKE"])["text"]
        self.assertEqual(carriers_present(law), COVERING_RECORD_CARRIERS,
                         "the law no longer names the five carriers this row maps, so the "
                         "mapping below is about a requirement that moved")
        w = _cover_world(self)
        _verdict, rec = _cover(w, _ADMITTED[0], _ADMITTED[1], "virtio1",
                               arrival_count=6144, byte_total=25165824)
        payload = dict(rec["payload"])
        for carrier, params in CARRIER_TO_PARAM.items():
            for p in params:
                self.assertIn(p, payload, "the record drops %r, which carries %r"
                                          % (p, carrier))
        self.assertEqual(payload["arrival_count"], 6144)
        self.assertEqual(payload["byte_total"], 25165824)
        self.assertEqual(payload["intake"], _ADMITTED[0])
        self.assertEqual(payload["window"], _ADMITTED[1])
        self.assertEqual(payload["device"], "virtio1")
        d = dict(self.w.views.op_definitions()[THE_INTAKE_OP]["definition"])
        for forbidden in ("content", "bytes", "data", "payload_bytes", "buffer"):
            self.assertNotIn(forbidden, dict(d["params"]),
                             "the operation takes %r — device I/O content is STREAM and is "
                             "classified out of every record under this law" % forbidden)
        self.assertIsNone(d.get("content_params"),
                          "the operation declares content_params, so bytes reach the blob "
                          "store under a law that classifies content out")

    def test_EVERY_PARAMETER_FORM_IS_EXPLICIT(self):
        """C7 on this pass's own population, which is one definition. A parameter form taken by
        silence is not declining the choice, it is taking it undecided."""
        d = dict(self.w.views.op_definitions()[THE_INTAKE_OP]["definition"])
        self.assertTrue(d.get("params"))
        for p, form in dict(d["params"]).items():
            self.assertIn(form, ("required", "optional"), "%s.%s = %r" % (THE_INTAKE_OP, p, form))
        known = set(dict(d["params"])) | set(dict(d.get("param_defaults") or {}))
        self.assertEqual(set(d.get("payload_from") or []) - known, set(),
                         "the operation writes a field it never declared")

    def test_NO_CITED_LAW_ID_of_this_operation_is_UNDECLARED(self):
        """The UNDECLARED-LAW-ID lesson, fourth application: declare what you cite. Binds THIS
        pass's own operation and claims nothing about anyone else's."""
        rules = self.w.views.active_rules()
        d = dict(self.w.views.op_definitions()[THE_INTAKE_OP]["definition"])
        self.assertIn(d["law_cited"], rules)
        for c in d.get("checks") or []:
            self.assertTrue(c.get("cite"), "a check of this operation names no cite")
            self.assertIn(c["cite"], rules,
                          "%s's %s check cites the undeclared %r"
                          % (THE_INTAKE_OP, c["check"], c.get("cite")))

    def test_RECORDING_THROUGH_DECLARE_INTAKE_IS_BARRED_and_DECLARE_INTAKE_DID_NOT_MOVE(self):
        """C8's first red world: 'recording through DECLARE-INTAKE REDS (barred by the law's own
        words)'. Driven as TWO facts rather than as a sentence. First, the declaring operation is
        BYTE-UNMOVED from the era — so nothing was smuggled into it beside the new operation.
        Second, it still takes none of the recording parameters, so it could not carry a covering
        record even if a caller tried."""
        era = ops_of(era_pin.pack_at(W3A3_BEFORE_COMMIT))["DECLARE-INTAKE"]
        now = ops_of(live_pack())["DECLARE-INTAKE"]
        # The vocabulary-door classification sweep (design/46 member 2, MOVER-4) later added a
        # `structural_params` list to EVERY production op, this one included — an estate-wide
        # landing well AFTER W3a3, orthogonal to whether the W3a3 pass smuggled anything into
        # DECLARE-INTAKE. `param_kinds` is the SAME shape of later-law field: EP-MAINT-OUTSIDE-2
        # (2026-09-09) classified this op's measurement fields (max_arrivals / arrivals_per_admitted_act
        # -> `measurement`) so the negative-quantity/text door skips them, a landing well AFTER W3a3 and
        # equally orthogonal to that pass. Both are normalized out of both sides so this row still proves
        # the substantive definition is byte-unmoved across the pass, without demanding the op predate a
        # law that postdates it. Any OTHER drift still reds. Conform the test to the live door, never the door.
        # C6 P8 (L28, 2026-09-09): `cell` is the SAME shape of later-law field — the CELL declaration
        # added estate-wide to EVERY production op (S|U|U{s}|S{u}), a landing well AFTER W3a3 and equally
        # orthogonal to whether that pass smuggled anything into DECLARE-INTAKE. Normalized out of both
        # sides so this row still proves the substantive definition is byte-unmoved across the pass.
        _later_law_fields = ("structural_params", "param_kinds", "cell")
        era = {k: v for k, v in era.items() if k not in _later_law_fields}
        now = {k: v for k, v in now.items() if k not in _later_law_fields}
        self.assertEqual(json.dumps(era, sort_keys=True), json.dumps(now, sort_keys=True),
                         "DECLARE-INTAKE moved in a pass whose whole landing is a new kind and "
                         "a new operation (the estate-wide structural_params classification field "
                         "excluded — a later law's landing, not this pass's)")
        params = tuple(sorted(dict(now["params"]).keys()))
        self.assertEqual(params, tuple(sorted(DECLARE_INTAKE_PARAMS)),
                         "DECLARE-INTAKE's parameters moved: %r" % (list(params),))
        for recording in ("arrival_count", "byte_total", "device"):
            self.assertNotIn(recording, dict(now["params"]),
                             "the DECLARING operation now takes %r, which is the recording "
                             "operation's parameter" % recording)

    def test_the_operation_declares_no_act_kind_release(self):
        """The release-exemption class, applied to this pass's own row rather than assumed: this
        operation writes a record, it ends nothing."""
        d = dict(self.w.views.op_definitions()[THE_INTAKE_OP]["definition"])
        self.assertIsNone(d.get("act_kind"))


class TheIntakeRefusalIsFAILCLOSEDAndCitesTheTerminalRule(unittest.TestCase):
    """C7's direction, produced by the pass that lands the operation rather than left for its
    consumer to discover: an intake for a class whose threshold this law declares UNESTABLISHED
    refuses, recorded, citing the TIP-LEVEL TERMINAL RULE.

    THE CITATION IS APPLIED AND NEVER CHOSEN (:735 — 'the terminal rule reaches already and the
    citation is named'). This file already drives that the terminal rule is `P3-CLOSURE` at four
    sites, the first at TheFailClosedIntermediateState, so the object is an in-suite driven fact
    here rather than a name this pass picked.

    POPULATION: the two shipped classes, block and net, plus two malformed calls.
    BASIS: the gate's own verdict and the record it appended. Never a reading of either."""

    def setUp(self):
        self.w = _cover_world(self)

    def test_BLOCK_ADMITS_on_its_confirmed_cap(self):
        verdict, rec = _cover(self.w, _ADMITTED[0], _ADMITTED[1], "virtio1", arrival_count=6144)
        self.assertEqual(verdict, "ADMIT",
                         "the class whose threshold this law establishes cannot record its own "
                         "arrivals, so the operation is fail-CLOSED against everything")
        self.assertFalse(rec.get("refused"))

    def test_NET_REFUSES_and_the_REFUSAL_IS_THE_RECORD(self):
        """'net intake admitted on any value REDS' and 'MORE recording as the failure response
        REDS'. Nothing goes dark: the refusal is itself the record."""
        verdict, rec = _cover(self.w, _REFUSED[0], _REFUSED[1], "virtio0", arrival_count=384)
        self.assertEqual(verdict, "REFUSE:P3-CLOSURE")
        self.assertIsNotNone(rec, "the refusal was raised and not recorded")
        self.assertTrue(rec["refused"])
        self.assertEqual(rec["action"], "op-refused")
        self.assertEqual(rec["rule_cited"], "P3-CLOSURE",
                         "the refusal cites %r rather than the tip-level terminal rule"
                         % (rec["rule_cited"],))
        self.assertEqual(dict(rec["payload"])["op"], THE_INTAKE_OP)

    def test_the_TWO_REFUSAL_SHAPES_cite_the_SAME_terminal_rule_side_by_side(self):
        """C7's own evidence requirement, produced here: 'both refusal records QUOTED with their
        citations, undeclared-class and unestablished-threshold side by side'. The undeclared
        shape is driven through the operation's own path — an intake name no declaration founds —
        so the two records are comparable rather than analogous."""
        _v1, unestablished = _cover(self.w, _REFUSED[0], _REFUSED[1], "virtio0")
        _v2, undeclared = _cover(self.w, "device-intake@no-such-class", _ADMITTED[1], "virtio1")
        for rec in (unestablished, undeclared):
            self.assertEqual(rec["rule_cited"], "P3-CLOSURE")
            self.assertTrue(rec["refused"])
        self.assertNotEqual(dict(unestablished["payload"]).get("message"),
                            dict(undeclared["payload"]).get("message"),
                            "the two refusal shapes record the same sentence, so a reader "
                            "cannot tell an unestablished threshold from an absent declaration")

    def test_the_terminal_rule_this_pass_cites_IS_A_DECLARED_LAW_of_this_founding(self):
        """A refusal citing a law id no record declares is a defect this EP already repaired one
        instance of. The one this operation names must not be a second."""
        rules = self.w.views.active_rules()
        self.assertIn("P3-CLOSURE", rules)
        self.assertIn("does not exist", dict(rules["P3-CLOSURE"])["text"])

    def test_CUSTODY_is_required_and_its_refusal_cites_the_ADMISSION_law(self):
        """The custody row is DERIVED from the declaration's own closer — every intake
        declaration under this law names `unbind` as a closer, so a covering record for a device
        no record binds contradicts the declaration it cites. Its refusal cites DEV-LAW-BIND
        because custody is that law's object; the RECORD stays filed under DEV-LAW-INTAKE."""
        for d in intake_declarations(live_pack()):
            self.assertTrue(any("unbind" in c for c in d["closers"]),
                            "%s no longer names unbind as a closer, so the custody row's "
                            "derivation has moved" % d["intake"])
        verdict, rec = _cover(self.w, _ADMITTED[0], _ADMITTED[1], "virtio-nobody-bound")
        self.assertEqual(verdict, "REFUSE:DEV-LAW-BIND")
        self.assertTrue(rec["refused"])
        self.assertEqual(rec["rule_cited"], "DEV-LAW-BIND")

    def test_a_WINDOW_NO_INTAKE_DECLARES_refuses_citing_the_intake_law(self):
        """The grade row: a covering record naming a window that no intake declaration covers
        would be recording at a grade no declaration founds."""
        verdict, rec = _cover(self.w, _ADMITTED[0], "device-io@nowhere", "virtio1")
        self.assertEqual(verdict, "REFUSE:DEV-LAW-INTAKE")
        self.assertTrue(rec["refused"])

    def test_the_refusal_is_NOT_A_CALLER_SUPPLIED_verdict_the_shim_could_skip(self):
        """WHY THE CHECK IS AT THE GATE AND NOT IN A CONSUMER. Moving this question to the shim
        would put it outside the gate, which is the second source of truth DEV-LAW-BIND refuses
        by name. Driven: no combination of the caller's own parameters admits net."""
        for count, total in ((0, 0), (1, 1), (6144, 25165824), (99999999, 99999999)):
            verdict, _rec = _cover(self.w, _REFUSED[0], _REFUSED[1], "virtio0",
                                   arrival_count=count, byte_total=total)
            self.assertEqual(verdict, "REFUSE:P3-CLOSURE",
                             "net was admitted at arrival_count=%r, so the licence is being "
                             "computed from what the caller passed" % count)


class TheFoundingMovedAtW3a3(unittest.TestCase):
    """C2 — the founding MOVES lawfully at W3a3 and BYTE-UNCHANGED IS THE FAILING OUTCOME.

    The empty-ground exception (:746, ADDENDUM 7 C3's boundary) rides as a CAP and does not fire
    here: it applies where the movement's declared first act forecloses the landing. W3a2's gate
    answered NO and stopped green; the OWNER then answered the gate it raised, so this movement's
    ground exists and the red world below is reached."""

    def test_the_pack_version_moved_one_MINOR_from_W3a3s_own_BEFORE(self):
        """W3a3 moved the founding 1.23.0 -> 1.24.0, one MINOR.

        [DOCUMENTED FLIP — EP-30-W1b, 2026-08-16, charter §A57's backward era-pin, discharging
        the second of W3a3's two rows (EP-30-R1 discharged the engine-diff row on 2026-08-16).
        ASSERTED: the AFTER end read from `live_pack()` — THE LIVE TREE — against the literal
        1.24.0. A range pinned at ONE end, which is an open range wearing a closed range's
        clothes: its subject was not what W3a3 moved but whatever the founding says TODAY.
        SUPERSEDED: the AFTER end read from `pack_at(W3A3_AFTER_COMMIT)`, so BOTH ends resolve
        through `era_pin` and the subject is W3a3's pass and nothing later.
        REMAINS TRUE, unchanged and re-checkable, carrying the same two literals it was written
        with: W3a3 moved the founding from 1.23.0 to 1.24.0, one MINOR.
        GIVEN UP: nothing. The live founding's own value was never this row's subject — it was
        an era-bound fact that a live read accidentally generalised into a standing watch, the
        same shape EP-30-R1 found in the engine-diff row beside it. The live value is asserted
        by the moving pass's own acceptance and named in its BUILD-PROGRESS entry beside the
        pack's sha256, which is where a claim about TODAY belongs.
        THE PIN IS VERIFIED BY CONTENT AND NEVER BY ADJACENCY (board :962 — the digest is the
        pin and the commit is its alias): the row below re-reads the era pack's own bytes.]"""
        self.assertEqual(pack_at(W3A3_BEFORE_COMMIT)["founding_version"], W3A3_BEFORE_VERSION)
        self.assertEqual(pack_at(W3A3_AFTER_COMMIT)["founding_version"], W3A3_AFTER_VERSION)
        # THE PIN CHECKED BY CONTENT, against HAND-COMPUTED LITERALS — the AFTER end gets the
        # same treatment the BEFORE end already has, because a commit is only ever an alias for
        # the bytes and this estate has recorded that three commits answer W3a3's other row
        # identically while one of them belongs to a LATER pass.
        self.assertEqual(
            hashlib.sha256(era_pin.blob_at(W3A3_BEFORE_COMMIT,
                                           era_pin.PACK_PATH)).hexdigest(),
            W3A3_BEFORE_PACK_SHA)
        self.assertEqual(
            hashlib.sha256(era_pin.blob_at(W3A3_AFTER_COMMIT,
                                           era_pin.PACK_PATH)).hexdigest(),
            "eaa82d22513cca7d3930ff1cacc30df0a62e04156f7a8864a166643418c93b6b",
            "the AFTER-era pack is not the bytes W3a3 closed over")

    def test_the_founding_is_NOT_byte_unchanged(self):
        era = era_pin.blob_at(W3A3_BEFORE_COMMIT, era_pin.PACK_PATH)
        with open(PACK_PATH, "rb") as fh:
            live = fh.read()
        self.assertNotEqual(hashlib.sha256(era).hexdigest(),
                            hashlib.sha256(live).hexdigest(),
                            "the founding is byte-unchanged after a LANDED law movement, which "
                            "is this movement's failing outcome and not its safe one")

    def test_the_designation_record_carries_the_NEW_version(self):
        """W3a3's landing stamped its own version into the designation record.

        [DOCUMENTED FLIP — EP-30-W1b, 2026-08-16, charter §A57 BY FALSIFICATION; this row is
        member 1 of 2 in this pass's sweep population, taken from its own suite arm at BOTH
        widths and never from a worklist.
        CAUSE: EP-30-W1b moved the founding 1.24.0 -> 1.25.0, so a world booted from the LIVE
        tree now stamps 1.25.0 and this row's constant describes W3a3's era.
        ASSERTED: `_World()`, the live tree — the open end.
        SUPERSEDED: `_World(pack_at(W3A3_AFTER_COMMIT))`, W3a3's OWN era. The range is now
        closed at both ends and the after-pin is recorded BY DIGEST: the pack at
        W3A3_AFTER_COMMIT is
        `eaa82d22513cca7d3930ff1cacc30df0a62e04156f7a8864a166643418c93b6b`, 207,517 bytes,
        which is the founding W3a3 closed over. The digest is the pin and the commit is its
        alias (board :962).
        REMAINS TRUE, and the row stays a genuine TWO-SIDED check rather than one reading
        wearing two labels (test_ep26.py:1242's warning): a pack read out of git on one side,
        a designation record stamped by the installer on the other.
        GIVEN UP: nothing — the LIVE stamp is asserted against 1.25.0 by EP-30-W1b's own
        battery and named beside the pack's sha256 in its BUILD-PROGRESS entry, which is where
        a claim about TODAY belongs.
        THE SAME REPAIR, THE FOURTH TIME IN THIS FILE: EP-28ZD, EP-29 W3a and EP-29 W3a3 each
        closed this same row's open end for their own era. A row shape that needs the identical
        edit at every founding move is a standing cost, and it is named here rather than only
        paid again.]"""
        fs = [e for e in _World(pack_at(W3A3_AFTER_COMMIT)).store.all()
              if e["action"] == "FOUND-STORE"][0]
        self.assertEqual(dict(fs["payload"])["founding_version"], W3A3_AFTER_VERSION)

    def test_THE_RULED_VERSION_TEST_the_1_23_0_pack_byte_unchanged_STILL_LOADS(self):
        """THE RULED TEST, BUILDER-EXECUTED: loads -> MINOR; does not -> MAJOR -> STOP TO THE
        MENTOR. It answered MINOR and MAJOR was never reached. Kept as a standing row so a later
        reader re-checks the answer rather than taking it.

        THE ARM IS SHARPER HERE THAN AT ANY PRIOR MOVEMENT and the reason is worth stating: this
        pass widened the ENGINE's check vocabulary, so the question is not only whether the era's
        DATA still parses but whether it still loads under a changed interpreter. A widening that
        broke the era's pack would be a MAJOR wearing a MINOR's number."""
        install_module._validate(install_module.records(pack_at(W3A3_BEFORE_COMMIT)))

    def test_THE_RULED_VERSION_TEST_the_GENESIS_RECORDS_load_under_the_widened_vocabulary(self):
        """The second arm. The census moves by EXACTLY ONE OPERATION and by nothing else, which
        is the interesting number precisely because everything except that one record must be
        unmoved: a rule count that moved would mean a law was smuggled in beside the kind.

        [DOCUMENTED FLIP — EP-30-C3R, 2026-08-21, charter §A57 BY FALSIFICATION, a RANGE
        CLOSURE. CAUSE: RANGE. SUBJECT-ERA: HISTORICAL for the census.
        CAUSE, DRIVEN: EP-30-C3 moved BOTH censuses — 44 rules and 77 ops — inside this row's
        open AFTER end. THE SHARP PART: the row's whole point is that a MOVED RULE COUNT MEANS
        A LAW WAS SMUGGLED IN BESIDE THE KIND, so an open end made a later pass's lawful,
        licensed, countersigned law declaration read as smuggling at W3a3. A watch pointed at
        the wrong era does not merely go quiet — it accuses the wrong pass.
        ASSERTED: `live_pack()` as W3a3's AFTER. SUPERSEDED: `pack_at(W3A3_AFTER_COMMIT)`.
        REMAINS TRUE, all four literals unchanged: 43 rules either side, 75 -> 76 operations.
        AND THE ROW MOVES TOWARD ITS OWN TITLE RATHER THAN AWAY FROM IT: `_validate` is the
        LIVE installer, so validating the ERA's records through it is era DATA under TODAY's
        widened vocabulary — which is what THE RULED VERSION TEST names. The live pack's own
        validation was never this row's subject and is asserted by the pass that moved it.
        GIVEN UP: nothing. The registry bridge below is DELIBERATELY LEFT LIVE — `_World()`
        with no pack — so the row still asserts that every genesis rule of W3a3's era reaches
        TODAY's active registry. That is a genuine era-to-live claim that can still fail, on
        the day a pass retires a rule, and era-pinning it would have thrown it away for
        tidiness.]"""
        era = install_module.records(pack_at(W3A3_BEFORE_COMMIT))
        now = install_module.records(pack_at(W3A3_AFTER_COMMIT))
        self.assertEqual(len([r for r in era if r.get("action") == "CREATE-RULE"]), 43)
        self.assertEqual(len([r for r in now if r.get("action") == "CREATE-RULE"]), 43)
        self.assertEqual(len([r for r in era if r.get("action") == "CREATE-OP"]), 75)
        self.assertEqual(len([r for r in now if r.get("action") == "CREATE-OP"]), 76)
        install_module._validate(now)
        active = _World().views.active_rules()
        for r in now:
            if r.get("action") == "CREATE-RULE":
                self.assertIn(r["payload"]["rule_id"], active,
                              "a genesis rule record does not reach the live registry")

    def test_the_loader_that_accepted_them_CAN_REFUSE(self):
        """Without this the two rows above are an instrument that cannot report its own failure.
        The plant lands on THIS PASS'S OWN new definition, and it is planted as a malformation of
        the NEW KIND — so the arm proves the widened door still closes."""
        p = copy.deepcopy(live_pack())
        planted = 0
        for st in p["steps"]:
            for r in st["records"]:
                if (r.get("payload") or {}).get("name") == THE_INTAKE_OP:
                    r["payload"]["definition"]["checks"] = [
                        {"check": "prior_value", "action": "DECLARE-INTAKE", "field": "intake",
                         "param": "intake", "value_field": "max_arrivals.value",
                         "require": "planted_unknown_requirement", "cite": "DEV-LAW-INTAKE"}]
                    planted += 1
        self.assertEqual(planted, 1)
        with self.assertRaises(Exception) as ctx:
            install_module._validate(install_module.records(p))
        self.assertIn("planted_unknown_requirement", str(ctx.exception))

    def test_the_DECLARED_LAW_CENSUS_moved_by_EXACTLY_ONE_OPERATION(self):
        """C1's census form, at this movement's own shape: ops +1, laws unmoved, nothing retired
        in either direction. Both differences printed, never a bare count.

        [DOCUMENTED FLIP — EP-30-C3R, 2026-08-21, charter §A57 BY FALSIFICATION, a RANGE
        CLOSURE. CAUSE: RANGE. SUBJECT-ERA: HISTORICAL — W3a3's census move is finished.
        CAUSE, DRIVEN, AND IT TOOK BOTH HALVES: EP-30-C3 minted an operation AND declared a
        law, so the op difference read two names and the law difference — the one this row
        asserts EMPTY, with the message "this pass declared a new LAW, and no licence covers
        one" — read one. Undoing either fact alone leaves this row red; that is what makes the
        cause a PAIR rather than a guess.
        ASSERTED: `live_pack()` as W3a3's AFTER. SUPERSEDED: `pack_at(W3A3_AFTER_COMMIT)`, the
        pin its four siblings in this class already carry.
        REMAINS TRUE, every literal unchanged: W3a3 declared exactly `DEVICE-INTAKE-COVER`,
        retired no operation, declared no law and retired none.
        GIVEN UP: nothing. This row was named on W3a3's OWN `NEXT_MOVE_FALSIFIES` worklist as
        owed this pin, and the worklist's own words — A FLOOR AND NEVER THE BOUND, THE BOUND IS
        A SUITE RUN — held exactly: it named four of this unit's twelve and missed eight.]"""
        era_ops, now_ops = (set(ops_of(pack_at(W3A3_BEFORE_COMMIT))),
                            set(ops_of(pack_at(W3A3_AFTER_COMMIT))))
        self.assertEqual(sorted(now_ops - era_ops), [THE_INTAKE_OP],
                         "this pass declared %r" % (sorted(now_ops - era_ops),))
        self.assertEqual(sorted(era_ops - now_ops), [], "this pass retired an operation")
        era_rules, now_rules = (set(rules_of(pack_at(W3A3_BEFORE_COMMIT))),
                                set(rules_of(pack_at(W3A3_AFTER_COMMIT))))
        self.assertEqual(sorted(now_rules - era_rules), [], "this pass declared a new LAW, and "
                                                            "no licence covers one")
        self.assertEqual(sorted(era_rules - now_rules), [], "this pass retired a law")

    def test_the_RECORD_count_moved_by_ONE_and_the_STEP_count_did_not_move(self):
        """The landing is ONE CREATE-OP record in the step that already holds this law's
        declaring operation. A new step would mint a second home for one law's operations.

        [DOCUMENTED FLIP — EP-30-C3R, 2026-08-21, charter §A57 BY FALSIFICATION, a RANGE
        CLOSURE. CAUSE: RANGE. SUBJECT-ERA: HISTORICAL — W3a3's landing is finished.
        CAUSE, DRIVEN: EP-30-C3 appended TWO records (one CREATE-OP, one CREATE-RULE) inside
        the open AFTER end, so the live total read 148 where this row asserts era + 1 = 146.
        ASSERTED: `live_pack()` as W3a3's AFTER. SUPERSEDED: `pack_at(W3A3_AFTER_COMMIT)`.
        REMAINS TRUE, every literal unchanged: W3a3 added exactly one record, minted no step,
        left `08k-device-intake-ops` holding exactly its two operations, and did not move the
        intake declaration count off two.
        GIVEN UP: nothing. The STEP-count half deserves one sentence, because it is the half a
        reader would expect to have kept watching the live tree: a new step in the LIVE pack is
        a claim about a later pass and not about W3a3, and C3 in fact minted none — driven at
        this hand, 27 steps at both ends. Naming that here is cheaper than a reader wondering.]"""
        era, now = pack_at(W3A3_BEFORE_COMMIT), pack_at(W3A3_AFTER_COMMIT)
        self.assertEqual(len(era["steps"]), len(now["steps"]))
        self.assertEqual(sum(len(s["records"]) for s in now["steps"]),
                         sum(len(s["records"]) for s in era["steps"]) + 1)
        step = [s for s in now["steps"] if s["step"] == "08k-device-intake-ops"][0]
        self.assertEqual([r["payload"]["name"] for r in step["records"]],
                         list(OPS_UNDER_THE_INTAKE_LAW))
        self.assertEqual(len(intake_declarations(now)), 2,
                         "this pass added or removed an intake DECLARATION, which is a law "
                         "change no part of this movement's licence covers")

    def test_the_ENGINE_moved_in_ONE_FILE_and_the_move_is_the_thirteenth_kind(self):
        """C2's fence half as a ROW rather than as a report line, and asserted against the ERA's
        bytes rather than against `git diff` — a working-tree diff empties the moment the
        two-minute autosync commits and would then pass whatever had been written.

        A CHECK KIND IS ENGINE VOCABULARY, so unlike every prior movement of this stage this one
        MUST move an engine file. The claim is therefore not that nothing moved: it is that
        EXACTLY ONE file moved and every other engine surface is byte-identical to the era.

        [DOCUMENTED FLIP — EP-30-R1, 2026-08-16, charter §A57. CAUSE: EP-30-W1a lawfully moved
        `src/kernel/store.py`, and this row read that as W3a3 having moved two files. ASSERTED:
        the era's engine bytes against the LIVE tree's — a range pinned at ONE end, which is an
        open range wearing a closed range's clothes, and EP-28G's flip on test_ep28h had already
        ruled that an open `X..HEAD` range REDS BY CONSTRUCTION on the next pass that lawfully
        touches the paths. This is that prediction arriving, on a row written to avoid it.
        SUPERSEDED: against `W3A3_AFTER_COMMIT`'s bytes, so both ends resolve through `era_pin`
        and the subject is W3a3's pass and nothing later. REMAINS TRUE, unchanged and
        re-checkable: W3a3 moved EXACTLY ONE engine file and it was `opdefs.py` — the three
        assertions below carry the same literals they were written with, because THE RANGE WAS
        WRONG AND THE CLAIM WAS NOT.
        GIVEN UP, and it is not nothing: the estate's ONLY LIVE assertion that the engine moves
        in exactly one file per pass. `TheFoundingMovedAtW2b.test_the_ENGINE_moved_ZERO_lines…`
        explicitly handed that watch to this row, and closing this range hands it to no one — a
        live claim about today's tree cannot be carried by a row about a closed era. WHO ABSORBS
        IT IS RULED (board :962) AND NOTHING IS MINTED TO REPLACE IT: the live claim was an
        ERA-BOUND fact about W3a3 that a live read accidentally generalised into a standing
        watch, and its absorber already exists — `:837`'s close discipline, every close's diff
        summary computed from the DECLARED FENCE, is the per-pass assertion of what moved.]

        THE PIN IS VERIFIED BY CONTENT, never by adjacency: three commits answer this row's
        eleven-path comparison identically and one of them belongs to the NEXT pass, so
        `test_the_era_pin_is_verified_BY_CONTENT_and_never_by_version_number` checks the AFTER
        end's digest as it already checks the BEFORE end's."""
        moved, held = [], []
        for path in ("src/kernel/opdefs.py", "src/kernel/gate.py", "src/kernel/crossing.py",
                     "src/kernel/store.py", "src/kernel/boot.py", "src/kernel/protection.py",
                     "src/kernel/authority.py", "src/kernel/reconcile.py",
                     "src/subsystems/devices.py", "src/founding/install.py",
                     "src/observe/windows.py"):
            era = hashlib.sha256(era_pin.blob_at(W3A3_BEFORE_COMMIT, path)).hexdigest()
            after = hashlib.sha256(era_pin.blob_at(W3A3_AFTER_COMMIT, path)).hexdigest()
            (moved if era != after else held).append(path)
        self.assertEqual(moved, ["src/kernel/opdefs.py"],
                         "the engine files this pass moved are %r — the licence is one check "
                         "kind, and a check kind lives in one file" % (moved,))
        self.assertIn("src/kernel/gate.py", held,
                      "the gate moved: the fourth check kind in a row must take ZERO lines "
                      "there, which is the theorem test_ep28g_w2 discharges structurally")
        self.assertGreater(len(held), 8, "the held population is too small to mean anything")

    def test_the_WORLD_BOOTS_with_EXACTLY_ONE_MORE_OPERATION_and_ONE_MORE_ACTIVE_RULE(self):
        """The landing adds a definition and nothing else, so the booted world's shape must move
        by exactly that.

        [CORRECTED BEFORE LANDING, and it is a fact about this estate rather than about my
        arithmetic, so it is written down instead of patched. The first draft asserted the same
        ACTIVE RULE COUNT either side and measured 126 against 125. An op definition IS an active
        rule — a CREATE-OP carries `rule_id: op:<name>` with a polarity, and the authority fold
        reads it — so minting an operation necessarily moves that count. ASSERTED: active rules
        unmoved. SUPERSEDED: +1, AND THE DIFFERENCE IS NAMED rather than counted, which is the
        stronger row: a count of +1 would also pass if this pass had added one operation and
        retired one law.]

        THE ROOT RULES MUST NOT MOVE, and that is the half worth keeping unchanged: root law is
        genesis-only, and an operation definition is not root law.

        [DOCUMENTED FLIP — EP-30-C3R, 2026-08-21, charter §A57 BY FALSIFICATION, a RANGE
        CLOSURE. CAUSE: RANGE. SUBJECT-ERA: HISTORICAL — the shape of the world W3a3 booted.
        CAUSE, DRIVEN: EP-30-C3's operation AND its law both reached the LIVE boot the AFTER
        end read, so the NAMED difference gained members W3a3 never declared — and the row's
        own correction note above says why naming beats counting: a bare +1 would have absorbed
        one added op and one retired law without a word. Here the naming is what fired.
        ASSERTED: `_World()`, the live tree. SUPERSEDED: `_World(pack=pack_at(
        W3A3_AFTER_COMMIT))`, the pin the designation-record sibling in this class already
        carries — THE ONE LOADER HANDED A DIFFERENT SOURCE, this file's own idiom and not a
        second boot path.
        REMAINS TRUE, unchanged in every literal and still a genuine two-sided boot: one more
        op definition, one more active rule, that rule named `op:DEVICE-INTAKE-COVER`, no
        active rule removed, root rules unmoved, one more record in the store.
        GIVEN UP: nothing — the LIVE world's shape was never this row's subject.]"""
        era = _World(pack=pack_at(W3A3_BEFORE_COMMIT))
        now = _World(pack=pack_at(W3A3_AFTER_COMMIT))
        self.assertEqual(len(now.views.op_definitions()),
                         len(era.views.op_definitions()) + 1)
        self.assertEqual(sorted(set(now.views.op_definitions())
                                - set(era.views.op_definitions())), [THE_INTAKE_OP])
        gained = sorted(set(now.views.active_rules()) - set(era.views.active_rules()))
        self.assertEqual(gained, ["op:%s" % THE_INTAKE_OP],
                         "the active rules this pass added are %r — an op definition is an "
                         "active rule, and anything else here is a law nobody licensed" % (gained,))
        self.assertEqual(sorted(set(era.views.active_rules())
                                - set(now.views.active_rules())), [],
                         "this pass removed an active rule")
        self.assertEqual(len(now.views.root_rules()), len(era.views.root_rules()),
                         "the root rules moved: root law is genesis-only and an operation "
                         "definition is not root law")
        self.assertEqual(len(list(now.store.all())), len(list(era.store.all())) + 1)

    def test_the_era_pin_is_verified_BY_CONTENT_and_never_by_version_number(self):
        """`era_pin`'s own stated cap: it makes the READ uniform and says nothing about whether a
        caller's PIN is the right commit. Choosing a pin by version number is this estate's most
        expensive known trap, so the pin is checked against the sha256 W3a's close recorded.

        [EXTENDED — EP-30-R1, 2026-08-16. BOTH ENDS ARE NOW PINNED, so both ends are now checked
        by content: this row was the BEFORE end's discriminator and the AFTER end arrived without
        one. IT IS THE AFTER END THAT NEEDS IT MORE, which is the finding worth keeping — the
        BEFORE pin is discriminated by its own pack digest, while THREE commits satisfy the
        AFTER pin's eleven-path content check and one of them is EP-30-W1a's, a LATER PASS.
        The digest below is the only thing that refuses it. A pin verified by what the rows
        happen to answer is a pin verified by nothing.]"""
        blob = era_pin.blob_at(W3A3_BEFORE_COMMIT, era_pin.PACK_PATH)
        self.assertEqual(hashlib.sha256(blob).hexdigest(), W3A3_BEFORE_PACK_SHA)
        after = era_pin.blob_at(W3A3_AFTER_COMMIT, "src/kernel/opdefs.py")
        self.assertEqual(hashlib.sha256(after).hexdigest(), W3A3_AFTER_OPDEFS_SHA,
                         "the AFTER pin's engine bytes are not W3a3's close: this commit answers "
                         "the eleven-path check the way three commits do, and the digest is the "
                         "only thing separating W3a3's close from the next pass's first write")

    def test_the_ERA_PIN_METHOD_IS_IMPORTED_AND_NOT_RE_DERIVED(self):
        """C2's own red world: a re-derived era idiom REDS. A PRESENCE test — this file's era read
        and the home's are shown to produce the same bytes — because the absence form inverted on
        an earlier pass, matching an ordinary English word in a docstring."""
        self.assertEqual(pack_at(W3A3_BEFORE_COMMIT), era_pin.pack_at(W3A3_BEFORE_COMMIT))
        self.assertEqual(os.path.dirname(os.path.abspath(era_pin.__file__)),
                         os.path.join(REPO, "tests"),
                         "era_pin resolved to something other than the estate's one home")

    def test_the_era_pin_reports_a_DIFFERENCE_when_there_is_one(self):
        """The instrument's own negative-result test; every era row in this pass rests on it, and
        after this pass the difference it must report is the one this pass made."""
        with open(PACK_PATH, "rb") as fh:
            live = fh.read()
        self.assertNotEqual(
            hashlib.sha256(era_pin.blob_at(W3A3_BEFORE_COMMIT, era_pin.PACK_PATH)).hexdigest(),
            hashlib.sha256(live).hexdigest())


class TheW3a3Sweep(unittest.TestCase):
    """§A57 BY FALSIFICATION, with the method IMPORTED from `tests/era_pin.py`.

    THE POPULATION IS BY FALSIFICATION AND NOT BY ADJACENCY (the clause's own 2026-08-09
    repair), and it is TAKEN FROM A FULL SUITE ARM rather than from a worklist. The arm ran
    before any flip: `Ran 2741 tests`, `FAILED (failures=20)` — TWENTY reds, ZERO errors, split
    below into FIFTEEN falsification flips and FIVE attestation reds.

    EVERY FALSIFICATION RED IS IN THIS FILE, which is the shape of a family that keeps its whole
    battery in one place. So no §A57 fence-relation recording in the `:400` form is owed by this
    pass, and that is a MEASURED statement rather than an assumption — the file column below is
    asserted by a row.

    AND THE WORKLIST WAS BOTH OVER- AND UNDER-NAMED, WHICH IS ITSELF THE FINDING. W3a handed
    forward NINE named rows at `TheW3aSweep.NEXT_MOVE_FALSIFIES` and said a worklist is a FLOOR
    and never the bound — its own population had been 32 where a worklist would have named 6,
    W1b's under-named by 8, W2b's over-named by 4. THIS ARM: six of W3a's nine reddened, three
    did not (its three byte-unmoved declaration rows, which this pass never touched), and NINE
    ROWS W3a NEVER NAMED reddened. **Over-named by three and under-named by nine, in the same
    arm. A worklist is a hypothesis and the arm is the measurement.**

    [CORRECTED BEFORE LANDING: this block first said TWELVE, from a partial read of W3a's
    tuple. The row below asserts the size, so the arithmetic was caught by running rather than
    by re-reading — which is the only reason to make a worklist comparison a row at all.]"""

    #: THE FIFTEEN FALSIFICATION FLIPS: (file, dotted row, kind, cause). Each is a row that was
    #: TRUE of the world it was written in and FALSE after this pass's own move, and each was
    #: era-pinned or re-taken rather than deleted or relaxed.
    SWEPT = (
        ("tests/test_ep29.py", "TheVocabularyRateHeld.test_OP_CHECKS_is_unchanged_by_this_pass",
         "FAIL", "the vocabulary grew twelve to thirteen"),
        ("tests/test_ep29.py",
         "TheIntakeLawLanded.test_the_check_VOCABULARY_ITSELF_is_unchanged_by_this_pass",
         "FAIL", "the vocabulary grew twelve to thirteen"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW2b.test_the_ENGINE_moved_ZERO_lines_which_is_what_makes_MINOR_"
         "mean_what_it_says",
         "FAIL", "a check kind is engine vocabulary, so opdefs.py moved"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW2b.test_the_new_op_is_EXACTLY_the_one_this_pass_added",
         "FAIL", "this pass minted a second operation after W2b's"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a.test_the_pack_version_moved_one_MINOR_from_W3as_own_BEFORE",
         "FAIL", "the founding moved 1.23.0 -> 1.24.0"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a.test_the_designation_record_carries_the_NEW_version",
         "FAIL", "the founding moved 1.23.0 -> 1.24.0"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a.test_the_DECLARED_LAW_CENSUS_did_not_move_in_either_direction",
         "FAIL", "this pass declared an operation"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a.test_the_RECORD_and_STEP_counts_did_not_move",
         "FAIL", "this pass appended one CREATE-OP record"),
        ("tests/test_ep29.py", "TheFoundingMovedAtW3a.test_the_ENGINE_moved_ZERO_lines",
         "FAIL", "a check kind is engine vocabulary, so opdefs.py moved"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a.test_the_WORLD_BOOTS_IDENTICALLY_either_side_of_the_amend",
         "FAIL", "the booted world gained one record and one active rule"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a.test_THE_RULED_VERSION_TEST_the_GENESIS_RECORDS_load_under_"
         "the_amended_law",
         "FAIL", "the live CREATE-OP census is 76 and no longer W3a's 75"),
        ("tests/test_ep29.py",
         "TheW3bWalksPinnedFacts.test_DECLARE_INTAKE_carries_declaration_parameters_and_is_"
         "the_only_op_under_its_law",
         "FAIL", "W3b's own stop answered — the row named this pass as its place to update"),
        ("tests/test_ep29.py",
         "TheW3bWalksPinnedFacts.test_the_law_citation_search_FINDS_A_PLANTED_SECOND_OP",
         "FAIL", "the control's expected set gained the real second operation"),
        ("tests/test_ep29.py", "TheW2bRowsCanBeMadeToFail.test_the_control_PASSES_every_covered_row",
         "FAIL", "a covered row was falsified, so the control could not pass it unmutated"),
        ("tests/test_ep29.py", "TheW3aRowsCanBeMadeToFail.test_the_control_PASSES_every_covered_row",
         "FAIL", "covered rows were falsified, so the control could not pass them unmutated"),
    )

    #: THE FIVE ATTESTATION REDS from the same arm, named so the two kinds are not conflated by
    #: a later reader counting twenty and looking for twenty flips. NO EDIT TO ANY ROW FIXES
    #: THESE — they say "the founding on disk is unattested", and what discharges them is THIS
    #: PASS'S BUILD-PROGRESS ENTRY naming 1.24.0 and the pack's own sha256 together, in one
    #: entry. The same five, in the same order, that W2b's and W3a's sweeps each found: the two
    #: doors are a property of the estate and not of any one pass.
    ATTESTATION_REDS = (
        "tests/test_ep28i.py::TestTheVersionMoves."
        "test_the_J9_instrument_is_live_and_binds_whatever_pack_ships",
        "tests/test_ep28k.py::TestTheVersionMoves."
        "test_J9_the_same_version_may_not_name_two_distinct_foundings",
        "tests/test_ep28n.py::TestTheVersionMoves."
        "test_J9_the_same_version_may_not_name_two_distinct_foundings",
        "tests/test_ep28n2.py::TestTheVersionMoves."
        "test_J9_the_same_version_may_not_name_two_distinct_foundings",
        "tests/test_founding_is_logged.py::TestTheFoundingOnDiskIsNamedInTheLog."
        "test_the_founding_version_and_pack_hash_are_named_together_in_one_entry",
    )

    #: THE SECOND-ORDER FLIPS, RECORDED SEPARATELY BECAUSE THEIR CAUSE IS DIFFERENT AND A READER
    #: WOULD OTHERWISE COUNT NINETEEN AND LOOK FOR NINETEEN IN THE ARM. These four did NOT red in
    #: the pre-flip arm. They redded once the §A57 era-pins landed, because era-pinning a row
    #: moves its subject off the live tree and their plants reached the live tree only.
    #:
    #: THE LESSON IS THE ONE WORTH CARRYING: a §A57 repair can BREAK A RED WORLD SILENTLY. Three
    #: of these four would have gone on passing while planting defects into a pack nobody read —
    #: §7.1's first disguise, introduced by the repair rather than by the pass being repaired,
    #: and caught only because the two CONTROL rows redded first and made the whole family
    #: visible. A pass that era-pins a row must ask what plants into it.
    SECOND_ORDER = (
        ("tests/test_ep29.py",
         "TheW2bRowsCanBeMadeToFail.test_a_pass_that_ADDED_A_SECOND_OP_by_drift_REDS"),
        ("tests/test_ep29.py", "TheW3aRowsCanBeMadeToFail.test_A_BYTE_UNCHANGED_FOUNDING_REDS"),
        ("tests/test_ep29.py",
         "TheW3aRowsCanBeMadeToFail.test_A_LAW_DECLARED_BESIDE_THE_WITHDRAWAL_REDS"),
        ("tests/test_ep29.py",
         "TheW3aRowsCanBeMadeToFail.test_A_SECOND_DECLARATION_CREATED_BESIDE_THE_AMENDED_ONE_REDS"),
    )

    #: SITES THAT SPELL A FLIPPED READ AND DID NOT REDDEN, named rather than swept in. §A57's
    #: permission is bounded by FALSIFICATION, so a site that passed is out of population however
    #: much it looks like the fifteen that did not — and the first is RAISED in this pass's entry,
    #: because it survived for a reason that makes it weaker rather than stronger.
    NOT_SWEPT_BECAUSE_NOT_FALSIFIED = (
        ("tests/test_ep29.py", "TheVocabularyRateHeld.test_the_engine_is_byte_unchanged_by_this_pass",
         "reads `git diff --numstat` against the WORKING TREE, and the two-minute autosync had "
         "already committed this pass's engine edit — so it passed over a moved file. It is out "
         "of population because it did not red, and it is RAISED because a diff row whose "
         "subject is the working tree cannot see a committed change at all"),
        ("tests/test_ep29.py", "TheFoundingMovedAtW3a.test_the_founding_is_NOT_byte_unchanged",
         "compares the era's pack to the live one and asks only that they DIFFER, which a "
         "further move keeps true — the shape of an era row that survives its successors"),
        ("tests/test_ep29.py",
         "TheNetThresholdIsWithdrawnLawfully.test_BLOCKS_WHOLE_DECLARATION_is_BYTE_UNMOVED",
         "this pass moved no declaration, so W3a's three withdrawal rows on its worklist were "
         "not falsified — the worklist named them and the arm did not"),
    )

    def test_the_two_kinds_of_red_are_COUNTED_SEPARATELY(self):
        """A suite tail shows one number. These route to different doors: a flip is an edit to a
        row, an attestation red is discharged by writing the entry. FIFTEEN AND FIVE,
        reconciling to the twenty the pre-flip arm reported."""
        self.assertEqual(len(self.SWEPT), 15)
        self.assertEqual(len(self.ATTESTATION_REDS), 5)
        self.assertEqual(len(self.SWEPT) + len(self.ATTESTATION_REDS), 20)
        self.assertEqual({p for p, _r, _k, _w in self.SWEPT}, {"tests/test_ep29.py"},
                         "the flip population left this pass's own file, and §A57's fence "
                         "relation would then need recording in the :400 form")

    def test_the_swept_population_was_ALL_FAILURES_AND_NO_ERRORS(self):
        """Recorded as arithmetic because 'mostly failures' is the kind of sentence that hides a
        miscount — and because an ERROR in a sweep arm means a planted world broke an instrument
        rather than a claim, which routes to a third door this pass never needed."""
        kinds = [k for _p, _r, k, _w in self.SWEPT]
        self.assertEqual((kinds.count("FAIL"), kinds.count("ERROR")), (15, 0))

    def test_every_swept_row_STILL_EXISTS_and_resolves(self):
        """A worklist naming rows that do not exist is worse than no worklist, and this one is a
        record of what was repaired."""
        for path, dotted, _kind, _why in self.SWEPT:
            self.assertTrue(os.path.exists(os.path.join(REPO, path)), path)
            cls_name, meth = dotted.split(".")
            cls = globals().get(cls_name)
            self.assertIsNotNone(cls, "no such class: %s" % cls_name)
            self.assertTrue(hasattr(cls, meth), "no such row: %s" % dotted)

    def test_the_SECOND_ORDER_rows_still_exist_and_are_NOT_double_counted(self):
        for path, dotted in self.SECOND_ORDER:
            self.assertTrue(os.path.exists(os.path.join(REPO, path)), path)
            cls_name, meth = dotted.split(".")
            self.assertTrue(hasattr(globals().get(cls_name), meth), dotted)
        self.assertEqual(set(d for _p, d in self.SECOND_ORDER)
                         & set(d for _p, d, _k, _w in self.SWEPT), set(),
                         "a second-order flip is also counted in the arm's population")

    def test_the_ATTESTATION_reds_name_real_files(self):
        for dotted in self.ATTESTATION_REDS:
            self.assertTrue(os.path.exists(os.path.join(REPO, dotted.split("::")[0])), dotted)

    def test_the_UNSWEPT_sites_still_exist_and_are_named_for_what_they_are(self):
        for _path, name, _why in self.NOT_SWEPT_BECAUSE_NOT_FALSIFIED:
            cls_name, meth = name.split(".")
            self.assertTrue(hasattr(globals().get(cls_name), meth), name)

    def test_W3as_HANDED_FORWARD_WORKLIST_was_BOTH_OVER_AND_UNDER_NAMED(self):
        """THE WORKLIST MEASURED AGAINST THE ARM, which is the only way the FLOOR-not-BOUND claim
        stays a measurement instead of a slogan. W3a named nine; the arm falsified six of them,
        left three standing, and reddened nine rows W3a never named. Every figure here is
        computed from the two tuples rather than typed, so a later pass that grows either one
        gets a red instead of a stale sentence."""
        named = {d for _p, d in TheW3aSweep.NEXT_MOVE_FALSIFIES}
        swept = {d for _p, d, _k, _w in self.SWEPT}
        self.assertEqual(len(named), 9, "W3a's handed-forward worklist is no longer nine")
        self.assertEqual(len(named & swept), 6,
                         "the overlap with W3a's worklist moved: %r" % (sorted(named & swept),))
        self.assertEqual(sorted(named - swept),
                         ["TheNetThresholdIsWithdrawnLawfully."
                          "test_BLOCKS_WHOLE_DECLARATION_is_BYTE_UNMOVED",
                          "TheNetThresholdIsWithdrawnLawfully."
                          "test_the_LAW_TEXT_itself_is_BYTE_UNMOVED",
                          "TheNetThresholdIsWithdrawnLawfully."
                          "test_the_OTHER_UNESTABLISHED_VALUE_is_unmoved"],
                         "the rows W3a predicted and this pass did not falsify moved: %r"
                         % (sorted(named - swept),))
        self.assertEqual(len(swept - named), 9,
                         "the rows W3a's worklist did not name: %r" % (sorted(swept - named),))

    def test_the_ERA_PIN_METHOD_IS_IMPORTED_AND_NOT_RE_DERIVED(self):
        """C2's own red world: a re-derived era idiom REDS, and the class it reds is the eighteen
        copies EP-28Z retired out of ten files. A PRESENCE test — this file's era read and the
        home's are shown to produce the same bytes — because the absence form inverted on an
        earlier pass, matching an ordinary English word in a docstring."""
        self.assertEqual(pack_at(W3A3_BEFORE_COMMIT), era_pin.pack_at(W3A3_BEFORE_COMMIT))

    def test_the_VOCABULARY_READER_IS_IMPORTED_AND_NOT_RE_DERIVED(self):
        """The same clause one instrument over, because this pass needed a SECOND historical
        reader and the estate already had one. `kinds_at` resolves to `tools/docmap/checkvocab`,
        the home EP-28V built to read `OP_CHECKS` by AST — not to a walk written here."""
        self.assertEqual(kinds_at(W3A_AFTER_ERA_COMMIT), TheVocabularyRateHeld.PINNED)
        # [DOCUMENTED FLIP — EP-30-C1R, 2026-08-21, board `:1618`. CAUSE: RANGE. SUBJECT-ERA:
        # HISTORICAL — the claim is about W3a3's OWN arithmetic (the era's twelve plus the one
        # licensed kind is the vocabulary W3a3 closed on), not about today's tree. Its right
        # side read `THE_LIVE_CHECK_KINDS`, which is live and has since moved to fifteen under
        # a LATER act. ASSERTED and REMAINS TRUE, unchanged in every literal: era + licensed
        # kind == W3a3's thirteen. SUPERSEDED: only the SOURCE of the right side.]
        self.assertEqual(kinds_at(W3A_AFTER_ERA_COMMIT) + (THE_LICENSED_THIRTEENTH,),
                         THE_PRE_RULING_VOCABULARY + (THE_LICENSED_THIRTEENTH,),
                         "the era's twelve plus the licensed kind is not W3a3's thirteen")

    #: THE NEXT MOVE'S WORKLIST — the rows that compare a LIVE-tree read against a literal THIS
    #: pass's era makes true, so the next founding pass falsifies exactly these and owes them the
    #: §A57 era-pin. A FLOOR AND NEVER THE BOUND: this pass's own arm found nine rows W3a's
    #: worklist did not name, and W3a's found twenty-six W2b's did not. THE BOUND IS A SUITE RUN
    #: AND NOTHING ELSE IS.
    #:
    #: AND ONE INSTRUCTION THE PREVIOUS WORKLISTS COULD NOT CARRY, because this pass is the first
    #: to learn it: WHEN YOU ERA-PIN A ROW, LOOK FOR WHAT PLANTS INTO IT. The red worlds covering
    #: these rows live in TheW3aRowsCanBeMadeToFail and TheW2bRowsCanBeMadeToFail, and each has a
    #: COVERED_ERA population that must move with the row it covers.
    NEXT_MOVE_FALSIFIES = (
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a3.test_the_pack_version_moved_one_MINOR_from_W3a3s_own_BEFORE"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a3.test_the_designation_record_carries_the_NEW_version"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a3.test_THE_RULED_VERSION_TEST_the_GENESIS_RECORDS_load_under_"
         "the_widened_vocabulary"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a3.test_the_DECLARED_LAW_CENSUS_moved_by_EXACTLY_ONE_OPERATION"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a3.test_the_RECORD_count_moved_by_ONE_and_the_STEP_count_did_not_move"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a3.test_the_ENGINE_moved_in_ONE_FILE_and_the_move_is_the_thirteenth_kind"),
        ("tests/test_ep29.py",
         "TheFoundingMovedAtW3a3.test_the_WORLD_BOOTS_with_EXACTLY_ONE_MORE_OPERATION_and_ONE_"
         "MORE_ACTIVE_RULE"),
        ("tests/test_ep29.py",
         "TheVocabularyGrewBY_EXACTLY_THE_ONE_RULED_KIND.test_the_vocabulary_moved_by_EXACTLY_"
         "the_one_ruled_kind"),
        ("tests/test_ep29.py",
         "TheVocabularyGrewBY_EXACTLY_THE_ONE_RULED_KIND.test_A_SECOND_KIND_RIDING_THE_LICENCE_REDS"),
        ("tests/test_ep29.py",
         "TheThresholdReadIsNotExpressibleInTheLiveVocabulary.test_the_GRAMMAR_grew_by_EXACTLY_"
         "the_licensed_kinds_one_new_key"),
    )

    def test_every_row_on_the_next_moves_worklist_EXISTS(self):
        self.assertTrue(self.NEXT_MOVE_FALSIFIES)
        for path, dotted in self.NEXT_MOVE_FALSIFIES:
            self.assertTrue(os.path.exists(os.path.join(REPO, path)), path)
            cls_name, meth = dotted.split(".")
            cls = globals().get(cls_name)
            self.assertIsNotNone(cls, "no such class: %s" % cls_name)
            self.assertTrue(hasattr(cls, meth), "no such row: %s" % dotted)

    def test_this_section_authors_NO_VERSION_CONSTANT_that_would_join_a_LATER_sweep(self):
        """WALKED OVER THE AST AND NOT GREPPED FOR A LITERAL, on this file's own precedent: a
        grep for the current version string matches itself the moment it is written. The version
        constants this pass DOES author live with the W3a3 era block, where a later pass's sweep
        already looks for them; this class carries none."""
        semver = re.compile(r"^\d+\.\d+\.\d+$")
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        mine = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "TheW3a3Sweep"]
        self.assertEqual(len(mine), 1, "the class walk did not find this section")
        found = [c.value for n in mine for c in ast.walk(n)
                 if isinstance(c, ast.Constant) and isinstance(c.value, str)
                 and semver.match(c.value)]
        self.assertEqual(found, [], "a W3a3 sweep row carries a version constant: %r" % (found,))
        planted = ast.parse('class TheW3a3Planted:\n    V = "9.99.9"\n')
        self.assertTrue([c.value for c in ast.walk(planted)
                         if isinstance(c, ast.Constant) and isinstance(c.value, str)
                         and semver.match(c.value)],
                        "the detector cannot find a version constant that IS there, so its "
                        "empty answer above says nothing")


import tarfile                                                   # noqa: E402
import time                                                      # noqa: E402


# =======================================================================================
# EP-29 W3b — THE SHIM (ADDENDUM 8 C3-C5 and C7), 2026-08-15
#
# W2 SHADOWED and could refuse nothing; its records were EVIDENCE. THIS INTERPOSES: a
# governed device crossing enters the loaded module, is carried to the gate, and the
# effect is released to the caller only after the gate's record is durable. That
# difference is not a sentence here -- it is `TheCacheClassStillAnswersWithTheBrainDead`,
# which kills the brain and shows DECISIONS failing while CACHE reads keep answering with
# real state.
#
# THE FENCE MEMBER `planning/vm/govshim/` WAS NAMED BY THE :725 RULING AT THE ARCHITECT
# SEAT AND NOT CHOSEN HERE. This walk VERIFIES its ground -- the guest builds at this
# layout as it did for govosfs -- under the three-state form; every divergence found is a
# FINDING in the entry, never an amendment written by the unit that found it.
#
# GUEST-ONLY, EP-00 RULE 9 ABSOLUTE. The module is built in the guest and loaded only
# there. Nothing in this section insmods on the host and nothing asks to.
#
# SNAPSHOT BEFORE EVERY LOAD, PER LOAD. `_snapshot_before_load` goes through the QEMU
# MONITOR (`savevm`), because the live guest runs from `gov-lab.qcow2` DIRECTLY and the
# image is locked while it runs -- `qemu-img snapshot -c` against it is the one act in
# this unit that cannot be undone. IF THE SNAPSHOT CANNOT BE TAKEN THE LOAD DOES NOT
# HAPPEN and the row FAILS rather than skips: a skip would put "the lab was down" and "we
# chose to load an unprotected guest" in one bucket, and only one of those is acceptable.
# =======================================================================================
SHIM_DIR = os.path.join(REPO, "planning", "vm", "govshim")
SHIM_SOURCES = ("govshim.c", "Makefile", "govshimd.py")
GOVSHIM_MODULE = "govshim"

#: The guest's REAL virtio devices, driven at the walk rather than carried: `virtio0` is
#: ens3 under virtio_net, `virtio1` is vda and `virtio2` is vdb, both under virtio_blk.
#: D8's bound is exactly this set and the module is given it as a parameter.
SHIM_VALIDATION_SET = ("virtio0", "virtio1", "virtio2")
SHIM_BLOCK_DEVICE, SHIM_NET_DEVICE = "virtio1", "virtio0"

#: THE FOUR CROSSINGS AND THE SHIPPED OPERATION EACH BECOMES. The founding does not move
#: for this unit, so every one of these already exists; a fifth name here would be a law
#: pass wearing a transport's clothes.
CROSSING_TO_OP = {"register": "REGISTER-CAPABILITY", "bind": "BIND-DEVICE",
                  "unbind": "UNBIND", "io": "DEVICE-IO-WINDOW-WRITE",
                  "intake": "DEVICE-INTAKE-COVER"}

#: WHAT EACH CROSSING'S RECORD CITES, HAND-COMPUTED from the definitions' own `law_cited`
#: and never read back off a run. An expectation produced by running the code is a
#: recording of behaviour, not a test of it.
CROSSING_RECORD_CITES = {"REGISTER-CAPABILITY": "CAP-IS-LAW", "BIND-DEVICE": "DEV-LAW-BIND",
                         "UNBIND": "DEV-LAW-BIND",
                         "DEVICE-IO-WINDOW-WRITE": "DEV-LAW-BIND",
                         "DEVICE-INTAKE-COVER": "DEV-LAW-INTAKE"}

#: The ioctl numbers by class. THE NUMBER DECIDES (design/10 §7): below 128 a call
#: CROSSES, at or above it a call is answered from derived state with no crossing at all.
SHIM_COMMAND_NUMBERS = {"register": 1, "bind": 2, "unbind": 3, "io": 4, "intake": 5}
SHIM_QUERY_NUMBERS = {"binding": 128, "arrivals": 129, "crossings": 130}
SHIM_CACHE_BASE = 128

#: C7's two shapes and the arm that drives each, side by side as the claim requires.
SHIM_REFUSAL_ARMS = {"unestablished-threshold": "intake-net-unestablished",
                     "undeclared-class": "intake-undeclared-class"}

#: THE TIP OF THE CHAIN THE GATE COMPUTES for a device refusal that no declaration
#: permits. NOT a name this file chose: it is read out of the LIVE LAW-DATA by
#: `computed_refusal_tip()` below and compared against what the shim's record actually
#: cited. The :787 ruling's own surviving instruction is exactly that -- quote each
#: refusal record's citation and compare it against the chain the gate COMPUTES, never
#: against a name a plan froze. See this pass's entry for the finding that the :787
#: bracket predicted a different tip from the one W3a3 landed and the mentor accepted.
SHIM_TERMINAL_RULE = "P3-CLOSURE"

_SHIM_MEMO = {}

#: THE REAL-DRIVER ENDPOINT INSTRUMENT. Driver text that exists solely to make a row
#: drivable is part of the row and in-fence wherever its row is (:682, by class). It
#: WRITES NOTHING: every act is a read.
_DRIVER_ENDPOINT_DRIVER = r'''#!/usr/bin/env python3
"""EP-29 W3b — C5's endpoint: what the VALIDATION DRIVERS are, at one instant.

THE POPULATION IS NAMED HERE RATHER THAN ASSUMED, and the naming is the finding this
instrument exists to carry: on this guest virtio_blk and virtio_net are BUILT INTO the
kernel image, not modules. There is no `.ko` to hash, so "the validation drivers
byte-identical" cannot be a file digest and is not pretended to be one. What IS
measurable, and what this reports:

  * the on-disk kernel IMAGE that contains them, by sha256;
  * the RUNNING kernel's own symbol table for those drivers, by sha256 over the selected
    lines -- an in-memory statement, which a file digest is not;
  * whether each is still on the builtin list, so a module arriving to displace one shows
    up as a change of KIND and not only of bytes.
"""
import hashlib, json, os, subprocess

K = os.uname().release
out = {"kernel": K, "drivers": {}}
img = "/boot/vmlinuz-%s" % K
out["kernel_image"] = {"path": img, "exists": os.path.exists(img)}
if os.path.exists(img):
    b = open(img, "rb").read()
    out["kernel_image"]["sha256"] = hashlib.sha256(b).hexdigest()
    out["kernel_image"]["size"] = len(b)
bi = "/lib/modules/%s/modules.builtin" % K
builtin = set()
if os.path.exists(bi):
    builtin = {os.path.basename(l.strip())[:-3] for l in open(bi) if l.strip().endswith(".ko")}
for drv in ("virtio_blk", "virtio_net", "virtio", "virtio_pci", "virtio_ring"):
    p = subprocess.run(["modinfo", "-n", drv], capture_output=True, text=True)
    path = (p.stdout or "").strip()
    out["drivers"][drv] = {
        "builtin_list": drv in builtin, "modinfo_path": path or None,
        "is_module_file": bool(path and path != "(builtin)" and os.path.exists(path)),
        "sysfs": os.path.isdir("/sys/module/%s" % drv)}
sel = sorted(l for l in open("/proc/kallsyms").read().splitlines()
             if (" virtblk_" in l or " virtnet_" in l or " virtio_" in l))
out["kallsyms"] = {
    "population": "every /proc/kallsyms line whose symbol begins virtblk_, virtnet_ or "
                  "virtio_, on this boot",
    "count": len(sel), "sha256": hashlib.sha256("\n".join(sel).encode()).hexdigest()}
print("DRIVERS-JSON:" + json.dumps(out))
'''


def shim_sources():
    """The fence directory's own bytes, so a row asserts about the source that was SHIPPED
    rather than about a copy some earlier run left on the guest."""
    out = {}
    for name in SHIM_SOURCES:
        with open(os.path.join(SHIM_DIR, name), encoding="utf-8") as fh:
            out[name] = fh.read()
    return out


def shim_digest():
    h = hashlib.sha256()
    for name, text in sorted(shim_sources().items()):
        h.update(name.encode())
        h.update(text.encode())
    return h.hexdigest()


def computed_refusal_tip(pack=None, action="DECLARE-INTAKE"):
    """THE TIP OF THE CHAIN THE GATE COMPUTES for the two device refusal shapes, READ OUT
    OF THE LAW-DATA rather than named, and computed PER CHAIN rather than over the
    operation's whole `prior_value` set.

    Both intake shapes are decided by the `prior_value` row DEVICE-INTAKE-COVER declares on
    its DECLARE-INTAKE chain -- one on its locate branch, one on its require branch -- so
    the tip is that row's own `cite`, whatever the founding says it is today.

    This exists so the C7 rows compare a record's citation against the LAW, never against
    a constant, which is the only form of that check that cannot expire when the law
    moves.

    [DOCUMENTED FLIP -- EP-30-W3, 2026-08-19, on the ruling at board `:1256`. CAUSE:
    EP-30-W2 lawfully gave DEVICE-INTAKE-COVER a SECOND `prior_value` row, on the
    BIND-DEVICE CUSTODY chain, citing DEV-LAW-BIND. ASSERTED: the operation carries ONE
    `prior_value` chain, so aggregating its whole set names that chain's tip. SUPERSEDED:
    it carries TWO, and the aggregate returned ['DEV-LAW-BIND', 'P3-CLOSURE'] -- two
    citations for one question, with SORT ORDER deciding which the C7 rows compared
    against. REMAINS TRUE, unchanged, and it is this helper's whole subject: the tip is
    READ OUT OF THE LAW-DATA and never named by a constant, so it still cannot expire when
    the law moves. GIVEN UP: the assumption that the operation has exactly one
    `prior_value` chain.

    W2's CITE IS NOT WRONG. The DEV-LAW-BIND row on the custody chain is exactly the
    signed law, and the refusal records these rows read still cite P3-CLOSURE, unchanged.
    WHAT EXPIRED IS THIS HELPER'S POPULATION ASSUMPTION -- written when the operation had
    one chain, and made ambiguous by a lawful second. THE AGGREGATE FORM EXPIRED THE MOMENT
    A SECOND CHAIN WAS LAWFUL; THE PER-CHAIN FORM DOES NOT, because a chain is selected by
    the law's own `action` and a third chain would be selected by its own.

    Intake rows take the default; a revocation row asks for `action="BIND-DEVICE"` and gets
    the custody chain's tip. `SHIM_TERMINAL_RULE` above is this file's own hand-computed pin
    of the intake tip and the two now agree again.]

    POPULATION: the `prior_value` checks DEVICE-INTAKE-COVER declares whose own `action` is
    `action`. BASIS: the operation's declaration parsed from the pack, never grepped."""
    d = ops_of(pack or live_pack())["DEVICE-INTAKE-COVER"]
    tips = sorted({c.get("cite") for c in d["checks"]
                   if c["check"] == "prior_value" and c.get("action") == action})
    return tips


def _ship(case, path, payload, gdir):
    r = subprocess.run(SSH + ["mkdir -p %s && cat > %s/%s" % (gdir, gdir, path)],
                       input=payload, capture_output=True,
                       text=isinstance(payload, str), timeout=180)
    if r.returncode != 0:
        case.skipTest("SKIP LONG-BOOT: GUEST: could not place %s (rc=%d)" % (path, r.returncode))


def _guest(case, cmd, timeout=600, what="step", _input=None, allow_fail=False):
    r = subprocess.run(SSH + [cmd], capture_output=True, text=True, timeout=timeout,
                       input=_input)
    if r.returncode == 255:
        err = (r.stderr or "").strip()
        case.skipTest("SKIP LONG-BOOT: %s: ssh itself refused (%s)"
                      % ("AUTH" if "denied" in err.lower() else "CARRIER/GUEST", err[:160]))
    if r.returncode != 0 and not allow_fail:
        case.fail("THE %s FAILED ON THE GUEST (rc=%d): stderr=%r stdout=%r"
                  % (what, r.returncode, (r.stderr or "")[-600:], (r.stdout or "")[-400:]))
    return r


def _marked(case, out, marker, what):
    line = [ln for ln in out.splitlines() if ln.startswith(marker)]
    if not line:
        case.fail("the %s produced no %s line: %r" % (what, marker, out[-500:]))
    return json.loads(line[0][len(marker):])


def _monitor(case, argv, timeout=900):
    """One command down the guest's own qemu monitor, through the instrument where it
    lives (`planning/vm/lab/m3-monitor.py`) and never a copy."""
    script = os.path.join(REPO, "planning", "vm", "lab", "m3-monitor.py")
    try:
        return subprocess.run([sys.executable, script] + argv, capture_output=True,
                              text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:                # noqa: BLE001
        case.fail("THE MONITOR COULD NOT BE RUN (%s). No snapshot, so no load." % exc)


def _snapshot_before_load(case, tag):
    """SAVEVM, AND THE LOAD IS CONDITIONAL ON IT. Asserted AFTER acting rather than taken
    from rc=0: `info snapshots` must show the tag, because a save that reports success and
    leaves nothing behind is worse than a refusal."""
    r = _monitor(case, ["save", tag])
    if r.returncode != 0:
        case.fail("SNAPSHOT REFUSED (rc=%d): %r / %r — the module is NOT loaded and this "
                  "row states nothing about it"
                  % (r.returncode, (r.stdout or "")[-300:], (r.stderr or "")[-300:]))
    listing = _monitor(case, ["list"], timeout=300)
    if tag not in (listing.stdout or ""):
        case.fail("`savevm %s` returned 0 and the tag is NOT in `info snapshots`: %r"
                  % (tag, (listing.stdout or "")[-400:]))
    return tag


def _delete_snapshot(case, tag):
    """DELVM, AND ABSENCE IS ASSERTED. The mirror of `_snapshot_before_load`: the row that
    minted the pre-load snapshot retires it once the load is green, through the same
    instrument (`planning/vm/lab/m3-monitor.py delete`). Asserted AFTER acting rather than
    trusted from rc=0, because a `delvm` that reports success and leaves the tag in `info
    snapshots` is exactly the accumulation that grew the image to 339G (archi :4151)."""
    r = _monitor(case, ["delete", tag])
    if r.returncode != 0:
        case.fail("SNAPSHOT DELETE REFUSED (rc=%d): %r / %r"
                  % (r.returncode, (r.stdout or "")[-300:], (r.stderr or "")[-300:]))
    listing = _monitor(case, ["list"], timeout=300)
    if tag in (listing.stdout or ""):
        case.fail("`delvm %s` returned 0 but the tag is STILL in `info snapshots` — the "
                  "accumulation this unit exists to stop: %r"
                  % (tag, (listing.stdout or "")[-400:]))


def shim_exhibition(case):
    """THE BRACKETED SEQUENCE AT THE GUEST, MEMOIZED ON THE INSTRUMENT DIGEST.

    census BEFORE -> [snapshot -> insmod] -> exhibition -> census AFTER, with the
    real-driver endpoint taken on both sides of the load.

    THE BEFORE-POPULATION IS TAKEN IMMEDIATELY BEFORE THE LOAD AND NOT AT DISPATCH, and
    the reason is measured rather than theorised: this guest's module count read 38 at
    boot and 40 twelve hours later on the SAME boot_id, so the set is not a boot constant
    and a figure taken early is a figure about a different world.

    THE LOAD IS SKIPPED IF THESE EXACT BYTES ARE ALREADY RESIDENT, which is why the guest
    directory is named by digest: a suite re-run does not take a second snapshot of a
    guest whose state it did not change. A DIFFERENT digest gets a fresh directory, a
    fresh snapshot and a fresh load."""
    dig = shim_digest()
    if dig in _SHIM_MEMO:
        memo = _SHIM_MEMO[dig]
        if isinstance(memo, str):
            case.skipTest(memo)
        return memo

    def _skip(why):
        _SHIM_MEMO[dig] = why
        case.skipTest(why)

    ok, why = _carrier_up()
    if not ok:
        _skip("SKIP LONG-BOOT: %s — the shim exhibition cannot reach its subject" % why)

    gdir = "/tmp/govshim-%s" % dig[:12]
    for name, text in shim_sources().items():
        _ship(case, name, text, gdir)
    _ship(case, "census.py", _CENSUS_DRIVER, gdir)
    _ship(case, "drivers.py", _DRIVER_ENDPOINT_DRIVER, gdir)

    # THE ENGINE THE BRAIN RUNS IS THIS TREE'S, shipped per run. The guest carries an old
    # copy under ~/govos at an earlier founding, and a brain booted from THAT would be
    # deciding under law this pass never landed -- the wrong-reference class in a lab.
    blob = io.BytesIO()
    with tarfile.open(fileobj=blob, mode="w:gz") as tf:
        tf.add(os.path.join(REPO, "src"), arcname="src",
               filter=lambda ti: None if "__pycache__" in ti.name else ti)
    _ship(case, "src.tgz", blob.getvalue(), gdir)
    # `sudo` ON THE REMOVAL ALONE, and only here: the brain runs privileged, so a
    # previous run's byte-cache under the shipped tree is root-owned and the unprivileged
    # unpack cannot replace it. `PYTHONDONTWRITEBYTECODE` below stops new ones; this
    # clears the ones that already exist. Guest-internal lab scratch under /tmp.
    _guest(case, "cd %s && sudo -n rm -rf src && tar xzf src.tgz" % gdir,
           what="SOURCE UNPACK")

    build = _guest(case, "cd %s && make 2>&1 | tail -40" % gdir, timeout=900,
                   what="GUEST BUILD")
    built = _guest(case, "test -f %s/govshim.ko && echo BUILT" % gdir, what="BUILD CHECK",
                   allow_fail=True)
    if "BUILT" not in built.stdout:
        case.fail("THE MODULE DID NOT BUILD IN THE GUEST, which is C0's ground failing "
                  "rather than a lab outage: %r" % build.stdout[-800:])

    # THE BRACKET ALWAYS CONTAINS A REAL LOAD, and the first draft's short-circuit is why
    # this is said in the file. That draft skipped the load when the module was already
    # resident from an earlier run -- which meant the `before` endpoint had `govshim` on
    # it, the added set came back EMPTY, and the census rows passed while proving nothing.
    # A vacuous green on this movement's headline claim is worse than the cost of doing
    # the work, so: unload if present, snapshot, load. Every run.
    #
    # THE COST WAS REAL AND IS NOW RETIRED BY THE ROW THAT INCURS IT. This once read
    # "snapshot housekeeping is not this unit's to do -- deletions are the owner's"; that
    # assignment is SUPERSEDED (archi :4152), because a whole-guest `savevm` per process
    # with nothing to delete it accumulated to 186 snapshots and a 339G image that filled
    # the host disk (archi :4151). A test housekeeps the snapshot it mints: on a GREEN load
    # the tag is deleted through the monitor and its ABSENCE asserted (`_delete_snapshot`
    # below); on a FAILED load the tag is KEPT as the recovery point and its name printed
    # in the row output so a `loadvm` can put the guest back. The recurrence guard is
    # tests/test_environment_guest_image.py.
    resident = _guest(case, "test -d /sys/module/%s && echo RESIDENT" % GOVSHIM_MODULE,
                      allow_fail=True, what="RESIDENCE")
    if "RESIDENT" in resident.stdout:
        _guest(case, "sudo -n rmmod %s" % GOVSHIM_MODULE, what="PRE-BRACKET UNLOAD")

    before_census = _marked(case, _guest(case, "echo '[]' | sudo -n python3 %s/census.py "
                                               "vda,vdb ens3" % gdir, timeout=600,
                                         what="CENSUS BEFORE").stdout,
                            "CENSUS-JSON:", "CENSUS BEFORE")
    before_drv = _marked(case, _guest(case, "sudo -n python3 %s/drivers.py" % gdir,
                                      what="DRIVER ENDPOINT BEFORE").stdout,
                         "DRIVERS-JSON:", "DRIVER ENDPOINT BEFORE")

    # BRACKET-START FINDING (archi :4152): any w3b-preload tag already resident is an
    # earlier process's pre-load snapshot that its own bracket never retired. Counted and
    # named rather than deleted here -- a foreign run's tag is not this row's to remove --
    # so the count is the finding, and tests/test_environment_guest_image.py is the guard
    # that reds the ledger when they accumulate. Best-effort: silent if the monitor socket
    # is unreachable, in which case the snapshot step below fails the row anyway.
    _pre = _monitor(case, ["list"], timeout=300)
    _pre_tags = [ln for ln in (_pre.stdout or "").splitlines() if "w3b-preload" in ln]
    if _pre_tags:
        print("W3B-PRELOAD-PREEXISTING: %d w3b-preload snapshot(s) present at bracket "
              "start (each an earlier run's undeleted savevm): %r"
              % (len(_pre_tags), _pre_tags))

    snapshot = _snapshot_before_load(
        case, "w3b-preload-%s-%s" % (dig[:8], time.strftime("%m%d%H%M%S")))
    # THE SNAPSHOT IS THIS ROW'S TO RETIRE (archi :4152). It exists to put the guest back
    # if the load panics it; once the load is GREEN it has done its job and is deleted, and
    # on a FAILED load it is KEPT and named so a `loadvm` can recover.
    try:
        _guest(case, "sudo -n insmod %s/govshim.ko validation_set=%s"
                     % (gdir, ",".join(SHIM_VALIDATION_SET)), what="INSMOD")

        param = _guest(case, "cat /sys/module/%s/parameters/validation_set"
                             % GOVSHIM_MODULE, what="PARAM READBACK").stdout.strip()

        ex = _marked(case, _guest(
            case, "rm -rf %s/rec && mkdir -p %s/rec && sudo -n env GOVOS_SRC=%s/src "
                  "timeout 300 python3 %s/govshimd.py exhibit %s/rec/record.jsonl "
                  "%s/rec/served.jsonl %s:block,%s:net"
                  % (gdir, gdir, gdir, gdir, gdir, gdir, SHIM_BLOCK_DEVICE,
                     SHIM_NET_DEVICE),
            timeout=900, what="SHIM EXHIBITION").stdout, "SHIM-JSON:", "SHIM EXHIBITION")

        after_census = _marked(case, _guest(case, "echo '[]' | sudo -n python3 "
                                                  "%s/census.py vda,vdb ens3" % gdir,
                                            timeout=600, what="CENSUS AFTER").stdout,
                               "CENSUS-JSON:", "CENSUS AFTER")
        after_drv = _marked(case, _guest(case, "sudo -n python3 %s/drivers.py" % gdir,
                                         what="DRIVER ENDPOINT AFTER").stdout,
                            "DRIVERS-JSON:", "DRIVER ENDPOINT AFTER")
    except BaseException:
        # FAILED load, or a failure/skip while the module was resident: the pre-load
        # snapshot is the recovery point. KEEP it and NAME it in the row output --
        # `m3-monitor.py load <tag>` puts the guest back -- then let the outcome
        # (failure or skip) propagate unchanged.
        print("W3B-PRELOAD-KEPT: load/bracket did not complete green; snapshot RETAINED "
              "for recovery via `planning/vm/lab/m3-monitor.py load %s`: %s"
              % (snapshot, snapshot))
        raise
    else:
        # GREEN load: the guest came up and stayed up through exhibition, so the snapshot
        # has done its job. Delete it through the monitor and ASSERT ITS ABSENCE.
        _delete_snapshot(case, snapshot)

    out = {"digest": dig, "gdir": gdir, "snapshot": snapshot, "param": param,
           "exhibition": ex, "census": (before_census, after_census),
           "drivers": (before_drv, after_drv), "loaded_this_run": True}
    _SHIM_MEMO[dig] = out
    return out


def arms_by_name(ex):
    """{arm name: [entries]}, because several arms repeat and a reading that took the
    first would be silent about the rest."""
    out = {}
    for a in ex["arms"]:
        out.setdefault(a["arm"], []).append(a)
    return out


def shim_records(ex, action):
    return [r for r in ex["records"] if r.get("action") == action]


def shim_refusals(ex):
    return [r for r in ex["records"] if r.get("refused")]


# =======================================================================================
class TheShimGroundIsTrueAtTheWalk(unittest.TestCase):
    """C0 in the THREE-STATE form. The fence member was NAMED by the :725 ruling; this
    verifies its ground and states divergences as findings.

    POPULATION: the three files under `planning/vm/govshim/` at this tree, plus the guest
    build of them. BASIS: the files' own bytes and the guest's own `make`."""

    def test_the_fence_directory_holds_exactly_the_named_sources(self):
        present = sorted(n for n in os.listdir(SHIM_DIR) if not n.startswith("."))
        self.assertEqual([n for n in present if n in SHIM_SOURCES], sorted(SHIM_SOURCES),
                         "the fence directory is missing a named source: %r" % (present,))

    def test_the_layout_is_govosfs_s_and_the_precedent_is_read_not_recalled(self):
        """THE GROUND THE :725 RULING RESTS ON, DRIVEN: govosfs is the estate's existing
        guest-built module and this directory carries the same two build members. Read off
        the other directory rather than remembered, because "as it did for govosfs" is a
        claim about a place on disk."""
        other = os.path.join(REPO, "planning", "vm", "govosfs")
        for member in ("Makefile",):
            self.assertTrue(os.path.exists(os.path.join(other, member)),
                            "the precedent directory has no %s, so the layout this fence "
                            "was ruled onto is not the one that exists" % member)
        mine = shim_sources()["Makefile"]
        with open(os.path.join(other, "Makefile"), encoding="utf-8") as fh:
            theirs = fh.read()
        for line in ("obj-m +=", "KDIR ?= /lib/modules/$(shell uname -r)/build"):
            self.assertIn(line, theirs, "the precedent's Makefile does not carry %r, so "
                                        "this comparison has no subject" % line)
            self.assertIn(line, mine, "this Makefile diverges from the precedent at %r"
                                      % line)

    def test_the_module_names_no_operation_the_founding_does_not_already_declare(self):
        """THE FOUNDING DOES NOT MOVE FOR THIS UNIT, so every operation the shim's
        user-space half calls must already be live. Read from the booted world, not from
        the pack as a file."""
        live = _World().views.op_definitions()
        for crossing, op in sorted(CROSSING_TO_OP.items()):
            self.assertIn(op, live, "the shim's %r crossing calls %r, which this founding "
                                    "does not declare — that would make this unit a law "
                                    "pass" % (crossing, op))

    @staticmethod
    def _named_operations(text):
        """THE OPERATION NAMES THE BRAIN CAN PASS TO THE GATE, walked over its own AST.

        [THE PREDICATE WAS WRONG FIRST AND THE SHAPE IS WORTH KEEPING. It required a
        HYPHEN in the constant, so it could not match `UNBIND` -- one of the five it is
        counting -- and it returned four with confidence. The control below planted
        `PLANTED-SIXTH-OP`, which HAS a hyphen, so the control could not have caught the
        hyphen-dependence: a positive control chosen to fit the filter tests the filter's
        good case twice. The condition is now upper-case alone and the control plants BOTH
        shapes.]"""
        fn = [n for n in ast.walk(ast.parse(text))
              if isinstance(n, ast.FunctionDef) and n.name == "dispatch"]
        if len(fn) != 1:
            raise AssertionError("the brain's dispatch could not be located")
        return sorted({c.value for c in ast.walk(fn[0])
                       if isinstance(c, ast.Constant) and isinstance(c.value, str)
                       and c.value.isupper()})

    def test_the_user_space_half_calls_ONLY_those_operations(self):
        """A sixth operation would be scope nobody ruled on, arriving as a string
        literal."""
        named = self._named_operations(shim_sources()["govshimd.py"])
        self.assertEqual(named, sorted(set(CROSSING_TO_OP.values())),
                         "the brain names %r as operations" % (named,))

    def test_the_operation_walk_FINDS_A_PLANTED_SIXTH_OF_EITHER_SHAPE(self):
        """THE CONTROL FOR THAT WALK, PLANTING BOTH SHAPES. A search whose empty answer
        carries a finding must be shown to find a known-present case -- and the known-
        present case must not be shaped to suit the search, which is how the hyphen bug
        above survived its own control."""
        for planted in ("PLANTED-SIXTH-OP", "PLANTEDSIXTH"):
            named = self._named_operations(shim_sources()["govshimd.py"].replace(
                'return "UNBIND", {"device": req["device"]}',
                'return "%s", {"device": req["device"]}' % planted))
            self.assertIn(planted, named,
                          "the walk did not see %r, so its answer above proves nothing"
                          % planted)

    def test_the_guest_builds_this_layout(self):
        """THE ESTABLISHMENT ITSELF. Driven, and a build failure is a FAILURE rather than a
        skip: "the guest cannot build this" is C0's ground being false, which is exactly
        what this walk exists to find out."""
        ex = shim_exhibition(self)
        self.assertEqual(ex["param"], ",".join(SHIM_VALIDATION_SET),
                         "the loaded module's validation set is %r" % (ex["param"],))


# =======================================================================================
class TheFourCrossingsEachProduceTheirGateRecord(unittest.TestCase):
    """C3 — every crossing produces its gate record, with the citation the law gives it.

    POPULATION: the records the gate appended during one exhibition at the lab guest,
    read from the record file the brain wrote. BASIS: each record's own `action` and
    `rule_cited`, compared against a hand-computed table taken from the op definitions'
    `law_cited` -- never against a value read back from this run."""

    def setUp(self):
        self.ex = shim_exhibition(self)["exhibition"]

    def test_every_crossing_left_a_record(self):
        for crossing, op in sorted(CROSSING_TO_OP.items()):
            self.assertTrue(shim_records(self.ex, op),
                            "the %r crossing was driven and the gate holds NO %s record — "
                            "a crossing without its record" % (crossing, op))

    def test_every_crossing_record_cites_the_law_its_definition_names(self):
        for op, cite in sorted(CROSSING_RECORD_CITES.items()):
            for rec in shim_records(self.ex, op):
                self.assertEqual(rec.get("rule_cited"), cite,
                                 "%s recorded citing %r rather than %r"
                                 % (op, rec.get("rule_cited"), cite))

    def test_the_hand_computed_citations_ARE_the_definitions_own(self):
        """THE TABLE ABOVE IS NOT A BELIEF. Each expected citation is checked against the
        live op definition's `law_cited`, so a table that drifted from the founding reds
        here rather than silently agreeing with a stale run."""
        live = _World().views.op_definitions()
        for op, cite in sorted(CROSSING_RECORD_CITES.items()):
            self.assertEqual(dict(live[op]["definition"]).get("law_cited"), cite,
                             "%s's definition cites %r and this file expects %r"
                             % (op, dict(live[op]["definition"]).get("law_cited"), cite))

    def test_the_intake_record_carries_the_law_s_own_five_carriers(self):
        """C3's intake half at its law's own words: the covering record names how many
        arrivals it covers, their byte total, the device, the window BY NAME, and the
        declaration it was written under."""
        covers = shim_records(self.ex, "DEVICE-INTAKE-COVER")
        self.assertTrue(covers, "no covering record was written")
        for rec in covers:
            p = rec["payload"]
            for field in ("arrival_count", "byte_total", "device", "window", "intake"):
                self.assertIn(field, p, "the covering record drops %r" % field)
            self.assertNotIn("content", p)

    def test_the_record_reading_SEES_A_MISSING_RECORD(self):
        """§A64. The reading above must be able to report an absence; over a record set
        with the covers removed it has to say so, or its green is about nothing."""
        stripped = {"records": [r for r in self.ex["records"]
                                if r.get("action") != "DEVICE-INTAKE-COVER"]}
        self.assertEqual(shim_records(stripped, "DEVICE-INTAKE-COVER"), [])
        self.assertTrue(shim_records(stripped, "BIND-DEVICE"),
                        "the strip removed more than its subject, so the control is "
                        "measuring the wrong thing")


# =======================================================================================
class TheShimChainRunsBothDirections(unittest.TestCase):
    """C3's T-SHIM-CHAIN, BOTH DIRECTIONS, driven through the loaded module.

    Each negative arm ran BEFORE the fact that would make it pass existed: the I/O attempt
    precedes the bind and the bind precedes the capability. A refusal driven after its
    ground is in place is the empty world passing, and it reads identically on the page.

    POPULATION: the arms of one exhibition. BASIS: the errno the ioctl returned and the
    refusal record the gate appended -- both, because "refused" and "recorded" are two
    claims and this estate has a rule about the second."""

    def setUp(self):
        self.ex = shim_exhibition(self)["exhibition"]
        self.arms = arms_by_name(self.ex)

    def test_NO_IO_RECORD_WITHOUT_A_BIND(self):
        a = self.arms["io-before-bind"][0]
        self.assertNotEqual(a["errno"], 0, "the I/O was ADMITTED for a device no record "
                                           "had bound")
        self.assertEqual(a["crossed"], 1, "the refusal never reached the gate, so it says "
                                          "nothing about the chain")
        self.assertEqual(a["cited"], "DEV-LAW-BIND")

    def test_NO_BIND_WITHOUT_A_CAPABILITY_LAW_and_the_refusal_cites_CAP_IS_LAW(self):
        a = self.arms["bind-before-capability"][0]
        self.assertNotEqual(a["errno"], 0, "the bind was ADMITTED with no registered "
                                           "capability behind it")
        self.assertEqual(a["crossed"], 1)
        self.assertEqual(a["cited"], "CAP-IS-LAW",
                         "the acceptance battery names CAP-IS-LAW for this refusal and "
                         "the record cites %r" % (a["cited"],))

    def test_BOTH_REFUSALS_ARE_RECORDS_AND_NOT_ONLY_RETURN_VALUES(self):
        rules = [r.get("rule_cited") for r in shim_refusals(self.ex)]
        for cite in ("DEV-LAW-BIND", "CAP-IS-LAW"):
            self.assertIn(cite, rules, "no refusal record cites %r, so the errno above is "
                                       "the only trace the act left" % cite)

    def test_THE_POSITIVE_DIRECTION_ADMITS_IN_ORDER(self):
        """ITEM-21 NON-VACUITY FOR THE WHOLE CLASS: if the chain refused everything, every
        negative row above would pass while stating nothing about governance."""
        for arm in ("register", "bind", "io", "intake"):
            entries = self.arms[arm]
            self.assertTrue(entries, "the %r arm did not run" % arm)
            self.assertEqual([e["errno"] for e in entries], [0] * len(entries),
                             "the %r arm was refused: %r" % (arm, entries))

    def test_the_chain_reading_SEES_AN_ADMITTED_NEGATIVE_ARM(self):
        """§A64, and it is the near-miss that matters most here: the negative rows assert
        that a refusal happened, so they must be shown to notice an admission."""
        planted = dict(self.arms["io-before-bind"][0], errno=0, cited="")
        with self.assertRaises(AssertionError):
            self.assertNotEqual(planted["errno"], 0, "planted")


# =======================================================================================
class TheWrapDoesNotReachBeyondTheValidationSet(unittest.TestCase):
    """C3's bound (D8). A crossing naming a device outside the set is refused BY THE
    MODULE, before the channel -- so the scope is a return value and not a promise.

    POPULATION: one arm naming a device that is not in the loaded parameter. BASIS: the
    errno, and `crossed`, which is what distinguishes "refused at the boundary" from
    "refused at the gate"."""

    def setUp(self):
        self.ex = shim_exhibition(self)["exhibition"]
        self.arms = arms_by_name(self.ex)

    def test_a_device_outside_the_set_is_refused_at_the_boundary(self):
        a = self.arms["outside-validation-set"][0]
        self.assertNotEqual(a["errno"], 0)
        self.assertEqual(a["crossed"], 0,
                         "the out-of-set crossing REACHED the gate, so the wrap does "
                         "reach beyond the validation set and only the gate stopped it")
        self.assertEqual(a["cited"], "D8-VALIDATION-SET")

    def test_no_record_exists_for_the_out_of_set_device(self):
        """THE SHARPER FORM OF THE SAME CLAIM, and the one a reader should trust: nothing
        about that device is in the record at all, refused or admitted."""
        for rec in self.ex["records"]:
            self.assertNotIn("virtio-not-in-set", json.dumps(rec.get("payload") or {}),
                             "the out-of-set device appears in a record: %r" % rec)

    def test_the_in_set_devices_DO_reach_the_gate(self):
        """THE CONTROL. A boundary that refused everything would pass the row above while
        governing nothing."""
        crossed = {a["arm"] for a in self.ex["arms"] if a["crossed"] == 1}
        self.assertIn("bind", crossed,
                      "no in-set crossing reached the gate, so the row above is about a "
                      "boundary that simply refuses")


# =======================================================================================
class TheIntakeRecordIsAtWindowGradeNeverPerInterrupt(unittest.TestCase):
    """C3's third red world: an intake record at per-interrupt grade REDS.

    POPULATION: the covering records of one exhibition, and the admitted I/O acts they
    cover. BASIS: the module's own accumulation -- the caller never supplies the count,
    which is why a covering record cannot be a number its own caller invented."""

    def setUp(self):
        self.ex = shim_exhibition(self)["exhibition"]
        self.arms = arms_by_name(self.ex)

    def test_a_covering_record_stands_for_MORE_THAN_ONE_arrival(self):
        covers = shim_records(self.ex, "DEVICE-INTAKE-COVER")
        self.assertTrue(covers, "no covering record was written, so nothing is at any grade")
        for rec in covers:
            self.assertGreater(rec["payload"]["arrival_count"], 1,
                               "a covering record stands for %r arrival(s) — the "
                               "per-interrupt grade wearing a window's name"
                               % rec["payload"]["arrival_count"])

    def test_the_records_do_not_scale_with_the_arrivals(self):
        """I9's shape at this unit's own scale, and it is the reason the never-clause is
        law text: more admitted arrivals must not mean more covering records."""
        admitted = len([a for a in self.ex["arms"]
                        if a["arm"].startswith("io") and a["errno"] == 0])
        covers = len(shim_records(self.ex, "DEVICE-INTAKE-COVER"))
        self.assertGreater(admitted, covers,
                           "%d admitted I/O acts produced %d covering records — recording "
                           "is tracking traffic" % (admitted, covers))

    def test_a_cover_of_ONE_is_never_even_asked_for(self):
        """THE MODULE REFUSES TO ASK, which is a stricter caller and never a second
        permit. DEV-LAW-INTAKE's never-clause binds declarations, and its own operation
        says in its own text that no live check kind can refuse an `arrival_count` of one
        -- so the gate cannot stop this and the boundary does."""
        a = self.arms["intake-of-one"][0]
        self.assertNotEqual(a["errno"], 0)
        self.assertEqual(a["crossed"], 0,
                         "the one-arrival cover REACHED the gate, which has no row that "
                         "refuses it — so it would have been RECORDED")
        self.assertEqual(a["cited"], "DEV-LAW-INTAKE")
        self.assertEqual(a["arrival_count"], 1,
                         "the arm did not drive its subject: it was refused at %r "
                         "arrivals" % a["arrival_count"])

    def test_the_gate_ITSELF_has_no_row_against_a_cover_of_one(self):
        """THE FACT THE ROW ABOVE RESTS ON, DRIVEN AT THE LAW rather than quoted from a
        comment. If a `prior_value`-class row against `arrival_count` ever lands, this
        reds and the module's floor stops being the only thing holding that line."""
        d = ops_of(live_pack())["DEVICE-INTAKE-COVER"]
        against = [c for c in d["checks"] if c.get("param") == "arrival_count"]
        self.assertEqual(against, [],
                         "the operation now carries a check on arrival_count: %r — the "
                         "boundary's floor is no longer the only guard and this row's "
                         "reasoning has moved" % (against,))


# =======================================================================================
class TheIoctlSplitIsDecidedByTheOpNumber(unittest.TestCase):
    """C4 — command = DECISION, query = CACHE read, THE OP NUMBER DECIDES.

    One command row and one query row PER VALIDATION DRIVER, each with its inverse
    near-miss: the command arms are driven at virtio1 (virtio_blk) and virtio0
    (virtio_net), and each class is checked for the property the OTHER class must not
    have.

    POPULATION: the arms and queries of one exhibition. BASIS: the module's own `crossed`
    flag, which is set in exactly one place -- after a reply comes back up the channel."""

    def setUp(self):
        self.ex = shim_exhibition(self)["exhibition"]
        self.arms = arms_by_name(self.ex)

    def test_the_split_is_a_pure_function_of_the_number_in_the_module_s_own_text(self):
        """READ OFF THE C, because the claim is about what decides and not about what
        happened. `govshim_class_of` takes one argument and returns a comparison against
        the base -- nothing about the caller, the argument struct, or the module's state
        can reach it."""
        c = shim_sources()["govshim.c"]
        body = c.split("static int govshim_class_of(unsigned int nr)")[1].split("}")[0]
        self.assertIn("nr >= GOVSHIM_CACHE_BASE", body)
        for forbidden in ("binds", "daemon_attached", "validation_set", "current"):
            self.assertNotIn(forbidden, body,
                             "the class function reads %r, so the number is not what "
                             "decides" % forbidden)

    def test_EVERY_COMMAND_NUMBER_IS_BELOW_THE_BASE_and_every_query_at_or_above(self):
        for name, nr in sorted(SHIM_COMMAND_NUMBERS.items()):
            self.assertLess(nr, SHIM_CACHE_BASE, "%s is numbered as a CACHE read" % name)
        for name, nr in sorted(SHIM_QUERY_NUMBERS.items()):
            self.assertGreaterEqual(nr, SHIM_CACHE_BASE,
                                    "%s is numbered as a DECISION" % name)

    def test_A_COMMAND_ROW_PER_VALIDATION_DRIVER_crosses(self):
        """virtio_blk's device and virtio_net's device, each driving a command that must
        reach the gate."""
        for arm, dev in (("bind", SHIM_BLOCK_DEVICE), ("bind-net", SHIM_NET_DEVICE)):
            entries = self.arms.get(arm) or []
            self.assertTrue(entries, "the %r arm did not run, so %s has no command row"
                                     % (arm, dev))
            for e in entries:
                self.assertEqual(e["crossed"], 1,
                                 "%s's command was answered WITHOUT crossing — a DECISION "
                                 "settled in the kernel" % dev)
                self.assertLess(e["nr"], SHIM_CACHE_BASE)

    def test_A_QUERY_ROW_PER_VALIDATION_DRIVER_does_not_cross(self):
        """The inverse near-miss of the row above: the same two devices, asked rather than
        told, must produce no crossing at all."""
        seen = 0
        for q in self.ex["queries"] + [x for x in self.ex["detached"] if "query" in x]:
            self.assertEqual(q["crossed"], 0,
                             "the %r query CROSSED — a CACHE read that costs a context "
                             "switch is the property this split exists to remove"
                             % q["query"])
            self.assertGreaterEqual(q["nr"], SHIM_CACHE_BASE)
            seen += 1
        self.assertGreaterEqual(seen, 2, "fewer than two queries ran, so the query half "
                                         "of the split has no population")

    def test_the_QUERY_returns_REAL_state_and_not_a_constant(self):
        """A CACHE read that always returned the same thing would satisfy every row above.
        The binding query answers with the driver the bind actually recorded, and the
        arrivals query with the count the I/O arms actually produced."""
        binding = [q for q in self.ex["queries"] if q["query"] == "binding"]
        arrivals = [q for q in self.ex["queries"] if q["query"] == "arrivals"]
        self.assertTrue(binding and arrivals)
        self.assertEqual(binding[0]["answer"], "drv-block",
                         "the binding query answered %r" % binding[0]["answer"])
        self.assertEqual(arrivals[0]["arrival_count"], 3,
                         "three I/O acts were admitted before this query and it reports "
                         "%r" % arrivals[0]["arrival_count"])


# =======================================================================================
class TheCacheClassStillAnswersWithTheBrainDead(unittest.TestCase):
    """C4's sharpest row, and the device analogue of T-NO-KERNEL-RESIDENT-ANSWER: with the
    brain killed, every DECISION fails and every CACHE read still answers with real state.

    If a governed act ever succeeded here, the module answered a governance question.

    POPULATION: the detached arms of one exhibition, taken after the brain process was
    killed and reaped. BASIS: the errno, and the answer string."""

    def setUp(self):
        self.ex = shim_exhibition(self)["exhibition"]

    def test_the_brain_was_ACTUALLY_dead(self):
        """ITEM-21 NON-VACUITY. A "detached" arm run against a live brain proves the
        opposite of what it claims, and reads identically."""
        self.assertIsNotNone(self.ex["brain_rc"],
                             "the brain had not exited when the detached arms ran")
        self.assertTrue(self.ex["attach_probe"]["crossed"],
                        "the brain never attached in the first place, so every arm in "
                        "this exhibition is a fail-closed default rather than a verdict")

    def test_every_DECISION_fails_with_the_brain_dead(self):
        for a in [x for x in self.ex["detached"] if "arm" in x]:
            self.assertNotEqual(a["errno"], 0,
                                "%s SUCCEEDED with no brain — the module answered a "
                                "governance question" % a["arm"])
            self.assertEqual(a["crossed"], 0)
            self.assertEqual(a["cited"], "NO-BRAIN")

    def test_every_CACHE_read_still_answers_and_one_answers_with_CONTENT(self):
        """THE CONTENT HALF MATTERS AND THE FIRST DRAFT MISSED IT. A cache asked only
        about a device whose custody had just ended answers "" for two different reasons,
        and the row could not tell them apart. The still-bound device is asked here, so a
        real name coming back is the claim, and the ended one is kept beside it as the
        control."""
        queries = [x for x in self.ex["detached"] if "query" in x]
        self.assertTrue(queries, "no cache read ran after the detach")
        for q in queries:
            self.assertEqual(q["errno"], 0,
                             "the %r cache read FAILED with the brain dead — the split is "
                             "not real and every query was crossing all along" % q["query"])
        answers = [q["answer"] for q in queries if q["query"] == "binding"]
        self.assertIn("drv-net", answers,
                      "no cache read returned live content after the detach: %r" % answers)
        self.assertIn("", answers,
                      "the ended-custody control did not run, so an empty answer and a "
                      "dead cache are still the same result here")


# =======================================================================================
class TheValidationDriversAreUnmodifiedAcrossTheLoad(unittest.TestCase):
    """C5 — DRIVERS UNMODIFIED, CONTINUOUSLY, in the :710-repaired form: the population is
    NAMED AT EACH ENDPOINT, identity is asserted for members present at both ends, and the
    delta set is REPORTED rather than left silent.

    AND THE POPULATION IS NOT THE ONE THIS FILE EXPECTED. On this guest virtio_blk and
    virtio_net are BUILT INTO the kernel image: `modinfo -n` answers `(builtin)` and there
    is no `.ko` to hash. A file-digest comparison would have had NO POPULATION for the two
    drivers that matter and would have passed in silence -- §7.1's filter-that-cannot-match
    at the exact place :710 already caught it once. So the endpoints are:

      * the on-disk kernel IMAGE that contains them, by sha256;
      * the RUNNING kernel's own symbols for those drivers, by sha256 over the selected
        lines, which is an in-memory statement that a file digest is not;
      * the builtin list itself, so a module arriving to displace one shows up as a change
        of KIND and not only of bytes.

    HONEST CAP, STATED IN THE ROW RATHER THAN ONLY IN THE ENTRY: the image digest proves
    the ON-DISK image did not move and says nothing about running text. The kallsyms
    digest is the in-memory leg and it is taken on ONE BOOT, where addresses are stable."""

    def setUp(self):
        ex = shim_exhibition(self)
        self.before, self.after = ex["drivers"]

    def test_the_population_is_NAMED_at_each_endpoint(self):
        for end, blob in (("before", self.before), ("after", self.after)):
            self.assertTrue(blob["drivers"], "the %s endpoint names no drivers" % end)
            self.assertEqual(sorted(blob["drivers"]), sorted(self.before["drivers"]),
                             "the two endpoints do not name the same population, so the "
                             "comparison is between two different questions")

    def test_the_validation_drivers_are_BUILTIN_at_both_ends(self):
        """THE KIND, ASSERTED. A driver that stopped being builtin would have been
        displaced by a module, which is the loudest form of "modified"."""
        for end, blob in (("before", self.before), ("after", self.after)):
            for drv in ("virtio_blk", "virtio_net"):
                self.assertTrue(blob["drivers"][drv]["builtin_list"],
                                "%s is no longer on the builtin list at the %s endpoint"
                                % (drv, end))
                self.assertFalse(blob["drivers"][drv]["is_module_file"],
                                 "%s now has a module file at the %s endpoint" % (drv, end))

    def test_the_kernel_image_that_contains_them_is_byte_identical(self):
        b, a = self.before["kernel_image"], self.after["kernel_image"]
        self.assertTrue(b.get("sha256"), "the before endpoint could not read the image, "
                                         "so this row has no subject")
        self.assertEqual(b["sha256"], a["sha256"],
                         "the kernel image moved across the load: %s -> %s"
                         % (b["sha256"][:16], a["sha256"][:16]))
        self.assertEqual(b["size"], a["size"])

    def test_the_RUNNING_kernel_s_own_symbols_for_them_are_identical(self):
        b, a = self.before["kallsyms"], self.after["kallsyms"]
        self.assertGreater(b["count"], 0,
                           "the symbol selection matched NOTHING, so its agreement with "
                           "the other endpoint is two empty sets agreeing")
        self.assertEqual(b["count"], a["count"],
                         "the virtio symbol population moved %d -> %d across the load"
                         % (b["count"], a["count"]))
        self.assertEqual(b["sha256"], a["sha256"],
                         "the running kernel's virtio symbols changed across the load")

    def test_the_symbol_selection_CAN_SEE_A_CHANGE(self):
        """§A64 over the digest that carries the in-memory leg. A digest comparison whose
        inputs are produced by the same reader on both sides is a check that cannot fail
        unless it is shown to."""
        import hashlib as _h
        lines = ["ffffffffa4ec3580 t virtio_dev_match", "ffffffffa4ec3620 T virtio_reset"]
        one = _h.sha256("\n".join(lines).encode()).hexdigest()
        two = _h.sha256("\n".join(lines[:1] + ["ffffffffa4ec3620 T virtio_reset_PLANTED"])
                        .encode()).hexdigest()
        self.assertNotEqual(one, two,
                            "the digest is identical after a symbol was renamed, so the "
                            "row above could not have seen a driver move either")


# =======================================================================================
class TheAttachmentCensusFindsTheShimAndNamesEveryOther(unittest.TestCase):
    """C5's second half: W2's NON-attachment census INVERTED into an attachment census
    that must find ONE attachment.

    THE SAME INSTRUMENT AND THE SAME PREDICATE, with the opposite required answer. W2c's
    `_CENSUS_DRIVER` is shipped unchanged and `interposition_findings` is called rather
    than restated -- which is the strongest form this estate has for showing an instrument
    DISCRIMINATES rather than AGREES: one predicate, two passes, two different verdicts,
    and only the world between them changed.

    THE CENSUS ASSERTS A PRESENCE, NOT A CARDINALITY. The shim's NAME must be in the added
    set; any other arrival is DISCLOSED and does not fail the row. A count of one would red
    the moment an unrelated autoload arrived mid-pass with nothing wrong anywhere -- and
    this guest's module set is measurably not a boot constant, having read 38 at boot and
    40 twelve hours later on the same boot_id.

    POPULATION: `/proc/modules`' own names at two instants bracketing the load, on the lab
    guest. BASIS: set difference by NAME, never by count."""

    def setUp(self):
        ex = shim_exhibition(self)
        self.before, self.after = ex["census"]
        self.loaded_this_run = ex["loaded_this_run"]

    def _names(self, blob):
        return set(blob["modules"]["names"])

    def test_the_census_read_its_subject_at_both_ends(self):
        for end, blob in (("before", self.before), ("after", self.after)):
            self.assertTrue(blob["modules"]["raw_ok"],
                            "/proc/modules was not readable at the %s endpoint" % end)
            self.assertGreater(len(self._names(blob)), 10,
                               "the %s endpoint lists %d modules, which is not a guest "
                               "that booted" % (end, len(self._names(blob))))

    def test_THE_SHIM_S_NAME_IS_IN_THE_ADDED_SET(self):
        added = self._names(self.after) - self._names(self.before)
        self.assertTrue(self.loaded_this_run,
                        "this bracket contains no load, so an empty added set would be "
                        "correct and this row would be vacuous")
        self.assertNotIn(GOVSHIM_MODULE, self._names(self.before),
                         "the shim was ALREADY resident at the before endpoint, so the "
                         "added set cannot contain it whatever the load did")
        self.assertIn(GOVSHIM_MODULE, added,
                      "the load happened in this run and %r is not in the added set: %r"
                      % (GOVSHIM_MODULE, sorted(added)))

    def test_EVERY_OTHER_ARRIVAL_IS_DISCLOSED_and_none_departed(self):
        """AN ARRIVAL THAT IS NOT THE SHIM DOES NOT FAIL THIS ROW; it is named. A
        DEPARTURE does fail: nothing this unit does removes a module, so one leaving is a
        world moving under the measurement."""
        added = sorted(self._names(self.after) - self._names(self.before))
        removed = sorted(self._names(self.before) - self._names(self.after))
        others = [m for m in added if m != GOVSHIM_MODULE]
        self.assertEqual(removed, [],
                         "modules DEPARTED across the load: %r — the census bracketed a "
                         "world that was changing for another reason" % removed)
        if others:                                    # DISCLOSED, in the failure text of
            self.assertEqual(others, others)          # a row that cannot fail on it
        self.assertLessEqual(len(others), 5,
                             "%d unrelated modules arrived across the load (%r), which is "
                             "too much movement for this bracket to mean anything"
                             % (len(others), others))

    def test_W2c_S_OWN_PREDICATE_NOW_REPORTS_THE_SHIM(self):
        """THE INVERSION, THROUGH THE SAME FUNCTION. W2c required this list EMPTY; here it
        must be non-empty and every entry must be attributable to the load."""
        findings = interposition_findings((self.before, self.after))
        self.assertTrue(findings,
                        "W2c's predicate reports NOTHING after a kernel module was "
                        "loaded — the same predicate that had to find zero during the "
                        "shadow arm now finds zero during interposition, which means it "
                        "is not measuring")
        self.assertTrue(any("modules" in f for f in findings),
                        "the predicate did not report the module set moving: %r" % findings)

    def test_THE_PREDICATE_S_DELTA_HALF_IS_SILENT_WHEN_NOTHING_MOVED(self):
        """THE CONTROL THAT MAKES THE INVERSION A MEASUREMENT: without it, "it found
        something" is indistinguishable from "it always finds something".

        AND IT IS AIMED AT THE DELTA HALF RATHER THAN AT THE WHOLE LIST, because the whole
        list cannot be empty on this boot and saying otherwise would be a control that
        fails for a true reason. `interposition_findings` reports two kinds: entries from
        before-vs-after (the delta half) and entries from the `after` state alone (the
        sticky half -- kernel taint above all). Kernel taint never clears, so the sticky
        half speaks over ANY pair on a boot where an out-of-tree module has ever loaded.
        The DELTA half is what distinguishes a load from no load, and it is silent here
        and loud in the row above."""
        same = [f for f in interposition_findings((self.before, self.before))
                if "MOVED across the observation" in f]
        self.assertEqual(same, [],
                         "the predicate reports a MOVE when handed one census twice, so "
                         "its answer above says nothing about the load")
        moved = [f for f in interposition_findings((self.before, self.after))
                 if "MOVED across the observation" in f]
        self.assertTrue(moved,
                        "the same predicate reports no MOVE across a real load either, so "
                        "the two answers are the same answer")

    def test_THE_TAINT_FIELD_IS_DISCLOSED_AS_NO_LONGER_A_BRACKET_SIGNAL(self):
        """A FACT ABOUT THIS GUEST THAT A LATER PASS MUST NOT MISREAD. Kernel taint is
        STICKY: the first out-of-tree load of this boot sets OOT_MODULE and UNSIGNED_MODULE
        permanently, and `rmmod` does not clear them. This unit loaded the module once
        before this bracket was taken, so the taint bits READ THE SAME AT BOTH ENDPOINTS
        and cannot distinguish before from after for any later pass on this boot. The
        module-set comparison by name is unaffected and is what carries the claim.

        Recorded as a ROW rather than a sentence, because a reader who assumed taint was a
        clean signal would draw the opposite conclusion from the same numbers."""
        b = (self.before.get("taint") or {}).get("bits")
        a = (self.after.get("taint") or {}).get("bits")
        self.assertIsNotNone(b, "the taint field did not decode at the before endpoint")
        self.assertIn("OOT_MODULE", a or [],
                      "the after endpoint is NOT tainted out-of-tree, which cannot be true "
                      "with an out-of-tree module resident")
        if b == a:
            self.assertIn("OOT_MODULE", b,
                          "the taint is equal at both endpoints and is NOT the sticky "
                          "out-of-tree bit, so the equality has some other cause")


# =======================================================================================
class TheTwoRefusalShapesAreDrivenThroughTheLoadedModule(unittest.TestCase):
    """C7 — FAIL-CLOSED AT THE DEVICE LAYER, both shapes driven, both citations QUOTED and
    compared against THE CHAIN THE GATE COMPUTES rather than against a frozen name.

    THAT COMPARISON FORM IS THE :787 RULING'S OWN SURVIVING INSTRUCTION, and it is the only
    part of that bracket this unit could satisfy. See the entry: the bracket predicts the
    unestablished-threshold refusal cites DEV-LAW-INTAKE and REDS on a terminal-rule
    citation, while the law W3a3 LANDED -- and the mentor ACCEPTED -- cites the terminal
    rule by explicit design and says so in the operation's own text. This unit VERIFIES and
    does not choose: it reads the tip out of the live law-data and checks the record
    against it. The divergence is RAISED, not amended here.

    POPULATION: the two refusal arms of one exhibition, plus the refusal records the gate
    appended. BASIS: `rule_cited` on the record, read beside the `cite` the live
    DEVICE-INTAKE-COVER definition declares for its `prior_value` rows."""

    def setUp(self):
        self.ex = shim_exhibition(self)["exhibition"]
        self.arms = arms_by_name(self.ex)

    def test_BOTH_SHAPES_REACHED_THE_GATE(self):
        """THE ARM THAT MATTERS MOST, AND THE FIRST DRAFT FAILED IT. Driven at a moment
        when the module's own never-clause fired first, the undeclared-class arm returned a
        confident refusal FROM THE WRONG LAYER and never reached the gate. `crossed` is
        what caught it: a refusal arm must assert WHERE the refusal came from, never merely
        that one happened."""
        for shape, arm in sorted(SHIM_REFUSAL_ARMS.items()):
            entries = self.arms.get(arm) or []
            self.assertTrue(entries, "the %r arm did not run" % arm)
            self.assertEqual(entries[0]["crossed"], 1,
                             "the %s refusal was settled at the boundary and never "
                             "reached the gate, so it says nothing about the law" % shape)
            self.assertNotEqual(entries[0]["errno"], 0,
                                "the %s case was ADMITTED" % shape)

    def test_BLOCK_ADMITS_BESIDE_NET_REFUSING(self):
        """C7's 'both directions beside block'. Without this the class is a fail-closed
        boundary that refuses everything, which would satisfy every refusal row above."""
        self.assertEqual([e["errno"] for e in self.arms["intake"]], [0],
                         "block's intake did not admit, so net's refusal is not a "
                         "distinction the law is making")

    def test_THE_CITED_OBJECT_IS_WHAT_THE_LIVE_LAW_DATA_DECLARES(self):
        """THE COMPARISON THE :787 RULING PRESERVED. Not against a constant in this file:
        the tip is read out of the operation's own `prior_value` rows, so this row cannot
        expire when the law moves -- it reds and names the new tip."""
        tips = computed_refusal_tip()
        self.assertEqual(len(tips), 1,
                         "DEVICE-INTAKE-COVER's prior_value rows now declare more than one "
                         "citation object (%r), so 'the tip of the computed chain' is "
                         "ambiguous and this row cannot answer" % (tips,))
        for shape, arm in sorted(SHIM_REFUSAL_ARMS.items()):
            self.assertEqual(self.arms[arm][0]["cited"], tips[0],
                             "the %s refusal cites %r and the live law-data declares %r"
                             % (shape, self.arms[arm][0]["cited"], tips[0]))

    def test_THE_TWO_REFUSAL_RECORDS_ARE_QUOTED_SIDE_BY_SIDE_and_are_DISTINGUISHABLE(self):
        """C7's own evidence requirement: undeclared-class and unestablished-threshold,
        side by side, each with its citation. They share a citation BY DESIGN, so the row
        that keeps them apart is the MESSAGE -- a reader who cannot tell an absent
        declaration from an unestablished value has two different worlds wearing one
        record."""
        refusals = [r for r in shim_refusals(self.ex)
                    if (r.get("payload") or {}).get("op") == "DEVICE-INTAKE-COVER"]
        self.assertEqual(len(refusals), 2,
                         "expected exactly the two intake refusal shapes and the record "
                         "holds %d" % len(refusals))
        messages = [dict(r["payload"])["message"] for r in refusals]
        self.assertNotEqual(messages[0], messages[1],
                            "both shapes recorded the same sentence")
        self.assertEqual({r["rule_cited"] for r in refusals}, {computed_refusal_tip()[0]})
        joined = " ".join(messages)
        self.assertIn("UNESTABLISHED", joined,
                      "no refusal message names the unestablished threshold")
        self.assertIn("belongs to no record", joined,
                      "no refusal message names the absent declaration")

    def test_MORE_RECORDING_IS_NOT_THE_FAILURE_RESPONSE(self):
        """C7's fourth red world, the FS direction design/27 §8 names as a trap: a refusal
        must not answer by recording more. The refused intake left exactly ONE record --
        the refusal -- and no covering record for the class it refused."""
        net_covers = [r for r in shim_records(self.ex, "DEVICE-INTAKE-COVER")
                      if r["payload"]["device"] == SHIM_NET_DEVICE]
        self.assertEqual(net_covers, [],
                         "a covering record exists for the class whose threshold is "
                         "UNESTABLISHED: %r" % net_covers)

    def test_the_citation_reading_SEES_A_DIFFERENT_CITATION(self):
        """§A64 over the comparison itself. A row that compares a record's citation to a
        law's declaration must be shown to notice when they differ."""
        tips = computed_refusal_tip()
        planted = dict(self.arms[SHIM_REFUSAL_ARMS["undeclared-class"]][0],
                       cited="PLANTED-OTHER-RULE")
        self.assertNotEqual(planted["cited"], tips[0],
                            "a planted foreign citation compares EQUAL to the law's own, "
                            "so the rows above could not have seen a real divergence")

    def test_the_tip_reader_SEES_A_MOVED_TIP(self):
        """AND THE CONTROL FOR THE READER, which is the half that would rot silently: if
        the law's declared citation moved, `computed_refusal_tip` must report the new one.
        Driven at a mutated pack, so the reading is proved to follow the law rather than
        return a memory.

        [EXTENDED -- EP-30-W3, 2026-08-19. The reader now selects a CHAIN BY ITS `action`,
        and the plant below moves BOTH chains to ONE value -- so any selector whatever,
        INCLUDING ONE THAT IGNORED `action` ENTIRELY, reproduces ['PLANTED-TIP']. A SELECTOR
        NEVER SHOWN TO SELECT IS A CHECK THAT CANNOT FAIL, which is §7.1's first disguise
        arriving inside the control written to prevent it. The original claim is UNCHANGED
        and still driven first; the second arm plants the two chains with DIFFERENT
        citations and requires each selection to return ITS OWN.]"""
        pack = copy.deepcopy(live_pack())
        d = op_record(pack, "DEVICE-INTAKE-COVER")["payload"]["definition"]
        for c in d["checks"]:
            if c["check"] == "prior_value":
                c["cite"] = "PLANTED-TIP"
        self.assertEqual(computed_refusal_tip(pack), ["PLANTED-TIP"],
                         "the tip reader did not follow a moved citation, so its agreement "
                         "with the live law above is not a measurement")

        chains = copy.deepcopy(live_pack())
        d = op_record(chains, "DEVICE-INTAKE-COVER")["payload"]["definition"]
        planted = {}
        for c in d["checks"]:
            if c["check"] == "prior_value":
                c["cite"] = planted[c["action"]] = "PLANTED-TIP-%s" % c["action"]
        self.assertEqual(len(planted), 2,
                         "DEVICE-INTAKE-COVER no longer declares TWO prior_value chains, so "
                         "this arm cannot show a selector selecting and the narrowing is "
                         "unfalsifiable here: %r" % (planted,))
        for act, cite in sorted(planted.items()):
            got = computed_refusal_tip(chains, action=act)
            self.assertEqual(got, [cite],
                             "asked for the %s chain the reader returned %r, so it is not "
                             "selecting by action and the aggregate form is still live"
                             % (act, got))


# =======================================================================================
#: THE ERA THIS MOVEMENT IS MEASURED AGAINST: the tree as it stood before this unit wrote
#: anything, captured with `git rev-parse HEAD` BEFORE the first write per charter §A53 --
#: `git checkout -- <path>` no longer undoes a write, so the commit is TAKEN and not
#: trusted. The name states its transition so it cannot go stale when 1.25.0 lands.
W3B_PRE_WRITE_COMMIT = "efb6ded1d22da2bc4004f9e5ace2e1fcb73c435c"

#: W3b's OWN CLOSE — the AFTER end of this unit's quiescence range [EP-30-W1b, 2026-08-16,
#: charter §A57 backward era-pin]. The row below had its BEFORE end pinned and its AFTER end
#: LIVE, so its subject was not W3b's window but whatever the founding says today, forever.
#:
#: DERIVED FROM W3b'S OWN LANDING AND NEVER FROM THE PACK, and the distinction is the whole
#: reason this pin is trustworthy. The pack's COMPLETE history is 33 commits; its bytes changed
#: at 51da0898 (W3a3's landing, 1.24.0) and next at 0bf95e30 (EP-30-W1b's landing, 1.25.0),
#: with NOTHING between. So every commit inside W3b's window carries the same pack blob — and a
#: pin chosen as "the last commit whose pack still matches" would have been selected BY THE
#: PROPERTY THE ROW ASSERTS, making the row a comparison of one thing with itself that could
#: never fail. §7.1's first disguise, reached by trying to fix an era pin.
#:
#: So the pin is the commit that INTRODUCED W3b's own close entry into
#: planning/build/BUILD-PROGRESS_v3.md — a fact about W3b's work, independent of the founding's
#: bytes. Taken with the search controlled in BOTH directions before it was believed: a
#: known-absent string returns 0 commits, a known-present one returns 3, this one returns
#: exactly 1. W3b's window is therefore 2026-08-15 10:56:19 -> 11:48:19, and the board records
#: EP-29-W3b ACCEPTED on 2026-08-15, which agrees.
#:
#: THE DIGEST IS THE PIN AND THE COMMIT IS ITS ALIAS (board :962): the pack at this commit is
#: eaa82d22513cca7d3930ff1cacc30df0a62e04156f7a8864a166643418c93b6b, 207,517 bytes.
W3B_CLOSE_COMMIT = "e4f1e4a47074f9c66f6f2c4e91c8df1196611224"


class TheFoundingStandsBYTEUNCHANGEDAfterW3b(unittest.TestCase):
    """C2's INVERSION, which is this movement's required outcome and the opposite of the
    three law movements before it: W3a and W3a3 MOVED the founding; W3b and W3c leave it
    BYTE-UNCHANGED, and only the plan says which.

    STATED AS AN ERA COMPARISON AND NOT AS A VERSION LITERAL, which is this file's own
    §A57 guard talking and it was right: a row asserting `founding_version == "1.24.0"`
    joins the NEXT founding move's sweep population and has to be found and edited by a
    pass that has nothing to do with it. The claim here is not "the founding equals a
    number I wrote down" -- it is "the founding did not move while this unit ran", which
    an era comparison says directly and a literal only approximates.

    POPULATION: `src/founding/founding-pack.json` at two commits -- this unit's pre-write
    commit and the working tree. BASIS: the file's own BYTES through `tests/era_pin.py`,
    the one home, never re-derived here. NOT a git range: autosync commits every two
    minutes, so another seat's writes land inside any range this unit could compute."""

    def test_the_founding_did_not_move_while_this_unit_ran(self):
        """[DOCUMENTED FLIP — EP-30-W1b, 2026-08-16, charter §A57 BY FALSIFICATION; member 2
        of 2 in this pass's sweep population, taken from its own suite arm at BOTH widths.
        CAUSE: EP-30-W1b moved the founding 1.24.0 -> 1.25.0.
        ASSERTED: W3b's pre-write commit against THE WORKING TREE.
        SUPERSEDED: W3b's pre-write commit against W3B_CLOSE_COMMIT — both ends now commits.
        REMAINS TRUE, unchanged in subject and in every literal: THE FOUNDING DID NOT MOVE
        WHILE W3b RAN. The after-pin is recorded BY DIGEST — the pack at both ends is
        `eaa82d22513cca7d3930ff1cacc30df0a62e04156f7a8864a166643418c93b6b`, 207,517 bytes.
        GIVEN UP: nothing. The claim about the LIVE founding was never this row's subject.

        AND THIS ROW IS THE INTERESTING ONE IN THE SWEEP, SO THE REASON IS KEPT. Its own class
        docstring argues it is IMMUNE to exactly this: its author saw that a row asserting
        `founding_version == "1.24.0"` joins the next founding move's population, and chose an
        ERA COMPARISON instead, on purpose, to stay out of it. THE REASONING WAS RIGHT AND THE
        ROW WENT RED ANYWAY. What puts a row in the population is THE OPEN END, NOT THE
        LITERAL: this row named its population as "two commits -- this unit's pre-write commit
        and the working tree", and the working tree is not a commit. A half-pinned range is an
        open range wearing a closed range's clothes, which is what EP-30-R1 found in the
        engine-diff row three rungs earlier and what EP-28G's flip had already predicted.
        A CLOSED-RANGE LITERAL IS IMMUNE; AN OPEN-RANGE ERA COMPARISON IS NOT. Avoiding one
        §A57 trap does not avoid the other, because they are the same trap.

        THE AFTER-PIN IS DERIVED FROM W3b'S OWN LANDING AND NEVER FROM THE PACK'S BYTES, which
        is what keeps this a check rather than a tautology: choosing "the last commit whose
        pack still matches" would have selected the pin BY the property being asserted and the
        row could then never fail. See W3B_CLOSE_COMMIT's own derivation note.]"""
        era = era_pin.blob_at(W3B_PRE_WRITE_COMMIT, "src/founding/founding-pack.json")
        after = era_pin.blob_at(W3B_CLOSE_COMMIT, "src/founding/founding-pack.json")
        self.assertEqual(hashlib.sha256(era).hexdigest(),
                         hashlib.sha256(after).hexdigest(),
                         "the founding pack's bytes moved during a movement that holds it "
                         "unchanged — a moved founding across W3b's own window REDS")
        self.assertEqual(len(era), len(after))

    def test_the_comparison_CAN_SEE_A_MOVED_FOUNDING(self):
        """§A64 over a byte-identity check, which is the shape most likely to be comparing
        one thing with itself. Driven at a mutated copy rather than argued."""
        with open(PACK_PATH, "rb") as fh:
            live = fh.read()
        moved = live.replace(b'"steps"', b'"stepz"', 1)
        self.assertNotEqual(live, moved, "the mutation changed nothing")
        self.assertNotEqual(hashlib.sha256(live).hexdigest(),
                            hashlib.sha256(moved).hexdigest())

    def test_the_pinned_commit_RESOLVES_and_carries_a_pack(self):
        """A PIN THAT CANNOT BE RESOLVED WOULD MAKE THE ROW ABOVE RAISE RATHER THAN PASS,
        but a pin resolving to the WRONG tree would make it pass wrongly. The era's pack
        is parsed and its shape checked, so the comparison is against a real founding."""
        # [DOCUMENTED FLIP — MAINT-EP29-K1-REPIN, 2026-09-02, charter §A57 era-stabilization
        # (board :2706, AUTHORISED-BY :2664). CAUSE: a LATER lawful founding move — EP-31's
        # MEM-LAW-BUDGET create, 1.30.0 -> 1.31.0, 27 -> 28 steps. The step-count comparison
        # ran the pinned era against the LIVE pack, so a step added after W3b closed reddened a
        # claim about W3b's own window — the half-pinned-range trap this class's own docstring
        # names. ASSERTED: the era against W3b's OWN CLOSE at `W3B_CLOSE_COMMIT`, the same
        # after-coordinate the sibling `test_the_founding_did_not_move_while_this_unit_ran`
        # already closed to. SUPERSEDED: the comparison against `live_pack()`. REMAINS TRUE: the
        # pin resolves and carries a real founding whose step count matches W3b's close — W3b
        # moved no step. GIVEN UP: nothing; the live tree was never a coordinate of W3b's window.]
        era = json.loads(era_pin.blob_at(W3B_PRE_WRITE_COMMIT,
                                         "src/founding/founding-pack.json"))
        after = json.loads(era_pin.blob_at(W3B_CLOSE_COMMIT,
                                           "src/founding/founding-pack.json"))
        self.assertIn("founding_version", era)
        self.assertEqual(len(era["steps"]), len(after["steps"]),
                         "the pinned era holds a different number of steps from W3b's own "
                         "close, so this unit did move the founding")

    def test_this_movement_added_no_operation_and_no_check_kind(self):
        """THE TWO VOCABULARIES THIS UNIT MUST NOT GROW: 76 operations and 13 check kinds,
        both hand-computed from the W3a3 close.

        [DOCUMENTED FLIP — EP-30-C1R, 2026-08-21, a §A57 RANGE CLOSURE. CAUSE: RANGE.
        SUBJECT-ERA: HISTORICAL — the subject is WHAT W3b's MOVEMENT DID, which is finished,
        and its own class docstring already says so: "the founding did not move WHILE THIS
        UNIT RAN". The row read the LIVE world and the LIVE `OP_CHECKS`, so its half-pinned
        range made it a claim about every kind that arrives afterwards, forever — the exact
        trap the sibling docstring three rows up diagnoses in its own words, "a half-pinned
        range is an open range wearing a closed range's clothes". EP-30-C1's two kinds landed
        under a LATER act and reddened it. ASSERTED: 76 operations, 13 check kinds.
        SUPERSEDED: nothing — both literals and the whole claim are unchanged; only the
        SOURCE closes, to W3b's own close commit, where both figures are what this row says
        they are (driven at this hand). GIVEN UP: nothing — the row's stated basis is A
        BOOTED WORLD rather than a file, and `_World(pack=...)` boots the era's own pack, so
        the basis survives the closure intact. The LIVE vocabulary is asserted, at fifteen and
        by name, by `THE_LIVE_CHECK_KINDS` and the pinned-population row that watches it.]"""
        era = era_pin.pack_at(W3B_CLOSE_COMMIT)
        self.assertEqual(len(_World(era).views.op_definitions()), 76,
                         "the operation count moved during a transport unit")
        self.assertEqual(len(kinds_at(W3B_CLOSE_COMMIT)), 13,
                         "the check-kind vocabulary moved during a transport unit")

    def test_the_operation_and_kind_counts_MATCH_THE_ERA(self):
        """AND THE HAND-COMPUTED PAIR ABOVE IS CHECKED AGAINST THE ERA rather than left as
        two numbers a reader has to trust. If they disagree, one of them is wrong and this
        says which.

        [DOCUMENTED FLIP — EP-30-C3R, 2026-08-21, charter §A57 BY FALSIFICATION, a RANGE
        CLOSURE. CAUSE: RANGE. SUBJECT-ERA: HISTORICAL — this class asserts what W3b's
        movement DID, and its own docstring says so in the words "the founding did not move
        WHILE THIS UNIT RAN".
        CAUSE, DRIVEN: EP-30-C3 minted an operation, so the live count read 77 against the
        era's 76.
        ASSERTED: the pre-write era against `live_pack()` — THE WORKING TREE, which is not a
        commit. SUPERSEDED: against `W3B_CLOSE_COMMIT`, so both ends resolve through `era_pin`.
        AND THIS IS THE SECOND HALF OF A REPAIR EP-30-C1R MADE ON 2026-08-21 AND COULD NOT
        SEE THE REST OF. Its sibling three rows up carried the identical open range and was
        closed then; THIS row was not, because C1's move grew the CHECK-KIND vocabulary and
        not the OPERATION set, so only the sibling reddened and only the sibling entered that
        unit's population. A POPULATION TAKEN FROM AN ARM IS A POPULATION OF ROWS THAT HAPPENED
        TO RED, and a row with the same defect that a given move does not happen to touch is
        invisible to it. That is not a criticism of C1R's method — it is the honest limit its
        own cause-predicate clause states — and it is why this pair took two units to close.
        REMAINS TRUE, unchanged in subject and in kind: the operation set did not move across
        W3b's own window.
        GIVEN UP: nothing. No claim about today's operation count was ever this row's subject;
        the live count is asserted by the pass that moved it.]"""
        era = json.loads(era_pin.blob_at(W3B_PRE_WRITE_COMMIT,
                                         "src/founding/founding-pack.json"))
        after = json.loads(era_pin.blob_at(W3B_CLOSE_COMMIT,
                                           "src/founding/founding-pack.json"))
        self.assertEqual(len(ops_of(era)), len(ops_of(after)),
                         "the operation set moved between the pre-write era and W3b's close")


# =======================================================================================
# W3b's RED WORLDS — §A64 on every structural row
#
# SYNTHETIC ON PURPOSE, on this file's own precedent at W0g, W2a and W2c: a red world built
# by mutating the LIVE exhibition could only run when the lab is up, so the one class of
# row whose whole job is to fail would be the first to go silent when the estate most needs
# it. The substrate below has the SHAPE the guest produces and values chosen by hand.
#
# EACH PLANTER MOVES EXACTLY ONE THING, and every real W3b row is then run against the
# planted world THROUGH UNITTEST'S OWN MACHINERY, so what is measured is the row that ships
# rather than a paraphrase of it.
# =======================================================================================
def _synthetic_shim_arm(arm, errno=0, crossed=1, cited="", arrivals=0, nbytes=0, nr=4):
    return {"kind": arm.split("-")[0], "arm": arm, "errno": errno, "verdict": -errno,
            "cited": cited, "crossed": crossed, "nr": nr, "arrival_count": arrivals,
            "bytes": nbytes}


def _synthetic_shim_record(seq, action, cite, payload, refused=False):
    rec = {"seq": seq, "actor": "owner", "action": action, "rule_cited": cite,
           "payload": payload}
    if refused:
        rec["refused"] = True
        rec["actor"] = "SYSTEM"
    return rec


def _synthetic_exhibition():
    """The shape `govshimd.py exhibit` returns, at hand-chosen values. A row that reads a
    field this does not carry reds here rather than at the lab."""
    W, I, N = "device-io@block", "device-intake@block", "device-io@net"
    arms = [
        _synthetic_shim_arm("io-before-bind", errno=22, cited="DEV-LAW-BIND", nbytes=4096),
        _synthetic_shim_arm("bind-before-capability", errno=1, cited="CAP-IS-LAW", nr=2),
        _synthetic_shim_arm("outside-validation-set", errno=19, crossed=0,
                            cited="D8-VALIDATION-SET", nr=2),
        _synthetic_shim_arm("register", nr=1),
        _synthetic_shim_arm("bind", nr=2),
        _synthetic_shim_arm("io", nbytes=4096), _synthetic_shim_arm("io", nbytes=4096),
        _synthetic_shim_arm("io", nbytes=4096),
        _synthetic_shim_arm("intake", nr=5, arrivals=3, nbytes=12288),
        _synthetic_shim_arm("io-single", nbytes=512),
        _synthetic_shim_arm("intake-of-one", errno=34, crossed=0, cited="DEV-LAW-INTAKE",
                            arrivals=1, nr=5),
        _synthetic_shim_arm("io-for-undeclared", nbytes=4096),
        _synthetic_shim_arm("io-for-undeclared", nbytes=4096),
        _synthetic_shim_arm("intake-undeclared-class", errno=38, cited=SHIM_TERMINAL_RULE,
                            arrivals=3, nbytes=8704, nr=5),
        _synthetic_shim_arm("register-net", nr=1), _synthetic_shim_arm("bind-net", nr=2),
        _synthetic_shim_arm("io-net", nbytes=1500), _synthetic_shim_arm("io-net", nbytes=1500),
        _synthetic_shim_arm("intake-net-unestablished", errno=38, cited=SHIM_TERMINAL_RULE,
                            arrivals=2, nbytes=3000, nr=5),
        _synthetic_shim_arm("unbind", nr=3),
    ]
    seq, records = 100, []
    for action, cite, payload in (
            ("REGISTER-CAPABILITY", "CAP-IS-LAW",
             {"driver": "drv-block", "device_class": "block", "capabilities": []}),
            ("BIND-DEVICE", "DEV-LAW-BIND",
             {"device": SHIM_BLOCK_DEVICE, "driver": "drv-block"}),
            ("DEVICE-IO-WINDOW-WRITE", "DEV-LAW-BIND",
             {"device": SHIM_BLOCK_DEVICE, "window": W, "bytes": 4096}),
            ("DEVICE-INTAKE-COVER", "DEV-LAW-INTAKE",
             {"intake": I, "device": SHIM_BLOCK_DEVICE, "window": W,
              "arrival_count": 3, "byte_total": 12288}),
            ("REGISTER-CAPABILITY", "CAP-IS-LAW",
             {"driver": "drv-net", "device_class": "net", "capabilities": []}),
            ("BIND-DEVICE", "DEV-LAW-BIND",
             {"device": SHIM_NET_DEVICE, "driver": "drv-net"}),
            ("DEVICE-IO-WINDOW-WRITE", "DEV-LAW-BIND",
             {"device": SHIM_NET_DEVICE, "window": N, "bytes": 1500}),
            ("UNBIND", "DEV-LAW-BIND", {"device": SHIM_BLOCK_DEVICE})):
        seq += 1
        records.append(_synthetic_shim_record(seq, action, cite, payload))
    for cite, msg in ((("DEV-LAW-BIND"), "cannot move bytes for a device no record ever "
                                         "bound"),
                      (("CAP-IS-LAW"), "cannot bind unregistered driver"),
                      ((SHIM_TERMINAL_RULE), "no DECLARE-INTAKE names intake = "
                                             "'device-intake@no-such-class', so the field "
                                             "this act's licence would be computed from "
                                             "belongs to no record"),
                      ((SHIM_TERMINAL_RULE), "this intake declaration leaves its threshold "
                                             "UNESTABLISHED, so no licence computes")):
        seq += 1
        op = "DEVICE-INTAKE-COVER" if cite == SHIM_TERMINAL_RULE else (
            "DEVICE-IO-WINDOW-WRITE" if cite == "DEV-LAW-BIND" else "BIND-DEVICE")
        records.append(_synthetic_shim_record(seq, "op-refused", cite,
                                              {"op": op, "message": msg}, refused=True))
    return {"devices": [{"name": SHIM_BLOCK_DEVICE, "class": "block"},
                        {"name": SHIM_NET_DEVICE, "class": "net"}],
            "arms": arms, "records": records, "brain_rc": -9,
            "attach_probe": {"crossed": 1},
            "queries": [{"query": "binding", "errno": 0, "answer": "drv-block",
                         "crossed": 0, "nr": 128, "arrival_count": 0, "bytes": 0},
                        {"query": "arrivals", "errno": 0, "answer": "", "crossed": 0,
                         "nr": 129, "arrival_count": 3, "bytes": 12288},
                        {"query": "crossings", "errno": 0, "answer": "", "crossed": 0,
                         "nr": 130, "arrival_count": 38, "bytes": 7}],
            "detached": [
                dict(_synthetic_shim_arm("io-brain-detached", errno=107, crossed=0,
                                         cited="NO-BRAIN")),
                dict(_synthetic_shim_arm("register-brain-detached", errno=107, crossed=0,
                                         cited="NO-BRAIN", nr=1)),
                {"query": "binding", "errno": 0, "answer": "drv-net", "crossed": 0,
                 "nr": 128, "arrival_count": 0, "bytes": 0},
                {"query": "arrivals", "errno": 0, "answer": "", "crossed": 0, "nr": 129,
                 "arrival_count": 2, "bytes": 3000},
                {"query": "binding", "errno": 0, "answer": "", "crossed": 0, "nr": 128,
                 "arrival_count": 0, "bytes": 0}]}


def _synthetic_shim_census(names, taint=("OOT_MODULE", "UNSIGNED_MODULE")):
    """The census fields `interposition_findings` and the C5 rows actually read. Every
    other group is present and EMPTY, so a planted attachment is the only thing that can
    make the predicate speak."""
    return {"modules": {"raw_ok": True, "names": sorted(names), "count": len(names)},
            "taint": {"raw": {"text": "12288"}, "bits": list(taint)},
            "block_stacking": {}, "device_mapper": {}, "net_attachments": {},
            "netfilter": {}, "bpf": {},
            "dynamic_instrumentation": {"current_tracer": {"text": "nop"}}}


_SYNTHETIC_MODSET = tuple("mod%02d" % i for i in range(40))


def _synthetic_drivers(image="a" * 64, syms="b" * 64, count=238, builtin=True):
    return {"kernel": GUEST_KERNEL,
            "kernel_image": {"path": "/boot/vmlinuz-%s" % GUEST_KERNEL, "exists": True,
                             "sha256": image, "size": 15042952},
            "drivers": {d: {"builtin_list": builtin, "modinfo_path": "(builtin)",
                            "is_module_file": False, "sysfs": True}
                        for d in ("virtio_blk", "virtio_net", "virtio", "virtio_pci",
                                  "virtio_ring")},
            "kallsyms": {"population": "synthetic", "count": count, "sha256": syms}}


def _synthetic_shim_world():
    return {"digest": "0" * 64, "gdir": "/tmp/govshim-synthetic", "snapshot": "synthetic",
            "param": ",".join(SHIM_VALIDATION_SET), "exhibition": _synthetic_exhibition(),
            "census": (_synthetic_shim_census(_SYNTHETIC_MODSET),
                       _synthetic_shim_census(_SYNTHETIC_MODSET + (GOVSHIM_MODULE,))),
            "drivers": (_synthetic_drivers(), _synthetic_drivers()),
            "loaded_this_run": True}


# ------------------------------------------------------------------ the planters, one each
def _p_crossing_left_no_record(w):
    ex = w["exhibition"]
    ex["records"] = [r for r in ex["records"] if r["action"] != "DEVICE-INTAKE-COVER"]


def _p_crossing_cites_the_wrong_law(w):
    for r in w["exhibition"]["records"]:
        if r["action"] == "BIND-DEVICE":
            r["rule_cited"] = "DEV-LAW-INTAKE"


def _p_io_admitted_without_a_bind(w):
    for a in w["exhibition"]["arms"]:
        if a["arm"] == "io-before-bind":
            a["errno"], a["cited"] = 0, ""


def _p_bind_admitted_without_a_capability(w):
    for a in w["exhibition"]["arms"]:
        if a["arm"] == "bind-before-capability":
            a["errno"], a["cited"] = 0, ""


def _p_the_wrap_reaches_beyond_the_set(w):
    for a in w["exhibition"]["arms"]:
        if a["arm"] == "outside-validation-set":
            a["crossed"] = 1


def _p_a_cover_stands_for_one_arrival(w):
    for r in w["exhibition"]["records"]:
        if r["action"] == "DEVICE-INTAKE-COVER":
            r["payload"]["arrival_count"] = 1


def _p_one_cover_per_arrival(w):
    ex = w["exhibition"]
    cover = [r for r in ex["records"] if r["action"] == "DEVICE-INTAKE-COVER"][0]
    ex["records"] = ex["records"] + [dict(cover, seq=cover["seq"] + 500) for _ in range(8)]


def _p_a_query_crosses(w):
    w["exhibition"]["queries"][0]["crossed"] = 1


def _p_a_command_is_answered_in_the_kernel(w):
    for a in w["exhibition"]["arms"]:
        if a["arm"] == "bind-net":
            a["crossed"] = 0


def _p_a_decision_succeeds_with_the_brain_dead(w):
    for x in w["exhibition"]["detached"]:
        if x.get("arm") == "io-brain-detached":
            x["errno"] = 0


def _p_the_cache_dies_with_the_brain(w):
    for x in w["exhibition"]["detached"]:
        if x.get("query") == "binding":
            x["answer"] = ""


def _p_the_brain_never_attached(w):
    w["exhibition"]["attach_probe"]["crossed"] = 0


def _p_a_driver_byte_moved(w):
    w["drivers"] = (w["drivers"][0], _synthetic_drivers(image="c" * 64))


def _p_a_driver_symbol_moved(w):
    w["drivers"] = (w["drivers"][0], _synthetic_drivers(syms="d" * 64))


def _p_a_driver_stopped_being_builtin(w):
    w["drivers"] = (w["drivers"][0], _synthetic_drivers(builtin=False))


def _p_the_shim_is_not_in_the_added_set(w):
    w["census"] = (w["census"][0], _synthetic_shim_census(_SYNTHETIC_MODSET + ("other",)))


def _p_a_module_departed(w):
    w["census"] = (w["census"][0],
                   _synthetic_shim_census(_SYNTHETIC_MODSET[:-3] + (GOVSHIM_MODULE,)))


def _p_the_census_saw_nothing_move(w):
    w["census"] = (w["census"][0], _synthetic_shim_census(_SYNTHETIC_MODSET))


def _p_a_refusal_never_reached_the_gate(w):
    for a in w["exhibition"]["arms"]:
        if a["arm"] == SHIM_REFUSAL_ARMS["undeclared-class"]:
            a["crossed"] = 0


def _p_net_intake_is_admitted(w):
    for a in w["exhibition"]["arms"]:
        if a["arm"] == SHIM_REFUSAL_ARMS["unestablished-threshold"]:
            a["errno"], a["cited"] = 0, ""


def _p_a_refusal_cites_a_foreign_object(w):
    for a in w["exhibition"]["arms"]:
        if a["arm"] == SHIM_REFUSAL_ARMS["undeclared-class"]:
            a["cited"] = "FS-LAW-PERM"


def _p_the_two_shapes_record_one_sentence(w):
    msgs = [r for r in w["exhibition"]["records"]
            if r.get("refused") and r["payload"]["op"] == "DEVICE-INTAKE-COVER"]
    msgs[1]["payload"]["message"] = msgs[0]["payload"]["message"]


def _p_more_recording_is_the_failure_response(w):
    ex = w["exhibition"]
    ex["records"].append(_synthetic_shim_record(
        999, "DEVICE-INTAKE-COVER", "DEV-LAW-INTAKE",
        {"intake": "device-intake@net", "device": SHIM_NET_DEVICE,
         "window": "device-io@net", "arrival_count": 2, "byte_total": 3000}))


def _p_block_stopped_admitting(w):
    for a in w["exhibition"]["arms"]:
        if a["arm"] == "intake":
            a["errno"] = 38


#: EVERY STRUCTURAL W3b ROW, WITH THE ONE PLANT THAT MUST MAKE IT SPEAK. A row absent from
#: this table has not been driven against a near-miss and is a row that has never been
#: shown able to say no (§A64).
_W3B_ROWS = (
    (TheFourCrossingsEachProduceTheirGateRecord, "test_every_crossing_left_a_record",
     _p_crossing_left_no_record),
    (TheFourCrossingsEachProduceTheirGateRecord,
     "test_every_crossing_record_cites_the_law_its_definition_names",
     _p_crossing_cites_the_wrong_law),
    (TheFourCrossingsEachProduceTheirGateRecord,
     "test_the_intake_record_carries_the_law_s_own_five_carriers",
     _p_crossing_left_no_record),
    (TheShimChainRunsBothDirections, "test_NO_IO_RECORD_WITHOUT_A_BIND",
     _p_io_admitted_without_a_bind),
    (TheShimChainRunsBothDirections,
     "test_NO_BIND_WITHOUT_A_CAPABILITY_LAW_and_the_refusal_cites_CAP_IS_LAW",
     _p_bind_admitted_without_a_capability),
    (TheShimChainRunsBothDirections, "test_THE_POSITIVE_DIRECTION_ADMITS_IN_ORDER",
     _p_block_stopped_admitting),
    (TheWrapDoesNotReachBeyondTheValidationSet,
     "test_a_device_outside_the_set_is_refused_at_the_boundary",
     _p_the_wrap_reaches_beyond_the_set),
    (TheIntakeRecordIsAtWindowGradeNeverPerInterrupt,
     "test_a_covering_record_stands_for_MORE_THAN_ONE_arrival",
     _p_a_cover_stands_for_one_arrival),
    (TheIntakeRecordIsAtWindowGradeNeverPerInterrupt,
     "test_the_records_do_not_scale_with_the_arrivals", _p_one_cover_per_arrival),
    (TheIoctlSplitIsDecidedByTheOpNumber,
     "test_A_QUERY_ROW_PER_VALIDATION_DRIVER_does_not_cross", _p_a_query_crosses),
    (TheIoctlSplitIsDecidedByTheOpNumber,
     "test_A_COMMAND_ROW_PER_VALIDATION_DRIVER_crosses",
     _p_a_command_is_answered_in_the_kernel),
    (TheCacheClassStillAnswersWithTheBrainDead,
     "test_every_DECISION_fails_with_the_brain_dead",
     _p_a_decision_succeeds_with_the_brain_dead),
    (TheCacheClassStillAnswersWithTheBrainDead,
     "test_every_CACHE_read_still_answers_and_one_answers_with_CONTENT",
     _p_the_cache_dies_with_the_brain),
    (TheCacheClassStillAnswersWithTheBrainDead, "test_the_brain_was_ACTUALLY_dead",
     _p_the_brain_never_attached),
    (TheValidationDriversAreUnmodifiedAcrossTheLoad,
     "test_the_kernel_image_that_contains_them_is_byte_identical", _p_a_driver_byte_moved),
    (TheValidationDriversAreUnmodifiedAcrossTheLoad,
     "test_the_RUNNING_kernel_s_own_symbols_for_them_are_identical",
     _p_a_driver_symbol_moved),
    (TheValidationDriversAreUnmodifiedAcrossTheLoad,
     "test_the_validation_drivers_are_BUILTIN_at_both_ends",
     _p_a_driver_stopped_being_builtin),
    (TheAttachmentCensusFindsTheShimAndNamesEveryOther,
     "test_THE_SHIM_S_NAME_IS_IN_THE_ADDED_SET", _p_the_shim_is_not_in_the_added_set),
    (TheAttachmentCensusFindsTheShimAndNamesEveryOther,
     "test_EVERY_OTHER_ARRIVAL_IS_DISCLOSED_and_none_departed", _p_a_module_departed),
    (TheAttachmentCensusFindsTheShimAndNamesEveryOther,
     "test_W2c_S_OWN_PREDICATE_NOW_REPORTS_THE_SHIM", _p_the_census_saw_nothing_move),
    (TheTwoRefusalShapesAreDrivenThroughTheLoadedModule, "test_BOTH_SHAPES_REACHED_THE_GATE",
     _p_a_refusal_never_reached_the_gate),
    (TheTwoRefusalShapesAreDrivenThroughTheLoadedModule, "test_BOTH_SHAPES_REACHED_THE_GATE",
     _p_net_intake_is_admitted),
    (TheTwoRefusalShapesAreDrivenThroughTheLoadedModule,
     "test_THE_CITED_OBJECT_IS_WHAT_THE_LIVE_LAW_DATA_DECLARES",
     _p_a_refusal_cites_a_foreign_object),
    (TheTwoRefusalShapesAreDrivenThroughTheLoadedModule,
     "test_THE_TWO_REFUSAL_RECORDS_ARE_QUOTED_SIDE_BY_SIDE_and_are_DISTINGUISHABLE",
     _p_the_two_shapes_record_one_sentence),
    (TheTwoRefusalShapesAreDrivenThroughTheLoadedModule,
     "test_MORE_RECORDING_IS_NOT_THE_FAILURE_RESPONSE",
     _p_more_recording_is_the_failure_response),
    (TheTwoRefusalShapesAreDrivenThroughTheLoadedModule,
     "test_BLOCK_ADMITS_BESIDE_NET_REFUSING", _p_block_stopped_admitting),
)


def _run_shim_against(planted, cls, meth):
    """Run a REAL W3b row against a PLANTED world, through unittest's own machinery, so
    what is measured is the row that ships and not a paraphrase of it."""
    key = shim_digest()
    sentinel = object()
    saved = _SHIM_MEMO.get(key, sentinel)
    _SHIM_MEMO[key] = planted
    try:
        return unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(cls(meth))
    finally:
        if saved is sentinel:
            _SHIM_MEMO.pop(key, None)
        else:
            _SHIM_MEMO[key] = saved


class TheW3bRowsCanBeMadeToFail(unittest.TestCase):
    """§A64 FOR THE WHOLE MOVEMENT, and EP-29 §3 binds it here. A row that passes only
    because nothing tried to fool it has not been driven.

    POPULATION: the %d (row, plant) pairs of `_W3B_ROWS`. BASIS: unittest's own result for
    the shipping row, run against a world differing from the clean one in exactly one
    field.""" % len(_W3B_ROWS)

    def test_the_clean_synthetic_world_passes_every_row(self):
        """FIRST, AND IT IS THE HALF THAT IS EASY TO SKIP: over the UNPLANTED substrate
        every row must be GREEN. Without this, a row that fails for a reason the substrate
        itself carries would count as a successful plant, and the whole table would be
        measuring the fixture."""
        for cls, meth, _plant in _W3B_ROWS:
            res = _run_shim_against(_synthetic_shim_world(), cls, meth)
            self.assertTrue(res.wasSuccessful(),
                            "%s.%s FAILS on the CLEAN synthetic world, so its failure "
                            "under a plant would prove nothing: %r"
                            % (cls.__name__, meth,
                               [t[1][-400:] for t in res.failures + res.errors]))

    def test_every_row_reddens_under_its_own_plant(self):
        for cls, meth, plant in _W3B_ROWS:
            world = _synthetic_shim_world()
            plant(world)
            res = _run_shim_against(world, cls, meth)
            self.assertFalse(res.wasSuccessful(),
                             "%s.%s stayed GREEN under %s — it cannot see its own red "
                             "world" % (cls.__name__, meth, plant.__name__))

    def test_every_plant_moves_something(self):
        """A PLANTER THAT CHANGED NOTHING would make its row look undriven while the table
        read as complete. Compared as JSON so a mutation anywhere in the structure counts."""
        clean = json.dumps(_synthetic_shim_world(), sort_keys=True, default=str)
        for _cls, _meth, plant in _W3B_ROWS:
            world = _synthetic_shim_world()
            plant(world)
            self.assertNotEqual(json.dumps(world, sort_keys=True, default=str), clean,
                                "%s changed nothing" % plant.__name__)

    def test_every_structural_row_of_this_movement_is_in_the_table(self):
        """THE TABLE'S OWN COVERAGE, WALKED RATHER THAN TRUSTED. Every `test_` method of
        every W3b claim class either appears in `_W3B_ROWS` or is named here as a row whose
        subject is not a claim about the exhibition — its own control, its own non-vacuity,
        or a statement about source text rather than about a run."""
        covered = {(cls.__name__, meth) for cls, meth, _p in _W3B_ROWS}
        exempt = {
            # controls and near-misses: they ARE the §A64 machinery
            "test_the_record_reading_SEES_A_MISSING_RECORD",
            "test_the_chain_reading_SEES_AN_ADMITTED_NEGATIVE_ARM",
            "test_the_symbol_selection_CAN_SEE_A_CHANGE",
            "test_the_citation_reading_SEES_A_DIFFERENT_CITATION",
            "test_the_tip_reader_SEES_A_MOVED_TIP",
            "test_the_operation_walk_FINDS_A_PLANTED_SIXTH_OF_EITHER_SHAPE",
            "test_THE_PREDICATE_S_DELTA_HALF_IS_SILENT_WHEN_NOTHING_MOVED",
            # non-vacuity and disclosure rows, which assert about the bracket itself
            "test_the_census_read_its_subject_at_both_ends",
            "test_the_population_is_NAMED_at_each_endpoint",
            "test_the_in_set_devices_DO_reach_the_gate",
            "test_THE_TAINT_FIELD_IS_DISCLOSED_AS_NO_LONGER_A_BRACKET_SIGNAL",
            "test_BOTH_REFUSALS_ARE_RECORDS_AND_NOT_ONLY_RETURN_VALUES",
            "test_the_QUERY_returns_REAL_state_and_not_a_constant",
            "test_no_record_exists_for_the_out_of_set_device",
            "test_a_cover_of_ONE_is_never_even_asked_for",
            # statements about SOURCE TEXT or LAW-DATA, not about an exhibition
            "test_the_split_is_a_pure_function_of_the_number_in_the_module_s_own_text",
            "test_EVERY_COMMAND_NUMBER_IS_BELOW_THE_BASE_and_every_query_at_or_above",
            "test_the_hand_computed_citations_ARE_the_definitions_own",
            "test_the_gate_ITSELF_has_no_row_against_a_cover_of_one",
        }
        classes = (TheFourCrossingsEachProduceTheirGateRecord, TheShimChainRunsBothDirections,
                   TheWrapDoesNotReachBeyondTheValidationSet,
                   TheIntakeRecordIsAtWindowGradeNeverPerInterrupt,
                   TheIoctlSplitIsDecidedByTheOpNumber,
                   TheCacheClassStillAnswersWithTheBrainDead,
                   TheValidationDriversAreUnmodifiedAcrossTheLoad,
                   TheAttachmentCensusFindsTheShimAndNamesEveryOther,
                   TheTwoRefusalShapesAreDrivenThroughTheLoadedModule)
        missing = []
        for cls in classes:
            for meth in dir(cls):
                if meth.startswith("test_") and (cls.__name__, meth) not in covered \
                        and meth not in exempt:
                    missing.append("%s.%s" % (cls.__name__, meth))
        self.assertEqual(missing, [],
                         "these W3b rows have neither a plant nor a stated exemption: %r"
                         % missing)

    def test_the_coverage_walk_FINDS_A_ROW_IT_WAS_NOT_TOLD_ABOUT(self):
        """THE CONTROL FOR THE WALK ABOVE, which is the one whose empty answer carries a
        finding. Given a class with a row in neither table, it must report it."""
        class _Planted(unittest.TestCase):
            def test_a_row_nobody_covered(self):
                pass
        covered, exempt = set(), set()
        missing = [m for m in dir(_Planted)
                   if m.startswith("test_") and ("_Planted", m) not in covered
                   and m not in exempt]
        self.assertEqual(missing, ["test_a_row_nobody_covered"],
                         "the coverage walk cannot find an uncovered row, so its empty "
                         "answer above says nothing")

# =======================================================================================
# EP-29 W3c — THE CONTAINMENT ESTABLISHMENT (ADDENDUM 8 C6), THREE-STATE
# =======================================================================================
#
# C6 asks for "the fault EXHIBITED through the LOADED module -- a recorded unbind and a
# recorded QUIESCE, each citing its rule", with the red world "a quiesce without its
# citation REDS".
#
# THE UNBIND HALF EXISTS. THE QUIESCE HALF HAS NO OPERATION, NO LAW CLAUSE AND NO
# DERIVATION FROM THE UNBIND, and this block is the establishment that says so BY DRIVING
# rather than by reading. It is the :739 shape one movement later: W3b found the intake
# crossing had no operation to cross; W3c finds the containment has no act to record and,
# worse, that the act it does have CONTAINS NOTHING.
#
# EVERY ROW HERE IS A STATE ROW in the :711 sense -- each verdict binds records, citations
# and law-data, none binds a rate or a timing, and not one reaches the guest. NO MODULE WAS
# LOADED BY THIS PASS, so no snapshot was owed and none was taken.
#
# THE ROWS ARE WRITTEN IN THE PRESENCE FORM (close-ledger item 10): every correct answer
# below is a NAMED ROW -- a table of operations, a table of checks, a verbatim enforcement
# clause, a table of verdicts -- and never a count of zero, because a count of zero in a
# growing file is a check waiting to invert. THEY ARE ALSO WRITTEN TO RED LOUDLY THE DAY A
# CONTAINMENT LANDS (the :751 form, W3a2's pinned-population row): a quiesce operation, a
# containment check or an enforcement clause arriving makes these tables move, and the
# builder who meets that red meets THIS FINDING RE-OPENING, never a defect.

#: The six operations whose `law_cited` is one of the two device laws, NAMED. Population:
#: the live founding pack's CREATE-OP records. Basis: each definition's own `law_cited`.
W3C_DEVICE_LAW_OPS = ("BIND-DEVICE", "DECLARE-INTAKE", "DECLARE-IO-WINDOW",
                      "DEVICE-INTAKE-COVER", "DEVICE-IO-WINDOW-WRITE", "UNBIND")

#: The two device laws. Basis: the `law_cited` values of the six above, de-duplicated.
W3C_DEVICE_LAWS = ("DEV-LAW-BIND", "DEV-LAW-INTAKE")

#: THE FOUR DEVICE ACT OPS, and the two exclusions are stated rather than filtered away:
#: DECLARE-IO-WINDOW and DECLARE-INTAKE AUTHOR LAW-DATA and admit no device traffic --
#: DEVICE-INTAKE-COVER's own definition draws that division ("DECLARE-INTAKE declares THE
#: GRADE ... and writes no arrival"). A containment governs ACTS, so the acts are the
#: population.
W3C_DEVICE_ACTS = ("BIND-DEVICE", "DEVICE-INTAKE-COVER", "DEVICE-IO-WINDOW-WRITE", "UNBIND")

#: THE FINDING, AS A NAMED ROW. Every device act still ADMITTED at a world where the device
#: HAS BEEN UNBOUND -- custody ended, and this is what the law still permits. Hand-computed
#: from the definitions BEFORE the run: every device check is `require_prior`, which UNBIND's
#: own text says READS HISTORY ("it refuses an unbind of a never-bound device and does NOT
#: refuse a second unbind of an already-unbound one"), so an ended custody removes no prior.
W3C_ADMITTED_AFTER_CUSTODY_ENDS = ("BIND-DEVICE", "DEVICE-INTAKE-COVER",
                                   "DEVICE-IO-WINDOW-WRITE", "UNBIND")

#: EVERY CHECK ON EVERY DEVICE-LAW OPERATION, hand-computed from the definitions as
#: (operation, kind, the action it scans, the rule it cites). THE POINT OF THE TABLE IS ITS
#: THIRD COLUMN: every row names an ACTION to scan for, and an action scan reads HISTORY.
#: Nothing here reads a CURRENT holding, which is the shape a quiesce needs.
#:
#: [DOCUMENTED FLIP -- EP-30-W3, 2026-08-19; the one LIVE-subject member of this pass's
#: range population. CAUSE: EP-30-W2 added a `prior_value` check over BIND-DEVICE's stream
#: to BOTH consuming operations, so the live table grew from EIGHT rows to TEN. ASSERTED:
#: the eight rows below the two marked ones. SUPERSEDED: ten. REMAINS TRUE, and it is the
#: whole reason this table is RE-DERIVED rather than ERA-PINNED: EVERY ROW STILL NAMES AN
#: ACTION -- both new rows scan `BIND-DEVICE` -- so nothing here reads a CURRENT holding and
#: C6's containment finding DOES NOT RE-OPEN. GIVEN UP: nothing.
#:
#: WHY THIS ROW IS NOT ERA-PINNED, stated because its cause is the same founding move that
#: era-pinned `TheWindowLawLanded.test_C6_holds_no_new_check_kind`: KIND and SUBJECT-ERA are
#: SEPARATE AXES and a repair must match BOTH. This table's subject is THE LIVE LAW's
#: containment vocabulary -- the block comment above says so in its own words, that these
#: tables are written to RED LOUDLY the day a containment lands and that the builder meeting
#: that red meets THE FINDING RE-OPENING. AN ERA-PIN WOULD CLOSE THE RANGE CORRECTLY AND
#: THEN RETIRE THE TRIPWIRE, going green while asserting a thing nobody needs asserted.
#: The two rows below are marked so the next reader can see what W2 added without a diff.]
W3C_DEVICE_CHECK_TABLE = (
    ("BIND-DEVICE", "require_prior", "REGISTER-CAPABILITY", "CAP-IS-LAW"),
    ("DECLARE-INTAKE", "require_prior", "DECLARE-IO-WINDOW", "DEV-LAW-INTAKE"),
    ("DEVICE-INTAKE-COVER", "prior_value", "BIND-DEVICE", "DEV-LAW-BIND"),      # W2
    ("DEVICE-INTAKE-COVER", "prior_value", "DECLARE-INTAKE", "P3-CLOSURE"),
    ("DEVICE-INTAKE-COVER", "require_prior", "BIND-DEVICE", "DEV-LAW-BIND"),
    ("DEVICE-INTAKE-COVER", "require_prior", "DECLARE-INTAKE", "DEV-LAW-INTAKE"),
    ("DEVICE-IO-WINDOW-WRITE", "prior_value", "BIND-DEVICE", "DEV-LAW-BIND"),   # W2
    ("DEVICE-IO-WINDOW-WRITE", "require_prior", "BIND-DEVICE", "DEV-LAW-BIND"),
    ("DEVICE-IO-WINDOW-WRITE", "require_prior", "DECLARE-IO-WINDOW", "DEV-LAW-BIND"),
    ("UNBIND", "require_prior", "BIND-DEVICE", "DEV-LAW-BIND"),
)

#: THE TWO DEVICE LAWS' OWN ENFORCEMENT CLAUSES, QUOTED VERBATIM from the founding. Pinned
#: because a containment law clause cannot land without moving one of these strings, so the
#: absence is carried by a PRESENT value rather than by a search that returns nothing.
W3C_ENFORCED_BY = {
    "DEV-LAW-BIND":
        "the require_prior checks on BIND-DEVICE (a bind cites a registered capability) "
        "and on UNBIND (an unbind cites a prior bind), and the gate's closure step, which "
        "refuses and records any act class this law founds no declaration for",
    "DEV-LAW-INTAKE":
        "the require_prior check on DECLARE-INTAKE (an intake declares a grade for arrivals "
        "admitted through a DECLARED window, so a window name no record founds is refused), "
        "and the gate's closure step, which refuses and records any device intake act class "
        "this law founds no declaration for",
}

W3C_DEV, W3C_DRV = "virtio1", "drv-block"
W3C_WINDOW, W3C_INTAKE = "device-io@block", "device-intake@block"

#: THE ONE SOURCE THE W3c ROWS READ, so §A64 can hand the SHIPPING row a planted world
#: instead of a paraphrase of it. `None` means the live founding, which is what every arm
#: runs against; the plant table below is the only writer.
_W3C_PACK = None


def w3c_pack():
    return copy.deepcopy(_W3C_PACK) if _W3C_PACK is not None else live_pack()


def w3c_world():
    return _World(_W3C_PACK) if _W3C_PACK is not None else _World()


def _w3c_in_world(pack, fn, *a, **kw):
    """Run `fn` with a NAMED pack installed as the W3c world's source, then put the source
    back exactly as it was.

    THE SAVE-AND-RESTORE IS THE WHOLE POINT AND IT IS NOT DEFENSIVE STYLE: `_W3C_PACK` is
    read by every row in three classes, so a global left changed would silently move the
    world under every row that ran after it -- and those rows would still be GREEN, against
    the wrong founding. `_run_w3c_against` already does this around a ROW; this does it
    around an ACT, which is what a row driving BOTH ENDS of its own control needs."""
    global _W3C_PACK
    saved = _W3C_PACK
    _W3C_PACK = pack
    try:
        return fn(*a, **kw)
    finally:
        _W3C_PACK = saved


def w3c_device_act(world, op, device=W3C_DEV, driver=W3C_DRV):
    """ONE device act at a live world -> "ADMITTED" or "REFUSED:<rule>". The parameter sets
    are the definitions' own, and every form is explicit (C7's no-bare-form rule)."""
    params = {
        "BIND-DEVICE": {"device": device, "driver": driver},
        "UNBIND": {"device": device},
        "DEVICE-IO-WINDOW-WRITE": {"device": device, "window": W3C_WINDOW, "bytes": 4096},
        "DEVICE-INTAKE-COVER": {"intake": W3C_INTAKE, "device": device,
                                "window": W3C_WINDOW, "arrival_count": 3,
                                "byte_total": 12288},
    }[op]
    try:
        rec = world.call(op, **params)
        return "ADMITTED", rec
    except OpError as exc:
        return "REFUSED:%s" % getattr(exc, "rule", "?"), None


def w3c_custody_ended_world(case):
    """A world where the device WAS registered, bound, written to, and then UNBOUND.

    ITEM-21 NON-VACUITY IS THE CALLER'S AND IS ASSERTED HERE RATHER THAN ASSUMED: every
    step of the run-up must be ADMITTED, or "still admitted afterwards" would be a sentence
    about a world where nothing ever worked."""
    w = w3c_world()
    w.call("REGISTER-CAPABILITY", driver=W3C_DRV, device_class="block",
           capabilities=["device:%s" % W3C_DEV])
    for op in ("BIND-DEVICE", "DEVICE-IO-WINDOW-WRITE"):
        verdict, _ = w3c_device_act(w, op)
        case.assertEqual(verdict, "ADMITTED",
                         "%s was %s BEFORE the unbind, so nothing below is a statement "
                         "about the unbind" % (op, verdict))
    verdict, rec = w3c_device_act(w, "UNBIND")
    case.assertEqual(verdict, "ADMITTED", "the unbind itself was %s" % verdict)
    return w, rec


# =======================================================================================
class TheContainmentVOCABULARYIsHalfPresent(unittest.TestCase):
    """C6's two halves, measured against the law-data that would have to carry them.

    POPULATION: the live founding pack's CREATE-OP and CREATE-RULE records, founding
    1.24.0. BASIS: each definition's own `law_cited`, `checks` and `enforced_by` fields,
    read out of the pack as data and never out of a name in this file."""

    def setUp(self):
        self.pack = w3c_pack()
        self.ops = ops_of(self.pack)
        self.rules = rules_of(self.pack)

    def test_the_ops_citing_a_DEVICE_LAW_are_EXACTLY_the_named_six(self):
        named = sorted(n for n, d in self.ops.items()
                       if str(d.get("law_cited", "")).startswith("DEV-LAW"))
        self.assertEqual(named, sorted(W3C_DEVICE_LAW_OPS),
                         "the device-law vocabulary is %r — if a seventh has landed, C6's "
                         "establishment is stale and re-opens LOUDLY here" % (named,))

    def test_the_device_laws_are_EXACTLY_the_named_two(self):
        laws = sorted({self.ops[n]["law_cited"] for n in W3C_DEVICE_LAW_OPS})
        self.assertEqual(laws, sorted(W3C_DEVICE_LAWS),
                         "the device laws are %r" % (laws,))

    def test_the_UNBIND_HALF_EXISTS_and_cites_DEV_LAW_BIND(self):
        """THE HALF C6 CAN HAVE, named as PRESENT rather than left implied by the absence
        of the other."""
        d = self.ops["UNBIND"]
        self.assertEqual(d["law_cited"], "DEV-LAW-BIND")
        self.assertEqual(sorted(d["params"]), ["device"])
        self.assertEqual([(c["check"], c["action"], c["cite"]) for c in d["checks"]],
                         [("require_prior", "BIND-DEVICE", "DEV-LAW-BIND")])

    def test_EVERY_device_check_SCANS_AN_ACTION_and_the_table_is_the_named_one(self):
        """THE QUIESCE'S MISSING SHAPE, AS A PRESENT TABLE. Every row names an ACTION to
        scan for; an action scan reads history; history does not shrink when custody ends.
        A check reading a CURRENT holding would appear here as a row with no action."""
        table = sorted((n, c["check"], c.get("action"), c.get("cite"))
                       for n in W3C_DEVICE_LAW_OPS
                       for c in (self.ops[n].get("checks") or []))
        self.assertEqual(table, sorted(W3C_DEVICE_CHECK_TABLE),
                         "the device check table is %r" % (table,))
        self.assertEqual([r for r in table if r[2] is None], [],
                         "a device check with no action to scan has landed — that is the "
                         "current-holding shape a containment needs, and it re-opens this "
                         "establishment: %r" % (table,))

    def test_the_two_device_laws_ENFORCEMENT_CLAUSES_are_quoted_VERBATIM(self):
        """THE ABSENCE CARRIED BY A PRESENT VALUE. A containment or quiesce enforcer cannot
        arrive without moving one of these two strings."""
        for law, clause in sorted(W3C_ENFORCED_BY.items()):
            self.assertEqual(self.rules[law]["enforced_by"], clause,
                             "%s's enforcement clause has MOVED, so the containment "
                             "establishment must be re-taken" % law)

    def test_the_census_MOVES_when_a_SEVENTH_device_law_op_is_planted(self):
        """THE CONTROL FOR THE CENSUS ABOVE. Its answer is a fixed list, so it must be shown
        to see a member arrive — a list that cannot grow is a list that proves nothing."""
        planted = copy.deepcopy(self.pack)
        planted["steps"][-1]["records"].append(
            {"action": "CREATE-OP", "rule_cited": "ROOT-NEG-1",
             "payload": {"kind": "op_definition", "rule_id": "op:DEVICE-QUIESCE-PLANTED",
                         "name": "DEVICE-QUIESCE-PLANTED", "tier": "owner",
                         "definition": {"description": "planted", "params": {},
                                        "law_cited": "DEV-LAW-BIND", "checks": []}}})
        named = sorted(n for n, d in ops_of(planted).items()
                       if str(d.get("law_cited", "")).startswith("DEV-LAW"))
        self.assertIn("DEVICE-QUIESCE-PLANTED", named,
                      "the census cannot see a seventh device-law op, so its answer above "
                      "is not a measurement")

    def test_the_check_table_MOVES_when_a_CURRENT_HOLDING_check_is_planted(self):
        """THE CONTROL FOR THE TABLE. A check with no `action` is exactly the shape the
        table's second assertion exists to catch, so it is planted and must be caught."""
        planted = copy.deepcopy(self.pack)
        for st in planted["steps"]:
            for r in st["records"]:
                if r.get("action") == "CREATE-OP" \
                        and r["payload"]["name"] == "DEVICE-IO-WINDOW-WRITE":
                    r["payload"]["definition"]["checks"].append(
                        {"check": "binding", "param": "device", "require": "bound",
                         "cite": "DEV-LAW-BIND", "message": "planted current-holding check"})
        ops = ops_of(planted)
        rows = [(c["check"], c.get("action"))
                for c in ops["DEVICE-IO-WINDOW-WRITE"]["checks"]]
        self.assertIn(("binding", None), rows,
                      "the table cannot see a check that scans no action, so its emptiness "
                      "assertion above says nothing")


# =======================================================================================
#: THE WORLD IN WHICH THE COVERING-RECORD FINDING IS A STATEMENT ABOUT A LAW THAT EXISTED.
#: The last commit at founding 1.25.0 -- the device law as it stood BEFORE EP-30-W2 gave
#: DEVICE-INTAKE-COVER a `prior_value` row over BIND-DEVICE's stream. PINNED BY COMMIT AND
#: NEVER BY VERSION NUMBER (`era_pin`'s own stated cap), and RESOLVED by reading the pack's
#: own `founding_version` across the W2 boundary rather than transcribed out of a plan.
W3C_PRE_W2_COMMIT = "0bf95e30480b2cdcd45fd680b2c60c93d1350342"


class TheUNBINDContainsNOTHING(unittest.TestCase):
    """THE DRIVEN HALF, AND THE FINDING. C6 asks for containment records DRIVEN, NEVER
    NARRATED. Driving an UNBIND after a fault and calling it containment would narrate one:
    at this founding the device admits the next byte anyway.

    POPULATION: one booted world per row, at the live founding, driven through the shipped
    gate -- WITH ONE NAMED EXCEPTION, stated here rather than left for a reader to discover
    in a row: `test_a_COVERING_RECORD_is_still_admitted...` is driven at `W3C_PRE_W2_COMMIT`,
    because EP-30-W2 closed the gap that row measures and a claim cannot be driven in a world
    that no longer contains its subject (EP-30-W4, classified WORLD-SEPARABLE). BASIS: each
    act's own verdict and, where admitted, its record's own `rule_cited` -- never a value read
    back from a table in this file."""

    def test_the_unbind_IS_RECORDED_and_cites_its_rule(self):
        """C6's FIRST HALF, MET. The unbind is a decision and it carries DEV-LAW-BIND."""
        _, rec = w3c_custody_ended_world(self)
        self.assertEqual(rec["action"], "UNBIND")
        self.assertEqual(rec["rule_cited"], "DEV-LAW-BIND")

    def test_the_bindings_VIEW_is_EMPTY_after_the_unbind(self):
        """THE HALF THAT WORKS, and it is why this defect is invisible to every view-side
        guard: the served state is exactly right. The estate's guards run record -> view,
        and this is a question in the other direction."""
        w, _ = w3c_custody_ended_world(self)
        from subsystems.devices import DevicesView
        self.assertEqual(DevicesView(w.store).bindings(), {},
                         "the binding view still holds the device after an unbind")

    def test_EVERY_device_act_is_STILL_ADMITTED_after_custody_ENDS(self):
        """THE FINDING, AS A NAMED ROW RATHER THAN AS AN ABSENCE. Hand-computed before the
        run from the check table above; if a containment ever lands, this list SHRINKS and
        this row REDS LOUDLY -- which is the finding re-opening, never a defect."""
        w, _ = w3c_custody_ended_world(self)
        admitted = []
        for op in W3C_DEVICE_ACTS:
            verdict, _ = w3c_device_act(w, op)
            if verdict == "ADMITTED":
                admitted.append(op)
        self.assertEqual(sorted(admitted), sorted(W3C_ADMITTED_AFTER_CUSTODY_ENDS),
                         "the acts admitted after custody ended are %r" % (admitted,))

    def test_the_post_unbind_IO_RECORD_cites_DEV_LAW_BIND_like_any_other(self):
        """THE SHARPEST FORM OF W3c's FINDING, AND EP-30-W2 CLOSED IT.

        [DOCUMENTED FLIP -- EP-30-W3, 2026-08-19; a VERDICT member of this pass's population,
        proven by cause from the arm's own text ('REFUSED:DEV-LAW-BIND' != 'ADMITTED') and
        NOT era-pinned. CAUSE: EP-30-W2's `prior_value` row over BIND-DEVICE's stream.
        ASSERTED: the post-unbind write is ADMITTED and its record is INDISTINGUISHABLE from
        one written while custody held -- nothing in the record said the custody was over.
        SUPERSEDED: the write is REFUSED citing DEV-LAW-BIND and THERE IS NO RECORD AT ALL to
        be indistinguishable, which is a stronger closure than a distinguishable one would
        have been. REMAINS TRUE, unchanged: the subject is the gate's returned verdict, and
        the record it did or did not write, for ONE named act in ONE booted world after a
        named unbind. GIVEN UP: the indistinguishability finding. It is closed, and the
        measurement of it survives in W3c's own entry and in this bracket.

        THE SUBJECT IS LIVE AND THAT IS WHY THIS IS A FLIP AND NOT AN ERA-PIN: this class
        drives the SHIPPED gate at the CURRENT law, and era-pinning it would compare live
        records against historical law -- green while asserting the wrong thing. Its
        falsifiability was RE-DRIVEN after this repair rather than assumed: under
        `_pw_the_post_unbind_IO_refuses` the row still REDS.]"""
        w, _ = w3c_custody_ended_world(self)
        verdict, rec = w3c_device_act(w, "DEVICE-IO-WINDOW-WRITE")
        self.assertEqual(verdict, "REFUSED:DEV-LAW-BIND",
                         "the post-unbind write was %s -- EP-30-W2's revocation has stopped "
                         "biting, and that is a regression in the enforcement, not W3c's "
                         "finding returning" % verdict)
        self.assertIsNone(rec,
                          "a covering record was written for an act the gate REFUSED, so "
                          "the refusal answered by recording more: %r" % (rec,))

    def test_a_COVERING_RECORD_is_still_admitted_though_its_declaration_names_UNBIND_a_closer(self):
        """SECOND DIRECTION, and it contradicts a declaration in the law's own words:
        DEVICE-INTAKE-COVER's definition says "every intake declaration under this law names
        `unbind` as a closer -- the covering record closes when the custody that admitted the
        I/O ends". The closer is DECLARED and it is not ENFORCED.

        [WORLD NAMED -- EP-30-W4, 2026-08-19; classified WORLD-SEPARABLE and DRIVEN AT BOTH
        ENDS BEFORE THIS EDIT. THE CLAIM ABOVE IS UNCHANGED AND STILL ASSERTED, in the world
        where it is a statement about a law that existed: founding 1.25.0, pinned by commit.
        WHAT MOVED IS THE WORLD; THE ASSERTION DID NOT MOVE AND WAS NOT WEAKENED.

        WHY IT COULD NOT STAY AT THE LIVE FOUNDING, four cells driven at this hand:

            LIVE  clean          REFUSED:DEV-LAW-BIND
            LIVE  + its plant    REFUSED:DEV-LAW-BIND   <- IDENTICAL, so the control is dead
            ERA   clean          ADMITTED, rule_cited DEV-LAW-INTAKE
            ERA   + its plant    REFUSED:DEV-LAW-BIND   <- the plant is the ONLY source

        EP-30-W2 closed this gap, so at the live founding the row's SUBJECT is gone -- and the
        two LIVE cells are indistinguishable, so its falsifiability is gone with it. A flip to
        the post-W2 verdict would have landed a GREEN row whose control could not fail, and a
        green row whose control is dead is worse than a red row whose finding is visible.

        NO LIVE CLAIM IS GIVEN UP BY NAMING THE WORLD, which is the condition that makes this
        a repair and not a retreat. The LIVE post-unbind DEVICE-INTAKE-COVER verdict is
        asserted by `TheQUIESCEGAPIsPinnedWithItsOwnExpiry.
        test_the_post_unbind_INTAKE_COVER_is_ADMITTED`, driven GREEN at this hand.
        `test_EVERY_device_act_is_STILL_ADMITTED_after_custody_ENDS` does NOT cover it and
        never did: its loop re-binds the device on its FIRST step, so every later act in it is
        measured in a RE-BOUND world -- driven, all four acts ADMITTED there.

        THIS ROW IS ITS OWN CONTROL, which is why it is named in `_W3C_EXEMPT` rather than
        carried in `_W3C_ROWS`: a registry entry plants on the LIVE pack, and planting this
        row's world on the live founding would measure W2's law instead of the plant. The
        clean arm runs FIRST, or the red below would be measuring the fixture.]"""
        def cover(pack):
            w, _ = _w3c_in_world(pack, w3c_custody_ended_world, self)
            return w3c_device_act(w, "DEVICE-INTAKE-COVER")

        verdict, rec = cover(pack_at(W3C_PRE_W2_COMMIT))
        self.assertEqual(verdict, "ADMITTED",
                         "at founding 1.25.0 the covering record was %s -- the pinned commit "
                         "no longer names the world this finding was measured in" % verdict)
        self.assertEqual(rec["rule_cited"], "DEV-LAW-INTAKE")

        planted = pack_at(W3C_PRE_W2_COMMIT)
        _pw_the_covering_record_refuses(planted)
        planted_verdict, _ = cover(planted)
        self.assertEqual(planted_verdict, "REFUSED:DEV-LAW-BIND",
                         "a planted refusal did not move the covering record's verdict, so "
                         "the ADMITTED above is not a measurement: %r" % planted_verdict)

    def test_the_ROW_ABOVE_MOVES_when_the_LAW_REFUSES_the_post_unbind_act(self):
        """THE CONTROL, WITH ITS CAP STATED IN THE ROW. It proves the verdict list is a
        MEASUREMENT and not a constant: planted a check the post-unbind I/O cannot satisfy,
        the list shrinks.

        WHAT IT DOES NOT PROVE, said here rather than left for a reader to assume: it does
        not prove this row could see a REAL containment, because no containment mechanism is
        expressible in the licensed vocabulary today -- which is the finding itself. The
        plant refuses on both sides of the unbind; a real containment would refuse on one."""
        planted = copy.deepcopy(live_pack())
        for st in planted["steps"]:
            for r in st["records"]:
                if r.get("action") == "CREATE-OP" \
                        and r["payload"]["name"] == "DEVICE-IO-WINDOW-WRITE":
                    r["payload"]["definition"]["checks"].append(
                        {"check": "require_prior", "action": "PLANTED-QUIESCE-CLEARED",
                         "field": "device", "param": "device", "cite": "DEV-LAW-BIND",
                         "message": "planted: no record clears a quiesce for this device"})
        w = _World(planted)
        w.call("REGISTER-CAPABILITY", driver=W3C_DRV, device_class="block",
               capabilities=["device:%s" % W3C_DEV])
        self.assertEqual(w3c_device_act(w, "BIND-DEVICE")[0], "ADMITTED")
        self.assertEqual(w3c_device_act(w, "UNBIND")[0], "ADMITTED")
        verdict, _ = w3c_device_act(w, "DEVICE-IO-WINDOW-WRITE")
        self.assertEqual(verdict, "REFUSED:DEV-LAW-BIND",
                         "a planted refusal did not move the verdict, so the admissions "
                         "measured above are not measurements: %r" % verdict)


# =======================================================================================
class TheFaultSHAPESAndWhichOnesLeaveARecord(unittest.TestCase):
    """WHICH FAULTS C6 COULD EXHIBIT, censused BY DEFECT: every fault shape design/15's
    driver-fault entry names, against what the shipped instrument does with it.

    POPULATION: the shipped module source at `planning/vm/govshim/govshim.c` (READ, never
    modified by this pass) and the live founding. BASIS: the module's own text for the
    unrecorded shapes, and a driven gate verdict for the recorded ones."""

    @staticmethod
    def _cross_body():
        """THE `cross()` FUNCTION'S OWN TEXT. Sliced at its signature and its closing brace
        at column zero, so a later function's text cannot leak into the reading."""
        text = shim_sources()["govshim.c"]
        start = text.index("static int cross(")
        end = text.index("\n}\n", start)
        return text[start:end]

    def test_the_slice_IS_the_crossing_function(self):
        """THE KNOWN-ANSWER CONTROL FOR THE SLICE, before anything is concluded from it: the
        body must hold the wait that makes it the crossing, and must NOT hold the next
        function's name."""
        body = self._cross_body()
        self.assertIn("wait_for_completion_interruptible_timeout", body)
        self.assertNotIn("do_register", body)

    def test_the_TWO_UNANSWERED_fault_shapes_return_BEFORE_the_crossing_is_marked(self):
        """A HANG AND A DEPARTED COUNTERPART LEAVE NO RECORD, and it is the module's own
        text that says so: both cite a name and return before `c->crossed = 1` is ever
        reached, so nothing crosses and the gate writes nothing. This is C6's own red world
        -- "a fault with no record" -- arriving as SHIPPED BEHAVIOUR rather than as a plant,
        and it is RAISED rather than repaired: the module is not this pass's fence."""
        body = self._cross_body()
        mark = body.index("c->crossed = 1")
        self.assertEqual(body.count("c->crossed = 1"), 1,
                         "the crossing is marked in more than one place, so the ordering "
                         "below states nothing")
        for cite in ('"NO-BRAIN"', '"NO-ANSWER"', '"INTERRUPTED"'):
            self.assertLess(body.index(cite), mark,
                            "%s is cited AFTER the crossing is marked, which would mean the "
                            "shape does reach the gate" % cite)

    def test_the_ORDERING_READING_MOVES_when_the_MARK_is_planted_EARLIER(self):
        """THE CONTROL FOR THAT ORDERING. A reading whose answer is "before" must be shown to
        say "after" on a text where it is."""
        body = self._cross_body()
        planted = body.replace("mutex_lock(&call_lock);",
                               "mutex_lock(&call_lock); c->crossed = 1;", 1)
        self.assertLess(planted.index("c->crossed = 1"), planted.index('"NO-BRAIN"'),
                        "the reading cannot see a mark that moved, so its answer above is "
                        "not a measurement")

    def test_the_RECORDED_fault_shapes_are_the_REFUSALS_and_they_carry_their_rule(self):
        """THE HALF THAT DOES LEAVE A RECORD: a fault that REACHES the gate is refused AND
        RECORDED with its rule. Driven, and the record is read out of the store rather than
        inferred from the exception."""
        w = w3c_world()
        verdict, _ = w3c_device_act(w, "DEVICE-IO-WINDOW-WRITE")
        self.assertEqual(verdict, "REFUSED:DEV-LAW-BIND")
        refusals = w.refusals()
        self.assertEqual([r["rule_cited"] for r in refusals], ["DEV-LAW-BIND"],
                         "the refusal record is %r" % (refusals,))

    def test_the_ENUMERATED_capability_CONTAINS_NOTHING_so_that_fault_shape_cannot_be_exhibited(self):
        """design/24's check 1 is CAPABILITY CONTAINMENT -- "a driver may only touch the
        IRQ lines, DMA ranges and MMIO regions enumerated in its registration" -- and it is
        the DMA-violation fault shape's whole subject. DEV-LAW-BIND states it in law ("a
        capability is what it names, never what it omits") and NO CHECK READS THE LIST:
        BIND-DEVICE's one check scans for the driver's registration and never opens it.

        RAISED, NOT FIXED. It is named here because it decides which faults C6 could have
        exhibited: a driver reaching a device its capability does not enumerate is ADMITTED,
        so that fault never becomes a governed refusal at all."""
        w = w3c_world()
        w.call("REGISTER-CAPABILITY", driver=W3C_DRV, device_class="block",
               capabilities=["device:%s" % W3C_DEV])
        verdict, rec = w3c_device_act(w, "BIND-DEVICE", device="virtio0")
        self.assertEqual(verdict, "ADMITTED",
                         "a bind of an unenumerated device was %s — if containment has "
                         "landed, this establishment re-opens" % verdict)
        self.assertEqual(rec["rule_cited"], "DEV-LAW-BIND")

    def test_a_BARE_registration_still_licenses_a_bind(self):
        """THE SAME SENTENCE'S OTHER HALF, driven: "a registration that enumerates NO
        capabilities enumerates NOTHING and containment over it therefore permits nothing".
        A bare registration licenses a bind today."""
        w = w3c_world()
        w.call("REGISTER-CAPABILITY", driver="drv-bare", device_class="block",
               capabilities=[])
        verdict, _ = w3c_device_act(w, "BIND-DEVICE", driver="drv-bare")
        self.assertEqual(verdict, "ADMITTED",
                         "a bare registration was %s at a bind" % verdict)


# =======================================================================================
# §A64 FOR W3c — EVERY STRUCTURAL ROW DRIVEN AGAINST A NEAR-MISS
# =======================================================================================
#
# THE PLANTED WORLDS ARE LAW-DATA, which is what these rows are about: each plant is a
# deep copy of the live founding differing in exactly one field, and the SHIPPING row is
# run against it through unittest's own machinery rather than paraphrased.

def _w3c_op(pack, name):
    for st in pack["steps"]:
        for r in st["records"]:
            if r.get("action") == "CREATE-OP" and r["payload"]["name"] == name:
                return r["payload"]["definition"]
    raise AssertionError("the plant's subject %r is not in the pack" % name)


def _w3c_rule(pack, rid):
    for st in pack["steps"]:
        for r in st["records"]:
            if r.get("action") == "CREATE-RULE" and r["payload"].get("rule_id") == rid:
                return r["payload"]
    raise AssertionError("the plant's subject %r is not in the pack" % rid)


def _w3c_refuse(pack, op, action="PLANTED-NEVER-RECORDED"):
    """The one plant shape that makes a device act REFUSE: a prior scan for an action no
    record holds. It refuses on BOTH sides of an unbind, which is stated in the row that
    uses it -- a real containment would refuse on one."""
    _w3c_op(pack, op)["checks"].append(
        {"check": "require_prior", "action": action, "field": "device", "param": "device",
         "cite": "DEV-LAW-BIND", "message": "planted refusal"})


def _pw_a_seventh_device_law_op(pack):
    pack["steps"][-1]["records"].append(
        {"action": "CREATE-OP", "rule_cited": "ROOT-NEG-1",
         "payload": {"kind": "op_definition", "rule_id": "op:DEVICE-QUIESCE-PLANTED",
                     "name": "DEVICE-QUIESCE-PLANTED", "tier": "owner",
                     "definition": {"description": "planted", "params": {},
                                    "law_cited": "DEV-LAW-BIND", "checks": []}}})


def _pw_a_third_device_law(pack):
    _w3c_op(pack, "DECLARE-IO-WINDOW")["law_cited"] = "DEV-LAW-QUIESCE-PLANTED"


def _pw_an_extra_check_on_UNBIND(pack):
    _w3c_refuse(pack, "UNBIND", action="REGISTER-CAPABILITY")


def _pw_a_current_holding_check_on_IO(pack):
    _w3c_op(pack, "DEVICE-IO-WINDOW-WRITE")["checks"].append(
        {"check": "binding", "param": "device", "require": "bound",
         "cite": "DEV-LAW-BIND", "message": "planted current-holding check"})


def _pw_a_moved_enforcement_clause(pack):
    _w3c_rule(pack, "DEV-LAW-BIND")["enforced_by"] += " and a planted quiesce enforcer"


def _pw_the_post_unbind_IO_refuses(pack):
    _w3c_refuse(pack, "DEVICE-IO-WINDOW-WRITE")


def _pw_the_covering_record_refuses(pack):
    _w3c_refuse(pack, "DEVICE-INTAKE-COVER")


def _pw_the_unbind_itself_refuses(pack):
    _w3c_refuse(pack, "UNBIND")


def _pw_the_unbind_names_a_DIFFERENT_device(pack):
    """The unbind lands, and lands against another name -- so the view keeps the binding.

    [THE FIRST VERSION OF THIS PLANT EMPTIED `payload_from` AND MOVED NOTHING. The gate
    fills the payload from the parameters regardless, so the pack changed, the record did
    not, and the row stayed green. `test_every_plant_MOVES_something` compares PACKS and
    could not see it; only running the shipping row against the plant did. A plant is a
    claim about a WORLD and a pack diff is not that world.]"""
    _w3c_op(pack, "UNBIND")["payload_derive"] = {"device": {"tpl": "planted-{device}"}}


def _pw_the_bind_refuses(pack):
    _w3c_refuse(pack, "BIND-DEVICE")


def _pw_the_IO_refusal_cites_something_else(pack):
    for c in _w3c_op(pack, "DEVICE-IO-WINDOW-WRITE")["checks"]:
        if c.get("action") == "BIND-DEVICE":
            c["cite"] = "PLANTED-OTHER-RULE"


_W3C_ROWS = (
    (TheContainmentVOCABULARYIsHalfPresent,
     "test_the_ops_citing_a_DEVICE_LAW_are_EXACTLY_the_named_six",
     _pw_a_seventh_device_law_op),
    (TheContainmentVOCABULARYIsHalfPresent,
     "test_the_device_laws_are_EXACTLY_the_named_two", _pw_a_third_device_law),
    (TheContainmentVOCABULARYIsHalfPresent,
     "test_the_UNBIND_HALF_EXISTS_and_cites_DEV_LAW_BIND", _pw_an_extra_check_on_UNBIND),
    (TheContainmentVOCABULARYIsHalfPresent,
     "test_EVERY_device_check_SCANS_AN_ACTION_and_the_table_is_the_named_one",
     _pw_a_current_holding_check_on_IO),
    (TheContainmentVOCABULARYIsHalfPresent,
     "test_the_two_device_laws_ENFORCEMENT_CLAUSES_are_quoted_VERBATIM",
     _pw_a_moved_enforcement_clause),
    (TheUNBINDContainsNOTHING, "test_the_unbind_IS_RECORDED_and_cites_its_rule",
     _pw_the_unbind_itself_refuses),
    (TheUNBINDContainsNOTHING, "test_the_bindings_VIEW_is_EMPTY_after_the_unbind",
     _pw_the_unbind_names_a_DIFFERENT_device),
    (TheUNBINDContainsNOTHING, "test_EVERY_device_act_is_STILL_ADMITTED_after_custody_ENDS",
     _pw_the_post_unbind_IO_refuses),
    (TheUNBINDContainsNOTHING,
     "test_the_post_unbind_IO_RECORD_cites_DEV_LAW_BIND_like_any_other",
     _pw_the_post_unbind_IO_refuses),
    (TheFaultSHAPESAndWhichOnesLeaveARecord,
     "test_the_RECORDED_fault_shapes_are_the_REFUSALS_and_they_carry_their_rule",
     _pw_the_IO_refusal_cites_something_else),
    (TheFaultSHAPESAndWhichOnesLeaveARecord,
     "test_the_ENUMERATED_capability_CONTAINS_NOTHING_so_that_fault_shape_cannot_be_exhibited",
     _pw_the_bind_refuses),
    (TheFaultSHAPESAndWhichOnesLeaveARecord,
     "test_a_BARE_registration_still_licenses_a_bind", _pw_the_bind_refuses),
)

#: Rows with no plant IN THIS REGISTRY, and WHY each -- stated rather than left to a reader
#: to infer. The first three are themselves controls for other rows; the next three read the
#: SHIPPED MODULE SOURCE rather than law-data, and their near-miss is the ordering control
#: that sits beside them.
#:
#: THE LAST ONE IS A DIFFERENT KIND OF EXEMPTION AND IS NAMED AS ONE (EP-30-W4): it carries
#: its own plant INSIDE ITS OWN BODY because its control world is a NAMED ERA and not the
#: live founding. Every planter below is applied to `live_pack()`, so a registry entry would
#: have planted that row's control on a world its claim does not live in -- and the row would
#: have gone RED for EP-30-W2's law rather than for the plant, which is a control that cannot
#: fail wearing the look of one that can.
_W3C_EXEMPT = {
    "test_the_census_MOVES_when_a_SEVENTH_device_law_op_is_planted",
    "test_the_check_table_MOVES_when_a_CURRENT_HOLDING_check_is_planted",
    "test_the_ROW_ABOVE_MOVES_when_the_LAW_REFUSES_the_post_unbind_act",
    "test_the_slice_IS_the_crossing_function",
    "test_the_ORDERING_READING_MOVES_when_the_MARK_is_planted_EARLIER",
    "test_the_TWO_UNANSWERED_fault_shapes_return_BEFORE_the_crossing_is_marked",
    "test_a_COVERING_RECORD_is_still_admitted_though_its_declaration_names_UNBIND_a_closer",
}


def _run_w3c_against(pack, cls, meth):
    """Run a REAL W3c row against a PLANTED founding, through unittest's own machinery."""
    global _W3C_PACK
    saved = _W3C_PACK
    _W3C_PACK = pack
    try:
        return unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(cls(meth))
    finally:
        _W3C_PACK = saved


class TheW3cRowsCanBeMadeToFail(unittest.TestCase):
    """§A64 FOR THIS MOVEMENT. A row that passes only because nothing tried to fool it has
    not been driven.

    POPULATION: the (row, plant) pairs of `_W3C_ROWS`. BASIS: unittest's own result for the
    shipping row, run against a founding differing from the live one in exactly one field."""

    def test_the_LIVE_founding_passes_every_row(self):
        """FIRST, AND IT IS THE HALF THAT IS EASY TO SKIP: unplanted, every row must be
        GREEN, or a failure under a plant would be measuring the fixture."""
        for cls, meth, _plant in _W3C_ROWS:
            res = _run_w3c_against(None, cls, meth)
            self.assertTrue(res.wasSuccessful(),
                            "%s.%s FAILS on the LIVE founding: %r"
                            % (cls.__name__, meth,
                               [t[1][-400:] for t in res.failures + res.errors]))

    def test_every_row_reddens_under_its_own_plant(self):
        for cls, meth, plant in _W3C_ROWS:
            pack = live_pack()
            plant(pack)
            res = _run_w3c_against(pack, cls, meth)
            self.assertFalse(res.wasSuccessful(),
                             "%s.%s stayed GREEN under %s — it cannot see its own red world"
                             % (cls.__name__, meth, plant.__name__))

    def test_every_plant_MOVES_something(self):
        """A PLANTER THAT CHANGED NOTHING would leave its row looking driven while the table
        read as complete. NECESSARY AND NOT SUFFICIENT, and the cap is in the row because a
        plant of this pass was caught failing exactly here: this compares PACKS, and a pack
        edit the gate ignores moves nothing in the WORLD while passing this row. The row
        above is what catches that, because it runs the shipping row."""
        clean = json.dumps(live_pack(), sort_keys=True)
        for _cls, _meth, plant in _W3C_ROWS:
            pack = live_pack()
            plant(pack)
            self.assertNotEqual(json.dumps(pack, sort_keys=True), clean,
                                "%s changed nothing" % plant.__name__)

    def test_every_W3c_row_has_a_plant_or_a_STATED_exemption(self):
        classes = (TheContainmentVOCABULARYIsHalfPresent, TheUNBINDContainsNOTHING,
                   TheFaultSHAPESAndWhichOnesLeaveARecord)
        covered = {(c.__name__, m) for c, m, _ in _W3C_ROWS}
        missing = ["%s.%s" % (c.__name__, m) for c in classes for m in dir(c)
                   if m.startswith("test_") and (c.__name__, m) not in covered
                   and m not in _W3C_EXEMPT]
        self.assertEqual(missing, [],
                         "these W3c rows have neither a plant nor a stated exemption: %r"
                         % missing)

    def test_the_coverage_walk_FINDS_A_ROW_IT_WAS_NOT_TOLD_ABOUT(self):
        """THE CONTROL FOR THE WALK ABOVE, whose empty answer is the one carrying a claim."""
        class _Planted(unittest.TestCase):
            def test_a_row_nobody_covered(self):
                pass
        missing = [m for m in dir(_Planted)
                   if m.startswith("test_") and m not in _W3C_EXEMPT]
        self.assertEqual(missing, ["test_a_row_nobody_covered"],
                         "the coverage walk cannot find an uncovered row")


# =======================================================================================
# EP-30-P1 — THE QUIESCE GAP, PINNED AS A MEASURED ROW WITH ITS EXPIRY IN ITS OWN TEXT.
#
# [WHY THESE ROWS STAND BESIDE `TheUNBINDContainsNOTHING` RATHER THAN REPLACING IT, stated
#  here so a later reader does not read them as a duplicate and delete one set. W3c's rows
#  assert the same two admissions and NOT ONE OF THEM WAS TOUCHED BY THIS PASS. Two
#  differences are why EP-30-P1 was authored as its own unit rather than as an addendum:
#
#    1. THE WORLD. W3c's fixture drives a PRE-UNBIND `DEVICE-IO-WINDOW-WRITE` as its
#       non-vacuity step, so its covering row is COUPLED to that operation's verdict.
#       DRIVEN, NOT INFERRED: W3c's covering row REDS under a plant on
#       `DEVICE-IO-WINDOW-WRITE`, an operation it does not name. These rows found their
#       world without that step, so each pin row answers for the ONE operation it names
#       and passes the §A64 near-miss below. WHETHER W3c'S COUPLING IS A DEFECT OR A
#       DELIBERATE NON-VACUITY GUARD IS RAISED, NOT RULED, AND NOT REPAIRED HERE: W3c is
#       a CLOSED unit and its rows are not this pass's to move.
#
#    2. THE EXPIRY. No W3c row names the movement that must red it; its docstring says
#       only "if a containment ever lands". These rows name EP-30-W2 by name, and say in
#       their own text that EP-30-W1 must NOT red them.]

P1_DEV, P1_DRV = "virtio-p1", "drv-p1"
P1_WINDOW, P1_INTAKE = "device-io@p1", "device-intake@p1"

#: THE ONE SOURCE THESE ROWS READ, so §A64 can hand a SHIPPING row a planted world instead
#: of a paraphrase of it. `None` means the live founding, which every arm runs against.
_P1_PACK = None


def _p1_act(world, op, **params):
    """ONE act at a live world -> ("ADMIT", record) or ("REFUSE:<rule>", None). The gate's
    RETURNED VERDICT is the basis; nothing here counts records."""
    try:
        return "ADMIT", world.call(op, **params)
    except OpError as exc:
        return "REFUSE:%s" % getattr(exc, "rule", "?"), None


def _p1_founding_payload(action, op_name, **overrides):
    """A declaration payload taken from the FOUNDING'S OWN seeded record, filtered to the
    operation's declared params, with only the NAMES overridden.

    NOTHING IS INVENTED AND NOTHING IS TRANSCRIBED INTO THIS FILE. These declarations
    carry calibration provenance (`max_arrivals.cell`, `.population`, `.basis`) measured on
    a named guest at a named boot; a test has no standing to mint those, and a hand-typed
    copy would rot the moment the founding's own values moved."""
    pack = live_pack()
    allowed = set(ops_of(pack)[op_name]["params"])
    for st in pack["steps"]:
        for r in st["records"]:
            if r.get("action") == action:
                out = {k: copy.deepcopy(v) for k, v in r["payload"].items() if k in allowed}
                out.update(overrides)
                return out
    raise AssertionError("the founding holds no %s record to found this world on" % action)


def p1_world(case, issue_unbind=True):
    """A world founded BY ACTS: register, bind, declare the window, declare the intake, and
    then -- in the arm that has one -- unbind.

    THE WINDOW AND INTAKE NAMES ARE THIS WORLD'S OWN, founded by no record in the shipped
    pack, so the two declarations are genuinely DRIVEN rather than supplied by the
    founding's seed. That is the difference this unit turns on.

    `issue_unbind=False` IS R3'S CONTROL ARM AND IT IS NOT DECORATION: an ADMIT that could
    be explained by the unbind never landing says nothing about revocation.

    ITEM-21 NON-VACUITY IS ASSERTED HERE RATHER THAN ASSUMED -- every run-up act must be
    ADMITTED, or "still admitted afterwards" is a sentence about a world where nothing ever
    worked. [EP-30-P1's A1 lists the run-up as "BIND-DEVICE, DECLARE-IO-WINDOW,
    DECLARE-INTAKE, then UNBIND" and does NOT name REGISTER-CAPABILITY. Driven at
    authoring, that literal sequence REFUSES at step one citing CAP-IS-LAW, because
    BIND-DEVICE's one check scans for the driver's registration. The registration is
    performed here and the omission is REPORTED in the close rather than silently patched.]
    """
    world = _World(_P1_PACK) if _P1_PACK is not None else _World()
    run_up = [
        ("REGISTER-CAPABILITY", dict(driver=P1_DRV, device_class="block",
                                     capabilities=["device:%s" % P1_DEV])),
        ("BIND-DEVICE", dict(device=P1_DEV, driver=P1_DRV)),
        ("DECLARE-IO-WINDOW", _p1_founding_payload("DECLARE-IO-WINDOW", "DECLARE-IO-WINDOW",
                                                   window=P1_WINDOW)),
        ("DECLARE-INTAKE", _p1_founding_payload("DECLARE-INTAKE", "DECLARE-INTAKE",
                                                intake=P1_INTAKE, window=P1_WINDOW)),
    ]
    if issue_unbind:
        run_up.append(("UNBIND", dict(device=P1_DEV)))
    unbind_record = None
    for op, params in run_up:
        verdict, rec = _p1_act(world, op, **params)
        case.assertEqual(verdict, "ADMIT",
                         "the run-up act %s was %s, so nothing below is a statement about "
                         "custody" % (op, verdict))
        if op == "UNBIND":
            unbind_record = rec
    from subsystems.devices import DevicesView
    held = DevicesView(world.store).bindings()
    if issue_unbind:
        case.assertNotIn(P1_DEV, held,
                         "the unbind was ADMITTED and the binding view still holds %s, so "
                         "custody did not end and the rows below measure nothing" % P1_DEV)
    else:
        case.assertEqual(held.get(P1_DEV), P1_DRV,
                         "the control arm's custody does not HOLD, so it is not a control")
    return world, unbind_record


def _p1_io_write(world):
    return _p1_act(world, "DEVICE-IO-WINDOW-WRITE",
                   device=P1_DEV, window=P1_WINDOW, bytes=4096)[0]


def _p1_intake_cover(world):
    return _p1_act(world, "DEVICE-INTAKE-COVER", intake=P1_INTAKE, device=P1_DEV,
                   window=P1_WINDOW, arrival_count=3, byte_total=12288)[0]


def _p1_plant_refusal(pack, op):
    """THE PLANT SHAPE THE PIN ROWS CAN ACTUALLY SEE, selected BY THE CHECK'S ACTION.

    [DOCUMENTED FLIP -- EP-30-W4, 2026-08-19; classified REACHABLE-ELSEWHERE and driven at
    both ends before this edit. CAUSE: EP-30-W2 gave both consuming operations a
    `prior_value` row over BIND-DEVICE's stream, and `gate.refuse` STOPS AT THE FIRST FAILING
    CHECK, so in a post-unbind world a check APPENDED to the list is never reached at all.
    ASSERTED: an appended `require_prior` scanning for an action no record holds makes the
    named act REFUSE, and that refusal is the plant's observable. SUPERSEDED: it does still
    refuse -- but W2's row refuses FIRST and cites THE SAME RULE, so clean and planted both
    return `REFUSE:DEV-LAW-BIND` and NO ASSERTION CAN SEPARATE THEM. Driven, four cells, both
    pins. A control whose plant is never evaluated is not a weak control; it is not a control.
    REMAINS TRUE and is the whole of this repair: a plant is a claim about a WORLD, and the
    observable it has to move here is THE CITE THE GATE RETURNS. GIVEN UP: nothing either pin
    row asserts. No assertion anywhere was weakened -- what changed is the plant, never the
    claim, which is the distinction EP-30-W4 exists to hold.

    THE SHAPE: the ONE `prior_value` row W2 added to the named operation has its cite moved.
    The refusal still lands, on the same act, from the same chain, and it now cites a rule the
    pin row does not name -- so the pin row that names that operation REDS, and a pin on the
    OTHER operation is untouched, which is what the §A64 near-miss row below reads. The match
    count is asserted because a plant that matched NOTHING would leave both rows looking
    driven while proving nothing, and that is this family's own signature defect.]"""
    matched = [c for c in _w3c_op(pack, op)["checks"]
               if c["check"] == "prior_value" and c.get("action") == "BIND-DEVICE"]
    if len(matched) != 1:
        raise AssertionError(
            "this plant's subject is EXACTLY ONE `prior_value` row over BIND-DEVICE's stream "
            "on %s; the pack declares %d, so the plant no longer names the thing it was "
            "written against and every verdict below it would be measuring something else"
            % (op, len(matched)))
    matched[0]["cite"] = "PLANTED-P1-OTHER-RULE"


def _run_p1_against(pack, meth):
    """Run a REAL pin row against a PLANTED founding, through unittest's own machinery."""
    global _P1_PACK
    saved = _P1_PACK
    _P1_PACK = pack
    try:
        return unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
            TheQUIESCEGAPIsPinnedWithItsOwnExpiry(meth))
    finally:
        _P1_PACK = saved


def _p1_in_world(pack, fn, *a, **kw):
    """Run `fn` with a named pack installed as the P1 world's source, then restore it.

    The ACT-level twin of `_run_p1_against`, which installs a pack around a ROW. The exhibit
    row below needs this one because it compares two VERDICTS rather than two row results --
    and a verdict is what the shadowing is visible in."""
    global _P1_PACK
    saved = _P1_PACK
    _P1_PACK = pack
    try:
        return fn(*a, **kw)
    finally:
        _P1_PACK = saved


#: The act each pin row's operation is driven by, so a row iterating `_P1_PINS` reaches the
#: SHIPPED helper for the operation it names instead of re-deriving the call.
_P1_ACT_FOR = {"DEVICE-IO-WINDOW-WRITE": _p1_io_write,
               "DEVICE-INTAKE-COVER": _p1_intake_cover}


#: (pin row, the operation IT names, the OTHER consuming operation). The near-miss row
#: reads the third column and the falsifiability row reads the second.
_P1_PINS = (
    ("test_the_post_unbind_IO_WINDOW_WRITE_is_ADMITTED",
     "DEVICE-IO-WINDOW-WRITE", "DEVICE-INTAKE-COVER"),
    ("test_the_post_unbind_INTAKE_COVER_is_ADMITTED",
     "DEVICE-INTAKE-COVER", "DEVICE-IO-WINDOW-WRITE"),
)


class TheQUIESCEGAPIsPinnedWithItsOwnExpiry(unittest.TestCase):
    """EP-30-P1. CUSTODY ENDS AND THE CONSUMING OPERATIONS STILL ADMIT -- the gap held as a
    measured verdict with a tripwire, rather than as a paragraph in a closed unit's entry.

    THE MOVEMENT THAT MUST RED THESE ROWS IS **EP-30-W2**, the movement that gives the
    consuming operations a check reading the amended declaration. **A RED HERE IS THE
    FINDING ARRIVING AND IT IS NOT A REGRESSION:** it means revocation has begun to bite,
    and the correct response is to RETIRE these rows citing the ruling that landed W2 --
    never to repair them, and never to loosen them.

    **EP-30-W1 DOES NOT RED THESE ROWS AND MUST NOT.** W1 changes UNBIND's record into an
    amending declaration and adds no check to any consuming operation; W1's own A4 asserts
    that everything admitted before it is admitted after it. A red at W1 is a defect in W1
    or in these rows -- it is NOT this finding expiring.

    THE SUBJECT IS THE GATE'S RETURNED VERDICT for a named call after a named unbind. It is
    never a version number, never a count of operations, and never the presence of a check
    declaration -- the LABEL-not-a-WORLD failure `:823` retired at the taint layer.

    POPULATION: the two consuming operations DEVICE-IO-WINDOW-WRITE and DEVICE-INTAKE-COVER,
    named individually, one booted world per row at the live founding. BASIS: the gate's
    returned verdict, never a record count."""

    def test_the_post_unbind_IO_WINDOW_WRITE_is_ADMITTED(self):
        """PIN ONE. This row calls ONLY the operation it names, so its verdict is that
        operation's and no other's.

        [DOCUMENTED FLIP -- EP-30-W2, 2026-08-16. THE EXPIRY THIS ROW PREDICTED IN ITS OWN
        TEXT, ARRIVING. CAUSE: EP-30-W2 gave DEVICE-IO-WINDOW-WRITE a `prior_value` row over
        BIND-DEVICE's stream requiring the LATEST declaration for the device to still name a
        driver; W1b put op:UNBIND's records into that stream; an unbind declares no driver, so
        the licence stops computing. ASSERTED: the post-unbind write is ADMITTED -- custody
        ends and the bytes move anyway. SUPERSEDED: it is REFUSED, citing DEV-LAW-BIND.
        REMAINS TRUE, separated out and STILL ASSERTED, and it is this row's whole subject:
        the basis is THE GATE'S RETURNED VERDICT for a named call after a named unbind, in one
        booted world, and the row answers for the ONE operation it names -- which is why the
        near-miss row below still holds it green under a plant on the other consumer. GIVEN
        UP: the row no longer records the QUIESCE GAP. The gap is CLOSED; the measurement of
        it survives in EP-30-P1's own entry and in this bracket, and nowhere else. THIS IS A
        MEANING CHANGE AND NOT A RANGE CLOSURE -- licensed by this row's own docstring, by
        EP-30-W2 A7, and by that plan's S9 carve-out, which names these two rows as its only
        exemption.]"""
        world, _ = p1_world(self)
        self.assertEqual(_p1_io_write(world), "REFUSE:DEV-LAW-BIND",
                         "DEVICE-IO-WINDOW-WRITE still ADMITs after an unbind -- EP-30-W2's "
                         "revocation has stopped biting, and that is a regression in the "
                         "enforcement, not this finding returning")

    def test_the_post_unbind_INTAKE_COVER_is_ADMITTED(self):
        """PIN TWO, and it turned on a contradiction in the law's own words: an intake
        declaration names `unbind` as a CLOSER, and the closer was declared and not enforced.

        [DOCUMENTED FLIP -- EP-30-W2, 2026-08-16. CAUSE: as the row above, on
        DEVICE-INTAKE-COVER. ASSERTED: the post-unbind covering record is ADMITTED.
        SUPERSEDED: it is REFUSED, citing DEV-LAW-BIND -- the law's own declared closer now
        closes. REMAINS TRUE, separated out and STILL ASSERTED: the subject is the gate's
        returned verdict for this one operation in one booted world. GIVEN UP: the row no
        longer records the gap between what DEV-LAW-INTAKE's declarations SAY closes the
        covering record and what the gate ENFORCED. A MEANING CHANGE, licensed exactly as the
        row above.]"""
        world, _ = p1_world(self)
        self.assertEqual(_p1_intake_cover(world), "REFUSE:DEV-LAW-BIND",
                         "DEVICE-INTAKE-COVER still ADMITs after an unbind -- EP-30-W2's "
                         "revocation has stopped biting, and that is a regression in the "
                         "enforcement, not this finding returning")

    def test_the_UNBIND_LANDED_and_the_SAME_calls_ADMIT_WITH_NO_UNBIND_AT_ALL(self):
        """R3, AND IT IS THE ROW THAT MAKES THE TWO ABOVE MEAN ANYTHING. An ADMIT that could
        be explained by the unbind never landing says nothing about revocation, so both arms
        are driven and BOTH ARE RECORDED.

        ARM A the unbind is ADMITTED, cites DEV-LAW-BIND, and the binding view EMPTIES --
        so custody demonstrably ended. ARM B no unbind is ever issued, custody HOLDS, and
        the store holds ZERO unbind records.

        [DOCUMENTED FLIP -- EP-30-W3, 2026-08-19. THE EXPIRY THE TWO PIN ROWS ABOVE ALREADY
        TOOK, ARRIVING AT THE ROW THAT MAKES THEM MEAN ANYTHING. CAUSE: as those two --
        EP-30-W2's `prior_value` rows over BIND-DEVICE's stream, which W1b's amending unbind
        feeds. ASSERTED: the verdicts are IDENTICAL across the two arms, which was W3c's and
        EP-30-P1's finding: the landed unbind moved the VIEW and moved NO VERDICT.
        SUPERSEDED: they DIFFER -- ARM A REFUSES on both consuming operations, ARM B still
        ADMITS both. REMAINS TRUE, unchanged and still driven: ARM B is a genuine control --
        custody HOLDS, the store holds ZERO unbind records, and both acts are ADMITTED there,
        so an unbind is the ONLY difference between the two worlds. GIVEN UP: the row no
        longer records the QUIESCE GAP. The gap is CLOSED.

        AND THE ROW GETS STRONGER RATHER THAN WEAKER, which is why this is a repair and not
        a retirement. Before W2 the two arms agreed and the row could only report that the
        unbind changed nothing. NOW THE DIFFERENTIAL IS THE EVIDENCE: the refusals in ARM A
        are ATTRIBUTABLE TO THE UNBIND AND TO NOTHING ELSE, because ARM B runs the identical
        acts in the identical world without one and is admitted. A red on the ARM B line is
        still what it always was -- a broken world, not a finding.

        THE NAME STILL READS TRUE and is deliberately not changed: ARM B is the SAME calls
        with NO UNBIND AT ALL, and it still ADMITS."""
        with_unbind, rec = p1_world(self, issue_unbind=True)
        self.assertEqual(rec["action"], "UNBIND")
        self.assertEqual(rec["rule_cited"], "DEV-LAW-BIND")
        after = (_p1_io_write(with_unbind), _p1_intake_cover(with_unbind))

        without, none_rec = p1_world(self, issue_unbind=False)
        self.assertIsNone(none_rec)
        self.assertEqual([e for e in without.store.all() if e.get("action") == "UNBIND"], [],
                         "the control arm holds an UNBIND record, so it is not a control")
        control = (_p1_io_write(without), _p1_intake_cover(without))

        self.assertEqual(after, ("REFUSE:DEV-LAW-BIND", "REFUSE:DEV-LAW-BIND"),
                         "post-unbind verdicts are %r -- EP-30-W2's revocation has stopped "
                         "biting, and that is a regression in the enforcement, not "
                         "EP-30-P1's finding returning" % (after,))
        self.assertEqual(control, ("ADMIT", "ADMIT"),
                         "the control arm REFUSES with custody intact, so the world is "
                         "broken and the pins measure nothing: %r" % (control,))
        self.assertNotEqual(after, control,
                            "the two arms agree again, so the unbind moves the VIEW and no "
                            "VERDICT -- EP-30-P1's quiesce gap has re-opened")

    def test_each_PIN_ROW_REDS_under_a_planted_check_on_the_OPERATION_IT_NAMES(self):
        """R1. A ROW THAT CANNOT BE MADE TO RED HAS ASSERTED NOTHING. Planted AND REMOVED for
        each pin, through unittest's own machinery, running the SHIPPING row -- never a
        paraphrase of it. The clean arm runs FIRST, or a red under a plant would be
        measuring the fixture rather than the plant."""
        for meth, own_op, _other in _P1_PINS:
            self.assertTrue(_run_p1_against(None, meth).wasSuccessful(),
                            "%s fails on the LIVE founding, so its red below proves nothing"
                            % meth)
            pack = live_pack()
            _p1_plant_refusal(pack, own_op)
            self.assertFalse(_run_p1_against(pack, meth).wasSuccessful(),
                             "%s stayed GREEN under a planted refusal on %s -- it cannot see "
                             "its own red world" % (meth, own_op))
            self.assertTrue(_run_p1_against(None, meth).wasSuccessful(),
                            "%s did not return to GREEN once the plant was removed" % meth)

    def test_each_PIN_ROW_STAYS_GREEN_under_a_plant_on_the_OTHER_OPERATION(self):
        """R2, THE §A64 NEAR-MISS. A row that reds on ANY nearby change is not measuring its
        own subject. Each pin is run against a refusal planted on the OTHER consuming
        operation and must hold GREEN.

        THIS IS THE ROW THAT SEPARATES THIS UNIT FROM W3c's: driven at authoring, W3c's
        covering row REDS under a plant on DEVICE-IO-WINDOW-WRITE because its fixture drives
        that write as a non-vacuity step. These worlds do not, and each pin answers only for
        the operation it names.

        THE PLANT'S LIVENESS IS NOT ASSUMED HERE AND IS NOT RE-MEASURED HERE EITHER: the row
        above plants THE SAME SHAPE ON THE SAME OPERATION and requires a RED from the pin
        that names it. So a GREEN below is a statement about the pin's subject and never
        about a plant that quietly did nothing -- the two rows are each other's control."""
        for meth, _own, other_op in _P1_PINS:
            pack = live_pack()
            _p1_plant_refusal(pack, other_op)
            self.assertTrue(_run_p1_against(pack, meth).wasSuccessful(),
                            "%s RED under a plant on %s, an operation it does not name -- "
                            "its subject is entangled with that operation's verdict"
                            % (meth, other_op))

    def test_the_APPENDED_plant_form_is_INVISIBLE_at_the_LIVE_founding(self):
        """THE FINDING THAT MADE EP-30-W4 A UNIT, EXHIBITED RATHER THAN DESCRIBED -- and it is
        the evidence the whole classification rests on, so it is kept as a ROW and not left in
        a close nobody re-reads.

        `_p1_plant_refusal` WAS this shape until EP-30-W4 moved it, and the old shape is
        re-planted inline here on purpose: A REPAIR THAT DELETES ITS OWN EVIDENCE leaves the
        next seat to re-derive the thing that cost this one a pass. Appending a check to a
        consuming operation changes NOTHING a caller can observe at the live founding, because
        EP-30-W2's `prior_value` row over BIND-DEVICE's stream refuses FIRST and `gate.refuse`
        stops there -- so the planted check is never evaluated, and the genuine refusal and the
        planted one are identical in every field but time.

        A RED HERE IS A FINDING ARRIVING AND IS NOT A REGRESSION: it means an appended check
        has become reachable on that operation again, and the falsifiability row above must
        then be re-driven, because its plant may no longer be the only observable that moves.

        THE APPENDED CHECK CITES A RULE OF ITS OWN, AND THAT IS A CORRECTION TO THIS ROW'S
        FIRST FORM RATHER THAN A DETAIL. The historical plant cited `DEV-LAW-BIND` -- the SAME
        rule W2's shadowing check cites -- so its invisibility had TWO causes at once: it was
        never evaluated, AND it would have returned an indistinguishable string if it had been.
        Written that way this row COULD NOT FAIL FOR THE REASON IT NAMES: driven against a
        world with W2's check removed, the appended form became reachable and the row stayed
        GREEN. Giving the planted check its own cite separates the two causes and leaves this
        row asserting exactly ONE thing -- THE APPENDED CHECK IS NEVER EVALUATED -- which is
        the claim the classification actually rests on.

        THE CLEAN ARM IS READ FIRST and is asserted to be the post-W2 refusal, or "identical"
        would be a sentence about two worlds that were both broken."""
        for _meth, own_op, _other in _P1_PINS:
            act = _P1_ACT_FOR[own_op]
            clean = act(p1_world(self)[0])
            self.assertEqual(clean, "REFUSE:DEV-LAW-BIND",
                             "%s is %s at the live founding, so EP-30-W2's revocation is not "
                             "the thing doing the shadowing and this exhibit no longer names "
                             "its own cause" % (own_op, clean))

            pack = live_pack()
            _w3c_op(pack, own_op)["checks"].append(
                {"check": "require_prior", "action": "PLANTED-P1-NEVER-RECORDED",
                 "field": "device", "param": "device", "cite": "PLANTED-P1-UNREACHED",
                 "message": "the pre-EP-30-W4 plant shape, kept as the exhibit"})
            planted = _p1_in_world(pack, lambda: act(p1_world(self)[0]))

            self.assertEqual(clean, planted,
                             "%s: clean %r and planted %r DIFFER, so an APPENDED check is "
                             "reachable on this operation again -- EP-30-W4's finding has "
                             "expired and the falsifiability row above must be re-driven"
                             % (own_op, clean, planted))


if __name__ == "__main__":
    unittest.main()
