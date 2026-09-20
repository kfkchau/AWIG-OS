# gov-os provenance · FRAME: test-tooling · CORPUS-CLASS: test · a pytest-loaded runner-path shim
# for the stranger's plain in-repo run: it puts the repository ROOT (the directory that contains
# tools/ and src/) and the tests/ directory on sys.path so `import tools...` and the sibling test
# helpers (era_pin, ...) resolve with no PYTHONPATH incantation. NON-GOAL: no offensive capability;
# a real path fix, never a skip. Full declaration: SCOPE-STATEMENT.md.
"""Runner path for a plain ``pytest`` run in a fresh checkout or render.

Without PYTHONPATH the repository root is not on ``sys.path``, so ``import tools.*`` reds with
``No module named 'tools'`` (and a bare ``import era_pin`` reds unless tests/ is on the path).
pytest imports this conftest before it collects anything, so inserting the two directories here
resolves those imports for the whole suite. This is a RUNNER-PATH FIX, not a skip: every test
that was runnable stays runnable, it merely finds its imports.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))          # .../tests
_REPO_ROOT = os.path.dirname(_HERE)                         # the repo root: contains tools/, src/

for _p in (_REPO_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
