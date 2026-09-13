"""EP-30-C4 — THE SHARED GRANT AT THE PORT: a grant that asks what it is granting over.

WHAT THIS UNIT DID. `SHM-GRANT` shipped declaring an EMPTY `checks` list and citing
`COMM-LAW-SHARE-GRANT`, a rule the founding pack has never contained. So a grant naming a
region nobody created, handed to a party nobody established, was appended and answered with
success, citing a law that did not exist. This unit CREATES that law through the founding
door and gives the operation THE ONE QUESTION THE CHECK VOCABULARY CAN EXPRESS — the region
names an established prior record — so that its refusal names a rule that exists.

ONE QUESTION AND NOT TWO, AND THE NARROWING IS A FINDING RATHER THAN A SCOPE CUT. The plan
shipped asking two. Its own first builder falsified the second at the arms and stopped
(`:1989`), the mentor re-drove it and ruled option A (`:1991`), and the row was WITHDRAWN
WITH ITS EVIDENCE rather than deleted. `grantees` is MANY-VALUED, every one of the check
kinds asks its question about ONE VALUE, and THE VOCABULARY HAS NO QUANTIFIER — so a
many-valued parameter cannot be asked anything at all: not every, not any, not none. That
gap is EXHIBITED here as a driven row (`TheCardinalityGapIsExhibited`) rather than asserted
in prose, because A QUESTION THIS UNIT SILENTLY STOPPED ASKING WOULD BE INDISTINGUISHABLE,
AT ANY LATER READING, FROM A QUESTION IT NEVER HAD.

TWO ROWS HERE PASS BY EXHIBITING A GAP AND THEIR GREEN IS A BOUNDARY RATHER THAN A PASS —
`TheCardinalityGapIsExhibited` and `TheAuthorityWallIsExhibited`. Each names, in its own
docstring, exactly what would INVERT it. They are instruments pointed at known gaps and they
fire BY FAILING WHEN THE GAP CLOSES. That is deliberate: the estate's close ledger records
that four real defects in a fortnight were found by a change or an attempt and none by an
instrument, and a row that goes red when the estate gains a capability is the cheapest
instrument that exists for the opposite failure.

AND THE COMPLEMENT OF THIS ARC'S SIGNATURE DEFECT, WHICH THIS UNIT'S OWN STOP FOUND. Five
layers of this arc say A CHECK THAT HAS NEVER BEEN SHOWN REFUSING ANYTHING IS NOT A CHECK.
The withdrawn spelling is the inverse: A CHECK THAT CANNOT BE SHOWN ACCEPTING ANYTHING IS
NOT A CHECK EITHER — it refuses the lawful and the unlawful with one message, and every
directional row over it passes. `TheCardinalityGapIsExhibited` drives that spelling four ways
with BOTH SCALAR CONTROLS SEPARATING, so the finding is a fact about the vocabulary and not
about a broken probe.

WHAT THIS UNIT DID NOT LAND, AND IT IS STATED HERE RATHER THAN LEFT TO A READER. It does not
ask whether the grantees are established entities (no quantifier — EP-30-K2 carries the
capability, EP-30-C4W the wiring) and it does not ask whether the granter HOLDS the region
(that needs a record bound by one parameter and a field of it compared against another —
EP-30-K1's `bound_field`, wired onto this operation by EP-30-C4W). The law's own text says
so at its own hand, because A LAW THAT CLAIMED THE COVER IT DOES NOT HAVE WOULD BE WORSE THAN
THE DANGLING CITATION IT REPLACES.
"""
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(REPO, "src"))

import era_pin  # noqa: E402  — the estate's one home for reading a path at a named commit

import founding.install as install  # noqa: E402
from kernel.blobs import BlobStore  # noqa: E402
from kernel.boot import build_kernel  # noqa: E402
from kernel.errors import OpError  # noqa: E402
from kernel.opdefs import OP_CHECKS  # noqa: E402

PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")
PAPER_PATH = os.path.join(REPO, "design", "36-CAMPAIGN-3-DEPTH.md")
LOG_PATH = os.path.join(REPO, "planning", "build", "BUILD-PROGRESS_v3.md")

#: THE ERA THIS UNIT'S OWN EDIT STANDS AGAINST — the commit at the builder's hand IMMEDIATELY
#: BEFORE its first write, captured by `git rev-parse HEAD` and filed at
#: `planning/evidence/EP-30-C4/PRE-EDIT-HEAD.txt`. Chosen by CONTENT and not by version
#: number: the era's pack hashes to the value this unit recorded as its BEFORE, and
#: `test_the_era_pin_resolves_to_the_pack_this_unit_actually_edited` drives exactly that,
#: because choosing a pin by version rather than by content is the estate's most expensive
#: known trap and `era_pin` states plainly that it cannot see it for its callers.
PRE_EDIT_COMMIT = "c7438cd6c0ecf8d51352c47d82adf9d0fa7a3aff"
#: §A57 era-pin (EP-31-BUILD, board :2662). C4's OWN AFTER commit — the founding as C4 LEFT it
#: (1.30.0, COMM-LAW-SHARE-GRANT created). The version-move row reads its era, not the live pack,
#: so it is robust to any LATER founding move (EP-31 creating MEM-LAW-BUDGET was the first).
C4_AFTER_ERA_COMMIT = "b64defaa3caefad6cd39ab18d2320e5fcb895642"
PRE_EDIT_PACK_SHA = "ee1987d72d07d08d2fcad34f2ffac09c901a95b317ef07cd2953513bfcce05e3"

#: §A57 era-pin (ATTEST-CONTROL-ERAPIN, board :2922). THE ANCHOR THE REAL-LOG NON-VACUITY CONTROL
#: BELOW READS OVER — EP-35's founding move to 1.32.0, whose pack sha EP-37 later re-cited HELD /
#: unmoved. This pair is a DRIVEN FINDING, never an asserted literal: it is the ONE historical
#: (version, sha) that satisfies BOTH of the control's properties over the CURRENT log — non-vacuity
#: (the sha is named by >=2 entries: EP-35's bump AND EP-37's held re-citation) AND exactly ONE
#: bump-attestation. The whole population was enumerated from the pack's git history and each pair
#: driven against both properties; the on-disk founding has since moved (1.33.0, then 1.34.0) and its
#: sha now names ONE entry, which is WHY this control reads the era and never the live tree. Chosen by
#: CONTENT: `test_the_attest_anchor_era_resolves_by_content` hashes the blob at the commit and matches
#: it against ATTEST_ANCHOR_SHA, so a pin resolving to the wrong tree fails loudly rather than passing
#: vacuously. Evidence: planning/evidence/ATTEST-CONTROL-ERAPIN/ (the anchor-drive population table).
ATTEST_ANCHOR_COMMIT = "640fd2d182d8f7793133023f00abf7a244f99c1b"
ATTEST_ANCHOR_VERSION = "1.32.0"
ATTEST_ANCHOR_SHA = "b35de0aba16ad03b7b42a9ef391d670d156fe40776eda0bb938f25e0371cbd15"

LAW = "COMM-LAW-SHARE-GRANT"

#: THE WITHDRAWN SPELLING, kept as a LITERAL so the row that killed it can still be driven.
#: This is A3's evidence. It is never landed in the pack.
WITHDRAWN_GRANTEE_CHECK = {
    "check": "require_prior", "action": "CREATE-ACCOUNT", "field": "account_id",
    "param": "grantees", "cite": LAW, "message": "a grantee is not an established entity",
}


# =========================================================================================
# HELPERS — reading the pack, and founding a kernel from an AMENDED one for the red worlds
# =========================================================================================

def live_pack():
    with open(PACK_PATH, "rb") as fh:
        return json.loads(fh.read())


def op_definitions(pack):
    """Every op definition the pack creates, by name. THE POPULATION EVERY ROW BELOW COUNTS
    OVER, taken once so no row invents its own."""
    return {r["payload"]["name"]: r["payload"]["definition"]
            for s in pack["steps"] for r in s["records"] if r.get("action") == "CREATE-OP"}


def created_rules(pack):
    return {r["payload"]["rule_id"]
            for s in pack["steps"] for r in s["records"] if r.get("action") == "CREATE-RULE"}


class Founded:
    """A kernel founded from a pack this test hands it, so a red world can move a declaration
    WITHOUT touching the repository's own founding.

    WHY THE MODULE GLOBAL IS PATCHED AND RESTORED. `install.load_pack`'s default argument is
    bound at definition, so re-pointing `install.PACK_PATH` alone would be read by nothing.
    The TRUE loader is captured ONCE at class definition, before any patch, so a red world can
    never be founded by a lambda that another red world installed.
    """

    _TRUE_LOADER = staticmethod(install.load_pack)

    def __init__(self, pack=None):
        self.dir = tempfile.mkdtemp()
        self._saved = install.load_pack
        if pack is not None:
            path = os.path.join(self.dir, "pack.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(pack, fh)
            install.load_pack = lambda p=None: Founded._TRUE_LOADER(path)
        self.store, self.gate, self.views = build_kernel(
            os.path.join(self.dir, "record.jsonl"),
            blobs=BlobStore(os.path.join(self.dir, "blobs")))

    def close(self):
        install.load_pack = self._saved

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def landed_checks(self, opname):
        """The op's checks READ BACK OUT OF THE FOUNDED RECORD, never out of the file that
        produced it. An amendment proven by re-reading its own input proves nothing."""
        rec = [e for e in self.store.by_action("CREATE-OP")
               if (e.get("payload") or {}).get("name") == opname][0]
        defn = dict(dict(rec["payload"])["definition"])
        return [dict(c).get("check") for c in (defn.get("checks") or [])]

    def verdict(self, opname, actor, payload):
        """ACCEPTED with the record, or REFUSED with the rule that refused."""
        try:
            return ("ACCEPTED", self.gate.execute(opname, actor, dict(payload)))
        except OpError as e:
            return ("REFUSED", e)

    def establish(self, *account_ids):
        for a in account_ids:
            self.gate.execute("CREATE-ACCOUNT", "SYSTEM", {"account_id": a, "actor_class": "process"})

    def found_region(self, region, size=4096):
        self.gate.execute("MEM-GRANT", "SYSTEM", {"region": region, "size": size})


def pack_with_shm_checks(checks, pack=None):
    """A copy of the pack with SHM-GRANT's checks REPLACED. The red worlds' only lever."""
    p = copy.deepcopy(pack or live_pack())
    for s in p["steps"]:
        for r in s["records"]:
            if r.get("action") == "CREATE-OP" and r["payload"].get("name") == "SHM-GRANT":
                r["payload"]["definition"]["checks"] = copy.deepcopy(checks)
    return p


def _log_entries(log_text):
    """The build log's entries, split at its own `## ` headings (a `### ` is a section inside
    one and does not open an entry). Byte-for-byte the splitter the standing guard uses."""
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


#: THE VERSION-CLASS a bump-attestation is required to state (semver class of the move). A genuine
#: attestation restates it beside its transition; a bare MENTION never bothers to. ALL-CAPS,
#: word-boundaried, so it cannot be a substring of a longer word.
_BUMP_CLASS = re.compile(r"\b(?:MINOR|MAJOR|PATCH)\b")

#: A same-line ATTRIBUTION marker (archi ruling, board :3325). A P11 concurrent-work disclosure
#: re-cites a founding transition it did NOT make and attributes it to the named mover — "the
#: CONCURRENT EP-49A/EP-49B work, NOT this unit ... Attributed by file". Such a line MENTIONS the
#: move, it does not CLAIM it, even when it phrases the transition founding-adjacent
#: (`founding_version went 1.41.0 -> 1.42.0`). The estate's attribution convention is the word
#: "attribut(ed/ion)"; a genuine bump-attestation attests its OWN move and never disclaims it.
_ATTRIBUTED = re.compile(r"\battribut\w+", re.I)


def _claims_move_into(line, version):
    """True when THIS LINE CLAIMS the founding's move into `version`, false when it only MENTIONS
    one. The distinction is drawn per line and per transition, because the referential entry the
    ruling names carries its mention on a different line from any claim of its own.

    A transition arrow into `version` (`OLD -> version`, ASCII or Unicode) is a CLAIM when, on its
    own line, its OLD side DIFFERS from `version` (a genuine move, never a restatement) AND EITHER
    the founding subject is bound immediately before the transition — the estate's move-claim forms
    `founding_version 1.32.0 -> 1.33.0`, `the founding moved, 1.29.0 -> 1.30.0`, `THE FOUNDING MOVED
    1.32.0 -> 1.33.0`, `moves the founding 1.30.0 -> 1.31.0` — OR the line carries the bump
    version-class the attestation must state (`A2 -- 1.24.0 -> 1.25.0, MINOR`, the one genuine chain
    member whose transition line names no founding subject).

    AN UNMOVED TRANSITION IS A MENTION, NEVER A CLAIM (archi ruling, board :2977 — "OLD != target").
    A no-bump close discloses that the founding did NOT move by restating its version beside itself,
    `founding_version 1.35.0 -> 1.35.0 (UNMOVED)`, and pairs the full pack sha in the same entry to
    say WHICH pack is byte-identical. Its OLD side EQUALS `version`, so it records no move and the
    arrow is excluded. This is a STRICT NARROWING — it removes only same-version arrows and changes
    nothing about a genuine `OLD -> version` where OLD differs, so a genuine same-target double (two
    `1.34.0 -> 1.35.0` attestations) still counts as two. The exact false positive it excludes is the
    on-disk 1.35.0 no-bump close, which paired the full pack sha with an unmoved-version line and was
    read as a second attestation of the founding on disk.

    A MENTION carries neither adjacent to its transition: `mover-1 COMPLETE-KEY-FAMILY moved
    1.32.0->1.33.0` attributes the move to a named unit, and `CLOSED :2899 (1.32.0 -> 1.33.0)`
    parks the transition in a close reference — the two arrow lines the LEDGER-REEXPRESS-3 entry
    carries, and among the false positives this reader excludes.
    """
    trans = re.compile(r"(\d+\.\d+\.\d+)\s*(?:->|→)\s*" + re.escape(version) + r"(?![\w.])")
    for mo in trans.finditer(line):
        if mo.group(1) == version:
            continue  # OLD == target: an UNMOVED restatement records no move (board :2977)
        founding_bound = re.search(r"founding[\w]*\b[^.\n]{0,25}$", line[:mo.start()], re.I)
        if founding_bound or _BUMP_CLASS.search(line):
            # archi ruling, board :3325 — a same-line ATTRIBUTED mention is not a claim,
            # wherever the attribution sits on the line. A concurrent-work disclosure re-cites
            # the transition founding-adjacent yet attributes the move to the named mover and
            # disclaims its own authorship; it claims no move of its own, so no honest disclosure
            # is ever shortened for this instrument (the mgr marker-surgery that occasioned this
            # is reverted). A genuine bump-attestation attests its OWN move and carries no
            # attribution word, so it is untouched.
            if _ATTRIBUTED.search(line):
                continue
            return True
    return False


def bump_attestations(log_text, version, sha):
    """The entries that ATTEST THE FOUNDING'S MOVE TO `version` — the reserved bump-attestation.

    THE TRUE SUBJECT IS WHICH ENTRIES CLAIM A MOVE, NOT WHICH MENTION ONE (archi ruling, board
    :2914). A bump attestation records a version TRANSITION INTO the live version — `OLD -> version`,
    the estate's own bump form (ASCII `->` or the Unicode arrow, both on the record across every
    founding move: `1.13.0 -> 1.14.0` ... `1.32.0 -> 1.33.0`). But an entry that MENTIONS another
    unit's transition — attributing it to a named mover, or citing it in a close — is not itself an
    attestation: `## MAINT LEDGER-REEXPRESS-3` moved no founding, yet its body names mover-1's
    `1.32.0 -> 1.33.0` and re-cites the same pack sha, so a whole-entry `sha in e and OLD->version
    anywhere` counted it as a second attestation of the on-disk founding. The reader now asks, per
    line, whether the transition is CLAIMED (`_claims_move_into`) rather than merely present.

    A HELD-founding close that re-cites the same pack sha as byte-identical / unmoved evidence names
    NO transition into the live version at all, so it was never counted and is not now. The full
    64-char (version, sha) pair is RESERVED for the one bump-attesting entry (archi ruling, board
    :2805); a held close discloses the sha in SHORT (8-char) form or unmoved-phrasing — poorer
    disclosure to please an instrument is never asked of it, and the fix lives in this reader.

    THIS STRENGTHENS THE STANDING BINDING, IT DOES NOT LOOSEN IT. A claim is a transition, and a
    transition is a co-occurrence of `version` with an arrow whose target it is, so the match set is
    a STRICT SUBSET of the standing guard's `version in e and sha in e` — and a strict subset of the
    prior whole-entry reader, which this only NARROWS by dropping mentions. Driven against the whole
    historical bump chain (`planning/evidence/ATTEST-MATCHER-REFINE/`): every genuine (version, sha)
    is kept, and the on-disk founding drops from two matches to one with LEDGER-REEXPRESS-3 excluded.
    """
    return [e.splitlines()[0] for e in _log_entries(log_text)
            if sha in e and any(_claims_move_into(ln, version) for ln in e.splitlines())]


# =========================================================================================
# A1 — ABSENCE, AT THE ERA THIS UNIT CHANGED. Plus R4, the control that can fail.
# =========================================================================================

class TheOperationAskedNothingBeforeThisUnit(unittest.TestCase):
    """A1 and R4.

    A1 IS A READING OF THE ERA AND NOT OF THE LIVE TREE, AND THAT IS FORCED RATHER THAN
    CHOSEN. The row asserts that `SHM-GRANT` declared NO checks — the red fact this unit
    exists to change — so reading it against the live pack after the edit would assert the
    opposite of what the unit did. Pinned at the commit immediately before this unit's first
    write, verified BY CONTENT.

    AN EMPTY LIST FROM A WALKER THAT NEVER MATCHED ANYTHING IS NOT AN ABSENCE. R4 is the
    other half of this row and is not optional: the SAME reader, over an op known to declare
    checks, must come back non-empty.
    """

    @classmethod
    def setUpClass(cls):
        cls.era = era_pin.pack_at(PRE_EDIT_COMMIT, missing="assert")
        cls.era_ops = op_definitions(cls.era)

    def test_the_era_pin_resolves_to_the_pack_this_unit_actually_edited(self):
        """A PIN RESOLVING TO THE WRONG TREE WOULD MAKE EVERY ROW BELOW PASS WRONGLY. The
        era's bytes are hashed and matched against the BEFORE this unit recorded at its own
        hand, so the pin is chosen by CONTENT rather than by a version number."""
        raw = era_pin.blob_at(PRE_EDIT_COMMIT, era_pin.PACK_PATH, missing="assert")
        self.assertEqual(hashlib.sha256(raw).hexdigest(), PRE_EDIT_PACK_SHA)

    def test_a1_shm_grant_declared_no_checks_at_the_era_before_this_unit(self):
        self.assertEqual(self.era_ops["SHM-GRANT"]["checks"], [])

    def test_a1_and_it_cited_a_law_the_pack_did_not_contain(self):
        """THE OTHER HALF OF THE RED FACT. A citation to a rule that does not exist is the
        record plane's own shape failing on the plane it exists to protect."""
        self.assertEqual(self.era_ops["SHM-GRANT"]["law_cited"], LAW)
        self.assertNotIn(LAW, created_rules(self.era))

    def test_a1_control_the_same_reader_finds_an_op_that_DOES_declare_checks(self):
        """R4. The control names FILE-CUSTODY-TRANSFER and quotes its `require_prior` over
        the giving party, so the row proves the reader can find a check rather than proving
        the field name happens to be absent everywhere."""
        control = self.era_ops["FILE-CUSTODY-TRANSFER"]["checks"]
        self.assertNotEqual(control, [], "the reader found nothing where checks are known "
                                         "to be declared — the walker is broken, not the op")
        giving = [c for c in control
                  if c.get("check") == "require_prior" and c.get("param") == "from_entity"]
        self.assertEqual(len(giving), 1)
        self.assertEqual(giving[0]["action"], "CREATE-ACCOUNT")
        self.assertEqual(giving[0]["field"], "account_id")

    def test_a1_the_field_this_row_reads_is_check_and_not_kind(self):
        """THE AUTHOR'S FIRST CENSUS OF THIS VOCABULARY READ THE WRONG FIELD and returned
        fourteen confident `None`s. A row whose walker reads a field no check row carries
        would report a confident, wrong absence for every operation in the pack."""
        rows = [c for d in self.era_ops.values() for c in (d.get("checks") or [])]
        self.assertTrue(rows)
        self.assertTrue(all("check" in c for c in rows))
        self.assertFalse(any("kind" in c for c in rows),
                         "no check row carries a `kind` field — a walker reading it would "
                         "return None for every row and call the result an absence")


# =========================================================================================
# A2 — THE LAW IS CREATED, THROUGH THE FRONT DOOR, AND THE FOUNDING MOVES
# =========================================================================================

class TheLawIsCreatedAndTheFoundingMoved(unittest.TestCase):
    """A2. The refusal must name a rule that exists, so the law is created here or this unit
    lands nothing. Created by a `CREATE-RULE` record in the shape `FS-LAW-CUSTODY-TRANSFER`
    already uses, through the founding door, with the founding version moved MINOR."""

    def test_a2_the_law_is_created_by_a_CREATE_RULE_record_in_the_pack(self):
        pack = live_pack()
        recs = [r for s in pack["steps"] for r in s["records"]
                if r.get("action") == "CREATE-RULE" and r["payload"]["rule_id"] == LAW]
        self.assertEqual(len(recs), 1, "exactly one creating record, or the rule's identity "
                                       "is a question rather than a fact")
        p = recs[0]["payload"]
        self.assertEqual(recs[0]["object"], LAW)
        self.assertEqual(p["scope"], "space:root")
        self.assertEqual(p["enforcement"], "live")
        self.assertTrue(p["text"].strip())
        self.assertTrue(p["enforced_by"].strip())

    def test_a2_the_law_carries_ITS_OWN_ACCOUNT_OF_WHAT_IT_DOES_NOT_REACH(self):
        """A LAW THAT CLAIMED THE COVER IT DOES NOT HAVE WOULD BE WORSE THAN THE DANGLING
        CITATION IT REPLACES. The two unasked questions are named IN THE RULE'S OWN TEXT with
        their owners, so a reader of the record — not of this plan — learns the boundary."""
        pack = live_pack()
        p = [r["payload"] for s in pack["steps"] for r in s["records"]
             if r.get("action") == "CREATE-RULE" and r["payload"]["rule_id"] == LAW][0]
        for owner in ("EP-30-K2", "EP-30-C4W"):
            self.assertIn(owner, p["text"],
                          "the law names the unit that owns each question it cannot ask")

    def test_a2_the_law_is_in_the_FOUNDED_RECORD_and_not_only_in_the_file(self):
        """A rule present in the pack but not in the founded record would be a rule the
        machine never received. Read out of the record the founding produced."""
        with Founded() as f:
            got = [e for e in f.store.by_action("CREATE-RULE")
                   if (e.get("payload") or {}).get("rule_id") == LAW]
            self.assertEqual(len(got), 1)

    def test_a2_the_founding_version_moved_MINOR_from_the_era(self):
        era = era_pin.pack_at(PRE_EDIT_COMMIT, missing="assert")["founding_version"]
        now = era_pin.pack_at(C4_AFTER_ERA_COMMIT, missing="assert")["founding_version"]  # §A57 era-pin :2662
        self.assertNotEqual(era, now, "a new law and a new check row on a shipped op is a "
                                      "new surface, and a new surface moves the founding")
        e_maj, e_min, _ = (int(x) for x in era.split("."))
        n_maj, n_min, n_pat = (int(x) for x in now.split("."))
        self.assertEqual((n_maj, n_min, n_pat), (e_maj, e_min + 1, 0),
                         "MINOR for a new surface — not PATCH, which is an amendment inside "
                         "one EP's own scope")

    def test_a2_the_founding_on_disk_is_ATTESTED_in_one_build_log_entry(self):
        """THE LEDGER DUTY IS PART OF MAKING THE TREE GREEN, NOT A RECORD OF HAVING DONE SO.
        The estate mechanically refuses an unattested founding move: EXACTLY ONE entry must
        ATTEST THE MOVE to the founding on disk — naming the pack's own sha256 AND recording the
        version transition INTO it. Driven here as well as at the standing guard so THIS unit's
        move carries its own instrument.

        WHY THE ANCHOR IS THE TRANSITION AND NOT MERE CO-OCCURRENCE (archi ruling, board :2805).
        A version-and-sha co-occurrence is satisfied twice over: once by the bump-attesting entry
        and again by any later HELD-founding close that re-cites the same full sha as
        byte-identical / unmoved evidence (EP-37 did exactly this over EP-35's 1.32.0 move). Both
        are legitimate disclosures, so the count cannot be lowered by asking anyone to disclose
        less. The full (version, sha) pair is RESERVED for the one bump-attestation, which is the
        entry that records the MOVE — a form the held recitation does not carry. `bump_attestations`
        strengthens the standing binding rather than loosening it (its match set is a strict
        subset of version+sha)."""
        with open(PACK_PATH, "rb") as fh:
            raw = fh.read()
        version = json.loads(raw)["founding_version"]
        sha = hashlib.sha256(raw).hexdigest()
        with open(LOG_PATH, encoding="utf-8") as fh:
            log = fh.read()
        naming = bump_attestations(log, version, sha)
        self.assertEqual(len(naming), 1,
                         "the founding on disk is %s with pack sha256 %s, and it must be the "
                         "target of EXACTLY ONE bump-attestation (an entry recording the "
                         "transition INTO %s and naming this pack sha). Found: %r"
                         % (version, sha, version, naming))


# =========================================================================================
# THE BUMP-ATTESTATION ANCHOR — IT MUST STILL RED ON A GENUINE DOUBLE-BUMP (MAINT-PACK-ATTEST-GUARD)
# =========================================================================================

#: A log shaped like the real one, used to prove the anchor can fail and to fix the FORM
#: distinction the ruling drew between BUILD-PROGRESS line 60869 (the move) and line 61308 (the
#: held re-citation). Every row below is the SAME reader the guard runs, over a synthetic log
#: wrong in exactly one way — so a reader that cannot tell a move from a re-citation is caught
#: here rather than in production.
_V = "7.7.7"
_SHA = "a" * 64
_ONE_BUMP_ONE_HELD = f"""# GOV-OS — build progress

## EP-AA BUILD — something earlier — 2026-01-01

The founding stood at 7.7.6 then; this entry names no new pack.

## EP-BB BUILD — THE FOUNDING MOVED and this entry attests it — 2026-01-02

FOUNDING MOVE. founding_version 7.7.6 -> {_V}, class MINOR (a new surface). Pack sha256
{_SHA} (version AND hash named together in this one entry).

## EP-CC BUILD — a HELD close that re-cites the same sha as unmoved evidence — 2026-01-03

IN FENCE, DELIBERATELY UNTOUCHED (HELD): founding-pack.json (sha256 {_SHA}, byte-identical to
the pre-EP baseline); founding byte-untouched at {_V}.
"""


class TheBumpAttestationAnchorCanFail(unittest.TestCase):
    """MAINT-PACK-ATTEST-GUARD. A CHECK THAT HAS NEVER BEEN SHOWN REFUSING ANYTHING IS NOT A
    CHECK — this estate's signature defect, and the amended guard is exactly the shape that
    carries it. The reader must still RED on a genuine double-bump, or it has been loosened into
    a formality."""

    def test_the_real_shape_one_move_one_held_recitation_counts_only_the_move(self):
        """THE DEFECT THIS UNIT FIXES, DRIVEN SYNTHETICALLY. One bump-attestation and one HELD
        close that re-cites the SAME full sha — the exact shape of EP-35 (60869) and EP-37
        (61308) — counts as ONE. The held recitation names the sha but records no move, so it
        is not an attestation and is not counted."""
        atts = bump_attestations(_ONE_BUMP_ONE_HELD, _V, _SHA)
        self.assertEqual(len(atts), 1, "one move + one held re-citation must count as one")
        self.assertIn("EP-BB", atts[0], "the counted entry is the one that records the move")
        self.assertNotIn("EP-CC", "".join(atts), "the held re-citation must not be counted")

    def test_a_GENUINE_double_bump_REDS(self):
        """THE LOAD-BEARING CONTROL. Two REAL bump-attestations of the same move — each naming
        the transition into the version AND the pack sha — must count as TWO, so the guard's
        assertEqual(len, 1) reds. The anchor tightened the FORM; it did not remove the guard's
        ability to fail on the thing it exists to catch."""
        double = _ONE_BUMP_ONE_HELD + f"""
## EP-DD BUILD — a SECOND genuine bump-attestation of the SAME move — 2026-01-04

FOUNDING MOVE. founding_version 7.7.6 -> {_V}, MINOR. Pack sha256 {_SHA}.
"""
        atts = bump_attestations(double, _V, _SHA)
        self.assertEqual(len(atts), 2,
                         "two genuine bump-attestations of one move must both count — the guard "
                         "reds on a double-bump, which is what a guard that can fail looks like")

    def test_a_referential_MENTION_of_a_move_is_NOT_counted_and_the_control_can_fail(self):
        """THE DEFECT :2914 NAMES, DRIVEN SYNTHETICALLY. A second entry that MENTIONS the move —
        attributing it to a named mover and parking it in a close reference, the LEDGER-REEXPRESS-3
        shape — re-cites the SAME full sha but CLAIMS no move of its own. The sharpened reader counts
        the one genuine claim and drops the mention.

        THE HALF THAT MATTERS: the pre-:2914 whole-entry reader WOULD have counted the mention, so
        this control is watching the sharpening refuse something rather than passing vacuously — the
        estate's signature defect is a check that has never been shown refusing anything."""
        referential = _ONE_BUMP_ONE_HELD + f"""
## MAINT LEDGER-REEXPRESS-N — re-expresses a ledger, moves NO founding — 2026-01-05

Clears the reds the earlier move left in settled modules; this entry moves no founding of its own.
production founding_version = {_V} (mover-1 SOME-UNIT moved 7.7.6->{_V}); the pack is byte-identical.
mover-1 (SOME-UNIT) CLOSED :999 (7.7.6 -> {_V}). Pack sha256 {_SHA}, re-cited as unmoved evidence.
"""
        atts = bump_attestations(referential, _V, _SHA)
        self.assertEqual(len(atts), 1, "the referential MENTION must not count as a 2nd attestation")
        self.assertIn("EP-BB", atts[0], "the one counted entry is the genuine bump-claim")
        self.assertNotIn("LEDGER-REEXPRESS-N", "".join(atts), "the mention entry is excluded")
        loose = [e.splitlines()[0] for e in _log_entries(referential)
                 if _SHA in e and re.search(
                     r"\d+\.\d+\.\d+\s*(?:->|→)\s*" + re.escape(_V) + r"(?![\w.])", e)]
        self.assertEqual(len(loose), 2,
                         "the pre-:2914 whole-entry reader counts the mention as a second "
                         "attestation — the CLAIM/MENTION distinction this control drives is real, "
                         "and a select-nothing (whole-entry) form fails here")

    def test_a_founding_adjacent_ATTRIBUTED_mention_is_excluded_and_the_control_can_fail(self):
        """archi ruling, board :3325 — DRIVEN SYNTHETICALLY. The shape the LEDGER-REEXPRESS control
        did NOT catch: a concurrent-work disclosure that re-cites the transition FOUNDING-ADJACENT
        (`founding_version went 7.7.6 -> 7.7.7`, which trips the founding-bound check) yet attributes
        the move to the named mover and disclaims its own authorship (`the CONCURRENT mover-1 work,
        NOT this unit ... Attributed by file`). It MENTIONS the move; it claims none. This is the
        exact production shape (EP-47B's disclosure beside EP-49B's 1.42.0 move) that once held the
        reserved slot and forced a peer's honest full-sha disclosure to be shortened for the
        instrument — which this ruling ends.

        BOTH DIRECTIONS, or the sharpening is a formality:
          - the attributed mention is EXCLUDED (the new behavior);
          - the mention IS founding-adjacent, so the pre-ruling reader (founding-bound, no
            attribution guard) WOULD have counted it as a second attestation — the sharpening is
            watched refusing something;
          - a genuine founding-adjacent claim carrying NO attribution word is STILL counted (EP-BB)."""
        attributed = _ONE_BUMP_ONE_HELD + f"""
## EP-BESIDE — a concurrent-work disclosure that re-cites the move it did NOT make — 2026-01-07

CONCURRENT-WORK DISCLOSURE (P11, attributed — NOT mine): founding_version went 7.7.6 -> {_V} in my window; this is the CONCURRENT mover-1 work, NOT this unit. Attributed by file. Pack sha256 {_SHA}, the tree I built against.
"""
        atts = bump_attestations(attributed, _V, _SHA)
        self.assertEqual(len(atts), 1, "the attributed founding-adjacent mention must not count")
        self.assertIn("EP-BB", atts[0], "the one counted entry is the genuine bump-claim")
        self.assertNotIn("EP-BESIDE", "".join(atts), "the attributed mention is excluded")
        def _pre_ruling_claims(ln, version):
            # _claims_move_into WITHOUT the :3325 attribution guard — the reader as it stood before.
            trans = re.compile(r"(\d+\.\d+\.\d+)\s*(?:->|→)\s*" + re.escape(version) + r"(?![\w.])")
            for mo in trans.finditer(ln):
                if mo.group(1) == version:
                    continue
                if re.search(r"founding[\w]*\b[^.\n]{0,25}$", ln[:mo.start()], re.I) or _BUMP_CLASS.search(ln):
                    return True
            return False
        preruling = [e.splitlines()[0] for e in _log_entries(attributed)
                     if _SHA in e and any(_pre_ruling_claims(ln, _V) for ln in e.splitlines())]
        self.assertEqual(len(preruling), 2,
                         "the pre-ruling founding-bound reader counts the attributed mention as a "
                         "second attestation — the sharpening is watched refusing something real")
        self.assertIn("EP-BESIDE", "".join(preruling),
                      "and the thing it refuses is exactly the founding-adjacent attributed mention")

    def test_an_UNMOVED_same_version_transition_is_NOT_a_move_claim(self):
        """THE OLD != target NARROWING, DRIVEN SYNTHETICALLY (archi ruling, board :2977). A no-bump
        close discloses that the founding did NOT move by restating its version beside itself —
        `founding_version {V} -> {V} (UNMOVED)` — and pairs the full pack sha in the SAME entry to
        say which pack is byte-identical. The OLD side EQUALS the target, so it records no move and
        must not be counted. The exact production shape this fixes: the on-disk 1.35.0 close paired
        the full sha with an unmoved-version line and was read as a second attestation.

        BOTH DIRECTIONS, or the narrowing is a formality:
          - the unmoved same-version arrow is EXCLUDED (the new behavior);
          - the pre-:2977 reader (founding-bound OR bump-class, WITHOUT the OLD != target guard)
            WOULD have counted it — so the narrowing is watched REFUSING something, this estate's
            signature-defect discipline;
          - a genuine `OLD -> target` (OLD differs) on an otherwise-identical founding-bound line is
            STILL a claim — the narrowing removes only same-version arrows and nothing else.
        """
        unmoved = _ONE_BUMP_ONE_HELD + f"""
## EP-UNMOVED — a no-bump close that restates the version unmoved and re-cites the sha — 2026-01-06

NO-BUMP GUARD (satisfied): founding_version {_V} -> {_V} (UNMOVED). Pack sha256 {_SHA}, byte-identical.
"""
        atts = bump_attestations(unmoved, _V, _SHA)
        self.assertEqual(len(atts), 1, "the unmoved same-version transition must not count as a 2nd "
                                       "attestation — OLD == target records no move")
        self.assertIn("EP-BB", atts[0], "the one counted entry is the genuine bump-claim")
        self.assertNotIn("EP-UNMOVED", "".join(atts), "the unmoved restatement is excluded")

        # CAN-FAIL: the pre-:2977 reader had no OLD != target guard, so its founding-bound arm counts
        # the unmoved line. The sharpened reader refuses it — a narrowing watched refusing something,
        # never a formality passing vacuously.
        def _claims_pre2977(line, version):
            trans = re.compile(r"(\d+\.\d+\.\d+)\s*(?:->|→)\s*" + re.escape(version) + r"(?![\w.])")
            for mo in trans.finditer(line):
                founding_bound = re.search(r"founding[\w]*\b[^.\n]{0,25}$", line[:mo.start()], re.I)
                if founding_bound or _BUMP_CLASS.search(line):
                    return True
            return False
        loose = [e.splitlines()[0] for e in _log_entries(unmoved)
                 if _SHA in e and any(_claims_pre2977(ln, _V) for ln in e.splitlines())]
        self.assertEqual(len(loose), 2,
                         "the pre-:2977 reader counts the unmoved restatement — the OLD != target "
                         "narrowing is real and refuses exactly this false positive")
        self.assertIn("EP-UNMOVED", "".join(loose),
                      "and the entry it now refuses is the unmoved restatement")

        # STRICT NARROWING: only same-version arrows go. A genuine OLD -> target on the identical
        # founding-bound shape is still a claim; the same-version restatement is not.
        self.assertTrue(
            _claims_move_into(f"founding_version 7.7.6 -> {_V} (MOVED). Pack sha256 {_SHA}.", _V),
            "a genuine OLD -> target on the unmoved line's own shape must still be a claim")
        self.assertFalse(
            _claims_move_into(f"founding_version {_V} -> {_V} (UNMOVED). Pack sha256 {_SHA}.", _V),
            "the unmoved same-version transition is not a claim")

    def test_the_unicode_arrow_form_is_also_a_move(self):
        """The estate writes the transition with an ASCII `->` and with the Unicode arrow across
        its history; both are the same attestation form and both must count."""
        uni = _ONE_BUMP_ONE_HELD.replace(f"7.7.6 -> {_V}", f"7.7.6 → {_V}")
        self.assertEqual(len(bump_attestations(uni, _V, _SHA)), 1)

    def test_a_held_recitation_alone_is_not_an_attestation(self):
        """A log carrying ONLY the held re-citation (full sha, no transition into the version)
        attests no move: zero. The founding would read as unattested — correctly, because a
        re-citation of a sha is not a record that the founding moved TO it."""
        held_only = f"""# log

## EP-CC BUILD — a HELD close, sha re-cited, no move — 2026-01-03

sha256 {_SHA}, byte-identical to the pre-EP baseline; founding byte-untouched at {_V}.
"""
        self.assertEqual(bump_attestations(held_only, _V, _SHA), [])

    def test_the_binding_survives_a_move_named_without_its_hash(self):
        """THE STANDING (version, sha) BINDING IS PRESERVED. An entry that records the move but
        names no pack sha states nothing about WHICH pack this version is — not counted, exactly
        as the standing guard requires. The move form was ADDED to the binding, not swapped for
        it."""
        no_sha = _ONE_BUMP_ONE_HELD.replace(_SHA, "")
        self.assertEqual(bump_attestations(no_sha, _V, _SHA), [])

    def test_the_attest_anchor_era_resolves_by_content(self):
        """THE PIN IS CHOSEN BY CONTENT, NEVER BY VERSION NUMBER (board :410, the estate's most
        expensive known trap; `era_pin` states plainly it cannot see it for its callers). The
        blob at the anchor commit is hashed and matched against the driven ATTEST_ANCHOR_SHA, so
        a pin that has drifted to the wrong tree FAILS here rather than making the control below
        pass over some other era's founding."""
        raw = era_pin.blob_at(ATTEST_ANCHOR_COMMIT, era_pin.PACK_PATH, missing="assert")
        self.assertEqual(hashlib.sha256(raw).hexdigest(), ATTEST_ANCHOR_SHA)
        self.assertEqual(json.loads(raw)["founding_version"], ATTEST_ANCHOR_VERSION)

    def test_the_reader_over_the_real_log_counts_the_bump_and_leaves_the_held_uncounted(self):
        """OVER THE REAL LOG, AT A FROZEN ERA: exactly one attestation, and it is EP-35's move.
        Non-vacuity is proven by showing the EP-37 held entry IS present naming the same full sha
        yet is not the counted attestation — the two entries the ruling names, driven.

        THE SOURCE IS THE ERA, NOT THE LIVE PACK, AND ONLY THE SOURCE CHANGED (board :2922). The
        control's law is unchanged: exactly ONE bump-attestation AND the sha named by >=2 entries.
        It once read the on-disk pack, which WAS 1.32.0 when this row was written; the founding has
        since moved (1.33.0, then 1.34.0) and the on-disk sha now names ONE entry, so a live read
        would fail non-vacuity for a reason that has nothing to do with the reader this row proves.
        The (version, sha) is read from git at the anchor commit — never a live read, never an
        asserted literal driving the control — while the LOG stays live (append-only; the reader's
        real input)."""
        raw = era_pin.blob_at(ATTEST_ANCHOR_COMMIT, era_pin.PACK_PATH, missing="assert")
        version = json.loads(raw)["founding_version"]
        sha = hashlib.sha256(raw).hexdigest()
        with open(LOG_PATH, encoding="utf-8") as fh:
            log = fh.read()
        atts = bump_attestations(log, version, sha)
        self.assertEqual(len(atts), 1, "exactly one bump-attestation over the real log")
        # NON-VACUITY: the same full sha IS carried by more than one entry — the guard's job is
        # to count only the move among them. If only one entry named the sha at all, this row
        # would pass for the wrong reason.
        naming_the_sha = [e.splitlines()[0] for e in _log_entries(log) if sha in e]
        self.assertGreaterEqual(len(naming_the_sha), 2,
                                "the real log is expected to carry the sha in the bump AND in a "
                                "held re-citation — if not, this control is vacuous")

    def test_the_real_log_control_is_not_vacuous_a_wrong_era_source_fails_it(self):
        """THE CAN-FAIL DIRECTION OF THE ERA-PINNED CONTROL (board :2922 A3; REBUILT to fail BY
        CONSTRUCTION, archi board :2982, cites :2836). The method name keeps the legacy `wrong_era`
        wording so the record's three citations of it still resolve; the wrong source is no longer
        an era read off the tree but one CONSTRUCTED here in full.

        BOTH DIRECTIONS ARE CONTROLLED — never the live tree's incidental shape (the family pattern,
        archi :2982). The PASS case is the content-pinned anchor (ATTEST_ANCHOR_VERSION / _SHA) read
        over the real, append-only log — a controlled case in the correct direction. The FAIL case is
        a source built inside this test: a version, a sha, and a build-log fragment shaped so the guard
        legitimately rejects it, so the refusal cannot drift with the on-disk founding.

        WHY THE OLD FAIL CASE HAD TO GO. It read the live founding pack and expected non-vacuity to
        fail because that pack's sha named ONE entry. At the era the row was written that held; the
        on-disk founding has since had its sha named by a second entry, so the live source stopped
        being a wrong one and a can-fail control was resting on the live tree's shape — the defect
        this rebuild removes.

        THE NAMED PROPERTY. The constructed source fails PROPERTY-2 (non-vacuity: its sha is named by
        fewer than two entries). PROPERTY-1 (exactly one bump-attestation) HOLDS over it — that is what
        makes it a genuine wrong source and not a trivially broken input: a well-formed founding move
        the guard rejects for the exact reason the non-vacuity arm exists, a move over which 'exactly
        one attestation' would pass with only one sha-naming entry to count."""
        with open(LOG_PATH, encoding="utf-8") as fh:
            log = fh.read()
        # PASS — the content-pinned anchor over the real log satisfies BOTH properties. This reads
        # the (version, sha) from module constants driven by content (test_the_attest_anchor_era_
        # resolves_by_content), never from the live founding pack.
        anchor_ok = (len(bump_attestations(log, ATTEST_ANCHOR_VERSION, ATTEST_ANCHOR_SHA)) == 1
                     and len([e for e in _log_entries(log) if ATTEST_ANCHOR_SHA in e]) >= 2)
        self.assertTrue(anchor_ok, "the anchor source satisfies both properties over the real log")

        # FAIL — a CONSTRUCTED wrong source, built here in full: a founding that moved ONCE (one
        # well-formed bump-attestation of the move) whose pack sha is re-cited by NO later entry.
        # Nothing below opens the on-disk founding pack; the source is built here in full.
        wrong_v = "5.5.5"
        wrong_sha = "c" * 64
        wrong_log = f"""# GOV-OS — build progress

## EP-XX BUILD — an earlier unit, names no pack — 2026-02-01

The founding stood at 5.5.4 then; this entry names no new pack and moves nothing.

## EP-YY BUILD — THE FOUNDING MOVED and this entry attests it — 2026-02-02

FOUNDING MOVE. founding_version 5.5.4 -> {wrong_v}, class MINOR (a new surface). Pack sha256
{wrong_sha} (version AND hash named together in this one entry).

## EP-ZZ BUILD — a later close that re-cites no pack sha — 2026-02-03

Cleared the reds the move left in settled modules; the founding did not move here and this entry
re-cites no pack sha.
"""
        wrong_atts = bump_attestations(wrong_log, wrong_v, wrong_sha)
        naming_wrong = [e.splitlines()[0] for e in _log_entries(wrong_log) if wrong_sha in e]
        # PROPERTY-1 HOLDS BY CONSTRUCTION — a genuine, single bump-attestation, so the wrong source
        # is a real founding shape and not a trivially broken input.
        self.assertEqual(len(wrong_atts), 1,
                         "property-1 holds by construction — the constructed wrong source is a genuine "
                         "founding move with exactly one bump-attestation, not a broken input")
        self.assertIn("EP-YY", wrong_atts[0], "the one attestation is the genuine bump-claim")
        # PROPERTY-2 FAILS BY CONSTRUCTION — the sha is named by exactly one entry (fewer than two).
        self.assertEqual(len(naming_wrong), 1,
                         "property-2 fails by construction — the sha is named by exactly one entry")
        wrong_ok = (len(wrong_atts) == 1 and len(naming_wrong) >= 2)
        self.assertFalse(wrong_ok,
                         "the constructed wrong source must fail the control — it fails PROPERTY-2 "
                         "(non-vacuity, sha named by >=2 entries): its sha is named by %d entr%s"
                         % (len(naming_wrong), "y" if len(naming_wrong) == 1 else "ies"))
        # MUST-RED: strip PROPERTY-2 (check only 'exactly one attestation') and the wrong source is
        # ACCEPTED — so property-2 is the arm doing the refusing here, and this control is watched
        # refusing something rather than passing vacuously. Were the non-vacuity logic ever vacuous
        # (always ok), wrong_ok would be True and the assertFalse above would red.
        vacuous_ok = (len(wrong_atts) == 1)  # property-1 alone, the non-vacuity arm removed
        self.assertTrue(vacuous_ok,
                        "a guard checking only property-1 would ACCEPT the wrong source — property-2 "
                        "is what refuses it, and a control that could not fail here would be a formality")


# =========================================================================================
# A4 / A5 — THE REFUSAL, AND THE LAWFUL GRANT THAT MUST STILL LAND
# =========================================================================================

class TheGrantNowAsksWhatItIsGrantingOver(unittest.TestCase):
    """A4 and A5, driven against the LIVE founding — the shipped operation, not a scratch."""

    def setUp(self):
        self.f = Founded()
        self.addCleanup(self.f.close)

    def test_a4_a_grant_over_a_region_nobody_created_is_REFUSED_naming_the_law(self):
        verdict, err = self.f.verdict(
            "SHM-GRANT", "browser",
            {"region": "shm:nobody-made-this", "grantees": ["ghost"], "mode": "rw"})
        self.assertEqual(verdict, "REFUSED")
        self.assertEqual(err.rule, LAW)
        self.assertIn("MEM-GRANT", err.message)

    def test_a4_the_law_the_refusal_names_EXISTS_in_the_founding(self):
        """THE WHOLE POINT OF THE LAW HALF. Before this unit the same refusal would have
        cited a rule the pack never created — a refusal with no law behind it."""
        _, err = self.f.verdict("SHM-GRANT", "browser", {"region": "shm:nope"})
        self.assertIn(err.rule, created_rules(live_pack()))

    def test_a5_a_lawful_grant_is_APPENDED_citing_its_law(self):
        self.f.establish("alice")
        self.f.found_region("shm:lawful")
        verdict, rec = self.f.verdict(
            "SHM-GRANT", "browser",
            {"region": "shm:lawful", "grantees": ["alice"], "mode": "rw"})
        self.assertEqual(verdict, "ACCEPTED")
        self.assertEqual(rec["rule_cited"], LAW)
        self.assertEqual(rec["payload"]["region"], "shm:lawful")

    def test_a5_the_granter_is_STAMPED_to_the_acting_actor_even_when_the_caller_supplies_one(self):
        """THE REGRESSION GUARD. Attribution was already sound and this unit must not spend
        it: `granter` is an attribution field stamped to the acting actor, so a caller
        supplying a different one is recorded as itself and not as whom it named."""
        self.f.establish("alice")
        self.f.found_region("shm:lawful")
        verdict, rec = self.f.verdict(
            "SHM-GRANT", "browser",
            {"region": "shm:lawful", "grantees": ["alice"], "mode": "rw", "granter": "mallory"})
        self.assertEqual(verdict, "ACCEPTED")
        self.assertEqual(rec["payload"]["granter"], "browser")
        self.assertEqual(rec["actor"], "browser")

    def test_a5_the_view_still_folds_the_grant(self):
        """The grant's view is READ by this unit and written by no part of it."""
        from subsystems.comms import CommsView
        self.f.establish("alice")
        self.f.found_region("shm:lawful")
        self.f.gate.execute("SHM-GRANT", "browser",
                            {"region": "shm:lawful", "grantees": ["alice"], "mode": "rw"})
        g = CommsView(self.f.store).shm_grants()["shm:lawful"]
        self.assertEqual(g["granter"], "browser")
        self.assertIn("alice", g["grantees"])


# =========================================================================================
# R2 — THE REGION CHECK IS LOAD-BEARING (differential, and it states which way it moves)
# =========================================================================================

class TheRegionCheckIsLoadBearing(unittest.TestCase):
    """R2. A4's verdict must MOVE when the plant is removed. A row whose verdict cannot be
    shown moving is not evidence of the thing it asserts."""

    def test_r2_a4s_refusal_becomes_an_acceptance_with_the_check_REMOVED(self):
        payload = {"region": "shm:nobody-made-this", "grantees": ["ghost"], "mode": "rw"}
        with Founded() as landed:
            self.assertEqual(landed.landed_checks("SHM-GRANT"), ["require_prior", "live_present"])  # +live_present: EP-MAINT-OUTSIDE-4 R10
            with_check, err = landed.verdict("SHM-GRANT", "browser", payload)
        with Founded(pack_with_shm_checks([])) as removed:
            self.assertEqual(removed.landed_checks("SHM-GRANT"), [],
                             "the plant was not actually removed from the FOUNDED record")
            without, _ = removed.verdict("SHM-GRANT", "browser", payload)
        self.assertEqual(with_check, "REFUSED")
        self.assertEqual(err.rule, LAW)
        self.assertEqual(without, "ACCEPTED")


# =========================================================================================
# R1 — THE CARDINALITY GAP, EXHIBITED. ITS EXPECTED VERDICT IS ACCEPTANCE.
# =========================================================================================

class TheCardinalityGapIsExhibited(unittest.TestCase):
    """R1, and it is A3's withdrawal driven rather than asserted.

    WHAT INVERTS THIS ROW: `EP-30-K2` minting a quantified kind AND `EP-30-C4W` wiring this
    operation's grantee question — BOTH, never either alone. A kind that exists and is not
    wired onto this operation leaves the grant still accepting, and a wiring with no kind to
    wire cannot be written. When both land, the first row below goes RED and that is this
    row REPORTING, not regressing.

    THE ROW'S GREEN IS A BOUNDARY AND NOT A PASS.
    """

    def test_r1_a_grant_to_grantees_NONE_of_which_is_established_is_ACCEPTED(self):
        """With every check this unit lands in force. Accepted BECAUSE no kind among the
        vocabulary can ask a many-valued parameter anything."""
        with Founded() as f:
            self.assertEqual(f.landed_checks("SHM-GRANT"), ["require_prior", "live_present"])  # +live_present: EP-MAINT-OUTSIDE-4 R10 (a region-LIVENESS check, not authority/cardinality — the exhibited gap stays open)
            f.found_region("shm:lawful")
            verdict, rec = f.verdict(
                "SHM-GRANT", "browser",
                {"region": "shm:lawful", "grantees": ["ghost-a", "ghost-b"], "mode": "rw"})
        self.assertEqual(verdict, "ACCEPTED",
                         "if this REFUSED, the estate gained a way to ask a many-valued "
                         "parameter a question and this row is reporting it")
        self.assertEqual(list(rec["payload"]["grantees"]), ["ghost-a", "ghost-b"])

    def test_r1_the_WITHDRAWN_spelling_refuses_a_list_of_FULLY_ESTABLISHED_entities(self):
        """THE ROW THAT KILLS THE SPELLING, and the reason A3 is withdrawn rather than built.

        Four ways, with BOTH SCALAR CONTROLS SEPARATING — or the probe is broken rather than
        the check. A LIST OF FULLY ESTABLISHED ENTITIES REFUSED IDENTICALLY TO A LIST OF
        GHOSTS IS THE WHOLE FINDING: the check cannot tell them apart, which is to say it is
        not asking the question. `require_prior` reads the parameter into ONE value and its
        `any(...)` quantifies over RECORDS, never over the parameter's values, so a list is
        compared whole against a scalar field and can never equal one.
        """
        pack = pack_with_shm_checks([WITHDRAWN_GRANTEE_CHECK])
        with Founded(pack) as f:
            # SCRATCH pack (not the live pack) — SHM-GRANT's checks are set to the withdrawn spelling
            # alone (a require_prior variant), so R10's live_present is deliberately absent here.
            self.assertEqual(f.landed_checks("SHM-GRANT"), ["require_prior"])
            f.establish("alice", "bob")
            f.found_region("shm:lawful")
            base = {"region": "shm:lawful", "mode": "rw"}
            scalar_ok, _ = f.verdict("SHM-GRANT", "browser", dict(base, grantees="alice"))
            scalar_no, _ = f.verdict("SHM-GRANT", "browser", dict(base, grantees="ghost"))
            list_ok, _ = f.verdict("SHM-GRANT", "browser", dict(base, grantees=["alice", "bob"]))
            list_no, _ = f.verdict("SHM-GRANT", "browser", dict(base, grantees=["ghost"]))
        self.assertEqual(scalar_ok, "ACCEPTED", "scalar control A did not separate")
        self.assertEqual(scalar_no, "REFUSED", "scalar control B did not separate")
        self.assertEqual(list_ok, "REFUSED",
                         "a list of FULLY ESTABLISHED entities — refused identically to a "
                         "list of ghosts. This is why the row was withdrawn")
        self.assertEqual(list_no, "REFUSED")
        self.assertEqual(list_ok, list_no,
                         "the lawful and the unlawful answered with one message: A CHECK "
                         "THAT CANNOT BE SHOWN ACCEPTING ANYTHING IS NOT A CHECK EITHER")

    def test_r1_no_check_row_in_the_pack_names_a_MANY_VALUED_parameter(self):
        """THE ABSENCE, WITH BOTH CONTROLS, because one would not have been enough.

        CONTROL A proves the sweep works — check rows naming a parameter exist and are found.
        CONTROL B is the one that matters: without it, zero would be consistent with `the
        pack declares no many-valued parameters`, making this a fact about the PACK'S SHAPE.
        With it, the zero is a fact about the CHECK VOCABULARY — many-valued parameters
        exist, have existed since these ops shipped, and not one has ever been asked anything.
        """
        ops = op_definitions(live_pack())
        many_valued = {(n, p) for n, d in ops.items()
                       for p, v in (d.get("param_defaults") or {}).items() if isinstance(v, list)}
        naming_a_param = [(n, c) for n, d in ops.items() for c in (d.get("checks") or [])
                          if c.get("param")]
        self.assertTrue(naming_a_param, "CONTROL A: the sweep found no check row naming a "
                                        "parameter at all — the sweep is broken")
        self.assertTrue(many_valued, "CONTROL B: the pack declares no many-valued parameter, "
                                     "so a zero below would say nothing about the vocabulary")
        asked = [(n, c["param"]) for n, c in naming_a_param
                 if (n, c["param"]) in many_valued]
        self.assertEqual(asked, [], "a check row names a many-valued parameter — the "
                                    "vocabulary gained a quantifier and this row is "
                                    "reporting it")

    def test_r1_the_gap_is_a_property_of_EVERY_kind_and_not_of_one(self):
        """No arm in the vocabulary iterates a parameter. Stated over the whole declared
        vocabulary so the claim is about the SET rather than about the kind this unit used."""
        self.assertIn("require_prior", OP_CHECKS)
        self.assertIn("bound_field", OP_CHECKS,
                      "EP-30-K1's kind is present — and it is scalar on BOTH ends, so it "
                      "does not close this gap either")


# =========================================================================================
# R5 — THE AUTHORITY WALL, EXHIBITED. ITS EXPECTED VERDICT IS ACCEPTANCE.
# =========================================================================================

class TheAuthorityWallIsExhibited(unittest.TestCase):
    """R5. A grant whose granter is a fully established entity that DOES NOT HOLD THE REGION
    is ACCEPTED, because this operation cannot ask it.

    WHAT DOES *NOT* INVERT THIS ROW, and it is stated because the plan's author got it wrong
    and the error reached two plans and a ruling: `EP-30-K1`'s LANDING DOES NOT INVERT IT.
    K1 minted `bound_field` and proved granter-holds against a scratch definition, putting
    `SHM-GRANT`'s declaration in its own MUST-NOT-TOUCH. After K1 the kind EXISTS and THIS
    OPERATION STILL DOES NOT USE IT, so this row stays green and is CORRECT to.

    WHAT DOES INVERT IT: `EP-30-C4W` wiring a `bound_field` granter-holds row onto
    `SHM-GRANT`. That unit repairs THIS ROW AT ITS CAUSE in the same act. So this is a
    SCHEDULED inversion and not an open one.
    """

    def test_r5_a_granter_that_does_not_hold_the_region_is_ACCEPTED(self):
        with Founded() as f:
            self.assertEqual(f.landed_checks("SHM-GRANT"), ["require_prior", "live_present"])  # +live_present: EP-MAINT-OUTSIDE-4 R10 (a region-LIVENESS check, not authority/cardinality — the exhibited gap stays open)
            f.establish("alice", "mallory")
            # alice founds the region; mallory holds nothing at all
            f.gate.execute("MEM-GRANT", "alice", {"region": "shm:alices", "size": 4096})
            verdict, rec = f.verdict(
                "SHM-GRANT", "mallory",
                {"region": "shm:alices", "grantees": ["alice"], "mode": "rw"})
        self.assertEqual(verdict, "ACCEPTED",
                         "if this REFUSED, SHM-GRANT gained an authority check and EP-30-C4W "
                         "has landed — this row is reporting the gap CLOSING, not a defect")
        self.assertEqual(rec["payload"]["granter"], "mallory",
                         "and the record correctly names the party that acted")

    def test_r5_the_operation_declares_no_bound_field_row(self):
        """The mechanical statement of the same boundary, so the row does not depend on a
        driven acceptance alone."""
        shm = op_definitions(live_pack())["SHM-GRANT"]
        # +live_present: EP-MAINT-OUTSIDE-4 R10 (a region-LIVENESS check over MEM-GRANT/MEM-EVICT); the
        # exhibit's claim — no granter-holds authority check — is the assertNotIn below, still true.
        self.assertEqual([c["check"] for c in shm["checks"]], ["require_prior", "live_present"])
        self.assertNotIn("bound_field", [c["check"] for c in shm["checks"]])


# =========================================================================================
# A6 — THE RIDER. A CLAIM ABOUT A POPULATION, WITH R3 PROVING IT CAN FAIL.
# =========================================================================================

#: THE SCHEDULE'S ANCHORS. Each family's scheduled unit, and A PHRASE FROM `design/36` THAT
#: MUST STILL BE THERE. The row does not restate the schedule — it FAILS if the paper stops
#: carrying it, which is what "the schedule data comes from the paper and nowhere else"
#: means mechanically. A rider whose data is restated in the plan that checks it is a claim
#: checking its own copy.
SCHEDULE_ANCHORS = {
    "COMM": ("EP-30-C6", "THE COMMS LAW SCHEDULE SETTLES HERE"),
    "MEM": ("EP-31", "EP-31 — M6: memory."),
    "SCHED": ("EP-32", "EP-32 — M7: scheduling"),
}


def scheduled_unit(law_id):
    """The unit a not-yet-created law is scheduled at, or None. The family is the law id's
    own first token — the pack's own naming and not a list kept here."""
    entry = SCHEDULE_ANCHORS.get(law_id.split("-")[0])
    return entry[0] if entry else None


def unscheduled_danglers(pack):
    """Every op citing a law that is NEITHER created in the pack NOR scheduled at a named
    unit. THE POPULATION IS THE PACK'S OP DEFINITIONS."""
    created = created_rules(pack)
    return sorted((name, d["law_cited"]) for name, d in op_definitions(pack).items()
                  if d.get("law_cited") and d["law_cited"] not in created
                  and scheduled_unit(d["law_cited"]) is None)


class EveryCitedLawIsCreatedOrScheduled(unittest.TestCase):
    """A6 and R3.

    ARCHI'S RIDER: dangling citations that no instrument reds are the scheduled-trap class
    one tier up. The claim is about a POPULATION — every op definition in the pack — and not
    about this operation. `COMM-LAW-SHARE-GRANT` moves out of the dangling set by being
    CREATED here; the four remaining comms laws are the PAPER'S to schedule and this row
    reads that schedule rather than asserting it.
    """

    def test_a6_the_schedule_data_is_STILL_IN_THE_PAPER(self):
        """The row's data lives in `design/36`. If the paper stops carrying a family's
        schedule, this row goes red BEFORE the count below can pass on a stale copy."""
        with open(PAPER_PATH, encoding="utf-8") as fh:
            paper = fh.read()
        for family, (unit, phrase) in SCHEDULE_ANCHORS.items():
            self.assertIn(phrase, paper,
                          "the paper no longer carries %s's schedule (%s) — the rider's "
                          "data is gone and the row must not pass on this file's copy"
                          % (family, unit))

    def test_a6_there_are_ZERO_unscheduled_dangling_citations(self):
        self.assertEqual(unscheduled_danglers(live_pack()), [])

    def test_a6_the_population_is_non_empty_and_danglers_DO_still_exist(self):
        """CONTROL. Zero unscheduled danglers must not be zero because the walk found
        nothing. Ops exist, cited laws exist, and laws cited-and-uncreated STILL EXIST — they
        are merely all scheduled."""
        pack = live_pack()
        ops = op_definitions(pack)
        created = created_rules(pack)
        self.assertGreater(len(ops), 1)
        dangling = [(n, d["law_cited"]) for n, d in ops.items()
                    if d.get("law_cited") and d["law_cited"] not in created]
        self.assertTrue(dangling, "no cited-and-uncreated law remains, so a zero above would "
                                  "say nothing about the schedule")
        self.assertTrue(all(scheduled_unit(law) for _, law in dangling))

    def test_a6_this_units_own_law_LEFT_the_dangling_set(self):
        era = era_pin.pack_at(PRE_EDIT_COMMIT, missing="assert")
        self.assertNotIn(LAW, created_rules(era))
        self.assertIn(LAW, created_rules(live_pack()))

    def test_r3_the_rider_REDS_on_a_planted_coined_law_and_NAMES_it(self):
        """R3. A CHECK THAT HAS NEVER BEEN SHOWN REFUSING ANYTHING IS NOT A CHECK — this
        estate's signature defect, and A6 is exactly the shape that carries it. Plant an op
        citing a law that is neither created nor scheduled; remove it; the verdict moves."""
        planted = copy.deepcopy(live_pack())
        step = planted["steps"][-1]
        step["records"].append({
            "actor": "PC_RUNTIME", "action": "CREATE-OP", "object": "op:PLANTED-DANGLER",
            "rule_cited": "CAP-IS-LAW",
            "payload": {"kind": "op_definition", "rule_id": "op:PLANTED-DANGLER",
                        "polarity": "+", "name": "PLANTED-DANGLER",
                        "definition": {"description": "plant", "params": {"x": "required"},
                                       "law_cited": "ZZZ-LAW-NOBODY-COINED",
                                       "object_param": "x", "payload_from": ["x"],
                                       "checks": []},
                        "tier": "owner", "text": "plant"}})
        found = unscheduled_danglers(planted)
        self.assertEqual(found, [("PLANTED-DANGLER", "ZZZ-LAW-NOBODY-COINED")],
                         "the rider did not name the planted citation")
        self.assertEqual(unscheduled_danglers(live_pack()), [],
                         "and with the plant removed it is green again — the verdict moves")


if __name__ == "__main__":
    unittest.main()
