# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: conformance-harness ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""Targets: the two things the harness can be pointed at, and how it reaches them.

A **stock** target is a plain kernel. It has no record, so only check 1 has
anything to read there, and the harness's only lawful use of it is `--capture`:
drive the rows, write the answers down, pin them. After that the stock target is
finished with — a baseline that quietly re-reads reality is a live side in
disguise (the EP-15 whole-class lesson, applied to baselines).

A **governed** target is a gov-os custody surface: a filesystem root it serves,
the record file it runs on, its own declaration of which action belongs to which
recording class, and a way to kill its derived state and rebuild it from the
record. Those four are what checks 2 and 3 consume.

The harness never imports the governed target's code. It reads the record FILE —
the append-only jsonl that IS the definitive — and the target's class map as
data. That is why this tree has no dependency on src/ and why EP-25's mount, and
the in-kernel module after it, can be measured by the same instrument without
either of them being rebuilt for it.
"""

import importlib
import json
import os
import shlex
import shutil
import subprocess
import uuid
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
TARGETS_DIR = HARNESS_DIR.parent / "targets"
PROBE_PATH = HARNESS_DIR / "probe.py"

#: The `fstype` a descriptor declares when the correct subject is an ordinary
#: directory rather than a mount of its own. It is an assertion in its own right:
#: a target that quietly became a mount point would refuse rather than report.
SUBJECT_DIRECTORY = "directory"

#: How many of a dirty scratch's entries a refusal names before it stops. Enough
#: to identify what is there; the refusal says how many more there were.
DIRTY_REPORT_LIMIT = 12


class TargetError(RuntimeError):
    pass


class VocabularyError(TargetError):
    """The target has not declared what its records are ABOUT.

    design/10 §11.4a: a record is attributed to the act it covers, read from its
    own action — and what an action means is the target's vocabulary. A target
    that exposes a record and declares no covers map cannot be judged on the
    recording leg, and the run refuses rather than falling back to the landing
    point the subsection retired.
    """


class SubjectError(TargetError):
    """The subject is not what its descriptor claims, or cannot be established.

    design/10 §11.2b: an instrument establishes its subject before reporting on
    it, and leaves it as it found it. A pass against an absent subject is worse
    than a failure, because it is indistinguishable from success.
    """


def resolve_local_path(p):
    """A path this process will hand to the filesystem, resolved as the shell
    would resolve it. `~` is expanded HERE because `Path("~/x")` is a directory
    literally named `~` — which is not a hypothetical: a `~` in a target
    descriptor sent the probe into one, and the harness reported ABI 40 of 40
    while the record file held one name."""
    return os.path.abspath(os.path.expanduser(str(p)))


def _unescape_mountinfo(field):
    """mountinfo octal-escapes space, tab, newline and backslash in paths."""
    for esc, ch in (("\\040", " "), ("\\011", "\t"), ("\\012", "\n"), ("\\134", "\\")):
        field = field.replace(esc, ch)
    return field


def served_by(path):
    """Which filesystem serves this path, read from the kernel's own mount table,
    or None when the path is not a mount point of its own.

    /proc/self/mountinfo is the answer the kernel gives about itself; nothing here
    asks the target what it is. That distinction is the whole check: the target
    under test is exactly the thing whose word cannot be taken for it.
    """
    want = os.path.realpath(path)
    try:
        with open("/proc/self/mountinfo", "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    found = None
    for line in lines:
        parts = line.split()
        if len(parts) < 8 or "-" not in parts:
            continue
        if _unescape_mountinfo(parts[4]) != want:
            continue
        sep = parts.index("-")
        if sep + 1 < len(parts):
            found = parts[sep + 1]  # the last mount at this point is the live one
    return found


class ProbeTransport:
    """Runs the probe ON the target and returns its answer. One program, both
    sides: capture and verify execute the same probe.py bytes."""

    name = "abstract"

    def run(self, plan, as_root=False):
        raise NotImplementedError


class LocalTransport(ProbeTransport):
    name = "local"

    def __init__(self, scratch, python="python3", sudo=None):
        self.scratch = resolve_local_path(scratch)
        self.python = python
        self.sudo = sudo
        #: Every directory this transport made in the subject's scratch. The
        #: teardown removes what the run created and nothing else, which is the
        #: only way "leave the subject as it was found" can be kept honestly.
        self.run_dirs = []

    def run(self, plan, as_root=False):
        run_dir = Path(self.scratch) / ("run-%s" % uuid.uuid4().hex[:8])
        run_dir.mkdir(parents=True, exist_ok=True)
        self.run_dirs.append(run_dir)
        plan = dict(plan, scratch=str(run_dir / "tree"))
        plan_path = run_dir / "plan.json"
        plan_path.write_text(json.dumps(plan))
        cmd = shlex.split(self.python) + [str(PROBE_PATH), str(plan_path)]
        if as_root:
            if not self.sudo:
                raise TargetError("local target declares no root route")
            cmd = shlex.split(self.sudo) + cmd
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        if out.returncode != 0:
            raise TargetError("probe failed (rc=%s): %s" % (out.returncode, out.stderr[-2000:]))
        return json.loads(out.stdout)


class SshTransport(ProbeTransport):
    name = "ssh"

    def __init__(self, host, port=22, user=None, key=None, scratch="/tmp", python="python3",
                 sudo="sudo -n"):
        self.host = host
        self.port = port
        self.user = user
        self.key = key
        self.scratch = scratch
        self.python = python
        self.sudo = sudo

    def _ssh_base(self):
        cmd = [
            "ssh",
            "-p",
            str(self.port),
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            "LogLevel=ERROR",
            "-o",
            "ConnectTimeout=10",
        ]
        if self.key:
            cmd += ["-i", os.path.expanduser(self.key)]
        cmd.append("%s@%s" % (self.user, self.host) if self.user else self.host)
        return cmd

    def _scp(self, local, remote):
        cmd = [
            "scp",
            "-P",
            str(self.port),
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            "LogLevel=ERROR",
        ]
        if self.key:
            cmd += ["-i", os.path.expanduser(self.key)]
        dest = "%s@%s:%s" % (self.user, self.host, remote) if self.user else "%s:%s" % (self.host, remote)
        cmd += [str(local), dest]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if out.returncode != 0:
            raise TargetError("scp failed: %s" % out.stderr[-2000:])

    def run(self, plan, as_root=False):
        run_dir = "%s/govos-conf-%s" % (self.scratch.rstrip("/"), uuid.uuid4().hex[:8])
        mk = subprocess.run(
            self._ssh_base() + ["mkdir -p %s" % shlex.quote(run_dir)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if mk.returncode != 0:
            raise TargetError("could not reach target: %s" % mk.stderr[-2000:])
        plan = dict(plan, scratch="%s/tree" % run_dir)
        local_plan = Path(run_dir.replace("/", "_") + ".plan.json")
        tmp = Path(os.environ.get("TMPDIR", "/tmp")) / local_plan.name
        tmp.write_text(json.dumps(plan))
        self._scp(PROBE_PATH, "%s/probe.py" % run_dir)
        self._scp(tmp, "%s/plan.json" % run_dir)
        tmp.unlink(missing_ok=True)
        inner = "%s %s/probe.py %s/plan.json" % (self.python, run_dir, run_dir)
        if as_root:
            inner = "%s %s" % (self.sudo, inner)
        out = subprocess.run(
            self._ssh_base() + [inner], capture_output=True, text=True, timeout=1800
        )
        if out.returncode != 0:
            raise TargetError("probe failed on target (rc=%s): %s" % (out.returncode, out.stderr[-2000:]))
        return json.loads(out.stdout)


class JsonlRecordSource:
    """The record, read as the append-only file it is. `mark()` is a line count
    and `since()` is what was appended after it — no index, no cache, nothing
    stored. If the file does not exist yet the mark is zero, which is the honest
    answer for a target that has recorded nothing."""

    def __init__(self, path):
        self.path = Path(path)

    def _lines(self):
        if not self.path.exists():
            return []
        return [ln for ln in self.path.read_text().splitlines() if ln.strip()]

    def mark(self):
        return len(self._lines())

    def since(self, mark):
        """What was appended after the mark — and a REFUSAL if the record is now
        shorter than the mark. An append-only record does not shrink, so a shorter
        one means the file was replaced between the mark and the read, and the
        window this would return is empty. "Nothing was appended" and "I am looking
        at a different file" are the same empty list and mean opposite things."""
        lines = self._lines()
        if mark and len(lines) < mark:
            raise TargetError(
                "the record at %s held %d lines at the mark and holds %d now. An "
                "append-only record does not shrink; this window cannot be computed "
                "and is refused rather than returned empty." % (self.path, mark, len(lines))
            )
        return [json.loads(ln) for ln in lines[mark:]]

    def select(self, indices):
        lines = self._lines()
        return [json.loads(lines[i]) for i in indices if 0 <= i < len(lines)]

    @property
    def path_on_target(self):
        return str(self.path)


class Replayer:
    """Kill the derived state, rebuild it from the record, and hand back what the
    target then serves. Declared by the target either as a command that prints a
    JSON snapshot, or as a python entry point for an in-tree fixture."""

    def __init__(self, spec):
        self.spec = spec or {}

    @property
    def available(self):
        return bool(self.spec)

    def snapshot(self, row_id, context=None):
        if not self.spec:
            return None
        if "python" in self.spec:
            mod_name, attr = self.spec["python"].split(":")
            fn = getattr(importlib.import_module(mod_name), attr)
            return fn(row_id, context or {}, self.spec.get("config") or {})
        if "command" in self.spec:
            cmd = [c.replace("{row_id}", row_id) for c in self.spec["command"]]
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            if out.returncode != 0:
                raise TargetError("replay command failed: %s" % out.stderr[-2000:])
            return json.loads(out.stdout)
        raise TargetError("replay spec declares neither python nor command")


class Target:
    """A named place the harness can be pointed at. Loaded from data; the harness
    holds no target in code."""

    def __init__(self, spec, base_dir=None):
        self.spec = spec
        self.base_dir = Path(base_dir or TARGETS_DIR)
        self.name = spec["name"]
        self.kind = spec["kind"]
        if self.kind not in ("stock", "governed"):
            raise TargetError("target %s: kind must be stock or governed" % self.name)
        self.description = spec.get("description", "")
        self.capabilities = tuple(spec.get("capabilities", ()))
        self.coalescing_policies = tuple(spec.get("coalescing_policies", ()))
        self._transport = None
        self._created_scratch = False

    @classmethod
    def load(cls, name, targets_dir=None):
        d = Path(targets_dir or TARGETS_DIR)
        path = d / ("%s.json" % name)
        if not path.exists():
            raise TargetError("no target descriptor at %s" % path)
        return cls(json.loads(path.read_text()), base_dir=d)

    # ---- probe side -----------------------------------------------------
    @property
    def transport(self):
        if self._transport is None:
            t = dict(self.spec.get("transport") or {})
            kind = t.pop("type", None)
            if kind == "local":
                self._transport = LocalTransport(**t)
            elif kind == "ssh":
                self._transport = SshTransport(**t)
            else:
                raise TargetError("target %s: unknown transport %r" % (self.name, kind))
        return self._transport

    @property
    def can_root(self):
        return "root" in self.capabilities

    @property
    def transport_kind(self):
        return (self.spec.get("transport") or {}).get("type")

    @property
    def scratch_path(self):
        """Where the probe works, resolved. None for a transport whose scratch is
        not a path in this process's own filesystem."""
        t = self.spec.get("transport") or {}
        if t.get("type") != "local" or not t.get("scratch"):
            return None
        return resolve_local_path(t["scratch"])

    # ---- the subject (design/10 §11.2b) ---------------------------------
    def establish_subject(self):
        """Confirm the target is the thing its descriptor claims, or REFUSE.

        This runs before any row, and its failure is an abort rather than a failing
        row: a report about a subject that was never established is the thing the
        subsection exists to prevent. During EP-25 a mount failed to launch and
        every check passed against a plain host directory; a `~` in a descriptor
        sent the probe into a directory literally named `~` and the harness
        reported ABI 40 of 40 while the record held one name; and at the EP-25
        verdict a verify run against an unraised mount reported forty rows instead
        of refusing. Three instances, one missing check.
        """
        spec = self.spec.get("subject")
        if not spec:
            raise SubjectError(
                "target %r declares no subject. design/10 §11.2b requires an "
                "instrument to establish its subject before reporting on it, and a "
                "descriptor that does not say what its subject IS cannot be checked "
                "against it." % self.name
            )
        declared = spec.get("fstype")
        if not spec.get("path") or not declared:
            raise SubjectError(
                "target %r declares a subject without both a path and an fstype" % self.name
            )
        if self.transport_kind != "local":
            raise SubjectError(
                "target %r is reached over %s, and the subject check reads THIS "
                "host's mount table, which says nothing about that one. The subject "
                "cannot be established from here, so the run REFUSES rather than "
                "reporting on a subject it never established."
                % (self.name, self.transport_kind)
            )
        path = resolve_local_path(spec["path"])
        if not os.path.isdir(path):
            raise SubjectError(
                "target %r declares its subject at %s and there is no directory "
                "there. Nothing is created: a missing subject is a finding, not a "
                "setup step." % (self.name, path)
            )
        served = served_by(path)
        if declared == SUBJECT_DIRECTORY:
            if served is not None:
                raise SubjectError(
                    "target %r declares its subject at %s is an ordinary directory, "
                    "and it is a mount point of type %r. The run REFUSES: the subject "
                    "is not the thing the descriptor claims."
                    % (self.name, path, served)
                )
        elif served is None:
            raise SubjectError(
                "target %r declares its subject at %s is served by %r, and nothing "
                "is mounted there — the path is an ordinary directory. A pass "
                "against an absent subject is worse than a failure, because it is "
                "indistinguishable from success (design/10 §11.2b)."
                % (self.name, path, declared)
            )
        elif not (served == declared or served.startswith(declared + ".")):
            raise SubjectError(
                "target %r declares its subject at %s is served by %r and it is "
                "served by %r" % (self.name, path, declared, served)
            )
        return {"path": path, "declared": declared, "served_by": served or SUBJECT_DIRECTORY}

    # ---- the scratch lifecycle (design/10 §11.2b, second half) ----------
    def establish_scratch(self):
        """Clean before the run: created if absent, verified empty if present.

        A scratch found DIRTY is reported by name and refused, never driven. Those
        files are evidence of a prior mis-addressed run, and driving them would
        both measure someone else's leftovers and destroy the evidence of how they
        got there.
        """
        path = self.scratch_path
        if path is None:
            return {
                "lifecycle": "not established",
                "reason": "the %s transport makes a fresh uuid-named directory on the "
                "target for each run and addresses no mountpoint of this host's; the "
                "lifecycle is not established for it and that limit is stated rather "
                "than assumed away." % self.transport_kind,
            }
        if os.path.exists(path):
            if not os.path.isdir(path):
                raise SubjectError(
                    "the scratch of target %r is %s, which is not a directory"
                    % (self.name, path)
                )
            entries = sorted(os.listdir(path))
            if entries:
                shown = ", ".join(entries[:DIRTY_REPORT_LIMIT])
                more = (
                    " (and %d more)" % (len(entries) - DIRTY_REPORT_LIMIT)
                    if len(entries) > DIRTY_REPORT_LIMIT
                    else ""
                )
                raise SubjectError(
                    "the scratch of target %r is NOT clean: %s holds %d entr%s — %s%s. "
                    "Those are evidence of a prior run that was not torn down, and a "
                    "run that drives them measures leftovers. REFUSED, never driven "
                    "(design/10 §11.2b)."
                    % (self.name, path, len(entries),
                       "y" if len(entries) == 1 else "ies", shown, more)
                )
            self._created_scratch = False
        else:
            os.makedirs(path)
            self._created_scratch = True
        return {"path": path, "created": self._created_scratch}

    def teardown_scratch(self):
        """Leave the subject as it was found. What the run created, the run
        removes — and nothing else, which is why the run directories are tracked
        rather than the scratch being emptied wholesale."""
        path = self.scratch_path
        if path is None:
            return {"lifecycle": "not established"}
        removed = []
        if self._transport is not None:
            for d in self._transport.run_dirs:
                if os.path.exists(d):
                    shutil.rmtree(d, ignore_errors=True)
                removed.append(str(d))
            self._transport.run_dirs = []
        if self._created_scratch and os.path.isdir(path) and not os.listdir(path):
            os.rmdir(path)
            self._created_scratch = False
        return {"path": path, "removed": removed}

    def run_probes(self, assertions, as_root=False, record_file=None):
        """Drive a set of rows. Returns {row_id: observation}."""
        plan_rows = []
        for a in assertions:
            probe = a.root_probe if as_root else a.probe
            if not (probe and probe.get("steps")):
                continue
            plan_rows.append({"row_id": a.row_id, "steps": probe["steps"]})
        if not plan_rows:
            return {}, {}
        plan = {"rows": plan_rows}
        if record_file:
            plan["record_file"] = record_file
        answer = self.transport.run(plan, as_root=as_root)
        meta = {k: v for k, v in answer.items() if k != "rows"}
        return answer.get("rows", {}), meta

    # ---- record side (governed targets only) ----------------------------
    @property
    def record_source(self):
        rec = self.spec.get("record")
        if not rec:
            return None
        if "jsonl" in rec:
            return JsonlRecordSource(self._resolve(rec["jsonl"]))
        raise TargetError("target %s: unknown record spec" % self.name)

    @property
    def class_map(self):
        """action -> recording class, declared BY THE TARGET. The harness reads it
        the way it reads the rows: as data it does not author."""
        cm = self.spec.get("class_map")
        if not cm:
            return None
        if "inline" in cm:
            return dict(cm["inline"])
        if "json" in cm:
            return json.loads(Path(self._resolve(cm["json"])).read_text())
        if "python" in cm:
            mod_name, attr = cm["python"].split(":")
            return dict(getattr(importlib.import_module(mod_name), attr))
        raise TargetError("target %s: unknown class_map spec" % self.name)

    @property
    def covers_map(self):
        """action -> the acts that record kind COVERS, declared BY THE TARGET
        (design/10 §11.4a). Read as data, the same way the class map is: the class
        map says what a record IS, this says what it is ABOUT, and both are the
        target's own vocabulary rather than the instrument's.

        Two declarations carry meaning beyond a list of calls. An EMPTY list says
        the kind is about no act any caller made — the port's own bookkeeping —
        and it is attributed to no row. `"*"` says the kind is about whatever act
        was under test and names it in its own payload, which is the shape of a
        gate refusal.
        """
        cm = self.spec.get("covers_map")
        if not cm:
            return None
        if "inline" in cm:
            return dict(cm["inline"])
        if "json" in cm:
            return json.loads(Path(self._resolve(cm["json"])).read_text())
        if "python" in cm:
            mod_name, attr = cm["python"].split(":")
            return dict(getattr(importlib.import_module(mod_name), attr))
        raise TargetError("target %s: unknown covers_map spec" % self.name)

    @property
    def replayer(self):
        return Replayer(self.spec.get("replay"))

    def _resolve(self, p):
        p = os.path.expanduser(p)
        return p if os.path.isabs(p) else str((self.base_dir / p).resolve())
