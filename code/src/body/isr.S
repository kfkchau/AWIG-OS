/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the descriptor-table loaders and the interrupt stubs (C7 P3b-3; RE-BASED to x86_64
 * long mode, C7 P3b-4L).
 *
 * The asm half of the interrupt path, now 64-bit: load the GDT (with a far-RETURN CS reload, since a
 * 64-bit far jump cannot take an immediate selector:offset) and the IDT, and one stub per vector
 * 0..47 that normalises the CPU's two entry shapes (with / without an error code) into ONE 64-bit
 * stack frame, then hands a pointer to that frame to the C dispatcher (idt.c: isr_dispatch) and
 * returns with iretq. Vectors 0..31 are the CPU exceptions; 32..47 are the PIC's IRQs after the remap
 * (so IRQ0, the timer, is vector 32). Read whole: this is the entire low-level entry surface. Every
 * instruction runs in the guest's nested qemu; nothing here targets the host kernel (L11).
 *
 * The System V AMD64 convention: gdt_flush/idt_flush take their pointer in %rdi; isr_dispatch takes
 * the frame pointer in %rdi. In long mode the CPU always pushes SS:RSP on an interrupt (even ring0 ->
 * ring0) and aligns the frame to 16 bytes, so the frame ends at ss and the stub build below reaches
 * isr_dispatch 16-byte aligned.
 */
.code64

/* ── gdt_flush(%rdi = &gdt_ptr): lgdt, reload the data segments, far-RETURN to reload CS ─────────*/
.global gdt_flush
.type gdt_flush, @function
gdt_flush:
    lgdt (%rdi)
    movw $0x10, %ax          /* the flat data selector */
    movw %ax, %ds
    movw %ax, %es
    movw %ax, %fs
    movw %ax, %gs
    movw %ax, %ss
    leaq .gdt_reloaded(%rip), %rax   /* far-return target */
    pushq $0x08              /* the flat 64-bit code selector — reloads CS */
    pushq %rax
    lretq
.gdt_reloaded:
    ret
.size gdt_flush, . - gdt_flush

/* ── idt_flush(%rdi = &idt_ptr): lidt ──────────────────────────────────────────────────────────*/
.global idt_flush
.type idt_flush, @function
idt_flush:
    lidt (%rdi)
    ret
.size idt_flush, . - idt_flush

/* ── the common trampoline: build the isr_frame, call the C dispatcher, restore, iretq ─────────*/
isr_common:
    pushq %rax               /* the general registers, high-address-first (rax at the top)       */
    pushq %rbx
    pushq %rcx
    pushq %rdx
    pushq %rsi
    pushq %rdi
    pushq %rbp
    pushq %r8
    pushq %r9
    pushq %r10
    pushq %r11
    pushq %r12
    pushq %r13
    pushq %r14
    pushq %r15               /* r15 ends at the lowest address — matches struct isr_frame         */
    movq %rsp, %rdi          /* arg: a pointer to the isr_frame (the current stack top)           */
    call isr_dispatch
    popq %r15
    popq %r14
    popq %r13
    popq %r12
    popq %r11
    popq %r10
    popq %r9
    popq %r8
    popq %rbp
    popq %rdi
    popq %rsi
    popq %rdx
    popq %rcx
    popq %rbx
    popq %rax
    addq $16, %rsp           /* drop the pushed int_no and err_code */
    iretq                    /* restores rip, cs, rflags, rsp, ss (and re-enables interrupts) */

/* Stubs. ISR_NOERR pushes a dummy error code so every frame has the same shape; ISR_ERR relies on the
 * CPU's own error code. IRQ pushes a dummy error code and the remapped vector number. */
.macro ISR_NOERR num
.global isr\num
isr\num:
    cli
    pushq $0
    pushq $\num
    jmp isr_common
.endm

.macro ISR_ERR num
.global isr\num
isr\num:
    cli
    pushq $\num
    jmp isr_common
.endm

.macro IRQ num, vec
.global irq\num
irq\num:
    cli
    pushq $0
    pushq $\vec
    jmp isr_common
.endm

    /* CPU exceptions 0..31. 8,10,11,12,13,14,17 deliver an error code; the rest do not. */
    ISR_NOERR 0
    ISR_NOERR 1
    ISR_NOERR 2
    ISR_NOERR 3
    ISR_NOERR 4
    ISR_NOERR 5
    ISR_NOERR 6
    ISR_NOERR 7
    ISR_ERR   8
    ISR_NOERR 9
    ISR_ERR   10
    ISR_ERR   11
    ISR_ERR   12
    ISR_ERR   13
    ISR_ERR   14
    ISR_NOERR 15
    ISR_NOERR 16
    ISR_ERR   17
    ISR_NOERR 18
    ISR_NOERR 19
    ISR_NOERR 20
    ISR_NOERR 21
    ISR_NOERR 22
    ISR_NOERR 23
    ISR_NOERR 24
    ISR_NOERR 25
    ISR_NOERR 26
    ISR_NOERR 27
    ISR_NOERR 28
    ISR_NOERR 29
    ISR_NOERR 30
    ISR_NOERR 31

    /* PIC IRQs 0..15 -> vectors 32..47 (the timer is IRQ0 -> vector 32). */
    IRQ 0, 32
    IRQ 1, 33
    IRQ 2, 34
    IRQ 3, 35
    IRQ 4, 36
    IRQ 5, 37
    IRQ 6, 38
    IRQ 7, 39
    IRQ 8, 40
    IRQ 9, 41
    IRQ 10, 42
    IRQ 11, 43
    IRQ 12, 44
    IRQ 13, 45
    IRQ 14, 46
    IRQ 15, 47

/* The table of stub addresses, indexed by vector 0..47, so idt.c installs the gates in one loop.
 * 64-bit addresses (.quad) — long-mode handler offsets are 64-bit. */
.section .rodata
.align 8
.global isr_stub_table
isr_stub_table:
    .quad isr0,  isr1,  isr2,  isr3,  isr4,  isr5,  isr6,  isr7
    .quad isr8,  isr9,  isr10, isr11, isr12, isr13, isr14, isr15
    .quad isr16, isr17, isr18, isr19, isr20, isr21, isr22, isr23
    .quad isr24, isr25, isr26, isr27, isr28, isr29, isr30, isr31
    .quad irq0,  irq1,  irq2,  irq3,  irq4,  irq5,  irq6,  irq7
    .quad irq8,  irq9,  irq10, irq11, irq12, irq13, irq14, irq15

/* mark the stack non-executable (matches boot.S) — a freestanding body never needs an exec stack. */
.section .note.GNU-stack, "", @progbits
