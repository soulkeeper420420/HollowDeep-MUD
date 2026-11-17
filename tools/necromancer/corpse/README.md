# HollowDeep: Monster corpses, raising, and deity sacrifice

Private playtest, based on the successful operator-reported deity/ELF32 build
at `57f4eba8ac518e1166ad4577256bffb4fdcd1ca0`. No deployment or service restart.

## Player commands

- `look`: displays `The corpse of <monster> lies here. [corpse <id>]`.
- `loot corpse [id]`: any player can consume a corpse, dropping its ordinary
  inventory and gold into the room. Use ordinary get commands to collect it.
- `sacrifice corpse [id]`: only a character with a valid saved deity (1–16).
  Consumes the corpse and releases the same loot. No favor award yet.
- `raise corpse [id]`: verified Necromancer, 8 mana, one living summon. Consumes
  the corpse, releases loot, and creates a skeleton with the monster's full
  maximum HP/MP. `raise skeleton [id]` and `raiseskeleton` are aliases. No timer.
- With more than one corpse, select the displayed numeric ID. Every action
  uses the same one-use record, so subsequent attempts on that ID cannot
  provide more loot or summons. Failed raises (including no mana, existing pet,
  or an unraisable corpse) leave the corpse and loot intact. Merchant stock
  stays excluded, and summoned pets never become loot-bearing corpses.
- Native help: `help corpse`, `help loot`, `help sacrifice`, `help raise corpse`,
  `help raise skeleton`, `help necromancer`, `help deity`, and authorized
  `help *deity`. Existing unrelated help pages are preserved.

## File map

| File | Change |
|---|---|
| `hd_corpse.c/.h` | Room-local corpse IDs, one-use escrow of the actual inventory tags, gold and inherited stats, command validation and original-tag transfer |
| `creature.c::die()` | Capture before normal auto-drop, retain Round74B XP and guardian hooks; no pet death reward/corpse, remove dead pet from active list |
| `hd_necro_skeleton.c/.h` | Raise from selected corpse, disable the earlier last-kill path under the new flag |
| `room.c::display_rom()` | Display corpses in the room |
| `files1.c::free_rom()` | Clear corpse entries and free escrow on room destruction |
| `global.c`, `Makefile` | Player command IDs 152/153; require all three playtest flags |
| `hollowdeep_help.c`, packaged `help/` | Seven native pages and alias routes |
| `apply_private.py`, `raise_from_corpse.inc` | Coupled exact eight-file source fingerprint of the reconstructed integrated candidate and exact-anchor staging |
| `test_corpse.c`, `test_healing.c`, `test_help.c`, `run_private.sh` | Focused C regression, actual native healing and help handlers, syntax and optional ELF32 build |
| `stage_help.py` | Private help installer, refuses conflicting existing files |

## Evidence and limits

Local 64-bit C tests passed for escrow ownership, nested items, gold bonus,
same-ID duplicate denial, multiple corpses, room isolation, corrupted/missing
allegiance denial, failed mana and failed gold-object preparation, one-pet
limit, inherited HP/MP, no timer, no corpse for a pet, merchant restrictions,
room cleanup, and ordinary raise socials. ASan/UBSan passed on the focused
corpse test. Actual native Vigor/Mend/Restore/item tests and actual native
help dispatcher/file-opening tests passed. A fresh replay also passed native
legacy/private syntax and refused duplicate patch application. Local syntax
used reconstructed Round74B source and its declaration-only XP header; the
real Linode source fingerprint and full native ELF32 build remain to be checked.
No real socket session has run on this corpse candidate.

**NO-GO for production.** Corpses are room-visible server records, not objects
that can be picked up or put in a bag. Their escrow, like ordinary transient
room drops, is not durable across room unloading or restarting this prototype.
The bounded registry (1024 corpses) falls back to native drops on saturation;
this must be addressed before promising corpses on every monster death. Native
ordinary inventory and gold are captured; separate existing quest/treasure
rewards are unchanged. Exactly-once consumption is in the single game process,
not a crash-safe transaction. Durable corpse/pet persistence and rollback,
actual socket gameplay, and full regression remain required before live release.

The one-pass bundle copies the successful private source to a fresh workspace,
checks the eight exact fingerprints, stages only in that workspace, runs the
focused tests, stages help in a private fixture, and forces a complete ELF32
build. It checks the existing production PID before and after. Any unexpected
source or help conflict is a hard stop. Never force-apply to the live world.

## Operator-reported combined ELF32 acceptance

The maintainer reported all focused corpse ownership, deity gate, failed raise,
ID selection, single consumption, inherited HP/MP, merchant and room cleanup,
native healing, seven help pages and legacy/private syntax checks PASS. The
combined ELF32 candidate is `necromancer-playtest-corpse-3nl5y8b7/src`, built
from the milestone at `60a8f7e`; production service PID reportedly unchanged.

Next gate: [gameplay_smoke.py](gameplay_smoke.py), at `cdfbc5f`, is a staged,
**not yet executed** real socket replay derived from the prior summon smoke
and published combined corpse source. It checks the exact corpse module
against the pinned bundle, verifies compile hooks and ELF32 header, records
the executable SHA, creates a new world, two synthetic saved players and
three distinct loot-bearing monsters, installs native help, seeds a test-only
deity record, and runs the private binary inside an unprivileged chroot.
Launch it in a fresh network namespace (enable loopback; do not use a PID
namespace with its own /proc, because the guard compares the caller's network
namespace to host PID 1). This verifies commands and visible loot, not exact
item-count multiplicity in the game display, actual staff assignment by socket,
interactive healing, room traversal, gold release, or restart durability.
Those remain gates; the focused C tests previously cover many of them.
The socket harness and fixture have not been compiled/executed in this turn.
If it fails, inspect private logs before modifying any source. **NO-GO for
production**, pending durable corpse/pet state and rollback.

### Socket launcher correction

The operator's first socket replay successfully wrote the native three-monster/two-player fixture, then raised `FileNotFoundError: chroot` because the restricted listener PATH omitted `/usr/sbin`. Commit `1f1375d` resolves the absolute system chroot executable before launch, refuses missing isolation, and pins the operator-reported accepted executable SHA-256 `26c806cf59b159555f8c0ec73f5daa0c0b0516d99bced49487c30cde0397bde7`. This changes the test harness only. The corrected real gameplay replay remains unexecuted; no production deployment.

### Operator-reported real gameplay progress; combat logout correction

The third socket attempt used the pinned combined ELF32 candidate and passed
the unprivileged loader preflight, three real in-game help pages, three
native monster kills and visible corpse IDs, unassigned sacrifice denial,
a successful 147 HP / 51 MP raise (110 to 102 MP), actual pet combat assist,
second-summon denial without corpse consumption, ordinary loot release,
non-Necromancer raise denial, assigned-deity sacrifice, and repeated ID
denial. These are operator-reported socket observations. The replay stopped
when native quit returned "Please wait 15 more seconds." This is not a
completed logout/reconnect or a final gameplay PASS.

Harness commit `3f8be61` respects the native cooldown with bounded retries,
requires original socket EOF and a surviving listener, checks the other
player's room view after logout, and requires a fresh room display of the
skeleton after reconnect. Combat retries are bounded by elapsed time to
accommodate randomized native attacks. The correction has not been executed
on Linode yet. No game binary or live world change. One display anomaly
requires follow-up: the ordinary Mage fixture was announced as Necromancer
even though its raise command correctly denied the class privilege. Verify
saved identities and title generation separately; actual title bug cause is
not established. The help headings also show legacy client encoding
artifacts. Restart/room-unload persistence and rollback remain NO-GO gates.

### Operator-reported complete native socket PASS

At harness commit `4b959e7bee0108d4a3b050b1192e0d73818e8ef2`, the maintainer supplied the full real network-isolated/chroot replay. It confirmed the pinned ELF32 executable, real native help, monster kills, corpse IDs, failed sacrifice for unassigned characters, 147 HP / 51 MP summon and exactly 8 MP (110 to 102), pet combat assistance, one-pet denial, ordinary loot, non-Necromancer raise denial, deity sacrifice, no repeated corpse use, native quit respecting a 13-second cooldown, disappearance of the owner in a witness room view, and fresh login with the same skeleton still present. Final marker: `CORPSE: REAL NATIVE SOCKET RAISE/SACRIFICE/LOOT/HELP PASS`. Production deployment: NONE. This establishes same-process behavior, not restart durability, interactive healing, exact item multiplicity after crashes, or live deployment. The legacy level 7-9 Mage title and non-ASCII help headings are separate display issues; full durable storage remains a release gate.
