"""Shared harness for the mentor probe library. Each probe file imports build() and check().

build() returns a fully composed kernel (gate + protection ops registered) in a temp dir,
so probes exercise the same surface a real deployment has. check() prints PASS/FAIL and
records failures; run_report() exits non-zero if any probe failed (so CI / a reviewer sees red).
"""
import os
import sys
import tempfile

REPO_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src")
sys.path.insert(0, REPO_SRC)

_FAILS = []


def build():
    """A bare-record kernel with protection ops registered (GRANT-READ, CONSUME, and the
    EP-09 brake/review surface). Returns (store, gate, views, protection, path)."""
    from kernel.boot import build_kernel
    from kernel.protection import Protection, register_protection_ops
    d = tempfile.mkdtemp()
    path = os.path.join(d, "r.jsonl")
    store, gate, views = build_kernel(path)
    prot = Protection(store, gate, views)
    register_protection_ops(gate, store, prot)
    return store, gate, views, prot, path


def rebuild(path):
    """Reopen the SAME record file in a fresh kernel — the reboot archetype."""
    from kernel.boot import build_kernel
    from kernel.protection import Protection, register_protection_ops
    store, gate, views = build_kernel(path)
    prot = Protection(store, gate, views)
    register_protection_ops(gate, store, prot)
    return store, gate, views, prot


def check(label, condition, detail=""):
    ok = bool(condition)
    print(("PASS " if ok else "FAIL ") + label + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        _FAILS.append(label)
    return ok


def refuses(fn, want_rule=None):
    """True if fn() raises OpError (optionally with the named rule). The hostile-nobody staple."""
    from kernel.errors import OpError
    try:
        fn()
        return False
    except OpError as e:
        return want_rule is None or e.rule == want_rule


def run_report(name):
    print(f"\n{name}: {'ALL PASS' if not _FAILS else str(len(_FAILS)) + ' FAILED -> ' + ', '.join(_FAILS)}")
    sys.exit(1 if _FAILS else 0)
