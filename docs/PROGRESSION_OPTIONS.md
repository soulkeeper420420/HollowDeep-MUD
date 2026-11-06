# Remorts and possible new classes

Status: design recommendations, not implemented character changes. Research checked November 5, 2026 (America/New_York).

## What Atlas publicly documents

The [classic Secret of Atlas overview](https://www.atlasmud.com/) advertises **15 classes: 12 available at creation and three earned by remorting**. This supports using an earned second progression path as a comparison point. The overview alone does not establish detailed remort rules or builder allocations. A later [help-library investigation](ATLAS_RESEARCH_AND_QUEST_DESIGN.md) records additional public evidence and inconsistencies; use it for the current research notes. Hollowdeep's 50-room default is the host's requested design, not a verified Atlas specification.

The separate [Atlas beta changelog](https://www.atlasmud.com/changelog.html) describes three-month resets and permanent 25x bonuses. It explicitly lists resets of levels, items, spells, skills, stats, gold and other property. That seasonal policy is distinct from a voluntary remort. Hollowdeep's implemented events are temporary, bounded monster-reward multipliers; they do not reset characters.

## Recommended first remort design

Make remort voluntary, with a preview followed by explicit confirmation. A provisional unlock at level 25 plus a dedicated quest is a starting proposal for playtesting, not an engine-imposed level cap: Mordor's XP table has 25 entries and its code extrapolates requirements afterward.

Preserve the login, character name, cosmetic badges and exploration history. Preview exactly which progression values would reset before committing. Proposed first cycle: return to level 1, recalculate the selected class's starting HP/mana and combat statistics, reset level-derived proficiencies and apply that class's starting spell rules. Do not carry high-level combat values into a level-1 character. Avoid permanent multiplicative stat bonuses; offer a specialization choice, title or cosmetic reward first.

Inventory, gold, bank/property interactions and cross-class spell retention require an explicit policy before implementation. A high-level item may need storage or an equip restriction, not silent deletion. Staff roles and room assignments must never be earned or escalated through remort. Native DM/caretaker characters should be ineligible.

A reliable implementation needs an atomic remort transaction covering both the original character save and a versioned progression journal, with a recoverable pre-remort backup and a transaction ID that prevents applying a reset twice. Ordinary save/quit is not sufficient to make two independent files atomic.

## Candidate specializations

Prefer specializations layered on the ten existing classes first. Mordor uses numeric class IDs throughout training, titles, spells and combat; IDs 11 and 12 already mean caretaker and DM. Adding a class by incrementing an enum could accidentally create staff authority.

| Candidate | Starting path | Distinct play style | First mechanic to prototype |
| --- | --- | --- | --- |
| Warden | Ranger or fighter | Defensive exploration and group protection | Limited protective stance and tracking utility. |
| Spellblade | Fighter or mage | Alternating weapon strikes and magic | A short-lived weapon enchantment with a mana cost. |
| Runekeeper | Mage or cleric | Preparation and area support | One active ward with a clear duration and replacement rule. |
| Shadowdancer | Thief or assassin | Positioning and escape | A movement trick with a cooldown; no permanent invisibility. |
| Spiritcaller | Cleric or bard | Support through a bounded companion | One temporary companion, with explicit ownership and logout cleanup. |

These are original Hollowdeep proposals, not claims about Atlas's class roster. Implement one specialization end to end before adding several: training, help, equipment, damage/healing balance, persistence, revocation/reset behavior and multiplayer tests all need coverage.

## Suggested order

1. Install and observe builder permissions and timed reward events.
2. Measure ordinary leveling time and economy growth with and without x2 events.
3. Prototype one specialization on a disposable world, leaving native class IDs intact.
4. Agree on the remort preview/reset policy and prove backup/recovery before enabling it.

No remort, seasonal wipe or new class is activated by the builder/event updater.

For complementary social progression, profession guilds and cooperative content, see [clans and feature options](CLANS_AND_FEATURES.md).

## Detailed follow-up

See [levels and experience](LEVELS_AND_EXPERIENCE.md) for actual engine thresholds, proposed level 1–50 curves, training fees, monk/stat hazards and migration checks. The suggested unlock at 25 above is provisional; a supported level-30 milestone followed by an optional quest is another candidate. [Quest-area designs](ATLAS_RESEARCH_AND_QUEST_DESIGN.md) describe gear requirements, specific objectives and recoverable rewards. None changes the live progression system.
