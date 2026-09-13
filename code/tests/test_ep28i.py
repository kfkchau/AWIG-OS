"""EP-28I — identity minting made CLASS-WIDE: the LAW pass, with the founding open.

Every probe here is a regression test (the campaign method: a verification probe lands as a
test).

WHAT THIS PASS CLOSES. `FILE-CREATE` declares `param_defaults: {"inode": "$path"}` and so
derives its node's identity from its own act. `FILE-MKDIR` declared only `{"perm": "755"}`
and `FILE-SYMLINK` declared no `param_defaults` block at all, so every unstamped mkdir and
symlink recorded `inode: None` and COLLAPSED onto one key in the namespace fold. The defect
is not the two missing entries. **The defect is that the derivation was PER-OP where the
property claimed is CLASS-WIDE** (§A49's first ruled instance): a property was read off one
member and stated of the gate.

THE NAMED WRONG REFERENCE THIS BATTERY EXISTS TO REFUSE is the two-line instance patch —
add the missing defaults to the two members and stop. That fixes two ops and leaves the
CLASS: the next minting op arrives with no derivation and nothing refuses it.
`TestTheGuardAtThreeDoors` is the detector, and its can-fail control is the row that says
the guard was guarding rather than decorating.

THE LAW, as data. An op DECLARES `mints: [<field>, ...]` — the fields of its own act by
which the thing it mints is identified. A declared field must DERIVE FROM THE ACT'S OWN
DISTINGUISHING CONTENT and can never arrive absent; a definition that declares a mint it
cannot derive is REFUSED AT DEFINITION TIME, at all three doors, by one validation
(`opdefs.validate_definition_shape`; design/36 ADDENDUM I.3).

Coverage (the EP's named battery):
  T-MINT-SET-ENUMERATED   the population computed from the pack's STRUCTURE (every CREATE-OP
                          record IS an op — §A51), reconciled against the EP's figure and
                          RED before any per-op verdict is read; the declared minting set
                          set-diffed both directions against the enumeration's own verdict.
  T-IDENTITY-PER-ACT      unstamped mints through the real gate produce distinct identities,
                          none None — driven on three members INCLUDING `FILE-SYMLINK`, the
                          member LEAST likely to share the property (§A49).
  T-COLLAPSE-IS-GONE-AT-THE-SYMPTOM   the collapse driven at `_fill_readdir`'s own site, with
                          the residual this pass does NOT close exhibited rather than claimed.
  T-GUARD-AT-THREE-DOORS  a minting declaration without a derivation refuses at the founding
                          installer, at CREATE-OP and at AMEND-OP; one validation, three
                          doors, asserted at each — plus the can-fail control.
  T-DIFF-IS-THE-CHANGE    the founding diff equals the declared change list EXACTLY, set-
                          diffed both directions against the pack at the BEFORE commit.
  T-VERSION-MOVES         `founding_version` reads 1.14.0 (MINOR, ruled), in the pack and in
                          the record the installer stamps.
  T-DEGENERATE-IDENTICAL  a STAMPED create is byte-identical under the new law — the port
                          still stamps until EP-28C W4b removes it, so this law had to be
                          compatible with the stamp present or W4b's ordering breaks.
  the declaration's leash the same round it arrives (design-soul §2): a malformed `mints`,
                          a mint that names nothing the record writes, a mint defaulted to a
                          CONSTANT and a mint defaulted to `$actor` are each refused, each
                          for its own stated reason.
"""

import json
import os
import shutil
# [EP-28Z, 2026-08-12] `import subprocess` REMOVED: this file's only spawn was its copy
# of the era-pin act, which now lives at `tests/era_pin.py`. An import naming a capability
# the file no longer uses tells a later reader it spawns processes, which is false.
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import era_pin                                                    # noqa: E402  (the era-pin home, EP-28Z)
from founding import install as install_module                    # noqa: E402
from founding.install import (                                    # noqa: E402
    FoundingIntegrityError, _validate, load_pack, records as _records,
)
from kernel import opdefs                                         # noqa: E402
from kernel.compose import build_full_kernel                      # noqa: E402
from kernel.errors import OpError                                 # noqa: E402
from bridge import custody                                        # noqa: E402
from bridge.kernel_port import KernelPort                          # noqa: E402
from bridge.mount import build_brain                              # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OWNER = "owner"

#: The port-shaped provenance the namespace fold reads its creator uid/gid out of. A
#: `FILE-MKDIR` whose `provenance_param` is REQUIRED cannot be called without one.
PROV = {"uid": 1000, "gid": 1000, "pid": 42, "window": "test"}

#: [RENAMED 2026-08-15, NOT REVALUED. Board `:575` filed the defect, `:816` verified it
#: against a live 1.24.0, `:841` drew this unit's fence. The four constants below were
#: spelled `BEFORE_COMMIT`, `AFTER_COMMIT`, `NEW_VERSION` and `OLD_VERSION`; those spellings
#: are kept here verbatim so a grep for any of them still lands. NOT ONE VALUE MOVED and no
#: assertion changed meaning.
#:
#: THE DEFECT IS THE NAME, NOT THE VALUE. A constant called `NEW_VERSION` holding 1.14.0 sits
#: TEN founding transitions behind a live 1.24.0, WITH A GREEN TEST UNDER IT — so a reader
#: reaching for "the current founding version" gets a stale one AND an assertion agreeing
#: with it. The rows were always right: they assert about a completed, accepted past, which
#: is what `:575` said when it filed this. A stored label that froze while the world moved is
#: this estate's own class, and a relative name is what defeats it.
#:
#: WHICH TRANSITION, ESTABLISHED BY READING THE CONSUMERS AND NOT ASSUMED FROM THE FILENAME:
#: `test_the_pack_body_outside_the_op_definitions_moved_only_where_declared` and
#: `TestTheVersionMoves.test_the_pack_reads_1_14_0` each pair BEFORE with OLD and AFTER with
#: NEW, and the pins measure `2965309` -> 1.13.0 and `a6a20f3` -> 1.14.0 when read at `git
#: show` rather than taken from these comments. That is EP-28I's own move, hence `EP28I_`.
#: NO CONSUMER DISAGREED WITH ANOTHER; one that did would have been a raise, not a choice.
#:
#: THE QUALIFIER IS THE ESTATE'S CONVENTION, CENSUSED BEFORE IT WAS CHOSEN.
#: `tests/test_ep29.py` spells 21 era-pin constants `<UNIT>_BEFORE_COMMIT` / `_BEFORE_VERSION`
#: / `_AFTER_VERSION` / `_AFTER_COMMIT` over `W1A_`, `W1B_`, `W2B_`, `W3A_` and `W3A3_`;
#: `tests/test_ep28n.py` spells its own `EP28N_`. That file is one EP holding many units so
#: its designation is the sub-unit; THIS file is one unit and its designation is EP-28I. The
#: hyphen is dropped because it is not an identifier character. `OLD`/`NEW` became
#: `BEFORE`/`AFTER` on `:780`'s precedent and for its reason: a version and a commit on the
#: same side are ONE era pin, and naming them alike says so. `EP28I_` collided with nothing
#: anywhere in the repo before this pass.
#:
#: TWO PROSE MENTIONS WERE RE-SPELLED WITH THE CODE — both documented-flip comments naming
#: the constant they flipped (the class `setUp` note below, and `TestTheVersionMoves`'s).
#: Leaving them would have left this file describing a name it no longer contains, which is
#: the dangling reference this pass exists to stop.]
#: THE COMMIT THIS PASS OPENED AT — the BEFORE side of the founding diff, recorded here so
#: the diff row compares against a fixed artifact rather than against whatever HEAD holds.
#: `git rev-parse 2965309:src/founding` was b65496215eeef0ab40a66d22bc552d019cc611c9 at the
#: dispatch and the manager measured all four anchor values against it.
EP28I_BEFORE_COMMIT = "2965309"

#: THE AFTER SIDE, ERA-PINNED TOO [DOCUMENTED FLIP, EP-28K, 2026-08-04 — and it is a CLASS
#: repair rather than a bump].
#:
#: These rows compared the BEFORE commit against the LIVE pack, so they asserted "the founding
#: looks exactly like this" rather than "EP-28I changed exactly this". The first lawful founding
#: move after them therefore reddened six rows that were describing a completed, accepted,
#: unchanged past — which is EP-28C AMENDMENT 8's raise 3 arriving a second time, at the diff
#: row instead of at the rev-parse pin: an identity check cannot tell a LAWFUL change from an
#: unlawful one, and it carries no expiry that keys on a lawful move.
#:
#: `pack_at`'s own docstring already stated the principle — "era-pinned on the BEFORE side, so
#: founding GROWTH cannot move this row (DIGEST-C2 theorem 11)" — and it was applied to one
#: side of a two-sided comparison. Both sides are pinned now, so this pass's claim is about the
#: diff it made and stays true however far the founding travels afterwards.
#:
#: `a6a20f3` is EP-28I's own founding-move commit: `git rev-parse a6a20f3:src/founding` is
#: `a7e119c1bf7930dfe4c53cdc5eb906ce0d7ec0ab`, the value its close entry recorded as its AFTER.
EP28I_AFTER_COMMIT = "a6a20f3"

#: THE POPULATION, as the EP states it. Reconciled against the pack's STRUCTURE in `setUp`
#: below and never trusted: a completeness figure stated only in prose is unfalsifiable, and
#: that is exactly how "sixty" survived a pre-flight, an authoring and a dispatch note
#: (§A51). The previous figure came from a probe filtering names on `isupper() and '-' in
#: name`, which silently dropped twelve hyphen-free ops — `MOUNT` among them.
DECLARED_POPULATION = 72

#: THE VERSION THIS PASS MOVES TO. MINOR, ruled: the pass adds a REFUSAL, and a refusal is
#: law-surface even when no existing byte breaks. The discriminator the ruling filed: does
#: the version tell a reader they must RE-READ THE LAW before writing against it?
EP28I_AFTER_VERSION = "1.14.0"
EP28I_BEFORE_VERSION = "1.13.0"

#: THE ENUMERATION'S VERDICT, in full, and it is the deliverable rather than a convenience.
#: Every one of the seventy-two ops was read; these are the ops whose OWN DESCRIPTION says
#: their effect brings a named entity into existence for the first time, with the field of
#: their own act by which that entity is identified. The reasons are in the entry, per op,
#: so a pre-flight can re-derive each verdict rather than take it.
ENUMERATED_MINTERS = {
    # object-borne identities — the record's `object` is a rendering of the named field
    "CREATE-ACCOUNT":      ["account_id"],
    "CREATE-SPACE":        ["name"],
    "CREATE-ROLE":         ["name"],
    "CREATE-OBLIGATION":   ["rule_id"],
    "GRANT":               ["grant_id"],
    "SEAL-SECRET":         ["name"],
    "SESSION-OPEN":        ["session_id"],
    "MAP-UID":             ["uid"],
    "COMMS-OPEN":          ["channel"],
    "MEM-GRANT":           ["region"],
    "REGISTER-CAPABILITY": ["driver"],
    "MOUNT":               ["mount_point"],
    # payload-borne identities — the namespace node's inode, which the object does not carry
    "FILE-CREATE":         ["inode"],
    "FILE-MKDIR":          ["inode"],
    "FILE-SYMLINK":        ["inode"],
}

#: THE DECLARED CHANGE LIST — what this pass changes in the founding and NOTHING else. The
#: diff row set-diffs the real pack against the BEFORE pack in BOTH directions against this.
CHANGED_DEFINITIONS = set(ENUMERATED_MINTERS)          # each gains `mints`
GAINED_INODE_DEFAULT = {"FILE-MKDIR", "FILE-SYMLINK"}  # each gains param_defaults["inode"]


def pack_ops(pack):
    """THE POPULATION, READ FROM THE STRUCTURE. Every `CREATE-OP` record IS an op (§A51):
    no name filter, no shape assumption, nothing that could exclude a member without saying
    so in the output. Returns {name: definition}."""
    out = {}
    for step in pack["steps"]:
        for r in step["records"]:
            if r.get("action") == "CREATE-OP":
                pl = r.get("payload") or {}
                out[pl["name"]] = pl["definition"]
    return out


def _name_shape_filtered(pack):
    """THE DOUBLE THAT GENERATES THE RED WORLD for the population clause: the exact filter
    that produced "sixty" — names that are upper-case AND contain a hyphen. Kept as an
    EXHIBIT, never as an instrument. It is here so the population row's failure mode is
    something this suite performs rather than something an entry asserts."""
    return {n: d for n, d in pack_ops(pack).items() if n.isupper() and "-" in n}


def pack_at(commit):
    """The founding pack as it stood at a pinned commit. Era-pinned on the BEFORE side, so
    founding GROWTH cannot move this row (DIGEST-C2 theorem 11).

    [DOCUMENTED FLIP — EP-28Z, 2026-08-12. CAUSE: one of EIGHTEEN copies of the era-pin act
    across TEN test files (board :410 counted five; the walk found the class). ASSERTED: a
    local `git show` spawn with its own skip-on-unresolvable branch. SUPERSEDED: the same
    act from `tests/era_pin.py`. REMAINS TRUE: the unresolvable-pin behaviour, exactly — a
    pin that stops resolving still raises `SkipTest` carrying git's own stderr, which is
    what `missing="skip"` names. GIVEN UP: nothing; the name and signature are unchanged.]
    """
    return era_pin.pack_at(commit, missing="skip")


# =================================================================================================
# T-MINT-SET-ENUMERATED — the population, computed, reconciled, and RED before any verdict
# =================================================================================================

class TestThePopulationIsComputedNotCarried(unittest.TestCase):
    """§A51 made an assertion instead of a sentence.

    THE PLACEMENT IS THE CLAUSE (§A48). The population check runs in `setUp`, not as a
    sibling row, because `unittest` orders methods alphabetically and a precedence stated in
    a docstring is void: `test_every_...` sorts before `test_the_population_...` would, so a
    mismatch would have been read only after the per-op verdicts had already gone green."""

    def setUp(self):
        # [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12, charter §A57. CAUSE: this pass added two
        # op definitions (DECLARE-IO-WINDOW, DEVICE-IO-WINDOW-WRITE) and moved the founding
        # 1.19.0 -> 1.20.0, so the live pack declares 74 CREATE-OP records against this pass's
        # enumerated 72 and every row in this class reddened in `setUp`. ASSERTED: `load_pack()`,
        # the LIVE tree. SUPERSEDED: `pack_at(EP28I_AFTER_COMMIT)` — EP-28I's own close commit, the
        # era these verdicts were read over. REMAINS TRUE: every per-op verdict below, unchanged,
        # about the seventy-two ops this enumeration actually read. GIVEN UP: the LIVE reach of
        # `test_every_declared_mint_passes_the_guard_in_the_shipped_pack`, which said "the whole
        # SHIPPED founding validates" and now says it of this era's founding. That claim is not
        # dropped — it is RE-HOMED to the pass that owns the current era, at
        # tests/test_ep29.py::TheWholeShippedFoundingStillValidates, because §A57's fence
        # permits no new row in THIS file.]
        self.pack = pack_at(EP28I_AFTER_COMMIT)
        self.ops = pack_ops(self.pack)
        self.assertEqual(
            len(self.ops), DECLARED_POPULATION,
            "the pack declares %d CREATE-OP records and this pass was written against %d — "
            "the population is COMPUTED from the structure and reconciled, never carried, "
            "and a mismatch reds HERE before any per-op verdict is read"
            % (len(self.ops), DECLARED_POPULATION))

    def test_every_create_op_record_is_an_op_and_the_names_are_distinct(self):
        """The structure count and the distinct-name count agree, so no member is hidden
        behind a duplicate name."""
        records = [r for r in _records(self.pack) if r.get("action") == "CREATE-OP"]
        self.assertEqual(len(records), DECLARED_POPULATION)
        self.assertEqual(len(self.ops), len(records))

    def test_the_name_shape_filter_returns_fewer_and_reds_only_the_population_clause(self):
        """THE GENERATED RED WORLD, produced through the instrument and recorded as output
        (§A42). The filter that produced "sixty" is run against today's pack and returns
        FEWER than the structure count; the twelve it drops are named, and the drop is
        invisible to every per-op row — which is why the population clause exists and why it
        is not an enumeration clause wearing a different name."""
        filtered = _name_shape_filtered(self.pack)
        self.assertLess(len(filtered), len(self.ops))
        dropped = sorted(set(self.ops) - set(filtered))
        self.assertEqual(
            dropped,
            ["COMPARE", "DESCHEDULE", "DISPUTE", "GRANT", "HANDOVER", "MOUNT", "OVERTURN",
             "REVIEW", "REVOKE", "TICK", "UNBIND", "UNMOUNT"])
        self.assertIn("MOUNT", dropped,
                      "the op that mints the mount root was excluded FOR NOT HAVING A HYPHEN")

    def test_the_enumerated_minting_set_matches_what_the_pack_declares_both_directions(self):
        """T-MINT-SET-ENUMERATED. The set the reading found and the set the pack declares are
        the same set, diffed in BOTH directions — a count would let one member swap for
        another silently."""
        # [EP-28T, 2026-08-08 — `AppendNothing` PER ROW.]
        # ASSERTED (2026-08-03): every op the enumeration names declares `mints: [<field>]`,
        #   set-diffed BOTH directions against the pack, with the field lists compared exactly.
        # SUPERSEDED (2026-08-08, EP-28S): the three FILESYSTEM minting ops moved off `mints`
        #   onto `mints_from: record_coordinate` — they no longer name a FIELD of their own act,
        #   because the thing that names what they found is the act's POSITION and a position is
        #   not a field. The other members of the enumeration are untouched.
        # REMAINS TRUE, separated out and STILL ASSERTED, and the set-diff is kept in BOTH
        #   directions because that is what stops one member swapping for another silently: every
        #   enumerated minter still DECLARES A SOURCE for the identity it founds, and the pack
        #   declares no minter the enumeration did not find. What moved is that a source is now
        #   one of TWO declarations, so the row reads both and says which each member uses.
        # NOT WIDENED: an op declaring NEITHER is still a finding, and an op declaring BOTH is
        #   refused at definition time by `opdefs` — asserted here as the population fact rather
        #   than assumed from that refusal.
        by_field = {n: list(d.get("mints") or []) for n, d in self.ops.items() if d.get("mints")}
        by_coordinate = {n for n, d in self.ops.items() if d.get("mints_from")}
        declared = set(by_field) | by_coordinate
        self.assertEqual(declared - set(ENUMERATED_MINTERS), set(),
                         "the pack declares a mint the enumeration did not find")
        self.assertEqual(set(ENUMERATED_MINTERS) - declared, set(),
                         "the enumeration found a mint the pack does not declare")
        self.assertEqual(by_field.keys() & by_coordinate, set(),
                         "an op declares BOTH sources — one says a field of the act names what "
                         "it founds and the other says none does, so it has declared neither")
        for name, fields in ENUMERATED_MINTERS.items():
            if name in by_coordinate:
                self.assertEqual(self.ops[name]["mints_from"], "record_coordinate", name)
                self.assertIsNone(self.ops[name].get("mints"), name)
            else:
                self.assertEqual(by_field[name], fields, name)

    def test_the_ops_the_enumeration_EXCLUDED_carry_no_mint_declaration(self):
        """The exclusions are a claim, so they are asserted rather than implied by silence.
        Fifty-seven ops reference an identity an earlier record founded, supersede one under
        an identity they share on purpose, or found nothing at all."""
        excluded = set(self.ops) - set(ENUMERATED_MINTERS)
        self.assertEqual(len(excluded), DECLARED_POPULATION - len(ENUMERATED_MINTERS))
        for name in sorted(excluded):
            self.assertIsNone(self.ops[name].get("mints"), name)

    def test_every_declared_mint_passes_the_guard_in_the_shipped_pack(self):
        """The positive half: the whole shipped founding validates under the new clause. A
        guard whose only evidence is that nothing refused it has not been shown to admit
        anything either."""
        for name, d in self.ops.items():
            opdefs.validate_definition_shape(_Door(), "FOUNDING", "SYSTEM", name, d)


class _Door:
    """A door that RAISES rather than records, so a refusal is observable without a store."""

    class Refused(Exception):
        def __init__(self, rule, message):
            super().__init__(message)
            self.rule, self.message = rule, message

    def refuse(self, actor, op, rule, message):
        raise _Door.Refused(rule, message)


# =================================================================================================
# T-GUARD-AT-THREE-DOORS — the deliverable
# =================================================================================================

def _minting_op_without_a_derivation():
    """A definition that DECLARES it mints an identity and cannot derive it: `ident` is an
    optional parameter with no default, which is exactly `FILE-MKDIR` before this pass."""
    return {"law_cited": "CAP-IS-LAW", "description": "a test-world minting op",
            "params": {"path": "required", "ident": "optional"},
            "object_param": "path", "payload_from": ["path", "ident"],
            "mints": ["ident"]}


def _minting_op_with_a_derivation():
    """The same op with the derivation declared — the FILE-CREATE shape."""
    d = _minting_op_without_a_derivation()
    d["param_defaults"] = {"ident": "$path"}
    # `path`/`ident`: both STRUCTURAL — a namespace path and a minted identity scalar are
    # governance fields safe inline (census: `path` structural everywhere; a minted identity
    # sits with `inode`/`grant_id`/`account_id`, all structural). Classified ONLY here, on the
    # ADMIT-intent op (this is the definition the three-door test creates lawfully); the
    # derivation-less refusal fixture stays unclassified — it refuses at `_require_derivable_
    # mints`, which runs before the vocabulary door. [design/46 member-2, archi :2956 RULING 1]
    d["structural_params"] = ["path", "ident"]
    return d


class _Live(unittest.TestCase):
    """A kernel composed from the SHIPPED founding and nothing else."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28i-")
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def definition(self, name):
        return (self.views.op_definitions().get(name) or {}).get("definition") or {}


class TestTheGuardAtThreeDoors(_Live):
    """ONE VALIDATION, THREE DOORS (design/36 ADDENDUM I.3). A guard at two of three doors
    guards nothing, and the founding installer is the door all seventy-two live definitions
    actually came through."""

    def test_door_one_the_founding_installer_refuses_the_whole_founding(self):
        """The installer's pre-flight walks every CREATE-OP record and refuses the WHOLE
        founding on the first malformed one — nothing appended, because a half-founded record
        is worse than none."""
        recs = [{"actor": "SYSTEM", "action": "CREATE-OP", "object": "op:MINTER",
                 "rule_cited": "CAP-IS-LAW",
                 "payload": {"kind": "op_definition", "name": "MINTER",
                             "definition": _minting_op_without_a_derivation()}}]
        with self.assertRaises(FoundingIntegrityError) as raised:
            _validate(recs)
        self.assertIn("mints", str(raised.exception))
        self.assertIn("the whole founding is refused", str(raised.exception))

    def test_door_two_create_op_refuses_cited_and_recorded(self):
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError) as raised:
            self.gate.execute("CREATE-OP", OWNER,
                              {"name": "MINTER", "definition": _minting_op_without_a_derivation()})
        self.assertEqual(raised.exception.rule, "AR-2")
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)
        self.assertFalse(self.gate.has("MINTER"))

    def test_door_three_amend_op_refuses_cited_and_recorded(self):
        """AMEND-OP is the door a LATER campaign uses, so it is the one a fix landed only at
        CREATE-OP would leave open. The op is created LAWFULLY first, then amended into the
        malformed shape."""
        self.gate.execute("CREATE-OP", OWNER,
                          {"name": "MINTER", "definition": _minting_op_with_a_derivation()})
        self.assertTrue(self.gate.has("MINTER"))
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError) as raised:
            self.gate.execute("AMEND-OP", OWNER,
                              {"name": "MINTER", "definition": _minting_op_without_a_derivation()})
        self.assertEqual(raised.exception.rule, "AR-2")
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)
        self.assertEqual(self.definition("MINTER").get("param_defaults"), {"ident": "$path"},
                         "the refused amendment left the lawful definition standing")

    def test_the_three_doors_run_the_SAME_validation_and_not_three_copies(self):
        """The property under 'one validation': the installer imports the function the
        CREATE-OP path calls. Asked of the module object, not of anybody's source text."""
        self.assertIs(install_module.validate_definition_shape,
                      opdefs.validate_definition_shape)

    def test_the_can_fail_control_the_guard_neutered_ADMITS_the_definition(self):
        """THE ROW THAT SAYS THE GUARD WAS GUARDING. With the minting clause replaced by a
        no-op in a double, the derivation-less definition sails through every door. A guard
        that has never been seen NOT firing has not been shown to be the thing that fired."""
        original = opdefs._require_derivable_mints
        try:
            opdefs._require_derivable_mints = lambda gate, opname, actor, d: None
            opdefs.validate_definition_shape(_Door(), "CREATE-OP", OWNER, "MINTER",
                                             _minting_op_without_a_derivation())
            recs = [{"actor": "SYSTEM", "action": "CREATE-OP", "object": "op:MINTER",
                     "rule_cited": "CAP-IS-LAW",
                     "payload": {"kind": "op_definition", "name": "MINTER",
                                 "definition": _minting_op_without_a_derivation()}}]
            _validate(recs)                       # the founding would have loaded
        finally:
            opdefs._require_derivable_mints = original
        with self.assertRaises(_Door.Refused):    # and the real guard refuses it again
            opdefs.validate_definition_shape(_Door(), "CREATE-OP", OWNER, "MINTER",
                                             _minting_op_without_a_derivation())


class TestTheDeclarationsOwnLeash(_Live):
    """Every power arrives with its leash in the same round (design-soul §2). A declaration
    outside the grammar would read as a sentence nobody wrote, and the closed-vocabulary
    discipline that already governs `checks`, `act_kind` and the router family governs this."""

    def _refused(self, **extra):
        d = {"law_cited": "CAP-IS-LAW", "description": "d",
             "params": {"path": "required"}, "object_param": "path", "payload_from": ["path"]}
        d.update(extra)
        with self.assertRaises(_Door.Refused) as raised:
            opdefs.validate_definition_shape(_Door(), "CREATE-OP", OWNER, "X", d)
        self.assertEqual(raised.exception.rule, "AR-2")
        return raised.exception.message

    def test_a_mints_that_is_not_a_list_refuses(self):
        self.assertIn("a list", self._refused(mints="path"))

    def test_an_empty_mints_refuses(self):
        self.assertIn("names no field", self._refused(mints=[]))

    def test_a_non_string_member_refuses(self):
        self.assertIn("a list", self._refused(mints=[7]))

    def test_a_mint_naming_a_field_the_record_never_writes_refuses(self):
        self.assertIn("never writes", self._refused(mints=["ghost"]))

    def test_a_mint_defaulted_to_a_CONSTANT_refuses(self):
        """A constant is the same for every act, so every unstamped mint would share one
        identity — the collapse this pass exists to close, wearing a value instead of None."""
        msg = self._refused(params={"path": "required", "ident": "optional"},
                            payload_from=["path", "ident"],
                            param_defaults={"ident": "fixed"}, mints=["ident"])
        self.assertIn("the same for every act", msg)

    def test_a_mint_defaulted_to_the_ACTOR_refuses(self):
        """`$actor` is present, so it passes a determinacy test and fails the real one: two
        acts by one actor would collide."""
        msg = self._refused(params={"path": "required", "ident": "optional"},
                            payload_from=["path", "ident"],
                            param_defaults={"ident": "$actor"}, mints=["ident"])
        self.assertIn("the same for every act", msg)

    def test_a_derivation_chain_that_LOOPS_refuses(self):
        """`$a -> $b -> $a` fills nothing at run time. A guard that recursed on it would be a
        worse defect than the one it guards."""
        msg = self._refused(params={"path": "required", "a": "optional", "b": "optional"},
                            payload_from=["path", "a", "b"],
                            param_defaults={"a": "$b", "b": "$a"}, mints=["a"])
        self.assertIn("can arrive absent", msg)

    def test_a_mint_derived_through_a_chain_to_a_required_param_PASSES(self):
        """The positive control for the same machinery: a two-step `$` chain ending at a
        required parameter is a derivation, and the guard admits it."""
        opdefs.validate_definition_shape(
            _Door(), "CREATE-OP", OWNER, "X",
            {"law_cited": "CAP-IS-LAW", "description": "d",
             "params": {"path": "required", "mid": "optional", "ident": "optional"},
             "object_param": "path", "payload_from": ["path", "mid", "ident"],
             "param_defaults": {"mid": "$path", "ident": "$mid"}, "mints": ["ident"]})

    def test_the_guard_reads_a_FROZEN_definition_identically(self):
        """A definition read back off the record is FROZEN (H1): dicts become
        `MappingProxyType` and LISTS BECOME TUPLES (`store._freeze`). A membership test
        written as `isinstance(decl, list)` would therefore refuse a lawful declaration the
        moment it arrived from the record instead of from a caller — which is exactly the
        defect `router_param` carries a comment about, one field over. Driven rather than
        reasoned about: the same two definitions, frozen, get the same two verdicts."""
        from kernel.store import _freeze
        opdefs.validate_definition_shape(
            _Door(), "CREATE-OP", OWNER, "X", _freeze(_minting_op_with_a_derivation()))
        with self.assertRaises(_Door.Refused):
            opdefs.validate_definition_shape(
                _Door(), "CREATE-OP", OWNER, "X",
                _freeze(_minting_op_without_a_derivation()))

    def test_a_mint_carried_by_payload_derive_PASSES_and_an_underived_one_does_not(self):
        """`payload_derive` is the other way a payload field gets a value, so the guard reads
        it — and reads the parameters the template depends on, which is where an underived
        one is caught."""
        base = {"law_cited": "CAP-IS-LAW", "description": "d",
                "params": {"path": "required", "loose": "optional"},
                "object_param": "path", "payload_from": ["path"], "mints": ["ident"]}
        opdefs.validate_definition_shape(
            _Door(), "CREATE-OP", OWNER, "X",
            dict(base, payload_derive={"ident": {"tpl": "node:{path}"}}))
        with self.assertRaises(_Door.Refused):
            opdefs.validate_definition_shape(
                _Door(), "CREATE-OP", OWNER, "X",
                dict(base, payload_derive={"ident": {"tpl": "node:{loose}"}}))


# =================================================================================================
# T-IDENTITY-PER-ACT — driven, on three members, including the least-likely one BY NAME
# =================================================================================================

class TestIdentityPerAct(_Live):
    """§A49 APPLIED INSIDE THIS PASS'S OWN ACCEPTANCE. The class property is driven on
    `FILE-SYMLINK` by name — the member with no `param_defaults` block at all, whose shape is
    furthest from `FILE-CREATE`, the member the property was first observed on. Checking a
    second create-shaped op would have confirmed nothing."""

    #: [EP-28T, 2026-08-08 — `AppendNothing`, and it is stated ONCE at the helper the four rows
    #: below share, then per row where each row's own claim differs.]
    #:
    #: WHAT THESE ROWS ASSERTED (2026-08-03, EP-28I): an unstamped mint of each kind RECORDS a
    #: derived identity rather than `None`, and under founding 1.14.0-1.17.0 that identity was
    #: the act's PATH, so `mint(...) == "/d1"` was the whole claim.
    #: WHAT SUPERSEDED IT (2026-08-08, EP-28S, founding 1.18.0): the three minting ops declare
    #: `mints_from: record_coordinate` and write NO identity into the record at all. Every one
    #: of these rows now reads `None` out of the payload — which is not the collapse the rows
    #: were written against, it is the identity having moved OUT of the payload entirely.
    #: WHAT REMAINS TRUE, separated out and STILL ASSERTED, and it is the class property this
    #: whole file exists for: **AN UNSTAMPED MINT OF ANY KIND IS IDENTIFIED, AND TWO OF THEM ARE
    #: NEVER THE SAME THING.** That was the defect EP-28I closed — mkdir and symlink collapsing
    #: onto one key — and it is closed harder now: distinctness used to rest on the PATHS being
    #: distinct, and now rests on record POSITIONS being distinct, which holds even for two
    #: mints of ONE path. So `mint()` returns the identity the act is KNOWN BY rather than the
    #: identity it RECORDED, and it returns it from the record's own coordinate.
    #: WHAT IS GIVEN UP: these rows no longer prove the identity is written into the payload.
    #: They never should have — that was the mechanism, not the property, and the mechanism is
    #: what changed. `test_ep28c_w4b` holds the payload's own shape.
    def mint(self, op, path, **kw):
        """One unstamped mint through the REAL gate — the inode simply not supplied.

        Returns WHAT THE ACT FOUNDS, derived exactly as the fold derives it: the recorded
        identity where the record names one (pre-1.18.0 worlds), the act's own coordinate where
        it does not. Two cases, non-overlapping, read from the record's own shape."""
        params = {"path": path, "provenance": PROV}
        params.update(kw)
        self.gate.execute(op, OWNER, params)
        e = self.store.by_action(op)[-1]
        named = (e.get("payload") or {}).get("inode")
        return named if named is not None else custody.formal_name(e["seq"])

    def test_file_mkdir_unstamped_records_a_derived_identity_not_None(self):
        e = self.gate.execute("FILE-MKDIR", OWNER, {"path": "/d1", "provenance": PROV})
        self.assertIsNone((e.get("payload") or {}).get("inode"),
                          "EP-28T: the record names no identity under 1.18.0")
        self.assertEqual(self.store.by_action("FILE-MKDIR")[-1]["seq"], e["seq"])
        self.assertEqual(custody.formal_name(e["seq"]),
                         custody.fold(self.store.all()).lookup("/d1").identity)

    def test_file_symlink_unstamped_records_a_derived_identity_not_None(self):
        """THE LEAST-LIKELY MEMBER, driven by name — §A49, and it stays driven by name."""
        self.assertEqual(self.mint("FILE-SYMLINK", "/l1", target="/d1"),
                         custody.fold(self.store.all()).lookup("/l1").identity)

    def test_file_create_unstamped_is_unchanged_it_already_had_the_derivation(self):
        """The row's NAME records a fact about EP-28I: `FILE-CREATE` already carried the
        derivation the other two lacked. Under 1.18.0 all three take the SAME source, so what
        this row now says is that the member that never needed repair is not a special case."""
        self.assertEqual(self.mint("FILE-CREATE", "/f1"),
                         custody.fold(self.store.all()).lookup("/f1").identity)

    def test_two_unstamped_mints_of_each_kind_are_DISTINCT_and_none_is_None(self):
        """The property the law exists for, over all three members at once — UNCHANGED, and
        this is the row that carries the class claim after the mechanism moved."""
        got = [self.mint("FILE-MKDIR", "/a"), self.mint("FILE-MKDIR", "/b"),
               self.mint("FILE-SYMLINK", "/c", target="/a"),
               self.mint("FILE-SYMLINK", "/d", target="/a"),
               self.mint("FILE-CREATE", "/e"), self.mint("FILE-CREATE", "/f")]
        self.assertNotIn(None, got)
        self.assertEqual(len(set(got)), len(got))
        # AND THE STRONGER FORM THE NEW SOURCE MAKES AVAILABLE, driven rather than argued: two
        # mints of ONE path are also distinct, which path identity could never deliver and is
        # the collision the campaign spent EP-28P and EP-28S deleting.
        self.gate.execute("FILE-UNLINK", OWNER, {"path": "/e", "provenance": PROV})
        self.assertNotEqual(self.mint("FILE-CREATE", "/e"), got[4])

    def test_the_namespace_fold_holds_SIX_distinct_nodes_and_not_one(self):
        """Driven where it matters: the fold that serves the mount. Before this pass the four
        mkdir/symlink acts collapsed onto the single key None."""
        for op, path, extra in (("FILE-MKDIR", "/a", {}), ("FILE-MKDIR", "/b", {}),
                                ("FILE-SYMLINK", "/c", {"target": "/a"}),
                                ("FILE-SYMLINK", "/d", {"target": "/a"}),
                                ("FILE-CREATE", "/e", {}), ("FILE-CREATE", "/f", {})):
            self.mint(op, path, **extra)
        state = custody.CustodyState()
        for e in self.store.all():
            state.apply(e)
        minted = {ino for ino in state.inodes if ino != custody.ROOT_INO}
        self.assertEqual(len(minted), 6)
        self.assertNotIn(None, minted)

    def test_THE_RED_WORLD_the_era_pinned_PRE_LAW_definitions_collapse_onto_None(self):
        """PRODUCED THROUGH THE INSTRUMENT AND RECORDED AS OUTPUT (§A42), with the pack read
        from the BEFORE commit so the world is era-pinned rather than described. The SAME
        interpreter, the SAME gate, the SAME drive — one variable changed, the definition —
        and both mkdirs land on the single key None."""
        before = pack_ops(pack_at(EP28I_BEFORE_COMMIT))
        old = before["FILE-MKDIR"]
        self.assertIsNone((old.get("param_defaults") or {}).get("inode"),
                          "the BEFORE pack is supposed to be the one without the derivation")
        run = opdefs._interpreter(self.gate, self.store, self.views, "FILE-MKDIR", old)
        got = [run(OWNER, {"path": "/x", "provenance": PROV})["payload"]["inode"],
               run(OWNER, {"path": "/y", "provenance": PROV})["payload"]["inode"]]
        self.assertEqual(got, [None, None])
        # DOCUMENTED FLIP, EP-28C W4b (2026-08-03). The collapse this red world drove is now
        # UNREACHABLE THROUGH THE FOLD rather than merely absent: `custody.Inode` renders the
        # recorded identity at ingestion and an absent identity has nothing to render, so the
        # fold REFUSES the pre-law record instead of filing two directories under one key.
        # The row keeps its subject — the pre-law definitions produce no identity — and its
        # second half now asserts the stronger outcome. **The cost is stated rather than
        # hidden: a world recorded before 1.14.0 that contains an unstamped namespace create
        # no longer folds at all.** No such world exists in this estate (both ports stamped
        # under the old law), which is why this is a refusal and not a migration.
        # [EP-28T, 2026-08-08 — `AppendNothing` PER ROW, second flip on the same clause.]
        # ASSERTED (2026-08-03, W4b's flip): a pre-law record naming NO identity is REFUSED by
        #   the fold with `UnrenderableIdentity`, because `render_ino(None)` has nothing to
        #   render — so the collapse was unreachable rather than merely absent.
        # SUPERSEDED (2026-08-08, EP-28S, founding 1.18.0): "names no identity" stopped meaning
        #   "unfoldable" and started meaning "named by its own coordinate". The refusal moved
        #   from `render_ino` to `formal_name`, and its CLASS moved with it — these records
        #   carry no `seq` either, so the parse door refuses first with
        #   `UnparseableRecordValue`. WHAT WAS FATAL BECAME THE SIGNAL, and this row is where
        #   that sentence has a consequence.
        # REMAINS TRUE, separated out and STILL ASSERTED — the row's subject is untouched:
        #   neither identity-less create enters the namespace, so the collapse onto one key is
        #   still unreachable. Both refusal classes are named because they mean different
        #   things and a bare `except` would hide which fired.
        # AND THE COST STATED AT W4b IS NOW SMALLER, which is worth recording because it was
        #   recorded as a cost: a pre-1.14.0 world with an unstamped create no longer fails to
        #   fold merely for lacking an identity — it folds and gets distinct coordinates —
        #   PROVIDED its records carry their positions. Only a record with NO position refuses.
        #   The second arm below drives exactly that difference.
        state = custody.CustodyState()
        for path in ("/x", "/y"):
            with self.assertRaises((custody.UnrenderableIdentity,
                                    custody.UnparseableRecordValue)):
                state.apply({"action": "FILE-MKDIR", "actor": OWNER,
                             "payload": {"path": path, "inode": None, "perm": "755"}})
        self.assertEqual(len([i for i in state.inodes if i != custody.ROOT_INO]), 0,
                         "the collapse is not merely gone, it is unreachable: neither "
                         "identity-less create entered the namespace at all")
        # THE CURE, DRIVEN: the same two identity-less creates, now carrying their record
        # positions, fold to TWO DISTINCT nodes instead of collapsing onto one key. This is the
        # half W4b could not have written, and it is asserted rather than described.
        cured = custody.CustodyState()
        for seq, path in ((1, "/x"), (2, "/y")):
            cured.apply({"action": "FILE-MKDIR", "actor": OWNER, "seq": seq,
                         "payload": {"path": path, "inode": None, "perm": "755"}})
        minted = [i for i in cured.inodes if i != custody.ROOT_INO]
        self.assertEqual(len(minted), 2, "the two pre-law creates did not become two nodes")
        self.assertNotEqual(cured.names["/x"], cured.names["/y"])


# =================================================================================================
# T-COLLAPSE-IS-GONE-AT-THE-SYMPTOM — and the residual this pass does NOT close
# =================================================================================================

class TestTheCollapseAtTheSymptomSite(unittest.TestCase):
    """`kernel_port._fill_readdir` is where the collapse surfaced as a `TypeError`. The
    collapse is gone; the SYMPTOM is not, and the reason is a fact about the port rather than
    about the law. Exhibited rather than claimed — see the raise this row carries."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28i-port-")
        self.store, self.gate, self.views, self.blobs = build_brain(
            os.path.join(self.dir, "rec.jsonl"), os.path.join(self.dir, "blobs"))
        self.port = KernelPort(self.store, self.gate, self.views, self.blobs)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _unstamped(self, op, path, **kw):
        params = {"path": path, "provenance": PROV}
        params.update(kw)
        self.gate.execute(op, OWNER, params)

    def test_the_collapse_is_gone_two_unstamped_mkdirs_are_two_nodes_in_the_served_fold(self):
        """THE GOVERNANCE PROPERTY, at the symptom's own site. The port's state is the fold
        the mount serves; before this pass these two directories were one node in it."""
        self._unstamped("FILE-MKDIR", "/p")
        self._unstamped("FILE-MKDIR", "/q")
        # DOCUMENTED FLIP, EP-28C W4b (2026-08-03): the fold is keyed by the RENDERING now,
        # so the identities are read off the nodes rather than off the keys. Same property,
        # same two nodes; what moved is which of the two values the table is keyed by.
        # [EP-28T, 2026-08-08 — `AppendNothing` PER ROW, second flip on this clause.]
        # ASSERTED (2026-08-03): the two directories are two nodes and their identities are the
        #   two PATHS `{"/p", "/q"}`.
        # SUPERSEDED (2026-08-08, EP-28S): an identity is the birth act's own record coordinate,
        #   so the two identities are two integers in the formal-name band, not two paths.
        # REMAINS TRUE, separated out and STILL ASSERTED — and it is the row's own name: TWO
        #   UNSTAMPED MKDIRS ARE TWO NODES IN THE SERVED FOLD. Before EP-28I they were one. The
        #   count is the governance property; the spelling of the identities never was, which is
        #   exactly what the 2026-08-03 flip said when it moved from keys to node identities.
        #   Asserted on the COUNTABLE, so the row stops needing a rewrite every time the
        #   identity's source moves.
        minted = {n.identity for i, n in self.port.state.inodes.items()
                  if i != custody.ROOT_INO}
        self.assertEqual(len(minted), 2, "the two mkdirs are not two nodes in the served fold")
        self.assertEqual({self.port.state.lookup(p).identity for p in ("/p", "/q")}, minted,
                         "the two names do not resolve to the two nodes")
        self.assertNotIn(None, minted)

    def test_THE_RESIDUAL_a_derived_identity_is_not_an_INTEGER_and_the_port_needs_one(self):
        """WHAT THIS PASS DOES NOT CLOSE, driven rather than described, so nobody downstream
        reads the law as having finished the job.

        The only derivation forms the interpreter has — `param_defaults` `$other`,
        `payload_derive` `tpl` and `copy` — all yield the value of another field, and for a
        namespace mint that field is the PATH, a string. `_fill_readdir` formats `%d` and
        `_int` coerces a non-number to 0, so a derived identity is unservable at the port in
        two different ways. THIS IS TRUE OF `FILE-CREATE` TODAY, under the derivation the
        ruling called 'unique per path BY CONSTRUCTION' and this pass was directed to extend
        — so it is a property of the mechanism and not of this pass's choice of it.

        EP-28C W4b removes the port's stamp. It cannot land on a string identity, and this
        row is the evidence for that raise rather than a claim about it."""
        self._unstamped("FILE-MKDIR", "/p")
        node = self.port.state.lookup("/p")
        # DOCUMENTED FLIP, EP-28C W4b (2026-08-03) — AND THIS ROW IS ITS OWN DISCHARGE
        # EVIDENCE. It was written to exhibit a residual and to name W4b as the pass that
        # would close it, so its expiry is the closure. Both halves of the residual are gone
        # and both are re-asserted here in the form that proves it: the identity is still the
        # PATH (the governance property, untouched), the served number is its RENDERING, and
        # `_fill_readdir`'s own `%d` expression can no longer meet a string. The silent-zero
        # coercion that produced the second half is deleted, so asking for it now REFUSES.
        # [EP-28T, 2026-08-08 — `AppendNothing` PER ROW, THIRD writing of this clause and the
        # one where the residual finally has no remainder.]
        # ASSERTED (2026-08-03, W4b's discharge): the identity is still the PATH, its RENDERING
        #   is an integer at or above `RENDER_FLOOR`, and `%d` can no longer meet a string.
        # SUPERSEDED (2026-08-08, EP-28S): the identity is the birth act's coordinate, so it is
        #   ALREADY an integer and it sits in the FORMAL-NAME band `[SEQ_FLOOR, RENDER_FLOOR)`
        #   — below the digest band this row pinned, and deliberately: the three spaces are
        #   pairwise disjoint by construction.
        # REMAINS TRUE, separated out and STILL ASSERTED — the residual this row was written to
        #   exhibit is CLOSED, and closed further than W4b closed it. The residual was "a
        #   derived identity is not an INTEGER and the port needs one". Under 1.18.0 the derived
        #   identity IS an integer: `formal_name` returns one and `render_ino` is the identity
        #   map on integers, so identity and rendering are ONE VALUE and there is no conversion
        #   left to fail. The band assertion is kept but moved to the band the value is actually
        #   in — asserted as a MEMBERSHIP with both edges, not as a floor, so it reds if a
        #   formal name ever drifts into the digest space.
        # THE SILENT-ZERO CLAUSE IS KEPT UNCHANGED: `_int` on a non-number still refuses.
        self.assertEqual(node.identity, custody.formal_name(
            self.store.by_action("FILE-MKDIR")[-1]["seq"]))
        self.assertIsInstance(node.ino, int)
        self.assertEqual(node.ino, node.identity,
                         "a formal name is its own rendering — there is no lookback")
        self.assertGreaterEqual(node.ino, custody.SEQ_FLOOR)
        self.assertLess(node.ino, custody.RENDER_FLOOR,
                        "a formal name rendered into the digest space would stop being "
                        "distinguishable from a rendered path identity")
        self.assertEqual("%s\t%s\t%d" % ("p", "d", node.ino), "p\td\t%d" % node.ino)
        with self.assertRaises(custody.UnparseableRecordValue):
            custody._int("/p")   # the shape the residual was about: a PATH is still unservable

    def test_the_STAMPED_path_still_serves_integers_so_W4b_is_the_only_thing_blocked(self):
        """The stamp is still in the port until W4b removes it, and under the stamp nothing
        about the served view moved."""
        self.assertEqual(self.port.handle(
            {"id": "1", "op": "FILE-MKDIR", "class": "DECISION",
             "uid": "1000", "gid": "1000", "pid": "42", "path": "/s"}, b"")[0], 0)
        node = self.port.state.lookup("/s")
        # DOCUMENTED FLIP, EP-28C W4b (2026-08-03): the row's name says "W4b is the only
        # thing blocked" and W4b is this pass, so the pin expires here. The port no longer
        # stamps — the founding derives the identity — and the served view did not move: the
        # number is still an integer, still unique per path, and still what `%d` formats.
        # [EP-28T, 2026-08-08 — `AppendNothing` PER ROW, third writing of this clause.]
        # ASSERTED (2026-08-03): the port no longer stamps and the FOUNDING derived the
        #   identity, which under 1.14.0-1.17.0 meant the path `/s`.
        # SUPERSEDED (2026-08-08, EP-28S): the founding derives nothing into the payload at all;
        #   the FOLD derives the identity from the act's own coordinate.
        # REMAINS TRUE, separated out and STILL ASSERTED, and it is the row's name: NOTHING
        #   ABOUT THE SERVED VIEW MOVED. The number is still an integer, still unique per act,
        #   and still what `%d` formats — driven below. Only WHERE the identity comes from has
        #   changed, and that is asserted against the record rather than against a literal, so
        #   this clause stops being rewritten on every move of the source.
        self.assertEqual(node.identity, custody.formal_name(
            self.store.by_action("FILE-MKDIR")[-1]["seq"]),
            "the stamp is gone; the act's own coordinate derived this")
        self.assertIsInstance(node.ino, int)
        self.assertEqual("%s\t%s\t%d" % ("s", "d", node.ino), "s\td\t%d" % node.ino)


# =================================================================================================
# T-DIFF-IS-THE-CHANGE · T-VERSION-MOVES · T-DEGENERATE-IDENTICAL
# =================================================================================================

class TestTheDiffIsTheChange(unittest.TestCase):
    """The founding diff equals the declared change list EXACTLY, set-diffed both directions
    against the pack at the BEFORE commit. A founding pass whose diff is not enumerable is a
    founding pass nobody can review."""

    def setUp(self):
        self.before = pack_ops(pack_at(EP28I_BEFORE_COMMIT))
        self.after = pack_ops(pack_at(EP28I_AFTER_COMMIT))   # DOCUMENTED FLIP (EP-28K): era-pinned

    def test_no_op_was_added_or_removed(self):
        self.assertEqual(set(self.before), set(self.after))
        self.assertEqual(len(self.after), DECLARED_POPULATION)

    def test_exactly_the_enumerated_definitions_changed_both_directions(self):
        moved = {n for n in self.after if self.after[n] != self.before[n]}
        self.assertEqual(moved - CHANGED_DEFINITIONS, set(),
                         "a definition changed that this pass did not declare")
        self.assertEqual(CHANGED_DEFINITIONS - moved, set(),
                         "a declared change did not land")

    def test_the_only_key_that_changed_is_mints_except_for_the_two_gaining_a_derivation(self):
        """Field-level exactness: everything else in every changed definition is untouched."""
        for name in CHANGED_DEFINITIONS:
            b, a = dict(self.before[name]), dict(self.after[name])
            self.assertNotIn("mints", b)
            self.assertEqual(a.pop("mints"), ENUMERATED_MINTERS[name])
            if name in GAINED_INODE_DEFAULT:
                self.assertNotIn("inode", b.get("param_defaults") or {})
                self.assertEqual(a["param_defaults"].pop("inode"), "$path")
                self.assertEqual(a["param_defaults"], b.get("param_defaults") or {}, name)
                if "param_defaults" not in b:
                    del a["param_defaults"]      # FILE-SYMLINK had no block at all
            self.assertEqual(a, b, name)

    def test_the_pack_body_outside_the_op_definitions_moved_only_where_declared(self):
        """The version string and its description paragraph are the pass's other two edits
        and are DECLARED rather than left to be noticed: the pack's own convention is that a
        bump prepends its paragraph, and a version whose description does not name it would
        break the convention every earlier bump established."""
        before_pack, after_pack = pack_at(EP28I_BEFORE_COMMIT), pack_at(EP28I_AFTER_COMMIT)
        self.assertEqual(before_pack["founding_version"], EP28I_BEFORE_VERSION)
        self.assertEqual(after_pack["founding_version"], EP28I_AFTER_VERSION)
        self.assertEqual(before_pack["mother_space"], after_pack["mother_space"])
        self.assertIn("v" + EP28I_AFTER_VERSION, after_pack["description"])
        self.assertIn("v" + EP28I_BEFORE_VERSION, after_pack["description"],
                      "the description GROWS; an earlier version's paragraph is never dropped")
        self.assertTrue(after_pack["description"].endswith(
            before_pack["description"][-200:]),
            "the new paragraph is PREPENDED and the old text is carried byte-identical")


class TestTheVersionMoves(unittest.TestCase):
    """T-VERSION-MOVES. MINOR, ruled: a new REFUSAL is law-surface even when no existing byte
    breaks. J9's uniqueness guard — the same string may never name two distinct foundings —
    has an instrument already, `tests/test_founding_is_logged.py`, which pins the pack's
    sha256 to an entry naming the LIVE version; it is CITED here rather than rebuilt.

    [DOCUMENTED FLIP, EP-28K: era-pinned, and the class is above at EP28I_AFTER_COMMIT. These rows
    asked the LIVE pack what version it is, so they answered about whatever founding happens
    to be shipping rather than about the move this pass made. What EP-28I did is a fact about
    two commits and it does not change when a later pass lawfully moves the founding again.]"""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28i-era-")
        self.era = pack_at(EP28I_AFTER_COMMIT)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_the_pack_reads_1_14_0(self):
        self.assertEqual(pack_at(EP28I_BEFORE_COMMIT)["founding_version"], EP28I_BEFORE_VERSION)
        self.assertEqual(self.era["founding_version"], EP28I_AFTER_VERSION)

    def test_the_record_the_installer_stamped_carries_the_same_string(self):
        """Founded from the ERA pack, so the stamp asserted is the one THIS pass produced.
        The era-pinning idiom is `tests/test_ep14.py`'s: the module-global reader is repointed
        for the call and restored, and the installer's own frozen signature is untouched."""
        saved = install_module.load_pack
        install_module.load_pack = lambda path=None: self.era
        try:
            store, _gate, _views, _blobs, _subs = build_full_kernel(
                os.path.join(self.dir, "record.jsonl"), os.path.join(self.dir, "blobs"),
                os.path.join(self.dir, "vault"))
        finally:
            install_module.load_pack = saved
        found = store.by_action("FOUND-STORE")[0]
        self.assertEqual((found.get("payload") or {}).get("founding_version"), EP28I_AFTER_VERSION)

    def test_the_J9_instrument_is_live_and_binds_whatever_pack_ships(self):
        """J9's standing property is not about 1.14.0: it is that the founding ON DISK, at
        whatever version, is named with its own sha256 in one log entry. Asserting the live
        version here made a standing guard into a pin on one pass's number."""
        from test_founding_is_logged import audit, entries_naming, pack_facts
        a = audit()
        self.assertTrue(a["logged"],
                        "the founding on disk is unattested: no single log entry names its "
                        "version with its own pack sha256")
        self.assertEqual(a["version"], pack_facts()["version"])
        self.assertEqual(entries_naming("## nothing here\n", a["version"], a["sha256"]), [],
                         "non-vacuity: the instrument answers NO for a log that names neither")


class TestDegenerateIdentical(_Live):
    """T-DEGENERATE-IDENTICAL. The port still stamps until EP-28C W4b removes it, so this law
    had to be compatible with the stamp PRESENT — if a supplied inode were displaced by the
    new default, W4b's ordering would break in the other direction."""

    def test_a_supplied_inode_is_never_displaced_by_the_new_default(self):
        """[EP-28T, 2026-08-08 — `AppendNothing` PER ROW, and this row's claim is REVERSED
        rather than weakened, which is why it gets its own paragraph.]

        ASSERTED (2026-08-03): a caller-supplied `inode` survives into the record — the new
        class-wide `param_defaults {"inode": "$path"}` must not displace it, or EP-28C W4b's
        ordering would break in the other direction (the port still stamped at that time).
        SUPERSEDED (2026-08-08, EP-28S): the three minting ops dropped the `inode` PARAMETER and
        dropped `inode` from `payload_from`, so a supplied value is now DROPPED rather than
        preserved. The precondition that made the old claim necessary is gone with it: the port
        stopped stamping at W4b, so there is no longer a caller whose value must survive.
        REMAINS TRUE, and it is the same underlying property read the other way round: WHAT THE
        RECORD SAYS ABOUT IDENTITY IS NOT UP TO THE CALLER. The old form protected a caller's
        value from the law; the new form protects the law from a caller's value. Both are the
        one claim that the identity source is DECLARED and not negotiated, and this row now
        drives the direction the founding actually takes.
        AND THE DIVERGENCE IS KEPT REAL: 4242 cannot coincide with a formal name, because 4242
        is below `SEQ_FLOOR` and every formal name is at or above it. The two candidate values
        cannot agree, so a pass here is evidence rather than a coincidence."""
        self.assertLess(4242, custody.SEQ_FLOOR,
                        "the divergence value must be unreachable as a formal name")
        for op, path, extra in (("FILE-CREATE", "/f", {}), ("FILE-MKDIR", "/d", {}),
                                ("FILE-SYMLINK", "/l", {"target": "/f"})):
            params = {"path": path, "inode": 4242, "provenance": PROV}
            params.update(extra)
            e = self.gate.execute(op, OWNER, params)
            self.assertIsNone((self.store.by_action(op)[-1]["payload"]).get("inode"), op)
            self.assertEqual(custody.fold(self.store.all()).lookup(path).identity,
                             custody.formal_name(e["seq"]), op)

    def test_the_declaration_is_INERT_at_run_time_it_is_read_only_at_definition_time(self):
        """`mints` is law-data the DOORS read. The interpreter never looks at it, so no
        recorded payload can differ because of it."""
        src = open(os.path.join(REPO, "src", "kernel", "opdefs.py"), encoding="utf-8").read()
        body = src.split("def _interpreter(", 1)[1].split("\ndef ", 1)[0]
        self.assertNotIn('"mints"', body)
        self.assertNotIn("MINTS", body)


if __name__ == "__main__":
    unittest.main()
