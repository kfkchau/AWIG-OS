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
from .views import Views, VIEW_FILTER_DIMENSIONS, FOLD_NAMES, DERIVE_DIMENSIONS

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
    # THE READER OUTCOME (EP-MAINT-OUTSIDE-5, re-spec C; archi :4199) rides HERE transitively: with
    # lock=True, when a LIVE writer already holds this record in THIS process, the store opens as a
    # READER (store._reader) — no OS lock, every view computed, any append refused by name. Genesis
    # and the replays below are idempotent on an already-founded record (they append nothing on a
    # reconstruction reopen), so a second build_kernel over a live record reads and reconstructs
    # transparently; only a caller that then APPENDS through it trips the reader refusal.
    store = EventStore(file_path, lock=lock, require_rule_cited=True)
    views = Views(store)
    gate = Gate(store, views)  # views is REQUIRED (C0): no gate without its constitution guard
    gate.blobs = blobs  # content_params ops register only when the blob store is present
    _register_bootstrap(gate, store, views)
    register_opdef_ops(gate, store, views)
    genesis(store)
    replay_op_definitions(gate, store, views)
    # C7 P3 (design/54 §3 B11, §5 L16; archi :3993): DERIVE the seam's act set from the record. The
    # twelve act-kind DEFINITIONS are genesis-seeded rows; `replay_act_kinds` folds them and reconciles
    # the derivation against the seam's declared work (A2 + precision b), exactly as replay_op_definitions
    # rebuilds the op registry from CREATE-OP rows. Reads + reconciles + installs — it APPENDS NOTHING, so
    # build_kernel stays pack-exact (the founding roundtrip asserts a rebuild adds nothing). Inert on a
    # pre-1.55.0 world that carries no act-kind rows (the wire-at-birth idiom — founds exactly as before).
    replay_act_kinds(store)
    # EP-40 (:2769 R1): the engine attestation does NOT ride here. `build_kernel` stays pack-exact
    # — the founding roundtrip (test_ep14 TestFoundingRoundTrip) asserts a rebuild adds nothing, so
    # a boot append in this path is a founding-record divergence. The attestation is a COMPOSE-LAYER
    # act, ABOVE the founding boot (kernel/compose.build_full_kernel), through the gate.
    return store, gate, views


# ---- C7 P3: THE SEAM'S ACT SET DERIVED FROM THE RECORD (design/54 §3 B11, §5 L16; archi :3993) ----
# The twelve KINDS OF WORK the seam performs (bridge/host_seam.py ACT_KINDS) are genesis-seeded as
# CREATE-RULE rows of law — one per kind, each carrying its name, its portability label and its meaning
# (founding step "13-act-kind-definitions"). This is the DEFINITIONAL half of "our own kernel": its
# definition is rows in the record, its act set derived from them at build. The fold mirrors
# opdefs.live_definitions (the op registry rebuilt from CREATE-OP rows — "kill the registry, replay,
# identical") but reads the ACT-KIND LAW rows, NEVER the op_definition cell: an act kind is a rule, not
# an operation (archi :3993 precision a — no CREATE-OP, no new operation). L16: the set is a fold, never
# a truth beside the record; delete the built set and regenerate it and the same twelve come back.

#: The payload `kind` marking an act-kind definition row (distinct from "op_definition"/"view_definition";
#: NOT "act_kind", the unrelated op-level release-semantics field on op definitions).
ACT_KIND_RECORD_KIND = "seam_act_definition"


def live_act_kinds(store):
    """Fold the act-kind definition rows into the seam's act set {seam_kind: {"label", "meaning"}} —
    the seam's act set DERIVED from the record (B11). A fold over the CREATE-RULE rows whose payload
    kind is `seam_act_definition` (archi :3993 precision a: the derived act set is a fold over the
    act-kind law rules), never a stored status (L16). Kill it, replay, identical. A world with no such
    rows folds to {} (a pre-1.55.0 world — the wire-at-birth idiom; the caller stays inert)."""
    out = {}
    for e in store.all():
        p = e.get("payload") or {}
        if e.get("action") == "CREATE-RULE" and p.get("kind") == ACT_KIND_RECORD_KIND:
            out[p["seam_kind"]] = {"label": p["label"], "meaning": p["meaning"]}
    return out


def replay_act_kinds(store):
    """Derive the seam's act set from the act-kind rows at build (B11) and reconcile it against the
    seam's declared work: fold the rows, reconcile (host_seam — A2 + the site-vs-row label check,
    precision b; refuses on divergence), and install the derived set. APPENDS NOTHING (build_kernel
    stays pack-exact). Returns the derived act set, or None on a world with no act-kind rows (INERT —
    a pre-1.55.0 world derives nothing and founds exactly as before, the estate's wire-at-birth idiom;
    a PARTIAL set — some kinds present, others missing — is a corrupt founding and reconcile refuses it,
    never inert)."""
    from bridge import host_seam
    derived = live_act_kinds(store)
    if not derived:
        return None                                  # inert: no act-kind rows (pre-1.55.0 world)
    host_seam.install_derived_act_kinds(derived)     # reconciles (A2 + precision b), then installs
    return derived


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
        # A view is a standing rule (design/27 §4) in one of THREE forms: a FILTER view (trigger
        # `when` -> outcome `then`); a MASTER (`bind` names an S-plane fold, EP-08); or a DERIVED view
        # row (`derive = {from, where}` — a parent view narrowed by one closed dimension, C6a VT-3,
        # design/25 v2). All three vocabularies are CLOSED: a `when` dimension outside
        # VIEW_FILTER_DIMENSIONS, a `bind` outside FOLD_NAMES, or a `derive` dimension outside
        # DERIVE_DIMENSIONS is a nonconforming call refused before anything is written (the closure
        # discipline — an unknown filter/fold/dimension does not exist). A master keeps the DICT `when`
        # shape; it never carries a LIST trigger (that is executable law, the full-form pass's
        # territory).
        name = params["name"]
        bind = params.get("bind")
        derive = params.get("derive")
        if bind is not None and bind not in FOLD_NAMES:
            gate.refuse(actor, "CREATE-VIEW", "AR-2",
                        f'unknown fold "{bind}" — a master may bind only: ' + ", ".join(FOLD_NAMES))
        when = params.get("when") or {}
        for dim in when:
            if dim not in VIEW_FILTER_DIMENSIONS:
                gate.refuse(actor, "CREATE-VIEW", "AR-2",
                            f'unknown trigger dimension "{dim}" — a view may test only: '
                            + ", ".join(VIEW_FILTER_DIMENSIONS))
        # THE DERIVED-VIEW DOOR (C6a VT-3; design/25 v2 "the third view form"; design/53 L16; board
        # :3825). CREATE-VIEW is BOOT-REGISTERED (below, gate.register) — it has NO op definition, so
        # nothing here is a "declared structural param"; the door IS this inline code, mirroring the
        # bind/trigger closure above. A derive names its parent view and EXACTLY ONE closed dimension.
        # Four refusals, each an AR-2 that can fail; a well-formed derive is recorded (its serving —
        # narrowing the parent's output — is VT-3b, not here).
        if derive is not None:
            if bind is not None or when:
                gate.refuse(actor, "CREATE-VIEW", "AR-2",
                            "one form per row: a derived view carries neither a bind nor a when")
            where = derive.get("where") or {}
            if len(where) != 1:
                gate.refuse(actor, "CREATE-VIEW", "AR-2",
                            f"a derived view narrows by exactly one dimension; got {len(where)}")
            d_dim = next(iter(where))
            if d_dim not in DERIVE_DIMENSIONS:
                gate.refuse(actor, "CREATE-VIEW", "AR-2",
                            f'unknown derived dimension "{d_dim}" — a derive may narrow only: '
                            + ", ".join(DERIVE_DIMENSIONS))
            parent = derive.get("from")
            if parent not in views.view_definitions():
                gate.refuse(actor, "CREATE-VIEW", "AR-2",
                            f'derived-view parent "{parent}" names no view definition at head '
                            "— the parent must already be seeded")
        then = params.get("then") or {}
        if derive is not None:
            _w = derive["where"]; _d = next(iter(_w))
            text = f"derived view {name}: {derive.get('from')} narrowed by {_d}={_w[_d]}"
        elif bind:
            text = f"master view {name}: derived by the {bind} fold"
        else:
            text = (f"when a record matches {when} -> "
                    + (f"move it to {then['move_to']}" if then.get("move_to") else "surface it to the requester"))
        # Carries a rule_id: a view definition IS law (REQ-form), visible to active_rules,
        # contradiction-gated like any rule creation (ROOT-NEG-6). Same name = amendment.
        payload = {"kind": "view_definition", "rule_id": f"view:{name}", "polarity": "+",
                   "name": name, "when": when, "then": then, "text": text}
        if bind:
            payload["bind"] = bind            # a master names its fold; a runtime bind is ordinary tier
        if derive is not None:
            payload["derive"] = derive        # a derived row records its parent + one closed dimension
        if params.get("refresh") is not None:
            payload["refresh"] = params["refresh"]
        return {"actor": actor, "action": "CREATE-VIEW", "object": f"view:{name}", "rule_cited": "ROOT-NEG-6",
                             "payload": payload}
    gate.register("CREATE-VIEW",
                  {"description": "define a view: a filter ('when matches, move it'), a master (bind to a fold), "
                                  "or a derived row (derive: a parent view narrowed by one closed dimension)",
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


# ---- C7 P4: THE WAKE CHECKLIST — six verdicts as a genesis row before the first act --------------
# The boot-time self-check (design/54 §3 B4, §5 L3; design/47 §3 — genesis the standing guardian
# family, the wake checklist its BOOT size). Before the first ACTOR act, the machine records SIX
# verdicts about itself — body, chain, constitution, views, keys, account chain — as ONE genesis row,
# and REFUSES the first act on any failure. Each verdict is DERIVED from a mechanism that already
# exists (attestation.match_probe / store.verify_chain / the founding read-back / views.master over
# the fold set / keys.key_valid / views.chain_end + actor_grounded): the checklist COMPOSES the six,
# it authors no new check kind. It reads only the RECORD, the CONSTITUTION, the KEYS and the ACCOUNTS
# — never the performer beneath the effect seam (bridge/host_seam) — so it runs on the hosted estate
# today and is carried to our own core unchanged (PERFORMER-INDEPENDENT, archi :3946).
#
# THE GATING RULE IS GENESIS MACHINERY IN CODE, NOT FOUNDING DATA (archi ruling, coord 2026-09-11):
# the first act refused unless the six pass is a boot-path composition, so founding-pack.json is
# byte-unchanged and no version bump / bump-attestation / §A57 sweep is owed. It is NOT wired into
# build_full_kernel (whose founding roundtrip must stay pack-exact, and which composes many test
# worlds); it is the boot-point guardian a caller runs before its first actor act — the measured-boot
# "refuse-before-first-act" shape.
#
# THE CHECKLIST REFUSES, IT NEVER BLESSES (design/54 §3 B4; A5). A passing checklist PERMITS the first
# act; it adds no legitimacy — it does not touch the gate's per-act decision, so an act refused on its
# own merits stays refused though the checklist passed. The genesis row is a RECORD written by the one
# pen (the gate, a SYSTEM WRITE-ACTIVITY); it is NOT gated by its own checklist (coord 2026-09-11: the
# checklist gates the first ACTOR act, never the SYSTEM act that writes the row — no chicken-and-egg).

#: The six verdict names, in the design/54 §3 B4 order. A grow of this set is a deliberate edit.
WAKE_VERDICTS = ("body", "chain", "constitution", "views", "keys", "account_chain")

#: The WRITE-ACTIVITY object naming the genesis row the wake checklist records (the one pen).
WAKE_GENESIS_OBJECT = "wake-checklist"


class WakeRefused(RuntimeError):
    """The wake checklist REFUSED the first act: one or more of the six boot verdicts failed. Raised
    AFTER the genesis row has been recorded (the row names which verdicts failed), so the refusal is
    a fact of the record before the first actor act is stopped. A machine that wakes wrong refuses to
    act rather than acting wrongly (design/54 §3 B4). Carries `.failed` — the failed verdict names."""

    def __init__(self, failed):
        self.failed = list(failed)
        super().__init__(
            "the wake checklist refuses the first act — failed verdict(s): " + ", ".join(self.failed))


def _wake_body(store, views, src_dir=None):
    """(1) BODY — the attested member set verifies against its boot attestation. Reads the EXISTING
    boot-attestation row (compose.attest_boot) through `attestation.match_probe`: the running engine's
    recomputed attested-set digest equals the one the boot attestation recorded. ONE body verdict per
    boot — this reads the existing row, it never mints a second attestation (coord 2026-09-11). A
    tampered / missing member reddens it (match_probe matches=False); an engine that never attested is
    not a matching engine (attested=False)."""
    from . import attestation
    probe = attestation.match_probe(store, src_dir)
    ok = bool(probe.get("attested") and probe.get("matches"))
    if ok:
        return True, "attested set matches the boot attestation"
    if not probe.get("attested"):
        return False, "no boot attestation on record — the engine has never attested"
    changed = probe.get("changed") or []
    missing = probe.get("missing") or []
    return False, "attested set diverges from the boot attestation (changed=%s missing=%s)" % (changed, missing)


def _wake_chain(store, views, src_dir=None):
    """(2) CHAIN — the record chain walks clean end to end. `store.verify_chain` recomputes every
    link on demand; ok is the conjunction (a whole prefix that still hashes to the anchor, and no
    post-anchor `prev_hash` that no longer matches its predecessor). An UNANCHORED world is vacuously
    ok (nothing sealed to verify) — the same inert-when-not-applicable posture keys and the founding
    read-back carry. A broken sealed record reddens it (prefix_ok False, or a break_at seq)."""
    vc = store.verify_chain()
    if vc.get("ok"):
        return True, "verify_chain walks clean (verified_through=%s)" % vc.get("verified_through")
    if vc.get("prefix_ok") is False:
        return False, "the sealed prefix no longer hashes to the chain anchor"
    return False, "the chain breaks at seq %s" % vc.get("break_at")


def _wake_constitution(store, views, src_dir=None):
    """(3) CONSTITUTION — the world's own founding version reads back equal to the pack it was founded
    on. Reads the world's FIRST FOUND-STORE record's stamped `founding_version` (install.py's own
    read-back, VT-3c) and compares it to the live pack's `founding_version`. A world that cannot state
    its own founding version, or whose version differs from the pack, cannot confirm its constitution
    — the read-back verdict reds (the first act refused rather than run under an unconfirmed founding)."""
    from founding import install
    fs = store.by_action("FOUND-STORE")
    if not fs:
        return False, "no FOUND-STORE record — the world states no founding"
    world_version = (fs[0].get("payload") or {}).get("founding_version")
    if world_version is None:
        return False, "the FOUND-STORE record is unstamped — the world states no founding version"
    pack_version = install.founding_version()
    if world_version == pack_version:
        return True, "the world's founding version reads back equal to the pack (%s)" % world_version
    return False, "the world's founding version %s differs from the pack's %s" % (world_version, pack_version)


def _wake_views(store, views, src_dir=None):
    """(4) VIEWS — the fold set folds fresh without error. Runs every SEEDED MASTER view (a view
    definition that binds an S-plane fold) through `views.master`, forcing each fold value fresh from
    the record. A master bound to a not-yet-served fold returns None LAWFULLY (its serving is a later
    unit's work — that is not an error, it is an unbuilt fold); the verdict reds only when folding
    RAISES — a record the derived views cannot fold. Reads only the record through the view engine;
    never the performer."""
    try:
        for name, d in views.view_definitions().items():
            if not d.get("bind"):
                continue
            result = views.master(name)          # runs the bound fold FRESH; None == fold not yet served (lawful)
            if result is not None:
                _ = result["value"]              # force the fold value (a fold that errors raises here)
        return True, "the fold set folds fresh without error"
    except Exception as exc:                     # a fold the derived views could not compute
        return False, "a view folded with an error: %s: %s" % (type(exc).__name__, exc)


def _wake_keys(store, views, src_dir=None):
    """(5) KEYS — the chain-end's key is bound and valid, WHERE ONE IS BOUND. Reads the chain-end
    (the current root-authority holder) and `keys.key_valid`. INERT-WHEN-NOT-APPLICABLE (the estate's
    own posture, as bound_key is inert with no key law and verify_chain is vacuously ok unanchored):
    a chain-end with NO key records binds nothing at boot (the owner's real key ceremony is his own
    act) — vacuously valid. A chain-end whose key IS on record but no longer resolves (revoked /
    superseded to none) reddens it (key records present, key_valid False)."""
    from . import keys
    ce = views.chain_end()
    records = keys._key_records(store, ce)
    if not records:
        return True, "no key bound to the chain-end (%s) — vacuously valid" % ce
    if keys.key_valid(store, ce):
        return True, "the chain-end's key (%s) is bound and valid" % ce
    return False, "the chain-end's key (%s) is on record but no longer valid (revoked / unbound)" % ce


def _wake_account_chain(store, views, src_dir=None):
    """(6) ACCOUNT CHAIN — every account grounds to the chain-end / the founding anchors. The chain-end
    (`views.chain_end`) must derive to a root-authority holder (the authority chain intact end to end),
    and every minted actor must reach the constitution's root group through a containment chain
    (`views.actor_grounded`) — the ACTOR form of the anchor least-fixpoint `views._verified_accounts`
    rides for accounts, both bottoming out at the founding anchors. An orphan actor that grounds at no
    anchor reddens it."""
    ce = views.chain_end()
    if ce is None:
        return False, "the chain-end does not derive — the authority chain is broken"
    ungrounded = []
    for e in store.by_action("CREATE-ACTOR"):
        p = e.get("payload") or {}
        actor = p.get("actor_id") or e.get("object")
        if actor is not None and not views.actor_grounded(actor):
            ungrounded.append(actor)
    if ungrounded:
        return False, "actor(s) do not ground to the founding anchors: %s" % sorted(set(ungrounded))
    return True, "the chain-end derives and every actor grounds to the founding anchors"


_WAKE_VERDICT_FUNCS = {
    "body": _wake_body,
    "chain": _wake_chain,
    "constitution": _wake_constitution,
    "views": _wake_views,
    "keys": _wake_keys,
    "account_chain": _wake_account_chain,
}


def wake_verdicts(store, views, src_dir=None):
    """Compute the six wake verdicts, each DEFENSIVELY: a verdict whose computation RAISES is a FAILED
    verdict (a check that cannot complete cannot pass — the refusing default). Returns an ordered dict
    {name: {"ok": bool, "detail": str}} over `WAKE_VERDICTS`. Appends NOTHING — a pure read of the
    record / constitution / keys / accounts (the `wake` orchestrator below records the genesis row)."""
    out = {}
    for name in WAKE_VERDICTS:
        try:
            ok, detail = _WAKE_VERDICT_FUNCS[name](store, views, src_dir)
            out[name] = {"ok": bool(ok), "detail": detail}
        except Exception as exc:                 # a verdict that cannot be computed is a failed verdict
            out[name] = {"ok": False, "detail": "verdict raised: %s: %s" % (type(exc).__name__, exc)}
    return out


def wake(store, gate, views, src_dir=None):
    """THE WAKE CHECKLIST (design/54 §3 B4). Before the first ACTOR act: compute the six verdicts,
    record them as ONE genesis row through the gate (the one pen — a SYSTEM WRITE-ACTIVITY, not gated
    by its own checklist), and REFUSE the first act on any failure.

    Returns the verdicts dict when all six pass (the first act is PERMITTED). Raises `WakeRefused`
    (carrying the failed names) when any fails — AFTER the genesis row is recorded, so the refusal is
    a fact of the record. The genesis row (`WAKE_GENESIS_OBJECT`) carries every verdict's ok + detail
    and the refusal set, so a reader locates a wrong-woken machine's exact fault without re-deriving.

    REFUSES, NEVER BLESSES: this records verdicts and refuses; it makes no unlawful act lawful. It does
    not touch the gate's per-act decision, so an act refused on its own merits stays refused though the
    checklist passed (A5). PERFORMER-INDEPENDENT: the verdicts read only the record/constitution/keys/
    accounts, never the performer beneath the effect seam."""
    verdicts = wake_verdicts(store, views, src_dir)
    failed = [name for name in WAKE_VERDICTS if not verdicts[name]["ok"]]
    # THE GENESIS ROW — the one pen. A SYSTEM WRITE-ACTIVITY through the gate; it is NOT gated by its
    # own checklist (coord 2026-09-11), so it records the verdicts whether they pass or fail.
    try:
        gate.execute("WRITE-ACTIVITY", "SYSTEM", {"about": WAKE_GENESIS_OBJECT, "data": {
            "kind": "wake-checklist",
            "verdicts": {name: verdicts[name]["ok"] for name in WAKE_VERDICTS},
            "details": {name: verdicts[name]["detail"] for name in WAKE_VERDICTS},
            "all_pass": not failed,
            "refused_on": failed,
        }})
    except Exception:
        # The store's own append path folds every record; a record so corrupt that a VIEW cannot fold
        # it (the views verdict's failure mode) also stops the genesis row being appended. When a
        # verdict has ALREADY failed this is the SAME corruption — REFUSE the first act rather than let
        # the append error escape as if nothing were wrong (the row is unrecordable, but the machine
        # still must not act). When NOTHING failed, a store that cannot record the wake row is itself a
        # real failure and is not masked — the error propagates.
        if failed:
            raise WakeRefused(failed)
        raise
    if failed:
        raise WakeRefused(failed)
    return verdicts


# ---- C7 P6: THE GENESIS PAIR — two witness bodies, no shared write path; the row a mutual receipt ----
# design/54 §3 B5, §5 L4; design/47 §4 (the diving-buddy genesis, D07.10, canon). This EXTENDS P4's
# single-body genesis row (the wake checklist, above — READ and COMPOSED, never re-authored) into a
# TWO-BODY MUTUAL RECEIPT, and MIRRORS the dual-audit two-mutually-blind-witnesses idiom of
# kernel/protection.py (_sign_stream_a / _sign_stream_b, the two keys held apart, the third-party
# cross-check — READ and MIRRORED, never re-authored) at the GENESIS size. IT IS A SEPARATE MECHANISM:
# it imports no Protection and calls no dual-audit path; it composes `wake_verdicts` and records its own
# genesis row. (THE WRONG-REFERENCE TRAP the plan names, refused here in code: the dual audit is not
# imported and P4's `wake` is not rewritten — the pairing is a new mechanism at the genesis size.)
#
# THE SELF-ATTESTATION FLOOR, escaped by PAIRING not cleverness (design/47 §4): "can an insane checker
# check that it is sane?" — no. So TWO witness bodies with two SEPARATE bodies. In the guest a SECOND
# IMAGE stands in for the PHYSICAL chip body, which is the OWNER's, HELD BY NAME (design/54 Q3, I6): no
# hardware is bound here — the second image is a git-revertible stand-in (a second store copy). Each
# body (1) verifies the OTHER's genesis is CLEAN — the other's wake checklist (the six P4 verdicts)
# passes — and (2) checks the OTHER's genesis code-and-data against ITS OWN COPY. The genesis row
# records BOTH bodies' verdicts as a MUTUAL RECEIPT, never one signer's claim; ONE body alone cannot
# write it; a planted DISAGREEMENT refuses the wake.
#
# NO SHARED WRITE PATH (design/47 §4 — the common-mode failure one hand writing both defeats; the direct
# mirror of protection.py's "no signer both streams call"): the two bodies write APART — two separate
# images (two store objects) and two separate write-tokens (body ids). A mutual receipt requires TWO
# verdicts under TWO different bodies over TWO different images; a planted single hand (both verdicts
# under one body id, or both bodies over one image) is REFUSED.
#
# THE CHIP CARRIES THE GENESIS PART ONLY (design/54 L4, I4; design/47 §4): the checker (the genesis-
# checker code digest — witness-the-code, small enough to read whole) + what verifying needs (the
# attested-set digest, the chain anchor) + the anchor key (the chain-end and its bound key) — NEVER the
# constitution, which lives ONCE, in the record (a second copy is a second truth that can drift). A
# planted constitution copy on the genesis part is REFUSED (closed shape + the constitution content belt).
#
# NOT FOUNDING (archi countersign :3955; campaign design/54 v0.11 "the pairing code not a constitution
# rule"): the pairing is genesis MACHINERY IN CODE, exactly as P4's gating rule was — founding-pack.json
# is byte-unchanged, no version bump / bump-attestation / §A57. A BOOT ADDITION on the already-attested
# kernel/boot.py — no new src module, so ATTESTED_MEMBERS is unchanged (the count-pin rider is inert).
# PERFORMER-INDEPENDENT: the pairing reads GENESIS (the record / constitution / keys / accounts and the
# genesis-part digests), never the performer beneath the effect seam.

#: The mutual-receipt genesis row object (the one pen — extends P4's WAKE_GENESIS_OBJECT).
GENESIS_PAIR_OBJECT = "genesis-pair"

#: The CLOSED shape of the genesis part a witness body carries — the checker + digests + anchor key ONLY.
#: The chip carries THESE and no more; a planted constitution copy is an extra key (or smuggled content).
_GENESIS_PART_KEYS = frozenset({"checker", "digests", "anchor_key"})

#: The genesis-checker code member — the checker's own body, witness-the-code (the wake checklist and the
#: pairing both live in kernel/boot.py, an already-attested member).
_GENESIS_CHECKER_MEMBER = "kernel/boot.py"


class MutualReceiptRefused(RuntimeError):
    """The genesis pair REFUSED the wake. `.reason` is one of:
      "disagreement"         — the two bodies disagree (one finds the other not clean, or its genesis
                               code-and-data not matching its own copy); recorded in the genesis row,
                               then the wake is refused (design/54 B5; A3).
      "solo-write"           — one body alone tried to write the row (a verdict is absent); the mutual
                               receipt is not a solo signature (B5; A2).
      "shared-write-path"    — both verdicts under one body id, or both bodies over one image — one hand
                               writing both (the common-mode failure defeated; design/47 §4; A4).
      "constitution-on-chip" — the genesis part carries the constitution (an extra key or smuggled root-
                               law content); the chip carries the genesis part only (L4, I4; A4).
    Carries `.reason` and `.detail`."""

    def __init__(self, reason, detail=""):
        self.reason = reason
        self.detail = detail
        super().__init__(
            "the genesis pair refuses the wake — %s%s" % (reason, (": " + detail) if detail else ""))


def _constitution_markers():
    """The constitution's own distinctive identifiers, DERIVED from the live founding pack (never
    hardcoded): the root-law rule ids. A legitimate genesis part (digests, an account, a key) carries
    none of them; a planted constitution copy does. Version-robust — it reads the pack the world was
    founded on, so the belt does not go stale on a founding bump."""
    from founding import install
    return {law[0] for law in install.root_laws()
            if isinstance(law, (list, tuple)) and law and isinstance(law[0], str)}


def assert_chip_carries_genesis_part_only(part):
    """The chip body carries the GENESIS PART ONLY — checker + digests + anchor key, NEVER the
    constitution (design/54 L4, I4; design/47 §4). Two guards, each able to fail:
      1. CLOSED SHAPE — any key outside `_GENESIS_PART_KEYS` (a planted `constitution` copy) is refused.
      2. CONTENT BELT — the constitution's own root-law ids (derived from the live pack) must not appear
         anywhere in the serialized part (a constitution smuggled into an allowed field is refused).
    The constitution lives once, in the record; a second copy on the chip is a second truth that can
    drift. Raises `MutualReceiptRefused("constitution-on-chip", ...)`."""
    import json
    extra = set(part) - _GENESIS_PART_KEYS
    if extra:
        raise MutualReceiptRefused(
            "constitution-on-chip",
            "the genesis part carries key(s) outside {checker, digests, anchor_key}: %s "
            "— the chip carries the genesis part only, never the constitution" % sorted(extra))
    blob = json.dumps(part, sort_keys=True, default=str)
    for marker in _constitution_markers():
        if marker and marker in blob:
            raise MutualReceiptRefused(
                "constitution-on-chip",
                "the genesis part carries constitution content (%r) — the constitution lives once, in "
                "the record, never a copy on the chip" % marker)


def genesis_part(store, views, src_dir=None):
    """The GENESIS PART a witness body carries a copy of (design/54 L4; design/47 §4) — the checker +
    digests + anchor key, and NOTHING else. Re-derived from the body's own genesis:
      checker    the genesis-checker code digest (attestation's own per-member digest for the checker
                 module — witness-the-code; READ, not re-authored).
      digests    what verifying needs — the attested-set digest and the chain anchor (the sealed-prefix
                 hash, or None unanchored). NEVER the constitution.
      anchor_key the anchor identity (the chain-end) and its bound key (or None at boot — the owner's
                 real key ceremony is his own act, so a fresh world binds none: vacuous, exactly as P4's
                 keys verdict is inert with no key bound).
    Refuses if the derived part would carry the constitution (the belt is inert on a real part). Reads
    only the record / attested set / keys — never the performer (performer-independent)."""
    from . import attestation, keys
    from .store import CHAIN_ANCHOR_ACTION
    aset = attestation.attested_set(src_dir)
    ce = views.chain_end()
    anchors = store.by_action(CHAIN_ANCHOR_ACTION)
    part = {
        "checker": aset["members"][_GENESIS_CHECKER_MEMBER],
        "digests": {
            "attested_set": aset["set_digest"],
            "chain_anchor": (anchors[-1]["payload"]["prefix_hash"] if anchors else None),
        },
        "anchor_key": {"account": ce, "public_key": keys.bound_key(store, ce)},
    }
    assert_chip_carries_genesis_part_only(part)
    return part


class WitnessBody:
    """One of the TWO witness bodies of the genesis pair (design/47 §4). Two bodies with two SEPARATE
    images (`store`) and two SEPARATE write-tokens (`body_id`) — NO shared write path. A body holds ITS
    OWN COPY of the genesis part (snapshotted at construction — the chip's copy, carried apart from the
    other's) and witnesses the OTHER body:
      - the other's genesis is CLEAN: the other's wake checklist (the six P4 verdicts) all pass;
      - the other's genesis code-and-data MATCHES this body's own copy.
    A body's verdict is bound to ITS OWN `body_id` only — the genesis-size mirror of protection.py's
    per-stream key: the path names its own token and no other's, so the A4 no-shared-write-path guard
    proves the two verdicts come from two paths held apart."""

    def __init__(self, body_id, store, views, src_dir=None, own_part=None):
        self.body_id = body_id
        self.store = store
        self.views = views
        self.src_dir = src_dir
        # THIS body's OWN copy of the genesis part — the chip's copy, carried apart from the other's.
        self.own_part = own_part if own_part is not None else genesis_part(store, views, src_dir)
        assert_chip_carries_genesis_part_only(self.own_part)   # a body carries the genesis part only

    def witness(self, other):
        """THIS body's verdict ABOUT the `other` body — bound to THIS body's write-token ONLY (no shared
        write path). Returns {by, about, clean, matches}: `clean` is the other's wake checklist (the six
        P4 verdicts) all passing; `matches` is the other's LIVE genesis code-and-data equalling THIS
        body's own copy. Reads no performer (performer-independent)."""
        verdicts = wake_verdicts(other.store, other.views, other.src_dir)     # P4's six verdicts, composed
        clean = all(v["ok"] for v in verdicts.values())
        other_part = genesis_part(other.store, other.views, other.src_dir)    # the other's LIVE part
        matches = (other_part == self.own_part)                              # against THIS body's own copy
        return {"by": self.body_id, "about": other.body_id,
                "clean": bool(clean), "matches": bool(matches)}


def mutual_receipt(verdict_a, verdict_b):
    """Assemble the MUTUAL RECEIPT from TWO verdicts produced by two SEPARATE bodies (design/54 B5;
    design/47 §4). This is the THIRD-PARTY assembly — the genesis-size mirror of protection.py's
    `dual_blind_divergences`, which neither writer runs. REFUSES:
      - "solo-write":        a verdict is absent — one body alone cannot write the row (A2).
      - "shared-write-path": both verdicts under one body id — one hand writing both (A4).
    Returns {kind, receipt: {body_id: verdict, ...}, agree, bodies}. `agree` is BOTH bodies finding the
    other clean AND matching — the mutual receipt is two witnesses' agreement, or it is refused."""
    if verdict_a is None or verdict_b is None:
        raise MutualReceiptRefused(
            "solo-write",
            "the mutual receipt requires BOTH bodies' verdicts — one body alone cannot write it")
    if verdict_a["by"] == verdict_b["by"]:
        raise MutualReceiptRefused(
            "shared-write-path",
            "both verdicts under one body (%r) — one hand writing both (common-mode failure)"
            % verdict_a["by"])
    agree = bool(verdict_a["clean"] and verdict_a["matches"]
                 and verdict_b["clean"] and verdict_b["matches"])
    return {"kind": "genesis-pair",
            "receipt": {verdict_a["by"]: verdict_a, verdict_b["by"]: verdict_b},
            "agree": agree, "bodies": sorted([verdict_a["by"], verdict_b["by"]])}


def genesis_pair_wake(body_a, body_b, gate):
    """THE GENESIS PAIR (design/54 §3 B5, §5 L4; design/47 §4). Two witness bodies with NO shared write
    path each witness the OTHER; the genesis row records BOTH verdicts as a MUTUAL RECEIPT (extending
    P4's single-body genesis row); ONE body alone cannot write it; a planted DISAGREEMENT refuses the
    wake.

    Records ONE mutual-receipt genesis row through `gate` (the one pen — a SYSTEM WRITE-ACTIVITY, I1),
    then returns the receipt when the two bodies AGREE (the wake is permitted). Raises
    `MutualReceiptRefused` when they DISAGREE — AFTER the row is recorded, so the disagreement is a fact
    of the record (exactly as P4 records its genesis row before it refuses). The two bodies must sit on
    TWO SEPARATE images: a shared image is one hand writing both and is refused before any row.

    PERFORMER-INDEPENDENT: the pairing reads GENESIS (the wake checklist and the genesis-part digests),
    never the performer beneath the seam. NO physical body is bound — the second image is a revertable
    stand-in; the PHYSICAL chip body is the OWNER's, HELD (design/54 Q3, I6)."""
    if body_a.store is body_b.store:
        raise MutualReceiptRefused(
            "shared-write-path",
            "the two bodies share one image (store) — no shared write path: the two bodies write apart")
    va = body_a.witness(body_b)          # A's verdict about B — A's write-token only
    vb = body_b.witness(body_a)          # B's verdict about A — B's write-token only
    receipt = mutual_receipt(va, vb)     # THIRD-PARTY assembly; refuses solo-write / shared-write-path
    # THE MUTUAL-RECEIPT GENESIS ROW — the one pen (a SYSTEM WRITE-ACTIVITY through the gate), extending
    # P4's genesis row. Recorded whether the bodies agree or not (the row is the record of the pairing),
    # exactly as P4 records the six verdicts before it refuses.
    gate.execute("WRITE-ACTIVITY", "SYSTEM", {"about": GENESIS_PAIR_OBJECT, "data": {
        "kind": "genesis-pair",
        "verdicts": receipt["receipt"],
        "agree": receipt["agree"],
        "bodies": receipt["bodies"],
    }})
    if not receipt["agree"]:
        raise MutualReceiptRefused(
            "disagreement",
            "the two bodies disagree — the wake is refused: %s" % receipt["receipt"])
    return receipt


# ---- C7 P3: THE RUNNING KERNEL CHECKED AGAINST ITS DEFINITION ROWS AT EVERY WAKING ---------------
# design/54 §3 B11 (second half), §9 Q8 (:3985). At every waking the running kernel is checked against
# its own definition rows — BY HASH and BY DECLARED WORK — AFTER the two-body check (P6) and before the
# first actor act, or the first act is refused. On OUR OWN KERNEL the waking IS the boot (owner :3973),
# so this wiring — left out of build_full_kernel at P4 (whose founding roundtrip must stay pack-exact and
# which composes many test worlds on a performer that is not ours) — lands here as the boot-point guardian
# a caller runs after the two-body check, exactly as P4's wake and P6's pair are standalone boot-point
# guardians. It REFUSES, IT NEVER BLESSES (A5): a passing check permits the first act, adds no legitimacy.
#
# TWO INDEPENDENT SOURCES, never a match that cannot fail ([[feedback-match-is-not-independence]]):
#   ROWS (source A):    live_act_kinds(store) — the act-kind rows folded FRESH from the record.
#   RUNNING (source B):  the running kernel's DECLARED WORK — read from the code's declare_act SITES
#                        (host_seam.HostSeam.ACTS), the IMMUTABLE code half, NOT the installed derivation
#                        (which is source A itself and would make the check tautological).
# BY DECLARED WORK the kind sets must be equal (a kind in the running set not in the rows, or the reverse,
# is named); BY HASH the {kind: label} digests must be equal (a planted kernel whose site label differs
# from its row reds the hash). Either divergence refuses. On a world with no act-kind rows the check is
# INERT (vacuously conformant — a pre-1.55.0 world), the estate's inert-when-not-applicable posture; on
# our own 1.55.0 world the rows are present and the check is LIVE and CAN refuse (Q8b: an unrecordable
# genesis row still refuses, the failure carried, witnessed by the second body under P6).

#: The WRITE-ACTIVITY object naming the genesis row the kernel-conformance check records (the one pen).
KERNEL_CONFORMANCE_OBJECT = "kernel-conformance"


class KernelConformanceRefused(RuntimeError):
    """The running kernel's declared work diverges from its own definition rows — the first act is
    REFUSED (design/54 §3 B11; Q8). Raised AFTER the genesis row records the divergence, so the refusal
    is a fact of the record before the first actor act is stopped. Carries `.detail` — the divergence."""

    def __init__(self, detail):
        self.detail = detail
        super().__init__(
            "the running kernel diverges from its definition rows — the first act is refused: %s" % detail)


def _act_kind_digest(kind_to_label):
    # THE ONE-SERIALIZER LAW (design/37 §4; EP-34): a governed digest is taken over the estate's
    # SINGLE canonical serializer (kernel/canonical.py, the floor), never a second sort_keys json
    # dump. The act-kind {kind: label} map hashes through canonical_hash, the same floor views.py and
    # protection.py stand on. The value is derived (no external pin); its shape is "sha256:<hex>".
    from . import canonical
    return canonical.canonical_hash(kind_to_label)


def kernel_conformance_verdict(store):
    """Check the RUNNING KERNEL against its DEFINITION ROWS (design/54 B11 second half). Returns
    (ok, detail, digests) — two INDEPENDENT sources (the record vs the immutable code sites), so a
    planted divergence in EITHER reds the verdict. INERT (vacuously ok) on a world with no act-kind
    rows. Reads only the record and the seam's own declaration — never the performer beneath the seam
    (performer-independent, exactly as P4/P6)."""
    from bridge import host_seam
    rows = live_act_kinds(store)                                   # source A: the record, folded fresh
    # Source B — the running kernel's DECLARED WORK, from the IMMUTABLE code (never the installed
    # derivation): the DECLARED CLOSED SET (ACT_KINDS, the store-free gate) and the LABEL each declare_act
    # SITE carries. Reading both catches a plant of either — a kind added to the declared set, or a site
    # whose label (or kind) differs from its row.
    running_kinds = frozenset(host_seam.ACT_KINDS)
    running_labels = {}
    for _method, (kind, label) in host_seam.HostSeam.ACTS.items():
        running_labels[kind] = label
    running_digest = _act_kind_digest(running_labels)
    if not rows:
        return (True, "no act-kind rows on record — vacuously conformant (a world before the act-kind "
                "founding)", {"rows_digest": None, "running_digest": running_digest})
    rows_labels = {k: rows[k]["label"] for k in rows}
    rows_kinds = frozenset(rows_labels)
    rows_digest = _act_kind_digest(rows_labels)
    digests = {"rows_digest": rows_digest, "running_digest": running_digest}
    # BY DECLARED WORK — the kind sets must agree.
    if rows_kinds != running_kinds:
        return (False, "declared work diverges from the rows — running-only=%s rows-only=%s"
                % (sorted(running_kinds - rows_kinds), sorted(rows_kinds - running_kinds)), digests)
    # BY HASH — the {kind: label} digests must agree (catches a planted label the kind-set check misses).
    if rows_digest != running_digest:
        disagreeing = sorted(k for k in rows_labels if rows_labels[k] != running_labels.get(k))
        return (False, "the running kernel's declared labels diverge from the rows (hash mismatch): %s"
                % disagreeing, digests)
    return (True, "the running kernel's declared work matches its definition rows (%d kinds, hash %s)"
            % (len(rows_labels), rows_digest[:12]), digests)


def check_kernel_against_rows(store, gate):
    """THE A3 WAKE VERDICT (design/54 §3 B11; §9 Q8). At every waking — AFTER the two-body check (P6)
    and before the first actor act — check the running kernel against its definition rows, record the
    verdict as ONE genesis row (the one pen — a SYSTEM WRITE-ACTIVITY, not gated by its own check), and
    REFUSE the first act on divergence.

    Returns the verdict dict when the running kernel conforms (the first act is PERMITTED). Raises
    `KernelConformanceRefused` (carrying the divergence) when it diverges — AFTER the genesis row is
    recorded, so the refusal is a fact of the record. REFUSES, NEVER BLESSES (A5): it makes no unlawful
    act lawful; it does not touch the gate's per-act decision. If the record is so corrupt the genesis
    row cannot be appended (the unrecordable case, Q8b), the first act is STILL refused with the failure
    carried — witnessed by the second body under P6 over its own record file."""
    ok, detail, digests = kernel_conformance_verdict(store)
    try:
        gate.execute("WRITE-ACTIVITY", "SYSTEM", {"about": KERNEL_CONFORMANCE_OBJECT, "data": {
            "kind": "kernel-conformance",
            "ok": ok,
            "detail": detail,
            "rows_digest": digests["rows_digest"],
            "running_digest": digests["running_digest"],
        }})
    except Exception:
        # A record so corrupt a view cannot fold it also stops the genesis row appending. When the check
        # has ALREADY failed this is the same corruption — REFUSE the first act rather than let the append
        # error escape as if nothing were wrong. When NOTHING failed, a store that cannot record the row is
        # itself a real failure and is not masked — the error propagates.
        if not ok:
            raise KernelConformanceRefused(detail)
        raise
    if not ok:
        raise KernelConformanceRefused(detail)
    return {"ok": ok, "detail": detail, "rows_digest": digests["rows_digest"],
            "running_digest": digests["running_digest"]}
