# Hollowdeep player guide

Hollowdeep runs the original Mordor 3.00 world with additional commands for exploration, character guidance, combat stances and staff moderation.

The native connection below has been confirmed by the host. New commands described as **update commands** become available after the native update is installed. Browser play also needs its separate bridge installation; a published website alone does not establish that connection.

## Connect from a phone or MUD client

| Setting | Value |
| --- | --- |
| Host | `172.233.176.81` |
| Port | `4040` |
| Protocol | Telnet |
| SSL/TLS | Off |

Enter your game character name and password at the Mordor prompt. A new character follows the original creation questions. Use a password unique to this game because native Telnet is unencrypted. Enter passwords only in the client password prompt.

`127.0.0.1` is for commands executed **inside the Linode's Lish console**. A Telnet app on your phone needs the public address above.

The [browser client](https://hollowdeep-dungeon.soulkeeper420.chatgpt.site/) uses ChatGPT sign-in before opening a game connection. You still log in to your Mordor character inside the terminal. ChatGPT sign-in does not assign game staff privileges.

## Your first session

Enter each command separately and read its response:

```text
look
score
inventory
equipment
hcommands
hclass
```

Read a room's description and exits before moving. `north`, `south`, `east`, `west`, `up` and `down` are movement commands. Original short forms include `n s e w ne nw se sw u d`, `l` for look, `i` for inventory and `sc` for score.

Ask for an action's rules with `help <command>`, for example `help train` or `help flee`. The original `flee` command can drop a wielded weapon, so keep its consequences in mind before combat.

End a session with:

```text
save
quit
```

If the game asks you to wait before quitting, wait for the displayed interval and send `quit` again. A refused quit is not queued automatically.

## Character progression

Mordor has ten playable classes: assassin, barbarian, bard, cleric, fighter, mage, monk, paladin, ranger and thief. Skills and spells retain their original class, level, equipment and target requirements.

Earn experience and gold through the game, then use `train` in the appropriate class training room. Training spends gold and retains accumulated experience. Spell learning uses the original scroll and `study` rules.

The update adds two compact views:

| Update command | What it shows |
| --- | --- |
| `hprofile status` | Current health/mana, class, level, XP, gold and Chronicle totals. |
| `hclass progress` | XP requirement, training cost, remaining resources and the current training-room checks. |

`hclass progress` uses the original progression table. Its readiness check also considers blindness and the engine's character-approval flag. It reads your state; use `train` to perform the actual level advancement.

## Your available spells

After installing the source update that adds this command, enter `spells` (or
`spell`) to see your learned spells alphabetically, one per line, together with
your current and maximum mana. The list uses your character's actual learned
spells, including spells learned from scrolls; it does not guess from your class.

Use `cast <spell> [target]` to cast and `help <spell-name>` for that spell's rules.
Knowing a spell does not guarantee you can cast it immediately: mana, class,
level, cooldowns and other conditions still apply. If the list is empty, use
`help study` to read about learning from scrolls. Listing spells does not cast
them, spend mana or change your character.

`help spell` explains the new command. `help spells` retains the original catalog
of all game spells, including spells your character has not learned.

## Exploration Chronicles

Start with:

```text
hquest accept first-steps
hquest survey
```

Move to another real room and survey again. A room counts once, even if revisited. After surveying three unique rooms:

```text
hquest claim first-steps
hprofile
```

| Chronicle | Unique rooms | Required level | Badge |
| --- | ---: | ---: | --- |
| `first-steps` | 3 | 1 | Wayfarer |
| `mapmaker` | 10 | 1 | Pathfinder |
| `apprentice` | 3 | 3 | Adept |
| `veteran` | 10 | 5 | Veteran |

Earlier surveys count toward later accepted Chronicles. Badges are cosmetic; they do not award XP, gold or class abilities. Chronicle progress is saved on the server and follows the same character between clients.

The update command `hquest next` suggests a claimable badge first, otherwise an unfinished active goal or the next Chronicle to accept. It does not accept or claim automatically.

## Combat stances — update commands

Use `hstance` to inspect your current stance, then choose one deliberately:

| Command | Physical combat tradeoff |
| --- | --- |
| `hstance balanced` | Original hit thresholds. |
| `hstance aggressive` | Easier to land a hit; easier for opponents to hit you. |
| `hstance guarded` | Harder for opponents to hit you; harder to land your own hit. |

The threshold adjustment is 1 point at levels 1–4, 2 at levels 5–9, and 3 at level 10 or above. Attacker and defender effects combine. Stances affect ordinary physical hit rolls, including attacks by monsters, without changing spell success or damage rolls.

A change requires 20 seconds since your previous change and 20 seconds beyond your last attack/spell cooldown. Choose before engaging instead of trying to switch between every attack and retaliation. The stance persists across logins. It applies to the ten playable classes, not administrative characters.

## Play together

| Command | Purpose |
| --- | --- |
| `who` | Request the visible player list. |
| `say <message>` | Talk in the current room. |
| `tell <name> <message>` | Send a direct message. |
| `follow <name>` | Follow a character in your room. |
| `group` or `party` | List characters following you. |
| `gtalk <message>` | Talk with your leader and group. |
| `lose` | Stop following your leader. |
| `lose <name>` | Remove one of your followers. |

The update adds `hcommands mobile` and `hcommands social` for these instructions inside the terminal. Role and mute rules are described in the [staff guide](STAFF_GUIDE.md).

## When something does not work

- **Unknown update command:** the game host may still run the earlier build. Existing `help`, `hcommands`, `hclass`, `hquest` and `hprofile` remain the starting points.
- **Connection refused or timed out:** verify the public IP, port 4040 and Telnet mode. Tell the host the exact error and client name.
- **Browser says the host is disconnected:** native play and browser bridging are separate. The host must install and verify the bridge.
- **Training denied:** check `hclass progress` after the update, then read the original `help train`. Have staff investigate approval problems.
- **Muted:** movement, combat, help, saving and logout remain available. Ask staff to review the restriction; reconnecting does not reset a timed mute.

Use the [Realm Codex](https://hollowdeep-dungeon.soulkeeper420.chatgpt.site/codex) for searchable command and class guidance.

## Timed rewards and assigned builders

After the builder/event update, `hbonus` shows the current monster XP/gold multiplier and time remaining. Events are temporary, survive restarts and end automatically. They affect newly earned monster-kill XP and newly dropped monster gold; shops, trades, existing coins and quest/PvP rewards are unchanged. Normal training and saving still apply. The event-tier update supports whole-number multipliers up to 20× and durations up to 24 hours, depending on the initiating staff role. 1× means normal rewards.

If an owner assigns you a building range, `hbuild mine` shows its inclusive room IDs. You can build within that range without becoming a moderator. See [the building guide](BUILDING_GUIDE.md). Remort and specialization ideas are documented in [progression options](PROGRESSION_OPTIONS.md); they are not active character features.

Clan and guild designs, housing, cooperative quests and other possible additions are covered in [clans and feature options](CLANS_AND_FEATURES.md). These are proposals; this update does not enable clan commands.

## Find commands and existing skills (new update)

- `help` shows the first command-index page and usage.
- `help commands 2` or `help all 2` moves through the alphabetical index. There are 315 unique registered names/aliases in this source; native staff-class entries are filtered for your character.
- `help search spell` finds matching command names. Search is a substring match, not typo correction.
- `help social` lists social actions; `help wave` explains their usage.
- `help search` alone explains the original room-search command.
- `skills` lists native skills allowed by your class and level. `skills all` shows the full 18-skill catalog and requirements.
- `dmcommands` (or `dmhelp`) shows your assigned staff/building tools. Ordinary players see that they have no staff powers.

The command index is a reference; seeing a command name does not grant its class, equipment, cooldown or staff requirements. The skill list does not promise immediate readiness and never spends resources. Use `spells` for learned magic.

Staff labels are `[OWNER]`, `[ADMIN]`, `[MOD]` and `[IMPLEMENTOR]` in `who`, `whois` and staff announcements. Existing invisibility rules still apply. Implementor and Moderator have equal starting authority, even though their labels differ. Builder allocation is separate. The HollowDeep Staff clan accepts staff roles automatically and excludes ordinary players and builder-only characters.

Plans for higher levels, new spells/classes and gear-based quests are in the [future release guide](FUTURE_RELEASES.md). They are not unlocked by installing the command/help update.
