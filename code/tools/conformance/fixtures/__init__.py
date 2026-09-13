# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: conformance-harness ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""The self-test's governed targets, and the one thing that stands them up.

THE INSTRUMENT NEVER CREATES ITS OWN SUBJECT. `Target.establish_subject` refuses a
subject that is not there, without exception, because "the mount was not raised"
and "the harness made something to measure" must never be the same code path —
that is precisely how a run comes to report on a plain directory (design/10
§11.2b).

Which leaves a true and separate obligation: a FIXTURE has to exist before it can
be judged, and standing one up is the self-test's job rather than the instrument's.
This function is that job, and it is deliberately narrow — it stands up the
`fixture-*` descriptors only, and only where the descriptor declares its subject
is an ordinary directory. A descriptor claiming a real filesystem is refused here,
so nothing in this file can ever be mistaken for a way to conjure a mount.
"""

import json
import shutil
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent
TARGETS_DIR = FIXTURES_DIR.parent / "targets"
PREFIX = "fixture-"


def stand_up(targets_dir=None):
    """Create the subject directory of each self-test fixture, if absent.

    Returns the paths it stood up. Nothing in the harness calls this; the
    self-test does, before it judges anything.
    """
    d = Path(targets_dir or TARGETS_DIR)
    made = []
    for path in sorted(d.glob("%s*.json" % PREFIX)):
        spec = json.loads(path.read_text())
        subject = spec.get("subject") or {}
        if not subject.get("path"):
            continue
        if subject.get("fstype") != "directory":
            raise ValueError(
                "%s declares its subject is served by %r. This function stands up "
                "ordinary directories and nothing else — a real filesystem is raised "
                "by whoever owns it, never by the instrument or its self-test."
                % (path.name, subject.get("fstype"))
            )
        p = Path(subject["path"])
        if not p.exists():
            p.mkdir(parents=True)
            made.append(str(p))
    return made


def tear_down(targets_dir=None):
    """Remove the subject tree of each self-test fixture — the tear-down half of the
    lifecycle `stand_up` opens (design/10 §11.2b, second half).

    THE SURFACE §11.2b'S RULE WAS NOT APPLIED TO. `targets.Target.teardown_scratch` tears down
    the TARGET's scratch after a run — the uuid-named `run-*` directories the transport made —
    but the fixture SUBJECTS this self-test stands up were left standing, established and never
    removed: `/tmp/govos-conformance/fixture-*` persisted as a WARM world across campaign 3
    (1,655 run directories and 68 MB accumulated since EP-24). A fixture, unlike a real target,
    IS the harness's own — a real mount is torn down by whoever raised it and the instrument
    must never touch it — so tearing the fixture subject down is the self-test's own obligation,
    exactly as standing it up is.

    Removes exactly the subject each `fixture-*` descriptor declares — what `stand_up` stands
    up and nothing else, the same "remove what the run created and nothing else" discipline the
    target teardown keeps. Refuses a descriptor that claims a real filesystem, the mirror of
    `stand_up`'s own refusal, so nothing here can ever tear down a mount. Returns the paths it
    removed; idempotent, so a tear-down over an already-clean tree removes nothing and says so.
    """
    d = Path(targets_dir or TARGETS_DIR)
    removed = []
    for path in sorted(d.glob("%s*.json" % PREFIX)):
        spec = json.loads(path.read_text())
        subject = spec.get("subject") or {}
        if not subject.get("path"):
            continue
        if subject.get("fstype") != "directory":
            raise ValueError(
                "%s declares its subject is served by %r. This function tears down "
                "ordinary directories and nothing else — a real filesystem is torn down "
                "by whoever owns it, never by the instrument or its self-test."
                % (path.name, subject.get("fstype"))
            )
        p = Path(subject["path"]).resolve()
        # Design for the stretch: rmtree is destructive where mkdir is not, so a malformed
        # descriptor must not be able to reach a filesystem root or a home directory. A fixture
        # subject is a nested scratch path by construction; anything shallower is refused.
        if len(p.parts) < 3 or p == Path.home().resolve():
            raise ValueError(
                "%s: refusing to tear down %r — a fixture subject is a nested scratch path, "
                "never a filesystem root or a home directory" % (path.name, str(p))
            )
        if p.exists():
            shutil.rmtree(p)
            removed.append(str(p))
    return removed
