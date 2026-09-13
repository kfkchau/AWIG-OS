"""EP-34-BUILD -- the canonical floor: promote, guard, prove.

Every probe here is a regression test (the campaign method: a verification probe lands as a
test). This battery PROMOTES src/kernel/canonical.py from "imported and trusted by use" to the
ENFORCED, fuzz-proven single floor design/37 §4 names:

  "the canonical serializer is engine surface (S-plane) ... one serializer, one fuzz battery, two
   consumers; a second serializer anywhere is a defect by construction."

The named WRONG REFERENCE (design/37 §5) is "just use the JSON dump" -- the ambient serializer as
the canonical form. It is refused by construction: the floor is a length-prefixed, type-tagged
byte encoding, NOT JSON, and this file's one-serializer guard treats a hash-of-canonically-
serialized-structure anywhere in src/ as a governed serializer that must be THE floor or a CLOSED
named exemption.

RUNNER NOTE (raised in the close): the EP §3 acceptance commands are written in pytest with `-k`.
This estate has NO pytest (and no pip); its definitive runner is `python3 -m unittest`, which also
supports `-k`. These tests are therefore unittest.TestCase methods named with the §3 selectors,
so the acceptance MEANING (A1 one_hash / A2 one_serializer / A3 bytes_frozen) is preserved on the
tree's real runner. Equivalences:
  A1  python3 -m unittest -k one_hash        tests.test_ep34   (== pytest -k one_hash)
  A2  python3 -m unittest -k one_serializer  tests.test_ep34   (== pytest -k one_serializer)
  A3  python3 -m unittest -k bytes_frozen    tests.test_ep34   (== pytest -k bytes_frozen)
  A4  python3 -m unittest discover -s tests -p 'test_*.py'     (== pytest tests/)

Coverage:
  A1  T-CANONICAL-ONE-HASH        the fuzz battery -- one state one hash, two states never one
                                  (key order, unicode NFC/NFD, numeric form, nesting, empty,
                                  list/tuple, mappingproxy) + RW1 colliding + RW2 non-deterministic
                                  red worlds through the instrument + the RULED U-B DRIFT PIN
                                  (protection._digest and views.digest_of agree over their shared
                                  corpus) with a non-vacuity control.
  A2  T-CANONICAL-ONE-SERIALIZER  the one-serializer guard: exactly {canonical.py} plus the CLOSED
                                  dual-audit exemption; RW3 plant REDS; a non-governed digest does
                                  NOT trip; a THIRD member REDS (the list is closed, not editable).
  A3  bytes_frozen                canonical_bytes / canonical_hash byte-identical to the PRE-EDIT
                                  module (RW4: a single changed byte is a STOP, never re-pinned).

MUST-NOT-TOUCH: protection.py and views.py are imported READ-ONLY here to drive the guard and the
drift pin; this file modifies neither. Source is ASCII-only: the two unicode spellings are built
from \\u escapes so the NFC/NFD fold is exercised without depending on how this file is stored.
"""

import ast
import itertools
import os
import sys
import tempfile
import types
import unicodedata
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel import canonical    # noqa: E402  -- the module being promoted (THE floor)
from kernel import protection   # noqa: E402  -- READ-ONLY: dual-audit _digest (live), MUST-NOT-TOUCH
from kernel import views        # noqa: E402  -- READ-ONLY: dual-audit digest_of (dormant), MUST-NOT-TOUCH

SRC = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "src"))
CANONICAL_HOME = os.path.realpath(os.path.join(SRC, "kernel", "canonical.py"))
# The CLOSED exemption list (RULED U-B, architect board :2742): the dual-audit digest family ONLY.
_EXEMPT = frozenset({
    (os.path.realpath(os.path.join(SRC, "kernel", "protection.py")), "_digest"),
    (os.path.realpath(os.path.join(SRC, "kernel", "views.py")), "digest_of"),
})

# Two spellings of one character sequence, ASCII-only in source:
_CAFE_NFD = "cafe\u0301"                        # 'e' + COMBINING ACUTE ACCENT (U+0301), decomposed
_CAFE_NFC = unicodedata.normalize("NFC", _CAFE_NFD)   # -> "caf" + U+00E9, composed (one code point)


# ============================================================================================
# Module-level battery helpers (shared by the property test and the red worlds)
# ============================================================================================

# Each class is a set of values that are ONE STATE -- the floor must give them ONE hash.
_EQUIV_CLASSES = [
    ("key_order", [dict(p) for p in itertools.permutations([("a", 1), ("b", 2), ("c", 3)])]),
    ("nested_key_order", [{"o": dict(p)} for p in itertools.permutations([("x", 1), ("y", 2)])]),
    ("unicode_nfc_nfd", [_CAFE_NFC, _CAFE_NFD]),
    ("unicode_in_key", [{_CAFE_NFC: 1}, {_CAFE_NFD: 1}]),
    ("neg_zero", [0.0, -0.0]),
    ("float_reprs", [1000.0, 1e3, 1E3]),
    ("list_tuple", [[1, 2, 3], (1, 2, 3)]),
    ("list_tuple_nested", [[1, [2, 3]], (1, (2, 3)), [1, (2, 3)]]),
    ("dict_mappingproxy", [{"a": 1, "b": 2}, types.MappingProxyType({"a": 1, "b": 2})]),
]

# Genuinely different states -- the floor must never give any two of these ONE hash.
_DISTINCT_REPS = [
    ("none", None), ("true", True), ("false", False),
    ("int0", 0), ("int1", 1), ("int1000", 1000),
    ("float0", 0.0), ("float1", 1.0), ("float1000", 1000.0),
    ("str_empty", ""), ("str_0", "0"), ("str_abc", "abc"),
    ("bytes_empty", b""), ("bytes_abc", b"abc"),
    ("list_empty", []), ("list_1", [1]),
    ("dict_empty", {}), ("dict_a1", {"a": 1}),
    ("colon_a", {"a": "b:c"}), ("colon_b", {"a:b": "c"}),   # the classic length-prefix collision pair
]


def _safe(hf, v):
    """Call hf(v); a raise is its own sentinel so a broken serializer that throws is still ranked."""
    try:
        return ("OK", hf(v))
    except Exception as exc:                                 # noqa: BLE001 -- deliberate: rank any failure
        return ("RAISE", type(exc).__name__)


def _one_hash_report(hf):
    """Run the one-state-one-hash property against an arbitrary hash function. Returns the list of
    violations: EQUIV (one state produced several hashes) and DISTINCT (two states collided)."""
    violations = []
    for name, members in _EQUIV_CLASSES:
        hashes = {_safe(hf, m) for m in members}
        if len(hashes) != 1:
            violations.append(("EQUIV", name, hashes))
    seen = {}
    for name, value in _DISTINCT_REPS:
        h = _safe(hf, value)
        if h in seen:
            violations.append(("DISTINCT", (seen[h], name), h))
        else:
            seen[h] = name
    return violations


def _bad_colliding(v):
    """A key-sorted but LENGTH-BLIND, TYPE-BLIND serializer: order-independent, yet it collides
    {"a":"b:c"} with {"a:b":"c"} -- exactly the collision the floor's length prefix forbids."""
    def enc(x):
        if isinstance(x, dict):
            return "{" + "".join(sorted(enc(k) + ":" + enc(val) for k, val in x.items())) + "}"
        if isinstance(x, (list, tuple)):
            return "[" + ",".join(enc(i) for i in x) + "]"
        return str(x)
    return enc(v)


def _bad_nondeterministic(v):
    import json
    return json.dumps(v, sort_keys=False)                    # output varies with dict insertion order


class OneHash(unittest.TestCase):
    """A1 -- T-CANONICAL-ONE-HASH: the fuzz battery (methods carry the `one_hash` selector)."""

    def test_one_hash_property_holds_for_the_floor(self):
        # the whole battery: one state one hash, two states never one
        report = _one_hash_report(canonical.canonical_hash)
        self.assertEqual(report, [], report)

    def test_one_hash_key_order_permutations(self):
        perms = [dict(p) for p in itertools.permutations([("a", 1), ("b", 2), ("c", 3), ("d", 4)])]
        self.assertEqual(len({canonical.canonical_hash(p) for p in perms}), 1)

    def test_one_hash_unicode_nfc_nfd(self):
        # composed and decomposed spellings of one character sequence are ONE state (NFC fold)
        self.assertNotEqual(_CAFE_NFC, _CAFE_NFD)             # the two source strings really do differ
        self.assertEqual(canonical.canonical_hash(_CAFE_NFC), canonical.canonical_hash(_CAFE_NFD))
        # ... but two genuinely different characters are TWO states (NFC, never the NFKC over-merge)
        self.assertNotEqual(canonical.canonical_hash("\u00e9"), canonical.canonical_hash("e"))

    def test_one_hash_numeric_forms(self):
        # -0.0 folds to 0.0 (one state); the same float written three ways is one state
        self.assertEqual(canonical.canonical_hash(0.0), canonical.canonical_hash(-0.0))
        self.assertEqual(canonical.canonical_hash(1000.0), canonical.canonical_hash(1e3))
        self.assertEqual(canonical.canonical_hash(1e3), canonical.canonical_hash(1E3))
        # a value's INT and FLOAT spellings are DIFFERENT states -- the encoding keeps them apart
        self.assertNotEqual(canonical.canonical_hash(1), canonical.canonical_hash(1.0))
        self.assertNotEqual(canonical.canonical_hash(1000), canonical.canonical_hash(1000.0))

    def test_one_hash_nesting_and_empty(self):
        # nested dicts with permuted inner keys are one state; the four empties are four distinct states
        self.assertEqual(canonical.canonical_hash({"o": {"a": 1, "b": 2}}),
                         canonical.canonical_hash({"o": {"b": 2, "a": 1}}))
        empties = [canonical.canonical_hash(x) for x in ({}, [], "", b"")]
        self.assertEqual(len(set(empties)), 4)

    def test_one_hash_list_tuple_and_mappingproxy(self):
        self.assertEqual(canonical.canonical_hash([1, 2, 3]), canonical.canonical_hash((1, 2, 3)))
        self.assertEqual(canonical.canonical_hash({"a": 1}),
                         canonical.canonical_hash(types.MappingProxyType({"a": 1})))

    def test_one_hash_distinct_states_never_collide(self):
        hashes = [canonical.canonical_hash(v) for _n, v in _DISTINCT_REPS]
        self.assertEqual(len(set(hashes)), len(hashes), "two distinct states share one hash (a false hold)")
        # the length-prefix specifically prevents the {"a":"b:c"} / {"a:b":"c"} collision
        self.assertNotEqual(canonical.canonical_hash({"a": "b:c"}), canonical.canonical_hash({"a:b": "c"}))

    # ---- RW1 / RW2: red worlds driven THROUGH the instrument (a battery that cannot fail is not one) ----

    def test_one_hash_redworld_colliding_serializer_is_caught(self):
        a, b = {"a": "b:c"}, {"a:b": "c"}
        self.assertNotEqual(canonical.canonical_hash(a), canonical.canonical_hash(b))  # floor keeps apart
        self.assertEqual(_bad_colliding(a), _bad_colliding(b))                         # broken one collides
        report = _one_hash_report(_bad_colliding)
        self.assertTrue(any(kind == "DISTINCT" for kind, *_ in report), report)        # battery EXHIBITS it

    def test_one_hash_redworld_nondeterministic_serializer_is_caught(self):
        base = {"a": 1, "b": 2, "c": 3}
        perms = [dict(p) for p in itertools.permutations(base.items())]
        self.assertEqual(len({canonical.canonical_hash(p) for p in perms}), 1)   # floor: one state, one hash
        self.assertGreater(len({_bad_nondeterministic(p) for p in perms}), 1)    # broken: one state, many

    # ---- tooth (2), RULED U-B: the dual-audit DRIFT PIN ----

    def test_one_hash_dual_audit_digest_drift_pin(self):
        # protection._digest (live) and views.digest_of (dormant parity copy) are two copies of one
        # function -- the latent defect U-B exempts rather than unifies. Over the shared corpus they
        # digest -- payload-BEARING governance records, the shape the dual audit mirrors -- they MUST
        # agree; drift between the two copies reds loudly here.
        corpus = [
            {"seq": 1, "actor": "alice", "action": "GRANT-READ", "payload": {"grantee": "bob", "target": "doc-1"}},
            {"seq": 2, "actor": "SYSTEM", "action": "CREATE-RULE", "payload": {"kind": "rule", "levels": ["a", "b"]}},
            {"seq": 3, "actor": "carol", "action": "FILE-OPEN", "payload": {}},
            {"seq": 4, "actor": "dave", "action": "APPEND", "payload": {"nested": {"z": 1, "a": [1, 2, 3]}, "u": _CAFE_NFC}},
            {"seq": 5, "actor": "eve", "action": "REVOKE", "payload": {"target": "doc-1", "reason": "rotate"}},
        ]
        for rec in corpus:
            self.assertEqual(protection._digest(rec), views.digest_of(rec), rec)
        # KNOWN BOUNDARY, disclosed (not introduced here; both files are MUST-NOT-TOUCH): the two copies
        # ALREADY diverge on an ABSENT/None payload -- _digest normalizes it to {} (dict(e.get("payload")
        # or {})), digest_of leaves it None. That is outside the shared (payload-bearing) corpus the pin
        # guards, and it is reported as a finding for the EP-35 re-home; deliberately NOT locked as an
        # assertion (a future fix that makes them agree everywhere must not red this row).

    def test_one_hash_dual_audit_drift_pin_CAN_red_nonvacuity(self):
        # a drift pin that cannot fail is not a pin (§A64): a copy drifted by one hex is caught,
        # while the live pair still agrees.
        import hashlib
        import json
        from kernel.store import frozen_default

        def _drifted(e):
            body = {"seq": e["seq"], "actor": e["actor"], "action": e["action"],
                    "payload": dict(e.get("payload") or {})}
            return hashlib.sha256(json.dumps(body, sort_keys=True,
                                             default=frozen_default).encode("utf-8")).hexdigest()[:15]

        rec = {"seq": 1, "actor": "a", "action": "X", "payload": {"k": "v"}}
        self.assertNotEqual(protection._digest(rec), _drifted(rec))       # drift is detectable
        self.assertEqual(protection._digest(rec), views.digest_of(rec))   # ... and the live pair agrees


# ============================================================================================
# A2 -- T-CANONICAL-ONE-SERIALIZER: the one-serializer guard (AST enumeration over src/)
# ============================================================================================

_HASHLIB_ALGOS = {
    "sha256", "sha1", "sha224", "sha384", "sha512", "md5", "blake2b", "blake2s",
    "sha3_224", "sha3_256", "sha3_384", "sha3_512", "shake_128", "shake_256", "new",
}


def _is_hashlib_call(node):
    """A `hashlib.<algo>(...)` construction."""
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name) and node.func.value.id == "hashlib"
            and node.func.attr in _HASHLIB_ALGOS)


def _arg_is_canonical_serialization(node):
    """True if the subtree canonically serializes a STRUCTURED value for hashing -- the tell that
    separates a governed canonical serializer from incidental hashing of raw bytes or a literal:
      * json.dumps(..., sort_keys=True)     -- a key-deterministic structured serialization, or
      * canonical_bytes(...) / _encode(...) -- the floor's own type-tagged encoder.
    A hash over raw bytes (vault, blobs, replay) or a plain string (custody blake2b) has neither."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            fn = sub.func
            if isinstance(fn, ast.Attribute) and fn.attr == "dumps":
                for kw in sub.keywords:
                    if kw.arg == "sort_keys" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        return True
            name = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else None)
            if name in ("canonical_bytes", "_encode"):
                return True
    return False


def _sites_in_tree(tree, path):
    found = set()

    def visit(node, func):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func = node.name
        if _is_hashlib_call(node) and (
                any(_arg_is_canonical_serialization(a) for a in node.args)
                or any(_arg_is_canonical_serialization(kw.value) for kw in node.keywords)):
            found.add((path, func))
        for child in ast.iter_child_nodes(node):
            visit(child, func)

    visit(tree, None)
    return found


def _governed_canonical_sites(roots):
    """Every site under `roots` that hashes a canonically-serialized structure, as (realpath, func)."""
    sites = set()
    for root in roots:
        for dirpath, _dirs, files in os.walk(root):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                path = os.path.realpath(os.path.join(dirpath, fn))
                with open(path, "r", encoding="utf-8") as fh:
                    tree = ast.parse(fh.read(), filename=path)
                sites |= _sites_in_tree(tree, path)
    return sites


def _offenders(roots):
    """Governed serializer sites that are neither THE floor nor a CLOSED named exemption."""
    return {s for s in _governed_canonical_sites(roots) if s[0] != CANONICAL_HOME and s not in _EXEMPT}


class OneSerializer(unittest.TestCase):
    """A2 -- T-CANONICAL-ONE-SERIALIZER (methods carry the `one_serializer` selector)."""

    def test_one_serializer_guard_holds_over_src(self):
        # the promotion is a real, mechanical label -- not a comment the guard cannot read
        self.assertEqual(canonical.ENGINE_SURFACE, "canonical-serializer")
        sites = _governed_canonical_sites([SRC])
        funcs = {f for _p, f in sites}
        # non-vacuity: the scan actually finds the three known governed-serialization sites
        self.assertTrue({"canonical_hash", "_digest", "digest_of"} <= funcs, sites)
        # and NOTHING governed lives outside {canonical.py} plus the CLOSED dual-audit exemption
        self.assertEqual(_offenders([SRC]), set(), _offenders([SRC]))

    def test_one_serializer_guard_REDS_on_a_planted_second_serializer(self):
        # RW3+: a second GOVERNED canonical serializer planted in a fixture makes the guard RED
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "planted_canon.py"), "w", encoding="utf-8") as fh:
                fh.write("import hashlib, json\n"
                         "def canonical_hash2(x):\n"
                         "    return hashlib.sha256(json.dumps(x, sort_keys=True).encode('utf-8')).hexdigest()\n")
            off = _offenders([SRC, d])
            self.assertTrue(any(f == "canonical_hash2" for _p, f in off), off)  # guard REDS, naming the plant
        self.assertEqual(_offenders([SRC]), set())                              # ... and it was the plant

    def test_one_serializer_guard_does_NOT_trip_on_a_nongoverned_digest(self):
        # RW3-: a test's own digest hashing RAW BYTES / a literal is incidental hashing, not a
        # governed serializer, and must NOT trip the guard
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "incidental.py"), "w", encoding="utf-8") as fh:
                fh.write("import hashlib\n"
                         "def my_digest(b):\n"
                         "    return hashlib.sha256(b).hexdigest()\n"
                         "def fixed():\n"
                         "    return hashlib.sha256(b'literal').hexdigest()\n")
            self.assertEqual(_offenders([SRC, d]), set())

    def test_one_serializer_exemption_list_is_CLOSED_a_third_member_reds(self):
        # tooth (3), RULED U-B: the exemption is the dual-audit family ONLY. A THIRD governed hash
        # site -- even one shaped exactly like a legitimate audit digest -- is a guard RED, never a
        # silent list edit.
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "third_audit.py"), "w", encoding="utf-8") as fh:
                fh.write("import hashlib, json\n"
                         "def digest_of_c(e):\n"
                         "    body = {'seq': e['seq']}\n"
                         "    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]\n")
            off = _offenders([SRC, d])
            self.assertTrue(any(f == "digest_of_c" for _p, f in off), off)


# ============================================================================================
# A3 -- bytes_frozen: promotion is byte-identical to the PRE-EDIT module (RW4)
# ============================================================================================

# Captured from the PRE-EDIT canonical (HEAD 93b419a4, canonical.py sha256 17f00cb2...) BEFORE the
# ENGINE_SURFACE promotion. label -> (canonical_bytes, canonical_hash). RW4/§8-c: a single changed
# byte reds HERE and is a STOP -- a re-seal, not a promotion, NEVER repaired by re-pinning. Every
# hash sealed by store.py:230 / crossing.py:191 rides these exact bytes.
_GOLDEN = {
    "none": (b"n", "sha256:1b16b1df538ba12dc3f97edbb85caa7050d46c148134290feba80f8236c83db9"),
    "true": (b"b1", "sha256:7dc96f776c8423e57a2785489a3f9c43fb6e756876d6ad9a9cac4aa4e72ec193"),
    "false": (b"b0", "sha256:c02c0b965e023abee808f2b548d8d5193a8b5229be6f3121a6f16e2d41a449b3"),
    "int_zero": (b"i0;", "sha256:72c17e08c1ce83294157613ce0a4b0604447971acebfa33550cced8ed515fcac"),
    "int_one": (b"i1;", "sha256:cc7130013527ac2a34de7f05846a80a6abc29cbd03fad13003867866f8c066d4"),
    "int_neg": (b"i-1;", "sha256:6b437068cf68b5615df11bcc6bf6a6decde9e031e5d356bc99e76b308a8f6ed3"),
    "int_big": (b"i9223372036854775808;", "sha256:d904395675ef2590109e37ccb619f7e772eef68472ad07965a4668109173876c"),
    "float_zero": (b"f0.0;", "sha256:39b79eea2e26d78881848458221ca2f36eb094350b5adbb532593ccdfd8743d0"),
    "float_negzero": (b"f0.0;", "sha256:39b79eea2e26d78881848458221ca2f36eb094350b5adbb532593ccdfd8743d0"),
    "float_half": (b"f1.5;", "sha256:47b9497a40c19e1e3fc5fc766be2cd457c0780b5a66b94979e81cef6990f3573"),
    "float_exp": (b"f1000.0;", "sha256:36a50a9a904333e49d7f95624c9ae1b5b89eb4a36399d122b4726b45a282006e"),
    "str_empty": (b"s0:", "sha256:fb912574cecad54c6a0bc75b46172350b6374929d602d5fbcb4ca0ec831fd532"),
    "str_ascii": (b"s3:abc", "sha256:4773c535ad69b2967b18f9178f4dd697e226dd58f8ffd0bab9df42ab112a5e3b"),
    "str_unicode_nfc": (b"s5:caf\xc3\xa9", "sha256:2e16f1720c84d8ae7ed4ad028660841a78fdc0c924a9af62031937c268986d80"),
    "bytes_empty": (b"y0:", "sha256:ad7dfaa8e7af4ae2e5841c0b418b9495fb19c7dd0e2021c508c75592ba47ec7c"),
    "bytes_bin": (b"y3:\x00\x01\xff", "sha256:a5c6498e7fd35c8b2c1f7a3804b6d8b4027252b566b3b833bdbf57ad94518da2"),
    "list_empty": (b"l0:", "sha256:0db2e8105005bd716261bab87ab0dafb638c42e4ff9c41bec5c39a735053dfc8"),
    "list_ints": (b"l3:i1;i2;i3;", "sha256:853373dbb9938804de3840b4b31224939539fcd686750bb66ffc37840db37573"),
    "tuple_ints": (b"l3:i1;i2;i3;", "sha256:853373dbb9938804de3840b4b31224939539fcd686750bb66ffc37840db37573"),
    "dict_empty": (b"d0:", "sha256:ee7d0fbed34482574a32d87dc754abd089afe0eab198e737989e34c14c3fe659"),
    "dict_ab": (b"d2:s1:ai1;s1:bi2;", "sha256:610e5bb9228dd6361ef081138bcf8f1841b118bb88533eee2a3b9c7fd655f501"),
    "dict_ba": (b"d2:s1:ai1;s1:bi2;", "sha256:610e5bb9228dd6361ef081138bcf8f1841b118bb88533eee2a3b9c7fd655f501"),
    "nested": (b"d2:s1:kl2:i1;d2:s1:xs1:ys1:ys1:xs1:zn", "sha256:df53c62c9a81e1cba7946dbc59c22f58ae339b56d5d7c00db9e6d7b9c361eec1"),
    "colon_key": (b"d1:s1:as3:b:c", "sha256:03158f953215bb60315c109efceeae5cc801f0b51e55ff02daba40e5c98860f5"),
    "colon_key2": (b"d1:s3:a:bs1:c", "sha256:4979d0181352f41acb1665b182c1ff1a9f8fe92652fff3f41f74c7bc8ea583b2"),
}

_CORPUS = [
    ("none", None), ("true", True), ("false", False),
    ("int_zero", 0), ("int_one", 1), ("int_neg", -1), ("int_big", 2 ** 63),
    ("float_zero", 0.0), ("float_negzero", -0.0), ("float_half", 1.5), ("float_exp", 1e3),
    ("str_empty", ""), ("str_ascii", "abc"), ("str_unicode_nfc", _CAFE_NFC),
    ("bytes_empty", b""), ("bytes_bin", b"\x00\x01\xff"),
    ("list_empty", []), ("list_ints", [1, 2, 3]), ("tuple_ints", (1, 2, 3)),
    ("dict_empty", {}), ("dict_ab", {"a": 1, "b": 2}), ("dict_ba", {"b": 2, "a": 1}),
    ("nested", {"z": None, "k": [1, {"y": "x", "x": "y"}]}),
    ("colon_key", {"a": "b:c"}), ("colon_key2", {"a:b": "c"}),
]


class BytesFrozen(unittest.TestCase):
    """A3 -- bytes_frozen (method carries the `bytes_frozen` selector)."""

    def test_bytes_frozen_canonical_output_is_unchanged(self):
        for label, value in _CORPUS:
            golden_bytes, golden_hash = _GOLDEN[label]
            self.assertEqual(canonical.canonical_bytes(value), golden_bytes, label)
            self.assertEqual(canonical.canonical_hash(value), golden_hash, label)


if __name__ == "__main__":
    unittest.main()
