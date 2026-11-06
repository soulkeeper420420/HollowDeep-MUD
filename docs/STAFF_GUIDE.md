# Hollowdeep staff guide

This guide describes the new native staff module. Install the native update before using `hstaff` and `hmoderate`; these commands are not available merely because this guide or the website has been published.

Staff roles are attached to authenticated **Mordor character names** and persist on the game server. Website sign-in, GitHub access and Linode ownership do not automatically create game staff roles.

## Roles and authority

| Role | Role management | Moderation | Other access |
| --- | --- | --- | --- |
| Owner | Assign or change owners, admins, mods and players, except the protected founder or their own role. | Moderate lower roles; native caretakers also require an owner. | Staff roster and audit. |
| Admin | Assign or remove mods; cannot change admins or owners. | Moderate lower roles. | Staff roster and audit. |
| Mod | Cannot assign roles. | Announce, mute, unmute and kick lower-role characters. | Staff roster. |
| Player | None. | None. | View their own role. |

The configured founder is **Realmkeeper** on this deployment. The founder's owner authority is protected and requires the configured original DM character; another character cannot obtain it by choosing a display name. Other owners can be appointed, but the founder cannot be demoted through these commands.

These roles govern Hollowdeep staff tools. They **do not grant original Mordor DM/caretaker classes**, character levels, spells, world-building commands or Linux access. Native engine privileges remain a separate system.

## Appoint staff

First have the intended character enter the game and use `save`. Role targets must already have a regular saved character file. As Realmkeeper, inspect your own role:

```text
hstaff whoami
```

Then assign the needed role, replacing the example names with actual characters:

```text
hstaff grant Aria admin
hstaff grant Rowan mod
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

The [server guide](SERVER_GUIDE.md) explains updates, service logs and the separation between game staff roles and host administration.
