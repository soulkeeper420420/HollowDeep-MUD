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
