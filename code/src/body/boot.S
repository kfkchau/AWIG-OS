/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the multiboot1 32-bit entry, TRAMPOLINED into the machine's own long mode
 * (C7 P3b-4L; design/54 §5 L18, §7 P3b-4L; §9 Q12). RE-BASED from 32-bit protected mode onto
 * x86_64 long mode.
 *
 * qemu's -kernel loader recognizes the multiboot1 header and enters _start in 32-bit protected
 * mode with a flat GDT and paging OFF — no bootloader, no GRUB, no Linux beneath. This entry is a
 * TRAMPOLINE: it saves the (magic, multiboot-info) the loader left in eax/ebx, builds an initial
 * four-level identity map (a bring-up SCAFFOLD, 2 MiB huge pages over the low 1 GiB), turns on PAE,
 * sets EFER.LME, enables paging (CR0.PG), loads a temporary GDT with a 64-bit code segment, and
 * FAR-JUMPS into 64-bit code — after which it reloads the data segments, restores (magic,
 * multiboot-info) into the 64-bit ABI's argument registers, and calls kmain. The body then REPLACES
 * this scaffold with its OWN four-level tables in vmm_init (precision 2). Every boot is the guest's
 * NESTED qemu (L11 / EP-00 rule 9); this asm never runs on the host kernel.
 *
 * PRECISION 3 (archi :4082, the HOW rider): the loader's (magic, multiboot-info) in eax/ebx MUST
 * survive the trampoline into 64-bit kmain — saved to memory here, reloaded into rdi/rsi below.
 *
 * A1 near-miss (build.sh -DPLANT_NO_LONGMODE — a check that cannot fail is not a check): the
 * trampoline is NOT taken; the body stays in 32-bit protected mode and REPORTS its mode read from
 * the machine (EFER.LMA == 0), so the long-mode line is absent and A1's machine-read mode check reds.
 */

.set MB_ALIGN,    1 << 0                 /* align loaded modules on page boundaries        */
.set MB_MEMINFO,  1 << 1                 /* ask the loader for the memory map (the PMM reads it) */
.set MB_AOUT,     1 << 16                /* the a.out kludge: load by the ADDRESS fields below */
.set MB_FLAGS,    MB_ALIGN | MB_MEMINFO | MB_AOUT
.set MB_MAGIC,    0x1BADB002             /* the multiboot1 header magic                     */
.set MB_CHECKSUM, -(MB_MAGIC + MB_FLAGS) /* header magic + flags + checksum == 0            */

/* The multiboot header — must sit in the first 8 KiB of the image (the linker puts it first).
 *
 * WHY THE A.OUT KLUDGE (address fields): qemu's -kernel multiboot loader ELF-parses only 32-bit
 * ELFs ("Cannot load x86-64 image, give a 32bit one"). The a.out kludge tells the loader to load the
 * image by these physical ADDRESS fields instead of parsing the ELF — so a FLAT binary (objcopy -O
 * binary of the linked x86_64 body, build.sh) boots regardless of ELF class. The loader still enters
 * 32-bit protected mode with (magic, multiboot-info) in eax/ebx and the memory map present — only the
 * LOAD path changes, not the boot protocol. The header sits at the flat image's byte 0 (== load_addr
 * 0x100000), so header_addr == load_addr and the load offset is 0. */
.section .multiboot
.align 4
mb_header:
.long MB_MAGIC
.long MB_FLAGS
.long MB_CHECKSUM
.long mb_header                          /* header_addr:   the VMA of this header             */
.long _load_start                        /* load_addr:     start loading here (0x100000)      */
.long _load_end                          /* load_end_addr: end of the loaded (PROGBITS) data  */
.long _bss_end                           /* bss_end_addr:  end of .bss (the loader zeroes it)  */
.long _start                             /* entry_addr:    the 32-bit entry                    */

/* A 16 KiB boot stack, zeroed by the loader (.bss). */
.section .bss
.align 16
stack_bottom:
.skip 16384
stack_top:

/* The bring-up SCAFFOLD four-level page tables (identity-map the low 1 GiB with 2 MiB huge pages),
 * enough to get the body running the instant paging turns on. The body REPLACES these with its own
 * four-level tables in vmm_init (precision 2 — the mapping self-check runs on the body's tables,
 * never this scaffold). Zeroed by the loader; the trampoline fills the live entries. */
.align 4096
scaffold_pml4:
.skip 4096
scaffold_pdpt:
.skip 4096
scaffold_pd:
.skip 4096

/* the (magic, multiboot-info) the loader leaves in eax/ebx — SAVED before the trampoline clobbers
 * the registers, so 64-bit kmain still receives them (precision 3). Low addresses, identity-mapped. */
.align 8
saved_magic:
.skip 8
saved_mbinfo:
.skip 8

/* A temporary GDT with a 64-bit code segment — enough to far-jump into long mode. The body installs
 * its OWN GDT in gdt_install (idt.c). null / 64-bit code 0x08 (L=1) / data 0x10. */
.section .rodata
.align 16
gdt64:
    .quad 0x0000000000000000        /* null                                                 */
    .quad 0x00209A0000000000        /* 0x08: 64-bit code (P, DPL0, code exec/read, L=1)      */
    .quad 0x0000920000000000        /* 0x10: data (P, DPL0, data writable)                   */
gdt64_end:
gdt64_ptr:
    .word gdt64_end - gdt64 - 1
    .long gdt64                     /* 32-bit base — the GDT sits at a low (identity) address */

.section .text
.code32
.global _start
.type _start, @function
_start:
    cld
    movl $stack_top, %esp                /* set up the (32-bit) stack                        */

    /* PRECISION 3: preserve the loader's (magic, multiboot-info) across the mode switch. */
    movl %eax, saved_magic
    movl %ebx, saved_mbinfo

#ifdef PLANT_NO_LONGMODE
    /* A1 near-miss (the machine-read mode check can fail): do NOT take the trampoline. The body
     * stays in 32-bit protected mode; the failure path reads EFER.LMA (== 0) from the machine and
     * announces it — the long-mode line is never printed, so A1's mode check reds. */
    jmp mode_not_taken32
#endif

    /* ── build the scaffold identity map: PML4[0] -> PDPT[0] -> PD (512 * 2 MiB huge pages) ── */
    /* zero PML4 + PDPT (the two link tables; one live entry each). PD is fully written below. */
    movl $scaffold_pml4, %edi
    movl $2048, %ecx                     /* 2 pages / 4 bytes = 2048 dwords                  */
    xorl %eax, %eax
    rep stosl
    /* fill the PD: 512 huge pages, entry i = (i * 2 MiB) | PRESENT | RW | PS (0x83) */
    movl $scaffold_pd, %edi
    xorl %ecx, %ecx
1:
    movl %ecx, %eax
    shll $21, %eax                       /* i * 2 MiB                                        */
    orl  $0x83, %eax                     /* PRESENT | RW | PS (2 MiB page)                   */
    movl %eax, (%edi)                     /* the low dword                                    */
    movl $0, 4(%edi)                      /* the high dword (phys < 4 GiB)                    */
    addl $8, %edi
    incl %ecx
    cmpl $512, %ecx
    jl 1b
    /* link PML4[0] -> PDPT and PDPT[0] -> PD (PRESENT | RW = 0x03) */
    movl $scaffold_pdpt, %eax
    orl  $0x03, %eax
    movl %eax, scaffold_pml4
    movl $0, scaffold_pml4 + 4
    movl $scaffold_pd, %eax
    orl  $0x03, %eax
    movl %eax, scaffold_pdpt
    movl $0, scaffold_pdpt + 4

    /* CR3 = the scaffold PML4 */
    movl $scaffold_pml4, %eax
    movl %eax, %cr3

    /* CR4.PAE = 1 (bit 5) — four-level paging needs PAE */
    movl %cr4, %eax
    orl  $0x20, %eax
    movl %eax, %cr4

    /* EFER.LME = 1 (MSR 0xC0000080, bit 8) — enable long mode */
    movl $0xC0000080, %ecx
    rdmsr
    orl  $0x100, %eax
    wrmsr

    /* CR0.PG = 1 (bit 31) — turn paging on; long mode activates (EFER.LMA is set by the CPU) */
    movl %cr0, %eax
    orl  $0x80000000, %eax
    movl %eax, %cr0

    /* load the 64-bit GDT and far-jump into the 64-bit code segment (reloads CS -> 64-bit) */
    lgdt gdt64_ptr
    ljmp $0x08, $long_mode_entry

#ifdef PLANT_NO_LONGMODE
/* ── the 32-bit failure path (only in the planted build) ──────────────────────────────────────
 * Read EFER.LMA from the machine (it is 0 — long mode was never entered), init COM1, and announce
 * the machine-read mode. A silent absence would red A1 too, but a loud machine-read marker is the
 * honest "a check that cannot fail is not a check". */
mode_not_taken32:
    /* minimal COM1 init (mirrors serial_init) */
    movw $0x3F9, %dx                     /* COM1+1: disable interrupts                       */
    xorb %al, %al
    outb %al, %dx
    movw $0x3FB, %dx                     /* COM1+3: DLAB on                                  */
    movb $0x80, %al
    outb %al, %dx
    movw $0x3F8, %dx                     /* divisor low (0x0003 -> 38400 baud)               */
    movb $0x03, %al
    outb %al, %dx
    movw $0x3F9, %dx                     /* divisor high                                     */
    xorb %al, %al
    outb %al, %dx
    movw $0x3FB, %dx                     /* 8 bits, no parity, one stop bit                  */
    movb $0x03, %al
    outb %al, %dx
    movw $0x3FA, %dx                     /* enable + clear FIFO                              */
    movb $0xC7, %al
    outb %al, %dx
    movw $0x3FC, %dx                     /* RTS/DSR                                          */
    movb $0x0B, %al
    outb %al, %dx

    /* print the prefix, then the machine-read EFER.LMA digit, then a newline */
    movl $mode32_msg, %esi
2:
    movb (%esi), %bl
    testb %bl, %bl
    jz 3f
    call putc32
    incl %esi
    jmp 2b
3:
    /* read EFER.LMA (bit 10) — a machine fact; it is 0 here (long mode never activated) */
    movl $0xC0000080, %ecx
    rdmsr                                /* eax = EFER low; LMA is bit 10                    */
    shrl $10, %eax
    andl $1, %eax
    addb $0x30, %al                      /* '0' + LMA                                        */
    movb %al, %bl
    call putc32
    movb $0x0A, %bl                      /* '\n'                                             */
    call putc32
4:
    cli
    hlt
    jmp 4b

/* putc32: write the byte in %bl to COM1 (polled), preserving %esi/%ecx. */
putc32:
    pushl %eax
    pushl %edx
    movw $0x3FD, %dx                     /* line status                                      */
5:
    inb  %dx, %al
    testb $0x20, %al                     /* transmit-holding-register empty                  */
    jz 5b
    movw $0x3F8, %dx
    movb %bl, %al
    outb %al, %dx
    popl %edx
    popl %eax
    ret

.section .rodata
mode32_msg:
    .asciz "LONGMODE: NOT-TAKEN (still 32-bit, EFER.LMA="
.section .text
#endif /* PLANT_NO_LONGMODE */

.code64
long_mode_entry:
    /* reload the data segment registers with the flat data selector */
    movw $0x10, %ax
    movw %ax, %ds
    movw %ax, %es
    movw %ax, %fs
    movw %ax, %gs
    movw %ax, %ss
    /* the boot stack (same 16 KiB region; stack_top is 16-byte aligned) */
    movq $stack_top, %rsp
    /* PRECISION 3: hand kmain the preserved (magic, multiboot-info) in the ABI's arg registers
     * (magic -> edi zero-extends into rdi; the mbi pointer -> esi zero-extends into rsi, a low addr). */
    movl saved_magic, %edi
    movl saved_mbinfo, %esi
    call kmain
.hang:
    cli
    hlt
    jmp .hang
.size _start, . - _start

/* mark the stack non-executable — silences the linker's GNU-stack warning; a freestanding
 * body never needs an executable stack. */
.section .note.GNU-stack, "", @progbits
