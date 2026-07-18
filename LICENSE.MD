# Licensing of AWIG OS

This document explains, in plain language, how this project is licensed and why. It is the licensing map for the whole repository. The legally binding texts are the license files it points to; where this explanation and a license text differ, the license text governs.

The license is this project's first rule: written down, legible to everyone, binding on everyone, and heaviest on the strongest. A project about accountable power should be governed by an instrument that holds power accountable, starting with whoever forks it.

---

## 1. The structure at a glance

| Layer | What it covers | License | In one sentence |
|---|---|---|---|
| **Core** | The operating system itself: kernel work, rule engine, permission and trace machinery, AI-organisation machinery. Everything under `/core`, and any directory not otherwise marked. | **GNU GPLv3** | Use it freely for anything; if you distribute a modified version, your modifications must be published under this same license. It stays open, in every hand, forever. |
| **Ring** | SDKs, client libraries, rule-format tooling, examples. Everything under `/sdk`, `/tools`, `/examples`. | **Apache License 2.0** | Do anything, including building closed commercial products on top. Keep the notices. Contributors grant patent rights. |
| **Text** | Documentation, specification text, this file, the README. | **CC BY 4.0** | Share and adapt freely for any purpose, with attribution. |

**Using AWIG OS does not make your software GPL.** Running programs on AWIG OS, calling its interfaces, writing rules in its rule format, or building applications and services on top of it does not extend GPLv3 to your code. The copyleft obligation applies only to modified versions of the Core itself that you distribute. This is the same boundary promise that lets the whole software industry run on Linux.

## 2. What each license means in practice

### 2.1 Core: GNU General Public License v3 (GPLv3)

Plain meaning:

- **You may** use it for anything, including commercially; study it, modify it, redistribute it, and charge for distribution and services.
- **You must**, if you distribute a modified version, release your modifications under GPLv3, with source code, keeping notices intact.
- **You may not** take the Core private. No one, individual or giant, can ship a closed, modified AWIG OS. The anti-lockdown terms also mean it cannot be sealed inside hardware its users are forbidden to modify. A system whose promise is inspectable governance cannot be sold in a sealed box.
- **Patents**: every contributor grants the patents needed for their contribution; suing users over those patents forfeits your license.

Why GPLv3 for the Core: the product of AWIG OS is not capability. It is a guarantee: one rule format, traceable permission, glass-box AI. A closed fork would carry the brand of accountability with the accountability removable. GPLv3 is the tamper-seal that makes the guarantee travel with the code.

Canonical text: the file [`LICENSE`](./LICENSE) in this repository must contain the **verbatim** GPLv3 text from <https://www.gnu.org/licenses/gpl-3.0.txt>. Do not retype or reformat it. Copy it exactly.

### 2.2 Ring: Apache License 2.0

Plain meaning: take it, use it, modify it, embed it in closed commercial products. Keep the copyright and attribution notices, and the NOTICE file if present. Contributors grant patent rights; patent aggression against users forfeits the license.

Why Apache for the Ring: everything that helps others build on AWIG OS should travel with as little friction as possible. The Ring is how the mission spreads. The Core is how it stays honest.

Canonical text: the file [`LICENSE-APACHE`](./LICENSE-APACHE) must contain the verbatim Apache 2.0 text from <https://www.apache.org/licenses/LICENSE-2.0.txt>.

### 2.3 Text: Creative Commons Attribution 4.0 International (CC BY 4.0)

Plain meaning: copy, redistribute, remix, transform, and build upon all documentation and specification text in this repository, for any purpose, even commercially, provided you give appropriate credit.

Why CC BY for text: the ideas, the philosophy, the governance model, the specification, should travel at full speed with mandatory attribution. The theory infrastructure this project implements is published under the [Open Governance Framework](https://github.com/kfkchau/open-governance-framework) umbrella, including the [Open Meta-Governance Standard](https://github.com/kfkchau/Open-Meta-Governance-Standard/), already under CC BY 4.0. This repository's text follows the same rule and the same attribution.

Canonical text: [`LICENSE-DOCS`](./LICENSE-DOCS), from <https://creativecommons.org/licenses/by/4.0/legalcode.txt>.

## 3. Contributions: Developer Certificate of Origin (DCO)

All contributions carry a **DCO sign-off**: add `Signed-off-by: Your Name <email>` to each commit (`git commit -s`), certifying you have the right to submit the work under this project's licenses (per <https://developercertificate.org/>).

Two consequences, stated openly:

1. **You keep your copyright.** Contributors are not asked to assign copyright. Your work remains yours, licensed to the project under the layer's license.
2. **The project keeps steering room.** The original author remains the copyright holder of the project's own code and may, if capture of the commons through loopholes ever emerges (for example, cloud-stripping of the Core), adopt stronger copyleft terms for **future versions**. Already-released code remains under its released license forever. This possibility is recorded here so that no one is ever surprised by it.

## 4. Per-file headers

Every source file in the Core begins with:

```
SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2026 Kelvin Chau and AWIG OS contributors

This file is part of AWIG OS.
AWIG OS is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option)
any later version. See the LICENSE file for details.
```

Ring files use `SPDX-License-Identifier: Apache-2.0`. Documentation files carry the CC BY 4.0 footer.

## 5. What this licensing does not do

- It does **not** grant or imply any trademark rights. There are none. See the Naming Commitments in the [README](./README.md).
- It does **not** restrict anyone's traditional, cultural, or community use of the words *awig*, *awig-awig*, or *subak*. Those words belong to their communities, not to this project.
- It does **not** make software that merely runs on, targets, or interoperates with AWIG OS subject to the GPL.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project, delivered under the [Open Governance Framework](https://github.com/kfkchau/open-governance-framework).
For attribution, citation, or inquiries: [https://au.linkedin.com/in/kfkchau](https://au.linkedin.com/in/kfkchau)
