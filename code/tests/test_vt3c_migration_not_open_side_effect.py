# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test
# Vocabulary is OS-architecture (idempotent founding, FOUND-STORE version, complete-vs-partial world,
# migration as an explicit act). NON-GOAL: no offensive capability — these tests prove that OPENING an
# older complete world under a newer founding pack leaves it byte-identical (a migration is an explicit
# act, never an open side-effect), by function. Full declaration: SCOPE-STATEMENT.md.
#
# VT-3c (design/53 §7 row VT-3c; archi :3846) — install.py's idempotency reads the WORLD'S OWN FOUND-STORE
# founding_version FIRST:
#   - version DIFFERENT from the pack's  -> a COMPLETE OLDER WORLD -> open returns byte-identical (A1/A4);
#   - version SAME as the pack's + last record absent -> the :2901 partial prefix -> re-lands as today (A2);
#   - no FOUND-STORE -> a fresh world -> founds (A3); complete same-version returns (A3).
#
# RUNNER OF RECORD — PER-MODULE (:3158):
#   PYTHONPATH=src:tests python3 -m unittest tests.test_vt3c_migration_not_open_side_effect -v
# never discover; no pytest.

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kernel.boot import build_kernel                                  # noqa: E402
from kernel.store import EventStore                                   # noqa: E402
from founding.install import install, load_pack, records, founding_version  # noqa: E402


PACK = load_pack()
RECS = records(PACK)
PACK_VERSION = founding_version(PACK)          # "1.53.0" at this writing — READ, never a literal
LAST = RECS[-1]                                # the pack's terminal record (VT-3 made it CREATE-VIEW view:4.2.3)
FOUND_STORE_OBJECT = RECS[0].get("object")     # "event-store" — the founding designation, first in the pack


def _new_store():
    return EventStore(os.path.join(tempfile.mkdtemp(), "rec.jsonl"), require_rule_cited=True)


def _stamp_found_store(rec, version):
    """A copy of a FOUND-STORE pack record with `founding_version` stamped into its payload — exactly
    what install.py's F4 (:273-276) writes when it lands the founding designation. A world's OWN version
    lives here."""
    out = dict(rec)
    out["payload"] = dict(rec.get("payload") or {}, founding_version=version)
    return out


def _has_last_record(store):
    """Is the pack's terminal record present? (the :2901 completion marker)"""
    return any(e.get("object") == LAST.get("object") for e in store.by_action(LAST.get("action")))


class TestA1OlderCompleteWorldOpenIsByteIdentical(unittest.TestCase):
    """A1 — an older complete world (its own FOUND-STORE version DIFFERS from the pack's) opened under a
    newer pack stays BYTE-IDENTICAL: open reads it, appends nothing, returns. THE READ-ONLY OPEN THAT CAN
    FAIL — a planted re-found reds, because the older world's last record is absent (VT-3 moved it), so
    WITHOUT the version read the last-record idempotency would re-found the whole pack on open."""

    def test_a1_older_world_open_appends_nothing(self):
        store = _new_store()
        # a COMPLETE older world: the whole pack MINUS its terminal record (the older pack lacked VT-3's
        # step-11 tail), with its FOUND-STORE stamped an OLDER version. Its own version != the pack's.
        older = list(RECS[:-1])
        older[0] = _stamp_found_store(older[0], "1.52.0")
        for r in older:
            store._append(dict(r))
        self.assertFalse(_has_last_record(store),
                         "fixture invalid: the older world already holds the pack's terminal record")
        self.assertNotEqual(PACK_VERSION, "1.52.0", "fixture invalid: the older stamp equals the pack version")

        before = store.file_path.read_bytes()          # capture the world on disk
        n_before = len(store.all())
        install(store)                                  # OPEN under the current (newer) pack
        after = store.file_path.read_bytes()

        # the planted re-found: WITHOUT the version read, the absent terminal record makes install re-found
        # the whole pack here — the bytes would grow. WITH it, open returns byte-identical.
        self.assertEqual(before, after,
                         "an older complete world was RE-FOUNDED on open — migration became an open side-effect")
        self.assertEqual(len(store.all()), n_before, "records were appended to an older world on open")

    def test_a1_two_found_stores_judged_by_first(self):
        """Precision (1) / govos-w4: a world already holding TWO FOUND-STOREs (its FIRST stamped an older
        version, a SECOND stamped the current version by an earlier accidental re-found) is judged by its
        FIRST — so it returns byte-identical under the current pack. A buggy read of the LAST FOUND-STORE
        (== the pack version) would fall through and re-found; the FIRST read returns."""
        store = _new_store()
        older = list(RECS[:-1])
        older[0] = _stamp_found_store(older[0], "1.38.0")
        for r in older:
            store._append(dict(r))
        # a SECOND FOUND-STORE stamped the CURRENT version — the record govos-w4's accidental re-found left.
        store._append(_stamp_found_store(RECS[0], PACK_VERSION))
        self.assertEqual(len(store.by_action("FOUND-STORE")), 2, "fixture invalid: expected two FOUND-STOREs")

        before = store.file_path.read_bytes()
        install(store)
        after = store.file_path.read_bytes()
        self.assertEqual(before, after,
                         "a world with two FOUND-STOREs was judged by its LAST, not its FIRST, and re-founded")


class TestA2PartialPrefixRelands(unittest.TestCase):
    """A2 — the :2901 partial-prefix re-land is KEPT. A world whose FOUND-STORE version EQUALS the pack's
    but whose terminal record is ABSENT is a partial prefix, and re-lands cleanly, as today."""

    def test_a2_partial_prefix_same_version_relands(self):
        store = _new_store()
        # a partial prefix: FOUND-STORE (stamped the CURRENT version, as a real interrupted install would)
        # + CREATE-ACTOR SYSTEM, before the pack's terminal record.
        prefix = list(RECS[:2])
        self.assertEqual(prefix[1].get("action"), "CREATE-ACTOR")
        prefix[0] = _stamp_found_store(prefix[0], PACK_VERSION)
        for r in prefix:
            store._append(dict(r))
        self.assertFalse(_has_last_record(store), "fixture invalid: the prefix already holds the terminal record")

        install(store)                                  # must RE-LAND (same version, last record absent)
        self.assertTrue(_has_last_record(store),
                        "the :2901 partial prefix did not re-land — the version read swallowed a same-version world")


class TestA3CompleteSameVersionReturnsFreshFounds(unittest.TestCase):
    """A3 — a complete same-version world founds nothing twice (returns); a world with NO FOUND-STORE is
    fresh and founds fully."""

    def _last_record_count(self, store):
        return len([e for e in store.by_action(LAST.get("action")) if e.get("object") == LAST.get("object")])

    def test_a3_complete_same_version_returns(self):
        store, _g, _v = build_kernel(os.path.join(tempfile.mkdtemp(), "rec.jsonl"))
        self.assertEqual(self._last_record_count(store), 1, "a fresh build did not land the terminal record once")
        self.assertEqual(founding_version(),  # sanity: the built world carries the current pack version
                         (store.by_action("FOUND-STORE")[0].get("payload") or {}).get("founding_version"))
        before = store.file_path.read_bytes()
        install(store)                                  # second install on a complete current world
        after = store.file_path.read_bytes()
        self.assertEqual(before, after, "a complete same-version world re-landed on a second install")
        self.assertEqual(self._last_record_count(store), 1, "the terminal record was landed twice")

    def test_a3_fresh_world_founds(self):
        store = _new_store()
        self.assertEqual(store.by_action("FOUND-STORE"), [], "fixture invalid: a fresh world already has a FOUND-STORE")
        install(store)                                  # a fresh world founds fully
        self.assertEqual(len(store.by_action("FOUND-STORE")), 1, "a fresh world was not founded")
        self.assertTrue(_has_last_record(store), "a fresh founding did not land the pack's terminal record")


class TestA4MigrationIsNotAnOpenSideEffect(unittest.TestCase):
    """A4 — migration is an EXPLICIT act. Opening an older world NEVER appends a migration: no second
    FOUND-STORE and no records appear. A planted open-time migration (a re-found on version mismatch) reds."""

    def test_a4_open_of_older_world_appends_no_migration(self):
        store = _new_store()
        older = list(RECS[:-1])
        older[0] = _stamp_found_store(older[0], "1.40.0")
        for r in older:
            store._append(dict(r))
        found_stores_before = len(store.by_action("FOUND-STORE"))
        n_before = len(store.all())

        install(store)                                  # OPEN — must not migrate

        self.assertEqual(len(store.by_action("FOUND-STORE")), found_stores_before,
                         "opening an older world appended a second FOUND-STORE — a migration ran as an open side-effect")
        self.assertEqual(len(store.all()), n_before,
                         "opening an older world appended records — migration is never an open side-effect")


if __name__ == "__main__":
    unittest.main()
