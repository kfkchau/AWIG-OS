# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (hash chain, key binding, signed door, vault, append-only record). NON-GOAL: no
# offensive capability of any kind — these probes prove a governed record is edit-evident, a signed
# door refuses an unsigned act, the vault has no read path, and the vocabulary holds no record-removal
# function; they mint nothing real and model no attack. Full declaration: SCOPE-STATEMENT.md.
"""Campaign-4 sealed-world probes (committed at the EP-42 review, R3/R14 — the drill grows).

The module batteries (test_ep34..46) prove each C4 column in its own area. This file adds the
reviewer's WHOLE-WORLD legs that span areas at once, and the one estate-wide census the batteries
lack (they prove no-delete at the blob surface only — EP-42 finding).

  P1  cold whole-world round-trip (T-TOTAL-ROUNDTRIP-4 shape): a sealed, keyed, signed world is
      rebuilt from the record file ALONE — the chain re-verifies, every recorded signature verifies
      AS DATA, the key binding and op registry reconstruct, and replay mints NOTHING.
  P2  the chain red-world: an edited byte-of-meaning in a chained record is DETECTED and LOCATED
      (P1's chain column proven able to fail).
  P3  the signed door: a keyed account's unsigned act REFUSES citing SIGN-LAW and does NOT land;
      the same act signed accepts (the crux column, both directions).
  P4  the vault still closed: the vault surface is seal + compare only — no read path (R4).
  P5  the estate-wide no-delete census (design/46): the append-only substrate exposes no
      record-removal method and the vocabulary holds no record-removal op — with a planted positive
      control so the census CAN fail.

SHAPE OVER MODELLED KEY MATERIAL (design/37 §9 as-built): the signed door checks
possession-plus-provenance, not real cryptography; KEY-MATERIAL-REAL is the named next unit. A probe
that finds nothing shows its column CAN fail — each carries its own red world. Probes build fresh
kernels in temp dirs; they never touch a real record.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))

from kernel.boot import build_kernel                                             # noqa: E402
from kernel.blobs import BlobStore                                               # noqa: E402
from kernel import keys                                                          # noqa: E402
from kernel.gate import SIGN_LAW, INVOKER_SIG, make_invoker_sig, verify_invoker_sig  # noqa: E402
from kernel.vault import VaultStore                                              # noqa: E402
from kernel.errors import OpError                                                # noqa: E402
from kernel.store import EventStore                                              # noqa: E402

RESULTS = []
ALICE_KEY = "testpub:alice:v1"


def check(name, ok):
    RESULTS.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name)


# --- world helpers (production founding: SIGN-LAW + the key family are live) ------------------
def _world():
    d = tempfile.mkdtemp()
    path = os.path.join(d, "record.jsonl")
    blobdir = os.path.join(d, "blobs")
    store, gate, views = build_kernel(path, blobs=BlobStore(blobdir))
    return d, path, blobdir, store, gate, views


def _keyed_alice(gate):
    gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "alice", "actor_class": "human"})
    gate.execute("VERIFY-ACCOUNT", "owner",
                 {"account": "alice", "evidence_hash": "sha256:" + hashlib.sha256(b"alice").hexdigest()})
    gate.execute(keys.KEY_BIND, "owner", {"account": "alice", "public_key": ALICE_KEY})


def _signed_create_info(gate, actor, content, key):
    draft = gate.ops["CREATE-INFO"]["handler"](actor, {"content": content})
    sig = make_invoker_sig(key, draft, deciding_time=None, seal=draft.get("seal"))
    return gate.execute("CREATE-INFO", actor, {"content": content, INVOKER_SIG: sig})


def _rewrite_record(path, seq, mutate):
    with open(path, "r", encoding="utf-8") as fh:
        lines = [ln for ln in fh.read().splitlines() if ln]
    rec = json.loads(lines[seq - 1])
    mutate(rec)
    lines[seq - 1] = json.dumps(rec, separators=(",", ":"))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# ============================================================================================
# P1 — the cold whole-world round-trip (chain + keys + signed act, replayed from the record alone)
# ============================================================================================
def probe_cold_roundtrip():
    d, path, blobdir, store, gate, views = _world()
    _keyed_alice(gate)
    store.seal_prefix()                              # open the chained era over the whole prefix
    rec = _signed_create_info(gate, "alice", "kept-doc", ALICE_KEY)     # a chained, signed act
    recorded_sig = rec["provenance"][INVOKER_SIG]

    check("cold round-trip: the live sealed chain verifies clean", store.verify_chain()["ok"])
    live_bytes = open(path, "rb").read()
    live_ops = set(views.op_definitions())
    live_key = views.bound_key("alice")
    live_len = len(store.events)

    # KILL everything derived: rebuild the kernel from the record FILE ALONE.
    store2, gate2, views2 = build_kernel(path, blobs=BlobStore(blobdir))
    check("cold round-trip: replay minted NOTHING (record file byte-identical)",
          open(path, "rb").read() == live_bytes)
    check("cold round-trip: replay appended no event", len(store2.events) == live_len)
    check("cold round-trip: the chain re-verifies from the record alone", store2.verify_chain()["ok"])
    check("cold round-trip: the key binding reconstructs identically", views2.bound_key("alice") == live_key)
    check("cold round-trip: the op registry reconstructs identically", set(views2.op_definitions()) == live_ops)
    r2 = [e for e in store2.all() if e["action"] == "CREATE-INFO" and e.get("object") == "kept-doc"][-1]
    check("cold round-trip: the recorded signature verifies as DATA after replay (re-signs nothing)",
          verify_invoker_sig(recorded_sig, views2.bound_key("alice"), r2, deciding_time=None, seal=r2.get("seal")))
    shutil.rmtree(d, ignore_errors=True)


# ============================================================================================
# P2 — the chain red-world: P1's chain column proven able to fail
# ============================================================================================
def probe_chain_red_world():
    d, path, blobdir, store, gate, views = _world()
    store.seal_prefix()
    gate.execute("CREATE-INFO", "owner", {"content": "post-1"})     # a post-anchor record WITH a successor
    gate.execute("CREATE-INFO", "owner", {"content": "post-2"})     # the head
    check("chain red-world: a clean sealed chain verifies (no false alarm)", EventStore(path).verify_chain()["ok"])
    target = [e for e in EventStore(path).all() if e.get("object") == "post-1"][0]["seq"]
    _rewrite_record(path, target, lambda r: r.__setitem__("payload", {"content": "TAMPERED"}))
    res = EventStore(path).verify_chain()
    check("chain red-world: an edit to a chained record is DETECTED", res["ok"] is False)
    check("chain red-world: the break is LOCATED at the first broken link (edit X -> break at X+1)",
          res.get("break_at") == target + 1 and res.get("verified_through") == target)
    shutil.rmtree(d, ignore_errors=True)


# ============================================================================================
# P3 — the signed door: unsigned keyed refuses and does NOT land; signed accepts
# ============================================================================================
def probe_signed_door():
    d, path, blobdir, store, gate, views = _world()
    _keyed_alice(gate)
    before = len([e for e in store.all() if e["action"] == "CREATE-INFO"])
    refused = False
    try:
        gate.execute("CREATE-INFO", "alice", {"content": "unsigned-ghost"})
    except OpError as e:
        refused = (e.rule == SIGN_LAW)
    check("signed door: an unsigned act by a keyed account REFUSES citing SIGN-LAW", refused)
    after = [e for e in store.all() if e["action"] == "CREATE-INFO"]
    check("signed door: the refused unsigned act did NOT land (RW1 too-weak)",
          len(after) == before and not any(e.get("object") == "unsigned-ghost" for e in after))
    rec = _signed_create_info(gate, "alice", "signed-doc", ALICE_KEY)
    check("signed door: the SAME act signed accepts (the column can pass)", rec["action"] == "CREATE-INFO")
    shutil.rmtree(d, ignore_errors=True)


# ============================================================================================
# P4 — the vault still closed (no read path)
# ============================================================================================
def probe_vault_still_closed():
    public = [m for m in dir(VaultStore) if not m.startswith("_")]
    banned = ("get", "read", "reveal", "open", "value", "has", "plaintext", "fetch", "load", "decrypt")
    leaks = [m for m in public if any(b in m.lower() for b in banned)]
    check("vault still closed: no read/get/reveal/open path on the vault surface", leaks == [])
    check("vault still closed: the surface is exactly seal + compare", set(public) == {"seal", "compare"})


# ============================================================================================
# P5 — the estate-wide no-delete census (design/46): capability-absence over the whole vocabulary
# ============================================================================================
def probe_no_delete_census():
    d, path, blobdir, store, gate, views = _world()
    removal = ("delete", "remove", "erase", "destroy", "truncate", "rewrite", "overwrite", "drop", "pop")
    # (a) the append-only RECORD substrate exposes no record-removal method.
    substrate = [m for m in dir(store) if not m.startswith("_") and any(v in m.lower() for v in removal)]
    check("no-delete census: the record substrate (EventStore) exposes no record-removal method",
          substrate == [])
    # (b) estate-wide: no op in the vocabulary is a record-removal op. FILE-TRUNCATE / FILE-XATTR-REMOVE
    #     are CONTENT ops — they append a record describing a content/attr change and remove no record.
    opnames = list(views.op_definitions())
    record_removal_ops = [n for n in opnames
                          if any(("record-" + v) in n.lower() or (v + "-record") in n.lower() for v in removal)]
    check("no-delete census: no op in the vocabulary is a record-removal op (design/46 capability-absence)",
          record_removal_ops == [])
    # (c) POSITIVE CONTROL — the census CAN fail: a planted record-removal op name reds it.
    planted = [n for n in opnames + ["RECORD-DELETE"]
               if any(("record-" + v) in n.lower() or (v + "-record") in n.lower() for v in removal)]
    check("no-delete census: the census CAN fail (a planted RECORD-DELETE op reds it)", planted == ["RECORD-DELETE"])
    shutil.rmtree(d, ignore_errors=True)


def main():
    probe_cold_roundtrip()
    probe_chain_red_world()
    probe_signed_door()
    probe_vault_still_closed()
    probe_no_delete_census()
    failed = [n for n, ok in RESULTS if not ok]
    print()
    if failed:
        print("campaign4_sealed_world_probes: %d FAILED -> %s" % (len(failed), ", ".join(failed)))
        sys.exit(1)
    print("campaign4_sealed_world_probes: ALL PASS (%d probes)" % len(RESULTS))


if __name__ == "__main__":
    main()
