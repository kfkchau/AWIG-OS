# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS kernel — the foundation (record + gate + views).

The spine every governed subsystem rides on. Ported from the estate's proving code
(pwc-app/src/core, src/domain) into the AWIG OS canonical envelope
(design/11-RECORD-SHAPES.md, names per design/20-CANONICAL-GLOSSARY.md).

One definitive (the record), one write path (the gate), all current state computed
(views). Nothing stored that can be derived; a crash loses only caches; recovery is
recompute.
"""
