# Building, DM powers and bonus events

These commands require the builder/event native update. Preparing a package or publishing this guide does not install it on Linode.

## Assign 50-room building areas

Log into the game as Realmkeeper or another owner. The target character must already exist and have used `save`.

```text
hbuild assign Aria 8000
hbuild assign Rowan 8050
hbuild ranges
```

These assignments cover **8000–8049** and **8050–8099**, including both endpoints. Substitute actual character names. The default is 50 rooms; an optional count permits 1–500 rooms. Room numbers must stay within 2–8999. Overlapping assignments are rejected, including overlaps with another range for the same builder. Multiple disjoint ranges per builder are supported.

Owners choose suitable ranges: assignment alone does not create, erase or overwrite any world content. An existing room inside an assigned range becomes editable by that builder. Use unused room numbers for a new area.

Building access is independent of moderation. Any saved player can receive a range without becoming a mod or admin. Admins also need assigned ranges to edit rooms; owners may edit any room. `hbuild mine` shows your assignments.

## Build and connect rooms

After receiving the example range, Aria can run:

```text
hbuild create 8000
hdm goto 8000
hbuild name Lantern Courtyard
hbuild describe Warm lanterns illuminate a quiet stone courtyard.
hbuild create 8001
hbuild link north 8001
hdm goto 8001
hbuild link south 8000
hbuild info
```

Changes save immediately. `create` refuses to overwrite an existing room. An existing exit must be explicitly removed with `hbuild unlink north` before replacement. Links are one-way, so add the return exit separately. Both ends must be within the builder's assigned ranges. Ask an owner to connect the finished area to the public world.

Names accept 1–79 printable ASCII characters, descriptions 1–180. Use full lowercase compass directions, `up` or `down`. New rooms start empty; existing flags, permanent objects and permanent monsters are preserved. This release does not add object/monster editing or mass deletion.

Moderators can inspect rooms with `hbuild info`; an assigned builder can also inspect the room they occupy. Building permission is checked for every edit.

## Remove permissions

```text
hbuild unassign Aria
hstaff revoke Aria
```

The first command immediately removes all Aria's room assignments. The second separately removes the staff role. Use both when removing both kinds of access. Completed rooms and character saves remain intact. Owners always retain full-world access through their owner role.

## DM powers by role

| Access | Commands |
| --- | --- |
| Assigned builder, any role | `hdm goto <room>` within their assignments. |
| Admin or owner | `hdm goto <room>` anywhere; `hdm restore` for self. |
| Owner | `hdm bring <name>` and `hdm restore <name>` for online lower-role characters. |

Founder and peer owners are protected from targeted powers. Characters in combat or possessing a monster cannot be teleported. Restoration sets current HP/mana to existing maxima; it does not change maximum stats, level, class or learned spells. Restored characters should use `save` afterward. Original `*` DM commands remain separate.

## Run a timed event

```text
hbonus
hbonus start both 2 60
hbonus stop
```

Everyone can view status. The event-tier update provides these whole-number limits:

| Role | Multiplier | Duration in minutes |
| --- | --- | --- |
| Moderator | 1–5× | 1–60 |
| Implementor | 1–5× | 1–60 |
| Admin | 1–10× | 1–1440 |
| Owner | 1–20× | 1–1440 |

Replace `both` with `xp` or `gold` to change one reward. 1× gives normal rewards. One event runs at a time; stop it explicitly before starting another. Staff can stop an event started by their own rank or lower. Moderators and Implementors can stop each other's events, but cannot stop Admin or Owner events. Start and stop are announced to players.

As an Owner, `hbonus start both 20 1440` gives 20× monster rewards for 24 hours. As a Moderator or Implementor, `hbonus start both 5 60` gives 5× for an hour. Each event benefits everyone. The creator's saved rank governs stopping even if that character later changes roles. Expiration continues while the server is offline; restarting never renews the event.

Owners have unrestricted room access within valid engine room IDs. “Unrestricted” does not remove their 20×/1440-minute event caps.

Events survive server restarts and expire automatically at the saved end time. Monster-kill XP is multiplied after the original damage-contribution calculation; newly dropped monster gold is multiplied once when the pile is created. Everyone earning those rewards benefits. Coin piles already created retain their value after expiry.

Existing coins, shops, trades, banks, quests and PvP rewards are not multiplied. Repeated pickup or transfer cannot trigger the multiplier again. The original training requirements remain. XP/gold calculations stay within 32-bit bounds; pickup refuses coin amounts that would overflow a wallet.

## Audit and backups

Admins and owners can use `hstaff audit`. Builder, range, DM and event commands log authorized attempts before effects. A failed save may therefore have an audit entry; the command's response states whether it succeeded. A failed audit write prevents the change.

Back up the entire world, including `hollowdeep-data/staff.db`, `builders.db` and `bonus.db`. Corrupt staff/range records deny protected actions. Corrupt bonus data falls back to normal rewards and refuses event changes until repaired.
