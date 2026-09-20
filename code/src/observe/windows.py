# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""M1 W1 — the five windows: the read-only Linux facilities the record machine watches.

Each window is a thin typed adapter: it opens ONE facility, reports its own availability and
its own version, yields Observations (seam.py), and STATES WHAT IT CANNOT SEE. It holds no
authority, appends nothing, and knows nothing about the gate.

WINDOW@VERSION — what the version pins, and why it is not decoration. Two things move
underneath a window and either one changes what a record means: the kernel that serves the
facility, and the adapter contract that reads it. Both ride in one string,
`<contract>-<route>+<kernel release>`, so `file@m1.1-inotify+7.0.0-28-generic` says exactly
which reading produced the record. A window with two routes (the device window's sysfs scan
and its uevent socket) reports a DIFFERENT version per route, because they are different
readings of the same subject — which is the whole point of pinning the version and not just
the name.

COVERAGE IS STATED, NEVER IMPLIED (planning/11 §2, `03 §1.5`). Every window declares
`does_not_see` in its own words, and the shadow views carry it into their answers. The
coverage-completeness QUESTION — is this combination enough — is the owner's calibration
with an evidence step (the coverage audit); this module's job is to make it MEASURABLE, never
to declare it sufficient.

TRAINED KNOWLEDGE, FLAGGED (Estimate — High), and dated: every Linux facility named here —
/proc, /proc/self/mountinfo, inotify, netlink sock_diag, netlink uevents, sysfs — is trained
knowledge about the stable Linux user-space interface, not read from kernel source
(clean-room law). Availability is MEASURED at open time on the box the adapter runs on, never
assumed: a facility that will not open is a DEFERRED window carrying its observed reason.
"""

import ctypes
import datetime
import os
import select
import socket
import struct
from collections.abc import Mapping

from .seam import Observation, TIME_SUBMISSION_SUBSTITUTED, TIME_WINDOW_REPORTED

#: The adapter read-contract version. Bump when a window changes WHAT IT READS or HOW it maps
#: what it reads onto acts — records either side of a bump are not comparable without saying so.
CONTRACT = "m1.1"


def kernel_release():
    """The kernel serving these facilities. Read from /proc, not from `platform`, so the
    version pin names the same source the windows themselves read."""
    try:
        with open("/proc/sys/kernel/osrelease", "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "unknown"


def _version(route):
    return f"{CONTRACT}-{route}+{kernel_release()}"


def _iso(epoch_seconds):
    return datetime.datetime.fromtimestamp(epoch_seconds, datetime.timezone.utc).isoformat()


# =============================================================================================
# The window contract
# =============================================================================================

class Window:
    """The typed boundary. Subclasses implement `_snapshot`/`_events` and `coverage`."""

    name = None
    route = None

    def __init__(self, source=None):
        #: An injected reader makes a window deterministic under test without changing the
        #: code the box runs — the campaign-1 adapter discipline, carried forward.
        self._injected = source
        self._unavailable_reason = None
        self._probed = None

    # ---- identity ---------------------------------------------------------------------
    @property
    def version(self):
        return _version(self.route)

    def available(self):
        """(bool, reason). MEASURED, never assumed — once per window, then held: a window's
        availability is a property of the box, and re-probing it on every read would put a
        syscall on the observation path for an answer that does not move. An unavailable
        window is deferred with its observed reason and raised — never quietly skipped, and
        never chased by reconfiguring the box (that is outside this EP's fence)."""
        if self._injected is not None:
            return True, "injected source"
        if self._probed is None:
            self._probed = self._probe()
        return self._probed

    def _probe(self):
        return True, "ok"

    # ---- what it sees -----------------------------------------------------------------
    def coverage(self):
        """{'facility', 'sees', 'does_not_see'} — the window's own statement of its blind
        spots. Carried into every shadow view's answer."""
        raise NotImplementedError

    def read(self):
        """Yield the Observations since the last read. Returns [] when unavailable."""
        raise NotImplementedError

    def live_state(self):
        """The window's view of the box's CURRENT state, read fresh. Used by the shadow
        views to check that they still track (T-SHADOW-TRACKS) — never to answer a query."""
        return {}

    def close(self):
        pass


class DiffWindow(Window):
    """A window whose facility reports STATE, so crossings are the diff of two snapshots.
    Process, mount, device and connection all read this way; only files get true events."""

    #: act names for the three diff directions; a subclass sets what it uses.
    act_appeared = None
    act_removed = None
    act_changed = None

    def __init__(self, source=None):
        super().__init__(source)
        self.prev = None

    def _snapshot(self):
        raise NotImplementedError

    def snapshot(self):
        if self._injected is not None:
            return self._injected()
        return self._snapshot()

    def live_state(self):
        ok, _ = self.available()
        return self.snapshot() if ok else {}

    # A subclass may override to report the facility's own time for one key.
    def _occurrence_for(self, key, attrs, act):
        return None, TIME_SUBMISSION_SUBSTITUTED

    def _object_for(self, key):
        return f"{self.name}:{key}"

    def _observe(self, act, key, attrs):
        when, source = self._occurrence_for(key, attrs, act)
        data = {"key": key}
        if isinstance(attrs, dict):
            data.update(attrs)
        data.setdefault("source", self.route)
        return Observation(window=self.name, window_version=self.version, act=act,
                           object=self._object_for(key), occurrence_time=when,
                           time_source=source, data=data,
                           principal=(attrs or {}).get("principal") if isinstance(attrs, dict) else None)

    def read(self):
        ok, reason = self.available()
        if not ok:
            self._unavailable_reason = reason
            return []
        cur = self.snapshot()
        out = []
        first = self.prev is None
        prev = self.prev or {}
        for key, attrs in cur.items():
            if key not in prev:
                out.append(self._observe(self.act_appeared, key, attrs))
            elif self.act_changed and prev[key] != attrs:
                out.append(self._observe(self.act_changed, key, attrs))
        if not first:
            for key in prev:
                if key not in cur:
                    out.append(self._observe(self.act_removed, key, prev[key]))
        self.prev = cur
        return out


# =============================================================================================
# 1. The process window — /proc
# =============================================================================================

def _boot_time():
    try:
        with open("/proc/stat", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("btime "):
                    return int(line.split()[1])
    except OSError:
        pass
    return None


def _proc_start_epoch(pid, btime, hz):
    """The process's own start time, as /proc reports it: field 22 of /proc/<pid>/stat is
    start time in clock ticks since boot, and /proc/stat's `btime` anchors boot to the epoch.
    This is a genuinely WINDOW-REPORTED occurrence — the process began before we saw it, and
    the record says when it began, not when we looked (design/36 K7, the two times)."""
    if btime is None:
        return None
    try:
        with open(f"/proc/{pid}/stat", "r", encoding="utf-8") as f:
            line = f.read()
    except OSError:
        return None
    # comm sits in parentheses and may contain spaces and parens; everything after the LAST
    # ')' is the fixed-width tail starting at field 3 (state), so field 22 is index 19.
    tail = line[line.rfind(")") + 2:].split()
    if len(tail) < 20:
        return None
    try:
        return btime + int(tail[19]) / hz
    except (ValueError, ZeroDivisionError):
        return None


def scan_processes():
    """{pid: {comm, uid, start_epoch}} from /proc. A process that exits mid-scan is skipped —
    that race is normal and is named in this window's coverage."""
    btime, hz = _boot_time(), os.sysconf("SC_CLK_TCK")
    out = {}
    try:
        names = os.listdir("/proc")
    except OSError:
        return out
    for name in names:
        if not name.isdigit():
            continue
        pid = int(name)
        try:
            with open(f"/proc/{pid}/comm", "r", encoding="utf-8", errors="replace") as f:
                comm = f.read().strip()
            uid = os.stat(f"/proc/{pid}").st_uid
        except OSError:
            continue                      # exited between listdir and read — a normal race
        out[pid] = {"comm": comm, "uid": uid, "start_epoch": _proc_start_epoch(pid, btime, hz)}
    return out


class ProcessWindow(DiffWindow):
    name = "process"
    route = "proc"
    #: The Linux host facility this window reads. STATIC descriptor (not probed) — read by the
    #: under-our-core census (seam.window_census) so the census names the facility a window
    #: reads WITHOUT opening it. The core presents no such facility (L1), which is why the
    #: census settles this window re-sourced-from-the-core or absent, never by reading here.
    host_facility = "/proc (directory scan, polled)"
    act_appeared = "process-created"
    act_removed = "process-exited"
    act_changed = "process-credentials-changed"

    def _probe(self):
        if not os.path.isdir("/proc"):
            return False, "no /proc on this platform"
        return True, "ok"

    def _snapshot(self):
        return scan_processes()

    def _object_for(self, key):
        return f"proc:{key}"

    def _occurrence_for(self, key, attrs, act):
        start = (attrs or {}).get("start_epoch") if isinstance(attrs, dict) else None
        if act == self.act_appeared and start:
            return _iso(start), TIME_WINDOW_REPORTED
        # An exit has no reported time in /proc — the entry is simply gone. Submission time
        # stands in AND SAYS SO (RAISED-BY-DESIGN 4), so EP-26 knows which times are which.
        return None, TIME_SUBMISSION_SUBSTITUTED

    def _observe(self, act, key, attrs):
        obs = super()._observe(act, key, attrs)
        if isinstance(attrs, dict) and attrs.get("uid") is not None:
            obs.principal = f"uid:{attrs['uid']}"       # K6: the uid is EVIDENCE, not an actor
        return obs

    def coverage(self):
        return {
            "facility": "/proc (directory scan, polled)",
            "sees": ["a process that exists at one poll and not the next, in either direction",
                     "the comm and owning uid /proc reports",
                     "the process's own start time (window-reported occurrence)"],
            "does_not_see": [
                "any process that both starts and exits between two polls — the poll cadence "
                "IS the granularity, and it is not a sample of a stream but a gap in the record",
                "exec and credential changes as distinct crossings (only their visible effect "
                "on comm/uid, at the next poll)",
                "the exit's own time — /proc reports none, so those records carry a marked "
                "submission-time substitution",
                "anything inside a process (memory writes, futex words) — permanently and "
                "honestly out of audit reach, not an M1 gap",
                "the fork/exec/exit connector's per-event stream: the netlink proc connector "
                "binds but delivers no events to an unprivileged observer on this host "
                "(measured), so that route is DEFERRED with its reason",
            ],
        }


# =============================================================================================
# 2. The file window — inotify
# =============================================================================================

IN_ACCESS, IN_MODIFY, IN_ATTRIB = 0x001, 0x002, 0x004
IN_CLOSE_WRITE, IN_CLOSE_NOWRITE, IN_OPEN = 0x008, 0x010, 0x020
IN_MOVED_FROM, IN_MOVED_TO, IN_CREATE, IN_DELETE = 0x040, 0x080, 0x100, 0x200
IN_NONBLOCK = 0o4000

#: The mask this window subscribes to, and the act each bit becomes. The CACHE/STREAM bits
#: are subscribed DELIBERATELY: a window that only asked for the recordable events could not
#: prove it classifies the rest OUT, and that proof is exactly T-RATE-GOVERNANCE.
INOTIFY_ACTS = (
    (IN_CREATE, "file-created"),
    (IN_DELETE, "file-removed"),
    (IN_MODIFY, "file-modified"),
    (IN_CLOSE_WRITE, "file-closed-write"),
    (IN_ATTRIB, "file-attr-changed"),
    (IN_MOVED_FROM, "file-moved-from"),
    (IN_MOVED_TO, "file-moved-to"),
    (IN_OPEN, "file-opened"),
    (IN_CLOSE_NOWRITE, "file-closed-noswrite"),
    (IN_ACCESS, "file-read"),
)
INOTIFY_MASK = 0
for _bit, _act in INOTIFY_ACTS:
    INOTIFY_MASK |= _bit


class FileWindow(Window):
    """inotify. The one window whose facility reports EVENTS rather than state, so it sees
    crossings the poll-based windows cannot — and, for the same reason, it sees the reads and
    opens that the class map drops. fanotify is the stage spec's first choice and its mark
    requires a privilege this observer does not hold (measured at open); inotify is the spec's
    own named alternative, and the version string says which route read the record."""

    name = "file"
    route = "inotify"
    #: STATIC host-facility descriptor for the census (see ProcessWindow.host_facility).
    host_facility = "inotify"

    def __init__(self, paths=(), source=None, exclude=()):
        super().__init__(source)
        self.paths = list(paths)
        #: THE OBSERVER'S OWN FOOTPRINT, EXCLUDED AND DECLARED. Found while driving this
        #: window against a real box: if a watched directory contains AWIG OS's own record
        #: file, then every append modifies a watched file, the window sees it, and the
        #: observation of the append is itself an append — the act of recording becomes the
        #: thing recorded, and the record inflates with its own writing. The exclusion is a
        #: DECLARED blind spot carried in this window's coverage statement, never a silent
        #: filter, because a reader must be able to see that the audit does not audit itself.
        #: (The same self-reference returns with teeth at EP-25, where the mount IS the
        #: record — raised there, not resolved here.)
        self.exclude = [os.path.abspath(p) for p in exclude]
        self.excluded_events = 0
        self._fd = None
        self._wd = {}
        self._libc = None

    def _is_excluded(self, path):
        ap = os.path.abspath(path)
        return any(ap == x or ap.startswith(x.rstrip(os.sep) + os.sep) for x in self.exclude)

    def _probe(self):
        try:
            libc = ctypes.CDLL("libc.so.6", use_errno=True)
        except OSError as exc:
            return False, f"libc not loadable for the inotify syscalls: {exc}"
        fd = libc.inotify_init1(IN_NONBLOCK)
        if fd < 0:
            err = ctypes.get_errno()
            return False, f"inotify_init1 failed: {os.strerror(err)}"
        os.close(fd)
        return True, "ok"

    @staticmethod
    def fanotify_available():
        """Measured, so the deferral of the stage spec's first-choice route is a fact with a
        reason and not a preference."""
        try:
            libc = ctypes.CDLL("libc.so.6", use_errno=True)
        except OSError as exc:
            return False, str(exc)
        fd = libc.fanotify_init(0x00000001, 0o2)     # FAN_CLASS_NOTIF, O_RDONLY
        if fd < 0:
            return False, os.strerror(ctypes.get_errno())
        os.close(fd)
        return True, "ok"

    def open(self):
        if self._injected is not None or self._fd is not None:
            return self
        self._libc = ctypes.CDLL("libc.so.6", use_errno=True)
        fd = self._libc.inotify_init1(IN_NONBLOCK)
        if fd < 0:
            raise OSError(ctypes.get_errno(), "inotify_init1")
        self._fd = fd
        for p in self.paths:
            self.watch(p)
        return self

    def watch(self, path):
        if self._fd is None:
            self.open()
        wd = self._libc.inotify_add_watch(self._fd, os.fsencode(path), INOTIFY_MASK)
        if wd < 0:
            raise OSError(ctypes.get_errno(), f"inotify_add_watch {path}")
        self._wd[wd] = path
        if path not in self.paths:
            self.paths.append(path)
        return wd

    def close(self):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
            self._wd = {}

    def _raw_events(self):
        """(wd, mask, name) tuples currently queued. Non-blocking: an empty queue is not an
        error, it is a quiet box."""
        if self._fd is None:
            return []
        out = []
        while True:
            r, _, _ = select.select([self._fd], [], [], 0)
            if not r:
                return out
            try:
                buf = os.read(self._fd, 65536)
            except BlockingIOError:
                return out
            off = 0
            while off + 16 <= len(buf):
                wd, mask, _cookie, ln = struct.unpack_from("=iIII", buf, off)
                off += 16
                name = buf[off:off + ln].split(b"\x00", 1)[0].decode("utf-8", "replace")
                off += ln
                out.append((wd, mask, name))

    def read(self):
        ok, reason = self.available()
        if not ok:
            self._unavailable_reason = reason
            return []
        if self._injected is None and self._fd is None and self.paths:
            self.open()
        raw = self._injected() if self._injected is not None else self._raw_events()
        out = []
        for wd, mask, name in raw:
            base = self._wd.get(wd, self.paths[0] if self.paths else "")
            path = os.path.join(base, name) if name else base
            if self._is_excluded(path):
                self.excluded_events += 1      # counted, so the blind spot is measurable
                continue
            for bit, act in INOTIFY_ACTS:
                if not mask & bit:
                    continue
                when, src = self._occurrence(path, act)
                out.append(Observation(
                    window=self.name, window_version=self.version, act=act,
                    object=f"file:{path}", occurrence_time=when, time_source=src,
                    data={"path": path, "watch": base, "mask": mask, "source": self.route}))
        return out

    @staticmethod
    def _occurrence(path, act):
        """inotify carries no timestamp. For an act that leaves the file present, the
        filesystem's own mtime IS the window-reported occurrence; for a removal there is
        nothing left to ask, so submission time stands in and is marked."""
        if act in ("file-removed", "file-moved-from"):
            return None, TIME_SUBMISSION_SUBSTITUTED
        try:
            st = os.stat(path)
        except OSError:
            return None, TIME_SUBMISSION_SUBSTITUTED
        return _iso(st.st_mtime), TIME_WINDOW_REPORTED

    def live_state(self):
        out = {}
        for base in self.paths:
            for root, _dirs, files in os.walk(base):
                for nm in files:
                    fp = os.path.join(root, nm)
                    if self._is_excluded(fp):
                        continue
                    try:
                        st = os.stat(fp)
                    except OSError:
                        continue
                    out[fp] = {"size": st.st_size, "mtime": int(st.st_mtime)}
        return out

    def coverage(self):
        fan_ok, fan_reason = self.fanotify_available()
        excluded = [
            f"the observer's own artifacts at {self.exclude} — excluded so that the act of "
            f"recording does not become the thing recorded ({self.excluded_events} event(s) "
            "dropped by this exclusion so far). A DECLARED blind spot: the audit does not "
            "audit its own writing, and says so"
        ] if self.exclude else []
        return {
            "facility": f"inotify on {self.paths or '(no watch installed)'}",
            "sees": ["create, delete, modify, close-after-write, attribute change and rename "
                     "under the installed watches",
                     "opens and reads, which it classifies OUT (CACHE / STREAM) rather than "
                     "not seeing — the drop is a decision, and it is counted"],
            "does_not_see": [
                "anything outside the installed watches — this window's reach IS its watch list",
                "subdirectories created after the watch, unless a watch is installed on them "
                "(inotify is not recursive)",
                "which actor wrote: inotify names the path and the event, never the writer, so "
                "no observed principal is recorded here and none is guessed",
                "the event's own time — inotify reports none, so occurrence comes from the "
                "file's mtime where the file still exists and is a MARKED substitution where "
                "it does not",
                "events dropped by an overflowed kernel queue under load (IN_Q_OVERFLOW); the "
                "loss would be silent to this reader, which is why file history states its "
                "coverage rather than claiming completeness",
                f"the stage spec's first-choice route: fanotify is unavailable here ({fan_reason}) "
                "— DEFERRED with its measured reason, not chased",
            ] + excluded,
        }


# =============================================================================================
# 2a. The file window RE-SOURCED FROM THE RECORD (C7-MAINT-FILE-WINDOW-FROM-RECORD)
# =============================================================================================
#
# Under our core there is no inotify to open — the governance core presents no host facility
# (L1 / the P1 seam-census finding). But a file change under our core IS a recorded write act:
# the body's writable surface is EXACTLY the seam's declared write acts (append a record,
# write-once a file by temp-and-swap, declare a directory, remove, the writer's lock — L21),
# and every one of them lands in the record itself. So the file window's route under our core
# is THE RECORD: it reads the record's OWN write-act entries and yields file-change
# observations from them, its version string naming the record route (never inotify). The
# inotify FileWindow above is the HOST reader C7 is moving off of; this is the same "file"
# observation surface, RE-SOURCED from the core's own state (B10). No Linux facility is added
# to the body — the window reads the record the body already serves (L21).
#
# THE SELF-AUDIT EXCLUSION, INVERTED FOR THE RECORD SOURCE. FileWindow above excludes the
# observer's own artifact PATH so that observing an append does not become an append that is
# then observed. The record-sourced window carries the SAME concern from the other side: its
# OWN observations, once submitted, append `observed-file` records to the record; were it to
# read those back as write acts it would observe its own observation-writes and the record
# would inflate on every read. So it excludes its own observation-writes (the `observed-file`
# records) from the write acts it reads — a DECLARED, COUNTED blind spot, so a reader sees
# that the audit does not audit its own writing.

RECORD_ROUTE = "record"
OBSERVED_FILE_KIND = "observed-file"


class RecordFileWindow(FileWindow):
    """The file window RE-SOURCED FROM THE RECORD. It opens no host facility: its source is
    the record's own write-act entries, read through a caller-supplied read-only reader. Each
    write act appended to the record since the last read is a file change under our core, and
    the window yields it as a file-change observation whose version names the record route and
    whose data carries the record seq it traces to (so a fabricated observation with no
    matching write act does not trace). Its own observation-writes are excluded (the inverted
    self-audit exclusion), so reading does not inflate the record with observations of itself."""

    name = "file"
    route = RECORD_ROUTE
    #: This window reads the record, not a Linux facility. It carries no host-facility
    #: descriptor because the census settles it RE-SOURCED (a core route), never absent.
    host_facility = None

    def __init__(self, record_reader=None, record_name="the-record", source=None):
        # No inotify paths and no watches — the source is the record, never a host facility.
        super().__init__(paths=(), source=source, exclude=())
        #: A read-only reader over the record's committed entries: a callable returning the
        #: list of record dicts (each with 'seq' and, for the observer's own writes, a
        #: 'payload.kind'). The window NEVER appends — reading the record is not writing it.
        self._record_reader = record_reader
        self._record_name = record_name
        #: The highest record seq already yielded, so each read yields only NEW write acts.
        self._last_seq = 0

    # ---- availability: the record is the source, not a facility to probe -----------------
    def _probe(self):
        if self._record_reader is None and self._injected is None:
            return False, "no record reader wired to the file window (route %r)" % self.route
        return True, "ok"

    def _entries(self):
        if self._injected is not None:
            return list(self._injected() or [])
        if self._record_reader is None:
            return []
        return list(self._record_reader() or [])

    @staticmethod
    def is_own_observation_write(entry):
        """THE INVERTED SELF-AUDIT EXCLUSION. The window's own observation-writes are the
        `observed-file` records it produced; reading them back as write acts is what would
        make the audit audit itself, so they are excluded (and counted, and declared)."""
        payload = entry.get("payload") if isinstance(entry, Mapping) else None
        return isinstance(payload, Mapping) and payload.get("kind") == OBSERVED_FILE_KIND

    def read(self):
        ok, reason = self.available()
        if not ok:
            self._unavailable_reason = reason
            return []
        out = []
        high = self._last_seq
        for entry in self._entries():
            seq = entry.get("seq") if isinstance(entry, Mapping) else None
            if seq is None or seq <= self._last_seq:
                continue                       # only NEW write acts since the last read
            if seq > high:
                high = seq
            if self.is_own_observation_write(entry):
                self.excluded_events += 1      # counted, so the blind spot is measurable
                continue
            when, src = self._occurrence_from_record(entry)
            out.append(Observation(
                window=self.name, window_version=self.version,
                act="file-modified",           # every write act GROWS the append-only record
                object="file:%s" % self._record_name,
                occurrence_time=when, time_source=src,
                data={"path": self._record_name, "record_seq": seq,
                      "record_action": entry.get("action"), "source": self.route}))
        self._last_seq = high
        return out

    @staticmethod
    def _occurrence_from_record(entry):
        # The write act's own recorded time IS the window-reported occurrence — the record
        # carries it (record_time), so unlike inotify this window never has to substitute.
        rt = entry.get("record_time") if isinstance(entry, Mapping) else None
        if rt:
            return rt, TIME_WINDOW_REPORTED
        return None, TIME_SUBMISSION_SUBSTITUTED

    def open(self):
        # The record window opens no descriptor; availability is the reader, not a syscall.
        return self

    def close(self):
        pass

    def coverage(self):
        return {
            "facility": "the record's own write acts (route %r; NOT a host facility)" % self.route,
            "sees": [
                "every write act appended to the record since the last read — a file change "
                "under our core IS a recorded write act (append, write-once, declare, remove, "
                "the writer's lock; L21), read from the record and never from inotify",
                "each observation traces to a real record entry by its seq, so it cannot be a "
                "fabricated event",
            ],
            "does_not_see": [
                "the window's OWN observation-writes (the %r records it produced): excluded so "
                "the act of recording does not become the thing recorded — the audit does not "
                "audit its own writing (%d event(s) dropped by this exclusion so far). The "
                "self-audit exclusion inverted for the record source, DECLARED and never silent"
                % (OBSERVED_FILE_KIND, self.excluded_events),
                "any change the record never captured — this window's reach IS the record; a "
                "write that did not become a record is outside it, honestly and by construction",
            ],
        }


# =============================================================================================
# 3. The mount window — /proc/self/mountinfo
# =============================================================================================

def scan_mountinfo():
    """{mount point: {source, fstype, options, mount_id}} from /proc/self/mountinfo, which
    carries the mount id and the propagation/attribute fields /proc/mounts drops."""
    out = {}
    try:
        with open("/proc/self/mountinfo", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 10 or "-" not in parts:
                    continue
                sep = parts.index("-")
                mount_point = parts[4].replace("\\040", " ")
                out[mount_point] = {"mount_id": parts[0], "options": parts[5],
                                    "fstype": parts[sep + 1],
                                    "source": parts[sep + 2] if len(parts) > sep + 2 else None}
    except OSError:
        pass
    return out


class MountWindow(DiffWindow):
    name = "mount"
    route = "mountinfo"
    #: STATIC host-facility descriptor for the census (see ProcessWindow.host_facility).
    host_facility = "/proc/self/mountinfo"
    act_appeared = "mount-added"
    act_removed = "mount-removed"
    act_changed = "mount-attr-changed"

    def _probe(self):
        if not os.path.exists("/proc/self/mountinfo"):
            return False, "no /proc/self/mountinfo on this platform"
        return True, "ok"

    def _snapshot(self):
        return scan_mountinfo()

    def _object_for(self, key):
        return f"mount:{key}"

    def notified(self, timeout=0):
        """The mount NOTIFICATION the stage spec names: /proc/self/mountinfo becomes
        POLLPRI-readable when the mount table changes, so the window need not poll blind."""
        try:
            with open("/proc/self/mountinfo", "rb") as f:
                p = select.poll()
                p.register(f.fileno(), select.POLLPRI | select.POLLERR)
                return bool(p.poll(timeout * 1000))
        except OSError:
            return False

    def coverage(self):
        return {
            "facility": "/proc/self/mountinfo (POLLPRI notification + parse)",
            "sees": ["a mount appearing, disappearing, or changing its options/propagation, "
                     "in THIS mount namespace"],
            "does_not_see": [
                "mounts in other mount namespaces — the file is the observer's own view, and "
                "a container's private mounts are outside it",
                "who mounted it, or under what authority: mountinfo names no actor",
                "the mount's own time — none is reported, so every mount record carries a "
                "marked submission-time substitution",
                "a mount that appears and disappears between two reads",
            ],
        }


# =============================================================================================
# 4. The device window — sysfs (+ the uevent socket as a second route)
# =============================================================================================

NETLINK_KOBJECT_UEVENT = 15


def scan_devices():
    """{devpath: {subsystem, driver}} from /sys/bus/*/devices. A device present under a bus IS
    the capability; the `driver` symlink IS the binding — so the two crossings planning/11
    names (capability appearing = LAW, bind = DECISION) are both readable here."""
    out = {}
    bus_root = "/sys/bus"
    try:
        buses = os.listdir(bus_root)
    except OSError:
        return out
    for bus in buses:
        devdir = os.path.join(bus_root, bus, "devices")
        try:
            names = os.listdir(devdir)
        except OSError:
            continue
        for name in names:
            link = os.path.join(devdir, name, "driver")
            driver = None
            try:
                driver = os.path.basename(os.readlink(link))
            except OSError:
                pass
            out[f"{bus}/{name}"] = {"subsystem": bus, "driver": driver}
    return out


class DeviceWindow(DiffWindow):
    """sysfs scan. The diff carries BOTH device crossings, and they are different classes:
    a device appearing or leaving is a capability change (LAW); a driver binding or releasing
    is a bind decision (DECISION). So `_observe` is overridden to pick the act from WHAT
    CHANGED rather than from the diff direction alone."""

    name = "device"
    route = "sysfs"
    #: STATIC host-facility descriptor for the census (see ProcessWindow.host_facility).
    host_facility = "/sys/bus/*/devices scan (+ the netlink uevent socket, second route)"
    act_appeared = "device-capability-registered"
    act_removed = "device-capability-removed"
    act_changed = "device-bound"          # refined per-change in read(), below

    def _probe(self):
        if not os.path.isdir("/sys/bus"):
            return False, "no /sys/bus on this platform"
        return True, "ok"

    def _snapshot(self):
        return scan_devices()

    def _object_for(self, key):
        return f"device:{key}"

    def read(self):
        out = super().read()
        # A `changed` row is a driver bind or unbind; which one is read from the driver
        # field, never guessed. The base class emitted `device-bound`; correct an unbind.
        for obs in out:
            if obs.act == "device-bound" and obs.data.get("driver") is None:
                obs.act = "device-unbound"
        return out

    def coverage(self):
        return {
            "facility": "/sys/bus/*/devices (scan)",
            "sees": ["a device appearing or leaving a bus (its capability)",
                     "a driver binding to or releasing a device (the bind)"],
            "does_not_see": [
                "devices with no bus entry — the class-only and platform-implicit devices",
                "interrupts, I/O completions and device traffic: those are the INPUT/STREAM "
                "classes, whose window needs tracepoints and is DEFERRED (see ArrivalWindow)",
                "the crossing's own time — sysfs reports none, so every device record carries "
                "a marked submission-time substitution",
                "hotplug between two scans; the uevent socket is the live route and its "
                "availability is reported separately",
            ],
        }


class UeventSource(Window):
    """The device window's SECOND route: the kernel's uevent multicast. Same window, different
    reading, therefore a different version string — which is what pinning window@version is
    for. A quiescent box emits nothing here, so this route adds freshness, never coverage."""

    name = "device"
    route = "uevent"

    def __init__(self, source=None):
        super().__init__(source)
        self._sock = None

    def _probe(self):
        try:
            s = socket.socket(socket.AF_NETLINK, socket.SOCK_DGRAM, NETLINK_KOBJECT_UEVENT)
            s.bind((0, 1))
            s.close()
            return True, "ok"
        except OSError as exc:
            return False, f"netlink uevent bind failed: {exc}"

    def open(self):
        if self._sock is None and self._injected is None:
            s = socket.socket(socket.AF_NETLINK, socket.SOCK_DGRAM, NETLINK_KOBJECT_UEVENT)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)
            s.bind((0, 1))
            s.setblocking(False)
            self._sock = s
        return self

    def close(self):
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    _ACTS = {"add": "device-capability-registered", "remove": "device-capability-removed",
             "bind": "device-bound", "unbind": "device-unbound"}

    def _drain(self):
        out = []
        if self._sock is None:
            return out
        while True:
            r, _, _ = select.select([self._sock], [], [], 0)
            if not r:
                return out
            try:
                buf = self._sock.recv(65536)
            except BlockingIOError:
                return out
            fields = {}
            for token in buf.split(b"\x00"):
                if b"=" in token:
                    k, v = token.split(b"=", 1)
                    fields[k.decode("utf-8", "replace")] = v.decode("utf-8", "replace")
            if fields:
                out.append(fields)

    def read(self):
        ok, reason = self.available()
        if not ok:
            self._unavailable_reason = reason
            return []
        raw = self._injected() if self._injected is not None else self._drain()
        out = []
        for fields in raw:
            act = self._ACTS.get(fields.get("ACTION"))
            if act is None:
                continue          # `change` and the rest: state reads, not crossings
            devpath = fields.get("DEVPATH", "?")
            out.append(Observation(
                window=self.name, window_version=self.version, act=act,
                object=f"device:{devpath}", occurrence_time=None,
                time_source=TIME_SUBMISSION_SUBSTITUTED,
                data={"devpath": devpath, "subsystem": fields.get("SUBSYSTEM"),
                      "seqnum": fields.get("SEQNUM"), "source": self.route}))
        return out

    def coverage(self):
        return {
            "facility": "netlink NETLINK_KOBJECT_UEVENT (kernel group)",
            "sees": ["add / remove / bind / unbind announcements as the kernel emits them"],
            "does_not_see": [
                "anything on a quiescent box — this route reports change, never state, so it "
                "adds freshness to the sysfs scan and no coverage of its own",
                "the crossing's own time — uevents carry a sequence number, not a timestamp",
                "events emitted before this socket was bound",
            ],
        }


# =============================================================================================
# 4a. The device window RE-SOURCED FROM THE RECORD (C7 P7b — the device drivers)
# =============================================================================================
#
# Under our core there is no /sys/bus to scan and no uevent socket to bind — the governance core
# presents no host facility (L1 / the P1 seam-census finding). But the freestanding body DISCOVERS
# each device it performs at bring-up — its OWN block (ata), network (the NIC self-check) and clock
# (the RTC) drivers — and RECORDS one discovery row per device, each riding the record-pen act (C7
# P7b, the body-lane emitter). So the device window's route under our core is THE RECORD: it reads
# the discovery rows the body wrote and yields a device observation per discovered device, its
# version string naming the record route (never sysfs). The sysfs DeviceWindow above is the HOST
# reader C7 is moving off of; this is the same "device" observation surface, RE-SOURCED from the
# core's own state (B10). No Linux facility is added to the body — the window reads the record the
# body already serves (L21). It mirrors RecordFileWindow (the file-window re-source precedent).
#
# WHAT THE ROW HOLDS IS WHAT THE BODY EXPORTS AT BRING-UP (the archi :4605 precision). The block
# row is ata_present's verdict; the network row is the wire self-check's class (PASS/ABSENT/FAIL)
# plus the MAC net_nic_bringup exports — NEVER the file-static PCI vendor/device id, slot or BAR
# (net.c keeps those static and never exports them; re-probing them would edit a driver or add a
# parallel probe). The clock row is the RTC's presence + its epoch. This window reads whatever the
# body recorded; it invents no identity of its own.
#
# THE SELF-AUDIT EXCLUSION, INVERTED FOR THE RECORD SOURCE (as RecordFileWindow). Its own
# observations, once submitted, append `observed-device` records to the record; it excludes those
# from the discovery rows it reads, so reading does not inflate the record with observations of
# itself — a DECLARED, COUNTED blind spot, so a reader sees the audit does not audit its own writing.

DEVICE_DISCOVERY_KIND = "device-discovery"
OBSERVED_DEVICE_KIND = "observed-device"


class RecordDeviceWindow(DeviceWindow):
    """The device window RE-SOURCED FROM THE RECORD. It opens no host facility: its source is the
    body's device-discovery rows (C7 P7b), read through a caller-supplied read-only reader. Each
    discovery row the body wrote at bring-up is a device under our core, and the window yields it as
    a device observation whose version names the record route and whose data carries the discovery
    row's seq (so a fabricated observation with no matching discovery row does not trace). Its own
    observation-writes are excluded (the inverted self-audit exclusion), so reading does not inflate
    the record with observations of itself."""

    name = "device"
    route = RECORD_ROUTE
    #: This window reads the record's discovery rows, not a Linux facility. It carries no
    #: host-facility descriptor because the census settles it RE-SOURCED (a core route), never absent.
    host_facility = None

    def __init__(self, record_reader=None, record_name="the-record", source=None):
        # No sysfs scan and no uevent socket — the source is the record, never a host facility.
        super().__init__(source=source)
        #: A read-only reader over the record's committed entries: a callable returning the list of
        #: record dicts (each with 'seq' and, for a discovery row, a 'payload.kind' of
        #: DEVICE_DISCOVERY_KIND). The window NEVER appends — reading the record is not writing it.
        self._record_reader = record_reader
        self._record_name = record_name
        #: The highest record seq already yielded, so each read yields only NEW discovery rows.
        self._last_seq = 0
        #: Own observation-writes dropped by the inverted self-audit exclusion (counted, declared).
        self.excluded_events = 0

    # ---- availability: the record is the source, not a facility to probe -----------------
    def _probe(self):
        if self._record_reader is None and self._injected is None:
            return False, "no record reader wired to the device window (route %r)" % self.route
        return True, "ok"

    def _entries(self):
        if self._injected is not None:
            return list(self._injected() or [])
        if self._record_reader is None:
            return []
        return list(self._record_reader() or [])

    @staticmethod
    def is_own_observation_write(entry):
        """THE INVERTED SELF-AUDIT EXCLUSION. The window's own observation-writes are the
        `observed-device` records it produced; reading them back as discovery rows is what would
        make the audit audit itself, so they are excluded (counted, declared)."""
        payload = entry.get("payload") if isinstance(entry, Mapping) else None
        return isinstance(payload, Mapping) and payload.get("kind") == OBSERVED_DEVICE_KIND

    @staticmethod
    def is_discovery_row(entry):
        """A device-discovery row the body wrote at bring-up — the window's ONLY source. A record
        entry that is not a discovery row (an ordinary act, a self-check row) is not a device."""
        payload = entry.get("payload") if isinstance(entry, Mapping) else None
        return isinstance(payload, Mapping) and payload.get("kind") == DEVICE_DISCOVERY_KIND

    def read(self):
        ok, reason = self.available()
        if not ok:
            self._unavailable_reason = reason
            return []
        out = []
        high = self._last_seq
        for entry in self._entries():
            seq = entry.get("seq") if isinstance(entry, Mapping) else None
            if seq is None or seq <= self._last_seq:
                continue                       # only NEW discovery rows since the last read
            if seq > high:
                high = seq
            if self.is_own_observation_write(entry):
                self.excluded_events += 1      # counted, so the blind spot is measurable
                continue
            if not self.is_discovery_row(entry):
                continue                       # a non-discovery record is not a device
            payload = entry.get("payload") or {}
            device = payload.get("device")
            present = bool(payload.get("present"))
            # A discovered device that the probe found present is a capability under our core; one
            # the probe found ABSENT is a capability the body performs over but does not have — read
            # from the row's own `present`, never guessed (mirrors DeviceWindow's per-change act pick).
            act = self.act_appeared if present else self.act_removed
            when, src = self._occurrence_from_record(entry)
            out.append(Observation(
                window=self.name, window_version=self.version, act=act,
                object="device:%s" % device,
                occurrence_time=when, time_source=src,
                data={"device": device, "present": present, "record_seq": seq,
                      "identity": payload.get("identity"), "source": self.route}))
        self._last_seq = high
        return out

    @staticmethod
    def _occurrence_from_record(entry):
        # The discovery row's own recorded time IS the window-reported occurrence — the record
        # carries it (record_time), so unlike sysfs this window never has to substitute.
        rt = entry.get("record_time") if isinstance(entry, Mapping) else None
        if rt:
            return rt, TIME_WINDOW_REPORTED
        return None, TIME_SUBMISSION_SUBSTITUTED

    def close(self):
        pass

    def coverage(self):
        return {
            "facility": "the body's own device-discovery rows (route %r; NOT a host facility)" % self.route,
            "sees": [
                "every device the body discovered at bring-up over the settled three-device list "
                "(block, network, clock; Q4 :3919) — each a discovery row the body recorded, read "
                "from the record and never from sysfs or the uevent socket",
                "each observation traces to a real discovery row by its seq, so it cannot be a "
                "fabricated event",
                "the identity the body EXPORTS for each device (the block verdict, the network "
                "self-check class + the offered MAC, the clock presence + epoch) — never the "
                "file-static PCI id/slot/BAR the driver keeps to itself",
            ],
            "does_not_see": [
                "the window's OWN observation-writes (the %r records it produced): excluded so the "
                "act of recording does not become the thing recorded — the audit does not audit its "
                "own writing (%d event(s) dropped by this exclusion so far). The self-audit "
                "exclusion inverted for the record source, DECLARED and never silent"
                % (OBSERVED_DEVICE_KIND, self.excluded_events),
                "any device the body never discovered a row for — this window's reach IS the "
                "record's discovery rows; a device outside the settled list is outside it, honestly "
                "and by construction",
                "device traffic, interrupts and I/O completions — those are the INPUT/STREAM classes "
                "(the deferred arrival window), never a discovery row",
            ],
        }


# =============================================================================================
# 5. The connection window — netlink sock_diag, with /proc/net as the declared fallback
# =============================================================================================

NETLINK_SOCK_DIAG = 4
SOCK_DIAG_BY_FAMILY = 20
NLM_F_REQUEST, NLM_F_DUMP = 0x001, 0x300
NLMSG_ERROR, NLMSG_DONE = 2, 3
TCP_STATES = {1: "ESTABLISHED", 2: "SYN_SENT", 3: "SYN_RECV", 4: "FIN_WAIT1", 5: "FIN_WAIT2",
              6: "TIME_WAIT", 7: "CLOSE", 8: "CLOSE_WAIT", 9: "LAST_ACK", 10: "LISTEN",
              11: "CLOSING"}


def _fmt_addr(family, raw):
    return socket.inet_ntop(family, raw[:4] if family == socket.AF_INET else raw)


def sock_diag_dump(family=socket.AF_INET, proto=socket.IPPROTO_TCP):
    """One inet_diag dump. Returns [{state, src, sport, dst, dport, uid, inode}].
    Layout is the stable netlink diag ABI (trained knowledge, Estimate — High)."""
    s = socket.socket(socket.AF_NETLINK, socket.SOCK_DGRAM, NETLINK_SOCK_DIAG)
    try:
        s.bind((0, 0))
        s.settimeout(2.0)
        req = struct.pack("=BBBBI", family, proto, 0, 0, 0xFFFFFFFF) + b"\x00" * 48
        hdr = struct.pack("=IHHII", 16 + len(req), SOCK_DIAG_BY_FAMILY,
                          NLM_F_REQUEST | NLM_F_DUMP, 1, 0)
        s.send(hdr + req)
        rows = []
        while True:
            buf = s.recv(1 << 16)
            off, done = 0, False
            while off + 16 <= len(buf):
                ln, typ, _flags, _seq, _pid = struct.unpack_from("=IHHII", buf, off)
                if ln < 16:
                    return rows
                if typ in (NLMSG_DONE, NLMSG_ERROR):
                    done = True
                    break
                body = off + 16
                fam, state = struct.unpack_from("=BB", buf, body)
                sport, dport = struct.unpack_from("!HH", buf, body + 4)
                src = buf[body + 8:body + 24]
                dst = buf[body + 24:body + 40]
                # inet_diag_msg: 4 (family/state/timer/retrans) + 48 (sockid) + expires,
                # rqueue, wqueue (4 each) puts uid at +64 and inode at +68.
                uid, inode = struct.unpack_from("=II", buf, body + 64)
                af = socket.AF_INET if fam == socket.AF_INET else socket.AF_INET6
                rows.append({"state": TCP_STATES.get(state, str(state)),
                             "src": _fmt_addr(af, src), "sport": sport,
                             "dst": _fmt_addr(af, dst), "dport": dport,
                             "uid": uid, "inode": inode})
                off += (ln + 3) & ~3
            if done:
                return rows
    finally:
        s.close()


def scan_connections_sock_diag():
    out = {}
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            rows = sock_diag_dump(family)
        except OSError:
            continue
        for r in rows:
            key = f"tcp:{r['src']}:{r['sport']}-{r['dst']}:{r['dport']}"
            out[key] = {"state": r["state"], "uid": r["uid"], "inode": r["inode"],
                        "principal": f"uid:{r['uid']}"}
    return out


def scan_connections_procnet():
    """The declared fallback route. Same subject, different reading — so a record read this
    way carries `connection@...-procnet+...`, not the sock_diag version."""
    out = {}
    for path, proto in (("/proc/net/tcp", "tcp"), ("/proc/net/tcp6", "tcp6")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()[1:]
        except OSError:
            continue
        for line in lines:
            p = line.split()
            if len(p) < 8:
                continue
            out[f"{proto}:{p[1]}-{p[2]}"] = {"state": TCP_STATES.get(int(p[3], 16), p[3]),
                                             "uid": int(p[7]), "principal": f"uid:{p[7]}"}
    return out


class ConnectionWindow(DiffWindow):
    name = "connection"
    #: STATIC host-facility descriptor for the census (see ProcessWindow.host_facility). The
    #: live `route` is probed (sock_diag vs procnet); this descriptor names the facility class
    #: WITHOUT probing, so the census reads it without opening a host facility.
    host_facility = "netlink sock_diag (/proc/net fallback)"
    act_appeared = "connection-opened"
    act_removed = "connection-closed"
    act_changed = "connection-state-changed"

    def __init__(self, source=None):
        super().__init__(source)
        self._route = None

    @property
    def route(self):
        if self._route is None:
            ok, _ = self._probe()
            self._route = "sock_diag" if ok else "procnet"
        return self._route

    def _probe(self):
        try:
            s = socket.socket(socket.AF_NETLINK, socket.SOCK_DGRAM, NETLINK_SOCK_DIAG)
            s.bind((0, 0))
            s.close()
            return True, "ok"
        except OSError as exc:
            if os.path.exists("/proc/net/tcp"):
                return False, f"netlink sock_diag unavailable ({exc}); /proc/net is the route"
            return False, f"neither netlink sock_diag nor /proc/net available: {exc}"

    def available(self):
        if self._injected is not None:
            return True, "injected source"
        if self._probed is None:
            ok, reason = self._probe()
            self._probed = (True, "ok") if ok else (os.path.exists("/proc/net/tcp"), reason)
        return self._probed

    def _snapshot(self):
        return scan_connections_sock_diag() if self.route == "sock_diag" else scan_connections_procnet()

    def _object_for(self, key):
        return f"conn:{key}"

    def coverage(self):
        return {
            "facility": f"netlink sock_diag (route in use: {self.route})",
            "sees": ["TCP endpoints appearing, changing state, and disappearing, with the "
                     "owning uid as observed evidence"],
            "does_not_see": [
                "the bytes on any connection — that is STREAM traffic and is classified out, "
                "never recorded",
                "UDP, unix-domain and packet sockets: this window dumps TCP only",
                "a connection that opens and closes between two reads",
                "the open's own time — the diag record carries none, so every connection "
                "record carries a marked submission-time substitution",
                "which ACCOUNT acted: the uid is recorded as evidence and is never resolved "
                "to an actor (K6 — resolution derives from recorded mapping acts, and at M1 "
                "there are none)",
            ],
        }


# =============================================================================================
# 6. The arrival window — DEFERRED, declared with its reason
# =============================================================================================

class ArrivalWindow(Window):
    """The INPUT class's window: interrupts, I/O completions, timer ticks (planning/11 §1's
    last two rows). It is DECLARED and DEFERRED, never silently absent — an audit that omits
    a class without saying so is the failure this whole EP exists to refuse."""

    name = "arrival"
    route = "tracepoints"

    #: The tracefs mount this window would read. `/sys/kernel/tracing` and the legacy
    #: `/sys/kernel/debug/tracing` are ONE filesystem — driven at the lab guest, stat device
    #: 12 inode 1 at both names — so naming either declares the same surface and nothing is
    #: lost by the choice. THIS one is named because it is the path where PRESENCE is
    #: establishable WITHOUT privilege: its parent `/sys/kernel` is traversable (0755), where
    #: debugfs's parent is 0700, and a probe whose only oracle is a path it cannot resolve
    #: can report neither absence nor presence honestly.
    #: It is an attribute rather than a literal so this method's three states can be DRIVEN
    #: at a constructed world; nothing in the estate rebinds it.
    tracefs_path = "/sys/kernel/tracing"

    def _probe(self):
        """THREE STATES, NEVER TWO, and the distinction is the whole of this method.

        `os.path.exists` — what this probe used to call — returns False for a TRAVERSAL
        DENIAL on a path that exists. Reading that False as absence converts an ACCESS
        result into a claim about the host's kernel and a configuration need: a view
        asserting what it did not measure, which is the one class this estate refuses.

        `os.stat` is called instead and ITS ERRNO IS READ. ENOENT/ENOTDIR is the kernel
        saying the path is not there. Anything else is THIS OBSERVER being refused, which
        leaves PRESENCE UNDETERMINED — and an undetermined presence is reported as
        undetermined, never as absent (the original defect) and never as present (the same
        defect inverted, which is this repair's own red world)."""
        path = self.tracefs_path
        try:
            os.stat(path)
        except (FileNotFoundError, NotADirectoryError) as exc:
            return False, (f"no {path} on this host — the kernel reports it not there "
                           f"(errno {exc.errno} {os.strerror(exc.errno)}, measured), so the "
                           "tracepoint and eBPF routes for interrupt/completion arrivals are "
                           "unavailable to this observer, and configuring the kernel for them "
                           "is outside this EP's fence")
        except OSError as exc:
            return False, (f"{path} could not be resolved by this observer: the path walk was "
                           f"refused (errno {exc.errno} {os.strerror(exc.errno)}, measured), "
                           "so WHETHER THE FACILITY IS THERE IS UNDETERMINED — this is an "
                           "access result about the observer and states nothing about the "
                           "host's kernel; the arrival routes stay DEFERRED")
        if not os.access(path, os.R_OK):
            return False, (f"{path} is present but not readable by this observer (measured) "
                           "— the arrival routes stay DEFERRED; kernel configuration is "
                           "outside this EP's fence")
        return True, "ok"

    def read(self):
        ok, reason = self.available()
        self._unavailable_reason = None if ok else reason
        return []                       # deferred: it yields nothing, and it says why

    def coverage(self):
        ok, reason = self.available()
        return {
            "facility": "eBPF / tracepoints (DEFERRED)",
            "sees": [],
            "does_not_see": [
                f"every INPUT-class arrival — interrupts, I/O completions, timer ticks: {reason}"
                if not ok else
                "nothing is subscribed: the route is open but this EP builds no arrival adapter",
                "consequently the INPUT class carries no M1 records, and no view claims it does",
            ],
        }


#: The M1 window set, in the order the stage spec lists them. `exclude` is the observer's own
#: footprint, declared out of the file window's reach (see FileWindow.__init__).
def default_windows(file_paths=(), exclude=()):
    return [ProcessWindow(), FileWindow(file_paths, exclude=exclude), MountWindow(),
            DeviceWindow(), ConnectionWindow(), ArrivalWindow()]
