# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS founding installer — genesis as the execution of a data document (design/31 J9).

The founding is `founding-pack.json`: one data file holding the founding in corpus
venn2-foundational §09 step order — the founding designation; SYSTEM + owner actors;
the owner tunnel; the mother space; ALL root laws in full trigger->outcome form, each
naming the space it binds (the `scope` field — J5's ground); the vocabulary and policy
packs; the core + governance + obligation op definitions; the seven master views; and
the founding openness grant (design/31 EP-17's transition policy needs it to EXIST from
the founding — it enforces nothing yet).

The installer is genesis, not a new write path (EP-14 F2). It:
  - is idempotent exactly as the old genesis was (fresh / reload / explicit call never
    double-seed) — same SYSTEM-actor-present guard;
  - validates referential integrity across the WHOLE pack BEFORE it appends anything:
    each declared reference (a law's scope, the grant's space, the tunnel's endpoints)
    must name an entity that an earlier step already founds. A half-founded record is
    worse than none, so the FIRST violation refuses the WHOLE founding, loudly, with
    nothing appended;
  - validates DEFINITION SHAPE over every op the pack defines, with the same vocabulary
    the CREATE-OP path uses (EP-27B ADDENDUM 2 W6c; design/36 ADDENDUM I.3). Op
    definitions reach the registry through three doors and this is the one they all came
    through; a check at the other two sits away from the traffic. Founding-only legitimacy
    means nothing can AUTHORIZE the founding — it exempts the pack from authority checks
    and from nothing else. A record that cannot be interpreted is not made interpretable
    by being at genesis;
  - appends via the SAME sanctioned direct `store._append` genesis always used — no gate
    change, no new appender (T-GATE-SOLE-APPENDER unchanged); the founding is a
    constitutional seed, above the gate exactly as before;
  - stamps the pack's `founding_version` into the founding designation payload (F4), so a
    booted record shows which founding version raised it and a future founding's diff is a
    document diff.

The pack is the FOUNDING, singular and versioned — never a config file. There are no
environment overrides, no optional sections, no per-deployment merge (EP-14's named wrong
reference: configurability is the door to an ungoverned founding).
"""

import json
import os

from bridge.host_seam import host   # C7 P2 — the pack READ is a declared host act (the pack itself is untouched DATA)
from kernel.opdefs import validate_definition_shape, VOCAB_DOOR_LAW, CELL_LAW, CELL, CELL_SET

PACK_PATH = os.path.join(os.path.dirname(__file__), "founding-pack.json")


class FoundingIntegrityError(RuntimeError):
    """A pack record references an entity no earlier step founds, or defines an operation the
    one interpreter cannot read. The whole founding is refused; nothing is appended (a
    half-founded record is worse than none)."""


class _FoundingDoor:
    """The founding's door, shaped like the gate so the SAME shape vocabulary runs at it.

    `validate_definition_shape` is written against `gate.refuse`, where a refusal is recorded
    and raised. There is no store to record into here — the pre-flight runs before the first
    append, and a refused founding leaves nothing behind by design — so this door turns the
    same refusal into the installer's own: the whole founding, refused loudly, with the gate's
    citation and message carried through unchanged. One validation, three doors."""

    def __init__(self, where, name):
        self.where, self.name = where, name

    def refuse(self, actor, op, rule, message):
        raise FoundingIntegrityError(
            f"{self.where}: operation {self.name!r} is malformed — {message} [{rule}] — "
            f"the whole founding is refused (nothing appended)")


def load_pack(path=PACK_PATH):
    """Read the founding pack document. The pack is DATA — this is the only reader."""
    with host().open_read_text(path, encoding="utf-8") as f:
        return json.load(f)


def records(pack):
    """The founding as a single ordered list of records (steps flattened in document
    order). The order IS the founding order — each entry references only what an earlier
    entry already founds."""
    out = []
    for step in pack["steps"]:
        out.extend(step["records"])
    return out


def founding_version(pack=None):
    return (pack or load_pack())["founding_version"]


def root_laws(pack=None):
    """The root laws as (rule_id, polarity, text, extras) tuples — the shape the old
    boot.ROOT_RULES literal exposed, now READ FROM the pack, never a source literal. For
    tests/tools that enumerate the constitution; the record remains the truth."""
    pack = pack or load_pack()
    out = []
    for r in records(pack):
        pl = r.get("payload") or {}
        if r.get("action") == "CREATE-RULE" and pl.get("root") is True:
            extras = {k: v for k, v in pl.items()
                      if k not in ("rule_id", "root", "polarity", "text")}
            out.append((pl["rule_id"], pl["polarity"], pl["text"], extras))
    return out


def op_definitions(pack=None):
    """The founding's op SHAPES, `{name: definition}`, read from the pack's CREATE-OP
    records — the single authoritative home for every op definition (EP-14B). Modules that
    still carry a copy of one of these shapes are non-authoritative references; the drift
    guard (tests/test_ep14b.py) compares each surviving copy against this reader and fails
    loudly if they diverge. Tests that need an op's shape as payload material READ IT HERE,
    never from a module dict (the EP-14B repoint; the `root_laws` precedent above)."""
    pack = pack or load_pack()
    out = {}
    for r in records(pack):
        pl = r.get("payload") or {}
        if r.get("action") == "CREATE-OP" and pl.get("kind") == "op_definition":
            out[pl["name"]] = pl["definition"]
    return out


def op_definition(name, pack=None):
    """One op's shape by name, read from the pack (EP-14B). Raises KeyError if the founding
    defines no such op — the founding is the source of truth for what ops exist."""
    return op_definitions(pack)[name]


def _validate(recs):
    """Whole-pack pre-flight, in step order: referential integrity, and the SHAPE of every op
    the pack defines. Builds the set of founded entities as it walks; a record whose declared
    reference is not yet founded, or whose definition the one interpreter could not read,
    refuses the WHOLE founding on the first violation. Appends nothing.

    The declared references checked are exactly the ones §09 step order guarantees resolve
    in the faithful founding: an actor mint founds an actor; the mother-space mint founds a
    space; the tunnel names two actors; every root law names the space it binds; the
    openness grant names its space. (Envelope `actor`/`rule_cited` are bootstrap citations —
    the founding cites BOOT-INT before BOOT-INT is seeded — so they are NOT references.)

    The definition shape is not a second list living here: it is `opdefs`'
    `validate_definition_shape`, the same function the CREATE-OP and AMEND-OP doors call, run
    through `_FoundingDoor`. When that vocabulary grows, this door grows with it and no one has
    to remember to copy it (EP-27B ADDENDUM 2 W6c).

    THE PEERS ARE COLLECTED BEFORE THE WALK AND NOT DURING IT (EP-28K). One clause in that
    vocabulary asks about a definition's PLACE among the others — an op citing the law whose
    acts bind names must say what it does to them — and answering that from a set built as the
    walk proceeds would make the verdict depend on document order: the first namespace op in
    the pack would be judged against a set that did not yet contain the law it cites. Document
    order is the FOUNDING order (each record references what an earlier one founds); it is not
    a statement about which definitions govern each other, and reading it as one would make a
    guard that refuses or admits by position.
    """
    actors = set()
    spaces = set()
    peers = {(r.get("payload") or {}).get("name"): (r.get("payload") or {}).get("definition") or {}
             for r in recs
             if r.get("action") == "CREATE-OP" and (r.get("payload") or {}).get("kind") == "op_definition"}
    # EP-41A member 2 (design/46): the vocabulary door engages at the FOUNDING installer only where
    # THIS founding declares the vocabulary-door law — read from the pack's OWN rule records (a law
    # is self-declared by its payload `rule_id`, the `active_rules` idiom), the founding-time equal
    # of the runtime doors' live-`active_rules` read. A pack that does not declare it (every world
    # before the MOVER-4 create + census sweep) classifies nothing and founds exactly as before —
    # the wire-at-birth gate that keeps the held founding-move inert until the owner's word.
    classify_law_live = any((r.get("payload") or {}).get("rule_id") == VOCAB_DOOR_LAW for r in recs)
    # C6 P8 (design/52 L28): the CELL-PRESENCE requirement engages at the FOUNDING door only where THIS
    # founding declares CELL-LAW — read from the pack's OWN rule records (the wire-at-birth idiom,
    # VOCAB_DOOR_LAW's precedent). Every op the founding declares must carry a well-formed cell or the
    # WHOLE founding is refused. This lives HERE, not at the runtime CREATE-OP / AMEND-OP doors,
    # because the cell is FOUNDING DATA (a pack-scope declaration) — a runtime extension op is not the
    # pack the law binds, and refusing one over the record's own history is exactly the enforcement the
    # law HOLDS. A pack that does not declare CELL-LAW (every world before P8) requires no cell and
    # founds exactly as before. The cell is NEVER defaulted (a silent default of S is a program holding
    # judgment, which L28 forbids), so an op with no cell REFUSES rather than being assigned one.
    cell_law_live = any((r.get("payload") or {}).get("rule_id") == CELL_LAW for r in recs)
    # C6 P8 / K12 (design/52 L28; archi :3731 C): the ACTOR-CLASS DOMAIN check at the founding door — the
    # wire-at-birth companion to the runtime write-refusal (P8b A6). A genesis CREATE-ACTOR whose
    # actor_class is outside the pack's OWN declared class domain refuses the WHOLE founding: the
    # cell-presence idiom above applied to the class field. It differs from `cell_law_live` in ONE way and
    # the difference is load-bearing. cell_law_live is a WHOLE-PACK flag because every op must carry a cell
    # WHATEVER its position; a class domain closes only over actors founded AFTER it is declared — the
    # recorder-system SYSTEM (actor_class "system") is founded at the pack's head, long before the
    # {human,ai,program} domain goes live, and cannot be judged against a domain that did not yet exist
    # (the same reason the pairing census re-judges no past act). So the domain is tracked POSITIONALLY as
    # the walk proceeds (like `actors`/`spaces`), live only for the records that follow it, and INERT where
    # absent — every world before P8 (no actor-classes pack) founds exactly as before.
    class_domain = None
    for i, r in enumerate(recs):
        action = r.get("action")
        pl = r.get("payload") or {}
        where = f"record #{i + 1} ({action} {r.get('object')!r})"

        if action == "CREATE-TUNNEL":
            for role in ("sender", "target"):
                who = pl.get(role)
                if who is not None and who not in actors:
                    raise FoundingIntegrityError(
                        f"{where}: tunnel {role} {who!r} is not a founded actor — "
                        f"the whole founding is refused (nothing appended)")
        elif action == "CREATE-RULE" and pl.get("root") is True:
            scope = pl.get("scope")
            if scope is not None and scope not in spaces:
                raise FoundingIntegrityError(
                    f"{where}: root law scope {scope!r} names a space no earlier step founds — "
                    f"the whole founding is refused (nothing appended)")
        elif action == "GRANT":
            space = pl.get("space")
            if space is not None and space not in spaces:
                raise FoundingIntegrityError(
                    f"{where}: grant space {space!r} names a space no earlier step founds — "
                    f"the whole founding is refused (nothing appended)")
        elif action == "CREATE-OP" and pl.get("kind") == "op_definition":
            name = pl.get("name")
            definition = pl.get("definition") or {}
            validate_definition_shape(_FoundingDoor(where, name), "FOUNDING",
                                      "SYSTEM", name, definition, peers,
                                      classify_law_live=classify_law_live)
            # C6 P8 / L28: the cell-presence requirement, engaged only under a live CELL-LAW founding.
            # A well-formed cell (value in the set) is validated by validate_definition_shape above; here
            # the founding door additionally requires the cell to be PRESENT — every op declares one, or
            # the whole founding is refused (never defaulted). A missing cell is the founding data gap the
            # law closes; a malformed one already refused above.
            if cell_law_live and definition.get(CELL) not in CELL_SET:
                raise FoundingIntegrityError(
                    f"{where}: operation {name!r} declares no cell (design/52 L28: every operation "
                    f"declares its cell as founding data, one of {CELL_SET}, never derived from field "
                    f"shapes and never defaulted) — the whole founding is refused (nothing appended)")
        elif action == "CREATE-ACTOR":
            # K12 wire-at-birth: a genesis actor founded AFTER the class domain goes live must declare a
            # class WITHIN it; INERT while no domain is live yet (SYSTEM/owner at the pack head), so the
            # production founding still founds. The domain is `class_domain`, tracked positionally below.
            actor_class = pl.get("actor_class")
            if class_domain is not None and actor_class not in class_domain:
                raise FoundingIntegrityError(
                    f"{where}: actor {pl.get('actor_id') or r.get('object')!r} declares actor_class "
                    f"{actor_class!r}, outside the live class domain {class_domain} (K12: the class "
                    f"field's domain closes; design/52 L28) — the whole founding is refused (nothing appended)")

        # having validated this record's references, it now founds its own entity
        if action == "CREATE-ACTOR":
            actors.add(pl.get("actor_id") or r.get("object"))
        elif action == "CREATE-INFO" and pl.get("kind") == "info_space":
            spaces.add(r.get("object"))
        # the actor-class domain goes live (or re-cuts) here, so it binds only the actors that FOLLOW it
        # in founding order — the wire-at-birth ordering that keeps the pack-head SYSTEM actor inert.
        if pl.get("kind") == "category_pack" and pl.get("name") == "actor-classes" \
                and isinstance(pl.get("levels"), (list, tuple)):
            class_domain = tuple(pl["levels"])


def install(store):
    """Execute the founding pack against `store`. Idempotent; validated whole before any
    append; the founding designation gains the pack's version. Returns None (matches the
    old genesis signature; compose re-exports boot.genesis which delegates here)."""
    pack = load_pack()
    recs = records(pack)
    # VT-3c (archi :3846): READ THE WORLD'S OWN FOUNDING VERSION BEFORE THE LAST-RECORD IDEMPOTENCY.
    # A world's own version is its FIRST FOUND-STORE record's stamped founding_version —
    # store.by_action("FOUND-STORE")[0], the founding designation, first in the pack, where F4 stamps it
    # (:273-276). A version DIFFERENT from the pack's is a COMPLETE OLDER WORLD: opening it appends NOTHING
    # and returns byte-identical. Bringing an older world forward is a MIGRATION — an EXPLICIT act, NEVER an
    # open side-effect. Without this read, VT-3's seed (which appended a founding step at the END, moving the
    # pack's terminal record) leaves every pre-1.53.0 world's last record absent, so the last-record check
    # below would re-found the WHOLE pack on open — a second founding under a new-version FOUND-STORE
    # (govos-w4), which is forward-amend by accident and the genesis law forbids (:2901). A world already
    # holding TWO FOUND-STOREs (an already-migrated world) is judged by its FIRST ([0]), so it returns
    # byte-identical under every future pack. An UNSTAMPED FOUND-STORE (version None — pre-F4, or a raw-record
    # test fixture) declares no older version: it falls through to the last-record idempotency, which keeps
    # the :2901 partial-prefix re-land exactly as before (STOP-condition (d): the re-land is never lost).
    found_store = store.by_action("FOUND-STORE")
    if found_store:
        world_version = (found_store[0].get("payload") or {}).get("founding_version")
        if world_version is not None and world_version != pack.get("founding_version"):
            return
    # IDEMPOTENCY READS THE PACK'S OWN LAST RECORD (EP-MAINT-OUTSIDE-1 B9). The old guard keyed on
    # "a SYSTEM actor exists", which is the SECOND record of the pack — so a founding that stopped
    # after CREATE-ACTOR SYSTEM (or any early record) was taken as already founded, and the genesis-
    # pack clean-stop-and-re-land case (:2901) could never re-land. Instead the guard asks whether
    # the pack's LAST record — by the pack's OWN order (records(pack)[-1]) — is present: a complete
    # founding has it and founds nothing twice, while a partial PREFIX (its last record absent) re-
    # lands cleanly. Keyed on the last record's action+object, not on the FOUND-STORE designation,
    # which is FIRST in the pack (views.py:442) and can never be the completion marker. VT-3c adds the
    # version read ABOVE, for the SAME-version fall-through this handles (older worlds returned already).
    last = recs[-1]
    if any(e.get("object") == last.get("object") for e in store.by_action(last.get("action"))):
        return

    _validate(recs)                      # refuse the WHOLE founding before any append
    version = pack.get("founding_version")

    for r in recs:
        ev = dict(r)                      # do not mutate the loaded pack
        if ev.get("action") == "FOUND-STORE" and version is not None:
            # F4: stamp the founding version into the founding designation payload. One
            # source of truth (the pack's top-level founding_version); the record reflects it.
            ev["payload"] = dict(ev.get("payload") or {}, founding_version=version)
        store._append(ev)
