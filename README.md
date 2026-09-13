# AWIG OS

*An operating system that follows a thousand-year-old way of governing.*

---

## 1. Start with the water

Rain falls on a volcano in Bali. It runs down through black rock and forest, and by the time it reaches the rice terraces it has become the most political substance on the island. Everyone's field needs it. No one's field may take it all.

For about a thousand years, the farming communities of Bali have governed that water together. They are called **subak**. Their meeting places are water temples. Their method is deliberation. Their protocol is ritual. In 2012, UNESCO inscribed the subak system as a World Heritage of humanity.

Each subak, and each Balinese village, writes and keeps its own rulebook. The rulebook is called the ***awig-awig***.

An awig-awig is a constitution written by the community it governs. The people who live under the rules are the people who make them. It is written down, so any member can read it. It is amended in the open, by a known process, in front of everyone. It binds because it is shared, not because someone stronger imposed it.

Water flows through everyone's fields. Rules are written by everyone's hands. Decisions are made where everyone can see. That design kept a complex, life-critical, shared system alive for a millennium, through empires, colonisers and modernity, without ever being owned by anyone.

This project holds that the same design is the honest way to govern the most powerful shared flow of our own time: computation and AI.

## 2. What the philosophy asks of the machine

AWIG OS is an attempt to build that design into the foundation of a computer system. Not as a feature. As the ground.

Every deployment of AWIG OS writes and keeps its own machine-readable rulebook, its own awig-awig. The system does not tell you what your rules should be. It guarantees that your rules are yours, written, and real.

All rules in the system share one common, readable, executable format. There is no privileged syntax for privileged actors. What governs you can be read by you.

Like water through the terraces, every exercise of permission leaves a visible trace. Authority that leaves no trace does not run. The powerful are not asked to be good. They are structured to be seen.

This year the largest operating systems began to fence what an AI agent may touch: which folders, which apps, which network, granted once for the session, off until an administrator switches it on. AWIG OS has no switch. Every act, by an agent or a person, crosses one gate as its own decision, citing the written rule that allowed it, and the row of that decision is the act. An AI organisation inside it meets the world at two openings only, what it is asked and what it asks for, and nothing arriving at the second executes until a rule says so. The two openings are built and proven in test worlds; the organisation between them is the work now under way.

AI inside AWIG OS lives as a governed community, not an oracle. It is bounded, inspectable, constitutional, and the human owner stands above the whole, the way subak members stand above their own institutions.

The commons stays common. This project takes no trademark, sells nothing, and is licensed so that no one, however large, can close it and sell it back to the world with the accountability stripped out. The license is this project's first rule: written down, binding on everyone, heaviest on the strongest. See [`LICENSING.md`](./LICENSING.md).

## 3. Acknowledgment

This project is named in homage to the awig-awig tradition of Bali and Lombok, Indonesia, and to the subak communities who have practised governance as a commons for a thousand years. It also honours Indonesia's wider heritage of deliberation toward consensus, *musyawarah untuk mufakat*.

These traditions are not decoration on this project. They are its argument: legible, self-written, openly practised governance of a shared vital flow is not utopian. It is one of the most proven institutional designs in human history. The world should know where it comes from.

Contributors from Indonesia, and corrections to how this heritage is described, are welcome now and always. Documentation in Bahasa Indonesia is a stated goal of this project.

## 4. Naming commitments (standing, irrevocable)

1. **No enclosure.** This project will never register, claim, or assert trademark or any exclusive right over "AWIG", "awig", or "awig-awig", and will never object to any traditional, cultural, community, or commercial use of these words by anyone.
2. **No litigation.** This project will never initiate or sustain legal action over its name.
3. **No fight over the name, and no surrender on demand.** The name is not worth a lawsuit, and this project will not spend its life in one. Any demand, and the project's answer to it, is published here in full and unedited, on arrival.
4. **Permanent record.** The meaning of the name, this acknowledgment, and, if it ever occurs, the full record of any demand to erase it will be preserved permanently in this project's history.

*Clause 3 amended 8 September 2026.*

## 5. How this project governs itself

A project about governance keeps its own awig-awig, visibly. [`GOVERNANCE.md`](./GOVERNANCE.md) records how decisions here are proposed, discussed, and made, and can be amended only by the process it describes. Decisions of consequence are recorded in the open, including rejections. A community that keeps its refusals honest keeps its acceptances meaningful.

Until a contributor community forms, the project runs as a single maintainer with a full written trace, and moves to community governance as participation grows, the way a rulebook grows with its village.

## 6. The machine

Every organisation keeps five things in five places: a rulebook, an audit log, an institution, a constitution, and the machine that acts, and reads its own history from copies of copies. Here they are one record and five names for it. The record is the definitive; every view, every log, every screen is derived from it and can be thrown away and rebuilt, hash for hash. Fix the definitive and the derivative follows. One kind of rule governs everything in it, from who may open a file to how the rules themselves may change, with no special language for anyone. An AI organisation lives inside it on the far side of one boundary: what it says stays unstructured, what the institution does is structured rows, and nothing crosses from the one to the other except by passing a rule, every yes and every no on the record. The record, the gate and the rules run today in the layer below; the organisation's room has its two doors built and nothing yet living between them. What this is for, situation by situation: [`WHAT-THIS-IS-FOR.md`](./WHAT-THIS-IS-FOR.md).

The technical design is in [`ARCHITECTURE.md`](./ARCHITECTURE.md): what AWIG OS is as software, how it is built, its rule engine, its AI organisation.

Read this as a reference model, not a product. The code that runs is an executable specification of the governing layer, built first so the rules run and can be tested before the kernel underneath them exists; the design papers are the contracts it implements, and `STATUS.md` says what is true today. The kernel is being built to the same contracts and arrives when a stranger can boot it.

The code you can run is in the [`code`](./code/) folder. Download it and run it with Python 3 and nothing else (`cd code && python3 check.py`). The folder carries its own [`code/README.md`](./code/README.md), a fingerprint of every file in `code/RENDER-STAMP.json`, sixteen checks, and the program's own test suite. [`STATUS.md`](./STATUS.md) says in plain words what you can try today, what exists but is not public yet, what is only designed, and the one warning.

The theory it runs on is the [Open Governance Standard](https://github.com/kfkchau/Open-Governance-Standard), and under it the [Open Meta-Governance Standard](https://github.com/kfkchau/Open-Meta-Governance-Standard/): a kernel for governing rules themselves, rules about rules. Read them if that interests you. AWIG OS is that theory, running.

**Where this stands, 13 September 2026.** The engine after campaign 5 runs, and you can check it in three commands: `cd code && python3 seed_demo.py && python3 check.py && python3 run_public_suite.py` (Linux, stock Python; on Windows, WSL). What runs is the governing layer: one record as the only truth, every act a row citing its rule, refusals recorded the same way, the whole world rebuilt from the record alone, hash for hash. The record is chained and sealed, keys are rows, the engine attests itself at boot, there is no delete, and now the border is governed too: a socket act is a recorded decision, something arriving from outside is a draft the rulebook decides, and one machine's row becomes another's receipt. The constitution says so, fifty amendments in. Real cryptography is in this code and off until you install one library; the tree says that on its own front page, and says what an administrator can still read. The test suite ships for the first time. `STATUS.md` holds what is built, what is designed and every cap, dated. The earlier milestones are kept in history at the tags `milestone-0-seed` and `c4-close`.

## 7. Contributing

Code, architecture review, documentation, translation (Bahasa Indonesia especially), and critique of the governance model itself are all welcome. Read [`GOVERNANCE.md`](./GOVERNANCE.md) first. Substantial proposals follow a simple written flow: proposal, open discussion, recorded decision. Accepted or rejected, both are preserved. Contributions carry a Developer Certificate of Origin sign-off (see [`LICENSING.md`](./LICENSING.md)).

## 8. License

In short: the ideas travel free with attribution, and the code stays open forever, for everyone, no matter who touches it. The plain-language explanation is in [`LICENSING.md`](./LICENSING.md).

---

The farmers of the subak never asked whether ordinary people could govern something complex and vital. They wrote their rules and opened the water. The systems that govern your days have rulebooks too. Could you read them if you asked?

---

© Kelvin Chau, 2026
Named in homage to the *awig-awig* and *subak* traditions of Bali and Lombok, Indonesia.
Documentation licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); code under [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html). See [`LICENSING.md`](./LICENSING.md).
For attribution, citation, or inquiries: kelvin@rootrebuilder.org · [https://au.linkedin.com/in/kfkchau](https://au.linkedin.com/in/kfkchau) · or open an issue here.
