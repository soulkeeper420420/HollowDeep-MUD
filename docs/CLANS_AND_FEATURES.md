# Clans, guilds and future HollowDeep features

Status: the new source implements the **HollowDeep Staff** clan (`staffclan`), with role-derived membership and private online chat. It still requires live installation. Player-created clans, profession guilds, treasuries and other proposals below remain unimplemented. Reviewed November 6, 2026. See [staff guide](STAFF_GUIDE.md) for current staff-clan rules and [updated Atlas research](ATLAS_RESEARCH_AND_QUEST_DESIGN.md) for public help findings.

## What exists and what Atlas confirms

The [classic Secret of Atlas overview](https://www.atlasmud.com/) advertises clans, world quests, player shops, homes, fifteen classes (twelve starting and three remort), browser play, a help library and MSP sound. Its overview alone does not explain detailed clan rules. The later [help-library investigation](ATLAS_RESEARCH_AND_QUEST_DESIGN.md) adds evidence about delegated clan rights; banking, member limits, ownership transfer and builder allocations still need verification. The designs below are HollowDeep proposals, not claims about Atlas's rules.

The separate [Atlas beta changelog](https://www.atlasmud.com/changelog.html) describes seasonal wipes, including clans, homes and banks. That is a beta policy, not evidence of how classic clans work. No wipe is proposed here.

HollowDeep already has native parties (`follow`, `group`, `gtalk`), character classes and training, commerce, persistent exploration Chronicles, combat stances and staff roles. Its original Mordor source also contains `pledge` and `rescind` in `command10.c`, registered in `global.c`. Those commands use a two-kingdom flag system, designated rooms and NPCs, rewards or penalties, and access/combat rules. They are not a general player-created clan registry. Availability in play depends on the world's configured rooms and NPCs.

Use a new persistent clan registry rather than repurposing kingdom flags. Keep three kinds of authority separate: a character's class and training, a player's organization rank, and game staff permissions. A clan leader must not become a Moderator, Admin or builder merely by leading a clan.

## Clans versus guilds

Recommended initial model: one player-run clan per character, with optional membership in several NPC profession guilds later. A clan is a social organization; a profession guild offers training, reputation and contracts. If the host wants both “clans” and “guilds” to mean player-run groups, use one underlying organization system with a chosen display label rather than two incompatible membership systems.

Start with one-clan membership because invitations, chat, leadership and shared rewards are easier to understand. Alliances and multiple membership can follow after defining how conflicts and treasury rights work. Decide whether limits apply per character or account before adding competitive rewards; the current character login alone cannot reliably identify alternate characters as one person.

## Recommended first clan release

Proposed command family: `hclan`. These examples are designs, not commands available in this updater.

| Capability | Proposed behavior | Who controls it |
| --- | --- | --- |
| Found a clan | Reserve a unique name and short tag; initially require staff approval, with no automatic gold deduction. | Admin/Owner approves a player leader. |
| Invite and join | Invitation names a saved character and expires; the target explicitly accepts. | Leader/Officer invites; target accepts. |
| Roster and notice | Persistent roster, ranks, description and message of the day. | Members read; Leader/Officer edits notice. |
| Clan chat | Online members only; bounded text, spam control, existing mutes respected. | Members send; moderation remains enforced by staff. |
| Promote or remove | Only lower clan ranks can be changed; Officers cannot create peers or replace the Leader. | Leader manages Officers; Officers manage lower ranks. |
| Leave | Leave without deleting the character or losing ordinary possessions. | Each member; Leader transfers leadership first. |
| Transfer leadership | The proposed successor explicitly accepts; the old leader remains until the transfer commits. | Current Leader and successor. |
| Disband | Explicit confirmation, audit and archived record; shared assets require a settlement policy. | Leader; exceptional staff action is separately audited. |

Suggested ranks: Recruit, Member, Officer and Leader. “Clan Leader” avoids confusing organization leadership with the game-wide Owner role. Clan moderation only affects membership and clan channels; it cannot kick a character off the server, assign staff, change another player's class or grant world-editing access.

Example workflow for a future release: `hclan invite Aria`, `hclan accept lanterns`, `hclan roster`, `hclan say Meet at the hall`. Final syntax and help should ship together with the implementation.

## Expansions that are possible

| Feature | Player benefit | Requirements before enabling |
| --- | --- | --- |
| Clan halls | A shared meeting place with a noticeboard and approved services. | Host-approved rooms, membership access checks, safe exits and ownership transfer. Clan membership does not confer `hbuild` access; the Owner assigns builders separately. |
| Treasury and dues | Members contribute toward hall upgrades and events. | One recoverable transaction for wallet and treasury, receipt IDs, withdrawal permissions, daily limits and an immutable ledger. Joining fees must not deduct gold if joining fails. |
| Shared vault | Store supplies for members. | Real item transfer with duplicate protection, withdrawal records, object restrictions and restart recovery. Start with a treasury before handling serialized items. |
| Cooperative quests | Survey regions, defeat encounter targets or deliver supplies together. | Server-verified contribution, unique claim IDs, level guidance, duplicate prevention and clear eligibility for new/leaving members. |
| Clan progression | Earn hall decorations, titles, banners and convenience unlocks. | Persistent milestones and caps. Start with cosmetic rewards to avoid an escalating combat advantage for established groups. |
| Profession guilds | Crafting, gathering, reputation and repeatable contracts. | Recipes, resource sources/sinks, trainer rules, skill persistence and cooldowns. These can complement existing classes. |
| Alliances and rivalries | Shared events and optional competition. | Consent, membership visibility rules, shared-chat moderation and a policy for switching clans. |
| Territory and clan wars | Organized competitive play. | Explicit opt-in, safe areas, war schedules, victory conditions and recovery from abandoned ownership. Do not silently connect clans to legacy kingdom PvP. |
| Player homes and shops | Personal storage, decoration and player trade. | Property ownership, safe item persistence, listings/escrow and atomic purchases; builder room assignments alone are not property deeds. |

Treasury transfers, trading, quests and existing coins must stay outside the current monster-reward multipliers. Otherwise moving money between characters could manufacture gold. Any future quest bonuses should have their own explicit policy.

## Other useful feature candidates

| Priority | Candidate | Why it fits HollowDeep |
| --- | --- | --- |
| First | Mobile-friendly quest journal and command search | Makes existing content discoverable; commands can remain short and readable. |
| First | Tutorial quest chain with level-appropriate encounters | Builds on Chronicles while teaching training, spells, stances and group play. |
| First | Clan membership, ranks, chat and notice | Establishes persistent social groups before introducing shared assets. |
| Next | Group finder and scheduled event notices | Helps a small population meet for cooperative play; respect chat mutes and privacy. |
| Next | Builder preview/review and area validation | Check exits, unreachable rooms and content before opening a new zone. Current room edits save immediately; review staging would be new work. |
| Next | Crafting contracts and gathering | Adds noncombat progression, with resource sinks and transaction-safe rewards. |
| Next | One class specialization | Test a distinct play style before expanding the full class roster. See [progression options](PROGRESSION_OPTIONS.md). |
| Later | Voluntary remort | Needs a preview, explicit confirmation and recoverable character/progression changes. Never reuse native staff class IDs. |
| Later | Housing, shops, shared vaults and opt-in clan competition | Valuable longer-term systems that depend on the ownership and transaction foundations above. |
| Optional | Sound and accessibility settings | MSP can serve supporting clients; text must remain complete and sound optional. |

Timed event scheduling, a pending-event queue and event history would also be useful. They are not part of this update: currently one event runs at a time and staff explicitly stop it before replacing it. Measure reward rates at normal play and at 5×, 10× and 20× before adding rewards that multiply again.

## Save compatibility and acceptance checks

Use versioned data beside the existing saves, without changing the original serialized character structure. Give organizations stable IDs independent of display names. Membership, pending invitations, rank changes and their audit should commit together. Character deletion/rename, absent leaders and damaged records need defined recovery procedures.

Before deployment, test unauthorized invitations and promotions, peer protection, duplicate names, simultaneous membership changes, expired invitations, muted clan chat, leadership acceptance, reconnect/restart persistence and failed writes. Test money or item transfers with failures between every write and repeated requests; balances/items must neither disappear nor duplicate. Back up the full world and sidecar data.

Recommended next build: implement the first clan release end to end, with in-game help and a player guide. Add halls and cooperative quests next; add treasury/item systems only after their recovery behavior has been proven.
