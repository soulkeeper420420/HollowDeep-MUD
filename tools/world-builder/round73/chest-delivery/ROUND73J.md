# HollowDeep Round 73J — private chest-to-reward/recovery integration

**Status: source-only, test-gated candidate. NOT deployed; real MUD chest rewards remain OFF.**

This batch *combines* previously validated Round 73G native player saving and
native reward creation, Round 73H exact-monster guardian records, and Round 73I
process-pinned SQLite ledger calls in one **disposable, runnable native chest
harness**. It is not another disconnected protocol proof: the tested
`hd_treasure_open()` C command dispatches to a test-fenced native callback,
receives a server-selected immutable reward manifest, adds two real native
object records and gold using `hd_native_reward_apply()`, persists the receipt
in the same compressed character file, and asks the ledger to mark it delivered
**only after an independent native player-file verifier** confirms the receipt.

## What is implemented

- `reward_server.py`: test-only Unix socket service extends the Round 73I
  kernel `SO_PEERCRED` exact-game-PID/UID boundary. Validates trusted native
  site/reward templates from **private server-authored** files; `GRANT` creates
  a stable `DurableRewardCoordinator._prepare` manifest inside the existing
  SQLite claim transaction. `ACK` verifies claim/digest and independently
  invokes a private ELF-native compressed player-file receipt checker before
  changing the ledger to `delivered`. Delivered claims are rechecked against
  their persisted receipt and never grant again.
- `hd_reward_transport.[ch]`: server UID-verified C client; bounded ASCII
  manifest grammar, fixed maximum 32 items, exact 32-hex/64-hex IDs/digests,
  native OMAX bound, enchantments rejected, zero/overflow guards. Player
  text does not select a template, a reward or a claim key.
- `build_reward_variant.py`: SHA-256-fenced amendment to the exact generated
  Round 73I guard. Replaces its disabled-rewards message **only if the private
  `HD_J_REWARD_TEST` compile flag is present**. Does not modify the production
  source, native Makefile, or running service.
- `test_receipt_probe.c`: separate process runs `fsync()` on the player
  directory, independently decodes the compressed player record and checks
  the claim/digest. A mere client assertion of save success can **never**
  acknowledge a claim.
- `test_reward_native.c`, `test_reward_replay.py`, `run.sh`: a real native
  `open chest`/pointer-verified monster death and reconnect test harness,
  reused 73G C serialization/receipt code, repeated game process + ledger
  service restarts, spoof tests and explicit fault injection. No live world,
  player records or game service are used.

## Local result — 64-bit (not Linode ELF32 yet)

`HD_TEST_ELF32=0 HD_SANITIZE=0 bash round73j/run.sh DISPOSABLE_PATCHED_NATIVE_SOURCE`

**PASS in both unsanitized and ASan/UBSan 64-bit builds:** normal authorization/grant/ledger ACK; ACK interrupted after native
save; failed write before rename; uncertain post-rename write; exact PID
spoof denial; previously owned nested item survival; reconnect and repeat
open without duplicate items/gold; independent directory fsync + receipt
verification before ACK. Every scenario uses a fresh SQLite database and
private native player directory. Existing Round 73G/73H/73I focused ELF32
results and prior full Round 59–73F browser/native regression remain recorded
on the predecessor branches and are not changed or rerun by this local test.

## Gates before real server gameplay or Round 73 deployment

1. **Minted map identity:** `hd_treasure_has_map()` in the source guard still
   checks a visible item name. The private harness explicitly stubs a held
   map. A trustworthy *native map instance minted to a specific player* and
   checked against the active server-owned encounter must replace this before
   any live `open chest` grant can be enabled. Name lookup alone is forgeable.
2. **Production privilege separation:** test daemon and game share a UID,
   directory mode 0700 and socket 0600, with exact PID pinning. For deployed
   security, run the ledger as a separate service identity, set safe socket
   access/ACLs, pin PID via trusted supervisor and verify restarts. The test
   has **not** proven that deployment boundary.
3. **Real object bank:** the C test's `template_loader` is a fixture for object
   templates 123/124; real gameplay must load audited native object records,
   enforce live carry/weight and equipped item rules, and refuse unsupported
   enchantment effects. No test fixture loader may ship into production.
4. **Single session/recovery:** a real engine must enforce one writer per
   character and freeze or disconnect a stale live player when native saves
   become uncertain. The private harness simulates disconnect by exiting.
5. **Full native runtime/regression:** run the Round 73J ELF32 replay on Linode
   using a disposable source with the 73G player-store patch and original
   73D guardian source; then run one complete candidate-specific Round 59–73F
   regression **after** the actual native game command has been integrated.
   This phase does **not** include that full engine executable/replay.
6. **Durable source of truth:** keep the SQLite ledger pending through faults;
   never treat an untrusted guardian proof file, a visible receipt after an
   un-fsynced directory, or a client ACK string as proof of award.

**No production deployment, service restart, player writes or private
configuration publication authorized.** This branch is suitable for a private
ELF32 milestone check, not production release or claims of playable live loot.

## Operator-reported ELF32 validation — 2026-11-16

The operator supplied the output of the **private ELF32** `run.sh` replay from
`/root/hollowdeep-dev/round73j-IaltphxW`. It includes:

- `ROUND 73J: same-UID wrong-PID manifest spoof DENIED PASS`
- `ROUND 73J: native chest grant/save/receipt gameplay PASS`
- `ROUND 73J: native chest reconnect/no duplicate claim PASS`
- `ROUND 73J: normal durable native chest->receipt->ledger recovery PASS`
- `ROUND 73J: successful save interrupted before ledger ack stays pending PASS`
- `ROUND 73J: ack_lost durable native chest->receipt->ledger recovery PASS`
- `ROUND 73J: failed native save does not acknowledge/alter existing player PASS`
- `ROUND 73J: failed_before durable native chest->receipt->ledger recovery PASS`
- `ROUND 73J: uncertain save blocks session until reload PASS`
- `ROUND 73J: uncertain rename leaves ledger pending until fresh process+dir fsync PASS`
- `ROUND 73J: uncertain_after durable native chest->receipt->ledger recovery PASS`
- `ROUND 73J: isolated native playable-claim simulator PASS (production rewards disabled)`
- `ROUND 73J ELF32 PRIVATE INTEGRATION: PASS`
- `Production deployment: NONE`

This evidence was supplied by the operator and not fetched independently from
Linode. The new combined replay demonstrates a **private simulator**, not an
actual full native engine gameplay session. The existing production chest
continues to disable loot. Remaining activation gates include authenticated
map issuance/ownership, actual privileged ledger socket access policy,
native object bank/carry validation and single-session synchronization, and
an isolated full MUD native/browser regression after hooking the integration.
No production deployment, live-world modifications or server restart occurred.
