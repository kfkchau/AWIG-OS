"""EP-30-K1 — THE SIXTEENTH CHECK KIND: `bound_field`, binding the record so a holder can
be asked about.

THE ONE SENTENCE THIS UNIT EXISTS FOR: the estate could ask whether a record EXISTS with a
field equal to a parameter. It could not ask whether *THIS* record — the one this parameter
names — has its field equal to *THAT* parameter. THE MISSING CAPABILITY IS BINDING THE
RECORD, NOT COMPARING TO IT.

EVERY VERIFICATION PROBE THIS UNIT RAN LANDS HERE AS A REGRESSION ROW (charter). The rows
are named for the plan's own acceptance and red-world ids so a reader can pair them with
`planning/evidence/EP-30-K1/`.

SELF-READING, and it is named at authoring per EP-SHAPE's amended definition (`:1867`):
several rows below read THIS FILE and the engine's SOURCE rather than only its behaviour —
the minimality gate is a claim about what the arms ASK, and a claim about what code asks
cannot be discharged by calling it.
"""

import ast
import copy
import json
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import founding.install as inst                                    # noqa: E402
from kernel import opdefs                                          # noqa: E402
from kernel.blobs import BlobStore                                 # noqa: E402
from kernel.boot import build_kernel                               # noqa: E402
from kernel.errors import OpError                                  # noqa: E402

PACK_PATH = os.path.join(ROOT, "src/founding/founding-pack.json")
REAL = json.load(open(PACK_PATH, encoding="utf-8"))
TRUE_LOADER = inst.load_pack        # captured ONCE, before any patch

OP = "FILE-CUSTODY-TRANSFER"
DEVICE, DRIVER = "dev:sda1", "drv:block"
GIVER, TAKER, THIRD, STRANGER = "ent:giver", "ent:taker", "ent:third", "ent:stranger"
H1, H2 = "/mnt/one", "/mnt/two"


def op_definition(pack, name):
    for step in pack["steps"]:
        for r in step["records"]:
            if r.get("action") == "CREATE-OP" and r["payload"].get("name") == name:
                return r["payload"]["definition"]
    raise AssertionError("%s carries no definition in the founding pack" % name)


class WorldCase(unittest.TestCase):
    """A kernel built from a pack amended IN A TEMP TREE. The repo pack is never written.

    THE AMENDMENT IS PROVEN LANDED BY READING `checks` BACK OUT OF THE FOUNDED RECORD, never
    out of the file that produced it. A world built from a pack the installer silently ignored
    would green every row below while testing the shipped shape — the failure that makes a
    whole file's worth of evidence worthless without anyone seeing a red.
    """

    def build(self, checks=None, op=OP):
        pack = copy.deepcopy(REAL)
        if checks is not None:
            for step in pack["steps"]:
                for r in step["records"]:
                    if r.get("action") == "CREATE-OP" and r["payload"].get("name") == op:
                        r["payload"]["definition"]["checks"] = checks
        d = tempfile.mkdtemp()
        pp = os.path.join(d, "pack.json")
        with open(pp, "w", encoding="utf-8") as fh:
            json.dump(pack, fh)
        inst.PACK_PATH = pp
        inst.load_pack = lambda path=None: TRUE_LOADER(pp)
        self.addCleanup(setattr, inst, "load_pack", TRUE_LOADER)
        self.addCleanup(setattr, inst, "PACK_PATH", PACK_PATH)
        import shutil
        self.addCleanup(shutil.rmtree, d, True)
        self.store, self.gate, self.views = build_kernel(
            os.path.join(d, "record.jsonl"), blobs=BlobStore(os.path.join(d, "blobs")))
        founded = [e for e in self.store.by_action("CREATE-OP")
                   if (e.get("payload") or {}).get("name") == op]
        self.landed = [dict(c).get("check")
                       for c in (dict(dict(founded[0]["payload"])["definition"]).get("checks") or [])]
        if checks is not None:
            self.assertEqual(self.landed, [c["check"] for c in checks],
                             "the pack amendment did not reach the FOUNDED RECORD, so every "
                             "row built on this world would be testing the shipped shape")
        return self

    def stand_up(self, handles=(H1,)):
        for e in (GIVER, TAKER, THIRD, STRANGER):
            self.gate.execute("CREATE-ACCOUNT", "owner",
                              {"account_id": e, "actor_class": "program"})
        self.gate.execute("REGISTER-CAPABILITY", "owner",
                          {"driver": DRIVER, "device_class": "block"})
        self.gate.execute("BIND-DEVICE", "owner", {"device": DEVICE, "driver": DRIVER})
        for h in handles:
            self.gate.execute("FILE-OPEN", "owner", {"path": h, "provenance": "test"})

    def hand(self, handle=H1, frm=GIVER, to=TAKER, device=DEVICE):
        return self.gate.execute(OP, "owner", {"handle": handle, "from_entity": frm,
                                               "to_entity": to, "device": device})

    def refusal_of(self, fn, *a, **kw):
        """Drive an act expected to refuse; return (cited rule, message). Fails loudly if the
        act was ADMITTED — a refusal row whose subject was never refused proves nothing."""
        before = len(self.store.by_action("op-refused"))
        try:
            fn(*a, **kw)
        except OpError as exc:
            self.assertEqual(len(self.store.by_action("op-refused")), before + 1,
                             "the act raised but recorded no refusal — a governed refusal is "
                             "a RECORDED rule-citing decision, not an exception")
            return self.store.by_action("op-refused")[-1].get("rule_cited"), str(exc)
        raise AssertionError("the act was ADMITTED where the law requires a refusal")

    def shipped_checks(self, op=OP):
        return copy.deepcopy(op_definition(copy.deepcopy(REAL), op)["checks"])

    def without_bound_field(self):
        return [c for c in self.shipped_checks() if c["check"] != opdefs.BOUND_FIELD]


# =====================================================================================
# A1 — THE MINIMALITY GATE, DISCHARGED AGAINST THE ARMS AND NOT AGAINST THE RULING
# =====================================================================================

class A1MinimalityGateCase(unittest.TestCase):
    """A1 — KIND: INSPECTED, over the engine's own source.

    THIS IS A ROW AND NOT A FOOTNOTE BECAUSE THE MINT WAS RULED ON A FORMULATION THE ARMS
    REFUTE (`:1968`). `:1920` said *a current parameter against a prior record field has no
    kind in the fifteen*; `require_prior`'s arm compares a record's field to a caller
    parameter in its own second line and always has. THE WALL STANDS AND ITS FORMULATION DID
    NOT — so this gate is discharged against the CODE.
    """

    def arm_source(self, needle, stop):
        src = open(opdefs.__file__, encoding="utf-8").read().splitlines()
        first = next(i for i, l in enumerate(src) if re.search(needle, l))
        last = next(i for i in range(first + 1, len(src)) if re.search(stop, src[i]))
        return "\n".join(src[first:last])

    def test_a1_require_prior_compares_to_a_parameter_and_binds_no_record(self):
        """THE NEAREST KIND, AND IT STOPS AT SELECTION. Its arm is an EXISTENCE SCAN: `any(...)`
        over `store.by_action`. So "the giver holds THIS handle" and "the giver holds
        SOMETHING" are one question to it, which is exactly what R1 drives."""
        arm = self.arm_source(r'if c\["check"\] == "require_prior"', r'elif c\["check"\] == "sight"')
        self.assertIn("any(", arm,
                      "require_prior's arm is no longer an existence scan — A1's whole "
                      "premise, and therefore the minimality gate, must be re-derived")
        self.assertIn("store.by_action", arm)
        # IT DOES COMPARE TO A PARAMETER — the half `:1920` got wrong, pinned so the
        # correction cannot quietly rot back.
        self.assertIn('p_in.get(c["param"])', arm,
                      "require_prior no longer reads a caller parameter — then `:1920`'s "
                      "refuted wording would become true again and A1 must be re-argued")
        # AND IT NAMES NO KEY PARAMETER: there is nowhere to tell it WHICH record.
        self.assertNotIn("key_param", arm,
                         "require_prior's arm gained a record selector — if it can bind a "
                         "record, the sixteenth kind is not minimal and the mint is refused")

    def test_a1_sight_asks_about_the_actor_and_reads_no_record_field(self):
        """ITS SUBJECT IS THE ACTOR'S PERMISSIONS, answered by `can_read` against GRANT-READ.
        It names no field of any prior record and has nowhere to be told one."""
        arm = self.arm_source(r'elif c\["check"\] == "sight"', r'elif c\["check"\] == "ceiling"')
        self.assertIn("can_read(", arm)
        self.assertNotIn('c["field"]', arm)
        self.assertNotIn("key_param", arm)

    def test_a1_prior_value_binds_a_record_and_cannot_be_told_a_value_to_expect(self):
        """IT BINDS THE RECORD AND COMPARES TO NO PARAMETER. Its requirement vocabulary is
        established / unestablished — a PRESENCE test — and its own docstring states the
        exclusion as a design property rather than an omission."""
        fn = opdefs._prior_value_check
        src = open(opdefs.__file__, encoding="utf-8").read()
        body = src[src.index("def _prior_value_check"):src.index("def _bound_field_check")]
        self.assertIn("THE VALUE COMES FROM THE RECORD AND NEVER FROM A PARAMETER", fn.__doc__)
        self.assertEqual(opdefs.PRIOR_VALUE_REQUIREMENTS,
                         (opdefs.ESTABLISHED, opdefs.UNESTABLISHED),
                         "prior_value's requirement vocabulary moved — if it can now be told "
                         "a value to expect, the sixteenth kind is not minimal")
        # THE COMPARISON IS AGAINST A REQUIREMENT WORD, never against a second parameter.
        self.assertNotIn('params.get(c["value_param"])', body)

    def test_a1_the_new_kind_is_the_only_one_that_does_both(self):
        """THE GATE, STATED AS THE PROPERTY THAT SEPARATES: binding a record BY A PARAMETER and
        comparing a field of it TO ANOTHER PARAMETER. Read off the arm rather than asserted."""
        src = open(opdefs.__file__, encoding="utf-8").read()
        arm = src[src.index("def _bound_field_check"):src.index("def _interpreter")]
        self.assertIn('params.get(c["key_param"])', arm, "the new kind binds no record")
        self.assertIn('params.get(c["param"])', arm, "the new kind compares to no parameter")
        self.assertIn('max(matched, key=lambda e: e["seq"])', arm, "latest-wins was dropped")


# =====================================================================================
# A2 — THE KIND EXISTS, IS REFUSED-IF-UNKNOWN, AND IS DISPATCHED
# =====================================================================================

class A2KindMintedCase(WorldCase):

    def test_a2_the_vocabulary_carries_the_new_name(self):
        self.assertIn(opdefs.BOUND_FIELD, opdefs.OP_CHECKS)
        self.assertEqual(opdefs.BOUND_FIELD, "bound_field")

    def test_a2_an_unknown_kind_is_still_refused_with_the_full_vocabulary_listed(self):
        """THE MINT DID NOT OPEN THE DOOR. A near-miss spelling is refused at definition time,
        and the refusal LISTS the vocabulary — so an author who misspells learns the whole set
        rather than only that they were wrong."""
        raised = {}

        class Door:
            def refuse(self, actor, op, rule, message):
                raised["rule"], raised["message"] = rule, message
                raise OpError(rule, message)

        with self.assertRaises(OpError):
            opdefs.validate_definition_shape(
                Door(), "CREATE-OP", "owner", "X",
                {"law_cited": "CAP-IS-LAW", "params": {"a": "required"},
                 "checks": [{"check": "bound_fieldd", "cite": "CAP-IS-LAW"}]})
        self.assertEqual(raised["rule"], "AR-2")
        self.assertIn("bound_fieldd", raised["message"])
        for name in opdefs.OP_CHECKS:
            self.assertIn(name, raised["message"])

    def test_a2_the_new_arm_is_reached_by_the_interpreter(self):
        """DISPATCHED, not merely declared. Driven: the arm's own refusal message reaches a
        caller, which no amount of tuple membership would prove."""
        self.build().stand_up()
        self.hand(H1, GIVER, TAKER)
        rule, message = self.refusal_of(self.hand, H1, STRANGER, THIRD)
        self.assertEqual(rule, "FS-LAW-CUSTODY-TRANSFER")
        self.assertIn("holds", message)


# =====================================================================================
# A3 / A4 — ONE ROW IN TWO DIRECTIONS. NEITHER ALONE IS EVIDENCE.
# =====================================================================================

class GiverHoldsCase(WorldCase):
    """A3 and A4. DIRECTION, stated by the rows for themselves (`:1715`): the verdict moves
    from ACCEPTED (the giver IS the recorded holder) to REFUSED (it is not). The thing that
    moves between them is WHO GIVES, and nothing else."""

    def setUp(self):
        self.build().stand_up()
        self.hand(H1, GIVER, TAKER)          # the handle enters the chain; TAKER holds it

    def test_a3_a_giver_that_is_established_but_does_not_hold_is_refused(self):
        rule, message = self.refusal_of(self.hand, H1, STRANGER, THIRD)
        self.assertEqual(rule, "FS-LAW-CUSTODY-TRANSFER",
                         "a non-holding giver raised something other than a cited refusal")
        self.assertIn("holds", message)
        self.assertEqual(len(self.store.by_action(OP)), 1, "the refused act appended a record")

    def test_a3_the_refusal_is_not_the_establishment_check_wearing_a_new_message(self):
        """THE ROW THAT KEEPS A3 HONEST. `STRANGER` is a FULLY ESTABLISHED ENTITY, so C3's four
        establishment checks admit it; the refusal above is attributable to this kind alone.
        Without this the row would be green for a cause it does not name."""
        established = {(e.get("payload") or {}).get("account_id")
                       for e in self.store.by_action("CREATE-ACCOUNT")}
        self.assertIn(STRANGER, established,
                      "the A3 subject is not an established entity, so its refusal could be "
                      "C3's establishment check and this row proves nothing about custody")

    def test_a4_the_recorded_holder_is_admitted_and_the_holding_moves(self):
        """A CHECK THAT REFUSES EVERYTHING IS NOT A CHECK."""
        before = len(self.store.by_action(OP))
        self.hand(H1, TAKER, THIRD)
        after = self.store.by_action(OP)
        self.assertEqual(len(after) - before, 1, "the lawful handover appended nothing")
        self.assertEqual(after[-1]["payload"]["to_entity"], THIRD)
        self.assertEqual(after[-1]["rule_cited"], "FS-LAW-CUSTODY-TRANSFER")

    def test_a4_latest_wins_so_the_previous_holder_can_no_longer_give(self):
        """THE AMENDING-DECLARATION SHAPE, ASSERTED. EP-30-E1 (`:888`) established that a
        current holding is expressible under latest-seq-wins BECAUSE the state is written as
        an amending declaration of the same action. A row reading the EARLIEST match would
        admit the act below, which is what makes this the load-bearing direction."""
        self.hand(H1, TAKER, THIRD)                       # THIRD holds it now
        rule, _ = self.refusal_of(self.hand, H1, TAKER, GIVER)   # TAKER is the OLD holder
        self.assertEqual(rule, "FS-LAW-CUSTODY-TRANSFER")


# =====================================================================================
# A5 — GRANTER-HOLDS IS EXPRESSIBLE, AND THIS ROW LANDS NOTHING
# =====================================================================================

class A5GranterHoldsExpressibleCase(WorldCase):
    """A5 — the kind REACHES the second debt WITHOUT SPENDING IT. Driven against a SCRATCH
    definition minted through the ordinary door, never against the shipped `SHM-GRANT`, whose
    declaration is this plan's MUST-NOT-TOUCH and EP-30-C4's row."""

    DECL = {"check": "bound_field", "action": "MEM-GRANT", "field": "region",
            "key_param": "region", "value_field": "holder", "param": "granter",
            "cite": "COMM-LAW-SHARE-GRANT",
            "message": "the party granting shared access to this region is not the party "
                       "that holds it"}

    def setUp(self):
        self.build()
        self.gate.execute("CREATE-OP", "SYSTEM", {
            "kind": "op_definition", "rule_id": "op:SCRATCH-GRANTER-HOLDS", "polarity": "+",
            "name": "SCRATCH-GRANTER-HOLDS",
            "definition": {"description": "A5 scratch — NOT the shipped SHM-GRANT",
                           "params": {"region": "required", "granter": "required"},
                           # region = a shm region id ("shm:alices"), STRUCTURAL matching the
                           # shipped census (MEM-GRANT/MEM-EVICT/MEM-PROTECT/SHM-GRANT).
                           # granter = an actor id ("alice"), read inline by the bound_field
                           # check — a structural identifier, not a custody-conserved body.
                           "structural_params": ["region", "granter"],
                           "law_cited": "COMM-LAW-SHARE-GRANT", "object_param": "region",
                           "payload_from": ["region", "granter"], "checks": [self.DECL]},
            "tier": "owner", "text": "A5 scratch"})
        for a in ("alice", "mallory"):
            self.gate.execute("CREATE-ACCOUNT", "SYSTEM",
                              {"account_id": a, "actor_class": "program"})
        self.gate.execute("MEM-GRANT", "alice", {"region": "shm:alices", "size": 4096})

    def grant(self, granter, region="shm:alices"):
        return self.gate.execute("SCRATCH-GRANTER-HOLDS", "SYSTEM",
                                 {"region": region, "granter": granter})

    def test_a5_the_declaration_is_well_formed_and_dispatches(self):
        """WELL-FORMED IS PROVED BY THE DOOR ADMITTING IT, and dispatched by the holder's grant
        landing — a declaration the engine ignored would also 'pass' the door."""
        r = self.grant("alice")
        self.assertEqual(r["action"], "SCRATCH-GRANTER-HOLDS")

    def test_a5_the_non_holder_is_refused(self):
        rule, message = self.refusal_of(self.grant, "mallory")
        self.assertEqual(rule, "COMM-LAW-SHARE-GRANT")
        self.assertIn("holds", message)

    def test_a5_the_shipped_shm_grant_declares_no_checks_and_this_unit_did_not_move_it(self):
        """THE ROW THAT PROVES THIS UNIT LANDED NOTHING ON THE SECOND DEBTOR. Two units wiring
        one op is the double-landing the seam exists to prevent, so the absence is ASSERTED
        rather than left to a diff nobody re-reads.

        [DOCUMENTED FLIP — EP-30-C4R, 2026-08-26, §A57 cause-mapped repair, board :2128.
        CAUSE: this row asserted an EMPTY check list as a PROXY for THIS unit's restraint, and
        EP-30-C4 lawfully landed `require_prior` on the shipped op — the row THIS PLAN'S OWN §3
        A5 assigns to C4 in writing ("`SHM-GRANT`'s SHIPPED DECLARATION IS NOT THIS UNIT'S TO
        EDIT — it is EP-30-C4's row"). THE PROXY BECAME FALSE; THE CLAIM DID NOT.
        ASSERTED: this unit's claim DIRECTLY — that no check of THIS UNIT'S OWN KIND,
        `bound_field` granter-holds, stands on the shipped op, and that every check that IS
        there is one a named unit is accountable for.
        SUPERSEDED: the empty-list proxy.
        REMAINS TRUE, AND STRICTER: the old form redded identically whether this unit
        double-landed or C4 did its own released work — IT COULD NOT TELL THEM APART. This one
        can, and it still reds the moment a granter-holds check of this kind appears.
        GIVEN UP, and named rather than left to be noticed: the ability to detect ANY change to
        the op by ANY unit. That was never this unit's claim and it was C4's row to make.]"""
        checks = op_definition(REAL, "SHM-GRANT")["checks"]
        self.assertNotIn("bound_field", [c["check"] for c in checks],
                         "SHM-GRANT gained a granter-holds check of THIS UNIT's kind — that is "
                         "the double-landing this row exists to prevent")
        # Every check on SHM-GRANT is accounted for by a NAMED unit: require_prior is EP-30-C4's,
        # live_present is EP-MAINT-OUTSIDE-4 R10's (a region-LIVENESS check over MEM-GRANT/MEM-EVICT,
        # NOT this unit's granter-holds kind — the assertNotIn above still holds). A check named by no
        # unit still reds here (the guard's teeth), and this unit's own bound_field never lands.
        accounted = {"require_prior", "live_present"}
        for c in checks:
            self.assertIn(c["check"], accounted,
                          "SHM-GRANT gained a check that no named unit accounts for (EP-30-C4's "
                          "require_prior, EP-MAINT-OUTSIDE-4 R10's live_present) — name its unit "
                          "before it lands")


# =====================================================================================
# A6 — THE VOCABULARY CLAIM. EVERY DECLARED KIND IS ACCOUNTED FOR.
# =====================================================================================

#: THE ONE MEMBER UNDER A LIVE RAISE, NAMED HERE RATHER THAN FILTERED SILENTLY.
#:
#: `sight` HAS ZERO USERS and A6's sweep computes RETIREMENT for it — but this unit did NOT
#: retire it, and the reason is the plan's OWN stop 7: *a candidate user that is arguable
#: rather than plain is a raise, not a judgement call; retirement removes an implemented arm
#: and is not undone cheaply.* FIVE shipped ops declare `target_param`, which is sight's own
#: input (COMMS-SEND, SHM-GRANT, FILE-LINK, FILE-SYMLINK, FILE-RENAME); none ASKS a
#: read-permission question, and that gap between "could carry it" and "asks it" is exactly
#: the arguable case stop 7 reserves to the mentor.
#:
#: THE EXCEPTION IS A NAMED SINGLETON AND NOT A PREDICATE, deliberately. A predicate — "skip
#: kinds with no users" — would swallow the next unowned kind silently, which is the failure
#: this claim exists to prevent. R4 plants exactly that kind and this row still reds on it.
SIGHT_RAISED_PENDING_MENTOR_RULING = ("sight",)


def kinds_with_users(pack):
    """Which declared kinds any shipped op actually declares. COMPUTED from the pack, never
    listed here — a literal list would stop reporting the day a kind lost its last user."""
    used = set()
    for step in pack["steps"]:
        for r in step["records"]:
            if r.get("action") == "CREATE-OP":
                for c in (r["payload"]["definition"].get("checks") or []):
                    used.add(c.get("check"))
    return used


#: THE PLAN LIST IS THE ONLY HOME OF SCHEDULE DATA. EP-30-C4's A6 takes its schedule from this
#: file's plan list and from nowhere else (`:1970`), and the plan list's own closing row says the
#: schedule data any rider row reads takes its content from that list and nowhere else. A rider
#: whose data is RESTATED in the file that checks it is a claim checking its own copy (`:1793`) —
#: so no kind name reaches the branch below as a literal. The path is data; the CONTENT is not.
PLAN_LIST = os.path.join(ROOT, "design", "36-CAMPAIGN-3-DEPTH.md")

#: The plan list is one section of that document, bounded by its own heading and the next one.
#: Anchored on the HEADING TEXT rather than on any coordinate: a line number is a ROLE and a
#: name is an IDENTITY, and this unit's sibling moved seven live coordinates by doing its job.
_PLAN_LIST_OPENS = re.compile(r"(?m)^## 6\. ")
_PLAN_LIST_CLOSES = re.compile(r"(?m)^## 7\. ")

#: A schedule row names the kind it schedules BY ITS PERMANENT NAME, in backticks. Both of the
#: rows that carry the quantifier say so in those words, and they say so because the `:2282`
#: repair replaced a DESCRIPTION ("the kind K2 mints") with the name: a description resolves only
#: while someone remembers what it described. THE BACKTICK IS THE WHOLE DISCRIMINATOR — §4's R3
#: drives the description form and requires that it NOT resolve.
_PERMANENT_NAME = re.compile(r"`([a-z][a-z0-9_]*)`")

#: MAINT-3. A SCHEDULE ROW IS A RECORD, AND RECORD MEMBERSHIP IS THE WHOLE DISCRIMINATOR —
#: NEVER SENTENCE SHAPE. The plan list carries pipe-delimited records wrapped across many
#: lines, and it carries ordinary prose at the SAME indent, immediately adjacent, with no
#: blank line between them. `every_member`'s backtick at design/36:686 falls mid-sentence
#: inside a record; `fingerprint`'s at :367 falls mid-sentence inside a markdown bullet. THEY
#: READ EQUALLY LIKE PROSE. Nothing about the sentence separates them and a predicate that
#: tried to would narrow past its target — so the question asked below is only ever "is this
#: backtick inside a record", never "does this look like a row".
#:
#: A record OPENS with its identifier followed by a pipe, and CLOSES on its terminating STATUS
#: field — the tuple's last field, which may sit on a line of its own carrying no pipe at all
#: (design/36:881 is the bare word PENDING). The status is matched STRUCTURALLY, as a single
#: capitalised token optionally trailed by a board citation, rather than against a list of
#: status words: a vocabulary would be narrowed to today's data and would stop seeing a row
#: the day someone wrote a status nobody had written before.
_ROW_OPENS = re.compile(r"^\s{0,4}[A-Za-z][A-Za-z0-9_-]*\s+\|")
_ROW_CLOSES = re.compile(r"(?:\||^)\s*[A-Z][A-Z-]*(?:\s+:\d+)?\s*$")


def schedule_rows(span):
    """The plan list's schedule records, each as (first_line, last_line, lines).

    THE TERMINATOR SEARCH IS BOUNDED BY THE NEXT OPENER, and that bound is not decoration —
    it was put here by a near-miss control that found the defect regrowing through a second
    door. Unbounded, a line that merely LOOKS like an opener (an identifier and a pipe) with
    no terminator after it swallows every line of prose between itself and the next genuine
    record's status field. Driven at this unit's build: one such line planted above
    design/36:367 put `fingerprint` back into the answer with the row-shaped predicate
    otherwise intact. The repair would have passed every other row in this unit while the
    hole it exists to close was still open two hundred lines further up.

    HONEST CAP, and it fails in the safe direction. A record whose continuation line begins
    with a bare capitalised token and a pipe, carrying no status on that line, is read as a
    new opener and its record is not seen. No row in design/36 is written that way — all
    fourteen parse, including the two whose terminator is split across lines (:714/:715 and
    :880/:881). Were such a row ever written, the kind it schedules would stop resolving and
    A6 would RED on it, loudly. The unbounded alternative fails the other way: a mention
    resolves and every claim above it stays green. A guard that goes silent is worse than one
    that shouts, so the bound stays and its cost is stated rather than discovered."""
    rows, lines, i = [], span.splitlines(), 0
    while i < len(lines):
        if _ROW_OPENS.search(lines[i]):
            nxt = next((k for k in range(i + 1, len(lines))
                        if _ROW_OPENS.search(lines[k])), len(lines) - 1)
            close = next((k for k in range(i, nxt + 1)
                          if _ROW_CLOSES.search(lines[k])), None)
            if close is not None:
                rows.append((i, close, lines[i:close + 1]))
                i = close + 1
                continue
        i += 1
    return rows


def kinds_named_anywhere_in_the_plan_list(path=PLAN_LIST):
    """THE PRE-MAINT-3 BEHAVIOUR, RETAINED ON PURPOSE AS A CONTROL AND NOT AS A LEFTOVER.

    This is what the scheduled branch used to be: every backticked name anywhere in the span,
    row or prose alike. It is kept because MAINT-3's A3 compares the branch's answer BEFORE
    and AFTER the narrowing BY SET DIFFERENCE OVER MEMBERS, and a comparison whose earlier
    half is a number typed into a file has stopped being a comparison. Keeping the old
    predicate executable means the difference is recomputed from the document every time the
    suite runs, so the row keeps answering after the schedule moves.

    NOTHING IN THE SHIPPED CLAIM CALLS THIS. A6 asks `kinds_with_scheduled_users`."""
    return set(_PERMANENT_NAME.findall(plan_list_text(path)))


def plan_list_text(path=PLAN_LIST):
    """The plan list's own text, read from disk AT CALL TIME. Never cached: a branch that
    answers from a value captured at import has stopped reading the source it claims to read.

    REFUSES rather than guesses. If either boundary is absent the section has been renamed or
    removed, and BOTH silent answers are wrong in the direction that hides it — a whole-file
    read over-resolves every kind mentioned anywhere, an empty read resolves none and reds on
    kinds that ARE scheduled. §4's R2 exists because a predicate that answers the same on an
    emptied source is reading something else; a predicate that answers ANYTHING on a source it
    could not find is the same defect one step earlier."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    opens, closes = _PLAN_LIST_OPENS.search(text), _PLAN_LIST_CLOSES.search(text)
    if opens is None or closes is None or closes.start() <= opens.start():
        raise RuntimeError(
            "the plan list's section boundaries are not readable in %s — this branch reads a "
            "SECTION of that document and will not fall back to the whole file or to nothing, "
            "because both answers look like a working predicate" % path)
    return text[opens.start():closes.start()]


def kinds_with_scheduled_users(path=PLAN_LIST):
    """THE SCHEDULED-USER BRANCH: the set of kinds named in the plan list's schedule rows.

    A PREDICATE OVER DECLARED DATA, not a second singleton and not a literal list. The claim A6
    makes (`:1965`) is that every declared kind has a user, A NAMED SCHEDULED USER, or a recorded
    retirement — and until this function existed the third of those four branches had no
    implementation at all, so a kind whose only users are scheduled read as unowned.

    IT DOES NOT FILTER BY `opdefs.OP_CHECKS`, and that is §4's R4: a branch that only ever
    returns names the engine already declares is reading the ENGINE, not the schedule, and would
    resolve exactly the kinds that need no resolving. What it returns is what the plan list
    NAMES; A6 is what asks whether a declared kind is among them. A name here that is not a check
    kind is inert — nothing consults this set except by asking after a kind it already holds.

    IT IS NOT A "SKIP KINDS WITH NO USERS" PREDICATE. The singleton's own comment refuses that
    shape because it would swallow the next unowned kind silently. This one resolves a kind only
    where the schedule EARNS it by naming it, and §4's R1 is the row that proves the difference:
    a declared kind with no pack user, no plan-list entry and no raise still reds.

    MAINT-3 NARROWED THIS TO SCHEDULE ROWS. It used to read the whole span, so a kind was
    resolved as SCHEDULED by a sentence that merely MENTIONED it — design/36:367 describes
    what EP-23 already shipped and scheduled nothing, and `fingerprint` resolved off it. The
    hole that mattered was not the wrong answer it gave (nothing consulted it for that kind)
    but the RED IT COULD NO LONGER GIVE: the day `fingerprint` lost its last pack user, A6
    would have resolved it off that sentence and stayed green, and the claim would have
    stopped being able to fail on the one case it exists for."""
    names = set()
    for _, _, body in schedule_rows(plan_list_text(path)):
        names |= set(_PERMANENT_NAME.findall("\n".join(body)))
    return names


class A6VocabularyClaimCase(unittest.TestCase):
    """A6's EXTENDED CLAIM (`:1965`): every declared kind has a user, a named scheduled user,
    or a recorded retirement. KIND: ABSENCE, and it carries its control."""

    #: The schedule source, as an ATTRIBUTE so §4's red worlds can point this claim at a COPY
    #: they have mutated. The rows below drive the real one; nothing here writes to it.
    PLAN_LIST = PLAN_LIST

    def test_a6_every_declared_kind_has_a_user_or_is_a_named_raise(self):
        used = kinds_with_users(REAL)
        scheduled = kinds_with_scheduled_users(self.PLAN_LIST)
        unowned = [k for k in opdefs.OP_CHECKS
                   if k not in used and k not in scheduled
                   and k not in SIGHT_RAISED_PENDING_MENTOR_RULING]
        self.assertEqual(unowned, [],
                         "these declared check kinds have no user, no named scheduled user "
                         "and no recorded retirement: %s — a vocabulary member nothing uses "
                         "is a claim that cannot fail" % unowned)

    def test_a6_the_control_the_SCHEDULED_BRANCH_is_load_bearing(self):
        """THE OTHER SWEEP NEEDS THE SAME CONTROL, and this one is stricter than 'it found
        something'. A6 greens above by NOT listing a kind, so a scheduled branch that returned
        the whole world would green it by resolving everything, and one that returned nothing
        would be invisible here for as long as the pack happened to cover every kind.

        WHAT THIS ROW ASSERTS IS THAT THE BRANCH IS DOING WORK: at least one declared kind is
        resolved BY THE SCHEDULE AND BY NOTHING ELSE — no shipped op declares it and it is not
        the named singleton. That is the whole reason this unit exists, and the day the pack
        grows a user for it this row reds and the branch's claim on it must be re-read."""
        scheduled = kinds_with_scheduled_users(self.PLAN_LIST)
        self.assertTrue(scheduled,
                        "the scheduled branch returned nothing at all — a branch with no "
                        "answers cannot be told apart from a branch nobody calls")
        used = kinds_with_users(REAL)
        only_scheduled = [k for k in opdefs.OP_CHECKS
                          if k in scheduled and k not in used
                          and k not in SIGHT_RAISED_PENDING_MENTOR_RULING]
        self.assertTrue(only_scheduled,
                        "no declared kind is resolved by the schedule alone, so A6 would green "
                        "identically with this branch deleted — the branch has stopped being "
                        "the thing that answers and nothing above would notice")

    def test_a6_the_control_the_sweep_can_find_things(self):
        """A ZERO PROVES NOTHING WITHOUT A CONTROL. If the sweep were mis-built it would find
        no users at all and the row above would pass by finding nothing to complain about."""
        used = kinds_with_users(REAL)
        self.assertIn("require_prior", used)
        self.assertIn(opdefs.BOUND_FIELD, used,
                      "this unit's own kind is not declared by any op — then the mint landed "
                      "an implementation with no user, which is sight's condition exactly")
        self.assertGreaterEqual(len(used), 10)

    def test_a6_the_named_exception_is_still_genuinely_unowned(self):
        """THE EXCEPTION MUST KEEP EARNING ITS PLACE. The day an op declares `sight`, this row
        reds and the raise is discharged by the world rather than by anyone remembering."""
        used = kinds_with_users(REAL)
        for name in SIGHT_RAISED_PENDING_MENTOR_RULING:
            self.assertNotIn(name, used,
                             "%r now HAS a user, so its raise is stale — remove it from "
                             "SIGHT_RAISED_PENDING_MENTOR_RULING" % name)
            self.assertIn(name, opdefs.OP_CHECKS,
                          "%r is no longer declared, so the exception is stale — remove it "
                          "from SIGHT_RAISED_PENDING_MENTOR_RULING" % name)

    def test_a6_sight_is_law_keeps_a_live_home_outside_the_check_vocabulary(self):
        """THE FACT THAT MAKES THE RAISE DECIDABLE, PINNED SO IT CANNOT ROT. Retiring the check
        kind would follow `attenuation`'s precedent ONLY IF the law keeps another home —
        attenuation's leash MOVED to the gate chokepoint, which is why *one law, one home* was
        a retirement and not a deletion. Sight's other home is `protection.assert_can_read`,
        called from CONSUME. If this row ever reds, the raise's answer changes."""
        from kernel import protection
        self.assertTrue(hasattr(protection, "can_read"))
        src = open(protection.__file__, encoding="utf-8").read()
        self.assertIn("assert_can_read", src)
        self.assertIn("SIGHT_IS_LAW", src)
        self.assertIn('protection.assert_can_read(actor, params["target"], "CONSUME")', src,
                      "CONSUME no longer enforces sight, so the check kind may be the law's "
                      "only remaining home and retirement would DELETE it rather than move it")


# =====================================================================================
# §4 RED WORLDS
# =====================================================================================

class R1ExistenceIsNotSelectionCase(WorldCase):
    """R1 — EXISTENCE IS NOT SELECTION, AND THIS ROW IS THE WHOLE MINT'S JUSTIFICATION.

    DIRECTION: the verdict moves from ACCEPTED (the `require_prior` spelling) to REFUSED (the
    new kind), over ONE world and ONE act. THE PLANT IS THE SPELLING.

    IF THIS ROW CANNOT SEPARATE THE TWO, THE SIXTEENTH KIND IS NOT MINIMAL AND THE MINT MUST
    BE REFUSED — INCLUDING BY ITS OWN AUTHOR (plan stop 2)."""

    def world_where_the_giver_holds_a_different_handle(self):
        self.stand_up(handles=(H1, H2))
        self.hand(H1, STRANGER, GIVER)        # GIVER comes to hold H1
        self.hand(H2, STRANGER, THIRD)        # THIRD holds H2

    def test_r1_the_require_prior_spelling_admits_a_giver_who_holds_a_different_handle(self):
        self.build(self.without_bound_field())
        self.world_where_the_giver_holds_a_different_handle()
        r = self.hand(H2, GIVER, TAKER)
        self.assertEqual(r["action"], OP,
                         "the establishment spelling refused — then R1's differential has no "
                         "ACCEPT half and the minimality gate is not discharged")

    def test_r1_the_bound_field_spelling_refuses_the_same_act(self):
        self.build()
        self.world_where_the_giver_holds_a_different_handle()
        rule, message = self.refusal_of(self.hand, H2, GIVER, TAKER)
        self.assertEqual(rule, "FS-LAW-CUSTODY-TRANSFER")
        self.assertIn("holds", message)

    def test_r1_the_nearer_require_prior_spelling_is_vacuous_from_genesis(self):
        """THE SPELLING A READER WOULD REACH FOR NEXT, DRIVEN so nobody thinks it was untried.
        `require_prior` over the TRANSFER stream is the closest existence scan to giver-holds
        and IT CANNOT BE USED AT ALL: the first transfer of any handle would need a PRIOR
        transfer naming its giver as a recipient, and at genesis there are none. IT IS NOT A
        STRICTER SPELLING; IT IS A VACUOUS ONE."""
        plant = {"check": "require_prior", "action": OP, "field": "to_entity",
                 "param": "from_entity", "cite": "FS-LAW-CUSTODY-TRANSFER",
                 "message": "R1 plant: require_prior over the transfer stream"}
        self.build(self.without_bound_field() + [plant])
        self.stand_up(handles=(H1,))
        rule, _ = self.refusal_of(self.hand, H1, GIVER, TAKER)
        self.assertEqual(rule, "FS-LAW-CUSTODY-TRANSFER")


class R2TheCheckCanFailAndPassCase(WorldCase):
    """R2 — DIRECTION: REFUSED with the plant present, ACCEPTED with it removed, REFUSED again
    when restored. THE PLANT IS THE CHECK ROW ITSELF."""

    def a3_act(self):
        self.stand_up(handles=(H1,))
        self.hand(H1, GIVER, TAKER)

    def test_r2_removing_the_check_turns_the_refusal_into_an_acceptance(self):
        self.build(self.without_bound_field())
        self.a3_act()
        r = self.hand(H1, STRANGER, THIRD)
        self.assertEqual(r["action"], OP)

    def test_r2_restoring_the_check_brings_the_refusal_back(self):
        self.build()
        self.a3_act()
        rule, _ = self.refusal_of(self.hand, H1, STRANGER, THIRD)
        self.assertEqual(rule, "FS-LAW-CUSTODY-TRANSFER")


class R3TheLiteralReadingOfC3R1Case(WorldCase):
    """R3 — C3's R1 IN ITS LITERAL READING, and the row states DISCHARGE OR NARROWING in its
    own words because a narrowing described as a discharge is the defect this arc has filed
    five times.

    IT IS A NARROWING. Two reasons, both driven below:

      1. THE FIRST HOP IS NOT REACHED. The shipped declaration carries `when_unbound: permit`,
         so a handle no transfer names may be handed on by anyone established. That is not a
         convenience: DRIVEN with both controls, the strict form reds ELEVEN shipped rows and
         makes the op unusable, because no handle could ever make a first hop and the chain
         would stay permanently empty.
      2. AND IT CANNOT BE CLOSED BY THIS KIND. Over the record plane as it stands, WHO HOLDS
         THIS HANDLE is a TWO-SOURCE fold — the transfer chain's latest `to_entity` once a
         handle is in it, and THE OPENER before that. `FILE-OPEN`'s `payload_from` is
         ["path", "inode", "flags"]: IT RECORDS NO OPENER AT ALL. One `bound_field` row binds
         one action's records, so it expresses one source and not both.

    WHAT IS DISCHARGED: for a handle IN the chain, a transfer by anyone other than its
    recorded holder is refused, cited. That is strictly more than C3's reading reached."""

    def test_r3_an_established_non_holder_is_refused_which_c3s_reading_admitted(self):
        self.build()
        self.stand_up(handles=(H1,))
        self.hand(H1, GIVER, TAKER)
        rule, _ = self.refusal_of(self.hand, H1, STRANGER, THIRD)
        self.assertEqual(rule, "FS-LAW-CUSTODY-TRANSFER")

    def test_r3_the_narrowing_is_real_the_first_hop_is_admitted_by_anyone(self):
        """THE NARROWING, ASSERTED RATHER THAN CONFESSED IN PROSE. This row is EXPECTED to pass
        an act the full property would refuse, and it exists so the gap is visible to a reader
        of the suite and not only to a reader of the close."""
        self.build()
        self.stand_up(handles=(H2,))
        r = self.hand(H2, STRANGER, THIRD)      # STRANGER never opened or held H2
        self.assertEqual(r["action"], OP,
                         "the first hop is now refused — the narrowing this row documents has "
                         "closed, and R3's statement in the close is stale")

    def test_r3_file_open_records_no_opener_which_is_why_the_first_hop_is_unaskable(self):
        """THE CAUSE OF THE NARROWING, PINNED AT ITS SOURCE. The day FILE-OPEN records its
        opener, the first hop becomes expressible and this row reds — which is the correct
        moment for someone to revisit R3's statement."""
        d = op_definition(REAL, "FILE-OPEN")
        self.assertEqual(d["payload_from"], ["path", "inode", "flags"],
                         "FILE-OPEN's recorded fields moved — if it now records an opener, "
                         "the first hop of custody is expressible and R3's narrowing can be "
                         "closed by a successor unit")
        self.assertIsNone(d.get("stamp_actor"),
                          "FILE-OPEN now stamps an actor field — see above")


class R4TheVocabularyClaimCanFailCase(unittest.TestCase):
    """R4 — A6 MUST BE SHOWN REFUSING SOMETHING OR IT IS A CLAIM THAT CANNOT FAIL.

    DIRECTION: A6's claim moves from GREEN (plant removed) to RED, NAMING THE PLANT (plant
    present). The plant is a sixteenth-and-a-half name in the vocabulary with no user, no
    schedule and no retirement."""

    PLANT = "a_kind_nobody_uses"

    def test_r4_a_planted_unowned_kind_reds_a6_and_is_named_in_the_failure(self):
        real = opdefs.OP_CHECKS
        try:
            opdefs.OP_CHECKS = real + (self.PLANT,)
            case = A6VocabularyClaimCase("test_a6_every_declared_kind_has_a_user_or_is_a_named_raise")
            with self.assertRaises(AssertionError) as caught:
                case.test_a6_every_declared_kind_has_a_user_or_is_a_named_raise()
            self.assertIn(self.PLANT, str(caught.exception),
                          "A6 red without naming the kind that caused it — a claim that "
                          "cannot say WHAT is wrong sends the reader hunting")
        finally:
            opdefs.OP_CHECKS = real

    def test_r4_the_control_with_the_plant_removed_a6_greens(self):
        """THE OTHER HALF: without the plant the same row passes, so the red above is
        attributable to the plant and not to a claim that reds on everything."""
        case = A6VocabularyClaimCase("test_a6_every_declared_kind_has_a_user_or_is_a_named_raise")
        case.test_a6_every_declared_kind_has_a_user_or_is_a_named_raise()

    def test_r4_the_named_exception_does_not_swallow_the_plant(self):
        """THE SHAPE OF THE EXCEPTION IS ITSELF THE RISK. A predicate-shaped exception ('skip
        kinds with no users') would swallow the plant and A6 would never red again. This row
        proves the exception is a NAMED SINGLETON."""
        self.assertNotIn(self.PLANT, SIGHT_RAISED_PENDING_MENTOR_RULING)
        self.assertEqual(len(SIGHT_RAISED_PENDING_MENTOR_RULING), 1)


# =====================================================================================
# EP-30-K2R §4 — THE SCHEDULED BRANCH'S OWN RED WORLDS
#
# The rows above green because a branch resolves a kind. These rows drive the branch against
# sources it must answer DIFFERENTLY on, because a predicate that returns the same answer
# whatever its source is reading something other than its source. Each mutation is made on a
# COPY; design/36 is this unit's MUST-NOT-TOUCH and a check that edits its own data source is
# the defect being repaired (`:1793`), not a test of it.
# =====================================================================================

class TheScheduledBranchIsAPredicateOverDeclaredDataCase(unittest.TestCase):
    """EP-30-K2R's R2, R3 and R4 — the three ways this branch could be a hardcode wearing a
    function's name, each driven rather than promised.

    EVERY KIND NAME IN THIS CLASS IS COMPUTED FROM THE PLAN LIST, never typed. That is the
    unit's A5 and it is also what keeps these rows alive: a row that named its subject would
    have to be re-typed the day the schedule moved, and until someone did it would be asserting
    about a kind the schedule no longer carries. THE ONE LITERAL BELOW IS A FIXTURE — a name
    planted INTO a copy, which is control data and never schedule data."""

    #: FIXTURE, NOT SCHEDULE DATA. A name this estate does not declare and the plan list does
    #: not carry, planted into a COPY so R4 can ask whether the branch resolves by membership
    #: or by identity. Named as a fixture here because A5 requires the exemption to be stated.
    PLANTED_SECOND = "a_second_scheduled_kind"

    #: FIXTURE, NOT SCHEDULE DATA. R1's plant: a declared kind that no branch resolves. Named
    #: as a fixture here for the same reason, and its absence from the schedule is asserted in
    #: the row rather than assumed by it.
    PLANTED_UNOWNED = "a_kind_no_branch_resolves"

    def setUp(self):
        with open(PLAN_LIST, encoding="utf-8") as fh:
            self.document = fh.read()
        self.real = plan_list_text()
        self.resolving = self.kinds_the_branch_alone_resolves()

    def kinds_the_branch_alone_resolves(self, path=PLAN_LIST):
        """The kinds this branch is CARRYING — declared, named in the plan list, and declared by
        no shipped op. These are the ones whose resolution changes when the schedule moves, so
        they are the subjects every row below mutates. Computed, so the rows follow the schedule
        instead of pinning a copy of it."""
        scheduled = kinds_with_scheduled_users(path)
        used = kinds_with_users(REAL)
        return [k for k in opdefs.OP_CHECKS
                if k in scheduled and k not in used
                and k not in SIGHT_RAISED_PENDING_MENTOR_RULING]

    def copy_of_the_plan_list(self, mutated_section):
        """A mutated plan list on disk, so the branch reads it exactly as it reads the real one —
        through its own file-opening path and not through an argument that bypasses it.

        THE WHOLE DOCUMENT IS COPIED AND ONLY ITS PLAN LIST REPLACED, for a reason this unit's
        builder met by getting it wrong first: the branch finds its section by that document's
        OWN headings, so a file containing the bare section has no closing boundary and the
        branch REFUSES it. That refusal is the guard working — but it would arrive in every row
        below, from the fixture rather than from the mutation, and a red that comes from the
        fixture proves nothing about the subject. Mutating in place keeps every row's red
        attributable to the one thing that row changed."""
        self.assertIn(self.real, self.document,
                      "the plan list is not a contiguous slice of its own document, so this "
                      "fixture cannot replace it without changing something it did not mean to")
        fd, path = tempfile.mkstemp(suffix=".md", prefix="govos_k2r_plan_list_")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.document.replace(self.real, mutated_section, 1))
        self.addCleanup(os.remove, path)
        return path

    def a6_against(self, path):
        """A6's own claim, pointed at a copied schedule. The row is constructed and called the
        way R4's rows already drive it, so what reds here is the shipped claim and not a
        paraphrase of it living in this class."""
        case = A6VocabularyClaimCase("test_a6_every_declared_kind_has_a_user_or_is_a_named_raise")
        case.PLAN_LIST = path
        return case.test_a6_every_declared_kind_has_a_user_or_is_a_named_raise

    def test_the_branch_is_carrying_at_least_one_kind_or_these_rows_test_nothing(self):
        """THE GUARD THAT MAKES THE THREE ROWS BELOW READABLE. Every one of them mutates the
        kinds the branch alone resolves; if that set were empty each would mutate nothing,
        observe no change, and pass. A control that cannot fail is this estate's signature
        defect and it is named here rather than left to be discovered."""
        self.assertTrue(self.resolving,
                        "no kind is resolved by the schedule alone, so R2, R3 and R4 would "
                        "each be driving a mutation with no subject")

    def test_r1_THE_PLANT_MUST_STILL_RED_and_the_schedule_is_why_it_does(self):
        """R1 — THE LOAD-BEARING ROW. A6 WITHOUT IT IS INDISTINGUISHABLE FROM DELETING THE CLAIM.

        A declared kind with no pack user, NO PLAN-LIST ENTRY and no raise must still red, and
        must still be NAMED in the failure. The middle clause is the one this unit put weight
        on: before the scheduled branch existed the plan list was not consulted at all, so the
        plant's absence from it was not load-bearing and nothing was watching it. It is now.

        THE ROW ASSERTS THAT ABSENCE FIRST, so a future red here says WHICH condition stopped
        holding instead of only that a red did not arrive. This is the branch's own R1: the
        predicate is over DECLARED DATA and not over absence, and the difference between those
        two stops being a sentence exactly here."""
        self.assertNotIn(self.PLANTED_UNOWNED, kinds_with_scheduled_users(),
                         "the plant is named in the plan list, so it now HAS a scheduled user "
                         "and this row can no longer show A6 refusing anything — rename the "
                         "fixture; do not weaken the branch")
        self.assertNotIn(self.PLANTED_UNOWNED, kinds_with_users(REAL),
                         "the plant is declared by a shipped op, so it has a pack user")
        self.assertNotIn(self.PLANTED_UNOWNED, SIGHT_RAISED_PENDING_MENTOR_RULING)

        real = opdefs.OP_CHECKS
        try:
            opdefs.OP_CHECKS = real + (self.PLANTED_UNOWNED,)
            with self.assertRaises(AssertionError) as caught:
                self.a6_against(PLAN_LIST)()
            self.assertIn(self.PLANTED_UNOWNED, str(caught.exception),
                          "A6 redded without naming the kind that caused it — a claim that "
                          "cannot say WHAT is wrong sends the reader hunting")
        finally:
            opdefs.OP_CHECKS = real
        self.a6_against(PLAN_LIST)()          # THE OTHER HALF: plant removed, the claim greens

    def test_r2_the_predicate_must_be_able_to_return_NOTHING(self):
        """R2 — DRIVE IT AGAINST A PLAN LIST WITH EVERY SCHEDULE MENTION REMOVED. A predicate
        that answers the same on an emptied source is reading something else: its import-time
        state, the engine's own tuple, or a literal somewhere. EXPECTED both halves — the
        branch returns the empty set, AND A6 then reds on the kinds it had been resolving."""
        emptied = _PERMANENT_NAME.sub("", self.real)
        self.assertNotEqual(emptied, self.real,
                            "no schedule mention was removed, so this row tests nothing")
        path = self.copy_of_the_plan_list(emptied)
        self.assertEqual(kinds_with_scheduled_users(path), set(),
                         "the branch still names kinds after every backticked name was removed "
                         "from its source — it is not reading the source it claims to read")
        with self.assertRaises(AssertionError) as caught:
            self.a6_against(path)()
        for kind in self.resolving:
            self.assertIn(kind, str(caught.exception),
                          "A6 did not red on %r after the schedule stopped naming it, so that "
                          "kind was being resolved by something other than the schedule" % kind)

    def test_r3_A_DESCRIPTION_MUST_NOT_RESOLVE(self):
        """R3 — THE DEFECT THAT MADE THIS UNIT UNAUTHORABLE, DRIVEN AS A RED WORLD. Before the
        `:2282` repair the plan list described the kind instead of naming it, and a description
        resolves only while someone remembers what it described. On a COPY, every backticked
        name of every kind the branch carries is replaced by that pre-repair wording.

        AND ITS NEAR-MISS CONTROL, WHICH IS THE HALF THAT PROVES THE SEARCH DISCRIMINATES: the
        plan list mentions at least one of these kinds BARE as well as backticked — prose about
        the kind rather than a row scheduling it. After the substitution the bare mention is
        still there, and the branch must STILL not return the kind. A predicate that matched on
        mere occurrence would pass the first half of this row and fail here."""
        described, bare_survivors = self.real, []
        for kind in self.resolving:
            backticked = "`%s`" % kind
            self.assertIn(backticked, described,
                          "%r is not named in backticks in the plan list, so the substitution "
                          "below would test nothing" % kind)
            described = described.replace(backticked, "the kind K2 mints")
            if re.search(r"(?<![`\w])%s(?![`\w])" % re.escape(kind), described):
                bare_survivors.append(kind)
        path = self.copy_of_the_plan_list(described)
        answered = kinds_with_scheduled_users(path)
        for kind in self.resolving:
            self.assertNotIn(kind, answered,
                             "the branch still resolves %r when the plan list only DESCRIBES "
                             "it — a description-resolver has regrown and the `:2282` repair "
                             "it was written for has stopped being load-bearing" % kind)
        self.assertTrue(bare_survivors,
                        "no kind survives as a BARE mention after its backticked names were "
                        "replaced, so this row's near-miss control has no subject and its "
                        "green above cannot tell 'reads backticks' from 'the word is gone'")
        with self.assertRaises(AssertionError):
            self.a6_against(path)()

    def test_r4_THE_SEVENTEENTH_IS_NOT_SPECIAL(self):
        """R4 — the branch must resolve by PLAN-LIST MEMBERSHIP and not by the kind's identity.
        A second name is planted into a copied plan-list row, beside a name already there, and
        the branch must return BOTH. A branch that works for exactly one kind is a hardcode
        wearing a function's name, and it would pass every row above."""
        before = kinds_with_scheduled_users()
        anchor = "`%s`" % self.resolving[0]
        planted_text = self.real.replace(
            anchor, "%s and `%s`" % (anchor, self.PLANTED_SECOND), 1)
        self.assertNotEqual(planted_text, self.real,
                            "the second name did not land, so this row tests nothing")
        path = self.copy_of_the_plan_list(planted_text)
        after = kinds_with_scheduled_users(path)
        self.assertEqual(sorted(after - before), [self.PLANTED_SECOND],
                         "planting one name into a plan-list row changed the branch's answer "
                         "by %r — a branch reading its source adds exactly what was added"
                         % (sorted(after - before),))
        self.assertEqual(sorted(before - after), [],
                         "planting a name REMOVED %r from the answer, so the branch is not "
                         "reading membership" % (sorted(before - after),))


# =====================================================================================
# THE DEFINITION-TIME LEASH — the policy arrives in the same round the kind does
# =====================================================================================

class TheLeashCase(unittest.TestCase):
    """THE LEASH THIS DECLARATION ARRIVES WITH, IN THE SAME ROUND IT DOES (design-soul §2).

    EVERY CLAUSE IS DRIVEN TO ITS REFUSAL. A leash whose clauses were never shown firing is
    the same defect as a check that has never refused anything — the estate has filed that
    five times and this file will not add a sixth."""

    BASE = {"check": "bound_field", "action": "A", "field": "f", "key_param": "k",
            "value_field": "v", "param": "p", "cite": "CAP-IS-LAW"}
    DEF = {"law_cited": "CAP-IS-LAW", "params": {"k": "required", "p": "required"}}

    def check(self, **overrides):
        c = dict(self.BASE)
        for key, val in overrides.items():
            if val is None:
                c.pop(key, None)
            else:
                c[key] = val
        d = dict(self.DEF)
        d["checks"] = [c]
        raised = {}

        class Door:
            def refuse(self, actor, op, rule, message):
                raised["rule"], raised["message"] = rule, message
                raise OpError(rule, message)

        try:
            opdefs.validate_definition_shape(Door(), "CREATE-OP", "owner", "X", d)
        except OpError:
            return raised
        return None

    def test_the_wellformed_row_passes_the_leash(self):
        """THE CONTROL FIRST. Without it every refusal below could be a leash that refuses
        everything, and the clauses would prove nothing."""
        self.assertIsNone(self.check(), "the leash refuses a well-formed row")

    def test_a_row_naming_no_action_is_refused(self):
        self.assertIn("no action", self.check(action=None)["message"])

    def test_a_row_naming_no_field_is_refused(self):
        self.assertIn("no field", self.check(field=None)["message"])

    def test_a_row_naming_no_key_param_is_refused(self):
        self.assertIn("no key_param", self.check(key_param=None)["message"])

    def test_a_row_naming_no_value_field_is_refused(self):
        self.assertIn("no value_field", self.check(value_field=None)["message"])

    def test_a_row_naming_no_param_is_refused(self):
        self.assertIn("no param", self.check(param=None)["message"])

    def test_a_key_param_the_op_does_not_take_is_refused(self):
        """THE CLAUSE A COPY OF `prior_value`'s LEASH WOULD HAVE MISSED, since that kind has
        only ONE parameter to lose. A key_param the op does not take binds by an absent value
        on every act, so the record is never found and the whole question collapses into
        `when_unbound` — silently, while reading as law the entire time."""
        self.assertIn("key_param", self.check(key_param="nope")["message"])

    def test_a_compared_param_the_op_does_not_take_is_refused(self):
        self.assertIn("param", self.check(param="nope")["message"])

    def test_an_unknown_when_unbound_policy_is_refused_and_never_defaulted(self):
        """A MISSPELT POLICY MUST NOT RESOLVE TO SILENCE. `permitt` falling back to the strict
        default would behave strictly while the author believed they had weakened it — the
        author's intent would vanish with nothing going red."""
        got = self.check(when_unbound="permitt")
        self.assertIn("permitt", got["message"])
        for policy in opdefs.UNBOUND_POLICIES:
            self.assertIn(policy, got["message"])

    def test_both_declared_policies_pass_the_leash(self):
        for policy in opdefs.UNBOUND_POLICIES:
            self.assertIsNone(self.check(when_unbound=policy), policy)


class WhenUnboundCase(WorldCase):
    """SILENCE MEANS REFUSE, and the weakening is visible in the LAW-DATA.

    THIS IS ROUTER_ABSENCE's RULE APPLIED TO A SECOND VOCABULARY, deliberately and for its
    reason: no declaration may weaken by omission or by habit."""

    def test_silence_means_refuse(self):
        """DRIVEN, not read off the constant. A row that omits the key refuses an unbound key."""
        checks = self.without_bound_field()
        row = [c for c in self.shipped_checks() if c["check"] == opdefs.BOUND_FIELD][0]
        silent = {k: v for k, v in row.items() if k != "when_unbound"}
        self.build(checks + [silent])
        self.stand_up(handles=(H1,))
        rule, message = self.refusal_of(self.hand, H1, GIVER, TAKER)
        self.assertEqual(rule, "FS-LAW-CUSTODY-TRANSFER")
        self.assertIn("belongs to no record", message,
                      "the refusal is not the engine-worded unbound one — the row's own "
                      "message reached a case it does not describe")

    def test_the_declared_permit_is_what_admits_the_first_hop(self):
        """THE CONTROL FOR THE ROW ABOVE, and the proof that the shipped weakening is doing the
        work rather than some other clause: the SAME act under the SHIPPED row is admitted."""
        self.build()
        self.stand_up(handles=(H1,))
        r = self.hand(H1, GIVER, TAKER)
        self.assertEqual(r["action"], OP)

    def test_the_shipped_declaration_states_its_weakening_in_the_law_data(self):
        """A LAW WHOSE REACH STOPS SHORT SAYS SO WHERE A READER OF THE DECLARATION CAN SEE IT.
        If this row ever reds, a weakening has become invisible."""
        row = [c for c in op_definition(REAL, OP)["checks"]
               if c["check"] == opdefs.BOUND_FIELD][0]
        self.assertEqual(row["when_unbound"], opdefs.UNBOUND_PERMIT)

    def test_the_engine_words_the_unbound_and_unresolved_refusals_not_the_author(self):
        """`prior_value`'s REPAIR, CARRIED FORWARD RATHER THAN REDISCOVERED. An author's
        `message` describes the law its row is about — the field not matching. Letting it reach
        a record that DOES NOT EXIST would record a refusal asserting what nothing measured."""
        src = open(opdefs.__file__, encoding="utf-8").read()
        arm = src[src.index("def _bound_field_check"):src.index("def _interpreter")]
        self.assertEqual(arm.count('c.get("message")'), 1,
                         "the row's message override reaches more than the mismatch refusal")


# =====================================================================================
# THE STRUCTURAL PROPERTIES THE PREVIOUS SIX ARRIVALS EACH RE-PROVED
# =====================================================================================

class StructuralCase(unittest.TestCase):

    def test_the_new_arm_is_dispatched_with_a_literal_spelling(self):
        """A NAMED CONSTANT HERE WOULD MAKE THE KIND INVISIBLE TO ITS OWN GUARD.
        `tests/test_ep28g_w2.py` enumerates the dispatch sites by walking for a
        `c["check"] == <constant>` comparison, and that guard is what proves every declared
        kind runs inside the decide region."""
        tree = ast.parse(open(opdefs.__file__, encoding="utf-8").read())
        literals = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare) and node.comparators:
                left, right = node.left, node.comparators[0]
                if (isinstance(left, ast.Subscript)
                        and isinstance(getattr(left, "slice", None), ast.Constant)
                        and left.slice.value == "check"
                        and isinstance(right, ast.Constant)):
                    literals.add(right.value)
        self.assertIn(opdefs.BOUND_FIELD, literals)
        for name in opdefs.OP_CHECKS:
            self.assertIn(name, literals,
                          "%r is declared and dispatched nowhere the guard can see" % name)

    def test_the_kind_took_zero_lines_in_the_gate(self):
        """THE SEVENTH ARRIVAL AND THE SEVENTH TIME THIS HOLDS. A kind needing a line in
        `gate.py` would be a kind that is not general vocabulary."""
        src = open(os.path.join(ROOT, "src/kernel/gate.py"), encoding="utf-8").read()
        self.assertNotIn(opdefs.BOUND_FIELD, src)

    def test_the_read_gains_no_reach_over_prior_values(self):
        """THE DOTTED PATH IS ALL THE REACH IT GAINS, and it is the SAME walker. A second
        resolver would be two computers of one thing (§A52)."""
        src = open(opdefs.__file__, encoding="utf-8").read()
        arm = src[src.index("def _bound_field_check"):src.index("def _interpreter")]
        self.assertIn("_resolve_field_path(", arm)
        self.assertEqual(src.count("def _resolve_field_path"), 1)


# =====================================================================================
# MAINT-3 — THE BRANCH THAT RESOLVES A MENTION AS A SCHEDULE
#
# A6's scheduled branch could not tell a SCHEDULE from a MENTION. It resolved any backticked
# lowercase identifier anywhere in design/36's plan-list span, and one such identifier sits in
# a sentence describing what a DIFFERENT EP already shipped. The rows below drive the
# narrowing and, more importantly, drive what the narrowing must NOT take with it.
# =====================================================================================

MAINT3_EVIDENCE = os.path.join(ROOT, "planning", "evidence", "MAINT-3")


class Maint3TheMentionIsNotAScheduleCase(unittest.TestCase):
    """MAINT-3's A1-A4 and R1-R4.

    EVERY KIND NAME HERE IS COMPUTED, never typed, with one stated exception class: the
    COINED fixtures below, which are control data planted into COPIES and are named as
    fixtures precisely because a name typed into a test that asserts about the schedule is a
    check reading its own copy. THE SUBJECT of A2 is computed too — it is whatever the
    narrowing removed, and the rows assert that this equals the mention site rather than
    assuming it."""

    #: FIXTURE, NOT SCHEDULE DATA. Coined names this estate does not declare and design/36
    #: does not carry. Their ABSENCE from the document is asserted before use, so a row that
    #: greens by finding nothing is told apart from a row that greens by discriminating.
    COINED_CONTROL = "a_name_no_document_carries"
    COINED_IN_PROSE = "a_coined_kind_planted_in_prose"
    COINED_ON_A_ROW = "a_coined_kind_planted_on_a_row"

    #: THE MENTION SITE, as text rather than as a line number. A coordinate is a ROLE and
    #: this text is an IDENTITY: design/36 has had seven live coordinates moved under it by
    #: its own siblings, and a row pinned to :367 would silently start asserting about a
    #: different sentence the next time a line was inserted above it.
    THE_MENTION = "whole-context version pinning, and the `fingerprint` check kind"

    def setUp(self):
        with open(PLAN_LIST, encoding="utf-8") as fh:
            self.document = fh.read()
        self.span = plan_list_text()
        self.narrow = kinds_with_scheduled_users()
        self.wide = kinds_named_anywhere_in_the_plan_list()

    # -- helpers ----------------------------------------------------------------------

    def line_of(self, needle, text=None):
        """The 1-based line number of `needle` in design/36, asserted UNIQUE. A site this
        unit reports must be the only one, or the number names one of several things."""
        text = self.document if text is None else text
        self.assertEqual(text.count(needle), 1,
                         "%r occurs %d times, so a line number for it names one of several "
                         "sites" % (needle[:50], text.count(needle)))
        return 1 + text[:text.index(needle)].count("\n")

    def copy_with_span(self, mutated):
        """The whole document copied with only its plan-list span replaced, written to a temp
        file so the branch reads it through its own file-opening path. THE WHOLE DOCUMENT is
        copied because the branch finds its section by that document's OWN headings — a file
        holding the bare span has no closing boundary and the branch REFUSES it, which would
        red every row below from the fixture rather than from the mutation."""
        self.assertIn(self.span, self.document,
                      "the span is not a contiguous slice of its document")
        fd, path = tempfile.mkstemp(suffix=".md", prefix="govos_maint3_")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.document.replace(self.span, mutated, 1))
        self.addCleanup(os.remove, path)
        return path

    def bank(self, name, lines):
        with open(os.path.join(MAINT3_EVIDENCE, name), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    # -- A1 ---------------------------------------------------------------------------

    def test_a1_the_determination_driven_or_refuted(self):
        """A1 — THE ROW THAT MAY END THIS UNIT, and it stays live rather than being a probe
        that was deleted after answering once. The plan's author could execute nothing and
        labelled the claim DETERMINED-BY-READING; this row drives it.

        BOTH PREDICATES ARE DRIVEN HERE, and that is what keeps A1 reproducible after the
        repair. The pre-MAINT-3 behaviour is `kinds_named_anywhere_in_the_plan_list`; the
        determination is a claim about THAT function, and it is confirmed or refuted every
        time the suite runs instead of being frozen into a text file on one afternoon."""
        self.assertNotIn(self.COINED_CONTROL, self.document,
                         "the coined control is IN design/36, so its absence from an answer "
                         "says nothing about the predicate")
        self.assertNotIn(self.COINED_CONTROL, self.wide,
                         "the control name is in the returned set, so this query is not "
                         "reading the plan list and its answer about anything else is void")
        self.assertTrue(self.wide,
                        "the pre-repair predicate returned nothing at all — an empty query "
                        "cannot confirm or refute a determination about what it contains")

        confirmed = "fingerprint" in self.wide
        site = self.line_of(self.THE_MENTION)
        span_start = 1 + self.document[:self.document.index(self.span)].count("\n")
        sites = {n: sorted(1 + m.start() and 1 + self.document[:m.start()].count("\n")
                           for m in re.finditer(re.escape("`%s`" % n), self.document))
                 for n in sorted(self.wide)}

        self.bank("A1-THE-DETERMINATION-DRIVEN-OR-REFUTED.txt", [
            "MAINT-3 A1 — THE DETERMINATION, DRIVEN. NOT READ.",
            "",
            "THE VERDICT, in the plan's own words:",
            "    THE AUTHOR'S DETERMINATION IS %s" % ("CONFIRMED" if confirmed else "REFUTED"),
            "",
            "The determination (plan §2): the pre-MAINT-3 scheduled branch resolves",
            "`fingerprint` off a sentence that merely mentions it.",
            "",
            "PRE-REPAIR predicate  kinds_named_anywhere_in_the_plan_list()",
            "    returns : %s" % sorted(self.wide),
            "    contains `fingerprint` : %s" % confirmed,
            "",
            "POST-REPAIR predicate kinds_with_scheduled_users()",
            "    returns : %s" % sorted(self.narrow),
            "    contains `fingerprint` : %s" % ("fingerprint" in self.narrow),
            "",
            "THE CONTROL — a coined name this estate does not declare and design/36 does",
            "not carry. Without it an absent subject cannot be told from an empty query.",
            "    coined control       : %r" % self.COINED_CONTROL,
            "    in design/36 at all  : %s" % (self.COINED_CONTROL in self.document),
            "    in the pre-repair set: %s" % (self.COINED_CONTROL in self.wide),
            "",
            "THE SPAN THE BRANCH READ:",
            "    opens at design/36 line : %d" % span_start,
            "    characters              : %d" % len(self.span),
            "    schedule records found  : %d" % len(schedule_rows(self.span)),
            "",
            "THE MENTION SITE, located by its TEXT and asserted unique, never by coordinate:",
            "    design/36 line %d" % site,
            "    %r" % self.THE_MENTION,
            "",
            "EVERY SITE OF EVERY PRE-REPAIR NAME, across the whole document, so a site",
            "inside the span can be told from one outside it:",
        ] + ["    %-16s %s" % (n, s) for n, s in sites.items()])

        self.assertTrue(confirmed,
                        "A1 REFUTES THE PLAN: `fingerprint` is NOT in the pre-repair set, so "
                        "the branch is narrower than its source reads and the hole this unit "
                        "was authored to repair does not exist — plan §8.1, STOP")

    # -- A2 ---------------------------------------------------------------------------

    def test_a2_a_mention_does_not_resolve(self):
        """A2 — THE FLIP. `fingerprint` must no longer be resolved on the strength of the
        sentence at design/36:367, which describes what EP-23 landed and schedules nothing."""
        site = self.line_of(self.THE_MENTION)
        self.assertIn(self.THE_MENTION, self.span,
                      "the mention is not inside the plan-list span, so this row's subject "
                      "was never one the branch could have resolved")
        inside_a_record = any(self.THE_MENTION in "\n".join(body)
                              for _, _, body in schedule_rows(self.span))

        self.bank("A2-a-mention-does-not-resolve.txt", [
            "MAINT-3 A2 — A MENTION DOES NOT RESOLVE.",
            "",
            "THE SITE THAT NO LONGER RESOLVES:",
            "    design/36-CAMPAIGN-3-DEPTH.md line %d" % site,
            "    %r" % self.THE_MENTION,
            "    located by TEXT and asserted unique in the document, never by coordinate",
            "",
            "    inside the plan-list span     : True   (so it WAS reachable before)",
            "    inside a schedule record      : %s" % inside_a_record,
            "    enclosing structure           : a markdown bullet, '- **EP-23 — ...**'",
            "",
            "THE ANSWER AFTER THE REPAIR:",
            "    kinds_with_scheduled_users() : %s" % sorted(self.narrow),
            "    contains `fingerprint`       : %s" % ("fingerprint" in self.narrow),
            "",
            "AND THE ANSWER BEFORE IT, driven in the same run so the pair is one taking:",
            "    kinds_named_anywhere_in_...  : %s" % sorted(self.wide),
            "    contained `fingerprint`      : %s" % ("fingerprint" in self.wide),
        ])

        self.assertFalse(inside_a_record,
                         "the mention IS inside a schedule record, so it is a row after all "
                         "and A2 is asking the branch to stop resolving a real schedule")
        self.assertNotIn("fingerprint", self.narrow,
                         "the scheduled branch still resolves `fingerprint`, which the plan "
                         "list only MENTIONS at line %d" % site)

    # -- A3 ---------------------------------------------------------------------------

    def test_a3_every_real_schedule_row_still_resolves(self):
        """A3 — THE LOAD-BEARING ROW, AND A2's CONTROL. A2 WITHOUT IT IS INDISTINGUISHABLE
        FROM BREAKING THE BRANCH: a predicate narrowed until it resolves nothing passes A2
        perfectly. THE WHOLE HAZARD OF THIS UNIT IS NARROWING PAST THE TARGET.

        COMPARED BY SET DIFFERENCE OVER MEMBERS, NEVER BY CARDINALITY (`:2263`). Two sets of
        the same size can differ in both directions at once and a count sees neither."""
        removed, added = sorted(self.wide - self.narrow), sorted(self.narrow - self.wide)
        survivors = sorted(self.narrow)
        sites = {n: sorted(1 + self.document[:m.start()].count("\n")
                           for m in re.finditer(re.escape("`%s`" % n), self.document))
                 for n in survivors}

        self.bank("A3-every-real-schedule-row-still-resolves.txt", [
            "MAINT-3 A3 — EVERY REAL SCHEDULE ROW STILL RESOLVES.",
            "",
            "THE SET DIFFERENCE, BY MEMBERS, NEVER BY CARDINALITY (:2263).",
            "Both sets are driven in ONE run, from the same document, in this test.",
            "",
            "    BEFORE  kinds_named_anywhere_in_the_plan_list() : %s" % sorted(self.wide),
            "    AFTER   kinds_with_scheduled_users()            : %s" % sorted(self.narrow),
            "",
            "    REMOVED (before - after) : %s" % removed,
            "    ADDED   (after - before) : %s" % added,
            "",
            "EXPECTED: removed == ['ceiling', 'fingerprint'] exactly; added == [] exactly.",
            "",
            "THE SURVIVORS AND THEIR SITES — the members that MUST NOT have left:",
        ] + ["    %-16s design/36 lines %s" % (n, s) for n, s in sites.items()] + [
            "",
            "THE COMMAND THAT PRODUCED THEM, kept per the extent rule:",
            "    PYTHONPATH=tests python3 -m unittest \\",
            "      tests.test_ep30_k1.Maint3TheMentionIsNotAScheduleCase\\",
            ".test_a3_every_real_schedule_row_still_resolves",
            "",
            "SCHEDULE RECORDS PARSED: %d" % len(schedule_rows(self.span)),
        ])

        # [DOCUMENTED FLIP — MAINT-EP29-K1-REPIN, 2026-09-02, charter §A57 era-stabilization
        # (board :2706, AUTHORISED-BY :2664). CAUSE: FOUNDING GROWTH, not a narrowing regression.
        # EP-31's lawful MEM-LAW-BUDGET founding create (1.30.0 -> 1.31.0) added the `ceiling`
        # check kind to opdefs.OP_CHECKS, and design/36's §6 plan-list prose describes it at its
        # own bullet ("exists as the `ceiling` kind ... EP-31 COMPLETES ceiling"). So `ceiling`
        # now appears in `kinds_named_anywhere_in_the_plan_list` (a backticked mention) while
        # NOT appearing in any schedule RECORD — the same shape `fingerprint` has always had.
        # CONFIRMED before this flip, per plan §8.2's STOP: `ceiling` is in OP_CHECKS, is
        # backticked inside the plan-list span, and is inside NO schedule record — the narrowing
        # predicate dropped no real schedule row. Its arrival in `removed` is a mention of a
        # lawfully-added kind, not the repair narrowing past its target.
        # ASSERTED: removed == ['ceiling', 'fingerprint'] — the lawful post-1.31.0 value.
        # SUPERSEDED: removed == ['fingerprint'].
        # REMAINS TRUE, AND STILL RED-CAPABLE: a THIRD member entering `removed` — a real
        # schedule row the predicate stops resolving — still reds and names itself, and `added`
        # staying [] still reds the moment the narrowing gains a member.]
        self.assertEqual(removed, ["ceiling", "fingerprint"],
                         "the narrowing removed %s — plan §8.2: any member other than the two "
                         "prose-mentioned kinds `ceiling` (EP-31, MEM-LAW-BUDGET) and "
                         "`fingerprint` leaving the set means the repair narrowed past its "
                         "target, STOP" % removed)
        self.assertEqual(added, [],
                         "the narrowing ADDED %s, so it is not a narrowing" % added)

    # -- A4 ---------------------------------------------------------------------------

    def test_a4_the_boundary_refusal_survives(self):
        """A4 — THE REPAIR MUST NOT REACH THE GUARD ONE STEP EARLIER. `plan_list_text`
        REFUSES when either boundary is missing rather than falling back to the whole file or
        to nothing, and both silent answers are wrong in the direction that hides it. A
        repair that quietly replaced it with a fallback would have removed a working guard
        while fixing a different one."""
        verdicts = []
        for label, mutate in (
                ("opening boundary removed", lambda d: d.replace("## 6. ", "## SIX ", 1)),
                ("closing boundary removed", lambda d: d.replace("## 7. ", "## SEVEN ", 1))):
            fd, path = tempfile.mkstemp(suffix=".md", prefix="govos_maint3_bound_")
            os.close(fd)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(mutate(self.document))
            self.addCleanup(os.remove, path)
            with self.assertRaises(RuntimeError) as caught:
                plan_list_text(path)
            verdicts.append((label, str(caught.exception)[:70]))
            with self.assertRaises(RuntimeError):
                kinds_with_scheduled_users(path)

        control = self.copy_with_span(self.span)
        self.assertEqual(kinds_with_scheduled_users(control), self.narrow,
                         "an UNMUTATED copy does not answer as the original does, so the "
                         "refusals above may come from the fixture and not the mutation")

        self.bank("A4-the-boundary-refusal-survives.txt", [
            "MAINT-3 A4 — THE BOUNDARY REFUSAL SURVIVES THE REPAIR.",
            "",
            "Driven on COPIES with a boundary removed. The tracked design/36 is never",
            "written by this unit — plan §6, and a unit that edits its own source is a",
            "check writing its own answer (:1793).",
            "",
            "REFUSALS OBSERVED — RuntimeError, not a fallback and not an empty answer:",
        ] + ["    %-26s %s..." % (l, m) for l, m in verdicts] + [
            "",
            "AND THE SAME REFUSAL REACHES THE NARROWED BRANCH, not only the text reader:",
            "    kinds_with_scheduled_users(copy) raised RuntimeError in both worlds",
            "",
            "THE CONTROL, and it is the half that proves the refusals came from the",
            "mutation rather than from the fixture: an UNMUTATED copy, written through",
            "the same temp-file path, answers exactly as the tracked document does.",
            "    copy answers : %s" % sorted(self.narrow),
        ])

    # -- R1 ---------------------------------------------------------------------------

    def test_r1_the_description_still_must_not_resolve(self):
        """R1 — EP-30-K2R's R3, RE-DRIVEN AFTER THIS REPAIR. Replacing a kind's backticked
        name with the pre-`:2282` wording must still stop it resolving. A row-shaped
        predicate that resolved a description would have traded one over-resolution for
        another, and this unit would have moved the defect rather than closed it."""
        described = self.span
        for kind in sorted(self.narrow):
            backticked = "`%s`" % kind
            self.assertIn(backticked, described,
                          "%r is not backticked in the span, so the substitution below "
                          "would test nothing" % kind)
            described = described.replace(backticked, "the kind K2 mints")
        self.assertNotEqual(described, self.span)
        answered = kinds_with_scheduled_users(self.copy_with_span(described))
        self.assertEqual(answered, set(),
                         "the branch still resolves %s when the plan list only DESCRIBES "
                         "the kinds — a description-resolver has regrown" % sorted(answered))

    # -- R2 ---------------------------------------------------------------------------

    def test_r2_a_planted_mention_must_not_resolve(self):
        """R2 — THE DEFECT ITSELF, PLANTED DELIBERATELY. This is the row that proves the
        repair addressed the CLASS and not the instance: `fingerprint` at :367 is one
        mention, and a predicate special-cased to that one sentence would pass A2 and fail
        here.

        THE PLANT IS A LIVE DECLARED KIND, not a coined one, and that is deliberate. A
        predicate that resolved by asking 'is this a kind the engine declares' would resolve
        it. The coined half runs beside it so the row also fails a predicate that resolves
        any backtick at all."""
        live = "require_prior"
        self.assertIn(live, opdefs.OP_CHECKS,
                      "the plant is not a declared kind, so this row's stronger half is not "
                      "being driven")
        self.assertNotIn(live, self.wide,
                         "the plant is ALREADY named in the span, so planting it changes "
                         "nothing and this row tests nothing")
        for coined in (self.COINED_IN_PROSE,):
            self.assertNotIn(coined, self.document)

        planted = self.span.replace(
            self.THE_MENTION,
            self.THE_MENTION + " (see `%s` and `%s`)" % (live, self.COINED_IN_PROSE), 1)
        self.assertNotEqual(planted, self.span, "the plant did not land")

        with_plant = kinds_with_scheduled_users(self.copy_with_span(planted))
        self.assertNotIn(live, with_plant,
                         "a LIVE kind mentioned in PROSE resolved — the branch is reading "
                         "mentions again and A2 passed only for the one sentence it names")
        self.assertNotIn(self.COINED_IN_PROSE, with_plant,
                         "a coined name mentioned in PROSE resolved")
        self.assertEqual(with_plant, self.narrow,
                         "planting a mention changed the answer by %s"
                         % sorted(with_plant ^ self.narrow))

        removed = kinds_with_scheduled_users(self.copy_with_span(self.span))
        self.assertEqual(removed, self.narrow,
                         "PLANT REMOVED: the answer did not return to what it was")

    # -- R3 ---------------------------------------------------------------------------

    def test_r3_a_planted_row_must_resolve(self):
        """R3 — A PREDICATE THAT CANNOT ADMIT A NEW SCHEDULE ROW IS NARROWED TO TODAY'S DATA
        AND WILL RED ON TOMORROW'S. Both wrapping shapes design/36 actually uses are driven:
        the terminator on the row's last line, and the terminator SPLIT so its status sits
        alone on a line carrying no pipe at all (design/36:880-881 is written that way)."""
        self.assertNotIn(self.COINED_ON_A_ROW, self.document)
        anchor = "  C6 | THE GROUP BATTERY AND CLOSE"
        self.assertIn(anchor, self.span, "the anchor row is not in the span")

        shapes = {
            "terminator on the row's own last line":
                "  C9 | A PLANTED ROW — wires `%s` by its permanent\n"
                "  name | XHIGH | order 9 | PENDING\n" % self.COINED_ON_A_ROW,
            "terminator split, status alone and pipeless":
                "  C9 | A PLANTED ROW — wires `%s` by its\n"
                "  permanent name | XHIGH | order 9 |\n  PENDING\n" % self.COINED_ON_A_ROW,
        }
        for label, row in shapes.items():
            planted = self.span.replace(anchor, row + anchor, 1)
            self.assertNotEqual(planted, self.span, "the row did not land (%s)" % label)
            answered = kinds_with_scheduled_users(self.copy_with_span(planted))
            self.assertEqual(sorted(answered - self.narrow), [self.COINED_ON_A_ROW],
                             "a NEW schedule row (%s) added %s to the answer — a predicate "
                             "that cannot admit a new row is pinned to today's document"
                             % (label, sorted(answered - self.narrow)))
            self.assertEqual(sorted(self.narrow - answered), [],
                             "adding a row REMOVED %s (%s)"
                             % (sorted(self.narrow - answered), label))

    # -- R4 ---------------------------------------------------------------------------

    def test_r4_the_emptied_source_still_answers_nothing(self):
        """R4 — EP-30-K2R's R2, RE-DRIVEN. A predicate that answers the same on an emptied
        source is reading something else: its import-time state, the engine's own tuple, or a
        literal somewhere. The records survive the emptying — only the NAMES go — so this
        also proves the answer comes from the names and not from the record count."""
        emptied = _PERMANENT_NAME.sub("", self.span)
        self.assertNotEqual(emptied, self.span, "no name was removed, so this tests nothing")
        path = self.copy_with_span(emptied)
        self.assertEqual(schedule_rows(emptied) and len(schedule_rows(emptied)),
                         len(schedule_rows(self.span)),
                         "emptying the NAMES also destroyed the RECORDS, so an empty answer "
                         "below would prove nothing about where names are read from")
        self.assertEqual(kinds_with_scheduled_users(path), set(),
                         "the branch still names kinds after every backticked name was "
                         "removed from its source")

    # -- R5, and it is this builder's own probe landed as a row -------------------------

    def test_r5_a_malformed_opener_must_not_swallow_the_prose_after_it(self):
        """R5 — NOT IN THE PLAN'S §4. ADDED BY THIS UNIT'S BUILDER AND DISCLOSED AS AN
        ADDITION, because the probe that found it is a verification probe and the charter
        says those land as regression rows.

        WHAT IT PINS. `schedule_rows` bounds its terminator search at the next opener-shaped
        line. Without that bound a line that merely LOOKS like a record opener — an
        identifier and a pipe — with no terminator after it swallows every line between
        itself and the next genuine record's status field, and every mention in that stretch
        resolves. Driven during this build: one such line planted above the EP-23 bullet put
        `fingerprint` back into the answer with the row-shaped predicate otherwise intact.

        WHY IT IS A ROW AND NOT A COMMENT. With the bound removed and nothing else changed,
        ALL SIXTY ROWS OF THIS MODULE PASSED — A2, A3, R1, R2, R3 and R4 included. The bound
        is the thing that makes this unit's repair hold, and until this row existed nothing
        in the estate would have noticed its deletion. A guard no row watches is this
        estate's signature defect and it had grown back inside the fix for it.

        THE PLANT IS A NEAR-MISS, not a known-present string: it is shaped exactly like a
        record opener and differs only in never terminating."""
        malformed = "  NOTE | this line opens like a record and never terminates\n"
        self.assertIsNotNone(_ROW_OPENS.search(malformed),
                             "the plant is not opener-shaped, so it is not the near-miss "
                             "this row exists to drive")
        self.assertIsNone(_ROW_CLOSES.search(malformed),
                          "the plant terminates, so it is a well-formed record and this row "
                          "would be driving R3 again rather than the runaway")

        planted = self.span.replace(self.THE_MENTION, malformed + self.THE_MENTION, 1)
        self.assertNotEqual(planted, self.span, "the malformed opener did not land")
        answered = kinds_with_scheduled_users(self.copy_with_span(planted))

        self.assertNotIn("fingerprint", answered,
                         "a malformed opener planted ABOVE the mention put `fingerprint` "
                         "back into the answer — the terminator search has stopped being "
                         "bounded and this unit's repair is open at a second door")
        self.assertEqual(answered, self.narrow,
                         "the malformed opener changed the answer by %s — prose between it "
                         "and the next record's status field is being read as schedule"
                         % sorted(answered ^ self.narrow))


if __name__ == "__main__":
    unittest.main()
