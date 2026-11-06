# Hollowdeep and The Secret of Atlas

The comparison target is the **classic Secret of Atlas**, as requested by the host. Hollowdeep uses original Mordor 3.00 with its own additions. Atlas remains an inspiration and comparison point; its world text, source, assets and help pages are not copied into Hollowdeep.

The Atlas facts below were checked against its [official classic overview](https://www.atlasmud.com/) on 2026-11-05. Hollowdeep's column describes this source version. The newly prepared native features require installation before players can use them.

| Area | Classic Atlas | Hollowdeep |
| --- | --- | --- |
| Character paths | 15 advertised classes: 12 starting and 3 remort. | Ten original Mordor classes. Remort and additional classes remain roadmap items. |
| Progression | Class abilities and advancement through the realm. | Original XP/gold training, a new eligibility/progress view, and stance strength at levels 1, 5 and 10. |
| Exploration | World quests. | Original Mordor world plus four persistent survey Chronicles; their rewards are cosmetic badges. |
| Social play | Clans. | Original follow/group/party communication. A new clan-management system is not implemented. |
| Property and trade | Player shops and homes. | Original game commerce; player-owned shops and homes remain roadmap items. |
| Access | Browser play and native MUD clients. | Native access confirmed at `172.233.176.81:4040`; website transport requires the separate bridge installation. |
| Help | A searchable web help library. | Source-based Realm Codex, in-game help, and player/staff/server guides. |
| Sound | MUD Sound Protocol support. | No added MSP sound implementation. |

Hollowdeep also adds its own owner/admin/mod hierarchy, saved moderation state and audited staff actions. This is a description of Hollowdeep's implementation, not a claim that it matches Atlas's staff system.

## Keep classic and beta comparisons separate

Atlas's separate [beta changelog](https://www.atlasmud.com/changelog.html) describes seasonal resets, permanent 25× XP/gold bonuses and newer help behavior. Hollowdeep does not implement those reset or bonus policies. Existing Hollowdeep saves are retained by its updater; importing a destructive seasonal reset would require a separate, explicit design decision.

## Development priorities

1. Keep the working native connection and original save compatibility stable.
2. Complete deployment and validation of stances, progression guidance and staff roles.
3. Connect the website to the same live world through its authenticated TLS bridge.
4. Expand original quests and progression after evaluating actual play and reward balance.
5. Design clans, player housing, shop ownership and additional class/remort systems as separately tested features.

For each future release, update this comparison with **implemented**, **deployed** or **planned** status. Similarity is assessed feature by feature; the list is not a claim of Atlas compatibility or parity.
