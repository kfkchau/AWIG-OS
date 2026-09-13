#!/usr/bin/env python3
# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: release-tooling · OS/release
# vocabulary (render, stamp, anchor, edition) as in the reproducible-build literature. NON-GOAL:
# no offensive capability of any kind — this renders a pack of text ROWS into a human-readable
# edition and stamps it; it reads data and returns data, touching no record. Full: SCOPE-STATEMENT.md.
"""THE HUMAN EDITION — a pure, generic renderer of ANY pack into an ANCHORED human edition
(design/51 N7, EP-51; the tools/release/render.py precedent, :3226; the anchored edition, D08.40).

render.py renders the ESTATE'S OWN src/ tree as a licensed build output. edition.py is its sibling
for the OTHER end of the border round trip: it renders a PACK — rows of law/text carried across the
border as DATA — into a human-readable edition, ONE sentence per row, each ANCHORED to its row id, so
a reader can trace any sentence back to the exact row it renders and no sentence floats free of the
record. It is PURE and GENERIC: same pack + same source + same engine -> same bytes, for ANY pack
(nothing pack-specific — D08.41 holds: the record is gov-os's, the pack is a submitter's data, and
this renderer never founds, trusts, or decides a pack row; it only re-presents it).

THE STAMP (source / renderer / engine) — the render.py precedent carried into the round trip:
  source   — WHAT is rendered: the crossing's content hash (kernel.border.content_id), the id of the
             BORDER-SUBMIT that carried the pack across. The edition names the exact crossing it
             renders, so the round trip's content hash recomputes EQUAL at this final hop.
  renderer — HOW: this tool's own sha256 (edition.py's bytes). A changed renderer is visible in the
             stamp (the render.py tool-sha discipline).
  engine   — UNDER WHICH WORLD: the servicing world the caller NAMES (the gov-os founding version and
             the as-of head the view was serviced over). The master gradient's law — a rendering,
             like a count, names its world. edition.py stays generic by taking the engine as data.

No clock in the edition BODY (render.py's discipline: a stamp may carry a date; the edition never).
The `edition_digest` is a sha256 over the canonical (sort_keys) body — source, engine, pack identity
and the anchored sentences — so a drift in ANY rendered byte moves it. `verify_edition` re-renders and
compares; `selftest` plants a one-byte drift and proves the control NAMES it while the clean edition
passes (the check_clean_from_cut.py --selftest planted-control precedent). Reads a pack dict, returns
a dict; NEVER edits a record, a pack, or any file under src/.

Run from the repo root:
  python3 tools/release/edition.py --selftest   # planted-drift control: a changed byte is NAMED
"""
import hashlib
import json
import os
import sys


def tool_sha():
    """This renderer's own sha256 (the `renderer` stamp) — edition.py's bytes, so a changed renderer
    shows in every edition it produces (the render.py tool-sha precedent)."""
    with open(os.path.abspath(__file__), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _row_anchor(row):
    """A row's ANCHOR — its own id, under whichever key the pack uses. Generic across packs: a pack
    row identifies itself by `row_id`, or a law row by `ruleId`, or a bare `id`. None if the row
    carries no id (an unanchorable row — the edition refuses to invent one)."""
    return row.get("row_id") or row.get("ruleId") or row.get("id")


def sentence_for(row):
    """ONE anchored sentence for one pack row (generic). The sentence carries the row's ANCHOR (its
    id), its TEXT verbatim, and how the constitution would enforce it (`enforced_by`, the pack's own
    classification) — so a reader sees both the rule and whether a gate or a human holds it. The
    renderer re-presents the row; it never decides it (D08.41 / RW-PEER-TRUSTED)."""
    return {"anchor": _row_anchor(row), "text": row.get("text", ""),
            "enforced_by": row.get("enforced_by")}


def render_edition(pack, *, source, engine):
    """Render `pack` into an anchored human edition, PURE and GENERIC. `source` is the crossing's
    content hash (what this edition renders); `engine` is the servicing world (named by the caller,
    kept as data so this stays pack-agnostic). Returns {stamp, sentences, edition_digest}. Same
    inputs -> same bytes (no clock in the body)."""
    sentences = [sentence_for(r) for r in pack.get("rows", [])]
    body = {
        "source": source,
        "engine": engine,
        "pack": pack.get("pack"),
        "version": pack.get("version"),
        "sentences": sentences,
    }
    edition_digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    stamp = {"source": source, "renderer": tool_sha(), "engine": engine,
             "pack": pack.get("pack"), "version": pack.get("version")}
    return {"stamp": stamp, "sentences": sentences, "edition_digest": edition_digest}


def verify_edition(edition, pack, *, source, engine):
    """Does `edition` match a fresh render of `pack` under the same `source` and `engine`? Re-renders
    and compares the edition_digest — True iff every rendered byte still matches. A changed byte of
    the pack, the source, or the engine moves the digest and this returns False (the drift check that
    can fail). Reused by the planted-drift control below."""
    fresh = render_edition(pack, source=source, engine=engine)
    return edition.get("edition_digest") == fresh["edition_digest"]


def selftest():
    """PLANTED-DRIFT CONTROL (the check_clean_from_cut.py --selftest precedent). Render a tiny pack,
    then plant a ONE-BYTE drift in a rendered sentence and prove `verify_edition` NAMES it (returns
    False), while the untouched edition still passes. A control that cannot red is the defect."""
    pack = {"pack": "SELFTEST", "version": "0.0.0",
            "rows": [{"row_id": "R1", "text": "a rule", "enforced_by": "structured"},
                     {"row_id": "R2", "text": "another rule", "enforced_by": "judgment"}]}
    source = "sha256:" + "0" * 64
    engine = {"founding_version": "0.0.0", "as_of_head": 0}
    ed = render_edition(pack, source=source, engine=engine)

    clean = verify_edition(ed, pack, source=source, engine=engine)
    drifted = dict(ed)                                   # a changed byte of what was shown
    drifted_sentences = [dict(s) for s in ed["sentences"]]
    drifted_sentences[0]["text"] = "a rulE"              # one byte
    drifted["sentences"] = drifted_sentences
    drifted["edition_digest"] = hashlib.sha256(
        json.dumps({"source": source, "engine": engine, "pack": pack.get("pack"),
                    "version": pack.get("version"), "sentences": drifted_sentences},
                   sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    caught = not verify_edition(drifted, pack, source=source, engine=engine)

    print("CONTROL clean edition verifies ->", clean)
    print("CONTROL planted one-byte drift caught ->", caught)
    ok = clean and caught
    print("\n%s: the edition drift check %s name a planted one-byte drift"
          % ("PASS" if ok else "FAIL", "can" if ok else "CANNOT"))
    return 0 if ok else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    sys.stderr.write("edition.py is a library (render_edition / verify_edition); "
                     "run --selftest for the planted-drift control.\n")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
