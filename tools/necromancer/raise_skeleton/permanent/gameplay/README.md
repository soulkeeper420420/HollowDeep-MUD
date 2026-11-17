# HollowDeep Necromancer — native socket gameplay smoke (private only)

**Readiness: test harness published, results pending operator execution on Linode.**

This is the next acceptance layer after operator-reported successful build
`82a3c3c6bea8e216a65370a3fbfc06216df44762` on the exact
`round74b-integrated` source fingerprints. The reported private results show
ELF32 compilation, C-function heal testing and no-timer summon lifecycle,
but **do not** demonstrate real interactive gameplay.

## What `gameplay_smoke.py` does

1. Refuses all source paths except an existing
   `/root/hollowdeep-dev/necromancer-playtest-*/src` directory and verifies
   the exact staged permanent skeleton implementation SHA-256
   `1aaa3bb54dbefda6e8d706dfc42e20c55c7e1018d5ddcaa9972ad89c77da5e75`.
2. Checks required private death, login/reconnect and targeted-healing source
   hooks; refuses absent/non-ELF32 binaries.
3. Creates a new disposable root at
   `/root/hollowdeep-dev/necromancer-socket-XXXXXXXX`, with new private
   `rooms`, `player`, `objmon`, `help`, `post`, `bin` and `log` directories.
4. Compiles a small ELF32 native fixture against the **private** player/room
   serializers. Seeds a new Necromancer with an authenticated save marker and
   a trial monster at one current HP but 147 maximum HP / 51 maximum MP.
5. Starts **only** the private `frp.new` from that source, with the current
   working directory set to the disposable world and
   `HOLLOWDEEP_BIND=127.0.0.1` on a random high port. It connects as the
   disposable test player, kills the test monster through the real combat
   command, uses `raise skeleton`, checks `147 HP / 51 MP`, tests the
   one-skeleton limit, logs out, reconnects to the same private listener,
   and confirms the skeleton is present.
6. Always terminates the private game subprocess on completion or failure.
   Keeps the test world and game log for review. It **does not** touch the
   live world, production player saves, running service, website or Discord.

The earlier C-function tests already exercise actual native Vigor, Mend,
Restore and targeted potion handlers. This socket smoke does **not** claim
that those spells have been exercised interactively; that is a separate
remaining acceptance test, along with movement across rooms and native pet
combat/death/loot attribution.

## Execution

Use the **pinned GitHub command** provided with the release note, passing the
actual private source path from the operator's successful compile:

`/root/hollowdeep-dev/necromancer-playtest-LnYdQ8Pe/src`

Do not point this at `/srv/hollowdeep/world/src_3.00`, copy test player files
into production, or switch `hollowdeep.service` to the test binary.

## Important release blocker: until killed across restart

In this candidate, the skeleton is retained in **process memory only**.
Its limitless lifetime and same-process logout/reconnect do not imply that it
survives a server restart, crash, or unloaded room. To fully implement the
user's rule **"stays until it dies"**, a later private patch must persist an
authenticated, owner-bound pet record (identity, HP, MP, monster prototype/
level, current location and alive/dead state), reload it without duplicate
spawn/loot, and implement crash-safe atomic replacement and rollback tests.
Do not count or publish this feature as live until that has been verified.

## Expected success markers

```text
PASS: fixture holds native Necromancer save and 147 HP / 51 MP victim
PASS: socket login, native kill, 8MP raise with inherited 147HP/51MP
PASS: second summon denied with existing living skeleton
PASS: skeleton visible on same-process reconnect
NECROMANCER: REAL NATIVE SOCKET KILL/RAISE/RECONNECT PASS
PRODUCTION DEPLOYMENT: NONE
```

These are **expected**, not observed, until the operator supplies the actual
private run output.
