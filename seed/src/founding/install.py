"""gov-os founding installer — genesis as the execution of a data document (design/31 J9).

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

from kernel.opdefs import validate_definition_shape

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
    with open(path, encoding="utf-8") as f:
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
            validate_definition_shape(_FoundingDoor(where, name), "FOUNDING",
                                      "SYSTEM", name, pl.get("definition") or {}, peers)

        # having validated this record's references, it now founds its own entity
        if action == "CREATE-ACTOR":
            actors.add(pl.get("actor_id") or r.get("object"))
        elif action == "CREATE-INFO" and pl.get("kind") == "info_space":
            spaces.add(r.get("object"))


def install(store):
    """Execute the founding pack against `store`. Idempotent; validated whole before any
    append; the founding designation gains the pack's version. Returns None (matches the
    old genesis signature; compose re-exports boot.genesis which delegates here)."""
    # idempotency: the same SYSTEM-actor guard the old genesis used — a reload or an
    # explicit second call founds nothing twice.
    already = any((e.get("payload") or {}).get("actor_id") == "SYSTEM"
                  for e in store.by_action("CREATE-ACTOR"))
    if already:
        return

    pack = load_pack()
    recs = records(pack)
    _validate(recs)                      # refuse the WHOLE founding before any append
    version = pack.get("founding_version")

    for r in recs:
        ev = dict(r)                      # do not mutate the loaded pack
        if ev.get("action") == "FOUND-STORE" and version is not None:
            # F4: stamp the founding version into the founding designation payload. One
            # source of truth (the pack's top-level founding_version); the record reflects it.
            ev["payload"] = dict(ev.get("payload") or {}, founding_version=version)
        store._append(ev)
