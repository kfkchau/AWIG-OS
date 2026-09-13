# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (merkle, fold, gate, deferred effect, recover splice, quantity, param). NON-GOAL: no
# offensive capability of any kind — every test asserts the CORRECT behaviour by function: a dir's own
# metadata seals into its hash, a deferred effect's failure lands on the record, the served fold skips
# every recovered tail, a missing blob raises a named refusal, a malformed quantity refuses at the
# door. Authored from the architect's read + our own code at the cited line; the outside harness was
# NOT read and NOT run. Full declaration: SCOPE-STATEMENT.md.
"""EP-MAINT-OUTSIDE-2 — the red-then-green battery for three fronts:

  A (B11)   a directory's own metadata enters its merkle hash, behind a scheme version so OLD roots
            verify UNCHANGED under their own scheme.
  B (A-1..A-4)  the deferred effect's failure recorded as a row; the served fold skips the UNION of all
            live recover splices' tails; a recover splice landing LIVE re-folds the mount; a NAMED
            exception for a missing blob.
  C (C-1/C-2)  a negative or non-integer declared quantity refuses at the door (the QUANTITIES
            declaration + the door guard); a lawful POSIX negative l_len is normalised before recording.

The I5-instrument arm (C-4, the REJECTED finding class) lives in tests/test_instr_boundary_sweep.py.
"""

import ctypes
import fcntl
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bridge import merkle                                              # noqa: E402
from bridge import checkpoint                                         # noqa: E402
from bridge import custody                                            # noqa: E402
from bridge import replay_snapshot                                    # noqa: E402
from bridge.records_fs import RecordsFS, _Flock                       # noqa: E402
from kernel import compose                                            # noqa: E402
from kernel import erasure                                            # noqa: E402
from kernel import gate as gate_mod                                   # noqa: E402
from kernel import opdefs                                             # noqa: E402
from kernel.errors import OpError                                     # noqa: E402


def _kernel():
    d = tempfile.mkdtemp(prefix="maint2-")
    store, gate, views = compose.build_full_kernel(
        os.path.join(d, "rec.jsonl"), os.path.join(d, "blobs"))[:3]
    return d, store, gate, views


# ==================================================================================================
# FRONT A — B11: a directory's own metadata enters its merkle hash (backward-safe by scheme version)
# ==================================================================================================

class TestB11DirMetadataInHash(unittest.TestCase):

    def _trees(self):
        ta = {"d": {"type": "dir", "perm": "0o755", "nlink": 2},
              "d/f": {"type": "file", "perm": "0o644", "nlink": 1, "size": 3, "sha256": "abc"}}
        tb = {"d": {"type": "dir", "perm": "0o700", "nlink": 2},            # ONLY the dir's own mode
              "d/f": {"type": "file", "perm": "0o644", "nlink": 1, "size": 3, "sha256": "abc"}}
        return ta, tb

    def test_a_dir_mode_enters_hash(self):
        # Under the current scheme (2) a directory whose OWN mode changed moves its merkle hash even
        # when no child moved — the tree seals the directory, not only its contents. Reds against the
        # pre-B11 children-only fold, where the two roots are equal.
        ta, tb = self._trees()
        self.assertNotEqual(merkle.merkle_root(ta), merkle.merkle_root(tb),
                            "a directory's own mode change did not move its merkle hash")
        # LOCALIZATION HOLDS: the divergence names the directory, not the unchanged child leaf.
        self.assertEqual(merkle.localize(ta, tb), ["d"])
        self.assertNotIn("d/f", merkle.localize(ta, tb))

    def test_a_old_scheme_children_only_is_unchanged(self):
        # scheme 1 is the pre-B11 spec (children only): the dir's own metadata is OUT, so a mode-only
        # change moves NO hash — this is what makes every root already on disk verify unchanged.
        ta, tb = self._trees()
        self.assertEqual(merkle.merkle_root(ta, merkle.SCHEME_CHILDREN_ONLY),
                         merkle.merkle_root(tb, merkle.SCHEME_CHILDREN_ONLY))

    def test_a_old_root_verifies_under_its_scheme(self):
        # A checkpoint minted under the OLD scheme (children-only, no merkle_scheme recorded) still
        # verifies — the verifier reads the checkpoint's OWN scheme (absent -> scheme 1) and folds
        # under it. Reds if the verifier folds the recomputed tree under the current default instead.
        d, store, gate, views = _kernel()
        path = os.path.join(d, "rec.jsonl")
        blob_dir = os.path.join(d, "blobs")
        # a NEW cross-attested checkpoint (scheme 2, recorded) verifies clean on an unchanged world
        cp_new = checkpoint.cross_attest(store, path, blob_dir, witness="w", root="/")
        self.assertEqual(cp_new["provenance"]["merkle_scheme"], merkle.SCHEME_DIR_METADATA)
        self.assertTrue(checkpoint.verify(cp_new, path, blob_dir)["merkle_root"])
        # an OLD checkpoint: the SAME tree, its root folded under scheme 1 and NO merkle_scheme
        # recorded (the pre-B11 artifact shape). It must still verify — under ITS scheme.
        cp_old = checkpoint.create(store, path, blob_dir, root="/")
        cp_old["provenance"]["merkle_root"] = merkle.merkle_root(cp_old["tree"],
                                                                 merkle.SCHEME_CHILDREN_ONLY)
        cp_old["provenance"].pop("merkle_scheme", None)                    # the pre-B11 artifact records none
        self.assertEqual(checkpoint.merkle_scheme_of(cp_old), merkle.SCHEME_CHILDREN_ONLY)
        v = checkpoint.verify(cp_old, path, blob_dir)
        self.assertTrue(v["merkle_root"], "an old-scheme root did not verify under its own scheme")
        self.assertNotIn("diverging", v)


# ==================================================================================================
# FRONT B, A-1 — the deferred effect's failure recorded as a row
# ==================================================================================================

class TestA1DeferredEffectFailure(unittest.TestCase):

    def test_a1_deferred_effect_failure_recorded(self):
        # A lawfully-decided act whose IRREVERSIBLE effect RAISES after the decision: the act's own
        # record is never appended (the raise precedes the write), so without A-1 a partial effect
        # stands with nothing on the record. The gate must append a FAILURE ROW under the act's own
        # rule, carrying the exception text AND the effect's partial outcome. Reds against the pre-A-1
        # gate, where the effect's raise leaves no row.
        _d, store, gate, _v = _kernel()

        def handler(actor, params):
            def effect():
                e = RuntimeError("effect blew up after removing 2 of 3 targets")
                e.outcome = ["sha256:removed-a", "sha256:removed-b"]        # what it did before failing (P2)
                raise e
            return {"actor": actor, "action": "SYNTH-EFFECT-OP", "object": "x",
                    "rule_cited": "ROOT-NEG-5",
                    gate_mod.IRREVERSIBLE_EFFECT: effect,
                    "payload": {"note": "a deferred irreversible effect that fails"}}
        gate.register("SYNTH-EFFECT-OP",
                      {"description": "synthetic op whose deferred effect raises",
                       "rules": ["ROOT-NEG-5"], "params": {}}, handler)

        with self.assertRaises(RuntimeError):
            gate.execute("SYNTH-EFFECT-OP", "owner", {})

        rows = [e for e in store.all() if e.get("action") == gate_mod.EFFECT_FAILED]
        self.assertEqual(len(rows), 1, "the deferred effect's failure was not recorded as a row")
        fr = rows[-1]
        self.assertEqual(fr["rule_cited"], "ROOT-NEG-5")                   # under the act's OWN rule (P2)
        self.assertIn("blew up", fr["payload"]["effect_error"])
        self.assertEqual(list(fr["payload"]["outcome"]),
                         ["sha256:removed-a", "sha256:removed-b"])          # the partial state, line by line
        # the act's own record was NOT appended — the effect failed, so no success stands
        self.assertEqual([e for e in store.all() if e.get("action") == "SYNTH-EFFECT-OP"], [])

    def test_a1_a_succeeding_deferred_effect_still_appends_the_act(self):
        # The complement: an effect that does NOT raise leaves the act's own record appended and NO
        # failure row — the failure path is additive, never a change to the success path.
        _d, store, gate, _v = _kernel()

        def handler(actor, params):
            return {"actor": actor, "action": "SYNTH-OK-OP", "object": "y",
                    "rule_cited": "ROOT-NEG-5",
                    gate_mod.IRREVERSIBLE_EFFECT: (lambda: ["did the thing"]),
                    "payload": {"note": "ok"}}
        gate.register("SYNTH-OK-OP",
                      {"description": "synthetic op whose deferred effect succeeds",
                       "rules": ["ROOT-NEG-5"], "params": {}}, handler)
        gate.execute("SYNTH-OK-OP", "owner", {})
        self.assertEqual(len([e for e in store.all() if e.get("action") == "SYNTH-OK-OP"]), 1)
        self.assertEqual([e for e in store.all() if e.get("action") == gate_mod.EFFECT_FAILED], [])


# ==================================================================================================
# FRONT B, A-2 — the served fold skips the UNION of all live recover splices' tails
# ==================================================================================================

class TestA2RecoverTailUnion(unittest.TestCase):

    def _file(self, seq, path):
        return {"seq": seq, "actor": "owner", "action": "FILE-CREATE", "object": path,
                "rule_cited": "ROOT-NEG-5", "record_time": seq,
                "payload": {"path": path, "node_type": "file", "perm": "644"}}

    def _splice(self, seq, target_seq):
        return {"seq": seq, "actor": "owner", "action": erasure.RECOVER_OP, "object": "sha256:x",
                "rule_cited": "RECOVER-LAW", "record_time": seq,
                "payload": {"kind": erasure.RECOVER_RECORD, erasure.TARGET_SEQ: target_seq,
                            erasure.TARGET_HEAD: "sha256:x", erasure.CHECKPOINT_REF: "cp"}}

    def _records(self):
        # Two recoveries where the SECOND woke to a point AFTER the first's splice — two disjoint
        # broken tails. The served fold must skip BOTH.
        return [
            self._file(1, "/keep"),        # sound, survives
            self._file(2, "/broken1"),     # broken tail 1
            self._splice(3, 1),            # recover to seq 1 -> skips (1,3]: /broken1 + this splice
            self._file(4, "/mid"),         # after splice 1, sound
            self._file(5, "/broken2"),     # broken tail 2
            self._splice(6, 4),            # recover to seq 4 (AFTER splice 1) -> skips (4,6]: /broken2
        ]

    def test_a2_two_recoveries_skip_union(self):
        names = set(custody.fold(self._records()).names)
        norm = custody._norm
        # both sound points survive
        self.assertIn(norm("/keep"), names)
        self.assertIn(norm("/mid"), names)
        # BOTH broken tails are skipped — the first's is the one the pre-A-2 latest-only fold replayed
        self.assertNotIn(norm("/broken1"), names,
                         "the first recovery's broken tail was replayed — the fold skipped only the latest")
        self.assertNotIn(norm("/broken2"), names)

    def test_a2_recovered_points_returns_both_live_splices(self):
        pts = erasure.recovered_points(self._records())
        self.assertEqual([p["seq"] for p in pts], [3, 6])                  # both live, in seq order
        # the singular helper is UNCHANGED (still the latest) — its callers are untouched
        self.assertEqual(erasure.recovered_point(self._records())["seq"], 6)

    def test_a2_a_superseded_earlier_splice_is_not_live(self):
        # A later recovery that woke BEFORE an earlier splice re-adjudicates it: the earlier splice's
        # own record sits inside the later's broken tail, so it is superseded and NOT live.
        recs = [self._file(1, "/a"), self._file(2, "/b"), self._splice(3, 2),   # splice at 3 (target 2)
                self._file(4, "/c"), self._splice(5, 1)]                          # splice at 5 wakes to 1 (< 3)
        pts = erasure.recovered_points(recs)
        self.assertEqual([p["seq"] for p in pts], [5],
                         "the earlier splice was superseded by a later recovery that woke before it")


# ==================================================================================================
# FRONT B, A-3 — a recover splice landing on a LIVE mount re-folds without a remount
# ==================================================================================================

class TestA3LiveRecoverRefolds(unittest.TestCase):

    def test_a3_live_recover_refolds(self):
        d, store, gate, views = _kernel()
        blobs = None
        adapter = RecordsFS(store, gate, views, blobs)

        def append_file(path):
            return store._append({"actor": "owner", "action": "FILE-CREATE", "object": path,
                                  "rule_cited": "ROOT-NEG-5",
                                  "payload": {"path": path, "node_type": "file", "perm": "644"}})
        keep = append_file("/keepfile")
        broken = append_file("/brokenfile")
        norm = custody._norm
        # both are live in the served state (the incremental apply put them there)
        self.assertIn(norm("/brokenfile"), set(adapter.state.names))

        # a recover splice lands LIVE, waking to keep's seq -> its tail (keep_seq, splice_seq] holds
        # /brokenfile. Before A-3 the incremental apply could not undo it; A-3 re-folds on the record.
        store._append({"actor": "owner", "action": erasure.RECOVER_OP, "object": "sha256:x",
                       "rule_cited": "RECOVER-LAW",
                       "payload": {"kind": erasure.RECOVER_RECORD,
                                   erasure.TARGET_SEQ: keep["seq"], erasure.TARGET_HEAD: "sha256:x",
                                   erasure.CHECKPOINT_REF: "cp"}})

        names = set(adapter.state.names)                                  # NO remount — the live state
        self.assertIn(norm("/keepfile"), names)
        self.assertNotIn(norm("/brokenfile"), names,
                         "a recover splice on a live mount was not consumed until a remount (A-3)")


# ==================================================================================================
# FRONT B, A-4 — a NAMED exception for a missing blob (assertable by a caller)
# ==================================================================================================

class TestA4MissingBlobNamedException(unittest.TestCase):

    def test_a4_missing_blob_named_exception(self):
        d = tempfile.mkdtemp(prefix="maint2-a4-")
        record_path = os.path.join(d, "rec.jsonl")
        blob_dir = os.path.join(d, "blobs")
        os.makedirs(blob_dir, exist_ok=True)
        # a record naming content bytes that are neither departed nor present — a missing blob
        recs = [
            {"seq": 1, "actor": "owner", "action": "FILE-MKDIR", "object": "/tree",
             "payload": {"path": "/tree", "node_type": "dir", "perm": "755"}},
            {"seq": 2, "actor": "owner", "action": "FILE-MKDIR", "object": "/tree/row1",
             "payload": {"path": "/tree/row1", "node_type": "dir", "perm": "755"}},
            {"seq": 3, "actor": "owner", "action": "FILE-CREATE", "object": "/tree/row1/f",
             "payload": {"path": "/tree/row1/f", "node_type": "file", "perm": "644"}},
            {"seq": 4, "actor": "owner", "action": "FILE-WRITE", "object": "/tree/row1/f",
             "payload": {"path": "/tree/row1/f", "content_hash": "sha256:" + "de" * 32, "length": 5}},
        ]
        with open(record_path, "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r) + "\n")
        # a caller can CATCH the named refusal (I2's path) — assertable, not a bare CLI exit
        with self.assertRaises(replay_snapshot.MissingBlobError):
            replay_snapshot.snapshot(record_path, blob_dir, row_id="row1")
        # and it stays a SystemExit subclass, so the CLI idiom and any `except SystemExit` are unchanged
        self.assertTrue(issubclass(replay_snapshot.MissingBlobError, SystemExit))


# ==================================================================================================
# FRONT C, C-1 — the QUANTITIES declaration + the door's quantity guard
# ==================================================================================================

class TestC1QuantityGuard(unittest.TestCase):

    def _refuses(self, gate, store, op, params):
        # The refusal is a RECORDED op-refused row citing AR-2 — found among the records the call added
        # (the dual-audit mirror lands its own row after, so it is not necessarily store.all()[-1]).
        n = len(store.all())
        with self.assertRaises(OpError):
            gate.execute(op, "owner", params)
        added = store.all()[n:]
        refusals = [e for e in added if e.get("action") == "op-refused"
                    and e.get("rule_cited") == "AR-2"
                    and (e.get("payload") or {}).get("op") == op]
        self.assertTrue(refusals, "%s did not record an AR-2 refusal row" % op)

    def test_c1_negative_quantity_refused(self):
        # Each of the five negative-quantity ops refuses a negative declared quantity AT THE DOOR
        # (AR-2, with a row), before the handler runs. Reds without the QUANTITIES declaration + guard,
        # where these five silently ACCEPT the negative (the I5 finding this closes).
        _d, store, gate, _v = _kernel()
        self._refuses(gate, store, "AMEND-BUDGET", {"holder": "owner", "ceiling": -1})
        self._refuses(gate, store, "MEM-GRANT", {"region": "r", "size": -5})
        self._refuses(gate, store, "FILE-LOCK", {"path": "/f", "ltype": "read", "length": -4})
        self._refuses(gate, store, "FILE-UNLOCK", {"path": "/f", "length": -4})
        self._refuses(gate, store, "FILE-TRUNCATE", {"path": "/f", "content": "x", "length": -9})

    def test_c1_non_integer_quantity_refused_bool_and_float(self):
        # A quantity is an INT: a boolean (an int in Python, excluded FIRST) and a float both refuse.
        _d, store, gate, _v = _kernel()
        self._refuses(gate, store, "AMEND-BUDGET", {"holder": "owner", "ceiling": True})
        self._refuses(gate, store, "AMEND-BUDGET", {"holder": "owner", "ceiling": 1.5})

    def test_c1_a_valid_quantity_is_admitted(self):
        # The guard DISCRIMINATES: a non-negative integer passes the door (the handler runs).
        _d, store, gate, _v = _kernel()
        gate.execute("AMEND-BUDGET", "SYSTEM", {"holder": "owner", "ceiling": 100})
        got = [e for e in store.all() if e.get("action") == "AMEND-BUDGET"]
        self.assertTrue(got, "a lawful non-negative ceiling was not admitted")

    def test_c1_undeclared_param_kind_refused_at_definition(self):
        # DEFINITION time: a `param_kinds` entry naming a param the op does not declare, or naming a
        # kind outside the closed set, is a malformed definition (AR-2). `a` is CLASSIFIED (structural)
        # so the vocabulary door passes it — the ONLY malformation is the param_kinds entry.
        _d, store, gate, _v = _kernel()
        undeclared = {"description": "param_kinds naming a param the op does not declare",
                      "law_cited": "ROOT-NEG-5", "params": {"a": "required"},
                      "structural_params": ["a"], "param_kinds": {"not_a_param": "quantity"}}
        with self.assertRaises(OpError):
            gate.execute("CREATE-OP", "owner", {"name": "BAD-PK-PARAM-OP", "definition": undeclared})
        unknown_kind = {"description": "param_kinds naming a kind outside the closed set",
                        "law_cited": "ROOT-NEG-5", "params": {"a": "required"},
                        "structural_params": ["a"], "param_kinds": {"a": "not_a_kind"}}
        with self.assertRaises(OpError):
            gate.execute("CREATE-OP", "owner", {"name": "BAD-PK-KIND-OP", "definition": unknown_kind})
        # the well-formed twin (a declared param, a known kind) is admitted — R1 both ways
        good_def = {"description": "param_kinds naming a declared param and a known kind",
                    "law_cited": "ROOT-NEG-5", "params": {"a": "required"},
                    "param_kinds": {"a": "quantity"}, "structural_params": ["a"]}
        gate.execute("CREATE-OP", "owner", {"name": "GOOD-PK-OP", "definition": good_def})
        self.assertIn("GOOD-PK-OP", gate.ops)
        self.assertEqual(gate.ops["GOOD-PK-OP"]["meta"].get(opdefs.PARAM_KINDS), {"a": "quantity"})


# ==================================================================================================
# FRONT C, C-3 — the door refuses a malformed text value BEFORE the group-commit crash
# ==================================================================================================

class TestC3MalformedTextRefused(unittest.TestCase):

    def _refuses_at_door(self, gate, store, op, params, pname):
        n = len(store.all())
        with self.assertRaises(OpError):
            gate.execute(op, "owner", params)
        added = store.all()[n:]
        refusals = [e for e in added if e.get("action") == "op-refused"
                    and e.get("rule_cited") == "AR-2"
                    and (e.get("payload") or {}).get("op") == op]
        self.assertTrue(refusals, "%s.%s did not record an AR-2 refusal row" % (op, pname))
        # the store is NOT broken — the refusal landed BEFORE the group commit that a raw bytes value
        # would have crashed (the point of C-3: refuse before BatchFailed, never after).
        self.assertFalse(getattr(store, "_broken", None), "%s crashed the store instead of refusing" % op)

    def test_c3_malformed_text_refused(self):
        # A `text`-kind param handed a raw non-UTF-8 (bytes) value refuses at the door (AR-2, a row),
        # never crashes the record write. Reds without C-3, where the raw bytes reach the group commit
        # (json.dumps -> BatchFailed). Driven over a definition-born op (DICT-ENTRY) and the one
        # code-registered op in the class (CREATE-INFO).
        _d, store, gate, _v = _kernel()
        self._refuses_at_door(gate, store, "DICT-ENTRY",
                              {"term": b"\xff\xfe\x00\x80", "entity_kind": "x"}, "term")
        _d2, store2, gate2, _v2 = _kernel()
        self._refuses_at_door(gate2, store2, "CREATE-INFO", {"content": b"\xff\xfe"}, "content")

    def test_c3_a_utf8_text_value_is_admitted(self):
        # The guard DISCRIMINATES: a valid UTF-8 string (including a non-ASCII one) is admitted.
        _d, store, gate, _v = _kernel()
        gate.execute("DICT-ENTRY", "owner", {"term": "café — 汉字", "entity_kind": "x"})
        self.assertTrue([e for e in store.all() if e.get("action") == "DICT-ENTRY"])

    def test_c3_a_bytes_kind_param_is_exempt(self):
        # A `bytes`-kind param is EXEMPT from the text guard (a byte payload lawfully carries non-UTF-8):
        # the door does NOT refuse it (:3520). It is unaffected — the door adds no AR-2 refusal for it.
        _d, store, gate, _v = _kernel()
        self.assertEqual(gate.ops["FILE-XATTR-SET"]["meta"]["param_kinds"].get("value"), "bytes")
        n = len(store.all())
        try:
            gate.execute("FILE-XATTR-SET", "owner",
                         {"path": "/f", "name": "user.x", "value": b"\xff\xfe"})
        except OpError as e:
            # if it refuses, it must NOT be the text-kind door refusal (no "must be a UTF-8 string")
            self.assertNotIn("must be a UTF-8 string", str(e))
        except Exception:
            pass  # a downstream crash on a raw byte payload is the pinned residual, not a door refusal
        # no AR-2 text refusal row was added for the bytes-kind param
        text_refusals = [e for e in store.all()[n:] if e.get("action") == "op-refused"
                         and "must be a UTF-8 string" in ((e.get("payload") or {}).get("message") or "")]
        self.assertEqual(text_refusals, [], "a bytes-kind param was refused by the text guard")


# ==================================================================================================
# FRONT C, C-2 — a lawful POSIX negative l_len is normalised before recording
# ==================================================================================================

class TestC2NegativeLLenNormalised(unittest.TestCase):

    def test_c2_negative_llen_normalised(self):
        d, store, gate, views = _kernel()
        adapter = RecordsFS(store, gate, views, None)
        store._append({"actor": "owner", "action": "FILE-CREATE", "object": "/f",
                       "rule_cited": "ROOT-NEG-5",
                       "payload": {"path": "/f", "node_type": "file", "perm": "644"}})

        # a POSIX lock with a NEGATIVE l_len: it names the range ENDING at the offset — [start+len, start)
        fl = _Flock(l_type=fcntl.F_WRLCK, l_whence=os.SEEK_SET, l_start=100, l_len=-40, l_pid=0)
        adapter.lock("/f", 999, fcntl.F_SETLK, ctypes.addressof(fl))

        locks = [e for e in store.all() if e.get("action") == "FILE-LOCK"]
        self.assertTrue(locks, "the lock was not recorded")
        p = locks[-1]["payload"]
        # normalised to (start+len, -len) = (60, 40): a well-formed range the fold reads correctly.
        # Reds without C-2, where the record carries l_len = -40 and `_overlaps` inverts on it.
        self.assertEqual(p["start"], 60)
        self.assertEqual(p["length"], 40)
        # _overlaps on the STORED (normalised) range is correct: [60,100) overlaps [50,70), not [0,60)
        self.assertTrue(custody._overlaps(p["start"], p["length"], 50, 20))
        self.assertFalse(custody._overlaps(p["start"], p["length"], 0, 60))


if __name__ == "__main__":
    unittest.main()
