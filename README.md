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

*Amended 8 September 2026: clause 3 previously promised to rename within 30 days of any formal demand. A demand is a letter, and a letter is not a right; the clause handed the name to whoever wrote first. The project now answers demands in public and does not surrender on demand. Nothing else changed.*

## 5. How this project governs itself

A project about governance keeps its own awig-awig, visibly. [`GOVERNANCE.md`](./GOVERNANCE.md) records how decisions here are proposed, discussed, and made, and can be amended only by the process it describes. Decisions of consequence are recorded in the open, including rejections. A community that keeps its refusals honest keeps its acceptances meaningful.

Until a contributor community forms, the project runs as a single maintainer with a full written trace, and moves to community governance as participation grows, the way a rulebook grows with its village.

## 6. The machine

The technical design is in [`ARCHITECTURE.md`](./ARCHITECTURE.md): what AWIG OS is as software, how it is built, its rule engine, its AI organisation.

The code you can run is in the [`code`](./code/) folder. Download it and run it with Python 3 and nothing else (`cd code && python3 check.py`). The folder carries its own [`code/README.md`](./code/README.md), a fingerprint of every file in `code/RENDER-STAMP.json`, and eight checks. [`STATUS.md`](./STATUS.md) says in plain words what you can try today, what exists but is not public yet, what is only designed, and the one warning.

The theory it runs on is the [Open Governance Standard](https://github.com/kfkchau/Open-Governance-Standard), and under it the [Open Meta-Governance Standard](https://github.com/kfkchau/Open-Meta-Governance-Standard/): a kernel for governing rules themselves, rules about rules. Read them if that interests you. AWIG OS is that theory, running.

**Where this stands, 8 September 2026.** The smallest piece runs, and you can check it in two commands: `cd code && python3 seed_demo.py && python3 check.py` (Linux, stock Python; on Windows, WSL). What runs is the governing layer: one record as the only truth, every act a row citing its rule, refusals recorded the same way, the whole world rebuilt from the record alone, hash for hash. The record is chained and sealed, keys are rows, the engine attests itself at boot, and there is no delete: the constitution says so, thirty-nine amendments in. Every key in this release is a stand-in of the right shape, not real cryptography, and the tree says that on its own front page. `STATUS.md` holds what is built, what is designed and every cap, dated. The first milestone, the seed, is kept in history at the tag `milestone-0-seed`.

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
For attribution, citation, or inquiries: [https://au.linkedin.com/in/kfkchau](https://au.linkedin.com/in/kfkchau)
