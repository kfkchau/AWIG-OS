"""gov-os kernel — boot: the foundational op HANDLERS + the installer call.

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
    return store, gate, views


def _register_bootstrap(gate, store, views):
    def create_info(actor, params):
        return {"actor": actor, "action": "CREATE-INFO",
                             "object": params["content"], "rule_cited": "ROOT-NEG-5"}
    gate.register("CREATE-INFO",
                  {"description": "mint an information object", "rules": ["ROOT-NEG-5"],
                   "params": {"content": "required"}}, create_info)

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
