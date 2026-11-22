# AtlasMUD flag screenshots — HollowDeep design/reference notes

**Recorded:** November 21, 2026  
**Evidence:** six user-supplied GMud AtlasMUD screen captures, made between
22:57 and 23:02 local time. Captures show a player flag list, an object flag
list, a monster flag list, and several pages of raw named player flags.  
**Status:** REFERENCE / DESIGN BACKLOG ONLY. No AtlasMUD source, runtime
implementation or authoritative flag mapping was supplied, and no HollowDeep
production/native game files were modified for this note.

The screenshots give visible **labels and numbers**. They do **not** prove
how an individual feature is implemented, whether flags are persisted,
whether corresponding commands exist, or that all captures are from the
same revision. Numbers below are Atlas display positions only, **never
HollowDeep C enum constants or offsets**. Do not directly copy Atlas
source, proprietary text, game data, or assets into HollowDeep.

## 1. Player flags and status

Screenshots include readable player status names in a numbered flag
table and multiple screens of named P-prefixed flags.

| Atlas display flag / named equivalent where visible | HollowDeep idea | Evidence caution |
| --- | --- | --- |
| 19 "see prompt" / PPROMP | Configurable numerical HP/MP/Breath prompt | HollowDeep already has a native ANSI/compact HUD; keep preference separate from resource state |
| 27 "ansi color on" / PANSIC | Accessible color and no-color presentation | Don't borrow the Atlas bit offset |
| 15 "wimpy" / PWIMPY, 10 "no auto attack" / PNOAAT | Opt-in conservative combat controls | Verify existing native combat flags and defaults first |
| 5–8 hide descriptions/room names/exits | Configurable display density | Never hide a combat/safety warning |
| 32 "flying", 26 "levitating" | Separate player movement effects from mount flight | Flying flags should not bypass native exit/room checks |
| 67 "dragon" / PDRAG, 68 "bat", 69 "gray wolf", 97 "morphed" | Temporary transformation class abilities | **Transformation is not mount ownership** |
| 74 "hired", 75 "guild leader", 76 "undead", 82 "no follow" | Distinguish hired companions, clan rank, undead servants and follow preferences | Necromancer Raise Corpse and universal Conjure remain independent |
| 83 "duel", 84 "frozen", 86 "afk" | Duel opt-in, restrained movement, AFK availability | Duel needs explicit opt-in and anti-abuse rules |
| 92 "remorting" / PPREMORT | Optional rebirth workflow | Rebirth must use a journal and atomic save transaction, not a new ad hoc flag |
| 101–103 "quest1", "quest2", "quest3" | Multi-stage, independently verifiable quests | Do not encode quest state in borrowed numeric flags |
| 105 "no-quest", 106 "quieted" | Moderation/quest eligibility states | Keep authority/moderation state distinct from gameplay rewards |
| 88 "sanctuary", 89 "fireshield", 90 "reflect magic", 91 "mirror", 95 "concentrate", 96 "precision" | Ability/status-effect UI and class mechanics | Spell names are *flag labels*, not proof of current spells/abilities |
| 110 "on network", 113 "player corpse", 114 "system bot" | Networking, corpse identity and system actors | Requires strict source/role validation, not user-editable bits |

### Important discrepancies inside the screenshots

The human-readable list and the raw P-prefixed list are **not a
perfectly consistent one-to-one dictionary**:

- Display number **16** is shown as **"avatar"** on one capture, while
  the named P-flag screen shows **PEAVES = eavesdropping mode** at 16.
- Display number **64** is shown as **"null"**, while the named
  P-flag screen shows **PINDOR = Player is indoors** at 64.
- Display number **104** is shown as **"safe"**, while a named P-flag
  screen shows **PTMPLAW = temporary lawful after a PK** at 104.

These may be different Atlas versions, flag-display contexts or label
changes; the screenshots do not establish which. **Never infer exact
C constants from a single number** without validating the exact
target source. In particular, staff or security flags such as
DM invisibility (11) and authentication (50) must not be repurposed.

## 2. Monster/creature flags

The numbered monster flag screen includes:

| Atlas monster flag | Candidate application | Safeguard |
| --- | --- | --- |
| **75 MOUNT** | Identify a creature eligible to be a ridden mount | A flag alone does not establish ownership, riding or Endurance |
| **54 HIREABLE**, **55 HIRED** | Hired mercenaries or hireable NPC helpers | Separate from permanent Conjure and temporarily raised undead |
| **76 NOWANDER**, **81 WANDERING MOB**, **85 ACTIVE** | AI movement, stabled/nonwandering creatures, scheduled actors | Respect room/respawn and leash rules |
| **58 TRAINER**, **73 VENDOR**, **82 HEALER** | Native specialized NPC templates for the World Builder | Test behavior in disposable native area before export |
| **72 TOKEN COLLECTOR**, **88 LOTTERY DEALER** | Quest-token turn-in and future event NPCs | Reward receipts must be once-only and server-authoritative |
| **83 GROUP LEADER**, **84 GROUP MEMBER** | Squad monster behavior or encounter groups | Do not conflate with player party data |
| **87 RAISED** | Identifying raised undead | HollowDeep already has Raise Corpse persistence/death safeguards; preserve current semantics |
| **9 FOLLOWS ATTACKER**, **77 PREVENT FLEE** | Reactive combat encounters and chase behavior | Avoid infinite pursuit or no-escape traps |
| **29 BREATH TOG 1**, **30 BREATH TOG 2** | Possible monster breath-attack toggles | **Not** evidence of the HollowDeep player Breath travel resource |
| **78 AGGROS LAWFUL**, **79 AGGROS CHAOTIC** | Alignment-dependent PvE aggro design | Must not bypass safe-room, PvP or level protection |

The Atlas creature MOUNT label is a useful **conceptual signal** for
Round79 mount research. HollowDeep's actual mount contract remains
a durable character-epoch-bound roster with **one active mount**, a
separate **mount Endurance** resource, verified wilderness tile/terrain,
and native movement checks. Do not mark a generic creature as owned
merely because it carries a MOUNT bit.

## 3. Item/object flags

The item table provides several high-value ideas. All numbers here
are Atlas item positions, in a separate namespace from player and
monster flag positions.

| Atlas item flag | HollowDeep use | Implementation caveat |
| --- | --- | --- |
| **7 CONTAINER**, **8 WEIGHTLESS** | Earnable weightless bag via rebirth gifts | Bounded capacity, nested inventory saving, no unlimited weight bypass |
| **48 Legend**, **76 ARTIFACT**, **82 REMORT**, **87 GIFT** | Legendary/legacy/rebirth gear | Character epoch binding, controlled acquisition, atomic receipt |
| **74 PERSONAL**, **91 PLY-NOSELL**, **92 PLY-NODROP** | Bind-to-character and limited trade/drop | Restrict transfers consistently across vendors, inventory and death |
| **75 RANDOMLOOT**, **96 OTREASURE**, **101 OQUEST** | Quest rewards/loot tables/guarded treasure | Unique reward claims and protected quest items |
| **35–47 class labels** including **44 VAMPIRE**, **45 WEREWOLF**, **46 NECROMANCER**, **47 SPEC CLASS** | Class-restricted item eligibility | These are **item flags**, not proof of class creation or skill implementation |
| **15 ENCHANTED**, **60 TEMPENCHANT**, **62 SLOT**, **65 STATS**, **88 EXCEPTIONAL** | Limited crafting, enhancements and equipment slots | Reserve structured versioned data; avoid changing native object ABI blindly |
| **54 HERBREW**, **55 HERBRINGEST**, **56 HERBPASTE**, **57 HERBAPPLY**, **58 PREPARING**, **59 PREPARED** | Alchemist/herbal crafting workflow | Ingredient decrement and output must commit atomically |
| **64 TRADER**, **67 NOSELL**, **68 DONATED**, **89 CRAFTED** | Shops, donations and maker attribution | Prevent price cycling, item dupes and restricted resales |
| **85 THROW**, **86 DYABLE**, **90 TWO-HAND** | Throwables, dyes, and hand-slot/dual-wield rules | Equipment legality must be server-side |
| **70 NOSAVE**, **77 NODROP**, **98 OSPKEY** | Temporary items, secure locks and quest keys | No bypass of protected item custody or save recovery |

The screenshot's names are not a complete specification: e.g.,
WEIGHTLESS does not tell us if Atlas uses a whole-container reduction,
nested weight rules, capacity constraints or an item-only special case.

## 4. Which ideas to reuse first

These priorities are **original HollowDeep designs inspired by the
visible names**, not copied Atlas implementations:

1. **Mounts and Endurance:** Start from the *existing* HollowDeep
   Round79G pure-rule species/terrain tests and Round79P privately
   verified Breath/native movement checkpoint. Investigate whether
   HollowDeep's own creature template flag namespace has a safe
   mount-specific marker, but keep durable rider/mount identity,
   stables and Endurance in a versioned, epoch-bound record. Horse,
   warhorse, dire wolf, nightmare, griffin, dark dragon are already
   proposed; do not add real mount movement before atomic tests.
2. **Rebirth/legacy equipment:** Propose a weightless bag, one
   named legacy gift and an item that gains a bounded affix after
   a verified rebirth. Use existing Round74 progression/receipts.
   No copied object bit positions, no temporary staff authority,
   no silently retrofitted live items.
3. **World Builder NPC roles:** Provide builder-selectable
   trainer/vendor/healer/token-collector/quest-giver templates
   with valid native creature IDs. Start with read-only role
   inspection; native placement and respawn must preserve existing
   creatures, inventories and exit records.
4. **Herbal crafting:** Model prepare -> brew/apply as a small
   class/profession prototype; include ingredients, cooldown,
   skill level, and a one-transaction consume/create test.
   Candidate for the Alchemist class, not automatically enabled
   for everyone.
5. **Events and parties:** Duel opt-in, token collector,
   lottery/event dealer, coordinated monster groups and
   visual status flags are options for later milestones.
   Fairness, cash/gold custody, arena consent and claim
   idempotency must precede gameplay implementation.
6. **Player quality of life:** Retain ANSI/plain display choice,
   show the distinction between Breath and mount Endurance,
   and support readable prompts and clear interruption messages
   without copying Atlas UI or adding unauthorized player flags.

## 5. Porting and testing rules

- Inspect HollowDeep's actual native \`mtype.h\`, \`mstruct.h\`,
  \`global.c\`, flag macros, and serializer from a **disposable
  ELF32 source tree** before touching definitions.
- Verify per-flag namespace, bit/byte capacity, reserve IDs,
  class/role permissions and the actual game save contract.
  A number reused across an Atlas screenshot and HollowDeep
  is *not* evidence of binary compatibility.
- Prefer explicit versioned sidecar state for new persistent
  systems instead of modifying the legacy ELF32 \`creature\`
  or \`object\` binary layout. Mount and remort mutations must
  be revisioned, replay-safe and atomic with character saves.
- Keep Necromancer Raise Corpse, universal Conjure, hired NPCs,
  mounts and player transformations distinct; test ownership,
  combat death, logout, reboot and recreation separately.
- Use the tested isolated World Builder, one-room/area fixtures,
  native ELF32 compiler and real socket replay. Reject corrupt,
  ambiguous, symlinked or stale save and map input.
- Never restart \`hollowdeep.service\`, patch the live world,
  modify live player saves, or publish private source excerpts,
  credentials, synthetic world data or logs without approval.

## Existing HollowDeep references

- [Round79G mounts and Breath](ROUND79G_MOUNTS_AND_BREATH.md) —
  mount species profiles and early terrain rules, not yet mounts.
- [Round79 gameplay milestones](ROUND79_GAMEPLAY_QOL.md) —
  later private native Breath and rest validation. At the time of
  these notes, Round79P's +15 atomic and rest command/socket checks
  are verified; Round79Q's **real connected wall-clock tick**
  remains unverified.
- [Existing Atlas comparison](ATLAS_COMPARISON.md) and
  [Atlas quest research](ATLAS_RESEARCH_AND_QUEST_DESIGN.md) —
  context from earlier Atlas public materials.
- [Base class and race proposals](design/base-class-and-race-expansion.md)
  and [progression options](PROGRESSION_OPTIONS.md) —
  original HollowDeep class and rebirth ideas.

**Decision:** Record this research in GitHub only. No Atlas flag ID
mapping, native feature, player/item/monster stat or live production
configuration is changed by this document.
