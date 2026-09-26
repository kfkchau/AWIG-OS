# Third-party code

No bytes of anyone else's code are included in this repository. Everything under `code/` is this project's own, under the licences in [`LICENSING.md`](./LICENSING.md).

The full kernel build, the one that runs an interpreter and a network connection, takes two inputs from your own machine at build time. `code/src/body/build.sh` stages them and pins each by its fingerprint; the kernel checks the pins at boot and refuses to start on a mismatch.

| Input | What the build takes | From where | Licence |
|---|---|---|---|
| The Python interpreter | Your system's Python 3.12, which the build script expects at `/usr/bin/python3.12` with its library at `/usr/lib/python3.12` (another version or path needs the script edited), its loader, the C library pieces it needs and its standard library, staged into a sealed image | Your own machine | Python: PSF-2.0. The C library pieces are your system's own copies (LGPL); you stage them, we redistribute nothing |
| The network worker | lwIP 2.2.0 source, unmodified, with its own example and our configuration only | `apt-get source liblwip-dev` on your machine | BSD-3-Clause |

The plain kernel needs neither. It builds from this repository alone with `gcc`, `binutils` and Python 3, and boots in `qemu`.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project.
