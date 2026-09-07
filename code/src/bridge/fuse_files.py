# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""SUPERSEDED at EP-25. The live custody server is `bridge/records_fs.py`.

This file held the D9 stepping stone: a `RecordsFS` over a FLAT top-level namespace, enough
to prove that real programs could read and write a records-backed mount, and explicitly not
more ("nested directories are a later completeness item, not part of the stance-3 proof").

EP-25 is that later round. `bridge/records_fs.py` serves full tree custody — nested
directories, hard links with counted link counts, symlinks, rename, extended attributes,
record-before-effect ordering, the recorded coalescing policy, port identity in provenance,
and continuous shadow-diff with a divergence halt. Nothing imports this module.

It is left as a POINTER rather than deleted, which is the estate's own documentation law
applied to code: remove-from-view, never erasure, with something at the old name for whoever
follows a citation here. The campaign-1 findings item that homed the stepping stone to "the
round that takes up the bridge" is closed by that round, on the record.

The behaviour it proved is not lost — it is a subset of what `tests/test_ep25.py` asserts,
and the two ops it drove (FILE-CREATE, FILE-WRITE) are the same founding definitions the new
server drives, amended at EP-25 to carry an inode and the coalescing fields.
"""
