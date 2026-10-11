# How test stick 1 was built

The image in this folder was assembled on 3 October 2026 from the project's private tree at commit `85d953f9` (07:52 that day). That tree is not in this repository yet: it ships with the campaign 9 release, and until then the author provides it on request (see SECURITY.md for the address). This page says what the build read, what it needed that is in no tree, and what a rebuild gives, so that the published image can be checked against the published hashes.

## What the build reads

Three whole folders of that commit: `src`, `tests` and `tools/probe` (503 files). All of `src` is needed, not only the kernel's folder, and `tests` is not optional: the run the stick performs lives in a test module. The build script is `src/body/build.sh`; the stick assembly is under `tools/probe/`.

## One input that is not in the tree

The build takes a pinned record segment by `--segment`: a 385,226-byte cut of the record, SHA-256 beginning `5163f63e`. It is in this folder as its own file beside the image. It is already inside the image; the standalone file adds nothing a stranger does not already hold, and without it a rebuild reproduces the kernel but not this exact image.

## What else is in the image, and where its source is

The image carries other people's software, read from the image's own bytes:

- GRUB 2.12-1ubuntu7.3, the boot loader. Source: Ubuntu's `grub2` source package for that version.
- Ubuntu's Linux kernel `vmlinuz-6.8.0-134-generic` with twelve of its driver modules (ahci, libahci, nvme, nvme-core, xhci-pci, usb-storage, uas, usbhid, hid, hid-generic, e1000, vga16fb, each as .ko.zst), as the image's own `cargo/MANIFEST` lists them; the manifest's first line is the hash of the boot configuration, so it is the image's own inventory. The image's `boot/grub/grub.cfg`, read from the boot partition, has no menu and no entry that boots this kernel: carried, not booted. Source: Ubuntu's `linux` source package for 6.8.0-134.

- Inside `sealed.img`, the standard Python 3.12 interpreter and its library, with the loader and C library pieces it needs (PSF licence; LGPL for the C library pieces), as `THIRD-PARTY.md` lists them for the full kernel build.

None of it is this project's code. `THIRD-PARTY.md` lists all of it.

## The build environment

Ubuntu with kernel 6.8.0-134, and these tool versions: gcc 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1), GNU ld 2.42, Python 3.12.3, sgdisk 1.0.10, mkfs.fat 4.2, grub-mkimage 2.12-1ubuntu7.3, xz 5.4.5, zstd 1.5.5, blkid 2.39.3; also `losetup`, `grub-bios-setup` and `partprobe`, which the build script checks for.

## What a rebuild gives

This source builds the kernel deterministically: two builds from this code on one machine are byte-identical to each other. The shipped bytes were built on 3 October 2026 with the tool versions listed; a rebuild under other versions will not match byte for byte, and the one run on 11 October did not. Verify the shipped files against the hashes, not against your own rebuild.

## The plain kernel

The plain kernel for a virtual machine is the file on the v0.7.0 release (65,588 bytes, 20 September 2026), the default build of the kernel sources, with filed boots. The `body.img` inside this stick image is a different build, with the ledger flags; the image's own `cargo/MANIFEST` states its hash, `46a884077c6452da7c853a1a281d0ec92597d634434b91f04f6b18233d2f89f2` (`core.img` shows the same hash; the build makes it a byte-copy by design). No boot of that file on its own is filed, so the test-stick page claims nothing for it. If you want to boot it anyway, copy it out of the image's boot partition and run `qemu-system-x86_64 -display none -no-reboot -serial stdio -kernel body.img`.

## The steps

The stick: `src/body/build.sh` with the ledger flags, then `tools/probe/mkprobe.sh --segment record-segment-385226.bin` (the exact invocation is the script's own usage text), in the tree named above. The plain kernel: extract `body.img` from the image's boot partition.
