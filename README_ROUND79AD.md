# Round79AD Fast-track: private six-species mount integration candidate

Candidate only; **NOT** an accepted playable mount release. This branch
contains a dedicated, unexposed, noncombat native six-species fleet and a
single pure board/dismount/stable/retrieve/mounted-travel planner. The final
native commands, death tombstone, logout/reconnect restoration, atomic move
checkpoint and all-species socket gameplay are still required before this
branch may be accepted or deployed.

## One private verification runner

`tools/gameplay/round79/private_mount_ad_fasttrack.sh WORK SOURCE`

`WORK` must be a fresh `/root/hollowdeep-dev/round79ad-*` directory.
`SOURCE` must be the accepted Round79AC3C **private** source at
`/tmp/hd-army-game-round79trustedspawn-3W2RXVIA/src`.

The runner checks eight staging/isolation regressions, six inert species
native C spawn/rollback tests, a pure native action/travel policy replay,
the real native world identity/roster/presence modules, full isolated ELF32
game compilation, stablecheck/Breath socket replay, and unchanged production
service PID/binary and accepted private ELF32 executable.

No private fixture/log, native player save, world binary, or credential is
committed to GitHub. No command, login, or production service is modified.
All generated creatures are 1-HP test placeholders with no spells, XP or
combat; they are not game-balanced or player-accessible.

**Important:** The runner only validates the *foundation*. It does not
constitute full mount gameplay acceptance and must not be used to promote
the candidate to `round79-gameplay-qol` until all integration gates in
`docs/ROUND79AD_FASTTRACK.md` pass.
