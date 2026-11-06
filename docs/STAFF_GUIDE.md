# Hollowdeep staff guide

This guide describes the new native staff module. Install the native update before using `hstaff` and `hmoderate`; these commands are not available merely because this guide or the website has been published.

Staff roles are attached to authenticated **Mordor character names** and persist on the game server. Website sign-in, GitHub access and Linode ownership do not automatically create game staff roles.

## Roles and authority

| Role | Role management | Moderation | Other access |
| --- | --- | --- | --- |
| Owner | Assign or change owners, admins, mods, implementors and players, except the protected founder or their own role. | Moderate lower roles; native caretakers also require an owner. | Staff roster and audit. |
| Admin | Assign or remove mods and implementors; cannot change admins or owners. | Moderate lower roles. | Staff roster and audit. |
| Mod | Cannot assign roles. | Announce, mute, unmute and kick lower-role characters. | Staff roster. |
| Implementor | Cannot assign roles. | Same starting permissions as Mod; cannot moderate Mods or other Implementors. | Staff roster. |
| Player | None. | None. | View their own role. |

Implementor is a separate assignable role at the same authority level as Moderator: `Player < (Mod = Implementor) < Admin < Owner`. The role does not grant native DM class powers.

The configured founder is **Realmkeeper** on this deployment. The founder's owner authority is protected and requires the configured original DM character; another character cannot obtain it by choosing a display name. Other owners can be appointed, but the founder cannot be demoted through these commands.

After the builder/event update, these roles also govern `hbuild`, `hdm` and `hbonus`. Owners assign room ranges; builders edit only their ranges; admins/owners gain the listed teleport and restoration powers. See the [building and event guide](BUILDING_GUIDE.md). These tools do not change original classes, levels or Linux access, or grant blanket access to the original `*` DM commands.

## Appoint staff

First have the intended character enter the game and use `save`. Role targets must already have a regular saved character file. As Realmkeeper, inspect your own role:

```text
hstaff whoami
```

Then assign the needed role, replacing the example names with actual characters:

```text
hstaff grant Aria admin
hstaff grant Rowan mod
hstaff grant Elara implementor
hstaff list
```

An owner can appoint another owner with `hstaff grant Aria owner`. A self-role change is refused; another owner must make it. To return a character to player status:

```text
hstaff revoke Rowan
```

`hstaff grant Rowan player` has the same role outcome. A role change clears an older mute on that character. Assign the least authority needed for the work, and use ordinary playable characters for regular adventuring.

## Moderate a session

```text
hmoderate announce Welcome to Hollowdeep!
hmoderate mute Trouble 10
hmoderate unmute Trouble
hmoderate kick Trouble
```

- Announcements accept 1–180 printable ASCII characters. They reach the game through the original broadcast routine.
- Mutes default to 10 minutes and accept 1–1440 minutes. Mute and kick targets must be online and already saved; unmute can remove a stored restriction after a character disconnects.
- A mute blocks `say`, `tell`, `emote`, `yell`, `sendmail`, `gtalk` and `broadcast`, including their registered aliases. Staff announcements also respect the speaker's mute.
- Mutes survive reconnects and server restarts. Movement, combat, help, saving and logout remain available.
- Kicking uses the original engine's disconnect/save path. It does not delete a character or ban a future connection.
- Staff cannot moderate themselves, peers or higher roles. The founder is protected.

## Review staff actions

Admins and owners can run:

```text
hstaff audit
```

The server retains the most recent 64 action records and displays the most recent 10. Entries contain a UTC timestamp, actor, action, target and role/duration where relevant. Announcement text and passwords are not stored in this audit.

Role changes, mute changes and their audit records are committed together. If storage is corrupt or linked unexpectedly, staff operations and protected chat fail closed rather than granting authority. Movement and saving still work. Ask the Linux host operator to inspect the retained data; do not delete the database to bypass a failure.

## Help and backups

```text
help hstaff
help hmoderate
```

Staff data lives in `/srv/hollowdeep/world/hollowdeep-data/staff.db`. Include the whole `hollowdeep-data/` directory with normal world backups; it also holds Chronicle journals and stance choices. Keep backups private because the world contains player account data.

The builder/event update adds `builders.db` for room assignments and `bonus.db` for the event end time and multipliers. Authorized attempts use the audit actions `buildtry`, `rangetry`, `powertry` and `eventtry`; these are written before effects, so a failed operation can still have an audit entry. Read its command response to confirm success. Failed audit writes prevent changes.

The event-tier update allows Mods/Implementors x1–x5 for 1–60 minutes, Admins x1–x10 for 1–1440 minutes, and Owners x1–x20 for 1–1440 minutes. Use whole numbers. An active event can be stopped only by staff of its creator's rank or higher. Owners retain unrestricted room access within the engine's valid room IDs; their reward events retain the stated bounds.

Existing stored role IDs remain unchanged; Implementor has a new ID whose authority is explicitly mapped to Moderator. Do not compare numeric IDs as ranks in new code. Back up the full sidecar directory before downgrading: an older engine does not understand Implementor records or the expanded bonus limits.

The [server guide](SERVER_GUIDE.md) explains updates, service logs and the separation between game staff roles and host administration.

## Discover your powers and identify staff (new update)

Use `dmcommands` or `dmhelp` to list tools allowed by your current role and builder assignments. `dmcommands native [page]` lists original `*` commands only for characters with the native caretaker/DM class. For syntax use `help hstaff`, `help hmoderate`, `help hbuild`, `help hdm` and `help hbonus`. Native commands retain target/named-operator restrictions. A role grant never changes native class.

`who`, `whois`, the staff roster and announcements display `[OWNER]`, `[ADMIN]`, `[MOD]` or `[IMPLEMENTOR]`. Mod and Implementor are peers. `who`/`whois` preserve native invisibility filtering. Revoking a role removes its badge immediately.

## HollowDeep Staff clan

Every verified Owner, Admin, Moderator and Implementor belongs automatically. There are no invitations, dues, treasury, player-clan ownership or extra powers. A builder range or native caretaker class alone does not confer membership.

```text
staffclan
staffclan who
staffclan say Please review the new area entrance.
```

`hstaffclan` is an alias. The roster includes offline staff; chat is delivered only to online staff and is not queued for offline readers. Chat accepts 1–160 printable ASCII characters, includes the sender's role badge, and respects existing timed mutes. Role revocation removes access and delivery immediately. Membership is derived from `staff.db`, so no second roster can become stale. Invalid role storage denies access. This is separate from proposed player-run clans.
