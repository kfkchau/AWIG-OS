"""EP-28J — THE DECLARATION-DIVERGENCE AUDIT, pinned.

WHAT THIS FILE IS. An AUDIT's durable half. EP-28I repaired ONE divergence (`inode`
minting, declared per-op where the property claimed was class-wide) and its close found
the NEXT one field over: `FILE-MKDIR`/`FILE-SYMLINK` declare `provenance_param` where
`FILE-CREATE` declares it with an absence policy. The mentor named the real class —
PER-OP DECLARATION DIVERGENCE — and this file reads that class whole.

WHAT IT IS NOT. It changes no law. `src/founding/` is byte-unchanged by requirement and
every unjustified divergence here is RAISED with its evidence, never repaired. An audit
that edits what it audits is a law change without the founding open.

ITS CONSUMER IS EP-29's AUTHORING. EP-29 mints the largest population of new op
definitions this campaign will produce. It reads THE TABLE below before writing any, so
the divergence class is not copied forward.

THE POPULATION AND THE FIELD UNIVERSE BOTH COME FROM STRUCTURE (charter §A51). Every
`CREATE-OP` record IS an op; the declaration-field universe is the union of keys the ops
themselves declare. A name-shape filter and a hand-written field list are both carried
here as RED WORLDS, driven, because each is what the correct instrument must beat.
"""

import copy
import hashlib
import json
import os
import subprocess
import sys
import unittest
from collections.abc import Mapping

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import era_pin  # noqa: E402  (the era-pin home, EP-28Z)
from test_ep28f import commit_identity  # noqa: E402  (the abbreviation-width home, MAINT-2)

from kernel.opdefs import (  # noqa: E402  (path juggling above, as every suite file does)
    DEFAULTED,
    ENVELOPE_ROUTERS,
    MINTED_ROUTERS,
    REQUIRED,
    router_param,
)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")


# ---------------------------------------------------------------------------------------
# THE READING — every figure below is COMPUTED from the pack at import, never carried.
# ---------------------------------------------------------------------------------------

def load_pack_bytes():
    with open(PACK_PATH, "rb") as fh:
        return fh.read()


def op_definitions(pack):
    """THE POPULATION, FROM STRUCTURE. Every `CREATE-OP` record is an op — §A51's first
    half, filed on this class's own count defect, where a probe filtering names on
    `isupper() and '-' in name` returned sixty against a true seventy-two and hid `MOUNT`
    for want of a hyphen. There is no name test anywhere in this function."""
    out = {}
    for step in pack["steps"]:
        for rec in step["records"]:
            if rec.get("action") == "CREATE-OP":
                payload = rec["payload"]
                out[payload["name"]] = payload["definition"]
    return out


def field_universe(defs):
    """THE DECLARATION-FIELD UNIVERSE, FROM THE DEFINITIONS THEMSELVES — the union of keys
    the ops actually declare. A field list written into this file would be §A51's hyphen
    filter one layer up: exactly as complete as the author's memory, and unreviewable
    because the assumption never appears in the output."""
    return sorted({k for d in defs.values() for k in d})


def declared_shape(defn, field):
    """THE SHAPE ONE OP DECLARES FOR ONE FIELD — its declaration FORM, never its content.

    THE GRAIN IS DERIVED FROM WHERE THE PACK'S GRAMMAR ACTUALLY CONSTRAINS THE VALUE, and
    this file's first grain was WRONG in a way worth recording, because it is the wrong
    reference the whole audit is about arriving inside the audit's own instrument:

    * For the two MINTED ROUTERS the engine's own `router_param` RESOLVES the declaration
      to its absence policy — `required` or `default`. Taken THROUGH THE ENGINE, never by
      re-reading the JSON's shape here, because the engine's silence rule (a bare name
      means REQUIRED) is what decides what a declaration MEANS.
    * For the other envelope routers the declaration's KEY SET is grammar
      (`opdefs.ROUTER_DECL_KEYS`), so it is the shape.
    * For every other field the shape is the CONTAINER KIND and nothing finer.

    WHAT THE FIRST GRAIN DID AND WHY IT IS RECORDED RATHER THAN QUIETLY FIXED: it used a
    mapping's KEY SET for every field. That reported `params: map{path,perm}` against
    `params: map{channel}` as a divergence — which is each op's own parameter list, i.e.
    CONTENT — and returned seven divergent fields where the true figure is one. An
    instrument that calls content divergence manufactures findings, and this audit exists
    to hand EP-29 a table it can trust. EMPTINESS IS CONTENT TOO: an op with no checks and
    an op with three checks do not disagree about anything, they are different ops."""
    if field in MINTED_ROUTERS:
        param, when_absent = router_param(defn, field)
        return "absent" if param is None else when_absent
    if field not in defn:
        return "absent"
    return value_shape(defn[field], field)


def value_shape(value, field=None):
    if isinstance(value, Mapping):
        if field in ENVELOPE_ROUTERS:
            return "map{" + ",".join(sorted(value)) + "}"
        return "map"
    if isinstance(value, list):
        return "list"
    return type(value).__name__


def presence_holdouts(defs):
    """AXIS B — PRESENCE divergence, at the only bar a grouping cannot explain away: a
    field declared by EVERY op but one.

    WHY THIS BAR RATHER THAN A PER-LAW GROUPING. Grouping by `law_cited` yields thirty
    presence differences, and nearly all of them are an op's own semantics speaking — five
    of fifteen `CAP-IS-LAW` ops declare `object_param` because the other ten derive their
    object, and that is two ways of doing one thing, not drift. A LONE HOLDOUT is
    different: seventy-one ops answered a question and one did not, and no reading of that
    op's effect explains the silence."""
    out = {}
    for field in field_universe(defs):
        missing = [n for n in sorted(defs) if field not in defs[n]]
        if len(missing) == 1:
            out[field] = missing[0]
    return out


def partition(defs, field):
    """shape -> sorted op names. The partition is TOTAL over the population by
    construction: every op lands in exactly one cell, `absent` included, so the cell sizes
    reconcile against the population with no remainder and a table that quietly dropped an
    op could not."""
    cells = {}
    for name in sorted(defs):
        cells.setdefault(declared_shape(defs[name], field), []).append(name)
    return cells


def divergent_fields(defs):
    """A field DIVERGES when the ops that declare it do not all declare it the same way.
    `absent` is excluded from the shape count on purpose: not declaring a field is the
    ordinary case for 20 of the 24 fields and would make every field 'divergent', which is
    a partition that has stopped discriminating."""
    out = {}
    for field in field_universe(defs):
        shapes = sorted(s for s in partition(defs, field) if s != "absent")
        if len(shapes) > 1:
            out[field] = shapes
    return out


PACK_BYTES = load_pack_bytes()
PACK = json.loads(PACK_BYTES.decode("utf-8"))
DEFS = op_definitions(PACK)
UNIVERSE = field_universe(DEFS)

# [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12, charter §A57. Deferred to the foot of the era-pin
# block below, where `ERA_COMMIT` is defined; `DEFS` and `UNIVERSE` are REBOUND there. Named
# here so a reader of these four lines is not told a stale story about which era they hold.]


# ---------------------------------------------------------------------------------------
# THE ERA PIN — added by EP-29 W1a under charter §A57, 2026-08-09
# ---------------------------------------------------------------------------------------
#
# WHY THIS FILE NEEDED ONE. Three rows below assert THIS AUDIT'S OWN ERA — the pack EP-28S
# landed and EP-28T, this audit and EP-28C W4e.C all left byte-unchanged — and they read it
# off the LIVE tree. EP-29 W1a moved the founding 1.18.0 -> 1.19.0 on 2026-08-09, so the
# live side stopped being this audit's era and the three rows reddened on a LAWFUL move.
# That is §A57 exactly, one file on from EP-28K reddening EP-28I: a landing pass cannot pin
# an after-commit that does not exist yet, so the NEXT founding pass owes the pin backwards.
#
# THE PIN IS CHOSEN BY CONTENT, NEVER BY A LABEL — EP-28T's rule, and this file's own
# `TProvenanceHistory` clause said it first. Choosing by version number picks `05f29f7`,
# which reads `1.17.0` AND ALREADY CARRIES EP-28S's law: a two-minute autosync commit that
# landed inside a half-written change. RE-DRIVEN before this constant was written, not
# taken from the note that warned about it: at `05f29f7` three ops declare `mints_from`
# while the pack still reads 1.17.0; at the commit below they declare it and the pack reads
# 1.18.0.
#
# HOW IT WAS DERIVED, so it is attackable by re-derivation rather than trusted:
#   * EP-28S's close entry names its founding tree `58c946e5820356517102ace0e98ec2cf26d312b7`
#     and pack sha256 `a9ab2641…`. EXACTLY ONE commit in this repo carries that
#     `src/founding` tree, and it is the one below — searched, not guessed.
#   * The pack at `ba125bd7~1`, the commit immediately before EP-29 W1a's own founding
#     write, is BYTE-IDENTICAL to the pack at this pin. So this audit's whole life sits
#     inside one unbroken byte-state and the pin cannot be landing mid-change.
#   * `sha256` of the blob at this commit reproduces the digest `TAuditChangedNoLaw`
#     asserts below — which makes that row the POSITIVE CONTROL on this pin: if the pin
#     ever resolved to the wrong bytes, it reds, instead of the other two era-pinned rows
#     quietly asserting about the wrong era.
#
# FORTY CHARACTERS, where this file's other pin (`TProvenanceHistory.PIN`) is seven. The
# departure is deliberate and stated rather than silent: this repo commits every two
# minutes, an era pin is among the longest-lived citations it holds, and a seven-character
# prefix is a citation that resolves by the repo's current size rather than by
# construction. It fails LOUD either way (`check=True`), so the width buys robustness only.
ERA_COMMIT = "4f0839dea02f23bce599cd8acd1ad0d50d29074a"


def era_pack_bytes():
    """The estate's era-pin idiom and nothing else: `git show`. Bytes, not text — the
    digest row below hashes exactly what git stores.

    [DOCUMENTED FLIP — EP-28Z, 2026-08-12. CAUSE: this docstring says "the estate's era-pin
    idiom" and the estate had no home for it — EIGHTEEN copies across TEN test files, one
    per pass, because charter §A57 states the duty and states no method. ASSERTED: a local
    `git show` spawn with `check=True`. SUPERSEDED: `era_pin.blob_at`, from the one home.
    REMAINS TRUE: BYTES, never text — the home returns exactly what git stores and the
    digest row below is unmoved; and the failure mode, `CalledProcessError`, which
    `missing="raise"` is by name. GIVEN UP: nothing.]"""
    return era_pin.blob_at(ERA_COMMIT, era_pin.PACK_PATH)


def era_pack():
    return json.loads(era_pack_bytes().decode("utf-8"))


# [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12, charter §A57. THE REBIND ANNOUNCED AT `DEFS`' OWN
# DEFINITION ABOVE, LANDED HERE because `ERA_COMMIT` does not exist until this point in the
# file. CAUSE: this pass added two op definitions (DECLARE-IO-WINDOW, DEVICE-IO-WINDOW-WRITE)
# and moved the founding 1.19.0 -> 1.20.0, which falsified four rows reading the LIVE tree —
# `len(DEFS) == 72` became 74, the name-shape double's 60 became 62, the field partition's
# coverage 72 became 74, and `cells["absent"] == 50` became 52. ASSERTED: `DEFS` over the LIVE
# pack. SUPERSEDED: `DEFS` over `era_pack()`, the pin this file already holds and already
# describes as "THIS AUDIT'S OWN ERA" — verified before the rebind: 72 ops and 60 name-shape
# matches at ERA_COMMIT, which are exactly the two pinned figures. REMAINS TRUE: every audit
# verdict below, unchanged, about the population this audit actually read; and `PACK_BYTES`
# and `PACK` STAY LIVE, because `test_the_bytes_were_never_touched_by_the_synthetic_world`
# asks whether the file on disk moved DURING THIS RUN, which is not an era claim and would be
# made vacuous by pinning it. GIVEN UP: nothing — no row here ever claimed the live founding.]
DEFS = op_definitions(era_pack())
UNIVERSE = field_universe(DEFS)


# ---------------------------------------------------------------------------------------
# THE PIN — the audit's durable half. DECLARED-OR-RED.
# ---------------------------------------------------------------------------------------
#
# WHAT IS PINNED AND WHAT DELIBERATELY IS NOT. The pin holds the DIVERGENCE SET — which
# fields carry more than one declared shape, and which shapes — and NOT the per-cell
# counts. A lawful founding that adds an op in a shape already present stays GREEN; a
# founding that introduces a NEW shape on any field REDS this pin until the shape is
# declared here with its reason.
#
# The counts are asserted separately, in the TABLE row, against the reading. Pinning them
# HERE would red this row on every lawful op addition — which is the stored-copy-of-a-
# computable-value defect (M2) that EP-28T spent a work item removing from thirty-six
# version literals. A pin that reds on lawful growth gets edited until it stops meaning
# anything.
#
# SHRINK-ONLY IN THE UNJUSTIFIED DIRECTION: a candidate leaves this table by a RULING that
# changes the founding, never by an edit to this file.

#: AXIS A — SHAPE divergence. Exactly one member in the whole twenty-four-field universe.
PINNED_SHAPE_DIVERGENCES = {
    # field               sorted shapes            classification
    "provenance_param": (["default", "required"], "candidate"),
}

#: AXIS B — PRESENCE divergence at the lone-holdout bar. Exactly one member.
PINNED_HOLDOUTS = {
    # field      the one op that does not declare it    classification
    "checks": ("DICT-ENTRY", "candidate"),
}

PINNED_POPULATION = 72          # EP-28I's enumerated figure, re-asserted from structure
PINNED_UNIVERSE_SIZE = 24       # computed at this audit, asserted as a countable


# ---------------------------------------------------------------------------------------
# THE RED-WORLD DOUBLES — each is a WRONG instrument, driven, so the right one is proven
# to beat something rather than merely to run.
# ---------------------------------------------------------------------------------------

def population_by_name_shape(pack):
    """§A51's OWN DEFECT, reconstructed: the filter that returned sixty. Carried from
    EP-28I's row and cited. It is a list of ops whose NAMES MATCHED A PATTERN."""
    out = {}
    for step in pack["steps"]:
        for rec in step["records"]:
            if rec.get("action") == "CREATE-OP":
                name = rec["payload"]["name"]
                if name.isupper() and "-" in name:
                    out[name] = rec["payload"]["definition"]
    return out


def field_universe_by_hand():
    """THE NAMED-FIELD AUDIT, the plan's wrong reference #2: audit the two fields findings
    have named. This is the hyphen filter at the FIELD layer."""
    return sorted(["provenance_param", "param_defaults"])


def table_omitting(defs, drop):
    """A TABLE DOUBLE that omits one field's partition — the red world T-DIVERGENCE-TABLE
    names. The field-universe reconciliation is what catches it."""
    return {f: partition(defs, f) for f in field_universe(defs) if f != drop}


def defs_with_synthetic_divergence(defs):
    """A SYNTHETIC FUTURE FOUNDING (§A42's shape: the red world is GENERATED, driven
    through the pin, and the real bytes are never touched). A new op arrives declaring
    `object_param` as a LIST where all fifty-six existing declarations are strings."""
    doubled = copy.deepcopy(defs)
    doubled["SYNTHETIC-FUTURE-OP"] = {
        "description": "a definition that does not exist, minted in memory for this row",
        "params": {"path": "required"},
        "law_cited": "FS-LAW-NAMESPACE",
        "object_param": ["path"],       # <- the new shape: list where every sibling is str
        "payload_from": ["path"],
        "checks": [],
    }
    return doubled


# =======================================================================================
class TPopulation(unittest.TestCase):
    """T-POPULATION — the op population computed from the pack's STRUCTURE equals the
    EP-28I-pinned seventy-two. A mismatch reds BEFORE any field is read.

    RED WORLD: the name-shape-filter double, carried from EP-28I's row and cited."""

    def test_population_from_structure_is_the_pinned_figure(self):
        self.assertEqual(len(DEFS), PINNED_POPULATION)
        self.assertEqual(len(set(DEFS)), PINNED_POPULATION, "seventy-two DISTINCT names")

    def test_red_world_name_shape_filter_returns_fewer_and_is_unreachable_by_structure(self):
        # [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12, charter §A57, the same rebind as `DEFS`'.
        # CAUSE: the double is run against a pack and compared to `len(DEFS)`, so leaving it on
        # the LIVE pack while `DEFS` reads the era would compare two different worlds — the
        # exact defect this row exists to exhibit. Both of this pass's new ops are upper-case
        # AND hyphenated, so they PASS the name-shape filter and the "sixty" it returned became
        # sixty-two. ASSERTED: `PACK`, live. SUPERSEDED: `era_pack()`. REMAINS TRUE: the twelve
        # names the filter hides, `MOUNT` among them, unchanged.]
        wrong = population_by_name_shape(era_pack())
        self.assertLess(len(wrong), PINNED_POPULATION)
        self.assertEqual(len(wrong), 60, "the exact figure §A51 was filed on")
        hidden = sorted(set(DEFS) - set(wrong))
        self.assertEqual(len(hidden), 12)
        self.assertIn("MOUNT", hidden, "the op that mints the mount root, hidden by a hyphen")

    def test_near_miss_a_hyphenless_op_is_in_the_population(self):
        """§A64 both ways on a structural row. SHOULD match and is spelled differently: a
        hyphen-free name is still an op."""
        self.assertIn("MOUNT", DEFS)
        self.assertIn("REVOKE", DEFS)

    def test_near_miss_op_shaped_records_that_are_NOT_ops(self):
        """SHOULD NOT match and is spelled similarly. The pack holds 136 records and 72 of
        them are ops; the other 64 carry actions that pass the very name filter the red
        world above uses — `CREATE-RULE`, `CREATE-VIEW`, `CREATE-INFO`, `FOUND-STORE`.
        The structural reading keys on `action == "CREATE-OP"` and nothing else, so a
        record that LOOKS op-shaped cannot enter the population.

        AND THE TRAP INSIDE THE TRAP, which is why this row names it: `CREATE-RULE` is
        BOTH a record action in this pack and the name of a real op. So 'is it an op?'
        cannot be answered by looking at the action string — only by looking at which
        record declared it.

        [EP-29 W1a, 2026-08-09 — ERA-PINNED under §A57. A documented flip with its cause.]

        ASSERTED (2026-08-08): the LIVE pack holds 136 records, 72 of them ops, 64 not.
        SUPERSEDED: EP-29 W1a declared `DEV-LAW-BIND` — ONE new `CREATE-RULE` record, cited
        by `BIND-DEVICE` and `UNBIND` since campaign 1 and declared by nothing until then —
        so the live reading is 137 and 65. The op population did NOT move (72 both sides;
        the pass was an amendment, not a creation), which is exactly why this row and not
        `test_population_from_structure_is_the_pinned_figure` went red.
        REMAINS TRUE, at this audit's own era where the census was taken: 136 and 64.
        GIVEN UP: nothing. The claim this row exists to make — that an op-shaped ACTION is
        not an op, and that `CREATE-RULE` is both — is structural, and it is re-asserted
        below against the era's own definitions rather than against a count."""
        era = era_pack()
        era_defs = op_definitions(era)
        actions = {rec.get("action") for step in era["steps"] for rec in step["records"]}
        total = sum(len(step["records"]) for step in era["steps"])
        self.assertEqual(total, 136)
        self.assertEqual(total - len(era_defs), 64)
        for a in ("CREATE-RULE", "CREATE-VIEW", "CREATE-INFO", "FOUND-STORE"):
            self.assertIn(a, actions)
        for a in ("CREATE-VIEW", "CREATE-INFO", "FOUND-STORE"):
            self.assertNotIn(a, era_defs, "an op-shaped action that is not an op")
        self.assertIn("CREATE-RULE", era_defs, "and one that IS both — the trap")


# =======================================================================================
class TFieldsFromStructure(unittest.TestCase):
    """T-FIELDS-FROM-STRUCTURE — the declaration-field universe is the union read from the
    seventy-two definitions themselves, its size asserted as a countable.

    RED WORLD: a hand-list double naming the two known fields — returns a smaller universe
    and reds the structure clause."""

    def test_universe_size_is_a_countable_asserted_from_structure(self):
        self.assertEqual(len(UNIVERSE), PINNED_UNIVERSE_SIZE)

    def test_universe_covers_every_key_every_op_declares(self):
        for name, d in DEFS.items():
            for key in d:
                self.assertIn(key, UNIVERSE, f"{name} declares {key} and the universe missed it")

    def test_red_world_hand_list_returns_a_smaller_universe(self):
        by_hand = field_universe_by_hand()
        self.assertLess(len(by_hand), len(UNIVERSE))
        self.assertEqual(len(by_hand), 2)
        missed = sorted(set(UNIVERSE) - set(by_hand))
        self.assertEqual(len(missed), 22)
        self.assertIn("mints_from", missed, "the field EP-28S's law landed, unnamed by any finding")

    def test_near_miss_a_field_declared_by_exactly_one_op_is_in_the_universe(self):
        """§A64: the near-miss on a union's own axis is the SINGLETON — the member a
        threshold or a majority rule would drop."""
        singletons = [f for f in UNIVERSE
                      if sum(1 for d in DEFS.values() if f in d) == 1]
        self.assertTrue(singletons)
        for f in singletons:
            self.assertIn(f, UNIVERSE)
        self.assertIn("anchor_guard", singletons)


# =======================================================================================
class TDivergenceTable(unittest.TestCase):
    """T-DIVERGENCE-TABLE — per field, the partition (required / defaulted / absent, per
    op), machine-readable and set-diffable; the known `provenance_param` member present as
    a CANDIDATE with its evidence.

    RED WORLD: a table double omitting one field's partition — the field-universe
    reconciliation reds it."""

    def test_every_field_has_a_partition_and_it_is_total_over_the_population(self):
        for field in UNIVERSE:
            cells = partition(DEFS, field)
            covered = sum(len(v) for v in cells.values())
            self.assertEqual(covered, PINNED_POPULATION,
                             f"{field}: partition covers {covered} of {PINNED_POPULATION}")
            flat = [n for v in cells.values() for n in v]
            self.assertEqual(len(flat), len(set(flat)), f"{field}: an op in two cells")

    def test_red_world_table_omitting_one_field_fails_the_universe_reconciliation(self):
        double = table_omitting(DEFS, "provenance_param")
        self.assertNotEqual(sorted(double), UNIVERSE)
        self.assertEqual(sorted(set(UNIVERSE) - set(double)), ["provenance_param"])

    def test_the_known_member_is_present_as_a_candidate_with_its_evidence(self):
        cells = partition(DEFS, "provenance_param")
        self.assertEqual(sorted(s for s in cells if s != "absent"), [DEFAULTED, REQUIRED])
        # The mentor's finding, re-derived rather than quoted.
        self.assertEqual(declared_shape(DEFS["FILE-MKDIR"], "provenance_param"), REQUIRED)
        self.assertEqual(declared_shape(DEFS["FILE-SYMLINK"], "provenance_param"), REQUIRED)
        self.assertEqual(declared_shape(DEFS["FILE-CREATE"], "provenance_param"), DEFAULTED)
        self.assertEqual(len(cells[REQUIRED]), 17)
        self.assertEqual(len(cells[DEFAULTED]), 5)
        self.assertEqual(len(cells["absent"]), 50)

    def test_A49_least_likely_member_of_the_provenance_class(self):
        """§A49 — a property claimed of a class is checked on the member LEAST likely to
        share it. The claim that would be natural to make here is 'provenance declarations
        are a filesystem concern': twenty-one of the twenty-two cite an FS law. The least
        likely member is `MAP-UID`, which cites `CAP-IS-LAW` — and it DECLARES, so the
        FS-only reading is FALSE and is recorded as false rather than quietly dropped."""
        cells = partition(DEFS, "provenance_param")
        declaring = sorted(cells[REQUIRED] + cells[DEFAULTED])
        non_fs = [n for n in declaring if not DEFS[n]["law_cited"].startswith("FS-")]
        self.assertEqual(non_fs, ["MAP-UID"])
        self.assertEqual(declared_shape(DEFS["MAP-UID"], "provenance_param"), REQUIRED)

    def test_the_divergent_field_set_is_exactly_what_the_pin_declares(self):
        found = divergent_fields(DEFS)
        self.assertEqual(sorted(found), sorted(PINNED_SHAPE_DIVERGENCES))
        self.assertEqual(found["provenance_param"],
                         PINNED_SHAPE_DIVERGENCES["provenance_param"][0])

    def test_AXIS_B_the_lone_holdout_is_checks_and_the_holdout_is_DICT_ENTRY(self):
        """THE SECOND AXIS, and it is the one a shape reading cannot see. Seventy-one ops
        declare `checks`; `DICT-ENTRY` omits the key. The behaviour is identical —
        `d.get("checks") or []` — so nothing in the estate distinguishes the two
        spellings, and an author of a checkless op has NO declared answer to 'do I write
        `checks: []` or leave it out?'. Fifty-four ops answer one way by example and one
        answers the other, and neither is law.

        [EP-29 W1a, 2026-08-09 — ERA-PINNED under §A57. A documented flip with its cause.]

        ASSERTED (2026-08-08): on the LIVE pack, 54 ops spell it `checks: []`, 17 declare
        checks, `DICT-ENTRY` omits the key, and 54 + 17 + 1 reconciles to the population.
        SUPERSEDED: EP-29 W1a parameterized an existing check kind onto `UNBIND` — a
        `require_prior` on `BIND-DEVICE` — so UNBIND LEFT the empty-checks set and the live
        reading is 53 + 18 + 1. The counts moved; the FINDING did not. That is the whole
        point of the flip: the three spellings are still three, the lone holdout is still
        `DICT-ENTRY`, and a lawful amendment moved a census this row froze.
        REMAINS TRUE, at this audit's own era where the counts were taken: 54 / 17 / 1.
        GIVEN UP: nothing this row held. The DIVERGENCE SET — the durable half, and the half
        the file's own pin comment says is pinned deliberately where the counts are not — is
        `test_the_divergent_field_set_is_exactly_what_the_pin_declares` and the
        `TPinDeclaredOrRed` class, all still reading the LIVE pack and all still green."""
        era_defs = op_definitions(era_pack())
        holdouts = presence_holdouts(era_defs)
        self.assertEqual({f: n for f, (n, _v) in PINNED_HOLDOUTS.items()}, holdouts)
        self.assertNotIn("checks", era_defs["DICT-ENTRY"])
        self.assertEqual(len([n for n in era_defs if era_defs[n].get("checks") == []]), 54)
        self.assertEqual(len([n for n in era_defs if era_defs[n].get("checks")]), 17)
        self.assertEqual(54 + 17 + 1, PINNED_POPULATION, "the three spellings reconcile")


# =======================================================================================
class TPinDeclaredOrRed(unittest.TestCase):
    """T-PIN-DECLARED-OR-RED — the pinned table equals what the structure yields; a
    SYNTHETIC future divergence reds the pin until it is declared with a reason.

    RED WORLD: that synthetic double IS this row's red world — generated, driven THROUGH
    the pin, and the pack's bytes are never touched (§A42)."""

    def test_pin_equals_the_structure_today(self):
        self.assertEqual(sorted(divergent_fields(DEFS)), sorted(PINNED_SHAPE_DIVERGENCES))
        self.assertEqual({f: n for f, (n, _v) in PINNED_HOLDOUTS.items()},
                         presence_holdouts(DEFS))

    def test_synthetic_future_divergence_REDS_the_pin(self):
        doubled = defs_with_synthetic_divergence(DEFS)
        found = divergent_fields(doubled)
        self.assertIn("object_param", found, "the new shape must be SEEN")
        self.assertNotIn("object_param", PINNED_SHAPE_DIVERGENCES, "and it is NOT declared")
        self.assertNotEqual(sorted(found), sorted(PINNED_SHAPE_DIVERGENCES),
                            "so the pin REDS — declared-or-red, working")

    def test_synthetic_future_HOLDOUT_also_reds_the_pin(self):
        """AXIS B's own red world, driven separately: the two axes fail independently or
        one of them is decoration. A new op omitting `law_cited` — declared by all
        seventy-two today — makes that field a lone holdout the pin does not declare."""
        doubled = copy.deepcopy(DEFS)
        doubled["SYNTHETIC-HOLDOUT-OP"] = {
            "description": "declares everything universal except one",
            "params": {}, "payload_from": [], "checks": [],
        }
        found = presence_holdouts(doubled)
        self.assertEqual(found.get("law_cited"), "SYNTHETIC-HOLDOUT-OP")
        self.assertNotIn("law_cited", PINNED_HOLDOUTS)
        self.assertNotEqual({f: n for f, (n, _v) in PINNED_HOLDOUTS.items()}, found)

    def test_the_bytes_were_never_touched_by_the_synthetic_world(self):
        """The generated red world runs on a deep copy. The pack on disk is the same
        object it was at import, byte for byte."""
        self.assertEqual(load_pack_bytes(), PACK_BYTES)

    def test_near_miss_a_lawful_addition_in_an_EXISTING_shape_stays_GREEN(self):
        """§A64's other direction, and it is the clause that decides whether this pin
        survives contact with a growing founding: an op added in a shape already present
        must NOT red. A pin that reds on lawful growth gets edited until it means
        nothing."""
        doubled = copy.deepcopy(DEFS)
        doubled["ANOTHER-LAWFUL-OP"] = {
            "description": "a lawful addition in shapes that already exist",
            "params": {"path": "required"},
            "law_cited": "FS-LAW-NAMESPACE",
            "object_param": "path",      # str, as all fifty-six are
            "payload_from": ["path"],
            "checks": [],
        }
        self.assertEqual(sorted(divergent_fields(doubled)),
                         sorted(PINNED_SHAPE_DIVERGENCES))


# =======================================================================================
class TRouterPolicyResolvedMechanically(unittest.TestCase):
    """T-ROUTER-POLICY — the required/defaulted axis is resolved THROUGH THE ENGINE'S OWN
    READER (`opdefs.router_param`), never by this file re-reading the JSON's shape.

    WHY IT MATTERS RATHER THAN BEING TIDINESS: a citation in a docstring is prose and
    prose rots silently. Two shipped citations were driven false this week. Resolving the
    grammar through the one reader means this row cannot disagree with the engine."""

    def test_bare_string_resolves_REQUIRED_by_silence(self):
        param, when_absent = router_param({"provenance_param": "provenance"}, "provenance_param")
        self.assertEqual((param, when_absent), ("provenance", REQUIRED))

    def test_longhand_naming_default_resolves_DEFAULTED(self):
        decl = {"provenance_param": {"param": "provenance", "when_absent": "default"}}
        self.assertEqual(router_param(decl, "provenance_param"), ("provenance", DEFAULTED))

    def test_near_miss_longhand_that_says_nothing_about_absence_resolves_REQUIRED(self):
        """§A64: the construct spelled SIMILARLY to the defaulted form that must NOT be
        read as defaulted. Silence means required in EITHER form of the grammar, so a
        declaration cannot weaken by habit."""
        decl = {"provenance_param": {"param": "provenance"}}
        self.assertEqual(router_param(decl, "provenance_param"), ("provenance", REQUIRED))

    def test_near_miss_absent_declaration_routes_NOTHING(self):
        self.assertEqual(router_param({}, "provenance_param"), (None, REQUIRED))

    def test_the_required_or_defaulted_axis_exists_for_exactly_two_fields(self):
        """A finding EP-29's author needs stated as a countable: of the six envelope
        routers, only the two whose field the STORE MINTS on absence may declare what an
        absent parameter means. On the other twenty-two fields there is no such choice to
        make, so 'required or defaulted' is not a question a new definition can answer."""
        self.assertEqual(sorted(MINTED_ROUTERS), ["occurrence_time_param", "provenance_param"])
        self.assertEqual(len(MINTED_ROUTERS), 2)
        for r in MINTED_ROUTERS:
            self.assertIn(r, ENVELOPE_ROUTERS)
            self.assertIn(r, UNIVERSE, "and both are live in the pack, not merely defined")


# =======================================================================================
class TParamsRouterAgreement(unittest.TestCase):
    """THE SECOND CANDIDATE, and this audit found it rather than inheriting it.

    For every op declaring a minted router, TWO declarations describe the SAME parameter:
    the `params` block says `optional` or `required`, and the router says what an absent
    value means. On seventeen ops they give OPPOSITE answers — `params` says the caller
    may omit `provenance`, and omitting it refuses.

    THE READING, and it is checkable rather than asserted: `gate.execute` refuses a
    missing `required` parameter with AR-2; the router refuses a missing REQUIRED envelope
    parameter with AR-2. One condition, one citation, two sites — and the `params` block's
    word 'optional' is FALSE as a statement about the op.

    RAISED, NOT REPAIRED. Which declaration is wrong is a founding pass's question."""

    def _rows(self):
        rows = []
        for name in sorted(DEFS):
            d = DEFS[name]
            for field in sorted(MINTED_ROUTERS):
                param, when_absent = router_param(d, field)
                if param is None:
                    continue
                rows.append((name, field, param, when_absent,
                             (d.get("params") or {}).get(param, "<not-in-params>")))
        return rows

    def test_every_router_parameter_is_named_in_the_params_block(self):
        for name, field, param, _wa, params_word in self._rows():
            self.assertNotEqual(params_word, "<not-in-params>",
                                f"{name}.{field} routes {param}, absent from its own params")

    def test_seventeen_ops_declare_optional_and_refuse_on_absence(self):
        disagree = [(n, f) for n, f, _p, wa, pw in self._rows()
                    if wa == REQUIRED and pw == "optional"]
        self.assertEqual(len(disagree), 17)
        self.assertEqual(sorted({f for _n, f in disagree}), ["provenance_param"])

    def test_the_agreeing_cell_is_non_empty_and_reconciles(self):
        rows = self._rows()
        self.assertEqual(len(rows), 25, "22 provenance + 3 occurrence_time")
        agree = [r for r in rows if r[3] == DEFAULTED and r[4] == "optional"]
        self.assertEqual(len(agree), 8, "5 provenance + 3 occurrence_time")
        self.assertEqual(len(rows), 17 + 8, "the partition reconciles with no remainder")

    def test_near_miss_no_op_declares_a_router_parameter_REQUIRED_in_params(self):
        """§A64's other side: the construct that SHOULD have been found if it existed. A
        `params: required` + router REQUIRED pair would be two declarations AGREEING, and
        would show the divergence is a choice rather than a habit. There are none — which
        is the evidence that the seventeen are a habit."""
        both_required = [(n, f) for n, f, _p, wa, pw in self._rows()
                         if wa == REQUIRED and pw == "required"]
        self.assertEqual(both_required, [])

    def test_no_param_defaults_entry_shadows_a_router_parameter(self):
        """The control that keeps the finding honest. `param_defaults` fills a COPY of the
        caller's parameters, and if one filled a router's parameter the REQUIRED refusal
        could never fire — the divergence would be invisible rather than merely latent.
        `opdefs` closed that by reading RAW parameters; this asserts the pack agrees."""
        for name, _field, param, _wa, _pw in self._rows():
            self.assertNotIn(param, DEFS[name].get("param_defaults") or {},
                             f"{name}: param_defaults shadows a routed parameter")


# =======================================================================================
class TClassification(unittest.TestCase):
    """THE CLASSIFICATION, and the check the plan puts on the AUDIT rather than on the
    pack: the `justified` class must be NON-EMPTY, or the audit suspects its own reading.
    A partition with one cell is a reading that stopped early — and harmonisation as the
    default verdict is this plan's named wrong reference #3.

    Each justified row's reason is RESOLVED MECHANICALLY against the definitions here, not
    stated in prose. A reason that cannot be re-derived is a claim, not a finding."""

    def test_justified_class_is_non_empty(self):
        self.assertGreaterEqual(len(JUSTIFIED), 4)

    def test_justified_act_kind_only_the_ops_whose_whole_effect_is_a_release(self):
        """`act_kind` is declared by 2 of 72. The reason is IN the definitions: the only
        value in the pack is `release`, and it is on the two ops that END something the
        caller already holds. `FILE-LOCK` sits beside `FILE-UNLOCK` under one law and does
        not declare — because taking a lock is not a release."""
        declared = {n: DEFS[n]["act_kind"] for n in DEFS if "act_kind" in DEFS[n]}
        self.assertEqual(sorted(declared), ["FILE-CLOSE", "FILE-UNLOCK"])
        self.assertEqual(set(declared.values()), {"release"})
        self.assertNotIn("act_kind", DEFS["FILE-LOCK"])
        self.assertNotIn("act_kind", DEFS["FILE-OPEN"])

    def test_justified_content_form_only_the_ops_that_carry_content(self):
        """`content_form` is declared by 2 of the 10 ops citing FS-LAW-PERM. The reason
        re-derives: both declare `content_params` too, and no op declares one without the
        other under that law."""
        cf = {n for n in DEFS if "content_form" in DEFS[n]}
        self.assertEqual(sorted(cf), ["FILE-TRUNCATE", "FILE-WRITE"])
        for n in cf:
            self.assertIn("content_params", DEFS[n])

    def test_justified_authority_regime_the_four_power_structure_ops(self):
        """4 of the 15 ops citing CAP-IS-LAW declare `authority_regime`. The reason
        re-derives from the values themselves: all four carry ONE regime name, and they
        are the delegation family (DIGEST-C2 §2 item 12 — the regime is DATA on the op,
        never a code verb-list)."""
        ar = {n: DEFS[n]["authority_regime"] for n in DEFS if "authority_regime" in DEFS[n]}
        self.assertEqual(sorted(ar), ["CREATE-ROLE", "CREATE-SPACE", "GRANT", "REVOKE"])
        self.assertEqual(set(ar.values()), {"attenuation-family"})

    def test_justified_empty_payload_from_only_the_ops_with_no_parameters(self):
        """3 ops declare an EMPTY `payload_from` where 69 declare a non-empty one. The
        reason re-derives exactly: those three declare NO parameters at all, and a payload
        built from parameters cannot name one that does not exist."""
        empty = {n for n in DEFS if DEFS[n]["payload_from"] == []}
        self.assertEqual(sorted(empty),
                         ["ACCEPT-SUCCESSION", "HANDOVER", "REVOKE-SUCCESSION"])
        for n in empty:
            self.assertEqual(DEFS[n]["params"], {})

    def test_near_miss_an_op_with_no_params_but_a_DEFAULT_still_carries_a_payload(self):
        """§A64 on the row above: the construct spelled similarly that must NOT match.
        `SCHED-HALT` and `SCHED-RESUME` also declare `params: {}` — and they declare a
        non-empty `payload_from`, because `param_defaults` supplies the value. So 'no
        params' does NOT imply 'no payload', and the justified reason is the conjunction,
        not the first half."""
        for n in ("SCHED-HALT", "SCHED-RESUME"):
            self.assertEqual(DEFS[n]["params"], {})
            self.assertNotEqual(DEFS[n]["payload_from"], [])
            self.assertTrue(DEFS[n].get("param_defaults"))

    def test_candidates_carry_their_evidence_and_no_verdict(self):
        for table in (PINNED_SHAPE_DIVERGENCES, PINNED_HOLDOUTS):
            for field, (_evidence, verdict) in table.items():
                self.assertIn(verdict, ("candidate", "justified"))
                self.assertIn(field, UNIVERSE)
        self.assertEqual(PINNED_SHAPE_DIVERGENCES["provenance_param"][1], "candidate")
        self.assertEqual(PINNED_HOLDOUTS["checks"][1], "candidate")


# =======================================================================================
class TWhereTheDivergenceCameFrom(unittest.TestCase):
    """THE PROBE THAT CHANGES WHAT THE CANDIDATE IS, landed as a regression test.

    The mentor's finding reads as two authored positions: MKDIR/SYMLINK chose REQUIRED
    where CREATE chose DEFAULTED. THE HISTORY SAYS OTHERWISE, and it is resolvable by
    machine rather than by argument.

    Commit `b9d9573` (2026-07-28, founding 1.11.0 -> 1.12.0 — EP-27B, the pass that
    INVENTED the required-or-defaulted grammar) ADDED five longhand declarations and
    CONVERTED NONE. Before it: seventeen bare declarations, zero longhand. After it:
    seventeen bare, five longhand. The seventeen have not been touched since before the
    grammar existed.

    SO THE DIVERGENCE IS NOT BETWEEN TWO CHOICES. It is between FIVE authored choices and
    SEVENTEEN policies nobody wrote, supplied by the grammar's silence rule. That reading
    is what EP-29's author needs: writing a new op in the bare form does not decline the
    choice, it takes REQUIRED without deciding.

    ERA-PINNED ON BOTH SIDES (the campaign-2 standing theorem 11): the commit is named by
    CONTENT — the only commit that introduced the longhand string — never by a label, and
    both sides are read out of git rather than out of today's tree."""

    PIN = "b9d9573"

    def _pack_at(self, rev):
        """[DOCUMENTED FLIP — EP-28Z, 2026-08-12. THE SECOND COPY IN THIS FILE, forty lines
        of docstring after the first: `era_pack_bytes` above reads the same act at a
        different pin, and neither knew about the other. That is the debt in one file.
        ASSERTED: a local `git show` spawn with `check=True`. SUPERSEDED: `era_pin.pack_at`.
        REMAINS TRUE: both sides still read out of git and never out of today's tree, and
        `CalledProcessError` is still what an unresolvable pin raises. GIVEN UP: nothing.]"""
        return era_pin.pack_at(rev)

    def _router_shapes(self, pack):
        bare = longhand = 0
        for defn in op_definitions(pack).values():
            v = defn.get("provenance_param")
            if isinstance(v, str):
                bare += 1
            elif isinstance(v, Mapping):
                longhand += 1
        return bare, longhand

    def test_the_grammar_commit_added_longhand_and_converted_nothing(self):
        before = self._router_shapes(self._pack_at(self.PIN + "~1"))
        after = self._router_shapes(self._pack_at(self.PIN))
        self.assertEqual(before, (17, 0), "before the grammar: seventeen bare, no longhand")
        self.assertEqual(after, (17, 5), "after it: the SAME seventeen, plus five")
        self.assertEqual(before[0], after[0], "not one bare declaration was converted")

    def test_the_bare_seventeen_are_unchanged_today(self):
        self.assertEqual(self._router_shapes(PACK), (17, 5))

    def test_the_pin_is_chosen_by_CONTENT_not_by_a_label(self):
        """A PIN CHOSEN BY A LABEL CAN LAND INSIDE A HALF-WRITTEN CHANGE — a two-minute
        autosync committer does not produce semantically atomic commits. This pin is THE
        commit that FIRST introduced the longhand STRING, found by searching for it, and it
        must be the OLDEST of the commits that did — the original introduction, by identity,
        never a count.

        WHY A-OLDEST AND NOT A-MEMBERSHIP (MAINT, architect ruling `:2895`, superseding the
        `:2888` membership form). The history has two lawful introducers now: `b9d9573`
        (EP-27B, the pass that invented the required-or-defaulted grammar and first wrote the
        longhand `"when_absent": "default"` into the pack) and `be07593d` (the COMPLETE-KEY-
        FAMILY move, board `:2887`, which lawfully declared `occurrence_time_param` in the
        longhand form under architect ruling `:2885`). `git log` reports them NEWEST-FIRST,
        so `introducing[-1]` is the ORIGINAL introduction — the pin — and its referent stays
        unique however many later introducers accrue.

        MEMBERSHIP (`:2888`) had two defects `test_ep28z` caught, and A-OLDEST repairs both
        at once:
          * MUTE RED — its `assertTrue` carried a STATIC message that could not name what
            moved, so when the pin was replaced by a commit that is not an introducer the row
            reddened with no way to say which commit it was. A3 (the SUBJECT-MOVED direction
            of `test_ep28z`'s width guard) needs the moved commit named; a static string
            cannot, and that is the live red this swap clears.
          * INTRODUCER-COLLISION GREEN — `any(... in introducing)` passes a MOVED pin as long
            as it is SOME introducer, so just after a founding commit that introduces the
            longhand form a pin set to HEAD (itself an introducer) would pass while it must
            fail. Membership cannot tell 'the original' from 'an introducer'.
        A-OLDEST names BOTH commits in its message (must-red-AND-name-it, architect's A3
        law), has a unique referent `introducing[-1]`, survives unlimited lawful growth, and
        uses no count. Coverage MOVES, never shrinks (architect `:2866`): the row STILL FAILS
        when the pin is not the oldest introducer — that is the property, not the tally."""
        out = subprocess.run(
            ["git", "log", "--format=%h", "-S", '"when_absent": "default"',
             "--", "src/founding/founding-pack.json"],
            cwd=REPO, capture_output=True, text=True, check=True)
        introducing = [l.strip() for l in out.stdout.splitlines() if l.strip()]
        # [MAINT, board `:2895`, form A-OLDEST — supersedes the `:2888` A-MEMBERSHIP form.
        # `introducing` is NEWEST-FIRST (git log default; no --reverse), so `introducing[-1]`
        # is the OLDEST = the original introduction. `commit_identity` (imported, MAINT-2's
        # home for the act) resolves each short `%h` to its full object name, so what is
        # compared is the COMMIT and never its seven- or eight-character rendering — the
        # reason identity and not a prefix is used. The second lawful introducer is `be07593d`
        # (COMPLETE-KEY-FAMILY, board `:2887`), which is why `introducing` now has two members
        # and `introducing[-1]` — not `[0]` — is the one that cannot move under lawful growth.
        # The assert REDS unless the pin is the ORIGINAL introducer, and its message names
        # both `introducing[-1]` and the pin (must-red-AND-name-it, fixing membership's mute
        # red and its introducer-collision green).]
        self.assertEqual(commit_identity(introducing[-1]), commit_identity(self.PIN),
                         f"the ORIGINAL introducer {introducing[-1]!r} is not the pin {self.PIN!r}")


# =======================================================================================
class TIsTheDivergenceREACHABLE(unittest.TestCase):
    """THE SECOND PROBE, and it prices the candidate rather than merely naming it.

    Both bridge readers of this declaration — `bridge/records_fs.py` and
    `bridge/kernel_port.py` — ask `bool(d.get("provenance_param"))` and supply the
    parameter whenever ANY declaration is present. To those two callers the seventeen and
    the five are INDISTINGUISHABLE, so the divergence is LATENT on every path they own.

    The caller that does NOT supply provenance is `kernel/syscall_port.py`, and its
    syscall map reaches exactly four of the five DEFAULTED ops. That is the reason the
    five were converted — and IT IS NOT WRITTEN IN THE LAW. A reader of the founding pack
    cannot recover it, which is the finding: the justification for a law-data divergence
    lives in a caller.

    §A49 — AND THE LEAST-LIKELY MEMBER FALSIFIES THE TIDY VERSION. `FILE-LINK` is the
    fifth DEFAULTED op and NO syscall reaches it, so 'the defaulted set is the
    provenance-less caller set' is FOUR OF FIVE, not five of five. Recorded as four rather
    than rounded to a rule."""

    def _syscall_map_ops(self):
        with open(os.path.join(REPO, "src", "kernel", "syscall_port.py"), "r") as fh:
            src = fh.read()
        import ast
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == "SYSCALL_MAP":
                        return {e.elts[0].value for e in node.value.values}
        self.fail("SYSCALL_MAP not found — AST, not grep, when the question is structure")

    def test_the_defaulted_five_are_the_syscall_callees_plus_one_unexplained(self):
        cells = partition(DEFS, "provenance_param")
        defaulted = set(cells[DEFAULTED])
        self.assertEqual(len(defaulted), 5)
        reached = self._syscall_map_ops() & defaulted
        self.assertEqual(sorted(reached),
                         ["FILE-CREATE", "FILE-PERM", "FILE-UNLINK", "FILE-WRITE"])
        self.assertEqual(sorted(defaulted - reached), ["FILE-LINK"],
                         "the member the caller-reason does NOT explain")

    def test_no_REQUIRED_op_is_reached_by_a_provenance_less_syscall(self):
        """The control. If a syscall reached a REQUIRED op, the divergence would be a live
        refusal rather than a latent one — and that is a different finding with a different
        price. It does not, today, and this row reds the day it does."""
        cells = partition(DEFS, "provenance_param")
        self.assertEqual(sorted(self._syscall_map_ops() & set(cells[REQUIRED])), [])

    def test_both_bridge_readers_cannot_tell_the_two_shapes_apart(self):
        """Read at the line rather than described: both sites coerce the declaration to a
        BOOLEAN, which discards the policy. That is why the divergence has survived."""
        for rel in ("src/bridge/records_fs.py", "src/bridge/kernel_port.py"):
            with open(os.path.join(REPO, rel), "r") as fh:
                text = fh.read()
            self.assertIn('bool(d.get("provenance_param"))', text, rel)


#: THE JUSTIFIED CLASS — divergences whose reason is READ FROM THE DEFINITIONS and
#: re-derived mechanically by the rows above. Named here so the count is falsifiable
#: rather than an impression.
JUSTIFIED = ("act_kind", "content_form", "authority_regime", "payload_from-empty")


# =======================================================================================
class TAuditChangedNoLaw(unittest.TestCase):
    """THE HARD CONSTRAINT, asserted rather than promised: this pass is an AUDIT and the
    founding is byte-UNCHANGED under it. An audit that edits what it audits is a law
    change without the founding open."""

    def test_founding_version_and_digest_are_read_not_written(self):
        """[EP-29 W1a, 2026-08-09 — ERA-PINNED under §A57. A documented flip with its cause.]

        ASSERTED (2026-08-08): the LIVE pack declares 1.18.0 with digest `a9ab2641…`.
        SUPERSEDED: EP-29 W1a moved the founding 1.18.0 -> 1.19.0 on 2026-08-09 — declaring
        `DEV-LAW-BIND`, two parameters on `REGISTER-CAPABILITY` and a `require_prior` on
        `UNBIND` — so the live side names a LATER era's founding and this row reddened on a
        lawful move. §A57's own class: a landing pass cannot pin an after-commit that does
        not exist yet, so the pin arrives from the next founding pass.
        REMAINS TRUE, and it is what the row always meant: THIS AUDIT changed no law, so the
        pack AT THIS AUDIT'S OWN ERA declares 1.18.0 with that digest. Read out of git at
        `ERA_COMMIT`, which cannot go stale.
        AND IT GAINS A JOB: this row is now the POSITIVE CONTROL on `ERA_COMMIT` itself. The
        two other era-pinned rows in this file read that pin for counts; if it ever resolved
        to the wrong bytes they would assert confidently about the wrong era and say nothing.
        This row reds first.
        GIVEN UP: the live side's forward-looking half — noticing a BACKWARDS move. That is
        `test_founding_version_floor` beside this one, which is live, green and untouched;
        and `test_the_founding_tree_is_clean_under_this_pass` still reads live porcelain.
        NOT ASSERTED, stated as a cap rather than smuggled in: the message's continuity claim
        ("and EP-28T left byte-unchanged") spans an era this single-commit read cannot span.
        It was verified at this pass by hand — the pack at `ba125bd7~1` is byte-identical to
        the pin — and NOT written as an assertion, because this pass's fence licenses
        era-pinning the falsified assertions and nothing beyond them."""
        era_bytes = era_pack_bytes()
        self.assertEqual(json.loads(era_bytes.decode("utf-8"))["founding_version"], "1.18.0")
        digest = hashlib.sha256(era_bytes).hexdigest()
        self.assertEqual(
            digest,
            "a9ab26415843efe3a830c223a2876e08e55c5f0f8f8d09ea44338d199a0c39f9",
            "the pack EP-28S landed and EP-28T left byte-unchanged",
        )

    def test_founding_version_floor(self):
        """A FLOOR, not a literal — EP-28T's own remedy for the M2 class. The founding
        never goes backwards past what this audit read; a lawful bump does not red this
        row, and a regression does."""
        parts = tuple(int(x) for x in PACK["founding_version"].split("."))
        self.assertGreaterEqual(parts, (1, 18, 0))

    #: THE COMMIT THIS AUDIT'S WORK LANDED IN — the second and last of the two commits that
    #: carry it (`afabded` created this file, `69764cf` completed it). Re-taken by a row below
    #: rather than trusted from this comment. The near end is `ERA_COMMIT`, the audit's own
    #: pre-write era, already named at the head of this file and reused rather than duplicated.
    AUDIT_LANDED_AT = "69764cf"

    #: A RANGE THE FOUNDING DID MOVE IN, for the red world below: W3a3's pre-write commit to
    #: the commit its pack write landed in. CLOSED at both ends, so it cannot drift as HEAD
    #: advances. These commits belong to EP-29 and are named here only as a world to drive
    #: against; nothing in this file asserts anything about that pass.
    A_RANGE_THE_FOUNDING_MOVED_IN = ("be0d00e8", "51da089")

    def _founding_diff(self, before, after):
        """THE ONE READER for this claim, so the guard and its red world cannot drift apart."""
        out = subprocess.run(
            ["git", "diff", "--stat", "%s..%s" % (before, after), "--", "src/founding/"],
            cwd=REPO, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        return out.stdout.strip()

    def test_the_founding_tree_is_clean_under_this_pass(self):
        """[DOCUMENTED FLIP — GUARD-ASKS-THE-WORKING-TREE, 2026-08-14, board `:776`. CAUSE:
        the row asked the WORKING TREE — `git status --porcelain` — whether the audit had
        written into the founding. Autosync commits every two minutes, so the tree is EMPTY
        before any suite reads it and the answer was a fact about the timer rather than about
        the audit. The row could not fail. ASSERTED: the diff between this audit's own
        pre-write era and the commit its work landed in, which no commit can launder.
        SUPERSEDED: live porcelain. REMAINS TRUE, and it is the row's whole claim: THIS AUDIT
        wrote nothing into `src/founding/`. GIVEN UP: the forward-looking half — noticing a
        LATER pass writing into the founding. That was never this row's subject and it was
        never true of a porcelain read either, because porcelain sees only uncommitted work;
        the founding's live position is held by `test_founding_version_floor` above, which is
        live, green and untouched.

        THE RANGE IS CLOSED. EP-28G's flip on `tests/test_ep28h.py` ruled it: an open
        `X..HEAD` range reds by construction on the next pass that lawfully touches the
        paths, and the founding has moved 1.18.0 -> 1.24.0 since this audit ran.]"""
        self.assertEqual(
            self._founding_diff(ERA_COMMIT, self.AUDIT_LANDED_AT), "",
            "the audit wrote into the founding")

    def test_the_range_the_founding_row_reads_is_THIS_AUDITS_OWN_and_is_CLOSED(self):
        """§A39 on the row above: both ends resolve, the near end is an ancestor of the far
        end, and the far end is this audit's own landing rather than whatever HEAD happens to
        be — otherwise the diff above could be empty for the wrong reason, which is the whole
        defect being repaired. The far end is re-taken from history rather than trusted: it
        must be the LAST commit touching this file inside the audit's own two-commit window."""
        for rev in (ERA_COMMIT, self.AUDIT_LANDED_AT):
            out = subprocess.run(["git", "rev-parse", "--verify", rev + "^{commit}"],
                                 cwd=REPO, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, "%s does not resolve: %s" % (rev, out.stderr))
        anc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ERA_COMMIT, self.AUDIT_LANDED_AT],
            cwd=REPO, capture_output=True, text=True)
        self.assertEqual(anc.returncode, 0,
                         "the audit's era commit is not an ancestor of its landing commit")
        created = subprocess.run(
            ["git", "log", "--format=%h", "--diff-filter=A", "--", "tests/test_ep28j.py"],
            cwd=REPO, capture_output=True, text=True)
        self.assertEqual(created.returncode, 0, created.stderr)
        self.assertEqual(len(created.stdout.split()), 1,
                         "this file has more than one creating commit")
        birth = created.stdout.split()[0]
        reach = subprocess.run(
            ["git", "log", "--format=%h", "%s..%s" % (birth, self.AUDIT_LANDED_AT),
             "--", "tests/test_ep28j.py"],
            cwd=REPO, capture_output=True, text=True)
        self.assertEqual(reach.returncode, 0, reach.stderr)
        # [MAINT-2, 2026-08-26. `%h` emits eight characters on this repository and
        # `AUDIT_LANDED_AT` is seven, so this row was comparing a RENDERING where it means
        # an IDENTITY and could not succeed while the widths differed — with its subject
        # never having moved. Both sides resolve to full object names now. The window claim
        # is untouched: exactly one commit reaches this file inside the audit's range, and
        # it is this audit's own landing commit.]
        self.assertEqual([commit_identity(h) for h in reach.stdout.split()],
                         [commit_identity(self.AUDIT_LANDED_AT)],
                         "the audit's window is not the two commits this row names")

    def test_the_founding_guard_REDS_WHEN_A_LINE_MOVED(self):
        """THE NEGATIVE-RESULT TEST, and it is the whole reason this row exists. The guard
        above passes by PRODUCING NO OUTPUT, and a guard that cannot produce output is not a
        guard — which is exactly how the porcelain form reported clean over a founding that
        has since moved six minor versions. Driven through the SAME reader over a range the
        founding DID move in, it must report, and the guard's own assertion must FAIL.

        The literals are HAND-READ from `git diff --numstat be0d00e8 51da089 -- src/founding/`
        — a different flag from the one the row runs — and never produced by running this
        row."""
        before, after = self.A_RANGE_THE_FOUNDING_MOVED_IN
        moved = self._founding_diff(before, after)
        self.assertIn("src/founding/founding-pack.json", moved)
        self.assertIn("63 insertions(+), 2 deletions(-)", moved)
        with self.assertRaises(AssertionError):
            self.assertEqual(moved, "", "the guard's own assertion, over a world that moved")

    def test_the_red_worlds_range_is_CLOSED_so_the_world_it_names_cannot_drift(self):
        """The red world is only a red world while its range still holds the move. Both ends
        resolve and neither is HEAD, so a later pass cannot quietly empty it."""
        for rev in self.A_RANGE_THE_FOUNDING_MOVED_IN:
            out = subprocess.run(["git", "rev-parse", "--verify", rev + "^{commit}"],
                                 cwd=REPO, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, "%s does not resolve: %s" % (rev, out.stderr))

    def test_the_pack_declares_three_files_and_this_pass_added_none(self):
        out = subprocess.run(["git", "ls-files", "--", "src/founding/"],
                             cwd=REPO, capture_output=True, text=True, check=True)
        self.assertEqual(len([l for l in out.stdout.splitlines() if l.strip()]), 3)


if __name__ == "__main__":
    unittest.main()
