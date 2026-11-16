# Round 74B — first test-gated native progression hooks

**Status: private development only. No live deployment or website changes.**

This milestone is a first *actual native-engine hook* using the owner's uploaded
`round74b-native-source.tar.gz` (original source-derived SHA checks in
`apply_private.py`). It intentionally does **not** attempt to migrate old player
records, enable remort, unlock skills, change native training, or activate a
60-level cap. The full progression core remains from Round 74A.

## Implemented in the disposable native build

1. `command1.c` calls the strict `hd74_parse_starting_stats` parser **only** with
   `HD74_PRIVATE_NATIVE` defined. New characters may distribute up to **65 total points**
   across five stats, each stat **3–18**, matching the legacy allocation
   semantics except for increasing the ceiling from 54 to 65. The strict
   parser rejects extra tokens, non-decimal input, negative numbers, oversized totals and out-of-range values *without changing input or stat output*.
   Existing race modifiers still run afterward, and legacy characters remain
   untouched. Without the private macro, the original 54-point creation flow
   is bit-for-bit the original source.
2. `global.c` registers read-only `hprogress` for the **private build only**.
   It prints the current native `creature` class/level/XP/stats, compares them
   to the Round 74A sample XP curve (base 1000, growth 50, cap 60), and labels
   every result **development preview, not active training**. It does not
   write a player file, mutate a character, or claim the remort status exists.
3. `Makefile` adds `hd74_native.o`, `hd74_progression.o` and
   `-DHD74_PRIVATE_NATIVE` to the **disposable candidate only**.

## Boundaries and remaining integration

The original 25-entry `needed_exp` table remains active in `train()`
(`command7.c`), `info()` (`command4.c`), `exp_to_lev()` (`misc.c`),
`hclass progress` (`hollowdeep.c`) and death penalties (`creature.c`). Combat,
quest and trade XP are awarded from several different functions, including
`command2.c`, `command8.c`, `command10.c` and `creature.c`; those paths must be
bounded together before the new curve/cap can become live. The source also
contains an external `gstat.c` with `cls_lvl[11][26]` and indexing by level;
any level-cap increase requires separate tooling repair.

The Round 74A 512-byte progression snapshot is still standalone and is **not**
part of `hd_player_store` or actual character saves. Remort, prior-class skill
inheritance, permanent Legacy equipment, Divine Favor offerings and item
sacrifice remain offline design/model features only. The `No Save` item flag
must not be used for permanent gear without native serialization validation.

## Tests and expectations

- Normal and ASan/UBSan 64-bit C tests of the real `creature` struct and strict
  native stat parser, plus Round 74A progression core replay.
- Syntax-only compile of the patched `command1.c` and `global.c` against the
  owner's actual headers; existing legacy warnings are not suppressed in code.
- Source SHA checks reject unauthorized drift; re-applying the private patch
  is forbidden; no command changes are made unless the exact private `Makefile`
  is also patched.
- **Linode ELF32 executable and actual isolated game-session tests are still
  pending.** No old tests need to be repeated until the candidate actually
  changes native gameplay (which the private compiler switch does).

## How the maintainer tests on Linode

Extract the published branch's 
`tools/world-builder/round74/native-hook/` plus Round 74A `hd74_progression.[ch]`
from an exact verified GitHub commit. Copy the private **native build** to a new
`/root/hollowdeep-dev/round74b-*/src` directory. Run:

```bash
python3 native-hook/apply_private.py PRIVATE_NATIVE_SRC native-hook core
HD_TEST_ELF32=1 HD_SANITIZE=0 bash native-hook/run_tests.sh PRIVATE_NATIVE_SRC
make -C PRIVATE_NATIVE_SRC -j2 frp.new
```

Do not run the executable in the production world. After a successful build,
exercise **new character creation** and `hprogress` in an isolated native game
server with disposable player/world records. Run the complete Round 59–73J
regression only for the final combined candidate, not after every source edit.
Production service, player records, PHP site, and DNS must remain unchanged.

## Rollback

Because the patched sources reside in a fresh disposable copy, rollback means
**discard the `round74b-*` workspace**. Do not copy patched binaries, objects,
player files or modified rooms over `/srv/hollowdeep/world`.

## File guide

See `docs/HOLLOWDEEP_SOURCE_ATLAS.md` for the actual C file/function map, and
`docs/ROUND74B_EDITING_GUIDE.md` for the hands-on editing workflow. The user's
workflow is **assistant implements; user reads guides if/when desired**.
