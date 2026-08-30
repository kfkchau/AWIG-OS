"""gov-os kernel — operations as definition records (design/27 §3, build step three).

An operation is a RECORD: its parameters, its checks, and its decision shape enter the
store as a governed amendment (CREATE-OP, citing CAP-IS-LAW — no capability without a
recorded amendment with named authority). The gate runs ONE generic interpreter over
these definitions, and the registry itself becomes derived state: build replays
CREATE-OP / RETIRE-OP from the record and re-registers the live set, so "kill the
registry, replay, identical" now holds for the kernel's own surface. Adding an
operation is a recorded act; retiring one reverts it to not-existing (Closure Hit).

The check vocabulary is CLOSED (adopted-definitives, B09): a check is admitted only
because an existing governed handler already needed it. v1:

  require_prior — a record with action = A and payload.F equal to the named param must
                  exist, else refuse citing R. (The capability pattern — BIND-DEVICE
                  refusing an unregistered driver — and referential integrity itself:
                  nothing may reference what was never minted.)
  sight         — the actor must have been granted read of the target param, else
                  refuse citing SIGHT-IS-LAW. (Sight binds action — the CONSUME pattern.)

An unknown check kind is refused at definition time: a check outside the vocabulary
does not exist. Definition time means ALL THREE DOORS a definition can arrive through —
CREATE-OP, AMEND-OP, and the founding installer — which run one shared vocabulary
(`validate_definition_shape`), because a guard at two of three doors guards nothing.
Growth path, named not built: the ceiling check (the memory-budget
pattern) arrives with the memory-core migration; a full predicate AST (the cgl-app
matchPattern class) is the later shape. Amending a definition-born op = retire + create
(v1 keeps shadowing impossible rather than clever).
"""

import re
from collections.abc import Mapping

from . import authority
from . import crossing
from .errors import OpError
from .protection import can_read

# THE NAMESPACE'S OWN CANONICAL SPELLING, IMPORTED RATHER THAN RE-WRITTEN (EP-28O).
#
# THE DIRECTION IS BACKWARDS AND IT IS SAID HERE RATHER THAN LEFT TO BE NOTICED: this is the
# kernel reading a module that sits above it. It is written this way because `custody._norm`
# is the ONE computer of a canonical path spelling in this repository, and a second computer
# is the exact defect this pass exists to remove — §A52's countable is ONE computer and N
# readers, and a copy of four characters of string arithmetic in kernel space would make it
# two computers that agree until the day they do not. A reader with the direction's cost in
# hand should also have the residual: the law-data home for a key's canonical form is a
# DECLARATION on the binding row, which is a founding change and therefore a ruled law pass —
# never an engine pass's side effect. RAISED by EP-28O, not resolved by it.
from bridge import custody

# THE ENVELOPE-ROUTER FAMILY (design/28 §I6 shape; EP-24B item B completes it). An op
# definition may DECLARE which of its parameters supplies an envelope field, and the one
# interpreter routes it — a general capability, never a per-op branch. The four that existed
# before EP-24B are the first four; the last two are its addition, in the same declaration
# shape, read by the same interpreter, at the same place in `run`. Enumerated here so the
# family stays checkable rather than remembered.
ENVELOPE_ROUTERS = ("target_param", "content_form", "evidence_param", "stamp_actor",
                    "occurrence_time_param", "provenance_param")

# THE FAMILY READS ONE MAP, AND IT IS THE RAW CALLER PARAMETERS (EP-27B ADDENDUM 2 W6a/W6b;
# design/36 ADDENDUM I.2). Members whose declaration NAMES A CALLER PARAMETER are spelled
# `<field>_param` — derived from the family's own spelling rather than enumerated a second time.
# The two that are not — `content_form`, a literal string on the record, and `stamp_actor`, a
# list of payload fields overwritten with the acting actor — name no parameter at all, so there
# is no map for them to be uniform on.
#
# WHY UNIFORMITY RATHER THAN A REFUSAL. `param_defaults` fills a COPY of the caller's parameters
# before the checks run, and three of these four used to read that copy — so a definition could
# supply a router's field with an author-chosen constant, and a REQUIRED pin's refusal would
# never fire, silently. `param_defaults` and the router's own `when_absent` distinction were two
# mechanisms for one idea (how an envelope field is supplied when the caller omits the
# parameter), and two mechanisms for one idea is how the next four arrivals get created. Reading
# the RAW parameters everywhere makes the contradiction structurally impossible rather than
# guarded: a default reaches the PAYLOAD, which is what it is for, and never the envelope.
PARAM_ROUTERS = tuple(r for r in ENVELOPE_ROUTERS if r.endswith("_param"))

# THE REQUIRED-OR-DEFAULTED DISTINCTION (EP-27B; design/36 ADDENDUM F.2). Of the family above,
# these are the members whose envelope FIELD THE STORE MINTS when the record does not carry one
# — mapped to the field each supplies. That property, and nothing about which ops happen to use
# them, is what makes "what does an absent parameter mean" a real question here and an answer
# everywhere else: an absent `target` records an absent target, which is honest, while an absent
# `occurrence_time` records a minted one, which would be the record stating a time nobody
# observed. So these two, and only these two, may declare what an absent parameter means.
#
# SILENCE MEANS REQUIRED, in either form of the grammar, so no declaration can weaken by
# omission or by habit — the EP's named wrong reference is "defaulted" sliding into "does not
# matter", and its detector is EP-22's three observer pins, which still refuse on absence.
MINTED_ROUTERS = {"occurrence_time_param": "occurrence_time",
                  "provenance_param": "provenance"}

#: What an ABSENT parameter means, per op, explicitly. Closed, like the check vocabulary: a
#: value outside it does not exist and is refused at definition time, so a misspelt policy can
#: never sit in a definition reading as one nobody wrote.
REQUIRED, DEFAULTED = "required", "default"
ROUTER_ABSENCE = (REQUIRED, DEFAULTED)

#: The whole grammar of a router's value: a bare parameter name, or the same name written out
#: with what its absence means. Nothing else is admitted.
ROUTER_DECL_KEYS = ("param", "when_absent")

# WHAT KIND OF ACT AN OP IS (EP-28B W1; design/10 §11.1c and its 2026-07-30 amendment).
#
# READ THIS BEFORE ADDING A VALUE, because the field is one wrong reading away from being the
# thing this estate refuses. `act_kind` STATES WHAT AN OP IS. It is not a switch for what the
# gate does with it. The test for a member is a sentence about the op that is true whether or
# not any code reads the field: "RELEASE" means the op's WHOLE effect is to end something the
# caller already lawfully holds — it creates nothing, transfers nothing, and moves no other
# actor's holdings. An op that releases AND does something else is not a release; it is that
# other thing (§11.1c), and the honest declaration is silence.
#
# The CONSEQUENCE is law and lives in `gate._authority_step`, not here: a release is never
# subjected to the authority fold, because refusing a release is incoherent — no actor can be
# denied permission to stop holding what it lawfully holds — and folding one manufactures an ABI
# divergence, since POSIX `close()` on a valid descriptor cannot fail with a permission error.
# So the field carries a fact and the gate derives the exemption from the fact. A declaration
# whose only justification is "it makes the branch go the right way" is refused by review, not
# by code, and that is why the justification is written here beside the vocabulary.
#
# MEMBERSHIP IS BY OP DEFINITION, NOT BY SERVED CAPABILITY (§11.1c amendment): an op is in the
# class the moment its definition exists, so `FILE-UNLOCK` is a release today even though no
# mount serves a lock yet and `T-FLOCK-RECORDS` is red. Those facts do not conflict.
#
# CLOSED, like the check vocabulary and the absence vocabulary above. An unknown value would
# read as no declaration at all — the fold would run, which errs closed and is therefore SAFE
# behaviourally, and that is exactly what makes it dangerous: a misspelt `relase` would sit in
# the founding as a false sentence about an op with nothing ever going red. Refused at
# definition time, at all three doors.
RELEASE = "release"
ACT_KINDS = (RELEASE,)

# WHICH STREAM A RECORD IS WRITTEN UNDER (EP-30-W1a; board :918 route (a)).
#
# THE CONFLATION THIS REMOVES, in one sentence: the DOOR an act enters decided the STREAM its
# declaration landed in, because the interpreter sets the recorded `action` to the op's own
# registered name and `store.by_action` locates by that field. So a declaration could not land
# anywhere but under the door that wrote it — and which stream a law writes into is LAW
# CONTENT, exactly the class this estate has moved into declarations all campaign.
#
# THE DOOR IS NEVER ERASED (constraint 2, and it is why this is a SECOND field rather than a
# rewrite of `action`). `action` still carries the op that wrote the record, unchanged, where
# every existing reader already looks; `record_stream` names where the declaration LANDS. A
# record carries BOTH facts or the shape could not carry the capability at all, which is S5's
# stop. Rewriting `action` instead would hide a record's own author — the W4e class, where the
# record holds an act nobody performed while every view derives correctly from it.
#
# ABSENT BY DEFAULT, AND THAT IS CONSTRAINT 1. An op that does not declare the key sets no
# field, so its record is byte-identical to the one it wrote before this key existed. The
# default is not "the door's name written out"; it is silence, because a written-out default
# would move all 76 shipped records to say something none of them used to say.
#
# NAMED `record_stream` AND NOT `stream`, deliberately: `payload.stream` is already live
# vocabulary for the dual-audit mirror ("dual-audit" / "dual-audit-b", protection.py, read at
# reconcile.py's mirror predicate). A top-level `stream` would put two unrelated meanings of
# one word in one record, which is the same conflation this key exists to remove, one layer
# out. The definition key and the record field share a name, as `content_form` does, because
# the value is a literal the definition states rather than a parameter it routes.
RECORD_STREAM = "record_stream"

OP_CHECKS = ("require_prior", "sight", "ceiling", "consistency", "sop", "definition_ref", "entry_ref",
             "space_tree", "fingerprint", "binding", "kind", "contains", "prior_value",
             "value_domain", "live_slot", "bound_field", "every_member")
#            every_member: EP-30-K2 — APPLY A DECLARED QUESTION TO EVERY MEMBER OF A MANY-VALUED
#            PARAMETER. The SEVENTEENTH kind, and THE FIRST THAT IS NOT A QUESTION — it is a
#            QUANTIFIER OVER THE OTHER SIXTEEN. The sixteen above have sixteen ways to ask about a
#            VALUE and no way to ask about a SET: every one of them reads its subject with a single
#            `params.get` into a single name, so a check declared over a LIST refuses every input
#            including the ones that must pass. The pack declares exactly two many-valued
#            parameters (`COMMS-OPEN endpoints`, `SHM-GRANT grantees`) and neither could be asked
#            anything at all. The minimality gate is discharged against the ARMS by hand rather
#            than by a sweep (EP-30-K2 A1, and the sweep that was wrong twice in sixteen rows at
#            `:2037`): `require_prior` and `ceiling` and `consistency` and `prior_value` quantify
#            over RECORDS, not over a parameter's values; `bound_field` compares ONE VALUE TO ONE
#            VALUE after a locate; `binding`/`kind`/`contains` probe ONE key against a computed
#            space. THE TWO NEAREST MISSES, named because a tool fires on both and is wrong on
#            both: `value_domain` carries a list IN THE DECLARATION and probes ONE parameter value
#            against MANY DECLARED CONSTANTS — the exact INVERSE of this kind's direction; and
#            `live_slot` genuinely ITERATES a declared list, but it iterates PARAMETER NAMES,
#            reading one value out of each into one tuple, and applies no question to any of them.
#            A list of NAMES is not a many-valued PARAMETER.
#            A QUANTIFIER AND NOT A SPECIAL, and that is the owner's rebuildability rider deciding
#            it rather than taste (design/28 §5, the fifth answering of that gate): a flat special
#            — `every_grantee_established` — would BAKE ONE INNER QUESTION INTO THE MENU, and the
#            owner's standing intent to RE-CUT the word list would have to REWRITE it rather than
#            re-derive it. A quantifier adds an AXIS over the existing words: re-cut the words and
#            the axis survives, because it never named any of them. This kind's evaluator names NO
#            other kind — it takes the engine's ONE dispatch site as a callable and hands each
#            member to it, so a re-derivation of the vocabulary moves nothing here.
#            THE EMPTY SET IS DECLARED AND NEVER DEFAULTED. See ON_EMPTY below: "every member of
#            nothing passes" is VACUOUSLY TRUE, and a vacuous pass is the empty-population trap
#            arriving inside the very kind minted to close a cardinality gap.
#            bound_field: EP-30-K1 — BIND A PRIOR RECORD BY ONE PARAMETER AND COMPARE A FIELD OF
#            THAT RECORD AGAINST ANOTHER PARAMETER. The SIXTEENTH kind. The estate could ask
#            whether a record EXISTS with a field equal to a parameter; it could not ask whether
#            *THIS* record — the one this parameter names — has its field equal to *THAT*
#            parameter. THE MISSING CAPABILITY IS BINDING THE RECORD, NOT COMPARING TO IT, and
#            the minimality gate is discharged against the ARMS rather than against a ruling
#            (EP-30-K1 A1, and the ruling it corrects at `:1968`): `require_prior` locates by
#            equality and BINDS NO PARTICULAR RECORD — its question is satisfied by ANY record of
#            the action, so a holder of some OTHER thing satisfies it; `prior_value` binds a
#            record and reads a field out of it but CANNOT BE TOLD A VALUE TO EXPECT, testing
#            only presence against established/unestablished; `sight` asks whether the ACTOR
#            could lawfully read a target, which is a question about the actor and not about a
#            record's field. Neither is derivable from the others, and the separation is DRIVEN
#            rather than asserted (EP-30-K1 R1: the `require_prior` spelling of giver-holds
#            ACCEPTS a giver who holds a DIFFERENT handle; this kind REFUSES it).
#            value_domain / live_slot: EP-30-C1 — the two questions COMMS-OPEN's law asks that no
#            existing kind could ask. `value_domain` asks whether a PARAMETER's value is one the law
#            declares (the existing `kind` check asks what a KEY names, read from the live namespace,
#            which a plain enumerated value never enters). `live_slot` asks whether a computed LIVE
#            SET already holds an occupant for a declared slot — the two-channel invariant's own
#            shape. Neither is derivable from the other twelve, which is the minimality gate stated
#            rather than assumed; and they are two kinds and not one because the estate's own
#            requirement vocabulary separates binding/kind/contains for exactly this reason — a check
#            that merged two questions could not say WHICH one refused.
#            sop: EP-09, design 28 §5 · definition_ref: EP-12 · entry_ref: EP-13B/W5 — a record-seq
#            reference (DISPUTE/RESOLVE-DISPUTE) must name an existing dictionary entry, integrity at use.
#            space_tree: EP-16 X1 — the check the space-founding op (CREATE-SPACE) carried as boot-handler
#            logic, now vocabulary so it is a definition-born pack record (the space-tree cycle +
#            parent-exists bar). CREATE-ROLE / REVOKE need no check (pure record producers).
#            RETIRED (EP-19 R-C2, design/28 §5): the `attenuation` check kind. GRANT's whole-containment
#            leash moved to the gate chokepoint (`_grant_containment`, EP-18 R-A) so a passthrough op
#            minting a grant-kind record cannot bypass it; no pack op cites `attenuation` any longer —
#            one law, one home. (The check vocabulary grows/shrinks only by design amendment.)
#            fingerprint: EP-23 — design/34 §6 verbatim, adopted by the design/35 ruling: "recompute the
#            declared input-view asOf now; compare canonical hash to the hash recorded at hand-out; on
#            mismatch refuse citing the staleness rule". The one check kind that RECORDS ITS VERDICT
#            (fingerprint_check: pass) rather than only refusing — design/34 §7 asks the accepted record
#            to carry the passed check, so a reader sees that the seal was tested and not merely
#            unrefused. Returns runs in the governance lane; no per-operation hot path touches it (K3).
#            binding: EP-28K — the EXISTENCE precondition, moved off the port and into the law. See
#            the derivation at BINDING below; the design/28 §5 row and its owner gate are RAISED by
#            that pass rather than taken, because a check kind is engine vocabulary.
#            kind: EP-28N — WHAT the key names, as distinct from WHETHER it is bound. See the
#            derivation at KIND below; the design/28 §5 row and its owner gate are RAISED by that
#            pass on the same reasoning as `binding`'s.
#            contains: EP-28N AMENDMENT 1 — WHAT a key HOLDS, the first question whose answer
#            depends on the key space AROUND a key rather than on the key alone. See the
#            derivation at CONTAINS below; the design/28 §5 row and its owner gate are RAISED by
#            that pass on the same reasoning as `binding`'s and `kind`'s.
#            prior_value: EP-29 W3a3 — WHETHER A NAMED FIELD INSIDE A CITED PRIOR RECORD HOLDS A
#            VALUE. The THIRTEENTH kind, and the FIRST one whose §5 gate was ANSWERED BEFORE the
#            kind was written rather than raised after it: the owner ruled the vocabulary grows
#            twelve to thirteen on 2026-08-14, on EP-29 W3a2's establishment — seventeen
#            formulations spanning all twelve live kinds, minted through the ordinary door and
#            called against the two shipped intake declarations, ZERO separating them, both
#            positive controls separating. See the derivation at PRIOR_VALUE below. THE LICENCE IS
#            ONE KIND: nothing else rides it, and the growth path this block names below is still
#            named-not-built.

# WHAT AN OP DOES TO A NAME BINDING (EP-28K; design/28 §5's check vocabulary, one new kind).
#
# READ THIS BEFORE ADDING A DECLARATION, because the field states FACTS about the op and is one
# wrong reading away from being a switch. A `binding` check says two things about ONE parameter:
# what must already be true of the key that parameter carries (`require`), and what this act does
# to that key (`effect`). Both are sentences about the operation, true whether or not any code
# reads them — "a create may not land on a name something already holds" and "a create takes that
# name" are facts about creating, not instructions to this interpreter.
#
# WHY THE CHECK BELONGS HERE AND NOT AT A PORT, which is the whole of EP-28K. A caller that reads
# "is this name taken?" and then asks the gate to act has performed CHECK-THEN-ACT ACROSS THE
# DECIDE REGION'S BOUNDARY: two callers both read absent, both decide, and both append. The served
# state is right — both derive one identity (EP-28I) — and the RECORD holds an act nobody
# performed, which is the inversion nothing in this estate looks for, because every guard runs
# record -> view. Inside the region the read and the append are ONE UNIT BY CONSTRUCTION, which is
# what the region is for (EP-28G ADDENDUM 1: the decision IS the record).
#
# IDEMPOTENCE IS REFUSED, and the reason is the same sentence: a create that finds the name held
# and reports success makes the STATE right and the RECORD wrong. Accepted-but-cannot-honour
# REFUSES (standing theorem 6), the refusal cites the declared check, and the caller's remedy is
# the estate's re-ask shape.
#
# THE FOLD IS THE LAW'S OWN, NOT THIS MODULE'S (I5). Which acts bind and unbind is read from the
# op definitions themselves — every op declaring an `effect` contributes its rows — so the live set
# is derived from the recorded law and never from a list in code. An op added next campaign that
# moves a name declares it, or the door refuses it. WHICH PARAMETERS CARRY KEYS is read the same
# way (`_declared_keys` below): this module holds no list of parameter names either.
#
# THE CLAIM THAT STOOD HERE IS NARROWED BY EP-28O, AND THE NARROWING IS STATED RATHER THAN QUIETLY
# DROPPED. It read: "the engine holds NO namespace grammar: a key is whatever string the declared
# parameter carries, compared as recorded." Compared-as-recorded meant `/a/` and `/a` were TWO KEYS
# to the law and ONE NAME to the namespace fold — one object under two keys — so every question the
# law could ask about a name answered about a namespace it was not in (measured: EP-28K's committed
# divergence row, and EP-28N's eight members blocked on exactly it). This module now holds EXACTLY
# ONE item of namespace grammar and no more: a declared key is compared in the NAMESPACE'S CANONICAL
# SPELLING, computed by that namespace's own `_norm` and by nothing here. The residual — that the
# spelling's law-data home is a declaration on the row rather than an import at the top of this file
# — is RAISED by EP-28O rather than resolved by it, because a founding change is a ruled law pass.
#
# THE LEASH IS STRUCTURAL AND LIVES IN THE SUITE (`tests/test_ep28o.py`, TestTheLeashThisPowerArrives
# With): the ops declaring a key check and the ops citing the namespace law are TODAY the same seven,
# set-diffed both directions, so the first key space that is not a path REDS instead of being
# silently respelled by a rule that was never about it.
#
# AN ACT'S EFFECT APPLIES ONLY WHERE ITS OWN DECLARED REQUIREMENTS HELD. That is one rule rather
# than a second spelling of the same condition: FILE-LINK binds its new name only where its target
# was bound, and FILE-RENAME moves a name only where the source was bound. Records appended UNDER
# this law always met their requirements, so the rule is inert for them; it is what makes the fold
# reproduce a PRE-LAW history exactly, which is what a two-times estate needs from any fold that
# walks records decided under an older law.
BINDING = "binding"
BOUND, UNBOUND = "bound", "unbound"
BINDING_REQUIREMENTS = (BOUND, UNBOUND)
BIND, UNBIND = "bind", "unbind"
BINDING_EFFECTS = (BIND, UNBIND)

# WHAT A KEY NAMES, AS DISTINCT FROM WHETHER IT IS BOUND (EP-28N; design/28 §5's check
# vocabulary, one new kind).
#
# READ THIS BEFORE ADDING A DECLARATION, because both fields state FACTS about the op and are
# one wrong reading away from being switches. A `kind` check says one thing about ONE
# parameter: the key it carries must be (`require`), or must not be (`forbid`), of a stated
# class. A `binds_kind` on a bind-effect binding row says what class this act GIVES the key it
# binds. Both are sentences about the operation, true whether or not any code reads them.
#
# THE ENGINE LEARNS NO VOCABULARY, AND THAT IS THE WHOLE OF I5 HERE. A class is whatever string
# the law declares — this module never holds one, never compares against one, and cannot tell a
# directory from anything else. It folds `key -> class` out of the declarations and compares
# what it was handed against what the row asked for. The words live in the founding.
#
# THREE SOURCES, EACH NEEDED BY A SHIPPED OPERATION and none of them decoration:
#   {"literal": C}     the act always gives this class (a directory-making act makes directories)
#   {"param": P}       the act gives the class its own record carries in P (a create records what
#                      it created, so the record answers rather than the op's name)
#   {"from_key": K}    the act CARRIES the class of the key parameter K named (a rename moves a
#                      name and the thing keeps being what it was; a second name for a thing is
#                      a name for that same thing)
# Without the third, a renamed directory would lose its class in the fold and the next act over
# it would be refused for being something it never stopped being.
#
# THE CLASS CLAUSE IS THE DELIVERABLE AND THE THREE MEMBERS ARE ITS INSTANCES. An op that binds
# a key under a law some op asks class questions about, and does not say what class it binds,
# leaves that key CLASSLESS — so every later class question answers about a namespace it is not
# in, silently, and worse the longer it runs. Refused at all three definition doors.
#
# WHY A CLASS QUESTION MAY ONLY BE ASKED OVER A KEY THE SAME OP REQUIRES BOUND. An unbound key
# has no class, so a class check answering first would report "not of this class" about a name
# that is not there — a true sentence about the wrong question, and at a boundary that renders
# errnos it is the wrong answer to the caller. The guard holds the ORDER too, because
# declaration order is the answer order.
KIND = "kind"
BINDS_KIND = "binds_kind"
KIND_SOURCES = ("literal", "param", "from_key")

# WHICH KEY A ROW ASKS ABOUT, WHEN IT IS NOT THE ONE THE PARAMETER CARRIES (EP-28N
# AMENDMENT 1; design/28 §5's check vocabulary, one new declaration).
#
# READ THIS BEFORE ADDING A VALUE. `key_of` states a FACT about the question a row asks:
# this row is about the key that CONTAINS the one this parameter carries. "A name can only
# be taken inside something that is there" is a sentence about creating, true whether or not
# any code reads it — it is not an instruction to derive a key here.
#
# WHY THE DERIVATION IS THE LAW'S AND NOT THE CALLER'S, which is the whole reason this is a
# declaration and not a parameter. The cheaper shape is to let the PORT compute the container
# and hand it in as a parameter the law then checks — the plan floats it, on the `render_ino`
# precedent. It is not that precedent and it is the opposite direction: `render_ino` renders
# OUTWARD a decision the record already made, while a handed-in container is a caller
# computing a PRECONDITION the gate then trusts. That is CHECK-THEN-ACT ACROSS THE DECIDE
# REGION'S BOUNDARY wearing a parameter — a caller supplying a container of its own choosing
# is checked against a key nobody derived — and closing exactly that shape is what EP-28K
# exists for. The derivation happens INSIDE the region, from the act's own already-canonical
# key, or it is not a precondition at all.
#
# THE RELATION IS THE NAMESPACE'S OWN AND IS READ FROM ITS ONE COMPUTER (§A52) — the same
# import, and for the same reason, as EP-28O's canonicalisation: a copy of the container
# arithmetic in kernel space would be a SECOND computer of one rule. The layering cost of
# that import is real, it is now two functions rather than one, and EP-28N AMENDMENT 1 RAISES
# it rather than paying it down — see that pass's entry for why the fence cannot.
#
# AN EFFECT MAY NEVER CARRY ONE. An act binds the name it acts on and never the name that
# contains it; a row that declared both would say a create takes its own parent. Refused at
# all three definition doors.
KEY_OF = "key_of"
CONTAINER = "container"
KEY_DERIVATIONS = (CONTAINER,)

# THE ONE KEY NO ACT BINDS (EP-28N AMENDMENT 1).
#
# A hierarchy question needs a bottom. `container("/a")` is the root, and the root is bound by
# NO RECORDED ACT — nothing creates it, `custody.ROOT_INO`'s own comment pins it as the one
# identity with no covering record — so a fold over acts can never contain it, and every
# top-level create would be refused for landing in a container that no record founds.
#
# SO THE LAW SAYS IT, BECAUSE THE LAW IS THE ONLY THING THAT CAN. A `key_space` on the rule a
# key check cites declares the root of that key space and what the root NAMES; the fold seeds
# both before it walks. The engine still holds no root and no class of its own: both are the
# law's own words, read through the same view every other law read takes.
#
# A LAW THAT DECLARES NO KEY SPACE SEEDS NOTHING, and that is the two-times law holding by
# construction rather than by a branch: a world founded before this declaration has no key
# space and no rows that need one, so its fold is bit-for-bit the fold it always had.
KEY_SPACE = "key_space"
KEY_SPACE_ROOT = "root"
KEY_SPACE_ROOT_KIND = "root_kind"

# WHAT A KEY HOLDS, AS DISTINCT FROM WHETHER IT IS BOUND AND WHAT IT NAMES (EP-28N
# AMENDMENT 1; design/28 §5's check vocabulary, one new kind).
#
# READ THIS BEFORE ADDING A DECLARATION. A `contains` check says one thing about ONE key:
# nothing else in this key space sits inside it. `binding` and `kind` ask about a key alone;
# this is the first question whose answer depends on the key space AROUND the key, which is
# why it is a new kind rather than another polarity on an existing one.
#
# IT NEEDS NO CLASS-ABSENCE CLAUSE OF ITS OWN, and that is derived rather than skipped:
# containment is computed from the live key set, and that set is folded from the `binding`
# declarations EP-28K's own absence clause already forces every act under this law to make.
# There is nothing an op could omit here that would leave a container silently reading empty.
#
# AND IT DEMANDS NO PRIOR BOUND ROW, unlike `kind`. An unbound key NAMES nothing, so asking
# what it is would answer about a name that need not be there; but an unbound key HOLDS
# nothing, which is a true and useful answer — FILE-RENAME's destination is exactly that case,
# and POSIX gives it no ENOTEMPTY either.
CONTAINS = "contains"
EMPTY = "empty"
CONTAINS_REQUIREMENTS = (EMPTY,)

# WHETHER A NAMED FIELD INSIDE A CITED PRIOR RECORD HOLDS A VALUE (EP-29 W3a3; design/28 §5's
# check vocabulary, THE THIRTEENTH KIND, owner-ruled 2026-08-14 on EP-29 W3a2's establishment).
#
# READ THIS BEFORE ADDING A DECLARATION. A `prior_value` check says one thing about ONE prior
# record: the record this act's licence would be computed from names a field, and that field
# either HOLDS A VALUE or is DECLARED to hold none. It is the first question in this vocabulary
# whose subject is INSIDE a record rather than the record's existence, its actor, an aggregate
# over many records, or a key's state.
#
# WHY IT COULD NOT BE AN EXISTING KIND PARAMETERIZED, which is C6's own order of preference and
# was DRIVEN before this kind was written rather than argued (EP-29 W3a2, seventeen formulations,
# all twelve kinds, zero separating, two positive controls separating):
#
#   * `require_prior` is the nearest and stops TWO steps short. Its `field` is a LITERAL KEY, so
#     a nested name finds nothing and refuses the very class it must admit — the same row over
#     the top-level key admits both, inverted by nothing but a dot. And its comparison value
#     comes from a PARAMETER, so the CALLER supplies what the record is measured against, which
#     is a check the caller satisfies by construction.
#   * THE TWO-ROW CONJUNCTION DOES NOT HOLD, and this is the decisive fact. Each `require_prior`
#     row is an INDEPENDENT existence scan, so binding the record with one row and asking about
#     its value with a second is satisfied by TWO DIFFERENT RECORDS — measured: a call citing net
#     while carrying block's threshold passes both rows. THIS KIND'S WHOLE ADDITION IS THAT THE
#     LOCATE AND THE READ MEET THE SAME RECORD, and that is why the read lives here and not in a
#     second row.
#   * `ceiling` is the one kind that reads a numeric field out of prior records, and it COLLIDES
#     with the law rather than falling short of it: it SUMS that field, and a law that requires
#     every value to carry its population and basis (§A51) cannot have a summable one.
#   * `binding` / `kind` are refused AT THE FOUNDING DOOR for a law whose acts bind no names, so
#     the shape closest to "this name is of a class meaning its value is established" cannot even
#     be declared.
#
# THE READ IS A DOTTED PATH AND THE PATH IS ALL THE REACH IT GAINS. `value_field` is the ONE new
# declaration key this kind adds to the check-row grammar; everything else it needs — `action`,
# `field`, `param`, `require`, `cite`, `message` — is grammar the twelve already speak. The path
# is walked over MAPPINGS ONLY and it neither indexes sequences nor evaluates anything: this is
# not the predicate AST the growth path names, and that shape stays named-not-built.
#
# THREE REFUSALS, NEVER TWO, because the law's own sentence distinguishes them and an engine that
# merged them would answer a different question than the one declared. An UNESTABLISHED value is
# DECLARED unestablished, NEVER OMITTED — so a declaration that is SILENT about the field is not
# the unestablished case, it is interior silence, and interior silence filled by a default is the
# fail-open trap this vocabulary exists to refuse (EP-29 ADDENDUM 4 §5's taxonomy):
#
#   no prior record matches   -> the record the licence computes from does not exist
#   the path does not resolve -> the field is omitted where the law requires it declared
#   the value's presence      -> compared against `require`; a mismatch refuses
#
# LATEST WINS, and it is the estate's own direction rather than a convenience: a declaration
# amended later is the one in force, so the record read is the HIGHEST-SEQ match. A row that read
# the earliest would answer about a superseded law.
PRIOR_VALUE = "prior_value"
ESTABLISHED, UNESTABLISHED = "established", "unestablished"
PRIOR_VALUE_REQUIREMENTS = (ESTABLISHED, UNESTABLISHED)

# BIND A PRIOR RECORD BY ONE PARAMETER, COMPARE A FIELD OF IT AGAINST ANOTHER (EP-30-K1; the
# SIXTEENTH kind, minted by archi at board :1965 and countersigned whole-plan at :1982).
#
# READ THIS BEFORE ADDING A DECLARATION. A `bound_field` check says one thing about ONE prior
# record: the record THIS ACT'S OWN PARAMETER NAMES carries a field, and that field must equal
# what a SECOND parameter of the same act carries. It is the first question in this vocabulary
# whose two ends are BOTH supplied by the caller while the ANSWER is not — the caller says which
# record and says what it expects, and the RECORD says whether that is so.
#
# WHY IT COULD NOT BE AN EXISTING KIND PARAMETERIZED, discharged against the ARMS and not against
# the ruling that minted it — the ruling's own formulation was refuted by `require_prior`'s arm
# and corrected at `:1968`, so a gate argued from the ruling would have passed on a false sentence:
#
#   * `require_prior` IS THE NEAREST AND IT BINDS NOTHING. Its arm asks whether ANY record of the
#     declared action carries the declared field equal to the parameter — `any(...)` over
#     `store.by_action`. It is an EXISTENCE SCAN, so "the giver holds this handle" and "the giver
#     holds SOMETHING" are the same question to it. DRIVEN, not argued (EP-30-K1 R1): with a giver
#     who holds a DIFFERENT handle, the `require_prior` spelling ACCEPTS and this kind REFUSES.
#     EXISTENCE IS NOT SELECTION, and that sentence is this kind's whole addition.
#   * `prior_value` BINDS THE RECORD AND CANNOT BE TOLD WHAT TO EXPECT. Its value comes from the
#     record and never from a parameter — deliberately, because a caller-supplied comparand is a
#     check the caller satisfies by construction, which is exactly right for a LICENCE test and
#     exactly wrong here. The question here is a RELATION BETWEEN TWO OF THE CALLER'S OWN
#     PARAMETERS, adjudicated by the record; `prior_value` can only test presence against
#     established / unestablished and has no place to put the second parameter.
#   * `sight` asks whether the ACTOR could lawfully READ the target. That is a question about the
#     actor's permissions, answered by `can_read` against GRANT-READ; it names no field of any
#     prior record and could not be pointed at one.
#   * `binding` / `kind` / `contains` ask about a KEY'S STATE in the live namespace, not about a
#     RECORD'S FIELD, and the custody chain binds no names at all.
#
# ONE NEW DECLARATION KEY, WHICH IS `prior_value`'s OWN BUDGET. Everything this kind needs —
# `action`, `field`, `key_param`, `value_field`, `param`, `cite`, `message` — is grammar the
# fifteen already speak: `key_param` is `binding`/`kind`/`contains`'s locator, `value_field` is
# `prior_value`'s read. The one addition is WHEN_UNBOUND, below.
#
# THE READ REUSES `_resolve_field_path` AND GAINS NO REACH. Mappings only, no sequence indexing,
# no evaluation; the predicate AST the growth path names stays unbuilt.
#
# LATEST WINS, and here it is not a convenience but the ESTABLISHED SHAPE OF A CURRENT HOLDING.
# EP-30-E1 (board :888) drove eighteen formulations and found the check vocabulary was never the
# constraint — THE RECORD SHAPE IS: a current holding is expressible under latest-seq-wins when
# the state is written as an AMENDING DECLARATION OF THE SAME ACTION, and blind when written as a
# separate revoking act. So the HIGHEST-SEQ match is read, and a row reading the earliest would
# answer about a superseded holding.
BOUND_FIELD = "bound_field"

# WHAT AN UNBOUND KEY MEANS, PER DECLARATION, EXPLICITLY — the ONE key this kind adds.
#
# THE QUESTION IT ANSWERS: the key parameter names a record, and no record of the declared action
# carries it. Is that a refusal, or is it outside this rule's reach?
#
# BOTH ARE REAL LAWS AND NEITHER IS DERIVABLE FROM THE OTHER, which is why this is DECLARED rather
# than decided here. `prior_value`'s subject is a DECLARATION the licence is computed from, and a
# missing one means no licence exists — refuse. THIS kind's subject can be a RELATION THAT HAS NOT
# YET BEEN ENTERED INTO: a handle no transfer names has not entered the custody chain, and the law
# that governs the chain has nothing to say about it. An engine that picked one would be answering
# a question the law-data is entitled to answer.
#
# AND THE MEASUREMENT IS WHY THIS EXISTS AT ALL, recorded here because it is the kind of fact that
# is expensive to rediscover. A `bound_field` that refuses every unbound key makes
# FILE-CUSTODY-TRANSFER UNUSABLE: no handle could ever make its FIRST hop into the chain, so the
# chain would stay permanently empty and the check would never have anything to compare. DRIVEN
# before this kind was written, with both controls (EP-30-K1 PROBE A): the shipped four checks red
# ZERO rows; the same world plus a "a prior transfer must name this handle" row reds ELEVEN. The
# strict form is not stricter — IT IS VACUOUS, and a check that refuses everything is not a check.
#
# SILENCE MEANS REFUSE, following ROUTER_ABSENCE's rule verbatim and for its reason: no declaration
# may weaken by omission or by habit. A law whose reach stops short SAYS SO, in the law-data, where
# a reader looking at the declaration can see it — never by an engine default nobody wrote down.
# CLOSED, like every vocabulary in this module: an unknown value is refused at all three doors, so
# a misspelt policy can never sit in a definition reading as one nobody wrote.
WHEN_UNBOUND = "when_unbound"
UNBOUND_REFUSE, UNBOUND_PERMIT = "refuse", "permit"
UNBOUND_POLICIES = (UNBOUND_REFUSE, UNBOUND_PERMIT)

EVERY_MEMBER = "every_member"
INNER = "inner"
MEMBER_PARAM = "member_param"

# THE EMPTY-SET ANSWER, DECLARED BY THE LAW AND NEVER SUPPLIED BY THIS ENGINE (EP-30-K2).
#
# THE TRAP THIS KEY EXISTS TO CLOSE, stated before the mechanism because the mechanism is
# obvious and the trap is not: "EVERY MEMBER OF NOTHING PASSES" IS VACUOUSLY TRUE. A quantifier
# that defaults to admitting the empty set gives every law declared over a many-valued parameter
# a free exit — supply no members and the question is satisfied by the absence of anything to
# ask. THAT IS A FAIL-OPEN DRESSED AS LOGIC, and it is the empty-population defect arriving
# inside the very kind minted to close a cardinality gap.
#
# AND THE OTHER DEFAULT IS NOT SAFE EITHER, which is why this is DECLARED rather than decided
# here. Defaulting to REFUSE makes a law over an OPTIONAL many-valued parameter unusable: both
# pack parameters default to `[]`, so a strict-by-default quantifier would refuse every act that
# simply did not use the optional list — the vacuity failure `bound_field`'s measurement found
# from the other side (a check that refuses everything is not a check). BOTH ANSWERS ARE REAL
# LAWS, NEITHER IS DERIVABLE FROM THE OTHER, and an engine picking one would be answering a
# question the law-data is entitled to answer.
#
# SO SILENCE IS NOT AN ANSWER HERE AND DOES NOT RESOLVE TO ONE. Unlike WHEN_UNBOUND, where
# silence means the strict policy, THIS KEY IS MANDATORY: a declaration omitting it is REFUSED AT
# DEFINITION TIME, at all three doors, before any act reaches it. That follows `value_domain`'s
# absent-is-not-in-the-domain precedent one layer out — a default is a statement the law makes
# where silence is not — and it is what keeps the requirement from being a *must* with no refusal
# behind it, which is the written-rule rung of this estate's enforcement ladder and the rung a
# seat can breach by accident.
ON_EMPTY = "on_empty"
ON_EMPTY_ADMIT, ON_EMPTY_REFUSE = "admit", "refuse"
ON_EMPTY_ANSWERS = (ON_EMPTY_ADMIT, ON_EMPTY_REFUSE)

# THE REQUIREMENT VOCABULARY, WITH ONE HOME (EP-28N). A refusal raised by one of these checks
# carries WHAT THE ACT REQUIRED AND DID NOT GET, because a boundary rendering the caller's answer
# must key on THE ACT and the rule cannot tell it: one rule governs a refused create and a refused
# unlink of an absent name, and POSIX gives them different answers, so no rule-keyed row could be
# right for both. The strings are composed from the law's own declared values, so this module
# still names no class of its own; and they are built HERE rather than at each boundary, because a
# vocabulary spelled twice is two vocabularies (ADDENDUM I.2).
REQ_BINDING = "binding:%s"
REQ_KIND_REQUIRE = "kind:require:%s"
REQ_KIND_FORBID = "kind:forbid:%s"
REQ_CONTAINS = "contains:%s"


def _requirement(base, key_of):
    """THE ACT'S DEMAND, CARRYING WHICH KEY IT WAS ABOUT (EP-28N AMENDMENT 1).

    THIS EP'S OWN LESSON, APPLIED TO ITS OWN VOCABULARY BEFORE ANYTHING NEEDED IT.
    `binding:bound` over the key a parameter carries and `binding:bound` over the key that
    CONTAINS it are two different outcomes: POSIX answers the first ENOENT for an unlink of an
    absent name and the second ENOENT for a create into an absent container, and today no
    shipped op raises both — which is exactly the condition under which a shared string looks
    harmless and stays wrong. A requirement that could not tell them apart would be a
    rule-keyed map wearing an act key, one layer down from the one this EP removed. The
    suffix is what stops the next op from rebuilding it."""
    return base if not key_of else "%s@%s" % (base, key_of)


def declared_requirements(d):
    """The requirement strings this definition's checks can raise — the set a boundary that
    renders outcomes must cover, computed from the definition rather than remembered."""
    out = set()
    for c in (d.get("checks") or []):
        of = c.get(KEY_OF)
        if c.get("check") == BINDING and c.get("require") is not None:
            out.add(_requirement(REQ_BINDING % c["require"], of))
        elif c.get("check") == KIND:
            if c.get("require") is not None:
                out.add(_requirement(REQ_KIND_REQUIRE % c["require"], of))
            if c.get("forbid") is not None:
                out.add(_requirement(REQ_KIND_FORBID % c["forbid"], of))
        elif c.get("check") == CONTAINS and c.get("require") is not None:
            out.add(_requirement(REQ_CONTAINS % c["require"], of))
    return out


def _refuse_about_the_act(gate, actor, opname, c, message, requirement):
    """Refuse, and let the ACT'S OWN DEMAND travel with the refusal (EP-28N).

    The record is unchanged and stays keyed by the RULE — the tip-level terminal rule the act
    is under — because that is the justification a reader ever sees, and a citation chosen to
    steer a return value is forgery of it (§A56). What travels alongside is not a second
    citation: it is what this act asked of its key, which the check has just computed and which
    the caller cannot re-derive without reading state the region owns.

    Only `OpError` is touched, so a door that raises its own refusal — the founding installer's,
    or a shape check running without a store — passes through unchanged."""
    try:
        gate.refuse(actor, opname, c.get("cite") or "ROOT-NEG-1", message)
    except OpError as e:
        e.requirement = requirement
        raise


def router_param(d, router):
    """THE ONE READER of a router's value (EP-27B). Returns (parameter name, what an absent
    parameter means). Silence — no declaration, a bare name, or a longhand form that says
    nothing about absence — is REQUIRED, which is what every declaration meant before this
    grammar existed, so an op written yesterday cannot have been weakened by it."""
    decl = d.get(router)
    if decl is None:
        return None, REQUIRED
    # Mapping, not dict: a definition read back off the record is FROZEN (H1), so the longhand
    # form arrives as a read-only mapping. Testing for `dict` would silently take a frozen
    # longhand declaration for a parameter NAMED after the whole declaration — a router that
    # routes a dictionary, which is the defect this line exists to not have.
    if isinstance(decl, Mapping):
        return decl.get("param"), decl.get("when_absent") or REQUIRED
    return decl, REQUIRED


def _require_wellformed_routers(gate, opname, actor, d):
    """The leash the distinction arrives with, in the same round it does (design-soul §2), and
    at DEFINITION time — the way an unknown check kind is already refused, because a policy that
    does not exist should not wait for a caller to discover it.

    Three refusals, each closing one way "defaulted" could come to mean "does not matter":
    a longhand declaration that names no parameter routes nothing; an unknown key or an unknown
    absence value is a policy nobody wrote and would silently read as REQUIRED; and a longhand
    declaration on a router the store does not mint for is DECORATION — there is no minted value
    to fall back to, so the words would read as law and do nothing. Two mechanisms for one idea
    is how the next four arrivals get created."""
    for router in ENVELOPE_ROUTERS:
        decl = d.get(router)
        if not isinstance(decl, Mapping):
            continue
        if router not in MINTED_ROUTERS:
            gate.refuse(actor, opname, "AR-2",
                        f'"{router}" may not declare what an absent parameter means: the store '
                        f"mints no value for the field it supplies, so there is nothing to fall "
                        f"back to (the members that can are: {', '.join(MINTED_ROUTERS)})")
        unknown = [k for k in decl if k not in ROUTER_DECL_KEYS]
        if unknown:
            gate.refuse(actor, opname, "AR-2",
                        f'"{router}" declares {unknown[0]!r}, which is not part of a router '
                        f"declaration — the whole grammar is: {', '.join(ROUTER_DECL_KEYS)}")
        if not decl.get("param"):
            gate.refuse(actor, opname, "AR-2",
                        f'"{router}" names no parameter — a router that routes nothing from '
                        "nowhere is unrecordable")
        if "when_absent" in decl and decl["when_absent"] not in ROUTER_ABSENCE:
            gate.refuse(actor, opname, "AR-2",
                        f'"{router}" says an absent parameter means '
                        f'{decl["when_absent"]!r} — the vocabulary is: '
                        + ", ".join(ROUTER_ABSENCE))


def _require_wellformed_act_kind(gate, opname, actor, d):
    """The leash `act_kind` arrives with, in the same round it does (design-soul §2), and at
    DEFINITION time — the way an unknown check kind and an unknown absence policy are already
    refused, because a policy that does not exist should not wait for a caller to discover it.

    Two refusals. An unknown kind is a sentence nobody wrote: it would read as no declaration,
    the fold would run, and the founding would carry a false statement about an op with nothing
    going red. And a RELEASE that is also attenuation-family is a self-contradicting definition:
    the attenuation family WRITES the power structure, which is doing something else, and
    §11.1c says an op that releases and does something else is not a release. Refusing the
    combination keeps the contradiction unrepresentable rather than merely unlikely — and it
    also closes the route by which a release declaration could reach the leashed branch at all.
    """
    kind = d.get("act_kind")
    if kind is None:
        return
    if kind not in ACT_KINDS:
        gate.refuse(actor, opname, "AR-2",
                    f'"act_kind" says this operation is a {kind!r}, which is not a kind of act '
                    f"this system knows — the vocabulary is: " + ", ".join(ACT_KINDS))
    if kind == RELEASE and d.get("authority_regime") == "attenuation-family":
        gate.refuse(actor, opname, "AR-2",
                    'an operation may not declare itself a release AND attenuation-family: '
                    "the attenuation family writes the power structure, and an op that releases "
                    "and also does something else is not a release (design/10 §11.1c)")


def _near_miss(key, target):
    """Is `key` one single-character edit away from `target`? One substitution, one insertion
    or one deletion — the three ways a name gets typed wrong.

    Deliberately NOT a general similarity score. The question this answers is "was this key
    trying to be `record_stream`", and a distance-1 test answers it without ever having to
    decide how close is close enough."""
    if key == target:
        return False
    a, b = key, target
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):                       # one substitution
        return sum(x != y for x, y in zip(a, b)) == 1
    if len(a) > len(b):                        # one deletion from `key` reaches `target`
        a, b = b, a
    for i in range(len(b)):                    # one insertion into `a` reaches `b`
        if a == b[:i] + b[i + 1:]:
            return True
    return False


def _require_wellformed_record_stream(gate, opname, actor, d):
    """The leash `record_stream` arrives with, in the same round it does (design-soul §2), and
    at DEFINITION time — the way an unknown check kind, an unknown absence policy and an
    unknown act kind are already refused.

    THE REFUSAL THAT MATTERS IS THE MISSPELLED KEY, and it is worth stating why it is not
    symmetric with a misspelled VALUE. This key's absence is meaningful: it means "write under
    the door", which is what all 76 shipped ops do. So a key spelled `record_streem` is read by
    nobody, the definition falls back to the default, and the op writes under its own door
    while its author's declaration sits in the founding saying otherwise. THAT IS A FAIL-OPEN
    WEARING A DEFAULT'S CLOTHES — nothing goes red, no view disagrees, and the law says one
    thing while the record does another. A near-miss is therefore REFUSED rather than ignored.

    A misspelled VALUE needs no such rule and does not get one. A record declaring a stream
    nobody reads lands in that stream visibly: `by_action` on the door correctly does not
    return it, so the mistake is loud at the first read. The asymmetry is the point — the key
    is refused because its failure is SILENT, and the value is left alone because its failure
    is not. (Whether a declared stream must name an existing op is a law-surface question this
    engine pass does not answer; it is RAISED, not decided here.)

    Two refusals: a near-miss key, and a value that is not a non-empty string — an empty or
    non-string value would fall back to the door exactly as a missing key does, which is the
    same fail-open reached by a different route."""
    for key in d:
        if _near_miss(key, RECORD_STREAM):
            gate.refuse(actor, opname, "AR-2",
                        f'{key!r} is one character from "{RECORD_STREAM}" and is not a key this '
                        "system reads — a near-miss would be ignored in silence and the "
                        "operation would write under its own door while its definition says "
                        "otherwise. Spell it exactly or remove it")
    if RECORD_STREAM not in d:
        return
    value = d[RECORD_STREAM]
    if not isinstance(value, str) or not value:
        gate.refuse(actor, opname, "AR-2",
                    f'"{RECORD_STREAM}" names {value!r} as the stream this operation\'s records '
                    "are written under, which is not a name — a stream that cannot be named "
                    "would fall back to the door in silence")


# WHAT AN OP MINTS (EP-28I; design/36 ADDENDUM I.3's three doors).
#
# READ THIS BEFORE ADDING A MEMBER, because the field states a FACT about the op and is one
# wrong reading away from being a switch. `mints` names the fields of the op's own act by
# which the thing it brings into existence is IDENTIFIED — the account by its `account_id`,
# the space by its `name`, the namespace node by its `inode`. The test for a member is a
# sentence true whether or not any code reads the field: "this act founds a thing, and that
# thing is thereafter known by THIS". An op that acts on something an earlier record founded
# REFERENCES an identity and declares nothing; an op that supersedes under an identity it
# SHARES ON PURPOSE (an amendment, a revoke, a close) declares nothing either, because
# sharing is the point there and the declaration would be a false sentence.
#
# WHY THE DECLARATION IS NEEDED AT ALL, rather than derived. `FILE-CHOWN` records an absent
# `uid` as absent, which is honest — the chown changed no owner. `FILE-MKDIR` recording an
# absent `inode` is NOT honest: the inode is the key the namespace fold stores the node
# under, so every unstamped mkdir landed on the single key None and distinct directories
# became one node. The difference between "absent is honest" and "absent merges two things"
# is not visible in the definition's shape — it is a fact only the op knows, exactly as
# MINTED_ROUTERS' required-or-defaulted distinction is. So the op says it, and the guard
# holds it to what it said.
#
# THE GUARD IS THE DELIVERABLE AND THE MEMBERS ARE ITS INSTANCES. Adding the two missing
# defaults would have fixed two ops and left the class: the next minting op arrives with no
# derivation and nothing refuses it. Refused at DEFINITION time, at all three doors, an op
# that declares a mint it cannot derive cannot be loaded, created or amended into existence.
#
# THE HONEST CAP, stated where it will be read rather than in a log entry: this guard reaches
# what an op DECLARES. An op that mints a payload-borne identity and declares nothing is
# invisible to it, because nothing in a definition says which payload field a fold will use
# as a key. Closing that needs the FOLDS to declare what they key on — a structural question
# about the read side, RAISED by EP-28I and never built inside it. The object-borne half is
# narrower and safer by construction: every shipped op's `object_param` names a required or
# defaulted parameter and every `object_derive` template's fields do too (measured, 72 of 72),
# so no object can arrive absent today — but nothing yet REFUSES one that could, and that
# guard is raised beside this one rather than smuggled in under it.
MINTS = "mints"

# WHERE A MINTED IDENTITY COMES FROM WHEN NO FIELD OF THE ACT CARRIES IT (EP-28S).
#
# `mints` answers WHICH FIELD names the thing an act founds. This answers a question `mints`
# cannot: what if NO field should. The two are alternatives and never companions, which is
# the refusal below.
#
# THE DEFECT THAT FORCED IT, and it is a hole in `_mint_is_derivable` rather than in any
# op. That function asks whether a declared field VARIES BETWEEN TWO SIMULTANEOUS ACTS. It
# never asks whether the field's value is unique OVER THE RECORD'S WHOLE HISTORY, and for a
# reusable name those are different questions: `$path` varies per act and is still handed
# back the moment a rename or an unlink frees it, so two births separated in time derive one
# identity and the fold binds one node for two files. Measured on the shipped founding: a
# create, a rename away, a re-create of the vacated name — two lawful acts, ONE node, `nlink`
# reporting two files nobody linked, and a chmod addressed to one name changing the other.
#
# WHY A RECORD COORDINATE IS THE ANSWER AND NOT A BETTER FIELD. Every candidate field is
# CONTENT, and content repeats; the one thing about an act that cannot repeat is WHERE IT
# SITS IN THE RECORD. The store mints `seq` inside its own write lock, one position per
# record, never reissued (`store.py:810`) — so the map from birth act to identity is
# injective BY CONSTRUCTION, with no digest and no birthday bound under it.
#
# AND IT IS A RETURN RATHER THAN AN INVENTION. The FUSE port identified nodes by ALLOCATION
# ORDER — a private counter — and a counter cannot collide; that regime was sound and was
# replaced class-wide at 1.14.0 by `param_defaults {"inode": "$path"}`, which is not. This
# restores allocation order and takes its source from the record instead of from a counter
# that dies with the process while the records citing it do not.
#
# THE ENGINE LEARNS NO VOCABULARY HERE. `record_coordinate` names a property of the RECORD,
# which this module already holds; it names no subsystem, no field and no filesystem.
MINTS_FROM = "mints_from"
RECORD_COORDINATE = "record_coordinate"
MINT_SOURCES = (RECORD_COORDINATE,)


def _param_is_supplied(d, param, seen=frozenset()):
    """Is this PARAMETER guaranteed to carry a value by the time the record is built?

    The three ways are read out of `_interpreter` rather than listed from memory: the gate
    refuses a call missing a `required` parameter, `param_defaults` fills an absent key
    before the checks run, and a default spelled `$other` takes another parameter's value —
    so it is supplied exactly when that other one is. A `$` chain that LOOPS fills nothing at
    run time and is reported as unsupplied, which also stops this walk recursing forever."""
    if param in seen:
        return False
    if (d.get("params") or {}).get(param) == "required":
        return True
    defaults = d.get("param_defaults") or {}
    if param not in defaults:
        return False
    dv = defaults[param]
    if dv == "$actor":
        return True
    if isinstance(dv, str) and dv.startswith("$"):
        return _param_is_supplied(d, dv[1:], seen | {param})
    return dv not in (None, "")


def _param_varies_per_act(d, param, seen=frozenset()):
    """Does this PARAMETER's value distinguish one act from another?

    Stronger than being supplied, and it is the property an IDENTITY needs. A required
    parameter varies: the caller states it per act. A `$other` default varies exactly when
    the parameter it points at does. A CONSTANT does not — every unstamped act would share
    one identity, which is the collapse this clause exists to close wearing a value instead
    of None. `$actor` does not either: two acts by one actor would collide."""
    if param in seen:
        return False
    if (d.get("params") or {}).get(param) == "required":
        return True
    defaults = d.get("param_defaults") or {}
    if param not in defaults:
        return False
    dv = defaults[param]
    if isinstance(dv, str) and dv.startswith("$") and dv != "$actor":
        return _param_varies_per_act(d, dv[1:], seen | {param})
    return False


def _mint_is_derivable(d, field):
    """(ok, why-not) for ONE declared minted identity, walked back to where its value comes
    from. The three sources are the interpreter's own: a `payload_derive` template over
    resolved parameters, a `payload_derive` copy of one, or a parameter that reaches the
    payload. Anything else means the field is never written at all."""
    derived = (d.get("payload_derive") or {}).get(field)
    if derived is not None:
        if "tpl" in derived:
            fields = re.findall(r"\{(\w+)\}", derived["tpl"])
            if not fields:
                return False, ("is derived from a template naming no parameter, so it is "
                               "the same for every act")
            missing = [f for f in fields if not _param_is_supplied(d, f)]
            if missing:
                return False, ('is derived from "%s", which can arrive absent' % missing[0])
            if not any(_param_varies_per_act(d, f) for f in fields):
                return False, "is derived only from values that are the same for every act"
            return True, None
        if "copy" in derived:
            src = derived["copy"]
            if not _param_is_supplied(d, src):
                return False, ('copies "%s", which can arrive absent' % src)
            if not _param_varies_per_act(d, src):
                return False, ('copies "%s", which is the same for every act' % src)
            return True, None
        return False, "declares a derivation this interpreter cannot read"
    written = d.get("payload_from") or list((d.get("params") or {}).keys())
    known = set(d.get("params") or {}) | set(d.get("param_defaults") or {})
    if field not in written and field not in known:
        return False, "names a field this operation never writes"
    if not _param_is_supplied(d, field):
        return False, "can arrive absent, so two acts would share one identity"
    if not _param_varies_per_act(d, field):
        return False, "is the same for every act, so two acts would share one identity"
    return True, None


def _require_derivable_mints(gate, opname, actor, d):
    """THE CLAUSE THIS PASS EXISTS FOR, and the leash the declaration arrives with in the
    same round it does (design-soul §2).

    Two refusals and they are different things. A malformed declaration is a sentence nobody
    wrote — it would read as no declaration at all and the op would carry a false statement
    about itself with nothing going red, which is how an unknown `act_kind` would have
    behaved and why that one is refused too. And a declared mint the definition cannot
    DERIVE is the defect itself: the op says it founds a thing identified by a field, and
    that field can arrive absent or is a constant, so two acts collide.

    TWO MORE, ON `mints_from`, AND THEY ARRIVE IN THE SAME ROUND AS ITS READER (EP-28S).
    An unknown SOURCE is the same shape as an unknown `act_kind`: a sentence nobody wrote,
    which would read as no declaration at all while the founding carried a false statement
    about the op. And declaring BOTH is the one that matters — `mints` says a field of the
    act names the thing it founds, `mints_from` says no field does and the act's own
    position in the record names it. **An operation that declares two sources for one
    identity has declared none**, and it would leave every reader to guess which sentence
    won. The combination is refused so the contradiction is unrepresentable rather than
    merely unlikely."""
    source = d.get(MINTS_FROM)
    if source is not None:
        if source not in MINT_SOURCES:
            gate.refuse(actor, opname, "AR-2",
                        '"mints_from" says the identity this act founds comes from %r, which '
                        "is not a source this system knows — the vocabulary is: %s"
                        % (source, ", ".join(MINT_SOURCES)))
        if d.get(MINTS) is not None:
            gate.refuse(actor, opname, "AR-2",
                        'this operation declares BOTH "mints" and "mints_from" — one says a '
                        "field of the act names what it founds and the other says no field "
                        "does, so an operation declaring both has declared no identity source "
                        "at all and every reader of it would have to guess")
    decl = d.get(MINTS)
    if decl is None:
        return
    if (not isinstance(decl, (list, tuple)) or isinstance(decl, str)
            or not all(isinstance(f, str) and f for f in decl)):
        gate.refuse(actor, opname, "AR-2",
                    '"mints" must be a list of field names — it says what this act founds is '
                    "identified by, and anything else is a sentence nobody wrote")
    if not decl:
        gate.refuse(actor, opname, "AR-2",
                    '"mints" names no field — an operation that declares it mints an identity '
                    "and does not say which field carries it has declared nothing")
    for field in decl:
        ok, why = _mint_is_derivable(d, field)
        if not ok:
            gate.refuse(actor, opname, "AR-2",
                        'this operation declares it mints an identity carried in "%s", and '
                        'that field %s — a minted identity DERIVES from the act\'s own '
                        "distinguishing content, declared here, or the operation does not "
                        "exist" % (field, why))


def _require_wellformed_binding(gate, opname, actor, d, peers):
    """THE LEASH THE DECLARATION ARRIVES WITH, IN THE SAME ROUND IT DOES (design-soul §2), and
    at DEFINITION time — the way an unknown check kind is already refused, because a policy
    that does not exist should not wait for a caller to discover it.

    FIVE REFUSALS ON THE DECLARATION, and each closes a different way a row could read as law
    and do nothing. A row naming no key checks nothing. A row naming a parameter the op does
    not take reads an absent value on every act. A row naming a field the record never writes
    is invisible to the fold, which reads PAYLOADS while the check reads PARAMS — a divergence
    no reader would see, because the two names agree in every shipped op today by coincidence
    rather than by rule. An unknown `require` or `effect` is a policy nobody wrote and would
    read as silence. And a row with neither is decoration.

    AND ONE REFUSAL ON ITS ABSENCE, which is the guard that closes the CLASS rather than its
    members (ADDENDUM C's lesson, EP-28I's precedent). The live set is folded from these
    declarations, so an op that moves a name WITHOUT declaring it makes every later existence
    check answer about a namespace it is not in — silently, and worse the longer it runs. The
    ops that must declare are found STRUCTURALLY and not from a list here: they are the ops
    citing the law that the declared checks themselves cite. Nothing in this module names a
    filesystem, and a future namespace op cannot omit what the installer refuses to load."""
    rows = [c for c in (d.get("checks") or []) if c.get("check") == BINDING]
    written = d.get("payload_from") or list((d.get("params") or {}).keys())
    for c in rows:
        key = c.get("key_param")
        if not key:
            gate.refuse(actor, opname, "AR-2",
                        'a "binding" check names no key_param — a check over no key checks '
                        "nothing and is unrecordable")
        if key not in (d.get("params") or {}) and key not in (d.get("param_defaults") or {}):
            gate.refuse(actor, opname, "AR-2",
                        'a "binding" check names key_param %r, which this operation does not '
                        "take — the check would read an absent value on every act" % key)
        if key not in written:
            gate.refuse(actor, opname, "AR-2",
                        'a "binding" check names key_param %r, which this operation never '
                        "writes to its record — the check reads a parameter and the fold reads "
                        "the payload, so a key that reaches one and not the other is a rule "
                        "nobody enforces" % key)
        if c.get("require") is not None and c["require"] not in BINDING_REQUIREMENTS:
            gate.refuse(actor, opname, "AR-2",
                        'a "binding" check requires %r, which is not a state a key can be in — '
                        "the vocabulary is: %s" % (c["require"], ", ".join(BINDING_REQUIREMENTS)))
        if c.get("effect") is not None and c["effect"] not in BINDING_EFFECTS:
            gate.refuse(actor, opname, "AR-2",
                        'a "binding" check declares the effect %r, which is not something an '
                        "act can do to a key — the vocabulary is: %s"
                        % (c["effect"], ", ".join(BINDING_EFFECTS)))
        if c.get("require") is None and c.get("effect") is None:
            gate.refuse(actor, opname, "AR-2",
                        'a "binding" check that requires nothing and does nothing is '
                        "decoration — it would read as law and change no outcome")
    if rows or not peers:
        return
    governed = {c.get("cite") for peer in peers.values()
                for c in (peer.get("checks") or [])
                if c.get("check") == BINDING and c.get("cite")}
    if d.get("law_cited") in governed:
        gate.refuse(actor, opname, "AR-2",
                    "this operation cites %r, the law whose acts bind and unbind names, and "
                    "declares no binding — the live set is folded from these declarations, so "
                    "an act that moves a name without saying so makes every later existence "
                    "check answer about a namespace it is not in" % d.get("law_cited"))


def _require_wellformed_key_of(gate, opname, actor, d):
    """THE LEASH `key_of` ARRIVES WITH, IN THE SAME ROUND IT DOES (design-soul §2), and at
    DEFINITION time — one home for one vocabulary, walked over EVERY check row rather than
    repeated inside each kind's own guard, because a declaration spelled twice is two
    declarations (ADDENDUM I.2).

    THREE REFUSALS. An unknown derivation is a question nobody wrote and would read as
    silence — as "the key the parameter carries" — so a misspelt `containr` would sit in the
    founding asking a different question from the one its author wrote, with nothing ever
    going red. A `key_of` on a row that asks nothing is decoration. And a `key_of` on a row
    that carries an EFFECT is the one combination that is not merely useless but false: an
    act binds the name it acts on and never the name that contains it, so a create declaring
    both would be saying it takes its own parent."""
    for c in (d.get("checks") or []):
        of = c.get(KEY_OF)
        if of is None:
            continue
        if of not in KEY_DERIVATIONS:
            gate.refuse(actor, opname, "AR-2",
                        'a check declares "%s": %r, which is not a key this law can derive — '
                        "the whole vocabulary is: %s"
                        % (KEY_OF, of, ", ".join(KEY_DERIVATIONS)))
        if c.get("check") not in (BINDING, KIND, CONTAINS):
            gate.refuse(actor, opname, "AR-2",
                        'a %r check declares "%s" — only a check that asks about a KEY can ask '
                        "about a derived one" % (c.get("check"), KEY_OF))
        if c.get("effect") is not None:
            gate.refuse(actor, opname, "AR-2",
                        'a check declares "%s": %r AND the effect %r — an act moves the name it '
                        "acts on and never the name that contains it, so this row would say the "
                        "act takes its own container" % (KEY_OF, of, c["effect"]))


def _require_wellformed_contains(gate, opname, actor, d):
    """THE LEASH THE DECLARATION ARRIVES WITH, IN THE SAME ROUND IT DOES (design-soul §2), and
    at DEFINITION time — `binding`'s and `kind`'s precedent, one law over.

    FIVE REFUSALS, each closing a different way a row could read as law and change no outcome.
    A row naming no key asks about nothing. A row naming a parameter the op does not take
    reads an absent value on every act. A row naming a field the record never writes is
    invisible to the fold, which reads PAYLOADS while the check reads PARAMS. A row requiring
    nothing is decoration. And an unknown requirement is a policy nobody wrote, which would
    read as silence.

    NO ABSENCE CLAUSE AND NO PRIOR-BOUND CLAUSE, both derived rather than skipped: containment
    is computed from the live key set that `binding`'s own absence clause already forces every
    act under this law to declare into, and an unbound key holds nothing, which is a true
    answer rather than a question about a name that need not be there."""
    written = d.get("payload_from") or list((d.get("params") or {}).keys())
    known = set(d.get("params") or {}) | set(d.get("param_defaults") or {})
    for c in (d.get("checks") or []):
        if c.get("check") != CONTAINS:
            continue
        key = c.get("key_param")
        if not key:
            gate.refuse(actor, opname, "AR-2",
                        'a "contains" check names no key_param — a question about what no key '
                        "holds asks nothing and is unrecordable")
        if key not in known:
            gate.refuse(actor, opname, "AR-2",
                        'a "contains" check names key_param %r, which this operation does not '
                        "take — the check would read an absent value on every act" % key)
        if key not in written:
            gate.refuse(actor, opname, "AR-2",
                        'a "contains" check names key_param %r, which this operation never '
                        "writes to its record — the check reads a parameter and the fold reads "
                        "the payload, so a key that reaches one and not the other is a rule "
                        "nobody enforces" % key)
        require = c.get("require")
        if require is None:
            gate.refuse(actor, opname, "AR-2",
                        'a "contains" check that requires nothing is decoration — it would read '
                        "as law and change no outcome")
        if require not in CONTAINS_REQUIREMENTS:
            gate.refuse(actor, opname, "AR-2",
                        'a "contains" check requires %r, which is not a state a container can '
                        "be in — the vocabulary is: %s"
                        % (require, ", ".join(CONTAINS_REQUIREMENTS)))


def _require_wellformed_kind(gate, opname, actor, d, peers):
    """THE LEASH THE DECLARATION ARRIVES WITH, IN THE SAME ROUND IT DOES (design-soul §2), and
    at DEFINITION time — the way an unknown check kind is already refused, because a policy
    that does not exist should not wait for a caller to discover it.

    SEVEN REFUSALS ON THE CLASS CHECK, and each closes a different way a row could read as law
    and change no outcome. A row naming no key checks nothing. A row naming a parameter the op
    does not take reads an absent value on every act. A row naming a field the record never
    writes is invisible to the fold, which reads PAYLOADS while the check reads PARAMS. A row
    asking nothing is decoration, and a row asking two things is two rules wearing one row —
    an author would read it as one and the interpreter runs it as both. An unknown class value
    is unrecordable rather than merely unknown, because the classes are the LAW's own words and
    a row may not ask about an absence. And a class question over a key the op does not require
    BOUND answers about a name that need not be there — with its order held too, because an
    unbound key has no class and declaration order is the answer order.

    FIVE ON THE GIFT. A `binds_kind` on a row that binds nothing is decoration; a gift naming
    none or more than one source is a sentence nobody wrote; and a source naming a parameter
    the op does not take, or does not write, gives a class the fold can never read.

    AND ONE ON ITS ABSENCE, which is the clause that closes the CLASS rather than its members
    (EP-28K's precedent, one law over). The ops that must declare are found STRUCTURALLY: they
    are the ops citing the law that some peer's class check itself cites. Nothing here names a
    filesystem, and a future op that binds a name under a class-governed law cannot omit what
    the installer refuses to load."""
    checks = d.get("checks") or []
    written = d.get("payload_from") or list((d.get("params") or {}).keys())
    known = set(d.get("params") or {}) | set(d.get("param_defaults") or {})

    def _refuse(msg):
        gate.refuse(actor, opname, "AR-2", msg)

    for i, c in enumerate(checks):
        if c.get("check") != KIND:
            continue
        key = c.get("key_param")
        if not key:
            _refuse('a "kind" check names no key_param — a question about no key asks nothing '
                    "and is unrecordable")
        if key not in known:
            _refuse('a "kind" check names key_param %r, which this operation does not take — '
                    "the check would read an absent value on every act" % key)
        if key not in written:
            _refuse('a "kind" check names key_param %r, which this operation never writes to '
                    "its record — the check reads a parameter and the fold reads the payload, "
                    "so a key that reaches one and not the other is a rule nobody enforces"
                    % key)
        want, forbid = c.get("require"), c.get("forbid")
        if want is None and forbid is None:
            _refuse('a "kind" check that requires nothing and forbids nothing is decoration — '
                    "it would read as law and change no outcome")
        if want is not None and forbid is not None:
            _refuse('a "kind" check may not both require and forbid — that is two rules in one '
                    "row, and a reader who takes it for one has read half the law")
        for value in (want, forbid):
            if value is not None and (not isinstance(value, str) or not value):
                _refuse('a "kind" check names %r as a class — a class is the law\'s own word '
                        "for what a key names, and an empty one is unrecordable" % (value,))
        # THE MATCH IS ON THE KEY THE ROW ASKS ABOUT, NOT ON THE PARAMETER (EP-28N AMENDMENT
        # 1). A create requires its own name UNBOUND and its container BOUND, over one
        # parameter — so a match on `key_param` alone would read the unbound row as the
        # class question's prior bound row, and admit a class question over a name the act
        # requires not to be there. The pair (key_param, key_of) is the key.
        bound_at = [j for j, b in enumerate(checks)
                    if b.get("check") == BINDING and b.get("key_param") == key
                    and b.get(KEY_OF) == c.get(KEY_OF) and b.get("require") == BOUND]
        if not bound_at:
            _refuse('a "kind" check asks what %r names while this operation does not require '
                    "that key to be bound — an unbound key names nothing, so the question "
                    "would be answered about a name that need not be there"
                    % (key if not c.get(KEY_OF) else "the %s of %s" % (c[KEY_OF], key)))
        elif bound_at[0] > i:
            _refuse('a "kind" check over %r is answered BEFORE this operation requires that '
                    "key to be bound — declaration order is the answer order, so the class "
                    "question would report about a name that is not there" % key)

    for c in checks:
        gift = c.get(BINDS_KIND)
        if gift is None:
            continue
        if not (c.get("check") == BINDING and c.get("effect") == BIND):
            _refuse('"%s" sits on a check that binds no key — a class can only be given to a '
                    "key an act takes, so the words would read as law and give nothing"
                    % BINDS_KIND)
        if not isinstance(gift, Mapping) or len(
                [k for k in gift if k in KIND_SOURCES]) != 1 or len(gift) != 1:
            _refuse('"%s" must name exactly one source — the whole grammar is: %s'
                    % (BINDS_KIND, ", ".join(KIND_SOURCES)))
        source, value = next(iter(gift.items()))
        if source in ("param", "from_key"):
            if value not in known:
                _refuse('"%s" takes the class from %r, which this operation does not take'
                        % (BINDS_KIND, value))
            if value not in written:
                _refuse('"%s" takes the class from %r, which this operation never writes to '
                        "its record — the fold reads the payload, so the class would be read "
                        "from a field that is not there" % (BINDS_KIND, value))
        elif not isinstance(value, str) or not value:
            _refuse('"%s" declares %r as the class this act gives — an empty class is '
                    "unrecordable" % (BINDS_KIND, value))

    if not peers:
        return
    governed = {c.get("cite") for peer in peers.values()
                for c in (peer.get("checks") or [])
                if c.get("check") == KIND and c.get("cite")}
    if d.get("law_cited") not in governed:
        return
    for c in checks:
        if c.get("check") == BINDING and c.get("effect") == BIND and not c.get(BINDS_KIND):
            _refuse("this operation cites %r, the law whose acts are asked what their names "
                    "name, and binds %r without saying what class it gives it — the classes "
                    "are folded from these declarations, so a bind that says nothing leaves "
                    "the name classless and every later question about it answers about a "
                    "namespace it is not in" % (d.get("law_cited"), c.get("key_param")))


def _require_wellformed_prior_value(gate, opname, actor, d):
    """THE LEASH THIS DECLARATION ARRIVES WITH, IN THE SAME ROUND IT DOES (design-soul §2), and
    at DEFINITION time — the way an unknown check kind is already refused, because a policy that
    does not exist should not wait for a caller to discover it.

    SIX REFUSALS, and each closes a different way a row could read as law and change no outcome.
    A row naming no `action` searches nothing. A row naming no `field` or no `param` cannot
    locate the record its question is about — and a `param` the op does not take reads an absent
    value on every act, so the row would refuse every call for a reason no author wrote. A row
    naming no `value_field` asks about no field. A row asking nothing is decoration, and an
    unknown requirement is a policy nobody wrote, which would read as silence.

    NO PAYLOAD-WRITE CLAUSE, and it is derived rather than skipped — the one place this kind's
    leash differs from `binding`'s and `contains`'s, so the difference is stated instead of
    looking like an omission. Those kinds ask about a KEY THIS ACT MOVES, so a key reaching the
    check and not the record is a rule nobody enforces. This kind asks about A PRIOR RECORD THE
    ACT CITES: the subject is that record's field, which this act never writes and could not.
    What the act must write is its own citation, and `payload_from` carrying the locating param
    is the op author's business under C7's explicit-form rule rather than this kind's."""
    known = set(d.get("params") or {}) | set(d.get("param_defaults") or {})
    for c in (d.get("checks") or []):
        if c.get("check") != PRIOR_VALUE:
            continue
        for key, why in (("action", "a %r check names no action — a question about no prior "
                                    "record searches nothing"),
                         ("field", "a %r check names no field — the record it asks about "
                                   "cannot be located"),
                         ("param", "a %r check names no param — nothing carries the name of "
                                   "the record it asks about"),
                         ("value_field", "a %r check names no value_field — a question about "
                                         "no field of that record asks nothing")):
            if not c.get(key):
                gate.refuse(actor, opname, "AR-2", why % PRIOR_VALUE)
        if c.get("param") not in known:
            gate.refuse(actor, opname, "AR-2",
                        'a "%s" check names param %r, which this operation does not take — the '
                        "check would locate its record by an absent value on every act"
                        % (PRIOR_VALUE, c.get("param")))
        require = c.get("require")
        if require is None:
            gate.refuse(actor, opname, "AR-2",
                        'a "%s" check that requires nothing is decoration — it would read as '
                        "law and change no outcome" % PRIOR_VALUE)
        if require not in PRIOR_VALUE_REQUIREMENTS:
            gate.refuse(actor, opname, "AR-2",
                        'a "%s" check requires %r, which is not a state a declared value can '
                        "be in — the vocabulary is: %s"
                        % (PRIOR_VALUE, require, ", ".join(PRIOR_VALUE_REQUIREMENTS)))


def _require_wellformed_bound_field(gate, opname, actor, d):
    """THE LEASH THIS DECLARATION ARRIVES WITH, IN THE SAME ROUND IT DOES (design-soul §2), at
    DEFINITION time and at all three doors — `prior_value`'s leash carried forward, because a
    policy that does not exist should not wait for a caller to discover it.

    SEVEN REFUSALS, each closing a different way a row could read as law and change no outcome.
    A row naming no `action` searches nothing. A row naming no `field` or no `key_param` cannot
    BIND the record its question is about, which is the one thing this kind exists to do. A row
    naming no `value_field` asks about no field of it. A row naming no `param` has nothing to
    compare that field against, so it would assert a relation between one thing.

    AND BOTH PARAMETERS ARE CHECKED AGAINST THE OP'S OWN, not one of them. A `param` the op does
    not take reads an absent value on every act, so the row refuses every call for a reason no
    author wrote; a `key_param` the op does not take binds by an absent value on every act, so
    the row's record is never found and the whole question collapses into `when_unbound` —
    silently, and reading as law the entire time. THE SECOND CLAUSE IS THE ONE A COPY OF
    `prior_value`'s LEASH WOULD HAVE MISSED, since that kind has only one parameter to lose.

    AN UNKNOWN `when_unbound` IS REFUSED RATHER THAN DEFAULTED, which is the whole reason the key
    is closed: a misspelt `permitt` that fell back to silence would read as the strict policy and
    behave as the strict policy, so the author's intended weakening would vanish with nothing
    going red — or, written the other way, a misspelt strict policy would fall open. Silence is
    the strict policy; a WRONG WORD is not silence and never resolves to it."""
    known = set(d.get("params") or {}) | set(d.get("param_defaults") or {})
    for c in (d.get("checks") or []):
        if c.get("check") != BOUND_FIELD:
            continue
        for key, why in (("action", "a %r check names no action — a question about no prior "
                                    "record searches nothing"),
                         ("field", "a %r check names no field — the record it binds cannot be "
                                   "located"),
                         ("key_param", "a %r check names no key_param — nothing carries the "
                                       "name of the record it binds"),
                         ("value_field", "a %r check names no value_field — a question about "
                                         "no field of that record asks nothing"),
                         ("param", "a %r check names no param — the field it reads is compared "
                                   "against nothing, which asserts a relation between one thing")):
            if not c.get(key):
                gate.refuse(actor, opname, "AR-2", why % BOUND_FIELD)
        for key in ("key_param", "param"):
            if c.get(key) not in known:
                gate.refuse(actor, opname, "AR-2",
                            'a "%s" check names %s %r, which this operation does not take — the '
                            "check would read an absent value on every act"
                            % (BOUND_FIELD, key, c.get(key)))
        if c.get(WHEN_UNBOUND) is not None and c.get(WHEN_UNBOUND) not in UNBOUND_POLICIES:
            gate.refuse(actor, opname, "AR-2",
                        'a "%s" check declares %s %r, which is not a policy an unbound key can '
                        "have — the vocabulary is: %s (and silence means %s)"
                        % (BOUND_FIELD, WHEN_UNBOUND, c.get(WHEN_UNBOUND),
                           ", ".join(UNBOUND_POLICIES), UNBOUND_REFUSE))


def validate_definition_shape(gate, doorname, actor, name, d, peers=None):
    """THE DEFINITION-SHAPE VOCABULARY, IN ONE PLACE, RUN AT ALL THREE DOORS (EP-27B ADDENDUM 2
    W6c; design/36 ADDENDUM I.3).

    `peers` is the definitions this one sits among — the pack at the founding door, the live
    registry at the two runtime doors. It arrived with EP-28K's absence clause, which is the
    first clause whose question is about a definition's PLACE among the others rather than
    about its own shape, and it defaults to None so a caller with nothing to compare against
    (a shape check in isolation) runs every other clause unchanged.

    An op definition reaches the live registry three ways: `CREATE-OP`, `AMEND-OP`, and the
    founding installer, which appends every pack record directly. The first two carried this
    vocabulary and the third validated nothing — so every one of the live definitions, and every
    definition a later campaign seeds, entered through the door with no check on it. That is the
    enforcement-at-the-chokepoint theorem's own lesson arriving about SHAPE instead of about
    authority: a guard at two of three doors guards nothing.

    Founding-only legitimacy is why the third door looked exempt and is not. Nothing can
    AUTHORIZE the founding — it enters at genesis and its legitimacy is live-under-it-or-exit —
    and that exempts it from authority checks and from nothing else. A record that cannot be
    interpreted is not made interpretable by being at genesis.

    `gate` is anything with the gate's `refuse(actor, op, rule, message)`: the gate itself at the
    two runtime doors, where a refusal is recorded and raised; the installer's own door object at
    the founding, where there is no store to record into yet and the whole founding is refused
    instead. One validation, three doors, one vocabulary — not a copy of it per door."""
    if not d.get("law_cited"):
        gate.refuse(actor, doorname, "ROOT-NEG-5",
                    "an operation whose decisions cite no law is unrecordable")
    for c in d.get("checks", []):
        if c.get("check") not in OP_CHECKS:
            gate.refuse(actor, doorname, "AR-2",
                        f'unknown check "{c.get("check")}" — the check vocabulary is: '
                        + ", ".join(OP_CHECKS))
        _require_non_empty_cite(gate, doorname, actor, c)
    _require_wellformed_routers(gate, doorname, actor, d)
    _require_wellformed_act_kind(gate, doorname, actor, d)
    _require_wellformed_record_stream(gate, doorname, actor, d)
    _require_derivable_mints(gate, doorname, actor, d)
    _require_wellformed_key_of(gate, doorname, actor, d)
    _require_wellformed_check_rows(gate, doorname, actor, d, peers)
    if d.get("executor") is not None:
        crossing.validate_station(gate, actor, doorname, name, d)   # T-CONTEXT-PINNED


def _require_wellformed_check_rows(gate, doorname, actor, d, peers=None):
    """THE PER-KIND LEASHES, WITH ONE HOME (EP-30-K2).

    Extracted from `validate_definition_shape` with NO change to what any of them does, for one
    reason: `every_member` carries an INNER declaration, and an inner row that never met its own
    kind's leash would be a check reading as law with its malformed-declaration door standing
    open — the very door each of these functions exists to shut. The quantifier's guard hands the
    inner row BACK TO THIS FUNCTION on a synthetic definition, so an inner `value_domain` with an
    empty domain, or an inner `bound_field` naming no `action`, refuses at DEFINITION time exactly
    as a top-level one does, and the vocabulary of leashes is spelled ONCE.

    A LIST OF LEASH CALLS SPELLED TWICE IS TWO LISTS, and the second one silently stops growing —
    the divergence class this module keeps paying for and names at REQ_BINDING above."""
    _require_wellformed_binding(gate, doorname, actor, d, peers)
    _require_wellformed_kind(gate, doorname, actor, d, peers)
    _require_wellformed_contains(gate, doorname, actor, d)
    _require_wellformed_prior_value(gate, doorname, actor, d)
    _require_wellformed_bound_field(gate, doorname, actor, d)
    _require_wellformed_value_domain(gate, doorname, actor, d)
    _require_wellformed_live_slot(gate, doorname, actor, d)
    _require_wellformed_every_member(gate, doorname, actor, d, peers)


def _require_wellformed_every_member(gate, opname, actor, d, peers=None):
    """A QUANTIFIER THAT CANNOT NAME ITS SET, ITS MEMBER, ITS QUESTION OR ITS EMPTY CASE IS NOT A
    CHECK (EP-30-K2). Definition time, all three doors, `bound_field`'s leash carried forward.

    THE MANDATORY `on_empty` IS THE ONE CLAUSE THIS KIND WOULD BE UNSAFE WITHOUT, and it is
    mandatory rather than defaulted because BOTH answers are real laws (see ON_EMPTY above). A
    *must* with no refusal behind it is a written rule, and a rule a seat can breach by accident
    is not a control — so the omission refuses HERE, before any act, rather than being discovered
    when a caller supplies an empty list and the law quietly agrees with them.

    THE MEMBER NAME MAY NOT SHADOW A REAL PARAMETER. Each member is bound under `member_param`
    for the inner row to read; if that name were also an op parameter, the quantifier would
    OVERWRITE a value the caller supplied and the inner row would silently ask about the wrong
    thing on every act — a check reading as law and measuring something nobody declared.

    NO NESTING, AND IT IS REFUSED RATHER THAN LEFT UNDEFINED. A quantifier over a quantifier needs
    a parameter whose members are themselves many-valued, and nothing in the pack declares one, so
    the composition has no subject to be right about. Refused at the door with its reason, closed
    like every vocabulary in this module — and REFUSING it hardens nothing, because lifting the
    refusal is one line the day a nested parameter exists.

    THE INNER ROW MEETS ITS OWN KIND'S LEASH, through `_require_wellformed_check_rows` on a
    synthetic definition carrying `member_param` as a parameter — so the inner is validated by the
    SAME functions a top-level row is, never by a copy of them."""
    known = set(d.get("params") or {}) | set(d.get("param_defaults") or {})
    for c in (d.get("checks") or []):
        if c.get("check") != EVERY_MEMBER:
            continue
        param, member = c.get("param"), c.get(MEMBER_PARAM)
        if not isinstance(param, str) or not param:
            gate.refuse(actor, opname, "AR-2",
                        'an "%s" check names no param — a question about the members of nothing '
                        "asks nothing" % EVERY_MEMBER)
        if param not in known:
            gate.refuse(actor, opname, "AR-2",
                        'an "%s" check names param %r, which this operation does not take — the '
                        "check would read an absent value on every act" % (EVERY_MEMBER, param))
        if not isinstance(member, str) or not member:
            gate.refuse(actor, opname, "AR-2",
                        'an "%s" check names no %s — nothing carries the member the inner '
                        "question is asked about" % (EVERY_MEMBER, MEMBER_PARAM))
        if member in known:
            gate.refuse(actor, opname, "AR-2",
                        'an "%s" check binds its member to %r, which this operation already takes '
                        "— the member would overwrite a value the caller supplied and the inner "
                        "question would measure the wrong thing on every act"
                        % (EVERY_MEMBER, member))
        if c.get(ON_EMPTY) not in ON_EMPTY_ANSWERS:
            gate.refuse(actor, opname, "AR-2",
                        'an "%s" check on %r declares %s %r — the empty set has no default here '
                        "because BOTH answers are real laws: every member of nothing PASSES "
                        "vacuously, which is a fail-open dressed as logic, and refusing every "
                        "empty set makes a law over an optional list refuse acts that simply did "
                        "not use it. The law states which: %s"
                        % (EVERY_MEMBER, param, ON_EMPTY, c.get(ON_EMPTY),
                           ", ".join(ON_EMPTY_ANSWERS)))
        inner = c.get(INNER)
        if not isinstance(inner, Mapping) or not inner.get("check"):
            gate.refuse(actor, opname, "AR-2",
                        'an "%s" check on %r declares no %s question — a quantifier with nothing '
                        "to quantify asks every member nothing" % (EVERY_MEMBER, param, INNER))
        if inner.get("check") == EVERY_MEMBER:
            gate.refuse(actor, opname, "AR-2",
                        'an "%s" check may not quantify another — a quantifier over a quantifier '
                        "needs a parameter whose members are themselves many-valued, and no "
                        "operation declares one" % EVERY_MEMBER)
        if inner.get("check") not in OP_CHECKS:
            gate.refuse(actor, opname, "AR-2",
                        'unknown check "%s" inside an "%s" — the check vocabulary is: %s'
                        % (inner.get("check"), EVERY_MEMBER, ", ".join(OP_CHECKS)))
        _require_non_empty_cite(gate, opname, actor, inner)
        _require_wellformed_check_rows(
            gate, opname, actor,
            {"law_cited": d.get("law_cited"),
             "params": dict(d.get("params") or {}, **{member: "required"}),
             "param_defaults": d.get("param_defaults") or {},
             "checks": [inner]},
            peers)


def _require_non_empty_cite(gate, opname, actor, c):
    """W4/finding A4 (definition-time half): a check that DECLARES a cite must declare a non-empty one.
    A check whose `cite` key is present but empty (cite:null) drove the refusal path to record
    rule_cited=None and CRASH before appending — no record, no cite. Refuse the malformed declaration
    at op-definition time, the way an unknown check kind is already refused. (The use-time half is the
    `c.get("cite") or <default>` fallback at every interpreter refuse site — a check that OMITS cite
    keeps its default, so an op need not name a cite, but it may not name an empty one.)"""
    if "cite" in c and not c["cite"]:
        gate.refuse(actor, opname, "ROOT-NEG-5",
                    f'check "{c.get("check")}" cites no law — a check that cites nothing is unrecordable')


def _require_wellformed_value_domain(gate, opname, actor, d):
    """A DECLARED VALUE DOMAIN THAT DECLARES NOTHING IS A SENTENCE NOBODY WROTE (EP-30-C1).

    Same shape as the guards its neighbours arrive with, and here for their reason: a row naming
    no `param` asks about nothing, and a row whose `domain` is absent or empty admits EVERY value
    while looking like a restriction. That second one is the dangerous half — it would read as a
    check and behave as none, and the op would carry a false statement about itself with nothing
    going red. Refused at definition time, at all three doors."""
    for c in (d.get("checks") or []):
        if c.get("check") != "value_domain":
            continue
        if not isinstance(c.get("param"), str) or not c.get("param"):
            gate.refuse(actor, opname, "AR-2",
                        'a "value_domain" check names no param — a check over no parameter '
                        "checks nothing")
        # LIST OR TUPLE, because a recorded definition is frozen all the way down and a
        # re-validated declaration arrives in its frozen spelling. A `list`-only test would
        # refuse a definition the estate itself had already admitted.
        dom = c.get("domain")
        if not isinstance(dom, (list, tuple)) or not dom:
            gate.refuse(actor, opname, "AR-2",
                        'a "value_domain" check on %r declares no domain — a domain that is '
                        "absent or empty admits every value while reading as a restriction"
                        % (c.get("param"),))


def _require_wellformed_live_slot(gate, opname, actor, d):
    """A SLOT LAW THAT CANNOT NAME ITS SLOT IS UNENFORCEABLE (EP-30-C1).

    Four requirements, each because its absence makes the fold answer a different question than
    the one declared: no `open_action` or `close_action` and the live set cannot be computed at
    all; no `instance_param` and a closing act frees nothing, so the set only ever grows and the
    check becomes the lifetime quota this law exists to refuse; no `slot_params` and every act
    shares one slot, which would admit exactly one opening in the whole estate."""
    for c in (d.get("checks") or []):
        if c.get("check") != "live_slot":
            continue
        for field in ("open_action", "close_action", "instance_param"):
            if not isinstance(c.get(field), str) or not c.get(field):
                gate.refuse(actor, opname, "AR-2",
                            'a "live_slot" check declares no %s — the live set it reads cannot '
                            "be computed without one" % field)
        sp = c.get("slot_params")
        if (not isinstance(sp, (list, tuple)) or not sp
                or not all(isinstance(k, str) and k for k in sp)):
            gate.refuse(actor, opname, "AR-2",
                        'a "live_slot" check declares no slot_params — every act would share '
                        "one slot, admitting exactly one opening in the whole estate")


def _peer_definitions(views):
    """The live definitions a runtime door compares an arriving one against (EP-28K). The
    LIVE REGISTRY rather than the pack, because that is what the arriving definition will
    actually sit among: an op retired since the founding is no longer governing anything."""
    return {n: (v.get("definition") or {}) for n, v in views.op_definitions().items()}


def _definition_exists(gate, views, ref):
    """Does a definition_ref ('op:NAME' / 'view:NAME') point to a REAL registered definition?
    R29 (EP-13): `op:` resolves against the LIVE REGISTRY via `gate.has` — a truthful view of the
    registry that sees BOTH definition-born ops AND code-registered bootstrap ops (CREATE-INFO,
    GRANT-READ, …), which `op_definitions()` (definition-born only) cannot; the old fold-only lookup
    fail-CLOSED, refusing a term that links a live code op at use. `view:` stays the view fold."""
    if not ref or ":" not in ref:
        return False
    kind, name = ref.split(":", 1)
    if kind == "op":
        return gate.has(name)
    if kind == "view":
        return name in views.view_definitions()
    return False


def _consistency_check(gate, views, actor, opname, c, params):
    """The consistency check (EP-05 Phase B): a proposed rule may not contradict an ACTIVE
    EXCLUSIVE rule on the same policy_key with a different value — extracted verbatim from the
    retired `create_rule` handler so CREATE-RULE can be a definition. No policy_key -> nothing
    to conflict with. Refuses ROOT-NEG-6 (no activation of a contradicting rule)."""
    key = params.get(c["policy_key_param"])
    if key is None:
        return
    val = params.get(c["value_param"])
    for r in views.active_rules().values():
        if r.get("policy_key") == key and r.get("exclusive") and r.get("value") != val:
            rid = params.get(c.get("id_param", "rule_id"))
            gate.refuse(actor, opname, c.get("cite") or "ROOT-NEG-6",
                        f"proposed {rid} contradicts an active exclusive rule on '{key}'")


def _ceiling_check(gate, store, views, actor, opname, c, params):
    """The ceiling check (design 28 §5), derived to reproduce `memory._resident` EXACTLY.

    policy_value(key) vs an aggregate, refuse if aggregate + requested > policy. The
    aggregate is an ORDERED keyed fold over the whole record — NOT two by-action scans —
    so grant/evict/re-grant interleave correctly:
      - `aggregate_action` sets (OVERWRITES) the key's field for the scoped holder;
      - `removal_action` REMOVES the key, UNFILTERED by holder (an eviction carries no
        holder; it frees whatever region it names).
    A set-based `granted minus evicted` port silently under-counts a re-granted region and
    lets a holder exceed budget; a holder-filtered removal silently stops evictions freeing
    budget. Missing policy = None = unlimited (current behaviour). key-and-holder resolution
    matches the handler's `params.get("holder", actor)` — the caller already resolved it via
    param_defaults, so check and recorded payload agree."""
    holder = params.get(c["holder_param"])
    ceiling = views.policy_value(c["policy_key_prefix"] + str(holder))
    if ceiling is None:
        return  # no budget set -> unlimited
    agg = {}
    for e in store.all():
        a, pp = e["action"], (e.get("payload") or {})
        if a == c["aggregate_action"] and pp.get(c["holder_field"]) == holder:
            agg[pp.get(c["key_param"])] = pp.get(c["aggregate_field"], 0)
        elif a == c["removal_action"]:
            agg.pop(pp.get(c["key_param"]), None)
    used = sum(agg.values())
    requested = params.get(c["amount_param"], 0)
    if used + requested > ceiling:
        gate.refuse(actor, opname, c.get("cite") or "ROOT-NEG-1",
                    f"{opname}: {requested} exceeds budget for {holder} (used {used}, ceiling {ceiling})")


def _declared_keys(d):
    """The parameters ONE definition declares as KEYS, read from its own checks (EP-28O).

    `binding` and `kind` are the two check kinds that ask a question ABOUT A KEY, so the union
    of their `key_param` declarations IS the set of parameters whose values enter the law's key
    space. Read here rather than listed, for the same reason `binding_rows` and `kind_gifts` are
    read: this module must not learn that a parameter spelled `path` holds a path (I5). An op
    added next campaign that carries a key declares it, and is canonicalised for having done so.

    SORTED AND FROZEN AS A TUPLE because the caller holds it for the life of a registration: the
    declarations cannot change under a live definition (amending one is retire + create), so the
    walk happens once, at registration, and never on the gate's per-act path (K3)."""
    return tuple(sorted({c.get("key_param") for c in (d.get("checks") or [])
                         if c.get("check") in (BINDING, KIND) and c.get("key_param")}))


def _row_cite(c, d):
    """Which law governs the key ONE check row asks about (EP-28N AMENDMENT 1).

    A row that names its own citation carries it; a row that names none is governed by the
    OPERATION'S OWN law — the same fallback `_refuse_about_the_act` already applies to the
    refusal such a row raises, so the law that would be cited and the law whose key space is
    read are one law and not two."""
    return c.get("cite") or d.get("law_cited")


def _key_space(views, cite, as_of=None):
    """The key space the cited law declares, or {} (EP-28N AMENDMENT 1).

    LAW-DATA, read through the same cached view every other law read takes. `{}` is a
    complete answer and not a failure: a law that declares no key space has no root, so a
    fold under it seeds nothing — which is exactly what every world founded before this
    declaration must see."""
    return ((views.active_rules(as_of).get(cite) or {}).get(KEY_SPACE)) or {}


def _derive(key_of, value):
    """The key a row asks about, given the value its parameter carries (EP-28N AMENDMENT 1).

    APPLIED AFTER CANONICALISATION AND NOWHERE ELSE (EP-28O's order): the value arriving here
    is already the namespace's canonical spelling, so the container is computed once, from one
    spelling, by that namespace's own one computer (§A52). Anything that is not a string has
    no container — absent stays absent, and nothing is coerced into a path here."""
    if key_of != CONTAINER:
        return value
    return custody.parent_of(value) if isinstance(value, str) else None


def _key_for(c, value):
    """`_derive` for a check row: the key THIS row is about."""
    return _derive(c.get(KEY_OF), value)


def declared_roots(definitions, views, as_of=None):
    """{root key: what the root names} over every key space the LIVE LAW declares, read from
    the citations the live definitions' own key checks carry (EP-28N AMENDMENT 1).

    THE POPULATION IS THE CITATIONS AND NOT A LIST HERE (I5), exactly as `binding_rows` and
    `kind_gifts` are read: this module learns which laws govern key spaces from the rows that
    cite them, so a key space arriving next campaign is seeded for having been declared and
    for no other reason. A world whose laws declare no key space yields {}."""
    out = {}
    for d in definitions.values():
        for c in (d.get("checks") or []):
            if c.get("check") not in (BINDING, KIND, CONTAINS):
                continue
            space = _key_space(views, _row_cite(c, d), as_of)
            if space.get(KEY_SPACE_ROOT) is not None:
                out[space[KEY_SPACE_ROOT]] = space.get(KEY_SPACE_ROOT_KIND)
    return out


def binding_rows(definitions):
    """{action: [(key_param, require, effect, key_of), ...]} — THE FOLD'S LAW, READ FROM THE
    DEFINITIONS rather than held here (I5).

    DECLARATION ORDER IS PRESERVED BECAUSE IT IS LOAD-BEARING TWICE: the interpreter runs an
    op's checks in it, so FILE-LINK answers "the target is not there" before "the new name is
    taken" exactly as the port does; and the fold applies an act's effects in it, so
    FILE-RENAME unbinds its source before it binds its destination, which is what a rename
    onto its own name needs."""
    rows = {}
    for name, d in definitions.items():
        got = [(c.get("key_param"), c.get("require"), c.get("effect"), c.get(KEY_OF))
               for c in (d.get("checks") or []) if c.get("check") == BINDING]
        if got:
            rows[name] = got
    return rows


def kind_gifts(definitions):
    """{action: {key_param: source-declaration}} — WHAT CLASS EACH BINDING ACT GIVES the key
    it binds, read from the declarations rather than held here (I5). Same law, same reader,
    same fold as `binding_rows`; a second walk over the same records would be a second
    mechanism for one idea (ADDENDUM I.2)."""
    out = {}
    for name, d in definitions.items():
        got = {c.get("key_param"): c[BINDS_KIND] for c in (d.get("checks") or [])
               if c.get("check") == BINDING and c.get("effect") == BIND and c.get(BINDS_KIND)}
        if got:
            out[name] = got
    return out


def _live_namespace(store, views, as_of=None):
    """(the keys currently bound, {key: the class it names}) — ONE FOLD, TWO PROJECTIONS.

    A SUBSET READ, NEVER THE WHOLE RECORD (design/36 ADDENDUM C): the store is asked for each
    declared action's own records and they are merged by sequence, so what this walks is the
    namespace traffic rather than the ledger. The HONEST CAP, stated where it will be read: it
    is O(that traffic) per act and the estate has no projection for it — `views.py` is outside
    this pass's fence as it was outside EP-28K's — so the acceleration is RAISED with its
    measurement rather than smuggled in as a memo nobody derived.

    THE TWO ANSWERS COME OUT OF ONE WALK BECAUSE THEY ARE ONE QUESTION ASKED TWICE. Whether a
    key is bound and what it names are both decided by the same acts in the same order; two
    folds over one record would be two readers that can disagree, which is the failure this
    estate keeps finding rather than a tidiness point.

    A GIFT IS RESOLVED BEFORE ANY OF THE ACT'S OWN EFFECTS ARE APPLIED, and that is not a
    convenience. A rename unbinds its source and binds its destination in declaration order,
    so a destination taking its class `from_key` the source would read a class the unbind had
    already dropped. Requirements are evaluated against the pre-act state; effects are what the
    act does to it; a gift is read on the same side of that line as the requirement.

    NO DECLARATIONS, NO FOLD. A world founded before this law declares none, so this returns
    the empty set and every act there is admitted exactly as it was. That is the two-times law
    holding by construction rather than by a branch: the law reaches FOUNDINGS, and a recorded
    world stands under the law of its own deciding time."""
    definitions = {n: (v.get("definition") or {})
                   for n, v in views.op_definitions(as_of).items()}
    rows = binding_rows(definitions)
    if not rows:
        return frozenset(), {}
    gifts = kind_gifts(definitions)
    merged = []
    for action in rows:
        merged.extend(store.by_action(action, as_of))
    merged.sort(key=lambda e: e["seq"])
    live, classes = set(), {}
    # THE DECLARED ROOTS ARE SEEDED BEFORE THE WALK AND NOT AFTER IT (EP-28N AMENDMENT 1),
    # because the walk READS this set: an act's own requirements are evaluated against it, so
    # a root arriving afterwards would leave every recorded create inside it looking like a
    # create into a container that was not there, and the fold would silently drop effects
    # the gate had lawfully admitted. Seeded HERE and in no other reader, so "is this key
    # bound" has exactly one answer in this module and in every caller of it.
    roots = declared_roots(definitions, views, as_of)
    for root, root_kind in roots.items():
        live.add(root)
        if root_kind is not None:
            classes[root] = root_kind
    for e in merged:
        p = e.get("payload") or {}
        declared = rows[e["action"]]
        if not all((_derive(of, p.get(key)) in live) == (req == BOUND)
                   for key, req, _effect, of in declared if req is not None):
            continue                       # its own requirements did not hold: no effect
        given = {}
        for key_param, gift in (gifts.get(e["action"]) or {}).items():
            if "literal" in gift:
                given[key_param] = gift["literal"]
            elif "param" in gift:
                given[key_param] = p.get(gift["param"])
            else:
                given[key_param] = classes.get(p.get(gift["from_key"]))
        for key, _req, effect, _of in declared:
            if effect == BIND:
                live.add(p.get(key))
                # A BIND THAT DECLARED NO CLASS LEAVES THE KEY CLASSLESS RATHER THAN KEEPING
                # A STALE ONE. The record did not say, so the fold does not either — and the
                # definition-time guard is what stops that silence arising under a law whose
                # acts are asked the question.
                if given.get(key) is None:
                    classes.pop(p.get(key), None)
                else:
                    classes[p.get(key)] = given[key]
            elif effect == UNBIND:
                if p.get(key) in roots:
                    # A DECLARED ROOT IS NOT UNBINDABLE, AND THAT IS THE LEASH THE SEEDING
                    # ARRIVES WITH (design-soul §2). The root is bound by DECLARATION and by
                    # no act, so no act can unbind it: a record claiming to does not undo a
                    # binding nothing performed, and honouring it would empty the key space
                    # of its bottom and refuse every later act under that law. THE RECORD
                    # SUCH AN ACT LEAVES IS A DEFECT THIS PASS DOES NOT CLOSE — before this
                    # seeding the same act was inert because the root was absent, and it is
                    # inert now because the root is declared; either way an rmdir of a root
                    # is admitted and appends. RAISED with its arithmetic, not fixed here:
                    # refusing it is a new outcome, and the outcomes this pass declares are
                    # exactly the nineteen the port's own preconditions enumerate.
                    continue
                live.discard(p.get(key))
                classes.pop(p.get(key), None)
    return frozenset(live), classes


def _live_bindings(store, views, as_of=None):
    """The bound half of `_live_namespace`, kept as its own name because it is what EP-28K's
    rows and the port-equality rows read."""
    return _live_namespace(store, views, as_of)[0]


def _binding_check(gate, store, views, actor, opname, c, params):
    """THE DECLARED EXISTENCE PRECONDITION, ANSWERED INSIDE THE DECIDE REGION (EP-28K).

    Two refusals, one per polarity, each citing the law the check names. A refusal here is a
    FULL RECORD (P4) and no act-record claiming an effect is appended — which is the whole
    difference from the idempotent create this pass refuses, whose state is right and whose
    record holds an act that did not happen.

    A row that declares no `require` is an EFFECT-ONLY row: it tells the fold what the act does
    to a key and asks nothing of the caller (FILE-RENAME's destination, which POSIX lets a
    rename replace). It is not a check that always passes; it is a declaration with no
    question in it, and the definition-time guard refuses a row that has neither."""
    require = c.get("require")
    if require is None:
        return
    key = _key_for(c, params.get(c["key_param"]))
    bound = key in _live_bindings(store, views)
    if bound and require == UNBOUND:
        _refuse_about_the_act(gate, actor, opname, c,
                              c.get("message") or
                              "%s: %r is already bound and this operation requires a free name"
                              % (opname, key),
                              _requirement(REQ_BINDING % UNBOUND, c.get(KEY_OF)))
    if not bound and require == BOUND:
        _refuse_about_the_act(gate, actor, opname, c,
                              c.get("message") or
                              "%s: %r is not bound and this operation requires an existing one"
                              % (opname, key),
                              _requirement(REQ_BINDING % BOUND, c.get(KEY_OF)))


def _value_domain_check(gate, store, views, actor, opname, c, params):
    """WHETHER A PARAMETER CARRIES A VALUE THE LAW DECLARES (EP-30-C1).

    ONE REFUSAL. The domain is a list the DEFINITION states, so the vocabulary has one home —
    the pack — and a reader asking "which roles exist" reads the law rather than a literal in a
    subsystem module. That is the whole reason this is a check kind and not an `if` in the comms
    view: a value set spelled in code beside a value set spelled in the founding is two
    vocabularies, which is the divergence class this estate keeps paying for.

    ABSENT IS NOT IN THE DOMAIN, and that asymmetry is the law rather than an accident: a
    parameter the caller omitted carries None, None is not a declared value, and the act refuses.
    An op that wants an omission to be lawful declares a `param_defaults` entry — a default is a
    statement the law makes, where silence is not."""
    domain = c.get("domain")
    if not domain:
        return
    value = params.get(c["param"])
    if value not in domain:
        gate.refuse(actor, opname, c.get("cite") or "AR-2",
                    c.get("message") or
                    "%s: %r is not a value this law declares for %r — the declared set is: %s"
                    % (opname, value, c["param"], ", ".join(repr(v) for v in domain)))


def _live_slots(store, c, as_of=None):
    """THE COMPUTED LIVE SET a `live_slot` check reads: {(slot, instance): slot}.

    RECORD THE ACT, COMPUTE THE VIEW — applied to the invariant itself, which is the point of
    the kind. Nothing here stores a count: the occupancy question is answered by folding the
    declared opening and closing actions in sequence order, so a closed opening leaves the set
    and its slot is free again. A quota kept as a stored tally would answer a DIFFERENT question
    — openings across a lifetime — and would bar every program restart (design/39 §3).

    KEYED BY (slot, instance) AND NOT BY INSTANCE ALONE, because two entities may lawfully open
    channels of the SAME NAME and they must stay distinct — the red fact this pass exists to
    cure, seen from the other side.

    THE HONEST CAP, stated where it will be read: a closing act names only `instance_param`, so
    a close frees EVERY live entry carrying that instance value. That is the CURRENT close
    semantics preserved exactly (the retired fold discarded a bare name from a set), and under
    two same-named channels held by two entities it frees both. This pass does NOT cure it —
    curing it means the closing op's own definition must name whose channel it closes, which is
    a second op's law and outside this plan's fence. RAISED, with its arithmetic, not smuggled."""
    ip, sp = c["instance_param"], c["slot_params"]
    merged = []
    for action in (c["open_action"], c["close_action"]):
        merged.extend(store.by_action(action, as_of))
    merged.sort(key=lambda e: e["seq"])
    live = {}
    for e in merged:
        p = e.get("payload") or {}
        if e["action"] == c["open_action"]:
            slot = tuple(p.get(k) for k in sp)
            live[(slot, p.get(ip))] = slot
        else:
            for key in [k for k in live if k[1] == p.get(ip)]:
                live.pop(key, None)
    return live


def _live_slot_check(gate, store, views, actor, opname, c, params):
    """AT MOST ONE LIVE OCCUPANT PER DECLARED SLOT, ANSWERED INSIDE THE DECIDE REGION (EP-30-C1).

    ONE REFUSAL, citing the law the check names. Inside the check loop for the same structural
    reason as its five neighbours: the loop runs inside a handler, a handler is invoked from
    exactly one site, so check-then-act is atomic here by the same construction that already
    covers the others — which matters more for this kind than for any of them, since a
    read-then-append race is precisely how a second live occupant would arrive."""
    live = _live_slots(store, c)
    slot = tuple(params.get(k) for k in c["slot_params"])
    if slot in live.values():
        gate.refuse(actor, opname, c.get("cite") or "AR-2",
                    c.get("message") or
                    "%s: a live occupant already holds %s — this slot admits one at a time"
                    % (opname, dict(zip(c["slot_params"], slot))))


def _kind_check(gate, store, views, actor, opname, c, params):
    """WHAT THE KEY NAMES, ANSWERED INSIDE THE DECIDE REGION (EP-28N).

    Two refusals, one per polarity, each citing the law the check names and each carrying what
    the act required — because the RECORD is keyed by the rule and the CALLER's answer is
    keyed by the act, and one rule governs both polarities over both keys.

    A KEY WITH NO RECORDED CLASS SATISFIES NEITHER POLARITY THE SAME WAY, and that asymmetry
    is the law rather than an accident: `require` fails, because nothing says the key is what
    the act needs it to be; `forbid` passes, because nothing says it is the thing the act
    refuses. Both read the record's silence as silence — the alternative is inventing a class
    nobody recorded, and the definition-time guard is what keeps that silence from arising
    under a law whose acts are asked the question."""
    want, forbid = c.get("require"), c.get("forbid")
    if want is None and forbid is None:
        return
    key = _key_for(c, params.get(c["key_param"]))
    held = _live_namespace(store, views)[1].get(key)
    if want is not None and held != want:
        _refuse_about_the_act(gate, actor, opname, c,
                              c.get("message") or
                              "%s: %r does not name what this operation acts on" % (opname, key),
                              _requirement(REQ_KIND_REQUIRE % want, c.get(KEY_OF)))
    if forbid is not None and held == forbid:
        _refuse_about_the_act(gate, actor, opname, c,
                              c.get("message") or
                              "%s: %r names what this operation does not act on" % (opname, key),
                              _requirement(REQ_KIND_FORBID % forbid, c.get(KEY_OF)))


def _contains_check(gate, store, views, actor, opname, c, params):
    """WHAT THE KEY HOLDS, ANSWERED INSIDE THE DECIDE REGION (EP-28N AMENDMENT 1).

    ONE REFUSAL: the act requires the key to hold nothing and the live key space says
    otherwise. The membership question and the `key_of: container` question are ONE RELATION
    ASKED FROM ITS TWO ENDS, read here through the same `_derive` — so "x holds y" and "y's
    container is x" cannot become two different answers, which is the divergence class this
    whole EP was opened over.

    THE ROOT IS NOBODY'S MEMBER AND NO KEY IS ITS OWN CONTAINER, both by the relation rather
    than by a branch: the root's container is nothing, and a container is always a strictly
    shorter key.

    A KEY THE ROW'S DERIVATION DOES NOT PRODUCE HAS NO MEMBERS AND IS NOT ASKED ABOUT. Absent
    is not a container of everything whose container is absent — reading it that way would
    make a row over a missing parameter refuse every act in the key space."""
    require = c.get("require")
    if require is None:
        return
    key = _key_for(c, params.get(c["key_param"]))
    if key is None:
        return
    held = sorted(k for k in _live_namespace(store, views)[0] if _derive(CONTAINER, k) == key)
    if require == EMPTY and held:
        _refuse_about_the_act(gate, actor, opname, c,
                              c.get("message") or
                              "%s: %r still holds %d name(s) and this operation requires one "
                              "that holds nothing" % (opname, key, len(held)),
                              _requirement(REQ_CONTAINS % EMPTY, c.get(KEY_OF)))


# PLACED HERE, BEFORE `_prior_value_check`, AND THE POSITION IS LOAD-BEARING (EP-30-K2).
# `tests/test_ep30_k1.py` reads two SOURCE SLICES of this module by function name —
# `_prior_value_check`->`_bound_field_check` and `_bound_field_check`->`_interpreter` — to
# assert that an author's `message` override reaches ONE refusal and not three. These two
# definitions sit OUTSIDE both slices, because a function landing inside one is counted as
# part of a neighbour's arm and reds a row about code it never touched. DRIVEN: they were
# first written between `_bound_field_check` and `_interpreter` and redded exactly that row
# (`3 != 1`). The constraint is not left to this comment — `tests/test_ep30_k2.py` carries a
# row that reds if either slice is polluted again.
class _ProbeGate:
    """THE GATE, ASKED WITHOUT BEING TOLD (EP-30-K2). A refusal raised through this object is
    RAISED AND NOT RECORDED.

    WHY IT HAS TO EXIST: `gate.refuse` APPENDS a refusal record and then raises. A quantifier that
    let its inner question refuse through the real gate would record ONE REFUSAL PER FAILING
    MEMBER, so a set with three bad members would leave three refusal records for a single act —
    a record holding acts nobody performed, which is the one lie class this estate refuses. The
    inner question is EVALUATED here and the single authoritative refusal is recorded ONCE, by the
    quantifier, naming the member that failed.

    EVERYTHING ELSE PASSES STRAIGHT THROUGH, so an inner check calling `gate.has` reads the real
    registry. Only the recording half of `refuse` is withheld. A gate-shaped double is already
    this module's idiom — `validate_definition_shape` is documented to accept "anything with the
    gate's refuse", and the founding installer passes its own door object."""

    def __init__(self, gate):
        self._gate = gate

    def __getattr__(self, name):
        return getattr(self._gate, name)

    def refuse(self, actor, op, rule, message, draft=None):
        raise OpError(rule, message)


def _every_member_check(gate, store, views, actor, opname, c, params, dispatch):
    """EVERY MEMBER OF A MANY-VALUED PARAMETER SATISFIES A DECLARED QUESTION (EP-30-K2).
    See the derivation at OP_CHECKS above.

    THIS EVALUATOR NAMES NO OTHER CHECK KIND, and that is the owner's rebuildability rider holding
    rather than a style: it receives THE ENGINE'S ONE DISPATCH SITE as `dispatch` and hands each
    member to it. Re-cut the vocabulary and nothing here moves, because nothing here knows what
    the words are. A kind-to-function table would have named all sixteen and turned a
    re-derivation into a rewrite — which is exactly what the rider forbids.

    THE MEMBER IS PART OF THE VERDICT, NEVER PART OF THE DEBUGGING. A refusal saying only that
    SOMETHING in the set is wrong answers two different worlds with one string, and a caller
    holding twenty grantees cannot act on it. The refusal names the member and carries the inner
    question's own reason.

    THE EMPTY SET IS ANSWERED BY THE DECLARATION AND NEVER BY THIS FUNCTION — `on_empty` is
    mandatory at definition time (see ON_EMPTY above), so by the time an act arrives the law has
    already said which way an empty set goes. There is no branch here that could be called a
    default, and there is deliberately no `.get` with a fallback: a fallback would be this engine
    answering a question the law-data is entitled to answer, silently, on the one input where
    vacuous truth is waiting.

    A SET THAT IS NOT A SET REFUSES rather than being coerced or iterated. A string is iterable
    and its members are characters, so admitting one would ask the inner question of every letter
    of a name — an answer computed over a subject nobody declared. Absent refuses for
    `value_domain`'s reason one layer out: a parameter the caller omitted carries None, None is
    not a set of anything, and the act refuses."""
    members = params.get(c["param"])
    if isinstance(members, (str, bytes)) or not isinstance(members, (list, tuple)):
        gate.refuse(actor, opname, c.get("cite") or "AR-2",
                    "%s: %r is not a set of values, so a question asked of every member of it "
                    "has no subject — this law is declared over a many-valued parameter"
                    % (opname, c["param"]))
    if not members:
        if c[ON_EMPTY] == ON_EMPTY_REFUSE:
            gate.refuse(actor, opname, c.get("cite") or "ROOT-NEG-1",
                        c.get("message") or
                        "%s: %r carries no members and this law requires at least one — every "
                        "member of an empty set satisfies any question, so an empty set is "
                        "answered by the law and never by the absence of anything to test"
                        % (opname, c["param"]))
        return
    probe = _ProbeGate(gate)
    for member in members:
        try:
            dispatch(probe, c[INNER], dict(params, **{c[MEMBER_PARAM]: member}))
        except OpError as refused:
            gate.refuse(actor, opname, c.get("cite") or refused.rule,
                        "%s: member %r of %r fails this law — %s"
                        % (opname, member, c["param"],
                           c.get("message") or refused.message))


def _resolve_field_path(payload, path):
    """Walk a DOTTED path into a record's payload. Returns `(resolved, value)`.

    MAPPINGS ONLY, and the narrowness is the point: a path that meets anything else STOPS
    UNRESOLVED rather than guessing. It never indexes a sequence, never calls, and never
    evaluates — the growth path `OP_CHECKS`'s block names (a full predicate AST) is a different
    thing and stays unbuilt. `Mapping` rather than `dict` because a record's payload arrives as
    a read-only mapping through the store's own resolve.

    RESOLVED-AND-None IS NOT THE SAME ANSWER AS UNRESOLVED, which is why this returns a pair and
    not a value: the law's `value: null` is a DECLARED absence and a missing key is silence, and
    a function returning None for both would erase exactly the distinction its caller exists to
    make."""
    node = payload
    for part in path.split("."):
        if not isinstance(node, Mapping) or part not in node:
            return False, None
        node = node[part]
    return True, node


def _prior_value_check(gate, store, views, actor, opname, c, params):
    """WHETHER A NAMED FIELD INSIDE A CITED PRIOR RECORD HOLDS A VALUE, ANSWERED INSIDE THE
    DECIDE REGION (EP-29 W3a3). See the derivation at PRIOR_VALUE above.

    THE LOCATE AND THE READ MEET THE SAME RECORD, and that single sentence is this kind's whole
    addition to the vocabulary. Two `require_prior` rows cannot do it: each is an independent
    existence scan, so a caller citing one declaration while carrying another's field satisfies
    both. Here the record is found ONCE and the field is read OUT OF THAT RECORD.

    THE VALUE COMES FROM THE RECORD AND NEVER FROM A PARAMETER. `require_prior` compares a
    record's field against what the CALLER supplied, which is a check the caller satisfies by
    construction; the question here is about the LAW-DATA's own content, so nothing the caller
    passes can move the answer. That is what makes it usable as a fail-closed licence test.

    LATEST WINS: the highest-seq match, because a declaration amended later is the one in force.

    THREE REFUSALS, one per state, and the middle one is the one a reader is most likely to
    think redundant. It is not: an unestablished value is DECLARED unestablished and never
    omitted, so a declaration silent about the field has not said "no value" — it has said
    nothing, and nothing filled by a default is the fail-open trap.

    THE ROW'S `message` WORDS THE REQUIREMENT MISMATCH AND ONLY IT. The other two refusals are
    ENGINE-WORDED, and that is a repair rather than a shortcut: the first draft let the override
    reach all three, so an act naming a declaration NOBODY MADE recorded a refusal saying that
    declaration leaves its field unestablished — a record asserting what nothing measured, which
    is the one lie class this estate refuses, produced by the check meant to prevent it. Caught by
    driving the paths, not by reading the branch. An author words the mismatch because that is the
    refusal its own law is about; the two absences are the engine's to describe truthfully."""
    require = c.get("require")
    if require is None:                                  # the leash refuses this at the door
        return
    want = params.get(c["param"])
    matched = [e for e in store.by_action(c["action"])
               if (e.get("payload") or {}).get(c["field"]) == want]
    if not matched:
        gate.refuse(actor, opname, c.get("cite") or "ROOT-NEG-1",
                    "no %s names %s = %r, so the field this act's licence would be computed from "
                    "belongs to no record — an act no declaration founds is permitted by nothing"
                    % (c["action"], c["field"], want))
    record = max(matched, key=lambda e: e["seq"])
    resolved, value = _resolve_field_path(record.get("payload") or {}, c["value_field"])
    if not resolved:
        gate.refuse(actor, opname, c.get("cite") or "ROOT-NEG-1",
                    "%s %r declares nothing at %r — a value this law leaves UNESTABLISHED is "
                    "declared unestablished and never omitted, so a silence here is not an "
                    "answer and no licence computes from it"
                    % (c["action"], want, c["value_field"]))
    holds = value is not None
    if (require == ESTABLISHED) != holds:
        gate.refuse(actor, opname, c.get("cite") or "ROOT-NEG-1",
                    c.get("message") or
                    "%s %r declares %r %s and this operation requires it %s"
                    % (c["action"], want, c["value_field"],
                       "a value" if holds else "UNESTABLISHED", require))


def _bound_field_check(gate, store, views, actor, opname, c, params):
    """THE RECORD THIS PARAMETER NAMES, AND WHETHER ITS FIELD EQUALS THAT PARAMETER (EP-30-K1).
    See the derivation at BOUND_FIELD above.

    EXISTENCE IS NOT SELECTION, and that single sentence is this kind's whole addition. The
    record is BOUND ONCE, by `key_param`, and the comparison is made against THAT record —
    where `require_prior` asks whether ANY record of the action carries the value, a question a
    holder of some other thing satisfies. Both spellings of "the giver holds it" are driven
    side by side in EP-30-K1 R1, and they separate.

    LATEST WINS: the highest-seq match, because a holding is written as an amending declaration
    of the same action and the last one is the one in force (EP-30-E1, board :888).

    THREE REFUSALS, and the FIRST IS DECLARED RATHER THAN DECIDED HERE. An unbound key means the
    record this act names does not exist, and whether that bars the act is a fact about the LAW,
    not about this engine: a licence with no declaration is nothing, while a relation not yet
    entered into is merely outside the rule's reach. `when_unbound` states which, silence means
    refuse, and the reason a weakening must be written out is ROUTER_ABSENCE's.

    THE ROW'S `message` WORDS THE MISMATCH AND ONLY IT, which is `prior_value`'s repair carried
    forward rather than rediscovered. An author's message describes the law its row is about —
    the field not matching. The two other refusals are ENGINE-WORDED, because a row message
    reused for a record that does not exist would record a refusal asserting something nothing
    measured, which is the one lie class this estate refuses."""
    policy = c.get(WHEN_UNBOUND) or UNBOUND_REFUSE      # the leash refuses an unknown at the door
    want_key = params.get(c["key_param"])
    matched = [e for e in store.by_action(c["action"])
               if (e.get("payload") or {}).get(c["field"]) == want_key]
    if not matched:
        if policy == UNBOUND_PERMIT:
            return
        gate.refuse(actor, opname, c.get("cite") or "ROOT-NEG-1",
                    "no %s names %s = %r, so the record this act's %r would be measured against "
                    "belongs to no record — and this law requires one"
                    % (c["action"], c["field"], want_key, c["param"]))
    record = max(matched, key=lambda e: e["seq"])
    resolved, value = _resolve_field_path(record.get("payload") or {}, c["value_field"])
    if not resolved:
        gate.refuse(actor, opname, c.get("cite") or "ROOT-NEG-1",
                    "%s %r declares nothing at %r — the field this act is measured against is "
                    "not on the record that names it, so a silence here is not an answer"
                    % (c["action"], want_key, c["value_field"]))
    supplied = params.get(c["param"])
    if value != supplied:
        gate.refuse(actor, opname, c.get("cite") or "ROOT-NEG-1",
                    c.get("message") or
                    "%s %r carries %s = %r and this operation was given %s = %r"
                    % (c["action"], want_key, c["value_field"], value, c["param"], supplied))


def _interpreter(gate, store, views, opname, d):
    """The one generic reader: the gate has validated params; resolve param defaults, run
    the definition's checks (refuse-and-record on failure), then return the decision shape
    (the gate appends it). All fields below are GENERAL op_definition capabilities, never a
    subsystem special case."""
    # READ ONCE, AT REGISTRATION, NOT PER ACT (EP-28O). A definition's declarations are fixed
    # for the life of its registration — amending one is retire + create — so walking them on
    # every call would put a per-act cost on the gate's hot path for an answer that cannot move.
    key_params = _declared_keys(d)

    def run(actor, params):
        # ONE CANONICAL SPELLING PER NAME, COMPUTED HERE AND READ EVERYWHERE AFTER (EP-28O).
        #
        # FIRST, AND THAT ORDER IS THE POINT rather than a tidiness: everything below reads
        # `p_in` — the `$path` identity derivation two lines down, the checks that compare the
        # key against the live set, the object, and the payload the record carries — so the
        # canonical value is computed ONCE, above all of them, and each of those is a READER of
        # it. Canonicalising at any one of them instead would make that one reader right and
        # leave the recorded key raw for the next.
        #
        # WHAT IS CANONICALISED IS DECLARED, NOT GUESSED: `key_params` is the union of the
        # `key_param`s this definition's own `binding` and `kind` checks name. An op declaring
        # no key is untouched, and a parameter that is not a key is untouched inside an op that
        # has one.
        #
        # PRESENT-AND-A-STRING ONLY. `_norm(None)` is "/" by its own documented behaviour, so
        # canonicalising an ABSENT parameter would manufacture a key nobody supplied — absent
        # stays absent, and a key that is not a string is left exactly as it arrived rather than
        # coerced into a path.
        p_in = dict(params)
        for k in key_params:
            v = p_in.get(k)
            if isinstance(v, str):
                p_in[k] = custody._norm(v)
        # param_defaults: apply the handler-era fallbacks BEFORE checks and payload, so both
        # see the same values. "$actor" reproduces `params.get(k, actor)`; any other value is
        # a static default (e.g. prot "rw"). Default only on an ABSENT key (matches dict.get).
        for pk, dv in (d.get("param_defaults") or {}).items():
            if pk not in p_in:
                if dv == "$actor":
                    p_in[pk] = actor                       # reproduces params.get(k, actor)
                elif isinstance(dv, str) and dv.startswith("$"):
                    p_in[pk] = p_in.get(dv[1:])            # default to another param (inode <- $path)
                else:
                    p_in[pk] = dv                          # a static default (priority "normal", perm "644")
        # object_derive (EP-16 X1): the object id is a TEMPLATED string over resolved params
        # (`space:{name}`, `grant:{grant_id}`, `role:{name}`) — the general form the four authority
        # ops need to be definition-born (their object is a prefixed param, not a raw one). Computed
        # BEFORE the checks so a check (space_tree) may reference it. General: mirrors object_param,
        # never a per-op case. Falls back to object_param, then None.
        if d.get("object_derive"):
            obj = d["object_derive"]["tpl"].format(**p_in)
        elif d.get("object_param"):
            obj = p_in.get(d["object_param"])
        else:
            obj = None
        # CHECK VERDICTS the accepted record carries (EP-23). Every check before the fingerprint
        # only ever REFUSED, so a pass left no trace and a reader could not tell a checked act from
        # an unchecked one. design/34 §7 requires the applied record to carry the passed check, so a
        # check may now return fields, collected here and merged into the payload below. General:
        # the mechanism is one dict, not a fingerprint special case.
        stamped = {}
        # THE ONE DISPATCH SITE, GIVEN A NAME SO A QUANTIFIER CAN REACH IT (EP-30-K2). The
        # chain below is UNCHANGED — every arm reads the same names it always did, because the
        # parameters shadow them exactly: `gate` is the gate this row refuses through, and
        # `p_in` the resolved parameters this row reads. What changed is that the chain is now
        # CALLABLE, so `every_member` can hand each member of a set to the SAME sixteen arms
        # instead of carrying a copy of them. A second dispatch table would be two vocabularies
        # for one menu — and it would have to name every kind, which is what the owner's
        # rebuildability rider forbids (design/28 §5): re-cut the word list and a table has to
        # be rewritten, while a callable knows none of the words and survives untouched.
        #
        # IT STAYS INSIDE `run`, and that is load-bearing rather than tidy: the structural proof
        # that every declared kind runs inside the decide region reads this loop as being inside
        # a handler, and a handler as invoked from exactly one site (tests/test_ep28g_w2.py).
        # The literal spellings stay literal for that file's enumerator, which walks for a
        # `c["check"] == <constant>` comparison and would not see a named constant.
        def _dispatch_check(gate, c, p_in):
                if c["check"] == "require_prior":
                    want = p_in.get(c["param"])
                    if not any((e.get("payload") or {}).get(c["field"]) == want
                               for e in store.by_action(c["action"])):
                        gate.refuse(actor, opname, c.get("cite") or "ROOT-NEG-1",
                                    c.get("message") or f"no prior {c['action']} with {c['field']} = {want}")
                elif c["check"] == "sight":
                    target = p_in.get(c["target_param"])
                    if not can_read(store, actor, target, views.chain_end()):  # root = chain-end (R-C1)
                        gate.refuse(actor, opname, "SIGHT-IS-LAW",
                                    f"{actor} may not act on '{target}' — it could not lawfully read it (sight is law)")
                elif c["check"] == "ceiling":
                    _ceiling_check(gate, store, views, actor, opname, c, p_in)
                elif c["check"] == "consistency":
                    _consistency_check(gate, views, actor, opname, c, p_in)
                elif c["check"] == "definition_ref":
                    # DICTIONARY INTEGRITY-AT-USE (EP-12; the EP-07 fire-time precedent). Using a term
                    # resolves its LATEST-UNDISPUTED entry and verifies its definition_ref points to a real
                    # op/view definition. A term that does not resolve, or a DANGLING ref, refuses HERE — at
                    # the act of use — cited, never a silent pointer. The dictionary is read through the view.
                    ek = p_in.get(c["entity_kind_param"])
                    term = p_in.get(c["term_param"])
                    entry = views.dictionary(ek).get((ek, term))     # term_key == term (v1, no normalisation)
                    if entry is None:
                        gate.refuse(actor, opname, c.get("cite") or "ROOT-NEG-1",
                                    f"no undisputed dictionary entry for {ek} '{term}' — the term does not resolve")
                    ref = entry.get("definition_ref")
                    if ref and not _definition_exists(gate, views, ref):
                        gate.refuse(actor, opname, c.get("cite") or "CAP-IS-LAW",
                                    f"dictionary term '{term}' links to '{ref}', which is not a registered op/view "
                                    "definition — a dangling reference refuses at use")
                elif c["check"] == "entry_ref":
                    # DICTIONARY-ENTRY INTEGRITY AT USE (W5/finding A5; mirrors definition_ref). A DISPUTE or
                    # RESOLVE-DISPUTE names a dictionary entry by its seq; a ref_seq that names no existing
                    # dictionary_entry record — a typo, or a FUTURE seq that would else silently suppress the
                    # entry that later lands there — is not a dispute but a dangling reference: refuse HERE, at
                    # the act of use, cited (the R18/R28 doctrine — accept-what-you-cannot-honour REFUSES).
                    seq = p_in.get(c["seq_param"])
                    ref = store.by_seq(seq) if isinstance(seq, int) and not isinstance(seq, bool) else None
                    if ref is None or (ref.get("payload") or {}).get("kind") != "dictionary_entry":
                        gate.refuse(actor, opname, c.get("cite") or "DICT-LAW",
                                    f"references seq {seq}, which names no dictionary entry — a dangling reference refuses at use")
                elif c["check"] == "sop":
                    # SEPARATION OF POWERS (design 28 §5/§7; EP-09): the MAKER of an object may not review
                    # or act on it. The creator is read through the CONSERVED VIEW SURFACE (views.creator_of
                    # -> the object's minting record), never a private store scan (the read-stack direction,
                    # §I8). No target / unknown object -> nothing to separate.
                    target = p_in.get(c["target_param"])
                    maker = views.creator_of(target) if target is not None else None
                    if maker is not None and actor == maker:
                        gate.refuse(actor, opname, c.get("cite") or "SOP",
                                    f"{actor} may not review its own object '{target}' — the maker is not the reviewer "
                                    "(separation of powers)")
                elif c["check"] == "space_tree":
                    # THE SPACE-TREE BAR (EP-16 X1; design/31 J2). Extracted verbatim from the retired
                    # CREATE-SPACE boot handler so it can be a definition. `obj` is the derived space id
                    # (space:<name>). Cycle FIRST (a space naming itself/a descendant as parent would loop
                    # the tree — the corpus's no-circular-authority item applied to territory, refused for
                    # everyone, BOOT-INT), then referential integrity (a space nests under an EXISTING
                    # space, CAP-IS-LAW). Reads the record through authority folds — never a string prefix.
                    parent = p_in.get(c["parent_param"])
                    if authority.would_cycle(store, obj, parent):
                        gate.refuse(actor, opname, c.get("cite_cycle") or "BOOT-INT",
                                    f"{obj} under {parent} would loop the tree — a space's parent chain must reach the root")
                    if not authority.space_exists(store, parent):
                        gate.refuse(actor, opname, c.get("cite_missing") or "CAP-IS-LAW",
                                    f"parent {parent!r} is not a founded space — a space nests under an existing space")
                elif c["check"] == "fingerprint":
                    # THE SEAL, CHECKED AT RETURN (EP-23; design/34 §6). Resolves the cited hand-out,
                    # recomputes its pinned input-view asOf now, compares canonical hashes. Three
                    # refusals, correctly separated: an unbound citation cites the CORRELATION rule
                    # (it did not go stale, it failed to bind), a moved read-set cites the STALENESS
                    # rule, and a declared interval guard that fired cites its own reason (path moved
                    # though state is equal). Returns the verdict the record will carry.
                    stamped.update(crossing.check_fingerprint(gate, store, views, actor, opname, c, p_in))
                elif c["check"] == "binding":
                    # THE EXISTENCE PRECONDITION AS LAW (EP-28K). Here, in the check loop, which is
                    # the whole point: `tests/test_ep28g_w2.py` proves STRUCTURALLY that every
                    # declared kind is dispatched from this loop, this loop runs inside a handler,
                    # and a handler is invoked from exactly one site — `gate._decide`, inside the
                    # region. So check-then-act is atomic for this kind by the same construction
                    # that already covered the other nine, including one added tomorrow.
                    _binding_check(gate, store, views, actor, opname, c, p_in)
                elif c["check"] == "kind":
                    # WHAT THE KEY NAMES (EP-28N). Here for the same reason `binding` is here, and
                    # the reason is now a discharged theorem rather than a claim:
                    # `tests/test_ep28g_w2.py` proves STRUCTURALLY that every declared kind is
                    # dispatched from this loop, that loop runs inside a handler, and a handler is
                    # invoked from exactly one site — `gate._decide`, inside the region. EP-28K was
                    # the first kind to arrive after that proof was written and took zero lines in
                    # `gate.py`; this is the second, and it takes zero there too. The literal
                    # spelling matches `binding`'s and for its reason: that file's enumerator reads
                    # constants, and a named constant would make the new kind invisible to it.
                    _kind_check(gate, store, views, actor, opname, c, p_in)
                elif c["check"] == "contains":
                    # WHAT THE KEY HOLDS (EP-28N AMENDMENT 1). Here for the same reason `binding`
                    # and `kind` are here, and the reason is a theorem discharged twice already:
                    # `tests/test_ep28g_w2.py` proves STRUCTURALLY that every declared kind is
                    # dispatched from this loop, that loop runs inside a handler, and a handler is
                    # invoked from exactly one site — `gate._decide`, inside the region. EP-28K was
                    # its first arrival and EP-28N its second, each taking zero lines in `gate.py`;
                    # this is the third and it takes zero there too. The literal spelling matches
                    # its two neighbours' and for their reason: that file's enumerator reads
                    # constants, and a named constant would make the new kind invisible to it.
                    _contains_check(gate, store, views, actor, opname, c, p_in)
                elif c["check"] == "prior_value":
                    # WHETHER A CITED PRIOR RECORD'S NAMED FIELD HOLDS A VALUE (EP-29 W3a3). Here
                    # for the same reason `binding`, `kind` and `contains` are here, and the reason
                    # is a theorem discharged three times already: `tests/test_ep28g_w2.py` proves
                    # STRUCTURALLY that every declared kind is dispatched from this loop, that loop
                    # runs inside a handler, and a handler is invoked from exactly one site —
                    # `gate._decide`, inside the region. EP-28K was the first arrival after that
                    # proof and EP-28N the second and third, each taking zero lines in `gate.py`;
                    # this is the fourth and it takes zero there too. The literal spelling matches
                    # its three neighbours' and for their reason: that file's enumerator reads
                    # constants, and a named constant would make the new kind invisible to it.
                    _prior_value_check(gate, store, views, actor, opname, c, p_in)
                elif c["check"] == "value_domain":
                    # WHETHER A PARAMETER'S VALUE IS ONE THE LAW DECLARES (EP-30-C1). Here for the
                    # same reason `binding`, `kind`, `contains` and `prior_value` are here, and the
                    # reason is a theorem discharged four times already: `tests/test_ep28g_w2.py`
                    # proves STRUCTURALLY that every declared kind is dispatched from this loop,
                    # that loop runs inside a handler, and a handler is invoked from exactly one
                    # site — `gate._decide`, inside the region. This is the fifth arrival and it
                    # takes zero lines in `gate.py` too. The literal spelling matches its four
                    # neighbours' and for their reason: that file's enumerator reads constants, and
                    # a named constant would make the new kind invisible to it.
                    _value_domain_check(gate, store, views, actor, opname, c, p_in)
                elif c["check"] == "live_slot":
                    # WHETHER A COMPUTED LIVE SET ALREADY HOLDS THIS SLOT (EP-30-C1). Sixth arrival,
                    # same structural theorem, same literal spelling, same zero lines in `gate.py`.
                    _live_slot_check(gate, store, views, actor, opname, c, p_in)
                elif c["check"] == "bound_field":
                    # WHETHER THE RECORD THIS PARAMETER NAMES CARRIES A FIELD EQUAL TO THAT ONE
                    # (EP-30-K1). Seventh arrival, same structural theorem, same literal spelling,
                    # same zero lines in `gate.py`. The spelling is a LITERAL and matches its six
                    # neighbours' for their reason: `tests/test_ep28g_w2.py` enumerates this loop's
                    # dispatch sites by walking for a `c["check"] == <constant>` comparison, so a
                    # named constant here would make the new kind invisible to the very guard that
                    # proves every declared kind runs inside the region.
                    _bound_field_check(gate, store, views, actor, opname, c, p_in)
                elif c["check"] == "every_member":
                    # EVERY MEMBER OF A MANY-VALUED PARAMETER SATISFIES A DECLARED QUESTION
                    # (EP-30-K2). The SEVENTEENTH kind and the first that is not itself a question:
                    # it takes THIS FUNCTION as its dispatcher and asks the inner row of each member,
                    # so it names none of its sixteen neighbours. Eighth arrival, same structural
                    # theorem, same literal spelling, same zero lines in `gate.py`.
                    _every_member_check(gate, store, views, actor, opname, c, p_in,
                                        _dispatch_check)
                # RETIRED (EP-19 R-C2): the `attenuation` check branch. GRANT's whole-containment leash lives
                # at the gate chokepoint now (gate._grant_containment, EP-18 R-A) — one law, one home; no pack
                # op cites `attenuation`. `authority.within_makers_reach` is still called, from the gate.

        for c in d.get("checks", []):
            _dispatch_check(gate, c, p_in)
        fields = d.get("payload_from") or list((d.get("params") or {}).keys())
        payload = {p: p_in.get(p) for p in fields}
        # payload_derive: computed fields the generic copy can't build — a templated string
        # (`tpl`, str.format over resolved params) or an aliased copy (`copy`, type-preserved).
        # AMEND-BUDGET's rule_id / policy_key / value stay law without a memory special case.
        for field, spec in (d.get("payload_derive") or {}).items():
            if "tpl" in spec:
                payload[field] = spec["tpl"].format(**p_in)
            elif "copy" in spec:
                payload[field] = p_in.get(spec["copy"])
        payload.update(stamped)                          # a check's own recorded verdict (EP-23)
        # content_params: full-fidelity content is content-addressed — the bytes go to the blob
        # store, the payload records the HASH (and, for the dict form, the byte length), never
        # the bytes. Needs the blob store (gate.blobs, wired when the full kernel composes); an
        # op with content_params stays unregistered without it (see _register_from_definition).
        for param, spec in (d.get("content_params") or {}).items():
            value = p_in.get(param)
            h = gate.blobs.put(value)
            if isinstance(spec, str):
                payload[spec] = h
            else:
                payload[spec["hash"]] = h
                if spec.get("length"):
                    payload[spec["length"]] = len(value.encode("utf-8") if isinstance(value, str) else value)
        # secret_params (EP-19; design/31 J8): a SECRET value crosses ONCE, is sealed into the
        # VAULT (write-once, keyed by hash, NO read path — unlike the blob store, which has get),
        # and the payload records the HASH only. Same content_params discipline (the value never
        # lands in a payload), but the vault's guarantee is closure, not a cipher: no op reads a
        # sealed value back. Needs the vault (gate.vault, wired when the full kernel composes); an
        # op with secret_params stays unregistered without it (secret_ops_pending_vault).
        for param, spec in (d.get("secret_params") or {}).items():
            value = p_in.get(param)
            payload[spec] = gate.vault.seal(value)   # the HASH only; the value is sealed, never recorded
        # secret_verify (EP-19; design/31 J8): a CANDIDATE crosses, the vault COMPARES it (by hash,
        # inside the S-plane) against the latest secret SEALED under `name` IN THE SAME SPACE (rotation
        # is supersession by hash — views.sealed_secret_hash reads latest-per-(space, name); V6/mentor
        # verdict 2026-07-25), and the decision records MATCH / NO-MATCH + the sealed hash, NEVER the
        # candidate. The verify's query space is the caller's `space` (the same value the general
        # passthrough stamps below, and the same default-to-mother the fold applies), so a verify in
        # one space never matches a same-named seal in another. Verify-never-reveal: no value and no
        # candidate ever enters the record. `name` and the result/hash fields are the whole record.
        sv = d.get("secret_verify")
        if sv:
            candidate = p_in.get(sv["candidate_param"])
            sealed = views.sealed_secret_hash(p_in.get(sv["name_param"]), p_in.get("space"))
            matched = gate.vault.compare(candidate, sealed)
            payload[sv.get("result_field", "result")] = "MATCH" if matched else "NO-MATCH"
            payload[sv.get("hash_field", "secret_hash")] = sealed
        # stamp_actor: an AUTHORITY / ATTRIBUTION field that MUST equal the acting actor —
        # STAMPED unconditionally, overwriting any caller value (distinct from param_defaults
        # "$actor", which only DEFAULTS a caller-choosable subject like memory's holder). Without
        # this, SHM-GRANT's `granter` was forgeable: a caller could attribute a grant to another
        # actor in the shm-grant audit ledger. The retired handler hard-set granter = actor.
        for f in (d.get("stamp_actor") or []):
            payload[f] = actor
        # THE GENERAL SPACE PASSTHROUGH (EP-16 X2, S2 remainder): ANY op may carry an explicit
        # `space` into its record — one interpreter line, never a per-op case. A record that does
        # not carry one keeps the default-space fold (views.space_of -> the mother space). setdefault
        # so an op that already puts space in its payload (CREATE-SPACE, GRANT, CREATE-ROLE) is untouched.
        if p_in.get("space") is not None:
            payload.setdefault("space", p_in["space"])
        # THE CROSSING (EP-23 W1; wall primitive 1, design/36 §5). The station kind is
        # op_definition DATA, never a code branch — which law governs an op is read from the op's
        # own record, the EP-16 authority-regime precedent applied to executors. Meeting
        # `executor: external`, the interpreter does NOT run a handler to completion: this record
        # becomes the HAND-OUT DECISION, carrying the pinned pack, the seal, and the four version
        # pins. The crossing is then OPEN — as a DERIVED difference between records, not as
        # anything held in memory. Written LAST so the crossing's own vocabulary wins: a station's
        # record IS a crossing hand-out, whatever its payload_derive would otherwise have said.
        if d.get("executor"):
            payload.update(crossing.handout_fields(gate, store, views, actor, opname, d, p_in))
        # obj was computed above (object_derive / object_param) so a check could reference it.
        rec = {"actor": actor, "action": opname, "object": obj,
               "rule_cited": d["law_cited"], "payload": payload}
        # THE DECLARED STREAM (EP-30-W1a; board :918 route (a)). `action` above is THE DOOR and
        # keeps carrying the op that wrote this record — that line is unchanged, and constraint 2
        # is why. This adds WHERE THE DECLARATION LANDS, as a second fact, only when the
        # definition states one. An op that declares nothing sets nothing here, so its record is
        # byte-identical to the one it wrote before this key existed (constraint 1): the
        # conditional is the default-preservation, not an optimisation of it.
        if d.get(RECORD_STREAM):
            rec[RECORD_STREAM] = d[RECORD_STREAM]
        # target_param / content_form: general envelope fields some ops carry (FILE-LINK/
        # COMMS-SEND/SHM-GRANT set a top-level target; FILE-WRITE marks content_form "blob").
        # target is UNDEFAULTED — the handlers used params.get — so a missing field records
        # target=None exactly, even when the same param is defaulted in the payload. PRESENCE is
        # therefore still decided by the RAW caller parameters and nothing else; what changed at
        # EP-28O is that the VALUE comes from the resolved map, so a record whose payload says
        # `/a` cannot carry an envelope saying `/a/`. One record, one spelling of one name — the
        # defect this pass removes would otherwise survive inside the record that closed it. For
        # every op whose target is not a declared key the two maps hold the same value, so
        # nothing outside the namespace moves.
        if d.get("target_param"):
            tp = d["target_param"]
            rec["target"] = p_in.get(tp) if tp in params else None
        if d.get("content_form"):
            rec["content_form"] = d["content_form"]
        # evidence_param: copy a param into evidence_summary (the decision-embeds-evidence
        # law, AUDIT-FIX 3), falling back to the definition's evidence_default. General.
        # RAW params (W6b): the fallback a definition declares for this field is
        # `evidence_default`, in the same definition, and a `param_defaults` entry used to
        # displace it silently. One field, one declared fallback.
        ep = d.get("evidence_param")
        if ep is not None:
            ev = params.get(ep)
            if not ev:  # absent OR empty/falsy -> the definition's default (reproduces the
                ev = d.get("evidence_default")  # retired handler's `params.get(ep) or DEFAULT`
            if ev is not None:
                rec["evidence_summary"] = ev
        # occurrence_time_param / provenance_param (EP-24B item B): the two remaining members
        # of the envelope-router family above. An op DECLARES which of its parameters supplies
        # an envelope field, and the interpreter routes it — one general line each, never a
        # per-op case, exactly as target_param and evidence_param already work. The store has
        # always accepted a caller-supplied occurrence_time and the gate has always preserved a
        # handler-asserted provenance; what was missing was only the declaration, so an op
        # needing either had to be written as code. Now it is a field on the record.
        #
        # WHY THESE TWO CAN REFUSE WHERE target_param DOES NOT, which is a difference in the
        # FIELDS and not in the family: target and evidence_summary are optional envelope
        # fields, so a missing param records an absent field, which is honest. occurrence_time
        # and provenance are MINTED BY THE STORE when absent — "now", and "asserted by whoever
        # called". An op that declares "this parameter says when the thing happened" and is
        # then called without it would record a fabricated time as though it were observed:
        # a record lying about the world, which the estate's standing rule refuses rather than
        # shrugs at (accepted-but-cannot-honour REFUSES). The refusal is the gate's own
        # nonconforming-call citation, because the defect is in the CALL and not in the actor's
        # authority to act.
        #
        # THE REQUIRED-OR-DEFAULTED DISTINCTION (EP-27B) is that this is TRUE OF SOME OPS AND
        # NOT OTHERS, and only the op knows which. An observer pin must always be present, so
        # its absence is a fabrication. A law-family record MAY carry the moment it was decided
        # away from the store and usually does not, so its absence is the ordinary synchronous
        # case where the two times coincide by construction — and the store's own value is then
        # the true one, not a stand-in for a missing fact. The op says which, per op, in its own
        # declaration; silence says REQUIRED. A DEFAULTED absence falls back to the envelope
        # default the store already computes AND TO NOTHING ELSE — the field is simply not set
        # here, so no value is invented, substituted or guessed anywhere on this path.
        #
        # AND THE VALUE COMES FROM THE RAW CALLER PARAMETERS (W6b), as target_param's always
        # did. A `param_defaults` entry for this parameter reaches the payload and stops there:
        # it cannot satisfy a REQUIRED pin with a constant nobody stated, and it cannot displace
        # the store's own mint under a DEFAULTED one. The fallback is the store's minted value
        # and nothing else — which is what the paragraph above promises, now true of every path
        # into this field rather than of the one the caller happens to take.
        for decl, field in MINTED_ROUTERS.items():
            param, when_absent = router_param(d, decl)
            if param is None:
                continue
            value = params.get(param)
            if value in (None, ""):
                if when_absent == DEFAULTED:
                    continue
                gate.refuse(actor, opname, "AR-2",
                            f'nonconforming call: parameter "{param}" supplies the envelope\'s '
                            f"{field} for {opname} and was not given — the record would carry a "
                            f"minted {field} as though it had been stated")
            rec[field] = value
        return rec
    return run


def live_definitions(store, as_of=None):
    """Fold CREATE-OP / AMEND-OP / RETIRE-OP into the live definition set: created (or amended
    in place, latest-wins — EP-05C) and not retired."""
    live = {}
    for e in store.all(as_of):
        p = e.get("payload") or {}
        if e["action"] in ("CREATE-OP", "AMEND-OP") and p.get("kind") == "op_definition":
            live[p["name"]] = p["definition"]  # AMEND-OP supersedes in place
        elif e["action"] == "RETIRE-OP" and p.get("name") in live:
            del live[p["name"]]
    return live


def _register_from_definition(gate, store, views, name, d):
    """Bind a definition-born op onto the gate. Idempotent (skips if already live), so the
    live path and boot replay share one registration path. A content-addressed op (one with
    content_params) needs the blob store; without it (a bare build_kernel), the op stays
    UNREGISTERED — surfaced by content_ops_pending_blobs, never silently broken — and registers
    when the full kernel composes blobs in and re-runs replay."""
    if gate.has(name):
        return
    if d.get("content_params") and gate.blobs is None:
        return
    if (d.get("secret_params") or d.get("secret_verify")) and gate.vault is None:
        return  # a secret op needs the vault; without it, honestly pending (secret_ops_pending_vault)
    gate.register(name, {"description": d.get("description", "definition-born operation"),
                         "rules": [d["law_cited"]], "params": d.get("params") or {}},
                  _interpreter(gate, store, views, name, d))


def replay_op_definitions(gate, store, views):
    """Rebuild the definition-born half of the registry from the record alone (boot)."""
    for name, d in live_definitions(store).items():
        _register_from_definition(gate, store, views, name, d)


def content_ops_pending_blobs(gate, store):
    """Content-addressed ops seeded as records but not registered for lack of a blob store —
    the honest ledger of what a bare build_kernel deferred (the full kernel wires blobs and
    registers them). Empty once composed. Makes the deferral discoverable, not silent."""
    return sorted(name for name, d in live_definitions(store).items()
                  if d.get("content_params") and not gate.has(name))


def secret_ops_pending_vault(gate, store):
    """Secret ops (SEAL-SECRET / VERIFY-SECRET) seeded as records but not registered for lack
    of a VAULT — the honest ledger of what a bare build_kernel deferred (the full kernel wires
    the vault and registers them). Empty once composed. The vault twin of content_ops_pending_
    blobs: makes the deferral discoverable, not silent (design/31 J8; EP-19)."""
    return sorted(name for name, d in live_definitions(store).items()
                  if (d.get("secret_params") or d.get("secret_verify")) and not gate.has(name))


def register_opdef_ops(gate, store, views):
    """CREATE-OP / RETIRE-OP: the governed way operations enter and leave the registry.

    The registry is derived state (design 28 §I3): the RECORD is the sole trigger for
    registering/retiring a definition-born op. An on-append listener reacts to the
    committed CREATE-OP / RETIRE-OP record — the same record-driven path boot replay uses.
    So the live registry can never get ahead of the record: since the gate is the sole
    appender (§I2), the handler only RETURNS its draft; the gate commits it (fsync), and
    ONLY THEN does the listener fire and mutate the registry. If the commit faults, no
    record and no registry change — atomic. (Doing the mutation inside the handler, before
    the gate's write, would let a phantom op exist with no record behind it.)"""

    def _on_record(e):
        p = e.get("payload") or {}
        if e["action"] == "CREATE-OP" and p.get("kind") == "op_definition":
            _register_from_definition(gate, store, views, p["name"], p["definition"])
        elif e["action"] == "AMEND-OP" and p.get("kind") == "op_definition":
            # Supersede in place. R18 refuses a content-addressed AMEND-OP when blobs is None at the
            # handler, so a COMMITTED AMEND-OP always registers cleanly here (non-content, or content
            # with blobs present). The old keep-the-old-binding special case is now unreachable and
            # removed — it survived only one process lifetime (replay dropped what live had kept, the
            # I10 break R18 closes). Replay of a content AMEND-OP committed under blobs into a later
            # BARE kernel is the honest-pending path (via _register_from_definition), not this listener.
            gate.unregister(p["name"])
            _register_from_definition(gate, store, views, p["name"], p["definition"])
        elif e["action"] == "RETIRE-OP" and p.get("name"):
            gate.unregister(p["name"])
    store.on_append(_on_record)

    def create_op(actor, params):
        name = params["name"]
        d = params.get("definition") or {}
        if gate.has(name):
            gate.refuse(actor, "CREATE-OP", "ROOT-NEG-6",
                        f'operation "{name}" already exists — a definition may not shadow the active registry')
        validate_definition_shape(gate, "CREATE-OP", actor, name, d,
                                  _peer_definitions(views))
        # RETURN the draft only; the gate commits it and the listener registers the op
        # from the committed record (registry stays behind the record, never ahead). A
        # runtime-created op is tier "ordinary": tiers above ordinary are genesis-only, so
        # the system cannot mint an owner/constitutional op at runtime (no entrenchment vector).
        return {"actor": actor, "action": "CREATE-OP", "object": f"op:{name}",
                "rule_cited": "CAP-IS-LAW",
                "payload": {"kind": "op_definition", "rule_id": f"op:{name}",
                            "polarity": "+", "name": name, "definition": d, "tier": "ordinary",
                            "text": (f"operation {name}: when invoked and its checks pass -> "
                                     f"append a {name} decision citing {d['law_cited']}")}}
    gate.register("CREATE-OP",
                  {"description": "admit an operation by definition record (a recorded amendment)",
                   "rules": ["CAP-IS-LAW"], "params": {"name": "required"}}, create_op)

    def retire_op(actor, params):
        name = params["name"]
        if name not in live_definitions(store):
            gate.refuse(actor, "RETIRE-OP", "BOOT-INT",
                        f'"{name}" is not a definition-born operation — boot and code operations are not retirable by amendment')
        # Tier protection is enforced at the GATE (conservation branch d): a bare RETIRE-OP of a
        # PROTECTED (owner/constitutional) op is refused for EVERY actor including the owner —
        # bare removal IS the protection gap (EP-05C; owner ruling "exit, not surgery"). Ordinary
        # ops retire here as in v1. The handler stays minimal; the gate is the conservation point.
        # RETURN the draft only; the listener unregisters from the committed RETIRE-OP.
        return {"actor": actor, "action": "RETIRE-OP", "object": f"op:{name}",
                "rule_cited": "CAP-IS-LAW", "payload": {"name": name}}
    gate.register("RETIRE-OP",
                  {"description": "retire a definition-born operation (reverts to not-existing)",
                   "rules": ["CAP-IS-LAW"], "params": {"name": "required"}}, retire_op)

    def amend_op(actor, params):
        # AMEND-OP: the mirror image of CREATE-OP (design/29 §2) — one gated act, one appended
        # record, in-place supersession. It REQUIRES the name to be LIVE (CREATE-OP requires it
        # NOT to be); its record carries the new definition with `tier` COPIED FROM THE ACTIVE
        # definition, never from caller params — so amendment cannot elevate or demote, and there
        # is no down moment (the gap is unrepresentable, not merely refused). Authority for a
        # protected target is checked at the gate (branch e): a non-owner amending an owner op is
        # refused there. Amending an ordinary op works under v1 rules (any permitted actor).
        name = params["name"]
        d = params.get("definition") or {}
        if name not in live_definitions(store):
            gate.refuse(actor, "AMEND-OP", "ROOT-NEG-6",
                        f'operation "{name}" is not live — AMEND-OP supersedes an existing definition, it does not create one')
        validate_definition_shape(gate, "AMEND-OP", actor, name, d,
                                  _peer_definitions(views))
        # R18: a content-addressed amendment this composition cannot register (no blob store) is
        # refused, not improvised. The shipped half-fix kept the old binding live and let the record
        # run ahead — but that divergence survives only one process lifetime: on reboot the replay
        # fold hands the new content def to registration, which declines, dropping the LIVE core off
        # the registry (I10: live != replayed). Round-trip identity is a boot condition, so refuse
        # citing BOOT-INT (the call is well-formed — AR-2 would name the wrong reason). Genesis-born
        # content ops differ: never live, honestly pending (content_ops_pending_blobs), no gap.
        if d.get("content_params") and gate.blobs is None:
            gate.refuse(actor, "AMEND-OP", "BOOT-INT",
                        f'"{name}" cannot be amended to a content-addressed definition with no blob store — the '
                        "amendment could not register and would leave the live registry unequal to the replayed one "
                        "(round-trip identity is a boot condition)")
        active_tier = views.op_definitions().get(name, {}).get("tier", "ordinary")
        return {"actor": actor, "action": "AMEND-OP", "object": f"op:{name}",
                "rule_cited": "CAP-IS-LAW",
                "payload": {"kind": "op_definition", "rule_id": f"op:{name}",
                            "polarity": "+", "name": name, "definition": d, "tier": active_tier,
                            "text": (f"operation {name}: amended in place -> append a {name} "
                                     f"decision citing {d['law_cited']} (tier {active_tier} conserved)")}}
    gate.register("AMEND-OP",
                  {"description": "amend a definition-born op in place (supersession; tier conserved)",
                   "rules": ["CAP-IS-LAW"], "params": {"name": "required", "definition": "required"}}, amend_op)
