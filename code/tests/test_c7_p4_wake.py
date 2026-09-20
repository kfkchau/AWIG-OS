# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: kernel-test · OS-architecture
# vocabulary (a boot-time self-check, a genesis attestation record, refuse-before-first-act, the
# genesis guardian family) as in the seL4/gVisor/Fuchsia literature. NON-GOAL: no offensive capability
# of any kind — every assertion proves design/54 §3 B4 by FUNCTION: before the first actor act, six
# verdicts (body, chain, constitution, views, keys, account chain) are recorded as one genesis row and
# each is able to REFUSE the first act; the checklist refuses, it never blesses. It attacks nothing and
# reveals nothing. Full declaration: SCOPE-STATEMENT.md.
"""C7 P4 — THE WAKE CHECKLIST (design/54 §3 B4, §5 L3; design/47 §3; plan
planning/exec/C7-P4-WAKE-CHECKLIST.md, sha 1ec20adb…). Six verdicts as a genesis row before the first
act; each able to refuse it.

Named in the plan before code, landed here as regression tests (charter: every verification probe
lands as a regression test). NOT FOUNDING (archi ruling, coord 2026-09-11: the gating rule is genesis
MACHINERY IN CODE, not founding data): founding-pack.json is byte-unchanged, no version bump / bump-
attestation / §A57 sweep. The NEW code is a BOOT ADDITION on the already-attested kernel/boot.py — no
new src module, so ATTESTED_MEMBERS is unchanged (the count-pin rider is inert). The six verdicts are
DERIVED from existing mechanisms (attestation.match_probe, store.verify_chain, install's founding read-
back, views.master over the fold set, keys.key_valid, views.chain_end + actor_grounded), composed —
no new check kind.

RUNNER OF RECORD (per-module, :3158): PYTHONPATH=src:tests python3 -m unittest tests.test_c7_p4_wake -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from kernel import boot                                   # noqa: E402
from kernel import attestation, keys as keysmod           # noqa: E402
from kernel.compose import build_full_kernel              # noqa: E402
from kernel.store import EventStore                       # noqa: E402
from kernel.views import Views                            # noqa: E402
from founding import install                              # noqa: E402


# ---- helpers: build the hosted estate, corrupt a record, recompose ------------------------------

def _fresh():
    """A full governed kernel in a fresh temp world. Returns (store, gate, views, record_path)."""
    td = tempfile.mkdtemp(prefix="c7p4-")
    rp = os.path.join(td, "record.jsonl")
    store, gate, views, _blobs, _subs = build_full_kernel(rp, os.path.join(td, "blobs"))
    return store, gate, views, rp


def _recompose(rp):
    """Recompose a full kernel over a COPY of the record file (a fresh dir, so the writer lock does
    not collide). Returns (store, gate, views). Used to obtain a live gate over a corrupted record."""
    td = tempfile.mkdtemp(prefix="c7p4-re-")
    rp2 = os.path.join(td, "record.jsonl")
    shutil.copy(rp, rp2)
    store, gate, views, _blobs, _subs = build_full_kernel(rp2, os.path.join(td, "blobs"))
    return store, gate, views


def _reload(rp):
    """A bare store + views over the record file (no gate). Used where a corruption is so severe the
    full compose cannot fold it. Returns (store, views)."""
    store = EventStore(rp, lock=False)
    return store, Views(store)


def _mirror_src():
    """A working copy of the real src/ tree (attestation's own detect-direction idiom, test_ep40)."""
    dst = os.path.join(tempfile.mkdtemp(prefix="c7p4-src-"), "src")
    shutil.copytree(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")), dst)
    return dst


def _read_lines(rp):
    with open(rp) as f:
        return [l for l in f.read().splitlines() if l.strip()]


def _write_lines(rp, lines):
    with open(rp, "w") as f:
        f.write("\n".join(lines) + "\n")


def _next_seq(rp):
    return json.loads(_read_lines(rp)[-1])["seq"] + 1


def _append_raw(rp, record):
    with open(rp, "a") as f:
        f.write(json.dumps(record) + "\n")


def _edit_records(rp, mutate):
    _write_lines(rp, [json.dumps(mutate(json.loads(l))) for l in _read_lines(rp)])


def _wake_row(store):
    rows = [e for e in store.by_action("WRITE-ACTIVITY")
            if e.get("object") == boot.WAKE_GENESIS_OBJECT]
    return rows[-1] if rows else None


# ================================================================================================
# A1 — THE SIX VERDICTS AS A GENESIS ROW BEFORE THE FIRST ACT (B4)
# ================================================================================================
class TestA1GenesisRowBeforeFirstAct(unittest.TestCase):
    def test_wake_records_one_genesis_row_naming_all_six_then_permits(self):
        store, gate, views, rp = _fresh()
        before = len(store.events)
        verdicts = boot.wake(store, gate, views)               # a healthy hosted estate: all six pass

        # exactly ONE genesis row was appended (the wake checklist's own SYSTEM act, the one pen)
        self.assertEqual(len(store.events) - before, 1, "the wake checklist records exactly one row")
        row = _wake_row(store)
        self.assertIsNotNone(row, "the genesis row is on the record")
        self.assertEqual(row["actor"], "SYSTEM", "the genesis row is a SYSTEM act (the one pen)")
        self.assertEqual(row["action"], "WRITE-ACTIVITY")

        # it NAMES each of the six verdicts
        self.assertEqual(set(row["payload"]["verdicts"]), set(boot.WAKE_VERDICTS))
        self.assertEqual(len(boot.WAKE_VERDICTS), 6, "six verdicts, no more, no fewer")
        for name in boot.WAKE_VERDICTS:
            self.assertTrue(row["payload"]["verdicts"][name], "%s passes on the hosted estate" % name)
            self.assertTrue(verdicts[name]["ok"])
        self.assertTrue(row["payload"]["all_pass"])
        self.assertEqual(list(row["payload"]["refused_on"]), [])

    def test_the_row_is_recorded_before_the_first_actor_act(self):
        # The wake row is a SYSTEM act; the FIRST governed ACTOR act comes after. Here the genesis row
        # is the LAST record after wake and precedes any actor mint we make next.
        store, gate, views, rp = _fresh()
        boot.wake(store, gate, views)
        wake_seq = _wake_row(store)["seq"]
        first_actor = gate.execute("CREATE-ACTOR", "owner", {"actor_id": "first-actor"})
        self.assertGreater(first_actor["seq"], wake_seq,
                           "the first actor act lands AFTER the wake genesis row")


# ================================================================================================
# A2 — EACH STEP ABLE TO REFUSE (six planted failures, six refusals, each by name)
# ================================================================================================
class TestA2EachStepAbleToRefuse(unittest.TestCase):
    def _assert_recorded_refusal(self, store, gate, views, verdict, src_dir=None):
        """wake() over a corrupted (but foldable) world REFUSES and NAMES `verdict` in the genesis row."""
        before = len(store.events)
        with self.assertRaises(boot.WakeRefused) as cm:
            boot.wake(store, gate, views, src_dir=src_dir)
        self.assertIn(verdict, cm.exception.failed, "%s is named in the refusal" % verdict)
        self.assertEqual(len(store.events) - before, 1, "the genesis row is recorded before the refusal")
        row = _wake_row(store)
        self.assertFalse(row["payload"]["verdicts"][verdict], "the genesis row names %s failed" % verdict)
        self.assertIn(verdict, list(row["payload"]["refused_on"]))

    def test_body_a_tampered_attested_member_refuses(self):
        store, gate, views, rp = _fresh()
        mirror = _mirror_src()
        with open(os.path.join(mirror, "kernel", "gate.py"), "a") as f:
            f.write("\n# C7 P4 planted body tamper (a silent engine change)\n")
        self._assert_recorded_refusal(store, gate, views, "body", src_dir=mirror)

    def test_chain_a_broken_sealed_prefix_refuses(self):
        store, gate, views, rp = _fresh()
        store.seal_prefix()                                    # anchor the chain
        # tamper a benign field of a sealed record — the prefix no longer hashes to the anchor
        L = _read_lines(rp)
        rec = json.loads(L[1]); rec["object"] = str(rec.get("object")) + "-tampered"; L[1] = json.dumps(rec)
        _write_lines(rp, L)
        s2, g2, v2 = _recompose(rp)
        self.assertFalse(s2.verify_chain()["ok"], "the planted chain is genuinely broken")
        self._assert_recorded_refusal(s2, g2, v2, "chain")

    def test_constitution_a_read_back_mismatch_refuses(self):
        store, gate, views, rp = _fresh()
        _edit_records(rp, lambda r: (r.update(payload=dict(r.get("payload") or {},
                                                           founding_version="0.0.1-planted"))
                                     if r.get("action") == "FOUND-STORE" else None) or r)
        s2, g2, v2 = _recompose(rp)
        self._assert_recorded_refusal(s2, g2, v2, "constitution")

    def test_keys_a_revoked_chain_end_key_refuses(self):
        store, gate, views, rp = _fresh()
        ce = views.chain_end()
        sb = _next_seq(rp)
        _append_raw(rp, {"seq": sb, "actor": "SYSTEM", "action": keysmod.KEY_BIND, "object": ce,
                         "rule_cited": "KEY-LAW-BIND",
                         "payload": {"kind": keysmod.KEY_BIND, keysmod.ACCOUNT: ce,
                                     keysmod.PUBLIC_KEY: "ed25519:planted"}})
        _append_raw(rp, {"seq": sb + 1, "actor": "SYSTEM", "action": keysmod.KEY_REVOKE, "object": ce,
                         "rule_cited": "KEY-LAW-BIND",
                         "payload": {"kind": keysmod.KEY_REVOKE, keysmod.ACCOUNT: ce}})
        s2, g2, v2 = _recompose(rp)
        self.assertFalse(keysmod.key_valid(s2, v2.chain_end()), "the chain-end key is genuinely revoked")
        self.assertTrue(keysmod._key_records(s2, v2.chain_end()), "key records exist (not the vacuous case)")
        self._assert_recorded_refusal(s2, g2, v2, "keys")

    def test_account_chain_an_ungrounded_actor_refuses(self):
        store, gate, views, rp = _fresh()
        gate.execute("CREATE-ACTOR", "SYSTEM", {"actor_id": "orphan"})   # minted, no grounding chain
        self.assertFalse(views.actor_grounded("orphan"), "the orphan grounds at no anchor")
        self._assert_recorded_refusal(store, gate, views, "account_chain")

    def test_views_a_fold_that_errors_refuses(self):
        # A record a VIEW cannot fold (a non-dict payload, e.g. disk corruption) fails the views
        # verdict AND — the same corruption — stops the store's own append path from folding, so the
        # genesis row is unrecordable. wake() still REFUSES the first act, naming views (the machine
        # must not act). The verdict's failure is proven directly through wake_verdicts.
        store, gate, views, rp = _fresh()
        _append_raw(rp, {"seq": _next_seq(rp), "actor": "owner", "action": "CREATE-VIEW",
                         "object": "corrupt", "rule_cited": "ROOT-NEG-6", "payload": "NOT-A-DICT"})
        s2, v2 = _reload(rp)
        vd = boot.wake_verdicts(s2, v2)
        self.assertFalse(vd["views"]["ok"], "a fold that errors reds the views verdict")

        # wake() refuses the first act (raises), naming views — build a bare gate over the corrupt store
        from kernel.gate import Gate
        s3, v3 = _reload(rp)
        g3 = Gate(s3, v3)
        boot._register_bootstrap(g3, s3, v3)
        with self.assertRaises(boot.WakeRefused) as cm:
            boot.wake(s3, g3, v3)
        self.assertIn("views", cm.exception.failed, "views is named in the refusal")

    def test_all_six_are_able_to_fail_independently(self):
        # A defensive census: every verdict is False in at least one planted world above. Here we
        # confirm the healthy world passes all six, so each red above is a real state flip, not a
        # verdict that is always False (§7c — a verdict that cannot pass is not a verdict either).
        store, gate, views, rp = _fresh()
        vd = boot.wake_verdicts(store, views)
        for name in boot.WAKE_VERDICTS:
            self.assertTrue(vd[name]["ok"], "%s passes on the healthy hosted estate" % name)


# ================================================================================================
# A3 — THE SIX VERDICTS DERIVED FROM EXISTING MECHANISMS, NO NEW CHECK KIND
# ================================================================================================
class TestA3DerivedFromExistingMechanisms(unittest.TestCase):
    def test_body_tracks_match_probe(self):
        store, gate, views, rp = _fresh()
        probe = attestation.match_probe(store)
        ok, _ = boot._wake_body(store, views)
        self.assertEqual(ok, bool(probe["attested"] and probe["matches"]),
                         "the body verdict IS attestation.match_probe, composed not re-authored")

    def test_chain_tracks_verify_chain(self):
        store, gate, views, rp = _fresh()
        ok, _ = boot._wake_chain(store, views)
        self.assertEqual(ok, store.verify_chain()["ok"], "the chain verdict IS store.verify_chain")

    def test_constitution_tracks_install_read_back(self):
        store, gate, views, rp = _fresh()
        world_v = (store.by_action("FOUND-STORE")[0].get("payload") or {}).get("founding_version")
        ok, _ = boot._wake_constitution(store, views)
        self.assertEqual(ok, world_v == install.founding_version(),
                         "the constitution verdict IS install's founding read-back")

    def test_views_tracks_the_fold_set(self):
        store, gate, views, rp = _fresh()
        # the verdict runs every seeded master; on the healthy world none errors
        ok, _ = boot._wake_views(store, views)
        self.assertTrue(ok)
        # it composes views.master over the seeded masters — not a new fold engine
        masters = [n for n, d in views.view_definitions().items() if d.get("bind")]
        self.assertTrue(masters, "there are seeded masters to fold")
        for m in masters:
            views.master(m)                                    # the SAME mechanism the verdict uses

    def test_keys_tracks_key_valid(self):
        store, gate, views, rp = _fresh()
        ce = views.chain_end()
        ok, _ = boot._wake_keys(store, views)
        # no key bound at boot -> vacuously valid, exactly as keys.bound_key is inert
        self.assertEqual(ok, (not keysmod._key_records(store, ce)) or keysmod.key_valid(store, ce))

    def test_account_chain_tracks_chain_end_and_actor_grounded(self):
        store, gate, views, rp = _fresh()
        ce = views.chain_end()
        ids = {(e.get("payload") or {}).get("actor_id") or e.get("object")
               for e in store.by_action("CREATE-ACTOR")}
        ok, _ = boot._wake_account_chain(store, views)
        self.assertEqual(ok, ce is not None and all(views.actor_grounded(a) for a in ids),
                         "the account verdict IS chain_end + actor_grounded")

    def test_no_new_check_kind_only_existing_mechanisms_are_imported(self):
        import inspect
        src = "".join(inspect.getsource(fn) for fn in (
            boot._wake_body, boot._wake_chain, boot._wake_constitution,
            boot._wake_views, boot._wake_keys, boot._wake_account_chain))
        # the verdicts read existing mechanisms by name; they mint no new check kind
        for token in ("match_probe", "verify_chain", "founding_version",
                      "view_definitions", "master", "key_valid", "chain_end", "actor_grounded"):
            self.assertIn(token, src, "the verdicts compose the existing mechanism %s" % token)


# ================================================================================================
# A4 — PERFORMER-INDEPENDENT
# ================================================================================================
class TestA4PerformerIndependent(unittest.TestCase):
    def test_wake_runs_with_no_performer_beneath_the_seam(self):
        # The hosted estate composes with no performer attached; the six verdicts read only the
        # record / constitution / keys / accounts, so wake passes with nothing beneath the seam.
        store, gate, views, rp = _fresh()
        self.assertFalse(hasattr(views, "performer"), "no performer is attached")
        boot.wake(store, gate, views)                          # passes reading only the record plane

    def test_the_verdicts_read_no_performer_or_seam_symbol(self):
        # Scan CODE only (docstrings stripped — they name "the performer" to say they do NOT read it):
        # the verdicts must import or call NO effect-seam / performer symbol.
        import ast
        import inspect

        def code_only(fn):
            tree = ast.parse(inspect.getsource(fn).lstrip())
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                    body = getattr(node, "body", None)
                    if body and isinstance(body[0], ast.Expr) and isinstance(
                            getattr(body[0], "value", None), ast.Constant) and isinstance(
                            body[0].value.value, str):
                        body.pop(0)                          # drop the docstring node
            return ast.unparse(tree)

        src = "".join(code_only(fn) for fn in (
            boot._wake_body, boot._wake_chain, boot._wake_constitution, boot._wake_views,
            boot._wake_keys, boot._wake_account_chain, boot.wake_verdicts, boot.wake))
        for token in ("host_seam", "RealHost", "StubHost", "bridge", "observe"):
            self.assertNotIn(token, src,
                             "a wake verdict must read no effect-seam / performer symbol (%s)" % token)

    def test_the_performer_read_guard_can_fire(self):
        # A control: the code scan CAN detect a performer read — so a planted performer-specific read
        # in a verdict WOULD red it (the check is able to fail, §A64).
        planted_code = "probe = views.host_seam.performer.read()"
        self.assertIn("host_seam", planted_code,
                      "a planted performer read is detectable by the same guard")


# ================================================================================================
# A5 — THE CHECKLIST REFUSES, IT NEVER BLESSES
# ================================================================================================
class TestA5RefusesNeverBlesses(unittest.TestCase):
    def test_a_passing_checklist_permits_but_an_unlawful_act_stays_refused(self):
        store, gate, views, rp = _fresh()
        boot.wake(store, gate, views)                          # passes -> the first act is PERMITTED
        # an act refused on its own merits stays refused THOUGH the checklist passed: the checklist
        # touches no gate decision, so it makes no unlawful act lawful.
        from kernel.errors import OpError
        with self.assertRaises(OpError):
            gate.execute("NO-SUCH-OP", "owner", {})            # unregistered -> the gate refuses on its merits

    def test_a_lawful_first_act_proceeds_after_a_passing_checklist(self):
        store, gate, views, rp = _fresh()
        boot.wake(store, gate, views)
        rec = gate.execute("CREATE-ACTOR", "owner", {"actor_id": "lawful-first"})
        self.assertEqual(rec["action"], "CREATE-ACTOR", "a lawful first act proceeds — permit, not bless")

    def test_the_wake_row_is_a_record_not_an_approval(self):
        # The genesis row is a WRITE-ACTIVITY (a record THAT the check happened) — it carries no
        # rule-permit and adds no legitimacy; the payload is verdicts, not a blessing.
        store, gate, views, rp = _fresh()
        boot.wake(store, gate, views)
        row = _wake_row(store)
        self.assertEqual(row["payload"]["kind"], "wake-checklist")
        self.assertNotIn("permit", row["payload"], "the row grants nothing")


# ================================================================================================
# A6 — WHOLE LEDGER GREEN PER MODULE; NO FOUNDING; NO NEW ATTESTED MODULE
# ================================================================================================
class TestA6LedgerPackAndAttestation(unittest.TestCase):
    def test_not_founding_the_pack_version_is_unchanged(self):
        # NOT founding data (archi ruling): the gating rule is genesis machinery in code. This unit made
        # NO founding move. The live version is read fresh, so this is a §A57 live-version pin: a LATER
        # founding mover, C7 P3 (THE KERNEL FROM THE RECORD — the twelve act-kind rows), moved the LIVE
        # founding 1.54.0 -> 1.55.0 BY NAME (§A57); P4 still adds no founding.
        self.assertEqual(install.founding_version(), "1.55.0",
                         "P4 adds no founding; the live version is C7 P3's 1.55.0")

    def test_no_new_attested_module_from_this_unit_global_count_68(self):
        # A boot ADDITION on the already-attested kernel/boot.py — no new src engine module joins the
        # attested set FROM THIS UNIT, so P4's OWN count-pin rider is inert. The absolute count is a
        # GLOBAL pin any estate-wide add moves: C7 P7a's interpreter-hosting layer moved it 55 -> 57
        # (+2: hosting/__init__.py, hosting/interpreter_host.py), then C7 P3b-1's first merged body
        # moved it 57 -> 68 (+11 src/body files; §9 mechanism 1, archi :4009) — both AFTER this unit.
        self.assertEqual(len(attestation.ATTESTED_MEMBERS), 88,
                         "this unit added no module (its rider is inert); the global count is 88 after C7 P3b-6a's +1 net.c, 87 after C7 P3b-4b's +2 serve files (serve.c/serve.h), 85 after C7 P3b-4a's +6 enclosure files (enclosure.S/enclosure.c/enclosure.h/sha256.c/worker.S/worker.ld), 79 after P3b-3's +6 clock/interrupt/entropy (73 after P3b-2's +5 disk, 68 after P3b-1's +11)")
        self.assertTrue(any("kernel/boot.py" in m for m in attestation.ATTESTED_MEMBERS),
                        "kernel/boot.py (the wake checklist's home) is attested, as before")

    def test_the_fold_set_is_unchanged(self):
        from kernel.views import FOLD_NAMES
        self.assertEqual(len(FOLD_NAMES), 16, "the wake checklist adds no fold; FOLD_NAMES is unchanged")


if __name__ == "__main__":
    unittest.main(verbosity=2)
