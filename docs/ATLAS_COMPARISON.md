# Hollowdeep and The Secret of Atlas

The comparison target is the **classic Secret of Atlas**, as requested by the host. Hollowdeep uses original Mordor 3.00 with its own additions. Atlas remains an inspiration and comparison point; its world text, source, assets and help pages are not copied into Hollowdeep.

The Atlas facts below were checked against its [official classic overview](https://www.atlasmud.com/) on 2026-11-05. Hollowdeep's column describes this source version. The newly prepared native features require installation before players can use them.

| Area | Classic Atlas | Hollowdeep |
| --- | --- | --- |
| Character paths | 15 advertised classes: 12 starting and 3 remort. | Ten original Mordor classes. Remort and additional classes remain roadmap items. |
| Progression | Class abilities and advancement through the realm. | Original XP/gold training, a new eligibility/progress view, and stance strength at levels 1, 5 and 10. |
| Exploration | World quests. | Original Mordor world plus four persistent survey Chronicles; their rewards are cosmetic badges. |
| Social play | Clans. | Original follow/group/party communication. The new source adds a staff-only clan; player-run clans remain planned; see [clan and feature options](CLANS_AND_FEATURES.md). |
| Property and trade | Player shops and homes. | Original game commerce; player-owned shops and homes remain roadmap items. |
| Access | Browser play and native MUD clients. | Native access confirmed at `172.233.176.81:4040`; website transport requires the separate bridge installation. |
| Help | A searchable web help library. | Source-based Codex, searchable registered-command help, a skill catalog, role-aware DM help and player/staff/server guides. |
| Sound | MUD Sound Protocol support. | No added MSP sound implementation. |

Hollowdeep also adds its own owner/admin/mod/implementor hierarchy (Mod and Implementor are peers), saved moderation state and audited staff actions. The builder/event source update adds owner-assigned room ranges (50 rooms by default), scoped DM tools and timed monster XP/gold events. These additions require their own native installation. The 50-room default follows the host's request; the retrieved Atlas overview does not establish Atlas's builder allocation rules.

## Keep classic and beta comparisons separate

Atlas's separate [beta changelog](https://www.atlasmud.com/changelog.html) describes seasonal resets and permanent 25× XP/gold bonuses. Hollowdeep retains saves and offers bounded, temporary monster-reward events; it does not implement the beta's resets or permanent multiplier. See [remort and class options](PROGRESSION_OPTIONS.md) for the researched comparison and proposed next steps.

## Development priorities

1. Keep the working native connection and original save compatibility stable.
2. Complete deployment and validation of stances, progression guidance and staff roles.
3. Connect the website to the same live world through its authenticated TLS bridge.
4. Expand original quests and progression after evaluating actual play and reward balance.
5. Design clans, player housing, shop ownership and additional class/remort systems as separately tested features.

For each future release, update this comparison with **implemented**, **deployed** or **planned** status. Similarity is assessed feature by feature; the list is not a claim of Atlas compatibility or parity.

## Detailed research update — November 6, 2026

The [class, skill, spell and quest investigation](ATLAS_RESEARCH_AND_QUEST_DESIGN.md) examines Atlas's public embedded help library and separates its documented rules from original HollowDeep proposals. The [level study](LEVELS_AND_EXPERIENCE.md) analyzes HollowDeep's actual engine, with three proposed XP curves. See [future releases](FUTURE_RELEASES.md) for implementation dependencies.
