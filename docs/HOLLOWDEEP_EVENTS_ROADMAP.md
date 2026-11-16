# HollowDeep MUD — World Events and Tournaments Roadmap

**Status: design / future work, not implemented or active.** Round 74B private XP/training and Round 74C rebirth/save integration take priority. No production, website or Discord deployments are implied by this document.

## Goal

Run automatic and staff-hosted game-wide events with announcements inside the MUD, opt-in participation, clear rules, fair brackets, durable results and safe rewards. Events must survive process crashes/restarts, not corrupt native room/player records, and not allow repeated payouts.

## The event catalog

| Event | Format | Entry / core rules | Proposed prizes | Priority |
|---|---|---|---|---|
| Last Man Standing | PvP free-for-all in a disposable arena | Opt-in; isolated rooms; one elimination; spectators; solo-account rules; reconnect policy | Title, trophy, event tokens | High |
| Arena Duels | 1v1, 2v2, unranked and ranked | Brackets by level/rebirth; saved loadout and safe restore; anti-win-trading | Rating, rankings, cosmetics | High |
| Lottery / raffle | Daily/weekly server-selected draw | Earned event tickets initially; optional **in-game gold only** ticket price later; per-account cap; no cash value | Cosmetic or bounded in-game rewards | High |
| World Boss | Server-wide cooperative PvE | Join a public raid, contribution measured for damage/healing/support; unique boss instance | Participation rewards, trophy | High |
| City Invasions | Waves of monsters attack a town | Wave timer; prevent world damage from persisting after event; defend friendly NPC | Gold, reputation, guild points | Medium |
| Treasure Hunt | Explore live world using riddles | Server-selected clues; unique discovery claims; no privileged `locate` leakage | Bounded items, titles | Medium |
| Survival Arena | Cooperative PvE waves | Timed increasingly difficult rounds; checkpoints; no inventory loss | Event points, cosmetics | Medium |
| King of the Hill | PvP zone-control | Timed point accumulation; participation required; safe spectator and restore | Ranking, event points | Medium |
| Capture the Flag | Team PvP | Two teams, no teleport exploits, flag reset on disconnect | Team titles, points | Medium |
| Guild Championship | Guild bracket/seasons | Opt-in rosters, minimum distinct participants, remort tiers | Seasonal banner/hall of fame | Later |
| Scavenger Hunt / Trivia | Noncombat | Puzzle prompts, clue trail, cooldowns, anti-spam | Event tokens, lore rewards | Early |
| Seasonal Festival | Holiday or monthly themed quests | Newbie-friendly zones, temporary NPCs and cosmetics | Cosmetic rewards | Later |
| Community World Quests | Cooperative world progress | Shared goals such as kills/contributions with capped personal credit | World announcement, personal rewards | Later |

Community references for design: [LegendMUD games/events](https://www.legendmud.org/index.php/Games_and_Events) show tag/LMS, trivia and scavenger hunts; [BatMUD events](https://dryad.batmudder.com/events.asp) show unpredictable noncombat and invasion events. HollowDeep implementations must be original and compatible with its own C engine.

## Recommended implementation order

### Round 75A — Event Director infrastructure

Create one event lifecycle: `DRAFT -> SCHEDULED -> REGISTRATION -> RUNNING -> SETTLING -> COMPLETED` with explicit `CANCELLED` and recovery states. Store UTC timestamps and display local time on website/Discord. Only one authoritative event runner may settle an instance. Provide GM create/modify/cancel and owner-only security settings; public `events`, `event join`, `event leave`, `event status`, `event leaderboard`, `event spectate` commands. Add automated broadcast countdowns and safe cleanup after an abort.

Start with trivia/scavenger events as end-to-end no-PvP pilots, using test-only prizes or score records until the reward engine is production-ready.

### Round 75B — Arena and Last Man Standing

Implement event-isolated PvP room sets. Preserve and restore a participant's original room, HP/MP status, inventory/equipment, combat flags and party state; do not let arena deaths trigger ordinary loss, graveyard drops or death penalties. Restore on exit, timeout, crash or disconnect; no live player data should be mutated outside an atomic safe restore path. One native-elimination token per participant; reject reconnect replay; announce winner with an auditable match ID.

Protect fairness: opt-in only; no unsafe teleport/recall into or out of running arenas; forbid external buffs/heals or take a deliberate snapshot; bracket by level **and rebirth count**, so first-life players are not automatically matched against legacy-powered remorts. Handle ties, a lone entrant, disconnections and GM cancellation explicitly.

### Round 75C — Lottery and event reward claims

Begin with earnable tickets to avoid a pay-to-enter lottery. If later allowed, virtual gold purchases must debit once in the **same durable transaction** as ticket issuance, enforce ticket/account limits, and refund cancellations exactly once. Drawing uses server-selected cryptographic randomness with recorded rules, immutable participant cutoff and an auditable draw record. Prevent ticket fabrication, duplicate claims, winner manipulation and admin retroactive entry. No real-world cash, crypto, or cash-out.

Event prizes must use the durable native receipt / SQLite claim bridge from the Round 73G–73J work **only after its remaining production security gates pass**; until then, record outcomes and leaderboard points privately without transferring live items or currency.

### Round 75D — World bosses, invasions and guild seasons

Use native verified monster IDs, real death hooks and contribution events with clear idempotency. Never grant rewards from client-submitted kill reports. Use temporary event overlays/isolated room templates; do not overwrite the live world's binary room records. Add balance bands, cooldowns, team sizes and per-account limits.

### Round 75E — Website, Discord and player guides

Live HollowDeep PHP: public event calendar, rules, registration status, leaderboard/champion history, match brackets, and a carefully permissioned staff scheduler. Discord: scheduled announcements, countdowns, registration reminders and winner posts (without private account or server data). Keep website administrative endpoints separate from private native builder access. Only advertise an event as enabled after production tests and deployment.

## Player-facing commands (planned, not present)

| Command | Planned effect |
|---|---|
| `events` | Event calendar and active countdowns |
| `event info <id>` | Rules, bracket, registration window and prizes |
| `event join <id>` | Validate eligibility and opt in |
| `event leave <id>` | Withdraw before lock-in; no silent escape during matches |
| `event status` | Current round, standings and own eligibility |
| `event leaderboard` | Past winners and current season records |
| `arena queue` / `arena spectate` | Duel matchmaking and spectator access |
| `lottery tickets` / `lottery results` | Read earned tickets and published draw outcome |

Staff should receive separate permission-gated commands (`event create`, `event schedule`, `event cancel`, `event resolve`) with audit logging. Do not enable blanket public admin operations.

## Source-file integration atlas

| Existing source | Planned role |
|---|---|
| `global.c`, `command1.c` | Command registry/dispatcher; only introduce event commands with matched indices/declarations |
| `update.c` | Periodic ticks/announcements; event transitions must be replay-safe and not rely solely on volatile timers |
| `room.c`, `files1.c`, `mstruct.h` | Inspect room/exit/lifecycle and native ABI before isolated arena/world templates; no binary structure changes by default |
| `creature.c` | Verified death/elimination and event boss kill hooks; avoid client-selected result IDs |
| `player.c`, `command4.c` | Participant status/HP/MP/visibility and player-facing summaries |
| `command2.c`, `command3.c`, `command7.c` | Temporary event movement, inventory/equipment handling and optional economy rules |
| `files2.c`, `hd_player_store.c`, `treasure_receipt.c`, `atomic_player_snapshot.c` | Durable reward/restore coupling with compressed player saves |
| `hollowdeep_staff.c`, `auth.c`, `hollowdeep_help.c` | Staff permissions, operator audit/help text |
| New `hd_events.*`, `hd_arena.*`, `hd_lottery.*` | Proposed isolated event core, PvP state and auditable draw logic (not created yet) |
| `/var/www/hollowdeep` | Separate future PHP public calendar and permissioned event administration |

## Nonnegotiable safety and fairness checks

- All event money/tickets/results/claim IDs are persistently unique and auditable; no reward duplication across restart or disconnect.
- Restoring arena players must preserve the exact pre-event save, inventory, gold, XP and room unless an explicit protected gameplay reward transaction succeeds.
- A character's life/remort state is verified from durable save data; no guessing first-life or rebirth status from class/level.
- Public PvP is opt-in and isolated. A player cannot enter an active arena without registration or attack outsiders from within.
- Pre-start cancellation/refunds and post-crash recovery run in isolated native test worlds, including multiple sessions and simultaneous actions.
- Build each milestone as ELF32 on Linode; run the full private MUD gameplay regression before any production deployment or restart.
- Keep all existing live website, game service, player saves and world binary files unchanged without explicit reviewed authorization.

## Relationship to Round 74

Round 74B still uses **one level per `train` call** while allowing accumulated XP sufficient for up to five eligible training levels. The proposed first-life discount is **half XP threshold and half gold cost** only after remort/life status is durably verified. These mechanics need completion before level/remort-stratified arena matchmaking and event rewards are finalized. An events roadmap is not evidence that the reward or progression integrations are live.

## Documentation expectations

Every delivered event will include: changed-file and exact-function guide, builder/GM setup, player help, website/Discord message template, fairness and eligibility policy, tests/recovery results, and GitHub changelog. The maintainer is not expected to hand-edit source.
