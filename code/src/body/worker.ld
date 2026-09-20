/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — OUR test worker's linker script (C7 P3b-4a; re-linked C7 P3b-4m, L20).
 *
 * Lays the bare static worker at the platform's CANONICAL BASE (0x400000, x86_64 ET_EXEC) — where every
 * ordinary program, the interpreter included, is linked to load (L20). The body vacated that range (its
 * own image sits beneath it at 1 MiB and the supervisor identity map is withdrawn from the program's
 * range), so the body's ELF64 loader maps the worker's PT_LOAD segments as USER pages there on fresh page
 * tables and the worker runs enclosed. The worker is NOT re-linked to fit the body (L19/L5): the body is
 * laid out to fit the program, and this is the program's own base. ET_EXEC, one fixed base — the loader
 * reads e_entry and the PT_LOAD program headers from the sealed image and maps by p_vaddr. Deterministic
 * link (no build-id, no timestamps) so the worker image is byte-reproducible and its seal is stable. */
ENTRY(_wstart)

SECTIONS
{
    . = 0x400000;                   /* the canonical base (L20) — the program's range, user space */

    .text : { *(.text*) }
    .rodata : { *(.rodata*) }
    .data : { *(.data*) }
    .bss : { *(.bss*) *(COMMON) }

    /DISCARD/ :
    {
        *(.eh_frame)
        *(.eh_frame_hdr)
        *(.comment)
        *(.note)
        *(.note.*)
    }
}
