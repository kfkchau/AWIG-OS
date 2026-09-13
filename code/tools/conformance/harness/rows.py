# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: conformance-harness ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""The row compiler: design/10's rows, as data, compiled into assertions.

design/10 §3 says each row is a test assertion with three independent checks, and
that the map is versioned as the contract — "adding a syscall, or reclassifying
one, is an amendment with authority". This module is the half of that sentence
the harness owns: it reads the rows, applies §11's six cross-cutting rules and
§12's variant rule, and hands out assertions. It contains no knowledge of any
particular syscall, and it must never gain any: a row that needs a code edit here
to compile is a row written wrongly, not a gap in this file.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

ROWS_DIR = Path(__file__).resolve().parent.parent / "rows"

#: design/10 §2 legend. The only five.
CLASSES = ("LAW", "DECISION", "INPUT", "CACHE", "STREAM")

#: A row whose activation EP the campaign plan does not name. It is written down
#: as this sentinel and counted, never left blank and never guessed at: the
#: coverage statement surfaces every one of them for the plan to settle.
UNASSIGNED = "UNASSIGNED"

#: Classes whose calls append a record at all (design/10 §2 audit-consequence column).
RECORDED_CLASSES = ("LAW", "DECISION", "INPUT")

#: design/10 §11.1a's three, declared by a probe whose tested outcome is an error
#: return. It rides the PROBE rather than the row because a row's privileged pass
#: tests a different outcome from its unprivileged one — files.mount succeeds as
#: root and returns EPERM otherwise — and a declaration attached to the row would
#: bind on an outcome it does not describe.
OUTCOME_CLASSES = ("REFUSAL", "ABSENCE", "NOT-GOVERNED")

#: Field names an observation may never carry on a shape-only row (§11.3). The
#: probe's normalizers already refuse to emit them; this list is what makes the
#: rule enforceable rather than merely honoured.
DYNAMIC_FIELDS = (
    "ino",
    "dev",
    "uid",
    "gid",
    "atime",
    "mtime",
    "ctime",
    "blocks",
    "blksize",
    "f_bfree",
    "f_bavail",
    "f_ffree",
    "f_favail",
    "pid",
)


class RowError(ValueError):
    """A row that does not conform to the schema. Loud, never skipped."""


@dataclass(frozen=True)
class Rules:
    """§11, per row. Two of the six are unconditional and cannot be turned off."""

    errno_identity: bool = True  # §11.1 — load-bearing, always
    timing_out_of_contract: bool = True  # §11.6 — always; nothing timed is observed
    ordering: str = None  # §11.2 — the guarantee's name, or None
    shape_only: bool = False  # §11.3
    coalescible: bool = False  # §11.4
    stream_not_lossy: bool = False  # §11.5 — derived from the class list


@dataclass(frozen=True)
class RecordExpectation:
    """What check 2 requires of the records a call appended (ROWS-SCHEMA.md)."""

    required_classes: tuple = ()
    permitted_classes: tuple = ()
    rule_citation_required: bool = False
    coalescing_policy_required: bool = False


@dataclass
class RowAssertion:
    row_id: str
    group: str
    syscall: str
    what_it_does: str
    subsystems: tuple
    recording_class: tuple
    conformance_note: str
    map_ref: str
    status: str
    active: bool
    activates_at: str
    rules: Rules
    record_expectation: RecordExpectation
    probe: dict = None
    root_probe: dict = None
    probe_limits: tuple = ()
    probe_absent_reason: str = None
    #: §11.1a, read from the probe this assertion carries. None where the tested
    #: outcome is not an error return, and the recording check then binds in full.
    outcome_class: str = None
    is_variant: bool = False
    driven_in_primary: bool = False
    rides: str = None
    disputed_because: str = None
    variants: tuple = ()

    #: design/10 §3: three independent checks, named once, carried by every row.
    checks: tuple = field(default=("abi-identity", "recording-class", "replay-invariance"))

    subject_calls_override: tuple = ()

    @property
    def has_probe(self):
        return bool(self.probe and self.probe.get("steps"))

    def subject_calls(self, drives):
        """Which probe-vocabulary entries in this row's step list ARE the call
        under test. Everything else in the list is setup, and its records belong
        to those acts rather than to this row's class.

        Derived, not declared: the row already says which syscall it is about and
        which variants ride it; `drives` says which vocabulary entry calls what.
        A row overrides only where the map's own naming and the available binding
        differ (creat, driven through its documented open-flag equivalent)."""
        if self.subject_calls_override:
            return set(self.subject_calls_override)
        wanted = {self.syscall} | set(self.variants)
        return {name for name, sc in drives.items() if sc in wanted}

    @property
    def has_root_probe(self):
        return bool(self.root_probe and self.root_probe.get("steps"))


def outcome_class(probe, where="probe"):
    """§11.1a's declaration, read off a probe and checked against the only three
    values it may take. A fourth value is a row defect and is refused loudly —
    the point of the subsection is that the author SAYS which of the three is
    true, and an unrecognised word says nothing."""
    if not probe:
        return None
    declared = probe.get("outcome_class")
    if declared is None:
        return None
    if declared not in OUTCOME_CLASSES:
        raise RowError(
            "%s: outcome_class %r is outside design/10 §11.1a's three (%s)"
            % (where, declared, ", ".join(OUTCOME_CLASSES))
        )
    return declared


def derive_rules(raw_rules, classes):
    """§11 applied. `stream_not_lossy` is DERIVED from the class list rather than
    declared, because §11.5 is a consequence of being STREAM-classified, not a
    property a row may opt out of."""
    raw_rules = raw_rules or {}
    unknown = set(raw_rules) - {"ordering", "shape_only", "coalescible"}
    if unknown:
        raise RowError(
            "rules may only override ordering/shape_only/coalescible; got %s"
            % sorted(unknown)
        )
    return Rules(
        errno_identity=True,
        timing_out_of_contract=True,
        ordering=raw_rules.get("ordering"),
        shape_only=bool(raw_rules.get("shape_only", False)),
        coalescible=bool(raw_rules.get("coalescible", False)),
        stream_not_lossy="STREAM" in classes,
    )


def derive_record_expectation(classes, override=None):
    """The class list -> what check 2 requires. Stated once, here, so no row can
    carry a private idea of what its class means."""
    if override:
        return RecordExpectation(
            required_classes=tuple(override.get("required_classes", ())),
            permitted_classes=tuple(override.get("permitted_classes", ())),
            rule_citation_required=bool(override.get("rule_citation_required", False)),
            coalescing_policy_required=bool(
                override.get("coalescing_policy_required", False)
            ),
        )
    required = tuple(c for c in classes if c in RECORDED_CLASSES)
    return RecordExpectation(
        required_classes=required,
        permitted_classes=tuple(classes),
        rule_citation_required=any(c in ("LAW", "DECISION") for c in classes),
        coalescing_policy_required="STREAM" in classes,
    )


def _compile_one(raw, group_meta):
    for required in ("row_id", "syscall", "recording_class", "conformance_note", "status"):
        if required not in raw:
            raise RowError("row %r missing %r" % (raw.get("row_id"), required))
    classes = tuple(raw["recording_class"])
    bad = [c for c in classes if c not in CLASSES]
    if bad:
        raise RowError("row %s: classes outside design/10 §2: %s" % (raw["row_id"], bad))
    if raw["status"] not in ("ENCODED", "DISPUTED"):
        raise RowError("row %s: status must be ENCODED or DISPUTED" % raw["row_id"])
    if raw["status"] == "DISPUTED" and not raw.get("disputed_because"):
        raise RowError("row %s: DISPUTED without disputed_because" % raw["row_id"])
    if not raw.get("probe") and not raw.get("probe_absent_reason"):
        raise RowError("row %s: no probe and no probe_absent_reason" % raw["row_id"])
    for which in ("probe", "root_probe"):
        outcome_class(raw.get(which), "row %s: %s" % (raw["row_id"], which))
    for name, vp in (raw.get("variant_probes") or {}).items():
        outcome_class(vp, "row %s: variant_probes[%s]" % (raw["row_id"], name))

    active = raw.get("active", group_meta.get("active", False))
    return RowAssertion(
        row_id=raw["row_id"],
        group=group_meta["group"],
        syscall=raw["syscall"],
        what_it_does=raw.get("what_it_does", ""),
        subsystems=tuple(raw.get("subsystems", ())),
        recording_class=classes,
        conformance_note=raw["conformance_note"],
        map_ref=group_meta["map_ref"],
        status=raw["status"],
        active=active,
        activates_at=raw.get("activates_at", group_meta.get("activates_at")),
        rules=derive_rules(raw.get("rules"), classes),
        record_expectation=derive_record_expectation(
            classes, raw.get("record_expectation")
        ),
        probe=raw.get("probe"),
        root_probe=raw.get("root_probe"),
        outcome_class=outcome_class(raw.get("probe")),
        probe_limits=tuple(raw.get("probe_limits", ())),
        probe_absent_reason=raw.get("probe_absent_reason"),
        disputed_because=raw.get("disputed_because"),
        variants=tuple(raw.get("variants", ())),
        subject_calls_override=tuple(raw.get("subject_calls", ())),
    )


def _expand_variants(primary, raw):
    """design/10 §12: a variant rides its primary — same class, same note — and
    the row for it is GENERATED, never spelled out. Where a variant is driven
    separately (`variant_probes`), the ride is TESTED; where it is not, the
    assertion says so in its own absent-reason instead of implying coverage."""
    out = []
    variant_probes = raw.get("variant_probes", {})
    driven_in_primary = set(raw.get("driven_in_primary", ()))
    unknown = driven_in_primary - set(primary.variants)
    if unknown:
        raise RowError(
            "row %s: driven_in_primary names non-variants %s"
            % (primary.row_id, sorted(unknown))
        )
    for name in primary.variants:
        vp = variant_probes.get(name)
        if not vp and name in driven_in_primary:
            reason = (
                "driven inside %s's own step list rather than as a separate "
                "assertion: the call is exercised on every capture and verify, and "
                "a divergence from its primary WOULD be seen, but it has no "
                "observation of its own to compare." % primary.row_id
            )
        elif not vp:
            reason = (
                "generated variant of %s (design/10 §12: variants ride their "
                "primary, same class, same note). It is not driven at all, so a "
                "divergence from the primary would not be seen — declared, not "
                "assumed." % primary.row_id
            )
        else:
            reason = None
        out.append(
            RowAssertion(
                row_id="%s~%s" % (primary.row_id, name),
                group=primary.group,
                syscall=name,
                what_it_does=primary.what_it_does,
                subsystems=primary.subsystems,
                recording_class=primary.recording_class,
                conformance_note=primary.conformance_note,
                map_ref=primary.map_ref,
                status=primary.status,
                active=primary.active,
                activates_at=primary.activates_at,
                rules=primary.rules,
                record_expectation=primary.record_expectation,
                probe=vp,
                outcome_class=outcome_class(vp),
                probe_limits=primary.probe_limits,
                probe_absent_reason=reason,
                driven_in_primary=name in driven_in_primary,
                subject_calls_override=primary.subject_calls_override,
                is_variant=True,
                rides=primary.row_id,
                disputed_because=primary.disputed_because,
            )
        )
    return out


def load_group(path):
    raw = json.loads(Path(path).read_text())
    for key in ("group", "map_ref", "rows"):
        if key not in raw:
            raise RowError("%s: group file missing %r" % (path, key))
    meta = {k: raw[k] for k in raw if k != "rows"}
    out = []
    for r in raw["rows"]:
        primary = _compile_one(r, meta)
        out.append(primary)
        out.extend(_expand_variants(primary, r))
    return meta, out


def load_all(rows_dir=None):
    """Every group file in the rows directory, compiled. Returns (groups, rows)."""
    rows_dir = Path(rows_dir or ROWS_DIR)
    groups, rows = {}, []
    for path in sorted(rows_dir.glob("*.json")):
        meta, compiled = load_group(path)
        if meta["group"] in groups:
            raise RowError("duplicate group %s" % meta["group"])
        groups[meta["group"]] = meta
        rows.extend(compiled)
    seen = set()
    for r in rows:
        if r.row_id in seen:
            raise RowError("duplicate row_id %s" % r.row_id)
        seen.add(r.row_id)
    return groups, rows


def active_rows(rows):
    return [r for r in rows if r.active]


def coverage(rows):
    """The coverage statement: what is asserted, what is driven, what is not, and
    why. A blind spot that is counted and named is the estate's own discipline
    (EP-22's window coverage statements); an uncounted one is a lie by omission."""
    out = {
        "rows_total": len(rows),
        "rows_active": 0,
        "rows_inactive": 0,
        "primaries": 0,
        "variants": 0,
        "disputed": [],
        "activation_unassigned": [],
        "active_probed": 0,
        "active_driven_in_primary": 0,
        "active_undriven": [],
        "active_unprobed": [],
        "root_probed": 0,
        "probe_limits": {},
        "by_group": {},
    }
    for r in rows:
        g = out["by_group"].setdefault(
            r.group, {"total": 0, "active": 0, "probed": 0, "activates_at": r.activates_at}
        )
        g["total"] += 1
        out["variants" if r.is_variant else "primaries"] += 1
        if r.status == "DISPUTED":
            out["disputed"].append(r.row_id)
        if not r.active and r.activates_at in (None, "", UNASSIGNED):
            out["activation_unassigned"].append(r.row_id)
        if r.active:
            out["rows_active"] += 1
            g["active"] += 1
            if r.has_probe:
                out["active_probed"] += 1
                g["probed"] += 1
            elif r.driven_in_primary:
                out["active_driven_in_primary"] += 1
                out["active_unprobed"].append(
                    {"row_id": r.row_id, "reason": r.probe_absent_reason}
                )
            else:
                out["active_undriven"].append(
                    {"row_id": r.row_id, "reason": r.probe_absent_reason}
                )
                out["active_unprobed"].append(
                    {"row_id": r.row_id, "reason": r.probe_absent_reason}
                )
            if r.has_root_probe:
                out["root_probed"] += 1
        else:
            out["rows_inactive"] += 1
        if r.probe_limits:
            out["probe_limits"][r.row_id] = list(r.probe_limits)
    return out
