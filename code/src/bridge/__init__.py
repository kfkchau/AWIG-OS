# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS bridge — the depth stances that take a governed core from record-logic to a
real resource (design/16-BRIDGE). Stance 3 (M2) serves a core as a live resource in user
space (FUSE); stance 4 (M3) moves it below the syscall line. These adapters may use
non-core dependencies (e.g. fusepy/libfuse); the zero-dependency rule binds the core, not
the bridge adapters.
"""
