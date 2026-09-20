/* gov-os body — the C7 P3b-6c (i) MAPS PROVER's linker script (a tests/ FIXTURE, never a signed member).
 *
 * Lays OUR test enclosure's CODE at 0x401000 — one virtual page ABOVE the canonical base 0x400000. The
 * body maps a WRITABLE sentinel page at 0x400000 itself (in each enclosure's OWN map), so the enclosure
 * occupies [0x400000, 0x401000+code) — the SAME base every ordinary program (the interpreter, the lwIP
 * worker) is linked at — while the write to 0x400000 never overwrites this code (which lives at 0x401000).
 * ET_EXEC, one fixed base; deterministic link (no build-id, no timestamps) so the image and its seal are
 * byte-reproducible. */
ENTRY(_mstart)

SECTIONS
{
    . = 0x401000;                   /* the code page — one page above the shared canonical base */

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
