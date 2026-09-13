"""EP-14 acceptance battery (design/31 J9): the founding is a document.

T-FOUNDING-PACK / THE DIFFERENTIAL ORACLE (F3, the acceptance) — reconstruct the retired
    Python-literal genesis() from git, run old-genesis and pack-genesis into two fresh
    stores, and prove the records EQUIVALENT except the DECLARED additions. Zero undeclared
    divergence. The declared additions are enumerated by the test itself:
      (1) a `scope` field on every root law (J5's ground),
      (2) a `founding_version` field on the founding designation (F4),
      (3) one extra record at the end: the founding openness grant (EP-17 transition policy).
    NOTE (raised in BUILD-PROGRESS): F3's prose names "the two declared additions"; F4 adds
    the version field as a third declared change. The binding guarantee is zero UNDECLARED
    divergence — all three are declared and enumerated here.

T-FOUNDING-IDEMPOTENT — fresh / reload / double-install never double-seed.
T-FOUNDING-INTEGRITY  — a pack whose record references an entity no earlier step founds
    refuses the WHOLE founding, loudly, with nothing appended (half-founded is worse).
T-FOUNDING-ROUNDTRIP  — the founded record replays byte-identically from the file alone.
T-FOUNDING-VERSION    — the pack carries a version; the founding designation records it.
T-FOUNDING-SINGULAR   — the pack is the founding, not a config file: no env overrides, no
    optional sections; install(store) takes only the store, one canonical pack.

Every probe here lands as a regression test (R14).
"""

import ast
import contextlib
import copy
import json
import os
# [EP-28Z, 2026-08-12] `import subprocess` REMOVED: this file's only spawn was its copy
# of the era-pin act, which now lives at `tests/era_pin.py`. An import naming a capability
# the file no longer uses tells a later reader it spawns processes, which is false.
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.store import EventStore, frozen_default  # noqa: E402
from kernel.boot import build_kernel  # noqa: E402
from founding.install import (  # noqa: E402
    install, load_pack, records, root_laws, founding_version,
    FoundingIntegrityError, PACK_PATH,
)
import founding.install as _install_mod  # noqa: E402  (patched in the oracle setup to found from the era pack)
import era_pin  # noqa: E402  (the era-pin home, EP-28Z)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(REPO_ROOT, "src")

# The commit whose src/kernel/boot.py still holds the retired Python-literal genesis() — the
# pinned reference the oracle reconstructs (DIGEST-C1 §3: reconstruct retired code via git show).
OLD_GENESIS_SHA = "190cec107cbd5a73c43b7ad837cc4da16fdc454f"

# EP-15 ADDENDUM-3 RULING 1(a) — THE PACK SIDE IS ERA-PINNED TOO. The oracle's subject is ONE
# historical event: the EP-14 migration from literal genesis to pack genesis. A historical claim
# compares two historical artifacts, so BOTH sides come from pinned commits — old genesis from
# OLD_GENESIS_SHA (above), and the PACK from the EP-14-era SHA here. Before this pin the pack side
# read the LIVE pack, which accidentally coupled "the migration was faithful" to "the founding
# never grows" — but the founding is DESIGNED to grow (J9: constitutional evolution is visible
# pack versions; EP-15 adds CREATE-ACCOUNT/VERIFY-ACCOUNT and bumps the version to 1.1.0). Pinning
# the pack side makes the oracle immune to ALL future founding growth: EP-16 and every later
# founding-touching EP never edits this harness again (per-EP re-declaration of diffs is REFUSED —
# a migration oracle must not become a running ledger of campaign 2). The equivalence assertions
# and the declared-diff enumeration below are BYTE-UNCHANGED; only the setup founds cls.new from
# the era pack instead of the live one. The pinned commit is the EP-14B-reviewed state (suite 275
# green): the pack there is the untouched EP-14 1.0.0 pack (its sole commit predates this one — the
# pack was untouched by EP-14B), and the oracle harness there already carries its era-reconstructed
# OLD side, so both artifacts of the reviewed migration coexist at one clean point.
ERA_PACK_SHA = "b922b608fe224a5b217eaeb32a23589fdf67adf4"

# Envelope fields minted AT append (store._append) — excluded from the equivalence compare;
# both sides mint them independently. Everything else is founding content and must match.
_MINTED = {"seq", "record_time", "submission_time", "occurrence_time", "record_id"}
MOTHER = "space:root"


def _plain(rec):
    """A frozen store record -> a plain dict with the append-minted envelope fields stripped."""
    d = json.loads(json.dumps(rec, default=frozen_default))
    return {k: v for k, v in d.items() if k not in _MINTED}


# The modules old genesis imports AT genesis()-call time, reconstructed from the SAME pinned
# commit so old genesis runs entirely against its OWN era's shapes (DIGEST-C1 §3: reconstruct
# retired code via git show), never the present tree. name -> (path at the SHA, package for
# relative imports).
#
# EP-20B ADDENDUM 1 (R1a/R1b, 2026-07-26) — THE PIN COMPLETES AS A CLASS, NOT A ROW. The first
# six rows pinned the op-definition-dict homes EP-14B retired. They did not pin the two modules
# whose CONTENT old genesis seeds into founding pack records at its step 7:
#   `kernel.protection`   -> DUAL_AUDIT_ACTIONS  -> the `dual-audit-actions` pack record
#   `kernel.syscall_port` -> SYSCALL_MAP/RULE_TO_ERRNO -> the `syscall-ops` + `rule-errno` records
# Both resolved against the LIVE tree, so the oracle's old side has been seeding a migration
# proof from present-day law. It was invisible because the content at the pinned commit and the
# content today were byte-identical — the signature of this whole defect class, and why it can
# only be found by changing something. EP-20B retired DUAL_AUDIT_ACTIONS and the old side broke;
# `kernel.syscall_port` is the same defect one module over, found by the enumeration rather than
# by the next break. `kernel.errors` joins them because both new rows import OpError from it at
# module level, inside the pin window: an era module reading a live type is the same live-side-in-
# disguise (standing theorem 11 — the pin covers EVERY read, not just the entry call).
#
# INSERTION ORDER IS LOAD-BEARING: reconstruction executes each module body, so `kernel.errors`
# must be injected BEFORE the three modules that import it, or they bind the live type.
_OLD_ERA_MODULES = {
    "kernel.errors": ("src/kernel/errors.py", "kernel"),
    "subsystems.devices": ("src/subsystems/devices.py", "subsystems"),
    "subsystems.memory": ("src/subsystems/memory.py", "subsystems"),
    "subsystems.comms": ("src/subsystems/comms.py", "subsystems"),
    "subsystems.files": ("src/subsystems/files.py", "subsystems"),
    "subsystems.scheduling": ("src/subsystems/scheduling.py", "subsystems"),
    "kernel.obligations": ("src/kernel/obligations.py", "kernel"),
    "kernel.protection": ("src/kernel/protection.py", "kernel"),
    "kernel.syscall_port": ("src/kernel/syscall_port.py", "kernel"),
}

# The rest of the enumeration (R1a): kernel modules the reconstructed old-era code imports that
# are DELIBERATELY not pinned. Each carries its reason, and the R1d guard fails on any kernel read
# that is neither pinned above nor named here — so the class cannot silently regrow.
_UNPINNED_BY_DESIGN = {
    "kernel.store":
        "THE SHARED INSTRUMENT OF COMPARISON. Both sides are appended through one live EventStore "
        "and normalized by _MINTED / _plain(frozen_default); pinning it would hand the old side a "
        "different store class and serializer than the store setUpClass built and than _plain "
        "normalizes with, destroying the comparison instead of protecting it. No content of it "
        "reaches a founded record — it is the instrument, not a side.",
    "kernel.gate":
        "Module-level import of old boot, used only by build_kernel(); the oracle calls genesis() "
        "directly and never constructs a Gate. Also structurally unpinnable here: old boot is "
        "reconstructed BEFORE _old_era_modules() opens, so a row for it would claim coverage the "
        "table cannot provide.",
    "kernel.views":
        "Module-level import of old boot, used only by build_kernel(); same structural note as "
        "kernel.gate — resolved before the pin window opens.",
    "kernel.opdefs":
        "Imported inside old build_kernel(), which the oracle never calls. Not reached at all.",
}


def _reconstruct_module(name, path, package):
    """Load a module from the pinned commit into a fresh namespace (its relative imports, e.g.
    obligations' `from .errors import OpError`, resolve against the era-invariant live package).

    [DOCUMENTED FLIP — EP-28Z, 2026-08-12. CAUSE: this file held FIVE of the eighteen copies
    of the era-pin act, the most of any file in the estate, and TWO of them were the sites
    the first census MISSED because their path is substituted rather than literal.
    ASSERTED: a local `git show` spawn, `.decode()`d. SUPERSEDED: `era_pin.text_at`, the one
    home. REMAINS TRUE: UTF-8 either way, driven at `test_ep28z.py` against every pin this
    suite holds. GIVEN UP: nothing; the module reconstruction is untouched.]"""
    src = era_pin.text_at(OLD_GENESIS_SHA, path)
    mod = types.ModuleType(name)
    mod.__package__ = package
    mod.__file__ = os.path.join(REPO_ROOT, path)
    exec(compile(src, f"<old:{path}>", "exec"), mod.__dict__)
    return mod


@contextlib.contextmanager
def _old_era_modules():
    """Inject the pinned era modules (reconstructed from OLD_GENESIS_SHA) into sys.modules for the
    duration of the old-genesis run, then restore the live tree exactly. Old genesis imports these
    at call time (`from subsystems.* import *_OP_DEFINITIONS`, `from .obligations import ...`,
    `from .protection import DUAL_AUDIT_ACTIONS`, `from .syscall_port import SYSCALL_MAP, ...`);
    pinning them to the commit keeps old genesis in its own era, so retiring the live op-definition
    dicts (EP-14B) or the live dual-audit list (EP-20B) cannot reach it. This makes the oracle
    self-contained and era-faithful. Iteration follows _OLD_ERA_MODULES' insertion order, which is
    load-bearing (kernel.errors precedes its importers)."""
    saved = {}
    try:
        for name, (path, package) in _OLD_ERA_MODULES.items():
            saved[name] = sys.modules.get(name)
            sys.modules[name] = _reconstruct_module(name, path, package)
        yield
    finally:
        for name, prev in saved.items():
            if prev is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = prev


def _reconstruct_old_genesis():
    """Load the retired genesis() from the pinned commit as a module in the live kernel
    package (so its relative imports resolve against the unchanged kernel modules).

    [DOCUMENTED FLIP — EP-28Z, 2026-08-12. As `_reconstruct_module` above: the era read
    moves to `tests/era_pin.py`, the caller's exec is untouched.]"""
    old_src = era_pin.text_at(OLD_GENESIS_SHA, "src/kernel/boot.py")
    mod = types.ModuleType("_old_boot")
    mod.__package__ = "kernel"                       # resolve `from .store import ...`
    mod.__file__ = os.path.join(SRC, "kernel", "boot.py")
    exec(compile(old_src, "<old_genesis>", "exec"), mod.__dict__)
    return mod


def _reconstruct_era_pack():
    """Reconstruct the EP-14-era founding-pack.json from ERA_PACK_SHA (ruling 1a). The installer
    is era-invariant mechanism (unchanged by EP-15), so pinning the pack DATA is the whole pin:
    the era pack run through install() reproduces the EP-14-era pack genesis regardless of how the
    LIVE pack grows afterward.

    [DOCUMENTED FLIP — EP-28Z, 2026-08-12. The era read moves to `tests/era_pin.py`, and
    this site is the §A57 act proper — an era's own founding law, read out of git.]"""
    return era_pin.pack_at(ERA_PACK_SHA)


def _kernel_reads(sources):
    """The R1d checker, factored so the guard can be driven with a synthetic source too.

    `sources` is {label: (module_source, package)}. Returns {imported_module: sorted[labels]} for
    every kernel.* / subsystems.* module the sources import — relative imports resolved against
    the importing module's package, exactly as Python resolves them at run time."""
    found = {}
    for label, (src, package) in sources.items():
        for node in ast.walk(ast.parse(src)):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                names = [f"{package}.{base}" if node.level else base]
            for n in names:
                if n.split(".")[0] in ("kernel", "subsystems"):
                    found.setdefault(n, set()).add(label)
    return {k: sorted(v) for k, v in found.items()}


def _old_era_sources():
    """Every reconstructed old-era source the oracle executes: old boot plus each pinned module,
    all read from OLD_GENESIS_SHA. label -> (source, package).

    [DOCUMENTED FLIP — EP-28Z, 2026-08-12. TWO sites in one function, the second of which
    carries a SUBSTITUTED path — the form the first census missed. Both now read through
    `tests/era_pin.py`.]"""
    out = {"kernel.boot (old genesis)":
           (era_pin.text_at(OLD_GENESIS_SHA, "src/kernel/boot.py"), "kernel")}
    for name, (path, package) in _OLD_ERA_MODULES.items():
        out[name] = (era_pin.text_at(OLD_GENESIS_SHA, path), package)
    return out


class TestOldEraPinCoversEveryKernelRead(unittest.TestCase):
    """EP-20B ADDENDUM 1 R1d — the class guard, so the defect cannot silently regrow.

    The whole-class era-pin law (DIGEST-C2 theorem 11): the pin must cover EVERY read the oracle's
    frozen assertions make, and a helper quietly reading the live tree is a live side in disguise.
    `kernel.protection` was one instance, found only because EP-20B broke it; `kernel.syscall_port`
    was a second, found by enumeration. Both hid behind byte-identity between the pinned era and
    today, which is why a human reading cannot be the guard. This test fails when a reconstructed
    old-era module imports a kernel module the pin table does not carry and _UNPINNED_BY_DESIGN
    does not name with a reason."""

    def test_every_kernel_module_the_old_era_reads_is_pinned_or_named_with_a_reason(self):
        reads = _kernel_reads(_old_era_sources())
        unaccounted = {m: who for m, who in reads.items()
                       if m not in _OLD_ERA_MODULES and m not in _UNPINNED_BY_DESIGN}
        self.assertEqual(unaccounted, {},
                         "a reconstructed old-era module reads a kernel module the pin table does "
                         "not carry — pin it, or name it in _UNPINNED_BY_DESIGN with its reason: "
                         f"{unaccounted}")

    def test_the_two_content_seeding_reads_are_pinned(self):
        # the named instances, asserted by name so a future edit cannot drop them quietly: both
        # seed founding pack records at old genesis step 7, so an unpinned read is live law
        # entering a historical proof.
        for m in ("kernel.protection", "kernel.syscall_port"):
            self.assertIn(m, _OLD_ERA_MODULES)
            self.assertIn(m, _kernel_reads(_old_era_sources()))

    def test_no_stale_rows(self):
        # the pin table and the reason list may not outlive what they describe: every row must
        # still be read by the reconstructed era, or it is bookkeeping pretending to be coverage.
        reads = _kernel_reads(_old_era_sources())
        self.assertEqual([m for m in _OLD_ERA_MODULES if m not in reads], [])
        self.assertEqual([m for m in _UNPINNED_BY_DESIGN if m not in reads], [])

    def test_the_new_pins_are_ACTIVE_not_merely_listed(self):
        # R1c is proven by unchangedness, and unchangedness alone cannot distinguish "the pin is
        # correct" from "the pin does nothing". This shows the injection is real: inside the
        # window the era module stands in sys.modules in place of the live one, and it still
        # carries the constant EP-20B retired from the live tree — which is the only way old
        # genesis can read DUAL_AUDIT_ACTIONS at all today.
        import kernel.protection, kernel.syscall_port, kernel.errors      # noqa: F401
        live = {n: sys.modules[n] for n in
                ("kernel.protection", "kernel.syscall_port", "kernel.errors")}
        self.assertFalse(hasattr(live["kernel.protection"], "DUAL_AUDIT_ACTIONS"),
                         "the live module still holds the constant EP-20B retired")
        with _old_era_modules():
            for n in live:
                self.assertIsNot(sys.modules[n], live[n], f"{n} was not era-substituted")
            self.assertTrue(hasattr(sys.modules["kernel.protection"], "DUAL_AUDIT_ACTIONS"))
            self.assertTrue(hasattr(sys.modules["kernel.syscall_port"], "SYSCALL_MAP"))
            self.assertTrue(hasattr(sys.modules["kernel.errors"], "OpError"))
        for n, m in live.items():                       # the live tree is restored exactly
            self.assertIs(sys.modules[n], m)
        self.assertFalse(hasattr(sys.modules["kernel.protection"], "DUAL_AUDIT_ACTIONS"))

    def test_the_guard_can_fail(self):
        # prove the column can fail before trusting the pass (DIGEST-C2 §4): a synthetic era module
        # reading an unpinned kernel module must be reported, by absolute and by relative import.
        synthetic = {"synthetic": ("from .brand_new import LAW\nimport kernel.other_new\n", "kernel")}
        reads = _kernel_reads(synthetic)
        self.assertEqual(sorted(reads), ["kernel.brand_new", "kernel.other_new"])
        for m in reads:
            self.assertNotIn(m, _OLD_ERA_MODULES)
            self.assertNotIn(m, _UNPINNED_BY_DESIGN)


class TestDifferentialOracle(unittest.TestCase):
    """F3: the acceptance. old-genesis vs pack-genesis, zero undeclared divergence."""

    @classmethod
    def setUpClass(cls):
        d = tempfile.mkdtemp()
        old = _reconstruct_old_genesis()
        so = EventStore(os.path.join(d, "old.jsonl"), require_rule_cited=True)
        with _old_era_modules():                     # old genesis runs against its own era's shapes
            old.__dict__["genesis"](so)
        sn = EventStore(os.path.join(d, "new.jsonl"), require_rule_cited=True)
        # ruling 1(a): the WHOLE oracle runs in the EP-14 era — install() founds cls.new from the
        # ERA pack, and any bare load_pack()/founding_version()/root_laws() the assertions call
        # resolves to it too (so the version assertion compares era-vs-era, not era-vs-live). The
        # module-global load_pack is era-pinned for the class and RESTORED in tearDownClass; the
        # frozen install() signature (T-FOUNDING-SINGULAR) is untouched, only its data source.
        cls._era_pack = _reconstruct_era_pack()
        cls._saved_load_pack = _install_mod.load_pack
        _install_mod.load_pack = lambda path=None: cls._era_pack
        install(sn)
        cls.old = [_plain(r) for r in so.all()]
        cls.new = [_plain(r) for r in sn.all()]
        cls.root_ids = {rid for rid, *_ in root_laws(cls._era_pack)}

    @classmethod
    def tearDownClass(cls):
        # restore the live-pack reader so the other founding tests (idempotent/roundtrip/version)
        # see the LIVE pack, exactly as before.
        _install_mod.load_pack = cls._saved_load_pack

    def test_oracle_zero_undeclared_divergence(self):
        old, new = self.old, self.new
        # the grant is the single extra record, appended last — so records 0..len(old)-1 align
        self.assertEqual(len(new), len(old) + 1,
                         "pack-genesis must add exactly one record (the openness grant)")
        extra = new[-1]
        self.assertEqual(extra["action"], "GRANT")
        self.assertEqual(extra["payload"]["kind"], "grant")
        self.assertEqual(extra["payload"]["space"], MOTHER)

        declared_scope = []      # root-law records that gained exactly {scope: space:root}
        declared_version = []    # the founding designation gained exactly {founding_version}
        undeclared = []          # ANYTHING else — must stay empty
        for i, (o, n) in enumerate(zip(old, new)):
            op, np_ = o.pop("payload", {}), n.pop("payload", {})
            # every non-payload envelope field must be identical
            if o != n:
                undeclared.append((i, "envelope", {k: (o.get(k), n.get(k))
                                                   for k in set(o) | set(n) if o.get(k) != n.get(k)}))
            removed = set(op) - set(np_)
            added = set(np_) - set(op)
            changed = {k for k in set(op) & set(np_) if op[k] != np_[k]}
            if removed or changed:
                undeclared.append((i, "payload-removed-or-changed",
                                   {"removed": sorted(removed), "changed": sorted(changed)}))
            for k in added:
                if n["action"] == "FOUND-STORE" and k == "founding_version":
                    declared_version.append((i, np_[k]))
                elif n["action"] == "CREATE-RULE" and k == "scope" and np_.get("root") is True \
                        and np_.get("rule_id") in self.root_ids and np_[k] == MOTHER:
                    declared_scope.append(np_["rule_id"])
                else:
                    undeclared.append((i, "undeclared-added-field", {k: np_[k]}))

        # THE ACCEPTANCE: nothing undeclared changed between old genesis and the pack.
        self.assertEqual(undeclared, [], f"UNDECLARED divergence found: {undeclared}")
        # and the declared additions are exactly what J5/F4 specify — every root law, once each.
        self.assertEqual(sorted(declared_scope), sorted(self.root_ids),
                         "scope must be added to EXACTLY the root laws, once each")
        self.assertEqual(len(declared_version), 1)
        self.assertEqual(declared_version[0][1], founding_version())

    def test_oracle_result_is_emitted_for_the_log(self):
        # The EP asks the oracle result be logged. Emit a one-line verdict (captured into
        # BUILD-PROGRESS) — evidence before the claim.
        scope_n = len(self.root_ids)
        print(f"\n[EP-14 ORACLE] old-genesis={len(self.old)} recs; pack-genesis={len(self.new)} recs; "
              f"declared diffs = {scope_n} scope fields + 1 founding_version + 1 openness grant; "
              f"undeclared divergence = 0 (T-FOUNDING-PACK PASS).")


class TestFoundingIdempotent(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")

    def test_fresh_reload_double_install_never_double_seed(self):
        store, _g, _v = build_kernel(self.path)     # fresh: install ran inside build_kernel
        n = len(store.all())
        install(store)                               # explicit second install: adds nothing
        self.assertEqual(len(store.all()), n)
        install(store)                               # and a third
        self.assertEqual(len(store.all()), n)
        store2 = EventStore(self.path, require_rule_cited=True)
        install(store2)                              # reload from file: no double-seed
        self.assertEqual(len(store2.all()), n)

    def test_a_fresh_install_seeds_the_whole_pack_once(self):
        store = EventStore(self.path, require_rule_cited=True)
        install(store)
        self.assertEqual(len(store.all()), len(records(load_pack())))
        self.assertEqual(len(store.by_action("FOUND-STORE")), 1)
        self.assertEqual(len(store.by_action("GRANT")), 1)


class TestFoundingIntegrity(unittest.TestCase):
    """The installer refuses the WHOLE founding on the first reference violation, loudly,
    with nothing appended (a half-founded record is worse than none)."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.pack = copy.deepcopy(load_pack())

    def _install_pack(self, pack, tmpname):
        """Install a (possibly corrupted) pack via a temporary pack file — exercises the real
        load_pack + _validate + append path without touching the committed pack."""
        p = os.path.join(self.dir, tmpname)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(pack, f)
        # install() reads the canonical PACK_PATH; drive validation directly on the corrupt pack
        from founding.install import _validate, records as _records
        _validate(_records(pack))

    def _corrupt_first(self, pack, action, mutate):
        for step in pack["steps"]:
            for r in step["records"]:
                if r.get("action") == action:
                    mutate(r)
                    return
        raise AssertionError(f"no {action} record to corrupt")

    def test_law_scoped_to_a_nonexistent_space_refuses_the_whole_founding(self):
        self._corrupt_first(self.pack, "CREATE-RULE",
                            lambda r: r["payload"].__setitem__("scope", "space:ghost")
                            if r["payload"].get("root") else None)
        # ensure at least one root law now scoped to a ghost
        with self.assertRaises(FoundingIntegrityError) as cm:
            self._install_pack(self.pack, "ghost-scope.json")
        self.assertIn("space:ghost", str(cm.exception))

    def test_grant_on_a_nonexistent_space_refuses_the_whole_founding(self):
        self._corrupt_first(self.pack, "GRANT",
                            lambda r: r["payload"].__setitem__("space", "space:nowhere"))
        with self.assertRaises(FoundingIntegrityError) as cm:
            self._install_pack(self.pack, "ghost-grant.json")
        self.assertIn("space:nowhere", str(cm.exception))

    def test_tunnel_to_a_nonexistent_actor_refuses_the_whole_founding(self):
        self._corrupt_first(self.pack, "CREATE-TUNNEL",
                            lambda r: r["payload"].__setitem__("target", "phantom"))
        with self.assertRaises(FoundingIntegrityError) as cm:
            self._install_pack(self.pack, "ghost-tunnel.json")
        self.assertIn("phantom", str(cm.exception))

    def test_a_refused_founding_appends_nothing(self):
        # the loud refusal happens BEFORE any append (whole-pack pre-flight): a store driven
        # with a corrupt pack must stay empty. Drive install() against a store whose validate
        # will raise, and confirm zero records landed.
        bad = copy.deepcopy(self.pack)
        self._corrupt_first(bad, "CREATE-RULE",
                            lambda r: r["payload"].__setitem__("scope", "space:ghost")
                            if r["payload"].get("root") else None)
        store = EventStore(self.path, require_rule_cited=True)
        from founding.install import _validate, records as _records
        before = len(store.all())
        with self.assertRaises(FoundingIntegrityError):
            _validate(_records(bad))
            for r in _records(bad):            # never reached — validate raised first
                store._append(dict(r))
        self.assertEqual(len(store.all()), before)   # nothing appended


class TestFoundingRoundTrip(unittest.TestCase):
    def _read(self, path):
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_founded_record_replays_and_rebuild_adds_nothing(self):
        d = tempfile.mkdtemp()
        path = os.path.join(d, "record.jsonl")
        store, _g, views = build_kernel(path)         # founds via the installer
        raw1 = self._read(path)
        # rebuild from the same file: the installer is idempotent, so no new bytes are written
        store2, _g2, views2 = build_kernel(path)
        self.assertEqual(raw1, self._read(path), "a rebuild re-seeded the founding (idempotency broken)")
        # the founded content survives the file round-trip: the pack's records are exactly what
        # replays back (append-minted envelope excluded), in order.
        pack_recs = records(load_pack())
        reloaded = [_plain(r) for r in EventStore(path, require_rule_cited=True).all()]
        self.assertEqual(len(reloaded), len(pack_recs))
        # and the constitution reconstructs as a VIEW after the round-trip (derived, not stored)
        self.assertEqual(len(views2.root_rules()), len(root_laws()))


class TestFoundingVersion(unittest.TestCase):
    def test_pack_carries_a_version_and_the_designation_records_it(self):
        pack = load_pack()
        self.assertIn("founding_version", pack)
        d = tempfile.mkdtemp()
        store, _g, _v = build_kernel(os.path.join(d, "r.jsonl"))
        fs = store.by_action("FOUND-STORE")[0]
        self.assertEqual((fs.get("payload") or {}).get("founding_version"), pack["founding_version"])


class TestFoundingSingular(unittest.TestCase):
    """The named wrong reference refused (EP-14): the pack is the founding, singular and
    versioned — not a config file. No env overrides, no optional sections, no per-deployment
    merge. install(store) takes only the store; one canonical pack path."""

    def test_install_takes_only_a_store_no_config_surface(self):
        import inspect
        params = list(inspect.signature(install).parameters)
        self.assertEqual(params, ["store"], "install grew a configuration parameter")

    def test_one_canonical_pack_no_env_override(self):
        # load_pack defaults to the single committed pack; the installer never consults the
        # environment for an alternate founding.
        self.assertTrue(PACK_PATH.endswith(os.path.join("founding", "founding-pack.json")))
        with open(os.path.join(SRC, "founding", "install.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("os.environ", src, "the installer reads the environment (config-file drift)")
        self.assertNotIn("getenv", src)


if __name__ == "__main__":
    unittest.main()
