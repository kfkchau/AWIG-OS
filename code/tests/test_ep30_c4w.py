# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-30-C4W — A CHECK OVER A STAMPED FIELD READS THE ACTING ACTOR, NOT A PARAMETER.

THE ONE SENTENCE THIS UNIT EXISTS FOR: a field an op STAMPS with the acting actor
(`stamp_actor`) is the ENGINE'S FACT — `payload[f] = actor` overwrites any caller value at
record time. A check that resolved its subject from that field THROUGH `p_in` read the
caller's PRE-STAMP value: a CLAIM about identity where the engine holds the fact. This unit
makes `_dispatch_check` resolve such a subject from `actor` — the same value the stamp
writes — for the one arm whose subject is an identity comparison (`require_prior`).

IT EXECUTES OWNER-RULED LAW AND MINTS NOTHING: design/41 Q1 (actor-slot-is-identity) and Q2
(verification order is law, identity first), both owner-ruled 2026-08-22, directed by archi
board :2610 direction B and countersigned :2616. NO new check kind, NO new vocabulary member
— `OP_CHECKS` and design/28 §5's table are untouched (R3 proves the alarm that would fire if
they were).

PREVENTIVE, NOT ACTIVE: NO shipped check reads its own stamped field today (A2), so NO
shipped verdict changes (A4). The seam is closed BEFORE a check is ever pointed at a stamped
field. The red worlds (§4) are where the guarantee is shown to bite.

EVERY VERIFICATION PROBE THIS UNIT RAN LANDS HERE AS A REGRESSION ROW (charter). Rows are
named for the plan's acceptance and red-world ids so a reader can pair them with
planning/evidence/EP-30-C4W/.

SELF-READING: A1/A4/R2/R3 read the engine's SOURCE, not only its behaviour. A claim that
`actor` is ONE binding, or that the diff is confined, or that no kind was added, is a claim
about what the code says — calling a function cannot discharge it.

THE REPO PACK IS NEVER WRITTEN. Every behavioural row drives a SCRATCH definition created
through the ordinary CREATE-OP door; SHM-GRANT / CREATE-ACCOUNT / VERIFY-ACCOUNT are read,
never amended.
"""

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from kernel import opdefs                                            # noqa: E402
from kernel.boot import build_kernel                                # noqa: E402
from kernel.blobs import BlobStore                                  # noqa: E402
from kernel.errors import OpError                                   # noqa: E402

OPDEFS_PATH = opdefs.__file__
with open(OPDEFS_PATH, encoding="utf-8") as _fh:
    OPDEFS_SRC = _fh.read()
PACK_PATH = os.path.join(ROOT, "src", "founding", "founding-pack.json")
DESIGN28 = os.path.join(ROOT, "design", "28-TARGET-STATE-HOST-KERNEL.md")

# The check-vocabulary comparator — the estate's own instrument for design/28 §5's gate.
# Loaded by path exactly as tests/test_checkvocab.py loads it (sys.path is not touched).
_CV_SPEC = importlib.util.spec_from_file_location(
    "govos_c4w_checkvocab", os.path.join(ROOT, "tools", "docmap", "checkvocab.py"))
cv = importlib.util.module_from_spec(_CV_SPEC)
_CV_SPEC.loader.exec_module(cv)


# ============================================================================ source helpers

def _run_def(src):
    """The `run(actor, params)` FunctionDef nested inside `_interpreter` — the enclosing scope
    the check dispatcher closes over. AST, not grep: the question is structural."""
    tree = ast.parse(src)
    interp = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "_interpreter")
    return next(n for n in ast.walk(interp)
                if isinstance(n, ast.FunctionDef) and n.name == "run")


def actor_rebindings(src):
    """Every place the name `actor` is BOUND inside `run`'s body other than its own signature.

    A binding is a Store of `actor`: an assignment target, an augmented/annotated assignment,
    a walrus, a for-target, a with-as, a comprehension target, or a `del`. `ast.walk` descends
    into the nested `_dispatch_check` scope — a rebinding there that shadowed the
    parameter before the stamp would also break the value-identity, so it is in scope for this
    walk. A `def`/`lambda` PARAMETER named `actor` would shadow too and is reported (none does).

    RETURNS the list of (lineno, kind) rebindings. EMPTY means `actor` is ONE binding — the
    parameter of `run` — read unchanged everywhere below, including the stamp at
    `payload[f] = actor`. This is A1's proof and R2's falsifier: plant a rebinding and it is
    non-empty."""
    run = _run_def(src)
    out = []
    for node in ast.walk(run):
        # a nested function/lambda parameter named `actor` shadows run's binding
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) and node is not run:
            args = node.args
            for a in (list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs)
                      + ([args.vararg] if args.vararg else []) + ([args.kwarg] if args.kwarg else [])):
                if a and a.arg == "actor":
                    out.append((a.lineno, "shadowing-parameter"))
        if isinstance(node, ast.Name) and node.id == "actor" and isinstance(node.ctx, (ast.Store, ast.Del)):
            out.append((node.lineno, type(node.ctx).__name__))
    return sorted(out)


def _fn_reads_actor_free(src, fn_name):
    """True iff the nested function `fn_name` LOADS `actor` and does not bind it — i.e. reads
    the enclosing `run`'s `actor` by closure."""
    run = _run_def(src)
    fn = next((n for n in ast.walk(run)
               if isinstance(n, ast.FunctionDef) and n.name == fn_name), None)
    if fn is None:
        return False
    loads = any(isinstance(n, ast.Name) and n.id == "actor" and isinstance(n.ctx, ast.Load)
                for n in ast.walk(fn))
    binds = any(isinstance(n, ast.Name) and n.id == "actor" and isinstance(n.ctx, ast.Store)
                for n in ast.walk(fn))
    params = {a.arg for a in fn.args.args}
    return loads and not binds and "actor" not in params


def require_prior_arm(src):
    """The SOURCE SPAN of `_dispatch_check`'s `require_prior` arm — from its `if` to the next
    `elif`. This is the exact span EP-30-K1's minimality gate reads, so this unit reads it the
    same way: the change is an OVERRIDE inside this arm, and the base caller-read must survive."""
    lines = src.splitlines()
    start = next(i for i, ln in enumerate(lines) if 'if c["check"] == "require_prior"' in ln)
    end = next(i for i in range(start + 1, len(lines)) if 'elif c["check"] == "sight"' in lines[i])
    return "\n".join(lines[start:end])


# ============================================================================ pack helpers

def stamp_actor_ops():
    """Every op definition in the founding pack that carries a non-empty `stamp_actor`,
    keyed by its declared name, with the fields A2/A4 read. Walks the whole JSON so a fourth
    op cannot hide in a structure a shaped probe guessed (the countersign's own caution)."""
    with open(PACK_PATH, encoding="utf-8") as fh:
        pack = json.load(fh)
    found = {}

    def walk(o):
        if isinstance(o, dict):
            if o.get("kind") == "op_definition" and (o.get("definition") or {}).get("stamp_actor"):
                found[o["name"]] = o["definition"]
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(pack)
    return found


def all_op_definitions():
    """Every op_definition in the pack, keyed by name — for the A4 sweep over all checks."""
    with open(PACK_PATH, encoding="utf-8") as fh:
        pack = json.load(fh)
    out = {}

    def walk(o):
        if isinstance(o, dict):
            if o.get("kind") == "op_definition" and o.get("definition") is not None:
                out[o["name"]] = o["definition"]
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(pack)
    return out


# ============================================================================ A1
class A1ValueIdentityCase(unittest.TestCase):
    """A1 — the value-identity :2154 left open. :2154 proved the NAME `actor` REACHABLE at the
    dispatch site (21 free names). It did NOT prove the VALUE `actor` HOLDS there is the value
    the stamp WRITES. These rows prove it: `actor` is one binding — run's parameter — read
    unchanged by both the dispatcher and the stamp, with no rebinding between."""

    def test_a1_actor_is_one_binding_with_no_rebinding_in_run(self):
        rebinds = actor_rebindings(OPDEFS_SRC)
        self.assertEqual(rebinds, [],
                         "`actor` is rebound inside run's body, so the value the dispatcher "
                         "reads may diverge from the value the stamp writes: %r" % (rebinds,))

    def test_a1_the_dispatcher_reads_actor_free_and_the_arm_overrides_a_stamped_subject(self):
        """The dispatcher reads run's `actor` by closure, and the `require_prior` arm keeps the
        base caller-read `p_in.get(c["param"])` while OVERRIDING it to `actor` when the subject is
        a field this op's OWN `stamp_actor` declares. The base read surviving is what keeps
        EP-30-K1's minimality gate green — the override is additive, not a replacement."""
        self.assertTrue(_fn_reads_actor_free(OPDEFS_SRC, "_dispatch_check"),
                        "the check dispatcher does not read run's `actor` by closure")
        arm = require_prior_arm(OPDEFS_SRC)
        self.assertIn('p_in.get(c["param"])', arm,
                      "the base caller-read was removed from the require_prior arm — that would "
                      "red EP-30-K1's minimality gate and move a caller-choosable subject")
        self.assertIn('d.get("stamp_actor")', arm,
                      "membership is not read from the op's own stamp_actor declaration — a "
                      "field-name string match would be a new latent kind (STOP §8.3)")
        self.assertIn("want = actor", arm,
                      "the arm does not override a stamped subject to the acting actor")
        self.assertNotIn("key_param", arm,
                         "the require_prior arm gained a record selector — out of this unit's scope")

    def test_a1_the_stamp_writes_the_same_free_actor(self):
        """`payload[f] = actor` at the stamp loop LOADS the same free `actor`. Read structurally
        so the identity is a fact about the tree, not a character match."""
        run = _run_def(OPDEFS_SRC)
        stamp_writes = [n for n in ast.walk(run)
                        if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Subscript)
                                and isinstance(t.value, ast.Name) and t.value.id == "payload"
                                for t in n.targets)
                        and isinstance(n.value, ast.Name) and n.value.id == "actor"]
        self.assertTrue(stamp_writes,
                        "the stamp `payload[f] = actor` was not found — A1's subject is gone")


# ============================================================================ A2
class A2StampActorOpsCase(unittest.TestCase):
    """A2 — the `stamp_actor` ops, re-taken from the pack. If the population differs from the
    enumerated set (an UNDECLARED op, or a check now reading a stamped field) this row REDS —
    which is stop condition §8.2 made visible: the unit's preventive shape would have become
    active. §A57 by-name COMPANION WIDEN (EP-50, VIEW-SERVICING): the population grew to FOUR —
    VIEW-SERVICE stamps `servicer` (the servicer is an ATTRIBUTION field, the engine's fact, so a
    servicing cannot be attributed to another — by-design, exactly like VERIFY-ACCOUNT:['verifier'],
    architect-cited board :3377). VIEW-SERVICE carries EMPTY checks (the CREATE-ACCOUNT group), so
    the preventive shape (a check reading its own stamped field) stays LATENT, not active."""

    def test_a2_exactly_four_ops_carry_stamp_actor_id_for_id(self):
        ops = stamp_actor_ops()
        got = {name: d["stamp_actor"] for name, d in ops.items()}
        self.assertEqual(got, {"SHM-GRANT": ["granter"],
                               "CREATE-ACCOUNT": ["founded_by"],
                               "VERIFY-ACCOUNT": ["verifier"],
                               "VIEW-SERVICE": ["servicer"]},
                         "the stamp_actor population moved: %r" % (got,))

    def test_a2_two_of_four_declare_non_empty_checks(self):
        ops = stamp_actor_ops()
        nonempty = sorted(n for n, d in ops.items() if d.get("checks"))
        self.assertEqual(nonempty, ["SHM-GRANT", "VERIFY-ACCOUNT"],
                         "the set of stamp_actor ops with non-empty checks moved: %r" % (nonempty,))
        # VIEW-SERVICE joins CREATE-ACCOUNT as a stamp_actor op with EMPTY checks (EP-50).
        for empty_checks_op in ("CREATE-ACCOUNT", "VIEW-SERVICE"):
            self.assertEqual(stamp_actor_ops()[empty_checks_op].get("checks") or [], [],
                             "%s grew a check" % empty_checks_op)

    def test_a2_neither_check_reads_its_own_stamped_field(self):
        """The deciding fact that makes this a PREVENTIVE unit. SHM-GRANT's check reads
        `region`; VERIFY-ACCOUNT's reads `account`/field `account_id`. Neither reads its own
        stamped field (`granter` / `verifier`)."""
        ops = stamp_actor_ops()
        for name in ("SHM-GRANT", "VERIFY-ACCOUNT"):
            d = ops[name]
            stamped = set(d["stamp_actor"])
            for c in d["checks"]:
                subject_keys = {c[k] for k in ("param", "target_param", "parent_param",
                                               "entity_kind_param", "term_param", "seq_param")
                                if k in c}
                self.assertEqual(subject_keys & stamped, set(),
                                 "%s's %s check resolves a subject from its own stamped field "
                                 "%r — the finding is now ACTIVE, not latent (STOP §8.2)"
                                 % (name, c.get("check"), subject_keys & stamped))


# ============================================================================ A3
class WorldCase(unittest.TestCase):
    """A real kernel over a temp record. Definitions enter through CREATE-OP, the ordinary
    runtime door, so a require_prior over a stamped field is a real dispatch, not a direct
    call to a guard."""

    def setUp(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        self.store, self.gate, self.views = build_kernel(
            os.path.join(d, "record.jsonl"), blobs=BlobStore(os.path.join(d, "blobs")))

    # a producer whose record's `tag` field carries whatever the caller passes — the prior
    # record a require_prior compares against.
    # `tag` carries an actor id ("owner") recorded INLINE and read back by the consumer's
    # require_prior/stamp_actor equality (the tests assert "tag = owner" and read the inline
    # value): STRUCTURAL. Content-homing would store only a hash and break that equality read.
    PROD = {"description": "a producer of prior records", "law_cited": "CAP-IS-LAW",
            "object_param": "tag", "params": {"tag": "required"},
            "structural_params": ["tag"], "payload_from": ["tag"]}

    def prod(self, tag):
        self.gate.execute("CREATE-OP", "owner", {"name": "C4W-PROD",
                                                 "definition": dict(self.PROD)})
        self.gate.execute("C4W-PROD", "owner", {"tag": tag})

    def consumer(self, stamp=True, name="C4W-CONS",
                 message="granter names no prior C4W-PROD tag"):
        """A consumer that DECLARES `granter` as a caller parameter AND (when stamp=True)
        stamps it — the exact shape R1 names: a caller value on a field the engine also
        stamps. Its one check is a require_prior whose subject param is `granter`. With
        `message=None` the check carries no custom message, so a refusal emits the engine's
        default string `... {field} = {want}` — which surfaces the RESOLVED subject value."""
        check = {"check": "require_prior", "action": "C4W-PROD", "field": "tag",
                 "param": "granter", "cite": "CAP-IS-LAW"}
        if message is not None:
            check["message"] = message
        d = {"description": "a consumer checking over a stamped field",
             "law_cited": "CAP-IS-LAW", "object_param": "subject",
             "params": {"subject": "required", "granter": "required"},
             # subject = inline object id; granter = an actor id stamped and recorded inline (the
             # test reads payload["granter"] == "owner"): both STRUCTURAL identifiers, not bodies.
             "structural_params": ["subject", "granter"],
             "payload_from": ["subject", "granter"], "checks": [check]}
        if stamp:
            d["stamp_actor"] = ["granter"]
        self.gate.execute("CREATE-OP", "owner", {"name": name, "definition": d})
        return name

    def refusal(self, name, params):
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError) as ctx:
            self.gate.execute(name, "owner", params)
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)
        return str(ctx.exception)


class A3DispatcherReadsActorCase(WorldCase):
    """A3 — the changed `_dispatch_check` resolves a require_prior over a stamped field from
    `actor`, not `p_in`. Proven by the OUTCOME turning on the ACTOR's value, never by the
    absence of an exception."""

    def test_a3_a_stamped_field_check_resolves_to_the_acting_actor(self):
        self.prod("owner")                       # a prior record whose tag == the acting actor
        self.consumer(stamp=True)
        # the caller sets the stamped field's parameter to a DIFFERENT value; it has no effect.
        res = self.gate.execute("C4W-CONS", "owner", {"subject": "x", "granter": "SOMEONE-ELSE"})
        self.assertIsNotNone(res, "the op refused where reading the actor must admit")
        rec = self.store.by_action("C4W-CONS")[-1]
        self.assertEqual((rec.get("payload") or {}).get("granter"), "owner",
                         "the record's granter is not the engine's fact (the acting actor)")

    def test_a3_the_resolved_value_IS_the_actor_not_merely_pass_through(self):
        """The proof that the resolved subject is the ACTOR and not something that happens to
        pass: with NO prior record carrying the actor's value, the same check REFUSES, and the
        refusal names the actor's value as the want."""
        self.prod("not-the-actor")               # a prior exists, but not for the actor
        self.consumer(stamp=True, message=None)  # default message surfaces the resolved `want`
        msg = self.refusal("C4W-CONS", {"subject": "x", "granter": "SOMEONE-ELSE"})
        self.assertIn("tag = owner", msg,
                      "the refusal's want is not the acting actor — the subject was not the actor")


# ============================================================================ R1
class R1ForgedParamReadsTheActorCase(WorldCase):
    """R1 — a caller-supplied value on the stamped field's parameter reads the ACTING actor
    anyway. CHANGE PRESENT: the value has no effect (the claim cannot displace the fact).
    CHANGE REMOVED: the value is read and the actor is not."""

    def test_r1_present_the_forged_param_has_no_effect(self):
        self.prod("owner")
        self.consumer(stamp=True)
        res = self.gate.execute("C4W-CONS", "owner", {"subject": "x", "granter": "FORGED-ACTOR"})
        self.assertIsNotNone(res,
                             "with the change present a stamped-field check must read the actor "
                             "and admit — the caller's claim on `granter` is inert")

    def test_r1_removed_via_an_unstamped_field_the_caller_value_is_read(self):
        """The override is `if c["param"] in stamp_actor: want = actor`, guarding the base read
        `want = p_in.get(c["param"])`. An op that does NOT stamp the field SKIPS the override and
        keeps the base read — byte-identical to the pre-change behaviour. So the same scenario
        with the field UNSTAMPED reproduces the removed behaviour in the LIVE engine: the caller's
        value is read and the check refuses."""
        self.prod("owner")
        self.consumer(stamp=False, name="C4W-CONS-UNSTAMPED")
        msg = self.refusal("C4W-CONS-UNSTAMPED", {"subject": "x", "granter": "FORGED-ACTOR"})
        self.assertIn("granter names no prior", msg,
                      "the unstamped field did not read the caller's value — the removed "
                      "behaviour was not reproduced")

    def test_r1_removed_on_a_genuinely_reverted_engine_the_forged_param_is_read(self):
        """The strongest 'change removed': a SUBPROCESS running a temp copy of the engine with the
        stamped-field OVERRIDE removed, so `require_prior` is back to the bare `want =
        p_in.get(c["param"])`. The stamped-field check then reads the caller's value and REFUSES —
        the finding, in the pre-change engine."""
        verdict = _reverted_engine_verdict()
        self.assertEqual(verdict, "REFUSE",
                         "the reverted engine did not read the caller's value (got %r)" % verdict)


def _reverted_engine_verdict():
    """Run the R1 scenario against a source-reverted copy of the engine, in a fresh process.
    Returns 'ADMIT' or 'REFUSE'. Reverting = removing the stamped-field OVERRIDE so require_prior
    is back to the bare caller-read; the substitution is asserted to have matched."""
    tmp = tempfile.mkdtemp()
    try:
        shutil.copytree(os.path.join(ROOT, "src"), os.path.join(tmp, "src"))
        p = os.path.join(tmp, "src", "kernel", "opdefs.py")
        with open(p, encoding="utf-8") as fh:
            s = fh.read()
        override = ('                    if c["param"] in (d.get("stamp_actor") or ()):\n'
                    '                        want = actor\n')
        assert override in s, "the stamped-field override was not found — the seam moved"
        s2 = s.replace(override, "", 1)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(s2)
        driver = textwrap.dedent('''
            import os, sys, tempfile
            sys.path.insert(0, sys.argv[1])
            from kernel.boot import build_kernel
            from kernel.blobs import BlobStore
            from kernel.errors import OpError
            d = tempfile.mkdtemp()
            store, gate, views = build_kernel(os.path.join(d, "r.jsonl"),
                                              blobs=BlobStore(os.path.join(d, "b")))
            gate.execute("CREATE-OP", "owner", {"name": "C4W-PROD", "definition":
                {"description": "p", "law_cited": "CAP-IS-LAW", "object_param": "tag",
                 "params": {"tag": "required"}, "structural_params": ["tag"],
                 "payload_from": ["tag"]}})
            gate.execute("C4W-PROD", "owner", {"tag": "owner"})
            gate.execute("CREATE-OP", "owner", {"name": "C4W-CONS", "definition":
                {"description": "c", "law_cited": "CAP-IS-LAW", "object_param": "subject",
                 "params": {"subject": "required", "granter": "required"},
                 "structural_params": ["subject", "granter"],
                 "stamp_actor": ["granter"], "payload_from": ["subject", "granter"],
                 "checks": [{"check": "require_prior", "action": "C4W-PROD", "field": "tag",
                             "param": "granter", "cite": "CAP-IS-LAW", "message": "no prior"}]}})
            try:
                gate.execute("C4W-CONS", "owner", {"subject": "x", "granter": "FORGED-ACTOR"})
                print("ADMIT")
            except OpError:
                print("REFUSE")
        ''')
        drv = os.path.join(tmp, "driver.py")
        with open(drv, "w", encoding="utf-8") as fh:
            fh.write(driver)
        out = subprocess.run([sys.executable, drv, os.path.join(tmp, "src")],
                             capture_output=True, text=True, timeout=120)
        return (out.stdout.strip().splitlines() or [out.stderr.strip()])[-1]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ============================================================================ R2
class R2ValueIdentityCanFailCase(unittest.TestCase):
    """R2 — A1 is not a tautology: it can report a broken premise. Plant a rebinding of
    `actor` inside run's body on a COPY of the source and A1's detector REDS, naming the
    divergence; the real source greens."""

    def test_r2_a_planted_rebinding_is_detected(self):
        planted = OPDEFS_SRC.replace(
            "        p_in = dict(params)\n",
            "        p_in = dict(params)\n        actor = \"REBOUND-ON-A-COPY\"  # R2 plant\n", 1)
        self.assertNotEqual(planted, OPDEFS_SRC, "the R2 plant matched nothing")
        rebinds = actor_rebindings(planted)
        self.assertTrue(rebinds,
                        "A1's detector did not see a planted rebinding — the row is a tautology")
        self.assertTrue(any(k == "Store" for _, k in rebinds),
                        "the planted rebinding was not read as a Store of `actor`: %r" % (rebinds,))

    def test_r2_the_real_source_has_no_rebinding(self):
        self.assertEqual(actor_rebindings(OPDEFS_SRC), [],
                         "the real source rebinds `actor` — A1 must green here")


# ============================================================================ R3
class R3ANewKindStopsCase(unittest.TestCase):
    """R3 — this unit may NOT mint its way out of the seam. Attempting the resolution as a new
    check kind REDS the estate's own comparator (design/28 §5's gate); the real fix adds no
    kind, so the comparator is green and OP_CHECKS is unchanged."""

    def test_r3_present_a_new_kind_reds_the_checkvocab_alarm(self):
        planted = OPDEFS_SRC.replace('OP_CHECKS = ("require_prior"',
                                     'OP_CHECKS = ("stamped_actor", "require_prior"', 1)
        self.assertNotEqual(planted, OPDEFS_SRC, "the R3 plant matched nothing")
        with open(DESIGN28, encoding="utf-8") as fh:
            _d28 = fh.read()
        undocumented, unbacked = cv.defect4(planted, _d28)
        self.assertEqual(undocumented, ["stamped_actor"],
                         "the comparator did not fire on a kind added with no §5 row")

    def test_r3_removed_the_real_fix_adds_no_kind(self):
        with open(DESIGN28, encoding="utf-8") as fh:
            _d28 = fh.read()
        undocumented, unbacked = cv.defect4(OPDEFS_SRC, _d28)
        self.assertEqual((undocumented, unbacked), ([], []),
                         "the real engine and §5's table diverge — the fix added a kind or row")

    def test_r3_op_checks_is_untouched_seventeen_kinds(self):
        self.assertEqual(len(opdefs.OP_CHECKS), 19,
                         "OP_CHECKS changed length — a kind was added or removed: %r"
                         % (opdefs.OP_CHECKS,))
        self.assertNotIn("stamped_actor", opdefs.OP_CHECKS,
                         "a stamped_actor kind reached the live vocabulary")


# ============================================================================ A4
class A4NoShippedCheckMovedCase(unittest.TestCase):
    """A4 — the tier row. No shipped check's resolved value moves, because none resolves a
    subject that is a stamped field of its own op. Proven over EVERY op in the pack, not only
    the three, and stated for the two shipped non-empty checks by name."""

    def test_a4_no_shipped_check_resolves_a_subject_that_is_its_own_stamped_field(self):
        moved = []
        for name, d in all_op_definitions().items():
            stamped = set(d.get("stamp_actor") or ())
            if not stamped:
                continue
            for c in (d.get("checks") or []):
                for key in ("param", "target_param", "parent_param", "entity_kind_param",
                            "term_param", "seq_param"):
                    if c.get(key) in stamped:
                        moved.append((name, c.get("check"), key, c.get(key)))
        self.assertEqual(moved, [],
                         "a shipped check resolves a subject from its own stamped field, so the "
                         "override WOULD move its value: %r" % (moved,))

    def test_a4_the_two_shipped_checks_resolve_unchanged_by_name(self):
        """SHM-GRANT (require_prior, param `region`) and VERIFY-ACCOUNT (require_prior, param
        `account`): the subject key is not in stamp_actor, so the override never fires and the
        base read `p_in.get(param)` stands — identical before and after."""
        ops = stamp_actor_ops()
        shm = ops["SHM-GRANT"]
        self.assertEqual(shm["checks"][0]["param"], "region")
        self.assertNotIn("region", shm["stamp_actor"])
        ver = ops["VERIFY-ACCOUNT"]
        self.assertEqual(ver["checks"][0]["param"], "account")
        self.assertNotIn("account", ver["stamp_actor"])


if __name__ == "__main__":
    unittest.main()
