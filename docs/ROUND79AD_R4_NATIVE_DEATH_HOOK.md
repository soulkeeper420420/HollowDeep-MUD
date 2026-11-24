# HollowDeep Round79AD R4 — Private native mount combat-death bridge

## Verified predecessor

R3 candidate `e1fa35059b41330d2b437dfcc414f74bb4e45538` passed the user's
private Linode ELF32 native compressed player-save, atomic fault, four-receipt,
Breath, logout and socket replay at exit 0. R3's disposable native source:
`/tmp/hd-army-game-round79adfour-03lRN95P/src`; private results:
`/root/hollowdeep-dev/round79ad-F5Dos5uu`. Neither production nor the
accepted branch was changed.

## New R4 source map and safety

- `hd79_ad_death_identity.inc`: private addition to the existing
  `hd79_mount_world_identity.c` translation unit, so it can inspect the real
  **process-local registered exact-pointer binding**. Only a dead native
  MONSTER actually present in the recorded native room, next to its live
  registered PLAYER owner, with matching owner name, epoch, ID, species and
  room can be identified; it never authorizes by monster display name alone.
- `hd79_ad_combat_death.c/.h`: internal server-only pre-removal callback.
  Reads authentic four-receipt owner state, compares recorded epoch and
  location, and invokes R3's locked exact-CAS `#83` death update.
  Before declaring success (including after an uncertain atomic rename),
  re-reads all **four canonical receipts** and verifies exactly one
  monotonic tombstone change, preserving roster/presence.
- `stage_mount_ad_combat_death.py`: strict one-time staging from the tested
  `/tmp/hd-army-game-round79adfour-*/src` source. Installs a feature-gated
  callback **at the beginning of native `del_crt_rom` before AC3B's
  `hd79_world_mount_unbind_creature()`**. It adds the private identity include
  and a Makefile gated object only. It preserves all previously tested
  `hd_player_store.c`, `files1.c`, `wilderness.c`, and player-command sources.
- `test_stage_mount_ad_combat_death.py`: nine strict staging tests including
  K&R/native C signatures, hook order, ambiguous signature rejection, and
  destination/source isolation.
- `test_hd79_ad_combat_death.c`, `ad4-mock/*`: isolated native C death-save
  fault/identity simulation: living, forged, stale, invalid, before-rename,
  after-rename, mismatched reread and repeated death.
- `private_mount_ad_combat_death.sh`: one root-only private ELF32 staged
  test, complete isolated game build, old stablecheck/Breath REST socket
  baseline, and live PID/binary plus prior R3 ELF32 hash verification.

## Important remaining blockers

This is a pre-removal **bridge**, not proof of full combat integration. The
callback currently runs only when the native `del_crt_rom` hook is invoked
while `hpcur <= 0`; all possible combat/monster death/remove paths still
need isolated actual gameplay coverage. A failed durable save returns a
fail-closed error, but the original native void removal function is not
interrupted. Therefore automatic login restoration remains **disabled**;
otherwise a failed write could resurrect a dead mount.

Before gameplay acceptance: prove all native death paths, transaction and
cleanup ordering under power failure; issue authenticated mount actions with
atomic four-receipt CAS and reversible native entity changes; prove safe
reconnect/idempotent restoration (including death and logout); mount
Endurance charge atomically with actual movement; and perform all-six-species
socket gameplay tests. None of those is claimed by a successful R4 foundation
runner. No public mount command or production deployment is included.

All private fixture players, logs, credentials and world records remain on
Linode. Candidate branch must not be merged into accepted or announced on
Discord until the **full** gameplay gates pass.
