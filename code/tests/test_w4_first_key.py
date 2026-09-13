# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (world founding, key-bind, signed door, root authority). NON-GOAL: no offensive
# capability of any kind — this READS a governed world and proves a key was bound and the signed
# door's shape holds; it mints nothing, executes nothing, and models no attack. Full declaration:
# SCOPE-STATEMENT.md.
"""EP-W4-FIRST-KEY (ACCEPTANCE) — the READ-ONLY verifier of the first-key ceremony (design/37 8-g).

The ceremony (tools/ceremony/w4_first_key.py) is a ONE-SHOT SCRIPT that binds a TEST master key on a
NON-REDERIVABLE world outside the repo. This test is its READ-ONLY companion: it EXECUTES nothing and
APPENDS nothing (it loads the world by REPLAY through build_kernel, which is pack-exact — no
compose-layer attest, genesis idempotent — and it self-guards that rec.jsonl is byte-identical before
and after the load). It SKIPS with a stated reason when the world is absent, so the whole-repo ledger
is green whether or not the manager has yet run the ceremony, and it never mutates the holding.

  A1  founded at 1.38.0: the world's own founding_version == "1.38.0"; KEY-LAW-BIND live.
  A2  exactly one bind: exactly ONE KEY-BIND record for views.chain_end(); bound_key returns the
      TEST master key verbatim; the bind payload shape is unchanged (no founding amend / extra field).
  A3  the door's SHAPE, IN MEMORY over a DRAFT (no execute, no row): a mark CITING the bound key
      verifies through the real verify_invoker_sig; a mark citing ANOTHER key does not; a tampered
      draft does not (a check that can fail).

THE WRONG REFERENCE THIS TEST REFUSES: verify_invoker_sig is the SIGNED DOOR's check (kernel/gate.py),
NOT keys.verify_countersign (the STORE's countersignature over a record's seq/record_time). A3 proves
the invoker/door signature — the mark cites a bound key over an act's content — so it uses the gate's
function, the same one EP-37's live door reads (keys.py's own docstring cross-references it by name).
"""

import hashlib
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kernel.boot import build_kernel                                            # noqa: E402
from kernel import keys                                                         # noqa: E402
from kernel.gate import make_invoker_sig, verify_invoker_sig                    # noqa: E402

# The world the manager's one-shot ceremony creates (owner-worded PLACE, :3140) — outside the repo,
# never autosynced. Absent until the ceremony has run; this test SKIPS while it is absent.
WORLD = "<HOME>/gov-lab/govos-w4/"

# The self-describing TEST master key — the SAME modelled literal the ceremony binds (its `<hex>` is
# the sha256 of a public descriptor, no secret). A2 expects bound_key to return exactly this.
_MODELLED_HEX = hashlib.sha256(
    b"gov-os W4 TEST master key: modelled material, no real secret (design/37 8-g)").hexdigest()
TEST_MASTER_KEY = f"TEST-MASTER-KEY 2026-09-07 {_MODELLED_HEX}"

# A DIFFERENT modelled key — A3's negative case: a mark citing it must not verify against the bound key.
OTHER_TEST_KEY = "TEST-OTHER-KEY 2026-09-07 " + hashlib.sha256(
    b"gov-os W4 a DIFFERENT modelled key that must never verify against the bound key").hexdigest()


def open_world_readonly(world_dir):
    """Load the world's (store, views) by REPLAY, appending NOTHING. build_kernel is the pack-exact
    boot path (no compose-layer attestation, genesis idempotent), so an existing world gains no
    record. Self-guarded: rec.jsonl's sha256 is identical before and after — a read that mutated the
    holding fails here rather than silently."""
    rec_path = os.path.join(world_dir, "rec.jsonl")
    before = hashlib.sha256(open(rec_path, "rb").read()).hexdigest()
    store, _gate, views = build_kernel(rec_path)
    after = hashlib.sha256(open(rec_path, "rb").read()).hexdigest()
    assert before == after, "READ-ONLY load MUTATED the world (rec.jsonl changed) — must never happen"
    return store, views


# ---- the assertion bodies, taking (store, views) so validation can drive them on a throwaway world
# without the real path present. The unittest methods below delegate to these.

def check_a1(store, views):
    fs = store.by_action("FOUND-STORE")
    assert len(fs) == 1, f"expected exactly one FOUND-STORE record, got {len(fs)}"
    fv = (fs[0].get("payload") or {}).get("founding_version")
    assert fv == "1.38.0", f"world founding_version is {fv!r}, expected '1.38.0'"
    assert keys.key_law_live(views), "KEY-LAW-BIND is not live in the founded world"


def check_a2(store, views):
    root = views.chain_end()
    binds = [e for e in store.all()
             if (e.get("payload") or {}).get("kind") == keys.KEY_BIND
             and (e.get("payload") or {}).get("account") == root]
    assert len(binds) == 1, f"expected exactly one KEY-BIND for chain_end {root!r}, got {len(binds)}"
    bound = keys.bound_key(store, root)
    assert bound == TEST_MASTER_KEY, f"bound_key is {bound!r}, expected the TEST master key verbatim"
    payload_keys = set(binds[0].get("payload").keys())
    assert payload_keys == {keys.ACCOUNT, keys.PUBLIC_KEY, "kind", keys.CLASS}, (
        f"KEY-BIND payload shape changed to {payload_keys} — a founding amend / extra field "
        f"(the declaration must live in the key's VALUE, not a new field)")


def check_a3(store, views):
    root = views.chain_end()
    bound = keys.bound_key(store, root)
    # a DRAFT — an ordinary act's caller-controlled content. No gate, no execute, no recorded row.
    draft = {"action": "CREATE-INFO", "object": "w4-door-shape-proof", "target": None,
             "payload": {"content": "w4-door-shape-proof"}}
    mark_bound = make_invoker_sig(bound, draft)
    assert verify_invoker_sig(mark_bound, bound, draft) is True, \
        "a mark CITING the bound key must verify through the signed door's check"
    mark_other = make_invoker_sig(OTHER_TEST_KEY, draft)
    assert verify_invoker_sig(mark_other, bound, draft) is False, \
        "a mark citing ANOTHER key must NOT verify against the bound key"
    tampered = dict(draft, payload={"content": "not-what-was-signed"})
    assert verify_invoker_sig(mark_bound, bound, tampered) is False, \
        "a tampered draft must NOT verify (a check that can fail)"


@unittest.skipUnless(
    os.path.isdir(WORLD),
    f"W4 world absent at {WORLD} — the first-key ceremony has not been run "
    f"(READ-ONLY test: nothing to verify, nothing mutated)")
class TestW4FirstKey(unittest.TestCase):
    """READ-ONLY over the W4 world. Skips entirely when the world is absent (the ledger stays green
    before the ceremony runs)."""

    @classmethod
    def setUpClass(cls):
        cls.store, cls.views = open_world_readonly(WORLD)

    def test_a1_founded_at_1_38_0_and_key_law_live(self):
        check_a1(self.store, self.views)

    def test_a2_exactly_one_bind_for_chain_end_and_key_bound(self):
        check_a2(self.store, self.views)

    def test_a3_the_signed_doors_shape_in_memory(self):
        check_a3(self.store, self.views)


if __name__ == "__main__":
    unittest.main()
