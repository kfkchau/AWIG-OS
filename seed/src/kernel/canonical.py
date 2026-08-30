"""gov-os kernel — the canonical serializer (EP-23 W3; design/34 §5).

TCB-GRADE. This module decides, for every value the record can hold, whether two things
are ONE STATE or TWO. Everything the fingerprint check answers rests on that decision:

  * two serializations of ONE state must give ONE hash  — or the check manufactures FALSE
    STALES, and every crossing over a re-encoded pack refuses for no reason;
  * two states must never give ONE hash                  — or the check manufactures FALSE
    HOLDS, and a judgment executes against a world that moved. That failure is INVISIBLE:
    nothing crashes, nothing is refused, and the record shows a pass.

Because the second failure cannot be seen from outside, the battery ships WITH the check
and was written before anything hashed with it (tests/test_ep23.py, T-FP-CANONICAL).

THE FORM: a length-prefixed, type-tagged byte encoding — not JSON.

JSON is not canonical. Its numbers have several spellings for one value, its objects have
no defined key order, its strings have several byte forms for one character sequence, and
a serializer that concatenates without lengths collides `{"a": "b:c"}` with `{"a:b": "c"}`.
Each of those is a way for two states to become one hash. So:

    null            n
    false / true    b0 / b1
    int             i<decimal>;
    float           f<repr>;                 finite only; -0.0 folds to 0.0
    str             s<len>:<utf-8 of NFC>
    bytes           y<len>:<raw>
    list / tuple    l<count>:<item>...       list and tuple are ONE state (see below)
    mapping         d<count>:<key><value>... pairs sorted by the key's own encoded bytes

WHY LIST AND TUPLE ARE ONE STATE. `store._freeze` turns every stored list into a tuple, so
the same pack read live and read back from the record differs by that alone. Hashing them
apart would false-stale every crossing whose pack holds a list. The same reasoning makes a
`MappingProxyType` and a `dict` one state.

WHY NFC AND NOT NFKC. Canonical composition folds the several byte sequences that spell ONE
abstract character; compatibility folding (NFKC) additionally merges characters that are
genuinely different — the ligature and the two letters. Merging distinct characters is a
false HOLD, the invisible failure. So NFC, never NFKC.

WHY `seq` IS NOT CONTENT. Callers pass folds through `strip_derivation`: the estate's folds
decorate their answers with the `seq` of the record they were derived from, which is ORDER,
not state. design/34 §3 rules that fingerprint equality is state-equality and not
history-equality — the ABA case must execute — so a sequence number may never enter a
state fingerprint. Stripping it is that ruling applied, not a convenience.

REFUSAL, NOT APPROXIMATION. A value this encoding cannot express raises
`NotCanonicalizable` (P4: refuse and cite, never improvise). Two keys that are different
strings but normalize to the same key would silently drop one — one hash for two states —
so that refuses too.
"""

import hashlib
import unicodedata
from collections.abc import Mapping


class NotCanonicalizable(ValueError):
    """A value the canonical encoding cannot express. Raised rather than approximated: an
    approximate hash is a false hold or a false stale that nothing downstream can see."""


def _encode(value, path="$"):
    if value is None:
        return b"n"
    if value is True:
        return b"b1"
    if value is False:
        return b"b0"
    if isinstance(value, int):                       # bool handled above (bool is an int)
        return b"i" + str(value).encode("ascii") + b";"
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise NotCanonicalizable(
                f"{path}: {value!r} is not a finite number — a non-finite value has no canonical form")
        if value == 0.0:
            value = 0.0                              # -0.0 and 0.0 are one quantity
        return b"f" + repr(value).encode("ascii") + b";"
    if isinstance(value, str):
        raw = unicodedata.normalize("NFC", value).encode("utf-8")
        return b"s" + str(len(raw)).encode("ascii") + b":" + raw
    if isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
        return b"y" + str(len(raw)).encode("ascii") + b":" + raw
    if isinstance(value, Mapping):
        pairs = []
        seen = {}
        for k, v in value.items():
            ek = _encode(k, f"{path}.<key>")
            if ek in seen:
                raise NotCanonicalizable(
                    f"{path}: keys {seen[ek]!r} and {k!r} are different but canonicalize to the same key — "
                    "one of them would be silently dropped (one hash for two states)")
            seen[ek] = k
            pairs.append((ek, _encode(v, f"{path}.{k}")))
        pairs.sort(key=lambda p: p[0])               # total order on the KEY's own bytes
        body = b"".join(ek + ev for ek, ev in pairs)
        return b"d" + str(len(pairs)).encode("ascii") + b":" + body
    if isinstance(value, (list, tuple)):
        items = [_encode(v, f"{path}[{i}]") for i, v in enumerate(value)]
        return b"l" + str(len(items)).encode("ascii") + b":" + b"".join(items)
    raise NotCanonicalizable(
        f"{path}: {type(value).__name__} has no canonical form — the record's value space is "
        "null / bool / int / float / str / bytes / list / mapping")


def canonical_bytes(value):
    """The canonical byte encoding of one value. Deterministic across processes and runs:
    ordering is by encoded bytes, never by Python's hash (no PYTHONHASHSEED dependence)."""
    return _encode(value)


def canonical_hash(value):
    """The canonical hash, in the estate's one hash form ("sha256:<hex>" — the same shape
    the blob store and the vault use). This is the SEAL: mint it at hand-out, recompute it
    at return, compare (design/34 §1)."""
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def strip_derivation(value, drop=("seq",)):
    """Remove DERIVATION PROVENANCE from a fold's answer before it is sealed.

    The estate's folds decorate each entry with the `seq` of the record it came from — the
    grant fold, the rule fold, the space tree, the role fold all do it. That number is the
    record's ORDER, not the state's content: a grant revoked and re-minted with identical
    terms is the SAME state at a later seq (design/34 §3, the ABA case, which must execute).
    Sealing the seq would make every fingerprint history-sensitive and turn the ruled ABA
    behaviour into its opposite.

    Applied recursively to mappings and sequences. Nothing else is removed — this is one
    named, derived exclusion, not a general filter."""
    if isinstance(value, Mapping):
        return {k: strip_derivation(v, drop) for k, v in value.items() if k not in drop}
    if isinstance(value, (list, tuple)):
        return [strip_derivation(v, drop) for v in value]
    return value
