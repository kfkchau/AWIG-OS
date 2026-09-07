# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Kelvin Chau and AWIG OS contributors
#
# This file is part of AWIG OS.
# AWIG OS is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version. See the LICENSE file for details.
"""AWIG OS devices subsystem — the governed CAPABILITY core (design 03 §4.4).

Capability is law: registering a driver's capability is a recorded amendment (not a
config edit); binding a device is a decision that must cite an existing capability, or
it refuses. The binding table and capability ledger are derived views. This is the
governance core, NOT the drivers themselves — the thousands of real drivers are the
out-of-scope breadth (DECISIONS D8). What is governed here is who may touch which
hardware, when, under whose authority: the exact gap the conventional kernel leaves
(capability without law).
"""

# The devices op definitions (REGISTER-CAPABILITY / BIND-DEVICE / UNBIND) and their law-name
# constants were RETIRED here in EP-14B: their one authoritative home is the founding pack,
# founding/founding-pack.json. The generic interpreter re-registers them from the record at boot;
# this module keeps only its derived view. Absence is guarded by
# tests/test_ep14b.py::test_no_module_op_definition_dicts_outside_the_founding.


class DevicesView:
    def __init__(self, store):
        self.store = store

    def bindings(self, as_of=None):
        b = {}
        # K12 FAMILY SOURCE (MAINT-K12-SUBSYSTEM-VIEWS; design/36 ADDENDUM S). The binding table
        # depends only on BIND-DEVICE / UNBIND records, so read that family through the existing
        # config-keyed projection (store.action_set_projection) rather than the whole record.
        # Only the iteration SOURCE moves; the fold body is byte-identical.
        for e in self.store.action_set_projection(
                {"BIND-DEVICE", "UNBIND"}).all(as_of):
            a, p = e["action"], (e.get("payload") or {})
            if a == "BIND-DEVICE":
                b[p["device"]] = p["driver"]
            elif a == "UNBIND":
                b.pop(p["device"], None)
        return b

    def capabilities(self, as_of=None):
        return {(e["payload"])["driver"]: e["payload"]
                for e in self.store.by_action("REGISTER-CAPABILITY", as_of)}
