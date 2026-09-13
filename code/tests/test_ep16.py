"""EP-16 acceptance battery (design/31 J2 + J3-data, design/30 §1): spaces, roles, grants —
where, and how far. The power model's DATA, fully derived; enforcement sleeps until EP-17.

S1 space tree + containment + cycle refusal · S2 the default-space fold (membership DERIVED) ·
S3 role/grant/revoke records, four dimensions, the founding openness grant parses · S4
power_view + covers as PURE READS, the permission master rebound · S5 both directions +
THE ORACLE (campaign-1 answers unchanged) + round-trip · S6 attenuation (design/31 E1).
Plus the two EP-15-verdict directed items: the anchor derivation tightened to the contiguous
founding prefix, and the oracle held to the whole-class era-pin.

The two named wrong references are refused by construction: (1) a space is not a filesystem
path — reach is a walk over parent-ref records, a rename is an amendment; (2) a role stores no
permission list (RBAC) — power lives in the grants, the role is a name. Every probe lands as a
regression test (R14 / DIGEST-C1 §4). Three lenses: an ordinary actor, the owner, a restart.
"""

import os
# [EP-28Z, 2026-08-12] `import subprocess` REMOVED: this file's only spawn was its copy
# of the era-pin act, which now lives at `tests/era_pin.py`. An import naming a capability
# the file no longer uses tells a later reader it spawns processes, which is false.
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import era_pin  # noqa: E402  (the era-pin home, EP-28Z)
from kernel.boot import build_kernel  # noqa: E402
from kernel.compose import build_full_kernel  # noqa: E402
from kernel.protection import can_read  # noqa: E402
from kernel.errors import OpError  # noqa: E402

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(REPO_ROOT, "src")
MOTHER = "space:root"


class _Kernel(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views = build_kernel(self.path)

    def _spaces(self):
        for n, p in [("team", MOTHER), ("team-sub", "space:team"), ("other", MOTHER)]:
            self.gate.execute("CREATE-SPACE", "owner", {"name": n, "parent": p})


# ---- S1: the space tree + containment + cycle refusal ----------------------------------

class TestSpaceTree(_Kernel):
    def test_space_records_build_a_tree_rooted_at_the_mother(self):
        self._spaces()
        tree = self.views.spaces()
        self.assertEqual(set(tree), {MOTHER, "space:team", "space:team-sub", "space:other"})
        self.assertIsNone(tree[MOTHER]["parent"])                 # the mother is the root
        self.assertEqual(tree["space:team-sub"]["parent"], "space:team")
        self.assertEqual(self.views.mother_space(), MOTHER)

    def test_containment_reach_both_directions(self):
        self._spaces()
        r = self.views.space_reaches
        self.assertTrue(r(MOTHER, "space:team-sub"))              # the root reaches everything
        self.assertTrue(r("space:team", "space:team-sub"))        # a parent reaches its subtree
        self.assertTrue(r("space:team", "space:team"))            # a space reaches itself
        self.assertFalse(r("space:team", "space:other"))          # a sibling is NOT reached
        self.assertFalse(r("space:team-sub", "space:team"))       # a child does NOT reach its parent

    def test_a_space_naming_a_descendant_as_parent_refuses(self):
        self._spaces()
        # AMEND team to sit under its own descendant team-sub -> a loop the tree can't have
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-SPACE", "owner", {"name": "team", "parent": "space:team-sub"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(self.views.spaces()["space:team"]["parent"], MOTHER)   # unchanged

    def test_a_space_naming_itself_as_parent_refuses(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-SPACE", "owner", {"name": "z", "parent": "space:z"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertNotIn("space:z", self.views.spaces())

    def test_a_space_under_an_unfounded_parent_refuses(self):
        with self.assertRaises(OpError) as cm:
            self.gate.execute("CREATE-SPACE", "owner", {"name": "orphan", "parent": "space:ghost"})
        self.assertEqual(cm.exception.rule, "CAP-IS-LAW")

    def test_create_space_is_non_retirable_at_least_as_protected_as_owner_tier(self):
        # X1: CREATE-SPACE is now an OWNER-TIER DEFINITION-BORN op, so bare RETIRE-OP refuses via the
        # gate's conservation branch d (a protected op is amended, never bare-removed). The first
        # build got the same BOOT-INT from "not a definition-born op"; X1 makes the TIER do the work,
        # which is the point — conservation now reaches the authority surface. (See TestAuthorityOps.)
        with self.assertRaises(OpError) as cm:
            self.gate.execute("RETIRE-OP", "owner", {"name": "CREATE-SPACE"})
        self.assertEqual(cm.exception.rule, "BOOT-INT")

    def test_reach_is_a_parent_walk_not_a_string_prefix(self):
        # the refused wrong reference (1): a space is NOT a filesystem path. `space:teamsub` has
        # `space:team` as a STRING prefix, but they are siblings under the root — so a path model
        # would (wrongly) say team contains teamsub, while reach (a parent-ref walk) says it does
        # not. Reach is a derivation over records, never a prefix match.
        self.gate.execute("CREATE-SPACE", "owner", {"name": "team", "parent": MOTHER})
        self.gate.execute("CREATE-SPACE", "owner", {"name": "teamsub", "parent": MOTHER})
        self.assertTrue("space:teamsub".startswith("space:team"))     # a string prefix...
        self.assertFalse(self.views.space_reaches("space:team", "space:teamsub"))  # ...but NOT reached

    def test_re_parenting_is_an_amendment_latest_wins(self):
        # a space record is amendable (renaming/re-parenting is an amendment, not a move): re-creating
        # an id with a new parent supersedes latest-wins, and reach follows the new parent.
        self._spaces()
        self.gate.execute("CREATE-SPACE", "owner", {"name": "team-sub", "parent": "space:other"})
        self.assertEqual(self.views.spaces()["space:team-sub"]["parent"], "space:other")
        self.assertFalse(self.views.space_reaches("space:team", "space:team-sub"))   # moved out of team
        self.assertTrue(self.views.space_reaches("space:other", "space:team-sub"))   # into other


# ---- S2: the default-space fold (membership DERIVED, the migration) ---------------------

class TestDefaultSpaceFold(_Kernel):
    def test_membership_is_derived_a_record_without_a_space_belongs_to_the_mother(self):
        rec = self.gate.execute("CREATE-INFO", "owner", {"content": "note"})
        # nothing was stamped onto the frozen record — the space is DERIVED by the fold
        self.assertNotIn("space", rec["payload"])
        self.assertEqual(self.views.space_of(rec), MOTHER)

    def test_every_genesis_record_defaults_to_the_mother(self):
        # THE FOLD IS THE MIGRATION: no history rewrite, everything lives where it already did
        for e in self.store.all():
            if e["action"] in ("CREATE-SPACE", "CREATE-ROLE"):
                continue                                          # these carry their own space
            expected = (e.get("payload") or {}).get("space") or MOTHER
            self.assertEqual(self.views.space_of(e), expected, e["action"])

    def test_a_record_carrying_an_explicit_space_belongs_there(self):
        self.gate.execute("CREATE-SPACE", "owner", {"name": "team", "parent": MOTHER})
        role = [e for e in self.store.by_action("CREATE-ROLE")]  # none yet
        self.gate.execute("CREATE-ROLE", "owner", {"name": "editor", "space": "space:team"})
        r = self.store.by_action("CREATE-ROLE")[0]
        self.assertEqual(self.views.space_of(r), "space:team")

    def test_no_history_was_rewritten_by_the_fold(self):
        # the migration adds NO record and rewrites NONE — the fold alone derives membership
        before = len(self.store.all())
        _ = [self.views.space_of(e) for e in self.store.all()]
        self.assertEqual(len(self.store.all()), before)


# ---- S3: role + grant + revoke records; four dimensions; the founding grant parses ------

class TestRolesGrantsRevoke(_Kernel):
    def test_a_role_is_a_name_that_stores_no_power(self):
        # the refused wrong reference (2): a role record carries NO permission list (RBAC). The op
        # cannot even accept one, and the meaning is DERIVED from the grants that cite it.
        self.gate.execute("CREATE-ROLE", "owner", {"name": "editor"})
        rec = self.store.by_action("CREATE-ROLE")[0]
        self.assertEqual(rec["payload"]["kind"], "role")
        for banned in ("permissions", "actions", "grants", "capabilities", "can"):
            self.assertNotIn(banned, rec["payload"], banned)     # no stored power
        self.assertNotIn("permissions", self.gate.list()["CREATE-ROLE"]["params"])
        self.assertEqual(self.views.role_meaning("editor"), {})  # a fresh role means nothing

    def test_grant_carries_all_four_dimensions_wildcards_explicit(self):
        self.gate.execute("CREATE-SPACE", "owner", {"name": "team", "parent": MOTHER})
        self.gate.execute("GRANT", "owner", {"grant_id": "g1", "grantee": "alice",
                          "actions": ["CREATE-INFO"], "info": ["note"], "space": "space:team"})
        g = self.views.grants()["grant:g1"]                      # lists are frozen to tuples on append
        self.assertEqual((g["grantee"], list(g["actions"]), list(g["info"]), g["space"]),
                         ("alice", ["CREATE-INFO"], ["note"], "space:team"))

    def test_law_is_an_info_kind_rule_writing_grant_is_ordinary(self):
        # granting rule-writing is a GRANT with info kind 'law' — no rule-specific machinery
        self.gate.execute("CREATE-SPACE", "owner", {"name": "team", "parent": MOTHER})
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        self.gate.execute("GRANT", "owner", {"grant_id": "law1", "grantee": "alice",
                          "actions": ["CREATE-RULE"], "info": ["law"], "space": "space:team"})
        self.assertTrue(self.views.covers("alice", "CREATE-RULE", "law", "space:team"))
        self.assertFalse(self.views.covers("alice", "CREATE-RULE", "note", "space:team"))  # not that info

    def test_the_founding_openness_grant_parses_as_a_normal_grant(self):
        g = self.views.grants()["grant:founding-openness"]
        self.assertEqual(g["grantee"], "*")
        self.assertEqual((g["actions"], g["info"]), ("*", "*"))
        self.assertEqual(g["space"], MOTHER)

    def test_revoke_supersedes_a_grant(self):
        self.gate.execute("CREATE-SPACE", "owner", {"name": "team", "parent": MOTHER})
        self.gate.execute("GRANT", "owner", {"grant_id": "g1", "grantee": "alice",
                          "actions": ["CREATE-INFO"], "info": ["note"], "space": "space:team"})
        self.assertIn("grant:g1", self.views.grants())
        self.gate.execute("REVOKE", "owner", {"grant_id": "g1"})
        self.assertNotIn("grant:g1", self.views.grants())        # gone from the live fold


# ---- S4: power_view + covers as PURE READS; the permission master rebound ---------------

class TestPowerViewAndCovers(_Kernel):
    def test_covers_and_power_view_are_pure_reads_they_never_append(self):
        before = len(self.store.all())
        _ = self.views.covers("anyone", "CREATE-RULE", "law", MOTHER)
        _ = self.views.power_view("anyone")
        self.assertEqual(len(self.store.all()), before)          # answered, appended nothing

    def test_covers_is_open_under_the_founding_grant(self):
        # the transition state: the openness grant covers everyone until EP-17 narrows it
        self.assertTrue(self.views.covers("nobody", "CREATE-RULE", "law", MOTHER))

    def test_the_permission_master_rebinds_onto_the_grant_fold(self):
        # S4: the permission master now reflects the four-dimensional grants (bind name unchanged)
        vdef = self.views.view_definitions()["permission-master"]
        self.assertEqual(vdef["bind"], "permissions")            # the record still binds 'permissions'
        val = self.views.master("permission-master")["value"]
        self.assertIn("grant:founding-openness", val)            # ...which now resolves to grants
        self.assertEqual(val, self.views.grants())

    def test_the_old_grant_read_sight_surface_stays_can_read_unbroken(self):
        # sight is its own check still (one info-kind of the general model; the join is EP-17)
        store, gate, views, blobs, sv = build_full_kernel(
            os.path.join(self.dir, "full.jsonl"), os.path.join(self.dir, "blobs"))
        self.assertFalse(can_read(store, "alice", "doc"))
        gate.execute("GRANT-READ", "owner", {"grantee": "alice", "target": "doc"})
        self.assertTrue(can_read(store, "alice", "doc"))         # GRANT-READ still governs sight


# ---- S5: both directions + role meaning + revoke-with-no-cascade + round-trip -----------

class TestBothDirections(_Kernel):
    def _narrowed(self):
        """A world where the openness grant is narrowed away and alice holds one limited grant —
        the world in which the four-dimension distinctions and revocation are observable."""
        for n, p in [("team", MOTHER), ("team-sub", "space:team"), ("other", MOTHER)]:
            self.gate.execute("CREATE-SPACE", "owner", {"name": n, "parent": p})
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        self.gate.execute("GRANT", "owner", {"grant_id": "a1", "grantee": "alice",
                          "actions": ["CREATE-INFO"], "info": ["note"], "space": "space:team"})

    def test_containment_a_parent_reach_covers_a_child_a_sibling_does_not(self):
        self._narrowed()
        self.assertTrue(self.views.covers("alice", "CREATE-INFO", "note", "space:team-sub"))   # child
        self.assertFalse(self.views.covers("alice", "CREATE-INFO", "note", "space:other"))     # sibling
        self.assertFalse(self.views.covers("alice", "CREATE-INFO", "note", MOTHER))            # parent (up)

    def test_covers_answers_the_four_dimensions_including_info_type(self):
        self._narrowed()
        self.assertTrue(self.views.covers("alice", "CREATE-INFO", "note", "space:team"))
        self.assertFalse(self.views.covers("alice", "CREATE-RULE", "note", "space:team"))      # action
        self.assertFalse(self.views.covers("alice", "CREATE-INFO", "law", "space:team"))       # info type

    def test_revoke_kills_the_chain_at_the_next_check_with_zero_cascade(self):
        self._narrowed()
        self.assertTrue(self.views.covers("alice", "CREATE-INFO", "note", "space:team"))
        before = len(self.store.all())
        self.gate.execute("REVOKE", "owner", {"grant_id": "a1"})
        # the ONLY record added is the single REVOKE — nothing cascaded
        self.assertEqual(len(self.store.all()), before + 1)
        self.assertFalse(self.views.covers("alice", "CREATE-INFO", "note", "space:team"))      # gone next check

    def test_role_meaning_changes_when_its_citing_grants_change(self):
        self.gate.execute("CREATE-SPACE", "owner", {"name": "team", "parent": MOTHER})
        self.gate.execute("CREATE-ROLE", "owner", {"name": "editor", "space": "space:team"})
        self.gate.execute("GRANT", "owner", {"grant_id": "g1", "grantee": "alice", "actions": ["CREATE-INFO"],
                          "info": ["note"], "space": "space:team", "role": "editor"})
        self.assertEqual(set(self.views.role_meaning("editor")), {"grant:g1"})
        self.gate.execute("GRANT", "owner", {"grant_id": "g2", "grantee": "bob", "actions": ["READ"],
                          "info": ["note"], "space": "space:team", "role": "editor"})
        self.assertEqual(set(self.views.role_meaning("editor")), {"grant:g1", "grant:g2"})
        self.gate.execute("REVOKE", "owner", {"grant_id": "g1"})
        self.assertEqual(set(self.views.role_meaning("editor")), {"grant:g2"})                 # meaning shrank


class TestRoundTrip(_Kernel):
    def test_spaces_grants_roles_replay_identically_from_the_record(self):
        self.gate.execute("CREATE-SPACE", "owner", {"name": "team", "parent": MOTHER})
        self.gate.execute("CREATE-ROLE", "owner", {"name": "editor", "space": "space:team"})
        self.gate.execute("GRANT", "owner", {"grant_id": "g1", "grantee": "alice", "actions": ["CREATE-INFO"],
                          "info": ["note"], "space": "space:team", "role": "editor"})
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        before = (self.views.spaces(), self.views.grants(), self.views.roles(),
                  dict(self.views.role_meaning("editor")))
        _s2, _g2, views2 = build_kernel(self.path)               # every derived cache killed
        self.assertEqual(views2.spaces(), before[0])
        self.assertEqual(views2.grants(), before[1])
        self.assertEqual(views2.roles(), before[2])
        self.assertEqual(dict(views2.role_meaning("editor")), before[3])
        self.assertFalse(views2.covers("nobody", "CREATE-INFO", "note", MOTHER))               # narrowing survived


# ---- S6 / ADDENDUM E1: attenuation — a grant is never wider than its maker --------------

class TestAttenuation(_Kernel):
    def _narrowed(self):
        for n, p in [("team", MOTHER), ("team-sub", "space:team"), ("other", MOTHER)]:
            self.gate.execute("CREATE-SPACE", "owner", {"name": n, "parent": p})
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        self.gate.execute("GRANT", "owner", {"grant_id": "a1", "grantee": "alice",
                          "actions": ["CREATE-INFO"], "info": ["note"], "space": "space:team"})

    def test_grant_wider_than_maker_refuses_at_creation(self):
        self._narrowed()
        base = {"grantee": "bob", "actions": ["CREATE-INFO"], "info": ["note"], "space": "space:team"}
        widenings = {
            "action":       {**base, "actions": ["CREATE-RULE"]},
            "info":         {**base, "info": ["law"]},
            "space-up":     {**base, "space": MOTHER},            # up to the parent (outside team)
            "space-sibling": {**base, "space": "space:other"},   # a sibling (outside team)
            "target-star":  {**base, "grantee": "*"},            # widen the subject to everyone
            "actions-star": {**base, "actions": "*"},            # widen actions to the wildcard
        }
        for label, g in widenings.items():
            with self.assertRaises(OpError) as cm:
                self.gate.execute("GRANT", "alice", {"grant_id": f"w-{label}", **g})
            self.assertEqual(cm.exception.rule, "ROOT-NEG-3", label)   # cites the authority hop
        # not one widened grant was minted
        self.assertEqual([k for k in self.views.grants() if k.startswith("grant:w-")], [])

    def test_grant_within_makers_reach_still_mints(self):
        self._narrowed()
        # equal reach passes ('no wider' includes equality)
        self.gate.execute("GRANT", "alice", {"grant_id": "eq", "grantee": "bob",
                          "actions": ["CREATE-INFO"], "info": ["note"], "space": "space:team"})
        # narrower (a subspace) passes
        self.gate.execute("GRANT", "alice", {"grant_id": "narrow", "grantee": "bob",
                          "actions": ["CREATE-INFO"], "info": ["note"], "space": "space:team-sub"})
        self.assertIn("grant:eq", self.views.grants())
        self.assertIn("grant:narrow", self.views.grants())

    def test_root_and_founding_grants_are_unaffected(self):
        self._narrowed()
        # the root's reach is the whole tree by containment — it mints the widest grant possible
        self.gate.execute("GRANT", "owner", {"grant_id": "wide", "grantee": "*",
                          "actions": "*", "info": "*", "space": MOTHER})
        self.assertIn("grant:wide", self.views.grants())
        # and the founding openness grant (genesis, bypasses the gate) is minted with NO refusal —
        # a fresh kernel carries it and records zero op-refused at the founding
        s2, _g2, v2 = build_kernel(os.path.join(self.dir, "fresh.jsonl"))
        self.assertIn("grant:founding-openness", v2.grants())
        self.assertEqual(len(s2.by_action("op-refused")), 0)     # the founding grant never hit the bar


# ---- Directed item 1: the anchor derivation tightened to the founding prefix ------------

class TestAnchorFoundingPrefix(_Kernel):
    def test_post_founding_runtime_assertion_mints_no_anchor(self):
        # a benign post-install act closes the founding prefix; a LATER caller spoofing the
        # founding-runtime name mints NO anchor (the EP-15 loose form is retired).
        self.gate.execute("CREATE-INFO", "owner", {"content": "post-install"})   # closes the prefix
        self.gate.execute("CREATE-ACTOR", "PC_RUNTIME", {"actor_id": "evil"})     # spoof the runtime name
        self.assertNotIn("evil", self.views._anchor_ids())
        self.assertEqual(self.views.resolve_asserted_by("evil"), "unverified:evil")

    def test_genesis_anchors_still_resolve_anchored(self):
        # both directions: the genuine genesis anchors are unaffected by the tightening
        self.gate.execute("CREATE-INFO", "owner", {"content": "activity"})
        self.gate.execute("CREATE-ACTOR", "PC_RUNTIME", {"actor_id": "spoof"})    # even after a spoof
        for anchor in ("owner", "SYSTEM", "PC_RUNTIME"):
            self.assertIn(anchor, self.views._anchor_ids(), anchor)
            self.assertEqual(self.views.accounts()[anchor]["resolution"], "anchored", anchor)


# ---- Directed item 2: THE ORACLE — campaign-1 answers unchanged, whole-class era-pin ----

PRE_EP16_SHA = "ede19f782ea5af498b441e02b43561690a848a4a"   # HEAD before EP-16 (EP-15 reviewed, suite 298)


def _reconstruct_pre_views():
    """Load the pre-EP-16 views.py from the pinned commit into a fresh module in the live kernel
    package (its `from .store import frozen_default` resolves against the era-INVARIANT live
    store.py — EP-16 changes no store code). WHOLE-CLASS ERA-PIN (directed item 2): the frozen
    (pre) Views makes only STORE reads; it calls NO load_pack / founding_version / root_laws (a
    Views never does), and EP-16 edits NO founding-pack record — so every read the frozen side
    makes resolves to the era state by construction, with no live-tree-in-disguise to pin away.

    [DOCUMENTED FLIP — EP-28Z, 2026-08-12. CAUSE: one of EIGHTEEN copies of the era-pin act
    across TEN test files. ASSERTED: a local `git show` spawn, `.decode()`d. SUPERSEDED:
    `era_pin.text_at`, from the one home. REMAINS TRUE: the decode is UTF-8 either way, and
    the equivalence is DRIVEN rather than assumed — `test_ep28z.py` reads every pin this
    suite holds for a carriage return, the one input on which the two decodings differ.
    GIVEN UP: nothing; the module reconstruction below is the CALLER's business and is
    untouched.]"""
    src = era_pin.text_at(PRE_EP16_SHA, "src/kernel/views.py")
    mod = types.ModuleType("_pre_ep16_views")
    mod.__package__ = "kernel"
    mod.__file__ = os.path.join(SRC, "kernel", "views.py")
    exec(compile(src, "<pre_ep16_views>", "exec"), mod.__dict__)
    return mod


def _plainify(o):
    """A fully-plain, order-normalised copy for equality: frozen MappingProxyType -> dict (tuple
    keys stringified, e.g. dictionary()'s (kind, term) keys), tuple/list -> list, set -> sorted
    list. Both the pre and current snapshots pass through this, so a divergence is real, never a
    frozen-shape or ordering artefact."""
    from collections.abc import Mapping
    if isinstance(o, Mapping):
        return {str(k): _plainify(v) for k, v in o.items()}
    if isinstance(o, (set, frozenset)):
        return sorted(_plainify(x) for x in o)
    if isinstance(o, (list, tuple)):
        return [_plainify(x) for x in o]
    return o


# the campaign-1 view answers compared before/after EP-16 (the permission-master is EXCLUDED —
# its rebind onto the grant fold is the one DECLARED change, S4, asserted separately below).
def _snapshot(views):
    out = {}
    out["active_rules"] = views.active_rules()
    out["category_packs"] = views.category_packs()
    out["op_definitions"] = views.op_definitions()
    out["view_definitions"] = views.view_definitions()
    out["root_rules"] = views.root_rules()
    out["accounts"] = views.accounts()
    out["anchor_ids"] = sorted(views._anchor_ids())
    out["toothless_musts"] = sorted(views.toothless_musts())
    out["dictionary"] = views.dictionary()
    out["metabolism"] = views.metabolism()
    for key in ("quantum_ms", "k"):
        out[f"policy:{key}"] = views.policy_value(key)
    for m in ("rule-master", "actor-master", "resource-master", "relationship-master",
              "op-registry", "view-registry"):
        out[f"master:{m}"] = views.master(m)["value"]            # permission-master EXCLUDED (declared)
    return _plainify(out)


class TestDefaultSpaceOracle(unittest.TestCase):
    """THE ORACLE (S5): the default-space fold (and the whole EP-16 change set) leaves EVERY
    campaign-1 view answer UNCHANGED. Proven differentially: the SAME campaign-1 record sequence
    read by the pre-EP-16 Views (reconstructed from the pinned commit) and by the current Views
    must give identical answers. The lone declared change (the permission-master rebind, S4) is
    excluded from the snapshot and asserted on its own."""

    @classmethod
    def setUpClass(cls):
        d = tempfile.mkdtemp()
        store, gate, views = build_kernel(os.path.join(d, "oracle.jsonl"))
        # a representative campaign-1 sequence touching many folds (no space/grant ops — those are
        # the new world; the oracle proves they don't disturb the old answers)
        gate.execute("CREATE-RULE", "SYSTEM",
                     {"rule_id": "law:q", "policy_key": "quantum_ms", "value": 4, "exclusive": True})
        gate.execute("CREATE-ACTOR", "owner", {"actor_id": "sched", "role": "subsystem"})
        gate.execute("AMEND-BUDGET", "owner", {"holder": "web", "ceiling": 100})
        gate.execute("MEM-GRANT", "web", {"region": "r1", "size": 10})
        gate.execute("CREATE-VIEW", "owner", {"name": "refusals", "when": {"refused": True},
                     "then": {"move_to": "owner-queue"}})
        gate.execute("DICT-ENTRY", "owner", {"term": "mount", "entity_kind": "action"})
        gate.execute("COMPARE", "owner", {"a": "x", "b": "y", "frame": "f", "verdict": "same"})
        gate.execute("TICK", "SYSTEM", {"now": 1000})
        cls.store = store
        cls.current = _snapshot(views)
        PreViews = _reconstruct_pre_views().Views
        cls.pre = _snapshot(PreViews(store))                    # pre-EP-16 Views over the SAME store

    def test_every_campaign1_answer_is_unchanged(self):
        # method by method, so a divergence names itself
        self.assertEqual(set(self.pre), set(self.current))
        for key in self.pre:
            self.assertEqual(self.pre[key], self.current[key], f"campaign-1 answer changed: {key}")

    def test_the_permission_master_rebind_is_the_only_declared_change(self):
        # the excluded answer DID change — and it changed to the grant fold, exactly as S4 directs
        _s, _g, views = build_kernel(os.path.join(tempfile.mkdtemp(), "r.jsonl"))
        PreViews = _reconstruct_pre_views().Views
        pre_pm = _plainify(PreViews(views.store).master("permission-master")["value"])
        cur_pm = _plainify(views.master("permission-master")["value"])
        self.assertNotEqual(pre_pm, cur_pm)                     # the rebind is real
        self.assertEqual(cur_pm, _plainify(views.grants()))    # ...to the grant fold

    def test_every_campaign1_record_lives_in_the_mother_space(self):
        # the fold IS the migration: every pre-account record defaults to where it already lived
        _s, _g, views = build_kernel(os.path.join(tempfile.mkdtemp(), "r.jsonl"))
        for e in views.store.all():
            self.assertEqual(views.space_of(e), MOTHER, e["action"])


# ================= VERDICT ADDENDUM — X1..X4 (the four completions before the crux) =================

# ---- X1: the four authority ops are OWNER-TIER DEFINITION-BORN PACK RECORDS -------------

class TestAuthorityOpsAreDefinitionBorn(_Kernel):
    """X1: CREATE-SPACE / CREATE-ROLE / GRANT / REVOKE moved from boot handlers to owner-tier
    definition-born PACK records. The gain the mentor named: a recorded tier (conservation reaches
    them), and the authority write surface visible IN the founding document — no law-in-code where
    power lives (the surface EP-14 closed, re-closed)."""

    OPS = ("CREATE-SPACE", "CREATE-ROLE", "GRANT", "REVOKE")

    def test_the_four_ops_are_definition_born_owner_tier_and_registered(self):
        od = self.views.op_definitions()
        for op in self.OPS:
            self.assertIn(op, od, op)                       # a RECORDED definition, not a code handler
            self.assertEqual(od[op]["tier"], "owner", op)   # owner tier (EP-15 A1 precedent)
            self.assertTrue(self.gate.has(op), op)          # still registered + callable

    def test_the_founding_document_shows_the_authority_surface(self):
        # a cold reader of the pack SEES the four ops exist (install.op_definitions reads the pack)
        from founding.install import op_definitions as pack_ops
        defs = pack_ops()
        for op in self.OPS:
            self.assertIn(op, defs, op)

    def test_conservation_reaches_them_bare_retire_refuses_for_everyone(self):
        for op in self.OPS:
            with self.assertRaises(OpError) as cm:
                self.gate.execute("RETIRE-OP", "owner", {"name": op})
            self.assertEqual(cm.exception.rule, "BOOT-INT", op)     # the owner-tier conservation bar
            self.assertIn(op, self.views.op_definitions(), op)      # survived the attempt

    def test_founding_version_bumped_to_1_4_0(self):
        # DOCUMENTED FLIP (EP-17 -> EP-18 -> EP-19): EP-17's Y-pass bumped the founding to 1.4.0; EP-18
        # to 1.5.0 (succession + the anchor); EP-19 bumped it to 1.6.0 (the secrets vault: CONST-SECRETS
        # live, the two secret ops, VERIFY-SECRET into the dual-audit pack); the EP-19 V5/V6 amendment
        # bumps once more to 1.6.1 (VERIFY-ACCOUNT joins the dual-audit pack — a growth of the
        # constitutionally-pinned audit floor, so the founding content changed and the version must
        # move to keep it uniquely identified, J9). Constitutional evolution is a visible pack-version diff.
        # EP-23 bumps the MINOR to 1.7.0 (the crossing: two rules, two recorded policy defaults, and the
        # ANSWER-RETURNED / PRESENT-CREDENTIAL ops) — a NEW EP surface, which is a MINOR under the
        # founding-version convention adopted at EP-19.
        # [EP-28T, 2026-08-08 — `AppendNothing` PER ROW, and the flip chain above stops here.]
        # ASSERTED: a FROZEN LITERAL "1.17.0", last set 2026-08-05 (EP-28N AMENDMENT 1).
        # SUPERSEDED: EP-28S landed the identity law on 2026-08-08 and the founding moved
        #   1.17.0 -> 1.18.0. That is the FIFTH rewrite of this literal, and the rewriting is
        #   the defect rather than the cure — a version literal in a test is a STORED COPY OF A
        #   COMPUTABLE VALUE, so every lawful bump reds a row that was never about the bump.
        #   Writing 1.18.0 here would guarantee a sixth.
        # REMAINS TRUE, separated out and STILL ASSERTED: (1) the founding never goes BACKWARDS
        #   past the version this row's own history recorded — a FLOOR cannot go stale on a
        #   lawful bump and still reds on a regression; (2) THE READER AND THE RECORD AGREE —
        #   `founding_version()` reads the pack on disk, while the designation was stamped into
        #   FOUND-STORE by the installer at genesis, so their agreement is two different takings
        #   of one fact and it catches an installer stamping a stale version.
        #   `load_pack()["founding_version"]` is deliberately NOT the second reader: it is
        #   literally what `founding_version()` returns, so that pairing would be one reading
        #   wearing two labels.
        # GIVEN UP, plainly: this row can no longer notice a bump. That was never its job —
        #   EP-28N2's `test_the_version_MOVED_which_is_this_passs_required_outcome` holds that
        #   against a PINNED before-side, and J9's guard holds version-with-hash uniqueness.
        from founding.install import founding_version
        v = founding_version()
        self.assertGreaterEqual(tuple(int(n) for n in v.split(".")), (1, 17, 0))
        fs = self.store.by_action("FOUND-STORE")[0]
        self.assertEqual((fs.get("payload") or {}).get("founding_version"), v)

    def test_the_four_ops_replay_from_the_record_after_a_restart(self):
        # the registry is derived state: rebuild from the file alone, the four ops come back registered
        _s2, gate2, views2 = build_kernel(self.path)
        for op in self.OPS:
            self.assertTrue(gate2.has(op), op)
            self.assertIn(op, views2.op_definitions(), op)

    def test_a_wrong_actor_cannot_amend_a_protected_authority_op(self):
        # conservation's other half: only the owner may amend an owner-tier op in place (branch e)
        newdef = self.views.op_definitions()["REVOKE"]["definition"]
        with self.assertRaises(OpError) as cm:
            self.gate.execute("AMEND-OP", "alice", {"name": "REVOKE", "definition": newdef})
        self.assertEqual(cm.exception.rule, "BOOT-INT")


# ---- X2: the general `space` passthrough (any op may carry an explicit space) -----------

class TestGeneralSpacePassthrough(_Kernel):
    """X2 (the S2 remainder): ONE interpreter passthrough lets ANY definition-born op carry an
    explicit `space` into its record — no per-op cases. Records without one keep the default fold."""

    def test_any_op_may_carry_an_explicit_space_into_its_record(self):
        self.gate.execute("CREATE-SPACE", "owner", {"name": "team", "parent": MOTHER})
        # DICT-ENTRY never declared a `space` param; the passthrough still carries one
        rec = self.gate.execute("DICT-ENTRY", "owner",
                                {"term": "t", "entity_kind": "action", "space": "space:team"})
        self.assertEqual(rec["payload"]["space"], "space:team")
        self.assertEqual(self.views.space_of(rec), "space:team")

    def test_a_record_without_a_space_keeps_the_default_space_fold(self):
        rec = self.gate.execute("DICT-ENTRY", "owner", {"term": "t2", "entity_kind": "action"})
        self.assertNotIn("space", rec["payload"])
        self.assertEqual(self.views.space_of(rec), MOTHER)


# ---- X3: role-holding is an ORDINARY GRANT; covers gains the one-hop role route ---------

class TestRoleRoute(_Kernel):
    """X3: holding a role is an ordinary grant `(+) account x hold x role:R x space`; `covers` gains
    a one-hop route — a covering grant whose SUBJECT is a role the account holds. No membership record
    kind, no role-permission list (RBAC stays refused); the role record still stores no power."""

    def _world(self):
        for n, p in [("team", MOTHER), ("team-sub", "space:team"), ("other", MOTHER)]:
            self.gate.execute("CREATE-SPACE", "owner", {"name": n, "parent": p})
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        self.gate.execute("CREATE-ROLE", "owner", {"name": "editor", "space": "space:team"})

    def _hold(self, gid, account):
        self.gate.execute("GRANT", "owner", {"grant_id": gid, "grantee": account,
                          "actions": ["hold"], "info": ["role:editor"], "space": "space:team"})

    def _power(self, gid):
        self.gate.execute("GRANT", "owner", {"grant_id": gid, "grantee": "role:editor",
                          "actions": ["EDIT"], "info": ["doc"], "space": "space:team"})

    def test_a_role_confers_to_its_holders_one_hop(self):
        self._world()
        self._hold("hold-a", "alice")
        self._power("pow")
        self.assertTrue(self.views.covers("alice", "EDIT", "doc", "space:team"))       # conferred
        self.assertTrue(self.views.covers("alice", "EDIT", "doc", "space:team-sub"))    # containment on the route
        self.assertFalse(self.views.covers("bob", "EDIT", "doc", "space:team"))         # a non-holder gets nothing

    def test_either_link_revoked_kills_instantly_with_zero_cascade(self):
        self._world()
        self._hold("hold-a", "alice")
        self._power("pow")
        self.assertTrue(self.views.covers("alice", "EDIT", "doc", "space:team"))
        before = len(self.store.all())
        self.gate.execute("REVOKE", "owner", {"grant_id": "hold-a"})                    # revoke the HOLD link
        self.assertEqual(len(self.store.all()), before + 1)                            # only the REVOKE — no cascade
        self.assertFalse(self.views.covers("alice", "EDIT", "doc", "space:team"))       # gone at the next check
        self._hold("hold-a2", "alice")                                                  # re-hold
        self.assertTrue(self.views.covers("alice", "EDIT", "doc", "space:team"))
        self.gate.execute("REVOKE", "owner", {"grant_id": "pow"})                       # revoke the POWER link
        self.assertFalse(self.views.covers("alice", "EDIT", "doc", "space:team"))       # also instant

    def test_a_role_citing_no_grants_confers_nothing(self):
        self._world()
        self._hold("hold-a", "alice")                                                  # holds editor, but editor has no power
        self.assertFalse(self.views.covers("alice", "EDIT", "doc", "space:team"))

    def test_the_role_record_still_stores_no_power(self):
        self._world()
        rec = [e for e in self.store.by_action("CREATE-ROLE") if e["payload"]["name"] == "editor"][0]
        for banned in ("permissions", "actions", "grants", "capabilities", "can"):
            self.assertNotIn(banned, rec["payload"], banned)                           # the role is a NAME

    def test_the_route_adds_coverage_never_alters_a_direct_grant_answer(self):
        # the mentor's binding constraint: route 2 is ADDITIVE. A direct grant answers exactly as the
        # first build even with the role machinery present, and no role held means route 2 is inert.
        self._world()
        self.gate.execute("GRANT", "owner", {"grant_id": "d", "grantee": "alice",
                          "actions": ["CREATE-INFO"], "info": ["note"], "space": "space:team"})
        self.assertTrue(self.views.covers("alice", "CREATE-INFO", "note", "space:team"))
        self.assertFalse(self.views.covers("alice", "CREATE-INFO", "note", "space:other"))  # unchanged
        self.assertFalse(self.views.covers("alice", "EDIT", "doc", "space:team"))            # no role held -> route 2 inert

    def test_hold_is_vocabulary_declared_in_the_founding_pack(self):
        # hold enters as a pack, never a hardcoded enum
        self.assertIn("hold", self.views.category_packs()["authority-actions"]["levels"])


# ---- X4: attenuation strictens to per-single-grant WHOLE containment --------------------

class TestWholeContainmentAttenuation(_Kernel):
    """X4 (corrects E1's "dimension by dimension" phrase; the owner's law "never wider than the maker"
    stands): a non-root grant must be contained WHOLE — actions AND info AND space together — inside
    AT LEAST ONE covering grant of its maker. Per-dimension unions across grants are refused."""

    def _maker_with_two_disjoint_grants(self):
        for n in ("A", "B"):
            self.gate.execute("CREATE-SPACE", "owner", {"name": n, "parent": MOTHER})
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        self.gate.execute("GRANT", "owner", {"grant_id": "rs", "grantee": "carol",
                          "actions": ["read"], "info": ["secrets"], "space": "space:A"})
        self.gate.execute("GRANT", "owner", {"grant_id": "wp", "grantee": "carol",
                          "actions": ["write"], "info": ["public"], "space": "space:B"})

    def test_recombination_across_two_grants_refuses(self):
        # THE NAMED FAILING TEST: (write x secrets x A) is covered by NEITHER single grant — new power
        # by recombining the action of one with the info+space of the other. The per-dimension-union
        # arithmetic would have (wrongly) admitted it; whole containment refuses.
        self._maker_with_two_disjoint_grants()
        with self.assertRaises(OpError) as cm:
            self.gate.execute("GRANT", "carol", {"grant_id": "recomb", "grantee": "dave",
                              "actions": ["write"], "info": ["secrets"], "space": "space:A"})
        self.assertEqual(cm.exception.rule, "ROOT-NEG-3")
        self.assertNotIn("grant:recomb", self.views.grants())

    def test_a_grant_contained_whole_in_one_grant_still_mints(self):
        # the too-wedged direction (tested beside the failing one): a grant WHOLLY inside one covering
        # grant mints fine — the strictening refuses only recombination, never legitimate delegation.
        self._maker_with_two_disjoint_grants()
        self.gate.execute("GRANT", "carol", {"grant_id": "ok", "grantee": "dave",
                          "actions": ["read"], "info": ["secrets"], "space": "space:A"})
        self.assertIn("grant:ok", self.views.grants())

    def test_a_lawful_span_is_expressed_as_two_narrower_grants(self):
        # no expressiveness lost, only the widening: carol delegates each of her grants separately
        self._maker_with_two_disjoint_grants()
        self.gate.execute("GRANT", "carol", {"grant_id": "s1", "grantee": "dave",
                          "actions": ["read"], "info": ["secrets"], "space": "space:A"})
        self.gate.execute("GRANT", "carol", {"grant_id": "s2", "grantee": "dave",
                          "actions": ["write"], "info": ["public"], "space": "space:B"})
        self.assertIn("grant:s1", self.views.grants())
        self.assertIn("grant:s2", self.views.grants())


if __name__ == "__main__":
    unittest.main()
