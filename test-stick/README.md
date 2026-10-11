# Test stick 1: the image written to the stick that booted one laptop on 3 October 2026

**Read this before you boot it.**

This is a test image of a pre-alpha kernel. On the one laptop it has booted, it booted from a USB stick, printed its own checks, and halted. It has no install step. It is not an operating system you can use.

Two images: the plain kernel for a virtual machine, on the v0.7.0 release; the test stick for a real machine you can afford to lose. This page is about the stick. The plain kernel is section 8.

**Boot it only on a machine you can afford to lose.** This image may write to a disk it finds. It has not been tested against any disk but its own. The stick also carries a Linux kernel and some drivers for a later probe; they are not booted. Do not boot this on a machine whose disk holds anything you cannot lose.

It has booted one laptop, the one boot on record, on 3 October 2026, at the author's hands. The image was built with no knowledge of that laptop. Nothing was installed on the laptop; one firmware setting, Secure Boot, was turned off after the firmware refused the stick; whether its disks were touched is not shown, which is what the caveat is for. Whether it boots yours is the question this image exists to answer. Pass or fail, please file it: [open a boot report](../../../issues/new?template=boot-report.md).

Secure Boot has to be off; the image is unsigned. With Secure Boot on, the HP laptop's firmware refused it ("Selected boot image did not authenticate"); expect the same elsewhere. UEFI with Secure Boot off is the one path that has booted. The image also carries a BIOS boot partition, so an older machine may boot it, but that has not been tried on real hardware. The smallest memory it needs has not been measured; builds of the same sources have run in a 2 GiB virtual machine, and this image has run on one real laptop, its memory not recorded.

On every filed boot, the laptop's and the lab's, the halt screen carries two FAIL lines: `FLOOR3L: FAIL (the module run did not complete on the body)` and `FLOOR3C-ACTS: FAIL`. A third, `FLOOR3C-BESIDE: FAIL`, appears earlier in the scroll. The first line's own words are misleading: the module did run and finish (the same screen says `Ran 1 test ... OK`). FLOOR3C-BESIDE is the record-filesystem reading itself, which cannot pass while the image finds no disk of its own kind to keep records on, and it is the part that turns the other two red. If an old-style disk is present, one more line is expected, `DISK: FS-FAIL (no BODYFS on the block device)` (from the source; no filed boot has shown it). Any other line containing FAIL, besides these three and that one, is a real result; please file it with a photo.

The image's SHA-256 is in [`SHA256SUMS`](./SHA256SUMS) beside this page. The source that builds this exact image is not in this tree yet: it ships with the campaign 9 release, and the author provides it on request now. What this tree builds today is the plain kernel. [`BUILD.md`](./BUILD.md) says what the image was built from; one input, the record segment, is in this folder. The installer, and the repairs [`STATUS.md`](../STATUS.md) lists, ship later; the rest of the project is already in this tree, as STATUS.md describes it.

## 1. Get the file and check it

This folder carries `awig-os-test-stick-1-DISPOSABLE-MACHINE-ONLY.img.xz` (about 30 MiB, 31.6 MB). Unpack it; the image inside is 103,809,024 bytes. Check the image, not only the archive:

    sha256sum awig-os-test-stick-1-DISPOSABLE-MACHINE-ONLY.img
    1f16d486b42787f9fb57fae847129fb030f0765496e4d36469ebbbd2ed923a95

On Windows, `certutil -hashfile <file> SHA256`; on macOS, `shasum -a 256 <file>`. If the number differs, stop and do not write it.

## 2. Write it to a stick

The stick is erased. 1 GB or larger.

- Windows: Rufus, choose the image, and when asked, write in **DD image** mode, not ISO mode. Or balenaEtcher. (Untested by us; the filmed stick was written by our own Linux tool.)
- macOS and Linux: find the stick's device name first (`diskutil list` or `lsblk`), then, with the stick's name in place of `sdX`:

      sudo dd if=awig-os-test-stick-1-DISPOSABLE-MACHINE-ONLY.img of=/dev/sdX bs=4M status=progress conv=fsync

  A wrong device name writes over that disk instead. Check it twice. To confirm the write, read it back and compare with the hash above:

      sudo head -c 103809024 /dev/sdX | sha256sum

## 3. Turn Secure Boot off

In the firmware settings (on the HP that booted, the firmware's startup menu at power-on; on others, Esc, F2, F12 or Del). Find Secure Boot and set it off. You can turn it back on afterwards.

## 4. Boot from the stick

Plug the stick in, power on, and open the firmware's boot menu (on the HP, its boot-menu key; on others, F12, F8 or Esc). Choose the USB stick. After you pick the stick there is no menu of ours (the image's own boot configuration has none); the screen goes to the kernel's own lines, then the checks. (What the first seconds look like on your screen is not filed.)

## 5. What you will see

A dark screen with yellow text: the checks scrolling past (`FLOOR3C-BESIDE: FAIL` among them), the two FAIL lines named above, and `BODY-HALT` as the last line. Then nothing moves: it has halted. The screen holds what it printed until you power off. Hold the power button, remove the stick, and turn Secure Boot back on if you want it.

If the screen stays black, or stops before `BODY-HALT`, give it one minute. Nothing by then means it probably did not fit this machine. Power off and file that as a fail, with a photo of whatever was last on the screen.

## 6. File the result

[Open a boot report](../../../issues/new?template=boot-report.md). It asks for: the image hash you checked; the machine's make and model; UEFI or legacy; Secure Boot off or could not be turned off; the result (reached `BODY-HALT`, stopped earlier, or black screen); the last line on the screen; a photo of the screen. A photo shows only the screen; nothing else about you is wanted. Photos can carry your phone's location in their metadata; switch location tagging off or strip it first.

## 7. What happens to it

Each report becomes one row in `STATUS.md`'s list of machines, dated, with the result as "reached BODY-HALT" or what the screen showed last, and your handle if you want it there. The list on STATUS.md is where each filed report is entered.

## 8. The plain kernel, for a virtual machine

The kernel alone, with no stick, no sealed interpreter, no carried record and no Linux cargo, is the file on the [v0.7.0 release](../../../releases/tag/v0.7.0) (65,588 bytes, SHA-256 `00e11b1c…`, 20 September 2026), the default build of the kernel sources; [`code/README.md`](../code/README.md) says how to build and boot it. The command:

    qemu-system-x86_64 -display none -no-reboot -serial stdio -kernel <that file>

On every filed boot of that build, no line reads FAIL. Three lines say ABSENT and are normal, `DISK: ABSENT`, `NET: ABSENT` and `NET-ACTS`; its checks print PASS, and the last line is `BODY-HALT`. Any line containing FAIL, or no output at all, is a real result: please file it with the command you ran and what printed. It prints the same rows header as the stick, `ROWS-DIGEST sha256:b16ee8a33d50424c8e4ed10474a3f2fed49f6693aa7b1b0492256d9ef842cfdb` and `ROWS-COUNT 0000000c`, which is a constant of the build. The `body.img` inside the stick image (hash `46a88407…` in the image's manifest) is a different build of the same sources, with the ledger flags; no boot of that file on its own is filed yet, so nothing is claimed for it here. The plain kernel is the image to try if you do not have a machine you can afford to lose.
