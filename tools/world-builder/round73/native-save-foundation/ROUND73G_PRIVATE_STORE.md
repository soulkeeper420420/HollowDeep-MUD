# Round 73G — private native player-store candidate

**Status: NOT DEPLOYED. TREASURE REWARDS DISABLED.**

Reviewed against the owner's uploaded native 73G C-source archive. This candidate
connects a bounded, fail-closed, receipt-preserving player-record codec to
`files2.c::save_ply` and `load_ply`, with `command8.c::savegame` no longer
reporting success on a failed or uncertain save. The existing native equipment
normalization remains in place. `compress.c` gains bounded LZW entry points;
file+parent fsync and atomic rename are provided by the previously tested
`atomic_player_snapshot.[ch]` helper. It does not change the native
`creature` or `object` structures.

## Tested locally (64-bit C, sanitizer enabled)

* Existing nested inventory and gold serialize, save, reload, and preserve identity.
* One staged item+gold+receipt commit reloads; duplicate claim IDs are refused.
* Ordinary subsequent saves preserve the in-file receipt without a sidecar.
* Four concurrent native grant attempts: exactly one commit, three already-applied.
* Injected write failure before rename leaves the old save intact. Injected
  post-rename failure reports **uncertain**, and receipt check verifies state.
* Cyclic inventory graphs, symlink player targets, malicious inventory counts,
  and tampered receipt CRCs fail closed.
* The patched actual `files2.c` save/load entry points and `command8.c`
  compile in syntax-only checks.

## One private Linode test (ELF32 build needed)

Copy the exact audited private native source directory into a fresh disposable
`/root/hollowdeep-dev/.../src` directory, then run:

```bash
python3 tools/world-builder/round73/native-save-foundation/apply_private.py \
  /root/hollowdeep-dev/ROUND73G_DISPOSABLE/src \
  tools/world-builder/round73/native-save-foundation
HD_TEST_ELF32=1 HD_SANITIZE=0 \
  bash tools/world-builder/round73/native-save-foundation/test_private.sh \
  /root/hollowdeep-dev/ROUND73G_DISPOSABLE/src
make -C /root/hollowdeep-dev/ROUND73G_DISPOSABLE/src -j2 frp.new
```

The patch refuses the production path, symlinked native sources, changed
`files2.c` or `compress.c`, missing source files, and double application.
The test executes in a disposable `/tmp` player directory and cleans up.
**Never point the patch or make command at `/srv/hollowdeep`.**

## Still blocked before real treasure awards

* Not linked to `treasure_guard.c` chest opening; guardian/map identity still
  relies on volatile monster pointers, not persistent authenticated kills.
* A trusted claim-authorizing native grant coordinator must create server-
  validated object templates, enforce carry/gold limits, reconcile the
  in-memory player after a durable save, and acknowledge SQLite only after
  independently verifying the in-file receipt.
* The code is a private candidate, not yet tested on ELF32 or in a running
  disposable server; the full Round 59–73F native/browser suite must be run
  against the **candidate binary**, not just the original baseline.
* The C format maximum is 64 receipts per player. When full, grants fail until
  an approved migration. Legacy `count_inv` caps top-level items at 80; the
  candidate safely refuses saves beyond that instead of silently deleting.
* Pre-existing saves are opened only if regular, singly linked, and owned by
  the executing game user. An environment with different existing ownership
  requires a separate migration plan, not weakening this check.

No private player records, production paths, credentials, fixtures, or test
runtime logs should be published with the patch.

## Operator-reported Linode candidate validation — 2026-11-16

The owner launched the guarded candidate-specific regression in a disposable
workspace `/root/hollowdeep-dev/round73g-candidate-nGN4h1BE` and reported
`candidate.status` **exit code 0**. The supplied log tail confirms:

- `ROUND 73F: native showmap movement, named-go, toggle, radius and suppression PASS`
- `ROUND 69: native draft room, custom templates and named exit gameplay PASS`
- `ROUND 59: PASS`, `ROUND 60: PASS`, `ROUND 61: PASS`, `ROUND 62: PASS`
- `ROUND 72: private regression suite PASS`
- `PASS: Production and prior fixture unchanged`

The guarded runner invokes `apply_private.py` and ELF32
`test_private.sh` in the private build before native/browser replay; its exit
status 0 means that command chain completed. The pasted excerpt includes the
**final** replay markers rather than the earlier candidate-specific test lines.
These results are operator-provided; no private Linode log or fixture was
uploaded to GitHub.

**Validation scope:** native file codec / save-load candidate and full
isolated regression **passed**. **Not proven / not enabled:** native chest
reward item creation, durable guardian/claim authorization, in-memory player
reconciliation after on-disk claim save, and ledger acknowledgment. Real chest
loot remains disabled. No live deployment/restart was performed.
