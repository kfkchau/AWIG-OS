# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: conformance-harness ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""The self-test's governed targets: four of them, three deliberately wrong.

EP-24 W4 says the harness must prove its own columns can fail before any baseline
is trusted, and names the three fixtures: one that returns a wrong errno, one that
appends no record for a DECISION row, and one whose replay diverges. This file is
all four — the three, plus the CORRECT one that is the control. Without the
control, a fixture failing proves nothing: every column would "fail" on a target
that is simply broken everywhere.

WHAT MAKES THIS A GOVERNED TARGET, honestly stated. It performs the acts and it
records them, which is the shape of the thing; a wrapper around the probe's own
call vocabulary appends the class-appropriate record at the moment the subject
call returns, so the record brackets the probe writes are exact. The records go
through the REAL `src/kernel/store.py`, so the harness's record reader is proven
against the store's actual envelope rather than against this file's idea of it.

WHAT IT IS NOT. Its replay does not re-derive a filesystem from a record — it
folds the state each record carried. It is a fixture for proving the CHECK fires,
not a proof that anything replays. The first real record and replay adapters land
with the mount at EP-25; that is the EP whose acceptance this instrument exists
to serve.

The wrongness in each broken fixture is REAL, not a rewritten answer:

  wrong-errno       the target's own tree differs before the row runs, so the
                    kernel itself returns EEXIST where the pinned capture has a
                    success. Nothing edits an observation.
  no-record         the target performs the DECISION act and appends nothing.
  replay-diverges   the target records and replays, and the replay drops one
                    entry — the shape a derived tree that is not really derived
                    would have.
"""

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from kernel.store import EventStore  # noqa: E402
from tools.conformance.harness import probe as probe_mod, rows as rows_mod  # noqa: E402

#: The fixture's own class map: action -> recording class. A target declares this;
#: the harness never authors one.
CLASS_MAP = {
    "fixture-custody-decision": "DECISION",
    "fixture-namespace-law": "LAW",
    "fixture-arrival-input": "INPUT",
    "fixture-traffic-stream": "STREAM",
}
BASE_CLASS_MAP = dict(CLASS_MAP)

CLASS_ACTION = {
    "DECISION": "fixture-custody-decision",
    "LAW": "fixture-namespace-law",
    "INPUT": "fixture-arrival-input",
    "STREAM": "fixture-traffic-stream",
}

#: The DEFERRED fixture's vocabulary: one action per act, so a record can say
#: which act it is about even when it is emitted three steps later. The four
#: actions above cannot say that — they are named by CLASS and are appended at
#: the act itself, which is why they declare `*`.
DEFERRED_PREFIX = "fixture-deferred-"


def deferred_action(syscall):
    return DEFERRED_PREFIX + syscall


#: design/10 §11.4a, declared by the target: what each record kind is ABOUT.
#: `*` means "the act under test, named in the record's own payload" — true of the
#: four class-named actions, which are appended by the wrapper around the subject
#: call itself. The deferred kinds name their act instead, because their whole
#: point is to land somewhere else.
COVERS_MAP = {action: ["*"] for action in BASE_CLASS_MAP}
COVERS_MAP.update(
    {deferred_action(sc): [sc] for sc in sorted({s for s in probe_mod.DRIVES.values() if s})}
)
#: A deferred record is a DECISION: the acts this fixture defers are writes.
CLASS_MAP.update({a: "DECISION" for a in COVERS_MAP if a.startswith(DEFERRED_PREFIX)})

RULE = {
    "DECISION": "FIXTURE-CUSTODY-1",
    "LAW": "FIXTURE-NAMESPACE-1",
    "INPUT": None,
    "STREAM": "FIXTURE-COALESCE-1",
}


def _deferred(store, state, name, when_flushed):
    """The DEFERRED target's recording, and it is the mount's shape rather than a
    caricature of it: the act's covering record is BUFFERED when the act happens
    and appended at a later step — the flush boundary — exactly as a folded write's
    covering decision is emitted at the fsync or the close that flushes the burst.

    So the act's own step brackets nothing and a later step brackets a DECISION it
    did not make. Under attribution by landing point that is two failures from one
    act; under §11.4a it is one record, about the write, wherever it lands.
    """
    if name in when_flushed:
        pending, state["pending"] = state.get("pending") or [], []
        for syscall in pending:
            store._append(
                {
                    "actor": "fixture-target",
                    "action": deferred_action(syscall),
                    "object": (state.get("assertion").row_id
                               if state.get("assertion") else "?"),
                    "rule_cited": "FIXTURE-CUSTODY-1",
                    "evidence_summary": "the covering decision for a deferred %s, "
                    "appended at the flush boundary" % syscall,
                    "payload": {"covers": syscall, "flushed_at": name},
                }
            )


def wrap_calls(store, assertions_by_row, state, mode, config=None):
    """Wrap the probe's vocabulary so a subject call also records itself. The
    callable underneath is untouched: the fixture changes who watches the act,
    never how the act is performed."""
    original = dict(probe_mod.CALLS)
    config = config or {}
    records_calls = tuple(config.get("records_calls", ()))
    flush_calls = tuple(config.get("flush_calls", ()))

    def make(name, fn, norm):
        def wrapped(*args, **kwargs):
            if mode == "deferred":
                _deferred(store, state, name, flush_calls)
            value = fn(*args, **kwargs)
            a = state.get("assertion")
            if a is None:
                return value
            if mode == "deferred":
                if name in records_calls:
                    state.setdefault("pending", []).append(probe_mod.DRIVES.get(name) or name)
                # A call that closes its own descriptor is its own flush boundary,
                # so its covering record lands inside its own bracket — which is
                # what the mount does when a probe step opens, writes and closes.
                if name in flush_calls:
                    _deferred(store, state, name, flush_calls)
                return value
            if name not in a.subject_calls(probe_mod.DRIVES):
                return value
            if mode == "no-record" and "DECISION" in a.recording_class:
                return value
            for cls in a.recording_class:
                action = CLASS_ACTION.get(cls)
                if action is None:  # CACHE appends nothing, by design
                    continue
                store._append(
                    {
                        "actor": "fixture-target",
                        "action": action,
                        "object": a.row_id,
                        "rule_cited": RULE[cls],
                        "evidence_summary": "%s under test on the fixture target" % name,
                        "payload": {"row_id": a.row_id, "call": name},
                    }
                )
            return value

        return (wrapped, norm)

    for name, (fn, norm) in original.items():
        probe_mod.CALLS[name] = make(name, fn, norm)
    return original


#: The action a row's closing state record carries. It is DELIBERATELY absent from
#: CLASS_MAP: it is appended after the last step, so it falls outside every subject
#: bracket and check 2 never sees it — and if a change ever did put it inside one,
#: check 2 would refuse it as an unclassified record rather than let it pass.
STATE_ACTION = "fixture-tree-state"

#: The action the descriptor-establishing record carries, DELIBERATELY absent from
#: CLASS_MAP for the same reason `STATE_ACTION` is: it is appended before the first
#: step of the first row, so it falls outside every bracket, and a change that ever
#: put it inside one would be refused as unclassified rather than pass.
READY_ACTION = "fixture-instrument-ready"


def establish_record_descriptor(store):
    """design/10 §11.2b pointed at the DESCRIPTOR TABLE: the instrument establishes
    its own descriptors before any row runs, because one row's subject IS the
    process's descriptor table and the row does not own it.

    `files.close`'s subject is that closing a released descriptor NUMBER returns
    EBADF, and its `close` is a subject call — so `wrap_calls` appends between the
    row's two closes. A store that opens its write descriptor on FIRST APPEND
    allocates it there, mid-row, and the lowest free number at that moment is
    exactly the one the first close released: the second close then lands on the
    store's descriptor, the row's EBADF answer disappears, and the store's next
    append is the thing that gets EBADF. The instrument creates the condition it
    then reports. Measured on this row at EP-28B, repaired here (EP-28D W1).

    One append before the row loop moves that allocation outside every row. It is a
    guard and not a workaround: nothing retries, nothing revalidates a descriptor,
    and no answer is masked — the number a row frees is simply not a number the
    instrument is about to want. Re-validating the descriptor and reopening on EBADF
    was written at EP-28B and REFUSED, because it repairs another component's
    double-release silently, inside the instrument the campaign depends on. Do not
    reinstate it.

    THE HONEST CAP HAS EXPIRED, AND THE REFUTED TEXT IS RETAINED BESIDE ITS CORRECTION
    [EP-28H item 6, 2026-08-02]. It read: *"THE HONEST CAP, because the guard's present
    effect and its purpose differ. The store re-opens the record file per append today
    (`src/kernel/store.py::_append`, the held-descriptor form having been written and
    withdrawn at EP-28B W2), so its claim on the freed number is released before the
    row's next step and this row already answers EBADF. What this line changes today is
    one record; what it is FOR is the held descriptor, whose failure
    `tests/test_ep28d.py` reproduces both ways rather than describing."*

    BOTH HALVES ENDED WITH EP-28C W3. The store does NOT re-open per append: it opens
    the record file once, lazily, and HOLDS it (`src/kernel/store.py:559-564`). So its
    claim on the freed number is NOT released before the row's next step, and THIS
    GUARD'S PRESENT EFFECT IS NOT ZERO. Measured at `tests/test_ep28d.py`'s
    `TestTheRealStoreAsItStands`, which is now the same row driven both ways over the
    REAL store: with this call the row answers EBADF and the descriptor table is
    unchanged across the row; without it the second close lands on the store's live
    descriptor and returns, answering nothing.

    This matters to a reader deciding whether the line may be removed. It may not: the
    text above said the guard did nothing today, and that is the sentence a later seat
    would have read before deleting it.
    """
    return store._append(
        {
            "actor": "fixture-target",
            "action": READY_ACTION,
            "rule_cited": "FIXTURE-CUSTODY-1",
            "evidence_summary": "the instrument's record descriptor, established "
            "before any row runs — design/10 §11.2b",
            "payload": {},
        }
    )


def replay_from_record(row_id, context, config):
    """Check 3's other side: what the target serves after its derived state is
    killed and rebuilt FROM THE RECORD. This reads the record file, folds the last
    tree the row's acts recorded, and returns it — the live observation is not
    consulted, which is the whole point of the leg."""
    record_path = Path(config["record"])
    mode = config.get("mode", "correct")
    tree = None
    if record_path.exists():
        for line in record_path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("action") == STATE_ACTION and rec.get("object") == row_id:
                tree = dict(rec["payload"]["tree"])
    if tree is None:
        return None
    if mode == "replay-diverges" and tree:
        tree.pop(sorted(tree)[0])
    return tree


def main(argv):
    config = json.loads(Path(argv[1]).read_text())
    plan = json.loads(Path(argv[3]).read_text())
    mode = config["mode"]
    record_path = Path(config["record"])
    record_path.parent.mkdir(parents=True, exist_ok=True)
    # A fixture target is disposable and starts from nothing, so each invocation
    # begins with an empty record. Nothing derived survives it either — which is
    # the state the replay leg wants anyway.
    if record_path.exists():
        record_path.unlink()

    _groups, all_rows = rows_mod.load_all()
    by_row = {}
    for r in all_rows:
        by_row[r.row_id] = r
        by_row[r.row_id + "#root"] = r

    scratch_root = os.path.abspath(plan.get("scratch") or ".")
    os.makedirs(scratch_root, exist_ok=True)
    store = EventStore(record_path)
    # BEFORE ANY ROW RUNS (design/10 §11.2b). See establish_record_descriptor.
    establish_record_descriptor(store)
    state = {"assertion": None, "pending": []}
    wrap_calls(store, by_row, state, mode, config)

    rows_out = {}
    for row in plan["rows"]:
        a = by_row.get(row["row_id"])
        state["assertion"] = a
        row_dir = os.path.join(scratch_root, row["row_id"].replace("/", "_"))
        if mode == "wrong-errno" and row["row_id"] == "files.mkdir":
            # A real difference in the target's own tree, chosen so the divergence
            # is a SINGLE variable: the directory the row's first step creates
            # already exists here with the same mode, so the kernel answers EEXIST
            # where the pinned capture has a success — and every later step, and
            # the resulting tree, are identical. One errno, nothing else.
            os.makedirs(row_dir, exist_ok=True)
            if not os.path.isdir(os.path.join(row_dir, "d")):
                os.mkdir(os.path.join(row_dir, "d"), 0o755)
                os.chmod(os.path.join(row_dir, "d"), 0o755)
        try:
            obs = probe_mod.run_row(row, scratch_root, str(record_path))
        except Exception as e:  # noqa: BLE001
            obs = {"driver_error": "%s: %s" % (type(e).__name__, e)}
        rows_out[row["row_id"]] = obs
        # The row's resulting tree, recorded AFTER the last step so it lands
        # outside every subject bracket. This is what the replay leg folds.
        state["assertion"] = None
        store._append(
            {
                "actor": "fixture-target",
                "action": STATE_ACTION,
                "object": row["row_id"],
                "rule_cited": "FIXTURE-CUSTODY-1",
                "payload": {"tree": obs.get("state") or {}},
            }
        )

    uname = os.uname()
    sys.stdout.write(
        json.dumps(
            {
                "probe_version": probe_mod.PROBE_VERSION,
                "fixture_mode": mode,
                "uname": {
                    "sysname": uname.sysname,
                    "release": uname.release,
                    "version": uname.version,
                    "machine": uname.machine,
                },
                "euid_is_root": os.geteuid() == 0,
                "python": sys.version.split()[0],
                "rows": rows_out,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
