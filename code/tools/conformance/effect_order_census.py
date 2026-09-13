# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (handler, effect, gate decision, reversible/irreversible, blob hand_off, deferred
# thunk). NON-GOAL: no offensive capability of any kind — this ENUMERATES the gate's own byte/world
# handlers and CLASSIFIES the order of their effects against the gate's decision, by reading. It
# performs no effect, mints no input, drives no attack; it is a conformance census over the source.
# Full declaration: SCOPE-STATEMENT.md.
"""EP-INSTRUMENTS-1 · I1 — THE EFFECT-ORDER CENSUS (the enumerator + classifier).

The outside reader's B1 finding — "an effect that cannot be undone must follow the gate's
decision, not precede it" — made a STANDING census: found once, now found everywhere.

WHAT IT CENSUSES
    Every handler registered on the gate (`gate.list()` is the completeness guarantee — "the
    bank has no counter", P3). For each, it reads the handler's SOURCE and classifies:

        handler  ->  touches bytes/the world?  ->  reversible | irreversible  ->  effect-after-decide?

    The classifier is MECHANICAL, over the AST of each handler: it finds every call to an
    IRREVERSIBLE byte/world primitive (the blob hand_off, a local byte removal, a real wire
    send) and asks ONE question of each — is the call DEFERRED (wrapped in a thunk the gate
    fires AFTER its decide passes, at `gate.py`'s reserved IRREVERSIBLE_EFFECT key) or INLINE
    (run inside the handler body, before the gate can refuse the act)?

THE LAW IT PROVES (B1, as corrected by archi P1: DECIDE -> EFFECT -> APPEND)
    A handler PROPOSES a draft; the gate's passes DECIDE it; only then does an irreversible
    effect fire; then the append attests it. So a standing rule that refuses the act at the
    gate leaves NO effect. An irreversible effect run INLINE removes the bytes before the
    gate's rule-refusal could stop it — a refused act with a real effect. The census REDS on
    exactly that shape.

WHY THE HOST READING IS RECORD-ONLY FOR MOST OPS
    On this host the socket/device/mount wire is a MODELLED table: the gate handlers RECORD a
    decision and the real arm is the guest's alone (EP-00 rule 9; the socket-grant law states
    this in the pack itself). So the only irreversible byte effect reachable from a gate
    handler on the host is the handover ceremony's blob `hand_off`, and it is DEFERRED. That is
    not an assumption the census makes — it is the reading the census PRODUCES, one row per
    handler, and it REDS the day a handler is added that removes a byte inline.

USAGE
    python3 -m tools.conformance.effect_order_census          # print the classification table
    python3 -m tools.conformance.effect_order_census --md     # emit the evidence markdown body
"""

import ast
import inspect
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(os.path.dirname(_HERE)), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


# ---- the vocabulary of an IRREVERSIBLE byte/world effect -------------------------------------
# A closed set of PRIMITIVE call targets (by attribute/function name) whose invocation removes a
# byte or reaches the world in a way no later record can undo. This is the census's subject: a
# handler that CALLS one of these has a byte/world effect; whether that effect is lawful is decided
# by WHERE it is called (deferred vs inline), not by the name. Extend this set only by a filed
# ruling — a new irreversible primitive that no row names is exactly what the census must not miss,
# so it is named here in ONE place, read by both the tool and its test.
IRREVERSIBLE_PRIMITIVES = frozenset({
    "hand_off",     # blobs.hand_off — transfer custody then remove the local bytes (design/46)
    "remove",       # os.remove — unlink a path's bytes
    "unlink",       # os.unlink — unlink a path's bytes
    "rmtree",       # shutil.rmtree — remove a subtree
    "rmdir",        # os.rmdir — remove a directory
    "sendall",      # a real wire send (guest-only arm; named so a host regression is caught)
    "truncate",     # shrink a file's bytes irrecoverably
})

# The reserved draft key at which a handler defers its irreversible effect for the gate to fire
# AFTER the decision (gate.py IRREVERSIBLE_EFFECT = "_irreversible_effect"). Read from the source
# rather than re-typed, so a rename in the gate cannot silently desync this census.
def _deferred_key():
    from kernel.gate import IRREVERSIBLE_EFFECT
    return IRREVERSIBLE_EFFECT


# ---- the mechanical classifier ---------------------------------------------------------------

class _EffectFinder(ast.NodeVisitor):
    """Walk a handler's AST; record every call to an irreversible primitive and whether that call
    sits inside a Lambda/nested-def (DEFERRED — the gate fires the thunk after its decision) or in
    the handler body (INLINE — it runs before the gate can refuse)."""

    def __init__(self):
        self.findings = []          # list of (primitive, deferred: bool)
        self._lambda_depth = 0

    def visit_Lambda(self, node):
        self._lambda_depth += 1
        self.generic_visit(node)
        self._lambda_depth -= 1

    def _nested_def(self, node):
        # a nested FunctionDef inside the handler is also a deferred thunk body IF it is the
        # value handed to the reserved key; conservatively we treat the OUTER handler function
        # (depth 0 for the census — see classify_source) as the body and any deeper def/lambda as
        # deferred. The outer handler itself is entered at depth 0 by classify_source.
        self._lambda_depth += 1
        self.generic_visit(node)
        self._lambda_depth -= 1

    visit_FunctionDef = _nested_def
    visit_AsyncFunctionDef = _nested_def

    def visit_Call(self, node):
        fn = node.func
        prim = None
        if isinstance(fn, ast.Attribute) and fn.attr in IRREVERSIBLE_PRIMITIVES:
            prim = fn.attr
        elif isinstance(fn, ast.Name) and fn.id in IRREVERSIBLE_PRIMITIVES:
            prim = fn.id
        if prim is not None:
            self.findings.append((prim, self._lambda_depth > 0))
        self.generic_visit(node)


def classify_source(src):
    """Classify a handler's source text. Returns a dict:
        {touches: 'bytes/world'|'none', primitives: [...], effect_site: 'deferred'|'inline'|'none',
         irreversible: bool}
    The OUTER handler body is depth 0 (INLINE); a Lambda or nested def inside it is depth>0
    (DEFERRED). This matches the gate's contract exactly: the handler builds the draft inline and
    hands the irreversible tail to the reserved key AS A THUNK, which the gate fires post-decision.
    """
    # dedent to the handler's own column so ast.parse accepts a nested def/closure source
    src = _dedent(src)
    tree = ast.parse(src)
    # If the source is `def handler(...): ...`, descend into the outer function body at depth 0.
    finder = _EffectFinder()
    body = tree.body
    if len(body) == 1 and isinstance(body[0], (ast.FunctionDef, ast.AsyncFunctionDef)):
        for stmt in body[0].body:
            finder.visit(stmt)
    else:
        for stmt in body:
            finder.visit(stmt)
    prims = [p for p, _ in finder.findings]
    if not finder.findings:
        return {"touches": "none", "primitives": [], "effect_site": "none", "irreversible": False}
    any_inline = any(not deferred for _, deferred in finder.findings)
    return {
        "touches": "bytes/world",
        "primitives": sorted(set(prims)),
        "effect_site": "inline" if any_inline else "deferred",
        "irreversible": True,
    }


def _dedent(src):
    import textwrap
    return textwrap.dedent(src)


def _handler_source(handler):
    """The source of a handler's ACTUAL body. Registered handlers are closures returned by a
    factory (`handover_handler` returns `_handover`); `inspect.getsource` on the closure returns
    the inner def, which is exactly the body that runs — the right subject."""
    try:
        return inspect.getsource(handler)
    except (OSError, TypeError):
        return None


# ---- enumerate + classify the live registry --------------------------------------------------

def build_full_kernel_for_census():
    """A composed full kernel — the widest byte/world surface (sockets, devices, mounts, the
    handover ceremony) — in a throwaway dir. Measurement only; nothing is driven."""
    from kernel import compose
    from kernel import erasure
    d = tempfile.mkdtemp(prefix="i1-census-")
    store, gate, views = compose.build_full_kernel(
        os.path.join(d, "rec.jsonl"), os.path.join(d, "blobs"))[:3]
    # register the handover ceremony so its irreversible-effect handler is in the census (the
    # production mover is held; the ceremony logic is the exact production logic — erasure.py).
    try:
        erasure.register_ceremony(gate, views)
    except Exception:
        pass
    return store, gate, views


def census(gate):
    """The census: one row per registered handler, sorted by name.
    Each row: {op, touches, primitives, effect_site, irreversible}."""
    rows = []
    for name in sorted(gate.ops):
        handler = gate.ops[name]["handler"]
        src = _handler_source(handler)
        if src is None:
            rows.append({"op": name, "touches": "unknown", "primitives": [],
                         "effect_site": "unknown", "irreversible": False})
            continue
        c = classify_source(src)
        c["op"] = name
        rows.append(c)
    return rows


def byte_world_rows(rows):
    return [r for r in rows if r["touches"] == "bytes/world"]


def inline_irreversible_rows(rows):
    """THE RED SET: any byte/world handler whose irreversible effect fires INLINE (before the
    gate's decision). Empty is the whole point; non-empty is B1 violated."""
    return [r for r in rows if r["irreversible"] and r["effect_site"] == "inline"]


# ---- the evidence table (P4: one row per handler, a persisted artifact) -----------------------

def render_markdown(rows):
    bw = byte_world_rows(rows)
    out = []
    out.append("<!-- GENERATED by tools/conformance/effect_order_census.py — do not hand-edit. -->")
    out.append("<!-- Regenerate: python3 -m tools.conformance.effect_order_census --md -->")
    out.append("")
    out.append("# I1 · Effect-order census — one row per handler")
    out.append("")
    out.append("The gate is the sole appender; a handler PROPOSES a draft and the gate DECIDES it "
               "before any irreversible effect fires (B1: DECIDE -> EFFECT -> APPEND). This table "
               "is the census's reading of every registered handler. A handler that removes a byte "
               "INLINE (before the decision) would show `effect_site=inline` and RED the census.")
    out.append("")
    out.append(f"Registered handlers censused: **{len(rows)}**. "
               f"Byte/world (irreversible-primitive) handlers: **{len(bw)}**. "
               f"Inline-irreversible (must be zero): **{len(inline_irreversible_rows(rows))}**.")
    out.append("")
    out.append("## Byte/world handlers")
    out.append("")
    out.append("| handler | touches | primitive(s) | effect site | order OK |")
    out.append("|---|---|---|---|---|")
    for r in bw:
        ok = "yes (deferred, post-decision)" if r["effect_site"] == "deferred" else "**NO — INLINE**"
        out.append(f"| {r['op']} | {r['touches']} | {', '.join(r['primitives'])} | "
                   f"{r['effect_site']} | {ok} |")
    out.append("")
    out.append("## Record-only handlers (no irreversible byte/world primitive at the gate)")
    out.append("")
    out.append("On this host the socket/device/mount wire is a MODELLED table (the real arm is the "
               "guest's alone, EP-00 rule 9), so these handlers RECORD a decision and reach no "
               "irreversible primitive. Listed for completeness — the census is over ALL handlers.")
    out.append("")
    recs = [r["op"] for r in rows if r["touches"] == "none"]
    out.append("`" + "`, `".join(recs) + "`" if recs else "_none_")
    unknown = [r["op"] for r in rows if r["touches"] == "unknown"]
    if unknown:
        out.append("")
        out.append("## Handlers whose source could not be read (builtins/C)")
        out.append("`" + "`, `".join(unknown) + "`")
    out.append("")
    return "\n".join(out)


EVIDENCE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(_HERE)),
    "planning", "evidence", "EP-INSTRUMENTS-1", "effect-order.md")


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    _store, gate, _views = build_full_kernel_for_census()
    rows = census(gate)
    if "--md" in argv:
        print(render_markdown(rows))
        return 0
    bw = byte_world_rows(rows)
    print(f"censused {len(rows)} handlers; {len(bw)} byte/world; "
          f"{len(inline_irreversible_rows(rows))} inline-irreversible (must be 0)")
    for r in bw:
        print(f"  {r['op']:24s} {r['effect_site']:9s} {','.join(r['primitives'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
