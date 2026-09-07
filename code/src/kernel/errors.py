# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""Every refusal cites its governing rule.

Ported from pwc-app/src/core/errors.js. A refusal is never a bare failure: it names
the LAW record it refused under (design 02 §1.2; audit guarantee "Explanation").
"""


class OpError(Exception):
    """A rule-cited refusal. `rule` is the LAW id (or root-rule id) that refused."""

    def __init__(self, rule, message):
        super().__init__(f"[{rule}] {message}")
        self.rule = rule
        self.message = message
