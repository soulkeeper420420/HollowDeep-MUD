# Atlas research and HollowDeep quest-area designs

Reviewed November 6, 2026. The designs below are **future proposals**. They do not add spells, classes, quest items or playable rooms to this release. The current `skills` command describes existing native abilities; it does not unlock these proposals.

## What Atlas's public help actually says

Source: [official Atlas site and Help Library](https://www.atlasmud.com/), including its publicly embedded help topics, read directly. Search the named topics in the library.

- `druid` emphasizes nature/healing; `necromancer` describes corpse control and poison. These are additions to the ten class names shared with HollowDeep.
- `vampire`, `werewolf` and `hero` describe earned paths. Their help gives five remorts, ten remorts, and mastery of all classes respectively.
- `remort` describes level-30 rebirth, retaining skills/items/gold while relearning spells. `remort_quest` describes automatically checked prerequisites.
- `skills` describes a trainer using skill points and money. `berserk` has a damage/flee tradeoff; `conjure` supplies a companion; `sing` heals nearby players.
- `mental-barrier`, `drain-mana`, `room-sanctuary`, `mirror-images` and `reflect-magic` suggest different support/control roles. The last two pages restrict use to arena scrolls.
- `treasure_map` requires holding the map and describes guarded treasure. `guild` redirects to clans; `clan_rights` describes delegated permissions.

These pages are documentation, not proof of today's server behavior. The `remort` class list omits classes present in the overview, suggesting mixed ages. Exact thresholds and restrictions need in-game confirmation before claiming parity. [Atlas's beta changelog](https://www.atlasmud.com/changelog.html) describes a separate seasonal ruleset; it is not HollowDeep's progression policy.

## Original class and specialization candidates

Keep the ten native class IDs and add versioned specialization data first. IDs 11 and 12 already grant native caretaker/DM authority. A new playable class requires auditing all class comparisons, spell access, equipment, creation, training, saving and class-indexed tables; it cannot safely be inserted as “class 11.”

| HollowDeep proposal | Parent paths | Identity and sample ability | Cost and counterplay |
| --- | --- | --- | --- |
| Warden | Ranger, Fighter | Guard an ally against one announced physical strike; read environmental tracks. | One guarded target; stamina/cooldown; does not negate area damage. |
| Grovekeeper | Ranger, Cleric | Plant a short-lived healing patch and prepare an antidote. | Limited charges/materials; one patch per group; healing cannot stack indefinitely. |
| Gravebinder | Mage, Cleric | Bind one temporary spectral helper and mark a monster for decay. | One pet; upkeep and expiry; no player corpses or duplicate loot/XP credit. |
| Spellblade | Fighter, Mage | Alternate a weapon technique with a temporary elemental infusion. | Consumes mana; replaces an existing infusion; neither extra free attacks nor permanent stat growth. |
| Runekeeper | Mage, Cleric | Prepare one protective rune that breaks when triggered. | Reagent and cast time; explicit duration, dispel rule and maximum reduction. |
| Nightstalker | Thief, Assassin | Spend a short-lived shadow charge to reposition before an attack. | Revealed after attacking; no bypass of locked exits, room gates or PvP consent. |
| Skald | Bard | Choose one group song: recovery, resolve or movement. | Channeling cost; one song per singer/group policy; damage or silence can interrupt. |
| Moonbound / Bloodbound | Later voluntary quest unlock | A distinct transformation or resource-management path. | Needs equipment-form rules, hunger/daylight policy, cooldowns and reversible preview. Do not simply stack both forms' benefits. |

Start with one path and a complete quest. Existing characters should have a preview and a way to decline. Treat specialization, clan rank, native class and staff role as independent systems. A later prestige path can offer a choice of a few earlier techniques; inheriting every powerful ability would erase class identity.

## Skill and spell backlog

All names and mechanics in this table are HollowDeep designs. Numbers are initial test values, not promised balance.

| Proposed ability | Purpose | First playable rule to test |
| --- | --- | --- |
| Brace | Fighter/Barbarian answer to a telegraphed heavy strike | Reduce the next physical hit by a capped amount; cannot attack during the brace window; 20-second cooldown. |
| Rallying verse | Bard group support | Heal only current consenting party members in the room over several ticks; interruptible, no overheal banking. |
| Root snare | Ranger/Grovekeeper control | Briefly delay an eligible monster's movement; bosses resist repeated control; no permanent root loop. |
| Veil echo | Mage defense | One decoy absorbs one eligible basic strike, then expires; no reflection or recursive triggers. |
| Mind ward | Cleric/Runekeeper protection | Temporary resistance to a clearly named mental effect; show remaining duration in a future effects view. |
| Ember seal | Spellblade interaction with elemental encounters | A short weapon infusion changes one attack's element; resistance can counter it; no damage multiplier chain. |
| Siphon spark | Gravebinder resource trade | Spend mana for a bounded chance to drain a monster; ignore targets without mana, forbid allied farming and unlimited net loops. |
| Survey tools | All classes | Record clues, assess hazards and reveal optional routes; successful observation can substitute for combat. |
| Field dressing | All classes, trained | Out-of-combat recovery using a consumable; interruption preserves or spends it according to one documented rule. |
| Salvage craft | Profession progression | Convert eligible unwanted loot to bounded materials through a logged transaction; never duplicate unique or quest items. |

Before adding a spell, define target types, room restrictions, resource cost, duration, cooldown, saving throw, stacking, dispel/death/logout behavior, group attribution and help. Existing known-spell bits have finite storage; reserve an unused ID deliberately and verify serialization. Persistent cooldowns or new skills need a versioned record, not arbitrary bits borrowed from unrelated flags.

## First area: The Lanternbound Trial

Recommended prototype: a **50-room allocation**, aimed at levels 10–15, with a solo route and a group route. Room numbers are placeholders until the Owner checks the actual live world's occupied rooms. Assigning a range authorizes a builder; it does not prove that range is empty or create a finished quest.

Player story: the old beacon has gone dark. Restore three seals, learn which lantern is false, and defeat or outwit the keeper before relighting it. The area should teach preparation, observation and tactical choices without requiring a specific class or a rare random drop.

### Entry requirements and preparation

- Complete a short prerequisite conversation/tutorial and explicitly accept the trial. Recommended level is guidance; if a hard minimum is chosen, explain it at the entrance.
- Obtain a **survey lantern** from the quest NPC. Check a stable quest-item identity, not an editable item name. Make replacement available after loss without granting a second tradeable reward.
- Bring **heat protection** for the forge route: a quest-issued heatwrap, an eligible spell, or a crafted salve can satisfy the same capability check. State whether an item must be equipped, carried or consumed; never make the player guess.
- Acquire a **beacon writ** after proving the first objective. Store completion in the character's journal so giving away an object cannot transfer the prerequisite.
- Optional rope, chalk and antidotes reveal easier routes or extra lore. Do not require these optional supplies to escape or finish the main quest.

Suggested entrance message: “Trial available. Missing: heat protection. Obtain a heatwrap from the quartermaster, use a suitable spell, or prepare a salve. Your survey lantern must be carried.” This is sample future text, not a current command response.

### Fifty-room plan

| Relative rooms | Count | Function |
| --- | ---: | --- |
| 00–05 | 6 | Arrival, quartermaster, trainer, quest briefing, safe recovery and exit. |
| 06–15 | 10 | Survey wing: readable clues, three landmarks, optional caches. |
| 16–25 | 10 | Flooded wing: alternate bridge or breathing-protection route. |
| 26–35 | 10 | Ember wing: protection check, forge puzzle, telegraphed hazards. |
| 36–43 | 8 | Guardian wing: encounter rooms and alternate noncombat objective. |
| 44–47 | 4 | Beacon approach, checkpoint, final puzzle, guardian chamber. |
| 48–49 | 2 | Reward hall and reliable return route. |

The counts total 50. Builder review should find unreachable rooms, one-way traps and unintended bypasses before opening an entrance to the live world. Current `hbuild` supports room names/descriptions/exits; monster, item and scripted-objective authoring needs additional reviewed tooling.

### Objectives and state

Use stable quest/objective IDs and server-observed events:

```text
offered → accepted → three seals recovered → beacon prepared
        → keeper resolved → reward pending → reward claimed
```

The three wings can complete in any order. Survey credit comes from observing the required landmark, puzzle credit from the actual validated solution, and encounter credit from participation in that specific attempt. Do not accept a client-written “done” flag, a renamed item, or presence in the final room as proof of the whole quest.

The final encounter telegraphs a lantern flare. Players may brace, use the prepared ward or move to cover before it resolves. An observation route exposes the false lantern and weakens the keeper, giving explorers and small groups a viable approach. Tune latency and text visibility for mobile players; avoid mandatory split-second typing.

Start with a shared area and per-character objective state. Shared gates should not allow another player's action to bypass a personal prerequisite. Reserve a short final attempt for an eligible party, with a timeout and recovery rules, before considering fully instanced 50-room copies. Unlimited instances need room-ID allocation, cleanup and persistence work that the current engine does not supply.

### Gear and reward rules

- Keep story items separate from marketable loot. Define drop, give, sell, death and replacement behavior for every required item.
- Check every entrant, including followers and teleported characters, at the relevant server-side gate. Staff testing overrides must be explicit and cannot mint normal rewards.
- Evaluate expiring protection at the hazardous action; warn before its expiry and provide retreat. Never trap someone because their effect or lantern charge expired.
- Give first completion a title/badge and a **choice** of similarly budgeted weapon, armor or focus. Validate class compatibility, inventory capacity and existing unique rewards before consuming tokens.
- For the prototype, make repeat completions offer modest supplies or reputation. Avoid compulsory daily attendance and a repeatable best-in-slot item faucet.
- If adding quest XP, use a fixed, separately tuned amount outside monster bonus events. A design target could be part of one normal level, with a published maximum; the final amount depends on the new curve and measured completion time.
- Make reward claims recoverable and idempotent across crashes. Journal completion, item placement and any XP/gold award must reconcile as one transaction; two independent successful saves are not enough.

## Further areas and endgame ideas

| Proposal | Intended audience | Preparation and objective | Reward direction |
| --- | --- | --- | --- |
| Sunken Archive | Levels 15–20 | Water-breathing or a dry bypass; recover inscriptions and open a seal using clues. | Utility spell lesson, lore journal, aquatic travel cosmetic. |
| Glassroot Conservatory | Levels 20–25 | Antidote kit and herbal samples; restore an ecosystem rather than merely kill its inhabitants. | Grovekeeper trial, profession recipe, garden decoration. |
| Ashen Observatory | Supported levels 25–30 | Several elemental defenses obtained through choices; rotate mechanisms and interrupt an announced ritual. | Runekeeper/Spellblade trial and bounded sidegrade gear. |
| Hall of Former Names | Future remort threshold | Personal quest completions, chosen keepsakes and a preview of the reset; final voluntary confirmation outside combat. | First remort/specialization; no forced reset or staff-role changes. |
| Clan Expedition | Midgame groups | Shared preparation plus individual contributions, with catch-up access for late members. | Hall decoration and reputation before shared financial assets. |
| Wandering survey | All supported levels | A generated clue points to an approved reachable region; a tool reveals a guarded cache. | Exploration rewards with per-attempt IDs and a bounded generation pool. |

Do not place an item needed for entry exclusively behind the same gate. Offer deterministic alternatives to rare drops, readable hints, meaningful retreat and a reset/recovery NPC. Difficulty should come from choices and encounters, not discovering undocumented prerequisites.

## Acceptance criteria for a quest release

Test solo and grouped entry, different classes, missing/wrong/renamed gear, equipment removed mid-step, inventory full, death, logout, server restart, expired buffs and abandoned parties. Test followers, summon/teleport, carrying an item in a container, trading it during a step, repeated clicks/commands and simultaneous claims. Every path must either preserve a recoverable attempt or explain how to restart without duplicating rewards.

Ship player walkthrough hints, full staff recovery instructions, a builder map, item/monster IDs, prerequisite rules and reward budgets with the implementation. Keep solutions behind optional spoiler sections. The first release should prove one area end to end before expanding into a large remort campaign.
