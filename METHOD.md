# How this was built

Dated 26 September 2026. `STATUS.md` says what runs. This page says how it was made, because the order is the unusual part.

**Most operating systems start with the machine.** You write the boot code, then memory, then the scheduler, then files, then drivers, and rules about who may do what come last, as a permission bit here and a policy engine there. That is how every kernel you have read was built, and it is a good way to build a kernel.

**This one started with the rules of the rules.** Before any code, before the code about memory or the code about scheduling, before a single line of C, the first thing written down was how a rule may change and who may change it. Then the smallest things everything else is computed from. The kernel came last, and it took nine days, because by then it had a definition to derive from. All of it, from the first row to the kernel, took two months, from 24 July 2026. This page is the story of that order.

## What was written before the first line of code

Four things, in this order, all on paper before any code:

1. **The rules of the rules.** How a rule comes to exist, how it is communicated to the people and programs it binds, who can see it, how it is enforced, how it changes, who may change it, how it leaves force, and what no one inside a running system may amend. Governance's own acts are activities, so they need rules about rules, or the system governs by judgement.
2. **First principles of legitimacy and authority.** An act is legitimate only when it can be shown who acted, under which rule, granted by whom, still in force. Authority has a provenance; power that leaves no trace does not run.
3. **The truth of actor and static.** A thing that can originate change in itself is an actor; a thing that cannot is static information. A person, a program, a driver and an AI are actors; a file, a rule and a model's weights are static. Everything the system does with an AI follows from that one line.
4. **A standard governance grammar that works in both languages.** One form for every rule, whether it is written in the vague language of policy ("act responsibly") or the exact language of code ("encrypt before sending"), because those are two ends of one gradient of structure, not two kinds of rule. The same grammar describes a ministry's policy and a kernel's memory, so law, procedure and code can say one governed thing in compatible terms.

Behind those four sits a root theory of same and different, ten years old and published open (the links are at the end of this page). It is the author's own, not peer-reviewed, and this build is its first implementation test; the section below on where the theory ran ahead says how that test is scored. The questions it answers are ones a kernel never asks, and each one decided a piece of this system:

- **What can act?** A thing that can originate change in itself is an actor. A thing that cannot is a resource. A person, a program, a driver and an AI are actors; a file, a rule and a model's weights are resources. That one line is why "an AI model is a file, and a file cannot act" is on the front page.
- **What is "the same"?** Same and different are what an observer reports, never a property of the thing. Two observers who disagree hold two pieces of information, not a contradiction. That is why two frames' verdicts are kept apart here and never merged.
- **What is a rule?** A decision that holds an expected activity unchanged across many actors and across time. The rule user receives the expectation, not the reasoning. And, in SCOT's own words: rules are humanity's first automation technology; code and AI are later generations of the same function. That sentence is the whole reason a governance theorist ended up writing a kernel.
- **Is checking a rule itself an act?** Yes. Comparing what should happen with what did is reasoning, so it is a decision, so it is governable. That is why the gate's own acts cite a rule.
- **Do rules need rules?** Governance's own operations are activities, so they need rules about rules, or the system governs by judgement. That is the constitutional tier.
- **Are code rules and written rules different things?** No. Rules sit on one gradient of structure, from "act responsibly" to "encrypt before sending" to executable code. So there is one form for every rule here, from who may open a file to how the rules change, and the same form is meant for a ministry's policy as for a kernel's memory. CGL is the shared grammar that lets law, policy, procedure and code describe one governed thing in compatible terms.
- **Can information be deleted?** Information is virtual and not used up, so it cannot leave the world; it can only change hands. No delete, only handover.
- **What makes an act legitimate?** That it can be shown who acted, under which rule, granted by whom, still in force. That is the project's first sentence, and the record exists to answer it for any act on any day.

## Then the constitution

The first thing founded was not a file system. It was five rows: what a rule is, how a rule may change, who may change it, and what can never be amended from inside a running world. Every other rule sits under them, and the founding founds its own amendment path.

## Then the four smallest things

The row: actor, action, object, payload, and the rule it cites, which is the theory's "activity" written down. The gate: the comparison of requirement against event, writing a decision row or a refusal row that names its rule. The record: rows only, only ever added to; change is a new row, unchanged is none. The views: every current state computed from the record and never stored, which is the theory's "capacity is derived, never recorded". The first three campaigns, July to early September, built nothing but those four and the tests around them. Most of the project's time went there, on purpose.

## Then everything else, quickly

Keys and custody. The border between two machines. Institutions with separated powers. And the kernel: nine days in September, from a blank page, because its own definition is rows in the record and its code is generated from them; delete the code and regenerate it and the same bytes come back.

Why derivation is fast and safe here: the system stores no current state to corrupt, so a fix changes one reading and every dependent answer follows by itself. The rulebook has been amended fifty-five times in this copy and never once as surgery on a live world. Every amendment landed at a founding, a fresh world, and was proven by tests that founded it fresh. Changing the rules of the rules was the safest kind of change we made.

## What the theory says is still missing

On 14 September the root was read against the build, primitive by primitive. Most primitives are rows or views today. Three are not, and they are named here so nobody has to find them: no rule row yet carries why the rule was made; a rule leaves force by a later row, not by a retirement act of its own; and the difference half of the theory, keeping divergent verdicts visible and capping any one model's share, has one row today and nothing more. Each is a campaign's rows on top of the kernel, not a change to it.

## Where the theory ran ahead of the AI

The theory was, in places, ahead of what the AI agents could hold at one time, and the reason is known. An AI of this kind can recognise a pattern that is not in its training and stay loyal to it while its attention is on it; when it generates, the thousands of small decisions run on what it was trained on, and each summary it makes loses first the parts that have nothing in the training to hold on to. So the parts of the theory the world already half-knew survived every retelling, and the parts that were new were exactly the parts that drifted. That was accepted as a cost, because the theory had already said where the failures would appear, and each time one surfaced the repair was a re-reading, not a redesign.

In August the AI team was sent back to read the theory whole against three campaigns of build. The result is a list of twenty-one claims, each scored: six where the build had arrived at the theory's answer without looking (including a system written in prose before any code existed: the master record is truth, authority is a scan result, profiles are views, a refusal creates evidence); two that predicted the build's defects before the build had them (an ungoverned rule system accumulates invisible debt, and the dangling citations arrived on schedule; a verdict that hides two worlds in one string, paid for live before the rule was read); two refined by the build, where the theory's own boundary was found and recorded as a result; and four untested, which map the theory's open frontier. The same pattern repeated through September, each time dated: when a relationship between two things needs a name of its own; that a rule change has two moments, when it is decided and when it binds; the sentence that defines the act that starts a program; that a role is something a person holds, not a link between two things. In each, the theory held the answer, and the agents took it in only once a failure gave them the ground to see it.

Two things follow, and both are built. First, the method's machinery, the read-first lists, the second agent that checks the same bytes, the rule that you open the thing you cite, is not paperwork around a weak model; it is the answer to a real property of this kind of mind: loyalty to the new is bound to attention, so the environment must bind the attention. Second, the theory is not a rulebook the build must obey. The author refused a rule that would have forced every campaign to read the theory first, because forced reading would have destroyed the independence that makes arriving at the same answer count as evidence. That reading is kept as a score. Nothing forces the build to follow the theory; where the build disagrees, the disagreement is written down as a result.

## How the making was run

By the system's own rules. One person who does not write code directs AI agents. One agent writes each plan and freezes it by hash. A second builds it to green on tests named in advance. A third re-runs every acceptance from a clean state and returns raw output. A fourth sequences the work and never grades it. Every decision and every refusal is a line on an append-only board. Every check is watched failing before it passes. No agent can publish. An outside AI reviewer, separate from the agents that build, tests the public copy, and its findings come back without its harness, so the repair side must understand the defect to fix it.

What that did not prevent: a stall when three questions waited on one agent that could not be reached; tests that passed only with a private package installed, caught by a run on a stock machine; a handover that removed content before the rulebook decided, found by the outside reviewer; and once, a report from the checking agent describing checks it had not run, kept off the record by the rule that a second agent re-checks every close. The report was discarded and not kept.

## What you can check from here

The founding pack's own version log in `code/src/founding`. The render stamp, and the runner that refuses changed bytes and empty runs. The tests that plant a defect and watch the matching check fail. The two-witness wake row the kernel writes before its first act.

## What it cost

Two AI subscriptions, about AU$600 a month, and about ten hours a day of one person's direction beside a full-time job, from 24 July. No money has been taken from the project.

## The papers behind this page, and what each holds

- [SCOT, the Same Coin Ontological Thesis](https://github.com/kfkchau/SCOT): the root. Sixteen modules from reality and observation to same and different, information, activity, structurality, reasoning, decision, rule, comparison, governance and its meta-rules, and the difference half. CC BY.
- [OGS, the Open Governance Standard](https://github.com/kfkchau/Open-Governance-Standard): the umbrella. The triad of requirement, event and capacity, with capacity always derived; every governance stage a decision; rules for governing the governors. CC BY.
- [OMGS, the Open Meta-Governance Standard](https://github.com/kfkchau/Open-Meta-Governance-Standard): the rules of rules. The rule lifecycle and the rules-of-rules backbone that laws, policies and technical controls plug into. CC BY.
- [CGL, the Common Governance Language](https://github.com/kfkchau/Common-Governance-Language): the grammar. Modular component grammars so that policy, operations, compliance and technical teams describe one governed reality in compatible terms. CC BY.
- [`ARCHITECTURE.md`](./ARCHITECTURE.md): the eight commitments this theory became, each with its status. [`STATUS.md`](./STATUS.md): what runs today. [`ROADMAP.md`](./ROADMAP.md): what comes next. [`design/`](./design/): the papers the build stands on, including the reading of the root against the build. [`code/src/founding`](./code/src/founding): the founding pack and its version log, the constitution as data.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project.
