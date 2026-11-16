# HollowDeep Round 73H — native guardian death evidence, restart recovery

**Status:** PRIVATE, TEST-GATED milestone. **Not a loot engine. No deployment.**

This batch addresses the known Round 73D issue that all guardian/chest state
lived in process memory. It adds an optional independent, file-backed C record
for **one** owner+map+site challenge, minted random 128-bit encounter and
unique guardian IDs, and a random event ID for each pointer-verified death.
A guarded native variant loads the record after a simulated restart and binds
only guardians not already recorded dead. The existing `open chest` command
continues to print `reward delivery is disabled in this test build`.

## Security contract and limitations

- `hd_treasure_guardian_death` must first compare the **exact live creature
  pointer** and the owner in the correct room. Matching monster names alone
  never create a credit. Deaths by other players are refused.
- On each write, the process locks the root-private `0700` evidence directory;
  the record is replaced using a new `0600` temp file, file `fsync`, atomic
  rename, and directory `fsync`. Short writes and pre-rename failures leave
  the old record intact. An after-rename fsync failure is **uncertain** and
  does **not** credit the in-memory chest.
- IDs are 128-bit random values from `/dev/urandom`. CRC-32 detects format
  corruption, not malicious tampering. The proof is **not a cryptographic
  attestation**. Any process with write access as the game account could
  forge it. **DO NOT import these files as trusted kills into SQLite or grant
  native inventory rewards.** A trusted, authenticated game-to-ledger event
  transport and authorized map minting are still required.
- An already-dead guardian is not rebound to a respawned copy after restart;
  it cannot be credited twice under the same map challenge. Claims must
  remain one-time and bound to durable native receipt IDs.
- Only one registered challenge per map ID. A different owner, room or guardian
  list is rejected, not silently reset. For new challenges, mint a new map.
- `HD_GUARD_EVIDENCE_TEST` is deliberately **absent** from prior validated
  builds. The `install_private.py` helper insists on an exact audited
  `treasure_guard.c` SHA and a disposable source path before modifying files.
- A new private runtime fixture must create
  `hollowdeep-data/treasure-proof` owned by the game process, mode 0700,
  before `open chest`; without it the test-gated version fails closed.

## Local tests run

- 64-bit sanitizer-enabled C evidence-unit tests: real fork/restart,
  immutable guardian/encounter IDs, two independent guardian death credits,
  owner/map/room mismatch, stale event replay, corrupt bytes, symlinks,
  deterministic before/after rename failure injection.
- Native `treasure_guard.c` harness with the **actual uploaded** C header and
  struct definitions: invalid lookalike monster pointer, wrong killer,
  correct pointer+owner death, opened chest after simulated restart, original
  non-chest command behavior, still disabled loot.
- **ELF32 private Linode build/test is not yet claimed.**

## Standalone tests (no gameplay/server startup)

```bash
HD_TEST_ELF32=1 HD_SANITIZE=0 bash run.sh \
  /root/hollowdeep-dev/PRIVATE_SOURCE/treasure_guard.c \
  /root/hollowdeep-dev/PRIVATE_SOURCE
```

If the private source already includes `hd_guard_proof`, use a separate copy
of the exact 73D baseline `treasure_guard.c` for the first path. Source drift
fails closed. A private game build can be patched with:

```bash
python3 install_private.py /root/hollowdeep-dev/PRIVATE-COPY/src .
make -C /root/hollowdeep-dev/PRIVATE-COPY/src -j2 frp.new
```

**Remaining before gameplay rewards:** authenticated in-process verified-kill
handoff to the SQLite ledger, trustworthy map creation (not name-matched
minting), immutable reward manifest authority, no stale sessions, native
`hd_native_reward_apply` integration, durable receipt/ledger acknowledgment
and one full Round59–73F isolated native/browser replay. No production
restart or publication of private fixtures, credentials or player data.

## Operator-reported Linode ELF32 result — 2026-11-16

The operator ran the private 32-bit test/build command against an audited,
**disposable** native source checkout and reported the following exact markers:

```text
ROUND 73H: durable unique guardian IDs, death proof, restart, spoof/corruption/symlink denial PASS
ROUND 73H: test-gated guardian proof variant generated
ROUND 73H: native pointer-only death, restart recovery, owner denial, disabled rewards PASS
ROUND 73H: private evidence gate PASS; chest rewards remain disabled
ROUND 73H: verified private guardian-evidence source installed
REWARDS: DISABLED; no production or service changes
ROUND 73H ELF32 PRIVATE BUILD: PASS
Production deployment: NONE
Private workspace: /root/hollowdeep-dev/round73h-clzepqqB
```

This is an **operator-reported** PASS of the focused ELF32 tests and native
compile in a test-only checkout; the publisher has not independently inspected
the private build or its logs. The full candidate-specific native/browser
regression **has not been rerun** with Round 73H enabled. The proof's CRC is
not an authenticated event, so the SQLite claim ledger must not import it as
trusted combat proof. The built game still has treasure rewards **disabled**.

Next complete integration gate (single milestone): in-process authenticated
native death and carried-map authorization into the trusted SQLite claim
boundary, exact guardian instance binding, durable claim receipt and live
inventory reconciliation, then one isolated native chest-kill-reconnect-restart
regression and full prior regressions. Never use `g-*.proof` records as an
independent grant authority, and do not deploy or restart production.
