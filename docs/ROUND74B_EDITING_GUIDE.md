# HollowDeep Round 74B — Editing Native MUD Files Safely

**Audience:** builders learning VS Code Remote SSH and the Mordor 3.00-derived C source.
**Status:** development guide only. Nothing here deploys, restarts, or modifies the live game.

## 1. Create your own isolated source folder

Do **not** edit `/srv/hollowdeep/world` or run `make` there. Use the private source-only archive exported from an audited disposable build:

```bash
set -Eeuo pipefail
umask 077
ARCHIVE='/absolute/path/to/round74b-native-source.tar.gz'
mkdir -p "$HOME/hollowdeep-dev"
WORK=$(mktemp -d "$HOME/hollowdeep-dev/round74b-edit-XXXXXXXX")
mkdir -m 700 "$WORK/src"
if tar -tzf "$ARCHIVE" | grep -Eq '(^/|(^|/)\.\.(/|$))'; then
  echo 'Unsafe archive entry: stop' >&2; exit 1
fi
tar -xzf "$ARCHIVE" -C "$WORK/src" --no-same-owner --no-same-permissions
test -f "$WORK/src/command1.c"
test -f "$WORK/src/mstruct.h"
printf 'EDIT FOLDER: %s\n' "$WORK/src"
```

Use **VS Code > Remote Explorer > SSH connection > File > Open Folder** and paste the printed `EDIT FOLDER` path. The source files are on Linode, not on your Windows disk.

## 2. Find code, edit and save

1. Press **Ctrl+Shift+F** to search all source files.
2. Press **Ctrl+P**, type `command1.c`, and press Enter.
3. Make a small change, review the surrounding logic, then press **Ctrl+S** to save.
4. Use **Terminal > New Terminal** in VS Code to run the checks below.

Start with a text-only practice change. In a **disposable copy** of `command1.c`, locate:

```c
print(fd, "\nAvailable classes:\n");
```

Change only the message:

```c
print(fd, "\nWelcome to HollowDeep! Available classes:\n");
```

To retain an easy undo before editing, run in the isolated source directory:

```bash
cp command1.c command1.c.before
```

After saving, inspect the exact change and compile privately:

```bash
diff -u command1.c.before command1.c || true
make -j2 frp.new
file frp.new
```

The executable should report **ELF 32-bit**. The command builds only a private executable; it does **not** start the MUD. To undo, copy `command1.c.before` back to `command1.c` and rebuild.

## 3. Understand the actual Round 74B hooks

| File/function | What it currently owns | What the new design must handle |
|---|---|---|
| `command1.c` / `create_ply` | Character creation, class/race selection, five stat inputs | Validated starting-stat allocation and legacy-character handling |
| `command7.c` / `train` | Training location, required XP and gold | Configurable XP thresholds and enforced level cap |
| `global.c` / `needed_exp[]` | Legacy 25-entry XP thresholds and command registry | New command dispatch and carefully migrated XP rules |
| `mtype.h` / `MAXALVL` | Compile-time 25-entry XP array limit | Cannot be changed alone |
| `mextern.h` / `needed_exp[25]` | Shared XP-table declaration | Must stay consistent with any threshold migration |
| `misc.c` / `exp_to_lev` | Converts accumulated XP to a level | Consistent cap/overflow handling |
| `player.c` / `up_level` | Level increases, HP/MP and stat bonuses | Safe cap checks and rebirth stat policy |
| `creature.c` / `die` | Combat deaths and XP credits | Trusted kill events, not client-supplied IDs |
| `magic*.c`, `command*.c` | Class, spell and proficiency checks | Real skill IDs and permitted inherited-class skills |
| `files2.c` / `save_ply`, `load_ply` | Entry points into `hd_player_store` | Commit progress/receipt with player data atomically |
| `mstruct.h` | Native serialized creature/object layouts | Never append fields without an ABI migration |
| `Makefile` | `frp.new` ELF32 object compilation | Add tested source objects with existing 32-bit flags |

## 4. Why changing the number 25 is dangerous

The old code uses `MAXALVL` in `mtype.h`, a 25-element `needed_exp[]` table in `global.c`, a fixed declaration in `mextern.h`, and readers in `command4.c`, `command7.c`, `misc.c` and `creature.c`. Changing only the constant or adding thresholds can read past array boundaries or overflow ELF32 `long`.

The original production character creator enforces **up to 54 total points** with **3–18** per stat. The updated private Round 74B test candidate uses **up to 65 total points**, keeping 3–18 per stat. Both the prompt and strict input validator are changed together; production is still at 54 until an approved native deployment. Changing the message alone would mislead players.

## 5. How to inspect, test and restore

```bash
grep -n 'create_ply\|Stat total\|Choose one' command1.c
grep -n 'needed_exp\|expneeded' global.c command7.c
make -j2 frp.new
file frp.new
diff -u command1.c.before command1.c || true
```

Test source and fixtures only in a disposable directory. Run gameplay with an isolated native world after the candidate builds. Do not copy the resulting binary to production, edit live player files, or run `systemctl restart hollowdeep.service` without a separate reviewed deployment decision.

## 6. Mobile / terminal fallback

Use `nano command1.c` in the private folder. **Ctrl+O**, Enter saves; **Ctrl+X** exits. In VS Code, use **Ctrl+S** instead. `nano` and VS Code modify the same remote file if they open the same path.

## 7. Review and publication

Before a GitHub push: review the diff, compile ELF32, run focused tests, then the full isolated gameplay regression if commands/game state changed. Publish **only reviewed source, public guides and changelogs**. Never publish archives containing credentials, private player files, runtime fixtures, passwords, or secret server configuration. Website copy should describe features as live only after production deployment is verified.
