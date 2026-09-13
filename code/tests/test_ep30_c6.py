"""EP-30-C6 — THE ARC-C CLOSE: GROUP BATTERY · MAPPING RE-CHECK · COMMS LAW-SCHEDULE SETTLEMENT.

This harness proves the three things the C6 row (design/36 §6, order 7) names, in one place,
each by command, and it makes the owner-gate boundary MECHANICAL rather than a note:

  1. THE GROUP BATTERY (A1) — the arc's comms conformance ground runs GREEN AS A GROUP, in one
     process, not row-by-row. Row-by-row-only is C6 stop condition 5; the group is the subject.
  2. THE MAPPING RE-CHECK (A2/A3) — design/39 §6's four obligations trace to Arc C units, and
     every Arc C unit traces to remit text — a SET EQUALITY checked in BOTH directions.
  3. THE COMMS LAW-SCHEDULE SETTLEMENT (A4/A5) — every law cited by a shipped op is CREATED or
     SCHEDULED at a named unit, driven pack-wide. The settlement may re-schedule freely (within
     the row's authority) but MAY NOT MINT LAW QUIETLY: a create is an OWNER GATE (design/28 §5),
     refused mechanically here (R3) and raised, never applied without the owner's word.

DRIVEN FINDINGS, PRESERVED NOT SMOOTHED (reasoning-standard §7). The dangling set depends on
which citation SURFACE defines "cited by a shipped op", and the two surfaces disagree by design:

  * `checks[].cite` surface (archi's / the EP §1 method): 12 distinct laws cited by a refusal-path
    check row; TWO uncreated — COMM-LAW-CONTRACT, MEM-LAW-BUDGET. This surface targets the live
    containment harm (a REFUSAL citing a rule the founding does not contain — EP-25 ADDENDUM 4).
  * `law_cited` surface (the estate's SETTLED instrument, test_ep29.py:387): each op's SUCCESS
    decision cites its primary law; ELEVEN uncreated — the two above PLUS COMM-LAW-QUEUE (a second
    comms-family law, cited by the check-less skeletal ops COMMS-SEND/COMMS-RECV) and the memory /
    scheduling families (MEM-LAW-ALLOC/EVICT/PROTECT, SCHED-LAW-ADMIT/HALT/KILL-CHAIN/ORDER/
    PRIORITY).

The "12 vs 13" the countersign preserved: the DRIVEN distinct-check-cite total is 12 (archi's
count, reproduced here); the doc's "13" is the EP-25 historical PRE_EXISTING_UNSEEDED count
(test_ep25.py:856), of which DEV-LAW-BIND (EP-29) and COMM-LAW-SHARE-GRANT (EP-30-C4) have since
been created — 13 minus 2 = 11, the live law_cited population. A4 keeps the extraction command.

THE SETTLEMENT'S RESOLUTION, DRIVEN (A5):
  * memory family (MEM-LAW-ALLOC/BUDGET/EVICT/PROTECT) -> SCHEDULED to EP-31 (named successor in
    the plan list; memory's depth runs there) — WITHIN THE ROW'S AUTHORITY, no gate.
  * scheduling family (SCHED-LAW-*) -> SCHEDULED to EP-32 — WITHIN AUTHORITY, no gate.
  * comms family still cited-and-uncreated (COMM-LAW-CONTRACT, and under the settled law_cited
    surface COMM-LAW-QUEUE) -> the comms arc CLOSES at C6, so their scheduled home (Arc C) is
    expiring and there is NO named comms successor in the plan list. Per C6 stop condition 4 a
    dangle owed by nobody is NOT re-schedulable; it is a CREATE (owner gate, stop condition 3) or
    a raise. => this unit STOPS at the owner gate and RAISES; the create branch holds for the
    owner's morning. It mints nothing.

NO FULL-SUITE TOTAL IS A PASS (C6 stop condition 7): K2W rests at an owner gate and C4W/C5 are
siblings in flight; the battery is scoped to the comms rows it names. Any whole-suite figure is a
labelled CONSEQUENCE elsewhere, never an acceptance here.

Runs on this box (the harness alone):
    python3 -m unittest test_ep30_c6           (from tests/)
The A1 group battery spawns ONE subprocess that runs the battery modules TOGETHER.
"""

import copy
import json
import os
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(REPO, "tests")
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, TESTS)
import era_pin  # noqa: E402 — §A57 era-pin reads (EP-31-BUILD, board :2662)

PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")
#: §A57 era-pin (EP-31-BUILD, board :2662). C6's OWN era — the pack as C6 settled it, with
#: MEM-LAW-BUDGET still a SCHEDULED dangler. The dangle/schedule rows below read THIS era, not the
#: live pack, so they are robust to EP-31 creating MEM-LAW-BUDGET (exactly what C6 scheduled it for).
C6_ERA_COMMIT = "3293a0e79f11c54c04e042c217d0002e2643d339"


# =======================================================================================
# GROUND — the pack, the citation surfaces, the created set. Pure functions so A4's
# extraction is exactly reproducible and can be lifted verbatim into evidence.
# =======================================================================================

def load_pack():
    with open(PACK_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _records(pack):
    for st in pack["steps"]:
        for r in st.get("records", []):
            yield r


def created_laws(pack):
    """Every law id CREATED by a CREATE-RULE record — the founding's declared law records.

    This is the same 'declared' set the settled instrument reads (test_ep29.py rules_of /
    active_rules); a rule created here IS a record in the founding after the bump."""
    return {r["payload"]["rule_id"] for r in _records(pack)
            if r.get("action") == "CREATE-RULE"}


def _op_definitions(pack):
    return {r["payload"]["name"]: r["payload"]["definition"]
            for r in _records(pack) if r.get("action") == "CREATE-OP"}


def cited_via_law_cited(pack):
    """SURFACE 1 — the law each shipped op's SUCCESS decision cites (`definition.law_cited`).
    This is the surface the estate's settled dangling instrument uses (test_ep29.py:387)."""
    return {d.get("law_cited"): name  # law -> one witness op (last wins; only membership matters)
            for name, d in _op_definitions(pack).items() if d.get("law_cited")}


def cited_via_check_cite(pack):
    """SURFACE 2 — the law each REFUSAL-PATH check row cites (`definition.checks[].cite`).
    This is archi's / the EP §1 method: the containment harm is a refusal citing a missing rule."""
    out = {}
    for name, d in _op_definitions(pack).items():
        for chk in d.get("checks", []) or []:
            c = chk.get("cite")
            if c:
                out.setdefault(c, set()).add(name)
    return out


def dangling(cited_laws, created):
    """A law CITED and NOT CREATED — the dangle predicate, one surface at a time."""
    return sorted(l for l in cited_laws if l not in created)


def law_family(law):
    """The subsystem family a -LAW- id belongs to (COMM, MEM, SCHED, DEV, FS, ...)."""
    return law.split("-LAW-")[0] if "-LAW-" in law else None


# =======================================================================================
# THE SCHEDULE — content taken from THE PLAN LIST and nowhere else (C6 row: "the schedule
# data any rider row reads takes its content from THIS plan list"). design/36 §6 + the
# :1961 deferral ruling (line 656-664): "the depth campaign's EP list IS the deferral
# schedule ... memory/scheduler/comms lag because theirs is EP-30-C/31/32."
# =======================================================================================

#: family -> the plan-list unit that is scheduled to home that family's laws.
SCHEDULE_BY_FAMILY = {
    "MEM": "EP-31",         # design/36 §6 "EP-31 — M6: memory"
    "SCHED": "EP-32",        # design/36 §6 "EP-32 — M7: scheduling"
    "COMM": "EP-30-C",       # comms family homed in Arc C — WHICH CLOSES AT C6 (see below)
}

#: The units in SCHEDULE_BY_FAMILY that are FUTURE (a live successor a dangle can be scheduled
#: onto). Arc C (EP-30-C) is NOT here: C6 is its last unit, so a comms law "scheduled to Arc C"
#: has no future home — its schedule is expiring, which is exactly what the settlement resolves.
LIVE_SUCCESSOR_UNITS = {"EP-31", "EP-32"}

#: The Arc C plan-list units (design/36 §6 EP sketch, C0..C6) — the population A3 checks.
ARC_C_UNITS = ("C0", "C1", "C2", "C3", "C4", "C5", "C6")


class OwnerGateRefused(Exception):
    """Raised when a CREATE of a founding law is attempted WITHOUT the owner gate.
    design/28 §5 made mechanical: a settlement may re-schedule freely but may not mint law
    quietly. This is R3's refusal object."""


def apply_create(pack, law, *, gate_grant):
    """CREATE a founding law through the settlement. REFUSED unless an owner-gate grant is
    present (a recorded owner word / archi ruling id). Returns a NEW pack; never mutates input.

    THE GATE IS THE ENFORCEMENT OF THE CLAUSE, NOT A NOTE (CLAUDE.md transport lesson applied to
    law-minting): 'only through the ruled gate' is a capability here, not a promise."""
    if not gate_grant:
        raise OwnerGateRefused(
            f"CREATE of {law} refused: an owner gate (design/28 §5) is required to mint a "
            f"founding law; a settlement may re-schedule freely but never mint law quietly. "
            f"The branch STOPS for archi.")
    new = copy.deepcopy(pack)
    new["steps"].append({
        "step": f"settlement-create-{law.lower()}",
        "records": [{
            "actor": "owner", "action": "CREATE-RULE", "object": law,
            "rule_cited": "BOOT-INT",
            "payload": {"rule_id": law, "gate_grant": gate_grant,
                        "text": f"{law} — created through the owner-gated founding door"},
        }],
    })
    return new


def settle(danglers, created, *, schedule=SCHEDULE_BY_FAMILY, grants=None,
           comms_reschedule_target=None):
    """Classify every dangling law. The settlement claim HOLDS pack-wide iff every dangler is
    CREATED, CREATED-VIA-GATE, SCHEDULED (to a live successor), or RESCHEDULED (to a named
    successor). A NEEDS-GATE law is neither created nor scheduled and cannot be re-homed to a
    named successor — it is a create (owner gate) or a raise, never a silent drop (stop cond 4)."""
    grants = grants or {}
    out = {}
    for law in danglers:
        if law in created:
            out[law] = ("CREATED", None)
        elif law in grants:
            out[law] = ("CREATED-VIA-GATE", grants[law])
        else:
            fam = law_family(law)
            succ = schedule.get(fam)
            if succ in LIVE_SUCCESSOR_UNITS:
                out[law] = ("SCHEDULED", succ)
            elif comms_reschedule_target and fam == "COMM":
                out[law] = ("RESCHEDULED", comms_reschedule_target)
            else:
                out[law] = ("NEEDS-GATE", None)
    return out


def claim_holds(settlement):
    """Pack-wide: nothing dangles that is neither created nor scheduled."""
    return all(status in ("CREATED", "CREATED-VIA-GATE", "SCHEDULED", "RESCHEDULED")
               for status, _ in settlement.values())


def needs_gate(settlement):
    return sorted(law for law, (status, _) in settlement.items() if status == "NEEDS-GATE")


# =======================================================================================
# A1 — THE GROUP BATTERY, RUN AS A GROUP.
# =======================================================================================

#: The comms conformance ground, each member named with the conformance role the C6 row cites.
#: Run TOGETHER in one process — the group, not the row. C4W/C5 sibling status is noted, but
#: the shadow/probe conformance (C5) and the settled channel/message/custody/medium ground
#: (C0-C4, test_comms round-trip) are the arc's comms battery.
BATTERY = [
    ("test_ep30_c0", "substrate / durability ground"),
    ("test_ep30_c1", "channels — COMMS-OPEN, two-channel invariant, probe set"),
    ("test_ep30_c2", "messages — COMMS-SEND/RECV syscall-semantic rows, probe set"),
    ("test_ep30_c3", "custody — T-CUSTODY-IS-DERIVED (channel state), T-CUSTODY-MATRIX (comms)"),
    ("test_ep30_c4", "shared medium — SHM-GRANT, probe set"),
    ("test_ep30_c5", "shadow — shadow-diff / divergence-halt probe set"),
    ("test_comms",   "round-trip — open/send/recv/close, view fold round-trips"),
]

#: A floor so an empty/failed-discovery run cannot pass as green (the fleet's signature
#: 'confident empty answer' defect). Observed 128; floor set well below to survive small drift.
BATTERY_TEST_FLOOR = 120


class TheGroupBattery(unittest.TestCase):
    """A1 — DRIVEN. The comms conformance battery, green AS A GROUP, in one process."""

    def test_the_comms_battery_is_green_as_a_group(self):
        modules = [m for m, _role in BATTERY]
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "-v", *modules],
            cwd=TESTS, capture_output=True, text=True)
        tail = proc.stderr.strip().splitlines()
        joined = "\n".join(tail[-6:])
        # GREEN AS A GROUP: one invocation, all modules, 0 failures / 0 errors.
        self.assertEqual(proc.returncode, 0,
                         f"the comms battery is NOT green as a group:\n{joined}")
        self.assertIn("OK", proc.stderr, f"group run did not end OK:\n{joined}")
        # NON-VACUITY: the group actually ran a real population, not an empty filter.
        ran = [ln for ln in tail if ln.startswith("Ran ")]
        self.assertTrue(ran, f"could not read a 'Ran N tests' line:\n{joined}")
        n = int(ran[-1].split()[1])
        self.assertGreaterEqual(n, BATTERY_TEST_FLOOR,
                                f"group ran only {n} tests (< floor {BATTERY_TEST_FLOOR}) — "
                                f"a shrunk group is a stop, not a silent pass")


# =======================================================================================
# A2 / A3 — THE MAPPING, BOTH DIRECTIONS, AS A SET EQUALITY.
# design/39 §6 (the four obligations) + design/36 §6 enumeration mapping note (line 886-890).
# =======================================================================================

#: design/39 §6 — the FOUR obligations EP-30-C's authoring owes design/39, verbatim in gist.
OBLIGATIONS = {
    "O1-crossings": "channel lifecycle / sends / receives authored as CROSSINGS of the "
                    "system-facing channel of an ENTITY, never process-to-process traffic",
    "O2-user-channel": "the USER-FACING channel treated as a first-class, distinct opening "
                       "(consent + presentation; the external-world seam)",
    "O3-two-channel": "the TWO-CHANNEL default stated as the INVARIANT; any additional opening "
                      "is a raise, never a convenience",
    "O4-row-vocabulary": "the ENTITY / PROCESS / CUSTODY split of §2 used as the ROW VOCABULARY",
}

#: obligation -> the Arc C unit that discharged it (design/36 §6 mapping note, line 886-888:
#: "§6's four obligations -> C1 (crossings, user channel, invariant) and C0/C1 (row vocabulary)").
OBLIGATION_TO_UNIT = {
    "O1-crossings": ("C1",),        # channels — the crossing vocabulary lands with COMMS-OPEN
    "O2-user-channel": ("C1",),     # the user-facing role is a COMMS-OPEN role (value_domain)
    "O3-two-channel": ("C1",),      # the two-channel invariant is COMMS-OPEN's live_slot check
    "O4-row-vocabulary": ("C0", "C1"),  # entity/process/custody split — substrate + channels
}

#: unit -> the remit line it serves (design/36 §6 mapping note, line 888-889:
#: "remit text -> C0 substrate/durability, C1 channels, C2 messages, C3 custody, C4 shared
#: medium, C5 shadow, C6 battery").
UNIT_TO_REMIT = {
    "C0": "substrate / durability",
    "C1": "channels",
    "C2": "messages",
    "C3": "custody",
    "C4": "shared medium",
    "C5": "shadow",
    "C6": "battery / close",
}


class TheObligationMapping(unittest.TestCase):
    """A2 — DRIVEN. Every design/39 §6 obligation traces to a named Arc C unit; nothing unmapped.

    R2's first face lives here: a dropped obligation mapping REDS this, naming the unmapped item.
    """

    def _every_obligation_maps(self, obligation_to_unit):
        unmapped = [o for o in OBLIGATIONS if not obligation_to_unit.get(o)]
        self.assertFalse(unmapped, f"§6 obligations tracing to NO unit (a mapping gap, "
                                   f"C6 stop condition 2): {unmapped}")
        # every named target is a real Arc C unit
        for o, units in obligation_to_unit.items():
            for u in units:
                self.assertIn(u, ARC_C_UNITS,
                              f"{o} maps to {u}, not an Arc C unit")

    def test_all_four_obligations_map_to_a_named_unit(self):
        self.assertEqual(len(OBLIGATIONS), 4, "design/39 §6 owes exactly four obligations")
        self._every_obligation_maps(OBLIGATION_TO_UNIT)

    def test_a_dropped_obligation_mapping_reds(self):
        """R2 (mapping direction 1). Drop one obligation's unit -> A2 REDS. Restore -> greens."""
        broken = dict(OBLIGATION_TO_UNIT)
        broken["O3-two-channel"] = ()      # the plant: the invariant now maps to nobody
        with self.assertRaises(AssertionError):
            self._every_obligation_maps(broken)
        self._every_obligation_maps(OBLIGATION_TO_UNIT)   # restore -> greens


class TheUnitRemitMapping(unittest.TestCase):
    """A3 — DRIVEN. Every Arc C unit traces to a remit line; set equality BOTH ways.

    R2's second face lives here: a unit tracing to no remit REDS this, naming the item.
    """

    def _set_equality_both_ways(self, unit_to_remit):
        # direction 1: no unit tracing to nothing (scope creep)
        tracing_to_nothing = [u for u in ARC_C_UNITS if not unit_to_remit.get(u)]
        self.assertFalse(tracing_to_nothing,
                         f"Arc C units tracing to NO remit (scope creep, stop cond 2): "
                         f"{tracing_to_nothing}")
        # direction 2: no remit line with no unit (a gap) — the mapping's units == the arc's units
        self.assertEqual(set(unit_to_remit) & set(ARC_C_UNITS), set(ARC_C_UNITS),
                         "a remit line has no unit — set equality fails in the reverse direction")

    def test_every_unit_maps_to_a_remit_line_set_equality(self):
        self.assertEqual(set(UNIT_TO_REMIT), set(ARC_C_UNITS),
                         "the unit->remit map and the Arc C unit set must be equal as sets")
        self._set_equality_both_ways(UNIT_TO_REMIT)

    def test_a_unit_tracing_to_nothing_reds(self):
        """R2 (mapping direction 2). A unit tracing to no remit -> A3 REDS. Restore -> greens."""
        broken = dict(UNIT_TO_REMIT)
        broken["C4"] = ""      # the plant: shared-medium unit now traces to nothing
        with self.assertRaises(AssertionError):
            self._set_equality_both_ways(broken)
        self._set_equality_both_ways(UNIT_TO_REMIT)   # restore -> greens


# =======================================================================================
# A4 — THE DANGLING SET, RE-DRIVEN AT BUILD, ON BOTH SURFACES.
# =======================================================================================

#: The check-cite dangle PAIR the EP §1 / archi drove (SURFACE 2). Asserted so a move is visible.
EXPECTED_CHECK_CITE_DANGLE = ("COMM-LAW-CONTRACT", "MEM-LAW-BUDGET")

#: The law_cited standing set (SURFACE 1) — the settled instrument's 11 (test_ep29.py
#: THE_LAWS_LEFT_STANDING). Asserted so a move is visible.
EXPECTED_LAW_CITED_DANGLE = (
    "COMM-LAW-CONTRACT", "COMM-LAW-QUEUE",
    "MEM-LAW-ALLOC", "MEM-LAW-BUDGET", "MEM-LAW-EVICT", "MEM-LAW-PROTECT",
    "SCHED-LAW-ADMIT", "SCHED-LAW-HALT", "SCHED-LAW-KILL-CHAIN",
    "SCHED-LAW-ORDER", "SCHED-LAW-PRIORITY",
)


class TheDanglingSetRedriven(unittest.TestCase):
    """A4 — DRIVEN. Re-drive the dangling set over the live pack, both surfaces, id for id."""

    def setUp(self):
        self.pack = era_pin.pack_at(C6_ERA_COMMIT, missing="assert")  # §A57 era-pin :2662
        self.created = created_laws(self.pack)

    def test_check_cite_surface_yields_the_pair(self):
        cite = cited_via_check_cite(self.pack)
        # the "12 vs 13" settled: the DRIVEN distinct check-cite total is 12 (archi's count).
        self.assertEqual(len(cite), 12,
                         "the driven distinct check-cite total is 12 (archi's method); the doc's "
                         "13 is the EP-25 historical PRE_EXISTING_UNSEEDED count, minus the two "
                         "since created (DEV-LAW-BIND, COMM-LAW-SHARE-GRANT)")
        dang = tuple(dangling(cite, self.created))
        self.assertEqual(dang, EXPECTED_CHECK_CITE_DANGLE,
                         "the check-cite dangle pair moved from the authored {CONTRACT, BUDGET}")

    def test_law_cited_surface_yields_eleven_including_comm_law_queue(self):
        cited = cited_via_law_cited(self.pack)
        dang = tuple(dangling(cited, self.created))
        self.assertEqual(dang, EXPECTED_LAW_CITED_DANGLE,
                         "the settled law_cited standing set moved from the 11 that test_ep29's "
                         "THE_LAWS_LEFT_STANDING pins; note it INCLUDES COMM-LAW-QUEUE, a second "
                         "comms-family dangle the check-cite surface does not reach")
        # PRESERVE, DON'T SMOOTH: the two surfaces agree on the two named laws and disagree on
        # COMM-LAW-QUEUE — recorded, not harmonised.
        self.assertIn("COMM-LAW-QUEUE", dang)
        self.assertNotIn("COMM-LAW-QUEUE", dangling(cited_via_check_cite(self.pack), self.created))

    def test_the_created_witnesses_prove_the_walk_can_distinguish(self):
        """Positive control on the walk (test_ep29's discipline): it also finds CREATED laws, so
        its 'uncreated' answer is interpretable rather than a walk that reds on everything."""
        cited = set(cited_via_law_cited(self.pack))
        self.assertTrue(cited & self.created,
                        "the walk finds no created cited law — its dangle set is uninterpretable")
        self.assertIn("COMM-LAW-SHARE-GRANT", self.created)   # cured by EP-30-C4
        self.assertIn("DEV-LAW-BIND", self.created)            # cured by EP-29


# =======================================================================================
# A5 — THE SETTLEMENT, AND THE CLAIM DRIVEN PACK-WIDE.
# =======================================================================================

class TheSettlement(unittest.TestCase):
    """A5 — DRIVEN. Each dangle resolved; the claim driven pack-wide; the owner gate made to bite.

    The subject is the SETTLED law_cited surface (the estate's own instrument), which is the
    stronger reading: it resolves every cited-uncreated law, not only the refusal-path subset.
    """

    def setUp(self):
        self.pack = era_pin.pack_at(C6_ERA_COMMIT, missing="assert")  # §A57 era-pin :2662
        self.created = created_laws(self.pack)
        self.danglers = dangling(cited_via_law_cited(self.pack), self.created)

    def test_memory_and_scheduling_reschedule_within_authority(self):
        s = settle(self.danglers, self.created)
        # memory family -> EP-31, scheduling family -> EP-32 — named successors, no gate.
        for law in ("MEM-LAW-ALLOC", "MEM-LAW-BUDGET", "MEM-LAW-EVICT", "MEM-LAW-PROTECT"):
            self.assertEqual(s[law], ("SCHEDULED", "EP-31"),
                             f"{law} should re-schedule to EP-31 (memory) within authority")
        for law in ("SCHED-LAW-ADMIT", "SCHED-LAW-HALT", "SCHED-LAW-KILL-CHAIN",
                    "SCHED-LAW-ORDER", "SCHED-LAW-PRIORITY"):
            self.assertEqual(s[law], ("SCHEDULED", "EP-32"),
                             f"{law} should re-schedule to EP-32 (scheduling) within authority")

    def test_the_comms_dangles_need_the_owner_gate(self):
        """The load-bearing STOP. The comms family's schedule (Arc C) closes at C6, no named
        comms successor remains, so the comms dangles cannot be re-homed -> NEEDS-GATE (create =
        owner gate, stop cond 3; a dangle owed by nobody is not re-schedulable, stop cond 4)."""
        s = settle(self.danglers, self.created)
        self.assertEqual(needs_gate(s), ["COMM-LAW-CONTRACT", "COMM-LAW-QUEUE"])
        # THE CLAIM DOES NOT YET HOLD PACK-WIDE — this is the owner-gate STOP, not a defect.
        self.assertFalse(claim_holds(s),
                         "the pack-wide claim must NOT read as holding while comms creates are "
                         "unresolved — that would be minting the settlement's own conclusion")

    def test_the_settlement_completes_once_the_gate_grants(self):
        """Proof the settlement COMPLETES on the owner's word, WITHOUT minting anything here: a
        simulated grant token (an owner-morning ruling) settles the comms pair and the claim then
        holds pack-wide. No pack edit; grants are tokens, not CREATE-RULE records."""
        grants = {"COMM-LAW-CONTRACT": "owner-morning-ruling",
                  "COMM-LAW-QUEUE": "owner-morning-ruling"}
        s = settle(self.danglers, self.created, grants=grants)
        self.assertTrue(claim_holds(s),
                        "with the owner-gated creates granted, every cited law is created or "
                        "scheduled — the claim holds pack-wide")
        self.assertEqual(needs_gate(s), [])

    def test_a_reschedule_needs_a_named_successor_never_a_silent_drop(self):
        """Stop condition 4, made mechanical: a comms law CANNOT be scheduled to a non-successor.
        Only a NAMED successor re-homes it; absent one it stays NEEDS-GATE (a create or a raise)."""
        # no comms successor exists -> NEEDS-GATE
        s = settle(self.danglers, self.created)
        self.assertIn("COMM-LAW-CONTRACT", needs_gate(s))
        # a NAMED comms successor (were one to exist in the plan list) would re-home it, no gate —
        # but naming one is archi's ruling, not this build's to invent.
        s2 = settle(self.danglers, self.created, comms_reschedule_target="EP-XX(named-by-archi)")
        self.assertEqual(s2["COMM-LAW-CONTRACT"], ("RESCHEDULED", "EP-XX(named-by-archi)"))


# =======================================================================================
# R1 — A DANGLE IS CAUGHT. R3 — A CREATE WITHOUT THE GATE IS REFUSED.
# =======================================================================================

def _pack_with_planted_dangle(pack, law="PLANT-LAW-NOBODY"):
    """A copy of the pack with a shipped op citing a law nothing creates or schedules."""
    new = copy.deepcopy(pack)
    new["steps"].append({
        "step": "r1-planted-dangle",
        "records": [{
            "actor": "PC_RUNTIME", "action": "CREATE-OP", "object": "op:PLANT-OP",
            "rule_cited": "CAP-IS-LAW",
            "payload": {"kind": "op_definition", "rule_id": "op:PLANT-OP", "name": "PLANT-OP",
                        "definition": {"description": "a planted shipped op",
                                       "law_cited": law, "checks": []}},
        }],
    })
    return new


class R1_ADangleIsCaught(unittest.TestCase):
    """R1 — the settlement claim must catch a FRESH dangle, or it is not the settlement."""

    def setUp(self):
        self.grants = {"COMM-LAW-CONTRACT": "owner-morning-ruling",
                       "COMM-LAW-QUEUE": "owner-morning-ruling"}  # the known comms pair, granted

    def _claim_holds_over(self, pack):
        created = created_laws(pack)
        danglers = dangling(cited_via_law_cited(pack), created)
        return claim_holds(settle(danglers, created, grants=self.grants))

    def test_a_planted_dangle_reds_the_claim(self):
        base = load_pack()
        # baseline: with the comms pair granted, the claim holds (nothing else dangles).
        self.assertTrue(self._claim_holds_over(base),
                        "baseline claim should hold once the comms pair is granted")
        planted = _pack_with_planted_dangle(base)          # add an unscheduled, ungrantable dangle
        self.assertFalse(self._claim_holds_over(planted),
                         "a fresh uncreated-unscheduled citation must RED the claim, naming it")
        s = settle(dangling(cited_via_law_cited(planted), created_laws(planted)),
                   created_laws(planted), grants=self.grants)
        self.assertIn("PLANT-LAW-NOBODY", needs_gate(s))     # the claim NAMES the fresh dangle
        # removing the plant greens it again (the base pack still holds under the grants)
        self.assertTrue(self._claim_holds_over(base))


class R3_ACreateWithoutTheGateIsRefused(unittest.TestCase):
    """R3 — the owner-gate boundary made to bite. A settlement may re-schedule freely but may not
    mint law quietly. A create with no gate is REFUSED mechanically (design/28 §5), not a note."""

    def test_a_naked_comms_law_create_is_refused(self):
        base = load_pack()
        with self.assertRaises(OwnerGateRefused):
            apply_create(base, "COMM-LAW-CONTRACT", gate_grant=None)     # naked create -> refused
        # the naked attempt adds nothing (deepcopy semantics; it never writes disk) — yet the law
        # IS on the real pack now, created through the owner-gate this EP represents
        # (EP-FND-COMMS-LAWS, the gated create), never through the refused naked path.
        self.assertIn("COMM-LAW-CONTRACT", created_laws(load_pack()))

    def test_the_gate_permits_a_create_only_with_a_recorded_grant(self):
        """The check must be able to PASS as well as fail: WITH a grant, the create proceeds (on a
        copy). This is what archi's ruling would authorise; this build never carries the grant."""
        base = load_pack()
        minted = apply_create(base, "COMM-LAW-CONTRACT", gate_grant=":owner-morning")
        self.assertIn("COMM-LAW-CONTRACT", created_laws(minted))          # created on the COPY
        self.assertIn("COMM-LAW-CONTRACT", created_laws(load_pack()))     # now on the real pack — EP-FND-COMMS-LAWS' gated create


if __name__ == "__main__":
    unittest.main(verbosity=2)
