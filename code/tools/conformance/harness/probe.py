# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: conformance-harness ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind; this file drives the documented
# system-call ABI and reports what it returned. Full declaration: SCOPE-STATEMENT.md.
"""The probe: the one program that drives a row's calls ON a target.

This file is SHIPPED to the target and run there (`python3 probe.py plan.json`),
by every transport, for every target kind. One program, both sides of the
differential oracle — a stock capture and a governed verify execute the same
bytes, so a difference in the result cannot be a difference in the driver
(DIGEST-C1 §3, the differential-oracle discipline).

It is stdlib-only and single-file on purpose: the target may be a bare cloud
image reached over ssh, and a harness that needs installing on the thing it
measures is a harness that changes it.

## The vocabulary IS the completeness guarantee (P3 applied)

`CALLS` below enumerates every call a row may name. A row naming a call that is
not in this table does not run — it is reported as `unknown-call` and counted,
never silently skipped. That is the estate's own registered-operation law
(DESIGN-SOUL P3: an unregistered op does not exist) applied to the instrument:
the table's enumeration is what makes the coverage statement trustworthy.

## What is observed, and what is deliberately not

Per design/10 §3 check 1, the ABI leg observes: the return value, the errno, the
visible ordering guarantee, and the process-visible side effect. Per design/10
§11.3 and §11.6, dynamic bytes and timing are NOT observed:

  - inode, device, uid, gid, link-count-of-the-fs, block counts, timestamps and
    free-space figures are reduced to their SHAPE (present/type), never their
    value;
  - no observation records a duration;
  - file descriptors are reported by their allocation ORDER within the row, not
    by their integer, except where a row asks for the lowest-free-descriptor
    guarantee explicitly (`fd_exact`).

Everything else — return values, errno names, byte counts, content hashes, mode
bits, the shape of the scratch tree after the row ran — is compared verbatim.
"""

import errno as errno_mod
import hashlib
import json
import os
import stat as stat_mod
import sys
import tempfile

PROBE_VERSION = "1"

# ---------------------------------------------------------------------------
# flag / mode resolution: rows name constants symbolically ("O_CREAT|O_EXCL")
# so a row never carries a numeric value that differs by architecture.
# ---------------------------------------------------------------------------

_CONST_MODULES = None


def _const_modules():
    global _CONST_MODULES
    if _CONST_MODULES is None:
        import fcntl as fcntl_mod

        _CONST_MODULES = (os, stat_mod, fcntl_mod, errno_mod)
    return _CONST_MODULES


def resolve_token(tok, binds):
    """One argument token -> a Python value.

    "$name"        a value bound by an earlier step's `as`
    "O_A|O_B"      OR of named constants from os / stat / fcntl / errno
    "0o644"        an octal literal
    123 / true     passed through
    "b'...'"       bytes literal, written as {"bytes": "..."} instead
    """
    if isinstance(tok, dict):
        if "bytes" in tok:
            return tok["bytes"].encode("utf-8")
        if "repeat" in tok:
            return (tok["repeat"]["unit"] * tok["repeat"]["times"]).encode("utf-8")
        raise ValueError("unknown token object %r" % (tok,))
    if not isinstance(tok, str):
        return tok
    if tok.startswith("$"):
        name = tok[1:]
        if name not in binds:
            raise KeyError("unbound name %r" % name)
        return binds[name]
    if tok.startswith("0o") or tok.startswith("0x"):
        return int(tok, 0)
    if "|" in tok or tok.isupper():
        total = 0
        for part in tok.split("|"):
            part = part.strip()
            if part.startswith("0o") or part.startswith("0x") or part.isdigit():
                total |= int(part, 0)
                continue
            val = None
            for mod in _const_modules():
                if hasattr(mod, part):
                    val = getattr(mod, part)
                    break
            if val is None:
                raise KeyError("unknown constant %r" % part)
            total |= val
        return total
    return tok


# ---------------------------------------------------------------------------
# normalizers: how a call's return value becomes a comparable observation
# ---------------------------------------------------------------------------


def _n_passthrough(v, ctx):
    return v


def _n_none(v, ctx):
    return None


def _n_fd(v, ctx):
    """A descriptor is reported by its allocation order in this row, not its
    integer: the integer is an allocation detail. The lowest-free-descriptor
    guarantee, which IS ABI, is asserted by the `fd_exact` call instead."""
    ctx["fds"].append(v)
    return "fd#%d" % (len(ctx["fds"]) - 1)


def _n_bytes(v, ctx):
    if v is None:
        return None
    return {"len": len(v), "sha256": hashlib.sha256(v).hexdigest()[:16]}


def _n_stat(v, ctx):
    """§11.3: shape and schema, never dynamic bytes. Mode BITS are contract
    (they are what chmod sets); inode/device/uid/gid/times/blocks are not."""
    out = {
        "type": _ftype(v.st_mode),
        "perm": oct(stat_mod.S_IMODE(v.st_mode)),
        "size": v.st_size,
        "nlink": v.st_nlink,
        "has_ino": v.st_ino > 0,
        "has_dev": v.st_dev > 0,
        "has_mtime": v.st_mtime > 0,
        "uid_is_caller": v.st_uid == os.getuid(),
    }
    # A directory's byte size is the filesystem's own bookkeeping (4096 on ext4,
    # 40 on tmpfs) and no interface promises it — §11.3 shape, not value.
    if out["type"] in ("dir", "lnk"):
        out.pop("size")
    return out


def _n_statvfs(v, ctx):
    """A filesystem-statistics answer is shape only: every field is a live
    figure of the target's storage and none of it is a promise (§11.3)."""
    return {
        "fields_present": sorted(
            k for k in dir(v) if k.startswith("f_") and isinstance(getattr(v, k), int)
        ),
        "bsize_positive": v.f_bsize > 0,
        "namemax_positive": v.f_namemax > 0,
    }


def _n_listing(v, ctx):
    return sorted(v)


def _n_dirents(v, ctx):
    return sorted((e["name"], e["type"]) for e in v)


def _ftype(mode):
    if stat_mod.S_ISREG(mode):
        return "reg"
    if stat_mod.S_ISDIR(mode):
        return "dir"
    if stat_mod.S_ISLNK(mode):
        return "lnk"
    if stat_mod.S_ISFIFO(mode):
        return "fifo"
    if stat_mod.S_ISCHR(mode):
        return "chr"
    if stat_mod.S_ISBLK(mode):
        return "blk"
    if stat_mod.S_ISSOCK(mode):
        return "sock"
    return "other"


# ---------------------------------------------------------------------------
# the call vocabulary
# ---------------------------------------------------------------------------


def _c_read(fd, n):
    return os.read(fd, n)


def _c_scandir(path):
    out = []
    with os.scandir(path) as it:
        for e in it:
            if e.is_symlink():
                t = "lnk"
            elif e.is_dir(follow_symlinks=False):
                t = "dir"
            elif e.is_file(follow_symlinks=False):
                t = "reg"
            else:
                t = "other"
            out.append({"name": e.name, "type": t})
    return out


def _c_fd_exact(fd, expect_lowest_free):
    """The lowest-free-descriptor guarantee, asserted as a guarantee rather than
    as an integer (§11.2: the guarantee's level, not the physics)."""
    return bool(fd == expect_lowest_free)


def _c_fcntl(fd, cmd, arg=0):
    import fcntl as f

    return f.fcntl(fd, cmd, arg)


def _c_fcntl_flags(fd, cmd):
    """F_GETFL/F_GETFD return a flag word whose low bits are the access mode;
    report the decoded set so the answer is comparable across kernels."""
    import fcntl as f

    v = f.fcntl(fd, cmd)
    names = []
    for nm in (
        "O_APPEND",
        "O_NONBLOCK",
        "O_SYNC",
        "O_DSYNC",
        "O_DIRECT",
        "O_NOATIME",
        "O_CLOEXEC",
        "FD_CLOEXEC",
    ):
        bit = getattr(os, nm, None)
        if bit is None:
            bit = getattr(f, nm, None)
        if bit and (v & bit) == bit:
            names.append(nm)
    acc = v & getattr(os, "O_ACCMODE", 3)
    accname = {os.O_RDONLY: "O_RDONLY", os.O_WRONLY: "O_WRONLY", os.O_RDWR: "O_RDWR"}.get(
        acc, "?"
    )
    return {"access": accname, "flags": sorted(names)}


def _c_flock(fd, op):
    import fcntl as f

    return f.flock(fd, op)


def _c_setlk(fd, ltype, whence=0, start=0, length=0, wait=False):
    """POSIX record locking through fcntl(F_SETLK/F_SETLKW)."""
    import fcntl as f
    import struct

    lockdata = struct.pack("hhllhh", ltype, whence, start, length, 0, 0)
    return f.fcntl(fd, f.F_SETLKW if wait else f.F_SETLK, lockdata)


def _c_getlk(fd, ltype, whence=0, start=0, length=0):
    import fcntl as f
    import struct

    lockdata = struct.pack("hhllhh", ltype, whence, start, length, 0, 0)
    out = f.fcntl(fd, f.F_GETLK, lockdata)
    t, w, st, ln, pid, _ = struct.unpack("hhllhh", out)
    return {"type_is_unlck": t == f.F_UNLCK, "start": st, "len": ln}


def _c_lock_conflict(path, ltype):
    """The lock-conflict guarantee needs a SECOND holder, so it forks one. The
    observation is the guarantee (the second attempt is refused, with which
    errno), never the timing of the race — §11.2."""
    import fcntl as f
    import struct
    import time

    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:  # child: take the lock, tell the parent, wait to be told to go
            try:
                os.close(r)
                cfd = os.open(path, os.O_RDWR)
                f.fcntl(cfd, f.F_SETLK, struct.pack("hhllhh", f.F_WRLCK, 0, 0, 0, 0, 0))
                os.write(w, b"1")
                time.sleep(2.0)
            finally:
                os._exit(0)
        os.close(w)
        os.read(r, 1)
        os.close(r)
        try:
            f.fcntl(fd, f.F_SETLK, struct.pack("hhllhh", ltype, 0, 0, 0, 0, 0))
            result = {"refused": False, "errno": None}
        except OSError as e:
            result = {"refused": True, "errno": errno_mod.errorcode.get(e.errno, str(e.errno))}
        os.kill(pid, 9)
        os.waitpid(pid, 0)
        return result
    finally:
        os.close(fd)


def _c_flock_conflict(path, op):
    import fcntl as f
    import time

    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            try:
                os.close(r)
                cfd = os.open(path, os.O_RDWR)
                f.flock(cfd, f.LOCK_EX)
                os.write(w, b"1")
                time.sleep(2.0)
            finally:
                os._exit(0)
        os.close(w)
        os.read(r, 1)
        os.close(r)
        try:
            f.flock(fd, op)
            result = {"refused": False, "errno": None}
        except OSError as e:
            result = {"refused": True, "errno": errno_mod.errorcode.get(e.errno, str(e.errno))}
        os.kill(pid, 9)
        os.waitpid(pid, 0)
        return result
    finally:
        os.close(fd)


def _c_append_atomicity(path, writers, per_writer, chunk):
    """O_APPEND's guarantee: concurrent appenders never lose or interleave WITHIN
    a write. Observed as the guarantee (§11.2) — final length is the exact sum,
    and every chunk in the file is whole — never as an interleaving order."""
    kids = []
    for i in range(writers):
        pid = os.fork()
        if pid == 0:
            try:
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
                payload = (chr(ord("a") + i) * chunk).encode()
                for _ in range(per_writer):
                    os.write(fd, payload)
                os.close(fd)
            finally:
                os._exit(0)
        kids.append(pid)
    for pid in kids:
        os.waitpid(pid, 0)
    data = open(path, "rb").read()
    whole = all(
        len(set(data[i : i + chunk])) == 1 for i in range(0, len(data) - chunk + 1, chunk)
    )
    # The file's BYTES are the interleaving, and the interleaving is physics, not
    # contract (§11.2). Leaving it in the scratch tree would put a nondeterministic
    # artifact into the side-effect snapshot and make the row disagree with itself
    # across runs — which is the very error this rule exists to refuse. The
    # guarantee is what is reported; the evidence for it is removed.
    os.unlink(path)
    return {
        "length_is_exact_sum": len(data) == writers * per_writer * chunk,
        "every_chunk_whole": whole,
    }


def _c_mount(source, target, fstype, flags=0, data=None):
    import ctypes

    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    rc = libc.mount(
        source.encode(),
        target.encode(),
        fstype.encode(),
        ctypes.c_ulong(flags),
        None if data is None else data.encode(),
    )
    if rc != 0:
        raise OSError(ctypes.get_errno(), os.strerror(ctypes.get_errno()))
    return 0


def _c_umount2(target, flags=0):
    import ctypes

    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    rc = libc.umount2(target.encode(), ctypes.c_int(flags))
    if rc != 0:
        raise OSError(ctypes.get_errno(), os.strerror(ctypes.get_errno()))
    return 0


def _c_mount_present(target):
    want = os.path.realpath(target)
    with open("/proc/self/mountinfo", "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) > 4 and parts[4] == want:
                return True
    return False


def _c_pipe_read_fd():
    """A pipe's read end, with the write end closed: the fd kind whose whole
    point is that it is not seekable (ESPIPE) and not syncable (EINVAL)."""
    r, w = os.pipe()
    os.close(w)
    return r


def _c_chroot_in_child(path):
    """chroot is observed in a forked child so the harness's own process is never
    confined. The observation is what the child saw of its own root."""
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            os.close(r)
            os.chroot(path)
            os.chdir("/")
            os.write(w, json.dumps(sorted(os.listdir("/"))).encode())
        except OSError as e:
            os.write(w, json.dumps({"errno": errno_mod.errorcode.get(e.errno)}).encode())
        finally:
            os._exit(0)
    os.close(w)
    out = b""
    while True:
        chunk = os.read(r, 4096)
        if not chunk:
            break
        out += chunk
    os.close(r)
    os.waitpid(pid, 0)
    return json.loads(out.decode() or "null")


def _c_umask(mask):
    """Returns the PREVIOUS mask as an integer, so a later step can restore it by
    reference; the normalizer renders it octal for the observation."""
    return os.umask(mask)


def _n_oct(v, ctx):
    return oct(v)


def _c_write_file(path, content, mode=0o644):
    fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, mode)
    try:
        return os.write(fd, content if isinstance(content, bytes) else content.encode())
    finally:
        os.close(fd)


def _c_sendfile(out_fd, in_fd, offset, count):
    return os.sendfile(out_fd, in_fd, offset, count)


def _c_splice_through_pipe(src_path, dst_path, count):
    r, w = os.pipe()
    sfd = os.open(src_path, os.O_RDONLY)
    dfd = os.open(dst_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        moved_in = os.splice(sfd, w, count)
        moved_out = os.splice(r, dfd, moved_in)
        return {"in": moved_in, "out": moved_out}
    finally:
        for fd in (r, w, sfd, dfd):
            os.close(fd)


#: call name -> (callable, normalizer). A row may name only what is here.
CALLS = {
    # --- open / close ---------------------------------------------------
    "open": (os.open, _n_fd),
    "openat": (lambda path, flags, mode=0o777, dir_fd=None: os.open(path, flags, mode, dir_fd=dir_fd), _n_fd),
    "close": (os.close, _n_none),
    "fd_exact": (_c_fd_exact, _n_passthrough),
    # --- read / write ---------------------------------------------------
    "read": (_c_read, _n_bytes),
    "pread": (os.pread, _n_bytes),
    "write": (os.write, _n_passthrough),
    "pwrite": (os.pwrite, _n_passthrough),
    "writev": (lambda fd, parts: os.writev(fd, [p.encode() if isinstance(p, str) else p for p in parts]), _n_passthrough),
    "write_file": (_c_write_file, _n_passthrough),
    "lseek": (os.lseek, _n_passthrough),
    "append_atomicity": (_c_append_atomicity, _n_passthrough),
    # --- metadata -------------------------------------------------------
    "stat": (os.stat, _n_stat),
    "lstat": (os.lstat, _n_stat),
    "fstat": (os.fstat, _n_stat),
    "fstatat": (lambda path, dir_fd, follow=True: os.stat(path, dir_fd=dir_fd, follow_symlinks=follow), _n_stat),
    "statvfs": (os.statvfs, _n_statvfs),
    "fstatvfs": (os.fstatvfs, _n_statvfs),
    "access": (os.access, _n_passthrough),
    "faccessat": (lambda path, mode, dir_fd: os.access(path, mode, dir_fd=dir_fd), _n_passthrough),
    "chmod": (os.chmod, _n_none),
    "fchmod": (os.fchmod, _n_none),
    "fchmodat": (lambda path, mode, dir_fd: os.chmod(path, mode, dir_fd=dir_fd), _n_none),
    "chown": (os.chown, _n_none),
    "lchown": (os.lchown, _n_none),
    "fchown": (os.fchown, _n_none),
    "utime_set": (lambda path, atime_ns, mtime_ns: os.utime(path, ns=(atime_ns, mtime_ns)), _n_none),
    "utime_read_ns": (lambda path: [os.stat(path).st_atime_ns, os.stat(path).st_mtime_ns], _n_passthrough),
    "umask": (_c_umask, _n_oct),
    # --- namespace ------------------------------------------------------
    "link": (os.link, _n_none),
    "linkat": (lambda src, dst, src_dir_fd, dst_dir_fd: os.link(src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd), _n_none),
    "symlink": (os.symlink, _n_none),
    "symlinkat": (lambda target, path, dir_fd: os.symlink(target, path, dir_fd=dir_fd), _n_none),
    "readlink": (os.readlink, _n_passthrough),
    "readlinkat": (lambda path, dir_fd: os.readlink(path, dir_fd=dir_fd), _n_passthrough),
    "unlink": (os.unlink, _n_none),
    "unlinkat": (lambda path, dir_fd: os.unlink(path, dir_fd=dir_fd), _n_none),
    "unlinkat_dir": (lambda path, dir_fd: os.rmdir(path, dir_fd=dir_fd), _n_none),
    "rename": (os.rename, _n_none),
    "renameat": (lambda src, dst, src_dir_fd, dst_dir_fd: os.rename(src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd), _n_none),
    "replace": (os.replace, _n_none),
    "mkdir": (os.mkdir, _n_none),
    "mkdirat": (lambda path, mode, dir_fd: os.mkdir(path, mode, dir_fd=dir_fd), _n_none),
    "rmdir": (os.rmdir, _n_none),
    "mknod": (os.mknod, _n_none),
    "mkfifo": (os.mkfifo, _n_none),
    "truncate": (os.truncate, _n_none),
    "ftruncate": (os.ftruncate, _n_none),
    "posix_fallocate": (os.posix_fallocate, _n_none),
    "listdir": (os.listdir, _n_listing),
    "scandir": (_c_scandir, _n_dirents),
    "chdir": (os.chdir, _n_none),
    "fchdir": (os.fchdir, _n_none),
    "getcwd_tail": (lambda n=1: os.path.basename(os.getcwd()), _n_passthrough),
    "chroot_in_child": (_c_chroot_in_child, _n_passthrough),
    # --- xattr ----------------------------------------------------------
    "setxattr": (os.setxattr, _n_none),
    "getxattr": (os.getxattr, _n_bytes),
    "listxattr": (os.listxattr, _n_listing),
    "removexattr": (os.removexattr, _n_none),
    # --- durability -----------------------------------------------------
    "fsync": (os.fsync, _n_none),
    "fdatasync": (os.fdatasync, _n_none),
    "sync": (os.sync, _n_none),
    # --- fd state and locks ---------------------------------------------
    "fcntl": (_c_fcntl, _n_passthrough),
    "fcntl_flags": (_c_fcntl_flags, _n_passthrough),
    "setlk": (_c_setlk, _n_none),
    "getlk": (_c_getlk, _n_passthrough),
    "lock_conflict": (_c_lock_conflict, _n_passthrough),
    "flock": (_c_flock, _n_none),
    "flock_conflict": (_c_flock_conflict, _n_passthrough),
    "dup": (os.dup, _n_fd),
    # `dup2` JOINS `_n_fd`'s RELATIVE SCHEME [EP-28H item 3, 2026-08-02]. It was the one
    # descriptor-returning entry that passed its integer through, which is why the
    # absolute-descriptor class had exactly one live member per baseline directory:
    # `files.dup` step 9's `dup2($f, $f)` returns `$f`, an ambient-occupancy-bound number
    # pinned as an absolute. Reporting it by allocation order EMPTIES THE CLASS BY
    # CONSTRUCTION rather than re-pinning its member one occupancy later. Step 6's
    # `dup2(fd, 200)` returns the caller's own 200 and becomes relative too — no ABI fact is
    # lost there, because the caller-chosen guarantee is what steps 7 and 8 exercise: they
    # `lseek` and `close` descriptor 200 by number, and both fail if `dup2` did not put it
    # there. The lowest-available guarantee keeps its own dedicated `fd_exact` step.
    "dup2": (os.dup2, _n_fd),
    # --- bulk movement --------------------------------------------------
    "copy_file_range": (os.copy_file_range, _n_passthrough),
    "sendfile": (_c_sendfile, _n_passthrough),
    "splice_through_pipe": (_c_splice_through_pipe, _n_passthrough),
    "pipe_read_fd": (_c_pipe_read_fd, _n_fd),
    # --- mounts (privileged) --------------------------------------------
    "mount": (_c_mount, _n_passthrough),
    "umount2": (_c_umount2, _n_passthrough),
    "mount_present": (_c_mount_present, _n_passthrough),
}

#: Which SYSCALL each vocabulary entry drives, or None for a step that only sets
#: a row up. This is what lets the record bracket be taken around the call UNDER
#: TEST rather than around the whole row: a row's writes-to-make-a-file are not
#: the row's subject, and counting their records against the row's class would
#: fail every CACHE row that needs a file to exist first. The table lives beside
#: the callables because that is the only place that knows what each one calls;
#: the compiler reads it as data and holds no syscall knowledge of its own.
DRIVES = {
    "open": "open", "openat": "openat", "close": "close", "fd_exact": None,
    "read": "read", "pread": "pread64", "write": "write", "pwrite": "pwrite64",
    "writev": "writev", "write_file": None, "lseek": "lseek",
    "append_atomicity": "write",
    "stat": "stat", "lstat": "lstat", "fstat": "fstat", "fstatat": "fstatat",
    "statvfs": "statfs", "fstatvfs": "fstatfs",
    "access": "access", "faccessat": "faccessat",
    "chmod": "chmod", "fchmod": "fchmod", "fchmodat": "fchmodat",
    "chown": "chown", "lchown": "lchown", "fchown": "fchown",
    "utime_set": "utimensat", "utime_read_ns": None, "umask": "umask",
    "link": "link", "linkat": "linkat", "symlink": "symlink", "symlinkat": "symlinkat",
    "readlink": "readlink", "readlinkat": "readlinkat",
    "unlink": "unlink", "unlinkat": "unlinkat", "unlinkat_dir": "unlinkat",
    "rename": "rename", "renameat": "renameat", "replace": "rename",
    "mkdir": "mkdir", "mkdirat": "mkdirat", "rmdir": "rmdir",
    "mknod": "mknod", "mkfifo": "mknod",
    "truncate": "truncate", "ftruncate": "ftruncate",
    "posix_fallocate": "fallocate",
    "listdir": "getdents", "scandir": "getdents",
    "chdir": "chdir", "fchdir": "fchdir", "getcwd_tail": "getcwd",
    "chroot_in_child": "chroot",
    "setxattr": "setxattr", "getxattr": "getxattr", "listxattr": "listxattr",
    "removexattr": "removexattr",
    "fsync": "fsync", "fdatasync": "fdatasync", "sync": "sync",
    "fcntl": "fcntl", "fcntl_flags": "fcntl", "setlk": "fcntl", "getlk": "fcntl",
    "lock_conflict": "fcntl", "flock": "flock", "flock_conflict": "flock",
    "dup": "dup", "dup2": "dup2",
    "copy_file_range": "copy_file_range", "sendfile": "sendfile",
    "splice_through_pipe": "splice", "pipe_read_fd": None,
    "mount": "mount", "umount2": "umount", "mount_present": None,
}

#: What each vocabulary entry PERFORMS on the target, where that is more than the
#: one call it drives. `DRIVES` answers "which row is this step the subject of";
#: this answers "which acts did the target actually see", and the two differ
#: wherever an entry is a compound (`write_file` opens, writes and closes) or
#: wherever the C library reaches its answer through other calls (`posix_fallocate`
#: falls back to writing zeroes on a filesystem with no allocation call).
#:
#: WHY IT EXISTS: design/10 §11.4a attributes a record to the act it covers, so a
#: record covering an act the row never drove is a finding. That test is only
#: sound if the row's acts are known IN FULL — a missing entry here turns a
#: legitimate record into a false finding. So the entries are GENEROUS on purpose:
#: listing a call the step might not make costs only detection power in that one
#: direction, while omitting one manufactures a failure. This is the harness
#: knowing what its own probe does, which is the one vocabulary it may hold.
PERFORMS = {
    "fd_exact": (),                       # compares two integers; calls nothing
    "mount_present": (),                  # reads /proc, never the target
    "write_file": ("open", "write", "close"),
    "utime_read_ns": ("stat",),
    "pipe_read_fd": ("pipe", "close"),
    "append_atomicity": ("open", "write", "close", "read", "unlink"),
    "lock_conflict": ("open", "close", "fcntl", "read", "write"),
    "flock_conflict": ("open", "close", "flock", "read", "write"),
    "splice_through_pipe": ("splice", "open", "close", "read", "write"),
    "sendfile": ("sendfile", "read", "write"),
    "copy_file_range": ("copy_file_range", "read", "write"),
    "posix_fallocate": ("fallocate", "read", "write"),
    "listdir": ("getdents", "open", "close"),
    "scandir": ("getdents", "open", "close", "stat"),
    "chroot_in_child": ("chroot", "chdir", "getdents", "read", "write", "close"),
    "dup2": ("dup2", "close"),            # dup2 closes the descriptor it lands on
    "open": ("open", "truncate"),         # O_TRUNC is a truncate at the port
    "openat": ("openat", "truncate"),
    "close": ("close", "write"),          # a deferred burst flushes on the last close
}


def performs(name):
    """Every act this vocabulary entry may perform on the target."""
    if name in PERFORMS:
        return tuple(PERFORMS[name])
    sc = DRIVES.get(name)
    return (sc,) if sc else ()


# ---------------------------------------------------------------------------
# the runner
# ---------------------------------------------------------------------------


def snapshot_tree(root):
    """The process-visible side effect: the scratch tree as the target shows it.
    Content by hash; mode bits verbatim; everything dynamic reduced to shape."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(dirnames) + sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            try:
                st = os.lstat(full)
            except OSError as e:
                out[rel] = {"lstat_errno": errno_mod.errorcode.get(e.errno)}
                continue
            entry = {
                "type": _ftype(st.st_mode),
                "perm": oct(stat_mod.S_IMODE(st.st_mode)),
                "nlink": st.st_nlink,
                "size": st.st_size,
            }
            if stat_mod.S_ISLNK(st.st_mode):
                try:
                    entry["target"] = os.readlink(full)
                except OSError:
                    entry["target"] = None
                entry.pop("size", None)
            elif stat_mod.S_ISDIR(st.st_mode):
                entry.pop("size", None)  # §11.3: filesystem bookkeeping, not contract
            elif stat_mod.S_ISREG(st.st_mode):
                try:
                    with open(full, "rb") as f:
                        entry["sha256"] = hashlib.sha256(f.read()).hexdigest()[:16]
                except OSError as e:
                    entry["sha256"] = "unreadable:%s" % errno_mod.errorcode.get(e.errno)
            out[rel] = entry
    return out


def _record_lines(path):
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for ln in f if ln.strip())
    except OSError:
        return 0


def run_row(row, scratch_root, record_file=None, hook=None):
    """Run one row's steps in its own fresh directory. Returns the observation.

    When `record_file` names the target's append-only record, each step also
    carries the record's length either side of it (`rec`). That bracket is taken
    HERE, by the thing performing the act, because that is the only place it can
    be exact — the harness, standing outside, could only bracket the whole row,
    and a row's setup writes are not the call its class is about.
    """
    row_dir = os.path.join(scratch_root, row["row_id"].replace("/", "_"))
    os.makedirs(row_dir, exist_ok=True)
    binds = {}
    ctx = {"fds": []}
    steps_out = []
    cwd_before = os.getcwd()
    try:
        os.chdir(row_dir)
        for i, step in enumerate(row["steps"]):
            name = step["call"]
            rec = {"i": i, "call": name}
            if name not in CALLS:
                rec["unknown_call"] = True
                steps_out.append(rec)
                continue
            fn, norm = CALLS[name]
            try:
                args = [resolve_token(a, binds) for a in step.get("args", [])]
                kwargs = {
                    k: resolve_token(v, binds) for k, v in step.get("kwargs", {}).items()
                }
            except Exception as e:  # an unbound name is a row defect, reported not hidden
                rec["bind_error"] = "%s: %s" % (type(e).__name__, e)
                steps_out.append(rec)
                continue
            before = _record_lines(record_file)
            try:
                if hook:
                    hook("before", row, i, step)
                val = fn(*args, **kwargs)
                rec["errno"] = None
                rec["ret"] = norm(val, ctx)
                if "as" in step:
                    binds[step["as"]] = val
                if hook:
                    hook("after", row, i, step)
            except OSError as e:
                rec["errno"] = errno_mod.errorcode.get(e.errno, "errno:%s" % e.errno)
                rec["ret"] = None
            except Exception as e:  # noqa: BLE001 - a driver fault must be visible
                rec["exception"] = "%s: %s" % (type(e).__name__, e)
                rec["errno"] = None
                rec["ret"] = None
            if record_file:
                rec["rec"] = [before, _record_lines(record_file)]
            steps_out.append(rec)
    finally:
        os.chdir(cwd_before)
        for fd in ctx["fds"]:
            try:
                os.close(fd)
            except OSError:
                pass
    return {"steps": steps_out, "state": snapshot_tree(row_dir)}


def main(argv):
    plan = json.load(open(argv[1], "r"))
    scratch_root = os.path.abspath(
        plan.get("scratch") or tempfile.mkdtemp(prefix="govos-conf-")
    )
    os.makedirs(scratch_root, exist_ok=True)
    rows_out = {}
    record_file = plan.get("record_file")
    for row in plan["rows"]:
        try:
            rows_out[row["row_id"]] = run_row(row, scratch_root, record_file)
        except Exception as e:  # noqa: BLE001
            rows_out[row["row_id"]] = {"driver_error": "%s: %s" % (type(e).__name__, e)}
    uname = os.uname()
    out = {
        "probe_version": PROBE_VERSION,
        "uname": {
            "sysname": uname.sysname,
            "release": uname.release,
            "version": uname.version,
            "machine": uname.machine,
        },
        "euid_is_root": os.geteuid() == 0,
        "python": sys.version.split()[0],
        "rows": rows_out,
    }
    sys.stdout.write(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
