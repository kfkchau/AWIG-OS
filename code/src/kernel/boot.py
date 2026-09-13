# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS kernel — boot: the foundational op HANDLERS + the installer call.

Registers the bootstrap operation handlers that build the gate's surface, then composes
store + gate + views into a booting governed kernel — the thin slice (design 02 §10) at
foundation scale. The twelve-op foundational import pack (venn2-foundational §01;
design/12 §0) is BOOTSTRAP_OPS; the load-bearing ones the thin slice exercises are wired
here, the rest are named-pending, not hidden.

EP-14 (design/31 J9): the founding is no longer Python literals in this module. The whole
constitution — the root laws (in full form, WITH scope), the vocabulary and policy packs,
the core/governance/obligation op definitions, the master views, and the founding openness
grant — lives in `founding/founding-pack.json` and is executed by `founding.install`.
`genesis()` here is the installer call; it keeps its name and signature so compose (and the
suite) are unchanged. What remains in this file is mechanism only: the op HANDLER
registrations (Python functions — no governance value) and the compose/replay wiring.
"""

from .store import EventStore
from .gate import Gate
from .views import Views, VIEW_FILTER_DIMENSIONS, FOLD_NAMES

# The foundational import pack (venn2-foundational §01).
BOOTSTRAP_OPS = [
    "READ", "FOLLOW", "CREATE-INFO", "CREATE-ACTIVITY", "CREATE-RELATIONSHIP",
    "CREATE-ACTOR", "CREATE-TUNNEL", "WRITE-ACTIVITY",
    "CHECK-RULE", "CHECK-CONTRADICTION", "BLOCK",
]  # CREATE-RULE left this list in EP-05 Phase B — it is now data-born (in the founding pack).

def build_kernel(file_path, lock=False, blobs=None):
    """Compose the spine, register the bootstrap surface, seed the constitution, and
    replay the definition-born operations. Returns (store, gate, views). Genesis is
    idempotent (fresh / reload / explicit call never double-seed), and the replay makes
    the registry itself derived state: operations admitted by CREATE-OP records come
    back registered on every rebuild — kill the registry, replay, identical. `blobs` (the
    content-addressed store) is optional: without it, content-addressed ops (FILE-WRITE,
    COMMS-SEND) stay unregistered (content_ops_pending_blobs surfaces them); the full kernel
    passes it so they register."""
    from .opdefs import register_opdef_ops, replay_op_definitions
    store = EventStore(file_path, lock=lock, require_rule_cited=True)
    views = Views(store)
    gate = Gate(store, views)  # views is REQUIRED (C0): no gate without its constitution guard
    gate.blobs = blobs  # content_params ops register only when the blob store is present
    _register_bootstrap(gate, store, views)
    register_opdef_ops(gate, store, views)
    genesis(store)
    replay_op_definitions(gate, store, views)
    # EP-40 (:2769 R1): the engine attestation does NOT ride here. `build_kernel` stays pack-exact
    # — the founding roundtrip (test_ep14 TestFoundingRoundTrip) asserts a rebuild adds nothing, so
    # a boot append in this path is a founding-record divergence. The attestation is a COMPOSE-LAYER
    # act, ABOVE the founding boot (kernel/compose.build_full_kernel), through the gate.
    return store, gate, views


def _register_bootstrap(gate, store, views):
    def create_info(actor, params):
        return {"actor": actor, "action": "CREATE-INFO",
                             "object": params["content"], "rule_cited": "ROOT-NEG-5"}
    gate.register("CREATE-INFO",
                  {"description": "mint an information object", "rules": ["ROOT-NEG-5"],
                   "params": {"content": "required"},
                   # C-3 (EP-MAINT-OUTSIDE-2): CREATE-INFO is the one CODE-registered op in the crash
                   # class — its `content` becomes the record object, so a raw `bytes` value crashes the
                   # record write (json.dumps -> BatchFailed). Declared `text` so the door refuses it,
                   # exactly as `param_kinds` on a definition-born op does (opdefs.PARAM_KINDS).
                   "param_kinds": {"content": "text"}}, create_info)

    def create_actor(actor, params):
        return {"actor": actor, "action": "CREATE-ACTOR",
                             "object": params["actor_id"], "rule_cited": "CAP-IS-LAW",
                             "payload": {"actor_id": params["actor_id"], "role": params.get("role")}}
    gate.register("CREATE-ACTOR",
                  {"description": "mint an actor (capability is law)", "rules": ["CAP-IS-LAW"],
                   "params": {"actor_id": "required"}}, create_actor)

    # CREATE-RULE is no longer a boot handler: it is data-born (CREATE_RULE_DEFINITION, seeded at
    # genesis), its contradiction check extracted into the `consistency` vocabulary check and its
    # A3 self-protection enforced at the gate. Genesis still founds the constitution by direct
    # _append (action CREATE-RULE), which needs no registered op.

    def read_op(actor, params):
        # READ populates provenance — the mechanical root of SIGHT-IS-LAW.
        return {"actor": actor, "action": "READ", "object": params["object"],
                             "rule_cited": "SIGHT-IS-LAW"}
    gate.register("READ",
                  {"description": "move info into active context (populates provenance)",
                   "rules": ["SIGHT-IS-LAW"], "params": {"object": "required"}}, read_op)

    def write_activity(actor, params):
        return {"actor": "SYSTEM", "action": "WRITE-ACTIVITY",
                             "object": params.get("about"), "rule_cited": "ROOT-NEG-5",
                             "payload": params.get("data", {})}
    gate.register("WRITE-ACTIVITY",
                  {"description": "record that an activity happened (SYSTEM only)",
                   "rules": ["ROOT-NEG-5"], "params": {}}, write_activity)

    def block_op(actor, params):
        return {"actor": "SYSTEM", "action": "BLOCK", "target": params.get("target"),
                             "rule_cited": params.get("rule", "P4-REFUSE"),
                             "payload": {"reason": params.get("reason")}, "refused": True}
    gate.register("BLOCK",
                  {"description": "the recorded no (refusal constructor)", "rules": ["P4-REFUSE"],
                   "params": {}}, block_op)

    def create_view(actor, params):
        # A view is a standing rule (design/27 §4): a FILTER view (trigger `when` -> outcome `then`)
        # or a MASTER (`bind` names an S-plane fold, EP-08). Both vocabularies are CLOSED: a `when`
        # dimension outside VIEW_FILTER_DIMENSIONS, or a `bind` outside FOLD_NAMES, is a nonconforming
        # call refused before anything is written (the closure discipline — an unknown filter/fold
        # does not exist). A master keeps the DICT `when` shape; it never carries a LIST trigger
        # (that is executable law, the full-form pass's territory).
        name = params["name"]
        bind = params.get("bind")
        if bind is not None and bind not in FOLD_NAMES:
            gate.refuse(actor, "CREATE-VIEW", "AR-2",
                        f'unknown fold "{bind}" — a master may bind only: ' + ", ".join(FOLD_NAMES))
        when = params.get("when") or {}
        for dim in when:
            if dim not in VIEW_FILTER_DIMENSIONS:
                gate.refuse(actor, "CREATE-VIEW", "AR-2",
                            f'unknown trigger dimension "{dim}" — a view may test only: '
                            + ", ".join(VIEW_FILTER_DIMENSIONS))
        then = params.get("then") or {}
        text = (f"master view {name}: derived by the {bind} fold" if bind else
                f"when a record matches {when} -> "
                + (f"move it to {then['move_to']}" if then.get("move_to") else "surface it to the requester"))
        # Carries a rule_id: a view definition IS law (REQ-form), visible to active_rules,
        # contradiction-gated like any rule creation (ROOT-NEG-6). Same name = amendment.
        payload = {"kind": "view_definition", "rule_id": f"view:{name}", "polarity": "+",
                   "name": name, "when": when, "then": then, "text": text}
        if bind:
            payload["bind"] = bind            # a master names its fold; a runtime bind is ordinary tier
        if params.get("refresh") is not None:
            payload["refresh"] = params["refresh"]
        return {"actor": actor, "action": "CREATE-VIEW", "object": f"view:{name}", "rule_cited": "ROOT-NEG-6",
                             "payload": payload}
    gate.register("CREATE-VIEW",
                  {"description": "define a view: a filter ('when matches, move it') or a master (bind to a fold)",
                   "rules": ["ROOT-NEG-6"], "params": {"name": "required"}}, create_view)

    # ---- the authority surface's write ops (EP-16 X1; design/31 J2 + J3-data) ------------
    # CREATE-SPACE / CREATE-ROLE / GRANT / REVOKE are NO LONGER boot handlers: they are OWNER-TIER
    # DEFINITION-BORN PACK RECORDS (founding-pack.json, step 08c), seeded at genesis and registered
    # by replay_op_definitions like every other definition-born op. The first build placed them here
    # as code because their refusals — the space-tree cycle/parent bar and the grant whole-containment
    # bar — needed handler logic the closed check vocabulary could not express, and opdefs was out of
    # fence. EP-16 X1 widens the fence and names two new checks (opdefs.OP_CHECKS: space_tree,
    # attenuation) plus a general object_derive capability, so the four ops move into the founding
    # document. The gain: they now carry a recorded tier (owner), conservation reaches them (bare
    # RETIRE-OP refuses via the gate's branch d), and a cold reader of the pack SEES the authority
    # write surface exists — no more law-in-code exactly where power lives (the surface EP-14 closed).


def genesis(store):
    """Execute the founding (design/31 J9). The constitution is a data document
    (`founding/founding-pack.json`), executed by the installer — no longer Python literals
    here. Kept as a thin, same-signature delegation so compose and the whole suite call it
    unchanged. Idempotent (the installer carries the SYSTEM-actor guard); the installer is a
    sanctioned constitutional seed appending through the same direct `store._append` genesis
    always used (no gate change, no new appender)."""
    from founding.install import install
    install(store)


def unregistered_bootstrap_ops(gate):
    """Bootstrap ops not yet wired — named-pending for the subsystems that need them."""
    return [op for op in BOOTSTRAP_OPS if not gate.has(op)]


# ---- EP-47B: THE SYSTEM SIGNER SEED STEP — the Option A ceremony's collection half ---------------
# The boot-time half of the system-signer ceremony (Option A — the recorded ceremony at boot; archi
# :3302, refined by two architect precisions folded in via coord on 2026-09-08). This module holds
# the PURE mechanism (collect + measure the entropy, mix it, create + seal the signer, derive the
# public half) with NO append: the BIND and the CEREMONY ROW (the records) ride the COMPOSE layer
# (compose.seal_system_signer), because build_kernel above is pack-exact (the founding roundtrip
# asserts a rebuild adds nothing) and must never grow a boot record. The seed is held IN MEMORY only
# (signer.py) — a restart drops it and this step must re-run, which is the whole point EP-47B proves
# (a restart needs the ceremony before the record can grow).
#
# THE CEREMONY INPUT (architect precision 2, 2026-09-08). Human randomness (mouse timing/path, key
# timing) MIXED BY HASH WITH THE OS CRYPTOGRAPHIC SOURCE — never instead of it. os.urandom is ALWAYS
# in the mix; the human events ADD to it. The ceremony MEASURES the human contribution and REFUSES
# below a minimum-entropy floor (this generalises the earlier fixed/low-entropy refusal). A HEADLESS
# boot (no human events) runs the OS-source-only path and the ceremony row SAYS SO. Test/demo worlds
# run the SCRIPTED TEST ceremony (the headless path invoked by the test), binding a MARKED-TEST value.

# A marked-TEST system key value, W4's :3140 form (TEST-<name> <date> <hash>): the recorded public
# half a TEST/DEMO world binds under the MODELLED (library-absent) era. It marks the record as TEST
# exactly as W4's master key was, so the record self-describes "not the owner's real key". The SEED
# behind it is drawn from os.urandom — the value is marked, the material is random.
_MARKED_TEST_SYSTEM_KEY_PREFIX = "TEST-SYSTEM-KEY 2026-09-08 "

_SEED_BYTES = 32
# The minimum-entropy floor (bits) the collected human contribution must clear (architect precision 2).
# os.urandom material carries ~8 bits/byte (≈256 bits over 32); a human contribution below this floor
# — all-zeros, a repeated byte, a too-short blob — is REFUSED. os.urandom itself always clears it, so
# the OS-only headless path never trips the floor. The floor is on the COLLECTED input, not on the
# final seed (which is always full-entropy because os.urandom is always mixed in).
_MIN_ENTROPY_BITS = 128


def measure_entropy_bits(material):
    """A Shannon-entropy estimate of collected ceremony material, in bits (H(bytes) × length). The
    ceremony MEASURES what it collected with this and refuses below `_MIN_ENTROPY_BITS` (architect
    precision 2). all-zeros / a repeated byte → 0 bits; os.urandom(32) → ≈256 bits."""
    from math import log2
    b = bytes(material)
    n = len(b)
    if n == 0:
        return 0.0
    counts = {}
    for x in b:
        counts[x] = counts.get(x, 0) + 1
    per_byte = -sum((c / n) * log2(c / n) for c in counts.values())
    return per_byte * n


def _floor(material, *, ascii_belt, min_len):
    """Enforce the minimum-entropy floor over collected `material` and return its measured bits.
    Refuses a too-short blob, a below-floor measurement (all-zeros / repeated / low-entropy), and —
    for a RAW-BYTES contribution — an all-printable-ASCII value (a human-typed / hardcoded constant,
    which can measure just above the Shannon floor). HONEST CAP: byte inspection cannot distinguish a
    diverse-but-predictable value from a random one, so the PRIMARY guarantee stays structural — the
    OS cryptographic source is ALWAYS mixed in — and this floor is the belt on the human contribution,
    proven able to fire (the planted low-entropy case reds)."""
    b = bytes(material)
    if len(b) < min_len:
        raise ValueError(
            "ceremony contribution is %d bytes — below the minimum length %d; too little collected "
            "to clear the entropy floor — refused" % (len(b), min_len))
    bits = measure_entropy_bits(b)
    if bits < _MIN_ENTROPY_BITS:
        raise ValueError(
            "ceremony contribution is BELOW the minimum-entropy floor (%.1f bits < %d) — a fixed / "
            "low-entropy / predictable value; the collected randomness must clear the floor — refused"
            % (bits, _MIN_ENTROPY_BITS))
    if ascii_belt and all(0x20 <= x < 0x7f for x in b):
        raise ValueError(
            "ceremony contribution is all printable ASCII — it looks like a FIXED / hardcoded "
            "constant; the collected randomness must not be a typed constant — refused")
    return bits


def new_os_material():
    """A fresh 32 bytes from the OS cryptographic random source (os.urandom, via crypto.new_signing_
    seed). ALWAYS drawn and ALWAYS mixed into the seed — the human events add to it, never replace it
    (architect precision 2)."""
    from . import crypto
    return crypto.new_signing_seed()


def _events_to_bytes(events):
    """Serialise a list of human event samples to bytes for MEASUREMENT and mixing, preserving the
    samples' own entropy (so a stuck/low-entropy stream measures low and is refused). The raw samples
    are never recorded — only the count and a hash commitment reach the ceremony row."""
    return b"".join(repr(e).encode("utf-8") for e in events)


def collect_system_seed(contributed=None):
    """Collect the system signing seed for the ceremony and return (seed_bytes, descriptor).

    The OS cryptographic source is ALWAYS drawn and ALWAYS mixed by hash (architect precision 2):
    `seed = sha256(os_material || collected)`. `contributed` is the HUMAN contribution — a list of
    event samples, or a raw-bytes blob (a scripted test / the owner's own material); None/empty runs
    the HEADLESS OS-only path. A non-None human contribution is MEASURED and REFUSED below the
    minimum-entropy floor. The descriptor carries {source, event_count, entropy_bits} for the
    ceremony row; it never carries the raw samples."""
    import hashlib
    os_material = new_os_material()                       # ALWAYS in the mix
    if not contributed:
        source = "headless-os-only"                       # a headless boot: OS-only, recorded as such
        collected = b""
        event_count = 0
        bits = measure_entropy_bits(os_material)          # the OS material's own entropy (always clears the floor)
    elif isinstance(contributed, (bytes, bytearray)):
        source = "human-mixed"
        collected = bytes(contributed)
        event_count = len(collected)
        bits = _floor(collected, ascii_belt=True, min_len=_SEED_BYTES)
    else:                                                 # a list/tuple of event samples
        source = "human-mixed"
        collected = _events_to_bytes(contributed)
        event_count = len(contributed)
        bits = _floor(collected, ascii_belt=False, min_len=1)
    seed = hashlib.sha256(os_material + collected).digest()
    return seed, {"source": source, "event_count": event_count, "entropy_bits": round(bits, 1)}


def seed_system_signer(contributed=None):
    """Run the seed-collection ceremony, create a SigningKeyStore, seal the mixed seed into it (in
    memory only), and derive the PUBLIC half — returning (signer, custody_hash, public_half,
    descriptor). No record is appended here (the bind and the ceremony row ride the compose layer).
    The public half is ERA-SPLIT (KEY-MATERIAL-REAL §3): a REAL Ed25519 public key when the vetted
    library is present, and a self-describing MARKED-TEST modelled commitment (W4 :3140 form) when
    absent — so a fresh checkout with nothing installed records a marked-TEST key exactly as W4 did,
    and installing the one package turns the real public half on. The custody hash (sha256 of the
    seed) is a public commitment — the ONLY thing the seal returns; the seed itself never leaves the
    signer and is never written to disk (signer.py's no-read discipline, USED here, never changed)."""
    from .signer import SigningKeyStore
    from . import crypto, keys
    seed, descriptor = collect_system_seed(contributed)
    signer = SigningKeyStore()
    custody = signer.seal(seed)                 # sha256:<hex> — the public commitment; the seed stays in-memory
    if crypto.real_available():
        public = crypto.public_from_seed(seed)  # a REAL ed25519:<hex> public half (the library present)
    else:
        public = _MARKED_TEST_SYSTEM_KEY_PREFIX + keys.canonical_hash({"test-system-sign-of": custody})
    return signer, custody, public, descriptor
