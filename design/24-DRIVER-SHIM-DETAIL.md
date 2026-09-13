<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=FROZEN supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — Driver-Shim Detail (binding existing Linux drivers to the governed boundary)

> **SUPERSESSION NOTE (2026-07-18 line-audit).** STANDS, UNBUILT: pure Campaign 3 (DEPTH)
> material — binding unmodified Linux drivers to the governed boundary is a hollow-out
> concern with no user-space analogue, so nothing in campaigns 1–2 touched it. Its four
> crossings → existing record classes derivation is intact and waiting for the devices/
> drivers stage of DEPTH. Live canon controls only if a later ruling reshapes the boundary.

**Status:** v0.1, 2026-07-12, xhigh, Route-A assumption. The last named-not-done
item (03 §8, 10 §12): how existing, unmodified Linux drivers bind to gov-os's
device subsystem through the typed, validated boundary (03 §4.4) without rewriting
them. Without this, "same ports" fails at the hardware edge — thousands of drivers
cannot be reimplemented. The shim is how the driver subsystem is *governed* while
the drivers stay *Linux*. Read 03 §4.4 and doc 11 §2.4/§3.4/§4.1 first. Labels per
`00-READ-FIRST`.

---

## 1. The problem the shim solves

A conventional Linux driver does four ungoverned things: it **registers** by
mutating a global table; it **binds** to a device by probe; it takes
**interrupts** by installing a handler; it moves **I/O** by direct DMA/MMIO. None
of these leaves a record, and the driver runs as fully-trusted in-kernel code
(03 §4.4's diagnosis: capability without law). Reimplementing every driver is
impossible (Route A's whole premise is *not* rewriting the world). So the shim
**wraps the four driver entry points**, translating each into the governed forms
already specified — and the driver's own code is untouched.

The shim is the device subsystem's version of the port contract: the driver sees
the Linux driver API it expects; gov-os sees governed records.

---

## 2. The four wrapped entry points (each maps to an already-specified record)

The shim mediates exactly the four boundary crossings and maps each to a record
class already defined in doc 11 — introducing **no new record type** (minimality
gate):

| Linux driver action | Shim translates to | Record (doc 11) | Class |
|---|---|---|---|
| `register_driver` / module init | a **capability registration** — the driver declares which device class + capabilities (DMA, IRQ line, MMIO range) it may use | `register-driver` → `cap:driver:X@v` | **LAW** (§2.4) |
| `probe` / bind to a device | a **bind decision** citing the driver's capability LAW | `bind-device` | **DECISION** (§3.4) |
| interrupt fires | an **IRQ arrival** input | `irq-arrival` | **INPUT** (§4.1) |
| DMA/MMIO read/write | **device I/O** | (throughput aggregate) | **STREAM** (03 §4.4) |

Everything a driver does decomposes into these four. Registration is the only
LAW step and it happens once per driver, at load, under a named authority (the
device-governor) — this is where "capability is law" (03 §4.4, twc R14) bites: a
driver that has not been registered as a capability **cannot bind**, because
`bind-device` must cite a `cap:driver:X@v` record that does not exist → refusal,
itself recorded (doc 12, `bind-device` refusal cites `CAP-IS-LAW`).

---

## 3. The typed boundary (what "validated" means concretely)

03 §4.4 says driver calls "cross a validated, typed boundary." Concretely, the
shim enforces three checks at the boundary — the device subsystem's equivalent of
the gate's op-validation:

1. **Capability containment.** A driver may only touch the IRQ lines, DMA ranges,
   and MMIO regions enumerated in its `cap:driver:X@v` registration. A DMA to an
   unregistered physical range is refused and recorded — the driver cannot reach
   memory it was not granted. This is the isolation of 03 §4.4, realised as a
   capability check, not a rewrite of the driver.
2. **Binding precondition.** No I/O record without a prior `bind-device` decision;
   no bind without a prior capability LAW. The chain LAW → bind → I/O is enforced,
   so "which driver touched this device, when, under whose authority" is always a
   replay (the gap 03 §4.4 diagnoses).
3. **Fault containment.** A driver fault (crash, DMA violation, IRQ storm) is
   caught at the boundary and handled by the failure book (`15-` FB5): the binding
   is revoked (a recorded `unbind-device` decision citing the fault), the device
   quiesced, the fault recorded. The driver's misbehaviour is contained by the
   *boundary*, governed and recorded — where a conventional kernel would let the
   trusted driver corrupt state silently.

**Honest scope of the isolation (per the standing guard).** This is *governance*
of the device boundary, not a security-hardening frame: the point is that every
capability, bind, and fault is **recorded and rule-cited**, so the device layer is
auditable and amendable. Physical enforcement strength (whether the boundary is a
hardware IOMMU or a software check) is a deployment choice; the *governed record*
is the architecture. (Re-root: 03 §0 — the frame is derivation, not threat models.)

---

## 4. Where the shim lives across the bridge stances (16-)

The shim is not one artifact; it thickens across the bridge:

- **Stance 2 (shadow):** the shim only *observes* — it reads Linux's existing
  driver/device events (via the kernel's own tracepoints/netlink) and records them
  as the four record types, deriving a shadow binding table. Linux drivers are
  authoritative; gov-os audits. Zero risk, and it already yields the "which driver
  held this device when" ledger Linux lacks.
- **Stance 3–4 (assume):** the shim *interposes* — driver entry points are routed
  through it, capability/binding/fault checks become enforcing (not just
  observing), and the governed binding table becomes authoritative behind the same
  Linux driver API. The driver still doesn't know; the boundary now governs.

So the shim follows the same shadow → assume → retire path (`16-`, 03 §6) as every
other subsystem: observe first (safe, valuable), enforce later.

---

## 5. What this closes, and the honest residue

**Closed:** the hardware edge of "same ports." Existing Linux drivers bind through
the shim unmodified; their four boundary crossings map onto the already-specified
LAW/DECISION/INPUT/STREAM records with no new record type; the LAW→bind→I/O chain
makes the device layer auditable; faults are contained and recorded. The last
named-not-done architecture item is specified.

**Residue (honest, named):**
- **Per-driver-class detail** (block vs net vs char vs GPU have different I/O
  shapes and DMA patterns) is not enumerated here — this is the *general* shim
  contract; a class-specific annex is a later, mechanical pass, not an architecture
  gap.
- **`ioctl` is the wildcard** (10 §7): a command ioctl is a DECISION crossing the
  boundary, a query ioctl is a CACHE read, and the op-number determines which — a
  per-driver mapping table the shim needs, deferred to the class annex.
- **Physical enforcement** (IOMMU programming, MMIO trapping) is deployment-level
  mechanism, not architecture; the architecture fixes *what is recorded and
  checked*, not *which hardware feature enforces it*.
- **Trained-knowledge flag:** the Linux driver model (register/probe/irq/dma,
  tracepoints, netlink, IOMMU) is trained knowledge (Estimate — High); the mapping
  of its four crossings onto the governed record classes is derived from 03 §4.4
  and doc 11.
