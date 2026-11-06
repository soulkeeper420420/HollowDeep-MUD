# HollowDeep future release plan

Planning guide, November 6, 2026. Milestones are ordered by dependencies, not promised dates. Source publication, testing and live installation are separate states. See [release notes](../CHANGELOG.md) for completed source changes and [confirmed live notes](LIVE_CHANGELOG_2026-11-06.md) for the latest operator evidence.

| Milestone | Concrete result | Ready when |
| --- | --- | --- |
| Command discovery and staff operations | Searchable help, existing skill list, role labels, staff-only clan, builder ranges, DM guide and bounded bonus events. | Native multiplayer, private-chat permissions, save/reload and guarded updater checks pass; operator verifies the new live commands after installation. |
| Progression foundations | One XP/level/fee API, bounded stats/rewards, repaired monk progression and accurate training displays. | Existing saves load; threshold/death/overflow boundaries and all ten classes are tested. No curve migration until private character inventory and recovery policy are ready. |
| Levels 26–30 with purpose | A smooth curve proposal selected from measured play, coherent training fees, new titles and a supported level-30 content milestone. | Current characters retain agreed progress; combat, death and trainer costs are usable at normal and event rates. |
| The first quest area | The Lanternbound Trial: 50 rooms, deterministic preparation, several objective types, a final encounter and safe reward claims. | Entry requirements, item replacement, group contribution, disconnects and interrupted claims are tested. |
| Social organizations | Player clan invitations, ranks, chat, notices and leadership transfer; staff clan remains separate. | Membership and permissions persist without grants of game staff authority. No treasury or shared items until transactions are recoverable. |
| One specialization | One complete Warden, Grovekeeper, Runekeeper or other path, earned through a quest and supported by help. | Acquisition, cooldowns, class interactions, save/reload and revocation/reset are tested. Native class IDs remain safe. |
| Levels 31–40 and professions | Several encounter bands, exploration contracts, gathering/crafting recipes and bounded resource sinks. | Content and economy measurements justify the extension; old zones and new players remain relevant. |
| Voluntary remort | Preview, eligibility quest, explicit confirmation, one tested reset policy and a recovery journal. | All inventory/gold/spell/proficiency rules are written and crash recovery proves no double reset. |
| Longer-term world systems | Supported levels to 50, player housing, shops, clan vaults and opt-in competition. | Ownership, transactions, capacity, balance and recovery foundations exist. These are separate releases, not one large migration. |

## Smaller improvements that can ship between milestones

- An effects view listing real buff durations and skill cooldowns, with accessible plain-text output.
- A quest journal showing missing prerequisites, the next objective and optional hints.
- Group finder and scheduled events with opt-in notices and moderation controls.
- A builder review queue, exit validation and a preview world before public area release.
- Starter equipment choices and a tutorial that teaches training, spells, skills, fleeing and saving.
- A stable item inspection view showing class/level requirements and quest restrictions.
- Personal exploration and profession achievements that grant titles or cosmetics before permanent combat bonuses.
- Optional sound cues with complete equivalent text; configurable output for small phone screens.
- A public release board that distinguishes newly published source from verified live changes.

## Design decisions to settle before implementation

Start with a small population and playable solo alternatives. Decide the desired hours per progression band, PvP policy, permanent-death/XP-loss policy, group contribution rules, remort retention and whether alternate characters share any account-level progress. Existing character logins do not establish one human/account, so do not promise alt-proof rewards.

Keep reward multipliers in one documented calculation. Keep staff authority independent of levels, clans, purchased skills, quests, remorts and rare gear. Keep quest requirements visible before a player spends supplies or enters a dangerous area.

## Design library

- [Level investigation, XP curves and migration plan](LEVELS_AND_EXPERIENCE.md)
- [Spreadsheet-friendly level 1–50 comparisons](XP_CURVE_PROPOSALS.csv)
- [Atlas research, class/skill/spell ideas and quest-area blueprint](ATLAS_RESEARCH_AND_QUEST_DESIGN.md)
- [Remort and specialization options](PROGRESSION_OPTIONS.md)
- [Player clans, guilds and shared property](CLANS_AND_FEATURES.md)
- [Builder commands and permissions](BUILDING_GUIDE.md)

A future feature is complete when a player can discover it, use it, understand its limits and retain correct progress after reconnecting, and staff can diagnose and recover failures. A command name or a finished design document alone does not establish that behavior.
