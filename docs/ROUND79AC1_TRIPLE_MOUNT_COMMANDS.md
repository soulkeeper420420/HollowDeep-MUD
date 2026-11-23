# Round79AC1: three-receipt native mount commands (accepted private ELF32 validation)

## Feature flag
`MOUNT_TRIPLE_COMMAND_PLAYTEST=1` requires `MOUNT_PRESENCE_STORE_PLAYTEST=1`
and registers the dismount adapter object BEFORE the `frp.new` dependency rule.
No player or creature binary ABI changes.

## Native command semantics
`mount list` and `mount status`: read all three receipts, verified against the
authoritative Breath epoch and canonical physical positions. No implicit
roster initialization, award, mount spawn or mutation.

`dismount`: a preexisting rider in a valid current native room receives a
single new revision of receipts 80/81/82. The mount Endurance is unchanged;
receipt 82 stores the dismount room. Before-rename faults never acknowledge.
After-rename uncertainty requires exact three-receipt re-read; stale/foreign
revision, wrong epoch or corrupt presence fails closed. Repeat dismount is
an on-foot no-op.

`mount ID`, `stable ID`, `retrieve ID`: STILL fail closed because location
receipts are not physical in-world NPC authority. Real owned mount entities,
world room binding, logout/restart and mounted travel require separate
native validation before these verbs can be enabled.

## Tests
Synthetic native player test extends the accepted Round79AB 3-receipt test:
seed a mount in room 42, use synthetic policy to board, fail a before-rename
dismount, then reconcile after-rename dismount once and check no Endurance
change, preserved Breath and no repeat writes. All private, no live data.

## Promotion policy
Accepted on Linode, exit code 0: mock command and triple-dismount failures PASS;
actual native ELF32 player-file rollback/recovery PASS; full ELF32 native game
build PASS; isolated stablecheck, native mount listing, Breath persistence and
logout/reconnect socket replays PASS. Results remain private at
`/root/hollowdeep-dev/round79ac-tUTmg1Qu`.
Do not publish private logs, credentials, fixture player files, or server config.
Production deployment: NONE.
