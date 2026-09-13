"""The founding cannot move without the log moving (EP-27 ADDENDUM 2, W5c).

WHAT THIS GUARDS, and it is a standing guard rather than one EP's row. The founding pack is
the constitution's source document. Its version and its content are the two facts every later
reader needs, and the only thing that has ever kept them honest is a person remembering to
write an entry. On 2026-07-27 that discipline did not fire: a builder bumped the founding from
1.10.0 to 1.11.0, stated the change class inside the pack's own description field and nowhere
in the build log, and died before writing an entry. Nothing in the estate could see it. It
surfaced nine hours later only because the NEXT execution plan happened to tell its builder to
reconcile a test count, and a plan that did not say so would have built straight over it.

SO THE GUARD: the founding on disk must be named — by version AND by the hash of its own
bytes, TOGETHER IN ONE ENTRY — somewhere in `planning/build/BUILD-PROGRESS_v3.md`. A session
that bumps the founding and logs it in the same session is unaffected. A session that bumps it
and stops is RED until it writes its entry, which is exactly the behaviour being asked for.

WHY THE HASH AND NOT THE VERSION ALONE. The version is a label a session controls; the hash is
a measurement of the file it cannot. J9 already forbids the same version naming two distinct
foundings, and that rule had no instrument. This is the instrument: change one byte of the pack
without changing the version and the hash moves, the log no longer names it, and the suite goes
red. Silent content drift stops being something a reader has to notice.

WHY ONE ENTRY AND NOT ANYWHERE IN THE FILE. A version mentioned in one entry and a hash
mentioned in another prove nothing about each other — the log would satisfy a weaker check
while recording no statement that THIS pack is THIS version. The binding is the entry.

This file reads two files and composes no kernel. It appends nothing, it touches no founding,
and it is deliberately a test rather than engine surface: the check is about the estate's
paperwork, not about what the machine does.
"""

import hashlib
import json
import os
import re
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
PACK_PATH = os.path.join(_HERE, "..", "src", "founding", "founding-pack.json")
LOG_PATH = os.path.join(_HERE, "..", "planning", "build", "BUILD-PROGRESS_v3.md")


def pack_facts(path=PACK_PATH):
    """The two facts about the founding as it sits on disk: what it calls itself, and what it
    IS. The hash is over the raw bytes rather than over a re-serialization, because the file is
    the document — a re-serialization would hash a reading of it and let formatting drift
    through unseen."""
    with open(path, "rb") as fh:
        raw = fh.read()
    return {"version": json.loads(raw)["founding_version"],
            "sha256": hashlib.sha256(raw).hexdigest()}


def entries(log_text):
    """The log's entries, split at the log's own headings. `## ` opens an entry; `### ` is a
    section inside one and does not."""
    out, cur = [], None
    for line in log_text.splitlines():
        if line.startswith("## ") and not line.startswith("###"):
            if cur is not None:
                out.append("\n".join(cur))
            cur = [line]
        elif cur is not None:
            cur.append(line)
    if cur is not None:
        out.append("\n".join(cur))
    return out


def entries_naming(log_text, version, sha256):
    """The headings of every entry that names BOTH facts. Empty means the founding on disk is
    unattested. The version is matched on its own boundaries so `1.1.0` cannot answer for
    `1.11.0`; the hash is matched plainly because a 64-hex string is its own boundary."""
    pattern = re.compile(r"(?<![\w.])" + re.escape(version) + r"(?![\w.])")
    return [e.splitlines()[0] for e in entries(log_text)
            if pattern.search(e) and sha256 in e]


def audit(pack_path=PACK_PATH, log_path=LOG_PATH):
    facts = pack_facts(pack_path)
    with open(log_path, encoding="utf-8") as fh:
        log_text = fh.read()
    naming = entries_naming(log_text, facts["version"], facts["sha256"])
    return {**facts, "entries": naming, "logged": bool(naming)}


# A log shaped like the real one, used to prove the columns can fail. Every failure row below
# is the SAME function that guards the real files, run against a log that is wrong in exactly
# one way — so a guard that cannot notice is caught here rather than in production.
_VERSION = "9.9.9"
_SHA = "f" * 64
_GOOD_LOG = f"""# GOV-OS — build progress

## EP-01 BUILD — something earlier — 2026-01-01

Body text. The founding stood at 1.0.0 then.

## EP-99 BUILD — the founding moved and this entry says so — 2026-01-02

The founding bumped to {_VERSION}, a MINOR, because a new op family entered.
Pack sha256 `{_SHA}`.

### A section inside that entry

More body.
"""


class TestTheFoundingOnDiskIsNamedInTheLog(unittest.TestCase):
    """The real files. This is the row that goes red when a founding moves unlogged."""

    def test_the_founding_version_and_pack_hash_are_named_together_in_one_entry(self):
        a = audit()
        self.assertTrue(
            a["logged"],
            "the founding on disk is version " + a["version"] + " with pack sha256 "
            + a["sha256"] + ", and no single entry in planning/build/BUILD-PROGRESS_v3.md "
            "names both. A founding that moves without the log moving is a constitution "
            "whose source document changed with nothing on the record saying so. Write the "
            "entry: state the version, its change class (MINOR for a new surface, PATCH for "
            "an amendment inside one EP's own scope), the reason, and this hash.")

    def test_the_hash_this_guard_checks_is_the_bytes_on_disk(self):
        """Not a re-serialization and not a field the pack could declare about itself."""
        with open(PACK_PATH, "rb") as fh:
            raw = fh.read()
        self.assertEqual(pack_facts()["sha256"], hashlib.sha256(raw).hexdigest())


class TestTheColumnCanFail(unittest.TestCase):
    """Prove the guard can go red. A check that has never been seen failing is not known to
    be checking anything (the campaign-2 lesson, applied to this estate's own paperwork)."""

    def test_a_log_naming_both_facts_in_one_entry_passes(self):
        found = entries_naming(_GOOD_LOG, _VERSION, _SHA)
        self.assertEqual(len(found), 1)
        self.assertIn("EP-99", found[0])

    def test_a_log_that_never_names_the_hash_fails(self):
        log = _GOOD_LOG.replace(f"Pack sha256 `{_SHA}`.", "")
        self.assertEqual(entries_naming(log, _VERSION, _SHA), [],
                         "a version with no hash beside it cannot identify a founding")

    def test_a_log_that_never_names_the_version_fails(self):
        log = _GOOD_LOG.replace(_VERSION, "9.9.8")
        self.assertEqual(entries_naming(log, _VERSION, _SHA), [])

    def test_the_two_facts_in_different_entries_do_not_bind(self):
        log = _GOOD_LOG.replace(f"Pack sha256 `{_SHA}`.", "") + f"""
## EP-100 BUILD — a later entry that happens to quote a hash — 2026-01-03

Pack sha256 `{_SHA}` appears here, in an entry that never says which version it is.
"""
        self.assertEqual(entries_naming(log, _VERSION, _SHA), [],
                         "a version in one entry and a hash in another state nothing about "
                         "each other")

    def test_a_near_miss_version_does_not_answer_for_the_real_one(self):
        """The substring trap: an old `1.1.0` must not satisfy a check for `1.11.0`."""
        log = _GOOD_LOG.replace(_VERSION, "1.1.0").replace("1.1.0", "1.1.0")
        self.assertEqual(entries_naming(log, "1.11.0", _SHA), [])
        self.assertEqual(len(entries_naming(log, "1.1.0", _SHA)), 1)

    def test_one_changed_byte_in_the_pack_moves_the_hash_the_log_must_carry(self):
        """The J9 half: the version can stay still while the content moves, and this is what
        notices. Nothing on disk is touched — the mutation is in memory."""
        with open(PACK_PATH, "rb") as fh:
            raw = fh.read()
        before = hashlib.sha256(raw).hexdigest()
        after = hashlib.sha256(raw + b" ").hexdigest()
        self.assertNotEqual(before, after)
        with open(LOG_PATH, encoding="utf-8") as fh:
            log_text = fh.read()
        self.assertEqual(entries_naming(log_text, pack_facts()["version"], after), [],
                         "a pack whose content moved is unattested until an entry names its "
                         "new hash, even when the version string never changed")

    def test_the_splitter_keeps_sections_inside_their_entry(self):
        """A `### ` section must not become an entry of its own, or the one-entry binding
        could be split apart by a subheading and the guard would fail on a correct log."""
        heads = [e.splitlines()[0] for e in entries(_GOOD_LOG)]
        self.assertEqual(len(heads), 2)
        self.assertTrue(all(h.startswith("## ") and not h.startswith("###") for h in heads))
        self.assertIn("### A section inside that entry", entries(_GOOD_LOG)[1])


if __name__ == "__main__":
    unittest.main()
