/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the linker script (C7 P3b-1; RE-BASED for the x86_64 long-mode body, C7 P3b-4L).
 * Loads the freestanding body at 1 MiB (the multiboot convention) with the multiboot header first so
 * it sits at the flat image's byte 0 (== load_addr). `_load_start`/`_load_end`/`_bss_end` feed the
 * multiboot a.out-kludge address fields (boot.S); `kernel_end` marks the image top so the PMM reserves
 * the body's own frames. The linked ELF is objcopy'd to a flat binary that qemu -kernel boots
 * (build.sh) — qemu's multiboot loader ELF-parses only 32-bit ELFs, so the flat image is what boots.
 * Every build+link is the guest's; nothing here targets the host kernel. */
ENTRY(_start)

SECTIONS
{
    . = 1M;
    _load_start = .;                 /* == load_addr in the multiboot header (0x100000) */

    .text BLOCK(4K) : ALIGN(4K)
    {
        *(.multiboot)      /* the multiboot1 header must come first (flat image byte 0) */
        *(.text)
    }

    .rodata BLOCK(4K) : ALIGN(4K)
    {
        *(.rodata)
        *(.rodata.*)
    }

    .data BLOCK(4K) : ALIGN(4K)
    {
        *(.data)
    }

    /* the end of the loaded (PROGBITS) data — the flat image ends here; the loader zeroes from here
     * to _bss_end (the body's .bss: the boot stack, the scaffold + real page tables, the bitmap, the
     * heap). */
    _load_end = .;

    .bss BLOCK(4K) : ALIGN(4K)
    {
        *(COMMON)
        *(.bss)
    }

    /* the top of the loaded image — the PMM reserves 0 .. kernel_end so the body never hands out a
     * frame it is itself standing on; the multiboot loader zeroes _load_end .. _bss_end. */
    kernel_end = .;
    _bss_end = .;

    /* C7-MAINT-4D-BOOT-AS-MODULE — FAIL THE BUILD LOUDLY if the body's end-of-data crosses the canonical
     * base. The body is a higher-half kernel: vmm_init keeps the supervisor identity map only for
     * [0, CANONICAL_BASE) and WITHDRAWS the program's range [CANONICAL_BASE, 1 GiB) at the CR3 switch
     * (body.h:64-73; design/54 L20). Any body byte at or above the base is unmapped the instant paging
     * turns on, so the first access to it triple-faults at "VMM: paging enabled" (FINDINGS.md F1/F2). This
     * assert turns that silent boot-time triple-fault into a loud build failure for the WHOLE class (an
     * over-size incbin, a large static buffer, .bss growth). The 0x400000 literal mirrors body.h:71
     * CANONICAL_BASE — a linker script cannot include the C header; a divergence here is itself caught by
     * the same boot this guard protects (a body over the base cannot reach its run floor). The fix for a
     * body that trips this is to carry large sealed images as a boot-time module (-initrd), never embed. */
    ASSERT(_bss_end < 0x400000,
           "body image end-of-data crosses the 4 MiB canonical base (body.h CANONICAL_BASE) -- carry large sealed images as a boot-time module (-initrd), do not embed them; see C7-MAINT-4D-BOOT-AS-MODULE / FINDINGS.md F1/F2")

    /* Drop orphan sections so nothing pushes the multiboot header out of the first-8 KiB scan window
     * (a build-id note or eh_frame landing first is what breaks the load) and to keep the flat image
     * and the .elf byte-reproducible. */
    /DISCARD/ :
    {
        *(.eh_frame)
        *(.eh_frame_hdr)
        *(.comment)
        *(.note)
        *(.note.*)
    }
}
