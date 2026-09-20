# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary. NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""P8B-HARDENING delta 2 (archi :3731 C) — the founding-door actor-class DOMAIN check.

install._validate refuses the WHOLE founding for a genesis CREATE-ACTOR whose actor_class is outside
the pack's OWN declared class domain — the cell-presence / wire-at-birth idiom (mirrors cell_law_live),
with ONE load-bearing difference: the domain is tracked POSITIONALLY, so it binds only actors founded
AFTER it goes live. That keeps the pack-head SYSTEM (actor_class 'system', founded before the
{human,ai,program} domain) INERT and the production founding intact, and refuses a planted post-domain
actor whose class is outside the domain (the reference to refuse).
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from founding import install                                          # noqa: E402
from founding.install import FoundingIntegrityError                   # noqa: E402
from kernel.boot import build_kernel                                  # noqa: E402

PACK = "pack:actor-classes"


def _domain_pack(levels):
    return {"action": "CREATE-INFO", "object": PACK,
            "payload": {"kind": "category_pack", "name": "actor-classes", "levels": levels}}


def _actor(aid, cls):
    return {"action": "CREATE-ACTOR", "object": f"actor:{aid}",
            "payload": {"actor_id": aid, "actor_class": cls}}


class TestFoundingDomainCheck(unittest.TestCase):

    def test_the_production_founding_still_founds(self):
        # THE HARD STOP: the recorder-system SYSTEM (actor_class 'system') is founded at the pack head,
        # before the {human,ai,program} domain; the positional check must be inert for it. Drive the
        # real founding end to end.
        d = tempfile.mkdtemp()
        store, gate, views = build_kernel(os.path.join(d, "r.jsonl"))   # runs install() -> _validate()
        self.assertGreater(len(store.all()), 40)                       # it founded (no refusal)
        self.assertEqual(set(views.class_domain()), {"human", "ai", "program"})
        install._validate(install.records(install.load_pack()))        # _validate directly: no raise

    def test_a_bad_post_domain_genesis_actor_reds(self):
        # THE REFERENCE TO REFUSE: a CREATE-ACTOR AFTER the domain goes live with a class outside it
        # refuses the whole founding.
        recs = [_domain_pack(["human", "ai", "program"]), _actor("bad", "wizard")]
        with self.assertRaises(FoundingIntegrityError):
            install._validate(recs)

    def test_a_good_post_domain_actor_founds(self):
        recs = [_domain_pack(["human", "ai", "program"]), _actor("ok", "human")]
        install._validate(recs)                                        # class in domain -> no raise

    def test_an_actor_before_the_domain_is_inert(self):
        # wire-at-birth: an actor founded BEFORE any domain pack cannot be judged against it (SYSTEM's case)
        recs = [_actor("system", "system"), _domain_pack(["human", "ai", "program"])]
        install._validate(recs)                                        # inert at the pack head -> no raise

    def test_absent_domain_is_inert(self):
        # inert-on-absence: a world with no actor-classes pack founds exactly as before (every pre-P8 world)
        recs = [_actor("weird", "anything-goes")]
        install._validate(recs)                                        # no domain declared -> no raise

    def test_a_recut_domain_binds_actors_that_follow_it(self):
        # the domain re-cuts positionally: an actor after a re-cut is judged against the NEW levels
        recs = [_domain_pack(["human", "ai", "program"]), _domain_pack(["human", "ai"]), _actor("p", "program")]
        with self.assertRaises(FoundingIntegrityError):                # 'program' dropped by the re-cut
            install._validate(recs)


if __name__ == "__main__":
    unittest.main(verbosity=2)
