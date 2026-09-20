# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
# AWIG OS provenance · FRAME: systems-architecture · CORPUS-CLASS: engine-source · OS-architecture
# vocabulary (a POSIX/libc personality above a small kernel, an enclosed borrowed worker, a sealed
# hash-checked interpreter, the host seam's act set) as in the seL4/gVisor/Fuchsia literature.
# NON-GOAL: no offensive capability — this package SUPPLIES what CPython needs to run above our own
# kernel, by function; it attacks nothing. Full declaration: SCOPE-STATEMENT.md.
"""AWIG OS hosting — the interpreter-hosting layer (C7 P7a).

The layer beneath CPython and above our own kernel that supplies what CPython needs to run — files,
threads, memory, the clock, entropy, the one connection and a libc surface — wiring each need DOWN
to the host seam's act set. See `interpreter_host.py`.
"""
