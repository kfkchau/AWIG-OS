"""EP-24B — the standing differential between the accelerated folds and the retained
unaccelerated folds. [EXTENDED BY EP-24C to the three per-act-path view folds.]

This is not a test file (the suite's discovery pattern is `test_*.py`); it is the
comparator `tests/test_ep24b.py`, `tests/test_ep24c.py` and the whole-suite sweep below all
import, so there is ONE implementation of "run both folds and compare" rather than several
that could drift.

WHAT IT COMPARES. Every member of `Views.AUTHORITY_FOLDS`, driven with an argument
population DERIVED FROM THE WORLD ITSELF — the accounts, actions, info kinds, spaces and
roles the record actually holds, plus deliberate misses (an unfounded space, an account
with no grant, an action nobody was granted). A fixed argument list would stop covering a
world that grew; this one grows with it. And, since EP-24C, every member of
`Views.PER_ACT_FOLDS` — the op-definition, law and vocabulary folds — which take no
arguments, so their whole population is the world plus the as-of points.

WHY THE VIEW FOLDS ARE HERE AT ALL, since EP-24C's scope is three items and this is not a
fourth: property 2 of that EP requires the stored-table proofs per fold rather than once for
the set, and a differential is the instrument that proves them. Extending it is how the item
lands, not an addition beside it.

WHAT A DIVERGENCE MEANS. A defect, never a discovery. Both sides are current code running
the SAME fold body; the only variable is the record source. So a difference can only mean a
subset failed to select a record the fold needed — which is the one failure mode a
projection has, and the reason this comparator is permanent rather than a one-off proof.

THE WHOLE-SUITE SWEEP. Run this file directly to wrap `Views.authority_fold` and
`Views.view_fold` so that EVERY answer either family gives to EVERY test in the PRE-EXISTING
suite is computed twice and compared:

    python3 tests/ep24b_differential.py

It reports the number of comparisons and exits non-zero on any divergence.

THE EXCLUSIONS ARE DECLARED, NOT APPLIED IN PASSING (EP-24C W4, directed at the EP-24B
verdict). `SWEEP_EXCLUDED` below names every test file the sweep skips and why, and
`tests/test_ep24c.py` guards it in both directions: an excluded file that no longer exists
is a stale row, and a file skipped without a declared reason is a silent change to what the
divergence count means. An undeclared exclusion list is worse than a wrong one, because the
next person to add a can-fail control elsewhere cannot see that the number moved.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from kernel.authority import WILDCARD          # noqa: E402
from kernel.views import Views                 # noqa: E402

UNFOUNDED_SPACE = "space:never-founded"

# ---- the DECLARED sweep exclusions (EP-24C W4) -------------------------------------------
# A test file appears here only because instrumenting it measures the instrument. Each row
# carries its reason in full; `tests/test_ep24c.py` fails on a row whose file has gone, and
# on any file the sweep skips that is not declared here.
SWEEP_EXCLUDED = {
    "test_ep24b.py":
        "It carries this comparator natively, so wrapping the folds around it measures the "
        "instrument twice. Worse, two of its tests exist to prove the comparator and the "
        "coherence check CAN fail, and they do it by deliberately stripping every grant out "
        "of the governance index; under the wrapper those controlled sabotages report as "
        "hundreds of real-looking divergences, and a third test asserts a timing against the "
        "very oracle it is supposed to beat. The sweep's job is the OTHER worlds.",
    "test_ep24c.py":
        "The same reason one EP later, for the three view-fold projections: its can-fail "
        "controls stall and mutilate those projections on purpose, and its guard tests "
        "install a synthetic whole-record fold on the per-act path to prove the guard fires. "
        "Every one of those would read as a divergence or a failure under the wrapper.",
}


def _population(views):
    """The argument sets, read off the world. Bounded on purpose: the cross product is run
    at three as-of points, so each dimension stays small enough to keep the whole
    comparison inside a few seconds while still covering all four grant dimensions, space
    containment and the role route."""
    grants = views.grants()
    spaces = list(views.spaces())
    roles = list(views.roles())
    accounts = sorted(views.accounts())[:4]
    # subjects named by grants (including the wildcard) + an account nobody granted anything
    granted = [g["grantee"] for g in grants.values() if g["grantee"] not in (None, WILDCARD)]
    actors = sorted(set(accounts + granted + ["nobody-at-all"]))[:6]
    actions = sorted({a for g in grants.values() for a in _dim_members(g["actions"])}
                     | {"CREATE-INFO", "CREATE-RULE", "GRANT", "never-granted-action"})[:6]
    infos = sorted({i for g in grants.values() for i in _dim_members(g["info"])}
                   | {"law", "op_definition", "never-granted-kind"}, key=str)[:4]
    targets = (spaces + [UNFOUNDED_SPACE, None])[:5]
    return actors, actions, infos, targets, spaces, roles


def _dim_members(dim):
    if dim == WILDCARD or dim is None:
        return set()
    if isinstance(dim, (list, tuple, set, frozenset)):
        return set(dim)
    return {dim}


def fold_calls(views):
    """(fold name, args) for every authority fold, over the derived population."""
    actors, actions, infos, targets, spaces, roles = _population(views)
    yield ("mother_space", ())
    yield ("spaces", ())
    yield ("roles", ())
    for outer in spaces + [UNFOUNDED_SPACE]:
        for inner in targets:
            yield ("space_reaches", (outer, inner))
    for a in actors:
        yield ("power_view", (a,))
        for t in targets:
            yield ("reaches_space", (a, t))
    for r in roles + ["role:never-founded"]:
        yield ("role_meaning", (r,))
    yield ("grants", ())
    for payload in ({"space": s} for s in targets):
        yield ("space_of", ({"payload": payload},))
    yield ("space_of", ({"payload": {}},))
    for a in actors[:3]:
        for act in actions[:3]:
            for sp in targets[:3]:
                yield ("within_makers_reach",
                       (a, {"grantee": a, "actions": [act], "info": "*", "space": sp}))
    for a in actors:
        for act in actions:
            for info in infos:
                for sp in targets:
                    yield ("covers", (a, act, info, sp))


def differential(views, as_of_points=(None,)):
    """Run every AUTHORITY fold on both record sources at every as-of point.

    Returns (compared, divergences). A divergence row names the fold, its arguments, the
    as-of point and both answers, so a failure reads as a fact rather than as a count."""
    compared, divergences = 0, []
    for as_of in as_of_points:
        for name, args in fold_calls(views):
            fast = views.authority_fold(name, *args, accelerated=True, as_of=as_of)
            slow = views.authority_fold(name, *args, accelerated=False, as_of=as_of)
            compared += 1
            if fast != slow:
                divergences.append(f"{name}{args!r} asOf={as_of}: index={fast!r} record={slow!r}")
    return compared, divergences


def view_differential(views, as_of_points=(None,)):
    """EP-24C — the same comparison for the three per-act-path view folds. They take no
    arguments, so the population is the world itself at every as-of point; the folds are read
    off `Views.PER_ACT_FOLDS` rather than listed here, so a fold added to the family without
    a projection cannot slip past this comparator by not being mentioned."""
    compared, divergences = 0, []
    for as_of in as_of_points:
        for name in sorted(views.PER_ACT_FOLDS):
            fast = views.view_fold(name, accelerated=True, as_of=as_of)
            slow = views.view_fold(name, accelerated=False, as_of=as_of)
            compared += 1
            if fast != slow:
                divergences.append(f"{name}() asOf={as_of}: projection={fast!r} record={slow!r}")
    return compared, divergences


def as_of_points(store):
    """A few historical points plus the head — the index filters by seq, so an as-of read is
    a separate way for a subset to be wrong."""
    n = len(store.events)
    return (None, n, max(1, n // 2), max(1, n // 4))


# ---------------------------------------------------------------------------------------
# The whole-suite sweep: every authority answer any test takes, computed twice and compared.
# ---------------------------------------------------------------------------------------

def sweep_modules():
    """The test modules the sweep runs: every `test_*.py` in this directory except the
    DECLARED exclusions. Exposed as a function so the guard in `tests/test_ep24c.py` can
    check the exclusion set against the directory rather than against a copy of this list."""
    here = os.path.dirname(os.path.abspath(__file__))
    return sorted(f[:-3] for f in os.listdir(here)
                  if f.startswith("test_") and f.endswith(".py") and f not in SWEEP_EXCLUDED)


def _sweep():
    import unittest

    state = {"authority": 0, "views": 0, "divergences": []}
    original = Views.authority_fold
    original_view = Views.view_fold

    def checked(self, name, *args, accelerated=True, as_of=None):
        fast = original(self, name, *args, accelerated=True, as_of=as_of)
        slow = original(self, name, *args, accelerated=False, as_of=as_of)
        state["authority"] += 1
        if fast != slow:
            state["divergences"].append(f"{name}{args!r} asOf={as_of}: index={fast!r} record={slow!r}")
        return fast if accelerated else slow

    def checked_view(self, name, accelerated=True, as_of=None):
        fast = original_view(self, name, accelerated=True, as_of=as_of)
        slow = original_view(self, name, accelerated=False, as_of=as_of)
        state["views"] += 1
        if fast != slow:
            state["divergences"].append(
                f"{name}() asOf={as_of}: projection={fast!r} record={slow!r}")
        return fast if accelerated else slow

    names = sweep_modules()
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    print(f"[WHOLE-SUITE DIFFERENTIAL] sweeping {len(names)} test modules "
          f"({', '.join(sorted(SWEEP_EXCLUDED))} excluded — see SWEEP_EXCLUDED above)")
    Views.authority_fold = checked
    Views.view_fold = checked_view
    try:
        result = unittest.TextTestRunner(verbosity=1).run(suite)
    finally:
        Views.authority_fold = original
        Views.view_fold = original_view

    print(f"\n[WHOLE-SUITE DIFFERENTIAL] authority answers compared across the suite: "
          f"{state['authority']}; per-act-path view-fold answers compared: {state['views']}; "
          f"divergences: {len(state['divergences'])}")
    for d in state["divergences"][:20]:
        print("  DIVERGENCE " + d)
    ok = result.wasSuccessful() and not state["divergences"]
    print("[WHOLE-SUITE DIFFERENTIAL] " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_sweep())
