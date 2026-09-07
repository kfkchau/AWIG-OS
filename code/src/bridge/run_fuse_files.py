# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""Mount the records-backed files custody as a real FUSE filesystem.

Usage: python3 run_fuse_files.py <record.jsonl> <blobdir> <mountpoint>

REBUILT AT EP-25 (the campaign-1 findings item closes here, design/36 §7 item 5). This
file was the D9 flat-namespace stepping stone and carried its own compose: a bare
`build_kernel`, the campaign-1 `FilesView`, and `RecordsFS` over a flat top-level
namespace. It has been the estate's named stale runner ever since, homed to "the round
that takes up the bridge", and this is that round.

It is REBUILT rather than retired, because what it did is what the crux needs — only over
full tree custody rather than a flat one. What is gone is its second compose: a runner
that builds its own kernel is a second way to raise a mount, and two ways drift. This file
is now a thin delegation to `bridge.mount`, kept at its documented path so anything that
learned this name still works.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridge.mount import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
