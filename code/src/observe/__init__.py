# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS observe — the watch-and-record adapters (bridge stance 1->2, M1).

Each adapter observes a real Linux resource through a window Linux already opens to
user space and records it through the gate (one write path). Linux stays
authoritative; AWIG OS only records and derives. This is the audit product that ships
before any subsystem takes authority (design/11-STAGE-1-WATCH-AND-RECORD.md).
"""
