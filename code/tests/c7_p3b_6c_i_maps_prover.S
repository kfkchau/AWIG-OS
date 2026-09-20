/* gov-os body — the C7 P3b-6c (i) MAPS PROVER: OUR small hand-written ring-3 test enclosure.
 *
 * A bare static x86_64 image of OURS (no C runtime, no libc), loaded by the body's OWN ELF64 loader from a
 * SEALED image and run UNPRIVILEGED (ring 3). It proves PER-ENCLOSURE ADDRESS MAPS: two instances of this
 * program are made RESIDENT AT ONCE, each in its OWN page-table hierarchy, and each writes a distinct
 * SENTINEL to the SAME virtual base 0x400000 — which land on DISTINCT physical frames with no aliasing when
 * each enclosure has its own map. This is a tests/ FIXTURE (content, NEVER a signed member, §9 mechanism 3 /
 * I3); it is not under src/, so ATTESTED_MEMBERS stays 88. Every build and boot is the guest's nested qemu
 * (L11 / EP-00 rule 9); nothing here runs on the host kernel. Validate by building/reading, never by attack.
 *
 * The body maps a WRITABLE user page at the canonical base 0x400000 (the sentinel page) in each enclosure's
 * OWN map, and loads THIS code above it at 0x401000 — so the write to 0x400000 never touches the code page.
 *
 * ONE entry (_mstart), dispatching on %rdi (the mode the body sets at entry), %rsi the argument:
 *   %rdi == 0  -> WRITE: store the sentinel (%rsi) to 0x400000, read it BACK, store the read-back to
 *                0x400008 — the body reads the read-back to confirm the ring-3 write/read saw its own frame.
 *   %rdi == 2  -> READ:  read 0x400000 (whatever persisted under this map), store it to 0x400008 — used
 *                after a hand-off to confirm the enclosure's state survived the map swap.
 *   %rdi == 1  -> FAULT: read a BODY address (%rsi, a supervisor page). The hardware FAULTS it (#PF) — the
 *                enclosure is a hardware fact (L18); the body catches it and recovers PER MAP. Only if the
 *                machine FAILED to enforce (never, on correct hw) is the next line reached, marking it.
 *   then EXIT (REQ_EXIT == 5): the body regains control by the crossing's own recovery.
 */
.code64
.section .text
.global _mstart
_mstart:
    movq $0x400000, %rdx            /* the sentinel page base (the body mapped it USER in THIS map) */
    cmpq $1, %rdi
    je _mfault
    cmpq $2, %rdi
    je _mread

    /* mode 0 — WRITE: sentinel = %esi; read it back; store the read-back at 0x400008. */
    movl %esi, (%rdx)              /* *(uint32_t*)0x400000 = the sentinel                          */
    movl (%rdx), %eax             /* read it back (ring-3 read of THIS enclosure's own frame)      */
    movl %eax, 8(%rdx)            /* *(uint32_t*)0x400008 = the read-back the body confirms        */
    jmp _mexit

_mread:
    /* mode 2 — READ: read 0x400000 (persisted), store to 0x400008 (the body confirms it survived). */
    movl (%rdx), %eax
    movl %eax, 8(%rdx)
    jmp _mexit

_mfault:
    /* mode 1 — FAULT: a direct ring-3 read of a BODY supervisor page. The hardware #PFs it (L18). */
    movq (%rsi), %rax             /* <-- #PF here: a ring-3 read of a supervisor body page */
    movl $0xDEAD, 8(%rdx)         /* reached ONLY if the boundary was NOT enforced (the machine failed) */

_mexit:
    movq $5, %rax                  /* REQ_EXIT — end this enclosure */
    syscall
.mhang:
    jmp .mhang                     /* EXIT never returns; a guard if it somehow did */
