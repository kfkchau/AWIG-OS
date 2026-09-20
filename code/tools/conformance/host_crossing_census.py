# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (the host seam, a crossing, the governance core, a portability label) as in the
# seL4/gVisor/Fuchsia literature. NON-GOAL: no offensive capability of any kind — this ENUMERATES,
# by reading source, every place the code crosses to the host (disk/clock/entropy/socket) and
# classifies each as ABOVE THE SEAM (the governance core, which must route through the host seam) or
# BELOW A SEAM (the effect-seam performer, the bridge adapters, the observe seam). It performs no
# effect, mints no input, drives no attack; it reads source. Full declaration: SCOPE-STATEMENT.md.
"""C7 P2 · I1/I2, B3/B8 — THE UNDECLARED-CROSSING + LABEL CENSUS (the enumerator + classifier).

The host seam (src/bridge/host_seam.py) declares the CLOSED set of acts the governance core asks its
host to perform. This census is the mechanical proof that NO crossing escapes it: it reads every .py
under src/ and finds every direct host crossing — a call to `os.<effect>` (os.path / os.environ are
namespace reads, not effects, and are exempt), `socket.<x>`, `time.<x>`, the builtin `open()`, or a
pathlib file method (`.open` / `.read_text` / `.write_text` / `.read_bytes` / `.write_bytes` /
`.unlink` / `.mkdir` / `.rmdir`) — then classifies it by WHERE it sits:

    ABOVE THE SEAM (RED)   the governance core — src/kernel/, src/subsystems/, src/founding/. Every
                          crossing here must route through the host seam; a DIRECT one is an
                          UNDECLARED CROSSING and REDS. After C7 P2's routing this set is EMPTY.
    BELOW A SEAM (allowed) the declared seam layer — src/bridge/ (the effect-seam performer + the M2/M3
                          adapters) — and src/observe/ (the OBSERVE seam, its own read-only contract,
                          L13). Host crossings here are where the host is legitimately touched; they
                          are classified and reported, never red.

THE CHECK CAN FAIL (A4). A planted direct `os` call in a core module reds the census; the near-miss
control the test drives. Reading observe/ classifies it (below its own seam) — reading is required,
never editing it (L13).

THE LABEL CENSUS (A5, B8 "no silent Linux"). Every host method the real performer implements must be
DECLARED in the seam's ACTS table with a portability label (portable-host-primitive / least-portable /
guest-gated-capability). A host method that carries no label is an unlabelled crossing and REDS — the
mechanical form of "no silent Linux". A twelfth act KIND cannot be declared without widening
`ACT_KINDS` (host_seam.declare_act refuses it), so the label set is closed too.

USAGE
    python3 -m tools.conformance.host_crossing_census            # print the classification + verdict
    python3 -m tools.conformance.host_crossing_census --md       # emit the evidence markdown body
    (exit 0 iff the core is host-clean AND every performer host method is labelled)
"""

import ast
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, os.pardir, os.pardir, "src"))

# The host namespaces whose DIRECT calls are effect crossings. `os.path.*` and `os.environ.*` are
# namespace reads (path arithmetic, config), not host effects — they are naturally EXEMPT because the
# call's function value is a nested attribute (os.path.join), not the bare name `os`.
HOST_MODULES = frozenset({"os", "socket", "time"})

# Pathlib file-crossing methods — a closed set. A call to one of these on any object is a file
# crossing (the estate's core reaches the disk through pathlib and os only).
FILE_METHODS = frozenset({
    "open", "read_text", "write_text", "read_bytes", "write_bytes",
    "unlink", "mkdir", "rmdir", "touch", "iterdir",
})

# The builtin that opens a file directly (attestation's member read, the installer's pack read before
# routing). `open(...)` as a bare name is a host crossing.
BUILTIN_HOST = frozenset({"open"})

# The governance core above the seam — every crossing here MUST route through the host seam.
CORE_PREFIXES = ("kernel/", "subsystems/", "founding/")
# The declared seam layer + the separate observe seam — host crossings here are below a seam (allowed).
SEAM_PREFIXES = ("bridge/", "observe/")

# ---- DECLARED EXCEPTIONS (owner law, recorded — never silent, L6) --------------------------------
# NONE. The mechanism stays (a future owner-law crossing that must NOT route could be recorded here,
# never silently dropped), but it is currently EMPTY. It once held src/kernel/vault.py's four write-once
# disk places, excepted while vault.py was byte-frozen owner law (RW-VAULT / §8-h). On archi's :3930/:3952
# — the owner's principle-level word (verify-never-reveal is a PROPERTY of the act set, not a byte-freeze;
# the disk is ours under our own core) — the vault is ROUTED through the seam like every other core file
# and its disk places now go through host(), so no exception remains. The census stays ABLE TO FAIL on
# ANY undeclared crossing — a different primitive, a new line, another core file all still RED.
DECLARED_EXCEPTIONS = {}


def _is_declared_exception(rel, crossing):
    """True iff (rel, crossing) is a RECORDED owner-law exception (the byte-frozen vault). A crossing
    NOT in the declared set — any other primitive, line, or file — is never excepted."""
    return crossing in DECLARED_EXCEPTIONS.get(rel, frozenset())


#: The name of the host-seam accessor. A method call whose RECEIVER is `host()` is a routed act
#: through the seam, never a direct host crossing — even when the method name (read_bytes / write_bytes)
#: coincides with a pathlib file method. This is the one exemption that keeps the seam's own vocabulary
#: from reading as a crossing.
_SEAM_ACCESSOR = "host"


def _is_seam_call(value):
    """True iff `value` is a call to the seam accessor — `host()` — so `host().read_bytes(...)` is a
    routed act, not a direct pathlib crossing."""
    return (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
            and value.func.id == _SEAM_ACCESSOR)


class _CrossingFinder(ast.NodeVisitor):
    """Walk one module's AST; record every direct host crossing (module, primitive, lineno)."""

    def __init__(self):
        self.crossings = []     # list of (namespace, primitive, lineno)

    def visit_Call(self, node):
        fn = node.func
        if isinstance(fn, ast.Attribute):
            val = fn.value
            if isinstance(val, ast.Name) and val.id in HOST_MODULES:
                # os.<x> / socket.<x> / time.<x> — a DIRECT host call. os.path.* / os.environ.* have a
                # nested-attribute value and never reach here (exempt by construction).
                self.crossings.append((val.id, fn.attr, node.lineno))
            elif fn.attr in FILE_METHODS and not _is_seam_call(val):
                # a pathlib file method (.open / .read_text / ...) on a real object — a direct crossing.
                # A call on the seam accessor (host().read_bytes(...)) is a ROUTED act, not a crossing,
                # so its method name colliding with pathlib's is exempt.
                self.crossings.append(("pathlib", fn.attr, node.lineno))
        elif isinstance(fn, ast.Name) and fn.id in BUILTIN_HOST:
            self.crossings.append(("builtin", fn.id, node.lineno))
        self.generic_visit(node)


def _rel(path, src_root):
    return os.path.relpath(path, src_root).replace(os.sep, "/")


def _iter_src_files(src_root):
    for root, _dirs, files in os.walk(src_root):
        for name in sorted(files):
            if name.endswith(".py"):
                yield os.path.join(root, name)


def _zone(rel):
    if rel.startswith(SEAM_PREFIXES):
        return "seam"
    if rel.startswith(CORE_PREFIXES):
        return "core"
    return "core"   # anything else under src/ is treated as core (conservative)


def crossings_by_file(src_dir=None):
    """{relpath: [(namespace, primitive, lineno), ...]} for every .py under src/ with a host crossing.
    Reads ALL of src/ — the core, the seam layer, and the observe seam (classified, never edited)."""
    root = os.path.abspath(src_dir) if src_dir else _SRC
    out = {}
    for path in _iter_src_files(root):
        with open(path, encoding="utf-8") as fh:
            try:
                tree = ast.parse(fh.read())
            except SyntaxError:
                continue
        finder = _CrossingFinder()
        finder.visit(tree)
        if finder.crossings:
            out[_rel(path, root)] = finder.crossings
    return out


def undeclared_crossings(src_dir=None):
    """The RED answer: every host crossing that sits ABOVE the seam (in the governance core) and is
    therefore NOT routed through the host seam AND is not a recorded owner-law exception. EMPTY after
    C7 P2's routing; a planted direct `os` call in a core module makes it non-empty (the check can
    fail). A DECLARED EXCEPTION (the byte-frozen vault, recorded above) is excluded here — but only
    its exact declared crossings; any OTHER undeclared crossing still reds."""
    bad = {}
    for rel, cx in crossings_by_file(src_dir).items():
        if _zone(rel) != "core":
            continue
        remaining = [c for c in cx if not _is_declared_exception(rel, c)]
        if remaining:
            bad[rel] = remaining
    return bad


def declared_exception_crossings(src_dir=None):
    """The RECORDED owner-law exceptions actually present in the tree (the byte-frozen vault's direct
    crossings). Reported so the exception is never silent (L6); a crossing here is above the seam but
    excepted by the owner's byte-freeze, not by the seam."""
    out = {}
    for rel, cx in crossings_by_file(src_dir).items():
        if _zone(rel) != "core":
            continue
        excepted = [c for c in cx if _is_declared_exception(rel, c)]
        if excepted:
            out[rel] = excepted
    return out


def declared_crossings(src_dir=None):
    """The classified BELOW-A-SEAM answer: host crossings in the seam layer + the observe seam. These
    are WHERE the host is legitimately touched — reported for the record, never red."""
    ok = {}
    for rel, cx in crossings_by_file(src_dir).items():
        if _zone(rel) == "seam":
            ok[rel] = cx
    return ok


def unlabelled_host_methods(performer_cls=None):
    """The LABEL census (A5): every host method the real performer implements must be DECLARED in the
    seam's ACTS table (kind + portability label). Returns the performer host methods that carry no
    label — a planted unlabelled crossing below the seam. EMPTY on the shipped performer; the test
    passes a subclass carrying an unlabelled host method to drive the check's ability to fail."""
    src_root = os.path.abspath(os.path.join(_HERE, os.pardir, os.pardir, "src"))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from bridge import host_seam
    declared = set(host_seam.HostSeam.ACTS)
    performer_cls = performer_cls or host_seam.RealHost
    # A host method on the performer is one whose source names a host namespace / builtin / file method.
    import inspect
    unlabelled = []
    for name in dir(performer_cls):
        if name.startswith("_"):
            continue
        fn = getattr(performer_cls, name)
        if not callable(fn):
            continue
        try:
            src = inspect.getsource(fn)
        except (OSError, TypeError):
            continue
        tree = ast.parse(src.lstrip())
        finder = _CrossingFinder()
        finder.visit(tree)
        if finder.crossings and name not in declared:
            unlabelled.append(name)
    return sorted(unlabelled)


def verdict(src_dir=None):
    """The whole census: the undeclared crossings (red if any), the label census (red if any), the
    classified below-seam crossings. `clean` is True iff the core is host-clean and every performer
    host method is labelled."""
    bad = undeclared_crossings(src_dir)
    unlabelled = unlabelled_host_methods()
    return {
        "undeclared_crossings": bad,
        "unlabelled_host_methods": unlabelled,
        "below_seam": declared_crossings(src_dir),
        "declared_exceptions": declared_exception_crossings(src_dir),
        "clean": (not bad) and (not unlabelled),
    }


def _render(v, md=False):
    lines = []
    bullet = "- " if md else "  "
    lines.append("# HOST-CROSSING CENSUS" if md else "HOST-CROSSING CENSUS (C7 P2)")
    lines.append("")
    if v["undeclared_crossings"]:
        lines.append("UNDECLARED CROSSINGS ABOVE THE SEAM (RED — must route through the host seam):")
        for rel, cx in sorted(v["undeclared_crossings"].items()):
            for ns, prim, ln in cx:
                lines.append("%s%s:%d  %s.%s" % (bullet, rel, ln, ns, prim))
    else:
        lines.append("UNDECLARED CROSSINGS ABOVE THE SEAM: none — the governance core is host-clean.")
    lines.append("")
    if v["unlabelled_host_methods"]:
        lines.append("UNLABELLED HOST METHODS ON THE PERFORMER (RED — no L6 label):")
        for m in v["unlabelled_host_methods"]:
            lines.append("%s%s" % (bullet, m))
    else:
        lines.append("UNLABELLED HOST METHODS: none — every performer host act carries a label.")
    lines.append("")
    if v.get("declared_exceptions"):
        lines.append("DECLARED EXCEPTIONS (owner law, recorded — NOT routed, never silent — L6):")
        for rel, cx in sorted(v["declared_exceptions"].items()):
            for ns, prim, ln in cx:
                lines.append("%s%s:%d  %s.%s  (byte-frozen owner law — RW-VAULT/§8-h, :3927)"
                             % (bullet, rel, ln, ns, prim))
        lines.append("")
    lines.append("BELOW A SEAM (classified, allowed — the seam layer + the observe seam):")
    for rel, cx in sorted(v["below_seam"].items()):
        lines.append("%s%s  (%d crossings)" % (bullet, rel, len(cx)))
    lines.append("")
    lines.append("VERDICT: %s" % ("CLEAN — no crossing escapes the seam" if v["clean"]
                                   else "RED — an undeclared or unlabelled crossing exists"))
    return "\n".join(lines)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    v = verdict()
    print(_render(v, md=("--md" in argv)))
    return 0 if v["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
