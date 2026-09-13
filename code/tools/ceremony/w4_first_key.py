#!/usr/bin/env python3
# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-tooling · OS-architecture
# vocabulary (world founding, key-bind, signed door, root authority, one-shot ceremony). NON-GOAL:
# no offensive capability of any kind — this founds an ordinary governed world from the production
# pack, binds a TEST master key to its root account, and exercises the ordinary signed door. It mints
# no real key material and models no attack. Full declaration: SCOPE-STATEMENT.md.
"""EP-W4-FIRST-KEY — the first-key ceremony (design/37 8-g), a ONE-SHOT SCRIPT run ONCE at mgr's hand.

A key-bind mutates a lasting, NON-REDERIVABLE record, so this is a script that runs ONCE against a
world folder OUTSIDE the repository (owner-worded PLACE, :3140) — never a per-ledger-run test. The
READ-ONLY verifier that checks the world afterwards is tests/test_w4_first_key.py.

The world path is argv[1]: the manager passes the real <HOME>/gov-lab/govos-w4 folder; a
throwaway temp path is passed to VALIDATE this script without touching the real holding.

The four printed verdicts (§3):
  FOUND      — build_full_kernel over the production 1.38.0 pack; founding_version printed.
  BIND       — the ONE key-bind: gate.execute(KEY_BIND, root, {account, public_key}) where
               account == views.chain_end() (the root authority holder, DERIVED) and public_key is
               the self-describing TEST master key (the declaration lives in the VALUE; no secret).
  DOOR CHECK — both directions: an UNSIGNED root act REFUSES at the signed door (SIGN-LAW); a SIGNED
               one (its mark citing the bound test key) PASSES.
  ONCE-ONLY  — if a KEY-BIND already exists in the world, prints that and exits WITHOUT appending.

THE CAP (§7): under modelled material the door checks that the MARK CITES THE BOUND KEY, never
possession of a secret. The test key commits to no secret, so the root holds no open capability under
it and nothing may be sealed to root until the owner's later rotation to his real key (his act, not a
seat's). This proves the door's SHAPE, nothing about cryptography.
"""

import hashlib
import os
import sys

# tools/ceremony/w4_first_key.py -> repo root is three dirs up.
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "src"))

from kernel.compose import build_full_kernel                                    # noqa: E402
from kernel import keys                                                         # noqa: E402
from kernel.gate import make_invoker_sig, INVOKER_SIG                           # noqa: E402
from kernel.errors import OpError                                               # noqa: E402

# The self-describing TEST master key. `<hex>` is MODELLED public material, not a secret: it is the
# sha256 of a public descriptor, so anyone may recompute it and it commits to nothing hidden. The
# SAME literal is carried by tests/test_w4_first_key.py (A2 expects bound_key to return exactly this).
# The declaration lives IN THE VALUE — the {account, public_key} bind shape is unchanged (no amend).
_MODELLED_HEX = hashlib.sha256(
    b"gov-os W4 TEST master key: modelled material, no real secret (design/37 8-g)").hexdigest()
TEST_MASTER_KEY = f"TEST-MASTER-KEY 2026-09-07 {_MODELLED_HEX}"

DOOR_OP = "CREATE-INFO"       # a production op the root may run; the signed door leashes it once keyed


def _founding_version(store):
    """The world's founding version, read from its own FOUND-STORE record (install.py F4 stamps the
    pack's founding_version into that payload) — read from the WORLD, never from the pack file."""
    fs = store.by_action("FOUND-STORE")
    return (fs[0].get("payload") or {}).get("founding_version") if fs else None


def _key_binds(store):
    """Every KEY-BIND record in the world, recognised by the payload's class tag (never a hard-coded
    action name) — the once-only guard reads this."""
    return [e for e in store.all() if (e.get("payload") or {}).get("kind") == keys.KEY_BIND]


def run(world_dir):
    rec_path = os.path.join(world_dir, "rec.jsonl")
    blob_dir = os.path.join(world_dir, "blobs")
    vault_dir = os.path.join(world_dir, "vault")

    # ---- FOUND (§3.1) ----------------------------------------------------------------------------
    store, gate, views, _blobs, _subs = build_full_kernel(rec_path, blob_dir, vault_dir)
    fv = _founding_version(store)
    print(f"[FOUND] world at {world_dir}")
    print(f"        founding_version = {fv}")
    if fv != "1.38.0":                                            # STOP condition §8.1
        print(f"[STOP] founding_version is {fv!r}, not '1.38.0' — refusing (EP-W4 §8.1). "
              f"Nothing bound.")
        return 2
    print(f"        key_law_live (KEY-LAW-BIND declared) = {keys.key_law_live(views)}")

    # ---- ONCE-ONLY GUARD (§3 / §8.6) -------------------------------------------------------------
    existing = _key_binds(store)
    if existing:
        print(f"[ONCE-ONLY GUARD] a KEY-BIND already exists in this world "
              f"({len(existing)} record(s), seq {[e.get('seq') for e in existing]}). "
              f"The first-key ceremony runs ONCE — exiting WITHOUT appending (EP-W4 §8.6).")
        return 0

    # ---- BIND — the ONE key-bind act (§3.2) ------------------------------------------------------
    root = views.chain_end()                                     # DERIVED, never given (§8.5 if None)
    if root is None:
        print("[STOP] views.chain_end() could not be derived — no root authority holder (EP-W4 §8.5).")
        return 5
    print(f"[ROOT] chain_end (derived root authority holder) = {root!r}")
    rec = gate.execute(keys.KEY_BIND, root, {"account": root, "public_key": TEST_MASTER_KEY})
    print("[BIND] recorded KEY-BIND row:")
    print(f"       seq         = {rec.get('seq')}")
    print(f"       action      = {rec.get('action')}")
    print(f"       actor       = {rec.get('actor')}")
    print(f"       object      = {rec.get('object')}")
    print(f"       payload     = {dict(rec.get('payload') or {})}")
    print(f"       bound_key(store, root) -> {keys.bound_key(store, root)!r}")

    # ---- DOOR CHECK, both directions (§3.3) ------------------------------------------------------
    # UNSIGNED: root is now key-bound, so an unsigned act refuses at the signed door (SIGN-LAW). A
    # refusal appends nothing.
    try:
        gate.execute(DOOR_OP, root, {"content": "w4-door-check-unsigned"})
        print("[DOOR unsigned] PASSED — UNEXPECTED: the leash did not engage. STOP (EP-W4 §8.3).")
        return 3
    except OpError as e:
        print(f"[DOOR unsigned] REFUSED at the signed door — rule={e.rule} (the leash engaged).")

    # SIGNED: the invoker's own mark cites the bound test key over the act's content; the door passes
    # it (a PASS records the act — part of this one-shot world, A4's sha256 is taken after it).
    params = {"content": "w4-door-check-signed"}
    draft = gate.ops[DOOR_OP]["handler"](root, dict(params))
    sig = make_invoker_sig(TEST_MASTER_KEY, draft, deciding_time=None, seal=draft.get("seal"))
    rec2 = gate.execute(DOOR_OP, root, {**params, INVOKER_SIG: sig})
    print(f"[DOOR signed]   PASSED — recorded seq={rec2.get('seq')} "
          f"(the mark cites the bound test key).")

    # ---- THE HOLDING (§4 A4) ---------------------------------------------------------------------
    with open(rec_path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    print(f"[HOLDING] rec.jsonl sha256 (after the ceremony's LAST act) = {digest}")
    print(f"[HOLDING] path = {rec_path}")

    # ---- THE CAP (§7) ----------------------------------------------------------------------------
    print("[CAP] Modelled material: the door checks that the MARK CITES THE BOUND KEY, not possession "
          "of a secret. The self-describing test key commits to no secret, so the root holds no open "
          "capability under it and NOTHING may be sealed to root until the owner's later rotation to "
          "his real key (his act, no seat holds it). The door's SHAPE is proven — nothing about "
          "cryptography.")
    print("[DONE] first-key ceremony complete — one bind, the door engaged both directions.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: w4_first_key.py <world_dir>")
        print("       mgr passes the real <HOME>/gov-lab/govos-w4 (created here, once);")
        print("       a throwaway temp path validates this script without touching the real holding.")
        sys.exit(64)
    sys.exit(run(sys.argv[1]))
