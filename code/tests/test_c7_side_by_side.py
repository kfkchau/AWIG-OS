# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-verification · machine register.
# Vocabulary is OS-architecture: the SAME scripted stretch of ordinary governed acts (create an actor, grant,
# decide, append — build_full_kernel + the gate) run under TWO performers, the Linux carrier and gov-os's own
# freestanding core, and the two records compared by the estate's CANONICAL digest over their rows — EQUAL when
# the stretch agrees, a planted CONTENT divergence reddening. The comparison is over the canonical record
# CONTENT, never the raw bytes (the performers differ in incidental bytes). NON-GOAL: no offensive capability;
# this RUNS ordinary acts and COMPARES records. It changes no core (no src/kernel, no src/body, no founding);
# the switch of the real record onto the core is NOT taken here (the owner's one-way word, named once at the
# digest). Full declaration: SCOPE-STATEMENT.md.
"""C7 SIDE-BY-SIDE — the same governed acts on both performers, records compared by the canonical digest.

Plan: planning/exec/C7-SIDE-BY-SIDE.md (sha f55f4004…); the :4487 ruling + DIGEST-C7 §5/§6 rider 3 (:4634).

THREE ROLES, ONE MODULE (the C7 P8 one-module-on-both-performers form, reused not re-authored):
  * `TestBodyStretch` RUNS the scripted stretch and EMITS the canonical result as `SBS-…` markers on stdout
    (the body's serial line under LEDGER mode). It runs on BOTH performers unchanged: on the Linux carrier
    as an ordinary unittest, and on gov-os's own core when the body-hosted interpreter runs it via LEDGER
    mode (GOVOS_RUNMOD=test_c7_side_by_side.TestBodyStretch). The same code -> the same act set by
    construction (A1) -> the same canonical record content when the performers agree (A2).
  * `TestBodyStretchPlanted` is the SAME stretch with ONE REAL CONTENT DIVERGENCE planted (a differing
    object in one round) — the runmod for the body's plant boot; it asserts, on whichever performer runs
    it, that the plant REDS against a clean run in the same process while an incidental-only difference
    (the three per-run timestamps) STILL AGREES (A3, both arms, L19).
  * `TestCanonicalMeasure` + `TestSideBySideEvidence` are the HOST-side acceptance: the measure's plants on
    real in-process runs, the raw-bytes anti-measure NAMED and shown to be a check that always reds (stop b),
    N and its basis within the body's cap (A4), and — reading the evidence the tools/sidebyside drivers
    produce, SKIPPING where absent so it never reds on the body — the cross-performer equality, the
    identical act sets, the on-body plant reddening, determinism across runs, and A5 (no core move).

THE MEASURE (the crux, the plan's landmine class): `stretch_digest(rows)` = the estate's ONE canonical
serializer (src/kernel/canonical.canonical_hash — used, never changed) over the ORDERED list of PROJECTED
rows, where a projected row is the record row minus a CLOSED, NAMED, MEASURED set of per-run fields:
    record_time / submission_time / occurrence_time  — the recording clock, per run (two Linux runs of the
                                                        identical stretch differ in EXACTLY these three and
                                                        nothing else — measured, planning/evidence)
    seq                                               — ORDER, not state (canonical.py's ruling); the row's
                                                        POSITION is still covered, because the digest is over
                                                        the ORDERED list — a reordered record reds
Everything else (actor, action, object, target, rule_cited, payload, provenance, refs, content_form,
record_id, origin, evidence_summary) is CONTENT and enters the digest. `RAW_BYTES_ANTI_MEASURE` names the
measure this module refuses: sha256 over the raw record file — two agreeing runs already differ in it
(timestamps), so it is a check that can only red (stop b) and is shown redding on agreeing content below,
never used for the verdict.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Mapping

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from bridge import host_seam, merkle, replay_snapshot                       # noqa: E402
from bridge.host_seam import using, ACT_KINDS                              # noqa: E402
from kernel.canonical import canonical_hash, strip_derivation              # noqa: E402
from kernel.compose import build_full_kernel                               # noqa: E402
from kernel.errors import OpError                                          # noqa: E402
from kernel.protection import can_read                                     # noqa: E402
from test_c7_p8_numbers import (ActRecorder, check_identical_act_sets,     # noqa: E402
                                machine_basis, performer)


# ---------------------------------------------------------------------------------------------------
# THE STRETCH — a bounded N of ordinary governed acts, scripted, REFUSAL-FREE by construction.
# ---------------------------------------------------------------------------------------------------
ROUNDS = 100
FILE_TREE = (("a.txt", "hello world"), ("c.txt", "second file"), ("e.txt", "third here"))
ACTS_PER_ROUND = 4                       # create an actor, grant (sight), decide (a consume under the grant), append
N_ACTS = ROUNDS * ACTS_PER_ROUND + len(FILE_TREE) * 2      # 406 governed acts through the gate
PLANT_ROUND = 42                         # the round whose object diverges under plant="content"
PLANT_SUFFIX = "-DIVERGENT"

# The body's measured caps (C7 P8 caps.json, :4626 / :4629) — PINNED here and CHECKED against the source
# constants on the host (TestCanonicalMeasure.test_A4_...). The stretch must sit within both.
BODY_CAP_DIR_ENTRIES = 2048              # src/body/disk.h BFS_MAX_ENTRIES = BFS_DIR_SECTORS(1024) * 2
BODY_CAP_RECORD_BYTES = 8 * 1024 * 1024  # src/body/mkdisk.py RECORD_CAPACITY_SECTORS(16384) * 512

# THE CLOSED EXCLUSION LIST — measured, not guessed (see the module docstring).
PER_RUN_FIELDS = ("record_time", "submission_time", "occurrence_time")
ORDER_FIELDS = ("seq",)
EXCLUDED_FIELDS = PER_RUN_FIELDS + ORDER_FIELDS

RAW_BYTES_ANTI_MEASURE = ("sha256 over the raw record file bytes — REFUSED as the verdict: the two performers "
                          "(and two runs of one performer) differ in incidental bytes (the recording clock), so "
                          "a raw compare can only red — a check that cannot pass is not a check (stop b, L19)")

STRETCH_BASIS = {
    "rounds": ROUNDS,
    "acts_per_round": ["CREATE-ACTOR owner", "GRANT-READ owner->actor (sight)", "CONSUME actor (the decide "
                       "that depends on the grant fold)", "WRITE-ACTIVITY owner (an append)"],
    "file_tree_acts": "FILE-CREATE + FILE-WRITE for each of %d fixed files (the checkpoint tree-state is non-empty)"
                      % len(FILE_TREE),
    "n_acts": N_ACTS,
    "refusal_free": "every act is permitted by construction (owner is the founding root; each CONSUME follows "
                    "its own GRANT-READ); a refusal would spawn two `op-refused` dual-audit mirror rows, so the "
                    "stretch is cut refusal-free and asserts no op-refused row exists",
    "mirror_rows": "GRANT-READ is in the `dual-audit-actions` pack, so each grant carries two SYSTEM mirror rows "
                   "(dual-audit-record / dual-audit-b-record) — deterministic, part of the compared content",
    "cap_basis": "the body's measured caps: %d directory entries / %d-byte fixed record (C7 P8 caps.json); the "
                 "stretch's record is measured per run and asserted under the cap" % (
                     BODY_CAP_DIR_ENTRIES, BODY_CAP_RECORD_BYTES),
}


def stretch_acts(plant=None):
    """The scripted stretch as (op, actor, params) triples — DETERMINISTIC, the same on both performers.
    `plant="content"` diverges ONE round's object (a real content difference: the grant's target, the
    consume's object, and the two mirror rows' digests all change)."""
    for i in range(ROUNDS):
        actor = "sbs-actor-%03d" % i
        doc = "sbs-doc-%03d" % i
        if plant == "content" and i == PLANT_ROUND:
            doc = doc + PLANT_SUFFIX
        yield ("CREATE-ACTOR", "owner", {"actor_id": actor})
        yield ("GRANT-READ", "owner", {"grantee": actor, "target": doc})
        yield ("CONSUME", actor, {"target": doc})
        yield ("WRITE-ACTIVITY", "owner", {"about": actor, "data": {"round": i, "note": "side-by-side"}})
    for name, body in FILE_TREE:
        yield ("FILE-CREATE", "owner", {"path": "/" + name})
        yield ("FILE-WRITE", "owner", {"path": "/" + name, "content": body})


def _thaw(v):
    """Deep-copy a frozen record (mapping proxies / tuples, store._freeze) into plain dict/list — the
    canonical serializer already treats those as ONE state; this is for JSON emission only."""
    if isinstance(v, Mapping):
        return {k: _thaw(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_thaw(x) for x in v]
    return v


def project_row(row):
    """The canonical CONTENT of one record row: every field but the closed excluded set."""
    return {k: _thaw(v) for k, v in row.items() if k not in EXCLUDED_FIELDS}


def row_digest(projected):
    return canonical_hash(projected)


def stretch_digest(projected_rows):
    """THE MEASURE: the estate's canonical hash over the ORDERED list of projected rows."""
    return canonical_hash(list(projected_rows))


def divergent_rows(digests_a, digests_b):
    """Localise a divergence: the row positions whose digests differ (plus any length difference)."""
    n = min(len(digests_a), len(digests_b))
    out = [i for i in range(n) if digests_a[i] != digests_b[i]]
    if len(digests_a) != len(digests_b):
        out.append("length %d != %d" % (len(digests_a), len(digests_b)))
    return out


def check_records_agree(result_a, result_b):
    """The agreement verdict between two stretch results: True iff their canonical stretch digests are
    EQUAL. A real content divergence on either side reds it; incidental per-run bytes cannot."""
    return result_a["stretch_digest"] == result_b["stretch_digest"]


def _sight_view(store, views):
    """A COMPUTED VIEW over the stretch: for every round's actor, can it read its round's CANONICAL doc
    (the un-planted name)? Derived from the recorded grants (protection.can_read) — the same question asked
    on both performers; a planted grant target flips one answer, so this view can red too."""
    end = views.chain_end()
    return {"sbs-actor-%03d" % i: can_read(store, "sbs-actor-%03d" % i, "sbs-doc-%03d" % i, end)
            for i in range(ROUNDS)}


def run_stretch(plant=None, label=None, keep_rows=True):
    """Run the stretch in a FRESH governed world beneath an ActRecorder (A1's manifest) and return the
    canonical result: projected rows, per-row digests, the stretch digest, the checkpoint tree-state
    digest (merkle root), a computed-views digest, the act manifest, the raw-bytes figures (for the
    anti-measure demonstration ONLY), N and its basis.

    `keep_rows=False` drops the big per-row lists (`rows`, `raw_rows`, `row_digests`) from the returned
    dict AFTER their digests are computed — the scalars and the stretch/tree/views digests are kept. On
    the body (256 MiB PMM cap) two full row-sets held at once during the heavy 839-row serial emit
    exhaust memory and the boot never halts; a lean control run leaves peak memory at one row-set (the
    shape the agree boot proved works). The digests are computed the same way either way, so a lean run
    and a kept run of the same stretch produce the SAME stretch_digest — the equality is unaffected."""
    d = tempfile.mkdtemp(prefix="sbs-")
    rec = os.path.join(d, "record.jsonl")
    bd = os.path.join(d, "blobs")
    recorder = ActRecorder(host_seam.host())
    refused = []
    with using(recorder):
        store, gate, views, blobs, subs = build_full_kernel(rec, bd, os.path.join(d, "vault"))
        genesis_rows = len(store.all())
        n_acts = 0
        for op, actor, params in stretch_acts(plant):
            try:
                gate.execute(op, actor, params)
            except OpError as exc:                                  # a refusal is a finding, never hidden
                refused.append((op, actor, repr(exc)))
            n_acts += 1
        rows = [_thaw(r) for r in store.all()]
        tree = replay_snapshot.snapshot(rec, bd, root="/")
        tree_root = merkle.merkle_root(tree)
        views_digest = canonical_hash(strip_derivation({
            "active_rules": _thaw(views.active_rules()),
            "chain_end": views.chain_end(),
            "grants": _thaw(views.grants()),
            "sight": _sight_view(store, views),
        }))
        with open(rec, "rb") as f:                                  # the RAW bytes — anti-measure only
            raw = f.read()
    projected = [project_row(r) for r in rows]
    digests = [row_digest(p) for p in projected]
    result = {
        "performer": performer(),
        "plant": plant,
        "label": label,
        "n_acts": n_acts,
        "genesis_rows": genesis_rows,
        "n_rows": len(rows),
        "stretch_rows": len(rows) - genesis_rows,
        "refused": refused,
        "op_refused_rows": sum(1 for r in rows if r.get("action") == "op-refused"),
        "stretch_digest": stretch_digest(projected),
        "row_digests": digests,
        "rows": projected,
        "raw_rows": rows,                    # UNPROJECTED, in-process only (never emitted): the plants' input
        "tree_root": tree_root,
        "tree_leaves": len(tree),
        "views_digest": views_digest,
        "manifest": sorted(recorder.kinds),
        "record_bytes": len(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "blob_contents": len({b for _, b in FILE_TREE}),
        "excluded_fields": list(EXCLUDED_FIELDS),
        "basis": dict(machine_basis(), **STRETCH_BASIS),
    }
    if not keep_rows:
        for k in ("rows", "raw_rows", "row_digests"):
            result.pop(k, None)
    return result


def emit(tag, obj):
    """One single-line marker for the body serial / the host capturer to parse (the P8 `emit` shape)."""
    sys.stdout.write(tag + " " + json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def emit_result(result, with_rows):
    """SBS-BEGIN, then (optionally) one SBS-ROW line per projected row `<i> <digest> <json>`, then
    SBS-RESULT carrying everything but the rows (the host re-digests the transferred rows to the on-body
    digest — a transfer-integrity check that can fail)."""
    emit("SBS-BEGIN", {"performer": result["performer"], "plant": result["plant"], "label": result["label"],
                       "n_rows": result["n_rows"], "with_rows": bool(with_rows)})
    if with_rows:
        for i, (dg, p) in enumerate(zip(result["row_digests"], result["rows"])):
            sys.stdout.write("SBS-ROW %d %s %s\n" % (i, dg, json.dumps(p, sort_keys=True, separators=(",", ":"))))
        sys.stdout.flush()
    slim = {k: v for k, v in result.items() if k not in ("rows", "row_digests", "raw_rows")}
    emit("SBS-RESULT", slim)


def parse_markers(text):
    """Parse SBS markers out of a serial/stdout capture (the marker may sit mid-line after unittest's
    'test_x ... ' prefix). Returns the list of results in emission order, each with its rows/digests
    re-attached from the SBS-ROW lines that preceded its SBS-RESULT."""
    results = []
    rows, digests = [], []
    for line in text.splitlines():
        for tag in ("SBS-BEGIN ", "SBS-ROW ", "SBS-RESULT "):
            idx = line.find(tag)
            if idx < 0:
                continue
            payload = line[idx + len(tag):].strip()
            if tag == "SBS-BEGIN ":
                rows, digests = [], []
            elif tag == "SBS-ROW ":
                i, dg, js = payload.split(" ", 2)
                rows.append(json.loads(js))
                digests.append(dg)
            else:
                res = json.loads(payload)
                res["rows"] = rows
                res["row_digests"] = digests
                results.append(res)
            break
    return results


def _body_caps_from_source(src_dir):
    """Drive the two cap constants from the body's own source (the P8 run_caps idiom)."""
    with open(os.path.join(src_dir, "body", "disk.h")) as f:
        disk_h = f.read()
    with open(os.path.join(src_dir, "body", "mkdisk.py")) as f:
        mkdisk = f.read()
    sectors = int(re.search(r"BFS_DIR_SECTORS\s+(\d+)", disk_h).group(1))
    per = 2                                                      # ENTRY_SIZE 256 -> 2 entries / sector
    entries = sectors * per
    rec_sectors = int(re.search(r"RECORD_CAPACITY_SECTORS\s*=\s*(\d+)", mkdisk).group(1))
    return entries, rec_sectors * 512


# ---------------------------------------------------------------------------------------------------
class TestBodyStretch(unittest.TestCase):
    """THE AGREEING RUN — the runmod the body boots (GOVOS_RUNMOD=test_c7_side_by_side.TestBodyStretch);
    runs unchanged on the Linux carrier. Runs the stretch TWICE in fresh worlds: emits the first with its
    rows, the second digest-only, and asserts the two agree (determinism across runs, on THIS performer)."""

    def test_stretch_runs_and_agrees_with_itself(self):
        a = run_stretch(label="agree")
        emit_result(a, with_rows=True)
        b = run_stretch(label="agree-rerun", keep_rows=False)   # lean: only b's digests are used below
        emit_result(b, with_rows=False)
        self.assertEqual(a["n_acts"], N_ACTS, "the stretch is exactly N_ACTS governed acts")
        self.assertEqual(a["refused"], [], "the stretch is refusal-free by construction: %r" % (a["refused"],))
        self.assertEqual(a["op_refused_rows"], 0, "no op-refused row (and so no refusal mirror rows)")
        self.assertLess(a["record_bytes"], BODY_CAP_RECORD_BYTES, "the record sits within the body's 8 MiB cap")
        self.assertEqual(a["stretch_digest"], stretch_digest(a["rows"]), "the digest re-derives from the rows")
        self.assertTrue(check_records_agree(a, b), "two runs of the same stretch agree by the canonical digest")
        self.assertEqual(a["tree_root"], b["tree_root"], "the checkpoint tree-state digest agrees")
        self.assertEqual(a["views_digest"], b["views_digest"], "the computed views agree")
        self.assertTrue(check_identical_act_sets(a["manifest"], b["manifest"]), "identical act sets (A1)")
        self.assertNotEqual(a["raw_sha256"], b["raw_sha256"],
                            "the RAW bytes of two agreeing runs differ (the clock) — the anti-measure")


class TestBodyStretchPlanted(unittest.TestCase):
    """THE PLANT BOOT — a REAL content divergence (one round's object) planted on THIS performer, shown
    redding against a clean run in the same process; and the incidental arm: the clean rows with their
    three per-run timestamps rewritten STILL agree. Both arms on whichever performer runs it (L19)."""

    def test_planted_content_divergence_reds_and_incidental_still_agrees(self):
        # MEMORY-LEAN ON THE BODY (256 MiB PMM cap): hold ONE full row-set at peak — the shape the agree
        # boot proved works. The clean CONTROL is a lean run (its rows are freed; only its digests survive);
        # the planted run is the one full result, emitted with rows for the host's cross-performer compare.
        clean = run_stretch(label="clean-in-plant-boot", keep_rows=False)
        emit_result(clean, with_rows=False)
        planted = run_stretch(plant="content", label="plant-content")
        emit_result(planted, with_rows=True)
        self.assertEqual(planted["n_acts"], N_ACTS)
        self.assertEqual(planted["refused"], [], "the planted stretch is still refusal-free")
        # A3 arm 1 — a real CONTENT divergence REDS (planted digest != the clean control's digest).
        self.assertFalse(check_records_agree(clean, planted), "a real content divergence REDS (A3)")
        self.assertNotEqual(clean["views_digest"], planted["views_digest"],
                            "the computed sight view reds too (the planted grant covers a different object)")
        divergent_name = "sbs-doc-%03d%s" % (PLANT_ROUND, PLANT_SUFFIX)
        planted_objects = [r["object"] for r in planted["rows"]]
        self.assertIn(divergent_name, planted_objects, "the planted object (a content change) is on the record")
        self.assertNotIn("sbs-doc-%03d" % PLANT_ROUND, planted_objects,
                         "the un-planted name is absent at the planted round (the object really diverged)")
        # A3 arm 2 — an INCIDENTAL (per-run-field-only) difference on the PLANTED run's own rows STILL
        # agrees with itself: rewrite every excluded field to a fixed value, re-project, digest unchanged.
        incidental = [dict(r) for r in planted["raw_rows"]]
        for r in incidental:
            for k in PER_RUN_FIELDS:
                r[k] = "1999-01-01T00:00:00.000000+00:00"
        self.assertNotEqual([r["record_time"] for r in incidental], [r["record_time"] for r in planted["raw_rows"]],
                            "the incidental mutation is real (the clock values changed)")
        self.assertEqual(stretch_digest([project_row(r) for r in incidental]), planted["stretch_digest"],
                         "an incidental (timestamp-only) difference STILL agrees (A3, the other arm)")


# ---------------------------------------------------------------------------------------------------
class TestCanonicalMeasure(unittest.TestCase):
    """HOST-side: the measure's plants on REAL runs and on planted-bad data — a check that can fail EITHER
    way — plus the raw-bytes anti-measure named and shown redding on agreeing content, and A4."""

    @classmethod
    def setUpClass(cls):
        cls.a = run_stretch(label="measure-a")
        cls.b = run_stretch(label="measure-b")
        cls.p = run_stretch(plant="content", label="measure-plant")

    def test_A2_equal_on_agreement_and_the_exclusion_list_is_exactly_what_differs(self):
        self.assertTrue(check_records_agree(self.a, self.b))
        self.assertEqual(self.a["tree_root"], self.b["tree_root"])
        self.assertEqual(self.a["views_digest"], self.b["views_digest"])
        # THE EXCLUSION LIST IS MEASURED: two unprojected runs differ in EXACTLY the per-run fields.
        ra, rb = self.a["raw_rows"], self.b["raw_rows"]
        self.assertEqual(len(ra), len(rb))
        differing = set()
        for x, y in zip(ra, rb):
            for k in set(x) | set(y):
                if x.get(k) != y.get(k):
                    differing.add(k)
        self.assertEqual(differing, set(PER_RUN_FIELDS),
                         "two runs differ in exactly the named per-run fields (the closed exclusion list)")

    def test_A2_raw_bytes_anti_measure_named_and_shown_to_always_red(self):
        self.assertIn("REFUSED", RAW_BYTES_ANTI_MEASURE)
        # two AGREEING runs: canonical digests equal, raw bytes NOT equal -> a raw compare reds on agreement.
        self.assertTrue(check_records_agree(self.a, self.b))
        self.assertNotEqual(self.a["raw_sha256"], self.b["raw_sha256"],
                            "the raw record bytes of two agreeing runs differ — a raw compare can only red")

    def test_A3_incidental_timestamp_difference_still_agrees(self):
        # PLANT (incidental): every per-run field rewritten on one side -> the measure STILL agrees.
        ra = self.a["raw_rows"]
        mutated = []
        for r in ra:
            r = dict(r)
            for k in PER_RUN_FIELDS:
                r[k] = "1999-01-01T00:00:00.000000+00:00"
            mutated.append(r)
        self.assertNotEqual([r["record_time"] for r in ra], [r["record_time"] for r in mutated])
        self.assertEqual(stretch_digest([project_row(r) for r in mutated]), self.a["stretch_digest"],
                         "an incidental (timestamp-only) difference must STILL agree")

    def test_A3_real_content_divergence_reds_on_a_real_run(self):
        self.assertFalse(check_records_agree(self.a, self.p), "a planted content divergence REDS")
        div = divergent_rows(self.a["row_digests"], self.p["row_digests"])
        self.assertEqual(len(div), 4, "localised to the planted round's four rows: %r" % (div,))
        self.assertTrue(all(self.a["rows"][i]["action"] in
                            ("GRANT-READ", "dual-audit-record", "dual-audit-b-record", "CONSUME") for i in div))
        self.assertNotEqual(self.a["views_digest"], self.p["views_digest"], "the computed sight view reds too")
        # the plant is NOT reachable by an incidental field: its object differs, which is content
        self.assertEqual(self.p["rows"][div[0]]["object"], "sbs-doc-%03d%s" % (PLANT_ROUND, PLANT_SUFFIX))

    def test_A3_pure_row_mutations_each_red(self):
        # PLANT (content, pure): one row's actor / object / payload / rule_cited / position -> each reds.
        rows = self.a["rows"]
        base = self.a["stretch_digest"]
        k = self.a["genesis_rows"] + 5                       # a stretch row
        for field, value in (("actor", "someone-else"), ("object", "another-object"),
                             ("rule_cited", "OTHER-RULE"), ("payload", {"planted": True})):
            m = [dict(r) for r in rows]
            m[k][field] = value
            self.assertNotEqual(stretch_digest(m), base, "a differing %s must red" % field)
        reordered = list(rows)
        reordered[k], reordered[k + 1] = reordered[k + 1], reordered[k]
        self.assertNotEqual(stretch_digest(reordered), base, "a reordered record reds (order is covered)")
        self.assertNotEqual(stretch_digest(rows[:-1]), base, "a missing row reds")

    def test_A1_identical_act_sets_real_and_a_real_extra_act_reds(self):
        self.assertTrue(check_identical_act_sets(self.a["manifest"], self.b["manifest"]))
        self.assertTrue(check_identical_act_sets(self.a["manifest"], self.p["manifest"]),
                        "a content plant changes no act KIND — the act set stays identical")
        # PLANT (A1): a stretch that crosses an EXTRA act kind on one performer -> the sets differ (reds).
        recorder = ActRecorder(host_seam.host())
        with using(recorder):
            host_seam.host().urandom(8)                       # a REAL crossing the stretch never makes
        extra = sorted(set(self.a["manifest"]) | recorder.kinds)
        self.assertIn("entropy", recorder.kinds)
        self.assertFalse(check_identical_act_sets(self.a["manifest"], extra), "an extra act kind REDS (A1)")
        self.assertNotIn("entropy", self.a["manifest"], "the stretch itself crosses no entropy act")

    def test_A4_N_stated_within_the_body_cap_and_the_cap_pins_match_the_source(self):
        src = os.path.join(os.path.dirname(__file__), "..", "src")
        entries, rec_bytes = _body_caps_from_source(src)
        self.assertEqual(entries, BODY_CAP_DIR_ENTRIES)
        self.assertEqual(rec_bytes, BODY_CAP_RECORD_BYTES)
        self.assertEqual(self.a["n_acts"], N_ACTS)
        self.assertEqual(N_ACTS, 406)
        self.assertLess(self.a["record_bytes"], BODY_CAP_RECORD_BYTES, "the whole record sits under 8 MiB")
        self.assertLess(self.a["record_bytes"] * 4, BODY_CAP_RECORD_BYTES, "with 4x headroom")
        # directory entries the stretch creates: the record + its lock + the distinct blob contents (each
        # a write-once file) + the vault dir + the tmp dir — two orders of magnitude under 2048
        entries_used = 2 + self.a["blob_contents"] + 2
        self.assertLess(entries_used * 20, BODY_CAP_DIR_ENTRIES)
        # PLANT: an N beyond the cap is refused by the SAME arithmetic (a bound that can fail)
        per_act_bytes = (self.a["record_bytes"]) / float(self.a["n_rows"])
        too_many = int(BODY_CAP_RECORD_BYTES / per_act_bytes) + 1
        self.assertGreater(too_many * per_act_bytes, BODY_CAP_RECORD_BYTES)
        self.assertGreater(too_many, self.a["n_rows"])

    def test_the_stretch_is_refusal_free_and_carries_its_basis(self):
        self.assertEqual(self.a["refused"], [])
        self.assertEqual(self.a["op_refused_rows"], 0)
        self.assertEqual(self.a["basis"]["n_acts"], N_ACTS)
        self.assertIn("refusal_free", self.a["basis"])
        self.assertTrue(self.a["basis"].get("performer") and self.a["basis"].get("machine"))


# ---------------------------------------------------------------------------------------------------
EVID = os.path.join(os.path.dirname(__file__), "..", "planning", "evidence", "C7-SIDE-BY-SIDE")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class TestSideBySideEvidence(unittest.TestCase):
    """The cross-performer acceptance, read from the evidence tools/sidebyside produces (SKIPS when absent
    so it never reds on the body, whose runmod is the stretch alone)."""

    def _need(self, *parts):
        p = os.path.join(EVID, *parts)
        if not os.path.exists(p):
            self.skipTest("SKIP BODY-BOOT: evidence not built yet: %s (run tools/sidebyside first)" % p)
        return _load(p)

    def test_A2_the_two_records_agree_over_the_stretch_by_the_canonical_digest(self):
        lin = self._need("linux", "run-1.json")
        bod = self._need("body", "agree.json")
        self.assertEqual(lin["performer"], "linux")
        self.assertEqual(bod["performer"], "body")
        self.assertTrue(check_records_agree(lin, bod), "Linux and the body AGREE by the canonical digest:\n"
                        "linux %s\nbody  %s\ndivergent rows %r" % (lin["stretch_digest"], bod["stretch_digest"],
                                                                     divergent_rows(lin["row_digests"],
                                                                                    bod["row_digests"])))
        self.assertEqual(lin["tree_root"], bod["tree_root"], "the checkpoint tree-state digest agrees")
        self.assertEqual(lin["views_digest"], bod["views_digest"], "the computed views agree")
        self.assertEqual(lin["n_rows"], bod["n_rows"])
        self.assertEqual(lin["n_acts"], bod["n_acts"])
        self.assertEqual(bod["n_acts"], N_ACTS)
        # the raw bytes DIFFER between the performers while the canonical content is equal (the anti-measure)
        self.assertNotEqual(lin["raw_sha256"], bod["raw_sha256"],
                            "the two performers' raw record bytes differ (incidental) — the measure is canonical")

    def test_A2_transfer_integrity_the_body_rows_redigest_to_the_on_body_digest(self):
        bod = self._need("body", "agree.json")
        self.assertEqual(len(bod["rows"]), bod["n_rows"], "every row crossed the serial")
        self.assertEqual([row_digest(r) for r in bod["rows"]], bod["row_digests"], "per-row digests re-derive")
        self.assertEqual(stretch_digest(bod["rows"]), bod["stretch_digest"],
                         "the transferred rows re-digest, on the host, to the digest computed ON THE BODY")

    def test_A1_identical_act_sets_across_performers(self):
        lin = self._need("linux", "run-1.json")
        bod = self._need("body", "agree.json")
        self.assertTrue(check_identical_act_sets(lin["manifest"], bod["manifest"]),
                        "identical act sets: linux=%r body=%r" % (lin["manifest"], bod["manifest"]))
        self.assertNotIn("entropy", bod["manifest"])

    def test_A3_the_planted_divergence_on_the_body_reds_against_linux(self):
        lin = self._need("linux", "run-1.json")
        pl = self._need("body", "plant-content.json")
        self.assertEqual(pl["performer"], "body")
        self.assertEqual(pl["plant"], "content")
        self.assertFalse(check_records_agree(lin, pl), "the body's planted content divergence REDS against Linux")
        div = divergent_rows(lin["row_digests"], pl["row_digests"])
        self.assertEqual(len(div), 4, "localised to the planted round's rows: %r" % (div,))
        self.assertEqual(pl["rows"][div[0]]["object"], "sbs-doc-%03d%s" % (PLANT_ROUND, PLANT_SUFFIX))
        # and the same body boot's CLEAN run agreed with Linux (the plant boot's own control)
        ctl = self._need("body", "plant-boot-clean.json")
        self.assertTrue(check_records_agree(lin, ctl), "the plant boot's clean control agrees with Linux")

    def test_determinism_across_runs_on_both_performers(self):
        lin1 = self._need("linux", "run-1.json")
        lin2 = self._need("linux", "run-2.json")
        bod = self._need("body", "agree.json")
        rerun = self._need("body", "agree-rerun.json")
        ctl = self._need("body", "plant-boot-clean.json")
        self.assertTrue(check_records_agree(lin1, lin2), "Linux: two runs agree")
        self.assertTrue(check_records_agree(bod, rerun), "body: two runs in one boot agree")
        self.assertTrue(check_records_agree(bod, ctl), "body: two BOOTS agree")
        self.assertNotEqual(lin1["raw_sha256"], lin2["raw_sha256"])

    def test_A4_N_and_its_basis_are_stated_in_evidence_within_the_cap(self):
        st = self._need("STRETCH.json")
        bod = self._need("body", "agree.json")
        self.assertEqual(st["n_acts"], N_ACTS)
        self.assertEqual(st["body_cap"]["directory_entries_max"], BODY_CAP_DIR_ENTRIES)
        self.assertEqual(st["body_cap"]["fixed_record_bytes"], BODY_CAP_RECORD_BYTES)
        self.assertLess(bod["record_bytes"], BODY_CAP_RECORD_BYTES, "the body's measured record is under the cap")
        self.assertIn("refusal_free", st["basis"])

    def test_A5_the_switch_is_not_taken_and_no_core_moved(self):
        self.assertEqual(len(ACT_KINDS), 12, "ACT_KINDS stays 12 (A5)")
        from kernel.attestation import ATTESTED_MEMBERS
        self.assertEqual(len(ATTESTED_MEMBERS), 88, "ATTESTED stays 88 (A5)")
        from founding import install
        self.assertEqual(install.founding_version(), "1.55.0", "no founding move (A5)")
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        try:
            out = subprocess.run(["git", "-C", root, "diff", "--stat", "--", "src/kernel", "src/body", "src/founding"],
                                 capture_output=True, text=True, timeout=30)
        except Exception:                                            # noqa: BLE001
            self.skipTest("SKIP RENDER-NO-GIT: git unavailable")
        self.assertEqual(out.stdout.strip(), "", "no working-tree change under src/kernel, src/body, src/founding")
        # the unit RUNS and REPORTS only: no artifact in its fence names the switch as taken
        rep = self._need("AGREEMENT-REPORT.json")
        self.assertEqual(rep.get("switch_taken"), False, "the switch of the real record onto the core is NOT taken")


if __name__ == "__main__":
    unittest.main(verbosity=2)
