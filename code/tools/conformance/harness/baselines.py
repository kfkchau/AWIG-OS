# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: conformance-harness ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""Baselines: what the stock kernel answered, written down and PINNED.

design/36 K4 puts the whole-class pinning law on this instrument's baselines: at
verify time no assertion reads the live stock system. The mechanism has five
parts and all five are here.

  1. A capture is committed TEXT — sorted, indented JSON in the repo — so a
     reviewer can read what the kernel said without running anything.
  2. A capture is DATED and sha-summed in its manifest, and `load()` recomputes
     every sum before handing a single row over. A baseline that changed since it
     was captured refuses; it does not quietly become the new truth.
  3. Loading takes a NAME and reads only under this directory. There is no
     parameter by which a live target could be substituted, which is why the
     pinning claim is structural rather than a promise the runner keeps.
  4. A capture PINS SOMETHING OR IT DOES NOT HAPPEN, at both ends [EP-28L, on
     the mentor's ruling of 2026-08-04]. Part 2's sums are computed by iterating
     the manifest's `files` map, and an empty map is a CLEAN LOOP — nothing to
     check, nothing mismatches — so a baseline naming no files passes every
     check parts 1 to 3 have and hands over zero rows. So `load` refuses a
     manifest whose `files` map is empty, and `write_capture` STOPS BEFORE
     WRITING when it would pin nothing.

The failure this refuses is the one EP-15 met: an oracle whose frozen side was
still, somewhere, reading the live world — so growth in the live world moved the
"frozen" answer and the divergence it was built to catch went silent.

Part 4 refuses a second one, found on 2026-08-04 by a capture aimed at a scratch
directory: a mistyped `--group` is one character, it matches no rows, and the
capture then wrote a complete, dated, sha-summed manifest reporting no files at
all and returned SUCCESS. `write_capture`'s `base` defaults to the PINNED
directory, so the same character typed without a scratch base replaces a pin
with an empty manifest, everything downstream reports green, and autosync makes
it history in under two minutes (§A53).

Part 5 refuses a THIRD one, and it is the same character typed VALIDLY [EP-28M,
2026-08-04]. A `--group` naming a real group that is only SOME of what the
artifact holds writes a complete, dated, sha-summed manifest naming that group
alone. Every other group file stays on disk ORPHANED — named by no manifest,
covered by no sum, its rows handed over to nobody — and the load SUCCEEDS,
because part 4 asks only whether the map is non-EMPTY and a PARTIAL map is not
an empty one. So the artifact accounts for every file it holds, in both
directions at both ends: `write_capture` STOPS before orphaning, and `load`
REFUSES an artifact already holding an unnamed member.
"""

import datetime
import hashlib
import json
from pathlib import Path

BASELINES_DIR = Path(__file__).resolve().parent.parent / "baselines"
MANIFEST_NAME = "MANIFEST.json"
HARNESS_VERSION = "1"

#: The clause both ends cite, written once so the two refusals cannot drift
#: apart. §A38 at the ARTIFACT layer: a check whose pass condition is the
#: ABSENCE of output cannot tell "nothing changed" from "nothing was looked at",
#: so its SUBJECT is proven non-empty before the pass counts. The founding
#: block's `ls-files >= 1` is the same clause one instrument over, and
#: T-MINT-SET-ENUMERATED's population clause is the same clause one layer down.
NON_EMPTY_CLAUSE = (
    "A pinned baseline with no files pins nothing: the sums are computed by "
    "iterating the manifest's `files` map, an empty map is a clean loop, and a "
    "baseline with zero rows then answers NOT-RUN for every row it is asked "
    "about — which is not a failure, so the run reports OK over nothing. The "
    "subject is proven non-empty before the artifact counts "
    "(EP-28L; §A38 at the artifact layer)."
)


#: The clause the partial-set refusals cite, at both ends. §A39's shape at the
#: ARTIFACT layer: an inherited narrowing is not forbidden, an UNDECLARED one is.
#: EP-28L proved the map non-EMPTY; a non-empty map can still be a PARTIAL one,
#: and a partial map leaves the files it stopped naming on disk, covered by no
#: sum, holding rows nothing hands over — while the load succeeds.
ACCOUNTED_CLAUSE = (
    "A pinned baseline ACCOUNTS FOR EVERY FILE IT HOLDS. `load` iterates the "
    "manifest's `files` map, so a group file present in the directory and absent "
    "from the map is ORPHANED: no sum covers it, no row it holds is handed over, "
    "and the load still succeeds because the map is non-empty. The accounting is "
    "a set difference in BOTH directions — a name with no file, and a file with "
    "no name — and neither silence is admitted (EP-28M)."
)


class BaselineError(RuntimeError):
    pass


def artifact_members(d):
    """Every group file the artifact HOLDS, read from the DIRECTORY.

    Read from the directory and never from the manifest, which is the whole
    point: the manifest is one side of the accounting and cannot also be the
    source for the other side. A directory that does not exist holds nothing —
    which is a first capture, not a partial one, and the caller distinguishes
    them by what it is about to write.
    """
    d = Path(d)
    if not d.is_dir():
        return set()
    return {
        p.name
        for p in d.iterdir()
        if p.is_file() and p.suffix == ".json" and p.name != MANIFEST_NAME
    }


def _sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _dump(obj):
    return json.dumps(obj, indent=1, sort_keys=True) + "\n"


class PinnedBaselines:
    """Read-only, name-addressed, sha-verified. Holds no transport and no target:
    it is data that was read off disk, and there is nothing live inside it."""

    def __init__(self, target_name, manifest, rows_by_id, path):
        self.target_name = target_name
        self.manifest = manifest
        self._rows = rows_by_id
        self.path = path

    @property
    def captured_at(self):
        return self.manifest.get("captured_at")

    @property
    def kernel(self):
        u = (self.manifest.get("target_identity") or {}).get("uname") or {}
        return "%s %s %s" % (u.get("sysname", "?"), u.get("release", "?"), u.get("machine", "?"))

    def get(self, row_id):
        return self._rows.get(row_id)

    def row_ids(self):
        return sorted(self._rows)

    def skipped(self):
        return self.manifest.get("skipped", [])


def baseline_dir(target_name, base=None):
    return Path(base or BASELINES_DIR) / target_name


def write_capture(target_name, target_spec, group_files, identity, root_identity,
                  coverage, skipped, base=None, captured_at=None):
    """Write one capture: the per-group observation files, then the manifest that
    sums them. The manifest is written LAST, after the bytes it certifies exist —
    the estate's own currency-line-last discipline, applied to an artifact.

    AND IT STOPS BEFORE WRITING when there is nothing to pin. The stop is the
    first statement for a reason that is about `base` rather than about tidiness:
    `base=None` resolves to the PINNED directory, so a zero-file capture replaces
    a pin with an empty manifest and reports success. Refusing that artifact at
    LOAD time would not be enough — an artifact that exists-but-refuses has
    ALREADY cost the pin its content, and a load that refuses tells a reader the
    pin is gone without giving it back. Only a stop taken BEFORE the write keeps
    the undo window open, which is why no path is resolved and no directory is
    made above this line.

    The refusal beats the repair (P4): it does not substitute a default base,
    re-select every group, or retry. A wrong `--group` is a caller error and it
    is surfaced at the caller, loudly, with nothing written.
    """
    if not group_files:
        raise BaselineError(
            "capture for target %r matched ZERO groups, so this write would pin "
            "NOTHING. It STOPS BEFORE WRITING and resolves no path at all. Check "
            "the --group value against the group ids `conformance list` reports: "
            "they carry their number, so the files group is `06-files` and not "
            "`files`. %s" % (target_name, NON_EMPTY_CLAUSE)
        )
    d = baseline_dir(target_name, base)
    #: AND IT STOPS AGAIN when the write would ORPHAN a file the artifact already
    #: holds. Resolving the path is a READ and creates nothing; the stop is above
    #: `mkdir` and above every `write_text`, so the existing manifest still names
    #: what it named and the undo window stays open — the same reason the
    #: zero-group stop is the first statement. A load-time refusal would tell a
    #: reader the artifact is inconsistent AFTER the manifest that named the
    #: orphan was overwritten, and §A53 makes that history in under two minutes.
    produced = {"%s.json" % group for group in group_files}
    orphans = artifact_members(d) - produced
    if orphans:
        raise BaselineError(
            "capture for target %r would write %d group file(s) %s and leave %d "
            "file(s) %s standing in %s ORPHANED — held by the artifact and named "
            "by no manifest. It STOPS BEFORE WRITING, so the manifest that still "
            "names them is intact. Capture every group the artifact holds, or "
            "capture into a scratch base. %s"
            % (target_name, len(produced), sorted(produced), len(orphans),
               sorted(orphans), d, ACCOUNTED_CLAUSE)
        )
    d.mkdir(parents=True, exist_ok=True)
    files_meta = {}
    for group, payload in sorted(group_files.items()):
        name = "%s.json" % group
        text = _dump(payload)
        (d / name).write_text(text)
        files_meta[name] = {
            "sha256": _sha256_text(text),
            "bytes": len(text.encode("utf-8")),
            "rows": len(payload.get("rows", {})),
        }
    manifest = {
        "target": target_name,
        "target_kind": target_spec.get("kind"),
        "target_description": target_spec.get("description", ""),
        "captured_at": captured_at
        or datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
        "harness_version": HARNESS_VERSION,
        "target_identity": identity,
        "root_pass_identity": root_identity,
        "files": files_meta,
        "coverage": coverage,
        "skipped": skipped,
        "pinning_law": (
            "design/36 K4: these captures are pinned artifacts. Verify mode reads "
            "them and never the live stock system. Re-capturing is a deliberate act "
            "with its own dated entry, never a side effect of running a verify."
        ),
    }
    (d / MANIFEST_NAME).write_text(_dump(manifest))
    return d, manifest


def load(target_name, base=None):
    """Load a pinned capture, recomputing every sum. Refuses on any mismatch —
    and refuses a manifest that names NO files, because every sum passing over an
    empty map is a vacuous pass rather than a verified one. Nothing downstream
    can green over a baseline this function never handed over."""
    d = baseline_dir(target_name, base)
    mpath = d / MANIFEST_NAME
    if not mpath.exists():
        raise BaselineError("no pinned baseline for target %r at %s" % (target_name, d))
    manifest = json.loads(mpath.read_text())
    files = manifest.get("files") or {}
    if not files:
        raise BaselineError(
            "baseline %s at %s names NO files: its manifest's `files` map is "
            "empty, so this load has no subject and would hand over a baseline "
            "with zero rows. %s" % (target_name, d, NON_EMPTY_CLAUSE)
        )
    #: THE ACCOUNTING, BOTH DIRECTIONS, over a subject EP-28L's clause above has
    #: already proven non-empty — so this set difference is read against N > 0
    #: names rather than against nothing. The other direction (a name with no
    #: file) is the per-file check inside the loop below: it stays there because
    #: it also catches a file that vanishes between this accounting and its read,
    #: which a single up-front pass cannot.
    orphans = artifact_members(d) - set(files)
    if orphans:
        raise BaselineError(
            "baseline %s at %s holds %d file(s) %s that its manifest NAMES "
            "NOWHERE: the map names %s. An orphaned group file is covered by no "
            "sum and hands over none of its rows, and this load would have "
            "succeeded because the map is non-empty — reporting on a subject "
            "smaller than the artifact without saying so. %s"
            % (target_name, d, len(orphans), sorted(orphans), sorted(files),
               ACCOUNTED_CLAUSE)
        )
    rows = {}
    for name, meta in sorted(files.items()):
        fpath = d / name
        if not fpath.exists():
            raise BaselineError("baseline %s names %s, which is missing" % (target_name, name))
        text = fpath.read_text()
        got = _sha256_text(text)
        if got != meta["sha256"]:
            raise BaselineError(
                "baseline %s/%s does not match its pinned sha256 "
                "(manifest %s, file %s) — a baseline that changed since capture is "
                "not a baseline" % (target_name, name, meta["sha256"][:16], got[:16])
            )
        payload = json.loads(text)
        for row_id, obs in payload.get("rows", {}).items():
            if row_id in rows:
                raise BaselineError("row %s appears in two baseline files" % row_id)
            rows[row_id] = obs
    return PinnedBaselines(target_name, manifest, rows, d)
